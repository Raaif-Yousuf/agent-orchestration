"""Tests for the PreToolUse hooks in tooling/hooks/.

Each hook is a standalone script with a hyphenated filename (so it can be
copied out of this repo on its own), which means it cannot be imported with
a normal `import` statement. They are loaded here via `importlib` from their
file paths instead.

Every hook gets at least one red case (it denies the thing it exists to
deny) and one green case (it stays silent on ordinary, unrelated commands),
because a hook with no red test is a check that cannot fail.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "tooling" / "hooks"


def _load(module_name: str, filename: str) -> types.ModuleType:
    path = HOOKS_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


block_git_stash = _load("block_git_stash", "block-git-stash.py")
block_agent_dispatch = _load(
    "block_agent_dispatch_in_worktree", "block-agent-dispatch-in-worktree.py"
)
block_recursive_delete = _load("block_recursive_delete", "block-recursive-delete.py")


# ---------------------------------------------------------------------------
# block-git-stash.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "git stash",
        "git stash push",
        "git stash pop",
        "git stash apply",
        "git stash drop",
        "git -C /tmp/repo stash",
        "git --no-pager stash",
        "GIT_PAGER=cat git stash",
        "cd /tmp && git stash",
        "git stash -u",
    ],
)
def test_git_stash_denies_mutating_forms(command: str) -> None:
    assert block_git_stash.verdict(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "git stash list",
        "git stash show",
        "git status",
        "grep 'git stash' notes.md",
        "echo 'never run git stash here'",
    ],
)
def test_git_stash_allows_read_only_and_unrelated(command: str) -> None:
    assert block_git_stash.verdict(command) is None


def test_git_stash_heredoc_body_is_not_a_command() -> None:
    command = "git commit -m \"$(cat <<'EOF'\nfix: ban git stash in the hook\nEOF\n)\""
    assert block_git_stash.verdict(command) is None


# ---------------------------------------------------------------------------
# block-agent-dispatch-in-worktree.py
# ---------------------------------------------------------------------------


@pytest.fixture
def primary_and_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A throwaway git repo with one linked worktree, for exercising the
    real --git-dir vs --git-common-dir divergence rather than mocking it."""
    primary = tmp_path / "primary"
    primary.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=primary, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t"]
        + ["commit", "--allow-empty", "-m", "x", "-q"],
        cwd=primary,
        check=True,
    )
    worktree = tmp_path / "linked-worktree"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "wt-branch", str(worktree)],
        cwd=primary,
        check=True,
    )
    return primary, worktree


def test_dispatch_allowed_from_primary_checkout(primary_and_worktree: tuple[Path, Path]) -> None:
    primary, _worktree = primary_and_worktree
    assert block_agent_dispatch.verdict(str(primary)) is None
    assert block_agent_dispatch.classify(str(primary)) == "primary"


def test_dispatch_denied_from_linked_worktree(primary_and_worktree: tuple[Path, Path]) -> None:
    _primary, worktree = primary_and_worktree
    assert block_agent_dispatch.verdict(str(worktree)) is not None
    assert block_agent_dispatch.classify(str(worktree)) == "linked_worktree"


def test_dispatch_allowed_when_cwd_is_not_a_repo(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "not-a-repo"
    not_a_repo.mkdir()
    assert block_agent_dispatch.verdict(str(not_a_repo)) is None
    assert block_agent_dispatch.classify(str(not_a_repo)) == "unknown"


def test_dispatch_explain_reports_three_way_split(primary_and_worktree: tuple[Path, Path]) -> None:
    primary, worktree = primary_and_worktree
    assert "PRIMARY CHECKOUT" in block_agent_dispatch.explain(str(primary))
    assert "LINKED WORKTREE" in block_agent_dispatch.explain(str(worktree))


# ---------------------------------------------------------------------------
# block-recursive-delete.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf .scratch",
        "rm -fr .scratch/",
        "rm -r -f .scratch",
        "rm --recursive --force .scratch",
        "Remove-Item -Recurse -Force .scratch",
        "Remove-Item -Recurse -For .scratch",  # PowerShell prefix matching
        "ri -r -fo .scratch",
        "rd .scratch -Recurse -Force",
    ],
)
def test_recursive_delete_denies_relative_repo_paths(command: str) -> None:
    assert block_recursive_delete.verdict(command) is not None


@pytest.mark.parametrize(
    "command",
    [
        "rm .scratch/one_file.log",
        "rm -r .scratch",  # recursive but not forced: git prompts, this hook lets it through
        "git clean -fdx",
        "echo 'do not rm -rf .scratch'",
    ],
)
def test_recursive_delete_allows_targeted_or_non_matching_commands(command: str) -> None:
    assert block_recursive_delete.verdict(command) is None


def test_recursive_delete_allows_paths_outside_the_repo(tmp_path: Path) -> None:
    outside = tmp_path / "genuinely-outside"
    command = f"rm -rf {outside.as_posix()}"
    assert block_recursive_delete.verdict(command) is None


def test_recursive_delete_heredoc_body_is_not_a_command() -> None:
    command = "git commit -m \"$(cat <<'EOF'\nfix: never rm -rf .scratch again\nEOF\n)\""
    assert block_recursive_delete.verdict(command) is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
