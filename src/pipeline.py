"""Command-line pipeline that produces reusable experiment result artifacts."""

import argparse
import json
from pathlib import Path
from typing import Any

from src.data_prep import load_data, summarize_groups
from src.power_analysis import analyze_power
from src.stats_tests import analyze_conversion


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "marketing_AB.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed"
DEFAULT_REPORTS = PROJECT_ROOT / "reports"


def run_pipeline(
    input_path: str | Path = DEFAULT_INPUT,
    output_dir: str | Path = DEFAULT_OUTPUT,
    reports_dir: str | Path = DEFAULT_REPORTS,
    *,
    minimum_detectable_effect: float = 0.002,
) -> dict[str, Any]:
    """Validate input, run the analysis, and write CSV/JSON output artifacts."""
    output_dir = Path(output_dir)
    reports_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(input_path)
    group_summary = summarize_groups(data)
    test_result = analyze_conversion(data)
    power_result = analyze_power(
        data, minimum_detectable_effect=minimum_detectable_effect
    )

    quality = {
        "rows": len(data),
        "unique_users": int(data["user_id"].nunique()),
        "duplicate_users": int(data["user_id"].duplicated().sum()),
        "missing_values": int(data.isna().sum().sum()),
    }
    results: dict[str, Any] = {
        "data_quality": quality,
        "primary_test": test_result.to_dict(),
        "power_analysis": power_result.to_dict(),
        "recommendation": (
            "roll_out_if_economically_positive"
            if test_result.statistically_significant
            and test_result.ci_lower > 0
            else "do_not_roll_out_or_continue_testing"
        ),
    }

    group_summary.to_csv(output_dir / "group_summary.csv", index=False)
    (reports_dir / "analysis_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the marketing A/B testing analysis pipeline."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument(
        "--mde",
        type=float,
        default=0.002,
        help="Absolute minimum detectable conversion effect (default: 0.002).",
    )
    args = parser.parse_args()
    results = run_pipeline(
        args.input,
        args.output_dir,
        args.reports_dir,
        minimum_detectable_effect=args.mde,
    )
    primary = results["primary_test"]
    print("Analysis complete")
    print(f"Absolute lift: {primary['absolute_lift']:.4%}")
    print(f"P-value: {primary['p_value']:.3g}")
    print(f"Recommendation: {results['recommendation']}")


if __name__ == "__main__":
    main()
