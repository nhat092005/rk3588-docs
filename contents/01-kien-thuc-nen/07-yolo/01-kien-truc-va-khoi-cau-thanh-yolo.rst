:tocdepth: 2

************************************
Kiến trúc và các khối cấu thành YOLO
************************************

Trang này phân tích và đối sánh chi tiết kiến trúc giữa hai thế hệ mạng phát hiện vật thể tiêu biểu: YOLOv8 (phiên bản nano YOLOv8n) và YOLO26 (phiên bản nano YOLO26n). Trọng tâm trình bày đặt vào các khối trích xuất đặc trưng đa tầng, khối kết tập ngữ cảnh không gian, cơ chế chú ý cục bộ, và cấu trúc đầu dự đoán giải mã tọa độ hộp. Để khảo sát chi tiết đường triển khai và tối ưu hóa trên phần cứng Rockchip, độc giả tham khảo thêm tại :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`.

.. contents:: Mục lục trang
   :local:
   :depth: 2

So sánh tổng quan YOLOv8n và YOLO26n
====================================

Dòng mô hình YOLO (You Only Look Once) đã trải qua nhiều bước chuyển dịch kiến trúc quan trọng nhằm cân bằng giữa độ chính xác và thông lượng tính toán thời gian thực:

- YOLOv8 (phát hành năm 2023 bởi Ultralytics) thiết lập chuẩn mực mới cho dòng mạng phát hiện anchor-free: "YOLOv8 (2023) improves convergence and small-object fidelity via a decoupled head and anchor-free design." [T2 UEVOL tr.12]. Mạng sử dụng xương sống (backbone) dựa trên khối C2f và module Spatial Pyramid Pooling - Fast (SPPF) nhằm giảm số lượng tham số nhưng vẫn duy trì trường tiếp nhận phong phú.
- YOLO26 (phát hành năm 2026 bởi Ultralytics) tái thiết kế toàn diện đường ống suy luận nhằm thu hẹp khoảng cách triển khai trên phần cứng biên (Export Gap). Kiến trúc chuyển đổi từ khối C2f sang C3k2, bổ sung cơ chế chú ý cục bộ (C2PSA), và loại bỏ hoàn toàn module phân phối hộp DFL để đạt thông lượng suy luận ổn định [T2 Y26A tr.5].

Bảng so sánh kiến trúc, tham số (params), FLOPs, độ trễ lý thuyết
-----------------------------------------------------------------

Bảng dưới đây tổng hợp các đặc tính cấu hình, khối lượng tính toán và độ trễ công bố giữa hai mô hình nano trên tập dữ liệu COCO (kích thước đầu vào chuẩn 640x640 pixel):

.. list-table:: So sánh đặc tính kiến trúc và hiệu năng lý thuyết giữa YOLOv8n và YOLO26n
   :header-rows: 1
   :widths: 22 36 36 16

   * - Đặc tính
     - YOLOv8n
     - YOLO26n
     - Nguồn
   * - Hệ số co giãn (scale n)
     - ``[depth=0.33, width=0.25, max_channels=1024]``
     - ``[depth=0.50, width=0.25, max_channels=1024]``
     - [T1 yolov8.yaml:11], [T1 yolo26.yaml:13]
   * - Số tầng (layers)
     - 129 tầng
     - 260 tầng
     - [T1 yolov8.yaml:11], [T1 yolo26.yaml:13]
   * - Khối backbone chủ đạo
     - ``Conv``, ``C2f``, ``SPPF``
     - ``Conv``, ``C3k2``, ``SPPF`` (shortcut=True), ``C2PSA``
     - [T1 yolov8.yaml:20-29], [T1 yolo26.yaml:22-32]
   * - Khối neck chủ đạo
     - ``C2f``, ``Upsample``, ``Concat``
     - ``C3k2`` (tích hợp khối chú ý ở P5), ``Upsample``, ``Concat``
     - [T1 yolov8.yaml:33-47], [T1 yolo26.yaml:36-50]
   * - Cấu trúc đầu dự đoán
     - Decoupled Head, ``reg_max=16`` (có DFL), cần NMS
     - Decoupled Head, ``reg_max=1`` (bỏ DFL), hỗ trợ NMS-free
     - [T1 yolo26.yaml:9-10], [T2 Y26A tr.8]
   * - Tham số (Params, COCO)
     - 3.2 M (đã fuse), 3,157,200 (chưa fuse)
     - 2.4 M (đã fuse), 2,572,280 (chưa fuse)
     - [T1 yolov8.yaml:11], [T2 Y26A tr.17, tr.22]
   * - Khối lượng tính toán (FLOPs)
     - 8.7 B (fused inference) / 8.9 GFLOPs (chưa fuse)
     - 5.4 B (fused inference) / 6.1 GFLOPs (chưa fuse)
     - [T1 yolo26.yaml:13], [T2 YOFF tr.14], [T2 Y26A tr.17]
   * - Độ trễ GPU (T4 TensorRT10)
     - < 2.0 ms (FP16, chưa gồm thời gian NMS)
     - 1.7 ms (FP16, đường suy luận end-to-end)
     - [T2 UEVOL tr.14], [T2 YOFF tr.14]
   * - Độ trễ CPU (Intel Xeon @ 2.0GHz)
     - ~80.4 ms (CPU ONNX)
     - 38.9 ms (CPU ONNX)
     - [T2 UEVOL tr.12], [T2 YOFF tr.14]
   * - Độ chính xác mAP 50-95 (COCO val)
     - 37.3% (hoặc 36.5% tùy bản tinh chỉnh)
     - 40.9% (nhánh NMS) / 40.1% (nhánh end-to-end một-một)
     - [T2 UEVOL tr.12], [T2 YOFF tr.14]

Quy ước về số tham số và FLOPs:
  - Các bài báo công bố chính thức nhấn mạnh: "Parameter counts and FLOPs denote the fused inference architecture, which merges Conv/BatchNorm layers and removes the auxiliary one-to-many detection head used during training." [T2 Y26A tr.17].
  - Khi chưa fuse, mô hình YOLO26n giữ nguyên cả hai nhánh đầu ra (nhánh một-nhiều và một-một), dẫn tới tổng tham số là 2,572,280 và FLOPs đo theo công cụ profile thop ở độ phân giải 32x32 ngoại suy là 6.1 GFLOPs [T1 yolo26.yaml:13].
  - Trong triển khai thực tế sau khi gộp lớp và loại bỏ nhánh phụ trợ, mô hình chỉ giữ lại 2.4 triệu tham số và tiêu thụ 5.4 tỷ FLOPs [T2 YOFF tr.14]. Ngược lại, YOLOv8n sau fuse đạt 3.2 triệu tham số và tiêu thụ 8.7 tỷ FLOPs [T2 Y26A tr.17, tr.22].
  - Về sai số giữa chú thích trong yaml và phép đo thực: công cụ ``thop`` thường đo ở ảnh nhỏ :math:`32 \times 32` rồi nhân tỷ lệ diện tích :math:`(640/32)^2 = 400`. Tuy nhiên, vì cơ chế Attention có độ phức tạp bậc hai theo diện tích ảnh, Ultralytics quy định tắt cơ chế ước lượng affine này đối với các mô hình chứa module chú ý [T1 ultralytics/utils/torch_utils.py]. Do đó, phép tính trực tiếp trên ảnh 640x640 thật cho ra 5.480 GFLOPs (làm tròn thành 5.5 B hoặc 5.4 B tùy quy ước làm tròn).

Khối trích xuất đặc trưng đa tầng: C2f và C3k2
==============================================

Cấu trúc Cross Stage Partial (CSP) là nền tảng giúp mạng phân tách dòng truyền đặc trưng thành hai nhánh: một nhánh đi qua các khối biến đổi phi tuyến sâu, nhánh còn lại đi tắt và hội tụ ở cuối module nhằm duy trì gradient ổn định.

Khối C2f trong YOLOv8n:
  - Đầu vào tensor có số kênh :math:`c_{in}` đi qua lớp tích chập :math:`1 \times 1` (`cv1`) để tăng số kênh lên :math:`2 \times c_{out}`.
  - Tensor đầu ra được chia đôi theo trục kênh thành hai phần bằng nhau :math:`y_0` và :math:`y_1` (mỗi phần có :math:`c_{out}` kênh) thông qua phép tách tensor [T1 ultralytics/nn/modules/block.py].
  - Nhánh :math:`y_0` đóng vai trò đường dẫn tắt (bypass). Nhánh :math:`y_1` được dẫn tuần tự qua chuỗi :math:`n` khối ``Bottleneck``. Mỗi khối ``Bottleneck`` gồm 2 lớp tích chập :math:`3 \times 3` liên tiếp với hàm kích hoạt SiLU và chuẩn hóa BatchNorm.
  - Các đầu ra trung gian của từng khối bottleneck được thu thập cùng :math:`y_0` và :math:`y_1`, sau đó ghép nối (concatenate) lại dọc trục kênh và đưa qua lớp tích chập :math:`1 \times 1` (`cv2`) để tái lập số kênh chuẩn :math:`c_{out}`.
  - Trong YOLOv8n, số khối lặp lại được chia tỷ lệ qua hệ số độ sâu 0.33, tạo ra cấu hình 1 khối bottleneck ở layer 2, 2 khối ở layer 4 và 6, và 1 khối ở layer 8 [T1 yolov8.yaml:20-29].

Khối C3k2 trong YOLO26n:
  - C3k2 kế thừa cấu trúc CSP của C2f nhưng tăng tính linh hoạt bằng cách hỗ trợ nhiều biến thể khối con thông qua tham số khởi tạo [T1 ultralytics/nn/modules/block.py].
  - Cấu trúc module con ``m`` trong C3k2 được điều khiển qua ba cờ: ``c3k``, ``attn``, và tỷ lệ mở rộng kênh ``e`` [T1 ultralytics/nn/modules/block.py].
  - Khi tham số ``c3k=False`` (được áp dụng tại các tầng nông layer 2 và 4 của YOLO26n), module sử dụng khối ``Bottleneck`` nhưng áp dụng tỉ lệ thu hẹp kênh :math:`e=0.25` [T1 yolo26.yaml:24,26]. Điều này giúp giảm số kênh tính toán ẩn bên trong bottleneck từ 16 xuống còn 8 kênh, tiết kiệm đáng kể chi phí bộ nhớ đệm và băng thông truyền dữ liệu.
  - Khi tham số ``c3k=True`` (tại các tầng sâu layer 6, 8, 13, 16, 19), module tích hợp khối con ``C3k`` gồm 3 lớp tích chập :math:`1 \times 1` và 2 khối bottleneck :math:`3 \times 3`, tăng cường khả năng trích xuất phi tuyến mà không làm bùng nổ tham số [T1 yolo26.yaml:28-50].
  - Khi tham số ``attn=True`` (tại layer 22 ở đầu ra P5), khối con được thay bằng chuỗi tuần tự gồm ``Bottleneck`` và ``PSABlock``, cho phép đưa cơ chế tự chú ý vào tầng ngữ cảnh cao nhất của neck mà không cần thay đổi giao diện kết nối tổng thể của khối CSP.

Khối kết tập ngữ cảnh không gian: SPPF
======================================

Khối Spatial Pyramid Pooling - Fast (SPPF) có nhiệm vụ tổng hợp thông tin ngữ cảnh đa kích thước vùng tiếp nhận (receptive field) trước khi chuyển đặc trưng từ backbone sang cổ mạng (neck):

- Nguyên lý hoạt động:
  - Tensor từ tầng sâu của backbone được chiếu qua một lớp tích chập :math:`1 \times 1` nhằm giảm một nửa số kênh dẫn.
  - Dữ liệu sau đó đi qua 3 phép gộp cực đại (MaxPooling) liên tiếp với kích thước vùng :math:`5 \times 5`, bước nhảy (stride) 1 và đệm (padding) 2 [T1 ultralytics/nn/modules/block.py].
  - Việc áp dụng liên tiếp các bộ lọc :math:`5 \times 5` tương đương về mặt toán học với việc trích xuất vùng tiếp nhận kích thước :math:`5 \times 5`, :math:`9 \times 9` và :math:`13 \times 13`, nhưng chi phí tính toán thấp hơn nhiều so với việc chạy song song 3 bộ lọc kích thước lớn.
  - Đầu ra của 3 tầng pooling cùng với nhánh đặc trưng ban đầu được ghép nối lại (tổng cộng 4 nhánh) và đưa qua lớp tích chập :math:`1 \times 1` để đưa số kênh về kích thước thiết kế.

- Khác biệt giữa YOLOv8n và YOLO26n trong SPPF:
  - Trong YOLOv8n: cấu hình là ``SPPF([1024, 5])`` không kích hoạt đường kết nối tắt residual [T1 yolov8.yaml:29].
  - Trong YOLO26n: cấu hình là ``SPPF([1024, 5, 3, True])`` với cờ ``shortcut=True`` [T1 yolo26.yaml:31]. Khi số kênh đầu vào bằng số kênh đầu ra (:math:`c_1 == c_2`), khối tự động cộng thêm tensor đầu vào vào tensor sau tích chập: :math:`x = x + \text{cv2}(\text{cat}(\dots))`.
  - Phép cộng shortcut này giúp bảo tồn chi tiết biên không gian và cải thiện dòng truyền đạo hàm ngược qua tầng sâu nhất của backbone, hạn chế hiện tượng suy giảm tín hiệu gradient khi truyền qua các toán tử pooling liên tiếp.

Khối chú ý cục bộ: C2PSA, PSABlock, Self-Attention (YOLO26)
===========================================================

Một trong những cải tiến kiến trúc đáng chú ý nhất của YOLO26 là việc tích hợp có chọn lọc cơ chế tự chú ý (Self-Attention) vào mạng tích chập nhằm giải quyết các tình huống đối tượng bị che khuất hoặc có biến dạng phức tạp:

- Vị trí bố trí cơ chế chú ý:
  - YOLOv8n hoàn toàn không sử dụng lớp chú ý nào trong suốt mạng.
  - YOLO26n đưa cơ chế chú ý vào đúng hai vị trí chiến lược trên lưới đặc trưng P5: khối C2PSA tại layer 10 (cuối backbone) và khối C3k2 có cờ chú ý tại layer 22 (cuối neck) [T1 yolo26.yaml:32,50].
  - Tác giả Jocher 2026 giải thích lý do thiết kế: "We further apply a light backbone/neck refinement by inserting one additional attention layer in the detection neck, which improves accuracy while keeping latency essentially unchanged." [T2 YOFF tr.11].

- Cấu tạo chi tiết của C2PSA và PSABlock:
  - Khối C2PSA (Cross Stage Partial with Pointwise Self-Attention): Tương tự cơ chế phân tách luồng CSP, đầu vào qua lớp tích chập :math:`1 \times 1` được chia làm hai nửa. Một nửa đi thẳng, nửa còn lại đi qua khối ``PSABlock``, sau đó ghép nối lại và chiếu qua tích chập :math:`1 \times 1` [T1 ultralytics/nn/modules/block.py]. Số đầu chú ý (attention heads) được tính động theo công thức :math:`\max(c // 64, 1)`.
  - Khối PSABlock: Gồm hai bước biến đổi liên tiếp có đường tắt residual: :math:`x = x + \text{attn}(x)` tiếp theo là :math:`x = x + \text{ffn}(x)`. Mạng truyền thẳng (FFN) được cấu tạo từ hai lớp tích chập :math:`1 \times 1`.
  - Module Attention: Chiếu không gian đặc trưng thành các vector truy vấn, khóa và giá trị :math:`(Q, K, V)` bằng tích chập :math:`1 \times 1`. Ma trận tương quan chú ý được tính qua:

    .. math::

       \text{Attn}(Q, K) = \text{Softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right)

    Đầu ra giá trị sau đó được cộng thêm một nhánh mã hóa vị trí (Positional Encoding - PE) triển khai bằng phép tích chập Depthwise Conv :math:`3 \times 3` (:math:`g=dim`) [T1 ultralytics/nn/modules/block.py].

- Hiệu quả tính toán:
  - Ở độ phân giải đầu vào chuẩn 640x640, tầng P5 có tỷ lệ thu nhỏ 32 lần, cho kích thước lưới không gian là :math:`20 \times 20`, tương ứng chuỗi chỉ có 400 token.
  - Do chuỗi token ngắn, chi phí tính toán ma trận ma sát :math:`O(N^2)` của tự chú ý tại đây chỉ tiêu tốn phần nhỏ năng lực tính toán nhưng mang lại lợi thế định vị ngữ cảnh toàn cục vượt trội.
  - Khi xuất khẩu sang đồ thị ONNX, hai khối chú ý này tạo ra đúng 4 toán tử ``MatMul`` và 2 toán tử ``Softmax``, hoàn toàn không gây tắc nghẽn thông lượng tổng thể.

Đầu dự đoán (Detect Head)
=========================

Đầu dự đoán chịu trách nhiệm chuyển đổi các bản đồ đặc trưng đa tỷ lệ từ neck (P3, P4, P5) thành danh sách hộp giới hạn và xác suất nhãn lớp.

Phân phối hộp DFL vs Đầu một-một (One-to-one Head)
--------------------------------------------------

- Hồi quy phân phối DFL (Distribution Focal Loss) trong YOLOv8n:
  - YOLOv8 áp dụng phương pháp hồi quy gián tiếp thông qua phân phối xác suất rời rạc trên 16 bin tọa độ cho mỗi cạnh hộp [T2 UEVOL tr.10].
  - Đầu ra của nhánh hộp có kích thước :math:`4 \times 16 = 64` kênh. Để trích xuất tọa độ thực tế, mô hình phải thực hiện biến đổi hàm mũ qua phép tính Softmax trên từng tập 16 bin, sau đó nhân vô hướng với vector chỉ số :math:`[0, 1, \dots, 15]` [T2 Y26A tr.8].
  - Rào cản phần cứng: Việc tính toán liên tục các hàm Softmax và phép chia số thực trên 8,400 điểm anchor (ảnh 640x640) tạo thành điểm nghẽn nghiêm trọng khi chạy trên các bộ xử lý tăng tốc chuyên dụng: "On specialized edge hardware (NPUs and DSPs), these Softmax layers are notoriously difficult to quantize and often become the primary latency bottleneck [30]." [T2 Y26A tr.8].

- Công thức toán học của DFL so với Hồi quy trực tiếp:
  - Trong cơ chế DFL, tọa độ :math:`\hat{y}` được tích phân rời rạc từ phân phối xác suất:

    .. math::

       \hat{y}_{DFL} = \sum_{i=0}^{n} i \cdot \text{Softmax}(w_i) = \sum_{i=0}^{n} i \cdot \frac{e^{w_i}}{\sum_{j=0}^{n} e^{w_j}}

    Đòi hỏi bộ tăng tốc phần cứng phải hỗ trợ hàm mũ phi tuyến và phép chia động cho từng tọa độ hộp [T2 Y26A tr.8].

  - YOLO26 bãi bỏ hoàn toàn module phân phối DFL: "One of the most significant architectural simplifications in YOLO26 is the removal of the Distribution Focal Loss (DFL) module" [T2 Y26B tr.6]. "YOLO26 reverts to a Direct Regression Strategy, removing this module entirely (see Fig. 4)." [T2 Y26A tr.8].
  - Trong YOLO26, phép giải mã được chuyển hóa thành ánh xạ hồi quy trực tiếp đơn giản:

    .. math::

       \hat{y}_{v26} = \mathcal{F}_{reg}(x) \in \mathbb{R}

    loại bỏ hoàn toàn các toán tử phi tuyến phức tạp trong khâu giải mã hộp [T2 Y26A tr.8].
  - Tham số ``reg_max`` được thiết lập cố định về 1 [T1 yolo26.yaml:10]. Nhánh hộp xuất trực tiếp 4 giá trị số thực đại diện cho khoảng cách tọa độ, biến đổi hàm giải mã thành một phép ánh xạ affine thuần túy tuyến tính, loại bỏ hoàn toàn các toán tử Softmax phức tạp ở đầu ra [T2 Y26A tr.8].
  - Cấu trúc nhánh phân loại lớp cũng được hiện đại hóa: khi cờ ``legacy=False`` (tự động kích hoạt khi có C3k2), nhánh lớp sử dụng tích hợp tích chập Depthwise Conv :math:`3 \times 3` kết hợp Conv :math:`1 \times 1`, giúp giảm số tham số của riêng phần đầu dự đoán từ 751,519 (ở YOLOv8n) xuống chỉ còn 120,443 tham số (ở YOLO26n đối với bài toán 5 lớp) [T1 ultralytics/nn/modules/head.py].

Cơ chế NMS-free và điều kiện kích hoạt
--------------------------------------

- Bản chất của cơ chế NMS-free:
  - Trong các kiến trúc truyền thống như YOLOv8, quá trình huấn luyện sử dụng chiến lược gán nhãn một-nhiều (one-to-many label assignment), trong đó một đối tượng ground truth được gán cho nhiều anchor lân cận. Hậu quả là ở pha suy luận, mô hình luôn dự đoán nhiều hộp chồng lấn cho cùng một thực thể, bắt buộc phải dùng thuật toán Non-Maximum Suppression (NMS) để triệt tiêu hộp trùng [T2 Y26A tr.7].
  - NMS có chi phí tính toán biến thiên theo số lượng vật thể trong khung hình và chứa các nhánh rẽ điều kiện khó ánh xạ hiệu quả lên kiến trúc tính toán song song cứng của NPU.
  - YOLO26 tích hợp nhánh dự đoán một-một (one-to-one lead head): "By redesigning the prediction head to support one-to-one label assignment [24], the model learns to output a single, definitive box per object instance during training." [T2 Y26A tr.7]. Cơ chế này cho phép mô hình học cách chỉ sinh ra đúng một hộp tin cậy nhất cho mỗi thực thể: "YOLO26 fundamentally redesigns the prediction head to produce direct, non-redundant bounding box predictions without the need for NMS" [T2 Y26B tr.7], từ đó đạt thời gian suy luận đơn định: "By removing the computational burden of DFL and adopting a native one-to-one prediction head, YOLO26 achieves deterministic inference times" [T2 Y26A tr.5].

- Điều kiện kích hoạt trong mã nguồn:
  - Cấu hình ``yolo26.yaml`` thiết lập cờ ``end2end: True`` [T1 yolo26.yaml:9].
  - Trong quá trình khởi tạo mô hình, đầu ``Detect`` sẽ sao chép cấu trúc nhánh hộp và nhánh lớp thành hai cặp song song: nhánh một-nhiều phụ trợ và nhánh một-một chính thức [T1 ultralytics/nn/modules/head.py].
  - Khi gọi phương thức tối ưu hóa mô hình ``model.fuse()`` cho triển khai, nhánh phụ trợ sẽ bị loại bỏ, chỉ giữ lại nhánh một-một cùng logic lọc hậu kỳ cố định dựa trên hàm ``topk`` mà không sử dụng thuật toán NMS lặp truyền thống [T1 ultralytics/nn/modules/head.py].

Ví dụ số: Đếm tham số và kích thước tensor qua một khối
=======================================================

Để minh họa sự khác biệt cụ thể giữa hai kiến trúc, xét chi tiết quá trình tính toán và kích thước tensor qua tầng trích xuất đặc trưng layer 2 trong backbone của YOLOv8n (khối C2f) và YOLO26n (khối C3k2) với ảnh đầu vào chuẩn kích thước :math:`(1, 3, 640, 640)`.

Sau khi đi qua tầng tích chập khởi tạo layer 0 (stride 2) và layer 1 (stride 2), tensor đưa vào layer 2 ở cả hai mô hình đều có cùng kích thước không gian và số kênh là :math:`(1, 32, 160, 160)`.

Chi tiết khối C2f tại layer 2 của YOLOv8n (đầu vào 32 kênh, đầu ra 32 kênh):
  - Lớp tích chập đầu vào ``cv1``: Conv2d(32 vào, 32 ra, kernel :math:`1 \times 1`, bias=False) kết hợp BatchNorm2d(32) và SiLU.
    - Trọng số tích chập: :math:`32 \times 32 \times 1 \times 1 = 1,024` tham số.
    - Tham số BatchNorm: :math:`2 \times 32 = 64` tham số (:math:`\gamma` và :math:`\beta`).
    - Kích thước tensor đầu ra: :math:`(1, 32, 160, 160)`.
  - Tách tensor: Chia đôi 32 kênh thành hai phần :math:`y_0` kích thước :math:`(1, 16, 160, 160)` và :math:`y_1` kích thước :math:`(1, 16, 160, 160)`.
  - Khối con ``Bottleneck`` (:math:`n=1`):
    - ``cv1``: Conv2d(16 vào, 16 ra, kernel :math:`3 \times 3`, bias=False) + BN(16). Trọng số conv: :math:`16 \times 16 \times 3 \times 3 = 2,304`; BN: 32 tham số. Output: :math:`(1, 16, 160, 160)`.
    - ``cv2``: Conv2d(16 vào, 16 ra, kernel :math:`3 \times 3`, bias=False) + BN(16). Trọng số conv: :math:`16 \times 16 \times 3 \times 3 = 2,304`; BN: 32 tham số. Output: :math:`(1, 16, 160, 160)`.
    - Phép cộng đường tắt: :math:`y_1 + \text{out}_{cv2}` tạo ra tensor kích thước :math:`(1, 16, 160, 160)`.
  - Ghép nối đặc trưng: Ghép :math:`y_0`, :math:`y_1` và tensor đầu ra của bottleneck thu được tensor :math:`(1, 48, 160, 160)`.
  - Lớp tích chập đầu ra ``cv2``: Conv2d(48 vào, 32 ra, kernel :math:`1 \times 1`, bias=False) + BN(32).
    - Trọng số tích chập: :math:`32 \times 48 \times 1 \times 1 = 1,536`; BN: 64 tham số.
    - Kích thước tensor đầu ra của C2f: :math:`(1, 32, 160, 160)`.
  - Tổng số tham số của khối C2f: :math:`1,024 + 64 + 2,304 + 32 + 2,304 + 32 + 1,536 + 64 = 7,360` tham số (trước khi fuse).

Chi tiết khối C3k2 tại layer 2 của YOLO26n (đầu vào 32 kênh, đầu ra 64 kênh):
  - Lớp tích chập đầu vào ``cv1``: Conv2d(32 vào, 32 ra, kernel :math:`1 \times 1`, bias=False) + BN(32). Trọng số conv: 1,024; BN: 64 tham số. Tensor ra: :math:`(1, 32, 160, 160)`.
  - Tách tensor: Chia thành :math:`y_0` kích thước :math:`(1, 16, 160, 160)` và :math:`y_1` kích thước :math:`(1, 16, 160, 160)`.
  - Khối con ``Bottleneck`` với hệ số nén kênh :math:`e=0.25`:
    - Số kênh ẩn trung gian bị thu hẹp còn: :math:`16 \times (0.25 / 0.5) = 8` kênh.
    - ``cv1``: Conv2d(16 vào, 8 ra, kernel :math:`3 \times 3`, bias=False) + BN(8). Trọng số conv: :math:`8 \times 16 \times 3 \times 3 = 1,152`; BN: 16 tham số. Tensor ra: :math:`(1, 8, 160, 160)`.
    - ``cv2``: Conv2d(8 vào, 16 ra, kernel :math:`3 \times 3`, bias=False) + BN(16). Trọng số conv: :math:`16 \times 8 \times 3 \times 3 = 1,152`; BN: 32 tham số. Tensor ra: :math:`(1, 16, 160, 160)`.
    - Phép cộng đường tắt: :math:`y_1 + \text{out}_{cv2}` tạo ra tensor kích thước :math:`(1, 16, 160, 160)`.
  - Ghép nối đặc trưng: Ghép :math:`y_0`, :math:`y_1` và tensor đầu ra bottleneck thu được tensor :math:`(1, 48, 160, 160)`.
  - Lớp tích chập đầu ra ``cv2``: Conv2d(48 vào, 64 ra, kernel :math:`1 \times 1`, bias=False) + BN(64).
    - Trọng số tích chập: :math:`64 \times 48 \times 1 \times 1 = 3,072`; BN: 128 tham số.
    - Kích thước tensor đầu ra của C3k2: :math:`(1, 64, 160, 160)` (tăng gấp đôi kênh so với đầu vào).
  - Tổng số tham số của khối C3k2: :math:`1,024 + 64 + 1,152 + 16 + 1,152 + 32 + 3,072 + 128 = 6,640` tham số (trước khi fuse).

So sánh khối lượng phép tính (MACs) qua layer 2:
  - Với lưới không gian :math:`160 \times 160 = 25,600` điểm ảnh:
    - Trong C2f: ``cv1`` tiêu tốn :math:`25,600 \times 32 \times 32 \times 1 = 26.21` MMACs. Hai lớp tích chập :math:`3 \times 3` của bottleneck tiêu tốn :math:`2 \times (25,600 \times 16 \times 16 \times 9) = 117.96` MMACs. Lớp ``cv2`` tiêu tốn :math:`25,600 \times 32 \times 48 \times 1 = 39.32` MMACs. Tổng khối C2f cần xấp xỉ 183.50 MMACs (tương đương 0.367 GFLOPs).
    - Trong C3k2: ``cv1`` tiêu tốn 26.21 MMACs. Nhờ :math:`e=0.25`, hai lớp tích chập :math:`3 \times 3` của bottleneck (16 vào 8 ra, và 8 vào 16 ra) chỉ tiêu tốn :math:`2 \times (25,600 \times 16 \times 8 \times 9) = 58.98` MMACs (giảm đúng 50% tính toán conv :math:`3 \times 3`). Lớp ``cv2`` tiêu tốn :math:`25,600 \times 64 \times 48 \times 1 = 78.64` MMACs. Tổng khối C3k2 tiêu tốn 163.84 MMACs (tương đương 0.328 GFLOPs).

Nhận xét:
  - Mặc dù khối C3k2 tại layer 2 nâng số kênh đặc trưng lên gấp đôi (từ 32 lên 64), tổng số tham số của khối (6,640) vẫn thấp hơn khối C2f (7,360) của YOLOv8n và khối lượng tính toán giảm từ 183.50 MMACs xuống 163.84 MMACs. Sự tối ưu hóa này đến từ cơ chế ép kênh ẩn bên trong bottleneck (:math:`e=0.25`), giúp giảm mạnh số lượng phép tính tích chập :math:`3 \times 3` tốn kém.
  - Sau khi thực hiện fuse tích chập và BatchNorm, khối C2f còn lại :math:`1,024 + 32 + 2,304 + 16 + 2,304 + 16 + 1,536 + 32 = 7,264` tham số gồm trọng số và bias. Khối C3k2 còn lại :math:`1,024 + 32 + 1,152 + 8 + 1,152 + 16 + 3,072 + 64 = 6,520` tham số, minh chứng cho sự tối ưu sâu sắc về mặt kiến trúc phần cứng.

Nguồn tài liệu tham khảo
========================

Các tài liệu kỹ thuật và bài báo hội thảo chính thức được sử dụng để đối chiếu dữ liệu trong trang này:

.. list-table:: Danh mục tài liệu tham khảo và đối soát trích dẫn
   :header-rows: 1
   :widths: 14 10 60 16

   * - Nhãn
     - Phân loại
     - Tên tài liệu / Đường dẫn lưu trữ
     - Ghi chú
   * - ``YOFF``
     - T2
     - :download:`yolo26_official_2026jocher.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_official_2026jocher.pdf>`
     - Jocher et al. (2026), bài báo chính thức về họ mô hình YOLO26
   * - ``Y26A``
     - T2
     - :download:`yolo26_nmsfree_2026chakrabarty.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_nmsfree_2026chakrabarty.pdf>`
     - Chakrabarty (2026), phân tích cơ chế NMS-free và giải mã không DFL
   * - ``Y26B``
     - T2
     - :download:`yolo26_arch_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_arch_2025sapkota.pdf>`
     - Sapkota et al. (2025), khảo sát cấu trúc mạng và tối ưu hóa phần cứng
   * - ``UEVOL``
     - T2
     - :download:`ultralytics_yolo_evolution_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/ultralytics_yolo_evolution_2025sapkota.pdf>`
     - Sapkota et al. (2025), tổng quan tiến trình tiến hóa họ mạng Ultralytics
   * - ``T1``
     - T1
     - Tệp cấu hình ``yolov8.yaml``, ``yolo26.yaml`` và mã nguồn Ultralytics
     - Cấu hình mạng gốc trong thư viện ``ultralytics``
