import unittest
from pathlib import Path

from _support import ROOT


WORKER = ROOT / "scripts" / "sheriff_worker.py"
DOCKERFILE = ROOT / "config" / "sheriff" / "Dockerfile.worker"


class SheriffWorkerContractTest(unittest.TestCase):
    def test_worker_reuses_oss_clients_and_glicko_math(self):
        text = WORKER.read_text(encoding="utf-8")
        self.assertIn("import nats", text)
        self.assertIn("import psycopg", text)
        self.assertIn("from glicko2.math import update_rating", text)
        self.assertIn("rating_to_mu", text)
        self.assertIn("rd_to_phi", text)
        self.assertIn("mu_to_rating", text)
        self.assertIn("phi_to_rd", text)
        self.assertIn("from prometheus_client import", text)

    def test_worker_is_jetstream_push_event_driven_not_polling(self):
        text = WORKER.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn('STREAM_NAME = "ZB_AGENT_EVENTS"', text)
        self.assertIn('SUBJECT = "zb.>"', text)
        self.assertIn('DURABLE_NAME = "sheriff-v1"', text)
        self.assertIn("manual_ack=True", text)
        self.assertIn("await msg.ack()", text)
        self.assertIn("await stop_event.wait()", text)
        self.assertNotIn("time.sleep", lower)
        self.assertNotIn("asyncio.sleep", lower)
        self.assertNotIn("pull_subscribe", lower)
        self.assertNotIn("fetch(", lower)

    def test_worker_commits_durable_state_before_ack_and_requires_opa(self):
        text = WORKER.read_text(encoding="utf-8")
        self.assertIn("decision = await request_opa_decision(event)", text)
        self.assertIn("await conn.commit()", text)
        self.assertLess(text.index("await conn.commit()"), text.index("await msg.ack()"))
        self.assertIn("OPA_DECISION_INVALID", text)
        self.assertIn("OPA_REJECTED_EVENT", text)
        self.assertIn("EVENT_ID_BODY_HASH_CONFLICT", text)

    def test_worker_gates_rating_and_emits_remediation(self):
        text = WORKER.read_text(encoding="utf-8")
        self.assertIn("safetyGatePassed", text)
        self.assertIn("ACTIVE_HOLD_BLOCKS_RATING", text)
        self.assertIn("remediation_path(", text)
        self.assertIn("zb.sheriff.verdict", text)
        self.assertIn("rated_matches", text)

    def test_worker_container_is_minimal_python_glue(self):
        text = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("FROM python:3.12-slim", text)
        self.assertIn("requirements-sheriff.txt", text)
        self.assertIn("sheriff_worker.py", text)
        self.assertNotIn("node", text.lower())
        self.assertNotIn("curl", text.lower())


if __name__ == "__main__":
    unittest.main()
