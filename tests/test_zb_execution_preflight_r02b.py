from __future__ import annotations

import json
import unittest

from scripts.zb_execution_preflight import PreflightError, run_implementation_preflight
from scripts.zb_execution_profiles import PROFILES


TASKS = json.dumps(
    {
        "tasks": [
            {"name": "zb:exec:lester:implement-r01"},
            {"name": "zb:exec:lester:implement-r02a"},
            {"name": "zb:exec:duncan:qc-r01"},
        ]
    }
)


class R02BPreflightTests(unittest.TestCase):
    def _run(self, **kwargs):
        try:
            return run_implementation_preflight(**kwargs)
        except TypeError as exc:
            self.fail(f"R02B copilot_version contract missing: {exc}")

    def test_r02b_requires_exact_copilot_cli_version(self) -> None:
        self._run(
            profile=PROFILES["LESTER_IMPLEMENT_R02A"],
            task_version="3.53.1",
            task_inventory_json=TASKS,
            opencode_version=None,
            copilot_version="1.0.80",
        )
        with self.assertRaisesRegex(PreflightError, "COPILOT_VERSION_MISSING"):
            self._run(
                profile=PROFILES["LESTER_IMPLEMENT_R02A"],
                task_version="3.53.1",
                task_inventory_json=TASKS,
                opencode_version=None,
                copilot_version=None,
            )
        with self.assertRaisesRegex(PreflightError, "COPILOT_VERSION_MISMATCH"):
            self._run(
                profile=PROFILES["LESTER_IMPLEMENT_R02A"],
                task_version="3.53.1",
                task_inventory_json=TASKS,
                opencode_version=None,
                copilot_version="1.0.79",
            )

    def test_r01_and_duncan_toolchain_requirements_remain_distinct(self) -> None:
        with self.assertRaisesRegex(PreflightError, "OPENCODE_VERSION_MISSING"):
            self._run(
                profile=PROFILES["LESTER_IMPLEMENT_R01"],
                task_version="3.53.1",
                task_inventory_json=TASKS,
                opencode_version=None,
                copilot_version=None,
            )
        self._run(
            profile=PROFILES["DUNCAN_QC_R01"],
            task_version="3.53.1",
            task_inventory_json=TASKS,
            opencode_version=None,
            copilot_version=None,
        )


if __name__ == "__main__":
    unittest.main()
