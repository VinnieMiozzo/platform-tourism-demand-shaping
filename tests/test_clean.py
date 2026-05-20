"""Tests for ``src/platform_tourism/clean.py``.

Each test targets a single pure transformation function. Synthetic
DataFrames are small enough to be obvious by inspection; the fixtures
live in ``conftest.py``.
"""

from __future__ import annotations

import pandas as pd
import pytest

from platform_tourism.clean import (
    apply_custom_renames,
    drop_null_values,
    flag_aggregates,
    flag_totals,
    labels_to_codes,
    parse_time_annual,
    parse_time_annual_by_month,
    parse_time_monthly,
)

# ---------------------------------------------------------------------------
# labels_to_codes
# ---------------------------------------------------------------------------


class TestLabelsToCodes:
    """``labels_to_codes`` should invert each dimension's label map."""

    def test_converts_known_labels(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["Italy", "France"],
                "c_resid": ["Total", "Domestic country"],
                "time": ["2024", "2024"],
                "value": [100.0, 50.0],
            }
        )
        result = labels_to_codes(df, minimal_payload)
        assert list(result["geo"]) == ["IT", "FR"]
        assert list(result["c_resid"]) == ["TOTAL", "DOM"]

    def test_unmapped_values_pass_through_unchanged(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["Italy", "Atlantis"],
                "c_resid": ["Total", "Total"],
                "time": ["2024", "2024"],
                "value": [1.0, 2.0],
            }
        )
        result = labels_to_codes(df, minimal_payload)
        # Italy maps to IT; Atlantis is unknown so it stays as-is.
        assert result.loc[0, "geo"] == "IT"
        assert result.loc[1, "geo"] == "Atlantis"

    def test_does_not_mutate_input(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["Italy"],
                "c_resid": ["Total"],
                "time": ["2024"],
                "value": [1.0],
            }
        )
        snapshot = df.copy()
        labels_to_codes(df, minimal_payload)
        pd.testing.assert_frame_equal(df, snapshot)

    def test_value_column_untouched(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["Italy"],
                "c_resid": ["Total"],
                "time": ["2024"],
                "value": [1.0],
            }
        )
        result = labels_to_codes(df, minimal_payload)
        assert result.loc[0, "value"] == 1.0


# ---------------------------------------------------------------------------
# Time parsers
# ---------------------------------------------------------------------------


class TestParseTimeAnnual:
    def test_year_strings_become_january_first(self):
        df = pd.DataFrame({"time": ["2023", "2024"], "value": [1, 2]})
        result = parse_time_annual(df)
        assert list(result["time"]) == [
            pd.Timestamp("2023-01-01"),
            pd.Timestamp("2024-01-01"),
        ]

    def test_output_dtype_is_datetime(self):
        df = pd.DataFrame({"time": ["2024"], "value": [1]})
        result = parse_time_annual(df)
        assert pd.api.types.is_datetime64_any_dtype(result["time"])


class TestParseTimeMonthly:
    def test_year_month_strings_become_month_first(self):
        df = pd.DataFrame({"time": ["2024-01", "2024-12"], "value": [1, 2]})
        result = parse_time_monthly(df)
        assert list(result["time"]) == [
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-12-01"),
        ]


class TestParseTimeAnnualByMonth:
    """The platform_monthly special case: year + month -> single timestamp."""

    def test_combines_year_and_month_code(self):
        df = pd.DataFrame(
            {
                "time": ["2024", "2024"],
                "month": ["M03", "M12"],
                "value": [1, 2],
            }
        )
        result = parse_time_annual_by_month(df, payload={})
        assert list(result["time"]) == [
            pd.Timestamp("2024-03-01"),
            pd.Timestamp("2024-12-01"),
        ]

    def test_total_month_falls_back_to_year_start(self):
        df = pd.DataFrame(
            {
                "time": ["2024", "2024"],
                "month": ["TOTAL", "M01"],
                "value": [1, 2],
            }
        )
        result = parse_time_annual_by_month(df, payload={})
        # Both end up at Jan 1; the month column distinguishes them.
        assert result.loc[0, "time"] == pd.Timestamp("2024-01-01")
        assert result.loc[1, "time"] == pd.Timestamp("2024-01-01")


# ---------------------------------------------------------------------------
# drop_null_values
# ---------------------------------------------------------------------------


class TestDropNullValues:
    def test_removes_nan_value_rows(self):
        df = pd.DataFrame(
            {
                "geo": ["IT", "FR", "DE"],
                "value": [1.0, float("nan"), 3.0],
            }
        )
        result = drop_null_values(df)
        assert len(result) == 2
        assert list(result["geo"]) == ["IT", "DE"]

    def test_keeps_zero_values(self):
        # Important: 0 is a valid measurement, not missing.
        df = pd.DataFrame({"geo": ["IT", "FR"], "value": [0.0, 1.0]})
        result = drop_null_values(df)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# flag_aggregates
# ---------------------------------------------------------------------------


class TestFlagAggregates:
    @pytest.mark.parametrize(
        "geo,expected",
        [
            # ISO country codes — never aggregates, even ones starting with E
            ("IT", False),
            ("FR", False),
            ("EE", False),  # Estonia
            ("EL", False),  # Greece
            ("ES", False),  # Spain
            # EU aggregates
            ("EU27_2020", True),
            ("EU28", True),
            # Euro area aggregates (all historical variants)
            ("EA19", True),
            ("EA20", True),
            ("EA21", True),
        ],
    )
    def test_flag_matches_eu_and_ea_prefixes(self, geo, expected):
        df = pd.DataFrame({"geo": [geo], "value": [1.0]})
        result = flag_aggregates(df)
        assert bool(result.loc[0, "is_aggregate"]) is expected

    def test_handles_missing_geo_column(self):
        # Some datasets might not have a geo column; should not crash.
        df = pd.DataFrame({"time": ["2024"], "value": [1.0]})
        result = flag_aggregates(df)
        assert (
            result.loc[0, "is_aggregate"] is False
            or bool(result.loc[0, "is_aggregate"]) is False
        )


# ---------------------------------------------------------------------------
# flag_totals
# ---------------------------------------------------------------------------


class TestFlagTotals:
    def test_adds_flag_for_dim_with_total(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["IT", "IT", "IT"],
                "c_resid": ["DOM", "FOR", "TOTAL"],
                "time": ["2024", "2024", "2024"],
                "value": [1.0, 2.0, 3.0],
            }
        )
        result = flag_totals(df, minimal_payload)
        assert "c_resid_is_total" in result.columns
        assert list(result["c_resid_is_total"]) == [False, False, True]

    def test_skips_dim_with_no_total_present(self, minimal_payload):
        df = pd.DataFrame(
            {
                "geo": ["IT", "FR"],
                "c_resid": ["DOM", "FOR"],  # no TOTAL row in the data
                "time": ["2024", "2024"],
                "value": [1.0, 2.0],
            }
        )
        result = flag_totals(df, minimal_payload)
        assert "c_resid_is_total" not in result.columns

    def test_skips_time_dimension(self, minimal_payload):
        # Even if (hypothetically) the time column held a TOTAL code,
        # we don't flag time -- it's continuous, not categorical.
        df = pd.DataFrame(
            {
                "geo": ["IT"],
                "c_resid": ["DOM"],
                "time": ["TOTAL"],
                "value": [1.0],
            }
        )
        result = flag_totals(df, minimal_payload)
        assert "time_is_total" not in result.columns


# ---------------------------------------------------------------------------
# apply_custom_renames
# ---------------------------------------------------------------------------


class TestApplyCustomRenames:
    def test_renames_accomunit_for_known_key(self):
        df = pd.DataFrame({"accomunit": ["BEDPL"], "value": [1.0]})
        result = apply_custom_renames(df, "hotel_occupancy_monthly")
        assert "occupancy_denominator" in result.columns
        assert "accomunit" not in result.columns

    def test_also_renames_matching_is_total_flag(self):
        df = pd.DataFrame(
            {
                "accomunit": ["BEDPL", "TOTAL"],
                "accomunit_is_total": [False, True],
                "value": [1.0, 2.0],
            }
        )
        result = apply_custom_renames(df, "hotel_occupancy_monthly")
        assert "occupancy_denominator_is_total" in result.columns
        assert "accomunit_is_total" not in result.columns

    def test_no_op_for_dataset_without_overrides(self):
        df = pd.DataFrame({"accomunit": ["X"], "value": [1.0]})
        result = apply_custom_renames(df, "some_unconfigured_dataset")
        assert "accomunit" in result.columns

    def test_capacity_dataset_uses_different_rename(self):
        # The whole point of custom renames: same column, different meaning.
        df = pd.DataFrame({"accomunit": ["ESTBL"], "value": [1.0]})
        result = apply_custom_renames(df, "capacity_establishments_bedplaces")
        assert "capacity_unit" in result.columns
        assert "occupancy_denominator" not in result.columns
