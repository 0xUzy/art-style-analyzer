import numpy as np
from PIL import Image
import cv2


def analyze_lighting(image_path):
    img = Image.open(image_path).convert("L")
    img_np = np.array(img).astype(np.float32) / 255.0
    h, w = img_np.shape

    mean_brightness = float(np.mean(img_np))
    median_brightness = float(np.median(img_np))
    brightness_std = float(np.std(img_np))

    contrast = float(brightness_std)

    data_flat = img_np.ravel()
    n = len(data_flat)
    mean_val = np.mean(data_flat)
    std_val = np.std(data_flat)
    if std_val > 1e-8:
        brightness_skewness = float(np.sum(((data_flat - mean_val) / std_val) ** 3) / n)
    else:
        brightness_skewness = 0.0

    low_key_ratio = float(np.mean(img_np < 0.3))
    mid_key_ratio = float(np.mean((img_np >= 0.3) & (img_np <= 0.7)))
    high_key_ratio = float(np.mean(img_np > 0.7))

    if high_key_ratio > 0.5:
        key_type = "high-key"
        key_confidence = high_key_ratio
    elif low_key_ratio > 0.5:
        key_type = "low-key"
        key_confidence = low_key_ratio
    elif low_key_ratio > 0.3 and contrast > 0.25:
        key_type = "chiaroscuro"
        key_confidence = min(low_key_ratio + contrast, 1.0)
    else:
        key_type = "mid-key"
        key_confidence = mid_key_ratio

    histogram, _ = np.histogram(img_np.ravel(), bins=256, range=(0, 1))
    histogram = histogram / histogram.sum()
    entropy = float(-np.sum(histogram[histogram > 0] * np.log2(histogram[histogram > 0])))
    tonal_range = entropy / 8.0

    tonal_bins = 10
    tonal_hist, _ = np.histogram(img_np.ravel(), bins=tonal_bins, range=(0, 1))
    tonal_hist = tonal_hist.astype(float) / tonal_hist.sum()

    shadow_detail = float(np.mean(img_np[(img_np > 0.05) & (img_np < 0.25)]) if np.any((img_np > 0.05) & (img_np < 0.25)) else 0)
    highlight_detail = float(np.mean(img_np[(img_np > 0.75) & (img_np < 0.95)]) if np.any((img_np > 0.75) & (img_np < 0.95)) else 0)

    blurred = cv2.GaussianBlur((img_np * 255).astype(np.uint8), (21, 21), 0)
    local_contrast = np.abs(img_np - blurred.astype(np.float32) / 255.0)
    dramatic_lighting = float(np.mean(local_contrast))

    micro_blurred = cv2.GaussianBlur((img_np * 255).astype(np.uint8), (3, 3), 0)
    micro_contrast = float(np.mean(np.abs(img_np - micro_blurred.astype(np.float32) / 255.0)))

    quadrant_brightness = []
    for i in range(2):
        for j in range(2):
            q = img_np[i * h // 2:(i + 1) * h // 2, j * w // 2:(j + 1) * w // 2]
            quadrant_brightness.append(float(np.mean(q)))

    light_direction_score = max(quadrant_brightness) - min(quadrant_brightness)
    if light_direction_score < 0.05:
        light_direction = "even/diffused"
    else:
        brightest_q = quadrant_brightness.index(max(quadrant_brightness))
        directions = ["top-left", "top-right", "bottom-left", "bottom-right"]
        light_direction = f"from {directions[brightest_q]}"

    highlights = float(np.mean(img_np > 0.85))
    shadows = float(np.mean(img_np < 0.15))
    midtones = float(np.mean((img_np >= 0.35) & (img_np <= 0.65)))

    rim_light = highlights > 0.05 and shadows > 0.15 and contrast > 0.2

    lighting_feature_vector = [
        mean_brightness,
        median_brightness,
        brightness_std,
        contrast,
        brightness_skewness,
        key_confidence,
        low_key_ratio,
        high_key_ratio,
        mid_key_ratio,
        tonal_range,
        shadow_detail,
        highlight_detail,
        dramatic_lighting,
        micro_contrast,
        light_direction_score,
        highlights,
        shadows,
        midtones,
    ]
    lighting_feature_vector.extend(tonal_hist.tolist())

    return {
        "mean_brightness": round(mean_brightness, 3),
        "median_brightness": round(median_brightness, 3),
        "brightness_std": round(brightness_std, 3),
        "contrast": round(contrast, 3),
        "brightness_skewness": round(brightness_skewness, 3),
        "key_type": key_type,
        "key_confidence": round(key_confidence, 3),
        "low_key_ratio": round(low_key_ratio, 3),
        "high_key_ratio": round(high_key_ratio, 3),
        "mid_key_ratio": round(mid_key_ratio, 3),
        "tonal_range": round(tonal_range, 3),
        "shadow_detail": round(shadow_detail, 3),
        "highlight_detail": round(highlight_detail, 3),
        "dramatic_lighting": round(dramatic_lighting, 3),
        "micro_contrast": round(micro_contrast, 3),
        "light_direction": light_direction,
        "light_direction_score": round(light_direction_score, 3),
        "highlights_pct": round(highlights, 3),
        "shadows_pct": round(shadows, 3),
        "midtones_pct": round(midtones, 3),
        "rim_lighting": rim_light,
        "feature_vector": [round(x, 6) for x in lighting_feature_vector],
    }
