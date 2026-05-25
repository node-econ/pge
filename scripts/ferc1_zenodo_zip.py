#!/usr/bin/env python3
"""
Work with Catalyst / PUDL Zenodo **raw** FERC Form 1 XBRL ZIP bundles.

Record: https://zenodo.org/records/19947273

Examples:
  python3 scripts/ferc1_zenodo_zip.py download --file ferc1-xbrl-2025.zip
  python3 scripts/ferc1_zenodo_zip.py list ferc1-xbrl-2025.zip
  python3 scripts/ferc1_zenodo_zip.py extract ferc1-xbrl-2025.zip \\
      --member Portland_General_Electric_Company_form1_Q4_1776114777.xbrl \\
      --output-dir data/utilities/ferc1_extracted
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
import zipfile

ZENODO_RECORD = "19947273"
ZENODO_FILE_URL = (
    f"https://zenodo.org/records/{ZENODO_RECORD}/files/{{}}?download=1"
)


def default_zip_dir() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(root, "data", "utilities", "ferc1_raw_zips")


def cmd_download(args: argparse.Namespace) -> int:
    os.makedirs(args.dest_dir, exist_ok=True)
    dest = os.path.join(args.dest_dir, args.file)
    if os.path.isfile(dest) and not args.force:
        print(f"Exists (use --force): {dest}", file=sys.stderr)
        return 0
    url = ZENODO_FILE_URL.format(args.file)
    print(f"GET {url}", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "PGE-ferc1-tools/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as out:
        out.write(r.read())
    print(f"Wrote {dest}", file=sys.stderr)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    path = os.path.join(args.dest_dir, args.zip)
    with zipfile.ZipFile(path, "r") as z:
        for i, n in enumerate(sorted(z.namelist())):
            if args.match and args.match.lower() not in n.lower():
                continue
            zi = z.getinfo(n)
            print(f"{zi.file_size:10d}  {n}")
            if args.limit and i >= args.limit:
                break
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    path = os.path.join(args.dest_dir, args.zip)
    os.makedirs(args.output_dir, exist_ok=True)
    with zipfile.ZipFile(path, "r") as z:
        data = z.read(args.member)
    out = os.path.join(args.output_dir, os.path.basename(args.member))
    with open(out, "wb") as f:
        f.write(data)
    print(out, file=sys.stderr)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="FERC1 raw XBRL ZIP helper (Zenodo).")
    p.add_argument(
        "--dest-dir",
        default=default_zip_dir(),
        help="Directory holding downloaded ZIPs.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("download", help="Download a file from the Zenodo record.")
    d.add_argument("--file", required=True)
    d.add_argument("--force", action="store_true")
    d.set_defaults(func=cmd_download)

    l = sub.add_parser("list", help="List ZIP members (optional substring filter).")
    l.add_argument("zip")
    l.add_argument("--match", default="", help="Substring filter (case-insensitive).")
    l.add_argument("--limit", type=int, default=0)
    l.set_defaults(func=cmd_list)

    e = sub.add_parser("extract", help="Extract one member to a directory.")
    e.add_argument("zip")
    e.add_argument("--member", required=True)
    e.add_argument("--output-dir", required=True)
    e.set_defaults(func=cmd_extract)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
