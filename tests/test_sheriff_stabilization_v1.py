import json
import re
import unittest
from pathlib import Path

from _support import ROOT


POLICY = ROOT / "docs" / "SHERIFF_POLICY_V1.md"
VERDICT_SCHEMA = ROOT / "schemas" / "SHERIFF_VERDICT_V1.schema.json"
EVENT_SCHEMA = ROOT / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json"
OPA = ROOT / "config" / "sheriff" / "opa" / "sheriff.rego"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
SQL = ROOT / "config" / "sheriff" / "postgres" / "001_sheriff.sql"
NATS = ROOT / "config" / "sheriff" / "nats.conf"
WORKER = ROOT / "scripts" / "sheriff_worker.py"
CORE = ROOT / "scripts" / "sheriff_core.py"
REQUIREMENTS = ROOT / "requirements-sheriff.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "sheriff-oss-validate.yml"


class SheriffStabilizationV1Test(unittest.TestCase):
    def test_policy_and_opa_have_one_i3_i4_consequence_contract(self):
        policy = POLICY.read_text(encoding="utf-8")
        rego = OPA.read_text(encoding="utf-8")
        self.assertIn("`I3_CRITICAL_INTEGRITY`", policy)
        self.assertIn("-20", policy)
        self.assertIn("execution HOLD", policy)
        self.assertIn("`I4_SAFETY_SECURITY`", policy)
        self.assertIn("-40", policy)
        self.assertIn("HARD_HOLD", policy)
        self.assertRegex(rego, r'I3_CRITICAL_INTEGRITY[\s\S]{0,500}"disciplineDelta": -20[\s\S]{0,500}"executionGate": "HOLD"')
        self.assertRegex(rego, r'I4_SAFETY_SECURITY[\s\S]{0,500}"disciplineDelta": -40[\s\S]{0,500}"executionGate": "HARD_HOLD"')

    def test_verdict_schema_rejects_self_judgement_and_requires_remediation(self):
        schema = json.loads(VERDICT_SCHEMA.read_text(encoding="utf-8"))
        all_of = json.dumps(schema.get("allOf", []), sort_keys=True)
        for agent in ("LESTER", "DUNCAN", "DJANGO", "JINGO", "SHERIFF"):
            self.assertIn(agent, all_of)
        self.assertIn('"sheriffId"', all_of)
        self.assertIn('"not"', all_of)
        self.assertIn('"minItems": 1', all_of)
        self.assertIn('"I0_SELF_CAUGHT"', all_of)

    def test_every_compose_image_is_declared_exactly_in_oss_manifest(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = {
            item["runtimeRef"]
            for item in manifest["components"]
            if not item["runtimeRef"].startswith("local:") and "==" not in item["runtimeRef"]
        }
        compose = COMPOSE.read_text(encoding="utf-8")
        images = set(re.findall(r"^\s*image:\s*([^\s#]+)", compose, flags=re.MULTILINE))
        self.assertEqual(images, declared)

    def test_forgejo_bootstrap_is_self_consistent_for_v1(self):
        compose = COMPOSE.read_text(encoding="utf-8")
        self.assertIn("FORGEJO__database__DB_TYPE: sqlite3", compose)
        self.assertNotIn("FORGEJO__database__HOST:", compose)
        self.assertNotIn("FORGEJO_DB_PASSWORD", compose)

    def test_runtime_uses_real_json_schema_validation(self):
        worker = WORKER.read_text(encoding="utf-8")
        requirements = REQUIREMENTS.read_text(encoding="utf-8").lower()
        dockerfile = (ROOT / "config" / "sheriff" / "Dockerfile.worker").read_text(encoding="utf-8")
        self.assertIn("jsonschema==", requirements)
        self.assertIn("from jsonschema import Draft202012Validator", worker)
        self.assertIn("SHERIFF_AGENT_EVENT_V1.schema.json", worker)
        self.assertIn("EVENT_SCHEMA_VALIDATION_FAILED", worker)
        self.assertIn("schemas/SHERIFF_AGENT_EVENT_V1.schema.json", dockerfile)

    def test_outbox_prevents_commit_publish_gap_from_losing_verdict(self):
        sql = SQL.read_text(encoding="utf-8")
        worker = WORKER.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS sheriff_outbox", sql)
        self.assertIn("_enqueue_verdict_outbox", worker)
        self.assertIn("_flush_outbox", worker)
        commit = worker.index("await conn.commit()")
        flush = worker.index("await _flush_outbox")
        ack = worker.index("await msg.ack()")
        self.assertLess(commit, flush)
        self.assertLess(flush, ack)
        self.assertIn("published_at IS NULL", worker)

    def test_poison_events_are_bounded_and_dead_lettered(self):
        sql = SQL.read_text(encoding="utf-8")
        worker = WORKER.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE IF NOT EXISTS sheriff_dead_letters", sql)
        self.assertIn("ConsumerConfig", worker)
        self.assertIn("max_deliver=5", worker)
        self.assertIn("backoff=", worker)
        self.assertIn("_record_dead_letter", worker)
        self.assertIn("await msg.term()", worker)

    def test_internal_services_are_not_published_to_host_and_nats_has_auth(self):
        compose = COMPOSE.read_text(encoding="utf-8")
        nats = NATS.read_text(encoding="utf-8")
        self.assertIn("NATS_PASSWORD", compose)
        self.assertIn("SHERIFF_NATS_URL: nats://sheriff:", compose)
        self.assertIn("authorization", nats.lower())
        for port in ("4222:4222", "8222:8222", "8181:8181", "5432:5432", "4317:4317", "4318:4318", "9090:9090", "3100:3100", "9464:9464"):
            self.assertNotIn(port, compose)

    def test_discipline_bands_drive_execution_gate(self):
        core = CORE.read_text(encoding="utf-8")
        worker = WORKER.read_text(encoding="utf-8")
        self.assertIn("def execution_gate_for_score", core)
        self.assertIn("HEIGHTENED_QC", core)
        self.assertIn("RESTRICTED", core)
        self.assertIn("HOLD", core)
        self.assertIn("execution_gate_for_score", worker)

    def test_dedicated_ci_installs_runtime_dependencies_before_runtime_checks(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pip install -r requirements-sheriff.txt", workflow)
        self.assertIn("test_sheriff_stabilization_v1.py", workflow)


if __name__ == "__main__":
    unittest.main()
