#!/usr/bin/env python
"""Initial bulk load script for OpenDiscourse.

Usage:
    # Load current congress (118)
    python scripts/initial_bulk_load.py --congress 118

    # Load specific source
    python scripts/initial_bulk_load.py --source congress.gov --congress 118

    # Load multiple congresses
    python scripts/initial_bulk_load.py --congress 117 118

    # Dry run (no DB writes)
    python scripts/initial_bulk_load.py --congress 118 --dry-run
"""

import argparse
import logging
import sys
import os

# Add project src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from opendiscourse.utils.logging_config import setup_logging
from opendiscourse.ingestion.congress_gov import CongressGovIngestion

logger = setup_logging()


def main():
    parser = argparse.ArgumentParser(description="OpenDiscourse initial bulk load")
    parser.add_argument(
        "--congress",
        type=int,
        nargs="+",
        default=[118],
        help="Congress number(s) to load (default: 118)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="congress.gov",
        choices=["congress.gov", "govinfo", "fec", "opensecrets"],
        help="Data source to load from",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be loaded without making changes",
    )
    parser.add_argument(
        "--bill-types",
        type=str,
        nargs="+",
        default=None,
        help="Specific bill types to load (hr, s, hjres, etc.). Default: all.",
    )
    args = parser.parse_args()

    if args.source == "congress.gov":
        for congress_num in args.congress:
            logger.info(f"{'[DRY RUN] ' if args.dry_run else ''}Loading Congress {congress_num}...")
            ingestor = CongressGovIngestion()

            try:
                if args.dry_run:
                    logger.info("DRY RUN - no changes will be made")
                    # Just show what endpoints would be hit
                    logger.info(f"  Would hit: /congress")
                    logger.info(f"  Would hit: /member (or /congress/{congress_num}/member)")
                    logger.info(f"  Would hit: /committee (or /committee/{congress_num})")
                    if args.bill_types:
                        for bt in args.bill_types:
                            logger.info(f"  Would hit: /bill/{congress_num}/{bt}")
                    else:
                        logger.info(f"  Would hit: /bill/{congress_num}")
                    logger.info(f"  Would hit: /vote/{congress_num}/senate")
                    logger.info(f"  Would hit: /vote/{congress_num}/house")
                else:
                    stats = ingestor.ingest(congress_number=congress_num)
                    logger.info(f"Congress {congress_num} stats: {stats}")
            except Exception as e:
                logger.error(f"Failed to load Congress {congress_num}: {e}")
                raise
            finally:
                ingestor.close()

    else:
        logger.warning(f"Source {args.source} not yet implemented")
        sys.exit(1)


if __name__ == "__main__":
    main()
