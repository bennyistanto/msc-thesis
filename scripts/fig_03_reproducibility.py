"""Thesis Figure 3.7 - "Reproducible implementation architecture".

Schematic of the LSEQM+DL reproducibility design (Section 3.8): a single
config.yml and a pinned environment drive six numbered notebooks, which call
ten single-responsibility src/ modules, which write the data/output
verification artefacts; a Quarto docs/ site cross-links every result to its
notebook cell and source function.

Data: none (schematic, no external inputs).

Output: paper/thesis/figures/fig_thesis_03_reproducibility.png
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(r"C:\Users\benny\OneDrive\Documents\Github\hybrid-bias-correction")
OUT = ROOT / "paper" / "thesis" / "figures" / "fig_thesis_03_reproducibility.png"

# muted, print-friendly palette (fill, edge) per layer
DECL = ("#e7eef8", "#3f6396")   # declared: config.yml + environment.yml
NB   = ("#e9f3e8", "#4a8a48")   # notebooks
SRC  = ("#fdf0e0", "#c07d28")   # src/ modules
OUTB = ("#f2e7f1", "#835089")   # data/output
DOC  = ("#f2f2f2", "#6f6f6f")   # docs (Quarto)
INK  = "#232323"

fig, ax = plt.subplots(figsize=(8.6, 7.0))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, style, fs=9, bold=False, dashed=False):
    fc, ec = style
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.4",
        fc=fc, ec=ec, lw=1.3, linestyle="--" if dashed else "-"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=INK, fontweight="bold" if bold else "normal",
            linespacing=1.15)


def flow(y1, y2, label):
    ax.add_patch(FancyArrowPatch((50, y1), (50, y2), arrowstyle="-|>",
                 mutation_scale=16, lw=1.6, color="#333"))
    ax.text(51.5, (y1 + y2) / 2, label, fontsize=8.5, style="italic",
            color="#333", ha="left", va="center")


def band(y, text, color):
    ax.text(50, y, text, ha="center", va="center", fontsize=9.5,
            style="italic", color=color, fontweight="bold")


# Vertical layout. Box heights are sized to the text they carry (line count x
# font size x linespacing) plus a small padding, rather than to a fixed block
# height; the band labels sit in the gap between an arrow head and the row it
# names, so they never overlap either.

# --- declared layer -------------------------------------------------------
box(6, 89.5, 42, 7.5, "config.yml\nsingle source of paths and parameters", DECL, bold=True)
box(52, 89.5, 42, 7.5, "environment.yml\npinned package versions", DECL, bold=True)
flow(89.5, 85.0, "declared once")

# --- notebooks ------------------------------------------------------------
band(83.5, "six numbered notebooks/", NB[1])
nb = ["01\ndata\nacquisition", "02\nLSEQM+DL\ncorrection", "03\nmeasuring\nperformances",
      "04\nQA\nframework", "05\nstation\nvalidation", "06\nvisualisation\nhub"]
nbw, gap, x0 = 13.75, 1.5, 5.0
for i, t in enumerate(nb):
    box(x0 + i * (nbw + gap), 73.0, nbw, 9, t, NB, fs=8)
flow(73.0, 68.0, "call")

# --- src/ modules ---------------------------------------------------------
band(66.5, "src/  twelve single-responsibility modules", SRC[1])
mods = ["config", "io", "utility", "bias_\ncorrection", "distribution_\nfitting",
        "deep_\nlearning", "station_\ndensity", "metrics", "qa_\nframework",
        "station_\nvalidation", "taylor_\ndiagram", "visualisation"]
mw, mg, mx0 = 13.8, 1.4, 5.0
for r in range(2):
    for c in range(6):
        box(mx0 + c * (mw + mg), 58.0 - r * 8.5, mw, 7, mods[r * 6 + c], SRC, fs=7.4)
flow(49.5, 44.5, "write")

# --- data/output ----------------------------------------------------------
box(13, 36.0, 74, 7.5, "data/output\ncorrected fields   -   31 metrics   -   QA / CQI   -   figures",
    OUTB, bold=True)

# --- docs (Quarto) --------------------------------------------------------
box(13, 20.5, 74, 7,
    "docs/  (Quarto site)\ncross-links every result to its notebook cell and src/ function",
    DOC, fs=8.5, dashed=True)
# dashed link from docs up to the output layer
ax.add_patch(FancyArrowPatch((50, 28.5), (50, 35.5), arrowstyle="-|>",
             mutation_scale=13, lw=1.3, color="#6f6f6f", linestyle="--"))

# --- trace callout --------------------------------------------------------
ax.add_patch(FancyBboxPatch((6, 7.0), 88, 5.5,
             boxstyle="round,pad=0.4,rounding_size=1.4",
             fc="#fffdf4", ec="#b9a24a", lw=1.2))
ax.text(50, 9.75,
        "Every reported number traces to a config value, a notebook cell, and a src/ function.",
        ha="center", va="center", fontsize=9.2, color="#5c531f", fontweight="bold")

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
fig.savefig(OUT, dpi=200, facecolor="white")
print(f"wrote {OUT.name}")
