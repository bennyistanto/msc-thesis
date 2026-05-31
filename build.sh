#!/usr/bin/env bash
# Reliable multi-pass build for main_thesis.tex.
# latexmk -pdf has been intermittently stopping after the first pass on
# this thesis, leaving the .toc/.lof/.lot empty and \ref{} unresolved.
# This script does the explicit pdflatex/bibtex/pdflatex/pdflatex cycle.
#
# Usage: ./build.sh [--clean]

set -u
cd "$(dirname "$0")"

if [[ "${1:-}" == "--clean" ]]; then
  echo "[1/5] cleaning latex artifacts..."
  latexmk -C >/dev/null 2>&1 || true
fi

echo "[1/4] pdflatex pass 1 (skeleton, generates .aux/.toc)..."
pdflatex -interaction=nonstopmode main_thesis.tex >/dev/null

echo "[2/4] bibtex (resolves citations)..."
bibtex main_thesis >/dev/null

# Italicise "et al." everywhere in the bibliography. There are two
# distinct occurrences bibtex emits, and they need different handling:
#
#   (A) Bracket label    [Author et~al.(YEAR)]        - plain, needs italic
#   (B) Author-list trail   {\em et~al.}              - already italic via \em
#
# Wrapping (B) blindly with \textit{et~al.} consumes the closing brace
# that \em depends on, so italics leak through the rest of the entry
# (this was the visible bug from Nash through Wilkinson, with journal
# names mis-italicised). Protect (B) with a placeholder first, wrap (A),
# then restore (B). Idempotent on re-runs because the first sed only
# matches a bare "et~al." without surrounding \textit{}.
if [[ -f main_thesis.bbl ]]; then
  # 1. Protect already-italic "{\em et~al.}" from being touched.
  sed -i 's/{\\em et~al\.}/__EMETAL_PLACEHOLDER__/g' main_thesis.bbl
  # 2. Wrap bare "et~al." (which now only occurs in bracket labels) in
  #    \textit{}, but only if it is not already wrapped.
  sed -i -E 's/(\\textit\{)?et~al\.(\})?/\\textit{et~al.}/g' main_thesis.bbl
  # 3. Collapse any double-wrap from re-runs.
  sed -i -E 's/\\textit\{\\textit\{et~al\.\}\}/\\textit{et~al.}/g' main_thesis.bbl
  # 4. Restore protected occurrences. {\em ...} already italicises them.
  sed -i 's/__EMETAL_PLACEHOLDER__/{\\em et~al.}/g' main_thesis.bbl
fi

echo "[3/4] pdflatex pass 2 (populates ToC/LoF/LoT, refs first read)..."
pdflatex -interaction=nonstopmode main_thesis.tex >/dev/null

echo "[4/4] pdflatex pass 3 (stable cross-references)..."
pdflatex -interaction=nonstopmode main_thesis.tex >/dev/null

echo
echo "=== build summary ==="
grep -o "([0-9]* pages" main_thesis.log | tail -1
unresolved=$(grep -c "Citation.*undefined" main_thesis.log)
undef=$(grep -c "LaTeX Warning: Reference.*undefined" main_thesis.log)
overfull=$(grep -cE "Overfull \\\\hbox \\([5-9][0-9]\\.|Overfull \\\\hbox \\([1-9][0-9][0-9]\\." main_thesis.log)
echo "  unresolved citations: $unresolved"
echo "  undefined refs:       $undef"
echo "  overfull >5pt boxes:  $overfull"

for f in main_thesis.toc main_thesis.lof main_thesis.lot; do
  if [[ -s "$f" ]]; then
    echo "  [OK]    $f ($(wc -l < "$f") lines)"
  else
    echo "  [EMPTY] $f"
  fi
done
ls -la main_thesis.pdf 2>/dev/null
