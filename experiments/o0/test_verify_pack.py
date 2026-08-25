import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from verify_pack import verify_pack


class VerifyPackTest(unittest.TestCase):
    def make_fixture(self, *, payload=b"pack-bytes", **overrides):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        pack = root / "oxihuman-core-v1.ohpk"
        pack.write_bytes(payload)
        provenance = {
            "pack": {
                "age_floor_years": 18.0,
                "base_vertex_count": 21833,
                "bytes": len(payload),
                "format": "OHPK v1",
                "license": "CC0-1.0",
                "name": pack.name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "target_count": 38,
                "tier": "core",
            },
            "targets": [],
        }
        provenance["pack"].update(overrides)
        prov = root / "oxihuman-core-v1.provenance.json"
        prov.write_text(json.dumps(provenance), encoding="utf-8")
        return td, pack, prov

    def test_accepts_matching_pack_and_provenance(self):
        td, pack, prov = self.make_fixture()
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertTrue(result["ok"])
        self.assertEqual(result["actual_sha256"], hashlib.sha256(b"pack-bytes").hexdigest())
        self.assertEqual(result["actual_bytes"], len(b"pack-bytes"))

    def test_rejects_hash_mismatch(self):
        td, pack, prov = self.make_fixture(sha256="0" * 64)
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertFalse(result["ok"])
        self.assertIn("SHA256_MISMATCH", result["errors"])

    def test_rejects_byte_count_mismatch(self):
        td, pack, prov = self.make_fixture(bytes=999)
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertFalse(result["ok"])
        self.assertIn("BYTE_COUNT_MISMATCH", result["errors"])

    def test_rejects_unexpected_pack_license(self):
        td, pack, prov = self.make_fixture(license="GPL-3.0")
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertFalse(result["ok"])
        self.assertIn("LICENSE_NOT_CC0_1_0", result["errors"])

    def test_rejects_unexpected_pack_format(self):
        td, pack, prov = self.make_fixture(format="OHPK v2")
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertFalse(result["ok"])
        self.assertIn("FORMAT_NOT_OHPK_V1", result["errors"])

    def test_rejects_name_mismatch(self):
        td, pack, prov = self.make_fixture(name="other.ohpk")
        self.addCleanup(td.cleanup)
        result = verify_pack(pack, prov)
        self.assertFalse(result["ok"])
        self.assertIn("PACK_NAME_MISMATCH", result["errors"])


if __name__ == "__main__":
    unittest.main()
