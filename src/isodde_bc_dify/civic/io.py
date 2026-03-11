"""I/O helpers: read / write MAF files and validate required columns."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_MAF_COLUMNS = {"Hugo_Symbol", "HGVSp_Short"}


def validate_maf(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if required columns are missing."""
    missing = REQUIRED_MAF_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"MAF file is missing required columns: {', '.join(sorted(missing))}. "
            f"Available columns: {', '.join(df.columns[:20])}…"
        )


def read_maf(path: Path, comment: str = "#") -> pd.DataFrame:
    """Read a MAF / TSV file into a DataFrame, skipping comment lines."""
    df = pd.read_csv(path, sep="\t", comment=comment, low_memory=False)
    validate_maf(df)
    logger.info("MAF loaded: %d rows, %d columns from %s", len(df), len(df.columns), path.name)
    return df


def write_maf(df: pd.DataFrame, path: Path) -> None:
    """Write annotated MAF back to TSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False)
    logger.info("Annotated MAF written to %s (%d rows)", path, len(df))
