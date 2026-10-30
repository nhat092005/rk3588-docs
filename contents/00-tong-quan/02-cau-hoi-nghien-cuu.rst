:tocdepth: 1

**********************
Research problem và RQ
**********************

.. admonition:: Trang này trả lời

   - Hiệu năng suy luận thời gian thực trên Edge NPU phụ thuộc vào những khía cạnh kỹ thuật nào?
   - Khả năng hỗ trợ toán tử (operator support) và cơ chế phân phối đa nhân của NPU RK3588 cho YOLOv8n ra sao?
   - Câu hỏi nghiên cứu (Research Question - RQ) trọng tâm của đề tài là gì?

.. admonition:: Tóm tắt

   - Research problem: hiệu quả real-time trên Edge NPU phụ thuộc operator support, tensor layout, datatype, memory access, memory copy, compiler optimization, NPU architecture và pre/post-processing overhead.
   - Trên RK3588, `Convolution` và các biến thể gộp `ReLU`, `Clip`, `PReLU/LeakyReLU`, `Add` hỗ trợ đa nhân, trong khi `Resize` không hỗ trợ và `ConvolutionSwish` (Conv + SiLU) tạm chưa hỗ trợ đa nhân (vẫn chạy trên một nhân). Chi tiết từng toán tử được phân tích tại trang :doc:`Operator support </contents/03-phuong-phap-de-xuat/02-tang-npu/01-operator-support>`.
   - Trình biên dịch RKNN tự động tối ưu đồ thị và hợp nhất toán tử (như gộp lớp tích chập với hàm kích hoạt đi kèm) trước khi sinh mã thực thi cho NPU.
   - Trên RK3588 chỉ dùng được `FP16` và `w8a8` (INT8/INT8, mặc định), còn `w4a8` chưa được hỗ trợ.
   - Độ trễ của từng tầng trên NPU không chỉ phụ thuộc số chu kỳ tính toán (`NPU Cycles`) mà còn phụ thuộc số chu kỳ chờ đọc và ghi bộ nhớ (`DDR Cycles`).
   - Research Question: giữ PPE detection accuracy tốt nhưng đồng thời cải thiện inference efficiency trên RK3588S NPU.

.. contents:: Trong trang này
   :local:
   :depth: 2

.. _21-research-problem-đề-xuất:

1. Vấn đề nghiên cứu đề xuất (Research Problem)
====================================================================================================

1.1. Các yếu tố quyết định hiệu năng Edge NPU
----------------------------------------------------------------------------------------------------

Các object detector có thể đạt accuracy tốt, nhưng khi triển khai real-time trên Edge NPU, hiệu quả thực tế còn phụ thuộc vào:

.. code:: text

   operator support → Mức độ NPU hỗ trợ các phép toán của model như Conv, Add, Resize...

   multi-core → Việc chạy model trên 1 hay nhiều nhân NPU (core_mask). Op không hỗ trợ đa nhân sẽ quay về Core0.

   tensor layout → Cách tensor được sắp xếp trong memory, ví dụ NCHW/NHWC.

   datatype → Kiểu dữ liệu của model. Trên RK3588 lựa chọn thực tế là FP16 và INT8 (w8a8).

   memory access → Cách model đọc/ghi dữ liệu từ memory trong lúc inference.

   memory copy → Việc copy dữ liệu giữa các buffer, copy nhiều sẽ làm tăng latency.

   compiler optimization → Các bước compiler tối ưu graph, operator, layout và memory trước khi chạy trên NPU.

   NPU architecture → Kiến trúc phần cứng của NPU quyết định loại phép toán nào chạy hiệu quả.

   pre/post-processing overhead → Thời gian ngoài inference, như resize, color conversion, NMS, decode output...

1.2. Đối chiếu với tài liệu kỹ thuật nền tảng RK3588
----------------------------------------------------------------------------------------------------

Ba yếu tố dưới đây được quy định trực tiếp trong bộ tài liệu chính thức của Rockchip cho RK3588:

.. list-table::
   :header-rows: 1

   * - Yếu tố
     - Đặc tả trên RK3588
     - Nguồn
   * - ``operator support``
     - ``Convolution`` hỗ trợ đa nhân ("多核联合: 支持"), nhưng **``Resize``** (upsample trong neck YOLO) **không** ("不支持"), và **``ConvolutionSwish``** (Conv + SiLU gộp) **tạm chưa hỗ trợ đa nhân** ("暂不支持", mục này ghi ``说明及规格限制同Convolution``, tức vẫn chạy trên một nhân). Các biến thể Conv kèm ReLU, Clip, PReLU/LeakyReLU hoặc Add đều ghi "支持", trong khi kiến trúc YOLOv8 mặc định dùng hàm kích hoạt SiLU sau các lớp tích chập
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`, mục 3.2 RK3588: 3.2.5 Convolution (trang PDF 59), 3.2.7 đến 3.2.10 (trang PDF 60 đến 61), 3.2.17 ConvolutionSwish (trang PDF 63), 3.2.54 Resize (trang PDF 87)
   * - ``compiler optimization``
     - Trình biên dịch RKNN tự động thực hiện tối ưu hóa đồ thị, loại bỏ các toán tử dư thừa và hợp nhất toán tử (operator fusion, như gộp lớp Conv với hàm kích hoạt đi kèm) để khớp với phần cứng NPU
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, mục 8.4 Graph optimization, tr.140 đến 141
   * - ``datatype``
     - Trên RK3588 chỉ dùng được ``FP16`` và ``w8a8`` (INT8/INT8, mặc định). Các chế độ lượng tử hóa khác đều giới hạn theo dòng chip: ``w4a16`` chỉ hỗ trợ RK3576/RV1126B, ``w8a16`` chỉ hỗ trợ RK3562, ``w16a16i`` chỉ hỗ trợ RV1103/RV1106 và ``w4a8`` chưa được hỗ trợ
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`, hàm ``config``, tham số ``quantized_dtype``, tr.7

Tài liệu hướng dẫn API của Rockchip cũng nêu rõ cơ chế phân tải khi chạy đa nhân (so sánh chi tiết giữa các tài liệu hãng và kiểm chứng thực nghiệm được trình bày tại trang :doc:`Operator support </contents/03-phuong-phap-de-xuat/02-tang-npu/01-operator-support>`): :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`, trang PDF 27, nguyên văn:

   "For multi-cores mode (when enabling RKNN_NPU_CORE_0_1 and RKNN_NPU_CORE_0_1_2), the following ops have better acceleration: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. Other type of op will fallback to Core0 to continue running."

Do đó:

.. code:: text

   low FLOPs ≠ low latency
   small model ≠ fast model on NPU

1.3. Nghịch lý chu kỳ bộ nhớ: DDR Cycles so với NPU Cycles
----------------------------------------------------------------------------------------------------

Theo tài liệu ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (mục 8.2.4 "Analysis of NPU operator performance bottlenecks", tr.140), khi phân tích một toán tử tích chập tốn nhiều thời gian trên NPU, cần đối chiếu ba cột ``DDR Cycles / NPU Cycles / Total Cycles``:

   "When analyzing the high time-consuming problem of the NPU operator, you can judge whether the theoretical bottleneck of the operator's time-consuming is a bandwidth bottleneck or a computing power bottleneck based on the three columns of DDR Cycles/NPU Cycles/Total Cycles. DDR Cycles refers to the number of cycles required by the operator to read and write. It has been converted into the number of Cycles required at the NPU frequency, so it can be directly compared with the NPU Cycle."

``NPU Cycles`` phản ánh số chu kỳ tính toán trên mảng MAC, còn ``DDR Cycles`` phản ánh số chu kỳ chờ đọc và ghi dữ liệu từ bộ nhớ RAM (đã quy đổi về cùng xung nhịp NPU). Ở các tầng thông thường, ``NPU Cycles`` lớn hơn ``DDR Cycles`` nên tính toán là nút thắt chính (compute-bound). Ngược lại, ở những tầng có ``DDR Cycles`` vượt ``NPU Cycles``, thời gian di chuyển dữ liệu lớn hơn thời gian tính toán, khiến băng thông bộ nhớ trở thành nút thắt thực sự (memory-bound). Phân tích thực nghiệm hiện tượng này trên từng khối của mô hình dự án được trình bày tại :doc:`Phân tích sâu latency từng khối </contents/03-phuong-phap-de-xuat/03-do-latency-npu/03-phan-tich-sau-latency-tung-khoi>`.

--------------

.. _22-research-question:

2. Câu hỏi nghiên cứu trọng tâm (Research Question)
====================================================================================================

   **Làm thế nào giữ PPE detection accuracy ở mức tốt nhưng đồng thời cải thiện inference efficiency trên RK3588S NPU?**
