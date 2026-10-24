#!/usr/bin/env python3
"""Chuyên đề: Lượng tử hóa RKNN (02-rknn-luong-tu-hoa).

Sinh hình vector SVG minh họa:
  1. quant-01-symmetric-vs-asymmetric:
     Trực quan hóa ánh xạ trục số lượng tử hóa Symmetric (Z=0) vs Asymmetric (Z!=0).
     Minh họa phân phối dữ liệu thực, bước lượng tử hóa và công thức phần cứng NPU MAC.
  2. quant-02-per-tensor-vs-per-channel:
     Trực quan hóa khối tensor 3D so sánh 1 scale toàn tensor vs scale độc lập từng channel.
     Minh họa phân bổ 256 mức lượng tử INT8 giải quyết triệt để lỗi underflow.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "02-nen-tang-rk3588", "02-rknn-luong-tu-hoa"
    )
)

W = 880
BOX_STROKE = "#334155"
ORANGE = "#D97706"


def tier(f, label="T1 RK3588", x=W - 130, y=14):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    r_attr = f' rx="{rx}" ry="{rx}"' if rx else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"{r_attr} fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH SYMMETRIC VS ASYMMETRIC (quant-01-symmetric-vs-asymmetric)
# ==============================================================================
def fig_symmetric_vs_asymmetric():
    card_h = 304
    y_top = 44
    H = 370
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Cơ chế ánh xạ lượng tử hóa INT8 trên RKNPU: Symmetric vs Asymmetric",
           size=14, weight=700, fill=DARK)

    card_w = 415
    x1 = 18
    x2 = 447

    # --------------------------------------------------------------------------
    # CỘT TRÁI: SYMMETRIC QUANTIZATION (ĐỐI XỨNG - Z = 0)
    # --------------------------------------------------------------------------
    rect(f, x1, y_top, card_w, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x1, y_top, card_w, 26, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x1 + 8, y_top + 4, 6, 18, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x1 + 22, y_top + 14, "A. Lượng tử hóa đối xứng (Symmetric: Z = 0)",
           size=10.5, weight=700, fill="#1E40AF")

    f.text(x1 + 14, y_top + 36, "Miền thực FP32 đối xứng qua 0: [-M, +M] với M = max(|x_min|, |x_max|)",
           size=8.2, weight=700, fill="#1E3A8A")
    f.text(x1 + 14, y_top + 48, "Công thức ánh xạ: q = round(x / S) | S = M / 127 | Z = 0",
           size=8, fill="#334155")

    # Trục số thực FP32
    ax_y1 = y_top + 78
    ax_x0 = x1 + 36
    ax_w = card_w - 72

    rect(f, ax_x0, ax_y1, ax_w, 3, fill="#64748B", stroke="#64748B", rx=1)
    rect(f, ax_x0, ax_y1 - 6, 2, 15, fill="#DC2626", stroke="#DC2626")
    f.text(ax_x0, ax_y1 - 12, "-M", size=8, weight=700, fill="#DC2626", anchor="middle")

    mid_ax1 = ax_x0 + ax_w / 2
    rect(f, mid_ax1, ax_y1 - 6, 2, 15, fill=BLUE, stroke=BLUE)
    f.text(mid_ax1, ax_y1 - 12, "0.0 (Float)", size=8, weight=700, fill=BLUE, anchor="middle")

    rect(f, ax_x0 + ax_w, ax_y1 - 6, 2, 15, fill="#059669", stroke="#059669")
    f.text(ax_x0 + ax_w, ax_y1 - 12, "+M", size=8, weight=700, fill="#059669", anchor="middle")

    # Mũi tên ánh xạ
    arrow(f, mid_ax1, ax_y1 + 10, mid_ax1, ax_y1 + 34, color=BLUE, sw=THIN)
    f.text(mid_ax1 + 8, ax_y1 + 24, "Zero điểm thực trùng khớp 0 điểm nguyên", size=7.5, weight=700, fill=BLUE)

    # Trục số nguyên INT8
    ax_y2 = ax_y1 + 44
    rect(f, ax_x0, ax_y2, ax_w, 3, fill=BLUE, stroke=BLUE, rx=1)
    rect(f, ax_x0, ax_y2 - 6, 2, 15, fill="#DC2626", stroke="#DC2626")
    f.text(ax_x0, ax_y2 + 16, "-127", size=8, weight=700, fill="#DC2626", anchor="middle")

    rect(f, mid_ax1, ax_y2 - 6, 2, 15, fill=BLUE, stroke=BLUE)
    f.text(mid_ax1, ax_y2 + 16, "q = 0 (INT8)", size=8, weight=700, fill=BLUE, anchor="middle")

    rect(f, ax_x0 + ax_w, ax_y2 - 6, 2, 15, fill="#059669", stroke="#059669")
    f.text(ax_x0 + ax_w, ax_y2 + 16, "+127", size=8, weight=700, fill="#059669", anchor="middle")

    # Khối công thức thực thi phần cứng MAC NPU
    mac_y1 = ax_y2 + 28
    rect(f, x1 + 14, mac_y1, card_w - 28, 48, fill="#EFF6FF", stroke="#2563EB", sw=1.1, rx=3)
    f.text(x1 + card_w / 2, mac_y1 + 13, "Biểu thức tích chập phần cứng NPU (Không phát sinh bù Zero):",
           size=8.2, weight=700, fill="#1E40AF", anchor="middle")
    f.text(x1 + card_w / 2, mac_y1 + 27, "y = S_w · S_x · ∑_{i=0}^{k-1} (w_i · x_i)",
           size=9.2, weight=700, fill="#1E3A8A", anchor="middle")
    f.text(x1 + card_w / 2, mac_y1 + 40, "→ Tính toán thuần túy trên mảng MAC INT8; 0 chu kỳ trễ bù trừ",
           size=7.5, fill="#166534", anchor="middle")

    # Khung phân tích hiệu năng & khuyến nghị
    perf_y1 = mac_y1 + 54
    rect(f, x1 + 14, perf_y1, card_w - 28, 58, fill="#FFFFFF", stroke="#2563EB", rx=3)
    f.text(x1 + 24, perf_y1 + 13, "Đặc tính phần cứng RKNPU Core:", size=8.2, weight=700, fill="#1E40AF")
    f.text(x1 + 24, perf_y1 + 27, "• Tiết kiệm triệt để thanh ghi và logic cộng offset.", size=7.8, fill="#334155")
    f.text(x1 + 24, perf_y1 + 40, "• Chuẩn mặc định cho toàn bộ Weight của các mô hình YOLO.", size=7.8, fill="#15803D")
    f.text(x1 + 24, perf_y1 + 51, "• Dải biểu diễn đối xứng [-127, 127] tối ưu hóa cho phân bố Gauss.", size=7.5, fill="#64748B")

    # Thẻ tóm tắt đáy
    bot_y = perf_y1 + 58 + 8
    rect(f, x1 + 14, bot_y, card_w - 28, 20, fill="#EFF6FF", stroke=BLUE, rx=2)
    f.text(x1 + card_w / 2, bot_y + 11, "Z = 0 → Tối ưu phần cứng tối đa, tốc độ MAC cao nhất",
           size=7.5, weight=700, fill="#1E40AF", anchor="middle")

    # --------------------------------------------------------------------------
    # CỘT PHẢI: ASYMMETRIC QUANTIZATION (BẤT ĐỐI XỨNG - Z ≠ 0)
    # --------------------------------------------------------------------------
    rect(f, x2, y_top, card_w, card_h, fill="#F8FAFC", stroke=ORANGE, sw=1.3, rx=6)
    rect(f, x2, y_top, card_w, 26, fill="#FFFBEB", stroke=ORANGE, sw=1.0, rx=6)
    rect(f, x2 + 8, y_top + 4, 6, 18, fill=ORANGE, stroke=ORANGE, sw=1, rx=2)
    f.text(x2 + 22, y_top + 14, "B. Lượng tử hóa bất đối xứng (Asymmetric / Affine: Z ≠ 0)",
           size=10.5, weight=700, fill="#92400E")

    f.text(x2 + 14, y_top + 36, "Miền thực FP32 lệch trục: [x_min, x_max] (ví dụ sau hàm kích hoạt ReLU)",
           size=8.2, weight=700, fill="#92400E")
    f.text(x2 + 14, y_top + 48, "Công thức ánh xạ: q = round(x / S) + Z | S = (x_max - x_min) / 255 | Z ≠ 0",
           size=8, fill="#334155")

    # Trục số thực FP32 (lệch: x_min = 0, x_max = 6)
    bx_x0 = ax_x0 + 429
    rect(f, bx_x0, ax_y1, ax_w, 3, fill="#64748B", stroke="#64748B", rx=1)
    rect(f, bx_x0, ax_y1 - 6, 2, 15, fill=BLUE, stroke=BLUE)
    f.text(bx_x0, ax_y1 - 12, "x_min = 0.0", size=7.8, weight=700, fill=BLUE, anchor="middle")

    mid_bx = bx_x0 + ax_w / 2
    rect(f, mid_bx, ax_y1 - 6, 2, 15, fill="#475569", stroke="#475569")
    f.text(mid_bx, ax_y1 - 12, "3.0", size=7.8, fill="#475569", anchor="middle")

    rect(f, bx_x0 + ax_w, ax_y1 - 6, 2, 15, fill="#059669", stroke="#059669")
    f.text(bx_x0 + ax_w, ax_y1 - 12, "x_max = 6.0", size=7.8, weight=700, fill="#059669", anchor="middle")

    # Mũi tên ánh xạ lệch trục
    arrow(f, bx_x0, ax_y1 + 10, bx_x0, ax_y1 + 34, color=ORANGE, sw=THIN)
    f.text(bx_x0 + 10, ax_y1 + 24, "x = 0.0 ánh xạ vào Zero-Point Z = -128", size=7.5, weight=700, fill="#B45309")

    # Trục số nguyên INT8
    rect(f, bx_x0, ax_y2, ax_w, 3, fill=ORANGE, stroke=ORANGE, rx=1)
    rect(f, bx_x0, ax_y2 - 6, 2, 15, fill=ORANGE, stroke=ORANGE)
    f.text(bx_x0, ax_y2 + 16, "q = Z = -128", size=7.8, weight=700, fill="#B45309", anchor="middle")

    rect(f, mid_bx, ax_y2 - 6, 2, 15, fill="#475569", stroke="#475569")
    f.text(mid_bx, ax_y2 + 16, "0", size=7.8, fill="#475569", anchor="middle")

    rect(f, bx_x0 + ax_w, ax_y2 - 6, 2, 15, fill="#059669", stroke="#059669")
    f.text(bx_x0 + ax_w, ax_y2 + 16, "+127", size=7.8, weight=700, fill="#059669", anchor="middle")

    # Khối công thức thực thi phần cứng MAC NPU
    rect(f, x2 + 14, mac_y1, card_w - 28, 48, fill="#FFFBEB", stroke=ORANGE, sw=1.1, rx=3)
    f.text(x2 + card_w / 2, mac_y1 + 13, "Biểu thức tích chập phần cứng NPU (Phát sinh số hạng bù):",
           size=8.2, weight=700, fill="#92400E", anchor="middle")
    f.text(x2 + card_w / 2, mac_y1 + 27, "y = S_w · S_x · [ ∑ (w_i · x_i) - Z_x · ∑ w_i ]",
           size=9.2, weight=700, fill="#B45309", anchor="middle")
    f.text(x2 + card_w / 2, mac_y1 + 40, "→ Cần phần cứng tính thêm tích lũy bù - Z_x ∑ w_i",
           size=7.5, fill="#B91C1C", anchor="middle")

    # Khung phân tích hiệu năng & khuyến nghị
    rect(f, x2 + 14, perf_y1, card_w - 28, 58, fill="#FFFFFF", stroke=ORANGE, rx=3)
    f.text(x2 + 24, perf_y1 + 13, "Đặc tính độ chính xác và tính toán phần cứng:", size=8.2, weight=700, fill="#92400E")
    f.text(x2 + 24, perf_y1 + 27, "• Tận dụng trọn vẹn 256 mức rời rạc cho dải phân bố lệch (ReLU, Sigmoid).", size=7.8, fill="#166534")
    f.text(x2 + 24, perf_y1 + 40, "• Tránh lãng phí 128 mức âm vô nghĩa khi dữ liệu luôn dương.", size=7.8, fill="#334155")
    f.text(x2 + 24, perf_y1 + 51, "• Thường áp dụng cho Activation tensor trong các mạng CNN.", size=7.5, fill="#64748B")

    # Thẻ tóm tắt đáy
    rect(f, x2 + 14, bot_y, card_w - 28, 20, fill="#FFFBEB", stroke=ORANGE, rx=2)
    f.text(x2 + card_w / 2, bot_y + 11, "Z ≠ 0 → Giữ trọn dải động kích hoạt, tốn thêm phép bù offset",
           size=7.5, weight=700, fill="#92400E", anchor="middle")

    source(f, y_top + card_h + 2, "[T1 UG232 tr.70-74, Fig. 6-1] [T1 Gholami survey 2021] [T1 Nagel whitepaper 2021]")
    return f


# ==============================================================================
# 2. HÌNH PER-TENSOR VS PER-CHANNEL (quant-02-per-tensor-vs-per-channel)
# ==============================================================================
def fig_per_tensor_vs_per_channel():
    card_h = 304
    y_top = 44
    H = 370
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Phạm vi chia sẻ hệ số Scale lượng tử hóa: Per-Tensor vs Per-Channel",
           size=14, weight=700, fill=DARK)

    card_w = 415
    x1 = 18
    x2 = 447

    # --------------------------------------------------------------------------
    # CỘT TRÁI: PER-TENSOR QUANTIZATION (TOÀN BỘ KHỐI TENSOR DÙNG CHUNG 1 SCALE)
    # --------------------------------------------------------------------------
    rect(f, x1, y_top, card_w, card_h, fill="#F8FAFC", stroke="#94A3B8", sw=1.3, rx=6)
    rect(f, x1, y_top, card_w, 26, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=6)
    rect(f, x1 + 8, y_top + 4, 6, 18, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x1 + 22, y_top + 14, "A. Lượng tử hóa theo Tensor (Per-Tensor / Per-Layer)",
           size=10.5, weight=700, fill="#991B1B")

    f.text(x1 + 14, y_top + 36, "Toàn bộ khối trọng số 4D W [C_out, C_in, K, K] dùng CHUNG đúng 1 scale S",
           size=8.2, weight=700, fill="#991B1B")
    f.text(x1 + 14, y_top + 48, "S_tensor = max(|W|) / 127 cho toàn bộ các kênh đầu ra",
           size=8, fill="#334155")

    # Mô hình 4 lát cắt channel
    tx0 = x1 + 16
    ty0 = y_top + 62
    tw = 72
    th = 84

    # Channel 0
    rect(f, tx0, ty0, tw, th, fill="#EFF6FF", stroke=BLUE, rx=3)
    f.text(tx0 + tw / 2, ty0 + 13, "Kênh W_0", size=8.5, weight=700, fill=BLUE, anchor="middle")
    f.text(tx0 + tw / 2, ty0 + 27, "Dải hẹp:", size=7.5, fill="#64748B", anchor="middle")
    f.text(tx0 + tw / 2, ty0 + 40, "[-0.2, +0.2]", size=8, weight=700, fill=DARK, anchor="middle")
    rect(f, tx0 + 4, ty0 + 52, tw - 8, 26, fill="#FEF2F2", stroke="#DC2626", rx=2)
    f.text(tx0 + tw / 2, ty0 + 62, "Chỉ dùng ±2 mức", size=6.8, weight=700, fill="#DC2626", anchor="middle")
    f.text(tx0 + tw / 2, ty0 + 73, "Lỗi Underflow", size=6.5, fill="#DC2626", anchor="middle")

    # Channel 1
    rect(f, tx0 + 80, ty0, tw, th, fill="#EFF6FF", stroke=BLUE, rx=3)
    f.text(tx0 + 80 + tw / 2, ty0 + 13, "Kênh W_1", size=8.5, weight=700, fill=BLUE, anchor="middle")
    f.text(tx0 + 80 + tw / 2, ty0 + 27, "Dải vừa:", size=7.5, fill="#64748B", anchor="middle")
    f.text(tx0 + 80 + tw / 2, ty0 + 40, "[-1.5, +1.5]", size=8, weight=700, fill=DARK, anchor="middle")
    rect(f, tx0 + 84, ty0 + 52, tw - 8, 26, fill="#F8FAFC", stroke="#94A3B8", rx=2)
    f.text(tx0 + 80 + tw / 2, ty0 + 62, "Dùng ~19 mức", size=6.8, fill="#475569", anchor="middle")
    f.text(tx0 + 80 + tw / 2, ty0 + 73, "Độ phân giải kém", size=6.5, fill="#64748B", anchor="middle")

    f.text(tx0 + 168, ty0 + 40, "...", size=14, weight=700, fill=GRAY, anchor="middle")

    # Channel Outlier
    rect(f, tx0 + 184, ty0, tw + 28, th, fill="#FEF2F2", stroke="#DC2626", sw=1.3, rx=3)
    f.text(tx0 + 184 + (tw + 28) / 2, ty0 + 13, "Kênh W_outlier", size=8.2, weight=700, fill="#DC2626", anchor="middle")
    f.text(tx0 + 184 + (tw + 28) / 2, ty0 + 27, "Dải cực đại:", size=7.5, fill="#7F1D1D", anchor="middle")
    f.text(tx0 + 184 + (tw + 28) / 2, ty0 + 40, "[-10.0, +10.0]", size=8, weight=700, fill="#DC2626", anchor="middle")
    rect(f, tx0 + 188, ty0 + 52, tw + 20, 26, fill="#FEE2E2", stroke="#DC2626", rx=2)
    f.text(tx0 + 184 + (tw + 28) / 2, ty0 + 62, "Chi phối Scale", size=6.8, weight=700, fill="#7F1D1D", anchor="middle")
    f.text(tx0 + 184 + (tw + 28) / 2, ty0 + 73, "Dùng trọn 256 mức", size=6.5, fill="#7F1D1D", anchor="middle")

    # Khung scale chung
    scale_y1 = ty0 + th + 8
    rect(f, x1 + 14, scale_y1, card_w - 28, 42, fill="#FEF2F2", stroke="#DC2626", sw=1.1, rx=3)
    f.text(x1 + card_w / 2, scale_y1 + 14, "Đúng 1 Scale chung: S = 10.0 / 127 = 0.0787 cho TẤT CẢ các kênh",
           size=8.2, weight=700, fill="#B91C1C", anchor="middle")
    f.text(x1 + card_w / 2, scale_y1 + 29, "Kênh W_0 bị nén từ [-0.2, +0.2] vào các mức {-2, -1, 0, 1, 2} → Underflow nặng nề!",
           size=7.5, fill="#7F1D1D", anchor="middle")

    # Khung kết luận cột trái
    eval_y1 = scale_y1 + 42 + 8
    rect(f, x1 + 14, eval_y1, card_w - 28, 58, fill="#FFFFFF", stroke="#94A3B8", rx=3)
    f.text(x1 + 24, eval_y1 + 13, "Hậu quả thực nghiệm trên mô hình phát hiện (YOLO):", size=8.2, weight=700, fill=DARK)
    f.text(x1 + 24, eval_y1 + 27, "• Triệt tiêu các gradient nhỏ và đặc trưng góc cạnh tinh vi.", size=7.8, fill="#DC2626")
    f.text(x1 + 24, eval_y1 + 40, "• Sụt giảm nghiêm trọng độ chính xác mAP50 và mAP50-95.", size=7.8, fill="#64748B")
    f.text(x1 + 24, eval_y1 + 51, "• Không khuyến nghị dùng cho lớp tích chập của Object Detector.", size=7.5, fill="#1D4ED8")

    # Thẻ tóm tắt đáy
    bot_y = eval_y1 + 58 + 8
    rect(f, x1 + 14, bot_y, card_w - 28, 20, fill="#FEF2F2", stroke="#DC2626", rx=2)
    f.text(x1 + card_w / 2, bot_y + 11, "1 Scale cho cả khối → Mất mát thông tin ở các kênh dải hẹp",
           size=7.5, weight=700, fill="#B91C1C", anchor="middle")

    # --------------------------------------------------------------------------
    # CỘT PHẢI: PER-CHANNEL QUANTIZATION (MỖI CHANNEL 1 SCALE ĐỘC LẬP)
    # --------------------------------------------------------------------------
    rect(f, x2, y_top, card_w, card_h, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=6)
    rect(f, x2, y_top, card_w, 26, fill="#DCFCE7", stroke="#16A34A", sw=1.0, rx=6)
    rect(f, x2 + 8, y_top + 4, 6, 18, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 22, y_top + 14, "B. Lượng tử hóa theo Kênh (Per-Channel - Chuẩn RKNPU)",
           size=10.5, weight=700, fill="#14532D")

    f.text(x2 + 14, y_top + 36, "Mỗi kênh đầu ra C_out có một hệ số scale S_c riêng biệt",
           size=8.2, weight=700, fill="#14532D")
    f.text(x2 + 14, y_top + 48, "S_c = max(|W_c|) / 127 tối ưu hóa hoàn hảo cho từng lát cắt trọng số",
           size=8, fill="#334155")

    # 4 Lát cắt channel tương ứng với từng scale riêng
    rx0 = x2 + 16

    # Channel 0
    rect(f, rx0, ty0, tw, th, fill="#FFFFFF", stroke="#16A34A", rx=3)
    f.text(rx0 + tw / 2, ty0 + 13, "Kênh W_0", size=8.5, weight=700, fill="#14532D", anchor="middle")
    f.text(rx0 + tw / 2, ty0 + 27, "[-0.2, +0.2]", size=8, weight=700, fill=DARK, anchor="middle")
    rect(f, rx0 + 4, ty0 + 40, tw - 8, 18, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx0 + tw / 2, ty0 + 49, "S_0 = 0.0015", size=7.0, weight=700, fill="#14532D", anchor="middle")
    rect(f, rx0 + 4, ty0 + 61, tw - 8, 18, fill="#F0FDF4", stroke="#86EFAC", rx=2)
    f.text(rx0 + tw / 2, ty0 + 70, "Trọn 256 mức", size=6.8, fill="#15803D", anchor="middle")

    # Channel 1
    rect(f, rx0 + 80, ty0, tw, th, fill="#FFFFFF", stroke="#16A34A", rx=3)
    f.text(rx0 + 80 + tw / 2, ty0 + 13, "Kênh W_1", size=8.5, weight=700, fill="#14532D", anchor="middle")
    f.text(rx0 + 80 + tw / 2, ty0 + 27, "[-1.5, +1.5]", size=8, weight=700, fill=DARK, anchor="middle")
    rect(f, rx0 + 84, ty0 + 40, tw - 8, 18, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx0 + 80 + tw / 2, ty0 + 49, "S_1 = 0.0118", size=7.0, weight=700, fill="#14532D", anchor="middle")
    rect(f, rx0 + 84, ty0 + 61, tw - 8, 18, fill="#F0FDF4", stroke="#86EFAC", rx=2)
    f.text(rx0 + 80 + tw / 2, ty0 + 70, "Trọn 256 mức", size=6.8, fill="#15803D", anchor="middle")

    f.text(rx0 + 168, ty0 + 40, "...", size=14, weight=700, fill=GRAY, anchor="middle")

    # Channel Outlier
    rect(f, rx0 + 184, ty0, tw + 28, th, fill="#FFFFFF", stroke="#16A34A", rx=3)
    f.text(rx0 + 184 + (tw + 28) / 2, ty0 + 13, "Kênh W_outlier", size=8.2, weight=700, fill="#14532D", anchor="middle")
    f.text(rx0 + 184 + (tw + 28) / 2, ty0 + 27, "[-10.0, +10.0]", size=8, weight=700, fill=DARK, anchor="middle")
    rect(f, rx0 + 188, ty0 + 40, tw + 20, 18, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx0 + 184 + (tw + 28) / 2, ty0 + 49, "S_c = 0.0787", size=7.0, weight=700, fill="#14532D", anchor="middle")
    rect(f, rx0 + 188, ty0 + 61, tw + 20, 18, fill="#F0FDF4", stroke="#86EFAC", rx=2)
    f.text(rx0 + 184 + (tw + 28) / 2, ty0 + 70, "Trọn 256 mức", size=6.8, fill="#15803D", anchor="middle")

    # Khung ưu điểm RKNPU
    rect(f, x2 + 14, scale_y1, card_w - 28, 42, fill="#ECFDF5", stroke="#059669", sw=1.1, rx=3)
    f.text(x2 + card_w / 2, scale_y1 + 14, "Mỗi kênh khai thác tối đa 100% dải biểu diễn INT8 [-127, +127]",
           size=8.2, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + card_w / 2, scale_y1 + 29, "Không bị ảnh hưởng bởi kênh outlier khác → Sai số lượng tử tối thiểu, bảo toàn mAP!",
           size=7.5, fill="#065F46", anchor="middle")

    # Khung kết luận cột phải
    rect(f, x2 + 14, eval_y1, card_w - 28, 58, fill="#FFFFFF", stroke="#16A34A", rx=3)
    f.text(x2 + 24, eval_y1 + 13, "Cơ chế hỗ trợ phần cứng RKNPU RK3588:", size=8.2, weight=700, fill="#14532D")
    f.text(x2 + 24, eval_y1 + 27, "• NPU hỗ trợ nhân Per-Channel Scale trực tiếp trong mảng MAC.", size=7.8, fill="#15803D")
    f.text(x2 + 24, eval_y1 + 40, "• Không làm tăng độ trễ suy luận so với Per-Tensor (Zero Latency Overhead).", size=7.8, fill="#334155")
    f.text(x2 + 24, eval_y1 + 51, "• Chuẩn công nghiệp mặc định trên RKNN-Toolkit2 khi xuất mô hình YOLO.", size=7.8, fill="#15803D")

    # Thẻ tóm tắt đáy
    rect(f, x2 + 14, bot_y, card_w - 28, 20, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(x2 + card_w / 2, bot_y + 11, "Per-Channel: Chuẩn công nghiệp bảo toàn độ chính xác cho YOLO trên RK3588",
           size=7.5, weight=700, fill="#14532D", anchor="middle")

    source(f, y_top + card_h + 2, "[T1 UG232 tr.72-76, Fig. 6-2] [T1 Nagel whitepaper 2021] [T1 Q-YOLO 2023]")
    return f


FIGURES = [
    ("quant-01-symmetric-vs-asymmetric", fig_symmetric_vs_asymmetric),
    ("quant-02-per-tensor-vs-per-channel", fig_per_tensor_vs_per_channel),
]

if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    run(FIGURES, DEFAULT_OUTDIR)
