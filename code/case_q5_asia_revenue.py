import argparse

from common import (
    add_common_args,
    customer_contributions,
    display_path,
    load_tables,
    print_summary,
    r2t_from_contributions,
    save_result,
)


CASE_NAME = "TPC-H Q5-style ASIA revenue"
CASE_SLUG = "case_q5_asia_revenue"


QUERY = """
SELECT
    c.C_CUSTKEY,
    SUM(l.L_EXTENDEDPRICE * (1.0 - l.L_DISCOUNT)) AS revenue
FROM Customer c
JOIN Orders o
    ON c.C_CUSTKEY = o.O_CUSTKEY
JOIN Lineitem l
    ON o.O_ORDERKEY = l.L_ORDERKEY
JOIN Supplier s
    ON l.L_SUPPKEY = s.S_SUPPKEY
JOIN Nation n
    ON c.C_NATIONKEY = n.N_NATIONKEY
   AND s.S_NATIONKEY = n.N_NATIONKEY
JOIN Region r
    ON n.N_REGIONKEY = r.R_REGIONKEY
WHERE r.R_NAME = 'ASIA'
  AND o.O_ORDERDATE >= '1994-01-01'
  AND o.O_ORDERDATE < '1995-01-01'
GROUP BY c.C_CUSTKEY
HAVING revenue > 0
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=CASE_NAME)
    add_common_args(parser)
    args = parser.parse_args()

    conn = load_tables(
        args.data_dir,
        ["customer", "orders", "lineitem", "supplier", "nation", "region"],
        args.sample_rows,
    )
    conn.execute("CREATE INDEX idx_orders_custkey ON Orders(O_CUSTKEY)")
    conn.execute("CREATE INDEX idx_lineitem_orderkey ON Lineitem(L_ORDERKEY)")
    conn.execute("CREATE INDEX idx_lineitem_suppkey ON Lineitem(L_SUPPKEY)")
    conn.execute("CREATE INDEX idx_supplier_nationkey ON Supplier(S_NATIONKEY)")

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
            "data_dir": display_path(args.data_dir),
        },
        contributions,
    )


if __name__ == "__main__":
    main()
