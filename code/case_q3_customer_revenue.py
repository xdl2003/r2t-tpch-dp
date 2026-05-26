import argparse

from common import (
    add_common_args,
    customer_contributions,
    load_tables,
    print_summary,
    r2t_from_contributions,
    save_result,
)


CASE_NAME = "TPC-H Q3-style customer revenue"
CASE_SLUG = "case_q3_customer_revenue"


QUERY = """
SELECT
    c.C_CUSTKEY,
    SUM(l.L_EXTENDEDPRICE * (1.0 - l.L_DISCOUNT)) AS revenue
FROM Customer c
JOIN Orders o
    ON c.C_CUSTKEY = o.O_CUSTKEY
JOIN Lineitem l
    ON o.O_ORDERKEY = l.L_ORDERKEY
WHERE c.C_MKTSEGMENT = 'BUILDING'
  AND o.O_ORDERDATE < '1995-03-15'
  AND l.L_SHIPDATE > '1995-03-15'
GROUP BY c.C_CUSTKEY
HAVING revenue > 0
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=CASE_NAME)
    add_common_args(parser)
    args = parser.parse_args()

    conn = load_tables(args.data_dir, ["customer", "orders", "lineitem"], args.sample_rows)
    conn.execute("CREATE INDEX idx_orders_custkey ON Orders(O_CUSTKEY)")
    conn.execute("CREATE INDEX idx_lineitem_orderkey ON Lineitem(L_ORDERKEY)")

    contributions = customer_contributions(conn, QUERY)
    result = r2t_from_contributions(
        contributions,
        epsilon=args.epsilon,
        beta=args.beta,
        gsq=args.gsq,
        seed=args.seed,
    )
    print_summary(CASE_NAME, result)
    save_result(
        CASE_SLUG,
        args.output_dir,
        result,
        {
            "epsilon": args.epsilon,
            "beta": args.beta,
            "gsq": args.gsq,
            "seed": args.seed,
            "sample_rows": args.sample_rows,
            "data_dir": str(args.data_dir),
        },
        contributions,
    )


if __name__ == "__main__":
    main()
