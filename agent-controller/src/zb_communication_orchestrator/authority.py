from __future__ import annotations
from dataclasses import dataclass
import json

class AuthorityError(RuntimeError):
    def __init__(self, code: str): self.code=code; super().__init__(code)

@dataclass(frozen=True)
class TransportRegistry:
    approved_transport_actors: tuple[str,...]
    logical_roles: tuple[str,...]

@dataclass(frozen=True)
class Transition:
    from_role: str
    to_role: str
    message_kind: str

def load_transport_registry(github) -> TransportRegistry:
    raw,_ = github.read_protected_file('.github/zb/roles.yml')
    try: data=json.loads(raw)
    except Exception as exc: raise AuthorityError('TRANSPORT_ACTOR_REJECTED') from exc
    actors=tuple(data.get('approvedTransportActors') or ()); roles=tuple(data.get('logicalRoles') or ())
    if actors != ('Lester-Sparx',) or not {'OWNER','LESTER','DUNCAN','DJANGO','JINGO'} <= set(roles):
        raise AuthorityError('TRANSPORT_ACTOR_REJECTED')
    return TransportRegistry(actors,roles)

def validate_transition(message, expected: Transition) -> None:
    if (message.from_role,message.to_role,message.message_kind)!=(expected.from_role,expected.to_role,expected.message_kind):
        raise AuthorityError('ROLE_TRANSITION_ILLEGAL')

def derive_next_transition(message_kind: str, architecture_required: bool) -> Transition:
    table={
        'ASSIGN':Transition('LESTER','JINGO','RETURN'),
        'RETURN':Transition('JINGO','DUNCAN','QC_REQUEST'),
        'QC_REQUEST':Transition('DUNCAN','JINGO','QC_VERDICT'),
        'ARCH_REVIEW':Transition('DJANGO','JINGO','ARCH_VERDICT'),
    }
    if message_kind=='QC_VERDICT':
        return Transition('JINGO','DJANGO','ARCH_REVIEW') if architecture_required else Transition('JINGO','JINGO','CLOSE_REQUEST')
    if message_kind=='ARCH_VERDICT': return Transition('JINGO','JINGO','CLOSE_REQUEST')
    if message_kind=='CLOSE_REQUEST': raise AuthorityError('OWNER_GATE_REQUIRED')
    try:return table[message_kind]
    except KeyError as exc:raise AuthorityError('ROLE_TRANSITION_ILLEGAL') from exc
