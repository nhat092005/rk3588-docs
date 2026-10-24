:tocdepth: 1

************
Research gap
************

.. admonition:: Trang này trả lời

   - Khoảng trống nghiên cứu (Research Gap) giữa các mô hình hiện tại và việc triển khai tối ưu trên NPU RK3588 là gì?
   - Vì sao nghịch lý FLOPs thấp nhưng NPU suy luận chậm lại xảy ra trên thực tế?
   - Những đánh đổi giữa độ chính xác và độ trễ khi lượng tử hóa INT8 trên kiến trúc đa lõi RK3588 cần được kiểm chứng ra sao?

.. admonition:: Tóm tắt

   - Cách làm đúng là đọc paper, liệt kê limitation, verify trên RK3588S, tìm bottleneck thật rồi mới đặt research question, không chọn kỹ thuật trước.
   - Case A (FP16 còn chậm): S3NAS bỏ bớt SE blocks cho 82.72% top-1 với 11.66ms latency, vừa nhanh hơn vừa chính xác hơn (Table 6, tr.10).
   - Giả thuyết đổi SiLU sang ReLU hoặc LeakyReLU để multi-core tăng tốc trên Conv, cần đo latency ở `CORE_0_1_2` và mAP, hiện `[chưa kiểm chứng]`.
   - Case B (INT8 giảm accuracy): RKNN-Toolkit2 có `hybrid_quantization_step1` / `hybrid_quantization_step2`, và quantize theo channel đã là mặc định.
   - Case C (FLOPs thấp nhưng NPU chậm): DAHD-YOLO có 21.8 GFLOPs so với 28.4 của YOLOv8s nhưng chỉ 50.2 FPS so với 70.9 FPS trên RK3588 INT8.
   - Chiều ngược lại cũng đúng: ours-M có nhiều parameters và FLOPS hơn EfficientNet-B1 nhưng latency ngắn hơn, nên độ phức tạp không phải chỉ báo trực tiếp của latency.

.. contents:: Trong trang này
   :local:
   :depth: 2

.. _41-sai-cách:

1. Tiếp cận sai cách: Chọn giải pháp trước khi tìm vấn đề
====================================================================================================

.. code:: text

   “Tôi muốn thêm attention”
      ↓
   “Tôi muốn pruning”
      ↓
   “Tôi muốn INT8”
      ↓
   sau đó mới tìm problem để giải thích

.. _42-đúng-cách:

2. Tiếp cận đúng cách: Xuất phát từ nút thắt phần cứng thực tế
====================================================================================================

.. code:: text

   Đọc paper
      ↓
   Liệt kê limitation
      ↓
   Tìm limitation lặp lại
      ↓
   Verify limitation trên RK3588S
      ↓
   Tìm bottleneck thật
      ↓
   Đặt research question
      ↓
   Chọn contribution

.. _43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark:

3. Các khoảng trống nghiên cứu tiềm năng (Research Gaps)
====================================================================================================

.. _case-a--fp16-còn-chậm:

3.1. Case A: FP16 còn chậm (Cần tối ưu kiến trúc và toán tử)
----------------------------------------------------------------------------------------------------

.. code:: text

   YOLOv8n
      ↓
   accuracy tốt
      ↓
   deploy RK3588S thành công
      ↓
   nhưng
      ↓
   NPU latency còn cao

Hướng tối ưu có thể cân nhắc:

.. code:: text

   architecture optimization
   → Tối ưu cấu trúc model để giảm compute nhưng vẫn giữ accuracy.

   operator-aware redesign
   → Chỉnh model theo các operator mà RK3588S NPU hỗ trợ và xử lý tốt.

   structured pruning
   → Cắt bỏ nguyên channel/filter/block ít quan trọng để model thật sự nhẹ hơn.

   lighter detection head
   → Làm phần đầu ra dự đoán bbox/class của YOLO đơn giản và nhẹ hơn.

   input-resolution optimization
   → Chọn kích thước input phù hợp để cân bằng accuracy và latency.

Bằng chứng RK3588-relevant: :download:`_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf <../../_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf>`, Table 6, tr.10. Paper viết nguyên văn về **Selective SE Removal**:

   "Finally, we selectively removed SE blocks from ours-XL+, resulting in ours-XL-rmSE+. [...] After removing SE blocks from ours-XL+ based on the metric, only about 60% of the blocks in the network have SE blocks. As a result, we could make the latency shorter, while the accuracy was slightly improved than ours-XL+. This model achieves 82.72% top-1 accuracy with only 11.66ms latency."

Tức bỏ bớt SE blocks (tốn băng thông bộ nhớ, không khai thác tốt mảng PE của NPU) giúp model **vừa nhanh hơn vừa chính xác hơn** cùng lúc mà không phải đánh đổi.

**``architecture optimization`` (Linear Depth Scaling):** cùng paper S3NAS, Table 4, tr.9 (dồn nhiều block hơn vào stage sâu, nơi feature map nhỏ nhưng số kênh lớn):

.. list-table::
   :header-rows: 1

   * - Cách chia block
     - Accuracy
     - Latency
   * - Constant depth (baseline)
     - 75.85%
     - 1.28 ms
   * - Linear depth
     - **77.09%**
     - 1.24 ms

..

   "As shown in Table 4, a supernet with linear depth outperforms a supernet with constant depth in terms of accuracy with similar latency. It confirms that this simple change of block assignment in supernet gives notable accuracy boost with the same latency constraint, without any additional optimization techniques."

**``operator-aware redesign`` (structural reparameterization):** :download:`_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, tr.6, Figure 2 (train dùng nhiều nhánh, inference gộp về 1 conv chuẩn mà NPU hỗ trợ tốt):

   "DBB has six transformation methods, which correspond to transforming conv-BN, branch addition, sequential convolutions, depth concatenation, and average pooling into a single convolutional layer, respectively."

Lưu ý: bản thân phép gộp không tốn thêm chi phí lúc inference, nhưng module DBCA đầy đủ của DAHD-YOLO còn kèm attention (CAA). Xem Case C, cả model vẫn chậm hơn YOLOv8s, nên phải đo trên board chứ không suy từ lý thuyết.

Giả thuyết cụ thể cho đề tài (xem bảng :ref:`Research problem đề xuất <21-research-problem-đề-xuất>`): đổi activation SiLU của YOLOv8 sang ReLU hoặc LeakyReLU, vì theo tài liệu Rockchip chỉ Conv + ReLU/Clip/LeakyReLU mới được tăng tốc khi chạy nhiều core, còn Conv + Swish thì không. Cần đo 2 thứ: latency ở ``CORE_0_1_2`` trước và sau khi đổi, và mAP có giảm không (phải train lại) ``[chưa kiểm chứng]``.

**``lighter detection head``:** :download:`_assets/pdf/papers/07_ppe_detection/ppe_yolo_chv_2021wang.pdf <../../_assets/pdf/papers/07_ppe_detection/ppe_yolo_chv_2021wang.pdf>`, Table 4, tr.12 (mục 3.2 "Different Layers"):

.. list-table::
   :header-rows: 1

   * - Model
     - mAP
     - Time GPU
   * - YOLO v3 (3 layers)
     - **82.65%**
     - **27.15 ms**
   * - YOLO v3 (5 layers)
     - 81.99%
     - 37.04 ms

..

   "In theory, the model with more layers has a stronger ability to detect small objects. However, the results show that the YOLO v3 (3 layers)'s mAP is only slightly higher than YOLO v3 (5 layers)'s. [...] In experiments, YOLO v3 (three layers) needs 27.25 ms to process an image on GPU, which is 27% faster than YOLO v3 (five layers)."

Tức thêm detection layer không tăng accuracy mà còn chậm hơn 27%, ủng hộ hướng head nhẹ hơn. (Paper ghi 27.25 ms trong văn bản nhưng 27.15 ms trong bảng, một sai khác nhỏ ngay trong bản gốc.)

.. _case-b--int8-nhanh-nhưng-accuracy-giảm:

3.2. Case B: INT8 nhanh nhưng suy giảm độ chính xác
----------------------------------------------------------------------------------------------------

.. code:: text

   FP16
      ↓
   INT8 PTQ
      ↓
   latency giảm
      ↓
   nhưng
      ↓
   AP_helmet / AP_safety_clothes giảm mạnh

Hướng tối ưu có thể cân nhắc:

.. code:: text

   better calibration
   → Chọn calibration dataset đại diện tốt hơn để INT8 giữ accuracy tốt hơn.

   QAT
   → Train model có mô phỏng quantization để model thích nghi với INT8.

   mixed precision
   → Không ép mọi layer dùng cùng precision. Layer nhạy có thể giữ FP16, layer khác dùng INT8.

   quantization-sensitive layer analysis
   → Phân tích layer nào bị giảm accuracy nhiều khi quantize để xử lý riêng.

Bằng chứng: :download:`_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf <../../_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf>`, Figure 7, tr.12. Bảng số liệu ở công nghệ 45nm: phép cộng INT8 (8b Add) tốn **0,03 pJ / 36 µm²**, phép cộng FP32 (32b FP Add) tốn **0,9 pJ / 7700 µm²**, nghĩa là INT8 rẻ hơn **30 lần năng lượng, ~214 lần diện tích**. Paper viết nguyên văn kết luận từ số liệu này:

   "As one can see, lower precision provides exponentially better energy efficiency and higher throughput."

Đây là lý do NPU luôn thiên về precision thấp, không chỉ vì giảm bộ nhớ.

Các hướng cứu accuracy ở trên, đối chiếu với thực tế RKNN-Toolkit2 trên RK3588 (Toolkit2-API = :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`):

.. list-table::
   :header-rows: 1

   * - Hướng
     - Thực tế trên RKNN-Toolkit2
   * - ``better calibration``
     - DAHD-YOLO dùng 200 ảnh calibration, :download:`dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>` tr.18: *"We establish a calibration set, comprising 200 randomly selected images from the training data"*
   * - ``mixed precision``
     - API thật: ``hybrid_quantization_step1`` / ``hybrid_quantization_step2`` (Toolkit2-API mục 2.12, trang PDF 20)
   * - Quantize theo channel
     - Đã là mặc định, không cần làm thêm. Toolkit2-API trang PDF 8: *"quantized_method: Currently support layer, channel or group{SIZE}. The default value is channel."*

Chú thích "quantize theo channel": khi quantize trọng số 1 layer conv, cần chọn khoảng giá trị (clipping range) để map sang INT8.

- **Theo layer (layerwise)**: Cả layer dùng chung 1 khoảng, filter nào có giá trị dao động hẹp sẽ bị mất độ chính xác, vì khoảng chung bị kéo rộng theo filter có giá trị dao động rộng nhất.
- **Theo channel (channelwise)**: Mỗi filter có khoảng riêng, giữ độ chính xác cho từng filter, chi phí gần như không đáng kể.

:download:`quantization_survey_2021gholami.pdf <../../_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf>`, Figure 3, tr.6, nguyên văn:

   "In layerwise quantization, the same clipping range is applied to all the filters that belong to the same layer. This can result in bad quantization resolution for the channels that have narrow distributions [...]. One can achieve better quantization resolution using channelwise quantization that dedicates different clipping ranges to different channels."

.. _case-c--flops-thấp-nhưng-npu-vẫn-chậm:

3.3. Case C: FLOPs thấp nhưng NPU vẫn chậm (Nghịch lý độ phức tạp)
----------------------------------------------------------------------------------------------------

.. code:: text

   Model A
      ↓
   FLOPs thấp

   nhưng

   operator/layout/memory behavior
      ↓
   RKNN/NPU xử lý không hiệu quả
      ↓
   latency cao

Đây là dạng gap rất hợp với hướng **hardware-aware**.

Bằng chứng trên đúng RK3588: :download:`_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, GFLOPs từ Table 4 (tr.15), FPS từ Table 6 (tr.18):

.. list-table::
   :header-rows: 1

   * - Model
     - GFLOPs
     - Size
     - FPS 720P trên RK3588 (INT8)
   * - YOLOv8s
     - 28.4
     - 12.6M
     - **70.9**
   * - DAHD-YOLO
     - 21.8 (−23,2%)
     - 8.8M
     - **50.2**

DAHD-YOLO ít FLOPs hơn 23% và nhỏ hơn 30%, nhưng chạy chậm hơn ~29% trên NPU thật. Lưu ý: mức 50.2 FPS dẫn ở mục 1 là nhờ multi-thread 3 core, trong khi bản thân thay đổi kiến trúc của DAHD-YOLO lại làm model chậm hơn YOLOv8s gốc.

Chiều ngược lại cũng đúng: model nhiều FLOPs/params hơn vẫn có thể chạy nhanh hơn trên NPU. :download:`_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf <../../_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf>`, tr.9 (so sánh ``ours-M`` với EfficientNet-B1 trên NPU MIDAP), nguyên văn:

   "Note that the number of parameters and the number of FLOPS in ours-M is larger than EfficientNet-B1. It implies that the complexity of the network is not a direct indicator of the end-to-end latency of the network. The end-to-end latency depends on the NPU architecture, and the proposed NAS technique could find a larger network with shorter latency by adding the latency factor to the loss function directly."
