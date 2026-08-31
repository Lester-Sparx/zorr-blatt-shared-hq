import copy
import json
from pathlib import Path
import unittest

import zorr_timestep_contract_r16 as r16

ROOT = Path(__file__).resolve().parent
R04 = json.loads((ROOT / "zorr_backend_manifest_r04.json").read_text(encoding="utf-8"))
R16 = json.loads((ROOT / "zorr_timestep_contract_r16_manifest.json").read_text(encoding="utf-8"))
SCHED = R16["selected_scheduler_config"]


class TestTimestepContractR16(unittest.TestCase):
    def test_r04_selected_baseline_is_exact(self):
        r16.validate_r04_manifest(R04)

    def test_scheduler_config_is_exact(self):
        r16.validate_scheduler_config(SCHED)

    def test_requested_euler_leading_schedule_is_exact(self):
        got = r16.euler_leading_timesteps(20, SCHED)
        self.assertEqual(got, [951,901,851,801,751,701,651,601,551,501,451,401,351,301,251,201,151,101,51,1])

    def test_strength_099_means_nineteen_effective_steps(self):
        c = r16.derive_selected_r04_contract(R04, SCHED)
        self.assertEqual(c.init_timestep, 19)
        self.assertEqual(c.t_start, 1)
        self.assertEqual(c.effective_denoising_steps, 19)
        self.assertEqual(len(c.effective_timesteps), 19)

    def test_effective_schedule_and_initial_noise_timestep_are_exact(self):
        c = r16.derive_selected_r04_contract(R04, SCHED)
        self.assertEqual(c.effective_timesteps, [901,851,801,751,701,651,601,551,501,451,401,351,301,251,201,151,101,51,1])
        self.assertEqual(c.initial_noise_timestep, 901)

    def test_requested_steps_are_not_mislabeled_as_actual_unet_iterations(self):
        c = r16.derive_selected_r04_contract(R04, SCHED)
        self.assertEqual(c.requested_num_inference_steps, 20)
        self.assertNotEqual(c.requested_num_inference_steps, c.effective_denoising_steps)

    def test_r04_baseline_drift_fails_closed(self):
        bad = copy.deepcopy(R04)
        bad["source_derived_baseline"]["strength"] = 1.0
        with self.assertRaises(ValueError):
            r16.validate_r04_manifest(bad)

    def test_scheduler_drift_fails_closed(self):
        bad = dict(SCHED)
        bad["timestep_spacing"] = "trailing"
        with self.assertRaises(ValueError):
            r16.validate_scheduler_config(bad)

    def test_manifest_records_identical_relevant_blobs_at_fresh_main(self):
        fw = R16["framework"]
        self.assertNotEqual(fw["pinned_ref"], fw["fresh_main_ref"])
        self.assertEqual(fw["pipeline_blob_pinned"], fw["pipeline_blob_fresh_main"])
        self.assertEqual(fw["euler_scheduler_blob_pinned"], fw["euler_scheduler_blob_fresh_main"])
        self.assertEqual(fw["euler_test_blob_pinned"], fw["euler_test_blob_fresh_main"])

    def test_truth_boundary_stays_non_runtime(self):
        b = R16["boundaries"]
        self.assertEqual(b["real_diffusion_runtime"], "NOT PROVEN")
        self.assertEqual(b["raw_real_backend_leakage"], "UNKNOWN")
        self.assertEqual(b["production_visual_quality"], "NOT PROVEN")
        self.assertEqual(b["sigma_vector"], "NOT PROVEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
