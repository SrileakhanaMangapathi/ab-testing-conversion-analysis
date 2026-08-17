# A/B Testing Conversion Analysis

This project evaluates whether a marketing advertisement increased conversion compared with a public-service announcement (PSA). It is an end-to-end analytics product with validated ingestion, reusable statistical analysis, power calculations, a command-line pipeline, machine-readable outputs, an interactive dashboard, an executed notebook, automated tests, CI, container packaging, charts, and a decision memo.

## Result

The advertisement produced a statistically significant improvement in conversion.

| Metric | Advertisement | PSA |
|---|---:|---:|
| Users | 564,577 | 23,524 |
| Conversions | 14,423 | 420 |
| Conversion rate | 2.555% | 1.785% |

- Absolute lift: **0.769 percentage points**
- Relative lift: **43.1%**
- 95% confidence interval: **0.595 to 0.943 percentage points**
- Two-sided p-value: **1.71 × 10⁻¹³**
- Observed power: approximately **100%**

The recommendation is to roll out the advertisement if the expected value of incremental conversions exceeds campaign delivery costs. See [`reports/decision_memo.md`](reports/decision_memo.md) for limitations and business safeguards.

## Repository structure

```text
app.py                          Interactive Streamlit decision dashboard
data/raw/marketing_AB.csv       Source experiment data
data/processed/group_summary.csv Pipeline-generated group summary
notebooks/ab_test_analysis.ipynb Executed reproducible analysis
reports/decision_memo.md         Decision and limitations
reports/analysis_results.json    Machine-readable pipeline result
reports/figures/                 Generated report charts
src/data_prep.py                 Loading, cleaning, and validation
src/stats_tests.py               Conversion inference and confidence interval
src/power_analysis.py            Observed power and sample-size planning
src/pipeline.py                  Reproducible command-line workflow
tests/                           Automated unit tests
.github/workflows/ci.yml         Continuous integration checks
Dockerfile                       Containerized dashboard runtime
```

## Setup

Python 3.12 is recommended. From Command Prompt:

```cmd
cd C:\Users\srile\ab-testing-conversion-analysis
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

From PowerShell, activate with:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts for only the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Reproduce the analysis

Run the complete data and analysis pipeline from the repository root:

```cmd
python -m src.pipeline
```

This validates the raw data and writes:

- `data/processed/group_summary.csv`
- `reports/analysis_results.json`

Run all automated tests from the repository root:

```cmd
python -m pytest
```

Execute the notebook and regenerate its charts:

```cmd
cd notebooks
python -m jupyter nbconvert --to notebook --execute --inplace ab_test_analysis.ipynb --ExecutePreprocessor.timeout=180
cd ..
```

Or open the notebook interactively:

```cmd
cd notebooks
python -m jupyter lab
```

Always confirm the prompt begins with `(.venv)` and `python --version` reports Python 3.12 before running the project.

## Launch the interactive dashboard

From the activated project environment:

```cmd
python -m streamlit run app.py
```

The dashboard opens at `http://localhost:8501` and includes:

- Executive experiment metrics and recommendation
- Conversion-rate comparison
- Confidence interval and test statistics
- Adjustable power and sample-size planning
- Exploratory day/hour breakdowns
- Data-integrity checks
- Downloadable JSON results

Stop the server with `Ctrl+C`.

## Run with Docker

Build and start the container from the repository root:

```cmd
docker build -t ab-testing-dashboard .
docker run --rm -p 8501:8501 ab-testing-dashboard
```

Then open `http://localhost:8501`.

## End-to-end workflow

```text
Raw CSV
  -> schema cleaning and integrity validation
  -> group metrics and statistical inference
  -> power and sample-size planning
  -> CSV/JSON analysis artifacts
  -> notebook, charts, decision memo, and interactive dashboard
  -> automated verification in CI
```

The CI workflow installs the pinned environment, runs all tests, executes the pipeline and notebook, and compiles the application modules on every push and pull request.

## Methodology

The primary metric is user-level conversion. The treatment effect is defined as the advertisement conversion rate minus the PSA conversion rate. Inference uses a two-sided pooled two-proportion z-test at a 5% significance level and an unpooled Wald confidence interval for the absolute difference.

Power planning assumes equal future group allocation, 80% power, a two-sided 5% significance level, and a 0.20 percentage-point minimum detectable effect. Under those assumptions, approximately 72,547 users per group are required.

Day and hour patterns are exploratory and do not drive the rollout decision.

## Data quality and limitations

The dataset contains 588,101 unique users, no missing required values, and no duplicate user IDs. The analysis assumes assignment was randomized, but the data does not document the randomization procedure, experiment duration, or stopping rule. It also measures conversion rather than revenue, profit, retention, or conversion quality.

The original dataset source and redistribution license are not recorded in this repository. Confirm and document provenance before publicly redistributing the raw CSV.
