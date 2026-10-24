:tocdepth: 1

****************
Operator support
****************

.. admonition:: Trang này trả lời

   - Op nào của YOLOv8n (SiLU, Resize và các op còn lại) NPU RK3588 hỗ trợ, và op nào chạy đa nhân?
   - Một op hoặc thay đổi kiến trúc (ví dụ đổi SiLU sang ReLU) có khả thi không, và quyết định theo tiêu chí nào?
   - Điều gì đã biết, điều gì còn chưa biết và chỉ đo trên board mới trả lời được?

.. admonition:: Tóm tắt

   - Phạm vi gồm SiLU, Resize, toàn bộ op của YOLOv8n và cổng khả thi bốn bước (T1, T2, T3 PC, T3 board).
   - ``ConvolutionSwish`` chỉ không hỗ trợ đa nhân (vẫn chạy một nhân), ``Resize`` không hỗ trợ đa nhân [T1].
   - Build lại YOLOv8n 5 class (FP16 và INT8, rknn-toolkit2 2.3.2, cùng danh sách op ở hai dtype): model SiLU có 57 op ``ConvExSwish`` (số 228 trong tài liệu cũ là số dòng log), model ReLU có 51 ``ConvRelu`` và 6 ``ConvReluAdd`` [T3 PC].
   - Theo T1, ``ConvExSwish`` không đa nhân dù ánh xạ vào mục nào. Đổi sang ReLU đưa ít nhất 90.9% cycles ước tính của compiler (build INT8) vào op có đa nhân, 9.1% (``ConvReluAdd``) chưa biết [T1, T3 PC].
   - Hai node Resize dùng ``coordinate_transformation_mode = asymmetric``, giá trị không nằm trong ba giá trị Operator List liệt kê, nhưng compiler vẫn xếp chúng lên NPU. Đổi sang giá trị được liệt kê cho bảng layer giống hệt, chưa rõ nguyên nhân [T1, T3 PC].
   - Guide SDK V2.3.2 và Operator List V2.3.2 khác nhau về ``Relu`` đứng riêng và ``Concat`` [T1].
   - Bản ghi T3 board ngày 2026-10-10 (model trọng số ngẫu nhiên, nhật ký gốc đã bị xóa): ``ConvExSwish`` chỉ chạy lõi 0, ``ConvRelu`` và ``ConvReluAdd`` chia ba lõi, ReLU nhanh hơn khoảng 8% ở ba lõi [T3 board, ghi nhận]. Chưa có mAP của model đã huấn luyện. Bài báo ``edgesoc_benchmark`` báo đa nhân trên RK3588 chỉ lợi nhỏ [T2] và không kiểm tra activation.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và quy tắc bằng chứng
================================

Phạm vi gồm SiLU, Resize và toàn bộ op của YOLOv8n. "Hỗ trợ" nghĩa là RKNN compiler xếp op lên NPU, "đa nhân" nghĩa là chạy với ``RKNN_NPU_CORE_0_1`` hoặc ``RKNN_NPU_CORE_0_1_2``. Op không có hỗ trợ đa nhân vẫn chạy, nhưng trên một nhân: layer hiển thị ``100.0%/0.0%/0.0%`` (SDK User Guide V2.3.2, trang PDF 75).

.. list-table::
   :header-rows: 1

   * - Tier
     - Nguồn
     - Trạng thái
   * - T1
     - Tài liệu hãng: Operator List V2.3.2, SDK User Guide V2.3.2, API guide V1.5.2
     - Có trong repo
   * - T2
     - Bài báo peer-reviewed trong repo: ``edgesoc_benchmark_2026kong``
     - Có trong repo
   * - T3 PC
     - Build model bằng rknn-toolkit2 2.3.2 do dự án chạy
     - Đã chạy (FP16 và INT8 cho model 5 class SiLU và ReLU, FP16 cho model 7 class cũ)
   * - T3 board
     - Đo ``eval_perf``, latency và mAP trên board
     - Có bản ghi 2026-10-10 (model trọng số ngẫu nhiên, nhật ký gốc đã bị xóa). Chưa đo model đã huấn luyện

Mọi khẳng định trong trang có thẻ tier trong ngoặc vuông, ví dụ [T1]. Mục không có tier là "chưa biết". Ba từ trạng thái 暂不支持, 尚不支持 và 不支持 không được Operator List định nghĩa (đã tìm ở trang PDF 1 đến 107, không thấy định nghĩa). Trang coi cả ba là "không hỗ trợ đa nhân" và không xếp hạng giữa chúng.

Nguồn và đường dẫn:

- :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`, chương 3.2 RK3588 (trang PDF 56 đến 107).
- ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (178 trang, nằm ngoài ``docs/``).
- :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>` (75 trang).
- :download:`edgesoc_benchmark_2026kong.pdf <../../../_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf>` (Scientific Reports 2026, 16:5875).

Mọi số trang trong trang này là trang PDF. Với chương 3.2 của Operator List, trang in = trang PDF - 6.

2. Cổng khả thi
===============

Cổng áp dụng cho mọi op hoặc thay đổi kiến trúc ứng viên, theo thứ tự từ rẻ nhất đến đắt nhất. G1 và G3 trả lời "op chạy được trên NPU không", G4 trả lời "đổi có đáng không". G2 chỉ ghi nhận bằng chứng và không chặn ứng viên. Ứng viên dừng ở bước đầu tiên không qua. Các tham số dưới đây do dự án đặt, không lấy từ tài liệu ngoài, và đã chốt ngày 2026-10-25.

.. list-table::
   :header-rows: 1

   * - Bước
     - Tier
     - Câu hỏi
     - Qua khi
     - Dừng khi
     - Công cụ hoặc nguồn
   * - G1
     - T1
     - Op có mục trong Operator List chương 3.2 RK3588 không, dtype int8/float16 thỏa không, ràng buộc thuộc tính thỏa không
     - Có mục và ràng buộc thỏa
     - Không có mục hoặc vi phạm ràng buộc
     - Operator List V2.3.2, chương 3.2. Dòng ``多核联合`` chỉ được ghi lại, không chặn, vì op không đa nhân vẫn chạy một nhân
   * - G2
     - T2
     - Bài báo trong repo có đo op này trên NPU nào, SoC nào
     - Luôn qua. Ghi bằng chứng cùng SoC, hoặc ghi "không có bằng chứng T2"
     - Không dừng ở bước này
     - ``edgesoc_benchmark_2026kong``
   * - G3
     - T3 PC
     - Build model ở INT8 (dtype triển khai), FP16 làm tham chiếu, đọc bảng từng layer (cột ``OpType``, ``Target``)
     - Không có op mới có ``Target`` CPU so với baseline
     - Có op mới có ``Target`` CPU
     - Pipeline ``ai/automation/export_npu.py`` (INT8, 300 ảnh calibration của protocol v1), ép ``RKNN(verbose=True)`` để in bảng layer. FP16: 5 lệnh ở mục 5.1
   * - G4
     - T3 board
     - Chạy ``rknn.init_runtime(target='rk3588', device_id=..., perf_debug=True)`` rồi ``rknn.eval_perf()`` ở ``CORE_0`` và ``CORE_0_1_2``, đọc cột ``WorkLoad(0/1/2)-ImproveTherical``, đo latency và mAP
     - Đạt cả ba điều kiện A, B, C bên dưới
     - Không đạt một trong ba điều kiện
     - SDK User Guide V2.3.2, trang 74 đến 75. Latency lấy ở phiên ``init_runtime`` mặc định, ``WorkLoad`` lấy ở phiên ``perf_debug=True`` (Evaluation Protocol v1). Trạng thái hiện tại: có bản ghi một phần (mục 3.6), chưa chạy theo chuẩn

Chuẩn của G4:

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Điều kiện
     - Chuẩn
   * - A. Phủ đa nhân
     - Các lớp có workload chia từ hai nhân trở lên phải chiếm ít nhất 50% tổng cycles ước tính (cột ``Cycles(DDR/NPU/Total)`` của build INT8)
   * - B. Latency
     - Median của 5 lần ``eval_perf`` cho mỗi ``core_mask``, lặp ở hai phiên ``init_runtime``. ``CORE_0_1_2`` được coi là nhanh hơn khi giảm ít nhất 5% và mức giảm lớn hơn chênh lệch median giữa hai phiên
   * - C. mAP
     - AP50-95 giảm tối đa 1.0 điểm phần trăm so với model SiLU cùng dtype và cùng seed. ``AP head`` và ``AP self_clothes`` mỗi lớp cũng giảm tối đa 1.0 điểm phần trăm
   * - dtype
     - INT8 (``w8a8``) là dtype kết luận, FP16 chỉ để tham chiếu
   * - Seed
     - Kết quả seed 42 ghi nhãn "tạm". Kết luận cuối cần seed 42, 43 và 44
   * - ``core_mask``
     - ``CORE_0`` và ``CORE_0_1_2``. Kế hoạch Phase 4 (``contents/09-tien-do/01-phase/03-phase-4.rst``) đã đo tầng 1 ở ``CORE_0``, ``CORE_0_1`` và ``CORE_0_1_2``, nên chuẩn này không đòi đo thêm

Nhãn kết luận cho một ứng viên: "Giữ" khi qua G1 đến G4, "Loại" khi trượt ở một bước, "Chưa biết" khi chưa chạy hết các bước. Trạng thái hiện tại của ứng viên đổi SiLU sang ReLU: G1 qua một phần (``ConvRelu`` ánh xạ được sang ``ConvolutionRelu``, ``ConvReluAdd`` chưa có mục cùng tên), G2 ghi nhận (không có bằng chứng T2 về activation), G3 qua ở INT8 và FP16 (mục 3.2), G4 có bản ghi T3 board cho điều kiện A và B trên model trọng số ngẫu nhiên (mục 3.6), chưa theo chuẩn hai phiên, và điều kiện C (mAP) chưa đo. Nhãn: Chưa biết.

Baseline của G3: ở cả build INT8 và FP16, các layer có ``Target`` CPU chỉ gồm ``InputOperator``, ``Transpose`` (ID 103 ở model SiLU, ID 97 ở model ReLU) và ``OutputOperator``.

Kết quả G1 ghi dòng đa nhân thành ba trạng thái:

- Có dòng rõ ràng: ghi nguyên văn dòng ``多核联合``.
- Thừa hưởng từ op cha: mục ghi ``说明及规格限制同X``, không có dòng riêng.
- Không có dòng: chưa biết.

G2 không dừng ứng viên vì bài báo chỉ đo latency của cả model và không nêu op nào chạy đa nhân. Thiếu bằng chứng T2 chỉ đánh dấu "chưa biết", quyết định nằm ở G3 và G4.

3. SiLU (Conv + Swish)
======================

3.1. Câu hỏi và giả thuyết
--------------------------

Giả thuyết: đổi SiLU của YOLOv8 sang ReLU hoặc LeakyReLU để Conv chạy đa nhân. Giả thuyết này cần đo latency ở ``CORE_0_1_2`` và mAP. Đây là giả thuyết, chưa phải kết quả, Bài báo T2 trong repo không kiểm tra nó. Bản ghi T3 board của dự án (mục 3.6) có số đo trên model trọng số ngẫu nhiên, chưa có mAP.

3.2. SiLU nằm ở đâu trong model
-------------------------------

Hai model 5 class đã train: SiLU (``sfchd_5class_yolov8n_baseline_100ep_s42``) và ReLU (``sfchd_5class_yolov8n_relu_100ep_s42``), cùng nằm trong ``ai/automation/runs``. Repo không lưu ONNX của hai run này, nên ONNX được export lại từ ``weights/best.pt`` bằng ``YOLO(...).export(format="onnx", imgsz=640, opset=19)`` (cùng lệnh ``export_onnx`` trong ``ai/core/rknn/baseline.py``). Sau đó build FP16 bằng rknn-toolkit2 2.3.2, target ``rk3588`` [T3 PC]. Build INT8 dùng pipeline ``export_npu.py`` (300 ảnh calibration của protocol v1, seed 42) và cho cùng số dòng bảng layer, cùng OpType, cùng op có ``Target`` CPU với FP16 [T3 PC].

.. list-table::
   :header-rows: 1
   :widths: 12 44 44

   * - Model
     - Activation trong ONNX
     - Op sau khi compiler gộp
   * - SiLU
     - 57 cặp ``Sigmoid`` và ``Mul`` làm SiLU (cộng 1 ``Sigmoid`` và 1 ``Mul`` ở head), 64 ``Conv``
     - 57 ``ConvExSwish``, 7 ``Conv``, 8 ``Add``
   * - ReLU
     - 57 ``Relu``, 64 ``Conv``
     - 51 ``ConvRelu``, 6 ``ConvReluAdd``, 7 ``Conv``, 2 ``Add``, không có ``Relu`` đứng riêng

Các op không liên quan activation giống nhau ở hai model (mục 5.2). Riêng ``Add`` là 8 ở model SiLU, còn model ReLU có 2 ``Add`` và 6 ``ConvReluAdd``, khớp với việc 6 ``Add`` được gộp vào Conv. Model 7 class cũ (run 2026-09-17, 5 epoch) có danh sách op giống model SiLU, nên bảng ở mục 5.2 dùng được cho cả hai.

Số 228 trong tài liệu cũ là số dòng chứa tên ``ConvExSwish`` trong stdout của compiler (57 + 57 + 114, vì stdout in ba bảng). Số op thật là 57. Cờ ``conv_eltwise_activation_fuse = 1`` có trong dòng tùy chọn compiler.

3.3. Bằng chứng T1
------------------

Dòng ``多核联合`` trong Operator List V2.3.2, chương 3.2 RK3588:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Op (mục, trang PDF)
     - Dòng ``多核联合``
   * - Convolution (3.2.5, tr. 59)
     - ``多核联合: 支持``
   * - ConvolutionRelu (3.2.7, tr. 60)
     - ``多核联合: 支持``
   * - ConvolutionClip (3.2.8, tr. 61)
     - ``多核联合: 支持``
   * - ConvolutionPRelu/LeakyRelu (3.2.9, tr. 61)
     - ``多核联合: 支持``
   * - ConvolutionAdd (3.2.10, tr. 61)
     - ``多核联合: 支持``
   * - ConvolutionAddRelu (3.2.19, tr. 63)
     - ``多核联合: 支持``
   * - ConvolutionSwish (3.2.17, tr. 63)
     - ``多核联合: 暂不支持``
   * - exSwish (3.2.69, tr. 98)
     - ``多核联合: 尚不支持``

``ConvolutionSwish`` có dòng ``说明及规格限制同Convolution``, nên chạy một nhân với cùng giới hạn như ``Convolution``. Chỉ dòng đa nhân là 暂不支持, nên "tạm chưa hỗ trợ" áp dụng cho chạy đa nhân, không áp dụng cho việc op chạy được. ConvolutionRelu, ConvolutionAdd và ConvolutionAddRelu cũng có dòng ``说明及规格限制同Convolution`` kèm dòng ``多核联合`` riêng.

SDK User Guide V2.3.2, ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, trang PDF 75:

   "This type of operator does not implement multi-core task segmentation in the NPU driver and will be supported in subsequent versions. The existing operators that support multi-core task segmentation include: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu."

API guide V1.5.2, ``docs/_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf``, trang PDF 27:

   "For multi-cores mode (when enabling RKNN_NPU_CORE_0_1 and RKNN_NPU_CORE_0_1_2), the following ops have better acceleration : Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu."

3.4. Đối chiếu tên op compiler với Operator List
------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 16 30 18 36

   * - Op trong bảng layer
     - Mục Operator List
     - ``多核联合``
     - Ghi chú
   * - ``ConvExSwish``
     - ``ConvolutionSwish`` (3.2.17) hoặc ``exSwish`` (3.2.69)
     - 暂不支持 hoặc 尚不支持
     - Tên ``ConvExSwish`` không có trong Operator List. Cả hai mục ứng viên đều không đa nhân
   * - ``ConvRelu``
     - ``ConvolutionRelu`` (3.2.7)
     - 支持
     - Tên ``ConvRelu`` không có trong Operator List, có trong ví dụ của SDK guide V2.3.2 trang 75. Ánh xạ theo tên
   * - ``ConvReluAdd``
     - không có mục cùng tên
     - chưa biết
     - Operator List có ``ConvolutionAddRelu`` (3.2.19), tính ``Relu(Add(Conv(Input0), Input1))``. Chưa xác nhận hai op cùng phép tính
   * - ``Conv``
     - ``Convolution`` (3.2.5)
     - 支持
     - Ánh xạ theo tên

Kết luận T1 cho ``ConvExSwish`` không phụ thuộc cách ánh xạ, vì cả hai mục ứng viên đều ghi không đa nhân. Đây là suy luận từ hai dòng T1, hành vi thật cần G4. Tên trong bảng layer và tên trong Operator List khác nhau có hệ thống, nên không dùng ánh xạ theo tên để kết luận trạng thái đa nhân của ``ConvReluAdd``.

3.5. So sánh hai biến thể theo cycles
-------------------------------------

Cột ``Cycles(DDR/NPU/Total)`` của bảng layer là ước tính của compiler [T3 PC]. Chỉ Conv có số khác 0 trong cột này. Các op còn lại ghi 0, nghĩa là compiler không ước tính, không có nghĩa là không tốn thời gian. Hai model có cùng tổng cycles ở mỗi dtype (INT8: 5666717, FP16: 9546256). Bảng dùng build INT8, cột tỉ lệ FP16 để tham chiếu.

.. list-table::
   :header-rows: 1
   :widths: 10 18 10 18 12 12 20

   * - Model
     - Op
     - Số lớp
     - Cycles INT8
     - Tỉ lệ INT8
     - Tỉ lệ FP16
     - ``多核联合`` theo T1
   * - SiLU
     - ``ConvExSwish``
     - 57
     - 5431517
     - 95.8%
     - 97.8%
     - không
   * - SiLU
     - ``Conv``
     - 7
     - 235200
     - 4.2%
     - 2.2%
     - có
   * - ReLU
     - ``ConvRelu``
     - 51
     - 4913117
     - 86.7%
     - 89.3%
     - có
   * - ReLU
     - ``ConvReluAdd``
     - 6
     - 518400
     - 9.1%
     - 8.4%
     - chưa biết
   * - ReLU
     - ``Conv``
     - 7
     - 235200
     - 4.2%
     - 2.2%
     - có

4913117 + 518400 = 5431517, đúng bằng cycles của ``ConvExSwish`` (FP16 cũng khớp: 8528459 + 806400 = 9334859). Đổi activation không đổi ước tính cycles. Theo T1, phần cycles ước tính nằm ở op có đa nhân là 4.2% ở model SiLU, và ít nhất 90.9% ở model ReLU (86.7% cộng 4.2%), còn 9.1% chưa biết. Ở FP16 các số tương ứng là 2.2%, 91.6% và 8.4%. Đây là phạm vi mà giả thuyết áp dụng, không phải mức tăng tốc dự kiến.

3.6. Bằng chứng T2, T3 board đã ghi nhận và kết luận
----------------------------------------------------

Bài báo ``edgesoc_benchmark_2026kong``, Table 4 (trang PDF 7), hàng YOLOv8n, latency (ms): AUTO 24.88, C0 24.54, C1 26.1, C2 25.89, C0_1 25.31, C0_1_2 25.33, ALL 21.25. Bài báo lượng tử hóa INT8 bằng PTQ với RKNN Toolkit 2.3.0 (trang 4). Bài báo không nhắc SiLU hay ReLU, không nêu op nào chạy đa nhân và không định nghĩa các mã cột. Vì vậy bài báo không ủng hộ cũng không bác bỏ giả thuyết ở mục 3.1. Kết luận của bài báo (trang PDF 6):

   "multi-core scheduling did not lead to proportional reductions in latency. For small models such as YOLOv5n, the difference between single-core and multi-core execution was less than 5% (21.5 ms vs. 20.5 ms). For larger models, the gains were similarly modest or even negligible."

Cùng bài, trang PDF 7: "YOLO11m achieved 93.7 ms in single-core mode and 95.5 ms in three-core mode". Số học của người đọc, bài báo không nêu: ở YOLOv8n, ``C0_1_2`` (25.33 ms) chậm hơn ``C0`` (24.54 ms) 0.79 ms, và ``ALL`` (21.25 ms) thấp hơn ``C0`` 13.4%. Bài báo không nói ``ALL`` ứng với chế độ nào.

Bản ghi T3 board ngày 2026-10-10 nằm trong ``contents/09-tien-do/03-khoang-trong/05-thiet-ke-model.rst`` và ``06-yolo.rst`` [T3 board, ghi nhận]. Điều kiện: YOLOv8n trọng số ngẫu nhiên ``nc=5``, INT8, 640x640, toolkit 2.3.2, RK3588S, NPU 1 GHz, ``eval_perf`` với ``fix_freq=True``. Ở ``CORE_0_1_2``, 57 lớp ``ConvExSwish`` đều có WorkLoad 100%/0%/0% (chỉ lõi 0), còn 51 ``ConvRelu`` và 6 ``ConvReluAdd`` được chia ba lõi (khoảng 35%/32.5%/32.5%). Model ReLU nhanh hơn ``CORE_0`` khoảng 8% khi dùng ba lõi (13.969 ms xuống 12.854 ms ở ``relu_opt3``, 13.955 ms xuống 12.801 ms ở ``relu_noadd``), model SiLU không khác biệt ngoài độ trải. Bản ghi có hai lượt đo, lượt 2 loại biến nhiễu do ghép ``Add``.

Giới hạn của bản ghi: nhật ký gốc ``04_debug-logs/2026-10-10_t3-board-silu-resize`` đã bị xóa, nên các số này không kiểm lại được và chỉ còn dưới dạng bản ghi trong docs. Bản ghi khớp với build PC ở mục 3.2 (57 ``ConvExSwish``, 51 ``ConvRelu``, 6 ``ConvReluAdd``). Model chưa huấn luyện nên không có mAP. Đối chiếu với chuẩn G4, phần này là suy ra từ bản ghi và build INT8 (mục 3.5), không phải đo mới: điều kiện A thỏa vì ``ConvRelu`` và ``ConvReluAdd`` chiếm 95.8% cycles ước tính (5431517 trên 5666717). Điều kiện B: mức giảm khoảng 8% lớn hơn 5%, chưa đối chiếu với chênh lệch giữa hai phiên. Điều kiện C chưa đo.

.. list-table::
   :header-rows: 1
   :widths: 44 22 34

   * - Câu hỏi
     - Trạng thái
     - Cách giải quyết
   * - ``ConvExSwish`` chạy đa nhân theo T1
     - Không (cả hai mục ứng viên). Bản ghi T3 board: 100%/0%/0%
     - Đo lại với model đã huấn luyện (G4)
   * - Phần cycles ước tính ở op đa nhân sau khi đổi sang ReLU
     - Ít nhất 90.9% (INT8) theo T1, còn 9.1% chưa biết theo T1. Bản ghi T3 board: ``ConvReluAdd`` chia ba lõi
     - T1 không có mục cùng tên, dựa vào bản ghi T3 board
   * - Đổi SiLU sang ReLU mở khóa tăng tốc đa nhân
     - Có ghi nhận: ReLU nhanh hơn khoảng 8% ở ba lõi (model trọng số ngẫu nhiên)
     - Đo lại theo chuẩn B với model đã huấn luyện (G4)
   * - Chi phí mAP của việc đổi activation
     - Chưa biết
     - G4

4. Resize
=========

4.1. Vai trò trong YOLOv8n
--------------------------

Neck của YOLOv8n upsample bằng 2 op Resize (số node ONNX là 2, xem mục 5.2). Operator List ghi Resize không hỗ trợ đa nhân (mục 4.2).

4.2. Bằng chứng T1
------------------

Nguồn: :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`, mục 3.2.54 Resize (tiêu đề ở trang PDF 86, dòng ``多核联合`` ở trang PDF 87).

.. list-table::
   :header-rows: 1
   :widths: 24 56 20

   * - Mục
     - Nguyên văn
     - Trang PDF
   * - Đa nhân
     - ``多核联合: 不支持``
     - 87
   * - Giới hạn scale
     - ``目前仅支持宽高方向的整数倍缩放, 且缩放倍数为 2‑8 的整数倍, 如果是 (1, c, 1, 1) 则支持放大到 (1, c, h, w)``
     - 87
   * - Giới hạn mode
     - ``目前仅支持 nearest 和 linear 两种可配置``
     - 87
   * - Giới hạn coordinate_transformation_mode
     - ``目前仅支持 half_pixel，pytorch_half_pixel，align_corners 三种``
     - 87
   * - Kiểu dữ liệu
     - ``T1: int8(Tensor), float16(Tensor)``
     - 87

Hai op Resize trong bản build đều scale 2 lần (xem mục 4.3), nên theo shape thì thỏa giới hạn bội số nguyên từ 2 đến 8.

Thuộc tính của hai node ONNX ``/model.10/Resize`` và ``/model.13/Resize`` (đọc từ ``ai/automation/runs/2026-09-17_sfchd_yolov8n_baseline_5ep/weights/best.onnx`` bằng onnx 1.18.0) [T3 PC]:

.. list-table::
   :header-rows: 1

   * - Thuộc tính
     - Giá trị
     - Khớp giới hạn Operator List
   * - ``mode``
     - ``nearest``
     - Có
   * - ``coordinate_transformation_mode``
     - ``asymmetric``
     - Không nằm trong ba giá trị được liệt kê
   * - ``nearest_mode``
     - ``floor``
     - Operator List ghi ``nearest_mode`` là ``目前不支持设置``

Bản build vẫn gán cả hai op Resize cho NPU (một nhân) [T3 PC]. Vì vậy hoặc compiler chuẩn hóa thuộc tính này trước khi xếp lên NPU, hoặc Operator List chưa phản ánh đầy đủ. Nguyên nhân chưa biết. Khi đổi hai thuộc tính này sang ``half_pixel`` và ``round_prefer_floor`` (giá trị Operator List cho phép) rồi build lại, bảng layer 119 dòng giống hệt bản gốc, không dòng nào khác [T3 PC]. Chưa kiểm số học hai bản có giống nhau không.

4.3. Bằng chứng T3 PC
---------------------

Bảng per-layer của bản rebuild FP16 (rknn-toolkit2 2.3.2, mô tả ở mục 5.1) có hai dòng Resize (bản INT8 cho hai dòng cùng shape và cùng Target NPU):

.. list-table::
   :header-rows: 1

   * - ID
     - InputShape
     - OutputShape
     - Target
     - DataType
   * - 46
     - (1,256,20,20)
     - (1,256,40,40)
     - NPU
     - FLOAT16
   * - 54
     - (1,128,40,40)
     - (1,128,80,80)
     - NPU
     - FLOAT16

4.4. Phương án thay thế
-----------------------

Một hướng thay Resize là ConvTranspose. Theo Operator List, mục 3.2.20 ConvTranspose (tiêu đề trang PDF 64, dòng ``多核联合`` trang PDF 65) cũng ghi ``多核联合: 暂不支持``. Ràng buộc nguyên văn ở trang PDF 64 và 65:

.. list-table::
   :header-rows: 1

   * - Ràng buộc
     - Nguyên văn
   * - stride
     - ``stride_h 仅支持 1,2,4,8``
   * - dilation
     - ``当 dilation 不等于 (1, 1) 时，只支持 kernel=(1,1)``

Vì vậy, theo Operator List, thay Resize bằng ConvTranspose không đem lại hỗ trợ đa nhân. ConvTranposeSwish (mục 3.2.31, trang PDF 66) ghi ``说明及规格限制同ConvTranspose``, tức kế thừa từ ConvTranspose.

Mọi phương án thay thế đều chưa thử [chưa đo]. Tài liệu API V1.5.2, trang PDF 27 (:download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`) có câu "In the future update, some ops like Pool or ConvTranpose will be supported." Câu này chỉ có trong guide V1.5.2, guide SDK V2.3.2 không có câu tương đương.

4.5. Kết luận hiện tại
----------------------

.. list-table::
   :header-rows: 1
   :widths: 34 16 50

   * - Câu hỏi
     - Trạng thái
     - Cách giải quyết
   * - Resize chạy được trên NPU
     - có
     - Bản build T3 PC, mục 4.3
   * - Resize chạy đa nhân
     - không
     - Operator List, trang PDF 87 [T1]
   * - Resize có kéo chậm ``CORE_0_1_2``
     - chưa biết
     - G4: đọc WorkLoad của ID 46 và 54 cùng latency
   * - Vì sao ``asymmetric`` và ``nearest_mode = floor`` vẫn lên NPU
     - chưa biết (build giống hệt khi dùng giá trị được liệt kê)
     - Đọc tài liệu compiler, và so số học hai bản trên board

5. Toàn bộ op của YOLOv8n
=========================

5.1. Nguồn và phạm vi
---------------------

Bảng ở mục 5.2 lấy từ model SiLU 5 class (run ``sfchd_5class_yolov8n_baseline_100ep_s42``): ONNX 233 node, opset 19, output ``[1, 9, 8400]``, bảng layer 119 dòng. Model 7 class cũ (``ai/automation/runs/2026-09-17_sfchd_yolov8n_baseline_5ep/weights/best.onnx``, output ``[1, 11, 8400]``) cho đúng danh sách op này. Danh sách op của model ReLU nằm ở mục 3.2.

Bảng lấy từ bản build FP16 (bản INT8 cho cùng 119 dòng, cùng OpType và Target), rknn-toolkit2 2.3.2, target ``rk3588``, ``librknnc version: 2.3.2 (e045de294f@2025-04-07T19:48:25)``. Build log gốc mà các trang cũ trích dẫn không còn tồn tại, trang này thay bằng build lại. Script ``build_fp16.py`` gồm 5 lệnh: ``RKNN(verbose=True)``, ``config(target_platform="rk3588")``, ``load_onnx``, ``build(do_quantization=False)``, ``release``.

5.2. Bảng đối chiếu từng op
---------------------------

Mỗi dòng là một OpType trong bảng layer của RKNN (119 dòng, 15 OpType). Target lấy từ bảng này [T3 PC]. Trạng thái đa nhân lấy từ Operator List V2.3.2 [T1].

.. list-table::
   :header-rows: 1
   :widths: 20 24 32 24

   * - Op (RKNN, số lớp, Target)
     - Mục Operator List
     - ``多核联合`` [T1] (trang PDF)
     - Ghi chú compiler
   * - ``ConvExSwish`` (57, NPU)
     - không có tên này trong list, xem mục 3.4
     - gần nhất: ``ConvolutionSwish`` ``暂不支持`` (63), ``exSwish`` ``尚不支持`` (98)
     - thay cặp Sigmoid và Mul (``replace_exswish``)
   * - ``Conv`` (7, NPU)
     - Convolution
     - ``支持`` (59)
     -
   * - ``Concat`` (17, NPU)
     - Concat
     - không có dòng, chưa biết (mục ở trang 58)
     -
   * - ``Split`` (9, NPU)
     - Split
     - không có dòng, chưa biết (mục ở trang 91)
     - nhận Slice qua ``replace_parallel_slice_by_split``
   * - ``Add`` (8, NPU)
     - Add
     - ``支持`` (56)
     -
   * - ``MaxPool`` (3, NPU)
     - MaxPool
     - không có dòng, chưa biết (mục ở trang 79)
     -
   * - ``Resize`` (2, NPU)
     - Resize
     - ``不支持`` (87)
     -
   * - ``Reshape`` (7, NPU)
     - Reshape
     - ``尚不支持`` (86)
     -
   * - ``Sub`` (2, NPU)
     - Sub
     - ``不支持`` (92)
     -
   * - ``Mul`` (2, NPU)
     - Mul
     - ``支持`` (77)
     - nhận Div qua ``convert_div_to_mul``
   * - ``exSoftmax13`` (1, NPU)
     - exSoftmax13
     - ``尚不支持`` (89)
     - từ Softmax qua ``convert_softmax_to_exsoftmax13``
   * - ``Transpose`` (1, CPU)
     - Transpose
     - ``暂不支持`` (95)
     -
   * - ``Sigmoid`` (1, NPU)
     - Sigmoid
     - ``尚不支持`` (95)
     -
   * - ``InputOperator`` (1, CPU)
     - không có mục (tìm tên trong Operator List, 0 kết quả)
     - không áp dụng
     -
   * - ``OutputOperator`` (1, CPU)
     - không có mục (tìm tên trong Operator List, 0 kết quả)
     - không áp dụng
     -

Số node ONNX của model SiLU 5 class để đối chiếu (233 node) [T3 PC]: Conv 64, Sigmoid 58, Mul 58, Concat 17, Split 8, Add 8, Reshape 8, MaxPool 3, Resize 2, Slice 2, Sub 2, Transpose 1, Softmax 1, Div 1.

Số dòng RKNN khác số node ONNX do các pass của compiler: 57 cặp Sigmoid và Mul được thay bằng ``exswish``, Div thành Mul, 2 Slice thành Split, Softmax thành exSoftmax13. Các chênh lệch còn lại ở Reshape (8 node ONNX, 7 dòng RKNN) và Split (8 node ONNX cộng 2 Slice, 9 dòng RKNN) chưa được giải thích bằng nguồn nào.

5.3. Các op chưa biết
---------------------

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Op
     - Tình trạng trong nguồn
     - Thời gian chiếm
   * - Concat
     - Operator List không có dòng ``多核联合``, chỉ có ``axis ∈ {0, 1, 2, 3}`` (trang 58). Cả hai guide đều liệt kê Concat là op đa nhân
     - chưa đo
   * - Split
     - Không có dòng ``多核联合``, chỉ có ``axis ∈ {0, 1, 2, 3}`` (trang 91)
     - chưa đo
   * - MaxPool
     - Không có dòng ``多核联合``. Ràng buộc ``kernel_h ∈ (0, 7]``, ``kernel_w ∈ (0, 7]`` và ``ceil_mode`` ghi ``不支持`` (trang 79)
     - chưa đo
   * - ConvExSwish
     - Tên không có trong Operator List và guide SDK V2.3.2
     - chưa đo

Slice không xuất hiện trong bảng per-layer của RKNN. Các op Sub, Reshape, Transpose, Sigmoid, exSoftmax13 và Resize có trạng thái không đa nhân rõ ràng trong Operator List và nằm ở neck và detection head. Chưa có nguồn nào chứa thời gian từng lớp, nên phần thời gian của chúng là chưa đo.

5.4. Việc cần làm để đóng bảng
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 28 32

   * - Việc
     - Công cụ
     - Kết quả cần có
   * - Chạy trên board ở ``CORE_0_1_2`` để điền WorkLoad cho cả 119 dòng
     - ``eval_perf`` với ``perf_debug=True``
     - Cột ``WorkLoad(0/1/2)-ImproveTherical`` đầy đủ

Bản ghi T3 board 2026-10-10 chỉ nêu ``ConvExSwish``, ``ConvRelu`` và ``ConvReluAdd``. Các op còn lại của bảng chưa có WorkLoad được ghi nhận.

6. Mâu thuẫn, điểm chưa biết và đặc tả đo T3
============================================

6.1. Hai tài liệu T1 khác nhau
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 14 29 29 28

   * - Op
     - Guide SDK V2.3.2, trang 75
     - Operator List V2.3.2
     - Guide API V1.5.2, trang 27
   * - Relu
     - Có trong danh sách: "Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu."
     - Trang 84: ``多核联合: 暂不支持``
     - Có trong danh sách: "Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu."
   * - Concat
     - Có trong cùng danh sách trên
     - Không có dòng ``多核联合`` (mục 3.2.4, trang 58)
     - Có trong cùng danh sách trên

Hai guide đều xếp Relu và Concat là op đa nhân, còn Operator List ghi Relu đứng riêng là ``暂不支持`` và không có dòng đa nhân cho Concat. Không nguồn nào trong repo giải thích sự khác biệt này.

Cách đọc (không phải nguồn): trong graph CNN, ReLU thường được gộp vào conv (ConvolutionRelu, ``支持``), nên giới hạn của Relu đứng riêng có thể ít khi xảy ra. Điều này cần G4 xác nhận.

Với model ReLU 5 class, bảng layer không có ``Relu`` đứng riêng (57 ``Relu`` ONNX gộp thành 51 ``ConvRelu`` và 6 ``ConvReluAdd``, mục 3.2), nên mâu thuẫn về ``Relu`` không ảnh hưởng hai model đang xét [T3 PC].

Trang này dùng Operator List cho trạng thái từng op vì tài liệu này có dòng riêng cho từng op. Hai guide chỉ dùng để đối chiếu. Về cách mô tả op không chia được đa nhân: chỉ guide API V1.5.2 trang 27 có cụm "Other type of op will fallback to Core0 to continue running." Guide SDK V2.3.2 trang 75 mô tả cùng hiệu ứng bằng một lớp hiện ``100.0%/0.0%/0.0%`` và "so this layer runs on a single core".

6.2. Bảng điểm chưa biết
------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Câu hỏi
     - Trạng thái
     - Cái gì giải quyết
   * - ``ConvExSwish`` có phải op tên ``ConvolutionSwish`` trong Operator List
     - chưa biết, nhưng kết luận T1 không phụ thuộc cách ánh xạ (mục 3.4). Bản ghi T3 board: 100%/0%/0%
     - T3: ``eval_perf`` với ``perf_debug=True`` ở ``CORE_0_1_2``, đọc WorkLoad của các lớp ConvExSwish
   * - Đổi SiLU sang ReLU hoặc LeakyReLU có mở khóa tăng tốc đa nhân cho model đã huấn luyện không
     - có ghi nhận khoảng 8% trên model trọng số ngẫu nhiên, chưa có mAP
     - T3: latency ở ``CORE_0`` và ``CORE_0_1_2``, model SiLU và ReLU, kèm mAP
   * - Concat, Split, Slice, MaxPool có chạy đa nhân không
     - chưa biết (Operator List không có dòng, Concat được hai guide liệt kê là đa nhân)
     - T3: cột WorkLoad
   * - Trạng thái đa nhân của ``ConvReluAdd`` (6 lớp ở model ReLU)
     - chưa biết theo T1 (không có mục cùng tên). Bản ghi T3 board: chia ba lõi
     - T3: cột WorkLoad của model đã huấn luyện
   * - Khác biệt khi compile INT8 so với FP16
     - Đã biết: cùng danh sách op và cùng op có ``Target`` CPU ở model SiLU và ReLU, cycles khác (mục 3.5) [T3 PC]
     - Không áp dụng
   * - Vì sao Resize với ``asymmetric`` và ``nearest_mode = floor`` vẫn lên NPU
     - chưa biết (build giống hệt khi dùng giá trị được liệt kê)
     - Đọc tài liệu compiler, hoặc đổi thuộc tính khi export ONNX rồi build lại
   * - Tên op trong chương 3.2 của Operator List sau các pass compiler cho từng op ONNX
     - biết một phần (Slice thành Split, Div thành Mul)
     - Không áp dụng

6.3. Đặc tả đo T3 board
-----------------------

Cách đo theo Evaluation Protocol v1 (``contents/03-phuong-phap/02-giao-thuc/02-bon-nhom-metric.rst``, tầng 1): latency lấy ở phiên ``init_runtime`` mặc định, bảng từng layer lấy ở phiên ``perf_debug=True``. Evaluation Protocol v1 mô tả cách đo và không ghi ngưỡng quyết định. Ngưỡng G4 ở mục 2 là tiêu chí phân tích của trang này, ``core_mask`` tầng 1 lấy từ kế hoạch Phase 4. Trang này không nhắc lại các giá trị khác của protocol.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Mục
     - Giá trị
   * - Model cần đo
     - YOLOv8n SiLU, YOLOv8n ReLU hoặc LeakyReLU, đều 5 class, đã train xong (``best.pt`` có sẵn). Hai run là ``sfchd_5class_yolov8n_baseline_100ep_s42`` và ``sfchd_5class_yolov8n_relu_100ep_s42`` trong ``ai/automation/runs``
   * - Target
     - ``rk3588``
   * - dtype
     - INT8 (kết luận), FP16 (tham chiếu)
   * - Toolkit
     - rknn-toolkit2 2.3.2
   * - Chế độ ``core_mask``
     - ``CORE_0`` và ``CORE_0_1_2``
   * - Công cụ
     - ``rknn.init_runtime(..., perf_debug=True)`` và ``rknn.eval_perf()`` (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, trang 74 và 75)
   * - Cột cần đọc
     - ``WorkLoad(0/1/2)-ImproveTherical`` và ``Target``
   * - Số liệu cần ghi
     - latency (ms), mAP, ``AP head``, ``AP self_clothes``, workload của từng lớp ConvExSwish hoặc ConvRelu
   * - Kết quả hiện tại
     - có bản ghi một phần ở mục 3.6, chưa đo model đã huấn luyện

Kết quả đo được ghi vào Table K và Table M trong trang contents/03-phuong-phap/03-dac-ta-bang.
