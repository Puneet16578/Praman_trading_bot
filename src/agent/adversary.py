"""The Adversary agent -- the point of Phase 7c. Every EvidenceClaim the three specialist agents
produce passes through here before Synthesis ever sees it. A claim that fails ANY check is
dropped from the accepted set and never reaches output; every check's outcome is recorded in
`findings` AND on the claim's own `verification` dict, so a rejected claim is never silently
missing and the report can state exactly which verification each surviving claim received.

Four checks:
  1. conclusion_language -- banned-term lint (CLAUDE.md invariant 12) on the claim's own text.
     Runs on every claim, no exceptions.
  2. window             -- cherry-pick/window check: a claim's declared window must match the
     canonical constant, not one chosen ad hoc to produce a particular tier.
  3. transcription       -- re-run the claim's `verify` closure (the SAME derivation function the
     claim's value came from) and compare to `cited_value`. Proves the claim was copied
     faithfully. This is also how a record-existence claim is checked (verify() returns whether
     the record is still found; cited_value is True).
  4. derivation          -- for a claim whose type has an independently-implemented second
     computation (`derivation_verify`, src/agent/derivation_check.py) AND that was selected by
     the deterministic ~20% seeded sample, recompute the value via that SEPARATE code path
     (plain SQL against raw bhavcopy, never the shared derivation function) and compare within a
     stated tolerance. This is the check transcription cannot do: transcription re-runs the SAME
     function twice, so a bug INSIDE that shared function passes both times; derivation uses a
     genuinely different implementation, so a systematic formula error surfaces here instead of
     propagating consistently through both the claim and its own check.

Claims whose type has no independent derivation implementation yet, or that were not selected by
the sample, are never silently treated as "verified" -- they are marked NOT_APPLICABLE or
NOT_SAMPLED respectively, both in `findings` and in the claim's own `verification` dict, so the
report can say plainly which claims received which tier rather than implying uniform coverage.
"""
from __future__ import annotations

from .banned_terms import lint_text
from .derivation_check import is_sampled_for_derivation, values_agree
from .models import AdversaryFinding, EvidenceClaim
from ..mcp.tools import ROLE_ADVERSARY

class AdversaryAgent:
    ROLE = ROLE_ADVERSARY

    def verify(self, claims: list[EvidenceClaim]) -> tuple[list[EvidenceClaim], list[AdversaryFinding]]:
        accepted: list[EvidenceClaim] = []
        findings: list[AdversaryFinding] = []

        for claim in claims:
            ok = True
            verification: dict[str, str] = {}

            violations = lint_text(claim.text)
            if violations:
                findings.append(AdversaryFinding(claim.claim_id, "conclusion_language", "FAIL",
                    f"Banned-term lint flagged: {[v.matched_text for v in violations]}"))
                ok = False
            else:
                findings.append(AdversaryFinding(claim.claim_id, "conclusion_language", "PASS", "clean"))

            if claim.canonical_window is not None:
                if claim.window_description != claim.canonical_window:
                    findings.append(AdversaryFinding(claim.claim_id, "window", "FAIL",
                        f"claim used window {claim.window_description!r}, canonical is {claim.canonical_window!r}"))
                    ok = False
                else:
                    findings.append(AdversaryFinding(claim.claim_id, "window", "PASS", "matches canonical window"))

            # Tier 1: TRANSCRIPTION -- re-run the SAME derivation function, catches mistranscription
            if claim.verify is not None:
                try:
                    recomputed = claim.verify()
                except Exception as exc:
                    findings.append(AdversaryFinding(claim.claim_id, "transcription", "FAIL",
                        f"verification raised {type(exc).__name__}: {exc}"))
                    verification["transcription"] = "FAIL"
                    ok = False
                else:
                    if recomputed != claim.cited_value:
                        findings.append(AdversaryFinding(claim.claim_id, "transcription", "FAIL",
                            f"cited {claim.cited_value!r}, independent recomputation gave {recomputed!r}"))
                        verification["transcription"] = "FAIL"
                        ok = False
                    else:
                        findings.append(AdversaryFinding(claim.claim_id, "transcription", "PASS",
                            "matches independent recomputation"))
                        verification["transcription"] = "PASS"
            else:
                verification["transcription"] = "NOT_APPLICABLE"

            # Tier 2: DERIVATION -- a SEPARATE implementation from raw bhavcopy, catches a bug in
            # the shared formula itself, which transcription cannot see. Only for claim types with
            # an independent recomputation implemented, and only a seeded sample of those.
            if claim.derivation_verify is None:
                verification["derivation"] = "NOT_APPLICABLE"
                findings.append(AdversaryFinding(claim.claim_id, "derivation", "NOT_APPLICABLE",
                    "no independent derivation implemented for this claim type"))
            elif not is_sampled_for_derivation(claim.claim_id):
                verification["derivation"] = "NOT_SAMPLED"
                findings.append(AdversaryFinding(claim.claim_id, "derivation", "NOT_SAMPLED",
                    "not selected in this report's seeded ~20% derivation sample"))
            else:
                try:
                    independent_value = claim.derivation_verify()
                except Exception as exc:
                    findings.append(AdversaryFinding(claim.claim_id, "derivation", "FAIL",
                        f"independent derivation raised {type(exc).__name__}: {exc}"))
                    verification["derivation"] = "FAIL"
                    ok = False
                else:
                    if not values_agree(claim.cited_value, independent_value):
                        findings.append(AdversaryFinding(claim.claim_id, "derivation", "FAIL",
                            f"cited {claim.cited_value!r}, independent derivation from raw bhavcopy gave {independent_value!r}"))
                        verification["derivation"] = "FAIL"
                        ok = False
                    else:
                        findings.append(AdversaryFinding(claim.claim_id, "derivation", "PASS",
                            "independent derivation from raw bhavcopy agrees within tolerance"))
                        verification["derivation"] = "PASS"

            claim.verification = verification
            if ok:
                accepted.append(claim)

        return accepted, findings
