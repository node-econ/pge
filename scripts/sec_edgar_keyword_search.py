#!/usr/bin/env python3
"""
Search SEC EDGAR full-text filings (EFTS) for a keyword.

Uses the SEC's public full-text index:
  https://efts.sec.gov/LATEST/search-index

SEC fair-access / identification: set a truthful User-Agent that includes
contact information (email or URL). See:
  https://www.sec.gov/about/developer-resources

Environment:
  SEC_EDGAR_USER_AGENT — default User-Agent if --user-agent is omitted.

Examples:
  SEC_EDGAR_USER_AGENT="MyOrg research/1.0 (you@company.com)" \\
    python3 scripts/sec_edgar_keyword_search.py --keyword wilfdire

  python3 scripts/sec_edgar_keyword_search.py \\
    --user-agent "Acme/1.0 (ops@acme.com)" \\
    --keyword wildfire --max-results 50 --forms 10-K,10-Q \\
    --output edgar_wildfire.csv
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EFTS_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
DEFAULT_PAGE_SIZE = 100
REQUEST_PAUSE_SEC = 0.15

CSV_FIELDNAMES = [
    "score",
    "adsh",
    "form",
    "file_date",
    "file_type",
    "file_description",
    "root_forms",
    "ciks",
    "display_names",
    "_id",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Search SEC EDGAR full-text (EFTS) for a keyword."
    )
    p.add_argument(
        "--keyword",
        "-k",
        default="wilfdire",
        help='Search term (default: "wilfdire" as requested; use "wildfire" if that was a typo).',
    )
    p.add_argument(
        "--user-agent",
        "-U",
        default=os.environ.get("SEC_EDGAR_USER_AGENT", ""),
        help="HTTP User-Agent identifying you (required by SEC). "
        "Default: SEC_EDGAR_USER_AGENT env var.",
    )
    p.add_argument(
        "--forms",
        default="",
        help="Optional comma-separated form types, e.g. 10-K,10-Q,8-K",
    )
    p.add_argument(
        "--date-range",
        choices=["all", "custom"],
        default="all",
        help='Use "custom" with --start-date / --end-date (YYYY-MM-DD).',
    )
    p.add_argument("--start-date", default="", help="With --date-range custom")
    p.add_argument("--end-date", default="", help="With --date-range custom")
    p.add_argument(
        "--max-results",
        type=int,
        default=300,
        help="Stop after collecting this many hits (pagination).",
    )
    p.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"Results per request (default {DEFAULT_PAGE_SIZE}).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Write a JSON array of hits instead of CSV.",
    )
    p.add_argument(
        "--output",
        "-o",
        default="",
        metavar="PATH",
        help="Write results to this file (UTF-8). If omitted, writes to stdout.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stderr summary line.",
    )
    return p.parse_args()


def efts_request(
    *,
    keyword: str,
    user_agent: str,
    forms: str,
    date_range: str,
    start_date: str,
    end_date: str,
    page_from: int,
    page_size: int,
) -> dict:
    params: list[tuple[str, str]] = [
        ("q", keyword),
        ("from", str(page_from)),
        ("size", str(page_size)),
    ]
    if forms.strip():
        params.append(("forms", forms.strip()))
    if date_range == "custom":
        params.append(("dateRange", "custom"))
        if start_date:
            params.append(("startdt", start_date))
        if end_date:
            params.append(("enddt", end_date))

    url = EFTS_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def hit_to_row(hit: dict) -> dict[str, str]:
    src = hit.get("_source") or {}
    names = src.get("display_names") or []
    ciks = src.get("ciks") or []
    return {
        "score": str(hit.get("_score") or ""),
        "adsh": str(src.get("adsh") or ""),
        "form": str(src.get("form") or ""),
        "file_date": str(src.get("file_date") or ""),
        "file_type": str(src.get("file_type") or ""),
        "file_description": str(src.get("file_description") or ""),
        "root_forms": ",".join(src.get("root_forms") or []),
        "display_names": " | ".join(names) if names else "",
        "ciks": ",".join(str(c) for c in ciks),
        "_id": str(hit.get("_id") or ""),
    }


def main() -> int:
    args = parse_args()
    if not args.user_agent or len(args.user_agent.strip()) < 10:
        print(
            "Error: set a descriptive User-Agent (SEC policy).\n"
            "  export SEC_EDGAR_USER_AGENT='YourOrg tool/1.0 (you@example.com)'\n"
            "or pass  --user-agent '...'",
            file=sys.stderr,
        )
        return 2

    page_size = max(1, min(args.page_size, 100))
    all_rows: list[dict[str, str]] = []
    page_from = 0
    total_reported: dict | None = None

    try:
        while len(all_rows) < args.max_results:
            data = efts_request(
                keyword=args.keyword,
                user_agent=args.user_agent,
                forms=args.forms,
                date_range=args.date_range,
                start_date=args.start_date,
                end_date=args.end_date,
                page_from=page_from,
                page_size=page_size,
            )
            hits_block = data.get("hits") or {}
            total_reported = hits_block.get("total") or total_reported
            batch = hits_block.get("hits") or []
            if not batch:
                break
            for h in batch:
                all_rows.append(hit_to_row(h))
                if len(all_rows) >= args.max_results:
                    break
            page_from += len(batch)
            if len(batch) < page_size:
                break
            time.sleep(REQUEST_PAUSE_SEC)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}\n{e.read()[:500]!r}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    out_path = (args.output or "").strip()
    out_cm = (
        open(out_path, "w", encoding="utf-8", newline="")
        if out_path
        else contextlib.nullcontext(sys.stdout)
    )

    with out_cm as out:
        if not args.quiet:
            tv = (total_reported or {}).get("value")
            tr = (total_reported or {}).get("relation")
            loc = out_path if out_path else "stdout"
            print(
                f"# keyword={args.keyword!r}  total>={tv!r} relation={tr!r}  "
                f"returned={len(all_rows)}  -> {loc}",
                file=sys.stderr,
            )

        if args.json:
            json.dump(all_rows, out, indent=2)
            out.write("\n")
        else:
            w = csv.DictWriter(out, fieldnames=CSV_FIELDNAMES)
            w.writeheader()
            w.writerows(all_rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
