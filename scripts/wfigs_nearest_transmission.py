#!/usr/bin/env python3
"""
Join **WFIGS incident points** (GeoJSON from ``wfigs_incident_locations_fetch.py``)
to the nearest **transmission line** segment in a shapefile (default:
``spatial/Transmission_Lines.shp``).

Each incident is optionally matched to **``web/NRI_Census_Tracts_PGE.geojson``**
(FEMA NRI tracts clipped for this repo): if the point lies inside a tract, **WFIR_RISKR**
is copied into the table/CSV/JSON; otherwise **WFIR_RISKR** is left blank. All Oregon
points in the input GeoJSON are retained (no service-area filter).

Distances are **horizontal** meters in **EPSG:5070** (NAD83 / Conus Albers), a
reasonable approximation for “how far is this fire from our line?” screening in
Oregon (default GeoJSON filter). Line geometries are assumed **EPSG:3857** (per the
shapefile’s ``.prj``); incident coordinates are **EPSG:4326**.

Requires **GDAL Python bindings** (``from osgeo import ogr, osr``), e.g. Homebrew
``brew install gdal`` then ``pip install gdal`` matching versions, or a conda env.

This is **decision-support screening**, not a geodesic audit for regulatory filings.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import subprocess
import sys
from typing import Any

try:
    from osgeo import ogr, osr
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "GDAL Python bindings are required (import osgeo.ogr, osgeo.osr). "
        "Install GDAL on your system and `pip install gdal` if needed."
    ) from e

ogr.UseExceptions()
osr.UseExceptions()

# NAD83 / Conus Albers (meters) — suitable for distance-based screening in the Pacific Northwest.
METRIC_EPSG = 5070
LINE_SOURCE_EPSG = 3857

FIRE_CSV_FIELDS = [
    "IrwinID",
    "GlobalID",
    "IncidentName",
    "POOState",
    "POOCounty",
    "PercentContained",
    "IncidentSize",
    "FireDiscoveryDateTime",
    "longitude",
    "latitude",
    "WFIR_RISKR",
]

LINE_ATTR_FIELDS = ["OBJECTID", "FENAME", "MILES", "Source", "GlobalID", "Edit_date"]


def _sr_epsg(code: int) -> osr.SpatialReference:
    sr = osr.SpatialReference()
    sr.ImportFromEPSG(code)
    if code == 4326:
        sr.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return sr


def _load_lines_metric(shp_path: pathlib.Path) -> list[tuple[ogr.Geometry, dict[str, Any]]]:
    """Return list of (geometry in EPSG:5070 meters, attribute dict)."""
    sr_line = _sr_epsg(LINE_SOURCE_EPSG)
    sr_metric = _sr_epsg(METRIC_EPSG)
    tr = osr.CoordinateTransformation(sr_line, sr_metric)

    ds = ogr.Open(str(shp_path))
    if ds is None:
        raise SystemExit(f"Could not open shapefile: {shp_path}")
    lyr = ds.GetLayer()
    out: list[tuple[ogr.Geometry, dict[str, Any]]] = []
    lyr.ResetReading()
    for feat in lyr:
        g = feat.GetGeometryRef()
        if g is None:
            continue
        gm = g.Clone()
        gm.Transform(tr)
        attrs: dict[str, Any] = {}
        for name in LINE_ATTR_FIELDS:
            attrs[name] = feat.GetField(name)
        out.append((gm, attrs))
    return out


def _nearest_line_m(
    pt_metric: ogr.Geometry,
    lines: list[tuple[ogr.Geometry, dict[str, Any]]],
) -> tuple[float, dict[str, Any]]:
    best_d = float("inf")
    best_a: dict[str, Any] = {}
    for geom, attrs in lines:
        d = pt_metric.Distance(geom)
        if d < best_d:
            best_d = d
            best_a = attrs
    return best_d, best_a


def _load_incident_geojson(path: pathlib.Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") != "FeatureCollection":
        raise SystemExit("GeoJSON must be a FeatureCollection")
    return data


def _load_nri_tract_geometries(geojson_path: pathlib.Path) -> list[tuple[ogr.Geometry, dict[str, Any]]]:
    """Tract polygons in WGS 84 with WFIR_RISKR from NRI attributes."""
    ds = ogr.Open(str(geojson_path))
    if ds is None:
        raise SystemExit(f"Could not open tracts GeoJSON: {geojson_path}")
    lyr = ds.GetLayer()
    sr4326 = _sr_epsg(4326)
    out: list[tuple[ogr.Geometry, dict[str, Any]]] = []
    lyr.ResetReading()
    for feat in lyr:
        g = feat.GetGeometryRef()
        if g is None:
            continue
        gc = g.Clone()
        if gc.GetSpatialReference() is None:
            gc.AssignSpatialReference(sr4326)
        wfir = feat.GetField("WFIR_RISKR")
        out.append(
            (
                gc,
                {
                    "WFIR_RISKR": "" if wfir is None else str(wfir),
                },
            )
        )
    return out


def _tract_containing_point(
    lon: float,
    lat: float,
    tracts: list[tuple[ogr.Geometry, dict[str, Any]]],
) -> dict[str, Any] | None:
    pt = ogr.CreateGeometryFromWkt(f"POINT ({lon} {lat})")
    pt.AssignSpatialReference(_sr_epsg(4326))
    for geom, attrs in tracts:
        if geom.Contains(pt):
            return attrs
    return None


def _write_csv(path: pathlib.Path, table: list[dict[str, Any]]) -> None:
    fieldnames = [
        *FIRE_CSV_FIELDS,
        "nearest_dist_m",
        "nearest_dist_mi",
        "line_OBJECTID",
        "line_FENAME",
        "line_MILES",
        "line_Source",
        "line_GlobalID",
        "line_Edit_date",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in table:
            w.writerow(row)


def _md_escape(s: Any) -> str:
    if s is None:
        return ""
    t = str(s).replace("|", "\\|").replace("\n", " ")
    return t[:200] + ("…" if len(t) > 200 else "")


def _write_markdown(path: pathlib.Path, table: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    lines_out: list[str] = [
        "# WFIGS incidents (Oregon) — nearest transmission line",
        "",
        "**WFIR_RISKR** is the FEMA NRI wildfire risk rating for the census tract in "
        "`web/NRI_Census_Tracts_PGE.geojson` that contains the incident point (blank if outside that layer or if the field is missing).",
        "",
        "Distances are **horizontal meters** in **EPSG:5070** (NAD83 / Conus Albers) from the incident point to the closest vertex/segment of the line geometry in `spatial/Transmission_Lines.shp` (Web Mercator → 5070).",
        "",
        "**Not** a substitute for field verification or official incident products.",
        "",
        f"- **Incident GeoJSON:** `{meta.get('geojson', '')}`",
        f"- **NRI tracts (WFIR lookup):** `{meta.get('nri_tracts_geojson', '')}`",
        f"- **Lines:** `{meta.get('lines_shp', '')}`",
        f"- **Generated (UTC):** `{meta.get('generated_utc', '')}`",
        "",
        "| Distance (Miles) | Incident | County | NRI tract WFIR_RISKR | Contain % | Acres | IrwinID | Line (FENAME) | Line OID |",
        "|---:|---|---|---|---|---:|---:|---|---:|",
    ]
    for row in sorted(table, key=lambda r: float(r["nearest_dist_m"])):
        mi = row.get("nearest_dist_mi", "")
        lines_out.append(
            f"| {mi} | {_md_escape(row.get('IncidentName'))} | {_md_escape(row.get('POOCounty'))} | "
            f"{_md_escape(row.get('WFIR_RISKR'))} | "
            f"{_md_escape(row.get('PercentContained'))} | {_md_escape(row.get('IncidentSize'))} | `{_md_escape(row.get('IrwinID'))}` | "
            f"{_md_escape(row.get('line_FENAME'))} | {_md_escape(row.get('line_OBJECTID'))} |"
        )
    lines_out.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")


def _write_json(path: pathlib.Path, table: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    """JSON for the demo HTML table (browser-friendly; same rows as CSV)."""
    payload = {"meta": meta, "rows": table}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _export_transmission_lines_wgs84(shp_path: pathlib.Path, out_path: pathlib.Path) -> bool:
    """
    Write all transmission features as GeoJSON in EPSG:4326 for Leaflet on the demo map.
    Returns True if the file was written successfully.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.is_file():
        out_path.unlink()
    try:
        subprocess.run(
            [
                "ogr2ogr",
                "-overwrite",
                "-f",
                "GeoJSON",
                "-t_srs",
                "EPSG:4326",
                str(out_path),
                str(shp_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print(
            "ogr2ogr not found on PATH; skipping transmission_lines_wgs84.geojson "
            "(map line highlight will be unavailable).",
            file=sys.stderr,
        )
        return False
    except subprocess.CalledProcessError as e:
        print(f"ogr2ogr failed ({e.returncode}): {e.stderr[:800]}", file=sys.stderr)
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(
        description="List each WFIGS incident with nearest transmission line segment."
    )
    ap.add_argument(
        "--geojson",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/wfigs_incident_locations_or.geojson"),
        help="FeatureCollection from wfigs_incident_locations_fetch.py (Oregon-wide by default).",
    )
    ap.add_argument(
        "--lines",
        type=pathlib.Path,
        default=pathlib.Path("spatial/Transmission_Lines.shp"),
        help="Transmission line shapefile (EPSG:3857 per .prj).",
    )
    ap.add_argument(
        "-o",
        "--csv-out",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/incidents_nearest_transmission.csv"),
        help="Output CSV path.",
    )
    ap.add_argument(
        "--md-out",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/incidents_nearest_transmission.md"),
        help="Output Markdown table path.",
    )
    ap.add_argument(
        "--json-out",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/incidents_nearest_transmission.json"),
        help="Output JSON for web/wfigs_incidents_or_wa.html embedded table.",
    )
    ap.add_argument(
        "--lines-geojson-out",
        type=pathlib.Path,
        default=pathlib.Path("data/wildfire/transmission_lines_wgs84.geojson"),
        help="GeoJSON (EPSG:4326) of all lines for the demo map overlay.",
    )
    ap.add_argument(
        "--skip-lines-geojson",
        action="store_true",
        help="Do not run ogr2ogr to refresh transmission_lines_wgs84.geojson.",
    )
    ap.add_argument(
        "--tracts-geojson",
        type=pathlib.Path,
        default=pathlib.Path("web/NRI_Census_Tracts_PGE.geojson"),
        help="NRI census tracts (PGE clip) for WFIR_RISKR point-in-polygon lookup.",
    )
    args = ap.parse_args()

    if not args.geojson.is_file():
        raise SystemExit(f"Missing GeoJSON: {args.geojson} (run wfigs_incident_locations_fetch.py first)")
    if not args.lines.is_file():
        raise SystemExit(f"Missing shapefile: {args.lines}")
    if not args.tracts_geojson.is_file():
        raise SystemExit(f"Missing tracts GeoJSON: {args.tracts_geojson}")

    sr_wgs = _sr_epsg(4326)
    sr_metric = _sr_epsg(METRIC_EPSG)
    tr_pt = osr.CoordinateTransformation(sr_wgs, sr_metric)

    lines_metric = _load_lines_metric(args.lines)
    if not lines_metric:
        raise SystemExit(f"No line features read from {args.lines}")

    tracts = _load_nri_tract_geometries(args.tracts_geojson)
    if not tracts:
        raise SystemExit(f"No tract geometries read from {args.tracts_geojson}")

    raw_fc = _load_incident_geojson(args.geojson)
    all_feats = raw_fc.get("features") or []
    point_count = 0
    for _f in all_feats:
        g = (_f.get("geometry") or {}) if isinstance(_f, dict) else {}
        if g.get("type") == "Point":
            point_count += 1
    if point_count == 0:
        raise SystemExit("No point features found in source GeoJSON")

    table: list[dict[str, Any]] = []

    for feat in all_feats:
        if not isinstance(feat, dict):
            continue
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon = float(coords[0])
        lat = float(coords[1])
        tract_attrs = _tract_containing_point(lon, lat, tracts)
        wfir = tract_attrs.get("WFIR_RISKR", "") if tract_attrs else ""

        props = dict(feat.get("properties") or {})
        props["longitude"] = lon
        props["latitude"] = lat

        pt = ogr.CreateGeometryFromWkt(f"POINT ({lon} {lat})")
        pt.AssignSpatialReference(sr_wgs)
        pt.Transform(tr_pt)
        dist_m, line_attrs = _nearest_line_m(pt, lines_metric)
        dist_mi = dist_m / 1609.344

        row = {k: props.get(k, "") for k in FIRE_CSV_FIELDS}
        row["WFIR_RISKR"] = wfir
        row["nearest_dist_m"] = round(dist_m, 1)
        row["nearest_dist_mi"] = round(dist_mi, 3)
        row["line_OBJECTID"] = line_attrs.get("OBJECTID", "")
        row["line_FENAME"] = line_attrs.get("FENAME", "")
        row["line_MILES"] = line_attrs.get("MILES", "")
        row["line_Source"] = line_attrs.get("Source", "")
        row["line_GlobalID"] = line_attrs.get("GlobalID", "")
        row["line_Edit_date"] = line_attrs.get("Edit_date", "")
        table.append(row)

    meta = {
        "geojson": str(args.geojson),
        "nri_tracts_geojson": str(args.tracts_geojson),
        "lines_shp": str(args.lines),
        "generated_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "line_count": len(lines_metric),
        "fire_count": len(table),
        "incident_point_count": point_count,
        "metric_crs": f"EPSG:{METRIC_EPSG}",
    }

    if not args.skip_lines_geojson:
        ok = _export_transmission_lines_wgs84(args.lines, args.lines_geojson_out)
        if ok and args.lines_geojson_out.is_file():
            meta["transmission_lines_geojson"] = str(args.lines_geojson_out)

    _write_csv(args.csv_out, table)
    _write_markdown(args.md_out, table, meta)
    _write_json(args.json_out, table, meta)

    print(f"Wrote {len(table)} rows to {args.csv_out}", file=sys.stderr)
    print(f"Wrote {args.md_out}", file=sys.stderr)
    print(f"Wrote {args.json_out}", file=sys.stderr)
    if not args.skip_lines_geojson and args.lines_geojson_out.is_file():
        print(f"Wrote {args.lines_geojson_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
