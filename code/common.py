import argparse
import csv
import json
import math
import random
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data"
DEFAULT_OUTPUT_DIR = ROOT / "results"


TABLES = {
    "customer": (
        "Customer",
        [
            "C_CUSTKEY INTEGER",
            "C_NAME TEXT",
            "C_ADDRESS TEXT",
            "C_NATIONKEY INTEGER",
            "C_PHONE TEXT",
            "C_ACCTBAL REAL",
            "C_MKTSEGMENT TEXT",
            "C_COMMENT TEXT",
        ],
    ),
    "orders": (
        "Orders",
        [
            "O_ORDERKEY INTEGER",
            "O_CUSTKEY INTEGER",
            "O_ORDERSTATUS TEXT",
            "O_TOTALPRICE REAL",
            "O_ORDERDATE TEXT",
            "O_ORDERPRIORITY TEXT",
            "O_CLERK TEXT",
            "O_SHIPPRIORITY INTEGER",
            "O_COMMENT TEXT",
        ],
    ),
    "lineitem": (
        "Lineitem",
        [
            "L_ORDERKEY INTEGER",
            "L_PARTKEY INTEGER",
            "L_SUPPKEY INTEGER",
            "L_LINENUMBER INTEGER",
            "L_QUANTITY REAL",
            "L_EXTENDEDPRICE REAL",
            "L_DISCOUNT REAL",
            "L_TAX REAL",
            "L_RETURNFLAG TEXT",
            "L_LINESTATUS TEXT",
            "L_SHIPDATE TEXT",
            "L_COMMITDATE TEXT",
            "L_RECEIPTDATE TEXT",
            "L_SHIPINSTRUCT TEXT",
            "L_SHIPMODE TEXT",
            "L_COMMENT TEXT",
        ],
    ),
    "supplier": (
        "Supplier",
        [
            "S_SUPPKEY INTEGER",
            "S_NAME TEXT",
            "S_ADDRESS TEXT",
            "S_NATIONKEY INTEGER",
            "S_PHONE TEXT",
            "S_ACCTBAL REAL",
            "S_COMMENT TEXT",
        ],
    ),
    "nation": (
        "Nation",
        [
            "N_NATIONKEY INTEGER",
            "N_NAME TEXT",
            "N_REGIONKEY INTEGER",
            "N_COMMENT TEXT",
        ],
    ),
    "region": (
        "Region",
        [
            "R_REGIONKEY INTEGER",
            "R_NAME TEXT",
            "R_COMMENT TEXT",
        ],
    ),
}


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--epsilon", type=float, default=0.8)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--gsq", type=float, default=10_000_000.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="Optional per-table row cap for fast smoke tests.",
    )


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_tables(data_dir: Path, table_names, sample_rows=None) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    for key in table_names:
        table_name, columns = TABLES[key]
        conn.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        path = data_dir / f"{key}.tbl"
        rows = []
        with path.open(newline="") as f:
            reader = csv.reader(f, delimiter="|")
            for i, row in enumerate(reader):
                if sample_rows is not None and i >= sample_rows:
                    break
                rows.append(row[:-1])
                if len(rows) >= 10_000:
                    conn.executemany(insert_sql, rows)
                    rows.clear()
        if rows:
            conn.executemany(insert_sql, rows)
    conn.commit()
    return conn


def customer_contributions(conn: sqlite3.Connection, query: str):
    rows = conn.execute(query).fetchall()
    return [(int(custkey), float(value or 0.0)) for custkey, value in rows]


def tau_candidates(gsq: float):
    max_power = int(math.floor(math.log2(gsq)))
    return [2.0**j for j in range(1, max_power + 1)]


def laplace(rng: random.Random, scale: float) -> float:
    u = rng.random() - 0.5
    return -scale * math.copysign(math.log(1.0 - 2.0 * abs(u)), u)


def r2t_from_contributions(contributions, epsilon, beta, gsq, seed):
    log_g = math.log2(gsq)
    penalty_factor = log_g * math.log(log_g / beta) / epsilon
    rng = random.Random(seed)
    total = sum(value for _, value in contributions)
    rows = []

    for tau in tau_candidates(gsq):
        truncated = sum(min(value, tau) for _, value in contributions)
        noise_scale = log_g * tau / epsilon
        noisy_score = truncated + laplace(rng, noise_scale) - penalty_factor * tau
        rows.append(
            {
                "tau": tau,
                "truncated": truncated,
                "noise_scale": noise_scale,
                "noisy_score": noisy_score,
            }
        )

    best = max(rows, key=lambda item: item["noisy_score"])
    q0_value = 0.0
    r2t_output = max(best["noisy_score"], q0_value)
    max_contribution = max((value for _, value in contributions), default=0.0)
    return {
        "true_total": total,
        "private_entities": len(contributions),
        "max_contribution": max_contribution,
        "q0_value": q0_value,
        "r2t_output": r2t_output,
        "q0_selected": r2t_output == q0_value and best["noisy_score"] < q0_value,
        "best": best,
        "rows": rows,
    }


def print_summary(case_name: str, result) -> None:
    best = result["best"]
    print(f"case: {case_name}")
    print(f"private relation: Customer")
    print(f"private entities with nonzero contribution: {result['private_entities']}")
    print(f"true SQL total: {result['true_total']:.2f}")
    print(f"max customer contribution: {result['max_contribution']:.2f}")
    print(f"selected tau: {best['tau']:.0f}")
    print(f"truncated value at tau: {best['truncated']:.2f}")
    print(f"r2t noisy output: {result['r2t_output']:.2f}")
    print(f"noise scale at tau: {best['noise_scale']:.2f}")
    print("top noisy candidates:")
    for row in sorted(result["rows"], key=lambda item: item["noisy_score"], reverse=True)[:5]:
        print(
            "  tau={tau:.0f} truncated={truncated:.2f} noisy={noisy_score:.2f}".format(
                **row
            )
        )


def contribution_quantiles(contributions):
    values = sorted(value for _, value in contributions)
    if not values:
        return {}

    def percentile(q):
        position = (len(values) - 1) * q
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return values[int(position)]
        weight = position - lower
        return values[lower] * (1.0 - weight) + values[upper] * weight

    return {
        "p50": percentile(0.50),
        "p75": percentile(0.75),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
    }


def save_result(case_slug: str, output_dir: Path, result, params, contributions=None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{case_slug}_summary.json"
    candidates_path = output_dir / f"{case_slug}_candidates.csv"
    contributions_path = output_dir / f"{case_slug}_contributions.csv"

    summary = {
        "case": case_slug,
        "params": params,
        "true_total": result["true_total"],
        "private_entities": result["private_entities"],
        "max_contribution": result["max_contribution"],
        "q0_value": result["q0_value"],
        "q0_selected": result["q0_selected"],
        "r2t_output": result["r2t_output"],
        "selected": result["best"],
    }
    if contributions is not None:
        summary["contribution_quantiles"] = contribution_quantiles(contributions)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with candidates_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tau", "truncated", "noise_scale", "noisy_score"],
        )
        writer.writeheader()
        writer.writerows(result["rows"])

    if contributions is not None:
        with contributions_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["custkey", "contribution"])
            writer.writeheader()
            for custkey, contribution in sorted(contributions, key=lambda item: item[1], reverse=True):
                writer.writerow({"custkey": custkey, "contribution": contribution})

    print(f"saved summary: {summary_path}")
    print(f"saved candidates: {candidates_path}")
    if contributions is not None:
        print(f"saved contributions: {contributions_path}")
