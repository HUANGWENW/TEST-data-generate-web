"""Check texture pixel mapping, exact mask alpha and legacy task compatibility."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import algorithms


class TextureFillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.texture = (np.arange(3 * 5 * 3).reshape(3, 5, 3) * 5).astype(np.uint8)
        self.mask = np.full((17, 31), 255, np.uint8)
        self.mask[3:7, 8:12] = 0
        self.mask[10, 20] = 87
        self.mask_dir = self.root / 'masks'
        self.mask_dir.mkdir()
        self.mask_path = self.mask_dir / 'mask.png'
        self.texture_path = self.root / 'texture.png'
        algorithms.write_png(self.mask_path, self.mask)
        algorithms.write_png(self.texture_path, self.texture)

    def tearDown(self):
        self.temp.cleanup()

    def fill(self, name, **params):
        # Fix the crop origin so tiled pixel values are reproducible.
        with patch.object(algorithms.random, 'randrange', return_value=0), patch.object(algorithms.random, 'randint', return_value=0):
            path, = algorithms.texture_mask_files([self.mask_path], self.texture_path, self.root / name, **params)
        return algorithms.read_image(path, cv2.IMREAD_UNCHANGED)

    def test_stretch_resizes_both_axes_and_preserves_holes_and_alpha(self):
        result = self.fill('stretch', texture_fit='stretch')
        self.assertEqual(result.shape, (17, 31, 4))
        np.testing.assert_array_equal(result[:, :, :3], cv2.resize(self.texture, (31, 17), interpolation=cv2.INTER_LINEAR))
        np.testing.assert_array_equal(result[:, :, 3], self.mask)

    def test_tile_keeps_original_texture_pixels_and_overrides_legacy_flag(self):
        result = self.fill('tile', texture_fit='tile', random_crop=False)
        expected = np.tile(self.texture, (6, 7, 1))[:17, :31]
        np.testing.assert_array_equal(result[:, :, :3], expected)
        np.testing.assert_array_equal(result[:, :, 3], self.mask)

    def test_historical_random_crop_flags_keep_their_pixel_mapping(self):
        for flag, mode in ((True, 'tile'), (False, 'stretch')):
            with self.subTest(random_crop=flag):
                legacy = self.fill('legacy-' + mode, random_crop=flag)
                explicit = self.fill('explicit-' + mode, texture_fit=mode)
                np.testing.assert_array_equal(legacy, explicit)

    def test_directory_input_supports_stretch(self):
        path, = algorithms.texture_masks(self.mask_dir, self.texture_path, self.root / 'directory', texture_fit='stretch')
        result = algorithms.read_image(path, cv2.IMREAD_UNCHANGED)
        np.testing.assert_array_equal(result[:, :, :3], cv2.resize(self.texture, (31, 17), interpolation=cv2.INTER_LINEAR))
        np.testing.assert_array_equal(result[:, :, 3], self.mask)

    def test_stretch_obeys_explicit_output_limit_without_upscaling(self):
        result = self.fill('limited', texture_fit='stretch', max_side_pixels=10)
        self.assertEqual(result.shape, (5, 10, 4))
        result = self.fill('uncapped', texture_fit='stretch', max_side_pixels=100)
        self.assertEqual(result.shape, (17, 31, 4))

    def test_invalid_fill_mode_fails_before_creating_output(self):
        for mode in ('', 'auto', True, 1, []):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'texture_fit'):
                self.fill('invalid', texture_fit=mode)
        self.assertFalse((self.root / 'invalid').exists())


if __name__ == '__main__':
    unittest.main()
