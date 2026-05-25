import type {
  EsriDynamicLayerConfig,
  EsriFeatureLayerConfig,
  EsriTiledLayerConfig,
  LayerCatalog,
} from "./layerTypes";

/**
 * Example catalog: replace URLs with your GeoServer / ArcGIS endpoints.
 * WMS example shape is documented; swap in your workspace:layer names.
 */
export const defaultLayerCatalog: LayerCatalog = [
  {
    group: "Basemap",
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
  {
    group: "Oregon — wildfire risk & reference (ArcGIS)",
    layers: [
      {
        id: "or-pnw-qwra-integrated-risk-2023",
        type: "esri-dynamic",
        title: "Integrated expected wildfire risk (PNW QWRA 2023, layer 0)",
        defaultVisible: true,
        url: "https://arcgis-prod.oregonexplorer.info/arcgis/rest/services/LibraryData/library_env_or_integrated_expected_wildfire_risk_2023/MapServer",
        layers: [0],
        opacity: 0.75,
        zIndex: 40,
        attribution:
          "Oregon Explorer / Oregon State University et al., PNW QWRA 2023",
      } satisfies EsriDynamicLayerConfig,
      {
        id: "or-counties-2015",
        type: "esri-feature",
        title: "Oregon county boundaries (BLM 2015)",
        defaultVisible: true,
        url: "https://services1.arcgis.com/CD5mKowwN6nIaqd8/arcgis/rest/services/library_bnd_or_counties_2015/FeatureServer/8",
        opacity: 1,
        zIndex: 80,
        attribution: "BLM Library 2015 (ArcGIS)",
        style: {
          color: "#0f172a",
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0,
        },
      } satisfies EsriFeatureLayerConfig,
      {
        id: "or-electric-transmission",
        type: "esri-feature",
        title: "Electric transmission lines",
        defaultVisible: false,
        url: "https://services8.arcgis.com/8PAo5HGmvRMlF2eU/arcgis/rest/services/Electric_Transmission_Lines/FeatureServer/0",
        opacity: 1,
        zIndex: 90,
        attribution: "ArcGIS Hosted Features (Electric_Transmission_Lines)",
        style: {
          color: "#b45309",
          weight: 2,
          opacity: 0.95,
        },
      } satisfies EsriFeatureLayerConfig,
    ],
  },
  {
    group: "Remote overlays (examples)",
    layers: [
      {
        id: "usgs-hazards",
        type: "esri-tiled",
        title: "USGS National Map (sample ArcGIS tiled layer)",
        defaultVisible: false,
        url: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer",
        opacity: 0.85,
        attribution: "USGS",
        maxZoom: 16,
      } satisfies EsriTiledLayerConfig,
      // GeoServer WMS template — point baseUrl at your service; set layers to workspace:layer
      {
        id: "example-wms",
        type: "wms",
        title: "Example WMS slot (disabled until you set a real URL)",
        defaultVisible: false,
        baseUrl: "https://example.com/geoserver/wms",
        layers: "workspace:fire_risk",
        extraParams: {},
        opacity: 0.75,
      },
    ],
  },
];
