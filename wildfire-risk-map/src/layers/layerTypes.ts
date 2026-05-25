/**
 * Declarative remote layer definitions. Nothing is bundled server-side:
 * the browser requests tiles/features from the URLs you configure.
 */

/** Shared fields for all remote layers */
export type LayerBase = {
  id: string;
  title: string;
  /** Start unchecked in the layer list */
  defaultVisible?: boolean;
  /** Lower = drawn below */
  zIndex?: number;
  opacity?: number;
  attribution?: string;
};

/** OGC WMS (GeoServer, MapServer, QGIS Server, ArcGIS ImageServer WMS, …) */
export type WmsLayerConfig = LayerBase & {
  type: "wms";
  /** WMS entrypoint, e.g. https://example.com/geoserver/wms */
  baseUrl: string;
  layers: string;
  styles?: string;
  format?: string;
  transparent?: boolean;
  version?: "1.3.0" | "1.1.1";
  /** Appended as query params (CQL_FILTER, env, dim_*, …) */
  extraParams?: Record<string, string>;
};

/** Slippy map raster tiles (XYZ/TMS). Mapbox raster tiles work here. */
export type XyzLayerConfig = LayerBase & {
  type: "xyz";
  urlTemplate: string;
  /** 256 or 512 depending on provider */
  tileSize?: number;
  /** tms:true flips Y for TMS servers */
  tms?: boolean;
  /** Subdomains a,b,c for {s} in template */
  subdomains?: string | string[];
  maxZoom?: number;
  minZoom?: number;
};

/** ArcGIS MapServer tiled layer */
export type EsriTiledLayerConfig = LayerBase & {
  type: "esri-tiled";
  url: string;
  maxZoom?: number;
  minZoom?: number;
};

/** ArcGIS MapServer dynamic (single image per view) — heavier but flexible */
export type EsriDynamicLayerConfig = LayerBase & {
  type: "esri-dynamic";
  url: string;
  layers?: number[];
  maxZoom?: number;
  minZoom?: number;
};

/** ArcGIS FeatureServer layer (vector features, queried on demand by Esri Leaflet) */
export type EsriFeatureLayerConfig = LayerBase & {
  type: "esri-feature";
  /** Full layer URL ending in /FeatureServer/{id} */
  url: string;
  /**
   * When true (default), Esri Leaflet follows `exceededTransferLimit` with
   * `resultOffset` so each map tile can load more than `maxRecordCount` features.
   * Set false only for very heavy layers where you accept truncated results.
   */
  fetchAllFeatures?: boolean;
  /** Merged into the ArcGIS query string (e.g. custom filters the host supports) */
  requestParams?: Record<string, string | boolean | number>;
  /** Default symbol for GeoJSON features returned by the service */
  style?: {
    color?: string;
    weight?: number;
    opacity?: number;
    fillOpacity?: number;
    fillColor?: string;
  };
};

/** GeoJSON loaded from a URL (must allow CORS from your app origin) */
export type GeoJsonUrlLayerConfig = LayerBase & {
  type: "geojson-url";
  url: string;
  /** Leaflet path styling for line/polygon features */
  style?: {
    color?: string;
    weight?: number;
    opacity?: number;
    fillOpacity?: number;
    fillColor?: string;
  };
};

export type RemoteLayerConfig =
  | WmsLayerConfig
  | XyzLayerConfig
  | EsriTiledLayerConfig
  | EsriDynamicLayerConfig
  | EsriFeatureLayerConfig
  | GeoJsonUrlLayerConfig;

export type LayerCatalog = {
  /** Human-readable group name in the layer panel */
  group: string;
  layers: RemoteLayerConfig[];
}[];
