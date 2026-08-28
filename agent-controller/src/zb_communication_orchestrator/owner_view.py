from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
CORE_ROLES=('JINGO','LESTER','DUNCAN','DJANGO')
ALL_ROWS=('JINGO','LESTER','DUNCAN','DJANGO','SALVADOR','LYNCH','MAO','CHARLIE','MEMORO')
@dataclass(frozen=True)
class OwnerProjection:
    updated_at:datetime; overall_status:str; correlation_id:str; task_id:str; last_transition:str; running_role:str|None; blocker:str|None; next_gate:str; owner_action_required:bool; evidence_summary:str

def _ts(dt): return dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
def format_owner_view(p:OwnerProjection)->str:
    action='OWNER ACTION REQUIRED' if p.owner_action_required else 'NONE'
    why=p.blocker or f'correlation={p.correlation_id}; task={p.task_id}; last={p.last_transition}; next={p.next_gate}; evidence={p.evidence_summary}'
    lines=['ZB_OWNER_VIEW_V0',f'UPDATED_AT = {_ts(p.updated_at)}',f'OVERALL_STATUS = {p.overall_status}',f'SPARX_ACTION = {action}',f'WHY = {why}','SCOUT_LAST_CHECK = UNKNOWN','SCOUT_SUMMARY = NONE']
    for role in ALL_ROWS:
        working=(role==p.running_role)
        status='WORKING' if working else 'WAITING'
        doing=f'communication {p.correlation_id}' if role in CORE_ROLES else 'outside initial communication core'
        done=p.last_transition if role in CORE_ROLES else 'NONE'
        blocker=p.blocker or 'NONE'
        nxt=p.next_gate if role in CORE_ROLES else 'wait'
        lines.append(f'AGENT = {role} | {status} | {doing} | {done} | {blocker} | {nxt}')
    lines.append(f'GATE = COMMUNICATION | {p.overall_status} | correlation={p.correlation_id}; task={p.task_id}; next={p.next_gate}; evidence={p.evidence_summary}')
    return '\n'.join(lines)
