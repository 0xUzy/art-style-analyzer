# Art Style Analyzer

Analyze any image to identify its art style using OpenAI's CLIP model. Upload an image and instantly match it against 35 art styles — from Anime and Cyberpunk to Gouache and Origami. Each result includes a copy-paste style transfer prompt for AI image generators.

## Features

- **35 art styles** — Ghibli, Stylized 3D, Cel-Shaded 3D, Pixel Art, Chibi, Manga, Glitch Art, Voxel Art, and more
- **CLIP-powered matching** — locally, no API key, no internet after first download
- **Style transfer prompts** — copy-paste ready prompts for Midjourney, DALL·E, Stable Diffusion
- **Color palette extraction** — dominant colors with hex codes
- **Lighting & composition analysis** — key type, contrast, texture, symmetry
- **Export to JSON** — download full analysis for each match
- **100% local** — runs entirely on your machine, no data leaves your computer

## How It Works

OpenAI's CLIP model embeds both the uploaded image and text descriptions of each art style into a shared vector space. Cosine similarity finds the closest style matches. The model runs locally — downloaded once (~600MB) and cached thereafter.

## Quick Start

```bash
# Clone
git clone https://github.com/0xUzy/art-style-analyzer.git
cd art-style-analyzer

# Setup virtual environment
python -m venv venv

# Activate (macOS / Linux)
source venv/bin/activate
# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:5001** — upload an image and click "Analyze Art Style".

First run downloads CLIP (~600MB, one-time ~10s). Subsequent runs start instantly.

## Requirements

- Python 3.9+
- pip
- ~3GB free disk space (for CLIP model)

## Project Structure

```
art-style-analyzer/
├── app.py                  # Flask web server
├── analyzer/
│   ├── color_analysis.py   # Color palette & histogram extraction
│   ├── composition.py      # Edge, texture, symmetry analysis
│   ├── lighting.py         # Lighting, contrast, tonal analysis
│   └── style_matcher.py    # CLIP model loader & style matching
├── data/
│   └── styles.json         # 35 style definitions with transfer prompts
├── static/
│   ├── css/style.css       # Glass-morphism dark UI
│   ├── js/main.js          # Drag-drop, results rendering, clipboard
│   └── uploads/            # Temporary uploaded images
├── templates/
│   └── index.html          # Single-page app template
└── requirements.txt
```

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
