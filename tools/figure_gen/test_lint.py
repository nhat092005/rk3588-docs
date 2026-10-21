"""Kiểm thử recall của lint.py: mỗi luật có ít nhất một SVG nhỏ chứa đúng lỗi đó, và một SVG sạch không được báo gì.

Chạy: python3 -m unittest docs/tools/figure_gen/test_lint.py   (cần google-chrome hoặc chromium)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint

CHROME = shutil.which("google-chrome") or shutil.which("chromium")
INK = "#222222"
DEFS = "".join(f'<marker id="m{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="{s}" markerHeight="{s}" '
               f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="{INK}"/></marker>'
               for k, s in (("n", 10), ("t", 13)))


def svg(body, w=200, h=100):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="Times New Roman"><defs>{DEFS}</defs><rect width="{w}" height="{h}" fill="white"/>{body}</svg>')


def T(x, y, s, size=9, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{INK}" text-anchor="start" dominant-baseline="central" {extra}>{s}</text>'


def box(x, y, w, h, fill="none", extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{INK}" stroke-width="1" {extra}/>'


def path(d, stroke=INK, width=1, extra=""):
    return f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{width}" {extra}/>'


HALO = 'stroke="white" stroke-width="3"'
THICK, THIN = 'marker-end="url(#mt)"', 'marker-end="url(#mn)"'

# (tên, svg, luật phải có, luật không được có)
CASES = [
    ("OVERLAP", T(20, 30, "Hello world") + T(22, 31, "Hello world"), {"OVERLAP"}, set()),
    ("CROSS_EDGE", box(20, 20, 60, 40) + T(10, 40, "Crossing the edge"), {"CROSS_EDGE"}, set()),
    ("COVERED", T(20, 30, "Hidden") + '<rect x="15" y="20" width="60" height="20" fill="#ffcc00"/>', {"COVERED"}, set()),
    ("LINE_THROUGH", T(20, 30, "Struck through") + path("M10 30 L100 30"), {"LINE_THROUGH"}, set()),
    ("OUT_OF_CANVAS", T(-10, 30, "Out"), {"OUT_OF_CANVAS"}, set()),
    ("SHAPE_OUT_OF_CANVAS", f'<circle cx="-10" cy="50" r="5" fill="none" stroke="{INK}"/>', {"SHAPE_OUT_OF_CANVAS"}, set()),
    ("ARROW_TOO_SHORT", path("M10 50 L19 50", width=3, extra=THICK), {"ARROW_TOO_SHORT"}, set()),
    ("SHAPE_CROSS_EDGE", box(20, 10, 160, 50) + path("M30 40 L100 40 L100 80"), {"SHAPE_CROSS_EDGE"}, set()),
    ("SMALL_FONT", T(20, 30, "tiny", 5), {"SMALL_FONT"}, set()),
    ("TIGHT_TEXT", box(20, 20, 100, 40) + T(21.5, 40, "x"), {"TIGHT_TEXT"}, set()),
    ("LOW_CONTRAST", T(20, 30, "Pale text", 9, 'fill="#cccccc"').replace(f'fill="{INK}" ', ""), {"LOW_CONTRAST"}, set()),
    ("EMPTY_SPACE", box(10, 10, 180, 80) + T(20, 20, "Title"), {"EMPTY_SPACE"}, set()),
    ("BIG_GAP", box(10, 5, 50, 20) + box(10, 60, 50, 20), {"BIG_GAP"}, set()),
    ("HALO_CROSS_EDGE", box(20, 20, 60, 40) + T(10, 40, "Crossing the edge", 9, HALO), {"HALO_CROSS_EDGE"}, {"CROSS_EDGE"}),
    ("HALO_LINE_THROUGH", T(20, 30, "Struck through", 9, HALO) + path("M10 30 L100 30"), {"HALO_LINE_THROUGH"}, {"LINE_THROUGH"}),
    ("HALO_COVERED", T(20, 30, "Hidden", 9, HALO) + '<rect x="15" y="20" width="60" height="20" fill="#ffcc00"/>', {"HALO_COVERED"}, {"COVERED"}),
    ("GRID_THROUGH", path("M10 30 L100 30", stroke="#CFD8DC") + T(20, 30, "Over the grid"), {"GRID_THROUGH"}, {"LINE_THROUGH"}),
    ("LINE_UNDER_CHIP", path("M10 30 L100 30") + '<rect x="15" y="22" width="90" height="16" fill="white"/>' + T(20, 30, "Chip hides line"),
     {"LINE_UNDER_CHIP"}, {"LINE_THROUGH"}),
    ("COVERED_PARTIAL", T(20, 30, "Hidden words here") + '<rect x="15" y="20" width="12" height="20" fill="#ffcc00"/>', {"COVERED_PARTIAL"}, {"COVERED"}),
    ("TEXT_TOUCH", T(20, 30, "First line", 12) + T(20, 41, "Second line", 12), {"TEXT_TOUCH"}, {"OVERLAP"}),
    ("TEXT_NEAR_EDGE", box(20, 50, 100, 30) + T(25, 44, "Just above the box"), {"TEXT_NEAR_EDGE"}, {"CROSS_EDGE"}),
    ("TEXT_NEAR_STROKE", T(20, 30, "Label here") + path("M0 34.5 L200 34.5"), {"TEXT_NEAR_STROKE"}, {"LINE_THROUGH"}),
    ("SHAPE_ENTERS_EDGE", box(20, 20, 100, 50) + path("M0 45 L35 45"), {"SHAPE_ENTERS_EDGE"}, {"SHAPE_CROSS_EDGE"}),
    ("SHAPE_UNDER_FILL", path("M0 45 L60 45") + box(20, 20, 100, 50, fill="#eeeeee"), {"SHAPE_UNDER_FILL"}, {"SHAPE_CROSS_EDGE"}),
    ("ARROW_SHORT_SHAFT", box(0, 40, 9, 20) + path("M10 50 L22 50", extra=THIN) + box(24, 40, 20, 20), {"ARROW_SHORT_SHAFT"}, {"ARROW_TOO_SHORT"}),
    ("DANGLING_ARROW", path("M20 50 L80 50", width=3, extra=THICK), {"DANGLING_ARROW"}, set()),
    ("ARROW_THROUGH_BOX", box(60, 20, 40, 40) + box(0, 35, 6, 10) + path("M8 40 L150 40", extra=THIN) + box(152, 35, 6, 10),
     {"ARROW_THROUGH_BOX"}, set()),
    ("ARROWHEAD_ON_TEXT", path("M20 50 L110 50", extra=THIN) + T(100, 50, "Target label"), {"ARROWHEAD_ON_TEXT"}, set()),
    ("NOT_EVALUATED", T(20, 30, "Moved", 9, 'transform="translate(5,5)"'), {"NOT_EVALUATED"}, set()),
]

# Hình sạch: hộp có chữ giữa, mũi tên nối hai hộp có thân đủ dài, nhãn đặt sát nhưng không chạm.
CLEAN = (box(20, 20, 60, 50) + T(50, 45, "A", 10, 'text-anchor="middle"').replace('text-anchor="start" ', "")
         + box(120, 20, 60, 50) + T(150, 45, "B", 10, 'text-anchor="middle"').replace('text-anchor="start" ', "")
         + path("M80 45 L118 45", extra=THIN) + T(85, 80, "Nối A với B"))


@unittest.skipUnless(CHROME, "cần google-chrome hoặc chromium")
class LintRecall(unittest.TestCase):
    def rules(self, body):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "case.svg")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body)
            return {i["rule"] for i in lint.lint_svg(p, 6.5, CHROME)}

    def test_each_rule_is_detected(self):
        for name, body, must, mustnt in CASES:
            with self.subTest(rule=name):
                got = self.rules(svg(body))
                self.assertTrue(must <= got, f"thiếu {must - got}, có {got}")
                self.assertFalse(mustnt & got, f"không được có {mustnt & got}, có {got}")

    def test_every_rule_has_a_case(self):
        covered = set().union(*(c[2] for c in CASES))
        self.assertEqual(set(), (lint.ERRORS | lint.WARNS) - covered, "luật ERROR/WARN chưa có ca kiểm thử")

    def findings(self, body):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "case.svg")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(svg(body))
            return lint.lint_svg(p, 6.5, CHROME)

    def test_tight_text_in_small_grid_cell(self):
        # ô 14x14 cạnh nhau, chữ rộng ~12 px: chỉ báo TIGHT_TEXT, không báo TEXT_NEAR_EDGE với cạnh chung của ô bên cạnh
        cells = "".join(box(20 + 14 * i, 30, 14, 14) + T(21 + 14 * i, 37, "w·x", 8) for i in range(3))
        got = {i["rule"] for i in self.findings(cells)}
        self.assertIn("TIGHT_TEXT", got)
        self.assertNotIn("TEXT_NEAR_EDGE", got)

    def test_grid_lines_through_one_label_are_one_finding(self):
        grid = path("M30 10 L30 60", stroke="#E2E8F0") + path("M60 10 L60 60", stroke="#E2E8F0")
        res = [i for i in self.findings(grid + T(20, 30, "Label across grid", 9)) if i["rule"] == "GRID_THROUGH"]
        self.assertEqual(1, len(res))
        self.assertIn("2 nét mờ", res[0]["detail"])

    def test_clean_figure_reports_nothing(self):
        self.assertEqual(set(), self.rules(svg(CLEAN)))

    def test_exit_code_follows_errors_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, body in (("err", T(20, 30, "Hello world") + T(22, 31, "Hello world")), ("review", CASES[16][1]), ("clean", CLEAN)):
                with open(os.path.join(tmp, name + ".svg"), "w", encoding="utf-8") as fh:
                    fh.write(svg(body))
            run = lambda n: subprocess.run([sys.executable, os.path.join(os.path.dirname(lint.__file__), "lint.py"), os.path.join(tmp, n + ".svg")],
                                           capture_output=True, text=True)
            self.assertEqual(1, run("err").returncode)
            self.assertEqual(0, run("review").returncode)
            self.assertEqual(0, run("clean").returncode)
            self.assertIn("ưu tiên nội dung", run("review").stdout)


if __name__ == "__main__":
    unittest.main()
