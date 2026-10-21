:tocdepth: 1

***********************
Op của YOLOv8 trên RKNN
***********************

.. admonition:: Trang này trả lời

   - những op nào thường gặp có trong danh sách NPU của RK3588, kèm ràng buộc gì?

.. admonition:: Tóm tắt

   - SiLU có hai dạng trong OPL là ConvolutionSwish (OPL tr.63) và exSwish (OPL tr.98), model YOLOv8 từ Ultralytics ghép thành dạng nào là unknown.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _62-các-op-của-detector-kiểu-yolov8-trên-rk3588:

Các op của detector kiểu YOLOv8 trên RK3588
===========================================

**Câu hỏi:** những op nào thường gặp có trong danh sách NPU của RK3588, kèm ràng buộc gì?

Danh sách op dưới đây là danh sách op thường gặp trong detector, không có nguồn. Mỗi dòng chỉ có giá trị khi có quote của Operator List.

.. list-table::
   :header-rows: 1

   * - Op
     - Mục OPL
     - PDF
     - Trên NPU RK3588
     - Đa lõi ("多核联合")
   * - Conv
     - 3.2.5
     - 58 đến 59
     - có
     - 支持
   * - ConvolutionSwish (SiLU hợp nhất)
     - 3.2.17
     - 63
     - có
     - 暂不支持. T3 (log T3 board 2026-10-10, lượt 2 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``, ``raw/summary2.json``, ``raw/*_CORE_0_1_2_layers.txt``)): lớp ``ConvExSwish`` chạy lõi 0 (100%/0%/0%) ở CORE_0_1_2, phù hợp với "暂不支持" ở cột này, tên trong bảng lớp là ``ConvExSwish``, tên trong OPL là ConvolutionSwish, không khẳng định cùng một op (một model: YOLOv8n trọng số ngẫu nhiên ``nc=5``, INT8, 640x640, toolkit 2.3.2, RK3588S, NPU 1 GHz, ``eval_perf`` ``fix_freq=True``, xem ``08_``)
   * - exSwish (SiLU đứng riêng)
     - 3.2.69
     - 98
     - có
     - 尚不支持
   * - Sigmoid
     - 3.2.63
     - 95
     - có
     - 尚不支持
   * - Resize
     - 3.2.54
     - 86 đến 87
     - một phần (xem dưới)
     - 不支持
   * - Concat
     - 3.2.4
     - 58
     - có
     - không có dòng
   * - Split
     - 3.2.59
     - 91
     - có
     - không có dòng
   * - MaxPool
     - 3.2.44
     - 79 đến 80
     - có
     - không có dòng
   * - Add, Mul
     - 3.2.1, 3.2.41
     - 56, 77
     - có
     - 支持
   * - Reshape
     - 3.2.53
     - 86
     - có
     - 尚不支持
   * - Transpose
     - 3.2.62
     - 93 đến 95
     - có, có điều kiện
     - 暂不支持
   * - Softmax
     - 3.2.56
     - 88 đến 89
     - có, có điều kiện
     - 尚不支持
   * - Slice
     - 3.2.55
     - 88
     - có, có điều kiện
     - không có dòng
   * - Upsample
     - không có trong 3.2
     - CPU 4.67, PDF 329
     - không thấy ở mục NPU
     - không có

Upsample không có trong danh sách NPU của RK3588. Chương CPU OPs có một mục ``Upsample`` với "支持插值方式 bilinear; nearest2d" (OPL tr.329).

**Nguồn nói gì** (tiếng Trung, kèm tạm dịch)

   "Convolution 与 Swish 融合计算, Output = Swish(Conv(Input))" [T1 OPL tr.63] (Conv hợp nhất với Swish. Mục này ghi "说明及规格限制同Convolution", tức ràng buộc như Convolution.)

..

   "按元素应用 Sigmoid 线性单元函数, Swish 函数也称为 SiLU 函数, y = x \* sigmoid(x)" [T1 OPL tr.98] (Áp dụng theo phần tử hàm Sigmoid Linear Unit. Swish còn gọi là SiLU. Đây là mục exSwish, op đứng riêng.)

   "给定输入张量，函数 y = 1 / (1 + exp(‑x)) 按元素应用于输入张量，得到输出张量" [T1 OPL tr.95] (Cho tensor đầu vào, hàm ``y = 1 / (1 + exp(-x))`` được áp dụng theo phần tử và cho ra tensor đầu ra. Mục 3.2.63 Sigmoid.)

..

   "目前仅支持宽高方向的整数倍缩放, 且缩放倍数为 2‑8 的整数倍" [T1 OPL tr.87] (Hiện chỉ hỗ trợ phóng nguyên lần theo chiều cao và rộng, hệ số là bội nguyên trong khoảng 2 đến 8.)

   "目前仅支持 nearest 和 linear 两种可配置" [T1 OPL tr.87] (Hiện chỉ hai chế độ ``nearest`` và ``linear`` cấu hình được.)

..

   "目前仅支持 half_pixel，pytorch_half_pixel，align_corners 三种" [T1 OPL tr.87] (Chế độ ``coordinate_transformation_mode`` hiện chỉ hỗ trợ ba giá trị ``half_pixel``, ``pytorch_half_pixel``, ``align_corners``.)

   "pad 的方式: 仅支持 NOTSET" [T1 OPL tr.79] (MaxPool: chỉ hỗ trợ ``auto_pad = NOTSET``. Cùng mục: kernel và stride tối đa trong (0, 7] và (0, 8], ``ceil_mode`` không hỗ trợ.)

..

   "将向量沿着 axis 方向分成 num_outputs 个向量" [T1 OPL tr.91] (Split: tách vector theo ``axis`` thành ``num_outputs`` vector.``axis ∈ {0, 1, 2, 3}``.)

   "否则只有 steps == [1,1,1,1] 时，才可通过 NPU 运行 Slice OP" [T1 OPL tr.88] (Slice: nếu không thỏa điều kiện chứa ``subc`` thì chỉ ``steps == [1,1,1,1]`` mới chạy trên NPU. OPL không định nghĩa ``subc``.)

..

   "做 softmax 的轴: 1,3，即 channel 和 width 方向" [T1 OPL tr.89] (Softmax: chỉ hỗ trợ trục 1 hoặc 3, tức channel hoặc width. Ghi thêm "受限于 tranpose 的规格限制", bị ràng buộc theo giới hạn của Transpose.)

   "在不改变输入数据和元素数量的情况下，返回一个具有指定形状的张量。" [T1 OPL tr.86] (Reshape: trả về tensor có hình dạng chỉ định mà không đổi dữ liệu và số phần tử.)

..

   "不同 perm 参数限制如下：(其中 p=8192, q=2048 )" [T1 OPL tr.93] (Transpose: mỗi hoán vị ``perm`` có giới hạn riêng, với p = 8192 và q = 2048. Ví dụ ``perm=[0,3,1,2]``: ``h1*w1<p, w1<8192, h1*c1<p``.)

Ràng buộc của Convolution (mục 3.2.5, PDF 58 đến 59): ``kernel_h``, ``kernel_w`` ∈ [1, 31], ``stride`` ∈ [1, 7], ``pads`` ∈ [0, 15], ``dilations`` ∈ [1, 31], dtype ``int8`` và ``float16``, weight hỗ trợ ``per‑layer`` và ``per‑channel``, input và output chỉ ``per‑layer``. Mục 3.2.6 Depthwise Convolution ghi ``dilations`` ∈ [1, 32], khác 31 của Convolution cùng bản tài liệu.

**Resize có chạy trên NPU không (mâu thuẫn T1)**

   "Possible reasons are:" [T1 UG232 tr.176]

..

   "The decrease in accuracy is because the NPU does not currently support hardware-level Resize (will be supported in the future), and the RKNN-Toolki2 will convert Reszie to ConvTranspose, which will cause a little loss of accuracy." [T1 UG232 tr.176]

   "The parameter optimization_level=2 can be added to rknn.config . At this time, the Resize Op will use the CPU, and the precision will not drop, but it will cause performance degradation." [T1 UG232 tr.176]

Operator List (OPL tr.86, 87) có mục Resize cho RK3588 với ``int8`` và ``float16``. File ``tests/fixtures/eval_perf_2.3.2_layers.txt`` của repo (commit ``a79457a``) ghi hai lớp ``Resize INT8 NPU``. Nguồn gốc file này chưa được kiểm, chỉ dùng làm gợi ý, không phải bằng chứng T1.

**Ý chính**

- Có op SiLU cho RK3588 ở hai dạng: ``ConvolutionSwish`` (hợp nhất với Conv) và ``exSwish`` (đứng riêng). Operator List liệt kê hai mục riêng (OPL tr.63, 98).
- Tổng hợp của file này: Operator List không cho thấy một model YOLOv8 xuất từ Ultralytics sẽ ghép thành ``ConvolutionSwish`` hay giữ ``Sigmoid`` và ``Mul`` rời. Điều đó ``unknown``.
- Resize hỗ trợ phóng nguyên lần 2 đến 8 theo chiều cao và rộng, riêng đầu vào ``(1, c, 1, 1)`` thì "支持放大到 (1, c, h, w)" (hỗ trợ phóng lên ``(1, c, h, w)``) (OPL tr.87). Với model dùng nhiều Resize, UG232 tr.176 nói độ chính xác có thể giảm vì toolkit đổi Resize thành ConvTranspose.
- Softmax chỉ theo channel hoặc width, và bị ràng buộc theo Transpose (OPL tr.89).

**Giới hạn**

- Hai tài liệu T1 chưa thống nhất về Resize: Operator List liệt kê nó với ``int8``, ``float16``, còn User Guide tr.176 nói NPU chưa hỗ trợ Resize cấp phần cứng. Có thể hòa giải một phần: OPL tr.9 (V2.3.2) ghi "更新 Resize 算子限制". ``CHANGELOG.md`` dòng 100 và 140 liệt kê Resize trong các NPU operator được thêm hỗ trợ ở các phiên bản cũ. User Guide nói toolkit đổi Resize thành ConvTranspose (có mục NPU 3.2.20). Operator List chương CPU cũng có Resize (mục 4.50, PDF 326, "支持插值方式 bilinear; nearest2d"). Chưa đủ để kết luận. Cần đo T3 (``eval_perf`` với ``optimization_level`` 3 và 2, đọc cột op và target) để chốt. Đóng một phần (T3 board, 2026-10-10): xem :ref:`Điều chưa biết về compiler nội bộ của Rockchip <66-điều-chưa-biết-về-compiler-nội-bộ-của-rockchip>`, hàng Resize.
- Danh sách op của detector là suy nghĩ chung, không có nguồn. Tên op trong log (ví dụ ``ConvExSwish``) không xuất hiện trong T1 nào và khác tên trong Operator List.


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
     - 12
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 3
