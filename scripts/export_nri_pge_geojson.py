#!/usr/bin/env python3
"""
Export ``spatial/NRI_Census_Tracts_PGE.shp`` to GeoJSON (EPSG:4326) for web maps.

Requires **GDAL** ``ogr2ogr`` on PATH (e.g. ``brew install gdal`` on macOS).

Keeps a small attribute set for popups and file size (tract id, county, state abbreviation, wildfire risk, building and population exposure, WFIR_EALT), simplifies geometry slightly,
and writes ``web/NRI_Census_Tracts_PGE.geojson`` by default (used by ``nri_wfir_exposure.html``).

OpenStreetMap tile use: follow https://operations.osmfoundation.org/policies/tiles/
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Export NRI PGE tract shapefile to GeoJSON for Leaflet.")
    ap.add_argument(
        "--shp",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "spatial" / "NRI_Census_Tracts_PGE.shp",
        help="Input shapefile path (.shp)",
    )
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "web" / "NRI_Census_Tracts_PGE.geojson",
        help="Output GeoJSON path",
    )
    ap.add_argument(
        "--simplify",
        type=float,
        default=0.00025,
        help="OGR simplify tolerance in target CRS degrees (0 = no simplify)",
    )
    args = ap.parse_args()

    ogr = shutil.which("ogr2ogr")
    if not ogr:
        print("ogr2ogr not found; install GDAL (e.g. brew install gdal).", file=sys.stderr)
        sys.exit(1)

    if not args.shp.is_file():
        raise SystemExit(f"missing shapefile: {args.shp}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.is_file():
        args.out.unlink()

    cmd = [
        ogr,
        "-f",
        "GeoJSON",
        "-t_srs",
        "EPSG:4326",
        "-select",
        "TRACTFIPS,COUNTY,STATEABBRV,WFIR_RISKR,WFIR_EXPB,WFIR_EXPP,WFIR_EALT",
        "-lco",
        "COORDINATE_PRECISION=6",
    ]
    if args.simplify and args.simplify > 0:
        cmd.extend(["-simplify", str(args.simplify)])
    cmd.extend([str(args.out), str(args.shp)])

    subprocess.run(cmd, check=True)
    print(f"Wrote {args.out} ({args.out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
