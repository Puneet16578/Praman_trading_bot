# Praman demo -- 5-minute interview walkthrough

**Before the interview:**
```
pip install -r requirements-demo.txt
python demo/build_demo_store.py      # rebuild if production has moved on since your last build
powershell -NoProfile -ExecutionPolicy Bypass -File .\demo\run_demo.ps1
```
The launcher passes `--server.address localhost` explicitly and resolves `Home.py`
relative to its own location. From another folder, invoke the launcher's full path
(for example, `powershell -NoProfile -ExecutionPolicy Bypass -File 'D:\Agentic_ai_project\praman\demo\run_demo.ps1'`).
The execution-policy override applies only to that PowerShell process; it does not
change the machine policy. Where local scripts are already permitted, use
`.\demo\run_demo.ps1` directly.
This binds to `localhost` only and opens only
`data/demo/praman_demo.sqlite` -- a truncated copy of the real store, never production, never the
network.

Every example below was run against this project's own real data and verified live this session
(not assumed) -- exact numbers may drift slightly if you rebuild the demo store later, since
weekly ingestion keeps extending the real store up to the same fixed cutoff (2026-09-15).

---

## 1. Home (15 seconds)

Point at the cutoff banner: nothing dated after 2026-09-15 exists in this demo's own copy of the
store, structurally -- not just hidden in the UI. That date is this project's own pre-registered
forward evaluation window; no interim look at it is taken by this demo or anything else.

## 2. Event Browser -- a GROUNDED event (60 seconds)

**Filter tab** -> From/To = 2021-10-27 -> pick **AXISBANK / 2021-10-27 / GROUNDED**.

Point at:
- The classification (**GROUNDED**) and its verbatim limitation note: a substantive disclosure was
  found, but this project does NOT check whether the disclosure's materiality is proportionate to
  the move's size.
- The microstructure signals with their raw OHLC inputs, side by side.
- The disclosure list -- real NSE announcements (a management re-designation, financial results)
  in the 10-session pre-event window.
- The `discriminative_power_note` at the bottom -- rendered on EVERY report, stating the P8-001
  correction plainly: no precision lift over base rate under the corrected label.

## 3. Event Browser -- an UNEXPLAINED_ISOLATED event (30 seconds)

**Filter tab** -> classification = UNEXPLAINED_ISOLATED, From/To = 2020-03-24 -> pick
**GSPL / 2020-03-24**. Contrast with AXISBANK: no disclosure tier gate here, and the
`INDISTINGUISHABLE_PAIR_NOTE` if it's the class this event landed on (GROUNDED and
UNEXPLAINED_ISOLATED are NOT statistically distinguishable by outcome in this project's own
measurement -- say so plainly if asked "so isolated moves are worse?").

## 4. Event Browser -- a move deliberately EXCLUDED, not misjudged (45 seconds)

**Search tab** -> symbol `RELIANCE` -> "Check a specific date" -> **2023-07-20**.

Result: *"RELIANCE on 2023-07-20 is NOT in this project's event catalogue"* plus the reason --
a real `DEMERGER` (the Jio Financial demerger) ex-dated that exact day. The raw close fell 7.8%
that session. **This is the point**: an unadjustable structural break is silently and correctly
absent from the catalogue, never shown with a fabricated adjusted return. Contrast this with the
nearest real catalogued RELIANCE event, 2023-07-10 (unrelated, ten days earlier).

## 5. As-of Guard -- BAJFINANCE 2025 (60 seconds)

Symbol `BAJFINANCE`, price date **2025-01-15**, as-of #1 **2025-04-01**, as-of #2 **2025-07-01**.

Live result:
- **(a) Is the action visible?** as-of #1: 0 rows (the bonus+split wasn't announced yet --
  `knowledge_date` is 2025-04-29). as-of #2: 2 rows (BONUS 4:1 + SPLIT 2:1, both now visible).
- **(b) Does the adjustment apply?** as-of #1: factor **1x**, close **7177.40**. as-of #2: factor
  **10x**, close **717.74** -- the real, publicly verifiable 4:1 bonus x 2:1 split = 10x share
  multiplication, exactly.

Say plainly: knowing an action is coming (crossing `knowledge_date`) and the action actually taking
effect (crossing `event_date`, the ex-date) are two different boundaries -- this page shows both,
separately, because they answer different questions.

## 6. Verifier -- the Adversary catching a tampered claim (60 seconds)

From the AXISBANK report still selected, go to Verifier. Show the claim list with each one's
verification tier (transcription / derivation / window / conclusion_language) and result.

Click into "Tamper with a claim", pick a numeric claim (e.g. `volume_ratio`), override its value,
click **Tamper and re-verify**. Live result: the Adversary's transcription check re-derives the
real value from the store, disagrees with the overridden one, and rejects the claim -- shown with
the exact `cited X, independent recomputation gave Y` finding. Nothing was written anywhere; this
ran on an in-memory copy of the claim.

## 7. Findings -- the headline retraction and the frozen pre-registration (60 seconds)

No live query on this page -- everything here is loaded from committed results.

- The retraction: classifier top-tier precision 90.6% -> 28.6% (n=7, actually below base rate)
  once the raw label's shared anchor is removed; disclosure-tier-alone 78.7% -> 51.1% (exactly its
  own base rate -- zero lift).
- The final, frozen 7-feature AUC table, parsed directly from `docs/RESULTS.md`.
- The frozen forward pre-registration: 4.3% missing-data threshold, the 2026-09-16 to 2027-01-15
  evaluation window, pinned commit, and the plain statement that no forward outcome has existed at
  any point this was written -- the next real evaluation is ~June 2027, and this specification is
  now frozen against further tuning.

## If asked to go off-script

Toggle **"Anonymise symbols"** on Home before re-opening a report -- every symbol and the company
name extracted from its own real disclosure text (e.g. "Axis Bank Limited") are both masked to
`STOCK_A`/`STOCK_B`/etc., for anything you might record.

The Event Browser's filter tab supports any date up to the cutoff, any classification, any cap
band -- there is nothing scripted-only about the four examples above; they were chosen because
they're clean illustrations of one point each, not because the rest of the catalogue is hidden.
