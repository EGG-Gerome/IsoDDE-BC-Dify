"""Command-line interface for IsoDDE-BC-Dify tools.

Usage examples::

    # TSV backend (default) -- uses nightly CIViC dump files
    python -m isodde_bc_dify.cli civic-annotate \\
        --input-maf data/cohortMAF.2026-03-10.maf \\
        --output-maf data/annotated_brca_maf.tsv

    # Override data file names
    python -m isodde_bc_dify.cli civic-annotate \\
        --input-maf data/cohortMAF.2026-03-10.maf \\
        --output-maf data/annotated_brca_maf.tsv \\
        --variant-tsv Variants.tsv \\
        --assertion-tsv Accepted_AID.tsv

    # GraphQL backend (queries CIViC API; slower but always up-to-date)
    python -m isodde_bc_dify.cli civic-annotate \\
        --input-maf data/cohortMAF.2026-03-10.maf \\
        --output-maf data/annotated_brca_maf.tsv \\
        --backend graphql \\
        --sleep-seconds 1.5
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def _resolve_data_dir(args_data_dir: str | None) -> Path:
    """Resolve the data directory from CLI arg or environment variable."""
    if args_data_dir:
        return Path(args_data_dir)
    env = os.environ.get("ISO_DDE_DATA_DIR")
    if env:
        return Path(env)
    return Path("data")


def cmd_civic_annotate(args: argparse.Namespace) -> None:
    """Entry point for the ``civic-annotate`` sub-command."""
    from .civic.annotate import annotate_maf
    from .civic.backends.graphql import GraphQLBackend
    from .civic.backends.tsv import TSVBackend

    data_dir = _resolve_data_dir(args.data_dir)
    input_maf = Path(args.input_maf)
    output_maf = Path(args.output_maf)

    if not input_maf.exists():
        logging.error("Input MAF not found: %s", input_maf)
        sys.exit(1)

    if args.backend == "tsv":
        variant_tsv = data_dir / args.variant_tsv
        assertion_tsv = data_dir / args.assertion_tsv
        backend = TSVBackend(variant_tsv=variant_tsv, assertion_tsv=assertion_tsv)
    else:
        cache_dir = data_dir / "cache"
        backend = GraphQLBackend(
            cache_dir=cache_dir,
            sleep_seconds=args.sleep_seconds,
        )

    annotate_maf(
        input_maf=input_maf,
        output_maf=output_maf,
        backend=backend,
        save_every=args.save_every,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="isodde",
        description="IsoDDE-BC-Dify CLI tools",
    )
    sub = parser.add_subparsers(dest="command")

    civic = sub.add_parser(
        "civic-annotate",
        help="Annotate a MAF file with CIViC variant / assertion data",
    )
    civic.add_argument("--input-maf", required=True, help="Path to input MAF/TSV file")
    civic.add_argument("--output-maf", required=True, help="Path for annotated output")
    civic.add_argument(
        "--data-dir",
        default=None,
        help="Directory containing CIViC TSV files (default: data/ or $ISO_DDE_DATA_DIR)",
    )
    civic.add_argument(
        "--variant-tsv",
        default="nightly-VariantSummaries.tsv",
        help="Filename of the variant summaries TSV inside --data-dir",
    )
    civic.add_argument(
        "--assertion-tsv",
        default="nightly-AcceptedAssertionSummaries.tsv",
        help="Filename of the assertion summaries TSV inside --data-dir",
    )
    civic.add_argument(
        "--backend",
        choices=["tsv", "graphql"],
        default="tsv",
        help="Annotation backend (default: tsv)",
    )
    civic.add_argument(
        "--sleep-seconds",
        type=float,
        default=1.0,
        help="Seconds between GraphQL API calls (default: 1.0)",
    )
    civic.add_argument(
        "--save-every",
        type=int,
        default=50,
        help="Save progress every N rows (default: 50)",
    )
    civic.set_defaults(func=cmd_civic_annotate)

    return parser


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
