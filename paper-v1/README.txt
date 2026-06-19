DSECS NeurIPS 2026 Submission - README

This directory contains the DSECS paper package for
NeurIPS 2026 / arXiv submission.

Contents:
  main.tex              - Main paper (8 pages)
  appendix.tex          - Supplementary proofs
  neurips_2026.sty      - NeurIPS style file
  references.bib        - Bibliography
  figures/              - Publication-ready figures (4)
  data/                 - Experimental data (JSON)
  run_experiments.py    - Experiment runner
  generate_figures.py   - Figure generator

System: https://github.com/leebaron/dsecs-csco-v1

Compile:
  pdflatex main && bibtex main && pdflatex main && pdflatex main

Authors: Anonymous (double-blind)

