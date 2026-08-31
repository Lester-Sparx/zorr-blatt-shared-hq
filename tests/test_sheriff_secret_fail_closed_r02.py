import re
import unittest

from _support import ROOT


COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"


class SheriffSecretFailClosedR02Test(unittest.TestCase):
    def test_security_credentials_have_no_default_fallbacks(self):
        text = COMPOSE.read_text(encoding="utf-8")

        required_secrets = (
            "NATS_PASSWORD",
            "SHERIFF_DB_PASSWORD",
            "GRAFANA_ADMIN_PASSWORD",
        )
        for name in required_secrets:
            with self.subTest(secret=name):
                self.assertNotRegex(
                    text,
                    rf"\$\{{{name}:-[^}}]+\}}",
                    f"{name} must not silently fall back to a known default",
                )
                self.assertRegex(
                    text,
                    rf"\$\{{{name}:\?[^}}]+\}}",
                    f"{name} must fail closed when missing",
                )

        self.assertNotIn("sheriff-dev-only", text)
        self.assertNotIn("admin-dev-only", text)


if __name__ == "__main__":
    unittest.main()
