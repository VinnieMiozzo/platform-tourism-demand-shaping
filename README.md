# Shaping Shoulder-Season Demand in European Platform Tourism
## Business Problem
European destinations increasingly depend on short-stay accommodation booked through online platforms. Demand is highly seasonal, and peak-season growth does not automatically tell a destination marketing team where additional campaign budget should go.
This project identifies European countries and NUTS2 regions where platform-tourism demand shows strong shoulder-season opportunity: places with meaningful demand, improving growth, and underused months outside the summer peak.
## Stakeholder and Decision
**Stakeholder:** Destination marketing lead or accommodation portfolio strategy team.
**Decision:** Which European regions and months should receive shoulder-season marketing, promotion, or pricing attention over the next planning cycle?
**Decision sentence:**
> This analysis helps a destination marketing lead decide where and when to shift campaign spend by using Eurostat platform-tourism data to evaluate seasonality, demand growth, and shoulder-season opportunity across European destinations.

## Data Sources

All data is fetched from the Eurostat REST API in JSON-stat format. Country-level coverage; NUTS2 is a future extension.

| Dataset | Eurostat code | What it measures |
|---|---|---|
| Platform short-stay (monthly) | `tour_ce_omr` | Nights booked via collaborative-economy platforms, by month and resident origin (the centerpiece dataset) |
| Total nights (monthly) | `tin00171` | All accommodation nights, recent 12 months — used as the denominator for platform share |
| Hotel occupancy (monthly) | `tin00173` | Occupancy rate by bedplaces / bedrooms |
| Arrivals (annual) | `tin00174` | Tourist arrivals, 2013–2024 |
| Accommodation nights (annual) | `tin00175` | Nights spent, 2013–2024, by resident origin |
| Nights by accommodation type | `tin00177` | Hotels vs camping vs other short-stay |
| Capacity (annual) | `tin00181` | Establishments and bedplaces |

## Methodology

The pipeline is a classical raw → interim → marts data flow:

1. **Ingest** — JSON-stat is pulled from the Eurostat REST API and saved verbatim. One snapshot per dataset, atomic writes, retries on transient failure.
2. **Clean** — each raw payload is parsed to long-format Parquet: column names and cell values converted from labels to JSON-stat codes, timestamps parsed, aggregate (EU-27, Euro-area) and total rows flagged but preserved.
3. **Marts** *(in progress)* — wide analytical views built by joining and pivoting the long interim tables, one mart per analysis question.

The layered separation is deliberate. Re-running the analysis next year doesn't require redoing the cleaning; adding a new analytical view doesn't require re-ingesting. Each layer's outputs are durable inputs to the next.

## Running it

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd platform-tourism-demand-shaping
uv sync

# Full pipeline (ingest + clean)
uv run python main.py

# Re-clean only (fast inner loop while iterating)
uv run python main.py --skip-ingest

# Tests
uv run pytest

# Exploration notebook
uv run marimo edit notebooks/01_data_exploration.py
```

## Project Structure

```
platform-tourism-demand-shaping/
├── data/
│   ├── raw/eurostat/         JSON-stat snapshots from the API
│   ├── interim/              cleaned long-format Parquet
│   └── marts/                analysis-ready wide views (WIP)
├── notebooks/
│   └── 01_data_exploration.py
├── src/platform_tourism/
│   ├── config.py             dataset definitions, paths, helpers
│   ├── ingest.py             API fetch with retries + atomic writes
│   ├── clean.py              long-format cleaning pipeline
│   ├── logger.py             logging setup
│   └── marts.py              wide views (WIP)
├── tests/
│   ├── conftest.py
│   ├── test_clean.py         per-transform unit tests
│   └── test_config.py        config sanity tests
├── main.py                   pipeline orchestrator (CLI)
└── pyproject.toml
```

## Tech Stack

Python 3.12 · uv · pandas · pyarrow · pyjstat · marimo · pytest

## Status

- [x] Ingest pipeline with retries and atomic writes
- [x] Long-format cleaning with frequency-dispatched normalizers
- [x] Unit tests for transformations and config
- [ ] First mart: platform share of accommodation nights by country and month
- [ ] Analysis notebook with shoulder-season opportunity scoring
- [ ] CI (GitHub Actions)
