import numpy as np
from PIL import Image
from colorthief import ColorThief
from collections import Counter


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    v = mx
    s = 0 if mx == 0 else df / mx
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    else:
        h = (60 * ((r - g) / df) + 240) % 360
    return h / 360.0, s, v


def classify_color_name(r, g, b):
    h, s, v = rgb_to_hsv(r, g, b)
    if s < 0.15:
        if v < 0.2:
            return "black"
        elif v < 0.5:
            return "gray"
        elif v < 0.8:
            return "light_gray"
        else:
            return "white"

    if v < 0.25:
        return "dark"

    if h < 0.05 or h >= 0.95:
        if s > 0.7 and v > 0.7:
            return "bright_red"
        elif v < 0.5:
            return "dark_red"
        return "red"
    elif h < 0.1:
        if v > 0.8:
            return "orange"
        return "dark_orange"
    elif h < 0.17:
        return "yellow" if v > 0.7 else "dark_yellow"
    elif h < 0.25:
        return "yellow_green" if s > 0.5 else "olive"
    elif h < 0.45:
        if s > 0.7 and v > 0.7:
            return "bright_green"
        elif v < 0.4:
            return "dark_green"
        return "green"
    elif h < 0.55:
        if s > 0.6:
            return "teal"
        return "cyan"
    elif h < 0.65:
        if v > 0.8:
            return "light_blue"
        elif v < 0.4:
            return "dark_blue"
        return "blue"
    elif h < 0.75:
        return "purple" if v > 0.5 else "dark_purple"
    elif h < 0.85:
        return "magenta" if s > 0.6 else "mauve"
    else:
        if v > 0.8 and s > 0.5:
            return "pink"
        return "lavender"


def get_palette_bias(colors):
    bias = Counter()
    for r, g, b in colors:
        name = classify_color_name(r, g, b)
        bias[name] += 1
    return [name for name, _ in bias.most_common(5)]


def _extract_color_histogram_features(h, s, v, num_hue_bins=12, num_sat_bins=4, num_val_bins=4):
    h_bins = np.digitize(h, np.linspace(0, 1, num_hue_bins + 1)) - 1
    h_bins = np.clip(h_bins, 0, num_hue_bins - 1)
    s_bins = np.digitize(s, np.linspace(0, 1, num_sat_bins + 1)) - 1
    s_bins = np.clip(s_bins, 0, num_sat_bins - 1)
    v_bins = np.digitize(v, np.linspace(0, 1, num_val_bins + 1)) - 1
    v_bins = np.clip(v_bins, 0, num_val_bins - 1)

    hist_2d_sv = np.zeros((num_sat_bins, num_val_bins))
    for si in range(num_sat_bins):
        for vi in range(num_val_bins):
            hist_2d_sv[si, vi] = np.sum((s_bins == si) & (v_bins == vi))
    hist_2d_sv = hist_2d_sv / hist_2d_sv.sum() if hist_2d_sv.sum() > 0 else hist_2d_sv

    hist_h, _ = np.histogram(h, bins=num_hue_bins, range=(0, 1))
    hist_h = hist_h / hist_h.sum() if hist_h.sum() > 0 else hist_h

    hist_v, _ = np.histogram(v, bins=num_val_bins, range=(0, 1))
    hist_v = hist_v / hist_v.sum() if hist_v.sum() > 0 else hist_v

    features = []
    features.extend(hist_h.tolist())
    features.extend(hist_v.tolist())
    features.extend(hist_2d_sv.flatten().tolist())

    return features


def _compute_color_harmony(h, s, v):
    dominant_hue_bin = np.argmax(np.bincount(
        np.clip((h * 12).astype(int), 0, 11), minlength=12
    ))
    dominant_hue = dominant_hue_bin / 12.0

    complementary_diff = min(abs(h - ((dominant_hue + 0.5) % 1.0)), key=lambda x: x) if len(h) > 0 else 0
    complementary_score = float(np.mean(np.abs(h - ((dominant_hue + 0.5) % 1.0)) < 0.08))

    triadic_score = float(np.mean(
        (np.abs(h - ((dominant_hue + 1/3) % 1.0)) < 0.08) |
        (np.abs(h - ((dominant_hue + 2/3) % 1.0)) < 0.08)
    ))

    analogous_score = float(np.mean(
        (np.abs(h - ((dominant_hue + 1/12) % 1.0)) < 0.06) |
        (np.abs(h - ((dominant_hue - 1/12) % 1.0)) < 0.06)
    ))

    monochromatic_score = float(np.mean(np.abs(h - dominant_hue) < 0.04))

    return {
        "complementary": round(complementary_score, 4),
        "triadic": round(triadic_score, 4),
        "analogous": round(analogous_score, 4),
        "monochromatic": round(monochromatic_score, 4),
    }


def analyze_colors(image_path):
    img = Image.open(image_path).convert("RGB")
    img_small = img.resize((200, 200))
    pixels = np.array(img_small).reshape(-1, 3).astype(float) / 255.0

    ct = ColorThief(image_path)
    try:
        dominant = ct.get_color(quality=1)
    except Exception:
        dominant = tuple(img_small.resize((1, 1)).getpixel((0, 0)))

    try:
        palette = ct.get_palette(color_count=8, quality=1)
    except Exception:
        palette = [dominant]

    r, g, b = pixels[:, 0], pixels[:, 1], pixels[:, 2]
    h, s, v = np.vectorize(rgb_to_hsv)(r, g, b)

    saturation = float(np.mean(s))
    saturation_std = float(np.std(s))
    brightness = float(np.mean(v))
    brightness_std = float(np.std(v))

    warm_hues = ((h < 0.12) | (h > 0.88) | ((h > 0.0) & (h < 0.18)))
    warmth = float(np.mean(warm_hues))

    unique_colors = len(set(map(tuple, (pixels * 255).astype(int).tolist())))
    total_pixels = len(pixels)
    color_diversity = min(1.0, unique_colors / (total_pixels * 0.1))

    h_shifted = np.where(h < 0.5, h + 0.5, h - 0.5)
    hue_std = float(np.std(h_shifted))
    color_uniformity = 1.0 - min(1.0, hue_std / 0.25)

    color_hist_features = _extract_color_histogram_features(h, s, v)
    color_harmony = _compute_color_harmony(h, s, v)

    r_var = float(np.var(r))
    g_var = float(np.var(g))
    b_var = float(np.var(b))
    rgb_correlation = float(np.corrcoef(np.stack([r, g, b]))[0, 1]) if len(r) > 1 else 0

    color_feature_vector = [
        saturation,
        saturation_std,
        brightness,
        brightness_std,
        warmth,
        color_diversity,
        color_uniformity,
        hue_std,
        r_var,
        g_var,
        b_var,
        color_harmony["complementary"],
        color_harmony["triadic"],
        color_harmony["analogous"],
        color_harmony["monochromatic"],
    ]
    color_feature_vector.extend(color_hist_features)

    color_names = [classify_color_name(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)) for c in palette]
    named_palette = []
    for i, (r_val, g_val, b_val) in enumerate(palette):
        named_palette.append({
            "rgb": [int(r_val), int(g_val), int(b_val)],
            "hex": f"#{int(r_val):02x}{int(g_val):02x}{int(b_val):02x}",
            "name": color_names[i] if i < len(color_names) else "unknown"
        })

    warm_count = int(np.sum(warm_hues))
    cool_count = total_pixels - warm_count
    temperature = "warm" if warm_count > cool_count * 1.2 else ("cool" if cool_count > warm_count * 1.2 else "neutral")

    return {
        "dominant_color": {
            "rgb": list(dominant),
            "hex": f"#{int(dominant[0]):02x}{int(dominant[1]):02x}{int(dominant[2]):02x}",
            "name": classify_color_name(*dominant)
        },
        "palette": named_palette,
        "palette_bias": get_palette_bias(palette),
        "saturation": round(saturation, 3),
        "saturation_std": round(saturation_std, 3),
        "brightness": round(brightness, 3),
        "brightness_std": round(brightness_std, 3),
        "warmth": round(warmth, 3),
        "temperature": temperature,
        "color_diversity": round(color_diversity, 3),
        "color_uniformity": round(color_uniformity, 3),
        "color_harmony": color_harmony,
        "feature_vector": [round(x, 6) for x in color_feature_vector],
    }
