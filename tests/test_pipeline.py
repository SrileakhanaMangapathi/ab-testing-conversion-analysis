import json

import pandas as pd

from src.pipeline import run_pipeline


def test_pipeline_writes_machine_readable_outputs(tmp_path):
    input_path = tmp_path / "experiment.csv"
    output_dir = tmp_path / "processed"
    reports_dir = tmp_path / "reports"
    data = pd.DataFrame(
        {
            "user id": range(200),
            "test group": ["ad"] * 100 + ["psa"] * 100,
            "converted": [True] * 20 + [False] * 80 + [True] * 10 + [False] * 90,
            "total ads": [1] * 200,
            "most ads day": ["Monday"] * 200,
            "most ads hour": [12] * 200,
        }
    )
    data.to_csv(input_path, index=False)

    results = run_pipeline(
        input_path,
        output_dir,
        reports_dir,
        minimum_detectable_effect=0.05,
    )

    assert (output_dir / "group_summary.csv").is_file()
    results_path = reports_dir / "analysis_results.json"
    assert results_path.is_file()
    saved = json.loads(results_path.read_text(encoding="utf-8"))
    assert saved == results
    assert saved["primary_test"]["absolute_lift"] == 0.1
    assert saved["recommendation"] == "roll_out_if_economically_positive"
