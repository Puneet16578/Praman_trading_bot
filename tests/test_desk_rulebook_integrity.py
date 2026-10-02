"""Acceptance test 2 + the two integrity bugs flagged in review:
(a) an untracked file must not pass as "clean" (git diff succeeds trivially against nothing);
(b) a hash must be stable across CRLF/LF checkout differences (this checkout has
    core.autocrlf=true, confirmed via `git config --get core.autocrlf`).

git_is_tracked/git_is_clean/require_git_clean_and_tracked take a repo_root precisely so these can
be exercised against a disposable, throwaway git repository -- never this project's own git state.
"""
from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.lib.versioned_config import (
    VersionedConfigError, git_is_clean, git_is_tracked, read_lf_normalized_bytes,
    require_git_clean_and_tracked, resolve_active_version, sha256_lf_normalized,
)
from desk.lib.rulebook import DeskRulebook, load_active_rulebook
from desk.lib.costs import CostConfig, load_active_cost_config


def _run(args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class ThrowawayRepoTestCase(unittest.TestCase):
    def setUp(self):
        # The OS's own temp directory (tempfile's default location), not a path under this repo --
        # a scratch git repo has no reason to live inside (or even near) the project tree at all.
        self.repo = Path(tempfile.mkdtemp(prefix="praman_desk_test_repo_"))
        _run(["git", "init", "-q"], cwd=self.repo)
        _run(["git", "config", "user.email", "test@example.com"], cwd=self.repo)
        _run(["git", "config", "user.name", "Test"], cwd=self.repo)

    def tearDown(self):
        # git marks some object files read-only; shutil.rmtree(ignore_errors=True) alone silently
        # leaves them behind on Windows instead of removing them -- widen permissions first.
        for p in self.repo.rglob("*"):
            if p.is_file():
                p.chmod(0o600)
        shutil.rmtree(self.repo, ignore_errors=True)


class UntrackedFileTest(ThrowawayRepoTestCase):
    def test_untracked_file_is_not_tracked(self):
        f = self.repo / "rulebook.yaml"
        f.write_text("version: v1\n", encoding="utf-8")
        self.assertFalse(git_is_tracked(f, repo_root=self.repo))

    def test_require_git_clean_and_tracked_raises_for_untracked_file(self):
        f = self.repo / "rulebook.yaml"
        f.write_text("version: v1\n", encoding="utf-8")
        with self.assertRaises(VersionedConfigError):
            require_git_clean_and_tracked(f, repo_root=self.repo)

    def test_staged_but_never_committed_file_is_tracked_but_not_clean(self):
        """The exact bug: `git diff --quiet HEAD` alone would call this "clean" (nothing in HEAD
        to differ from an uncommitted addition is not how git diff works -- it DOES report the new
        file as a diff -- but ls-files is what actually proves "tracked" here, since a plain
        untracked file fails ls-files outright; this test confirms the STAGED case specifically:
        tracked (in the index) but still dirty relative to HEAD, since HEAD has nothing for it."""
        f = self.repo / "rulebook.yaml"
        f.write_text("version: v1\n", encoding="utf-8")
        _run(["git", "add", "rulebook.yaml"], cwd=self.repo)
        self.assertTrue(git_is_tracked(f, repo_root=self.repo))
        self.assertFalse(git_is_clean(f, repo_root=self.repo))
        with self.assertRaises(VersionedConfigError):
            require_git_clean_and_tracked(f, repo_root=self.repo)


class CommittedFileTest(ThrowawayRepoTestCase):
    def test_committed_unmodified_file_is_clean_and_tracked(self):
        f = self.repo / "rulebook.yaml"
        f.write_text("version: v1\n", encoding="utf-8")
        _run(["git", "add", "rulebook.yaml"], cwd=self.repo)
        _run(["git", "commit", "-q", "-m", "add"], cwd=self.repo)
        require_git_clean_and_tracked(f, repo_root=self.repo)  # must not raise

    def test_committed_then_modified_file_is_tracked_but_dirty(self):
        f = self.repo / "rulebook.yaml"
        f.write_text("version: v1\n", encoding="utf-8")
        _run(["git", "add", "rulebook.yaml"], cwd=self.repo)
        _run(["git", "commit", "-q", "-m", "add"], cwd=self.repo)
        f.write_text("version: v2\n", encoding="utf-8")
        with self.assertRaises(VersionedConfigError):
            require_git_clean_and_tracked(f, repo_root=self.repo)


class HashStabilityTest(unittest.TestCase):
    def test_crlf_and_lf_versions_of_the_same_content_hash_identically(self):
        scratch_dir = Path(tempfile.mkdtemp(prefix="praman_desk_test_hash_"))
        lf_path = scratch_dir / "_lf.yaml"
        crlf_path = scratch_dir / "_crlf.yaml"
        content = "version: v1\nrisk:\n  x: 1\n"
        try:
            lf_path.write_bytes(content.encode("utf-8"))
            crlf_path.write_bytes(content.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(sha256_lf_normalized(lf_path), sha256_lf_normalized(crlf_path))
            self.assertEqual(read_lf_normalized_bytes(lf_path), read_lf_normalized_bytes(crlf_path))
        finally:
            shutil.rmtree(scratch_dir, ignore_errors=True)
            crlf_path.unlink(missing_ok=True)


class ActiveVersionPointerTest(ThrowawayRepoTestCase):
    def test_resolve_active_version_reads_the_pointer_not_a_hardcoded_name(self):
        versions_dir = self.repo / "rulebook"
        versions_dir.mkdir()
        (versions_dir / "desk_rulebook_v7.yaml").write_text("version: v7\n", encoding="utf-8")
        active = versions_dir / "ACTIVE"
        active.write_text("desk_rulebook_v7.yaml\n", encoding="utf-8")
        _run(["git", "add", "-A"], cwd=self.repo)
        _run(["git", "commit", "-q", "-m", "add"], cwd=self.repo)
        resolved = resolve_active_version(active, versions_dir, repo_root=self.repo)
        self.assertEqual(resolved.name, "desk_rulebook_v7.yaml")


class SchemaValidationTest(unittest.TestCase):
    """Acceptance test 2: invalid values fail validation. load_active_rulebook() wraps exactly this
    validation call in a VersionedConfigError (desk/lib/rulebook.py) -- tested directly here since
    exercising the full git-integrity path too would require a fixture rulebook actually committed
    to THIS repo, which the real v1 deliberately is not yet (STOP 2 has not happened)."""

    def test_out_of_range_value_fails_schema_validation(self):
        import yaml
        from pydantic import ValidationError

        raw = yaml.safe_load(
            "version: v1\ndated: '2026-01-01'\n"
            "risk: {capital_allocated_inr: 100000, risk_per_trade_pct: 250, max_open_risk_pct: 5,\n"
            "       max_per_stock_pct: 10, max_per_sector_pct: 25, monthly_drawdown_brake_pct: 6}\n"
            "liquidity: {max_order_pct_of_adv: 1, stressed_volume_factor: 0.25, max_days_to_exit_stressed: 3}\n"
            "surveillance_exclusions: {exclude_trade_for_trade_series: true, max_asm_stage: null, exclude_gsm: true}\n"
            "behavioural_brakes: {max_g7_overrides_per_month: 2, consecutive_loss_brake_count: 3, stress_loss_lookback_sessions: 252}\n"
            "inference_rules: {thresholds: {}}\n"
            "required_evidence_dimensions: {required: [price]}\n"
            "paper_to_live_criteria: {min_paper_trades: 30, min_paper_trade_days: 90, max_rule_violations: 0}\n"
        )
        with self.assertRaises(ValidationError):
            DeskRulebook.model_validate(raw)

    def test_non_null_max_asm_stage_is_rejected_at_load_time(self):
        """Fixed per review: previously a non-null max_asm_stage would only fail with a
        NotImplementedError raised MID-ASSESSMENT (inside g4_surveillance). Now the schema itself
        rejects it at LOAD time, before any assessment can even start."""
        from pydantic import ValidationError
        from tests.desk_fixtures import make_test_rulebook

        with self.assertRaises(ValidationError):
            make_test_rulebook(surveillance_exclusions={
                "exclude_trade_for_trade_series": True, "max_asm_stage": "ASM_ST I", "exclude_gsm": True,
            })

    def test_missing_required_section_fails_schema_validation(self):
        import yaml
        from pydantic import ValidationError

        raw = yaml.safe_load("version: v1\ndated: '2026-01-01'\n")
        with self.assertRaises(ValidationError):
            DeskRulebook.model_validate(raw)


class RealRulebookAndCostsLoadTest(unittest.TestCase):
    """rulebook v1 and the cost config are now committed and clean (STOP 2 approved) -- both
    loaders must succeed against the REAL files, not a fixture. Superseded the prior
    "must currently refuse because uncommitted" test, which documented a deliberately temporary
    state before either file existed."""

    def test_real_rulebook_loads_and_matches_the_approved_capital_figure(self):
        loaded = load_active_rulebook()
        self.assertEqual(loaded.version_file, (Path(__file__).resolve().parents[1] / 'rulebook/ACTIVE').read_text().strip())
        self.assertIn(loaded.rulebook.version, ('v1', 'v2'))
        self.assertRegex(loaded.sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(loaded.rulebook.risk.capital_allocated_inr, 500000)
        self.assertIsNone(loaded.rulebook.surveillance_exclusions.max_asm_stage)

    def test_real_cost_config_loads_and_matches_the_confirmed_zerodha_rates(self):
        loaded = load_active_cost_config()
        self.assertEqual(loaded.version_file, "costs_india_delivery_v1.yaml")
        self.assertRegex(loaded.sha256, r"^[0-9a-f]{64}$")
        costs = loaded.costs

        for confirmed in (costs.brokerage, costs.depository_charges, costs.securities_transaction_tax,
                          costs.exchange_transaction_charges, costs.sebi_turnover_fee, costs.stamp_duty):
            self.assertEqual(confirmed.status, "CONFIRMED")

        self.assertEqual(costs.brokerage.rate, 0.0)
        self.assertEqual(costs.depository_charges.rate, 15.34)
        self.assertEqual(costs.exchange_transaction_charges.rate, 0.00307)
        self.assertEqual(costs.gst.status, "TO_VERIFY")
        for bucket in costs.slippage_by_liquidity_bucket:
            self.assertEqual(bucket.status, "ASSUMPTION")


if __name__ == "__main__":
    unittest.main()
