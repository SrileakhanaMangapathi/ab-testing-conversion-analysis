import math

import pandas as pd
import pytest

from src.stats_tests import analyze_conversion, two_proportion_z_test


def experiment_data(
    ad_conversions: int,
    ad_users: int,
    psa_conversions: int,
    psa_users: int,
) -> pd.DataFrame:
    groups = ["ad"] * ad_users + ["psa"] * psa_users
    conversions = (
        [True] * ad_conversions
        + [False] * (ad_users - ad_conversions)
        + [True] * psa_conversions
        + [False] * (psa_users - psa_conversions)
    )
    total_users = ad_users + psa_users
    return pd.DataFrame(
        {
            "user_id": range(total_users),
            "test_group": groups,
            "converted": conversions,
            "total_ads": [1] * total_users,
            "most_ads_day": ["Monday"] * total_users,
            "most_ads_hour": [12] * total_users,
        }
    )


def test_analyze_conversion_calculates_lifts_and_significance():
    result = analyze_conversion(experiment_data(20, 100, 10, 100))

    assert result.treatment_rate == pytest.approx(0.20)
    assert result.control_rate == pytest.approx(0.10)
    assert result.absolute_lift == pytest.approx(0.10)
    assert result.relative_lift == pytest.approx(1.0)
    assert result.z_statistic == pytest.approx(1.9803, rel=1e-3)
    assert result.p_value == pytest.approx(0.0477, rel=1e-2)
    assert result.statistically_significant
    assert result.ci_lower < result.absolute_lift < result.ci_upper


def test_identical_rates_have_no_lift_and_p_value_one():
    result = analyze_conversion(experiment_data(10, 100, 10, 100))

    assert result.absolute_lift == pytest.approx(0.0)
    assert result.relative_lift == pytest.approx(0.0)
    assert result.z_statistic == pytest.approx(0.0)
    assert result.p_value == pytest.approx(1.0)
    assert not result.statistically_significant


def test_zero_control_rate_reports_infinite_relative_lift():
    result = analyze_conversion(experiment_data(1, 10, 0, 10))

    assert math.isinf(result.relative_lift)


@pytest.mark.parametrize(
    "values, message",
    [
        ((-1, 100, 10, 100), "treatment conversions"),
        ((101, 100, 10, 100), "treatment conversions"),
        ((10, 0, 10, 100), "treatment users"),
        ((10, 100, 10, 0), "control users"),
    ],
)
def test_two_proportion_z_test_rejects_invalid_counts(values, message):
    with pytest.raises(ValueError, match=message):
        two_proportion_z_test(*values)


def test_two_proportion_z_test_rejects_invalid_alpha():
    with pytest.raises(ValueError, match="alpha"):
        two_proportion_z_test(10, 100, 10, 100, alpha=1.0)
