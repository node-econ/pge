#!/usr/bin/env python3
"""
PGE FERC Form 1 — 2026 proforma and borrowing-cost NPV sensitivity.

1. Proforma 2026 amounts = average(2024, 2025) × 1.03 for every line in the
   consolidated financial JSON (all statement types). Missing years: if only
   one of 2024/2025 exists, that value × 1.03; if neither, blank.

2. Uses the proforma 2026 value for **ProceedsFromIssuanceOfLongTermDebtFinancingActivities**
   (cash flows) as the debt-proceeds forecast. For each **rating_bucket** in the
   ICE BofA OAS tidy CSV (latest observation date per bucket; **BBB+** = mean of
   A and BBB on that date if absent):

   - riskfree_rate = 4.0 (% points, same units as ``oas_pct`` in the CSV)
   - coupon_rate = riskfree_rate + oas_pct
   - coupon_pmt = forecast_proceeds × (coupon_rate / 100)
   - npv_borrowing_cost = PV of 30 annual ``coupon_pmts`` discounted at 6%

3. Writes a rating-bucket table sorted **high-to-low** by ``npv_borrowing_cost``.
   **CCC & lower** is omitted from the NPV table and CSV (same scope as the OAS chart).

Outputs (default under ``data/utilities/``):

- ``pge_form1_proforma_2026.csv``
- ``pge_borrowing_cost_npv_by_rating.csv``
- ``pge_borrowing_cost_npv_by_rating.md``

Not investment advice; illustrative only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from typing import Any

STATEMENT_KEYS = (
    "income_statement",
    "balance_sheet_assets",
    "balance_sheet_liabilities",
    "cash_flows",
)

DEBT_CONCEPT = "ProceedsFromIssuanceOfLongTermDebtFinancingActivities"
RISK_FREE_PCT = 4.0
DISCOUNT_PCT = 6.0
TERM_YEARS = 30
GROWTH = 1.03

# Omitted from NPV CSV / markdown (aligned with OAS line chart).
EXCLUDED_NPV_RATING_BUCKETS = frozenset({"CCC_and_lower"})

BBB_PLUS = "BBB+"


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_num(s: Any) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def proforma_2026(by_year: dict[str, Any]) -> float | None:
    a = parse_num(by_year.get("2024"))
    b = parse_num(by_year.get("2025"))
    if a is not None and b is not None:
        return (a + b) / 2.0 * GROWTH
    if a is not None:
        return a * GROWTH
    if b is not None:
        return b * GROWTH
    return None


def annuity_pv(pmt: float, rate: float, n: int) -> float:
    """Ordinary annuity PV; rate as decimal (e.g. 0.06)."""
    if n <= 0:
        return 0.0
    if abs(rate) < 1e-15:
        return pmt * n
    return pmt * (1.0 - math.pow(1.0 + rate, -n)) / rate


def read_tidy_oas(path: str) -> list[dict[str, str]]:
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
        rdr = csv.DictReader(f, fieldnames=header)
        for row in rdr:
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


def latest_oas_by_bucket(rows: list[dict[str, str]]) -> dict[str, tuple[str, float]]:
    """rating_bucket -> (observation_date, oas_pct as float). Latest date wins."""
    best: dict[str, tuple[str, float]] = {}
    for r in rows:
        b = r["rating_bucket"]
        d = r["observation_date"]
        try:
            o = float(r["oas_pct"])
        except ValueError:
            continue
        if b not in best or d > best[b][0]:
            best[b] = (d, o)
    max_d = max((t[0] for t in best.values()), default="")
    if max_d and BBB_PLUS not in best:
        on_date = {
            r["rating_bucket"]: float(r["oas_pct"])
            for r in rows
            if r["observation_date"] == max_d
            and r["rating_bucket"] in ("A", "BBB")
        }
        if "A" in on_date and "BBB" in on_date:
            best[BBB_PLUS] = (max_d, (on_date["A"] + on_date["BBB"]) / 2.0)
    return best


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--financials-json",
        default="",
        help="pge_form1_financials.json path (default: data/utilities/ferc1_pge_viewer/...).",
    )
    ap.add_argument(
        "--oas-csv",
        default="",
        help="ice_bofa_oas_tidy.csv path (default: data/utilities/...).",
    )
    ap.add_argument(
        "--out-dir",
        "-o",
        default="",
        help="Output directory (default: data/utilities).",
    )
    args = ap.parse_args()
    root = repo_root()
    jpath = (args.financials_json or "").strip() or os.path.join(
        root, "data", "utilities", "ferc1_pge_viewer", "pge_form1_financials.json"
    )
    oas_path = (args.oas_csv or "").strip() or os.path.join(
        root, "data", "utilities", "ice_bofa_oas_tidy.csv"
    )
    out_dir = (args.out_dir or "").strip() or os.path.join(root, "data", "utilities")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isfile(jpath):
        print(f"Missing financials JSON: {jpath}", file=sys.stderr)
        return 2
    if not os.path.isfile(oas_path):
        print(f"Missing OAS CSV: {oas_path}", file=sys.stderr)
        return 2

    with open(jpath, encoding="utf-8") as f:
        fin: dict[str, Any] = json.load(f)

    proforma_path = os.path.join(out_dir, "pge_form1_proforma_2026.csv")
    fieldnames = [
        "statement",
        "concept",
        "label",
        "depth",
        "amount_2024",
        "amount_2025",
        "amount_2026_proforma",
    ]
    proceeds_forecast: float | None = None
    with open(proforma_path, "w", encoding="utf-8", newline="") as outf:
        w = csv.DictWriter(outf, fieldnames=fieldnames)
        w.writeheader()
        for stmt in STATEMENT_KEYS:
            for row in fin.get(stmt) or []:
                by = row.get("by_year") or {}
                v24 = parse_num(by.get("2024"))
                v25 = parse_num(by.get("2025"))
                p26 = proforma_2026(by)
                w.writerow(
                    {
                        "statement": stmt,
                        "concept": row.get("concept", ""),
                        "label": row.get("label", ""),
                        "depth": row.get("depth", ""),
                        "amount_2024": "" if v24 is None else f"{v24:.0f}",
                        "amount_2025": "" if v25 is None else f"{v25:.0f}",
                        "amount_2026_proforma": ""
                        if p26 is None
                        else f"{p26:.0f}",
                    }
                )
                if row.get("concept") == DEBT_CONCEPT:
                    proceeds_forecast = p26

    print(f"Wrote {proforma_path}", file=sys.stderr)

    if proceeds_forecast is None:
        print(
            f"Could not find {DEBT_CONCEPT} or proforma value in cash_flows.",
            file=sys.stderr,
        )
        return 1

    oas_rows = read_tidy_oas(oas_path)
    oas_latest = latest_oas_by_bucket(oas_rows)
    if not oas_latest:
        print("No OAS rows parsed.", file=sys.stderr)
        return 1

    r_disc = DISCOUNT_PCT / 100.0
    sens_rows: list[dict[str, Any]] = []
    for bucket in sorted(oas_latest.keys()):
        if bucket in EXCLUDED_NPV_RATING_BUCKETS:
            continue
        obs_d, oas_pct = oas_latest[bucket]
        coupon_rate = RISK_FREE_PCT + oas_pct
        coupon_pmt = proceeds_forecast * (coupon_rate / 100.0)
        npv = annuity_pv(coupon_pmt, r_disc, TERM_YEARS)
        sens_rows.append(
            {
                "rating_bucket": bucket,
                "oas_observation_date": obs_d,
                "oas_pct": oas_pct,
                "riskfree_rate_pct": RISK_FREE_PCT,
                "coupon_rate_pct": coupon_rate,
                "forecast_proceeds_lt_debt_2026": proceeds_forecast,
                "coupon_pmt_annual": coupon_pmt,
                "discount_rate_pct": DISCOUNT_PCT,
                "term_years": TERM_YEARS,
                "npv_borrowing_cost": npv,
            }
        )

    sens_rows.sort(key=lambda r: r["npv_borrowing_cost"], reverse=True)

    sens_csv = os.path.join(out_dir, "pge_borrowing_cost_npv_by_rating.csv")
    sens_fields = list(sens_rows[0].keys()) if sens_rows else []
    with open(sens_csv, "w", encoding="utf-8", newline="") as outf:
        wr = csv.DictWriter(outf, fieldnames=sens_fields)
        wr.writeheader()
        wr.writerows(sens_rows)
    print(f"Wrote {sens_csv}", file=sys.stderr)

    md_path = os.path.join(out_dir, "pge_borrowing_cost_npv_by_rating.md")
    lines = [
        "# Borrowing cost NPV by rating bucket",
        "",
        f"Forecast **2026** proceeds (LT debt issuance, proforma): **{proceeds_forecast:,.0f}** USD.",
        "",
        f"Assumptions: risk-free **{RISK_FREE_PCT}%** + OAS = coupon (%); "
        f"`coupon_pmt` = proceeds × (coupon_rate/100); **{TERM_YEARS}** annual payments; "
        f"discounted at **{DISCOUNT_PCT}%** (`npv_borrowing_cost`). OAS = latest date in tidy CSV per bucket. "
        "**CCC & lower** is excluded from this table.",
        "",
        "Sorted by **npv_borrowing_cost** (high → low).",
        "",
        "| rating_bucket | oas_date | oas % | coupon % | coupon_pmt (annual) | NPV |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for r in sens_rows:
        lines.append(
            "| {bucket} | {d} | {oas:.2f} | {cr:.2f} | {pmt:,.0f} | {npv:,.0f} |".format(
                bucket=r["rating_bucket"],
                d=r["oas_observation_date"],
                oas=r["oas_pct"],
                cr=r["coupon_rate_pct"],
                pmt=r["coupon_pmt_annual"],
                npv=r["npv_borrowing_cost"],
            )
        )
    lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {md_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
