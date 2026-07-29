"""Tests for color_analysis.py"""

import numpy as np
from analyzer.color_analysis import (
    rgb_to_hsv,
    classify_color_name,
    get_palette_bias,
    analyze_colors,
    _compute_color_harmony,
    _extract_color_histogram_features,
    _saturation_label,
    _diversity_label,
)


class TestRgbToHsv:
    def test_red(self):
        h, s, v = rgb_to_hsv(255, 0, 0)
        assert abs(h) < 0.01 or abs(h - 1.0) < 0.01
        assert s == 1.0
        assert v == 1.0

    def test_green(self):
        h, s, v = rgb_to_hsv(0, 255, 0)
        assert abs(h - 1 / 3) < 0.01
        assert s == 1.0
        assert v == 1.0

    def test_blue(self):
        h, s, v = rgb_to_hsv(0, 0, 255)
        assert abs(h - 2 / 3) < 0.01
        assert s == 1.0
        assert v == 1.0

    def test_black(self):
        h, s, v = rgb_to_hsv(0, 0, 0)
        assert s == 0.0
        assert v == 0.0

    def test_white(self):
        h, s, v = rgb_to_hsv(255, 255, 255)
        assert s == 0.0
        assert v == 1.0

    def test_gray(self):
        h, s, v = rgb_to_hsv(128, 128, 128)
        assert s == 0.0
        assert abs(v - 0.5) < 0.01


class TestClassifyColorName:
    def test_black(self):
        assert classify_color_name(10, 10, 10) == "black"

    def test_white(self):
        assert classify_color_name(240, 240, 240) == "white"

    def test_gray(self):
        assert classify_color_name(128, 128, 128) == "gray"

    def test_red(self):
        assert classify_color_name(200, 40, 40) == "red"

    def test_bright_red(self):
        assert classify_color_name(255, 50, 50) == "bright_red"

    def test_blue(self):
        assert classify_color_name(40, 40, 200) == "blue"

    def test_green(self):
        assert classify_color_name(40, 200, 40) == "green"

    def test_bright_green(self):
        assert classify_color_name(50, 255, 50) == "bright_green"

    def test_yellow(self):
        assert classify_color_name(200, 200, 40) == "yellow"

    def test_purple(self):
        assert classify_color_name(120, 40, 180) == "purple"

    def test_pink(self):
        assert classify_color_name(255, 100, 150) == "pink"

    def test_orange(self):
        assert classify_color_name(255, 120, 30) == "orange"

    def test_teal(self):
        assert classify_color_name(30, 180, 160) == "teal"

    def test_light_blue(self):
        assert classify_color_name(100, 180, 255) == "light_blue"

    def test_dark(self):
        assert classify_color_name(40, 30, 20) == "dark"


class TestGetPaletteBias:
    def test_returns_top_colors(self):
        colors = [(200, 40, 40), (40, 40, 200), (40, 200, 40)]
        bias = get_palette_bias(colors)
        assert len(bias) <= 5
        assert "red" in bias or "bright_red" in bias
        assert "blue" in bias
        assert "green" in bias or "bright_green" in bias

    def test_empty_palette(self):
        bias = get_palette_bias([])
        assert bias == []


class TestColorHarmony:
    def test_harmony_returns_dict(self):
        h = np.array([0.0, 0.2, 0.5, 0.8])
        s = np.array([0.5, 0.5, 0.5, 0.5])
        v = np.array([0.5, 0.5, 0.5, 0.5])
        harmony = _compute_color_harmony(h, s, v)
        assert isinstance(harmony, dict)
        for key in ("complementary", "triadic", "analogous", "monochromatic"):
            assert key in harmony
            assert 0 <= harmony[key] <= 1

    def test_all_same_hue(self):
        # Use a hue that aligns exactly with a bin center so the monochromatic
        # check (distance < 0.04) reliably triggers.
        h = np.full(100, 0.25)
        s = np.full(100, 0.5)
        v = np.full(100, 0.5)
        harmony = _compute_color_harmony(h, s, v)
        assert harmony["monochromatic"] > 0.9
        assert harmony["complementary"] < 0.1


class TestAnalyzeColors:
    def test_analyze_returns_expected_keys(self, test_image_path):
        result = analyze_colors(test_image_path)
        expected_keys = {
            "dominant_color", "palette", "palette_bias",
            "saturation", "saturation_std", "brightness", "brightness_std",
            "warmth", "temperature", "color_diversity", "color_uniformity",
            "color_harmony", "feature_vector",
        }
        assert expected_keys.issubset(result.keys())

    def test_dominant_color_structure(self, test_image_path):
        result = analyze_colors(test_image_path)
        dc = result["dominant_color"]
        for key in ("rgb", "hex", "name"):
            assert key in dc
        assert len(dc["rgb"]) == 3
        assert dc["hex"].startswith("#")
        assert len(dc["hex"]) == 7

    def test_palette_is_list_of_dicts(self, test_image_path):
        result = analyze_colors(test_image_path)
        assert isinstance(result["palette"], list)
        assert len(result["palette"]) > 0
        for swatch in result["palette"]:
            assert "rgb" in swatch
            assert "hex" in swatch
            assert "name" in swatch

    def test_feature_vector_length(self, test_image_path):
        result = analyze_colors(test_image_path)
        # 15 base features + 12 hue bins + 4 val bins + 16 sv bins = 47
        assert len(result["feature_vector"]) == 47

    def test_saturation_in_range(self, test_image_path):
        result = analyze_colors(test_image_path)
        assert 0 <= result["saturation"] <= 1

    def test_temperature_valid(self, test_image_path):
        result = analyze_colors(test_image_path)
        assert result["temperature"] in ("warm", "cool", "neutral")

    def test_solid_color(self, solid_color_path):
        """A solid red image should have low diversity and high saturation."""
        result = analyze_colors(solid_color_path)
        assert result["color_diversity"] < 0.5
        assert result["saturation"] > 0.5
        assert result["temperature"] in ("warm", "neutral")

    def test_color_harmony_scores(self, test_image_path):
        result = analyze_colors(test_image_path)
        ch = result["color_harmony"]
        for val in ch.values():
            assert 0 <= val <= 1


class TestHelpers:
    def test_saturation_label(self):
        assert "muted" in _saturation_label(0.1)
        assert "moderate" in _saturation_label(0.5)
        assert "vivid" in _saturation_label(0.9)

    def test_diversity_label(self):
        assert "limited" in _diversity_label(0.1)
        assert "moderate" in _diversity_label(0.5)
        assert "diverse" in _diversity_label(0.9)
