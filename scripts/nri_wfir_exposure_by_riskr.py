#!/usr/bin/env python3
"""
Wildfire (WFIR) exposure by wildfire risk rating (WFIR_RISKR) from an NRI census-tract
shapefile attribute table (.dbf only — no geometry).

Produces CSV + Markdown under ``spatial/``, and a static HTML page under ``web/`` for GitHub Pages.

- **WFIR_EXPB**: building exposure, tabulated in **millions of USD** (2 decimal places).
- **WFIR_EXPP**: population exposure, tabulated in **millions of persons** (2 decimal places) — not dollars;
  NRI defines this field as population-type exposure.

Rows are sorted **highest risk first** (Very High → … → Very Low), then No Rating / missing.

NRI field definitions: https://hazards.fema.gov/nri/technical-documentation
"""

from __future__ import annotations

import argparse
import csv
import html
import struct
from collections import defaultdict
from pathlib import Path


# Highest risk first; unknown labels sort after "(missing)"
RISK_ROW_ORDER_DESC: tuple[str, ...] = (
    "Very High",
    "Relatively High",
    "Relatively Moderate",
    "Relatively Low",
    "Very Low",
    "No Rating",
    "(missing)",
)


def parse_dbf_header(data: bytes) -> tuple[int, int, int, list[tuple[str, str, int, int]]]:
    """Return (n_records, header_len, record_len, [(name, type, len, dec), ...])."""
    _ver, _yy, _mm, _dd, nrec, hlen, rlen = struct.unpack_from("<4B I H H", data, 0)
    pos = 32
    fields: list[tuple[str, str, int, int]] = []
    while pos < hlen:
        blk = data[pos : pos + 32]
        if len(blk) < 32 or blk[0] == 0x0D:
            break
        name = blk[0:11].split(b"\x00")[0].decode("latin-1", errors="replace").strip()
        ftype = chr(blk[11])
        flen = blk[16]
        fdec = blk[17]
        fields.append((name, ftype, flen, fdec))
        pos += 32
    return nrec, hlen, rlen, fields


def field_offsets(fields: list[tuple[str, str, int, int]]) -> dict[str, tuple[int, int, str, int]]:
    off = 1
    out: dict[str, tuple[int, int, str, int]] = {}
    for name, ftype, flen, fdec in fields:
        out[name] = (off, flen, ftype, fdec)
        off += flen
    return out


def get_field(rec: bytes, fo: dict[str, tuple[int, int, str, int]], fname: str) -> float | int | str | None:
    off, flen, ftype, fdec = fo[fname]
    raw = rec[off : off + flen]
    if ftype == "C":
        t = raw.split(b"\x00")[0].decode("latin-1", errors="replace").strip()
        return t if t else None
    if ftype == "N":
        s = raw.decode("latin-1").strip()
        if not s or s == "*":
            return None
        if fdec:
            return float(s)
        try:
            return int(s)
        except ValueError:
            return float(s)
    return None


def iter_records(data: bytes, nrec: int, hlen: int, rlen: int):
    for i in range(nrec):
        rec = data[hlen + i * rlen : hlen + (i + 1) * rlen]
        if len(rec) < rlen:
            return
        if rec[0:1] == b"*":
            continue
        yield rec


def sort_key_rating_desc(label: str) -> int:
    try:
        return RISK_ROW_ORDER_DESC.index(label)
    except ValueError:
        return len(RISK_ROW_ORDER_DESC)


def fmt_m_usd(value: float) -> str:
    return f"{value / 1e6:.2f}"


def fmt_m_persons(value: float) -> str:
    return f"{value / 1e6:.2f}"


def fmt_persons_int(value: float) -> str:
    """Whole persons (EXPP means are tiny in 'millions' units)."""
    return f"{int(round(value)):,}"


def build_html(rows: list[tuple[str, dict[str, float]]]) -> str:
    """rows: (label, {tracts, expb, expp}) sorted for display."""
    tr_b = []
    tr_p = []
    for label, v in rows:
        n = int(v["tracts"])
        s_b = float(v["expb"])
        s_p = float(v["expp"])
        mean_b = s_b / n if n else 0.0
        mean_p = s_p / n if n else 0.0
        esc = html.escape(label)
        tr_b.append(
            f"<tr><td>{esc}</td><td class=\"num\">{n}</td>"
            f"<td class=\"num\">{fmt_m_usd(s_b)}</td><td class=\"num\">{fmt_m_usd(mean_b)}</td></tr>"
        )
        tr_p.append(
            f"<tr><td>{esc}</td><td class=\"num\">{n}</td>"
            f"<td class=\"num\">{fmt_m_persons(s_p)}</td><td class=\"num\">{fmt_persons_int(mean_p)}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>NRI wildfire exposure by risk rating</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem; background: #f1f5f9; color: #0f172a; }}
  h1 {{ font-size: 1.2rem; margin: 0 0 0.5rem; }}
  h2 {{ font-size: 1.05rem; margin: 1.25rem 0 0.5rem; color: #0f172a; }}
  p.meta {{ font-size: 0.82rem; color: #64748b; margin: 0 0 1rem; line-height: 1.45; max-width: 52rem; }}
  p.back {{ font-size: 0.88rem; margin: 0 0 1rem; }}
  .wrap {{ max-width: 52rem; margin: 0 auto 1rem; background: #fff; padding: 1rem 1.25rem; border-radius: 8px;
    box-shadow: 0 1px 3px rgb(0 0 0 / 0.08); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 0.35rem; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 0.45rem 0.55rem; text-align: left; }}
  th {{ background: #f8fafc; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tbody tr:nth-child(even) {{ background: #fafafa; }}
  a {{ color: #2563eb; }}
</style>
</head>
<body>
  <p class="back"><a href="index.html">← PGE reports</a></p>
  <div class="wrap">
    <h1>NRI wildfire: exposure by risk rating</h1>
    <p class="meta">FEMA National Risk Index census tracts (PGE clip). Rows: <strong>WFIR_RISKR</strong> (highest risk first).
      <strong>WFIR_EXPB</strong> = building exposure — sums and per-tract means in <strong>millions of USD</strong> (2 dp).
      <strong>WFIR_EXPP</strong> = population exposure — <strong>sum</strong> in millions of persons (2 dp); <strong>mean per tract</strong> in whole persons (not dollars).
      Source: <code>NRI_Census_Tracts_PGE.dbf</code>. Not a FEMA publication; confirm definitions in the
      <a href="https://hazards.fema.gov/nri/technical-documentation">NRI technical documentation</a>.</p>
    <h2>1. Building exposure (WFIR_EXPB) by WFIR_RISKR</h2>
    <table>
      <thead><tr><th>WFIR_RISKR</th><th class="num">Tracts</th><th class="num">Sum (M USD)</th><th class="num">Mean per tract (M USD)</th></tr></thead>
      <tbody>
{chr(10).join(tr_b)}
      </tbody>
    </table>
    <h2>2. Population exposure (WFIR_EXPP) by WFIR_RISKR</h2>
    <table>
      <thead><tr><th>WFIR_RISKR</th><th class="num">Tracts</th><th class="num">Sum (M persons)</th><th class="num">Mean per tract (persons)</th></tr></thead>
      <tbody>
{chr(10).join(tr_p)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="WFIR building/pop exposure by WFIR_RISKR (NRI tract .dbf).")
    ap.add_argument(
        "--dbf",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "spatial" / "NRI_Census_Tracts_PGE.dbf",
        help="Path to NRI tract .dbf",
    )
    ap.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "spatial",
        help="Directory for CSV and Markdown output",
    )
    ap.add_argument(
        "--html-out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "web" / "nri_wfir_exposure.html",
        help="Path for generated static HTML (GitHub Pages)",
    )
    args = ap.parse_args()

    data = args.dbf.read_bytes()
    nrec, hlen, rlen, fields = parse_dbf_header(data)
    fo = field_offsets(fields)
    for req in ("WFIR_RISKR", "WFIR_EXPB", "WFIR_EXPP"):
        if req not in fo:
            raise SystemExit(f"missing column {req} in {args.dbf}")

    agg: dict[str, dict[str, float]] = defaultdict(lambda: {"tracts": 0, "expb": 0.0, "expp": 0.0})
    for rec in iter_records(data, nrec, hlen, rlen):
        r = get_field(rec, fo, "WFIR_RISKR")
        key = r if isinstance(r, str) else "(missing)"
        b = get_field(rec, fo, "WFIR_EXPB")
        p = get_field(rec, fo, "WFIR_EXPP")
        cell = agg[key]
        cell["tracts"] += 1
        if isinstance(b, (int, float)):
            cell["expb"] += float(b)
        if isinstance(p, (int, float)):
            cell["expp"] += float(p)

    rows = sorted(agg.items(), key=lambda kv: sort_key_rating_desc(kv[0]))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.html_out.parent.mkdir(parents=True, exist_ok=True)

    md_path = args.out_dir / "nri_wfir_exposure_by_riskr.md"
    csv_b = args.out_dir / "nri_wfir_expb_by_riskr.csv"
    csv_p = args.out_dir / "nri_wfir_expp_by_riskr.csv"

    with csv_b.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "WFIR_RISKR",
                "tract_count",
                "WFIR_EXPB_sum_millions_usd",
                "WFIR_EXPB_mean_millions_usd_per_tract",
            ]
        )
        for label, v in rows:
            n = int(v["tracts"])
            s = v["expb"]
            w.writerow([label, n, fmt_m_usd(s), fmt_m_usd(s / n) if n else ""])

    with csv_p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "WFIR_RISKR",
                "tract_count",
                "WFIR_EXPP_sum_millions_persons",
                "WFIR_EXPP_mean_persons_per_tract",
            ]
        )
        for label, v in rows:
            n = int(v["tracts"])
            s = v["expp"]
            mean_p = s / n if n else 0.0
            w.writerow([label, n, fmt_m_persons(s), int(round(mean_p)) if n else ""])

    lines = [
        "# NRI wildfire: exposure by wildfire risk rating",
        "",
        "Source: `NRI_Census_Tracts_PGE.dbf` (FEMA National Risk Index, wildfire fields).",
        "Rows are **WFIR_RISKR** sorted **highest risk first**; **tract_count** = census tracts in that category.",
        "",
        "**WFIR_EXPB** values are in **millions of USD** (2 decimal places). **WFIR_EXPP** sums are in **millions of persons** (2 dp); means are **whole persons per tract** (not dollars).",
        "",
        "## 1. WFIR_EXPB (building exposure) by WFIR_RISKR",
        "",
        "| WFIR_RISKR | Tracts | Sum (M USD) | Mean per tract (M USD) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, v in rows:
        n = int(v["tracts"])
        s = v["expb"]
        mean = s / n if n else 0.0
        lines.append(f"| {label} | {n} | {fmt_m_usd(s)} | {fmt_m_usd(mean)} |")

    lines.extend(
        [
            "",
            "## 2. WFIR_EXPP (population exposure) by WFIR_RISKR",
            "",
        "| WFIR_RISKR | Tracts | Sum (M persons) | Mean per tract (persons) |",
        "| --- | ---: | ---: | ---: |",
        ]
    )
    for label, v in rows:
        n = int(v["tracts"])
        s = v["expp"]
        mean = s / n if n else 0.0
        lines.append(f"| {label} | {n} | {fmt_m_persons(s)} | {fmt_persons_int(mean)} |")

    lines.append("")
    lines.append("Not a FEMA publication; confirm units in the NRI technical documentation.")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    args.html_out.write_text(build_html(rows), encoding="utf-8")

    print(f"Wrote {csv_b}")
    print(f"Wrote {csv_p}")
    print(f"Wrote {md_path}")
    print(f"Wrote {args.html_out}")


if __name__ == "__main__":
    main()
