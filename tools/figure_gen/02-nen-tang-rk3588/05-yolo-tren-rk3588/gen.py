#!/usr/bin/env python3
"""Chuyên đề: YOLO trên RK3588 (05-yolo-tren-rk3588).

Sinh hình vector SVG minh họa:
  1. yolo-04-rknn-graph-cut:
     Ranh giới phân tách đồ thị YOLOv8 trên RK3588: NPU Hardware vs Host CPU.
     Trực quan hóa quá trình lọc và giảm số lượng hộp: 8,400 thô -> ~50 ứng viên -> Hộp phát hiện chuẩn.
  2. yolo-05-npu-compatibility-matrix:
     Ma trận tương thích toán tử phần cứng NPU Rockchip RK3588 dạng bảng trực quan.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "02-nen-tang-rk3588", "05-yolo-tren-rk3588"
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
# 1. HÌNH PHÂN TÁCH ĐỒ THỊ YOLO TRÊN RK3588 (yolo-04-rknn-graph-cut) - VISUAL-FIRST
# ==============================================================================
def fig_yolo_rknn_graph_cut():
    H = 390
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Phân tách đồ thị YOLOv8 trên RK3588: Tăng tốc NPU vs Hậu xử lý CPU",
           size=14, weight=700, fill=DARK)

    # --------------------------------------------------------------------------
    # KHỐI 1: TĂNG TỐC PHẦN CỨNG NPU (Đồ thị RKNN INT8)
    # --------------------------------------------------------------------------
    rect(f, 14, 42, 852, 146, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, 14, 42, 852, 26, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, 22, 46, 6, 18, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(36, 56, "1. Phần cứng RKNPU RK3588: Đồ thị nơ-ron INT8 (3 Nhân 6 TOPS - 100% phần cứng)",
           size=10.5, weight=700, fill="#1E40AF")

    # 1.A Input frame
    rect(f, 28, 76, 110, 100, fill="white", stroke="#94A3B8", rx=4)
    f.text(83, 93, "Frame đầu vào", size=9, weight=700, fill=DARK, anchor="middle")
    f.text(83, 107, "RGB 640×640×3", size=8.5, weight=700, fill=BLUE, anchor="middle")
    rect(f, 36, 116, 94, 20, fill="#ECFDF5", stroke="#059669", rx=2)
    f.text(83, 126, "DMA Zero-Copy", size=7.8, weight=700, fill="#047857", anchor="middle")
    f.text(83, 146, "Căn lề 16 byte", size=7.5, fill="#64748B", anchor="middle")
    f.text(83, 160, "[T1 OPL tr.335]", size=7.2, fill=GRAY, anchor="middle")

    arrow(f, 138, 126, 158, 126, color=BLUE)

    # 1.B Backbone & Neck
    rect(f, 158, 76, 185, 100, fill="white", stroke="#94A3B8", rx=4)
    f.text(250, 93, "Backbone & Neck (PAN-FPN)", size=9, weight=700, fill=DARK, anchor="middle")
    f.text(250, 107, "Conv-Swish + C2f + SPPF", size=8, fill="#334155", anchor="middle")

    # Vẽ 3 tầng đặc trưng P3, P4, P5
    rect(f, 170, 116, 48, 22, fill="#EFF6FF", stroke=BLUE, rx=2)
    f.text(194, 127, "P3 (80²)", size=7.5, weight=700, fill=BLUE, anchor="middle")

    rect(f, 226, 116, 48, 22, fill="#EFF6FF", stroke=BLUE, rx=2)
    f.text(250, 127, "P4 (40²)", size=7.5, weight=700, fill=BLUE, anchor="middle")

    rect(f, 282, 116, 48, 22, fill="#EFF6FF", stroke=BLUE, rx=2)
    f.text(306, 127, "P5 (20²)", size=7.5, weight=700, fill=BLUE, anchor="middle")

    f.text(250, 148, "Hợp nhất toán tử (Operator Fusion)", size=7.5, weight=700, fill="#15803D", anchor="middle")
    f.text(250, 162, "100% thực thi trên mảng MAC NPU", size=7.2, fill="#64748B", anchor="middle")

    arrow(f, 343, 126, 363, 126, color=BLUE)

    # 1.C Decoupled Head
    rect(f, 363, 76, 180, 100, fill="white", stroke="#94A3B8", rx=4)
    f.text(453, 93, "Decoupled Head", size=9, weight=700, fill=DARK, anchor="middle")
    rect(f, 375, 104, 156, 20, fill="#F8FAFC", stroke="#64748B", rx=2)
    f.text(453, 114, "Nhánh Cls: Conv 3×3 + Sigmoid", size=7.5, fill="#334155", anchor="middle")

    rect(f, 375, 128, 156, 20, fill="#F8FAFC", stroke="#64748B", rx=2)
    f.text(453, 138, "Nhánh Reg: Conv 3×3 + 1×1", size=7.5, fill="#334155", anchor="middle")

    f.text(453, 156, "Bọc _NormalizeCoords", size=7.5, weight=700, fill="#B45309", anchor="middle")
    f.text(453, 168, "(Bỏ DFL để tránh chuyển vị CPU)", size=7.2, fill="#DC2626", anchor="middle")

    arrow(f, 543, 126, 563, 126, color=BLUE)

    # 1.D Raw Output Tensor
    rect(f, 563, 76, 290, 100, fill="#EFF6FF", stroke="#2563EB", sw=1.3, rx=4)
    f.text(708, 93, "Tensor thô đầu ra NPU", size=9.5, weight=700, fill="#1E40AF", anchor="middle")
    f.text(708, 108, "Shape: [1, 4 + nc, 8400] (8400 anchors)", size=8.8, weight=700, fill=DARK, anchor="middle")

    # Mô phỏng tensor
    rect(f, 575, 118, 128, 22, fill="white", stroke=BLUE, rx=2)
    f.text(639, 129, "4 kênh: Box thô [x, y, w, h]", size=7.5, fill="#1E40AF", anchor="middle")

    rect(f, 711, 118, 130, 22, fill="white", stroke=BLUE, rx=2)
    f.text(776, 129, "nc kênh: Xác suất lớp (Scores)", size=7.5, fill="#1E40AF", anchor="middle")

    rect(f, 575, 146, 266, 20, fill="#FEF2F2", stroke="#DC2626", rx=2)
    f.text(708, 156, "Chứa 8,400 hộp ứng viên dày đặc (Cần lọc và giải mã)",
           size=7.5, weight=700, fill="#DC2626", anchor="middle")

    # --------------------------------------------------------------------------
    # ĐƯỜNG PHÂN CẮT ĐỒ THỊ (GRAPH CUT BOUNDARY)
    # --------------------------------------------------------------------------
    y_cut = 196
    rect(f, 14, y_cut, 852, 28, fill="#FEF2F2", stroke="#DC2626", sw=1.2, dashed=True, rx=4)
    f.text(28, y_cut + 14, "✂ RANH GIỚI CẮT ĐỒ THỊ: Ultralytics ép model.end2end = False khi xuất định dạng RKNN [T1 ULT exporter.py:685]",
           size=9, weight=700, fill="#B91C1C")
    f.text(585, y_cut + 14, "Lý do: NPU thiếu nhân TopK / GatherElements",
           size=8.5, weight=700, fill="#7F1D1D")

    # --------------------------------------------------------------------------
    # KHỐI 2: HẬU XỬ LÝ TRÊN HOST CPU (ARM NEON C++)
    # --------------------------------------------------------------------------
    y_cpu = 232
    rect(f, 14, y_cpu, 852, 146, fill="#FFFBEB", stroke="#D97706", sw=1.3, rx=6)
    rect(f, 14, y_cpu, 852, 26, fill="#FEF3C7", stroke="#D97706", sw=1.0, rx=6)
    rect(f, 22, y_cpu + 4, 6, 18, fill=ORANGE, stroke=ORANGE, sw=1, rx=2)
    f.text(36, y_cpu + 14, "2. Hậu xử lý trên Host CPU (Cortex-A76/A55): Tối ưu SIMD NEON đa luồng C++",
           size=10.5, weight=700, fill="#92400E")

    # 2.A Dequantize
    rect(f, 28, y_cpu + 36, 192, 100, fill="white", stroke="#CBD5E1", rx=4)
    f.text(124, y_cpu + 52, "Bước 1: Dequantize & Scale", size=9, weight=700, fill=DARK, anchor="middle")
    f.text(124, y_cpu + 68, "• Chuyển INT8 → FP32", size=7.8, fill="#334155", anchor="middle")
    f.text(124, y_cpu + 82, "• Nhân ngược cỡ ảnh (× 640)", size=7.8, fill="#334155", anchor="middle")
    rect(f, 38, y_cpu + 96, 172, 28, fill="#F8FAFC", stroke="#94A3B8", rx=2)
    f.text(124, y_cpu + 110, "Đầu vào: 8,400 anchors", size=7.8, weight=700, fill="#64748B", anchor="middle")

    arrow(f, 220, y_cpu + 86, 240, y_cpu + 86, color=INK)

    # 2.B Score Filter
    rect(f, 240, y_cpu + 36, 192, 100, fill="white", stroke="#CBD5E1", rx=4)
    f.text(336, y_cpu + 52, "Bước 2: Lọc ngưỡng Score", size=9, weight=700, fill=DARK, anchor="middle")
    f.text(336, y_cpu + 68, "• max(cls_score) > conf_thres", size=7.8, fill="#334155", anchor="middle")
    f.text(336, y_cpu + 82, "• Loại bỏ 90% - 95% hộp rác", size=7.8, fill="#DC2626", anchor="middle")
    rect(f, 250, y_cpu + 96, 172, 28, fill="#FEF2F2", stroke="#DC2626", rx=2)
    f.text(336, y_cpu + 110, "Còn lại: ~30 - 80 ứng viên", size=7.8, weight=700, fill="#B91C1C", anchor="middle")

    arrow(f, 432, y_cpu + 86, 452, y_cpu + 86, color=INK)

    # 2.C Decode Box
    rect(f, 452, y_cpu + 36, 192, 100, fill="white", stroke="#CBD5E1", rx=4)
    f.text(548, y_cpu + 52, "Bước 3: Giải mã Bbox (Decode)", size=9, weight=700, fill=DARK, anchor="middle")
    f.text(548, y_cpu + 68, "• Nhân stride lưới (8, 16, 32)", size=7.8, fill="#334155", anchor="middle")
    f.text(548, y_cpu + 82, "• Đổi tâm [cx, cy, w, h] → [x1, y1, x2, y2]", size=7.5, fill="#334155", anchor="middle")
    rect(f, 462, y_cpu + 96, 172, 28, fill="#F8FAFC", stroke="#94A3B8", rx=2)
    f.text(548, y_cpu + 110, "Chuẩn bị tọa độ thực để NMS", size=7.8, weight=700, fill="#64748B", anchor="middle")

    arrow(f, 644, y_cpu + 86, 664, y_cpu + 86, color=INK)

    # 2.D NMS Triệt tiêu hộp
    rect(f, 664, y_cpu + 36, 192, 100, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=4)
    f.text(760, y_cpu + 52, "Bước 4: NMS lọc chồng lặp", size=9, weight=700, fill="#15803D", anchor="middle")
    f.text(760, y_cpu + 68, "• Tính IoU giữa các hộp cùng lớp", size=7.8, fill="#334155", anchor="middle")
    f.text(760, y_cpu + 82, "• Triệt tiêu hộp nếu IoU > 0.45", size=7.8, fill="#15803D", anchor="middle")
    rect(f, 674, y_cpu + 96, 172, 28, fill="#ECFDF5", stroke="#059669", rx=2)
    f.text(760, y_cpu + 110, "Kết quả cuối: [N, 6] hộp chuẩn", size=8, weight=700, fill="#047857", anchor="middle")

    source(f, H - 12, "[T1 ULT exporter.py:682-688] [T1 OPL tr.58-63, tr.330-333] [T1 UG232 tr.140-150]")
    return f


# ==============================================================================
# 2. HÌNH MA TRẬN TIÊU CHÍ THÂN THIỆN NPU (yolo-05-npu-compatibility-matrix) - VISUAL GRID
# ==============================================================================
def fig_npu_compatibility_matrix():
    H = 405
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Ma trận tương thích toán tử phần cứng NPU Rockchip RK3588 (OPL 3.2)",
           size=14, weight=700, fill=DARK)

    # 3 Cột nhóm toán tử
    col_w = 274
    col_h = 350
    col_y = 44
    x1 = 14
    x2 = 303
    x3 = 592

    # --------------------------------------------------------------------------
    # CỘT 1: VÙNG XANH - THÂN THIỆN 100% NPU
    # --------------------------------------------------------------------------
    rect(f, x1, col_y, col_w, col_h, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=6)
    rect(f, x1, col_y, col_w, 28, fill="#DCFCE7", stroke="#16A34A", sw=1.0, rx=6)
    f.text(x1 + col_w / 2, col_y + 11, "1. VÙNG XANH: 100% PHẦN CỨNG NPU", size=9.5, weight=700, fill="#14532D", anchor="middle")
    f.text(x1 + col_w / 2, col_y + 23, "Hỗ trợ 3 nhân song song | Hiệu suất tối đa", size=7.5, fill="#15803D", anchor="middle")

    row_h = 92
    rx1 = x1 + 8
    rw = col_w - 16

    # 1.1 Conv 3x3 / 1x1
    rect(f, rx1, col_y + 36, rw, row_h, fill="white", stroke="#86EFAC", rx=3)
    f.text(rx1 + 10, col_y + 51, "Conv 3×3 & Conv 1×1 (Chuẩn)", size=8.8, weight=700, fill="#14532D")
    rect(f, rx1 + rw - 60, col_y + 42, 52, 16, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx1 + rw - 34, col_y + 50, "Full NPU", size=7.2, weight=700, fill="#14532D", anchor="middle")
    f.text(rx1 + 10, col_y + 67, "• Tận dụng trọn mảng MAC INT8 / 3 Core", size=7.5, fill=DARK)
    f.text(rx1 + 10, col_y + 80, "• Kênh INT8: Khuyến nghị bội số của 32", size=7.5, weight=700, fill="#15803D")
    f.text(rx1 + 10, col_y + 93, "• Không phân mảnh băng thông DDR", size=7.2, fill="#64748B")
    f.text(rx1 + 10, col_y + 106, "• Đạt đỉnh 6 TOPS trên RK3588", size=7.2, fill="#64748B")

    # 1.2 ConvSwish Fusion
    rect(f, rx1, col_y + 136, rw, row_h, fill="white", stroke="#86EFAC", rx=3)
    f.text(rx1 + 10, col_y + 151, "Hợp nhất Conv + BN + SiLU", size=8.8, weight=700, fill="#14532D")
    rect(f, rx1 + rw - 60, col_y + 142, 52, 16, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx1 + rw - 34, col_y + 150, "Fused OP", size=7.2, weight=700, fill="#14532D", anchor="middle")
    f.text(rx1 + 10, col_y + 167, "• Tự động gộp thành 1 lệnh phần cứng", size=7.5, fill=DARK)
    f.text(rx1 + 10, col_y + 180, "• Triệt tiêu ghi tensor trung gian ra RAM", size=7.5, weight=700, fill="#15803D")
    f.text(rx1 + 10, col_y + 193, "• Tiết kiệm 40% lưu lượng bus DDR", size=7.2, fill="#64748B")
    f.text(rx1 + 10, col_y + 206, "• Chuẩn hóa mặc định trên YOLOv8/v11", size=7.2, fill="#64748B")

    # 1.3 Residual Add & SPPF
    rect(f, rx1, col_y + 236, rw, row_h, fill="white", stroke="#86EFAC", rx=3)
    f.text(rx1 + 10, col_y + 251, "C2f / C3k2 & MaxPool SPPF", size=8.8, weight=700, fill="#14532D")
    rect(f, rx1 + rw - 60, col_y + 242, 52, 16, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx1 + rw - 34, col_y + 250, "Multi-Core", size=7.2, weight=700, fill="#14532D", anchor="middle")
    f.text(rx1 + 10, col_y + 267, "• Phép cộng residual Add hỗ trợ 3 core", size=7.5, fill=DARK)
    f.text(rx1 + 10, col_y + 280, "• SPPF MaxPool kernel ≤ 7 chạy 100% NPU", size=7.5, weight=700, fill="#15803D")
    f.text(rx1 + 10, col_y + 293, "• Split & Concat xử lý trực tiếp", size=7.2, fill="#64748B")
    f.text(rx1 + 10, col_y + 306, "• Độ ổn định suy luận hoàn hảo", size=7.2, fill="#64748B")

    # Thẻ tóm tắt đáy cột 1
    rect(f, rx1, col_y + 332, rw, 14, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(rx1 + rw / 2, col_y + 339, "Mô hình thuần nhóm này: 0% tải CPU", size=7.2, weight=700, fill="#14532D", anchor="middle")

    # --------------------------------------------------------------------------
    # CỘT 2: VÙNG VÀNG - CẦN CẤU HÌNH VÀ TỐI ƯU HÓA
    # --------------------------------------------------------------------------
    rect(f, x2, col_y, col_w, col_h, fill="#FEFCE8", stroke="#CA8A04", sw=1.3, rx=6)
    rect(f, x2, col_y, col_w, 28, fill="#FEF9C3", stroke="#CA8A04", sw=1.0, rx=6)
    f.text(x2 + col_w / 2, col_y + 11, "2. VÙNG VÀNG: CẦN TỐI ƯU HÓA", size=9.5, weight=700, fill="#713F12", anchor="middle")
    f.text(x2 + col_w / 2, col_y + 23, "Chạy trên NPU nhưng có thể nghẽn MAC", size=7.5, fill="#854D0E", anchor="middle")

    rx2 = x2 + 8
    # 2.1 Depthwise Conv
    rect(f, rx2, col_y + 36, rw, row_h, fill="white", stroke="#FDE047", rx=3)
    f.text(rx2 + 10, col_y + 51, "Depthwise Conv (DWConv)", size=8.8, weight=700, fill="#713F12")
    rect(f, rx2 + rw - 60, col_y + 42, 52, 16, fill="#FEF9C3", stroke="#CA8A04", rx=2)
    f.text(rx2 + rw - 34, col_y + 50, "Low MAC", size=7.2, weight=700, fill="#713F12", anchor="middle")
    f.text(rx2 + 10, col_y + 67, "• Thiếu tái sử dụng dữ liệu chéo kênh", size=7.5, fill=DARK)
    f.text(rx2 + 10, col_y + 80, "• Kênh INT8: Bắt buộc bội số 64", size=7.5, weight=700, fill="#B45309")
    f.text(rx2 + 10, col_y + 93, "• Hiệu suất tính toán MAC chỉ đạt ~30%", size=7.2, fill="#64748B")
    f.text(rx2 + 10, col_y + 106, "• Khuyến nghị: Dùng Conv 3×3 tiêu chuẩn", size=7.2, fill="#15803D")

    # 2.2 FlashAttention
    rect(f, rx2, col_y + 136, rw, row_h, fill="white", stroke="#FDE047", rx=3)
    f.text(rx2 + 10, col_y + 151, "Cơ chế chú ý (FlashAttention)", size=8.8, weight=700, fill="#713F12")
    rect(f, rx2 + rw - 60, col_y + 142, 52, 16, fill="#FEF9C3", stroke="#CA8A04", rx=2)
    f.text(rx2 + rw - 34, col_y + 150, "Need Config", size=7.0, weight=700, fill="#713F12", anchor="middle")
    f.text(rx2 + 10, col_y + 167, "• MatMul rời rạc không có phần cứng riêng", size=7.5, fill=DARK)
    f.text(rx2 + 10, col_y + 180, "• Phải bật: enable_flash_attention=True", size=7.5, weight=700, fill="#1D4ED8")
    f.text(rx2 + 10, col_y + 193, "• Hợp nhất thành op exSDPAttention", size=7.2, fill="#64748B")
    f.text(rx2 + 10, col_y + 206, "• Giới hạn kênh channel ≤ 8,192", size=7.2, fill="#64748B")

    # 2.3 Resize & Concat
    rect(f, rx2, col_y + 236, rw, row_h, fill="white", stroke="#FDE047", rx=3)
    f.text(rx2 + 10, col_y + 251, "Phép chuyển dữ liệu & Resize", size=8.8, weight=700, fill="#713F12")
    rect(f, rx2 + rw - 60, col_y + 242, 52, 16, fill="#FEF9C3", stroke="#CA8A04", rx=2)
    f.text(rx2 + rw - 34, col_y + 250, "Bus Heavy", size=7.2, weight=700, fill="#713F12", anchor="middle")
    f.text(rx2 + 10, col_y + 267, "• Concat / Split / Reshape: Tốn bus DDR", size=7.5, fill=DARK)
    f.text(rx2 + 10, col_y + 280, "• Resize: Tự chuyển sang ConvTranspose", size=7.5, fill="#334155")
    f.text(rx2 + 10, col_y + 293, "• Không có mạch nội suy phần cứng", size=7.2, fill="#64748B")
    f.text(rx2 + 10, col_y + 306, "• Cần tiết giảm số nhánh ghép nối", size=7.2, fill="#B45309")

    # Thẻ tóm tắt đáy cột 2
    rect(f, rx2, col_y + 332, rw, 14, fill="#FEF9C3", stroke="#CA8A04", rx=2)
    f.text(rx2 + rw / 2, col_y + 339, "Cần cấu hình đúng để tránh rớt TOPS", size=7.2, weight=700, fill="#713F12", anchor="middle")

    # --------------------------------------------------------------------------
    # CỘT 3: VÙNG ĐỎ - NGUY CƠ RƠI CPU (FALLBACK)
    # --------------------------------------------------------------------------
    rect(f, x3, col_y, col_w, col_h, fill="#FEF2F2", stroke="#DC2626", sw=1.3, rx=6)
    rect(f, x3, col_y, col_w, 28, fill="#FEE2E2", stroke="#DC2626", sw=1.0, rx=6)
    f.text(x3 + col_w / 2, col_y + 11, "3. VÙNG ĐỎ: NGUY CƠ RƠI CPU (FALLBACK)", size=9.5, weight=700, fill="#7F1D1D", anchor="middle")
    f.text(x3 + col_w / 2, col_y + 23, "Thiếu nhân phần cứng | Làm sụt giảm FPS", size=7.5, fill="#991B1B", anchor="middle")

    rx3 = x3 + 8
    # 3.1 DFL
    rect(f, rx3, col_y + 36, rw, row_h, fill="white", stroke="#FCA5A5", rx=3)
    f.text(rx3 + 10, col_y + 51, "Khối DFL (Distribution Focal Loss)", size=8.8, weight=700, fill="#991B1B")
    rect(f, rx3 + rw - 60, col_y + 42, 52, 16, fill="#FEE2E2", stroke="#DC2626", rx=2)
    f.text(rx3 + rw - 34, col_y + 50, "CPU Drop", size=7.2, weight=700, fill="#991B1B", anchor="middle")
    f.text(rx3 + 10, col_y + 67, "• Reshape + Softmax + Transpose phẳng", size=7.5, fill=DARK)
    f.text(rx3 + 10, col_y + 80, "• Chiều dài 16×8400 vượt trần NPU", size=7.5, weight=700, fill="#B91C1C")
    f.text(rx3 + 10, col_y + 93, "• Bị đẩy ngược về chạy trên nhân CPU", size=7.2, fill="#DC2626")
    f.text(rx3 + 10, col_y + 106, "• Giải pháp: Bỏ DFL, dùng direct reg", size=7.2, fill="#15803D")

    # 3.2 End-to-End NMS
    rect(f, rx3, col_y + 136, rw, row_h, fill="white", stroke="#FCA5A5", rx=3)
    f.text(rx3 + 10, col_y + 151, "End-to-End NMS (TopK / Sort)", size=8.8, weight=700, fill="#991B1B")
    rect(f, rx3 + rw - 60, col_y + 142, 52, 16, fill="#FEE2E2", stroke="#DC2626", rx=2)
    f.text(rx3 + rw - 34, col_y + 150, "No NPU Op", size=7.2, weight=700, fill="#991B1B", anchor="middle")
    f.text(rx3 + 10, col_y + 167, "• NPU không có mạch so sánh / sắp xếp động", size=7.5, fill=DARK)
    f.text(rx3 + 10, col_y + 180, "• OPL 3.2 thiếu TopK & GatherElements", size=7.5, weight=700, fill="#B91C1C")
    f.text(rx3 + 10, col_y + 193, "• Exporter ép tắt: model.end2end=False", size=7.2, fill="#334155")
    f.text(rx3 + 10, col_y + 206, "• Giải pháp: Viết NMS C++ NEON riêng", size=7.2, fill="#15803D")

    # 3.3 Logical ops & int64
    rect(f, rx3, col_y + 236, rw, row_h, fill="white", stroke="#FCA5A5", rx=3)
    f.text(rx3 + 10, col_y + 251, "Toán tử logic & Kiểu int64", size=8.8, weight=700, fill="#991B1B")
    rect(f, rx3 + rw - 60, col_y + 242, 52, 16, fill="#FEE2E2", stroke="#DC2626", rx=2)
    f.text(rx3 + rw - 34, col_y + 250, "Unsupported", size=7.0, weight=700, fill="#991B1B", anchor="middle")
    f.text(rx3 + 10, col_y + 267, "• Ép kiểu int64: NPU hoàn toàn không có", size=7.5, fill=DARK)
    f.text(rx3 + 10, col_y + 280, "• Equal, Mod, ReduceMax chỉ có trên CPU", size=7.5, weight=700, fill="#B91C1C")
    f.text(rx3 + 10, col_y + 293, "• Làm đứt gãy luồng thực thi đồ thị", size=7.2, fill="#DC2626")
    f.text(rx3 + 10, col_y + 306, "• Phải chuyển sang int32 / float32", size=7.2, fill="#334155")

    # Thẻ tóm tắt đáy cột 3
    rect(f, rx3, col_y + 332, rw, 14, fill="#FEE2E2", stroke="#DC2626", rx=2)
    f.text(rx3 + rw / 2, col_y + 339, "Triệt tiêu toán tử đỏ để bảo toàn FPS", size=7.2, weight=700, fill="#7F1D1D", anchor="middle")

    source(f, H - 12, "[T1 OPL tr.56-107, tr.320-333] [T1 UG232 tr.140-150] [T1 ULT engine/exporter.py:682-688]")
    return f


FIGURES = [
    ("yolo-04-rknn-graph-cut", fig_yolo_rknn_graph_cut),
    ("yolo-05-npu-compatibility-matrix", fig_npu_compatibility_matrix),
]

if __name__ == "__main__":
    run(FIGURES, DEFAULT_OUTDIR)
