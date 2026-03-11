"""Online GraphQL backend: queries the CIViC public GraphQL API.

Features:
- Deduplicates (gene, variant) pairs to avoid redundant calls.
- Local JSONL cache so repeated runs don't re-query.
- Exponential back-off on 429 / 5xx errors.
- Maps API results into the same ``CIViCAnnotation`` schema as the TSV
  backend.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

import requests

from ..schemas import CIViCAnnotation

logger = logging.getLogger(__name__)

CIVIC_GRAPHQL_URL = "https://civicdb.org/api/graphql"

VARIANT_QUERY = """\
query VariantSearch($geneName: String!) {
  variants(
    geneNames: [$geneName]
    first: 50
  ) {
    edges {
      node {
        id
        name
        variantAliases
        singleVariantMolecularProfileId
        assertions(first: 50) {
          edges {
            node {
              significance
              assertionType
              ampLevel
              therapies {
                name
              }
              disease {
                name
              }
            }
          }
        }
      }
    }
  }
}
"""


class GraphQLBackend:
    """CIViC GraphQL backend with local cache and retry logic."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        sleep_seconds: float = 1.0,
        max_retries: int = 3,
    ) -> None:
        self.sleep_seconds = sleep_seconds
        self.max_retries = max_retries
        self._cache: dict[str, Any] = {}

        self._cache_path: Optional[Path] = None
        if cache_dir is not None:
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_path = cache_dir / "civic_graphql_cache.jsonl"
            self._load_cache()

    # ----- cache -----------------------------------------------------------

    def _cache_key(self, gene: str, variant: str) -> str:
        return f"{gene.upper()}||{variant.upper()}"

    def _load_cache(self) -> None:
        if self._cache_path and self._cache_path.exists():
            with open(self._cache_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    self._cache[entry["key"]] = entry["value"]
            logger.info("GraphQL cache loaded: %d entries", len(self._cache))

    def _save_cache_entry(self, key: str, value: Any) -> None:
        self._cache[key] = value
        if self._cache_path:
            with open(self._cache_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")

    # ----- API call --------------------------------------------------------

    def _query_api(self, gene: str) -> Optional[dict]:
        """Query CIViC GraphQL for all variants of a gene."""
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(
                    CIVIC_GRAPHQL_URL,
                    json={"query": VARIANT_QUERY, "variables": {"geneName": gene}},
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "errors" in data:
                        logger.warning("GraphQL errors for %s: %s", gene, data["errors"])
                        return None
                    return data
                if resp.status_code in (429, 500, 502, 503, 504):
                    wait = self.sleep_seconds * (2 ** (attempt - 1))
                    logger.warning(
                        "HTTP %d for %s, retrying in %.1fs (attempt %d/%d)",
                        resp.status_code, gene, wait, attempt, self.max_retries,
                    )
                    time.sleep(wait)
                    continue
                logger.error("HTTP %d for gene %s", resp.status_code, gene)
                return None
            except requests.RequestException as exc:
                logger.error("Request failed for %s: %s", gene, exc)
                if attempt < self.max_retries:
                    time.sleep(self.sleep_seconds * (2 ** (attempt - 1)))
                    continue
                return None
        return None

    # ----- annotation ------------------------------------------------------

    def annotate(self, gene: str, variant_name: str) -> CIViCAnnotation:
        """Return a CIViCAnnotation for the given (gene, variant)."""
        cache_key = self._cache_key(gene, variant_name)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return CIViCAnnotation(**cached)

        data = self._query_api(gene)
        time.sleep(self.sleep_seconds)

        if data is None:
            return CIViCAnnotation.empty()

        edges = (
            data.get("data", {})
            .get("variants", {})
            .get("edges", [])
        )

        matched_node = None
        match_type = "none"
        for edge in edges:
            node = edge.get("node", {})
            node_name = (node.get("name") or "").strip()
            if node_name.lower() == variant_name.lower():
                matched_node = node
                match_type = "exact"
                break
            aliases = node.get("variantAliases") or []
            if any(variant_name.lower() == a.lower() for a in aliases):
                matched_node = node
                match_type = "alias"
                break

        if matched_node is None:
            empty = CIViCAnnotation.empty()
            self._save_cache_entry(cache_key, empty.as_dict())
            return empty

        amp_cats: list[str] = []
        significances: list[str] = []
        drugs: list[str] = []
        diseases: list[str] = []
        atypes: list[str] = []

        assertion_edges = (
            matched_node.get("assertions", {}).get("edges", [])
        )
        for ae in assertion_edges:
            an = ae.get("node", {})
            if an.get("ampLevel"):
                amp_cats.append(an["ampLevel"])
            if an.get("significance"):
                significances.append(an["significance"])
            if an.get("assertionType"):
                atypes.append(an["assertionType"])
            if an.get("disease", {}) and an["disease"].get("name"):
                diseases.append(an["disease"]["name"])
            for therapy in an.get("therapies") or []:
                if therapy.get("name"):
                    drugs.append(therapy["name"])

        ann = CIViCAnnotation(
            CIViC_Variant_ID=str(matched_node.get("id", "")),
            CIViC_Variant_Name=matched_node.get("name", ""),
            CIViC_AMP_Category="; ".join(sorted(set(amp_cats))),
            CIViC_Clinical_Significance="; ".join(sorted(set(significances))),
            CIViC_Drug_Associations="; ".join(sorted(set(drugs))),
            CIViC_Disease="; ".join(sorted(set(diseases))),
            CIViC_Assertion_Types="; ".join(sorted(set(atypes))),
            CIViC_Match_Type=match_type,
            CIViC_Evidence_Level="; ".join(sorted(set(amp_cats))),
        )

        self._save_cache_entry(cache_key, ann.as_dict())
        return ann
