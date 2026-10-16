"""Lint rules that `sphinx-build -W` does not catch.

1. Exactly one page title per file: a `*` overline + underline block.
2. A page has at most MAX_LINES lines (list-table syntax costs about 3 lines per cell, so the limit is above the
   250 lines the reading rule is based on).
3. No adornment-looking line of 1-3 characters (docutils silently treats it as text).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"_build", ".venv", "tools"}
MAX_LINES = 450
ADORN = re.compile(r"^([!-/:-@\[-`{-~])\1*$")


def check(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    errs, titles = [], 0
    for i, line in enumerate(lines):
        if not ADORN.match(line):
            continue
        n = len(line)
        if n < 4 and i > 0 and lines[i - 1].strip():
            errs.append(f"{path}:{i + 1}: adornment shorter than 4 chars is read as text")
        is_overline = (
            n >= 4
            and line[0] == "*"
            and i + 2 < len(lines)
            and lines[i + 1].strip()
            and lines[i + 2] == line
        )
        if is_overline:
            titles += 1
    if len(lines) > MAX_LINES:
        errs.append(f"{path}: {len(lines)} lines, limit {MAX_LINES}; split at an H2")
    if path.name != "index.rst" or path.parent != ROOT:
        if titles != 1:
            errs.append(f"{path}: expected 1 '*' page title, found {titles}")
    return errs


def main():
    errs = []
    for p in sorted(ROOT.rglob("*.rst")):
        if SKIP & set(p.relative_to(ROOT).parts):
            continue
        errs += check(p)
    print("\n".join(errs) if errs else "lint ok")
    return 1 if errs else 0


sys.exit(main())
