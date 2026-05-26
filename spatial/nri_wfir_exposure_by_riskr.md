# NRI wildfire: exposure by wildfire risk rating

Source: `NRI_Census_Tracts_PGE.dbf` (FEMA National Risk Index, wildfire fields).
Rows are **WFIR_RISKR** sorted **highest risk first**; **tract_count** = census tracts in that category.

**WFIR_EXPB** total per row: **millions of USD** (numeric column in CSV; Markdown shows **$** with commas). **WFIR_EXPP** total: **persons** (whole numbers).

## 1. WFIR_EXPB (building exposure) by WFIR_RISKR

| WFIR_RISKR | Tracts | Sum (million USD) |
| --- | ---: | ---: |
| Very High | 2 | $1,892.94 |
| Relatively High | 1 | $469.79 |
| Relatively Moderate | 7 | $1,422.22 |
| Relatively Low | 58 | $11,296.28 |
| Very Low | 329 | $19,913.44 |
| No Rating | 82 | $0.00 |

## 2. WFIR_EXPP (population exposure) by WFIR_RISKR

| WFIR_RISKR | Tracts | Sum (persons) |
| --- | ---: | ---: |
| Very High | 2 | 5,772 |
| Relatively High | 1 | 1,207 |
| Relatively Moderate | 7 | 8,056 |
| Relatively Low | 58 | 46,573 |
| Very Low | 329 | 90,916 |
| No Rating | 82 | 0 |

Not a FEMA publication; confirm units in the NRI technical documentation.
