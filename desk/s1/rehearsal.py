"""Seeded synthetic S1 rehearsal. Never reads real post-entry data or availability."""
from contextlib import contextmanager, ExitStack
import hashlib
import sys
import time
from unittest.mock import patch

import numpy as np

from desk.s1.reader import Bar, seal_real_reads, OutcomeReadRefused
from desk.s1.evaluation import evaluate_inputs, evaluate_sensitivities
from desk.s1.inputs import DEV_END

SEED = 20261020


@contextmanager
def outcomes_sealed():
    """Seal S1 and legacy reader aliases, and refuse any database open.

    Captured S1 method aliases are also blocked by the reader's ContextVar.
    No pre-existing real database connection is passed to the synthetic runner.
    """
    import sqlite3
    from shared import sqlite_readonly
    from desk import outcome_firewall
    from desk.t1_outcome import reader as t1_reader
    originals = [sqlite3.connect, sqlite_readonly.open_readonly,
                 outcome_firewall.require_outcome_access, outcome_firewall.evaluate_event,
                 t1_reader.read_adverse20, t1_reader._labels]
    def refuse(*args, **kwargs):
        raise OutcomeReadRefused("Real outcome readers and database opens are sealed during S1 rehearsal.")
    with seal_real_reads(), ExitStack() as stack:
        # Include aliases already imported by older outcome modules.
        for name, module in list(sys.modules.items()):
            if module is None or not name.startswith(("desk.", "scripts.", "src.", "shared.", "tests.", "sqlite3")):
                continue
            for attr, value in list(vars(module).items()):
                if any(value is original for original in originals):
                    stack.enter_context(patch.object(module, attr, refuse))
        yield


def noise(*parts):
    digest = hashlib.sha256(("|".join(map(str, (SEED,)+parts))).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


class SyntheticReader:
    def __init__(self, records):
        self.records = {(r["day"], r["symbol"]): r for r in records}
        self.calls = 0

    def bar(self, event, symbol, day):
        self.calls += 1
        plan = self.records[event, symbol]["plan"]
        rng = noise("bar", event, symbol, day)
        if rng.random() < .01:
            return None
        opening = plan["decision_price"] * max(.1, 1+rng.normal(0, .035))
        high, low = opening*(1+rng.uniform(0, .04)), opening*(1-rng.uniform(0, .04))
        lock = rng.random() < .01
        if lock:
            high = low = opening
        return Bar(opening, high, low, opening, blocks_buy=lock, blocks_sell=lock, dividend=None)

    def market_members(self, event):
        return ["SYNTHETIC_MARKET"]

    def benchmark_open(self, event, symbol, day, fill_day):
        return 100. if day == fill_day else 100*(1+noise("benchmark", event, day).normal(0, .01))

    def market_states(self, event, symbol):
        rng = noise("states", event, symbol)
        return {v: bool(rng.integers(2)) for v in ("V1", "V2", "V3")}


def random_return(row):
    # Same random label across one-change sensitivities for the same trade key.
    return noise("label", row["day"], row["symbol"], row["group"], row["horizon"]).normal(0, .025)


def rehearse(artifact, costs, *, sensitivities=True):
    start = time.perf_counter()
    development = dict(artifact, records=[r for r in artifact["records"] if r["day"] <= DEV_END])
    reader = SyntheticReader(development["records"])
    with outcomes_sealed():
        # Positive proof that the seal is active before any simulated evaluation.
        from desk.s1.reader import RealReader
        try:
            RealReader(None, None, DEV_END, authorized=True).bar("2024-01-01", "A", "2024-01-02")
        except OutcomeReadRefused:
            guard_proof = True
        else:
            raise AssertionError("Real reader seal failed.")
        primary = evaluate_inputs(development, reader, costs, random_labels=random_return)
        variants = (evaluate_sensitivities(development, reader, costs, period="development", random_labels=random_return)
                    if sensitivities else {})
    # Keep coverage and inference mechanics, but no per-stock fake outcomes in a
    # research registry. Any synthetic verdict is explicitly not an S1 result.
    def compact(result):
        return {k: v for k, v in result.items() if k != "records"}
    return dict(kind="SYNTHETIC RANDOM-LABEL REHEARSAL; NOT AN S1 EVALUATION",
        seed=SEED, real_reader_block_verified=guard_proof, real_outcome_reads=0,
        synthetic_bar_calls=reader.calls, elapsed_seconds=time.perf_counter()-start,
        primary=compact(primary), sensitivities={k: compact(v) for k, v in variants.items()},
        limitation="All post-entry bars, missingness, circuits, benchmark paths, market states and net-return labels "
                   "are synthetic. Coverage and usable draws are rehearsal diagnostics, not actual trade counts "
                   "or evidence for S1. No 2025 rehearsal or outcome evaluation performed.")
