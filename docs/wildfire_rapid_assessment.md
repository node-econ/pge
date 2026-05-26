# Wildfire rapid assessment (utility / land manager)

This note ties together **near-real-time incident points** (implemented in-repo), **WindNinja** (fast terrain-aware wind), and **ELMFIRE** (2D spread when you need more than a point on a map). The goal is **triage**: decide quickly whether a new ignition deserves immediate attention—not a replacement for interagency incident command products.

## 1. Incident feed (implemented)

Script: [`scripts/wfigs_incident_locations_fetch.py`](../scripts/wfigs_incident_locations_fetch.py)

- Pulls **WFIGS_Incident_Locations_Current** from NIFC’s public ArcGIS service (same program lineage as IRWIN / EGP viewers).
- Default filter: **`POOState` = `US-OR`** (Oregon). Pass `--states US-OR,US-WA` (or other `POOState` values) to widen.
- Writes **GeoJSON** plus a small **metadata JSON** (fetch time, query, attribution reminder).
- Optional **`--bbox min_lon,min_lat,max_lon,max_lat`** narrows to a service territory after fetch.
- Optional **CSV** for a simple operations board (`IrwinID`, name, county, discovery time, containment, acres, lat/lon, …).

**Attribution and terms:** use NIFC Open Data [data-nifc.opendata.arcgis.com](https://data-nifc.opendata.arcgis.com/) license language on any map or dashboard. Do not imply official evacuation or suppression guidance unless your organization is the authoritative issuer.

**Operational caveat:** `POOState` is the **place of origin** jurisdiction, not a guarantee the flame front sits inside that polygon. Combine with distance-to-asset checks and official perimeters when available (**WFIGS_Interagency_Perimeters_Current** on the same host family).

### 1b. Nearest transmission line (implemented)

Script: [`scripts/wfigs_nearest_transmission.py`](../scripts/wfigs_nearest_transmission.py)

- Reads the Oregon incident **GeoJSON** (`wfigs_incident_locations_or.geojson` by default), joins **WFIR_RISKR** from `web/NRI_Census_Tracts_PGE.geojson` when the point falls inside a tract, and joins `spatial/Transmission_Lines.shp` (EPSG:3857 per `.prj`).
- For each incident point, finds the **closest line geometry** (whole shapefile feature) and writes:
  - `data/wildfire/incidents_nearest_transmission.csv`
  - `data/wildfire/incidents_nearest_transmission.md` (sorted by distance for quick review)
  - `data/wildfire/incidents_nearest_transmission.json` (same rows as Oregon points in the GeoJSON, for the embedded table in `web/wfigs_incidents_or_wa.html`)
  - `data/wildfire/transmission_lines_wgs84.geojson` (all lines in WGS 84 via **`ogr2ogr`** — map overlay; click a fire or table row to **highlight** the nearest feature by `OBJECTID`)
- Distance is computed in **EPSG:5070** (NAD83 / Conus Albers, meters) after reprojecting points from WGS 84 and lines from Web Mercator — suitable for **screening** distances in the Pacific Northwest, not a certified clearance measurement.

Requires **GDAL Python bindings** (`osgeo.ogr`, `osgeo.osr`) and **`ogr2ogr` on PATH** (unless `--skip-lines-geojson`). Run after refreshing incidents:

```bash
python3 scripts/wfigs_incident_locations_fetch.py --user-agent "YourOrg/1.0 (you@example.com)"
python3 scripts/wfigs_nearest_transmission.py
```

Some segments may have an empty **`FENAME`** in the source shapefile; **`OBJECTID`** / **`GlobalID`** still identify the matched feature.

## 2. Time horizon: hours to day-ahead (spread-model development)

For **ELMFIRE** and **WindNinja**, the tools you are leaning on are generally aligned with **sub-daily to next-day** forcing, not seasonal climate outlooks:

| Tool | Typical horizon | How it shows up in practice |
|------|-----------------|-----------------------------|
| **WindNinja — forecast mode** | Next **hours to ~1–2 days** | Initialization from a **mesoscale weather model** (NWS-style grids); run time stays short, but you must manage **model cycle**, **valid time**, and **domain/DEM** setup. |
| **WindNinja — uniform / station** | **“Now”** or a user-held scenario | Good for **what-if** channeling over the next operational period when you do not yet have a full forecast grid wired in. |
| **ELMFIRE — Tutorial 02** | **Multi-hour** simulations | **Transient** wind / moisture via `wx.csv` → rasters; tutorial example is on the order of **hours** of simulated time with stepped wind changes. |
| **ELMFIRE — Tutorial 03+** | Same order, larger prep | Real fuels + DEM; still driven by **your** choice of weather series length and `SIMULATION_TSTOP` — day-ahead is feasible if inputs and domain size are modest. |

**Nearest-line table (§1b)** is an **instantaneous** geometric join: it does **not** forecast where a fire will be tomorrow. Use it as a **priority screen** (“which incidents sit closest to our assets **right now**?”), then layer **WindNinja**/**ELMFIRE** when you need time-evolving exposure.

## 3. WindNinja — fast “what is the wind doing here?”

[WindNinja](https://research.fs.usda.gov/firelab/products/dataandtools/windninja) is a **diagnostic** wind model tuned for wildland fire: typical domains on the order of tens of kilometers, **run times of seconds** on a laptop, outputs **gridded speed and direction** suitable for spatial fire behavior tools.

**Modes relevant to triage:**

| Mode | When to use |
|------|----------------|
| **Uniform** | You only have a single speed/direction (e.g. RAWS or a quick NWS estimate) and need **terrain channeling** in minutes. |
| **Station / observations** | Several nearby surface observations; WindNinja blends them across the DEM. |
| **Forecast (wx model)** | You have time to pull a mesoscale layer and want a **time-stamped** field (heavier setup than uniform). |

**Integration paths:**

- **Desktop / CLI** — official builds for Windows; Linux often **build from source** ([firelab/windninja](https://github.com/firelab/windninja)).
- **C API** — embed in custom services ([wiki](https://github.com/firelab/windninja/wiki/C-API)); Doxygen examples exist for weather-model initialization.
- **Python** — third-party bindings such as [windninjapy](https://pypi.org/project/windninjapy/) (evaluate maturity for production; still wraps the same core).

**For “is this worth a phone call?”** a **small domain + uniform or two-station wind** is often enough to see whether **ridges/channels** align flames toward critical infrastructure, before you invest in a full ELMFIRE stack.

## 4. ELMFIRE — when points need a 2D answer

[ELMFIRE](https://elmfire.io/) is an open-source **Eulerian level-set** wildfire spread model. It is appropriate when triage escalates to **“how could this grow over the next N hours on real fuels?”**

**Why it is not the first 30-second step:** real landscapes need **fuel + topography rasters**, weather forcing, and a sane domain extent. The ELMFIRE tutorials show the progression:

1. **Tutorial 01** — flat terrain, uniform wind, **point ignition** (seconds—learning only).
2. **Tutorial 02** — **transient** uniform wind (`wx.csv` → rasters).
3. **Tutorial 03** — **real-world LANDFIRE + DEM** via the **Cloudfire** helper `fuel_wx_ign.py` (pulls a geospatial tile bundle for a **center lat/lon**); still a deliberate modeling exercise, not a one-click ping.

**Linking to this repo’s GeoJSON:** Tutorial-style workflows use **projected coordinates** in the model domain (`X_IGN`, `Y_IGN` in the `&SIMULATOR` namelist). For automation you would: choose domain center from the incident point → fetch/build rasters → transform WGS84 ignition to the simulation CRS → set `NUM_IGNITIONS` / `X_IGN` / `Y_IGN` / `T_IGN` per the [Tutorial 02 / 03](https://elmfire.io/tutorials/tutorial_02.html) documentation.

**Implementation guide in this repo:** [`docs/wildfire_ignition_spread_model.md`](wildfire_ignition_spread_model.md) and [`scripts/wildfire_ignitions_spread_handoff.py`](../scripts/wildfire_ignitions_spread_handoff.py) (generates `data/wildfire/ignitions_spread_model_handoff.md` with per-incident **Cloudfire** stubs).

**MODE = 2 (landscape fire potential):** ELMFIRE can also run a **FlamMap-like** “head fire in every pixel” potential surface for wind scenarios ([Tutorial 04](https://elmfire.io/tutorials/tutorial_04.html)). That is useful for **planning** and **screening large areas**, less for a single breaking ignition unless precomputed.

## 5. Suggested triage ladder (electric utility style)

1. **Ingest** — scheduled run of `wfigs_incident_locations_fetch.py` (cron, GitHub Actions, or internal scheduler); alert on **new `IrwinID` / `GlobalID`** or large change in **acres / containment**.
2. **Geofence** — run `wfigs_nearest_transmission.py` (or your own asset layers) for **distance to transmission** and thresholds; not only `POOState`.
3. **Wind sanity** — WindNinja **uniform** (or observation mode) on a **small DEM** clipped to the area between fire and assets.
4. **Spread only if warranted** — ELMFIRE (or delegated analyst) on a **prepared domain** or HPC queue; document assumptions (fuel version, wx source). Start from [`docs/wildfire_ignition_spread_model.md`](wildfire_ignition_spread_model.md) and the handoff Markdown from [`wildfire_ignitions_spread_handoff.py`](../scripts/wildfire_ignitions_spread_handoff.py).

## 6. Liability and governance

Automated outputs should be labeled **decision support**, with model version, time of weather, and data snapshot IDs. Align internal use with **NERC / state wildfire coordination** expectations and your legal team for public-facing maps.
