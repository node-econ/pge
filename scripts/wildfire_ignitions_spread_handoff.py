#!/usr/bin/env python3
"""
Build a **handoff document** from ``incidents_nearest_transmission.json`` so you can
take Oregon WFIGS ignitions into an **ELMFIRE** + **WindNinja** spread workflow.

This script does **not** run ELMFIRE or WindNinja. It writes Markdown with:

- One section per incident (WGS84 coordinates, IrwinID, nearest-line metadata)
- Copy-paste **Cloudfire** ``fuel_wx_ign.py`` stubs (ELMFIRE Tutorial 03 pattern) centered on each point
- Pointers to where **``X_IGN`` / ``Y_IGN``** live in the ELMFIRE namelist after you build the domain

Requires **stdlib only**. Run after:

    python3 scripts/wfigs_nearest_transmission.py
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def _md_esc(s: object) -> str:
    if s is None:
        return ""
    return str(s).replace("|", "\\|")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Write Markdown handoff for ELMFIRE/WindNinja from incidents_nearest_transmission.json."
    )
    ap.add_argument(
        "--json",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/incidents_nearest_transmission.json"),
        help="Output from wfigs_nearest_transmission.py",
    )
    ap.add_argument(
        "-o",
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/ignitions_spread_model_handoff.md"),
        help="Output Markdown path.",
    )
    ap.add_argument(
        "--top",
        type=int,
        default=0,
        help="If >0, only include the N closest incidents (by miles).",
    )
    args = ap.parse_args()

    if not args.json.is_file():
        raise SystemExit(f"Missing {args.json} — run wfigs_nearest_transmission.py first.")

    with open(args.json, encoding="utf-8") as f:
        payload = json.load(f)
    rows = list(payload.get("rows") or [])
    rows.sort(key=lambda r: float(r.get("nearest_dist_mi") or 1e9))
    if args.top and args.top > 0:
        rows = rows[: args.top]

    meta = payload.get("meta") or {}
    lines = [
        "# Ignition → spread model handoff",
        "",
        "Generated from this repo’s **nearest-transmission** join. Coordinates are **EPSG:4326** (WGS 84).",
        "",
        f"- **Incident GeoJSON:** `{meta.get('geojson', '')}`",
        f"- **Transmission lines shapefile:** `{meta.get('lines_shp', '')}`",
        f"- **Join generated (UTC):** `{meta.get('generated_utc', '')}`",
        "",
        "See **`docs/wildfire_ignition_spread_model.md`** (repo root) for the full ignition + WindNinja + ELMFIRE workflow.",
        "",
        "---",
        "",
        "## Per-incident stubs (ELMFIRE Cloudfire tile fetch)",
        "",
        "After [ELMFIRE](https://elmfire.io/) and **Cloudfire** are installed per Tutorial 03, use the incident center as "
        "``--center_lon`` / ``--center_lat`` (adjust ``--fuel_version``, ``--outdir``, ``--name``). "
        "Then set ``NUM_IGNITIONS``, ``X_IGN``, ``Y_IGN``, ``T_IGN`` in the ``&SIMULATOR`` group in **projected** model coordinates "
        "([Tutorial 02](https://elmfire.io/tutorials/tutorial_02.html)).",
        "",
    ]

    for i, row in enumerate(rows, start=1):
        name = _md_esc(row.get("IncidentName") or "(unnamed)")
        lon = row.get("longitude")
        lat = row.get("latitude")
        irwin = _md_esc(row.get("IrwinID"))
        county = _md_esc(row.get("POOCounty"))
        dist_mi = row.get("nearest_dist_mi")
        line_oid = row.get("line_OBJECTID")
        lines.append(f"### {i}. {name}")
        lines.append("")
        lines.append(f"- **County:** {county}")
        lines.append(f"- **IrwinID:** `{irwin}`")
        lines.append(f"- **WGS84:** `{lon}`, `{lat}`")
        lines.append(f"- **Nearest transmission OBJECTID:** {line_oid} (~{dist_mi} mi per screening join)")
        lines.append("")
        if lon is not None and lat is not None:
            try:
                lo = float(lon)
                la = float(lat)
            except (TypeError, ValueError):
                lines.append("*(Invalid lon/lat — skip Cloudfire stub.)*")
                lines.append("")
                continue
            slug = "".join(c if c.isalnum() else "_" for c in str(row.get("IncidentName") or "incident"))[:40].strip("_")
            lines.append("```bash")
            lines.append("# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).")
            lines.append("fuel_wx_ign.py \\")
            lines.append("  --do_wx=False --do_ignition=False \\")
            lines.append(f"  --center_lon={lo} --center_lat={la} \\")
            lines.append("  --fuel_source='landfire' --fuel_version='2.2.0' \\")
            lines.append(f"  --outdir='./fuel' --name='{slug or 'incident'}'")
            lines.append("```")
        lines.append("")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({len(rows)} incidents)", file=sys.stderr)


if __name__ == "__main__":
    main()
