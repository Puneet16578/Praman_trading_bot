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

## Proposed tests

All-day lock at the known lower band (including positive volume); ordinary gap
above the lower band; band touch without all-day lock; missing/dynamic bands;
corporate-action reference reset; correct preceding-session report; consecutive
locked days followed by an executable session; next-open time exits; unchanged
position/risk while deferred; no duplicate events and no forward outcome display.

Evidence: synthetic call above executed locally and source traced through both
callers. No network requests, production writes, new fills or engine changes.

Subsequent user-requested operational fill screen (counts only, no outcome
access): docs/desk/locked_fill_audit_20261013.md. Zero exactly-flat bars among
four recorded Strategy 0 fills; manual book has no fills. The full tick-tolerant
classification remains unresolved without authoritative historical tick/limit
inputs. This does not amend the proposed detector or certify past liquidity.
