*************
Tensor layout
*************

.. admonition:: Trang này trả lời

   - Dự án thấy layout nào ở đâu trong đường từ ảnh đến đầu ra của YOLOv8n INT8 trên RK3588?
   - Op layout nào nằm trên CPU, tốn bao nhiêu thời gian theo bảng layer, và nguồn gốc của nó là gì?
   - Layout có đòn bẩy FPS nào, đòn bẩy nào đã đo, đòn bẩy nào chỉ có nguồn, đòn bẩy nào chưa biết?

.. admonition:: Tóm tắt

   1. Đầu vào trên board là tensor ``(1, 640, 640, 3)`` uint8 RGB (NHWC), lời gọi ``rknn.inference`` không đặt ``data_format`` hay ``pass_through``. Trong bảng layer, tensor ``images`` hiện ở dạng NC1HWC2 và đầu ra ``output0`` ở dạng UNDEFINED [T3 board, ``ai/board/common.py:65``, build log h5 dòng 454 và 623].
   2. Đường thường của API: chuẩn hóa, lượng tử hóa, chuyển layout và giải lượng tử hóa chạy trên CPU. Vendor mô tả zero-copy là cách hiệu quả hơn cho luồng đầu vào [T1 UG232 tr.8].
   3. Op layout duy nhất trên CPU trong bảng layer là một dòng ``Transpose`` (FLOAT16 ở bản ``int8h5``, INT8 ở các bản INT8 khác), 571.5 us (SiLU) và 573.0 us (ReLU) ở ``core0``. Nó có trong 10 trên 12 log build và không có ở cả hai log tách đầu [T3 board, ``results/npu/operator_support/g4_latency_workload.json``].
   4. Nguồn gốc của dòng này là nút ONNX ``dfl/Transpose``, đồ thị ONNX chỉ có một nút Transpose và các pass đồ thị chỉ viết lại nó [T3 board, ``results/npu/operator_support/q2e_pc.json``, build log h5 dòng 73].
   5. Chi phí riêng của Transpose khi chạy thật: chưa tách. Số đo A1 tách đầu đổi nhiều thứ cùng lúc nên không quy cho riêng Transpose.
   6. Ba đòn bẩy: L1 bỏ Transpose qua tách đầu (ĐO gộp), L2 zero-copy (NGUỒN, chưa thử), L3 ``pass_through`` (ĐO một lần ở harness C và bị từ chối).

Kiến thức nền về NC1HWC2 ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2`. Kết quả FPS của các đòn bẩy sẽ ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không giải thích lại định dạng NC1HWC2, bảng C2 theo kiểu số hay điều kiện căn chỉnh zero-copy. Phần đó đã có ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2` và :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api`. Chỉ các điểm cần cho quyết định của dự án được nhắc lại, kèm thẻ nguồn. Tầng bộ nhớ và di chuyển dữ liệu nói chung ở :doc:`../../01-kien-thuc-nen/02-npu/02-dataflow-va-phan-cap-bo-nho`.

Mục tiêu FPS của người dùng là 30 FPS, đổi từ 60 ngày 2026-11-08 vì camera chỉ có 30 khung/giây (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Hiểu là một luồng camera, ngân sách 33.33 ms mỗi khung. Mọi cấu hình đã đo đạt mốc này theo cả thông lượng lẫn thời gian mỗi khung, nên trang này nói đòn bẩy có thể đổi thời gian ở đâu, không coi đòn bẩy nào là cần để đạt mục tiêu.

2. Layout mà dự án nhìn thấy
============================

Định nghĩa bốn định dạng của RKNN (NHWC, NCHW, NC1HWC2, UNDEFINE) và công thức C1 ở trang nền. Với RK3588, C2 bằng 16 cho int8 và 8 cho float16 [T1 UG232 tr.61]. Layout gốc của NPU là layout cho hiệu năng tốt nhất: "NATIVE_LAYOUT: It refers to the native layout of NPU. In other words, it has the best performance when NPU is processing data with this memory layout." [T1 UG232 tr.11].

Bảng sau là những gì dự án thực sự quan sát, theo vị trí trong đường dữ liệu.

.. list-table::
   :header-rows: 1
   :widths: 22 26 52

   * - Vị trí
     - Quan sát
     - Nguồn
   * - Đầu vào phía board (Python)
     - ``(1, 640, 640, 3)`` uint8 RGB. Lời gọi ``rknn.inference(inputs=[inp])`` không có ``data_format`` hay ``pass_through``
     - [T3 board, ``ai/board/common.py:65``, ``ai/board/infer_dump.py:41``]
   * - Quy ước của vendor cho đầu vào RKNNLite
     - Đầu vào 4 chiều: buffer phải theo NHWC. Toolkit-2 mặc định layout đầu vào là NHWC
     - [T1 UG232 tr.39], [T1 API232 tr.17]
   * - Tensor ``images`` trong bảng layer
     - Dòng 1 (``ConvExSwish``): INT8, NC1HWC2, OrigShape ``(1,3,640,640)``, NativeShape ``(1,1,640,640,3)``
     - [T3 board, build log h5 dòng 454]
   * - Tensor FLOAT16 ở đầu DFL
     - NativeShape có chiều cuối 8, ví dụ dòng 101: ``(1,64,105,80)`` thành ``(1,32,105,80,8)``. Các op ``exDataConvert`` INT8 chạy trên NPU
     - [T3 board, build log h5 dòng 422, 439, 590]
   * - Đầu ra ``output0``
     - FLOAT16, UNDEFINED, ``(1,9,8400)``
     - [T3 board, build log h5 dòng 623]
   * - Cảnh báo compiler
     - 27 dòng ``LayoutMatchManager``: "LayoutMatchManager: recursion_depth=3, Logic is Dangerous, Will Force layout to native."
     - [T3 board, build log h5 dòng 214 đến 240]

Điểm cần đọc đúng: tensor ``images`` có dtype INT8 trong bảng layer lúc build và trong thuộc tính tensor lúc chạy (``type=INT8``, ``zp=-128``, ``scale=0.003922``, :doc:`04-datatype` mục 5), trong khi dữ liệu board đưa vào là uint8 và bảng layer của ``eval_perf`` trên board ghi ``InputOperator`` là UINT8. Dự án không có log nào ghi tham số lượng tử hóa lúc chạy của tensor vào và ra (mục 5).

Về việc ai chuyển layout: vendor viết "Data normalization, quantization, data layout format conversion, and dequantization are performed on the CPU, while model inference is executed on the NPU." [T1 UG232 tr.8]. Khi thỏa điều kiện căn chỉnh của zero-copy thì chuẩn hóa và lượng tử hóa chạy trên NPU nhưng CPU vẫn chép đầu vào: "When alignment requirements for zero-copy input are met, normalization and quantization will run on the NPU, but the input data still needs to be copied to the model's input buffer using the CPU)." [T1 UG232 tr.65]. Trên RK3588 điều kiện chiều rộng là căn 16 pixel: "The input width is 16 pixel aligned for RK3562, RK3588 and RV1106/RV1103" [T1 UG152 tr.19]. Ảnh 640 chia hết cho 16, nhưng repo không dùng đường zero-copy (mục 4).

3. Transpose trên CPU
=====================

3.1. Dòng trong bảng layer
--------------------------

Bảng layer của model ``int8h5`` có đúng một dòng op layout trên CPU, ``Transpose`` FLOAT16 (ở các bản INT8 khác dòng này là INT8, ví dụ ``build_..._base.log`` dòng 395), vào ``(4,1,1,8400)`` và ra ``(1,4,1,8400)``, FullName ``Transpose:/model/model.22/dfl/Reshape_1_output_0_rs`` [T3 board, build log h5 dòng 426]. Dòng này có trong 10 trên 12 file ``build_ppe5_yolov8n_baseline_100ep_s0_*.log`` và không có ở cả hai log ``*_split_*`` [T3 board, ``experiments/npu/operator_support/onboard_q2c/logs/``].

Thời gian của dòng này ở ``core0`` theo bảng layer:

.. list-table::
   :header-rows: 1
   :widths: 24 24 24 28

   * - Model
     - Số dòng
     - Thời gian ``core0`` (us)
     - Tỉ lệ thời gian dòng trong bảng
   * - SiLU
     - 1
     - 571.5
     - 0.0342
   * - ReLU
     - 1
     - 573.0
     - 0.0428

Nguồn: [T3 board, ``results/npu/operator_support/g4_latency_workload.json``, ``by_op.silu.Transpose`` và ``by_op.relu.Transpose``]. Đây là thời gian một dòng trong bảng ``perf_debug``, không phải chi phí đo riêng khi chạy suy luận liên tục.

3.2. Nguồn gốc
--------------

Đồ thị ONNX có đúng một nút Transpose (``/model/model.22/dfl/Transpose``) và bảng RKNN cũng có Transpose 1 [T3 board, ``results/npu/operator_support/q2e_pc.json``, ``g10.onnx_ops`` và ``g10.rknn_ops``]. Log build ghi các pass viết lại chính nút này, ví dụ dòng 73: ``fuse_reshape_transpose: remove node = ['/model/model.22/dfl/Transpose'], add node = ['/model/model.22/dfl/Transpose']`` [T3 board, build log h5 dòng 73, 79, 82, 83, 103]. Nghĩa là dòng Transpose trên CPU là nút ``dfl/Transpose`` của khối giải mã DFL sau khi qua các pass.

Vì sao compiler đặt nó trên CPU: chưa biết. Log không có trường lý do, ``RKNNToolKit2_OP_Support-2.3.2.md`` dòng 190 ghi ``| Transpose | |`` với ghi chú trống, và TRM chương 36 không nêu. TRM nói khối DPU có chức năng transpose và chuyển định dạng dữ liệu: "It also provides function: softmax, transpose, data format conversion, …etc." [T1 TRM1 tr.1985]. Câu này không cho biết điều kiện nào buộc Transpose này rơi xuống CPU.

3.3. Chi phí khi chạy thật
--------------------------

Chưa tách. Số đo gần nhất là A1 tách đầu (:doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`), trong đó đồ thị NPU không còn Transpose. Ở ``CORE_0`` dưới P2, phần NPU của A1 là 13.07 ms so với 16.442 ms của ``int8h5`` (:doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2). Hiệu số này gộp ba thay đổi cùng lúc: bỏ Transpose, bỏ đuôi giải mã khỏi đồ thị và đổi kiểu của các tensor còn lại. Vì vậy dự án không có số cho phần đóng góp riêng của Transpose.

4. Đòn bẩy từ layout
====================

Nhãn trạng thái: ĐO (có số đo T3), NGUỒN (chỉ có tài liệu hoặc mã), CHƯA BIẾT.

.. list-table::
   :header-rows: 1
   :widths: 8 24 12 56

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng và giới hạn
   * - L1
     - Bỏ Transpose khỏi đồ thị NPU bằng tách đầu (A1)
     - ĐO gộp
     - Log tách đầu không có dòng Transpose. Thời gian NPU nhanh hơn nhưng tổng với giải mã CPU chậm hơn nếu không chồng lấp (:doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 9). Đóng góp riêng của Transpose chưa tách. Kết quả FPS khi chồng lấp giải mã: :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`
   * - L2
     - Zero-copy để bỏ bước chuẩn hóa và lượng tử hóa trên CPU
     - NGUỒN
     - Vendor: "The zero-copy API has higher efficiency in handling the input data flow." [T1 UG232 tr.8]. RKNNLite không có API zero-copy và repo không dùng (đã tìm ``zero_copy``, ``set_io_mem``, ``create_mem`` trong ``ai/``, không thấy). Dùng C API chưa thử. Không có số đo
   * - L3
     - ``pass_through`` để đưa thẳng buffer đã ở layout gốc
     - ĐO một lần, bị từ chối
     - Harness C ``ai/board/rknn_perf_bench.c`` đã thử. Ghi chú trong mã (dòng 77 đến 78) viết ``pass_through = 1 was rejected by rknn_inputs_set (expects 4915200 bytes for this 1228800 byte INT8 input)``, nên harness dùng uint8 NHWC với ``pass_through = 0`` ở dòng 95. Nguyên nhân kích thước kỳ vọng gấp 4 lần: chưa biết

Về L3, vendor mô tả hai chế độ: "When pass_through is 0, the input data layout need to be arranged as NHWC. When pass_through is 1, the input data layout need to reshaped as RKNN_TENSOR_NC1HWC2." [T1 UG152 tr.53]. Với ``pass_through`` bằng 1 buffer được đưa thẳng vào nút đầu vào của model và không qua tiền xử lý [T1 RKNNRT tr.15]. Ghi chú của harness cho thấy khi phép chuyển nằm trong ``rknn_inputs_set`` thì nó nằm ngoài đoạn ``rknn_run`` được tính giờ. Nghĩa là số của harness C không gồm bước chuyển layout đầu vào. Với ``rknn.inference`` của harness Python, vendor xếp phép chuyển layout vào phần CPU của đường thường [T1 UG232 tr.8], dự án không tách riêng phần này (xem :doc:`06-memory-copy`).

Probe micro-op ``ai/npu/operator_support/micro_ops.py:64`` là nơi duy nhất trong mã Python của ``ai/`` truyền ``data_format="nchw"``. Nó không nằm trên đường suy luận của pipeline.

5. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Việc
     - Trạng thái
     - Đã tìm gì
   * - Chi phí chuyển layout theo số của vendor (ms hoặc cycles)
     - chưa biết
     - SDK tr.8, 18 đến 19, 61 đến 65, UG152 và RKNNRT chỉ có phát biểu định tính
   * - Chi phí riêng của Transpose khi chạy thật
     - chưa biết
     - Chỉ có số dòng bảng layer (571.5 us) và hiệu A1 gộp nhiều thay đổi
   * - Vì sao Transpose chạy CPU
     - chưa biết
     - Build log không có trường lý do, ``RKNNToolKit2_OP_Support-2.3.2.md`` dòng 190 ghi chú trống, TRM chương 36 không nêu
   * - Tham số lượng tử hóa lúc chạy (zp, scale, kiểu) của tensor vào và ra
     - chưa biết
     - Đã tìm mọi log, json, md của ``onboard_q2c`` và ``ai/core/rknn/*.py``. Build log chỉ có DataType và DataFormat
   * - C2 mà RKNNLite thực sự dùng lúc chạy
     - chưa biết
     - Không có log ghi lại
   * - Chi phí layout trong các bài báo đã có
     - chưa biết
     - Đã grep text 46 PDF trong ``docs/_assets/pdf/papers/``, chưa đọc toàn bộ ba bài ``mobile_multicore_npu_2023jung``, ``flexer_multi_npu_2023min``, ``layer_puzzle_multicore_2023gao``
   * - Mâu thuẫn UINT8 so với INT8 của đầu vào
     - chưa biết
     - Bảng layer lúc build và thuộc tính lúc chạy ghi INT8 cho ``images``, bảng layer của ``eval_perf`` ghi UINT8 cho ``InputOperator``, ``preprocess`` trả uint8. Chưa có log giải thích chỗ chuyển (liên hệ :doc:`04-datatype`)

6. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, tr.8, 11, 39, 61, 65), User Guide RKNN API V1.5.2 (tr.19, 53), API Reference RKNNRT V2.3.2 (tr.12, 15, 27), API Reference Toolkit2 V2.3.2 (tr.17, 18), ``rk3588_part1.pdf`` (TRM1 tr.1985).
- T3: ``ai/board/common.py:65``, ``ai/board/infer_dump.py:41``, ``ai/board/rknn_perf_bench.c:77-98``, ``ai/npu/operator_support/micro_ops.py:64``, ``results/npu/operator_support/g4_latency_workload.json``, ``results/npu/operator_support/q2e_pc.json``, build log ``experiments/npu/operator_support/onboard_q2c/logs/build_ppe5_yolov8n_baseline_100ep_s0_h5.log``.
- Trang liên quan: :doc:`04-datatype`, :doc:`06-memory-copy`, :doc:`07-compiler-optimization`, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
