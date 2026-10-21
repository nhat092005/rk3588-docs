:tocdepth: 1

**********************
Research problem và RQ
**********************

.. admonition:: Tóm tắt

   - Research problem: hiệu quả real-time trên Edge NPU phụ thuộc operator support, tensor layout, datatype, memory access, memory copy, compiler optimization, NPU architecture và pre/post-processing overhead.
   - Trên RK3588, `Convolution` hỗ trợ đa nhân nhưng `Resize` không, và `ConvolutionSwish` tạm chưa; chỉ Conv + ReLU/Clip/LeakyReLU được hỗ trợ.
   - Build log của model 7 class cũ có 228 op `ConvExSwish`, và cờ `conv_eltwise_activation_fuse = 1` mặc định bật.
   - Trên RK3588 chỉ dùng được `w8a8` (INT8/INT8, mặc định); `w4a8` chưa hỗ trợ.
   - Log gọi op là `ConvExSwish`, tài liệu gọi `ConvolutionSwish`; chưa tài liệu nào xác nhận cùng một op, và cần chạy `eval_perf` ở `CORE_0_1_2` `[chưa kiểm chứng]`.
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

   tensor layout → Cách tensor được sắp xếp trong memory, ví dụ NCHW/NHWC.

   datatype → Kiểu dữ liệu của model, ví dụ FP32, FP16, INT8.

   memory access → Cách model đọc/ghi dữ liệu từ memory trong lúc inference.

   memory copy → Việc copy dữ liệu giữa các buffer, copy nhiều sẽ làm tăng latency.

   compiler optimization → Các bước compiler tối ưu graph, operator, layout và memory trước khi chạy trên NPU.

   NPU architecture → Kiến trúc phần cứng của NPU quyết định loại phép toán nào chạy hiệu quả.

   pre/post-processing overhead → Thời gian ngoài inference, như resize, color conversion, NMS, decode output...

1.2. Bằng chứng thực nghiệm trên nền tảng RK3588
----------------------------------------------------------------------------------------------------

3 yếu tố dưới đây đã có bằng chứng thật trên chính model/board của project (không phải trích paper ngoài):

.. list-table::
   :header-rows: 1

   * - Yếu tố
     - Phát hiện thật
     - Nguồn
   * - ``operator support``
     - ``Convolution`` hỗ trợ đa nhân ("多核联合: 支持"), nhưng **``Resize``** (upsample trong neck YOLO) **không** ("不支持"), và **``ConvolutionSwish``** (Conv + SiLU gộp) **tạm chưa** ("暂不支持"). Chỉ các biến thể Conv + ReLU/Clip/LeakyReLU mới hỗ trợ. YOLOv8 dùng SiLU sau hầu hết lớp conv (228 op ``ConvExSwish`` trong build log của model 7 class cũ)
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`, mục 3.2 RK3588: 3.2.5 Convolution (trang PDF 59), 3.2.17 ConvolutionSwish (trang PDF 63), 3.2.54 Resize (trang PDF 87)
   * - ``compiler optimization``
     - Operator đã được compiler tự gộp thật: 228 op ``ConvExSwish`` (Conv + SiLU gộp làm 1), cờ ``conv_eltwise_activation_fuse = 1`` mặc định bật
     - Build log thật của model ``sfchd`` YOLOv8n (model 7 class cũ, cần đo lại sau khi train 5 class), ``tmp/05_training-logs/2026-09-18_sfchd_yolov8n_rknn_build_verbose_loglevel3.log`` (cờ ở dòng 154)
   * - ``datatype``
     - Trên RK3588 chỉ dùng được ``w8a8`` (INT8/INT8, mặc định). Các mode khác đều giới hạn chip: ``w4a16`` chỉ RK3576/RV1126B, ``w8a16`` chỉ RK3562, ``w16a16i`` chỉ RV1103/RV1106, ``w4a8`` chưa hỗ trợ
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`, hàm ``config``, tham số ``quantized_dtype``, tr.7

Tài liệu Rockchip thứ 2 cho cùng kết luận về đa nhân: :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`, trang PDF 27, nguyên văn:

   "For multi-cores mode (when enabling RKNN_NPU_CORE_0_1 and RKNN_NPU_CORE_0_1_2), the following ops have better acceleration: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. Other type of op will fallback to Core0 to continue running."

Lưu ý: log gọi op là ``ConvExSwish``, tài liệu gọi ``ConvolutionSwish``. Hai tên cùng chức năng (Conv + Swish gộp) nhưng không tài liệu nào xác nhận là cùng một op. Cần chạy ``eval_perf`` ở ``CORE_0_1_2`` trên board để xem từng layer thực sự chạy trên core nào ``[chưa kiểm chứng]``.

Do đó:

.. code:: text

   low FLOPs ≠ low latency
   small model ≠ fast model on NPU

1.3. Nghịch lý chu kỳ bộ nhớ: DDR Cycles so với NPU Cycles
----------------------------------------------------------------------------------------------------

Minh hoạ nhẹ trên chính model ``sfchd`` YOLOv8n (model 7 class cũ, cần đo lại sau khi train 5 class; nguồn: build log ``tmp/05_training-logs/2026-09-18_sfchd_yolov8n_rknn_build_verbose_loglevel3.log``, dòng 331, cột ``Cycles(DDR/NPU/Total)`` = ``52317/51200/52317``):

.. list-table::
   :header-rows: 1

   * - Layer
     - NPU cycles
     - DDR cycles
     - Tỉ lệ DDR/NPU
   * - ``model.4/cv2/conv``
     - 51.200
     - 52.317
     - **1.022**

NPU cycles là thời gian tính toán, còn DDR cycles là thời gian chờ đọc/ghi RAM. Ở các layer khác NPU cycles luôn cao hơn (tính toán là nút thắt). Riêng layer này DDR cycles cao hơn, cho thấy nút thắt là di chuyển dữ liệu thay vì khối lượng tính toán.

--------------

.. _22-research-question:

2. Câu hỏi nghiên cứu trọng tâm (Research Question)
====================================================================================================

   **Làm thế nào giữ PPE detection accuracy ở mức tốt nhưng đồng thời cải thiện inference efficiency trên RK3588S NPU?**
