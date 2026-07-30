"""Thesis Figure (new) - execution flowchart of the LSEQM+DL pipeline.

Answers the exam request for a standard-symbol flowchart of the method: it
shows the stage dependency (each stage consumes the previous stage's output),
the dedicated per-stage output that makes the stages independently comparable,
the decision node that governs when the CNN is activated, and the verification
step, which reads all three corrected products. Figures 3.3 and 3.6 remain the
detail views of the pipeline and Stage 4; this is the process-and-control view.

Accuracy notes (checked against the source):
- The CNN gate is TWO conditions, not one. src/deep_learning.py:568 first builds
  mask_extreme (pixel above the per-pixel GPD_THRESHOLD_PERCENTILE quantile),
  and only inside that mask does the station-density confidence scale the blend
  (alpha_eff). Sub-threshold pixels pass through as LSEQM regardless of density,
  and C = 0 gives alpha_eff = 1, which is also LSEQM - so the "no" branch has one
  outcome for both failure modes and the two conditions merge into one node.
- The gridded metrics come from src/metrics.py:run_metrics_pipeline and the CQI
  from src/qa_framework.py:run_qa_pipeline (a separate module that reads the
  metrics NetCDF). The BMKG arm is src/station_validation.py and writes a
  per-station CSV with a different metric subset - it does NOT feed the
  metrics/quality NetCDF, so the store names both artefact types explicitly.

Standard ANSI/ISO 5807 symbols only (drawn by flow_symbols); a legend keys the
ones used. Output: paper/thesis/figures/fig_thesis_03_execution.png
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
import flow_symbols as fs  # noqa: E402

OUT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "figures", "fig_thesis_03_execution.png"))

TERM = "#dfe7f2"
PROC = "#e9f3e8"
PRED = "#e3eecf"
DEC = "#fdf0e0"
IO = "#eef2f7"
STORE = "#f2e7f1"
DOC = "#f4f4f4"

SP = 45        # correction spine x
OUTX = 75      # per-stage output column x
BUS = 91       # right-hand collector bus x
GAP = 4.2      # guaranteed vertical gap between consecutive spine boxes
TOP = 96

fig, ax = plt.subplots(figsize=(9.4, 12.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# ---- stack the spine so every vertical arrow is >= GAP long ---------------
spine = [
    ("start", fs.terminator, 4.6, TERM, "Start", 9),
    ("imerg", fs.data_io, 6.0, IO, "IMERG-L daily\n(input to correct)", 8.5),
    ("ls", fs.process, 6.5, PROC, "Stage 1: Linear Scaling\n(mean bias)", 8.5),
    ("eqm", fs.predefined, 7.5, PRED, "Stages 2-3: EQM + GPD\n(distribution + heavy tail)", 8.5),
    ("dec", fs.decision, 9.0, DEC, "Above GPD threshold\nand $C(x,y) > 0$ ?", 8.5),
    ("cnn", fs.process, 7.5, PROC, "Stage 4: CNN refinement, blended\n$\\alpha_{\\mathrm{eff}} = 1 - C\\,(1-\\alpha)$", 8.5),
    ("ver", fs.predefined, 7.5, PRED, "Verification of all three products:\n31 metrics + CQI vs CPC-UNI, station validation vs BMKG", 8.0),
    ("met", fs.stored_data, 6.5, STORE, "metrics + quality (NetCDF)\nstation validation (CSV)", 8.0),
    ("end", fs.terminator, 4.6, TERM, "End", 9),
]
W = dict(start=16, imerg=24, ls=30, eqm=36, dec=30, cnn=36, ver=46, met=26, end=16)
cy, top = {}, TOP
for key, fn, h, fill, label, lfs in spine:
    c = top - h / 2
    cy[key] = c
    bold = key in ("start", "end")
    fn(ax, SP, c, W[key], h, label, fill, fs=lfs, bold=bold)
    top = c - h / 2 - GAP

# convenience: box top / bottom edge y for a spine node
H = {k: h for k, _, h, _, _, _ in spine}
def topy(k):  return cy[k] + H[k] / 2
def boty(k):  return cy[k] - H[k] / 2

# ---- side inputs ---------------------------------------------------------
CFGY = 88
fs.document(ax, 16, CFGY, 20, 5.5, "config.yml\npaths + parameters", DOC, fs=8)
fs.data_io(ax, 74, cy["imerg"], 22, 6, "CPC-UNI\n(calibration reference)", IO, fs=8)
fs.data_io(ax, 13, cy["met"], 16, 6, "BMKG\n(independent)", IO, fs=8)

# ---- per-stage dedicated outputs -----------------------------------------
fs.stored_data(ax, OUTX, cy["ls"], 18, 5.2, "corrected_ls", STORE, fs=8)
fs.stored_data(ax, OUTX, cy["eqm"], 18, 5.2, "corrected_lseqm", STORE, fs=8)
fs.stored_data(ax, OUTX + 2, cy["cnn"], 18, 5.2, "corrected_lseqmdl", STORE, fs=8)

# ---- spine arrows --------------------------------------------------------
fs.arrow(ax, (SP, boty("start")), (SP, topy("imerg")))
fs.arrow(ax, (SP, boty("imerg")), (SP, topy("ls")))
fs.arrow(ax, (SP, boty("ls")), (SP, topy("eqm")), label="LS output")
fs.arrow(ax, (SP, boty("eqm")), (SP, topy("dec")), label="LSEQM output")
fs.arrow(ax, (SP, boty("dec")), (SP, topy("cnn")), label="yes")
fs.arrow(ax, (SP, boty("ver")), (SP, topy("met")))
fs.arrow(ax, (SP, boty("met")), (SP, topy("end")))

# CPC-UNI (calibration reference) into the correction
fs.arrow(ax, (63, boty("imerg") + 0.5), (SP + 13, topy("ls") - 1))

# ---- stage -> its stored output ------------------------------------------
fs.arrow(ax, (SP + W["ls"] / 2, cy["ls"]), (OUTX - 9, cy["ls"]))
fs.arrow(ax, (SP + W["eqm"] / 2, cy["eqm"]), (OUTX - 9, cy["eqm"]))
fs.arrow(ax, (SP + W["cnn"] / 2, cy["cnn"]), (OUTX + 2 - 9, cy["cnn"]))

# ---- no-branch: C = 0 -> CNN weight 0, product stays LSEQM ----------------
ny = (cy["dec"] + cy["cnn"]) / 2
fs.arrow(ax, (SP + W["dec"] / 2, cy["dec"]), (OUTX + 2, cy["dec"]))
fs.arrow(ax, (OUTX + 2, cy["dec"]), (OUTX + 2, topy("cnn")))
ax.text(OUTX + 2 - 2, ny, "no: CNN weight 0\n(product = LSEQM)", fontsize=7.4,
        style="italic", color="#333", ha="right", va="center")

# ---- bus: all three corrected products -> verification -------------------
for k in ("ls", "eqm", "cnn"):
    x0 = OUTX + (2 if k == "cnn" else 0) + 9
    fs.arrow(ax, (x0, cy[k]), (BUS, cy[k]))
ax.plot([BUS, BUS], [cy["ver"], cy["ls"]], color=fs.EDGE, lw=1.6, zorder=2)
fs.arrow(ax, (BUS, cy["ver"]), (SP + W["ver"] / 2, cy["ver"]))
ax.text(BUS - 13, (cy["cnn"] + cy["ver"]) / 2, "all three\ncorrected products",
        fontsize=7.8, style="italic", color="#333", ha="center", va="center")

# ---- BMKG -> verification (end at the box edge so the head is not hidden) --
fs.arrow(ax, (20, cy["met"] + 2.5), (SP - W["ver"] / 2 + 8, boty("ver")))

# ---- config -> LS (dashed L-route down the left, clear of the IMERG symbol) -
lsy = cy["ls"] + 1.2                         # enter LS a little above its middle
ax.plot([16, 16], [CFGY - 5.5 / 2, lsy], color="#777", lw=1.2, ls="--", zorder=2)
fs.arrow(ax, (16, lsy), (SP - W["ls"] / 2, lsy), ls="--", color="#777", lw=1.2)
ax.text(13.6, (CFGY - 5.5 / 2 + lsy) / 2, "parameters", fontsize=7.6,
        style="italic", color="#777", ha="center", va="center", rotation=90)

# ---- legend --------------------------------------------------------------
fs.legend(ax, 3, cy["ls"] - 2, [
    (fs.terminator, "Terminator"),
    (fs.process, "Process"),
    (fs.predefined, "Predefined process"),
    (fs.decision, "Decision"),
    (fs.data_io, "Data input / output"),
    (fs.stored_data, "Stored data"),
    (fs.document, "Document"),
], fs=7.8)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote %s" % os.path.basename(OUT))
