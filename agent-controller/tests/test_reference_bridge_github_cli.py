import json
from types import SimpleNamespace
import pytest
from zb_reference_bridge.github_cli import BridgeGitHubCLI, BridgeGitHubError

VALID_BODY = """ZB_AGENT_TASK_V0
TASK_ID = ZB-REF-001
AGENT = SALVADOR
TASK_KIND = CANON_REFERENCE_EDIT
STATE = ASSIGNED
REFERENCE = LOCAL_INBOX

Preserve reference.
"""
class FakeRunner:
    def __init__(self,responses): self.responses=list(responses); self.calls=[]
    def __call__(self,args,**kwargs): self.calls.append((args,kwargs)); return self.responses.pop(0)
def cp(code=0,out="",err=""): return SimpleNamespace(returncode=code,stdout=out,stderr=err)
def test_list_task_issues_uses_open_task_search_and_comments():
    runner=FakeRunner([cp(out=json.dumps([{"number":92,"title":"x","body":VALID_BODY,"comments":[{"id":"IC_kwDOA1","body":"note"}]}]))]); gh=BridgeGitHubCLI("Lester-Sparx/zorr-blatt-shared-hq",runner=runner); issues=gh.list_task_issues(); assert issues[0].number==92; assert "ZB_AGENT_TASK_V0" in issues[0].body; assert issues[0].comments[0].id=="IC_kwDOA1"; assert issues[0].comments[0].body=="note"; args,kwargs=runner.calls[0]; assert args[:3]==["gh","issue","list"]; assert "--state" in args and args[args.index("--state")+1]=="open"; assert "--search" in args and args[args.index("--search")+1]=="ZB_AGENT_TASK_V0"; assert "--limit" in args and args[args.index("--limit")+1]=="1000"; assert "--json" in args and args[args.index("--json")+1]=="number,title,body,comments"; assert kwargs["capture_output"] is True and kwargs["text"] is True and kwargs["shell"] is False
def test_invalid_task_contract_is_filtered():
    runner=FakeRunner([cp(out=json.dumps([{"number":1,"title":"x","body":"ZB_AGENT_TASK_V0","comments":[]}]))]); assert BridgeGitHubCLI("o/r",runner=runner).list_task_issues()==()
def test_invalid_json_fails_closed():
    with pytest.raises(BridgeGitHubError) as exc: BridgeGitHubCLI("o/r",runner=FakeRunner([cp(out="not-json")])).list_task_issues()
    assert exc.value.code=="BRIDGE_GH_OUTPUT_INVALID"
def test_failed_list_has_stable_code():
    with pytest.raises(BridgeGitHubError) as exc: BridgeGitHubCLI("o/r",runner=FakeRunner([cp(code=1)])).list_task_issues()
    assert exc.value.code=="BRIDGE_GH_ISSUE_LIST_FAILED"
def test_post_reference_event_uses_issue_comment_and_failure_is_stable():
    ok=FakeRunner([cp()]); BridgeGitHubCLI("o/r",runner=ok).post_reference_event(92,"ZB_REFERENCE_EVENT_V1"); assert ok.calls[0][0][:3]==["gh","issue","comment"]; bad=FakeRunner([cp(code=1)]); 
    with pytest.raises(BridgeGitHubError) as exc: BridgeGitHubCLI("o/r",runner=bad).post_reference_event(92,"x")
    assert exc.value.code=="BRIDGE_GH_COMMENT_FAILED"
def test_auth_preflight_uses_gh_auth_status():
    runner=FakeRunner([cp()]); BridgeGitHubCLI("o/r",runner=runner).ensure_authenticated(); assert runner.calls[0][0]==["gh","auth","status"]
