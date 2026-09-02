from __future__ import annotations

import json
import re
import unittest

from _support import ROOT


COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"
DOCKERFILE = ROOT / "config" / "sheriff" / "Dockerfile.worker"
MANIFEST = ROOT / "config" / "sheriff" / "OPEN_SOURCE_COMPONENTS.json"
DIGEST_REF = re.compile(r"^[^\s@]+:[^\s@]+@sha256:[0-9a-f]{64}$")


class SheriffImageProvenanceR02Test(unittest.TestCase):
    def test_every_external_compose_image_is_digest_pinned(self) -> None:
        compose = COMPOSE.read_text(encoding="utf-8")
        images = re.findall(r"^\s*image:\s*([^\s#]+)", compose, flags=re.MULTILINE)
        self.assertTrue(images)
        for image in images:
            with self.subTest(image=image):
                self.assertRegex(image, DIGEST_REF)

    def test_worker_base_image_is_digest_pinned(self) -> None:
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        match = re.search(r"^FROM\s+([^\s]+)", dockerfile, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertRegex(match.group(1), DIGEST_REF)

    def test_oss_manifest_preserves_exact_digest_pinned_compose_refs(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = {
            item["runtimeRef"]
            for item in manifest["components"]
            if not item["runtimeRef"].startswith("local:") and "==" not in item["runtimeRef"]
        }
        compose = COMPOSE.read_text(encoding="utf-8")
        images = set(re.findall(r"^\s*image:\s*([^\s#]+)", compose, flags=re.MULTILINE))
        self.assertEqual(images, declared)
        for image in declared:
            with self.subTest(image=image):
                self.assertRegex(image, DIGEST_REF)


if __name__ == "__main__":
    unittest.main()
