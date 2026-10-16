# Ghi chú chuyên đề: Hàm kích hoạt ReLU và SiLU trên NPU RK3588

## Câu hỏi mở đầu
Hàm kích hoạt ReLU và SiLU khác nhau như thế nào về mặt toán học, vi kiến trúc mạch silicon NPU RK3588 thực thi phép cắt ngưỡng (Clamp), bộ tích lũy (Accumulator) và bảng tra (LUT) ra sao, và tại sao cơ chế ghép toán tử (Operator Fusion) trong OPL lại quyết định khả năng chạy đa lõi của mô hình?

## Hình A.1 (ha-1-toan-hoc-va-do-thi) [T2 chung]
So sánh toán học, đạo hàm và đồ thị giữa ReLU và SiLU:
- ReLU (Rectified Linear Unit): f(x) = max(0, x). Đạo hàm từng đoạn f'(x) = 1 khi x > 0 và f'(x) = 0 khi x < 0. Ưu điểm là tính toán cực kỳ đơn giản (chỉ cần một phép so sánh ngưỡng), dập tắt hoàn toàn giá trị âm về 0. Nhược điểm lớn nhất là hiện tượng "dying ReLU": khi một nơ-ron nhận đầu vào âm lớn và gradient bị triệt tiêu về 0, trọng số của nó sẽ ngừng cập nhật vĩnh viễn.
- SiLU (Sigmoid Linear Unit, còn gọi là Swish-1): f(x) = x * sigmoid(x) = x / (1 + e^(-x)). Đạo hàm f'(x) = sigmoid(x) + x * sigmoid(x) * (1 - sigmoid(x)). SiLU có tính chất trơn (smooth), không đơn điệu (non-monotonic), đạt cực tiểu tại x ≈ -1.28 với f(x) ≈ -0.278. Nhờ có một vùng gradient âm nhỏ, SiLU cho phép gradient tiếp tục lan truyền, giúp việc huấn luyện mô hình sâu ổn định hơn và thường đạt độ chính xác (mAP) cao hơn ReLU. Tuy nhiên, SiLU tốn chi phí tính toán đáng kể do chứa hàm mũ e^(-x) và phép chia.
Đọc thêm: 08_ mục 8.1, 8.2; 09_ mục 9.2, 9.4. Khái niệm: Hình 8.1, Hình 9.2

## Hình A.2 (ha-2-so-do-mach-phan-cung-va-residual) [T1 RK3588]
Vi kiến trúc mạch phần cứng NPU RK3588: Mảng MAC, Bộ tích lũy (Accumulator), Mạch cắt ngưỡng Clamp, Bảng tra LUT và Nhánh cộng tắt Residual:
- Luồng tính toán bên trong khối CNA (Convolution Accelerator):
  - Mảng MAC (Multiplier-Accumulator Array): Thực hiện phép nhân chập trọng số với dữ liệu đầu vào theo từng chu kỳ (INT8 32x32 mode, 1024 MACs/lõi).
  - Bộ tích lũy (Accumulator): Cộng dồn các tích cục bộ (partial sums) từ mảng MAC vào thanh ghi nội bộ để tạo thành giá trị tổng hoàn chỉnh.
  - Nhánh cộng tắt Residual (Shortcut Add): Với các kiến trúc mạng có kết nối tắt residual (như ResNet, CSP, C2f), tensor đầu vào từ nhánh shortcut được nạp vào cộng trực tiếp với kết quả trong bộ tích lũy trước khi đi qua hàm kích hoạt, tạo thành chuỗi tính toán khép kín Conv + Add + Act mà không cần ghi ra RAM trung gian.
- Xử lý hàm kích hoạt trên silicon (DPU - Data Processing Unit):
  - Cơ chế ReLU (Clamp - Cắt ngưỡng): Mạch so sánh số nguyên cực kỳ đơn giản. Nếu bit dấu âm (x < 0), dập bit về 0; nếu x > 0, giữ nguyên. Thao tác này được thực hiện "zero-cost" (gần như không tốn thêm chu kỳ xung nhịp) ngay trên thanh ghi đầu ra của bộ tích lũy.
  - Cơ chế SiLU (Bảng tra LUT / Bộ xấp xỉ phần cứng): Hàm phi tuyến x / (1 + e^(-x)) không thể tính bằng logic cổng số học thông thường. NPU phải sử dụng bảng tra (Look-Up Table - LUT) lưu sẵn các giá trị rời rạc hoặc bộ xấp xỉ đa thức từng đoạn (piecewise linear approximation) trong DPU, đòi hỏi chu kỳ tính toán và năng lượng cao hơn nhiều.
Đọc thêm: 02_ mục 2.2, 2.3; 06_ mục 6.3. Khái niệm: Hình 2.2, Hình 2.4, Hình 6.3

## Hình A.3 (ha-3-ghep-toan-tu-va-da-loi-opl) [T1 RK3588]
Cơ chế ghép toán tử (Operator Fusion), Tài liệu OPL và Phân bổ đa lõi NPU RK3588:
- Ghép toán tử (Fused Operator) so với Toán tử rời rạc (Disjoint Operator):
  - Fused Operator (ConvolutionRelu, ConvolutionSwish, ConvolutionAddRelu): RKNN Compiler nén cả cụm Conv, Add và Kích hoạt thành 1 mã lệnh phần cứng duy nhất thực thi trọn vẹn trong bộ đệm nội bộ CBUF (384 KB mỗi lõi), loại bỏ hoàn toàn việc ghi feature map thô ra DRAM DDR rồi đọc lại.
  - Disjoint Operator (exSwish, Add rời): Khi compiler không thể ghép (hoặc mô hình tách rời), feature map phải ghi ngược ra bộ nhớ ngoài DDR, tiêu tốn băng thông truyền dữ liệu và tăng độ trễ hệ thống.
- Hỗ trợ đa lõi trong tài liệu đặc tả toán tử NPU (OPL):
  - ConvolutionRelu: Tài liệu OPL ghi rõ "多核联合: 支持" (Hỗ trợ phân bổ đa lõi). Mạch điều khiển NPU có thể tự động băm nhỏ ma trận tính toán để chia đều cho cả 3 core NPU (Core 0, 1, 2).
  - ConvolutionSwish và exSwish: Tài liệu OPL ghi rõ "多核联合: 暂不支持" hoặc "尚不支持" (Chưa hỗ trợ đa lõi). Toàn bộ khối tính toán này bị ép chạy 100% trên Core 0.
- Đo kiểm thực tế T3 và Quy tắc chọn model của đề tài:
  - Trên board RK3588S thật, mô hình YOLOv8n SiLU dồn toàn bộ 57 lớp ConvExSwish vào Core 0 (chạy 100%/0%/0%). Trong khi đó, bản YOLOv8n ReLU chia đều 3 core và giảm độ trễ NPU khoảng 35%.
  - Quy tắc đề tài (tmp/02_decisions/2026-10-11): Chỉ chọn mô hình nhanh nhất nếu mAP50-95 INT8 trên board không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm mAP; nếu không rõ ràng thì giữ nguyên YOLOv8n SiLU.
Đọc thêm: 06_ mục 6.2; 10_ mục 10.3; 11_ mục 11.2. Khái niệm: Hình 6.2, Hình 10.3, Hình 11.2

## Hiểu sai thường gặp
- "SiLU luôn vượt trội hơn ReLU trong mọi ứng dụng thực tế" -> SiLU cho độ chính xác cao hơn nhưng tốn chi phí tính toán và không hỗ trợ chạy đa lõi trên NPU RK3588 [Y6 tr.8; OPL tr.63] (Hình A.1, Hình A.3)
- "NPU RK3588 chạy mô hình SiLU nhanh gấp 3 lần khi bật cả 3 core" -> OPL ghi ConvolutionSwish là 多核联合 暂不支持, thực tế trên board cả 57 lớp ConvExSwish đều chạy 100% trên Core 0 [OPL tr.63; LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt] (Hình A.3)
- "Nhánh residual shortcut chỉ là một phép cộng toán học, không ảnh hưởng đến bộ nhớ" -> Nếu không ghép vào thanh ghi tích lũy (Accumulator), phép Add rời buộc phải ghi dữ liệu ra DDR rồi nạp lại, gây nút thắt băng thông nghiêm trọng [OPL tr.63] (Hình A.2, Hình A.3)
- "ReLU có đạo hàm xác định tại mọi điểm x" -> Đạo hàm của ReLU không xác định tại điểm gãy x = 0 (trong cài đặt số học thường gán giá trị 0 hoặc 1) [NAGEL tr.4] (Hình A.1)
- "Đọc được chi tiết vi kiến trúc bảng tra LUT của NPU RK3588 từ tài liệu nhà sản xuất" -> TRM và Datasheet chỉ liệt kê kiểu dữ liệu và op được hỗ trợ, không công bố vi kiến trúc bảng tra nội bộ [TRM1 tr.1984; DS tr.7] (Hình A.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Trình bày sự khác biệt về mặt mạch silicon giữa phép cắt ngưỡng (Clamp) của ReLU và cơ chế bảng tra (LUT) của SiLU sau khi dữ liệu đi qua mảng MAC và bộ tích lũy.
Đáp án: Sau khi mảng MAC tính toán và bộ tích lũy (Accumulator) cộng dồn partial sums, kết quả được đưa qua khối DPU. Với ReLU, mạch chỉ cần một khối so sánh ngưỡng (Clamp) đơn giản để cắt các giá trị âm về 0 mà không tốn thêm chu kỳ xung nhịp. Với SiLU, hàm phi tuyến x / (1 + e^(-x)) phức tạp đòi hỏi phải tra bảng LUT hoặc dùng bộ xấp xỉ phần cứng đa thức, làm tăng diện tích silicon và thời gian tính toán (Hình A.2).

### Câu 2 (phân biệt)
Phân biệt sự khác nhau giữa toán tử ghép (Fused Operator: ConvolutionRelu, ConvolutionSwish) và toán tử tách rời (Disjoint Operator: exSwish) về đường đi dữ liệu trong NPU.
Đáp án: Toán tử ghép (Fused Operator) giữ luồng tính toán hoàn toàn bên trong bộ đệm nội bộ CBUF và thanh ghi tích lũy của NPU, thực hiện Conv rồi áp dụng kích hoạt ngay lập tức mà không cần ghi ra RAM ngoài. Ngược lại, toán tử tách rời (Disjoint Operator) buộc NPU phải ghi feature map trung gian ra bộ nhớ RAM DDR sau lớp Conv, sau đó nạp lại vào NPU để chạy lớp kích hoạt rời, gây tiêu tốn băng thông và tăng độ trễ (Hình A.3).

### Câu 3 (áp dụng)
Theo tài liệu OPL và kết quả đo kiểm thực tế trên RK3588, tại sao mô hình YOLOv8n SiLU không thể tận dụng được sức mạnh 3 core NPU khi đặt core_mask=CORE_0_1_2?
Đáp án: Vì tài liệu OPL của Rockchip quy định toán tử ConvolutionSwish (SiLU ghép) và exSwish tạm thời chưa hỗ trợ đa lõi (多核联合: 暂不支持). Kết quả đo thực tế T3 trên board RK3588 xác nhận toàn bộ 57 lớp ConvExSwish đều bị dồn 100% vào Core 0, khiến Core 1 và Core 2 hoàn toàn không được phân bổ tính toán (Hình A.3).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| A.1 | Tên gọi Swish và SiLU là một | T1 | OPL tr.47 | Swish 函数也称为 SiLU 函数 |
| A.1 | SiLU cho độ chính xác cao hơn, ReLU có lợi thế tốc độ khi ghép lớp | T2 | Y6 tr.8 | SiLU performs with better accuracy |
| A.1 | ReLU có lợi thế tốc độ nhờ ghép vào tích chập | T2 | Y6 tr.8 | ReLU has a greater speed advantage because of its fusion into convolution |
| A.1 | Tác động của hàm kích hoạt rõ nét trên NPU do mức độ hỗ trợ phần cứng | T2 | ACTNAS tr.8 | the impact of different activations is more prominent on NPUs |
| A.1 | Trộn SiLU và ReLU để tối ưu độ trễ | T2 | ACTNAS tr.6 | LZCM1 model aims to minimize overall latency by mixing SiLU and ReLU activations |
| A.1 | Công thức và đạo hàm của ReLU và SiLU | tính | OPL tr.47 | (số học) |
| A.2 | Vi kiến trúc khối CNA và bộ tích lũy Accumulator | T1 | TRM1 tr.1985 | convolution pre-process controller, internal buffer, mac array, accumulator |
| A.2 | Khối DPU xử lý các hàm kích hoạt relu, sigmoid | T1 | TRM1 tr.1985 | Data Processing Unit mainly process the single data calculate, such as leaky_relu, relu, relux, sigmoid, tanh |
| A.2 | Vi kiến trúc bảng tra LUT của NPU | T1 | (không có) | (unknown) |
| A.3 | Ghép Convolution với Relu | T1 | OPL tr.60 | Convolution 与 Relu 融合计算 |
| A.3 | ConvolutionRelu hỗ trợ đa lõi | T1 | OPL tr.60 | 多核联合: 支持 |
| A.3 | Ghép Convolution với Swish | T1 | OPL tr.63 | Convolution 与 Swish 融合计算 |
| A.3 | ConvolutionSwish tạm chưa hỗ trợ đa lõi | T1 | OPL tr.63 | 多核联合: 暂不支持 |
| A.3 | Op exSwish chưa hỗ trợ đa lõi | T1 | OPL tr.98 | 多核联合: 尚不支持 |
| A.3 | T3: YOLOv8n 5 lớp SiLU đã huấn luyện | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | YOLOv8n 5 lớp, SiLU, đã huấn luyện |
| A.3 | T3: 57 lớp ConvExSwish chạy 100% trên core 0 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | (số học) |
| A.3 | Quy tắc: mAP50-95 INT8 không thấp hơn SiLU quá 1.0 điểm | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm |
| A.3 | Quy tắc: không rõ thì giữ YOLOv8n SiLU | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | giữ YOLOv8n SiLU |
| A.3 | Chi tiết vi kiến trúc không hỗ trợ đa lõi của ConvolutionSwish | T1 | (không có) | (unknown) |
