# NRI wildfire: exposure by wildfire risk rating

Source: `NRI_Census_Tracts_PGE.dbf` (FEMA National Risk Index, wildfire fields).
Rows are **WFIR_RISKR** sorted **highest risk first**; **tract_count** = census tracts in that category.

**WFIR_EXPB** values are in **millions of USD** (2 decimal places). **WFIR_EXPP** sums are in **millions of persons** (2 dp); means are **whole persons per tract** (not dollars).

## 1. WFIR_EXPB (building exposure) by WFIR_RISKR

| WFIR_RISKR | Tracts | Sum (M USD) | Mean per tract (M USD) |
| --- | ---: | ---: | ---: |
| Very High | 2 | 1892.94 | 946.47 |
| Relatively High | 1 | 469.79 | 469.79 |
| Relatively Moderate | 7 | 1422.22 | 203.17 |
| Relatively Low | 58 | 11296.28 | 194.76 |
| Very Low | 329 | 19913.44 | 60.53 |
| No Rating | 82 | 0.00 | 0.00 |

## 2. WFIR_EXPP (population exposure) by WFIR_RISKR

| WFIR_RISKR | Tracts | Sum (M persons) | Mean per tract (persons) |
| --- | ---: | ---: | ---: |
| Very High | 2 | 0.01 | 2,886 |
| Relatively High | 1 | 0.00 | 1,207 |
| Relatively Moderate | 7 | 0.01 | 1,151 |
| Relatively Low | 58 | 0.05 | 803 |
| Very Low | 329 | 0.09 | 276 |
| No Rating | 82 | 0.00 | 0 |

Not a FEMA publication; confirm units in the NRI technical documentation.
