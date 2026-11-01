#!/usr/bin/env python3
"""Sinh trang 04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc.rst (giai đoạn 2d: tách đầu A1, QAT, bỏ DFL A2) từ kết quả đo, không gõ tay số.

Đọc results/{q2j_split,q2k_qat,q2k_qat_layers,q2l_nodfl}.json và các file xuất của run.
Chạy từ gốc repo chính:  .venv/bin/python docs/tools/gen_phase2d_results_page.py
Lời văn nằm trong script, mọi con số lấy từ file JSON. Các assert bảo vệ những số có trong lời văn.
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
RUNS = REPO / "ai" / "automation" / "runs"
OUT = REPO / "docs" / "contents" / "03-phuong-phap" / "04-tang-npu-ket-qua" / "07-ket-qua-qat-kien-truc.rst"
SILU, A2R = "ppe5_yolov8n_baseline_100ep_s0", "ppe5_yolov8n_nodfl_100ep_s0"

J = json.loads((RES / "q2j_split.json").read_text())
Q = json.loads((RES / "q2k_qat.json").read_text())
QL = json.loads((RES / "q2k_qat_layers.json").read_text())
N = json.loads((RES / "q2l_nodfl.json").read_text())
EXP_A2 = json.loads((RUNS / A2R / "export_int8.json").read_text())
EXP_SILU = json.loads((RUNS / SILU / "export_int8.json").read_text())
META_QAT = (RUNS / SILU / "weights" / "rknn_int8_qat" / "recipe.json")
RECIPE_QAT = json.loads(META_QAT.read_text())
CAL = ("11d6a5c69414a6eafd8b98f99724b0b2", "6652576adb7608ddf8ff326c57851732")
CRIT = 48.41


def f(x, d=2):
    return f"{x:.{d}f}"


def pm(x, d=2):
    return f"{x:+.{d}f}"


def table(headers, rows, widths=None):
    out = [".. list-table::", "   :header-rows: 1"]
    if widths:
        out.append("   :widths: " + " ".join(str(w) for w in widths))
    out.append("")
    for line in [headers] + rows:
        for i, cell in enumerate(line):
            out.append(("   * - " if i == 0 else "     - ") + str(cell))
    return "\n".join(out)


# ---- asserts on the facts the prose states
acc = J["accuracy"]["css_test"]
assert J["v_pc"]["max_abs"] < 0.01 and J["v_board"]["ok"] and J["s1"]["meets"]
assert acc["fp16"]["map50_95"] == 49.76 and acc["int8"]["map50_95"] == 36.75 and acc["int8h5"]["map50_95"] == 49.66
assert acc["split"]["map50_95"] == 49.84 and acc["fp16_split"]["map50_95"] == 49.94
assert J["coverage_split"]["cpu_ops"] == [] and J["coverage_split"]["dtypes"] == ["CPU|INT8", "NPU|INT8"] and J["coverage_split"]["rows"] == 106
assert all(c["realized"] for k, c in J["conditions"].items() if not k.startswith("int8|"))
assert not any(J["conditions"][k]["realized"] for k in ("int8|CORE_0", "int8|CORE_0_1_2"))
assert all(v["changes"] == "chưa kết luận" for v in J["cost"].values())
assert round(J["total"]["CORE_0"]["split_total_ms"], 2) == 21.09 and round(J["total"]["CORE_0"]["diff_vs_int8h5_ms"], 2) == 4.65
qa = Q["rknn_int8_qat"]
assert qa["map50_95"] == 49.85 and Q["statements"]["meets_48.41"] and Q["statements"]["Q-1_minus_split_ptq"] == 0.01
assert qa["sha256"] == hashlib.sha256((RUNS / SILU / "weights" / "rknn_int8_qat" / "best-rk3588.rknn").read_bytes()).hexdigest()
assert qa["sha256"] not in (Q["rknn_int8_split"]["sha256"], Q["rknn_int8"]["sha256"], Q["rknn_int8h5"]["sha256"])
qc = QL["qat"]["counts"]
assert qc == {"CPU|INT8": 3, "NPU|INT8": 103, "NPU|FLOAT16": 8} and QL["qat"]["rows"] == 114 and QL["qat"]["cpu_ops"] == []
assert QL["split_ptq"]["counts"] == {"CPU|INT8": 3, "NPU|INT8": 103} and QL["split_ptq"]["rows"] == 106
assert sorted(r["op"] for r in QL["qat"]["non_int8_npu"]) == ["Resize", "Resize", "exDataConvert", "exDataConvert", "exDataConvert", "exDataConvert", "exSwish", "exSwish"]
assert RECIPE_QAT["args"] == dict(run_id=SILU, epochs=6, batch=8, lr=0.0001, limit_batches=0, seed=0, no_rknn=False)
a2, sl = N["a2"], N["silu"]
assert N["reading"].startswith("within 1.35 of SiLU drop") and not N["n3_int8_ge_48_41"] and N["second_experiment_run"] is False
assert (N["drop_a2"], N["drop_silu"]) == (12.58, 13.01) and N["band"] == [11.66, 14.36]
assert a2["rknn_int8"]["map50_95"] == sl["rknn_int8"]["map50_95"] == 36.75 and a2["rknn_int8"]["sha256"] != sl["rknn_int8"]["sha256"]
assert a2["rknn_int8"]["map50"] != sl["rknn_int8"]["map50"]
assert (N["calibration"]["stems_md5"], N["calibration"]["png_md5"]) == CAL == (EXP_A2["calibration"]["stems_md5"], EXP_A2["calibration"]["png_md5"])
EXP_A2_16 = json.loads((RUNS / A2R / "export_fp16.json").read_text())
assert EXP_A2_16["rknn_sha256"] == a2["rknn_fp16"]["sha256"]
assert EXP_A2["rknn_sha256"] == N["rknn_sha256_int8"] == a2["rknn_int8"]["sha256"]
assert N["layers_int8"]["rows"] == 116 and N["layers_int8"]["counts"] == {"CPU|INT8": 2, "NPU|INT8": 114} and N["layers_int8"]["cpu_ops"] == []
assert N["layers_fp16"]["rows"] == 116 and N["transferred"].startswith("285/354")
fp16_gap = round(sl["rknn_fp16"]["map50_95"] - a2["rknn_fp16"]["map50_95"], 2)
assert fp16_gap == 0.43

A1 = acc
P = []
w = P.append
w("""*******************
Ứng viên INT8 thuần
*******************

.. admonition:: Trang này trả lời

   - Có model INT8 thuần (không tensor FP16 nào trong đồ thị NPU) đạt độ chính xác của FP16 mà không cần công thức lai ``int8h5`` không?
   - Ba ứng viên đã thử: tách đầu (A1), tinh chỉnh có lượng tử hóa (QAT, B) và bỏ DFL (A2). Mỗi ứng viên cho biết gì về nguyên nhân mất điểm của INT8 mặc định?

.. admonition:: Tóm tắt
""")
w(f"""
   - A1 tách đầu (PTQ, không huấn luyện lại, SiLU seed 0): AP50-95 trên ``css_test`` là {f(A1['split']['map50_95'])} (FP16 {f(A1['fp16']['map50_95'])}, ``int8h5`` {f(A1['int8h5']['map50_95'])}, INT8 mặc định {f(A1['int8']['map50_95'])}), đồ thị NPU toàn INT8, không op CPU. Phần NPU nhanh hơn ``int8h5`` khoảng {f(J['total']['CORE_0']['int8h5_ms'] - J['total']['CORE_0']['split_npu_ms'], 1)} ms nhưng giải mã box trên CPU tốn {f(J['decode']['median_ms'])} ms, nên tổng cộng chậm hơn khoảng {f(J['total']['CORE_0']['diff_vs_int8h5_ms'])} ms nếu không chồng lấp. Mọi so sánh thời gian mang nhãn "chưa kết luận" (hai phiên tham chiếu INT8 không thực hiện đúng dưới P2).
   - B QAT (6 epoch, 1 seed): AP50-95 {f(qa['map50_95'])}, hơn A1 {f(Q['statements']['Q-1_minus_split_ptq'])} điểm và hơn FP16 {f(Q['statements']['Q-1_minus_fp16'])} điểm, nằm trong nhiễu. Đồ thị RKNN của bản QAT không thuần INT8: có {qc['NPU|FLOAT16']} hàng FLOAT16 trên NPU. Với câu hỏi như đã viết (model INT8 thuần), câu trả lời của QAT là không, và QAT không thêm gì so với PTQ tách đầu.
   - A2 bỏ DFL (``reg_max`` 1, huấn luyện lại từ ``yolov8n.pt``): FP16 {f(a2['rknn_fp16']['map50_95'])}, INT8 mặc định {f(a2['rknn_int8']['map50_95'])}, mức rơi {f(N['drop_a2'])} điểm so với {f(N['drop_silu'])} điểm của SiLU. Theo bảng đọc viết trước, mức rơi nằm trong 1.35 điểm quanh mức của SiLU, nghĩa là bỏ DFL mà giữ phép giải mã trong đồ thị INT8 không tránh được mất điểm. Đây không phải cơ chế.
   - Chưa biết: nguyên nhân chính xác (phép giải mã hay lượng tử hóa đầu ra của lớp tích chập hồi quy ltrb), vì A2 mặc định không tách được hai thành phần này. Một seed, một run mỗi ứng viên.
""")
w("""
Kết quả chẩn đoán và công thức ``h5`` ở :doc:`05-ket-qua-luong-tu-hoa`, cách chạy lại ở :doc:`06-quy-trinh-tai-lap`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Câu hỏi, tiêu chí và nguồn
=============================
""")
w(f"""
Câu hỏi: model INT8 thuần có đạt độ chính xác của FP16 trên ``css_test`` không. Tiêu chí viết trước dữ liệu: AP50-95 từ {CRIT} trở lên, tức không thấp hơn FP16 seed 0 ({f(A1['fp16']['map50_95'])}) quá 1.35 điểm. Con số 1.35 là khoảng trải seed của INT8 SiLU ở :doc:`05-ket-qua-luong-tu-hoa`, đây là cách dùng mới và người dùng chưa duyệt. Nhãn cổng G4 đã duyệt không đổi, ba ứng viên này là phần bổ sung. Mốc tham chiếu: ``int8h5`` ({f(A1['int8h5']['map50_95'])}, lai, 15 tensor FP16) và INT8 mặc định ({f(A1['int8']['map50_95'])}).

Quy tắc viết trước dữ liệu nằm ở ``bench/onboard_q2c/rule_split.txt`` (A1), ``rule_qat.txt`` (B) và ``rule_nodfl.txt`` (A2) của run ``{SILU}``. Nguồn T1:

- Tách hậu xử lý khỏi đồ thị NPU có tiền lệ trong SDK: "Due to hardware limitations, the demo model moves the post-processing part of the yolov5 model to the cpu implementation by default." (``3rdparty/rknn-toolkit2/rknpu2/examples/rknn_yolov5_demo/README.md:13``).
- QAT trên RKNN-Toolkit2 đi qua giao diện FX: "RKNN currently supports quantized models generated from the FX interface, specifically the prepare_qat_fx interface and its associated interfaces." [T1 UG232 tr.127]. Khi nạp model đã QAT, đặt ``do_quantization=False`` (``examples/pytorch/resnet18_qat/README.md:18``).
- Phiên bản torch: "we recommend using PyTorch 1.10~1.13.1 to export the model" [T1 UG232 tr.156]. Repo dùng torch 2.4.0 cho cả huấn luyện và toolkit, nên đây là một khác biệt với khuyến nghị (xem mục 3).

Nguồn T2, chỉ để định vị, khác bộ dữ liệu và khác bộ lượng tử hóa nên không so trực tiếp. Bài YOLO26 báo bỏ DFL một mình làm mất 0.6 AP: "removing DFL alone costs 0.6 AP on the YOLO11s baseline (47.0 to 46.4)" [T2 Jocher 2026 tr.11] (COCO, FP, không nói INT8). Bài QARepVGG báo YOLOv6s-RepVGG giảm từ 42.4 xuống 35.0 sau PTQ INT8 còn YOLOv6s-QARepVGG từ 42.3 xuống 41.0 [T2 QAREP tr.7 Table 8] (COCO). Không có bài đã đọc đo mAP INT8 của YOLO khi bỏ DFL.

Phần bỏ DFL dựa trên mã Ultralytics 8.4.154 đã cài: tham số ``reg_max: 1`` của yaml YOLO26 (``cfg/models/26/yolo26.yaml:10``), ``Detect.dfl`` là ``nn.Identity()`` khi ``reg_max`` bằng 1 (``nn/modules/head.py:138``), độ rộng nhánh box ``c2 = max(16, ch[0] // 4, reg_max * 4)`` (``nn/modules/head.py:122``), ``reg_max`` đọc từ yaml (``nn/tasks.py:2014``) và hàm mất mát đổi tên cột ``dfl_loss`` thành ``l1_loss`` (``utils/loss.py:357-358``). Chỉ ``reg_max`` được mượn của YOLO26, ``end2end`` không.

2. A1: tách đầu, PTQ, không huấn luyện lại
=========================================
""")
w(f"""
``ai/automation/build_split.py`` xuất mô hình SiLU seed 0 đã fuse thành hai đầu ra thô qua ``forward_head`` của chính đầu Detect: ``boxes`` (1x64x8400, logit DFL) và ``scores`` (1x5x8400, logit class). Mô hình dựng bằng cấu hình INT8 của Ultralytics và danh sách hiệu chuẩn seed 0. Phần giải mã (kỳ vọng softmax DFL, xywh, nhân stride, sigmoid) chạy bằng numpy trên CPU (``ai/board/split_decode.py``). Hai kiểm tra hợp lệ viết trước khi đọc số INT8 đều qua: giải mã float của ONNX so với ``output0`` của ONNX chuẩn lệch tối đa {J['v_pc']['max_abs']:.1e} (giới hạn 0.01), và model FP16 tách đầu cho {f(A1['fp16_split']['map50_95'])} trên ``css_test`` so với {f(A1['fp16']['map50_95'])} của FP16 chuẩn (giới hạn chênh 1.35).

Độ chính xác trên ``css_test`` (AP50-95, điểm):
""")
w(table(["Model", "AP50-95", "AP50", "NoHelmet", "Vest"],
        [[lab, f(A1[k]["map50_95"]), f(A1[k]["map50"]), f(A1[k]["NoHelmet"]), f(A1[k]["Vest"])] for lab, k in
         (("FP16 chuẩn", "fp16"), ("FP16 tách đầu", "fp16_split"), ("INT8 mặc định", "int8"), ("INT8 ``int8h5`` (lai)", "int8h5"), ("INT8 tách đầu (A1)", "split"))], [34, 14, 14, 14, 14]))
w(f"""

Đồ thị NPU của A1 có {J['coverage_split']['rows']} hàng, toàn INT8 và không op CPU ngoài Input và Output. INT8 tách đầu hơn FP16 {pm(J['s1']['split_minus_fp16'])} điểm và hơn ``int8h5`` {pm(J['s1']['split_minus_int8h5'])} điểm, đạt tiêu chí. Cách đọc viết trước: ``h5`` giữ logit DFL và phép tính giải mã ở FP16 cùng lúc, còn mô hình tách đầu đưa logit DFL về INT8 và chỉ chuyển phần tính toán sang float. Vì tách đầu đạt, theo cách đọc đó phần đuôi tính toán của giải mã được ủng hộ là nguồn mất điểm, còn việc lượng tử hóa logit DFL thì không được ủng hộ. Đây không phải cơ chế.

Thời gian (một lần chạy xen kẽ dưới P2, SiLU seed 0, ``bench/onboard_q2j``). Hai phiên tham chiếu của model ``int8`` mặc định không thực hiện đúng P2 nên mọi hàng so với ``int8`` mang nhãn "chưa kết luận". Các phiên của ``int8h5`` và A1 thực hiện đúng:
""")
cs = J["conditions"]
w(table(["Model", "CORE_0 (ms)", "CORE_0_1_2 (ms)", "P2 thực hiện đúng"],
        [[lab, f(cs[f"{k}|CORE_0"]["median"], 3), f(cs[f"{k}|CORE_0_1_2"]["median"], 3), "có" if cs[f"{k}|CORE_0"]["realized"] and cs[f"{k}|CORE_0_1_2"]["realized"] else "không"]
         for lab, k in (("INT8 mặc định", "int8"), ("``int8h5``", "int8h5"), ("A1 tách đầu (chỉ phần NPU)", "split"))], [40, 20, 24, 24]))
w(f"""

Giải mã CPU bằng numpy: trung vị {f(J['decode']['median_ms'])} ms, p95 {f(J['decode']['p95_ms'], 3)} ms trên 200 lần (``ai/board/bench_decode.py``, ghim CPU4, tần số khóa). Tổng ở ``CORE_0`` là {f(J['total']['CORE_0']['split_npu_ms'])} + {f(J['decode']['median_ms'])} = {f(J['total']['CORE_0']['split_total_ms'])} ms so với {f(J['total']['CORE_0']['int8h5_ms'], 3)} ms của ``int8h5``. Đây là tổng của hai trung vị đo riêng (NPU dưới P2, giải mã trên CPU), không phải phép đo từ đầu đến cuối. Nếu giải mã chồng lấp với suy luận ảnh kế tiếp thì thông lượng cao hơn: điều này đã đo sau đó ở :doc:`09-ket-qua-don-bay-fps` (một context đạt 65.99 FPS), còn thời gian mỗi khung thì không giảm. Bản giải mã C hay NEON có thể nhanh hơn numpy, cũng không được đo.

3. B: QAT
=========
""")
w(f"""
Phương pháp (``ai/core/rknn/qat_split.py``, ``ai/automation/qat_split.py``): mô hình tách đầu (hai đầu ra thô), đầu vào FX trace qua một lớp bọc tường minh (các phép cắt tĩnh của C2f, đầu trả hai tensor), ``prepare_qat_fx`` với qconfig của tr.127 (activation ``FakeQuantize`` ``MovingAverageMinMaxObserver`` từ 0 đến 255, trọng số per-channel affine int8), tinh chỉnh {RECIPE_QAT['args']['epochs']} epoch, batch {RECIPE_QAT['args']['batch']} (batch 16 hết bộ nhớ GPU 4 GB), SGD lr {RECIPE_QAT['args']['lr']}, tắt observer từ epoch 5, đóng băng thống kê BN từ epoch 6, hàm mất mát phát hiện của Ultralytics trên đầu ra thô. Sau đó ``convert_fx``, ``torch.jit.trace``, ``load_pytorch`` và ``build`` với ``do_quantization=False``. Siêu tham số không đổi sau khi thấy kết quả. Loss trung bình mỗi epoch: {', '.join(f(e['mean_loss'], 3) for e in RECIPE_QAT['log'])}.

Phiên bản torch 2.4.0 khác khuyến nghị 1.10 đến 1.13.1 của tr.156. Chuỗi trace, TorchScript, nạp và dựng chạy được trên torch 2.4.0 nên khác biệt này không gây lỗi. Ảnh hưởng của nó lên độ chính xác thì chưa biết.

Độ chính xác trên ``css_test``: AP50-95 {f(qa['map50_95'])} (AP NoHelmet {f(qa['per_class']['NoHelmet'])}, AP Vest {f(qa['per_class']['Vest'])}), hơn FP16 {pm(Q['statements']['Q-1_minus_fp16'])}, hơn A1 PTQ tách đầu {pm(Q['statements']['Q-1_minus_split_ptq'])}, hơn ``int8h5`` {pm(Q['statements']['Q-1_minus_int8h5'])} và hơn INT8 mặc định {pm(Q['statements']['Q-1_minus_int8'])} điểm. Đạt tiêu chí {CRIT}. Tiêu chí mới và chưa duyệt, và một run, một seed.

Câu hỏi của quy tắc gồm hai vế: đạt FP16 và đồ thị INT8 thuần. Vế độ chính xác đạt. Vế đồ thị không đạt: bảng layer của bản dựng có {QL['qat']['rows']} hàng, {qc['NPU|INT8']} hàng NPU INT8, {qc['NPU|FLOAT16']} hàng NPU FLOAT16 (2 ``exSwish``, 2 ``Resize``, 4 ``exDataConvert``) và {qc['CPU|INT8']} hàng CPU (Input và các hàng Output, A1 và QAT có hai đầu ra) so với {QL['split_ptq']['rows']} hàng toàn INT8 của A1. Nguyên nhân các hàng FP16 chưa biết, hướng dẫn nói op không đạt quy tắc lượng tử hóa giữ tính toán FP32 (tr.128) và ``exDataConvert`` được chèn quanh một số op (tr.130), không có danh sách op cụ thể. Thời gian NPU và độ phủ đa nhân của bản QAT đo sau đó ở :doc:`08-so-muc-chua-biet` mục 9 (ngoài ngân sách của quy tắc ban đầu). Kết luận: với câu hỏi như đã viết, QAT trả lời không, và độ chính xác ngang A1 nên QAT không thêm gì.

4. A2: bỏ DFL (reg_max 1)
=========================
""")
w(f"""
A2 huấn luyện lại ``ai/models/yolov8n_nodfl.yaml`` (yaml gốc ``yolov8.yaml`` thêm ``scale: n`` và ``reg_max: 1``) từ ``yolov8n.pt``, cùng cấu hình với baseline (``ppe5``, 100 epoch, seed 0, SiLU), xuất mặc định của Ultralytics (giải mã trong đồ thị, không công thức lai, vì ``h5`` cần 4 tensor DFL không còn) với danh sách hiệu chuẩn seed 0 (``stems_md5`` ``{CAL[0]}``, ``png_md5`` ``{CAL[1]}``). Kiểm tra trước trên model chưa huấn luyện: đầu ra 1x9x8400, 116 hàng toàn INT8, không op CPU.

Yếu tố gây nhiễu cần biết: với ``reg_max`` 1, cả nhánh box ``cv2`` thu từ 64 xuống 16 kênh (``head.py:122``), nên toàn bộ nhánh box khởi tạo ngẫu nhiên, chỉ {N['transferred']} chuyển từ ``yolov8n.pt``. A2 là một model khác chứ không chỉ khác ở phép giải mã. Số liệu: FP16 của A2 là {f(a2['rknn_fp16']['map50_95'])}, thấp hơn FP16 SiLU seed 0 {f(fp16_gap)} điểm, trong khi khoảng trải seed của FP16 SiLU là 1.25 điểm. mAP50-95 trên tập validation ở epoch cuối là {f(N['val_map50_95_a2']['final'], 4)} (A2) và {f(N['val_map50_95_silu']['final'], 4)} (SiLU).

Độ chính xác trên ``css_test`` (AP50-95, điểm), cùng đường đo trên board:
""")
w(table(["Model", "FP32 (PyTorch)", "FP16", "INT8 mặc định", "Mức rơi FP16 xuống INT8"],
        [["SiLU baseline seed 0", f(sl["pt_fp32"]["map50_95"]), f(sl["rknn_fp16"]["map50_95"]), f(sl["rknn_int8"]["map50_95"]), f(N["drop_silu"])],
         ["A2 bỏ DFL", f(a2["pt_fp32"]["map50_95"]), f(a2["rknn_fp16"]["map50_95"]), f(a2["rknn_int8"]["map50_95"]), f(N["drop_a2"])]], [30, 18, 14, 18, 28]))
w(f"""

Hai số INT8 trùng nhau đến hai chữ số thập phân ({f(a2['rknn_int8']['map50_95'])}) là trùng nhau, không có liên hệ nào được đo. Hai file khác nhau (sha256 khác), AP50 khác ({f(a2['rknn_int8']['map50'])} và {f(sl['rknn_int8']['map50'])}) và AP từng lớp khác. Đồ thị INT8 của A2 có {N['layers_int8']['rows']} hàng, {N['layers_int8']['counts']['NPU|INT8']} hàng NPU INT8, không op CPU ngoài Input và Output.

Bảng đọc viết trước: mức rơi nhỏ hơn hoặc bằng 1.35 thì phần DFL bị liên quan. Mức rơi trong 1.35 quanh {f(N['drop_silu'])} (từ {f(N['band'][0])} đến {f(N['band'][1])}) thì phép giải mã trong INT8 đủ để gây mất điểm kể cả khi không có DFL, phù hợp với cách đọc của A1. Mức rơi giữa hai khoảng là một phần, không gán nhãn. Mức rơi {f(N['drop_a2'])} nằm trong khoảng thứ hai. Tiêu chí tuyệt đối {CRIT} không đạt (INT8 {f(a2['rknn_int8']['map50_95'])}), tiêu chí này phụ thuộc cả mức FP16 của A2.

Giới hạn của cách đọc: A2 mặc định không tách được lượng tử hóa đầu ra của lớp tích chập hồi quy ltrb khỏi các phép tính của phần đuôi giải mã. Lần chạy A2 tách đầu (quy tắc mới, :doc:`08-so-muc-chua-biet` mục 9) tách được hai thành phần này và cho kết quả đạt tiêu chí.

5. Tổng hợp ba ứng viên
=======================
""")
w(table(["Ứng viên", "AP50-95 INT8", "Đồ thị INT8 thuần", "Chi phí và điều kiện"],
        [["A1 tách đầu (PTQ)", f(A1["split"]["map50_95"]), "có (106 hàng INT8)", f"NPU nhanh hơn ``int8h5`` {f(J['total']['CORE_0']['int8h5_ms'] - J['total']['CORE_0']['split_npu_ms'], 1)} ms, giải mã CPU {f(J['decode']['median_ms'])} ms, tổng chậm hơn {f(J['total']['CORE_0']['diff_vs_int8h5_ms'])} ms nếu không chồng lấp. Không cần huấn luyện"],
         ["B QAT", f(qa["map50_95"]), f"không ({qc['NPU|FLOAT16']} hàng FP16)", f"6 epoch huấn luyện ({sum(e['seconds'] for e in RECIPE_QAT['log']) / 60:.1f} phút). Thời gian NPU ở :doc:`08-so-muc-chua-biet` mục 9. Không hơn A1"],
         ["A2 bỏ DFL", f(a2["rknn_int8"]["map50_95"]), "có (114 hàng INT8)", "Huấn luyện lại 100 epoch. Không giảm mức rơi INT8 mặc định"],
         ["``int8h5`` (tham chiếu)", f(A1["int8h5"]["map50_95"]), "không (15 tensor FP16)", "Không tốn latency đo được (:doc:`05-ket-qua-luong-tu-hoa`)"]], [24, 16, 24, 60]))
w("""

Đọc chung, trong giới hạn của mỗi ứng viên một seed: trong các ứng viên đã thử, chỉ A1 cho model INT8 thuần đạt FP16, và đó là bản có phần đuôi giải mã nằm ngoài đồ thị NPU (không có phép đo nào kiểm điều kiện cần). Giải mã chuyển sang CPU làm tổng thời gian dài hơn ``int8h5`` ở phép đo này. Công thức lai ``int8h5`` vẫn là cách đạt độ chính xác FP16 mà đồ thị còn trên NPU, với 15 tensor FP16 ở phần đuôi. QAT 6 epoch không thêm gì so với PTQ ở cấu hình đã thử. Bỏ DFL không giảm mức rơi.

6. Chưa biết và giới hạn
========================

- Nguyên nhân chính xác của mức rơi INT8 mặc định: chưa biết. A2 mặc định không tách được các thành phần của phần đuôi giải mã (phép trừ, cộng, chia, nối với điểm class, nhân stride) khỏi lượng tử hóa đầu ra của lớp hồi quy.
- QAT với torch 1.10 đến 1.13.1 (khuyến nghị tr.156): không chạy, cần bộ công cụ thứ hai (:doc:`08-so-muc-chua-biet` mục 8). Nguyên nhân 8 hàng FP16 của bản QAT: vẫn chưa biết (vị trí đã mô tả ở :doc:`08-so-muc-chua-biet` mục 9). Thời gian NPU và độ phủ của bản QAT đã đo ở :doc:`08-so-muc-chua-biet` mục 9.
- Giải mã chồng lấp với suy luận kế tiếp đã đo ở :doc:`09-ket-qua-don-bay-fps`. Giải mã bằng C hay NEON không chạy vì điều kiện kích hoạt viết trước không xảy ra, nên chưa đo.
- Một seed, một run mỗi ứng viên, chỉ SiLU, một board, giao thức đo thời gian P2 (đã duyệt ngày 2026-11-01). Tiêu chí 48.41 mới và chưa duyệt.
- A2 là model khác (nhánh box khởi tạo ngẫu nhiên). A2 tách đầu đã chạy sau đó (:doc:`08-so-muc-chua-biet` mục 9): INT8 đạt FP16, ủng hộ cách đọc phép giải mã.

7. Tái lập
==========

Mọi lệnh chạy từ gốc repo chính, board đã khóa tần số và có ``rknn_server`` (:doc:`06-quy-trinh-tai-lap`). Quy tắc viết trước nằm ở ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2c/`` (``rule_split.txt``, ``rule_qat.txt``, ``rule_nodfl.txt``).

.. code-block:: bash

   # A1: xuất tách đầu (int8 và fp16), chấm mAP trên board (FP16 tách đầu là kiểm tra hợp lệ V-board, chấm trước số INT8)
   .venv/bin/python -m ai.automation.build_split ppe5_yolov8n_baseline_100ep_s0 int8
   .venv/bin/python -m ai.automation.build_split ppe5_yolov8n_baseline_100ep_s0 fp16
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_baseline_100ep_s0 --backend rknn --precision fp16 --variant split --board minhnhat@192.168.137.49 --board-repo rk3588
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_baseline_100ep_s0 --backend rknn --precision int8 --variant split --board minhnhat@192.168.137.49 --board-repo rk3588
   # A1: thời gian. Phần NPU dưới P2 (benchmark_npu --variant split, xen kẽ với int8 và int8h5, theo quy tắc rule_split.txt mục S-3),
   # giải mã CPU ghim CPU4 (ai/board/bench_decode.py chạy trên board), rồi phân tích
   .venv/bin/python -m ai.automation.analyze_q2j
   # B: QAT rồi chấm mAP
   RKNN_LOG_LEVEL=3 .venv/bin/python -m ai.automation.qat_split ppe5_yolov8n_baseline_100ep_s0 --epochs 6 --batch 8
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_baseline_100ep_s0 --backend rknn --precision int8 --variant qat --board minhnhat@192.168.137.49 --board-repo rk3588
   # A2: huấn luyện, xuất (INT8 dùng danh sách hiệu chuẩn của seed 0), chấm mAP
   make train CONFIG=ai/automation/configs/ppe5_yolov8n_nodfl.yaml
   .venv/bin/python -m ai.automation.export_npu ppe5_yolov8n_nodfl_100ep_s0 --quantize 16
   .venv/bin/python -m ai.automation.export_npu ppe5_yolov8n_nodfl_100ep_s0 --quantize 8 --calib-from ppe5_yolov8n_baseline_100ep_s0
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_nodfl_100ep_s0 --backend rknn --precision fp16 --board minhnhat@192.168.137.49 --board-repo rk3588
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_nodfl_100ep_s0 --backend rknn --precision int8 --board minhnhat@192.168.137.49 --board-repo rk3588
   # QAT và A2: bảng số liệu (đọc các file eval và log xuất trong repo)
   .venv/bin/python -m ai.automation.analyze_q2kl

``make export-npu PREC=int8`` chỉ truyền ``--calib-from`` khi có ``CALIB_FROM=<run>`` (từ 2026-11-01, ``pipeline.py`` luôn truyền). Không có biến này, với run A2 nó sẽ lấy mẫu một danh sách hiệu chuẩn mới. Dùng lệnh ``export_npu`` ở trên, hoặc ``make export-npu RUN=ppe5_yolov8n_nodfl_100ep_s0 PREC=int8 CALIB_FROM=ppe5_yolov8n_baseline_100ep_s0``, để giữ danh sách của seed 0.

Số liệu: ``results/q2j_split.json`` (A1, ``analyze_q2j.py``), ``results/q2k_qat.json`` và ``results/q2k_qat_layers.json`` (QAT, ``analyze_q2kl.py``), ``results/q2l_nodfl.json`` (A2, ``analyze_q2kl.py``). Log: ``bench/onboard_q2c/logs/`` (``qat_train.log``, ``evaluate_qat_int8.log``, ``a2_precheck_untrained_export.log``) và ``runs/ppe5_yolov8n_nodfl_100ep_s0/logs/``. Thiết kế: ``results/phase2d_design.md``, nguồn: ``results/phase2d_source_facts.md``. Sinh trang này: ``.venv/bin/python docs/tools/gen_phase2d_results_page.py``.
""")
text = "\n".join(P).replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
lines = text.split("\n")
for i in range(1, len(lines)):  # underline of each section title as wide as the title
    if lines[i] and set(lines[i]) == {"="} and lines[i - 1]:
        lines[i] = "=" * (len(lines[i - 1]) + 2)
OUT.write_text("\n".join(lines))
print("wrote", OUT, OUT.stat().st_size)
