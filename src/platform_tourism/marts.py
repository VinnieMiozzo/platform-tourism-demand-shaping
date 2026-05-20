"""Build analysis-ready wide views from interim cleaned data.

Marts are the "presentation layer" of the data pipeline: they join,
filter, and pivot the long interim tables into shapes optimized for
specific analysis questions. Compared to ``interim``, marts are:

- **opinionated about filtering** (aggregates and totals removed)
- **shaped for the question** (typically wider, sometimes pivoted)
- **disposable** (rebuilding a mart is cheap; rebuilding interim is not)

Each ``build_*`` function returns a DataFrame; :func:`build_all_marts`
writes them all to ``data/marts/`` as Parquet.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from platform_tourism.config import DATASETS, INTERIM_FILES, MARTS_DIR

logger = logging.getLogger(__name__)

# Calendar definition of European tourism seasons. Standard in tourism
# literature: peak = high summer, shoulder = spring/autumn warm months,
# off = winter and early spring. Override per-country if needed in analysis.
PEAK_MONTHS: frozenset[int] = frozenset({6, 7, 8})
SHOULDER_MONTHS: frozenset[int] = frozenset({4, 5, 9, 10})
OFF_MONTHS: frozenset[int] = frozenset({1, 2, 3, 11, 12})


def _season_for(month: int) -> str:
    """Map a month number to a season label."""
    if month in PEAK_MONTHS:
        return "peak"
    if month in SHOULDER_MONTHS:
        return "shoulder"
    return "off"


def _nights_indicator_code() -> str:
    """Find the 'nights spent' indicator code from config."""
    indicators = DATASETS["platform_monthly"]["main_indicators"]
    # Match by friendly name (case-insensitive partial)
    for code, name in indicators.items():
        if "night" in name.lower():
            return code
    raise KeyError(f"No 'nights' indicator in main_indicators: {indicators}")


def _load_platform_filtered() -> pd.DataFrame:
    """Load platform_monthly interim, dropping geo aggregates and month-totals.

    Keeps ``c_resid=TOTAL`` rows so analysis can choose between the
    domestic/foreign breakdown and the pre-aggregated total. Callers must
    pick one to avoid double-counting.
    """
    df = pd.read_parquet(INTERIM_FILES["platform_monthly"])
    before = len(df)
    df = df[~df["is_aggregate"]]
    if "month_is_total" in df.columns:
        df = df[~df["month_is_total"]]
    # NOTE: c_resid_is_total deliberately NOT filtered — analysis chooses
    logger.info("platform_monthly: %d → %d rows after filtering", before, len(df))
    return df.reset_index(drop=True)


def build_platform_country_month() -> pd.DataFrame:
    """Country × month × indicator × residence grid of platform tourism.

    Long format. Use this as the input for any platform-tourism slice;
    ifilter to your chosen ``indic_to`` (e.g. ``"NS"`` for nights spent)
    and ``c_resid`` (``"TOTAL"`` for all visitors) at the analysis layer.

    Returns:
        DataFrame with columns ``geo``, ``time``, ``year``, ``month``,
        ``season``, ``indic_to``, ``c_resid``, ``nights``.
    """
    df = _load_platform_filtered().rename(columns={"value": "nights"})

    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["season"] = df["month"].map(_season_for)

    cols = ["geo", "time", "year", "month", "season", "indic_to", "c_resid", "nights"]
    out = df[cols].sort_values(["geo", "time", "indic_to", "c_resid"])
    return out.reset_index(drop=True)


def build_seasonality_components(
    indicator: str = "NGT_SP",
    c_resid: str = "TOTAL",
) -> pd.DataFrame:
    """Per-country components feeding the shoulder-season opportunity score.

    Computes raw signals only; combining them into a single score
    happens in the analysis notebook so the weighting is visible to
    reviewers.

    Columns produced:

    - ``mean_annual_nights``: average annual platform nights over the
      most recent three complete years; demand level.
    - ``yoy_growth_pct``: percentage change in average annual nights
      between the last two complete years and the prior two; trend.
    - ``peak_share`` / ``shoulder_share`` / ``off_share``: shares of
      annual nights falling in each season in the most recent complete
      year; seasonality structure.

    Args:
        indicator: Eurostat ``indic_to`` code to filter on. Defaults to
            ``"NS"`` (nights spent). Verify codes against
            ``config.DATASETS['platform_monthly']['main_indicators']``.
        c_resid: Eurostat ``c_resid`` code to filter on. Defaults to
            ``"TOTAL"`` (all visitors).

    Returns:
        DataFrame indexed by ``geo``, one row per country.
    """
    df = build_platform_country_month()
    df = df[(df["indic_to"] == indicator) & (df["c_resid"] == c_resid)]

    if indicator is None:
        indicator = _nights_indicator_code()

    if df.empty:
        raise ValueError(
            f"No rows after filtering indic_to={indicator!r} c_resid={c_resid!r}. "
            f"Check the codes in your data."
        )

    # Drop years that don't have 12 months of data (e.g. partial current year)
    months_per_year = df.groupby("year")["month"].nunique()
    complete_years = sorted(months_per_year[months_per_year == 12].index)
    if not complete_years:
        raise ValueError("No complete years found in platform_monthly.")
    df = df[df["year"].isin(complete_years)]
    logger.info("Using complete years: %s", complete_years)

    # Demand level: average annual nights over the most recent 3 years
    recent_3 = complete_years[-3:]
    level = (
        df[df["year"].isin(recent_3)]
        .groupby(["geo", "year"])["nights"]
        .sum()
        .groupby("geo")
        .mean()
        .rename("mean_annual_nights")
    )

    # Growth: last 2 complete years vs the prior 2
    if len(complete_years) >= 4:
        last2 = complete_years[-2:]
        prior2 = complete_years[-4:-2]
        last_avg = (
            df[df["year"].isin(last2)]
            .groupby(["geo", "year"])["nights"]
            .sum()
            .groupby("geo")
            .mean()
        )
        prior_avg = (
            df[df["year"].isin(prior2)]
            .groupby(["geo", "year"])["nights"]
            .sum()
            .groupby("geo")
            .mean()
        )
        growth = ((last_avg - prior_avg) / prior_avg * 100).rename("yoy_growth_pct")
    else:
        growth = pd.Series(name="yoy_growth_pct", dtype="float64")

    # Seasonality shares: most recent complete year
    last_year = complete_years[-1]
    shares = (
        df[df["year"] == last_year]
        .groupby(["geo", "season"])["nights"]
        .sum()
        .unstack(fill_value=0)
    )
    # Ensure all three season columns exist even if some are zero everywhere
    for s in ("peak", "shoulder", "off"):
        if s not in shares.columns:
            shares[s] = 0
    totals = shares.sum(axis=1)
    shares = shares.div(totals.where(totals != 0), axis=0)
    shares.columns = [f"{c}_share" for c in shares.columns]

    out = pd.concat(
        [level, growth, shares[["peak_share", "shoulder_share", "off_share"]]], axis=1
    )
    return out.dropna(subset=["mean_annual_nights"])


def build_all_marts(out_dir: Path = MARTS_DIR) -> dict[str, Path]:
    """Build every mart and write to ``out_dir``.

    Args:
        out_dir: Destination directory; created if missing.

    Returns:
        Mapping ``{mart_name: path}`` of Parquet files written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    cm = build_platform_country_month()
    p = out_dir / "platform_country_month.parquet"
    cm.to_parquet(p, index=False)
    logger.info("Wrote %s (%d rows)", p.name, len(cm))
    written["platform_country_month"] = p

    sc = build_seasonality_components()
    p = out_dir / "seasonality_components.parquet"
    sc.reset_index().to_parquet(p, index=False)
    logger.info("Wrote %s (%d countries)", p.name, len(sc))
    written["seasonality_components"] = p

    return written


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    build_all_marts()
