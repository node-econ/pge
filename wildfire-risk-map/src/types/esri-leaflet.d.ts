declare module "esri-leaflet" {
  import type { Layer } from "leaflet";

  /** Minimal typings — see https://github.com/Esri/esri-leaflet */
  export function tiledMapLayer(options: {
    url: string;
    opacity?: number;
    zIndex?: number;
    maxZoom?: number;
    minZoom?: number;
  }): Layer;

  export function dynamicMapLayer(options: {
    url: string;
    layers?: number[];
    opacity?: number;
    zIndex?: number;
  }): Layer;

  export function featureLayer(options: {
    url: string;
    opacity?: number;
    zIndex?: number;
    fetchAllFeatures?: boolean;
    requestParams?: Record<string, string | boolean | number>;
    /** Esri passes GeoJSON-like features from the REST API */
    style?: (
      feature: GeoJSON.Feature
    ) => import("leaflet").PathOptions | false;
  }): Layer;
}
