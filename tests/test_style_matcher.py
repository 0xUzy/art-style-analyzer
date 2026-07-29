"""Tests for style_matcher.py"""

import json
import os
from analyzer.style_matcher import (
    _build_style_prompt,
    load_styles,
    _saturation_label,
    _diversity_label,
    _texture_label,
    _edge_label,
)


def _make_style(name="TestStyle", **kwargs):
    style = {
        "name": name,
        "description": "A test style description.",
        "techniques": ["technique_a", "technique_b"],
        "palette_bias": ["red", "blue"],
        "mood": ["happy", "calm"],
        "era": "Modern",
        "movement": "Test Movement",
        "characteristics": {},
        "influences": "Test influences",
        "key_artists": ["Artist One", "Artist Two"],
        "style_transfer_prompt": "Convert this into test style.",
    }
    style.update(kwargs)
    return style


class TestBuildStylePrompt:
    def test_returns_string(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_contains_style_name(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert "TestStyle" in prompt

    def test_contains_description(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert "A test style description." in prompt

    def test_contains_techniques(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert "technique_a" in prompt
        assert "technique_b" in prompt

    def test_contains_palette_bias(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert "red" in prompt
        assert "blue" in prompt

    def test_contains_mood(self):
        style = _make_style()
        prompt = _build_style_prompt(style)
        assert "happy" in prompt
        assert "calm" in prompt

    def test_empty_techniques(self):
        style = _make_style(techniques=[])
        prompt = _build_style_prompt(style)
        # Should still work without techniques
        assert "TestStyle" in prompt

    def test_empty_mood(self):
        style = _make_style(mood=[])
        prompt = _build_style_prompt(style)
        assert "TestStyle" in prompt

    def test_empty_palette(self):
        style = _make_style(palette_bias=[])
        prompt = _build_style_prompt(style)
        assert "TestStyle" in prompt


class TestLoadStyles:
    def test_loads_styles_file(self):
        data = load_styles()
        assert "styles" in data
        assert len(data["styles"]) == 35

    def test_styles_have_required_keys(self):
        data = load_styles()
        required = {"name", "era", "movement", "characteristics",
                     "palette_bias", "techniques", "mood",
                     "description", "style_transfer_prompt",
                     "influences", "key_artists"}
        for style in data["styles"]:
            missing = required - set(style.keys())
            assert not missing, f"Style '{style.get('name', '?')}' missing keys: {missing}"

    def test_all_style_names_are_unique(self):
        data = load_styles()
        names = [s["name"] for s in data["styles"]]
        assert len(names) == len(set(names))

    def test_characteristics_have_min_max(self):
        data = load_styles()
        for style in data["styles"]:
            for field, bounds in style["characteristics"].items():
                assert "min" in bounds, f"{style['name']}.{field} missing min"
                assert "max" in bounds, f"{style['name']}.{field} missing max"
                assert 0 <= bounds["min"] <= bounds["max"] <= 1, \
                    f"{style['name']}.{field} bounds invalid: [{bounds['min']}, {bounds['max']}]"


class TestHelperLabelFunctions:
    def test_saturation_label_all_ranges(self):
        ranges = [(0.1, "muted"), (0.3, "moderately"), (0.5, "moderate"),
                  (0.7, "saturated"), (0.9, "vivid")]
        for val, expected_sub in ranges:
            assert expected_sub in _saturation_label(val), f"Failed at {val}"

    def test_diversity_label_all_ranges(self):
        ranges = [(0.1, "limited"), (0.3, "limited"), (0.5, "moderate"),
                  (0.7, "diverse"), (0.9, "diverse")]
        for val, expected_sub in ranges:
            assert expected_sub in _diversity_label(val), f"Failed at {val}"

    def test_texture_label_all_ranges(self):
        ranges = [(0.1, "smooth"), (0.3, "smooth"), (0.5, "moderate"),
                  (0.7, "textured"), (0.9, "heavily")]
        for val, expected_sub in ranges:
            assert expected_sub in _texture_label(val), f"Failed at {val}"

    def test_edge_label_all_ranges(self):
        ranges = [(0.03, "few"), (0.1, "soft"), (0.2, "moderate"),
                  (0.4, "sharp"), (0.6, "sharp")]
        for val, expected_sub in ranges:
            assert expected_sub in _edge_label(val), f"Failed at {val}"
