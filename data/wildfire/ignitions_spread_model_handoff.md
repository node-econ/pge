# Ignition → spread model handoff

Generated from this repo’s **nearest-transmission** join. Coordinates are **EPSG:4326** (WGS 84).

- **Incident GeoJSON:** `data/wildfire/wfigs_incident_locations_or.geojson`
- **Transmission lines shapefile:** `spatial/Transmission_Lines.shp`
- **Join generated (UTC):** `2026-05-26T03:07:18+00:00`

See **`docs/wildfire_ignition_spread_model.md`** (repo root) for the full ignition + WindNinja + ELMFIRE workflow.

---

## Per-incident stubs (ELMFIRE Cloudfire tile fetch)

After [ELMFIRE](https://elmfire.io/) and **Cloudfire** are installed per Tutorial 03, use the incident center as ``--center_lon`` / ``--center_lat`` (adjust ``--fuel_version``, ``--outdir``, ``--name``). Then set ``NUM_IGNITIONS``, ``X_IGN``, ``Y_IGN``, ``T_IGN`` in the ``&SIMULATOR`` group in **projected** model coordinates ([Tutorial 02](https://elmfire.io/tutorials/tutorial_02.html)).

### 1. Rowell

- **County:** Polk
- **IrwinID:** `{1F95A5C8-AE2B-4479-B048-E551D23C31BD}`
- **WGS84:** `-123.489198027794`, `44.9896175417313`
- **Nearest transmission OBJECTID:** 62.0 (~3.451 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.489198027794 --center_lat=44.9896175417313 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Rowell'
```

### 2. Camp Cody Rx - East

- **County:** Wasco
- **IrwinID:** `{FE28FD4C-8981-40BC-AB0B-501666DD4846}`
- **WGS84:** `-121.381731215027`, `45.2197005783236`
- **Nearest transmission OBJECTID:** 60.0 (~8.746 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-121.381731215027 --center_lat=45.2197005783236 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Camp_Cody_Rx___East'
```

### 3. Fred Taylor

- **County:** Lincoln
- **IrwinID:** `{6041F421-1763-44E4-87D0-09CDFC042BCC}`
- **WGS84:** `-123.902255004958`, `44.7166870947325`
- **Nearest transmission OBJECTID:** 1398.0 (~21.267 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.902255004958 --center_lat=44.7166870947325 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Fred_Taylor'
```

### 4. Botkin

- **County:** Benton
- **IrwinID:** `{49B15722-CBC5-4812-879F-25BEAE81D174}`
- **WGS84:** `-123.462931057099`, `44.4482886532932`
- **Nearest transmission OBJECTID:** 1369.0 (~24.341 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.462931057099 --center_lat=44.4482886532932 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Botkin'
```

### 5. Mill 3

- **County:** Jefferson
- **IrwinID:** `{13EECC73-83E2-497E-9999-E6F095E53760}`
- **WGS84:** `-121.228625101211`, `44.7708385647206`
- **Nearest transmission OBJECTID:** 60.0 (~24.482 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-121.228625101211 --center_lat=44.7708385647206 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Mill_3'
```

### 6. 0231 ZEN

- **County:** Wasco
- **IrwinID:** `{FDA49146-327E-4651-835C-75B7F568A941}`
- **WGS84:** `-120.437903987861`, `44.8556356485372`
- **Nearest transmission OBJECTID:** 60.0 (~51.178 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-120.437903987861 --center_lat=44.8556356485372 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='0231_ZEN'
```

### 7. UMATILLA NWR TUMBLEWEED RX

- **County:** Morrow
- **IrwinID:** `{071D817D-6DDB-485A-9B8E-387FE4E03C51}`
- **WGS84:** `-119.569481048669`, `45.8863518053616`
- **Nearest transmission OBJECTID:** 1403.0 (~84.08 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-119.569481048669 --center_lat=45.8863518053616 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='UMATILLA_NWR_TUMBLEWEED_RX'
```

### 8. PINE MOUNTAIN

- **County:** Deschutes
- **IrwinID:** `{5985829D-31DE-4A80-A836-25907B851057}`
- **WGS84:** `-120.917772869837`, `43.8102995301558`
- **Nearest transmission OBJECTID:** 1360.0 (~89.018 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-120.917772869837 --center_lat=43.8102995301558 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='PINE_MOUNTAIN'
```

### 9. Boulder

- **County:** Douglas
- **IrwinID:** `{3279F565-9957-4FE6-B689-A04C7FC2BFE3}`
- **WGS84:** `-122.522381032942`, `43.3062053438897`
- **Nearest transmission OBJECTID:** 1369.0 (~97.635 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-122.522381032942 --center_lat=43.3062053438897 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Boulder'
```

### 10. Springer Creek

- **County:** Douglas
- **IrwinID:** `{A831E05F-E2A3-4A24-B1FF-47F4832A4BBA}`
- **WGS84:** `-122.984464072978`, `43.1343052892103`
- **Nearest transmission OBJECTID:** 1369.0 (~105.807 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-122.984464072978 --center_lat=43.1343052892103 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Springer_Creek'
```

### 11. PP-A7343/Dog Creek Rd. 2001

- **County:** Josephine
- **IrwinID:** `{DAB0AEEB-7C61-4C14-9179-85076ACEDE5B}`
- **WGS84:** `-123.426064052904`, `42.635288546098`
- **Nearest transmission OBJECTID:** 1369.0 (~141.502 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.426064052904 --center_lat=42.635288546098 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='PP_A7343_Dog_Creek_Rd__2001'
```

### 12. Rogue River Hwy 535

- **County:** Jackson
- **IrwinID:** `{AA7B7AB3-22ED-45A8-A989-E245EB767FE8}`
- **WGS84:** `-123.106513970399`, `42.42747190203`
- **Nearest transmission OBJECTID:** 1369.0 (~154.817 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.106513970399 --center_lat=42.42747190203 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Rogue_River_Hwy_535'
```

### 13. PP-01336005/Greens Creek Rd 190

- **County:** Josephine
- **IrwinID:** `{FE1E9C1F-34DC-4E6F-A1C0-B4EBF3318C71}`
- **WGS84:** `-123.261313992667`, `42.4225552175366`
- **Nearest transmission OBJECTID:** 1369.0 (~155.447 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.261313992667 --center_lat=42.4225552175366 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='PP_01336005_Greens_Creek_Rd_190'
```

### 14. Blackwell Rd 8087

- **County:** Jackson
- **IrwinID:** `{D2619F53-FF96-4ABB-8E24-14A8281C922D}`
- **WGS84:** `-122.966630617828`, `42.4178719141904`
- **Nearest transmission OBJECTID:** 1369.0 (~155.555 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-122.966630617828 --center_lat=42.4178719141904 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Blackwell_Rd_8087'
```

### 15. ELK 16 RX

- **County:** Grant
- **IrwinID:** `{3B027DFA-0D43-4756-9F30-95CD8BB77DB9}`
- **WGS84:** `-118.450113512075`, `44.1370057887299`
- **Nearest transmission OBJECTID:** 60.0 (~160.809 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-118.450113512075 --center_lat=44.1370057887299 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='ELK_16_RX'
```

### 16. Griffin Lane 5213

- **County:** Jackson
- **IrwinID:** `{37180B8C-DCB5-4631-8B1F-C36C45AE949D}`
- **WGS84:** `-122.916063914708`, `42.26370523853`
- **Nearest transmission OBJECTID:** 1369.0 (~166.357 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-122.916063914708 --center_lat=42.26370523853 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Griffin_Lane_5213'
```

### 17. PP# 342802 UPPER APPLEGATE RD

- **County:** Jackson
- **IrwinID:** `{AB96BE21-35D9-4005-AF2E-B5E6497D3DBB}`
- **WGS84:** `-123.047647928307`, `42.2263412240941`
- **Nearest transmission OBJECTID:** 1369.0 (~168.783 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-123.047647928307 --center_lat=42.2263412240941 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='PP__342802_UPPER_APPLEGATE_RD'
```

### 18. Anderson Creek Rd

- **County:** Jackson
- **IrwinID:** `{B06DB187-521B-402C-BD73-6D788B54E9B1}`
- **WGS84:** `-122.851513889471`, `42.1690385680173`
- **Nearest transmission OBJECTID:** 1369.0 (~173.102 mi per screening join)

```bash
# From ELMFIRE Tutorial 03 — fetch LANDFIRE + topo tile (no wx/ignition in tarball when these flags are false).
fuel_wx_ign.py \
  --do_wx=False --do_ignition=False \
  --center_lon=-122.851513889471 --center_lat=42.1690385680173 \
  --fuel_source='landfire' --fuel_version='2.2.0' \
  --outdir='./fuel' --name='Anderson_Creek_Rd'
```

