from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "ZORR_EXECUTION_CONSTITUTION.md"


class ZorrMathLawTests(unittest.TestCase):
    def test_math_geometry_timing_law_is_mandatory(self):
        text = CONSTITUTION.read_text(encoding="utf-8")
        self.assertIn("MATH / GEOMETRY / TIMING LAW", text)
        self.assertIn("DO NOT EYEBALL", text)
        self.assertIn("proportions", text)
        self.assertIn("camera", text)
        self.assertIn("timing", text)
        self.assertIn("trajectories", text)
        self.assertIn("collision", text)
        self.assertIn("units", text)
        self.assertIn("tolerances", text)
        self.assertIn("reproducible", text)


if __name__ == "__main__":
    unittest.main()
