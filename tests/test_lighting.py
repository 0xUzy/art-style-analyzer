"""Tests for lighting.py"""

from analyzer.lighting import analyze_lighting


class TestAnalyzeLighting:
    def test_returns_expected_keys(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        expected_keys = {
            "mean_brightness", "median_brightness", "brightness_std",
            "contrast", "brightness_skewness",
            "key_type", "key_confidence",
            "low_key_ratio", "high_key_ratio", "mid_key_ratio",
            "tonal_range", "shadow_detail", "highlight_detail",
            "dramatic_lighting", "micro_contrast",
            "light_direction", "light_direction_score",
            "highlights_pct", "shadows_pct", "midtones_pct",
            "rim_lighting", "feature_vector",
        }
        assert expected_keys.issubset(result.keys())

    def test_key_type_valid(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert result["key_type"] in ("high-key", "low-key", "mid-key", "chiaroscuro")

    def test_key_confidence_in_range(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert 0 <= result["key_confidence"] <= 1

    def test_brightness_in_range(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert 0 <= result["mean_brightness"] <= 1
        assert 0 <= result["median_brightness"] <= 1

    def test_contrast_positive(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert result["contrast"] >= 0
        assert result["contrast"] <= 1

    def test_light_direction_string(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert isinstance(result["light_direction"], str)
        assert len(result["light_direction"]) > 0

    def test_rim_lighting_boolean(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        assert isinstance(result["rim_lighting"], bool)

    def test_feature_vector_length(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        # 18 base features + 10 tonal hist bins = 28
        assert len(result["feature_vector"]) == 28

    def test_percentages_sum_reasonable(self, test_image_grayscale_path):
        result = analyze_lighting(test_image_grayscale_path)
        total = result["highlights_pct"] + result["shadows_pct"] + result["midtones_pct"]
        # Ranges have intentional gaps (0.15-0.35 and 0.65-0.85), so the sum
        # can be noticeably below 1.0 on controlled test images.
        assert 0.6 <= total <= 1.2

    def test_quadrant_based_light_direction(self, test_image_grayscale_path):
        """Our test image has the brightest value (220) in the bottom-right quadrant."""
        result = analyze_lighting(test_image_grayscale_path)
        # The grayscale test image has bottom-right at 220, the brightest quadrant
        assert "bottom-right" in result["light_direction"] or result["light_direction"] == "even/diffused"

    def test_high_key_on_bright_image(self):
        """A white image should be classified high-key."""
        import numpy as np
        from PIL import Image
        import tempfile, os
        arr = np.full((50, 50), 230, dtype=np.uint8)
        img = Image.fromarray(arr, "L")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f, format="PNG")
            path = f.name
        try:
            result = analyze_lighting(path)
            assert result["key_type"] == "high-key"
        finally:
            os.unlink(path)

    def test_low_key_on_dark_image(self):
        """A dark image should be classified low-key."""
        import numpy as np
        from PIL import Image
        import tempfile, os
        arr = np.full((50, 50), 30, dtype=np.uint8)
        img = Image.fromarray(arr, "L")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f, format="PNG")
            path = f.name
        try:
            result = analyze_lighting(path)
            assert result["key_type"] == "low-key"
        finally:
            os.unlink(path)
