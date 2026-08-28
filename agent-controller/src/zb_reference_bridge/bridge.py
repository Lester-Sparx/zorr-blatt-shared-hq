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


def _comment_body(comment) -> str:
    return comment.body if hasattr(comment, "body") else comment


def _comment_id(comment) -> str | None:
    value = getattr(comment, "id", None)
    return value if isinstance(value, str) and value else None


def _has_reference_event(
    comments: list[str],
    task_id: str,
    delivery_id: str,
    state: str,
    error_code: str | None = None,
    source_comment_id: str | None = None,
    delivery_metadata_sha256: str | None = None,
    require_unbound_source: bool = False,
) -> bool:
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
            if (
                fields.get("STATE") == state
                and (error_code is None or fields.get("ERROR_CODE") == error_code)
                and (source_comment_id is None or fields.get("SOURCE_COMMENT_ID") == source_comment_id)
                and (delivery_metadata_sha256 is None or fields.get("DELIVERY_METADATA_SHA256") == delivery_metadata_sha256)
                and (not require_unbound_source or ("SOURCE_COMMENT_ID" not in fields and "DELIVERY_METADATA_SHA256" not in fields))
            ):
                return True
    return False


def _has_following_reference_event(
    comments,
    comment_id: str | None,
    delivery_metadata_sha256: str,
    task_id: str,
    delivery_id: str,
    state: str,
    error_code: str,
) -> bool:
    bodies = [_comment_body(comment) for comment in comments]
    if comment_id is not None and _has_reference_event(
        bodies,
        task_id,
        delivery_id,
        state,
        error_code,
        source_comment_id=comment_id,
    ):
        return True
    if _has_reference_event(
        bodies,
        task_id,
        delivery_id,
        state,
        error_code,
        delivery_metadata_sha256=delivery_metadata_sha256,
    ):
        return True
    if comment_id is None:
        return _has_reference_event(
            bodies,
            task_id,
            delivery_id,
            state,
            error_code,
        )
    found_source = False
    for comment in comments:
        if not found_source:
            found_source = _comment_id(comment) == comment_id
            continue
        body = _comment_body(comment)
        if isinstance(body, str) and body.splitlines() and body.splitlines()[0].strip() == "ZB_REFERENCE_DELIVERY_V1":
            try:
                later_delivery = parse_delivery_event(body)
            except ReferenceContractError:
                return False
            if later_delivery is not None and _delivery_metadata_sha256(later_delivery) == delivery_metadata_sha256:
                continue
            return False
        if _has_reference_event(
            [body],
            task_id,
            delivery_id,
            state,
            error_code,
            require_unbound_source=True,
        ):
            return True
    return False


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

    def _post_failed(
        self,
        issue_number: int,
        task_id: str,
        delivery: ReferenceDelivery,
        code: str,
        observed_comments: list[str] | None = None,
        source_comment_id: str | None = None,
        delivery_metadata_sha256: str | None = None,
    ) -> None:
        body = format_reference_failed(
            task_id,
            delivery.delivery_id,
            code,
            source_comment_id=source_comment_id,
            delivery_metadata_sha256=delivery_metadata_sha256,
        )
        self.github.post_reference_event(issue_number, body)
        if observed_comments is not None:
            observed_comments.append(body)

    def _reject(self, issue_number: int, task_id: str, delivery: ReferenceDelivery, code: str, *, comment_id: str | None = None, observed_comments: list[str] | None = None, persist: bool = True, quarantine: bool = True) -> None:
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
        self._post_failed(
            issue_number,
            task_id,
            delivery,
            code,
            observed_comments,
            comment_id,
            _delivery_metadata_sha256(delivery),
        )
        if comment_id is not None:
            self.journal.mark_comment_consumed(comment_id)

    def run_once(self) -> BridgeCycleSummary:
        issues = self.github.list_task_issues()
        waiting = accepted = rejected = skipped = 0

        for issue in issues:
            comment_bodies = [_comment_body(comment) for comment in issue.comments]
            try:
                task = parse_task(issue.body)
            except TaskContractError:
                skipped += 1
                continue
            if task.reference != "LOCAL_INBOX":
                skipped += 1
                continue

            deliveries: list[tuple[str | None, ReferenceDelivery]] = []
            malformed_delivery = False
            for comment in issue.comments:
                body = _comment_body(comment)
                try:
                    delivery = parse_delivery_event(body)
                except ReferenceContractError:
                    if isinstance(body, str) and body.splitlines() and body.splitlines()[0].strip() == "ZB_REFERENCE_DELIVERY_V1":
                        malformed_delivery = True
                    continue
                if delivery is not None:
                    deliveries.append((_comment_id(comment), delivery))
            if not deliveries:
                skipped += 1
                continue

            terminal = latest_agent_terminal_state(tuple(comment_bodies), task.task_id)
            emitted_conflict_bindings: set[str] = set()
            for comment_id, delivery in deliveries:
                if comment_id is not None and self.journal.is_comment_consumed(comment_id):
                    skipped += 1
                    continue
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
                        if (
                            binding not in emitted_conflict_bindings
                            and not _has_following_reference_event(
                                issue.comments,
                                comment_id,
                                binding,
                                task.task_id,
                                delivery.delivery_id,
                                "REFERENCE_FAILED",
                                "REFERENCE_DELIVERY_ID_CONFLICT",
                            )
                        ):
                            self._post_failed(
                                issue.number,
                                task.task_id,
                                delivery,
                                "REFERENCE_DELIVERY_ID_CONFLICT",
                                comment_bodies,
                                comment_id,
                                binding,
                            )
                            emitted_conflict_bindings.add(binding)
                        if comment_id is not None:
                            self.journal.mark_comment_consumed(comment_id)
                        rejected += 1
                        continue
                    if existing.state == "ACCEPTED":
                        if not _has_reference_event(comment_bodies, task.task_id, delivery.delivery_id, "REFERENCE_READY"):
                            body = format_reference_ready(task.task_id, delivery.delivery_id, delivery.source_sha256)
                            self.github.post_reference_event(issue.number, body)
                            comment_bodies.append(body)
                        else:
                            skipped += 1
                        if comment_id is not None:
                            self.journal.mark_comment_consumed(comment_id)
                        continue
                    if existing.state == "REJECTED":
                        error_code = existing.error_code or "REFERENCE_PUBLISH_FAILED"
                        if not _has_reference_event(comment_bodies, task.task_id, delivery.delivery_id, "REFERENCE_FAILED", error_code):
                            self._post_failed(issue.number, task.task_id, delivery, error_code, comment_bodies, comment_id, binding)
                        else:
                            skipped += 1
                        if comment_id is not None:
                            self.journal.mark_comment_consumed(comment_id)
                        continue

                waiting_binding = self._waiting_binding.get(delivery.delivery_id)
                if waiting_binding is not None and waiting_binding != binding:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_DELIVERY_ID_CONFLICT", comment_id=comment_id, observed_comments=comment_bodies, quarantine=True)
                    rejected += 1
                    continue

                if delivery.task_id != task.task_id:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_ID_MISMATCH", comment_id=comment_id, observed_comments=comment_bodies, quarantine=False)
                    rejected += 1
                    continue

                task_receipt = self.journal.lookup_task(task.task_id)
                if task_receipt is not None and task_receipt.state == "ACCEPTED" and task_receipt.source_sha256 != delivery.source_sha256:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_CONFLICT", comment_id=comment_id, observed_comments=comment_bodies, quarantine=True)
                    rejected += 1
                    continue

                if terminal is not None:
                    self._reject(issue.number, task.task_id, delivery, "REFERENCE_TASK_TERMINAL", comment_id=comment_id, observed_comments=comment_bodies, quarantine=False)
                    rejected += 1
                    continue

                try:
                    source = validate_delivery_source(self.config, delivery)
                except ReferenceValidationError as exc:
                    self._reject(issue.number, task.task_id, delivery, exc.code, comment_id=comment_id, observed_comments=comment_bodies, quarantine=True)
                    rejected += 1
                    continue
                if source is None:
                    now = self._clock()
                    started = self._waiting_since.setdefault(delivery.delivery_id, now)
                    self._waiting_binding.setdefault(delivery.delivery_id, binding)
                    if now - started >= self.config.cloud_retry_timeout_seconds:
                        self._reject(issue.number, task.task_id, delivery, "REFERENCE_DRIVE_FOLDER_TIMEOUT", comment_id=comment_id, observed_comments=comment_bodies, quarantine=False)
                        rejected += 1
                    else:
                        waiting += 1
                    continue

                try:
                    publish_reference(self.config, delivery, source)
                except PublishError as exc:
                    self._reject(issue.number, task.task_id, delivery, exc.code, comment_id=comment_id, observed_comments=comment_bodies, quarantine=True)
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
                    self._post_failed(issue.number, task.task_id, delivery, exc.code, comment_bodies, comment_id, binding)
                    if comment_id is not None:
                        self.journal.mark_comment_consumed(comment_id)
                    rejected += 1
                    continue
                accepted += 1
                body = format_reference_ready(task.task_id, delivery.delivery_id, delivery.source_sha256)
                self.github.post_reference_event(issue.number, body)
                comment_bodies.append(body)
                if comment_id is not None:
                    self.journal.mark_comment_consumed(comment_id)

        return BridgeCycleSummary(len(issues), waiting, accepted, rejected, skipped)
