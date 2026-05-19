import csv
import json
import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
REPORT = ROOT / "report.pdf"
GITHUB_URL = "https://github.com/xdl2003/r2t-tpch-dp"

PAGE_W, PAGE_H = 1240, 1754
MARGIN = 90


def font(name, size):
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}.ttf", size)


FONT_TITLE = font("DejaVuSans-Bold", 42)
FONT_H1 = font("DejaVuSans-Bold", 32)
FONT_H2 = font("DejaVuSans-Bold", 24)
FONT_BODY = font("DejaVuSans", 20)
FONT_SMALL = font("DejaVuSans", 16)
FONT_MONO = font("DejaVuSansMono", 16)


def new_page():
    return Image.new("RGB", (PAGE_W, PAGE_H), "white")


def draw_wrapped(draw, text, x, y, width_chars=90, font_obj=FONT_BODY, line_gap=8, fill=(20, 20, 20)):
    for paragraph in text.split("\n"):
        lines = textwrap.wrap(paragraph, width=width_chars) or [""]
        for line in lines:
            draw.text((x, y), line, font=font_obj, fill=fill)
            y += font_obj.size + line_gap
        y += line_gap
    return y


def draw_title(draw, text, y):
    draw.text((MARGIN, y), text, font=FONT_H1, fill=(0, 45, 90))
    return y + 58


def read_summary(name):
    return json.loads((RESULTS / f"{name}_summary.json").read_text())


def read_candidates(name):
    with (RESULTS / f"{name}_candidates.csv").open(newline="") as f:
        return [
            {
                "tau": float(row["tau"]),
                "truncated": float(row["truncated"]),
                "noisy_score": float(row["noisy_score"]),
            }
            for row in csv.DictReader(f)
        ]


def save_algorithm_flow():
    img = Image.new("RGB", (1100, 620), "white")
    d = ImageDraw.Draw(img)
    d.text((350, 35), "R2T Processing Flow", font=FONT_H1, fill=(0, 45, 90))
    boxes = [
        (60, 220, 200, 90, "TPC-H .tbl\nfiles"),
        (320, 220, 200, 90, "SQLite\ncase SQL"),
        (580, 220, 220, 90, "Customer\ncontributions"),
        (860, 220, 200, 90, "R2T tau\nrace"),
        (430, 430, 250, 90, "Saved JSON/CSV\nresults"),
    ]
    for x, y, w, h, label in boxes:
        d.rounded_rectangle((x, y, x + w, y + h), radius=10, outline=(30, 70, 120), width=3, fill=(236, 244, 255))
        for i, line in enumerate(label.split("\n")):
            d.text((x + 24, y + 20 + i * 26), line, font=FONT_BODY, fill=(0, 0, 0))
    for x1, y1, x2, y2 in [(260, 265, 320, 265), (520, 265, 580, 265), (800, 265, 860, 265), (960, 310, 680, 430)]:
        d.line((x1, y1, x2, y2), fill=(30, 70, 120), width=4)
    d.text((260, 360), "Q3 and Q5 are implemented as separate scripts.", font=FONT_BODY, fill=(40, 40, 40))
    path = FIGURES / "algorithm_flow.png"
    img.save(path)
    return path


def save_schema_cases():
    img = Image.new("RGB", (1100, 620), "white")
    d = ImageDraw.Draw(img)
    d.text((235, 35), "TPC-H Relations Used by the Two Cases", font=FONT_H1, fill=(0, 45, 90))
    nodes = {
        "Customer": (80, 240),
        "Orders": (330, 240),
        "Lineitem": (580, 240),
        "Supplier": (830, 240),
        "Nation": (455, 420),
        "Region": (705, 420),
    }
    for name, (x, y) in nodes.items():
        fill = (255, 243, 218) if name == "Customer" else (240, 240, 240)
        d.rounded_rectangle((x, y, x + 170, y + 70), radius=8, outline=(70, 70, 70), width=3, fill=fill)
        d.text((x + 26, y + 23), name, font=FONT_BODY, fill=(0, 0, 0))
    for edge in [(250, 275, 330, 275), (500, 275, 580, 275), (750, 275, 830, 275), (540, 420, 170, 310), (915, 310, 540, 420), (625, 455, 705, 455)]:
        d.line(edge, fill=(80, 80, 80), width=4)
    d.text((80, 135), "Q3-style: Customer -> Orders -> Lineitem", font=FONT_BODY, fill=(0, 0, 0))
    d.text((80, 170), "Q5-style: adds Supplier, Nation, and Region", font=FONT_BODY, fill=(0, 0, 0))
    d.text((80, 540), "Privacy unit: one Customer and its referencing tuples.", font=FONT_BODY, fill=(0, 0, 0))
    path = FIGURES / "schema_cases.png"
    img.save(path)
    return path


def save_candidate_chart(name, title, filename):
    rows = read_candidates(name)
    summary = read_summary(name)
    img = Image.new("RGB", (1100, 620), "white")
    d = ImageDraw.Draw(img)
    d.text((300, 30), title, font=FONT_H1, fill=(0, 45, 90))
    left, top, w, h = 90, 100, 890, 390
    bottom = top + h
    d.line((left, top, left, bottom), fill=(0, 0, 0), width=3)
    d.line((left, bottom, left + w, bottom), fill=(0, 0, 0), width=3)
    xs = [math.log2(r["tau"]) for r in rows]
    trunc = [r["truncated"] / 1_000_000 for r in rows]
    noisy = [r["noisy_score"] / 1_000_000 for r in rows]
    y_min, y_max = min(0, min(noisy)), max(max(trunc), max(noisy))
    x_min, x_max = min(xs), max(xs)

    def tx(x):
        return left + (x - x_min) / (x_max - x_min) * w

    def ty(y):
        return bottom - (y - y_min) / (y_max - y_min) * h

    for i in range(6):
        y = y_min + (y_max - y_min) * i / 5
        yy = ty(y)
        d.line((left - 8, yy, left, yy), fill=(0, 0, 0), width=2)
        d.text((20, yy - 10), f"{y:.0f}", font=FONT_SMALL, fill=(0, 0, 0))
    for power in [1, 5, 10, 15, 20, 23]:
        if x_min <= power <= x_max:
            xx = tx(power)
            d.line((xx, bottom, xx, bottom + 8), fill=(0, 0, 0), width=2)
            d.text((xx - 8, bottom + 14), str(power), font=FONT_SMALL, fill=(0, 0, 0))

    trunc_points = [(tx(x), ty(y)) for x, y in zip(xs, trunc)]
    noisy_points = [(tx(x), ty(y)) for x, y in zip(xs, noisy)]
    d.line(trunc_points, fill=(0, 70, 180), width=4)
    d.line(noisy_points, fill=(190, 35, 25), width=4)
    selected = math.log2(float(summary["selected"]["tau"]))
    d.line((tx(selected), top, tx(selected), bottom), fill=(0, 130, 50), width=3)
    d.text((720, 520), "blue: truncated", font=FONT_SMALL, fill=(0, 70, 180))
    d.text((720, 545), "red: noisy score", font=FONT_SMALL, fill=(190, 35, 25))
    d.text((720, 570), f"selected tau={summary['selected']['tau']:.0f}", font=FONT_SMALL, fill=(0, 130, 50))
    d.text((450, 535), "log2(tau)", font=FONT_BODY, fill=(0, 0, 0))
    d.text((20, 75), "million", font=FONT_SMALL, fill=(0, 0, 0))
    path = FIGURES / filename
    img.save(path)
    return path


def add_image(page, path, x, y, width):
    img = Image.open(path).convert("RGB")
    ratio = width / img.width
    img = img.resize((width, int(img.height * ratio)))
    page.paste(img, (x, y))
    return y + img.height


def make_report():
    FIGURES.mkdir(exist_ok=True)
    schema = save_schema_cases()
    flow = save_algorithm_flow()
    q3_chart = save_candidate_chart("case_q3_customer_revenue", "Q3-style R2T Candidate Values", "q3_r2t_candidates.png")
    q5_chart = save_candidate_chart("case_q5_asia_revenue", "Q5-style R2T Candidate Values", "q5_r2t_candidates.png")
    q3 = read_summary("case_q3_customer_revenue")
    q5 = read_summary("case_q5_asia_revenue")

    pages = []

    page = new_page()
    d = ImageDraw.Draw(page)
    y = 230
    d.text((MARGIN, y), "CSIT6910", font=FONT_TITLE, fill=(0, 45, 90))
    y += 75
    d.text((MARGIN, y), "Independent Project Report", font=FONT_H1, fill=(0, 45, 90))
    y += 90
    d.text((MARGIN, y), "R2T-Based Differentially Private", font=FONT_TITLE, fill=(0, 0, 0))
    y += 60
    d.text((MARGIN, y), "Query Evaluation on TPC-H", font=FONT_TITLE, fill=(0, 0, 0))
    y += 130
    for line in [
        "Name: Xu Dongliu",
        "Student ID: 21208710",
        "Instructor: Ke Yi",
        "Semester: 2025-26 Spring",
        "Date: May 19, 2026",
    ]:
        d.text((MARGIN, y), line, font=FONT_BODY, fill=(0, 0, 0))
        y += 42
    pages.append(page)

    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Project Overview", MARGIN)
    text = (
        "Differential privacy protects the contribution of one private entity when query answers are released. "
        "In TPC-H, one customer may reference many orders and lineitems, so a join-and-aggregate query may have large sensitivity. "
        "R2T addresses this by evaluating geometrically increasing truncation thresholds and selecting a noisy penalized candidate.\n\n"
        "This project implements two concrete TPC-H revenue cases rather than a general SQL engine. Both cases designate Customer as the private relation. "
        "The Q3-style case uses Customer, Orders, and Lineitem. The Q5-style case additionally uses Supplier, Nation, and Region."
    )
    y = draw_wrapped(d, text, MARGIN, y)
    add_image(page, schema, MARGIN, y + 30, 980)
    pages.append(page)

    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Algorithm Design", MARGIN)
    y = add_image(page, flow, MARGIN, y, 980) + 35
    text = (
        "For each case, the program loads the required .tbl files into SQLite and computes each customer's revenue contribution. "
        "For a candidate threshold tau, the truncated query value is sum(min(customer_contribution, tau)). "
        "Because the implemented cases are self-join-free and protect customers, this is the closed-form equivalent of the corresponding LP truncation.\n\n"
        "R2T evaluates tau = 2, 4, 8, ..., GS_Q. For each tau it adds Laplace noise with scale log2(GS_Q) * tau / epsilon, subtracts the R2T penalty term, and returns max(0, max noisy candidate)."
    )
    draw_wrapped(d, text, MARGIN, y)
    pages.append(page)

    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Implemented Queries", MARGIN)
    y = draw_wrapped(d, "Q3-style customer revenue keeps BUILDING customers, orders before 1995-03-15, and lineitems shipped after 1995-03-15.", MARGIN, y)
    code = [
        "SELECT c.C_CUSTKEY, SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT))",
        "FROM Customer c JOIN Orders o ON c.C_CUSTKEY = o.O_CUSTKEY",
        "JOIN Lineitem l ON o.O_ORDERKEY = l.L_ORDERKEY",
        "WHERE c.C_MKTSEGMENT = 'BUILDING'",
        "  AND o.O_ORDERDATE < '1995-03-15'",
        "  AND l.L_SHIPDATE > '1995-03-15'",
        "GROUP BY c.C_CUSTKEY;",
    ]
    for line in code:
        d.text((MARGIN + 20, y), line, font=FONT_MONO, fill=(30, 30, 30))
        y += 28
    y += 35
    y = draw_wrapped(d, "Q5-style ASIA revenue keeps 1994 ASIA region records and requires customer and supplier nation to match.", MARGIN, y)
    code = [
        "SELECT c.C_CUSTKEY, SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT))",
        "FROM Customer c JOIN Orders o ON c.C_CUSTKEY = o.O_CUSTKEY",
        "JOIN Lineitem l ON o.O_ORDERKEY = l.L_ORDERKEY",
        "JOIN Supplier s ON l.L_SUPPKEY = s.S_SUPPKEY",
        "JOIN Nation n ON c.C_NATIONKEY = n.N_NATIONKEY",
        "             AND s.S_NATIONKEY = n.N_NATIONKEY",
        "JOIN Region r ON n.N_REGIONKEY = r.R_REGIONKEY",
        "WHERE r.R_NAME = 'ASIA' AND o.O_ORDERDATE >= '1994-01-01'",
        "  AND o.O_ORDERDATE < '1995-01-01'",
        "GROUP BY c.C_CUSTKEY;",
    ]
    for line in code:
        d.text((MARGIN + 20, y), line, font=FONT_MONO, fill=(30, 30, 30))
        y += 28
    pages.append(page)

    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Experiment Results", MARGIN)
    rows = [
        ("Metric", "Q3-style", "Q5-style"),
        ("Contributing customers", f"{q3['private_entities']}", f"{q5['private_entities']}"),
        ("True SQL total", f"{q3['true_total']:,.2f}", f"{q5['true_total']:,.2f}"),
        ("Max customer contribution", f"{q3['max_contribution']:,.2f}", f"{q5['max_contribution']:,.2f}"),
        ("Selected tau", f"{q3['selected']['tau']:,.0f}", f"{q5['selected']['tau']:,.0f}"),
        ("Truncated at tau", f"{q3['selected']['truncated']:,.2f}", f"{q5['selected']['truncated']:,.2f}"),
        ("R2T noisy output", f"{q3['r2t_output']:,.2f}", f"{q5['r2t_output']:,.2f}"),
    ]
    x0, col_w = MARGIN, [430, 280, 280]
    for r, row in enumerate(rows):
        x = x0
        h = 54
        fill = (230, 238, 250) if r == 0 else (255, 255, 255)
        for c, cell in enumerate(row):
            d.rectangle((x, y, x + col_w[c], y + h), outline=(80, 80, 80), fill=fill)
            d.text((x + 12, y + 16), cell, font=FONT_SMALL if r else FONT_H2, fill=(0, 0, 0))
            x += col_w[c]
        y += h
    y += 35
    draw_wrapped(d, "Validation passed for both cases: positive output, monotone truncation, no truncation above the SQL total, and the tau * customer_count bound.", MARGIN, y)
    pages.append(page)

    for title, chart in [("Q3 Candidate Chart", q3_chart), ("Q5 Candidate Chart", q5_chart)]:
        page = new_page()
        d = ImageDraw.Draw(page)
        y = draw_title(d, title, MARGIN)
        add_image(page, chart, MARGIN, y + 20, 980)
        pages.append(page)

    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Comparison and Conclusion", MARGIN)
    text = (
        "The reference notebook was used only for orientation. It uses pandas, SQLite, and PuLP to demonstrate one Supplier-Lineitem-Orders-Customer revenue join. "
        "This project instead implements two separate Python scripts, saves reproducible outputs, and uses the closed-form truncation for selected self-join-free customer-private queries.\n\n"
        "The project demonstrates how R2T can be applied to concrete foreign-key relational queries without implementing a full private SQL engine. "
        "Outputs are stored in results/, figures are stored in figures/, and validation is provided by code/validate_cases.py.\n\n"
        f"Public GitHub repository: {GITHUB_URL}"
    )
    draw_wrapped(d, text, MARGIN, y)
    pages.append(page)

    meetings = [
        ("1st Project Meeting", "Saturday, February 7, 2026", "Discussed R2T paper, TPC-H data, and initial project direction."),
        ("2nd Project Meeting", "Tuesday, March 17, 2026", "Reviewed the R2T truncation mechanism and selected two concrete TPC-H cases."),
        ("3rd Project Meeting", "Tuesday, April 21, 2026", "Discussed implementation progress, customer-level contributions, and saved outputs."),
        ("4th Project Meeting", "Tuesday, May 19, 2026", "Reviewed final report, validation results, generated figures, and repository link."),
    ]
    page = new_page()
    d = ImageDraw.Draw(page)
    y = draw_title(d, "Meeting Minutes", MARGIN)
    for title, date, body in meetings:
        d.text((MARGIN, y), title, font=FONT_H2, fill=(0, 45, 90))
        y += 36
        d.text((MARGIN + 20, y), f"Date: {date}", font=FONT_BODY, fill=(0, 0, 0))
        y += 34
        y = draw_wrapped(d, body, MARGIN + 20, y, width_chars=82)
        y += 24
    pages.append(page)

    pages[0].save(REPORT, save_all=True, append_images=pages[1:], resolution=150)
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    make_report()
