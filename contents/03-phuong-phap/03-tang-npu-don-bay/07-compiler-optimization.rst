*********************
Compiler optimization
*********************

.. admonition:: Trang này trả lời

   - Compiler của RKNN-Toolkit2 biến đồ thị YOLOv8n thành gì, theo log build của dự án và theo tài liệu vendor?
   - Tùy chọn build hay chỉnh đồ thị nào có thể tăng FPS, cái nào đã đo, cái nào chỉ có nguồn, cái nào chưa biết?
   - Số đo của dự án về các đòn bẩy phía compiler (hybrid ``h5``, tách đầu, chồng lấp giải mã, đổi activation) cho 60 FPS thấy gì?

.. admonition:: Tóm tắt

   1. Log build của model SiLU 5 class ghi 57 lần ``replace_exswish`` (mỗi lần thay một cặp Sigmoid và Mul), 2 lần ``replace_parallel_slice_by_split``, 2 lần ``convert_div_to_mul``, 1 lần ``convert_softmax_to_exsoftmax13`` và 1 lần ``fuse_reshape_transpose``. Đồ thị RKNN có 57 op ``ConvExSwish`` [T3 board, base log dòng 19, 76, 91, ``results/q2e_pc.json``].
   2. Tên ``ConvExSwish`` không có trong bất kỳ tài liệu T1 đã tìm. Operator List có ``ConvolutionSwish`` và ``exSwish``, UG232 có quy tắc Conv+Sigmoid(Silu). Việc ba tên này là một hay khác nhau: chưa biết [T1 UG232 tr.142, T1 OPL mục lục tr.326].
   3. ``optimization_level`` mặc định 3. Mã build của repo không đặt tham số này nên build dùng mặc định [T1 UG232 tr.22, Mã nguồn repo ``ai/automation/build_recipe.py:64``].
   4. Đóng góp FPS riêng của từng fusion: chưa biết. Không có số T1 hay T2, và dự án chưa đo bằng cách tắt từng pass.
   5. Đã đo: K1 hybrid ``h5`` (độ chính xác về mức FP16, latency đổi -0.121 ms ở ``CORE_0`` tức dưới 5%, throughput không phân biệt được), K2 tách đầu (NPU nhanh hơn, tổng chậm hơn nếu không chồng lấp), K3 chồng lấp giải mã (65.99 FPS một context ``CORE_0``), K4 đổi sang ReLU (nhãn Loại).
   6. K5 ``optimization_level`` thấp hơn: chỉ có nguồn, không đo. Vendor nói mức thấp tắt một số tối ưu.
   7. Mục tiêu 60 FPS: đạt theo cách đọc thông lượng ở K3. Theo cách đọc thời gian mỗi khung (16.67 ms), chưa đạt và thời gian mỗi khung ở nhịp 60 FPS chưa đo [T3 board, ``results/q2f_fps.json``].

Kiến thức nền ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/01-luong-onnx-sang-rknn` và :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2`. Kết quả FPS của các đòn bẩy ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không giải thích lại luồng năm lời gọi ONNX sang RKNN, danh sách pass lộ ra trong log của vendor, bảng rule fusion phần cứng hay rule đồ thị con. Phần đó ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/01-luong-onnx-sang-rknn` (mục 2) và :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2` (mục 3). Lý thuyết về fusion, constant folding và tiling ở ``01-kien-thuc-nen/04-compiler/`` (:doc:`../../01-kien-thuc-nen/04-compiler/02-toi-uu-do-thi-va-operator-fusion`, :doc:`../../01-kien-thuc-nen/04-compiler/03-tiling-va-lap-lich-thuc-thi`). Op của YOLOv8 trên RKNN ở :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/02-op-yolov8-tren-rknn`, tiêu chí thân thiện NPU ở :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/03-tieu-chi-than-thien-npu`.

Trang chỉ ghi điều dự án cần cho quyết định: compiler đã làm gì với đồ thị của dự án (quan sát từ log), tùy chọn nào là đòn bẩy, và đã đo gì. Trang cạnh bên: :doc:`03-tensor-layout` (Transpose và layout), :doc:`04-datatype` (hybrid và kiểu số), :doc:`05-memory-access`, :doc:`06-memory-copy`, :doc:`08-npu-architecture`, :doc:`09-pre-post-processing`.

Mục tiêu FPS là 60 (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Người dùng chưa xác nhận đó là một luồng hay tổng nhiều luồng, thông lượng hay thời gian mỗi khung. Mục 5 ghi cả hai cách đọc.

2. Compiler làm gì với đồ thị YOLOv8n
=====================================

2.1. Biến đổi quan sát trong log build
--------------------------------------

Log build INT8 mặc định ghi từng pass tối ưu (``base_optimize``, ``fold_constant``, ``correct_ops``, ``fuse_ops``, ``sparse_weight``, ``quant_optimizer``, ``recover_const_share``) và các pass RKNN nội bộ (``RKNNTilingPass``, ``RKNNMultiSurfacePass``, ``RKNNWeightTransposePass``, ``RKNNCPUWeightTransposePass``, ``RKNNProfileAnalysisPass``, ``ConvStrideFixPass``, ``ConvCachePass``, ``OpEmit``) [T3 board, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2c/logs/build_ppe5_yolov8n_baseline_100ep_s0_base.log`` dòng 6, 9, 12, 15, 120]. Các quy tắc fuse có số lần xuất hiện như sau.

.. list-table::
   :header-rows: 1
   :widths: 40 12 48

   * - Quy tắc trong log
     - Số lần
     - Ý nghĩa quan sát được
   * - ``replace_exswish``
     - 57
     - Mỗi lần gỡ một cặp ``Sigmoid`` và ``Mul`` của một khối activation, thêm một node tên ``..._2swish``
   * - ``replace_parallel_slice_by_split``
     - 2
     - Hai ``Slice`` song song thành một node ``Slice_2sp``
   * - ``convert_div_to_mul``
     - 2
     - Chỉ có trong log, T1 không nhắc
   * - ``convert_softmax_to_exsoftmax13``
     - 1
     - Softmax của DFL thành op ``exSoftmax13`` trong đồ thị RKNN
   * - ``fuse_reshape_transpose``
     - 1
     - Gộp Reshape và Transpose liên tiếp
   * - ``swap_transpose_softmax``, ``swap_transpose_conv``
     - 1 mỗi loại
     - Đổi thứ tự Transpose với Softmax hoặc Conv

Nguồn của bảng là [T3 board, base log dòng 17, 74, 89 và 93]. Dòng 17 có dạng:

   ``replace_exswish: remove node = ['/model/model.0/act/Sigmoid', '/model/model.0/act/Mul'], add node = ['/model/model.0/act/Sigmoid_2swish']``

Dòng 74 ghi hai ``Slice`` của khối ``model.22`` được thay bằng ``Slice_2sp``. Ý nghĩa cột cuối là mô tả log, không phải mô tả cơ chế bên trong toolkit (chưa biết, T1 không công bố pass).

2.2. Đếm op trước và sau
------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - Op
     - ONNX
     - Đồ thị RKNN
   * - Conv
     - 64
     - 7
   * - ConvExSwish
     - không có
     - 57
   * - Sigmoid
     - 58
     - 1
   * - Mul
     - 58
     - không có trong danh sách đếm
   * - Split
     - 8
     - 9
   * - Slice
     - 4
     - không có trong danh sách đếm
   * - Div
     - 2
     - không có trong danh sách đếm
   * - Concat, Add, Reshape, Transpose, exSoftmax13
     - không trích
     - 17, 8, 7, 1, 1

Nguồn: [T3 board, ``results/q2e_pc.json``, trường ``g10.onnx_ops`` và ``g10.rknn_ops``]. Số ``ConvExSwish`` (57) trùng số lần ``replace_exswish`` (57). Bảng layer INT8 và FP16 của cùng model giống nhau về loại op và target (57 ``ConvExSwish`` trên NPU, 1 ``Transpose`` trên CPU, 1 ``InputOperator`` trên CPU) và đều 119 dòng, chỉ khác kiểu số [T3 board, ``export_fp16_20261031-042838.log`` tiêu đề cột dòng 180, base log dòng 290]. Bản ``h5`` có 121 dòng (thêm 2 ``exDataConvert`` INT8 trên NPU, một số dòng Reshape, Sub, Add, Mul, Concat ở FLOAT16 trên NPU). Bản tách đầu INT8 có 106 dòng, không có ``Transpose``, chỉ ``InputOperator`` và ``OutputOperator`` chạy CPU [T3 board, log ``_h5`` và ``_split_int8``, đếm bằng grep]. Chi tiết dòng ``Transpose`` ở :doc:`03-tensor-layout` mục 3 và chi tiết op ở :doc:`01-operator-support`.

2.3. So với tài liệu vendor
---------------------------

UG232 liệt kê quy tắc fusion phần cứng, trong đó có Conv+Relu, Conv+PRelu(LeakyRelu), Conv+Clip, Conv+Sigmoid(Tanh/Elu/Silu...), Conv+Add, Conv+Activation+Add [T1 UG232 tr.142]. Câu dẫn của bảng là "The hardware fusion rules are as follows:" [T1 UG232 tr.142]. Cột bên phải của bảng là quy tắc của kế hoạch tương lai và không nêu chip [T1 UG232 tr.142]. Quy tắc Conv+Sigmoid(Silu) phù hợp với việc log gộp 57 cặp Sigmoid và Mul, nhưng UG232 không có tên op của kết quả gộp.

Các điểm không khớp giữa log và tài liệu, ghi nguyên trạng:

- ``ConvExSwish``: 0 kết quả trong Operator List, UG232, API Reference và Quick Start. Operator List có mục ``ConvolutionSwish`` (3.1.17 và mục tương ứng ở 3.2 đến 3.4) và ``exSwish`` (3.1.65, mục lục 4.90) [T1 OPL mục lục tr.326, tiêu đề mục]. Chưa biết ``ConvExSwish`` là tên khác của mục nào. Đối chiếu SiLU và Swish ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2` mục 3.3.
- Quy tắc ``replace_exswish`` (Sigmoid cộng Mul thành exSwish): không tìm thấy văn bản T1 mô tả.
- ``replace_parallel_slice_by_split`` và ``convert_div_to_mul``: chỉ có trong log T3. Ví dụ của vendor về Slice là gộp nhiều Slice vào một Conv (đồ thị tương đương YOLOv5-nano), "which integrates several complex Slice numbers into Conv to form a new Conv, which greatly simplifies the graph structure." [T1 UG232 tr.142]. Đây là biến đổi khác với Slice thành Split.
- Vendor gộp được Reshape, Transpose, Slice và một số Add, Mul, Sub, Div khi liên tiếp: "such as Reshape, Transpose, Slice, some Add/Mul/Sub/Div, etc." [T1 UG232 tr.143].

Vendor cũng nói toolkit chưa tối ưu hết. Có thể đổi thứ tự Transpose và Clip để Conv và Clip gộp được: "by adjusting the order of the Transpose and Clip operators, the Conv and Clip fusion operations are performed, improving performance." [T1 UG232 tr.141]. Mục 8.4 mô tả các cách này là không bắt buộc [T1 UG232 tr.141].

2.4. Op kém hiệu quả theo vendor
--------------------------------

UG232 Bảng 8-5 khuyên giảm ba nhóm op: chuyển dữ liệu (Transpose, Reshape, Split, Concat), đổi kích thước (Resize, Tile, Pooling, Pad) và activation không phải Relu (Sigmoid, Tanh, Softplus, Hardswish): "Try to reduce the following three types of operators in the model" [T1 UG232 tr.146]. Đồ thị của dự án có Concat 17, Split 9, Reshape 7, Transpose 1 (bảng ở mục 2.2). Vendor cũng lưu ý Reshape và Transpose dư ở đầu và cuối đồ thị ảnh hưởng hiệu năng: "It is common for redundant reshape and transpose ops to exist at the input and output nodes of the model, which affects the inference performance of the RKNN model." [T1 UG232 tr.117]. Mức đóng góp FPS của từng op trong nhóm này ở model của dự án: chưa biết.

3. Tùy chọn build liên quan
===========================

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Tùy chọn
     - Nguồn nói gì
     - Dự án dùng gì
   * - ``optimization_level``
     - Mặc định 3: "The default value of this parameter is 3, which turns on all optimization options." Mức 2 hoặc 1: "When the value is 2 or 1, some optimization options that may affect the accuracy of some models are turned off." Mức 3 là ưu tiên tốc độ [T1 UG232 tr.22, tr.133]
     - Không đặt trong mã build của ``ai/`` nên dùng mặc định 3 (suy từ việc vắng tham số)
   * - ``quantized_dtype``, ``quantized_algorithm``, ``quantized_method``
     - Mặc định ``asymmetric_quantized-8``, thuật toán ``normal``, phương pháp ``channel`` [T1 UG232 tr.122]. API232 liệt kê thêm các kiểu như ``w8a8`` mặc định và ``w4a16``, hai tài liệu mâu thuẫn, xem :doc:`04-datatype` mục 3
     - Hybrid ``h5`` dùng ``hybrid_quantization_step1``, ``custom_quantize_layers`` kiểu ``float16`` rồi step 2 [Mã nguồn repo ``ai/core/rknn/hybrid.py:66, 71, 75``]
   * - ``mean_values``, ``std_values``
     - Dùng trong lượng tử hóa [T1 UG232 tr.22]
     - ``mean_values=[[0, 0, 0]]``, ``std_values=[[255, 255, 255]]``, ``target_platform="rk3588"`` [Mã nguồn repo ``ai/automation/build_recipe.py:64``, ``build_split.py:47``]
   * - ``rknn_batch_size``
     - Chỉ đổi chiều batch của mô hình xuất, trên RK3588 nên là bội số của 3 [T1 UG232 tr.165, tr.105]
     - ``rknn_batch_size=1`` ở ``build_split.py:52``. Kết quả batch 4 ở :doc:`06-memory-copy` mục 5

Xung đột chưa kiểm về Resize: UG232 viết "the Resize Op will use the CPU, and the precision will not drop, but it will cause performance degradation" cho ``optimization_level=2`` [T1 UG232 tr.176]. Ghi chép ``docs/contents/09-tien-do/03-khoang-trong/06-yolo.rst:195`` nói Resize nearest 2x INT8 có Target NPU ở level 1, 2 và 3 [T3 board]. Log gốc của dòng ghi chép đó chưa được kiểm. Log build mặc định (level 3) có Resize INT8 trên NPU ở dòng 338, điều này không mâu thuẫn với UG232 vì UG232 chỉ nói về mức 2. Dự án chưa build ở mức 2 để thử, nên kết luận cho mức 2: chưa biết.

4. Đòn bẩy và kết quả đã đo
===========================

Nhãn: ĐO (có số T3 của dự án), NGUỒN (chỉ có tài liệu), CHƯA BIẾT. Các nhãn đều chưa phải cổng quyết định. Ngưỡng số mới của từng thí nghiệm chưa duyệt, giao thức P2 và P3 đã duyệt (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).

.. list-table::
   :header-rows: 1
   :widths: 8 24 10 58

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng
   * - K1
     - Hybrid ``h5`` (15 tensor nhánh giải mã box giữ FP16, còn lại INT8)
     - ĐO
     - AP50-95 của SiLU từ 36.75 lên 49.66 (FP16: 49.76). Latency đổi -0.121 ms ở ``CORE_0``, dưới 5% [:doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`]. Throughput ``int8h5`` và ``int8`` chênh 0.01% đến 0.68% ở bốn cấu hình, không phân biệt được [T3 board, ``results/q2f_fps.json``, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 2]
   * - K2
     - Tách đầu A1: bỏ ``Transpose`` và đuôi giải mã khỏi đồ thị NPU, giải mã box bằng numpy trên CPU
     - ĐO
     - AP50-95 49.84, đồ thị NPU toàn INT8, không op CPU. NPU 13.07 ms ở ``CORE_0`` nhưng giải mã 8.02 ms, tổng 21.09 ms so với 16.44 ms của ``int8h5`` nếu cùng luồng [T3 board, ``results/q2j_split.json``, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2]
   * - K3
     - Chồng lấp giải mã bằng pipeline (một luồng pre, một NPU, một post)
     - ĐO
     - 65.99 FPS ở một context ``CORE_0``, so với 54.79 của ``int8h5`` tuần tự và 42.05 của tách đầu giải mã cùng luồng [T3 board, ``results/q2f_fps.json``]
   * - K4
     - Đổi SiLU sang ReLU (cổng G4)
     - ĐO
     - Nhãn Loại vì điều kiện C (độ chính xác) trượt: AP50-95 chênh -3.51 điểm, AP NoHelmet -4.94 điểm. Điều kiện A và B đạt [:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`]
   * - K5
     - ``optimization_level`` thấp hơn 3
     - NGUỒN
     - Vendor nói mức thấp tắt một số tối ưu và mức 2 đưa Resize về CPU [T1 UG232 tr.22, tr.176]. Không có số FPS, dự án chưa đo

Điều rút ra từ K1 và K2: model chuẩn của dự án đã dùng hybrid (K1) để lấy lại độ chính xác mà không tốn latency đo được, trong khi K2 đạt cùng độ chính xác bằng cách đưa phần giải mã ra khỏi đồ thị. Hybrid có chi phí theo vendor: lớp chuyển sang không lượng tử hóa chạy chậm hơn trên NPU, làm giảm tốc độ suy luận [T1 UG232 tr.123]. Vendor còn nêu hybrid là cách xử lý khi độ chính xác đủ nhưng hiệu năng chưa đạt: "or if the accuracy is sufficient but the performance does not meet the requirements due to hybrid quantization" [T1 UG232 tr.135]. Ở ``h5`` dự án không thấy chi phí đó trong latency (K1). Vì sao, chưa biết.

K3 không phải tùy chọn của compiler mà là thay đổi cách xếp luồng ở harness trên model tách đầu (kết quả của K2), và là thay đổi duy nhất đã đưa một context lên trên 60 FPS theo thông lượng. Mô tả của phép đo: phần NPU của model tách đầu ngắn hơn phần NPU của ``int8h5`` (13.07 so với 16.44 ms ở ``CORE_0``, K2) và ở điều kiện C trung vị ``T_post`` (11.61 ms) nhỏ hơn ``T_npu`` (15.04 ms). Pipeline một mình không giúp ``int8h5`` (56.62 FPS, không phân biệt được với tuần tự), phép đo không nói vì sao. Thêm một luồng giải mã (D) hay dùng ba lõi cho một context (E) không phân biệt được với K3. Đây là mô tả của phép đo, không phải cơ chế [:doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 4].

5. Đọc theo mục tiêu 60 FPS
===========================

**Đọc theo thông lượng**: K3 đạt (65.99 FPS, khoảng trải 0.03) với một context ``CORE_0``, không cần nhiều context. ``int8h5`` một context chưa đạt (54.79 đến 56.62 FPS) và cần hai context (101.89 FPS) [T3 board, ``results/q2f_fps.json``, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8]. Tổn phí của K3: CPU tiến trình khoảng 100% so với 24% của ``int8h5`` tuần tự, model tách đầu chưa nối vào script demo của repo [:doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 7].

**Đọc theo thời gian mỗi khung** (mỗi khung xong trong 16.67 ms): không điều kiện nào của K3 đạt. Thời gian đầu cuối đo trong pipeline bão hòa lớn hơn 128 ms. Số này gồm thời gian chờ hàng đợi nên chỉ là cận trên, không phải thời gian mỗi khung. Thời gian mỗi khung ở nhịp 60 FPS chưa đo. Thứ tự đầu ra của pipeline được giữ theo cách xây dựng (một luồng mỗi giai đoạn, hàng đợi FIFO) nhưng chưa kiểm.

6. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 44 18 38

   * - Câu hỏi
     - Trạng thái
     - Đã tìm gì
   * - Đóng góp FPS riêng của mỗi fusion (``replace_exswish`` và các quy tắc khác)
     - chưa biết
     - Không có số trong UG232, API Reference, Operator List, Quick Start, và các bài T2 đã lưu. Dự án chưa tắt từng pass
   * - ``ConvExSwish`` là tên nào trong Operator List
     - chưa biết
     - grep bốn tài liệu T1, chỉ thấy ``ConvolutionSwish`` và ``exSwish``
   * - Vì sao pass cho ra đúng các kết quả của log
     - chưa biết
     - T1 không liệt kê pass, chỉ có dấu vết ``GraphOptimizer._fuse_ops`` ở stack trace [T1 UG232 tr.166]
   * - Hành vi ở ``optimization_level`` 0, 1, 2 trên model của dự án
     - chưa biết
     - Chưa build. Xung đột về Resize ở mục 3
   * - Chi phí hybrid ngoài số của ``h5``
     - chưa biết
     - Chỉ có hai câu của vendor (UG232 tr.123, tr.135) và số K1
   * - Thời gian mỗi khung của K3 ở nhịp 60 FPS, thứ tự đầu ra
     - chưa đo
     - :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 7
   * - Cách hiểu mục tiêu 60 FPS
     - chưa xác nhận
     - :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8

7. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, UG232 tr.22, 105, 117, 122, 123, 133, 135, 141, 142, 143, 146, 165, 166, 176), Operator List V2.3.2 (OPL mục lục tr.326).
- T3: base log ``build_ppe5_yolov8n_baseline_100ep_s0_base.log`` dòng 6, 9, 12, 15, 17, 74, 89, 93, 120, 290, 338, ``export_fp16_20261031-042838.log``, ``results/q2e_pc.json``, ``results/q2j_split.json``, ``results/q2f_fps.json``.
- Mã nguồn repo: ``ai/automation/build_recipe.py:64``, ``ai/automation/build_split.py:47, 52``, ``ai/core/rknn/hybrid.py:66, 71, 75``.
- Trang liên quan: :doc:`01-operator-support`, :doc:`03-tensor-layout`, :doc:`04-datatype`, :doc:`06-memory-copy`, :doc:`09-pre-post-processing`, :doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`, :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
