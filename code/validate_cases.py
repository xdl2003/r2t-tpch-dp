import argparse
from pathlib import Path

from case_q3_customer_revenue import QUERY as Q3_QUERY
from case_q5_asia_revenue import QUERY as Q5_QUERY
from common import (
    DEFAULT_DATA_DIR,
    customer_contributions,
    load_tables,
    r2t_from_contributions,
)


def validate_result(case_name, result):
    assert result["private_entities"] > 0, f"{case_name}: no contributing customers"
    assert result["true_total"] > 0, f"{case_name}: true total is not positive"
    assert result["best"]["tau"] > 0, f"{case_name}: invalid selected tau"

    previous = -1.0
    for row in result["rows"]:
        truncated = row["truncated"]
        tau = row["tau"]
        assert truncated >= previous, f"{case_name}: truncated values are not monotonic"
        assert truncated <= result["true_total"] + 1e-6, f"{case_name}: truncation exceeded total"
        assert truncated <= tau * result["private_entities"] + 1e-6, (
            f"{case_name}: truncation violated per-customer tau bound"
        )
        previous = truncated


def run_q3(args):
    conn = load_tables(args.data_dir, ["customer", "orders", "lineitem"], args.sample_rows)
    conn.execute("CREATE INDEX idx_orders_custkey ON Orders(O_CUSTKEY)")
    conn.execute("CREATE INDEX idx_lineitem_orderkey ON Lineitem(L_ORDERKEY)")
    contributions = customer_contributions(conn, Q3_QUERY)
    return r2t_from_contributions(contributions, args.epsilon, args.beta, args.gsq, args.seed)


def run_q5(args):
    conn = load_tables(
        args.data_dir,
        ["customer", "orders", "lineitem", "supplier", "nation", "region"],
        args.sample_rows,
    )
    conn.execute("CREATE INDEX idx_orders_custkey ON Orders(O_CUSTKEY)")
    conn.execute("CREATE INDEX idx_lineitem_orderkey ON Lineitem(L_ORDERKEY)")
    conn.execute("CREATE INDEX idx_lineitem_suppkey ON Lineitem(L_SUPPKEY)")
    conn.execute("CREATE INDEX idx_supplier_nationkey ON Supplier(S_NATIONKEY)")
    contributions = customer_contributions(conn, Q5_QUERY)
    return r2t_from_contributions(contributions, args.epsilon, args.beta, args.gsq, args.seed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the two R2T TPC-H cases.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--epsilon", type=float, default=0.8)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--gsq", type=float, default=100_000.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--sample-rows", type=int, default=10_000)
    args = parser.parse_args()

    checks = [
        ("TPC-H Q3-style customer revenue", run_q3(args)),
        ("TPC-H Q5-style ASIA revenue", run_q5(args)),
    ]
    for case_name, result in checks:
        validate_result(case_name, result)
        print(f"ok: {case_name}")


if __name__ == "__main__":
    main()
