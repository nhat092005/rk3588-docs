"""Research-style SVG helpers for the NPU study figure set.

Shared by every topic under docs/tools/visual_guide/. Copied from /home/nhat/workspace/prjs/aiot-edge/tmp/report/app/figlib.py (itself copied from
blockchain-iot/tmp/report/luong-blockchain/gen_blockchain_flows.py); the original API is unchanged.

Added here:
  tier(x, y, label)           badge T1 RK3588 / T2 chung / T3 do
  original(x, y, w, path, caption)  embeds an original PNG as a "Hinh goc" panel (path relative to the topic dir; base64 data URI,
                              because SVG loaded through <img> blocks external resources)
  unknown(x, y, text)         dashed red note for facts the sources do not give
Changes from the template source: text()/rich() take a halo colour, phase() draws a titled step group for
sequence diagrams, lifelines() draws sequence-diagram heads, and run() writes SVG + PNG for a list of figures.
"""
import base64
import html
import os
import shutil
import struct
import subprocess
import sys
import tempfile

FONT = "'Times New Roman', Times, serif"
MONO = "Consolas, 'DejaVu Sans Mono', monospace"
BLUE, GREEN, RED, GRAY, INK = "#1E5BB8", "#2E7D32", "#C62828", "#777777", "#222222"
DARK = "#444444"
LAYER_FILL, LAYER_STROKE, LAYER_LABEL = "#F5F5F5", "#666666", "#333333"
BOX_STROKE = "#333333"
THIN, THICK = 1.6, 3.0


def _halo(color):
    return (f' stroke="{color}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"'
            if color else "")


def topic_dir():
    """Topic directory = parent of the part folder containing the script being run (resolved from the file, not cwd)."""
    main = getattr(sys.modules.get("__main__"), "__file__", None) or __file__
    return os.path.dirname(os.path.dirname(os.path.abspath(main)))


class Fig:
    def __init__(self, w, h):
        self.w, self.h, self.out = w, h, []

    def a(self, s):
        self.out.append(s)

    # ---------- text ----------
    def text(self, x, y, s, size=14, weight=400, fill=INK, anchor="start", italic=False, mono=False,
             halo=None):
        st = ' font-style="italic"' if italic else ""
        fam = f' font-family="{MONO}"' if mono else ""
        self.a(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
               f'text-anchor="{anchor}" dominant-baseline="central"{fam}{st}{_halo(halo)}>'
               f'{html.escape(s)}</text>')

    def rich(self, x, y, parts, size=13, anchor="start", fill=INK, halo=None):
        """parts: str or list of (text, kind); kind 't' plain, 'c' code, 'b' bold."""
        if isinstance(parts, str):
            parts = [(parts, "t")]
        spans = []
        for s, kind in parts:
            attr = ""
            if kind == "c":
                attr = f' font-family="{MONO}" font-size="{size - 1}"'
            elif kind == "b":
                attr = ' font-weight="700"'
            spans.append(f'<tspan{attr}>{html.escape(s)}</tspan>')
        self.a(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
               f'dominant-baseline="central"{_halo(halo)} xml:space="preserve">{"".join(spans)}</text>')

    # ---------- shapes ----------
    def box(self, x, y, w, h, title, sub="", dashed=False, mono=False, sub_fill=INK, sub_size=14,
            title_size=16.5, fill="white"):
        dash = ' stroke-dasharray="5 3"' if dashed else ""
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{BOX_STROKE}" '
               f'stroke-width="1.2"{dash}/>')
        cx = x + w / 2
        if sub:
            # proportional spacing reads well up to ~70 px; taller boxes keep the two lines together
            ty, sy = (y + h * 0.37, y + h * 0.70) if h <= 70 else (y + h / 2 - 11, y + h / 2 + 12)
            self.text(cx, ty, title, size=title_size - (1.5 if mono else 0), weight=700,
                      anchor="middle", mono=mono)
            self.text(cx, sy, sub, size=sub_size, anchor="middle", fill=sub_fill)
        else:
            self.text(cx, y + h / 2, title, size=title_size, weight=700, anchor="middle", mono=mono)

    def note(self, x, y, w, lines, size=12.5):
        h = 10 + 16 * len(lines)
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="white" stroke="{GRAY}" '
               f'stroke-width="1"/>')
        for i, ln in enumerate(lines):
            self.rich(x + w / 2, y + 13 + 16 * i, ln, size=size, anchor="middle")
        return y + h

    def layer(self, x, y, w, h, lines, side=False):
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{LAYER_FILL}" '
               f'stroke="{LAYER_STROKE}" stroke-width="1.2"/>')
        if side:
            top = y + h / 2 - (len(lines) - 1) * 9
            for i, ln in enumerate(lines):
                self.text(x + 14, top + 18 * i, ln, size=14.5 if i == 0 else 13,
                          weight=700 if i == 0 else 400, fill=LAYER_LABEL)
        else:
            self.text(x + 14, y + 19, lines[0], size=15, weight=700, fill=LAYER_LABEL)

    def lifelines(self, heads, y0, y1, phases=(), bw=150, bh=56, x=10, w=880):
        """heads: list of (x, title, sub); phases: list of (y, h, title) step groups.

        Order matters: phase frames, then lifelines, then phase titles with a halo so the
        lifelines do not run through them.
        """
        for py, ph, _ in phases:
            self.a(f'<rect x="{x}" y="{py}" width="{w}" height="{ph}" rx="6" fill="none" stroke="#AAAAAA" '
                   f'stroke-width="1" stroke-dasharray="6 4"/>')
        for lx, title, sub in heads:
            self.a(f'<path d="M{lx} {y0 + bh} L{lx} {y1}" stroke="{GRAY}" stroke-width="1" '
                   f'stroke-dasharray="4 4"/>')
            self.box(lx - bw / 2, y0, bw, bh, title, sub, title_size=15.5, sub_size=13)
        for py, _, title in phases:
            # halo only covers glyphs; a white plate also hides lifelines in the gaps between words
            tw = len(title) * 13.5 * 0.5
            self.a(f'<rect x="{x + 8}" y="{py + 4}" width="{tw + 8:g}" height="20" fill="white"/>')
            self.text(x + 12, py + 14, title, size=13.5, weight=700, fill=LAYER_LABEL)

    def line(self, pts, color, width=THIN, dashed=False, head=True):
        if head and width >= THICK:
            # pull the last point back so the thick stroke does not poke through the arrow tip
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            dx, dy = x2 - x1, y2 - y1
            n = (dx * dx + dy * dy) ** 0.5 or 1
            pts = pts[:-1] + [(x2 - dx / n * 6, y2 - dy / n * 6)]
        d = "M" + " L".join(f"{px:g} {py:g}" for px, py in pts)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        mk = f' marker-end="url(#{self.marker(color, width)})"' if head else ""
        self.a(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{mk}/>')

    def marker(self, color, width):
        return f"m{color[1:]}{'t' if width >= THICK else 'n'}"

    def badge(self, x, y, s, color=BLUE):
        self.a(f'<circle cx="{x}" cy="{y}" r="10" fill="{color}" stroke="white" stroke-width="1.5"/>')
        self.text(x, y + 0.5, s, size=12.5, weight=700, fill="white", anchor="middle")

    # ---------- composite ----------
    def table(self, x, y, widths, header, rows, size=12.5, line_h=17, fills=None):
        """Cells: str, list of parts, or ('lines', [line, ...]) / ('badge', n, color)."""
        def lines_of(cell):
            if isinstance(cell, tuple) and cell[0] == "lines":
                return cell[1]
            return [cell]

        head_h = 28
        self.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{head_h}" fill="#E8E8E8"/>')
        cx = x
        for wd, hd in zip(widths, header):
            self.text(cx + 8, y + head_h / 2, hd, size=size, weight=700)
            cx += wd
        cy = y + head_h
        for ri, row in enumerate(rows):
            n = max(len(lines_of(c)) for c in row if not (isinstance(c, tuple) and c[0] == "badge"))
            rh = 9 + line_h * n
            if fills and fills.get(ri):
                self.a(f'<rect x="{x}" y="{cy}" width="{sum(widths)}" height="{rh}" fill="{fills[ri]}"/>')
            self.a(f'<path d="M{x} {cy} L{x + sum(widths)} {cy}" stroke="#BBBBBB" stroke-width="0.8"/>')
            cx = x
            for wd, cell in zip(widths, row):
                if isinstance(cell, tuple) and cell[0] == "badge":
                    self.badge(cx + wd / 2, cy + rh / 2, cell[1], cell[2])
                else:
                    ls = lines_of(cell)
                    top = cy + rh / 2 - (len(ls) - 1) * line_h / 2
                    for i, ln in enumerate(ls):
                        self.rich(cx + 8, top + i * line_h, ln, size=size)
                cx += wd
            cy += rh
        self.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{cy - y}" fill="none" '
               f'stroke="#999999" stroke-width="1"/>')
        cx = x
        for wd in widths[:-1]:
            cx += wd
            self.a(f'<path d="M{cx} {y} L{cx} {cy}" stroke="#CCCCCC" stroke-width="0.8"/>')
        return cy

    def entity(self, x, y, w, title, fields, dashed=False, row_h=18, title_size=14):
        """ERD table box. fields: (name, tag) where tag like 'PK', 'FK', 'PK, FK → users'. Returns height."""
        h = 28 + row_h * len(fields) + 8
        dash = ' stroke-dasharray="5 3"' if dashed else ""
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="white" stroke="{BOX_STROKE}" '
               f'stroke-width="1.2"{dash}/>')
        self.a(f'<rect x="{x + 0.6}" y="{y + 0.6}" width="{w - 1.2}" height="27" rx="4" fill="{LAYER_FILL}"/>')
        self.a(f'<path d="M{x} {y + 28} L{x + w} {y + 28}" stroke="{BOX_STROKE}" stroke-width="1"/>')
        self.text(x + w / 2, y + 14, title, size=title_size, weight=700, anchor="middle", mono=True)
        for i, (name, tag) in enumerate(fields):
            ry = y + 28 + 4 + row_h * i + row_h / 2
            self.text(x + 8, ry, name, size=12, mono=True, weight=700 if "PK" in tag else 400)
            if tag:
                self.text(x + w - 8, ry, tag, size=11, fill=DARK, anchor="end")
        return h

    def state(self, x, y, w, name, sub="", h=52, fill="white", stroke=BOX_STROKE, width=1.2, mono=True):
        """Rounded state box for state-machine figures: name (code by default) over a short meaning."""
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" '
               f'stroke-width="{width}"/>')
        size = 14 if mono else 15
        if sub:
            self.text(x + w / 2, y + h / 2 - 9, name, size=size, weight=700, anchor="middle", mono=mono)
            self.text(x + w / 2, y + h / 2 + 10, sub, size=12.5, anchor="middle", fill=DARK)
        else:
            self.text(x + w / 2, y + h / 2, name, size=size, weight=700, anchor="middle", mono=mono)

    def textbox(self, x, y, w, lines, size=13):
        """Bordered free-text box (edge cases, notes under a figure). Returns its bottom y."""
        h = 24 + 20 * len(lines)
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#999999" '
               f'stroke-width="1"/>')
        for i, ln in enumerate(lines):
            self.rich(x + 14, y + 22 + 20 * i, ln, size=size)
        return y + h

    def legend(self, x, y, w, items, title="Chú thích"):
        h = 34 + 22 * len(items)
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#999999" '
               f'stroke-width="1"/>')
        self.text(x + 14, y + 17, title, size=14, weight=700)
        for i, (kind, label) in enumerate(items):
            ly = y + 40 + 22 * i
            sx = x + 16
            if kind == "badge":
                self.badge(sx + 19, ly, "n", BLUE)
            elif kind == "dashedbox":
                self.a(f'<rect x="{sx}" y="{ly - 8}" width="38" height="16" rx="2" fill="white" '
                       f'stroke="{BOX_STROKE}" stroke-dasharray="5 3"/>')
            elif kind.startswith("fill:"):
                self.a(f'<rect x="{sx}" y="{ly - 8}" width="38" height="16" rx="2" fill="{kind[5:]}" '
                       f'stroke="#BBBBBB"/>')
            elif kind == "phase":
                self.a(f'<rect x="{sx}" y="{ly - 8}" width="38" height="16" rx="3" fill="none" '
                       f'stroke="#AAAAAA" stroke-dasharray="6 4"/>')
            else:
                color, width, dashed = {
                    "blue": (BLUE, THIN, False), "green": (GREEN, THICK, False), "red": (RED, THICK, False),
                    "redthin": (RED, THIN, False), "greenthin": (GREEN, THIN, False),
                    "gray": (GRAY, THIN, True), "ink": (INK, THIN, False)}[kind]
                self.line([(sx, ly), (sx + 40, ly)], color, width, dashed)
            self.rich(sx + 52, ly, label, size=13)
        return y + h

    def params(self, x, y, w, rows, title="Tham số"):
        h = 34 + 20 * len(rows)
        self.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="white" stroke="#999999" '
               f'stroke-width="1"/>')
        self.text(x + 14, y + 17, title, size=14, weight=700)
        for i, (name, value) in enumerate(rows):
            self.rich(x + 16, y + 40 + 20 * i, [(name, "c"), (" = " + value, "t")], size=13)
        return y + h

    def msg(self, x1, x2, y, color, above="", below="", num=None, width=THIN, dashed=False,
            above_code=False, num_color=BLUE):
        """Sequence-diagram message between two lifelines with labels centred over the arrow."""
        self.line([(x1, y), (x2, y)], color, width, dashed)
        # keep the label clear of the badge sitting at the sender's end
        cx = (x1 + x2) / 2 + ((8 if x2 > x1 else -8) if num else 0)
        if above:
            parts = [(above, "c")] if above_code else above
            self.rich(cx, y - 10, parts, size=13, anchor="middle", halo="white")
        if num:
            # on the line at the sender's end, clear of lifelines and the arrow head
            self.badge(x1 + (22 if x2 > x1 else -22), y, num, num_color)
        if below:
            self.rich(cx, y + 11, below, size=12, anchor="middle", fill=DARK, halo="white")

    # ---------- additions for the NPU study set ----------
    TIERS = {"T1 RK3588": BLUE, "T2 chung": GREEN, "T3 đo": RED}

    def tier(self, x, y, label):
        """Tier badge; (x, y) is the top-left corner. Labels are fixed by the decision log."""
        color = self.TIERS[label]
        w = 14 + 7.4 * len(label)
        self.a(f'<rect x="{x}" y="{y}" width="{w:g}" height="22" rx="11" fill="white" stroke="{color}" '
               f'stroke-width="1.8"/>')
        self.text(x + w / 2, y + 11.5, label, size=13, weight=700, fill=color, anchor="middle")
        return x + w

    def original(self, x, y, w, path, caption):
        """Panel 'Hình gốc' with a PNG and a caption (source + page). Returns the panel bottom y.

        path: absolute, or relative to the topic directory (the parent of the part folder that holds the running
        gen.py), e.g. "../../npu_study/images/02_rk3588_npu_hardware/trm2_p16_fig1-1.png".
        """
        full = path if os.path.isabs(path) else os.path.normpath(os.path.join(topic_dir(), path))
        with open(full, "rb") as fh:
            data = fh.read()
        iw, ih = struct.unpack(">II", data[16:24])  # PNG IHDR width, height
        h = round(w * ih / iw)
        lines = [caption] if isinstance(caption, str) else list(caption)
        ph = 30 + h + 10 + 17 * len(lines) + 4
        self.a(f'<rect x="{x}" y="{y}" width="{w + 20}" height="{ph}" rx="6" fill="white" stroke="#999999" '
               f'stroke-width="1"/>')
        self.text(x + 10, y + 16, "Hình gốc", size=14, weight=700)
        b64 = base64.b64encode(data).decode("ascii")
        self.a(f'<image x="{x + 10}" y="{y + 30}" width="{w}" height="{h}" '
               f'href="data:image/png;base64,{b64}"/>')
        self.a(f'<rect x="{x + 10}" y="{y + 30}" width="{w}" height="{h}" fill="none" stroke="#CCCCCC"/>')
        for i, ln in enumerate(lines):
            self.text(x + 10, y + 30 + h + 14 + 17 * i, ln, size=12, fill=DARK, italic=True)
        return y + ph

    def unknown(self, x, y, text, w=None, size=12.5):
        """Dashed red-ish note marking a fact that the sources do not give. text: str or list of lines."""
        lines = [text] if isinstance(text, str) else list(text)
        if w is None:
            w = 30 + max(len(ln) for ln in lines) * size * 0.5 + 62
        h = 12 + 17 * len(lines)
        self.a(f'<rect x="{x}" y="{y}" width="{w:g}" height="{h}" rx="4" fill="#FFF3F3" stroke="{RED}" '
               f'stroke-width="1.3" stroke-dasharray="5 3"/>')
        for i, ln in enumerate(lines):
            parts = ([("unknown: ", "b")] if i == 0 else [("          ", "t")]) + [(ln, "t")]
            self.rich(x + 10, y + 6 + 8.5 + 17 * i, parts, size=size)
        return y + h

    def svg(self):
        colors = [(c, w) for c in (BLUE, GREEN, RED, GRAY, INK) for w in (THIN, THICK)]
        defs = []
        for c, w in colors:
            size = 13 if w >= THICK else 10
            defs.append(f'<marker id="{self.marker(c, w)}" viewBox="0 0 10 10" refX="9" refY="5" '
                        f'markerWidth="{size}" markerHeight="{size}" markerUnits="userSpaceOnUse" '
                        f'orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="{c}"/></marker>')
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" font-family="{FONT}"><defs>{"".join(defs)}</defs>'
                f'<rect width="{self.w}" height="{self.h}" fill="white"/>')
        return "\n".join([head] + self.out + ["</svg>"])


C = lambda s: [(s, "c")]  # noqa: E731


def to_png(svg_path, png_path, w, h):
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "page.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}</style>'
                     f'<img src="file://{os.path.abspath(svg_path)}" width="{w}" height="{h}">')
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp}",
                        "--force-device-scale-factor=3", f"--window-size={w},{h}",
                        f"--screenshot={os.path.abspath(png_path)}", f"file://{page}"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def source(f, y, text):
    """Italic source line under a figure; sets the figure height to fit it."""
    f.text(10, y + 18, text, size=12, fill=DARK, italic=True)
    f.h = y + 32


def run(figs, default_dir, make_png=False):
    """figs: list of (name, build). Usage: script.py [outdir] [--png] [name ...]"""
    args = sys.argv[1:]
    png_enabled = "--png" in args or make_png
    clean_args = [a for a in args if a != "--png"]
    outdir = clean_args[0] if clean_args and not any(clean_args[0] == n for n, _ in figs) else default_dir
    only = [a for a in clean_args if any(a == n for n, _ in figs)]
    for name, build in figs:
        if only and name not in only:
            continue
        fig = build()
        svg_path = os.path.join(outdir, name + ".svg")
        with open(svg_path, "w", encoding="utf-8") as fh:
            fh.write(fig.svg())
        png_done = False
        if png_enabled:
            png_done = to_png(svg_path, os.path.join(outdir, name + ".png"), fig.w, fig.h)
        print(f"{name}: {fig.w}x{fig.h}{' + png' if png_done else ''}")

