import unittest

import cv2
import numpy as np

from experiments.draw_qc_r01.zorr_draw_qc import analyze_image_bgr, analyze_region_bgr, evaluate_metrics


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

    def test_region_mask_excludes_character_truth_black_mass(self):
        image = np.full((180, 180, 3), 250, dtype=np.uint8)

        # Skin field with five controlled tone bands.
        cv2.rectangle(image, (45, 50), (134, 149), (112, 88, 72), -1)
        cv2.rectangle(image, (45, 50), (134, 69), (104, 82, 68), -1)
        cv2.rectangle(image, (45, 70), (134, 89), (96, 76, 64), -1)
        cv2.rectangle(image, (45, 90), (134, 109), (88, 70, 60), -1)
        cv2.rectangle(image, (45, 110), (134, 129), (80, 64, 56), -1)
        cv2.rectangle(image, (45, 130), (134, 149), (72, 58, 52), -1)

        # Character Truth black hair mass touching the face component.
        cv2.rectangle(image, (35, 20), (144, 54), (5, 5, 5), -1)

        # Controlled structural lines inside the skin region.
        cv2.line(image, (62, 78), (118, 78), (10, 10, 10), 1)
        cv2.line(image, (62, 103), (118, 103), (10, 10, 10), 4)
        cv2.line(image, (62, 133), (118, 133), (10, 10, 10), 8)

        face_mask = np.zeros((180, 180), dtype=np.uint8)
        cv2.rectangle(face_mask, (45, 55), (134, 149), 255, -1)

        whole_metrics = analyze_image_bgr(image, target_width=397)
        face_metrics = analyze_region_bgr(image, face_mask, target_width=397)

        self.assertGreater(whole_metrics["deep_ink_coverage"], face_metrics["deep_ink_coverage"])
        self.assertLess(face_metrics["deep_ink_coverage"], 0.05)
        self.assertGreaterEqual(face_metrics["tone_bands"], 4)
        self.assertLessEqual(face_metrics["tone_bands"], 6)

    def test_region_mask_requires_same_image_shape(self):
        image = np.full((100, 100, 3), 250, dtype=np.uint8)
        wrong_mask = np.ones((50, 50), dtype=np.uint8)

        with self.assertRaises(ValueError):
            analyze_region_bgr(image, wrong_mask)

    def test_region_mask_requires_non_empty_region(self):
        image = np.full((100, 100, 3), 250, dtype=np.uint8)
        empty_mask = np.zeros((100, 100), dtype=np.uint8)

        with self.assertRaises(ValueError):
            analyze_region_bgr(image, empty_mask)


if __name__ == "__main__":
    unittest.main()
