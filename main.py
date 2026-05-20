"""Run the pipeline end-to-end."""

import argparse

from platform_tourism.clean import clean_all
from platform_tourism.ingest import ingest_all
from platform_tourism.logger import setup_logging
from platform_tourism.marts import build_all_marts


def main() -> None:
    """Parse CLI args, configure logging, run the pipeline."""
    parser = argparse.ArgumentParser(description="Tourism data pipeline.")
    parser.add_argument(
        "--force", action="store_true", help="Re-download raw files even if they exist."
    )
    parser.add_argument(
        "--skip-ingest", action="store_true", help="Skip ingest; only run cleaning."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Set console log level to DEBUG."
    )
    args = parser.parse_args()

    setup_logging(console_level="DEBUG" if args.verbose else "INFO")

    if not args.skip_ingest:
        ingest_all(force=args.force)
    clean_all()
    build_all_marts()


if __name__ == "__main__":
    main()
