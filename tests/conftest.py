from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture()
def tiny_variant_tsv() -> Path:
    return FIXTURES_DIR / "tiny_variants.tsv"


@pytest.fixture()
def tiny_assertion_tsv() -> Path:
    return FIXTURES_DIR / "tiny_assertions.tsv"


@pytest.fixture()
def tiny_maf(tmp_path: Path) -> Path:
    """Copy the tiny MAF fixture to a temp dir so tests can write output nearby."""
    src = FIXTURES_DIR / "tiny_maf.tsv"
    dst = tmp_path / "tiny_maf.tsv"
    dst.write_text(src.read_text())
    return dst
