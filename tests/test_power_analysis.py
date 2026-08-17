import pandas as pd
import pytest

from src.power_analysis import analyze_power


def experiment_data(
    ad_conversions: int,
    ad_users: int,
    psa_conversions: int,
    psa_users: int,
) -> pd.DataFrame:
    total_users = ad_users + psa_users
    return pd.DataFrame(
        {
            "user_id": range(total_users),
            "test_group": ["ad"] * ad_users + ["psa"] * psa_users,
            "converted": (
                [True] * ad_conversions
                + [False] * (ad_users - ad_conversions)
                + [True] * psa_conversions
                + [False] * (psa_users - psa_conversions)
            ),
            "total_ads": [1] * total_users,
            "most_ads_day": ["Monday"] * total_users,
            "most_ads_hour": [12] * total_users,
        }
    )


def test_analyze_power_reports_observed_power_and_sample_size():
    result = analyze_power(
        experiment_data(200, 1000, 100, 1000),
        minimum_detectable_effect=0.05,
    )

    assert result.control_rate == pytest.approx(0.10)
    assert result.observed_treatment_rate == pytest.approx(0.20)
    assert result.observed_absolute_lift == pytest.approx(0.10)
    assert result.allocation_ratio == pytest.approx(1.0)
    assert result.achieved_power > 0.99
    assert result.required_users_per_group > 0
    assert result.required_total_users == 2 * result.required_users_per_group


def test_identical_rates_have_power_equal_to_alpha():
    result = analyze_power(
        experiment_data(100, 1000, 100, 1000),
        minimum_detectable_effect=0.05,
    )

    assert result.achieved_power == pytest.approx(result.alpha)


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"alpha": 0}, "alpha"),
        ({"target_power": 1}, "target_power"),
        ({"minimum_detectable_effect": 0}, "minimum_detectable_effect"),
    ],
)
def test_analyze_power_rejects_invalid_parameters(kwargs, message):
    with pytest.raises(ValueError, match=message):
        analyze_power(experiment_data(20, 100, 10, 100), **kwargs)


def test_mde_cannot_push_planned_rate_above_one():
    with pytest.raises(ValueError, match="less than 1"):
        analyze_power(
            experiment_data(95, 100, 90, 100),
            minimum_detectable_effect=0.10,
        )
