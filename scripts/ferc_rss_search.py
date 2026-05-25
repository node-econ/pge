#!/usr/bin/env python3
"""
Filter FERC eCollection accepted XBRL filings from the public RSS feed.

Endpoint (documented by FERC):
  https://ecollection.ferc.gov/api/rssfeed

The feed does **not** accept a company-name search parameter. It returns a
bounded set of the most recent accepted filings (~650). For older periods,
FERC supports month/year query parameters, e.g.:
  https://ecollection.ferc.gov/api/rssfeed?month=5&year=2022

This script downloads one or more feeds and **filters items client-side** whose
<title> or <description> contains your phrase (default: "Portland General").

References:
  https://www.ferc.gov/filing-forms/eforms-refresh (RSS feed behavior)
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import html
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

RSS_BASE = "https://ecollection.ferc.gov/api/rssfeed"
DOWNLOAD_RE = re.compile(
    r"https://eCollection\.ferc\.gov/api/DownloadDocument/[^\s'\"<>]+",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Filter FERC eCollection RSS filings by company / phrase."
    )
    p.add_argument(
        "--phrase",
        "-p",
        default="Portland General",
        help="Case-insensitive substring to match in item title or description.",
    )
    p.add_argument(
        "--month",
        type=int,
        metavar="M",
        help="Calendar month 1–12 (use with --year). Omit for the default “current” feed.",
    )
    p.add_argument(
        "--year",
        type=int,
        metavar="YYYY",
        help="Four-digit year (use with --month).",
    )
    p.add_argument(
        "--months",
        metavar="YYYY-MM",
        nargs="*",
        default=[],
        help="Additional feeds to merge, e.g. 2024-11 2024-12 (each becomes ?month=&year=). Ignored if --month/--year set.",
    )
    p.add_argument(
        "--user-agent",
        "-U",
        default="ferc-rss-search/1.0 (replace-with-your-contact)",
        help="HTTP User-Agent header.",
    )
    p.add_argument(
        "--output",
        "-o",
        default="",
        metavar="PATH",
        help="Write CSV to this path. Default: stdout.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stderr progress lines.",
    )
    return p.parse_args()


def rss_url(*, month: int | None, year: int | None) -> str:
    if month is not None and year is not None:
        q = urllib.parse.urlencode({"month": str(month), "year": str(year)})
        return f"{RSS_BASE}?{q}"
    if month is not None or year is not None:
        raise SystemExit("Error: specify both --month and --year, or neither.")
    return RSS_BASE


def fetch_rss(url: str, user_agent: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def parse_month_year_token(token: str) -> tuple[int, int]:
    parts = token.strip().split("-")
    if len(parts) != 2:
        raise ValueError(f"Expected YYYY-MM, got {token!r}")
    y, m = int(parts[0]), int(parts[1])
    if not (1 <= m <= 12 and 2000 <= y <= 2100):
        raise ValueError(f"Bad YYYY-MM: {token!r}")
    return m, y


def iter_items(xml_bytes: bytes):
    root = ET.fromstring(xml_bytes)
    for item in root.findall(".//item"):
        guid_el = item.findtext("guid", default="").strip()
        title = item.findtext("title", default="").strip()
        desc = item.findtext("description", default="")
        link = item.findtext("link", default="").strip()
        pub = item.findtext("pubDate", default="").strip()
        yield guid_el, title, desc, link, pub


def item_matches(phrase: str, title: str, description: str) -> bool:
    needle = phrase.casefold()
    blob = html.unescape(f"{title}\n{description}").casefold()
    return needle in blob


def extract_download_urls(description_html: str) -> str:
    text = html.unescape(description_html)
    urls = DOWNLOAD_RE.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return " | ".join(out)


def main() -> int:
    args = parse_args()
    phrase = args.phrase.strip()
    if not phrase:
        print("Error: empty --phrase", file=sys.stderr)
        return 2

    urls: list[str] = []
    if args.month is not None or args.year is not None:
        if args.month is None or args.year is None:
            print("Error: use both --month and --year together.", file=sys.stderr)
            return 2
        urls.append(rss_url(month=args.month, year=args.year))
    else:
        urls.append(rss_url(month=None, year=None))
        for tok in args.months:
            try:
                m, y = parse_month_year_token(tok)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                return 2
            urls.append(rss_url(month=m, year=y))

    rows: list[dict[str, str]] = []
    seen_guids: set[str] = set()

    for i, url in enumerate(urls):
        if not args.quiet:
            print(f"# fetching ({i + 1}/{len(urls)}) {url}", file=sys.stderr)
        try:
            raw = fetch_rss(url, args.user_agent)
        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return 1
        n_items = 0
        n_match = 0
        for guid, title, desc, link, pub in iter_items(raw):
            n_items += 1
            if not item_matches(phrase, title, desc):
                continue
            n_match += 1
            if guid in seen_guids:
                continue
            seen_guids.add(guid)
            rows.append(
                {
                    "guid": guid,
                    "title": title,
                    "pub_date": pub,
                    "link": link,
                    "download_urls": extract_download_urls(desc),
                    "description_excerpt": html.unescape(re.sub(r"\s+", " ", desc))[
                        :500
                    ],
                }
            )
        if not args.quiet:
            print(
                f"#   items={n_items} matched_phrase={n_match} unique_rows={len(rows)}",
                file=sys.stderr,
            )
        if i + 1 < len(urls):
            time.sleep(0.2)

    out_path = (args.output or "").strip()
    out_cm = (
        open(out_path, "w", encoding="utf-8", newline="")
        if out_path
        else contextlib.nullcontext(sys.stdout)
    )
    fieldnames = [
        "guid",
        "title",
        "pub_date",
        "link",
        "download_urls",
        "description_excerpt",
    ]
    with out_cm as out:
        w = csv.DictWriter(out, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    if not args.quiet:
        loc = out_path if out_path else "stdout"
        print(f"# wrote {len(rows)} row(s) -> {loc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
