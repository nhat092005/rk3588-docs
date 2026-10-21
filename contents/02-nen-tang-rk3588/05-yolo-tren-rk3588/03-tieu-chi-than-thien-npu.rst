:tocdepth: 1

***********************
Tiêu chí thân thiện NPU
***********************

.. admonition:: Tóm tắt

   - OPL chương 3.2 có mục NPU cho Conv, Concat, Split, Resize, Softmax, Reshape, Transpose, exSDPAttention. ConvolutionSwish ghi đa lõi "暂不支持", còn MatMul, TopK, GatherElements, Mod, ReduceMax, Equal, Cast, Flatten chỉ có mục CPU.
   - Ràng buộc căn chỉnh width ở lớp đầu chỉ áp dụng cho zero-copy API theo OPL tr.335, không áp dụng cho API thường mà đường RKNN của repo dùng.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _95-tiêu-chí-thân-thiện-npu-cho-rk3588-t1:

Tiêu chí thân thiện NPU cho RK3588 (T1)
=======================================

Mọi dòng dưới đây đã mở lại PDF gốc. Trang OPL là chỉ số PDF (in = PDF - 6). Nguyên văn tiếng Trung trích từ OPL.

.. _951-op-có-mục-npu-trong-opl-chương-32:

Op có mục NPU trong OPL (chương 3.2)
------------------------------------

.. list-table::
   :header-rows: 1

   * - Op
     - Mục OPL
     - Điều kiện đáng chú ý
     - Đa lõi ("多核联合")
   * - Conv
     - 3.2.5, tr.58-59
     - ``kernel_h ∈ [1, 31]``.``stride_h ∈ [1, 7]``.``T1: int8(Tensor), float16(Tensor)``
     - 支持
   * - Conv depthwise
     - 3.2.6, tr.59-60
     - ``kernel_h ∈ [1, 8]``.``dilations_h ∈ [1, 32]``
     - 支持
   * - ConvolutionSwish
     - 3.2.17, tr.63
     - "Convolution 与 Swish 融合计算"
     - 暂不支持
   * - Sigmoid
     - 3.2.63, tr.95
     - int8, float16
     - 尚不支持
   * - Add
     - 3.2.1, tr.56
     - "支持任意维度广播操作" kèm "广播约束同Expand算子"
     - 支持
   * - Mul
     - 3.2.41, tr.77
     - như Add (broadcast ràng buộc như Expand)
     - 支持
   * - Sub
     - 3.2.60, tr.91-92
     - broadcast chỉ ``[b, c, 1, 1]`` hoặc scalar
     - 不支持
   * - Div
     - 3.2.33, tr.67
     - ``T1: float16(Tensor)``
     - 不支持
   * - MaxPool
     - 3.2.44, tr.79-80
     - ``kernel_h ∈ (0, 7]``, ``ceil_mode`` không hỗ trợ, ``auto_pad`` chỉ NOTSET
     - không có dòng này
   * - Resize
     - 3.2.54, tr.86-87
     - nearest và linear.``coordinate_transformation_mode`` chỉ ``half_pixel``, ``pytorch_half_pixel``, ``align_corners``.``nearest_mode`` "目前不支持设置", nguyên lần 2-8
     - 不支持
   * - Concat
     - 3.2.4, tr.58
     - ``axis ∈ {0,1,2,3}``
     - không có dòng này
   * - Split
     - 3.2.59, tr.91
     - ``axis ∈ {0,1,2,3}``
     - không có dòng này
   * - Slice
     - 3.2.55, tr.88
     - chỉ chạy NPU khi ``steps == [1,1,1,1]`` (ngoại lệ có ``subc``, OPL không định nghĩa ``subc``)
     - không có dòng này
   * - Softmax
     - 3.2.56, tr.88-89
     - ``axis`` là 1 hoặc 3, chịu giới hạn của Transpose. OPL không nêu giới hạn kích thước riêng
     - 尚不支持
   * - Reshape
     - 3.2.53, tr.86
     - int8, float16
     - 尚不支持
   * - Transpose
     - 3.2.62, tr.93-95
     - điều kiện theo từng ``perm`` (ví dụ ``perm=[0,1,3,2]`` int8: ``h1%16=0``, ``h1*w1<16*p``, ``h1*w1<2*q``, với ``p=8192``, ``q=2048``)
     - 暂不支持
   * - Gather
     - 3.2.36, tr.71
     - indices rank 1, ``axis ∈ {0,1,2,3}``
     - 尚不支持
   * - Where
     - 3.2.74, tr.100-101
     - mask ``bool``, data int8 hoặc float16
     - không có dòng này
   * - Expand
     - 3.2.34, tr.68
     - 5 dạng broadcast cụ thể (ví dụ ``[b, c, 1, w]`` sang ``[b, c, h, w]``)
     - 不支持
   * - exMatMul
     - 3.2.76, tr.102
     - ``A [b, k, 1, n]``, ``k ∈ (0, 8192]``, int8 hoặc float16
     - 不支持
   * - exSDPAttention
     - 3.2.78, tr.104-105
     - ``query/key/value``: ``[batch, channel, height, width]``, ``channel ∈ (0, 8192]``
     - 不支持

Khác biệt với UG232 về đa lõi (UG232 tr.75): danh sách đa lõi gồm "Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu". OPL không ghi dòng đa lõi cho ``Concat`` và ghi ``Mul`` là 支持 trong khi UG232 không liệt kê ``Mul`` (mâu thuẫn đã ghi ở ``06_``, :ref:`Điều chưa biết về compiler nội bộ của Rockchip <66-điều-chưa-biết-về-compiler-nội-bộ-của-rockchip>`).

.. _952-tiêu-chí-hiệu-năng-ug232:

Tiêu chí hiệu năng (UG232)
--------------------------

.. list-table::
   :header-rows: 1

   * - Tiêu chí
     - Nguồn
     - Nội dung
   * - Căn chỉnh kênh
     - UG232 tr.145 Bảng 8-2 (RK3588)
     - Conv int8: kênh vào 32, kênh ra 32. Depthwise Conv: kênh int8 là 64, float16 là 32
   * - Kích thước kernel
     - UG232 tr.146-147
     - "The larger the ratio of Ksize / Kstride, the higher the utilization rate"."the utilization rate is relatively high when KH\* KW \* KC \* type_bytes < 6K Bytes"
   * - Op kém hiệu quả
     - UG232 tr.146 Bảng 8-5
     - Ba nhóm nên giảm: "Data transfer" (có ``Concat``, ``Split``, ``Transpose``, ``Reshape``), "Size transformation" (có ``Pooling``, ``Resize``), "Non-Relu activation function" (có ``Sigmoid``)
   * - Ghép op
     - UG232 tr.141-142
     - "NPU supports fusion of some operators", quy tắc đã hỗ trợ gồm ``Conv+Sigmoid(Tanh/Elu/Silu...)``."Conv+Activation+Mul" và "Conv+Mul" nằm ở cột kế hoạch tương lai
   * - Ràng buộc đầu vào lớp đầu (RK3588, đọc từ ảnh)
     - OPL §5.1.2, PDF tr.336
     - Lớp đầu int8, đầu vào uint8 hoặc int8 do NPU thực hiện: căn chỉnh ``width`` 16 phần tử khi kênh vào là 1, 3 hoặc 4 (1 với kênh khác), với kênh 1, 3, 4: "width \* dilation_kernel_h <= 2048 \* N" và "width <= 8192", N nguyên từ 1 đến 7 tính theo loại conv bằng công thức trong bảng (có ``CEIL((dilation_kernel_h * dilation_kernel_w) / 128)`` cho Convolution và ``/ 2048`` cho Depthwise). Với đầu vào 640x640x3 và conv đầu 3x3 stride 2: 640 chia hết cho 16, 640 \* 3 = 1920 <= 2048 (thỏa với mọi N >= 1, tính của file này, số 3 ở đây là ``dilation_kernel_h`` của conv đầu 3x3, trùng với số kênh vào). Lưu ý: với conv 3x3 công thức in trong OPL cho Convolution là N = 12 - MAX(CEIL(9/128), 3) = 9, nằm ngoài khoảng 1 đến 7 mà chính bảng nêu. OPL tự mâu thuẫn hoặc in sai, file này không phân xử. Điều kiện bị thiếu trước đây: ghi chú 1 của OPL §5.1 (PDF tr.335) nói ràng buộc căn chỉnh ``width`` "仅针对零拷贝 API，普通 API 无此对齐约束", tức chỉ áp dụng cho API zero-copy. API thường không có ràng buộc căn chỉnh này. Đường RKNN của repo dùng API thường qua toolkit hoặc Lite2 (wheel 2.3.2 không có zero-copy cho Python, :ref:`Zero-copy, cờ bộ nhớ và căn lề <74-zero-copy-cờ-bộ-nhớ-và-căn-lề>`), nên hàng này là tiêu chí tham khảo cho triển khai C API. Chữ trong bảng đọc từ ảnh, cần kiểm lại nếu dùng kích thước khác
   * - Ghép attention
     - UG232 tr.148, API232 tr.10
     - UG232 chỉ liệt kê "Split + Sigmoid + Mul -> GLU" và LayerNorm, không có quy tắc ghép ``MatMul``-``Softmax``-``MatMul``. API232 tr.10 có tham số ``enable_flash_attention`` trỏ tới ``exSDPAttention``

.. _953-op-không-có-mục-npu-trong-opl:

Op không có mục NPU trong OPL
-----------------------------

.. list-table::
   :header-rows: 1

   * - Op
     - Kết quả sau khi tìm toàn bộ OPL (343 trang)
   * - ``MatMul``
     - Không có mục trong 3.2, có mục CPU 4.33 (tr.324) "无限制", chỉ có ``exMatMul`` (3.2.76) cho NPU. Quy tắc ánh xạ ONNX ``MatMul`` sang ``exMatMul``: chưa tìm thấy trong OPL, UG232, UG152, API232, QS232
   * - ``TopK``
     - Chỉ có mục CPU 4.96 (tr.333). OPSUP dòng 189: "Not Supported"
   * - ``GatherElements``, ``ReduceMax``, ``Mod``, ``Equal``, ``Cast``, ``Flatten``
     - Chỉ có mục CPU (chương 4): 4.75 (tr.330), 4.44 (tr.325), 4.72 (tr.329), 4.17 (tr.321), 4.7 (tr.320), 4.19 (tr.322). ``Cast``: đích hỗ trợ ``float32/int8/int32/float16``, không có ``int64``
   * - ``ConstantOfShape``, ``Unsqueeze``, ``Shape``
     - Không có mục ở bất kỳ chương nào của OPL. UG232 tr.167 chỉ nhắc ``Shape``, ``Gather``, ``Unsqueeze``, ``Concat``, ``Cast`` trong log ``_fold_constant remove nodes`` của một model mẫu

Chương 4.1 của OPL chỉ hạn chế RK2118 và họ RV1103/RV1106, việc suy ra "RK3588 dùng được toàn bộ danh sách CPU" là suy luận của file này, OPL không viết câu đó.

.. _97-đối-chiếu-khối-kiến-trúc-với-tiêu-chí:

Đối chiếu khối kiến trúc với tiêu chí
=====================================

Trạng thái: **Đo** = có phép đo T3 trên board (YOLOv8n ở lượt trước, YOLO26n ở :ref:`Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên) <955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên>`), **Mục NPU** = OPL có mục NPU nhưng chưa đo, **CPU** = OPL chỉ có mục CPU, **unknown** = không có nguồn đủ để kết luận.

.. list-table::
   :header-rows: 1

   * - Khối hoặc đặc điểm
     - Có ở
     - Bằng chứng
     - Trạng thái
   * - Conv 3x3 và 1x1, stride 1 và 2
     - cả hai
     - OPL 3.2.5 (đa lõi 支持). T3 board: ``Conv`` chạy NPU
     - Đo (YOLOv8n)
   * - Conv + SiLU
     - cả hai
     - OPL 3.2.17 (đa lõi 暂不支持). T3 board: YOLOv8n 57 và YOLO26n 87 ``ConvExSwish`` NPU, chỉ lõi 0 ở 3 lõi
     - Đo (cả hai)
   * - ``MaxPool`` 5x5 stride 1 (SPPF)
     - cả hai
     - OPL 3.2.44 (kernel 5, pad 2 nằm trong giới hạn). T3 board: ``MaxPool`` NPU
     - Đo (YOLOv8n)
   * - ``Resize`` nearest 2x (neck)
     - cả hai
     - OPL 3.2.54 (``asymmetric`` và ``floor`` trong ONNX không nằm trong danh sách OPL). UG232 tr.176 nói NPU không có Resize phần cứng. T3 board: ``Resize`` NPU ở 3 mức
     - Đo (YOLOv8n), vẫn mâu thuẫn T1
   * - ``Concat``, ``Split``, ``Add``
     - cả hai
     - OPL 3.2.1, 3.2.4, 3.2.59. T3 board: chạy NPU
     - Đo (YOLOv8n)
   * - ``Slice``
     - cả hai
     - OPL 3.2.55 (NPU khi ``steps == [1,1,1,1]``). ONNX có 2 ``Slice`` và 8 ``Split``, trên board không có lớp ``Slice`` nào mà có 9 lớp ``Split``
     - Mục NPU, không đo trực tiếp (biên dịch đổi thành ``Split``)
   * - Cộng residual trong SPPF
     - YOLO26n
     - ``block.py:233, 240``, op là ``Add``. T3 board: 18 ``Add`` NPU ở YOLO26n
     - Đo (op ``Add``, không tách riêng cái của SPPF)
   * - ``C3k2``, ``C3k`` (so với ``C2f``)
     - YOLO26n
     - Chỉ gồm Conv, Add, Concat, chia kênh (:ref:`C2f (YOLOv8n) và C3k2 (YOLO26n) <921-c2f-yolov8n-và-c3k2-yolo26n>`). T3 board: toàn bộ chạy NPU
     - Đo (chạy NPU), hiệu năng so với ``C2f`` chưa tách
   * - Conv depthwise 3x3
     - YOLO26n: 8 (6 ở nhánh lớp, 2 ở ``pe`` của attention). YOLOv8n: 0
     - OPL 3.2.6 (hỗ trợ, đa lõi 支持). UG232 tr.145 (căn chỉnh kênh int8 là 64). T3 board: 6 ghép thành ``ConvExSwish``, 2 là ``Conv``, ``MacUsage`` 0.30% đến 1.24%, tổng 1296 us
     - Đo (YOLO26n): chạy NPU, hiệu suất MAC rất thấp, thời gian tuyệt đối nhỏ
   * - DFL (Reshape, Transpose, Softmax, Conv1x1)
     - YOLOv8n
     - T3 board: ``exSoftmax13`` NPU, còn 1 ``Transpose`` CPU (tên lớp gắn với DFL). OPL Transpose có điều kiện theo ``perm``
     - Đo gián tiếp (YOLOv8n, không bóc riêng từng op của DFL)
   * - Attention (qkv, Split, Reshape, ``MatMul``, ``Softmax``, ``Transpose``, proj, ``pe``)
     - YOLO26n x2
     - OPL: ``MatMul`` chỉ có mục CPU, NPU có ``exMatMul`` (3.2.76) và ``exSDPAttention`` (3.2.78, đa lõi 不支持). UG232 không có quy tắc ghép attention. T3 board: mỗi khối thành 1 ``exSDPAttention`` INT8 NPU, lõi 0, khoảng 1.23 ms
     - Đo (YOLO26n): chạy NPU như một op gộp, quy tắc nhận chuỗi không có trong T1
   * - ``Softmax`` trong attention (INT8)
     - YOLO26n
     - T2 Y26B tr.8 (giả thuyết khó lượng tử hóa, trích khảo sát chung).``Softmax`` nằm trong ``exSDPAttention``
     - **unknown** (cần model đã huấn luyện, đo mAP FP32 so INT8)
   * - Đầu bỏ DFL, nhánh hộp 4 kênh
     - YOLO26n
     - T3 board: không có ``exSoftmax13`` và không có ``Transpose`` CPU. YOLOv8n có hai lớp đó (khoảng 15.5% tổng thời gian debug ở AUTO). UG232 tr.146 khuyến nghị giảm ``Transpose`` và ``Reshape``
     - Đo (loại bỏ được hai lớp đó), lợi ích độ trễ tổng chưa tách
   * - Đầu ``end2end``: ``TopK``, ``GatherElements``, ``Mod``, ``ReduceMax``, ``Cast`` INT64, ``Where``
     - YOLO26n khi ``end2end``
     - ``TopK``, ``GatherElements``, ``Mod``, ``ReduceMax``, ``Cast``: OPL chỉ có mục CPU. OPSUP ``TopK`` "Not Supported". ``Where`` có mục NPU (3.2.74, data int8 hoặc float16) và mục CPU 4.69, nhưng trong đồ thị ``end2end`` thiết lập (A) nó chạy trên tensor INT64 kiểu shape nên điều kiện NPU không áp dụng (ở thiết lập (B), ``onnxslim`` đã gộp ``Where``). ``end2end`` không bật ở đường xuất mặc định và bị tắt lại với ``rknn`` nếu truyền ``nms=False`` (:ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`)
     - Không nằm trong đường triển khai
   * - NMS
     - cả hai (đường RKNN)
     - Ngoài đồ thị, chạy phía host
     - Không đánh giá ở khối này

Phép tính tĩnh về điều kiện ``Transpose`` (không phải phát biểu của vendor): lấy shape trong ONNX đặt vào điều kiện của OPL thì ``Transpose`` của DFL (ví dụ ``perm=[0,3,1,2]`` trên ``[1,4,16,8400]`` có ``h1*w1 = 134400``, vượt ``p = 8192``) và ``Transpose`` của attention (``perm=[0,1,3,2]`` trên ``[1,2,400,400]`` có ``h1*w1 = 160000``, vượt ``16*p = 131072``) đều **vi phạm** điều kiện. Tuy nhiên YOLOv8n đo thật (đồ thị thiết lập (A), 2 ``Transpose``) chạy được với 1 ``Transpose`` CPU trên board, nên phép tính tĩnh **không dự đoán được** hành vi của trình biên dịch (có thể gộp hoặc tách tensor). Không dùng nó để kết luận về YOLO26n. Quan sát thực tế ở YOLO26n: ONNX thiết lập (B) có 4 ``Transpose`` và 4 ``MatMul``, còn đồ thị RKNN không có lớp ``Transpose`` hay ``MatMul`` nào (attention thành ``exSDPAttention``).
