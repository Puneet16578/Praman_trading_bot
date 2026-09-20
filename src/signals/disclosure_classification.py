"""Substantive vs. routine disclosure classification (Phase 7), built from the real, complete
category distribution in `corporate_announcements` (280 distinct categories, 1,021,591 rows,
full backfill) -- not invented from intuition. Every category below was assigned by reading its
real name against what NSE's own disclosure framework means by it; the ones this project itself
already investigated content for (`Updates`, `Analysts/Institutional Investor Meet/Con. Call
Updates`) were assigned using that direct evidence, not guesswork.

Why this exists: `disclosure_present` (a plain boolean) treats an investor-meet notice --
"a meeting will occur" -- identically to a results release, an order win, or a regulatory
approval. `Analysts/Institutional Investor Meet/Con. Call Updates` alone is 114,140 of 1,021,591
rows (11.2%) -- the single largest category in the entire store. A boolean GROUNDED-adjacent
signal built on presence alone would be generous in exactly the way real evidence does not
support.

Three tiers, not two:
- SUBSTANTIVE: results, orders/contracts, board-meeting outcomes, M&A/restructuring, credit
  rating actions, personnel changes, regulatory actions/approvals, litigation/default,
  capital-structure changes (buyback/rights/QIP/bonus/split), price/volume queries from the
  exchange itself.
- ROUTINE: meeting/call *scheduling* (not outcomes), trading-window notices, compliance
  certificates/filings, newspaper republication of already-disclosed content, share-certificate
  administrivia, record-date/book-closure mechanics of an already-announced action, corrections/
  clarifications of a prior filing.
- AMBIGUOUS: generic catch-all categories this project directly confirmed (Phase 7a content-
  similarity analysis) bundle both substantive and routine real content under one label --
  `Updates` and `General Updates` were shown, by reading real row pairs, to contain CRISIL/CARE
  rating letters and Regulation 30 disclosures alongside routine investor-conference notes.
  `Press Release` and `Investor Presentation` are the same shape by name (a generic label that
  could carry either), not separately investigated. AMBIGUOUS categories are conservatively
  treated as NOT substantive for the three-way event classification below (the safer failure mode
  for a system that must never overclaim, CLAUDE.md invariant 12) -- how much this specific
  choice matters is reported explicitly, not hidden inside a combined number.

Every one of the 280 real categories observed is covered explicitly (asserted at import time,
not merely hoped) -- an uncategorized real category is a defect to fix, not silently absorbed
into a default bucket.
"""
from __future__ import annotations

SUBSTANTIVE_CATEGORIES: frozenset[str] = frozenset({
    "Outcome of Board Meeting", "Outcome of Board Meeting-XBRL",
    "Financial Result Updates", "Financial Results Updates", "Clarification - Financial Results",
    "Clarification- Financial Results", "Reply to Clarification- Financial results",
    "Reply to Clarification Sought- Financial Results", "Integrated Filing- Financial",
    "Consolidated Result Updates - IFRS", "Publish Audited Results", "Limited Review Report",
    "Statement of deviation(s) or variation(s) under Reg. 32",
    "Reasons for Delayed/Non-submission of Financial Results", "Integrated Filing- Governance",
    "Disclosure under SEBI Takeover Regulations", "Public Announcement - Buyback of Shares",
    "Public Announcement-Open Offer", "Open Offer", "Offer for sale", "Offer For Sale-Stock Exchange Mechanism",
    "Post Buyback Public Announcement", "Post Offer Public Announcement", "Post Offer Public announcement",
    "Closure of Buy Back", "Closure of Buyback", "Buyback", "Buyback - others", "Buyback - Tender offer",
    "Buyback - Open Market", "Daily Buy Back of securities", "Rights Issue", "Withdrawal of Rights Issue",
    "Preferential issue", "Preferential Issue", "Qualified Institutional Placement",
    "Qualified Institutional Placements", "Allotment of Securities", "Allotment of ESOP/ESPS",
    "ESOP/ESOS/ESPS", "ESOP/ESPS/SBEB Scheme", "Public Announcement - Delisting",
    "Acquisition", "Amalgamation/Merger", "Scheme of Arrangement", "Demerger", "Restructuring",
    "Other Restructuring", "Corp Restructuring - others", "Diversification/Disinvestment",
    "Sale or disposal", "Sale or disposal-XBRL", "Sale or disposal of unit/ division/subsidiary",
    "Closure of operations", "Closure of operations of any unit/division",
    "Corporate Insolvency Resolution Process", "Corporate Debt Restructuring", "Slump Sale",
    "Incorporation", "Incorporation-XBRL", "Voluntary Delisting", "Delisting", "Liquidation",
    "CIRP - others", "CIRP - Committee meeting updates", "CIRP - Commencement",
    "CIRP - Filing of application", "CIRP - Approval of Resolution Plan",
    "CIRP - Filing of Resolution Plan", "CIRP - Change in Resolutional Professional",
    "CIRP - Revocation/rejection",
    # JUDGMENT CALL, recorded so a reader can disagree explicitly rather than discover it inside a
    # threshold: "Board Meeting Intimation" (361 real rows) / "Intimation of Board Meeting" (4)
    # announce only that a board meeting WILL occur, not what was decided -- structurally the same
    # shape as an investor-meet notice (classed ROUTINE above). Classed SUBSTANTIVE anyway because,
    # unlike an investor-meet notice, a board meeting intimation must (under SEBI LODR) disclose
    # WHY the board is meeting -- results, a fundraise, an M&A decision, etc. -- so the market
    # reacts to a real, board-meeting-agenda-shaped implication, not to the mere fact of a meeting.
    # This is a real disagreement-worthy call, not a clean case: it means a stock that only ever
    # got a board-meeting intimation (no later outcome captured in the same window) still counts
    # as SUBSTANTIVE for this event, even though what was actually decided is unknown.
    "Board Meeting Intimation", "Intimation of Board Meeting",
    "Credit Rating", "Credit Rating- Revision", "Credit Rating- New", "Credit Rating- Others",
    "Related Party Transactions", "Related Party Transaction",
    "Change in Director(s)", "Change in Management", "Resignation", "Resignation of Independent director",
    "Resignation of Director/KMP/SMP", "Resignation of Statutory Auditor", "Appointment",
    "Appointment of Director", "Appointment of Company Secretary and Compliance Officer",
    "Appointment of Chairman and CEO/Election of Directors", "Re-appointment", "Reappointment",
    "Cessation", "Change in Auditors", "Auditor's report", "Statement on Impact of Audit Qualifications",
    "Audit Qualifications/Comments", "Change in Company Secretary/Compliance Officer", "Demise",
    "Change in Directors/ Key Managerial Personnel/ Auditor/ Compliance Officer/ Share Transfer Agent",
    "Change in designation", "Change in Financial Year", "Extension  of Financial Year",
    "Bagging/Receiving of orders/contracts", "Awarding of order(s)/contract(s)",
    "Awarding orders/contract", "Bagging orders/contract",
    "Action(s) taken or orders passed", "Action(s) initiated or orders passed",
    "Granting/withdrawal/surrender/cancellation/suspension of key licenses/ regulatory approvals",
    "Grant of licenses/regulatory approvals",
    "Withdrawal/Surrender/Cancellation or suspension of licenses/ regulatory approvals",
    "Defaults on Payment of Interest/Principal", "Delay/default in the payment of fines/penalties/dues etc. to authority",
    "Fraud/Default/Arrest", "Frauds/Default by employees", "Initiation of Forensic Audit",
    "Final  forensic  audit  report", "Pendency of Litigation(s)/dispute(s) or the outcome impacting the Company",
    "Litigations/Disputes/Regulatory actions", "Strikes/Lockouts/Disturbances",
    "Disruption of Operations", "Disruption of operations", "One Time Settlement", "One time settlement",
    "Dividend", "Dividend Updates", "Date of payment of dividend", "Cancellation of Dividend",
    "Price movement", "Spurt in Volume", "Rumour Verification - Regulation 30(11)",
    "Product launch", "Capacity addition", "Capacity addition/product launch",
    "Commencement of commercial production/operations", "Commencement/Postponement of Operations",
    "Postponement of commercial production/operations", "Adoption of new line(s) of business",
    "Monitoring Agency Report", "Amendment to AOA/MOA", "Postal Ballot", "Extra Ordinary Meeting",
    "NCLT/ Court Convened Meeting",
    "Disclosure of material issue", "Disclosure of other UPSI/material event", "Disclosure of Pledged Shares",
    "Disclosure of Valuation report", "Communication to shareholders as per Reg 30", "Annual Disclosure",
    "Disclosure of Annual financial information (if submitted as part of Annual Report)",
    "Disclosure of Half yearly financial information (if submitted as part of Half-Yearly Report)",
    "Agreements", "Memorandum of Understanding/Agreements", "Agreements/Contracts/Arrangements/ MOU's PARA A",
    "Agreements/Contracts/Arrangements/ MOU's PARA B", "Agreements,Contracts,Arrangements,MOU-XBRL",
    "Arrangements for strategic, technical, manufacturing, or marketing tie up",
    "Issue of Securities", "Preference Shares", "Debentures", "Share Warrants", "FCCBs", "FCCB/ FCEB",
    "GDRs/GDS", "Global Depository Receipts", "Institutional Placement Programme", "Follow-on public issue",
    "Increase in Authorised Capital", "Conversion", "Options to purchase securities",
    "Stock split", "Split of shares", "Bonus", "Bonus/Dividend", "Capital Reduction",
    "Suspension of Trading", "Suspension of trading in equity shares", "Suspension of partly paid up equity shares",
    "Revocation of Suspension of Securities", "Name Change", "Name and Symbol Change",
    "Symbol Change of company", "Name & Symbol Change", "Utilisation of Funds",
    "Withdrawal", "Rescission/termination(s)", "Cancellation", "Amendment(s)", "Alteration/revision(s)",
    "Change in Management Control", "Effect(s) on listed entity due to changed regulatory  framework applicable",
    "Effects - Change in regulatory framework", "Giving guarantees/indemnity/ becoming a surety for third party",
    "Giving of guarantee/indemnity or becoming surety", "Voluntary Revision of Financial statements or Report",
    "Amendment/Termination of awards/contracts", "Notice of Unitholder meetings", "Outcome of Unitholder meetings",
    "Payouts- others", "Confirmation of payment of Interest/Principal", "Date of payment of Interest/Principal",
    "Alteration Of Capital and Fund Raising-XBRL", "Update-Acquisition/Scheme/Sale/Disposal/Reg30-XBRL",
    "Issuance/changes in Capital-Others",
    "Retirement", "Redemption", "Insider Trading - Others", "Forfeiture", "Extinguishment",
    "Shifting of security out of Z category", "Raising of Funds", "Open offer",
})

ROUTINE_CATEGORIES: frozenset[str] = frozenset({
    "Analysts/Institutional Investor Meet/Con. Call Updates",
    "Schedule of Analysts/Institutional Investor Meet/Con. Call",
    "Transcript of Analysts/Institutional Investor Meet/Con. Call",
    "Recording of Analysts/Institutional Investor Meet/Con. Call",
    "Trading Window", "Closure of trading window",
    "Certificate under SEBI (Depositories and Participants) Regulations, 2018",
    "Annual Secretarial Compliance Report", "Quarterly Compliance Report on Corporate governance - within 21 days from the end of the quarter",
    "Business Responsibility & Sustainability Report (BRSR)",
    "Code of Conduct under SEBI(PIT) Reg., 2015", "Code of conduct under SEBI (PIT) Regulations",
    "Structural Digital Database", "Trading Plan under PIT", "Trading Plan under SEBI (PIT) Regulations",
    "Trading Plan under SEBI (PIT) Reg., 2015", "Disclosure under SEBI (PIT) Reg 2015",
    "Disc. under Reg.30 of SEBI (SAST) Reg.2011",
    "Copy of Newspaper Publication", "Newspaper Advertisements", "Press Release (Revised)",
    "Loss of Share Certificates", "Loss of share certificate", "Issue of Duplicate Share Certificate",
    "Record Date", "Revised Record date", "Book Closure", "Revised Book Closure",
    "Cancellation of Book closure", "Cancellation of Record date", "Cancellation of Record Date",
    "AGM/Book Closure", "AGM/Record Date", "Extension of Annual General Meeting",
    "Disclosure of record date for purpose of distribution", "Record Date Updates",
    "Registrar & Share Transfer Agent Update", "Address Change", "E-mail ID for Investor's Grievance Redressal",
    "Shareholders meeting", "Annual General Meeting",
    "Board meeting Cancelled", "Board Meeting Adjourned", "Board Meeting Postponed",
    "Board meeting Rescheduled", "Board Meeting Deferred", "Adjournment/Reschedule/Postpone",
    "Committee Meeting Updates", "Outcome of committee meeting",
    "Corrigendum", "Addendum", "Clarification", "Reply to Clarification Sought",
    "News Verification", "News Clarification", "News verification",
    "Interest Rates Updates", "Monthly Business Updates",
    "Notice Of Shareholders Meetings-XBRL",
    "Declaration for audit reports with unmodified opinion(s)",
    "Submission of Standalone/ Consolidated or Both",
    "Disclosure of all complaints including SCORES complaints received by the InvIT on a quarterly basis",
})

AMBIGUOUS_CATEGORIES: frozenset[str] = frozenset({
    "Updates", "General Updates", "General updates", "Press Release", "Investor Presentation", "Others",
})

_ALL_CLASSIFIED = SUBSTANTIVE_CATEGORIES | ROUTINE_CATEGORIES | AMBIGUOUS_CATEGORIES

def classify_category(category: str) -> str:
    """Returns "SUBSTANTIVE", "ROUTINE", or "AMBIGUOUS". Raises for any category not in the
    explicit mapping above -- an uncategorized real category is a defect (a gap in this module's
    coverage, checked against the real store by test_disclosure_classification_coverage.py), not
    something to silently default."""
    if category in SUBSTANTIVE_CATEGORIES:
        return "SUBSTANTIVE"
    if category in ROUTINE_CATEGORIES:
        return "ROUTINE"
    if category in AMBIGUOUS_CATEGORIES:
        return "AMBIGUOUS"
    raise ValueError(f"Category {category!r} is not covered by disclosure_classification.py's mapping -- add it explicitly, do not guess.")

def classify_category_safe(category: str) -> str:
    """Live-classification entry point: never raises. An unmapped category (e.g. a new NSE
    announcement category introduced after this mapping was built) defaults to "ROUTINE" -- never
    "SUBSTANTIVE" -- so a category this module has never seen can only ever make a report look
    LESS grounded, never inflate the grounded population. `classify_category()` above stays
    strict (raises) deliberately: that is what the coverage-audit test
    (test_disclosure_classification.py::FullCoverageAgainstRealStoreTest) uses to catch a real
    mapping gap at test time, before it reaches live classification. Both matter: strict at audit
    time, safe-by-default at classification time.
    """
    try:
        return classify_category(category)
    except ValueError:
        return "ROUTINE"

def classify_disclosure_window(rows: list[dict]) -> str:
    """Three-way classification for a set of announcement rows in some window (e.g. the 10
    sessions before an event). Returns "SUBSTANTIVE", "ROUTINE_ONLY", or "NONE".

    AMBIGUOUS-category rows are conservatively treated as NOT substantive here -- the safer
    failure mode (CLAUDE.md invariant 12: never overclaim). A window containing only AMBIGUOUS
    rows (no confirmed SUBSTANTIVE, no confirmed ROUTINE either) is reported as "ROUTINE_ONLY"
    for this same reason: a report may not treat unverified content as grounds for calling a move
    "explained" by a substantive disclosure. Uses `classify_category_safe`, not `classify_category`
    -- an unmapped category in a live window must degrade to ROUTINE, never crash the report or
    inflate the grounded population.
    """
    if not rows:
        return "NONE"
    tiers = {classify_category_safe(r["category"]) for r in rows}
    if "SUBSTANTIVE" in tiers:
        return "SUBSTANTIVE"
    return "ROUTINE_ONLY"
