# 13 October 2026 follow-ups and read-only market data

## A1 - manual time exits

The manual book now follows Strategy 0's order timing: standing stops are checked
across missed sessions, while time exits require an order at the recovery run and
fill only at the following session open. The append-only journal preserves the
order and its session delay; the brief shows pending orders and their delay.
Repeated monitoring cannot replace the frozen order date. The live manual book
has zero trade events, verified read-only; no live journal was changed.

Regression coverage: missed horizon, next-open fill, on-time order followed by
missed runs, stop precedence, gap-through, and duplicate-run safety.
