#!/usr/bin/env python3
"""Chuyên đề: Tensor và kiểu dữ liệu (tensor-va-kieu-du-lieu.rst).

Sinh các hình minh họa chuẩn visual_guide:
  - tk-1-tien-hoa-tensor-tu-0d-den-4d (T2 chung):
    Tiến hóa của tensor từ Scalar đến Tensor 4D (0D đến 4D).
  - tk-2-co-che-cat-lat-va-chi-so-hoa-tensor (T2 chung):
    Cơ chế cắt lát (Slicing) và lập chỉ mục đa trục trên tensor.
  - tk-3-bo-cuc-bo-nho-nchw-va-nhwc (T2 chung):
    Bố cục bộ nhớ Tensor NCHW (planar) vs NHWC (channels-last).
  - tk-4-cau-truc-bit-va-kieu-du-lieu (T2 chung):
    Cấu trúc phân bổ bit và đánh đổi kiểu dữ liệu FP32, FP16, BF16, INT8.
  - tk-5-ban-chat-channel-rgb-va-feature-map (T2 chung):
    Bản chất của Channel: Từ Kênh màu RGB đầu vào đến Kênh đặc trưng (Feature Map).

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "tensor-va-kieu-du-lieu"
    )
)

W = 900


def tier(f, label):
    f.tier(W - 130, 10, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def draw_perspective_slice(f, x, y, w, h, label="", fill="#E3F2FD", stroke=BLUE, dx=14, dy=10):
    """Vẽ một mặt phẳng 2D ở góc chiếu nghiêng (axonometric/perspective)."""
    pts = [
        f"{x},{y + dy}",
        f"{x + dx},{y}",
        f"{x + w + dx},{y}",
        f"{x + w + dx},{y + h}",
        f"{x + w},{y + h + dy}",
        f"{x},{y + h + dy}",
    ]
    f.a(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.1"/>')
    f.a(f'<line x1="{x + w}" y1="{y + dy}" x2="{x + w + dx}" y2="{y}" stroke="{stroke}" stroke-width="0.9"/>')
    f.a(f'<line x1="{x + w}" y1="{y + dy}" x2="{x + w}" y2="{y + h + dy}" stroke="{stroke}" stroke-width="0.9"/>')
    f.a(f'<line x1="{x}" y1="{y + dy}" x2="{x + w}" y2="{y + dy}" stroke="{stroke}" stroke-width="0.9"/>')
    if label:
        f.text(x + w / 2, y + dy + h / 2, label, size=8.5, weight=700, fill=DARK, anchor="middle")


# ==============================================================================
# HÌNH 1: TIẾN HÓA CỦA TENSOR TỪ 0D ĐẾN 4D (tk-1)
# ==============================================================================
def fig_tensor_evolution():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "TIẾN HÓA CỦA TENSOR: TỪ SCALAR ĐẾN TENSOR 4 CHIỀU (0D ĐẾN 4D)", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Cấu trúc dữ liệu đa trục: Bậc (Rank/Order), Shape, Indexing và ví dụ thực tế trong Computer Vision / NPU", size=9.2, fill=GRAY)

    col_w = 168
    col_gap = 7
    start_x = 16
    y_top = 58
    box_h = 252

    cols = [
        {
            "rank": "Bậc 0 (Scalar)",
            "name": "Số vô hướng",
            "bg": "#FAFAFA",
            "stroke": "#B0BEC5",
            "shape": "()  hoặc  torch.Size([])",
            "idx": "x  (không có chỉ số)",
            "cv": "Loss = 0.28, Conf_thresh = 0.25",
            "type": "scalar",
        },
        {
            "rank": "Bậc 1 (Vector)",
            "name": "Mảng 1 chiều",
            "bg": "#F5FBF6",
            "stroke": "#A5D6A7",
            "shape": "(d,)  ví dụ  (4,)",
            "idx": "x[i]   (0 ≤ i < d)",
            "cv": "Tọa độ bbox [x1, y1, x2, y2], nhãn",
            "type": "vector",
        },
        {
            "rank": "Bậc 2 (Matrix)",
            "name": "Ma trận 2 chiều",
            "bg": "#F4F8FD",
            "stroke": "#90CAF9",
            "shape": "(H, W)  ví dụ  (4, 4)",
            "idx": "x[i, j]   (hàng i, cột j)",
            "cv": "Ảnh xám, trọng số Dense W[d_out, d_in]",
            "type": "matrix",
        },
        {
            "rank": "Bậc 3 (3D Tensor)",
            "name": "Khối 3 chiều",
            "bg": "#FCF8F2",
            "stroke": "#FFCC80",
            "shape": "(C, H, W)  hoặc  (H, W, C)",
            "idx": "x[c, h, w]   (kênh c, cao h, rộng w)",
            "cv": "1 ảnh màu RGB (3 kênh), feature map",
            "type": "3d",
        },
        {
            "rank": "Bậc 4 (4D Tensor)",
            "name": "Chuỗi khối 4 chiều",
            "bg": "#F9F5FB",
            "stroke": "#CE93D8",
            "shape": "(N, C, H, W)  chuẩn NCHW",
            "idx": "x[n, c, h, w]   (ảnh n trong batch)",
            "cv": "Mini-batch nạp vào NPU RK3588",
            "type": "4d",
        },
    ]

    for idx, c in enumerate(cols):
        cx = start_x + idx * (col_w + col_gap)
        # Khung panel
        rect(f, cx, y_top, col_w, box_h, fill=c["bg"], stroke=c["stroke"], sw=1.1, rx=5)

        # Tiêu đề bậc & tên
        rect(f, cx + 6, y_top + 6, col_w - 12, 32, fill="#FFFFFF", stroke=c["stroke"], sw=0.8, rx=3)
        f.text(cx + col_w / 2, y_top + 16, c["rank"], size=8.5, weight=700, fill=DARK, anchor="middle")
        f.text(cx + col_w / 2, y_top + 29, c["name"], size=7.5, fill=GRAY, anchor="middle")

        # Khung đồ họa minh họa hình học (y: 104 đến 180, cao 76)
        diag_y = y_top + 43
        diag_h = 78
        rect(f, cx + 6, diag_y, col_w - 12, diag_h, fill="#FFFFFF", stroke="#CFD8DC", sw=0.8, rx=3)

        # Vẽ hình học theo loại
        if c["type"] == "scalar":
            # Điểm đơn lẻ và giá trị
            f.a(f'<circle cx="{cx + col_w/2}" cy="{diag_y + 30}" r="14" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.3"/>')
            f.text(cx + col_w / 2, diag_y + 30, "42", size=10, weight=700, fill="#0369A1", anchor="middle")
            f.text(cx + col_w / 2, diag_y + 58, "1 điểm số duy nhất", size=7.5, fill="#555555", anchor="middle")

        elif c["type"] == "vector":
            # Dải 4 ô ngang
            vx_start = cx + 22
            vy = diag_y + 22
            box_sz = 26
            vals = ["1.2", "-0.5", "3.0", "0.8"]
            for v_idx, val in enumerate(vals):
                bx = vx_start + v_idx * box_sz
                rect(f, bx, vy, box_sz, box_sz, fill="#E8F5E9", stroke="#2E7D32", sw=1.0)
                f.text(bx + box_sz / 2, vy + box_sz / 2, val, size=7.0, weight=700, fill="#1B5E20", anchor="middle")
                f.text(bx + box_sz / 2, vy - 6, f"[{v_idx}]", size=6.5, fill=GRAY, anchor="middle")
            # Trục ngang
            f.text(cx + col_w / 2, diag_y + 60, "Trục 0 (chiều dài d = 4)", size=7.5, fill="#2E7D32", anchor="middle")

        elif c["type"] == "matrix":
            # Lưới 3x3
            mx_start = cx + 54
            my = diag_y + 8
            sz = 17
            for r in range(3):
                for col in range(3):
                    bx = mx_start + col * sz
                    by = my + r * sz
                    fill_c = "#E3F2FD" if (r == 1 and col == 2) else "#F0F4F8"
                    stroke_c = "#1565C0" if (r == 1 and col == 2) else "#90A4AE"
                    rect(f, bx, by, sz, sz, fill=fill_c, stroke=stroke_c, sw=0.8)
            # Nhãn hàng & cột thoáng đãng
            f.text(mx_start - 8, my + sz * 1.5, "Hàng", size=6.8, fill=DARK, anchor="end")
            f.text(mx_start + sz * 1.5, my - 4, "Cột", size=6.8, fill=DARK, anchor="middle")
            f.text(cx + col_w / 2, diag_y + 68, "Lưới 2D: x[i, j]", size=7.5, fill="#1565C0", weight=700, anchor="middle")

        elif c["type"] == "3d":
            # 3 lát mặt phẳng (R, G, B)
            sl_w = 44
            sl_h = 32
            sl_x = cx + 34
            sl_y = diag_y + 8
            draw_perspective_slice(f, sl_x, sl_y, sl_w, sl_h, "R", fill="#FFEBEE", stroke="#E53935", dx=11, dy=7)
            draw_perspective_slice(f, sl_x + 16, sl_y + 9, sl_w, sl_h, "G", fill="#E8F5E9", stroke="#43A047", dx=11, dy=7)
            draw_perspective_slice(f, sl_x + 32, sl_y + 18, sl_w, sl_h, "B", fill="#E3F2FD", stroke=BLUE, dx=11, dy=7)
            f.text(cx + col_w / 2, diag_y + 69, "3 kênh: (C=3, H, W)", size=7.5, fill="#D97706", weight=700, anchor="middle")

        elif c["type"] == "4d":
            # 3 khối hộp nhỏ xếp theo hàng batch
            b_w = 34
            b_h = 28
            bx_base = cx + 18
            by_base = diag_y + 15
            for b_i, b_lbl in enumerate(["N=0", "N=1", "..."]):
                bx = bx_base + b_i * 44
                draw_perspective_slice(f, bx, by_base, b_w, b_h, b_lbl, fill="#F3E8FF", stroke="#9333EA", dx=9, dy=7)
            f.text(cx + col_w / 2, diag_y + 69, "Batch N ảnh: x[n, c, h, w]", size=7.5, fill="#7E22CE", weight=700, anchor="middle")

        # Khối thông số chi tiết (Shape, Index, CV)
        info_y = diag_y + diag_h + 8

        # 1. Shape
        rect(f, cx + 6, info_y, col_w - 12, 34, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
        f.text(cx + 12, info_y + 10, "Shape kích thước:", size=6.8, weight=700, fill="#546E7A")
        f.text(cx + 12, info_y + 24, c["shape"], size=7.2, weight=700, fill=DARK, mono=True)

        # 2. Indexing
        rect(f, cx + 6, info_y + 38, col_w - 12, 34, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
        f.text(cx + 12, info_y + 48, "Cú pháp truy cập (Indexing):", size=6.8, weight=700, fill="#546E7A")
        f.text(cx + 12, info_y + 62, c["idx"], size=7.0, weight=700, fill=BLUE, mono=True)

        # 3. Ứng dụng thực tế
        rect(f, cx + 6, info_y + 76, col_w - 12, 42, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
        f.text(cx + 12, info_y + 86, "Ứng dụng trong AI / NPU:", size=6.8, weight=700, fill="#546E7A")
        # Chia thành 2 dòng gọn gàng
        if c["type"] == "scalar":
            f.text(cx + 12, info_y + 98, "• Loss = 0.28", size=6.8, fill=DARK)
            f.text(cx + 12, info_y + 110, "• Conf_thresh = 0.25", size=6.8, fill=DARK)
        elif c["type"] == "vector":
            f.text(cx + 12, info_y + 98, "• Tọa độ bbox [x1, y1, x2, y2]", size=6.8, fill=DARK)
            f.text(cx + 12, info_y + 110, "• Vector nhãn phân loại (logits)", size=6.8, fill=DARK)
        elif c["type"] == "matrix":
            f.text(cx + 12, info_y + 98, "• Ảnh xám 1 kênh (H × W)", size=6.8, fill=DARK)
            f.text(cx + 12, info_y + 110, "• Ma trận trọng số W[d_out, d_in]", size=6.8, fill=DARK)
        elif c["type"] == "3d":
            f.text(cx + 12, info_y + 98, "• 1 ảnh màu RGB [3, H, W]", size=6.8, fill=DARK)
            f.text(cx + 12, info_y + 110, "• Feature map tích chập", size=6.8, fill=DARK)
        elif c["type"] == "4d":
            f.text(cx + 12, info_y + 98, "• Mini-batch [N, C, H, W]", size=6.8, fill=DARK)
            f.text(cx + 12, info_y + 110, "• Chuẩn nạp phần cứng NPU", size=6.8, fill=DARK)

    source(f, H - 32, "Nguồn: [T2 D2L tr.30, tr.31, tr.41, tr.43, tr.44]. Bậc là số trục; Shape là độ dài từng trục.")
    return f


# ==============================================================================
# HÌNH 2: CƠ CHẾ CẮT LÁT VÀ CHỈ SỐ HÓA TENSOR (tk-2)
# ==============================================================================
def fig_tensor_slicing():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "CƠ CHẾ CẮT LÁT (SLICING) VÀ LẬP CHỈ MỤC TRÊN TENSOR ĐA TRỤC", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Cách trích xuất dữ liệu không gian, kênh màu và mẫu dữ liệu từ Batch: Phân biệt chỉ số cố định và lát cắt range (:)", size=9.2, fill=GRAY)

    y_top = 58
    p_h = 252

    # Panel A: Trích xuất 1 ảnh từ Batch (4D -> 3D)
    w_a = 280
    x_a = 16
    rect(f, x_a, y_top, w_a, p_h, fill="#FBFBFC", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, x_a + 8, y_top + 8, w_a - 16, 26, fill="#EDE7F6", stroke="#B39DDB", sw=0.8, rx=3)
    f.text(x_a + w_a / 2, y_top + 21, "A. LẤY 1 MẪU TỪ BATCH (4D → 3D)", size=8.2, weight=700, fill="#4A148C", anchor="middle")

    # Đồ họa Panel A
    diag_ya = y_top + 42
    rect(f, x_a + 8, diag_ya, w_a - 16, 95, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # Batch 3 khối, khối 0 được highlight
    for bi in range(3):
        bx = x_a + 22 + bi * 46
        by = diag_ya + 22
        fill_b = "#E1BEE7" if bi == 0 else "#F3E5F5"
        stroke_b = "#8E24AA" if bi == 0 else "#CE93D8"
        draw_perspective_slice(f, bx, by, 34, 34, f"i={bi}", fill=fill_b, stroke=stroke_b, dx=10, dy=8)
    f.text(x_a + 39, diag_ya + 14, "Trích ảnh i=0", size=7.2, weight=700, fill="#8E24AA", anchor="middle")

    # Mũi tên kéo ra khối 3D riêng
    f.a(f'<path d="M {x_a + 175} {diag_ya + 45} L {x_a + 205} {diag_ya + 45}" stroke="#8E24AA" stroke-width="1.5" marker-end="url(#{f.marker(BLUE, THIN)})"/>')
    draw_perspective_slice(f, x_a + 215, diag_ya + 22, 34, 34, "3D", fill="#E1BEE7", stroke="#8E24AA", dx=10, dy=8)

    # Code và giải thích Panel A
    f.text(x_a + 12, y_top + 152, "Cú pháp thực hiện:", size=7.5, weight=700, fill=DARK)
    rect(f, x_a + 8, y_top + 162, w_a - 16, 26, fill="#263238", stroke="#263238", rx=3)
    f.text(x_a + 16, y_top + 175, "img = batch[0]  # shape: [C, H, W]", size=7.5, fill="#80D8FF", mono=True)

    f.text(x_a + 12, y_top + 202, "Ý nghĩa:", size=7.5, weight=700, fill=DARK)
    f.text(x_a + 12, y_top + 216, "• Cố định trục batch n=0, giải phóng trục N.", size=7.0, fill="#455A64")
    f.text(x_a + 12, y_top + 229, "• Giảm bậc từ 4D xuống 3D (C, H, W).", size=7.0, fill="#455A64")
    f.text(x_a + 12, y_top + 242, "• Tương đương cú pháp batch[0, :, :, :].", size=7.0, fill="#455A64")

    # Panel B: Trích xuất 1 Channel màu (3D -> 2D)
    w_b = 280
    x_b = x_a + w_a + 12
    rect(f, x_b, y_top, w_b, p_h, fill="#FBFBFC", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, x_b + 8, y_top + 8, w_b - 16, 26, fill="#E8F5E9", stroke="#A5D6A7", sw=0.8, rx=3)
    f.text(x_b + w_b / 2, y_top + 21, "B. CẮT KÊNH MÀU CHANNEL (3D → 2D)", size=8.2, weight=700, fill="#1B5E20", anchor="middle")

    # Đồ họa Panel B
    diag_yb = y_top + 42
    rect(f, x_b + 8, diag_yb, w_b - 16, 95, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # 3 mặt phẳng R, G, B thoáng, nhãn ngắn gọn R, G, B
    draw_perspective_slice(f, x_b + 20, diag_yb + 16, 40, 38, "R", fill="#FFCDD2", stroke="#C62828", dx=12, dy=8)
    draw_perspective_slice(f, x_b + 55, diag_yb + 24, 40, 38, "G", fill="#E8F5E9", stroke="#388E3C", dx=12, dy=8)
    draw_perspective_slice(f, x_b + 90, diag_yb + 32, 40, 38, "B", fill="#E3F2FD", stroke=BLUE, dx=12, dy=8)
    f.text(x_b + 38, diag_yb + 13, "Kênh 0 (R)", size=7.2, weight=700, fill="#C62828", anchor="middle")

    # Mũi tên kéo mặt phẳng R ra
    f.a(f'<path d="M {x_b + 160} {diag_yb + 45} L {x_b + 195} {diag_yb + 45}" stroke="#C62828" stroke-width="1.5" marker-end="url(#{f.marker(RED, THIN)})"/>')
    rect(f, x_b + 208, diag_yb + 22, 52, 46, fill="#FFEBEE", stroke="#C62828", sw=1.2, rx=3)
    f.text(x_b + 234, diag_yb + 40, "2D (H×W)", size=7.5, weight=700, fill="#C62828", anchor="middle")
    f.text(x_b + 234, diag_yb + 52, "Ma trận ảnh", size=6.8, fill="#C62828", anchor="middle")

    # Code và giải thích Panel B
    f.text(x_b + 12, y_top + 152, "Cú pháp thực hiện:", size=7.5, weight=700, fill=DARK)
    rect(f, x_b + 8, y_top + 162, w_b - 16, 26, fill="#263238", stroke="#263238", rx=3)
    f.text(x_b + 16, y_top + 175, "red_plane = img[0, :, :]  # [H, W]", size=7.5, fill="#A5D6A7", mono=True)

    f.text(x_b + 12, y_top + 202, "Ý nghĩa:", size=7.5, weight=700, fill=DARK)
    f.text(x_b + 12, y_top + 216, "• Cố định chỉ số channel c=0 (kênh Red).", size=7.0, fill="#455A64")
    f.text(x_b + 12, y_top + 229, "• Giữ nguyên toàn bộ chiều cao (H) và rộng (W).", size=7.0, fill="#455A64")
    f.text(x_b + 12, y_top + 242, "• Kết quả là một ma trận 2D cường độ điểm ảnh.", size=7.0, fill="#455A64")

    # Panel C: Trích xuất 1 Pixel đa kênh (3D -> 1D Vector)
    w_c = 280
    x_c = x_b + w_b + 12
    rect(f, x_c, y_top, w_c, p_h, fill="#FBFBFC", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, x_c + 8, y_top + 8, w_c - 16, 26, fill="#E3F2FD", stroke="#90CAF9", sw=0.8, rx=3)
    f.text(x_c + w_c / 2, y_top + 21, "C. TRÍCH PIXEL ĐA KÊNH (3D → 1D)", size=8.2, weight=700, fill="#0D47A1", anchor="middle")

    # Đồ họa Panel C
    diag_yc = y_top + 42
    rect(f, x_c + 8, diag_yc, w_c - 16, 95, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # Khối 3D và tia đâm xuyên (h, w)
    draw_perspective_slice(f, x_c + 20, diag_yc + 16, 40, 38, "R", fill="#FFCDD2", stroke="#C62828", dx=12, dy=8)
    draw_perspective_slice(f, x_c + 55, diag_yc + 24, 40, 38, "G", fill="#E8F5E9", stroke="#388E3C", dx=12, dy=8)
    draw_perspective_slice(f, x_c + 90, diag_yc + 32, 40, 38, "B", fill="#E3F2FD", stroke=BLUE, dx=12, dy=8)

    # Chấm pixel xuyên suốt 3 kênh
    f.a(f'<circle cx="{x_c + 45}" cy="{diag_yc + 33}" r="3" fill="#D50000"/>')
    f.a(f'<circle cx="{x_c + 80}" cy="{diag_yc + 41}" r="3" fill="#00C853"/>')
    f.a(f'<circle cx="{x_c + 115}" cy="{diag_yc + 49}" r="3" fill="#2979FF"/>')
    f.a(f'<line x1="{x_c + 45}" y1="{diag_yc + 33}" x2="{x_c + 115}" y2="{diag_yc + 49}" stroke="#D50000" stroke-width="1.5" stroke-dasharray="3 2"/>')

    # Mũi tên kéo ra vector 1D
    f.a(f'<path d="M {x_c + 145} {diag_yc + 45} L {x_c + 175} {diag_yc + 45}" stroke="#1565C0" stroke-width="1.5" marker-end="url(#{f.marker(BLUE, THIN)})"/>')
    # 3 ô vector đứng [R, G, B]
    vy = diag_yc + 16
    v_sz = 18
    rect(f, x_c + 195, vy, 40, v_sz, fill="#FFEBEE", stroke="#C62828", sw=0.8)
    f.text(x_c + 215, vy + v_sz / 2, "R=255", size=6.5, weight=700, fill="#C62828", anchor="middle")
    rect(f, x_c + 195, vy + v_sz, 40, v_sz, fill="#E8F5E9", stroke="#388E3C", sw=0.8)
    f.text(x_c + 215, vy + v_sz * 1.5, "G=128", size=6.5, weight=700, fill="#388E3C", anchor="middle")
    rect(f, x_c + 195, vy + v_sz * 2, 40, v_sz, fill="#E3F2FD", stroke=BLUE, sw=0.8)
    f.text(x_c + 215, vy + v_sz * 2.5, "B=64", size=6.5, weight=700, fill=BLUE, anchor="middle")
    f.text(x_c + 248, vy + v_sz * 1.5, "1D", size=7.5, weight=700, fill=DARK)

    # Code và giải thích Panel C
    f.text(x_c + 12, y_top + 152, "Cú pháp thực hiện:", size=7.5, weight=700, fill=DARK)
    rect(f, x_c + 8, y_top + 162, w_c - 16, 26, fill="#263238", stroke="#263238", rx=3)
    f.text(x_c + 16, y_top + 175, "pixel = img[:, h, w]  # [C=3]", size=7.5, fill="#80D8FF", mono=True)

    f.text(x_c + 12, y_top + 202, "Ý nghĩa:", size=7.5, weight=700, fill=DARK)
    f.text(x_c + 12, y_top + 216, "• Cố định tọa độ không gian (h, w).", size=7.0, fill="#455A64")
    f.text(x_c + 12, y_top + 229, "• Trích xuất toàn bộ kênh màu thành vector 1D.", size=7.0, fill="#455A64")
    f.text(x_c + 12, y_top + 242, "• Là pixel biểu diễn màu sắc tại vị trí (h, w).", size=7.0, fill="#455A64")

    source(f, H - 32, "Nguồn: [T2 D2L tr.31, tr.44, tr.135]. Chỉ số nguyên cố định làm giảm bậc (rank); dấu : giữ nguyên trục.")
    return f


# ==============================================================================
# HÌNH 3: BỐ CỤC BỘ NHỚ NCHW VS NHWC (tk-3)
# ==============================================================================
def fig_memory_layout_nchw_nhwc():
    H = 415
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "BỐ CỤC BỘ NHỚ TENSOR: NCHW (PLANAR) VS NHWC (CHANNELS-LAST)", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Cùng tensor logic 3D (C=3, H=2, W=2) nhưng khác trật tự trải phẳng 1D trong RAM; cơ chế Stride và offset", size=9.2, fill=GRAY)

    y_top = 58
    pw = 428
    ph = 320

    # Panel A: NCHW (Planar)
    xa = 16
    rect(f, xa, y_top, pw, ph, fill="#FCFDFD", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, xa + 8, y_top + 8, pw - 16, 26, fill="#E3F2FD", stroke="#90CAF9", sw=0.8, rx=3)
    f.text(xa + pw / 2, y_top + 21, "A. NCHW (PLANAR / KÊNH TRƯỚC - PYTORCH CHUẨN)", size=8.2, weight=700, fill="#0D47A1", anchor="middle")

    # Đồ họa Tensor 3D logic mẫu (C=3, H=2, W=2) trong Panel A
    diag_ya = y_top + 40
    rect(f, xa + 10, diag_ya, pw - 20, 68, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # 3 mặt phẳng kênh 2x2
    draw_perspective_slice(f, xa + 24, diag_ya + 10, 38, 34, "R", fill="#FFCDD2", stroke="#E53935", dx=10, dy=7)
    draw_perspective_slice(f, xa + 50, diag_ya + 15, 38, 34, "G", fill="#C8E6C9", stroke="#43A047", dx=10, dy=7)
    draw_perspective_slice(f, xa + 76, diag_ya + 20, 38, 34, "B", fill="#BBDEFB", stroke="#1E88E5", dx=10, dy=7)

    # Giải thích logic NCHW bên cạnh đồ họa
    f.text(xa + 130, diag_ya + 18, "Tensor 3D: C=3, H=2, W=2 (12 phần tử)", size=7.5, weight=700, fill="#1565C0")
    f.text(xa + 130, diag_ya + 34, "• Trật tự: Hết kênh Đỏ (R) → Kênh Lục (G) → Kênh Lam (B)", size=6.8, fill=DARK)
    f.text(xa + 130, diag_ya + 48, "• Lưu theo từng khối mặt phẳng 2D (Planar format).", size=6.8, fill=DARK)

    # Tiêu đề Mảng RAM 1D căn giữa panel
    ram_title_ya = diag_ya + 78
    f.text(xa + pw / 2, ram_title_ya, "Mảng RAM 1D tuyến tính (12 ô nhớ liên tiếp):", size=7.2, weight=700, fill="#37474F", anchor="middle")

    # 12 ô RAM 1D cho NCHW căn giữa panel tuyệt đối
    ram_ya = ram_title_ya + 10
    cell_w = 32
    cell_h = 24
    start_cell_x = xa + (pw - 12 * cell_w) / 2  # xa + 22

    # 4 ô Red (0..3)
    for i in range(4):
        cx = start_cell_x + i * cell_w
        rect(f, cx, ram_ya, cell_w, cell_h, fill="#FFCDD2", stroke="#E53935", sw=0.9)
        lbl = f"R{i // 2}{i % 2}"
        f.text(cx + cell_w / 2, ram_ya + 12, lbl, size=6.8, weight=700, fill="#B71C1C", anchor="middle")
        f.text(cx + cell_w / 2, ram_ya + 32, str(i), size=6.5, fill="#78909C", anchor="middle")

    # 4 ô Green (4..7)
    for i in range(4):
        cx = start_cell_x + (4 + i) * cell_w
        rect(f, cx, ram_ya, cell_w, cell_h, fill="#C8E6C9", stroke="#43A047", sw=0.9)
        lbl = f"G{i // 2}{i % 2}"
        f.text(cx + cell_w / 2, ram_ya + 12, lbl, size=6.8, weight=700, fill="#1B5E20", anchor="middle")
        f.text(cx + cell_w / 2, ram_ya + 32, str(4 + i), size=6.5, fill="#78909C", anchor="middle")

    # 4 ô Blue (8..11)
    for i in range(4):
        cx = start_cell_x + (8 + i) * cell_w
        rect(f, cx, ram_ya, cell_w, cell_h, fill="#BBDEFB", stroke="#1E88E5", sw=0.9)
        lbl = f"B{i // 2}{i % 2}"
        f.text(cx + cell_w / 2, ram_ya + 12, lbl, size=6.8, weight=700, fill="#0D47A1", anchor="middle")
        f.text(cx + cell_w / 2, ram_ya + 32, str(8 + i), size=6.5, fill="#78909C", anchor="middle")

    f.text(xa + pw / 2, ram_ya + 44, "Chỉ số offset phần tử trong bộ nhớ RAM tuyến tính (0 đến 11)", size=6.8, fill=GRAY, anchor="middle")

    # Bảng Stride và Công thức NCHW
    box_info_y = ram_ya + 54
    rect(f, xa + 10, box_info_y, pw - 20, 114, fill="#FFFFFF", stroke="#ECEFF1", sw=0.9, rx=4)

    f.text(xa + 18, box_info_y + 14, "Cơ chế Stride và công thức ánh xạ địa chỉ:", size=7.8, weight=700, fill="#263238")

    # Stride box
    f.rich(xa + 18, box_info_y + 32, [
        ("• Shape: ", "b"), ("(C=3, H=2, W=2)", "c"),
        ("  |  Stride: ", "b"), ("(4, 2, 1)", "c")
    ], size=7.2)
    f.text(xa + 18, box_info_y + 46, "  (Nhảy 1 kênh: bước 4 ô | Nhảy 1 hàng H: bước 2 ô | Nhảy 1 cột W: bước 1 ô)", size=6.6, fill="#546E7A")

    # Offset formula
    f.rich(xa + 18, box_info_y + 64, [
        ("• Công thức offset: ", "b"),
        ("Offset = c × 4 + h × 2 + w × 1", "c")
    ], size=7.2)

    # Ví dụ phần tử G(1, 0)
    f.rich(xa + 18, box_info_y + 80, [
        ("• Ví dụ phần tử ", "b"), ("G(h=1, w=0)", "c"),
        (" có c=1:  Offset = 1×4 + 1×2 + 0×1 = ", "t"),
        ("6", "b"), (" (ô nhớ số 6)", "t")
    ], size=7.2)

    # Đánh giá ưu nhược điểm
    f.text(xa + 18, box_info_y + 96, "• Phù hợp thuật toán xử lý riêng từng kênh (Convolution 2D độc lập).", size=6.8, fill="#2E7D32")
    f.text(xa + 18, box_info_y + 108, "• Khi đọc trọn bộ pixel (R,G,B), dữ liệu bị phân tán, không liên tục.", size=6.8, fill="#C62828")

    # Panel B: NHWC / Channels-Last
    xb = 456
    rect(f, xb, y_top, pw, ph, fill="#FCFDFD", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, xb + 8, y_top + 8, pw - 16, 26, fill="#FFF3E0", stroke="#FFE082", sw=0.8, rx=3)
    f.text(xb + pw / 2, y_top + 21, "B. NHWC / CHANNELS-LAST (INTERLEAVED - RKNN NPU MẶC ĐỊNH)", size=8.2, weight=700, fill="#E65100", anchor="middle")

    # Đồ họa Tensor 3D logic mẫu trong Panel B
    diag_yb = y_top + 40
    rect(f, xb + 10, diag_yb, pw - 20, 68, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # 3 mặt phẳng kênh 2x2 với tia đâm xuyên điểm ảnh
    draw_perspective_slice(f, xb + 24, diag_yb + 10, 38, 34, "R", fill="#FFCDD2", stroke="#E53935", dx=10, dy=7)
    draw_perspective_slice(f, xb + 50, diag_yb + 15, 38, 34, "G", fill="#C8E6C9", stroke="#43A047", dx=10, dy=7)
    draw_perspective_slice(f, xb + 76, diag_yb + 20, 38, 34, "B", fill="#BBDEFB", stroke="#1E88E5", dx=10, dy=7)

    # Giải thích logic NHWC bên cạnh đồ họa
    f.text(xb + 130, diag_yb + 18, "Tensor 3D: C=3, H=2, W=2 (12 phần tử)", size=7.5, weight=700, fill="#E65100")
    f.text(xb + 130, diag_yb + 34, "• Trật tự: Pixel (0,0) → Pixel (0,1) → Pixel (1,0) → Pixel (1,1)", size=6.8, fill=DARK)
    f.text(xb + 130, diag_yb + 48, "• Lưu xen kẽ các kênh của cùng 1 pixel (Interleaved format).", size=6.8, fill=DARK)

    # Tiêu đề Mảng RAM 1D căn giữa panel
    f.text(xb + pw / 2, ram_title_ya, "Mảng RAM 1D tuyến tính (12 ô nhớ liên tiếp):", size=7.2, weight=700, fill="#37474F", anchor="middle")

    start_cell_xb = xb + (pw - 12 * cell_w) / 2  # xb + 22
    # 4 cụm pixel (0,0), (0,1), (1,0), (1,1)
    pixels = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for p_idx, (ph_i, pw_i) in enumerate(pixels):
        base_i = p_idx * 3
        # R
        cx_r = start_cell_xb + base_i * cell_w
        rect(f, cx_r, ram_ya, cell_w, cell_h, fill="#FFCDD2", stroke="#E53935", sw=0.9)
        f.text(cx_r + cell_w / 2, ram_ya + 12, f"R{ph_i}{pw_i}", size=6.8, weight=700, fill="#B71C1C", anchor="middle")
        f.text(cx_r + cell_w / 2, ram_ya + 32, str(base_i), size=6.5, fill="#78909C", anchor="middle")
        # G
        cx_g = start_cell_xb + (base_i + 1) * cell_w
        rect(f, cx_g, ram_ya, cell_w, cell_h, fill="#C8E6C9", stroke="#43A047", sw=0.9)
        f.text(cx_g + cell_w / 2, ram_ya + 12, f"G{ph_i}{pw_i}", size=6.8, weight=700, fill="#1B5E20", anchor="middle")
        f.text(cx_g + cell_w / 2, ram_ya + 32, str(base_i + 1), size=6.5, fill="#78909C", anchor="middle")
        # B
        cx_b = start_cell_xb + (base_i + 2) * cell_w
        rect(f, cx_b, ram_ya, cell_w, cell_h, fill="#BBDEFB", stroke="#1E88E5", sw=0.9)
        f.text(cx_b + cell_w / 2, ram_ya + 12, f"B{ph_i}{pw_i}", size=6.8, weight=700, fill="#0D47A1", anchor="middle")
        f.text(cx_b + cell_w / 2, ram_ya + 32, str(base_i + 2), size=6.5, fill="#78909C", anchor="middle")

    f.text(xb + pw / 2, ram_ya + 44, "Chỉ số offset phần tử trong bộ nhớ RAM tuyến tính (0 đến 11)", size=6.8, fill=GRAY, anchor="middle")

    # Bảng Stride và Công thức NHWC
    rect(f, xb + 10, box_info_y, pw - 20, 114, fill="#FFFFFF", stroke="#ECEFF1", sw=0.9, rx=4)
    f.text(xb + 18, box_info_y + 14, "Cơ chế Stride và công thức ánh xạ địa chỉ:", size=7.8, weight=700, fill="#263238")

    # Stride box
    f.rich(xb + 18, box_info_y + 32, [
        ("• Shape: ", "b"), ("(C=3, H=2, W=2)", "c"),
        ("  |  Stride: ", "b"), ("(1, 6, 3)", "c")
    ], size=7.2)
    f.text(xb + 18, box_info_y + 46, "  (Channels-last PyTorch: channel bước 1 ô, H bước 6 ô, W bước 3 ô)", size=6.6, fill="#546E7A")

    # Offset formula
    f.rich(xb + 18, box_info_y + 64, [
        ("• Công thức offset: ", "b"),
        ("Offset = c × 1 + h × 6 + w × 3", "c")
    ], size=7.2)

    # Ví dụ phần tử G(1, 0)
    f.rich(xb + 18, box_info_y + 80, [
        ("• Ví dụ phần tử ", "b"), ("G(h=1, w=0)", "c"),
        (" có c=1:  Offset = 1×1 + 1×6 + 0×3 = ", "t"),
        ("7", "b"), (" (ô nhớ số 7)", "t")
    ], size=7.2)

    # Đánh giá ưu nhược điểm
    f.text(xb + 18, box_info_y + 96, "• Channel là chiều dày nhất (stride=1). Tối ưu NPU đọc burst pixel.", size=6.8, fill="#2E7D32")
    f.text(xb + 18, box_info_y + 108, "• Chuẩn mặc định của RKNN-Toolkit2 (input_is_nchw=False mặc định là NHWC).", size=6.8, fill="#E65100")

    source(f, H - 22, "Nguồn: [T2 PTMF] PyTorch Channels Last Memory Format; [T1 RKNNAPI pdf 11, pdf 17]. Stride định nghĩa bước nhảy phần tử giữa các chỉ số.")
    return f


# ==============================================================================
# HÌNH 4: CẤU TRÚC PHÂN BỔ BIT VÀ KIỂU DỮ LIỆU (tk-4)
# ==============================================================================
def fig_bit_structure_datatypes():
    H = 370
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "CẤU TRÚC PHÂN BỔ BIT VÀ ĐÁNH ĐỔI KIỂU DỮ LIỆU: FP32, FP16, BFLOAT16 VÀ INT8", size=13, weight=700, fill=DARK)
    f.text(20, 42, "So sánh các trường bit (Sign, Exponent, Mantissa), dung lượng bộ nhớ, dải động (Dynamic Range) và độ chính xác", size=9.2, fill=GRAY)

    y_top = 58

    # Khung bao các thanh ghi
    reg_w = 460
    reg_x = 110

    # Chú thích các trường bit trên đầu
    f.text(reg_x, y_top + 10, "Trường bit:", size=7.5, weight=700, fill=DARK)
    rect(f, reg_x + 65, y_top + 2, 12, 12, fill="#EF5350", stroke="#C62828", sw=0.8)
    f.text(reg_x + 82, y_top + 9, "Sign (Dấu: s)", size=7.0, fill=DARK)
    rect(f, reg_x + 160, y_top + 2, 12, 12, fill="#FFA726", stroke="#EF6C00", sw=0.8)
    f.text(reg_x + 177, y_top + 9, "Exponent (Mũ: e)", size=7.0, fill=DARK)
    rect(f, reg_x + 270, y_top + 2, 12, 12, fill="#42A5F5", stroke="#1565C0", sw=0.8)
    f.text(reg_x + 287, y_top + 9, "Mantissa (Định trị: m)", size=7.0, fill=DARK)
    rect(f, reg_x + 400, y_top + 2, 12, 12, fill="#66BB6A", stroke="#2E7D32", sw=0.8)
    f.text(reg_x + 417, y_top + 9, "Integer (Số nguyên)", size=7.0, fill=DARK)

    # 4 kiểu dữ liệu
    types_data = [
        {
            "name": "FP32",
            "bytes": "4 Byte (32 bit)",
            "sign_w": 14,
            "exp_w": 115,
            "exp_lbl": "Exponent: 8 bit",
            "man_w": 331,
            "man_lbl": "Mantissa: 23 bit",
            "unused_w": 0,
            "range": "Max: 3.40 × 10³⁸",
            "prec": "Chính xác cao (~7 chữ số)",
            "npu": "Chuẩn gốc huấn luyện",
            "color": "#1565C0",
        },
        {
            "name": "FP16",
            "bytes": "2 Byte (16 bit)",
            "sign_w": 14,
            "exp_w": 72,
            "exp_lbl": "Exp: 5 bit",
            "man_w": 144,
            "man_lbl": "Mantissa: 10 bit",
            "unused_w": 230,
            "range": "Max: 6.55 × 10⁴ (dải hẹp)",
            "prec": "Trung bình (~3-4 chữ số)",
            "npu": "Tiết kiệm 50% RAM, cần loss-scaling",
            "color": "#E65100",
        },
        {
            "name": "BFLOAT16",
            "bytes": "2 Byte (16 bit)",
            "sign_w": 14,
            "exp_w": 115,
            "exp_lbl": "Exponent: 8 bit (như FP32)",
            "man_w": 101,
            "man_lbl": "Mantissa: 7 bit",
            "unused_w": 230,
            "range": "Max: 3.38 × 10³⁸ (như FP32)",
            "prec": "Thấp hơn FP16 (~2-3 chữ số)",
            "npu": "Tiết kiệm 50% RAM, dải rộng như FP32",
            "color": "#7B1FA2",
        },
        {
            "name": "INT8",
            "bytes": "1 Byte (8 bit)",
            "sign_w": 0,
            "exp_w": 0,
            "exp_lbl": "",
            "man_w": 0,
            "man_lbl": "",
            "int_w": 115,
            "int_lbl": "Integer: 8 bit (b=8)",
            "unused_w": 345,
            "range": "[-128, 127] hoặc [0, 255]",
            "prec": "Lượng tử hóa rời rạc",
            "npu": "Tiết kiệm 75% RAM, tối ưu NPU RK3588",
            "color": "#2E7D32",
        },
    ]

    row_h = 36
    row_start_y = y_top + 24

    for idx, t in enumerate(types_data):
        ry = row_start_y + idx * (row_h + 8)

        # Tên kiểu và dung lượng byte
        rect(f, 16, ry, 86, row_h, fill="#FAFAFA", stroke="#CFD8DC", sw=0.8, rx=3)
        f.text(59, ry + 12, t["name"], size=8.5, weight=700, fill=t["color"], anchor="middle")
        f.text(59, ry + 25, t["bytes"], size=6.8, fill=GRAY, anchor="middle")

        # Vẽ thanh ghi bit
        curr_x = reg_x
        if t["sign_w"] > 0:
            rect(f, curr_x, ry, t["sign_w"], row_h, fill="#EF5350", stroke="#C62828", sw=0.8)
            f.text(curr_x + t["sign_w"] / 2, ry + row_h / 2, "s", size=6.5, weight=700, fill="#FFFFFF", anchor="middle")
            curr_x += t["sign_w"]

        if t["exp_w"] > 0:
            rect(f, curr_x, ry, t["exp_w"], row_h, fill="#FFA726", stroke="#EF6C00", sw=0.8)
            f.text(curr_x + t["exp_w"] / 2, ry + row_h / 2, t["exp_lbl"], size=6.8, weight=700, fill="#E65100", anchor="middle")
            curr_x += t["exp_w"]

        if t["man_w"] > 0:
            rect(f, curr_x, ry, t["man_w"], row_h, fill="#BBDEFB", stroke="#1565C0", sw=0.8)
            f.text(curr_x + t["man_w"] / 2, ry + row_h / 2, t["man_lbl"], size=6.8, weight=700, fill="#0D47A1", anchor="middle")
            curr_x += t["man_w"]

        if t.get("int_w", 0) > 0:
            rect(f, curr_x, ry, t["int_w"], row_h, fill="#A5D6A7", stroke="#2E7D32", sw=0.8)
            f.text(curr_x + t["int_w"] / 2, ry + row_h / 2, t["int_lbl"], size=6.8, weight=700, fill="#1B5E20", anchor="middle")
            curr_x += t["int_w"]

        if t["unused_w"] > 0:
            rect(f, curr_x, ry, t["unused_w"], row_h, fill="#F5F5F5", stroke="#BDBDBD", sw=0.8, dashed=True)
            saved_pct = "50% RAM" if t["unused_w"] == 230 else "75% RAM (4×)"
            f.text(curr_x + t["unused_w"] / 2, ry + row_h / 2, f"Không dùng: Tiết kiệm {saved_pct} so với FP32", size=6.8, fill="#757575", anchor="middle")

        # Cột thông số bên phải (x=580 đến 884)
        stat_x = reg_x + reg_w + 12
        stat_w = W - stat_x - 16
        rect(f, stat_x, ry, stat_w, row_h, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
        f.text(stat_x + 8, ry + 11, f"• Dải số: {t['range']}", size=6.8, weight=700, fill=DARK)
        f.text(stat_x + 8, ry + 24, f"• {t['npu']}", size=6.5, fill="#455A64")

    # Hai khối đánh đổi ở dưới cùng (Y: 258 đến 346)
    bot_y = 258
    box_w = 428

    # Khối 1: Đánh đổi dải động và độ chính xác
    rect(f, 16, bot_y, box_w, 88, fill="#FCFDFD", stroke="#CFD8DC", sw=0.9, rx=4)
    rect(f, 22, bot_y + 6, box_w - 12, 18, fill="#EDE7F6", stroke="#D1C4E9", sw=0.6, rx=2)
    f.text(22 + (box_w - 12) / 2, bot_y + 15, "1. ĐÁNH ĐỔI GIỮA DẢI ĐỘNG (EXPONENT) VÀ ĐỘ CHÍNH XÁC (MANTISSA)", size=7.2, weight=700, fill="#512DA8", anchor="middle")

    f.text(26, bot_y + 36, "• BFLOAT16 giữ trọn 8 bit Exponent như FP32 nên giữ nguyên dải động (~10³⁸),", size=6.8, fill=DARK)
    f.text(26, bot_y + 49, "  giúp quá trình training hội tụ ổn định không cần sửa thuật toán loss-scaling.", size=6.8, fill=DARK)
    f.text(26, bot_y + 62, "• FP16 có 10 bit Mantissa cho độ chính xác cao hơn BF16, nhưng Exponent chỉ có 5 bit,", size=6.8, fill=DARK)
    f.text(26, bot_y + 75, "  dẫn tới dải số cực đại chỉ 6.55 × 10⁴, rất dễ tràn số (overflow) hoặc tắt về 0 (underflow).", size=6.8, fill="#C62828")

    # Khối 2: Tối ưu trên phần cứng NPU
    rect(f, 456, bot_y, box_w, 88, fill="#FCFDFD", stroke="#CFD8DC", sw=0.9, rx=4)
    rect(f, 462, bot_y + 6, box_w - 12, 18, fill="#E8F5E9", stroke="#C8E6C9", sw=0.6, rx=2)
    f.text(462 + (box_w - 12) / 2, bot_y + 15, "2. Ý NGHĨA KHI TRIỂN KHAI TRÊN NPU RK3588 (6 TOPS INT8)", size=7.2, weight=700, fill="#1B5E20", anchor="middle")

    f.text(466, bot_y + 36, "• INT8 (1 byte): Giảm tải 4× băng thông DRAM và SRAM cache so với FP32.", size=6.8, fill=DARK)
    f.text(466, bot_y + 49, "• Phép cộng INT8 tiết kiệm năng lượng 30× và diện tích silicon 116× so với FP32.", size=6.8, fill=DARK)
    f.text(466, bot_y + 62, "• NPU RK3588 tối ưu hóa tuyệt đối cho INT8 (đạt đỉnh 6 TOPS với 3 lõi NPU),", size=6.8, fill="#1B5E20")
    f.text(466, bot_y + 75, "  trong khi FP16/BF16 đạt khoảng 3 TFLOPS và tiêu thụ điện năng/băng thông lớn hơn.", size=6.8, fill=DARK)

    source(f, bot_y + 94, "Nguồn: [T2 BF16 tr.4, Table 1], [T2 MIXP tr.1-3], [T2 NAGEL tr.5, Fig. 3], [T2 GHOLAMI pdf 12-13]. Tự tính: 1 byte = 8 bit.")
    return f


# ==============================================================================
# HÌNH 5: BẢN CHẤT CỦA CHANNEL: RGB VS FEATURE MAP (tk-5)
# ==============================================================================
def fig_channel_nature_rgb_vs_feature_map():
    H = 365
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "BẢN CHẤT CỦA CHANNEL: TỪ KÊNH MÀU RGB ĐẦU VÀO ĐẾN KÊNH ĐẶC TRƯNG (FEATURE MAP)", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Sự chuyển dịch ý nghĩa: Từ 3 kênh màu quang học vật lý đến hàng trăm bản đồ đặc trưng ngữ nghĩa trong mạng sâu", size=9.2, fill=GRAY)

    y_top = 58
    ph = 270

    # Panel A: Kênh màu quang học (Left: w=376)
    wa = 376
    xa = 16
    rect(f, xa, y_top, wa, ph, fill="#FCFDFD", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, xa + 8, y_top + 8, wa - 16, 26, fill="#E3F2FD", stroke="#90CAF9", sw=0.8, rx=3)
    f.text(xa + wa / 2, y_top + 21, "A. KÊNH MÀU QUANG HỌC VẬT LÝ (INPUT RGB)", size=8.2, weight=700, fill="#0D47A1", anchor="middle")

    # Đồ họa 3 lát cắt RGB (R, G, B)
    diag_ya = y_top + 42
    rect(f, xa + 10, diag_ya, wa - 20, 88, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # 3 mặt phẳng màu
    sl_w = 64
    sl_h = 48
    sl_x = xa + 26
    sl_y = diag_ya + 10
    dy = 10
    draw_perspective_slice(f, sl_x, sl_y, sl_w, sl_h, "", fill="#FFCDD2", stroke="#E53935", dx=14, dy=dy)
    f.text(sl_x + 16, sl_y + dy + sl_h / 2, "R", size=9, weight=700, fill="#C62828", anchor="middle")

    draw_perspective_slice(f, sl_x + 36, sl_y + 12, sl_w, sl_h, "", fill="#C8E6C9", stroke="#43A047", dx=14, dy=dy)
    f.text(sl_x + 36 + 16, sl_y + 12 + dy + sl_h / 2, "G", size=9, weight=700, fill="#2E7D32", anchor="middle")

    draw_perspective_slice(f, sl_x + 72, sl_y + 24, sl_w, sl_h, "B", fill="#BBDEFB", stroke="#1E88E5", dx=14, dy=dy)

    # Nhãn bên phải của đồ họa
    f.text(xa + 205, diag_ya + 22, "Shape ảnh gốc: (C=3, H, W)", size=7.8, weight=700, fill="#1565C0")
    f.text(xa + 205, diag_ya + 38, "• R: Kênh Đỏ (Red)", size=7.0, fill="#C62828", weight=700)
    f.text(xa + 205, diag_ya + 52, "• G: Kênh Lục (Green)", size=7.0, fill="#2E7D32", weight=700)
    f.text(xa + 205, diag_ya + 66, "• B: Kênh Lam (Blue)", size=7.0, fill="#1565C0", weight=700)
    f.text(xa + 205, diag_ya + 80, "• Kích thước H × W giữ nguyên", size=6.8, fill=GRAY)

    # Khối diễn giải bản chất Panel A
    info_ya = diag_ya + 96
    rect(f, xa + 10, info_ya, wa - 20, 118, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
    f.text(xa + 18, info_ya + 16, "Bản chất vật lý của Kênh màu RGB:", size=7.8, weight=700, fill="#263238")
    f.text(xa + 18, info_ya + 34, "• Đo cường độ bức xạ ánh sáng trên 3 dải bước sóng quang học.", size=7.0, fill=DARK)
    f.text(xa + 18, info_ya + 48, "• Mỗi vị trí (h, w) mang vector 3 phần tử [R, G, B] chỉ màu sắc điểm ảnh.", size=7.0, fill=DARK)
    f.text(xa + 18, info_ya + 62, "• Số channel cố định theo cảm biến camera (3 cho RGB, 1 cho xám).", size=7.0, fill=DARK)
    f.text(xa + 18, info_ya + 80, "Trích dẫn D2L tr.252:", size=7.0, weight=700, fill="#1565C0")
    f.text(xa + 18, info_ya + 96, '"each RGB input image has shape 3 × h × w. We refer to', size=6.8, italic=True, fill="#37474F")
    f.text(xa + 18, info_ya + 108, ' this axis, with a size of 3, as the channel dimension."', size=6.8, italic=True, fill="#37474F")

    # Khối giữa: Biến đổi qua Convolution (Middle: w=116, x=400)
    xm = 400
    wm = 100
    rect(f, xm, y_top + 30, wm, 210, fill="#FFFDE7", stroke="#FFF59D", sw=0.9, rx=4)
    f.text(xm + wm / 2, y_top + 48, "CÁC LỚP", size=7.5, weight=700, fill="#E65100", anchor="middle")
    f.text(xm + wm / 2, y_top + 60, "TÍCH CHẬP", size=7.5, weight=700, fill="#E65100", anchor="middle")
    f.text(xm + wm / 2, y_top + 72, "(CONVOLUTION)", size=6.8, weight=700, fill="#E65100", anchor="middle")

    # Mũi tên dẫn hướng chuẩn figlib
    f.line([(xm + 18, y_top + 98), (xm + wm - 18, y_top + 98)], RED, width=THICK)
    f.text(xm + wm / 2, y_top + 118, "Bộ lọc trượt (Kernels)", size=6.8, fill=DARK, anchor="middle")
    f.text(xm + wm / 2, y_top + 130, "học đặc trưng đa tầng", size=6.8, fill=DARK, anchor="middle")

    # Quy luật D2L tr.253
    rect(f, xm + 6, y_top + 144, wm - 12, 86, fill="#FFFFFF", stroke="#FFF176", sw=0.6, rx=3)
    f.text(xm + wm / 2, y_top + 158, "Quy luật D2L:", size=6.8, weight=700, fill="#E65100", anchor="middle")
    f.text(xm + wm / 2, y_top + 172, "Mạng càng sâu:", size=6.8, fill=DARK, anchor="middle")
    f.text(xm + wm / 2, y_top + 188, "• Channel ↑ (tăng)", size=6.8, weight=700, fill="#2E7D32", anchor="middle")
    f.text(xm + wm / 2, y_top + 200, " (3 → 64 → 256)", size=6.2, fill="#2E7D32", anchor="middle")
    f.text(xm + wm / 2, y_top + 214, "• Không gian ↓ (giảm)", size=6.8, weight=700, fill="#C62828", anchor="middle")
    f.text(xm + wm / 2, y_top + 224, " (H × W thu nhỏ)", size=6.2, fill="#C62828", anchor="middle")

    # Panel B: Kênh đặc trưng ngữ nghĩa (Right: w=376, x=508)
    xb = 508
    wb = 376
    rect(f, xb, y_top, wb, ph, fill="#FCFDFD", stroke="#CFD8DC", sw=1.1, rx=5)
    rect(f, xb + 8, y_top + 8, wb - 16, 26, fill="#EDE7F6", stroke="#D1C4E9", sw=0.8, rx=3)
    f.text(xb + wb / 2, y_top + 21, "B. KÊNH ĐẶC TRƯNG NGỮ NGHĨA (FEATURE MAPS)", size=8.2, weight=700, fill="#512DA8", anchor="middle")

    # Đồ họa các Feature Maps
    diag_yb = y_top + 42
    rect(f, xb + 10, diag_yb, wb - 20, 88, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)

    # 4 lát cắt biểu diễn Channel đặc trưng với nhãn gọn và rõ
    sl_w2 = 54
    sl_h2 = 42
    sl_xb = xb + 24
    sl_yb = diag_yb + 12
    dy2 = 7
    draw_perspective_slice(f, sl_xb, sl_yb, sl_w2, sl_h2, "", fill="#EDE7F6", stroke="#7E57C2", dx=10, dy=dy2)
    f.text(sl_xb + 12, sl_yb + dy2 + sl_h2 / 2, "0", size=8, weight=700, fill="#512DA8", anchor="middle")

    draw_perspective_slice(f, sl_xb + 26, sl_yb + 8, sl_w2, sl_h2, "", fill="#D1C4E9", stroke="#5E35B1", dx=10, dy=dy2)
    f.text(sl_xb + 26 + 12, sl_yb + 8 + dy2 + sl_h2 / 2, "1", size=8, weight=700, fill="#512DA8", anchor="middle")

    draw_perspective_slice(f, sl_xb + 52, sl_yb + 16, sl_w2, sl_h2, "", fill="#B39DDB", stroke="#4527A0", dx=10, dy=dy2)
    f.text(sl_xb + 52 + 12, sl_yb + 16 + dy2 + sl_h2 / 2, "2", size=8, weight=700, fill="#4527A0", anchor="middle")

    draw_perspective_slice(f, sl_xb + 78, sl_yb + 24, sl_w2, sl_h2, "255", fill="#9575CD", stroke="#311B92", dx=10, dy=dy2)

    # Nhãn bên phải của đồ họa
    f.text(xb + 196, diag_yb + 22, "Shape tầng sâu: (C=256, H', W')", size=7.8, weight=700, fill="#512DA8")
    f.text(xb + 196, diag_yb + 38, "• Ch 0: Bản đồ cạnh & góc", size=7.0, fill=DARK)
    f.text(xb + 196, diag_yb + 52, "• Ch 1: Hoa văn, kết cấu bề mặt", size=7.0, fill=DARK)
    f.text(xb + 196, diag_yb + 66, "• Ch 2..k: Hình dạng bộ phận vật thể", size=7.0, fill=DARK)
    f.text(xb + 196, diag_yb + 80, "• Kích thước H' × W' co nhỏ lại", size=6.8, fill="#512DA8")

    # Khối diễn giải bản chất Panel B
    info_yb = diag_yb + 96
    rect(f, xb + 10, info_yb, wb - 20, 118, fill="#FFFFFF", stroke="#ECEFF1", sw=0.8, rx=3)
    f.text(xb + 18, info_yb + 16, "Bản chất toán học của Feature Map:", size=7.8, weight=700, fill="#263238")
    f.text(xb + 18, info_yb + 34, "• Không còn là màu sắc! Là mức độ phản ứng với một đặc trưng cụ thể.", size=7.0, fill=DARK)
    f.text(xb + 18, info_yb + 48, "• Tầng nông học cạnh viền, góc; tầng sâu học bộ phận (bánh xe, khuôn mặt).", size=7.0, fill=DARK)
    f.text(xb + 18, info_yb + 62, "• Số channel được quyết định bởi số bộ lọc (kernels) thiết kế trong kiến trúc.", size=7.0, fill=DARK)
    f.text(xb + 18, info_yb + 80, "Trích dẫn D2L tr.238:", size=7.0, weight=700, fill="#512DA8")
    f.text(xb + 18, info_yb + 96, '"They are also sometimes called feature maps, as each', size=6.8, italic=True, fill="#37474F")
    f.text(xb + 18, info_yb + 108, ' provides a spatialized set of learned features for the subsequent layer."', size=6.8, italic=True, fill="#37474F")

    source(f, H - 22, "Nguồn: [T2 D2L tr.44, tr.135, tr.238, tr.252, tr.253]. Kênh màu đo quang học; Kênh đặc trưng đo mức kích hoạt của thuộc tính học được.")
    return f


FIGS = [
    ("tk-1-tien-hoa-tensor-tu-0d-den-4d", fig_tensor_evolution),
    ("tk-2-co-che-cat-lat-va-chi-so-hoa-tensor", fig_tensor_slicing),
    ("tk-3-bo-cuc-bo-nho-nchw-va-nhwc", fig_memory_layout_nchw_nhwc),
    ("tk-4-cau-truc-bit-va-kieu-du-lieu", fig_bit_structure_datatypes),
    ("tk-5-ban-chat-channel-rgb-va-feature-map", fig_channel_nature_rgb_vs_feature_map),
]

if __name__ == "__main__":
    run(FIGS, DEFAULT_OUTDIR)


