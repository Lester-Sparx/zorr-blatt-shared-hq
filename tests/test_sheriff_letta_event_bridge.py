from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "config" / "sheriff" / "integrations" / "letta" / "zorr-sheriff-events.ts"
INSTALLER = ROOT / "config" / "sheriff" / "integrations" / "letta" / "Install-SheriffLettaBridge.ps1"
COMPOSE = ROOT / "config" / "sheriff" / "docker-compose.yml"


class SheriffLettaEventBridgeTest(unittest.TestCase):
    def test_agent_scoped_mod_emits_real_turn_and_failure_events(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('letta.events.on("turn_start"', text)
        self.assertIn('letta.events.on("tool_end"', text)
        self.assertIn('letta.events.on("llm_end"', text)
        self.assertIn('"zb.agent.task.started"', text)
        self.assertIn('"zb.agent.result"', text)
        self.assertIn('incidentAttribution: "NONE"', text)
        self.assertNotIn('status: "PASS"', text)

    def test_bridge_reuses_internal_worker_container_without_new_port(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn('"exec", "-i"', text)
        self.assertIn("zb-sheriff-sheriff-worker-1", text)
        self.assertIn("SHERIFF_NATS_URL", text)
        self.assertNotIn("shell: true", text)
        self.assertIn("_validate_event(event)", text)
        self.assertIn("MAX_PAYLOAD_BYTES", text)

        compose = COMPOSE.read_text(encoding="utf-8")
        nats_block = compose.split("  nats:", 1)[1].split("\n  opa:", 1)[0]
        self.assertNotIn("ports:", nats_block)

    def test_bridge_does_not_send_prompt_or_tool_output(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertNotIn("event.input", text)
        self.assertNotIn("event.output", text)
        self.assertIn("toolCallId", text)
        self.assertIn("errorType", text)

    def test_bridge_has_no_agent_callable_pass_or_terminal_result_tool(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertNotIn('sheriff_report_result', text)
        self.assertNotIn('letta.tools.register', text)
        self.assertNotIn('SHERIFF_EVENT_ACCEPTED', text)
        self.assertIn('SHERIFF_EVENT_PUBLISHED', text)

    def test_identity_is_bound_and_persistent_ids_are_pseudonymous(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("SHERIFF_LETTA_AGENT_ID", text)
        self.assertIn("SHERIFF_EVENT_HMAC_KEY", text)
        self.assertIn("createHmac", text)
        self.assertIn("IDENTITY_MISMATCH", text)
        self.assertNotIn("encodeURIComponent", text)

    def test_queue_is_bounded_and_disposal_kills_active_publisher(self):
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("MAX_QUEUE_DEPTH", text)
        self.assertIn("SHERIFF_EVENT_QUEUE_FULL", text)
        self.assertIn("activeChild.kill()", text)
        self.assertIn('child.stdin.on("error"', text)
        self.assertIn('letta.events.on("conversation_close"', text)
        timeout_body = text.split("const timer = setTimeout", 1)[1].split("}, PUBLISH_TIMEOUT_MS)", 1)[0]
        self.assertNotIn("finish(", timeout_body)

    def test_installer_targets_agent_memory_mods_and_preserves_existing_files(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("$env:MEMORY_DIR", text)
        self.assertIn('Join-Path $env:MEMORY_DIR "mods"', text)
        self.assertNotIn("Remove-Item", text)
        self.assertIn("Copy-Item", text)


if __name__ == "__main__":
    unittest.main()
