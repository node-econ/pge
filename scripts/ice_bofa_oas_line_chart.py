#!/usr/bin/env python3
"""
Build **line chart** HTML (Chart.js) of ICE BofA OAS by rating bucket, and optionally
a **combined dashboard** with the borrowing-cost NPV table + the same chart.

Reads the tidy CSV from ``fred_ice_bofa_oas_tidy.py`` (or ``--input``). Uses the
last ``--years`` of data by default. **BBB+** is the mean of **A** and **BBB**
per date (computed if not already present in the CSV). The **CCC & lower** strip is
**not** drawn on the line chart (other buckets unchanged).

Outputs (defaults under ``data/utilities/``):

- ``ice_bofa_oas_line_chart.html`` — chart only
- ``pge_oas_debt_dashboard.html`` — NPV table (from ``--npv-csv``) + chart (skipped
  table if the NPV file is missing)

ICE / FRED — respect license terms on the underlying series pages.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
from collections import defaultdict
from typing import Any

# Plot order (BBB+ drawn last so it sits on top). CCC & lower omitted from chart per product choice.
BUCKETS_BASE = ["AAA", "AA", "A", "BBB", "BB", "B"]
BBB_PLUS = "BBB+"

# line color, line width (BBB+ gets heavy black stroke).
STYLE: dict[str, tuple[str, float]] = {
    "AAA": ("#166534", 2.0),
    "AA": ("#22c55e", 2.0),
    "A": ("#86efac", 2.0),
    "BBB": ("#fca5a5", 2.0),
    "BB": ("#ef4444", 2.0),
    "B": ("#b91c1c", 2.0),
    BBB_PLUS: ("#0a0a0a", 4.0),
}


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input",
        "-i",
        default="",
        help="Tidy OAS CSV (default: data/utilities/ice_bofa_oas_tidy.csv).",
    )
    p.add_argument(
        "--output",
        "-o",
        default="",
        help="Output HTML (default: data/utilities/ice_bofa_oas_line_chart.html).",
    )
    p.add_argument(
        "--years",
        type=float,
        default=2.0,
        help="Use observations from the last N years (default: 2).",
    )
    p.add_argument(
        "--npv-csv",
        default="",
        help="Borrowing-cost NPV CSV for dashboard table (default: try data/utilities/pge_borrowing_cost_npv_by_rating.csv).",
    )
    p.add_argument(
        "--dashboard-output",
        default="",
        help="Combined table+chart HTML (default: data/utilities/pge_oas_debt_dashboard.html).",
    )
    p.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Do not write the combined dashboard HTML.",
    )
    return p.parse_args()


def read_tidy_csv(path: str) -> list[dict[str, str]]:
    """Skip comment lines; use first non-comment as header."""
    rows: list[dict[str, str]] = []
    with open(path, encoding="utf-8", newline="") as f:
        header: list[str] | None = None
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            header = line.split(",")
            break
        if not header:
            return rows
        reader = csv.DictReader(f, fieldnames=header)
        for row in reader:
            if not row.get("observation_date"):
                continue
            rows.append(
                {
                    "observation_date": row["observation_date"].strip(),
                    "rating_bucket": row["rating_bucket"].strip(),
                    "oas_pct": row["oas_pct"].strip(),
                }
            )
    return rows


def legend_label(key: str) -> str:
    if key == "CCC_and_lower":
        return "CCC & lower"
    if key == BBB_PLUS:
        return "BBB+"
    return key.replace("_", " ")


def clip_dates(
    dates_sorted: list[str], *, years: float
) -> list[str]:
    if not dates_sorted or years <= 0:
        return dates_sorted
    last = dt.date.fromisoformat(dates_sorted[-1])
    start = last - dt.timedelta(days=int(365.25 * years))
    start_s = start.isoformat()
    return [d for d in dates_sorted if d >= start_s]


def pivot_with_bbb_plus(rows: list[dict[str, str]]) -> tuple[list[str], dict[str, dict[str, float]]]:
    """Return sorted dates and date -> {bucket: oas_pct}."""
    by_date: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        try:
            v = float(r["oas_pct"])
        except ValueError:
            continue
        by_date[r["observation_date"]][r["rating_bucket"]] = v
    dates = sorted(by_date.keys())
    for d in dates:
        b = by_date[d]
        if BBB_PLUS not in b and "A" in b and "BBB" in b:
            b[BBB_PLUS] = (b["A"] + b["BBB"]) / 2.0
    return dates, dict(by_date)


def chart_payload_dict(
    labels: list[str], series: dict[str, list[float | None]]
) -> dict[str, Any]:
    order = [b for b in BUCKETS_BASE if b in series] + ([BBB_PLUS] if BBB_PLUS in series else [])
    datasets: list[dict[str, Any]] = []
    for key in order:
        color, width = STYLE.get(key, ("#64748b", 2.0))
        datasets.append(
            {
                "label": legend_label(key),
                "data": series[key],
                "borderColor": color,
                "backgroundColor": "transparent",
                "borderWidth": width,
                "pointRadius": 0,
                "pointHoverRadius": 3,
                "tension": 0.12,
                "fill": False,
            }
        )
    return {"labels": labels, "datasets": datasets}


def chart_init_script(payload_json: str, *, canvas_id: str = "c") -> str:
    return f"""
const _oasChartData = {payload_json};
const _oasEl = document.getElementById('{canvas_id}');
if (_oasEl) {{
  new Chart(_oasEl.getContext('2d'), {{
    type: 'line',
    data: _oasChartData,
    options: {{
      responsive: true,
      maintainAspectRatio: true,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 14 }} }},
        title: {{ display: false }}
      }},
      scales: {{
        x: {{
          ticks: {{ maxRotation: 45, minRotation: 0, autoSkip: true, maxTicksLimit: 14 }},
          grid: {{ display: false }}
        }},
        y: {{
          title: {{ display: true, text: 'OAS (%)' }},
          grid: {{ color: 'rgba(148, 163, 184, 0.25)' }}
        }}
      }}
    }}
  }});
}}
"""


def build_html(*, labels: list[str], series: dict[str, list[float | None]], title: str) -> str:
    payload = json.dumps(chart_payload_dict(labels, series), ensure_ascii=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #f8fafc; color: #0f172a; }}
  h1 {{ font-size: 1.1rem; margin: 0 0 0.5rem; }}
  p.meta {{ font-size: 0.8rem; color: #64748b; margin: 0 0 1rem; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; background: #fff; padding: 1rem; border-radius: 8px;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.08); }}
  canvas {{ max-height: 70vh; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{title}</h1>
  <p class="meta">Option-adjusted spread (%), daily. <strong>BBB+</strong> = average of <strong>A</strong> and <strong>BBB</strong> each day.
    IG buckets (AAA–A) in greens; HY (BBB–B) in reds; <strong>BBB+</strong> black (wide line). CCC & lower excluded from this chart. Not investment advice.</p>
  <canvas id="c" height="420"></canvas>
</div>
<script>
{chart_init_script(payload, canvas_id="c")}
</script>
</body>
</html>
"""


def read_npv_csv(path: str) -> list[dict[str, str]]:
    skip = frozenset({"CCC_and_lower"})
    rows: list[dict[str, str]] = []
    with open(path, encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            b = row.get("rating_bucket", "").strip()
            if b and b not in skip:
                rows.append(dict(row))
    return rows


def fmt_money(x: str | float) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    return f"{v:,.0f}"


def npv_table_html(rows: list[dict[str, str]]) -> str:
    if not rows:
        return '<p class="warn">No NPV rows.</p>'
    r0 = rows[0]
    proceeds = r0.get("forecast_proceeds_lt_debt_2026", "")
    intro = (
        f"<p class=\"meta\">Forecast 2026 LT debt issuance (proforma): <strong>{fmt_money(proceeds)}</strong> USD. "
        f"Risk-free {r0.get('riskfree_rate_pct', '')}% + OAS = coupon (%); "
        f"annual coupon = proceeds × (coupon/100); NPV of {r0.get('term_years', '')} payments at "
        f"{r0.get('discount_rate_pct', '')}% discount. Sorted by NPV (high → low). CCC & lower excluded.</p>"
    )
    head = (
        "<table class=\"npv\"><thead><tr>"
        "<th>rating_bucket</th><th>OAS date</th><th>OAS %</th><th>Coupon %</th>"
        "<th class=\"num\">Annual coupon</th><th class=\"num\">NPV</th>"
        "</tr></thead><tbody>"
    )
    body_parts: list[str] = []
    for r in rows:
        body_parts.append(
            "<tr>"
            f"<td>{r.get('rating_bucket', '')}</td>"
            f"<td>{r.get('oas_observation_date', '')}</td>"
            f"<td class=\"num\">{float(r.get('oas_pct', 0)):,.2f}</td>"
            f"<td class=\"num\">{float(r.get('coupon_rate_pct', 0)):,.2f}</td>"
            f"<td class=\"num\">{fmt_money(r.get('coupon_pmt_annual', ''))}</td>"
            f"<td class=\"num\">{fmt_money(r.get('npv_borrowing_cost', ''))}</td>"
            "</tr>"
        )
    return intro + head + "".join(body_parts) + "</tbody></table>"


def build_dashboard_html(
    *,
    labels: list[str],
    series: dict[str, list[float | None]],
    npv_rows: list[dict[str, str]] | None,
    npv_missing_note: str,
) -> str:
    payload = json.dumps(chart_payload_dict(labels, series), ensure_ascii=True)
    if npv_rows:
        table_block = (
            "<h2>Borrowing cost NPV by rating</h2>" + npv_table_html(npv_rows)
        )
    else:
        table_block = f'<p class="warn">{npv_missing_note}</p>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>PGE — OAS & borrowing cost</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #f1f5f9; color: #0f172a; }}
  h1 {{ font-size: 1.25rem; margin: 0 0 0.75rem; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 0.5rem; color: #0f172a; }}
  p.meta {{ font-size: 0.8rem; color: #64748b; margin: 0 0 0.75rem; line-height: 1.45; }}
  p.warn {{ font-size: 0.85rem; color: #b45309; background: #fffbeb; padding: 0.75rem; border-radius: 6px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto 1rem; background: #fff; padding: 1rem 1.25rem; border-radius: 8px;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.08); }}
  table.npv {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-top: 0.5rem; }}
  table.npv th, table.npv td {{ border: 1px solid #e2e8f0; padding: 0.4rem 0.5rem; text-align: left; }}
  table.npv th {{ background: #f8fafc; }}
  table.npv td.num, table.npv th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.npv tbody tr:nth-child(even) {{ background: #fafafa; }}
  canvas {{ max-height: 65vh; }}
</style>
</head>
<body>
  <h1>PGE — ICE BofA OAS & borrowing cost</h1>
  <div class="wrap">
    {table_block}
  </div>
  <div class="wrap">
    <h2>OAS by rating ({labels[0]} to {labels[-1]})</h2>
    <p class="meta">Daily OAS (%). <strong>BBB+</strong> = average of <strong>A</strong> and <strong>BBB</strong> each day.
      IG (AAA–A) greens; HY (BBB–B) reds; <strong>BBB+</strong> black (wide line). CCC & lower excluded. Not investment advice.</p>
    <canvas id="oasChart" height="400"></canvas>
  </div>
<script>
{chart_init_script(payload, canvas_id="oasChart")}
</script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    in_path = (args.input or "").strip() or os.path.join(
        repo_root(), "data", "utilities", "ice_bofa_oas_tidy.csv"
    )
    out_path = (args.output or "").strip() or os.path.join(
        repo_root(), "data", "utilities", "ice_bofa_oas_line_chart.html"
    )
    if not os.path.isfile(in_path):
        print(f"Input not found: {in_path}", file=sys.stderr)
        return 2

    rows = read_tidy_csv(in_path)
    if not rows:
        print("No data rows in CSV.", file=sys.stderr)
        return 2

    dates_all, by_date = pivot_with_bbb_plus(rows)
    dates = clip_dates(dates_all, years=args.years)
    if not dates:
        print("No dates after clip.", file=sys.stderr)
        return 2

    plot_buckets = BUCKETS_BASE + [BBB_PLUS]
    series: dict[str, list[float | None]] = {}
    for b in plot_buckets:
        vals: list[float | None] = []
        for d in dates:
            v = by_date.get(d, {}).get(b)
            vals.append(v if v is not None else None)
        if any(v is not None for v in vals):
            series[b] = vals

    t0, t1 = dates[0], dates[-1]
    title = f"ICE BofA OAS by rating ({t0} to {t1})"
    html = build_html(labels=dates, series=series, title=title)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {out_path} ({len(dates)} days, {len(series)} series)", file=sys.stderr)

    if not args.no_dashboard:
        dash_path = (args.dashboard_output or "").strip() or os.path.join(
            repo_root(), "data", "utilities", "pge_oas_debt_dashboard.html"
        )
        npv_path = (args.npv_csv or "").strip() or os.path.join(
            repo_root(), "data", "utilities", "pge_borrowing_cost_npv_by_rating.csv"
        )
        npv_rows: list[dict[str, str]] | None = None
        npv_note = (
            "NPV table not found. Run: "
            "<code>python3 scripts/pge_proforma_2026_debt_sensitivity.py</code>"
        )
        if os.path.isfile(npv_path):
            npv_rows = read_npv_csv(npv_path)
            if not npv_rows:
                npv_rows = None
                npv_note = "NPV file was empty."
        dash_html = build_dashboard_html(
            labels=dates,
            series=series,
            npv_rows=npv_rows,
            npv_missing_note=npv_note,
        )
        os.makedirs(os.path.dirname(dash_path) or ".", exist_ok=True)
        with open(dash_path, "w", encoding="utf-8") as f:
            f.write(dash_html)
        print(f"Wrote {dash_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
