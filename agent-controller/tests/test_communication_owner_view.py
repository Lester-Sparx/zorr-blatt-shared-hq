from datetime import datetime, timezone
from zb_communication_orchestrator.owner_view import OwnerProjection, format_owner_view
from zb_local_controller.owner_snapshot import parse_owner_view_comments

def test_producer_is_parser_compatible_and_contains_django():
    p=OwnerProjection(datetime(2026,8,28,5,tzinfo=timezone.utc),'WAITING','corr-1','ZB-COMM-1','DUNCAN->JINGO',None,None,'OWNER_GATE',True,'comment:1 sha256:abc')
    body=format_owner_view(p); parsed=parse_owner_view_comments((body,),datetime(2026,8,28,5,1,tzinfo=timezone.utc)); assert parsed is not None and 'DJANGO' in parsed.agents; assert parsed.sparx_action=='OWNER ACTION REQUIRED'

def test_only_true_running_role_is_working():
    p=OwnerProjection(datetime(2026,8,28,5,tzinfo=timezone.utc),'WORKING','corr-1','ZB-COMM-1','JINGO->LESTER','LESTER',None,'LESTER_RESULT',False,'NONE')
    body=format_owner_view(p); parsed=parse_owner_view_comments((body,),datetime(2026,8,28,5,1,tzinfo=timezone.utc)); assert parsed.agents['LESTER'].status=='WORKING'; assert parsed.agents['DUNCAN'].status!='WORKING'
