import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import * as esri from "esri-leaflet";
import { buildWmsGetMapUrl } from "../lib/wms3857";
import type { RemoteLayerConfig } from "../layers/layerTypes";

type Props = {
  config: RemoteLayerConfig;
  active: boolean;
};

/**
 * Mounts a single declarative remote layer on the parent map when `active`.
 * All fetching is on-demand (tiles or one GeoJSON GET per activation).
 */
export function RemoteLayerHost({ config, active }: Props) {
  const map = useMap();
  const layerRef = useRef<L.Layer | null>(null);

  useEffect(() => {
    if (!active) {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
      return;
    }

    let cancelled = false;
    const ac = new AbortController();

    function detach() {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    }

    void (async () => {
      detach();
      let layer: L.Layer | null = null;

      switch (config.type) {
        case "wms": {
          const wmsOptions = {
            tileSize: 256,
            opacity: config.opacity ?? 1,
            attribution: config.attribution,
            zIndex: config.zIndex ?? 100,
            maxNativeZoom: 22,
            getTileUrl: (coords: L.Coords) =>
              buildWmsGetMapUrl({
                baseUrl: config.baseUrl,
                layers: config.layers,
                styles: config.styles,
                format: config.format,
                transparent: config.transparent,
                version: config.version ?? "1.3.0",
                extraParams: config.extraParams,
                x: coords.x,
                y: coords.y,
                z: coords.z,
              }),
          } as L.TileLayerOptions & { getTileUrl: (coords: L.Coords) => string };
          layer = L.tileLayer("", wmsOptions);
          break;
        }
        case "xyz": {
          layer = L.tileLayer(config.urlTemplate, {
            tileSize: config.tileSize ?? 256,
            opacity: config.opacity ?? 1,
            attribution: config.attribution,
            zIndex: config.zIndex ?? 0,
            subdomains: config.subdomains,
            tms: config.tms,
            maxZoom: config.maxZoom ?? 22,
            minZoom: config.minZoom,
          });
          break;
        }
        case "esri-tiled": {
          layer = esri.tiledMapLayer({
            url: config.url,
            opacity: config.opacity ?? 1,
            zIndex: config.zIndex ?? 50,
            maxZoom: config.maxZoom,
            minZoom: config.minZoom,
          });
          break;
        }
        case "esri-dynamic": {
          layer = esri.dynamicMapLayer({
            url: config.url,
            layers: config.layers,
            opacity: config.opacity ?? 1,
            zIndex: config.zIndex ?? 50,
          });
          break;
        }
        case "esri-feature": {
          const s = config.style;
          layer = esri.featureLayer({
            url: config.url,
            opacity: config.opacity ?? 1,
            zIndex: config.zIndex ?? 60,
            // Without this, each grid cell stops at the service maxRecordCount (~2000)
            // and the rest of the features never load (often looks like a “missing” band).
            fetchAllFeatures: config.fetchAllFeatures !== false,
            requestParams: config.requestParams,
            style: () => ({
              color: s?.color ?? "#1d4ed8",
              weight: s?.weight ?? 2,
              opacity: s?.opacity ?? 0.95,
              fillOpacity: s?.fillOpacity ?? 0.15,
              fillColor: s?.fillColor ?? "#93c5fd",
            }),
          });
          break;
        }
        case "geojson-url": {
          try {
            const res = await fetch(config.url, { signal: ac.signal });
            if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
            const data = (await res.json()) as GeoJSON.GeoJSON;
            if (cancelled) return;
            layer = L.geoJSON(data, {
              style: () => ({
                color: config.style?.color ?? "#e25822",
                weight: config.style?.weight ?? 2,
                opacity: config.style?.opacity ?? 0.9,
                fillOpacity: config.style?.fillOpacity ?? 0.2,
                fillColor: config.style?.fillColor ?? "#ffb347",
              }),
            });
          } catch (e) {
            if ((e as Error).name === "AbortError") return;
            console.error(`GeoJSON layer ${config.id}:`, e);
            return;
          }
          break;
        }
      }

      if (cancelled || !layer) return;
      layer.addTo(map);
      layerRef.current = layer;
    })();

    return () => {
      cancelled = true;
      ac.abort();
      detach();
    };
  }, [map, config, active]);

  return null;
}
