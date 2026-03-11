"""Canonical data structures for CIViC annotation results.

All backends (TSV, GraphQL) must produce these structures so the annotator
logic remains backend-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CIViCVariantMatch:
    """A single matched CIViC variant."""

    variant_id: int
    gene: str
    variant_name: str
    molecular_profile_id: Optional[int] = None
    variant_aliases: str = ""


@dataclass
class CIViCAssertion:
    """One assertion row, already linked to a molecular profile."""

    molecular_profile_id: int
    molecular_profile: str = ""
    disease: str = ""
    therapies: str = ""
    assertion_type: str = ""
    assertion_direction: str = ""
    significance: str = ""
    amp_category: str = ""
    nccn_guideline: str = ""
    nccn_guideline_version: str = ""


@dataclass
class CIViCAnnotation:
    """Aggregated annotation to be appended to a MAF row."""

    CIViC_Variant_ID: str = ""
    CIViC_Variant_Name: str = ""
    CIViC_AMP_Category: str = ""
    CIViC_Clinical_Significance: str = ""
    CIViC_Drug_Associations: str = ""
    CIViC_Disease: str = ""
    CIViC_Assertion_Types: str = ""
    CIViC_Match_Type: str = ""  # "exact" | "alias" | "api" | "none"

    # Deprecated column kept for backwards compatibility
    CIViC_Evidence_Level: str = ""

    def as_dict(self) -> dict[str, str]:
        return {k: v for k, v in self.__dict__.items()}

    @staticmethod
    def empty() -> CIViCAnnotation:
        return CIViCAnnotation()

    @staticmethod
    def output_columns() -> list[str]:
        return list(CIViCAnnotation().__dict__.keys())
