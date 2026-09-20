#!/usr/bin/env python3
"""Fail if anything that should have stayed private made it into the tree.

This repo is assembled from my own private project configuration, so the
interesting failure mode is not a bug, it is a leak. This check is the
mechanical half of that review: it greps every tracked text file for the
patterns that have actually shown up in drafts.

Run it directly or through pytest. Exit code 0 means the tree is clean.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SELF_PATH = Path(__file__).resolve()

TEXT_SUFFIXES = {
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".py",
    ".sh",
    ".ps1",
    ".txt",
    ".toml",
    ".cfg",
    ".jq",
    "",
}

# (label, compiled pattern). Every pattern is deliberately narrow: a rule that
# fires on ordinary prose gets disabled, and a disabled rule guards nothing.
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "absolute Windows user path",
        re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!<)[A-Za-z0-9._-]+", re.IGNORECASE),
    ),
    (
        "absolute Unix home path",
        re.compile(r"/(?:home|Users)/(?!<|USER>)[a-z][a-z0-9._-]{2,}/"),
    ),
    (
        "private token or key",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}"
            r"|sk-(?:ant-)?[A-Za-z0-9_-]{20,}"
            r"|AKIA[0-9A-Z]{16}"
            r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
        ),
    ),
    (
        "hardcoded secret assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*"
            r"['\"][A-Za-z0-9/+_-]{12,}['\"]"
        ),
    ),
    (
        "bare IPv4 address",
        # Loopback and the documentation ranges are fine; anything else is a host.
        re.compile(
            r"(?<![\w.])(?!127\.0\.0\.1|0\.0\.0\.0|255\.255\.255\.255"
            r"|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![\w.])"
        ),
    ),
    (
        "personal email address",
        re.compile(
            r"(?i)\b[A-Za-z0-9._%+-]+@"
            r"(?!example\.(?:com|org)\b|users\.noreply\.github\.com\b)"
            r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
    ),
]

# Names and strings from the private sources this toolkit was generalised from.
# They must never appear. Kept lowercase; matching is case-insensitive.
BANNED_SUBSTRINGS = [
    "clairanalytics",
    "ignatiusnocturne",
    "abako",
    "classwiz",
    "onrender.com",
    "trusted_signing",
    "r2_libpack",
]


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths = [REPO_ROOT / name for name in out.split("\0") if name]
    return [p for p in paths if p.suffix.lower() in TEXT_SUFFIXES and p.is_file()]


def scan(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if path.resolve() == SELF_PATH:
            continue  # this file necessarily contains the patterns themselves
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "sanitization-allow" in line:
                continue
            for label, pattern in RULES:
                match = pattern.search(line)
                if match:
                    findings.append(f"{rel}:{lineno}: {label}: {match.group(0)!r}")
            lowered = line.lower()
            for banned in BANNED_SUBSTRINGS:
                if banned in lowered:
                    findings.append(f"{rel}:{lineno}: private source name: {banned!r}")
    return findings


def main() -> int:
    paths = tracked_files()
    findings = scan(paths)
    for finding in findings:
        print(f"FAIL {finding}", file=sys.stderr)
    print(f"scanned {len(paths)} file(s), {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
