:tocdepth: 1

*************
Operator List
*************

.. admonition:: Trang này trả lời

   - Operator List (OPL) tổ chức thế nào, và một mục op cho biết những gì?
   - Op nào chạy trên NPU, op nào rơi về CPU, và đổi đích chạy bằng cách nào?
   - Ba nguồn về op hỗ trợ (OPL, bảng op của toolkit, user guide) mâu thuẫn ở đâu?

.. admonition:: Tóm tắt

   - OPL V2.3.2 chia theo chip. Mục RK3588 là chương 3.2 với 79 mục op NPU (PDF 56 đến 107), op CPU nằm ở chương 4 và không chia theo chip [T1 OPL tr.3] [T1 OPL tr.319].
   - Mỗi mục op có input, output, ràng buộc kiểu dữ liệu, thuộc tính và dòng "多核联合" (đa lõi). Dòng này chỉ nói về chạy đa lõi, không nói op có chạy NPU hay không [T1 OPL tr.56].
   - Op chạy ngoài NPU vì ba lý do: kích thước vượt giới hạn, chưa hỗ trợ, hoặc phần cứng không làm được [T1 UG232 tr.139]. OPL không viết quy tắc "rơi về CPU".
   - Đích dự phòng khi NPU không hỗ trợ op là ``cpu`` theo mặc định, đổi sang ``gpu`` được trên chip có GPU [T1 API232 tr.17]. ``op_target`` ép từng op hoặc từng loại op sang ``cpu``, ``npu``, ``gpu`` hay ``auto`` [T1 API232 tr.9].
   - Resize mâu thuẫn giữa OPL (có mục NPU, PDF 86 và 87) và UG232 tr.176 ("does not currently support hardware-level Resize"). Danh sách op đa lõi của UG232 tr.75 cũng khác OPL ở Relu, Clip, PRelu, LeakyRelu.
   - Bảng op của toolkit (tệp ``RKNNToolKit2_OP_Support-2.3.2.md``) ghi "Not Supported" cho Hardmax, Not, OneHot, ReduceL2, Round, TopK, ThresholdedRelu, trong khi OPL có mục cho các op này.
   - Ba cách viết "尚不支持", "暂不支持", "不支持" không được OPL định nghĩa. Thuật toán chọn đích của ``auto`` là unknown.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _operator-list-cau-truc:

1. Cấu trúc Operator List
=========================

OPL là tài liệu "RKNN Compiler Support Operator List" bản V2.3.2, mã tài liệu RK-YH-YF-418, ngày 2025-03-28 [T1 OPL tr.7]. Đây là trang chủ về hỗ trợ op trong bộ tài liệu này. Layout NC1HWC2 và fusion nằm ở :doc:`05-fusion-va-layout-nc1hwc2`.

1.1 Các chương
--------------

- Chương 3 "NPU OPs" chia theo chip: 3.1 RK3566/RK3568 (PDF 12), 3.2 RK3588 (PDF 56), 3.3 RK3562 (PDF 108), 3.4 RV1103/RV1106 (PDF 154), 3.5 RK3576/RV1126B (PDF 197), 3.6 RK2118 (PDF 249), 3.7 RV1103B/RV1106B (PDF 286). Số PDF là số trang in cộng 6, đã đối chiếu với tiêu đề 3.2.1 Add ở PDF 56 [T1 OPL tr.3] [T1 OPL tr.56].
- Chương 4 "CPU OPs" liệt kê 98 op (mục 4.2 đến 4.99), mỗi op có mô tả và "规格约束" (ràng buộc), phần lớn ghi "无限制" (không giới hạn) [T1 OPL tr.319] [T1 OPL tr.320]. Số 98 là phép đếm của trang này (suy ra).
- Chương 5 là giới hạn input và output của model (căn lề, xem :ref:`layout-alignment`). Chương 6 định nghĩa ``dilated_kernel_h = kernel_h * dilations_h - dilations_h + 1`` và tương tự cho ``w`` [T1 OPL tr.335] [T1 OPL tr.343].

1.2 Một mục op NPU
------------------

Mục 3.2.1 Add là ví dụ đầy đủ nhất cho cấu trúc. Add chạy phép cộng theo phần tử và hỗ trợ broadcast kiểu Numpy theo mọi chiều [T1 OPL tr.56]. Các trường lặp lại ở hầu hết mục:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Trường (tiếng Trung)
     - Nội dung
   * - ``输入列表`` và ``输出列表``
     - Tên tensor, ``shape`` dạng ``[batch, channel, height, width]``, kiểu lượng tử hóa (``per-layer``, một số có ``per-channel``) và ràng buộc broadcast [T1 OPL tr.56]
   * - ``数据类型约束``
     - Kiểu của các tensor ``T1``, ``T2``. Add dùng ``int8`` và ``float16`` cho ``T1``, ``float`` hằng cho ``T2`` [T1 OPL tr.56]
   * - ``属性列表``
     - Thuộc tính và miền giá trị. Ví dụ Convolution cho ``stride_h`` và ``stride_w`` trong [1, 7], ``kernel_h`` và ``kernel_w`` trong [1, 31] [T1 OPL tr.58] [T1 OPL tr.59]
   * - ``其他支持``
     - Dòng ``多核联合`` (chạy đa lõi) với bốn giá trị ở mục 2.3 [T1 OPL tr.56]
   * - ``说明及规格限制同X``
     - Mục op hợp nhất không lặp lại bảng, trỏ về mục gốc. ConvolutionRelu ghi giống Convolution [T1 OPL tr.60]

Các op hợp nhất thành một mục riêng (ConvolutionRelu, AddRelu và các op cùng họ) và cách hãng nói về fusion được gom ở :doc:`05-fusion-va-layout-nc1hwc2`. Mục 3.2 có 3.2.1 đến 3.2.79. Trong đó họ Convolution chiếm 3.2.5 đến 3.2.19 (15 mục) và họ ConvTranspose chiếm 3.2.20 đến 3.2.32 (13 mục) (suy ra từ tiêu đề mục).

--------------

.. _operator-list-npu-cpu:

2. Op chạy NPU và op rơi về CPU
===============================

2.1 Ba lý do chạy ngoài NPU
---------------------------

UG232 viết trong phần phân tích hiệu năng: op chạy ngoài NPU thường vì ba lý do sau [T1 UG232 tr.139].

   "The operator size exceeds the limit (see the operator size limit in the OpList document)" [T1 UG232 tr.139]

   "The operator does not yet support operation on NPU (check whether OpList supports this operator, you can submit an issue on the Github project)" [T1 UG232 tr.139]

   "NPU hardware limitations cannot support it (can the algorithm be equivalent to other implementations supported by other NPUs)" [T1 UG232 tr.139]

Lý do thứ nhất có hệ quả quan trọng: một op có mục NPU trong OPL vẫn chạy ở CPU nếu kích thước vượt ràng buộc ở mục đó (suy ra từ lý do thứ nhất). OPL không viết quy tắc chung cho trường hợp này. Log mẫu của UG232 với ``--target rk3588`` cho thấy ``InputOperator`` và ``Reshape`` ở cột ``Target`` là ``CPU``, còn ``ConvClip`` và ``Conv`` là ``NPU`` [T1 UG232 tr.56]. OPL có mục 3.2.53 Reshape cho RK3588 [T1 OPL tr.86], và UG232 không nêu vì sao Reshape trong log chạy ở CPU (unknown. Đã tìm ở: UG232 tr.56 và tr.139, từ khóa: ``Reshape``).

2.2 Giới hạn kiểu chiều và hậu xử lý
------------------------------------

   "At present, RKNN does not support 6-dimensional OP. In most cases, it only supports 4-dimensional. Other dimensions will have some limitations." [T1 UG232 tr.168]

   "Post-processing Ops such as NonMaxSuppression , RKNN currently do not support." [T1 UG232 tr.168]

Mục op NPU của OPL mô tả tensor bốn chiều ``[batch, channel, height, width]``, khớp với câu trên. UG232 tr.168 khuyên cắt phần hậu xử lý khỏi đồ thị (tham số ``outputs`` của ``rknn.load_onnx``) và xử lý ở CPU. Khi gặp lỗi ``Expand``, UG232 viết bản mới đã hỗ trợ Expand ở CPU [T1 UG232 tr.168]. OPL có cả mục NPU 3.2.34 Expand (PDF 68) lẫn mục CPU 4.85 Expand (PDF 331) [T1 OPL tr.68] [T1 OPL tr.331].

2.3 Dòng đa lõi trong mỗi mục
-----------------------------

Dòng ``多核联合`` xuất hiện ở 59 trong 79 mục của chương 3.2 (đếm của trang này, suy ra). Dịch từng chữ: ``支持`` là hỗ trợ, ``不支持`` là không hỗ trợ, ``暂不支持`` là tạm chưa hỗ trợ, ``尚不支持`` là còn chưa hỗ trợ. OPL không định nghĩa sự khác nhau giữa ba cách phủ định. UG232 chỉ định nghĩa gián tiếp: op không chia tác vụ đa lõi trong driver "will be supported in subsequent versions" [T1 UG232 tr.75].

.. list-table::
   :header-rows: 1
   :widths: 16 10 74

   * - Giá trị
     - Số mục
     - Ví dụ
   * - ``支持``
     - 11
     - Add, Convolution, Depthwise Convolution, ConvolutionRelu, Mul
   * - ``暂不支持``
     - 18
     - Relu, Clip/ReLU6, PRelu, LeakyRelu, Transpose, Max, Min, LSTM
   * - ``尚不支持``
     - 23
     - BatchNormalization, Softmax, Sigmoid, Tanh, Pad, Reshape, Gather
   * - ``不支持``
     - 7
     - Div, Expand, Resize, Sub, Tile, exMatMul, exSDPAttention
   * - Không có dòng
     - 20
     - Concat, MaxPool, AveragePool, Slice, Split, Where, 12 mục ConvTranspose hợp nhất

Nguồn các giá trị là mục tương ứng trong OPL (ví dụ Add ở PDF 56, Relu ở PDF 83 và 84, Resize ở PDF 87, Div ở PDF 67). Cách chia core và hành vi "fallback to Core0" của chế độ đa lõi được trình bày ở :doc:`../01-phan-cung-npu/03-che-do-da-loi-va-system-sram`.

2.4 Đổi đích chạy của op
------------------------

API232 mô tả hai cơ chế, cả hai không nằm trong OPL.

- Tham số ``fallback_prior_device`` của ``init_runtime``:

   "set fallback prior device when OP is not supported by NPU. currently support: 'gpu' or 'cpu', 'gpu' is only valid for platform which has gpu hardware. The default value is 'cpu'." [T1 API232 tr.17]

  Header runtime có cờ tương ứng ở phía C: ``RKNN_FLAG_EXECUTE_FALLBACK_PRIOR_DEVICE_GPU`` với chú thích "set GPU as the preferred execution backend When the operator is not supported by the NPU" [T1 EX 3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h:65-66].
- Tham số ``op_target`` của ``rknn.config``: khóa là tên tensor đầu ra của op hoặc ``op_type`` (ví dụ ``{'Add':'cpu', 'Expand':'cpu'}``), giá trị là ``cpu``, ``npu``, ``gpu`` hoặc ``auto``, mặc định ``None`` [T1 API232 tr.9]. Tên tensor lấy từ kết quả ``accuracy_analysis`` [T1 API232 tr.9].

Thuật toán mà ``auto`` dùng để chọn đích là unknown. Đã tìm ở: API232, UG232, UG152, OPL, từ khóa: ``auto``, ``op_target``, ``automatically select``. UG232 tr.141 tóm tắt cách khắc phục từ phía mô hình: thay op chưa chạy NPU bằng phép tương đương mà NPU hỗ trợ, ví dụ thay Transpose và Reshape trong channel shuffle bằng Conv trọng số 0 và 1 [T1 UG232 tr.141].

2.5 Op CPU trong OPL
--------------------

Chương 4 chỉ nêu giới hạn theo chip ở mục 4.1: RK2118 "không hỗ trợ tất cả CPU op" và nhóm RV1106/RV1103/RV1106B/RV1103B chỉ hỗ trợ 11 op gồm Concat, DataConvert, Div, exLayerNorm, Exp, Gather, ReduceL2, ReduceMax, Reshape, ScatterND, Softmax [T1 OPL tr.319]. Câu về RK2118 viết ngắn, có thể hiểu là "không có op CPU nào" hoặc "không đủ hết", OPL không phân xử (unknown. Đã tìm ở: OPL tr.319). Không có ghi chú loại trừ nào cho RK3588, nên với RK3588 OPL không nêu giới hạn riêng cho op CPU (suy ra từ việc không có ghi chú).

Ví dụ Resize CPU (mục 4.50) "bilinear; nearest2d" và Upsample (mục 4.67) cùng ràng buộc đó [T1 OPL tr.326] [T1 OPL tr.329]. Upsample chỉ có ở chương CPU, không có mục NPU trong 3.2 (suy ra từ danh sách mục 3.2.1 đến 3.2.79) [T1 OPL tr.329].

--------------

.. _operator-list-mau-thuan:

3. Mâu thuẫn giữa các nguồn
===========================

Ba nguồn bàn về op hỗ trợ nhưng ở ba góc khác nhau. OPL là tài liệu từng chip và từng ràng buộc. UG232 là hướng dẫn và FAQ. Tệp ``RKNNToolKit2_OP_Support-2.3.2.md`` (EX) là danh sách op theo framework đầu vào, trong đó có 185 dòng ONNX với 96 dòng ghi "Not Supported", 9 dòng có ghi chú khác và 80 dòng để trống (đếm của trang này, suy ra) [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:8-195]. Chính tệp này dặn xem OPL để biết thêm hạn chế [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:6-7]. Các dòng sau là mâu thuẫn bề mặt, chưa chứng minh một nguồn sai.

.. list-table::
   :header-rows: 1
   :widths: 14 30 30 26

   * - Chủ đề
     - Nguồn A
     - Nguồn B
     - Ghi chú
   * - Resize
     - OPL 3.2.54: mục NPU, hỗ trợ ``nearest`` và ``linear``, chỉ phóng to nguyên lần từ 2 đến 8 theo chiều rộng và cao, đa lõi ``不支持`` [T1 OPL tr.86] [T1 OPL tr.87]. Lịch sử V2.3.2 có dòng "更新 Resize 算子限制" [T1 OPL tr.9]
     - UG232 tr.176: NPU chưa hỗ trợ Resize cấp phần cứng, toolkit đổi Resize thành ConvTranspose [T1 UG232 tr.176]. Tệp op của toolkit ghi Resize "mode: nearest2d/bilinear" [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:147]
     - Hai nguồn T1 chưa thống nhất. UG232 ghi ngày 2025-04-03, OPL ghi 2025-03-28 [T1 UG232 tr.1] [T1 OPL tr.7]. Ngày không đủ để kết luận bản nào đúng với runtime
   * - Op đa lõi
     - UG232 tr.75 liệt kê op chia được tác vụ đa lõi, gồm Relu, Clip, Relu6, PRelu, LeakyRelu, ThresholdedRelu [T1 UG232 tr.75]. UG152 tr.27 có danh sách tương tự [T1 UG152 tr.27]
     - OPL 3.2.49 đến 3.2.52: Relu, Clip/ReLU6, PRelu, LeakyRelu đều ``暂不支持`` [T1 OPL tr.84] [T1 OPL tr.85]. OPL không có mục ThresholdedRelu, tệp op của toolkit ghi "Not Supported" cho nó [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:187]
     - Mâu thuẫn trực tiếp. Concat có trong UG232 nhưng mục 3.2.4 của OPL không có dòng đa lõi
   * - Op ghi "Not Supported" ở tệp toolkit nhưng có trong OPL
     - Tệp op ghi "Not Supported": Hardmax, Not, OneHot, ReduceL2, Round, TopK [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:80] [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:117] [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:189]
     - OPL: Hardmax là mục NPU 3.2.37 (PDF 72). Not, ReduceL2, Round, TopK, OneHot là mục CPU 4.68, 4.82, 4.95, 4.96, 4.99 (PDF 329, 331, 333) [T1 OPL tr.72] [T1 OPL tr.329] [T1 OPL tr.331] [T1 OPL tr.333]
     - Tệp toolkit là danh sách theo framework, OPL chương 4 là op CPU. Có thể hai bên đo "hỗ trợ" khác nhau, nguồn không nói rõ
   * - Op tính ở CPU
     - UG232 tr.168: NonMaxSuppression không hỗ trợ [T1 UG232 tr.168]
     - Tệp toolkit cũng ghi "Not Supported" [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:115]. OPL không có mục nào cho NMS
     - Nhất quán. Dùng để đối chiếu với các dòng trên

Hai chỗ đáng chú ý khi dùng bảng này để quyết định:

- Với Resize, UG232 tr.176 cho cách chạy CPU: thêm ``optimization_level=2`` vào ``rknn.config`` thì Resize chạy CPU, độ chính xác không giảm nhưng hiệu năng giảm.

   "the Resize Op will use the CPU, and the precision will not drop, but it will cause performance degradation" [T1 UG232 tr.176]

- Với danh sách op đa lõi, danh sách UG232 tr.75 chỉ có thể kiểm chứng bằng log ``WorkLoad(0/1/2)`` trên board. Trang này không dùng phép đo nên giữ nguyên là mâu thuẫn.

--------------

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 52 20

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Op có mục NPU trong OPL thì luôn chạy NPU
     - Kích thước vượt giới hạn cũng đưa op ra ngoài NPU. Log mẫu RK3588 có Reshape chạy CPU
     - [T1 UG232 tr.139] [T1 UG232 tr.56]
   * - ``暂不支持`` ở dòng đa lõi nghĩa là op không chạy NPU
     - Dòng này nằm trong ``其他支持`` và chỉ nói về chạy đa lõi
     - [T1 OPL tr.84] [T1 UG232 tr.75]
   * - Op ghi "supported" trong tệp op của toolkit chắc chắn chạy NPU
     - Tệp đó liệt kê theo framework và tự dặn xem OPL để biết hạn chế
     - [T1 EX 3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md:6-7]
   * - Op không hỗ trợ trên NPU mặc định đi sang GPU
     - Giá trị mặc định của ``fallback_prior_device`` là ``cpu``
     - [T1 API232 tr.17]
   * - OPL có mục Resize nghĩa là Resize chạy bằng phần cứng
     - UG232 tr.176 nói NPU chưa có Resize cấp phần cứng. Hai nguồn chưa thống nhất
     - [T1 OPL tr.86] [T1 UG232 tr.176]

--------------

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``OPL``
     - T1
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`
     - 36
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 20
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 6
   * - ``UG152``
     - T1
     - :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`
     - 1
   * - ``EX``
     - T1
     - Tài liệu và mã đi kèm SDK trong ``3rdparty/rknn-toolkit2/`` (``doc/RKNNToolKit2_OP_Support-2.3.2.md``, ``rknpu2/runtime/Linux/librknn_api/include/rknn_api.h``), không tải xuống
     - 10
