"""01 — Data Exploration (marimo).

Understand the shape of raw Eurostat JSON-stat payloads so the cleaning
logic in clean.py is informed by the data, not guessed at.

Run with:
    uv run marimo edit notebooks/01_data_exploration.py
"""

import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # 01 — Data Exploration

    **Goal.** Understand the shape of the raw Eurostat JSON-stat payloads
    so the cleaning logic in `clean.py` is informed by the data, not guessed at.

    **Plan**

    1. Inspect the JSON-stat structure of one dataset (interactive dropdown).
    2. Parse to a DataFrame with dimension **codes** as columns.
    3. Coverage checks for the selected dataset.
    4. Summary scorecard across **every** enabled dataset.
    5. Capture quirks that will need handling in cleaning.
    """)
    return


@app.cell
def _():
    import json
    from pathlib import Path

    import pandas as pd
    from pyjstat import pyjstat

    from platform_tourism.config import (
        ENABLED_DATASETS,
        RAW_DIR,
        RAW_FILES,
    )

    pd.set_option("display.max_columns", 30)
    pd.set_option("display.width", 200)
    return ENABLED_DATASETS, RAW_DIR, RAW_FILES, json, pd, pyjstat


@app.cell
def _(ENABLED_DATASETS, RAW_DIR, mo):
    mo.md(f"""
    **Raw directory:** `{RAW_DIR}`

    **Enabled datasets:** {len(ENABLED_DATASETS)}
    """)
    return


@app.cell
def _(RAW_DIR, mo, pd):
    _raw_files = sorted(RAW_DIR.glob("*.json"))
    _files_table = pd.DataFrame(
        [
            {"file": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
            for f in _raw_files
        ]
    )
    mo.ui.table(_files_table, label="Ingested raw files")
    return


@app.cell
def _(json, pyjstat):
    def load_dataset(raw_path):
        """Load a Eurostat JSON-stat file as ``(payload, df)``.

        ``payload`` is the raw JSON-stat dict (for inspecting dimensions,
        metadata, density). ``df`` is a long-format DataFrame whose columns
        are renamed from pyjstat's default verbose labels back to the
        canonical JSON-stat dimension codes.
    
        Args:
        raw_path: Path to a Eurostat JSON-stat file on disk.
    
        Returns:
        Tuple ``(payload, df)``.
        """
        raw_text = raw_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        label_to_code = {
        payload["dimension"][code].get("label", code): code
        for code in payload["id"]
        }
        df = (
        pyjstat.Dataset.read(raw_text)
        .write("dataframe")
        .rename(columns=label_to_code)
        )
        return payload, df

    return (load_dataset,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Inspect the JSON-stat structure

    Pick a dataset — sections 1–3 are reactive to this choice.
    """)
    return


@app.cell
def _(ENABLED_DATASETS, mo):
    dataset_picker = mo.ui.dropdown(
        options=list(ENABLED_DATASETS),
        value=list(ENABLED_DATASETS)[0],
        label="Dataset to inspect",
    )
    dataset_picker
    return (dataset_picker,)


@app.cell
def _(RAW_FILES, dataset_picker, load_dataset):
    # One load. payload feeds the structural cells; selected_df feeds analysis.
    selected_payload, selected_df = load_dataset(RAW_FILES[dataset_picker.value])
    return selected_df, selected_payload


@app.cell
def _(RAW_FILES, dataset_picker, mo, selected_payload):
    _path = RAW_FILES[dataset_picker.value]
    mo.md(
        f"""
        **File:** `{_path.name}`

        **Label:** {selected_payload.get("label")}

        **Source:** {selected_payload.get("source")}

        **Updated:** {selected_payload.get("updated")}

        **Top-level keys:** `{list(selected_payload)}`
        """
    )
    return


@app.cell
def _(pd, selected_payload):
    dim_ids = selected_payload["id"]
    sizes = selected_payload["size"]
    dim_table = pd.DataFrame({"dimension": dim_ids, "n_categories": sizes})

    _expected = 1
    for _n in sizes:
        _expected *= _n
    _actual = len(selected_payload["value"])

    print(f"Fully-expanded cells: {_expected:,}")
    print(f"Values in payload:    {_actual:,}")
    print(f"Density:              {_actual / _expected:.1%}")
    dim_table
    return (dim_ids,)


@app.cell
def _(dim_ids, selected_payload):
    # First five categories of each dimension — peek at the codebook.
    for _dim in dim_ids:
        _labels = selected_payload["dimension"][_dim]["category"].get("label", {})
        print(f"\n{_dim}: {len(_labels)} categories")
        for _code, _label in list(_labels.items())[:5]:
            print(f"  {_code:10s} -> {_label}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. Parsed DataFrame

    Columns are JSON-stat dimension **codes** (`geo`, `time`, `unit`, ...) thanks
    to the rename in `load_dataset()`. The cell *values* inside the dimension
    columns are still labels (e.g. `"Italy"`, `"European Union - 27 ..."`).
    Whether to keep labels or switch to codes for values is a clean.py question.
    """)
    return


@app.cell
def _(mo, selected_df):
    mo.md(f"""
    **Shape:** {selected_df.shape}  •  **Columns:** `{list(selected_df.columns)}`
    """)
    return


@app.cell
def _(selected_df):
    selected_df
    return


@app.cell
def _(selected_df):
    selected_df.info()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. Coverage checks (selected dataset)
    """)
    return


@app.cell
def _(mo, selected_df):
    _bits = []
    if "time" in selected_df.columns:
        _bits.append(
            f"**Time range:** {selected_df['time'].min()} → "
            f"{selected_df['time'].max()}  "
        )
        _bits.append(f"**Distinct time points:** {selected_df['time'].nunique()}  ")
    if "geo" in selected_df.columns:
        _bits.append(f"**Distinct geos:** {selected_df['geo'].nunique()}  ")
    _n_null = selected_df["value"].isna().sum()
    _geo_null = list(selected_df.loc[selected_df["value"].isna(),"geo"].unique())
    _bits.append(
        f"**Null values:** {_n_null:,} of {len(selected_df):,} "
        f"({_n_null / len(selected_df):.1%})  "
    )
    _bits.append(
        f"**Countries With null values**: "
        f"{_geo_null}"
    )
    mo.md("\n".join(_bits))
    return


@app.cell
def _(selected_df):
    selected_df.loc[selected_df["value"].isna()]
    return


@app.cell
def _(mo, selected_df):
    if "geo" in selected_df.columns:
        _geo_top = (
            selected_df["geo"]
            .value_counts()
            .head(15)
            .rename_axis("geo")
            .reset_index(name="rows")
        )
        _view = mo.ui.table(_geo_top, label="Top 15 geos by row count")
    else:
        _view = mo.md("_No `geo` column in this dataset._")
    _view
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4. Summary across all enabled datasets

    Same loader, applied to every enabled dataset. A dataset that errors here
    or has wildly different shape from its peers is a candidate for special
    handling in `clean.py`.
    """)
    return


@app.cell
def _(ENABLED_DATASETS, RAW_FILES, load_dataset, pd):
    _records = []
    for _key in ENABLED_DATASETS:
        _path = RAW_FILES[_key]
        if not _path.exists():
            _records.append({"dataset": _key, "status": "MISSING"})
            continue
        try:
            _, _df = load_dataset(_path)
            _records.append(
                {
                    "dataset": _key,
                    "rows": len(_df),
                    "n_dims": _df.shape[1] - 1,
                    "time_min": str(_df["time"].min())
                    if "time" in _df.columns
                    else None,
                    "time_max": str(_df["time"].max())
                    if "time" in _df.columns
                    else None,
                    "n_geo": _df["geo"].nunique() if "geo" in _df.columns else None,
                    "pct_null": round(_df["value"].isna().mean() * 100, 1),
                }
            )
        except Exception as _exc:
            _records.append({"dataset": _key, "status": f"ERROR: {_exc}"})

    summary_table = pd.DataFrame(_records).set_index("dataset")
    summary_table
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4b. Per-dataset detail — automated walkthrough

    Shape, columns, unique values per dimension, and null density for every
    enabled dataset. Scroll through; anything that looks out of place
    becomes a bullet in section 5.
    """)
    return


@app.cell
def _(ENABLED_DATASETS, RAW_FILES, load_dataset):
    for _i, _key in enumerate(ENABLED_DATASETS, 1):
        _path = RAW_FILES[_key]
        print(f"\n{'=' * 72}")
        print(f"[{_i}]  {_key}")
        print('=' * 72)

        if not _path.exists():
            print(f"  MISSING: {_path}")
            continue

        try:
            _, _df = load_dataset(_path)
        except Exception as _exc:
            print(f"  ERROR: {_exc}")
            continue

        print(f"  shape:   {_df.shape}")
        print(f"  columns: {list(_df.columns)}")
        print()

        for _col in _df.columns:
            if _col == "value":
                _n_null = _df[_col].isna().sum()
                _pct = _n_null / len(_df) * 100
                print(
                    f"    {_col:14s} {len(_df) - _n_null:>9,} / {len(_df):,} "
                    f"non-null ({_pct:.1f}% null)"
                )
            else:
                _uniques = _df[_col].unique()
                _n = len(_uniques)
                if _n <= 12:
                    _show = list(_uniques)
                else:
                    _show = list(_uniques[:8]) + [f"... (+{_n - 8} more)"]
                print(f"    {_col:14s} {_n:>3} unique → {_show}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 5. Notes for clean.py

    UNIVERSAL TRANSFORMATIONS (apply to every dataset):
      1. Column names: rename pyjstat labels to JSON-stat codes (already in load_dataset).
      2. Cell values: rename labels to JSON-stat codes via payload["dimension"][dim]["category"]["index"].
      3. Time column: parse to pd.Timestamp using a format dispatcher (YYYY | YYYY-MM | year+month).
      4. Drop rows where value is null.
      5. Flag aggregates: add is_aggregate (True for EU27/Euro area rows) and per-dimension is_total columns.

    SHAPE-SPECIFIC HANDLING:
      - platform_monthly: combine year (time) + month into a single timestamp;
        route month="Total" rows to a separate aggregates table.
      - monthly datasets (2, 3): parse time as YYYY-MM.
      - annual datasets (4-7): parse time as YYYY.

    PER-DATASET NORMALIZATION:
      - Datasets 3 and 7: rename accomunit to a dataset-specific name
        (occupancy_denominator vs capacity_unit) to prevent silent mixing.
      - Datasets with constant nace_r2 / unit: keep column, but log
        a warning if the value isn't what config expects.

    OUTPUT:
      - Long-format Parquet, one file per dataset key, written to data/interim/.
      - Columns: dimension codes + value + is_aggregate + per-dim is_total flags.
      - File metadata (unit, single nace_r2 if applicable) saved as a sidecar JSON.
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
