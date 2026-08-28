from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


ALLOWED_OVERALL_STATUSES = {"WORKING", "WAITING", "BLOCKED", "FAIL", "DONE", "UNKNOWN"}
ALLOWED_ROW_STATUSES = ALLOWED_OVERALL_STATUSES | {"STALE"}
ALLOWED_AGENTS = {"JINGO", "LESTER", "DUNCAN", "SALVADOR", "LYNCH", "MAO", "CHARLIE", "MEMORO"}
REQUIRED_SCALARS = {
    "UPDATED_AT",
    "OVERALL_STATUS",
    "SPARX_ACTION",
    "WHY",
    "SCOUT_LAST_CHECK",
    "SCOUT_SUMMARY",
}


@dataclass(frozen=True)
class AgentView:
    name: str
    status: str
    doing: str
    done: str | None
    blocker: str | None
    next: str


@dataclass(frozen=True)
class GateView:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class OwnerSnapshot:
    updated_at: datetime
    overall_status: str
    sparx_action: str | None
    why: str
    scout_last_check: datetime | None
    scout_summary: str | None
    agents: dict[str, AgentView]
    gates: dict[str, GateView]
    is_stale: bool


def _none(value: str) -> str | None:
    return None if value == "NONE" else value


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("TIMESTAMP_NOT_UTC")
    return parsed.astimezone(timezone.utc)


def _parse_comment(body: str, now_utc: datetime) -> OwnerSnapshot:
    lines = body.splitlines()
    if not lines or lines[0].strip() != "ZB_OWNER_VIEW_V0":
        raise ValueError("MARKER_INVALID")
    if now_utc.tzinfo is None:
        raise ValueError("NOW_NOT_AWARE")

    scalars: dict[str, str] = {}
    agents: dict[str, AgentView] = {}
    gates: dict[str, GateView] = {}
    for raw in lines[1:]:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("AGENT = "):
            parts = [part.strip() for part in line.removeprefix("AGENT = ").split("|")]
            if len(parts) != 6:
                raise ValueError("AGENT_INVALID")
            name, status, doing, done, blocker, next_action = parts
            if name not in ALLOWED_AGENTS or status not in ALLOWED_ROW_STATUSES or name in agents:
                raise ValueError("AGENT_INVALID")
            if not doing or not next_action:
                raise ValueError("AGENT_INVALID")
            agents[name] = AgentView(name, status, doing, _none(done), _none(blocker), next_action)
            continue
        if line.startswith("GATE = "):
            parts = [part.strip() for part in line.removeprefix("GATE = ").split("|")]
            if len(parts) != 3:
                raise ValueError("GATE_INVALID")
            name, status, reason = parts
            if not name or status not in ALLOWED_ROW_STATUSES or not reason or name in gates:
                raise ValueError("GATE_INVALID")
            gates[name] = GateView(name, status, reason)
            continue
        if " = " not in line:
            raise ValueError("LINE_INVALID")
        key, value = line.split(" = ", 1)
        if key not in REQUIRED_SCALARS or key in scalars or not value:
            raise ValueError("SCALAR_INVALID")
        scalars[key] = value

    if set(scalars) != REQUIRED_SCALARS or set(agents) != ALLOWED_AGENTS or not gates:
        raise ValueError("REQUIRED_DATA_MISSING")
    if scalars["OVERALL_STATUS"] not in ALLOWED_OVERALL_STATUSES:
        raise ValueError("STATUS_INVALID")

    updated_at = _utc(scalars["UPDATED_AT"])
    scout_raw = scalars["SCOUT_LAST_CHECK"]
    scout_last_check = None if scout_raw == "UNKNOWN" else _utc(scout_raw)
    now = now_utc.astimezone(timezone.utc)
    return OwnerSnapshot(
        updated_at=updated_at,
        overall_status=scalars["OVERALL_STATUS"],
        sparx_action=_none(scalars["SPARX_ACTION"]),
        why=scalars["WHY"],
        scout_last_check=scout_last_check,
        scout_summary=_none(scalars["SCOUT_SUMMARY"]),
        agents=agents,
        gates=gates,
        is_stale=now - updated_at > timedelta(hours=2),
    )


def parse_owner_view_comments(comments: tuple[str, ...], now_utc: datetime) -> OwnerSnapshot | None:
    for body in reversed(comments):
        try:
            return _parse_comment(body, now_utc)
        except (AttributeError, TypeError, ValueError):
            continue
    return None
