# Art Style Analyzer

Analyze any image to identify its art style using OpenAI's CLIP model. Upload an image and instantly match it against 35 art styles — from Anime and Cyberpunk to Gouache and Origami. Each result includes a copy-paste style transfer prompt for AI image generators.

🎨 **Fully local** — no API key, no data leaves your machine.

## Features

- **35 art styles** — Ghibli, Stylized 3D, Cel-Shaded 3D, Pixel Art, Chibi, Manga, Glitch Art, Voxel Art, and more
- **CLIP-powered matching** — locally, no API key, no internet after first download
- **Structured feature scoring** — color, composition, and lighting features are matched against each style's characteristic ranges
- **Style transfer prompts** — copy-paste ready prompts for Midjourney, DALL·E, Stable Diffusion
- **Color palette extraction** — dominant colors with hex codes
- **Lighting & composition analysis** — key type, contrast, texture, symmetry
- **Export to JSON** — download full analysis for each match
- **100% local** — runs entirely on your machine, no data leaves your computer

## Quick Start

Choose your platform:

### macOS — Double-click

1. **Install Python 3** (if you haven't already) — run this in Terminal once:
   ```bash
   xcode-select --install
   ```

2. Double-click **`run.command`** in Finder.
   > First time: Terminal opens, creates a virtual environment, installs dependencies, and downloads the CLIP model (~600MB). Takes 1-2 minutes.
   > After that: starts instantly.

3. Your browser opens to **http://localhost:5001** — upload an image and click **Analyze Art Style**.

### Windows — Double-click

1. **Install Python 3.9+** from [python.org](https://python.org). Make sure to check **"Add Python to PATH"** during installation.

2. Double-click **`run.bat`** in File Explorer.
   > First time: Command Prompt opens, creates a virtual environment, installs dependencies, and downloads the CLIP model (~600MB). Takes 1-2 minutes.
   > After that: starts instantly.

3. Your browser opens to **http://localhost:5001** — upload an image and click **Analyze Art Style**.

### Terminal (any OS)

```bash
git clone https://github.com/0xUzy/art-style-analyzer.git
cd art-style-analyzer
python3 -m venv venv
source venv/bin/activate    # macOS/Linux
# venv\Scripts\activate     # Windows
pip install -r requirements.txt
python3 app.py              # or python app.py on Windows
```

Open **http://localhost:5001** in your browser.

> **First run downloads CLIP** (~600MB, one-time ~10s). Subsequent runs start instantly.

## Requirements

- Python 3.9+
- ~3GB free disk space (for CLIP model and virtual environment)

## How It Works

1. **Upload** an image through the web UI.
2. **Feature extraction** runs three analyzers in parallel:
   - `color_analysis.py` — saturation, brightness, temperature, palette, color harmony
   - `composition.py` — edge density, texture, symmetry, focal strength
   - `lighting.py` — key type, contrast, tonal range, light direction
3. **CLIP embedding** compares the uploaded image against text embeddings of all 35 styles.
4. **Blended scoring** combines CLIP similarity with structured feature matching using the `characteristics` ranges in `data/styles.json`.
5. **Results** show the top styles, confidence scores, feature breakdowns, and a copyable style-transfer prompt.

## Project Structure

```
art-style-analyzer/
├── run.command              # 🚀 Double-click to launch (macOS)
├── run.bat                  # 🚀 Double-click to launch (Windows)
├── app.py                   # Flask web server
├── analyzer/
│   ├── color_analysis.py    # Color palette & histogram extraction
│   ├── composition.py       # Edge, texture, symmetry analysis
│   ├── lighting.py          # Lighting, contrast, tonal analysis
│   └── style_matcher.py     # Style matching logic
├── data/
│   └── styles.json          # 35 style definitions with transfer prompts
├── utils/
│   └── clip_wrapper.py      # Shared CLIP model loader & embeddings
├── static/
│   ├── css/style.css        # Glass-morphism dark UI
│   ├── js/main.js           # Drag-drop, results rendering, clipboard
│   └── uploads/             # Temporary uploaded images
├── templates/
│   └── index.html           # Single-page app template
├── tests/                   # Test suite (pytest)
├── requirements.txt
├── README.md
├── AGENTS.md
└── .gitignore
```

## Development

### Running tests

```bash
python -m pytest tests/
```

CLIP model loading is lazy: importing `app.py` or the analyzer modules does **not** download or load the model. Only the `/analyze` endpoint triggers CLIP when it receives a real image.

### Architecture

- **Linear data flow** — all feature extractors accept a Pillow `Image` object and return standardized dictionaries. `app.py` opens the image once and passes it to each analyzer.
- **Shared CLIP wrapper** — `utils/clip_wrapper.py` is the single module that talks to Hugging Face Transformers, handling model loading, device placement (MPS/CUDA/CPU), and embedding generation.
- **Injectable matcher** — `analyzer/style_matcher.StyleMatcher` encapsulates style embeddings and matching logic, making it easy to test with a mocked CLIP wrapper.

## Art Styles

| Digital | Traditional | Stylized |
|---------|-------------|----------|
| Photorealistic | Photography / Natural Photo | Stylized 3D |
| Anime | Watercolor | Cel-Shaded 3D |
| Comic Book | Pencil Sketch / Graphite | Claymation / Stop-Motion |
| Cartoon / Cel-Shaded | Gouache Painting | Origami |
| Semi-Realistic | Pastel / Chalk Art | Low Poly |
| Pixel Art | Ink Wash / Sumi-e | Voxel Art |
| 3D Render / CGI | Line Art / Clean Line | Isometric Illustration |
| Flat Design / Vector | Manga | Duotone |
| Cyberpunk | Children's Book Illustration | Glitch Art |
| Synthwave / Retrowave | Steampunk | Chibi |
| Fantasy Illustration | | Ghibli Style |
| Concept Art | | Matte Painting |
| Editorial Illustration (2D) | | |

## License

MIT
