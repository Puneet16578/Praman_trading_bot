# T1 coverage: decisions for the user (18 October 2026)

A decision note. Nothing is changed by it. Counts are from the T1 build artifact
(`data/t1/build_20261013T202004Z.sqlite`, code 1a3991d) and the Praman store, read-only, and cover the
**development period** (decision sessions 2019-10-01 to 2024-12-02; the purge rule holds back
2024-12-03 to 2024-12-31). They are input counts only: the artifact holds no outcome
(`meta.outcomes = "none loaded or computed"`), no outcome file was opened, and none informed anything
here.

Reference figures: 1,281 development sessions; 2,160,208 development stock-days, of which 1,621,986
are eligible. The pre-registration requires, for each contrast, coverage of at least 80% of eligible
stock-days in each period. Today's coverage of the variants' states on eligible development
stock-days: V1 100%, **V2 85.8%** (1,392,151), V3 98.4% (1,596,277). V2 is UNKNOWN on 310 development
sessions: 49 warm-up sessions at the start, 200 from the late sessions (point 1), 50 from 2022-08-08
(point 2), and 11 single sessions.

## 1. Five sessions whose bars are known only months later

**Cause.** Each date has one stored vintage, fetched in the full-history load of 2026-09-16, whose
knowledge date is the IST date of the archive file's Last-Modified at that moment. NSE rewrote these
five files after the session; the original publication time was never recorded.

| Session | EQ bars | Stored knowledge date | Source file | Next stored session (its knowledge date) | Next file's previous close equals this close |
| --- | --- | --- | --- | --- | --- |
| 2020-04-13 | 1,515 | 2024-12-23 | sec_bhavdata_full_13Apr2020bhav.csv | 2020-04-15 (2020-04-15) | 1,487 of 1,487 symbols |
| 2020-09-28 | 1,539 | 2024-12-23 | sec_bhavdata_full_28Sep2020bhav.csv | 2020-09-29 (2020-09-29) | 1,530 of 1,530 |
| 2022-03-07 | 1,653 | 2024-12-23 | sec_bhavdata_full_07Mar2022bhav.csv | 2022-03-08 (2022-03-08) | 1,651 of 1,651 |
| 2023-07-31 | 1,726 | 2024-01-31 | sec_bhavdata_full_31Jul2023bhav.csv | 2023-08-01 (2023-08-11, itself late) | 1,726 of 1,726 |
| 2023-08-01 | 1,727 | 2023-08-11 | sec_bhavdata_full_01Aug2023bhav.csv | 2023-08-02 (2023-08-02) | 1,723 of 1,723 |

**Was the data out the same evening?** Nothing we hold shows that. The earliest proof is the next
session's file: its previous-close column repeats every one of these closes, and that file is known
on its own date. That proves the closes were public by the next session (for 31 Jul 2023, by
11 Aug 2023), not the same evening, and proves nothing about the open, high and low. The store also
holds 253 to 731 announcements dated each of these days, which shows the exchange was operating, not
when the bhavcopy appeared.

**Options and what they keep or lose (development).**

| Option | V2 state | Eligibility (ATR needs the day's high and low) |
| --- | --- | --- |
| A. Strict, as built: each file known from its stored date | UNKNOWN for 50 sessions from each date: 200 sessions, 156,962 eligible stock-days without V2 | about 106,800 stock-days lost in the 21 sessions after each date (25,533, 27,864, 28,803, 28,630 ATR-incomplete against 1,511, 2,218, 192, 147 in the 21 sessions before), plus 8,160 bars not known on the dates themselves |
| B. Each date's close taken from the next file's previous close, known on that file's date; open, high and low stay strict | UNKNOWN only on the date itself (31 Jul to 10 Aug 2023: 9 sessions): 12 sessions; nearly all 156,962 stock-days recovered | unchanged from A (about 106,800 lost) |
| C. A labelled ASSUMPTION like T1's D+1 rule: each of these five files known from the next session | UNKNOWN only on the dates themselves: 5 sessions | nearly all of the 106,800 recovered; only the dates themselves lost |

B uses only data we hold with a proven date and adds no assumption; it changes which file supplies an
input, so it would need your decision and probably a dated addendum. C rests on an unprovable
assumption about five rewritten files (the previous-close evidence supports the closes only).

**Recommendation: B.** It recovers V2 and V3, which depend on closes, without any assumption, and keeps
the strict rule where we have no evidence (the day's high and low). The cost that stays is about
106,800 eligible stock-days in 84 sessions, which does not threaten the 80% coverage rule.

## 2. 2022-08-08

**Was it a session?** Yes, by evidence we hold: the official NIFTY 50, NIFTY 500 and India VIX
histories list it; 675 announcements are dated that day; and the next session's file (10 Aug; 9 Aug
was a holiday) has a previous close different from the 5 Aug close for 1,774 of 1,811 symbols, so a
session with its own closes took place between them.

**Why is it missing?** Not established. The full-history loader requests each weekday and treats a
request answered with another day's file as a weekend or holiday fallback
(scripts/ingest_bhavcopy_full_history.py, P2-005); the 2026-09-16 run's output was not kept and no
log mentions the date (P8-070).

**Knowledge date a fetch now would get.** Under the current loader: the IST date of the archive file's
Last-Modified at the time of the fetch, which cannot be known until fetched: 2022-08-08 if the
original file still stands, a later date if NSE rewrote it (as for the five sessions above). Under
your rule of 18 Oct, a research backfill of an old file needs its own labelled rule, decided then. A
fetch also needs a download budget (one request) and a Praman store write (P8-070's proposed fix).

**Options (development).** A. As built: V2 UNKNOWN 2022-08-08 to 2022-10-20 (50 sessions, 45,842
eligible stock-days without V2); about 32,000 stock-days lost to ATR windows (32,654 against 623);
the day has no bars. B. Closes from the 10 Aug previous close (known 10 Aug): V2 UNKNOWN on 8 Aug only;
ATR loss unchanged. C. Fetch the file with a labelled backfill rule: recovers everything if the rule
dates it to 8 Aug. D. Drop the day from the calendar: windows across it span 21 real sessions
(P8-070's distortion); not recommended.

**Recommendation: B**, as for point 1, and leave P8-070's store fix as a separate decision.

## 3. Missing identity snapshots

**What T1 uses identity for.** The primary population needs equity status known at the decision
date: a resolved non-INF ISIN is equity, an INF ISIN is a fund unit (excluded), and an unknown
identity excludes the stock-day. Breadth denominators and V3's equal-weight market are built from
the same eligible equities, so identity also shapes the market states.

**How it works now.** Each dated snapshot's ISIN applies from its own session onward until a later
snapshot changes it (desk/t1/panel.py `identity_matrix`), so the last known snapshot is already
carried forward, using past information only. Snapshots in the development period: 2019-11-15,
2020-06-15, 2021-02-17, 2021-06-15, 2021-07-22, 2022-06-15, 2023-06-15 (then 2025-02-04).

**Missing development stock-days by year and why.**

| Year | Identity UNKNOWN | Before the first snapshot (2019-11-15) | Listed only by a later snapshot | In no snapshot at all |
| --- | --- | --- | --- | --- |
| 2019 | 43,007 | 41,521 | 1,402 | 84 |
| 2020 | 18,641 | — | 17,779 | 862 |
| 2021 | 12,395 | — | 12,063 | 332 |
| 2022 | 25,285 | — | 24,589 | 696 |
| 2023 | 25,618 | — | 24,635 | 983 |
| 2024 | 59,482 | — | 58,869 | 613 |
| Total | 184,428 | 41,521 | 139,337 | 3,570 |

**Is carrying forward safe?** Yes, and it is already done: it uses only snapshots dated on or before
the session. Across the nine pairs of consecutive snapshots, between 2 and 74 symbols changed ISIN,
and not one moved between equity and fund unit. Carrying forward cannot recover the unknowns,
though: every one of them is a symbol that no earlier snapshot lists (new listings, and the weeks
before the first snapshot). Filling them from a later snapshot would use future information; not safe.

**Options.** A. As built: 184,428 development stock-days excluded. B. More dated snapshots (each one
dated NSE CM bhavcopy file with ISINs, one request each; a download budget). With one on the first
session of every development month (about 56 more files), an estimated 11,600 stock-days would stay
unknown (each new listing only until the next month's snapshot); the 20-month gap from 2023-06-15 to
2025-02-04 alone accounts for 58,869 of 2024's unknowns. Fewer files (for example 2019-10-01 plus
quarterly) recover less; not estimated.

**Recommendation: B, monthly, if you approve the budget.** One thing to decide with it: the ten
snapshots T1 already uses were themselves fetched in October 2026 and are treated as known from their
own dates. Under your 18 Oct rule, research backfills need their own labelled rule; that rule should
be stated for the existing snapshots too, not only for new ones.

## 4. Weekend index sessions

| Date | What it was (general knowledge, not re-checked today) | In the stock store? |
| --- | --- | --- |
| 2019-10-27 (Sun) | Diwali Muhurat trading | yes: 1,470 EQ bars, from the 28 Oct file, known 28 Oct |
| 2020-02-01 (Sat) | Union Budget day, full session | no |
| 2020-11-14 (Sat) | Diwali Muhurat trading | yes: 1,604, from the 16 Nov file, known 16 Nov |
| 2023-11-12 (Sun) | Diwali Muhurat trading | no |
| 2024-01-20 (Sat) | special full trading session | yes: 1,792, from the 22 Jan file, known 22 Jan |
| 2024-03-02 (Sat) | special session (switch to the disaster-recovery site) | no |
| 2024-05-18 (Sat) | special session (switch to the disaster-recovery site) | yes: 1,892, from the 20 May file, known 20 May |
| 2025-02-01 (Sat) | Union Budget day, full session (hold-out year) | no |

Why the store has four of them: each was followed by a weekday holiday (by general knowledge, 28 Oct
2019, 16 Nov 2020, 22 Jan 2024 and 20 May 2024), so the weekday-only loader's request for that
Monday was answered with the weekend session's file, stored under its own date with the Monday's
knowledge date. The other four were followed by an ordinary trading Monday, so they were never
requested (P8-070). None of the four present ones has an eligible stock-day: their bars are known
only on the next weekday.

**Options (development).** A. As built: in T1's calendar only if the store has them (four in, three
out); no eligible stock-days on them, but their bars count inside windows. B. Leave every weekend
session out of the calendar, for stocks and indices alike: no eligible stock-day is lost; windows
across all seven count one session fewer, the same everywhere; their index closes go unused.
C. Put all of them in: fetch the three missing development files (a budget and a labelled backfill
rule); until then each would be a session with every stock missing, costing like 2022-08-08 (about
46,000 eligible stock-days without V2 and 32,000 lost to ATR, each).

**Recommendation: B.** It makes the calendar a rule rather than an accident of which files were
fetched, loses no eligible stock-day, and treats a one-hour Muhurat session and a missing Budget
Saturday the same way. Note for the outcome step: adverse20 counts "the next 20 GLOBAL market
sessions", so whichever calendar you choose here also defines the outcome windows.
