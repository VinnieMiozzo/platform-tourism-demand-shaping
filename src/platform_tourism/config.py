"""Central configuration for the data pipeline."""

from pathlib import Path
from typing import TypedDict


class DatasetConfig(TypedDict):
    """Schema for one Eurostat dataset entry in ``DATASETS``.

    Attributes:
        eurostat_code: The Eurostat dataset code (e.g. ``"tour_ce_omr"``).
        friendly_name: Human-readable name used in logs and reports.
        description: One-paragraph description of what the dataset contains.
        theme: Analytical theme this dataset belongs to (e.g. ``"capacity"``).
        priority: 1 = core, 2 = supporting, 3 = exploratory, 4 = optional.
        frequency: Reporting frequency, e.g. ``"monthly"``, ``"annual"``.
        grain: Natural-key dimensions of one row in the cleaned table.
        main_indicators: Mapping of Eurostat indicator codes to friendly names.
        raw_file: Filename written by ``ingest.py`` into ``RAW_DIR``.
        interim_file: Filename written by ``clean.py`` into ``INTERIM_DIR``.
        processed_file: Filename written into ``PROCESSED_DIR``.
        enabled: Whether this dataset is currently included in pipeline runs.
    """

    eurostat_code: str
    friendly_name: str
    description: str
    theme: str
    priority: int
    frequency: str
    grain: list[str]
    main_indicators: dict[str, str]
    raw_file: str
    interim_file: str
    processed_file: str
    enabled: bool


PROJECT_ROOT: Path = Path(__file__).resolve().parent[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
INTERIM_DIR: Path = DATA_DIR / "interim"
PROCESSED_DIR: Path = DATA_DIR / "processed"
MARTS_DIR: Path = DATA_DIR / "marts"


# priority: 1 = core (must-have for the analysis),
#           2 = supporting context, 3 = exploratory, 4 = optional / reserved.

DATASETS: dict[str, DatasetConfig] = {
    # ------------------------------------------------------------------
    # Core project dataset: platform / collaborative economy tourism
    # ------------------------------------------------------------------
    "platform_monthly": {
        "eurostat_code": "tour_ce_omr",
        "friendly_name": "Platform short-stay accommodation",
        "description": (
            "Short-stay accommodation offered via collaborative economy "
            "platforms, by month and residence of guest."
        ),
        "theme": "platform_tourism",
        "priority": 1,
        "frequency": "annual_by_month",
        "grain": ["geo", "time", "month", "c_resid", "indic_to", "unit"],
        "main_indicators": {
            "STY": "stays",
            "NGT_SP": "nights_spent",
            "LSTY": "length_of_stay",
        },
        "raw_file": "tour_ce_omr.json",
        "interim_file": "platform_monthly_flat.parquet",
        "processed_file": "fact_platform_monthly.parquet",
        "enabled": True,
    },
    # ------------------------------------------------------------------
    # Traditional / total tourist accommodation market
    # ------------------------------------------------------------------
    "total_accommodation_nights_monthly": {
        "eurostat_code": "tin00171",
        "friendly_name": "Total accommodation nights monthly",
        "description": (
            "Nights spent at tourist accommodation establishments by "
            "residents and non-residents, monthly data."
        ),
        "theme": "market_size",
        "priority": 1,
        "frequency": "monthly",
        "grain": ["geo", "time", "c_resid", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00171.json",
        "interim_file": "total_accommodation_nights_monthly_flat.parquet",
        "processed_file": "fact_total_accommodation_nights_monthly.parquet",
        "enabled": True,
    },
    "total_accommodation_nights_yoy_monthly": {
        "eurostat_code": "tin00172",
        "friendly_name": "Accommodation nights YoY change",
        "description": (
            "Percentage change compared with the same period of the previous "
            "year in nights spent at tourist accommodation establishments."
        ),
        "theme": "growth",
        "priority": 3,
        "frequency": "monthly",
        "grain": ["geo", "time", "c_resid", "unit"],
        "main_indicators": {
            "value": "yoy_change_pct",
        },
        "raw_file": "tin00172.json",
        "interim_file": "total_accommodation_nights_yoy_flat.parquet",
        "processed_file": "fact_accommodation_nights_yoy.parquet",
        "enabled": False,
    },
    "hotel_occupancy_monthly": {
        "eurostat_code": "tin00173",
        "friendly_name": "Hotel occupancy rate monthly",
        "description": (
            "Net occupancy rate of bed-places and bedrooms in hotels and "
            "similar accommodation, monthly data."
        ),
        "theme": "market_pressure",
        "priority": 2,
        "frequency": "monthly",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "occupancy_rate",
        },
        "raw_file": "tin00173.json",
        "interim_file": "hotel_occupancy_monthly_flat.parquet",
        "processed_file": "fact_hotel_occupancy_monthly.parquet",
        "enabled": True,
    },
    # ------------------------------------------------------------------
    # Annual occupancy data
    # ------------------------------------------------------------------
    "arrivals_annual": {
        "eurostat_code": "tin00174",
        "friendly_name": "Accommodation arrivals annual",
        "description": (
            "Arrivals of residents and non-residents at tourist accommodation "
            "establishments."
        ),
        "theme": "market_size",
        "priority": 2,
        "frequency": "annual",
        "grain": ["geo", "time", "c_resid", "unit"],
        "main_indicators": {
            "value": "arrivals",
        },
        "raw_file": "tin00174.json",
        "interim_file": "arrivals_annual_flat.parquet",
        "processed_file": "fact_arrivals_annual.parquet",
        "enabled": True,
    },
    "accommodation_nights_annual": {
        "eurostat_code": "tin00175",
        "friendly_name": "Accommodation nights annual",
        "description": (
            "Nights spent at tourist accommodation establishments by "
            "residents and non-residents."
        ),
        "theme": "market_size",
        "priority": 2,
        "frequency": "annual",
        "grain": ["geo", "time", "c_resid", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00175.json",
        "interim_file": "accommodation_nights_annual_flat.parquet",
        "processed_file": "fact_accommodation_nights_annual.parquet",
        "enabled": True,
    },
    "accommodation_nights_by_residence_region": {
        "eurostat_code": "tin00176",
        "friendly_name": "Accommodation nights by tourist residence region",
        "description": (
            "Nights spent at tourist accommodation establishments by country "
            "or world region of residence of the tourist."
        ),
        "theme": "source_markets",
        "priority": 3,
        "frequency": "annual",
        "grain": ["geo", "time", "c_resid", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00176.json",
        "interim_file": "accommodation_nights_by_residence_flat.parquet",
        "processed_file": "fact_accommodation_nights_by_residence.parquet",
        "enabled": False,
    },
    "accommodation_nights_by_type": {
        "eurostat_code": "tin00177",
        "friendly_name": "Accommodation nights by accommodation type",
        "description": (
            "Nights spent at tourist accommodation establishments by NACE "
            "accommodation type."
        ),
        "theme": "accommodation_mix",
        "priority": 1,
        "frequency": "annual",
        "grain": ["geo", "time", "nace_r2", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00177.json",
        "interim_file": "accommodation_nights_by_type_flat.parquet",
        "processed_file": "fact_accommodation_nights_by_type.parquet",
        "enabled": True,
    },
    "accommodation_nights_nuts2": {
        "eurostat_code": "tgs00111",
        "friendly_name": "Accommodation nights by NUTS 2 region",
        "description": (
            "Nights spent at tourist accommodation establishments by NUTS 2 region."
        ),
        "theme": "regional_concentration",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tgs00111.json",
        "interim_file": "accommodation_nights_nuts2_flat.parquet",
        "processed_file": "fact_accommodation_nights_nuts2.parquet",
        "enabled": False,
    },
    # ------------------------------------------------------------------
    # Capacity / supply-side context
    # ------------------------------------------------------------------
    "capacity_establishments_bedplaces": {
        "eurostat_code": "tin00181",
        "friendly_name": "Accommodation capacity",
        "description": (
            "Number of establishments and bed-places in tourist accommodation."
        ),
        "theme": "capacity",
        "priority": 2,
        "frequency": "annual",
        "grain": ["geo", "time", "indic_to", "unit"],
        "main_indicators": {
            "ESTBL": "establishments",
            "BEDPL": "bed_places",
        },
        "raw_file": "tin00181.json",
        "interim_file": "capacity_establishments_bedplaces_flat.parquet",
        "processed_file": "fact_capacity_establishments_bedplaces.parquet",
        "enabled": True,
    },
    "capacity_bedplaces_by_type": {
        "eurostat_code": "tin00182",
        "friendly_name": "Bed-places by accommodation type",
        "description": ("Number of bed-places by NACE Rev. 2 accommodation type."),
        "theme": "capacity",
        "priority": 3,
        "frequency": "annual",
        "grain": ["geo", "time", "nace_r2", "unit"],
        "main_indicators": {
            "value": "bed_places",
        },
        "raw_file": "tin00182.json",
        "interim_file": "capacity_bedplaces_by_type_flat.parquet",
        "processed_file": "fact_capacity_bedplaces_by_type.parquet",
        "enabled": False,
    },
    "capacity_establishments_bedplaces_nuts2": {
        "eurostat_code": "tgs00112",
        "friendly_name": "Accommodation capacity by NUTS 2 region",
        "description": ("Number of establishments and bed-places by NUTS 2 region."),
        "theme": "regional_capacity",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "indic_to", "unit"],
        "main_indicators": {
            "ESTBL": "establishments",
            "BEDPL": "bed_places",
        },
        "raw_file": "tgs00112.json",
        "interim_file": "capacity_nuts2_flat.parquet",
        "processed_file": "fact_capacity_nuts2.parquet",
        "enabled": False,
    },
    # ------------------------------------------------------------------
    # Tourism demand / trip behavior
    # ------------------------------------------------------------------
    "tourism_participation_number": {
        "eurostat_code": "tin00185",
        "friendly_name": "Tourism participation - number of tourists",
        "description": (
            "Persons participating in tourism for personal purposes, number "
            "of tourists."
        ),
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "tourists",
        },
        "raw_file": "tin00185.json",
        "interim_file": "tourism_participation_number_flat.parquet",
        "processed_file": "fact_tourism_participation_number.parquet",
        "enabled": False,
    },
    "tourism_participation_pct": {
        "eurostat_code": "tin00186",
        "friendly_name": "Tourism participation - percentage of population",
        "description": (
            "Participation in tourism for personal purposes as percentage of "
            "total population."
        ),
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "participation_pct",
        },
        "raw_file": "tin00186.json",
        "interim_file": "tourism_participation_pct_flat.parquet",
        "processed_file": "fact_tourism_participation_pct.parquet",
        "enabled": False,
    },
    "trips_by_purpose": {
        "eurostat_code": "tin00188",
        "friendly_name": "Trips by purpose",
        "description": "Trips by purpose.",
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "purpose", "unit"],
        "main_indicators": {
            "value": "trips",
        },
        "raw_file": "tin00188.json",
        "interim_file": "trips_by_purpose_flat.parquet",
        "processed_file": "fact_trips_by_purpose.parquet",
        "enabled": False,
    },
    "trips_by_duration": {
        "eurostat_code": "tin00189",
        "friendly_name": "Trips by duration",
        "description": "Trips by duration of the trip.",
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "duration", "unit"],
        "main_indicators": {
            "value": "trips",
        },
        "raw_file": "tin00189.json",
        "interim_file": "trips_by_duration_flat.parquet",
        "processed_file": "fact_trips_by_duration.parquet",
        "enabled": False,
    },
    "nights_by_purpose": {
        "eurostat_code": "tin00191",
        "friendly_name": "Nights by trip purpose",
        "description": "Nights spent by purpose of the trip.",
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "purpose", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00191.json",
        "interim_file": "nights_by_purpose_flat.parquet",
        "processed_file": "fact_nights_by_purpose.parquet",
        "enabled": False,
    },
    "nights_by_duration": {
        "eurostat_code": "tin00192",
        "friendly_name": "Nights by trip duration",
        "description": "Nights spent by duration of the trip.",
        "theme": "tourism_demand",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "duration", "unit"],
        "main_indicators": {
            "value": "nights_spent",
        },
        "raw_file": "tin00192.json",
        "interim_file": "nights_by_duration_flat.parquet",
        "processed_file": "fact_nights_by_duration.parquet",
        "enabled": False,
    },
    "tourism_expenditure_by_category": {
        "eurostat_code": "tin00194",
        "friendly_name": "Tourism expenditure by category",
        "description": "Tourism expenditure by category of expenditure.",
        "theme": "tourism_spending",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "expenditure_category", "unit"],
        "main_indicators": {
            "value": "expenditure",
        },
        "raw_file": "tin00194.json",
        "interim_file": "tourism_expenditure_by_category_flat.parquet",
        "processed_file": "fact_tourism_expenditure_by_category.parquet",
        "enabled": False,
    },
    "average_expenditure_per_trip": {
        "eurostat_code": "tin00195",
        "friendly_name": "Average expenditure per trip",
        "description": "Average expenditure per tourism trip.",
        "theme": "tourism_spending",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "avg_expenditure_per_trip",
        },
        "raw_file": "tin00195.json",
        "interim_file": "avg_expenditure_per_trip_flat.parquet",
        "processed_file": "fact_avg_expenditure_per_trip.parquet",
        "enabled": False,
    },
    "average_expenditure_per_night": {
        "eurostat_code": "tin00196",
        "friendly_name": "Average expenditure per night",
        "description": "Average expenditure per tourism night.",
        "theme": "tourism_spending",
        "priority": 4,
        "frequency": "annual",
        "grain": ["geo", "time", "unit"],
        "main_indicators": {
            "value": "avg_expenditure_per_night",
        },
        "raw_file": "tin00196.json",
        "interim_file": "avg_expenditure_per_night_flat.parquet",
        "processed_file": "fact_avg_expenditure_per_night.parquet",
        "enabled": False,
    },
}

CORE_DATASETS = {key: cfg for key, cfg in DATASETS.items() if cfg["enabled"]}

DATASET_CODES = {key: cfg["eurostat_code"] for key, cfg in DATASETS.items()}

DATASET_NAMES = {key: cfg["friendly_name"] for key, cfg in DATASETS.items()}

RAW_FILES = {key: RAW_DIR / cfg["raw_file"] for key, cfg in DATASETS.items()}

INTERIM_FILES = {
    key: INTERIM_DIR / cfg["interim_file"] for key, cfg in DATASETS.items()
}

PROCESSED_FILES = {
    key: PROCESSED_DIR / cfg["processed_file"] for key, cfg in DATASETS.items()
}
