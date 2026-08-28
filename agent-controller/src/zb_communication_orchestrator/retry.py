from __future__ import annotations
from dataclasses import dataclass
class RetryError(RuntimeError):
    def __init__(self,code='RETRY_EXHAUSTED'): self.code=code; super().__init__(code)
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts:int
    def __post_init__(self):
        if self.max_attempts<=0: raise ValueError('max_attempts')
def retry_operation(policy,operation,*,is_success):
    for attempt in range(1,policy.max_attempts+1):
        value=operation(attempt)
        if is_success(value): return value
    raise RetryError()
