# Repository Guidelines

## Project Structure & Module Organization

This repository implements two R2T-based cases on the TPC-H dataset. Keep the root focused on project materials:

- `R2T.pdf`: source paper for the Race-to-the-Top algorithm.
- `TPC-H_v3.0.1.pdf`: TPC-H schema and query reference.
- `CLAUDE.md`: existing project notes and algorithm summary.
- `BDT_IP_Differential-privacy/`: reference implementation and local TPC-H `.tbl` data. Consult it only; do not copy code directly.
- `BDT_IP_Differential-privacy/data/`: TPC-H tables such as `customer.tbl`, `orders.tbl`, `lineitem.tbl`, and `supplier.tbl`.
- `BDT_IP_Differential-privacy/result/`: generated plots from the reference project.

For new work, prefer adding project-owned code outside the reference directory, for example `src/`, `notebooks/`, `tests/`, and `results/`.

## Build, Test, and Development Commands

The project is Python/Jupyter based. Use a virtual environment before installing dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy pulp jupyter
jupyter notebook
```

Use `jupyter notebook` to run notebooks. If you add script entry points, document them here, for example `python src/run_case.py --case q3`.

## Coding Style & Naming Conventions

Use Python with 4-space indentation, descriptive snake_case names, and small functions for loading, query construction, optimization, and reporting. Keep algorithm names close to the paper, such as `compute_tau_candidates`, `solve_truncation_lp`, or `select_noisy_max`.

Do not hard-code absolute paths. Use repository-relative paths such as `BDT_IP_Differential-privacy/data/lineitem.tbl`. Keep generated outputs in `results/` or a clearly named case directory.

## Testing Guidelines

No formal test suite exists yet. When adding reusable Python modules, add `pytest` tests under `tests/` with names like `test_tau_selection.py` or `test_tpch_loader.py`.

Prioritize tests for schema parsing, join cardinality assumptions, LP constraints, and deterministic behavior with fixed random seeds. For notebook-only work, include a reproducibility cell listing parameters, seed, input tables, and output files.

## Commit & Pull Request Guidelines

The root history is not currently readable as a normal Git repository, and the reference project has only a terse initial commit. Use concise, imperative commits, for example `Add R2T case runner` or `Validate TPC-H lineitem loader`.

Pull requests should describe the selected TPC-H cases, explain how the implementation maps to `R2T.pdf`, list commands run, and include key result artifacts or screenshots when plots are produced. State clearly when reference-project behavior was consulted and how the submitted implementation differs.

## Agent-Specific Instructions

Implement only two selected TPC-H cases unless the task is explicitly expanded. Treat `BDT_IP_Differential-privacy/` as a reference, not a source to clone. Preserve original papers, data files, and generated reference results unless the user asks to update them.
