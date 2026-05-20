"""Shared pytest fixtures for the platform_tourism test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def minimal_payload() -> dict:
    """A minimal JSON-stat payload covering the most common test cases.

    Includes three dimensions (``geo``, ``c_resid``, ``time``) with
    label→code mappings that mirror real Eurostat data: ISO country
    codes, EU/EA aggregates, and a ``TOTAL`` level for ``c_resid``.

    Returns:
        A JSON-stat-shaped dict with only the keys our cleaning code
        actually reads (``id`` and ``dimension``).
    """
    return {
        "id": ["geo", "c_resid", "time"],
        "dimension": {
            "geo": {
                "category": {
                    "label": {
                        "IT": "Italy",
                        "FR": "France",
                        "EU27_2020": "European Union - 27 countries",
                    }
                }
            },
            "c_resid": {
                "category": {
                    "label": {
                        "DOM": "Domestic country",
                        "FOR": "Foreign country",
                        "TOTAL": "Total",
                    }
                }
            },
            "time": {
                "category": {
                    "label": {"2023": "2023", "2024": "2024"},
                }
            },
        },
    }
