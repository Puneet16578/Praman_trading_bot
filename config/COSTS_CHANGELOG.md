# Cost config changelog

## v1 (2026-09-27) -- CONFIRMED (partial), committed

Six of eight rate blocks confirmed against the user's broker (Zerodha)'s official charges page
(https://zerodha.com/charges/), checked 2026-09-27: `brokerage` (Rs 0/order), `depository_charges`
(Rs 15.34/scrip/sell day, GST-inclusive), `securities_transaction_tax` (0.1% both legs),
`exchange_transaction_charges` (0.00307% per leg), `sebi_turnover_fee` (0.0001% per leg),
`stamp_duty` (0.015% buy-side only).

**Correction**: the draft version of `exchange_transaction_charges` had 0.00297%; confirmed against
Zerodha's charges page, the current published NSE rate is 0.00307% per leg. Corrected before this
config was ever active/committed, so there is no prior score or decision to restate.

`gst` (18%, statutory rather than broker-specific) stays TO_VERIFY. `slippage_by_liquidity_bucket`
is marked ASSUMPTION (a new status added to the schema alongside TO_VERIFY/CONFIRMED) -- it is a
modelling estimate with no published rate to confirm, not an unconfirmed real rate.

Added `tests/test_desk_cost_round_trip.py`: computes the round-trip cost of a Rs 50,000 delivery
trade from this file via `desk/risk/officer.py:round_trip_cost_inr` and checks it against an
independently written-out hand calculation (Rs 126.5806), including an explicit check that the
GST-inclusive DP charge is never taxed a second time.
