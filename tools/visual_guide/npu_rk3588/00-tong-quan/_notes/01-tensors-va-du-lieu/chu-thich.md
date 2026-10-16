# Ghi chú chuyên đề: Tensors, Kênh dữ liệu và Kiểu số học trong NPU

## Câu hỏi mở đầu
Tensor và Channel (kênh) trong mạng nơ-ron là gì, quan hệ giữa số channel và số bộ lọc (filter) diễn ra như thế nào? NPU RK3588 hỗ trợ những kiểu dữ liệu số học nào (FP16, INT8, INT4, BF16), và việc giảm bit cùng căn chỉnh kênh (sub-channel 32) quyết định hiệu năng phần cứng ra sao?

## Hình T.1 (ht-1-ban-chat-channel) [T2 chung]
Bản chất của Channel trong mạng nơ-ron và phép tích chập:
- Định nghĩa mặt phẳng 2D: Một tensor đặc trưng (feature map) có dạng [C, H, W], trong đó C là số channel và mỗi channel là một ma trận 2D kích thước H x W đại diện cho một mặt phẳng kích hoạt (Eyeriss mô tả: "multiple 2D planes, i.e., channels"). Ở tầng đầu vào, channel đại diện cho các kênh màu vật lý (ví dụ ảnh RGB có 3 channels: Đỏ, Xanh lá, Xanh dương). Ở các tầng ẩn tiếp theo, mỗi channel đại diện cho một bản đồ kích hoạt của một loại đặc trưng trừu tượng được trích xuất (mép cạnh, góc, vân bề mặt, kết cấu, bộ phận vật thể).
- Quan hệ giữa Channel và Filter trong tích chập:
  - Một bộ lọc 3D (filter / kernel) có kích thước [C_in, K, K]. Để sinh ra 1 channel duy nhất ở đầu ra, bộ lọc này phải quét qua toàn bộ C_in channels đầu vào, thực hiện nhân tương ứng trên từng lát cắt 2D rồi cộng dồn toàn bộ lại xuyên kênh (channel reduction sum).
  - Do đó, số lượng bộ lọc 3D độc lập (M) luôn bằng đúng số lượng channel của feature map đầu ra (Eyeriss ghi rõ: "# of 3D filters / # of ofmap channels" và "# of ifmap/filter channels"). Trọng số của lớp tích chập có kích thước tổng thể là [C_out, C_in, K, K].
- Các biến thể thao tác trên channel:
  - Standard Convolution: Trộn thông tin không gian (K x K) đồng thời tổng hợp xuyên kênh (C_in sang C_out).
  - Pointwise Convolution (1x1 Conv): Không quét không gian lân cận (K = 1), chỉ làm nhiệm vụ tổ hợp tuyến tính và thay đổi số lượng channel (tăng hoặc giảm chiều kênh).
  - Depthwise Convolution (DWConv): Mỗi channel đầu vào đi qua một bộ lọc 2D riêng (groups = C_in), không có sự tổng hợp xuyên kênh.
Đọc thêm: 01_ mục 1.2; 08_ mục 8.1. Khái niệm: Hình 1.2, Hình 1.4

## Hình T.2 (ht-2-channel-tren-npu-rk3588) [T1 RK3588]
Tổ chức Channel trên phần cứng NPU RK3588 và lượng tử hóa Per-Channel:
- Căn chỉnh Channel trên mảng phần cứng (Hardware Tiling): Mảng PE và bộ đệm CBUF của NPU RK3588 được thiết kế để xử lý dữ liệu theo từng khối song song channel (ví dụ sub-channel bằng 16, 32 hoặc 64). Trong bảng bố cục ma trận hiệu năng cao (UG232 Table 3-5), các chiều dữ liệu ma trận A, B đều được chia theo các khối channel như [K/32, M, 32] hoặc [N/64, K/32, 64, 32]. Khi số channel của mô hình là bội số của 32, NPU đạt hiệu suất lấp đầy mảng MAC tối đa.
- Lượng tử hóa Per-Channel so với Per-Layer trong RKNN-Toolkit2:
  - Per-Layer (Per-Tensor): Toàn bộ các channel trong một lớp dùng chung một cặp tham số scale và zero-point ("Per-Layer quantization quantizes all channels of a network layer as a whole").
  - Per-Channel: Mỗi output channel (tương ứng với một bộ lọc weight riêng biệt) được cấp riêng một tham số scale và zero-point ("Per-Channel quantization is only applied to the weights"). Việc này giúp mô hình INT8 thích ứng với các filter có dải động biên độ khác biệt lớn mà không làm tăng độ phức tạp của mạch tích chập.
  - Ràng buộc Activation: RKNN chỉ áp dụng Per-Channel cho trọng số (weights), còn activation và giá trị trung gian bắt buộc dùng Per-Layer, vì phần cứng NPU cộng dồn tích lũy xuyên kênh đầu vào trong mảng MAC trước khi nhân scale đầu ra.
- Giới hạn Channel trong toán tử NPU (OPL): Một số toán tử nâng cao trên NPU có giới hạn cụ thể về kích thước channel, ví dụ exSDPAttention giới hạn channel trong khoảng (0, 8192], hay Softmax trên NPU thực hiện trên trục channel và width (axis 1, 3).
Đọc thêm: 02_ mục 2.2; 03_ mục 3.2; 04_ mục 4.2. Khái niệm: Hình 2.2, Hình 3.2, Hình 4.2

## Hình T.3 (ht-3-phan-loai-va-tradeoff) [T2 chung]
Kiểu dữ liệu số trong mạng nơ-ron chia thành hai họ: số dấu phẩy động (FP32, FP16, BF16) và số nguyên cố định hay lượng tử (INT8, INT4, INT16). Với họ số nguyên, NAGEL mô tả lưới lượng tử đều có kích thước 2^b mức, tách nhánh có dấu và không dấu. Với họ dấu phẩy động, bộ nguồn chỉ cho tên kiểu, độ rộng và dải giá trị của FP16 (-65504 đến 65504); cấu trúc bit chi tiết theo từng trường (bit dấu, số mũ, phần định trị) không có trong bộ nguồn nên hình đánh dấu unknown, không đoán.
Đánh đổi cốt lõi khi giảm số bit: chuyển sang số nguyên từ 4 bit trở xuống về lý thuyết giảm bộ nhớ và độ trễ tới 16 lần, thực tế thường đạt 4 đến 8 lần; nhân INT8 tốn ít năng lượng và ít diện tích hơn nhân dấu phẩy động 16 bit IEEE 754. Về độ chính xác, W8A8 thường nằm trong khoảng 1% so với FP32, nhưng 4 bit có thể sụp mô hình: EfficientDet-D1 với W4A8 per-tensor chỉ còn 0.31 AP, và YOLOv5s lượng tử 4-bit chỉ còn 7.0% mAP.
Đọc thêm: 03_ mục 3.1, 3.2. Khái niệm: Hình 3.1, Hình 3.2

## Hình T.4 (ht-4-ho-tro-phan-cung-rk3588) [T1 RK3588]
Khả năng hỗ trợ kiểu dữ liệu trên RK3588 tách thành hai cấp: mảng MAC của silicon và bộ công cụ RKNN. Ở cấp silicon, mỗi lõi có thông lượng MAC trên mỗi chu kỳ tùy kiểu số: INT4 2048, INT8 1024, INT16/FP16/BF16 512, TF32 256; TRM ghi kèm hậu tố "x3" ứng với ba lõi. Datasheet nói NPU hỗ trợ INT4/INT8/INT16/FP16 hybrid và "up to 6TOPs"; đây là con số vendor, còn phép tính 1024 x 3 x 2 x 1 GHz = 6.144 TOPS là số học của bộ hình (quy ước 2 phép mỗi MAC lấy từ T2 BAMB tr.1, tần số 1 GHz chỉ là ví dụ vì tần số tối đa ghi TBD). Ở cấp toolkit, rknn.config mặc định lượng tử w8a8 với float_dtype float16; khi không lượng tử, model float được chuyển weight từ float32 sang float16 với độ mất chính xác gần như bằng không, vì NPU không hỗ trợ tính FP32. w4a16 và w8a16 đều ghi dành cho chip khác, không có đường qua rknn.config cho RK3588; riêng đường Matmul C API thì hỗ trợ int4, int8 và float16.
Đọc thêm: 02_ mục 2.3, 2.4; 04_ mục 4.1. Khái niệm: Hình 2.3, Hình 3.4, Hình 4.1, Hình 6.3

## Hiểu sai thường gặp
- "Số channel đầu ra (C_out) bằng với số channel đầu vào (C_in) của lớp tích chập" -> Số channel đầu ra được quyết định hoàn toàn bởi số lượng bộ lọc 3D (filters) độc lập được cấu hình cho lớp đó, không phụ thuộc vào C_in [EYE tr.3] (Hình T.1)
- "Lượng tử hóa Per-Channel có thể áp dụng tùy ý cho cả activation trên RKNN" -> RKNN chỉ hỗ trợ Per-Channel cho weights; activation và các giá trị trung gian bắt buộc lượng tử theo Per-Layer [UG232 tr.120] (Hình T.2)
- "Chọn số channel bất kỳ lẻ (như 37, 53) đều chạy nhanh như nhau trên NPU" -> Mảng MAC và layout ma trận NPU RK3588 chia khối kênh theo bội số 16 hoặc 32 (như [K/32, M, 32]); số channel không chia hết sẽ buộc compiler phải chèn thêm padding làm lãng phí bộ nhớ và giảm thông lượng tính toán [UG232 tr.49] (Hình T.2)
- "Depthwise Convolution có số channel đầu ra tùy ý" -> Trong DWConv chuẩn, mỗi filter chỉ tương ứng với 1 channel đầu vào duy nhất (groups = C_in), do đó số channel không bị trộn xuyên kênh [SURV tr.7] (Hình T.1)
- "Tài liệu kỹ thuật giải thích chi tiết mạch gom kênh nội bộ của NPU" -> TRM và tài liệu RKNN chỉ công bố đặc tả layout shape và danh mục op, không công bố vi kiến trúc cây cộng dồn channel [TRM1 tr.1984; UG232 tr.49] (Hình T.2)
- "NPU RK3588 chạy suy luận bằng dữ liệu FP32 nguyên bản" -> NPU không hỗ trợ tính toán FP32; khi không lượng tử, weight được chuyển từ float32 sang float16 với độ mất chính xác gần như bằng không [UG232 tr.131, tr.165] (Hình T.4)
- "Con số 6 TOPS áp dụng cho mọi kiểu dữ liệu" -> Datasheet chỉ ghi "up to 6TOPs" cho NPU; thông lượng MAC/chu kỳ giảm một nửa ở 16 bit (512 so 1024) và gấp đôi ở INT4 (2048); 6.144 TOPS là phép tính của bộ hình với quy ước 2 phép mỗi MAC [DS tr.7; TRM1 tr.1984; BAMB tr.1] (Hình T.4)
- "RK3588 chạy model INT4, BF16 hay TF32 qua rknn.config" -> danh sách quantized_dtype chỉ có w8a8 không bị giới hạn sang chip khác; w4a16 và w8a16 đều ghi chip khác [API232 tr.7] (Hình T.4)
- "INT4 luôn tốt hơn INT8 vì nén nhẹ đi một nửa" -> 4 bit có thể sụp mô hình thị giác: YOLOv5s lượng tử 4-bit chỉ còn 7.0% mAP, và EfficientDet-D1 W4A8 per-tensor còn 0.31 AP [QYOLO tr.2; NAGEL tr.17] (Hình T.3)
- "Đọc được cấu trúc bit (dấu, số mũ, định trị) của FP16 và BF16 từ bộ tài liệu" -> bộ nguồn chỉ cho tên kiểu, độ rộng và dải giá trị FP16 (-65504 đến 65504), không cho cấu trúc bit [TRM1 tr.1984; DS tr.11; UG232 tr.133] (Hình T.3)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Tại sao khi thực hiện phép tích chập tiêu chuẩn từ một feature map có 64 channels để tạo ra một feature map có 128 channels, kích thước tensor trọng số của lớp đó phải là 4 chiều [128, 64, K, K]?
Đáp án: Vì để tạo ra 128 channels đầu ra, mạng cần 128 bộ lọc 3D độc lập. Mỗi bộ lọc 3D phải quét qua đầy đủ 64 channels của đầu vào để cộng dồn thông tin xuyên kênh, nên mỗi bộ lọc cần 64 lát cắt kích thước K x K. Tổng số trọng số là 128 x 64 x K x K [EYE tr.3] (Hình T.1).

### Câu 2 (phân biệt)
Phân biệt sự khác nhau giữa Per-Channel quantization và Per-Layer quantization trong RKNN-Toolkit2 đối với tensor trọng số (weight) và activation.
Đáp án: Per-Layer áp dụng chung một giá trị scale và zero-point cho toàn bộ các channel trong lớp. Per-Channel gán cho mỗi output channel của weight một scale và zero-point riêng, giúp giữ độ chính xác cao hơn khi phân phối trọng số giữa các filter chênh lệch nhau. RKNN chỉ hỗ trợ Per-Channel cho weight; activation bắt buộc phải dùng Per-Layer vì các channel đầu vào được cộng tích lũy xuyên kênh trong phần cứng MAC [UG232 tr.120; NAGEL tr.16] (Hình T.2).

### Câu 3 (áp dụng)
Khi thiết kế một mạng nơ-ron tùy chỉnh chạy trên NPU RK3588, tại sao các kỹ sư thường làm tròn số channel ở các tầng ẩn thành bội số của 32 (ví dụ 32, 64, 128, 256) thay vì chọn các số lẻ như 50 hay 100?
Đáp án: Vì phần cứng NPU RK3588 tổ chức mảng MAC và layout bộ nhớ theo các khối channel sub-K = 32 (Table 3-5 trong UG232 quy định shape hiệu năng cao như [K/32, M, 32]). Nếu số channel chia hết cho 32, NPU đạt 100% hiệu suất tính toán song song; nếu chọn số lẻ, compiler phải chèn zero-padding gây tốn dung lượng bộ đệm CBUF và lãng phí chu kỳ tính toán [UG232 tr.49] (Hình T.2).

### Câu 4 (so sánh)
Phân biệt FP16 và INT8 trên RK3588 về thông lượng phần cứng và dải giá trị biểu diễn.
Đáp án: Cả hai là kiểu phần cứng được TRM liệt kê, nhưng FP16 chạy 512 MAC mỗi chu kỳ mỗi lõi còn INT8 chạy 1024, tức INT8 gấp đôi. FP16 biểu diễn dấu phẩy động với dải -65504 đến 65504 (vượt dải thì tràn), còn INT8 là số nguyên trên lưới lượng tử đều 2^8 = 256 mức, có dấu hoặc không dấu [TRM1 tr.1984; UG232 tr.133; NAGEL tr.4, tr.5] (Hình T.3, Hình T.4).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| T.1 | Channel là các mặt phẳng 2D trong tensor | T2 | EYE tr.3 | multiple 2D planes, i.e., channels |
| T.1 | Số channel của ifmap và filter | T2 | EYE tr.3 | # of ifmap/filter channels |
| T.1 | Số bộ lọc 3D bằng số channel của ofmap | T2 | EYE tr.3 | # of 3D filters / # of ofmap channels |
| T.1 | Cấu trúc tensor 4D và phép nhân tích chập | tính | EYE tr.3 | (số học) |
| T.2 | Per-Channel chỉ áp dụng cho weight | T1 | UG232 tr.120 | Per-Channel quantization is only applied to the weights |
| T.2 | Per-Layer lượng tử hóa toàn bộ channel của một lớp | T1 | UG232 tr.120 | Per-Layer quantization quantizes all channels of a network layer as a whole |
| T.2 | Khuyến nghị dùng per-channel cho weight khi phần cứng hỗ trợ | T2 | NAGEL tr.16 | If supported by the HW/SW stack then it is favorable to use per-channel quantization for weights. |
| T.2 | Bố cục ma trận căn chỉnh channel K/32 cho RK3588 | T1 | UG232 tr.49 | [K/32,M,32] |
| T.2 | exSDPAttention giới hạn channel trong khoảng (0, 8192] | T1 | OPL tr.104 | channel ∈ (0, 8192] |
| T.2 | Softmax trên NPU theo trục channel và width | T1 | OPL tr.89 | 做 softmax 的轴: 1,3，即 channel 和 width 方向 |
| T.3 | Hai họ dữ liệu: dấu phẩy động và số nguyên hẹp | T2 | TPU tr.1 | transforms floating-point numbers into narrow integers |
| T.3 | Lưới lượng tử đều 2^b mức | T2 | NAGEL tr.4 | map it to the unsigned integer grid |
| T.3 | Lưới có dấu và không dấu | T2 | NAGEL tr.5 | for unsigned integers |
| T.3 | TRM liệt kê INT4/8/16, float 16, Bfloat 16, tf32 | T1 | TRM1 tr.1984 | Support integer 4, integer 8, integer 16, float 16, Bfloat 16 and tf32 operation |
| T.3 | Datasheet tr.11 thêm Bfloat16, tf32 | T1 | DS tr.11 | Support integer 4, integer 8, integer 16, float 16, Bfloat 16 and tf32 operation |
| T.3 | Dải giá trị FP16 -65504 đến 65504 | T1 | UG232 tr.133 | exceeding the FP16 expression range (-65504～65504) |
| T.3 | Không lượng tử: weight float32 sang float16, gần như không mất chính xác | T1 | UG232 tr.165 | convert the weights from float32 to float16, with almost no accuracy loss |
| T.3 | Giảm bit: bộ nhớ và độ trễ giảm tới 16x, thực tế 4x đến 8x | T2 | GHOLAMI tr.1 | 4x to 8x are often realized in practice |
| T.3 | Nhân INT8 tốn ít năng lượng và diện tích hơn nhân FP16 IEEE 754 | T2 | TPU tr.1 | 6X less energy and 6X less area than IEEE 754 16-bit floating-point multiplies |
| T.3 | W8A8 trong khoảng 1% so FP32; weight 4-bit mất thêm ít | T2 | NAGEL tr.25 | 8-bit quantization of weights and activations within only 1% |
| T.3 | EfficientDet-D1 COCO AP: FP32 40.08, W8A8 38.29, W4A8 0.31 | T2 | NAGEL tr.17 | EfficientDet-D1 40.08 38.29 0.31 |
| T.3 | YOLOv5s PTQ 4-bit chỉ còn 7.0% mAP | T2 | QYOLO tr.2 | 4-bit quantized YOLOv5s employing Percentile achieves only 7.0% mAP |
| T.3 | Cấu trúc bit (dấu, số mũ, định trị) của FP32/FP16/BF16 | T2 | (không có) | (unknown) |
| T.4 | INT8 1024x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| T.4 | INT4 2048x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 2048x3 integer 4 MAC operation per cycle |
| T.4 | INT16 512x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 512x3 integer 16 MAC operations per cycle |
| T.4 | FP16 512x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 512x3 float 16 MAC operations per cycle |
| T.4 | BF16 512x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 512x3 bfloat 16 MAC operations per cycle |
| T.4 | TF32 256x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 256x3 tf32 MAC operation per cycle |
| T.4 | Tổng 3 core 6144, 3072, 1536, 768 | tính | TRM1 tr.1984 | (số học) |
| T.4 | NPU hỗ trợ INT4/INT8/INT16/FP16 hybrid, "up to 6TOPs" | T1 | DS tr.7 | computing power is up to 6TOPs |
| T.4 | Tần số tối đa NPU ghi TBD | T1 | DS tr.31 | Max NPU frequency NA NA TBD MHz |
| T.4 | Quy ước TOPS bằng hai lần số MAC nhân tần số | T2 | BAMB tr.1 | twice the number of MAC units multiplied by the clock frequency |
