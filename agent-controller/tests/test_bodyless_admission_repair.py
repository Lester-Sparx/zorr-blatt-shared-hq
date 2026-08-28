from types import SimpleNamespace

import zb_communication_orchestrator.handler as handler
from zb_communication_orchestrator.admission import WebhookEnvelope
from zb_communication_orchestrator.handler import handle_webhook


def test_bodyless_work_event_allows_missing_event_actor_and_type_after_exact_source_match(monkeypatch):
    body = 'ZB_AGENT_MESSAGE_V1\nMESSAGE_ID = bodyless-admission-1'
    envelope = WebhookEnvelope(
        'delivery-bodyless-admission-1',
        'Lester-Sparx/zorr-blatt-shared-hq',
        111,
        None,
        None,
        None,
        None,
        None,
    )

    class GH:
        def fetch_top_level_comments(self, pr):
            return [SimpleNamespace(id=300, body=body, actor='Lester-Sparx', top_level=True)]

        def fetch_issue_comments(self, issue):
            return []

        def read_comment(self, cid):
            return SimpleNamespace(id=cid, body=body, actor='Lester-Sparx', top_level=True)

    seen = {}
    monkeypatch.setattr(handler, 'route_message', lambda resolved, *a, **k: seen.setdefault('envelope', resolved))

    handle_webhook(
        envelope,
        GH(),
        object(),
        SimpleNamespace(communication_pr=111, ingress_epoch_comment_id=150, tracker_issue=106),
    )

    resolved = seen['envelope']
    assert resolved.comment_id == 300
    assert resolved.comment_body == body
    assert resolved.authenticated_actor == 'Lester-Sparx'
    assert resolved.event_type == 'issue_comment.created'
    assert resolved.top_level is True
