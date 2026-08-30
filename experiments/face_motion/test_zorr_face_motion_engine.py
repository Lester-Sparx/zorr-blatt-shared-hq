import importlib.util
import unittest
from pathlib import Path

import numpy as np

ENGINE = Path(__file__).with_name("zorr_face_motion_engine.py")
spec = importlib.util.spec_from_file_location("zorr_face_motion_engine", ENGINE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FaceMotionEngineTests(unittest.TestCase):
    def test_local_warp_preserves_pixels_outside_mask(self):
        h, w = 160, 220
        y, x = np.mgrid[0:h, 0:w]
        image = np.stack(
            [
                (x % 256).astype(np.uint8),
                (y % 256).astype(np.uint8),
                ((x + y) % 256).astype(np.uint8),
            ],
            axis=2,
        )
        region = {
            "name": "test",
            "rbf_sigma_px": 18,
            "mask": {
                "type": "ellipse",
                "center": [110, 80],
                "axes": [45, 30],
                "feather_px": 6,
            },
            "controls": [
                {"xy": [90, 80], "delta_at_1": [-4, -5]},
                {"xy": [130, 80], "delta_at_1": [4, -5]},
            ],
            "locks": [[70, 55], [110, 48], [150, 55], [70, 105], [110, 112], [150, 105]],
        }
        out, mask, _ = mod.apply_region_warp(image, region, 1.0)
        outside = mask <= 1e-5
        self.assertTrue(np.array_equal(out[outside], image[outside]))
        changed = np.max(np.abs(out.astype(int) - image.astype(int)), axis=2)
        self.assertGreater(np.count_nonzero(changed[mask > 1e-5]), 0)

    def test_easing_endpoints(self):
        for name in ("linear", "smoothstep", "smootherstep"):
            self.assertEqual(mod.easing(name, 0), 0.0)
            self.assertEqual(mod.easing(name, 1), 1.0)


if __name__ == "__main__":
    unittest.main()
