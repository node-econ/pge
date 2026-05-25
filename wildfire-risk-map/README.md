# Wildfire risk map (remote layers)

Lightweight **Vite + React + Leaflet** app that renders **on-demand** map layers from remote APIs (OGC WMS / GeoServer-style endpoints, ArcGIS MapServer via [Esri Leaflet](https://github.com/Esri/esri-leaflet), XYZ raster tiles including Mapbox raster URLs, and GeoJSON over HTTP).

There is **no bundled spatial database** in this repo: tiles and features are requested by the browser from whatever URLs you configure in `src/layers/defaultCatalog.ts` (or pass a custom catalog into `MapShell`).

## Local development

```bash
cd wildfire-risk-map
npm install
npm run dev
```

Copy `.env.example` to `.env` and set `VITE_MAPBOX_ACCESS_TOKEN` if you want the optional Mapbox **raster** basemap entry (the app also works fine with OpenStreetMap only).

## Layer framework

- **Types**: `src/layers/layerTypes.ts` — discriminated union (`wms`, `xyz`, `esri-tiled`, `esri-dynamic`, `esri-feature`, `geojson-url`).
- **Catalog**: `src/layers/defaultCatalog.ts` — edit groups, titles, URLs, and defaults.
- **Runtime helpers**: `src/layers/catalogUtils.ts` — ensures a basemap group exists and optionally injects Mapbox from env.
- **Mounting**: `src/components/RemoteLayerHost.tsx` — maps each config to a Leaflet layer and attaches it when enabled.

### WMS / GeoServer notes

WMS `GetMap` URLs are built for **EPSG:3857** tiles in the browser. Your GeoServer layer must be published in Web Mercator (or GeoServer must be able to reproject). If the remote host does not send **CORS** headers, the browser will block tile requests: fix CORS on GeoServer, put the app and GeoServer on the same site, or add a small reverse proxy in front of GeoServer.

### ESRI

Point `esri-tiled` or `esri-dynamic` at a public `.../MapServer` REST URL. Use `esri-feature` for `.../FeatureServer/{id}` vector layers. Many Esri endpoints already allow browser CORS.

**Feature layers and “missing” geometry:** ArcGIS Feature services cap each query at `maxRecordCount` (often 2000). Esri Leaflet only keeps requesting the rest of that tile when **`fetchAllFeatures`** is enabled. This app sets `fetchAllFeatures: true` by default for `esri-feature` (override with `fetchAllFeatures: false` in the catalog if you need fewer requests and can accept truncation).

**Map panning:** `worldCopyJump` is off so vector queries stay aligned with a single world copy (the previous default could interact oddly with some overlays).

## Production build

```bash
npm run build
npm run preview
```

## Docker → DigitalOcean App Platform

From this directory:

```bash
docker build -t wildfire-risk-map:local .
docker run --rm -p 8080:8080 wildfire-risk-map:local
```

Then open `http://localhost:8080`.

On **DigitalOcean App Platform**, create an app from this repo (or container registry), set:

- **HTTP port**: `8080` (matches `nginx.conf` / `Dockerfile`).
- **Build-time args** (if you use Mapbox at build time): `VITE_MAPBOX_ACCESS_TOKEN`, etc. Vite inlines `VITE_*` at **build** time, not runtime — set these as build arguments in DO, or rebuild when the token changes.

Alternatively, ship without Mapbox and rely on OSM + your own WMS/ArcGIS endpoints (no secret required).

### Optional App Platform spec fragment

```yaml
services:
  - name: web
    dockerfile_path: wildfire-risk-map/Dockerfile
    source_dir: wildfire-risk-map
    http_port: 8080
    instance_count: 1
    instance_size_slug: apps-s-1vcpu-0.5gb
```

Adjust `source_dir` / `dockerfile_path` to match how this folder sits in your repository.

## License

MIT (app scaffold). Respect the licenses/attribution of each remote map service you use.
