# Manuscript

LaTeX source for the *Games: Research and Practice* submission, using ACM's `acmart` class.

Build options:

- **Overleaf** (easiest): upload `main.tex` and `refs.bib`, and the figures from `../figures/` into a `figures/` folder (then change `\graphicspath` to `{{figures/}}`). Overleaf has `acmart` built in.
- **Locally**: install a TeX distribution (MiKTeX on Windows), then from this folder run `latexmk -pdf main.tex`.

`review,anonymous` in `\documentclass` gives line numbers and hides the author for peer review; remove them for the camera-ready version.
