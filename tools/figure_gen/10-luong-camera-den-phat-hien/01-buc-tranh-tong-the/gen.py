#!/usr/bin/env python3
"""Trang 01-buc-tranh-tong-the (nhóm 10-luong-camera-den-phat-hien), hình 1: đường đi của ảnh.

Bố cục lấy DDR làm trục: hàng 1 (bước 0 đến 3) truyền trực tiếp, ISP ghi xuống DDR, hàng 2 (bước 4 đến 8) trao đổi qua DDR.
Nội dung (bước, khối, dữ liệu ra, trạng thái đo, nhãn trên mũi tên) giữ đúng sơ đồ ASCII cũ của trang.
Chiều đọc của bước 4 và 5 không có nhãn riêng trong sơ đồ cũ, suy ra từ chiều ghi của bước trước [SL].

Hình 2 (lcd-2-ai-doc-ghi-ddr): các khối đọc ghi DDR qua interconnect, thay sơ đồ ASCII của mục 3.
Hình 3 (lcd-3-mat-phang-dieu-khien): vòng 3A giữa rkaiq, ISP và I2C, thay sơ đồ ASCII của mục 4.

Chạy: python3 gen.py [outdir] [--png] [tên_ảnh ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, INK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "_assets", "generated",
                                              "10-luong-camera-den-phat-hien", "01-buc-tranh-tong-the"))

W = 1060
M = 30                  # lề trái và phải
BH = 124                # chiều cao hộp
MEAS_FILL = "#CDE5D3"      # đo khi chạy camera (một màu duy nhất cho trạng thái đo, đậm dần theo mức chắc)
LIVE_FILL, LIVE_STROKE = "#F8E6BC", "#B7791F"   # đo trên khung NV12 thật
BADGE = "#444444"
ARROW = 2.2          # mũi tên DDR, mảnh hơn THICK để bớt rực
OUT_COLOR = "#1F3A66"   # chỉ dùng cho chữ trên thanh DDR
TEXT2 = "#444444"

# bước: (tên, [dòng mô tả], [dòng dữ liệu ra], trạng thái: live = đo khi chạy camera, frame = đo trên khung NV12 thật, none = chưa đo)
S = {
    0: (["OV13855 cảm biến"], ["13 MP, kèm VCM DW9714"], ["Bayer RAW10, 4224x3136,", "30 khung/giây"], "live"),
    1: (["D-PHY + CSI-2 host"], ["MIPI, 1080 Mbps mỗi lane"], ["luồng pixel RAW10"], "live"),
    2: (["VICAP (rkcif)"], ["thu nhận"], ["RAW10"], "live"),
    3: (["ISP (rkisp0)"], ["Bayer sang YUV, khử nhiễu"], ["NV12 (và NV16, UYVY...)"], "live"),
    4: (["RGA hoặc CPU"], ["resize, đổi màu,", "viền 114"], ["RGB888 640x640x3"], "frame"),
    5: (["NPU, 3 lõi"], ["RKNN INT8"], ["tensor thô"], "frame"),
    6: (["CPU"], ["giải mã hộp,", "lọc, NMS"], ["hộp + lớp"], "frame"),
    7: (["CPU"], ["ByteTrack"], ["hộp + mã số"], "none"),
    8: (["VOP hoặc bộ mã", "hóa video"], ["hiển thị, lưu", "hoặc phát"], ["màn hình hoặc", "luồng nén"], "none"),
}


def stage_box(f, n, x, y, w):
    title, sub, out, state = S[n]
    fill = {"live": MEAS_FILL, "frame": LIVE_FILL, "none": "white"}[state]
    dash = ' stroke-dasharray="5 3"' if state == "none" else ""
    stroke = LIVE_STROKE if state == "frame" else "#333333"
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{BH}" rx="5" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1.3"{dash}/>')
    cx, ty = x + w / 2, y + 16
    for ln in title:
        f.text(cx, ty, ln, size=16, weight=700, anchor="middle")
        ty += 18
    for ln in sub:
        f.text(cx, ty + 2, ln, size=13.5, anchor="middle")
        ty += 16
    sep = y + BH - 46
    f.a(f'<path d="M{x + 12} {sep} L{x + w - 12} {sep}" stroke="#AAAAAA" stroke-width="0.8"/>')
    oy = sep + 14
    for ln in out:
        f.text(cx, oy, ln, size=13.5, anchor="middle", fill=TEXT2, italic=True)
        oy += 16
    f.badge(x, y, str(n), BADGE)


def frame(f, x, y, w, h):
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#F7F7F7" stroke="#BBBBBB" '
        f'stroke-width="1.3"/>')


def fig_path():
    inner = W - 2 * M
    # hàng 1: bốn hộp rộng 180, ba khoảng 93
    w1 = 180
    gap1 = (inner - 4 * w1) / 3
    xs1 = [M + i * (w1 + gap1) for i in range(4)]
    # hàng 2: năm hộp rộng 160, các khoảng 30 (qua DDR), 30, 50 (6 sang 7), 90 (7 sang 8)
    w2 = 160
    gaps2 = [36, 36, 40, 88]
    xs2, x = [], M
    for i in range(5):
        xs2.append(x)
        x += w2 + (gaps2[i] if i < 4 else 0)
    assert abs(x - (W - M)) < 1, x

    y_leg = 12
    y_f1 = 54
    y_b1 = y_f1 + 34
    y_ddr = y_b1 + BH + 66
    y_f2 = y_ddr + 40 + 42
    y_b2 = y_f2 + 34
    H = y_f2 + 34 + BH + 14 + 56
    f = Fig(W, H)

    # chú thích ngay dưới đầu hình
    x = M
    for color, width, label, kw in ((INK, THIN, "truyền giữa hai khối", 0),
                                    (BLUE, ARROW, "ghi, đọc qua DDR", 0)):
        f.line([(x, y_leg + 12), (x + 34, y_leg + 12)], color, width)
        f.text(x + 44, y_leg + 12, label, size=13.5, anchor="start")
        x += 44 + len(label) * 6.4 + 28
    for fill, stroke, dash, label in ((MEAS_FILL, "#333333", "", "đo khi chạy camera"),
                                      (LIVE_FILL, LIVE_STROKE, "", "đo trên khung thật"),
                                      ("white", "#333333", ' stroke-dasharray="5 3"', "chưa đo")):
        f.a(f'<rect x="{x}" y="{y_leg + 4}" width="30" height="16" rx="3" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="1.2"{dash}/>')
        f.text(x + 40, y_leg + 12, label, size=13.5, anchor="start")
        x += 40 + len(label) * 6.4 + 24

    # hàng 1
    frame(f, M - 14, y_f1, inner + 28, 34 + BH + 14)
    f.text(M, y_f1 + 16, "Thu nhận ảnh, bước 0 đến 3 (đo khi chạy camera)", size=14, weight=700, fill=DARK)
    for i in range(4):
        stage_box(f, i, xs1[i], y_b1, w1)
    cy1 = y_b1 + BH / 2
    links1 = [(["MIPI D-PHY"]), (["luồng pixel"]), (["online: thẳng", "vào ISP,", "dma = 0"])]
    for i, lab in enumerate(links1):
        xa, xb = xs1[i] + w1, xs1[i + 1]
        f.line([(xa, cy1), (xb, cy1)], INK, THIN)
        top = cy1 - 12 - 15 * (len(lab) - 1)
        for k, ln in enumerate(lab):
            f.text((xa + xb) / 2, top + 15 * k, ln, size=13, anchor="middle", fill=DARK, halo="white")

    # thanh DDR
    f.a(f'<rect x="{M - 14}" y="{y_ddr}" width="{inner + 28}" height="40" rx="6" fill="#EEF2F8" '
        f'stroke="{BLUE}" stroke-width="1.6"/>')
    f.text(W / 2, y_ddr + 20, "DDR, bộ nhớ dùng chung (từ ISP trở đi mọi khối trao đổi qua bộ đệm trong DDR)",
           size=15, weight=700, fill=OUT_COLOR, anchor="middle")

    # ISP ghi NV12
    xi = xs1[3] + w1 / 2
    f.line([(xi, y_b1 + BH), (xi, y_ddr)], BLUE, ARROW)
    f.text(xi - 14, (y_b1 + BH + y_ddr) / 2 + 8, "ghi bộ đệm NV12 vào DDR", size=13, anchor="end", fill=DARK)

    # hàng 2
    frame(f, M - 14, y_f2, inner + 28, 34 + BH + 14)
    f.text(W - M, y_f2 + 16, "Xử lý, theo dõi, xuất, bước 4 đến 8 (4 đến 6 đo trên khung thật)", size=14, weight=700, fill=DARK,
           anchor="end")
    for i in range(5):
        stage_box(f, 4 + i, xs2[i], y_b2, w2)
    ya, yb = y_ddr + 40, y_b2
    ylab = ya + 20
    # (x offset, hướng, nhãn): xuống = đọc từ DDR, lên = ghi vào DDR
    arrows = {
        4: [(30, "down", "đọc NV12"), (124, "up", "ghi RGB888")],
        5: [(30, "down", "đọc RGB888"), (124, "up", "ghi tensor thô")],
        6: [(30, "down", "CPU đọc tensor từ DDR")],
    }
    for n, lst in arrows.items():
        for dx, d, lab in lst:
            ax = xs2[n - 4] + dx
            pts = [(ax, ya), (ax, yb)] if d == "down" else [(ax, yb), (ax, ya)]
            f.line(pts, BLUE, ARROW)
            f.text(ax + 11, ylab, lab, size=13, anchor="start", fill=DARK)

    cy2 = y_b2 + BH / 2
    f.line([(xs2[2] + w2, cy2), (xs2[3], cy2)], INK, THIN)
    f.line([(xs2[3] + w2, cy2), (xs2[4], cy2)], INK, THIN)
    xm = (xs2[3] + w2 + xs2[4]) / 2
    for k, ln in enumerate(["dữ liệu trong", "bộ nhớ CPU"]):
        f.text(xm, cy2 - 24 + 15 * k, ln, size=13, anchor="middle", fill=DARK, halo="white")

    yb = y_f2 + 34 + BH + 14 + 12
    source(f, yb, "Đo trên board Orange Pi 5 (RK3588S), camera OV13855, ngày 2026-11-07 [T3 board]. "
                  "Bước 4 đến 6 đo trên khung NV12 chụp ra tệp, chưa chạy liên tục.")
    source(f, yb + 18, "Chiều đọc của bước 4 và 5 suy ra từ chiều ghi của bước trước [SL].")
    return f


def fig_ddr():
    f = Fig(W, 420)
    inner = W - 2 * M
    y_leg, y_box, bh = 12, 62, 70
    y_ic, y_ddr = 196, 288
    # chú thích
    x = M
    f.line([(x, y_leg), (x, y_leg + 22)], BLUE, ARROW)
    f.text(x + 14, y_leg + 11, "ghi vào DDR", size=13.5, anchor="start")
    x += 14 + 11 * 6.4 + 36
    f.line([(x, y_leg + 22), (x, y_leg)], BLUE, ARROW)
    f.text(x + 14, y_leg + 11, "đọc từ DDR", size=13.5, anchor="start")
    x += 14 + 10 * 6.4 + 36
    f.a(f'<path d="M{x} {y_leg + 11} L{x + 34} {y_leg + 11}" stroke="{GRAY}" stroke-width="1.6" '
        f'stroke-dasharray="5 4" fill="none"/>')
    f.text(x + 46, y_leg + 11, "không đi vào DDR", size=13.5, anchor="start")

    # bảy khối
    w, gap = 130, 15
    blocks = [("ISP", "ghi NV12", "w"), ("RGA", "đọc, ghi", "rw"), ("NPU", "đọc, ghi", "rw"),
              ("CPU", "đọc, ghi", "rw"), ("VOP", "đọc khung", "r"), ("VPU", "đọc, ghi", "rw"),
              ("VICAP", "không ghi DDR", "x")]
    for i, (name, role, mode) in enumerate(blocks):
        bx = M + i * (w + gap)
        cx = bx + w / 2
        dash = ' stroke-dasharray="5 3"' if mode == "x" else ""
        f.a(f'<rect x="{bx}" y="{y_box}" width="{w}" height="{bh}" rx="5" fill="white" stroke="#333333" '
            f'stroke-width="1.3"{dash}/>')
        f.text(cx, y_box + 24, name, size=17, weight=700, anchor="middle")
        f.text(cx, y_box + 50, role, size=13.5, anchor="middle", fill=TEXT2)
        yb = y_box + bh
        if mode == "x":
            f.a(f'<path d="M{cx} {yb} L{cx} {yb + 34}" stroke="{GRAY}" stroke-width="1.6" '
                f'stroke-dasharray="5 4" fill="none"/>')
            f.a(f'<path d="M{cx - 7} {yb + 34} L{cx + 7} {yb + 48} M{cx + 7} {yb + 34} L{cx - 7} {yb + 48}" '
                f'stroke="{DARK}" stroke-width="2.2" fill="none"/>')
            continue
        offs = {"w": [(0, "down")], "r": [(0, "up")], "rw": [(-16, "down"), (16, "up")]}[mode]
        for dx, d in offs:
            ax = cx + dx
            pts = [(ax, yb), (ax, y_ic)] if d == "down" else [(ax, y_ic), (ax, yb)]
            f.line(pts, BLUE, ARROW)

    # interconnect và DDR
    f.a(f'<rect x="{M - 14}" y="{y_ic}" width="{inner + 28}" height="34" rx="6" fill="#EEEEEE" stroke="#999999" '
        f'stroke-width="1.3"/>')
    f.text(W / 2, y_ic + 17, "interconnect", size=15.5, weight=700, anchor="middle", fill=DARK)
    f.line([(W / 2, y_ic + 34), (W / 2, y_ddr)], GRAY, THIN, head=False)
    f.a(f'<rect x="{M - 14}" y="{y_ddr}" width="{inner + 28}" height="72" rx="6" fill="#EEF2F8" stroke="{BLUE}" '
        f'stroke-width="1.6"/>')
    f.text(W / 2, y_ddr + 25, "DDR, 4 GB trên board (MemTotal)", size=17, weight=700, anchor="middle", fill=OUT_COLOR)
    f.text(W / 2, y_ddr + 50, "xung 528, 1068, 1560, 2112 MHz, dmc_ondemand", size=14, anchor="middle", fill=TEXT2)

    yb = y_ddr + 72 + 12
    source(f, yb, "Đo trên board Orange Pi 5, ngày 2026-11-07 [T3 board, /proc/meminfo, /sys/class/devfreq/dmc]. "
                  "Dấu x: VICAP chưa cấp bộ đệm DDR trong luồng này [SL].")
    return f


def fig_ctrl():
    f = Fig(W, 372)
    y_top, th = 24, 74
    y_bot, bh = 206, 98
    # khối trên: rkaiq_3A_server
    tx, tw = 190, 680
    f.a(f'<rect x="{tx}" y="{y_top}" width="{tw}" height="{th}" rx="5" fill="white" stroke="#333333" stroke-width="1.3"/>')
    f.text(tx + tw / 2, y_top + 26, "rkaiq_3A_server", size=17, weight=700, anchor="middle", mono=True)
    f.text(tx + tw / 2, y_top + 54, "tiến trình người dùng, CPU [SL]", size=14, anchor="middle", fill=TEXT2)
    # hai khối dưới
    boxes = [(90, 380, "ISP (rkisp0)", ["vào: tham số", "ra: thống kê"]),
             (590, 380, "I2C bus 2", ["OV13855 địa chỉ 0x36", "VCM DW9714 địa chỉ 0x0c"])]
    for bx, bw, title, lines in boxes:
        f.a(f'<rect x="{bx}" y="{y_bot}" width="{bw}" height="{bh}" rx="5" fill="white" stroke="#333333" '
            f'stroke-width="1.3"/>')
        f.text(bx + bw / 2, y_bot + 24, title, size=17, weight=700, anchor="middle")
        for k, ln in enumerate(lines):
            f.text(bx + bw / 2, y_bot + 52 + 24 * k, ln, size=14, anchor="middle", fill=TEXT2)
    y0, y1 = y_top + th, y_bot
    ym = (y0 + y1) / 2
    # 1: tham số xuống ISP, 2: thống kê lên rkaiq, 3: điều khiển I2C
    f.line([(250, y0), (250, y1)], INK, THIN)
    f.line([(330, y1), (330, y0)], INK, THIN)
    f.line([(780, y0), (780, y1)], INK, THIN)
    for x, n in ((250, "1"), (330, "2"), (780, "3")):
        f.badge(x, ym, n, BADGE)
    f.text(250 - 18, ym, "tham số", size=13.5, anchor="end", fill=DARK)
    f.text(330 + 18, ym, "thống kê", size=13.5, anchor="start", fill=DARK)
    f.text(780 + 18, ym, "điều khiển", size=13.5, anchor="start", fill=DARK)
    source(f, y_bot + bh + 14, "Đo trên board Orange Pi 5, ngày 2026-11-07 [T3 board, media-ctl -d /dev/media1 -p, "
                               "/sys/bus/i2c/devices/2-0036, 2-000c]. Rkaiq chạy trên CPU là suy luận [SL].")
    return f


FIGURES = [("lcd-1-duong-di-cua-anh", fig_path), ("lcd-2-ai-doc-ghi-ddr", fig_ddr),
           ("lcd-3-mat-phang-dieu-khien", fig_ctrl)]

if __name__ == "__main__":
    run(FIGURES, DEFAULT_OUTDIR)
