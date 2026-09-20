"""Negative-controlled test for the CLAUDE.md invariant 12 lint (src/agent/banned_terms.py).
Five deliberately constructed violation shapes -- blatant, hedged, split-across-sentences,
implied-by-ranking, rhetorical-question -- each representing a different way a verdict could try
to evade a naive keyword filter.

The result below is reported as "5/5 on self-authored controls," deliberately not as "100%" or
"catch rate" unqualified: these 5 shapes were written by the same person who wrote the detector
they're tested against, so a perfect score is weak evidence the lint generalizes, not strong
evidence it does. InsightForge's own comparable heuristics scored 1/3 and 2/3 on their own
self-authored controls -- a perfect score here is the more suspicious result of the two, not the
more reassuring one, and is labeled accordingly rather than presented as a clean pass.

tests/test_banned_terms_adversarial_evasion.py is the separate, honestly-adversarial follow-up:
sentences written SPECIFICALLY to state a verdict while evading these exact regexes. Its catch
rate (0/5, measured) is reported there and is not blended into this file's self-authored number --
they answer different questions ("does the lint catch what it was designed to catch" vs. "does it
catch what a motivated author would try to sneak past it") and conflating them would overstate
this lint's real robustness.

A separate false-positive suite checks the lint stays clean on CLAUDE.md's own example of
acceptable output and other legitimate factual sentences this project actually renders --
including one that cites a real NSE disclosure category whose name could plausibly collide with a
banned term if the lint were naive (it is not banned by this lint, deliberately -- see
banned_terms.py's module docstring).
"""
from __future__ import annotations
import unittest

from src.agent.banned_terms import is_clean, lint_text

VIOLATION_SHAPES: dict[str, str] = {
    "blatant": "This is a clear case of stock price manipulation.",
    "hedged": "This is likely manipulation, though not certain given the available evidence.",
    "split_across_sentences": "These signals, taken together, point to one explanation. That explanation is manipulation.",
    "implied_by_ranking": "This event scores 9 out of 10 on our suspicion index.",
    "rhetorical_question": "Could this be anything other than manipulation?",
}

CLEAN_TEXTS: list[str] = [
    "Delivery 11% on 14x average volume; no disclosure in preceding 10 sessions.",  # CLAUDE.md's own example
    "Traded quantity was 3.20x the trailing 60-session median traded quantity.",
    "A 'Insider Trading - Others' announcement (seq_id 12345) was disclosed on 2024-01-05, before this event.",
    "ASM stage as of the event date: not under ASM.",
    "Disclosure tier for the 10-session pre-event window: NONE.",
    "Lead time to subsequent surveillance flag: no subsequent flag as of latest data.",
    "The event-day return had a z-score of 3.14 against its trailing 60-session return distribution.",
    "What was the closing price on the event day?",  # genuine open question, no presupposed verdict
]

class BannedTermCatchRateTest(unittest.TestCase):
    def test_catch_rate_across_five_violation_shapes(self):
        results = {shape: bool(lint_text(text)) for shape, text in VIOLATION_SHAPES.items()}
        caught = sum(results.values())
        total = len(results)
        print(f"\nBanned-term lint: {caught}/{total} on SELF-AUTHORED controls ({100*caught/total:.0f}%) --")
        print("  not a general robustness claim; see test_banned_terms_adversarial_evasion.py for")
        print("  the separately-reported catch rate against sentences written to evade this lint.")
        for shape, was_caught in results.items():
            print(f"  {shape:26s} {'CAUGHT' if was_caught else 'MISSED'}")
        # Recorded, not silently assumed: every constructed shape here is expected to be caught by
        # this lint's design (see banned_terms.py's module docstring for how each is targeted). If
        # a future edit to banned_terms.py regresses one of these, this assertion -- not a silent
        # pass-through -- is what catches it. This assertion is a regression guard on THIS lint's
        # own design targets, not a claim that 5/5 here means the lint is robust in general.
        self.assertEqual(caught, total, f"Self-authored catch rate {caught}/{total} -- see per-shape results above.")

    def test_each_shape_individually(self):
        for shape, text in VIOLATION_SHAPES.items():
            with self.subTest(shape=shape):
                self.assertFalse(is_clean(text), f"Shape '{shape}' was not caught: {text!r}")

class BannedTermFalsePositiveTest(unittest.TestCase):
    def test_legitimate_factual_sentences_stay_clean(self):
        for text in CLEAN_TEXTS:
            with self.subTest(text=text):
                violations = lint_text(text)
                self.assertEqual(violations, [], f"False positive on legitimate text: {text!r} -> {violations}")

if __name__ == "__main__":
    unittest.main()
