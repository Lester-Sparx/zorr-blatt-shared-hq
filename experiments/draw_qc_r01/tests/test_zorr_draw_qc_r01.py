import unittest

import cv2
import numpy as np

from experiments.draw_qc_r01.zorr_draw_qc import analyze_image_bgr, evaluate_metrics


class DrawQCR01Tests(unittest.TestCase):
    def test_evaluate_metrics_passes_anchor_envelope(self):
        verdict = evaluate_metrics(
            {
                "tone_bands": 5,
                "strong_edge_density": 0.109,
                "deep_ink_coverage": 0.031,
                "line_hierarchy_ratio": 5.0,
                "high_freq_laplacian_variance": 520.0,
            }
        )
        self.assertEqual(verdict["verdict"], "PASS")
        self.assertEqual(verdict["failures"], [])

    def test_evaluate_metrics_fails_known_rendered_pattern(self):
        verdict = evaluate_metrics(
            {
                "tone_bands": 7,
                "strong_edge_density": 0.158,
                "deep_ink_coverage": 0.020,
                "line_hierarchy_ratio": 1.4,
                "high_freq_laplacian_variance": 1469.0,
            }
        )
        self.assertEqual(verdict["verdict"], "FAIL")
        self.assertIn("STYLE_TONE_COUNT_FAIL", verdict["failures"])
        self.assertIn("STYLE_EDGE_DENSITY_FAIL", verdict["failures"])
        self.assertIn("STYLE_LINE_HIERARCHY_FAIL", verdict["failures"])
        self.assertIn("STYLE_TOO_NOISY", verdict["failures"])

    def test_analyze_image_uses_opencv_metrics(self):
        image = np.full((160, 160, 3), 250, dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (139, 139), (110, 80, 60), -1)
        cv2.rectangle(image, (20, 20), (139, 59), (95, 70, 55), -1)
        cv2.rectangle(image, (20, 60), (139, 89), (80, 60, 50), -1)
        cv2.rectangle(image, (20, 90), (139, 114), (65, 50, 42), -1)
        cv2.rectangle(image, (20, 115), (139, 139), (50, 40, 35), -1)
        cv2.line(image, (35, 40), (125, 40), (10, 10, 10), 1)
        cv2.line(image, (35, 75), (125, 75), (10, 10, 10), 4)
        cv2.line(image, (35, 125), (125, 125), (10, 10, 10), 8)

        metrics = analyze_image_bgr(image, target_width=397)

        self.assertGreaterEqual(metrics["tone_bands"], 4)
        self.assertLessEqual(metrics["tone_bands"], 6)
        self.assertGreater(metrics["strong_edge_density"], 0.0)
        self.assertGreater(metrics["deep_ink_coverage"], 0.0)
        self.assertGreater(metrics["line_hierarchy_ratio"], 1.0)
        self.assertGreater(metrics["high_freq_laplacian_variance"], 0.0)


if __name__ == "__main__":
    unittest.main()
