// ============================================
// Art Style Analyzer — Main Application
// ============================================

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const previewContainer = document.getElementById("preview-container");
const previewImage = document.getElementById("preview-image");
const previewFilename = document.getElementById("preview-filename");
const dropZoneContent = document.getElementById("drop-zone-content");
const clearBtn = document.getElementById("clear-btn");
const analyzeBtn = document.getElementById("analyze-btn");
const loading = document.getElementById("loading");
const results = document.getElementById("results");
const resultsReport = document.getElementById("results-report");
const resultImage = document.getElementById("result-image");
const uploadSection = document.getElementById("upload-section");
const newAnalysisBtn = document.getElementById("new-analysis-btn");
const statsGrid = document.getElementById("stats-grid");
const loadingSteps = document.querySelectorAll(".loading-step");
const navbar = document.querySelector(".navbar");

let selectedFile = null;

// ============================================
// Navbar scroll effect
// ============================================
let lastScroll = 0;
window.addEventListener("scroll", () => {
    const scrollY = window.scrollY;
    if (scrollY > 20) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
    lastScroll = scrollY;
}, { passive: true });

// ============================================
// Drop zone interactions
// ============================================
dropZone.addEventListener("click", (e) => {
    if (e.target === clearBtn || clearBtn.contains(e.target)) return;
    if (!selectedFile) fileInput.click();
});

dropZone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (!selectedFile) fileInput.click();
    }
});

fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
});

// Drag and drop
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
newAnalysisBtn.addEventListener("click", () => {
    results.classList.add("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
    setTimeout(() => {
        uploadSection.classList.remove("hidden");
        resetUpload();
    }, 300);
});

// ============================================
// File handling
// ============================================
function handleFile(file) {
    if (!file.type.startsWith("image/")) return;
    selectedFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewFilename.textContent = file.name;
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

// ============================================
// Loading animation with step progression
// ============================================
let loadingTimer = null;
function startLoadingAnimation() {
    loadingSteps.forEach((step, i) => {
        step.classList.remove("active", "completed");
        setTimeout(() => {
            step.classList.add("active");
        }, i * 800);
    });

    // Mark steps as completed progressively
    loadingSteps.forEach((step, i) => {
        setTimeout(() => {
            step.classList.remove("active");
            step.classList.add("completed");
            // Activate next step
            if (i + 1 < loadingSteps.length) {
                loadingSteps[i + 1].classList.add("active");
            }
        }, (i + 1) * 800 + 1200);
    });
}

function resetLoadingAnimation() {
    loadingSteps.forEach((step) => {
        step.classList.remove("active", "completed");
    });
}

// ============================================
// Analysis
// ============================================
async function analyzeImage() {
    if (!selectedFile) return;

    // Hide other sections, show loading
    uploadSection.classList.add("hidden");
    results.classList.add("hidden");
    loading.classList.remove("hidden");

    // Scroll to loading
    loading.scrollIntoView({ behavior: "smooth", block: "center" });

    // Start the animated loading steps
    resetLoadingAnimation();
    startLoadingAnimation();

    const formData = new FormData();
    formData.append("image", selectedFile);

    try {
        const response = await fetch("/analyze", { method: "POST", body: formData });
        const data = await response.json();

        // Complete all loading steps
        loadingSteps.forEach((step) => {
            step.classList.remove("active");
            step.classList.add("completed");
        });

        // Brief pause to show completion
        await new Promise(r => setTimeout(r, 400));

        loading.classList.add("hidden");

        if (data.error) {
            showError(data.error);
            return;
        }

        renderResults(data);
        results.classList.remove("hidden");

        // Scroll to results
        setTimeout(() => {
            results.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 100);

    } catch (err) {
        loading.classList.add("hidden");
        loadingSteps.forEach((step) => {
            step.classList.remove("active", "completed");
        });
        showError("Analysis failed. Please check your connection and try again.");
    }
}

function showError(msg) {
    // Create a toast-like error
    const existing = document.querySelector(".error-banner");
    if (existing) existing.remove();

    const banner = document.createElement("div");
    banner.className = "error-banner";
    banner.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
        <span>${msg}</span>
        <button onclick="this.parentElement.remove(); uploadSection.classList.remove('hidden')" class="btn-icon" style="flex-shrink:0;width:28px;height:28px;background:rgba(255,255,255,0.08);color:#fff;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
    `;
    Object.assign(banner.style, {
        position: "fixed",
        top: "80px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: "200",
        background: "rgba(239,68,68,0.1)",
        border: "1px solid rgba(239,68,68,0.3)",
        borderRadius: "12px",
        padding: "0.75rem 1rem",
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        color: "#FCA5A5",
        fontSize: "0.88rem",
        fontWeight: "500",
        backdropFilter: "blur(20px)",
        maxWidth: "90vw",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        animation: "fadeSlideUp 0.3s ease-out",
    });
    document.body.appendChild(banner);

    setTimeout(() => {
        if (banner.parentElement) banner.remove();
        uploadSection.classList.remove("hidden");
    }, 5000);
}

// ============================================
// Results rendering
// ============================================
function renderResults(data) {
    resultImage.src = data.image_url;
    resultsReport.innerHTML = "";
    statsGrid.innerHTML = "";

    // ---- Stats Overview ----
    const stats = [
        { label: "Color Temperature", value: data.features.colors.temperature, cls: "warm" },
        { label: "Saturation", value: formatPercent(data.features.colors.saturation), cls: "accent" },
        { label: "Brightness", value: formatPercent(data.features.colors.brightness), cls: "" },
        { label: "Lighting", value: data.features.lighting.key_type, cls: "accent2" },
        { label: "Composition", value: data.features.composition.composition_type, cls: "" },
        { label: "Contrast", value: formatPercent(data.features.lighting.contrast), cls: "" },
        { label: "Texture", value: formatPercent(data.features.composition.texture_variance), cls: "" },
        { label: "Complexity", value: formatPercent(data.features.composition.complexity), cls: "" },
    ];

    stats.forEach(s => {
        const el = document.createElement("div");
        el.className = "stat-item";
        el.innerHTML = `<span class="stat-label">${s.label}</span><span class="stat-value ${s.cls}">${s.value}</span>`;
        statsGrid.appendChild(el);
    });

    // ---- Style Cards ----
    const scrollWrapper = document.createElement("div");
    scrollWrapper.className = "results-report";

    data.styles.forEach((s, idx) => {
        const card = document.createElement("div");
        card.className = `style-card${idx === 0 ? " top-match" : ""}`;
        card.style.animationDelay = `${idx * 0.1}s`;

        let html = `
            <div class="style-header">
                <span class="style-name">${escapeHtml(s.style.name)}</span>
                <span class="style-era">${escapeHtml(s.style.era)}</span>
                ${idx === 0 ? '<span class="top-match-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>Best Match</span>' : ''}
            </div>
            <div class="style-confidence">
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width:0%"></div>
                </div>
                <span class="confidence-text">${s.confidence}%</span>
                <button class="export-btn" data-style-idx="${idx}" title="Export this analysis as JSON">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Export JSON
                </button>
            </div>
            <p class="style-description">${escapeHtml(s.style.description)}</p>
        `;

        // Animate confidence bar
        setTimeout(() => {
            const fill = card.querySelector(".confidence-fill");
            if (fill) fill.style.width = s.confidence + "%";
        }, 200 + idx * 150);

        // Analysis breakdown sections
        if (s.analysis_breakdown) {
            s.analysis_breakdown.forEach((section, secIdx) => {
                const sectionId = `section-${idx}-${secIdx}`;

                if (section.copyable) {
                    html += `<div class="analysis-section">
                        <div class="analysis-section-header" onclick="toggleSection('${sectionId}')">
                            <h4>${escapeHtml(section.title)}</h4>
                            <svg class="section-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                        </div>
                        <div class="analysis-section-body" id="${sectionId}">
                            <div class="prompt-block">
                                <p class="prompt-text">${escapeHtml(section.details[0])}</p>
                                <button class="copy-btn" data-prompt="${escapeAttr(section.details[0])}">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                                    Copy Prompt
                                </button>
                            </div>
                        </div>
                    </div>`;
                } else {
                    html += `<div class="analysis-section">
                        <div class="analysis-section-header" onclick="toggleSection('${sectionId}')">
                            <h4>${escapeHtml(section.title)}</h4>
                            <svg class="section-toggle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                        </div>
                        <div class="analysis-section-body" id="${sectionId}">
                            <ul>`;

                    if (section.matched) {
                        section.matched.forEach((m) => {
                            html += `<li>${escapeHtml(m)}</li>`;
                        });
                    }
                    if (section.deviations) {
                        section.deviations.forEach((d) => {
                            html += `<li class="deviation">${escapeHtml(d)}</li>`;
                        });
                    }
                    if (section.details) {
                        section.details.forEach((d) => {
                            html += `<li>${escapeHtml(d)}</li>`;
                        });
                    }

                    html += `</ul></div></div>`;
                }
            });
        }

        // Techniques
        if (s.style.techniques && s.style.techniques.length) {
            html += `<div class="analysis-section">
                <div class="analysis-section-header">
                    <h4>Techniques</h4>
                </div>
                <div><div class="tags">`;
            s.style.techniques.forEach((t) => {
                html += `<span class="tag">${escapeHtml(t)}</span>`;
            });
            html += `</div></div></div>`;
        }

        // Mood
        if (s.style.mood && s.style.mood.length) {
            html += `<div class="analysis-section">
                <div class="analysis-section-header">
                    <h4>Mood & Atmosphere</h4>
                </div>
                <div><div class="tags">`;
            s.style.mood.forEach((m) => {
                html += `<span class="tag">${escapeHtml(m)}</span>`;
            });
            html += `</div></div></div>`;
        }

        // Color palette
        if (data.features.colors.palette && data.features.colors.palette.length) {
            html += `<div class="analysis-section">
                <div class="analysis-section-header">
                    <h4>Color Palette</h4>
                </div>
                <div><div class="palette-strip">`;
            data.features.colors.palette.forEach((c) => {
                html += `<div class="palette-swatch" style="background:${c.hex}" title="${escapeHtml(c.name)}"><span class="tooltip">${escapeHtml(c.name)}<br>${c.hex}</span></div>`;
            });
            html += `</div></div></div>`;
        }

        // Key info badges
        html += `<div class="key-info">
            <span class="key-badge"><strong>Lighting:</strong> ${escapeHtml(data.features.lighting.key_type)} (${escapeHtml(data.features.lighting.light_direction)})</span>
            <span class="key-badge"><strong>Temperature:</strong> ${escapeHtml(data.features.colors.temperature)}</span>
            <span class="key-badge"><strong>Composition:</strong> ${escapeHtml(data.features.composition.composition_type)}</span>
        </div>`;

        // Key artists
        if (s.style.key_artists && s.style.key_artists.length) {
            html += `<div class="analysis-section">
                <div class="analysis-section-header">
                    <h4>Key Artists</h4>
                </div>
                <div><div class="tags">`;
            s.style.key_artists.forEach((a) => {
                html += `<span class="tag">${escapeHtml(a)}</span>`;
            });
            html += `</div></div></div>`;
        }

        // Influences
        if (s.style.influences) {
            html += `<div class="analysis-section">
                <div class="analysis-section-header">
                    <h4>Artistic Influences</h4>
                </div>
                <div><p class="style-description" style="margin:0.25rem 0 0">${escapeHtml(s.style.influences)}</p></div>
            </div>`;
        }

        card.innerHTML = html;

        // Wire up events
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
                }).catch(() => {
                    // Fallback
                    const ta = document.createElement("textarea");
                    ta.value = promptText;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
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
}

// ============================================
// Section toggle
// ============================================
function toggleSection(id) {
    const body = document.getElementById(id);
    const toggle = body.parentElement.querySelector(".section-toggle");
    if (!body) return;
    body.classList.toggle("collapsed");
    if (toggle) toggle.classList.toggle("collapsed");
}

// ============================================
// Export
// ============================================
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

// ============================================
// Helpers
// ============================================
function formatPercent(v) {
    if (v == null) return "—";
    return (v * 100).toFixed(0) + "%";
}

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    if (!str) return "";
    return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/\n/g, "&#10;");
}
