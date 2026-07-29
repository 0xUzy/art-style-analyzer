"""Tests for composition.py"""

import numpy as np
from analyzer.composition import analyze_composition, _classify_composition


class TestClassifyComposition:
    def test_highly_symmetrical(self):
        assert _classify_composition(0.85, 0.3, 0.4) == "highly symmetrical"

    def test_moderately_symmetrical(self):
        assert _classify_composition(0.7, 0.3, 0.4) == "moderately symmetrical"

    def test_centrally_focused(self):
        assert _classify_composition(0.5, 0.7, 0.4) == "centrally focused"

    def test_complex_all_over(self):
        assert _classify_composition(0.4, 0.3, 0.6) == "complex, all-over"

    def test_minimal_open(self):
        assert _classify_composition(0.4, 0.3, 0.05) == "minimal, open"

    def test_asymmetrical(self):
        assert _classify_composition(0.4, 0.3, 0.3) == "asymmetrical, balanced"


class TestAnalyzeComposition:
    def test_returns_expected_keys(self, test_image_path):
        result = analyze_composition(test_image_path)
        expected_keys = {
            "edge_density", "texture_variance", "symmetry",
            "horizontal_balance", "vertical_balance", "diagonal_symmetry",
            "focal_strength", "visual_weight_distribution",
            "complexity", "simplicity", "composition_type", "feature_vector",
        }
        assert expected_keys.issubset(result.keys())

    def test_composition_type_string(self, test_image_path):
        result = analyze_composition(test_image_path)
        assert isinstance(result["composition_type"], str)
        assert len(result["composition_type"]) > 0

    def test_values_in_range(self, test_image_path):
        result = analyze_composition(test_image_path)
        for key in ("edge_density", "texture_variance", "symmetry",
                     "horizontal_balance", "vertical_balance",
                     "focal_strength", "complexity", "simplicity"):
            assert 0 <= result[key] <= 1, f"{key} = {result[key]} out of range"

    def test_edge_density_present(self, test_image_path):
        result = analyze_composition(test_image_path)
        assert result["edge_density"] > 0

    def test_feature_vector_length(self, test_image_path):
        result = analyze_composition(test_image_path)
        # 16 base + 10 lbp + 4 freq_profile = 30
        assert len(result["feature_vector"]) == 30

    def test_symmetry_and_balance_sums(self, test_image_path):
        result = analyze_composition(test_image_path)
        # symmetry is average of horizontal + vertical balance
        expected_sym = (result["horizontal_balance"] + result["vertical_balance"]) / 2
        assert abs(result["symmetry"] - expected_sym) < 0.001

    def test_simplicity_complexity_opposites(self, test_image_path):
        result = analyze_composition(test_image_path)
        # simplicity is 1 - complexity
        assert abs(result["simplicity"] + result["complexity"] - 1.0) < 0.001
