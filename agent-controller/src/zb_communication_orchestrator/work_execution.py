from __future__ import annotations

from dataclasses import dataclass
import re

from .execution import StartResult

_SAFE_DELIVERY_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


@dataclass(frozen=True)
class WorkRunContext:
    webhook_delivery_id: str | None
    role_phase_started: bool


def start_current_work_run(context: WorkRunContext) -> StartResult:
    """Bind the current physical Work webhook run to one logical-role execution.

    The adapter may call this only after the source message has passed admission,
    bindings and durable RECEIVED read-back. Missing/unsafe physical delivery
    identity fails closed; no synthetic fallback execution ID is permitted.
    """
    delivery_id = context.webhook_delivery_id
    if context.role_phase_started is not True:
        return StartResult(False, None, None, None)
    if not isinstance(delivery_id, str) or not _SAFE_DELIVERY_ID.fullmatch(delivery_id):
        return StartResult(False, None, None, None)
    return StartResult(True, f"work-event:{delivery_id}", None, None)
