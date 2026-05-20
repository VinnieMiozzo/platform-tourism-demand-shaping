"""Fetch raw Eurostat datasets and persist them to ``RAW_DIR``."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from platform_tourism.config import (
    ENABLED_DATASETS,
    RAW_FILES,
    DatasetConfig,
)

logger = logging.getLogger(__name__)

EUROSTAT_BASE_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
)
REQUEST_TIMEOUT = 60  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds; doubled on each retry


def build_url(eurostat_code: str) -> str:
    """Build the JSON-stat URL for a Eurostat dataset.

    Args:
        eurostat_code: Eurostat dataset code, e.g. ``"tour_ce_omr"``.

    Returns:
        URL to the dataset's JSON-stat 2.0 representation.
    """
    return f"{EUROSTAT_BASE_URL}/{eurostat_code}?format=JSON&lang=EN"


def fetch_dataset(eurostat_code: str) -> dict[str, Any]:
    """Download a Eurostat dataset as JSON-stat, with retries.

    Retries on any network or HTTP error with exponential backoff
    (``RETRY_BACKOFF_BASE * 2**(attempt-1)`` seconds).

    Args:
        eurostat_code: Eurostat dataset code.

    Returns:
        Parsed JSON-stat payload.

    Raises:
        RuntimeError: If all retry attempts fail.
    """
    url = build_url(eurostat_code)
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug("GET %s (attempt %d/%d)", url, attempt, MAX_RETRIES)
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            if not payload:
                raise ValueError(f"Empty response for {eurostat_code}")
            logger.debug(
                "Received %d bytes for %s", len(response.content), eurostat_code
            )
            return payload
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                sleep = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "Fetch failed for %s (attempt %d/%d): %s — retrying in %ds",
                    eurostat_code,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    sleep,
                )
                time.sleep(sleep)

    raise RuntimeError(
        f"Failed to fetch {eurostat_code} after {MAX_RETRIES} attempts"
    ) from last_error


def save_raw(payload: dict[str, Any], destination: Path) -> None:
    """Write a JSON-stat payload atomically to disk.

    Writes to a ``.tmp`` sibling and then renames into place, so an
    interrupted run never leaves a corrupt half-file at ``destination``.

    Args:
        payload: JSON-stat payload to persist.
        destination: Final path of the file to write.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(destination)  # atomic on POSIX and Windows
    logger.info("Wrote %s (%.1f KB)", destination, destination.stat().st_size / 1024)


def ingest_dataset(key: str, cfg: DatasetConfig) -> Path:
    """Fetch one dataset and persist it under its configured raw filename.

    Args:
        key: Friendly key from ``DATASETS``.
        cfg: The matching ``DatasetConfig``.

    Returns:
        Path to the written file.
    """
    logger.info("Ingesting '%s' (Eurostat code: %s)", key, cfg["eurostat_code"])
    payload = fetch_dataset(cfg["eurostat_code"])
    destination = RAW_FILES[key]
    save_raw(payload, destination)
    return destination


def ingest_all(
    datasets: dict[str, DatasetConfig] | None = None,
    force: bool = False,
) -> dict[str, Path]:
    """Ingest every enabled dataset.

    Logs a per-dataset result and a summary at the end. Failures do
    not abort the run: each dataset is attempted independently and
    failures are reported in the summary.

    Args:
        datasets: Datasets to ingest. Defaults to ``ENABLED_DATASETS``.
        force: If False, skip datasets whose raw file already exists.

    Returns:
        Mapping ``{key: raw_path}`` of files written this run.
        Datasets that were skipped or failed are not in the result.
    """
    datasets = datasets if datasets is not None else ENABLED_DATASETS

    written: dict[str, Path] = {}
    skipped: list[str] = []
    failed: list[str] = []

    for key, cfg in datasets.items():
        destination = RAW_FILES[key]
        if destination.exists() and not force:
            logger.info(
                "Skip '%s' (exists at %s, use force=True to refresh)", key, destination
            )
            skipped.append(key)
            continue
        try:
            written[key] = ingest_dataset(key, cfg)
        except Exception as exc:
            logger.exception("Failed to ingest '%s': %s", key, exc)
            failed.append(key)

    logger.info(
        "Ingest complete: %d written, %d skipped, %d failed",
        len(written),
        len(skipped),
        len(failed),
    )
    if failed:
        logger.warning("Failed datasets: %s", ", ".join(failed))

    return written
