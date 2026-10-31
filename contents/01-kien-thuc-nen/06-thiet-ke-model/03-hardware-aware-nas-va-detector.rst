:tocdepth: 1

******************************
Hardware-aware NAS và detector
******************************

.. admonition:: Trang này trả lời

   - Tìm kiếm kiến trúc nơ-ron nhận biết phần cứng (Hardware-aware NAS) sử dụng những chỉ số nào và kết quả có chuyển giao được giữa các NPU không?
   - Các detector hiện đại như YOLOv6 tối ưu hóa cấu trúc tích chập, nhánh rẽ và đầu giải mã như thế nào cho phần cứng?

.. admonition:: Tóm tắt

   - Hardware-aware NAS giải quyết sự lệch pha giữa FLOPs lý thuyết và độ trễ thực tế trên phần cứng: S3NAS sử dụng bộ ước lượng độ trễ xây dựng trên bộ mô phỏng chu kỳ chính xác của NPU MIDAP [T2 S3NAS tr.1, 4], trong khi ActNAS tìm kiếm hàm kích hoạt tối ưu theo từng tầng trên đồ thị YOLO [T2 ACTNAS tr.1, 2].
   - Kết quả tối ưu hóa từ NAS phụ thuộc chặt chẽ vào đặc tính vi kiến trúc của phần cứng đích và có khả năng chuyển giao rất thấp sang các bộ tăng tốc khác [T2 ACTNAS tr.8]. Các công bố học thuật hiện tại chưa có công trình NAS nào nhắm trực tiếp tới NPU Rockchip.
   - YOLOv6 tối ưu hóa cho phần cứng công nghiệp thông qua cấu trúc EfficientRep Backbone dùng khối RepBlock (lúc train) gộp thành RepConv (lúc suy luận), còn với các mô hình lớn hơn, khối CSPStackRep kết hợp kết nối tắt CSP để cân bằng giữa độ chính xác và dung lượng tính toán [T2 Y6 tr.4]. Đồng thời, YOLOv6 loại bỏ Distribution Focal Loss (DFL) ở các mô hình nhỏ để triệt tiêu chi phí hồi quy hộp bao quá mức [T2 Y6 tr.5].
   - Trên RK3588, bài EDGE thấy FLOPs thấp không đồng nghĩa độ trễ thấp: YOLO11n có FLOPs thấp nhất nhưng độ trễ INT8 cao nhất trong ba bản nano [T2 EDGE tr.4, tr.7].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. NAS nhận biết NPU
====================

Trong tối ưu hóa mô hình học sâu, số lượng phép tính dấu phẩy động (FLOPs) hoặc số lượng tham số (Parameters) thường được sử dụng làm thước đo hiệu năng tính toán. Tuy nhiên, trên các bộ xử lý chuyên dụng NPU, độ trễ thực tế không tỷ lệ thuận với FLOPs do chi phí truy cập bộ nhớ (MAC), băng thông truyền dữ liệu giữa DRAM và SRAM nội bộ, cùng mức độ lấp đầy mảng nhân chập (MAC array utilization) đóng vai trò chi phối. Phương pháp tìm kiếm kiến trúc nơ-ron nhận biết phần cứng (Hardware-aware Neural Architecture Search - HW-NAS) đưa độ trễ đo đạc trực tiếp hoặc độ trễ ước lượng từ bộ mô phỏng vào hàm mục tiêu tối ưu nhằm sinh ra kiến trúc khớp với vi cấu trúc phần cứng.

1.1 S3NAS
---------

Công trình S3NAS (Lee và cộng sự, 2020) phát triển một framework tìm kiếm kiến trúc siêu mạng (supernet-based NAS) tối ưu hóa riêng cho bộ xử lý nơ-ron:

   "an analytical latency estimator is devised, based on a cycle-level NPU simulator that runs an entire CNN considering the memory access overhead accurately." [T2 S3NAS tr.1]

Cần lưu ý rằng phần cứng mục tiêu trong nghiên cứu S3NAS là MIDAP - một bộ xử lý NPU giả định được phát triển dưới dạng mô hình ảo chu kỳ chính xác (cycle-accurate simulator) chứ chưa phải chip vật lý thương mại [T2 S3NAS tr.4]:

   "Note that MIDAP has not been implemented as a real hardware chip yet but as a virtual prototype with a cycle-accurate simulator." [T2 S3NAS tr.4]

Để tối ưu hóa cho mảng tính toán của MIDAP, S3NAS áp dụng các ràng buộc kiến trúc vi mô cụ thể nhằm tránh lãng phí chu kỳ xử lý [T2 S3NAS tr.9]:

   "We make the number of filters to be multiples of 16 to maximize the MAC unit utilization on MIDAP." [T2 S3NAS tr.9]

Không gian tìm kiếm siêu mạng của S3NAS cho phép số lượng khối ở từng giai đoạn thay đổi linh hoạt thay vì cố định như các phương pháp One-Shot NAS truyền thống, với các kích thước kernel ứng viên :math:`\{3 \times 3, 5 \times 5, 7 \times 7\}` và hệ số mở rộng kênh :math:`\{3, 4, 6\}` [T2 S3NAS tr.4, 5]. Do số phép nhân trong một lớp DWConv bằng :math:`W \times H \times C \times K^2`, các giai đoạn sâu hơn của mạng thường có độ trễ ngắn hơn nhờ diện tích không gian :math:`H \times W` giảm nhanh hơn tốc độ tăng của số kênh :math:`C` [T2 S3NAS tr.5].

Một phát hiện quan trọng trong S3NAS là sự tương tác giữa loại khối tích chập và phần cứng NPU. Trong khi các khối tích chập tách kênh (Depthwise Separable Convolution - DWConv trong MBConv) giúp giảm mạnh FLOPs lý thuyết, chúng có tỷ lệ tính toán trên bộ nhớ rất thấp (arithmetic intensity thấp). Trên các bộ xử lý như Google Edge TPU, các khối tích chập hợp nhất (Fused Inverted Bottleneck Conv) chạy nhanh hơn đáng kể dù sở hữu nhiều phép tính hơn [T2 S3NAS tr.1]. Ngược lại, trên kiến trúc MIDAP vốn trang bị các đơn vị vector xử lý DWConv hiệu quả, kết quả so sánh ở Bảng 1 [T2 S3NAS tr.5] cho thấy thứ tự ngược lại:

.. list-table:: So sánh hiệu năng các loại khối xây dựng cơ bản trong S3NAS trên bộ mô phỏng MIDAP
   :header-rows: 1
   :widths: 40 30 30

   * - Loại khối xây dựng cơ bản (Building Block)
     - Độ chính xác Top-1 ImageNet (%)
     - Độ trễ ước lượng trên MIDAP (ms)
   * - Fused Inverted Bottleneck Conv
     - 77.34
     - 6.90
   * - MBConv (Depthwise Separable Conv)
     - 77.75
     - 2.05
   * - Combined (Không gian kết hợp cả hai)
     - 76.55
     - 2.20

Số liệu từ Bảng 1 của S3NAS [T2 S3NAS tr.5] chứng minh rằng trên MIDAP, khối MBConv đạt độ trễ 2.05 ms, nhanh hơn gấp 3.3 lần so với khối Fused Conv (6.90 ms) ở cùng mức độ chính xác tương đương. Điều này khẳng định loại khối "tối ưu nhất" hoàn toàn phụ thuộc vào đặc tính phần cứng đích [T2 S3NAS tr.1, 2]:

   "the NPU assumed in this paper can execute depth-wise separable convolution (DWConv), squeeze-and-excitation (SE), and h-swish activation function efficiently" [T2 S3NAS tr.2]

.. figure:: ../../../_assets/img/01-kien-thuc-nen/06-thiet-ke-model/hardware-aware-nas-va-detector/s3nas-fig8-mixconv-implementations.png
   :align: center
   :alt: Hai cách cài đặt cùng một khối MixConv

   Hình 8.3. Hai cách cài đặt cùng một khối MixConv: cùng FLOPS nhưng độ trễ ước lượng khác nhau. Nguồn: [T2 S3NAS tr.6, Figure 8]

Hình 8.3 minh họa rõ ràng hiện tượng này: cùng một khối MixConv với cùng số lượng FLOPs nhưng khi sắp xếp các toán tử con và luồng dữ liệu khác nhau, độ trễ ước lượng trên NPU có sự phân hóa đáng kể do chi phí chuyển kênh và lưu trữ trung gian [T2 S3NAS tr.6].

1.2 ActNAS
----------

Khác với các phương pháp NAS truyền thống can thiệp vào cấu trúc kênh và số tầng, ActNAS tập trung vào bài toán tối ưu hóa hàm kích hoạt phi tuyến theo từng lớp riêng lẻ trên đồ thị YOLO [T2 ACTNAS tr.1, 2]:

   "we generate a search space by systematically replacing each activation function in the reference model with a set of candidate activations: [ReLU, SiLU, Hardswish, ReLU6, and LeakyReLU]." [T2 ACTNAS tr.2]

Thay vì huấn luyện lại toàn bộ mô hình cho từng cấu hình ứng viên trong không gian tìm kiếm rộng lớn, ActNAS sử dụng chỉ số ước lượng không chi phí (Zero-Cost Proxy NWOT) [T2 ACTNAS tr.3]:

   "Figure 3 shows that the NWOT score has a strong correlation with the mAP of fully trained models." [T2 ACTNAS tr.3]

Kết hợp thuật toán tiến hóa với bảng tra độ trễ thực tế trên thiết bị (lấy trung bình 50 lần đo), ActNAS phát hiện quy luật cấu trúc then chốt:

   "None of the ActNAS models utilized SiLU or Hardswish in the first two layers." [T2 ACTNAS tr.7]

Bằng cách áp dụng các biến thể ReLU tại các tầng đầu có kích thước bản đồ đặc trưng lớn và giữ lại SiLU hoặc Hardswish ở các tầng sâu, mô hình ActNAS5n.1 giảm được 58% bộ nhớ trên NPU 1, tăng 22.28% tốc độ so với bản thuần SiLU mà mAP chỉ giảm dưới 1% [T2 ACTNAS tr.7]. Trên mô hình lớn hơn, ActNAS8m.2 đạt bước nhảy vọt [T2 ACTNAS tr.8]:

   "ActNAS8m.2 model is 1.66x faster compared to the SiLU model without significant impact on accuracy of the model." [T2 ACTNAS tr.8]

Tuy nhiên, nghiên cứu ActNAS cũng chỉ ra ranh giới nghiêm ngặt về khả năng tổng quát hóa của các mô hình NAS:

   "We can see that both NPU aware models provide highest speedup on these devices but very low speedup on other devices." [T2 ACTNAS tr.8]

Mô hình được tối ưu hóa cho NPU đích đạt tốc độ cao nhất trên phần cứng đó, nhưng khi chuyển giao sang các NPU của hãng khác thì hệ số tăng tốc suy giảm rõ rệt. Trong các tài liệu chuẩn hiện tại, chưa có công bố nào thực hiện NAS trực tiếp trên vi xử lý Rockchip RK3588.

2. Detector thiết kế theo phần cứng
===================================

Mô hình phát hiện đối tượng YOLOv6 được thiết kế với mục tiêu thu hẹp khoảng cách phần cứng (hardware gap) giữa nghiên cứu học thuật và môi trường phục vụ công nghiệp thực tế [T2 Y6 tr.2]:

   "There is a hardware gap when it comes to real serving environment. Typically, low-power GPUs like Tesla T4 are less costly and provide rather good inference performance." [T2 Y6 tr.2]

Nhóm tác giả nhận định các lớp tích chập chuẩn kích thước :math:`3 \times 3` sở hữu mật độ tính toán cao và được hỗ trợ tối đa bởi các thư viện vi mã trên phần cứng [T2 Y6 tr.3]:

   "Typically a 3×3 convolution is highly optimized on mainstream GPUs and CPUs and it enjoys higher computational density." [T2 Y6 tr.3]

.. figure:: ../../../_assets/img/01-kien-thuc-nen/06-thiet-ke-model/hardware-aware-nas-va-detector/yolov6-fig3-repblock-repconv-cspstackrep.png
   :align: center
   :alt: YOLOv6 RepBlock lúc train, RepConv lúc suy luận và CSPStackRep Block

   Hình 8.4a. YOLOv6: (a) RepBlock lúc train, (b) RepConv lúc suy luận, (c) CSPStackRep Block. Nguồn: [T2 Y6 tr.4, Figure 3]

Kiến trúc YOLOv6 đề xuất ba cải tiến cấu trúc then chốt hướng tới phần cứng:

1. **Khối RepBlock và RepConv**:
   - Ở các mô hình quy mô nhỏ (YOLOv6-N, YOLOv6-T, YOLOv6-S), mạng sử dụng cấu trúc đường dẫn đơn (plain single-path).
   - Lúc huấn luyện, khối RepBlock duy trì các nhánh song song :math:`3 \times 3`, :math:`1 \times 1` và identity kèm BN (Hình 8.4a-a).
   - Lúc suy luận, khối được hợp nhất hoàn toàn thành RepConv chỉ gồm một lớp Conv 3x3 kết hợp với ReLU (Hình 8.4a-b), tối ưu hóa bộ nhớ đệm và triệt tiêu chi phí phân mảnh toán tử [T2 Y6 tr.3, 4].

2. **Khối CSPStackRep cho mô hình dung lượng lớn**:
   - Khi mở rộng quy mô mô hình (YOLOv6-M, YOLOv6-L), cấu trúc mạng đơn thuần khiến số lượng tham số và phép tính bùng nổ theo cấp số mũ [T2 Y6 tr.4].
   - Để kiểm soát chi phí tính toán mà vẫn đảm bảo độ chính xác cao, YOLOv6 giới thiệu khối CSPStackRep (Hình 8.4a-c). Khối này tích hợp kết nối tắt phân tách Cross Stage Partial (CSP), bao gồm ba lớp tích chập :math:`1 \times 1` và một chuỗi các sub-block (mỗi sub-block gồm hai khối RepVGG/RepConv kèm kết nối cộng dư) [T2 Y6 tr.4].

3. **Mạng cổ Rep-PAN và phân bổ gán nhãn động**:
   - Cấu trúc mạng cổ (Neck) áp dụng thiết kế Rep-PAN dựa trên PANet, nhưng thay thế các khối tích chập chuẩn bằng RepBlocks (hoặc CSPStackRep ở bản lớn) kết hợp với các phép nối kênh (concatenation) và up-sampling [T2 Y6 tr.3].
   - Trong quá trình huấn luyện, nhóm tác giả áp dụng cơ chế gán nhãn động Task Alignment Learning (TAL) kết hợp VariFocal Loss cho phân loại và SIoU/GIoU cho hồi quy, giúp ổn định quá trình hội tụ mà không làm thay đổi cấu trúc đồ thị lúc suy luận [T2 Y6 tr.3, 5].

4. **Cắt giảm chi phí ở đầu giải mã (Efficient Decoupled Head & DFL)**:
   - Các đầu giải mã tách nhánh truyền thống (như trong FCOS hay YOLOX) sử dụng hai lớp Conv 3x3 trên mỗi nhánh phân loại và định vị. YOLOv6 tinh gọn cấu trúc bằng cách chỉ giữ lại duy nhất một lớp Conv 3x3 trung gian theo chiến lược hybrid-channel, giúp giảm đáng kể chi phí tính toán [T2 Y6 tr.4].
   - Đặc biệt, đối với hàm mất mát phân phối hộp bao Distribution Focal Loss (DFL), YOLOv6 chỉ ra sự lãng phí tài nguyên phần cứng nghiêm trọng [T2 Y6 tr.5]:

   "DFL usually outputs 17× more regression values than general box regression, leading to a substantial overhead." [T2 Y6 tr.5]

   Việc xuất ra số lượng giá trị hồi quy gấp 17 lần khiến cho chi phí xử lý I/O và độ trễ tăng vọt, triệt tiêu lợi thế thời gian thực trên các mô hình nhỏ. Vì vậy, DFL bị loại bỏ hoàn toàn trên YOLOv6-N và YOLOv6-S [T2 Y6 tr.5].

Trong các thử nghiệm triệt tiêu trên GPU Tesla T4 [T2 Y6 Table 4, tr.9], RepConv + ReLU đạt 1233 FPS (35.2% AP) so với 971 FPS của RepConv + SiLU, khẳng định ưu thế của sự kết hợp giữa tái tham số hóa và toán tử thân thiện phần cứng [T2 Y6 tr.8]:

   "ReLU has a greater speed advantage because of its fusion into convolution." [T2 Y6 tr.8]

   "We suggest users adopt RepConv with ReLU in latency-sensitive applications." [T2 Y6 tr.8]

Liên hệ RK3588: bài EDGE đo trên RK3588 thấy YOLO11n có FLOPs thấp nhất nhưng độ trễ INT8 cao nhất trong ba bản nano [T2 EDGE tr.4, tr.7]. Số đo YOLO trên RK3588 trong các bài báo nằm ở :doc:`Tiêu chí thân thiện NPU </contents/02-nen-tang-rk3588/05-yolo-tren-rk3588/03-tieu-chi-than-thien-npu>` mục 2.

Nguồn
=====

Các tài liệu nghiên cứu chuẩn (Tier 2) được trích dẫn trong trang này:

.. list-table::
   :header-rows: 1
   :widths: 15 10 60 15

   * - Nhãn
     - Tier
     - Tên tài liệu và đường dẫn
     - Số lần trích
   * - ``S3NAS``
     - T2
     - :download:`s3nas_npu_aware_2020lee.pdf <../../../_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf>`
     - 15
   * - ``ACTNAS``
     - T2
     - :download:`actnas_yolo_2025sah.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/actnas_yolo_2025sah.pdf>`
     - 11
   * - ``Y6``
     - T2
     - :download:`yolov6_hwfriendly_2022li.pdf <../../../_assets/pdf/papers/08_npu_friendly_arch/yolov6_hwfriendly_2022li.pdf>`
     - 20
   * - ``EDGE``
     - T2
     - :download:`edgesoc_benchmark_2026kong.pdf <../../../_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf>`
     - 2
