# G6 correction: old and new results

The rulebook defines planned loss including buy and sell costs. The follow-up used that definition correctly. Original sizing divided its budget by gross stop distance and G6 omitted the per-trade check. Corrected sizing uses the same cost function as the gate and follow-up, with whole-share search. G6 independently rejects a cost-inclusive excess. No cap, rulebook or paper entry convention changed.

Preregistration addenda were committed at `cb89f96`, before the correction (`7801550`) and the complete reruns. Original results remain in `*_pre_g6.md/.json` and the preserved raw artifact. Quantities and potentially screening states change; outcomes and frozen volatility boundaries are independently checked unchanged.

## Primary 2019-2025: decision-cap audit

State transitions: `{'SCREEN_FAIL -> SCREEN_FAIL': 14924, 'SCREEN_PASS -> SCREEN_PASS': 45707, 'SCREEN_FAIL -> SCREEN_PASS': 63}`. Quantity changes: 21782. Corrected passes checked: 45770. Unchanged full labels/adverse20: 60694 / 60694. Quantity decreases / increases: 21782 / 0.

Net SCREEN_PASS change: +63 (63 FAIL->PASS, 0 PASS->FAIL). Each flip is attributed by the gates whose result changed and the caps over limit at the record's own frozen quantity (per-event detail in the JSON companion):

| Flip cause | Events |
|---|---:|
| SCREEN_FAIL -> SCREEN_PASS; gates G5; caps over at old quantity order_adv+per_trade; at new quantity none | 63 |

| Cap | Old all passes | Old filled passes | New all passes | New filled passes |
|---|---:|---:|---:|---:|
| per_trade | 12695 | 12693 | 0 | 0 |
| open_risk | 0 | 0 | 0 | 0 |
| per_stock | 0 | 0 | 0 | 0 |
| per_sector | 0 | 0 | 0 | 0 |
| order_adv | 0 | 0 | 0 | 0 |
| exit_days | 0 | 0 | 0 | 0 |

### Original replay: All candidates

| State / statistic | Old [95% CI] | New [95% CI] | Old / new valid N |
|---|---|---|---:|
| SCREEN_PASS candidates / NO_FILL | 45707 / 7 | 45770 / 7 | - |
| SCREEN_PASS signed_return_90d, % | -2.1353 [-2.5721, -1.7177]; draws=2000 | -2.1412 [-2.5812, -1.7251]; draws=2000 | 45110 / 45173 |
| SCREEN_PASS collapse, % | 58.8761 [57.7961, 59.9023]; draws=2000 | 58.8936 [57.8187, 59.9148]; draws=2000 | 45110 / 45173 |
| SCREEN_PASS adverse20, % | 9.9998 [8.6882, 11.6749]; draws=2000 | 10.0145 [8.7057, 11.6815]; draws=2000 | 45501 / 45564 |
| SCREEN_PASS stop_gap, % | 3.9076 [3.4756, 4.4280]; draws=2000 | 3.9110 [3.4808, 4.4272]; draws=2000 | 45501 / 45564 |
| SCREEN_PASS entry_gap, % | 0.2699 [0.0909, 0.5650]; draws=2000 | 0.2695 [0.0908, 0.5643]; draws=2000 | 45578 / 45641 |
| SCREEN_PASS mae_decision, % | 9.6999 [9.2679, 10.2403]; draws=2000 | 9.7064 [9.2727, 10.2446]; draws=2000 | 45501 / 45564 |
| SCREEN_PASS mae_fill, % | 10.2308 [9.8442, 10.6819]; draws=2000 | 10.2382 [9.8534, 10.6902]; draws=2000 | 45497 / 45560 |
| SCREEN_PASS locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |
| SCREEN_FAIL candidates / NO_FILL | 14987 / 189 | 14924 / 189 | - |
| SCREEN_FAIL signed_return_90d, % | -3.1802 [-3.7272, -2.5817]; draws=2000 | -3.1666 [-3.7245, -2.5676]; draws=2000 | 14788 / 14725 |
| SCREEN_FAIL collapse, % | 62.5304 [61.3814, 63.6060]; draws=2000 | 62.4924 [61.3396, 63.5737]; draws=2000 | 14788 / 14725 |
| SCREEN_FAIL adverse20, % | 16.0131 [14.4310, 17.8904]; draws=2000 | 15.9932 [14.4187, 17.8713]; draws=2000 | 14688 / 14625 |
| SCREEN_FAIL stop_gap, % | 5.6917 [5.2449, 6.2002]; draws=2000 | 5.6889 [5.2379, 6.1988]; draws=2000 | 14688 / 14625 |
| SCREEN_FAIL entry_gap, % | 0.1282 [0.0403, 0.2750]; draws=2000 | 0.1287 [0.0405, 0.2762]; draws=2000 | 14821 / 14758 |
| SCREEN_FAIL mae_decision, % | 11.8141 [11.3453, 12.4015]; draws=2000 | 11.8031 [11.3365, 12.3844]; draws=2000 | 14688 / 14625 |
| SCREEN_FAIL mae_fill, % | 13.6177 [13.1836, 14.1211]; draws=2000 | 13.6092 [13.1732, 14.1055]; draws=2000 | 14636 / 14573 |
| SCREEN_FAIL locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |

### First follow-up volatility: All candidates

| Statistic | Old, pp [95% CI] | New, pp [95% CI] |
|---|---|---|
| Unstratified gap | 6.0133 [5.1103, 6.8875]; draws=2000 | 5.9787 [5.0802, 6.8353]; draws=2000 |
| Standardized gap | 0.7419 [-0.2846, 1.7245]; draws=2000 | 0.7383 [-0.2839, 1.7104]; draws=2000 |
| Attenuation | 5.2714 [4.5501, 6.0895]; draws=2000 | 5.2404 [4.5232, 6.0541]; draws=2000 |
| Q1 FAIL minus PASS | 1.4766 [0.1149, 2.9062]; draws=2000 | 1.4766 [0.1149, 2.9062]; draws=2000 |
| Q2 FAIL minus PASS | 0.7739 [-0.5255, 2.1770]; draws=2000 | 0.7739 [-0.5255, 2.1770]; draws=2000 |
| Q3 FAIL minus PASS | 1.6891 [0.1999, 3.0198]; draws=2000 | 1.6891 [0.1999, 3.0198]; draws=2000 |
| Q4 FAIL minus PASS | 1.2770 [-0.4817, 2.9403]; draws=2000 | 1.2107 [-0.5802, 2.8971]; draws=2000 |
| Q5 FAIL minus PASS | -1.5073 [-4.6465, 1.4601]; draws=2000 | -1.4589 [-4.5245, 1.5146]; draws=2000 |

### Original replay: Filled only

| State / statistic | Old [95% CI] | New [95% CI] | Old / new valid N |
|---|---|---|---:|
| SCREEN_PASS candidates / NO_FILL | 45700 / 0 | 45763 / 0 | - |
| SCREEN_PASS signed_return_90d, % | -2.1337 [-2.5706, -1.7164]; draws=2000 | -2.1396 [-2.5797, -1.7228]; draws=2000 | 45105 / 45168 |
| SCREEN_PASS collapse, % | 58.8715 [57.7896, 59.8978]; draws=2000 | 58.8890 [57.8142, 59.9094]; draws=2000 | 45105 / 45168 |
| SCREEN_PASS adverse20, % | 9.9985 [8.6868, 11.6735]; draws=2000 | 10.0132 [8.7042, 11.6820]; draws=2000 | 45497 / 45560 |
| SCREEN_PASS stop_gap, % | 3.9079 [3.4757, 4.4284]; draws=2000 | 3.9113 [3.4810, 4.4279]; draws=2000 | 45497 / 45560 |
| SCREEN_PASS entry_gap, % | 0.2699 [0.0909, 0.5650]; draws=2000 | 0.2695 [0.0908, 0.5644]; draws=2000 | 45574 / 45637 |
| SCREEN_PASS mae_decision, % | 9.6996 [9.2680, 10.2395]; draws=2000 | 9.7061 [9.2729, 10.2448]; draws=2000 | 45497 / 45560 |
| SCREEN_PASS mae_fill, % | 10.2308 [9.8442, 10.6819]; draws=2000 | 10.2382 [9.8534, 10.6902]; draws=2000 | 45497 / 45560 |
| SCREEN_PASS locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |
| SCREEN_FAIL candidates / NO_FILL | 14798 / 0 | 14735 / 0 | - |
| SCREEN_FAIL signed_return_90d, % | -3.1562 [-3.7209, -2.5566]; draws=2000 | -3.1424 [-3.7088, -2.5489]; draws=2000 | 14605 / 14542 |
| SCREEN_FAIL collapse, % | 62.5539 [61.3907, 63.6371]; draws=2000 | 62.5155 [61.3544, 63.6104]; draws=2000 | 14605 / 14542 |
| SCREEN_FAIL adverse20, % | 16.0563 [14.4633, 17.9295]; draws=2000 | 16.0365 [14.4569, 17.9181]; draws=2000 | 14636 / 14573 |
| SCREEN_FAIL stop_gap, % | 5.7051 [5.2600, 6.2090]; draws=2000 | 5.7023 [5.2539, 6.2018]; draws=2000 | 14636 / 14573 |
| SCREEN_FAIL entry_gap, % | 0.1219 [0.0405, 0.2532]; draws=2000 | 0.1224 [0.0407, 0.2544]; draws=2000 | 14769 / 14706 |
| SCREEN_FAIL mae_decision, % | 11.8366 [11.3687, 12.4228]; draws=2000 | 11.8257 [11.3577, 12.4107]; draws=2000 | 14636 / 14573 |
| SCREEN_FAIL mae_fill, % | 13.6177 [13.1836, 14.1211]; draws=2000 | 13.6092 [13.1732, 14.1055]; draws=2000 | 14636 / 14573 |
| SCREEN_FAIL locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |

### First follow-up volatility: Filled only

| Statistic | Old, pp [95% CI] | New, pp [95% CI] |
|---|---|---|
| Unstratified gap | 6.0578 [5.1531, 6.9353]; draws=2000 | 6.0233 [5.1280, 6.8886]; draws=2000 |
| Standardized gap | 0.7577 [-0.2672, 1.7424]; draws=2000 | 0.7542 [-0.2635, 1.7283]; draws=2000 |
| Attenuation | 5.3001 [4.5692, 6.1379]; draws=2000 | 5.2692 [4.5448, 6.1018]; draws=2000 |
| Q1 FAIL minus PASS | 1.5842 [0.1574, 3.0733]; draws=2000 | 1.5842 [0.1574, 3.0733]; draws=2000 |
| Q2 FAIL minus PASS | 0.7413 [-0.5714, 2.1115]; draws=2000 | 0.7413 [-0.5714, 2.1115]; draws=2000 |
| Q3 FAIL minus PASS | 1.6911 [0.2033, 3.0279]; draws=2000 | 1.6911 [0.2033, 3.0279]; draws=2000 |
| Q4 FAIL minus PASS | 1.2770 [-0.4817, 2.9403]; draws=2000 | 1.2107 [-0.5802, 2.8971]; draws=2000 |
| Q5 FAIL minus PASS | -1.5025 [-4.6533, 1.4815]; draws=2000 | -1.4540 [-4.5242, 1.5178]; draws=2000 |

### First follow-up cap breaches at fills

| Cap / sizing | Old rate % [CI] | New rate % [CI] | Old median / p90 excess % [CI] | New median / p90 excess % [CI] |
|---|---|---|---|---|
| Any / baseline | 54.9344 [53.4084, 56.3274]; draws=2000 | 52.2890 [50.7701, 53.7131]; draws=2000 | - | - |
| per_trade / baseline | 32.9978 [31.6747, 34.3514]; draws=2000 | 30.3826 [29.1097, 31.6754]; draws=2000 | 11.6317 [11.1621, 12.1240]; draws=2000 / 40.7112 [39.3066, 42.2396]; draws=2000 | 11.5011 [11.0132, 11.9752]; draws=2000 / 40.6666 [39.3715, 42.3315]; draws=2000 |
| open_risk / baseline | 0.0066 [0.0000, 0.0150]; draws=2000 | 0.0044 [0.0000, 0.0111]; draws=2000 | 0.2202 [0.1609, 5.4350]; draws=1901 SMALL SAMPLE / 4.3921 [0.1609, 5.4350]; draws=1901 SMALL SAMPLE | 2.8276 [0.2202, 5.4350]; draws=1747 SMALL SAMPLE / 4.9136 [0.2202, 5.4350]; draws=1747 SMALL SAMPLE |
| per_stock / baseline | 35.2232 [34.0158, 36.4241]; draws=2000 | 33.7937 [32.6225, 34.9313]; draws=2000 | 0.8480 [0.8188, 0.8700]; draws=2000 / 3.2000 [3.0575, 3.3256]; draws=2000 | 0.8320 [0.8028, 0.8590]; draws=2000 / 3.1458 [3.0220, 3.2837]; draws=2000 |
| per_sector / baseline | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| order_adv / baseline | 0.2801 [0.2358, 0.3313]; draws=2000 | 0.2644 [0.2192, 0.3158]; draws=2000 | 1.2993 [1.0614, 1.6250]; draws=2000 / 5.5692 [4.7136, 7.3200]; draws=2000 | 1.5852 [1.0790, 2.0753]; draws=2000 / 5.4994 [5.0029, 7.9391]; draws=2000 |
| exit_days / baseline | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| Any / variant | 15.4397 [14.5615, 16.4109]; draws=2000 | 15.4818 [14.6001, 16.4519]; draws=2000 | - | - |
| per_trade / variant | 15.4397 [14.5615, 16.4109]; draws=2000 | 15.4818 [14.6001, 16.4519]; draws=2000 | 10.1540 [9.7104, 10.6759]; draws=2000 / 41.3068 [39.2551, 43.8437]; draws=2000 | 10.1757 [9.7317, 10.6876]; draws=2000 / 41.5112 [39.3049, 43.9077]; draws=2000 |
| open_risk / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| per_stock / variant | 0.1335 [0.1012, 0.1698]; draws=2000 | 0.1333 [0.1010, 0.1696]; draws=2000 | 2.2000 [1.3760, 3.0820]; draws=2000 / 7.0840 [5.0185, 7.8083]; draws=2000 | 2.2000 [1.3760, 3.0820]; draws=2000 / 7.0840 [5.0185, 7.8083]; draws=2000 |
| per_sector / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| order_adv / variant | 0.0044 [0.0000, 0.0110]; draws=2000 | 0.0109 [0.0022, 0.0218]; draws=2000 | 1.3782 [1.3054, 1.4510]; draws=1734 SMALL SAMPLE / 1.4364 [1.3054, 1.4510]; draws=1734 SMALL SAMPLE | 1.4510 [0.7260, 3.2781]; draws=1989 SMALL SAMPLE / 2.6546 [1.3054, 3.2781]; draws=1989 SMALL SAMPLE |
| exit_days / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |

## Descriptive 2026: decision-cap audit

State transitions: `{'SCREEN_PASS -> SCREEN_PASS': 7133, 'SCREEN_FAIL -> SCREEN_FAIL': 2526, 'SCREEN_FAIL -> SCREEN_PASS': 9}`. Quantity changes: 3491. Corrected passes checked: 7142. Unchanged full labels/adverse20: 9668 / 9668. Quantity decreases / increases: 3491 / 0.

Net SCREEN_PASS change: +9 (9 FAIL->PASS, 0 PASS->FAIL). Each flip is attributed by the gates whose result changed and the caps over limit at the record's own frozen quantity (per-event detail in the JSON companion):

| Flip cause | Events |
|---|---:|
| SCREEN_FAIL -> SCREEN_PASS; gates G5; caps over at old quantity order_adv+per_trade; at new quantity none | 8 |
| SCREEN_FAIL -> SCREEN_PASS; gates G6; caps over at old quantity open_risk+per_trade; at new quantity none | 1 |

| Cap | Old all passes | Old filled passes | New all passes | New filled passes |
|---|---:|---:|---:|---:|
| per_trade | 1958 | 1958 | 0 | 0 |
| open_risk | 0 | 0 | 0 | 0 |
| per_stock | 0 | 0 | 0 | 0 |
| per_sector | 0 | 0 | 0 | 0 |
| order_adv | 0 | 0 | 0 | 0 |
| exit_days | 0 | 0 | 0 | 0 |

### Original replay: All candidates

| State / statistic | Old [95% CI] | New [95% CI] | Old / new valid N |
|---|---|---|---:|
| SCREEN_PASS candidates / NO_FILL | 7133 / 2 | 7142 / 2 | - |
| SCREEN_PASS signed_return_90d, % | 0.9993 [-0.0660, 2.0042]; draws=2000 | 0.9948 [-0.0769, 2.0091]; draws=2000 | 4413 / 4418 |
| SCREEN_PASS collapse, % | 52.2547 [49.9095, 54.6089]; draws=2000 | 52.2408 [49.8973, 54.6060]; draws=2000 | 4413 / 4418 |
| SCREEN_PASS adverse20, % | 7.7351 [6.3049, 9.2229]; draws=2000 | 7.7396 [6.2974, 9.2312]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS stop_gap, % | 4.6880 [3.5386, 5.8641]; draws=2000 | 4.6818 [3.5327, 5.8593]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS entry_gap, % | 0.1966 [0.0452, 0.4323]; draws=2000 | 0.1964 [0.0451, 0.4316]; draws=2000 | 7120 / 7129 |
| SCREEN_PASS mae_decision, % | 9.3090 [8.5971, 10.0254]; draws=2000 | 9.3125 [8.5997, 10.0282]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS mae_fill, % | 9.5534 [8.8195, 10.3005]; draws=2000 | 9.5580 [8.8216, 10.3100]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |
| SCREEN_FAIL candidates / NO_FILL | 2535 / 34 | 2526 / 34 | - |
| SCREEN_FAIL signed_return_90d, % | -4.2917 [-6.0937, -2.5695]; draws=2000 | -4.2959 [-6.1102, -2.5532]; draws=2000 | 1553 / 1548 |
| SCREEN_FAIL collapse, % | 61.8802 [57.4669, 66.3380]; draws=2000 | 61.9509 [57.5673, 66.3642]; draws=2000 | 1553 / 1548 |
| SCREEN_FAIL adverse20, % | 12.8837 [10.2877, 15.8095]; draws=2000 | 12.8906 [10.2994, 15.8145]; draws=2000 | 2313 / 2304 |
| SCREEN_FAIL stop_gap, % | 5.3178 [4.1782, 6.6075]; draws=2000 | 5.3385 [4.1896, 6.6423]; draws=2000 | 2313 / 2304 |
| SCREEN_FAIL entry_gap, % | 0.1603 [0.0376, 0.3307]; draws=2000 | 0.1609 [0.0378, 0.3316]; draws=2000 | 2495 / 2486 |
| SCREEN_FAIL mae_decision, % | 10.8430 [9.7881, 11.9042]; draws=2000 | 10.8384 [9.7886, 11.9015]; draws=2000 | 2313 / 2304 |
| SCREEN_FAIL mae_fill, % | 12.1737 [11.1502, 13.2263]; draws=2000 | 12.1702 [11.1609, 13.2307]; draws=2000 | 2309 / 2300 |
| SCREEN_FAIL locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |

### First follow-up volatility: All candidates

| Statistic | Old, pp [95% CI] | New, pp [95% CI] |
|---|---|---|
| Unstratified gap | 5.1486 [3.1265, 7.4481]; draws=2000 | 5.1510 [3.1084, 7.4434]; draws=2000 |
| Standardized gap | 1.4638 [-0.3020, 3.2083]; draws=2000 | 1.4810 [-0.2788, 3.2185]; draws=2000 |
| Attenuation | 3.6848 [2.4095, 5.1078]; draws=2000 | 3.6700 [2.3899, 5.0850]; draws=2000 |
| Q1 FAIL minus PASS | -0.5845 [-3.1118, 2.5859]; draws=2000 | -0.5845 [-3.1118, 2.5859]; draws=2000 |
| Q2 FAIL minus PASS | -0.8688 [-3.4760, 2.1192]; draws=2000 | -0.8688 [-3.4760, 2.1192]; draws=2000 |
| Q3 FAIL minus PASS | 2.2627 [-1.0543, 5.8735]; draws=2000 | 2.2627 [-1.0543, 5.8735]; draws=2000 |
| Q4 FAIL minus PASS | 4.3280 [0.2698, 8.2708]; draws=2000 | 4.4945 [0.4196, 8.3563]; draws=2000 |
| Q5 FAIL minus PASS | 1.7842 [-2.1522, 5.3407]; draws=2000 | 1.6998 [-2.2390, 5.3083]; draws=2000 |

### Original replay: Filled only

| State / statistic | Old [95% CI] | New [95% CI] | Old / new valid N |
|---|---|---|---:|
| SCREEN_PASS candidates / NO_FILL | 7131 / 0 | 7140 / 0 | - |
| SCREEN_PASS signed_return_90d, % | 0.9993 [-0.0660, 2.0042]; draws=2000 | 0.9948 [-0.0769, 2.0091]; draws=2000 | 4413 / 4418 |
| SCREEN_PASS collapse, % | 52.2547 [49.9095, 54.6089]; draws=2000 | 52.2408 [49.8973, 54.6060]; draws=2000 | 4413 / 4418 |
| SCREEN_PASS adverse20, % | 7.7351 [6.3049, 9.2229]; draws=2000 | 7.7396 [6.2974, 9.2312]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS stop_gap, % | 4.6880 [3.5386, 5.8641]; draws=2000 | 4.6818 [3.5327, 5.8593]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS entry_gap, % | 0.1966 [0.0452, 0.4323]; draws=2000 | 0.1964 [0.0451, 0.4316]; draws=2000 | 7120 / 7129 |
| SCREEN_PASS mae_decision, % | 9.3090 [8.5971, 10.0254]; draws=2000 | 9.3125 [8.5997, 10.0282]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS mae_fill, % | 9.5534 [8.8195, 10.3005]; draws=2000 | 9.5580 [8.8216, 10.3100]; draws=2000 | 6826 / 6835 |
| SCREEN_PASS locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |
| SCREEN_FAIL candidates / NO_FILL | 2501 / 0 | 2492 / 0 | - |
| SCREEN_FAIL signed_return_90d, % | -4.3627 [-6.1608, -2.6528]; draws=2000 | -4.3671 [-6.1467, -2.6619]; draws=2000 | 1539 / 1534 |
| SCREEN_FAIL collapse, % | 62.0533 [57.6103, 66.5477]; draws=2000 | 62.1252 [57.6798, 66.5713]; draws=2000 | 1539 / 1534 |
| SCREEN_FAIL adverse20, % | 12.8627 [10.2617, 15.7972]; draws=2000 | 12.8696 [10.2264, 15.7557]; draws=2000 | 2309 / 2300 |
| SCREEN_FAIL stop_gap, % | 5.2837 [4.1482, 6.5673]; draws=2000 | 5.3043 [4.1697, 6.5862]; draws=2000 | 2309 / 2300 |
| SCREEN_FAIL entry_gap, % | 0.1606 [0.0377, 0.3313]; draws=2000 | 0.1612 [0.0379, 0.3326]; draws=2000 | 2491 / 2482 |
| SCREEN_FAIL mae_decision, % | 10.8482 [9.7965, 11.9115]; draws=2000 | 10.8437 [9.7950, 11.9059]; draws=2000 | 2309 / 2300 |
| SCREEN_FAIL mae_fill, % | 12.1737 [11.1502, 13.2263]; draws=2000 | 12.1702 [11.1609, 13.2307]; draws=2000 | 2309 / 2300 |
| SCREEN_FAIL locked_rate, % | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 / 0 |

### First follow-up volatility: Filled only

| Statistic | Old, pp [95% CI] | New, pp [95% CI] |
|---|---|---|
| Unstratified gap | 5.1276 [3.1155, 7.4499]; draws=2000 | 5.1300 [3.0878, 7.4334]; draws=2000 |
| Standardized gap | 1.4323 [-0.3293, 3.1915]; draws=2000 | 1.4496 [-0.3115, 3.2206]; draws=2000 |
| Attenuation | 3.6953 [2.4096, 5.1214]; draws=2000 | 3.6804 [2.3922, 5.1057]; draws=2000 |
| Q1 FAIL minus PASS | -0.5108 [-3.1118, 2.7603]; draws=2000 | -0.5108 [-3.1118, 2.7603]; draws=2000 |
| Q2 FAIL minus PASS | -0.8688 [-3.4760, 2.1192]; draws=2000 | -0.8688 [-3.4760, 2.1192]; draws=2000 |
| Q3 FAIL minus PASS | 2.0594 [-1.2656, 5.6892]; draws=2000 | 2.0594 [-1.2656, 5.6892]; draws=2000 |
| Q4 FAIL minus PASS | 4.3280 [0.2698, 8.2708]; draws=2000 | 4.4945 [0.4196, 8.3563]; draws=2000 |
| Q5 FAIL minus PASS | 1.7842 [-2.1522, 5.3407]; draws=2000 | 1.6998 [-2.2390, 5.3083]; draws=2000 |

### First follow-up cap breaches at fills

| Cap / sizing | Old rate % [CI] | New rate % [CI] | Old median / p90 excess % [CI] | New median / p90 excess % [CI] |
|---|---|---|---|---|
| Any / baseline | 45.3232 [41.5731, 49.3948]; draws=2000 | 41.8768 [38.0391, 46.1767]; draws=2000 | - | - |
| per_trade / baseline | 28.9020 [25.7632, 32.5136]; draws=2000 | 25.4762 [22.2953, 29.2609]; draws=2000 | 10.4716 [8.7499, 12.7462]; draws=2000 / 38.1029 [32.5978, 43.0918]; draws=2000 | 11.2510 [9.6204, 13.1254]; draws=2000 / 38.4660 [33.1634, 45.1496]; draws=2000 |
| open_risk / baseline | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| per_stock / baseline | 28.1587 [25.4431, 30.9834]; draws=2000 | 26.7647 [24.1723, 29.4185]; draws=2000 | 0.8325 [0.7496, 0.9500]; draws=2000 / 3.2449 [2.8454, 3.5760]; draws=2000 | 0.8060 [0.7406, 0.9360]; draws=2000 / 3.1520 [2.7714, 3.4768]; draws=2000 |
| per_sector / baseline | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| order_adv / baseline | 0.2384 [0.1130, 0.3853]; draws=2000 | 0.2381 [0.1052, 0.3976]; draws=2000 | 2.2545 [0.9151, 3.9249]; draws=2000 SMALL SAMPLE / 6.4775 [2.9766, 8.2154]; draws=2000 SMALL SAMPLE | 2.0030 [0.5557, 3.9768]; draws=2000 SMALL SAMPLE / 6.0212 [2.3922, 6.8205]; draws=2000 SMALL SAMPLE |
| exit_days / baseline | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| Any / variant | 12.8033 [10.2316, 15.9662]; draws=2000 | 12.8431 [10.2781, 16.0055]; draws=2000 | - | - |
| per_trade / variant | 12.8033 [10.2316, 15.9662]; draws=2000 | 12.8431 [10.2781, 16.0055]; draws=2000 | 10.2647 [8.5122, 12.2570]; draws=2000 / 38.8875 [32.2365, 42.4875]; draws=2000 | 10.2647 [8.5272, 12.2736]; draws=2000 / 38.7060 [32.2448, 42.4152]; draws=2000 |
| open_risk / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| per_stock / variant | 0.0982 [0.0257, 0.2098]; draws=2000 | 0.0980 [0.0256, 0.2095]; draws=2000 | 2.4320 [1.6236, 6.5000]; draws=1986 SMALL SAMPLE / 6.0864 [2.4320, 6.5000]; draws=1986 SMALL SAMPLE | 2.4320 [1.6236, 6.5000]; draws=1986 SMALL SAMPLE / 6.0864 [2.4320, 6.5000]; draws=1986 SMALL SAMPLE |
| per_sector / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| order_adv / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |
| exit_days / variant | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE / unavailable [unavailable]; draws=0 SMALL SAMPLE |

## Verification scope

The real-assessment regression checks an ELIGIBLE decision with a binding per-trade budget, and real SCREEN_PASS decisions, against all six caps. The full replay asserts the same invariant for every corrected pass. This does not remove the separately documented approximation of existing portfolio risk or the missing historical band data. All prior research limitations remain. Full original gate-group statistics and all first-follow-up per-statistic denominators remain in each old/new JSON report.

Reproduce: `python scripts/desk_g6_comparison.py`.
