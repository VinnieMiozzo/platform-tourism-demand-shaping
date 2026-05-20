import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        r"""
        # 02 — Shoulder-Season Opportunity in European Platform Tourism

        **Decision supported.**  
        Which European countries and shoulder-season months should receive marketing
        or pricing attention in the next planning cycle?

        **Approach.**  
        Combine three signals — demand level, growth, and seasonality concentration —
        into a single opportunity ranking, then drill into the top candidates.

        **Notebook role.**  
        This notebook is the full analytical workspace. It contains both the business
        interpretation and the technical checks. The LaTeX report will be produced later
        from the exported figures and conclusions.
        """
    )
    return (mo,)


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import pandas as pd

    from platform_tourism.visuals import (
        build_heatmap_share,
        compute_weighted_score,
        detect_value_column,
        ensure_geo_column,
        export_all_figures,
        normalize_months,
        plot_country_monthly_curve,
        plot_growth_vs_demand,
        plot_opportunity_components,
        plot_opportunity_ranking,
        plot_seasonality_heatmap,
        plot_top_demand,
    )

    return (
        Path,
        build_heatmap_share,
        compute_weighted_score,
        detect_value_column,
        ensure_geo_column,
        export_all_figures,
        normalize_months,
        pd,
        plot_country_monthly_curve,
        plot_growth_vs_demand,
        plot_opportunity_ranking,
        plot_seasonality_heatmap,
        plot_top_demand,
    )


@app.cell
def _(Path):
    DATA_DIR = Path("data/marts")
    FIG_DIR = Path("reports/figures")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    COUNTRY_MONTH_PATH = DATA_DIR / "platform_country_month.parquet"
    COMPONENTS_PATH = DATA_DIR / "seasonality_components.parquet"

    COUNTRY_MONTH_PATH, COMPONENTS_PATH, FIG_DIR
    return COMPONENTS_PATH, COUNTRY_MONTH_PATH, FIG_DIR


@app.cell
def _(
    COMPONENTS_PATH,
    COUNTRY_MONTH_PATH,
    detect_value_column,
    ensure_geo_column,
    normalize_months,
    pd,
):
    country_month_raw = pd.read_parquet(COUNTRY_MONTH_PATH)
    components_raw = pd.read_parquet(COMPONENTS_PATH)

    components = ensure_geo_column(components_raw, geo_col="geo")
    country_month = ensure_geo_column(country_month_raw, geo_col="geo")
    country_month = normalize_months(country_month)

    VALUE_COL = detect_value_column(country_month)

    components.head()
    return VALUE_COL, components, country_month


@app.cell
def _(VALUE_COL, components, country_month, mo):
    n_countries = components["geo"].nunique()
    n_rows_long = len(country_month)
    years = sorted(country_month["year"].dropna().unique())
    min_year = int(min(years))
    max_year = int(max(years))

    mo.md(
        f"""
        ## Coverage

        - Countries: **{n_countries:,}**
        - Years: **{min_year}–{max_year}**
        - Rows in long country-month mart: **{n_rows_long:,}**
        - Detected demand column: `{VALUE_COL}`
        """
    )
    return


@app.cell
def _(VALUE_COL, components, country_month, pd):
    technical_checks = {
        "country_month_rows": len(country_month),
        "country_month_columns": country_month.shape[1],
        "components_rows": len(components),
        "components_columns": components.shape[1],
        "countries_in_country_month": country_month["geo"].nunique(),
        "countries_in_components": components["geo"].nunique(),
        "missing_geo_country_month": country_month["geo"].isna().sum(),
        "missing_geo_components": components["geo"].isna().sum(),
        "missing_value_rows": country_month[VALUE_COL].isna().sum(),
    }

    pd.DataFrame.from_dict(
        technical_checks,
        orient="index",
        columns=["value"],
    )
    return


@app.cell(hide_code=True)
def _(components, mo):
    top_n = mo.ui.slider(
        start=5,
        stop=25,
        step=1,
        value=15,
        label="Countries shown",
    )

    weight_level = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=0.45,
        label="Weight: demand level",
    )

    weight_growth = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=0.30,
        label="Weight: growth",
    )

    weight_seasonality = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=0.25,
        label="Weight: seasonality / shoulder opportunity",
    )

    country_select = mo.ui.dropdown(
        options=components["geo"].astype(str).sort_values().tolist(),
        value=components["geo"].astype(str).iloc[0],
        label="Country deep-dive",
    )

    mo.vstack(
        [
            mo.md("## Scenario controls"),
            mo.hstack([top_n, country_select]),
            mo.hstack([weight_level, weight_growth, weight_seasonality]),
        ]
    )
    return (
        country_select,
        top_n,
        weight_growth,
        weight_level,
        weight_seasonality,
    )


@app.cell
def _(
    components,
    compute_weighted_score,
    weight_growth,
    weight_level,
    weight_seasonality,
):
    components_scored = compute_weighted_score(
        components,
        demand_col="mean_annual_nights",
        growth_col="yoy_growth_pct",
        weight_level=weight_level.value,
        weight_growth=weight_growth.value,
        weight_seasonality=weight_seasonality.value,
        geo_col="geo",
    )

    components_scored.head(10)
    return (components_scored,)


@app.cell(hide_code=True)
def _(mo, weight_growth, weight_level, weight_seasonality):
    mo.md(
        f"""
        ## Technical note — opportunity score

        The score is a weighted composite of three normalized components:

        1. **Demand level**  
           Based on `mean_annual_nights`, log-scaled before min-max normalization.

        2. **Growth**  
           Based on `yoy_growth_pct`, min-max normalized.

        3. **Seasonality opportunity**  
           Based on the available seasonality concentration field, usually `peak_share`
           when present.

        Current weights:

        - Demand level: **{weight_level.value:.2f}**
        - Growth: **{weight_growth.value:.2f}**
        - Seasonality: **{weight_seasonality.value:.2f}**

        The score is directional. It is designed to rank markets for further review,
        not to estimate causal impact.
        """
    )
    return


@app.cell
def _(VALUE_COL, build_heatmap_share, components_scored, country_month, top_n):
    latest_year = int(country_month["year"].max())

    heatmap_share = build_heatmap_share(
        country_month=country_month,
        components=components_scored,
        latest_year=latest_year,
        top_n=top_n.value,
        value_col=VALUE_COL,
        demand_col="mean_annual_nights",
        geo_col="geo",
    )

    heatmap_share
    return heatmap_share, latest_year


@app.cell(hide_code=True)
def _(mo, top_n):
    mo.md(
        f"""
        # Business analysis

        ## 1. Demand landscape — where scale matters

        The first filter is absolute demand. Campaigns, pricing actions, and operational
        focus matter more in countries where the platform already has meaningful volume.

        The chart below shows the top **{top_n.value}** markets by recent annualized
        platform nights.
        """
    )
    return


@app.cell
def _(FIG_DIR, components_scored, plot_top_demand, top_n):
    fig_top_demand = plot_top_demand(
        components_scored,
        n=top_n.value,
        demand_col="mean_annual_nights",
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_top_demand
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(f"""
    ## 2. Seasonality — when demand is concentrated

    The heatmap normalizes each country to its own annual total. This means the
    colors show **within-year shape**, not absolute market size.

    A country with strong summer concentration may offer clearer shoulder-season
    upside, especially if April–May or September–October remain below summer levels
    but above the winter trough.
    """)
    return


@app.cell
def _(FIG_DIR, heatmap_share, latest_year, plot_seasonality_heatmap):
    fig_seasonality = plot_seasonality_heatmap(
        heatmap_share,
        latest_year=latest_year,
        output_dir=FIG_DIR,
    )

    fig_seasonality
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. Growth versus demand level — where the market is expanding

    This view separates large but mature markets from countries that are both
    meaningful and expanding.

    The most attractive quadrant is usually:

    - higher demand scale;
    - above-median growth;
    - visible seasonality opportunity.
    """)
    return


@app.cell
def _(FIG_DIR, components_scored, plot_growth_vs_demand):
    fig_growth = plot_growth_vs_demand(
        components_scored,
        n_labels=10,
        demand_col="mean_annual_nights",
        growth_col="yoy_growth_pct",
        score_col="weighted_score",
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_growth
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4. Composite opportunity ranking

    The ranking combines the three signals into one prioritization view.

    This is not meant to replace judgment. It is meant to make the prioritization
    discussion explicit: changing the weights changes the ranking.
    """)
    return


@app.cell
def _(FIG_DIR, components_scored, plot_opportunity_ranking, top_n):
    fig_ranking = plot_opportunity_ranking(
        components_scored,
        n=top_n.value,
        score_col="weighted_score",
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_ranking
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 5. Why the top opportunities rank highly

    The score decomposition helps explain whether a country ranks highly because it is:

    - already large;
    - growing quickly;
    - seasonally concentrated;
    - or a balanced combination of all three.
    """)
    return


@app.cell
def _(
    FIG_DIR,
    VALUE_COL,
    country_month,
    country_select,
    plot_country_monthly_curve,
):
    fig_country_curve = plot_country_monthly_curve(
        country_month,
        country=country_select.value,
        value_col=VALUE_COL,
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_country_curve
    return


@app.cell
def _(country_month, pd):
    schema_country_month = pd.DataFrame(
        {
            "column": country_month.columns,
            "dtype": [str(country_month[col].dtype) for col in country_month.columns],
            "missing_rows": [country_month[col].isna().sum() for col in country_month.columns],
            "missing_pct": [
                country_month[col].isna().mean()
                for col in country_month.columns
            ],
        }
    )

    schema_country_month
    return


@app.cell
def _(components_scored, pd):
    schema_components = pd.DataFrame(
        {
            "column": components_scored.columns,
            "dtype": [str(components_scored[col].dtype) for col in components_scored.columns],
            "missing_rows": [components_scored[col].isna().sum() for col in components_scored.columns],
            "missing_pct": [
                components_scored[col].isna().mean()
                for col in components_scored.columns
            ],
        }
    )

    schema_components
    return


@app.cell
def _(components_scored, top_n):
    ranking_cols = [
        "geo",
        "mean_annual_nights",
        "yoy_growth_pct",
        "peak_share",
        "shoulder_share",
        "off_share",
        "level_component",
        "growth_component",
        "seasonality_component",
        "weighted_score",
    ]

    available_ranking_cols = [
        col for col in ranking_cols if col in components_scored.columns
    ]

    ranking_table = (
        components_scored
        .head(top_n.value)
        [available_ranking_cols]
        .copy()
    )

    ranking_table
    return


@app.cell
def _(components, compute_weighted_score, pd):
    weight_scenarios = {
        "balanced": (0.40, 0.30, 0.30),
        "scale_led": (0.60, 0.25, 0.15),
        "growth_led": (0.25, 0.55, 0.20),
        "seasonality_led": (0.25, 0.25, 0.50),
    }

    scenario_tables = []

    for scenario_name, weights in weight_scenarios.items():
        w_level, w_growth, w_seasonality = weights

        scenario_df = compute_weighted_score(
            components,
            demand_col="mean_annual_nights",
            growth_col="yoy_growth_pct",
            weight_level=w_level,
            weight_growth=w_growth,
            weight_seasonality=w_seasonality,
            geo_col="geo",
        )

        scenario_table = (
            scenario_df
            .head(10)
            [["geo", "weighted_score"]]
            .assign(
                scenario=scenario_name,
                rank=lambda df: range(1, len(df) + 1),
            )
        )

        scenario_tables.append(scenario_table)

    sensitivity_table = pd.concat(scenario_tables, ignore_index=True)

    sensitivity_table
    return (sensitivity_table,)


@app.cell
def _(sensitivity_table):
    sensitivity_pivot = (
        sensitivity_table
        .pivot_table(
            index="geo",
            columns="scenario",
            values="rank",
            aggfunc="min",
        )
        .sort_values("balanced")
    )

    sensitivity_pivot
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Caveats and interpretation rules

    ## Business caveats

    - A high opportunity score does not mean guaranteed campaign impact.
    - Large markets may dominate because scale is commercially important.
    - Strong summer concentration can indicate opportunity, but also structural
      seasonality that may be hard to change.

    ## Technical caveats

    - The score is sensitive to weighting choices.
    - Growth depends on the selected baseline period.
    - Row-normalized heatmaps show timing, not absolute demand.
    - Countries with low absolute volume can show high growth from a small base.
    - The model ranks markets; it does not estimate causal uplift.

    ## Recommended usage

    Use the ranking to shortlist countries. Then validate the top candidates with:

    - campaign cost;
    - pricing flexibility;
    - supply availability;
    - local market context;
    - operational constraints;
    - historical campaign response, if available.
    """)
    return


@app.cell
def _(
    FIG_DIR,
    components_scored,
    country_month,
    country_select,
    export_all_figures,
    heatmap_share,
    latest_year,
    mo,
    top_n,
):
    export_all_figures(
        components=components_scored,
        country_month=country_month,
        selected_country=country_select.value,
        heatmap_share=heatmap_share,
        latest_year=latest_year,
        top_n=top_n.value,
        output_dir=FIG_DIR,
    )

    mo.md(
        f"""
        # Export complete

        Figures saved to:

        ```text
        {FIG_DIR}
        ```

        Use the `.pdf` files later in LaTeX.

        Suggested report split:

        - **Business report:** charts, ranking, interpretation, recommendations.
        - **Technical appendix:** metric definitions, scoring formula, sensitivity,
          caveats, and data quality checks.
        """
    )
    return


app._unparsable_cell(
    r"""
    |
    """,
    name="_"
)


if __name__ == "__main__":
    app.run()
