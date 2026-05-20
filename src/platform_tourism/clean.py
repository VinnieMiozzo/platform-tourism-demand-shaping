"""Clean raw Eurostat JSON-stat into long-format Parquet files.

The cleaning step turns one raw JSON-stat payload at
``data/raw/eurostat/<code>.json`` into one long-format Parquet table at
``data/interim/<key>.parquet`` per dataset.

Pipeline (in order):

1. Load JSON-stat (column names already become JSON-stat codes via pyjstat
   rename in :func:`load_raw`).
2. Convert dimension *cell values* from labels to codes
   (:func:`labels_to_codes`).
3. Parse the ``time`` column to ``pd.Timestamp``; dispatched on
   ``cfg["frequency"]`` (annual / monthly / annual_by_month).
4. Drop rows where ``value`` is null (Eurostat's ``:`` becomes NaN).
5. Flag aggregate geo rows (``EU27_2020``, ``EA19``, ...) as
   ``is_aggregate``.
6. Flag per-dimension ``TOTAL`` rows as ``<dim>_is_total``.
7. Apply per-dataset custom column renames (e.g. ``accomunit`` ambiguity
   between hotel_occupancy_monthly and capacity_establishments_bedplaces).
8. Write Parquet to ``data/interim/<key>.parquet``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Callable

import pandas as pd
from pyjstat import pyjstat

from platform_tourism.config import (
    DATASETS,
    INTERIM_DIR,
    RAW_FILES,
    DatasetConfig,
)

logger = logging.getLogger(__name__)

# Codes Eurostat uses for synthetic "all categories" rows. Most datasets use
# "TOTAL"; a few use shorter variants. Detection is case-sensitive.
TOTAL_CODES: frozenset[str] = frozenset({"TOTAL", "TOT", "_T", "T"})

# Aggregate geo codes: anything starting with EU (EU27_2020, EU28, ...) or
# EA (EA19, EA20, EA21). Country ISO codes never use these prefixes.
AGGREGATE_GEO_PREFIXES: tuple[str, ...] = ("EU", "EA")

# Per-dataset column renames applied last. The ``accomunit`` column means
# different things in different datasets (Bedplaces/Bedrooms in occupancy vs
# Establishments/Bedplaces in capacity); renaming prevents silent mixing if
# datasets are ever stacked.
COLUMN_RENAMES: dict[str, dict[str, str]] = {
    "hotel_occupancy_monthly": {"accomunit": "occupancy_denominator"},
    "capacity_establishments_bedplaces": {"accomunit": "capacity_unit"},
}


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_raw(raw_path: Path) -> tuple[dict, pd.DataFrame]:
    """Load a raw JSON-stat file as ``(payload, df)``.

    Column names are renamed from pyjstat's verbose labels back to the
    JSON-stat dimension codes (``geo``, ``time``, ...). Cell values
    remain as labels at this stage; :func:`labels_to_codes` converts
    those separately so each step is independently testable.

    Args:
        raw_path: Path to a Eurostat JSON-stat file on disk.

    Returns:
        Tuple ``(payload, df)``. ``payload`` is the raw dict (needed
        downstream for label↔code lookups); ``df`` is the long-format
        DataFrame with coded column names and label-valued cells.
    """
    raw_text = raw_path.read_text(encoding="utf-8")
    payload = json.loads(raw_text)
    label_to_code_columns = {
        payload["dimension"][code].get("label", code): code for code in payload["id"]
    }
    df = (
        pyjstat.Dataset.read(raw_text)
        .write("dataframe")
        .rename(columns=label_to_code_columns)
    )
    return payload, df


# ---------------------------------------------------------------------------
# Universal transformations
# ---------------------------------------------------------------------------


def labels_to_codes(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Convert dimension cell values from labels to JSON-stat codes.

    pyjstat returns dimension values as labels (``"Belgium"``,
    ``"Domestic country"``). For joins and code-based filtering, codes
    are preferable. This inverts each dimension's
    ``category.label`` mapping and applies it column-wise.

    Args:
        df: DataFrame with coded column names but label-valued cells.
        payload: JSON-stat payload providing label→code lookups.

    Returns:
        DataFrame with both column names and cell values as codes.
    """
    df = df.copy()
    for dim in payload["id"]:
        if dim not in df.columns:
            continue
        labels = payload["dimension"][dim]["category"].get("label", {})
        label_to_code = {label: code for code, label in labels.items()}
        # Unmapped values are kept as-is (shouldn't happen if pyjstat and
        # Eurostat agree, but stays robust if they don't).
        df[dim] = df[dim].map(lambda v: label_to_code.get(v, v))
    return df


def parse_time_annual(df: pd.DataFrame) -> pd.DataFrame:
    """Parse a ``YYYY`` time column to pd.Timestamp (Jan 1 of each year).

    Args:
        df: DataFrame with a string ``time`` column like ``"2024"``.

    Returns:
        DataFrame with ``time`` as ``pd.Timestamp``.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], format="%Y")
    return df


def parse_time_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Parse a ``YYYY-MM`` time column to pd.Timestamp (first day of month).

    Args:
        df: DataFrame with a string ``time`` column like ``"2025-04"``.

    Returns:
        DataFrame with ``time`` as ``pd.Timestamp``.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], format="%Y-%m")
    return df


def parse_time_annual_by_month(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Combine year (``time``) + month (``month``) into a single timestamp.

    Used by the platform_monthly dataset, which encodes annual data with
    a separate ``month`` dimension (``M01`` … ``M12`` + ``TOTAL``).

    For monthly rows: ``time`` becomes the first day of the month.
    For ``month=TOTAL`` rows: ``time`` becomes Jan 1 of the year (these
    rows are flagged separately by :func:`flag_totals`, so the duplicate
    timestamp with the January row is distinguishable downstream).

    Args:
        df: DataFrame with ``time`` (year string) and ``month`` (code).
        payload: JSON-stat payload (currently unused but kept for
            signature symmetry with the other parsers).

    Returns:
        DataFrame with ``time`` as ``pd.Timestamp``.
    """
    del payload  # not needed for now
    df = df.copy()
    month_num = df["month"].str.extract(r"M(\d{2})")[0]
    is_month_row = month_num.notna()

    parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    # Per-month rows: combine year + zero-padded month
    parsed.loc[is_month_row] = pd.to_datetime(
        df.loc[is_month_row, "time"].astype(str)
        + "-"
        + month_num[is_month_row].astype(str)
        + "-01",
        format="%Y-%m-%d",
    )
    # TOTAL (or any non-Mnn) rows: just Jan 1 of the year
    parsed.loc[~is_month_row] = pd.to_datetime(
        df.loc[~is_month_row, "time"].astype(str), format="%Y"
    )

    df["time"] = parsed
    return df


def drop_null_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows whose ``value`` column is null.

    Eurostat encodes missing observations as ``:``, which pyjstat
    converts to NaN. Drop counts are logged for auditability.
    """
    before = len(df)
    df = df.dropna(subset=["value"])
    after = len(df)
    if before != after:
        logger.info(
            "  dropped %d null-value rows (%d -> %d)",
            before - after,
            before,
            after,
        )
    return df


def flag_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``is_aggregate`` column flagging EU/Euro-area geo rows.

    Aggregate codes start with ``EU`` (``EU27_2020``, ...) or ``EA``
    (``EA19``, ``EA20``, ``EA21``). These pre-sum multiple countries and
    would double-count if mixed with country-level rows.

    Args:
        df: DataFrame with a coded ``geo`` column (or no geo).

    Returns:
        DataFrame with a boolean ``is_aggregate`` column added.
    """
    df = df.copy()
    if "geo" in df.columns:
        df["is_aggregate"] = (
            df["geo"].astype(str).str.startswith(AGGREGATE_GEO_PREFIXES)
        )
    else:
        df["is_aggregate"] = False
    return df


def flag_totals(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Add ``<dim>_is_total`` columns for every dimension with a total level.

    Many Eurostat dimensions include a synthetic ``TOTAL`` level summing
    the others (e.g. ``c_resid=TOTAL`` is domestic + foreign). Flagging
    these explicitly lets downstream analysis avoid double-counting.

    Args:
        df: DataFrame with code-valued dimension columns.
        payload: JSON-stat payload (provides the dimension list).

    Returns:
        DataFrame with per-dimension ``_is_total`` columns added where
        such totals exist.
    """
    df = df.copy()
    for dim in payload["id"]:
        if dim == "time" or dim not in df.columns:
            continue
        is_total = df[dim].isin(TOTAL_CODES)
        if is_total.any():
            df[f"{dim}_is_total"] = is_total
    return df


def apply_custom_renames(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Apply per-dataset column renames (e.g. accomunit disambiguation).

    Also renames the matching ``<col>_is_total`` flag columns so the
    naming stays consistent after renaming a dimension.

    Args:
        df: DataFrame after all universal transforms.
        key: Dataset key (used to look up renames in ``COLUMN_RENAMES``).

    Returns:
        DataFrame with renames applied (or unchanged if none configured).
    """
    base_renames = COLUMN_RENAMES.get(key, {})
    if not base_renames:
        return df

    full_renames: dict[str, str] = {}
    for old, new in base_renames.items():
        full_renames[old] = new
        old_flag, new_flag = f"{old}_is_total", f"{new}_is_total"
        if old_flag in df.columns:
            full_renames[old_flag] = new_flag

    # Filter to only keys that actually exist (defensive)
    full_renames = {k: v for k, v in full_renames.items() if k in df.columns}
    if full_renames:
        df = df.rename(columns=full_renames)
        logger.info("  applied custom renames: %s", full_renames)
    return df


# ---------------------------------------------------------------------------
# Normalizers (frequency-specific time handling)
# ---------------------------------------------------------------------------


def normalize_annual(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Normalizer for ``frequency='annual'`` datasets."""
    del payload
    return parse_time_annual(df)


def normalize_monthly(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Normalizer for ``frequency='monthly'`` datasets."""
    del payload
    return parse_time_monthly(df)


def normalize_annual_by_month(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Normalizer for ``frequency='annual_by_month'`` (platform_monthly)."""
    return parse_time_annual_by_month(df, payload)


NORMALIZERS: dict[str, Callable[[pd.DataFrame, dict], pd.DataFrame]] = {
    "annual": normalize_annual,
    "monthly": normalize_monthly,
    "annual_by_month": normalize_annual_by_month,
}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _interim_path_for(key: str, cfg: DatasetConfig) -> Path:
    """Resolve the interim output path for a dataset, forcing .parquet."""
    path = INTERIM_DIR / cfg["interim_file"]
    if path.suffix != ".parquet":
        path = path.with_suffix(".parquet")
    return path


def clean_dataset(key: str, cfg: DatasetConfig) -> Path:
    """Clean one dataset and write its interim Parquet file.

    Args:
        key: Dataset key from ``DATASETS``.
        cfg: The matching ``DatasetConfig``.

    Returns:
        Path to the written interim file.

    Raises:
        FileNotFoundError: If the raw file is missing.
        KeyError: If ``cfg["frequency"]`` is unknown.
    """
    raw_path = RAW_FILES[key]
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file missing for {key}: {raw_path}")

    logger.info("Cleaning '%s' (%s)", key, raw_path.name)

    payload, df = load_raw(raw_path)
    logger.debug("  loaded %d rows, %d cols", df.shape[0], df.shape[1])

    df = labels_to_codes(df, payload)

    frequency = cfg["frequency"]
    if frequency not in NORMALIZERS:
        raise KeyError(
            f"No normalizer for frequency '{frequency}'. "
            f"Available: {sorted(NORMALIZERS)}"
        )
    df = NORMALIZERS[frequency](df, payload)

    df = drop_null_values(df)
    df = flag_aggregates(df)
    df = flag_totals(df, payload)
    df = apply_custom_renames(df, key)

    out_path = _interim_path_for(key, cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info(
        "  wrote %s (%d rows, %d cols)", out_path.name, df.shape[0], df.shape[1]
    )

    return out_path


def clean_all(
    datasets: dict[str, DatasetConfig] | None = None,
    respect_enabled: bool = True,
) -> dict[str, Path]:
    """Clean every enabled dataset and write interim Parquets.

    Mirrors :func:`platform_tourism.ingest.ingest_all`: defaults to
    every dataset in the config, filters by ``enabled`` flag unless
    explicitly overridden, continues past per-dataset failures.

    Args:
        datasets: Datasets to clean. Defaults to all of ``DATASETS``.
        respect_enabled: If True (default), skip ``enabled=False`` entries.

    Returns:
        Mapping ``{key: interim_path}`` for files written this run.
    """
    datasets = datasets if datasets is not None else DATASETS
    if respect_enabled:
        datasets = {k: v for k, v in datasets.items() if v["enabled"]}

    written: dict[str, Path] = {}
    failed: list[str] = []

    for key, cfg in datasets.items():
        try:
            written[key] = clean_dataset(key, cfg)
        except Exception as exc:
            logger.exception("Failed to clean '%s': %s", key, exc)
            failed.append(key)

    logger.info(
        "Clean complete: %d written, %d failed",
        len(written),
        len(failed),
    )
    if failed:
        logger.warning("Failed datasets: %s", ", ".join(failed))

    return written


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    clean_all()
