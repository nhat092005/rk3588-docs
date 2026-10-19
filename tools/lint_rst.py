"""Lint rules that `sphinx-build -W` does not catch.

1. Exactly one page title per file: a `*` overline + underline block.
2. A page has at most MAX_LINES lines (list-table syntax costs about 3 lines per cell, so the limit is above the
   250 lines the reading rule is based on).
3. No adornment-looking line of 1-3 characters (docutils silently treats it as text).
4. Sidebar depth is at most MAX_DEPTH: sphinx_rtd_theme with navigation_depth 3 hides deeper pages.
5. Page titles are unique across the site.
6. Content rules (report only until STRICT_CONTENT is True, which is set once the pages are rewritten): no bold-only
   line standing in for a heading, no TBD or checkbox outside the status sections, no tmp/ path, no numbered anchor.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"_build", ".venv", "tools"}
MAX_LINES = 650
MAX_DEPTH = 3
STRICT_CONTENT = False
# dac-ta-bang is exempt only until its pages are rewritten (they hold the old [TBD] cells); then drop it from this list
STATUS_DIRS = ("contents/08-tien-do", "contents/02-phuong-phap/03-dac-ta-bang", "contents/03-ket-qua")
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


def pages():
    return [p for p in sorted(ROOT.rglob("*.rst")) if not SKIP & set(p.relative_to(ROOT).parts)]


def title_of(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    for i in range(len(lines) - 2):
        if re.fullmatch(r"\*{4,}", lines[i]) and lines[i + 2] == lines[i] and lines[i + 1].strip():
            return lines[i + 1].strip()
    return None


def toctree_entries(path):
    """Yield doc paths (relative to ROOT, no suffix) listed in the toctrees of one file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == ".. toctree::":
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith("   ")):
                e = lines[i].strip()
                if e and not e.startswith(":"):
                    m = re.search(r"<([^>]+)>$", e)
                    e = m.group(1) if m else e
                    base = ROOT if e.startswith("/") else path.parent
                    yield (base / e.lstrip("/")).resolve().relative_to(ROOT)
                i += 1
        else:
            i += 1


def depth_errors():
    errs, depth, queue = [], {}, [(ROOT / "index.rst", 0)]
    while queue:
        doc, d = queue.pop(0)
        for e in toctree_entries(doc):
            f = ROOT / (str(e) + ".rst")
            if not f.exists():
                continue
            if f in depth:
                continue
            depth[f] = d + 1
            queue.append((f, d + 1))
    for f, d in depth.items():
        if d > MAX_DEPTH:
            errs.append(f"{f.relative_to(ROOT)}: sidebar depth {d}, limit {MAX_DEPTH}")
    return errs


def title_errors():
    seen, errs = {}, []
    for p in pages():
        t = title_of(p)
        if t is None:
            continue
        if t in seen:
            errs.append(f"{p.relative_to(ROOT)}: title {t!r} also used by {seen[t]}")
        seen[t] = p.relative_to(ROOT)
    return errs


BOLD_ONLY = re.compile(r"^\*\*[^*]+\*\*:?\s*$")
NUM_ANCHOR = re.compile(r"^\.\. _\d+[\w-]*:\s*$")


def content_findings():
    out = {"bold-only heading": 0, "TBD or checkbox outside status": 0, "tmp/ path": 0, "numbered anchor": 0}
    for p in pages():
        rel = str(p.relative_to(ROOT))
        for line in p.read_text(encoding="utf-8").splitlines():
            if BOLD_ONLY.match(line):
                out["bold-only heading"] += 1
            if ("TBD" in line or "\u2610" in line or "\u2611" in line) and not rel.startswith(STATUS_DIRS):
                out["TBD or checkbox outside status"] += 1
            if "tmp/" in line:
                out["tmp/ path"] += 1
            if NUM_ANCHOR.match(line):
                out["numbered anchor"] += 1
    return out


def main():
    errs = []
    for p in pages():
        errs += check(p)
    errs += depth_errors() + title_errors()
    found = content_findings()
    if STRICT_CONTENT:
        errs += [f"{k}: {n}" for k, n in found.items() if n]
    elif any(found.values()):
        print("content findings (not enforced yet): " + ", ".join(f"{k} {n}" for k, n in found.items()))
    print("\n".join(errs) if errs else "lint ok")
    return 1 if errs else 0


sys.exit(main())
