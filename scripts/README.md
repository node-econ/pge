# Utility scripts

## `sec_edgar_keyword_search.py`

Full-text search against SEC EDGAR via `efts.sec.gov` (no API key).

```bash
export SEC_EDGAR_USER_AGENT="birchard@pdx.edu"
python3 scripts/sec_edgar_keyword_search.py --keyword wildfire --output results.csv
```

Omit `--output` to print CSV to **stdout**. Progress / counts go to **stderr** so `> results.csv` stays a clean CSV if you prefer shell redirection.

The SEC requires a truthful **User-Agent** that identifies the requester. See [SEC developer resources](https://www.sec.gov/about/developer-resources).

Default keyword is `wilfdire` (as requested). If you meant **wildfire**, pass `-k wildfire`.

## `ferc_rss_search.py`

FERC’s [eCollection RSS feed](https://ecollection.ferc.gov/api/rssfeed) lists **accepted XBRL filings**; there is **no server-side “company name” query**—you pull the feed (optionally by **month/year**) and filter locally.

- **Default feed**: last ~**650** filings (per [FERC eForms refresh](https://www.ferc.gov/filing-forms/eforms-refresh)).
- **Historical**: `?month=M&year=YYYY` (same page documents this).

```bash
python3 scripts/ferc_rss_search.py --phrase "Portland General" -o ferc_pge.csv
python3 scripts/ferc_rss_search.py --month 4 --year 2026 -p "Portland General" -o ferc_pge_apr2026.csv
python3 scripts/ferc_rss_search.py --months 2025-01 2025-02 -p "Portland General" -o out.csv
```

With `--months`, the script fetches the **current** default feed first, then each listed month (dedupes by `guid`). Set `--user-agent` / `-U` to identify your client.

Output CSV columns: `guid`, `title`, `pub_date`, `link`, `download_urls`, `description_excerpt`.

## `fred_ice_bofa_oas_tidy.py`

Pulls **ICE BofA option-adjusted spread** (OAS) from the [FRED API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) for **discrete rating buckets only** (AAA, AA, A, BBB, BB, B, CCC & lower) and writes a **tidy** long CSV: one row per `(observation_date, rating_bucket)`. It also appends a synthetic **BBB+** row per date as the **mean of the A and BBB** OAS for that date (`fred_series_id` documents the blend).

Loads **`FRED_API_KEY` from the repo `.env`** if the variable is not already set in the environment.

```bash
python3 scripts/fred_ice_bofa_oas_tidy.py --years 2
python3 scripts/fred_ice_bofa_oas_tidy.py --start-date 2024-05-22 --end-date 2026-05-22 -o data/utilities/ice_bofa_oas_tidy.csv
```

Default output: `data/utilities/ice_bofa_oas_tidy.csv`.

Columns: `observation_date`, `rating_bucket`, `fred_index_segment` (`US_Corporate` vs `US_High_Yield`), `fred_series_id`, `oas_pct`.

## `ice_bofa_oas_line_chart.py`

Reads the tidy CSV (no FRED calls) and writes **`data/utilities/pge_oas_debt_dashboard.html`** — **Borrowing cost by credit rating** (NPV table with interactive issuance amount + OAS chart; reads `pge_borrowing_cost_npv_by_rating.csv` if present; otherwise shows a short notice to run the proforma script).

**BBB+** is the daily mean of **A** and **BBB** (computed if missing from the CSV). Styling: **BBB+** = black, thicker stroke; **AAA / AA / A** = greens; **BBB / BB / B** = reds. The **line chart** and **NPV table** both omit **CCC & lower** (rows are filtered when reading the NPV CSV for the dashboard).

```bash
python3 scripts/ice_bofa_oas_line_chart.py --years 2
```

Open the HTML in a browser (Chart.js loads from a CDN).

**Note:** BB/B/CCC are **US High Yield** index names on FRED; AAA–BBB are **US Corporate** ([BB example](https://fred.stlouisfed.org/series/BAMLH0A1HYBB)). Respect **ICE/FRED** redistribution terms.

## `pge_proforma_2026_debt_sensitivity.py`

Builds **2026 proforma** FERC line items as ``average(2024, 2025) × 1.03`` from ``pge_form1_financials.json`` and writes ``data/utilities/pge_form1_proforma_2026.csv``. Uses the proforma **Proceeds from issuance of long-term debt** (cash flows) as the debt forecast, combines it with the **latest OAS** per ``rating_bucket`` from ``ice_bofa_oas_tidy.csv`` (BBB+ = mean of A and BBB on that date if needed), and writes **NPV of 30 years** of annual coupon payments (coupon = proceeds × (risk-free + OAS) / 100, PV at **6%**) to ``pge_borrowing_cost_npv_by_rating.csv`` and a **high-to-low** markdown table ``pge_borrowing_cost_npv_by_rating.md`` (**CCC & lower** excluded from NPV outputs). Regenerate the **combined** OAS + NPV view with ``python3 scripts/ice_bofa_oas_line_chart.py`` (writes ``pge_oas_debt_dashboard.html``).

```bash
python3 scripts/pge_proforma_2026_debt_sensitivity.py
python3 scripts/pge_proforma_2026_debt_sensitivity.py --financials-json path/to/pge_form1_financials.json --oas-csv path/to/ice_bofa_oas_tidy.csv -o data/utilities
```

Not investment advice.

## FERC Form 1 (PUDL raw XBRL on Zenodo)

Catalyst’s **Public Utility Data Liberation** project publishes annual FERC Form 1 XBRL ZIPs on Zenodo ([record 19947273](https://zenodo.org/records/19947273)). See [PUDL](https://github.com/catalyst-cooperative/pudl) and [FERC1 data source notes](https://docs.catalyst.coop/pudl/en/v2025.7.0/data_sources/ferc1.html).

- **`ferc1_zenodo_zip.py`** — download / list / extract members from those ZIPs (default cache: `data/utilities/ferc1_raw_zips/`, **gitignored** so clones stay small; re-fetch ZIPs here before running `ferc1_form1_export.py` on a fresh machine).
- **`ferc1_form1_export.py`** — for a given company (default **Portland General Electric**), pulls **statement of operations**, **balance sheet** (assets + liabilities), and **cash flows** for selected years, using taxonomy presentation order. Each statement is **one table with a column per year**; displayed amounts are **millions of USD** (raw ÷ 1e6, **two decimal places**). A **2026** column is included as an empty placeholder until a filing is added. Writes `pge_form1_financials.json`, `pge_form1_financials.md`, and `index.html` under `data/utilities/ferc1_pge_viewer/` (override with `--out-dir`). JSON stores raw XBRL strings per year under each row’s `by_year`.

```bash
python3 scripts/ferc1_zenodo_zip.py list data/utilities/ferc1_raw_zips/ferc1-xbrl-2025.zip | head
python3 scripts/ferc1_form1_export.py --years 2024 2025
```

## `nri_wfir_exposure_by_riskr.py`

Summarizes **wildfire** building exposure (`WFIR_EXPB`) by **risk category** (`WFIR_RISKR`) and **expected annual loss** (`WFIR_EALT`) **by county** (tracts grouped by `STCOFIPS` from the same `.dbf`). Risk table rows are **highest risk first**; **EXPB** totals use **$** and **millions of USD**; county **EALT** is summed in **USD**. Writes `spatial/nri_wfir_expb_by_riskr.csv`, `spatial/nri_wfir_ealt_by_county.csv`, `spatial/nri_wfir_exposure_by_riskr.md`, and **`web/nri_wfir_exposure.html`** (Leaflet map over OpenStreetMap; loads **`web/NRI_Census_Tracts_PGE.geojson`** — include `WFIR_EALT` in the GeoJSON via `export_nri_pge_geojson.py`). See [NRI technical documentation](https://hazards.fema.gov/nri/technical-documentation).

```bash
python3 scripts/export_nri_pge_geojson.py
# requires GDAL ogr2ogr; writes web/NRI_Census_Tracts_PGE.geojson
python3 scripts/nri_wfir_exposure_by_riskr.py
python3 scripts/nri_wfir_exposure_by_riskr.py --dbf spatial/NRI_Census_Tracts_PGE.dbf -o spatial --html-out web/nri_wfir_exposure.html
```

## `export_nri_pge_geojson.py`

Exports `spatial/NRI_Census_Tracts_PGE.shp` to **`web/NRI_Census_Tracts_PGE.geojson`** (WGS 84, selected fields, light geometry simplify) for the NRI exposure map. Requires **GDAL** `ogr2ogr` on your machine (`brew install gdal` on macOS).

```bash
python3 scripts/export_nri_pge_geojson.py
python3 scripts/export_nri_pge_geojson.py --shp spatial/NRI_Census_Tracts_PGE.shp -o web/NRI_Census_Tracts_PGE.geojson --simplify 0.00025
```

## `wfigs_incident_locations_fetch.py`

Downloads **current** WFIGS wildland fire **incident point locations** from NIFC’s public ArcGIS layer (`WFIGS_Incident_Locations_Current`), filtered by **`POOState`** (default **Oregon only**: `US-OR`). Pass **`--states US-OR,US-WA`** to include Washington or other values. Writes **GeoJSON** plus a **`.meta.json`** sidecar (fetch time, query, attribution reminder). Optional **CSV** for a quick triage table.

Uses **stdlib only** (`urllib`); set a truthful **`--user-agent`** for your organization.

```bash
python3 scripts/wfigs_incident_locations_fetch.py --user-agent "YourOrg-wfigs/1.0 (contact@example.com)"
python3 scripts/wfigs_incident_locations_fetch.py --csv-out data/wildfire/wfigs_incident_locations_or.csv
python3 scripts/wfigs_incident_locations_fetch.py --bbox -125.0,41.9,-116.0,46.5 -o data/wildfire/wfigs_bbox.geojson
```

**Data terms:** [NIFC Open Data](https://data-nifc.opendata.arcgis.com/). **Context** (WindNinja, ELMFIRE, triage ladder): [`docs/wildfire_rapid_assessment.md`](../docs/wildfire_rapid_assessment.md).

**Demo map:** [`web/wfigs_incidents_or_wa.html`](../web/wfigs_incidents_or_wa.html) — from repo root run `python3 -m http.server 8765`, then open `http://localhost:8765/web/wfigs_incidents_or_wa.html` (needs HTTP so the browser can load `../data/wildfire/…`).

## `wfigs_nearest_transmission.py`

For each **Oregon** incident in the GeoJSON, looks up **WFIR_RISKR** from **`web/NRI_Census_Tracts_PGE.geojson`** when the point falls inside a tract (blank otherwise). Finds the closest feature in **`spatial/Transmission_Lines.shp`** (Web Mercator) using **EPSG:5070** for distance in meters. Writes **`data/wildfire/incidents_nearest_transmission.csv`**, **`.md`**, and **`.json`** (JSON feeds the table on `web/wfigs_incidents_or_wa.html`). Also runs **`ogr2ogr`** to write **`data/wildfire/transmission_lines_wgs84.geojson`** (all lines in WGS 84 for the map overlay and highlight). Requires **GDAL Python bindings** and **`ogr2ogr` on your PATH** (`brew install gdal` on macOS).

```bash
python3 scripts/wfigs_nearest_transmission.py
python3 scripts/wfigs_nearest_transmission.py --geojson data/wildfire/wfigs_incident_locations_or.geojson --lines spatial/Transmission_Lines.shp -o data/wildfire/out.csv --md-out data/wildfire/out.md --json-out data/wildfire/out.json
# CSV/MD/JSON only; skip ogr2ogr (no transmission_lines_wgs84.geojson)
python3 scripts/wfigs_nearest_transmission.py --skip-lines-geojson
```

Run after `wfigs_incident_locations_fetch.py`. See [`docs/wildfire_rapid_assessment.md`](../docs/wildfire_rapid_assessment.md) §1b and §2 (time horizon). **Spread model:** [`docs/wildfire_ignition_spread_model.md`](../docs/wildfire_ignition_spread_model.md), [`wildfire_ignitions_spread_handoff.py`](wildfire_ignitions_spread_handoff.py).

## `wildfire_ignitions_spread_handoff.py`

Reads **`data/wildfire/incidents_nearest_transmission.json`** and writes **`data/wildfire/ignitions_spread_model_handoff.md`**: per-incident WGS84 + copy-paste **`fuel_wx_ign.py`** stubs (ELMFIRE Tutorial 03). Stdlib only. **`--top N`** limits to the N closest fires (by miles).

```bash
python3 scripts/wildfire_ignitions_spread_handoff.py
python3 scripts/wildfire_ignitions_spread_handoff.py --top 5 -o data/wildfire/handoff_top5.md
```

## GitHub Pages

Static dashboards under `data/utilities/` (plus `web/index.html`) can be published with **GitHub Actions**. See the repo root [GITHUB_PAGES.md](../GITHUB_PAGES.md) for Settings steps and the public URL pattern.
