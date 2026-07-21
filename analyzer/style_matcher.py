import json
import os
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

_model = None
_processor = None
_device = None
_style_embeddings = None
_style_names = None


def _get_device():
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    elif torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_clip():
    global _model, _processor, _device, _style_embeddings, _style_names
    if _model is not None:
        return

    from transformers import CLIPProcessor, CLIPModel
    import torch

    _device = _get_device()
    _model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    _processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    _model.to(_device)
    _model.eval()

    data = load_styles()
    styles = data["styles"]
    _style_names = [s["name"] for s in styles]
    prompts = [_build_style_prompt(s) for s in styles]

    _style_embeddings = []
    batch_size = 8
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i + batch_size]
        inputs = _processor(text=batch, return_tensors="pt", padding=True, truncation=True, max_length=77)
        inputs = {k: v.to(_device) for k, v in inputs.items()}
        with torch.no_grad():
            emb = _model.get_text_features(**inputs)
            if hasattr(emb, "pooler_output"):
                emb = emb.pooler_output
            emb = emb / emb.norm(dim=-1, keepdim=True)
        _style_embeddings.append(emb.cpu().numpy())
    _style_embeddings = np.concatenate(_style_embeddings, axis=0)


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


def match_style(color_features, composition_features, lighting_features, top_n=3, data_path=None, image_path=None):
    import torch

    _load_clip()

    data = load_styles(data_path)
    styles = data["styles"]

    if image_path is None:
        return _fallback_match(styles, color_features, composition_features, lighting_features, top_n)

    image = Image.open(image_path).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    with torch.no_grad():
        image_emb = _model.get_image_features(**inputs)
        if hasattr(image_emb, "pooler_output"):
            image_emb = image_emb.pooler_output
        image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
    image_emb_np = image_emb.cpu().numpy()

    similarities = cosine_similarity(image_emb_np, _style_embeddings)[0]

    min_s = float(np.min(similarities))
    max_s = float(np.max(similarities))
    span = max_s - min_s
    if span < 0.001:
        span = 0.001

    ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)

    results = []
    for idx, sim in ranked[:top_n]:
        style = styles[idx]
        confidence = round(15.0 + (float(sim) - min_s) / span * 80.0, 1)

        results.append({
            "style": style,
            "score": round(float(sim), 3),
            "confidence": min(99.0, confidence),
            "feature_scores": {},
            "palette_match": 0,
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["analysis_breakdown"] = _generate_breakdown(
            r["style"], color_features, composition_features, lighting_features
        )

    return results


def _fallback_match(styles, color_features, composition_features, lighting_features, top_n):
    results = []
    for style in styles[:top_n]:
        results.append({
            "style": style,
            "score": 0.5,
            "feature_scores": {},
            "palette_match": 0,
        })
    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["confidence"] = 50.0
        r["analysis_breakdown"] = _generate_breakdown(
            r["style"], color_features, composition_features, lighting_features
        )
    return results


def _generate_breakdown(style, color_features, composition_features, lighting_features):
    sections = []

    sections.append({
        "title": "Color Profile",
        "details": [
            f"Dominant color: {color_features['dominant_color']['name']} ({color_features['dominant_color']['hex']})",
            f"Color temperature: {color_features['temperature']}",
            f"Saturation level: {color_features['saturation']:.2f} ({_saturation_label(color_features['saturation'])})",
            f"Color diversity: {color_features['color_diversity']:.2f} ({_diversity_label(color_features['color_diversity'])})",
            f"Palette: {', '.join(color_features['palette_bias'][:5])}",
        ],
    })

    sections.append({
        "title": "Technique Indicators",
        "details": [
            f"Brushwork texture: {composition_features['texture_variance']:.2f} ({_texture_label(composition_features['texture_variance'])})",
            f"Edge density: {composition_features['edge_density']:.2f} ({_edge_label(composition_features['edge_density'])})",
            f"Composition: {composition_features['composition_type']}",
            f"Lighting: {lighting_features['key_type']} ({lighting_features['light_direction']})",
            f"Contrast: {lighting_features['contrast']:.2f}",
        ],
    })

    sections.append({
        "title": "Style Transfer Prompt",
        "copyable": True,
        "details": [
            style.get("style_transfer_prompt", "No prompt available for this style."),
        ],
    })

    return sections


def _saturation_label(val):
    if val < 0.2: return "muted/desaturated"
    if val < 0.4: return "moderately muted"
    if val < 0.6: return "moderate saturation"
    if val < 0.8: return "saturated"
    return "highly saturated/vivid"


def _diversity_label(val):
    if val < 0.2: return "very limited palette"
    if val < 0.4: return "limited palette"
    if val < 0.6: return "moderate range"
    if val < 0.8: return "diverse palette"
    return "highly diverse"


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
