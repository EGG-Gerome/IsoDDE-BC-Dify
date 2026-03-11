"""Tests for the offline TSV backend: index building & variant-level matching."""

from __future__ import annotations

from pathlib import Path

from isodde_bc_dify.civic.backends.tsv import TSVBackend


class TestTSVBackendIndexes:
    """Verify that indexes are built correctly from tiny fixtures."""

    def test_variant_index_has_expected_genes(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        assert "pik3ca" in backend.variant_index
        assert "erbb2" in backend.variant_index
        assert len(backend.variant_index["pik3ca"]) == 2

    def test_assertion_index_keyed_by_mol_profile_id(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        assert 100 in backend.assertion_index  # PIK3CA H1047R
        assert 306 in backend.assertion_index  # ERBB2 Amplification


class TestVariantLevelMatching:
    """Ensure assertions are scoped to the exact variant, not gene-wide."""

    def test_pik3ca_h1047r_gets_own_assertion(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        ann = backend.annotate("PIK3CA", "H1047R")

        assert ann.CIViC_Match_Type == "exact"
        assert ann.CIViC_AMP_Category == "Tier I - Level A"
        assert "Alpelisib" in ann.CIViC_Drug_Associations

    def test_pik3ca_e545k_gets_different_amp_level(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        ann = backend.annotate("PIK3CA", "E545K")

        assert ann.CIViC_Match_Type == "exact"
        assert ann.CIViC_AMP_Category == "Tier I - Level B"

    def test_h1047r_does_not_include_e545k_assertions(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        """Critical: variant-level constraint must NOT mix up same-gene variants."""
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        ann_h1047r = backend.annotate("PIK3CA", "H1047R")
        ann_e545k = backend.annotate("PIK3CA", "E545K")

        # They should have different AMP categories (Level A vs Level B)
        assert ann_h1047r.CIViC_AMP_Category != ann_e545k.CIViC_AMP_Category

    def test_no_match_returns_empty(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        ann = backend.annotate("TP53", "R175H")

        assert ann.CIViC_Match_Type == ""
        assert ann.CIViC_AMP_Category == ""

    def test_alias_matching(
        self, tiny_variant_tsv: Path, tiny_assertion_tsv: Path
    ):
        backend = TSVBackend(tiny_variant_tsv, tiny_assertion_tsv)
        ann = backend.annotate("PIK3CA", "HIS1047ARG")

        assert ann.CIViC_Match_Type == "alias"
        assert ann.CIViC_Variant_Name == "H1047R"


class TestVariantParsing:
    """Test p. prefix stripping and edge cases."""

    def test_strip_p_prefix(self):
        from isodde_bc_dify.civic.annotate import _strip_p_prefix

        assert _strip_p_prefix("p.H1047R") == "H1047R"
        assert _strip_p_prefix("H1047R") == "H1047R"
        assert _strip_p_prefix("p.") == ""
        assert _strip_p_prefix("") == ""
