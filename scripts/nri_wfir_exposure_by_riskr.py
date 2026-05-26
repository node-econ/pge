#!/usr/bin/env python3
"""
Wildfire (WFIR) exposure by wildfire risk rating (WFIR_RISKR) from an NRI census-tract
shapefile attribute table (.dbf only — no geometry).

Produces CSV + Markdown under ``spatial/``, and a static HTML page under ``web/`` for GitHub Pages.

- **WFIR_EXPB**: building exposure total per rating — **millions of USD** with a **$** prefix and comma grouping (2 dp).
- **WFIR_EXPP**: population exposure total per rating — **whole persons** with comma grouping (no means).

Rows are sorted **highest risk first** (Very High → … → Very Low), then No Rating / missing.

The HTML page includes a **Leaflet** map with **OpenStreetMap** tiles and tract polygons loaded from
``NRI_Census_Tracts_PGE.geojson`` (generate with ``scripts/export_nri_pge_geojson.py``).

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


def fmt_usd_millions(value: float) -> str:
    """Millions of USD with $ and comma grouping (2 dp)."""
    return f"${value / 1e6:,.2f}"


def fmt_persons_sum(value: float) -> str:
    return f"{int(round(value)):,}"


def build_html(rows: list[tuple[str, dict[str, float]]]) -> str:
    """rows: (label, {tracts, expb, expp}) sorted for display."""
    tr_b: list[str] = []
    tr_p: list[str] = []
    for label, v in rows:
        n = int(v["tracts"])
        s_b = float(v["expb"])
        s_p = float(v["expp"])
        esc = html.escape(label)
        tr_b.append(
            f"<tr><td>{esc}</td><td class=\"num\">{n}</td><td class=\"num\">{fmt_usd_millions(s_b)}</td></tr>"
        )
        tr_p.append(
            f"<tr><td>{esc}</td><td class=\"num\">{n}</td><td class=\"num\">{fmt_persons_sum(s_p)}</td></tr>"
        )

    table_b = "\n".join(tr_b)
    table_p = "\n".join(tr_p)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>NRI wildfire exposure by risk rating</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
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
  #map {{ height: min(52vh, 520px); width: 100%; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 0.35rem; }}
  .map-note {{ font-size: 0.78rem; color: #64748b; margin: 0.35rem 0 0; }}
</style>
</head>
<body>
  <p class="back"><a href="index.html">← PGE reports</a></p>
  <div class="wrap">
    <h1>NRI wildfire: exposure by risk rating</h1>
    <p class="meta">FEMA National Risk Index census tracts (PGE clip). Rows: <strong>WFIR_RISKR</strong> (highest risk first).
      <strong>WFIR_EXPB</strong> = building exposure — <strong>total</strong> in millions of USD (table shows <strong>$</strong> with comma grouping).
      <strong>WFIR_EXPP</strong> = population exposure — <strong>total persons</strong> (comma grouping).
      Source: <code>NRI_Census_Tracts_PGE.dbf</code>. Map: tract boundaries from <code>NRI_Census_Tracts_PGE.geojson</code> (EPSG:4326, simplified) over
      <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>. Not a FEMA publication; confirm definitions in the
      <a href="https://hazards.fema.gov/nri/technical-documentation">NRI technical documentation</a>.</p>
    <h2>Tract map (wildfire risk rating)</h2>
    <div id="map" role="img" aria-label="Map of NRI census tracts colored by WFIR_RISKR"></div>
    <p class="map-note">Tiles © OpenStreetMap contributors. Click a tract for attributes.</p>
    <h2>1. Building exposure (WFIR_EXPB) by WFIR_RISKR</h2>
    <table>
      <thead><tr><th>WFIR_RISKR</th><th class="num">Tracts</th><th class="num">Sum (million USD)</th></tr></thead>
      <tbody>
{table_b}
      </tbody>
    </table>
    <h2>2. Population exposure (WFIR_EXPP) by WFIR_RISKR</h2>
    <table>
      <thead><tr><th>WFIR_RISKR</th><th class="num">Tracts</th><th class="num">Sum (persons)</th></tr></thead>
      <tbody>
{table_p}
      </tbody>
    </table>
  </div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
(function () {{
  const GEOJSON_URL = 'NRI_Census_Tracts_PGE.geojson';
  const map = L.map('map', {{ scrollWheelZoom: false }}).setView([44.2, -123.0], 8);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  }}).addTo(map);

  function wfirColor(r) {{
    switch (r) {{
      case 'Very High': return '#7f1d1d';
      case 'Relatively High': return '#dc2626';
      case 'Relatively Moderate': return '#ea580c';
      case 'Relatively Low': return '#ca8a04';
      case 'Very Low': return '#16a34a';
      case 'No Rating': return '#94a3b8';
      default: return '#64748b';
    }}
  }}

  function fmtUsdM(v) {{
    if (v == null || isNaN(v)) return '—';
    return '$' + (Number(v) / 1e6).toLocaleString(undefined, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}) + 'M';
  }}
  function fmtPop(v) {{
    if (v == null || isNaN(v)) return '—';
    return Math.round(Number(v)).toLocaleString();
  }}

  fetch(GEOJSON_URL)
    .then(function (r) {{ if (!r.ok) throw new Error(r.status); return r.json(); }})
    .then(function (data) {{
      const layer = L.geoJSON(data, {{
        style: function (feature) {{
          const r = feature.properties.WFIR_RISKR;
          return {{
            color: '#334155',
            weight: 0.6,
            fillColor: wfirColor(r),
            fillOpacity: 0.55
          }};
        }},
        onEachFeature: function (feature, lyr) {{
          const p = feature.properties || {{}};
          const lines = [
            '<strong>' + (p.TRACTFIPS || '') + '</strong>',
            p.COUNTY ? 'County: ' + p.COUNTY : '',
            p.WFIR_RISKR ? 'Wildfire risk: ' + p.WFIR_RISKR : '',
            'Building exposure: ' + fmtUsdM(p.WFIR_EXPB),
            'Population exposure: ' + fmtPop(p.WFIR_EXPP) + ' persons'
          ].filter(Boolean);
          lyr.bindPopup(lines.join('<br/>'));
        }}
      }}).addTo(map);
      map.fitBounds(layer.getBounds(), {{ padding: [18, 18] }});
    }})
    .catch(function () {{
      document.getElementById('map').innerHTML =
        '<p style="padding:1rem;color:#b45309;">Could not load tract GeoJSON. Run <code>python3 scripts/export_nri_pge_geojson.py</code> and publish <code>NRI_Census_Tracts_PGE.geojson</code> next to this page.</p>';
    }});
}})();
</script>
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
        w.writerow(["WFIR_RISKR", "tract_count", "WFIR_EXPB_sum_millions_usd"])
        for label, v in rows:
            n = int(v["tracts"])
            s = v["expb"]
            w.writerow([label, n, f"{s / 1e6:.2f}"])

    with csv_p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["WFIR_RISKR", "tract_count", "WFIR_EXPP_sum_persons"])
        for label, v in rows:
            n = int(v["tracts"])
            s = v["expp"]
            w.writerow([label, n, int(round(s)) if n else ""])

    lines = [
        "# NRI wildfire: exposure by wildfire risk rating",
        "",
        "Source: `NRI_Census_Tracts_PGE.dbf` (FEMA National Risk Index, wildfire fields).",
        "Rows are **WFIR_RISKR** sorted **highest risk first**; **tract_count** = census tracts in that category.",
        "",
        "**WFIR_EXPB** total per row: **millions of USD** (numeric column in CSV; Markdown shows **$** with commas). **WFIR_EXPP** total: **persons** (whole numbers).",
        "",
        "## 1. WFIR_EXPB (building exposure) by WFIR_RISKR",
        "",
        "| WFIR_RISKR | Tracts | Sum (million USD) |",
        "| --- | ---: | ---: |",
    ]
    for label, v in rows:
        n = int(v["tracts"])
        s = v["expb"]
        lines.append(f"| {label} | {n} | {fmt_usd_millions(s)} |")

    lines.extend(
        [
            "",
            "## 2. WFIR_EXPP (population exposure) by WFIR_RISKR",
            "",
            "| WFIR_RISKR | Tracts | Sum (persons) |",
            "| --- | ---: | ---: |",
        ]
    )
    for label, v in rows:
        n = int(v["tracts"])
        s = v["expp"]
        lines.append(f"| {label} | {n} | {fmt_persons_sum(s)} |")

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
