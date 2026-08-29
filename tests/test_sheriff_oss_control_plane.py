import json
import unittest
from pathlib import Path

from _support import ROOT


MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
NATS = ROOT / "config" / "sheriff" / "nats.conf"
REQUIREMENTS = ROOT / "requirements-sheriff.txt"
EVENT_SCHEMA = ROOT / "schemas" / "SHERIFF_AGENT_EVENT_V1.schema.json"
OPA_POLICY = ROOT / "config" / "sheriff" / "opa" / "sheriff.rego"
OPA_TEST = ROOT / "config" / "sheriff" / "opa" / "sheriff_test.rego"
VALIDATOR = ROOT / "scripts" / "sheriff_validate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "sheriff-oss-validate.yml"


class SheriffOssControlPlaneTest(unittest.TestCase):
    def test_all_runtime_components_have_explicit_open_source_provenance(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schemaVersion"], "SHERIFF_OSS_COMPONENTS_V1")

        components = {item["id"]: item for item in data["components"]}
        required = {
            "forgejo", "nats", "opa", "postgresql", "opentelemetry-collector",
            "prometheus", "loki", "grafana-oss", "sheriff-worker",
            "glicko2-py", "nats-py", "psycopg",
        }
        self.assertTrue(required.issubset(components), required - set(components))

        allowed_licenses = {
            "GPL-3.0-or-later", "Apache-2.0", "PostgreSQL", "AGPL-3.0-only",
            "MIT", "LGPL-3.0-only", "PSF-2.0",
        }
        for component_id, component in components.items():
            with self.subTest(component=component_id):
                self.assertTrue(component["source"].startswith("https://"))
                self.assertIn(component["license"], allowed_licenses)
                self.assertTrue(component["runtimeRef"])
                self.assertTrue(component["purpose"])
                self.assertNotEqual(component["license"].upper(), "PROPRIETARY")

    def test_compose_is_event_driven_and_uses_declared_oss_services(self):
        text = COMPOSE.read_text(encoding="utf-8")
        lower = text.lower()
        for service in (
            "forgejo:", "nats:", "opa:", "postgres:", "otel-collector:",
            "prometheus:", "loki:", "grafana:", "sheriff-worker:",
        ):
            self.assertIn(service, lower)

        self.assertIn("config/sheriff/nats.conf", lower)
        self.assertIn("config/sheriff/opa", lower)
        self.assertIn("config/sheriff/postgres", lower)
        self.assertNotIn("cron:", lower)
        self.assertNotIn("schedule:", lower)
        self.assertNotIn("sleep ", lower)

    def test_nats_jetstream_is_durable_and_not_polling(self):
        text = NATS.read_text(encoding="utf-8").lower()
        self.assertIn("jetstream", text)
        self.assertIn("store_dir", text)
        self.assertNotIn("poll", text)

    def test_rating_and_transport_reuse_open_source_libraries(self):
        text = REQUIREMENTS.read_text(encoding="utf-8").lower()
        self.assertIn("glicko2-py==0.1.0", text)
        self.assertIn("nats-py==", text)
        self.assertIn("psycopg", text)
        self.assertNotIn("openai", text)
        self.assertNotIn("anthropic", text)

    def test_event_schema_is_cloudevents_1_and_evidence_bound(self):
        schema = json.loads(EVENT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["specversion"]["const"], "1.0")
        self.assertEqual(schema["properties"]["datacontenttype"]["const"], "application/json")
        self.assertTrue({"specversion", "id", "source", "type", "subject", "time", "datacontenttype", "data"}.issubset(schema["required"]))
        self.assertEqual(
            set(schema["properties"]["type"]["enum"]),
            {"zb.agent.task.started", "zb.agent.result", "zb.agent.qc", "zb.sheriff.verdict", "zb.league.match"},
        )
        self.assertEqual(schema["$defs"]["evidence"]["minItems"], 1)
        self.assertGreaterEqual(len(schema["allOf"]), 4)

    def test_opa_policy_has_fail_closed_incident_and_independence_rules(self):
        policy = OPA_POLICY.read_text(encoding="utf-8")
        tests = OPA_TEST.read_text(encoding="utf-8")
        self.assertIn("package zorr.sheriff", policy)
        self.assertIn("default decision", policy)
        for incident_class in (
            "I0_SELF_CAUGHT", "I1_CORRECTNESS", "I2_PROCESS",
            "I3_CRITICAL_INTEGRITY", "I4_SAFETY_SECURITY",
        ):
            self.assertIn(incident_class, policy)
        self.assertIn("FALSE_PASS", policy)
        self.assertIn("SELF_JUDGEMENT", policy)
        self.assertIn("PASS_WITHOUT_EVIDENCE", policy)
        self.assertIn("test_honest_fail_is_admitted_without_penalty", tests)
        self.assertIn("test_false_pass_is_critical", tests)
        self.assertIn("test_sheriff_cannot_self_judge", tests)
        self.assertIn("test_pass_without_evidence_is_rejected", tests)

    def test_v1_has_one_dedicated_fail_closed_validation_gate(self):
        validator = VALIDATOR.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("SHERIFF OSS CONTROL PLANE V1 VALIDATION PASS", validator)
        self.assertIn("OPEN_SOURCE_COMPONENTS.json", validator)
        self.assertIn("PROPRIETARY", validator)
        self.assertIn("python3 scripts/sheriff_validate.py", workflow)
        self.assertIn("python3 -m py_compile scripts/sheriff_core.py scripts/sheriff_worker.py", workflow)
        self.assertIn("docker compose -f config/sheriff/docker-compose.yml config", workflow)
        self.assertIn("openpolicyagent/opa:1.0.1-static", workflow)
        self.assertIn("opa test", workflow)


if __name__ == "__main__":
    unittest.main()
