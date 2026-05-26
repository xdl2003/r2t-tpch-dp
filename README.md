# R2T-Based Differentially Private Query Evaluation on TPC-H

This project implements two concrete TPC-H revenue query cases using the
R2T (Race-to-the-Top) truncation idea for differentially private query
evaluation with foreign-key relationships.

## Implemented Cases

- `case_q3_customer_revenue.py`: TPC-H Q3-style customer revenue query.
- `case_q5_asia_revenue.py`: TPC-H Q5-style ASIA revenue query.

Both cases use `Customer` as the private relation. The implementation
loads local TPC-H `.tbl` files, computes each customer's contribution,
applies R2T candidate thresholds, adds Laplace noise and the R2T penalty,
then saves reproducible JSON and CSV outputs.

## Run

```bash
python3 code/case_q3_customer_revenue.py --seed 1
python3 code/case_q5_asia_revenue.py --seed 1
python3 code/validate_cases.py
python3 code/generate_report_figures.py
```

The default data path is:

```text
data
```

The TPC-H `.tbl` files used by the scripts are stored under this project
data directory. You can also pass `--data-dir /path/to/tpch/data` to use
another generated TPC-H dataset.

## Outputs

Results are saved under `results/`:

- `*_summary.json`: parameters, selected tau, true total, and R2T output.
- `*_candidates.csv`: all candidate tau values and noisy scores.
- `*_contributions.csv`: per-customer pre-truncation revenue contributions.

Report figures are saved under `figures/`, and the report source is
`report.tex`.
