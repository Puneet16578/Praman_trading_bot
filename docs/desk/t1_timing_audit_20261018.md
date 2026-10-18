# T1 timing audit (18 October 2026)

Item 1, before addendum 3 or implementation changes. No outcome was accessed.
The user's final timing wording retains the original current-close eligibility,
ATR percentage and moving-average definitions. Earlier proposed D+1-action and
all-inputs-D-1 readings were stopped because they contradicted explicit text.

## Timing against the approved wording

- Stock EQ bars: `panel.load_panel` maps the stored knowledge date to its first
  calendar session; `features.window_valid` requires every bar known by decision D.
  Same-date bars are usable at D. This is now to be labelled an ASSUMPTION, not
  verified publication timing. Later knowledge dates are retained unchanged.
- D's own stock bar is used by current-close eligibility and its 21-bar window;
  ATR20 and its decision-close denominator; advance/decline breadth and dispersion;
  inclusive 50/200-session averages; new highs/lows; stock returns and the
  equal-weight baskets underlying V3 and descriptive 1/5/60-session returns.
  These uses remain unchanged under the user's final wording. V2 uses the
  same-session breadth. No stock-bar calculation needs a timing change.
- NIFTY 50, NIFTY 500 and India VIX: `features.compute` shifts them to D-1,
  including V1 and index-based displays. Relative-to-NIFTY stock returns end
  at D-1 too, preserving identical endpoints. Addendum 2 remains unchanged.
- ISIN: `identity_matrix` currently starts on S (`searchsorted`, left).
  This is the only mismatch with (d). Change to the first calendar session
  strictly after S, retaining the last snapshot that lists each symbol.
  ASSUMPTION: no equity/fund-status change in any of the nine snapshot pairs;
  October 2026 download times are not historical availability evidence.
- The five late-known sessions and missing 2022-08-08 remain missing inputs;
  neither previous-close filling nor a download is introduced.

Other addendum 3 implementation work: make weekend exclusion the feature-build
default and update the report's calendar/assumption wording and explicit identity
exclusion count. The rehearsal already selects state-known coverage, sample-minimum
usable draws, linear percentiles and the complete unpurged development calendar.
Its real-reader/firewall guard will cover loading and feature computation too.
The real development outcome run remains unwired.

The research source clock is distinct from stored-row decision replay (P8-084).
The original development identity exclusion count is 184,428; the second rehearsal
must report its newly measured count after the S+1 change rather than hard-code it.
