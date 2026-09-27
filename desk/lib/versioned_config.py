"""Shared integrity mechanics for the Desk's two version-controlled config files (the rulebook and
the cost model): both must be committed, unmodified, and identified by a hash that is stable
regardless of checkout line-ending settings, because every Desk decision records that hash and
`desk replay` must be able to load the EXACT same content back by it.

Two real bugs this module exists to prevent, found in review before any code was written:

1. `git diff --quiet HEAD -- <file>` succeeds (exit 0, "no diff") for a file that was never
   committed at all -- there is nothing in the index to diff against, so a brand-new, never-added
   rulebook would silently pass a "no uncommitted changes" check. `require_git_clean_and_tracked()`
   also runs `git ls-files --error-unmatch <file>` first, which fails specifically when a path is
   not tracked, closing that gap.

2. This checkout has `core.autocrlf=true` (confirmed: `git config --get core.autocrlf` -> "true"),
   so the SAME committed bytes check out as LF on one machine and CRLF on this one -- hashing
   on-disk bytes directly would give "the same rulebook" two different hashes depending purely on
   checkout settings, breaking replay-by-hash. `.gitattributes` forces `eol=lf` for `rulebook/` and
   `config/` so a fresh checkout is consistent going forward, and `sha256_lf_normalized()` below
   normalizes CRLF->LF before hashing regardless, so a file that was already checked out (or
   hand-edited) with CRLF before that rule existed still hashes identically to its LF form.
"""
from __future__ import annotations
import hashlib
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class VersionedConfigError(RuntimeError):
    """Raised for any integrity failure: untracked, uncommitted, or a validation failure in the
    loaded content. Always a hard refusal -- the Desk does not run assessments against a config it
    cannot prove is exactly what's committed."""


def _run_git(args: list[str], repo_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)


def git_is_tracked(path: Path, repo_root: Path = PROJECT_ROOT) -> bool:
    rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
    result = _run_git(["ls-files", "--error-unmatch", rel], repo_root)
    return result.returncode == 0


def git_is_clean(path: Path, repo_root: Path = PROJECT_ROOT) -> bool:
    """Only meaningful for a tracked file -- an untracked file trivially has no diff against HEAD
    and this function alone would wrongly call that "clean". Callers must check git_is_tracked()
    first; require_git_clean_and_tracked() below does both, in the right order."""
    rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
    result = _run_git(["diff", "--quiet", "HEAD", "--", rel], repo_root)
    return result.returncode == 0


def require_git_clean_and_tracked(path: Path, repo_root: Path = PROJECT_ROOT) -> None:
    """`repo_root` defaults to this project -- overridable so this same, real logic (not a
    reimplementation) can be exercised against a disposable throwaway git repo in tests, without
    ever needing to touch this project's own git state to test "untracked" or "tracked but dirty"."""
    if not path.exists():
        raise VersionedConfigError(f"{path} does not exist.")
    if not git_is_tracked(path, repo_root):
        raise VersionedConfigError(
            f"{path} is not tracked by git. A rulebook/cost-config file must be committed before "
            "the Desk will run against it -- an untracked file passes `git diff` trivially (there "
            "is nothing to diff against), which is exactly the gap this check closes."
        )
    if not git_is_clean(path, repo_root):
        raise VersionedConfigError(
            f"{path} has uncommitted changes. Commit or revert them before running the Desk -- "
            "every decision records this file's hash, and that hash must mean 'the committed "
            "version', never 'whatever happens to be on disk right now'."
        )


def read_lf_normalized_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    return raw.replace(b"\r\n", b"\n")


def sha256_lf_normalized(path: Path) -> str:
    return hashlib.sha256(read_lf_normalized_bytes(path)).hexdigest()


def resolve_active_version(active_pointer_path: Path, versions_dir: Path, repo_root: Path = PROJECT_ROOT) -> Path:
    """Reads a one-line ACTIVE pointer file (e.g. rulebook/ACTIVE containing exactly
    "desk_rulebook_v1.yaml") and resolves it to the real file in `versions_dir`. The pointer file
    itself must also be tracked and clean -- switching which version is active by editing an
    uncommitted ACTIVE file would otherwise bypass the whole point of requiring the rulebook itself
    to be committed."""
    require_git_clean_and_tracked(active_pointer_path, repo_root)
    name = active_pointer_path.read_text(encoding="utf-8").strip()
    if not name:
        raise VersionedConfigError(f"{active_pointer_path} is empty -- it must name exactly one version file.")
    resolved = versions_dir / name
    if not resolved.exists():
        raise VersionedConfigError(f"{active_pointer_path} names {name!r}, but {resolved} does not exist.")
    return resolved
