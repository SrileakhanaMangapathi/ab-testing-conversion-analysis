"""Statistical inference for the primary conversion metric."""

from dataclasses import asdict, dataclass
from math import sqrt

import pandas as pd
from scipy.stats import norm

from src.data_prep import validate_data


@dataclass(frozen=True)
class ProportionTestResult:
    """Results from a two-sided comparison of two conversion proportions."""

    treatment_group: str
    control_group: str
    treatment_users: int
    control_users: int
    treatment_conversions: int
    control_conversions: int
    treatment_rate: float
    control_rate: float
    absolute_lift: float
    relative_lift: float
    confidence_level: float
    ci_lower: float
    ci_upper: float
    z_statistic: float
    p_value: float
    statistically_significant: bool

    def to_dict(self) -> dict[str, str | int | float | bool]:
        """Return a serialization-friendly representation of the result."""
        return asdict(self)


def two_proportion_z_test(
    treatment_conversions: int,
    treatment_users: int,
    control_conversions: int,
    control_users: int,
    *,
    alpha: float = 0.05,
) -> tuple[float, float, float, float]:
    """Return z, two-sided p-value, and a Wald CI for treatment minus control."""
    _validate_counts(treatment_conversions, treatment_users, "treatment")
    _validate_counts(control_conversions, control_users, "control")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    treatment_rate = treatment_conversions / treatment_users
    control_rate = control_conversions / control_users
    difference = treatment_rate - control_rate

    pooled_rate = (
        treatment_conversions + control_conversions
    ) / (treatment_users + control_users)
    null_standard_error = sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (1 / treatment_users + 1 / control_users)
    )
    if null_standard_error == 0:
        z_statistic = 0.0 if difference == 0 else float("inf")
        p_value = 1.0 if difference == 0 else 0.0
    else:
        z_statistic = difference / null_standard_error
        p_value = float(2 * norm.sf(abs(z_statistic)))

    ci_standard_error = sqrt(
        treatment_rate * (1 - treatment_rate) / treatment_users
        + control_rate * (1 - control_rate) / control_users
    )
    critical_value = float(norm.ppf(1 - alpha / 2))
    ci_lower = float(difference - critical_value * ci_standard_error)
    ci_upper = float(difference + critical_value * ci_standard_error)
    return z_statistic, p_value, ci_lower, ci_upper


def analyze_conversion(
    data: pd.DataFrame,
    *,
    treatment_group: str = "ad",
    control_group: str = "psa",
    alpha: float = 0.05,
) -> ProportionTestResult:
    """Compare conversion rates for treatment and control experiment groups."""
    validate_data(data)
    if treatment_group == control_group:
        raise ValueError("Treatment and control groups must be different")

    available_groups = set(data["test_group"].unique())
    requested_groups = {treatment_group, control_group}
    if not requested_groups.issubset(available_groups):
        raise ValueError(
            f"Requested groups {sorted(requested_groups)} are not both present"
        )

    treatment = data.loc[data["test_group"] == treatment_group, "converted"]
    control = data.loc[data["test_group"] == control_group, "converted"]
    treatment_users = int(treatment.size)
    control_users = int(control.size)
    treatment_conversions = int(treatment.sum())
    control_conversions = int(control.sum())
    treatment_rate = treatment_conversions / treatment_users
    control_rate = control_conversions / control_users
    absolute_lift = treatment_rate - control_rate
    relative_lift = (
        absolute_lift / control_rate if control_rate > 0 else float("inf")
    )

    z_statistic, p_value, ci_lower, ci_upper = two_proportion_z_test(
        treatment_conversions,
        treatment_users,
        control_conversions,
        control_users,
        alpha=alpha,
    )
    return ProportionTestResult(
        treatment_group=treatment_group,
        control_group=control_group,
        treatment_users=treatment_users,
        control_users=control_users,
        treatment_conversions=treatment_conversions,
        control_conversions=control_conversions,
        treatment_rate=treatment_rate,
        control_rate=control_rate,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        confidence_level=1 - alpha,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        z_statistic=z_statistic,
        p_value=p_value,
        statistically_significant=bool(p_value < alpha),
    )


def _validate_counts(conversions: int, users: int, label: str) -> None:
    if not isinstance(conversions, int) or not isinstance(users, int):
        raise TypeError(f"{label} conversions and users must be integers")
    if users <= 0:
        raise ValueError(f"{label} users must be positive")
    if conversions < 0 or conversions > users:
        raise ValueError(f"{label} conversions must be between 0 and users")
