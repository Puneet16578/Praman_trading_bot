# T1 development pipeline: rehearsal with random labels (18 October 2026)

The whole development pipeline ran on the real store with the outcome replaced by seeded random
labels (user decision 2026-10-18). **No adverse20 value was computed and no real outcome was read:**
the real reader and the firewall's entry points raised for the whole run (`outcomes_sealed`, tested
in tests/test_t1_rehearsal.py). The only forward look was the allowed one: whether each decision's
20-session window has every bar (positive open, high, low and close) and no unadjustable action. The
labels (seed 20261018, rate 10%) were drawn for every eligible stock-day without looking at any price
and kept only where the window is complete; a test shows they are identical when every low is cut to
1%. Nothing below depends on them. **The real development run waits for the user's approval.**

Run: `python -B scripts/t1_rehearsal.py` at code bfee6cc; report data/t1/rehearsal_20261018T050910Z.json
(not committed). Settings from the user's draft addendum 3, which is **not yet recorded** (P8-085): weekend
sessions left out of the calendar for inputs and outcome windows (b); coverage counts eligible stock-days
with a known state (e); a draw is usable only if every compared group meets the sample-size minimums (f);
linear percentiles (g); bootstrap dates = the development sessions after (b), 2019-10-01 to 2024-12-02,
the 20 purged sessions left out (h). The five late sessions and 2022-08-08 stay missing inputs, as built.
The build's knowledge rules are as they are (bars known on their own session; P8-085 asks the user).

## Runtime, memory, errors

| Stage | Seconds |
| --- | --- |
| Load (store, index inputs, ISIN snapshots; panel to 2024-12-31) | 13.4 |
| Features (V1, V2, V3, ATR, causes, periods, quintiles) | 16.9 |
| Rehearsal (windows, labels, tables, 3 × 2,000 bootstrap replicates, checks) | 1.6 |
| **Total** | **31.9** |

Peak memory (Windows peak working set): 2,091,945,984 bytes (about 1.95 GiB) on a 15.7 GB machine. No
error or warning. The decision step ran for all three variants.

## The panel and the population

- Calendar: 1,560 sessions from 2018-09-03 (index-only warm-up) to 2024-12-31; 2,670 symbols. Weekend
  sessions left out: 2019-10-27, 2020-02-01, 2020-11-14, 2023-11-12, 2024-01-20, 2024-03-02, 2024-05-18
  (four of them were stored; none had an eligible stock-day). 2022-08-08 stays a session with every
  stock missing.
- Development decision sessions: 1,277 (2019-10-01 to 2024-12-02).
- Eligible development stock-days: 1,621,903 (1,621,986 with weekend sessions kept).
- Excluded because no earlier snapshot lists the symbol: 184,428 development stock-days (draft (c)).
- Outcome windows with all 20 bars and no unadjustable action: 1,542,743 of the 1,621,903 (95.1%).
- Development quintile weights: 0.2000 each (to four decimals).

## Coverage and outcome availability (draft (e))

| Variant | Coverage (state known) | Adverse state: stock-days / complete windows | Other state | State UNKNOWN |
| --- | --- | --- | --- | --- |
| V1 | 100.0% | 407,835 / 373,570 | 1,214,068 / 1,169,173 | 0 / 0 |
| V2 | 85.7% | 202,111 / 198,220 | 1,187,244 / 1,119,298 | 232,548 / 225,225 |
| V3 | 98.4% | 962,317 / 926,736 | 633,825 / 591,351 | 25,761 / 24,656 |

All three meet the 80% rule.

## Sample sizes per state and quintile (candidates / complete windows / distinct dates)

| Cell | V1 | V2 | V3 |
| --- | --- | --- | --- |
| adverse q1 | 60,844 / 54,939 / 268 | 34,387 / 34,224 / 139 | 220,923 / 215,118 / 1,077 |
| adverse q2 | 70,171 / 63,604 / 261 | 34,468 / 34,219 / 135 | 207,148 / 200,927 / 1,079 |
| adverse q3 | 74,983 / 68,718 / 268 | 36,390 / 35,881 / 139 | 189,916 / 183,713 / 1,081 |
| adverse q4 | 83,979 / 77,498 / 268 | 39,405 / 38,639 / 139 | 174,082 / 167,010 / 1,092 |
| adverse q5 | 117,858 / 108,811 / 268 | 57,461 / 55,257 / 139 | 170,248 / 159,968 / 1,096 |
| other q1 | 263,537 / 259,876 / 847 | 251,029 / 241,852 / 810 | 99,265 / 95,560 / 1,095 |
| other q2 | 254,209 / 249,080 / 847 | 244,324 / 233,339 / 807 | 112,960 / 107,579 / 1,089 |
| other q3 | 249,398 / 241,237 / 847 | 240,515 / 227,620 / 810 | 130,137 / 122,016 / 1,096 |
| other q4 | 240,399 / 228,109 / 847 | 236,071 / 220,041 / 810 | 145,340 / 133,811 / 1,096 |
| other q5 | 206,525 / 190,871 / 847 | 215,305 / 196,446 / 810 | 146,123 / 132,385 / 1,096 |

Every cell clears 100 complete windows and 30 dates. Spells (addendum 1): V1 9, V2 13 (5 required).

## Bootstrap (2,000 replicates; usable = every cell meets the minimums in the replicate)

| Variant | Block | Usable draws | Unusable |
| --- | --- | --- | --- |
| V1 | 60 | 2,000 | 0 |
| V2 | 60 | 1,999 | 1 |
| V3 | 20 | 2,000 | 0 |

Under draft (f), more than 5% unusable (over 100 of 2,000) would make the verdict INCONCLUSIVE; none
comes close. No input-only requirement failed for any variant. The rehearsal's own verdicts rest on the
random labels and are not reported.

## Not done

No adverse20 value, rate, difference or interval from real outcomes. The real development run is not
started and is not wired: it waits for the recorded addendum (which waits on P8-085) and the user's
approval.
