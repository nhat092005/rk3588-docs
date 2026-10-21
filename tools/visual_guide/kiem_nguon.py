#!/usr/bin/env python3
"""Kiem nguon: check every row of the `## Nguon` table of <topic>/NN-*/chu-thich.md against the primary source.

Row format: | Hinh | Noi dung | Tier | Nguon | Nguyen van ngan |
Nguon forms (page numbers are PDF page indexes, the value of pdftotext -f; NO printed-page offset is applied):
  TRM1 tr.1984                 any PDF abbreviation + tr.N   (pdftotext, plain and -layout)
  DRV rknpu_job.c:508-538      file found recursively under 3rdparty/rknpu-driver-0.9.8/, lines a-b
  DTS dong 3478 | SRAM dong 21 | HDR dong 10-20 | OPSUP dong 5 | FIXTURE dong 1-30     text files, lines a-b
  RKNNPY rknn/api/rknn.py:56-58   file read from inside the toolkit wheel (zipfile)
  ULT nn/modules/block.py:123  file under .venv/lib/python3.12/site-packages/ultralytics/, lines
  UDOC <file>[:a-b]            html/txt in docs/_assets/pdf/papers/09_yolo_architecture/ (html tags stripped)
  REPO <path>[:a-b]            any repo file (ai/..., tmp/02_decisions/..., tests/...); PDF: REPO <path.pdf> tr.N
  RUN <run_id>/<file>[:a-b]    file under ai/automation/runs/
  LOG <dir>/<file>[:a-b]       file under tmp/04_debug-logs/ (whole file unless lines are given)
Several sources may be joined with "; " (the snippet must occur in at least one).
Verbatim cell `(so hoc)` or `(doc tu hinh)` -> MANUAL; `(unknown)` -> UNKNOWN (absence claim, no text to find).
A literal "|" inside a cell is written as "\\|".

Usage:
  python3 kiem_nguon.py [topic_dir ...]   default: every topic dir under docs/tools/visual_guide with NN-*/chu-thich.md
  python3 kiem_nguon.py --check-map       print every abbreviation and whether its path exists
Exit code 1 if any FAIL (or any missing path with --check-map).
"""
import glob
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
# ROOT = main repo root. This folder lives at <ROOT>/docs/tools/visual_guide (docs repo mounted as submodule at docs/).
ROOT = os.environ.get("RK3588_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
P = "docs/_assets/pdf/papers/"
SDK = "3rdparty/rknn-toolkit2/doc/"

# --- PDF sources, cited as "<KEY> tr.N". Same abbreviations as docs/npu_study/00_index.md sections 0 and 7.
PDFS = {
    "TRM1": "docs/_assets/pdf/datasheet/trm/rk3588_part1.pdf",
    "TRM2": "docs/_assets/pdf/datasheet/trm/rk3588_part2.pdf",
    "DS": "docs/_assets/pdf/datasheet/soc/02_RK3588_Datasheet_V0.1-20210727.pdf",
    "UG152": "docs/_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf",
    "API232": "docs/_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf",
    "OPL": "docs/_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf",
    "UG232": SDK + "02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf",
    "QS232": SDK + "01_Rockchip_RKNPU_Quick_Start_RKNN_SDK_V2.3.2_EN.pdf",
    "RT232": SDK + "04_Rockchip_RKNPU_API_Reference_RKNNRT_V2.3.2_EN.pdf",
    "EYE": P + "01_hardware/eyeriss_dataflow_2016chen.pdf",
    "TPU": P + "01_hardware/tpu_datacenter_2017jouppi.pdf",
    "JUNG": P + "01_hardware/mobile_multicore_npu_2023jung.pdf",
    "FLEX": P + "01_hardware/flexer_multi_npu_2023min.pdf",
    "LP": P + "01_hardware/layer_puzzle_multicore_2023gao.pdf",
    "SURV": P + "00_overview/edge_ai_survey_2025wang.pdf",
    "NAGEL": P + "02_quantization/quant_whitepaper_2021nagel.pdf",
    "GHOLAMI": P + "02_quantization/quantization_survey_2021gholami.pdf",
    "QYOLO": P + "02_quantization/qyolo_ptq_2023wang.pdf",
    "Y7Q": P + "02_quantization/quant_yolov7_2024.pdf",
    "QAREP": P + "08_npu_friendly_arch/qarepvgg_quant_2024chu.pdf",
    "REPVGG": P + "08_npu_friendly_arch/repvgg_reparam_2021ding.pdf",
    "MOBONE": P + "08_npu_friendly_arch/mobileone_reparam_2023vasu.pdf",
    "Y6": P + "08_npu_friendly_arch/yolov6_hwfriendly_2022li.pdf",
    "ACTNAS": P + "08_npu_friendly_arch/actnas_yolo_2025sah.pdf",
    "S3NAS": P + "06_nas/s3nas_npu_aware_2020lee.pdf",
    "DAHD": P + "05_rk3588/dahd_yolo_rk3588_2025.pdf",
    "EDGE": P + "05_rk3588/edgesoc_benchmark_2026kong.pdf",
    "LNB": P + "05_rk3588/lnbyolo_rk3568_2025zhuo.pdf",
    "RK66": P + "05_rk3588/rk3566_npu_yolo11_2026limaran.pdf",
    "AGENT": P + "05_rk3588/rknn_conversion_agent_2026su.pdf",
    "TVM": P + "03_compiler/tvm_compiler_2018chen.pdf",
    "LEE24": P + "03_compiler/fused_layer_multiworkload_2024lee.pdf",
    "BAMB": P + "03_compiler/npu_compiler_codesign_2025bamberg.pdf",
    "LENS": P + "03_compiler/npu_compiler_scheduling_2026.pdf",
    "MCU": P + "04_memory/mcunet_2020lin.pdf",
    "PHI": P + "04_memory/phinets_edge_2021paissan.pdf",
    "YOFF": P + "09_yolo_architecture/yolo26_official_2026jocher.pdf",
    "Y26A": P + "09_yolo_architecture/yolo26_arch_2025sapkota.pdf",
    "Y26B": P + "09_yolo_architecture/yolo26_nmsfree_2026chakrabarty.pdf",
    "YEVO": P + "09_yolo_architecture/ultralytics_yolo_evolution_2025sapkota.pdf",
}
# --- single text files, cited as "<KEY> dong N[-M]" (or the whole file when no line is given)
TEXTS = {
    "SRAM": "docs/tools/visual_guide/_sources/04_RK3588_NPU_SRAM_usage.md",
    "DTS": "3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi",
    "HDR": "3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h",
    "OPSUP": SDK + "RKNNToolKit2_OP_Support-2.3.2.md",
    "FIXTURE": "tests/fixtures/eval_perf_2.3.2_layers.txt",
}
# --- directories or special forms
DIRS = {
    "DRV": "3rdparty/rknpu-driver-0.9.8/",                           # DRV <file>:a-b, file found recursively
    "ULT": ".venv/lib/python3.12/site-packages/ultralytics/",         # ULT <path>:a-b
    "UDOC": P + "09_yolo_architecture/",                              # UDOC <file>[:a-b]
    "RUN": "ai/automation/runs/",                                     # RUN <run_id>/<file>[:a-b]
    "LOG": "tmp/04_debug-logs/",                                      # LOG <dir>/<file>[:a-b]
    "REPO": "",                                                       # REPO <path>[:a-b]
}
RKNNPY_WHEEL = "3rdparty/rknn-toolkit2/rknn-toolkit2/packages/x86_64/rknn_toolkit2-2.3.2-cp38-*.whl"
RKNNPY_MEMBER_DOC = "RKNNPY <path inside wheel>:a-b, e.g. RKNNPY rknn/api/rknn.py:56-58"

_page_cache, _file_cache = {}, {}


def split_row(line):
    cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
    return [c.strip().replace("\\|", "|") for c in cells]


def parse_sources(path):
    """Return (rows, error). Each row: dict(hinh, noidung, tier, nguon, van, lineno)."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "## Nguồn"), None)
    if start is None:
        return [], "khong co muc '## Nguồn'"
    rows = []
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if ln.startswith("## "):
            break
        if not ln.strip().startswith("|"):
            continue
        cells = split_row(ln)
        if len(cells) != 5:
            return rows, f"dong {i + 1}: can 5 cot, co {len(cells)}"
        if cells[0] == "Hình" or set(cells[0]) <= set("-: "):
            continue
        rows.append(dict(hinh=cells[0], noidung=cells[1], tier=cells[2], nguon=cells[3].replace("`", ""),
                         van=cells[4].strip("`").strip(), lineno=i + 1))
    return rows, (None if rows else "bang nguon rong")


def norm(s):
    s = re.sub(r"(\w)-[ \t]*\n[ \t]*(\w)", r"\1\2", s)                 # line-break hyphenation
    s = re.sub(r"[\"'‘’“”•⚫\-]", "", s)  # quotes, bullets, remaining hyphens
    return re.sub(r"\s+", " ", s).strip().casefold()


def pdf_page(key, page):
    """Page text in reading order plus -layout order (tables read better in the latter)."""
    k = (key, page)
    if k not in _page_cache:
        outs = []
        for extra in ([], ["-layout"]):
            r = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), *extra,
                                os.path.join(ROOT, PDFS[key]), "-"], capture_output=True, text=True)
            if r.returncode != 0:
                raise ValueError(f"pdftotext loi {key} tr.{page}: {r.stderr.strip()[:80]}")
            outs.append(r.stdout)
        _page_cache[k] = "\n\n".join(outs)
    return _page_cache[k]


def file_lines(path):
    if path not in _file_cache:
        if not os.path.isfile(path):
            raise ValueError(f"khong co file {os.path.relpath(path, ROOT)}")
        with open(path, encoding="utf-8", errors="replace") as fh:
            _file_cache[path] = fh.read().split("\n")
    return _file_cache[path]


def pick(lines, a, b):
    if a is None:
        return "\n".join(lines)
    if a < 1 or a > len(lines):
        raise ValueError(f"dong {a} ngoai file ({len(lines)} dong)")
    return "\n".join(lines[a - 1:b])


def span(m_a, m_b):
    a = int(m_a) if m_a else None
    return a, (int(m_b) if m_b else a)


def strip_html(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return re.sub(r"&nbsp;", " ", re.sub(r"&amp;", "&", t))


def find_drv(name):
    hits = glob.glob(os.path.join(ROOT, DIRS["DRV"], "**", name), recursive=True)
    if len(hits) != 1:
        raise ValueError(f"DRV {name}: {len(hits)} file khop")
    return hits[0]


def wheel_member(member):
    wheels = glob.glob(os.path.join(ROOT, RKNNPY_WHEEL))
    if not wheels:
        raise ValueError("khong co wheel rknn_toolkit2 cp38")
    key = (wheels[0], member)
    if key not in _file_cache:
        with zipfile.ZipFile(wheels[0]) as z:
            if member not in z.namelist():
                raise ValueError(f"RKNNPY: khong co {member} trong wheel")
            _file_cache[key] = z.read(member).decode("utf-8", errors="replace").split("\n")
    return _file_cache[key]


LINES = r"(?::(\d+)(?:-(\d+))?)?"


def located_text(src):
    """Text of one source reference such as 'TRM1 tr.1984' or 'DRV rknpu_job.c:508-538'."""
    src = src.strip()
    m = re.fullmatch(r"(\w+)\s+tr\.(\d+)", src)
    if m and m.group(1) in PDFS:
        return pdf_page(m.group(1), int(m.group(2)))
    m = re.fullmatch(r"(\w+)(?:\s+dòng\s+(\d+)(?:-(\d+))?)?", src)
    if m and m.group(1) in TEXTS:
        a, b = span(m.group(2), m.group(3))
        return pick(file_lines(os.path.join(ROOT, TEXTS[m.group(1)])), a, b)
    m = re.fullmatch(r"DRV\s+(\S+?)" + LINES, src)
    if m:
        a, b = span(m.group(2), m.group(3))
        return pick(file_lines(find_drv(m.group(1))), a, b)
    m = re.fullmatch(r"RKNNPY\s+(\S+?)" + LINES, src)
    if m:
        a, b = span(m.group(2), m.group(3))
        return pick(wheel_member(m.group(1)), a, b)
    m = re.fullmatch(r"ULT\s+(\S+?)" + LINES, src)
    if m:
        a, b = span(m.group(2), m.group(3))
        return pick(file_lines(os.path.join(ROOT, DIRS["ULT"], m.group(1))), a, b)
    m = re.fullmatch(r"UDOC\s+(\S+?)" + LINES, src)
    if m:
        a, b = span(m.group(2), m.group(3))
        path = os.path.join(ROOT, DIRS["UDOC"], m.group(1))
        text = pick(file_lines(path), a, b)
        return strip_html(text) if path.endswith(".html") else text
    m = re.fullmatch(r"REPO\s+(\S+\.pdf)\s+tr\.(\d+)", src)
    if m:
        key = "REPO:" + m.group(1)           # registered on the fly; skipped by --check-map (key has ":")
        PDFS[key] = m.group(1)
        return pdf_page(key, int(m.group(2)))
    m = re.fullmatch(r"(REPO|RUN|LOG)\s+(\S+?)" + LINES, src)
    if m:
        a, b = span(m.group(3), m.group(4))
        return pick(file_lines(os.path.join(ROOT, DIRS[m.group(1)], m.group(2))), a, b)
    raise ValueError(f"dang nguon khong ho tro: '{src}'")


def check_row(row):
    van = row["van"]
    if van in ("(số học)", "(đọc từ hình)"):
        return "MANUAL", van
    if van == "(unknown)":
        return "UNKNOWN", "khong co nguon de tim"
    if len(van) < 4:
        return "FAIL", "nguyen van qua ngan"
    want = norm(van)
    errs = []
    for src in row["nguon"].split(";"):
        try:
            text = norm(located_text(src))
        except ValueError as e:
            errs.append(str(e))
            continue
        if want in text or want.replace(" ", "") in text.replace(" ", ""):
            return "OK", src.strip()
        errs.append(f"khong thay trong {src.strip()}")
    return "FAIL", "; ".join(errs)


def check_map():
    """Print every abbreviation with its path and whether it exists. Returns the number of missing paths."""
    missing = 0
    entries = [(k, v) for k, v in {**PDFS, **TEXTS, **DIRS}.items() if ":" not in k]
    entries.append(("RKNNPY", RKNNPY_WHEEL))
    for key, rel in entries:
        full = os.path.join(ROOT, rel)
        ok = bool(glob.glob(full)) if "*" in rel else os.path.exists(full)
        if key == "REPO":
            ok = os.path.isdir(ROOT)
        missing += not ok
        print(f"{'OK     ' if ok else 'MISSING'} {key:8s} {rel or '(repo root)'}")
    for tool in ("pdftotext",):
        found = any(os.access(os.path.join(d, tool), os.X_OK) for d in os.environ.get("PATH", "").split(os.pathsep))
        missing += not found
        print(f"{'OK     ' if found else 'MISSING'} {tool}")
    print(f"--- {len(entries)} abbreviations, {missing} missing")
    return missing


def topic_dirs():
    return sorted(d for d in glob.glob(os.path.join(HERE, "*", "")) if glob.glob(os.path.join(d, "[0-9][0-9]-*", "chu-thich.md")))


def main():
    args = sys.argv[1:]
    if "--check-map" in args:
        sys.exit(1 if check_map() else 0)
    topics = [os.path.abspath(a) for a in args] or [os.path.abspath(d) for d in topic_dirs()]
    counts = {"OK": 0, "FAIL": 0, "MANUAL": 0, "UNKNOWN": 0}
    manual = []
    for topic in topics:
        for f in sorted(glob.glob(os.path.join(topic, "[0-9][0-9]-*", "chu-thich.md"))):
            rel = os.path.relpath(f, topic)
            rows, err = parse_sources(f)
            if err:
                print(f"FAIL {rel}: {err}")
                counts["FAIL"] += 1
            for row in rows:
                status, info = check_row(row)
                counts[status] += 1
                if status == "MANUAL":
                    manual.append((rel, row))
                print(f"{status:7s} {rel}:{row['lineno']} {row['hinh']} | {row['nguon']} | "
                      f"{info if status != 'OK' else ''}")
    print("---")
    print("Tong: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    for rel, row in manual:
        print(f"MANUAL {rel}:{row['lineno']} {row['hinh']} {row['noidung']} [{row['nguon']}]")
    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    main()
