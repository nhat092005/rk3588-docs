:tocdepth: 1

***********************
Tiêu chí thân thiện NPU
***********************

.. admonition:: Trang này trả lời

   - Hướng dẫn hiệu năng UG232 đưa ra các tiêu chí gì về căn lề kênh, tỷ số nhân với bước trượt và fusion?
   - Các bài báo đo YOLO trên RK3588 báo những số gì và có điểm nào bất nhất?

.. admonition:: Tóm tắt

   - Conv INT8 yêu cầu số kênh vào và ra là bội số của 32 phần tử, trong khi Depthwise Conv INT8 yêu cầu căn chỉnh 64 phần tử [T1 UG232 tr.145].
   - Ràng buộc căn chỉnh chiều rộng tại lớp đầu tiên ở OPL mục 5.1.2 chỉ áp dụng cho API zero-copy và không áp đặt lên API thông thường [T1 OPL tr.335].
   - Danh sách op có và không có mục NPU của YOLOv8 nằm ở :doc:`02-op-yolov8-tren-rknn`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Tiêu chí hiệu năng theo UG232
================================

Việc một toán tử có tên trong danh mục NPU chỉ đảm bảo tính khả thi về mặt biên dịch, không đồng nghĩa với việc toán tử đó đạt hiệu suất phần cứng cao. Tài liệu hướng dẫn người dùng Rockchip RKNPU User Guide (UG232) chương 8 đưa ra các nguyên tắc định lượng để thiết kế mô hình đạt hiệu năng tối ưu [T1 UG232 tr.140-150].

1.1 Căn chỉnh bộ nhớ và kích thước kernel
-----------------------------------------

Hiệu suất của mảng systolic trong mỗi NPU core phụ thuộc chặt chẽ vào cấu trúc căn lề dữ liệu trong bộ nhớ:

1. Căn chỉnh số lượng kênh:
   Bội số channel để chạy hiệu quả (Conv INT8 là 32, Depthwise INT8 là 64) nằm ở :ref:`layout-alignment` [T1 UG232 tr.145].

2. Tỷ số kích thước nhân và bước trượt:
   UG232 chỉ ra rằng tỷ số giữa kích thước nhân tích chập và bước trượt (``Ksize / Kstride``) càng lớn thì khả năng tái sử dụng dữ liệu trong bộ nhớ đệm cục bộ (SRAM buffer 384KB mỗi core) càng cao, dẫn đến hiệu suất phần cứng cao hơn [T1 UG232 tr.147]. Ngược lại, các tầng tích chập có stride lớn nhưng kernel nhỏ (ví dụ kernel 1x1 stride 2) tiêu tốn nhiều băng thông đọc dữ liệu từ DDR nhưng tính toán ít.
   Đồng thời, hiệu suất tính toán được duy trì ở mức tối đa khi dung lượng tham số nhân thỏa mãn bất đẳng thức:

   .. math::

      \text{KH} \times \text{KW} \times \text{KC} \times \text{type\_bytes} < 6\,\text{KB}

   Điều kiện này đảm bảo toàn bộ trọng số của một phép tính tích chập nằm vừa vặn trong bộ nhớ đệm tốc độ cao của DPU [T1 UG232 tr.147].

3. Căn chỉnh chiều rộng lớp đầu tiên:
   Ràng buộc width chia hết cho 16 khi số kênh vào là 1, 3 hoặc 4 chỉ áp dụng cho zero-copy API [T1 OPL tr.335, tr.336], xem :doc:`../04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api` mục 2.1.

1.2 Fusion và op kém hiệu quả
-----------------------------

Rule fusion phần cứng và ba nhóm op cần giảm (chuyển dữ liệu, đổi kích thước, activation không phải ReLU) nằm ở :ref:`fusion-rule` [T1 UG232 tr.142] [T1 UG232 tr.146].

2. Số đo YOLO trên RK3588 trong bài báo
=======================================

Trong khi các bài báo kiến trúc như YOLOv6 chủ yếu đo lường trên GPU Tesla T4, một số công trình học thuật gần đây đã tiến hành đo đạc thực nghiệm trực tiếp trên vi xử lý Rockchip RK3588.

2.1 Benchmark EDGE
------------------

Nghiên cứu EDGE tiến hành khảo sát hiệu năng của 9 biến thể YOLO (v5, v8, v11 ở các kích cỡ nano, small, medium) trên ba SoC của Rockchip gồm RV1106, RK3568 và RK3588 [T2 EDGE tr.4, 5]:

   "All deployments used the original FP32 PyTorch weights; no model was retrained, fine-tuned, pruned, or structurally modified beyond quantization." [T2 EDGE tr.4]

Các phép đo được thực hiện qua 100 lần chạy, loại bỏ 10 lần đầu khởi động, và độ lệch chuẩn luôn duy trì dưới 1% giá trị trung bình nhờ đường ống thực thi tần số cố định của NPU Rockchip [T2 EDGE tr.5].

.. figure:: ../../../_assets/img/01-kien-thuc-nen/06-thiet-ke-model/hardware-aware-nas-va-detector/edge-fig3-yolo-latency-rv1106-rk3568-rk3588.png
   :align: center
   :alt: Độ trễ suy luận trung bình của các model YOLO trên RV1106, RK3568 và RK3588

   Độ trễ suy luận trung bình của các model YOLO trên RV1106, RK3568 và RK3588 với ảnh 640x640. Nguồn: [T2 EDGE tr.5, Fig. 3]

.. list-table:: So sánh thông số kiến trúc và độ trễ INT8 trên NPU RK3588 (Đo ở ảnh 640x640)
   :header-rows: 1
   :widths: 18 16 16 16 18 16

   * - Mô hình
     - Tham số (M)
     - GFLOPS
     - mAP (%)
     - Độ trễ AUTO (ms)
     - Độ trễ C0_1_2 (ms)
   * - YOLOv5n
     - 2.6
     - 7.7
     - 34.3
     - 21.70
     - 21.07
   * - YOLOv8n
     - 3.2
     - 8.7
     - 37.3
     - 24.88
     - 25.33
   * - YOLO11n
     - 2.6
     - 6.5
     - 39.5
     - 30.71
     - 31.27

Từ Bảng 2 và Bảng 4 của công trình EDGE [T2 EDGE tr.4, 7], ta nhận thấy một hiện tượng nghịch lý:

- **FLOPs thấp nhưng trễ cao**: YOLO11n có số lượng phép tính lý thuyết thấp nhất (chỉ 6.5 GFLOPS so với 8.7 của v8n và 7.7 của v5n), nhưng thời gian suy luận trên NPU RK3588 lại cao nhất (30.71 ms so với 24.88 ms của v8n và 21.7 ms của v5n).
- **Nguyên nhân kiến trúc**: Nhóm tác giả EDGE đưa ra nhận định [T2 EDGE tr.5]:

   "Instead, latency correlated more closely with model accuracy (mAP), suggesting that architectural innovations (e.g., C2f in YOLOv8, C3k2 in YOLO11) introduce additional computational overheads that do not map efficiently onto NPUs." [T2 EDGE tr.5]

Cần lưu ý rằng đây là giả thuyết phân tích của nhóm tác giả EDGE, bài báo không thực hiện phép đo vi mô phân tách từng khối C2f hoặc C3k2 trên NPU.

- **Khả năng đáp ứng thời gian thực (Real-time Feasibility)**:
  Bài báo phân tích tính khả thi thời gian thực theo các ngưỡng 25 FPS (40 ms), 30 FPS (33.3 ms) và 50 FPS (20 ms) [T2 EDGE tr.5]. Trên RK3588 ở độ phân giải 640x640, toàn bộ các mô hình nano (v5n 21.7 ms, v8n 24.88 ms, v11n 30.71 ms) đều đạt ngưỡng 30 FPS, nhưng không mô hình nào đạt ngưỡng 50 FPS (20 ms). Ngược lại, các mô hình quy mô medium (v5m, v8m, v11m) có độ trễ từ 58 ms đến hơn 90 ms, không thể đáp ứng tần số khung hình camera giám sát tiêu chuẩn nếu không hạ độ phân giải hoặc áp dụng kỹ thuật cắt tỉa [T2 EDGE tr.5, 7].

- **Điểm bất nhất nội bộ trong công trình EDGE**: Tại trang 6, bài báo nêu rằng với mô hình YOLOv5n, sự khác biệt giữa cấu hình đơn lõi và đa lõi là dưới 5% (21.5 ms so với 20.5 ms) và đưa ra kết luận khái quát:

   "For larger models, the gains were similarly modest or even negligible" [T2 EDGE tr.6]

Tuy nhiên, bảng số liệu thực nghiệm Table 4 (trang 7) lại phản ánh điều ngược lại: ở YOLOv5s, độ trễ giảm từ 34.42 ms (lõi C0) xuống 27.95 ms (chế độ C0_1_2), ở YOLOv5m độ trễ giảm từ 69.61 ms xuống 58.34 ms (chế độ ALL), và ở YOLO11s cấu hình tự động AUTO đạt 41.25 ms, nhanh hơn rõ rệt so với 52.47 ms ở lõi đơn C0 [T2 EDGE Table 4]. Lời văn khái quát của EDGE mâu thuẫn trực tiếp với các số liệu chi tiết trong bảng của chính họ.

2.2 DAHD-YOLO
-------------

Công trình DAHD-YOLO cải tiến mạng YOLOv8 phục vụ bài toán phát hiện hành vi hút thuốc trong các môi trường phức tạp, tích hợp khối tái tham số hóa DBB (Diverse Branch Block) trong khối C2f_DBCA, cơ chế chú ý ECA-FPN, khối AFGCA và đầu DetectDBB [T2 DAHD tr.5, Figure 1].

.. figure:: ../../../_assets/img/01-kien-thuc-nen/06-thiet-ke-model/hardware-aware-nas-va-detector/dahd-fig1-dahd-yolo-architecture.png
   :align: center
   :alt: Kiến trúc DAHD-YOLO

   Kiến trúc DAHD-YOLO (xây trên YOLOv8, thêm C2f_DBCA, ECA-FPN, DetectDBB, AFGCA). Nguồn: [T2 DAHD tr.5, Figure 1]

Thực nghiệm triển khai trên bo mạch Orange Pi 5 Plus trang bị RK3588 (sử dụng nhóm luồng tăng tốc đa lõi) cung cấp các kết quả đối chiếu tại Bảng 6 [T2 DAHD Table 6, tr.18]:

- **Mô hình gốc YOLOv8s**: Ở chế độ INT8, đạt 56.3 ms độ trễ, thông lượng 70.9 FPS (ở độ phân giải 720P) và 73.0% mAP50.
- **Mô hình cải tiến DAHD-YOLO**: Ở chế độ INT8, đạt 79.1 ms độ trễ, thông lượng 50.2 FPS (720P) và 74.36% mAP50.

Nghiên cứu DAHD ghi nhận chi tiết về độ trễ trên ảnh 720P [T2 DAHD tr.18]:

   "single image with a resolution of 1280 × 720 reaches 79.1 ms" [T2 DAHD tr.18]

Kết quả thực nghiệm trên NPU RK3588 cho thấy một thực tế rõ ràng: mặc dù việc đưa vào các khối tái tham số hóa DBB và cơ chế chú ý giúp tăng nhẹ độ chính xác mAP50 (từ 73.0% lên 74.36%), tốc độ suy luận của mô hình ở INT8 lại bị suy giảm nghiêm trọng (độ trễ tăng từ 56.3 ms lên 79.1 ms, thông lượng giảm 29.2% từ 70.9 FPS xuống 50.2 FPS). Tác giả bài báo thừa nhận [T2 DAHD tr.20]:

   "The model's increased structural complexity has resulted in a decline in inference speed." [T2 DAHD tr.20]

Về khía cạnh tiêu thụ năng lượng, công trình DAHD ghi nhận bo mạch Orange Pi 5 Plus trang bị RK3588 chỉ tiêu thụ dưới 10 W (từ 6 W đến 9 W) trong toàn bộ quá trình thực thi đa luồng, thấp hơn rất nhiều so với mức tiêu thụ khoảng 200 W của nền tảng máy tính gắn card đồ họa RTX 3070 [T2 DAHD tr.18]. Điều này khẳng định lợi thế vượt trội về hiệu suất năng lượng của bộ xử lý NPU nhúng, ngay cả khi cấu trúc mô hình chưa đạt điểm tối ưu tuyệt đối về độ trễ.

2.3 Điểm bất nhất của DAHD-YOLO
-------------------------------

Khi thẩm định dữ liệu từ bài báo DAHD-YOLO, có nhiều điểm mâu thuẫn số liệu nội bộ cần lưu ý:

1. **Nghịch lý giữa độ trễ và thông lượng ở FP16**: Trong Table 6 (trang 18), ở chế độ FP16, DAHD-YOLO được báo cáo có thời gian suy luận là 116.2 ms (nhanh hơn mức 131.9 ms của YOLOv8s), nhưng thông lượng khung hình FPS ở 720P lại ghi 26.9 FPS (chậm hơn mức 32.9 FPS của YOLOv8s). Hai chỉ số này mâu thuẫn trực tiếp với nhau về mặt logic tính toán.
2. **Nhầm lẫn giữa FP16 và INT8 trong văn bản**: Tại trang 18, văn bản ghi: "the INT8 optimized model's single-thread inference time per frame is 0.1162 s", trong khi trong Table 6 giá trị 116.2 ms lại thuộc về dòng cấu hình FP16, còn cấu hình INT8 có thời gian là 79.1 ms.
3. **Mâu thuẫn giá trị mAP50 giữa các bảng**: Tại Table 6, độ chính xác mAP50 của YOLOv8s và DAHD-YOLO lần lượt là 73.6% và 78.76%. Tuy nhiên, trong bảng thử nghiệm triệt tiêu (Ablation Study, Table 4 trang 16), baseline YOLOv8s lại ghi 80.9% và DAHD-YOLO đạt 86.0% mà không có lời giải thích về sự khác biệt tập dữ liệu kiểm thử.
4. **Không bóc tách được yếu tố thành phần**: DAHD-YOLO thay đổi đồng thời nhiều thành phần kiến trúc (C2f_DBCA, ECA-FPN, AFGCA, Wise-PIoU, DetectDBB), do đó không thể bóc tách định lượng xem sự suy giảm tốc độ trên NPU RK3588 bắt nguồn từ phép tái tham số hóa DBB hay do các khối chú ý phân mảnh gây ra.

3. Hiểu sai thường gặp
======================

.. list-table:: Các hiểu sai phổ biến về tiêu chí thân thiện NPU trên RK3588
   :header-rows: 1
   :widths: 28 44 28

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Tích chập Depthwise (DWConv) luôn nhẹ hơn và chạy nhanh hơn tích chập thông thường trên NPU RK3588.
     - DWConv có tỷ lệ tái sử dụng tham số thấp và đòi hỏi căn chỉnh kênh INT8 tới 64 phần tử (so với 32 của Conv thường), dẫn đến hiệu suất phần cứng (MAC utilization) thực tế thấp hơn nhiều so với Conv tiêu chuẩn.
     - [T1 UG232 tr.145-147]
   * - Mọi mô hình có chứa phép nhân ma trận MatMul đều có thể chạy hoàn toàn trên phần cứng NPU.
     - OPL chương 3.2 chỉ hỗ trợ dạng exMatMul hạn chế (k <= 8192 và shape tensor đặc thù), còn MatMul tổng quát chỉ có mục CPU 4.33 và sẽ rơi về CPU nếu không được hợp nhất.
     - [T1 OPL tr.102, tr.324]
   * - Ràng buộc căn chỉnh chiều rộng lớp đầu tiên (width alignment) bắt buộc phải tuân thủ trong mọi dự án triển khai.
     - OPL mục 5.1 ghi chú rõ ràng ràng buộc căn lề chiều rộng này chỉ áp dụng đối với zero-copy API, còn API thông thường không bị ràng buộc.
     - [T1 OPL tr.335]

Nguồn
=====

.. list-table:: Các nguồn tài liệu kỹ thuật được sử dụng trong trang
   :header-rows: 1
   :widths: 15 10 60 15

   * - Nhãn
     - Tier
     - Tệp / Tài liệu
     - Số lần trích
   * - ``OPL``
     - T1
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`
     - 4
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 8
   * - ``EDGE``
     - T2
     - :download:`edgesoc_benchmark_2026kong.pdf <../../../_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf>`
     - 11
   * - ``DAHD``
     - T2
     - :download:`dahd_yolo_rk3588_2025.pdf <../../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`
     - 8
