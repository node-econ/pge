# WFIGS incidents (Oregon) — nearest transmission line

**WFIR_RISKR** is the FEMA NRI wildfire risk rating for the census tract in `web/NRI_Census_Tracts_PGE.geojson` that contains the incident point (blank if outside that layer or if the field is missing).

Distances are **horizontal meters** in **EPSG:5070** (NAD83 / Conus Albers) from the incident point to the closest vertex/segment of the line geometry in `spatial/Transmission_Lines.shp` (Web Mercator → 5070).

**Not** a substitute for field verification or official incident products.

- **Incident GeoJSON:** `data/wildfire/wfigs_incident_locations_or.geojson`
- **NRI tracts (WFIR lookup):** `web/NRI_Census_Tracts_PGE.geojson`
- **Lines:** `spatial/Transmission_Lines.shp`
- **Generated (UTC):** `2026-05-26T03:07:18+00:00`

| Distance (Miles) | Incident | County | NRI tract WFIR_RISKR | Contain % | Acres | IrwinID | Line (FENAME) | Line OID |
|---:|---|---|---|---|---:|---:|---|---:|
| 3.451 | Rowell | Polk | Relatively Low |  | 0.18 | `{1F95A5C8-AE2B-4479-B048-E551D23C31BD}` |  | 62.0 |
| 8.746 | Camp Cody Rx - East | Wasco |  |  | 32 | `{FE28FD4C-8981-40BC-AB0B-501666DD4846}` |  | 60.0 |
| 21.267 | Fred Taylor | Lincoln |  |  |  | `{6041F421-1763-44E4-87D0-09CDFC042BCC}` |  | 1398.0 |
| 24.341 | Botkin | Benton |  |  |  | `{49B15722-CBC5-4812-879F-25BEAE81D174}` |  | 1369.0 |
| 24.482 | Mill 3 | Jefferson |  |  | 6 | `{13EECC73-83E2-497E-9999-E6F095E53760}` |  | 60.0 |
| 51.178 | 0231 ZEN | Wasco |  | 0 | 1000 | `{FDA49146-327E-4651-835C-75B7F568A941}` |  | 60.0 |
| 84.08 | UMATILLA NWR TUMBLEWEED RX | Morrow |  |  |  | `{071D817D-6DDB-485A-9B8E-387FE4E03C51}` |  | 1403.0 |
| 89.018 | PINE MOUNTAIN | Deschutes |  | 100 | 2589 | `{5985829D-31DE-4A80-A836-25907B851057}` |  | 1360.0 |
| 97.635 | Boulder | Douglas |  |  | 0.5 | `{3279F565-9957-4FE6-B689-A04C7FC2BFE3}` |  | 1369.0 |
| 105.807 | Springer Creek | Douglas |  |  | 0.5 | `{A831E05F-E2A3-4A24-B1FF-47F4832A4BBA}` |  | 1369.0 |
| 141.502 | PP-A7343/Dog Creek Rd. 2001 | Josephine |  |  | 0.01 | `{DAB0AEEB-7C61-4C14-9179-85076ACEDE5B}` |  | 1369.0 |
| 154.817 | Rogue River Hwy 535 | Jackson |  |  | 0.25 | `{AA7B7AB3-22ED-45A8-A989-E245EB767FE8}` |  | 1369.0 |
| 155.447 | PP-01336005/Greens Creek Rd 190 | Josephine |  |  | 0.25 | `{FE1E9C1F-34DC-4E6F-A1C0-B4EBF3318C71}` |  | 1369.0 |
| 155.555 | Blackwell Rd 8087 | Jackson |  |  |  | `{D2619F53-FF96-4ABB-8E24-14A8281C922D}` |  | 1369.0 |
| 160.809 | ELK 16 RX | Grant |  |  | 10 | `{3B027DFA-0D43-4756-9F30-95CD8BB77DB9}` |  | 60.0 |
| 166.357 | Griffin Lane 5213 | Jackson |  |  |  | `{37180B8C-DCB5-4631-8B1F-C36C45AE949D}` |  | 1369.0 |
| 168.783 | PP# 342802 UPPER APPLEGATE RD | Jackson |  |  | 0.01 | `{AB96BE21-35D9-4005-AF2E-B5E6497D3DBB}` |  | 1369.0 |
| 173.102 | Anderson Creek Rd | Jackson |  |  | 0.25 | `{B06DB187-521B-402C-BD73-6D788B54E9B1}` |  | 1369.0 |

