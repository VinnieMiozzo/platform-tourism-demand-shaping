"""
visual.py

Seaborn-based, LaTeX-ready plotting layer for the platform tourism project.

Website palette:
- deep teal:  #36464B
- dark slate: #272B2B
- tan:        #B99A76
- beige:      #DAC4B0
- cream:      #F3E9DB

Main idea:\
- Keep all plot styling outside the marimo notebook.
- Save every figure as PDF for LaTeX and PNG for quick preview.
- Handle `geo` whether it is a column or the DataFrame index.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter, PercentFormatter

# ---------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------
PALETTE: dict[str, str] = {
    "deep_teal": "#36464B",
    "dark_slate": "#272B2B",
    "tan": "#B99A76",
    "beige": "#DAC4B0",
    "cream": "#F3E9DB",
    "soft_cream": "#FAF6EF",
    "muted_teal": "#6F858B",
    "light_teal": "#D9E3E4",
    "muted_tan": "#C8AD8D",
    "grid": "#E7DDD1",
    "light_grid": "#F0E9E1",
    "text": "#272B2B",
    "muted_text": "#657071",
    "white": "#FFFFFF",
}

MONTH_ORDER: list[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

MONTH_MAP: dict[int, str] = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

SHOULDER_MONTHS: list[str] = ["Apr", "May", "Sep", "Oct"]


# ---------------------------------------------------------------------
# Theme and saving
# ---------------------------------------------------------------------
def set_theme(context: str = "paper") -> None:
    """Apply a Seaborn/Matplotlib theme suitable for LaTeX figures."""

    sns.set_theme(
        context=context,
        style="whitegrid",
        palette=[
            PALETTE["deep_teal"],
            PALETTE["tan"],
            PALETTE["muted_teal"],
            PALETTE["beige"],
            PALETTE["dark_slate"],
        ],
        rc={
            "figure.dpi": 140,
            "savefig.dpi": 360,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],
            "font.size": 9.5,
            "axes.titlesize": 12,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
            "axes.titleweight": "bold",
            "axes.edgecolor": PALETTE["grid"],
            "axes.labelcolor": PALETTE["text"],
            "xtick.color": PALETTE["text"],
            "ytick.color": PALETTE["text"],
            "text.color": PALETTE["text"],
            "grid.color": PALETTE["light_grid"],
            "grid.linewidth": 0.75,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        },
    )


def save_fig(
    fig: plt.Figure,
    name: str,
    output_dir: str | Path = "reports/figures",
    formats: Sequence[str] = ("pdf", "png"),
) -> None:
    """Save a figure as vector PDF and quick-preview PNG."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    safe_name = name.strip().lower().replace(" ", "_")
    for fmt in formats:
        fig.savefig(
            output_path / f"{safe_name}.{fmt}",
            bbox_inches="tight",
            pad_inches=0.05,
            facecolor=PALETTE["white"],
        )


def clean_axis(
    ax: plt.Axes,
    *,
    x_grid: bool = True,
    y_grid: bool = False,
    despine: bool = True,
) -> None:
    """Standard chart cleanup."""

    ax.set_facecolor(PALETTE["white"])
    ax.grid(x_grid, axis="x", color=PALETTE["light_grid"], linewidth=0.75)
    ax.grid(y_grid, axis="y", color=PALETTE["light_grid"], linewidth=0.75)

    if despine:
        sns.despine(ax=ax, top=True, right=True, left=False, bottom=False)

    for side in ["left", "bottom"]:
        ax.spines[side].set_color(PALETTE["grid"])
        ax.spines[side].set_linewidth(0.8)

    ax.tick_params(axis="both", length=0)


def add_note(fig: plt.Figure, note: str, y: float = -0.025) -> None:
    """Add a small report note below the chart."""

    fig.text(
        0.01,
        y,
        note,
        ha="left",
        va="bottom",
        fontsize=7.6,
        color=PALETTE["muted_text"],
    )


def annotate_text(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    *,
    xytext: tuple[int, int] = (4, 3),
    size: float = 8,
) -> None:
    """Label a point with a subtle white outline."""

    label = ax.annotate(
        text,
        xy=(x, y),
        xytext=xytext,
        textcoords="offset points",
        fontsize=size,
        color=PALETTE["dark_slate"],
    )
    label.set_path_effects(
        [pe.withStroke(linewidth=2.5, foreground="white", alpha=0.9)]
    )


def format_millions(x: float, _pos=None) -> str:
    return f"{x:,.0f}M"


def format_thousands(x: float, _pos=None) -> str:
    return f"{x:,.0f}k"


def format_pct(x: float, _pos=None) -> str:
    return f"{x:.0f}%"


# ---------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------
def ensure_geo_column(df: pd.DataFrame, geo_col: str = "geo") -> pd.DataFrame:
    """Return a copy where country/geography id is available as a column."""

    if geo_col in df.columns:
        return df.copy()

    if df.index.name == geo_col or geo_col in df.index.names:
        return df.reset_index()

    out = df.reset_index()
    if geo_col not in out.columns:
        out = out.rename(columns={out.columns[0]: geo_col})

    return out


def normalize_months(df: pd.DataFrame) -> pd.DataFrame:
    """Create a consistent `month_name` column."""

    out = df.copy()

    if "month_name" in out.columns:
        out["month_name"] = out["month_name"].astype(str).str[:3].str.title()
        return out

    if "month_num" in out.columns:
        out["month_name"] = out["month_num"].astype(int).map(MONTH_MAP)
        return out

    if "month_number" in out.columns:
        out["month_name"] = out["month_number"].astype(int).map(MONTH_MAP)
        return out

    if "month" in out.columns:
        if pd.api.types.is_numeric_dtype(out["month"]):
            out["month_name"] = out["month"].astype(int).map(MONTH_MAP)
        else:
            parsed = pd.to_datetime(out["month"], errors="coerce")
            if parsed.notna().mean() > 0.8:
                out["month_name"] = parsed.dt.month.map(MONTH_MAP)
            else:
                out["month_name"] = out["month"].astype(str).str[:3].str.title()
        return out

    if "date" in out.columns:
        parsed = pd.to_datetime(out["date"], errors="coerce")
        out["month_name"] = parsed.dt.month.map(MONTH_MAP)
        return out

    raise ValueError(
        "Could not detect month information. Expected one of: "
        "`month_name`, `month_num`, `month_number`, `month`, or `date`."
    )


def detect_value_column(df: pd.DataFrame) -> str:
    """Detect the platform nights/value column in the long mart."""

    candidates = [
        "platform_nights",
        "nights",
        "tourism_nights",
        "guest_nights",
        "value",
        "OBS_VALUE",
        "obs_value",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    excluded = {"year", "month", "month_num", "month_number"}
    numeric_cols = [col for col in numeric_cols if col not in excluded]

    if not numeric_cols:
        raise ValueError(
            "Could not detect the value column. Rename the nights column to "
            "`platform_nights` or pass a value column explicitly."
        )

    return numeric_cols[0]


def minmax(series: pd.Series, *, log: bool = False) -> pd.Series:
    """Robust min-max scaling with light winsorization."""

    s = pd.to_numeric(series, errors="coerce").astype(float)

    if log:
        s = np.log1p(s.clip(lower=0))

    lower = s.quantile(0.02)
    upper = s.quantile(0.98)
    s = s.clip(lower, upper)

    denominator = s.max() - s.min()
    if denominator == 0 or pd.isna(denominator):
        return pd.Series(0.0, index=series.index)

    return (s - s.min()) / denominator


def compute_weighted_score(
    components: pd.DataFrame,
    *,
    demand_col: str = "mean_annual_nights",
    growth_col: str = "yoy_growth_pct",
    weight_level: float = 0.45,
    weight_growth: float = 0.30,
    weight_seasonality: float = 0.25,
    geo_col: str = "geo",
) -> pd.DataFrame:
    """Compute level/growth/seasonality components and weighted score."""

    out = ensure_geo_column(components, geo_col=geo_col)

    if demand_col not in out.columns:
        raise ValueError(f"Missing demand column: {demand_col}")

    if growth_col not in out.columns:
        raise ValueError(f"Missing growth column: {growth_col}")

    out["level_component"] = minmax(out[demand_col], log=True)
    out["growth_component"] = minmax(out[growth_col], log=False)

    if "peak_share" in out.columns:
        seasonality_col = "peak_share"
    elif "shoulder_share" in out.columns:
        seasonality_col = "shoulder_share"
    elif "off_share" in out.columns:
        seasonality_col = "off_share"
    else:
        seasonality_col = None

    if seasonality_col:
        out["seasonality_component"] = minmax(out[seasonality_col], log=False)
    else:
        out["seasonality_component"] = 0.0

    total_weight = weight_level + weight_growth + weight_seasonality
    if total_weight == 0:
        total_weight = 1.0

    out["weighted_score"] = (
        weight_level * out["level_component"]
        + weight_growth * out["growth_component"]
        + weight_seasonality * out["seasonality_component"]
    ) / total_weight

    return out.sort_values("weighted_score", ascending=False)


def build_heatmap_share(
    country_month: pd.DataFrame,
    components: pd.DataFrame,
    *,
    latest_year: int | None = None,
    top_n: int = 15,
    value_col: str | None = None,
    demand_col: str = "mean_annual_nights",
    geo_col: str = "geo",
) -> pd.DataFrame:
    """Build row-normalized month share heatmap for top demand countries."""

    cm = ensure_geo_column(country_month, geo_col=geo_col)
    cm = normalize_months(cm)
    comp = ensure_geo_column(components, geo_col=geo_col)

    if value_col is None:
        value_col = detect_value_column(cm)

    if latest_year is None:
        latest_year = int(cm["year"].max())

    top_countries = (
        comp.sort_values(demand_col, ascending=False)
        .head(top_n)[geo_col]
        .astype(str)
        .tolist()
    )

    source = cm.loc[
        cm["year"].eq(latest_year) & cm[geo_col].astype(str).isin(top_countries)
    ].copy()

    heatmap_abs = (
        source.pivot_table(
            index=geo_col,
            columns="month_name",
            values=value_col,
            aggfunc="sum",
        )
        .reindex(index=top_countries)
        .reindex(columns=MONTH_ORDER)
        .fillna(0)
    )

    heatmap_share = heatmap_abs.div(heatmap_abs.sum(axis=1), axis=0).fillna(0)
    heatmap_share = heatmap_share.loc[heatmap_share.sum(axis=1).gt(0)]

    return heatmap_share


# ---------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------
def plot_top_demand(
    components: pd.DataFrame,
    *,
    n: int = 15,
    demand_col: str = "mean_annual_nights",
    geo_col: str = "geo",
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Horizontal bar chart of top countries by recent demand."""

    set_theme()

    df = ensure_geo_column(components, geo_col)
    plot_df = (
        df[[geo_col, demand_col]]
        .dropna()
        .sort_values(demand_col, ascending=False)
        .head(n)
        .assign(value_m=lambda x: x[demand_col] / 1_000_000)
    )

    fig, ax = plt.subplots(figsize=(7.3, 4.8))

    plot_df["rank_group"] = np.where(
        np.arange(len(plot_df)) < 3,
        "Top 3",
        "Other top markets",
    )

    sns.barplot(
        data=plot_df,
        y=geo_col,
        x="value_m",
        hue="rank_group",
        dodge=False,
        palette={
            "Top 3": PALETTE["tan"],
            "Other top markets": PALETTE["deep_teal"],
        },
        ax=ax,
    )

    ax.legend_.remove()
    ax.set_title("Top countries by recent platform tourism demand", pad=12)
    ax.set_xlabel("Mean annual platform nights, latest 3 years")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(FuncFormatter(format_millions))

    max_value = plot_df["value_m"].max()
    ax.set_xlim(0, max_value * 1.17)

    for y, value in enumerate(plot_df["value_m"]):
        ax.text(
            value + max_value * 0.012,
            y,
            f"{value:,.0f}M",
            va="center",
            fontsize=8.2,
            color=PALETTE["dark_slate"],
        )

    clean_axis(ax, x_grid=True, y_grid=False)
    add_note(fig, "Top three markets highlighted; values are annualized averages.")
    fig.tight_layout()
    save_fig(fig, "top_demand", output_dir)
    return fig


def plot_seasonality_heatmap(
    heatmap_share: pd.DataFrame,
    *,
    latest_year: int | None = None,
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Heatmap of within-year share of demand."""

    set_theme()

    title_year = f", {latest_year}" if latest_year else ""

    cmap = LinearSegmentedColormap.from_list(
        "tourism_heat",
        [
            PALETTE["soft_cream"],
            PALETTE["cream"],
            PALETTE["beige"],
            PALETTE["tan"],
            PALETTE["deep_teal"],
        ],
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.0))

    vmax = max(0.01, np.nanpercentile(heatmap_share.values, 97))
    sns.heatmap(
        heatmap_share,
        cmap=cmap,
        vmin=0,
        vmax=vmax,
        linewidths=1.0,
        linecolor="white",
        cbar_kws={"label": "Share of annual nights"},
        ax=ax,
    )

    ax.set_title(f"Within-year concentration of platform nights{title_year}", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")

    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))

    add_note(
        fig,
        "Rows sum to 100%; color intensity shows demand timing, not market size.",
    )
    fig.tight_layout()
    save_fig(fig, "seasonality_heatmap", output_dir)
    return fig


def plot_growth_vs_demand(
    components: pd.DataFrame,
    *,
    n_labels: int = 10,
    demand_col: str = "mean_annual_nights",
    growth_col: str = "yoy_growth_pct",
    score_col: str = "weighted_score",
    geo_col: str = "geo",
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Bubble scatter of market size vs growth."""

    set_theme()

    df = ensure_geo_column(components, geo_col)
    plot_df = df.copy()
    plot_df["demand_m"] = plot_df[demand_col] / 1_000_000
    plot_df["bubble_size"] = 70 + 900 * np.sqrt(
        plot_df[demand_col] / plot_df[demand_col].max()
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.0))

    cmap = LinearSegmentedColormap.from_list(
        "score_scale",
        [PALETTE["beige"], PALETTE["tan"], PALETTE["deep_teal"]],
    )

    if score_col not in plot_df.columns:
        plot_df[score_col] = minmax(plot_df[demand_col], log=True)

    scatter = ax.scatter(
        plot_df["demand_m"],
        plot_df[growth_col],
        s=plot_df["bubble_size"],
        c=plot_df[score_col],
        cmap=cmap,
        alpha=0.80,
        linewidth=0.75,
        edgecolor=PALETTE["dark_slate"],
    )

    ax.set_xscale("log")
    ax.set_title("Growth vs demand level — where is the market expanding?", pad=12)
    ax.set_xlabel("Mean annual platform nights, latest 3 years (millions, log scale)")
    ax.set_ylabel("YoY growth, latest complete year vs prior 2 years")
    ax.yaxis.set_major_formatter(FuncFormatter(format_pct))

    ax.axhline(
        plot_df[growth_col].median(),
        color=PALETTE["tan"],
        linestyle="--",
        linewidth=1.0,
        alpha=0.85,
    )
    ax.axvline(
        plot_df["demand_m"].median(),
        color=PALETTE["tan"],
        linestyle="--",
        linewidth=1.0,
        alpha=0.85,
    )

    label_df = plot_df.sort_values(score_col, ascending=False).head(n_labels)
    for _, row in label_df.iterrows():
        annotate_text(
            ax,
            row["demand_m"],
            row[growth_col],
            str(row[geo_col]),
            size=8,
        )

    cbar = fig.colorbar(scatter, ax=ax, fraction=0.035, pad=0.025)
    cbar.set_label("Weighted opportunity score")

    clean_axis(ax, x_grid=True, y_grid=True)
    add_note(
        fig,
        "Dashed lines show medians; bubble size reflects market scale.",
    )
    fig.tight_layout()
    save_fig(fig, "growth_vs_demand", output_dir)
    return fig


def plot_opportunity_ranking(
    components: pd.DataFrame,
    *,
    n: int = 15,
    score_col: str = "weighted_score",
    geo_col: str = "geo",
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Lollipop chart for opportunity ranking."""

    set_theme()

    df = ensure_geo_column(components, geo_col)
    plot_df = (
        df[[geo_col, score_col]]
        .dropna()
        .sort_values(score_col, ascending=False)
        .head(n)
        .sort_values(score_col, ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7.3, 4.8))

    y = np.arange(len(plot_df))

    ax.hlines(
        y=y,
        xmin=0,
        xmax=plot_df[score_col],
        color=PALETTE["beige"],
        linewidth=6.0,
        alpha=0.78,
    )
    ax.scatter(
        plot_df[score_col],
        y,
        s=95,
        color=PALETTE["deep_teal"],
        edgecolor=PALETTE["dark_slate"],
        linewidth=0.8,
        zorder=3,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_df[geo_col])
    ax.set_xlabel("Weighted opportunity score")
    ax.set_title("Top countries by composite opportunity score", pad=12)
    ax.set_xlim(0, max(1.0, plot_df[score_col].max() * 1.12))

    for idx, value in enumerate(plot_df[score_col]):
        ax.text(
            value + 0.018,
            idx,
            f"{value:.2f}",
            va="center",
            fontsize=8.2,
            color=PALETTE["dark_slate"],
        )

    clean_axis(ax, x_grid=True, y_grid=False)
    add_note(fig, "Score combines level, growth, and seasonality weights.")
    fig.tight_layout()
    save_fig(fig, "opportunity_ranking", output_dir)
    return fig


def plot_opportunity_components(
    components: pd.DataFrame,
    *,
    n: int = 10,
    geo_col: str = "geo",
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Stacked score explanation chart for top countries."""

    set_theme()

    required = [
        geo_col,
        "level_component",
        "growth_component",
        "seasonality_component",
        "weighted_score",
    ]

    df = ensure_geo_column(components, geo_col)
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            "Missing score component columns. Run `compute_weighted_score()` first. "
            f"Missing: {missing}"
        )

    plot_df = (
        df[required]
        .dropna()
        .sort_values("weighted_score", ascending=False)
        .head(n)
        .sort_values("weighted_score", ascending=True)
    )

    fig, ax = plt.subplots(figsize=(7.3, 4.8))

    colors = [
        PALETTE["deep_teal"],
        PALETTE["tan"],
        PALETTE["muted_teal"],
    ]
    labels = [
        "Demand level",
        "Growth",
        "Seasonality",
    ]
    cols = [
        "level_component",
        "growth_component",
        "seasonality_component",
    ]

    left = np.zeros(len(plot_df))

    for col, label, color in zip(cols, labels, colors):
        ax.barh(
            plot_df[geo_col],
            plot_df[col],
            left=left,
            color=color,
            height=0.68,
            label=label,
        )
        left = left + plot_df[col].to_numpy()

    ax.set_title("Why the top opportunities rank highly", pad=12)
    ax.set_xlabel("Normalized component contribution before weight scaling")
    ax.legend(frameon=False, ncol=3, loc="lower right")

    clean_axis(ax, x_grid=True, y_grid=False)
    add_note(fig, "Use this chart to explain the ranking, not just report it.")
    fig.tight_layout()
    save_fig(fig, "opportunity_components", output_dir)
    return fig


def plot_country_monthly_curve(
    country_month: pd.DataFrame,
    *,
    country: str,
    value_col: str | None = None,
    geo_col: str = "geo",
    output_dir: str | Path = "reports/figures",
) -> plt.Figure:
    """Monthly platform nights by year for a selected country."""

    set_theme()

    df = ensure_geo_column(country_month, geo_col)
    df = normalize_months(df)

    if value_col is None:
        value_col = detect_value_column(df)

    plot_df = df.loc[df[geo_col].astype(str).eq(str(country))].copy()
    if plot_df.empty:
        raise ValueError(f"No rows found for country: {country}")

    plot_df["month_name"] = pd.Categorical(
        plot_df["month_name"],
        categories=MONTH_ORDER,
        ordered=True,
    )
    plot_df = plot_df.sort_values(["year", "month_name"])
    plot_df["value_k"] = plot_df[value_col] / 1_000

    years = sorted(plot_df["year"].dropna().unique())
    latest_year = max(years)

    fig, ax = plt.subplots(figsize=(7.4, 4.9))

    for month_name in SHOULDER_MONTHS:
        month_idx = MONTH_ORDER.index(month_name)
        ax.axvspan(
            month_idx - 0.5,
            month_idx + 0.5,
            color=PALETTE["beige"],
            alpha=0.28,
            linewidth=0,
            zorder=0,
        )

    # Older years as muted context.
    older = plot_df.loc[plot_df["year"].ne(latest_year)]
    if not older.empty:
        sns.lineplot(
            data=older,
            x="month_name",
            y="value_k",
            hue="year",
            estimator=None,
            units="year",
            color=PALETTE["muted_teal"],
            alpha=0.25,
            linewidth=1.2,
            legend=False,
            ax=ax,
        )

    # Latest year as the analytical focus.
    latest = plot_df.loc[plot_df["year"].eq(latest_year)]
    sns.lineplot(
        data=latest,
        x="month_name",
        y="value_k",
        marker="o",
        markersize=5,
        color=PALETTE["deep_teal"],
        linewidth=2.5,
        label=str(int(latest_year)),
        ax=ax,
    )

    ax.set_title(f"{country} — monthly platform nights by year", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("Platform nights")
    ax.yaxis.set_major_formatter(FuncFormatter(format_thousands))
    ax.legend(title="Highlighted year", frameon=False, loc="upper left")

    clean_axis(ax, x_grid=False, y_grid=True)
    add_note(fig, "Shaded bands mark shoulder months: Apr–May and Sep–Oct.")
    fig.tight_layout()
    save_fig(fig, f"{str(country).lower()}_monthly_curve", output_dir)
    return fig


def export_all_figures(
    *,
    components: pd.DataFrame,
    country_month: pd.DataFrame,
    selected_country: str,
    heatmap_share: pd.DataFrame | None = None,
    latest_year: int | None = None,
    top_n: int = 15,
    output_dir: str | Path = "reports/figures",
) -> None:
    """Export all report figures in one call."""

    if heatmap_share is None:
        heatmap_share = build_heatmap_share(
            country_month=country_month,
            components=components,
            latest_year=latest_year,
            top_n=top_n,
        )

    plot_top_demand(components, n=top_n, output_dir=output_dir)
    plot_seasonality_heatmap(
        heatmap_share,
        latest_year=latest_year,
        output_dir=output_dir,
    )
    plot_growth_vs_demand(components, output_dir=output_dir)
    plot_opportunity_ranking(components, n=top_n, output_dir=output_dir)
    plot_opportunity_components(components, n=min(10, top_n), output_dir=output_dir)
    plot_country_monthly_curve(
        country_month,
        country=selected_country,
        output_dir=output_dir,
    )
