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

Reads the tidy CSV (no FRED calls) and writes:

- **`data/utilities/ice_bofa_oas_line_chart.html`** — OAS line chart only
- **`data/utilities/pge_oas_debt_dashboard.html`** — **NPV table + OAS chart** on one page (reads `pge_borrowing_cost_npv_by_rating.csv` if present; otherwise shows a short notice to run the proforma script)

**BBB+** is the daily mean of **A** and **BBB** (computed if missing from the CSV). Styling: **BBB+** = black, thicker stroke; **AAA / AA / A** = greens; **BBB / BB / B** = reds. The **line chart** and **NPV table** both omit **CCC & lower** (rows are filtered when reading the NPV CSV for the dashboard).

```bash
python3 scripts/ice_bofa_oas_line_chart.py --years 2
python3 scripts/ice_bofa_oas_line_chart.py --no-dashboard   # chart HTML only
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

Summarizes **wildfire** building exposure (`WFIR_EXPB`) and population exposure (`WFIR_EXPP`) by `WFIR_RISKR` from an NRI tract **`.dbf`**. Rows are **highest risk first**; **EXPB** totals use **$** and **millions of USD**; **EXPP** totals are **whole persons**. Writes `spatial/nri_wfir_*.csv`, `spatial/nri_wfir_exposure_by_riskr.md`, and **`web/nri_wfir_exposure.html`** (includes a Leaflet map over OpenStreetMap; loads **`web/NRI_Census_Tracts_PGE.geojson`**). See [NRI technical documentation](https://hazards.fema.gov/nri/technical-documentation).

```bash
python3 scripts/export_nri_pge_geojson.py   # requires GDAL ogr2ogr; writes web/NRI_Census_Tracts_PGE.geojson
python3 scripts/nri_wfir_exposure_by_riskr.py
python3 scripts/nri_wfir_exposure_by_riskr.py --dbf spatial/NRI_Census_Tracts_PGE.dbf -o spatial --html-out web/nri_wfir_exposure.html
```

## `export_nri_pge_geojson.py`

Exports `spatial/NRI_Census_Tracts_PGE.shp` to **`web/NRI_Census_Tracts_PGE.geojson`** (WGS 84, selected fields, light geometry simplify) for the NRI exposure map. Requires **GDAL** `ogr2ogr` on your machine (`brew install gdal` on macOS).

```bash
python3 scripts/export_nri_pge_geojson.py
python3 scripts/export_nri_pge_geojson.py --shp spatial/NRI_Census_Tracts_PGE.shp -o web/NRI_Census_Tracts_PGE.geojson --simplify 0.00025
```

## GitHub Pages

Static dashboards under `data/utilities/` (plus `web/index.html`) can be published with **GitHub Actions**. See the repo root [GITHUB_PAGES.md](../GITHUB_PAGES.md) for Settings steps and the public URL pattern.
