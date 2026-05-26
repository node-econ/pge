#!/usr/bin/env python3
"""
Fetch **current** WFIGS wildland fire **incident point locations** from NIFC’s
public ArcGIS Feature Service and write **GeoJSON** (and optional **CSV**) for
rapid screening (e.g. utility / land manager situational awareness; default **Oregon**).

Data source (authoritative public layer; same program data as EGP / IRWIN-backed viewers):

  WFIGS_Incident_Locations_Current / layer 0
  https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0

Catalog / terms: https://data-nifc.opendata.arcgis.com/ — follow NIFC Open Data
license and attribution on any map or derivative product.

This script does **not** run ELMFIRE or WindNinja; it only produces clean
**ignition / incident coordinates** and attributes for downstream tools.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

# NIFC WFIGS — current incident points (not perimeters).
FEATURE_LAYER_QUERY = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Incident_Locations_Current/FeatureServer/0/query"
)

DEFAULT_STATES = ("US-OR",)

# ArcGIS layer maxRecordCount (see layer `?f=json`); use conservative page size.
PAGE_SIZE = 2000

# CSV columns useful for a quick human triage board (subset of layer fields).
CSV_FIELDS = [
    "IrwinID",
    "GlobalID",
    "IncidentName",
    "POOState",
    "POOCounty",
    "GACC",
    "IncidentTypeCategory",
    "IncidentTypeKind",
    "FireDiscoveryDateTime",
    "ModifiedOnDateTime_dt",
    "PercentContained",
    "IncidentSize",
    "DiscoveryAcres",
    "InitialLatitude",
    "InitialLongitude",
    "latitude",
    "longitude",
]


def _http_get_json(url: str, timeout_s: int, user_agent: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} from {url}: {e.read().decode('utf-8', errors='replace')[:500]}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Request failed for {url}: {e}") from e
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON from {url}: {e}") from e


def _build_where_clause(states: tuple[str, ...]) -> str:
    if not states:
        return "1=1"
    inner = ",".join("'" + s.replace("'", "''") + "'" for s in states)
    return f"POOState IN ({inner})"


def _query_page(
    *,
    where: str,
    offset: int,
    page_size: int,
    timeout_s: int,
    user_agent: str,
) -> dict:
    params = {
        "where": where,
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
        "resultOffset": str(offset),
        "resultRecordCount": str(page_size),
    }
    qs = urllib.parse.urlencode(params)
    url = f"{FEATURE_LAYER_QUERY}?{qs}"
    return _http_get_json(url, timeout_s=timeout_s, user_agent=user_agent)


def _fetch_all_features(
    *,
    states: tuple[str, ...],
    timeout_s: int,
    user_agent: str,
) -> list[dict]:
    where = _build_where_clause(states)
    features: list[dict] = []
    offset = 0
    while True:
        data = _query_page(
            where=where,
            offset=offset,
            page_size=PAGE_SIZE,
            timeout_s=timeout_s,
            user_agent=user_agent,
        )
        if "error" in data:
            raise SystemExit(f"ArcGIS error: {data['error']}")
        batch = data.get("features") or []
        features.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return features


def _point_in_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def _filter_by_bbox(features: list[dict], bbox: tuple[float, float, float, float]) -> list[dict]:
    out: list[dict] = []
    for feat in features:
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        if _point_in_bbox(lon, lat, bbox):
            out.append(feat)
    return out


def _write_geojson(path: str, features: list[dict], meta: dict) -> None:
    fc = {
        "type": "FeatureCollection",
        "features": features,
        # Non-standard keys — harmless for most GIS tools; useful for provenance.
        "_meta": meta,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fc, f, indent=2)


def _write_meta_json(path: str, meta: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def _write_csv(path: str, features: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for feat in features:
            props = dict(feat.get("properties") or {})
            geom = feat.get("geometry") or {}
            coords = geom.get("coordinates") or []
            if len(coords) >= 2:
                props["longitude"] = coords[0]
                props["latitude"] = coords[1]
            else:
                props["longitude"] = ""
                props["latitude"] = ""
            row = {k: props.get(k, "") for k in CSV_FIELDS}
            w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Fetch WFIGS current incident locations and write GeoJSON / CSV."
    )
    ap.add_argument(
        "--states",
        default=",".join(DEFAULT_STATES),
        help=f"Comma-separated POOState values (default: {','.join(DEFAULT_STATES)}).",
    )
    ap.add_argument(
        "--bbox",
        metavar="W,S,E,N",
        help="Optional filter: min_lon,min_lat,max_lon,max_lat (WGS 84). Applied after fetch.",
    )
    ap.add_argument(
        "-o",
        "--geojson-out",
        default="data/wildfire/wfigs_incident_locations_or.geojson",
        help="Output GeoJSON path.",
    )
    ap.add_argument(
        "--csv-out",
        default="",
        help="If set, write a triage-oriented CSV to this path.",
    )
    ap.add_argument(
        "--meta-out",
        default="",
        help="If set, write fetch metadata JSON to this path (default: same basename as GeoJSON with .meta.json).",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout seconds (default: 60).",
    )
    ap.add_argument(
        "--user-agent",
        default="PGE-wfigs-fetch/1.0 (+https://github.com/)",
        help="Identify your organization in the User-Agent string.",
    )
    args = ap.parse_args()

    states = tuple(s.strip() for s in args.states.split(",") if s.strip())
    bbox: tuple[float, float, float, float] | None = None
    if args.bbox:
        parts = [p.strip() for p in args.bbox.split(",")]
        if len(parts) != 4:
            ap.error("--bbox must be four comma-separated numbers: min_lon,min_lat,max_lon,max_lat")
        try:
            bbox = tuple(float(x) for x in parts)  # type: ignore[assignment]
        except ValueError as e:
            ap.error(f"Invalid --bbox: {e}")

    features = _fetch_all_features(
        states=states,
        timeout_s=args.timeout,
        user_agent=args.user_agent,
    )
    if bbox is not None:
        features = _filter_by_bbox(features, bbox)

    fetched_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    meta = {
        "fetched_at_utc": fetched_at,
        "source": FEATURE_LAYER_QUERY,
        "where_clause": _build_where_clause(states),
        "states": list(states),
        "bbox_wsen": list(bbox) if bbox else None,
        "feature_count": len(features),
        "attribution": "National Interagency Fire Center (NIFC) / WFIGS — verify license on data-nifc.opendata.arcgis.com",
    }

    geo_path = args.geojson_out
    _write_geojson(geo_path, features, meta)

    geo_p = pathlib.Path(geo_path)
    meta_path = args.meta_out or str(geo_p.with_suffix(".meta.json"))
    _write_meta_json(meta_path, meta)

    if args.csv_out:
        _write_csv(args.csv_out, features)

    print(f"Wrote {len(features)} features to {geo_path}", file=sys.stderr)
    print(f"Wrote metadata to {meta_path}", file=sys.stderr)
    if args.csv_out:
        print(f"Wrote CSV to {args.csv_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
