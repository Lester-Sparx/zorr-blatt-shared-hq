from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any


class BackendError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class BackendPollResult:
    state: str
    error_code: str | None = None


class Backend(Protocol):
    def ensure_ready(self) -> None: ...
    def submit(self, task: Any, reference: Any) -> str: ...
    def poll(self, execution_id: str) -> BackendPollResult: ...
    def collect(self, execution_id: str) -> bytes: ...
