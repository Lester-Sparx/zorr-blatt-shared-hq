from __future__ import annotations

import asyncio
import hashlib
import json
import os
import signal
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nats
import psycopg
from glicko2.math import update_rating, rating_to_mu, rd_to_phi, mu_to_rating, phi_to_rd
from jsonschema import Draft202012Validator, FormatChecker
from nats.js.api import AckPolicy, ConsumerConfig
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from sheriff_core import (
    SheriffIntegrityError,
    apply_discipline,
    canonical_body_hash,
    classify_replay,
    execution_gate_for_score,
    remediation_path,
    stricter_gate,
)


STREAM_NAME = "ZB_AGENT_EVENTS"
SUBJECT = "zb.>"
DURABLE_NAME = "sheriff-v1"
BACKOFF_SECONDS = [1.0, 5.0, 15.0, 30.0, 60.0]

EVENTS = Counter("zb_sheriff_events_total", "Processed SHERIFF events", ["type"])
INCIDENTS = Counter("zb_sheriff_incidents_total", "Recorded incidents", ["agent", "class"])
REPEATS = Counter("zb_sheriff_repeat_incidents_total", "Repeated incidents", ["agent"])
DISCIPLINE = Gauge("zb_sheriff_discipline_score", "Current discipline score", ["agent"])
HOLDS = Gauge("zb_sheriff_active_holds", "Active hard/restricted holds", ["agent"])
LATENCY = Histogram("zb_sheriff_verdict_latency_seconds", "SHERIFF event processing latency")

_EVENT_VALIDATOR: Draft202012Validator | None = None


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"MISSING_ENV:{name}")
    return value


def _schema_path() -> Path:
    explicit = os.environ.get("SHERIFF_EVENT_SCHEMA_PATH", "").strip()
    if explicit:
        return Path(explicit)
    here = Path(__file__).resolve().parent
    candidates = [
        here / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json",
        here.parent / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("SHERIFF_AGENT_EVENT_V1.schema.json:NOT_FOUND")


def _validator() -> Draft202012Validator:
    global _EVENT_VALIDATOR
    if _EVENT_VALIDATOR is None:
        schema = json.loads(_schema_path().read_text(encoding="utf-8"))
        _EVENT_VALIDATOR = Draft202012Validator(schema, format_checker=FormatChecker())
    return _EVENT_VALIDATOR


def _validate_event(event: dict[str, Any]) -> None:
    errors = sorted(_validator().iter_errors(event), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        raise ValueError(f"EVENT_SCHEMA_VALIDATION_FAILED:{location}:{first.message}")


def _opa_request_sync(url: str, event: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps({"input": event}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    result = decoded.get("result")
    if not isinstance(result, dict) or "admit" not in result:
        raise RuntimeError("OPA_DECISION_INVALID")
    return result


async def request_opa_decision(event: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_opa_request_sync, _required_env("SHERIFF_OPA_URL"), event)


async def _ensure_event(conn: psycopg.AsyncConnection, event: dict[str, Any]) -> bool:
    body_hash = canonical_body_hash(event)
    async with conn.cursor() as cur:
        await cur.execute("SELECT body_hash FROM sheriff_events WHERE event_id = %s", (event["id"],))
        row = await cur.fetchone()
        if row:
            try:
                classify_replay(row[0], body_hash)
            except SheriffIntegrityError as exc:
                raise RuntimeError("EVENT_ID_BODY_HASH_CONFLICT") from exc
            return False

        await cur.execute(
            """
            INSERT INTO sheriff_events(event_id, body_hash, event_type, source, subject, event_time, raw_event)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                event["id"], body_hash, event["type"], event["source"], event["subject"],
                event["time"], json.dumps(event, separators=(",", ":")),
            ),
        )
    return True


async def _active_hold(conn: psycopg.AsyncConnection, agent_id: str) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT active_gate FROM sheriff_agent_scores WHERE agent_id = %s",
            (agent_id,),
        )
        row = await cur.fetchone()
    return bool(row and row[0] in {"HOLD", "HARD_HOLD", "RESTRICTED"})


async def _record_incident(
    conn: psycopg.AsyncConnection,
    event: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any] | None:
    incident_class = decision.get("incidentClass")
    if not incident_class:
        return None

    data = event["data"]
    agent_id = data.get("agentId")
    if not agent_id:
        raise RuntimeError("INCIDENT_AGENT_MISSING")
    task_ref = data.get("taskRef", event["subject"])
    error_signature = data.get("errorSignature") or f"{incident_class}:{task_ref}"

    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT COUNT(*) FROM sheriff_incidents WHERE agent_id = %s AND error_signature = %s",
            (agent_id, error_signature),
        )
        repeat_count = int((await cur.fetchone())[0])
        incident_id = f"INC:{event['id']}"
        verdict_id = f"VERDICT:{event['id']}"
        await cur.execute(
            """
            INSERT INTO sheriff_incidents(
                incident_id, event_id, agent_id, task_ref, error_signature, incident_class, repeat_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (incident_id, event["id"], agent_id, task_ref, error_signature, incident_class, repeat_count),
        )

        evidence = data.get("evidence") or [f"event:{event['id']}"]
        root_cause = (
            data.get("rootCause")
            or data.get("errorDetail")
            or decision.get("reason")
            or "POLICY_DECISION"
        )
        await cur.execute(
            """
            INSERT INTO sheriff_verdicts(
                verdict_id, incident_id, sheriff_id, root_cause, evidence,
                discipline_delta, merit_delta, hard_hold, decision
            ) VALUES (%s, %s, 'SHERIFF', %s, %s::jsonb, %s, %s, %s, %s::jsonb)
            """,
            (
                verdict_id,
                incident_id,
                root_cause,
                json.dumps(evidence),
                int(decision.get("disciplineDelta", 0)),
                int(decision.get("meritDelta", 0)),
                bool(decision.get("hardHold", False)),
                json.dumps(decision, separators=(",", ":")),
            ),
        )

        steps = remediation_path(incident_class, repeat_count)
        for index, step in enumerate(steps, start=1):
            await cur.execute(
                "INSERT INTO sheriff_remediations(verdict_id, step_order, step_code) VALUES (%s, %s, %s)",
                (verdict_id, index, step),
            )

        await cur.execute(
            "SELECT discipline_score, merit_points FROM sheriff_agent_scores WHERE agent_id = %s FOR UPDATE",
            (agent_id,),
        )
        score, merit = await cur.fetchone()
        new_score = apply_discipline(score, int(decision.get("disciplineDelta", 0)))
        repeat_gate = "RESTRICTED" if repeat_count >= 2 else ("HEIGHTENED_QC" if repeat_count >= 1 else "NONE")
        policy_gate = str(decision.get("executionGate") or ("HARD_HOLD" if decision.get("hardHold") else "NONE"))
        gate = stricter_gate(policy_gate, repeat_gate, execution_gate_for_score(new_score))
        await cur.execute(
            """
            UPDATE sheriff_agent_scores
            SET discipline_score = %s,
                merit_points = %s,
                active_gate = %s,
                incident_count = incident_count + 1,
                updated_at = NOW()
            WHERE agent_id = %s
            """,
            (new_score, merit + int(decision.get("meritDelta", 0)), gate, agent_id),
        )

    INCIDENTS.labels(agent=agent_id, **{"class": incident_class}).inc()
    if repeat_count:
        REPEATS.labels(agent=agent_id).inc()
    DISCIPLINE.labels(agent=agent_id).set(new_score)
    HOLDS.labels(agent=agent_id).set(1 if gate != "NONE" else 0)

    return {
        "verdictId": verdict_id,
        "agentId": agent_id,
        "taskRef": task_ref,
        "incidentClass": incident_class,
        "repeatCount": repeat_count,
        "disciplineScore": new_score,
        "remediation": list(steps),
        "executionGate": gate,
        "hardHold": gate == "HARD_HOLD",
    }


async def _rate_match(conn: psycopg.AsyncConnection, event: dict[str, Any]) -> None:
    data = event["data"]
    if not data.get("safetyGatePassed"):
        raise RuntimeError("SAFETY_GATE_BLOCKS_RATING")
    competitors = data.get("competitors") or []
    if len(competitors) != 2 or competitors[0] == competitors[1]:
        raise RuntimeError("RATING_MATCH_INVALID")
    a, b = competitors
    if await _active_hold(conn, a) or await _active_hold(conn, b):
        raise RuntimeError("ACTIVE_HOLD_BLOCKS_RATING")

    result = data.get("result") or {}
    score_a = float(result.get(a, -1))
    if score_a not in {0.0, 0.5, 1.0}:
        raise RuntimeError("RATING_MATCH_INVALID")
    score_b = 1.0 - score_a

    async with conn.cursor() as cur:
        await cur.execute("SELECT 1 FROM sheriff_league_matches WHERE match_id = %s", (data["matchId"],))
        if await cur.fetchone():
            return
        await cur.execute(
            "SELECT agent_id, rating, rating_deviation, volatility, rated_matches FROM sheriff_skill_ratings WHERE agent_id = ANY(%s) FOR UPDATE",
            ([a, b],),
        )
        rows = {row[0]: row[1:] for row in await cur.fetchall()}
        if a not in rows or b not in rows:
            raise RuntimeError("RATING_AGENT_UNKNOWN")

        ar, ard, av, amatches = rows[a]
        br, brd, bv, bmatches = rows[b]
        au = update_rating(
            rating_to_mu(ar), rd_to_phi(ard), av,
            [(rating_to_mu(br), rd_to_phi(brd), score_a)],
        )
        bu = update_rating(
            rating_to_mu(br), rd_to_phi(brd), bv,
            [(rating_to_mu(ar), rd_to_phi(ard), score_b)],
        )

        for agent_id, updated, rated_matches in ((a, au, amatches), (b, bu, bmatches)):
            await cur.execute(
                """
                UPDATE sheriff_skill_ratings
                SET rating = %s, rating_deviation = %s, volatility = %s,
                    rated_matches = %s, updated_at = NOW()
                WHERE agent_id = %s
                """,
                (
                    mu_to_rating(updated.mu), phi_to_rd(updated.phi), updated.sigma,
                    int(rated_matches) + 1, agent_id,
                ),
            )

        await cur.execute(
            """
            INSERT INTO sheriff_league_matches(match_id, competitor_a, competitor_b, score_a, safety_gate_passed, evidence, applied_at)
            VALUES (%s, %s, %s, %s, TRUE, %s::jsonb, NOW())
            """,
            (data["matchId"], a, b, score_a, json.dumps(data.get("evidence") or [])),
        )


def _build_verdict_event(source_event: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": f"sheriff:{source_event['id']}",
        "source": "zb://sheriff/v1",
        "type": "zb.sheriff.verdict",
        "subject": source_event["subject"],
        "time": datetime.now(timezone.utc).isoformat(),
        "datacontenttype": "application/json",
        "data": {
            "sheriffId": "SHERIFF",
            "agentId": verdict["agentId"],
            "verdictId": verdict["verdictId"],
            "taskRef": verdict["taskRef"],
            "incidentClass": verdict["incidentClass"],
            "evidence": [f"event:{source_event['id']}"],
            "repeatCount": verdict["repeatCount"],
            "disciplineScore": verdict["disciplineScore"],
            "remediation": verdict["remediation"],
            "executionGate": verdict["executionGate"],
            "hardHold": verdict["hardHold"],
        },
    }


async def _enqueue_verdict_outbox(
    conn: psycopg.AsyncConnection,
    source_event: dict[str, Any],
    verdict: dict[str, Any],
) -> None:
    emitted = _build_verdict_event(source_event, verdict)
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO sheriff_outbox(outbox_id, source_event_id, subject, payload)
            VALUES (%s, %s, 'zb.sheriff.verdict', %s::jsonb)
            ON CONFLICT (outbox_id) DO NOTHING
            """,
            (
                emitted["id"],
                source_event["id"],
                json.dumps(emitted, separators=(",", ":")),
            ),
        )


async def _flush_outbox(
    conn: psycopg.AsyncConnection,
    js: Any,
    source_event_id: str | None = None,
) -> None:
    query = """
        SELECT outbox_id, subject, payload
        FROM sheriff_outbox
        WHERE published_at IS NULL
    """
    params: tuple[Any, ...] = ()
    if source_event_id is not None:
        query += " AND source_event_id = %s"
        params = (source_event_id,)
    query += " ORDER BY created_at FOR UPDATE SKIP LOCKED"

    async with conn.cursor() as cur:
        await cur.execute(query, params)
        rows = await cur.fetchall()
        for outbox_id, subject, payload in rows:
            body = payload if isinstance(payload, dict) else json.loads(payload)
            await js.publish(
                subject,
                json.dumps(body, separators=(",", ":")).encode("utf-8"),
                headers={"Nats-Msg-Id": outbox_id},
            )
            await cur.execute(
                "UPDATE sheriff_outbox SET published_at = NOW() WHERE outbox_id = %s",
                (outbox_id,),
            )
    await conn.commit()


def _delivery_count(msg: Any) -> int:
    try:
        return int(msg.metadata.num_delivered)
    except Exception:
        return 1


async def _record_dead_letter(
    conn: psycopg.AsyncConnection,
    msg: Any,
    event: dict[str, Any] | None,
    exc: Exception,
) -> None:
    digest = hashlib.sha256(msg.data).hexdigest()
    metadata = msg.metadata
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO sheriff_dead_letters(
                message_hash, event_id, subject, stream_sequence, consumer_sequence,
                deliveries, raw_payload, error_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stream_sequence, consumer_sequence) DO NOTHING
            """,
            (
                digest,
                event.get("id") if isinstance(event, dict) else None,
                msg.subject,
                metadata.sequence.stream,
                metadata.sequence.consumer,
                metadata.num_delivered,
                msg.data.decode("utf-8", errors="replace"),
                f"{type(exc).__name__}:{exc}"[:4000],
            ),
        )


async def run() -> None:
    nats_url = _required_env("SHERIFF_NATS_URL")
    postgres_dsn = _required_env("SHERIFF_POSTGRES_DSN")
    metrics_port = int(os.environ.get("SHERIFF_METRICS_PORT", "9464"))
    start_http_server(metrics_port)

    nc = await nats.connect(nats_url)
    js = nc.jetstream()
    try:
        await js.add_stream(name=STREAM_NAME, subjects=[SUBJECT])
    except Exception as exc:
        if "stream name already in use" not in str(exc).lower() and "stream already in use" not in str(exc).lower():
            raise

    async def handle(msg: Any) -> None:
        started = asyncio.get_running_loop().time()
        event: dict[str, Any] | None = None
        conn: psycopg.AsyncConnection | None = None
        try:
            event = json.loads(msg.data.decode("utf-8"))
            _validate_event(event)
            decision = await request_opa_decision(event)
            if not decision.get("admit"):
                raise RuntimeError(f"OPA_REJECTED_EVENT:{decision.get('reason', 'UNKNOWN')}")

            conn = await psycopg.AsyncConnection.connect(postgres_dsn)
            verdict = None
            inserted = await _ensure_event(conn, event)
            if inserted:
                if event["type"] == "zb.league.match":
                    await _rate_match(conn, event)
                else:
                    verdict = await _record_incident(conn, event, decision)
                    if verdict is not None:
                        await _enqueue_verdict_outbox(conn, event, verdict)

            await conn.commit()
            await _flush_outbox(conn, js, event["id"])
            await msg.ack()
            EVENTS.labels(type=event["type"]).inc()
        except Exception as exc:
            if conn is not None:
                try:
                    await conn.rollback()
                except Exception:
                    pass

            deliveries = _delivery_count(msg)
            if deliveries >= 5:
                dead_conn: psycopg.AsyncConnection | None = None
                try:
                    dead_conn = await psycopg.AsyncConnection.connect(postgres_dsn)
                    await _record_dead_letter(dead_conn, msg, event, exc)
                    await dead_conn.commit()
                    await msg.term()
                except Exception:
                    if dead_conn is not None:
                        try:
                            await dead_conn.rollback()
                        except Exception:
                            pass
                    await msg.nak(delay=BACKOFF_SECONDS[-1])
                finally:
                    if dead_conn is not None:
                        await dead_conn.close()
            else:
                await msg.nak(delay=BACKOFF_SECONDS[min(deliveries - 1, len(BACKOFF_SECONDS) - 1)])
        finally:
            if conn is not None:
                await conn.close()
            LATENCY.observe(asyncio.get_running_loop().time() - started)

    consumer_config = ConsumerConfig(
        durable_name=DURABLE_NAME,
        ack_policy=AckPolicy.EXPLICIT,
        max_deliver=5,
        backoff=BACKOFF_SECONDS,
    )
    await js.subscribe(
        SUBJECT,
        cb=handle,
        manual_ack=True,
        config=consumer_config,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass
    await stop_event.wait()
    await nc.drain()


if __name__ == "__main__":
    asyncio.run(run())
