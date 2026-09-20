#!/usr/bin/env python3
"""Fail if anything that should have stayed private made it into the tree.

This repo is assembled from my own private project configuration, so the
interesting failure mode is not a bug, it is a leak. This check is the
mechanical half of that review: it greps every tracked text file for the
patterns that have actually shown up in drafts.

Run it directly or through pytest. Exit code 0 means the tree is clean.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Two files necessarily contain the patterns themselves: this checker, and the
# test file that proves each rule can fire. Nothing else is ever exempt, and
# the list is asserted in the tests so it cannot quietly grow.
EXEMPT = frozenset(
    {
        Path(__file__).resolve(),
        (REPO_ROOT / "tests" / "test_validators.py").resolve(),
    }
)

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

# Names from the private sources this toolkit was generalised from. They are
# stored as SHA-256 of the lowercased token, never in plaintext, because this
# file is public and a denylist written out in the clear publishes exactly the
# names it exists to keep out. That is not paranoia: the first version of this
# list was plaintext, and it was the only place in the repo where those names
# still appeared.
#
# The trade-off is real and worth stating. A hash list only catches a token it
# has seen; it cannot catch a name nobody thought to add, and it cannot be
# reviewed by reading it. It is a backstop under human judgement, not a
# replacement for it.
#
# To add a name, add the sha256 of its lowercased form:
#   python -c "import hashlib,sys; \
#              print(hashlib.sha256(sys.argv[1].lower().encode()).hexdigest())" NAME
DENIED_TOKEN_HASHES = frozenset(
    {
        "e228188027a6616e1d2ff510d6738917c808497ed7a78197121c1424420fba9b",
        "2fc0631df2ae5e206fedbb9e6b5591b034ea6471b09af7f28a2c92f5f6ae3281",
        "9b6d5ec68fe54006a8ea3f0f2922a57e821916b4927447ea30f6cfa2e134008c",
        "579e21bc066861eddf98503abc397d0a3a469b614c0a94eba49dfb6f2371073e",
        "f2c6f61db7153a0debb204645a4227254169d923b2e0afe112622c4e6d71666d",
        "0194fa79624b7371a8ff856e9c8df499ba502ba10069c95fb81c664aeaaaa487",
        "f4319b43d42723e2a7cb086719d81482567c92a5097957b2c78d673a7aee453f",
        "5d86d506f4f54726d14d3ff3621922e97dfe6124ef8d24a140808107af89a3a2",
        # A canary, so the rule has a red test without publishing a real name.
        # It is the sha256 of the token in tests/test_validators.py's fixture.
        "b606d15cd0e11b3bc4cba25a487251bdf8002d4a667943bd213f0382bd84ed44",
    }
)

TOKEN = re.compile(r"[a-z0-9]+")


def denied_tokens(line: str) -> list[str]:
    """Return the tokens on this line whose hash is on the denylist."""
    hits = []
    for token in TOKEN.findall(line.lower()):
        if hashlib.sha256(token.encode()).hexdigest() in DENIED_TOKEN_HASHES:
            hits.append(token)
    return hits


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
        if path.resolve() in EXEMPT:
            continue
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
            for token in denied_tokens(line):
                findings.append(f"{rel}:{lineno}: name from a private source: {token!r}")
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
