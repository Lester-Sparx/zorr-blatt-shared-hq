from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ZORR_OWNER_COMMAND_BAR_R03.md"
LEGACY_SCRIPT = ROOT / "tools" / "browser" / "zorr-mode-toolbar.user.js"
LEGACY_DOC = ROOT / "docs" / "ZORR_MODE_TOOLBAR_V1.md"


class ZorrOwnerCommandBarR03PolicyTests(unittest.TestCase):
    def test_r03_is_documented_as_canonical(self):
        self.assertTrue(DOC.is_file(), "R03 canonical doc is required")
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("STATUS = CANONICAL OWNER COMMAND SURFACE", text)
        self.assertIn("ZORR_OWNER_COMMAND_BAR_R03.zip", text)
        self.assertIn("3c30f1cdc47d270030ea978c4bcdba8f6eb290b8e9dae8a1431df6edc97442a2", text)
        self.assertIn("OWNER_PC_PHYSICAL_PASS = YES", text)

    def test_compact_surface_is_locked(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("ZORR MODE | ДЕЛАЙ | ПРОДОЛЖАЙ | ДЕЛАЙ ДО PASS | ПРОВЕРЬ", text)
        self.assertIn("reuses the already working R02", text)

    def test_temporary_userscript_path_is_retired(self):
        self.assertFalse(LEGACY_SCRIPT.exists(), "Violentmonkey userscript must not remain a canonical fallback")
        self.assertFalse(LEGACY_DOC.exists(), "legacy userscript install doc must be removed")
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("Violentmonkey userscript is superseded", text)
        self.assertIn("R03 MV3 extension only", text)


if __name__ == "__main__":
    unittest.main()
