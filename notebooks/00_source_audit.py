import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    # 00_source_audit.py

    import json
    from pathlib import Path

    import pandas as pd
    import numpy as np

    raw_dir = Path("data/raw/eurostat")
    out_dir = Path("data/interim")
    out_dir.mkdir(parents=True, exist_ok=True)
    return json, np, out_dir, pd, raw_dir


@app.cell
def _(np, pd):
    def flatten_jsonstat(data: dict, include_labels: bool = True) -> pd.DataFrame:
        dataset_code = (
            data.get("extension", {}).get("id")
            or data.get("label")
            or "unknown_dataset"
        )

        dim_ids = data["id"]
        sizes = data["size"]
        dimensions = data["dimension"]

        dim_codes = {}
        dim_labels = {}

        for dim in dim_ids:
            category = dimensions[dim]["category"]
            index = category["index"]
            labels = category.get("label", {})

            if isinstance(index, dict):
                codes = [
                    code
                    for code, _ in sorted(index.items(), key=lambda item: item[1])
                ]
            else:
                codes = index

            dim_codes[dim] = codes
            dim_labels[dim] = labels

        values = data.get("value", {})

        if isinstance(values, list):
            value_items = enumerate(values)
        elif isinstance(values, dict):
            value_items = ((int(k), v) for k, v in values.items())
        else:
            raise TypeError("Unsupported JSON-stat value format")

        rows = []

        for flat_index, value in value_items:
            if value is None:
                continue

            coords = np.unravel_index(flat_index, sizes, order="C")

            row = {
                "dataset_code": dataset_code,
                "value": value,
            }

            for dim, pos in zip(dim_ids, coords):
                code = dim_codes[dim][pos]
                row[dim] = code

                if include_labels:
                    row[f"{dim}_label"] = dim_labels[dim].get(code, code)

            rows.append(row)

        return pd.DataFrame(rows)

    return (flatten_jsonstat,)


@app.cell
def _(flatten_jsonstat, json, out_dir, pd, raw_dir):
    all_dfs = []

    for path in raw_dir.glob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        print(path)
        try:
            df = flatten_jsonstat(data)
        except:
            print("ERROR: "+path)
            continue
        df["source_file"] = path.name

        all_dfs.append(df)

        output_path = out_dir / f"{path.stem}_flat.parquet"
        df.to_parquet(output_path, index=False)

    combined = pd.concat(all_dfs, ignore_index=True, sort=False)
    combined.to_parquet(out_dir / "eurostat_tourism_all_flat.parquet", index=False)
    return (combined,)


@app.cell
def _(combined):
    combined[combined["dataset_code"] == "TOUR_OCC_NINAT"]
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
