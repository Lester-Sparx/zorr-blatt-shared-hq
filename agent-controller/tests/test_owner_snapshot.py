from datetime import datetime, timezone
from zb_local_controller.owner_snapshot import parse_owner_view_comments
VALID="""ZB_OWNER_VIEW_V0
UPDATED_AT = 2026-08-27T01:00:00Z
OVERALL_STATUS = WAITING
SPARX_ACTION = NONE
WHY = Duncan verdict required before Task 9.
SCOUT_LAST_CHECK = 2026-08-27T00:50:00Z
SCOUT_SUMMARY = NONE
AGENT = JINGO | WORKING | coordinates | NONE | NONE | wait for Duncan
AGENT = LESTER | WAITING | repair ready | repair complete | Duncan QC | wait
AGENT = DUNCAN | WORKING | independent QC | NONE | NONE | PASS or CHANGES_REQUIRED
AGENT = DJANGO | WAITING | architecture review | NONE | NONE | wait for architecture gate
AGENT = SALVADOR | WAITING | production visual | NONE | gate | model smoke
AGENT = LYNCH | WORKING | research | NONE | NONE | continue
AGENT = MAO | WORKING | performance research | NONE | NONE | report
AGENT = CHARLIE | WAITING | model board | NONE | NONE | start
AGENT = MEMORO | WAITING | truth audit | NONE | NONE | start
GATE = DUNCAN_QC | WAITING | exact candidate under review
GATE = REAL_MODEL_SMOKE | WAITING | locked until Duncan PASS
"""
def test_parses_latest_valid_snapshot_with_django():
    now=datetime(2026,8,27,1,30,tzinfo=timezone.utc); s=parse_owner_view_comments(('noise',VALID),now); assert s is not None and s.agents['DJANGO'].status=='WAITING' and not s.is_stale
def test_snapshot_without_django_is_rejected_to_prevent_version_skew():
    now=datetime(2026,8,27,1,30,tzinfo=timezone.utc); old=VALID.replace('AGENT = DJANGO | WAITING | architecture review | NONE | NONE | wait for architecture gate\n',''); assert parse_owner_view_comments((old,),now) is None
def test_rejects_snapshot_missing_required_scalar_key(): assert parse_owner_view_comments((VALID.replace('WHY = Duncan verdict required before Task 9.\n',''),),datetime(2026,8,27,1,30,tzinfo=timezone.utc)) is None
def test_rejects_unknown_agent_name_and_unknown_status():
    now=datetime(2026,8,27,1,30,tzinfo=timezone.utc); assert parse_owner_view_comments((VALID.replace('AGENT = MEMORO','AGENT = GHOST'),),now) is None; assert parse_owner_view_comments((VALID.replace('OVERALL_STATUS = WAITING','OVERALL_STATUS = HEALTHY'),),now) is None
def test_malformed_newest_comment_does_not_hide_last_valid_snapshot(): assert parse_owner_view_comments((VALID,'ZB_OWNER_VIEW_V0\nUPDATED_AT = broken'),datetime(2026,8,27,1,30,tzinfo=timezone.utc)).why=='Duncan verdict required before Task 9.'
def test_snapshot_is_stale_only_after_two_hour_boundary():
    assert parse_owner_view_comments((VALID,),datetime(2026,8,27,3,0,0,tzinfo=timezone.utc)).is_stale is False; assert parse_owner_view_comments((VALID,),datetime(2026,8,27,3,0,1,tzinfo=timezone.utc)).is_stale is True
def test_agent_and_gate_rows_accept_owner_facing_stale_status():
    now=datetime(2026,8,27,1,30,tzinfo=timezone.utc); body=VALID.replace('AGENT = LESTER | WAITING','AGENT = LESTER | STALE').replace('GATE = DUNCAN_QC | WAITING','GATE = DUNCAN_QC | STALE'); s=parse_owner_view_comments((body,),now); assert s.agents['LESTER'].status=='STALE' and s.gates['DUNCAN_QC'].status=='STALE'
