import os
import tempfile
import numpy as np
from PIL import Image
import pytest


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="session")
def test_image_rgb():
    """A 200x200 RGB test image with a known pattern (gradient + solid blocks)."""
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    # Red gradient in top-left quadrant
    arr[:100, :100, 0] = np.linspace(0, 255, 100, dtype=np.uint8)[:, None]
    # Green block in top-right
    arr[:100, 100:, 1] = 200
    # Blue block in bottom-left
    arr[100:, :100, 2] = 255
    # White-to-black gradient bottom-right
    g = np.linspace(0, 255, 100, dtype=np.uint8)
    arr[100:, 100:] = g[:, None]
    img = Image.fromarray(arr, "RGB")
    return img


@pytest.fixture(scope="session")
def test_image_path(test_image_rgb):
    """Write the test image to a temporary file and yield the path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        test_image_rgb.save(f, format="PNG")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def test_image_grayscale():
    """A 100x100 grayscale image with known brightness zones."""
    arr = np.zeros((100, 100), dtype=np.uint8)
    arr[:50, :50] = 30    # dark quadrant
    arr[:50, 50:] = 200   # bright quadrant
    arr[50:, :50] = 100   # mid quadrant
    arr[50:, 50:] = 220   # very bright quadrant
    return Image.fromarray(arr, "L")


@pytest.fixture(scope="session")
def test_image_grayscale_path(test_image_grayscale):
    """Write grayscale image to temp file."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        test_image_grayscale.save(f, format="PNG")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture(scope="session")
def solid_color_image():
    """A simple 50x50 solid red image."""
    arr = np.full((50, 50, 3), [200, 40, 40], dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


@pytest.fixture(scope="session")
def solid_color_path(solid_color_image):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        solid_color_image.save(f, format="PNG")
        path = f.name
    yield path
    os.unlink(path)
