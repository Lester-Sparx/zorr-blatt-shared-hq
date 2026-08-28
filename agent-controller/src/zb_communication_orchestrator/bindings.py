from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256

class BindingError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)
@dataclass(frozen=True)
class PRMeta: number:int; head_sha:str
@dataclass(frozen=True)
class TaskMeta: task_id:str; revision:int|None
@dataclass(frozen=True)
class Evidence: content:bytes; target_head_sha:str|None=None

def verify_bindings(message, github) -> None:
    if message.target_pr is not None:
        meta=github.fetch_pr_meta(message.target_pr)
        if not meta or meta.head_sha!=message.target_head_sha: raise BindingError('TARGET_HEAD_STALE')
    if message.base_sha is not None and github.fetch_protected_main_sha()!=message.base_sha: raise BindingError('BASE_CAS_MISMATCH')
    if message.target_issue is not None and message.task_revision is not None:
        task=github.fetch_task_meta(message.target_issue)
        if not task or task.task_id!=message.task_id or task.revision!=message.task_revision: raise BindingError('TASK_REVISION_MISMATCH')
    if message.evidence_ref is not None:
        evidence=github.fetch_evidence(message.evidence_ref)
        if evidence is None: raise BindingError('EVIDENCE_MISSING')
        if sha256(evidence.content).hexdigest()!=message.evidence_sha256: raise BindingError('EVIDENCE_MISMATCH')
        if message.target_head_sha is not None and evidence.target_head_sha not in {None,message.target_head_sha}: raise BindingError('EVIDENCE_MISMATCH')
