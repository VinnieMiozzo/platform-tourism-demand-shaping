"""Eurostat tourism data pipeline.

Modules:
    config: Dataset definitions and project paths.
    ingest: Fetch raw JSON-stat payloads from the Eurostat API.
    clean:  Reshape raw payloads into long-format Parquet tables.
    logger: Logging configuration.
"""

__version__ = "0.1.0"

from platform_tourism.config import DATASETS, ENABLED_DATASETS
from platform_tourism.ingest import ingest_all

__all__ = ["ingest_all", "DATASETS", "ENABLED_DATASETS", "__version__"]
