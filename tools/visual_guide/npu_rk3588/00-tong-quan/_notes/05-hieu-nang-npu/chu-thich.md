# Ghi chú chuyên đề: Hiệu năng NPU RK3588, Độ trễ E2E và Định lượng FLOPs/TOPS

## Câu hỏi mở đầu
Độ trễ toàn chu trình (E2E Latency) của một mô hình phát hiện vật thể trên RK3588 được cấu thành từ những thành phần nào? Sự khác nhau giữa FPS tính theo độ trễ đơn luồng và Throughput đa luồng (3 contexts) là gì? Tại sao 1 MAC = 2 FLOPs, và nguyên nhân sâu xa của "Nghịch lý FLOPs" (mô hình ít FLOPs hơn nhưng NPU chạy lại chậm hơn) theo mô hình Roofline ra sao?

## Hình P.1 (hp-1-latency-pipeline-va-da-loi) [T2 chung]
Pipeline độ trễ (E2E Latency), FPS đơn luồng so với Thông lượng đa luồng và Kiến trúc 3-core NPU:
- Pipeline độ trễ đầu-cuối (End-to-End Latency Breakdown):
  - Pre-processing (Tiền xử lý, T_pre): Chạy trên CPU / RGA, bao gồm giải mã ảnh, letterbox resize về kích thước 640x640, chuẩn hóa kênh màu BGR sang RGB và chia tỷ lệ 1/255.
  - NPU Inference (Suy luận phần cứng, T_npu): Thời gian đưa tensor vào NPU, nạp trọng số, thực thi các phép nhân ma trận mảng tích chập (Conv MACs) qua driver rknpu và runtime RKNN, xuất ra các tensor đặc trưng thô.
  - Post-processing (Hậu xử lý, T_post): Chạy trên CPU, thực hiện giải mã hộp DFL (Distribution Focal Loss), khôi phục tọa độ hộp thực, lọc ngưỡng tin cậy (confidence score) và Non-Maximum Suppression (NMS) để loại bỏ các hộp trùng lặp.
  - Tổng thời gian trễ một frame tuần tự: T_E2E = T_pre + T_npu + T_post.
- FPS độ trễ (Single-stream FPS) so với Throughput FPS (Multi-stream):
  - FPS_latency = 1000 / T_E2E (khung hình/giây): Đây là tốc độ đo theo mô hình chuỗi tuần tự cho 1 camera đơn luồng (chờ xử lý xong hết pre, npu, post của frame cũ mới nhận frame tiếp theo).
  - Throughput FPS (Thông lượng song song): Khi triển khai nhiều camera hoặc nhiều context độc lập (3 contexts ứng với 3 core NPU độc lập: Core 0, Core 1, Core 2), cả 3 luồng cùng suy luận song song trên NPU. Thông lượng tổng hệ thống tăng gần gấp 3 lần (ví dụ từ ~50 FPS lên ~140-150 FPS tổng) mà độ trễ của từng frame riêng lẻ không bị đội lên.
- Quản lý đa lõi với core_mask trên RK3588:
  - NPU RK3588 tích hợp 3 lõi tính toán độc lập: Core 0 (0x1), Core 1 (0x2), Core 2 (0x4), hoặc toàn bộ 3 lõi (0x7 / CORE_0_1_2).
  - Hành vi ở core_mask=AUTO: Mặc định runtime gán công việc vào Core 0 vì các mô hình sử dụng hàm kích hoạt SiLU (toán tử ConvExSwish trong YOLOv8n SiLU) chưa được driver/runtime hỗ trợ tự động băm nhỏ lớp trên 3 lõi, khiến chỉ có Core 0 gánh tính toán. Khi chuyển sang mô hình dùng ReLU (toán tử ConvRelu), NPU có thể chia nhỏ workload trên cả 3 lõi (tỷ lệ xấp xỉ 35% / 34% / 32%), giúp giảm thời gian NPU đáng kể.
Đọc thêm: 02_ mục 2.5; 09_ mục 9.4; 10_ mục 10.3. Khái niệm: Hình 2.5, Hình 9.4, Hình 10.3

## Hình P.2 (hp-2-flops-mac-tops-va-nghich-ly-bo-nho) [T2 chung]
Định lượng FLOPs, MACs, TOPS và Nghịch lý bộ nhớ (Memory-bound) trên NPU RK3588:

1. Bản chất toán học: Quy đổi 1 MAC = 2 FLOPs:
Mỗi phép tính Multiply-Accumulate (MAC) bao gồm 1 phép nhân và 1 phép cộng dồn: y = y + (w · x). Do đó, 1 MAC tương đương đúng 2 phép tính số học (2 FLOPs).
Với một lớp Convolution 2D chuẩn trên tensor [H, W, Cin] với Cout bộ lọc kích thước [K, K, Cin]:
- Số phép tính MAC = Hout · Wout · Cout · (K · K · Cin)
- Số FLOPs lý thuyết = 2 · Số MAC = 2 · Hout · Wout · Cout · (K · K · Cin)
Ví dụ trong YOLOv8n (nguồn LOG table_v8n.md): Tổng mô hình có 3,006,623 tham số và 8.087 GFLOPs; riêng lớp Detect chiếm 2.965 GFLOPs (tương đương 36.7% tổng FLOPs toàn mạng).

2. Phân biệt 3 chỉ số dễ nhầm lẫn trong đánh giá phần cứng:
- FLOPs (Floating Point Operations / Phép tính số học): Đo lường khối lượng công việc lý thuyết cần thực hiện của mô hình. Đây là kích thước bài toán, mang tính chất thuật toán và không thay đổi theo phần cứng.
- FLOPS / TOPS (Operations Per Second): Tốc độ tính toán của cỗ máy phần cứng (chữ S viết hoa là Per Second). NPU RK3588 gồm 3 lõi, mỗi lõi hỗ trợ 1024 MACs INT8 mỗi chu kỳ (TRM1 tr.1984), đạt đỉnh lên tới 6 TOPS INT8 (DS tr.7).
- Latency / FPS (Thời gian trễ và Thông lượng thực tế): Thời gian thực tế (mili-giây) để NPU chạy xong một frame. Latency không chỉ phụ thuộc vào FLOPs mà phụ thuộc quyết định vào băng thông RAM DDR, dung lượng bộ đệm CBUF và độ tối ưu driver/compiler.

3. Nghịch lý FLOPs và Mô hình Roofline trên NPU RK3588:
- Nghịch lý FLOPs: Mô hình có FLOPs thấp hơn chưa chắc chạy nhanh hơn trên NPU!
  Ví dụ thực tế giữa YOLO26n và YOLOv8n trên board RK3588:
  - YOLO26n chỉ có 5.314 GFLOPs (giảm 34% FLOPs so với 8.087 GFLOPs của YOLOv8n).
  - Nhưng trên thực tế board RK3588 ở chế độ INT8 AUTO, độ trễ NPU của YOLO26n lại cao hơn YOLOv8n khoảng 13-16% (18.66 ms so với 16.14 ms).
- Nguyên nhân cốt lõi từ Mô hình Roofline (Roofline Model):
  - Cường độ tính toán (Arithmetic Intensity = FLOPs / Byte nạp): Nếu một lớp mạng đòi hỏi nạp nhiều dữ liệu từ RAM DDR nhưng thực hiện quá ít phép tính trên mỗi byte dữ liệu (như Depthwise Conv, Resize, Split), NPU sẽ rơi vào vùng nghẽn băng thông bộ nhớ (Memory-bound), mảng MAC 32x32 phải dừng chờ (stall).
  - Phân mảnh lớp và Overhead điều khiển: YOLO26n có tới 180 lớp NPU (so với 116 lớp của YOLOv8n). Mỗi lớp nhỏ đòi hỏi chi phí thiết lập phần cứng (kernel launch, context switch, DMA sync) làm suy giảm hiệu năng thực tế.
Đọc thêm: 01_ mục 1.4; 02_ mục 2.3; 09_ mục 9.1; 10_ mục 10.2, 10.3. Khái niệm: Hình C.1, Hình C.3, Hình 9.1, Hình 10.2

## Hiểu sai thường gặp
- "Tốc độ xử lý của mô hình phát hiện vật thể chỉ bằng thời gian chạy NPU" -> Thời gian NPU chỉ là một phần; tổng độ trễ thực tế còn bao gồm tiền xử lý (resize, letterbox) và hậu xử lý (DFL, NMS) trên CPU [REPO ai/automation/tables.py:288] (Hình P.1)
- "RK3588 có 3 lõi NPU nên mọi model tự động chạy nhanh gấp 3 lần" -> Nhiều lớp như ConvExSwish (SiLU) không thể chia đa lõi tự động và chỉ chạy trên Core 0; muốn tận dụng 3 lõi cần đổi hàm kích hoạt sang ReLU hoặc chạy 3 luồng context độc lập [LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_CORE_0_1_2.txt] (Hình P.1)
- "Mô hình có FLOPs thấp hơn chắc chắn sẽ chạy nhanh hơn trên NPU" -> YOLO26n có FLOPs thấp hơn nhưng nhiều lớp tuần tự và overhead nhỏ khiến độ trễ trên NPU lại cao hơn YOLOv8n khoảng 13-16% [LOG 2026-10-10_yolo-phaseA/README.md] (Hình P.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Trình bày 3 thành phần chính cấu thành nên độ trễ toàn chu trình (E2E Latency) của một frame video trong hệ thống giám sát đồ bảo hộ lao động trên RK3588. Thành phần nào chạy trên NPU và thành phần nào chạy trên CPU?
Đáp án: 3 thành phần gồm: (1) Pre-processing (tiền xử lý: resize letterbox, chuẩn hóa màu BGR->RGB) chạy trên CPU/RGA; (2) NPU Inference (suy luận mạng nơ-ron: nạp tensor, tính ma trận chập) chạy tăng tốc trên NPU; (3) Post-processing (hậu xử lý: giải mã hộp DFL, lọc ngưỡng tin cậy, khử trùng lặp NMS) chạy trên CPU [REPO ai/automation/tables.py:288] (Hình P.1).

### Câu 2 (phân biệt)
Phân biệt sự khác nhau giữa FPS tính theo độ trễ đơn chuỗi (FPS_latency) và FPS thông lượng đa luồng (Throughput FPS). Làm thế nào để tăng thông lượng trên chip RK3588?
Đáp án: FPS_latency = 1000 / T_E2E đo tốc độ xử lý tuần tự cho 1 camera đơn luồng (frame này xong mới nạp frame kế). Throughput FPS đo tổng số khung hình xử lý được trên một giây khi chạy đồng thời nhiều luồng. Trên RK3588 có 3 lõi NPU độc lập, ta có thể khởi tạo 3 runtime contexts tương ứng với Core 0, Core 1, Core 2 để xử lý đồng thời 3 luồng video từ 3 camera, giúp Throughput FPS tăng gần gấp 3 lần mà không tăng thời gian trễ của từng camera [REPO ai/automation/tables.py:325] (Hình P.1).

### Câu 3 (áp dụng)
Tại sao mô hình YOLO26n có tổng số phép tính (5.314 GFLOPs) thấp hơn đáng kể so với YOLOv8n (8.087 GFLOPs) nhưng độ trễ chạy trên NPU RK3588 thực tế lại chậm hơn khoảng 15%?
Đáp án: Do hai nguyên nhân chính theo mô hình Roofline: (1) Cường độ tính toán (Arithmetic Intensity) thấp: Các lớp depthwise và lớp nhỏ tính toán quá ít trên mỗi byte nạp từ RAM DDR khiến NPU rơi vào vùng memory-bound; (2) Phân mảnh lớp: YOLO26n có tới 180 lớp NPU (so với 116 lớp của YOLOv8n), chi phí DMA setup và chuyển đổi ngữ cảnh phần cứng cho từng lớp nhỏ làm suy giảm hiệu năng thực tế (Hình P.2).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| P.1 | Công thức E2E latency và FPS_latency = 1000 / E2E mean | T3 | REPO ai/automation/tables.py:288 | FPS_latency = 1000 / E2E mean |
| P.1 | Phân bổ Core_mask và WorkLoad lõi 0 ở AUTO | T3 | REPO tmp/04_debug-logs/2026-10-10_yolo-phaseA/README.md:22 | cột WorkLoad cho AUTO chỉ lõi 0 |
| P.1 | ConvExSwish chỉ chạy trên lõi 0 ở CORE_0_1_2 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_CORE_0_1_2.txt | (đọc từ hình) |
| P.2 | Bảng lớp: GFLOPs đo bằng FlopCounterMode, 2 FLOP mỗi MAC | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:2 | GFLOPs (torch FlopCounterMode, 2 FLOPs per MAC) |
| P.2 | 1024 MACs INT8 mỗi chu kỳ trên mỗi lõi NPU | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| P.2 | Datasheet NPU ghi lên tới 6 TOPS | T1 | DS tr.7 | up to 6TOPs |
| P.2 | Phần trăm GFLOPs của Detect: 2.965 / 8.087 = 36.7%, 0.435 / 5.314 = 8.2% | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | (số học) |
