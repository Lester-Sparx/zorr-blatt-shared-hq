from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from .admission import AdmissionError, admit_event
from .authority import AuthorityError, Transition, derive_next_transition, load_transport_registry, validate_transition
from .bindings import BindingError, verify_bindings
from .contracts import AgentMessage, AgentReceipt, canonical_message_body, canonical_receipt_body
from .execution import ExecutionError, require_started, require_terminal
from .ledger import CorrelationLedger, LedgerError, VerifiedRecord
from .owner_view import OwnerProjection, format_owner_view
from .persistence import PersistError, persist_and_verify

class RouterError(RuntimeError):
    def __init__(self, code:str): self.code=code; super().__init__(code)
@dataclass(frozen=True)
class OrchestratorConfig:
    communication_pr:int
    architecture_required:bool=False
    execution_timeout_seconds:float=900.0
    now_factory:object=lambda:datetime.now(timezone.utc)
    max_attempts:int=3
@dataclass(frozen=True)
class RouterResult:
    result_code:str
    next_message_id:str|None
    terminal_comment_id:int|None
    terminal_state_code:str|None=None
_ids=count(1)
def _rid(prefix): return f'{prefix}-{next(_ids)}'
def _receipt(message,source_comment_id,state,role,attempt=1,execution_id=None,result_code=None,evidence_ref=None,evidence_sha256=None):
    return AgentReceipt(message.message_id,message.event_id,message.correlation_id,source_comment_id,_rid('rcpt'),state,'Lester-Sparx',role,message.task_id,message.target_head_sha,execution_id,result_code,evidence_ref,evidence_sha256,attempt,True)
def _persist(github,pr,body,attempts=1):
    last=None
    for _ in range(max(1,attempts)):
        try:
            return persist_and_verify(github,pr,body)
        except PersistError as exc:
            last=exc
            if exc.code!='RECEIPT_WRITE_FAILED':
                break
    assert last is not None
    raise RouterError(last.code) from last

def _persist_stage(github, config, body):
    return _persist(github,config.communication_pr,body,config.max_attempts)

def _persist_owner(github, config, message, term, *, status, blocker, next_gate, owner_required=False):
    projection=OwnerProjection(config.now_factory(),status,message.correlation_id,message.task_id,f'{message.from_role}->{message.to_role}',None,blocker,next_gate,owner_required,f'comment:{term.comment_id} sha256:{term.sha256}')
    try:
        _persist_stage(github,config,format_owner_view(projection))
    except RouterError as exc:
        raise RouterError('OWNER_VIEW_PERSISTENCE_FAILED') from exc

def route_message(envelope,github,executor,config:OrchestratorConfig)->RouterResult|None:
    try: message=admit_event(envelope,config.communication_pr)
    except AdmissionError as exc: raise RouterError(exc.code) from exc
    if message is None:
        return None
    try:
        registry=load_transport_registry(github)
        if envelope.authenticated_actor not in registry.approved_transport_actors: raise AuthorityError('TRANSPORT_ACTOR_REJECTED')
        records=[]
        for raw in github.fetch_comments(config.communication_pr):
            if isinstance(raw,VerifiedRecord): records.append(raw)
        ledger=CorrelationLedger.from_verified(records)
        prior=ledger.last_message(message.correlation_id)
        check=ledger.check(message)
        if check.duplicate: return RouterResult('DUPLICATE',None,None)
        if prior is None:
            validate_transition(message,Transition('JINGO','LESTER','ASSIGN'))
        else:
            if not ledger.is_terminal(prior.message_id):
                raise AuthorityError('ROLE_TRANSITION_ILLEGAL')
            expected=derive_next_transition(prior.message_kind,config.architecture_required)
            validate_transition(message,expected)
        verify_bindings(message,github)
    except (AuthorityError,BindingError,LedgerError) as exc: raise RouterError(exc.code) from exc
    start=None
    attempt=1
    while attempt<=config.max_attempts:
        _persist_stage(github,config,canonical_receipt_body(_receipt(message,envelope.comment_id,'RECEIVED',message.to_role,attempt=attempt)))
        try:
            start=require_started(executor.start(message.to_role,message))
            break
        except ExecutionError:
            if attempt>=config.max_attempts:
                dead=_receipt(message,envelope.comment_id,'DEAD_LETTER',message.to_role,attempt=attempt,result_code='RETRY_EXHAUSTED')
                term=_persist_stage(github,config,canonical_receipt_body(dead))
                _persist_owner(github,config,message,term,status='BLOCKED',blocker='RETRY_EXHAUSTED',next_gate='STOP')
                return RouterResult('RETRY_EXHAUSTED',None,term.comment_id,'DEAD_LETTERED')
            attempt+=1
    assert start is not None
    _persist_stage(github,config,canonical_receipt_body(_receipt(message,envelope.comment_id,'RUNNING',message.to_role,attempt=attempt,execution_id=start.execution_id,evidence_ref=start.evidence_ref,evidence_sha256=start.evidence_sha256)))
    terminal_raw=executor.wait(start.execution_id,config.execution_timeout_seconds)
    try: terminal=require_terminal(terminal_raw)
    except ExecutionError as exc:
        terminal_receipt=_receipt(message,envelope.comment_id,'BLOCKED',message.to_role,attempt=attempt,execution_id=start.execution_id,result_code=exc.code,evidence_ref=terminal_raw.evidence_ref,evidence_sha256=terminal_raw.evidence_sha256)
        term=_persist_stage(github,config,canonical_receipt_body(terminal_receipt))
        _persist_owner(github,config,message,term,status='BLOCKED',blocker=exc.code,next_gate='STOP')
        return RouterResult(exc.code,None,term.comment_id)
    state='RESULT' if terminal.success else 'BLOCKED'
    terminal_receipt=_receipt(message,envelope.comment_id,state,message.to_role,execution_id=start.execution_id,result_code=terminal.result_code,evidence_ref=terminal.evidence_ref,evidence_sha256=terminal.evidence_sha256)
    term=_persist_stage(github,config,canonical_receipt_body(terminal_receipt))
    owner_required=False; next_transition=None
    if terminal.success:
        try: next_transition=derive_next_transition(message.message_kind,config.architecture_required)
        except AuthorityError as exc:
            if exc.code=='OWNER_GATE_REQUIRED': owner_required=True
            else: raise RouterError(exc.code) from exc
    _persist_owner(github,config,message,term,status='WAITING' if terminal.success else 'BLOCKED',blocker=None if terminal.success else terminal.result_code,next_gate='OWNER_GATE' if owner_required else (next_transition.message_kind if next_transition else 'STOP'),owner_required=owner_required)
    if not terminal.success or owner_required or next_transition is None: return RouterResult(terminal.result_code,None,term.comment_id)
    next_id=_rid('msg')
    next_message=AgentMessage(next_id,_rid('evt'),message.correlation_id,message.message_id,message.task_id,next_transition.from_role,next_transition.to_role,next_transition.message_kind,message.target_repo,message.target_issue,message.target_pr,message.base_sha,message.target_head_sha,message.task_revision,terminal.evidence_ref,terminal.evidence_sha256,next_transition.message_kind,True,'')
    _persist_stage(github,config,canonical_message_body(next_message))
    return RouterResult(terminal.result_code,next_id,term.comment_id)
