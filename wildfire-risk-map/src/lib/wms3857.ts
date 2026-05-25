/**
 * Web Mercator tile → BBOX (minX, minY, maxX, maxY) in EPSG:3857 for WMS GetMap.
 */
export function tileToWebMercatorBbox(
  x: number,
  y: number,
  z: number
): [number, number, number, number] {
  const n = 2 ** z;
  const minX = (x / n) * 360 - 180;
  const maxX = ((x + 1) / n) * 360 - 180;
  const minY =
    (180 / Math.PI) *
    Math.atan(Math.sinh(Math.PI * (1 - (2 * (y + 1)) / n)));
  const maxY =
    (180 / Math.PI) *
    Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / n)));
  const project = (lon: number, lat: number): [number, number] => {
    const x3857 = (lon * 20037508.34) / 180;
    let y3857 =
      Math.log(Math.tan(((90 + lat) * Math.PI) / 360)) / (Math.PI / 180);
    y3857 = (y3857 * 20037508.34) / 180;
    return [x3857, y3857];
  };
  const sw = project(minX, minY);
  const ne = project(maxX, maxY);
  return [sw[0], sw[1], ne[0], ne[1]];
}

export function buildWmsGetMapUrl(params: {
  baseUrl: string;
  layers: string;
  styles?: string;
  format?: string;
  transparent?: boolean;
  version?: string;
  extraParams?: Record<string, string>;
  x: number;
  y: number;
  z: number;
}): string {
  const {
    baseUrl,
    layers,
    styles = "",
    format = "image/png",
    transparent = true,
    version = "1.3.0",
    extraParams = {},
    x,
    y,
    z,
  } = params;
  const [minX, minY, maxX, maxY] = tileToWebMercatorBbox(x, y, z);
  const u = new URL(baseUrl);
  u.searchParams.set("SERVICE", "WMS");
  u.searchParams.set("REQUEST", "GetMap");
  u.searchParams.set("VERSION", version);
  u.searchParams.set("LAYERS", layers);
  u.searchParams.set("STYLES", styles);
  if (version === "1.3.0") {
    u.searchParams.set("CRS", "EPSG:3857");
  } else {
    u.searchParams.set("SRS", "EPSG:3857");
  }
  u.searchParams.set("BBOX", `${minX},${minY},${maxX},${maxY}`);
  u.searchParams.set("WIDTH", "256");
  u.searchParams.set("HEIGHT", "256");
  u.searchParams.set("FORMAT", format);
  u.searchParams.set("TRANSPARENT", transparent ? "true" : "false");
  for (const [k, v] of Object.entries(extraParams)) {
    u.searchParams.set(k, v);
  }
  return u.toString();
}
