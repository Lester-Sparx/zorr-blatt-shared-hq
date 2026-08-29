from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "browser" / "zorr-mode-toolbar.user.js"
DOC = ROOT / "docs" / "ZORR_MODE_TOOLBAR_V1.md"

PRIMARY = ["ZORR MODE", "Делай", "Продолжить", "Проверить", "Стоп", "⋯"]
PROMPTS = {
    "ZORR MODE": "ZORR MODE",
    "Делай": "ZORR MODE\\nДЕЛАЙ ДО PASS",
    "Продолжить": "ZORR MODE\\nПРОДОЛЖАЙ ОТ СВЕЖЕГО DURABLE СОСТОЯНИЯ. НЕ НАЧИНАЙ ЗАНОВО. ДОВЕДИ ДО PASS ИЛИ ОДНОГО ТОЧНОГО BLOCKER.",
    "Проверить": "ZORR MODE\\nТОЛЬКО СВЕЖАЯ ПРОВЕРКА. НИЧЕГО НЕ МЕНЯЙ. ПРОВЕРЬ EXACT HEAD / TESTS / RUNTIME EVIDENCE И ВЕРНИ PASS, FAIL ИЛИ NOT PROVEN.",
}


class ZorrModeToolbarContractTests(unittest.TestCase):
    def script_text(self) -> str:
        self.assertTrue(SCRIPT.is_file(), "userscript is required")
        return SCRIPT.read_text(encoding="utf-8")

    def test_metadata_is_chatgpt_only_and_dependency_free(self):
        text = self.script_text()
        self.assertIn("// @match        https://chatgpt.com/*", text)
        self.assertNotIn("@require", text)
        self.assertNotRegex(text, r"\bfetch\s*\(")
        self.assertNotIn("XMLHttpRequest", text)
        self.assertNotIn("WebSocket", text)

    def test_primary_button_order_is_exact(self):
        text = self.script_text()
        marker = re.search(r"const PRIMARY_ACTIONS = \[(.*?)\];", text, re.S)
        self.assertIsNotNone(marker, "PRIMARY_ACTIONS array is required")
        body = marker.group(1)
        positions = [body.find(f'label: "{label}"') for label in PRIMARY]
        self.assertTrue(all(pos >= 0 for pos in positions), positions)
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(body.count("label:"), len(PRIMARY))

    def test_exact_prompts_are_bound(self):
        text = self.script_text()
        for label, prompt in PROMPTS.items():
            with self.subTest(label=label):
                self.assertIn(f'"{prompt}"', text)
        self.assertIn("БРЕЙНШТОРМ. НЕ РЕАЛИЗОВЫВАЙ.", text)

    def test_internal_agents_are_not_primary_buttons(self):
        text = self.script_text()
        marker = re.search(r"const PRIMARY_ACTIONS = \[(.*?)\];", text, re.S)
        self.assertIsNotNone(marker)
        body = marker.group(1)
        for forbidden in ("LESTER", "DUNCAN", "JINGO", "SHERIFF", "COPILOT"):
            self.assertNotIn(forbidden, body.upper())

    def test_stop_is_local_non_destructive(self):
        text = self.script_text()
        self.assertIn("function stopGeneration", text)
        self.assertIn("STOP_NOT_AVAILABLE", text)
        self.assertNotIn('sendPrompt("СТОП', text)

    def test_install_doc_uses_oss_manager_and_raw_script(self):
        self.assertTrue(DOC.is_file(), "install doc is required")
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("Violentmonkey", text)
        self.assertIn("tools/browser/zorr-mode-toolbar.user.js", text)
        self.assertIn("raw.githubusercontent.com", text)
        self.assertIn("browser security", text.lower())


if __name__ == "__main__":
    unittest.main()
