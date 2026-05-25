# Borrowing cost NPV by rating bucket

Forecast **2026** proceeds (LT debt issuance, proforma): **504,700,000** USD.

Assumptions: risk-free **4.0%** + OAS = coupon (%); `coupon_pmt` = proceeds × (coupon_rate/100); **30** annual payments; discounted at **6.0%** (`npv_borrowing_cost`). OAS = latest date in tidy CSV per bucket. **CCC & lower** is excluded from this table.

Sorted by **npv_borrowing_cost** (high → low).

| rating_bucket | oas_date | oas % | coupon % | coupon_pmt (annual) | NPV |
| --- | --- | ---: | ---: | ---: | ---: |
| B | 2026-05-21 | 3.05 | 7.05 | 35,581,350 | 489,771,275 |
| BB | 2026-05-21 | 1.66 | 5.66 | 28,566,020 | 393,206,442 |
| BBB | 2026-05-21 | 0.94 | 4.94 | 24,932,180 | 343,187,248 |
| BBB+ | 2026-05-21 | 0.78 | 4.78 | 24,124,660 | 332,071,871 |
| A | 2026-05-21 | 0.62 | 4.62 | 23,317,140 | 320,956,495 |
| AA | 2026-05-21 | 0.47 | 4.47 | 22,560,090 | 310,535,830 |
| AAA | 2026-05-21 | 0.33 | 4.33 | 21,853,510 | 300,809,875 |
