import type { LayerCatalog } from "./layerTypes";
import { defaultLayerCatalog } from "./defaultCatalog";

const BASEMAP_GROUP = "Basemap";

/** Guarantee a basemap group exists so the map always has a valid background. */
export function ensureBasemapGroup(catalog: LayerCatalog): LayerCatalog {
  if (catalog.some((g) => g.group === BASEMAP_GROUP)) return catalog;
  return [
    {
      group: BASEMAP_GROUP,
      layers: [
        {
          id: "osm",
          type: "xyz",
          title: "OpenStreetMap",
          defaultVisible: true,
          urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
          attribution: "&copy; OpenStreetMap contributors",
          maxZoom: 19,
        },
      ],
    },
    ...catalog,
  ];
}

export function buildRuntimeCatalog(options: {
  base?: LayerCatalog;
  mapboxToken?: string;
}): LayerCatalog {
  const base = options.base ?? defaultLayerCatalog;
  const withBasemap = ensureBasemapGroup(base);
  const token = options.mapboxToken?.trim();
  if (!token) return withBasemap;
  const mapboxLayer = {
    id: "mapbox-streets",
    type: "xyz" as const,
    title: "Mapbox Streets (raster)",
    defaultVisible: false,
    urlTemplate: `https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/512/{z}/{x}/{y}@2x?access_token=${encodeURIComponent(token)}`,
    tileSize: 512,
    maxZoom: 22,
    attribution: "&copy; Mapbox &copy; OpenStreetMap",
  };
  return withBasemap.map((g) =>
    g.group === BASEMAP_GROUP
      ? { ...g, layers: [...g.layers, mapboxLayer] }
      : g
  );
}
