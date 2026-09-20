"""A separate, honestly-reported catch rate for tests/test_banned_terms.py's 5/5 result.

The original 5 violation shapes (blatant/hedged/split-across-sentences/implied-by-ranking/
rhetorical-question) were authored by the same person who wrote the detector they're tested
against -- a 5/5 catch rate there is "5/5 on self-authored controls," not evidence the lint is
robust in general. InsightForge's comparable heuristics scored 1/3 and 2/3 on their own controls;
a perfect score here is weak evidence on its own, not strong evidence, and is reported as such
(tests/test_banned_terms.py's own docstring/print output now says "self-authored controls",
not "100%").

This suite is the adversarial follow-up: 5 sentences written SPECIFICALLY to state a manipulation
verdict while evading every regex in banned_terms.py -- no DIRECT_TERM word or its variants, no
ranking/scoring language, no rhetorical question. Each one asserts a real verdict a human reader
would recognize as "this is manipulation" stated in a CLAUDE.md-invariant-12-violating way; none
of them use a word this project's lint currently searches for.

The catch rate is reported, not gated. A low score here is not a test failure to fix by loosening
what counts as "caught" -- it is the honest measurement this suite exists to produce. If/when
banned_terms.py is strengthened against these specific evasions, this suite is where that
improvement should be re-measured, not folded back into the self-authored 5/5.
"""
from __future__ import annotations
import unittest

from src.agent.banned_terms import lint_text

ADVERSARIAL_EVASIONS: dict[str, str] = {
    "deceptive_inflation": (
        "Investors were deliberately misled about the true state of this company in order to "
        "inflate its share price artificially."
    ),
    "orchestrated_scheme_euphemism": (
        "This price action bears every hallmark of an orchestrated effort designed to separate "
        "retail investors from their money."
    ),
    "insider_coordination_no_trigger_words": (
        "No genuine business development explains this move; the only plausible account involves "
        "a small group of insiders coordinating trades to move the price in their own favor."
    ),
    "reasonable_person_wrongdoing": (
        "Given everything observed here, a reasonable person would conclude that wrongdoing "
        "occurred."
    ),
    "euphemistic_verdict_via_pattern": (
        "The pattern in this stock's trading is the signature investigators look for when a "
        "company's insiders have engineered a price move for their own benefit."
    ),
}

class AdversarialEvasionCatchRateTest(unittest.TestCase):
    def test_catch_rate_reported_not_asserted(self):
        results = {name: bool(lint_text(text)) for name, text in ADVERSARIAL_EVASIONS.items()}
        caught = sum(results.values())
        total = len(results)
        print(f"\nBanned-term lint ADVERSARIAL EVASION catch rate: {caught}/{total} ({100*caught/total:.0f}%)")
        print("(sentences authored specifically to evade the regex while still stating a verdict --")
        print(" a low number here is the honest finding, not a bug to paper over)")
        for name, was_caught in results.items():
            print(f"  {name:38s} {'CAUGHT' if was_caught else 'EVADED'}")
        # Deliberately no assertion on the rate itself -- see module docstring. The only thing
        # asserted is that the measurement ran and produced a result for every constructed case,
        # so a future refactor that silently drops a case is still caught.
        self.assertEqual(len(results), len(ADVERSARIAL_EVASIONS))

if __name__ == "__main__":
    unittest.main()
