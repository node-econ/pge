# Ignition and spread model (WindNinja + ELMFIRE)

Companion to **[`wildfire_rapid_assessment.md`](wildfire_rapid_assessment.md)** (triage ladder and time horizon). This doc is the **next step** after the repo’s **Oregon incident map** and **nearest-transmission** join: turn a **WFIGS ignition** into a **time-evolving spread** view on real fuels and terrain, on **hours to day-ahead** horizons where the tools allow it.

Companion artifact: run [`scripts/wildfire_ignitions_spread_handoff.py`](../scripts/wildfire_ignitions_spread_handoff.py) to emit **`data/wildfire/ignitions_spread_model_handoff.md`** with per-fire **Cloudfire** command stubs.

## 1. What you already have in-repo

| Output | Role |
|--------|------|
| `data/wildfire/wfigs_incident_locations_or.geojson` | Oregon-wide ignition **WGS84** points + attributes (fetch output) |
| `data/wildfire/incidents_nearest_transmission.json` | Same points + **WFIR_RISKR** (when inside NRI PGE tracts), **nearest line OBJECTID**, and screening distances |
| `data/wildfire/transmission_lines_wgs84.geojson` | Lines for map context |

Incident points and nearest-line joins are **screening**, not a forecast.

## 2. WindNinja — gridded wind for the next few hours

**Goal:** produce **spatially varying** wind (speed + direction rasters) over a **DEM** for the same domain you will use in ELMFIRE or for a lighter-weight corridor check.

1. Clip or acquire a **DEM** covering the fire + lines of interest (domain often **≤ ~50 km** per WindNinja guidance).
2. Choose initialization: **uniform** (fastest), **station** (RAWS / Mesonet), or **forecast** (mesoscale model — aligns with **hourly to ~day-ahead** valid times).
3. Export **ASCII grids** or formats your downstream tool accepts (ELMFIRE’s wind inputs are raster-based in the tutorials; match the version you install).

**References:** [WindNinja product page](https://research.fs.usda.gov/firelab/products/dataandtools/windninja), [C API / wx example](https://github.com/firelab/windninja/wiki/C-API), optional [windninjapy](https://pypi.org/project/windninjapy/).

## 3. ELMFIRE — transient spread from a point ignition

**Goal:** [ELMFIRE](https://elmfire.io/) **MODE = 1** transient run: point ignition, fuels + topo, time-varying weather rasters built from your **`wx.csv`** (or equivalent), **`SIMULATION_TSTOP`** set for the horizon you care about (e.g. 6–24+ hours).

**Learning path (official tutorials):**

1. [Tutorial 01](https://elmfire.io/tutorials/tutorial_01.html) — flat + constant wind (sanity check).
2. [Tutorial 02](https://elmfire.io/tutorials/tutorial_02.html) — **transient** wind; **`X_IGN` / `Y_IGN` / `T_IGN`** in **model projection** (not lon/lat).
3. [Tutorial 03](https://elmfire.io/tutorials/tutorial_03.html) — **Cloudfire** `fuel_wx_ign.py` at **`--center_lon` / `--center_lat`** for real **LANDFIRE** + DEM around the ignition.

**Connecting this repo’s lon/lat to ELMFIRE:**

1. Use the handoff script’s **`fuel_wx_ign.py`** stub centered on the incident.
2. Unpack the tutorial run’s **project CRS** and domain extent from the created rasters / `elmfire.data` inputs.
3. Transform the ignition from **EPSG:4326** to that CRS (e.g. `gdaltransform` or your GIS) and set **`NUM_IGNITIONS`**, **`X_IGN(1)`**, **`Y_IGN(1)`**, **`T_IGN(1)`** in the **`&SIMULATOR`** namelist.
4. Build **wind / moisture rasters** for each time step you need (Tutorial 02 pattern) or extend with your **WindNinja** outputs if you map them into ELMFIRE’s expected bands.

## 4. Where to run ELMFIRE (GitHub Pages is display-only)

**GitHub Pages** can only host **static** assets (HTML, JS, GeoJSON, pre-rendered images). It cannot execute the ELMFIRE binary, write large GeoTIFFs, or run long CPU jobs.

**Practical options for forecasts:**

| Approach | Role |
|----------|------|
| **Workstation or Linux VM** | Easiest path to learn ELMFIRE: install per [elmfire.io](https://elmfire.io/), keep runs on local or NFS disk. |
| **Cloud VM** (AWS EC2, GCP Compute Engine, Azure VM, etc.) | Same as a server: pick **enough RAM and fast disk** for your domain; snapshot AMIs once the stack builds. Good when you need a shared “forecast box” without owning hardware. |
| **Corporate / university HPC** | Batch jobs, larger domains, queues; common for repeated ensemble work. |
| **GitHub Actions** | **Not** a substitute for operational forecasting (short timeouts, small runners, no persistent scratch). At most a **smoke test** on toy domains if you ever wire one. |

**Still using Pages:** run ELMFIRE **elsewhere**, then publish **lightweight derivatives** only if policy allows—e.g. simplified GeoJSON perimeters, downsampled PNGs, or small vector tiles—committed or uploaded to the site. The **source of truth** for the forecast remains the compute environment, not the static site.

## 5. Suggested order of operations (one escalation)

1. **Triage** — map + nearest line (already in-repo).
2. **Wind sanity** — WindNinja on a small DEM (uniform or observation first).
3. **Spread** — ELMFIRE Tutorial 03-style domain centered on the same lat/lon; Tutorial 02-style **`wx.csv`** horizon; document fuel version, wx source, and `SIMULATION_TSTOP`.

## 6. Governance

Label outputs **decision support**, record model and fuel versions, and keep a clear separation from **interagency** situational products. See also [`wildfire_rapid_assessment.md`](wildfire_rapid_assessment.md) §6.

## 7. Google Research — FireBench (optional ML / research track)

If you want to explore **Google Research–style wildfire ML** in parallel to ELMFIRE operations, the best-known open artifact is **FireBench**: a very large **high-fidelity simulation dataset** (ensemble of 3D fire–atmosphere scenarios) intended for **ML and process studies**, hosted on **Google Cloud**, not a small utility drop-in for daily incident runs.

- Overview: [FireBench — Wildfires](https://sites.research.google/gr/wildfires/firebench/) (Google Research)
- Blog: [FireBench: HPC and ML for wildfire research](https://research.google/blog/firebench-using-high-performance-computing-to-advance-machine-learning-and-wildfire-research/)
- Code / examples: [google-research/firebench](https://github.com/google-research/firebench) (repository is **archived**; treat as **research reference** and check whether dataset access terms still fit your use case.)

**Relationship to ELMFIRE:** FireBench is about **curated simulation data + ML**; ELMFIRE on your VM is about **your fuels, your weather, your ignitions** for a specific operational question. They complement each other at the **R&D** layer; they do not replace each other for “tonight’s line threat” unless you build and validate a custom model trained on your domain.
