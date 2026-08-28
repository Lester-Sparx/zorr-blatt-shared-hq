import inspect
from zb_communication_orchestrator.handler import handle_webhook

def test_handler_has_single_route_and_forbidden_surfaces_absent():
    src=inspect.getsource(handle_webhook).lower()
    for token in ('sleep(','subprocess','auto_merge','merge_pull','owner_lock','github polling','list_candidate'):
        assert token not in src

def test_self_generated_and_sibling_markers_are_ignored_without_execution():
    from dataclasses import replace
    from zb_communication_orchestrator.admission import WebhookEnvelope
    from zb_communication_orchestrator.router import OrchestratorConfig
    class GH: pass
    class NeverExecute:
        def start(self,*args,**kwargs): raise AssertionError('self-generated/sibling events must never execute a logical role')
    base=WebhookEnvelope('pe','Lester-Sparx/zorr-blatt-shared-hq',777,1,'x','Lester-Sparx','issue_comment.created',True)
    for body in ('ZB_AGENT_RECEIPT_V1\nMESSAGE_ID = x','ZB_OWNER_VIEW_V0\nUPDATED_AT = 2026-08-28T00:00:00Z','ZB_AGENT_EVENT_V0\nTASK_ID = X','ZB_REFERENCE_EVENT_V1\nSTATE = REFERENCE_READY','ZB_REFERENCE_DELIVERY_V1\nTASK_ID = X','ordinary prose'):
        assert handle_webhook(replace(base,comment_body=body),GH(),NeverExecute(),OrchestratorConfig(777)) is None
