# AGENTS/README_GUIDE.md - Project Agents Guide

This document serves as a blueprint for future development or agent interaction guidelines within the Art Style Analyzer project. It defines core operational concepts and suggests specific task prompts tailored to the codebase architecture.

## 🛠️ Agent Roles & Prompts

### 1. `CodeReviewer` (Effort: Medium/High)
**Goal:** To perform bug-hunting, correctness, or efficiency reviews on a given file diff (`file_path:line_number`).
**Prompt Example:** "As a senior PyTorch ML engineer, audit the provided code block in `analyzer/color_analysis.py`. Specifically check for race conditions when calculating histograms and suggest improvements to the color harmony calculation function."
**Focus Area:** Correctness of CV metrics; efficiency of NumPy/SciPy operations.

### 2. `FeatureExtractor` (Effort: Low)
**Goal:** To write unit tests or implement new, isolated feature extraction modules.
**Prompt Example:** "Implement a standalone class method in `analyzer/composition.py` that calculates the fractal dimension of an image's edge map given raw CV features."
**Focus Area:** Mathematical correctness; functional isolation (testing against fixed inputs).

### 3. `StyleMatcherRefiner` (Effort: High)
**Goal:** To improve or augment the core style matching logic within `style_matcher.py`. This is where ML model integration happens.
**Prompt Example:** "We need to modify the CLIP embedding generation process in `style_matcher.py`. The current method relies on simple prompt concatenation. Propose and implement a system that incorporates *structural* metadata (e.g., 'High Contrast, Golden Ratio composition') into the prompt template to improve matching specificity."
**Focus Area:** Model input engineering; vector comparison logic.

### 4. `SetupAssistant` (Effort: Low)
**Goal:** To provide foolproof instructions for setting up or running the project locally.
**Prompt Example:** "Write a comprehensive, step-by-step guide suitable for a new developer that explains all prerequisites, environment variables, and execution commands required to run this entire application."
**Focus Area:** Documentation clarity; dependency management (Virtual environments, CUDA compatibility).

## 🔄 Common Architectural Patterns to Follow

*   **Data Flow (Linear):** All feature extraction modules (`color_analysis`, `composition`, `lighting`) should operate on the **raw Pillow/OpenCV Image object** and return standardized, normalized dictionaries or NumPy arrays. Never pass through intermediate results without defining clear inputs and outputs.
*   **ML Inference:** All calls to the Hugging Face Transformers library must be wrapped in a dedicated utility class (`utils/clip_wrapper.py`) to handle model loading, caching, and device placement (CPU/CUDA) uniformly.
## Second brain

- The project's second brain is the **"Uzy's Workspace"** Obsidian vault, reachable at `brain/` (a symlink to `/Users/apple/Documents/Obsidian Vaults/Uzy's Workspace`). It is gitignored — never commit anything under it.
- **Before starting any task, read `brain/00-INDEX.md` and `brain/Projects/art-style-analyzer/art-style-analyzer.md` for full context on this project and how I work.**
