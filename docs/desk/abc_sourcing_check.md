# A, B and C: sourcing check, not a strategy registration

19 October 2026. Repository inspected: `38e79cf`.

The working descriptions of A, B and C remain unchanged and unregistered. This report chooses no entry, holding-period, reaction-strength, materiality, causal-explanation or surveillance-screening rule. The draft category map and time bins below are counting conventions for user review only; they are not installed in code. No inference about profitability or next-session tradability is made.

## Scope and reproducibility

The stored final catalogue supplies only symbol, event date and the sign of its existing event-day `return_1d`. No catalogue was rebuilt. The CSV contains contemporaneous/trailing features, not forward outcomes. SQLite was opened with `shared.sqlite_readonly.open_readonly` (`mode=ro`); only announcement metadata/text, surveillance transitions and bhavcopy symbol/date/knowledge-date/series membership were queried. No OHLC, subsequent returns, outcome labels, execution records or sealed paper results were selected for the census. Prior exposure was inventoried from analysis definitions, source code and artifact names, without opening outcome datasets or reproducing their performance tables.

Event/announcement counts cover 2019-10-01 through 2025-12-31 inclusive. Announcement lookup allows metadata back to 2019-07-03 for the 90-calendar-day lookback. Main counts use one read transaction; supplemental date/category checks use separate read-only connections. All comparisons use exact stored symbols, not a current alias map. Historical announcement ISIN/raw-response provenance is absent, as documented in `r2_sourcing_check.md`; renamed securities can therefore appear uncovered.

The firewall and Strategy 0 seal are unchanged. No API/data download, attachment retrieval, strategy evaluation or new post-event move calculation was performed. Only the three official documentation URLs listed in section 7 were opened, sequentially, using the documentation allowance; no data endpoint was called.

Catalogue SHA-256: `ab6dbe701b223076824f4430db5139dba8ed2ecdf9a5cdef5db29ed8e2e81908`.

Selected announcement metadata SHA-256: `51cb98e5375420c3d31449d67a6b5ed8b878962e083d78fc926c282ef7bddc82` (row_id order, JSON tuples of row_id/symbol/event_date/knowledge_date/category/sort_timestamp/description, ASCII escaping, compact separators, concatenated with no separator; bounds above).

## 1. Stored catalogue events

| Year | Up | Down | Zero | Total |
|---|---|---|---|---|
| 2019 | 0 | 0 | 0 | 0 |
| 2020 | 7,144 | 2,767 | 0 | 9,911 |
| 2021 | 7,691 | 1,272 | 0 | 8,963 |
| 2022 | 7,055 | 2,249 | 0 | 9,304 |
| 2023 | 9,280 | 2,616 | 0 | 11,896 |
| 2024 | 8,135 | 2,456 | 0 | 10,591 |
| 2025 | 7,394 | 2,635 | 0 | 10,029 |
| Total | 46,699 | 13,995 | 0 | 60,694 |

Distinct event symbols: **2,343**. First event is 2020-01-01; last in scope is 2025-12-31. The zero for October-December 2019 reflects the stored catalogue and its trailing-history requirement, not zero economic events. The underlying data starts in October 2019. Counts are unique (symbol, event_date); duplicate keys were asserted absent.

Source: `scripts/build_final_event_catalogue.py:45-55`: absolute 60-session z-score strictly greater than 2.5 and traded quantity / trailing 60-session median strictly greater than 2.0. Stored membership also reflects EQ/identity and structural-break exclusions; this is not a fresh application of two thresholds to every stock. Up/down is the sign of the event-day return, not the sign of the z-score and not a later return. The original identity stitching and current-map limitations remain part of this artifact's provenance.

## 2. Complete category inventory and draft map

Every category present in the bounded store is listed below, preserving spelling/case. Counts are stored rows, not deduplicated economic releases. There are 279 categories and 889,024 rows. Material news means the name explicitly identifies a potentially consequential result, business/capital event, default, regulatory action or operational change; its size, novelty and directional relevance are still unverified. Routine means the name chiefly describes scheduling, compliance, republication or administration. All other names are Unclear and marked **REVIEW**.

This deliberately does not copy the existing forensic SUBSTANTIVE label. For example, Outcome of Board Meeting, Updates, Press Release, Price movement and Spurt in Volume are Unclear: a board outcome may bundle many matters, and an exchange query about a move is not an independent explanation of that move. Corrections, generic credit-rating notices, management changes without role detail and transcripts also need review. Even a category provisionally mapped Material cannot, by itself, explain an event or support a long trade. Routine filings can contain embedded news; this map may miss it.

| Draft group | Categories | Rows |
|---|---|---|
| Material news | 90 | 78,937 |
| Routine | 57 | 397,939 |
| Unclear | 132 | 412,148 |

| Exact category | Rows | Draft group | Uncertainty |
|---|---|---|---|
| AGM/Book Closure | 47 | Routine | Embedded news possible |
| AGM/Record Date | 3 | Routine | Embedded news possible |
| Acquisition | 5,295 | Material news | Size/novelty unverified |
| Action(s) initiated or orders passed | 861 | Material news | Size/novelty unverified |
| Action(s) taken or orders passed | 1,612 | Material news | Size/novelty unverified |
| Addendum | 189 | Unclear | REVIEW |
| Address Change | 516 | Routine | Embedded news possible |
| Adjournment/Reschedule/Postpone | 6 | Routine | Embedded news possible |
| Adoption of new line(s) of business | 30 | Material news | Size/novelty unverified |
| Agreements | 637 | Unclear | REVIEW |
| Agreements,Contracts,Arrangements,MOU-XBRL | 7 | Unclear | REVIEW |
| Agreements/Contracts/Arrangements/ MOU's PARA A | 104 | Unclear | REVIEW |
| Agreements/Contracts/Arrangements/ MOU's PARA B | 95 | Unclear | REVIEW |
| Allotment of ESOP/ESPS | 706 | Unclear | REVIEW |
| Allotment of Securities | 5,665 | Unclear | REVIEW |
| Alteration Of Capital and Fund Raising-XBRL | 1 | Unclear | REVIEW |
| Alteration/revision(s) | 9 | Unclear | REVIEW |
| Amalgamation/Merger | 1,097 | Material news | Size/novelty unverified |
| Amendment to AOA/MOA | 1,371 | Unclear | REVIEW |
| Amendment(s) | 28 | Unclear | REVIEW |
| Amendment/Termination of awards/contracts | 6 | Material news | Size/novelty unverified |
| Analysts/Institutional Investor Meet/Con. Call Updates | 95,422 | Routine | Embedded news possible |
| Annual Disclosure | 983 | Unclear | REVIEW |
| Annual General Meeting | 5,703 | Routine | Embedded news possible |
| Annual Secretarial Compliance Report | 1,881 | Routine | Embedded news possible |
| Appointment | 13,712 | Unclear | REVIEW |
| Appointment of Chairman and CEO/Election of Directors | 1 | Unclear | REVIEW |
| Appointment of Company Secretary and Compliance Officer | 3 | Unclear | REVIEW |
| Appointment of Director | 3 | Unclear | REVIEW |
| Arrangements for strategic, technical, manufacturing, or marketing tie up | 80 | Material news | Size/novelty unverified |
| Audit Qualifications/Comments | 10 | Material news | Size/novelty unverified |
| Auditor's report | 146 | Unclear | REVIEW |
| Awarding of order(s)/contract(s) | 287 | Material news | Size/novelty unverified |
| Awarding orders/contract | 208 | Material news | Size/novelty unverified |
| Bagging orders/contract | 147 | Material news | Size/novelty unverified |
| Bagging/Receiving of orders/contracts | 1,352 | Material news | Size/novelty unverified |
| Board Meeting Adjourned | 80 | Routine | Embedded news possible |
| Board Meeting Deferred | 4 | Routine | Embedded news possible |
| Board Meeting Intimation | 363 | Routine | Embedded news possible |
| Board Meeting Postponed | 15 | Routine | Embedded news possible |
| Board meeting Cancelled | 227 | Routine | Embedded news possible |
| Board meeting Rescheduled | 3 | Routine | Embedded news possible |
| Bonus | 503 | Material news | Size/novelty unverified |
| Bonus/Dividend | 1 | Material news | Size/novelty unverified |
| Book Closure | 6,767 | Routine | Embedded news possible |
| Business Responsibility & Sustainability Report (BRSR) | 85 | Routine | Embedded news possible |
| Buyback | 433 | Material news | Size/novelty unverified |
| Buyback - Open Market | 13 | Material news | Size/novelty unverified |
| Buyback - Tender offer | 20 | Material news | Size/novelty unverified |
| Buyback - others | 68 | Unclear | REVIEW |
| CIRP - Approval of Resolution Plan | 13 | Material news | Size/novelty unverified |
| CIRP - Change in Resolutional Professional | 7 | Unclear | REVIEW |
| CIRP - Commencement | 28 | Material news | Size/novelty unverified |
| CIRP - Committee meeting updates | 369 | Unclear | REVIEW |
| CIRP - Filing of Resolution Plan | 10 | Unclear | REVIEW |
| CIRP - Filing of application | 15 | Material news | Size/novelty unverified |
| CIRP - Revocation/rejection | 4 | Material news | Size/novelty unverified |
| CIRP - others | 386 | Unclear | REVIEW |
| Cancellation | 24 | Unclear | REVIEW |
| Cancellation of Book closure | 40 | Routine | Embedded news possible |
| Cancellation of Dividend | 7 | Material news | Size/novelty unverified |
| Cancellation of Record Date | 1 | Routine | Embedded news possible |
| Cancellation of Record date | 40 | Routine | Embedded news possible |
| Capacity addition | 256 | Material news | Size/novelty unverified |
| Capacity addition/product launch | 92 | Material news | Size/novelty unverified |
| Capital Reduction | 3 | Material news | Size/novelty unverified |
| Certificate under SEBI (Depositories and Participants) Regulations, 2018 | 28,248 | Routine | Embedded news possible |
| Cessation | 3,184 | Unclear | REVIEW |
| Change in Auditors | 2,279 | Material news | Size/novelty unverified |
| Change in Company Secretary/Compliance Officer | 1,257 | Unclear | REVIEW |
| Change in Director(s) | 7,484 | Unclear | REVIEW |
| Change in Directors/ Key Managerial Personnel/ Auditor/ Compliance Officer/ Share Transfer Agent | 188 | Unclear | REVIEW |
| Change in Financial Year | 5 | Unclear | REVIEW |
| Change in Management | 5,631 | Unclear | REVIEW |
| Change in Management Control | 1 | Material news | Size/novelty unverified |
| Change in designation | 100 | Unclear | REVIEW |
| Clarification | 2,723 | Unclear | REVIEW |
| Clarification - Financial Results | 3,082 | Unclear | REVIEW |
| Clarification- Financial Results | 275 | Unclear | REVIEW |
| Closure of Buy Back | 107 | Unclear | REVIEW |
| Closure of Buyback | 9 | Unclear | REVIEW |
| Closure of operations | 65 | Material news | Size/novelty unverified |
| Closure of operations of any unit/division | 17 | Material news | Size/novelty unverified |
| Closure of trading window | 5,564 | Routine | Embedded news possible |
| Code of Conduct under SEBI(PIT) Reg., 2015 | 914 | Routine | Embedded news possible |
| Code of conduct under SEBI (PIT) Regulations | 231 | Routine | Embedded news possible |
| Commencement of commercial production/operations | 278 | Material news | Size/novelty unverified |
| Commencement/Postponement of Operations | 45 | Material news | Size/novelty unverified |
| Committee Meeting Updates | 1,224 | Routine | Embedded news possible |
| Communication to shareholders as per Reg 30 | 1,234 | Unclear | REVIEW |
| Confirmation of payment of Interest/Principal | 37 | Unclear | REVIEW |
| Consolidated Result Updates - IFRS | 9 | Material news | Size/novelty unverified |
| Conversion | 143 | Unclear | REVIEW |
| Copy of Newspaper Publication | 56,334 | Routine | Embedded news possible |
| Corp Restructuring - others | 20 | Unclear | REVIEW |
| Corporate Debt Restructuring | 21 | Material news | Size/novelty unverified |
| Corporate Insolvency Resolution Process | 3,152 | Material news | Size/novelty unverified |
| Corrigendum | 1,112 | Unclear | REVIEW |
| Credit Rating | 8,811 | Unclear | REVIEW |
| Credit Rating- New | 244 | Material news | Size/novelty unverified |
| Credit Rating- Others | 233 | Unclear | REVIEW |
| Credit Rating- Revision | 517 | Material news | Size/novelty unverified |
| Daily Buy Back of securities | 405 | Unclear | REVIEW |
| Date of payment of Interest/Principal | 13 | Routine | Embedded news possible |
| Date of payment of dividend | 540 | Routine | Embedded news possible |
| Debentures | 56 | Unclear | REVIEW |
| Declaration for audit reports with unmodified opinion(s) | 290 | Routine | Embedded news possible |
| Defaults on Payment of Interest/Principal | 1,912 | Material news | Size/novelty unverified |
| Delay/default in the payment of fines/penalties/dues etc. to authority | 46 | Material news | Size/novelty unverified |
| Delisting | 39 | Material news | Size/novelty unverified |
| Demerger | 110 | Material news | Size/novelty unverified |
| Demise | 457 | Unclear | REVIEW |
| Disc. under Reg.30 of SEBI (SAST) Reg.2011 | 35 | Routine | Embedded news possible |
| Disclosure of Annual financial information (if submitted as part of Annual Report) | 25 | Unclear | REVIEW |
| Disclosure of Half yearly financial information (if submitted as part of Half-Yearly Report) | 2 | Unclear | REVIEW |
| Disclosure of Pledged Shares | 1 | Unclear | REVIEW |
| Disclosure of Valuation report | 1 | Unclear | REVIEW |
| Disclosure of all complaints including SCORES complaints received by the InvIT on a quarterly basis | 3 | Routine | Embedded news possible |
| Disclosure of material issue | 914 | Material news | Size/novelty unverified |
| Disclosure of other UPSI/material event | 1,021 | Material news | Size/novelty unverified |
| Disclosure of record date for purpose of distribution | 74 | Routine | Embedded news possible |
| Disclosure under SEBI (PIT) Reg 2015 | 123 | Routine | Embedded news possible |
| Disclosure under SEBI Takeover Regulations | 23,558 | Unclear | REVIEW |
| Disruption of Operations | 59 | Material news | Size/novelty unverified |
| Disruption of operations | 41 | Material news | Size/novelty unverified |
| Diversification/Disinvestment | 529 | Material news | Size/novelty unverified |
| Dividend | 8,355 | Material news | Size/novelty unverified |
| Dividend Updates | 2,040 | Unclear | REVIEW |
| E-mail ID for Investor's Grievance Redressal | 35 | Routine | Embedded news possible |
| ESOP/ESOS/ESPS | 8,598 | Unclear | REVIEW |
| ESOP/ESPS/SBEB Scheme | 1,332 | Unclear | REVIEW |
| Effect(s) on listed entity due to changed regulatory  framework applicable | 8 | Unclear | REVIEW |
| Effects - Change in regulatory framework | 1 | Unclear | REVIEW |
| Extension  of Financial Year | 3 | Unclear | REVIEW |
| Extension of Annual General Meeting | 243 | Routine | Embedded news possible |
| Extinguishment | 2 | Unclear | REVIEW |
| Extra Ordinary Meeting | 648 | Unclear | REVIEW |
| FCCB/ FCEB | 2 | Unclear | REVIEW |
| FCCBs | 10 | Unclear | REVIEW |
| Final  forensic  audit  report | 3 | Material news | Size/novelty unverified |
| Financial Result Updates | 36,241 | Material news | Size/novelty unverified |
| Financial Results Updates | 1,379 | Material news | Size/novelty unverified |
| Follow-on public issue | 4 | Material news | Size/novelty unverified |
| Forfeiture | 27 | Unclear | REVIEW |
| Fraud/Default/Arrest | 49 | Material news | Size/novelty unverified |
| Frauds/Default by employees | 6 | Material news | Size/novelty unverified |
| GDRs/GDS | 6 | Unclear | REVIEW |
| General Updates | 19,864 | Unclear | REVIEW |
| General updates | 17,708 | Unclear | REVIEW |
| Giving guarantees/indemnity/ becoming a surety for third party | 198 | Unclear | REVIEW |
| Giving of guarantee/indemnity or becoming surety | 10 | Unclear | REVIEW |
| Global Depository Receipts | 1 | Unclear | REVIEW |
| Grant of licenses/regulatory approvals | 20 | Material news | Size/novelty unverified |
| Granting/withdrawal/surrender/cancellation/suspension of key licenses/ regulatory approvals | 118 | Material news | Size/novelty unverified |
| Incorporation | 215 | Unclear | REVIEW |
| Incorporation-XBRL | 4 | Unclear | REVIEW |
| Increase in Authorised Capital | 151 | Unclear | REVIEW |
| Initiation of Forensic Audit | 5 | Material news | Size/novelty unverified |
| Insider Trading - Others | 296 | Unclear | REVIEW |
| Institutional Placement Programme | 6 | Unclear | REVIEW |
| Integrated Filing- Financial | 2,469 | Material news | Size/novelty unverified |
| Integrated Filing- Governance | 177 | Unclear | REVIEW |
| Interest Rates Updates | 356 | Unclear | REVIEW |
| Intimation of Board Meeting | 4 | Routine | Embedded news possible |
| Investor Presentation | 19,322 | Unclear | REVIEW |
| Issuance/changes in Capital-Others | 57 | Unclear | REVIEW |
| Issue of Duplicate Share Certificate | 733 | Routine | Embedded news possible |
| Issue of Securities | 802 | Unclear | REVIEW |
| Limited Review Report | 491 | Unclear | REVIEW |
| Liquidation | 11 | Material news | Size/novelty unverified |
| Litigations/Disputes/Regulatory actions | 76 | Material news | Size/novelty unverified |
| Loss of Share Certificates | 62,932 | Routine | Embedded news possible |
| Loss of share certificate | 12,018 | Routine | Embedded news possible |
| Memorandum of Understanding/Agreements | 633 | Unclear | REVIEW |
| Monitoring Agency Report | 2,581 | Unclear | REVIEW |
| Monthly Business Updates | 1,083 | Unclear | REVIEW |
| NCLT/ Court Convened Meeting | 278 | Unclear | REVIEW |
| Name & Symbol Change | 31 | Routine | Embedded news possible |
| Name Change | 273 | Routine | Embedded news possible |
| Name and Symbol Change | 122 | Routine | Embedded news possible |
| News Clarification | 9 | Unclear | REVIEW |
| News Verification | 2,319 | Unclear | REVIEW |
| News verification | 1 | Unclear | REVIEW |
| Newspaper Advertisements | 8,600 | Routine | Embedded news possible |
| Notice Of Shareholders Meetings-XBRL | 16 | Routine | Embedded news possible |
| Notice of Unitholder meetings | 11 | Unclear | REVIEW |
| Offer For Sale-Stock Exchange Mechanism | 4 | Unclear | REVIEW |
| Offer for sale | 190 | Unclear | REVIEW |
| One Time Settlement | 31 | Material news | Size/novelty unverified |
| One time settlement | 16 | Material news | Size/novelty unverified |
| Open Offer | 286 | Material news | Size/novelty unverified |
| Open offer | 1 | Material news | Size/novelty unverified |
| Options to purchase securities | 347 | Unclear | REVIEW |
| Other Restructuring | 64 | Unclear | REVIEW |
| Others | 97 | Unclear | REVIEW |
| Outcome of Board Meeting | 52,314 | Unclear | REVIEW |
| Outcome of Board Meeting-XBRL | 3 | Unclear | REVIEW |
| Outcome of Unitholder meetings | 11 | Unclear | REVIEW |
| Outcome of committee meeting | 116 | Unclear | REVIEW |
| Payouts- others | 8 | Unclear | REVIEW |
| Pendency of Litigation(s)/dispute(s) or the outcome impacting the Company | 908 | Material news | Size/novelty unverified |
| Post Buyback Public Announcement | 210 | Unclear | REVIEW |
| Post Offer Public Announcement | 54 | Unclear | REVIEW |
| Post Offer Public announcement | 6 | Unclear | REVIEW |
| Postal Ballot | 1,900 | Unclear | REVIEW |
| Postponement of commercial production/operations | 4 | Material news | Size/novelty unverified |
| Preference Shares | 6 | Unclear | REVIEW |
| Preferential Issue | 75 | Material news | Size/novelty unverified |
| Preferential issue | 376 | Material news | Size/novelty unverified |
| Press Release | 37,574 | Unclear | REVIEW |
| Press Release (Revised) | 456 | Unclear | REVIEW |
| Price movement | 6,202 | Unclear | REVIEW |
| Product launch | 188 | Material news | Size/novelty unverified |
| Public Announcement - Buyback of Shares | 229 | Material news | Size/novelty unverified |
| Public Announcement - Delisting | 14 | Material news | Size/novelty unverified |
| Public Announcement-Open Offer | 212 | Material news | Size/novelty unverified |
| Publish Audited Results | 232 | Unclear | REVIEW |
| Qualified Institutional Placement | 320 | Material news | Size/novelty unverified |
| Qualified Institutional Placements | 8 | Material news | Size/novelty unverified |
| Quarterly Compliance Report on Corporate governance - within 21 days from the end of the quarter | 104 | Routine | Embedded news possible |
| Raising of Funds | 1 | Material news | Size/novelty unverified |
| Re-appointment | 841 | Unclear | REVIEW |
| Reappointment | 104 | Unclear | REVIEW |
| Reasons for Delayed/Non-submission of Financial Results | 250 | Unclear | REVIEW |
| Record Date | 8,899 | Routine | Embedded news possible |
| Record Date Updates | 15 | Routine | Embedded news possible |
| Recording of Analysts/Institutional Investor Meet/Con. Call | 2,127 | Unclear | REVIEW |
| Redemption | 378 | Unclear | REVIEW |
| Registrar & Share Transfer Agent Update | 748 | Routine | Embedded news possible |
| Related Party Transaction | 3,490 | Unclear | REVIEW |
| Related Party Transactions | 9,971 | Unclear | REVIEW |
| Reply to Clarification Sought | 2,355 | Unclear | REVIEW |
| Reply to Clarification Sought- Financial Results | 317 | Unclear | REVIEW |
| Reply to Clarification- Financial results | 2,759 | Unclear | REVIEW |
| Rescission/termination(s) | 22 | Unclear | REVIEW |
| Resignation | 7,982 | Unclear | REVIEW |
| Resignation of Independent director | 1,138 | Unclear | REVIEW |
| Resignation of Statutory Auditor | 192 | Material news | Size/novelty unverified |
| Restructuring | 133 | Material news | Size/novelty unverified |
| Retirement | 799 | Unclear | REVIEW |
| Revised Book Closure | 109 | Routine | Embedded news possible |
| Revised Record date | 313 | Routine | Embedded news possible |
| Revocation of Suspension of Securities | 8 | Unclear | REVIEW |
| Rights Issue | 534 | Material news | Size/novelty unverified |
| Rumour Verification - Regulation 30(11) | 276 | Unclear | REVIEW |
| Sale or disposal | 145 | Material news | Size/novelty unverified |
| Sale or disposal of unit/ division/subsidiary | 122 | Material news | Size/novelty unverified |
| Sale or disposal-XBRL | 3 | Material news | Size/novelty unverified |
| Schedule of Analysts/Institutional Investor Meet/Con. Call | 10,472 | Routine | Embedded news possible |
| Scheme of Arrangement | 1,116 | Material news | Size/novelty unverified |
| Share Warrants | 22 | Unclear | REVIEW |
| Shareholders meeting | 44,237 | Routine | Embedded news possible |
| Shifting of security out of Z category | 2 | Unclear | REVIEW |
| Slump Sale | 7 | Material news | Size/novelty unverified |
| Split of shares | 35 | Material news | Size/novelty unverified |
| Spurt in Volume | 5,206 | Unclear | REVIEW |
| Statement of deviation(s) or variation(s) under Reg. 32 | 3,736 | Unclear | REVIEW |
| Statement on Impact of Audit Qualifications | 70 | Unclear | REVIEW |
| Stock split | 341 | Material news | Size/novelty unverified |
| Strikes/Lockouts/Disturbances | 806 | Material news | Size/novelty unverified |
| Structural Digital Database | 303 | Routine | Embedded news possible |
| Submission of Standalone/ Consolidated or Both | 7 | Routine | Embedded news possible |
| Suspension of Trading | 266 | Material news | Size/novelty unverified |
| Suspension of partly paid up equity shares | 1 | Material news | Size/novelty unverified |
| Suspension of trading in equity shares | 1 | Material news | Size/novelty unverified |
| Symbol Change of company | 13 | Routine | Embedded news possible |
| Trading Plan under PIT | 142 | Routine | Embedded news possible |
| Trading Plan under SEBI (PIT) Reg., 2015 | 1 | Routine | Embedded news possible |
| Trading Plan under SEBI (PIT) Regulations | 11 | Routine | Embedded news possible |
| Trading Window | 42,762 | Routine | Embedded news possible |
| Transcript of Analysts/Institutional Investor Meet/Con. Call | 2,384 | Unclear | REVIEW |
| Update-Acquisition/Scheme/Sale/Disposal/Reg30-XBRL | 17 | Unclear | REVIEW |
| Updates | 104,048 | Unclear | REVIEW |
| Utilisation of Funds | 101 | Unclear | REVIEW |
| Voluntary Delisting | 150 | Material news | Size/novelty unverified |
| Voluntary Revision of Financial statements or Report | 3 | Unclear | REVIEW |
| Withdrawal | 34 | Unclear | REVIEW |
| Withdrawal of Rights Issue | 7 | Material news | Size/novelty unverified |
| Withdrawal/Surrender/Cancellation or suspension of licenses/ regulatory approvals | 1 | Material news | Size/novelty unverified |

## 3. Same-symbol announcement timing: event counts only

Assumption: stored naive `sort_timestamp` is IST, as requested. These are timestamp associations, not causal explanations. `knowledge_date <= event_date` is required. A timestamp parse failure or timestamp/date mismatch is kept separate, never assigned an invented hour. Repeated filings cannot multiply an event within a bin; one event can appear in multiple bins.

Counting boundaries: previous calendar evening = calendar D-1 after 15:30; before open = D 00:00 to before 09:15; during session = D 09:15 through 15:30 inclusive; after close = D later than 15:30. These use normal-session hours only; special-session schedules are not established by a bar date. Boundary choices are disclosed diagnostic conventions, not an approved decision clock.

For Monday/holiday gaps, a fifth column retains the rest of the interval from the previous stored EQ session's close to D midnight, excluding the already counted previous calendar evening. Thus Friday evening/weekend material is not silently lost. It uses the observed EQ-date calendar, including special/weekend sessions, with known missing-session limitations. After-close announcements cannot explain the already completed event-day move; during-session announcements cannot be ordered against the move using daily bars.

| Year | Previous calendar evening | Before open | During session | After close | Other intervening closure time | Any material in four requested bins | Any material including closure bridge |
|---|---|---|---|---|---|---|---|
| 2019 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2020 | 284 | 14 | 194 | 108 | 123 | 580 | 698 |
| 2021 | 322 | 7 | 201 | 91 | 186 | 602 | 786 |
| 2022 | 253 | 19 | 162 | 104 | 175 | 513 | 679 |
| 2023 | 576 | 6 | 360 | 142 | 300 | 1,065 | 1,362 |
| 2024 | 564 | 7 | 361 | 123 | 267 | 1,028 | 1,290 |
| 2025 | 444 | 18 | 245 | 230 | 216 | 837 | 1,045 |
| Total | 2,443 | 71 | 1,523 | 798 | 1,267 | 4,625 | 5,860 |

| Year | No draft material in full window | Unclear category present |
|---|---|---|
| 2019 | 0 | 0 |
| 2020 | 9,213 | 2,031 |
| 2021 | 8,177 | 2,042 |
| 2022 | 8,625 | 2,486 |
| 2023 | 10,534 | 3,057 |
| 2024 | 9,301 | 2,953 |
| 2025 | 8,984 | 3,277 |
| Total | 54,834 | 15,846 |

Unparseable material timestamps and timestamp/date mismatches in these event windows: 0. No material-category association does **not** mean unexplained: unclear categories, identity gaps, incomplete capture and earlier news remain unresolved. Material timing counts must not be used as an A/B split until reviewed.

## 4. Ninety-day announcement coverage

Window = [D minus 90 calendar days, D), any category, exact stored symbol, knowledge_date no later than D. Event-day filings are deliberately not allowed to fill a preceding-history gap. These are event counts, with repeated stocks across events retained; no-announcement is a coverage warning rather than evidence of no news.

| Year | At least one in prior 90 days | No announcement in prior 90 days | No earlier cached announcement |
|---|---|---|---|
| 2019 | 0 | 0 | 0 |
| 2020 | 9,072 | 839 | 832 |
| 2021 | 8,281 | 682 | 674 |
| 2022 | 8,648 | 656 | 643 |
| 2023 | 11,291 | 605 | 595 |
| 2024 | 10,254 | 337 | 337 |
| 2025 | 9,870 | 159 | 159 |
| Total | 57,416 | 3,278 | 3,240 |

**3,278 events across 179 distinct symbols** have no announcement in the preceding 90 days and cannot be called unexplained. The no-earlier-cache subset spans 174 distinct symbols. Conversely, finding one filing is not a completeness certificate. The old backfill skips any symbol already holding a row (`scripts/ingest_announcements_full_history.py:26-44`), so a partial history can remain partial. Missing historic aliases and the results-route gaps below are additional reasons not to call the rest confirmed covered.

## 5. Surveillance and trading-series history

The store records ASM_LT, ASM_ST and GSM **transitions**, not a complete per-stock daily clear-status ledger. A state may be replayed only from rows whose event_date and knowledge_date are both no later than the assessment day, ordered by event_date, knowledge_date, row_id. The latest ENTRY/STAGE_CHANGE supplies the stage; EXIT supplies a recorded exit. An absent mechanism is not proof of no surveillance (`src/signals/surveillance_state.py:33-57`). No later transitions were used to describe an earlier event.

ASM sourcing was intended to cover October 2019 onward. GSM ingestion deliberately starts January 2025 because earlier circulars require OCR (`docs/phase4_asm_gsm_sourcing.md`, format and ingestion sections; `CLAUDE.md`, Surveillance mechanisms). These are sourcing floors, not proofs that every stock was clear from those dates. Consolidated ASM snapshots were examined during sourcing but not ingested as baseline facts; ingestion chose daily deltas. No complete initial membership plus uninterrupted daily coverage proof was established here. ESM, IBC/ICA and encumbrance are separate excluded mechanisms, so ASM/GSM-clear would not mean free of every exchange restriction.

| Mechanism | Transition rows effective through 2025 | First effective date | Last effective date | First knowledge date | Last knowledge date | Rows learned after 2025 |
|---|---|---|---|---|---|---|
| ASM_LT | 11,432 | 2019-10-03 | 2025-12-31 | 2019-10-01 | 2025-12-30 | 0 |
| ASM_ST | 16,301 | 2019-10-03 | 2025-12-31 | 2019-10-01 | 2025-12-30 | 0 |
| GSM | 125 | 2025-01-22 | 2025-12-24 | 2025-01-21 | 2026-02-10 | 3 |

Three GSM rows effective in 2025 have knowledge dates in February 2026; they are excluded from 2025 point-in-time state. Pre-2025 GSM is unavailable, not clear. The first effective stored GSM transition is 2025-01-22; January 1 is only the source coverage floor, not an observed starting roster.

### ASM_LT evidence at catalogue event dates

| Year | Active from visible transition | Latest visible transition is exit | No visible transition |
|---|---|---|---|
| 2019 | 0 | 0 | 0 |
| 2020 | 315 | 1,431 | 8,165 |
| 2021 | 694 | 3,343 | 4,926 |
| 2022 | 256 | 4,822 | 4,226 |
| 2023 | 311 | 6,172 | 5,413 |
| 2024 | 452 | 5,386 | 4,753 |
| 2025 | 189 | 5,541 | 4,299 |
| Total | 2,217 | 26,695 | 31,782 |

### ASM_ST evidence at catalogue event dates

| Year | Active from visible transition | Latest visible transition is exit | No visible transition |
|---|---|---|---|
| 2019 | 0 | 0 | 0 |
| 2020 | 191 | 3,605 | 6,115 |
| 2021 | 151 | 5,550 | 3,262 |
| 2022 | 168 | 6,188 | 2,948 |
| 2023 | 185 | 8,154 | 3,557 |
| 2024 | 175 | 7,383 | 3,033 |
| 2025 | 108 | 7,229 | 2,692 |
| Total | 978 | 38,109 | 21,607 |

### GSM evidence at catalogue event dates

| Year | Active from visible transition | Latest visible transition is exit | No visible transition |
|---|---|---|---|
| 2019 | 0 | 0 | 0 |
| 2020 | 0 | 0 | 9,911 |
| 2021 | 0 | 0 | 8,963 |
| 2022 | 0 | 0 | 9,304 |
| 2023 | 0 | 0 | 11,896 |
| 2024 | 0 | 0 | 10,591 |
| 2025 | 9 | 32 | 9,988 |
| Total | 9 | 32 | 60,653 |

An exit is evidence of an exit, conditional on subsequent transition coverage; it is not a completeness guarantee. No-visible-transition includes both never-listed securities and missing/unanchored histories. The strict user requirement therefore cannot yet be converted into an exact count of fully known-clear events from this table. All 50,665 pre-2025 events lack GSM coverage; the 10,029 events in 2025 still need a baseline/completeness audit before absent flags may pass screening. This report does not adopt the existing Desk display's empty-state-to-"not under" wording as research evidence.

Series membership is stored on traded dates: EQ from 2019-10-01 through 2025-12-31 on 1,548 dates; BE and BZ over those same endpoints on 1,545 dates each. These are presence spans, not all-day completeness guarantees. The catalogue is EQ-built. For every one of its 60,694 in-scope event symbol-days, an EQ row with knowledge_date <= D exists; none has BE/BZ on that same symbol-day. Other series under the same symbol can represent separate instruments and do not override the EQ security's classification. No bar on a day means unknown series, not normal settlement. The next-session series may differ and has **not** been inferred from D or checked here; future execution screening must establish it independently. No after-event price was used for this membership check.

## 6. Prior outcome exposure: inventory of work already seen

This is an exposure register, not a re-evaluation. "Outcome" below names the measured variable, never its realised value. Repository source/registered methods and the existence of their documented artifacts support this inventory. It cannot certify that no uncommitted/manual analysis ever occurred. Catalogue versions changed with identity, corporate-action and series repairs; old and current event counts need not agree.

Period shorthand: H = historical catalogue from the October 2019 data floor (actual events start in 2020) through 2026-09-15; TRAIN = through 2025-12-31; spent hold-out = 2026-01-01 through 2026-09-15. These are event/decision bounds; earlier forensic horizons could read later bars to form their labels. All are distinct from the protected forward window beginning 2026-09-16. A new A/B/C registration must disclose that 2019-2025 is already outcome-exposed, even though a new 1-3-day strategy definition has not been tested here. No clean-hold-out claim follows merely from changing the horizon.

| Analysis / records | Period | Outcomes already computed or inspected |
|---|---|---|
| Phase 6 signal development: `docs/phase6_signals.md`; `compute_outcome_labels.py`, `compute_outcome_labels_relative.py`, `fit_outcome_ensemble.py` | H; ensemble train through 2024, test 2025-2026, plus pooled fit | Subsequent ASM/GSM entry and lead time; adjusted event-to-30/60/90-session returns; direction-aware reversal across the pre-event 20-session base within 90 sessions; benchmark-relative reversal; feature associations and ensemble prediction. |
| Phase 7b classifier comparisons: `docs/phase7b_classification_design.md`; `measure_collapse_rate_by_class.py`, `analyze_collapse_rate_confidence_intervals.py` | Historical catalogue available before the Phase 8 split (includes 2019-2025 and available 2026) | 30/60/90-session collapse by forensic class and cap band; confidence intervals / class separation. |
| Phase 8 layers 2/3 and ranking follow-ups: `docs/phase8_evaluation_results.md`; `phase8_layer2_metrics.py`, `phase8_layer3_baselines.py`, `phase8_precision_at_k_alternative_orderings.py`, `phase8_baseline3_vs_5_precision_at_k.py` | TRAIN score tables; spent 2026 evaluation | Collapse by class/horizon/band; subsequent flagging; calibration/Brier, precision-at-k and alternative score directions/orderings. Layer 1 factual-claim checks are not an additional forward-return study. |
| Phase 8 robustness: `docs/phase8_robustness_checks.md`; `phase8_robustness_relabel_t0.py`, `phase8_robustness_check1_direction.py`, `phase8_robustness_check1_rescoring.py`, `phase8_robustness_check1_skillscore.py`, `phase8_robustness_check2_baselines.py`, `phase8_robustness_check3_leadtime.py` | TRAIN and spent 2026 | Raw and relative pre-move-base labels; signed event-close-anchored 90-session market-relative return, primary below zero and secondary below -10%; AUC/direction, score tables, precision/lift/Brier skill; flag entry at 20/60/120 sessions and censoring. |
| Phase 8b clean-label feature review: `docs/phase8b_clean_label_features.md`; `phase8b_feature_reauc.py`, `phase8b_momentum_flagrate_check.py` | TRAIN and spent 2026 | Features assessed against event-anchored relative label; momentum versus later exchange flags. This is already disclosed model-selection exposure (P8-001). |
| Phase 10 scoring and procedure preparation: `docs/phase10_preregistration_amendments.md`; `phase10_fit_scoring_function.py`, `phase10_topdecile_lift_mechanism_check.py` | 2019-2025 fit; spent 2026 mechanism check | Relative_t0_primary fit and top-decile lift procedure. This is historical preparation, not the sealed forward evaluation. |
| P8-007 contamination sensitivity: `docs/phase10_p8007_scoping.md`, `docs/phase10_p8007_corrections.md`; `phase10_p8007_sensitivity_reauc.py` | TRAIN and spent 2026 | Clean-label feature AUC sensitivity after identifying non-equities / corporate-action contamination. Universe/shape scans are provenance diagnostics, not separate return strategies. |
| Amendment 4 diagnosis and repairs: `docs/phase10_amendment4_prep.md`, `prep2`, `prep3`, `prep4`; `phase10_amendment4_missing_outcomes.py`, `phase10_amendment4_boundary_diagnosis.py`, `phase10_amendment4_decay_curve.py`, `phase10_amendment4_new_label_check.py`, `phase10_amendment4_phase8b_reauc.py`, `phase10_amendment4_selection_problem.py` | TRAIN and spent 2026; artificial TRAIN truncation 2024-06-30 | 90-session outcome missingness/censoring, label agreement, rename and series bridging, staleness/buffer sensitivity, repaired feature AUCs and selection bias. |
| Amendment 5 preparation: `docs/phase10_amendment5_prep.md`; `phase10_amendment5_bridge_prototype.py`, `phase10_amendment5_measure.py` | TRAIN and spent 2026 | Final EQ/BE/BZ continuity and label availability/selection diagnostics for global-90-session relative outcome. |
| Pinned-label value verification: `docs/desk/label_value_verification.md`; `desk_verify_label.py` | Selected catalogue events in 2020, 2021, 2022, 2024, 2025 | Actual full 90-session relative outcome values compared with pinned Amendment 5 source. Not rerun here. |
| Shadow replay, original and G6-corrected: `docs/desk/shadow_replay_results_pre_g6.md`, `shadow_replay_results.md`, `g6_correction_comparison.md`; `desk_shadow_replay.py`, `desk_g6_comparison.py` | 2019-2025 primary; spent 2026 separately | Signed 90-session relative label/mean; next-session execution and fill cap breaches; adverse20 (low at least 20% below decision close), 20-session maximum adverse excursion, stop gap-through and lower-circuit observations, pass/fail comparisons. |
| Shadow follow-up 1, both pre-G6 and corrected artifacts: `shadow_replay_followup_prereg.md`, `shadow_replay_followup_results_pre_g6.md`, `shadow_replay_followup_results.md`; `desk_shadow_followup.py` | Same shadow periods | Volatility-quintile adverse20 contrasts and standardisation; fill-risk breach sizes and fixed 90% headroom sensitivity. |
| Shadow follow-up 2: `shadow_replay_followup2_prereg.md`, `shadow_replay_followup2_results.md`; `desk_shadow_followup2.py` | Same shadow periods | Next-session open versus decision+0.5 ATR limit execution, fill/no-fill, cap-breach severity and adverse20 among fill cohorts. |
| Shadow follow-up 3: `shadow_replay_followup3_prereg.md`, `shadow_replay_followup3_results.md`; `desk_shadow_followup3.py` | Same shadow periods | Reuses already seen next-session fill evidence to size against limit; cap utilisation/breaches and fill rates. No new return/adverse label, but execution evidence was exposed. |
| T1 market-context evaluations: `t1_development_results_20261018.md`, `t1_holdout_results_2025.md` | 2019-10-01 to 2024-12-31 development; 2025 hold-out, each purged | Actual adverse20 comparisons, volatility standardisation, variant coverage and quintile sign tests. Broad eligible stock-days, not a catalogue-only study, but overlapping stocks/dates are exposed; 2025 is labelled PARTIALLY EXPOSED. Random-label rehearsals are not actual-outcome studies. |

Paths without a directory in the table refer to `scripts/` for Python and `docs/desk/` for shadow/T1 reports. Phase 10 prep2/prep3/prep4 abbreviate `docs/phase10_amendment4_prep2.md`, `docs/phase10_amendment4_prep3.md`, `docs/phase10_amendment4_prep4.md`. `docs/RESULTS.md`, `docs/desk/shadow_replay_summary.md`, review documents and demo presentations repeat prior results rather than establishing untouched samples. The Phase 10 frozen forward experiment and Strategy 0 forward paper outcomes remain sealed; their existence is not permission to read them. No fresh 1-3-session A/B/C outcome study was found in the inspected analysis inventory, and none was run.

## 7. C: why results tags disappear, and repair options

The store-only R2 report correctly left the cause unresolved. Official documentation now establishes filing-route changes. These explain why an announcements-category census cannot substitute for a results-release universe. They do not establish exact missing-release counts or prove archive completeness.

### Stored evidence around the changes

Two results spellings below are Financial Result Updates and Financial Results Updates. Board mentions count only Outcome of Board Meeting descriptions containing the case-insensitive literal phrase `financial result`; they are evidence of routing, not certified first releases. Integrated counts are announcement rows, not the separate structured-results dataset.

| Month | All announcement rows | Two results spellings | Integrated Filing- Financial | Board outcomes mentioning financial results |
|---|---|---|---|---|
| 2022-01 | 8,243 | 539 | 0 | 28 |
| 2022-02 | 10,817 | 1,393 | 0 | 90 |
| 2022-03 | 8,326 | 9 | 0 | 2 |
| 2022-04 | 11,390 | 181 | 0 | 14 |
| 2022-05 | 15,640 | 1,591 | 0 | 154 |
| 2022-06 | 11,342 | 37 | 0 | 5 |
| 2022-07 | 10,963 | 20 | 0 | 96 |
| 2022-08 | 14,491 | 0 | 0 | 218 |
| 2022-09 | 13,083 | 0 | 0 | 4 |
| 2022-10 | 8,787 | 0 | 0 | 85 |
| 2022-11 | 14,043 | 0 | 0 | 223 |
| 2022-12 | 8,610 | 9 | 0 | 3 |
| 2025-01 | 13,376 | 681 | 562 | 55 |
| 2025-02 | 16,754 | 1,420 | 1,543 | 102 |
| 2025-03 | 10,553 | 13 | 22 | 1 |
| 2025-04 | 10,988 | 0 | 18 | 48 |
| 2025-05 | 20,021 | 0 | 130 | 1,357 |
| 2025-06 | 12,211 | 0 | 3 | 41 |
| 2025-07 | 16,094 | 0 | 23 | 677 |
| 2025-08 | 20,195 | 0 | 93 | 1,531 |
| 2025-09 | 16,098 | 0 | 0 | 34 |
| 2025-10 | 11,265 | 0 | 11 | 525 |
| 2025-11 | 16,423 | 0 | 64 | 1,782 |
| 2025-12 | 10,209 | 0 | 0 | 36 |

**2022: strong evidence of a portal-related coverage gap, not a demonstrated rename.** NSE/CML/2022/34 moved financial-results XBRL submissions to the new Digital Portal from 11 July 2022. NSE/CML/2022/58 returned equity announcements and results to NEAPS from 17 December 2022; it distinguishes results-only PDFs in Quick Results from multi-agenda board disclosures filed in both routes. The two main stored tags have their last summer rows on 12 July and resume exactly on 17 December. No such rows appear in the intervening interval. Other announcement traffic and results mentions continue. The alignment supports a route/capture gap in the legacy announcement feed, but does not prove whether omissions arose at the exchange endpoint, during historical ingestion, or both. A new replacement category of sufficient coverage has not been established. Sources: [July circular](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_Circular_08072022_1.pdf), [December circular](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Circular%20for%20filing%20of%20Equity%20announcements%20and%20Financial%20Results%20on%20NEAPS_0.pdf).

**2025: documented route/category change.** NSE/CML/2025/20, dated 2 April, discontinued the legacy Quick Results PDF route and Integrated Filing-Financial PDF announcement route from 1 April. Results PDFs go through Outcome of Board Meeting (type Financial results), while structured submissions use Integrated Filing-Financial XBRL. This matches zero legacy results tags after March and many results-bearing board outcomes. Sparse Integrated announcement rows after March are not a census of the structured integrated filings. Source: [April circular](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_Circular_02042025_0.pdf).

**Capture limitations apply in both eras.** The cache was built from the general per-symbol announcements endpoint; it was not a complete separately reconciled Quick Results / Full Results / Integrated Financial archive. The legacy parser copies `desc` without a category whitelist, so this code does not show a deliberate filter that dropped only these results categories. It can skip records lacking sort_date or seq_id. Historic raw responses are absent, so skipped/never-returned rows cannot be reconstructed from provenance. The symbol-level resume marker is not proof of quarter coverage. Merely renaming all Board Meeting outcomes to results would introduce false releases and duplicate standalone/consolidated/integrated versions.

### Proposed repair, not performed

1. **No-download work:** retain the legacy category, add a separate review inventory for stored descriptions mentioning results in board outcomes and other categories, and record unresolved first-release/quarter/version/timing status. Reconcile by historical security identity where evidence exists; do not use a current alias as proven historic identity. This can recover candidates already cached but cannot restore missing filings or validate the first-public clock.
2. **Download budget required for a complete repair:** inspect the dedicated historic financial-results and integrated-financial listings for the affected quarters, then compare first-release identifiers, reporting quarter, standalone/consolidated status, original/revision status and receipt/dissemination timestamps against the cache. Begin with a bounded pilot spanning the July/December 2022 and March/April 2025 boundaries. Save raw responses/hashes and a dated symbol-quarter coverage ledger, including confirmed empty and failed requests; retrieve attachments only where metadata cannot resolve the identity/period. No current size estimate is defensible before pagination, availability and attachment needs are measured. Seek a separate explicit request/byte/attachment budget before that pilot; the 20-documentation-page allowance does not authorise a data backfill.
3. Preserve every existing row and original knowledge date. Any newly retrieved historical record needs evidence for its historical public timestamp; otherwise retain first observed retrieval and mark earlier availability unknown. Never backfill a guessed publication hour. Register first-release, revision and causal-timing rules only after the sourcing audit is settled, before any new outcome inspection.

C therefore has more than a missing category: a validated quarterly first-release clock and reaction window are still unavailable. No threshold for a strong first reaction was chosen or measured. Daily bars alone cannot distinguish a pre-announcement move from an intraday reaction.

### Documentation access ledger

Three documents opened, one at a time, all on `nsearchives.nseindia.com`; five PDF pages total, below the 20-page-per-site allowance. No company attachment or data endpoint was opened. Search queries used: `site.nseindia.com integrated filing financial results January 2025 single filing system financial results announcements`; `site.nsearchives.nseindia.com 2022 financial results Quick July circular`; and `NSE/CML/2022/34 July digital financial results` restricted to the archive domain. Search-result snippets were used for discovery; unvisited result links were not used as evidence.

1. https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_Circular_02042025_0.pdf (2 pages).
2. https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Circular%20for%20filing%20of%20Equity%20announcements%20and%20Financial%20Results%20on%20NEAPS_0.pdf (1 page).
3. https://nsearchives.nseindia.com/web/sites/default/files/inline-files/NSE_Circular_08072022_1.pdf (2 pages).

## Validation and unresolved limits

Full required suite: `python -m unittest discover -s tests -p "test_*.py"` - **1,049 tests in 234.929 seconds, OK**. The sourcing census asserts unique event keys and uses metadata-only SQL projections; category totals reconcile to the prior R2 bounded inventory. Existing SQLite ResourceWarnings remain unchanged. No new tests or production changes are needed for this documentation-only task.

The report cannot verify causal explanation, complete historic announcement capture, true first-public timestamp semantics, an initial surveillance roster plus uninterrupted history, or next-session execution availability. These are sourcing limits, not failed strategy tests. No strategy verdict, trade list or outcome statistic is produced. Only this document is changed; stores, other documentation, code, registrations, firewall, seal and Windows task remain untouched.
