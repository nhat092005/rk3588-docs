*********************
Mục chưa biết còn lại
*********************

.. admonition:: Trang này trả lời

   - Với mỗi mục "chưa biết" còn lại của nhóm Tầng NPU (G7, G10, G11, M1, M2, M4, M6, M7, M8, M16 và các mục của giai đoạn 2c, 2d), đã đo hoặc tìm thêm gì, nhãn cuối là gì?
   - Mục nào vẫn chưa biết, vì sao, và cần gì để biết?

.. admonition:: Tóm tắt

   - Đã đo mới: Resize micro model (G7b), Relu đứng riêng (G11), ba luồng dùng chung một context (M4), ``async_mode`` (M6), ``rknn_batch_size`` 4 (M7), 32 context (M16), dựng lại ``h6``, A2 tách đầu, thời gian NPU của bản QAT. Đã phân tích thêm từ file có sẵn: G7a, G10, M1 và vết của 8 hàng FP16 của bản QAT.
   - G7: NPU chạy Resize micro model B (``half_pixel``, ``floor``) cho kết quả của A (``asymmetric``, ``floor``) chứ không phải kết quả đúng của B (lệch 6.57 so với onnxruntime của B, chênh 0.0019 so với A). Với kết quả này, thuộc tính bị bỏ qua trong thí nghiệm này. "Vì sao lên NPU" vẫn chưa biết.
   - G11: Relu đứng riêng trong micro model chạy NPU và chia 33.8%/33.8%/32.5% ở ``CORE_0_1_2``. Nghĩa là toolkit và runtime 2.3.2 chia Relu đứng riêng, trái với dòng Relu của Operator List và phù hợp với hai guide liệt kê Relu đa nhân. Đây là micro model, không phải Relu trong YOLO.
   - M4: ba luồng dùng chung một context: không exception, nhưng 300 trên 300 đầu ra khác tham chiếu tuần tự (lệch tối đa 1.04). Phép đối chứng cùng mã với một luồng cho 0 khác biệt. S2 không dùng chung context giữa các luồng, nên kết quả này không áp vào S2.
   - M16: tạo được 32 context, đều chạy đúng, dừng ở ngưỡng chặn 32, không phải giới hạn thật. M6: ``async_mode=True`` được chấp nhận và ``inference`` tuần tự vẫn trả đầu ra của chính ảnh vừa gửi. M7: batch 4 chạy, đầu ra từng ảnh khớp batch 1 ở lần chạy đầu (lệch 0) nhưng một ảnh lệch 0.19 ở lần chạy lặp.
   - ``h6``: dựng lần hai cho file khác byte và cùng AP50-95 (30.18), nguyên nhân ``h6`` tệ hơn vẫn chưa biết.
   - A2 tách đầu: AP50-95 INT8 49.96, đạt tiêu chí 47.98. QAT: NPU 13.84 ms ở ``CORE_0``, chậm hơn A1 PTQ tách đầu 6.3% và nhanh hơn ``int8h5`` 15.5% (phần NPU), tổng với giải mã CPU chậm hơn ``int8h5`` 5.48 ms.
   - M2: ``core_mask`` ``NPU_CORE_ALL`` (0xffff) chia 29 dòng, đúng tập dòng của ``CORE_0_1_2``, còn ``AUTO`` chia 0 dòng. Điều bài EDGE gọi là ``ALL`` vẫn chưa biết.
   - Vẫn chưa biết (nhãn cuối, đã ghi điều đã thử): quy tắc chia job của ``librknnrt`` (M1 chỉ mô tả), nguyên nhân ``h5`` lấy lại điểm, ``mmse``, QAT với torch 1.10 đến 1.13.1. Người dùng đã quyết định ngày 2026-11-01: M8 mục tiêu 60 FPS (:doc:`03-ket-qua-da-nhan` mục 8) và duyệt P2 và P3 (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).

Kiểm kê và lớp của từng mục ở ``results/phase2e_unknowns_inventory.md``, quy tắc viết trước dữ liệu ở ``bench/onboard_q2e/rule_*.txt`` và ``bench/onboard_q2e_qat/rule.txt`` (run ``ppe5_yolov8n_baseline_100ep_s0``). Trang liên quan: :doc:`../03-tang-npu-don-bay/01-operator-support`, :doc:`../03-tang-npu-don-bay/02-multi-core`, :doc:`05-ket-qua-luong-tu-hoa`, :doc:`07-ket-qua-qat-kien-truc`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Bảng nhãn cuối
===================

.. list-table::
   :header-rows: 1
   :widths: 14 34 44 12

   * - Mục
     - Câu hỏi
     - Nhãn cuối
     - Mục trong trang này
   * - G7
     - Vì sao Resize ``asymmetric`` vẫn lên NPU
     - Đo một phần: thuộc tính bị bỏ qua ở micro model. Vì sao lên NPU: vẫn chưa biết
     - 2
   * - G10
     - Reshape 8 nút ONNX, 7 dòng RKNN, Split
     - Đo (mô tả): số học các dòng khớp. Vì sao 3 Reshape và các Slice không có dòng cùng tên: vẫn chưa biết
     - 3
   * - G11
     - Hai guide và Operator List khác nhau về Relu
     - Đo ở micro model: Relu đứng riêng chia ba nhân. Không phân xử tài liệu
     - 4
   * - M1
     - Quy tắc chia job của ``librknnrt``
     - Đo (mô tả mẫu). Quy tắc: vẫn chưa biết
     - 5
   * - M2
     - ``ALL`` trong Table 4 của EDGE
     - Đo một phần: ``NPU_CORE_ALL`` chia như ``CORE_0_1_2`` ở runtime này. Nghĩa trong bài EDGE: vẫn chưa biết
     - 6
   * - M4
     - Một context cho nhiều luồng
     - Đo: đầu ra sai khi ba luồng dùng chung, không có exception
     - 7
   * - M6
     - ``async_mode``
     - Đo một phần: được chấp nhận, đầu ra là của ảnh vừa gửi trong phép thử tuần tự. Gửi nhiều ảnh liên tiếp: chưa thử
     - 7
   * - M7
     - ``rknn_batch_size``
     - Đo: batch 4 chạy, khớp batch 1 ở lần đầu, một ảnh lệch ở lần lặp (không tái lập)
     - 7
   * - M8
     - Mục tiêu FPS
     - Người dùng chốt 60 FPS (2026-11-01), kiểm tra đạt hoặc không đạt ở :doc:`03-ket-qua-da-nhan` mục 8
     - 6
   * - M16
     - Số context tối đa
     - Đo: không lỗi tới 32, giới hạn thật vẫn chưa biết
     - 7
   * - ``h6`` tệ hơn
     - Vì sao ``h6`` thấp hơn base 6.57 điểm
     - Đo: tái lập được, nguyên nhân vẫn chưa biết
     - 8
   * - ``h5`` lấy lại điểm
     - Nguyên nhân
     - Vẫn chưa biết (hết ngân sách)
     - 8
   * - ``mmse``
     - Hết bộ nhớ
     - Không chạy (sai lệch danh tính hiệu chuẩn)
     - 8
   * - 8 hàng FP16 của QAT
     - Vì sao
     - Đo (mô tả vị trí). Nguyên nhân: vẫn chưa biết
     - 9
   * - Thời gian NPU của QAT
     - Độ phủ và thời gian
     - Đo dưới P2
     - 9
   * - QAT với torch 1.10 đến 1.13.1
     - Ảnh hưởng của phiên bản
     - Không chạy (cần bộ công cụ thứ hai)
     - 8
   * - A2 tách đầu
     - Tách lượng tử hóa đầu ra ltrb khỏi phép giải mã
     - Đo: đạt tiêu chí
     - 9

2. G7: thuộc tính của Resize
==============================

Hai node Resize của model ``int8_input.onnx`` có ``mode`` ``nearest``, ``coordinate_transformation_mode`` ``asymmetric`` và ``nearest_mode`` ``floor`` (:doc:`../03-tang-npu-don-bay/01-operator-support` mục 4.3). Quy tắc ``rule_pc.txt`` và ``rule_micro.txt``.

**G7a, onnxruntime.** Ở tỉ lệ 2 (cũng ở 1.5 và 3), bộ ``half_pixel`` với ``round_prefer_floor`` cho đầu ra giống hệt bộ ``asymmetric`` với ``floor`` (lệch 0, trên đầu vào 1x256x20x20 là hình dạng của Resize đầu tiên trong bảng layer). Bộ ``half_pixel`` với ``floor`` lệch 6.57 ở tỉ lệ 2. Bộ ``align_corners`` giống ở tỉ lệ 2 và lệch 6.17 ở tỉ lệ 1.5. Nghĩa là quan sát cũ "đổi sang giá trị được liệt kê cho bảng build giống hệt" (:doc:`../03-tang-npu-don-bay/01-operator-support`) có thể chỉ vì các bộ thuộc tính đó cho cùng chỉ số nguồn ở hình dạng thử, chứ chưa nói gì về cách compiler xử lý thuộc tính.

**G7b, NPU.** Ba micro model Resize (đầu vào 1x256x20x20, tỉ lệ 2), FP16, chạy trên board:

.. list-table::
   :header-rows: 1
   :widths: 26 28 28 28

   * - Bộ thuộc tính
     - Lệch NPU so với onnxruntime của chính nó
     - Lệch NPU so với onnxruntime của A
     - Dòng Resize
   * - A (asymmetric, floor)
     - 0.0019
     - 0.0019
     - NPU, WorkLoad 100.0%/0.0%/0.0%
   * - B (half_pixel, floor)
     - 6.5713
     - 0.0019
     - NPU, WorkLoad 100.0%/0.0%/0.0%
   * - C (half_pixel, round_prefer_floor)
     - 0.0019
     - 0.0019
     - NPU, WorkLoad 100.0%/0.0%/0.0%

Ngưỡng khớp viết trước là 0.01 (làm tròn FP16 của giá trị tới khoảng 7 không quá khoảng 0.004). B là bộ duy nhất khác A trong onnxruntime (6.57) và đầu ra NPU của B khớp A chứ không khớp B. Theo bảng đọc viết trước: B chạy như A, thuộc tính ``half_pixel`` và ``floor`` bị bỏ qua. C khớp cả hai nên không kết luận gì. Cả ba bộ đều được xếp lên NPU, một nhân. Vì sao Resize của YOLO được xếp lên NPU: chưa biết, không có văn bản, phép đo này không trả lời câu đó. Giới hạn: một hình dạng (1x256x20x20, đúng đầu vào của Resize đầu tiên trong bảng layer, đầu ra 1x256x40x40), tỉ lệ 2, FP16, toolkit 2.3.2.

3. G10: số dòng Reshape và Split
==================================

Đối chiếu nút của ONNX mà toolkit đã nhận (``int8_input.onnx``, 237 nút) với 119 dòng của bảng layer. Quy tắc ``rule_pc.txt`` (kèm addendum: so khớp tên chính xác thay cho "chứa").

- Reshape: 8 nút ONNX, 7 dòng RKNN. Ba nút không có dòng cùng tên (``/model/model.22/Reshape``, ``Reshape_3`` và ``dfl/Reshape_1``). Hai dòng RKNN không có nút ONNX cùng tên (``Sigmoid_output_0_rs`` và ``output0-rs``, tên do compiler đặt). Số học: 8 trừ 3 cộng 2 bằng 7.
- Split: 8 nút Split ONNX đều có dòng Split cùng tên, thêm một dòng Split tên ``/model/model.22/Slice_2sp``. Cả 4 nút Slice ONNX đều không có dòng trùng tên chính xác, nên theo tên không biết dòng ``Slice_2sp`` sinh từ nút Slice nào (tên gần nhất là ``/model/model.22/Slice``). Tổng 9 dòng Split.

Số học các dòng được giải thích, vì sao ba nút Reshape và các nút Slice không có dòng cùng tên (gộp vào dòng khác, hay xóa) vẫn chưa biết. Phép đối chiếu chỉ theo tên.

4. G11: Relu đứng riêng
=========================

Micro model một node Relu (1x64x80x80, FP16). Kết quả ở ``CORE_0_1_2``: dòng Relu chạy NPU, ``WorkLoad`` 33.8%/33.8%/32.5%. Ở ``CORE_0``: 100.0%/0.0%/0.0%. Đầu ra khớp onnxruntime (lệch 0.0019). Operator List ghi Relu đứng riêng không hỗ trợ đa nhân và hai guide liệt kê Relu là đa nhân (:doc:`../03-tang-npu-don-bay/01-operator-support` mục 6.1). Trong phép thử này toolkit và runtime 2.3.2 chia Relu đứng riêng, phù hợp với hai guide. Giới hạn: một micro model, không phải Relu trong đồ thị YOLO (model ReLU dùng ``ConvRelu``, 51 trên 51 dòng chia). Kết quả cho biết hành vi của phiên bản này, không phải tài liệu nào đúng.

5. M1: mẫu chia job quan sát được
===================================

Từ bảng ``WorkLoad`` của các phiên ``CORE_0_1_2`` (``bench/onboard_g4b``), mỗi model một phiên. Đây là mẫu quan sát, không phải quy tắc.

.. list-table::
   :header-rows: 1
   :widths: 10 60 30

   * - Model
     - Op có dòng chia (số dòng chia trên tổng dòng của op)
     - Mỗi nhân nhận trong dòng chia
   * - SiLU
     - ``ConvExSwish`` 0/57, ``Split`` 0/9, ``Add`` 8/8, ``Concat`` 15/17, ``Conv`` 6/7
     - 30% đến 35%
   * - ReLU
     - ``ConvRelu`` 51/51, ``Split`` 0/9, ``ConvReluAdd`` 6/6, ``Concat`` 15/17, ``Conv`` 6/7, ``Add`` 2/2
     - 25% đến 37.5%

Quan sát: ở model SiLU không dòng ``ConvExSwish`` nào chia (0 trên 57) còn ở model ReLU mọi dòng ``ConvRelu`` chia (51 trên 51). Dòng ``Add``, ``Concat`` và sáu ``Conv`` ở đầu ra chia gần đều ba phần (mỗi nhân nhận từ 30% đến 35% ở SiLU). ``Split``, ``MaxPool``, ``Resize`` và ``Reshape`` không chia. Quy tắc của ``librknnrt`` nằm trong binary không có mã nguồn: vẫn chưa biết.

6. M2 và M8
=============

**M2** (``ALL`` trong Table 4 của EDGE): đã tìm lại toàn bộ bài báo và T1 ngày 2026-10-31, bài không định nghĩa ``ALL`` và header ghi ``0xffff`` chọn nhân theo nền tảng. :doc:`../03-tang-npu-don-bay/02-multi-core` mục 6.1 nêu một đường chưa dùng là đo ``ALL`` trên board, nên bảng kiểm kê ban đầu xếp M2 vào nhóm hết ngân sách là sai và đã sửa (``rule_core_all.txt``). Phép đo (``ai/automation/probe_core_all.py``, mô hình INT8 chuẩn của seed 0, bảng layer ``perf_debug`` một lần mỗi mặt nạ): ``AUTO`` chia 0 dòng, ``CORE_0_1_2`` chia 29 dòng và ``NPU_CORE_ALL`` chia 29 dòng, đúng cùng tập với ``CORE_0_1_2``. Trung vị latency một phiên không ghim: ``AUTO`` 19.14 ms, ``CORE_0_1_2`` 19.29 ms, ``ALL`` 19.27 ms, chỉ mô tả (một phiên, không dưới P2). Kết quả cho biết ``NPU_CORE_ALL`` chia đúng tập dòng của ``CORE_0_1_2`` (file kết quả chỉ ghi tên các dòng chia, không ghi số nhân từng dòng). Điều bài EDGE gọi là ``ALL`` vẫn chưa biết. **M8** (mục tiêu FPS): người dùng chốt 60 FPS ngày 2026-11-01, kiểm tra đạt hoặc không đạt ở :doc:`03-ket-qua-da-nhan` mục 8 (cấu hình một context chưa đạt, hai context, S2 và S3 đạt theo thông lượng, đo với model INT8 mặc định, ``int8h5`` không khác ``int8`` về thông lượng theo :doc:`09-ket-qua-don-bay-fps`).

7. M4, M6, M7, M16: thăm dò RKNNLite
======================================

Chạy trên board bằng ``ai/board/probe_runtime.py``, model INT8 chuẩn của seed 0, 8 ảnh nhiễu cố định, so đầu ra với tham chiếu tuần tự một context (``rule_probe.txt``). Không dưới P2 hay P3, thời gian chỉ mô tả.

- **M4** (một context cho ba luồng, mỗi luồng 100 lần gọi): 300 lần gọi, 0 exception, 300 đầu ra khác tham chiếu (lệch tối đa 1.04). Phép đối chiếu M4c (cùng mã, một luồng, 300 lần): 0 khác biệt, 0 exception. Vì M4c khớp hoàn toàn, phép so sánh hợp lệ và khác biệt của M4 đến từ việc ba luồng dùng chung một context. Runtime không báo lỗi khi sai, nên dùng chung một context giữa các luồng cho đầu ra sai âm thầm trong phép thử này. Điều này phù hợp với việc S2 dùng một context mỗi luồng. Nguyên nhân vì sao sai chưa biết.
- **M6** (``async_mode=True``): ``init_runtime`` thành công, tám lần ``inference`` tuần tự đều trả đầu ra khớp tham chiếu của chính ảnh vừa gửi (lệch 0) và khác đầu ra của ảnh trước. Hành vi khi gửi nhiều ảnh không đợi kết quả: chưa thử, thời gian không đo.
- **M7** (``rknn_batch_size`` 4, FP16): batch 4 dựng và chạy được, đầu ra [4, 9, 8400]. Lần chạy đầu: từng ảnh khớp batch 1 (lệch 0). Lần chạy lặp (chạy thêm chỉ để lưu log console, ``probe_m7b.json``): ảnh thứ ba lệch 0.19 so với batch 1, ba ảnh còn lại lệch 0. Nên kết quả "khớp" không tái lập giữa hai lần chạy, nguyên nhân chưa biết. Log console của lần lặp (``probe_m7_console.log``) ghi: "core mask = 1 is invalid for batch size: 4, fall back to CORE_AUTO mode" (``E RKNN``). Thời gian một lần gọi (lần chạy đầu, ``probe_m7.json``): batch 1 41.9 ms, batch 4 90.2 ms (22.5 ms mỗi ảnh). Hai số khác chế độ nhân (batch 4 rơi về ``CORE_AUTO``) và đo qua Python, chỉ mô tả, không so được với số P2.
- **M16** (nhiều context): tạo 32 context liên tiếp, mỗi context chạy một lần đúng, ``MemAvailable`` giảm từ 3209 MiB trước khi tạo context (và 3182 sau context đầu) xuống 2651 MiB. Dừng ở ngưỡng chặn 32, không có lỗi: giới hạn thật vẫn chưa biết, chỉ biết không nhỏ hơn 32 trên board này.

8. Nhãn cuối của các mục 2c và 2d còn lại
===========================================

- **Dựng lại ``h6``** (``rule_h6.txt``): file dựng lần hai (sha256 ``40e3ef03``) khác byte file lần đầu (``4fa1ae1e``) nhưng AP50-95 trên ``css_test`` giống nhau (30.18) và AP50 giống nhau (48.93). Theo bảng đọc viết trước: byte dựng không tất định nhưng độ chính xác tái lập, tức mức giảm 6.57 điểm tái lập qua hai lần dựng. Nguyên nhân vẫn chưa biết, và một lần dựng lại chưa đủ để nói gì thêm về nhiễu dựng. File lần đầu được khôi phục vào chỗ cũ, file lần hai ở ``bench/onboard_q2e/h6_second/``.
- **``h5`` lấy lại điểm:** đã dùng ``h1`` đến ``h4``, ``h6``, ``c_all``, ``kl`` và ``auto`` (:doc:`05-ket-qua-luong-tu-hoa`), hết ngân sách, không có đường mới trong ngân sách: vẫn chưa biết.
- **``mmse``:** dựng với 300 ảnh bị hệ điều hành dừng (mã 137). Giảm số ảnh hiệu chuẩn làm sai lệch danh tính hiệu chuẩn (cặp md5 chung), nên không chạy: không có kết quả.
- **QAT với torch 1.10 đến 1.13.1** (khuyến nghị UG232 tr.156): cần môi trường torch và python tương thích, venv hiện dùng python 3.12 và torch 2.4.0. Không chạy, không có kết quả.

9. QAT và A2 tách đầu
=======================

**Vị trí 8 hàng FLOAT16 của bản QAT** (``rule_pc.txt``). Hai nhóm hàng giống nhau, ở id 47, 48, 49, 50 và 59, 60, 61, 62: ``exSwish`` (FLOAT16), ``exDataConvert`` (lượng tử hóa), ``Resize`` (FLOAT16), ``exDataConvert`` (chuyển FLOAT16 về INT8). Ngay trước mỗi nhóm là một dòng ``Conv`` INT8 và một ``exDataConvert`` khử lượng tử hóa. Ở bản PTQ tách đầu, Conv và SiLU đứng trước hai Resize hợp thành ``ConvExSwish`` INT8 và hai dòng Resize là INT8. Nghĩa là trong bản QAT, phần SiLU của lớp Conv ngay trước hai Resize bị tách ra chạy FP16 cùng với Resize. Nguyên nhân chưa biết.

**Thời gian NPU của QAT** (``bench/onboard_q2e_qat``, dưới P2, mọi phiên thực hiện đúng). Trung vị hai phiên:

.. list-table::
   :header-rows: 1
   :widths: 40 24 28

   * - Model
     - CORE_0 (ms)
     - CORE_0_1_2 (ms)
   * - ``int8h5`` (lai)
     - 16.382
     - 15.898
   * - A1 tách đầu (chỉ NPU)
     - 13.020
     - 12.554
   * - QAT tách đầu (chỉ NPU)
     - 13.840
     - 13.329

QAT khác A1 ở ``CORE_0`` 0.820 ms (6.3%, lớn hơn chênh hai phiên 0.016 ms) nên là "khác", và nhanh hơn ``int8h5`` 2.542 ms. Tổng với giải mã CPU của A1 (8.02 ms, hai tensor đầu ra cùng hình dạng, không đo lại): 21.86 ms so với 16.382 ms của ``int8h5``, chậm hơn 5.48 ms nếu không chồng lấp, tổng của hai trung vị đo riêng (chồng lấp giải mã đã đo cho A1 ở :doc:`09-ket-qua-don-bay-fps`, chưa đo riêng cho bản QAT). Độ phủ đa nhân của bản QAT: 3.4% cycles ở các dòng chia (tiêu chí 50% chỉ để mô tả). Tổng cycles của bảng QAT (5532317) bằng đúng tổng của bản PTQ tách đầu dù có thêm 8 hàng FP16, điều này chưa được giải thích.

**A2 tách đầu** (``rule_nodfl_split.txt``). Hai kiểm tra hợp lệ qua (giải mã float của ONNX lệch 1.4e-07, FP16 tách đầu chênh -0.14 điểm so với FP16 chuẩn của A2). INT8 tách đầu của A2 đạt AP50-95 49.96 trên ``css_test`` (AP NoHelmet 32.24, AP Vest 56.04), hơn FP16 tách đầu +0.77, hơn FP16 chuẩn +0.63, hơn INT8 mặc định +13.21 điểm, đạt tiêu chí 47.98. Đồ thị NPU có 106 hàng toàn INT8, không op CPU ngoài Input và Output. Theo bảng đọc viết trước: khi xuất thẳng đầu ra ltrb và logit class, INT8 đạt FP16, nên việc lượng tử hóa đầu ra của lớp hồi quy không phải nguồn chính của mức rơi, phần đuôi tính toán của phép giải mã được ủng hộ, giống A1 nhưng không có DFL. Đây không phải cơ chế. Thời gian của A2 tách đầu không đo.

10. Việc còn lại và giới hạn
==============================

- Đã được người dùng quyết định: P2 và P3 duyệt (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`), mục tiêu FPS 60 (:doc:`03-ket-qua-da-nhan` mục 8). Cách hiểu 60 FPS (một luồng hay tổng, thông lượng hay thời gian mỗi khung) cần người dùng xác nhận.
- Vẫn chưa biết: nghĩa của ``ALL`` trong bài EDGE (M2), quy tắc chia job (M1), vì sao Resize lên NPU (G7), vì sao ba Reshape và các Slice không có dòng cùng tên (G10), nguyên nhân của ``h5``, ``h6``, 8 hàng FP16 của QAT, giới hạn số context (M16), hành vi ``async_mode`` khi gửi nhiều ảnh liên tiếp (M6).
- Không chạy: ``mmse`` (đổi danh tính hiệu chuẩn), QAT với torch 1.10 đến 1.13.1 (cần bộ công cụ thứ hai).
- Mọi kết quả là một board, một lần chạy mỗi phép đo, một seed, micro model không phải op trong YOLO, thời gian dưới P2.

11. Tái lập
=============

.. code-block:: bash

   .venv/bin/python -m ai.automation.analyze_q2e_pc            # G7a, G10, M1, vết QAT (PC)
   .venv/bin/python -m ai.automation.micro_ops 192.168.137.49:5555   # G7b, G11 (board, rknn_server)
   .venv/bin/python -m ai.automation.build_batch_probe          # M7 dựng batch 1 và 4 (PC)
   # board: .venv-board/bin/python -m ai.board.probe_runtime m4|m4c|m6|m7|m16 --model <rknn_int8 dir> --out <json>  (M7 thêm --b1 --b4)
   .venv/bin/python -m ai.automation.build_split ppe5_yolov8n_nodfl_100ep_s0 int8   # A2 tách đầu (cũng fp16)
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_nodfl_100ep_s0 --backend rknn --precision int8 --variant split --board minhnhat@192.168.137.49 --board-repo rk3588
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2e_qat/q2e_qat_driver.py   # thời gian QAT dưới P2 (helper x4_hold.sh đang chạy)
   .venv/bin/python -m ai.automation.probe_core_all 192.168.137.49:5555   # M2 (board, rknn_server)
   .venv/bin/python -m ai.automation.analyze_q2e_board
   .venv/bin/python docs/tools/gen_phase2e_results_page.py

Số liệu: ``results/q2e_pc.json``, ``q2e_micro.json``, ``q2e_core_all.json``, ``q2e_board.json``. Sau lần sửa mã ``decode_split`` cho ``reg_max``, board cần ``make board-sync`` trước khi chấm A2 tách đầu.
