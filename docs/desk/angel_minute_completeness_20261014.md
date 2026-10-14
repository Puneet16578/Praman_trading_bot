# Angel one-minute candles: completeness, SBIN 2026-09-01 (14 October 2026)

Design note for R1. Nothing is built. Prices are left out; where the candles and the store agree,
the agreement is stated instead of the number. Sources: the user's 08:10 connection test on
2026-10-14 (candles for 2026-09-01) and the local store's bhavcopy row (read-only).

## What Angel returned (user's run, 2026-10-14 08:10)

- 361 bars: every minute from 09:15 to 15:14 (360 bars), then a single bar at 15:29.
- No bar for the 14 minutes 15:15 to 15:28.
- The 15:29 bar is flat: open, high, low and close are the same price.

## What the store holds for that day

Row: SBIN EQ, event date 2026-09-01, knowledge date 2026-09-01, from NSE's
`sec_bhavdata_full_01Sep2026bhav.csv`.

| Question | Answer |
| --- | --- |
| Is the 15:29 bar's price the official close? | Yes: it equals the stored close price. |
| Do the day's high and low sit inside the candle range? | They are its edges: the highest candle high equals the stored high, and the lowest candle low equals the stored low. The first bar's open equals the stored open. |
| Last price | Not known from the store: the loader keeps open, high, low, close, previous close, traded and delivery quantity, but not NSE's LAST_PRICE, and the raw file is not on disk. |
| Traded quantity | 7,605,132 shares (delivery 3,384,666, 44.51%). The candles' volumes were not printed at 08:10 and nothing was saved, so their total cannot be compared with this. |
| A normal full session? | Nothing in the store says otherwise, but it cannot prove it. 1 Sep 2026 was a Tuesday; the store has 2,646 EQ rows that day (2,623 to 2,652 on the sessions from 18 Aug to 15 Sep) and SBIN's quantity is inside its range over the same sessions (4.8 to 13.8 million). The store has no minute-by-minute record of the market. |

## What this suggests (not confirmed)

- **The 14 missing minutes.** SBIN is among the most traded stocks on NSE and normally trades
  every minute. A 14-minute gap just before the close is unlike its trading, so the gap more
  likely sits in Angel's candle data than in the market. One day and one symbol; not confirmed.
- **The flat 15:29 bar.** A single flat bar at exactly the official close fits a bar that carries
  the day's closing price rather than the trades of that minute. NSE computes an equity's close as
  a weighted average price over the last 30 minutes of trading (general knowledge, not re-read
  today), so a real trade minute would rarely match it exactly. Not confirmed.

## Proposed R1 treatment (for the user's decision)

1. **Source.** R1's intraday bars come from the stream (R1 design note, 2026-10-14). Candles are
   requested only outside market hours, and only to check how complete the stream's bars were.
   They never fill a gap in the stream (the design already forbids backfilling).
2. **Missing minutes.** No bar is stored for a missing minute; it is never forward-filled or
   interpolated. For each symbol and day, R1 records the count and ranges of missing minutes from
   09:15 to 15:29 (the same summary the connection test prints). Any measure that needs a missing
   minute is UNKNOWN for that symbol and day, never computed from the neighbouring minutes.
3. **A flat last bar after a gap.** A bar at 15:29 whose open, high, low and close are all equal
   to the bhavcopy close is kept but labelled as a close marker (proposed label `close_marker`).
   It is left out of intraday measures (minute returns, ranges, volume profile). The official
   close always comes from the bhavcopy row, at its stored knowledge date, never from a candle.
4. **Completeness per symbol and day.** COMPLETE (all 375 minutes from 09:15 to 15:29, no close
   marker), GAPS (with the missing ranges), or UNKNOWN (no bars). In the brief's Data health, WARN
   when a liquid symbol (the probe's sentinels, for example) has GAPS; illiquid symbols can
   legitimately skip minutes, so they are counted but not warned on.
5. **Still to find out.** Whether the 15:15-15:28 gap repeats on other days and symbols (tonight's
   after-market run asks for 1 Sep again; `--candle-date` can ask for another stored session), and
   whether the candles' total volume matches the bhavcopy quantity. The connection test's summary
   line does not print total volume yet; adding it is a small change, offered to the user and not
   made.
