from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import time
from typing import Callable

from zb_local_controller.task_contract import TaskContractError, parse_task

from .config import BridgeConfig
from .contracts import (
    ReferenceContractError,
    ReferenceDelivery,
    format_reference_failed,
    format_reference_ready,
    latest_agent_terminal_state,
    parse_delivery_event,
)
from .journal import DeliveryReceipt, JournalConflict, ReferenceJournal
from .local_delivery import ReferenceValidationError, validate_delivery_source
from .publisher import PublishError, publish_reference, quarantine_delivery


@dataclass(frozen=True)
class BridgeCycleSummary:
    discovered: int
    waiting: int
    accepted: int
    rejected: int
    skipped: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _delivery_metadata_sha256(delivery: ReferenceDelivery) -> str:
    canonical = "\n".join((
        delivery.task_id,
        delivery.delivery_id,
        delivery.drive_folder_id,
        delivery.drive_file_id,
        delivery.source_file_name,
        str(delivery.size_bytes),
        delivery.source_sha256,
        delivery.mime_type,
        delivery.source_status,
        delivery.transport,
    ))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _reference_event_state(comments: tuple[str, ...], task_id: str, delivery_id: str) -> str | None:
    state = None
    for body in comments:
        if not isinstance(body, str):
            continue
        lines = body.splitlines()
        if not lines or lines[0].strip() != "ZB_REFERENCE_EVENT_V1":
            continue
        fields: dict[str, str] = {}
        for raw in lines[1:]:
            if not raw.strip():
                continue
            if "=" not in raw:
                fields = {}
                break
            key, value = (part.strip() for part in raw.split("=", 1))
            if key in fields:
                fields = {}
                break
            fields[key] = value
        if fields.get("TASK_ID") == task_id and fields.get("DELIVERY_ID") == delivery_id:
            candidate = fields.get("STATE")
            if candidate in {"REFERENCE_READY", "REFERENCE_FAILED"}:
                state = candidate
    return state


class ReferenceBridge:
    def __init__(
        self,
        config: BridgeConfig,
        github,
        journal: ReferenceJournal | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.config = config
        self.github = github
        self.journal = journal or ReferenceJournal(config.runtime_root)
        self._clock = clock
        self._waiting_since: dict[str, float] = {}
        self._waiting_binding: dict[str, str] = {}

    def _clear_wait(self, delivery_id: str) -> None:
        self._waiting_since.pop(delivery_id, None)
        self._waiting_binding.pop(delivery_id, None)

    def _source_path_if_safe(self, delivery: ReferenceDelivery) -> Path | None:
        if any(ch in delivery.delivery_id for ch in ("/", "\\", "..")):
            return None
        if Path(delivery.source_file_name).name != delivery.source_file_name:
            return None
        path = Path(self.config.drive_sync_root) / delivery.delivery_id / delivery.source_file_name
        try:
            if path.is_file() and not path.is_symlink():
                return path
        except OSError:
            pass
        return None

    def _quarantine_if_possible(self, delivery: ReferenceDelivery, error_code: str) -> None:
        path = self._source_path_if_safe(delivery)
        if path is not None:
            quarantine_delivery(self.config, delivery, path, error_code)

    def _post_failed(self, issue_number: int, task_id: str, delivery: ReferenceDelivery, code: str) -> None:
        self.github.post_reference_event(issue_number, format_reference_failed(task_id, delivery.delivery_id, code))

    def _reject(self, issue_number: int, task_id: str, delivery: ReferenceDelivery, code: str, *, persist: bool = True, quarantine: bool = True) -> None:
        self._clear_wait(delivery.delivery_id)
        if quarantine:
            self._quarantine_if_possible(delivery, code)
        if persist:
            self.journal.append(DeliveryReceipt(
                delivery.delivery_id,
                task_id,
                delivery.source_sha256,
                "REJECTED",
                issue_number,
                _utc_now(),
                code,
                _delivery_metadata_sha256(delivery),
            ))
        self._post_failed(issue_number, task_id, delivery, code)

    def run_once(self) -> BridgeCycleSummary:
        issues = self.github.list_task_issues()
        waiting = accepted = rejected = skipped = 0

        for issue in issues:
            try:
                task = parse_task(issue.body)
            except TaskContractError:
                skipped += 1
                continue
            if task.reference != "LOCAL_INBOX":
                skipped += 1
                continue

            deliveries: list[ReferenceDelivery] = []
            malformed_delivery = False
            for comment in issue.comments:
                try:
                    delivery = parse_delivery_event(comment)
                except ReferenceContractError:
                    if isinstance(comment, str) and comment.splitlines() and comment.splitlines()[0].strip() == "ZB_REFERENCE_DELIVERY_V1":
                        malformed_delivery = True
                    continue
                if delivery is not None:
                    deliveries.append(delivery)
            if not deliveries:
                skipped += 1
                continue

            terminal = latest_agent_terminal_state(issue.comments, task.task_id)
            for delivery in deliveries:
                event_state = _reference_event_state(issue.comments, task.task_id, delivery.delivery_id)
                binding = _delivery_metadata_sha256(delivery)
                existing = self.journal.lookup_delivery(delivery.delivery_id)

                if existing is not None:
                    self._clear_wait(delivery.delivery_id)
                    if (
                        existing.task_id != task.task_id
                        or existing.task_id != delivery.task_id
                        or existing.source_sha256 != delivery.source_sha256
                        or existing.delivery_metadata_sha256 is None
                        or existing.delivery_metadata_sha256 != binding
                    ):
                        self._quarantine_if_possible(delivery, "REFERENCE_DELIVERY_ID_CONFLICT")
                        self._post_failed(issue.number, task.task_id, delivery, "REFERENCE_DELIVERY_ID_CONFLICT")
                        rejected += 1
                        continue
                    if existing.state == "ACCEPTED":
                        if event_state != "REFERENCE_READY":
                            self.github.post_reference_event(issue.number, format_reference_ready(task.task_id, delivery.delivery_id, delivery.source_sha256))
                        else:
                            skipped += 1
                        continue
                    if existing.state == "REJECTED":
                        if event_state != "REFERENCE_FAILED":
                            self._post_failed(issue.number, task.task_id, delivery, existing.error_code or "REFERENCE_PUBLISH_FAILED")
                        else:
                            skipped += 1
                        continue

                waiting_binding = self._waiting_binding.get(delivery.delivery_id)
                if waiting_binding is not None and waiting_binding != binding:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_DELIVERY_ID_CONFLICT", quarantine=True)
                    rejected += 1
                    continue

                if delivery.task_id != task.task_id:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_ID_MISMATCH", quarantine=False)
                    rejected += 1
                    continue

                task_receipt = self.journal.lookup_task(task.task_id)
                if task_receipt is not None and task_receipt.state == "ACCEPTED" and task_receipt.source_sha256 != delivery.source_sha256:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_CONFLICT", quarantine=True)
                    rejected += 1
                    continue

                if terminal is not None:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_TERMINAL", quarantine=False)
                    rejected += 1
                    continue

                try:
                    source = validate_delivery_source(self.config, delivery)
                except ReferenceValidationError as exc:
                    self._reject(issue.number, task.task_id, delivery, exc.code, quarantine=True)
                    rejected += 1
                    continue
                if source is None:
                    now = self._clock()
                    started = self._waiting_since.setdefault(delivery.delivery_id, now)
                    self._waiting_binding.setdefault(delivery.delivery_id, binding)
                    if now - started >= self.config.cloud_retry_timeout_seconds:
                        self._reject(issue.number, task.task_id, delivery, "REFERENCE_DRIVE_FOLDER_TIMEOUT", quarantine=False)
                        rejected += 1
                    else:
                        waiting += 1
                    continue

                try:
                    publish_reference(self.config, delivery, source)
                except PublishError as exc:
                    self._reject(issue.number, task.task_id, delivery, exc.code, quarantine=True)
                    rejected += 1
                    continue
                self._clear_wait(delivery.delivery_id)
                try:
                    self.journal.append(DeliveryReceipt(
                        delivery.delivery_id,
                        task.task_id,
                        delivery.source_sha256,
                        "ACCEPTED",
                        issue.number,
                        _utc_now(),
                        None,
                        binding,
                    ))
                except JournalConflict as exc:
                    self._quarantine_if_possible(delivery, exc.code)
                    self._post_failed(issue.number, task.task_id, delivery, exc.code)
                    rejected += 1
                    continue
                accepted += 1
                self.github.post_reference_event(issue.number, format_reference_ready(task.task_id, delivery.delivery_id, delivery.source_sha256))

        return BridgeCycleSummary(len(issues), waiting, accepted, rejected, skipped)
