# Ghi chú chuyên đề: Convolution và Toán tử Add trong NPU

## Câu hỏi mở đầu
Một phép convolution chuyển từ trực quan đời thường (dò tìm nét mẫu) sang công thức toán học, các biến thể kiến trúc (Standard, DWConv, Pointwise, Group Conv, Residual Add) và mạch silicon NPU (CNA, psums, residual add, BatchNorm folding) như thế nào?

## Hình C.0 (hc-0-truc-quan-convolution) [T2 chung]
Bản chất trực quan của Convolution là hành động cầm một tấm bìa khoét lỗ nhỏ (Filter/Kernel, ví dụ 3x3) trượt khắp bức ảnh để dò tìm một đặc trưng cụ thể (ví dụ: nét thẳng đứng).
Tại mỗi vị trí dừng lại:
1. TÍCH (Nhân): Đặt tấm bìa đè lên vùng ảnh, lấy từng số của tấm bìa nhân với điểm ảnh tương ứng bên dưới.
2. CHẬP (Cộng dồn): Cộng dồn tất cả 9 kết quả nhân lại thành 1 con số duy nhất. Nếu vùng ảnh khớp với nét dọc trên tấm bìa, điểm số tính ra rất cao (ví dụ: 60 - sáng rực). Nếu không khớp, kết quả bằng 0 hoặc triệt tiêu.
Sau khi trượt hết bức ảnh, ta thu được một tấm bản đồ mới gọi là Feature Map đánh dấu những vị trí mà nét dọc xuất hiện.
Trong mạng nơ-ron sâu (CNN / YOLO), các lớp Conv nông tìm nét cạnh/góc cơ bản, các lớp Conv giữa ghép thành hình khối bộ phận, và các lớp Conv sâu ghép thành vật thể hoàn chỉnh (khuôn mặt, xe hơi, con mèo).
Đọc thêm: 01_ mục 1.2. Khái niệm: Hình C.1, Hình 1.1

## Hình C.1 (hc-1-toan-va-im2col) [T2 chung]
Một phép convolution 2D chuẩn trên tensor kích thước [H, W, Cin] với Cout bộ lọc kích thước [K, K, Cin] đòi hỏi Hout x Wout x Cout x (K x K x Cin) phép tính MAC (Multiply-Accumulate).

Trong quá trình tính, các kết quả tích nhân chập w · x được cộng dồn từng phần thành các giá trị tích lũy trung gian (partial sums, psums). Psums được lưu tạm trong các thanh ghi tích lũy (accumulator) trước khi hoàn tất toàn bộ kích thước cửa sổ để sinh ra 1 điểm ảnh hoàn chỉnh của output feature map.

Để đưa lên phần cứng tính toán song song, phép tích chập dạng cửa sổ trượt thường được chuyển đổi thành phép nhân hai ma trận tổng quát (GEMM) thông qua thao tác trải ma trận (im2col). Trong im2col, mỗi vùng receptive field kích thước K x K x Cin được duỗi thẳng thành một cột (hoặc hàng), và ma trận trọng số được nhân trực tiếp với ma trận dữ liệu đã trải.

Thao tác GEMM giúp tận dụng tối đa các mảng nhân ma trận (Systolic Array / MAC Array), nhưng đánh đổi lại bằng việc tăng bộ nhớ đệm nếu thực hiện sao chép dữ liệu tường minh; các NPU hiện đại thường thực hiện im2col ẩn (implicit GEMM) ngay trên đường nạp của bộ điều khiển tiền xử lý convolution.
Đọc thêm: 01_ mục 1.2, 1.6. Khái niệm: Hình C.0, Hình 1.1, Hình 1.5, Hình 2.2

## Hình C.2 (hc-2-cna-va-fusion) [T1 RK3588]
Bên trong mỗi lõi NPU của RK3588, khối CNA (Convolution Neural Network Accelerator) đảm nhận việc điều phối luồng tính toán convolution.

Đường đi của dữ liệu gồm: bộ điều khiển tiền xử lý convolution (CNA Controller) lấy dữ liệu từ bộ đệm nội bộ 384KB CBUF (hoặc từ DDR qua AXI master), giải nén trọng số và zero-skipping, đưa vào mảng MAC array cấu hình chế độ INT8 32x32 mode (1024 MAC mỗi chu kỳ cho mỗi lõi). Kết quả cộng dồn được đưa qua bộ tích lũy (Accumulator INT32 lưu trữ psums).

Tại bộ tích lũy, nhánh cộng tắt Residual Add (trong cấu trúc skip connection ResNet / CSPDarknet) được nối trực tiếp vào thanh ghi tích lũy để cộng dồn với kết quả tích chập trước khi đưa sang khối xử lý tiếp theo (tương ứng toán tử ghép ConvolutionAdd / ConvolutionAddRelu hỗ trợ cả 3 core NPU). Sau đó, dữ liệu chuyển tiếp sang khối DPU (Data Processing Unit) để áp dụng hàm kích hoạt (ReLU, SiLU, Leaky ReLU) và PPU (Planar Processing Unit) để thực hiện pooling nếu có.

Đồng thời, lớp Batch Normalization (BatchNorm) được gộp (fold) hoàn toàn vào trọng số và bias của Convolution trong pha build model ngoại tuyến (Offline BN Folding), biến đổi W_fused = γ·W / √(σ² + ε) và B_fused = β + γ·(B - μ) / √(σ² + ε). Toàn bộ quy trình này chạy khép kín trong nội bộ lõi NPU, giúp giảm triệt để số lần truy cập RAM DDR.
Đọc thêm: 02_ mục 2.2, 2.3; 06_ mục 6.3. Khái niệm: Hình 2.2, Hình 6.3, Hình 7.1

## Hình C.3 (hc-3-dwconv-va-pointwise) [T2 chung]
Depthwise Convolution (DWConv) và Pointwise Convolution (1x1) là hai thành phần tách rời của phép tích chập không gian và kênh, cấu thành khối Depthwise Separable Convolution kinh điển:

1. Depthwise Convolution (DWConv): Tách riêng việc lọc đặc trưng không gian (spatial filtering). Mỗi kênh đầu vào được xử lý độc lập bởi một bộ lọc 2D kích thước K x K x 1 (tổng cộng Cin bộ lọc). DWConv không có sự trộn thông tin giữa các kênh, giảm số phép tính FLOPs xuống Cin x Hout x Wout x K^2 (giảm Cout lần so với Standard Conv). Tuy nhiên, do tái sử dụng dữ liệu thấp và lượng tính toán trên mỗi byte nạp ít, DWConv có arithmetic intensity rất thấp, dễ rơi vào tình trạng nghẽn bộ nhớ (memory-bound) trên mảng MAC của NPU.

2. Pointwise Convolution (1x1 Conv): Tách riêng việc tổng hợp thông tin xuyên kênh (cross-channel mixing). Sử dụng Cout bộ lọc kích thước 1 x 1 x Cin để quét qua từng pixel. Do kích thước kernel là 1x1, không có sự tái sử dụng không gian giữa các pixel lân cận, bản chất biến đổi trực tiếp thành phép nhân ma trận thuần túy GEMM.

3. Khối Depthwise Separable Conv (DW + PW): Ghép nối một lớp DWConv 3x3 theo sau bởi một lớp Pointwise Conv 1x1. Tổng số phép tính giảm từ Hout x Wout x Cout x K^2 x Cin xuống Hout x Wout x (Cin x K^2 + Cin x Cout). Tỷ lệ FLOPs chỉ còn xấp xỉ 1/Cout + 1/K^2 (khoảng 1/9 đến 1/8 so với Standard Conv 3x3).
Đọc thêm: 01_ mục 1.4; 08_ mục 8.2. Khái niệm: Hình C.1, Hình C.4, Hình 1.4, Hình 8.2

## Hình C.4 (hc-4-group-convolution) [T2 chung]
Group Convolution (Phép tích chập nhóm) chia Cin kênh đầu vào và Cout kênh đầu ra thành G nhóm rời rạc không giao nhau (G <= min(Cin, Cout)):

Mỗi nhóm thực hiện một phép tích chập độc lập với Cin/G kênh vào và Cout/G bộ lọc kích thước K x K x (Cin/G). Tổng số tham số và số phép tính MAC của toàn bộ lớp giảm đúng G lần so với Standard Convolution: (Hout x Wout x Cout x K^2 x Cin) / G.

Phổ liên tục giữa các biến thể Convolution qua tham số nhóm G:
1. G = 1: Standard Convolution 2D thông thường. Kết nối dày đặc giữa mọi kênh đầu vào và mọi bộ lọc đầu ra, khai thác tối đa tính toàn vẹn kênh nhưng tốn chi phí tính toán cao nhất.
2. 1 < G < Cin: Group Convolution (như trong ResNeXt, ShuffleNet hoặc tùy biến backbone). Giúp giảm số tham số và cô lập các luồng biểu diễn kênh song song.
3. G = Cin = Cout: Depthwise Convolution. Trường hợp cực hạn khi số nhóm bằng đúng số kênh đầu vào, mỗi kênh tạo thành một nhóm độc lập riêng biệt.

Đánh đổi trên phần cứng NPU RK3588: RKNN hỗ trợ toán tử Convolution với thuộc tính group (OPL tr.60). Tuy nhiên, kiến trúc mảng MAC của RK3588 tối ưu cho luồng dữ liệu 32x32 mode (vector 32 phần tử). Khi Cin/G không chia hết cho 32 hoặc quá nhỏ, phần cứng NPU bị lãng phí các đơn vị tính toán MAC trống (MAC underutilization), khiến thời gian thực thi thực tế không giảm tỷ lệ thuận với mức giảm FLOPs trên giấy.
Đọc thêm: 01_ mục 1.4; 02_ mục 2.3; 06_ mục 6.2. Khái niệm: Hình C.1, Hình C.3, Hình 2.3, Hình 8.2

## Hình C.5 (hc-5-toan-tu-add-va-residual-block) [T2 chung]
Toán tử Element-wise Add và Cấu trúc khối Residual Block (ResNet / CSP / YOLO):

1. Bản chất toán học của phép cộng Element-wise Add:
Cộng trực tiếp từng phần tử tương ứng giữa hai tensor A và B có cùng kích thước [H, W, C]:
C(h, w, c) = A(h, w, c) + B(h, w, c)
Điều kiện tiên quyết: Hai tensor bắt buộc phải có cùng kích thước không gian (H, W) và cùng số lượng kênh (C). Nếu hai nhánh lệch số kênh hoặc kích thước feature map (ví dụ khi giảm chiều qua stride 2), nhánh shortcut bắt buộc phải chèn thêm một lớp Convolution 1x1 (Projection Shortcut) để chiếu khớp kích thước trước khi cộng.

2. Khối Residual Block kinh điển và Đạo hàm chống triệt tiêu gradient:
Tín hiệu đầu vào x rẽ thành hai nhánh song song:
- Nhánh chính (Residual branch): Đi qua các lớp biến đổi F(x) (chuỗi Conv 3x3, BatchNorm, ReLU).
- Nhánh tắt (Identity shortcut): Đi tắt thẳng qua, giữ nguyên vẹn 100% tín hiệu gốc x.
Tại nút cộng (ADD), hai nhánh hội tụ lại: y = F(x) + x, sau đó mới đi qua hàm kích hoạt ReLU cuối cùng.
Về mặt đạo hàm khi lan truyền ngược:
dy/dx = dF(x)/dx + 1
Số hạng hằng số +1 đảm bảo rằng ngay cả khi các lớp tích chập F(x) có đạo hàm suy giảm gần về 0 (vanishing gradient), gradient vẫn luôn có một đường cao tốc mang giá trị ít nhất là 1 để truyền ngược về các tầng nông đầu tiên, cho phép huấn luyện các mạng nơ-ron sâu hàng trăm tầng một cách ổn định.

3. Cơ chế thực thi trên phần cứng NPU RK3588 (Add rời vs Add ghép on-chip):
- Add rời (Disjoint Add): Nhánh Conv ghi kết quả ra RAM DDR, nhánh shortcut cũng nằm ở RAM DDR. NPU phải phát lệnh DMA đọc cả hai tensor vào lại lõi để cộng từng phần tử, sau đó ghi kết quả ra DDR. Quá trình này tiêu tốn gấp đôi băng thông bus bộ nhớ và làm tăng độ trễ khung hình (memory-bound).
- Add ghép on-chip (Fused ConvolutionAdd / ConvolutionAddRelu): Bộ điều khiển NPU nạp tensor của nhánh shortcut (Input1) trực tiếp vào thanh ghi tích lũy Accumulator INT32 từ bộ đệm CBUF. Phép cộng được hoàn tất ngay trên thanh ghi on-chip mà không cần ghi ra RAM DDR, sau đó chuyển thẳng sang khối DPU để áp dụng ReLU. OPL (tr.61, 63) xác nhận toán tử ConvolutionAdd và ConvolutionAddRelu được hỗ trợ phân bổ tính toán song song trên cả 3 lõi NPU của RK3588.
Đọc thêm: 01_ mục 1.5; 02_ mục 2.2; 06_ mục 6.3. Khái niệm: Hình C.2, Hình A.2, Hình 2.2, Hình 6.3

## Hiểu sai thường gặp
- "Convolution là phép toán ma trận phức tạp không thể hình dung trực quan" -> Bản chất Convolution chỉ là cầm một khuôn mẫu (Filter) trượt khắp ảnh, nhân từng cặp rồi cộng dồn để dò tìm mẫu đó [EYE tr.4] (Hình C.0)
- "Convolution trên NPU chạy trực tiếp từng vòng lặp for lồng nhau như mã C/Python" -> NPU biến đổi convolution thành implicit GEMM hoặc ánh xạ trực tiếp lên mảng systolic array / MAC array cố định [EYE tr.2; TPU tr.3] (Hình C.1, Hình 1.1)
- "Lớp Batch Normalization tốn thời gian tính toán của NPU khi suy luận" -> Batch Normalization được gộp (fold) hoàn toàn vào trọng số của lớp Convolution trước đó trong quá trình build model của RKNN-Toolkit [NAGEL tr.6; UG232 tr.142] (Hình C.2)
- "Mọi biến thể Convolution đều được 3 core NPU RK3588 chia đều tải" -> Toán tử ConvolutionSwish (SiLU) trên RKNN 2.3.2 chưa hỗ trợ đa lõi và bị dồn về Core 0, trong khi ConvRelu được chia đều cho 3 core [OPL tr.63; LOG 2026-10-10_t3-board-silu-resize/README.md] (Hình C.2, Hình 2.4)
- "Depthwise Convolution (DWConv) luôn chạy nhanh hơn Standard Convolution trên NPU" -> DWConv giảm số phép tính FLOPs nhưng có tỷ lệ tính toán trên bộ nhớ (arithmetic intensity) thấp, dễ rơi vào vùng giới hạn băng thông bộ nhớ (memory-bound) trên mảng PE [EYE tr.4; SURV tr.19] (Hình C.3, Hình 1.4)
- "Group Convolution chia càng nhiều nhóm thì NPU chạy càng nhanh" -> Khi Cin/G nhỏ hơn kích thước 32 của mảng MAC RK3588, phần cứng bị thiếu tải (underutilized PE) làm giảm hiệu suất thực tế [TRM1 tr.2001; OPL tr.60] (Hình C.4)
- "Phép cộng ADD trong khối Residual có thể cộng bất kỳ 2 tensor nào" -> Hai tensor bắt buộc phải có cùng kích thước [H, W, C]; nếu lệch kênh hoặc kích thước không gian, phải có một lớp Conv 1x1 để chiếu khớp kích thước trước khi cộng [MOBONE tr.4; OPL tr.61] (Hình C.5)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Tại sao trong ví dụ số của Hình C.0, khi vùng ảnh có nét thẳng đứng ở giữa ([0, 10, 0]), điểm số sau phép Tích Chập lại ra tới 60 trong khi vùng toàn số 0 chỉ ra kết quả là 0?
Đáp án: Vì bộ lọc Filter có trọng số dương (+2) đúng ở cột giữa trùng khớp với cột điểm sáng (10) của ảnh, nên phép nhân sinh ra 20 ở cả 3 hàng (tổng là 60). Đây là cơ chế cộng hưởng để báo hiệu cho mạng nơ-ron biết vị trí có nét thẳng đứng xuất hiện (Hình C.0).

### Câu 2 (phân biệt)
Phân biệt sự khác nhau giữa Convolution tiêu chuẩn (3x3), Depthwise Convolution (DWConv) và Pointwise Convolution (1x1) về mặt lọc không gian và trộn kênh.
Đáp án: Convolution tiêu chuẩn (3x3) kết hợp đồng thời cả lọc không gian và trộn kênh trên toàn bộ Cin và Cout. Depthwise Convolution (3x3) chỉ thực hiện lọc không gian độc lập trên từng kênh riêng lẻ (không trộn kênh). Pointwise Convolution (1x1) không thực hiện lọc không gian mà chỉ trộn thông tin xuyên kênh giữa các điểm ảnh tương ứng (Hình C.1, Hình C.3).

### Câu 3 (áp dụng)
Khi một khối ResNet có nhánh tắt Residual Add kết nối sau phép tích chập Conv 2D, khối CNA của NPU RK3588 xử lý phép cộng này ở đâu và có phải ghi ra RAM DDR không?
Đáp án: Phép cộng Residual Add được thực hiện trực tiếp tại thanh ghi tích lũy (Accumulator INT32) ngay sau mảng MAC của khối CNA trước khi chuyển tiếp sang DPU (toán tử ConvolutionAdd / ConvolutionAddRelu). Toàn bộ phép cộng chạy on-chip khép kín trong lõi NPU mà không cần ghi hay đọc lại dữ liệu từ RAM DDR (Hình C.2, Hình C.5).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| C.0 | Bản chất trượt và cộng dồn đặc trưng | T2 | EYE tr.4 | CR2 psums are reduced into one ofmap pixel |
| C.1 | Công thức MAC của Convolution | T2 | EYE tr.4 | CR2 psums are reduced into one ofmap pixel |
| C.1 | Thao tác nhân ma trận trong NPU | T2 | TPU tr.3 | 256x256 MACs |
| C.2 | Khối CNA và thứ tự phần cứng trong lõi | T1 | TRM1 tr.1985 | convolution pre-process controller, internal buffer, mac array, accumulator |
| C.2 | Khối DPU xử lý hàm kích hoạt | T1 | TRM1 tr.1985 | Data Processing Unit mainly process the single data calculate, such as leaky_relu, relu, relux, sigmoid, tanh |
| C.2 | Bộ đệm CBUF 384KB mỗi lõi | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| C.2 | Mảng MAC INT8 32x32 mode | T1 | TRM1 tr.2001 | Int8 mac array 32x32 mode |
| C.2 | Gộp toán tử Conv + Activation | T1 | UG232 tr.142 | Conv+Activation+Add |
| C.2 | ConvolutionSwish chưa hỗ trợ đa lõi | T1 | OPL tr.63 | 多核联合: 暂不支持 |
| C.2 | Gộp toán tử ConvolutionAdd đa lõi | T1 | OPL tr.61 | Convolution 与 Add 融合计算, Output = Add(Conv(Input0), Input1) |
| C.2 | Gộp toán tử ConvolutionAddRelu đa lõi | T1 | OPL tr.63 | Convolution 与 Add 及 Relu 融合计算, Output = Relu(Add(Conv(Input0), Input1)) |
| C.2 | Gộp Batch Normalization trước khi lượng tử | T2 | NAGEL tr.6 | Batch normalization folding |
| C.3 | Khối cơ bản Depthwise và Pointwise | T2 | MOBONE tr.4 | MobileNet-V1 [31] block of 3x3 depthwise convolution followed by 1x1 pointwise convolutions |
| C.3 | Giảm độ phức tạp tính toán của Depthwise | T2 | SURV tr.19 | depthwise convolutions to significantly reduce computational complexity |
| C.3 | Cường độ tính toán thấp và psums | T2 | EYE tr.4 | CR2 psums are reduced into one ofmap pixel |
| C.4 | Thuộc tính group trong Convolution NPU | T1 | OPL tr.60 | • group: int |
| C.4 | Khối MAC 32x32 của RK3588 | T1 | TRM1 tr.2001 | Int8 mac array 32x32 mode |
| C.4 | Group convolution và phân nhánh kiến trúc | T2 | MOBONE tr.4 | reparameterizable skip connection [13] with batchnorm along |
| C.5 | Phép cộng nhánh tắt trong khối cơ bản | T2 | MOBONE tr.4 | reparameterizable skip connection [13] with batchnorm along |
| C.5 | Ghép toán tử Convolution với Add | T1 | OPL tr.61 | Convolution 与 Add 融合计算, Output = Add(Conv(Input0), Input1) |
| C.5 | Ghép toán tử ConvolutionAddRelu đa lõi | T1 | OPL tr.63 | Convolution 与 Add 及 Relu 融合计算, Output = Relu(Add(Conv(Input0), Input1)) |
