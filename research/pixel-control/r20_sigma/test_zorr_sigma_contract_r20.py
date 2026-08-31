import copy
import json
from pathlib import Path
import unittest

import numpy as np

import zorr_sigma_contract_r20 as r20

ROOT = Path(__file__).resolve().parent
R04 = json.loads((ROOT / "zorr_backend_manifest_r04.json").read_text(encoding="utf-8"))
R16 = json.loads((ROOT / "zorr_timestep_contract_r16_manifest.json").read_text(encoding="utf-8"))
DEFAULTS = dict(r20.EXPECTED_SIGMA_DEFAULTS)

EXPECTED_FULL_SHA = "dd2b4c6776c6cad5ddb460a30f3906d4ccb3b1f694bf9e6e9e89a2dba07d578f"
EXPECTED_DENOISE_SHA = "e03af84d27673cb3cd8226551a084405224f01ead40a3ccc6c0189b993da24ec"
EXPECTED_SUCCESSOR_SHA = "600d524c9374a76235a04b0665cfdf03752792232a57b4f2d402ceabf8a1a1e2"


class TestSigmaContractR20(unittest.TestCase):
    def test_predecessor_identities_are_exact(self):
        got = r20.require_predecessor_identity(ROOT)
        self.assertEqual(len(got), 4)

    def test_upstream_identity_constants_are_exact(self):
        self.assertEqual(r20.PINNED_DIFFUSERS_REF, "c1bf18c92c6285334adcaac7e75ef8946a227f49")
        self.assertEqual(r20.FRESH_DIFFUSERS_MAIN, "2e618cb6027037597cf80905fc3e356a71923087")
        self.assertEqual(r20.EULER_SCHEDULER_BLOB, "eac6efe18aaf775b846e7536fd972686d3ec9683")
        self.assertEqual(r20.EULER_TEST_BLOB, "ee99465abfc39e7a7ce7a6734b22dbeb42df5efd")
        self.assertEqual(r20.PIPELINE_BLOB, "3f18cbe21d0fe12f89859d188dba2a487f3d87c5")

    def test_sigma_affecting_defaults_are_fail_closed(self):
        r20.validate_effective_scheduler_contract(R16["selected_scheduler_config"], DEFAULTS)
        for key in DEFAULTS:
            bad = copy.deepcopy(DEFAULTS)
            if isinstance(bad[key], bool):
                bad[key] = not bad[key]
            elif bad[key] is None:
                bad[key] = [0.1]
            elif bad[key] == "zero":
                bad[key] = "sigma_min"
            elif bad[key] == "discrete":
                bad[key] = "continuous"
            else:
                self.fail(f"unhandled test default {key}")
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    r20.validate_effective_scheduler_contract(R16["selected_scheduler_config"], bad)

    def test_scheduler_config_drift_changes_contract_gate(self):
        bad = copy.deepcopy(R16["selected_scheduler_config"])
        bad["beta_start"] = 0.0009
        with self.assertRaises(ValueError):
            r20.validate_effective_scheduler_contract(bad, DEFAULTS)

    def test_full_sigma_vector_is_binary32_with_terminal_zero(self):
        c, full, denoise, successor = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(full.dtype, np.float32)
        self.assertEqual(c.full_sigma_count, 21)
        self.assertEqual(float(full[-1]), 0.0)
        self.assertEqual(full[-1].tobytes().hex(), "00000000")
        self.assertEqual(len(denoise), 19)
        self.assertEqual(len(successor), 19)

    def test_full_sigma_content_fingerprint_is_exact_on_measured_host(self):
        c, full, _, _ = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(c.full_sigmas_sha256_le_f32, EXPECTED_FULL_SHA)
        self.assertEqual(r20.float32_sha256(full), EXPECTED_FULL_SHA)

    def test_effective_denoise_and_successor_fingerprints_are_exact(self):
        c, _, denoise, successor = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(c.denoise_sigmas_sha256_le_f32, EXPECTED_DENOISE_SHA)
        self.assertEqual(c.successor_sigmas_sha256_le_f32, EXPECTED_SUCCESSOR_SHA)
        self.assertEqual(r20.float32_sha256(denoise), EXPECTED_DENOISE_SHA)
        self.assertEqual(r20.float32_sha256(successor), EXPECTED_SUCCESSOR_SHA)

    def test_begin_index_one_skips_timestep_951_sigma(self):
        c, full, denoise, _ = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(c.begin_index, 1)
        self.assertEqual(c.requested_timesteps[0], 951)
        self.assertNotEqual(float(full[0]), float(denoise[0]))
        self.assertEqual(full[0].tobytes().hex(), "10743041")
        self.assertEqual(denoise[0].tobytes().hex(), "41400641")

    def test_initial_add_noise_and_first_step_use_same_begin_sigma(self):
        c, full, denoise, _ = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(c.initial_add_noise_sigma_f32, c.first_step_sigma_f32)
        self.assertEqual(c.initial_add_noise_sigma_f32, float(full[1]))
        self.assertEqual(c.first_step_sigma_f32, float(denoise[0]))
        self.assertEqual(full[1].tobytes().hex(), "41400641")

    def test_last_effective_step_transitions_to_exact_zero_sigma(self):
        c, _, _, successor = r20.derive_selected_contract(R04, R16, DEFAULTS)
        self.assertEqual(c.terminal_successor_sigma_f32, 0.0)
        self.assertEqual(float(successor[-1]), 0.0)
        self.assertEqual(successor[-1].tobytes().hex(), "00000000")

    def test_strength_drift_is_rejected_by_r04_predecessor_contract(self):
        bad = copy.deepcopy(R04)
        bad["source_derived_baseline"]["strength"] = 1.0
        with self.assertRaises(ValueError):
            r20.derive_selected_contract(bad, R16, DEFAULTS)

    def test_no_visual_or_real_runtime_pass_is_encoded(self):
        proof = json.loads((ROOT / "zorr_sigma_r20_proof.json").read_text(encoding="utf-8"))
        b = proof["truth_boundary"]
        self.assertEqual(b["REAL_DIFFUSION_RUNTIME"], "NOT PROVEN")
        self.assertEqual(b["RAW_REAL_BACKEND_LEAKAGE"], "UNKNOWN")
        self.assertEqual(b["FREE_SEAM_BACKGROUND_CONTINUITY"], "NOT MEASURED ON REAL BACKEND")
        self.assertEqual(b["PRODUCTION_VISUAL_QUALITY"], "NOT PROVEN")
        self.assertEqual(b["TARGET_R17_SIGMA_FINGERPRINT"], "NOT PROVEN")
        self.assertEqual(b["IMAGE_GENERATION_OR_EDITING"], "NONE")

    def test_controlnet_stays_unjustified_without_measured_failure(self):
        proof = json.loads((ROOT / "zorr_sigma_r20_proof.json").read_text(encoding="utf-8"))
        self.assertEqual(proof["truth_boundary"]["CONTROLNET_DEPTH_EDGE_NEED"], "NOT PROVEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
