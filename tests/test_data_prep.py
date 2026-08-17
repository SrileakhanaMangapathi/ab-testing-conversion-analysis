import pandas as pd
import pytest

from src.data_prep import load_data, summarize_groups, validate_data


def valid_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": [1, 2, 3, 4],
            "test_group": ["ad", "ad", "psa", "psa"],
            "converted": [True, False, False, False],
            "total_ads": [3, 2, 1, 4],
            "most_ads_day": ["Monday", "Tuesday", "Monday", "Friday"],
            "most_ads_hour": [10, 11, 12, 13],
        }
    )


def test_load_data_cleans_exported_index_and_column_names(tmp_path):
    path = tmp_path / "experiment.csv"
    raw = valid_data().rename(columns=lambda column: column.replace("_", " "))
    raw.insert(0, "Unnamed: 0", range(len(raw)))
    raw.to_csv(path, index=False)

    result = load_data(path)

    assert "Unnamed: 0" not in result.columns
    assert set(valid_data().columns) == set(result.columns)
    assert result["converted"].dtype == bool


def test_summarize_groups_calculates_rates():
    summary = summarize_groups(valid_data()).set_index("test_group")

    assert summary.loc["ad", "users"] == 2
    assert summary.loc["ad", "conversions"] == 1
    assert summary.loc["ad", "conversion_rate"] == pytest.approx(0.5)
    assert summary.loc["psa", "conversion_rate"] == pytest.approx(0.0)


def test_validate_data_rejects_duplicate_users():
    data = valid_data()
    data.loc[3, "user_id"] = 1

    with pytest.raises(ValueError, match="user_id"):
        validate_data(data)


def test_validate_data_requires_both_experiment_groups():
    data = valid_data().query("test_group == 'ad'")

    with pytest.raises(ValueError, match="Expected test groups"):
        validate_data(data)


def test_load_data_rejects_invalid_conversion_value(tmp_path):
    path = tmp_path / "invalid.csv"
    data = valid_data().astype({"converted": object})
    data.loc[0, "converted"] = "maybe"
    data.to_csv(path, index=False)

    with pytest.raises(ValueError, match="Invalid converted values"):
        load_data(path)
