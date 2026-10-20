# Operational defect gate: 21 October 2026

Read-only review first; then only P8-088's severity heading was corrected as
instructed by the user. No severity, status, gate code or stored event changed.
The start tree was clean at 6a4f7ea. Ingestion task Ready, last run 20 October
22:00, result 0; no competing Python/Claude process found. Session-start suite:
`Ran 1109 tests in 230.794s`, `OK`, Python exit 0. Existing ResourceWarnings remain.

## Rule and implementation, quoted

`docs/desk/TRADING_BLUEPRINT.md`, section 6.3:

> Critical unresolved defect | Operational gate fails

`desk/automation/kill_switches.py`:

```python
# OPERATIONAL_GATE_FAIL: an open high-severity or critical defect (the readiness gate also fails).
def open_critical_defect(high, unclassified):
    return Trip('OPEN_CRITICAL_DEFECT', bool(high or unclassified),
                dict(open_high_or_critical=list(high), unclassified_open=list(unclassified)))
```

`desk/readiness.py:open_defects`, section-based severity parsing:

```python
if not found or not (re.search(r'\(open\)', section.splitlines()[0], re.I)
                     or re.search(r'\*\*Status\.\*\*\s*Open', section, re.I)):
    continue
severity = re.search(r'\*\*Severity\.\*\*\s*(High|Critical|Medium|Low)', section, re.I)
if severity and severity[1].lower() in ('high','critical'):
    high.add(found[1])
elif not severity:
    unknown.add(found[1])
return sorted(high - closed), sorted(unknown - closed)
```

The same function also scans register table rows for open/not-fixed/deferred
High/Critical entries, and subtracts explicitly closed IDs. The readiness check is:

```python
'open_high_severity_defects': check(high, op.max_open_high_severity_defects,
    len(high) <= op.max_open_high_severity_defects and not unclassified)
```

## P8-088 entry before correction, quoted in full

> ## P8-088 - Test suite emits unclosed SQLite connection ResourceWarnings
>
> **Severity / priority.** Low. **Status.** Open, logged 2026-10-18 at the user's request.
> The full suite at `dea07c7` passed 1,029 tests in 231.224 seconds (exit 0), but Python
> 3.13 emitted `ResourceWarning: unclosed database in <sqlite3.Connection ...>`.
> Warnings surfaced during garbage collection in unittest.mock, bitemporal guards,
> Desk schema/fixtures and other modules. Those locations do not establish where
> each connection was opened; exact owners remain untraced. No failing assertion
> or demonstrated durable-store damage. Investigate test-fixture connection cleanup
> in a later task. No fix, warning suppression or rerun performed for this item.

The heading now reads `**Severity.** Low.`. This makes the existing documented
severity readable; it does not resolve the connection-warning defect.

## Before/after pure, read-only gate check

Called only `open_defects(Path('docs/DEFECT_REGISTER.md'))` and
`open_critical_defect(high, unknown)`; no nightly, readiness outcome calculation,
switch logging, reset or store mutation.

| Check | Before | After P8-088 heading correction |
|---|---|---|
| Classified open High/Critical | none | none |
| Unclassified open | P8-088, P8-094 | P8-094 |
| Defect trip triggered | true | true |

**The whole gate does not clear.** P8-094 has the same combined heading and is
documented High: the shared firewall's date-only release is weaker than D7.
Even correctly parsing its High severity would keep the defect gate active.
No other entry was changed. P8-099 remains open because the general parser issue
and P8-094 classification remain; only P8-088's contribution has been removed.
A claim that this one-line fix clears the whole operational gate would be false.
This check concerns the defect component, not every operational-readiness criterion.

## First activation and affected sessions

All available normal briefs through 14 October say `clear (never triggered)`.
The 19 October brief first says:

> OPEN_CRITICAL_DEFECT: ACTIVE -> OPERATIONAL_GATE_FAIL (last TRIGGERED 2026-10-19; {"open_high_or_critical": [], "unclassified_open": ["P8-088"]})

The unsealed switch record confirms 19 October, recorded at 18:41:24.991327 IST.
No earlier trigger appears in the stored switch history. There are no 15/16 October
briefs; the ingestion log and strategy gaps attribute those skips to battery power.

**Sessions blocked from Strategy 0 decisions by this gate: none evidenced.**
The active effect is not in `BLOCKS_ENTRIES`, whose values are `NO_NEW_TRADES`,
`FREEZE_ENTRIES`, and `DISABLE_AUTO_ENTRIES`. Strategy 0 filters entry blockers
through that set. Its 19 October run has `entry_blocked_by=[]`, 37 candidates,
2 accepted and 35 rejected for `OPEN_RISK_BUDGET`. The 14 October run has
46 candidates, 0 accepted and 46 rejected for the same budget reason.
The gate fails operational readiness; it did not block those paper decisions.
No change to this behavior was requested or made. The persisted active switch
was not rewritten by the pure check.

Validation after the heading change is recorded in this item's commit message.
No S1 evaluation or sealed Strategy 0 outcome payload was read.
