# PGE

Utilities, data pipelines, and static dashboards around PG&E–adjacent topics (wildfire screening, FEMA National Risk Index exposure, FERC Form 1 summaries, and credit-spread tooling). The public site is built as plain static assets and deployed with **GitHub Pages** (see [`GITHUB_PAGES.md`](GITHUB_PAGES.md)).

**Copyright © 2026 Kyle Birchard.** This repository is released under the [**GNU General Public License v3.0 only**](LICENSE) (SPDX: `GPL-3.0-only`). Third-party datasets and map tiles have their own terms—see [`Citations.md`](Citations.md).

---

## Technology stack

### Core tooling

| Area | What we use |
|------|----------------|
| **Languages** | **Python 3** for ingestion, joins, and HTML generators (mostly the standard library: `argparse`, `csv`, `json`, `pathlib`, `urllib.request`, `datetime`, etc.). |
| **Geospatial** | **GDAL / OGR** (`osgeo.ogr`, `osgeo.osr`) and **`ogr2ogr`** for shapefile handling, reprojection, and some GeoJSON workflows. **GeoJSON** and **Esri Shapefile** are the usual interchange formats on disk. |
| **Tabular / config** | **CSV**, **JSON**, and simple **`.env`** key files where an API key is needed locally (never committed). |

### Published web UI (GitHub Pages)

| Area | What we use |
|------|----------------|
| **Pages & assets** | Hand-authored **HTML**, **CSS**, and **vanilla JavaScript** (no bundler on the main site). |
| **Maps** | [**Leaflet**](https://leafletjs.com/) **1.9.x** loaded from **unpkg**; basemaps from **OpenStreetMap** raster tiles (`tile.openstreetmap.org`) with OSM attribution. |
| **Charts** | [**Chart.js**](https://www.chartjs.org/) **4.4.x** from **jsDelivr** (borrowing-cost / OAS dashboard). |
| **Data on disk** | Static **GeoJSON**, **JSON**, and **CSV** committed under `data/` and `web/`; the FERC “viewer” is static HTML plus a generated JSON bundle. |

### CI / hosting

| Area | What we use |
|------|----------------|
| **Automation** | **GitHub Actions** ([`.github/workflows/github-pages.yml`](.github/workflows/github-pages.yml)): checkout, assemble `_site/`, **actions/upload-pages-artifact**, **actions/deploy-pages**. |
| **Hosting** | **GitHub Pages** (project site URL documented in `GITHUB_PAGES.md`). |

### External services (scripts / docs)

These are used by Python scripts or documented workflows; keys and live calls stay on your machine unless you add automation.

| Area | What we use |
|------|----------------|
| **Macro / credit** | **FRED** REST API (`api.stlouisfed.org`) for **ICE BofA** option-adjusted spread series (see `scripts/fred_ice_bofa_oas_tidy.py`). |
| **Wildfire** | **NIFC** ArcGIS **FeatureServer** (WFIGS current incident locations); see `scripts/wfigs_incident_locations_fetch.py`. |
| **Hazard / exposure** | **FEMA National Risk Index** tract attributes (documented in `scripts/nri_wfir_exposure_by_riskr.py` and related export scripts). |
| **Regulatory / financials** | **FERC Form 1** via **Zenodo** / **PUDL**-style XBRL bundles (`scripts/ferc1_zenodo_zip.py`, `scripts/ferc1_form1_export.py`). |
| **Filings search** | Optional **SEC EDGAR** full-text search endpoints in keyword utilities (see `scripts/` and `Citations.md`). |

### Optional subfolder: `wildfire-risk-map/`

A self-contained **Vite** + **React 19** + **TypeScript** app (see `wildfire-risk-map/package.json`): **react-leaflet**, **Leaflet**, **esri-leaflet**, **ESLint**. It is **not** part of the default GitHub Pages bundle unless you wire it in separately.

---

## Documentation index

| Doc | Purpose |
|-----|---------|
| [`scripts/README.md`](scripts/README.md) | Script-by-script usage. |
| [`GITHUB_PAGES.md`](GITHUB_PAGES.md) | Pages setup and deploy flow. |
| [`Citations.md`](Citations.md) | Data source attribution and links. |
| [`data/README.md`](data/README.md) | Generated outputs under `data/`. |
