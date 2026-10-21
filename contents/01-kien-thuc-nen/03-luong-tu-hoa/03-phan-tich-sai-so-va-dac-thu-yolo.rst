:tocdepth: 1

*************************************
Phân tích sai số và đặc thù mạng YOLO
*************************************

.. admonition:: Trang này trả lời

   - sai số lượng tử hóa được đo thế nào?
   - model detection có vấn đề riêng khi lượng tử hóa không?

.. admonition:: Tóm tắt

   - Sai số lượng tử hóa của task đo bằng chênh lệch độ chính xác [T2 NAGEL tr.18], detection dùng COCO metrics [T2 QYOLO tr.8].
   - Quy trình debug của NAGEL đi từ toàn bộ tensor xuống từng lớp, lượng tử hóa từng phần và giữ phần còn lại ở 32 bit [T2 NAGEL tr.19].
   - SQNR chỉ được nhắc tên, không có định nghĩa hay công thức trong corpus, nên là `unknown`.
   - QYOLO gắn sụt độ chính xác của YOLO với activation distribution imbalance và liên hệ với SiLU [T2 QYOLO tr.2] [T2 QYOLO tr.7], trang coi đây là quan sát của tác giả, không phải chứng minh.
   - QYOLO viết weight "consistently" gây sụt nhiều hơn activation, nhưng Table 3 ở 6-bit YOLOv5m cho activation tệ hơn (-0.8 so với -0.4).
   - Không có số nào cho YOLOv8, C2f, DFL hay decoupled head, các mục này là `unknown`.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _36-đo-sai-số-lượng-tử-hóa:

Đo sai số lượng tử hóa
======================

**Câu hỏi:** sai số lượng tử hóa được đo thế nào?

**Nguồn nói gì**

   "Error is the difference between floating-point and quantized model accuracy." [T2 NAGEL tr.18]

..

   "Per-layer analysis If the global solutions have not restored accuracy to acceptable levels, we consider each quantizer individually. We set each quantizer sequentially, to the target bit-width while keeping the rest of the network to 32 bits" [T2 NAGEL tr.19]

   "one is interested in some sort of forward error metric (based on classification quality, perplexity, etc.)" [T2 GHOLAMI tr.4]

..

   "a metric called signal-to-quantization-noise ratio (SQNR) is defined to diagnose the quantization loss of each component of the network." [T2 QAREP tr.10]

   "Throughout our experimental analysis, we employed standard COCO metrics on the bounding box detection task to evaluate the efficacy of our approach." [T2 QYOLO tr.8]

|NAGEL Figure 9| *Hình 3.6. Sơ đồ debug PTQ của NAGEL: kiểm tra sai số khi quantize từng nhóm tensor, từng lớp, và sửa bằng range setting, AdaRound, per-channel, CLE, bias correction, cuối cùng chuyển sang QAT. Nguồn: [T2 NAGEL tr.18, Figure 9]*

**Ý chính**

- MSE giữa tensor gốc và tensor đã lượng tử hóa là tiêu chí chọn range ở mức tensor (NAGEL tr.9, Eq. 16). Sai số của task đo bằng chênh lệch độ chính xác (NAGEL tr.18) hoặc COCO metrics cho detection (QYOLO tr.8).
- Quy trình debug của NAGEL đi từ toàn bộ tensor xuống từng lớp: lượng tử hóa từng phần, giữ phần còn lại ở 32 bit (NAGEL tr.19).

**Giới hạn.** SQNR chỉ được nhắc tên, không có định nghĩa hay công thức trong corpus (QAREP tr.10 trích Sheng et al. 2018). ``unknown``. Ngưỡng ``ε`` trong Figure 9 không được nêu giá trị.

--------------

.. _37-lượng-tử-hóa-yolo-và-detection:

Lượng tử hóa YOLO và detection
==============================

**Câu hỏi:** model detection có vấn đề riêng khi lượng tử hóa không?

**Nguồn nói gì**

   "We find the performance drop of quantized YOLOs can be attributed to the activation distribution imbalance." [T2 QYOLO tr.2]

..

   "This phenomenon can be attributed to the frequent utilization of the Swish (SILU) activation function in the YOLO series." [T2 QYOLO tr.7]

   "Other more complex activation functions, such as sigmoid or Swish (Ramachandran et al., 2017), require more dedicated support. If this support is not available, we need to add a quantization step before and after the non-linearity in the graph. This can have a big impact on the accuracy of quantized model." [T2 NAGEL tr.7]

..

   "During addition, the quantization ranges of both inputs have to match exactly." [T2 NAGEL tr.7]

   "For on-device inference, these operations are folded into the previous or next linear layers in a step called batch normalization folding" [T2 NAGEL tr.6]

|QYOLO Figure 1| *Hình 3.7. Histogram activation (2048 bin) của lớp ``model.21.conv`` trong YOLOv5s: lệch, tập trung gần 0 và âm nhẹ. Nguồn: [T2 QYOLO tr.2, Figure 1]*

QYOLO Table 2 (tr.9), YOLOv5s, AP, activation asymmetric so với symmetric (real-valued 37.4):

.. list-table::
   :header-rows: 1

   * - Bit
     - Asymmetric
     - Symmetric
   * - 6-6
     - 35.9
     - 34.4
   * - 4-4
     - 14.0
     - 2.7

Cùng bảng cho YOLOv5m (real-valued 45.1): 6-6: 44.0 và 42.4, 4-4: 28.8 và 11.3.

**Ý chính**

- QYOLO gắn sụt độ chính xác của YOLO với phân bố activation lệch (QYOLO tr.2) và liên hệ với SiLU (QYOLO tr.7). Tổng hợp của file này: đây là quan sát của tác giả, không phải chứng minh.
- NAGEL nói activation phức tạp như sigmoid, Swish có thể cần thêm bước quantize trước và sau, và có thể ảnh hưởng lớn đến độ chính xác (NAGEL tr.7).
- Phép cộng cần hai đầu vào cùng range (NAGEL tr.7). NAGEL tr.8 nêu thêm concatenation cần requantization khi hai nhánh khác tham số. Tổng hợp của file này: residual và concat là điểm cần chú ý (từ "residual" là cách gọi của file, NAGEL chỉ nêu phép cộng và concat), nhưng nguồn chỉ nêu nguyên tắc, không có số cho YOLO.

**Giới hạn**

- QYOLO tr.10 viết weight "consistently" gây sụt nhiều hơn activation, nhưng Table 3 ở 6-bit YOLOv5m cho activation tệ hơn (-0.8 so với -0.4). Chỉ ở 4-bit weight mới tệ hơn rõ. Từ "consistently" quá mức.
- Không có số nào cho YOLOv8, cho C2f, DFL hay decoupled head. ``unknown``.

--------------

Chủ đề bổ sung mà các PDF nhấn mạnh
===================================

.. list-table::
   :header-rows: 1

   * - Chủ đề
     - Nguồn
   * - Accumulator INT32 và requantization trong phần cứng
     - NAGEL tr.3, tr.4 (Figure 2)
   * - Trade-off clipping và rounding
     - NAGEL tr.4
   * - Cross-layer equalization, bias correction, AdaRound
     - NAGEL tr.10 đến 15
   * - Static và dynamic quantization
     - GHOLAMI tr.6
   * - Non-uniform quantization
     - GHOLAMI tr.7. Y7Q tr.3
   * - Lượng tử hóa lớp đầu và cuối: QYOLO giữ float, QAREP lượng tử cả hai
     - QYOLO tr.9. QAREP tr.6

|NAGEL Figure 2| *Hình 3.9. Logic nhân ma trận trong bộ tăng tốc cho suy luận lượng tử hóa: input và weight INT8, accumulator INT32, requantization trả về INT8. Nguồn: [T2 NAGEL tr.4, Figure 2]*

.. |NAGEL Figure 9| image:: ../../../_assets/img/npu/03_quantization_theory/nagel_p18_fig9.png

.. |QYOLO Figure 1| image:: ../../../_assets/img/npu/03_quantization_theory/qyolo_fig1.png

.. |NAGEL Figure 2| image:: ../../../_assets/img/npu/03_quantization_theory/nagel_p4_fig2.png

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
   * - ``NAGEL``
     - T2
     - :download:`quant_whitepaper_2021nagel.pdf <../../../_assets/pdf/papers/02_quantization/quant_whitepaper_2021nagel.pdf>`
     - 7
   * - ``QYOLO``
     - T2
     - :download:`qyolo_ptq_2023wang.pdf <../../../_assets/pdf/papers/02_quantization/qyolo_ptq_2023wang.pdf>`
     - 4
   * - ``GHOLAMI``
     - T2
     - :download:`quantization_survey_2021gholami.pdf <../../../_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf>`
     - 1
   * - ``QAREP``
     - T2
     - :download:`qarepvgg_quant_2024chu.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/qarepvgg_quant_2024chu.pdf>`
     - 1
