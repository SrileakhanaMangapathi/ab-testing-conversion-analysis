"""Power and sample-size planning for a two-group conversion experiment."""

from dataclasses import asdict, dataclass
from math import ceil

import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from src.data_prep import validate_data


@dataclass(frozen=True)
class PowerAnalysisResult:
    """Observed power and equal-allocation planning estimates."""

    control_rate: float
    observed_treatment_rate: float
    observed_absolute_lift: float
    control_users: int
    treatment_users: int
    allocation_ratio: float
    alpha: float
    achieved_power: float
    target_power: float
    minimum_detectable_effect: float
    required_users_per_group: int
    required_total_users: int

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


def analyze_power(
    data: pd.DataFrame,
    *,
    treatment_group: str = "ad",
    control_group: str = "psa",
    minimum_detectable_effect: float = 0.002,
    alpha: float = 0.05,
    target_power: float = 0.80,
) -> PowerAnalysisResult:
    """Calculate observed power and future equal-allocation sample requirements.

    ``minimum_detectable_effect`` is an absolute conversion-rate difference. For
    example, 0.002 represents 0.20 percentage points.
    """
    validate_data(data)
    _validate_parameters(alpha, target_power, minimum_detectable_effect)
    if treatment_group == control_group:
        raise ValueError("Treatment and control groups must be different")

    treatment = data.loc[data["test_group"] == treatment_group, "converted"]
    control = data.loc[data["test_group"] == control_group, "converted"]
    if treatment.empty or control.empty:
        raise ValueError("Treatment and control groups must both be present")

    treatment_users = int(treatment.size)
    control_users = int(control.size)
    treatment_rate = float(treatment.mean())
    control_rate = float(control.mean())
    allocation_ratio = treatment_users / control_users
    observed_effect_size = abs(
        proportion_effectsize(control_rate, treatment_rate)
    )
    achieved_power = _achieved_power(
        observed_effect_size,
        control_users,
        allocation_ratio,
        alpha,
    )

    planned_treatment_rate = control_rate + minimum_detectable_effect
    if planned_treatment_rate >= 1:
        raise ValueError(
            "control rate plus minimum_detectable_effect must be less than 1"
        )
    planning_effect_size = abs(
        proportion_effectsize(control_rate, planned_treatment_rate)
    )
    required_per_group = ceil(
        NormalIndPower().solve_power(
            effect_size=planning_effect_size,
            power=target_power,
            alpha=alpha,
            ratio=1.0,
            alternative="two-sided",
        )
    )

    return PowerAnalysisResult(
        control_rate=control_rate,
        observed_treatment_rate=treatment_rate,
        observed_absolute_lift=treatment_rate - control_rate,
        control_users=control_users,
        treatment_users=treatment_users,
        allocation_ratio=allocation_ratio,
        alpha=alpha,
        achieved_power=achieved_power,
        target_power=target_power,
        minimum_detectable_effect=minimum_detectable_effect,
        required_users_per_group=required_per_group,
        required_total_users=required_per_group * 2,
    )


def _achieved_power(
    effect_size: float,
    control_users: int,
    allocation_ratio: float,
    alpha: float,
) -> float:
    if effect_size == 0:
        return alpha
    power = NormalIndPower().power(
        effect_size=effect_size,
        nobs1=control_users,
        alpha=alpha,
        ratio=allocation_ratio,
        alternative="two-sided",
    )
    return float(power)


def _validate_parameters(
    alpha: float,
    target_power: float,
    minimum_detectable_effect: float,
) -> None:
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")
    if not 0 < minimum_detectable_effect < 1:
        raise ValueError("minimum_detectable_effect must be between 0 and 1")
