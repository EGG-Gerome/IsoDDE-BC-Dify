"""Offline TSV backend: reads nightly CIViC dump files and builds in-memory
indexes for fast variant-level annotation.

Key design decisions:
- Variant matching uses ``single_variant_molecular_profile_id`` →
  ``molecular_profile_id`` join so assertions are scoped to the *exact*
  variant, not the whole gene.
- Indexes are built once (``load_civic_data``) and reused across all MAF
  rows.  Complexity per row is O(1) dict lookup + small assertion list scan.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from ..schemas import CIViCAnnotation, CIViCAssertion, CIViCVariantMatch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Index structures
# ---------------------------------------------------------------------------

# gene (lower) -> list[dict]   (raw variant rows)
GeneVariantIndex = dict[str, list[dict]]

# molecular_profile_id (int) -> list[CIViCAssertion]
MolProfileAssertionIndex = dict[int, list[CIViCAssertion]]


def _read_tsv(path: Path) -> list[dict]:
    """Read a TSV file and return list of row dicts.
    
    Handles rows with fewer fields than header gracefully.
    """
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


def build_variant_index(variant_rows: list[dict]) -> GeneVariantIndex:
    """Bucket variant rows by lowercased ``feature_name`` (gene symbol)."""
    idx: GeneVariantIndex = {}
    for row in variant_rows:
        gene = (row.get("feature_name") or "").strip().lower()
        if gene:
            idx.setdefault(gene, []).append(row)
    return idx


def build_assertion_index(assertion_rows: list[dict]) -> MolProfileAssertionIndex:
    """Bucket assertions by ``molecular_profile_id``."""
    idx: MolProfileAssertionIndex = {}
    for row in assertion_rows:
        raw_id = (row.get("molecular_profile_id") or "").strip()
        if not raw_id:
            continue
        try:
            mp_id = int(raw_id)
        except ValueError:
            continue
        assertion = CIViCAssertion(
            molecular_profile_id=mp_id,
            molecular_profile=row.get("molecular_profile", ""),
            disease=row.get("disease", ""),
            therapies=row.get("therapies", ""),
            assertion_type=row.get("assertion_type", ""),
            assertion_direction=row.get("assertion_direction", ""),
            significance=row.get("significance", ""),
            amp_category=row.get("amp_category", ""),
            nccn_guideline=row.get("nccn_guideline", ""),
            nccn_guideline_version=row.get("nccn_guideline_version", ""),
        )
        idx.setdefault(mp_id, []).append(assertion)
    return idx


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------

class TSVBackend:
    """Holds the in-memory indexes and performs annotation lookups."""

    def __init__(self, variant_tsv: Path, assertion_tsv: Path) -> None:
        logger.info("Loading CIViC TSV data …")

        if not variant_tsv.exists():
            raise FileNotFoundError(f"Variant TSV not found: {variant_tsv}")
        if not assertion_tsv.exists():
            raise FileNotFoundError(f"Assertion TSV not found: {assertion_tsv}")

        variant_rows = _read_tsv(variant_tsv)
        assertion_rows = _read_tsv(assertion_tsv)

        self.variant_index = build_variant_index(variant_rows)
        self.assertion_index = build_assertion_index(assertion_rows)

        logger.info(
            "CIViC TSV loaded: %d variants, %d assertions, %d genes indexed",
            len(variant_rows),
            len(assertion_rows),
            len(self.variant_index),
        )

    # ----- variant matching ------------------------------------------------

    def _find_variant(
        self, gene: str, variant_name: str
    ) -> Optional[tuple[CIViCVariantMatch, str]]:
        """Try to match (gene, variant_name) in the variant index.

        Returns ``(match, match_type)`` or ``None``.
        ``match_type`` is ``"exact"`` or ``"alias"``.
        """
        bucket = self.variant_index.get(gene.lower(), [])
        if not bucket:
            return None

        # Pass 1: exact match on ``variant`` column
        for row in bucket:
            var_col = (row.get("variant") or "").strip()
            if var_col.lower() == variant_name.lower():
                return self._row_to_match(row), "exact"

        # Pass 2: substring check in ``variant_aliases``
        for row in bucket:
            aliases = (row.get("variant_aliases") or "").lower()
            if variant_name.lower() in aliases:
                return self._row_to_match(row), "alias"

        # Pass 3: loose substring in variant column (e.g. "V600E" in "V600E/K")
        for row in bucket:
            var_col = (row.get("variant") or "").strip()
            if variant_name.lower() in var_col.lower():
                return self._row_to_match(row), "exact"

        return None

    @staticmethod
    def _row_to_match(row: dict) -> CIViCVariantMatch:
        mp_id_raw = (row.get("single_variant_molecular_profile_id") or "").strip()
        mp_id = int(mp_id_raw) if mp_id_raw else None
        vid_raw = (row.get("variant_id") or "").strip()
        vid = int(vid_raw) if vid_raw else 0
        return CIViCVariantMatch(
            variant_id=vid,
            gene=row.get("feature_name", ""),
            variant_name=row.get("variant", ""),
            molecular_profile_id=mp_id,
            variant_aliases=row.get("variant_aliases", ""),
        )

    # ----- annotation entry point ------------------------------------------

    def annotate(self, gene: str, variant_name: str) -> CIViCAnnotation:
        """Return a ``CIViCAnnotation`` for the given (gene, variant) pair."""
        result = self._find_variant(gene, variant_name)
        if result is None:
            return CIViCAnnotation.empty()

        match, match_type = result
        ann = CIViCAnnotation(
            CIViC_Variant_ID=str(match.variant_id),
            CIViC_Variant_Name=match.variant_name,
            CIViC_Match_Type=match_type,
        )

        if match.molecular_profile_id is None:
            return ann

        assertions = self.assertion_index.get(match.molecular_profile_id, [])
        amp_cats: list[str] = []
        significances: list[str] = []
        drugs: list[str] = []
        diseases: list[str] = []
        atypes: list[str] = []

        for a in assertions:
            if a.amp_category:
                amp_cats.append(a.amp_category)
            if a.significance:
                significances.append(a.significance)
            if a.therapies:
                drugs.extend(t.strip() for t in a.therapies.split(",") if t.strip())
            if a.disease:
                diseases.append(a.disease)
            if a.assertion_type:
                atypes.append(a.assertion_type)

        ann.CIViC_AMP_Category = "; ".join(sorted(set(amp_cats)))
        ann.CIViC_Clinical_Significance = "; ".join(sorted(set(significances)))
        ann.CIViC_Drug_Associations = "; ".join(sorted(set(drugs)))
        ann.CIViC_Disease = "; ".join(sorted(set(diseases)))
        ann.CIViC_Assertion_Types = "; ".join(sorted(set(atypes)))
        # backwards compat alias
        ann.CIViC_Evidence_Level = ann.CIViC_AMP_Category

        return ann
