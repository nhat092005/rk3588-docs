# Phần 6: Compiler và op

## Câu hỏi mở đầu
Một op của YOLOv8 chạy trên NPU RK3588 hay rơi sang CPU, nó có được ghép với op đứng trước và chia cho ba core không, và dữ liệu của nó nằm trong bộ nhớ NPU theo layout nào?

## Hình 6.1 (h6-1-npu-hay-cpu) [T1 RK3588]
Nguồn T1 nêu ba lý do khiến một op chạy ngoài NPU (kích thước vượt giới hạn, chưa hỗ trợ, phần cứng không làm được) nhưng không nêu quy tắc op rơi sang đâu: OPL không có quy tắc rơi về CPU và thuật toán chọn đích của op_target = 'auto' đều là unknown (khung đỏ). Lưu đồ đi từ việc toolkit nhận op khi convert, đến mục OPL 3.2 và giới hạn của mục, rồi hai cách người dùng can thiệp là op_target và optimization_level; ô xanh dương "chạy trên NPU" là suy ra của bộ hình từ ba lý do, không phải câu của vendor. Ô T3 ghi rằng trên YOLOv8n INT8 chỉ Transpose (cùng InputOperator và OutputOperator) có Target = CPU, và với Resize nearest 2x INT8 thì optimization_level 1, 2, 3 đều cho Target = NPU. Hình tách hai nghĩa của "fallback": rời NPU sang CPU (API232 tr.17) và về core 0 của NPU (UG152 tr.27, Hình 2.4).
Đọc thêm: 06_ mục 6.1. Số đo: Hình 10.2
Khái niệm: Hình 2.4, Hình 8.2, Hình 9.3

## Hình 6.2 (h6-2-ma-tran-op-yolo) [T1 RK3588]
Mọi op của detector kiểu YOLOv8 trong bảng đều có mục trong OPL 3.2 của RK3588 trừ Upsample (chỉ có ở chương CPU OPs, PDF 329), nhưng dòng 多核联合 (đa core) khác nhau: Conv, Add, Mul ghi 支持; ConvolutionSwish, Transpose ghi 暂不支持; exSwish, Sigmoid, Reshape, Softmax ghi 尚不支持; Resize, Sub ghi 不支持; Concat, Split, MaxPool, Slice không có dòng. Cột T3 là bảng lớp thật của một model YOLOv8n INT8 (trọng số ngẫu nhiên, CORE_0_1_2): chỉ Transpose (1 lớp) nằm trên CPU, cả 57 lớp ConvExSwish chỉ chạy core 0, còn Add và 15 trong 17 Concat chia ba core. ConvExSwish (tên trong bảng lớp) và ConvolutionSwish (tên trong OPL) chưa được chứng minh là cùng một op, và Mul ghi 支持 trong OPL nhưng 2 lớp Mul đo được chỉ chạy core 0. Phần dưới hình ghi mâu thuẫn số 3 (danh sách đa core của UG232 so với OPL), mâu thuẫn về Resize giữa OPL và UG232 tr.176, và một phép tính của bộ hình về lớp Transpose duy nhất trên CPU.
Đọc thêm: 06_ mục 6.2. Số đo: Hình 10.1, Hình 10.2, Hình 10.3
Khái niệm: Hình 2.4, Hình 9.4

## Hình 6.3 (h6-3-fusion) [T1 RK3588]
Toolkit ghép Conv với activation đứng sau thành một lớp: trong T3, 57 bộ Conv, Sigmoid, Mul của YOLOv8n dùng SiLU thành 57 lớp ConvExSwish; khi thay SiLU bằng ReLU thì có 51 ConvRelu và 6 ConvReluAdd, và số lớp Add đứng riêng giảm từ 8 xuống 2. Dòng 多核联合 của 13 mục Conv hợp nhất trong OPL chia theo họ activation (Relu, Clip, PRelu, Add: 支持; Sigmoid, Tanh, Softplus, HardSigmoid, HardSwish, Elu, Swish, Mish: 暂不支持), cùng chiều với số đo T3 nhưng OPL không giải thích vì sao. Người dùng can thiệp được bằng cách đổi thứ tự op theo luật của UG232 tr.142 (Figure 8-7 nhúng ở khung "Hình gốc"), còn thuật toán fusion, thứ tự pass và rule bị tắt bởi optimization_level là unknown. Khung xanh nhạt ở cuối chỉ là ngữ cảnh chung từ bài báo (T2), không nói về toolchain của Rockchip.
Đọc thêm: 06_ mục 6.3. Số đo: Hình 10.1, Hình 10.3
Khái niệm: Hình 8.2, Hình 9.3
Hình gốc: ../../npu_study/images/06_compiler_operators/ug232_p142_fig8-7_fusion_rules.png (UG232 tr.142, Figure 8-7; nhúng để đối chiếu bảng luật fusion phần cứng và ví dụ đổi thứ tự Transpose, Clip với bảng vẽ lại)

## Hình 6.4 (h6-4-layout) [T1 RK3588]
NC1HWC2 xếp dữ liệu theo thứ tự địa chỉ từ thấp đến cao C2, W, H, C1, N; C2 do nền tảng quyết định (RK3588: 16 cho int8, 8 cho float16), C1 là C/C2 làm tròn lên và phần kênh thiếu được lấp bằng dữ liệu căn thừa. "Alignment" trong tài liệu RKNN là ít nhất bốn khái niệm khác nhau: C2 của layout (UG232 tr.61), căn width của input chỉ cho zero-copy API (OPL PDF 335, 336), căn output của lớp cuối (OPL PDF 339) và căn kênh thân thiện DDR "not mandatory" (UG232 tr.144, 145); số 16 của int8 xuất hiện ở cả bốn nhưng nguồn không nối chúng. Ví dụ tensor int8 (1,13,4,4) trên RK3588 cho (1,1,4,4,16) là phép tính của bộ hình, còn log mẫu SRAM có NativeShape lệch quy tắc làm tròn (33 và 67 thay vì 32 và 64), unknown vì sao. Khung xanh nhạt cuối là ngữ cảnh chung của compiler (T2), không nói về cách Rockchip chọn layout.
Đọc thêm: 06_ mục 6.4
Khái niệm: Hình 2.2, Hình 8.2
Hình gốc: ../../npu_study/images/06_compiler_operators/ug232_p61_fig5-1_table5-1.png (UG232 tr.61, Figure 5-1 và Table 5-1; nhúng để thấy thứ tự lưu 0 đến 31 và bảng C2 theo chip, không vẽ lại được bản đồ số của hình vẽ khối)

## Hiểu sai thường gặp
- "Upsample là một NPU op trên RK3588" -> Upsample không có trong OPL mục 3.2 (PDF 56 đến 107); chỉ có mục CPU 4.67 (PDF 329) và trong OPSUP chỉ thấy ở danh sách Caffe, danh sách ONNX có Resize [OPL tr.329; OPSUP dòng 147; OPSUP dòng 461] (Hình 6.2)
- "UG232 tr.176 nói optimization_level=2 đưa Resize về CPU, nên luôn như vậy" -> T3 không tái hiện: hai lớp Resize nearest 2x INT8 đều Target = NPU ở level 1, 2, 3; bilinear và FP16 chưa thử, nên không kết luận UG232 sai [UG232 tr.176; LOG 2026-10-10_t3-board-silu-resize/README.md] (Hình 6.1, Hình 6.2)
- "ConvExSwish chính là ConvolutionSwish, đã chứng minh" -> chưa chứng minh: số đo T3 phù hợp với dòng 暂不支持 của ConvolutionSwish, nhưng tên trong bảng lớp và tên trong OPL khác nhau và chỉ có một model [OPL tr.63; LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt] (Hình 6.2, Hình 6.3)
- "Chỉ có một quy tắc alignment" -> ít nhất bốn khái niệm: C2 của layout, căn width input (chỉ zero-copy API), căn output lớp cuối, căn kênh thân thiện DDR (không bắt buộc) [UG232 tr.61, 144; OPL tr.335, 339] (Hình 6.4)
- "OPL nói op không hỗ trợ thì rơi về CPU" -> OPL không nêu quy tắc đó; UG232 tr.139 chỉ cho ba lý do op chạy ngoài NPU, và API232 tr.17 có tham số fallback_prior_device mặc định 'cpu' [UG232 tr.139; API232 tr.17; OPL tr.319] (Hình 6.1)
- "Op ghi 支持 ở OPL thì chắc chắn chia ba core" -> OPL ghi Mul là 支持 nhưng 2 lớp Mul đo được chỉ chạy core 0; UG232 tr.75 nêu thêm lý do tải của lớp nhỏ hơn đơn vị phân chia, nên không suy ra được nguyên nhân [OPL tr.77; UG232 tr.75; LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt] (Hình 6.2)
- "Gộp Conv và BN do compiler RKNN làm" -> BN được gộp trong PyTorch lúc export của Ultralytics (model.fuse); RKNN có gộp BN nữa hay không thì nguồn không cho (unknown) [ULT nn/modules/conv.py:80-90; ULT engine/exporter.py:863] (Hình 6.3)
- "Danh sách đa core của UG232 và OPL nhất quán" -> UG232 tr.75 liệt kê Relu, Clip, PRelu, LeakyRelu, ThresholdedRelu, còn OPL ghi Relu, Clip/ReLU6, PRelu, LeakyRelu là 暂不支持 và không có ThresholdedRelu; đây là mâu thuẫn số 3, một model T3 không phân xử được [UG232 tr.75; OPL tr.84, 85; UG152 tr.27] (Hình 6.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao khi chọn CORE_0_1_2 các lớp ConvRelu được chia ba core còn ConvExSwish chỉ chạy core 0, và kết luận này chắc đến đâu?
Đáp án: OPL ghi ConvolutionRelu 多核联合 là 支持 và ConvolutionSwish là 暂不支持; UG232 tr.75 nói op chưa hỗ trợ thì "does not implement multi-core task segmentation in the NPU driver". T3: 51 ConvRelu và 6 ConvReluAdd chia ba core (ví dụ 33.4%/33.4%/33.1%), 57 ConvExSwish là 100%/0%/0%. Phù hợp với OPL nhưng không chứng minh: ConvExSwish và ConvolutionSwish khác tên, chỉ một model có trọng số ngẫu nhiên, và UG232 tr.75 còn nêu một nguyên nhân khác là tải lớp nhỏ hơn đơn vị phân chia [OPL tr.60, 63; UG232 tr.75; LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt] (Hình 6.2, Hình 6.3)
### Câu 2 (phân biệt)
Số 16 xuất hiện ở C2 của int8, ở căn width input của lớp đầu, ở căn kênh output NHWC và ở căn kênh "Other OP". Chúng có phải một quy tắc không, và cái nào bắt buộc?
Đáp án: Không có nguồn nào nói chúng là một đại lượng; chúng thuộc bốn khái niệm. C2 là định nghĩa của layout NC1HWC2 (UG232 tr.61). Căn width input (int8 16 khi số kênh 1, 3, 4, đọc từ hình) chỉ áp dụng cho zero-copy API (OPL tr.335, 336). Căn output NHWC 16 có yêu cầu khi bước chuyển output do NPU làm (OPL tr.339). Căn kênh "Other OP" 16 thuộc nhóm quy tắc thân thiện DDR mà UG232 ghi "These rules are not mandatory" (UG232 tr.144, 145) [UG232 tr.61, 144, 145; OPL tr.335, 336, 339] (Hình 6.4)
### Câu 3 (áp dụng)
Model của bạn có Resize nearest 2x INT8 và UG232 tr.176 nói optimization_level=2 đưa Resize về CPU. Làm sao biết model của bạn có bị ảnh hưởng, và T3 cho biết gì?
Đáp án: Build với optimization_level 3 rồi 2, chạy eval_perf và đọc cột Target của lớp Resize trong bảng lớp; muốn ép đích có op_target. T3 trên YOLOv8n INT8 cho hai lớp Resize đều Target = NPU, INT8 ở level 1, 2, 3, nhưng chỉ thử nearest 2x INT8; bilinear và FP16 chưa thử, nên không kết luận UG232 sai [UG232 tr.75, 176; API232 tr.8, 9; LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt] (Hình 6.1, Hình 6.2)
### Câu 4 (áp dụng)
Trong bảng lớp YOLOv8n INT8 của T3, lớp CPU duy nhất ngoài Input và Output là Transpose có input (4,1,1,8400) và output (1,4,1,8400). Đối chiếu với OPL cho thấy gì, và chắc đến đâu?
Đáp án: Nếu perm là [1,0,2,3], mục OPL 3.2.62 ghi điều kiện "h1*w1<p" với p = 8192, mà h1*w1 = 1*8400 = 8400, vượt giới hạn; điều này phù hợp với lý do "The operator size exceeds the limit" của UG232 tr.139. Đây là phép tính của bộ hình: perm suy từ hai shape và nguyên nhân không được nguồn nào xác nhận [OPL tr.93; UG232 tr.139; LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt] (Hình 6.2)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 6.1 | OPSUP: bảng ONNX OPs supported by RKNN Toolkit2 | T1 | OPSUP dòng 3 | ONNX OPs supported by RKNN Toolkit2 |
| 6.1 | OPSUP: giới hạn chi tiết xem OPL | T1 | OPSUP dòng 7 | For more restrictions, please refer to <RKNN_Compiler_Support_Operator_List> |
| 6.1 | OPSUP: NonMaxSuppression ghi Not Supported | T1 | OPSUP dòng 115 | NonMaxSuppression \| Not Supported |
| 6.1 | Convert thử trực tiếp, không hỗ trợ sẽ có thông báo | T1 | UG232 tr.167 | Convert the model directly. If it is not supported, there will be relevant prompts. |
| 6.1 | NonMaxSuppression: hậu xử lý RKNN không hỗ trợ | T1 | UG232 tr.168 | Post-processing Ops such as NonMaxSuppression |
| 6.1 | Bỏ subgraph hậu xử lý khỏi graph | T1 | UG232 tr.168 | The post-processing subgraph part of the graph can be removed |
| 6.1 | Subgraph bị bỏ xử lý riêng ở phía CPU | T1 | UG232 tr.168 | The removed subgraphs are processed separately on the CPU side. |
| 6.1 | Op 6 chiều không hỗ trợ, phần lớn chỉ 4 chiều | T1 | UG232 tr.168 | At present, RKNN does not support 6-dimensional OP. In most cases, it only supports 4-dimensional. |
| 6.1 | Mục 3.2 là RK3588, bắt đầu ở PDF 56 | T1 | OPL tr.56 | 3.2 RK3588 |
| 6.1 | Mục 3.3 (RK3562) bắt đầu ở PDF 108, nên 3.2 kết thúc ở PDF 107 | T1 | OPL tr.108 | 3.3 RK3562 |
| 6.1 | Mục 3.2 gồm 79 mục (đếm các tiêu đề 3.2.N) | T1 | OPL tr.56 | (số học) |
| 6.1 | Cấu trúc mục: mô tả | T1 | OPL tr.56 | 执行元素级二进制加法 |
| 6.1 | Cấu trúc mục: input list | T1 | OPL tr.56 | 输入列表 |
| 6.1 | Cấu trúc mục: output list | T1 | OPL tr.56 | 输出列表 |
| 6.1 | Cấu trúc mục: ràng buộc kiểu dữ liệu | T1 | OPL tr.56 | T1: int8(Tensor), float16(Tensor) |
| 6.1 | Cấu trúc mục: 其他支持 có dòng 多核联合 | T1 | OPL tr.56 | 其他支持 多核联合: 支持 |
| 6.1 | Chưa có đường từ 'đủ điều kiện' đến 'chạy trên NPU' trong nguồn (suy ra từ ba lý do) | T1 | (không có) | (unknown) |
| 6.1 | Ba lý do op chạy ngoài NPU: kích thước | T1 | UG232 tr.139 | The operator size exceeds the limit (see the operator size limit in the OpList document) |
| 6.1 | Ba lý do: chưa hỗ trợ | T1 | UG232 tr.139 | The operator does not yet support operation on NPU (check whether OpList supports this operator |
| 6.1 | Ba lý do: giới hạn phần cứng | T1 | UG232 tr.139 | NPU hardware limitations cannot support it |
| 6.1 | Bảng lớp có cột Target và WorkLoad (ví dụ UG232) | T1 | UG232 tr.75 | OpType DataType Target WorkLoad |
| 6.1 | Ví dụ CPU operator performance analysis (UG232) | T1 | UG232 tr.139 | Figure 8-4 CPU operator performance analysis |
| 6.1 | OPL chương 4 là CPU OPs, bắt đầu ở PDF 319 | T1 | OPL tr.319 | Chapter 4. CPU OPs |
| 6.1 | Chương 5 bắt đầu ở PDF 335, nên chương 4 kết thúc ở PDF 334 | T1 | OPL tr.335 | Chapter 5. 模型输入输出限制说明 |
| 6.1 | Mục 4.1 chỉ ghi ngoại lệ RK2118 | T1 | OPL tr.319 | RK2118 不支持所有 CPU 算子 |
| 6.1 | Mục 4.1 ghi ngoại lệ RV1106, RV1103 (chỉ hỗ trợ một phần) | T1 | OPL tr.319 | RV1106/RV1103/RV1106B/RV1103B 仅支持部分 CPU 算子如下 |
| 6.1 | fallback_prior_device: gpu hoặc cpu, mặc định cpu | T1 | API232 tr.17 | set fallback prior device when OP is not supported by NPU. |
| 6.1 | fallback_prior_device: gpu chỉ cho chip có GPU | T1 | API232 tr.17 | 'gpu' is only valid for platform which has gpu hardware. The default value is 'cpu'. |
| 6.1 | OPL không nêu quy tắc rơi về CPU | T1 | (không có) | (unknown) |
| 6.1 | Nguồn không nói RK3588 dùng OPL chương 4 thế nào | T1 | (không có) | (unknown) |
| 6.1 | Thuật toán chọn đích của op_target 'auto' | T1 | (không có) | (unknown) |
| 6.1 | op_target: chỉ định đích từng op | T1 | API232 tr.9 | Used to specify the target of each operation (NPU/CPU/GPU etc.) |
| 6.1 | op_target: theo op_type | T1 | API232 tr.9 | or through op_type, the format is |
| 6.1 | op_target: ví dụ {'Add':'cpu'} | T1 | API232 tr.9 | e.g., {'Add':'cpu', 'Expand':'cpu' |
| 6.1 | op_target: giá trị cpu, npu, gpu, auto | T1 | API232 tr.9 | The currently available options are: 'cpu' / 'npu' / 'gpu' / 'auto' |
| 6.1 | op_target: auto là tự chọn đích | T1 | API232 tr.9 | 'auto' is for automatically selecting the execution target |
| 6.1 | op_target: tên tensor lấy từ accuracy_analysis | T1 | API232 tr.9 | which can be obtained from the returned results of the accuracy_analysis feature |
| 6.1 | optimization_level mặc định 3 | T1 | API232 tr.8 | Model optimization level. The default value is 3. |
| 6.1 | optimization_level 2 hoặc 1 tắt một số, 0 tắt hết | T1 | API232 tr.8 | When the value is 2 or 1, turn off some optimization options that may affect the accuracy of some models. Turn off all optimization options when the value is 0. |
| 6.1 | UG232 tr.176: level 2 thì Resize dùng CPU | T1 | UG232 tr.176 | the Resize Op will use the CPU |
| 6.1 | T3: Resize INT8 Target NPU ở level 1 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt1_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 6.1 | T3: Resize INT8 Target NPU ở level 2 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt2_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 6.1 | T3: Resize INT8 Target NPU ở level 3 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Resize INT8 NPU (1,256,20,20),(0),(4) |
| 6.1 | T3: lớp Resize thứ hai cũng NPU ở cả ba level (đếm trong gen.py) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Resize INT8 NPU (1,128,40,40),(0),(4) |
| 6.1 | T3: bilinear và FP16 chưa thử | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Chưa thử Resize bilinear, FP16 |
| 6.1 | T3: 119 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "n_layers": 119 |
| 6.1 | T3: Transpose Target CPU INT8 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Transpose INT8 CPU (4,1,1,8400) |
| 6.1 | T3: InputOperator Target CPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | InputOperator UINT8 CPU |
| 6.1 | T3: OutputOperator Target CPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | OutputOperator INT8 CPU |
| 6.1 | T3: Transpose 1 lớp (bảng xếp hạng) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Transpose 1 809 0 0 809 |
| 6.1 | T3: 116 = 119 - 3 lớp CPU (đếm trong gen.py) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 6.1 | T3: lần đo CORE_0_1_2, eval_perf, bảng lớp lấy một lần với perf_debug=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Bảng lớp: một lần `eval_perf` với `perf_debug=True` |
| 6.1 | T3: model YOLOv8n nc=5 trọng số ngẫu nhiên 640x640 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | khởi tạo ngẫu nhiên |
| 6.1 | WorkLoad(0/1/2) chỉ in trên NPU nhiều core | T1 | UG232 tr.75 | is only printed on multi-core NPUs |
| 6.1 | UG152 tr.27: op khác fallback về Core0 | T1 | UG152 tr.27 | Other type of op will fallback to Core0 to continue running. |
| 6.2 | Conv: mục 3.2.5 | T1 | OPL tr.58 | 3.2.5 Convolution |
| 6.2 | Conv: kernel_h ∈ [1,31] | T1 | OPL tr.58 | kernel_h ∈ [1, 31] |
| 6.2 | Conv: kernel_w ∈ [1,31] | T1 | OPL tr.58 | kernel_w ∈ [1, 31] |
| 6.2 | Conv: weight per-layer và per-channel | T1 | OPL tr.58 | per‑channel |
| 6.2 | Conv: stride ∈ [1,7] | T1 | OPL tr.59 | stride_h ∈ [1, 7] |
| 6.2 | Conv: pads ∈ [0,15] | T1 | OPL tr.59 | pads_top ∈ [0, 15] |
| 6.2 | Conv: dilations ∈ [1,31] | T1 | OPL tr.59 | dilations_h ∈ [1, 31] |
| 6.2 | Conv: int8, float16 | T1 | OPL tr.59 | T1: int8(Tensor), float16(Tensor) |
| 6.2 | Conv: 多核联合 支持 | T1 | OPL tr.59 | 其他支持 多核联合: 支持 3.2.6 Depthwise Convolution |
| 6.2 | ConvolutionSwish: mục 3.2.17, ràng buộc như Convolution, 暂不支持 | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish Convolution 与 Swish 融合计算, Output = Swish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.2 | exSwish: mục 3.2.69, SiLU | T1 | OPL tr.98 | Swish 函数也称为 SiLU 函数 |
| 6.2 | exSwish: int8, float16 | T1 | OPL tr.98 | T1: int8(Tensor), float16(Tensor) |
| 6.2 | exSwish: 尚不支持 | T1 | OPL tr.98 | T1: int8(Tensor), float16(Tensor) 其他支持 多核联合: 尚不支持 3.2.70 exMish |
| 6.2 | Sigmoid: mục 3.2.63 | T1 | OPL tr.95 | 3.2.63 Sigmoid |
| 6.2 | Sigmoid: int8, float16, 尚不支持 | T1 | OPL tr.95 | T1: int8(Tensor), float16(Tensor) 其他支持 多核联合: 尚不支持 3.2.64 Tanh |
| 6.2 | Resize: mục 3.2.54 | T1 | OPL tr.86 | 3.2.54 Resize |
| 6.2 | Resize: int8, float16 | T1 | OPL tr.87 | T1: int8(Tensor), float16(Tensor) |
| 6.2 | Resize: chỉ nhân nguyên 2 đến 8 theo H, W | T1 | OPL tr.87 | 目前仅支持宽高方向的整数倍缩放 |
| 6.2 | Resize: mode chỉ nearest, linear | T1 | OPL tr.87 | 目前仅支持 nearest 和 linear 两种可配置 |
| 6.2 | Resize: coordinate_transformation_mode chỉ ba giá trị | T1 | OPL tr.87 | half_pixel，pytorch_half_pixel，align_corners 三种 |
| 6.2 | Resize: 不支持 | T1 | OPL tr.87 | 多核联合: 不支持 |
| 6.2 | Upsample: mục CPU 4.67 | T1 | OPL tr.329 | 4.67 Upsample |
| 6.2 | Upsample: bilinear, nearest2d | T1 | OPL tr.329 | 支持插值方式 bilinear; nearest2d |
| 6.2 | Upsample không có trong OPL 3.2 (tìm toàn văn PDF 56 đến 107) | T1 | (không có) | (unknown) |
| 6.2 | Concat: mục 3.2.4, axis ∈ {0,1,2,3} | T1 | OPL tr.58 | 3.2.4 Concat |
| 6.2 | Concat: axis ∈ {0,1,2,3} | T1 | OPL tr.58 | axis ∈ {0, 1, 2, 3} |
| 6.2 | Concat: int8, float16 | T1 | OPL tr.58 | T: int8(Tensor), float16(Tensor) |
| 6.2 | Concat, Split, MaxPool, Slice không có dòng 多核联合 | T1 | (không có) | (unknown) |
| 6.2 | Split: mục 3.2.59 | T1 | OPL tr.91 | 3.2.59 Split |
| 6.2 | Split: axis ∈ {0,1,2,3} | T1 | OPL tr.91 | axis ∈ {0, 1, 2, 3} |
| 6.2 | MaxPool: mục 3.2.44 | T1 | OPL tr.79 | 3.2.44 MaxPool |
| 6.2 | MaxPool: kernel ∈ (0,7] | T1 | OPL tr.79 | kernel_h ∈ (0, 7] |
| 6.2 | MaxPool: strides ∈ (0,8] | T1 | OPL tr.79 | strides_h ∈ (0, 8] |
| 6.2 | MaxPool: auto_pad chỉ NOTSET | T1 | OPL tr.79 | pad 的方式: 仅支持 NOTSET |
| 6.2 | MaxPool: ceil_mode không hỗ trợ | T1 | OPL tr.79 | 使用 ceil 或 floor 的方式计算输出的 shape : 不支持 |
| 6.2 | MaxPool: pad ∈ [0,7] | T1 | OPL tr.80 | pad_top ∈ [0, 7] |
| 6.2 | Add: mục 3.2.1, 支持 | T1 | OPL tr.56 | 3.2.1 Add |
| 6.2 | Add: 多核联合 支持 | T1 | OPL tr.56 | T2: float(const Tensor) 其他支持 多核联合: 支持 |
| 6.2 | Add: broadcast theo luật Expand | T1 | OPL tr.56 | 广播约束同Expand算子 |
| 6.2 | Expand: mục 3.2.34 | T1 | OPL tr.68 | 3.2.34 Expand |
| 6.2 | Expand: h, w ∈ [1,8192] | T1 | OPL tr.68 | h ∈ [1, 8192], w ∈ [1, 8192] |
| 6.2 | Mul: mục 3.2.41, 支持 | T1 | OPL tr.77 | 3.2.41 Mul |
| 6.2 | Mul: int8, float16, 支持 | T1 | OPL tr.77 | T2: float(const Tensor) 其他支持 多核联合: 支持 |
| 6.2 | Sub: mục 3.2.60 | T1 | OPL tr.91 | 3.2.60 Sub |
| 6.2 | Sub: broadcast [b,c,1,1] hoặc [scalar] | T1 | OPL tr.92 | [scalar] |
| 6.2 | Sub: 不支持 | T1 | OPL tr.92 | T2: float(const Tensor) 其他支持 多核联合: 不支持 3.2.61 Tile |
| 6.2 | Reshape: mục 3.2.53, int8 float16, 尚不支持 | T1 | OPL tr.86 | 3.2.53 Reshape |
| 6.2 | Reshape: 尚不支持 | T1 | OPL tr.86 | 指定输出张量的形状 其他支持 多核联合: 尚不支持 |
| 6.2 | Transpose: mục 3.2.62 | T1 | OPL tr.93 | 3.2.62 Transpose |
| 6.2 | Transpose: giới hạn theo perm với p=8192, q=2048 | T1 | OPL tr.93 | p=8192, q=2048 |
| 6.2 | Transpose: perm=[1,0,2,3] có điều kiện T1 h1*w1<16*p, n1<8192, h1*w1<p | T1 | OPL tr.93 | h1*w1<16*p, n1<8192, h1*w1<p |
| 6.2 | Transpose: có mục perm=[1,0,2,3] | T1 | OPL tr.93 | perm=[1,0,2,3] |
| 6.2 | Transpose: T1 int8, T2 int16, float16 | T1 | OPL tr.95 | T2: int16(Tensor), float16(Tensor) |
| 6.2 | Transpose: 暂不支持 | T1 | OPL tr.95 | T2: int16(Tensor), float16(Tensor) 其他支持 多核联合: 暂不支持 |
| 6.2 | Softmax: mục 3.2.56 | T1 | OPL tr.88 | 3.2.56 Softmax |
| 6.2 | Softmax: bị ràng buộc theo transpose | T1 | OPL tr.88 | 受限于 tranpose 的规格限制 |
| 6.2 | Softmax: axis 1 hoặc 3 | T1 | OPL tr.89 | 做 softmax 的轴: 1,3，即 channel 和 width 方向 |
| 6.2 | Softmax: 尚不支持 | T1 | OPL tr.89 | 其他支持 多核联合: 尚不支持 3.2.57 exSoftmax13 |
| 6.2 | exSoftmax13: mục 3.2.57, 尚不支持 | T1 | OPL tr.89 | 3.2.57 exSoftmax13 |
| 6.2 | Slice: mục 3.2.55 | T1 | OPL tr.88 | 3.2.55 Slice |
| 6.2 | Slice: steps khác 1 chỉ khi điều kiện chứa subc | T1 | OPL tr.88 | steps 可以不为 1 |
| 6.2 | OPL không định nghĩa subc | T1 | (không có) | (unknown) |
| 6.2 | Mục 3.2: 59 mục có dòng 多核联合: 11, 18, 23, 7; 20 mục không có dòng (đếm của bộ hình) | T1 | OPL tr.56 | (số học) |
| 6.2 | OPL không định nghĩa 暂不支持, 尚不支持, 不支持 | T1 | (không có) | (unknown) |
| 6.2 | ConvExSwish có phải ConvolutionSwish không | T1 | (không có) | (unknown) |
| 6.2 | Danh sách YOLOv8 cần op nào không có nguồn | T1 | (không có) | (unknown) |
| 6.2 | T3: ConvExSwish 57 lớp (bảng xếp hạng) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | ConvExSwish 57 0 0 13539 13539 59.46% |
| 6.2 | T3: ConvExSwish INT8 NPU, 100%/0%/0% (một dòng mẫu) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | 603 6.37/6.37/6.37 100.0%/0.0%/0.0% |
| 6.2 | T3: Conv 7 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Conv 7 0 0 764 764 3.36% |
| 6.2 | T3: Concat 17 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Concat 17 0 0 1947 1947 8.55% |
| 6.2 | T3: Split 9 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Split 9 0 0 1078 1078 4.73% |
| 6.2 | T3: MaxPool 3 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | MaxPool 3 0 0 219 219 0.96% |
| 6.2 | T3: Add 8 lớp (SiLU) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Add 8 0 0 744 744 3.27% |
| 6.2 | T3: Add 2 lớp (ReLU) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | Add 2 0 0 157 157 1.05% |
| 6.2 | T3: Mul 2 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Mul 2 0 0 312 312 1.37% |
| 6.2 | T3: Sub 2 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Sub 2 0 0 258 258 1.13% |
| 6.2 | T3: Reshape 7 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Reshape 7 0 0 571 571 2.51% |
| 6.2 | T3: Reshape 3 lớp 0%/0%/0% (một dòng mẫu) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Reshape INT8 NPU (1,64,40,40),(4) (1,64,20,80) 0/0/0 2 0.0%/0.0%/0.0% |
| 6.2 | T3: Resize 2 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Resize 2 0 0 279 279 1.23% |
| 6.2 | T3: Sigmoid 1 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Sigmoid 1 0 0 126 126 0.55% |
| 6.2 | T3: exSoftmax13 1 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | exSoftmax13 1 0 0 2102 2102 9.23% |
| 6.2 | T3: Transpose 1 lớp CPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Transpose 1 809 0 0 809 3.55% |
| 6.2 | T3: Transpose input (4,1,1,8400), output (1,4,1,8400) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (4,1,1,8400) (1,4,1,8400) |
| 6.2 | T3: Concat 15 trong 17 chia 3 core, Conv 6 trong 7, Add cả 8, Mul và Sub core 0 (đếm cột WorkLoad trong gen.py) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 6.2 | T3: không có lớp tên exSwish, Upsample, Slice (bảng xếp hạng liệt kê 15 loại op) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 6.2 | Phép tính: h1*w1 = 1*8400 = 8400 so với p = 8192; perm suy từ shape | T1 | OPL tr.93 | (số học) |
| 6.2 | UG232 tr.75: danh sách op hỗ trợ tách task đa core | T1 | UG232 tr.75 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu. |
| 6.2 | UG232 tr.75: op chưa hỗ trợ tách task | T1 | UG232 tr.75 | does not implement multi-core task segmentation in the NPU driver |
| 6.2 | UG152 tr.27: danh sách tương tự | T1 | UG152 tr.27 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. |
| 6.2 | OPL: Relu 暂不支持 | T1 | OPL tr.84 | 其他支持 多核联合: 暂不支持 3.2.50 Clip/ReLU6 |
| 6.2 | OPL: Clip/ReLU6 暂不支持 | T1 | OPL tr.84 | 3.2.50 Clip/ReLU6 |
| 6.2 | OPL: PRelu 暂不支持 | T1 | OPL tr.85 | 3.2.51 PRelu |
| 6.2 | OPL: LeakyRelu 暂不支持 | T1 | OPL tr.86 | 其他支持 多核联合: 暂不支持 3.2.53 Reshape |
| 6.2 | OPL không có ThresholdedRelu | T1 | (không có) | (unknown) |
| 6.2 | T3: ConvRelu 51 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvRelu 51 0 0 5954 5954 39.69% |
| 6.2 | T3: ConvReluAdd 6 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvReluAdd 6 0 0 648 648 4.32% |
| 6.2 | UG232 tr.176: NPU chưa hỗ trợ Resize cấp phần cứng | T1 | UG232 tr.176 | the NPU does not currently support hardware-level Resize |
| 6.2 | UG232 tr.176: Resize đổi thành ConvTranspose | T1 | UG232 tr.176 | will convert Reszie to ConvTranspose |
| 6.2 | OPSUP: Resize có trong danh sách ONNX | T1 | OPSUP dòng 147 | Resize \| mode: nearest2d/bilinear |
| 6.2 | T3: lớp Transpose duy nhất trên CPU phù hợp với lý do 'size exceeds the limit' (suy ra) | T1 | UG232 tr.139 | The operator size exceeds the limit |
| 6.2 | OPSUP: Upsample chỉ có ở danh sách Caffe | T1 | OPSUP dòng 461 | Upsample \| according to https://github.com/SeanQ88/caffe_upsample |
| 6.2 | Danh sách ONNX của OPSUP không có Upsample (tìm trong dòng 3 đến 196) | T1 | (không có) | (unknown) |
| 6.2 | UG232 tr.75: tải lớp nhỏ hơn đơn vị phân chia thì chạy một core | T1 | UG232 tr.75 | The load of this layer is too small, smaller than the granularity of NPU multi-core task allocation |
| 6.3 | BN gộp vào Conv khi export: forward_fuse không có BN | T1 | ULT nn/modules/conv.py:80-90 | Apply convolution and activation without batch normalization. |
| 6.3 | Ultralytics gọi model.fuse trước khi export | T1 | ULT engine/exporter.py:863 | model = model.fuse(imgsz=self.imgsz) |
| 6.3 | RKNN có tự gộp BN hay không | T1 | (không có) | (unknown) |
| 6.3 | SiLU: y = x * sigmoid(x) | T1 | OPL tr.98 | y = x * sigmoid(x) |
| 6.3 | T3 README: ONNX có 57 bộ Conv/Sigmoid/Mul | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | ONNX có 57 bộ Conv/Sigmoid/Mul |
| 6.3 | Luật ghép SiLU của compiler | T1 | (không có) | (unknown) |
| 6.3 | T3: 57 lớp ConvExSwish, Target NPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | ConvExSwish 57 0 0 13539 13539 59.46% |
| 6.3 | T3: còn lớp Sigmoid tên /model.22/Sigmoid | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Sigmoid:/model.22/Sigmoid |
| 6.3 | T3: 1 Sigmoid, 2 Mul riêng | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Mul 2 0 0 312 312 1.37% |
| 6.3 | T3: 57 ConvExSwish chỉ core 0 ở CORE_0_1_2 (đếm trong gen.py) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 6.3 | OPL 3.2.17 ConvolutionSwish 暂不支持 | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish Convolution 与 Swish 融合计算, Output = Swish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.69 exSwish 尚不支持 | T1 | OPL tr.98 | T1: int8(Tensor), float16(Tensor) 其他支持 多核联合: 尚不支持 3.2.70 exMish |
| 6.3 | T3: ConvRelu 51 lớp, chia 3 core | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvRelu 51 0 0 5954 5954 39.69% |
| 6.3 | T3: ConvRelu mẫu 33.4%/33.4%/33.1% | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | 496 2.90/2.90/2.90 33.4%/33.4%/33.1% |
| 6.3 | T3: ConvReluAdd 6 lớp, chia 3 core | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvReluAdd 6 0 0 648 648 4.32% |
| 6.3 | T3: ConvReluAdd mẫu 33.7%/33.1%/33.1% | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | 163 11.78/11.78/11.78 33.7%/33.1%/33.1% |
| 6.3 | T3: Add 8 (SiLU) xuống 2 (ReLU); 8 - 2 = 6; 57 = 51 + 6 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 6.3 | T3: Add riêng ReLU 2 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | Add 2 0 0 157 157 1.05% |
| 6.3 | T3: README: ReLU còn ghép thêm Add residual | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | ReLU còn ghép thêm phép cộng residual |
| 6.3 | OPL 3.2.7 ConvolutionRelu 支持 | T1 | OPL tr.60 | 3.2.7 ConvolutionRelu Convolution 与 Relu 融合计算, Output = Relu(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 支持 |
| 6.3 | OPL 3.2.8 ConvolutionClip 支持 | T1 | OPL tr.61 | 3.2.8 ConvolutionClip Convolution 与 Clip 融合计算, Output = Clip(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 支持 |
| 6.3 | OPL 3.2.9 ConvolutionPRelu/LeakyRelu 支持 | T1 | OPL tr.61 | LeakyRelu(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 支持 |
| 6.3 | OPL 3.2.10 ConvolutionAdd 支持 | T1 | OPL tr.61 | 3.2.10 ConvolutionAdd Convolution 与 Add 融合计算, Output = Add(Conv(Input0), Input1) 说明及规格限制同Convolution 其他支持 多核联合: 支持 |
| 6.3 | OPL 3.2.19 ConvolutionAddRelu 支持 | T1 | OPL tr.63 | 3.2.19 ConvolutionAddRelu Convolution 与 Add 及 Relu 融合计算, Output = Relu(Add(Conv(Input0), Input1)) 说明及规格限制同Convolution 其他支持 多核联合: 支持 |
| 6.3 | OPL 3.2.11 ConvolutionSigmoid 暂不支持 | T1 | OPL tr.61 | 3.2.11 ConvolutionSigmoid Convolution 与 Sigmoid 融合计算, Output = Sigmoid(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.12 ConvolutionTanh 暂不支持 | T1 | OPL tr.62 | 3.2.12 ConvolutionTanh Convolution 与 Tanh 融合计算, Output = Tanh(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.13 ConvolutionSoftplus 暂不支持 | T1 | OPL tr.62 | 3.2.13 ConvolutionSoftplus Convolution 与 Softplus 融合计算, Output = Softplus(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.14 ConvolutionHardSigmoid 暂不支持 | T1 | OPL tr.62 | 3.2.14 ConvolutionHardSigmoid Convolution 与 HardSigmoid 融合计算, Output = HardSigmoid(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.15 ConvolutionHardSwish 暂不支持 | T1 | OPL tr.62 | 3.2.15 ConvolutionHardSwish Convolution 与 HardSwish 融合计算, Output = HardSwish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.16 ConvolutionElu 暂不支持 | T1 | OPL tr.63 | 3.2.16 ConvolutionElu Convolution 与 Elu 融合计算, Output = Elu(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | OPL 3.2.18 ConvolutionMish 暂不支持 | T1 | OPL tr.63 | 3.2.18 ConvolutionMish Convolution 与 Mish 融合计算, Output = Mish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 6.3 | UG232 tr.142 liệt kê Conv+Activation+Add | T1 | UG232 tr.142 | Conv+Activation+Add |
| 6.3 | Thứ tự bên trong lớp ConvReluAdd | T1 | (không có) | (unknown) |
| 6.3 | UG232 tr.141: toolkit tự tối ưu đồ thị ở mức nào đó | T1 | UG232 tr.141 | this process is not omnipotent and perfect |
| 6.3 | UG232 tr.141: graph optimization to a certain extent | T1 | UG232 tr.141 | already performs graph optimization to a certain extent |
| 6.3 | UG232 tr.141: NPU hỗ trợ fusion một số op | T1 | UG232 tr.141 | NPU supports fusion of some operators |
| 6.3 | UG232 tr.141: đổi thứ tự Transpose và Clip | T1 | UG232 tr.141 | by adjusting the order of the Transpose and Clip operators, the Conv and Clip fusion operations are performed |
| 6.3 | UG232 tr.142: bảng luật fusion phần cứng | T1 | UG232 tr.142 | The hardware fusion rules are as follows: |
| 6.3 | UG232 tr.142: Supported fusion rules | T1 | UG232 tr.142 | Supported fusion rules |
| 6.3 | UG232 tr.142: Conv+Relu | T1 | UG232 tr.142 | Conv+Relu |
| 6.3 | UG232 tr.142: Conv+PRelu(LeakyRelu) | T1 | UG232 tr.142 | Conv+PRelu(LeakyRelu) |
| 6.3 | UG232 tr.142: Conv+Clip | T1 | UG232 tr.142 | Conv+Clip |
| 6.3 | UG232 tr.142: Conv+Sigmoid(Tanh/Elu/Silu...) | T1 | UG232 tr.142 | Conv+Sigmoid(Tanh/Elu/Silu...) |
| 6.3 | UG232 tr.142: Conv+Add | T1 | UG232 tr.142 | Conv+Add |
| 6.3 | UG232 tr.142: Fusion rules supported by future plans | T1 | UG232 tr.142 | Fusion rules supported by future plans |
| 6.3 | UG232 tr.142: Activation+Add(Mul) | T1 | UG232 tr.142 | Activation+Add(Mul) |
| 6.3 | UG232 tr.142: Add(Mul)+Activation | T1 | UG232 tr.142 | Add(Mul)+Activation |
| 6.3 | UG232 tr.142: Conv+Mul | T1 | UG232 tr.142 | Conv+Mul |
| 6.3 | UG232 tr.142: Conv+Activation+Mul | T1 | UG232 tr.142 | Conv+Activation+Mul |
| 6.3 | UG232 tr.142: Conv+Activation+Pooling | T1 | UG232 tr.142 | Conv+Activation+Pooling |
| 6.3 | UG232 tr.142: Conv+Activation+Add(Mul)+Pooling | T1 | UG232 tr.142 | Conv+Activation+Add(Mul)+Pooling |
| 6.3 | UG232 tr.142: bảng luật không nêu chip | T1 | (không có) | (unknown) |
| 6.3 | UG232 tr.141: thay Transpose, Reshape bằng Conv | T1 | UG232 tr.141 | these operators can be integrated into the Conv operator to achieve data rearrangement |
| 6.3 | UG232 tr.142: gộp Slice vào Conv (YOLOv5-nano) | T1 | UG232 tr.142 | integrates several complex Slice numbers into Conv to form a new Conv |
| 6.3 | UG232 tr.143: gộp op giống nhau | T1 | UG232 tr.143 | can be simply merged into the same operator, such as Reshape, Transpose, Slice |
| 6.3 | UG232 tr.148: Split + Sigmoid + Mul thành GLU | T1 | UG232 tr.148 | Split + Sigmoid + Mul -> GLU |
| 6.3 | UG232 tr.148: LayerNorm | T1 | UG232 tr.148 | ReduceMean + Sub + Pow + ReduceMean + Add + Sqrt + Div (+ Mul + Add) -> LayerNorm |
| 6.3 | UG232 tr.147: toolkit ghép đồ thị thành custom operator | T1 | UG232 tr.147 | The RKNN software stack will match certain graph relationships into custom operators |
| 6.3 | API232 tr.8: optimization_level mặc định 3, bật mọi tối ưu | T1 | API232 tr.8 | The default value of this parameter is 3, and all optimization options are turned on. |
| 6.3 | Thuật toán fusion, thứ tự pass, rule bị tắt bởi level 1, 2 | T1 | (không có) | (unknown) |
| 6.3 | T3: bảng op giống hệt ở optimization_level 1, 2, 3 (so trong gen.py) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt1_layers.txt | (số học) |
| 6.3 | UG232 tr.168: tên pass RKNNInitCastConst | T1 | UG232 tr.168 | N4rknn17RKNNInitCastConstE |
| 6.3 | UG232 tr.168: tên pass RKNNMultiSurfacePass | T1 | UG232 tr.168 | N4rknn20RKNNMultiSurfacePassE |
| 6.3 | UG232 tr.168: tên pass RKNNTilingPass | T1 | UG232 tr.168 | N4rknn14RKNNTilingPassE |
| 6.3 | UG232 tr.168: tên pass RKNNProfileAnalysisPass | T1 | UG232 tr.168 | N4rknn23RKNNProfileAnalysisPassE |
| 6.3 | UG232 tr.168: OpEmit | T1 | UG232 tr.168 | start: OpEmit |
| 6.3 | UG232 tr.166: tên hàm graph_optimizer _fuse_ops | T1 | UG232 tr.166 | rknn.api.graph_optimizer.GraphOptimizer._fuse_ops |
| 6.3 | CHANGELOG v2.3.2: graph optimization | T1 | REPO 3rdparty/rknn-toolkit2/CHANGELOG.md:11 | Enhanced graph optimization capabilities |
| 6.3 | CHANGELOG v2.1.0: operator fusion | T1 | REPO 3rdparty/rknn-toolkit2/CHANGELOG.md:51 | Support more operators and operator fusion |
| 6.3 | TVM: operator fusion | T2 | TVM tr.3 | Operator fusion combines multiple operators into a single kernel without saving the intermediate results in memory. |
| 6.3 | LEE24: operator fusion giảm truy cập ngoài chip | T2 | LEE24 tr.1 | Operator fusion is a scheduling method for combining multiple operations to minimize off-chip memory access. |
| 6.3 | LEE24: FM buffer nhỏ hơn dram | T2 | LEE24 tr.2 | the FM buffer (on-chip memory) is much smaller than dram |
| 6.3 | BAMB: mid-end tiling, scheduling | T2 | BAMB tr.4 | the mid-end lowers and optimizes the graph through tiling, scheduling, and memory allocation |
| 6.3 | FLEX: solver tìm tiling cho một lớp DNN | T2 | FLEX tr.1 | used to find a good data tiling and loop ordering of a DNN layer |
| 6.3 | FLEX: áp lên phân chia dữ liệu của lớp trên nhiều NPU | T2 | FLEX tr.1 | these loop transformations are applied to a data partitioning of a layer |
| 6.3 | LENS: compiler NPU thương mại tối ưu khó đoán | T2 | LENS tr.1 | the compilers of commercial NPUs apply graph optimizations in unpredictable ways |
| 6.3 | Buffer 384KB mỗi core là phần cứng | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 6.3 | Thuật toán tiling của Rockchip | T1 | (không có) | (unknown) |
| 6.4 | Thứ tự địa chỉ thấp đến cao: C2, W, H, C1, N | T1 | UG152 tr.56 | The memory address from low to high is C2->W->H->C1->N |
| 6.4 | C2 đổi nhanh nhất, N chậm nhất | T1 | UG152 tr.56 | C2 has the fastest changing rate and N is the slowest one |
| 6.4 | C2 do nền tảng quyết định | T1 | UG232 tr.61 | C2 is determined by the platform |
| 6.4 | C1 là làm tròn lên của C/C2 | T1 | UG232 tr.61 | C1 is the rounded-up value of C/C2 |
| 6.4 | Dữ liệu căn thừa không hợp lệ | T1 | UG232 tr.61 | the remaining three data are additional aligned invalid data |
| 6.4 | UG152 Table 4-6: RK3588 int8 16, float16 8, int16 8 | T1 | UG152 tr.56 | RK3588 16 8 8 |
| 6.4 | UG152 Table 4-6: RK3566/RK3568 8, 4, 4 | T1 | UG152 tr.56 | RK3566/RK3568 8 4 4 |
| 6.4 | UG232 Table 5-1: int8 16, 8, /, 16, 8, 16 | T1 | UG232 tr.61 | int8 16 8 / 16 8 16 |
| 6.4 | UG232 Table 5-1: float16 8, /, 4, 8, 4, 8 | T1 | UG232 tr.61 | float16 8 / 4 8 4 8 |
| 6.4 | UG232 Table 5-1: cột RK3576/RK3588/RV1126B | T1 | UG232 tr.61 | RK3576/RK3588/RV1126B |
| 6.4 | UG232 Table 5-1 không có cột int16; API232 tr.7 không nêu int16 cho RK3588 | T1 | (không có) | (unknown) |
| 6.4 | Ví dụ RK3568: (1,2,4,4,8) khi int8 (1,13,4,4) | T1 | UG232 tr.61 | NC1HWC2 is (1, 2, 4, 4, 8) when the int8 feature data is (1, 13, 4, 4) |
| 6.4 | Ví dụ RK3568: chỉ 5 phần tử đầu hợp lệ | T1 | UG232 tr.61 | only the first five data of each corresponding C2 data blocks are valid |
| 6.4 | Ví dụ RK3588 (1,13,4,4): C1 = ceil(13/16) = 1, (1,1,4,4,16); float16 C2 = 8, C1 = 2, (1,2,4,4,8) | T1 | UG232 tr.61 | (số học) |
| 6.4 | SRAM log: input (1,3,224,224) có NativeShape (1,1,224,224,3) | T1 | SRAM dòng 148 | (1,3,224,224) (1,1,224,224,3) |
| 6.4 | SRAM log: (1,32,112,112) thành (1,2,112,112,16) | T1 | SRAM dòng 149 | (1,32,112,112) (1,2,112,112,16) |
| 6.4 | SRAM log: (1,512,7,7) thành (1,33,7,7,16) | T1 | SRAM dòng 172 | (1,512,7,7) (1,33,7,7,16) |
| 6.4 | SRAM log: (1,1024,7,7) thành (1,67,7,7,16) | T1 | SRAM dòng 173 | (1,1024,7,7) (1,67,7,7,16) |
| 6.4 | ceil(32/16) = 2, ceil(512/16) = 32, ceil(1024/16) = 64 (phép tính) | T1 | SRAM dòng 172 | (số học) |
| 6.4 | Cách chọn C2, C1 cho từng tensor; vì sao NativeShape lệch | T1 | (không có) | (unknown) |
| 6.4 | UG232 tr.69: số kênh 1, 3 hoặc 4 dùng NHWC | T1 | UG232 tr.69 | And the number of input channels is 1, 3 or 4. |
| 6.4 | UG232 tr.69: số kênh khác dùng NC1HWC2 | T1 | UG232 tr.69 | And the number of input channels is not 1, 3, or 4. |
| 6.4 | UG232 tr.177: kênh 1, 3, 4 dùng NHWC, kênh khác NC1HWC2 | T1 | UG232 tr.177 | For channel values 1, 3, and 4, the layout requires using |
| 6.4 | OPL tr.335: ràng buộc chỉ cho zero-copy API | T1 | OPL tr.335 | 该对齐约束仅针对零拷贝 API，普通 API 无此对齐约束 |
| 6.4 | OPL tr.335: w_stride query được, không đổi được | T1 | OPL tr.335 | w_stride 属性查询到，注意:w_stride 不支持更改 |
| 6.4 | OPL tr.336: bảng RK3588 là ảnh; layer đầu, 4 chiều, kênh 1,3,4: int8 16, float16 8; kênh khác 1 | T1 | OPL tr.336 | (đọc từ hình) |
| 6.4 | UG232 tr.65 Table 5-2: cột RK3588 | T1 | UG232 tr.65 | RV1103/RV1106/RV1126B/RK3562/RK3576/RK3588 |
| 6.4 | UG232 tr.65 Table 5-2: Width 16-byte aligned | T1 | UG232 tr.65 | Width 16-byte aligned |
| 6.4 | OPL tr.339: mục 5.2.2 RK3588 | T1 | OPL tr.339 | 5.2.2 RK3588 |
| 6.4 | OPL tr.339: ghi chú 1, NHWC có yêu cầu căn khi NPU làm chuyển output | T1 | OPL tr.339 | 则有对齐要求，CPU 实现的没 |
| 6.4 | OPL tr.339: int8 NHWC kênh 16 | T1 | OPL tr.339 | NHWC 16 对齐 |
| 6.4 | OPL tr.339: NC1HWC2 lớp cuối họ Conv 32 | T1 | OPL tr.339 | 最后一层卷积类算子，32 对齐 |
| 6.4 | OPL tr.339: NC1HWC2 lớp cuối không phải Conv 16, H*W căn 4 | T1 | OPL tr.339 | H*W 要 4 |
| 6.4 | OPL tr.339: float16 NHWC 8 căn | T1 | OPL tr.339 | NHWC 8 对齐 |
| 6.4 | OPL tr.339: float16 NC1HWC2 lớp cuối họ Conv 16 | T1 | OPL tr.339 | 最后一层卷积类算子，16 对齐 |
| 6.4 | OPL 卷积类算子 gồm op nào | T1 | (không có) | (unknown) |
| 6.4 | UG232 tr.144: not mandatory | T1 | UG232 tr.144 | These rules are not mandatory. |
| 6.4 | UG232 Table 8-2: RK3588/RK3576/RV1126B | T1 | UG232 tr.145 | Table 8-2 RK3588/RK3576/RV1126B |
| 6.4 | UG232 Table 8-2: Int8 32 32 64 16 | T1 | UG232 tr.145 | Int8 32 32 64 16 |
| 6.4 | UG232 Table 8-2: Float16 32 16 32 8 | T1 | UG232 tr.145 | Float16 32 16 32 8 |
| 6.4 | Số 16 ở bốn khái niệm; nguồn không nối (đếm của bộ hình) | T1 | UG232 tr.145 | (số học) |
| 6.4 | TVM: layout transformation giữa producer và consumer | T2 | TVM tr.4 | We then perform the proper layout transformation between a producer and a consumer if their preferred data layouts do not match. |
| 6.4 | BAMB: formats quan trọng cho hiệu suất tính | T2 | BAMB tr.5 | Formats are crucial for optimizing compute utilization. |
