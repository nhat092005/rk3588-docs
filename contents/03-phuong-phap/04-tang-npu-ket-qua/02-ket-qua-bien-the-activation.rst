*******************
Biến thể activation
*******************

.. admonition:: Trang này trả lời

   - LeakyReLU, ReLU6 và ReLU huấn luyện 200 epoch có qua cổng G4 (A phủ đa nhân, B latency, C mAP) khi thay SiLU của YOLOv8n ppe5 không, nhãn của từng biến thể là gì?
   - Huấn luyện dài hơn có lấy lại mAP của ReLU không, và có tách được ảnh hưởng của số epoch khỏi ảnh hưởng của activation không (đối chứng SiLU 200 epoch)?
   - Latency và độ phủ đa nhân của các biến thể so với SiLU và ReLU là bao nhiêu?

.. admonition:: Tóm tắt


   - LeakyReLU (0.1): cổng C không đạt (AP50-95 -2.64, AP NoHelmet -5.00, AP Vest -3.98 điểm so với SiLU seed 0). Nhãn: **Loại** (bước C).
   - ReLU6: cổng C không đạt (AP50-95 -3.63, AP NoHelmet -0.36, AP Vest -3.40 điểm so với SiLU seed 0). Nhãn: **Loại** (bước C).
   - ReLU 200 epoch: cổng C đạt (AP50-95 -0.57, AP NoHelmet +1.57, AP Vest +1.10 điểm so với SiLU seed 0). Nhãn: **Chưa biết** (bước G1).
   - Huấn luyện 200 epoch đưa ReLU từ -3.51 xuống -0.57 điểm AP50-95 so với SiLU 100 epoch. So với đối chứng SiLU 200 epoch, ReLU 200 epoch chênh -1.78 điểm. Chính SiLU 200 epoch chênh +1.21 điểm so với SiLU 100 epoch. Vì vậy câu đúng là ``ReLU 200 epoch đạt cổng C so với SiLU 100 epoch``, không phải ``đổi activation đạt``.
   - Cả ba biến thể nhanh hơn ở ``CORE_0_1_2`` so với ``CORE_0`` khoảng 32.8 đến 33.5% (hai thí nghiệm) và độ phủ đa nhân 97.6% (SiLU 1.8%). Hai lần chạy latency xen kẽ, mỗi mô hình có ít nhất một lần thực hiện đúng giao thức P2.
   - Mọi ứng viên là 1 seed, giao thức P2 đã duyệt ngày 2026-11-01. Độ dốc LeakyReLU 0.1 là một điểm do dự án chọn, không quét. Hardswish, GELU, Mish không thử vì không nằm trong danh sách op đa nhân của T1.

Kết quả của ReLU gốc, nhiễu seed và cổng ở :doc:`01-ket-qua-g4`. Đa nhân S1 đến S3 ở :doc:`03-ket-qua-da-nhan`. Mọi số INT8 ở trang này dùng công thức lượng tử hóa mặc định của Ultralytics. Trang :doc:`05-ket-qua-luong-tu-hoa` cho thấy công thức ``h5`` lấy lại gần hết mức rơi INT8 so với FP16, và cổng C dưới ``h5`` nằm ở mục 5 của trang đó.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Ứng viên và điều kiện
========================

Mỗi ứng viên là YOLOv8n ppe5, seed 0, khởi tạo từ trọng số ``yolov8n.pt`` (SiLU) nạp vào kiến trúc mới, cùng cài đặt huấn luyện Ultralytics của baseline, chỉ khác file yaml mô hình và số epoch. INT8 dùng danh sách hiệu chuẩn của seed 0 (``stems_md5`` và ``png_md5`` giống hệt như ở :doc:`01-ket-qua-g4`). Quy tắc viết trước dữ liệu: ``bench/eval_g4/rule_variants.txt`` (mAP), ``bench/onboard_g4v/rule.txt`` (latency, thí nghiệm 1 và 2). Cổng C của mọi ứng viên so với SiLU seed 0 huấn luyện 100 epoch (baseline đã duyệt).


.. list-table::
   :header-rows: 1
   :widths: 22 22 8 44 16

   * - Ứng viên
     - Activation
     - Epoch
     - Run
     - INT8 sha256 (8 ký tự đầu)
   * - SiLU (baseline)
     - ``SiLU``
     - 100
     - ``ppe5_yolov8n_baseline_100ep_s0``
     - a501f94e
   * - ReLU (:doc:`01-ket-qua-g4`)
     - ``nn.ReLU()``
     - 100
     - ``ppe5_yolov8n_relu_100ep_s0``
     - c36458b7
   * - LeakyReLU (0.1)
     - ``nn.LeakyReLU(0.1)``
     - 100
     - ``ppe5_yolov8n_leakyrelu_100ep_s0``
     - 7a1f6167
   * - ReLU6
     - ``nn.ReLU6()``
     - 100
     - ``ppe5_yolov8n_relu6_100ep_s0``
     - 0ea9b44c
   * - ReLU 200 epoch
     - ``nn.ReLU()``
     - 200
     - ``ppe5_yolov8n_relu_200ep_s0``
     - 6860ac8f
   * - SiLU 200 epoch (đối chứng)
     - ``SiLU``
     - 200
     - ``ppe5_yolov8n_baseline_200ep_s0``
     - 7a1e0f66

Độ dốc 0.1 của LeakyReLU là lựa chọn của dự án, theo quy ước của cấu hình Darknet YOLO, không lấy từ T1 hay T2 (mục T1 của LeakyReLU không có ràng buộc về độ dốc). Không quét độ dốc. Mốc kiểm tra trước khi huấn luyện (``val`` mAP50-95 trong ``metrics.csv`` của hai run 100 epoch, ``val`` mAP50-95 của cả hai còn tăng ròng từ epoch 90 đến 100, có dao động giữa các epoch) là lý do chọn thử 200 epoch. ``metrics.csv`` của ReLU 200 epoch có đủ 200 dòng.

2. G1 theo tên op
=================

Quy tắc ánh xạ (viết trước dữ liệu, giống ReLU): tên op sau khi compiler gộp ánh xạ theo tên sang mục ``ConvolutionXxx`` của Operator List. Tên có ``Add`` (``ConvLeakyReluAdd``, ``ConvReluAdd``) không có mục cùng tên, nên G1 chỉ qua một phần và nhãn tối đa là "Chưa biết" dù A, B, C đạt. Quy tắc này do dự án viết trong ``rule_variants.txt`` trước khi có dữ liệu, không nằm trong chuẩn ở :doc:`../03-tang-npu-don-bay/01-operator-support` mục 2 (chuẩn chỉ nói "Chưa biết" khi chưa chạy hết các bước). Nguồn T1 do doc-reader trích:

.. list-table::
   :header-rows: 1
   :widths: 30 70 24

   * - Việc
     - Kết quả
     - Nguồn
   * - ``ConvolutionPRelu/LeakyRelu`` (3.2.9)
     - Có mục: ``Output = LeakyRelu(Conv(Input))``, ``说明及规格限制同Convolution``, ``多核联合: 支持``, không có ràng buộc độ dốc
     - [T1 OPL tr.61]
   * - ``ConvolutionClip`` (3.2.8)
     - Có mục: ``Output = Clip(Conv(Input))``, ``多核联合: 支持``. Mục ``Clip/ReLU6`` đứng riêng (3.2.50) ghi phạm vi [0, 6]
     - [T1 OPL tr.61, tr.84]
   * - Mục gộp ``Add`` với LeakyRelu hoặc Clip
     - Không có mục nào trong chương 3.2. Chỉ có ``ConvolutionAdd`` (3.2.10, ``多核联合: 支持``) và ``ConvolutionAddRelu`` (3.2.19)
     - [T1 OPL tr.61, tr.63]
   * - Op đứng riêng ``Relu``, ``Clip/ReLU6``, ``PRelu``, ``LeakyRelu``
     - Cả bốn ghi ``多核联合: 暂不支持`` (tr.84 đến 86), trong khi SDK guide tr.75 và API guide tr.27 liệt kê chúng là op đa nhân. Không nguồn nào giải thích
     - [T1 OPL tr.84 đến 86] [T1 UG232 tr.75] [T1 UG152 tr.27]
   * - ``ConvClip`` trong ví dụ của hãng
     - Có trong bảng layer ví dụ của SDK guide (``ConvClip``, INT8)
     - [T1 UG232 tr.56 đến 57]
   * - Luật gộp cứng của phần cứng
     - SDK guide tr.142, cột ``Supported fusion rules``, liệt kê ``Conv+Relu``, ``Conv+PRelu(LeakyRelu)``, ``Conv+Clip``, ``Conv+Add`` và ``Conv+Activation+Add``. Phù hợp với ``ConvReluAdd`` và ``ConvLeakyReluAdd`` quan sát được trong bảng build. Đây là luật gộp, không phải mục Operator List tên ``ConvXxxAdd`` có dòng ``多核联合``, nên không đổi quy tắc ánh xạ G1
     - [T1 UG232 tr.142]

G1 theo quy tắc ánh xạ: LeakyReLU qua một phần (``ConvLeakyReluAdd`` 6 dòng không có mục), ReLU6 qua (``ConvClip`` ánh xạ sang ``ConvolutionClip``, không có dòng gộp ``Add``), ReLU 200 epoch qua một phần (cùng kiến trúc ReLU, ``ConvReluAdd``).

3. G3: bảng build
=================

Bảng layer của build INT8 và FP16 đã huấn luyện (kiểm sơ bộ trên trọng số chưa huấn luyện cho cùng tên op trước khi huấn luyện, không phải kết luận):

.. list-table::
   :header-rows: 1
   :widths: 18 40 12 12 30

   * - Mô hình
     - Op gộp
     - Số dòng INT8
     - Số dòng FP16
     - Op CPU ngoài Input, Output (INT8, FP16)
   * - SiLU
     - ``ConvExSwish`` 57
     - 119
     - 119
     - ['Transpose'], ['Transpose']
   * - ReLU
     - ``ConvRelu`` 51, ``ConvReluAdd`` 6
     - 113
     - 113
     - ['Transpose'], ['Transpose']
   * - LeakyReLU
     - ``ConvLeakyRelu`` 51, ``ConvLeakyReluAdd`` 6
     - 113
     - 113
     - ['Transpose'], ['Transpose']
   * - ReLU6
     - ``ConvClip`` 57
     - 119
     - 119
     - ['Transpose'], ['Transpose']
   * - ReLU 200 epoch
     - ``ConvRelu`` 51, ``ConvReluAdd`` 6
     - 113
     - 113
     - ['Transpose'], ['Transpose']

Kết quả G3: cả ba biến thể qua (chỉ ``Transpose`` ở CPU, như SiLU).

4. Điều kiện A và B: độ phủ đa nhân và latency
==============================================

Quy tắc như ở :doc:`01-ket-qua-g4` (mục 3 và 4), chạy xen kẽ dưới P2: hai mask ``CORE_0`` và ``CORE_0_1_2``, năm mô hình, hai vòng cùng thứ tự, 45 giây nghỉ. Thí nghiệm 1 (``onboard_g4v``) có một phiên SiLU không thực hiện đúng P2 (một mẫu giây có một luồng ``rknn_server`` chưa ở CPU4, ngắt vẫn 100% ở CPU4). Theo quy tắc viết trước, đó là điều kiện để chạy thí nghiệm 2 (``onboard_g4v2``, lặp lại nguyên thiết kế). Thí nghiệm 2 có ba phiên không thực hiện đúng ở các mô hình khác (cùng loại: một mẫu giây có một luồng ngoài CPU4). Ngân sách của giai đoạn là tối đa hai thí nghiệm cho mỗi việc, nên không chạy thêm. Mỗi mô hình có ít nhất một thí nghiệm mà cả hai mask thực hiện đúng, và kết quả B giữa các thí nghiệm hợp lệ không mâu thuẫn. Bảng ghi cả hai.

.. list-table::
   :header-rows: 1
   :widths: 18 10 14 16 10 20 24 12

   * - Mô hình
     - Thí nghiệm
     - ``CORE_0`` (ms)
     - ``CORE_0_1_2`` (ms)
     - Giảm (%)
     - Chênh hai phiên lớn nhất (ms)
     - Kết quả B
     - Độ phủ A
   * - SiLU
     - 1
     - 16.508
     - 16.024
     - 2.93
     - 0.014
     - chưa kết luận (P2 không thực hiện đúng)
     - 1.8%
   * - SiLU
     - 2
     - 16.542
     - 16.038
     - 3.05
     - 0.012
     - không nhanh hơn
     - 1.8%
   * - ReLU
     - 1
     - 12.837
     - 8.549
     - 33.40
     - 0.018
     - nhanh hơn
     - 97.6%
   * - ReLU
     - 2
     - 12.857
     - 8.561
     - 33.41
     - 0.021
     - chưa kết luận (P2 không thực hiện đúng)
     - 97.6%
   * - LeakyReLU
     - 1
     - 12.850
     - 8.541
     - 33.53
     - 0.038
     - nhanh hơn
     - 97.6%
   * - LeakyReLU
     - 2
     - 12.862
     - 8.555
     - 33.49
     - 0.014
     - chưa kết luận (P2 không thực hiện đúng)
     - 97.6%
   * - ReLU6
     - 1
     - 13.050
     - 8.744
     - 33.00
     - 0.037
     - nhanh hơn
     - 97.6%
   * - ReLU6
     - 2
     - 13.059
     - 8.772
     - 32.83
     - 0.029
     - nhanh hơn
     - 97.6%
   * - ReLU 200 epoch
     - 1
     - 12.843
     - 8.540
     - 33.50
     - 0.027
     - nhanh hơn
     - 97.6%
   * - ReLU 200 epoch
     - 2
     - 12.854
     - 8.543
     - 33.54
     - 0.012
     - nhanh hơn
     - 97.6%

Mô tả: ở ``CORE_0`` (thí nghiệm 1) LeakyReLU nhanh hơn SiLU 22.2%, ReLU6 20.9%, ReLU 22.2%, ReLU 200 epoch 22.2%. ReLU 100 epoch và 200 epoch có cùng kiến trúc và cùng latency (chênh 0.006 ms), nên số epoch không đổi tốc độ. ReLU6 chậm hơn ReLU khoảng 0.21 ms ở ``CORE_0`` (nguyên nhân chưa biết, bảng build ReLU6 có 119 dòng với 8 ``Add`` riêng so với 113 dòng của ReLU).
Điều kiện A đạt cho cả ba biến thể (97.6%), điều kiện B đạt cho cả ba ở ít nhất một thí nghiệm hợp lệ.

5. Điều kiện C: mAP
===================

Chấm bằng RKNNLite trên board, ``css_test`` (82 ảnh), INT8 là dtype kết luận. Chênh so với SiLU seed 0 (100 epoch), đơn vị điểm phần trăm. Cổng C đạt khi cả ba cột chênh từ -1.0 trở lên.

.. list-table::
   :header-rows: 1
   :widths: 26 34 40 14

   * - Ứng viên
     - AP50-95 / AP NoHelmet / AP Vest
     - Chênh so với SiLU seed 0, 100 epoch
     - Cổng C
   * - LeakyReLU (0.1)
     - 34.11 / 17.77 / 43.00
     - -2.64 / -5.00 / -3.98
     - không đạt
   * - ReLU6
     - 33.12 / 22.41 / 43.58
     - -3.63 / -0.36 / -3.40
     - không đạt
   * - ReLU 200 epoch
     - 36.18 / 24.34 / 48.08
     - -0.57 / +1.57 / +1.10
     - đạt
   * - ReLU (:doc:`01-ket-qua-g4`)
     - 33.24 / 17.83 / 47.12
     - -3.51 / -4.94 / +0.14
     - không đạt
   * - SiLU 200 epoch (đối chứng)
     - 37.96 / 26.31 / 48.71
     - +1.21 / +3.54 / +1.73
     - không áp dụng

Tham chiếu FP16 (RKNNLite) và mô tả FP32 (PyTorch) của AP50-95 ``css_test``, chênh so với SiLU seed 0 cùng dtype:

.. list-table::
   :header-rows: 1
   :widths: 26 20 20

   * - Ứng viên
     - FP16 chênh
     - FP32 chênh
   * - LeakyReLU (0.1)
     - -1.84
     - -1.59
   * - ReLU6
     - -4.69
     - -4.83
   * - ReLU 200 epoch
     - -0.70
     - -0.42
   * - SiLU 200 epoch
     - +3.87
     - +3.79

Về huấn luyện 200 epoch (V-E, mô tả cạnh cổng C): ReLU 200 epoch chênh -1.78 điểm AP50-95, -1.97 điểm AP NoHelmet, -0.63 điểm AP Vest so với SiLU 200 epoch. SiLU 200 epoch chênh +1.21 điểm AP50-95 so với SiLU 100 epoch (INT8). Cổng C của ReLU 200 epoch so với SiLU 100 epoch: đạt.

Đọc cùng nhiễu seed: khoảng trải AP50-95 INT8 giữa ba seed SiLU là 1.35 điểm và giữa ba seed ReLU là 1.57 điểm (:doc:`01-ket-qua-g4` mục 5). Ba ứng viên của trang này chỉ có 1 seed, nên mức chênh nhỏ hơn các khoảng trải đó không đủ để kết luận có khác biệt.

6. Nhãn của từng ứng viên
=========================

.. list-table::
   :header-rows: 1
   :widths: 24 16 10 8 8 8 12 14

   * - Ứng viên
     - G1
     - G2
     - G3
     - A
     - B
     - C
     - Nhãn
   * - LeakyReLU (0.1)
     - qua một phần
     - ghi nhận
     - qua
     - đạt
     - đạt
     - không đạt
     - **Loại**
   * - ReLU6
     - qua
     - ghi nhận
     - qua
     - đạt
     - đạt
     - không đạt
     - **Loại**
   * - ReLU 200 epoch
     - qua một phần
     - ghi nhận
     - qua
     - đạt
     - đạt
     - đạt
     - **Chưa biết**

Ứng viên dừng ở bước đầu tiên không qua. G1 qua một phần chỉ cho nhãn tối đa "Chưa biết" khi A, B, C đều đạt. Tất cả là 1 seed. Nhãn của ReLU gốc ở :doc:`01-ket-qua-g4`. Trang này không đổi nhãn đó.

7. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 22 50

   * - Việc
     - Trạng thái
     - Đã làm gì
   * - Vì sao ReLU6 chậm hơn ReLU ở ``CORE_0``
     - chưa biết
     - Chỉ mô tả hai bảng build (ReLU6 giữ 8 ``Add`` riêng)
   * - Nhiễu seed của LeakyReLU, ReLU6 và ReLU 200 epoch
     - chưa biết
     - Mỗi cái 1 seed
   * - Độ dốc LeakyReLU khác 0.1
     - chưa biết
     - Một điểm, không quét
   * - Hardswish, GELU, Mish
     - chưa biết
     - Không thử, không nằm trong danh sách op đa nhân của T1
   * - Mâu thuẫn Relu, Clip, LeakyRelu đứng riêng giữa Operator List và hai guide
     - chưa biết
     - Không nguồn T1 nào giải thích
   * - Có công thức lượng tử hóa nào đưa mAP INT8 về gần FP16 cho SiLU hoặc biến thể
     - đã làm ở trang khác
     - Công thức ``h5`` ở :doc:`05-ket-qua-luong-tu-hoa` (chẩn đoán giai đoạn 2c), một seed
   * - P2
     - đã duyệt ngày 2026-11-01
     - Hai thí nghiệm, mỗi lần có phiên bị đánh dấu không thực hiện đúng do một mẫu giây

8. Nguồn
========

- T1: Operator List V2.3.2 (``docs/_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf``, tr.59 đến 61, 63, 84 đến 86), SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, tr.56 đến 57, 75, 142), API guide V1.5.2 tr.27.
- T3 PC và board: ``results/g4v_latency_workload.*``, ``results/g4v_latency_workload_2.*``, ``results/eval_g4.*``, ``bench/onboard_g4v/``, ``bench/onboard_g4v2/``, ``bench/eval_g4/rule_variants.txt``, ``export_int8.json`` của các run.
- Tìm nguồn: ``results/phase2b_variants_design.md`` (thiết kế và kết quả tìm nguồn G1 của LeakyReLU và ReLU6, doc-reader).

