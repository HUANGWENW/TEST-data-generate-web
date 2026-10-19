"""Regression checks for cut geometry, source resolution and alpha preservation.

Run from the repository root: python -m unittest discover -s backend/tests -v
"""
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import algorithms


class ImagePipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, name, image):
        path = self.root / name
        algorithms.write_png(path, image)
        return path

    def outline(self):
        image = np.zeros((150, 240), np.uint8)
        cv2.rectangle(image, (3, 3), (237, 147), 255, 1)
        return image

    def extract(self, image, **params):
        paths = algorithms.extract_edge_masks(self.save("边缘.png", image), self.root / "掩码", **params)
        return [algorithms.read_image(path, cv2.IMREAD_GRAYSCALE) for path in paths]

    def test_closed_outline_retains_canvas_and_boundary(self):
        for kernel in (1, 3, 11):
            with self.subTest(kernel=kernel):
                result, = self.extract(self.outline(), dilation_size=kernel)
                self.assertEqual(result.shape, (150, 240))
                self.assertEqual(int(result[3, 100]), 255)
                self.assertEqual(int(result[2, 100]), 0)
                self.assertEqual(int(result[80, 100]), 255)

    def test_small_hole_is_transparent_and_not_an_extra_part(self):
        image = self.outline()
        cv2.circle(image, (70, 60), 12, 255, 1)
        result, = self.extract(image)
        self.assertEqual(int(result[60, 70]), 0)
        self.assertEqual(int(result[60, 90]), 255)

    def test_material_island_inside_hole_is_separate(self):
        image = self.outline()
        cv2.rectangle(image, (30, 30), (180, 120), 255, 1)
        cv2.rectangle(image, (60, 50), (150, 100), 255, 1)
        results = self.extract(image, min_area=100)
        self.assertEqual(len(results), 2)
        outer = max(results, key=lambda mask: mask.size)
        self.assertEqual(int(outer[70, 100]), 0)
        self.assertEqual(int(outer[15, 100]), 255)
        self.assertTrue(any(mask[mask.shape[0] // 2, mask.shape[1] // 2] == 255 for mask in results))

    def test_notch_stays_open(self):
        image = np.zeros((150, 240), np.uint8)
        polygon = np.array([(3, 3), (70, 3), (70, 30), (100, 30), (100, 3), (237, 3), (237, 147), (3, 147)])
        cv2.polylines(image, [polygon], True, 255, 1)
        result, = self.extract(image)
        self.assertEqual(int(result[10, 85]), 0)
        self.assertEqual(int(result[40, 85]), 255)

    def test_black_and_white_edges_match(self):
        image = self.outline()
        cv2.circle(image, (70, 60), 12, 255, 1)
        expected, = self.extract(image)
        actual, = self.extract(255 - image)
        np.testing.assert_array_equal(actual, expected)

    def test_gray_antialiased_edges_are_binarized(self):
        image = self.outline()
        image[image == 255] = 145
        result, = self.extract(image)
        self.assertEqual(set(np.unique(result)), {0, 255})
        self.assertEqual(int(result[80, 100]), 255)

    def test_separate_parts_are_not_merged(self):
        image = np.zeros((200, 350), np.uint8)
        cv2.rectangle(image, (10, 10), (140, 180), 255, 1)
        cv2.rectangle(image, (200, 10), (330, 180), 255, 1)
        self.assertEqual(len(self.extract(image)), 2)

    def test_border_outline_is_supported(self):
        image = np.zeros((150, 240), np.uint8)
        cv2.rectangle(image, (0, 0), (239, 149), 255, 1)
        result, = self.extract(image)
        self.assertEqual(result.shape, image.shape)
        self.assertTrue(np.all(result == 255))

    def test_open_and_empty_images_fail_with_explanation(self):
        image = self.outline()
        image[:5, 60:100] = 0
        for source in (image, np.zeros_like(image), np.full_like(image, 255)):
            with self.subTest(source=source.sum()), self.assertRaisesRegex(ValueError, "(closed|edges)"):
                self.extract(source)

    def test_small_gap_can_be_repaired(self):
        image = self.outline()
        image[3, 70] = 0
        with self.assertRaises(ValueError):
            self.extract(image, dilation_size=1)
        result, = self.extract(image, dilation_size=3)
        self.assertEqual(int(result[80, 100]), 255)

    def test_texture_keeps_11992_by_2475_and_exact_alpha(self):
        mask = np.full((2475, 11992), 255, np.uint8)
        mask[:50, :75] = 0
        mask[300:320, 400:420] = 0
        mask[400, 500] = 87
        mask_path = self.save("大尺寸掩码.png", mask)
        texture = self.save("纹理.png", np.full((31, 47, 3), (40, 80, 120), np.uint8))
        for random_crop in (True, False):
            with self.subTest(random_crop=random_crop):
                path, = algorithms.texture_mask_files([mask_path], texture, self.root / str(random_crop), random_crop=random_crop, project_name="武穴")
                result = algorithms.read_image(path, cv2.IMREAD_UNCHANGED)
                self.assertEqual(result.shape, (2475, 11992, 4))
                np.testing.assert_array_equal(result[:, :, 3], mask)
                np.testing.assert_array_equal(result[100, 100, :3], [40, 80, 120])

    def test_explicit_limit_is_exact_and_does_not_upscale(self):
        mask_path = self.save("mask.png", np.full((2475, 11992), 255, np.uint8))
        texture = self.save("texture.png", np.full((20, 20, 3), 100, np.uint8))
        path, = algorithms.texture_mask_files([mask_path], texture, self.root / "limited", max_side_pixels=1000)
        self.assertEqual(algorithms.read_image(path, -1).shape, (206, 1000, 4))
        small = self.save("small.png", np.full((30, 40), 255, np.uint8))
        path, = algorithms.texture_mask_files([small], texture, self.root / "small", max_side_pixels=1000)
        self.assertEqual(algorithms.read_image(path, -1).shape, (30, 40, 4))

    def test_invalid_parameters_fail(self):
        for params in ({"min_area": 0}, {"dilation_size": 2}, {"edge_polarity": "invalid"}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                self.extract(self.outline(), **params)

    def test_dataset_fits_before_allocating_large_scale(self):
        source = np.full((100, 500, 4), 255, np.uint8)
        with patch.object(algorithms.cv2, "resize", wraps=cv2.resize) as resize:
            result = algorithms.prepare_part(source, angle=0, scale=1000000, max_w=640, max_h=480)
        self.assertAlmostEqual(result.shape[1], 640 * 0.95, delta=1)
        self.assertAlmostEqual(result.shape[1] / result.shape[0], 5, delta=0.05)
        self.assertEqual(resize.call_count, 1)
        self.assertLessEqual(resize.call_args.args[1][0], 640)
        self.assertLessEqual(resize.call_args.args[1][1], 480)


if __name__ == "__main__":
    unittest.main()
