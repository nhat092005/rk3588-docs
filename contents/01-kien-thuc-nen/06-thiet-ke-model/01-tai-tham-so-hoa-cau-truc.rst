:tocdepth: 1

************************
Tái tham số hóa cấu trúc
************************

.. admonition:: Trang này trả lời

   - Gộp nhánh lúc suy luận là biến đổi toán học gì và điều kiện tương đương là gì?
   - Cấu trúc đa nhánh của RepVGG và MobileOne khác nhau như thế nào giữa huấn luyện và suy luận?
   - Vì sao RepVGG suy giảm độ chính xác nghiêm trọng khi lượng tử hóa INT8 và QARepVGG khắc phục bằng cách nào?

.. admonition:: Tóm tắt

   - Tái tham số hóa cấu trúc (structural re-parameterization) duy trì mạng nhiều nhánh lúc huấn luyện nhằm tăng khả năng biểu diễn, sau đó gộp thành một nhánh đơn duy nhất lúc suy luận để tối ưu băng thông bộ nhớ và tốc độ thực thi.
   - Khối RepVGG kết hợp ba nhánh: Conv 3x3 kèm BN, Conv 1x1 kèm BN và Identity kèm BN; khi suy luận, tham số BN được gộp vào Conv, các kernel 1x1 được đệm không thành 3x3 và cộng dồn thành một lớp Conv 3x3 duy nhất kèm bias [T2 REPVGG tr.5].
   - MobileOne áp dụng tái tham số hóa cho cấu trúc tích chập tách kênh (depthwise và pointwise), đồng thời bổ sung hệ số over-parameterization k nhánh nhằm tăng độ chính xác mà không làm tăng chi phí suy luận [T2 MOBONE tr.4, 5].
   - RepVGG gặp hiện tượng suy giảm độ chính xác nghiêm trọng khi lượng tử hóa INT8 (sụt hơn 20% top-1 ImageNet) do việc cộng ba nhánh có BN riêng rẽ làm bùng nổ phương sai activation và xuất hiện ngoại lai ở trọng số gộp [T2 QAREP tr.1, 5].
   - QARepVGG khắc phục bằng cách loại bỏ BN ở nhánh identity và 1x1, đồng thời đặt một lớp BN duy nhất sau phép cộng ba nhánh, giữ nguyên khả năng gộp thành Conv 3x3 đơn mà vẫn bảo toàn độ chính xác INT8 [T2 QAREP tr.1, 5].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Ý tưởng: Nhiều nhánh khi train, một nhánh khi suy luận
=========================================================

Trong thiết kế mạng nơ-ron tích chập, cấu trúc nhiều nhánh (multi-branch topology) như ResNet hay Inception giúp mô hình huấn luyện ổn định và đạt độ chính xác cao nhờ tạo ra tập hợp vô số các đường truyền gradient ngắn, khắc phục hiện tượng triệt tiêu gradient [T2 REPVGG tr.1, 2]. Tuy nhiên, khi triển khai suy luận trên phần cứng thực tế, kiến trúc nhiều nhánh bộc lộ hai nhược điểm chí mạng:

1. **Chi phí truy cập bộ nhớ (Memory Access Cost - MAC) và chiếm dụng bộ nhớ đỉnh**: Ở mạng nhiều nhánh, dữ liệu đầu vào của khối phải được lưu giữ trong bộ nhớ đệm (on-chip SRAM hoặc DRAM) cho đến khi toàn bộ các nhánh hoàn tất tính toán để thực hiện phép cộng hoặc ghép kênh (concatenation). Điều này làm tăng gấp đôi mức chiếm dụng bộ nhớ đỉnh so với kích thước tensor đầu vào [T2 REPVGG tr.4]. Ngược lại, cấu trúc đơn nhánh (plain topology) cho phép giải phóng bộ nhớ của tensor đầu vào ngay khi lớp hiện tại kết thúc tính toán [T2 REPVGG tr.4].
2. **Chi phí khởi chạy kernel và đồng bộ hóa**: Mạng nhiều nhánh chia nhỏ khối tính toán thành nhiều toán tử phân mảnh (fragmented operators), tạo thêm chi phí khởi chạy kernel (kernel launching) và đồng bộ hóa luồng tính toán trên các thiết bị song song mạnh như GPU hoặc NPU [T2 REPVGG tr.4].

Ý tưởng cốt lõi của tái tham số hóa cấu trúc là tách biệt hoàn toàn cấu trúc lúc huấn luyện và cấu trúc lúc suy luận:

- **Lúc huấn luyện**: Sử dụng kiến trúc nhiều nhánh để tối đa hóa dung lượng học và độ chính xác phân loại.
- **Lúc suy luận**: Sử dụng các phép biến đổi đại số tuyến tính để hợp nhất (fuse) toàn bộ các nhánh song song, bao gồm cả các lớp chuẩn hóa Batch Normalization (BN), thành một nhánh tích chập đơn duy nhất [T2 REPVGG tr.2, 5].

Sau khi gộp, mô hình suy luận hoàn toàn là một chuỗi tuần tự gồm một loại toán tử duy nhất: Conv 3x3 kết hợp với hàm kích hoạt ReLU, giúp phần cứng tính toán đạt hiệu suất lấp đầy nhân xử lý tối đa và tối ưu luồng dữ liệu [T2 REPVGG tr.2].

.. list-table:: So sánh đặc tính khối đa nhánh lúc huấn luyện và đơn nhánh lúc suy luận
   :header-rows: 1
   :widths: 25 35 40

   * - Tiêu chí so sánh
     - Khối đa nhánh (Lúc huấn luyện)
     - Khối đơn nhánh (Lúc suy luận)
   * - Dạng topo đồ thị
     - Phân nhánh song song (3x3, 1x1, Identity)
     - Đơn đường thẳng tuần tự (Plain feed-forward)
   * - Bộ nhớ lưu trữ tensor
     - Giữ tensor gốc đến điểm hội tụ (tăng peak SRAM)
     - Giải phóng ngay sau khi tính xong lớp hiện tại
   * - Toán tử thực thi
     - Nhiều toán tử phân mảnh, yêu cầu đồng bộ
     - Duy nhất Conv 3x3 kèm ReLU [T2 REPVGG tr.2]
   * - Khả năng tối ưu phần cứng
     - Bị giới hạn bởi băng thông truy cập bộ nhớ
     - Tận dụng tối đa bộ nhớ đệm và tăng throughput

2. RepVGG
=========

2.1 Ba nhánh: Conv 3x3, Conv 1x1, Identity
------------------------------------------

Khối xây dựng cơ bản của mạng RepVGG ở giai đoạn huấn luyện bao gồm ba nhánh song song cùng nhận chung một tensor đầu vào :math:`M^{(1)} \in \mathbb{R}^{N \times C_1 \times H_1 \times W_1}` [T2 REPVGG tr.5]:

1. **Nhánh Conv 3x3**: Gồm một lớp tích chập với kernel kích thước :math:`3 \times 3`, trọng số :math:`W^{(3)} \in \mathbb{R}^{C_2 \times C_1 \times 3 \times 3}`, theo sau là một lớp Batch Normalization.
2. **Nhánh Conv 1x1**: Gồm một lớp tích chập với kernel kích thước :math:`1 \times 1`, trọng số :math:`W^{(1)} \in \mathbb{R}^{C_2 \times C_1 \times 1 \times 1}`, theo sau là một lớp Batch Normalization.
3. **Nhánh Identity**: Nhánh kết nối tắt truyền thẳng tensor đầu vào qua một lớp Batch Normalization mà không qua tích chập (chỉ xuất hiện khi số kênh vào bằng số kênh ra :math:`C_1 = C_2` và stride bằng 1) [T2 REPVGG tr.5].

Đầu ra của khối huấn luyện là tổng của ba nhánh trước khi đi qua hàm kích hoạt phi tuyến [T2 REPVGG tr.5]:

.. math::

   M^{(2)} = \text{bn}(M^{(1)} * W^{(3)}, \mu^{(3)}, \sigma^{(3)}, \gamma^{(3)}, \beta^{(3)})
   + \text{bn}(M^{(1)} * W^{(1)}, \mu^{(1)}, \sigma^{(1)}, \gamma^{(1)}, \beta^{(1)})
   + \text{bn}(M^{(1)}, \mu^{(0)}, \sigma^{(0)}, \gamma^{(0)}, \beta^{(0)})

Để đảm bảo tính tương đương toán học khi gộp, RepVGG đòi hỏi các nhánh tích chập phải có cùng bước trượt (stride), đồng thời cấu hình đệm (padding) của nhánh 1x1 phải nhỏ hơn nhánh 3x3 đúng một pixel [T2 REPVGG tr.5]:

   "Note that the equivalence of such transformations requires the 3 × 3 and 1 × 1 layer to have the same stride, and the padding configuration of the latter shall be one pixel less than the former." [T2 REPVGG tr.5]

.. figure:: ../../../_assets/img/npu/08_model_design_for_npu/repvgg_p5_fig4.png
   :align: center
   :alt: Structural re-parameterization của một khối RepVGG

   Hình 8.1a. Structural re-parameterization của một khối RepVGG: ba nhánh (3x3 + BN, 1x1 + BN, identity + BN) được cộng lại thành một Conv 3x3 (A: cấu trúc, B: tham số). Nguồn: [T2 REPVGG tr.5, Figure 4]

2.2 Công thức gộp kernel và bias
--------------------------------

Quá trình hợp nhất khối RepVGG thành một lớp Conv 3x3 duy nhất kèm vector bias được thực hiện tuần tự qua bốn bước toán học:

**Bước 1: Gộp Batch Normalization vào lớp tích chập đứng trước**

Lớp BN ở chế độ suy luận áp dụng phép biến đổi affine lên từng kênh đầu ra :math:`i` (:math:`1 \le i \le C_2`):

.. math::

   \text{bn}(M, \mu, \sigma, \gamma, \beta)_{:,i,:,:} = (M_{:,i,:,:} - \mu_i) \frac{\gamma_i}{\sigma_i} + \beta_i

Do tính chất phân phối tuyến tính của phép tích chập, lớp BN đứng sau Conv có thể được gộp hoàn toàn vào một lớp Conv mới có trọng số :math:`W'` và bias :math:`b'` [T2 REPVGG tr.5]:

.. math::

   W'_{i,:,:,:} = \frac{\gamma_i}{\sigma_i} W_{i,:,:,:}, \quad b'_i = \beta_i - \frac{\mu_i \gamma_i}{\sigma_i}

**Bước 2: Chuyển đổi nhánh Identity thành lớp Conv 1x1**

Nhánh Identity được biểu diễn tương đương dưới dạng một lớp Conv 1x1 với trọng số là ma trận đơn vị :math:`W^{(0)} \in \mathbb{R}^{C_2 \times C_1 \times 1 \times 1}`, trong đó :math:`W^{(0)}_{i,j,0,0} = 1` nếu :math:`i = j` và bằng :math:`0` nếu :math:`i \ne j`. Sau đó, lớp BN của nhánh identity được gộp vào kernel đơn vị này theo đúng công thức ở Bước 1 [T2 REPVGG tr.5].

**Bước 3: Đệm không cho các kernel 1x1 về kích thước 3x3**

Hai kernel 1x1 thu được sau khi gộp BN (từ nhánh 1x1 và nhánh identity) được đệm không (zero-padding) xung quanh để đạt kích thước không gian :math:`3 \times 3`. Giá trị trọng số 1x1 được đặt chính xác vào tâm của ma trận :math:`3 \times 3` (tọa độ hàng 1, cột 1 theo chỉ số từ 0) [T2 REPVGG tr.5].

**Bước 4: Cộng dồn trọng số và bias**

Kernel :math:`3 \times 3` cuối cùng và vector bias cuối cùng là tổng số học của các thành phần đã quy đổi từ cả ba nhánh [T2 REPVGG tr.5]:

.. math::

   W_{\text{final}} = W'^{(3)} + \text{pad}(W'^{(1)}) + \text{pad}(W'^{(0)}), \quad b_{\text{final}} = b'^{(3)} + b'^{(1)} + b'^{(0)}

   "Then we obtain the final bias by adding up the three bias vectors, and the final 3 × 3 kernel by adding the 1×1 kernels onto the central point of 3×3 kernel" [T2 REPVGG tr.5]

2.3 Ví dụ số gộp một khối nhỏ
-----------------------------

Xét một khối RepVGG đơn giản có :math:`C_{\text{in}} = 1`, :math:`C_{\text{out}} = 1`, bước trượt :math:`\text{stride} = 1`.

Trọng số và tham số BN ban đầu của ba nhánh:

- **Nhánh 3x3**:
  :math:`W^{(3)} = \begin{bmatrix} 1.0 & 0.0 & -1.0 \\ 0.0 & 2.0 & 0.0 \\ 1.0 & 1.0 & 0.0 \end{bmatrix}`, tham số BN gồm :math:`\gamma^{(3)} = 2.0, \sigma^{(3)} = 1.0, \mu^{(3)} = 0.5, \beta^{(3)} = 1.0`.
- **Nhánh 1x1**:
  :math:`W^{(1)} = \begin{bmatrix} 3.0 \end{bmatrix}`, tham số BN gồm :math:`\gamma^{(1)} = 1.5, \sigma^{(1)} = 0.5, \mu^{(1)} = 1.0, \beta^{(1)} = 0.5`.
- **Nhánh Identity**:
  :math:`W^{(0)} = \begin{bmatrix} 1.0 \end{bmatrix}`, tham số BN gồm :math:`\gamma^{(0)} = 1.0, \sigma^{(0)} = 2.0, \mu^{(0)} = 0.4, \beta^{(0)} = 0.2`.

Thực hiện các bước tính toán (kiểm chứng bằng script Python):

1. **Gộp BN cho nhánh 3x3**:
   Hệ số tỉ lệ: :math:`\frac{\gamma^{(3)}}{\sigma^{(3)}} = \frac{2.0}{1.0} = 2.0`.

   .. math::

      W'^{(3)} = 2.0 \times W^{(3)} = \begin{bmatrix} 2.0 & 0.0 & -2.0 \\ 0.0 & 4.0 & 0.0 \\ 2.0 & 2.0 & 0.0 \end{bmatrix}

      b'^{(3)} = \beta^{(3)} - \frac{\mu^{(3)} \gamma^{(3)}}{\sigma^{(3)}} = 1.0 - (0.5 \times 2.0) = 0.0

2. **Gộp BN cho nhánh 1x1**:
   Hệ số tỉ lệ: :math:`\frac{\gamma^{(1)}}{\sigma^{(1)}} = \frac{1.5}{0.5} = 3.0`.

   .. math::

      W'^{(1)} = 3.0 \times 3.0 = 9.0, \quad b'^{(1)} = 0.5 - (1.0 \times 3.0) = -2.5

3. **Gộp BN cho nhánh Identity**:
   Hệ số tỉ lệ: :math:`\frac{\gamma^{(0)}}{\sigma^{(0)}} = \frac{1.0}{2.0} = 0.5`.

   .. math::

      W'^{(0)} = 0.5 \times 1.0 = 0.5, \quad b'^{(0)} = 0.2 - (0.4 \times 0.5) = 0.0

4. **Đệm không và cộng dồn**:
   Đệm hai giá trị 1x1 vào tâm ma trận :math:`3 \times 3`:

   .. math::

      \text{pad}(W'^{(1)}) = \begin{bmatrix} 0.0 & 0.0 & 0.0 \\ 0.0 & 9.0 & 0.0 \\ 0.0 & 0.0 & 0.0 \end{bmatrix}, \quad
      \text{pad}(W'^{(0)}) = \begin{bmatrix} 0.0 & 0.0 & 0.0 \\ 0.0 & 0.5 & 0.0 \\ 0.0 & 0.0 & 0.0 \end{bmatrix}

   Cộng tổng trọng số và bias:

   .. math::

      W_{\text{final}} = \begin{bmatrix} 2.0 & 0.0 & -2.0 \\ 0.0 & 4.0 + 9.0 + 0.5 & 0.0 \\ 2.0 & 2.0 & 0.0 \end{bmatrix} = \begin{bmatrix} 2.0 & 0.0 & -2.0 \\ 0.0 & 13.5 & 0.0 \\ 2.0 & 2.0 & 0.0 \end{bmatrix}

      b_{\text{final}} = b'^{(3)} + b'^{(1)} + b'^{(0)} = 0.0 + (-2.5) + 0.0 = -2.5

3. MobileOne (Depthwise + Pointwise re-param)
=============================================

Mặc dù RepVGG gộp được thành tích chập 3x3 đơn nhánh, các lớp tích chập chuẩn (standard convolution) vẫn tiêu tốn lượng tính toán lớn trên thiết bị di động có công suất thấp. Kiến trúc MobileOne kết hợp ý tưởng tái tham số hóa cấu trúc với tích chập tách kênh (depthwise separable convolution) theo phong cách MobileNet-V1 [T2 MOBONE tr.4].

Khối cơ bản của MobileOne chia thành hai giai đoạn liên tiếp [T2 MOBONE tr.4, 5]:

1. **Khối Depthwise (DWBlock)**: Thực hiện tích chập theo từng kênh độc lập. Lúc huấn luyện, khối này chứa :math:`k` nhánh DWConv 3x3 kèm BN, một nhánh DWConv 1x1 kèm BN và một nhánh identity kèm BN.
2. **Khối Pointwise (PWBlock)**: Thực hiện tích chập 1x1 liên kênh. Lúc huấn luyện, khối này gồm :math:`k` nhánh Conv 1x1 kèm BN và một nhánh identity kèm BN (khi số kênh vào bằng số kênh ra).

Tham số :math:`k` được gọi là hệ số over-parameterization (trivial over-parameterization factor), thường được chọn từ 1 đến 5 tùy theo quy mô biến thể mô hình (S0 đến S4) [T2 MOBONE tr.4, 5]:

   "MobileOne blocks are similar to blocks introduced in" [T2 MOBONE tr.4]

   "For skip connection the batchnorm is folded to a convolutional layer with identity 1x1 kernel" [T2 MOBONE tr.4]

.. figure:: ../../../_assets/img/npu/08_model_design_for_npu/mobileone_p5_fig3.png
   :align: center
   :alt: Khối MobileOne lúc train và lúc suy luận

   Hình 8.1b. Khối MobileOne lúc train (nhiều nhánh có thể reparameterize, k khối) và lúc suy luận (3x3d Conv + BN + Act rồi 1x1 Conv + BN + Act, khối được thiết kế cho conv tách thành depthwise và pointwise, MOBONE tr.4). Nguồn: [T2 MOBONE tr.5, Figure 3]

Khi chuyển sang chế độ suy luận, toàn bộ :math:`k+2` nhánh trong khối Depthwise được gộp thành duy nhất một lớp DWConv 3x3, và :math:`k+1` nhánh trong khối Pointwise được gộp thành một lớp PWConv 1x1. Mô hình hoàn toàn không còn nhánh rẽ lúc suy luận, loại bỏ triệt để chi phí truy cập bộ nhớ phụ trợ [T2 MOBONE tr.4].

.. list-table:: So sánh hiệu năng suy luận trên các nền tảng phần cứng khác nhau
   :header-rows: 1
   :widths: 18 20 20 22 20

   * - Mô hình
     - Top-1 (%)
     - iPhone 12 (ms)
     - GPU 2080Ti (ms)
     - CPU Xeon (ms)
   * - RepVGG-B0
     - 75.14
     - 1.82
     - 1.45
     - 55.97
   * - EfficientNet-B0
     - 77.10
     - 1.72
     - 1.35
     - 28.71
   * - MobileOne-S1
     - 75.90
     - 0.89
     - 0.66
     - 13.04

Theo số đo từ MobileOne Table 9 [T2 MOBONE tr.7], thứ hạng tốc độ giữa các mô hình phụ thuộc chặt chẽ vào thiết bị đo. Trên GPU NVIDIA 1080Ti (với batch 128), RepVGG-B0 nhanh hơn đáng kể so với EfficientNet-B0 (1817 so với 829 mẫu/giây) [T2 REPVGG tr.7]. Tuy nhiên, trên CPU Xeon, GPU 2080Ti và thiết bị di động iPhone 12, RepVGG-B0 lại chậm hơn EfficientNet-B0 và chậm hơn MobileOne-S1 gấp đôi [T2 MOBONE tr.7]. Không có công bố thực nghiệm nào đo RepVGG hay MobileOne trên NPU Rockchip RK3588 (unknown).

4. QARepVGG
===========

4.1 Vấn đề khi lượng tử hóa RepVGG (phương sai activation, sụt mAP/top-1 INT8)
------------------------------------------------------------------------------

Mặc dù RepVGG đạt tốc độ suy luận FP32 rất ấn tượng trên GPU nhờ topo đơn nhánh, mô hình này lại gặp thất bại nghiêm trọng khi lượng tử hóa hậu huấn luyện (Post-Training Quantization - PTQ) sang INT8 [T2 QAREP tr.1]:

   "Nonetheless, its quantization performance is usually too poor to deploy (more than 20% top-1 accuracy drop on ImageNet) when INT8 inference is desired." [T2 QAREP tr.1]

Nghiên cứu của Chu và cộng sự [T2 QAREP tr.1, 5, 6] chỉ ra rằng sự sụt giảm độ chính xác của RepVGG dao động rất lớn tùy biến thể: RepVGG-A0 sụt 20.2 điểm phần trăm (từ 72.4% xuống 52.2%), RepVGG-B0 sụt 34.9 điểm (từ 75.1% xuống 40.2%), và RepVGG-B1g4 sụt tới 77.05 điểm (từ 77.6% xuống 0.55%). Trên mô hình phát hiện đối tượng YOLOv6s sử dụng RepBlock, độ chính xác sụt giảm 7.4% mAP qua PTQ [T2 QAREP tr.7]:

   "Noticeably, YOLOv6s-RepVGG suffers a huge quantization degradation for about 7.4% mAP via PTQ." [T2 QAREP tr.7]

Nguyên nhân gốc rễ bắt nguồn từ sự vi phạm hai điều kiện cơ bản của lượng tử hóa [T2 QAREP tr.3]:

1. **Điều kiện C1 (Phân phối trọng số thân thiện lượng tử)**: Trọng số gộp của các tầng trung gian có phương sai cực lớn và xuất hiện nhiều giá trị ngoại lai (outliers), đặc biệt tại các tầng 5 và tầng 6 [T2 QAREP tr.5].
2. **Điều kiện C2 (Phân phối activation thân thiện lượng tử)**: Trong khối RepVGG, mỗi nhánh trong ba nhánh đều sở hữu một lớp Batch Normalization độc lập đặt trước phép cộng. Khi cộng ba phân phối chuẩn hóa có kỳ vọng khác nhau, phương sai của tensor activation bị khuếch đại mạnh mẽ ở đầu ra [T2 QAREP tr.5].

.. figure:: ../../../_assets/img/npu/03_quantization_theory/qarep_fig4.png
   :align: center
   :alt: Phương sai activation lớn của RepVGG-A0

   Hình 3.8b. Phương sai activation lớn của RepVGG-A0 (S2): đầu ra của từng nhánh tại lớp 4. Nguồn: [T2 QAREP tr.5, Figure 4]

4.2 Cách khắc phục của QARepVGG (tái cấu trúc BN sau phép cộng)
---------------------------------------------------------------

Để giải quyết triệt để hiện tượng sụt giảm độ chính xác INT8 mà vẫn duy trì ưu thế gộp nhánh lúc suy luận, kiến trúc QARepVGG (Quantization-Aware RepVGG) đề xuất tái cấu trúc vị trí của các lớp Batch Normalization thông qua bốn điều chỉnh (M1 đến M4) [T2 QAREP tr.5]:

- **M1 (Chuẩn hóa hàm mất mát)**: Thay thế hàm phạt custom L2 bằng hàm chuẩn hóa trọng số L2 thông thường, giúp kiểm soát phương sai trọng số ban đầu [T2 QAREP tr.5].
- **M2 (Bỏ BN ở nhánh Identity)**: Loại bỏ lớp BN trên đường truyền identity [T2 QAREP tr.5].
- **M3 (Bỏ BN ở nhánh Conv 1x1)**: Loại bỏ lớp BN sau lớp tích chập 1x1 [T2 QAREP tr.5].
- **M4 (Bổ sung Post-BN)**: Đặt một lớp Batch Normalization duy nhất ngay sau phép cộng của ba nhánh [T2 QAREP tr.5]:

   "we remove BN from the identity and 1×1 branch plus appending an extra BN after the addition of three branches." [T2 QAREP tr.5]

Việc bổ sung Post-BN đóng vai trò chuẩn hóa toàn bộ tensor đầu ra sau phép cộng, triệt tiêu hiện tượng dịch chuyển hiệp biến (covariate shift) và giữ cho phương sai activation luôn nằm trong dải phân bố hẹp, thân thiện với các thang chia lượng tử hóa INT8 đối xứng [T2 QAREP tr.5, 6].

.. figure:: ../../../_assets/img/npu/03_quantization_theory/qarep_fig1.png
   :align: center
   :alt: Reparameterization của khối RepVGG và QARepVGG

   Hình 3.8a. Reparameterization của khối RepVGG và QARepVGG, cả hai đều gộp được thành một Conv 3x3. QARepVGG bỏ BN khỏi nhánh identity và 1x1, thêm BN sau phép cộng. Nguồn: [T2 QAREP tr.1, Figure 1]

Khi chuyển sang chế độ triển khai (deploy mode), ba nhánh không có BN riêng rẽ được cộng trực tiếp thành một Conv 3x3, sau đó lớp Post-BN đứng sau được gộp vào chính lớp Conv 3x3 đó theo công thức gộp BN tiêu chuẩn. Do đó, mô hình triển khai của QARepVGG hoàn toàn tương đồng về cấu trúc và tốc độ suy luận với RepVGG gốc [T2 QAREP tr.1, 5].

.. list-table:: So sánh độ chính xác FP32 và INT8 (PTQ) giữa RepVGG và QARepVGG trên ImageNet
   :header-rows: 1
   :widths: 30 20 25 25

   * - Mô hình
     - Độ chính xác FP32 (%)
     - Độ chính xác INT8 (%)
     - Độ sụt giảm INT8 (%)
   * - RepVGG-A0
     - 72.4
     - 52.2
     - -20.2
   * - QARepVGG-A0
     - 72.2
     - 70.4
     - -1.8
   * - RepVGG-B0
     - 75.1
     - 40.2
     - -34.9
   * - QARepVGG-B0
     - 74.8
     - 72.9
     - -1.9
   * - RepVGG-B2
     - 78.8
     - 51.3
     - -27.5
   * - QARepVGG-B2
     - 79.0
     - 77.7
     - -1.3

Kết quả từ Bảng 5 của QAREP [T2 QAREP tr.6] khẳng định QARepVGG giải quyết triệt để vấn đề lượng tử hóa của RepVGG, duy trì độ chính xác INT8 chỉ chênh lệch dưới 2% so với bản gốc FP32 mà không phải trả thêm bất kỳ chi phí trễ nào trên phần cứng thực thi.

Nguồn tham khảo
===============

Các tài liệu nghiên cứu chuẩn (Tier 2) được trích dẫn trong trang này:

.. list-table::
   :header-rows: 1
   :widths: 15 10 60 15

   * - Nhãn
     - Tier
     - Tên tài liệu và đường dẫn
     - Số lần trích
   * - ``REPVGG``
     - T2
     - :download:`repvgg_reparam_2021ding.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/repvgg_reparam_2021ding.pdf>`
     - 9
   * - ``MOBONE``
     - T2
     - :download:`mobileone_reparam_2023vasu.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/mobileone_reparam_2023vasu.pdf>`
     - 5
   * - ``QAREP``
     - T2
     - :download:`qarepvgg_quant_2024chu.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/qarepvgg_quant_2024chu.pdf>`
     - 9
