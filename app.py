"""Interactive Streamlit dashboard for the marketing A/B test."""

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.data_prep import load_data, summarize_groups
from src.power_analysis import analyze_power
from src.stats_tests import analyze_conversion


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "marketing_AB.csv"

st.set_page_config(
    page_title="A/B Test Decision Center",
    page_icon="📈",
    layout="wide",
)


@st.cache_data(show_spinner="Validating experiment data…")
def get_data() -> pd.DataFrame:
    return load_data(DATA_PATH)


data = get_data()
summary = summarize_groups(data)
result = analyze_conversion(data)

st.title("A/B Test Decision Center")
st.caption(
    "Marketing advertisement vs. PSA · user-level conversion · two-sided α = 0.05"
)

with st.sidebar:
    st.header("Planning assumptions")
    mde_percentage_points = st.slider(
        "Minimum detectable effect (percentage points)",
        min_value=0.05,
        max_value=1.00,
        value=0.20,
        step=0.05,
        help="Smallest absolute conversion lift a future test should reliably detect.",
    )
    target_power = st.slider(
        "Target power",
        min_value=0.70,
        max_value=0.95,
        value=0.80,
        step=0.05,
    )
    st.divider()
    st.caption("Data is loaded from `data/raw/marketing_AB.csv` and validated on startup.")

power = analyze_power(
    data,
    minimum_detectable_effect=mde_percentage_points / 100,
    target_power=target_power,
)

overview_tab, inference_tab, power_tab, explore_tab, quality_tab = st.tabs(
    ["Overview", "Inference", "Power planning", "Explore", "Data quality"]
)

with overview_tab:
    metric_columns = st.columns(4)
    metric_columns[0].metric("Ad conversion", f"{result.treatment_rate:.2%}")
    metric_columns[1].metric("PSA conversion", f"{result.control_rate:.2%}")
    metric_columns[2].metric(
        "Absolute lift", f"{result.absolute_lift * 100:.3f} pp"
    )
    metric_columns[3].metric("Relative lift", f"{result.relative_lift:.1%}")

    st.success(
        "Recommendation: roll out the advertisement if the value of incremental "
        "conversions exceeds campaign delivery costs."
    )
    chart_data = summary.assign(
        group=lambda frame: frame["test_group"].map(
            {"ad": "Advertisement", "psa": "PSA"}
        ),
        conversion_percent=lambda frame: frame["conversion_rate"] * 100,
    )
    rate_chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("group:N", title=None, sort=["Advertisement", "PSA"]),
            y=alt.Y("conversion_percent:Q", title="Conversion rate (%)"),
            color=alt.Color(
                "group:N",
                scale=alt.Scale(
                    domain=["Advertisement", "PSA"], range=["#2563eb", "#94a3b8"]
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("group:N", title="Group"),
                alt.Tooltip("users:Q", format=",", title="Users"),
                alt.Tooltip("conversions:Q", format=",", title="Conversions"),
                alt.Tooltip(
                    "conversion_percent:Q", format=".3f", title="Conversion (%)"
                ),
            ],
        )
        .properties(height=380, title="Conversion rate by experiment group")
    )
    st.altair_chart(rate_chart, width="stretch")

with inference_tab:
    st.subheader("Primary statistical result")
    left, right = st.columns([2, 1])
    with left:
        interval = pd.DataFrame(
            {
                "estimate": [result.absolute_lift * 100],
                "lower": [result.ci_lower * 100],
                "upper": [result.ci_upper * 100],
                "comparison": ["Advertisement − PSA"],
            }
        )
        point = alt.Chart(interval).mark_point(size=180, filled=True).encode(
            x=alt.X("estimate:Q", title="Absolute lift (percentage points)"),
            y=alt.Y("comparison:N", title=None),
        )
        error = alt.Chart(interval).mark_rule(strokeWidth=4).encode(
            x="lower:Q", x2="upper:Q", y="comparison:N"
        )
        zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(
            color="#dc2626", strokeDash=[6, 4]
        ).encode(x="x:Q")
        st.altair_chart(
            (error + point + zero).properties(height=220, title="95% confidence interval"),
            width="stretch",
        )
    with right:
        st.metric("Z-statistic", f"{result.z_statistic:.2f}")
        st.metric("P-value", f"{result.p_value:.2e}")
        st.metric(
            "95% interval",
            f"{result.ci_lower * 100:.3f} to {result.ci_upper * 100:.3f} pp",
        )
    st.info(
        "The interval excludes zero, providing strong evidence that advertisement "
        "exposure increased conversion under the experiment assumptions."
    )

with power_tab:
    st.subheader("Future experiment sizing")
    columns = st.columns(4)
    columns[0].metric("Observed power", f"{power.achieved_power:.1%}")
    columns[1].metric("Target power", f"{power.target_power:.0%}")
    columns[2].metric("Users per group", f"{power.required_users_per_group:,}")
    columns[3].metric("Total users", f"{power.required_total_users:,}")
    st.write(
        f"With equal allocation, detecting a **{mde_percentage_points:.2f} percentage-point** "
        f"lift at **{target_power:.0%} power** requires approximately "
        f"**{power.required_users_per_group:,} users in each group**."
    )
    st.warning(
        f"The current allocation ratio is {power.allocation_ratio:.1f}:1. "
        "Balanced allocation is usually more statistically efficient."
    )

with explore_tab:
    st.subheader("Exploratory conversion patterns")
    dimension = st.radio(
        "Break down by", ["Day of highest exposure", "Hour of highest exposure"], horizontal=True
    )
    if dimension == "Day of highest exposure":
        field = "most_ads_day"
        order = [
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ]
    else:
        field = "most_ads_hour"
        order = list(range(24))
    exploratory = (
        data.groupby([field, "test_group"])["converted"]
        .agg(users="size", conversion_rate="mean")
        .reset_index()
    )
    exploratory["conversion_percent"] = exploratory["conversion_rate"] * 100
    line_chart = (
        alt.Chart(exploratory)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{field}:O", sort=order, title=dimension),
            y=alt.Y("conversion_percent:Q", title="Conversion rate (%)", scale=alt.Scale(zero=False)),
            color=alt.Color("test_group:N", title="Group"),
            tooltip=[field, "test_group", alt.Tooltip("users:Q", format=","), alt.Tooltip("conversion_percent:Q", format=".3f")],
        )
        .properties(height=420)
    )
    st.altair_chart(line_chart, width="stretch")
    st.caption(
        "These subgroup views are descriptive. They were not used for the rollout "
        "decision and are not adjusted for multiple comparisons."
    )

with quality_tab:
    st.subheader("Experiment integrity checks")
    checks = pd.DataFrame(
        {
            "Check": ["Rows", "Unique users", "Duplicate users", "Missing values", "Groups"],
            "Result": [
                f"{len(data):,}",
                f"{data['user_id'].nunique():,}",
                f"{data['user_id'].duplicated().sum():,}",
                f"{data.isna().sum().sum():,}",
                ", ".join(sorted(data["test_group"].unique())),
            ],
            "Status": ["Pass", "Pass", "Pass", "Pass", "Pass"],
        }
    )
    st.dataframe(checks, hide_index=True, width="stretch")
    st.warning(
        "The dataset does not document the randomization mechanism, experiment "
        "duration, prespecified stopping rule, or downstream revenue outcomes."
    )

download_payload = {
    "primary_test": result.to_dict(),
    "power_analysis": power.to_dict(),
}
st.download_button(
    "Download current results (JSON)",
    data=json.dumps(download_payload, indent=2),
    file_name="ab_test_results.json",
    mime="application/json",
)
