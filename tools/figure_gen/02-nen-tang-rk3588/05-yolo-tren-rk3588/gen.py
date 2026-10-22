#!/usr/bin/env python3
"""Chuyên đề: YOLO trên RK3588 (05-yolo-tren-rk3588).

Sinh hình vector SVG minh họa:
  1. yolo-04-rknn-graph-cut:
     Ranh giới phân tách đồ thị YOLOv8 trên RK3588: NPU Hardware vs Host CPU.
     - Phân định rõ đồ thị NPU tăng tốc (Backbone + Neck + Decoupled Head + _NormalizeCoords)
     - Ranh giới cắt đồ thị (Ultralytics exporter tắt end2end do thiếu nhân TopK/Gather trên NPU)
     - Pipeline hậu xử lý đa tầng trên Host CPU (Dequantize, Conf Filter, Decode, NMS).

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/02-nen-tang-rk3588/05-yolo-tren-rk3588 -> ../../.. = docs/tools/figure_gen
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
# 1. HÌNH PHÂN TÁCH ĐỒ THỊ YOLO TRÊN RK3588 (yolo-04-rknn-graph-cut)
# ==============================================================================
def fig_yolo_rknn_graph_cut():
    H = 508
    f = Fig(W, H)

    # Tiêu đề & Tier
    f.text(14, 28, "Ranh giới phân tách đồ thị YOLOv8 trên RK3588: NPU Hardware vs Host CPU",
           size=16, weight="bold", fill=INK)
    tier(f, "T1 RK3588")

    # --------------------------------------------------------------------------
    # KHỐI 1: NPU HARDWARE ACCELERATION (Đồ thị RKNN INT8)
    # --------------------------------------------------------------------------
    rect(f, 14, 48, 852, 192, fill="#F8FAFC", stroke="#2563EB", sw=1.5, rx=6)
    f.text(28, 68, "1. PHẦN CỨNG NPU RK3588 (Đồ thị RKNN INT8 - Chạy tăng tốc trên 3 lõi NPU 6 TOPS)",
           size=12.5, weight="bold", fill="#1E3A8A")

    # 1.A Input frame
    rect(f, 28, 82, 105, 110, fill="white", stroke="#94A3B8")
    f.text(36, 102, "Frame đầu vào", size=11, weight="bold", fill=INK)
    f.text(36, 122, "RGB 640x640x3", size=9.5, fill=DARK)
    f.text(36, 140, "Zero-Copy DMA", size=9.5, fill="#047857")
    f.text(36, 158, "Căn lề 16-byte", size=9.5, fill=DARK)
    f.text(36, 176, "[T1 OPL tr.335]", size=8.5, fill=GRAY)

    arrow(f, 133, 137, 155, 137, color=BLUE)

    # 1.B Backbone
    rect(f, 155, 82, 148, 110, fill="white", stroke="#94A3B8")
    f.text(165, 102, "Backbone CSPDarknet", size=11, weight="bold", fill=INK)
    f.text(165, 122, "• CBS (Conv+BN+SiLU)", size=9.5, fill=DARK)
    f.text(165, 140, "• C2f / C3k2 residual", size=9.5, fill=DARK)
    f.text(165, 158, "• SPPF trích xuất 3 tầng", size=9.5, fill=DARK)
    f.text(165, 176, "100% NPU [T1 OPL tr.58]", size=9, weight="bold", fill=GREEN)

    arrow(f, 303, 137, 325, 137, color=BLUE)

    # 1.C Neck PANet
    rect(f, 325, 82, 152, 110, fill="white", stroke="#94A3B8")
    f.text(335, 102, "Neck PAN-FPN", size=11, weight="bold", fill=INK)
    f.text(335, 122, "• Upsample (ConvTrans)", size=9.5, fill=DARK)
    f.text(335, 140, "• Concat kết nối tắt", size=9.5, fill=DARK)
    f.text(335, 158, "• 3 tỷ lệ đặc trưng:", size=9.5, fill=DARK)
    f.text(343, 176, "P3 (80²), P4 (40²), P5 (20²)", size=9, fill="#1D4ED8")

    arrow(f, 477, 137, 499, 137, color=BLUE)

    # 1.D Decoupled Head
    rect(f, 499, 82, 168, 110, fill="white", stroke="#94A3B8")
    f.text(509, 102, "Decoupled Head", size=11, weight="bold", fill=INK)
    f.text(509, 122, "• Cls: Conv 3x3 + Sigmoid", size=9.5, fill=DARK)
    f.text(509, 140, "• Reg: Conv 3x3 + 1x1", size=9.5, fill=DARK)
    f.text(509, 158, "• Bọc _NormalizeCoords", size=9.5, fill="#B45309")
    f.text(517, 176, "(Slice + Div + Concat) [T1]", size=8.5, fill=GRAY)

    arrow(f, 667, 137, 689, 137, color=BLUE)

    # 1.E Raw Output
    rect(f, 689, 82, 165, 110, fill="white", stroke="#2563EB", sw=1.4)
    f.text(699, 102, "Tensor thô đầu ra", size=11, weight="bold", fill="#1E3A8A")
    f.text(699, 122, "Kích thước: [1, 4+nc, 8400]", size=9, weight="bold", fill=INK)
    f.text(699, 140, "• 4 kênh: Hộp thô xywh", size=9.5, fill=DARK)
    f.text(699, 158, "• nc kênh: Logits lớp", size=9.5, fill=DARK)
    f.text(699, 176, "• 8400 anchors đa tỷ lệ", size=9.5, fill=DARK)

    # Ghi chú chân khối 1
    f.text(28, 226, "Toàn bộ Conv, BN-folding, SiLU, Concat chạy song song trên mảng MAC NPU; không rơi về CPU [T1 OPL tr.58-63].",
           size=9.5, fill=DARK)

    # --------------------------------------------------------------------------
    # RANH GIỚI CẮT ĐỒ THỊ (GRAPH CUT BOUNDARY)
    # --------------------------------------------------------------------------
    rect(f, 14, 248, 852, 40, fill="#FEF2F2", stroke="#DC2626", sw=1.3, dashed=True, rx=4)
    f.text(28, 265, "RANH GIỚI CẮT ĐỒ THỊ: Ultralytics ép model.end2end = False khi xuất định dạng RKNN [T1 ULT exporter.py:685]",
           size=10.5, weight="bold", fill="#B91C1C")
    f.text(28, 280, "Lý do: NPU RK3588 thiếu nhân phần cứng TopK & GatherElements trong OPL 3.2. Không hỗ trợ NMS nội suy [T1 OPL tr.330-333].",
           size=9.5, fill="#7F1D1D")

    # Mũi tên chuyển giao giữa NPU và CPU
    arrow(f, 770, 288, 770, 302, color=RED)

    # --------------------------------------------------------------------------
    # KHỐI 2: HẬU XỬ LÝ TRÊN HOST CPU (ARM Cortex-A76/A55)
    # --------------------------------------------------------------------------
    rect(f, 14, 304, 852, 108, fill="#FFFBEB", stroke="#D97706", sw=1.5, rx=6)
    f.text(28, 322, "2. HẬU XỬ LÝ TRÊN HOST CPU (ARM Cortex-A76/A55 - Viết bằng C++ / Tối ưu SIMD NEON đa luồng)",
           size=12, weight="bold", fill="#92400E")

    # 2.A Dequantize
    rect(f, 28, 332, 186, 68, fill="white", stroke="#CBD5E1")
    f.text(38, 350, "Bước 1: Dequantize & Scale", size=10.5, weight="bold", fill=INK)
    f.text(38, 368, "• Chuyển INT8 -> FP32", size=9.5, fill=DARK)
    f.text(38, 386, "• Nhân ngược cỡ ảnh (x640)", size=9.5, fill=DARK)

    arrow(f, 214, 366, 236, 366, color=INK)

    # 2.B Lọc ngưỡng
    rect(f, 236, 332, 194, 68, fill="white", stroke="#CBD5E1")
    f.text(246, 350, "Bước 2: Lọc ngưỡng Score", size=10.5, weight="bold", fill=INK)
    f.text(246, 368, "• max(cls_score) > conf_thres", size=9.5, fill=DARK)
    f.text(246, 386, "• Loại bỏ 90-95% anchor rác", size=9.5, fill=DARK)

    arrow(f, 430, 366, 452, 366, color=INK)

    # 2.C Giải mã hộp
    rect(f, 452, 332, 188, 68, fill="white", stroke="#CBD5E1")
    f.text(462, 350, "Bước 3: Giải mã Bbox (Decode)", size=10.5, weight="bold", fill=INK)
    f.text(462, 368, "• Nhân bước trượt (stride 8/16/32)", size=9.5, fill=DARK)
    f.text(462, 386, "• Đổi tâm sang góc [x1, y1, x2, y2]", size=9.5, fill=DARK)

    arrow(f, 640, 366, 662, 366, color=INK)

    # 2.D NMS
    rect(f, 662, 332, 192, 68, fill="white", stroke="#059669", sw=1.4)
    f.text(672, 350, "Bước 4: NMS lọc trùng lặp", size=10.5, weight="bold", fill="#065F46")
    f.text(672, 368, "• Triệt tiêu hộp IoU > 0.45", size=9.5, fill=DARK)
    f.text(672, 386, "-> Hộp phát hiện cuối [N, 6]", size=9.5, weight="bold", fill=GREEN)

    # --------------------------------------------------------------------------
    # THẺ TÓM TẮT BẢN CHẤT THIẾT KẾ
    # --------------------------------------------------------------------------
    rect(f, 14, 424, 852, 54, fill="#F1F5F9", stroke="#94A3B8", rx=4)
    f.text(24, 442, "Bản chất phân chia tính toán YOLO trên Rockchip RK3588:",
           size=11, weight="bold", fill=INK)
    f.text(24, 458, "• Mảng systolic NPU chỉ tối ưu cho các phép tính mảng tĩnh (Conv INT8); không có phần cứng tăng tốc cho logic lọc động (TopK/NMS).",
           size=9.5, fill=DARK)
    f.text(24, 471, "• Thiết kế chuẩn: Cắt đồ thị xuất tensor thô [1, 4+nc, 8400], đưa NMS ra CPU C++ tối ưu NEON đa luồng để đạt 30-60+ FPS [T1 ULT :682-688] [T1 OPL tr.330].",
           size=9.5, fill=DARK)

    # Dòng nguồn
    source(f, 480,
           "[T1 ULT engine/exporter.py:682-688] [T1 ULT utils/export/engine.py:34-47] [T1 OPL tr.58-63, tr.330-333]")

    return f


# ==============================================================================
# 2. HÌNH MA TRẬN TIÊU CHÍ THÂN THIỆN NPU (yolo-05-npu-compatibility-matrix)
# ==============================================================================
def fig_npu_compatibility_matrix():
    H = 508
    f = Fig(W, H)

    # Tiêu đề & Tier
    f.text(14, 28, "Ma trận tiêu chí thân thiện NPU trên RK3588: Phân loại toán tử và kiến trúc",
           size=16, weight="bold", fill=INK)
    tier(f, "T1 RK3588")

    col_w = 274
    col_h = 366
    col_y = 48
    item_w = 256
    item_h = 98

    # --------------------------------------------------------------------------
    # CỘT 1: VÙNG XANH - THÂN THIỆN NPU (100% NPU)
    # --------------------------------------------------------------------------
    x1 = 14
    rect(f, x1, col_y, col_w, col_h, fill="#F0FDF4", stroke="#16A34A", sw=1.5, rx=6)
    rect(f, x1, col_y, col_w, 35, fill="#DCFCE7", stroke="#16A34A", sw=1.5, rx=6)
    f.text(x1 + 10, col_y + 15, "1. VÙNG XANH: THÂN THIỆN NPU", size=11, weight="bold", fill="#14532D")
    f.text(x1 + 10, col_y + 28, "Thực thi 100% trên NPU, hỗ trợ đa lõi", size=8.5, fill="#15803D")

    ix1 = x1 + 9
    # 1.1 Standard Conv
    rect(f, ix1, 90, item_w, 96, fill="white", stroke="#86EFAC", rx=4)
    f.text(ix1 + 10, 108, "Tích chập tiêu chuẩn (Conv)", size=10.5, weight="bold", fill="#14532D")
    f.text(ix1 + 10, 125, "• Conv 3x3 (stride 1, 2) & Conv 1x1 [T1 OPL tr.58]", size=9, fill=DARK)
    f.text(ix1 + 10, 142, "• Kênh INT8: Bắt buộc bội số 32 [T1 UG232 tr.145]", size=9, fill="#15803D")
    f.text(ix1 + 10, 159, "• Hỗ trợ chạy song song cả 3 core NPU", size=9, fill=DARK)
    f.text(ix1 + 10, 174, "• Trọng số nhân < 6 KB nằm trọn cache DPU", size=8.5, fill=GRAY)

    # 1.2 ConvSwish
    rect(f, ix1, 194, item_w, 96, fill="white", stroke="#86EFAC", rx=4)
    f.text(ix1 + 10, 212, "Hợp nhất ConvolutionSwish", size=10.5, weight="bold", fill="#14532D")
    f.text(ix1 + 10, 229, "• Tự động gộp Conv + BN + SiLU [T1 OPL tr.63]", size=9, fill=DARK)
    f.text(ix1 + 10, 246, "• Thực thi như 1 lệnh phần cứng duy nhất", size=9, fill=DARK)
    f.text(ix1 + 10, 263, "• Triệt tiêu ghi tensor trung gian ra DDR", size=9, fill="#15803D")
    f.text(ix1 + 10, 278, "• Tiết kiệm băng thông và giảm độ trễ", size=8.5, fill=GRAY)

    # 1.3 C2f / C3k2 / SPPF
    rect(f, ix1, 298, item_w, 96, fill="white", stroke="#86EFAC", rx=4)
    f.text(ix1 + 10, 316, "Khối C2f, C3k2 & SPPF", size=10.5, weight="bold", fill="#14532D")
    f.text(ix1 + 10, 333, "• Phép cộng Add residual hỗ trợ 3 core [T1]", size=9, fill=DARK)
    f.text(ix1 + 10, 350, "• Split và Concat 100% trong OPL 3.2", size=9, fill=DARK)
    f.text(ix1 + 10, 367, "• SPPF: MaxPool kernel <= 7, auto_pad", size=9, fill=DARK)
    f.text(ix1 + 10, 382, "• Toàn bộ khối chạy trọn vẹn trên NPU", size=8.5, fill="#15803D")

    # --------------------------------------------------------------------------
    # CỘT 2: VÙNG VÀNG - CẦN CẤU HÌNH & TỐI ƯU HÓA
    # --------------------------------------------------------------------------
    x2 = 303
    rect(f, x2, col_y, col_w, col_h, fill="#FEFCE8", stroke="#CA8A04", sw=1.5, rx=6)
    rect(f, x2, col_y, col_w, 35, fill="#FEF9C3", stroke="#CA8A04", sw=1.5, rx=6)
    f.text(x2 + 10, col_y + 15, "2. VÙNG VÀNG: CẦN TỐI ƯU HÓA", size=11, weight="bold", fill="#713F12")
    f.text(x2 + 10, col_y + 28, "Chạy trên NPU nhưng có thể suy giảm hiệu năng", size=8.5, fill="#854D0E")

    ix2 = x2 + 9
    # 2.1 Depthwise Conv
    rect(f, ix2, 90, item_w, 96, fill="white", stroke="#FDE047", rx=4)
    f.text(ix2 + 10, 108, "Depthwise Conv (DWConv)", size=10.5, weight="bold", fill="#713F12")
    f.text(ix2 + 10, 125, "• Có hỗ trợ NPU nhưng MAC utilization thấp", size=9, fill=DARK)
    f.text(ix2 + 10, 142, "• Kênh INT8 bắt buộc bội số 64 [T1 UG232 tr.145]", size=9, fill="#B45309")
    f.text(ix2 + 10, 159, "• Thiếu tái sử dụng dữ liệu chéo kênh", size=9, fill=DARK)
    f.text(ix2 + 10, 174, "• Khuyến nghị: Ưu tiên Conv tiêu chuẩn 3x3", size=8.5, fill="#475569")

    # 2.2 Attention
    rect(f, ix2, 194, item_w, 96, fill="white", stroke="#FDE047", rx=4)
    f.text(ix2 + 10, 212, "Cơ chế chú ý (Attention)", size=10.5, weight="bold", fill="#713F12")
    f.text(ix2 + 10, 229, "• MatMul rời rạc không có NPU tổng quát", size=9, fill="#B45309")
    f.text(ix2 + 10, 246, "• Bắt buộc: Bật enable_flash_attention=True", size=9, fill="#1D4ED8")
    f.text(ix2 + 10, 263, "• Hợp nhất thành op exSDPAttention [T1]", size=9, fill=DARK)
    f.text(ix2 + 10, 278, "• Giới hạn số kênh channel <= 8192 [T1 OPL]", size=8.5, fill=GRAY)

    # 2.3 Data transfer & Resize
    rect(f, ix2, 298, item_w, 96, fill="white", stroke="#FDE047", rx=4)
    f.text(ix2 + 10, 316, "Toán tử chuyển dữ liệu & Resize", size=10.5, weight="bold", fill="#713F12")
    f.text(ix2 + 10, 333, "• Nhóm data transfer: Concat, Split, Reshape", size=9, fill=DARK)
    f.text(ix2 + 10, 350, "• Tiêu hao băng thông DDR, cần tiết giảm [T1]", size=9, fill=DARK)
    f.text(ix2 + 10, 367, "• Resize: Phóng to 2-8x qua ConvTranspose", size=9, fill=DARK)
    f.text(ix2 + 10, 382, "• Không có nhân phần cứng Resize chuyên dụng", size=8.5, fill=GRAY)

    # --------------------------------------------------------------------------
    # CỘT 3: VÙNG ĐỎ - NGUY CƠ RƠI CPU (FALLBACK)
    # --------------------------------------------------------------------------
    x3 = 592
    rect(f, x3, col_y, col_w, col_h, fill="#FEF2F2", stroke="#DC2626", sw=1.5, rx=6)
    rect(f, x3, col_y, col_w, 35, fill="#FEE2E2", stroke="#DC2626", sw=1.5, rx=6)
    f.text(x3 + 10, col_y + 15, "3. VÙNG ĐỎ: NGUY CƠ RƠI CPU", size=11, weight="bold", fill="#7F1D1D")
    f.text(x3 + 10, col_y + 28, "Thiếu nhân phần cứng, gây nghẽn tốc độ nặng", size=8.5, fill="#991B1B")

    ix3 = x3 + 9
    # 3.1 DFL
    rect(f, ix3, 90, item_w, 96, fill="white", stroke="#FCA5A5", rx=4)
    f.text(ix3 + 10, 108, "Khối DFL (Phân bố Box)", size=10.5, weight="bold", fill="#991B1B")
    f.text(ix3 + 10, 125, "• Chứa Reshape + Softmax + Transpose", size=9, fill=DARK)
    f.text(ix3 + 10, 142, "• Kích thước phẳng 16*8400 vượt p=8192 [T1]", size=9, fill="#B91C1C")
    f.text(ix3 + 10, 159, "• Toán tử Transpose bị đẩy về thực thi CPU", size=9, fill=DARK)
    f.text(ix3 + 10, 174, "• Giải pháp: Dùng head trực tiếp không DFL", size=8.5, fill="#15803D")

    # 3.2 End-to-end NMS
    rect(f, ix3, 194, item_w, 96, fill="white", stroke="#FCA5A5", rx=4)
    f.text(ix3 + 10, 212, "End-to-End NMS (Lọc hộp)", size=10.5, weight="bold", fill="#991B1B")
    f.text(ix3 + 10, 229, "• TopK & GatherElements chỉ có trong CPU OPs", size=9, fill=DARK)
    f.text(ix3 + 10, 246, "• NPU không có mạch so sánh / sắp xếp động", size=9, fill=DARK)
    f.text(ix3 + 10, 263, "• Ultralytics Exporter ép tắt end2end=False", size=9, fill="#B91C1C")
    f.text(ix3 + 10, 278, "• Bắt buộc: Đưa NMS ra CPU C++ ngoài đồ thị", size=8.5, fill="#15803D")

    # 3.3 Logic & Cast int64
    rect(f, ix3, 298, item_w, 96, fill="white", stroke="#FCA5A5", rx=4)
    f.text(ix3 + 10, 316, "Toán tử logic & Kiểu int64", size=10.5, weight="bold", fill="#991B1B")
    f.text(ix3 + 10, 333, "• Cast sang int64: NPU không hỗ trợ [T1]", size=9, fill=DARK)
    f.text(ix3 + 10, 350, "• Equal, Mod, ReduceMax: Chỉ có ở Ch.4 CPU", size=9, fill=DARK)
    f.text(ix3 + 10, 367, "• Xuất hiện trong đồ thị sẽ làm phân rã luồng", size=9, fill="#B91C1C")
    f.text(ix3 + 10, 382, "• Thay thế bằng phép tính số học hoặc CPU", size=8.5, fill=GRAY)

    # --------------------------------------------------------------------------
    # THẺ TÓM TẮT BẢN CHẤT THIẾT KẾ
    # --------------------------------------------------------------------------
    rect(f, 14, 424, 852, 54, fill="#F1F5F9", stroke="#94A3B8", rx=4)
    f.text(24, 442, "Quy tắc cốt lõi khi thiết kế detector YOLO trên Rockchip RK3588:",
           size=11, weight="bold", fill=INK)
    f.text(24, 458, "• Kênh Conv luôn chia hết cho 32 (DWConv chia hết 64); loại bỏ DFL chuyển sang hồi quy direct bbox để tránh rơi về CPU.",
           size=9.5, fill=DARK)
    f.text(24, 471, "• Khai thác Conv-Swish hợp nhất; đưa 100% logic TopK/NMS ra CPU máy host viết bằng C++ đa luồng [T1 UG232 tr.145-147] [T1 OPL tr.58-104].",
           size=9.5, fill=DARK)

    # Dòng nguồn
    source(f, 480,
           "[T1 OPL tr.56-107, tr.320-333] [T1 UG232 tr.140-150] [T1 ULT engine/exporter.py:682-688]")

    return f


FIGURES = [
    ("yolo-04-rknn-graph-cut", fig_yolo_rknn_graph_cut),
    ("yolo-05-npu-compatibility-matrix", fig_npu_compatibility_matrix),
]

if __name__ == "__main__":
    run(FIGURES, DEFAULT_OUTDIR)
