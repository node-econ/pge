# WFIGS incidents (Oregon) — nearest transmission line

**WFIR_RISKR** is the FEMA NRI wildfire risk rating for the census tract in `web/NRI_Census_Tracts_PGE.geojson` that contains the incident point (blank if outside that layer or if the field is missing).

Distances are **horizontal meters** in **EPSG:5070** (NAD83 / Conus Albers) from the incident point to the closest vertex/segment of the line geometry in `spatial/Transmission_Lines.shp` (Web Mercator → 5070).

**Not** a substitute for field verification or official incident products.

- **Incident GeoJSON:** `data/wildfire/wfigs_incident_locations_or.geojson`
- **NRI tracts (WFIR lookup):** `web/NRI_Census_Tracts_PGE.geojson`
- **Lines:** `spatial/Transmission_Lines.shp`
- **Generated (UTC):** `2026-05-28T03:18:30+00:00`

| Distance (Miles) | Incident | County | NRI tract WFIR_RISKR | Contain % | Acres | IrwinID | Line (FENAME) | Line OID |
|---:|---|---|---|---|---:|---:|---|---:|
| 3.053 | Lost Lane | Clackamas | Relatively Low |  | 0.1 | `{444A3025-BB51-4692-BBD8-96AA7B34F5D8}` |  | 2434.0 |
| 8.746 | Camp Cody Rx - East | Wasco |  |  | 32 | `{FE28FD4C-8981-40BC-AB0B-501666DD4846}` |  | 60.0 |
| 24.341 | Botkin | Benton |  |  | 0.59 | `{49B15722-CBC5-4812-879F-25BEAE81D174}` |  | 1369.0 |
| 32.336 | Alsea Structure | Benton |  |  |  | `{F65240E9-06D2-40CF-8CA0-D02D03E0BA81}` |  | 1369.0 |
| 51.178 | 0231 ZEN | Wasco |  | 40 | 1634 | `{FDA49146-327E-4651-835C-75B7F568A941}` |  | 60.0 |
| 58.654 | Elk | Lane |  |  | 0.25 | `{77C4B798-9FBC-49A2-9250-4A46313D884D}` |  | 1369.0 |
| 62.064 | Non-Stat HWY 58 MP 24 | Lane |  |  | 2 | `{007C11A0-4F59-49D9-8E99-43BB87BF4B6E}` |  | 1369.0 |
| 71.08 | South Jetty 1 | Lane |  |  | 0.68 | `{33864B64-AD58-47D8-9649-2A9408FB58DD}` |  | 1369.0 |
| 84.08 | UMATILLA NWR TUMBLEWEED RX | Morrow |  |  |  | `{071D817D-6DDB-485A-9B8E-387FE4E03C51}` |  | 1403.0 |
| 89.018 | PINE MOUNTAIN | Deschutes |  | 100 | 2589 | `{5985829D-31DE-4A80-A836-25907B851057}` |  | 1360.0 |
| 96.584 | 6750 Rd | Coos |  |  | 0.01 | `{75F90116-4E5F-4187-96C2-1BB89209291A}` |  | 1369.0 |
| 113.734 | Camas Way | Douglas |  |  | 0.1 | `{A6266DA4-C3F2-401F-A6AB-DD3A0E8B6043}` |  | 1369.0 |
| 141.502 | PP-A7343/Dog Creek Rd. 2001 | Josephine |  |  | 0.01 | `{DAB0AEEB-7C61-4C14-9179-85076ACEDE5B}` |  | 1369.0 |
| 155.447 | PP-01336005/Greens Creek Rd 190 | Josephine |  |  | 0.25 | `{FE1E9C1F-34DC-4E6F-A1C0-B4EBF3318C71}` |  | 1369.0 |
| 155.555 | Blackwell Rd 8087 | Jackson |  |  |  | `{D2619F53-FF96-4ABB-8E24-14A8281C922D}` |  | 1369.0 |
| 160.809 | ELK 16 RX | Grant |  |  | 10 | `{3B027DFA-0D43-4756-9F30-95CD8BB77DB9}` |  | 60.0 |
| 167.161 | Dark Hollow Rd. | Jackson |  |  | 0.01 | `{1D98C98D-2F8E-4EDF-BC11-BB9BEF4D1B11}` |  | 1369.0 |
| 168.798 | PP# 342802 UPPER APPLEGATE RD | Jackson |  |  | 0.01 | `{AB96BE21-35D9-4005-AF2E-B5E6497D3DBB}` |  | 1369.0 |

