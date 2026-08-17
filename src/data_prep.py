"""Loading, cleaning, validation, and summaries for the marketing A/B test."""

from pathlib import Path
from typing import Final

import pandas as pd


EXPECTED_COLUMNS: Final[set[str]] = {
    "user_id",
    "test_group",
    "converted",
    "total_ads",
    "most_ads_day",
    "most_ads_hour",
}
EXPECTED_GROUPS: Final[set[str]] = {"ad", "psa"}
VALID_DAYS: Final[set[str]] = {
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
}


def _normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with exported index columns removed and snake-case names."""
    cleaned = data.copy()
    cleaned = cleaned.loc[:, ~cleaned.columns.astype(str).str.startswith("Unnamed:")]
    cleaned.columns = [
        str(column).strip().lower().replace(" ", "_") for column in cleaned.columns
    ]
    return cleaned


def _coerce_converted(series: pd.Series) -> pd.Series:
    """Convert common boolean representations to a strict boolean series."""
    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)

    mapping = {
        True: True,
        False: False,
        1: True,
        0: False,
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }
    normalized = series.map(
        lambda value: value.strip().lower() if isinstance(value, str) else value
    )
    converted = normalized.map(mapping)
    if converted.isna().any():
        invalid = sorted(normalized[converted.isna()].astype(str).unique())
        raise ValueError(f"Invalid converted values: {invalid}")
    return converted.astype(bool)


def validate_data(data: pd.DataFrame) -> None:
    """Raise ``ValueError`` when experiment data violates integrity rules."""
    missing_columns = EXPECTED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if data.empty:
        raise ValueError("Experiment data is empty")
    if data[list(EXPECTED_COLUMNS)].isna().any().any():
        missing = data[list(EXPECTED_COLUMNS)].isna().sum()
        raise ValueError(
            f"Missing values found: {missing[missing > 0].to_dict()}"
        )
    if data["user_id"].duplicated().any():
        raise ValueError("Each user_id must appear exactly once")

    groups = set(data["test_group"].unique())
    if groups != EXPECTED_GROUPS:
        raise ValueError(
            f"Expected test groups {sorted(EXPECTED_GROUPS)}, found {sorted(groups)}"
        )
    if not data["most_ads_day"].isin(VALID_DAYS).all():
        raise ValueError("most_ads_day contains an invalid weekday")
    if not data["most_ads_hour"].between(0, 23).all():
        raise ValueError("most_ads_hour must be between 0 and 23")
    if not (data["total_ads"] >= 0).all():
        raise ValueError("total_ads cannot be negative")


def load_data(path: str | Path) -> pd.DataFrame:
    """Load the experiment CSV, normalize its schema, and validate its contents."""
    data = _normalize_columns(pd.read_csv(path))
    if "converted" in data.columns:
        data["converted"] = _coerce_converted(data["converted"])
    if "test_group" in data.columns:
        data["test_group"] = data["test_group"].astype(str).str.strip().str.lower()
    validate_data(data)
    return data


def summarize_groups(data: pd.DataFrame) -> pd.DataFrame:
    """Return sample sizes, conversions, and conversion rates by test group."""
    validate_data(data)
    summary = (
        data.groupby("test_group", sort=False)["converted"]
        .agg(users="size", conversions="sum", conversion_rate="mean")
        .reset_index()
    )
    summary["conversions"] = summary["conversions"].astype(int)
    return summary
