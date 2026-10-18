# Knowledge-date audits, 18 October 2026

Read-only. No stored row was changed.

## 1. P8-083: band rows known before we had them

Question: before 3d7423e (committed 2026-10-14 16:07:32 IST), was any stored price-band row's
knowledge date earlier than the date we fetched it, and did any paper decision read one?

**Answer: none, so no paper decision read one.** The Desk store holds 32,118 band rows: nine lists
dated 1 Oct to 14 Oct. The 24,978 rows recorded before 3d7423e (lists dated 1 to 12 Oct) were each
fetched the same evening NSE published them, so their knowledge date equals the IST date of the
fetch. The only late list, 13 Oct's, was fetched on 14 Oct at 19:42 IST, after 3d7423e, and is
stored as known from 14 Oct.

| List dated | NSE Last-Modified (IST) | Fetched (IST) | Knowledge date | Rows |
| --- | --- | --- | --- | --- |
| 1 Oct | 1 Oct 19:39 | 1 Oct 21:25 | 1 Oct | 3,574 |
| 5 Oct | 5 Oct 17:58 | 5 Oct 18:08 | 5 Oct | 3,559 |
| 6 Oct | 6 Oct 17:55 | 6 Oct 21:12 | 6 Oct | 3,562 |
| 7 Oct | 7 Oct 19:24 | 7 Oct 20:56 | 7 Oct | 3,565 |
| 8 Oct | 8 Oct 18:01 | 8 Oct 19:01 | 8 Oct | 3,563 |
| 9 Oct | 9 Oct 19:16 | 9 Oct 19:57 | 9 Oct | 3,585 |
| 12 Oct | 12 Oct 18:23 | 12 Oct 21:19 | 12 Oct | 3,570 |
| 13 Oct | 13 Oct 19:00 | 14 Oct 19:42 | 14 Oct | 3,570 |
| 14 Oct | 14 Oct 18:22 | 14 Oct 19:42 | 14 Oct | 3,570 |

Within a day: knowledge is stored as a date, so a list fetched at 21:25 is "known" on that whole
day. No paper decision dated that day ran before the fetch: in the nightly, circuit_bands runs
before desk_scan and auto_paper, and a live decision can only read rows already in the store.
Audit replays filter on recorded_at (desk/replay.py), so they see what the decision saw.

Not in the store: the September lists that docs/desk/price_band_source.md says were inserted on
1 Oct (35,427 rows). They were lost when the Desk store was reset on 1 Oct, before the nightly began
(P8-025, "durable Desk store cleared during a proof": "the present 3,574 rows do not substantiate that
historical coverage. Missing historical bands remain unknown, never zero"). So there is nothing to
correct and no new defect.
