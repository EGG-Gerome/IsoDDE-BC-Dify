"""Integration test: end-to-end annotation with tiny fixtures."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from isodde_bc_dify.civic.annotate import annotate_maf
from isodde_bc_dify.civic.backends.tsv import TSVBackend


def test_annotate_maf_end_to_end(
    tiny_maf: Path,
    tiny_variant_tsv: Path,
    tiny_assertion_tsv: Path,
    tmp_path: Path,
):
    output = tmp_path / "output.tsv"
    backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)

    df = annotate_maf(tiny_maf, output, backend, save_every=2)

    assert output.exists()
    result = pd.read_csv(output, sep="\t")

    # PIK3CA H1047R should be matched
    row_h1047r = result[result["HGVSp_Short"] == "p.H1047R"].iloc[0]
    assert row_h1047r["CIViC_Match_Type"] == "exact"
    assert "Alpelisib" in row_h1047r["CIViC_Drug_Associations"]

    # TP53 R175H should not be matched (not in fixture)
    row_tp53 = result[result["Hugo_Symbol"] == "TP53"].iloc[0]
    assert row_tp53["CIViC_Match_Type"] == "" or pd.isna(row_tp53["CIViC_Match_Type"])

    # BRCA1 with empty HGVSp_Short should be skipped gracefully
    row_brca1 = result[result["Hugo_Symbol"] == "BRCA1"].iloc[0]
    assert row_brca1["CIViC_Match_Type"] == "" or pd.isna(row_brca1["CIViC_Match_Type"])
