import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    mo.md(
        r"""
        # 02 — Country Screening for Shoulder-Season Platform Tourism

        **Decision supported.**  
        Which European countries should be prioritized for regional and city-level
        shoulder-season investigation before campaign or pricing budget is allocated?

        **Release role.**  
        This notebook supports `v0.2.0 — Country Screening Release`.

        **Analytical role.**  
        This is the analytical source of truth for Phase 1. It loads the country-level
        marts, computes the opportunity score, validates ranking stability, exports
        figures, and produces the tables needed for the business report and technical
        methodology.

        **Important boundary.**  
        The country score is a screening tool. It identifies where deeper data acquisition
        is justified. It does not recommend direct campaign deployment.
        """
    )
    return (mo,)


@app.cell
def _():
    from pathlib import Path

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
        plot_opportunity_components,
        plot_opportunity_ranking,
        plot_seasonality_heatmap,
        plot_top_demand,
    )


@app.cell
def _(Path):
    DATA_DIR = Path("data/marts")
    FIG_DIR = Path("reports/figures")
    TABLE_DIR = Path("reports/tables")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    COUNTRY_MONTH_PATH = DATA_DIR / "platform_country_month.parquet"
    COMPONENTS_PATH = DATA_DIR / "seasonality_components.parquet"

    REPORT_TOP_N = 15
    REPORT_DEEP_DIVE_COUNTRY = "AT"

    DEFAULT_WEIGHT_LEVEL = 0.45
    DEFAULT_WEIGHT_GROWTH = 0.30
    DEFAULT_WEIGHT_SEASONALITY = 0.25

    COUNTRY_SHORTLIST = ["EL", "FR", "IT", "HR", "ES"]

    COUNTRY_MONTH_PATH, COMPONENTS_PATH, FIG_DIR, TABLE_DIR
    return (
        COMPONENTS_PATH,
        COUNTRY_MONTH_PATH,
        COUNTRY_SHORTLIST,
        DEFAULT_WEIGHT_GROWTH,
        DEFAULT_WEIGHT_LEVEL,
        DEFAULT_WEIGHT_SEASONALITY,
        FIG_DIR,
        REPORT_DEEP_DIVE_COUNTRY,
        REPORT_TOP_N,
        TABLE_DIR,
    )


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
def _(VALUE_COL, country_month):
    country_month_scoring = country_month.copy()

    if "is_aggregate" in country_month_scoring.columns:
        aggregate_mask = (
            country_month_scoring["is_aggregate"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        country_month_scoring = country_month_scoring.loc[~aggregate_mask]

    if "month_is_total" in country_month_scoring.columns:
        month_total_mask = (
            country_month_scoring["month_is_total"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        country_month_scoring = country_month_scoring.loc[~month_total_mask]

    if "indic_to" in country_month_scoring.columns:
        country_month_scoring = country_month_scoring.loc[
            country_month_scoring["indic_to"].astype(str).eq("NGT_SP")
        ]

    if "c_resid" in country_month_scoring.columns:
        country_month_scoring = country_month_scoring.loc[
            country_month_scoring["c_resid"].astype(str).eq("TOTAL")
        ]
    elif "c_resid_is_total" in country_month_scoring.columns:
        residence_total_mask = (
            country_month_scoring["c_resid_is_total"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        country_month_scoring = country_month_scoring.loc[residence_total_mask]

    country_month_scoring = country_month_scoring.dropna(
        subset=["geo", "year", "month", VALUE_COL]
    ).copy()

    country_month_scoring["year"] = country_month_scoring["year"].astype(int)
    country_month_scoring["month"] = country_month_scoring["month"].astype(int)

    country_month_scoring.head()
    return (country_month_scoring,)


@app.cell
def _(country_month_scoring, pd):
    country_year_months = (
        country_month_scoring.groupby(["geo", "year"], as_index=False)["month"]
        .nunique()
        .rename(columns={"month": "n_months"})
    )

    expected_country_count = country_month_scoring["geo"].nunique()

    countries_per_complete_year = (
        country_year_months.query("n_months == 12").groupby("year")["geo"].nunique()
    )

    complete_panel_years = (
        countries_per_complete_year[
            countries_per_complete_year == expected_country_count
        ]
        .index.astype(int)
        .tolist()
    )

    if complete_panel_years:
        latest_complete_year = max(complete_panel_years)
    else:
        complete_year_candidates = (
            country_year_months.query("n_months == 12")["year"]
            .astype(int)
            .unique()
            .tolist()
        )
        latest_complete_year = max(complete_year_candidates)

    pd.DataFrame(
        {
            "metric": [
                "Expected country count",
                "Complete panel years",
                "Latest complete year used for seasonality charts",
            ],
            "value": [
                expected_country_count,
                ", ".join(str(year) for year in complete_panel_years),
                latest_complete_year,
            ],
        }
    )
    return (
        complete_panel_years,
        country_year_months,
        expected_country_count,
        latest_complete_year,
    )


@app.cell(hide_code=True)
def _(
    VALUE_COL,
    components,
    country_month,
    country_month_scoring,
    latest_complete_year,
    mo,
):
    n_countries = components["geo"].nunique()
    n_rows_long = len(country_month)
    n_rows_scoring = len(country_month_scoring)
    years = sorted(country_month["year"].dropna().astype(int).unique())
    min_year = int(min(years))
    max_year = int(max(years))

    mo.md(
        f"""
        ## Coverage

        - Countries in component mart: **{n_countries:,}**
        - Years observed in country-month mart: **{min_year}–{max_year}**
        - Latest complete year used for seasonality charts: **{latest_complete_year}**
        - Rows in long country-month mart: **{n_rows_long:,}**
        - Rows after scoring filters: **{n_rows_scoring:,}**
        - Detected demand column: `{VALUE_COL}`

        The analysis uses complete-year logic for seasonality. This avoids treating
        a partial current year as a full annual demand pattern.
        """
    )
    return


@app.cell(hide_code=True)
def _(
    DEFAULT_WEIGHT_GROWTH,
    DEFAULT_WEIGHT_LEVEL,
    DEFAULT_WEIGHT_SEASONALITY,
    REPORT_DEEP_DIVE_COUNTRY,
    REPORT_TOP_N,
    components,
    mo,
):
    top_n = mo.ui.slider(
        start=5,
        stop=25,
        step=1,
        value=REPORT_TOP_N,
        label="Exploration: countries shown",
    )

    weight_level = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=DEFAULT_WEIGHT_LEVEL,
        label="Exploration weight: demand level",
    )

    weight_growth = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=DEFAULT_WEIGHT_GROWTH,
        label="Exploration weight: growth",
    )

    weight_seasonality = mo.ui.slider(
        start=0,
        stop=1,
        step=0.05,
        value=DEFAULT_WEIGHT_SEASONALITY,
        label="Exploration weight: seasonality",
    )

    country_options = components["geo"].astype(str).sort_values().tolist()
    default_country = (
        REPORT_DEEP_DIVE_COUNTRY
        if REPORT_DEEP_DIVE_COUNTRY in country_options
        else country_options[0]
    )

    country_select = mo.ui.dropdown(
        options=country_options,
        value=default_country,
        label="Exploration: country deep-dive",
    )

    mo.vstack(
        [
            mo.md("## Exploration controls"),
            mo.hstack([top_n, country_select]),
            mo.hstack([weight_level, weight_growth, weight_seasonality]),
            mo.md(
                """
                These controls are for exploration. Report exports later in the
                notebook use fixed parameters to keep the LaTeX outputs reproducible.
                """
            ),
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
    exploration_total_weight = (
        weight_level.value + weight_growth.value + weight_seasonality.value
    )

    if exploration_total_weight <= 0:
        raise ValueError("At least one scoring weight must be greater than zero.")

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


@app.cell
def _(
    DEFAULT_WEIGHT_GROWTH,
    DEFAULT_WEIGHT_LEVEL,
    DEFAULT_WEIGHT_SEASONALITY,
    components,
    compute_weighted_score,
):
    components_scored_report = compute_weighted_score(
        components,
        demand_col="mean_annual_nights",
        growth_col="yoy_growth_pct",
        weight_level=DEFAULT_WEIGHT_LEVEL,
        weight_growth=DEFAULT_WEIGHT_GROWTH,
        weight_seasonality=DEFAULT_WEIGHT_SEASONALITY,
        geo_col="geo",
    )

    components_scored_report.head(10)
    return (components_scored_report,)


@app.cell(hide_code=True)
def _(
    DEFAULT_WEIGHT_GROWTH,
    DEFAULT_WEIGHT_LEVEL,
    DEFAULT_WEIGHT_SEASONALITY,
    mo,
    weight_growth,
    weight_level,
    weight_seasonality,
):
    mo.md(
        f"""
        ## Technical note — opportunity score

        The score is a weighted composite of three normalized components:

        1. **Demand level**  
           Based on `mean_annual_nights`, log-scaled before min-max normalization.

        2. **Growth**  
           Based on `yoy_growth_pct`, min-max normalized.

        3. **Seasonality concentration**  
           Based on the seasonality concentration field used by the scoring function,
           normally `peak_share`.

        **Default report weights**

        - Demand level: **{DEFAULT_WEIGHT_LEVEL:.2f}**
        - Growth: **{DEFAULT_WEIGHT_GROWTH:.2f}**
        - Seasonality: **{DEFAULT_WEIGHT_SEASONALITY:.2f}**

        **Current exploration weights**

        - Demand level: **{weight_level.value:.2f}**
        - Growth: **{weight_growth.value:.2f}**
        - Seasonality: **{weight_seasonality.value:.2f}**

        The score is ordinal and directional. It ranks countries for follow-up
        investigation; it does not estimate causal campaign uplift.
        """
    )
    return


@app.cell
def _(
    VALUE_COL,
    build_heatmap_share,
    components_scored,
    country_month_scoring,
    latest_complete_year,
    top_n,
):
    heatmap_share = build_heatmap_share(
        country_month=country_month_scoring,
        components=components_scored,
        latest_year=latest_complete_year,
        top_n=top_n.value,
        value_col=VALUE_COL,
        demand_col="mean_annual_nights",
        geo_col="geo",
    )

    heatmap_share
    return (heatmap_share,)


@app.cell
def _(
    VALUE_COL,
    REPORT_TOP_N,
    build_heatmap_share,
    components_scored_report,
    country_month_scoring,
    latest_complete_year,
):
    heatmap_share_report = build_heatmap_share(
        country_month=country_month_scoring,
        components=components_scored_report,
        latest_year=latest_complete_year,
        top_n=REPORT_TOP_N,
        value_col=VALUE_COL,
        demand_col="mean_annual_nights",
        geo_col="geo",
    )

    heatmap_share_report
    return (heatmap_share_report,)


@app.cell(hide_code=True)
def _(components_scored_report, mo):
    top5 = components_scored_report.head(5)["geo"].astype(str).tolist()

    top3_demand_share = (
        components_scored_report.sort_values("mean_annual_nights", ascending=False)
        .head(3)["mean_annual_nights"]
        .sum()
        / components_scored_report["mean_annual_nights"].sum()
    )

    top_market = components_scored_report.iloc[0]["geo"]
    top_score = components_scored_report.iloc[0]["weighted_score"]

    mo.md(
        f"""
        # Headline findings

        - Default top-five shortlist: **{", ".join(top5)}**
        - Top-ranked market: **{top_market}**, score **{top_score:.2f}**
        - Top-three demand markets account for **{top3_demand_share:.1%}**
          of panel demand.
        - The ranking should be interpreted as a **country-level screening tool**,
          not as a campaign deployment model.
        """
    )
    return top3_demand_share, top5


@app.cell(hide_code=True)
def _(mo, top_n):
    mo.md(
        f"""
        # Business analysis

        ## 1. Demand landscape — where scale matters

        The first filter is absolute demand. Campaigns, pricing actions, and
        operational focus matter more in countries where the platform already has
        meaningful volume.

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
    return (fig_top_demand,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## 2. Seasonality — when demand is concentrated

        The heatmap normalizes each country to its own annual total. This means the
        colors show **within-year shape**, not absolute market size.

        A country with strong summer concentration may offer clearer
        shoulder-season upside, especially if April–May or September–October remain
        below summer levels but above the winter trough.
        """
    )
    return


@app.cell
def _(FIG_DIR, heatmap_share, latest_complete_year, plot_seasonality_heatmap):
    fig_seasonality = plot_seasonality_heatmap(
        heatmap_share,
        latest_year=latest_complete_year,
        output_dir=FIG_DIR,
    )

    fig_seasonality
    return (fig_seasonality,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## 3. Growth versus demand level — where the market is expanding

        This view separates large but mature markets from countries that are
        expanding quickly from a smaller base.

        The most attractive profile is usually:

        - higher demand scale;
        - above-median growth;
        - visible seasonality concentration.

        Small markets with very high growth should be treated as watchlist signals
        unless they also have sufficient absolute volume.
        """
    )
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
    return (fig_growth,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## 4. Composite opportunity ranking

        The ranking combines demand scale, growth, and seasonality concentration
        into one prioritization view.

        The ranking is not meant to replace judgment. It is meant to make the
        prioritization discussion explicit: changing the weights changes the score.
        """
    )
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
    return (fig_ranking,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## 5. Why the top opportunities rank highly

        The score decomposition explains whether a country ranks highly because it is:

        - already large;
        - growing quickly;
        - seasonally concentrated;
        - or a balanced combination of all three.

        This matters because the same rank can imply different follow-up work.
        A scale-led market needs regional disaggregation. A seasonality-led market
        needs destination-month diagnosis.
        """
    )
    return


@app.cell
def _(FIG_DIR, components_scored, plot_opportunity_components):
    fig_components = plot_opportunity_components(
        components_scored,
        n=10,
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_components
    return (fig_components,)


@app.cell(hide_code=True)
def _(country_select, mo):
    mo.md(
        f"""
        ## 6. Country deep-dive — selected market: {country_select.value}

        The country-level monthly curve is a diagnostic tool. It checks whether the
        apparent seasonality pattern is stable across years or whether the country
        average may be hiding multiple destination types.

        Austria is useful as the standard diagnostic example because its February
        and summer peaks suggest winter-sport and summer-tourism markets being
        averaged together.
        """
    )
    return


@app.cell
def _(
    FIG_DIR,
    VALUE_COL,
    country_month_scoring,
    country_select,
    plot_country_monthly_curve,
):
    fig_country_curve = plot_country_monthly_curve(
        country_month_scoring,
        country=country_select.value,
        value_col=VALUE_COL,
        geo_col="geo",
        output_dir=FIG_DIR,
    )

    fig_country_curve
    return (fig_country_curve,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # Technical analysis

        ## Schema checks

        The following tables document column types and missingness in the two
        analysis marts used by this notebook.
        """
    )
    return


@app.cell
def _(country_month_scoring, pd):
    schema_country_month = pd.DataFrame(
        {
            "column": country_month_scoring.columns,
            "dtype": [
                str(country_month_scoring[col].dtype)
                for col in country_month_scoring.columns
            ],
            "missing_rows": [
                country_month_scoring[col].isna().sum()
                for col in country_month_scoring.columns
            ],
            "missing_pct": [
                country_month_scoring[col].isna().mean()
                for col in country_month_scoring.columns
            ],
        }
    )

    schema_country_month
    return (schema_country_month,)


@app.cell
def _(components_scored_report, pd):
    schema_components = pd.DataFrame(
        {
            "column": components_scored_report.columns,
            "dtype": [
                str(components_scored_report[col].dtype)
                for col in components_scored_report.columns
            ],
            "missing_rows": [
                components_scored_report[col].isna().sum()
                for col in components_scored_report.columns
            ],
            "missing_pct": [
                components_scored_report[col].isna().mean()
                for col in components_scored_report.columns
            ],
        }
    )

    schema_components
    return (schema_components,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Ranking table

        This table is the tabular version of the default report ranking. It should
        reconcile with the business and technical reports.
        """
    )
    return


@app.cell
def _(REPORT_TOP_N, TABLE_DIR, components_scored_report):
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
        col for col in ranking_cols if col in components_scored_report.columns
    ]

    ranking_table = components_scored_report.head(REPORT_TOP_N)[
        available_ranking_cols
    ].copy()

    ranking_table.to_csv(TABLE_DIR / "country_screening_ranking.csv", index=False)

    ranking_table
    return (ranking_table,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Sensitivity analysis

        The weight choices are judgmental, so the ranking is tested under several
        alternative scenarios.

        The key validation question is not whether the exact rank order changes.
        It is whether the recommended shortlist remains stable enough to justify
        follow-up data acquisition.
        """
    )
    return


@app.cell
def _(TABLE_DIR, components, compute_weighted_score, pd):
    weight_scenarios = {
        "default": (0.45, 0.30, 0.25),
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

        scenario_table = scenario_df.head(10)[["geo", "weighted_score"]].copy()
        scenario_table["scenario"] = scenario_name
        scenario_table["rank"] = range(1, len(scenario_table) + 1)

        scenario_tables.append(scenario_table)

    sensitivity_table = pd.concat(scenario_tables, ignore_index=True)
    sensitivity_table.to_csv(TABLE_DIR / "country_sensitivity_table.csv", index=False)

    sensitivity_table
    return sensitivity_table, weight_scenarios


@app.cell
def _(sensitivity_table):
    sensitivity_pivot = sensitivity_table.pivot_table(
        index="geo",
        columns="scenario",
        values="rank",
        aggfunc="min",
    ).sort_values("default")

    sensitivity_pivot
    return (sensitivity_pivot,)


@app.cell
def _(TABLE_DIR, pd, sensitivity_table):
    scenario_order = [
        "default",
        "balanced",
        "scale_led",
        "growth_led",
        "seasonality_led",
    ]

    default_top5 = set(
        sensitivity_table.query("scenario == 'default' and rank <= 5")["geo"].astype(
            str
        )
    )

    top5_stability_rows = []

    for scenario_name in scenario_order:
        scenario_top5_df = sensitivity_table.query(
            "scenario == @scenario_name and rank <= 5"
        ).sort_values("rank")
        scenario_top5 = set(scenario_top5_df["geo"].astype(str))

        top5_stability_rows.append(
            {
                "scenario": scenario_name,
                "top_5": ", ".join(scenario_top5_df["geo"].astype(str).tolist()),
                "overlap_with_default_top5": len(
                    scenario_top5.intersection(default_top5)
                ),
                "entered_top5_vs_default": ", ".join(
                    sorted(scenario_top5.difference(default_top5))
                ),
                "left_top5_vs_default": ", ".join(
                    sorted(default_top5.difference(scenario_top5))
                ),
            }
        )

    top5_stability = pd.DataFrame(top5_stability_rows)
    top5_stability.to_csv(TABLE_DIR / "country_top5_stability.csv", index=False)

    top5_stability
    return default_top5, top5_stability


@app.cell(hide_code=True)
def _(default_top5, mo, top5_stability):
    stable_scenarios = top5_stability["overlap_with_default_top5"].eq(5).sum()

    mo.md(
        f"""
        ### Sensitivity interpretation

        The default top-five set is:

        **{", ".join(sorted(default_top5))}**

        Number of scenarios preserving the full default top-five set:
        **{stable_scenarios} / {len(top5_stability)}**

        Interpretation:

        - If the top-five set remains stable, the shortlist is defensible as a
          follow-up priority.
        - If only the internal order changes, the recommendation should focus on
          the set rather than precise rank.
        - If growth-led scoring introduces small markets, those markets should be
          treated as a watchlist rather than as immediate campaign candidates.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ## Data quality checks

        These checks are designed to catch issues that would materially affect the
        ranking or the report figures:

        - duplicate country-month keys;
        - incomplete country-year coverage;
        - missing values in scoring fields;
        - invalid score component bounds;
        - mismatch between country coverage in marts.
        """
    )
    return


@app.cell
def _(
    components,
    components_scored_report,
    country_month_scoring,
    country_year_months,
    expected_country_count,
    latest_complete_year,
    pd,
):
    duplicate_key_cols = ["geo", "year", "month"]

    for optional_col in ["indic_to", "c_resid"]:
        if optional_col in country_month_scoring.columns:
            duplicate_key_cols.append(optional_col)

    duplicate_keys = country_month_scoring.duplicated(duplicate_key_cols).sum()
    incomplete_country_years = country_year_months.query("n_months < 12").copy()

    scoring_required_cols = [
        "mean_annual_nights",
        "yoy_growth_pct",
        "level_component",
        "growth_component",
        "seasonality_component",
        "weighted_score",
    ]

    available_scoring_required_cols = [
        col for col in scoring_required_cols if col in components_scored_report.columns
    ]

    missing_scoring_values = (
        components_scored_report[available_scoring_required_cols].isna().sum().sum()
    )

    score_component_cols = [
        "level_component",
        "growth_component",
        "seasonality_component",
        "weighted_score",
    ]

    available_score_component_cols = [
        col for col in score_component_cols if col in components_scored_report.columns
    ]

    component_bounds = components_scored_report[available_score_component_cols].agg(
        ["min", "max"]
    )

    components_within_bounds = (
        component_bounds.loc["min"].ge(0).all()
        and component_bounds.loc["max"].le(1).all()
    )

    latest_year_country_count = country_month_scoring.query(
        "year == @latest_complete_year"
    )["geo"].nunique()

    latest_year_complete_country_count = country_year_months.query(
        "year == @latest_complete_year and n_months == 12"
    )["geo"].nunique()

    quality_summary = pd.DataFrame(
        {
            "check": [
                "duplicate_country_month_keys",
                "countries_in_components",
                "countries_in_scoring_country_month",
                "latest_complete_year_country_count",
                "latest_complete_year_complete_country_count",
                "missing_scoring_values",
                "score_components_within_0_1_bounds",
                "incomplete_country_year_rows",
            ],
            "value": [
                duplicate_keys,
                components["geo"].nunique(),
                country_month_scoring["geo"].nunique(),
                latest_year_country_count,
                latest_year_complete_country_count,
                missing_scoring_values,
                components_within_bounds,
                len(incomplete_country_years),
            ],
            "expected": [
                0,
                expected_country_count,
                expected_country_count,
                expected_country_count,
                expected_country_count,
                0,
                True,
                "documented; excluded from complete-year scoring where needed",
            ],
        }
    )

    quality_summary
    return (
        component_bounds,
        duplicate_keys,
        incomplete_country_years,
        quality_summary,
    )


@app.cell
def _(component_bounds):
    component_bounds
    return


@app.cell
def _(incomplete_country_years):
    incomplete_country_years
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # Caveats and interpretation rules

        ## Business caveats

        - A high opportunity score does not mean guaranteed campaign impact.
        - Large markets may dominate because scale is commercially important.
        - Strong summer concentration can indicate opportunity, but also structural
          seasonality that may be hard to change.
        - Country-level ranking is an upstream screen, not a deployment plan.

        ## Technical caveats

        - The score is sensitive to weighting choices.
        - Growth depends on the selected baseline period.
        - Row-normalized heatmaps show timing, not absolute demand.
        - Countries with low absolute volume can show high growth from a small base.
        - The model ranks markets; it does not estimate causal uplift.
        - Country aggregation hides destination-level heterogeneity.

        ## Recommended usage

        Use the ranking to shortlist countries. Then validate the top candidates with:

        - regional platform-tourism demand;
        - city-level platform demand proxies;
        - hotel occupancy;
        - campaign cost;
        - pricing flexibility;
        - supply availability;
        - local regulation;
        - operational constraints;
        - historical campaign response, if available.
        """
    )
    return


@app.cell(hide_code=True)
def _(
    DEFAULT_WEIGHT_GROWTH,
    DEFAULT_WEIGHT_LEVEL,
    DEFAULT_WEIGHT_SEASONALITY,
    FIG_DIR,
    REPORT_DEEP_DIVE_COUNTRY,
    REPORT_TOP_N,
    mo,
):
    mo.md(
        f"""
        # Deterministic report export

        The export cell below uses fixed report parameters, not the exploration
        sliders.

        - Report top N: **{REPORT_TOP_N}**
        - Report deep-dive country: **{REPORT_DEEP_DIVE_COUNTRY}**
        - Report weights: **{DEFAULT_WEIGHT_LEVEL:.2f} / {DEFAULT_WEIGHT_GROWTH:.2f} / {DEFAULT_WEIGHT_SEASONALITY:.2f}**
        - Output directory: `{FIG_DIR}`

        This keeps the LaTeX figures reproducible across notebook sessions.
        """
    )
    return


@app.cell
def _(
    FIG_DIR,
    REPORT_DEEP_DIVE_COUNTRY,
    REPORT_TOP_N,
    VALUE_COL,
    components_scored_report,
    country_month_scoring,
    export_all_figures,
    heatmap_share_report,
    latest_complete_year,
    mo,
):
    export_all_figures(
        components=components_scored_report,
        country_month=country_month_scoring,
        selected_country=REPORT_DEEP_DIVE_COUNTRY,
        heatmap_share=heatmap_share_report,
        latest_year=latest_complete_year,
        top_n=REPORT_TOP_N,
        output_dir=FIG_DIR,
    )

    mo.md(
        f"""
        ## Export complete

        Figures saved to:

        ```text
        {FIG_DIR}
        ```

        Use the exported `.pdf` files in LaTeX.

        Suggested report split:

        - **Business report:** decision, figures, interpretation, recommendation.
        - **Technical Quarto report:** metric definitions, scoring formula,
          sensitivity, quality checks, caveats, and reproducibility.
        """
    )
    return


if __name__ == "__main__":
    app.run()
