#!/usr/bin/env python3
"""Ghi chú chuyên đề: Các chỉ số đánh giá mô hình phát hiện vật thể (06-chi-so-danh-gia).

Sinh 3 hình chất lượng cao chuẩn visual_guide:
  - hm-1-iou-va-phan-loai-du-doan (T2 chung): Bản chất hình học IoU và phân loại kết quả (TP, FP, FN)
  - hm-2-co-che-duong-cong-pr-va-ap (T2 chung): Trượt Confidence Threshold, Đồ thị P-R Curve và Cách tính AP, mAP
  - hm-3-map50-95-va-phan-tich-5-lop-ppe (T2 chung): Bản chất 10 mốc IoU mAP50-95, Biểu đồ 5 lớp PPE và Độ nhạy IoU của vật thể nhỏ

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: 06-chi-so-danh-gia -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GREEN, INK, RED, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"      # Nền khối tính toán / số học
ORANGE = "#E65100"
PURPLE = "#7B1FA2"
TEAL = "#00796B"
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
# HÌNH 1: BẢN CHẤT HÌNH HỌC IOU VÀ PHÂN LOẠI KẾT QUẢ
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


def fig_iou_classification():
    f = Fig(W, 580)
    tier(f, "T2 chung")
    f.text(10, 24, "Chỉ số IoU và Phân loại Kết quả Dự đoán (TP, FP, FN)", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: BẢN CHẤT HÌNH HỌC CỦA IOU ----
    f.text(10, 56, "A. Bản chất hình học của IoU (Intersection over Union)", size=13.5, weight=700, fill=DARK)

    f.a(f'<line x1="20" y1="80" x2="45" y2="80" stroke="{ORANGE}" stroke-width="2.2" stroke-dasharray="6 3"/>')
    f.text(52, 80, "Nhãn thực tế (Ground Truth B_gt)", size=11.5, weight=600, fill=DARK)

    f.a(f'<line x1="280" y1="80" x2="305" y2="80" stroke="{BLUE}" stroke-width="2.2"/>')
    f.text(312, 80, "Dự đoán mô hình (Prediction B_p)", size=11.5, weight=600, fill=DARK)

    rect(f, 540, 72, 18, 16, fill="#C8E6C9", stroke="none")
    f.text(566, 80, "Phần giao nhau (Intersection ∩)", size=11.5, weight=600, fill=DARK)

    draw_bbox_case(f, 10, 96, 275, 175, p_off_x=6, p_off_y=6,
                   title="1. Trùng khít cao (Rất tốt)", iou_val=0.88,
                   status_text="Đạt chuẩn mọi mốc IoU", status_color=GREEN)

    draw_bbox_case(f, 310, 96, 275, 175, p_off_x=28, p_off_y=24,
                   title="2. Trùng khớp vừa (Ngưỡng cơ bản)", iou_val=0.52,
                   status_text="Đạt mAP50, trượt mAP75 trở lên", status_color=ORANGE)

    draw_bbox_case(f, 610, 96, 275, 175, p_off_x=55, p_off_y=24,
                   title="3. Lệch vị trí (Trượt ngưỡng)", iou_val=0.16,
                   status_text="Phán đoán sai vị trí (FP)", status_color=RED)

    # Khung công thức IoU
    y_f = 280
    rect(f, 10, y_f, W - 20, 36, fill=CALC, stroke="#90CAF9", sw=1.2, rx=4)
    txt(f, 20, y_f + 11, [
        [("Công thức tính IoU: ", "b"),
         ("IoU = Diện tích vùng giao (B_p ∩ B_gt) / Diện tích vùng hợp (B_p ∪ B_gt)", "b"),
         ("  |  Miền giá trị: [0.0 (không chạm) đến 1.0 (trùng khít hoàn toàn)]", "t")],
    ], size=11.5, dy=16)

    # ---- PHẦN B: BẢNG PHÂN LOẠI DỰ ĐOÁN ----
    y_b = y_f + 48
    f.text(10, y_b, "B. Phân loại kết quả dự đoán (TP, FP, FN) trong bài toán đồ bảo hộ lao động", size=13.5, weight=700, fill=DARK)

    y_tab = f.table(10, y_b + 12, [130, 160, 290, 300], ["Ký hiệu", "Tên gọi", "Tình huống thực tế trên ảnh", "Ý nghĩa trong giám sát an toàn"], [
        ["True Positive (TP)", "Dương tính thật (Đúng)", "Dự đoán có mũ bảo hộ và IoU ≥ ngưỡng quy định", "Phát hiện chính xác trang bị bảo hộ."],
        ["False Positive (FP)", "Báo động giả (Đoán nhầm)", "Dự đoán có mũ nhưng thực tế không có, hoặc IoU < ngưỡng", "Gây phiền toái vì báo sai người không vi phạm."],
        ["False Negative (FN)", "Bỏ sót vi phạm", "Thực tế có người/mũ nhưng mô hình không tạo ra hộp nào", "Cực kỳ nguy hiểm: để lọt vi phạm an toàn công trường."],
    ], size=11.5, line_h=15)

    # Khung công thức Precision & Recall
    y_pr = y_tab + 12
    rect(f, 10, y_pr, W - 20, 36, fill="#FFF3E0", stroke="#FFB74D", sw=1.2, rx=4)
    txt(f, 20, y_pr + 11, [
        [("Precision (Độ chuẩn xác): ", "b"), ("P = TP / (TP + FP)", "b"), (" (Trong các hộp báo có mũ, bao nhiêu % là đúng?)", "t"),
         ("  |  ", "t"),
         ("Recall (Độ bao phủ): ", "b"), ("R = TP / (TP + FN)", "b"), (" (Bắt được bao nhiêu % tổng số mũ ngoài thực tế?)", "t")],
    ], size=11.5, dy=16)

    source(f, y_pr + 42, "Nguồn: REPO ai/automation/leaderboards/sfchd_5class.csv; tmp/02_decisions/2026-10-11_model-selection-rule.md.")
    return f


# ==============================================================================
# HÌNH 2: CƠ CHẾ ĐƯỜNG CONG P-R, AVERAGE PRECISION VÀ MAP
# ==============================================================================
def fig_pr_curve_and_ap():
    f = Fig(W, 640)
    tier(f, "T2 chung")
    f.text(10, 24, "Cơ chế Đường cong Precision-Recall (P-R Curve), Average Precision và mAP", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: THANH TRƯỢT CONFIDENCE THRESHOLD ----
    f.text(10, 56, "A. Sự đánh đổi giữa Precision và Recall khi trượt ngưỡng tin cậy (Confidence Threshold)", size=13.5, weight=700, fill=DARK)

    sw_w = 275
    sw_h = 100
    y_sw = 72

    # Mức 1: High Confidence
    rect(f, 10, y_sw, sw_w, sw_h, fill="#E3F2FD", stroke=BLUE, sw=1.5, rx=5)
    f.text(10 + sw_w / 2, y_sw + 16, "Ngưỡng cao: Confidence ≥ 0.90", size=11.5, weight=700, fill=BLUE, anchor="middle")
    txt(f, 20, y_sw + 36, [
        [("• Chỉ giữ lại các hộp cực kỳ chắc chắn", "t")],
        [("• Precision rất cao (~0.98): ", "b"), ("Hầu như không báo nhầm", "t")],
        [("• Recall rất thấp (~0.30): ", "b"), ("Bỏ sót hầu hết vật thể che khuất", "t")],
    ], size=11, dy=18)

    # Mức 2: Balanced
    rect(f, 310, y_sw, sw_w, sw_h, fill="#E8F5E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(310 + sw_w / 2, y_sw + 16, "Ngưỡng chuẩn: Confidence ≈ 0.50", size=11.5, weight=700, fill=GREEN, anchor="middle")
    txt(f, 320, y_sw + 36, [
        [("• Cân bằng tối ưu giữa phát hiện và báo nhầm", "t")],
        [("• Precision cao (~0.90): ", "b"), ("Báo sai dưới 10%", "t")],
        [("• Recall cao (~0.84): ", "b"), ("Bắt được 84% vật thể thực tế", "t")],
    ], size=11, dy=18)

    # Mức 3: Low Confidence
    rect(f, 610, y_sw, sw_w, sw_h, fill="#FFF8E1", stroke=ORANGE, sw=1.5, rx=5)
    f.text(610 + sw_w / 2, y_sw + 16, "Ngưỡng thấp: Confidence ≤ 0.10", size=11.5, weight=700, fill=ORANGE, anchor="middle")
    txt(f, 620, y_sw + 36, [
        [("• Giữ lại toàn bộ các vết nghi ngờ", "t")],
        [("• Recall tối đa (~0.95): ", "b"), ("Bắt gần như toàn bộ vật thể", "t")],
        [("• Precision sụt dốc (~0.35): ", "b"), ("Rất nhiều báo động giả (FP)", "t")],
    ], size=11, dy=18)

    # ---- PHẦN B: ĐỒ THỊ P-R CURVE VÀ DIỆN TÍCH AP ----
    y_b = y_sw + sw_h + 18
    f.text(10, y_b, "B. Đồ thị P-R Curve và Diện tích dưới đường cong (Area Under Curve - AUC = AP)", size=13.5, weight=700, fill=DARK)

    # Vẽ hệ trục tọa độ P-R
    gx, gy = 50, y_b + 30
    gw, gh = 420, 200

    # Trục tọa độ
    f.a(f'<line x1="{gx}" y1="{gy+gh}" x2="{gx+gw}" y2="{gy+gh}" stroke="{DARK}" stroke-width="1.8"/>')
    f.a(f'<line x1="{gx}" y1="{gy}" x2="{gx}" y2="{gy+gh}" stroke="{DARK}" stroke-width="1.8"/>')

    # Lưới toạ độ
    for i in range(1, 5):
        lx = gx + i * (gw / 4)
        ly = gy + gh - i * (gh / 4)
        f.a(f'<line x1="{lx}" y1="{gy}" x2="{lx}" y2="{gy+gh}" stroke="#E0E0E0" stroke-width="1.0" stroke-dasharray="3 3"/>')
        f.a(f'<line x1="{gx}" y1="{ly}" x2="{gx+gw}" y2="{ly}" stroke="#E0E0E0" stroke-width="1.0" stroke-dasharray="3 3"/>')
        f.text(lx, gy + gh + 14, f"{i*0.25:.2f}", size=10, fill="#666666", anchor="middle")
        f.text(gx - 8, ly, f"{i*0.25:.2f}", size=10, fill="#666666", anchor="end")

    f.text(gx - 8, gy + gh, "0", size=10, fill="#666666", anchor="end")
    f.text(gx + gw + 10, gy + gh + 4, "Recall (R)", size=11.5, weight=700, fill=DARK, anchor="start")
    f.text(gx - 8, gy - 12, "Precision (P)", size=11.5, weight=700, fill=DARK, anchor="middle")

    # Đường cong P-R và vùng tô màu AUC
    # Tọa độ các điểm nội suy cong chuẩn
    pts = [
        (0.00, 0.98), (0.20, 0.97), (0.40, 0.96), (0.60, 0.94),
        (0.75, 0.92), (0.84, 0.89), (0.90, 0.70), (0.94, 0.35), (0.97, 0.10)
    ]
    svg_pts = [(gx + r * gw, gy + gh - p * gh) for r, p in pts]

    # Tô màu diện tích AP
    path_d = f"M {svg_pts[0][0]} {svg_pts[0][1]} " + " ".join(f"L {x} {y}" for x, y in svg_pts) + f" L {svg_pts[-1][0]} {gy+gh} L {svg_pts[0][0]} {gy+gh} Z"
    f.a(f'<path d="{path_d}" fill="#C8E6C9" opacity="0.6"/>')

    # Vẽ đường viền P-R đậm
    curve_d = f"M {svg_pts[0][0]} {svg_pts[0][1]} " + " ".join(f"L {x} {y}" for x, y in svg_pts)
    f.a(f'<path d="{curve_d}" fill="none" stroke="{BLUE}" stroke-width="3.0"/>')

    # Chấm các điểm mốc trên đường cong
    p_high = svg_pts[1]
    p_opt = svg_pts[5]
    p_low = svg_pts[7]
    for px, py, col, lbl, off_y in [
        (p_high[0], p_high[1], BLUE, "Conf=0.9", 14),
        (p_opt[0], p_opt[1], GREEN, "Conf=0.5 (Tối ưu)", -8),
        (p_low[0], p_low[1], ORANGE, "Conf=0.1", -8),
    ]:
        f.a(f'<circle cx="{px}" cy="{py}" r="4.5" fill="{col}" stroke="white" stroke-width="1.5"/>')
        f.text(px + 6, py + off_y, lbl, size=10, weight=700, fill=col)

    # Chữ ghi diện tích AP
    f.text(gx + gw * 0.45, gy + gh * 0.55, "Diện tích AP = ∫ P(R) dR", size=13, weight=700, fill=GREEN, anchor="middle")
    f.text(gx + gw * 0.45, gy + gh * 0.55 + 18, "(Chất lượng toàn diện của 1 lớp đối tượng)", size=10.5, weight=600, fill="#2E7D32", anchor="middle")

    # Khung giải thích bên phải đồ thị
    rx = 520
    rect(f, rx, gy, 370, gh, fill="#FAFAFA", stroke="#CFD8DC", sw=1.2, rx=5)
    f.text(rx + 15, gy + 20, "Ý nghĩa của Average Precision (AP):", size=12, weight=700, fill=DARK)
    txt(f, rx + 15, gy + 42, [
        [("• Đường cong P-R càng phồng về góc trên bên phải,", "t")],
        [("  mô hình càng đạt cả Precision cao lẫn Recall cao.", "t")],
        [("• Diện tích AP nhận giá trị từ 0.0 đến 1.0 (hoàn hảo).", "b")],
        [("• Nếu chỉ nhìn Precision hoặc Recall đơn lẻ ở một", "t")],
        [("  ngưỡng, ta sẽ bị đánh lừa bởi hành vi thiên lệch.", "t")],
        [("• AP là thước đo tích phân bao quát toàn bộ dải", "b")],
        [("  ngưỡng tin cậy từ khắt khe đến lỏng lẻo.", "b")],
    ], size=11, dy=18)

    # ---- PHẦN C: CƠ CHẾ GOM TRUNG BÌNH MAP GIỮA CÁC LỚP ----
    y_c = gy + gh + 26
    f.text(10, y_c, "C. Từ AP từng lớp đối tượng đến mAP (Mean Average Precision)", size=13.5, weight=700, fill=DARK)

    # Vẽ 5 thẻ AP lớp đối tượng
    classes = [
        ("person", "AP_1 = 0.7186", BLUE),
        ("safety_clothes", "AP_2 = 0.6494", TEAL),
        ("helmet", "AP_3 = 0.6210", GREEN),
        ("self_clothes", "AP_4 = 0.5764", PURPLE),
        ("head", "AP_5 = 0.3884", RED),
    ]

    c_box_w = 115
    c_box_h = 50
    y_cb = y_c + 14

    for i, (cname, cap, col) in enumerate(classes):
        cx = 10 + i * (c_box_w + 10)
        rect(f, cx, y_cb, c_box_w, c_box_h, fill="#FFFFFF", stroke=col, sw=1.5, rx=4)
        f.text(cx + c_box_w / 2, y_cb + 16, cname, size=11, weight=700, fill=col, anchor="middle")
        f.text(cx + c_box_w / 2, y_cb + 34, cap, size=10, weight=600, fill=DARK, anchor="middle")

    # Mũi tên gom về mAP
    f.a(f'<polygon points="635,{y_cb+25} 650,{y_cb+25} 646,{y_cb+20} 655,{y_cb+25} 646,{y_cb+30} 650,{y_cb+25}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # Khung tính mAP
    rect(f, 665, y_cb - 5, 225, c_box_h + 10, fill=CALC, stroke="#90CAF9", sw=1.5, rx=5)
    f.text(665 + 225 / 2, y_cb + 16, "mAP (Mean AP)", size=12.5, weight=700, fill=BLUE, anchor="middle")
    f.text(665 + 225 / 2, y_cb + 36, "mAP = (1/C) * Σ AP_c = 0.5908", size=11.5, weight=700, fill=DARK, anchor="middle")

    source(f, y_cb + c_box_h + 18, "Nguồn: REPO ai/automation/leaderboards/sfchd_5class.csv; Y6 tr.8.")
    return f


# ==============================================================================
# HÌNH 3: BẢN CHẤT MAP50-95 VÀ PHÂN TÍCH 5 LỚP PPE
# ==============================================================================
def fig_map50_95_and_classes():
    f = Fig(W, 660)
    tier(f, "T2 chung")
    f.text(10, 24, "Bản chất Khắt khe của mAP50-95, Biểu đồ 5 Lớp PPE và Độ nhạy IoU của Vật thể nhỏ", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: CƠ CHẾ CO RÚT CỦA ĐƯỜNG CONG P-R QUA 10 MỐC IOU ----
    f.text(10, 56, "A. Tại sao mAP50-95 lại khắt khe hơn nhiều so với mAP50? (Sự co rút diện tích AP qua 10 mốc IoU)", size=13.5, weight=700, fill=DARK)

    # Vẽ 2 đồ thị so sánh trực quan mAP50 vs mAP95
    gw_s = 250
    gh_s = 130

    # Đồ thị 1: IoU = 0.50 (Dễ)
    gx1, gy1 = 50, 85
    f.a(f'<line x1="{gx1}" y1="{gy1+gh_s}" x2="{gx1+gw_s}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.5"/>')
    f.a(f'<line x1="{gx1}" y1="{gy1}" x2="{gx1}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.5"/>')
    # Đường cong phồng to
    f.a(f'<path d="M {gx1} {gy1+5} C {gx1+160} {gy1+10}, {gx1+210} {gy1+30}, {gx1+gw_s-10} {gy1+gh_s} L {gx1+gw_s-10} {gy1+gh_s} L {gx1} {gy1+gh_s} Z" fill="#C8E6C9" opacity="0.6"/>')
    f.a(f'<path d="M {gx1} {gy1+5} C {gx1+160} {gy1+10}, {gx1+210} {gy1+30}, {gx1+gw_s-10} {gy1+gh_s}" fill="none" stroke="{GREEN}" stroke-width="2.5"/>')
    f.text(gx1 + gw_s / 2, gy1 - 10, "Mốc IoU = 0.50 (Dễ dãi)", size=11, weight=700, fill=GREEN, anchor="middle")
    f.text(gx1 + gw_s * 0.45, gy1 + gh_s * 0.55, "AP@0.50 = 0.8924", size=13, weight=700, fill=DARK, anchor="middle")
    f.text(gx1 + gw_s / 2, gy1 + gh_s + 15, "Box chỉ cần chạm 50% diện tích nhãn", size=10, fill="#555555", anchor="middle")

    # Mũi tên siết ngưỡng
    f.a(f'<polygon points="325,{gy1+65} 345,{gy1+65} 340,{gy1+60} 350,{gy1+65} 340,{gy1+70} 345,{gy1+65}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')
    f.text(338, gy1 + 50, "Siết IoU", size=10, weight=700, fill=RED, anchor="middle")
    f.text(338, gy1 + 82, "0.50 -> 0.95", size=9.5, fill="#666666", anchor="middle")

    # Đồ thị 2: IoU = 0.95 (Cực kỳ khắt khe)
    gx2 = 370
    f.a(f'<line x1="{gx2}" y1="{gy1+gh_s}" x2="{gx2+gw_s}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.5"/>')
    f.a(f'<line x1="{gx2}" y1="{gy1}" x2="{gx2}" y2="{gy1+gh_s}" stroke="{DARK}" stroke-width="1.5"/>')
    # Đường cong co cụm lại
    f.a(f'<path d="M {gx2} {gy1+40} C {gx2+50} {gy1+70}, {gx2+80} {gy1+105}, {gx2+110} {gy1+gh_s} L {gx2+110} {gy1+gh_s} L {gx2} {gy1+gh_s} Z" fill="#FFCDD2" opacity="0.6"/>')
    f.a(f'<path d="M {gx2} {gy1+40} C {gx2+50} {gy1+70}, {gx2+80} {gy1+105}, {gx2+110} {gy1+gh_s}" fill="none" stroke="{RED}" stroke-width="2.5"/>')
    f.text(gx2 + gw_s / 2, gy1 - 10, "Mốc IoU = 0.95 (Khắt khe)", size=11, weight=700, fill=RED, anchor="middle")
    f.text(gx2 + 160, gy1 + 55, "AP@0.95 < 0.15", size=12, weight=700, fill=RED, anchor="middle")
    f.text(gx2 + gw_s / 2, gy1 + gh_s + 15, "Lệch nhẹ 1 vài pixel lập tức bị coi là FP", size=10, fill="#555555", anchor="middle")

    # Khung công thức trung bình 10 mốc bên phải
    rx = 645
    rect(f, rx, gy1, 245, gh_s, fill=CALC, stroke="#90CAF9", sw=1.2, rx=5)
    f.text(rx + 12, gy1 + 18, "Chuẩn COCO mAP50-95:", size=11.5, weight=700, fill=BLUE)
    txt(f, rx + 12, gy1 + 36, [
        [("• Lấy trung bình cộng tại 10 mốc:", "t")],
        [("  0.50, 0.55, 0.60, 0.65, 0.70,", "t")],
        [("  0.75, 0.80, 0.85, 0.90, 0.95", "t")],
        [("• mAP50: ", "b"), ("0.8924 (Rất cao)", "t")],
        [("• mAP50-95: ", "b"), ("0.5908 (Thực tế)", "b")],
    ], size=10.5, dy=16)

    # ---- PHẦN B: BIỂU ĐỒ THANH NGANG 5 LỚP BẢO HỘ LAO ĐỘNG ----
    y_b = gy1 + gh_s + 38
    f.text(10, y_b, "B. Biểu đồ mAP50-95 của 5 lớp đồ bảo hộ lao động (YOLOv8n baseline trên sfchd_5class)", size=13.5, weight=700, fill=DARK)

    # Vẽ Bar Chart ngang
    y_bar = y_b + 14
    bar_data = [
        ("person (người)", 0.7186, "71.86%", BLUE),
        ("safety_clothes (áo phản quang)", 0.6494, "64.94%", TEAL),
        ("helmet (mũ bảo hộ)", 0.6210, "62.10%", GREEN),
        ("self_clothes (quần áo thường)", 0.5764, "57.64%", PURPLE),
        ("head (đầu trần / không mũ)", 0.3884, "38.84%", RED),
    ]

    max_bar_w = 460
    for i, (cname, val, pct, col) in enumerate(bar_data):
        by = y_bar + i * 26
        # Tên nhãn
        f.text(190, by + 12, cname, size=11, weight=600, fill=DARK, anchor="end")
        # Nền thanh
        rect(f, 200, by, max_bar_w, 18, fill="#F0F0F0", stroke="none", rx=3)
        # Thanh giá trị
        bw = val * max_bar_w
        rect(f, 200, by, bw, 18, fill=col, stroke="none", rx=3)
        # Giá trị hiển thị
        f.text(205 + bw, by + 10, f"{val:.4f} ({pct})", size=10.5, weight=700, fill=col)

    # Đường mốc mAP trung bình
    mean_val = 0.5908
    mean_x = 200 + mean_val * max_bar_w
    f.a(f'<line x1="{mean_x}" y1="{y_bar-4}" x2="{mean_x}" y2="{y_bar+5*26}" stroke="{DARK}" stroke-width="1.8" stroke-dasharray="4 3"/>')
    f.text(mean_x, y_bar + 5 * 26 + 12, f"Trung bình mAP = {mean_val:.4f}", size=10, weight=700, fill=DARK, anchor="middle")

    # ---- PHẦN C: LÝ GIẢI HÌNH HỌC ĐỘ NHẠY IOU CỦA VẬT THỂ NHỎ ----
    y_c = y_bar + 5 * 26 + 28
    f.text(10, y_c, "C. Lý giải hình học: Tại sao vật thể nhỏ (head) lại có điểm mAP50-95 thấp nhất?", size=13.5, weight=700, fill=DARK)

    geom_h = 95
    y_g = y_c + 12

    # Case 1: Vật thể lớn (person)
    rect(f, 10, y_g, 430, geom_h, fill="#F0F7FF", stroke=BLUE, sw=1.2, rx=5)
    f.text(20, y_g + 16, "1. Vật thể lớn: person (Ví dụ hộp 200 x 400 px)", size=11.5, weight=700, fill=BLUE)
    txt(f, 20, y_g + 34, [
        [("• Khi mô hình dự đoán bị lệch 10 pixel: ", "b")],
        [("  Diện tích hộp rất lớn (80,000 px), độ lệch 10 px chỉ làm mất ~5% diện tích giao.", "t")],
        [("• Kết quả: ", "b"), ("IoU vẫn đạt > 0.90", "b"), (" -> Vượt qua cả các mốc khắt khe (0.80 - 0.90)!", "t")],
    ], size=10.5, dy=16)

    # Case 2: Vật thể nhỏ (head)
    rect(f, 460, y_g, 430, geom_h, fill="#FFEBEE", stroke=RED, sw=1.2, rx=5)
    f.text(470, y_g + 16, "2. Vật thể nhỏ: head (Ví dụ hộp 30 x 30 px)", size=11.5, weight=700, fill=RED)
    txt(f, 470, y_g + 34, [
        [("• Khi mô hình dự đoán bị lệch 10 pixel: ", "b")],
        [("  Diện tích hộp rất nhỏ (900 px), độ lệch 10 px làm mất hơn 1/3 diện tích giao.", "t")],
        [("• Kết quả: ", "b"), ("IoU tụt xuống dưới 0.50", "b"), (" -> Bị loại khỏi hầu hết 10 mốc tính điểm!", "t")],
    ], size=10.5, dy=16)

    source(f, y_g + geom_h + 8, "Nguồn: REPO ai/automation/leaderboards/sfchd_5class.csv:2; Y6 tr.8; QYOLO tr.2.")
    return f


def main():
    figs = [
        ("hm-1-iou-va-phan-loai-du-doan", fig_iou_classification),
        ("hm-2-co-che-duong-cong-pr-va-ap", fig_pr_curve_and_ap),
        ("hm-3-map50-95-va-phan-tich-5-lop-ppe", fig_map50_95_and_classes),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()
