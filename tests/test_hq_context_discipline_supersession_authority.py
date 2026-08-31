from __future__ import annotations

import unittest

from scripts import hq_context_discipline as context


class ContextSupersessionAuthorityTests(unittest.TestCase):
    def test_unverified_active_delta_cannot_supersede_owner_durable_fact(self) -> None:
        owner = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "owner-law",
            "class": "E2",
            "key": "OWNER_LOCK",
            "value": "NO_OWNER_RELAY",
            "exclusive": True,
            "verified": True,
            "authority": "OWNER",
            "created_at": "2026-01-01T00:00:00Z",
            "scope_tags": ["ZORR"],
            "source_refs": ["github:owner:directive"],
            "supersedes": [],
        }
        weak = {
            "schema": "ZB_CONTEXT_FACT_V1",
            "fact_id": "chat-guess",
            "class": "E1",
            "key": "OWNER_LOCK",
            "value": "OWNER_RELAY_ALLOWED",
            "exclusive": True,
            "verified": False,
            "authority": "CHAT",
            "created_at": "2026-08-31T17:40:00Z",
            "scope_tags": ["ZORR"],
            "source_refs": [],
            "supersedes": ["owner-law"],
        }
        with self.assertRaisesRegex(
            context.ContextDisciplineError,
            "CONTEXT_SUPERSESSION_AUTHORITY_INVALID",
        ):
            context.project_current_state([owner, weak], scope_tags={"ZORR"})


if __name__ == "__main__":
    unittest.main()
