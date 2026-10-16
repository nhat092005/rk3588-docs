#!/usr/bin/env python3
"""Phan 5 Toolchain: Hinh 5.1 den 5.3.

Primary sources (see chu-thich.md, table Nguon): UG232 (chuong 1, 2, 3, 5, 8, 10), API232, QS232, UG152, rknn_server_proxy.md,
rknn_api.h (HDR), rknn_lite.py (inside the lite2 wheel), examples of the toolkit, rknpu driver 0.9.8 (DRV), rk3588s.dtsi (DTS),
T3 logs (2026-09-18_board-bringup-log.md, 2026-10-10_t3-board-silu-resize/README.md).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
RB = "#EAF6EA"


def tier(f):
    f.tier(808, 8, "T1 RK3588")


def card(f, x, y, w, h, title, lines, size=12, title_size=15, dashed=False, mono_title=False, fill="white",
         stroke="#333333"):
    """Box: bold title then plain lines (all centred)."""
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=title_size, weight=700, anchor="middle", mono=mono_title)
    for i, ln in enumerate(lines):
        f.text(x + w / 2, y + 38 + 16 * i, ln, size=size, anchor="middle")


def panel(f, x, y, w, lines, fill="white", stroke="#999999", size=12.5, sw=1):
    """Left-aligned rich-text panel; lines: str or list of (text, kind) parts. Returns bottom y."""
    h = 14 + 19 * len(lines)
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"/>')
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + 16 + 19 * i, ln, size=size)
    return y + h


def call(f, x, y, w, h, name, sub="", n=None, sub_size=12.5):
    """API-call box: code title over a one-line sub; optional step badge."""
    f.box(x, y, w, h, name, sub, mono=True, title_size=15.5, sub_size=sub_size)
    if n:
        f.badge(x + 2, y + 2, str(n))


# =====================================================================
# Hinh 5.1: chuoi API
# =====================================================================
def fig_api():
    f = Fig(W, 1000)
    tier(f)
    # ---- A: conversion ----
    f.layer(10, 40, 880, 270, ["A. Chuyển ONNX sang RKNN trên PC (UG232 tr.9, Hình 3-1)"])
    xs = [24, 196, 368, 540, 712]
    names = ["RKNN()", "config()", "load_onnx()", "build()", "export_rknn()"]
    caps = [
        ["verbose, verbose_file", "API232 tr.6"],
        ["mean_values, std_values,", "target_platform", "API232 tr.6, 8"],
        ["model: đường dẫn .onnx", "API232 tr.12"],
        ["do_quantization, dataset", "API232 tr.14"],
        ["export_path: file .rknn", "API232 tr.15"],
    ]
    for i, (x, nm, cp) in enumerate(zip(xs, names, caps), 1):
        call(f, x, 78, 144, 48, nm, n=i)
        for j, ln in enumerate(cp):
            hot = (i == 2 and ln == "target_platform")
            f.text(x + 72, 143 + 15.5 * j, ln, size=11.5, anchor="middle", fill=BLUE if hot else DARK,
                   weight=700 if hot else 400)
        if i < 5:
            f.line([(x + 144, 102), (x + 172, 102)], BLUE)
    f.a('<rect x="24" y="200" width="832" height="96" rx="6" fill="white" stroke="#1E5BB8" stroke-width="1.6"/>')
    f.rich(38, 217, [("config() phải đặt ", "t"), ("target_platform='rk3588'", "c"), (" (UG232 tr.173).", "t")], size=13.5)
    f.text(38, 238, "Nếu không đặt, model chỉ chạy được trên RK3566/RK3568; ví dụ yolov5 của toolkit đặt 'rk3566'"
           " ở dòng 242.", size=12.5)
    f.text(38, 257, "Thứ tự theo UG232 tr.9: Configuration, Loading, Building, Export; API232 tr.6: config trước khi build.",
           size=12.5, fill=DARK)
    f.rich(38, 278, [("Model build cho RK3588 dùng được trên RK3588S (UG232 tr.158); \"RK3588\" trong tài liệu"
                          " chỉ cả RK3588/RK3588S (UG232 tr.10).", "t")], size=12.5, fill=DARK)

    # ---- B: run and measure (group shifted down 16) ----
    f.a('<g transform="translate(0,16)">')
    f.layer(10, 310, 880, 345, ["B. Chạy thử và đo trên PC (UG232 tr.29, 31; API232 tr.16 đến 19)"])
    call(f, 28, 420, 172, 62, "init_runtime()", "chọn nơi chạy", n=6)
    f.box(280, 354, 260, 66, "target=None", "mặc định: simulator trên PC", mono=True, title_size=15, sub_size=12.5)
    f.box(280, 446, 260, 66, "target='rk3588'", "NPU trên board nối PC", mono=True, title_size=15, sub_size=12.5)
    f.line([(200, 440), (240, 440), (240, 387), (278, 387)], BLUE)
    f.line([(200, 462), (240, 462), (240, 479), (278, 479)], BLUE)
    call(f, 590, 400, 140, 50, "inference()", n=7)
    call(f, 590, 478, 140, 48, "eval_perf()", n=7)
    call(f, 766, 442, 108, 50, "release()", n=8)
    f.line([(540, 387), (566, 387), (566, 420), (588, 420)], BLUE)
    f.line([(540, 462), (566, 462), (566, 436), (588, 436)], BLUE)
    f.line([(540, 495), (588, 495)], BLUE)
    f.line([(730, 425), (748, 425), (748, 458), (764, 458)], BLUE)
    f.line([(730, 502), (748, 502), (748, 476), (764, 476)], BLUE)
    ys = 540
    for i, ln in enumerate([
        [("target=None: phải gọi build hoặc hybrid_quantization trước init_runtime (API232 tr.16).", "t")],
        [("eval_perf, eval_memory: model phải chạy trên chip nối với PC (API232 tr.18, 19); ", "t"),
         ("fix_freq", "c"), (" mặc định True.", "t")],
        [("perf_debug=True", "c"), (" ở init_runtime mới có thời gian từng lớp; nếu không chỉ có tổng (API232 tr.16).", "t")],
        [("load_rknn() thay cho config, load, build; model nạp sẵn không dùng được với simulator (API232 tr.15).", "t")],
        [("Ví dụ chính thức: yolov5 test.py:271 gọi ", "t"), ("init_runtime()", "c"),
         (" không có target, nên chạy trên simulator.", "t")],
    ]):
        f.rich(28, ys + 1 + 19 * i, ln, size=12.5)
    f.a('</g>')

    # ---- unknown + legend ----
    y = f.unknown(10, 686, [
        "phiên bản ONNX: API232 tr.5 ghi \"1.7.0 ~1.17.0\", UG232 tr.21 ghi \"1.7.0~1.10.0\"; chưa có nguồn phân xử;",
        "ví dụ \"ONNX loading\" ở UG232 tr.24 lại gọi rknn.load_tflite; dùng API232 tr.12 (load_onnx) để tra tên hàm;",
        "mức lệch giữa kết quả simulator và board (UG232 tr.171 chỉ nói \"may not be consistent\")."], w=880)
    y = f.legend(10, y + 12, 880, [
        ("blue", "thứ tự gọi API (số trong vòng tròn là bước)"),
        ("badge", "bước 1 đến 8; bước 7 là inference hoặc eval_perf"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho, hoặc hai tài liệu nói khác nhau"),
    ])
    source(f, y + 8, "Nguồn: UG232 tr.9, 10, 21, 24, 29, 31, 158, 171, 173; API232 tr.5, 6, 8, 12, 14 đến 19; "
           "examples/onnx/yolov5/test.py:238-271.")
    return f


# =====================================================================
# Hinh 5.2: che do chay
# =====================================================================
def lane_title(f, x, w, text):
    f.layer(x, 40, w, 384, [text])


def fig_modes():
    f = Fig(W, 1500)
    tier(f)
    LW = 286
    X = [10, 307, 604]
    titles = ["1. Simulator trên PC", "2. PC nối board", "3. Trên board"]
    for x, t in zip(X, titles):
        lane_title(f, x, LW, t)
    # ---- lane 1 ----
    x = X[0] + 16
    card(f, x, 76, 254, 66, "RKNN-Toolkit2 (PC)", ["init_runtime(), target=None"], size=12, title_size=14.5)
    f.line([(x + 127, 142), (x + 127, 182)], BLUE)
    card(f, x, 184, 254, 66, "simulator", ["trên Linux x86_64, không cần board"], size=12, title_size=14.5)
    for i, ln in enumerate(["Kết quả có thể khác board:", "mức lệch là unknown.",
                            "Có thể lấy kết quả suy luận", "khi chưa có board."]):
        f.text(x + 4, 276 + 17 * i, ln, size=12.5, fill=DARK if i < 2 else INK)
    # ---- lane 2 ----
    x = X[1] + 16
    card(f, x, 76, 254, 56, "RKNN-Toolkit2 (PC)", ["init_runtime(target='rk3588')"], size=12, title_size=14.5)
    f.line([(x + 127, 132), (x + 127, 166)], BLUE)
    f.text(x + 137, 149, "adb (USB hoặc mạng)", size=12, fill=BLUE)
    card(f, x, 168, 254, 52, "rknn_server (board)", ["proxy nhận lệnh từ PC"], size=12, title_size=14.5)
    f.line([(x + 127, 220), (x + 127, 250)], BLUE)
    f.text(x + 137, 235, "gọi RKNPU2 C API", size=12, fill=BLUE)
    card(f, x, 252, 254, 52, "librknnrt.so (board)", ["RKNPU2 Runtime"], size=12, title_size=14.5)
    f.line([(x + 127, 304), (x + 127, 328)], BLUE)
    card(f, x, 330, 254, 44, "NPU", [], title_size=14.5)
    f.text(x + 127, 392, "Kết quả gửi về PC; thêm bước sao chép", size=12, anchor="middle", fill=DARK)
    f.text(x + 127, 408, "và truyền dữ liệu (UG232 tr.171)", size=12, anchor="middle", fill=DARK)
    # ---- lane 3 ----
    x = X[2] + 16
    card(f, x, 76, 254, 66, "Ứng dụng trên board", ["RKNN-Toolkit-Lite2 (Python)", "hoặc C API"], size=12,
         title_size=14.5)
    f.line([(x + 127, 142), (x + 127, 176)], BLUE)
    card(f, x, 178, 254, 52, "librknnrt.so (board)", ["RKNPU2 Runtime"], size=12, title_size=14.5)
    f.line([(x + 127, 230), (x + 127, 254)], BLUE)
    card(f, x, 256, 254, 44, "NPU", [], title_size=14.5)
    f.a(f'<rect x="{x}" y="316" width="254" height="98" rx="4" fill="{UNK_FILL}" stroke="{RED}" stroke-width="1.3" '
        f'stroke-dasharray="5 3"/>')
    for i, ln in enumerate([[("unknown: ", "b"), ("RKNN-Toolkit-Lite2 có cần", "t")],
                            "rknn_server hay không; không có",
                            "câu nào nói trực tiếp. rknn_server",
                            "là proxy nhận lệnh từ PC qua USB",
                            "(UG232 tr.16)."]):
        f.rich(x + 8, 332 + 17 * i, ln, size=12)

    # ---- comparison table ----
    f.text(10, 446, "So sánh ba chế độ", size=15, weight=700)
    f.table(10, 460, [130, 250, 250, 250], ["Mục", "Simulator", "PC nối board", "Trên board"], [
        ["init_runtime", ("lines", ["target=None", "(mặc định, API232 tr.16)"]),
         ("lines", ["target='rk3588'", "(UG232 tr.29)"]),
         ("lines", ["Lite2: init_runtime(core_mask=...)", "không đặt target (UG232 tr.39)"])],
        ["eval_perf", ("lines", ["cần model chạy trên chip", "nối với PC (API232 tr.18)"]),
         ("lines", ["có (API232 tr.18)"]),
         ("lines", ["RKNNLite không có hàm eval_perf;", "log từng lớp: RKNN_LOG_LEVEL=4", "hoặc RKNNLite(verbose=True)"])],
        ["Tốc độ", ("lines", ["tài liệu khuyên dùng board nối PC", "hoặc trên board hơn (UG232 tr.171)"]),
         ("lines", ["chậm hơn C API trên board", "vì sao chép và truyền dữ liệu"]),
         ("lines", ["hiệu năng thực của NPU", "lấy theo C API trên board"])],
    ], size=12, line_h=16)
    # ---- version rule and prerequisites ----
    y = 646
    y = panel(f, 10, y, 880, [
        [("Phiên bản: ", "b"), ("RKNN Server, Runtime library và RKNN-Toolkit2 phải cùng phiên bản (UG232 tr.17).", "t")],
        [("Chuẩn bị nối board: ", "b"), ("thường cần cập nhật rknn_server và librknnrt.so trên board rồi khởi động "
                                       "rknn_server bằng tay (rknn_server_proxy.md dòng 6).", "t")],
        [("Khởi động: ", "b"), ("nohup /usr/bin/rknn_server >/dev/null& (UG232 tr.16); lỗi \"The rknn_server on the "
                              "connected device is abnormal\" nghĩa là chưa chạy (QS232 tr.29).", "t")],
        [("RKNN-Toolkit2 bản ARM64: ", "b"), ("cài trên board, không cần adb và RKNN Server (UG232 tr.11, 16, 17); "
                                            "cần librknnrt.so.", "t")],
    ], size=12.5)
    # ---- T3 ----
    f.tier(10, y + 16, "T3 đo")
    f.text(100, y + 27, "Log nối board từ PC (2026-09-18) và log đo (2026-10-10), Orange Pi 5", size=12.5,
           fill=DARK)
    y = panel(f, 10, y + 44, 880, [
        "Board có librknnrt 2.3.0, PC dùng rknn-toolkit2 2.3.2: log ghi đây là nguyên nhân lỗi kết nối. Đẩy",
        "librknnrt.so 2.3.2 lên /usr/lib, khởi động lại rknn_server; get_sdk_version() ra 2.3.2 ở cả ba chỗ.",
        "Log ghi: nếu init_runtime báo device not found, chạy tay adb connect <ip>:5555 bằng adb đi kèm toolkit.",
        "adb hệ thống v41 thay adb server v40 của toolkit làm lần chạy đầu thất bại; dùng adb của toolkit.",
    ], fill=RB, stroke="#2E7D32")
    y = f.unknown(10, y + 12, [
        "chỗ đặt librknnrt.so: UG232 tr.18 lệnh push tới /usr/lib64, QS232 tr.17 và rknn_server_proxy.md dòng 103 tới",
        "/usr/lib; log T3 chỉ cho biết board này có /usr/lib/librknnrt.so, không phân xử hai tài liệu;",
        "giao thức NTB của list_devices (API232 tr.23 chỉ nêu có hai chế độ ADB và NTB);",
        "độ trễ eval_perf qua board nối PC so với C API trên board (UG232 tr.175 chỉ so rknn.inference với eval_perf)."],
        w=880)
    y = f.legend(10, y + 12, 880, [
        ("blue", "gọi hàm, truyền lệnh hoặc dữ liệu"),
        ("fill:" + RB, "T3: ghi trong log có trên đĩa"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho, hoặc hai tài liệu nói khác nhau"),
    ])
    source(f, y + 8, "Nguồn: UG232 tr.11, 16, 17, 18, 29, 39, 74, 171, 175; API232 tr.16, 18, 23; QS232 tr.17, 29; "
           "rknn_server_proxy.md; LOG 2026-09-18, 2026-10-10.")
    return f


# =====================================================================
# Hinh 5.3: stack tren board
# =====================================================================
def fig_stack():
    f = Fig(W, 1700)
    tier(f)
    # ---- layer 1: application ----
    f.layer(10, 40, 880, 138, ["ỨNG DỤNG", "UG232 tr.8, 36"], side=True)
    card(f, 140, 52, 360, 114, "Python: RKNNLite", [
        "RKNN-Toolkit-Lite2, chỉ nạp và chạy .rknn",
        "RKNNLite(), load_rknn(), inference(),",
        "init_runtime(core_mask=...), release()",
        "UG232 tr.37 đến 39; không convert"], size=11.5, title_size=15)
    card(f, 520, 52, 360, 114, "C/C++: RKNPU2 C API", [
        "rknn_init, rknn_set_core_mask,",
        "rknn_inputs_set, rknn_run,",
        "rknn_outputs_get, rknn_destroy",
        "rknn_api.h"], size=11.5, title_size=15)
    # ---- layer 2: runtime ----
    f.layer(10, 208, 880, 126, ["RUNTIME", "UG232 tr.8, 155"], side=True)
    card(f, 140, 220, 740, 102, "librknnrt.so (RKNPU2 Runtime)", [
        "Nạp RKNN model và gọi NPU driver để chạy model trên NPU (UG232 tr.8).",
        "RKNN-Toolkit-Lite2 và RKNPU2 C API đều dựa vào file này (UG232 tr.155).",
        "Node /dev/dri/renderD129 là node NPU của RK3588; Runtime dựa vào nó để bật NPU (UG232 tr.155)."],
         size=12, title_size=15.5, mono_title=False)
    f.line([(320, 166), (320, 218)], BLUE)
    f.line([(700, 166), (700, 218)], BLUE)
    # ---- layer 3: driver ----
    f.layer(10, 364, 880, 232, ["DRIVER", "rknpu 0.9.8", "(kernel)"], side=True)
    cw, gap, y0 = 140, 10, 376
    cards = [
        ("ioctl", ["ACTION, SUBMIT,", "MEM_CREATE, MEM_MAP,", "MEM_DESTROY, MEM_SYNC", "tiền tố RKNPU_",
                   "rknpu_ioctl.h"]),
        ("job", ["rknpu_submit tạo job,", "xếp vào todo_list của", "từng core theo core_mask;", "ngắt báo job xong",
                 "Hình 2.4"]),
        ("devfreq", ["governor rknpu_ondemand", "(driver đăng ký);", "UG152: đổi sang userspace", "để cố định tần số",
                     "rknpu_devfreq.c"]),
        ("iommu", ["DTS: iommus =", "<&rknpu_mmu>; driver dùng", "iommu mode khi có entry", "và node khả dụng",
                   "rknpu_drv.c"]),
        ("power", ["mỗi ioctl: power_get", "trước, power_put_delay", "sau; mặc định trễ", "3000 ms",
                   "rknpu_drv.c"]),
    ]
    for i, (t, ls) in enumerate(cards):
        card(f, 140 + i * (cw + gap), y0, cw, 124, t, ls, size=10 if t == "ioctl" else 11, title_size=14.5)
    f.text(140, 520, "Driver đăng ký các node rknpu/* (debugfs hoặc procfs): version, load, power, freq, volt, delayms, reset;",
           size=12.5)
    f.text(140, 538, "mm chỉ khi CONFIG_ROCKCHIP_RKNPU_SRAM (rknpu_debugger.c:304-316). Bảng node ở dưới.", size=12.5)
    f.line([(320, 334), (320, 362)], BLUE)
    f.line([(700, 334), (700, 362)], BLUE)
    f.text(332, 348, "dùng node /dev/dri/renderD129", size=12, fill=BLUE)
    # ---- layer 4: hardware ----
    f.layer(10, 626, 880, 90, ["PHẦN CỨNG", "NPU"], side=True)
    card(f, 140, 638, 740, 66, "NPU: 3 core, mỗi core một ngắt", [
        "Cấu hình thanh ghi theo PC mode: Hình 2.5. Cấu trúc core: Hình 2.2."], size=12, title_size=15)
    f.line([(260, 596), (260, 636)], BLUE)
    f.text(272, 608, "ghi thanh ghi (rknpu_job_subcore_commit_pc)", size=12, fill=BLUE)
    f.line([(780, 636), (780, 598)], INK)
    f.text(768, 608, "ngắt (rknpu_irq_handler)", size=12, fill=INK, anchor="end")

    # ---- node table ----
    f.text(10, 744, "Node rknpu/* và devfreq: hỏi gì, nguồn nào, giá trị đo", size=15, weight=700)
    f.tier(500, 732, "T3 đo")
    f.text(580, 743, "cột phải: đọc bằng sudo 2026-10-10", size=12, fill=DARK)
    widths = [130, 320, 230, 200]
    rows = [
        ["version", ("lines", ["phiên bản driver", "(UG232 tr.15, 137: node version)"]),
         ("lines", ["UG232 tr.15, 137; UG152 tr.74", "rknpu_debugger.c:31-37"]), "RKNPU driver: v0.9.8"],
        ["load", ("lines", ["phần trăm thời gian NPU chạy tác vụ (UG232", "tr.137); từng core (UG152 tr.73)"]),
         ("lines", ["UG232 tr.137; UG152 tr.73, 74", "rknpu_debugger.c:39-76"]),
         ("lines", ["NPU load:  Core0:  0%,", "Core1:  0%, Core2:  0%,"])],
        ["power", ("lines", ["on hoặc off; ghi on, off để bật,", "tắt nguồn NPU (UG152 tr.74)"]),
         ("lines", ["UG152 tr.74", "rknpu_debugger.c:78-130"]), "off"],
        ["freq", ("lines", ["tần số NPU (Hz); ghi để đặt", "(UG152 tr.74)"]),
         ("lines", ["UG152 tr.74", "rknpu_debugger.c:177-245"]), "1000000000"],
        ["volt", ("lines", ["điện áp NPU", "(UG152 tr.75)"]),
         ("lines", ["UG152 tr.75", "rknpu_debugger.c:247-260"]), "812500"],
        ["delayms", ("lines", ["trễ tắt nguồn, đơn vị ms", "(UG152 tr.75)"]),
         ("lines", ["UG152 tr.75", "rknpu_debugger.c:132-175"]), "3000"],
        ["devfreq", ("lines", ["cur_freq, governor của", "/sys/class/devfreq/fdab0000.npu"]),
         ("lines", ["UG152 tr.72, 73"]), "chưa có log"],
    ]
    # green background under the T3 column (drawn first; table text goes on top)
    ty = 756
    hh = 28
    tot = hh
    for r in rows:
        n = max(len(c[1]) if isinstance(c, tuple) else 1 for c in r)
        tot += 9 + 16 * n
    f.a(f'<rect x="{10 + sum(widths[:3])}" y="{ty + hh}" width="{widths[3]}" height="{tot - hh}" fill="{RB}"/>')
    ybot = f.table(10, ty, widths, ["Node", "Hỏi gì", "Nguồn", "Giá trị T3"], rows, size=12, line_h=16)
    y = panel(f, 10, ybot + 12, 880, [
        [("UG232 tr.137: ", "b"), ("\"the NPU load does not directly represent the actual MAC utilization\".", "t")],
        [("power, freq, volt, delayms ", "b"), ("chỉ có ở UG152 (driver sau 0.7.2 và sau 0.8.2), UG232 không nhắc lại.", "t")],
        [("Log T3 chỉ ghi giá trị, ", "b"), ("không ghi NPU đang làm gì lúc đọc; không suy ra tải hay nhàn rỗi.", "t")],
    ], size=12.5)
    y = f.unknown(10, y + 12, [
        "librknnrt gọi ioctl nào theo thứ tự nào: trong cây chỉ có librknnrt.so nhị phân, không có mã nguồn;",
        "vì sao UG232 không còn nhắc node power, freq, volt, delayms;",
        "UG232 tr.15 liệt kê cả node driver_version, nhưng chuỗi này không có trong mã driver 0.9.8 (chỉ version)."],
        w=880)
    y = f.legend(10, y + 12, 880, [
        ("blue", "lời gọi, ioctl, ghi thanh ghi (từ trên xuống)"),
        ("ink", "tín hiệu từ NPU về host (ngắt)"),
        ("fill:" + RB, "T3: ghi trong log có trên đĩa"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source(f, y + 8, "Nguồn: UG232 tr.8, 15, 36 đến 40, 137, 155; UG152 tr.72 đến 75; rknn_api.h:489, 512, 527, 542, 558-577, 589, 619; "
           "DRV rknpu 0.9.8; DTS dòng 3478; LOG 2026-10-10.")
    return f


FIGS = [
    ("h5-1-chuoi-api", fig_api),
    ("h5-2-che-do-chay", fig_modes),
    ("h5-3-stack-board", fig_stack),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
