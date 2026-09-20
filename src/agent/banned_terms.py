"""CLAUDE.md invariant 12 enforcement: "NEVER STATE A CONCLUSION ABOUT MANIPULATION." This module
is the mechanical lint every piece of report text (every EvidenceClaim.text, every Synthesis
section) passes through before it can reach output -- a failed line is dropped/rejected, never
silently rendered anyway.

Design note, stated so it isn't rediscovered by a future false-positive report: hedging a banned
term does NOT neutralize it. "This is likely manipulation" still states the banned conclusion --
CLAUDE.md's own example ("Delivery 11% on 14x average volume; no disclosure in preceding 10
sessions" is fact, "This is a pump" is defamation) draws the line at whether a verdict is stated
at all, not at how confidently it's stated. This lint therefore has no hedge-word carve-out, by
design -- a hedge is caught by the same substring/word-boundary check as a blatant statement.

Four detectors, covering five known evasion shapes (negative-controlled by
tests/test_banned_terms.py, which records the catch rate rather than assuming 100%):
  1. DIRECT_TERM_PATTERNS  -- catches "blatant" and "hedged" shapes (the banned word/phrase is
     present regardless of hedging), and "split-across-sentences" (the check scans the whole
     text, not sentence-by-sentence, so splitting a banned phrase's context across a sentence
     boundary does not evade it as long as the term itself appears intact).
  2. RANKING_PATTERNS      -- catches "implied-by-ranking": a verdict implied via a score/rank/
     rating against a suspicion-shaped axis, with no banned noun anywhere in the text.
  3. RHETORICAL_PATTERNS   -- catches "rhetorical-question": a verdict implied by a question whose
     only sensible answer is the banned conclusion, rather than a direct assertion of it.
This is a mechanical lint over English text, not a semantic understanding of the sentence -- it is
expected to have both false negatives (a sufficiently indirect phrasing) and, rarely, false
positives (a legitimate factual sentence that happens to use a flagged word in a different sense).
Both are recorded, not assumed away: see tests/test_banned_terms.py's explicit false-positive
checks against CLAUDE.md's own "acceptable fact" examples.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

DIRECT_TERMS = (
    "manipulation", "manipulated", "manipulative", "manipulating",
    "pump and dump", "pump-and-dump", "pump & dump",
    "fraud", "fraudulent", "defrauding",
    "scam", "scheme to defraud",
    "rigged", "rigging",
    "ponzi",
)
DIRECT_TERM_PATTERNS = [re.compile(r"\b" + re.escape(t).replace(r"\ ", r"[\s-]+") + r"\b", re.IGNORECASE)
                        for t in DIRECT_TERMS]

# "Scores/ranks/rates ... suspicion/manipulation-shaped axis" without necessarily using a banned
# noun on its own -- e.g. "scores 9/10 on our suspicion index" contains no DIRECT_TERM match but
# still asserts a manipulation-shaped verdict via quantified ranking.
RANKING_PATTERNS = [
    re.compile(r"\b(scores?|ranks?|rated?|rating)\b[^.?!]{0,40}\b(suspicio\w*|manipulat\w*|fraud\w*)\b", re.IGNORECASE),
    re.compile(r"\b(suspicio\w*|manipulat\w*|fraud\w*)\b[^.?!]{0,40}\b(index|score|rank|rating)\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}\s*(?:out of|/)\s*10\b[^.?!]{0,40}\b(suspicio\w*|manipulat\w*|fraud\w*|risk)\b", re.IGNORECASE),
]

# A question whose only sensible reading asserts the banned conclusion -- "could this be anything
# other than X" / "what else could this be but X" / a direct "is this X?" -- distinct from a
# genuine open question (those don't presuppose the answer).
RHETORICAL_PATTERNS = [
    re.compile(r"\bcould\s+(?:this|it)\s+be\s+anything\s+other\s+than\b[^.?!]{0,60}\?", re.IGNORECASE),
    re.compile(r"\bwhat\s+else\s+could\s+(?:this|it)\s+be\s+but\b[^.?!]{0,60}\?", re.IGNORECASE),
    re.compile(r"\b(?:is|isn'?t)\s+(?:this|it)\s+(?:not\s+)?(?:clearly\s+)?(?:manipulat\w*|a\s+scam|a\s+fraud|a\s+pump[\s-]+and[\s-]+dump)\b[^.?!]*\?", re.IGNORECASE),
]

@dataclass(frozen=True)
class LintViolation:
    detector: str    # "direct_term" / "ranking" / "rhetorical"
    matched_text: str
    span: tuple[int, int]

def lint_text(text: str) -> list[LintViolation]:
    """Returns every violation found in `text` (empty list if clean). Scans the WHOLE string, not
    per-sentence -- deliberate, see module docstring's "split-across-sentences" note."""
    violations: list[LintViolation] = []
    for pattern in DIRECT_TERM_PATTERNS:
        for m in pattern.finditer(text):
            violations.append(LintViolation("direct_term", m.group(0), m.span()))
    for pattern in RANKING_PATTERNS:
        for m in pattern.finditer(text):
            violations.append(LintViolation("ranking", m.group(0), m.span()))
    for pattern in RHETORICAL_PATTERNS:
        for m in pattern.finditer(text):
            violations.append(LintViolation("rhetorical", m.group(0), m.span()))
    return violations

def is_clean(text: str) -> bool:
    return not lint_text(text)
