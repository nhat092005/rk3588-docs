#!/usr/bin/env python3
"""Ghi chú chuyên đề: Tensors, Kênh dữ liệu và Kiểu số học trong NPU (01-tensors-va-du-lieu).

Sinh 4 hình chất lượng cao chuẩn visual_guide (không chồng lấn text, layout chuẩn pixel):
  - ht-1-ban-chat-channel (T2 chung): Bản chất của Channel trong mạng nơ-ron và phép tích chập
  - ht-2-channel-tren-npu-rk3588 (T1 RK3588): Tổ chức Channel trên NPU RK3588 và lượng tử hóa Per-Channel
  - ht-3-phan-loai-va-tradeoff (T2 chung): Phân loại hai họ kiểu dữ liệu và bảng đánh đổi khi giảm số bit
  - ht-4-ho-tro-phan-cung-rk3588 (T1 RK3588): Thông lượng MAC trên silicon RK3588 và ràng buộc của RKNN-Toolkit2

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: 01-tensors-va-du-lieu -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GREEN, INK, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"      # Màu nền phép tính / số học
STAT = "#FFF1CC"      # Màu highlight chú thích


def tier(f, label):
    f.tier(W - 130, 10, label)


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    """In chuỗi các dòng (str hoặc rich parts) xếp chồng từ toạ độ y; trả về y tiếp theo."""
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def card(f, x, y, w, h, title, size_t=14, dashed=False, fill="white"):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#333333" stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=size_t, weight=700, anchor="middle")


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def blk(f, x, y, w, h, lines, size=12.5, fill="white", weight=700, mono=False):
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
    top = y + h / 2 - (len(lines) - 1) * (size + 3) / 2
    for i, ln in enumerate(lines):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", mono=mono)


def draw_slice(f, x, y, w, h, label, fill="#E3F2FD", stroke=BLUE):
    """Vẽ một mặt phẳng 2D giả lập góc phối cảnh cho channel."""
    dx = 14
    dy = 10
    pts = [
        f"{x},{y + dy}",
        f"{x + dx},{y}",
        f"{x + w + dx},{y}",
        f"{x + w + dx},{y + h}",
        f"{x + w},{y + h + dy}",
        f"{x},{y + h + dy}"
    ]
    f.a(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
    f.a(f'<line x1="{x + w}" y1="{y + dy}" x2="{x + w + dx}" y2="{y}" stroke="{stroke}" stroke-width="1"/>')
    f.a(f'<line x1="{x + w}" y1="{y + dy}" x2="{x + w}" y2="{y + h + dy}" stroke="{stroke}" stroke-width="1"/>')
    f.a(f'<line x1="{x}" y1="{y + dy}" x2="{x + w}" y2="{y + dy}" stroke="{stroke}" stroke-width="1"/>')
    f.text(x + w / 2, y + dy + h / 2, label, size=11, weight=700, fill=DARK, anchor="middle")


# =====================================================================
# HÌNH T.1: BẢN CHẤT CỦA CHANNEL VÀ TÍCH CHẬP (T2 CHUNG)
# =====================================================================
def fig_channel_basics():
    f = Fig(W, 710)
    tier(f, "T2 chung")
    f.text(10, 48, "Bản chất của Channel trong mạng nơ-ron và phép tích chập", size=16, weight=700)

    # ---- A. TRỰC QUAN MẶT PHẲNG 2D VÀ FILTER ----
    f.text(10, 80, "A. Quan hệ giữa Channel đầu vào, Bộ lọc 3D (Filter) và Channel đầu ra", size=13.5, weight=700, fill=DARK)

    bx_y = 94
    bx_h = 175
    rect(f, 10, bx_y, 870, bx_h, fill="#FBFCFD", stroke="#CFD8DC", sw=1.0, rx=5)

    # Input Feature Map [C_in, H, W]
    f.text(25, bx_y + 22, "Input Feature Map [C_in, H, W]", size=12, weight=700, fill=BLUE)
    f.text(25, bx_y + 38, "gồm C_in mặt phẳng 2D (EYE tr.3)", size=10.5, fill="#555555")
    draw_slice(f, 30, bx_y + 55, 55, 55, "Ch 0 (R)", fill="#FFEBEE", stroke="#E53935")
    draw_slice(f, 60, bx_y + 65, 55, 55, "Ch 1 (G)", fill="#E8F5E9", stroke="#43A047")
    draw_slice(f, 90, bx_y + 75, 55, 55, "Ch 2 (B)", fill="#E3F2FD", stroke=BLUE)
    f.text(80, bx_y + 155, "C_in = 3 channels", size=10.5, weight=700, fill=DARK, anchor="middle")

    # Dấu nhân tích chập
    f.text(180, bx_y + 105, "✱", size=20, fill=DARK, anchor="middle")

    # Filter 3D [C_in, K, K]
    f.text(205, bx_y + 22, "1 Bộ lọc 3D [C_in, K, K]", size=12, weight=700, fill="#E65100")
    f.text(205, bx_y + 38, "gồm C_in lát cắt kernel KxK", size=10.5, fill="#555555")
    draw_slice(f, 215, bx_y + 55, 38, 38, "K 0", fill="#FFF3E0", stroke="#FB8C00")
    draw_slice(f, 238, bx_y + 65, 38, 38, "K 1", fill="#FFF3E0", stroke="#FB8C00")
    draw_slice(f, 260, bx_y + 75, 38, 38, "K 2", fill="#FFF3E0", stroke="#FB8C00")
    f.text(250, bx_y + 142, "Cộng dồn xuyên kênh", size=10, italic=True, fill="#E65100", anchor="middle")
    f.text(250, bx_y + 156, "(channel reduction)", size=10, italic=True, fill="#E65100", anchor="middle")

    # Mũi tên suy ra 1 Output Channel
    f.text(335, bx_y + 105, "➔", size=20, fill=DARK, anchor="middle")

    # 1 Output Channel [1, H', W']
    f.text(360, bx_y + 22, "1 Channel đầu ra", size=12, weight=700, fill=GREEN)
    f.text(360, bx_y + 38, "mặt phẳng đặc trưng mới", size=10.5, fill="#555555")
    draw_slice(f, 375, bx_y + 65, 55, 55, "Ofmap Ch 0", fill="#E8F8F5", stroke=GREEN)
    f.text(410, bx_y + 155, "1 output channel", size=10.5, weight=700, fill=GREEN, anchor="middle")

    # Ngăn cách giữa 1 filter và C_out filters
    f.a(f'<line x1="490" y1="{bx_y + 15}" x2="490" y2="{bx_y + bx_h - 15}" stroke="#CFD8DC" stroke-width="1.2" stroke-dasharray="4 3"/>')

    # Tổng kết quy tắc C_out filters
    f.text(510, bx_y + 24, "Quy tắc cốt lõi (EYE tr.3):", size=12.5, weight=700, fill=DARK)
    txt(f, 510, bx_y + 45, [
        [("Muốn có ", "t"), ("C_out", "b"), (" channels đầu ra:", "t")],
        [("cần đúng ", "t"), ("C_out bộ lọc 3D độc lập", "b"), (" (# of 3D filters = # of ofmap channels).", "t")],
        [("Kích thước tensor trọng số tổng thể: ", "t"), ("[C_out, C_in, K_h, K_w]", "b")],
        [("Tổng số trọng số (weights): ", "t"), ("C_out · C_in · K · K", "b")],
        [("Tại sao? ", "b"), ("Mỗi filter tính ra 1 channel; C_out filters tính ra C_out channels.", "t")],
    ], size=11, dy=18)

    y = bx_y + bx_h + 20

    # ---- B. BẢNG PHÂN LOẠI CÁC BIẾN THỂ CHANNEL ----
    f.text(10, y, "B. Các phép biến đổi và tổ hợp Channel trong kiến trúc CNN", size=13.5, weight=700, fill=DARK)
    y = f.table(10, y + 12, [150, 190, 240, 290], ["Phép biến đổi", "Kích thước Kernel", "Cơ chế xuyên kênh (Cross-channel)", "Ý nghĩa kiến trúc & Hiệu năng"], [
        ["Standard Conv", "[C_out, C_in, K, K]", "Cộng dồn toàn bộ C_in kênh", "Trộn cả không gian lẫn kênh; chuẩn trong CNN"],
        ["Pointwise (1x1 Conv)", "[C_out, C_in, 1, 1]", "Tổ hợp tuyến tính xuyên kênh", "Không quét không gian (K=1); thay đổi số channel"],
        ["Depthwise (DWConv)", "[C_in, 1, K, K]", "Tách rời, không trộn xuyên kênh", "groups = C_in; giảm FLOPs nhưng tốn băng thông"],
        ["Grouped Conv", "[C_out, C_in/G, K, K]", "Cộng dồn nội bộ từng nhóm G kênh", "Chia nhỏ mảng tính; trung gian giữa Conv và DWConv"],
    ], size=11.5, line_h=15)

    source(f, y + 10, "Nguồn: EYE tr.3 (# of ifmap/filter channels, # of 3D filters / # of ofmap channels); SURV tr.7.")
    return f


# =====================================================================
# HÌNH T.2: CHANNEL TRÊN NPU RK3588 (T1 RK3588)
# =====================================================================
def fig_rk3588_channel():
    f = Fig(W, 730)
    tier(f, "T1 RK3588")
    f.text(10, 48, "Tổ chức Channel trên phần cứng NPU RK3588 và lượng tử hóa Per-Channel", size=16, weight=700)

    # ---- A. SO SÁNH PER-CHANNEL VÀ PER-LAYER ----
    f.text(10, 80, "A. So sánh Per-Channel vs Per-Layer Quantization trên RKNN-Toolkit2", size=13.5, weight=700, fill=DARK)
    y = f.table(10, 92, [130, 230, 240, 270], ["Khía cạnh", "Per-Layer (Per-Tensor)", "Per-Channel (Channel-wise)", "Ràng buộc trên NPU RK3588"], [
        ["Số lượng Scale/ZP", "1 cặp dùng chung cho cả layer", "1 cặp riêng cho mỗi output channel", "Per-Channel chỉ áp dụng cho weight [UG232 tr.120]"],
        ["Độ chính xác Weight", "Dễ méo khi biên độ các filter lệch", "Bảo toàn phân phối từng filter", "NAGEL tr.16 khuyên dùng per-channel weight"],
        ["Lượng tử Activation", "Hỗ trợ và là chế độ bắt buộc", "Không hỗ trợ cho activation", "Activation phải cộng dồn xuyên kênh trước khi rescale"],
        ["Chi phí phần cứng NPU", "Tối thiểu", "Không tăng diện tích mảng MAC", "Scale được áp dụng ở bộ hoàn nguyên sau tích lũy"],
    ], size=11.5, line_h=15)

    # ---- B. CĂN CHỈNH CHANNEL VÀ GIỚI HẠN TOÁN TỬ ----
    y += 20
    f.text(10, y, "B. Căn chỉnh khối Channel (Tiling) và ràng buộc toán tử NPU RK3588", size=13.5, weight=700, fill=DARK)
    ch = 110
    rect(f, 10, y + 12, 870, ch, CALC, BLUE, 1.4, rx=6)
    txt(f, 24, y + 34, [
        [("Căn chỉnh bộ nhớ mảng MAC: ", "b"), ("Mảng tính toán NPU RK3588 tổ chức theo các khối channel sub-K = 32", "t")],
        [("(UG232 tr.49, Table 3-5 quy định shape hiệu năng cao Native như [K/32, M, 32] hoặc [N/64, K/32, 64, 32]).", "t")],
        [("Khuyến nghị thiết kế mô hình: ", "b"), ("Nên chọn số channel là bội số của 32 (ví dụ 32, 64, 128, 256) để đạt 100% hiệu suất", "t")],
        [("lấp đầy mảng PE; số channel lẻ buộc compiler phải chèn zero-padding gây lãng phí bộ đệm CBUF và chu kỳ.", "t")],
        [("Ràng buộc toán tử (OPL): ", "b"), ("exSDPAttention giới hạn channel ∈ (0, 8192] [OPL tr.104]; Softmax tính theo trục channel (axis 1) [OPL tr.89].", "t")],
    ], size=11.5, dy=17)
    y += 12 + ch

    # ---- C. UNKNOWN ----
    y += 16
    y = f.unknown(10, y, [
        "Vi kiến trúc cây cộng dồn channel (channel accumulation tree) nội bộ trong mảng MAC",
        "và cơ chế xử lý padding động khi C không chia hết cho 32 không được công bố chi tiết trong tài liệu vendor.",
    ], w=870)

    source(f, y + 8, "Nguồn: UG232 tr.49, tr.120; NAGEL tr.16; OPL tr.89, tr.104; TRM1 tr.1984.")
    return f


# =====================================================================
# HÌNH T.3: PHÂN LOẠI HAI HỌ KIỂU DỮ LIỆU VÀ ĐÁNH ĐỔI (T2 CHUNG)
# =====================================================================
def fig_classify():
    f = Fig(W, 720)
    tier(f, "T2 chung")
    f.text(10, 48, "Hai họ kiểu dữ liệu số và đánh đổi khi giảm số bit", size=16, weight=700)

    # ---- A. HAI HỌ KIỂU DỮ LIỆU ----
    f.text(10, 82, "A. Hai họ kiểu dữ liệu số trong mạng nơ-ron", size=13.5, weight=700, fill=DARK)
    y = f.table(10, 94, [70, 150, 70, 580], ["Kiểu", "Họ", "Số bit", "Điều nguồn cho (và nguồn)"], [
        ["FP32", "Dấu phẩy động", "32", ("lines", ["Tên kiểu dùng khi huấn luyện (float32); khi không lượng tử,", "weight được chuyển sang float16 [UG232 tr.165]"])],
        ["FP16", "Dấu phẩy động", "16", "Dải biểu diễn -65504 đến 65504; vượt dải thì tràn số [UG232 tr.133]"],
        ["BF16", "Dấu phẩy động", "16", "TRM và Datasheet liệt kê là kiểu phần cứng hỗ trợ [TRM1 tr.1984; DS tr.11]"],
        ["INT8", "Số nguyên", "8", "Số nguyên trên lưới lượng tử đều 2^b mức, có dấu hoặc không dấu [NAGEL tr.4, tr.5]"],
        ["INT4", "Số nguyên", "4", "16 mức; PTQ 4-bit trên YOLOv5s chỉ còn 7.0% mAP [NAGEL tr.4; QYOLO tr.2]"],
        ["INT16", "Số nguyên", "16", "TRM liệt kê là kiểu phần cứng hỗ trợ [TRM1 tr.1984]"],
    ], size=11.5, line_h=15)

    # ---- B. ĐÁNH ĐỔI KHI GIẢM SỐ BIT ----
    y += 20
    f.text(10, y, "B. Đánh đổi khi giảm số bit", size=13.5, weight=700, fill=DARK)
    y = f.table(10, y + 12, [210, 660], ["Khía cạnh", "Điều nguồn cho (và nguồn)"], [
        ["Bộ nhớ & độ trễ", ("lines", ["Số nguyên 4 bit trở xuống: lý thuyết giảm bộ nhớ và độ trễ tới 16 lần,", "thực tế thường 4-8 lần [GHOLAMI tr.1]"])],
        ["Năng lượng & diện tích", "Nhân INT8 tốn ít năng lượng và ít diện tích hơn nhân dấu phẩy động 16 bit IEEE 754 [TPU tr.1]"],
        ["Độ chính xác INT8 / FP16", ("lines", ["W8A8 thường trong khoảng 1% so FP32 [NAGEL tr.25]; không lượng tử: FP16 'almost no", "accuracy loss' [UG232 tr.165]"])],
        ["Độ chính xác INT4", ("lines", ["Weight 4-bit còn 'small additional drop' [NAGEL tr.25], nhưng EfficientDet-D1 W4A8", "per-tensor sụp còn 0.31 AP [NAGEL tr.17]; YOLOv5s PTQ 4-bit còn 7.0% mAP [QYOLO tr.2]"])],
    ], size=11.5, line_h=15)

    # ---- UNKNOWN ----
    y = f.unknown(10, y + 12, [
        "Cấu trúc bit chi tiết (bit dấu, số mũ, định trị) của FP32, FP16 và BF16 không có trong bộ nguồn.",
        "Nguồn chỉ cho tên kiểu, độ rộng và dải giá trị của FP16 (-65504 đến 65504).",
    ], w=870)

    source(f, y + 8, "Nguồn: TRM1 tr.1984; DS tr.11; UG232 tr.133, tr.165; NAGEL tr.4, tr.5, tr.17, tr.25; GHOLAMI tr.1; TPU tr.1; QYOLO tr.2.")
    return f


# =====================================================================
# HÌNH T.4: HỖ TRỢ PHẦN CỨNG RK3588 VÀ RKNN-TOOLKIT2 (T1 RK3588)
# =====================================================================
def fig_rk3588_dtypes():
    f = Fig(W, 760)
    tier(f, "T1 RK3588")
    f.text(10, 48, "Kiểu dữ liệu phần cứng RK3588 và ràng buộc của RKNN-Toolkit2", size=16, weight=700)

    # ---- A. THÔNG LƯỢNG MẢNG MAC ----
    f.text(10, 82, "A. Thông lượng mảng MAC của mỗi lõi (TRM1 tr.1984, ba lõi)", size=13.5, weight=700, fill=DARK)
    y = f.table(10, 94, [100, 160, 200, 410], ["Kiểu dữ liệu", "MACs / chu kỳ / lõi", "Tổng ba lõi (@ 1 GHz)", "Ý nghĩa hiệu năng"], [
        ["INT4", "2048x3 MACs", "12.288 TOPS (tính)", "Thông lượng cao nhất; rknn.config không hỗ trợ trực tiếp RK3588"],
        ["INT8", "1024x3 MACs", "6.144 TOPS (tính)", "Chuẩn suy luận chính; đạt mốc vendor 'up to 6TOPs' [DS tr.7]"],
        ["INT16", "512x3 MACs", "3.072 TOPS (tính)", "Độ chính xác cao hơn INT8; thông lượng giảm một nửa"],
        ["FP16 / BF16", "512x3 MACs", "3.072 TFLOPS (tính)", "Mặc định khi không lượng tử (do_quantization=False) [UG232 tr.165]"],
        ["TF32", "256x3 MACs", "1.536 TFLOPS (tính)", "Định dạng huấn luyện; thông lượng thấp nhất trong các kiểu"],
    ], size=11.5, line_h=15)

    # ---- B. RÀNG BUỘC CỦA RKNN-TOOLKIT2 ----
    y += 20
    f.text(10, y, "B. Ràng buộc cấu hình kiểu dữ liệu trong RKNN-Toolkit2", size=13.5, weight=700, fill=DARK)
    ch = 110
    rect(f, 10, y + 12, 870, ch, STAT, "#E65100", 1.4, rx=6)
    txt(f, 24, y + 34, [
        [("rknn.config mặc định: ", "b"), ("quantized_dtype='w8a8' (trọng số INT8, kích hoạt INT8); float_dtype='float16'.", "t")],
        [("Khi không lượng tử: ", "b"), ("Đặt do_quantization=False; model float được convert weight từ float32 sang float16", "t")],
        [("với độ mất chính xác gần như bằng không [UG232 tr.165] (NPU không hỗ trợ tính toán FP32).", "t")],
        [("Các kiểu bị giới hạn: ", "b"), ("quantized_dtype có w4a16 và w8a16 nhưng tài liệu API232 ghi dành cho chip khác", "t")],
        [("(RV1103/RV1106); trên RK3588 đường rknn.config thông thường chỉ dùng w8a8 hoặc float16.", "t")],
    ], size=11.5, dy=17)
    y += 12 + ch

    # ---- C. UNKNOWN ----
    y += 16
    y = f.unknown(10, y, [
        "Tần số xung nhịp tối đa của NPU được ghi 'TBD' trong Datasheet tr.31.",
        "Con số 6.144 TOPS ở trên là phép tính lý thuyết minh họa ở tần số ví dụ 1 GHz.",
    ], w=870)

    source(f, y + 8, "Nguồn: TRM1 tr.1984; DS tr.7, tr.11, tr.31; UG232 tr.165; API232 tr.7; BAMB tr.1.")
    return f


def main():
    figs = [
        ("ht-1-ban-chat-channel", fig_channel_basics),
        ("ht-2-channel-tren-npu-rk3588", fig_rk3588_channel),
        ("ht-3-phan-loai-va-tradeoff", fig_classify),
        ("ht-4-ho-tro-phan-cung-rk3588", fig_rk3588_dtypes),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()
