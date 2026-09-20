#!/usr/bin/env python3
"""Validate the frontmatter of every skill and subagent definition in this repo.

Skills live at ``skills/<dir>/SKILL.md``; subagents live at ``agents/<name>.md``.
Both carry YAML frontmatter, but the allowed keys differ, so they are checked
against separate schemas.

Run it directly (``python scripts/validate_skills.py``) or through pytest.
Exit code 0 means every file passed.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Agent Skills spec: name and description are required, the rest are optional.
SKILL_REQUIRED = {"name", "description"}
SKILL_ALLOWED = SKILL_REQUIRED | {
    "allowed-tools",
    "compatibility",
    "license",
    "metadata",
    "disable-model-invocation",
}

# Claude Code subagent definitions accept a wider, different set.
AGENT_REQUIRED = {"name", "description"}
AGENT_ALLOWED = AGENT_REQUIRED | {
    "tools",
    "disallowedTools",
    "model",
    "permissionMode",
    "mcpServers",
    "hooks",
    "maxTurns",
    "skills",
}

AGENT_MODELS = {"sonnet", "opus", "haiku", "inherit"}

# A description short enough to be useless as a trigger is the most common
# authoring mistake, so there is a floor as well as a ceiling.
MIN_DESCRIPTION = 40
MAX_DESCRIPTION = 1024
MAX_NAME = 64


@dataclass
class Problem:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path.relative_to(REPO_ROOT).as_posix()}: {self.message}"


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_yaml, body). Frontmatter is None when absent."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    return None, text


def check_common(path: Path, meta: dict, expected_name: str | None) -> list[Problem]:
    problems: list[Problem] = []
    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        problems.append(Problem(path, "'name' must be a non-empty string"))
    else:
        if len(name) > MAX_NAME:
            problems.append(Problem(path, f"'name' is longer than {MAX_NAME} characters"))
        if name != name.lower() or " " in name or "_" in name:
            problems.append(Problem(path, f"'name' must be lowercase-hyphenated, got {name!r}"))
        if expected_name is not None and name != expected_name:
            problems.append(
                Problem(path, f"'name' is {name!r} but the file says {expected_name!r}")
            )

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append(Problem(path, "'description' must be a non-empty string"))
    else:
        if len(description) < MIN_DESCRIPTION:
            problems.append(
                Problem(
                    path,
                    "'description' is too short to trigger reliably "
                    f"({len(description)} < {MIN_DESCRIPTION} characters)",
                )
            )
        if len(description) > MAX_DESCRIPTION:
            problems.append(Problem(path, f"'description' exceeds {MAX_DESCRIPTION} characters"))
        if "\n" in description.strip():
            problems.append(Problem(path, "'description' must be a single line"))
    return problems


def check_file(path: Path, kind: str) -> list[Problem]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if frontmatter is None:
        return [Problem(path, "missing YAML frontmatter delimited by ---")]
    try:
        meta = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:  # pragma: no cover - exercised by the bad fixture
        return [Problem(path, f"frontmatter is not valid YAML: {exc}")]
    if not isinstance(meta, dict):
        return [Problem(path, "frontmatter must be a YAML mapping")]

    if kind == "skill":
        required, allowed = SKILL_REQUIRED, SKILL_ALLOWED
        expected_name = path.parent.name
    else:
        required, allowed = AGENT_REQUIRED, AGENT_ALLOWED
        expected_name = path.stem

    problems = check_common(path, meta, expected_name)
    for key in sorted(required - set(meta)):
        problems.append(Problem(path, f"missing required frontmatter key {key!r}"))
    for key in sorted(set(meta) - allowed):
        problems.append(Problem(path, f"unknown frontmatter key {key!r} for a {kind}"))

    if kind == "agent":
        model = meta.get("model")
        if model is not None and model not in AGENT_MODELS:
            problems.append(
                Problem(path, f"'model' must be one of {sorted(AGENT_MODELS)}, got {model!r}")
            )

    if not body.strip():
        problems.append(Problem(path, "body is empty; a definition needs instructions"))
    return problems


def discover(root: Path = REPO_ROOT) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        found.append((skill, "skill"))
    for agent in sorted((root / "agents").glob("*.md")):
        if agent.name.upper() == "README.MD":
            continue
        found.append((agent, "agent"))
    return found


def main() -> int:
    targets = discover()
    problems: list[Problem] = []
    for path, kind in targets:
        problems.extend(check_file(path, kind))
    for problem in problems:
        print(f"FAIL {problem}", file=sys.stderr)
    print(f"checked {len(targets)} definition(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
