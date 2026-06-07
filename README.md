# How Far Can Bias Correction Improve Daily Satellite Precipitation?

Master's thesis (Bogor Agricultural University, 2026) on the hybrid LSEQM+DL bias correction framework for daily Integrated Multi-satellitE Retrievals for GPM Late Run (IMERG-L) precipitation over Indonesia, with gauge validation against 171 independent BMKG stations.

> **Status:** final draft submitted to the IPB Applied Climatology
> programme. See the parent code repository for the implementation
> and the data archive.

## Author

**Benny Istanto** (G2501222008)</br>
Applied Climatology Study Program</br>
Faculty of Mathematics and Natural Sciences</br>
Bogor Agricultural University</br>
Bogor, Indonesia

Supervised by Prof. Dr. Ir. Rizaldi Boer, M.S. and Dr. I Putu Santikayasa, S.Si., M.Sc.

## What this repository contains

This repository holds the LaTeX sources, figures, and figure-generator scripts for the thesis. The corresponding code, data pipeline, and validation framework live in the parent repository:

- Parent code repository: <https://github.com/bennyistanto/hybrid-bias-correction>
- Data archive: deposited on Zenodo (DOI in Appendix B of the thesis)

```
.
├── main_thesis.tex                  # entry point
├── frontmatter.tex                  # cover, abstracts, signatures, ToC, LoT, LoF
├── chapter_01_introduction.tex      # chapter 1
├── chapter_02_literature_review.tex # chapter 2
├── chapter_03_methods.tex           # chapter 3
├── chapter_04_results.tex           # chapter 4
├── chapter_05_discussion.tex        # chapter 5
├── chapter_06_conclusion.tex        # chapter 6
├── chapter_99_appendices.tex        # appendices A through G
├── biography.tex                    # author biography page
├── references.bib                   # bibliography (BibTeX)
├── ipb.bst                          # IPB PPKI bibliography style
├── build.sh                         # local build script (pdflatex x bibtex x pdflatex x pdflatex)
├── figures/                         # PNGs included by the .tex sources
└── scripts/                         # one Python script per figure (see scripts/README.md)
```

## How to build the PDF

### Prerequisites

- TeX Live 2023 or newer (with `pdflatex`, `bibtex`, `xspace`,
  `needspace`, `pdflscape`, `tocloft`, `titlesec`, `natbib`,
  `geometry`, `caption`, `booktabs`, `enumitem`, `hyperref`)
- GNU `sed` (for the `et al.` italic post-processing in `build.sh`)

### Build

```bash
./build.sh
```

This runs the canonical three-pass cycle:

1. `pdflatex` (skeleton, generates `.aux`/`.toc`)
2. `bibtex` (resolves citations) + post-processing `sed` for italic `et al.`
3. `pdflatex` (populates ToC / LoF / LoT)
4. `pdflatex` (stabilises cross-references)

The output is `main_thesis.pdf` (~ 97 pages, ~ 9 MB).

### Overleaf

This repository is Overleaf-compatible: upload the folder, set
`main_thesis.tex` as the main document, and use the pdfLaTeX compiler.
The `et al.` italic post-processing step does not run on Overleaf, so a
small number of `et al.` strings in the bibliography will render
upright instead of italic; the rest of the formatting is identical to
the local build.

## How to rebuild the figures

The figure generators live in `scripts/`. See `scripts/README.md` for
the one-script-per-figure inventory and dependencies. Each script is
runnable in isolation; collectively they require a scientific Python
stack (numpy / pandas / xarray / matplotlib / geopandas) plus access
to the data archive cited in Appendix B.

## Citation

If you reference this thesis, please cite it as recorded in
[`CITATION.cff`](CITATION.cff). After publication on Zenodo a DOI will
be added.

## License

The thesis text and figures are released under
[Creative Commons Attribution 4.0 (CC-BY-4.0)](LICENSE).
The build scripts and figure-generator Python code are released under
the [MIT License](LICENSE).

See [`LICENSE`](LICENSE) for the full text of both.

## Acknowledgments

Built on the IPB [PPKI](https://kmm.ipb.ac.id/ppki-edisi4-eng/) thesis format, customised for English-language submission. And the [modified](https://gist.github.com/bennyistanto/ef6b1a2bb1ed303a7832f789ac7e7a70) IPB CSL for English version.

Supervisors and data providers are credited in the front matter of the thesis.
