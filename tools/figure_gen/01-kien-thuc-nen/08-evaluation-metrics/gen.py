#!/usr/bin/env python3
"""Ghi chú chuyên đề: Các chỉ số đánh giá mô hình phát hiện vật thể (06-chi-so-danh-gia).

Sinh 3 hình chất lượng cao chuẩn visual_guide:
  - hm-1-iou-va-phan-loai-du-doan (T2 chung): Bản chất hình học IoU và phân loại kết quả (TP, FP, FN)
  - hm-2-co-che-duong-cong-pr-va-ap (T2 chung): Trượt Confidence Threshold, Đồ thị P-R Curve và Cách tính AP, mAP
  - hm-3-map50-95-va-phan-tich-5-lop-ppe (T2 chung): Bản chất 10 mốc IoU mAP50-95, Biểu đồ 5 lớp PPE và Độ nhạy IoU của vật thể nhỏ

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import base64
import io
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
# figlib nằm ở docs/tools/figure_gen/figlib.py
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "08-evaluation-metrics"))

W = 900
CALC = "#EAF2FF"      # Nền khối tính toán / số học
ORANGE = "#E65100"
GRAY_BG = "#F5F5F5"


def tier(f, label):
    f.tier(W - 130, 10, label)


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


# ==============================================================================
# HÌNH 1: BẢN CHẤT HÌNH HỌC CỦA IOU
# ==============================================================================
def draw_bbox_case(f, x, y, w, h, p_off_x, p_off_y, title, iou_val, status_text, status_color):
    """Vẽ 1 cặp bounding box minh họa mức IoU sạch đẹp, không đè chữ."""
    rect(f, x, y, w, h, fill="#FCFDFD", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(x + w / 2, y + 16, title, size=11, weight=700, fill=DARK, anchor="middle")

    # Toạ độ Ground Truth Box (Cam)
    gt_w, gt_h = 95, 75
    gt_x = x + 40
    gt_y = y + 36

    # Toạ độ Prediction Box (Xanh)
    p_x = gt_x + p_off_x
    p_y = gt_y + p_off_y

    # Vùng giao thoa (Intersection)
    ix1 = max(gt_x, p_x)
    iy1 = max(gt_y, p_y)
    ix2 = min(gt_x + gt_w, p_x + gt_w)
    iy2 = min(gt_y + gt_h, p_y + gt_h)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)

    # 1. Vẽ nền vùng giao nhau
    if iw > 0 and ih > 0:
        f.a(f'<rect x="{ix1}" y="{iy1}" width="{iw}" height="{ih}" fill="#C8E6C9" opacity="0.85"/>')

    # 2. Vẽ viền Ground Truth
    f.a(f'<rect x="{gt_x}" y="{gt_y}" width="{gt_w}" height="{gt_h}" fill="none" stroke="{ORANGE}" stroke-width="2.2" stroke-dasharray="6 3"/>')

    # 3. Vẽ viền Prediction
    f.a(f'<rect x="{p_x}" y="{p_y}" width="{gt_w}" height="{gt_h}" fill="none" stroke="{BLUE}" stroke-width="2.2"/>')

    # 4. Hiển thị thông số và đánh giá bên dưới hộp
    f.text(x + w / 2, y + h - 28, f"IoU = {iou_val:.2f}", size=13, weight=700, fill=DARK, anchor="middle")
    f.text(x + w / 2, y + h - 12, status_text, size=11, weight=600, fill=status_color, anchor="middle")


def fig_iou_geometry():
    """Hình minh họa bản chất hình học của IoU, không chứa bảng trùng lặp."""
    f = Fig(W, 335)
    tier(f, "T2 chung")
    f.text(10, 22, "Bản chất Hình học của IoU (Intersection over Union)", size=14.5, weight=700, fill=DARK)

    f.a(f'<line x1="20" y1="52" x2="45" y2="52" stroke="{ORANGE}" stroke-width="2.0" stroke-dasharray="6 3"/>')
    f.text(50, 52, "Nhãn thực tế (Ground Truth B_gt)", size=10, weight=600, fill=DARK)

    f.a(f'<line x1="280" y1="52" x2="305" y2="52" stroke="{BLUE}" stroke-width="2.0"/>')
    f.text(310, 52, "Dự đoán mô hình (Prediction B_p)", size=10, weight=600, fill=DARK)

    rect(f, 540, 45, 16, 14, fill="#C8E6C9", stroke="none")
    f.text(562, 52, "Phần giao nhau (Intersection ∩)", size=10, weight=600, fill=DARK)

    draw_bbox_case(f, 10, 68, 275, 175, p_off_x=6, p_off_y=6,
                   title="1. Trùng khít cao (Rất tốt)", iou_val=0.88,
                   status_text="Đạt chuẩn mọi mốc IoU", status_color=GREEN)

    draw_bbox_case(f, 310, 68, 275, 175, p_off_x=28, p_off_y=24,
                   title="2. Trùng khớp vừa (Ngưỡng cơ bản)", iou_val=0.52,
                   status_text="Đạt mAP50, trượt mAP75 trở lên", status_color=ORANGE)

    draw_bbox_case(f, 610, 68, 275, 175, p_off_x=55, p_off_y=24,
                   title="3. Lệch vị trí (Trượt ngưỡng)", iou_val=0.16,
                   status_text="Phán đoán sai vị trí (FP)", status_color=RED)

    # Khung công thức IoU
    y_f = 254
    rect(f, 10, y_f, W - 20, 32, fill=CALC, stroke="#90CAF9", sw=1.0, rx=4)
    txt(f, 20, y_f + 10, [
        [("Công thức tính IoU: ", "b"),
         ("IoU = Diện tích vùng giao (B_p ∩ B_gt) / Diện tích vùng hợp (B_p ∪ B_gt)", "b"),
         ("  |  Miền giá trị: [0.0 (không chạm) đến 1.0 (trùng khít hoàn toàn)]", "t")],
    ], size=10, dy=14)

    source(f, y_f + 38, "Nguồn: REPO ai/automation/leaderboards/sfchd_5class.csv; Y6 tr.8.")
    return f


# ==============================================================================
# HÌNH 2: CHỈ SỐ PRECISION (ĐỘ CHUẨN XÁC)
# ==============================================================================
def fig_precision():
    f = Fig(W, 350)
    tier(f, "T2 chung")
    f.text(10, 22, "Chỉ số Precision (Độ chuẩn xác) trong Phát hiện Vật thể", size=14.5, weight=700, fill=DARK)

    # Panel Trái: Tình huống mô hình dự đoán trên ảnh
    p1_x, p1_y, p1_w, p1_h = 10, 48, 435, 260
    rect(f, p1_x, p1_y, p1_w, p1_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p1_y + 16, "1. Mô phỏng dự đoán của mô hình (Tổng 5 hộp)", size=11.5, weight=700, fill=DARK)

    # Khung canvas ảnh
    c_x, c_y, c_w, c_h = p1_x + 10, p1_y + 30, p1_w - 20, 175
    rect(f, c_x, c_y, c_w, c_h, fill="#ECEFF1", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(c_x + c_w - 8, c_y + 12, "Camera giám sát công trường", size=9.0, fill=GRAY, anchor="end", italic=True)

    # Bounding boxes TP Hàng 1 (Đoán đúng mũ bảo hộ)
    # Box 1: Worker 1 Helmet
    rect(f, c_x + 16, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 16, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 19, c_y + 32, "TP: helmet 0.94", size=8.0, weight=700, fill="white")

    # Box 2: Worker 2 Helmet
    rect(f, c_x + 120, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 120, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 123, c_y + 32, "TP: helmet 0.91", size=8.0, weight=700, fill="white")

    # Box 3: Worker 3 Helmet
    rect(f, c_x + 224, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 224, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 227, c_y + 32, "TP: helmet 0.88", size=8.0, weight=700, fill="white")

    # Bounding boxes Hàng 2 (Khoảng cách an toàn, không đè lấn)
    # Box 4: Worker 1 Vest (TP)
    rect(f, c_x + 55, c_y + 112, 105, 50, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 55, c_y + 100, 105, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 58, c_y + 106, "TP: safety_vest 0.92", size=8.0, weight=700, fill="white")

    # Box 5: FP (False Positive - Báo nhầm thùng sơn màu cam thành helmet)
    rect(f, c_x + 205, c_y + 112, 105, 50, fill="#FFCDD2", stroke=RED, sw=1.8, rx=2, dashed=True)
    rect(f, c_x + 205, c_y + 100, 105, 12, fill=RED, stroke="none", rx=2)
    f.text(c_x + 208, c_y + 106, "FP: helmet 0.65", size=8.0, weight=700, fill="white")
    f.text(c_x + 257, c_y + 137, "(Thùng sơn màu cam)", size=8.5, weight=700, fill=RED, anchor="middle")

    # Tóm tắt số hộp ở đáy panel trái
    rect(f, p1_x + 10, p1_y + p1_h - 40, p1_w - 20, 28, fill="white", stroke="#B0BEC5", sw=1.0, rx=3)
    f.rich(p1_x + p1_w / 2, p1_y + p1_h - 26, [
        ("Tổng số phát hiện: ", "t"), ("5 hộp", "b"), (" = ", "t"),
        ("4 Đúng (TP)", "b"), (" + ", "t"), ("1 Báo nhầm (FP)", "b"),
    ], size=9.5, anchor="middle")

    # Panel Phải: Công thức & Ý nghĩa
    p2_x, p2_y, p2_w, p2_h = 455, 48, 435, 260
    rect(f, p2_x, p2_y, p2_w, p2_h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p2_y + 16, "2. Công thức và Ý nghĩa bản chất", size=11.5, weight=700, fill=DARK)

    # Khung công thức toán học
    f_h = 56
    rect(f, p2_x + 10, p2_y + 30, p2_w - 20, f_h, fill=CALC, stroke="#90CAF9", sw=1.0, rx=4)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, p2_y + 46, [
        ("Precision = ", "b"),
        ("TP / (TP + FP)", "b"),
        (" = ", "t"),
        ("4 / (4 + 1)", "b"),
        (" = ", "t"),
        ("4 / 5 = 80%", "b"),
    ], size=11.5, anchor="middle", fill=BLUE)
    f.text(p2_x + (p2_w - 20) / 2 + 10, p2_y + 68, "Mẫu số là toàn bộ những gì mô hình đã phán đoán", size=9.5, italic=True, fill=DARK, anchor="middle")

    # Diễn giải ý nghĩa
    txt(f, p2_x + 14, p2_y + 112, [
        [("• Bản chất: ", "b"), ("Trong các hộp tìm ra, bao nhiêu % là đúng?", "t")],
        [("• Ý nghĩa thực tế: ", "b"), ("Precision cao -> Rất ít báo động giả.", "t")],
        [("  Hệ thống giám sát không gây phiền toái vì báo sai vi phạm.", "t")],
        [("• Không xét đến FN: ", "b"), ("Chỉ đo độ tin cậy của box đã đoán,", "t")],
        [("  hoàn toàn không quan tâm có bao nhiêu vật thể bị bỏ sót.", "t")],
        [("• Đánh đổi: ", "b"), ("Hạ ngưỡng confidence -> Ra nhiều box -> Dễ tăng FP.", "t")],
    ], size=10.5, dy=25)

    source(f, 318, "Nguồn: Ultralytics utils/metrics.py; SHEL5K tr.8 (Equation 1).")
    return f


# ==============================================================================
# HÌNH 2B: CHỈ SỐ RECALL (ĐỘ NHẠY / ĐỘ BAO PHỦ)
# ==============================================================================
def fig_recall():
    f = Fig(W, 350)
    tier(f, "T2 chung")
    f.text(10, 22, "Chỉ số Recall (Độ nhạy / Độ bao phủ) trong Phát hiện Vật thể", size=14.5, weight=700, fill=DARK)

    # Panel Trái: Tình huống phát hiện trên ảnh
    p1_x, p1_y, p1_w, p1_h = 10, 48, 435, 260
    rect(f, p1_x, p1_y, p1_w, p1_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p1_y + 16, "1. Mô phỏng phát hiện trên ảnh (Tổng 5 vật thể thật)", size=11.5, weight=700, fill=DARK)

    # Khung canvas ảnh
    c_x, c_y, c_w, c_h = p1_x + 10, p1_y + 30, p1_w - 20, 175
    rect(f, c_x, c_y, c_w, c_h, fill="#ECEFF1", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(c_x + c_w - 8, c_y + 12, "Camera giám sát công trường", size=9.0, fill=GRAY, anchor="end", italic=True)

    # Hàng 1: 3 vật thể thật được phát hiện đúng (TP)
    # Box 1: Worker 1 Helmet
    rect(f, c_x + 16, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 16, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 19, c_y + 32, "TP: helmet 0.94", size=8.0, weight=700, fill="white")

    # Box 2: Worker 2 Helmet
    rect(f, c_x + 120, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 120, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 123, c_y + 32, "TP: helmet 0.91", size=8.0, weight=700, fill="white")

    # Box 3: Worker 3 Helmet
    rect(f, c_x + 224, c_y + 38, 80, 48, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 224, c_y + 26, 80, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 227, c_y + 32, "TP: helmet 0.88", size=8.0, weight=700, fill="white")

    # Hàng 2: 1 vật thể bắt trúng (TP) và 1 vật thể bị bỏ sót (FN)
    # Box 4: Worker 1 Vest (TP)
    rect(f, c_x + 55, c_y + 112, 105, 50, fill="#C8E6C9", stroke=GREEN, sw=1.8, rx=2)
    rect(f, c_x + 55, c_y + 100, 105, 12, fill=GREEN, stroke="none", rx=2)
    f.text(c_x + 58, c_y + 106, "TP: safety_vest 0.92", size=8.0, weight=700, fill="white")

    # Box 5: FN (False Negative - Công nhân có đội mũ nhưng mô hình bỏ sót)
    rect(f, c_x + 205, c_y + 112, 105, 50, fill="#FFF3E0", stroke=ORANGE, sw=1.8, rx=2, dashed=True)
    rect(f, c_x + 205, c_y + 100, 105, 12, fill=ORANGE, stroke="none", rx=2)
    f.text(c_x + 208, c_y + 106, "FN: helmet (Bỏ sót)", size=8.0, weight=700, fill="white")
    f.text(c_x + 257, c_y + 137, "(Mô hình không phát hiện)", size=8.0, weight=700, fill=ORANGE, anchor="middle")

    # Tóm tắt số vật thể ở đáy panel trái
    rect(f, p1_x + 10, p1_y + p1_h - 40, p1_w - 20, 28, fill="white", stroke="#B0BEC5", sw=1.0, rx=3)
    f.rich(p1_x + p1_w / 2, p1_y + p1_h - 26, [
        ("Tổng số vật thể thật: ", "t"), ("5 đối tượng", "b"), (" = ", "t"),
        ("4 Bắt trúng (TP)", "b"), (" + ", "t"), ("1 Bỏ sót (FN)", "b"),
    ], size=9.5, anchor="middle")

    # Panel Phải: Công thức & Ý nghĩa
    p2_x, p2_y, p2_w, p2_h = 455, 48, 435, 260
    rect(f, p2_x, p2_y, p2_w, p2_h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p2_y + 16, "2. Công thức và Ý nghĩa bản chất", size=11.5, weight=700, fill=DARK)

    # Khung công thức toán học
    f_h = 56
    rect(f, p2_x + 10, p2_y + 30, p2_w - 20, f_h, fill="#FFF8E1", stroke="#FFE082", sw=1.0, rx=4)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, p2_y + 46, [
        ("Recall = ", "b"),
        ("TP / (TP + FN)", "b"),
        (" = ", "t"),
        ("4 / (4 + 1)", "b"),
        (" = ", "t"),
        ("4 / 5 = 80%", "b"),
    ], size=11.5, anchor="middle", fill=ORANGE)
    f.text(p2_x + (p2_w - 20) / 2 + 10, p2_y + 68, "Mẫu số là toàn bộ số vật thể thực tế có trong ảnh", size=9.5, italic=True, fill=DARK, anchor="middle")

    # Diễn giải ý nghĩa
    txt(f, p2_x + 14, p2_y + 112, [
        [("• Bản chất: ", "b"), ("Trong tổng số vật thể thật, bắt được bao nhiêu %?", "t")],
        [("• Ý nghĩa an toàn: ", "b"), ("Recall cao -> Cực kỳ ít bỏ sót vi phạm.", "t")],
        [("  Đảm bảo không bỏ lọt công nhân không đội mũ hoặc thiếu bảo hộ.", "t")],
        [("• Không xét đến FP: ", "b"), ("Chỉ đo mức độ bao phủ vật thể thật,", "t")],
        [("  hoàn toàn không bị giảm điểm khi có báo động giả (FP).", "t")],
        [("• Đánh đổi: ", "b"), ("Tăng ngưỡng confidence -> Lọc bớt box -> Dễ tăng FN -> Recall giảm.", "t")],
    ], size=10.5, dy=25)

    source(f, 318, "Nguồn: Ultralytics utils/metrics.py; SHEL5K tr.8 (Equation 2).")
    return f


# ==============================================================================
# HÌNH 2C: CHỈ SỐ F1-SCORE (TRUNG BÌNH ĐIỀU HÒA)
# ==============================================================================
def fig_f1_score():
    f = Fig(W, 248)
    tier(f, "T2 chung")
    f.text(10, 20, "Chỉ số F1-Score (Trung bình điều hòa giữa Precision và Recall)", size=14.0, weight=700, fill=DARK)

    # Panel Trái: Cơ chế phạt lệch cực đoan
    p1_x, p1_y, p1_w, p1_h = 10, 38, 435, 190
    rect(f, p1_x, p1_y, p1_w, p1_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p1_y + 15, "1. Cơ chế tự phạt: Trung bình cộng vs Trung bình điều hòa (F1)", size=11.0, weight=700, fill=DARK)

    # Bảng 3 tình huống so sánh
    y_s = p1_y + 25
    case_h = 40
    gap = 5

    # Trường hợp 1: Quá khắt khe
    rect(f, p1_x + 10, y_s, p1_w - 20, case_h, fill="#FFF5F5", stroke="#FFCDD2", sw=1.0, rx=3)
    f.text(p1_x + 16, y_s + 12, "Trường hợp 1: Quá khắt khe (Confidence quá cao)", size=9.0, weight=700, fill=RED)
    f.rich(p1_x + 16, y_s + 27, [
        ("Precision = ", "t"), ("0.95", "b"), ("  |  ", "t"),
        ("Recall = ", "t"), ("0.10", "b"), (" (bỏ sót 90%)", "t"),
        ("  ->  ", "t"),
        ("Cộng: 52.5%  |  ", "t"), ("F1: 18.1% (Phạt nặng)", "b"),
    ], size=8.5, fill=DARK)

    # Trường hợp 2: Quá khoan dung
    y_s2 = y_s + case_h + gap
    rect(f, p1_x + 10, y_s2, p1_w - 20, case_h, fill="#FFF5F5", stroke="#FFCDD2", sw=1.0, rx=3)
    f.text(p1_x + 16, y_s2 + 12, "Trường hợp 2: Quá khoan dung (Confidence quá thấp)", size=9.0, weight=700, fill=RED)
    f.rich(p1_x + 16, y_s2 + 27, [
        ("Precision = ", "t"), ("0.15", "b"), (" (báo nhầm nhiều)  |  ", "t"),
        ("Recall = ", "t"), ("0.95", "b"),
        ("  ->  ", "t"),
        ("Cộng: 55.0%  |  ", "t"), ("F1: 25.9% (Phạt nặng)", "b"),
    ], size=8.5, fill=DARK)

    # Trường hợp 3: Cân bằng lý tưởng
    y_s3 = y_s2 + case_h + gap
    rect(f, p1_x + 10, y_s3, p1_w - 20, case_h, fill="#F1F8E9", stroke="#C8E6C9", sw=1.0, rx=3)
    f.text(p1_x + 16, y_s3 + 12, "Trường hợp 3: Cân bằng tối ưu (Đạt chuẩn triển khai)", size=9.0, weight=700, fill=GREEN)
    f.rich(p1_x + 16, y_s3 + 27, [
        ("Precision = ", "t"), ("0.85", "b"), ("  |  ", "t"),
        ("Recall = ", "t"), ("0.85", "b"),
        ("  ->  ", "t"),
        ("Cộng: 85.0%  |  ", "t"), ("F1-Score: 85.0% (Cân bằng tốt)", "b"),
    ], size=8.5, fill=GREEN)

    # Thanh kết luận đáy panel trái
    y_bot = y_s3 + case_h + gap
    rect(f, p1_x + 10, y_bot, p1_w - 20, 20, fill="white", stroke="#B0BEC5", sw=1.0, rx=3)
    f.text(p1_x + p1_w / 2, y_bot + 10, "F1-Score chỉ cao khi CẢ HAI chỉ số Precision và Recall cùng đạt mức tốt", size=8.5, weight=700, fill=DARK, anchor="middle")

    # Panel Phải: Công thức & Ứng dụng
    p2_x, p2_y, p2_w, p2_h = 455, 38, 435, 190
    rect(f, p2_x, p2_y, p2_w, p2_h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p2_y + 15, "2. Công thức toán học và Ứng dụng thực tế", size=11.0, weight=700, fill=DARK)

    # Khung công thức toán học
    f_h = 46
    rect(f, p2_x + 10, p2_y + 25, p2_w - 20, f_h, fill=CALC, stroke="#90CAF9", sw=1.0, rx=4)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, p2_y + 39, [
        ("F1-Score = ", "b"),
        ("2 × (Precision × Recall) / (Precision + Recall)", "b"),
    ], size=11.0, anchor="middle", fill=BLUE)
    f.text(p2_x + (p2_w - 20) / 2 + 10, p2_y + 57, "Trung bình điều hòa luôn bị kéo mạnh về phía giá trị thấp hơn", size=8.8, italic=True, fill=DARK, anchor="middle")

    # Diễn giải ý nghĩa
    txt(f, p2_x + 14, p2_y + 85, [
        [("• Bản chất: ", "b"), ("Thước đo đánh giá sự cân bằng giữa bắt đúng và ít báo nhầm.", "t")],
        [("• Cơ chế tự phạt: ", "b"), ("Nếu một trong hai chỉ số sụt giảm nghiêm trọng,", "t")],
        [("  F1 sẽ lập tức giảm mạnh, không che giấu khiếm khuyết như trung bình cộng.", "t")],
        [("• Ứng dụng chọn ngưỡng (max-F1): ", "b"), ("Ngưỡng confidence tại đó F1 đạt", "t")],
        [("  cực đại thường được chọn làm ngưỡng kích hoạt cảnh báo camera tự động.", "t")],
        [("• Khác biệt với mAP: ", "b"), ("F1 đánh giá tại một ngưỡng cố định, còn mAP", "t")],
        [("  quét và tính diện tích tích phân trên toàn bộ đường cong P-R.", "t")],
    ], size=9.0, dy=14.5)

    source(f, 238, "Nguồn: Ultralytics utils/metrics.py (max-F1); SHEL5K tr.8 (Equation 3).")
    return f


# ==============================================================================
## ==============================================================================
# HÌNH 2D: AVERAGE PRECISION (AP) VÀ ĐƯỜNG CONG NỘI SUY CHUẨN COCO
# ==============================================================================
def fig_pr_curve_and_ap():
    f = Fig(W, 322)
    tier(f, "T2 chung")
    f.text(10, 20, "Average Precision (AP): Bản chất Đường cong P-R và Phương pháp Nội suy (COCO Benchmark)", size=13.5, weight=700, fill=DARK)

    # Panel Trái: Đồ thị đường cong P-R và Diện tích AP nội suy
    p1_x, p1_y, p1_w, p1_h = 10, 38, 485, 242
    rect(f, p1_x, p1_y, p1_w, p1_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p1_y + 14, "1. Đồ thị P-R: Đường răng cưa thô vs Đường nội suy cực đại", size=10.0, weight=700, fill=DARK)

    # Hộp chú thích (Legend) nằm ngang phía trên đồ thị
    leg_y = p1_y + 24
    rect(f, p1_x + 10, leg_y, p1_w - 20, 20, fill="white", stroke="#CFD8DC", sw=0.8, rx=3)
    # Mục 1: Nội suy
    f.a(f'<line x1="{p1_x+20}" y1="{leg_y+10}" x2="{p1_x+36}" y2="{leg_y+10}" stroke="{BLUE}" stroke-width="2.4"/>')
    f.text(p1_x + 40, leg_y + 10, "Đường nội suy p_interp", size=7.8, weight=700, fill=BLUE)
    # Mục 2: Răng cưa thô
    f.a(f'<line x1="{p1_x+160}" y1="{leg_y+10}" x2="{p1_x+176}" y2="{leg_y+10}" stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="3 2"/>')
    f.text(p1_x + 180, leg_y + 10, "P-R thô (răng cưa do FP)", size=7.8, fill=ORANGE)
    # Mục 3: Diện tích AP
    rect(f, p1_x + 312, leg_y + 5, 16, 10, fill="#C8E6C9", stroke="none", rx=1)
    f.text(p1_x + 332, leg_y + 10, "Diện tích AP = 0.812 (AUC)", size=7.8, weight=700, fill=GREEN)

    # Tọa độ vùng đồ thị (gy = 102 để tách biệt hoàn toàn với nhãn Precision ở y=90 và legend ở y=62..82)
    gx, gy, gw, gh = 56, 102, 416, 132

    # Nhãn trục tung Precision (p) đặt ở trên đỉnh trục y, căn giữa trục
    f.text(gx, gy - 11, "Precision (p)", size=8.8, weight=700, fill=DARK, anchor="middle")

    # Lưới tọa độ và số mốc
    for i in range(1, 6):
        lx = gx + i * (gw / 5)
        ly = gy + gh - i * (gh / 5)
        f.a(f'<line x1="{lx}" y1="{gy}" x2="{lx}" y2="{gy+gh}" stroke="#EBEBEB" stroke-width="1.0" stroke-dasharray="3 3"/>')
        f.a(f'<line x1="{gx}" y1="{ly}" x2="{gx+gw}" y2="{ly}" stroke="#EBEBEB" stroke-width="1.0" stroke-dasharray="3 3"/>')
        # Số mốc trên trục hoành
        f.text(lx, gy + gh + 12, f"{i*0.2:.1f}", size=8.0, fill="#777777", anchor="middle")
        # Số mốc trên trục tung
        f.text(gx - 6, ly, f"{i*0.2:.1f}", size=8.0, fill="#777777", anchor="end")

    f.text(gx - 6, gy + gh, "0", size=8.0, fill="#777777", anchor="end")

    # Nhãn trục hoành Recall (r) đặt chính giữa trục hoành, dưới các số mốc 14px
    f.text(gx + gw / 2, gy + gh + 26, "Recall (r)", size=8.8, weight=700, fill=DARK, anchor="middle")

    # Trục tọa độ chính
    f.a(f'<line x1="{gx}" y1="{gy+gh}" x2="{gx+gw+8}" y2="{gy+gh}" stroke="{DARK}" stroke-width="1.4"/>')
    f.a(f'<line x1="{gx}" y1="{gy-4}" x2="{gx}" y2="{gy+gh}" stroke="{DARK}" stroke-width="1.4"/>')

    # Dữ liệu đường nội suy bậc thang (Staircase Curve)
    interp_steps = [
        (0.00, 1.00),
        (0.20, 1.00), (0.20, 0.93),
        (0.38, 0.93), (0.38, 0.89),
        (0.56, 0.89), (0.56, 0.83),
        (0.72, 0.83), (0.72, 0.71),
        (0.84, 0.71), (0.84, 0.48),
        (0.92, 0.48), (0.92, 0.00),
    ]
    svg_interp = [(gx + r * gw, gy + gh - p * gh) for r, p in interp_steps]

    # Tô màu diện tích AP dưới đường bậc thang nội suy
    poly_pts = f"{gx},{gy+gh} " + " ".join(f"{x:.1f},{y:.1f}" for x, y in svg_interp) + f" {gx+0.92*gw:.1f},{gy+gh}"
    f.a(f'<polygon points="{poly_pts}" fill="#C8E6C9" opacity="0.6"/>')

    # Dữ liệu đường P-R thô (Raw Sawtooth Curve)
    raw_steps = [
        (0.00, 1.00),
        (0.20, 1.00), (0.20, 0.88),  # FP dip
        (0.38, 0.93), (0.38, 0.84),  # FP dip
        (0.56, 0.89), (0.56, 0.78),  # FP dip
        (0.72, 0.83), (0.72, 0.68),  # FP dip
        (0.84, 0.71), (0.84, 0.46),  # FP dip
        (0.92, 0.48), (0.92, 0.15),  # Đuôi FP confidence thấp
    ]
    svg_raw = [(gx + r * gw, gy + gh - p * gh) for r, p in raw_steps]

    # Vẽ đường P-R thô (nét đứt cam)
    raw_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in svg_raw)
    f.a(f'<path d="{raw_d}" fill="none" stroke="{ORANGE}" stroke-width="1.5" stroke-dasharray="4 3"/>')

    # Vẽ đường nội suy bậc thang (nét liền xanh đậm)
    interp_d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in svg_interp)
    f.a(f'<path d="{interp_d}" fill="none" stroke="{BLUE}" stroke-width="2.2"/>')

    # Các điểm mốc nội suy
    for r, p in [(0.20, 0.93), (0.38, 0.89), (0.56, 0.83), (0.72, 0.71), (0.84, 0.48)]:
        px = gx + r * gw
        py = gy + gh - p * gh
        f.a(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.0" fill="{BLUE}" stroke="white" stroke-width="1.0"/>')

    # Huy hiệu AP đặt ở vùng an toàn không đè đường cong (góc dưới trái của đồ thị)
    badge_x, badge_y = gx + 20, gy + gh - 38
    rect(f, badge_x, badge_y, 135, 22, fill="white", stroke=GREEN, sw=1.2, rx=3)
    f.text(badge_x + 67.5, badge_y + 11, "Diện tích AP = 0.812", size=8.5, weight=700, fill=GREEN, anchor="middle")

    # Panel Phải: Quy trình xếp hạng và công thức nội suy (Tinh gọn)
    p2_x, p2_y, p2_w, p2_h = 505, 38, 385, 242
    rect(f, p2_x, p2_y, p2_w, p2_h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p2_y + 14, "2. Bản chất Toán học và Công thức COCO", size=10.0, weight=700, fill=DARK)

    # Khối A: Cơ chế sinh răng cưa
    b1_y = p2_y + 24
    rect(f, p2_x + 10, b1_y, p2_w - 20, 56, fill="#FFF8E1", stroke="#FFE082", sw=1.0, rx=3)
    f.text(p2_x + 16, b1_y + 11, "A. Cơ chế sinh răng cưa (Sawtooth Curve):", size=8.8, weight=700, fill=ORANGE)
    f.text(p2_x + 16, b1_y + 29, "• Sắp xếp tất cả box dự đoán theo Confidence giảm dần.", size=8.2, fill=DARK)
    f.rich(p2_x + 16, b1_y + 44, [
        ("• ", "t"), ("Gặp TP", "b"), (" -> Recall tăng  |  ", "t"),
        ("Gặp FP", "b"), (" -> Precision tụt dốc.", "t"),
    ], size=8.2, fill=DARK)

    # Khối B: Công thức nội suy cực đại
    b2_y = b1_y + 66
    rect(f, p2_x + 10, b2_y, p2_w - 20, 64, fill="#E3F2FD", stroke="#90CAF9", sw=1.0, rx=3)
    f.text(p2_x + 16, b2_y + 11, "B. Nội suy cực đại (Interpolated Precision):", size=8.8, weight=700, fill=BLUE)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, b2_y + 31, [
        ("p_interp(r) = ", "b"),
        ("max { p(r̃)  với  r̃ ≥ r }", "b"),
    ], size=9.8, anchor="middle", fill=BLUE)
    f.text(p2_x + (p2_w - 20) / 2 + 10, b2_y + 52, "Lấy giá trị Precision lớn nhất ở bên phải, làm phẳng răng cưa", size=8.0, italic=True, fill=DARK, anchor="middle")

    # Khối C: Tính diện tích AP chuẩn COCO 101 mốc
    b3_y = b2_y + 74
    rect(f, p2_x + 10, b3_y, p2_w - 20, 64, fill="#F1F8E9", stroke="#C8E6C9", sw=1.0, rx=3)
    f.text(p2_x + 16, b3_y + 11, "C. Chuẩn COCO: Tính AP trên 101 mốc Recall:", size=8.8, weight=700, fill=GREEN)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, b3_y + 31, [
        ("AP = (1 / 101) × Σ p_interp(r)", "b"),
        ("   (r ∈ {0.00, ..., 1.00})", "t"),
    ], size=9.2, anchor="middle", fill=GREEN)
    f.text(p2_x + (p2_w - 20) / 2 + 10, b3_y + 52, "Trung bình cộng tại 101 mốc đều nhau xuyên suốt dải [0, 1]", size=8.0, italic=True, fill=DARK, anchor="middle")

    source(f, 290, "Nguồn: PASCAL VOC 2012; COCO Evaluation Protocol; Everingham et al. IJCV 2010.")
    return f


# ==============================================================================
# HÌNH 3: BẢN CHẤT MAP50-95 VÀ PHÂN TÍCH 5 LỚP PPE
# ==============================================================================
# HÌNH 3A: CƠ CHẾ TÍNH TRUNG BÌNH MAP QUA CÁC LỚP ĐỐI TƯỢNG
# ==============================================================================
def fig_map_classes():
    f = Fig(W, 252)
    tier(f, "T2 chung")
    f.text(10, 20, "Mean Average Precision (mAP): Cơ chế Gom Trung bình AP qua các Lớp Đối tượng", size=13.5, weight=700, fill=DARK)

    # Panel Trái: Biểu đồ thanh AP của 5 lớp bảo hộ
    p1_x, p1_y, p1_w, p1_h = 10, 38, 510, 182
    rect(f, p1_x, p1_y, p1_w, p1_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p1_y + 14, "1. Điểm AP riêng lẻ của 5 lớp đối tượng bảo hộ lao động (sfchd_5class)", size=10.0, weight=700, fill=DARK)

    # 5 thanh Bar Chart ngang
    bar_data = [
        ("person (người)", 0.7186, "71.86%", BLUE),
        ("safety_clothes (áo phản quang)", 0.6494, "64.94%", BLUE),
        ("helmet (mũ bảo hộ)", 0.6210, "62.10%", BLUE),
        ("self_clothes (quần áo thường)", 0.5764, "57.64%", BLUE),
        ("head (đầu trần / không mũ)", 0.3884, "38.84%", RED),
    ]

    max_bar_w = 265
    y_bar_start = p1_y + 32
    bar_gap = 26

    for i, (cname, val, pct, col) in enumerate(bar_data):
        by = y_bar_start + i * bar_gap
        # Tên nhãn
        f.text(p1_x + 155, by + 9, cname, size=8.5, weight=600, fill=DARK, anchor="end")
        # Nền thanh xám
        rect(f, p1_x + 162, by, max_bar_w, 17, fill="#ECEFF1", stroke="none", rx=3)
        # Thanh giá trị có màu
        bw = val * max_bar_w
        rect(f, p1_x + 162, by, bw, 17, fill=col, stroke="none", rx=3)
        # Text giá trị AP
        lbl_x = p1_x + 166 + bw
        mean_px = p1_x + 162 + 0.5908 * max_bar_w
        if lbl_x < mean_px + 3 < lbl_x + 105:  # nhãn bị đường trung bình cắt: đặt sang phải đường
            lbl_x = mean_px + 6
        f.text(lbl_x, by + 9, f"{val:.4f} ({pct})", size=8.2, weight=700, fill=col)

    # Đường mốc mAP trung bình = 0.5908
    mean_val = 0.5908
    mean_x = p1_x + 162 + mean_val * max_bar_w
    f.a(f'<line x1="{mean_x:.1f}" y1="{y_bar_start-4}" x2="{mean_x:.1f}" y2="{y_bar_start+5*bar_gap}" stroke="{DARK}" stroke-width="1.6" stroke-dasharray="3 3"/>')
    f.text(mean_x, y_bar_start + 5 * bar_gap + 8, f"Trung bình mAP = {mean_val:.4f}", size=8.5, weight=700, fill=DARK, anchor="middle")

    # Mũi tên gom trung bình giữa 2 panel
    f.a(f'<polygon points="526,{p1_y+91} 540,{p1_y+91} 536,{p1_y+86} 544,{p1_y+91} 536,{p1_y+96} 540,{p1_y+91}" fill="{DARK}" stroke="{DARK}" stroke-width="1.5"/>')

    # Panel Phải: Công thức tính và ý nghĩa mAP
    p2_x, p2_y, p2_w, p2_h = 548, 38, 342, 182
    rect(f, p2_x, p2_y, p2_w, p2_h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p2_y + 14, "2. Công thức và Giá trị mAP tổng thể", size=10.0, weight=700, fill=DARK)

    # Khung công thức toán
    rect(f, p2_x + 10, p2_y + 26, p2_w - 20, 52, fill=CALC, stroke="#90CAF9", sw=1.0, rx=4)
    f.rich(p2_x + (p2_w - 20) / 2 + 10, p2_y + 40, [
        ("mAP = (1 / C) × Σ AP_c", "b"),
    ], size=10.5, anchor="middle", fill=BLUE)
    f.text(p2_x + (p2_w - 20) / 2 + 10, p2_y + 60, "mAP = (AP_1 + AP_2 + AP_3 + AP_4 + AP_5) / 5 = 0.5908", size=8.0, italic=True, fill=DARK, anchor="middle")

    # 3 ý nghĩa quan trọng
    txt(f, p2_x + 14, p2_y + 92, [
        [("• Thước đo toàn diện: ", "b"), ("Đại diện sức mạnh chung của mạng AI.", "t")],
        [("• Kháng mất cân bằng lớp: ", "b"), ("Mỗi lớp có trọng số ngang nhau,", "t")],
        [("  không bị lớp có nhiều ảnh lấn át lớp hiếm gặp.", "t")],
        [("• Cảnh báo lớp yếu: ", "b"), ("Lớp head (38.8%) kéo tụt mAP chung,", "t")],
        [("  chỉ ra điểm nghẽn cần bổ sung thêm dữ liệu huấn luyện.", "t")],
    ], size=8.5, dy=19)

    source(f, 226, "Nguồn: REPO ai/automation/leaderboards/sfchd_5class.csv; Ultralytics YOLOv8n.")
    return f


# ==============================================================================
# HÌNH 3B: SO SÁNH MAP@0.50 (VOC) VS MAP@0.50:0.95 (COCO)
# ==============================================================================
def fig_map50_vs_95():
    f = Fig(W, 238)
    tier(f, "T2 chung")
    f.text(10, 20, "So sánh Chuẩn mAP@0.50 (PASCAL VOC) vs mAP@0.50:0.95 (MS COCO)", size=13.5, weight=700, fill=DARK)

    col_h = 166
    y_c = 38

    # Cột 1: mAP@0.50 (Khoan dung)
    c1_x, c1_w = 10, 275
    rect(f, c1_x, y_c, c1_w, col_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(c1_x + c1_w / 2, y_c + 14, "A. Chuẩn VOC: mAP@0.50 (Khoan dung)", size=9.5, weight=700, fill=DARK, anchor="middle")

    # Mini plot P-R mAP50
    gx1, gy1, gw_s, gh_s = c1_x + 30, y_c + 30, 215, 80
    f.a(f'<line x1="{gx1}" y1="{gy1+gh_s}" x2="{gx1+gw_s}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<line x1="{gx1}" y1="{gy1}" x2="{gx1}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.2"/>')
    # Đường cong phồng to
    f.a(f'<path d="M {gx1} {gy1+4} C {gx1+130} {gy1+8}, {gx1+180} {gy1+24}, {gx1+gw_s-6} {gy1+gh_s} L {gx1+gw_s-6} {gy1+gh_s} L {gx1} {gy1+gh_s} Z" fill="#C8E6C9" opacity="0.6"/>')
    f.a(f'<path d="M {gx1} {gy1+4} C {gx1+130} {gy1+8}, {gx1+180} {gy1+24}, {gx1+gw_s-6} {gy1+gh_s}" fill="none" stroke="{GREEN}" stroke-width="2.2"/>')
    f.text(gx1 + gw_s * 0.45, gy1 + gh_s * 0.55, "mAP@0.50 = 0.8924", size=10.0, weight=700, fill=DARK, anchor="middle")

    # Diễn giải Cột 1
    txt(f, c1_x + 12, gy1 + gh_s + 15, [
        [("• Tiêu chí: ", "b"), ("Hộp chỉ cần chạm IoU ≥ 0.50.", "t")],
        [("• Bản chất: ", "b"), ("Đo xem có tìm thấy vật thể hay không.", "t")],
        [("• Hạn chế: ", "b"), ("Hộp méo hoặc lệch biên vẫn được điểm tối đa.", "t")],
    ], size=8.0, dy=14.5)

    # Mũi tên siết IoU giữa Cột 1 và Cột 2
    f.a(f'<polygon points="290,{y_c+70} 305,{y_c+70} 301,{y_c+66} 309,{y_c+70} 301,{y_c+74} 305,{y_c+70}" fill="{DARK}" stroke="{DARK}" stroke-width="1.5"/>')
    f.text(300, y_c + 56, "Siết IoU", size=7.5, weight=700, fill=RED, anchor="middle")
    f.text(300, y_c + 84, "0.5 →", size=7.5, fill="#666666", anchor="middle")
    f.text(300, y_c + 94, "0.95", size=7.5, fill="#666666", anchor="middle")

    # Cột 2: Tại mốc IoU = 0.95 (Cực kỳ khắt khe)
    c2_x, c2_w = 314, 275
    rect(f, c2_x, y_c, c2_w, col_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(c2_x + c2_w / 2, y_c + 14, "B. Mốc khắt khe: IoU = 0.95", size=9.5, weight=700, fill=DARK, anchor="middle")

    # Mini plot P-R IoU=0.95
    gx2, gy2 = c2_x + 30, y_c + 30
    f.a(f'<line x1="{gx2}" y1="{gy2+gh_s}" x2="{gx2+gw_s}" y2="{gy2+gh_s}" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<line x1="{gx2}" y1="{gy2}" x2="{gx2}" y2="{gy2+gh_s}" stroke="{DARK}" stroke-width="1.2"/>')
    # Đường cong co cụm
    f.a(f'<path d="M {gx2} {gy2+24} C {gx2+30} {gy2+44}, {gx2+50} {gy2+66}, {gx2+75} {gy2+gh_s} L {gx2+75} {gy2+gh_s} L {gx2} {gy2+gh_s} Z" fill="#FFCDD2" opacity="0.6"/>')
    f.a(f'<path d="M {gx2} {gy2+24} C {gx2+30} {gy2+44}, {gx2+50} {gy2+66}, {gx2+75} {gy2+gh_s}" fill="none" stroke="{RED}" stroke-width="2.2"/>')
    f.text(gx2 + 130, gy2 + 42, "AP@0.95 < 0.1500", size=9.5, weight=700, fill=RED, anchor="middle")

    # Diễn giải Cột 2
    txt(f, c2_x + 12, gy2 + gh_s + 15, [
        [("• Tiêu chí: ", "b"), ("Hộp phải trùng khít 95% diện tích nhãn.", "t")],
        [("• Bản chất: ", "b"), ("Lệch vài pixel lập tức bị phạt thành FP.", "t")],
        [("• Thách thức: ", "b"), ("Rất khó với vật thể nhỏ và mạng INT8.", "t")],
    ], size=8.0, dy=14.5)

    # Cột 3: Chuẩn COCO mAP50-95 (Tổng hợp toàn diện)
    c3_x, c3_w = 597, 293
    rect(f, c3_x, y_c, c3_w, col_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(c3_x + c3_w / 2, y_c + 14, "C. Chuẩn COCO: mAP@0.50:0.95", size=9.5, weight=700, fill=DARK, anchor="middle")

    # Khung công thức trung bình 10 mốc
    rect(f, c3_x + 10, y_c + 28, c3_w - 20, 56, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(c3_x + (c3_w - 20) / 2 + 10, y_c + 42, "Trung bình cộng tại 10 mốc IoU:", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(c3_x + (c3_w - 20) / 2 + 10, y_c + 57, "0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95", size=7.5, fill="#555555", anchor="middle")
    f.text(c3_x + (c3_w - 20) / 2 + 10, y_c + 72, "mAP50-95 = 0.5908 (Điểm thực tế)", size=8.5, weight=700, fill=DARK, anchor="middle")

    # Diễn giải Cột 3
    txt(f, c3_x + 12, y_c + 94, [
        [("• Đánh giá kép: ", "b"), ("Đo cả nhận diện và độ chuẩn xác pixel.", "t")],
        [("• Chuẩn vàng hiện đại: ", "b"), ("Mọi bảng xếp hạng quốc tế", "t")],
        [("  (COCO, Ultralytics, Paper) đều dùng thước đo này.", "t")],
        [("• Phản ánh thực chiến: ", "b"), ("Loại bỏ hiện tượng ăn may khi box", "t")],
        [("  bắt trúng đối tượng nhưng vị trí viền méo mó.", "t")],
    ], size=8.0, dy=14.5)

    source(f, 210, "Nguồn: COCO Evaluation Protocol; Lin et al. ECCV 2014; Y6 tr.8.")
    return f


# ==============================================================================
# HÌNH 4: ĐỘ SỤT GIẢM DO LƯỢNG TỬ HÓA (DELTA mAP) VÀ ĐÁNH ĐỔI NPU RK3588
# ==============================================================================
def fig_delta_map_quantization():
    f = Fig(W, 268)
    tier(f, "T2 chung")
    f.text(10, 22, "Độ sụt giảm do Lượng tử hóa (ΔmAP) và Đánh đổi Hiệu năng trên NPU RK3588", size=13.5, weight=700, fill=DARK)

    p_y = 38
    p_h = 200

    # -------------------------------------------------------------------------
    # Panel Trái: Đánh đổi FP32 vs INT8 và Thước đo Delta mAP
    # -------------------------------------------------------------------------
    p1_x, p1_w = 10, 440
    rect(f, p1_x, p_y, p1_w, p_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p_y + 16, "1. Đánh đổi mô hình gốc (FP32) vs Lượng tử hóa (INT8)", size=10.5, weight=700, fill=DARK)

    # Cột FP32 Baseline
    col1_x, col1_w = p1_x + 18, 114
    col1_h = 86
    col1_y = p_y + 34
    rect(f, col1_x, col1_y, col1_w, col1_h, fill="#E1F5FE", stroke=BLUE, sw=1.5, rx=4)
    f.text(col1_x + col1_w / 2, col1_y + 17, "FP32 Baseline", size=9.5, weight=700, fill=BLUE, anchor="middle")
    f.text(col1_x + col1_w / 2, col1_y + 37, "mAP: 45.2%", size=12.0, weight=700, fill=DARK, anchor="middle")
    f.text(col1_x + col1_w / 2, col1_y + 55, "Bộ nhớ: 100% (Gốc)", size=8.0, fill="#555555", anchor="middle")
    f.text(col1_x + col1_w / 2, col1_y + 71, "Tốc độ: 1.0x (NPU chậm)", size=8.0, fill="#555555", anchor="middle")

    # Mũi tên chênh lệch Delta mAP
    mid_x = p1_x + 160
    f.a(f'<line x1="{mid_x}" y1="{p_y + 60}" x2="{mid_x + 46}" y2="{p_y + 60}" stroke="{RED}" stroke-width="2.0"/>')
    f.a(f'<polygon points="{mid_x+46},{p_y+56} {mid_x+54},{p_y+60} {mid_x+46},{p_y+64}" fill="{RED}"/>')
    f.text(mid_x + 25, p_y + 48, "ΔmAP", size=9.5, weight=700, fill=RED, anchor="middle")
    f.text(mid_x + 25, p_y + 76, "-1.4%", size=11.5, weight=700, fill=RED, anchor="middle")

    # Cột INT8 Quantized
    col2_x, col2_w = p1_x + 242, 114
    col2_h = 86
    col2_y = p_y + 34
    rect(f, col2_x, col2_y, col2_w, col2_h, fill="#FFF3E0", stroke=ORANGE, sw=1.5, rx=4)
    f.text(col2_x + col2_w / 2, col2_y + 17, "INT8 (RKNN)", size=9.5, weight=700, fill=ORANGE, anchor="middle")
    f.text(col2_x + col2_w / 2, col2_y + 37, "mAP: 43.8%", size=12.0, weight=700, fill=DARK, anchor="middle")
    f.text(col2_x + col2_w / 2, col2_y + 55, "Bộ nhớ: -75% (Tiết kiệm)", size=8.0, weight=700, fill=DARK, anchor="middle")
    f.text(col2_x + col2_w / 2, col2_y + 71, "Tốc độ: x3.8 (Tối đa 3 Core)", size=8.0, weight=700, fill=DARK, anchor="middle")

    # Khung tiêu chuẩn đánh giá công nghiệp
    box_res_y = p_y + 130
    rect(f, p1_x + 14, box_res_y, p1_w - 28, 56, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(p1_x + 22, box_res_y + 16, "Tiêu chuẩn đánh giá suy giảm:", size=9.0, weight=700, fill=DARK)
    f.rich(p1_x + 22, box_res_y + 32, [
        ("• ", "t"), ("ΔmAP ≤ 1.5 - 2.0%: ", "b"),
        ("PASS. Đạt chuẩn đưa thẳng vào vận hành công nghiệp.", "t"),
    ], size=8.0)
    f.rich(p1_x + 22, box_res_y + 46, [
        ("• ", "t"), ("ΔmAP > 3.0%: ", "b"),
        ("FAIL. Cần can thiệp QAT hoặc Hybrid Quantization (FP16).", "t"),
    ], size=8.0)

    # -------------------------------------------------------------------------
    # Panel Phải: Bản chất sai số hình học do Quantization Jitter
    # -------------------------------------------------------------------------
    p2_x, p2_w = 460, 430
    rect(f, p2_x, p_y, p2_w, p_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p_y + 16, "2. Bản chất sai số: Lệch viền do làm tròn số học (Jitter)", size=10.5, weight=700, fill=DARK)

    # Ô A: FP32 khớp chuẩn
    box_a_x, box_a_y, box_a_w, box_a_h = p2_x + 14, p_y + 30, 186, 56
    rect(f, box_a_x, box_a_y, box_a_w, box_a_h, fill="#E1F5FE", stroke="#90CAF9", sw=1.0, rx=4)
    f.text(box_a_x + 8, box_a_y + 14, "A. FP32 (Độ chính xác cao)", size=8.0, weight=700, fill=BLUE)
    # Hộp GT xám và Hộp FP32 xanh
    rect(f, box_a_x + 10, box_a_y + 20, 36, 28, fill="white", stroke="#78909C", sw=1.0, rx=2, dashed=True)
    rect(f, box_a_x + 9, box_a_y + 19, 38, 30, fill="none", stroke=BLUE, sw=1.6, rx=2)
    # Nhãn text bên phải không đè hộp
    f.text(box_a_x + 56, box_a_y + 32, "IoU = 0.91 (Khớp 91%)", size=8.0, weight=700, fill=DARK)
    f.text(box_a_x + 56, box_a_y + 46, "Viền ôm sát nhãn thực tế", size=7.5, fill="#555555")

    # Ô B: INT8 lệch nhẹ
    box_b_x, box_b_y, box_b_w, box_b_h = p2_x + 14, p_y + 92, 186, 56
    rect(f, box_b_x, box_b_y, box_b_w, box_b_h, fill="#FFF3E0", stroke="#FFE0B2", sw=1.0, rx=4)
    f.text(box_b_x + 8, box_b_y + 14, "B. INT8 (Làm tròn số học)", size=8.0, weight=700, fill=ORANGE)
    # Hộp GT xám và Hộp INT8 cam lệch 4px
    rect(f, box_b_x + 10, box_b_y + 20, 36, 28, fill="white", stroke="#78909C", sw=1.0, rx=2, dashed=True)
    rect(f, box_b_x + 15, box_b_y + 24, 35, 27, fill="none", stroke=ORANGE, sw=1.6, rx=2, dashed=True)
    # Nhãn text bên phải không đè hộp
    f.text(box_b_x + 56, box_b_y + 32, "IoU = 0.63 (Lệch 4px)", size=8.0, weight=700, fill=ORANGE)
    f.text(box_b_x + 56, box_b_y + 46, "Nhiễu làm tròn (Jitter)", size=7.5, fill="#555555")

    # Bảng phân tích tác động tới mAP50 vs mAP50-95
    t_x, t_y, t_w, t_h = p2_x + 208, p_y + 30, p2_w - 222, 118
    rect(f, t_x, t_y, t_w, t_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(t_x + 10, t_y + 16, "Sát hạch qua 2 thước đo:", size=8.5, weight=700, fill=DARK)

    # Dòng 1: mAP@0.50
    f.rich(t_x + 10, t_y + 35, [
        ("• mAP@0.50: ", "b"), ("Cả 2 đều PASS", "b"),
    ], size=8.0, fill=GREEN)
    f.text(t_x + 18, t_y + 49, "Cả 0.91 và 0.63 đều ≥ 0.50", size=7.5, fill="#555555")
    f.text(t_x + 18, t_y + 61, "-> mAP50 hầu như không đổi", size=7.5, fill=GREEN)

    # Dòng 2: mAP@0.75 (trong mAP50-95)
    f.rich(t_x + 10, t_y + 80, [
        ("• mAP@0.75: ", "b"), ("INT8 bị FAIL", "b"),
    ], size=8.0, fill=RED)
    f.text(t_x + 18, t_y + 94, "FP32: 0.91 ≥ 0.75 (Đạt TP)", size=7.5, fill=BLUE)
    f.text(t_x + 18, t_y + 106, "INT8: 0.63 < 0.75 (Rớt thành FP)", size=7.5, fill=RED)

    # Diễn giải chốt ở đáy panel 2
    f.text(p2_x + 14, p_y + 164, "• Hệ quả: Lệch 3-5px không ảnh hưởng mAP50 nhưng kéo tụt mAP50-95.", size=8.0, fill=DARK)
    f.text(p2_x + 14, p_y + 180, "• Giải pháp: Dùng QAT hoặc Hybrid Quantization (giữ Head ở FP16).", size=8.0, fill=DARK)

    source(f, 248, "Nguồn: Rockchip RKNN-Toolkit2 Docs; Nagel et al. White Paper 2021; Y6 tr.12.")
    return f


# ==============================================================================
# HÌNH 5: THÔNG SỐ MÔ HÌNH (PARAMETERS / PARAMS) VÀ BỘ NHỚ TRÊN RK3588
# ==============================================================================
def fig_parameters():
    f = Fig(W, 268)
    tier(f, "T2 chung")
    f.text(10, 22, "Thông số Mô hình (Parameters / Params) và Ý nghĩa Bộ nhớ trên RK3588", size=13.5, weight=700, fill=DARK)

    p_y = 38
    p_h = 200

    # -------------------------------------------------------------------------
    # Panel Trái: Cấu thành Parameters trong Tầng Tích chập (Convolution)
    # -------------------------------------------------------------------------
    p1_x, p1_w = 10, 440
    rect(f, p1_x, p_y, p1_w, p_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p1_x + 14, p_y + 16, "1. Bản chất: Trọng số (Weights) và Bias trong Tầng Conv2D", size=10.5, weight=700, fill=DARK)

    # Khung công thức tính Params
    f_box_x, f_box_y, f_box_w, f_box_h = p1_x + 14, p_y + 28, p1_w - 28, 62
    rect(f, f_box_x, f_box_y, f_box_w, f_box_h, fill="#E3F2FD", stroke="#90CAF9", sw=1.0, rx=4)
    f.text(f_box_x + f_box_w / 2, f_box_y + 16, "Công thức tính số Parameters của một tầng tích chập:", size=8.5, weight=700, fill=BLUE, anchor="middle")
    f.rich(f_box_x + f_box_w / 2, f_box_y + 34, [
        ("Params = ", "b"),
        ("(K × K × C", "b"), ("in", "s"), (") × C", "b"), ("out", "s"),
        (" + C", "b"), ("out", "s"), (" (với K: kernel, C: số kênh)", "t"),
    ], size=10.0, anchor="middle", fill=DARK)
    f.text(f_box_x + f_box_w / 2, f_box_y + 50, "Ví dụ Conv 3x3 (Cin=64, Cout=128): (3 × 3 × 64) × 128 + 128 = 73,856 params", size=7.5, fill="#444444", anchor="middle")

    # Phân bố Params trong mô hình YOLO
    d_box_y = p_y + 98
    rect(f, p1_x + 14, d_box_y, p1_w - 28, 88, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(p1_x + 22, d_box_y + 16, "Phân bố Parameters trong kiến trúc YOLO (Ví dụ YOLOv8n ~ 3.2M):", size=8.5, weight=700, fill=DARK)

    # 3 khối thành phần
    kw = 126
    # Khối Backbone
    rect(f, p1_x + 22, d_box_y + 26, kw, 52, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=3)
    f.text(p1_x + 22 + kw / 2, d_box_y + 40, "Backbone (~45%)", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(p1_x + 22 + kw / 2, d_box_y + 54, "~1.44M params", size=8.0, fill=DARK, anchor="middle")
    f.text(p1_x + 22 + kw / 2, d_box_y + 68, "Trích xuất đặc trưng", size=7.0, fill="#555555", anchor="middle")

    # Khối Neck
    rect(f, p1_x + 156, d_box_y + 26, kw, 52, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=3)
    f.text(p1_x + 156 + kw / 2, d_box_y + 40, "Neck / PANet (~35%)", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(p1_x + 156 + kw / 2, d_box_y + 54, "~1.12M params", size=8.0, fill=DARK, anchor="middle")
    f.text(p1_x + 156 + kw / 2, d_box_y + 68, "Hợp nhất đa tỷ lệ", size=7.0, fill="#555555", anchor="middle")

    # Khối Head
    rect(f, p1_x + 290, d_box_y + 26, kw, 52, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=3)
    f.text(p1_x + 290 + kw / 2, d_box_y + 40, "Detect Head (~20%)", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(p1_x + 290 + kw / 2, d_box_y + 54, "~0.64M params", size=8.0, fill=DARK, anchor="middle")
    f.text(p1_x + 290 + kw / 2, d_box_y + 68, "Phân loại & Box reg", size=7.0, fill="#555555", anchor="middle")

    # -------------------------------------------------------------------------
    # Panel Phải: Dung lượng Lưu trữ & Ý nghĩa trên NPU RK3588
    # -------------------------------------------------------------------------
    p2_x, p2_w = 460, 430
    rect(f, p2_x, p_y, p2_w, p_h, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(p2_x + 14, p_y + 16, "2. Dung lượng Bộ nhớ Tĩnh (RAM / ROM) theo Kiểu Dữ liệu", size=10.5, weight=700, fill=DARK)

    # Bảng 3 mức nén dữ liệu cho 3.2M params
    tb_y = p_y + 28
    rect(f, p2_x + 14, tb_y, p2_w - 28, 86, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)

    # Header bảng
    rect(f, p2_x + 14, tb_y, p2_w - 28, 20, fill="#ECEFF1", stroke="none", rx=3)
    f.text(p2_x + 30, tb_y + 14, "Định dạng", size=7.5, weight=700, fill=DARK)
    f.text(p2_x + 110, tb_y + 14, "Byte / Param", size=7.5, weight=700, fill=DARK)
    f.text(p2_x + 200, tb_y + 14, "Dung lượng (3.2M)", size=7.5, weight=700, fill=DARK)
    f.text(p2_x + 300, tb_y + 14, "Tác động phần cứng RK3588", size=7.5, weight=700, fill=DARK)

    # Dòng 1: FP32
    f.text(p2_x + 30, tb_y + 36, "FP32 (PyTorch)", size=7.5, fill=DARK, weight=700)
    f.text(p2_x + 110, tb_y + 36, "4 bytes", size=7.5, fill=DARK)
    f.text(p2_x + 200, tb_y + 36, "12.8 MB", size=8.0, weight=700, fill=DARK)
    f.text(p2_x + 300, tb_y + 36, "Nặng, NPU không tối ưu", size=7.5, fill="#555555")

    # Dòng 2: FP16
    f.text(p2_x + 30, tb_y + 54, "FP16 (Nửa chính xác)", size=7.5, fill=DARK, weight=700)
    f.text(p2_x + 110, tb_y + 54, "2 bytes", size=7.5, fill=DARK)
    f.text(p2_x + 200, tb_y + 54, "6.4 MB (-50%)", size=8.0, weight=700, fill=DARK)
    f.text(p2_x + 300, tb_y + 54, "Chạy tốt trên NPU core", size=7.5, fill="#555555")

    # Dòng 3: INT8
    f.text(p2_x + 30, tb_y + 72, "INT8 (RKNN)", size=7.5, fill=GREEN, weight=700)
    f.text(p2_x + 110, tb_y + 72, "1 byte", size=7.5, fill=GREEN, weight=700)
    f.text(p2_x + 200, tb_y + 72, "3.2 MB (-75%)", size=8.0, weight=700, fill=GREEN)
    f.text(p2_x + 300, tb_y + 72, "Vừa vặn SRAM, siêu nhanh", size=7.5, fill=GREEN, weight=700)

    # Khung lưu ý phân biệt: Params vs Activations vs FLOPs
    nt_y = p_y + 122
    rect(f, p2_x + 14, nt_y, p2_w - 28, 66, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(p2_x + 22, nt_y + 15, "Lưu ý then chốt khi thiết kế cho Edge AI:", size=8.5, weight=700, fill=DARK)
    f.rich(p2_x + 22, nt_y + 31, [
        ("• ", "t"), ("Parameters = Bộ nhớ tĩnh: ", "b"),
        ("Chỉ phụ thuộc số tầng và số kênh, không đổi theo cỡ ảnh.", "t"),
    ], size=8.0)
    f.rich(p2_x + 22, nt_y + 45, [
        ("• ", "t"), ("Không đại diện cho Tốc độ: ", "b"),
        ("Mô hình ít params vẫn có thể chậm nếu kiến trúc phân mảnh.", "t"),
    ], size=8.0)
    f.rich(p2_x + 22, nt_y + 59, [
        ("• ", "t"), ("Khác biệt Activations: ", "b"),
        ("RAM runtime phụ thuộc lớn vào feature map (ảnh to thì RAM tăng).", "t"),
    ], size=8.0)

    source(f, 248, "Nguồn: Ultralytics YOLO Architecture; Rockchip RK3588 TRM; Lin et al. MCUNet 2020.")
    return f


# ==============================================================================
# HÌNH 6: BỘ NHỚ ĐỘNG (ACTIVATIONS) VÀ NÚT THẮT BĂNG THÔNG TRÊN RK3588
# ==============================================================================
def fig_activations_memory():
    """HÌNH 6: Bộ nhớ Động (Activations) vs Trọng số Tĩnh (Parameters) và Nút thắt Băng thông SRAM/DDR."""
    f = Fig(W, 395)
    tier(f, "T2 chung")

    f.text(20, 24, "BỘ NHỚ ĐỘNG (ACTIVATIONS) VS. TRỌNG SỐ TĨNH (PARAMETERS) VÀ NÚT THẮT SRAM/DDR", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Đối chiếu trực quan: Trọng số mô hình bất biến vs. Feature Map bùng nổ theo diện tích ảnh dẫn đến tràn SRAM ra DDR ngoài", size=9.2, fill=GRAY)

    box_y = 56
    box_h = 270

    # ==============================================================================
    # NỬA TRÁI: BIỂU ĐỒ CỘT ĐỐI CHIẾU DUNG LƯỢNG
    # ==============================================================================
    p1_x = 20
    p1_w = 425
    rect(f, p1_x, box_y, p1_w, box_h, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(p1_x + 12, 70, "1. ĐỐI CHIẾU DUNG LƯỢNG: PARAMETERS (TĨNH) VS. ACTIVATIONS (ĐỘNG)", size=8.5, weight=700, fill=DARK)
    f.text(p1_x + 12, 82, "Weights cố định theo model; Activations tăng bậc 2 theo diện tích H × W", size=6.8, fill=GRAY)

    # Khung biểu đồ cột
    rect(f, p1_x + 10, 92, p1_w - 20, 168, fill="#FFFFFF", stroke="#CFD8DC", sw=0.8, rx=3)

    # Trục tọa độ biểu đồ
    base_y = 222
    f.a(f'<line x1="45" y1="{base_y}" x2="415" y2="{base_y}" stroke="#90A4AE" stroke-width="1.0"/>')

    # Đường gióng mức dung lượng
    for y_val, lbl in [(177, "100 MB"), (132, "200 MB")]:
        f.a(f'<line x1="58" y1="{y_val}" x2="415" y2="{y_val}" stroke="#ECEFF1" stroke-width="0.8" stroke-dasharray="3 3"/>')
        f.text(33, y_val, lbl, size=6.5, fill="#90A4AE", anchor="start")

    # Cột 0: Parameters (Weights) - Cố định
    rect(f, 65, base_y - 10, 52, 10, fill="#E0F2FE", stroke="#0284C7", sw=1.2, rx=2)
    rect(f, 65, base_y - 24, 52, 12, fill="#0284C7", stroke="#0369A1", sw=0.8, rx=2)
    f.text(91, base_y - 18, "3.2 MB", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")
    f.text(91, base_y + 10, "Parameters", size=6.8, weight=700, fill="#0369A1", anchor="middle")
    f.text(91, base_y + 22, "(Cố định)", size=6.5, fill="#78909C", anchor="middle")

    # Cột 1: Activation 320x320
    rect(f, 150, base_y - 16, 52, 16, fill="#DCFCE7", stroke="#16A34A", sw=1.2, rx=2)
    rect(f, 150, base_y - 30, 52, 12, fill="#16A34A", stroke="#15803D", sw=0.8, rx=2)
    f.text(176, base_y - 24, "~15 MB", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")
    f.text(176, base_y + 10, "Ảnh 320²", size=6.8, weight=700, fill="#166534", anchor="middle")
    f.text(176, base_y + 22, "(1x diện tích)", size=6.5, fill="#78909C", anchor="middle")

    # Cột 2: Activation 640x640 (Chuẩn)
    rect(f, 235, base_y - 38, 52, 38, fill="#FED7AA", stroke="#EA580C", sw=1.2, rx=2)
    rect(f, 235, base_y - 52, 52, 12, fill="#EA580C", stroke="#C2410C", sw=0.8, rx=2)
    f.text(261, base_y - 46, "~60 MB", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")
    rect(f, 235, base_y - 66, 52, 11, fill="#FFEDD5", stroke="#FDBA74", sw=0.7, rx=2)
    f.text(261, base_y - 61, "x4 diện tích", size=6.5, weight=700, fill="#9A3412", anchor="middle")
    f.text(261, base_y + 10, "Ảnh 640²", size=6.8, weight=700, fill="#9A3412", anchor="middle")
    f.text(261, base_y + 22, "(Chuẩn phổ biến)", size=6.5, fill="#78909C", anchor="middle")

    # Cột 3: Activation 1280x1280 (Bùng nổ)
    rect(f, 320, base_y - 96, 52, 96, fill="#FECACA", stroke="#DC2626", sw=1.5, rx=2)
    rect(f, 320, base_y - 110, 52, 12, fill="#DC2626", stroke="#B91C1C", sw=0.8, rx=2)
    f.text(346, base_y - 104, "~240 MB", size=6.8, weight=700, fill="#FFFFFF", anchor="middle")
    rect(f, 320, base_y - 124, 52, 11, fill="#FEE2E2", stroke="#FCA5A5", sw=0.7, rx=2)
    f.text(346, base_y - 119, "x16 lần!", size=6.5, weight=700, fill="#991B1B", anchor="middle")
    f.text(346, base_y + 10, "Ảnh 1280²", size=6.8, weight=700, fill="#991B1B", anchor="middle")
    f.text(346, base_y + 22, "(Bùng nổ bộ nhớ)", size=6.5, weight=700, fill="#DC2626", anchor="middle")

    # Mũi tên uốn lượn biểu diễn bùng nổ O(H x W)
    f.a(f'<path d="M 195 190 Q 240 128 320 108" stroke="#DC2626" stroke-width="1.8" fill="none" stroke-dasharray="4 2" marker-end="url(#{f.marker("#DC2626", 1.8)})"/>')
    # Badge nền trắng chống đè nét đứt lên chữ
    rect(f, 240, 134, 76, 13, fill="#FFFFFF", stroke="#FCA5A5", sw=0.7, rx=2)
    f.text(278, 140.5, "Bùng nổ O(H×W)", size=6.5, weight=700, fill="#DC2626", anchor="middle")

    # Khung kết luận đáy trái
    rect(f, p1_x + 10, 268, p1_w - 20, 50, fill="#FFFFFF", stroke="#CFD8DC", sw=0.8, rx=3)
    f.text(p1_x + 16, 279, "• Đặc tính cốt lõi: Trọng số (weights) bất biến, chỉ nạp 1 lần vào RAM khi khởi động.", size=7.2, fill="#374151")
    f.text(p1_x + 16, 293, "• Nguy cơ thực tế: NPU hiếm khi nghẽn vì weights (chỉ 3.2 MB), mà luôn bị đe dọa", size=7.2, fill="#374151")
    f.text(p1_x + 16, 305, "  bởi Feature Maps của ảnh độ phân giải cao vượt quá dung lượng SRAM nội bộ.", size=7.2, weight=700, fill="#B71C1C")

    # ==============================================================================
    # NỬA PHẢI: SƠ ĐỒ PHẦN CỨNG NPU SRAM VS DDR RAM NGOÀI
    # ==============================================================================
    p2_x = 455
    p2_w = 425
    rect(f, p2_x, box_y, p2_w, box_h, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(p2_x + 12, 70, "2. SƠ ĐỒ PHẦN CỨNG: NÚT THẮT BĂNG THÔNG ON-CHIP SRAM VS. DDR NGOÀI", size=8.5, weight=700, fill=DARK)
    f.text(p2_x + 12, 82, "SRAM nội bộ siêu tốc vs. DDR ngoài nghẽn cổ chai (Memory Wall)", size=6.8, fill=GRAY)

    # Khung sơ đồ phần cứng
    rect(f, p2_x + 10, 92, p2_w - 20, 168, fill="#FFFFFF", stroke="#CFD8DC", sw=0.8, rx=3)

    # 1. Khối Lõi NPU (Core 0/1/2) bên trái
    rect(f, 475, 102, 165, 148, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(483, 114, "Lõi NPU RK3588 (Core 0/1/2)", size=7.2, weight=700, fill="#1E293B")

    # Mảng MAC
    rect(f, 483, 124, 149, 38, fill="#E0F2FE", stroke="#0284C7", sw=0.9, rx=3)
    f.text(557, 137, "Mảng Tính Toán MAC", size=6.8, weight=700, fill="#0369A1", anchor="middle")
    f.text(557, 150, "Đỉnh 2.0 TOPS / Core", size=6.5, fill="#0284C7", anchor="middle")

    # On-chip SRAM Cache
    rect(f, 483, 178, 149, 64, fill="#DCFCE7", stroke="#16A34A", sw=1.2, rx=3)
    f.text(557, 192, "ON-CHIP SRAM CACHE", size=7.2, weight=700, fill="#166534", anchor="middle")
    f.text(557, 206, "Dung lượng giới hạn (~vài MB)", size=6.5, fill="#15803D", anchor="middle")
    f.text(557, 219, "Băng thông siêu tốc > hàng trăm GB/s", size=6.5, weight=700, fill="#166534", anchor="middle")
    f.text(557, 232, "Độ trễ 0 ns · Tiêu hao điện cực thấp", size=6.5, fill="#15803D", anchor="middle")

    # Mũi tên vòng nội bộ MAC <-> SRAM (Cache Hit)
    f.a(f'<path d="M 520 162 L 520 178" stroke="#16A34A" stroke-width="1.8" marker-end="url(#{f.marker("#16A34A", 1.8)})"/>')
    f.a(f'<path d="M 590 178 L 590 162" stroke="#16A34A" stroke-width="1.8" marker-end="url(#{f.marker("#16A34A", 1.8)})"/>')
    f.text(555, 170, "Cache Hit", size=6.5, weight=700, fill="#166534", anchor="middle")

    # 2. Kênh Bus DDR và Biểu tượng Nút thắt cổ chai
    f.a(f'<line x1="640" y1="176" x2="735" y2="176" stroke="#DC2626" stroke-width="2.2" stroke-dasharray="3 2"/>')
    f.a(f'<line x1="735" y1="190" x2="640" y2="190" stroke="#DC2626" stroke-width="2.2" stroke-dasharray="3 2"/>')

    # Badge nút thắt cổ chai
    rect(f, 650, 166, 75, 34, fill="#FEE2E2", stroke="#EF4444", sw=0.9, rx=3)
    f.text(687, 173, "BUS DDR", size=6.5, weight=700, fill="#991B1B", anchor="middle")
    f.text(687, 183.5, "Nút thắt cổ chai", size=6.5, weight=700, fill="#DC2626", anchor="middle")
    f.text(687, 193, "(Memory Wall)", size=6.5, fill="#991B1B", anchor="middle")

    # 3. Khối External DRAM bên phải
    rect(f, 735, 102, 125, 148, fill="#FFF1F2", stroke="#E11D48", sw=1.1, rx=4)
    f.text(797, 114, "External DRAM", size=7.2, weight=700, fill="#9F1239", anchor="middle")
    f.text(797, 125, "(LPDDR4x / LPDDR5)", size=6.5, fill="#E11D48", anchor="middle")

    rect(f, 743, 134, 109, 108, fill="#FFFFFF", stroke="#FDA4AF", sw=0.8, rx=3)
    f.text(797, 146, "RAM Ngoại Vi", size=6.8, weight=700, fill="#BE123C", anchor="middle")
    f.text(749, 162, "• Dung lượng: 4 - 16 GB", size=6.5, fill="#374151")
    f.text(749, 176, "• Băng thông: ~34 GB/s", size=6.5, fill="#374151")
    f.text(749, 190, "• Tràn ra ngoài (Spill):", size=6.5, weight=700, fill="#E11D48")
    f.text(749, 204, "  Tiêu hao điện x10-50!", size=6.5, weight=700, fill="#E11D48")
    f.text(749, 218, "  Độ trễ cao (~100+ chu kỳ)", size=6.5, fill="#9F1239")
    f.text(749, 230, "  Kéo tụt FPS thực tế", size=6.5, weight=700, fill="#DC2626")

    # Khung kết luận đáy phải
    rect(f, p2_x + 10, 268, p2_w - 20, 50, fill="#FFFFFF", stroke="#CFD8DC", sw=0.8, rx=3)
    f.text(p2_x + 16, 279, "CHIẾN LƯỢC TỐI ƯU CỦA RKNN COMPILER & SYSTEM DESIGNER:", size=7.2, weight=700, fill=DARK)
    f.text(p2_x + 16, 293, "• Operator Fusion: Ghép Conv + BN + ReLU để giam giữ feature map trung gian trong SRAM.", size=7.0, fill="#374151")
    f.text(p2_x + 16, 305, "• Cân đối độ phân giải: Giữ ảnh 640×640 để vừa vặn SRAM, tránh sập bẫy nghẽn Bus DDR.", size=7.0, fill="#374151")

    # Dải băng thông điệp xuyên suốt toàn bộ hình
    rect(f, 20, 334, 860, 24, fill="#F1F5F9", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(450, 346, "BẢN CHẤT: Parameters quyết định dung lượng file (.rknn); Activations quyết định RAM thực thi và nguy cơ nghẽn phần cứng.", size=7.5, weight=700, fill="#1E293B", anchor="middle")

    source(f, 364, "Nguồn: Rockchip RK3588 TRM; Chen et al. Eyeriss ISCA 2016; Lin et al. MCUNet 2020.")
    return f


# ==============================================================================
# HÌNH 7: ĐỘ TRỄ 4 CHẶNG (LATENCY) & TIMELINE SUY LUẬN TRÊN RK3588
# ==============================================================================
def fig_latency_4_stages():
    """HÌNH 7: Cấu trúc Độ trễ 4 chặng (Latency Pipeline) trên SoC RK3588."""
    H = 435
    f = Fig(W, H)
    tier(f, "T1 RK3588")

    f.text(20, 24, "CẤU TRÚC ĐỘ TRỄ 4 CHẶNG (LATENCY PIPELINE) TRÊN SOC RK3588", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Minh họa trực quan 4 chặng: Ảnh camera gốc -> Tiền xử lý (LetterBox) -> NPU suy luận (3-Core) -> Hậu xử lý (NMS) & Timeline E2E", size=9.2, fill=GRAY)

    # -------------------------------------------------------------------------
    # PHẦN 1: HARDWARE DATAFLOW & ALGORITHM (NỬA TRÊN, Y: 56 -> 276)
    # -------------------------------------------------------------------------
    rect(f, 20, 56, W - 40, 220, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(32, 70, "1. LUỒNG THỰC THI 4 CHẶNG TRỰC QUAN (HARDWARE & ALGORITHM PIPELINE PER FRAME)", size=9.2, weight=700, fill=DARK)

    # -------------------------------------------------------------------------
    # Khối 0: Camera Input Frame (1080P)
    # -------------------------------------------------------------------------
    b0_x, b0_y, b0_w, b0_h = 32, 82, 122, 182
    rect(f, b0_x, b0_y, b0_w, b0_h, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(b0_x + b0_w / 2, b0_y + 14, "Ảnh Camera RTSP", size=8.2, weight=700, fill=DARK, anchor="middle")

    # Màn hình camera 16:9
    cam_x, cam_y, cam_w, cam_h = b0_x + 10, b0_y + 26, 102, 58
    rect(f, cam_x, cam_y, cam_w, cam_h, fill="#1E293B", stroke="#0F172A", sw=1.0, rx=3)
    # Vùng hiển thị camera
    disp_x, disp_y, disp_w, disp_h = cam_x + 2, cam_y + 2, cam_w - 4, cam_h - 4
    # Sky & Ground
    rect(f, disp_x, disp_y, disp_w, 34, fill="#E0F2FE", stroke="none")
    rect(f, disp_x, disp_y + 34, disp_w, disp_h - 34, fill="#CBD5E1", stroke="none")
    # Giàn giáo công trường
    f.a(f'<line x1="{disp_x + 12}" y1="{disp_y + 8}" x2="{disp_x + 12}" y2="{disp_y + disp_h}" stroke="#94A3B8" stroke-width="0.8"/>')
    f.a(f'<line x1="{disp_x + 28}" y1="{disp_y + 8}" x2="{disp_x + 28}" y2="{disp_y + disp_h}" stroke="#94A3B8" stroke-width="0.8"/>')
    f.a(f'<line x1="{disp_x + 8}" y1="{disp_y + 20}" x2="{disp_x + 32}" y2="{disp_y + 20}" stroke="#94A3B8" stroke-width="0.8"/>')
    # Công nhân trong khung ảnh
    wk_cx = disp_x + 68
    f.a(f'<circle cx="{wk_cx}" cy="{disp_y + 18}" r="4.5" fill="#F59E0B"/>')  # Nón bảo hộ vàng
    f.a(f'<circle cx="{wk_cx}" cy="{disp_y + 22}" r="3.2" fill="#FDE68A"/>')  # Mặt
    rect(f, wk_cx - 5.5, disp_y + 25, 11, 14, fill="#0284C7", stroke="none", rx=1.5)  # Áo xanh
    rect(f, wk_cx - 4.5, disp_y + 39, 3.5, 9, fill="#334155", stroke="none")  # Chân trái
    rect(f, wk_cx + 1.0, disp_y + 39, 3.5, 9, fill="#334155", stroke="none")  # Chân phải

    # Camera OSD (On-Screen Display)
    f.a(f'<circle cx="{disp_x + 8}" cy="{disp_y + 7}" r="2.2" fill="#EF4444"/>')
    f.text(disp_x + 13, disp_y + 7, "REC", size=6.5, weight=700, fill="#EF4444")
    f.text(disp_x + disp_w - 4, disp_y + 7, "1080P", size=6.5, weight=700, fill="#64748B", anchor="end")

    # Thông số khung hình camera
    f.text(b0_x + b0_w / 2, b0_y + 96, "Full HD (1920×1080)", size=7.2, weight=700, fill="#1E293B", anchor="middle")
    f.text(b0_x + b0_w / 2, b0_y + 109, "Tỉ lệ 16:9 · BGR/NV12", size=6.8, fill="#64748B", anchor="middle")
    f.text(b0_x + b0_w / 2, b0_y + 122, "DRAM Framebuffer", size=6.8, fill="#64748B", anchor="middle")

    # Badge trạng thái chặng 0
    rect(f, b0_x + 8, b0_y + 138, b0_w - 16, 34, fill="#F8FAFC", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(b0_x + b0_w / 2, b0_y + 149, "Độ phân giải lớn", size=6.5, fill="#475569", anchor="middle")
    f.text(b0_x + b0_w / 2, b0_y + 162, "Chưa tương thích NPU", size=6.5, weight=700, fill="#DC2626", anchor="middle")

    # Mũi tên 0 -> 1
    f.a(f'<path d="M {b0_x + b0_w + 1} 173 L {b0_x + b0_w + 18} 173" stroke="#64748B" stroke-width="1.8" fill="none" marker-end="url(#{f.marker("#64748B", 1.8)})"/>')
    f.text(b0_x + b0_w + 10, 163, "RGA2", size=6.5, weight=700, fill="#B45309", anchor="middle")

    # -------------------------------------------------------------------------
    # Khối 1: Chặng 1 - Pre-processing (RGA2 / CPU)
    # -------------------------------------------------------------------------
    b1_x, b1_y, b1_w, b1_h = 173, 82, 186, 182
    rect(f, b1_x, b1_y, b1_w, b1_h, fill="#FFFFFF", stroke="#F59E0B", sw=1.2, rx=4)
    f.text(b1_x + 10, b1_y + 14, "Chặng 1: Pre-processing", size=8.5, weight=700, fill="#B45309")
    rect(f, b1_x + b1_w - 68, b1_y + 6, 60, 16, fill="#FFFFFF", stroke="#D97706", sw=0.8, rx=2)
    f.text(b1_x + b1_w - 38, b1_y + 14, "T_pre ~2.5 ms", size=7.0, weight=700, fill="#B45309", anchor="middle")

    f.text(b1_x + 10, b1_y + 28, "Thực thi: Bộ tăng tốc RGA2 hoặc CPU", size=6.8, fill="#92400E")

    # Minh họa trực quan phép LetterBox
    lb_w, lb_h = 66, 66
    lb_x, lb_y = b1_x + (b1_w - lb_w) / 2, b1_y + 36
    rect(f, lb_x, lb_y, lb_w, lb_h, fill="#FFFFFF", stroke="#D97706", sw=1.0, rx=2)

    # Top pad (viền xám 114)
    rect(f, lb_x, lb_y, lb_w, 14, fill="#94A3B8", stroke="none")
    f.text(lb_x + lb_w / 2, lb_y + 7, "Pad xám (114)", size=6.5, fill="#FFFFFF", anchor="middle")

    # Bottom pad
    rect(f, lb_x, lb_y + lb_h - 14, lb_w, 14, fill="#94A3B8", stroke="none")
    f.text(lb_x + lb_w / 2, lb_y + lb_h - 7, "Giữ tỉ lệ 16:9", size=6.5, fill="#FFFFFF", anchor="middle")

    # Ảnh trung tâm 16:9 được scale gọn
    rect(f, lb_x, lb_y + 14, lb_w, 38, fill="#E0F2FE", stroke="none")
    rect(f, lb_x, lb_y + 38, lb_w, 14, fill="#CBD5E1", stroke="none")
    # Công nhân thu nhỏ
    wks_cx = lb_x + lb_w / 2
    f.a(f'<circle cx="{wks_cx}" cy="{lb_y + 23}" r="3.0" fill="#F59E0B"/>')
    rect(f, wks_cx - 3.5, lb_y + 27, 7.0, 10, fill="#0284C7", stroke="none", rx=1)
    rect(f, wks_cx - 2.8, lb_y + 37, 2.3, 7, fill="#334155", stroke="none")
    rect(f, wks_cx + 0.5, lb_y + 37, 2.3, 7, fill="#334155", stroke="none")

    # Nhãn kích thước đặt bên trái và dưới đáy box
    f.text(lb_x - 4, lb_y + lb_h / 2, "640", size=6.5, weight=700, fill="#D97706", anchor="end")
    f.text(lb_x + lb_w / 2, lb_y + lb_h + 8, "Khung chuẩn 640×640", size=6.5, weight=700, fill="#B45309", anchor="middle")

    # Danh sách thao tác
    f.text(b1_x + 10, b1_y + 118, "• Resize & LetterBox: Giữ tỉ lệ, chống méo", size=6.8, fill="#334155")
    f.text(b1_x + 10, b1_y + 132, "• Đổi màu BGR -> RGB & Chuẩn hoá giá trị", size=6.8, fill="#334155")
    f.text(b1_x + 10, b1_y + 146, "• Lượng tử hoá: Scale sang INT8 Tensor", size=6.8, fill="#334155")
    f.text(b1_x + 10, b1_y + 162, "-> Đầu ra: Tensor chuẩn [1, 3, 640, 640]", size=7.0, weight=700, fill="#B45309")

    # Mũi tên 1 -> 2 (Zero-Copy DMA, khoảng cách thoáng 47px)
    arr1_start = b1_x + b1_w
    arr1_end = arr1_start + 45
    f.a(f'<path d="M {arr1_start + 1} 173 L {arr1_end - 2} 173" stroke="#0284C7" stroke-width="2.0" fill="none" marker-end="url(#{f.marker("#0284C7", 2.0)})"/>')
    f.text(arr1_start + 23, 160, "DMA-BUF", size=6.5, weight=700, fill="#0284C7", anchor="middle")
    f.text(arr1_start + 23, 185, "Zero-Copy", size=6.5, fill="#0369A1", anchor="middle")

    # -------------------------------------------------------------------------
    # Khối 2: Chặng 2 - Pure NPU Inference (NPU RK3588)
    # -------------------------------------------------------------------------
    b2_x = arr1_end
    b2_y, b2_w, b2_h = 82, 246, 182
    rect(f, b2_x, b2_y, b2_w, b2_h, fill="#FFFFFF", stroke="#0284C7", sw=1.2, rx=4)
    f.text(b2_x + 10, b2_y + 14, "Chặng 2: Pure NPU Inference", size=8.5, weight=700, fill="#0369A1")
    rect(f, b2_x + b2_w - 74, b2_y + 6, 66, 16, fill="#FFFFFF", stroke="#0284C7", sw=0.8, rx=2)
    f.text(b2_x + b2_w - 41, b2_y + 14, "T_npu ~12.5 ms", size=7.0, weight=700, fill="#0369A1", anchor="middle")

    f.text(b2_x + 10, b2_y + 28, "Thực thi: 3 Lõi NPU RK3588 (Đỉnh 6.0 TOPS INT8)", size=6.8, fill="#075985")

    # Minh họa 3 Core NPU mini
    cw = (b2_w - 28) / 3
    for ci, cnm in enumerate(["Core 0 (2 TOPS)", "Core 1 (2 TOPS)", "Core 2 (2 TOPS)"]):
        cx = b2_x + 10 + ci * (cw + 4)
        rect(f, cx, b2_y + 36, cw, 16, fill="#E0F2FE", stroke="#0284C7", sw=0.8, rx=2)
        f.text(cx + cw / 2, b2_y + 44, cnm, size=6.5, weight=700, fill="#0369A1", anchor="middle")

    # Minh họa Mạng Nơ-ron Feature Maps & Head
    nn_y = b2_y + 58
    # Input Tensor
    rect(f, b2_x + 10, nn_y, 32, 46, fill="#E0F2FE", stroke="#0284C7", sw=0.8, rx=2)
    f.text(b2_x + 26, nn_y + 16, "Tensor", size=6.5, fill="#0369A1", anchor="middle")
    f.text(b2_x + 26, nn_y + 30, "640²×3", size=6.5, weight=700, fill="#0369A1", anchor="middle")

    # Mũi tên ->
    f.a(f'<path d="M {b2_x + 44} {nn_y + 23} L {b2_x + 53} {nn_y + 23}" stroke="#0284C7" stroke-width="1.2" fill="none" marker-end="url(#{f.marker("#0284C7", 1.2)})"/>')

    # Backbone Conv
    rect(f, b2_x + 55, nn_y + 4, 48, 38, fill="#E0F2FE", stroke="#0284C7", sw=0.9, rx=2)
    f.text(b2_x + 79, nn_y + 17, "Backbone", size=6.5, weight=700, fill="#0369A1", anchor="middle")
    f.text(b2_x + 79, nn_y + 29, "C2f / Conv", size=6.5, fill="#0284C7", anchor="middle")

    # Mũi tên ->
    f.a(f'<path d="M {b2_x + 105} {nn_y + 23} L {b2_x + 114} {nn_y + 23}" stroke="#0284C7" stroke-width="1.2" fill="none" marker-end="url(#{f.marker("#0284C7", 1.2)})"/>')

    # PANet & 3 Detect Heads
    rect(f, b2_x + 116, nn_y, 46, 14, fill="#E0F2FE", stroke="#0284C7", sw=0.8, rx=2)
    f.text(b2_x + 139, nn_y + 7, "P3 (80² S-obj)", size=6.5, weight=700, fill="#0369A1", anchor="middle")

    rect(f, b2_x + 116, nn_y + 16, 46, 14, fill="#E0F2FE", stroke="#0284C7", sw=0.8, rx=2)
    f.text(b2_x + 139, nn_y + 23, "P4 (40² M-obj)", size=6.5, weight=700, fill="#0369A1", anchor="middle")

    rect(f, b2_x + 116, nn_y + 32, 46, 14, fill="#E0F2FE", stroke="#0284C7", sw=0.8, rx=2)
    f.text(b2_x + 139, nn_y + 39, "P5 (20² L-obj)", size=6.5, weight=700, fill="#0369A1", anchor="middle")

    # Mũi tên gom ->
    f.a(f'<path d="M {b2_x + 164} {nn_y + 23} L {b2_x + 173} {nn_y + 23}" stroke="#0284C7" stroke-width="1.2" fill="none" marker-end="url(#{f.marker("#0284C7", 1.2)})"/>')

    # Raw Tensor output
    rect(f, b2_x + 175, nn_y + 4, 60, 38, fill="#E0F2FE", stroke="#0284C7", sw=1.0, rx=2)
    f.text(b2_x + 205, nn_y + 17, "Raw Output", size=6.5, weight=700, fill="#0369A1", anchor="middle")
    f.text(b2_x + 205, nn_y + 29, "[1, 84, 8400]", size=6.5, weight=700, fill="#0369A1", anchor="middle")

    # Danh sách thao tác
    f.text(b2_x + 10, b2_y + 120, "• Nạp trọng số INT8 từ SRAM Cache (weights 3.2 MB)", size=6.8, fill="#334155")
    f.text(b2_x + 10, b2_y + 134, "• Chiếm 67.5% tổng thời gian E2E -> Nút thắt chính", size=6.8, weight=700, fill="#C2410C")
    f.text(b2_x + 10, b2_y + 148, "• Nhân ma trận Systolic song song trên 3 lõi", size=6.8, fill="#334155")
    f.text(b2_x + 10, b2_y + 164, "-> Xuất 8,400 bounding box thô chưa qua lọc", size=7.0, weight=700, fill="#0369A1")

    # Mũi tên 2 -> 3
    arr2_start = b2_x + b2_w
    arr2_end = 680
    f.a(f'<path d="M {arr2_start + 1} 173 L {arr2_end - 2} 173" stroke="#64748B" stroke-width="1.8" fill="none" marker-end="url(#{f.marker("#64748B", 1.8)})"/>')
    rect(f, arr2_start + 3, 154, 22, 12, fill="#FFFFFF", stroke="#CBD5E1", sw=0.7, rx=2)
    f.text(arr2_start + 14, 160, "8.4k", size=6.5, weight=700, fill="#64748B", anchor="middle")

    # -------------------------------------------------------------------------
    # Khối 3: Chặng 3 - Post-processing (CPU)
    # -------------------------------------------------------------------------
    b3_x, b3_y, b3_w, b3_h = 680, 82, 190, 182
    rect(f, b3_x, b3_y, b3_w, b3_h, fill="#FFFFFF", stroke="#A855F7", sw=1.2, rx=4)
    f.text(b3_x + 10, b3_y + 14, "Chặng 3: Post-processing", size=8.5, weight=700, fill="#7E22CE")
    rect(f, b3_x + b3_w - 68, b3_y + 6, 60, 16, fill="#FFFFFF", stroke="#A855F7", sw=0.8, rx=2)
    f.text(b3_x + b3_w - 38, b3_y + 14, "T_post ~3.5 ms", size=7.0, weight=700, fill="#7E22CE", anchor="middle")

    f.text(b3_x + 10, b3_y + 28, "Thực thi: CPU Cortex-A76", size=6.8, fill="#6B21A8")

    # Minh họa thuật toán NMS trực quan: Trước NMS vs Sau NMS
    nms_y = b3_y + 34
    # Panel Trước NMS
    rect(f, b3_x + 8, nms_y, 76, 72, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(b3_x + 46, nms_y + 7, "Trước NMS", size=6.5, weight=700, fill="#475569", anchor="middle")
    # Người thu nhỏ
    p_cx = b3_x + 30
    f.a(f'<circle cx="{p_cx}" cy="{nms_y + 26}" r="3.0" fill="#F59E0B"/>')
    rect(f, p_cx - 3.5, nms_y + 29, 7.0, 10, fill="#0284C7", stroke="none", rx=1)
    rect(f, p_cx - 2.8, nms_y + 39, 2.3, 7, fill="#334155", stroke="none")
    rect(f, p_cx + 0.5, nms_y + 39, 2.3, 7, fill="#334155", stroke="none")
    # 3 Bounding Boxes chồng lấn
    rect(f, p_cx - 10, nms_y + 20, 20, 28, fill="none", stroke="#16A34A", sw=1.2, rx=1)
    rect(f, p_cx - 13, nms_y + 22, 23, 27, fill="none", stroke="#DC2626", sw=0.8, dashed=True, rx=1)
    rect(f, p_cx - 8, nms_y + 18, 19, 30, fill="none", stroke="#DC2626", sw=0.8, dashed=True, rx=1)
    # Nhãn danh sách các box đặt bên phải người trong mini-card
    f.text(b3_x + 46, nms_y + 23, "• 0.88", size=6.5, weight=700, fill="#16A34A")
    f.text(b3_x + 46, nms_y + 35, "• 0.65 ✖", size=6.5, weight=700, fill="#DC2626")
    f.text(b3_x + 46, nms_y + 46, "• 0.42 ✖", size=6.5, weight=700, fill="#DC2626")

    # Mũi tên NMS
    f.a(f'<path d="M {b3_x + 86} {nms_y + 36} L {b3_x + 98} {nms_y + 36}" stroke="#7E22CE" stroke-width="1.4" fill="none" marker-end="url(#{f.marker("#7E22CE", 1.4)})"/>')
    f.text(b3_x + 92, nms_y + 26, "NMS", size=6.5, weight=700, fill="#7E22CE", anchor="middle")
    f.text(b3_x + 92, nms_y + 45, "IoU", size=6.5, fill="#7E22CE", anchor="middle")
    f.text(b3_x + 92, nms_y + 52, "0.45", size=6.5, fill="#7E22CE", anchor="middle")

    # Panel Sau NMS
    rect(f, b3_x + 101, nms_y, 81, 72, fill="#FFFFFF", stroke="#86EFAC", sw=0.9, rx=2)
    f.text(b3_x + 141, nms_y + 7, "Sau NMS", size=6.5, weight=700, fill="#166534", anchor="middle")
    p2_cx = b3_x + 130
    # 1 BBox chuẩn duy nhất (vẽ trước với nền bán trong suốt)
    f.a(f'<rect x="{p2_cx - 11}" y="{nms_y + 20}" width="22" height="31" rx="1" fill="#DCFCE7" fill-opacity="0.35" stroke="#16A34A" stroke-width="1.4"/>')
    # Người thu nhỏ hiển thị rõ nét trên nền
    f.a(f'<circle cx="{p2_cx}" cy="{nms_y + 26}" r="3.0" fill="#F59E0B"/>')
    rect(f, p2_cx - 3.5, nms_y + 29, 7.0, 10, fill="#0284C7", stroke="none", rx=1)
    rect(f, p2_cx - 2.8, nms_y + 39, 2.3, 7, fill="#334155", stroke="none")
    rect(f, p2_cx + 0.5, nms_y + 39, 2.3, 7, fill="#334155", stroke="none")

    # Tag kết quả person gắn đỉnh bbox
    rect(f, p2_cx - 14, nms_y + 11, 36, 8, fill="#16A34A", stroke="none", rx=1)
    f.text(p2_cx + 4, nms_y + 15, "person 0.88", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")

    # Tag helmet gắn trực tiếp cạnh nón bảo hộ kèm đường chỉ dẫn
    f.a(f'<line x1="{p2_cx + 3}" y1="{nms_y + 26}" x2="{p2_cx + 12}" y2="{nms_y + 26}" stroke="#16A34A" stroke-width="0.8"/>')
    rect(f, p2_cx + 12, nms_y + 22, 34, 8, fill="#16A34A", stroke="none", rx=1)
    f.text(p2_cx + 29, nms_y + 26, "helmet 0.92", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")

    # Danh sách thao tác
    f.text(b3_x + 10, b3_y + 120, "• Lọc ngưỡng tin cậy Conf >= 0.25", size=6.8, fill="#334155")
    f.text(b3_x + 10, b3_y + 134, "• NMS triệt tiêu các box trùng lặp", size=6.8, fill="#334155")
    f.text(b3_x + 10, b3_y + 148, "• Ánh xạ tọa độ về ảnh gốc 1080P", size=6.8, fill="#334155")
    f.text(b3_x + 10, b3_y + 164, "-> Đầu ra: Danh sách bbox & nhãn PPE", size=7.0, weight=700, fill="#7E22CE")

    # -------------------------------------------------------------------------
    # PHẦN 2: LATENCY TIMELINE & END-TO-END (NỬA DƯỚI, Y: 284 -> 408)
    # -------------------------------------------------------------------------
    rect(f, 20, 284, W - 40, 126, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(32, 298, "2. DÒNG THỜI GIAN ĐỘ TRỄ TOÀN CHU TRÌNH (END-TO-END TIMELINE - CHẶNG 4) & SO SÁNH HIỆU QUẢ", size=9.2, weight=700, fill=DARK)

    # Biểu đồ thanh ngang phân rã tỉ lệ thời gian
    tl_x = 32
    tl_y = 312
    # Scale: 510 px / 18.5 ms = 27.56 px / ms
    w_pre = 2.5 * 27.56   # 68.9 px
    w_npu = 12.5 * 27.56  # 344.5 px
    w_post = 3.5 * 27.56  # 96.5 px
    tot_w = w_pre + w_npu + w_post  # 510 px

    # Segment 1: T_pre
    rect(f, tl_x, tl_y, w_pre, 30, fill="#FFFFFF", stroke="#F59E0B", sw=1.2, rx=2)
    f.text(tl_x + w_pre / 2, tl_y + 11, "T_pre", size=8.0, weight=700, fill="#B45309", anchor="middle")
    f.text(tl_x + w_pre / 2, tl_y + 22, "2.5 ms (13.5%)", size=7.0, fill="#92400E", anchor="middle")

    # Segment 2: T_npu (Nút thắt)
    rect(f, tl_x + w_pre, tl_y, w_npu, 30, fill="#FFFFFF", stroke="#0284C7", sw=1.5, rx=2)
    f.text(tl_x + w_pre + w_npu / 2, tl_y + 11, "T_npu: 12.5 ms (Pure NPU Suy Luận INT8 - Chiếm 67.5% Thời Gian)", size=8.5, weight=700, fill="#0369A1", anchor="middle")
    f.text(tl_x + w_pre + w_npu / 2, tl_y + 22, "NÚT THẮT TÍNH TOÁN CHÍNH CỦA HỆ THỐNG (BOTTLENECK)", size=7.0, weight=700, fill="#C2410C", anchor="middle")

    # Segment 3: T_post
    rect(f, tl_x + w_pre + w_npu, tl_y, w_post, 30, fill="#FFFFFF", stroke="#A855F7", sw=1.2, rx=2)
    f.text(tl_x + w_pre + w_npu + w_post / 2, tl_y + 11, "T_post", size=8.0, weight=700, fill="#7E22CE", anchor="middle")
    f.text(tl_x + w_pre + w_npu + w_post / 2, tl_y + 22, "3.5 ms (18.9%)", size=7.0, fill="#6B21A8", anchor="middle")

    # Thanh tổng End-to-End
    e2e_y = tl_y + 36
    rect(f, tl_x, e2e_y, tot_w, 24, fill="#F1F5F9", stroke="#64748B", sw=1.5, rx=3)
    f.rich(tl_x + tot_w / 2, e2e_y + 12, [
        ("Chặng 4: T_E2E (End-to-End Latency) = ", "b"),
        ("T_pre + T_npu + T_post = ", "t"),
        ("2.5 + 12.5 + 3.5 = 18.5 ms", "b"),
    ], size=8.5, fill="#1E293B", anchor="middle")

    # 2 Card so sánh chế độ thực thi bên phải
    c1_x = tl_x + tot_w + 14
    c1_w = 160
    c2_x = c1_x + c1_w + 10
    c2_w = (W - 32) - c2_x

    # Card 1: Đơn luồng tuần tự (Sequential)
    rect(f, c1_x, tl_y, c1_w, 88, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=3)
    f.text(c1_x + 8, tl_y + 12, "Tuần tự 1 Luồng (Sequential):", size=7.8, weight=700, fill="#1E293B")
    f.rich(c1_x + 8, tl_y + 26, [("FPS_latency = ", "t"), ("1000 / T_E2E", "b")], size=7.2, fill="#1E293B")
    f.text(c1_x + 8, tl_y + 40, "≈ 54.1 FPS", size=9.5, weight=700, fill="#1E293B")
    f.text(c1_x + 8, tl_y + 54, "• NPU rảnh 6.0 ms (lãng phí 32%)", size=6.5, fill="#475569")
    f.text(c1_x + 8, tl_y + 68, "• 2 lõi NPU bỏ phí hoàn toàn (0%)", size=6.5, fill="#475569")
    f.text(c1_x + 8, tl_y + 80, "• Kém tối ưu khi stream nhiều camera", size=6.5, italic=True, fill="#64748B")

    # Card 2: Đa luồng Pipeline (3 Core)
    rect(f, c2_x, tl_y, c2_w, 88, fill="#FFFFFF", stroke="#94A3B8", sw=1.2, rx=3)
    f.text(c2_x + 8, tl_y + 12, "Pipeline Đa Luồng (3 Core):", size=7.8, weight=700, fill="#1E293B")
    f.rich(c2_x + 8, tl_y + 26, [("Throughput = ", "t"), ("1000 / T_npu", "b")], size=7.2, fill="#1E293B")
    f.text(c2_x + 8, tl_y + 40, "≈ 80.0 FPS (+48%!)", size=9.5, weight=700, fill="#047857")
    f.text(c2_x + 8, tl_y + 54, "• Pre / NPU / Post chạy gối đầu", size=6.5, fill="#334155")
    f.text(c2_x + 8, tl_y + 68, "• Cả 3 lõi NPU full tải (Zero Idle)", size=6.5, fill="#334155")
    f.text(c2_x + 8, tl_y + 80, "• Chuẩn thiết kế cho Edge AI thực tế", size=6.5, weight=700, fill="#1E293B")

    source(f, 418, "Nguồn: Rockchip RKNPU2 Toolkit v2.3.2 Manual; Benchmark thực tế YOLOv8n INT8 640×640 trên Orange Pi 5 RK3588S.")
    return f


def get_thumbnail_b64(rel_path, max_size=(95, 63)):
    """Đọc ảnh từ đường dẫn tương đối của project rk3588, tạo thumbnail và encode base64."""
    root_dir = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
    abs_path = os.path.join(root_dir, rel_path)
    im = Image.open(abs_path)
    im.thumbnail(max_size, Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def fig_fps_latency_vs_throughput():
    """HÌNH 8: Tốc độ khung hình (FPS) - Độ trễ đơn luồng vs Thông lượng đa luồng Pipeline."""
    f = Fig(W, 495)
    tier(f, "T1 RK3588")

    f.text(20, 24, "TỐC ĐỘ KHUNG HÌNH (FPS): ĐỘ TRỄ ĐƠN LUỒNG VS. THÔNG LƯỢNG ĐA LUỒNG PIPELINE", size=13, weight=700, fill=DARK)
    f.text(20, 42, "So sánh cơ chế xử lý tuần tự (Sequential Latency FPS) và cơ chế đường ống gối đầu 3 Core NPU (Pipelined Throughput FPS) trên RK3588S", size=9.2, fill=GRAY)

    # ==============================================================================
    # KỊCH BẢN 1: TUẦN TỰ 1 LUỒNG (SINGLE THREAD)
    # ==============================================================================
    rect(f, 20, 58, W - 40, 140, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(32, 72, "1. KỊCH BẢN A: XỬ LÝ TUẦN TỰ 1 LUỒNG (SEQUENTIAL PROCESSING - 1 THREAD)", size=9.5, weight=700, fill=DARK)

    s = 8.5  # px / ms
    tl_x = 100
    # Trục nhãn
    f.text(tl_x - 8, 90 + 9, "CPU (Pre/Post)", size=8.0, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 114 + 9, "NPU Core 0", size=8.0, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 138 + 9, "NPU Core 1, 2", size=8.0, weight=700, fill="#78909C", anchor="end")

    # Frame 1
    rect(f, tl_x, 90, 2.5 * s, 17, fill="#F5F5F5", stroke="#777777", sw=1.0, rx=2)
    f.text(tl_x + 2.5 * s / 2, 90 + 8.5, "Pre 1", size=7.0, weight=700, fill="#222222", anchor="middle")

    rect(f, tl_x + 2.5 * s, 114, 12.5 * s, 17, fill="white", stroke=BLUE, sw=1.5, rx=2)
    f.text(tl_x + (2.5 + 6.25) * s, 114 + 8.5, "NPU Inference F1 (12.5 ms)", size=7.5, weight=700, fill="#222222", anchor="middle")

    rect(f, tl_x + 15.0 * s, 90, 3.5 * s, 17, fill="#F5F5F5", stroke="#777777", sw=1.0, rx=2)
    f.text(tl_x + (15.0 + 1.75) * s, 90 + 8.5, "Post 1", size=7.0, weight=700, fill="#222222", anchor="middle")

    # NPU Idle 1: 15.0 -> 21.0 (6.0 ms)
    rect(f, tl_x + 15.0 * s, 114, 6.0 * s, 17, fill="#FFEBEE", stroke=RED, sw=0.8, dashed=True, rx=2)
    f.text(tl_x + 18.0 * s, 114 + 8.5, "Idle 6.0ms", size=7.0, weight=700, fill=RED, anchor="middle")

    # Frame 2
    rect(f, tl_x + 18.5 * s, 90, 2.5 * s, 17, fill="#F5F5F5", stroke="#777777", sw=1.0, rx=2)
    f.text(tl_x + (18.5 + 1.25) * s, 90 + 8.5, "Pre 2", size=7.0, weight=700, fill="#222222", anchor="middle")

    rect(f, tl_x + 21.0 * s, 114, 12.5 * s, 17, fill="white", stroke=BLUE, sw=1.5, rx=2)
    f.text(tl_x + (21.0 + 6.25) * s, 114 + 8.5, "NPU Inference F2 (12.5 ms)", size=7.5, weight=700, fill="#222222", anchor="middle")

    rect(f, tl_x + 33.5 * s, 90, 3.5 * s, 17, fill="#F5F5F5", stroke="#777777", sw=1.0, rx=2)
    f.text(tl_x + (33.5 + 1.75) * s, 90 + 8.5, "Post 2", size=7.0, weight=700, fill="#222222", anchor="middle")

    # NPU Idle 2: 33.5 -> 39.5
    rect(f, tl_x + 33.5 * s, 114, 6.0 * s, 17, fill="#FFEBEE", stroke=RED, sw=0.8, dashed=True, rx=2)
    f.text(tl_x + 36.5 * s, 114 + 8.5, "Idle 6.0ms", size=7.0, weight=700, fill=RED, anchor="middle")

    # Frame 3
    rect(f, tl_x + 37.0 * s, 90, 2.5 * s, 17, fill="#F5F5F5", stroke="#777777", sw=1.0, rx=2)
    f.text(tl_x + (37.0 + 1.25) * s, 90 + 8.5, "Pre 3", size=7.0, weight=700, fill="#222222", anchor="middle")

    rect(f, tl_x + 39.5 * s, 114, 12.5 * s, 17, fill="white", stroke=BLUE, sw=1.5, rx=2)
    f.text(tl_x + (39.5 + 6.25) * s, 114 + 8.5, "NPU Inference F3 (12.5 ms)", size=7.5, weight=700, fill="#222222", anchor="middle")

    # Core 1 & 2 idle
    rect(f, tl_x, 138, 52.0 * s, 17, fill="#ECEFF1", stroke="#B0BEC5", sw=0.8, dashed=True, rx=2)
    f.text(tl_x + 26.0 * s, 138 + 8.5, "Core 1 & Core 2 hoàn toàn không sử dụng (0% tải)", size=7.5, fill="#78909C", anchor="middle")

    # Mốc timeline
    f.a(f'<path d="M {tl_x} 163 L {tl_x + 52.0 * s} 163" stroke="#90A4AE" stroke-width="1.0"/>')
    for t_val, t_lbl in [(0, "0ms"), (18.5, "18.5ms (Xong F1)"), (37.0, "37.0ms (Xong F2)"), (52.0, "52.0ms...")]:
        vx = tl_x + t_val * s
        f.a(f'<path d="M {vx} 160 L {vx} 166" stroke="#90A4AE" stroke-width="1.0"/>')
        f.text(vx, 173, t_lbl, size=7.0, fill=DARK, anchor="middle")

    # Panel bên phải Kịch bản 1
    bx1_x = tl_x + 52.0 * s + 16
    bx1_w = (W - 32) - bx1_x
    rect(f, bx1_x, 68, bx1_w, 120, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx1_x + 10, 81, "KẾT QUẢ ĐƠN LUỒNG (1 THREAD):", size=8.5, weight=700, fill=DARK)
    f.rich(bx1_x + 10, 97, [("FPS_latency = ", "b"), ("1000 / T_E2E", "c")], size=8.0, fill=DARK)
    f.rich(bx1_x + 10, 111, [("= 1000 / 18.5 ≈ ", "t"), ("54.1 FPS", "b")], size=8.5, fill=RED)
    f.text(bx1_x + 10, 128, "• NPU rảnh 6.0ms mỗi frame (lãng phí 32.4% thời gian)", size=7.5, fill=DARK)
    f.text(bx1_x + 10, 142, "• Chỉ 1 core chạy, 2 core NPU hoàn toàn bị bỏ phí", size=7.5, fill=DARK)
    f.text(bx1_x + 10, 157, "• Model nặng (DAHD-YOLO 79.1ms): chỉ ~12.6 FPS", size=7.5, weight=700, fill=RED)
    f.text(bx1_x + 18, 169, "-> Không đạt 25 FPS giám sát an toàn!", size=7.0, italic=True, fill=RED)

    # ==============================================================================
    # KỊCH BẢN 2: ĐA LUỒNG PIPELINE (3 CORE NPU)
    # ==============================================================================
    rect(f, 20, 204, W - 40, 252, fill="#FAFAFA", stroke="#CFD8DC", sw=1.2, rx=4)
    f.text(32, 218, "2. KỊCH BẢN B: ĐƯỜNG ỐNG ĐA LUỒNG GỐI ĐẦU 3 CORE NPU (PIPELINED MULTI-THREADING)", size=9.0, weight=700, fill=DARK)

    # Trục nhãn kịch bản B
    f.text(tl_x - 8, 235 + 8, "CPU Pre", size=7.5, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 256 + 8, "NPU Core 0", size=7.5, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 277 + 8, "NPU Core 1", size=7.5, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 298 + 8, "NPU Core 2", size=7.5, weight=700, fill="#222222", anchor="end")
    f.text(tl_x - 8, 319 + 8, "CPU Post", size=7.5, weight=700, fill="#222222", anchor="end")

    # Track CPU Pre
    for i, f_lbl in enumerate(["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "..."]):
        px = tl_x + i * 2.5 * s
        if px + 2.5 * s > tl_x + 52.0 * s:
            break
        rect(f, px, 235, 2.5 * s, 15, fill="#F5F5F5", stroke="#777777", sw=0.8, rx=2)
        f.text(px + 2.5 * s / 2, 235 + 7.5, f_lbl, size=6.5, weight=700, fill="#222222", anchor="middle")

    # Track NPU Core 0
    c0_frames = [(2.5, "F1 (12.5ms)"), (15.0, "F4 (12.5ms)"), (27.5, "F7 (12.5ms)"), (40.0, "F10 (12.5ms)")]
    for start_t, lbl in c0_frames:
        rect(f, tl_x + start_t * s, 256, 12.5 * s, 15, fill="white", stroke=BLUE, sw=1.2, rx=2)
        f.text(tl_x + (start_t + 6.25) * s, 256 + 7.5, lbl, size=6.5, weight=700, fill="#222222", anchor="middle")

    # Track NPU Core 1
    c1_frames = [(5.0, "F2 (12.5ms)"), (17.5, "F5 (12.5ms)"), (30.0, "F8 (12.5ms)")]
    for start_t, lbl in c1_frames:
        rect(f, tl_x + start_t * s, 277, 12.5 * s, 15, fill="white", stroke=BLUE, sw=1.2, rx=2)
        f.text(tl_x + (start_t + 6.25) * s, 277 + 7.5, lbl, size=6.5, weight=700, fill="#222222", anchor="middle")

    # Track NPU Core 2
    c2_frames = [(7.5, "F3 (12.5ms)"), (20.0, "F6 (12.5ms)"), (32.5, "F9 (12.5ms)")]
    for start_t, lbl in c2_frames:
        rect(f, tl_x + start_t * s, 298, 12.5 * s, 15, fill="white", stroke=BLUE, sw=1.2, rx=2)
        f.text(tl_x + (start_t + 6.25) * s, 298 + 7.5, lbl, size=6.5, weight=700, fill="#222222", anchor="middle")

    # Track CPU Post
    post_frames = [(15.0, "F1"), (17.5, "F2"), (20.0, "F3"), (27.5, "F4"), (30.0, "F5"), (32.5, "F6"), (40.0, "F7")]
    for start_t, lbl in post_frames:
        rect(f, tl_x + start_t * s, 319, 2.5 * s, 15, fill="#F5F5F5", stroke="#777777", sw=0.8, rx=2)
        f.text(tl_x + (start_t + 1.25) * s, 319 + 7.5, lbl, size=6.5, weight=700, fill="#222222", anchor="middle")

    # Mốc thời gian hoàn thành (Output completion ticks)
    f.a(f'<path d="M {tl_x} 345 L {tl_x + 52.0 * s} 345" stroke="#90A4AE" stroke-width="1.0"/>')
    out_ticks = [(18.5, "Xong F1 (18.5ms)", 0), (21.0, "F2 (21ms)", 8), (23.5, "F3 (23.5ms)", 0), (31.0, "F4", 0), (33.5, "F5", 8)]
    for t_val, t_lbl, y_shift in out_ticks:
        vx = tl_x + t_val * s
        f.a(f'<path d="M {vx} 341 L {vx} 347" stroke="#546E7A" stroke-width="1.2"/>')
        f.text(vx, 353 + y_shift, t_lbl, size=6.5, weight=700, fill=DARK, anchor="middle")

    # Ghi chú dưới timeline
    rect(f, tl_x, 368, 52.0 * s, 24, fill="#FFFFFF", stroke="#B0BEC5", sw=0.8, rx=3)
    f.text(tl_x + 52.0 * s / 2, 380, "✓ Cả 3 Core NPU hoạt động 100% liên tục | Triệt tiêu khe rảnh (Zero Idle) | Nhả frame dồn dập", size=7.5, weight=700, fill=DARK, anchor="middle")

    # Hộp 1 bên phải Kịch bản B: Throughput & DAHD-YOLO
    bx2_x = tl_x + 52.0 * s + 16
    bx2_w = (W - 32) - bx2_x
    rect(f, bx2_x, 214, bx2_w, 102, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx2_x + 10, 226, "KẾT QUẢ ĐA LUỒNG PIPELINE (3 CORE):", size=8.5, weight=700, fill=DARK)
    f.rich(bx2_x + 10, 241, [("Throughput FPS = ", "b"), ("1000 / T_bottleneck", "c")], size=8.0, fill=DARK)
    f.rich(bx2_x + 10, 255, [("Với 1 core: 1000/12.5 = ", "t"), ("80.0 FPS", "b"), (" (Tăng 1.48×)", "t")], size=8.0, fill="#2E7D32")
    f.text(bx2_x + 10, 271, "• Bằng chứng paper DAHD-YOLO (Table 6, tr.18):", size=7.5, weight=700, fill=DARK)
    f.text(bx2_x + 18, 283, "- Đơn luồng: 79.1ms (12.6 FPS) -> Không đủ 25 FPS", size=7.0, fill=DARK)
    f.text(bx2_x + 18, 296, "- Thread pool 3 core NPU: Đạt 50.2 FPS (720P) / 43.8 FPS (1080P)", size=7.0, weight=700, fill="#1B5E20")
    f.text(bx2_x + 18, 308, "-> Tăng gấp gần 4 lần, đáp ứng hoàn hảo real-time!", size=7.0, italic=True, fill=DARK)

    # Hộp 2 bên phải Kịch bản B: Minh họa ảnh PPE thực tế
    p1 = "data/demo/images/construction-safety.jpg"
    p2 = "data/demo/outputs/images/2026-09-17_sfchd_yolov8n_baseline_100ep/pt_fp32/predict/construction-safety.jpg"
    b64_1 = get_thumbnail_b64(p1, (95, 63))
    b64_2 = get_thumbnail_b64(p2, (95, 63))

    bx3_y = 322
    bx3_h = 126
    rect(f, bx2_x, bx3_y, bx2_w, bx3_h, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx2_x + 10, bx3_y + 12, "DỮ LIỆU PPE THỰC NGHIỆM TRÊN ORANGE PI 5:", size=8.0, weight=700, fill=DARK)

    # Ảnh 1 (thô)
    im1_x = bx2_x + 12
    im1_y = bx3_y + 22
    f.a(f'<image href="data:image/jpeg;base64,{b64_1}" x="{im1_x}" y="{im1_y}" width="95" height="63" preserveAspectRatio="xMidYMid slice"/>')
    rect(f, im1_x, im1_y, 95, 63, fill="none", stroke="#B0BEC5", sw=0.8, rx=2)
    f.text(im1_x + 95 / 2, im1_y + 72, "Ảnh thô Camera 1080P", size=6.5, fill=GRAY, anchor="middle")

    # Mũi tên
    arr_x1 = im1_x + 98
    arr_x2 = arr_x1 + 18
    f.a(f'<path d="M {arr_x1} {im1_y + 31} L {arr_x2} {im1_y + 31}" stroke="{GREEN}" stroke-width="1.5" fill="none" marker-end="url(#{f.marker(GREEN, 1.6)})"/>')

    # Ảnh 2 (detect PPE)
    im2_x = arr_x2 + 4
    f.a(f'<image href="data:image/jpeg;base64,{b64_2}" x="{im2_x}" y="{im1_y}" width="95" height="63" preserveAspectRatio="xMidYMid slice"/>')
    rect(f, im2_x, im1_y, 95, 63, fill="none", stroke="#4CAF50", sw=1.0, rx=2)
    f.text(im2_x + 95 / 2, im1_y + 72, "Nhận diện PPE (5 classes)", size=6.5, weight=700, fill="#2E7D32", anchor="middle")

    f.text(bx2_x + 10, bx3_y + 104, "• Phân loại: person, helmet, safety_clothes, self_clothes, head", size=6.8, fill=DARK)
    f.text(bx2_x + 10, bx3_y + 116, "• Pipeline đa luồng đảm bảo kiểm soát an toàn không trễ khung hình", size=6.8, italic=True, fill=DARK)

    source(f, 460, "Nguồn: Rockchip RKNPU2 Toolkit v2.3.2 Manual; DAHD-YOLO (Table 6, tr.18 - RK3588 NPU 3-Core Thread Pool); Dữ liệu thực nghiệm PPE.")
    return f


def main():
    figs = [
        ("hm-1-iou-ban-chat-hinh-hoc", fig_iou_geometry),
        ("hm-precision-do-chuan-xac", fig_precision),
        ("hm-recall-do-nhay-bao-phu", fig_recall),
        ("hm-f1-score-trung-binh-dieu-hoa", fig_f1_score),
        ("hm-2-co-che-duong-cong-pr-va-ap", fig_pr_curve_and_ap),
        ("hm-3a-map-co-che-trung-binh-cac-lop", fig_map_classes),
        ("hm-3b-map50-vs-map50-95-so-sanh", fig_map50_vs_95),
        ("hm-4-delta-map-luong-tu-hoa", fig_delta_map_quantization),
        ("hm-5-parameters-params-mo-hinh", fig_parameters),
        ("hm-6-activations-vs-parameters", fig_activations_memory),
        ("hm-7-latency-4-chang-end-to-end", fig_latency_4_stages),
        ("hm-8-fps-latency-vs-throughput", fig_fps_latency_vs_throughput),
    ]
    run(figs, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()



