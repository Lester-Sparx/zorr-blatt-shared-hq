from __future__ import annotations
from dataclasses import dataclass

class ExecutionError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)
@dataclass(frozen=True)
class StartResult:
    started:bool; execution_id:str|None; evidence_ref:str|None; evidence_sha256:str|None
@dataclass(frozen=True)
class TerminalResult:
    success:bool; result_code:str; evidence_ref:str|None; evidence_sha256:str|None; timed_out:bool=False

def require_started(result:StartResult)->StartResult:
    if result.started is not True or not result.execution_id: raise ExecutionError('EXECUTION_START_FAILED')
    return result

def require_terminal(result:TerminalResult)->TerminalResult:
    if result.timed_out: raise ExecutionError('EXECUTION_TIMEOUT')
    if not result.result_code: raise ExecutionError('EXECUTION_START_FAILED')
    return result
