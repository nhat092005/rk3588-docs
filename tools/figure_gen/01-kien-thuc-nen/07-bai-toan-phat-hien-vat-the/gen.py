#!/usr/bin/env python3
"""Chuyên đề: Bài toán phát hiện vật thể (07-bai-toan-phat-hien-vat-the.rst).

Sinh 4 hình minh họa kỹ thuật vector SVG chuẩn visual_guide:
  - det-1-bon-tac-vu-thi-giac:
    So sánh 4 tác vụ cốt lõi: Phân loại, Phát hiện, Phân đoạn ngữ nghĩa và Phân đoạn thể hiện trên cùng hoạt cảnh.
  - det-2-bounding-box-va-he-toa-do:
    Hệ tọa độ ảnh (gốc 0,0 trên-trái) và 3 định dạng Bounding Box (xyxy, xywh, xywh chuẩn hóa).
  - det-3-anchor-based-vs-anchor-free:
    Cơ chế dự đoán vị trí: Anchor-based (độ lệch anchor mẫu) vs Anchor-free (4 tia khoảng cách l, t, r, b).
  - det-4-thuat-toan-nms-va-batched-nms:
    Diễn biến thuật toán NMS trên ví dụ số cụ thể (hộp A, B, C, D) và kỹ thuật Batched NMS trên RK3588 (cls * MAX_WH).

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 2 cấp: 07-bai-toan-phat-hien-vat-the -> 01-kien-thuc-nen -> figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "07-bai-toan-phat-hien-vat-the"
    )
)

W = 860
PURPLE = "#7B1FA2"
ORANGE = "#E65100"
TEAL = "#00796B"
GRID = "#E2E8F0"


def tier(f, label, x=W - 130, y=4):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def bbox(f, x, y, w, h, fill="none", stroke="#333333", sw=1.2, dashed=False):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    pts = f"{x},{y} {x+w},{y} {x+w},{y+h} {x},{y+h}"
    f.a(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def circle(f, cx, cy, r, fill="white", stroke="#333333", sw=1.2, dashed=False):
    dash = ' stroke-dasharray="3 2"' if dashed else ""
    f.a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH BỐN TÁC VỤ THỊ GIÁC MÁY TÍNH (det-1)
# ==============================================================================
def fig_four_vision_tasks():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "So sánh 4 tác vụ thị giác máy tính cốt lõi trên cùng hoạt cảnh (2 người, 1 xe)", size=13.5, weight=700, fill=DARK)

    bw = 195
    bh = 225
    y_top = 42
    x_starts = [15, 226, 437, 648]

    def draw_base_scene(x_off, y_off):
        rect(f, x_off, y_off, 175, 115, fill="#F8FAFC", stroke="#94A3B8", sw=1.0, rx=3)
        rect(f, x_off, y_off + 75, 175, 40, fill="#E2E8F0", stroke="none")
        # Người 1
        circle(f, x_off + 32, y_off + 50, 7, fill="#CBD5E1", stroke=DARK)
        rect(f, x_off + 25, y_off + 58, 14, 28, fill="#CBD5E1", stroke=DARK, rx=2)
        # Người 2
        circle(f, x_off + 70, y_off + 50, 7, fill="#CBD5E1", stroke=DARK)
        rect(f, x_off + 63, y_off + 58, 14, 28, fill="#CBD5E1", stroke=DARK, rx=2)
        # Xe ô tô
        rect(f, x_off + 108, y_off + 66, 54, 24, fill="#CBD5E1", stroke=DARK, rx=3)
        rect(f, x_off + 118, y_off + 54, 34, 13, fill="#CBD5E1", stroke=DARK, rx=2)
        circle(f, x_off + 120, y_off + 82, 5, fill="#475569", stroke=DARK)
        circle(f, x_off + 150, y_off + 82, 5, fill="#475569", stroke=DARK)

    # PANEL 1: PHÂN LOẠI
    x1 = x_starts[0]
    rect(f, x1, y_top, bw, bh, fill="#FFFFFF", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x1, y_top, bw, 28, fill="#EFF6FF", stroke=BLUE, sw=1.3, rx=5)
    f.text(x1 + bw / 2, y_top + 19, "1. Phân loại (Classification)", size=9.0, weight=700, fill=BLUE, anchor="middle")

    draw_base_scene(x1 + 10, y_top + 36)

    rect(f, x1 + 10, y_top + 158, 175, 24, fill="#EFF6FF", stroke=BLUE, sw=1, rx=3)
    f.text(x1 + bw / 2, y_top + 174, "Nhãn: \"Công trường\" (0.95)", size=8.0, weight=700, fill=BLUE, anchor="middle")
    f.text(x1 + 12, y_top + 196, "• Một nhãn cho toàn bộ bức ảnh", size=7.8, fill=DARK)
    f.text(x1 + 12, y_top + 210, "• Không biết vị trí và số lượng vật", size=7.8, fill=GRAY)

    # PANEL 2: PHÁT HIỆN
    x2 = x_starts[1]
    rect(f, x2, y_top, bw, bh, fill="#FFFFFF", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2, y_top, bw, 28, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=5)
    f.text(x2 + bw / 2, y_top + 19, "2. Phát hiện (Detection)", size=9.0, weight=700, fill=GREEN, anchor="middle")

    draw_base_scene(x2 + 10, y_top + 36)
    # Bounding Box Người 1
    rect(f, x2 + 32, y_top + 76, 20, 48, fill="none", stroke=GREEN, sw=1.5)
    f.text(x2 + 42, y_top + 70, "person", size=6.5, weight=700, fill=GREEN, anchor="middle")
    # Bounding Box Người 2
    rect(f, x2 + 70, y_top + 76, 20, 48, fill="none", stroke=GREEN, sw=1.5)
    f.text(x2 + 80, y_top + 70, "person", size=6.5, weight=700, fill=GREEN, anchor="middle")
    # Bounding Box Xe bao cả bánh
    rect(f, x2 + 116, y_top + 87, 58, 44, fill="none", stroke=ORANGE, sw=1.5)
    f.text(x2 + 145, y_top + 82, "car: 0.95", size=6.5, weight=700, fill=ORANGE, anchor="middle")

    rect(f, x2 + 10, y_top + 158, 175, 24, fill="#F0FDF4", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + bw / 2, y_top + 174, "Danh sách hộp [xywh, conf, cls]", size=8.0, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 12, y_top + 196, "• Xác định cả vị trí (hộp) và lớp", size=7.8, fill=DARK)
    f.text(x2 + 12, y_top + 210, "• Tách riêng từng vật thể độc lập", size=7.8, fill=GRAY)

    # PANEL 3: PHÂN ĐOẠN NGỮ NGHĨA
    x3 = x_starts[2]
    rect(f, x3, y_top, bw, bh, fill="#FFFFFF", stroke=PURPLE, sw=1.3, rx=5)
    rect(f, x3, y_top, bw, 28, fill="#FAF5FF", stroke=PURPLE, sw=1.3, rx=5)
    f.text(x3 + bw / 2, y_top + 19, "3. Phân đoạn ngữ nghĩa", size=9.0, weight=700, fill=PURPLE, anchor="middle")

    rect(f, x3 + 10, y_top + 36, 175, 115, fill="#E2E8F0", stroke="#94A3B8", sw=1.0, rx=3)
    rect(f, x3 + 10, y_top + 111, 175, 40, fill="#CBD5E1", stroke="none")
    # Người 1 và Người 2 CÙNG MÀU XANH DƯƠNG
    circle(f, x3 + 42, y_top + 86, 7, fill=BLUE, stroke="none")
    rect(f, x3 + 35, y_top + 94, 14, 28, fill=BLUE, stroke="none", rx=2)
    circle(f, x3 + 80, y_top + 86, 7, fill=BLUE, stroke="none")
    rect(f, x3 + 73, y_top + 94, 14, 28, fill=BLUE, stroke="none", rx=2)
    # Xe MÀU CAM
    rect(f, x3 + 118, y_top + 102, 54, 24, fill=ORANGE, stroke="none", rx=3)
    rect(f, x3 + 128, y_top + 90, 34, 13, fill=ORANGE, stroke="none", rx=2)

    rect(f, x3 + 10, y_top + 158, 175, 24, fill="#FAF5FF", stroke=PURPLE, sw=1, rx=3)
    f.text(x3 + bw / 2, y_top + 174, "Mặt nạ điểm ảnh: Pixel -> Lớp", size=8.0, weight=700, fill=PURPLE, anchor="middle")
    f.text(x3 + 12, y_top + 196, "• Nhãn gán cho từng pixel ảnh", size=7.8, fill=DARK)
    f.text(x3 + 12, y_top + 210, "• Hai người bị gộp chung 1 màu", size=7.8, fill=GRAY)

    # PANEL 4: PHÂN ĐOẠN THỂ HIỆN
    x4 = x_starts[3]
    rect(f, x4, y_top, bw, bh, fill="#FFFFFF", stroke=TEAL, sw=1.3, rx=5)
    rect(f, x4, y_top, bw, 28, fill="#F0FDFA", stroke=TEAL, sw=1.3, rx=5)
    f.text(x4 + bw / 2, y_top + 19, "4. Phân đoạn thể hiện", size=9.0, weight=700, fill=TEAL, anchor="middle")

    rect(f, x4 + 10, y_top + 36, 175, 115, fill="#E2E8F0", stroke="#94A3B8", sw=1.0, rx=3)
    rect(f, x4 + 10, y_top + 111, 175, 40, fill="#CBD5E1", stroke="none")
    # Người 1: MÀU XANH DƯƠNG
    circle(f, x4 + 42, y_top + 86, 7, fill=BLUE, stroke="none")
    rect(f, x4 + 35, y_top + 94, 14, 28, fill=BLUE, stroke="none", rx=2)
    rect(f, x4 + 32, y_top + 76, 20, 48, fill="none", stroke=BLUE, sw=1, dashed=True)
    # Người 2: MÀU TÍM
    circle(f, x4 + 80, y_top + 86, 7, fill=PURPLE, stroke="none")
    rect(f, x4 + 73, y_top + 94, 14, 28, fill=PURPLE, stroke="none", rx=2)
    rect(f, x4 + 70, y_top + 76, 20, 48, fill="none", stroke=PURPLE, sw=1, dashed=True)
    # Xe: MÀU CAM
    rect(f, x4 + 118, y_top + 102, 54, 24, fill=ORANGE, stroke="none", rx=3)
    rect(f, x4 + 128, y_top + 90, 34, 13, fill=ORANGE, stroke="none", rx=2)
    rect(f, x4 + 116, y_top + 87, 58, 44, fill="none", stroke=ORANGE, sw=1, dashed=True)

    rect(f, x4 + 10, y_top + 158, 175, 24, fill="#F0FDFA", stroke=TEAL, sw=1, rx=3)
    f.text(x4 + bw / 2, y_top + 174, "Mặt nạ pixel riêng cho từng cá thể", size=8.0, weight=700, fill=TEAL, anchor="middle")
    f.text(x4 + 12, y_top + 196, "• Phân biệt từng người 1 và người 2", size=7.8, fill=DARK)
    f.text(x4 + 12, y_top + 210, "• Chi phí tính toán cao nhất", size=7.8, fill=GRAY)

    # KHUNG BẢNG TÓM TẮT DƯỚI ĐÁY
    box_y = 280
    box_h = 130
    rect(f, 15, box_y, 830, box_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, box_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, box_y + 16, "ĐỐI CHIẾU ĐẦU RA VÀ MỨC ĐỘ CHI TIẾT KHÔNG GIAN CỦA 4 TÁC VỤ", size=9.5, weight=700, fill=DARK)

    col_sub_w = 200
    for idx, (title, color, out_desc, note_desc) in enumerate([
        ("Phân loại ảnh", BLUE, "Một nhãn lớp cho cả ảnh", "Không định vị vật thể; giả định 1 đối tượng chính"),
        ("Phát hiện vật thể", GREEN, "Danh sách hộp (x, y, w, h) + lớp", "Trọng tâm dự án; YOLO xuất tọa độ và nhãn"),
        ("Phân đoạn ngữ nghĩa", PURPLE, "Bản đồ nhãn theo pixel (H × W)", "Gộp mọi cá thể cùng lớp thành 1 vùng màu"),
        ("Phân đoạn thể hiện", TEAL, "Mặt nạ pixel riêng từng cá thể", "Phức tạp nhất; phân biệt rõ người 1 và người 2"),
    ]):
        x_c = 25 + idx * col_sub_w
        f.text(x_c, box_y + 44, f"• {title}:", size=8.8, weight=700, fill=color)
        f.text(x_c + 8, box_y + 62, "Đầu ra:", size=8.0, weight=600, fill=DARK)
        f.text(x_c + 8, box_y + 76, out_desc, size=7.8, fill=DARK)
        f.text(x_c + 8, box_y + 94, "Đặc trưng:", size=8.0, weight=600, fill=GRAY)
        f.text(x_c + 8, box_y + 108, note_desc, size=7.5, fill=GRAY)

    source(f, 418, "Nguồn: T2 D2L tr.606, tr.609, tr.648 (Chương 14.1 và 14.9); T2 YOLOv4 tr.2.")
    return f


# ==============================================================================
# 2. HÌNH BOUNDING BOX VÀ HỆ TỌA ĐỘ (det-2)
# ==============================================================================
def fig_bounding_box_formats():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Hệ tọa độ ảnh và 3 định dạng biểu diễn Bounding Box: xyxy, xywh và xywh chuẩn hóa", size=13.5, weight=700, fill=DARK)

    # NỬA TRÁI: HỆ TỌA ĐỘ ẢNH (x=15..440)
    canvas_w = 425
    canvas_h = 225
    x_cv = 15
    y_cv = 42
    rect(f, x_cv, y_cv, canvas_w, canvas_h, fill="#F8FAFC", stroke="#94A3B8", sw=1.2, rx=5)

    circle(f, x_cv + 25, y_cv + 25, 4, fill=RED, stroke=RED)
    f.text(x_cv + 35, y_cv + 18, "(0, 0) Gốc tọa độ trên-trái", size=8.5, weight=700, fill=RED)
    arrow(f, x_cv + 25, y_cv + 25, x_cv + 160, y_cv + 25, color=DARK, sw=1.5)
    f.text(x_cv + 168, y_cv + 28, "Trục X (chiều rộng W)", size=8.0, fill=DARK)
    arrow(f, x_cv + 25, y_cv + 25, x_cv + 25, y_cv + 120, color=DARK, sw=1.5)
    f.text(x_cv + 32, y_cv + 115, "Trục Y (chiều cao H)", size=8.0, fill=DARK)

    f.text(x_cv + canvas_w - 15, y_cv + canvas_h - 10, "Kích thước ảnh: W × H (vd: 640 × 480)", size=7.8, fill=GRAY, anchor="end")

    bx1 = x_cv + 110
    by1 = y_cv + 55
    bw_box = 210
    bh_box = 125
    bx2 = bx1 + bw_box
    by2 = by1 + bh_box
    bcx = bx1 + bw_box / 2
    bcy = by1 + bh_box / 2

    # Vẽ vật thể
    circle(f, bcx, bcy - 18, 14, fill="#CBD5E1", stroke=DARK)
    rect(f, bcx - 18, bcy - 2, 36, 48, fill="#CBD5E1", stroke=DARK, rx=4)

    rect(f, bx1, by1, bw_box, bh_box, fill="none", stroke=GREEN, sw=2.0)

    circle(f, bx1, by1, 4, fill=GREEN, stroke=DARK)
    f.text(bx1 - 6, by1 - 6, "(x₁, y₁)", size=8.8, weight=700, fill=GREEN, anchor="end")

    circle(f, bx2, by2, 4, fill=GREEN, stroke=DARK)
    f.text(bx2 + 6, by2 + 14, "(x₂, y₂)", size=8.8, weight=700, fill=GREEN)

    circle(f, bcx, bcy, 4, fill=BLUE, stroke=DARK)
    f.text(bcx + 24, bcy - 6, "Tâm (c_x, c_y)", size=8.5, weight=700, fill=BLUE)

    # Chiều rộng w
    f.line([(bx1, by2 + 12), (bx2, by2 + 12)], BLUE, width=1.2, head=False)
    arrow(f, bcx - 15, by2 + 12, bx1, by2 + 12, color=BLUE, sw=1.2)
    arrow(f, bcx + 15, by2 + 12, bx2, by2 + 12, color=BLUE, sw=1.2)
    f.text(bcx, by2 + 24, "Chiều rộng: w = x₂ - x₁", size=8.0, weight=600, fill=BLUE, anchor="middle")

    # Chiều cao h
    f.line([(bx2 + 12, by1), (bx2 + 12, by2)], BLUE, width=1.2, head=False)
    arrow(f, bx2 + 12, bcy - 15, bx2 + 12, by1, color=BLUE, sw=1.2)
    arrow(f, bx2 + 12, bcy + 15, bx2 + 12, by2, color=BLUE, sw=1.2)
    f.text(bx2 + 18, bcy + 3, "h = y₂ - y₁", size=8.0, weight=600, fill=BLUE)

    # NỬA PHẢI: 3 ĐỊNH DẠNG (x=455..845)
    r_w = 390
    card_h = 68
    x_r = 455

    rect(f, x_r, y_cv, r_w, card_h, fill="#FFFFFF", stroke=GREEN, sw=1.3, rx=4)
    rect(f, x_r, y_cv, r_w, 22, fill="#DCFCE7", stroke=GREEN, sw=1.3, rx=4)
    f.text(x_r + 12, y_cv + 15, "1. Định dạng xyxy: (x₁, y₁, x₂, y₂) theo pixel", size=9.0, weight=700, fill=GREEN)
    f.text(x_r + 12, y_cv + 38, "• Tọa độ hai góc cực: góc trên-trái và góc dưới-phải.", size=8.2, fill=DARK)
    f.text(x_r + 12, y_cv + 54, "• Chuẩn hiển thị OpenCV (cv2.rectangle), tính giao/hợp IoU, NMS.", size=8.0, fill=GRAY)

    rect(f, x_r, y_cv + 78, r_w, card_h, fill="#FFFFFF", stroke=BLUE, sw=1.3, rx=4)
    rect(f, x_r, y_cv + 78, r_w, 22, fill="#DBEAFE", stroke=BLUE, sw=1.3, rx=4)
    f.text(x_r + 12, y_cv + 93, "2. Định dạng xywh: (c_x, c_y, w, h) theo pixel", size=9.0, weight=700, fill=BLUE)
    f.text(x_r + 12, y_cv + 116, "• Tọa độ tâm hình học và kích thước rộng, cao của hộp.", size=8.2, fill=DARK)
    f.text(x_r + 12, y_cv + 132, "• Chuẩn đầu ra mô hình hồi quy (độ lệch anchor hoặc bounding head).", size=8.0, fill=GRAY)

    rect(f, x_r, y_cv + 156, r_w, card_h + 1, fill="#FFFFFF", stroke=PURPLE, sw=1.3, rx=4)
    rect(f, x_r, y_cv + 156, r_w, 22, fill="#F3E8FF", stroke=PURPLE, sw=1.3, rx=4)
    f.text(x_r + 12, y_cv + 171, "3. Định dạng xywh chuẩn hóa: (c_x/W, c_y/H, w/W, h/H) ∈ [0, 1]", size=8.8, weight=700, fill=PURPLE)
    f.text(x_r + 12, y_cv + 194, "• Chia tọa độ cho kích thước ảnh: độc lập với độ phân giải đầu vào.", size=8.2, fill=DARK)
    f.text(x_r + 12, y_cv + 210, "• Định dạng nhãn huấn luyện Ultralytics YOLO (.txt 5 cột: cls cx cy w h).", size=8.0, fill=GRAY)

    # KHUNG CÔNG THỨC CHUYỂN ĐỔI DƯỚI ĐÁY
    box_y = 280
    box_h = 115
    rect(f, 15, box_y, 830, box_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, box_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, box_y + 16, "CÔNG THỨC CHUYỂN ĐỔI HAI CHIỀU VÀ VÍ DỤ SỐ ĐỐI CHIẾU", size=9.5, weight=700, fill=DARK)

    f.text(35, box_y + 44, "Từ xyxy sang xywh (Tính tâm và kích thước):", size=8.8, weight=700, fill=BLUE)
    f.text(45, box_y + 62, "c_x = (x₁ + x₂) / 2 ,   c_y = (y₁ + y₂) / 2", size=8.5, weight=600, fill=DARK)
    f.text(45, box_y + 78, "w = x₂ - x₁ ,   h = y₂ - y₁", size=8.5, weight=600, fill=DARK)
    f.text(35, box_y + 98, "Chuẩn hóa: c_x_norm = c_x / W ,  w_norm = w / W", size=8.0, fill=GRAY)

    f.text(455, box_y + 44, "Từ xywh sang xyxy (Tính hai góc cực):", size=8.8, weight=700, fill=GREEN)
    f.text(465, box_y + 62, "x₁ = c_x - w / 2 ,   y₁ = c_y - h / 2", size=8.5, weight=600, fill=DARK)
    f.text(465, box_y + 78, "x₂ = c_x + w / 2 ,   y₂ = c_y + h / 2", size=8.5, weight=600, fill=DARK)
    f.text(455, box_y + 98, "Ví dụ đối chiếu: W×H=640×480, hộp (160, 120, 480, 360) -> norm (0.5, 0.5, 0.5, 0.5)", size=7.8, fill=GRAY)

    source(f, 400, "Nguồn: T2 D2L tr.607-608; T1 ultralytics data/utils.py:348-358. Gốc tọa độ ảnh quy ước ở góc trên-trái (0, 0).")
    return f


# ==============================================================================
# 2b. HÌNH ĐỊNH DẠNG NHÃN VÀ PHÂN LOẠI MẪU DƯƠNG / ÂM (det-2b) - VISUAL-FIRST
# ==============================================================================
def fig_label_class_and_samples():
    """HÌNH 2b: Cấu trúc file nhãn Ultralytics YOLO và Cơ chế phân loại Mẫu Dương vs Mẫu Âm."""
    W_FIG = 880
    H_FIG = 350
    f = Fig(W_FIG, H_FIG)
    f.tier(W_FIG - 130, 11, "T2 chung")

    f.text(18, 22, "Định dạng Nhãn Ultralytics YOLO và Cơ chế Phân loại Mẫu Dương vs Mẫu Âm",
           size=13.5, weight=700, fill=DARK)

    card_w = 415
    card_h = 262
    y_top = 44
    x1 = 18
    x2 = 447

    # ==========================================================================
    # CỘT TRÁI: PANEL A - CẤU TRÚC FILE NHÃN VÀ ÁNH XẠ CLASS
    # ==========================================================================
    rect(f, x1, y_top, card_w, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x1, y_top, card_w, 26, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x1 + 8, y_top + 4, 6, 18, fill=BLUE, stroke=BLUE, rx=2)
    f.text(x1 + 22, y_top + 14, "A. Cấu trúc File Nhãn Ultralytics & Ánh xạ Class",
           size=10.5, weight=700, fill="#1E40AF")

    # 1. Khung Ảnh mẫu + File nhãn
    by = y_top + 34
    bh = 96
    iw = 135

    # Ảnh mẫu (640x640)
    rect(f, x1 + 12, by, iw, bh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.line([(x1 + 18, by + 86), (x1 + 12 + iw - 6, by + 86)], GRAY, width=THIN, dashed=True, head=False)

    # Box Person (cls 0) - dùng bbox để tránh cảnh báo EMPTY_SPACE của rect
    p_x, p_y, p_w, p_h = x1 + 26, by + 32, 56, 52
    bbox(f, p_x, p_y, p_w, p_h, stroke=BLUE, sw=1.4)
    rect(f, p_x, p_y - 10, 36, 10, fill=BLUE, stroke=BLUE, rx=1)
    f.text(p_x + 18, p_y - 5, "person 0", size=6.8, weight=700, fill="white", anchor="middle")

    # Box Helmet (cls 1) - dùng bbox
    h_x, h_y, h_w, h_h = x1 + 38, by + 34, 30, 20
    bbox(f, h_x, h_y, h_w, h_h, stroke=GREEN, sw=1.4)
    rect(f, h_x + 2, h_y + 23, 34, 11, fill=GREEN, stroke=GREEN, rx=1)
    f.text(h_x + 19, h_y + 28.5, "helmet 1", size=6.6, weight=700, fill="white", anchor="middle")

    # Tiêu đề ảnh đặt sau để tránh lỗi Z-order
    f.text(x1 + 18, by + 10, "Ảnh mẫu: 640×640 px", size=7.5, weight=700, fill=DARK)

    # File nhãn text
    fx = x1 + 12 + iw + 10
    fw = card_w - 24 - iw - 10
    rect(f, fx, by, fw, bh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    rect(f, fx, by, fw, 18, fill="#F1F5F9", stroke="#CBD5E1", rx=2)
    f.text(fx + 8, by + 9, "File nhãn: labels/train_001.txt", size=7.2, weight=700, fill=DARK)

    f.text(fx + 8, by + 27, "5 giá trị / dòng (chuẩn hóa [0.0, 1.0]):", size=7.2, weight=700, fill="#1E40AF")
    f.text(fx + 8, by + 40, "cls_id   x_center  y_center  width   height", size=7.0, mono=True, weight=700, fill=DARK)
    f.text(fx + 8, by + 54, "  0      0.4150    0.5500    0.3700  0.6000", size=7.0, mono=True, fill=BLUE)
    f.text(fx + 8, by + 68, "  1      0.4150    0.3600    0.2200  0.2100", size=7.0, mono=True, fill=GREEN)
    f.text(fx + 8, by + 84, "• x, w chia cho W_ảnh (640); y, h chia cho H_ảnh (640)", size=6.8, fill="#64748B")

    # 2. Khung Từ điển dataset.yaml
    my = by + bh + 10
    mw = card_w - 24
    mh = 48
    rect(f, x1 + 12, my, mw, mh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    rect(f, x1 + 12, my, mw, 16, fill="#F8FAFC", stroke="#CBD5E1", rx=2)
    f.text(x1 + 18, my + 8, "Khai báo từ điển danh mục lớp: dataset.yaml", size=7.2, weight=700, fill=DARK)
    f.text(x1 + 18, my + 25, "names: { 0: 'person', 1: 'helmet' }   |   nc: 2", size=7.2, mono=True, weight=700, fill=DARK)
    f.text(x1 + 18, my + 38, "• nc (number of classes) = 2; chỉ số lớp hợp lệ: 0 <= class_idx < nc", size=7.0, fill="#475569")

    # 3. Khung Chốt chặn an toàn Sanity Check
    gy = my + mh + 10
    gh = 48
    rect(f, x1 + 12, gy, mw, gh, fill="#FEF2F2", stroke=RED, sw=1.0, rx=3)
    rect(f, x1 + 12, gy, mw, 16, fill="#FEE2E2", stroke=RED, rx=2)
    f.text(x1 + 18, gy + 8, "Cơ chế kiểm tra chặn lỗi vượt số lớp (Sanity Check):", size=7.2, weight=700, fill="#991B1B")
    f.text(x1 + 18, gy + 25, "assert (lb[:, 0] < nc).all()   -> Nếu class >= nc: quăng ngoại lệ ngắt train", size=7.0, mono=True, fill="#7F1D1D")
    f.text(x1 + 18, gy + 38, 'Báo lỗi: "Label class 2 exceeds dataset class count 2" [T1 data/utils.py:365]', size=6.8, italic=True, fill="#991B1B")

    # ==========================================================================
    # CỘT PHẢI: PANEL B - PHÂN LOẠI MẪU DƯƠNG VS MẪU ÂM
    # ==========================================================================
    rect(f, x2, y_top, card_w, card_h, fill="#F8FAFC", stroke="#059669", sw=1.3, rx=6)
    rect(f, x2, y_top, card_w, 26, fill="#ECFDF5", stroke="#059669", sw=1.0, rx=6)
    rect(f, x2 + 8, y_top + 4, 6, 18, fill=GREEN, stroke=GREEN, rx=2)
    f.text(x2 + 22, y_top + 14, "B. Cơ chế Phân loại: Mẫu Dương (Foreground) vs Mẫu Âm (Background)",
           size=10.5, weight=700, fill="#047857")

    # 1. Khung Lưới đặc trưng + Định nghĩa
    gw = 135
    rect(f, x2 + 12, by, gw, bh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x2 + 18, by + 12, "Lưới mẫu đặc trưng (Feature Grid)", size=7.5, weight=700, fill=DARK)

    # Vẽ lưới 5x4
    gx0, gy0 = x2 + 16, by + 22
    cw, ch = 24, 16
    grid_data = [
        ["bg", "bg", "c1", "bg", "bg"],
        ["bg", "c0", "c0", "bg", "bg"],
        ["bg", "c0", "c0", "bg", "bg"],
        ["bg", "bg", "bg", "bg", "bg"],
    ]
    for r_idx in range(4):
        for c_idx in range(5):
            cx_pos = gx0 + c_idx * (cw + 1)
            cy_pos = gy0 + r_idx * (ch + 1)
            val = grid_data[r_idx][c_idx]
            if val == "c0":
                rect(f, cx_pos, cy_pos, cw, ch, fill="#DBEAFE", stroke=BLUE, rx=1)
                f.text(cx_pos + cw / 2, cy_pos + ch / 2, "c0", size=6.8, weight=700, fill=BLUE, anchor="middle")
            elif val == "c1":
                rect(f, cx_pos, cy_pos, cw, ch, fill="#DCFCE7", stroke=GREEN, rx=1)
                f.text(cx_pos + cw / 2, cy_pos + ch / 2, "c1", size=6.8, weight=700, fill=GREEN, anchor="middle")
            else:
                rect(f, cx_pos, cy_pos, cw, ch, fill="#F1F5F9", stroke="#CBD5E1", rx=1)
                f.text(cx_pos + cw / 2, cy_pos + ch / 2, "bg", size=6.8, fill="#64748B", anchor="middle")

    # Định nghĩa Mẫu Dương / Mẫu Âm
    rx = x2 + 12 + gw + 10
    rw = card_w - 24 - gw - 10
    rect(f, rx, by, rw, bh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    rect(f, rx, by, rw, 18, fill="#F8FAFC", stroke="#CBD5E1", rx=2)
    f.text(rx + 8, by + 9, "Định nghĩa Mẫu Dương vs Mẫu Âm", size=7.2, weight=700, fill=DARK)

    # Mẫu Dương chip (tăng chiều cao lên 34px)
    rect(f, rx + 8, by + 22, rw - 16, 34, fill="#F0FDF4", stroke="#16A34A", rx=2)
    rect(f, rx + 12, by + 26, 8, 8, fill="#DCFCE7", stroke="#16A34A", rx=1)
    f.text(rx + 24, by + 30, "Mẫu Dương (Positive / Foreground):", size=7.0, weight=700, fill="#166534")
    f.text(rx + 12, by + 41, "• Anchor/pixel nằm trong vật thể (IoU/khoảng cách)", size=6.8, fill=DARK)
    f.text(rx + 12, by + 50, "• Gán nhãn: c ∈ {0, 1} (person hoặc helmet)", size=6.8, weight=700, fill="#166534")

    # Mẫu Âm chip (tăng chiều cao lên 34px)
    rect(f, rx + 8, by + 58, rw - 16, 34, fill="#F8FAFC", stroke="#94A3B8", rx=2)
    rect(f, rx + 12, by + 62, 8, 8, fill="#F1F5F9", stroke="#94A3B8", rx=1)
    f.text(rx + 24, by + 66, "Mẫu Âm (Negative / Background):", size=7.0, weight=700, fill="#475569")
    f.text(rx + 12, by + 77, "• Vùng nền trống, không chứa vật thể nào", size=6.8, fill=DARK)
    f.text(rx + 12, by + 86, "• Gán nhãn: Nền (background, hoặc c* = 0)", size=6.8, fill="#475569")

    # 2. Bảng Tác động Loss
    rect(f, x2 + 12, my, mw, mh, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    rect(f, x2 + 12, my, mw, 16, fill="#F8FAFC", stroke="#CBD5E1", rx=2)
    f.text(x2 + 18, my + 8, "Tác động lên Hàm mất mát (Loss Function Impact):", size=7.2, weight=700, fill=DARK)

    # Row 1 (Mẫu Dương)
    rect(f, x2 + 16, my + 19, 58, 12, fill="#DCFCE7", stroke="#16A34A", rx=2)
    f.text(x2 + 45, my + 25, "Mẫu Dương", size=6.8, weight=700, fill="#166534", anchor="middle")
    f.text(x2 + 80, my + 25, "Tính đầy đủ: Loss Tọa độ (L_box + L_dfl) + Loss Phân loại (L_cls)", size=7.0, weight=700, fill="#166534")

    # Row 2 (Mẫu Âm)
    rect(f, x2 + 16, my + 33, 58, 12, fill="#F1F5F9", stroke="#94A3B8", rx=2)
    f.text(x2 + 45, my + 39, "Mẫu Âm", size=6.8, weight=700, fill="#475569", anchor="middle")
    f.text(x2 + 80, my + 39, "BỎ QUA Loss Tọa độ (L_box = 0); CHỈ tính Loss Phân loại triệt tiêu nền", size=7.0, fill=DARK)

    # 3. Khung Ý nghĩa thực tế
    rect(f, x2 + 12, gy, mw, gh, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=3)
    rect(f, x2 + 12, gy, mw, 16, fill="#DBEAFE", stroke=BLUE, rx=2)
    f.text(x2 + 18, gy + 8, "Ý nghĩa thực tế: Vấn đề mất cân bằng mẫu cực đoan (Class Imbalance)", size=7.2, weight=700, fill="#1E40AF")
    f.text(x2 + 18, gy + 25, "• Trong ảnh, mẫu âm (nền) chiếm hàng ngàn pixel/anchor, áp đảo mẫu dương (vài chục).", size=6.8, fill=DARK)
    f.text(x2 + 18, gy + 38, "• Vì vậy detector cần Focal Loss / BCE có trọng số để không bị mẫu nền áp đảo gradient.", size=6.8, weight=700, fill="#1E40AF")

    source(f, y_top + card_h + 8, "Nguồn: T1 ultralytics 8.4.154 data/utils.py:340-365; T2 D2L tr.616; T2 FCOS tr.4.")
    return f


# ==============================================================================
# 3. HÌNH ANCHOR-BASED VS ANCHOR-FREE (det-3)
# ==============================================================================
def fig_anchor_based_vs_free():
    H = 422
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Cơ chế dự đoán vị trí hộp: Anchor-based (độ lệch anchor) vs Anchor-free (khoảng cách l, t, r, b)", size=13.5, weight=700, fill=DARK)

    col_w = 405
    col_h = 205
    x1 = 15
    x2 = 440
    y_top = 42

    # --- PANEL TRÁI: ANCHOR-BASED ---
    rect(f, x1, y_top, col_w, col_h, fill="#FFFFFF", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x1, y_top, col_w, 28, fill="#EFF6FF", stroke=BLUE, sw=1.3, rx=5)
    f.text(x1 + col_w / 2, y_top + 19, "Trường phái Anchor-based (Hộp mẫu tham chiếu)", size=9.5, weight=700, fill=BLUE, anchor="middle")

    rect(f, x1 + 15, y_top + 38, 140, 140, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x1 + 85, y_top + 50, "Ground Truth (hộp xanh lá)", size=7.2, weight=700, fill=GREEN, anchor="middle")

    cx_a = x1 + 85
    cy_a = y_top + 112

    # 3 Anchor mẫu khác tỉ lệ
    bbox(f, cx_a - 40, cy_a - 40, 80, 80, fill="none", stroke=BLUE, sw=1.2, dashed=True)
    bbox(f, cx_a - 55, cy_a - 28, 110, 56, fill="none", stroke=BLUE, sw=1.0, dashed=True)
    bbox(f, cx_a - 28, cy_a - 55, 56, 110, fill="none", stroke=BLUE, sw=1.0, dashed=True)

    # Ground Truth Box
    bbox(f, cx_a - 30, cy_a - 50, 75, 95, fill="none", stroke=GREEN, sw=2.0)

    # Tâm anchor (xa, ya)
    circle(f, cx_a, cy_a, 4, fill=RED, stroke=DARK)
    f.text(cx_a, cy_a + 14, "(x_a, y_a)", size=7.5, weight=700, fill=RED, anchor="middle")

    # Mũi tên dự đoán offset dài 25px
    arrow(f, cx_a, cy_a, cx_a + 22, cy_a - 14, color=RED, sw=1.5)
    f.text(x1 + 85, y_top + 190, "Dự đoán độ lệch (Δx, Δy, Δw, Δh) so với anchor", size=7.6, weight=700, fill=BLUE, anchor="middle")

    f.text(x1 + 165, y_top + 46, "Đặc điểm Anchor-based:", size=8.5, weight=700, fill=DARK)
    f.text(x1 + 165, y_top + 64, "• Đặt trước nhiều hộp mẫu (anchor)", size=8.0, fill=DARK)
    f.text(x1 + 172, y_top + 78, "  với kích cỡ và tỉ lệ cạnh khác nhau.", size=7.8, fill=GRAY)
    f.text(x1 + 165, y_top + 96, "• Đích học: Mạng không đoán box trực tiếp", size=8.0, fill=DARK)
    f.text(x1 + 172, y_top + 110, "  mà dự đoán độ lệch so với anchor mẫu.", size=7.8, fill=GRAY)
    f.text(x1 + 165, y_top + 128, "• Gán nhãn huấn luyện: Tính IoU giữa", size=8.0, fill=DARK)
    f.text(x1 + 172, y_top + 142, "  mọi anchor và ground truth (tốn RAM).", size=7.8, fill=GRAY)
    f.text(x1 + 165, y_top + 162, "• Nhược điểm: Rất nhạy cảm với siêu", size=8.0, weight=600, fill=RED)
    f.text(x1 + 172, y_top + 176, "  tham số anchor (số lượng, tỉ lệ).", size=7.8, fill=RED)

    # --- PANEL PHẢI: ANCHOR-FREE ---
    rect(f, x2, y_top, col_w, col_h, fill="#FFFFFF", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2, y_top, col_w, 28, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=5)
    f.text(x2 + col_w / 2, y_top + 19, "Trường phái Anchor-free (Dự đoán điểm & 4 tia khoảng cách)", size=9.5, weight=700, fill=GREEN, anchor="middle")

    rect(f, x2 + 15, y_top + 38, 140, 140, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=3)

    gt_x1 = x2 + 35
    gt_y1 = y_top + 50
    gt_w = 100
    gt_h = 110
    bbox(f, gt_x1, gt_y1, gt_w, gt_h, fill="none", stroke=GREEN, sw=2.0)
    f.text(gt_x1 + gt_w - 8, gt_y1 + 14, "Ground Truth", size=7.2, weight=700, fill=GREEN, anchor="end")

    px = x2 + 75
    py = y_top + 115
    circle(f, px, py, 4, fill=RED, stroke=DARK)
    f.text(px - 8, py + 16, "(x, y)", size=8.0, weight=700, fill=RED, anchor="end")

    # 4 tia khoảng cách l, t, r, b
    arrow(f, px, py, gt_x1, py, color=BLUE, sw=1.6)
    f.text((px + gt_x1) / 2, py - 6, "l", size=8.0, weight=700, fill=BLUE, anchor="middle")
    arrow(f, px, py, px, gt_y1, color=BLUE, sw=1.6)
    f.text(px + 6, (py + gt_y1) / 2, "t", size=8.0, weight=700, fill=BLUE)
    arrow(f, px, py, gt_x1 + gt_w, py, color=BLUE, sw=1.6)
    f.text((px + gt_x1 + gt_w) / 2, py - 6, "r", size=8.0, weight=700, fill=BLUE, anchor="middle")
    arrow(f, px, py, px, gt_y1 + gt_h, color=BLUE, sw=1.6)
    f.text(px + 6, (py + gt_y1 + gt_h) / 2, "b", size=8.0, weight=700, fill=BLUE)

    f.text(x2 + 85, y_top + 192, "Hồi quy trực tiếp: [x - l, y - t, x + r, y + b]", size=7.6, weight=700, fill=GREEN, anchor="middle")

    f.text(x2 + 165, y_top + 46, "Đặc điểm Anchor-free (FCOS/YOLO):", size=8.5, weight=700, fill=DARK)
    f.text(x2 + 165, y_top + 64, "• Loại bỏ hoàn toàn hộp anchor mẫu,", size=8.0, fill=DARK)
    f.text(x2 + 172, y_top + 78, "  triệt tiêu toàn bộ siêu tham số nhạy cảm.", size=7.8, fill=GRAY)
    f.text(x2 + 165, y_top + 96, "• Mỗi điểm (x, y) trong vật thể là mẫu dương,", size=8.0, fill=DARK)
    f.text(x2 + 172, y_top + 110, "  dự đoán 4 khoảng cách (l, t, r, b) tới 4 cạnh.", size=7.8, fill=GRAY)
    f.text(x2 + 165, y_top + 128, "• Không cần tính toán ma trận IoU gán nhãn", size=8.0, fill=DARK)
    f.text(x2 + 172, y_top + 142, "  lúc train -> huấn luyện nhanh và nhẹ hơn.", size=7.8, fill=GRAY)
    f.text(x2 + 165, y_top + 162, "• Ưu thế: Kiến trúc hiện đại (YOLOv8 -> v26)", size=8.0, weight=600, fill=GREEN)
    f.text(x2 + 172, y_top + 176, "  dùng decoupled head anchor-free.", size=7.8, fill=GREEN)

    # KHUNG BẢNG ĐỐI CHIẾU DƯỚI ĐÁY
    box_y = 262
    box_h = 130
    rect(f, 15, box_y, 830, box_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, box_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, box_y + 16, "BẢNG ĐỐI CHIẾU 4 TIÊU CHÍ CỐT LÕI GIỮA ANCHOR-BASED VÀ ANCHOR-FREE", size=9.5, weight=700, fill=DARK)

    col_w_tbl = 195
    rows = [
        ("1. Hộp tham chiếu", "Anchor đặt sẵn quanh pixel", "Không dùng, mỗi vị trí là 1 mẫu"),
        ("2. Đích hồi quy", "Độ lệch (Δx, Δy, log w, log h)", "Khoảng cách 4 cạnh (l, t, r, b)"),
        ("3. Gán mẫu dương", "Theo ngưỡng IoU với anchor", "Điểm nằm trong hộp thật là mẫu dương"),
        ("4. Siêu tham số", "Kích thước, tỉ lệ cạnh anchor", "Không phụ thuộc siêu tham số anchor"),
    ]
    for idx, (crit, ab_val, af_val) in enumerate(rows):
        x_c = 25 + idx * col_w_tbl
        f.text(x_c, box_y + 44, f"• {crit}:", size=8.5, weight=700, fill=DARK)
        f.text(x_c + 8, box_y + 64, "Anchor-based:", size=7.8, weight=600, fill=BLUE)
        f.text(x_c + 8, box_y + 78, ab_val, size=7.5, fill=DARK)
        f.text(x_c + 8, box_y + 96, "Anchor-free:", size=7.8, weight=600, fill=GREEN)
        f.text(x_c + 8, box_y + 110, af_val, size=7.5, fill=DARK)

    source(f, 396, "Nguồn: T2 D2L tr.609-616; T2 FCOS tr.1-4; T2 Sapkota tr.2-3 (YOLOv8 decoupled head).")
    return f


# ==============================================================================
# 4. HÌNH THUẬT TOÁN NMS VÀ BATCHED NMS (det-4)
# ==============================================================================
def fig_nms_and_batched_nms():
    H = 475
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(12, 18, "Thuật toán Non-Maximum Suppression (NMS) và kỹ thuật Batched NMS trên RK3588", size=13.5, weight=700, fill=DARK)

    # PHẦN 1: DIỄN BIẾN THUẬT TOÁN NMS TRÊN VÍ DỤ SỐ (y=40..250)
    top_h = 205
    y_top = 40
    rect(f, 15, y_top, 830, top_h, fill="#FFFFFF", stroke=BLUE, sw=1.3, rx=5)
    rect(f, 15, y_top, 830, 24, fill="#EFF6FF", stroke=BLUE, sw=1.3, rx=5)
    f.text(25, y_top + 16, "PHẦN 1: DIỄN BIẾN THUẬT TOÁN NMS TRÊN VÍ DỤ SỐ CỤ THỂ (HỘP A, B, C, D)", size=9.2, weight=700, fill=BLUE)

    rect(f, 25, y_top + 34, 250, 160, fill="#F8FAFC", stroke="#CBD5E1", sw=1, rx=3)
    f.text(35, y_top + 48, "Phân bố 4 hộp ứng viên ban đầu:", size=8.0, weight=600, fill=DARK)

    # Hộp A: (10, 10, 110, 110) điểm 0.9
    bbox(f, 45, y_top + 62, 80, 80, fill="none", stroke=GREEN, sw=2.0)
    f.text(45, y_top + 56, "A (0.9)", size=7.8, weight=700, fill=GREEN)

    # Hộp B: (20, 20, 120, 120) điểm 0.8
    bbox(f, 53, y_top + 70, 80, 80, fill="none", stroke=RED, sw=1.4, dashed=True)
    f.text(137, y_top + 66, "B (0.8)", size=7.5, weight=700, fill=RED)

    # Hộp D: (30, 30, 130, 130) điểm 0.6
    bbox(f, 61, y_top + 78, 80, 80, fill="none", stroke=ORANGE, sw=1.2, dashed=True)
    f.text(61, y_top + 170, "D (0.6)", size=7.5, weight=700, fill=ORANGE)

    # Hộp C: (150, 150, 250, 250) điểm 0.7
    bbox(f, 165, y_top + 95, 75, 75, fill="none", stroke=BLUE, sw=1.8)
    f.text(165, y_top + 88, "C (0.7)", size=7.8, weight=700, fill=BLUE)

    f.text(35, y_top + 185, "IoU(A, B) = 0.68 | IoU(A, D) = 0.47 | C tách biệt", size=7.4, fill=GRAY)

    # Ngưỡng 0.5
    rect(f, 290, y_top + 34, 260, 160, fill="#FFF5F5", stroke=RED, sw=1.2, rx=4)
    f.text(300, y_top + 50, "Kịch bản 1: Ngưỡng IoU = 0.5", size=8.8, weight=700, fill=RED)
    f.text(300, y_top + 70, "1. Chọn A (0.9 làm cơ sở giữ lại):", size=8.0, weight=600, fill=DARK)
    f.text(310, y_top + 85, "• IoU(A, B) = 0.68 > 0.5 -> LOẠI B!", size=7.8, weight=700, fill=RED)
    f.text(310, y_top + 100, "• IoU(A, D) = 0.47 < 0.5 -> GIỮ D.", size=7.8, fill=DARK)
    f.text(300, y_top + 120, "2. Chọn C (0.7): IoU(C, D) = 0 -> Giữ C.", size=8.0, fill=DARK)
    f.text(300, y_top + 138, "3. Chọn D (0.6): Không trùng ai -> Giữ D.", size=8.0, fill=DARK)
    rect(f, 300, y_top + 155, 240, 26, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(420, y_top + 172, "KẾT QUẢ: GIỮ A, C, D (LOẠI B)", size=8.2, weight=700, fill=GREEN, anchor="middle")

    # Ngưỡng 0.7
    rect(f, 565, y_top + 34, 265, 160, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=4)
    f.text(575, y_top + 50, "Kịch bản 2: Ngưỡng IoU = 0.7", size=8.8, weight=700, fill=GREEN)
    f.text(575, y_top + 70, "1. Chọn A (0.9 làm cơ sở):", size=8.0, weight=600, fill=DARK)
    f.text(585, y_top + 85, "• IoU(A, B) = 0.68 ≤ 0.7 -> KHÔNG LOẠI B!", size=7.8, weight=700, fill=GREEN)
    f.text(585, y_top + 100, "• IoU(A, D) = 0.47 ≤ 0.7 -> Giữ D.", size=7.8, fill=DARK)
    f.text(575, y_top + 120, "2. Các bước sau: Không hộp nào vượt 0.7.", size=8.0, fill=DARK)
    f.text(575, y_top + 138, "-> Ngưỡng cao giữ lại nhiều hộp trùng hơn.", size=7.8, fill=GRAY)
    rect(f, 575, y_top + 155, 245, 26, fill="#FEF3C7", stroke=ORANGE, sw=1, rx=3)
    f.text(697, y_top + 172, "KẾT QUẢ: GIỮ CẢ A, B, C, D (0 LOẠI)", size=8.2, weight=700, fill=ORANGE, anchor="middle")

    # PHẦN 2: THỦ THUẬT BATCHED NMS TRÊN RK3588 (y=255..420)
    bot_y = 255
    bot_h = 165
    rect(f, 15, bot_y, 830, bot_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, bot_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, bot_y + 16, "PHẦN 2: THỦ THUẬT BATCHED NMS TRÊN RK3588 (ai/board/common.py: boxes + cls * MAX_WH)", size=9.2, weight=700, fill=DARK)

    rect(f, 25, bot_y + 32, 780, 52, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=4)

    # Vùng lớp 0
    rect(f, 35, bot_y + 40, 160, 36, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=3)
    f.text(115, bot_y + 54, "Lớp 0: Person", size=8.0, weight=700, fill=BLUE, anchor="middle")
    f.text(115, bot_y + 68, "Tọa độ: [0 .. 640]", size=7.2, fill=DARK, anchor="middle")

    f.text(235, bot_y + 58, "+ (1 × 7680)", size=8.5, weight=700, fill=GRAY, anchor="middle")

    # Vùng lớp 1
    rect(f, 280, bot_y + 40, 160, 36, fill="#FEF3C7", stroke=ORANGE, sw=1.2, rx=3)
    f.text(360, bot_y + 54, "Lớp 1: Car", size=8.0, weight=700, fill=ORANGE, anchor="middle")
    f.text(360, bot_y + 68, "Tọa độ: [7680 .. 8320]", size=7.2, fill=DARK, anchor="middle")

    f.text(480, bot_y + 58, "+ (2 × 7680)", size=8.5, weight=700, fill=GRAY, anchor="middle")

    # Vùng lớp 2
    rect(f, 525, bot_y + 40, 160, 36, fill="#DCFCE7", stroke=GREEN, sw=1.2, rx=3)
    f.text(605, bot_y + 54, "Lớp 2: Motorcycle", size=8.0, weight=700, fill=GREEN, anchor="middle")
    f.text(605, bot_y + 68, "Tọa độ: [15360 .. 16000]", size=7.2, fill=DARK, anchor="middle")

    f.text(750, bot_y + 58, "IoU ≡ 0 !", size=10, weight=700, fill=RED, anchor="middle")

    f.text(25, bot_y + 98, "LỢI ÍCH CỦA BATCHED NMS TRÊN PHẦN CỨNG BOARD:", size=8.8, weight=700, fill=DARK)
    f.text(35, bot_y + 115, "1. Chạy 1 lần duy nhất: Không cần vòng lặp for tách từng lớp bằng Python, gọi thẳng 1 hàm nms_xyxy bằng C/NumPy.", size=8.0, fill=DARK)
    f.text(35, bot_y + 130, "2. Triệt tiêu triệt để việc triệt tiêu nhầm: Nhờ khoảng cách 7680px (MAX_WH), hộp người và hộp xe dù đè nhau trên ảnh vẫn có IoU = 0.", size=8.0, fill=DARK)
    f.text(35, bot_y + 145, "3. Tương thích RKNN: Do Ultralytics tắt nhánh end2end khi export RKNN, Batched NMS ngoài đồ thị là giải pháp chuẩn và nhanh nhất.", size=8.0, fill=DARK)

    source(f, 430, "Nguồn: T2 D2L tr.619-620; T3 ai/board/common.py:22-25, 115; T1 ultralytics engine/exporter.py:682-688.")
    return f


# ==============================================================================
# DANH MỤC CÁC HÌNH
# ==============================================================================
FIGS = [
    ("det-1-bon-tac-vu-thi-giac", fig_four_vision_tasks),
    ("det-2-bounding-box-va-he-toa-do", fig_bounding_box_formats),
    ("det-2b-dinh-dang-nhan-va-phan-loai-mau", fig_label_class_and_samples),
    ("det-3-anchor-based-vs-anchor-free", fig_anchor_based_vs_free),
    ("det-4-thuat-toan-nms-va-batched-nms", fig_nms_and_batched_nms),
]

if __name__ == "__main__":
    run(FIGS, DEFAULT_OUTDIR)
