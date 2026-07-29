import numpy as np
from PIL import Image
import cv2
from skimage.feature import local_binary_pattern, hog


def _load_image(image_or_path):
    """Return a PIL RGB image from a file path or an existing Image object."""
    if isinstance(image_or_path, Image.Image):
        return image_or_path.convert("RGB")
    return Image.open(image_or_path).convert("RGB")


def analyze_composition(image_or_path):
    img = _load_image(image_or_path)
    img_gray = img.convert("L")
    img_np = np.array(img_gray).astype(np.float32) / 255.0
    h, w = img_np.shape

    img_uint8 = (img_np * 255).astype(np.uint8)

    edges = cv2.Canny(img_uint8, 50, 150)
    edge_density = float(np.mean(edges > 0))

    blurred = cv2.GaussianBlur(img_uint8, (5, 5), 0)
    laplacian = cv2.Laplacian(blurred, cv2.CV_64F)
    texture_variance = float(np.var(laplacian))
    texture_normalized = min(1.0, texture_variance / 5000)

    sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(sobelx ** 2 + sobely ** 2)

    left_half = np.mean(gradient_mag[:, :w // 2])
    right_half = np.mean(gradient_mag[:, w // 2:])
    top_half = np.mean(gradient_mag[:h // 2, :])
    bottom_half = np.mean(gradient_mag[h // 2:, :])

    horizontal_balance = 1.0 - abs(left_half - right_half) / max(left_half + right_half, 1e-6)
    vertical_balance = 1.0 - abs(top_half - bottom_half) / max(top_half + bottom_half, 1e-6)
    symmetry = float((horizontal_balance + vertical_balance) / 2)

    third_h, third_w = h // 3, w // 3
    center_region = img_np[third_h:2 * third_h, third_w:2 * third_w]
    edge_center = np.mean(edges[third_h:2 * third_h, third_w:2 * third_w] > 0)
    edge_periphery = np.mean(edges) - edge_center * (1 / 9)
    focal_strength = min(1.0, max(0.0, (edge_center - edge_periphery) * 5)) if edge_periphery > 0 else 0.5

    quadrant_edges = []
    for i in range(2):
        for j in range(2):
            q = edges[i * h // 2:(i + 1) * h // 2, j * w // 2:(j + 1) * w // 2]
            quadrant_edges.append(float(np.mean(q > 0)))
    quadrant_std = float(np.std(quadrant_edges))
    visual_weight_distribution = min(1.0, quadrant_std * 10)

    diagonal_tl_br = np.mean(np.diag(edges[:min(h, w), :min(h, w)]))
    diagonal_tr_bl = np.mean(np.diag(np.fliplr(edges[:min(h, w), :min(h, w)])))
    diagonal_symmetry = 1.0 - abs(diagonal_tl_br - diagonal_tr_bl) / max(diagonal_tl_br + diagonal_tr_bl, 1e-6)

    complexity = float(np.mean(edges > 0))
    simplicity = 1.0 - complexity

    img_resized = img_gray.resize((128, 128))
    img_np_128 = np.array(img_resized).astype(np.float32) / 255.0
    img_uint8_128 = (img_np_128 * 255).astype(np.uint8)

    try:
        lbp = local_binary_pattern(img_uint8_128, P=8, R=1, method="uniform")
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10))
        lbp_hist = lbp_hist.astype(float) / lbp_hist.sum()
        lbp_features = lbp_hist.tolist()
    except Exception:
        lbp_features = [0.0] * 10

    try:
        hog_features = hog(
            img_np_128,
            orientations=8,
            pixels_per_cell=(32, 32),
            cells_per_block=(2, 2),
            visualize=False,
        )
        hog_mean = float(np.mean(hog_features))
        hog_std = float(np.std(hog_features))
        hog_max = float(np.max(hog_features))
        hog_energy = float(np.sum(hog_features ** 2)) / len(hog_features)
    except Exception:
        hog_mean, hog_std, hog_max, hog_energy = 0.0, 0.0, 0.0, 0.0

    try:
        fft = np.fft.fft2(img_np_128)
        fft_shift = np.fft.fftshift(fft)
        magnitude = np.abs(fft_shift)
        magnitude_flat = magnitude.ravel()
        magnitude_flat.sort()
        low_freq_energy = float(np.mean(magnitude_flat[-int(len(magnitude_flat) * 0.05):]))
        high_freq_energy = float(np.mean(magnitude_flat[:int(len(magnitude_flat) * 0.5)]))
        freq_ratio = min(10.0, max(0.5, low_freq_energy / max(high_freq_energy, 1e-6)))

        rings = []
        center = 64
        for radius in [8, 16, 32, 64]:
            y, x = np.ogrid[:128, :128]
            mask = (np.sqrt((x - center) ** 2 + (y - center) ** 2) <= radius) & \
                   (np.sqrt((x - center) ** 2 + (y - center) ** 2) > radius / 2)
            rings.append(float(np.mean(magnitude[mask])))
        ring_total = sum(rings) + 1e-6
        freq_profile = [r / ring_total for r in rings]
    except Exception:
        freq_ratio = 0.0
        freq_profile = [0.0] * 4

    edge_strength_mean = float(np.mean(gradient_mag))
    edge_strength_std = float(np.std(gradient_mag))

    composition_feature_vector = [
        edge_density,
        texture_normalized,
        symmetry,
        horizontal_balance,
        vertical_balance,
        diagonal_symmetry,
        focal_strength,
        visual_weight_distribution,
        complexity,
        simplicity,
        edge_strength_mean,
        edge_strength_std,
        hog_mean,
        hog_std,
        hog_energy,
        freq_ratio,
    ]
    composition_feature_vector.extend(lbp_features)
    composition_feature_vector.extend(freq_profile)

    return {
        "edge_density": round(edge_density, 3),
        "texture_variance": round(texture_normalized, 3),
        "symmetry": round(symmetry, 3),
        "horizontal_balance": round(horizontal_balance, 3),
        "vertical_balance": round(vertical_balance, 3),
        "diagonal_symmetry": round(diagonal_symmetry, 3),
        "focal_strength": round(focal_strength, 3),
        "visual_weight_distribution": round(visual_weight_distribution, 3),
        "complexity": round(complexity, 3),
        "simplicity": round(simplicity, 3),
        "composition_type": _classify_composition(symmetry, focal_strength, complexity),
        "feature_vector": [round(x, 6) for x in composition_feature_vector],
    }


def _classify_composition(symmetry, focal, complexity):
    if symmetry > 0.8:
        return "highly symmetrical"
    elif symmetry > 0.6:
        return "moderately symmetrical"
    elif focal > 0.6:
        return "centrally focused"
    elif complexity > 0.5:
        return "complex, all-over"
    elif complexity < 0.1:
        return "minimal, open"
    else:
        return "asymmetrical, balanced"
