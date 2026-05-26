# Citations and data sources

This file collects **attribution, licensing, and citation** pointers for external data used in this repository and on the published GitHub Pages site. When you add a new dataset or public map layer, append a short entry here and link to the authoritative terms page.

---

## Wildfire — WFIGS (NIFC)

**Publisher:** National Interagency Fire Center (NIFC).

**Layer used (current incident point locations):**  
`WFIGS_Incident_Locations_Current` (ArcGIS FeatureServer layer 0).

**Service (REST):**  
https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0

**Open Data hub (catalog, terms, item metadata):**  
https://data-nifc.opendata.arcgis.com/

**Suggested citation (adapt date and style guide):**  
National Interagency Fire Center (NIFC). (*n.d.*). *WFIGS Incident Locations — Current* [Feature layer]. NIFC Open Data. Retrieved \<YYYY-MM-DD\>, from the FeatureServer URL above.

**Notes:** Follow **NIFC Open Data** license and attribution language on any map or derivative. This project’s fetch script and GeoJSON sidecar record the query URL and a short attribution string; see `data/wildfire/wfigs_incident_locations_or.meta.json` and `scripts/wfigs_incident_locations_fetch.py`.

---

## Wildfire — transmission lines (local)

Nearest-transmission analysis uses a bundled shapefile at **`spatial/Transmission_Lines.shp`** (and exported `data/wildfire/transmission_lines_wgs84.geojson`). **Add your organization’s citation** for that layer here once the authoritative source and license are documented (e.g. internal GIS, vendor, or public agency dataset).

---

## Flood / wildfire risk — FEMA National Risk Index (NRI)

**Program:** FEMA National Risk Index for Natural Hazards.

**Technical documentation (field definitions, methods):**  
https://hazards.fema.gov/nri/technical-documentation

**Notes:** Tract summaries and maps in this repo use NRI attributes (e.g. `WFIR_RISKR`, `WFIR_EXPB`, `WFIR_EALT`) from the PGE-area tract clip. **Not a FEMA publication** — confirm units and definitions in the NRI documentation for any formal reporting.

---

## Basemap tiles — OpenStreetMap

**Tiles (example used in Leaflet pages):**  
`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`

**Attribution:**  
https://www.openstreetmap.org/copyright  

Follow [OpenStreetMap Foundation tile usage and attribution policies](https://operations.osmfoundation.org/policies/tiles/).

---

## Credit / borrowing cost — ICE BofA OAS (via FRED)

**API:** FRED (Federal Reserve Economic Data) — see  
https://fred.stlouisfed.org/docs/api/fred/series_observations.html

**Series / index naming:** Respect **FRED** and **ICE** redistribution and attribution terms for the underlying ICE BofA index data. The tidy export script documents segment names (US Corporate vs US High Yield); see `scripts/fred_ice_bofa_oas_tidy.py` and series pages linked from FRED.

---

## FERC Form 1 — XBRL (PUDL / Catalyst Zenodo)

**Record (raw FERC Form 1 XBRL ZIP bundles):**  
https://zenodo.org/records/19947273

**PUDL / Catalyst Cooperative context:**  
https://github.com/catalyst-cooperative/pudl

**Notes:** `scripts/ferc1_form1_export.py` and `scripts/ferc1_zenodo_zip.py` document Zenodo file URLs and outputs under `data/utilities/ferc1_pge_viewer/`. Cite Zenodo and respect Zenodo/dataset license terms when redistributing or publishing derivatives.

---

## SEC EDGAR (optional utilities)

Keyword search utilities may use **SEC EDGAR** full-text search (`efts.sec.gov`). See SEC developer guidance for **User-Agent** and acceptable use:  
https://www.sec.gov/about/developer-resources  

(Document the specific filing or search you relied on in your own paper or appendix.)

---

## Updates

| Date       | Change |
| ---------- | ------ |
| 2026-05-27 | Initial `Citations.md` (WFIGS, NRI, OSM, FRED/ICE, FERC Zenodo, SEC pointer). |
