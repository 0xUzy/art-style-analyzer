import os
import uuid
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from analyzer.color_analysis import analyze_colors
from analyzer.composition import analyze_composition
from analyzer.lighting import analyze_lighting
from analyzer.style_matcher import match_style, _load_clip

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

print("Loading CLIP model (one-time, ~10s)...")
_load_clip()
print("CLIP model ready.")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Allowed: PNG, JPG, GIF, BMP, WebP"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        color_features = analyze_colors(filepath)
        composition_features = analyze_composition(filepath)
        lighting_features = analyze_lighting(filepath)

        styles = match_style(
            color_features, composition_features, lighting_features,
            top_n=2, image_path=filepath
        )

        return jsonify({
            "success": True,
            "image_url": f"/static/uploads/{filename}",
            "styles": styles,
            "features": {
                "colors": color_features,
                "composition": composition_features,
                "lighting": lighting_features,
            },
        })
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
