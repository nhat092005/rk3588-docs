# Phần 8: Thiết kế model

## Câu hỏi mở đầu
Khi thiết kế hay chọn model cho NPU RK3588, tiêu chí nào đã có nguồn T1 (vendor), T2 (paper) hoặc T3 (đo của chúng ta), và điều gì (re-parameterization, SiLU so với ReLU, NAS, sửa kiến trúc YOLO) vẫn là unknown trên RK3588?

## Hình 8.1 (h8-1-reparam) [T2 chung]
Structural re-parameterization huấn luyện một khối nhiều nhánh (Conv 3x3 + BN, Conv 1x1 + BN, identity + BN) rồi gộp thành một Conv 3x3 có bias để suy luận; phép gộp đòi hỏi cùng stride và padding của lớp 1x1 ít hơn lớp 3x3 một pixel. Sau gộp, thân RepVGG chỉ còn một loại op là Conv 3x3 + ReLU; YOLOv6 (Y6) dùng RepBlock lúc train và RepConv lúc inference, MobileOne bỏ hết nhánh lúc inference, và cả ba bài đo tốc độ trên GPU, CPU hay iPhone 12, không có NPU. Tác dụng phụ: với PTQ 8-bit symmetric trong PyTorch-Quantization của NVIDIA, RepVGG-A0 tụt từ 72.4 xuống 52.2 (top-1) và YOLOv6s-RepVGG từ 42.4 xuống 35.0 (mAP), còn QARepVGG (bỏ BN khỏi nhánh identity và 1x1, thêm một BN sau phép cộng) chỉ tụt 1.8 và 1.3. Liên hệ RK3588: Conv và ConvolutionRelu có mục NPU trong OPL nên dạng sau gộp biểu diễn được (suy ra của bộ hình), nhưng RK3588 có nhanh hơn hay INT8 có tụt như QAREP hay không là unknown vì không có nguồn T1 hay T3, và QAREP đo bằng toolkit khác với RKNN; fusion Conv trên RK3588 xem Hình 6.3.
Đọc thêm: 08_ mục 8.1, 8.5; 03_ mục 3.8.
Khái niệm: Hình 3.5, Hình 6.3
Hình gốc: ../../npu_study/images/08_model_design_for_npu/repvgg_p5_fig4.png (REPVGG tr.5, Figure 4; nhúng vì phần (B) cho thấy cách zero-pad kernel 1x1 và identity lên 3x3 rồi cộng, điều mà sơ đồ cấu trúc vẽ lại không biểu diễn được)

## Hình 8.2 (h8-2-checklist) [T1 RK3588]
Checklist là một cây năm câu hỏi (op nào có mục NPU, op nào chia ba NPU core, chọn activation, đạt tiêu chí hiệu năng UG232 chưa, có dùng re-param, NAS hay sửa kiến trúc không), và mỗi lá mang một huy hiệu tier cùng nguồn; chỉ T1 đủ để nói một op có mục NPU hay không. Điều T3 cho thấy chỉ đúng cho một model và một board: trong YOLOv8n ngẫu nhiên nc=5 INT8 ở CORE_0_1_2, 57 lớp ConvExSwish chỉ chạy lõi 0 còn ConvRelu và ConvReluAdd chia ba lõi, khớp với cột 多核联合 của OPL (ConvolutionSwish 暂不支持, ConvolutionRelu 支持); ReLU mới có số FP32 (mAP50-95 0.5835 so với 0.5908 của SiLU, một seed), còn INT8 trên board chưa có. Các paper T2 về activation, NAS và YOLO cho Rockchip được ghi kèm chip hoặc board mà chúng đo (RK3588, RK3568, RK3566, NPU không nêu tên), không được suy sang RK3588. Ô unknown liệt kê điều không nguồn nào trả lời.
Đọc thêm: 00_ mục 7.3; 08_ mục 8.2 đến 8.5; 09_ mục 9.5. Số đo: Hình 10.1, Hình 10.3, Hình 10.7
Khái niệm: Hình 6.2, Hình 6.3, Hình 8.1, Hình 9.4

## Hiểu sai thường gặp
- "ReLU luôn nhanh hơn SiLU trên mọi NPU" -> chỉ có số đo cho từng thiết bị đã ghi: trên RK3588 là một model YOLOv8n ngẫu nhiên (ConvRelu chia ba lõi, ConvExSwish chỉ lõi 0 ở CORE_0_1_2), còn các paper đo trên Tesla T4, iPhone 12 hoặc NPU không nêu tên; INT8 AP của ReLU trên board chưa có [LOG 2026-10-10_t3-board-silu-resize/README.md; Y6 tr.8; ACTNAS tr.1, 3] (Hình 8.2, Số đo: Hình 10.1, Hình 10.7)
- "Re-param luôn có lợi cho INT8" -> QAREP đo ngược lại cho RepVGG: A0 72.4 xuống 52.2, YOLOv6s-RepVGG 42.4 xuống 35.0 dưới PTQ 8-bit symmetric; QARepVGG sửa bằng cách đổi vị trí BN [QAREP tr.1, 7] (Hình 8.1)
- "Re-param làm RK3588 nhanh hơn" -> REPVGG chỉ nêu giả thuyết rằng chip chuyên dụng có thể nhanh hơn vì ít loại op, không có số đo; trên RK3588 là unknown [REPVGG tr.2] (Hình 8.1)
- "Số tăng tốc hay độ chính xác của paper trên RK3566 hoặc RK3568 bằng RK3588" -> RK66 chạy FP32 trên RK3566 vì INT8 cho kết quả sai, LNB chỉ có FPS trên RTX 3090 và đếm lỗi trên 20 ảnh ở RK3568, và EDGE cho thấy cùng loại model chạy khác nhau theo SoC (Nano: RK3568 34 đến 79 ms, RK3588 (chế độ single-core NPU, EDGE tr.5) 21 đến 30 ms) [RK66 tr.4; LNB tr.20; EDGE tr.5] (Hình 8.2)
- "SiLU không chạy được trên NPU RK3588" -> có op: OPL có ConvolutionSwish, T3 có 57 lớp ConvExSwish trên NPU; điều kiện đi kèm là OPL ghi 暂不支持 đa lõi và T3 thấy chỉ lõi 0 ở CORE_0_1_2 [OPL tr.63; LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt] (Hình 8.2)
- "Upsample chạy trên NPU như Resize" -> phần NPU của OPL không có mục Upsample (chỉ có mục CPU 4.67); Resize chỉ nhận phóng đại nguyên 2 đến 8 lần; một model T3 cho Resize nearest 2x Target NPU, trong khi UG232 tr.176 nói khác và hai tài liệu chưa được phân xử [OPL tr.87, 329; UG232 tr.176] (Hình 8.2, Hình 6.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao RepVGG lúc deploy chỉ còn một Conv 3x3, phép gộp cần điều kiện gì, và theo QAREP vì sao PTQ làm nó tụt mạnh?
Đáp án: Mỗi BN và conv đứng trước gộp thành conv có bias, identity coi như conv 1x1 với ma trận đơn vị; bias cuối là tổng ba bias, kernel 3x3 cuối là kernel 3x3 cộng hai kernel 1x1 đặt ở điểm giữa. Điều kiện: cùng stride, padding của lớp 1x1 ít hơn lớp 3x3 một pixel. QAREP nêu BN của từng nhánh đổi phương sai nên cộng ba nhánh làm phương sai tăng, và thiết kế cấu trúc của RepVGG dễ sinh trọng số outlier không kiểm soát được; QARepVGG bỏ BN khỏi nhánh identity và 1x1 và thêm một BN sau phép cộng [REPVGG tr.5; QAREP tr.3, 4, 5] (Hình 8.1)
### Câu 2 (phân biệt)
Phân biệt bằng chứng về SiLU và ReLU đến từ OPL (T1), từ T3 trên board và từ paper T2: mỗi loại cho biết điều gì và không cho biết điều gì về RK3588?
Đáp án: OPL cho biết ConvolutionSwish và ConvolutionRelu là hai op NPU và ghi đa lõi 暂不支持 so với 支持, nhưng không cho số độ trễ. T3 cho thấy trong một model YOLOv8n ngẫu nhiên, ở CORE_0_1_2, 57 lớp ConvExSwish chỉ chạy lõi 0 còn ConvRelu và ConvReluAdd chia ba lõi, nhưng chỉ một model, một board và chưa có AP INT8 (FP32: ReLU 0.5835, SiLU 0.5908). Y6 và ACTNAS cho thấy ReLU nhanh hơn SiLU trên Tesla T4 và các NPU không nêu tên, không phải RK3588 [OPL tr.60, 63; LOG 2026-10-10_t3-board-silu-resize/README.md; REPO ai/automation/leaderboards/sfchd_5class.csv; Y6 tr.8; ACTNAS tr.1, 3] (Hình 8.2, Số đo: Hình 10.1, Hình 10.7)
### Câu 3 (áp dụng)
Neck của model PPE cần phóng đại feature map. Theo nguồn của hình, chọn op nào, kiểm điều kiện nào, và phần nào chưa thể quyết?
Đáp án: Dùng Resize (có mục NPU) với phóng đại nguyên 2 đến 8 lần theo H và W, mode nearest hoặc linear, thay vì Upsample (không có mục NPU, chỉ có mục CPU). Một model T3 cho Resize nearest 2x chạy NPU ở optimization_level 1, 2, 3, nhưng UG232 tr.176 nói NPU chưa hỗ trợ Resize cấp phần cứng và optimization_level=2 đưa Resize về CPU; hai nguồn chưa phân xử, nên phải kiểm lại bằng bảng lớp của chính model (eval_perf). Chưa thử bilinear hay FP16 [OPL tr.87, 329; UG232 tr.176; LOG 2026-10-10_t3-board-silu-resize/README.md] (Hình 8.2, Hình 6.2)
### Câu 4 (áp dụng)
Một paper báo model YOLO sửa kiến trúc nhanh hơn trên RK3566 hoặc RK3568. Có dùng nó để chọn kiến trúc cho RK3588 được không, và các tiêu chí nào của UG232 dùng để kiểm từng lớp?
Đáp án: Không: RK66 chạy FP32 trên RK3566 và không sửa model, LNB không có độ trễ NPU ở RK3568, EDGE cho thấy cùng model có độ trễ khác nhau theo SoC, và DAHD (RK3588, Orange Pi 5 Plus) báo model sửa chậm hơn baseline ở INT8 (79.1 so với 56.3 ms), với nhiều sửa đổi cùng lúc. Kiểm từng lớp theo UG232: channel căn chỉnh (Conv int8: vào 32, ra 32; depthwise int8: 64), KH*KW*KC*type_bytes < 6K Bytes, Ksize/Kstride lớn, giảm Transpose, Reshape, Split, Concat, Resize, Pooling và activation không phải Relu, và ghép op theo luật fusion [RK66 tr.4; LNB tr.20; EDGE tr.5; DAHD tr.18; UG232 tr.142, 145, 146, 147] (Hình 8.2, Hình 9.4)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 8.1 | BN và conv đứng trước gộp thành conv có bias | T2 | REPVGG tr.5 | convert every BN and its preceding conv layer into a conv with a bias vector |
| 8.1 | Identity coi như conv 1x1 với ma trận đơn vị | T2 | REPVGG tr.5 | an identity can be viewed as a 1 × 1 conv with an identity matrix as the kernel |
| 8.1 | Bias cuối là tổng ba bias | T2 | REPVGG tr.5 | the final bias by adding up the three bias vectors |
| 8.1 | Kernel 3x3 cuối cộng hai kernel 1x1 vào điểm giữa, zero-pad | T2 | REPVGG tr.5 | zero-padding the two 1 × 1 kernels to 3 × 3 and adding the three kernels up |
| 8.1 | Điều kiện cùng stride | T2 | REPVGG tr.5 | requires the 3 × 3 and 1 × 1 layer to have the same stride |
| 8.1 | Padding của 1x1 ít hơn một pixel | T2 | REPVGG tr.5 | the padding configuration of the latter shall be one pixel less than the former |
| 8.1 | Không có nhánh identity khi kích thước không khớp | T2 | REPVGG tr.5 | Otherwise, we simply use no identity branch |
| 8.1 | Thân inference chỉ còn Conv 3x3 + ReLU | T2 | REPVGG tr.2 | one single type of operator: 3 × 3 conv followed by ReLU |
| 8.1 | Giả thuyết chip chuyên dụng nhanh hơn, không có số đo | T2 | REPVGG tr.2 | RepVGG allows for specialized hardware to achieve even higher speed |
| 8.1 | REPVGG đo tốc độ trên 1080Ti | T2 | REPVGG tr.7 | The speed is tested on 1080Ti |
| 8.1 | MobileOne: lúc inference không có nhánh | T2 | MOBONE tr.4 | At inference, MobileOne model does not have any branches. |
| 8.1 | MobileOne: 3x3 depthwise rồi 1x1 pointwise | T2 | MOBONE tr.4 | 3x3 depthwise convolution followed by 1x1 pointwise convolutions |
| 8.1 | MobileOne đo trên iPhone 12 bằng Core ML | T2 | MOBONE tr.1 | we deploy neural networks on an iPhone12 by using CoreML |
| 8.1 | Table 9 của MobileOne có cột CPU, GPU, Mobile | T2 | MOBONE tr.7 | CPU GPU Mobile |
| 8.1 | Y6: RepBlock lúc train | T2 | Y6 tr.3 | the main component of the backbone is RepBlock during the training phase |
| 8.1 | Y6: lúc inference thành stack Conv 3x3 (RepConv) + ReLU | T2 | Y6 tr.3 | converted to stacks of 3 × 3 convolutional layers (denoted as RepConv) with ReLU activation |
| 8.1 | Y6 đo trên Tesla T4, TensorRT, FP16 | T2 | Y6 tr.8 | measured in FP16-precision on a Tesla T4 in the same environment with TensorRT |
| 8.1 | Không bài nào đo RepVGG hay MobileOne trên NPU | T2 | (unknown) | (unknown) |
| 8.1 | RepVGG-A0 72.4 xuống 52.2, chênh 20.2 (bản official) | T2 | QAREP tr.3 | 72.4 52.2 (20.2↓) |
| 8.1 | Câu mở đầu của QAREP: PTQ chuẩn làm A0 tụt từ 72.4 xuống 52.2 | T2 | QAREP tr.1 | RepVGG-A0 from 72.4% to 52.2% |
| 8.1 | QARepVGG-A0 72.2 xuống 70.4, chênh 1.8 | T2 | QAREP tr.4 | QARepVGG-A0 72.2 70.4 (1.8↓) |
| 8.1 | YOLOv6s-RepVGG 42.4 xuống 35.0, chênh 7.4 | T2 | QAREP tr.7 | YOLOv6s-RepVGG⋆ 42.4 35.0 (7.4↓) |
| 8.1 | YOLOv6s-QARepVGG 42.3 xuống 41.0, chênh 1.3 | T2 | QAREP tr.7 | YOLOv6s-QARepVGG 42.3 41.0 (1.3↓) |
| 8.1 | Hai cột YOLOv6s là COCO mAP | T2 | QAREP tr.7 | Table 8: Detection results on COCO. |
| 8.1 | Thiết lập: symmetric uniform | T2 | QAREP tr.6 | the quantization scheme is set to symmetric uniform |
| 8.1 | Thiết lập: toolkit PyTorch-Quantization của NVIDIA | T2 | QAREP tr.6 | we use the Pytorch-Quantization toolkit (NVIDIA 2018) |
| 8.1 | Thiết lập: 8-bit kể cả lớp đầu và cuối | T2 | QAREP tr.6 | quantized into 8-bit, including the first and last layer |
| 8.1 | Đo trên bản deploy sau khi gộp nhánh | T2 | QAREP tr.3 | we use the deployed model after fusing multi-branches |
| 8.1 | QARepVGG gộp được thành một Conv 3x3 | T2 | QAREP tr.1 | Both can be identically fused into a single Conv 3 × 3. |
| 8.1 | QARepVGG: bỏ BN khỏi nhánh identity và 1x1 | T2 | QAREP tr.5 | remove BN from the identity and 1×1 branch |
| 8.1 | QARepVGG: thêm BN sau phép cộng ba nhánh | T2 | QAREP tr.5 | an extra BN after the addition of three branches |
| 8.1 | Nguyên nhân: BN đổi phương sai | T2 | QAREP tr.3 | the changed variance directly affects the quantization accuracy |
| 8.1 | Nguyên nhân: cộng ba nhánh làm phương sai tăng | T2 | QAREP tr.5 | adding three branches often enlarges the variance |
| 8.1 | Nguyên nhân: trọng số outlier không kiểm soát được | T2 | QAREP tr.4 | Structural design of RepVGG is prone to producing uncontrolled outlier weights |
| 8.1 | Conv có kernel_h thuộc [1, 31] trong mục NPU của RK3588 | T1 | OPL tr.58 | kernel_h ∈ [1, 31] |
| 8.1 | Conv nhận int8 và float16 | T1 | OPL tr.59 | T1: int8(Tensor), float16(Tensor) |
| 8.1 | ConvolutionRelu là Convolution và Relu fusion | T1 | OPL tr.60 | Convolution 与 Relu 融合计算 |
| 8.1 | RKNN mặc định w8a8 asymmetric | T1 | API232 tr.7 | w8a8: The weight is 8bit asymmetric quantitative accuracy |
| 8.1 | Dạng sau gộp biểu diễn được bằng op NPU | T1 | (số học) | (số học) |
| 8.1 | RK3588 nhanh hơn nhờ re-param hay INT8 tụt như QAREP: không có nguồn T1 hay T3 | T1 | (unknown) | (unknown) |
| 8.2 | Conv kernel_h thuộc [1, 31] | T1 | OPL tr.58 | kernel_h ∈ [1, 31] |
| 8.2 | Conv stride_h thuộc [1, 7] | T1 | OPL tr.59 | stride_h ∈ [1, 7] |
| 8.2 | Conv pads_top thuộc [0, 15] | T1 | OPL tr.59 | pads_top ∈ [0, 15] |
| 8.2 | Conv dilations_h thuộc [1, 31] | T1 | OPL tr.59 | dilations_h ∈ [1, 31] |
| 8.2 | Conv int8, float16 | T1 | OPL tr.59 | T1: int8(Tensor), float16(Tensor) |
| 8.2 | Depthwise Conv kernel_h thuộc [1, 8] | T1 | OPL tr.59 | kernel_h ∈ [1, 8] |
| 8.2 | Resize chỉ nhận phóng đại nguyên theo H và W | T1 | OPL tr.87 | 目前仅支持宽高方向的整数倍缩放 |
| 8.2 | Resize bội nguyên bắt đầu từ 2 (đến 8) | T1 | OPL tr.87 | 且缩放倍数为 2 |
| 8.2 | Resize mode chỉ nearest, linear | T1 | OPL tr.87 | 目前仅支持 nearest 和 linear 两种可配置 |
| 8.2 | Resize coordinate_transformation_mode ba giá trị | T1 | OPL tr.87 | 目前仅支持 half_pixel，pytorch_half_pixel，align_corners 三种 |
| 8.2 | Upsample có mục CPU 4.67 | T1 | OPL tr.329 | 4.67 Upsample |
| 8.2 | Upsample CPU: bilinear, nearest2d | T1 | OPL tr.329 | 支持插值方式 bilinear; nearest2d |
| 8.2 | Upsample không có mục trong phần NPU: tìm toàn bộ 343 trang OPL, chỉ thấy ở tr.4 (mục lục) và tr.329 | T1 | (số học) | (số học) |
| 8.2 | T3: Resize 2x nearest, Target NPU ở optimization_level 1 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt1_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 8.2 | T3: Resize ở optimization_level 2 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt2_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 8.2 | T3: Resize ở optimization_level 3 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 8.2 | T3: Resize là nearest (README của log) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (nearest, |
| 8.2 | T3: 2x vì (1,256,20,20) sang (1,256,40,40) | T3 | (số học) | (số học) |
| 8.2 | T3: không tái hiện được lời UG232 về optimization_level=2 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | không tái hiện được |
| 8.2 | T3: chưa thử bilinear, FP16 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Chưa thử Resize bilinear, FP16 hay các tham số khác |
| 8.2 | T3: model YOLOv8n nc=5, 640x640, ngẫu nhiên, INT8 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | 640x640) khởi tạo ngẫu nhiên, INT8 |
| 8.2 | UG232: NPU chưa hỗ trợ Resize cấp phần cứng | T1 | UG232 tr.176 | the NPU does not currently support hardware-level Resize |
| 8.2 | UG232: toolkit đổi Resize thành ConvTranspose | T1 | UG232 tr.176 | the RKNN-Toolki2 will convert Reszie to ConvTranspose |
| 8.2 | UG232: optimization_level=2 đưa Resize về CPU | T1 | UG232 tr.176 | optimization_level=2 can be added to rknn.config |
| 8.2 | Multi-core: các op tăng tốc tốt hơn | T1 | UG152 tr.27 | the following ops have better acceleration |
| 8.2 | Multi-core: danh sách op của UG152 | T1 | UG152 tr.27 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. |
| 8.2 | Op khác rơi về Core0 | T1 | UG152 tr.27 | Other type of op will fallback to Core0 to continue running |
| 8.2 | UG232 liệt kê cùng danh sách | T1 | UG232 tr.75 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu. |
| 8.2 | OPL mục 3.2.51 PRelu | T1 | OPL tr.85 | 3.2.51 PRelu |
| 8.2 | OPL PRelu: 多核联合 暂不支持 | T1 | OPL tr.85 | 多核联合: 暂不支持 |
| 8.2 | OPL Depthwise Conv: 多核联合 支持 | T1 | OPL tr.60 | 多核联合: 支持 |
| 8.2 | OPL Conv: 多核联合 支持 | T1 | OPL tr.59 | 多核联合: 支持 |
| 8.2 | Bộ hình không chọn phía nào (mâu thuẫn UG152, UG232 so với OPL) | T1 | (unknown) | (unknown) |
| 8.2 | T3: Split chạy lõi 0 ở CORE_0_1_2 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Split INT8 NPU (1,32,160,160),(2) (1,16,160,160),... 0/0/0 217 100.0%/0.0%/0.0% |
| 8.2 | T3: Concat chia ba lõi | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Concat INT8 NPU (1,16,160,160),(1,16,160,160),... (1,48,160,160) 0/0/0 161 33.7%/33.1%/33.1% |
| 8.2 | T3: số lớp theo WorkLoad: Split 9, MaxPool 3, Resize 2, Sub 2, Mul 2, Sigmoid 1, exSoftmax13 1 đều 100%/0%/0%; Add 8 chia ba lõi; Concat 15 trong 17 chia ba lõi (đếm bằng awk trên file lớp) | T3 | (số học) | (số học) |
| 8.2 | OPL ConvolutionRelu mục 3.2.7 | T1 | OPL tr.60 | 3.2.7 ConvolutionRelu |
| 8.2 | OPL ConvolutionRelu: 多核联合 支持 | T1 | OPL tr.60 | 多核联合: 支持 |
| 8.2 | OPL ConvolutionSwish mục 3.2.17 | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish |
| 8.2 | OPL ConvolutionSwish: Convolution và Swish fusion | T1 | OPL tr.63 | Convolution 与 Swish 融合计算 |
| 8.2 | OPL ConvolutionSwish: 多核联合 暂不支持 | T1 | OPL tr.63 | 多核联合: 暂不支持 |
| 8.2 | OPL: ConvolutionSwish và ConvolutionRelu cùng thông số như Convolution | T1 | OPL tr.63 | 说明及规格限制同Convolution |
| 8.2 | UG232: Conv+Sigmoid(Tanh/Elu/Silu...) đã hỗ trợ | T1 | UG232 tr.142 | Conv+Sigmoid(Tanh/Elu/Silu...) Conv+Activation+Mul |
| 8.2 | T3: ConvExSwish chạy lõi 0 ở CORE_0_1_2 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | ConvExSwish INT8 NPU (1,16,320,320),(32,16,3,3),(32) (1,32,160,160) 104104/230400/230400 603 6.37/6.37/6.37 100.0%/0.0%/0.0% |
| 8.2 | T3: 57 lớp ConvExSwish đều 100%/0%/0% | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | cả 57 lớp |
| 8.2 | T3: ConvRelu chia ba lõi | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvRelu INT8 NPU (1,32,160,160),(32,32,1,1),(32) (1,32,160,160) 69320/102400/102400 138 6.18/6.18/6.18 33.7%/33.1%/33.1% |
| 8.2 | T3: ConvReluAdd chia ba lõi | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvReluAdd INT8 NPU (1,16,160,160),(16,16,3,3),(16),... (1,16,160,160) 52058/230400/230400 163 11.78/11.78/11.78 33.7%/33.1%/33.1% |
| 8.2 | T3: 51 ConvRelu | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | cả 51 |
| 8.2 | T3: khoảng 35%/32.5%/32.5% | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | ba lõi (khoảng 35%/32.5%/32.5%) |
| 8.2 | T3: số lớp ConvExSwish 57 trên 57, ConvRelu 51, ConvReluAdd 6 (đếm bằng awk trên file lớp) | T3 | (số học) | (số học) |
| 8.2 | T3: số ConvExSwish ở lượt 3 (model đã huấn luyện) cũng chạy lõi 0 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Cả 57 lớp |
| 8.2 | REPO: tiêu đề cột map50_95 của leaderboard | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | precision,recall,map50,map50_95 |
| 8.2 | REPO: ReLU 0.5835 (seed 42, tập sfchd_test, protocol v1) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_relu_100ep_s42,yolov8n_relu,100,42,sfchd_test,v1,0.9218,0.8394,0.8845,0.5835 |
| 8.2 | REPO: SiLU 0.5908 (seed 42, tập sfchd_test, protocol v1) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_baseline_100ep_s42,yolov8n_baseline,100,42,sfchd_test,v1,0.9048,0.8394,0.8924,0.5908 |
| 8.2 | Hiệu 0.5908 - 0.5835 = 0.0073 (phép tính của bộ hình) | T3 | (số học) | (số học) |
| 8.2 | ReLU khởi tạo từ yolov8n.pt | T3 | REPO ai/models/README.md | YOLOv8 nano with ReLU, initialized from |
| 8.2 | Run ReLU: pretrained yolov8n.pt | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/args.yaml | pretrained: yolov8n.pt |
| 8.2 | Run ReLU: seed 42 | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/args.yaml | seed: 42 |
| 8.2 | AP của ReLU là cận dưới thực tế (nhận định, chưa kiểm bằng huấn luyện từ đầu) | T3 | (unknown) | (unknown) |
| 8.2 | INT8 AP của ReLU trên board chưa có (chờ pipeline, Hình 10.7) | T3 | (unknown) | (unknown) |
| 8.2 | Y6: ReLU nhanh hơn nhờ fusion vào conv | T2 | Y6 tr.8 | ReLU has a greater speed advantage because of its fusion into convolution |
| 8.2 | Y6: đo bằng TensorRT, Tesla T4 | T2 | Y6 tr.8 | measured in FP16-precision on a Tesla T4 in the same environment with TensorRT |
| 8.2 | ACTNAS: ReLU nhanh, kém chính xác hơn; SiLU ngược lại | T2 | ACTNAS tr.1 | ReLU is fast but often less precise |
| 8.2 | ACTNAS: SiLU chính xác hơn, đổi lại tốc độ | T2 | ACTNAS tr.1 | SiLU offers higher accuracy at the expense of speed |
| 8.2 | ACTNAS: NPU không nêu tên | T2 | ACTNAS tr.3 | We are not disclosing the vendor name |
| 8.2 | UG232 Table 8-2 RK3588 | T1 | UG232 tr.145 | Table 8-2 RK3588/RK3576/RV1126B |
| 8.2 | Table 8-2: Int8 Conv 32 vào, 32 ra, depthwise 64, op khác 16 | T1 | UG232 tr.145 | Int8 32 32 64 16 |
| 8.2 | Table 8-2: Float16 Conv 32 vào, 16 ra, depthwise 32, op khác 8 | T1 | UG232 tr.145 | Float16 32 16 32 8 |
| 8.2 | Channel đạt căn chỉnh thì utilization cao hơn | T1 | UG232 tr.146 | meets the alignment requirements |
| 8.2 | Bảng kích thước kernel là tham khảo theo dữ liệu kinh nghiệm | T1 | UG232 tr.146 | The following is a rough reference based on empirical data |
| 8.2 | Channel vào dưới 256 tương đối cao, trên 512 giảm dần | T1 | UG232 tr.146 | is > 512, the utilization rate will gradually decrease |
| 8.2 | KH*KW*KC*type_bytes < 6K Bytes | T1 | UG232 tr.147 | the utilization rate is relatively high when KH* KW * KC * type_bytes < 6K Bytes |
| 8.2 | Ksize/Kstride lớn thì utilization cao | T1 | UG232 tr.147 | The larger the ratio of Ksize / Kstride, the higher the utilization rate |
| 8.2 | Ksize=3, Kstride=1 tốt hơn Ksize=2, Kstride=1 | T1 | UG232 tr.147 | Ksize=3, Kstride=1 is better than Ksize=2, Kstride=1 |
| 8.2 | Utilization giảm khi Height*Width output < 16 | T1 | UG232 tr.147 | The utilization rate decreases when the Height * Width of the output Tensor < 16 |
| 8.2 | Ba loại op kém hiệu quả: giảm | T1 | UG232 tr.146 | Try to reduce the following three types of operators in the model |
| 8.2 | Ba nhóm: Data transfer, Size transformation, Non-Relu activation function | T1 | UG232 tr.146 | Data transfer Size transformation Non-Relu activation function |
| 8.2 | Hàng 1 của Table 8-5 | T1 | UG232 tr.146 | Transpose Resize Sigmoid |
| 8.2 | Hàng 2 của Table 8-5 | T1 | UG232 tr.146 | Reshape Tile Tanh |
| 8.2 | Hàng 3 của Table 8-5 | T1 | UG232 tr.146 | Split Pooling Softplus |
| 8.2 | Hàng 4 của Table 8-5 | T1 | UG232 tr.146 | Concat Pad Hardswish |
| 8.2 | Fusion đã hỗ trợ và kế hoạch tương lai | T1 | UG232 tr.142 | Supported fusion rules Fusion rules supported by future plans |
| 8.2 | Conv+Relu | T1 | UG232 tr.142 | Conv+Relu Activation+Add(Mul) |
| 8.2 | Conv+PRelu(LeakyRelu) | T1 | UG232 tr.142 | Conv+PRelu(LeakyRelu) Add(Mul)+Activation |
| 8.2 | Conv+Clip và kế hoạch Conv+Mul | T1 | UG232 tr.142 | Conv+Clip Conv+Mul |
| 8.2 | Conv+Add và kế hoạch Conv+Activation+Pooling | T1 | UG232 tr.142 | Conv+Add Conv+Activation+Pooling |
| 8.2 | Conv+Activation+Add | T1 | UG232 tr.142 | Conv+Activation+Add Conv+Activation+Add(Mul)+Pooling |
| 8.2 | QAREP: RepVGG-A0 72.4 xuống 52.2 | T2 | QAREP tr.3 | 72.4 52.2 (20.2↓) |
| 8.2 | QAREP: YOLOv6s-RepVGG 42.4 xuống 35.0 | T2 | QAREP tr.7 | YOLOv6s-RepVGG⋆ 42.4 35.0 (7.4↓) |
| 8.2 | QAREP: QARepVGG-A0 72.2 xuống 70.4 | T2 | QAREP tr.4 | QARepVGG-A0 72.2 70.4 (1.8↓) |
| 8.2 | QAREP: YOLOv6s-QARepVGG 42.3 xuống 41.0 | T2 | QAREP tr.7 | YOLOv6s-QARepVGG 42.3 41.0 (1.3↓) |
| 8.2 | QAREP: PTQ 8-bit symmetric uniform | T2 | QAREP tr.6 | the quantization scheme is set to symmetric uniform |
| 8.2 | QAREP: NVIDIA PyTorch-Quantization | T2 | QAREP tr.6 | we use the Pytorch-Quantization toolkit (NVIDIA 2018) |
| 8.2 | RK3588: re-param INT8 chưa biết | T2 | (unknown) | (unknown) |
| 8.2 | S3NAS: bộ ước lượng độ trễ xây từ bộ mô phỏng NPU | T2 | S3NAS tr.1 | an analytical latency estimator is devised, based on a cycle-level NPU simulator |
| 8.2 | S3NAS: MIDAP chưa là chip thật | T2 | S3NAS tr.4 | MIDAP has not been implemented as a real hardware chip yet |
| 8.2 | S3NAS: filter bội của 16 cho MAC utilization trên MIDAP | T2 | S3NAS tr.9 | multiples of 16 to maximize the MAC unit utilization on MIDAP |
| 8.2 | ACTNAS: tìm activation từng lớp trong năm ứng viên | T2 | ACTNAS tr.2 | we generate a search space by systematically replacing each activation function in the reference model |
| 8.2 | ACTNAS: model tối ưu cho NPU1 tăng tốc rất ít trên thiết bị khác | T2 | ACTNAS tr.8 | very low speedup on other devices |
| 8.2 | Không có NAS cho Rockchip | T2 | (unknown) | (unknown) |
| 8.2 | DAHD: bài về hút thuốc | T2 | DAHD tr.18 | suitable for the deployment of downstream tasks such as smoking behavior detection |
| 8.2 | DAHD: attention (AFGCA) | T2 | DAHD tr.1 | attention (AFGCA) |
| 8.2 | DAHD: kiến trúc có DetectDBB | T2 | DAHD tr.5 | DetectDBB |
| 8.2 | DAHD: Orange Pi 5 Plus với RK3588 | T2 | DAHD tr.17 | We utilize the Orange Pi 5 Plus equipped with the RK3588 SoC |
| 8.2 | DAHD Table 6: YOLOv8s INT8 56.3 ms | T2 | DAHD tr.18 | YOLOv8s INT8 12.6 70.9 66.6 57.3 73.0 56.3 9 |
| 8.2 | DAHD Table 6: DAHD-YOLO INT8 79.1 ms | T2 | DAHD tr.18 | DAHD-YOLO INT8 8.8 50.2 43.8 37.7 74.36 79.1 7 |
| 8.2 | DAHD: FPS đo bằng thread pool | T2 | DAHD tr.18 | By utilizing a thread pool for acceleration |
| 8.2 | DAHD: độ phức tạp làm giảm tốc độ | T2 | DAHD tr.20 | increased structural complexity has resulted in a decline in inference speed |
| 8.2 | EDGE: YOLO11n độ trễ cao hơn YOLOv8n | T2 | EDGE tr.5 | YOLO11n, with fewer parameters than YOLOv8n, exhibited higher latency on all three SoCs |
| 8.2 | EDGE: C2f, C3k2 là giả thuyết | T2 | EDGE tr.5 | suggesting that architectural innovations (e.g., C2f in YOLOv8, C3k2 in YOLO11) introduce additional computational overheads |
| 8.2 | EDGE: RK3588 ở chế độ một NPU core | T2 | EDGE tr.5 | operating in single-core NPU mode |
| 8.2 | EDGE: không sửa model | T2 | EDGE tr.4 | no model was retrained, fine-tuned, pruned, or structurally modified |
| 8.2 | EDGE: biên dịch bằng RKNN Toolkit, chạy trên RV1106, RK3568, RK3588 | T2 | EDGE tr.4 | inference conducted directly on the NPUs of RV1106, RK3568, and RK3588 |
| 8.2 | EDGE: RK3568 Nano 34 đến 79 ms | T2 | EDGE tr.5 | Nano models reduced to 34–79 ms |
| 8.2 | EDGE: RK3588 Nano 21 đến 30 ms | T2 | EDGE tr.5 | Nano variants consistently operated between 21–30 ms |
| 8.2 | LNB: FPS đo trên RTX 3090 | T2 | LNB tr.20 | NVIDIA GeForce RTX 3090 |
| 8.2 | LNB: board RK3568 của Rockchip | T2 | LNB tr.20 | The RK3568 edge computing board from Rockchip was employed |
| 8.2 | LNB: 20 ảnh khuyết tật | T2 | LNB tr.20 | comprising 20 phone surface defect images |
| 8.2 | LNB: không có độ trễ NPU ở RK3568 | T2 | (unknown) | (unknown) |
| 8.2 | RK66: FP32 trên RK3566 | T2 | RK66 tr.4 | All models were maintained at FP32 precision without pruning or quantization |
| 8.2 | RK66: thử INT8 cho kết quả sai | T2 | RK66 tr.4 | produced invalid results due to quantization noise |
| 8.2 | RK66: nguyên nhân INT8 là suy đoán | T2 | RK66 tr.12 | INT8 instability likely arises from unsupported or partially supported RKNN operators |
| 8.2 | ConvExSwish ép đa lõi được không: chưa thử | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Có cách nào ép |
| 8.2 | Vì sao YOLO11 chậm hơn YOLOv8 trên RK3588: nguồn chỉ có giả thuyết | T2 | (unknown) | (unknown) |
| 8.2 | Số của RK3566, RK3568 có bằng RK3588 hay không: nguồn không đo | T2 | (unknown) | (unknown) |
