"""Tests for the validators, plus the validators run against the real tree.

The validators are the only executable thing in this repo, so they get two
kinds of test: unit tests over fixtures that prove each check can actually
fail, and whole-tree runs that prove the checked-in content passes. A checker
that cannot fail is not a checker, so every rule below has a red case.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_sanitization  # noqa: E402
import validate_repo  # noqa: E402
import validate_skills  # noqa: E402


def write_skill(tmp_path: Path, name: str, frontmatter: str, body: str = "Body text.\n") -> Path:
    directory = tmp_path / "skills" / name
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


GOOD_DESCRIPTION = (
    "Use when dispatching parallel work to subagents, writing a brief, or "
    "merging an agent branch."
)


def test_valid_skill_passes(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "orchestrating-agents",
        f"name: orchestrating-agents\ndescription: {GOOD_DESCRIPTION}",
    )
    assert validate_skills.check_file(path, "skill") == []


def test_missing_frontmatter_is_caught(tmp_path: Path) -> None:
    directory = tmp_path / "skills" / "no-frontmatter"
    directory.mkdir(parents=True)
    path = directory / "SKILL.md"
    path.write_text("# Just a heading\n", encoding="utf-8")
    problems = validate_skills.check_file(path, "skill")
    assert any("missing YAML frontmatter" in p.message for p in problems)


def test_name_must_match_directory(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path, "tests-first", f"name: tests-second\ndescription: {GOOD_DESCRIPTION}"
    )
    problems = validate_skills.check_file(path, "skill")
    assert any("but the file says" in p.message for p in problems)


def test_short_description_is_caught(tmp_path: Path) -> None:
    path = write_skill(tmp_path, "thin", "name: thin\ndescription: Does stuff.")
    problems = validate_skills.check_file(path, "skill")
    assert any("too short" in p.message for p in problems)


def test_unknown_skill_key_is_caught(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "extra-key",
        f"name: extra-key\ndescription: {GOOD_DESCRIPTION}\ntools: Read, Grep",
    )
    problems = validate_skills.check_file(path, "skill")
    assert any("unknown frontmatter key 'tools'" in p.message for p in problems)


@pytest.mark.parametrize(
    "model", ["sonnet", "opus", "haiku", "fable", "inherit", "claude-sonnet-4-5-20250929"]
)
def test_valid_agent_models_are_accepted(model: str) -> None:
    assert validate_skills.is_valid_model(model)


@pytest.mark.parametrize("model", ["gpt", "Sonnet", "", 4, None, "claude sonnet"])
def test_invalid_agent_models_are_rejected(model: object) -> None:
    assert not validate_skills.is_valid_model(model)


def test_skill_may_carry_host_extension_keys(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path,
        "host-extras",
        f"name: host-extras\ndescription: {GOOD_DESCRIPTION}\nmodel: sonnet",
    )
    assert validate_skills.check_file(path, "skill") == []


def test_agent_model_is_validated(tmp_path: Path) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    path = agents / "cold-diff-reviewer.md"
    path.write_text(
        f"---\nname: cold-diff-reviewer\ndescription: {GOOD_DESCRIPTION}\n"
        "model: gpt\n---\n\nReview the diff.\n",
        encoding="utf-8",
    )
    problems = validate_skills.check_file(path, "agent")
    assert any("'model' must be one of" in p.message for p in problems)


def test_agent_accepts_tools_and_model(tmp_path: Path) -> None:
    agents = tmp_path / "agents"
    agents.mkdir()
    path = agents / "cold-diff-reviewer.md"
    path.write_text(
        f"---\nname: cold-diff-reviewer\ndescription: {GOOD_DESCRIPTION}\n"
        "tools: Read, Grep, Glob\nmodel: sonnet\n---\n\nReview the diff.\n",
        encoding="utf-8",
    )
    assert validate_skills.check_file(path, "agent") == []


def test_empty_body_is_caught(tmp_path: Path) -> None:
    path = write_skill(
        tmp_path, "hollow", f"name: hollow\ndescription: {GOOD_DESCRIPTION}", body=""
    )
    problems = validate_skills.check_file(path, "skill")
    assert any("body is empty" in p.message for p in problems)


@pytest.mark.parametrize(
    "line",
    [
        r"open C:\Users\someone\project\file.md",
        "see /home/someone/project/",
        "token gh" + "p_0123456789abcdefghijABCDEFGHIJ0123",
        'api_key = "0123456789abcdef"',
        "host 10.24.8.11 is the box",
        "mail me at somebody@somewhere.net",
        "the sanitizercanarytoken dashboard",
    ],
)
def test_sanitization_rules_fire(tmp_path: Path, line: str) -> None:
    path = tmp_path / "leak.md"
    path.write_text(f"# Heading\n\n{line}\n", encoding="utf-8")
    monkey = check_sanitization.REPO_ROOT
    check_sanitization.REPO_ROOT = tmp_path
    try:
        findings = check_sanitization.scan([path])
    finally:
        check_sanitization.REPO_ROOT = monkey
    assert findings, f"expected a finding for: {line}"


@pytest.mark.parametrize(
    "line",
    [
        "use %USERPROFILE%/.claude/settings.json",
        "or ~/.claude/settings.json on macOS and Linux",
        r"copy it to C:\Users\<you>\.claude\settings.json",
        "bind to 127.0.0.1 for local testing",
        "write to noreply@example.com",
    ],
)
def test_sanitization_allows_placeholders(tmp_path: Path, line: str) -> None:
    path = tmp_path / "fine.md"
    path.write_text(f"# Heading\n\n{line}\n", encoding="utf-8")
    monkey = check_sanitization.REPO_ROOT
    check_sanitization.REPO_ROOT = tmp_path
    try:
        findings = check_sanitization.scan([path])
    finally:
        check_sanitization.REPO_ROOT = monkey
    assert findings == [], f"unexpected finding for: {line}"


def test_workflow_trigger_names() -> None:
    assert validate_repo._trigger_names("pull_request") == ["pull_request"]
    assert validate_repo._trigger_names(["push", "schedule"]) == ["push", "schedule"]
    assert validate_repo._trigger_names({"pull_request": {"branches": ["main"]}}) == [
        "pull_request"
    ]


# --- whole-tree runs ---------------------------------------------------------


def test_repo_skills_and_agents_are_valid() -> None:
    problems = []
    for path, kind in validate_skills.discover(REPO_ROOT):
        problems.extend(validate_skills.check_file(path, kind))
    assert problems == [], "\n".join(str(p) for p in problems)


def test_repo_structure_is_valid() -> None:
    problems = (
        validate_repo.check_section_readmes()
        + validate_repo.check_markdown_headings()
        + validate_repo.check_issue_forms()
        + validate_repo.check_workflows()
    )
    assert problems == [], "\n".join(problems)


def test_denylist_is_stored_as_hashes_only() -> None:
    """The denylist must never carry a real name in plaintext.

    This file is public. A denylist written out in the clear publishes exactly
    the names it exists to keep out, which is how the first version of it
    became the only place those names still appeared.
    """
    source = (REPO_ROOT / "scripts" / "check_sanitization.py").read_text(encoding="utf-8")
    assert "BANNED_SUBSTRINGS" not in source
    for digest in check_sanitization.DENIED_TOKEN_HASHES:
        assert len(digest) == 64
        assert all(character in "0123456789abcdef" for character in digest)


def test_denied_token_is_found_anywhere_on_a_line() -> None:
    assert check_sanitization.denied_tokens("path/to/SanitizerCanaryToken-wt/x") == [
        "sanitizercanarytoken"
    ]
    assert check_sanitization.denied_tokens("an ordinary sentence") == []


def test_sanitization_exemptions_are_exactly_two_files() -> None:
    expected = {
        (REPO_ROOT / "scripts" / "check_sanitization.py").resolve(),
        (REPO_ROOT / "tests" / "test_validators.py").resolve(),
    }
    assert set(check_sanitization.EXEMPT) == expected


def test_repo_is_sanitized() -> None:
    findings = check_sanitization.scan(check_sanitization.tracked_files())
    assert findings == [], "\n".join(findings)
