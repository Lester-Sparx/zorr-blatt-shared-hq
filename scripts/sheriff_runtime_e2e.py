from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import time
import urllib.request
from typing import Any

import nats
import psycopg


NATS_URL = os.environ.get("SHERIFF_NATS_URL", "nats://sheriff:sheriff-dev-only@nats:4222")
POSTGRES_DSN = os.environ.get(
    "SHERIFF_POSTGRES_DSN",
    "postgresql://sheriff:sheriff-dev-only@postgres:5432/sheriff",
)
STREAM_NAME = "ZB_AGENT_EVENTS"
SUBJECT = "zb.agent.result"


def _event(kind: str) -> dict[str, Any]:
    common = {
        "specversion": "1.0",
        "source": "zb://runtime-e2e",
        "type": "zb.agent.result",
        "datacontenttype": "application/json",
    }
    if kind == "honest":
        return {
            **common,
            "id": "E2E-HONEST-FAIL-1",
            "subject": "task:E2E-HONEST",
            "time": "2026-08-29T09:20:00Z",
            "data": {
                "agentId": "LESTER",
                "taskRef": "E2E-HONEST",
                "executionId": "E2E-HONEST-EXEC-1",
                "status": "FAIL",
                "evidence": ["e2e:honest-fail"],
                "errorSignature": "E2E_UPSTREAM_FAILURE",
                "incidentAttribution": "SYSTEM_UPSTREAM",
                "selfCaught": False,
                "processViolation": False,
                "safetyViolation": False,
            },
        }
    if kind == "correctness":
        return {
            **common,
            "id": "E2E-CORRECTNESS-1",
            "subject": "task:E2E-CORRECTNESS",
            "time": "2026-08-29T09:21:00Z",
            "data": {
                "agentId": "DUNCAN",
                "taskRef": "E2E-CORRECTNESS",
                "executionId": "E2E-CORRECTNESS-EXEC-1",
                "status": "FAIL",
                "evidence": ["e2e:correctness-failure"],
                "errorSignature": "E2E_CORRECTNESS_FAILURE",
                "incidentAttribution": "AGENT_CORRECTNESS",
                "rootCause": "E2E deterministic correctness fault",
                "selfCaught": False,
                "processViolation": False,
                "safetyViolation": False,
            },
        }
    if kind == "falsepass":
        return {
            **common,
            "id": "E2E-FALSE-PASS-1",
            "subject": "task:E2E-FALSE-PASS",
            "time": "2026-08-29T09:22:00Z",
            "data": {
                "agentId": "DJANGO",
                "taskRef": "E2E-FALSE-PASS",
                "executionId": "E2E-FALSE-PASS-EXEC-1",
                "status": "PASS",
                "evidence": ["e2e:false-pass-evidence"],
                "verifiedPass": False,
                "errorSignature": "E2E_FALSE_PASS",
                "incidentAttribution": "NONE",
                "selfCaught": False,
                "processViolation": False,
                "safetyViolation": False,
            },
        }
    raise SystemExit(f"unknown kind: {kind}")


async def _db_fetchone(sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
    conn = await psycopg.AsyncConnection.connect(POSTGRES_DSN)
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            return await cur.fetchone()
    finally:
        await conn.close()


async def _db_scalar(sql: str, params: tuple[Any, ...] = ()) -> Any:
    row = await _db_fetchone(sql, params)
    return None if row is None else row[0]


async def _wait_until(predicate, label: str, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if await predicate():
                print(f"{label} = PASS")
                return
        except Exception as exc:  # readiness is intentionally retryable
            last_error = exc
        await asyncio.sleep(1.0)
    if last_error:
        raise RuntimeError(f"{label}=TIMEOUT:{type(last_error).__name__}:{last_error}")
    raise RuntimeError(f"{label}=TIMEOUT")


def _url_ready(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def _tcp_ready(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


async def health() -> None:
    async def db_ok() -> bool:
        return await _db_scalar("SELECT 1") == 1

    async def nats_ok() -> bool:
        nc = await nats.connect(NATS_URL, connect_timeout=3)
        try:
            js = nc.jetstream()
            await js.stream_info(STREAM_NAME)
            return True
        finally:
            await nc.close()

    await _wait_until(db_ok, "POSTGRES_READY")
    await _wait_until(nats_ok, "JETSTREAM_READY")

    http_checks = {
        "OPA_READY": "http://opa:8181/health",
        "NATS_HTTP_READY": "http://nats:8222/healthz",
        "PROMETHEUS_READY": "http://prometheus:9090/-/ready",
        "LOKI_READY": "http://loki:3100/ready",
        "GRAFANA_READY": "http://grafana:3000/api/health",
        "FORGEJO_READY": "http://forgejo:3000/",
        "WORKER_METRICS_READY": "http://sheriff-worker:9464/metrics",
    }
    for label, url in http_checks.items():
        async def ready(url=url) -> bool:
            return await asyncio.to_thread(_url_ready, url)
        await _wait_until(ready, label)

    async def otel_ok() -> bool:
        return await asyncio.to_thread(_tcp_ready, "otel-collector", 4317)

    await _wait_until(otel_ok, "OTEL_READY")
    print("SHERIFF_STACK_HEALTH = PASS")


async def publish(kind: str) -> None:
    event = _event(kind)
    nc = await nats.connect(NATS_URL, connect_timeout=5)
    try:
        js = nc.jetstream()
        await js.stream_info(STREAM_NAME)
        ack = await js.publish(SUBJECT, json.dumps(event, separators=(",", ":")).encode("utf-8"))
        if not ack or ack.stream != STREAM_NAME:
            raise RuntimeError("JETSTREAM_PUBLISH_ACK_INVALID")
        print(f"PUBLISH_{kind.upper()} = PASS")
        print(f"EVENT_ID = {event['id']}")
    finally:
        await nc.drain()


async def assert_absent(kind: str) -> None:
    event = _event(kind)
    count = int(await _db_scalar("SELECT COUNT(*) FROM sheriff_events WHERE event_id = %s", (event["id"],)))
    if count != 0:
        raise AssertionError(f"EVENT_UNEXPECTEDLY_PROCESSED:{event['id']}:{count}")
    print(f"ABSENT_{kind.upper()} = PASS")


async def _wait_event(event_id: str) -> None:
    async def exists() -> bool:
        return int(await _db_scalar("SELECT COUNT(*) FROM sheriff_events WHERE event_id = %s", (event_id,))) == 1
    await _wait_until(exists, f"EVENT_{event_id}_RECORDED")


async def assert_honest() -> None:
    event = _event("honest")
    await _wait_event(event["id"])
    incident_count = int(await _db_scalar("SELECT COUNT(*) FROM sheriff_incidents WHERE event_id = %s", (event["id"],)))
    score = await _db_fetchone(
        "SELECT discipline_score, merit_points, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id = 'LESTER'"
    )
    if incident_count != 0:
        raise AssertionError(f"HONEST_FAIL_CREATED_INCIDENT:{incident_count}")
    if score != (100, 0, "NONE", 0):
        raise AssertionError(f"HONEST_FAIL_SCORE_MUTATED:{score}")
    print("HONEST_FAIL_ZERO_PENALTY = PASS")


async def assert_correctness() -> None:
    event = _event("correctness")
    await _wait_event(event["id"])

    async def verdict_visible() -> bool:
        return int(await _db_scalar("SELECT COUNT(*) FROM sheriff_verdicts v JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s", (event["id"],))) == 1
    await _wait_until(verdict_visible, "CORRECTNESS_VERDICT_RECORDED")

    incident = await _db_fetchone(
        "SELECT incident_class, repeat_count FROM sheriff_incidents WHERE event_id = %s",
        (event["id"],),
    )
    verdict = await _db_fetchone(
        "SELECT v.discipline_delta, v.hard_hold FROM sheriff_verdicts v JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s",
        (event["id"],),
    )
    score = await _db_fetchone(
        "SELECT discipline_score, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id = 'DUNCAN'"
    )
    remediation_count = int(await _db_scalar(
        "SELECT COUNT(*) FROM sheriff_remediations r JOIN sheriff_verdicts v ON v.verdict_id = r.verdict_id JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s",
        (event["id"],),
    ))
    published = await _db_scalar(
        "SELECT published_at IS NOT NULL FROM sheriff_outbox WHERE source_event_id = %s",
        (event["id"],),
    )
    await _wait_event(f"sheriff:{event['id']}")

    if incident != ("I1_CORRECTNESS", 0):
        raise AssertionError(f"CORRECTNESS_INCIDENT_BAD:{incident}")
    if verdict != (-2, False):
        raise AssertionError(f"CORRECTNESS_VERDICT_BAD:{verdict}")
    if score != (98, "NONE", 1):
        raise AssertionError(f"CORRECTNESS_SCORE_BAD:{score}")
    if remediation_count < 3:
        raise AssertionError(f"CORRECTNESS_REMEDIATION_MISSING:{remediation_count}")
    if published is not True:
        raise AssertionError(f"CORRECTNESS_OUTBOX_NOT_PUBLISHED:{published}")
    print("CORRECTNESS_INCIDENT_REMEDIATION = PASS")


async def assert_replay() -> None:
    event = _event("correctness")
    await _wait_event(event["id"])
    await asyncio.sleep(2.0)
    event_rows = int(await _db_scalar("SELECT COUNT(*) FROM sheriff_events WHERE event_id = %s", (event["id"],)))
    incident_rows = int(await _db_scalar("SELECT COUNT(*) FROM sheriff_incidents WHERE event_id = %s", (event["id"],)))
    verdict_rows = int(await _db_scalar(
        "SELECT COUNT(*) FROM sheriff_verdicts v JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s",
        (event["id"],),
    ))
    score = await _db_fetchone(
        "SELECT discipline_score, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id = 'DUNCAN'"
    )
    if (event_rows, incident_rows, verdict_rows) != (1, 1, 1):
        raise AssertionError(f"REPLAY_DUPLICATED_DURABLE_STATE:{event_rows, incident_rows, verdict_rows}")
    if score != (98, "NONE", 1):
        raise AssertionError(f"REPLAY_DOUBLE_PENALTY:{score}")
    print("RESTART_REPLAY_IDEMPOTENT = PASS")


async def assert_falsepass() -> None:
    event = _event("falsepass")
    await _wait_event(event["id"])

    async def incident_visible() -> bool:
        return int(await _db_scalar("SELECT COUNT(*) FROM sheriff_incidents WHERE event_id = %s", (event["id"],))) == 1
    await _wait_until(incident_visible, "FALSE_PASS_INCIDENT_RECORDED")

    incident = await _db_fetchone(
        "SELECT incident_class, repeat_count FROM sheriff_incidents WHERE event_id = %s",
        (event["id"],),
    )
    verdict = await _db_fetchone(
        "SELECT v.discipline_delta, v.hard_hold FROM sheriff_verdicts v JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s",
        (event["id"],),
    )
    score = await _db_fetchone(
        "SELECT discipline_score, active_gate, incident_count FROM sheriff_agent_scores WHERE agent_id = 'DJANGO'"
    )
    remediation_count = int(await _db_scalar(
        "SELECT COUNT(*) FROM sheriff_remediations r JOIN sheriff_verdicts v ON v.verdict_id = r.verdict_id JOIN sheriff_incidents i ON i.incident_id = v.incident_id WHERE i.event_id = %s",
        (event["id"],),
    ))
    await _wait_event(f"sheriff:{event['id']}")

    if incident != ("I3_CRITICAL_INTEGRITY", 0):
        raise AssertionError(f"FALSE_PASS_INCIDENT_BAD:{incident}")
    if verdict != (-20, False):
        raise AssertionError(f"FALSE_PASS_VERDICT_BAD:{verdict}")
    if score != (80, "HOLD", 1):
        raise AssertionError(f"FALSE_PASS_HOLD_BAD:{score}")
    if remediation_count < 4:
        raise AssertionError(f"FALSE_PASS_REMEDIATION_MISSING:{remediation_count}")
    print("FALSE_PASS_CRITICAL_HOLD = PASS")


async def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("health")
    p_publish = sub.add_parser("publish")
    p_publish.add_argument("kind", choices=["honest", "correctness", "falsepass"])
    p_absent = sub.add_parser("assert-absent")
    p_absent.add_argument("kind", choices=["honest", "correctness", "falsepass"])
    p_assert = sub.add_parser("assert")
    p_assert.add_argument("kind", choices=["honest", "correctness", "replay", "falsepass"])
    args = parser.parse_args()

    if args.command == "health":
        await health()
    elif args.command == "publish":
        await publish(args.kind)
    elif args.command == "assert-absent":
        await assert_absent(args.kind)
    elif args.command == "assert":
        await {
            "honest": assert_honest,
            "correctness": assert_correctness,
            "replay": assert_replay,
            "falsepass": assert_falsepass,
        }[args.kind]()


if __name__ == "__main__":
    asyncio.run(main())
