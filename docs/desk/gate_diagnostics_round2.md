# Screening diagnosis and temporary-copy proof

Review begun 2026-10-01; proof checkpoint recorded 2026-10-02. No outcomes were read or computed.

## Cause

G2 required user-supplied sector even though mechanical research supplied none. Research now excludes only sector from G2 requirements; the bundle still records it as Unknown. User assessments remain unchanged. Missing ATR plans and genuine G6 failures still fail. ISIN metadata checksum verified: built 2026-10-01T21:24:21.911996+05:30, age 0 trading sessions at the last market date. No additional refresh was needed.

## Gate counts

Every non-PASS result counts as a failure, including UNKNOWN. Every-gate counts overlap.

| Sample | n | Pass | Fail | First G1/G2/G3/G4/G5/G6 | Every G1/G2/G3/G4/G5/G6 |
|---|---:|---:|---:|---|---|
| Stored recent rows (incomplete prior scan) | 527 | 0 | 527 | 2/525/0/0/0/0 | 2/527/5/25/111/8 |
| Historical sample, original screening | 200 | 0 | 200 | 1/199/0/0/0/0 | 1/200/0/7/36/1 |
| Full ten-session proof, original G2 on identical inputs | 538 | 0 | 538 | 2/536/0/0/0/0 | 2/538/5/25/116/6 |
| Full ten-session proof, repaired screening | 538 | 403 | 135 | 2/0/5/25/100/3 | 2/0/5/25/116/6 |

## Proof and sampling

Ten sessions: 2026-09-18, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01.
Execution rows: 503; remaining latest-session observations are pending. Scan rows were reset only in a freshly made temporary copy, retaining its other tables including circuit-band coverage. The durable store was untouched.

The 200 historical events were sampled with seed 20261001, stratified over available 2019-2025 catalogue years; undersized years contributed all available events and the remainder was sampled without replacement. All event identities and exact reasons are retained in the companion JSON. The catalogue has no usable 2019 events after its required history window.

The complete proof applies the original G2 sector requirement to exactly the same inputs and unchanged G1/G3-G6 results, so before/after reflects only the sector repair. The 527 older stored rows are separate evidence, not a complete ten-day sample.

## Reproduction

```text
python scripts/desk_gate_diagnostics.py --output scratch/gates_before.json  # original screening commit 07b916d
python scripts/desk_scan_proof.py
```

## All failing reasons in the repaired ten-session proof

- 1: G1: ADL has no bhavcopy row on ['2026-09-21'], dates the wider market traded.
- 1: G1: ARTNIRMAN has no bhavcopy row on ['2026-09-25'], dates the wider market traded.
- 5: G3: Structural break in the trailing 60-session window: True. Corporate action(s) in that window: ['RIGHTS'].
- 1: G4: AHCL is under ASM (stage I) as of 2026-09-21; rulebook tolerates no ASM stage.
- 1: G4: AHCL is under ASM (stage I) as of 2026-09-22; rulebook tolerates no ASM stage.
- 1: G4: ALKALI is under ASM (stage I) as of 2026-09-18; rulebook tolerates no ASM stage.
- 1: G4: ARVEE is under ASM (stage I) as of 2026-09-21; rulebook tolerates no ASM stage.
- 1: G4: ARVEE is under ASM (stage I) as of 2026-09-22; rulebook tolerates no ASM stage.
- 1: G4: ASHOKAMET is under ASM (stage I) as of 2026-09-23; rulebook tolerates no ASM stage.
- 1: G4: DELTACORP is under ASM (stage I) as of 2026-09-28; rulebook tolerates no ASM stage.
- 1: G4: DELTACORP is under ASM (stage I) as of 2026-09-29; rulebook tolerates no ASM stage.
- 1: G4: DELTACORP is under ASM (stage I) as of 2026-10-01; rulebook tolerates no ASM stage.
- 1: G4: DPABHUSHAN is under ASM (stage I) as of 2026-09-29; rulebook tolerates no ASM stage.
- 1: G4: ELECTHERM is under ASM (stage I) as of 2026-09-28; rulebook tolerates no ASM stage.
- 1: G4: INDORAMA is under ASM (stage I) as of 2026-09-21; rulebook tolerates no ASM stage.
- 1: G4: MANUGRAPH is under ASM (stage I) as of 2026-09-23; rulebook tolerates no ASM stage.
- 1: G4: NIBL is under ASM (stage I) as of 2026-09-22; rulebook tolerates no ASM stage.
- 1: G4: PAISALO is under ASM (stage I) as of 2026-09-28; rulebook tolerates no ASM stage.
- 1: G4: RAYMOND is under ASM (stage I) as of 2026-09-21; rulebook tolerates no ASM stage.
- 1: G4: SANSERA is under ASM (stage I) as of 2026-09-22; rulebook tolerates no ASM stage.
- 1: G4: SBC is under ASM (stage I) as of 2026-09-25; rulebook tolerates no ASM stage.
- 1: G4: TCC is under ASM (stage I) as of 2026-09-22; rulebook tolerates no ASM stage.
- 1: G4: TNTELE is under ASM (stage I) as of 2026-09-30; rulebook tolerates no ASM stage.
- 1: G4: TNTELE is under GSM (stage I) as of 2026-09-21; excluded by the rulebook.
- 1: G4: TNTELE is under GSM (stage I) as of 2026-09-25; excluded by the rulebook.
- 1: G4: TNTELE is under GSM (stage I) as of 2026-09-28; excluded by the rulebook.
- 1: G4: TNTELE is under GSM (stage I) as of 2026-09-29; excluded by the rulebook.
- 1: G4: TNTELE is under GSM (stage I) as of 2026-09-30; excluded by the rulebook.
- 1: G4: WALCHANNAG is under ASM (stage I) as of 2026-09-23; rulebook tolerates no ASM stage.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 10.1 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 10.2 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 11.9 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 14.8 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 16.8 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 17.6 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 3.0 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 3.1 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 3.2 sessions, exceeding the 3.0-session cap.
- 3: G5: Exiting under stressed volume at 10.0% participation would take 3.3 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 3.4 sessions, exceeding the 3.0-session cap.
- 3: G5: Exiting under stressed volume at 10.0% participation would take 3.8 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 3.9 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 32.9 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 4.0 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 4.2 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 4.5 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 4.6 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 4.8 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 4.9 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 5.1 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 6.7 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 7.1 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 7.2 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 7.4 sessions, exceeding the 3.0-session cap.
- 2: G5: Exiting under stressed volume at 10.0% participation would take 8.1 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 8.9 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 9.2 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 9.5 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 9.6 sessions, exceeding the 3.0-session cap.
- 3: G5: No thesis supplied.
- 2: G5: Order is 1.04% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 1.05% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 1.08% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.19% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.20% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.21% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.37% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.38% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.42% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 1.54% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.61% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.65% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.70% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.74% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.77% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.87% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.89% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.91% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.93% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 10.61% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 11.24% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 11.39% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 11.49% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 12.01% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 12.36% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 12.75% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 16.84% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 17.70% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 17.92% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 18.40% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 18.59% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.02% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.03% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 2.14% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.16% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.29% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.33% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.35% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 2.47% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.48% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.50% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.68% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.82% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.86% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.94% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 20.22% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 20.32% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 22.22% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 22.92% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 23.77% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 24.01% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 25.27% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 25.54% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 29.84% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 3.00% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.09% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.18% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.42% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.51% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.65% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.71% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.72% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.79% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.96% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 36.98% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.12% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.53% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.65% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.92% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.93% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 42.09% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 44.02% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 5.32% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 5.53% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 5.65% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 5.67% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 5.78% of average daily turnover, exceeding the 1.0% cap.
- 2: G5: Order is 5.94% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.03% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.13% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.18% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.37% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.39% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.63% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 6.80% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.08% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.10% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.26% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.54% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.74% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.82% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.02% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.10% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.22% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.29% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.30% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.41% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 82.26% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.46% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.48% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.59% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.83% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.90% of average daily turnover, exceeding the 1.0% cap.
- 1: G6: Adding this trade's stress loss (Rs 27,922) to open risk already used (Rs 0) would exceed the open-risk budget (Rs 25,000).
- 1: G6: Adding this trade's stress loss (Rs 34,172) to open risk already used (Rs 0) would exceed the open-risk budget (Rs 25,000).
- 1: G6: Adding this trade's stress loss (Rs 34,205) to open risk already used (Rs 0) would exceed the open-risk budget (Rs 25,000).
- 3: G6: No thesis supplied.
