"""Thesis Figure 3.1 - research framework (kerangka penelitian), square layout.

Compact framework-of-thinking view: background -> objectives -> scope
(data -> approach -> the three working groups: Verification, Diagnostic,
Reproducibility) -> findings -> contribution, read top to bottom. The three
groups are tagged with the objective each serves (O1-O3) and keep the output
numbers (31 metrics + CQI). Full descriptive text lives in the paragraph after
the figure, not in the boxes. Square aspect so the figure fits on the Chapter 3
opening page. The ANSI process flowchart of the pipeline is the companion
Figure (execution flow).

Output: paper/thesis/figures/fig_thesis_03_framework.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "figures", "fig_thesis_03_framework.png"))

BG   = ("#eef1f5", "#5b6b82")
OBJ  = ("#e7eef8", "#3f6396")
DATA = ("#eef2f7", "#4a6a8a")
METH = ("#e9f3e8", "#4a8a48")
VER  = ("#fdf0e0", "#b8842a")
DIA  = ("#fcecec", "#b3524f")
REP  = ("#e9f1ec", "#4f8a6b")
FIND = ("#f2e7f1", "#835089")
CONT = ("#fffdf4", "#b9a24a")
INK  = "#232323"

fig, ax = plt.subplots(figsize=(9.2, 9.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, style, fs=9, bold=False):
    fc, ec = style
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.3,rounding_size=1.2",
                 fc=fc, ec=ec, lw=1.3, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=INK, fontweight="bold" if bold else "normal",
            linespacing=1.25, zorder=5)


def tag(x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=7.8,
            color="#7a1f5c", fontweight="bold", style="italic", zorder=6)


def down(x, y1, y2):
    ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle="-|>",
                 mutation_scale=15, lw=1.7, color="#444", zorder=2))


def vline(x, y1, y2):
    """Plain vertical connector (no arrowhead) - feeds a distribution bus."""
    ax.plot([x, x], [y1, y2], color="#444", lw=1.7, zorder=2,
            solid_capstyle="round")


def hbus(x1, x2, y):
    """Horizontal distribution/collector bus joining the fan-out arrows."""
    ax.plot([x1, x2], [y, y], color="#444", lw=1.7, zorder=2,
            solid_capstyle="round")


C = 50  # centre spine

# --- background -----------------------------------------------------------
box(4, 91, 92, 6.5, "Background: daily IMERG-L is biased, aggregate scores\n"
    "hide the failing dimension, and corrections are rarely reproducible",
    BG, fs=9, bold=True)
down(C, 90.8, 87.2)

# --- objectives -----------------------------------------------------------
box(4, 79.5, 92, 7, "", OBJ)
ax.text(7, 86.0, "Objectives", fontsize=9, fontweight="bold", color=INK,
        ha="left", va="center", zorder=6)
for cx, t in zip((28, 50, 73),
                 ("O1  stage\nattribution", "O2  timing and\ncalendar window",
                  "O3  reproducible\npipeline")):
    ax.text(cx, 82.4, t, ha="center", va="center", fontsize=8, color=INK,
            linespacing=1.15, zorder=6)
down(C, 79.3, 74.7)

# --- scope boundary (dash-dot) --------------------------------------------
ax.add_patch(FancyBboxPatch((3, 27.5), 94, 47,
             boxstyle="round,pad=0.2,rounding_size=1.0",
             fc="none", ec="#555", lw=1.5, linestyle="-.", zorder=1))
ax.text(95.5, 72.6, "Research scope", fontsize=8.3, style="italic",
        color="#555", ha="right", va="center", zorder=6)

# --- data -----------------------------------------------------------------
box(8, 65, 84, 6, "Data:  IMERG-L (input)  |  CPC-UNI (calibration)  |  "
    "BMKG (validation)", DATA, fs=9)
down(C, 64.8, 61.2)

# --- approach -------------------------------------------------------------
box(8, 54, 84, 7, "Approach:  LS $\\rightarrow$ EQM $\\rightarrow$ GPD "
    "$\\rightarrow$ CNN,\nblended by station density $C(x,y)$", METH, fs=9)
tag(88.5, 59.4, "O1")
vline(C, 54.0, 50.4)

# --- three working groups -------------------------------------------------
gw, gy, gh = 28, 33.5, 12.5
groups = [(6, VER, "Verification", "31 metrics\n+ CQI", "O1"),
          (36, DIA, "Diagnostic", "correlation ceiling\ncalendar window", "O2"),
          (66, REP, "Reproducibility", "open pipeline (Colab)\n+ application classes",
           "O3")]
for gx, style, title, body, otag in groups:
    box(gx, gy, gw, gh, "", style)
    ax.text(gx + gw / 2, gy + gh - 2.6, title, ha="center", va="center",
            fontsize=8.8, fontweight="bold", color=INK, zorder=6)
    ax.text(gx + gw / 2, gy + gh / 2 - 2.0, body, ha="center", va="center",
            fontsize=8, color=INK, linespacing=1.2, zorder=6)
    tag(gx + gw - 3, gy + gh - 1.4, otag)
# fan-out: approach -> distribution bus -> the three groups
hbus(20, 80, 50.4)
for gx in (20, 50, 80):
    down(gx, 50.4, 46.3)
# merge: the three groups -> collector bus -> findings
for gx in (20, 50, 80):
    vline(gx, 33.5, 30.2)
hbus(20, 80, 30.2)
down(C, 30.2, 23.7)

# --- findings -------------------------------------------------------------
box(4, 16.5, 92, 6.5, "Findings: corrected daily product, stage-resolved\n"
    "attribution, and a recoverable calendar-window timing ceiling",
    FIND, fs=9)
down(C, 16.3, 12.7)

# --- contribution ---------------------------------------------------------
box(4, 5.5, 92, 6.5, "Contribution: an open, transferable bias-correction\n"
    "framework with honest stage-resolved verification",
    CONT, fs=9, bold=True)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote %s" % os.path.basename(OUT))
