"""Sanity tests for ``src/platform_tourism/config.py``.

These don't test logic so much as protect against typos and structural
drift -- catching things like a missing field, a duplicated code, or a
PROJECT_ROOT that's silently pointing at the wrong directory.
"""

from __future__ import annotations

import pytest

from platform_tourism.config import (
    DATASET_CODES,
    DATASETS,
    ENABLED_DATASETS,
    INTERIM_DIR,
    PROCESSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
    RAW_FILES,
)

REQUIRED_FIELDS = {
    "eurostat_code",
    "friendly_name",
    "description",
    "theme",
    "priority",
    "frequency",
    "grain",
    "main_indicators",
    "raw_file",
    "interim_file",
    "processed_file",
    "enabled",
}


def test_project_root_points_to_repo_root():
    assert (PROJECT_ROOT / "pyproject.toml").exists(), (
        f"PROJECT_ROOT does not contain pyproject.toml: {PROJECT_ROOT}"
    )


@pytest.mark.parametrize("directory", [RAW_DIR, INTERIM_DIR, PROCESSED_DIR])
def test_data_directories_are_inside_project_root(directory):
    # Catches PROJECT_ROOT bugs that would otherwise write data to
    # unexpected places on disk.
    assert PROJECT_ROOT in directory.parents


def test_dataset_codes_are_unique():
    codes = list(DATASET_CODES.values())
    assert len(codes) == len(set(codes)), (
        f"Duplicate eurostat_code values: {[c for c in codes if codes.count(c) > 1]}"
    )


def test_enabled_is_subset_of_all_datasets():
    assert set(ENABLED_DATASETS) <= set(DATASETS)


def test_raw_files_dict_matches_datasets():
    assert set(RAW_FILES) == set(DATASETS)


@pytest.mark.parametrize("key", list(DATASETS))
def test_every_dataset_has_required_fields(key):
    missing = REQUIRED_FIELDS - set(DATASETS[key].keys())
    assert not missing, f"{key} is missing fields: {missing}"


@pytest.mark.parametrize("key", list(DATASETS))
def test_frequency_is_recognized(key):
    valid = {"annual", "monthly", "annual_by_month"}
    assert DATASETS[key]["frequency"] in valid, (
        f"{key} has unrecognized frequency '{DATASETS[key]['frequency']}'; "
        f"expected one of {valid}"
    )
