import json
import os
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

from analyzer.color_analysis import _diversity_label, _saturation_label
from utils.clip_wrapper import CLIPWrapper, get_clip_wrapper


# Maps characteristic names from styles.json to the feature dictionary keys
# produced by the color/composition/lighting extractors.
_FEATURE_MAP = {
    "saturation": ("colors", "saturation"),
    "brightness": ("colors", "brightness"),
    "edge_density": ("composition", "edge_density"),
    "color_diversity": ("colors", "color_diversity"),
    "contrast": ("lighting", "contrast"),
    "warmth": ("colors", "warmth"),
    "texture_variance": ("composition", "texture_variance"),
}


# Weights used to combine CLIP similarity with the structured feature match.
_CLIP_WEIGHT = 0.60
_FEATURE_WEIGHT = 0.40


def _build_style_prompt(style):
    parts = []
    parts.append(f"An artwork in {style['name']} art style.")
    parts.append(style.get("description", ""))
    techniques = style.get("techniques", [])
    if techniques:
        parts.append("Characterized by " + "; ".join(techniques[:4]) + ".")
    palette = style.get("palette_bias", [])
    if palette:
        parts.append(f"Color palette features {', '.join(palette[:5])}.")
    mood = style.get("mood", [])
    if mood:
        parts.append(f"The mood is {', '.join(mood[:4])}.")
    return " ".join(parts)


def load_styles(data_path=None):
    if data_path is None:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "styles.json")
    with open(data_path, "r") as f:
        return json.load(f)


def _get_feature_value(feature_name: str, color_features, composition_features, lighting_features):
    """Return the extracted numeric value for a given characteristic name."""
    category, key = _FEATURE_MAP[feature_name]
    bucket = {"colors": color_features, "composition": composition_features, "lighting": lighting_features}[category]
    return float(bucket[key])


def _score_characteristic(value: float, min_val: float, max_val: float) -> float:
    """Score how well a value fits inside a [min, max] range (0-1)."""
    if min_val <= value <= max_val:
        return 1.0
    if value < min_val:
        return max(0.0, 1.0 - abs(min_val - value) / max(min_val, 0.05))
    return max(0.0, 1.0 - abs(value - max_val) / max(1.0 - max_val, 0.05))


def _score_style_features(
    style: Dict[str, Any],
    color_features,
    composition_features,
    lighting_features,
) -> tuple[Dict[str, float], float]:
    """Return per-feature scores and the mean feature-match score for a style."""
    characteristics = style.get("characteristics", {})
    if not characteristics:
        return {}, 0.0

    scores = {}
    for name, bounds in characteristics.items():
        if name not in _FEATURE_MAP:
            continue
        value = _get_feature_value(name, color_features, composition_features, lighting_features)
        scores[name] = round(_score_characteristic(value, bounds["min"], bounds["max"]), 3)

    mean_score = sum(scores.values()) / len(scores) if scores else 0.0
    return scores, round(mean_score, 3)


def _score_palette(style: Dict[str, Any], color_features) -> float:
    """Return a 0-1 score for palette bias overlap between image and style."""
    style_palette = set(p.lower().replace(" ", "_") for p in style.get("palette_bias", []))
    image_palette = set(p.lower().replace(" ", "_") for p in color_features.get("palette_bias", []))
    if not style_palette or not image_palette:
        return 0.0
    intersection = style_palette & image_palette
    union = style_palette | image_palette
    return round(len(intersection) / len(union), 3)


def _generate_breakdown(style, color_features, composition_features, lighting_features):
    sections = []

    # Color profile section with matched/deviations/details.
    color_scores, _ = _score_style_features(style, color_features, composition_features, lighting_features)
    color_matched = []
    color_deviations = []
    color_details = [
        f"Dominant color: {color_features['dominant_color']['name']} ({color_features['dominant_color']['hex']})",
        f"Color temperature: {color_features['temperature']}",
        f"Saturation level: {color_features['saturation']:.2f} ({_saturation_label(color_features['saturation'])})",
        f"Color diversity: {color_features['color_diversity']:.2f} ({_diversity_label(color_features['color_diversity'])})",
        f"Palette: {', '.join(color_features['palette_bias'][:5])}",
    ]
    for name, score in color_scores.items():
        label = name.replace("_", " ").title()
        value = _get_feature_value(name, color_features, composition_features, lighting_features)
        bounds = style.get("characteristics", {}).get(name, {})
        if score >= 1.0:
            color_matched.append(f"{label} ({value:.2f}) falls within the expected range [{bounds.get('min', 0)}-{bounds.get('max', 0)}]")
        else:
            color_deviations.append(f"{label} ({value:.2f}) is outside the expected range [{bounds.get('min', 0)}-{bounds.get('max', 0)}]")

    sections.append({
        "title": "Color Profile",
        "matched": color_matched,
        "deviations": color_deviations,
        "details": color_details,
    })

    # Technique indicators section.
    technique_matched = []
    technique_deviations = []
    technique_details = [
        f"Brushwork texture: {composition_features['texture_variance']:.2f} ({_texture_label(composition_features['texture_variance'])})",
        f"Edge density: {composition_features['edge_density']:.2f} ({_edge_label(composition_features['edge_density'])})",
        f"Composition: {composition_features['composition_type']}",
        f"Lighting: {lighting_features['key_type']} ({lighting_features['light_direction']})",
        f"Contrast: {lighting_features['contrast']:.2f}",
    ]

    comp_names = ["edge_density", "texture_variance"]
    for name in comp_names:
        if name not in color_scores:
            continue
        score = color_scores[name]
        label = name.replace("_", " ").title()
        value = _get_feature_value(name, color_features, composition_features, lighting_features)
        bounds = style.get("characteristics", {}).get(name, {})
        if score >= 1.0:
            technique_matched.append(f"{label} ({value:.2f}) falls within the expected range [{bounds.get('min', 0)}-{bounds.get('max', 0)}]")
        else:
            technique_deviations.append(f"{label} ({value:.2f}) is outside the expected range [{bounds.get('min', 0)}-{bounds.get('max', 0)}]")

    sections.append({
        "title": "Technique Indicators",
        "matched": technique_matched,
        "deviations": technique_deviations,
        "details": technique_details,
    })

    sections.append({
        "title": "Style Transfer Prompt",
        "copyable": True,
        "details": [
            style.get("style_transfer_prompt", "No prompt available for this style."),
        ],
    })

    return sections


def _texture_label(val):
    if val < 0.2: return "very smooth/flat"
    if val < 0.4: return "mostly smooth"
    if val < 0.6: return "moderate texture"
    if val < 0.8: return "textured"
    return "heavily textured"


def _edge_label(val):
    if val < 0.05: return "very few edges"
    if val < 0.15: return "soft edges"
    if val < 0.3: return "moderate definition"
    if val < 0.5: return "sharp edges"
    return "very sharp/complex edges"


class StyleMatcher:
    """Encapsulates CLIP-based style matching with structured feature scoring.

    This class replaces the module-level global state that previously held the
    CLIP model, processor, device, and style embeddings.
    """

    def __init__(self, clip_wrapper: Optional[CLIPWrapper] = None, data_path: Optional[str] = None):
        self.clip_wrapper = clip_wrapper or get_clip_wrapper()
        self.data_path = data_path
        self._styles: Optional[List[Dict[str, Any]]] = None
        self._style_names: Optional[List[str]] = None
        self._style_embeddings: Optional[np.ndarray] = None

    def _load_styles(self):
        if self._styles is None:
            data = load_styles(self.data_path)
            self._styles = data["styles"]
            self._style_names = [s["name"] for s in self._styles]

    def _build_embeddings(self):
        self._load_styles()
        if self._style_embeddings is None:
            prompts = [_build_style_prompt(s) for s in self._styles]
            self._style_embeddings = self.clip_wrapper.embed_text(prompts)

    def match(
        self,
        color_features,
        composition_features,
        lighting_features,
        top_n: int = 3,
        image_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self._load_styles()
        styles = self._styles

        if image_path is None:
            return self._fallback_match(
                styles, color_features, composition_features, lighting_features, top_n
            )

        self._build_embeddings()
        embeddings = self._style_embeddings

        image_emb = self.clip_wrapper.embed_image(image_path)
        similarities = cosine_similarity(image_emb, embeddings)[0]

        min_s = float(np.min(similarities))
        max_s = float(np.max(similarities))
        span = max_s - min_s
        if span < 0.001:
            span = 0.001

        # Build candidate results with both CLIP and structured feature scores.
        candidates = []
        for idx, sim in enumerate(similarities):
            style = styles[idx]
            feature_scores, feature_match = _score_style_features(
                style, color_features, composition_features, lighting_features
            )
            palette_match = _score_palette(style, color_features)

            # Normalize CLIP similarity to [0, 1] using the observed span.
            normalized_clip = (float(sim) - min_s) / span

            # Blend CLIP similarity with structured feature match.
            blended = _CLIP_WEIGHT * normalized_clip + _FEATURE_WEIGHT * feature_match

            # Confidence is a friendly percentage anchored in the blended score.
            confidence = round(15.0 + blended * 80.0, 1)

            candidates.append({
                "style": style,
                "clip_score": round(float(sim), 3),
                "score": round(blended, 3),
                "confidence": min(99.0, confidence),
                "feature_scores": feature_scores,
                "feature_match": feature_match,
                "palette_match": palette_match,
                "_idx": idx,
            })

        # Sort by the blended score and keep the top_n.
        candidates.sort(key=lambda x: x["score"], reverse=True)
        results = candidates[:top_n]

        # Remove internal sorting key and add rank/breakdown.
        for i, r in enumerate(results):
            r.pop("_idx", None)
            r["rank"] = i + 1
            r["analysis_breakdown"] = _generate_breakdown(
                r["style"], color_features, composition_features, lighting_features
            )

        return results

    def _fallback_match(self, styles, color_features, composition_features, lighting_features, top_n):
        results = []
        for style in styles[:top_n]:
            feature_scores, feature_match = _score_style_features(
                style, color_features, composition_features, lighting_features
            )
            palette_match = _score_palette(style, color_features)
            results.append({
                "style": style,
                "clip_score": 0.0,
                "score": round(feature_match, 3),
                "confidence": round(15.0 + feature_match * 80.0, 1),
                "feature_scores": feature_scores,
                "feature_match": feature_match,
                "palette_match": palette_match,
            })
        for i, r in enumerate(results):
            r["rank"] = i + 1
            r["analysis_breakdown"] = _generate_breakdown(
                r["style"], color_features, composition_features, lighting_features
            )
        return results


# Shared application-level matcher. Lazily created so importing this module does
# not trigger CLIP model loading.
_default_matcher: Optional[StyleMatcher] = None


def get_default_matcher(clip_wrapper: Optional[CLIPWrapper] = None, data_path: Optional[str] = None) -> StyleMatcher:
    """Return the shared :class:`StyleMatcher` instance."""
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = StyleMatcher(clip_wrapper=clip_wrapper, data_path=data_path)
    return _default_matcher


def reset_default_matcher():
    """Reset the shared matcher. Useful in tests."""
    global _default_matcher
    _default_matcher = None


def match_style(
    color_features,
    composition_features,
    lighting_features,
    top_n=3,
    data_path=None,
    image_path=None,
    clip_wrapper=None,
):
    """Public API for matching an image/features against the style database."""
    matcher = get_default_matcher(clip_wrapper=clip_wrapper, data_path=data_path)
    return matcher.match(
        color_features,
        composition_features,
        lighting_features,
        top_n=top_n,
        image_path=image_path,
    )
