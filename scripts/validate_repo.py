#!/usr/bin/env python3
"""Structural checks for the toolkit: templates, workflows and section READMEs.

Everything here is copy-pasteable by design, so the things worth checking
mechanically are the ones that break silently when copied: an issue form that
GitHub will reject, a workflow with a trigger I do not want, a section with no
README to explain what to take from it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = [
    "skills",
    "agents",
    "rules",
    "workflows",
    "templates",
    "orchestration",
    "tooling",
    "docs",
]

# GitHub issue form element types.
FORM_TYPES = {"markdown", "input", "textarea", "dropdown", "checkboxes"}

# This repo's own CI must stay PR-triggered. A cron cadence that an account
# cannot pay for stops running and looks exactly like nothing being wrong,
# which is why the rule is enforced rather than written down.
ALLOWED_OWN_TRIGGERS = {"pull_request", "workflow_dispatch", "workflow_call"}


def yaml_load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def check_section_readmes() -> list[str]:
    problems = []
    for section in SECTIONS:
        directory = REPO_ROOT / section
        if not directory.is_dir():
            problems.append(f"{section}/: expected section directory is missing")
            continue
        readme = directory / "README.md"
        if not readme.is_file():
            problems.append(f"{section}/: missing README.md")
        elif not readme.read_text(encoding="utf-8").lstrip().startswith("#"):
            problems.append(f"{section}/README.md: must open with a Markdown heading")
    return problems


def check_markdown_headings() -> list[str]:
    problems = []
    for directory in ("templates", "orchestration", "rules", "docs"):
        for path in sorted((REPO_ROOT / directory).rglob("*.md")):
            text = path.read_text(encoding="utf-8").lstrip()
            if text.startswith("---"):
                continue  # frontmatter-carrying file, checked elsewhere
            if not text.startswith("# "):
                rel = path.relative_to(REPO_ROOT).as_posix()
                problems.append(f"{rel}: must open with a level-1 heading")
    return problems


def check_issue_forms() -> list[str]:
    problems = []
    form_dir = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
    for path in sorted(form_dir.glob("*.yml")) + sorted(form_dir.glob("*.yaml")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if path.name == "config.yml":
            continue
        try:
            data = yaml_load(path)
        except yaml.YAMLError as exc:
            problems.append(f"{rel}: not valid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{rel}: issue form must be a mapping")
            continue
        for key in ("name", "description", "body"):
            if key not in data:
                problems.append(f"{rel}: missing required key {key!r}")
        body = data.get("body")
        if not isinstance(body, list) or not body:
            problems.append(f"{rel}: 'body' must be a non-empty list")
            continue
        for index, element in enumerate(body):
            if not isinstance(element, dict) or "type" not in element:
                problems.append(f"{rel}: body[{index}] needs a 'type'")
                continue
            if element["type"] not in FORM_TYPES:
                problems.append(f"{rel}: body[{index}] has unknown type {element['type']!r}")
    return problems


def _trigger_names(on_value) -> list[str]:
    if isinstance(on_value, str):
        return [on_value]
    if isinstance(on_value, list):
        return [str(item) for item in on_value]
    if isinstance(on_value, dict):
        return [str(key) for key in on_value]
    return []


def check_workflows() -> list[str]:
    problems = []
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")) + sorted(
        (REPO_ROOT / "workflows").glob("*.yml")
    ):
        rel = path.relative_to(REPO_ROOT).as_posix()
        try:
            data = yaml_load(path)
        except yaml.YAMLError as exc:
            problems.append(f"{rel}: not valid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            problems.append(f"{rel}: workflow must be a mapping")
            continue
        # PyYAML resolves a bare `on:` key to the boolean True.
        on_value = data.get("on", data.get(True))
        if on_value is None:
            problems.append(f"{rel}: missing 'on' trigger block")
            continue
        triggers = _trigger_names(on_value)
        if not triggers:
            problems.append(f"{rel}: 'on' block declares no trigger")
        if "jobs" not in data or not isinstance(data["jobs"], dict) or not data["jobs"]:
            problems.append(f"{rel}: missing a non-empty 'jobs' block")
        if rel.startswith(".github/workflows/"):
            for trigger in triggers:
                if trigger not in ALLOWED_OWN_TRIGGERS:
                    problems.append(
                        f"{rel}: trigger {trigger!r} is not allowed in this repo "
                        f"(allowed: {sorted(ALLOWED_OWN_TRIGGERS)})"
                    )
        for job_name, job in (data.get("jobs") or {}).items():
            if isinstance(job, dict) and "runs-on" not in job and "uses" not in job:
                problems.append(f"{rel}: job {job_name!r} has neither 'runs-on' nor 'uses'")
    return problems


def main() -> int:
    problems = (
        check_section_readmes()
        + check_markdown_headings()
        + check_issue_forms()
        + check_workflows()
    )
    for problem in problems:
        print(f"FAIL {problem}", file=sys.stderr)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
