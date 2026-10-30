:tocdepth: 1

***************************
Sai số lượng tử hóa và YOLO
***************************

.. admonition:: Trang này trả lời

   - Sai số lượng tử hóa được đo và chẩn đoán thế nào?
   - Detector như YOLO có vấn đề riêng khi lượng tử hóa không, và nguồn nào cho số?

.. admonition:: Tóm tắt

   - Nagel đo sai số của task bằng chênh lệch độ chính xác giữa mô hình float và mô hình lượng tử hóa [T2 Nagel 2021 tr.18]. Detection trong Q-YOLO dùng COCO metrics [T2 Wang 2023 tr.8].
   - Ở mức tensor, tiêu chí chọn range của Nagel là MSE giữa tensor gốc và tensor đã lượng tử hóa [T2 Nagel 2021 tr.9]. Để phân tích độ nhạy từng lớp, YOLOv6 so sánh trực tiếp MSE, SNR và Cosine similarity trên bản đồ đặc trưng đầu ra của lớp [T2 Y6 tr.6] [T2 Y6 tr.16].
   - Quy trình debug của Nagel đi từ toàn mô hình xuống từng quantizer: lượng tử hóa từng phần, giữ phần còn lại ở 32 bit [T2 Nagel 2021 tr.19].
   - Q-YOLO gắn sụt độ chính xác của YOLO với activation distribution imbalance và liên hệ với SiLU. Trang coi đây là quan sát của tác giả, không phải chứng minh [T2 Wang 2023 tr.2] [T2 Wang 2023 tr.7].
   - Q-YOLO viết quantize weight "consistently" làm sụt nhiều hơn activation, nhưng Table 3 ở 6-bit cho thấy activation tệ hơn trên cả YOLOv5s và YOLOv5m [T2 Wang 2023 tr.10].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Đo sai số lượng tử hóa
=========================

1.1 MSE và SQNR
---------------

Có hai mức đo cần tách rõ. Mức tensor đo khoảng cách giữa tensor gốc V và tensor đã lượng tử hóa :math:`\hat{V}`. Nagel dùng chuẩn Frobenius của hiệu hai tensor làm hàm mục tiêu khi chọn range (Eq. 16), tức tối thiểu hóa MSE [T2 Nagel 2021 tr.9]:

.. math::

   \arg\min_{q_{min},\,q_{max}} \left\| V - \hat{V}(q_{min}, q_{max}) \right\|_F^2

Mức task đo bằng chất lượng đầu ra cuối cùng:

   "Error is the difference between floating-point and quantized model accuracy." [T2 Nagel 2021 tr.18]

Gholami nói tương tự rằng điều người dùng quan tâm là một forward error metric dựa trên chất lượng của task, ví dụ phân loại hoặc perplexity [T2 Gholami 2021 tr.4]. Với detection, Q-YOLO đánh giá trên bài toán bounding box bằng COCO metrics chuẩn [T2 Wang 2023 tr.8].

Bên cạnh MSE, tỉ số tín hiệu trên nhiễu lượng tử hóa (SQNR - signal-to-quantization-noise ratio, Sheng et al. 2018) được sử dụng để chẩn đoán mức suy hao lượng tử hóa của từng thành phần trong mạng [T2 QAREP tr.10]. Trong phân tích độ nhạy từng lớp của YOLOv6, tác giả tính MSE và tỉ số tín hiệu trên nhiễu (SNR - signal-noise ratio) trực tiếp trên bản đồ đặc trưng đầu ra (sau hàm kích hoạt) của từng lớp khi có và không có lượng tử hóa [T2 Y6 tr.6].

1.2 Cosine similarity
---------------------

Để xếp hạng các lớp nhạy cảm với lượng tử hóa trong detector, YOLOv6 sử dụng độ tương đồng cosine (cosine similarity) song song với MSE và SNR trên bản đồ đặc trưng đầu ra của từng lớp [T2 Y6 tr.6]. Kết quả thực nghiệm ở Appendix B.2 (Table 21) trên mô hình YOLOv6-S khi chọn 6 lớp nhạy nhất giữ ở float cho thấy SNR và Cosine similarity cho phân bố độ nhạy tương quan chặt chẽ với nhau (cùng đạt 41.1% AP trên tập validation), trong khi MSE đạt 41.5% AP, gần nhất với phương pháp đánh giá AP trực tiếp từng lớp (42.0% AP) [T2 Y6 tr.16]. Cách RKNN-Toolkit2 tính và báo cáo độ tương đồng cosine giữa đầu ra float và đầu ra lượng tử hóa qua từng lớp nằm ở :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/03-hybrid-quantization-va-accuracy-analysis`.

1.3 Sai số tích lũy qua các lớp
-------------------------------

Khi tín hiệu đi qua nhiều lớp liên tiếp, sai số làm tròn ở các lớp trước có thể truyền dẫn và tích lũy sang các lớp sau. Khi thiết kế thuật toán AdaRound, Nagel nhấn mạnh việc tối ưu làm tròn trọng số phải tránh tích lũy sai số qua các lớp ("error accumulation across layers"), do đó bài toán tối ưu cục bộ của từng lớp cần xét cả hàm kích hoạt phi tuyến ở đầu ra [T2 Nagel 2021 tr.15].

Để cô lập lớp gây suy giảm độ chính xác trên toàn mạng, Nagel đưa ra quy trình chẩn đoán đi từ thô đến mịn trong sơ đồ debug (Figure 9) [T2 Nagel 2021 tr.18] [T2 Nagel 2021 tr.19]:

.. list-table::
   :header-rows: 1
   :widths: 22 52 26

   * - Bước
     - Việc làm
     - Nguồn
   * - Toàn mô hình
     - Lượng tử hóa toàn bộ activation, sau đó toàn bộ weight, xem sai số có nhỏ hơn ngưỡng không
     - [T2 Nagel 2021 tr.18]
   * - Sửa weight
     - Thử per-channel và bias correction hoặc AdaRound nếu có dữ liệu calibration
     - [T2 Nagel 2021 tr.19]
   * - Sửa activation
     - Đổi phương pháp range setting hoặc chỉnh cross-layer equalization
     - [T2 Nagel 2021 tr.19]
   * - Từng lớp
     - Lượng tử hóa từng quantizer, giữ phần còn lại ở 32 bit
     - [T2 Nagel 2021 tr.19]
   * - Cuối cùng
     - Lượng tử hóa toàn mô hình. Nếu chưa đạt, nâng bit-width, giảm granularity hoặc dùng QAT
     - [T2 Nagel 2021 tr.19]

Câu then chốt của bước từng lớp:

   "We set each quantizer sequentially, to the target bit-width while keeping the rest of the network to 32 bits" [T2 Nagel 2021 tr.19]

.. figure:: ../../../_assets/img/01-kien-thuc-nen/03-luong-tu-hoa/phan-tich-sai-so-va-dac-thu-yolo/nagel-fig9-ptq-debugging-flowchart.png
   :align: center
   :alt: Sơ đồ debug PTQ của Nagel

   Sơ đồ debug PTQ: kiểm tra sai số khi quantize từng nhóm tensor, từng lớp, và sửa bằng range setting, AdaRound, per-channel, CLE, bias correction, cuối cùng chuyển sang QAT. Nguồn: [T2 Nagel 2021 tr.18, Figure 9]

Ngưỡng sai số chấp nhận được (ký hiệu trong sơ đồ Figure 9) được xác định tùy theo yêu cầu độ chính xác mục tiêu của từng bài toán ứng dụng [T2 Nagel 2021 tr.18] [T2 Nagel 2021 tr.19].

2. Vì sao detector nhạy với lượng tử hóa
========================================

Mục này phân tích cơ chế suy giảm độ chính xác khi lượng tử hóa các mô hình YOLO dựa trên hai nghiên cứu chuyên biệt: Q-YOLO (Wang 2023, đánh giá PTQ trên YOLOv5) và bài báo lượng tử hóa trọng số YOLOv7 (Baghbanbashi 2024). Các mô hình YOLO diễn đạt bài toán phát hiện vật thể thành bài toán hồi quy một giai đoạn [T2 Baghbanbashi 2024 tr.1], dự đoán đồng thời tọa độ hộp bao và nhãn lớp trong một lượt truyền xuôi [T2 Wang 2023 tr.4]. Số liệu thực nghiệm lượng tử hóa INT8 đối với kiến trúc YOLOv8 trên phần cứng RK3588 được trình bày riêng tại :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/03-tieu-chi-than-thien-npu`.

2.1 Lệch phân bố activation do SiLU
-----------------------------------

Khi khảo sát các tầng bên trong mạng YOLO, Q-YOLO phát hiện nguyên nhân chính gây sụt giảm độ chính xác sau lượng tử hóa nằm ở sự mất cân bằng phân bố kích hoạt (activation distribution imbalance):

   "We find the performance drop of quantized YOLOs can be attributed to the activation distribution imbalance." [T2 Wang 2023 tr.2]

Tác giả mô tả giá trị activation dồn ở gần 0 và có cận dưới thực nghiệm -0.2785, rồi gán điều này cho việc dùng Swish (SiLU) thường xuyên trong họ YOLO:

   "This phenomenon can be attributed to the frequent utilization of the Swish (SILU) activation function in the YOLO series." [T2 Wang 2023 tr.7]

.. figure:: ../../../_assets/img/01-kien-thuc-nen/03-luong-tu-hoa/phan-tich-sai-so-va-dac-thu-yolo/qyolo-fig1-yolov5s-activation-histogram.png
   :align: center
   :alt: Histogram activation của lớp model.21.conv trong YOLOv5s

   Histogram activation (2048 bin) của lớp ``model.21.conv`` trong YOLOv5s: lệch, tập trung gần 0 và âm nhẹ. Nguồn: [T2 Wang 2023 tr.2, Figure 1]

Trang coi đây là quan sát và giải thích của tác giả Q-YOLO, không phải chứng minh. Nagel nói thêm các activation phức tạp như sigmoid hoặc Swish cần hỗ trợ riêng, nếu không có thì phải thêm bước lượng tử hóa trước và sau phi tuyến, và điều này có thể ảnh hưởng lớn đến độ chính xác:

   "Other more complex activation functions, such as sigmoid or Swish (Ramachandran et al., 2017), require more dedicated support. If this support is not available, we need to add a quantization step before and after the non-linearity in the graph. This can have a big impact on the accuracy of quantized model." [T2 Nagel 2021 tr.7]

Phép cộng và concat cũng là điểm cần chú ý. Nagel ghi hai đầu vào của phép cộng phải có range khớp nhau, và concat cần requantization khi hai nhánh khác tham số [T2 Nagel 2021 tr.7] [T2 Nagel 2021 tr.8]. Nguồn chỉ nêu nguyên tắc, không có số riêng cho YOLO.

2.2 Độ sụt AP theo mức bit và nhánh
-----------------------------------

Tác động của sự lệch phân bố activation thể hiện trực tiếp qua độ chênh lệch COCO AP giữa cấu hình lượng tử hóa bất đối xứng (asymmetric) và đối xứng (symmetric). Q-YOLO Table 2 (tr.9) trên YOLOv5s (bản số thực đạt 37.4 AP) ghi nhận:

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Bit (weight-activation)
     - Asymmetric
     - Symmetric
   * - 6-6
     - 35.9
     - 34.4
   * - 4-4
     - 14.0
     - 2.7

Q-YOLO Table 3 (tr.10) tách riêng ảnh hưởng của weight và activation, AP và độ lệch so với real-valued:

.. list-table::
   :header-rows: 1
   :widths: 30 17 17 18 18

   * - Cấu hình (weight-activation)
     - YOLOv5s only weights
     - YOLOv5s only activation
     - YOLOv5m only weights
     - YOLOv5m only activation
   * - 6 bit
     - 36.7 (-0.7)
     - 36.6 (-0.8)
     - 44.7 (-0.4)
     - 44.3 (-0.8)
   * - 4 bit
     - 19.6 (-16.3)
     - 30.6 (-5.3)
     - 34.6 (-9.4)
     - 37.7 (-6.3)

Real-valued: YOLOv5s 37.4, YOLOv5m 45.1. Văn bản của bài nói quantize weight "consistently" gây sụt lớn hơn quantize activation [T2 Wang 2023 tr.10]. Số trong bảng chỉ ủng hộ điều đó ở 4 bit. Ở 6 bit activation sụt nhiều hơn weight trên cả hai mô hình (-0.8 so với -0.7 và -0.4), nên từ "consistently" quá mức.

Bài YOLOv7 bổ sung một kết quả khác về lựa chọn thuật toán. Cùng ở 4 bit và cùng granularity, lượng tử hóa không đều (non-uniform) cho mAP cao hơn đều (uniform): filter-wise 0.672 so với 0.491, channel-wise 0.672 so với 0.621 (mAP của YOLOv7 FP16 là 0.691) [T2 Baghbanbashi 2024 tr.4]. Phương pháp non-uniform cụ thể là PWLQ trong bài, và hai nhóm số chỉ lượng tử hóa weight [T2 Baghbanbashi 2024 tr.4].

3. Chủ đề bổ sung
=================

.. list-table::
   :header-rows: 1
   :widths: 40 36 24

   * - Chủ đề
     - Điều nguồn nói
     - Nguồn
   * - Accumulator INT32 và requantization
     - Tích INT8 cộng dồn vào accumulator rộng để tránh tràn, rồi requantize về INT8
     - [T2 Nagel 2021 tr.3]
   * - Đánh đổi clipping và rounding
     - Mở rộng range giảm clipping error nhưng tăng rounding error
     - [T2 Nagel 2021 tr.4]
   * - Lớp đầu và lớp cuối
     - Q-YOLO giữ ở độ chính xác gốc vì nhạy với mất độ chính xác
     - [T2 Wang 2023 tr.9]
   * - Static và dynamic quantization
     - Static không thêm chi phí lúc chạy nhưng thường kém chính xác hơn
     - [T2 Gholami 2021 tr.6]
   * - Non-uniform quantization
     - Có thể đạt độ chính xác cao hơn ở cùng bit-width
     - [T2 Gholami 2021 tr.7]

Các chủ đề CLE, bias correction và AdaRound được Nagel trình bày ở tr.10 đến tr.15 và là các bước sửa trong sơ đồ debug ở mục 1.3. Cách chọn range và PTQ nói chung xem :doc:`02-chien-luoc-ptq-qat-va-hon-hop`. Kết quả đo độ chính xác sau lượng tử hóa bằng RKNN-Toolkit2 và quy trình lỗi độ chính xác trên RK3588 nằm ở :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/03-hybrid-quantization-va-accuracy-analysis`.

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 52 20

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Sai số lượng tử hóa là một con số MSE duy nhất
     - MSE dùng để chọn range của tensor, còn sai số của task đo bằng chênh lệch độ chính xác hoặc COCO metrics
     - [T2 Nagel 2021 tr.9] [T2 Nagel 2021 tr.18] [T2 Wang 2023 tr.8]
   * - Quantize weight luôn làm sụt nhiều hơn activation
     - Chỉ đúng rõ ở 4 bit. Ở 6 bit activation sụt nhiều hơn trên YOLOv5s và YOLOv5m
     - [T2 Wang 2023 tr.10]
   * - SiLU là nguyên nhân đã được chứng minh của sụt AP
     - Q-YOLO chỉ gán nguyên nhân, không có thí nghiệm cô lập
     - [T2 Wang 2023 tr.7]
   * - Số liệu 4-bit và 6-bit của YOLOv5/YOLOv7 áp dụng thẳng cho YOLOv8 INT8
     - Q-YOLO và Baghbanbashi đo ở cấu hình 4-bit/6-bit trên YOLOv5/YOLOv7, khác với kiến trúc C2f, decoupled head và lượng tử hóa INT8 của YOLOv8
     - [T2 Wang 2023 tr.9] [T2 Baghbanbashi 2024 tr.4]
   * - Kết quả 4 bit weight-only của bài YOLOv7 giải thích INT8 của RKNN
     - Bài chỉ lượng tử hóa weight ở 4 bit, khác điều kiện INT8
     - [T2 Baghbanbashi 2024 tr.4]

Nguồn
=====

.. list-table::
   :header-rows: 1
   :widths: 22 8 60 10

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``Nagel 2021``
     - T2
     - :download:`quant_whitepaper_2021nagel.pdf <../../../_assets/pdf/papers/02_quantization/quant_whitepaper_2021nagel.pdf>`
     - 24
   * - ``Gholami 2021``
     - T2
     - :download:`quantization_survey_2021gholami.pdf <../../../_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf>`
     - 3
   * - ``Wang 2023``
     - T2
     - :download:`qyolo_ptq_2023wang.pdf <../../../_assets/pdf/papers/02_quantization/qyolo_ptq_2023wang.pdf>`
     - 15
   * - ``Baghbanbashi 2024``
     - T2
     - :download:`quant_yolov7_2024.pdf <../../../_assets/pdf/papers/02_quantization/quant_yolov7_2024.pdf>`
     - 5
   * - ``Y6``
     - T2
     - :download:`yolov6_hwfriendly_2022li.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/yolov6_hwfriendly_2022li.pdf>`
     - 5
   * - ``QAREP``
     - T2
     - :download:`qarepvgg_quant_2024chu.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/qarepvgg_quant_2024chu.pdf>`
     - 1
