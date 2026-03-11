#!/usr/bin/env python3
"""Thin CLI wrapper around the isodde_bc_dify package.

For full usage, run::

    python -m isodde_bc_dify civic-annotate --help

This script provides a convenience entry point that mirrors the legacy
invocation style (``python scripts/civic_annotator.py``).  All core logic
lives in ``src/isodde_bc_dify/``.
"""

from __future__ import annotations

import os
import sys

# Ensure the src/ directory is on the import path when running the script
# directly (i.e. without ``pip install -e .``).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from isodde_bc_dify.cli import main  # noqa: E402


if __name__ == "__main__":
    # If invoked with no arguments, default to the legacy behaviour:
    # annotate the cohort MAF using the TSV backend.
    if len(sys.argv) == 1:
        data_dir = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "data"))
        default_args = [
            "civic-annotate",
            "--input-maf", os.path.join(data_dir, "cohortMAF.2026-03-10.maf"),
            "--output-maf", os.path.join(data_dir, "annotated_brca_maf.tsv"),
            "--data-dir", data_dir,
        ]
        main(default_args)
    else:
        main()
