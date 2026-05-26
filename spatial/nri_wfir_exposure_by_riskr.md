# NRI wildfire: tract exposure and county expected loss

Source: `NRI_Census_Tracts_PGE.dbf` (FEMA National Risk Index, wildfire fields).
Table 1: **WFIR_RISKR** sorted **highest risk first**; **tract_count** = census tracts in that category.
Table 2: **WFIR_EALT** summed by county using **STCOFIPS** from each tract (county label from **COUNTY** + **STATEABBRV** when present).

**WFIR_EXPB** total per row: **millions of USD** (numeric column in CSV; Markdown shows **$** with commas). **WFIR_EALT** totals: **USD** (see NRI technical documentation).

## 1. WFIR_EXPB (building exposure) by WFIR_RISKR

| WFIR_RISKR | Tracts | Sum (million USD) |
| --- | ---: | ---: |
| Very High | 2 | $1,892.94 |
| Relatively High | 1 | $469.79 |
| Relatively Moderate | 7 | $1,422.22 |
| Relatively Low | 58 | $11,296.28 |
| Very Low | 329 | $19,913.44 |
| No Rating | 82 | $0.00 |

## 2. WFIR_EALT (expected annual loss) by county

| County | # of Tracts | Expected annual loss (USD) |
| --- | ---: | ---: |
| Wasco, OR | 1 | 8,868,191 |
| Hood River, OR | 1 | 2,090,859 |
| Clackamas, OR | 87 | 1,084,028 |
| Multnomah, OR | 165 | 154,246 |
| Marion, OR | 64 | 74,722 |
| Washington, OR | 133 | 64,724 |
| Yamhill, OR | 14 | 58,169 |
| Polk, OR | 8 | 26,264 |
| Tillamook, OR | 4 | 20,308 |
| Columbia, OR | 2 | 909 |

Not a FEMA publication; confirm units in the NRI technical documentation.
