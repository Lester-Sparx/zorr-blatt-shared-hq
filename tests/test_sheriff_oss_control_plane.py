import json
import unittest
from pathlib import Path

from _support import ROOT


MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
NATS = ROOT / "config" / "sheriff" / "nats.conf"
REQUIREMENTS = ROOT / "requirements-sheriff.txt"


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


if __name__ == "__main__":
    unittest.main()
