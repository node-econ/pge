#!/usr/bin/env python3
"""
Download ICE BofA option-adjusted spread (OAS) from FRED into a **tidy** CSV:
one row per (observation_date, rating_bucket).

Only **discrete rating strips** are included (no Corporate Master / HY Master composites).

For each observation date, a **BBB+** row is appended as the arithmetic mean of the
**A** and **BBB** OAS (same date); it is not a FRED series (see ``fred_series_id`` in CSV).

Loads `FRED_API_KEY` from the process environment. If unset, reads repo-root `.env`
(simple KEY=value lines; does not override existing env vars).

FRED API: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
API key: https://fredaccount.stlouisfed.org/apikeys

ICE / BofA data — follow FRED and ICE license terms on each series page.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

FRED_OBS_URL = "https://api.stlouisfed.org/fred/series/observations"

# (rating_bucket, fred_index_segment, fred_series_id)
DISCRETE_SERIES: list[tuple[str, str, str]] = [
    ("AAA", "US_Corporate", "BAMLC0A1CAAA"),
    ("AA", "US_Corporate", "BAMLC0A2CAA"),
    ("A", "US_Corporate", "BAMLC0A3CA"),
    ("BBB", "US_Corporate", "BAMLC0A4CBBB"),
    ("BB", "US_High_Yield", "BAMLH0A1HYBB"),
    ("B", "US_High_Yield", "BAMLH0A2HYB"),
    ("CCC_and_lower", "US_High_Yield", "BAMLH0A3HYC"),
]

# Synthetic: average of A and BBB OAS for each date (not a FRED series).
BBB_PLUS_SYNTH_ID = "AVG(BAMLC0A3CA,BAMLC0A4CBBB)"

RATING_SORT_ORDER = {
    "AAA": 0,
    "AA": 1,
    "A": 2,
    "BBB+": 3,
    "BBB": 4,
    "BB": 5,
    "B": 6,
    "CCC_and_lower": 7,
}


def load_dotenv(path: str) -> None:
    """Minimal .env loader; does not override existing environment variables."""
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="ICE BofA OAS by rating bucket — tidy CSV from FRED."
    )
    p.add_argument(
        "--api-key",
        default=os.environ.get("FRED_API_KEY", ""),
        help="FRED API key (default: env FRED_API_KEY after loading .env).",
    )
    p.add_argument(
        "--years",
        type=float,
        default=2.0,
        help="Lookback from end date when --start-date is omitted (default: 2).",
    )
    p.add_argument(
        "--start-date",
        default="",
        help="Window start YYYY-MM-DD (if set, --years is ignored).",
    )
    p.add_argument(
        "--end-date",
        default="",
        help="Window end YYYY-MM-DD (default: today).",
    )
    p.add_argument(
        "--output",
        "-o",
        default="",
        metavar="PATH",
        help="Output CSV (default: data/utilities/ice_bofa_oas_tidy.csv).",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=0.35,
        help="Seconds between FRED API calls.",
    )
    return p.parse_args()


def observation_start(end: dt.date, years: float) -> dt.date:
    return end - dt.timedelta(days=int(365.25 * years))


def fetch_observations(
    *,
    series_id: str,
    api_key: str,
    observation_start: str,
    observation_end: str,
) -> dict[str, str]:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": observation_start,
        "observation_end": observation_end,
    }
    url = FRED_OBS_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "PGE-fred-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    out: dict[str, str] = {}
    for row in payload.get("observations", []):
        d = row.get("date")
        v = row.get("value")
        if d is None:
            continue
        if v in (".", "", None):
            continue
        out[str(d)] = str(v)
    return out


def main() -> int:
    load_dotenv(os.path.join(repo_root(), ".env"))
    args = parse_args()
    key = (args.api_key or "").strip()
    if not key:
        print(
            "Set FRED_API_KEY in .env or the environment, or pass --api-key.\n"
            "Register: https://fredaccount.stlouisfed.org/apikeys",
            file=sys.stderr,
        )
        return 2

    if args.end_date.strip():
        end = dt.date.fromisoformat(args.end_date.strip())
    else:
        end = dt.date.today()
    if args.start_date.strip():
        start = dt.date.fromisoformat(args.start_date.strip())
    else:
        start = observation_start(end, args.years)
    start_s = start.isoformat()
    end_s = end.isoformat()
    if start > end:
        print("Error: start date must be on or before end date.", file=sys.stderr)
        return 2

    rows: list[dict[str, str]] = []

    for rating_bucket, segment, sid in DISCRETE_SERIES:
        try:
            series_map = fetch_observations(
                series_id=sid,
                api_key=key,
                observation_start=start_s,
                observation_end=end_s,
            )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:800]
            print(f"HTTP {e.code} for {sid}: {body}", file=sys.stderr)
            return 1
        except urllib.error.URLError as e:
            print(f"Network error for {sid}: {e}", file=sys.stderr)
            return 1
        for date_str, val in series_map.items():
            rows.append(
                {
                    "observation_date": date_str,
                    "rating_bucket": rating_bucket,
                    "fred_index_segment": segment,
                    "fred_series_id": sid,
                    "oas_pct": val,
                }
            )
        time.sleep(max(0.0, args.sleep))

    by_date: dict[str, dict[str, str]] = {}
    for r in rows:
        by_date.setdefault(r["observation_date"], {})[r["rating_bucket"]] = r["oas_pct"]

    for date_str, buckets in sorted(by_date.items()):
        if "A" not in buckets or "BBB" not in buckets:
            continue
        v = (float(buckets["A"]) + float(buckets["BBB"])) / 2.0
        rows.append(
            {
                "observation_date": date_str,
                "rating_bucket": "BBB+",
                "fred_index_segment": "US_Corporate",
                "fred_series_id": BBB_PLUS_SYNTH_ID,
                "oas_pct": f"{v:.4f}",
            }
        )

    rows.sort(
        key=lambda r: (
            r["observation_date"],
            RATING_SORT_ORDER.get(r["rating_bucket"], 99),
        )
    )

    out_path = (args.output or "").strip()
    if not out_path:
        util_dir = os.path.join(repo_root(), "data", "utilities")
        os.makedirs(util_dir, exist_ok=True)
        out_path = os.path.join(util_dir, "ice_bofa_oas_tidy.csv")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    fieldnames = [
        "observation_date",
        "rating_bucket",
        "fred_index_segment",
        "fred_series_id",
        "oas_pct",
    ]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(
            f"# tidy ICE BofA OAS; start={start_s}; end={end_s}; rows={len(rows)}\n"
        )
        f.write(
            "# oas_pct = percent, daily, NSA. BBB+ = mean(A, BBB) per date. Not investment advice.\n"
        )
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} tidy rows -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
