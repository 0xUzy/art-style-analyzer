const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const previewContainer = document.getElementById("preview-container");
const previewImage = document.getElementById("preview-image");
const dropZoneContent = document.querySelector(".drop-zone-content");
const clearBtn = document.getElementById("clear-btn");
const analyzeBtn = document.getElementById("analyze-btn");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
const resultsReport = document.getElementById("results-report");
const resultImage = document.getElementById("result-image");
const uploadSection = document.getElementById("upload-section");

let selectedFile = null;

dropZone.addEventListener("click", (e) => {
    if (e.target === clearBtn || clearBtn.contains(e.target)) return;
    if (!selectedFile) fileInput.click();
});

fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});

clearBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUpload();
});

analyzeBtn.addEventListener("click", analyzeImage);

function handleFile(file) {
    if (!file.type.startsWith("image/")) return;
    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        dropZoneContent.classList.add("hidden");
        previewContainer.classList.remove("hidden");
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = "";
    previewContainer.classList.add("hidden");
    dropZoneContent.classList.remove("hidden");
    analyzeBtn.disabled = true;
}

async function analyzeImage() {
    if (!selectedFile) return;

    uploadSection.classList.add("hidden");
    results.classList.add("hidden");
    loading.classList.remove("hidden");

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
        const response = await fetch("/analyze", { method: "POST", body: formData });
        const data = await response.json();

        loading.classList.add("hidden");

        if (data.error) {
            alert(data.error);
            uploadSection.classList.remove("hidden");
            return;
        }

        renderResults(data);
        results.classList.remove("hidden");
    } catch (err) {
        loading.classList.add("hidden");
        alert("Analysis failed. Please try again.");
        uploadSection.classList.remove("hidden");
    }
}

function renderResults(data) {
    resultImage.src = data.image_url;
    resultsReport.innerHTML = "";

    const scrollWrapper = document.createElement("div");
    scrollWrapper.className = "results-scroll";

    data.styles.forEach((s, idx) => {
        const card = document.createElement("div");
        card.className = `style-card${idx === 0 ? " top-match" : ""}`;

        let html = `
            <div class="style-header">
                <span class="style-name">${s.style.name}</span>
                <span class="style-era">${s.style.era}</span>
                <span class="confidence-badge">${s.confidence}%</span>
                <button class="export-btn" data-style-idx="${idx}" title="Export this style as JSON">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export JSON
                </button>
            </div>
            <p class="description">${s.style.description}</p>
        `;

        if (s.analysis_breakdown) {
            s.analysis_breakdown.forEach((section) => {
                if (section.copyable) {
                    html += `<div class="analysis-section"><h4>${section.title}</h4>`;
                    html += `<div class="prompt-block">`;
                    html += `<p class="prompt-text">${section.details[0]}</p>`;
                    html += `<button class="copy-btn" data-prompt="${section.details[0].replace(/"/g, '&quot;')}">`;
                    html += `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
                    html += ` Copy Prompt`;
                    html += `</button></div></div>`;
                } else {
                    html += `<div class="analysis-section"><h4>${section.title}</h4><ul>`;
                    if (section.matched) {
                        section.matched.forEach((m) => {
                            html += `<li>${m}</li>`;
                        });
                    }
                    if (section.deviations) {
                        section.deviations.forEach((d) => {
                            html += `<li class="deviation">${d}</li>`;
                        });
                    }
                    if (section.details) {
                        section.details.forEach((d) => {
                            html += `<li>${d}</li>`;
                        });
                    }
                    html += `</ul></div>`;
                }
            });
        }

        html += `<div class="analysis-section"><h4>Techniques</h4><div class="tags">`;
        s.style.techniques.forEach((t) => {
            html += `<span class="tag">${t}</span>`;
        });
        html += `</div></div>`;

        html += `<div class="analysis-section"><h4>Mood</h4><div class="tags">`;
        s.style.mood.forEach((m) => {
            html += `<span class="tag">${m}</span>`;
        });
        html += `</div></div>`;

        html += `<div class="analysis-section"><h4>Color Palette</h4><div class="palette-strip">`;
        data.features.colors.palette.forEach((c) => {
            html += `<div class="palette-swatch" style="background:${c.hex}"><span class="tooltip">${c.name} (${c.hex})</span></div>`;
        });
        html += `</div></div>`;

        html += `<div class="key-info">
            <span class="key-badge"><strong>Lighting:</strong> ${data.features.lighting.key_type}</span>
            <span class="key-badge"><strong>Temperature:</strong> ${data.features.colors.temperature}</span>
            <span class="key-badge"><strong>Composition:</strong> ${data.features.composition.composition_type}</span>
        </div>`;

        html += `<div class="analysis-section" style="margin-top:0.8rem"><h4>Key Artists</h4><div class="tags">`;
        s.style.key_artists.forEach((a) => {
            html += `<span class="tag">${a}</span>`;
        });
        html += `</div></div>`;

        html += `<div class="analysis-section"><h4>Influences</h4><p class="description">${s.style.influences}</p></div>`;

        card.innerHTML = html;
        card.querySelectorAll(".copy-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.stopPropagation();
                const promptText = btn.getAttribute("data-prompt");
                navigator.clipboard.writeText(promptText).then(() => {
                    const origHTML = btn.innerHTML;
                    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
                    btn.classList.add("copied");
                    setTimeout(() => {
                        btn.innerHTML = origHTML;
                        btn.classList.remove("copied");
                    }, 2000);
                });
            });
        });
        card.querySelector(".export-btn").addEventListener("click", (e) => {
            e.stopPropagation();
            exportStyleJSON(data, idx);
        });
        scrollWrapper.appendChild(card);
    });

    resultsReport.appendChild(scrollWrapper);

    const backBtn = document.createElement("button");
    backBtn.className = "analyze-btn";
    backBtn.textContent = "Analyze Another Image";
    backBtn.style.marginTop = "1rem";
    backBtn.onclick = () => {
        results.classList.add("hidden");
        uploadSection.classList.remove("hidden");
        resetUpload();
    };
    resultsReport.appendChild(backBtn);
}

function buildStylePrompt(style, features) {
    const parts = [];
    parts.push(`Art style: ${style.name} (${style.era})`);

    const palette = features.colors.palette.map((c) => c.name).slice(0, 5).join(", ");
    parts.push(`Color palette: ${palette}`);
    parts.push(`Color temperature: ${features.colors.temperature}`);
    parts.push(`Saturation: ${features.colors.saturation > 0.6 ? "vivid" : features.colors.saturation > 0.35 ? "moderate" : "muted"}`);

    parts.push(`Lighting: ${features.lighting.key_type}, ${features.lighting.light_direction}`);
    parts.push(`Contrast: ${features.lighting.contrast > 0.5 ? "high" : features.lighting.contrast > 0.3 ? "medium" : "low"}`);

    parts.push(`Composition: ${features.composition.composition_type}`);
    parts.push(`Texture: ${features.composition.texture_variance > 0.6 ? "heavily textured, visible brushwork" : features.composition.texture_variance > 0.3 ? "moderate texture" : "smooth, flat"}`);

    parts.push(`Mood: ${style.mood.join(", ")}`);
    parts.push(`Techniques: ${style.techniques.join("; ")}`);

    return parts.join(". ");
}

function exportStyleJSON(data, styleIdx) {
    const s = data.styles[styleIdx];
    const f = data.features;

    const prompt = buildStylePrompt(s.style, f);

    const colorPalette = f.colors.palette.map((c) => ({
        name: c.name,
        hex: c.hex,
        rgb: c.rgb,
    }));

    const exportData = {
        _meta: {
            source: "Art Style Analyzer",
            exported: new Date().toISOString(),
            rank: s.rank,
        },
        style: {
            name: s.style.name,
            era: s.style.era,
            movement: s.style.movement,
            confidence: s.confidence,
            description: s.style.description,
            influences: s.style.influences,
            key_artists: s.style.key_artists,
        },
        prompt_for_image_generation: s.style.style_transfer_prompt || prompt,
        techniques: s.style.techniques,
        mood: s.style.mood,
        color_analysis: {
            dominant_color: f.colors.dominant_color,
            palette: colorPalette,
            temperature: f.colors.temperature,
            saturation: f.colors.saturation,
            brightness: f.colors.brightness,
            warmth: f.colors.warmth,
            color_diversity: f.colors.color_diversity,
        },
        composition: {
            type: f.composition.composition_type,
            symmetry: f.composition.symmetry,
            edge_density: f.composition.edge_density,
            texture_variance: f.composition.texture_variance,
            complexity: f.composition.complexity,
            focal_strength: f.composition.focal_strength,
        },
        lighting: {
            key_type: f.lighting.key_type,
            contrast: f.lighting.contrast,
            tonal_range: f.lighting.tonal_range,
            dramatic_lighting: f.lighting.dramatic_lighting,
            light_direction: f.lighting.light_direction,
            highlights_pct: f.lighting.highlights_pct,
            shadows_pct: f.lighting.shadows_pct,
        },
        analysis_breakdown: s.analysis_breakdown,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${s.style.name.toLowerCase().replace(/[^a-z0-9]+/g, "_")}_style.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
