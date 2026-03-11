"""Core annotation orchestrator.

Reads a MAF file, iterates over each row, calls the selected backend to
obtain a ``CIViCAnnotation``, and appends the result columns.  Saves
progress every ``save_every`` rows.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

import pandas as pd

from .backends.graphql import GraphQLBackend
from .backends.tsv import TSVBackend
from .io import read_maf, write_maf
from .schemas import CIViCAnnotation

logger = logging.getLogger(__name__)

Backend = Union[TSVBackend, GraphQLBackend]


def _strip_p_prefix(hgvsp: str) -> str:
    """Remove the ``p.`` prefix from HGVSp_Short if present."""
    if hgvsp.startswith("p."):
        return hgvsp[2:]
    return hgvsp


def annotate_maf(
    input_maf: Path,
    output_maf: Path,
    backend: Backend,
    save_every: int = 50,
) -> pd.DataFrame:
    """Run CIViC annotation on *input_maf* and write to *output_maf*.

    Returns the annotated DataFrame.
    """
    df = read_maf(input_maf)

    out_cols = CIViCAnnotation.output_columns()
    for col in out_cols:
        if col not in df.columns:
            df[col] = ""

    total = len(df)
    matched = 0

    for idx, row in df.iterrows():
        gene = row.get("Hugo_Symbol")
        hgvsp_raw = row.get("HGVSp_Short")

        if pd.isna(gene) or not str(gene).strip():
            continue

        gene = str(gene).strip()

        if pd.isna(hgvsp_raw) or not isinstance(hgvsp_raw, str) or not hgvsp_raw.strip():
            continue

        variant_name = _strip_p_prefix(hgvsp_raw.strip())
        if not variant_name:
            continue

        ann = backend.annotate(gene, variant_name)

        for col in out_cols:
            df.at[idx, col] = getattr(ann, col, "")

        if ann.CIViC_Match_Type and ann.CIViC_Match_Type != "none":
            matched += 1

        i = int(idx) + 1  # type: ignore[arg-type]
        if i % save_every == 0:
            write_maf(df, output_maf)
            logger.info("Progress: %d / %d rows (matched so far: %d)", i, total, matched)

    write_maf(df, output_maf)
    logger.info(
        "Annotation complete: %d / %d rows matched at least one CIViC variant",
        matched,
        total,
    )
    return df
