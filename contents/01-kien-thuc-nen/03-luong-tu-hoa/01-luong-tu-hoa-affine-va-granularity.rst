:tocdepth: 1

**********************************
Lượng tử hóa affine và granularity
**********************************

.. admonition:: Trang này trả lời

   - Vì sao phải lượng tử hóa, và nó tiết kiệm được gì?
   - Một số thực được ánh xạ sang số nguyên bằng scale và zero-point thế nào?
   - Symmetric và asymmetric khác nhau ra sao khi tính tích chập bằng số nguyên?
   - Dùng một bộ tham số cho cả tensor hay mỗi channel một bộ?

.. admonition:: Tóm tắt

   - Chuyển từ 32 xuống 8 bit giảm bộ nhớ lưu tensor 4 lần và chi phí nhân ma trận 16 lần [T2 Nagel 2021 tr.2]. Đổi lại là nhiễu lượng tử hóa có thể làm giảm độ chính xác [T2 Nagel 2021 tr.2].
   - Uniform affine quantization có ba tham số: scale s, zero-point z và bit-width b. Symmetric quantizer đặt z bằng 0 [T2 Nagel 2021 tr.4].
   - Zero-point đảm bảo số 0 thực được lượng tử hóa không sai số, nên zero padding và ReLU không sinh sai số [T2 Nagel 2021 tr.4].
   - Hai nguồn ký hiệu zero-point ngược dấu (Nagel Eq. 4, 6 so với Gholami Eq. 2, 3). Trang dùng ký hiệu của Nagel [T2 Nagel 2021 tr.4] [T2 Gholami 2021 tr.5].
   - Cách chọn thường gặp là weight symmetric, activation asymmetric, để tránh số hạng phụ thuộc dữ liệu khi nhân [T2 Nagel 2021 tr.8].
   - Per-channel cho weight hầu như không đổi kết quả ở 8 bit nhưng cải thiện lớn ở 4 bit (ResNet18 Min-Max từ 0.12 lên 44.49) [T2 Nagel 2021 tr.9].
   - "Channel-wise" có hai nghĩa giữa các nguồn, và per-channel cho activation khó thực hiện trên phần cứng [T2 Nagel 2021 tr.8] [T2 Baghbanbashi 2024 tr.3].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Vì sao lượng tử hóa
======================

Mạng nơ-ron thường được train bằng FP32. Suy luận bằng FP32 đòi hỏi bộ xử lý và accumulator hỗ trợ số thực dấu phẩy động, và phải chuyển dữ liệu 32 bit từ bộ nhớ sang đơn vị tính [T2 Nagel 2021 tr.2]. Lượng tử hóa thay các đại lượng này bằng biểu diễn số nguyên ít bit. Kiểu số FP32, FP16, INT8 và số bit của chúng được giải thích ở :doc:`../01-nen-tang-ai/02-tensor-va-kieu-du-lieu`.

1.1 Tiết kiệm bộ nhớ và băng thông
----------------------------------

Nagel nêu hệ số cụ thể:

   "moving from 32 to 8 bits, the memory overhead of storing tensors decreases by a factor of 4 while the computational cost for matrix multiplication reduces quadratically by a factor of 16." [T2 Nagel 2021 tr.2]

Nagel cũng ghi các phép MAC và việc chuyển dữ liệu chiếm phần lớn năng lượng của suy luận, nên biểu diễn số nguyên ít bit giảm cả lượng dữ liệu phải chuyển lẫn kích thước và năng lượng của phép MAC [T2 Nagel 2021 tr.2].

Ví dụ suy ra (không phải số của nguồn): một ảnh đầu vào 3×640×640 có 1 228 800 phần tử. Ở 4 byte mỗi phần tử (FP32) tensor chiếm 4 915 200 byte (khoảng 4.92 MB), ở 1 byte mỗi phần tử (INT8) chiếm 1 228 800 byte (khoảng 1.23 MB). Tỉ lệ đúng bằng 4 như Nagel nêu.

1.2 Tính toán số nguyên rẻ hơn số thực
--------------------------------------

Nagel giải thích chi phí của phép tính số học số tăng từ tuyến tính đến bậc hai theo số bit, và phép cộng dấu phẩy tĩnh hiệu quả hơn phép cộng dấu phẩy động [T2 Nagel 2021 tr.2] [T2 Nagel 2021 tr.3]. Gholami trích số đo trên công nghệ 45 nm (từ Horowitz): phép cộng INT8 tiết kiệm năng lượng gấp 30 lần và tiết kiệm diện tích gấp 116 lần so với phép cộng FP32 [T2 Gholami 2021 tr.13].

Trong bộ tăng tốc, tích của INT8 được cộng dồn vào accumulator rộng hơn, thường 32 bit, để tránh tràn số khi cộng nhiều tích. Kết quả INT32 lại được lượng tử hóa trở về INT8 (requantization) trước khi ghi ra bộ nhớ cho lớp sau [T2 Nagel 2021 tr.3].

.. _fig-nagel-matmul-luong-tu-hoa:

.. figure:: ../../../_assets/img/npu/03_quantization_theory/nagel_p4_fig2.png
   :align: center
   :alt: Logic nhân ma trận trong bộ tăng tốc suy luận lượng tử hóa

   Logic nhân ma trận trong bộ tăng tốc: input và weight INT8, accumulator INT32, requantization trả về INT8. Nguồn: [T2 Nagel 2021 tr.4, Figure 2]

Cái giá phải trả: nhiễu lượng tử hóa ở bit thấp có thể làm giảm độ chính xác, một số mạng chịu nhiễu tốt còn mạng khác cần thêm công sức để khai thác lợi ích [T2 Nagel 2021 tr.2]. Các trang tiếp theo trả lời việc giảm sai số đó bằng PTQ, QAT và hybrid, xem :doc:`02-chien-luoc-ptq-qat-va-hon-hop`.

2. Ánh xạ affine
================

2.1 Scale và zero-point
-----------------------

Nagel định nghĩa lượng tử hóa đều (uniform) kiểu affine:

   "Uniform affine quantization, also known as asymmetric quantization, is defined by three quantization parameters: the scale factor s, the zero-point z and the bit-width b." [T2 Nagel 2021 tr.4]

Scale thường là số thực và là bước nhảy (step-size) của quantizer. Zero-point là số nguyên [T2 Nagel 2021 tr.4]. Nguồn nêu lý do cần zero-point nguyên:

   "The zero-point is an integer that ensures that real zero is quantized without error. This is important to ensure that common operations like zero padding or ReLU do not induce quantization error." [T2 Nagel 2021 tr.4]

2.2 Công thức lượng tử hóa và giải lượng tử
-------------------------------------------

Theo Nagel, lượng tử hóa ánh xạ vector thực x sang lưới số nguyên không dấu {0, ..., 2^b - 1}, rồi giải lượng tử để xấp xỉ x [T2 Nagel 2021 tr.4]:

.. math::

   x_{int} = \mathrm{clamp}\left(\left\lfloor \frac{x}{s} \right\rceil + z;\ 0,\ 2^b - 1\right), \qquad
   \hat{x} = s\,(x_{int} - z)

Giới hạn của lưới là :math:`q_{min} = -sz` và :math:`q_{max} = s(2^b - 1 - z)`. Giá trị ngoài đoạn này bị cắt (clipping error). Tăng scale để mở rộng đoạn làm giảm clipping error nhưng tăng rounding error, vì rounding error nằm trong :math:`[-s/2,\ s/2]` [T2 Nagel 2021 tr.4].

Gholami viết cùng ý với ký hiệu khác: :math:`Q(r) = \mathrm{Int}(r/S) - Z` và :math:`\tilde{r} = S\,(Q(r) + Z)`, trong đó S là scale, Z là zero-point nguyên và :math:`S = (\beta - \alpha)/(2^b - 1)` với :math:`[\alpha, \beta]` là clipping range [T2 Gholami 2021 tr.5]. Quá trình chọn clipping range thường gọi là calibration [T2 Gholami 2021 tr.5].

.. list-table::
   :header-rows: 1
   :widths: 22 30 30 18

   * - Nguồn
     - Lượng tử hóa
     - Giải lượng tử hóa
     - Dấu của zero-point
   * - Nagel Eq. 4, 6 (tr.4)
     - ``clamp(round(x/s) + z; 0, 2^b - 1)``
     - ``s (x_int - z)``
     - cộng khi lượng tử hóa
   * - Gholami Eq. 2, 3 (tr.5)
     - ``Int(r/S) - Z``
     - ``S (Q(r) + Z)``
     - trừ khi lượng tử hóa

Hai ký hiệu không mâu thuẫn về ý nghĩa, chỉ khác dấu quy ước của zero-point (Z của Gholami tương ứng với -z của Nagel, suy ra từ hai công thức). Trang dùng ký hiệu của Nagel từ đây trở đi.

2.3 Ví dụ số trên một tensor nhỏ
--------------------------------

Các số dưới đây do script Python tính theo công thức Nagel (làm tròn về số nguyên gần nhất, b = 8). Tensor: ``x = [-1.20, -0.35, 0.00, 0.42, 1.80, 2.50]``.

**Asymmetric** với đoạn ``[min, max] = [-1.20, 2.50]``: ``s = 3.70/255 = 0.014510`` và ``z = round(1.20/s) = 83``.

.. list-table::
   :header-rows: 1
   :widths: 14 14 14 14 14 14 16

   * - x
     - -1.20
     - -0.35
     - 0.00
     - 0.42
     - 1.80
     - 2.50
   * - x_int (0 đến 255)
     - 0
     - 59
     - 83
     - 112
     - 207
     - 255
   * - x^ = s (x_int - z)
     - -1.2043
     - -0.3482
     - 0.0000
     - 0.4208
     - 1.7992
     - 2.4957

Sai số lớn nhất là 0.0043, nhỏ hơn s/2 = 0.0073 đúng như giới hạn rounding error. Số 0.00 được lượng tử hóa thành 83 và giải lượng tử lại đúng 0.0000, tức zero-point làm đúng vai trò nêu ở mục 2.1.

**Symmetric signed** (z = 0, đoạn đối xứng quanh 0): ``s = max|x|/127 = 0.019685``, ``x_int = [-61, -18, 0, 21, 91, 127]``, ``x^ = [-1.2008, -0.3543, 0.0000, 0.4134, 1.7913, 2.5000]``, sai số lớn nhất 0.0087. Cùng 8 bit nhưng bước nhảy 0.0197 lớn hơn 0.0145 vì đoạn đối xứng [-2.50, 2.50] rộng hơn đoạn dữ liệu thực [-1.20, 2.50].

**Hai biến thể làm thay đổi sai số**:

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Cấu hình (asymmetric)
     - s
     - z
     - Sai số lớn nhất
   * - 8 bit, dữ liệu gốc
     - 0.0145
     - 83
     - 0.0043
   * - 4 bit, dữ liệu gốc
     - 0.2467
     - 5
     - 0.1033
   * - 8 bit, thêm một outlier 20.0 vào tensor
     - 0.0831
     - 14
     - 0.0361

Giảm số bit hoặc có outlier làm bước nhảy tăng và sai số tăng theo. Đây chính là sự đánh đổi clipping và rounding mà Nagel mô tả ở mục 2.2, và là lý do chọn range cần cẩn thận (xem :doc:`02-chien-luoc-ptq-qat-va-hon-hop`).

3. Symmetric và asymmetric
==========================

3.1 Khác biệt về zero-point
---------------------------

Symmetric là trường hợp đặc biệt của asymmetric với z = 0:

   "The symmetric quantizer restricts the zero-point to 0." [T2 Nagel 2021 tr.4]

Cái giá là offset bị bỏ nên ánh xạ giữa miền nguyên và miền thực bị hạn chế [T2 Nagel 2021 tr.4]. Nagel phân biệt hai lưới: unsigned symmetric hợp với phân bố một đuôi như đầu ra ReLU, signed symmetric hợp với phân bố gần đối xứng quanh 0 [T2 Nagel 2021 tr.5]. Gholami ghi asymmetric thường cho clipping range chặt hơn symmetric [T2 Gholami 2021 tr.5], và có hai kiểu symmetric: full range dùng [-128, 127], restricted range chỉ dùng [-127, 127] [T2 Gholami 2021 tr.5].

.. _fig-nagel-luoi-luong-tu:

.. figure:: ../../../_assets/img/npu/03_quantization_theory/nagel_p5_fig3.png
   :align: center
   :alt: Các lưới lượng tử hóa đều 8 bit: symmetric signed, symmetric unsigned, asymmetric

   Ba lưới lượng tử hóa đều ở 8 bit. Nguồn: [T2 Nagel 2021 tr.5, Figure 3]

.. figure:: ../../../_assets/img/npu/03_quantization_theory/gholami_fig2.png
   :align: center
   :alt: Symmetric quantization so với asymmetric quantization

   Symmetric (restricted range [-127, 127]) so với asymmetric. Nguồn: [T2 Gholami 2021 tr.5, Figure 2]

3.2 Hệ quả khi tính tích chập số nguyên
---------------------------------------

Khi cả weight và activation đều có zero-point, tích của hai giá trị giải lượng tử khai triển thành bốn số hạng (Nagel Eq. 13) [T2 Nagel 2021 tr.8]:

.. math::

   \hat{W}\hat{x} = s_w s_x\, W_{int}x_{int} - s_w z_w s_x\, x_{int} - s_w s_x z_x\, W_{int} + s_w z_w s_x z_x

Nagel phân tích: số hạng thứ nhất giống trường hợp symmetric, số hạng thứ ba và thứ tư chỉ phụ thuộc scale, offset và weight đã biết trước nên tính sẵn rồi cộng vào bias gần như miễn phí. Số hạng thứ hai phụ thuộc dữ liệu đầu vào x, nên mỗi batch phải tính thêm khi suy luận, gây chi phí đáng kể về độ trễ và công suất vì tương đương thêm một channel [T2 Nagel 2021 tr.8]. Kết luận của nguồn:

   "it is a common approach to use asymmetric activation quantization and symmetric weight quantization that avoids the additional data-dependent term." [T2 Nagel 2021 tr.8]

Ví dụ số (script Python, suy ra theo Eq. 13). Weight ``W = [0.50, 0.80, 0.30, -0.10]``, activation ``a = [-0.40, 0.60, 1.50, 2.40]``, tích thực ``W·a = 0.49``. Weight symmetric: ``s_w = 0.006299``, ``W_int = [79, 127, 48, -16]``. Activation asymmetric: ``s_a = 0.010980``, ``z_a = 36``, ``a_int = [0, 91, 173, 255]``.

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Đại lượng
     - Giá trị
   * - Tổng cộng dồn ``Σ W_int * a_int`` (INT32)
     - 15 781
   * - Số hạng tính sẵn ``z_a * Σ W_int`` (chỉ cần weight)
     - 8 568
   * - Kết quả số nguyên ``15 781 - 8 568``
     - 7 213
   * - Giải lượng tử ``s_w * s_a * 7 213``
     - 0.49891

Kết quả 0.49891 so với 0.49 thực: lệch do làm tròn ở hai tensor. Nếu weight cũng asymmetric (z_w = 7 để minh họa, W_int + 7), số hạng ``z_w * Σ a_int = 3 633`` phụ thuộc a nên phải tính lại mỗi lần suy luận. Tổng bốn số hạng ``19 414 - 3 633 - 9 576 + 1 008`` vẫn bằng 7 213, chỉ khác ở chỗ có một số hạng không thể tính sẵn.

4. Granularity
==============

Granularity là mức chia tensor thành các phần dùng chung một bộ tham số lượng tử hóa.

4.1 Per-tensor
--------------

Mọi công thức ở mục 2 mới chỉ dùng một quantizer cho mỗi tensor:

   "This is called per-tensor quantization." [T2 Nagel 2021 tr.5]

Per-tensor là lựa chọn phổ biến nhất vì phần cứng đơn giản: mọi accumulator trong Eq. 3 dùng chung hệ số :math:`s_w s_x` [T2 Nagel 2021 tr.5]. Nagel cũng ghi per-tensor cho weight và activation đã là chuẩn từ lâu vì mọi bộ tăng tốc dấu phẩy tĩnh đều hỗ trợ [T2 Nagel 2021 tr.8]. Lưu ý: hệ số chung này nằm ngoài phép cộng tổng (Eq. 3), nên MAC chạy hoàn toàn bằng số nguyên.

4.2 Per-channel
---------------

   "For example, for weight tensors, we can specify a different quantizer per output channel. This is known as per-channel quantization" [T2 Nagel 2021 tr.5]

Với weight, mỗi output channel có scale riêng và bộ tăng tốc chỉ cần nhân scale riêng cho mỗi channel đầu ra, không phải rescale lại accumulator [T2 Nagel 2021 tr.8]. Với activation thì khác:

   "Per-channel quantization of activations is much harder to implement because we cannot factor the scale factor out of the summation and would, therefore, require rescaling the accumulator for each input channel." [T2 Nagel 2021 tr.8]

Không phải phần cứng thương mại nào cũng hỗ trợ per-channel weight, nên cần kiểm tra thiết bị đích [T2 Nagel 2021 tr.8]. Gholami xếp channelwise là phương pháp chuẩn để lượng tử hóa kernel tích chập [T2 Gholami 2021 tr.7].

Bảng sau là Nagel Table 1 (tr.9): chỉ lượng tử hóa weight (symmetric), activation giữ FP32, độ chính xác ImageNet (%), trung bình 5 lần chạy. FP32: ResNet18 69.68, MobileNetV2 71.72. Chữ "(per-tensor)" ở hai hàng đầu do trang này thêm cho dễ đối chiếu, bài gốc chỉ ghi "Min-Max" và "MSE".

.. list-table::
   :header-rows: 1
   :widths: 28 12 12 12 12 12 12

   * - Phương pháp
     - ResNet18 W8
     - W6
     - W4
     - MobileNetV2 W8
     - W6
     - W4
   * - Min-Max (per-tensor)
     - 69.57
     - 63.90
     - 0.12
     - 71.16
     - 64.48
     - 0.59
   * - MSE (per-tensor)
     - 69.45
     - 64.64
     - 18.82
     - 71.15
     - 65.43
     - 13.77
   * - Min-Max (per-channel)
     - 69.60
     - 69.08
     - 44.49
     - 71.21
     - 68.52
     - 18.40
   * - MSE (per-channel)
     - 69.66
     - 69.24
     - 54.67
     - 71.46
     - 68.89
     - 27.17

Ở W8 bốn hàng chênh nhau dưới 0.3 điểm so với FP32 trên ResNet18. Ở W4 per-channel Min-Max đưa ResNet18 từ 0.12 lên 44.49 (+44.37) và MobileNetV2 từ 0.59 lên 18.40 (+17.81), hiệu của hai số trong bảng.

Nagel Table 6 (tr.17) cho thấy hiệu ứng trên detector EfficientDet-D1 (COCO, mAP, FP32 40.08):

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Cấu hình
     - Per-tensor
     - Per-channel
   * - W8A8
     - 38.29
     - 38.67
   * - W4A8
     - 0.31
     - 35.08

Nagel gán mức giảm lớn của per-tensor ở MobileNetV2 và EfficientNet lite cho tích chập depth-wise separable ("This is likely due to the quantization of the depth-wise separable convolutions.") và nói hiệu ứng tương tự ở EfficientDet-D1 và DeeplabV3 [T2 Nagel 2021 tr.17]. Đoạn này không bàn riêng cấu hình W4A8 của EfficientDet-D1.

4.3 Các kiểu khác (per-group)
-----------------------------

Nagel nói có công trình chia quantizer theo nhóm weight hoặc activation, mịn hơn per-channel. Độ mịn tăng thường cải thiện độ chính xác nhưng kèm chi phí do accumulator phải cộng các giá trị có scale khác nhau, và phần lớn bộ tăng tốc dấu phẩy tĩnh hiện tại không hỗ trợ [T2 Nagel 2021 tr.5]. Gholami gọi hai mức mịn hơn per-tensor là channelwise và sub-channelwise (groupwise), và xem groupwise là thỏa hiệp giữa độ phân giải và chi phí tính toán [T2 Gholami 2021 tr.7].

.. figure:: ../../../_assets/img/npu/03_quantization_theory/gholami_fig3.png
   :align: center
   :alt: Layerwise và channelwise quantization

   Layerwise so với channelwise: cùng một clipping range cho mọi filter của lớp, hoặc mỗi filter một range. Nguồn: [T2 Gholami 2021 tr.6, Figure 3]

Baghbanbashi (lượng tử hóa YOLOv7) so sánh thêm các granularity filter-wise, C-shape-wise, F-shape-wise và channel-wise ở 4 bit chỉ cho weight [T2 Baghbanbashi 2024 tr.3] [T2 Baghbanbashi 2024 tr.4]. Table I (tr.4), lượng tử hóa đều, mAP của YOLOv7 FP16 là 0.691:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Granularity (4 bit, uniform)
     - mAP
     - Memory-saving
   * - F-shape-wise
     - 0.635
     - ~3.93
   * - Filter-wise
     - 0.491
     - ~3.97
   * - C-shape-wise
     - 0.657
     - ~3.93
   * - Channel-wise
     - 0.621
     - ~1.68

.. figure:: ../../../_assets/img/npu/03_quantization_theory/y7q_fig3.png
   :align: center
   :alt: Các granularity lượng tử hóa trong bài YOLOv7

   Các granularity trong bài YOLOv7. Nguồn: [T2 Baghbanbashi 2024 tr.3, Figure 3]

Thuật ngữ khác nhau giữa các nguồn: cách "mỗi output filter một quantizer" mà Nagel và Gholami gọi là per-channel hay channelwise, bài YOLOv7 gọi là filter-wise và dùng "channel-wise" cho mức mịn hơn (hình trên). Vì vậy kết quả filter-wise 0.491 ở 4 bit không bác bỏ per-channel kiểu Nagel ở INT8, và hai nhóm số không cùng điều kiện (bài YOLOv7 chỉ lượng tử hóa weight ở 4 bit).

Cấu hình thường dùng trong thí nghiệm YOLO của Wang (Q-YOLO): per-channel symmetric cho weight, per-layer asymmetric cho activation:

   "In our experiments, unless otherwise noted, we employed symmetric channel-wise quantization for weights and asymmetric layer-wise quantization for activations." [T2 Wang 2023 tr.9]

RKNN-Toolkit2 chọn scheme và granularity thế nào nằm ở :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`, không nhắc lại ở đây.

5. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 52 20

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Affine và symmetric là hai họ đối lập
     - Symmetric là trường hợp đặc biệt của công thức affine với z = 0. Nagel còn gọi affine là asymmetric.
     - [T2 Nagel 2021 tr.4]
   * - Công thức Gholami và Nagel khác nhau về bản chất
     - Cùng ý, khác dấu quy ước của zero-point.
     - [T2 Nagel 2021 tr.4] [T2 Gholami 2021 tr.5]
   * - Asymmetric luôn tốt hơn vì biểu diễn đoạn chặt hơn
     - Cho clipping range chặt hơn nhưng có thêm số hạng phụ thuộc dữ liệu khi nhân với activation asymmetric.
     - [T2 Gholami 2021 tr.5] [T2 Nagel 2021 tr.8]
   * - Per-channel luôn cải thiện kết quả
     - Ở 8 bit hầu như không đổi, ở 4 bit cải thiện lớn.
     - [T2 Nagel 2021 tr.9]
   * - Có thể dùng per-channel cho cả weight lẫn activation
     - Cho activation phải rescale accumulator, và không phải phần cứng nào cũng hỗ trợ per-channel weight.
     - [T2 Nagel 2021 tr.8]
   * - "Channel-wise" luôn có cùng nghĩa
     - Bài YOLOv7 dùng thuật ngữ khác bài của Nagel và Gholami.
     - [T2 Baghbanbashi 2024 tr.3] [T2 Nagel 2021 tr.5]

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
     - 43
   * - ``Gholami 2021``
     - T2
     - :download:`quantization_survey_2021gholami.pdf <../../../_assets/pdf/papers/02_quantization/quantization_survey_2021gholami.pdf>`
     - 12
   * - ``Wang 2023``
     - T2
     - :download:`qyolo_ptq_2023wang.pdf <../../../_assets/pdf/papers/02_quantization/qyolo_ptq_2023wang.pdf>`
     - 1
   * - ``Baghbanbashi 2024``
     - T2
     - :download:`quant_yolov7_2024.pdf <../../../_assets/pdf/papers/02_quantization/quant_yolov7_2024.pdf>`
     - 5
