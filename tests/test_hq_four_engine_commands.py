from __future__ import annotations

from pathlib import Path
import unittest

from scripts.hq_engine_profiles import (
    COMMON_BASE_PATH,
    ENGINE_IDS,
    ENGINE_PROFILES,
    build_activation_contract,
    resolve_engine_command,
)


class FourEngineCommandTests(unittest.TestCase):
    def test_exactly_four_engines_exist(self) -> None:
        expected = ("SALVADOR", "GAUZZ", "LYNCH", "HOKUSAI")
        self.assertEqual(ENGINE_IDS, expected)
        self.assertEqual(set(ENGINE_PROFILES), set(expected))
        self.assertEqual(len(ENGINE_PROFILES), 4)

    def test_command_is_exactly_engine_name_case_insensitive(self) -> None:
        cases = {
            "salvador": "SALVADOR",
            "GAUZZ measure this": "GAUZZ",
            "Lynch stage the shot": "LYNCH",
            "hokusai design variants": "HOKUSAI",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                profile = resolve_engine_command(message)
                self.assertIsNotNone(profile)
                self.assertEqual(profile["engine_id"], expected)
                self.assertEqual(profile["command"], expected)

    def test_no_alias_or_fifth_engine_command_exists(self) -> None:
        for message in ("duncan", "draw", "math", "scene", "design", "director", "sal", "lynch-mode"):
            with self.subTest(message=message):
                self.assertIsNone(resolve_engine_command(message))
        self.assertIsNone(resolve_engine_command("please ask lynch"))
        self.assertIsNone(resolve_engine_command(""))

    def test_all_profiles_preserve_duncan_root_and_have_unique_scope(self) -> None:
        scopes = set()
        for engine_id, profile in ENGINE_PROFILES.items():
            self.assertEqual(profile["engine_id"], engine_id)
            self.assertEqual(profile["command"], engine_id)
            self.assertEqual(profile["root_identity"], "DUNCAN PRIME")
            self.assertEqual(profile["profile_path"], f"hq/engine-profiles/{engine_id}.md")
            self.assertTrue(profile["scope"])
            self.assertTrue(profile["source_refs"])
            self.assertTrue(profile["skill_domains"])
            self.assertTrue(profile["restore_query"])
            self.assertTrue(profile["learning_query"])
            scopes.add(profile["scope"])
        self.assertEqual(len(scopes), 4)

    def test_activation_contract_is_one_common_learning_base(self) -> None:
        contract = build_activation_contract("lynch stage an unfamiliar confrontation")
        self.assertEqual(contract["schema"], "ZB_ENGINE_ACTIVATION_V1")
        self.assertEqual(contract["status"], "ACTIVATE")
        self.assertEqual(contract["engine_count"], 4)
        self.assertEqual(contract["engine_id"], "LYNCH")
        self.assertEqual(contract["command"], "LYNCH")
        self.assertEqual(contract["command_law"], "COMMAND_EQUALS_ENGINE_NAME")
        self.assertEqual(contract["aliases"], [])
        self.assertEqual(contract["root_identity"], "DUNCAN PRIME")
        self.assertEqual(contract["common_base_path"], COMMON_BASE_PATH)
        self.assertEqual(contract["profile_path"], "hq/engine-profiles/LYNCH.md")
        self.assertEqual(contract["skill_state_authority"], "VERIFIED_EVIDENCE_ONLY")
        self.assertIn("CURRENT_TASK_EVIDENCE", contract["required_restore"])
        self.assertIn("UNIFIED_ARCHIVE_CONTEXT", contract["required_restore"])
        self.assertIn("VERIFIED_LESSONS", contract["required_restore"])
        self.assertIn("ACCEPTED_OPTIMIZED_POLICY", contract["required_restore"])
        self.assertIn("REGRESSION", contract["learning_gate"])
        self.assertIn("CHANGED_OR_UNSEEN_TRANSFER", contract["learning_gate"])
        self.assertFalse(contract["stale_derived_state_may_override_fresh_evidence"])

    def test_engine_boundaries_do_not_collapse_into_one_profile(self) -> None:
        self.assertEqual(ENGINE_PROFILES["SALVADOR"]["scope"], "DRAW")
        self.assertEqual(ENGINE_PROFILES["GAUZZ"]["scope"], "MATH_QC")
        self.assertEqual(ENGINE_PROFILES["LYNCH"]["scope"], "SCENE_DIRECTING")
        self.assertEqual(ENGINE_PROFILES["HOKUSAI"]["scope"], "DESIGN")

    def test_common_manifest_is_the_single_four_engine_state(self) -> None:
        text = Path(COMMON_BASE_PATH).read_text(encoding="utf-8")
        self.assertIn("ENGINE_COUNT = 4", text)
        self.assertIn("ROOT_IS_ENGINE = NO", text)
        self.assertIn("ROOT_IS_COMMAND = NO", text)
        self.assertIn("COMMAND = ENGINE_NAME", text)
        self.assertIn("COMMANDS = SALVADOR | GAUZZ | LYNCH | HOKUSAI", text)
        self.assertIn("ALIASES = NONE", text)
        self.assertIn("GENERAL_STATE = FOUR_ENGINES_ONE_DURABLE_ROOT_ONE_LEARNING_BASE", text)
        self.assertIn("MATURE_OPEN_SOURCE", text)

    def test_durable_profile_files_match_registry_and_common_base(self) -> None:
        for engine_id, profile in ENGINE_PROFILES.items():
            with self.subTest(engine_id=engine_id):
                text = Path(profile["profile_path"]).read_text(encoding="utf-8")
                self.assertIn(f"ENGINE = {engine_id}", text)
                self.assertIn(f"COMMAND = {engine_id}", text)
                self.assertIn(f"SCOPE = {profile['scope']}", text)
                self.assertIn(f"COMMON_BASE = {COMMON_BASE_PATH}", text)
                self.assertIn("SKILL_STATE_AUTHORITY = VERIFIED_EVIDENCE_ONLY", text)
                self.assertIn("REGRESSION", text)
                self.assertIn("CHANGED_OR_UNSEEN_TRANSFER", text)

    def test_bootstrap_names_only_the_same_four_engine_commands(self) -> None:
        agents = Path("AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("There are exactly four production engines", agents)
        self.assertIn("`DUNCAN PRIME` is their shared root", agents)
        for engine_id in ENGINE_IDS:
            self.assertIn(f"`{engine_id}`", agents)
        self.assertIn("is NOT a fifth engine", agents)


if __name__ == "__main__":
    unittest.main()
