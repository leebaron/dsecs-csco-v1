#!/usr/bin/env bash
# DSECS Paper Build Script
# Usage: ./build.sh [clean|figures|paper|all|arxiv]

set -euo pipefail
cd "$(dirname "$0")"

BUILD_DIR="_build"
ARXIV_DIR="_arxiv_submission"

case "${1:-all}" in
  clean)
    echo "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR" "$ARXIV_DIR"
    rm -f *.aux *.log *.blg *.bbl *.out *.synctex.gz
    echo "Done."
    ;;

  figures)
    echo "Generating figures..."
    mkdir -p figures
    python3 figures/generator.py --seed 42 --format pdf
    ;;

  paper)
    echo "Building paper PDF..."
    mkdir -p "$BUILD_DIR"
    
    # Ensure figures exist
    if [ ! -f figures/fig1_convergence.pdf ]; then
      echo "  Figures missing, generating..."
      python3 figures/generator.py --seed 42 --format pdf
    fi

    cd "$BUILD_DIR"
    cp ../main.tex ../neurips_2025.sty ../references.bib .
    mkdir -p figures
    cp ../figures/*.pdf figures/

    echo "  pdflatex (1/3)..."
    pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
    echo "  bibtex..."
    bibtex main > /dev/null 2>&1 || true
    echo "  pdflatex (2/3)..."
    pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true
    echo "  pdflatex (3/3)..."
    pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1 || true

    if [ -f main.pdf ]; then
      cp main.pdf ../dsecs_neurips.pdf
      echo ""
      echo "✅ Paper built: dsecs_neurips.pdf"
    else
      echo ""
      echo "❌ PDF build failed. Check $BUILD_DIR/main.log for errors."
    fi
    ;;

  experiment)
    echo "Running experiments..."
    mkdir -p results
    python3 code/simulation.py --full-benchmark
    ;;

  all)
    echo "=== DSECS Paper Build ==="
    $0 figures
    $0 experiment
    $0 paper
    echo "=== Build Complete ==="
    ;;

  arxiv)
    echo "Building arXiv submission package..."
    mkdir -p "$ARXIV_DIR"
    $0 figures 2>/dev/null || true

    # Copy all submission files
    cp main.tex "$ARXIV_DIR/"
    cp neurips_2025.sty "$ARXIV_DIR/"
    cp references.bib "$ARXIV_DIR/"
    mkdir -p "$ARXIV_DIR/figures" "$ARXIV_DIR/code"
    cp figures/*.pdf "$ARXIV_DIR/figures/"
    cp code/simulation.py "$ARXIV_DIR/code/"
    
    # Generate arXiv submission zip
    cd "$ARXIV_DIR"
    tar czf ../dsecs_arxiv_submission.tar.gz .
    cd ..
    echo ""
    echo "✅ arXiv package: dsecs_arxiv_submission.tar.gz"
    echo "   Contents:"
    tar tzf dsecs_arxiv_submission.tar.gz | sed 's/^/     /'
    ;;

  *)
    echo "Usage: $0 [clean|figures|paper|experiment|all|arxiv]"
    exit 1
    ;;
esac
