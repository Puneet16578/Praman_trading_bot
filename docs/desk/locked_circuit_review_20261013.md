# Locked lower-circuit paper fills: review only

13 October 2026, Part A5. Engine behavior is unchanged; P8-064 is open.

## Reproduction and cause

Both the manual monitor and Strategy 0 call desk.paper.execution.stop_rule.
It sees only opening, low and stop. Synthetic example: previous close 100,
applicable fixed band 5%, open=high=low=close=95, standing stop 98.
Calling stop_rule(95, 95, 98) returned ('stop_gap', 95). This invents a sell fill
when the specified market has no buyers. Neither caller checks an executable bid,
the applicable daily band or an all-day locked bar before accepting that fill.
Pending time/manual exits also use the next open without a liquidity check.
No live trade outcomes were queried; existing sealed Strategy 0 results stay sealed.

## Proposed correction, awaiting approval

1. Resolve the band actually effective for session D, from the preceding trading
   session's exact report, visible by D. The report dated D describes the *next*
   session (docs/desk/price_band_source.md). Never use that look-ahead band for D.
2. Prefer an exchange-published absolute lower limit and tick size. If only a fixed
   percentage exists, derive the candidate lower limit from the exchange reference
   close on D's raw share basis, accounting for ex-date reference-price resets and
   official tick rounding. Do not blindly multiply an unadjusted pre-split close.
   Store currently has percentages, not a complete authoritative daily limit/tick
   and reference-price history; resolving this is a prerequisite, not a guess.
3. With valid finite raw OHLC, flag POSSIBLY_LOCKED_LOWER when all four equal the
   applicable lower price within one verified tick. Even positive traded volume
   does not prove that our sell could execute: daily data cannot reveal the queue
   or whether buyers were available when our stop fired. Conservatively do not fill.
4. Append a deferred-exit event with session, band/report provenance, reference
   price, tick, OHLC and reason. Keep the position, quantity and risk live. Retry
   the standing exit on later observed sessions in date order; never backfill a
   previous fictitious execution. The first unlocked day's fill must use that
   day's permitted rule and price, with the delay visible operationally.
5. Missing/inapplicable bands, dynamic ranges, missing bars and ambiguous corporate
   actions are UNKNOWN, never evidence of liquidity. Define a fail-closed deferred
   fill/manual-review policy for these cases before implementing it. A low merely
   touching the band while high is above it is not proof of an all-day lock; a
   daily-bar policy can still only model execution, not establish queue priority.

Apply the same execution-availability check to stop and next-open exit paths in
both books. Preserve append-only records and sealed outcomes. Decide separately
whether this correction requires a registered strategy amendment/version; do not
silently reinterpret past burn-in records. No historical outcome audit is authorized.

## Buy side: entries on a day locked at the upper limit (added 2026-10-13, user request)

The proposal above covers sells at a lower lock. The mirror case is an entry. On a
day locked at the upper limit all day there are buyers queued at the limit and no
sellers, yet both books' day limit entry (the registered follow-up 2 `limit_fill`,
used by Strategy 0's `_settle_entry` and the manual `desk paper open`) fills at the
open whenever the open is at or below the limit. Synthetic call (decision price 100,
ATR20 4, so limit 102):

- all four prices 102 (lock equal to the limit): `FILL_OPEN` at 102;
- all four prices 101 (lock below the limit): `FILL_OPEN` at 101;
- all four prices 103 (lock above the limit): `NO_FILL`, as today.

The first two invent a buy that a queued order at the upper limit would not get.
Daily volume at the upper limit shows that some sellers met the earlier queue, not
that our order, placed before the open, reached the front of it.

Proposed detection, the mirror of steps 1-3 above and with the same prerequisites:
- Resolve the upper limit effective for the entry session from the preceding
  trading session's exact band report, the exchange reference price on that
  session's raw share basis (with ex-date resets) and a verified tick size.
- Flag POSSIBLY_LOCKED_UPPER when the raw open, high, low and close all equal that
  upper limit within one verified tick. Then do not fill: record `ENTRY_NO_FILL`
  with reason `LOCKED_UPPER`, with the band report, reference price, tick and OHLC
  as evidence. The entry is a day order, so it is cancelled as any unfilled entry
  is; nothing is deferred and no risk is opened. This is a market outcome, not a
  data failure: under the fill-failure switch it counts as an attempt (ATTEMPT_OK),
  like an untouched limit.
- A bar that opens at the upper limit but trades below it during the day is not an
  all-day lock; the existing rule applies unchanged.
- A flat bar whose lock status cannot be verified (band report missing or not
  applicable, dynamic range, unverified tick, ambiguous corporate action): no
  entry. Declining an entry never opens risk, so failing closed is safe here, unlike
  the exit side. Record it as `ENTRY_FILL_FAILED` with failure `LOCK_STATUS_UNKNOWN`:
  data the fill decision needs were missing, which the switch already counts as an
  operational failure.
- Separately: a limit above the session's upper limit could not be placed as
  entered, because the exchange rejects orders outside the band, which is published
  the evening before. Whether the paper order should be capped at the upper limit
  or treated as rejected is a rule question for the same strategy-amendment
  decision; this review proposes no answer.

The four recorded Strategy 0 fills include no exactly flat bar
(docs/desk/locked_fill_audit_20261013.md), so this did not affect any recorded
entry under the flat-bar screen. As for exits, the full tick-tolerant test cannot
be run without authoritative tick and limit history. Engine unchanged.

## Proposed tests

All-day lock at the known lower band (including positive volume); ordinary gap
above the lower band; band touch without all-day lock; missing/dynamic bands;
corporate-action reference reset; correct preceding-session report; consecutive
locked days followed by an executable session; next-open time exits; unchanged
position/risk while deferred; no duplicate events and no forward outcome display.
Buy side: all-day upper lock with the limit equal to and above the locked price
(no fill, reason LOCKED_UPPER, counted as an attempt) in both books; lock above the
limit (ordinary NO_FILL); opening at the upper limit then trading lower (existing
rule); unverifiable band on a flat bar (LOCK_STATUS_UNKNOWN, operational failure).

Evidence: synthetic call above executed locally and source traced through both
callers. No network requests, production writes, new fills or engine changes.

Subsequent user-requested operational fill screen (counts only, no outcome
access): docs/desk/locked_fill_audit_20261013.md. Zero exactly-flat bars among
four recorded Strategy 0 fills; manual book has no fills. The full tick-tolerant
classification remains unresolved without authoritative historical tick/limit
inputs. This does not amend the proposed detector or certify past liquidity.
