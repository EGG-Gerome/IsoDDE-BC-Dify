"""Tests for MAF I/O and schema validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from isodde_bc_dify.civic.io import read_maf, validate_maf


def test_read_valid_maf(tiny_maf: Path):
    df = read_maf(tiny_maf)
    assert "Hugo_Symbol" in df.columns
    assert "HGVSp_Short" in df.columns
    assert len(df) == 5


def test_validate_maf_missing_column(tmp_path: Path):
    bad_maf = tmp_path / "bad.tsv"
    bad_maf.write_text("Hugo_Symbol\tFoo\nPIK3CA\tbar\n")

    with pytest.raises(ValueError, match="HGVSp_Short"):
        read_maf(bad_maf)
