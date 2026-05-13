#!/usr/bin/env python3
"""Offline CI safety gate for the Jiege automation repository.

This script is intentionally conservative:
- it never starts local services;
- it never calls webhooks, n8n, WeCom, uploaders, brokers, or Ollama;
- it only inspects tracked files and compiles selected Python source.
"""

from __future__ import annotations

import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_FILE_BYTES = 50 * 1024 * 1024

EXCLUDED_COMPILE_PARTS = {
    ".venv",
    "venv",
    "env",
    "ENV",
    "virtualenv",
    "site-packages",
    "__pycache__",
    "05备份",
    "06临时",
    "intention_router",
}

EXCLUDED_COMPILE_FILES = {
    "test_local_health.py",
}

TEXT_SUFFIXES = {
    ".py",
    ".ps1",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".md",
    ".txt",
    ".env",
}

REDLINE_TRUE_PATTERNS = [
    re.compile(r"真实发送[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"是否允许真实发送[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发n8n[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发Webhook[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\breal_send\s*=\s*True\b"),
    re.compile(r"\bREAL_SEND\s*=\s*True\b"),
]

FORBIDDEN_CIRCLECI_TERMS = [
    "test_local_health.py",
    "127.0.0.1:19310",
    "webhook",
    "n8n",
    "--real-send",
    "curl ",
    "wget ",
]


def run_git(*args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
    )


def tracked_files() -> list[Path]:
    raw = run_git("ls-files", "-z")
    names = raw.decode("utf-8", errors="replace").split("\0")
    return [ROOT / name for name in names if name]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_circleci_config() -> None:
    config = ROOT / ".circleci" / "config.yml"
    if not config.exists():
        fail(".circleci/config.yml is missing")

    text = config.read_text(encoding="utf-8")
    lower_text = text.lower()
    for term in FORBIDDEN_CIRCLECI_TERMS:
        if term.lower() in lower_text:
            fail(f"CircleCI config contains forbidden term: {term}")

    if "python ci/safe_ci_check.py" not in text:
        fail("CircleCI config must run python ci/safe_ci_check.py")


def check_tracked_file_sizes(paths: list[Path]) -> None:
    offenders: list[str] = []
    for path in paths:
        if path.exists() and path.is_file() and path.stat().st_size > MAX_TRACKED_FILE_BYTES:
            offenders.append(f"{rel(path)} ({path.stat().st_size / 1024 / 1024:.2f} MiB)")

    if offenders:
        fail("tracked files over 50 MiB:\n" + "\n".join(offenders[:20]))


def should_compile(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    relative = path.relative_to(ROOT)
    parts = set(relative.parts)
    if parts & EXCLUDED_COMPILE_PARTS:
        return False
    if path.name in EXCLUDED_COMPILE_FILES:
        return False
    return True


def check_python_compiles(paths: list[Path]) -> None:
    checked = 0
    failures: list[str] = []
    for path in paths:
        if not should_compile(path):
            continue
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # noqa: BLE001 - CI report should keep going.
            failures.append(f"{rel(path)}: {exc}")

    if failures:
        fail("python compile failures:\n" + "\n".join(failures[:30]))

    print(f"Python compile check: {checked} files")


def read_text_safely(path: Path) -> str | None:
    if path.suffix not in TEXT_SUFFIXES:
        return None
    if not path.exists() or path.stat().st_size > 2 * 1024 * 1024:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def check_redline_flags(paths: list[Path]) -> None:
    offenders: list[str] = []
    for path in paths:
        if rel(path) == "ci/safe_ci_check.py":
            continue
        relative = path.relative_to(ROOT)
        if not (
            relative.parts[:1] in [(".circleci",), ("ci",), (".github",)]
            or path.name.lower() in {"circleci.yml", "config.yml"}
        ):
            continue
        text = read_text_safely(path)
        if text is None:
            continue
        for pattern in REDLINE_TRUE_PATTERNS:
            if pattern.search(text):
                offenders.append(f"{rel(path)} matched {pattern.pattern}")
                break

    if offenders:
        fail("redline flags enabled in tracked files:\n" + "\n".join(offenders[:30]))


def main() -> int:
    os.environ.setdefault("JIEGE_CI_SAFE_MODE", "1")
    paths = tracked_files()
    print(f"Tracked files: {len(paths)}")

    check_circleci_config()
    check_tracked_file_sizes(paths)
    check_redline_flags(paths)
    check_python_compiles(paths)

    print("Safe CI checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
