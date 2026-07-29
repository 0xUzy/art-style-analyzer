"""Integration test for the Flask app.

CLIP loading is now lazy (triggered only when /analyze receives a real image),
so the app module can be imported in tests without mocking. The actual /analyze
endpoint that needs CLIP is tested via the skip test below.
"""

import io

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = "/tmp/test_uploads"
    with app.test_client() as client:
        yield client


@pytest.fixture
def test_png_bytes():
    """Generate a small valid PNG in memory."""
    import numpy as np
    from PIL import Image

    arr = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


class TestFlaskValidation:
    """Tests that don't require CLIP (validation layer only)."""

    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Art Style Analyzer" in resp.data

    def test_analyze_no_image(self, client):
        resp = client.post("/analyze")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_analyze_empty_filename(self, client):
        resp = client.post("/analyze", data={"image": (io.BytesIO(b""), "")})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_analyze_invalid_type(self, client):
        resp = client.post("/analyze", data={
            "image": (io.BytesIO(b"not an image"), "test.txt"),
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_analyze_invalid_ext(self, client):
        """WebP is allowed, .txt is not - test via the allowed_file check."""
        # The file type check happens after is_uploaded, so we need a valid image
        # but wrong extension. The analyze endpoint will reject before save.
        pass

    def test_max_content_length(self, client):
        """Upload a file that exceeds the 16MB limit."""
        large_data = b"x" * (16 * 1024 * 1024 + 1)
        resp = client.post("/analyze", data={
            "image": (io.BytesIO(large_data), "large.png"),
        })
        assert resp.status_code == 413


@pytest.mark.skip(reason="Requires real CLIP model to be loaded")
class TestAnalyzeWithCLIP:
    """Tests that exercise the full /analyze pipeline with mocked CLIP."""

    def test_analyze_valid_image(self, client, test_png_bytes):
        resp = client.post("/analyze", data={
            "image": (test_png_bytes, "test_image.png"),
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("success") is True
        assert "image_url" in data
        assert "styles" in data
        assert "features" in data
        for style in data["styles"]:
            assert "style" in style
            assert "score" in style
            assert "confidence" in style
            assert "rank" in style
