#!/usr/bin/env python3
"""
Build the **combined dashboard** HTML (Chart.js) of ICE BofA OAS by rating bucket
plus the borrowing-cost NPV table when the NPV CSV is present.

Reads the tidy CSV from ``fred_ice_bofa_oas_tidy.py`` (or ``--input``). Uses the
last ``--years`` of data by default. **BBB+** is the mean of **A** and **BBB**
per date (computed if not already present in the CSV). The **CCC & lower** strip is
**not** drawn on the line chart (other buckets unchanged).

Default output: ``data/utilities/pge_oas_debt_dashboard.html`` (NPV table from
``--npv-csv`` when available; chart always included).

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


def chart_init_script(
    payload_json: str, *, canvas_id: str = "c", y_axis_label: str = "OAS (%)"
) -> str:
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
          title: {{ display: true, text: {json.dumps(y_axis_label)} }},
          grid: {{ color: 'rgba(148, 163, 184, 0.25)' }}
        }}
      }}
    }}
  }});
}}
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


def build_dashboard_html(
    *,
    labels: list[str],
    series: dict[str, list[float | None]],
    npv_rows: list[dict[str, str]] | None,
    npv_missing_note: str,
) -> str:
    payload = json.dumps(chart_payload_dict(labels, series), ensure_ascii=True)
    chart_js = chart_init_script(
        payload,
        canvas_id="oasChart",
        y_axis_label="Option-adjusted spread (%)",
    )
    t0, t1 = labels[0], labels[-1]

    footnote_chart = (
        "Daily option-adjusted spread (% of par), ICE BofA series. <strong>BBB+</strong> is the average of "
        "<strong>A</strong> and <strong>BBB</strong> each trading day. Investment-grade (AAA–A) in greens; "
        "high yield (BBB–B) in reds; <strong>BBB+</strong> in black with a wider line. CCC and lower excluded "
        "from the chart. Not investment advice."
    )

    if npv_rows:
        r0 = npv_rows[0]
        eff = (r0.get("oas_observation_date") or "").strip()
        proceeds = str(int(float(r0.get("forecast_proceeds_lt_debt_2026", 504700000))))
        rf = float(r0.get("riskfree_rate_pct", 4.0))
        disc = float(r0.get("discount_rate_pct", 6.0))
        term = int(float(r0.get("term_years", 30)))
        spec_rows: list[dict[str, Any]] = []
        for r in npv_rows:
            b = (r.get("rating_bucket") or "").strip()
            if b:
                spec_rows.append({"rating": b, "oas": float(r.get("oas_pct", 0))})
        npv_json = json.dumps(
            {"rf": rf, "discountPct": disc, "term": term, "rows": spec_rows},
            separators=(",", ":"),
        )
        footnote_table = (
            f"The default issuance amount matches the 2026 proforma "
            f"<strong>proceeds from long-term debt</strong> in the cash-flow model ({int(float(r0.get('forecast_proceeds_lt_debt_2026', 0))):,} USD). "
            f"Coupon rate equals risk-free {rf:g}% plus the option-adjusted spread as of the effective date; "
            f"annual coupon equals proceeds times (coupon rate divided by 100). "
            f"Borrowing cost NPV is the present value of {term} annual coupons discounted at {disc:g}% per year. "
            "Rows sort by NPV, high to low. CCC and lower are excluded. Not investment advice."
        )
        npv_block = f"""
  <div class="wrap">
    <div class="calc-row">
      <label for="debt-proceeds">Long-term debt issuance (USD)</label>
      <input id="debt-proceeds" type="number" inputmode="numeric" step="1000000" min="0" value="{proceeds}" />
    </div>
    <table class="npv">
      <thead>
        <tr>
          <th>Credit Rating</th>
          <th class="num">Option-Adjusted Spread</th>
          <th class="num">Coupon %</th>
          <th class="num">Annual coupon</th>
          <th class="num">NPV (USD)</th>
        </tr>
      </thead>
      <tbody id="npv-tbody"></tbody>
    </table>
  </div>
<script>
window._npvSpec = {npv_json};
(function () {{
  function pvAnnuity(A, r, n) {{
    if (!(A >= 0) || !isFinite(A)) return 0;
    if (r <= 0) return A * n;
    return A * (1 - Math.pow(1 + r, -n)) / r;
  }}
  function fmtInt(n) {{
    return Math.round(n).toLocaleString('en-US');
  }}
  function fmtUsd(n) {{
    if (!(typeof n === 'number' && isFinite(n))) return '';
    return '$' + Math.round(n).toLocaleString('en-US');
  }}
  function renderNpv() {{
    var inp = document.getElementById('debt-proceeds');
    var p = inp ? Number(String(inp.value).replace(/,/g, '')) : NaN;
    if (!isFinite(p) || p < 0) return;
    var spec = window._npvSpec;
    var rf = spec.rf;
    var disc = spec.discountPct / 100;
    var n = spec.term;
    var rows = spec.rows.map(function (row) {{
      var couponPct = rf + row.oas;
      var annual = p * (couponPct / 100);
      var npv = pvAnnuity(annual, disc, n);
      return {{ rating: row.rating, oas: row.oas, couponPct: couponPct, annual: annual, npv: npv }};
    }});
    rows.sort(function (a, b) {{ return b.npv - a.npv; }});
    var tb = document.getElementById('npv-tbody');
    if (!tb) return;
    tb.innerHTML = '';
    function tdPct(x) {{
      var c = document.createElement('td');
      c.className = 'num';
      c.textContent = typeof x === 'number' && isFinite(x) ? x.toFixed(2) + '%' : '';
      return c;
    }}
    function tdNum(x) {{
      var c = document.createElement('td');
      c.className = 'num';
      c.textContent = typeof x === 'number' && isFinite(x) ? (Math.abs(x - Math.round(x)) < 1e-6 ? fmtInt(x) : x.toFixed(2)) : '';
      return c;
    }}
    function tdUsd(x) {{
      var c = document.createElement('td');
      c.className = 'num';
      c.textContent = fmtUsd(x);
      return c;
    }}
    function tdText(t) {{
      var c = document.createElement('td');
      c.textContent = t;
      return c;
    }}
    rows.forEach(function (r) {{
      var tr = document.createElement('tr');
      if (r.rating === 'BBB+') tr.className = 'rating-bbb-plus';
      tr.appendChild(tdText(r.rating));
      tr.appendChild(tdPct(r.oas));
      tr.appendChild(tdPct(r.couponPct));
      tr.appendChild(tdNum(r.annual));
      tr.appendChild(tdUsd(r.npv));
      tb.appendChild(tr);
    }});
  }}
  var debtEl = document.getElementById('debt-proceeds');
  if (debtEl) {{
    debtEl.addEventListener('input', renderNpv);
    debtEl.addEventListener('change', renderNpv);
  }}
  renderNpv();
}})();
</script>
"""
        head_date = f'    <p class="effective-date">Effective date: {eff}</p>\n' if eff else ""
    else:
        npv_block = f'  <div class="wrap"><p class="warn">{npv_missing_note}</p></div>\n'
        head_date = ""
        footnote_table = (
            "NPV table was not generated. Run "
            "<code>python3 scripts/pge_proforma_2026_debt_sensitivity.py</code> and rebuild this page."
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Borrowing Cost by Credit Rating</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #f1f5f9; color: #0f172a; }}
  p.back {{ font-size: 0.88rem; margin: 0 0 0.75rem; }}
  p.back a {{ color: #2563eb; }}
  header.page-head {{ margin: 0 0 0.75rem; }}
  header.page-head h1 {{ font-size: 1.35rem; margin: 0; font-weight: 650; color: #0f172a; }}
  p.effective-date {{ font-size: 0.9rem; color: #475569; margin: 0.35rem 0 0; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 0.5rem; color: #0f172a; }}
  p.meta {{ font-size: 0.8rem; color: #64748b; margin: 0 0 0.75rem; line-height: 1.45; }}
  p.warn {{ font-size: 0.85rem; color: #b45309; background: #fffbeb; padding: 0.75rem; border-radius: 6px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto 1rem; background: #fff; padding: 1rem 1.25rem; border-radius: 8px;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.08); }}
  .calc-row {{ margin: 0 0 1rem; display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 1rem; }}
  .calc-row label {{ font-size: 0.88rem; font-weight: 600; color: #334155; }}
  .calc-row input#debt-proceeds {{
    font-size: 0.95rem; padding: 0.35rem 0.5rem; border: 1px solid #cbd5e1; border-radius: 6px;
    min-width: 12rem; font-variant-numeric: tabular-nums;
  }}
  table.npv {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-top: 0.25rem; }}
  table.npv th, table.npv td {{ border: 1px solid #e2e8f0; padding: 0.4rem 0.5rem; text-align: left; }}
  table.npv th {{ background: #f8fafc; }}
  table.npv td.num, table.npv th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.npv tbody tr:nth-child(even):not(.rating-bbb-plus) {{ background: #fafafa; }}
  table.npv tbody tr.rating-bbb-plus {{ background: #fef9c3 !important; box-shadow: inset 3px 0 0 #ca8a04; }}
  canvas {{ max-height: 65vh; }}
  footer.footnotes {{ font-size: 0.78rem; color: #475569; line-height: 1.55; max-width: 1100px; margin: 0 auto 1.5rem; }}
  footer.footnotes h2 {{ font-size: 0.95rem; margin: 0 0 0.4rem; color: #334155; }}
  footer.footnotes ol {{ margin: 0; padding-left: 1.25rem; }}
  footer.footnotes li {{ margin: 0.35rem 0; }}
</style>
</head>
<body>
  <p class="back"><a href="../index.html">← PGE reports</a></p>
  <header class="page-head">
    <h1>Borrowing Cost by Credit Rating</h1>
{head_date}  </header>
{npv_block}  <div class="wrap">
    <h2>ICE BofA OAS by rating ({t0} to {t1})</h2>
    <canvas id="oasChart" height="400"></canvas>
  </div>
  <footer class="footnotes">
    <h2>Notes</h2>
    <ol>
      <li>{footnote_table}</li>
      <li>{footnote_chart}</li>
    </ol>
  </footer>
<script>
{chart_js}
</script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    in_path = (args.input or "").strip() or os.path.join(
        repo_root(), "data", "utilities", "ice_bofa_oas_tidy.csv"
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

    if not series:
        print("No series to plot after filtering.", file=sys.stderr)
        return 2

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
    print(
        f"Wrote {dash_path} ({len(dates)} days, {len(series)} series)",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
