from __future__ import annotations
from dataclasses import dataclass
from .contracts import RECEIPT_MARKER, MESSAGE_MARKER, message_body_digest, parse_message, parse_receipt

class LedgerError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)
@dataclass(frozen=True)
class VerifiedRecord: comment_id:int; actor:str; body:str
@dataclass(frozen=True)
class LedgerCheck: duplicate:bool=False

class CorrelationLedger:
    def __init__(self): self.messages={}; self.order=[]; self.terminal=set()
    @classmethod
    def from_verified(cls, records):
        obj=cls()
        for record in records:
            if record.actor!='Lester-Sparx': continue
            if record.body.startswith(MESSAGE_MARKER):
                try:m=parse_message(record.body)
                except Exception: continue
                digest=message_body_digest(m)
                prev=obj.messages.get(m.message_id)
                if prev and prev[0]!=digest: continue
                obj.messages[m.message_id]=(digest,m)
                if m.message_id not in obj.order: obj.order.append(m.message_id)
            elif record.body.startswith(RECEIPT_MARKER):
                try:r=parse_receipt(record.body)
                except Exception: continue
                if r.state in {'RESULT','BLOCKED','DEAD_LETTER'}: obj.terminal.add(r.message_id)
        return obj
    def check(self,message):
        digest=message_body_digest(message)
        if message.message_id in self.messages:
            if self.messages[message.message_id][0]!=digest: raise LedgerError('MESSAGE_ID_COLLISION')
            if message.message_id in self.terminal: raise LedgerError('REPLAY_TERMINAL')
            return LedgerCheck(True)
        prior=[self.messages[mid][1] for mid in self.order if self.messages[mid][1].correlation_id==message.correlation_id]
        if prior:
            if message.causation_message_id!=prior[-1].message_id: raise LedgerError('CAUSATION_MISMATCH')
        elif message.causation_message_id is not None: raise LedgerError('CAUSATION_MISMATCH')
        return LedgerCheck(False)
