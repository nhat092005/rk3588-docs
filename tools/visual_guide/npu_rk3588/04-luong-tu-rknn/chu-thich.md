# Phần 4: Lượng tử RKNN

## Câu hỏi mở đầu
Khi convert một model sang RKNN cho RK3588, RKNN-Toolkit2 cho chọn những kiểu, thuật toán, phương pháp lượng tử nào, làm sao tìm lớp gây sai số, và những chỗ nào trong bộ tài liệu 2.3.2 tự mâu thuẫn?

## Hình 4.1 (h4-1-ho-tro-rk3588) [T1 RK3588]
Với target_platform là rk3588, trong ba tham số lượng tử của rknn.config chỉ quantized_dtype = w8a8 (mặc định) không bị API Reference ghi giới hạn sang chip khác, còn quantized_algorithm và quantized_method đều có giá trị dùng được là normal, mmse, kl_divergence và layer, channel. Giá trị gdq (chỉ hợp lệ với w4a16 và w8a16) và group{SIZE} (chỉ hợp lệ khi w4a16) bị loại cho RK3588 bằng một suy ra của bộ hình từ hai câu T1 (ô nền xanh), không phải một câu của vendor. Per-channel chỉ áp dụng cho weight, activation vẫn per-layer; số ảnh calibration đề xuất khác nhau theo thuật toán. Nửa dưới hình gom các quy tắc của build: do_quantization mặc định True, cách build FP16 (do_quantization=False với model float), cách nạp model đã lượng tử, QAT, và các quy tắc cho dataset calibration. Khung T3 là phép thử trên PC: config() với rk3588 từ chối w8a16 và w4a16 nhưng nhận w16a16i dù API Reference ghi chỉ RV1103/RV1106, nên "chấp nhận ở config()" chưa chứng minh phần cứng hỗ trợ.
Đọc thêm: 04_ mục 4.1, 4.2, 4.5, 4.6. Số đo: Hình 10.6
Khái niệm: Hình 3.1, Hình 3.2, Hình 3.3, Hình 3.5

## Hình 4.2 (h4-2-hybrid) [T1 RK3588]
Hybrid quantization gồm bốn bước: hybrid_quantization_step1 sinh ba file (.model, .data, .quantization.cfg), sửa mục custom_quantize_layers trong file cfg, hybrid_quantization_step2 tạo model rồi export_rknn mới lưu file .rknn, cuối cùng suy luận. Lớp được đưa về FP16 chạy chậm hơn trên NPU, nên đây là đổi tốc độ lấy độ chính xác; nên chọn lớp theo kết quả accuracy analysis (Hình 4.3). hybrid_quantization_step2 trả 0 hoặc -1 và chỉ có ba tham số đầu vào; việc nó không tự ghi file .rknn là suy ra của bộ hình từ danh sách tham số, từ Hình 6-4 của UG232 và từ ví dụ chính thức (ô nền xanh). auto_hybrid thay bước sửa tay: khi đang lượng tử, lớp có cosine distance dưới ngưỡng (mặc định 0.98) chuyển sang FP16, chỉ cho w8a8; khi model chưa lượng tử, lớp vượt khoảng FP16 chuyển sang INT16. Hình đánh dấu unknown bốn điều: hướng so sánh của ngưỡng euclidean (hai tài liệu nói ngược nhau), kiểu int8 và int16 trên RK3588, hành vi của proposal=False, ngữ nghĩa của quantized_hybrid_level.
Đọc thêm: 04_ mục 4.3.
Khái niệm: Hình 3.5

## Hình 4.3 (h4-3-phan-tich-sai-so) [T1 RK3588]
accuracy_analysis so từng lớp của model float (golden) với model đã lượng tử trên simulator, và với NPU nếu đặt target, rồi ghi bốn nhóm cột sai số vào error_analysis.txt; nó gọi được sau build hoặc hybrid_quantization_step2 và không dùng được sau load_rknn. Cột entire là sai số tích lũy từ đầu đến lớp hiện tại, cột single dùng đầu vào golden của lớp hiện tại nên phản ánh sai số của riêng lớp; runtime_error có thêm single_sim so board với simulator. Quy trình của vendor (UG232 chương 7, Hình 7-1) đi theo thứ tự Simulator FP16, Simulator Quant, Connect Test, Runtime Test: bước sau chỉ có ý nghĩa khi bước trước đúng. Khi Simulator Quant sai, vendor gợi ý thử theo thứ tự cấu hình, một ảnh, layer sang channel, normal sang kl_divergence hoặc mmse, hybrid, rồi QAT. Quy trình này là của vendor cho model thông thường; nguồn không có bản áp dụng riêng cho YOLOv8 hay PPE (unknown).
Đọc thêm: 04_ mục 4.4, 4.6, 4.7. Số đo: Hình 10.7
Khái niệm: Hình 3.5
Hình gốc: ../../npu_study/images/04_quantization_rknn/ug232_p131_fig7-1.png (UG232 tr.131, Figure 7-1; nhúng để đối chiếu lưu đồ vẽ lại với hình của vendor, nhất là chiều mũi tên fail và ok)

## Hình 4.4 (h4-4-mau-thuan-tai-lieu) [T1 RK3588]
Bộ tài liệu 2.3.2 không nhất quán ở 10 chỗ; API Reference và rknn.py khớp nhau về mặc định và danh sách giá trị nên guide theo hai nguồn này, còn UG232 tr.22, 122 mô tả khác code. Hàng 1 đến 3 (kiểu mặc định, danh sách thuật toán, mặc định của do_quantization) được phân xử bằng code. Hàng 5, 6, 8 không có code hay nguồn thứ ba phân xử nên để unknown; hàng 7 theo UG232 vì khớp ví dụ chính thức. Hàng 10 không phải hai trang tài liệu mâu thuẫn mà là ví dụ so với khuyến nghị. UG232 ghi ngày phát hành 2025-04-03, sau API Reference 2025-4-1, nên "UG232 cũ hơn" không đúng: chỉ có thể nói phần mô tả không theo kịp code.
Đọc thêm: 00_ mục 5; 04_ phần "Mâu thuẫn".
Khái niệm: Hình 4.1

## Hiểu sai thường gặp
- "quantized_dtype mặc định là asymmetric_quantized-8" -> mặc định là w8a8; chuỗi cũ nằm ở UG232 tr.22 và tr.122. Trên PC, config() vẫn nhận chuỗi cũ và cho quant_tab giống w8a8 [API232 tr.7; RKNNPY rknn.py:56; UG232 tr.122; LOG 2026-10-10_t3-calibration-pc/README.md] (Hình 4.1, Hình 4.4)
- "do_quantization mặc định là False" -> mặc định True [API232 tr.14; RKNNPY rknn.py:188; UG232 tr.122 viết 'False'] (Hình 4.4)
- "Calibration luôn 20 đến 200 ảnh" -> API232 tr.8 đề xuất theo thuật toán (normal và kl_divergence 20-100, mmse 20-50, gdq trên 200); UG232 tự khác nhau (tr.28 theo thuật toán, tr.122, 133, 134 và 159 nêu 20-200) [API232 tr.8; UG232 tr.28, 122, 159] (Hình 4.1, Hình 4.4)
- "RK3588 dùng được gdq hoặc w4a16" -> w4a16 ghi "Only RK3576/RV1126B supported"; gdq chỉ hợp lệ với w4a16 và w8a16 (w8a16 ghi "Only RK3562 supported"), nên không dùng cho RK3588 (suy ra của bộ hình từ hai câu T1) [API232 tr.7, 8] (Hình 4.1)
- "hybrid_quantization_step2 ghi file .rknn" -> step2 trả 0 hoặc -1 và chỉ nhận ba đường dẫn đầu vào; file .rknn do export_rknn lưu, và ví dụ chính thức gọi export_rknn ngay sau step2 (suy ra của bộ hình) [API232 tr.15, 21; UG232 tr.124; REPO examples/functions/hybrid_quant/step2.py:13-23] (Hình 4.2)
- "Per-channel lượng tử cả activation" -> chỉ áp dụng cho weight; activation và giá trị trung gian vẫn per-layer [UG232 tr.120] (Hình 4.1)
- "accuracy_analysis dùng được sau load_rknn" -> không, vì model RKNN thiếu thông tin model gốc [UG232 tr.30; API232 tr.15] (Hình 4.3)
- "quant_img_RGB2BGR=True thì inference tự đổi kênh" -> tham số chỉ ảnh hưởng việc đọc ảnh ở bước lượng tử và không ghi vào model; dữ liệu lúc inference phải tự đúng thứ tự kênh. Câu Note ở UG232 tr.22 nói ngược lại, cùng trang có câu nói không có tác dụng ở bước inference [API232 tr.7; UG232 tr.22, 158] (Hình 4.4)
- "Thêm ảnh calibration thì luôn chính xác hơn" -> thêm ảnh làm thuật toán chạy lâu hơn, chưa chắc chính xác hơn [UG232 tr.122] (Hình 4.1)
- "config() nhận w16a16i nghĩa là RK3588 hỗ trợ" -> API232 ghi chỉ RV1103/RV1106; đo trên PC thấy config() trả 0, và README của log nói chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ [API232 tr.7; LOG 2026-10-10_t3-calibration-pc/README.md] (Hình 4.1)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao gdq và group{SIZE} không dùng được cho RK3588, và đây là câu của vendor hay suy ra?
Đáp án: gdq chỉ hợp lệ với w4a16 và w8a16, group{SIZE} chỉ hợp lệ khi quantized_dtype = w4a16, mà w4a16 ghi "Only RK3576/RV1126B supported" và w8a16 ghi "Only RK3562 supported". Ghép các câu ra kết luận cho RK3588 là suy ra của bộ hình từ hai câu T1, không phải câu của vendor [API232 tr.7, 8] (Hình 4.1)
### Câu 2 (phân biệt)
Phân biệt cột entire và single của simulator_error, và nói cột single_sim của runtime_error cho biết điều gì.
Đáp án: entire so kết quả simulator với golden từ đầu đến lớp hiện tại nên sai số tích lũy qua các lớp; single lấy đầu vào golden của lớp hiện tại rồi so, nên phản ánh sai số của riêng lớp. single_sim so kết quả chạy thật ở board với kết quả simulator khi dùng đầu vào golden của lớp hiện tại; nếu nó thấp (vàng hoặc đỏ) và khoảng cách giữa entire của runtime_error với entire của simulator_error tăng dần, có thể runtime làm lớp đó sai [UG232 tr.31, 135; REPO examples/functions/accuracy_analysis/README.md:19-21] (Hình 4.3)
### Câu 3 (áp dụng)
Model YOLO INT8 chạy trên RK3588 cho kết quả lệch so với model gốc. Theo vendor, kiểm tra theo thứ tự nào và việc đầu tiên là gì? Nguồn có bản áp dụng riêng cho YOLO không?
Đáp án: Việc đầu tiên là Simulator FP16: build với do_quantization=False, init_runtime(target=None), so với model gốc bằng cosine distance, vì FP16 đúng là điều kiện để lượng tử đúng. Sau đó Simulator Quant (cấu hình, thử một ảnh, layer sang channel, normal sang kl_divergence hoặc mmse, hybrid, QAT), rồi Connect Test, rồi Runtime Test. Nguồn không có quy trình áp dụng riêng cho YOLOv8 hay PPE: unknown [UG232 tr.131, 132, 134, 135] (Hình 4.3)
### Câu 4 (áp dụng)
Bạn sửa file .quantization.cfg rồi gọi hybrid_quantization_step2 và nhận 0. Còn thiếu bước nào trước khi có file để deploy, và lớp được đưa về FP16 ảnh hưởng gì tới tốc độ?
Đáp án: Còn gọi export_rknn(export_path) để lưu file .rknn (step2 không có tham số đường dẫn xuất; ví dụ chính thức gọi export_rknn ngay sau step2). Lớp được tính bằng FP16 chạy chậm hơn trên NPU, nên giảm tốc độ suy luận [API232 tr.15, 21; UG232 tr.123, 124; REPO examples/functions/hybrid_quant/step2.py:13-23] (Hình 4.2)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 4.1 | quantized_dtype mặc định w8a8 | T1 | API232 tr.7 | The default value is "w8a8". |
| 4.1 | w8a8: weight và activation 8-bit asymmetric | T1 | API232 tr.7 | w8a8: The weight is 8bit asymmetric quantitative accuracy |
| 4.1 | w8a8: RK2118 không hỗ trợ | T1 | API232 tr.7 | (RK2118 not supported) |
| 4.1 | w4a16: weight 4-bit, activation FP16; chỉ RK3576/RV1126B | T1 | API232 tr.7 | the activation value is 16bit floating point accuracy. (Only RK3576/RV1126B supported) |
| 4.1 | w8a16: chỉ RK3562 | T1 | API232 tr.7 | (Only RK3562 supported) |
| 4.1 | w4a8: chưa hỗ trợ | T1 | API232 tr.7 | (Not supported yet) |
| 4.1 | w16a16i: chỉ RV1103/RV1106 | T1 | API232 tr.7 | (Only RV1103/RV1106 supported) |
| 4.1 | w16a16i_dfp: 16-bit dynamic fixed-point | T1 | API232 tr.7 | w16a16i_dfp: The weight is 16bit dynamic fixed-point quantitative accuracy |
| 4.1 | Danh sách thuật toán và mặc định normal | T1 | API232 tr.8 | Currently support: normal, mmse, kl_divergence and gdq. The default value is normal. |
| 4.1 | normal: nhanh, khoảng 20-100 ảnh | T1 | API232 tr.8 | The characteristic of normal quantization algorithm is fast. |
| 4.1 | normal: khoảng 20-100 ảnh | T1 | API232 tr.8 | The recommended quantization data is generally about 20-100 pieces. with more data |
| 4.1 | mmse: chậm do lặp vét cạn, thường chính xác hơn normal | T1 | API232 tr.8 | The mmse quantization algorithm is slower due to the violent iteration method |
| 4.1 | mmse: khoảng 20-50 ảnh | T1 | API232 tr.8 | The recommended quantization data is generally about 20-50 pieces. |
| 4.1 | kl_divergence: lâu hơn normal, ít hơn mmse | T1 | API232 tr.8 | will take more time than normal, but will be much less than mmse |
| 4.1 | kl_divergence: tốt hơn khi feature phân bố không đều; khoảng 20-100 ảnh | T1 | API232 tr.8 | better improvement effects can be obtained by kl_divergence. the recommended quantization data is generally about 20-100 pieces. |
| 4.1 | gdq: chỉ hợp lệ với w4a16 và w8a16 | T1 | API232 tr.8 | The gdq quantization algorithm is only valid at w4a16 and w8a16 |
| 4.1 | gdq: hơn 200 ảnh | T1 | API232 tr.8 | more than 200 pieces |
| 4.1 | Bỏ gdq và group{SIZE} cho RK3588 (suy ra của bộ hình từ hai câu T1) | T1 | API232 tr.8 | (số học) |
| 4.1 | quantized_method: layer, channel, group{SIZE}; mặc định channel | T1 | API232 tr.8 | Currently support layer, channel or group{SIZE}. The default value is channel. |
| 4.1 | layer: mỗi weight một bộ tham số | T1 | API232 tr.8 | layer: each weight has only one set of quantization parameters. |
| 4.1 | channel: mỗi channel của weight một bộ tham số | T1 | API232 tr.8 | channel: each channel of weight has its own set of quantization parameters. |
| 4.1 | channel thường chính xác hơn layer | T1 | API232 tr.8 | usually the channel will be more accurate than the layer. |
| 4.1 | group{SIZE}: chia weight của mỗi output channel theo input channel | T1 | API232 tr.8 | the weight of each output channel is subdivided into multiple groups according to {SIZE} on the input channel |
| 4.1 | SIZE là bội của 32 từ 32 đến 256 | T1 | API232 tr.8 | {SIZE} is the multiple value of 32 between 32 and 256 |
| 4.1 | group{SIZE} chỉ hợp lệ khi w4a16 | T1 | API232 tr.8 | group{SIZE} is currently only valid when quantized_dtype = w4a16. |
| 4.1 | rknn.py: mặc định quantized_dtype | T1 | RKNNPY rknn/api/rknn.py:56 | quantized_dtype='w8a8', |
| 4.1 | rknn.py: mặc định quantized_algorithm | T1 | RKNNPY rknn/api/rknn.py:57 | quantized_algorithm='normal', |
| 4.1 | rknn.py: mặc định quantized_method | T1 | RKNNPY rknn/api/rknn.py:58 | quantized_method='channel', |
| 4.1 | rknn.py: danh sách thuật toán, mặc định normal | T1 | RKNNPY rknn/api/rknn.py:85 | currently support: normal, mmse (Min Mean Square Error), kl_divergence, gdq. default is normal. |
| 4.1 | rknn.py: SIZE bội của 32 | T1 | RKNNPY rknn/api/rknn.py:87 | {SIZE} is the multiple value of 32 between 32 and 256 |
| 4.1 | Per-channel chỉ áp dụng cho weight, activation per-layer | T1 | UG232 tr.120 | Per-Channel quantization is only applied to the weights, while the activation values and intermediate values are still quantized using Per-Layer quantization. |
| 4.1 | Per-layer: mọi channel dùng chung tham số | T1 | UG232 tr.120 | all channels share the same quantization parameters |
| 4.1 | Per-channel: mỗi channel có tham số riêng | T1 | UG232 tr.120 | each channel has its own quantization parameters |
| 4.1 | Ba hình chữ nhật weight và một hình activation là minh họa của bộ hình | T1 | UG232 tr.120 | (số học) |
| 4.1 | do_quantization mặc định True | T1 | API232 tr.14 | do_quantization: Whether to quantize the model. The default value is True. |
| 4.1 | do_quantization=False với model float: weight float32 sang float16 | T1 | UG232 tr.165 | will convert the weights from float32 to float16, with almost no accuracy loss |
| 4.1 | do_quantization=False với model đã lượng tử: dùng tham số trong model | T1 | UG232 tr.165 | do_quantization=False of the rknn.build() interface will use the quantization parameters in the model. |
| 4.1 | Build FP16: do_quantization đặt False | T1 | UG232 tr.131 | To convert the original model to an FP16 RKNN model, use the rknn.build() interface with the do_quantization parameter set False. |
| 4.1 | Bật lượng tử thì cần dataset | T1 | UG232 tr.158 | When enabling quantization, dataset parameter in the rknn.build() interface is required to specify the quantization data. |
| 4.1 | QAT: load_pytorch nhận model QAT, cần torch 1.9.0 trở lên | T1 | API232 tr.13 | Support the Quantization Aware Training (QAT) model, but need update torch version to '1.9.0' or higher. |
| 4.1 | QAT: RKNN nhận model từ giao diện FX prepare_qat_fx | T1 | UG232 tr.127 | RKNN currently supports quantized models generated from the FX interface, specifically the prepare_qat_fx interface and its associated interfaces. |
| 4.1 | dataset: mỗi dòng một đường dẫn | T1 | API232 tr.14 | A file path for each line. |
| 4.1 | dataset: nhiều input cách nhau bằng dấu cách | T1 | API232 tr.14 | If there are multiple inputs, the corresponding files are divided by space. |
| 4.1 | dataset: mỗi dòng là một bộ input | T1 | UG232 tr.158 | The rule is that one line serves as a set of inputs. |
| 4.1 | Chọn ảnh cùng bối cảnh dự đoán | T1 | API232 tr.14 | It is generally recommended to select the quantization image which is consistent with the prediction scene. |
| 4.1 | Calibration phủ các phân bố dữ liệu của ứng dụng | T1 | UG232 tr.122 | it should cover different data distributions in the actual application scenarios of the model. |
| 4.1 | Thêm ảnh làm chạy lâu hơn, chưa chắc chính xác hơn | T1 | UG232 tr.122 | will increase the runtime of the quantization algorithm but may not necessarily improve quantization accuracy |
| 4.1 | Ảnh khác kích thước input được tự resize, nên dùng đúng kích thước | T1 | UG232 tr.165 | RKNN-Toolkit2 will automatically resize these images. However, the resize operation may also change the image information |
| 4.1 | npy phải khớp shape input | T1 | UG232 tr.165 | it needs to be consistent with the shape input by the model. |
| 4.1 | Input không phải ảnh RGB/BGR: nên dùng npy | T1 | UG232 tr.158 | For models with non-RGB/BGR image input, it is recommended to use numpy's npy format to provide quantization data. |
| 4.1 | quant_img_RGB2BGR chỉ hợp lệ với jpg, png, bmp | T1 | API232 tr.7 | this configuration is only valid for the quantized image format of jpg/png/bmp. |
| 4.1 | quant_img_RGB2BGR bị bỏ qua với npy | T1 | API232 tr.7 | This configuration is ignored when the npy format is read. |
| 4.1 | mean, std áp dụng lên dữ liệu calibration trước | T1 | UG232 tr.132 | the quantization correction dataset will undergo normalization first |
| 4.1 | rknn_batch_size chỉ đổi chiều batch của model xuất | T1 | UG232 tr.165 | will only modify the batch dimension of the finally exported RKNN model |
| 4.1 | Dữ liệu calibration chuẩn bị như model không batch | T1 | UG232 tr.165 | the quantization correction data should be prepared like a non-batch model. |
| 4.1 | rknn.py: do_quantization mặc định True | T1 | RKNNPY rknn/api/rknn.py:188 | def build(self, do_quantization=True, dataset=None |
| 4.1 | T3: PC, toolkit 2.3.2, target_platform rk3588 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | target_platform='rk3588' |
| 4.1 | T3: w8a16 và w4a16 báo not support in rk3588 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | not support in 'rk3588' |
| 4.1 | T3: config() trả 0 với w8a8, w16a16i, w16a16i_dfp, asymmetric_quantized-8 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | trả 0 |
| 4.1 | T3: chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | chưa chứng minh phần cứng hỗ trợ |
| 4.1 | Số bin và cách clipping của normal, mmse, kl_divergence trong toolkit | T1 | (không có) | (unknown) |
| 4.1 | Số ảnh calibration cho miền hẹp như PPE | T1 | (không có) | (unknown) |
| 4.2 | step1 sinh .model, .data, .quantization.cfg | T1 | API232 tr.20 | the data file (<model_name>.data), and the quantization configuration file |
| 4.2 | Hybrid gồm bốn bước | T1 | UG232 tr.123 | it involves four specific steps. |
| 4.2 | Bước 1: RKNN(), config, load, step1, release (Hình 6-3) | T1 | UG232 tr.123 | (đọc từ hình) |
| 4.2 | step1: tham số proposal | T1 | API232 tr.20 | proposal: Generate hybrid quantization config suggestions. The default value is False. |
| 4.2 | step1: tham số custom_hybrid | T1 | API232 tr.21 | custom_hybrid: Select the hybrid quantization subgraph according to multiple sets of input |
| 4.2 | step1: chữ ký hàm trong code | T1 | RKNNPY rknn/api/rknn.py:200 | def hybrid_quantization_step1(self, dataset='dataset.txt', rknn_batch_size=None, proposal=False, proposal_dataset_size=1, custom_hybrid=None): |
| 4.2 | Chọn lớp theo kết quả accuracy analysis | T1 | UG232 tr.123 | should be quantized based on the output results of accuracy analysis. |
| 4.2 | Lớp về FP16 chạy chậm hơn trên NPU | T1 | UG232 tr.123 | non-quantized computation on the NPU has lower performance, resulting in reduced inference speed. |
| 4.2 | Không khuyến nghị sửa quantization parameters | T1 | UG232 tr.123 | It is not recommended to modify the quantization parameters. |
| 4.2 | Mẫu cfg: custom_quantize_layers và tên tensor | T1 | UG232 tr.124 | Conv__350:0: float16 |
| 4.2 | Mẫu cfg: các trường của quantize_parameters | T1 | UG232 tr.124 | qtype: asymmetric_quantized qmethod: layer dtype: int8 |
| 4.2 | custom_quantize_layers: thêm tên tensor và kiểu | T1 | UG232 tr.124 | users can add custom quantization layers by specifying the tensor name followed by the quantization type. |
| 4.2 | Kiểu hiện có trong cfg là float16 | T1 | UG232 tr.124 | Currently, the available quantization data type is "float16". |
| 4.2 | Xem tên tensor bằng Netron | T1 | UG232 tr.124 | use Netron to open the temporary model file named {model_name}.model |
| 4.2 | step2: ba tham số đầu vào, tham số cfg | T1 | API232 tr.21 | model_quantization_cfg: Path to the modified model quantization configuration file |
| 4.2 | step2: trả 0 hoặc -1 | T1 | API232 tr.21 | -1: failure. |
| 4.2 | step2: chữ ký hàm trong code | T1 | RKNNPY rknn/api/rknn.py:214 | def hybrid_quantization_step2(self, model_input, data_input, model_quantization_cfg): |
| 4.2 | step2 không có tham số đường dẫn xuất file; file do export_rknn lưu (suy ra của bộ hình) | T1 | API232 tr.21 | (số học) |
| 4.2 | Bước 3: RKNN(), step2, export_rknn, release (Hình 6-4) | T1 | UG232 tr.124 | (đọc từ hình) |
| 4.2 | export_rknn lưu file .rknn | T1 | API232 tr.15 | Save RKNN model in the specified file |
| 4.2 | export_rknn trong code | T1 | RKNNPY rknn/api/rknn.py:224-234 | Export rknn model to file |
| 4.2 | Ví dụ chính thức gọi export_rknn ngay sau step2 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/step2.py:13-23 | ret = rknn.export_rknn('./ssd_mobilenet_v2.rknn') |
| 4.2 | Bước 4: suy luận bằng model của bước 3 | T1 | UG232 tr.125 | Perform inference using the RKNN model generated in the third step. |
| 4.2 | auto_hybrid khi đang lượng tử: FP16, chỉ w8a8 | T1 | API232 tr.14 | enabling auto_hybrid will convert operations with cosine distance and euclidean distance below the specified thresholds to FP16 computation (currently only supported for 'w8a8' quantization) |
| 4.2 | auto_hybrid khi chưa lượng tử: vượt khoảng FP16 thì INT16 | T1 | API232 tr.14 | When the model is not quantized, enabling auto_hybrid will convert operations that exceed the FP16 value range to INT16 computation. |
| 4.2 | Ngưỡng cosine mặc định 0.98 | T1 | API232 tr.10 | The threshold for cosine distance in automatic hybrid quantization during model quantization. The default value is 0.98. |
| 4.2 | Ngưỡng euclidean mặc định None, không bật | T1 | API232 tr.10 | The default value is None, meaning it is not enabled. |
| 4.2 | rknn.py: ngưỡng cosine mặc định 0.98 | T1 | RKNNPY rknn/api/rknn.py:76 | auto_hybrid_cos_thresh=0.98, |
| 4.2 | rknn.py: ngưỡng euclidean mặc định None | T1 | RKNNPY rknn/api/rknn.py:77 | auto_hybrid_euc_thresh=None, |
| 4.2 | UG232: chỉ hỗ trợ tự chỉnh từ int8 sang fp16 | T1 | UG232 tr.125 | Currently, only automatic adjustment from int8 quantization to fp16 is supported. |
| 4.2 | UG232: mặc định chỉ ngưỡng cosine bật, euclidean tắt | T1 | UG232 tr.125 | only operators whose cosine distance precision is specified less than the threshold are converted to fp16 by default, and the Euclidean distance threshold is turned off at this time. |
| 4.2 | UG232: model chưa lượng tử cần dataset để tính khoảng giá trị | T1 | UG232 tr.125 | you need to provide a dataset to calculate the numerical range of |
| 4.2 | UG232: hướng so sánh euclidean | T1 | UG232 tr.125 | the greater than euclidean distance threshold |
| 4.2 | step1.py: kiểu cho phép int8, int16, float16 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/step1.py:47 | Currently supported data types are: 'int8', 'int16', 'float16'. |
| 4.2 | step1.py: gọi với proposal=False | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/step1.py:28 | ret = rknn.hybrid_quantization_step1(dataset='./dataset.txt', proposal=False) |
| 4.2 | step1.py: cfg tự điền một số lớp (mâu thuẫn với proposal=False) | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/step1.py:49-50 | the configuration file will automatically fill in some layers that may cause a decrease in |
| 4.2 | changelog: proposal=False không sinh lớp gợi ý | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/doc/changelog-2.3.2.txt:399 | proposal=False不生成推荐层 |
| 4.2 | rknn.py: quantized_hybrid_level có trong code | T1 | RKNNPY rknn/api/rknn.py:59 | quantized_hybrid_level=0, |
| 4.2 | Hướng so sánh euclidean thật của auto_hybrid | T1 | (không có) | (unknown) |
| 4.2 | int8, int16 trong custom_quantize_layers chạy được trên RK3588 | T1 | (không có) | (unknown) |
| 4.2 | proposal=False có điền lớp gợi ý hay không | T1 | (không có) | (unknown) |
| 4.2 | Ngữ nghĩa của quantized_hybrid_level | T1 | (không có) | (unknown) |
| 4.3 | accuracy_analysis chỉ gọi sau build hoặc step2 | T1 | API232 tr.22 | This interface can only be called after build or hybrid_quantization_step2. |
| 4.3 | Không dùng được sau load_rknn | T1 | UG232 tr.30 | the model accuracy analysis function can not be used because the RKNN model lacks the original model information. |
| 4.3 | load_rknn: không dùng cho simulator hay accuracy analysis | T1 | API232 tr.15 | It can not be used for simulator or accuracy analysis. |
| 4.3 | Model QAT và target=None: lỗi | T1 | API232 tr.22 | If target is None and the original model is quantized model (QAT model), the call will fail. |
| 4.3 | inputs: jpg, png, bmp, npy | T1 | API232 tr.22 | inputs: the path list of image (jpg/png/bmp/npy). |
| 4.3 | Không đặt target: các thư mục xuất | T1 | API232 tr.22 | If the target is not set, the following content will be output under |
| 4.3 | Thư mục golden: model float trên simulator | T1 | API232 tr.22 | Directory golden: Save the results of each layer on simulator when the entire floating-point |
| 4.3 | Thư mục simulator: model lượng tử trên simulator | T1 | API232 tr.22 | Directory simulator: Save the results of each layer on simulator when the entire quantitative |
| 4.3 | Đầu ra đổi sang float32 | T1 | API232 tr.22 | (The output has been converted to float32). |
| 4.3 | Đặt target: thêm thư mục runtime | T1 | API232 tr.22 | If the target is set, more content will output under |
| 4.3 | Thư mục runtime: model lượng tử trên NPU | T1 | API232 tr.22 | Directory runtime: Save the results of each layer when the entire quantitative model is fully |
| 4.3 | API232 gọi cột là entire_error và single_error | T1 | API232 tr.22 | cosine distance (entire_error and single_error) |
| 4.3 | Chia bốn nhóm cột | T1 | UG232 tr.30 | It is divided into 4 columns of accuracy |
| 4.3 | simulator_error entire: simulator so golden từ đầu đến lớp hiện tại | T1 | UG232 tr.31 | The cosine distance and Euclidean distance from the beginning to the current layer simulator result compared with the golden result. |
| 4.3 | simulator_error single: đầu vào golden của lớp hiện tại | T1 | UG232 tr.31 | When using the current layer golden input, the cosine distance and |
| 4.3 | runtime_error entire: kết quả thật so golden | T1 | UG232 tr.31 | The cosine distance and Euclidean distance between the actual result and the golden result from the beginning to the end of the current layer. |
| 4.3 | runtime_error single_sim: board so simulator | T1 | UG232 tr.31 | the actual result of the current layer at the board end and the simulator result are compared. |
| 4.3 | entire tích lũy qua các lớp (ví dụ chính thức) | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/accuracy_analysis/README.md:20 | these errors will accumulate layer by layer. |
| 4.3 | single phản ánh độ chính xác của riêng lớp (ví dụ chính thức) | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/accuracy_analysis/README.md:21 | can better reflect the single-layer accuracy of the simulator. |
| 4.3 | Simulator đúng là điều kiện cho runtime đúng | T1 | UG232 tr.131 | Correct simulator inference results are the prerequisite for correct board-side runtime inference. |
| 4.3 | FP16 đúng thì lượng tử mới đúng | T1 | UG232 tr.131 | FP16 inference results must be correct for quantization inference to be correct. |
| 4.3 | Nhãn Hình 7-1 | T1 | UG232 tr.131 | Figure 7-1 The step of accuracy analysis |
| 4.3 | Lưu đồ: Runtime Error, Simulator FP16, Simulator Quant, Connect Test, Runtime Test, Runtime OK và các danh sách fail | T1 | UG232 tr.131 | (đọc từ hình) |
| 4.3 | Simulator FP16: init_runtime(target=None) | T1 | UG232 tr.131 | call rknn.init_runtime(target=None) |
| 4.3 | FP16: so với model gốc bằng cosine distance | T1 | UG232 tr.132 | cosine distance can be used to judge consistency |
| 4.3 | FP16: mean_values, std_values | T1 | UG232 tr.132 | mean_values / std_values: Normalization parameters of the model. |
| 4.3 | FP16: input_size_list | T1 | UG232 tr.132 | input_size_list: If the input node shape information |
| 4.3 | FP16: inputs, outputs | T1 | UG232 tr.132 | inputs / outputs: If the input and output node names |
| 4.3 | FP16: tham số inference, BGR của cv2.imread | T1 | UG232 tr.132 | the image format read by cv2.imread() is BGR |
| 4.3 | FP16: layout NHWC của cv2.imread | T1 | UG232 tr.132 | The layout of the image read by cv2.imread() is NHWC |
| 4.3 | FP16: tràn FP16 | T1 | UG232 tr.133 | exceeding the FP16 expression range |
| 4.3 | Quant: quant_img_RGB2BGR | T1 | UG232 tr.133 | quant_img_RGB2BGR: Indicates whether to perform RGB2BGR operation when loading quantized |
| 4.3 | Quant: optimization_level | T1 | UG232 tr.133 | optimization_level: The choice of optimization level |
| 4.3 | Quant: dataset thường 20 đến 200 ảnh | T1 | UG232 tr.133 | typically choose 20 to 200 images |
| 4.3 | Quant: chạy accuracy_analysis với target=None | T1 | UG232 tr.133 | call the rknn.accuracy_analysis(..., target=None) interface |
| 4.3 | Thử một ảnh trước | T1 | UG232 tr.134 | Initially, use a single image for quantization (leave only one line in dataset.txt) |
| 4.3 | Chưa đủ thì tăng khoảng 20 đến 200 ảnh | T1 | UG232 tr.134 | can be increased to about 20 to 200 |
| 4.3 | layer sang channel | T1 | UG232 tr.134 | If the original method was layer quantization, try switching to channel quantization. |
| 4.3 | channel thường chính xác hơn layer nhiều | T1 | UG232 tr.134 | channel quantization often provides significantly higher accuracy than layer quantization |
| 4.3 | normal sang kl_divergence hoặc mmse | T1 | UG232 tr.134 | consider changing the quantization algorithm from normal to kl_divergence or mmse |
| 4.3 | Đổi thuật toán: thời gian lượng tử tăng, runtime không bị ảnh hưởng | T1 | UG232 tr.134 | The runtime performance is not adversely affected. |
| 4.3 | Hybrid: xét cột single và vị trí lớp | T1 | UG232 tr.134 | consider both the accuracy loss of the single column of simulator_error and the position of the layer in the model. |
| 4.3 | Lớp cuối có thể chuyển sang post-processing | T1 | UG232 tr.134 | move the execution of that layer's operation to post-processing |
| 4.3 | QAT khi hybrid chưa đủ chính xác hoặc đủ nhưng hiệu năng chưa đạt | T1 | UG232 tr.135 | if the accuracy is sufficient but the performance does not meet the requirements due to hybrid quantization |
| 4.3 | QAT chỉ khi cả PTQ và hybrid không đạt | T1 | UG232 tr.126 | it is recommended to consider using QAT when both of the following conditions are met: |
| 4.3 | Connect Test: init_runtime với target | T1 | UG232 tr.135 | set the target parameter of rknn.init_runtime() |
| 4.3 | Connect Test: xem single_sim của runtime_error | T1 | UG232 tr.135 | Check the single_sim column of runtime_error in the analysis results. |
| 4.3 | Connect Test: hiển thị vàng hoặc đỏ | T1 | UG232 tr.135 | (displayed in yellow or red) |
| 4.3 | Connect Test: gửi phản hồi cho Rockchip NPU team | T1 | UG232 tr.135 | can be fed back to the Rockchip NPU team for repair. |
| 4.3 | Runtime Test: input 4 chiều dùng NHWC | T1 | UG232 tr.135 | for 4-dimensional input shapes, fmt=NHWC |
| 4.3 | Runtime Test: pre-process, post-process giống phía simulator | T1 | UG232 tr.135 | (they need to be completely consistent with the processes on the simulator side) |
| 4.3 | Runtime Test: RKNN_LOG_LEVEL=5 để dump từng lớp | T1 | UG232 tr.136 | users can set RKNN_LOG_LEVEL=5 before running the application. |
| 4.3 | Runtime Test: thư mục dump trên Linux | T1 | UG232 tr.136 | /userdata/dumps (Linux system) |
| 4.3 | Ngưỡng cosine để coi là đạt | T1 | (không có) | (unknown) |
| 4.3 | Quy trình áp dụng cho YOLOv8 hay PPE | T1 | (không có) | (unknown) |
| 4.3 | Nhãn hình gốc | T1 | UG232 tr.131 | Figure 7-1 The step of accuracy analysis |
| 4.4 | Hàng 1, phía A: mặc định w8a8 | T1 | API232 tr.7 | The default value is "w8a8". |
| 4.4 | Hàng 1, phía A: code khớp | T1 | RKNNPY rknn/api/rknn.py:56 | quantized_dtype='w8a8', |
| 4.4 | Hàng 1, phía B: UG232 tr.22 | T1 | UG232 tr.22 | and the default is 'asymmetric_quantized-8'. |
| 4.4 | Hàng 1, phía B: UG232 tr.122 | T1 | UG232 tr.122 | only linear asymmetric INT8 quantization is supported, and the default value is 'asymmetric_quantized-8'. |
| 4.4 | Hàng 1: T3 config() nhận tên cũ, quant_tab giống w8a8 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | chấp nhận tên cũ |
| 4.4 | Hàng 2, phía A: bốn thuật toán | T1 | API232 tr.8 | Currently support: normal, mmse, kl_divergence and gdq. The default value is normal. |
| 4.4 | Hàng 2, phía A: code khớp | T1 | RKNNPY rknn/api/rknn.py:85 | currently support: normal, mmse (Min Mean Square Error), kl_divergence, gdq. default is normal. |
| 4.4 | Hàng 2, phía B: UG232 tr.122 | T1 | UG232 tr.122 | The optional values are 'normal', 'kl_divergence', and 'mmse' |
| 4.4 | Hàng 2, phía B: UG232 tr.22 | T1 | UG232 tr.22 | You can choose normal, mmse or kl_divergence. |
| 4.4 | Hàng 2, phía B: UG232 tr.159 | T1 | UG232 tr.159 | namely normal , mmse , and kl_divergence |
| 4.4 | Hàng 3, phía A: True | T1 | API232 tr.14 | do_quantization: Whether to quantize the model. The default value is True. |
| 4.4 | Hàng 3, phía A: code khớp | T1 | RKNNPY rknn/api/rknn.py:188 | def build(self, do_quantization=True, dataset=None |
| 4.4 | Hàng 3, phía B: UG232 tr.122 | T1 | UG232 tr.122 | Specify whether to enable quantization, with the default value being 'False'. |
| 4.4 | Hàng 4, phía A: normal, 20-100 | T1 | API232 tr.8 | The recommended quantization data is generally about 20-100 pieces. with more data |
| 4.4 | Hàng 4, phía A: mmse, 20-50 | T1 | API232 tr.8 | The recommended quantization data is generally about 20-50 pieces. |
| 4.4 | Hàng 4, phía A: gdq hơn 200 | T1 | API232 tr.8 | more than 200 pieces |
| 4.4 | Hàng 4: UG232 tr.28 normal 20-100 | T1 | UG232 tr.28 | The recommended amount of quantified data is generally about 20-100 data sample. |
| 4.4 | Hàng 4: UG232 tr.28 mmse 20-50 | T1 | UG232 tr.28 | The recommended amount of quantified data is generally about 20-50 data sample. |
| 4.4 | Hàng 4: UG232 tr.28 chỉ ba thuật toán | T1 | UG232 tr.28 | Three quantization algorithms: |
| 4.4 | Hàng 4, phía B: UG232 tr.122 | T1 | UG232 tr.122 | It is generally recommended to use a quantization calibration set of 20-200 images |
| 4.4 | Hàng 4, phía B: UG232 tr.133 | T1 | UG232 tr.133 | typically choose 20 to 200 images |
| 4.4 | Hàng 4, phía B: UG232 tr.134 | T1 | UG232 tr.134 | can be increased to about 20 to 200 |
| 4.4 | Hàng 4, phía B: UG232 tr.159 | T1 | UG232 tr.159 | For normal or kl_divergence, 20-200 sets of data are recommended. For mmse, 20-50 sets of data are recommended. |
| 4.4 | Hàng 5, phía A: UG232 tr.124 | T1 | UG232 tr.124 | Currently, the available quantization data type is "float16". |
| 4.4 | Hàng 5, phía B: ví dụ step1.py | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/step1.py:47 | Currently supported data types are: 'int8', 'int16', 'float16'. |
| 4.4 | Hàng 6, phía A: API232 tr.14 | T1 | API232 tr.14 | cosine distance and euclidean distance below the specified thresholds |
| 4.4 | Hàng 6, phía B: UG232 tr.125 | T1 | UG232 tr.125 | operators lesser than the cosine distance threshold or the greater than euclidean distance threshold are converted to fp16. |
| 4.4 | Hàng 7, phía A: API232 tr.22 | T1 | API232 tr.22 | cosine distance (entire_error and single_error) |
| 4.4 | Hàng 7, phía B: UG232 tr.30 | T1 | UG232 tr.30 | It is divided into 4 columns of accuracy |
| 4.4 | Hàng 7, phía B: tên nhóm trong ví dụ chính thức | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/accuracy_analysis/README.md:19 | # simulator_error: calculate the output error of each layer of the simulator |
| 4.4 | Hàng 7: Hình 3-2 hiển thị các nhóm cột (khớp UG232 tr.31) | T1 | UG232 tr.30 | Figure 3-2 Accuracy analysis results |
| 4.4 | Hàng 8, phía A: API232 tr.22 | T1 | API232 tr.22 | include fp32 & quant for calculate quantitative |
| 4.4 | Hàng 8, phía B: UG232 tr.131 | T1 | UG232 tr.131 | RKNPU currently does not support FP32 calculations |
| 4.4 | Hàng 9, phía A: Note ở UG232 tr.22 | T1 | UG232 tr.22 | the model's inference sequence is to perform RGB2BGR conversion first then perform mean_valuesand std_values operations later. |
| 4.4 | Hàng 9, phía A: cùng trang, câu nói không có tác dụng ở inference | T1 | UG232 tr.22 | will not take effect during the model inference stage |
| 4.4 | Hàng 9, phía B: UG232 tr.158 | T1 | UG232 tr.158 | The quant_img_RGB2BGR parameter only affects reading images in the quantization step. |
| 4.4 | Hàng 9, phía B: API232 tr.7 | T1 | API232 tr.7 | will not be recorded in the final RKNN model. |
| 4.4 | Hàng 10, phía A: UG232 tr.122 | T1 | UG232 tr.122 | It is generally recommended to use a quantization calibration set of 20-200 images |
| 4.4 | Hàng 10, phía B: onnx/yolov5 dataset.txt | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/dataset.txt:1 | bus.jpg |
| 4.4 | Hàng 10, phía B: hybrid_quant dataset.txt | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/hybrid_quant/dataset.txt:1 | dog_bike_car_300x300.jpg |
| 4.4 | Hàng 10, phía B: accuracy_analysis dataset.txt | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/accuracy_analysis/dataset.txt:1 | dog_224x224.jpg |
| 4.4 | Hàng 10, phía B: quantize_algorithm_mmse dataset.txt | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/quantize_algorithm_mmse/dataset.txt:1 | dog_224x224.jpg |
| 4.4 | Hàng 10: mỗi dataset.txt trên có đúng 1 dòng | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/dataset.txt | (số học) |
| 4.4 | Hàng 10: lý do ví dụ dùng 1 ảnh | T1 | (không có) | (unknown) |
| 4.4 | Cảnh báo phạm vi: 24 dòng target_platform=, 18 rk3566, 5 rk3588, 1 rk3562 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/npu_device_test/test.py:30 | target_platform='rk3588' |
| 4.4 | Cảnh báo phạm vi: số đếm 24, 18, 5, 1 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/codegen/test.py:29 | (số học) |
| 4.4 | README accuracy_analysis ghi mặc định rk3566 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/functions/accuracy_analysis/README.md:13 | The default target platform in script is 'rk3566' |
| 4.4 | UG232 ngày phát hành 2025-04-03 | T1 | UG232 tr.1 | Release Date: 2025-04-03 |
| 4.4 | API232 ngày phát hành 2025-4-1 | T1 | API232 tr.1 | Release Date: 2025-4-1 |
