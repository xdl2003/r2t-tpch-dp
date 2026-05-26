import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = ROOT / "figures"
RESULT_DIR = ROOT / "results"


class PdfCanvas:
    def __init__(self, path, width=720, height=420):
        self.path = Path(path)
        self.width = width
        self.height = height
        self.commands = []

    def _escape(self, text):
        return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def line(self, x1, y1, x2, y2, width=1, color=(0, 0, 0)):
        self.commands.append(
            f"{color[0]} {color[1]} {color[2]} RG {width} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"
        )

    def rect(self, x, y, w, h, stroke=(0, 0, 0), fill=None, width=1):
        if fill is None:
            self.commands.append(
                f"{stroke[0]} {stroke[1]} {stroke[2]} RG {width} w {x:.2f} {y:.2f} {w:.2f} {h:.2f} re S"
            )
        else:
            self.commands.append(
                f"{fill[0]} {fill[1]} {fill[2]} rg {stroke[0]} {stroke[1]} {stroke[2]} RG {width} w "
                f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re B"
            )

    def text(self, x, y, text, size=12, color=(0, 0, 0)):
        self.commands.append(
            f"BT /F1 {size} Tf {color[0]} {color[1]} {color[2]} rg {x:.2f} {y:.2f} Td "
            f"({self._escape(text)}) Tj ET"
        )

    def polyline(self, points, width=2, color=(0, 0, 0)):
        if not points:
            return
        commands = [f"{color[0]} {color[1]} {color[2]} RG {width} w"]
        commands.append(f"{points[0][0]:.2f} {points[0][1]:.2f} m")
        for x, y in points[1:]:
            commands.append(f"{x:.2f} {y:.2f} l")
        commands.append("S")
        self.commands.append(" ".join(commands))

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = "\n".join(self.commands).encode("latin-1", errors="replace")
        objects = []
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
            f"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode()
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")

        content = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for i, obj in enumerate(objects, start=1):
            offsets.append(len(content))
            content += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        xref = len(content)
        content += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
        for offset in offsets[1:]:
            content += f"{offset:010d} 00000 n \n".encode()
        content += (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode()
        self.path.write_bytes(content)


def draw_algorithm_flow():
    pdf = PdfCanvas(FIGURE_DIR / "algorithm_flow.pdf")
    pdf.text(250, 380, "R2T Processing Flow", 18)
    boxes = [
        (40, 260, 120, 60, "TPC-H .tbl\nfiles"),
        (200, 260, 120, 60, "SQLite\ncase SQL"),
        (360, 260, 130, 60, "Customer\ncontributions"),
        (540, 260, 130, 60, "R2T tau\nrace"),
        (280, 120, 160, 60, "Saved JSON/CSV\nresults"),
    ]
    for x, y, w, h, label in boxes:
        pdf.rect(x, y, w, h, fill=(0.93, 0.96, 1.0))
        for i, line in enumerate(label.split("\n")):
            pdf.text(x + 18, y + h - 24 - i * 16, line, 12)
    pdf.line(160, 290, 200, 290, 1.5)
    pdf.line(320, 290, 360, 290, 1.5)
    pdf.line(490, 290, 540, 290, 1.5)
    pdf.line(605, 260, 440, 180, 1.5)
    pdf.line(360, 180, 260, 260, 1.5)
    pdf.text(235, 225, "Q3 and Q5 are implemented as separate scripts", 11)
    pdf.save()


def draw_schema_cases():
    pdf = PdfCanvas(FIGURE_DIR / "schema_cases.pdf")
    pdf.text(230, 380, "TPC-H Relations Used by the Two Cases", 18)
    nodes = {
        "Customer": (70, 250),
        "Orders": (240, 250),
        "Lineitem": (410, 250),
        "Supplier": (580, 250),
        "Nation": (325, 120),
        "Region": (500, 120),
    }
    for name, (x, y) in nodes.items():
        fill = (1.0, 0.95, 0.86) if name == "Customer" else (0.94, 0.94, 0.94)
        pdf.rect(x, y, 110, 45, fill=fill)
        pdf.text(x + 18, y + 17, name, 12)
    pdf.line(180, 272, 240, 272, 1.5)
    pdf.line(350, 272, 410, 272, 1.5)
    pdf.line(520, 272, 580, 272, 1.5)
    pdf.line(125, 250, 360, 165, 1)
    pdf.line(635, 250, 380, 165, 1)
    pdf.line(435, 142, 500, 142, 1.5)
    pdf.text(65, 325, "Q3-style: Customer -> Orders -> Lineitem", 12)
    pdf.text(65, 305, "Q5-style: adds Supplier, Nation, and Region", 12)
    pdf.text(65, 80, "Privacy unit in both cases: one Customer and its referencing tuples.", 12)
    pdf.save()


def read_candidates(name):
    path = RESULT_DIR / f"{name}_candidates.csv"
    with path.open(newline="") as f:
        return [
            {
                "tau": float(row["tau"]),
                "truncated": float(row["truncated"]),
                "noise_scale": float(row["noise_scale"]),
                "noisy_score": float(row["noisy_score"]),
            }
            for row in csv.DictReader(f)
        ]


def read_summary(name):
    return json.loads((RESULT_DIR / f"{name}_summary.json").read_text())


def read_contributions(name):
    path = RESULT_DIR / f"{name}_contributions.csv"
    with path.open(newline="") as f:
        return [
            {
                "custkey": int(row["custkey"]),
                "contribution": float(row["contribution"]),
            }
            for row in csv.DictReader(f)
        ]


def draw_candidate_chart(name, title, output):
    rows = read_candidates(name)
    summary = read_summary(name)
    pdf = PdfCanvas(FIGURE_DIR / output)
    pdf.text(210, 385, title, 16)

    left, bottom, width, height = 70, 75, 580, 270
    pdf.line(left, bottom, left, bottom + height, 1)
    pdf.line(left, bottom, left + width, bottom, 1)

    xs = [math.log2(row["tau"]) for row in rows]
    ys = [row["truncated"] / 1_000_000 for row in rows]
    ns = [row["noisy_score"] / 1_000_000 for row in rows]
    y_min = min(0, min(ns))
    y_max = max(max(ys), max(ns))
    x_min, x_max = min(xs), max(xs)

    def tx(x):
        return left + (x - x_min) / (x_max - x_min) * width

    def ty(y):
        return bottom + (y - y_min) / (y_max - y_min) * height

    for i in range(6):
        y = y_min + (y_max - y_min) * i / 5
        pdf.line(left - 4, ty(y), left, ty(y), 1)
        pdf.text(18, ty(y) - 4, f"{y:.0f}", 8)
    for power in [1, 5, 10, 15, 20, 23]:
        if x_min <= power <= x_max:
            pdf.line(tx(power), bottom, tx(power), bottom - 4, 1)
            pdf.text(tx(power) - 8, bottom - 18, str(power), 8)

    pdf.polyline([(tx(x), ty(y)) for x, y in zip(xs, ys)], 2, (0.0, 0.25, 0.75))
    pdf.polyline([(tx(x), ty(y)) for x, y in zip(xs, ns)], 2, (0.75, 0.15, 0.1))
    selected_tau = float(summary["selected"]["tau"])
    selected_x = tx(math.log2(selected_tau))
    pdf.line(selected_x, bottom, selected_x, bottom + height, 1, (0.0, 0.55, 0.15))
    pdf.text(left + 410, bottom + height + 15, "blue: truncated", 10, (0.0, 0.25, 0.75))
    pdf.text(left + 410, bottom + height, "red: noisy score", 10, (0.75, 0.15, 0.1))
    pdf.text(left + 410, bottom + height - 15, f"selected tau={selected_tau:.0f}", 10, (0.0, 0.55, 0.15))
    pdf.text(left + 230, 35, "log2(tau)", 10)
    pdf.text(15, 355, "million", 10)
    pdf.save()


def draw_tau_tradeoff(name, title, output):
    rows = read_candidates(name)
    summary = read_summary(name)
    true_total = float(summary["true_total"])
    pdf = PdfCanvas(FIGURE_DIR / output)
    pdf.text(190, 385, title, 16)

    left, bottom, width, height = 75, 75, 580, 270
    pdf.line(left, bottom, left, bottom + height, 1)
    pdf.line(left, bottom, left + width, bottom, 1)

    xs = [math.log2(row["tau"]) for row in rows]
    retained = [row["truncated"] / true_total for row in rows]
    missing = [max(0.0, (true_total - row["truncated"]) / true_total) for row in rows]
    noise = [row["noise_scale"] / true_total for row in rows]
    y_min, y_max = 0.0, max(1.05, max(noise), max(retained), max(missing)) * 1.08
    x_min, x_max = min(xs), max(xs)

    def tx(x):
        return left + (x - x_min) / (x_max - x_min) * width

    def ty(y):
        return bottom + (y - y_min) / (y_max - y_min) * height

    for i in range(6):
        y = y_min + (y_max - y_min) * i / 5
        pdf.line(left - 4, ty(y), left, ty(y), 1)
        pdf.text(25, ty(y) - 4, f"{y:.1f}", 8)
    for power in [1, 5, 10, 15, 20, 23]:
        if x_min <= power <= x_max:
            pdf.line(tx(power), bottom, tx(power), bottom - 4, 1)
            pdf.text(tx(power) - 8, bottom - 18, str(power), 8)

    pdf.polyline([(tx(x), ty(y)) for x, y in zip(xs, retained)], 2, (0.0, 0.25, 0.75))
    pdf.polyline([(tx(x), ty(y)) for x, y in zip(xs, missing)], 2, (0.9, 0.45, 0.05))
    pdf.polyline([(tx(x), ty(y)) for x, y in zip(xs, noise)], 2, (0.45, 0.2, 0.65))
    selected_x = tx(math.log2(float(summary["selected"]["tau"])))
    pdf.line(selected_x, bottom, selected_x, bottom + height, 1, (0.0, 0.55, 0.15))

    legend_x = left + 385
    pdf.text(legend_x, bottom + height + 18, "blue: retained / true", 10, (0.0, 0.25, 0.75))
    pdf.text(legend_x, bottom + height + 3, "orange: truncation loss / true", 10, (0.9, 0.45, 0.05))
    pdf.text(legend_x, bottom + height - 12, "purple: noise scale / true", 10, (0.45, 0.2, 0.65))
    pdf.text(legend_x, bottom + height - 27, f"selected tau={summary['selected']['tau']:.0f}", 10, (0.0, 0.55, 0.15))
    pdf.text(left + 230, 35, "log2(tau)", 10)
    pdf.text(12, 355, "ratio", 10)
    pdf.save()


def draw_selected_output_comparison():
    cases = [
        ("Q3-style", read_summary("case_q3_customer_revenue")),
        ("Q5-style", read_summary("case_q5_asia_revenue")),
    ]
    pdf = PdfCanvas(FIGURE_DIR / "selected_output_comparison.pdf")
    pdf.text(185, 385, "Selected Threshold Output Comparison", 16)

    left, bottom, width, height = 90, 80, 540, 270
    pdf.line(left, bottom, left, bottom + height, 1)
    pdf.line(left, bottom, left + width, bottom, 1)
    series = [
        ("true SQL total", (0.0, 0.25, 0.75), lambda s: s["true_total"] / 1_000_000),
        ("truncated at tau*", (0.0, 0.55, 0.15), lambda s: s["selected"]["truncated"] / 1_000_000),
        ("R2T noisy output", (0.75, 0.15, 0.1), lambda s: s["r2t_output"] / 1_000_000),
    ]
    y_max = max(get_value(summary) for _, summary in cases for _, _, get_value in series) * 1.15

    def ty(y):
        return bottom + y / y_max * height

    for i in range(6):
        y = y_max * i / 5
        pdf.line(left - 4, ty(y), left, ty(y), 1)
        pdf.text(25, ty(y) - 4, f"{y:.0f}", 8)

    group_width = 210
    bar_width = 42
    for group_idx, (case_label, summary) in enumerate(cases):
        group_left = left + 105 + group_idx * group_width
        for series_idx, (_, color, get_value) in enumerate(series):
            value = get_value(summary)
            x = group_left + series_idx * (bar_width + 10)
            bar_height = ty(value) - bottom
            pdf.rect(x, bottom, bar_width, bar_height, stroke=color, fill=color, width=0.5)
            pdf.text(x - 2, bottom + bar_height + 8, f"{value:.1f}", 8)
        pdf.text(group_left + 20, bottom - 25, case_label, 10)

    legend_x = 430
    for i, (label, color, _) in enumerate(series):
        y = bottom + height - i * 18
        pdf.rect(legend_x, y, 12, 8, stroke=color, fill=color, width=0.5)
        pdf.text(legend_x + 18, y - 1, label, 9, color)
    pdf.text(15, 355, "million", 10)
    pdf.save()


def draw_contribution_concentration():
    cases = [
        ("Q3-style", "case_q3_customer_revenue", (0.0, 0.25, 0.75)),
        ("Q5-style", "case_q5_asia_revenue", (0.75, 0.15, 0.1)),
    ]
    pdf = PdfCanvas(FIGURE_DIR / "contribution_concentration.pdf")
    pdf.text(190, 385, "Customer Contribution Concentration", 16)

    left, bottom, width, height = 75, 75, 580, 270
    pdf.line(left, bottom, left, bottom + height, 1)
    pdf.line(left, bottom, left + width, bottom, 1)

    def tx(percent):
        return left + percent / 100.0 * width

    def ty(percent):
        return bottom + percent / 100.0 * height

    for percent in [0, 20, 40, 60, 80, 100]:
        pdf.line(tx(percent), bottom, tx(percent), bottom - 4, 1)
        pdf.text(tx(percent) - 8, bottom - 18, str(percent), 8)
        pdf.line(left - 4, ty(percent), left, ty(percent), 1)
        pdf.text(25, ty(percent) - 4, str(percent), 8)
    pdf.line(left, bottom, left + width, bottom + height, 1, (0.65, 0.65, 0.65))

    legend_y = bottom + height + 16
    pdf.text(360, legend_y, "gray: uniform baseline", 9, (0.4, 0.4, 0.4))
    for label, slug, color in cases:
        values = sorted((row["contribution"] for row in read_contributions(slug)), reverse=True)
        total = sum(values)
        cumulative = 0.0
        points = [(tx(0.0), ty(0.0))]
        for i, value in enumerate(values, start=1):
            cumulative += value
            points.append((tx(100.0 * i / len(values)), ty(100.0 * cumulative / total)))
        pdf.polyline(points, 2, color)

        top_ten_count = max(1, math.ceil(len(values) * 0.10))
        top_ten_share = sum(values[:top_ten_count]) / total * 100.0
        pdf.text(360, legend_y - 16 * (1 + cases.index((label, slug, color))), f"{label}: top 10% = {top_ten_share:.1f}%", 9, color)

    pdf.text(left + 180, 35, "customers sorted by contribution (%)", 10)
    pdf.text(12, 355, "revenue share (%)", 10)
    pdf.save()


def main():
    draw_algorithm_flow()
    draw_schema_cases()
    draw_candidate_chart(
        "case_q3_customer_revenue",
        "Q3-style R2T Candidate Values",
        "q3_r2t_candidates.pdf",
    )
    draw_candidate_chart(
        "case_q5_asia_revenue",
        "Q5-style R2T Candidate Values",
        "q5_r2t_candidates.pdf",
    )
    draw_tau_tradeoff(
        "case_q3_customer_revenue",
        "Q3-style Tau Tradeoff Ratios",
        "q3_tau_tradeoff.pdf",
    )
    draw_tau_tradeoff(
        "case_q5_asia_revenue",
        "Q5-style Tau Tradeoff Ratios",
        "q5_tau_tradeoff.pdf",
    )
    draw_selected_output_comparison()
    draw_contribution_concentration()
    print(f"figures written to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
