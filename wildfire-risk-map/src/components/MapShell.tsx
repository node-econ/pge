import { MapContainer, ZoomControl } from "react-leaflet";
import { useMemo, useState } from "react";
import { RemoteLayerHost } from "./RemoteLayerHost";
import type { LayerCatalog, RemoteLayerConfig } from "../layers/layerTypes";
import { defaultLayerCatalog } from "../layers/defaultCatalog";
import { buildRuntimeCatalog } from "../layers/catalogUtils";

const BASEMAP_GROUP = "Basemap";

function flattenCatalog(catalog: LayerCatalog): RemoteLayerConfig[] {
  return catalog.flatMap((g) => g.layers);
}

function initialBasemapId(catalog: LayerCatalog): string {
  const basemaps =
    catalog.find((g) => g.group === BASEMAP_GROUP)?.layers ?? [];
  const def = basemaps.find((l) => l.defaultVisible);
  return (def ?? basemaps[0])?.id ?? "osm";
}

function initialOverlayIds(catalog: LayerCatalog): Set<string> {
  const ids = new Set<string>();
  for (const g of catalog) {
    if (g.group === BASEMAP_GROUP) continue;
    for (const l of g.layers) {
      if (l.defaultVisible) ids.add(l.id);
    }
  }
  return ids;
}

type Props = {
  catalog?: LayerCatalog;
};

export function MapShell({ catalog: catalogProp }: Props) {
  const catalog = useMemo(
    () =>
      buildRuntimeCatalog({
        base: catalogProp ?? defaultLayerCatalog,
        mapboxToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN,
      }),
    [catalogProp]
  );

  const flat = useMemo(() => flattenCatalog(catalog), [catalog]);
  const [basemapId, setBasemapId] = useState(() => initialBasemapId(catalog));
  const [overlayIds, setOverlayIds] = useState(() =>
    initialOverlayIds(catalog)
  );

  const centerLat = Number(import.meta.env.VITE_DEFAULT_CENTER_LAT ?? 37.25);
  const centerLng = Number(import.meta.env.VITE_DEFAULT_CENTER_LNG ?? -119.5);
  const zoom = Number(import.meta.env.VITE_DEFAULT_ZOOM ?? 6);

  function toggleOverlay(id: string) {
    setOverlayIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Layer controls">
        <header className="sidebar-header">
          <h1>Wildfire risk map</h1>
          <p className="muted">
            Remote layers only — configure GeoServer WMS, ArcGIS, XYZ, or
            GeoJSON URLs in the catalog.
          </p>
        </header>

        {catalog.map((group) => (
          <section key={group.group} className="layer-group">
            <h2>{group.group}</h2>
            <ul className="layer-list">
              {group.layers.map((layer) => {
                const isBasemap = group.group === BASEMAP_GROUP;
                const checked = isBasemap
                  ? basemapId === layer.id
                  : overlayIds.has(layer.id);
                return (
                  <li key={layer.id}>
                    <label className="layer-row">
                      <input
                        type={isBasemap ? "radio" : "checkbox"}
                        name={isBasemap ? "basemap" : layer.id}
                        checked={checked}
                        onChange={() => {
                          if (isBasemap) setBasemapId(layer.id);
                          else toggleOverlay(layer.id);
                        }}
                      />
                      <span>{layer.title}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}

        <footer className="sidebar-footer muted">
          Deploy as a static container — no hosted tiles in this repo.
        </footer>
      </aside>

      <div className="map-wrap">
        <MapContainer
          center={[centerLat, centerLng]}
          zoom={zoom}
          className="map"
          zoomControl={false}
          worldCopyJump={false}
        >
          <ZoomControl position="topright" />
          {flat.map((cfg) => {
            const isBasemap =
              catalog
                .find((g) => g.group === BASEMAP_GROUP)
                ?.layers.some((l) => l.id === cfg.id) ?? false;
            const active = isBasemap
              ? basemapId === cfg.id
              : overlayIds.has(cfg.id);
            return (
              <RemoteLayerHost key={cfg.id} config={cfg} active={active} />
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
