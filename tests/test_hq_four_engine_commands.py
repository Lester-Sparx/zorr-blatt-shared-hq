from __future__ import annotations

from pathlib import Path
import unittest

from scripts.hq_engine_profiles import (
    ENGINE_PROFILES,
    build_activation_contract,
    resolve_engine_command,
)


class FourEngineCommandTests(unittest.TestCase):
    def test_exactly_four_engines_exist(self) -> None:
        self.assertEqual(set(ENGINE_PROFILES), {"SALVADOR", "GAUZZ", "LYNCH", "HOKUSAI"})
        self.assertEqual(len(ENGINE_PROFILES), 4)

    def test_first_token_activates_case_insensitively(self) -> None:
        cases = {
            "salvador draw this": "SALVADOR",
            "GAUZZ measure this": "GAUZZ",
            "Lynch stage the shot": "LYNCH",
            "hokusai design variants": "HOKUSAI",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                profile = resolve_engine_command(message)
                self.assertIsNotNone(profile)
                self.assertEqual(profile["engine_id"], expected)

    def test_unknown_or_embedded_names_do_not_activate(self) -> None:
        self.assertIsNone(resolve_engine_command("duncan"))
        self.assertIsNone(resolve_engine_command("please ask lynch"))
        self.assertIsNone(resolve_engine_command(""))

    def test_all_profiles_preserve_duncan_root_and_have_unique_scope(self) -> None:
        scopes = set()
        for engine_id, profile in ENGINE_PROFILES.items():
            self.assertEqual(profile["engine_id"], engine_id)
            self.assertEqual(profile["root_identity"], "DUNCAN PRIME")
            self.assertTrue(profile["scope"])
            self.assertTrue(profile["source_refs"])
            self.assertTrue(profile["skill_domains"])
            self.assertTrue(profile["restore_query"])
            self.assertTrue(profile["learning_query"])
            scopes.add(profile["scope"])
        self.assertEqual(len(scopes), 4)

    def test_activation_contract_requires_durable_restore_and_transfer_gate(self) -> None:
        contract = build_activation_contract("lynch stage an unfamiliar confrontation")
        self.assertEqual(contract["schema"], "ZB_ENGINE_ACTIVATION_V1")
        self.assertEqual(contract["engine_id"], "LYNCH")
        self.assertEqual(contract["root_identity"], "DUNCAN PRIME")
        self.assertEqual(contract["skill_state_authority"], "VERIFIED_EVIDENCE_ONLY")
        self.assertIn("CURRENT_TASK_EVIDENCE", contract["required_restore"])
        self.assertIn("UNIFIED_ARCHIVE_CONTEXT", contract["required_restore"])
        self.assertIn("VERIFIED_LESSONS", contract["required_restore"])
        self.assertIn("ACCEPTED_OPTIMIZED_POLICY", contract["required_restore"])
        self.assertEqual(
            contract["learning_gate"],
            [
                "SOURCE_OR_LESSON",
                "EXERCISE",
                "OBJECTIVE_CHECK",
                "REGRESSION",
                "CHANGED_OR_UNSEEN_TRANSFER",
                "DURABLE_EVIDENCE",
                "PROVEN_OR_PARTIAL_OR_FAILED",
            ],
        )

    def test_engine_boundaries_do_not_collapse_into_one_profile(self) -> None:
        self.assertEqual(ENGINE_PROFILES["SALVADOR"]["scope"], "DRAW")
        self.assertEqual(ENGINE_PROFILES["GAUZZ"]["scope"], "MATH_QC")
        self.assertEqual(ENGINE_PROFILES["LYNCH"]["scope"], "SCENE_DIRECTING")
        self.assertEqual(ENGINE_PROFILES["HOKUSAI"]["scope"], "DESIGN")

    def test_bootstrap_names_exact_four_commands_and_root_is_not_fifth_engine(self) -> None:
        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("There are exactly four production engines", agents)
        self.assertIn("DUNCAN PRIME` is their shared root identity/memory/learning authority and is NOT a fifth engine", agents)
        for engine_id in ("SALVADOR", "GAUZZ", "LYNCH", "HOKUSAI"):
            self.assertIn(f"`{engine_id}`", agents)

    def test_durable_profile_files_match_registry_scope_and_learning_gate(self) -> None:
        root = Path("hq/engine-profiles")
        index = (root / "FOUR_ENGINE_R01.md").read_text(encoding="utf-8")
        self.assertIn("ENGINE_COUNT = 4", index)
        self.assertIn("DUNCAN PRIME", index)
        for engine_id, profile in ENGINE_PROFILES.items():
            text = (root / f"{engine_id}.md").read_text(encoding="utf-8")
            self.assertIn(f"ROOT = DUNCAN PRIME", text)
            self.assertIn(f"SCOPE = {profile['scope']}", text)
            self.assertIn("CHANGED_OR_UNSEEN_TRANSFER", text)
            self.assertIn("DURABLE_EVIDENCE", text)


if __name__ == "__main__":
    unittest.main()
