# Screening diagnosis and temporary-copy proof

Final verification: 2026-10-03. These gate audits use inputs only. Label spot checks are documented separately.

## Cause and repair

G2 required user sector on every mechanical candidate. Sector is now inapplicable only to research G2 and remains Unknown in its evidence bundle. User assessments still require it. Missing ATR plans remain failures.

The initially fresh ISIN map (built 2026-10-01, age zero trading sessions) had lost historical identities and allowed old snapshots to overwrite current ISINs. P8-034 repaired both issues. Recovery restored 32 identities and corrected 51 conflicts; the entire existing 70,638-event catalogue resolves as equity. See isin_recovery_round2.json for timestamps, hashes and exact changes. G1 now also applies knowledge-date cutoffs (P8-032).

## Gate counts

Every non-PASS result, including UNKNOWN, counts below. Every-gate counts overlap.

| Sample | n | Pass | Fail | First G1/G2/G3/G4/G5/G6 | Every G1/G2/G3/G4/G5/G6 |
|---|---:|---:|---:|---|---|
| Historical original screening | 200 | 0 | 200 | 1/199/0/0/0/0 | 1/200/0/7/36/1 |
| Final ten sessions, original sector requirement on identical repaired inputs | 540 | 0 | 540 | 2/538/0/0/0/0 | 2/540/5/25/118/8 |
| Final ten sessions, repaired screening | 540 | 403 | 137 | 2/2/5/25/100/3 | 2/2/5/25/118/8 |
| Same historical 200, repaired screening | 200 | 158 | 42 | 1/0/0/7/34/0 | 1/1/0/7/36/1 |

## Proof and sampling

Ten sessions: 2026-09-18, 2026-09-21, 2026-09-22, 2026-09-23, 2026-09-24, 2026-09-25, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01.

The final temporary-copy scan created 540 opportunities and 505 execution observations. The latest-session executions remain pending. Both Praman and Desk were temporary copies; only the copied opportunity tables were reset. Production records were preserved.

The 200 historical events use seed 20261001 with year strata over 2019-2025, taking undersized strata in full and filling without replacement. There are no usable 2019 catalogue events after the required history window. The same 200 identities were reused for the final audit.

The ten-session counterfactual changes only G2 sector applicability on the final frozen inputs. It is not a replay of every old code defect. Earlier stored-row and 538-event checks remain in the companion JSON for audit. The repaired identity map adds two CRESTO events: both fail G2 because price, volume and delivery evidence are unavailable under the assessment history. Historical ORTINGLOBE also retains genuine missing evidence. These are not sector failures.

G5/G6 reason text `No thesis supplied` in research means the mechanical ATR plan is invalid or unavailable; no user-authored thesis is required.

## Exact failing reasons

### Final ten sessions

- 1: G1: ADL has no bhavcopy row on ['2026-09-21'], dates the wider market traded.
- 1: G1: ARTNIRMAN has no bhavcopy row on ['2026-09-25'], dates the wider market traded.
- 2: G2: Required dimension 'delivery' is UNKNOWN, not a Fact.
- 2: G2: Required dimension 'price' is UNKNOWN, not a Fact.
- 2: G2: Required dimension 'volume' is UNKNOWN, not a Fact.
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
- 5: G5: No thesis supplied.
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
- 5: G6: No thesis supplied.

### Historical 200

- 1: G1: ORTINGLOBE has no bhavcopy row on ['2024-08-27', '2024-08-28', '2024-08-29', '2024-08-30', '2024-09-02'], dates the wider market traded.
- 1: G2: Required dimension 'delivery' is UNKNOWN, not a Fact.
- 1: G2: Required dimension 'price' is UNKNOWN, not a Fact.
- 1: G2: Required dimension 'volume' is UNKNOWN, not a Fact.
- 1: G4: ALPHAGEO is under ASM (stage I) as of 2021-05-11; rulebook tolerates no ASM stage.
- 1: G4: APOLLO is under ASM (stage I) as of 2025-01-06; rulebook tolerates no ASM stage.
- 1: G4: BHARATWIRE is under ASM (stage I) as of 2022-09-05; rulebook tolerates no ASM stage.
- 1: G4: FCL is under ASM (stage I) as of 2020-12-29; rulebook tolerates no ASM stage.
- 1: G4: PFOCUS is under ASM (stage I) as of 2023-04-18; rulebook tolerates no ASM stage.
- 1: G4: PRESSMN is under ASM (stage I) as of 2023-05-31; rulebook tolerates no ASM stage.
- 1: G4: SEPOWER is under ASM (stage I) as of 2020-04-30; rulebook tolerates no ASM stage.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 17.2 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 21.0 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 3.3 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 3.6 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 4.1 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 6.6 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 6.7 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 78.4 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 8.5 sessions, exceeding the 3.0-session cap.
- 1: G5: Exiting under stressed volume at 10.0% participation would take 9.5 sessions, exceeding the 3.0-session cap.
- 1: G5: No thesis supplied.
- 1: G5: Order is 1.00% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.09% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.21% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.23% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.24% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.25% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.35% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.51% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.53% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.54% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.67% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.71% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 1.78% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 10.20% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 16.62% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 16.76% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 196.12% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.20% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.56% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.62% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 2.68% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 21.33% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 23.63% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.04% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.18% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.43% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 3.50% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.55% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.62% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 4.75% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 42.96% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 52.38% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 7.39% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 8.25% of average daily turnover, exceeding the 1.0% cap.
- 1: G5: Order is 9.05% of average daily turnover, exceeding the 1.0% cap.
- 1: G6: No thesis supplied.
