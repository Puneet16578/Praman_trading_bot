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

# Scratch git repos live under data/desk/ (already gitignored) so they never risk being committed.
SCRATCH_ROOT = Path(__file__).resolve().parents[1] / "data" / "desk" / "_test_scratch_repos"


def _run(args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class ThrowawayRepoTestCase(unittest.TestCase):
    def setUp(self):
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        self.repo = Path(tempfile.mkdtemp(dir=SCRATCH_ROOT))
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
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        lf_path = SCRATCH_ROOT / "_lf.yaml"
        crlf_path = SCRATCH_ROOT / "_crlf.yaml"
        content = "version: v1\nrisk:\n  x: 1\n"
        try:
            lf_path.write_bytes(content.encode("utf-8"))
            crlf_path.write_bytes(content.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(sha256_lf_normalized(lf_path), sha256_lf_normalized(crlf_path))
            self.assertEqual(read_lf_normalized_bytes(lf_path), read_lf_normalized_bytes(crlf_path))
        finally:
            lf_path.unlink(missing_ok=True)
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


class RealRulebookAndCostsLoaderRefusalTest(unittest.TestCase):
    """The REAL rulebook/cost config in this repo are deliberately left uncommitted until STOP 2
    approval -- so, right now, both loaders must refuse. This test is expected to need updating
    (or removal) once rulebook v1 is actually committed; it documents the current, real state."""

    def test_real_rulebook_currently_refuses_because_it_is_not_yet_committed(self):
        with self.assertRaises(VersionedConfigError):
            load_active_rulebook()

    def test_real_cost_config_currently_refuses_because_it_is_not_yet_committed(self):
        with self.assertRaises(VersionedConfigError):
            load_active_cost_config()


if __name__ == "__main__":
    unittest.main()
