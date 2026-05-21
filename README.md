# Platform Tourism Demand Shaping

## Business Problem

European short-stay platform tourism is highly seasonal. Destination marketing and accommodation portfolio teams need to understand where shoulder-season demand can plausibly be stimulated before allocating campaign, pricing, or market-development effort.

This project builds a staged decision framework:

1. **Country screening** — identify which European countries justify deeper analysis.
2. **Regional prioritization** — identify which regions inside shortlisted countries explain the opportunity.
3. **City investment scoring** — identify city-month combinations with enough demand, supply, and pricing opportunity to justify action.
4. **Final recommendation** — propose where campaign or pricing investment should be focused.

## Current Release

**Version:** `v0.2.0 — Country Screening Release`

This release answers:

> Which European countries justify deeper regional and city-level shoulder-season analysis?

The output is a country-level screening model. It does **not** allocate campaign budget directly.

## Recommendation

Prioritize the following markets for Phase 2 regional and city-level analysis:

1. Greece (`EL`)
2. France (`FR`)
3. Italy (`IT`)
4. Croatia (`HR`)
5. Spain (`ES`)

These markets rank highly for different reasons:

- `EL` and `HR`: strong summer concentration and visible shoulder-season gaps.
- `FR` and `ES`: very large absolute demand scale.
- `IT`: combination of demand scale and Mediterranean seasonality.

The shortlist should be interpreted as a **data-acquisition and follow-up priority**, not as a final campaign plan.

## Key Findings

- The platform-tourism panel is highly concentrated: France, Spain, and Italy dominate total demand.
- Mediterranean markets show the clearest summer concentration and therefore the clearest theoretical shoulder-season redistribution signal. Growth is broadly positive among large markets, so ranking differences at the top are mostly driven by scale and seasonality rather than growth.
- High-growth small markets such as Malta, Norway, and Sweden are watchlist candidates, not immediate investment priorities.
- Country-level aggregation hides destination-level variation, so Phase 2 must move to regional and city-level data.

## Data Sources

### Current source

Primary source:

- Eurostat collaborative-economy short-stay accommodation data.

Current analytical grain:

- Country-month.

Current primary metric:

- Platform tourism nights.

### Planned Phase 2 and Phase 3 sources

Future planned sources:

- Eurostat regional platform-tourism data.
- Eurostat traditional accommodation data.
- Inside Airbnb city-level listings, calendar, and review data.
- Manual regulation and market-feasibility inputs.

## Methodology

The Phase 1 country score combines three normalized components:

```text
country_score =
0.45 * demand_level
+ 0.30 * growth
+ 0.25 * seasonality_concentration
```

Where:

- `demand_level` is log-scaled mean annual platform nights.
- `growth` is recent growth versus the prior baseline.
- `seasonality_concentration` captures peak-season demand concentration.

The score is ordinal and directional. It ranks markets for follow-up investigation; it is not a causal estimate, forecast, or uplift model.

## Validation

The Phase 1 country shortlist is tested using:

- complete-year coverage checks;
- schema and null checks;
- sensitivity analysis under alternative scoring weights;
- interpretation of small-base growth outliers;
- component decomposition to verify why countries rank highly;
- explicit limitations around country-level aggregation.

## Repository Structure

```text
platform-tourism-demand-shaping/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── marts/
├── notebooks/
│   └── 02_country_screening.py
├── reports/
│   ├── business/
│   │   ├── country_screening_business.tex
│   │   └── output/
│   ├── technical/
│   │   ├── country_screening_methodology.qmd
│   │   └── output/
│   ├── figures/
│   └── tables/
├── sql/
│   ├── 00_schema.sql
│   ├── 01_staging.sql
│   ├── 02_marts_country.sql
│   ├── 03_kpis_country.sql
│   └── 99_validation.sql
├── src/
│   └── platform_tourism/
│       ├── config.py
│       ├── ingest.py
│       ├── clean.py
│       ├── marts.py
│       ├── visuals.py
│       ├── queries.py
│       └── utils.py
├── README.md
├── pyproject.toml
├── uv.lock
└── Makefile
```

## How to Reproduce

Install dependencies:

```bash
uv sync
```

Run the full pipeline:

```bash
uv run python main.py
```

Open the country-screening analysis notebook:

```bash
uv run marimo edit notebooks/02_country_screening.py
```

Render the technical methodology report:

```bash
quarto render reports/technical/country_screening_methodology.qmd
```

Compile the business report:

```bash
latexmk -pdf reports/business/country_screening_business.tex
```

## Outputs

| Output | Path | Audience |
|---|---|---|
| Business report | `reports/business/output/country_screening_business.pdf` | Strategy / marketing stakeholder |
| Technical methodology | `reports/technical/output/country_screening_methodology.html` | Technical reviewer / interviewer |
| Analysis notebook | `notebooks/02_country_screening.py` | Analyst / reviewer |
| Figures | `reports/figures/` | Report inputs |
| Marts | `data/marts/` | Analytical tables |

## Current Limitations

- Country-level analysis is a screening tool, not a deployment model.
- Marketing decisions happen at destination and month level.
- Eurostat platform data does not cover all short-stay rental channels.
- Supply, regulation, pricing flexibility, campaign cost, and historical response are not yet modeled.
- Growth rates from small bases can overstate commercial relevance.
- Regional and city-level heterogeneity is intentionally deferred to later releases.

## Scope Note

Phase 1 screens the full available European country panel. Phase 2 intentionally limits regional and city-level analysis to the top-ranked shortlisted countries (`EL`, `FR`, `IT`, `HR`, `ES`).

This is a deliberate release-scope decision. A full regional and city-level study across all European countries would require substantially broader data acquisition, validation, and local-market interpretation. For this portfolio release, the objective is to demonstrate a reproducible decision framework on a focused, high-signal subset rather than produce exhaustive European market coverage.

Countries outside the shortlist are not interpreted as having no opportunity. They are simply not prioritized for the next analytical pass under the current scoring assumptions and project scope.

## Next Release: `v0.3.0`

Phase 2 will move from country-level screening to regional prioritization.

Next decision:

> Which regions inside EL, FR, IT, HR, and ES deserve city-level data acquisition?

Planned additions:

- Eurostat NUTS regional platform-tourism data.
- Regional seasonality scoring.
- Regional contribution to national opportunity.
- Platform-versus-hotel comparison.
- Ranked regional shortlist for city-level analysis.

Planned regional score:

```text
region_score =
0.30 * regional_platform_scale
+ 0.20 * regional_growth
+ 0.25 * peak_to_shoulder_gap
+ 0.15 * share_of_country_platform_nights
+ 0.10 * platform_vs_hotel_gap
```

## Final Target

The final project will produce a city-month investment score:

```text
city_investment_score =
0.25 * demand_proxy
+ 0.20 * shoulder_gap
+ 0.20 * supply_readiness
+ 0.15 * price_opportunity
+ 0.10 * regional_alignment
+ 0.10 * validation_support
- risk_penalty
```

The final recommendation will answer:

> Which city-months should receive shoulder-season campaign or pricing investment?

## Version Roadmap

| Version | Scope | Main output |
|---|---|---|
| `v0.1.0` | Initial pipeline and exploratory analysis | Working data pipeline |
| `v0.2.0` | Country screening | Business PDF + technical Quarto methodology |
| `v0.3.0` | Regional prioritization | NUTS regional score and shortlist |
| `v0.4.0` | City investment scoring | City-month opportunity score |
| `v1.0.0` | Final recommendation | Deployable campaign/pricing plan |

