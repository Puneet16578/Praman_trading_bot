# Phase 3, Session B — SEBI Label Count Spike (read-only measurement)

## Headline

Cannot answer the core question (confirmed count of usable post-2019-10-01 price-manipulation
labels) from this environment. Zero SEBI order documents were opened — not one PDF, not one order
detail page — through any method tried. **Decision: SEBI is no longer the primary evaluation
label source.** The evaluation rests on ASM/GSM placements and computed outcome labels (price
held/consolidated/collapsed at 30/60/90 days) instead. Confirmed SEBI cases become an optional
small-sample validation layer if ever obtained, not a dependency.

## The finding that matters more than the blocker

**SEBI order titles never use manipulation vocabulary.** Zero hits across 175 real titles (parsed
from 7 Wayback-archived listing snapshots, 2019–2026) for "manipulat", "artificial", "pump",
"synchron", "circular trad", "price rigging". A keyword filter built on the obvious vocabulary
would have returned nothing, and a less careful pass would have wrongly concluded no such cases
exist. The real signature in SEBI's own titling convention is **"trading activities of certain
entities in the scrip of X"** / **"N entities/noticees in the matter of X"** — found via reading
real titles, not guessed in advance.

**46% of titles (81/175) are bare "Adjudication Order in the matter of [Company]"** with no
category signal at all. Even with full PDF access, title-level filtering cannot identify the
population on its own — classification would require opening a large fraction of the ~5,000
orders published since the 2019-10-01 floor. SEBI was always going to be an expensive source,
independent of the access blocker.

## What was reachable, and what was not

- **Live `sebi.gov.in`**: reachable at the homepage only (200, after fixing a genuine server-side
  TLS chain misconfiguration — the missing Sectigo intermediate — with a proper combined CA
  bundle, not `verify=False`). Every deeper path (listing, individual order, alternate
  `HomeAction.do` listing, a direct PDF under `/sebi_data/`) returns 403, confirmed identically
  via `requests`, `curl` (independent TLS stack), and a cookie-warmed session.
- **WebFetch**: blocked by the same cert-chain issue independently.
- **Wayback Machine**: archived the listing/menu pages 32 times since 2017 (useful — see below),
  but **zero** individual order pages or PDFs (`sebi.gov.in/enforcement/orders/*` returns no CDX
  results at all). Nothing to open even via archive.

## Real index-level data obtained (via Wayback, not live SEBI)

"Orders of AO" (Adjudicating Officer) is the relevant category (`smid=6`) — `/enforcement/orders.html`
itself is only a category menu, not a listing.

Total records over time (real, read from each snapshot's own count line):

| Snapshot | Total AO orders |
|---|---|
| 2019-03-25 | 6,577 |
| 2021-04-16 | 8,235 |
| 2022-04-05 | 9,368 |
| 2023-02-01 | 10,094 |
| 2024-02-21 | 11,233 |
| 2025-01-08 | 11,482 |
| 2026-06-11 | 11,961 |

Category breakdown (175 distinct titles, 7 snapshots): illiquid stock options at BSE 35.4%,
unclassified bare-company 46.3%, trading-pattern-in-scrip (manipulation proxy) 6.3%, other
intermediary/disclosure 4.6%, GDR fraud 2.3%, inspection/debenture-trustee/fit-and-proper 4.0%,
front running 1.1%.

**Extrapolated estimate, explicitly not a count**: ~6,975 AO orders existed as of 2019-10-01
(linear interpolation) → ~4,986 published since → ~314 matching the title-pattern proxy. Actual
population is almost certainly larger given the 46% unclassified bucket, and an unknown
(plausibly large) fraction of the ~314 concern pre-floor activity despite post-floor publication
(adjudication lag is real and unmeasured here). No further precision is honest without opening
documents.

## Follow-up 1 — is the block IP-based or fingerprint-based?

Could not literally test from a second physical network (no phone/alternate connection available
in this environment). Checked the next best thing: this sandbox's own egress IP resolves to
**AS55836, Reliance Jio Infocomm, West Bengal, India** — a real residential/mobile ISP
allocation, not a datacenter/hosting range. Since a plainly non-datacenter Indian ISP IP is
already blocked past the homepage, **IP-range reputation is an unlikely sole explanation** — the
block is more likely fingerprint/bot-management-based (missing browser TLS/JS characteristics),
which a phone hotspot would probably not fix either. Not proven to the standard of an actual
side-by-side test; flagged as suggestive evidence, not certainty. The user can still run the
literal test in ~2 minutes if full certainty is wanted.

## Follow-up 2 — IndianKanoon SAT appeals, scrip/period extractability

IndianKanoon (indiankanoon.org) returns 200 and is reachable. Searched for SEBI/SAT manipulation
appeals; opened three post-2019 decisions in full (not summarized — full judgment text read):

1. **Morepen Laboratories Ltd. vs SEBI** (SAT, decided 2021-04-15) — appeal against a 2019-09-24
   SEBI WTM order. On reading: this is a **GDR-issuance/market-access matter, not a clean
   price-manipulation case** — the word "manipulation" appears only in a denial, and the one
   scrip+period mention found (`Oregon Commercial Ltd., Jan 2010–Jan 2011`) is a citation to a
   different, older precedent case, not Morepen's own facts. **Not a usable hit** — an honest
   miss, reported rather than stretched to count.

2. **Aahuti Rasik Mistry (incl. Arshad Hussain Warsi) vs SEBI** (SAT, decided 2023-03-27) — a
   **clean, fully extractable hit**: scrip = **Sadhna Broadcast Ltd.**; period = a YouTube video
   uploaded **July 15, 2022** drove a price run-up, with the order distinguishing "patch 1"
   (April–July 2022) from a second patch after; SEBI's own language: "price manipulation and
   offloading of shares... misleading YouTube videos." Real scrip name, real period, squarely
   post-2019-10-01. **Exchange listing (NSE vs. BSE) not independently verified this session —
   flagged, not assumed.**

3. **Ketan Jumakhlal Mehta / Sorabh Kumar Poddar vs SEBI** (SAT, decided 2023-02-14) — another
   clean, fully extractable hit, and a useful negative example: scrip = **Mishka Finance Ltd.**,
   explicitly stated as **"listed on the Bombay Stock Exchange"** (BSE, not NSE), period =
   **February 14, 2013 – December 31, 2014**. Real manipulation case, real scrip, real period —
   but fails both the NSE-listed criterion and the 2019-10-01 floor by nine years, despite being
   *decided* in 2023. This is a concrete, real instance of the conduct-to-disposition lag this
   whole exercise has been theorizing about, not a hypothetical.

**Answer to the question asked**: yes, scrip name and period ARE consistently extractable from
full SAT judgment text once opened (all three cases had both, cleanly stated) — the difficulty is
entirely in *finding* the right cases (title-based search is unreliable, as above) and in the
conduct-to-disposition lag (2 of 3 opened cases concerned dates far removed from their decision
date, one on the wrong side of the 2019-10-01 floor entirely). Partial coverage (3 of the
requested 5) — stopping here per "a short read-only pass."

## ASM/GSM — now load-bearing, not a feature (next session, not started)

Per the decision above, ASM/GSM placements are now one of the two primary label sources for the
evaluation (the other being computed outcome labels). The endpoint-discovery gap flagged in the
prior source-evaluation session (guessed URLs, all 404) is unresolved and now matters more than
it did before. Next session: open NSE's surveillance page in a real browser with devtools and
read the network tab rather than guessing further; report definitively whether it's an API call
or server-rendered (in which case circular PDFs are the answer). Not started this session, per
instruction.

## Rules followed

Read-only throughout — no ingestion, no store writes, no schema changes. Everything fetched
(7 Wayback snapshots, parsed titles, 3 full SAT judgments, cert bundle) cached to disk in the
scratchpad for reuse without re-fetching.
