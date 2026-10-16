# Phần 3: Lý thuyết lượng tử

## Câu hỏi mở đầu
Một số thực được biến thành số nguyên INT8 như thế nào, sai số đến từ đâu, và các kỹ thuật PTQ, QAT sửa sai số đó ra sao?

## Hình 3.1 (h3-1-affine) [T2 chung]
Lượng tử hóa affine ánh xạ trục số thực sang lưới số nguyên bằng scale s và zero-point z, rồi cắt phần nằm ngoài [q_min, q_max]. Theo NAGEL Eq. 4 và 6, x_int = clamp(round(x/s) + z; 0, 2^b - 1) và x^ = s (x_int - z); z là số nguyên nên số 0 thực được lượng tử hóa không sai số. Symmetric là trường hợp z = 0 (lưới có dấu hoặc không dấu), asymmetric có z tùy ý và cắt range chặt hơn. GHOLAMI viết dấu zero-point ngược lại (-Z khi lượng tử hóa); bộ hình dùng NAGEL làm chuẩn.
Đọc thêm: 03_ mục 3.1.
Khái niệm: Hình 4.1

## Hình 3.2 (h3-2-do-min) [T2 chung]
Granularity là số phần tử của tensor dùng chung một bộ (s, z): per-tensor một bộ cho cả tensor, per-channel một bộ cho mỗi output channel của weight, group một bộ cho mỗi nhóm channel. "Channel-wise" có hai nghĩa: NAGEL và GHOLAMI dùng cho mỗi output filter, còn Y7Q gọi mức đó là filter-wise và dành channel-wise cho mức mịn hơn. Per-channel của weight thực hiện được vì scale tách khỏi tổng; per-channel của activation phải rescale accumulator. Liên hệ RK3588: trong RKNN-Toolkit2, per-channel chỉ áp dụng cho weight, activation vẫn per-layer (UG232 tr.120, T1), xem Hình 4.1.
Đọc thêm: 03_ mục 3.2.
Khái niệm: Hình 4.1

## Hình 3.3 (h3-3-clipping-rounding) [T2 chung]
Range [q_min, q_max] quyết định đánh đổi giữa sai số clipping và sai số làm tròn: range rộng thì ít clipping nhưng bước s lớn nên làm tròn kém, vì vậy min-max nhạy với outlier còn MSE chọn range hẹp hơn. Các cách chọn range trong nguồn gồm min-max, MSE, cross-entropy (cho logits lớp cuối), BN-based, percentile, KL divergence và UH của Q-YOLO. Hai biểu đồ (a) và (b) là dữ liệu minh họa, không phải số đo; hình dạng theo NAGEL tr.4 và tr.9. Số đo thật là Table 1 và 2 của NAGEL trên phân loại ImageNet, không phải detection; RKNN-Toolkit2 có Normal, KL-Divergence, MMSE (UG232 tr.120, 121, T1), xem Hình 4.1.
Đọc thêm: 03_ mục 3.3.
Khái niệm: Hình 4.1

## Hình 3.4 (h3-4-phep-tinh-int8) [T2 chung]
Suy luận số nguyên nhân INT8 với INT8, cộng dồn vào accumulator INT32, rồi requantization về INT8 để lớp sau đọc từ bộ nhớ. Quanh phép nhân này có ba việc: gộp BN vào lớp tuyến tính liền trước, đặt requantization sau non-linearity, và làm hai đầu vào của phép cộng hoặc concat cùng một lưới lượng tử. Sigmoid và Swish cần hỗ trợ riêng, nếu không phải thêm bước quantize trước và sau; Q-YOLO gắn sụt độ chính xác của YOLO với SiLU nhưng đó là quan sát của tác giả. Không nguồn nào có số cho Add, Concat của YOLOv8 (unknown). Vị trí accumulator trong core NPU: Hình 2.2; fusion trên RKNN: Hình 6.3.
Đọc thêm: 03_ mục 3.4, 3.7, phần "Chủ đề bổ sung".
Khái niệm: Hình 2.2, Hình 6.3

## Hình 3.5 (h3-5-ptq-qat) [T2 chung]
PTQ lượng tử hóa model đã train bằng bước calibration, không train lại; QAT train lại với khối Quantizer giả lập trong đồ thị và dùng STE để lan truyền gradient qua phép làm tròn. Quy trình PTQ chuẩn của NAGEL: CLE, thêm quantizer (weight symmetric, activation asymmetric), đặt range weight bằng MSE, AdaRound nếu có dữ liệu hoặc bias correction nếu không, rồi đặt range activation. Khi kết quả chưa đạt, lưu đồ debug kiểm tra FP32, từng nhóm tensor weight hoặc activation, từng lớp, và chỉ cuối cùng mới chuyển sang QAT. "Simulated quantization" có hai nghĩa (NAGEL tr.6, GHOLAMI tr.12), và model re-parameterized như RepVGG suy giảm mạnh khi PTQ (QAREP, Hình 8.1). Quy trình phân tích sai số của vendor: Hình 4.3; hybrid trên RKNN: Hình 4.2.
Đọc thêm: 03_ mục 3.3, 3.4, 3.6, 3.8. Số đo: Hình 10.7
Khái niệm: Hình 4.2, Hình 4.3, Hình 8.1
Hình gốc: ../../npu_study/images/03_quantization_theory/nagel_fig8.png (NAGEL tr.16, Figure 8; nhúng để đối chiếu pipeline vẽ lại với hình gốc)
Hình gốc: ../../npu_study/images/03_quantization_theory/nagel_p18_fig9.png (NAGEL tr.18, Figure 9; nhúng để đối chiếu lưu đồ debug vẽ lại, nhất là chiều các mũi tên)

## Hiểu sai thường gặp
- "Zero-point luôn cộng khi lượng tử hóa" -> NAGEL Eq. 4 cộng +z và Eq. 6 trừ z; GHOLAMI Eq. 2 trừ Z và Eq. 3 cộng Z; QYOLO theo dấu NAGEL. Bộ hình dùng NAGEL làm chuẩn [NAGEL tr.4; GHOLAMI tr.5; QYOLO tr.6] (Hình 3.1)
- "Channel-wise luôn là một quantizer cho mỗi output filter" -> NAGEL tr.5 và GHOLAMI tr.7 dùng cho mỗi output filter; Y7Q tr.4 gọi mức đó là filter-wise và dùng channel-wise cho mỗi channel của một filter. Kết quả 4 bit (hàng Uniform của Y7Q Table I; hàng Non-Uniform cho cả hai là 0.672) chỉ weight của Y7Q (filter-wise 0.491, channel-wise 0.621) không dùng để bác bỏ per-channel kiểu NAGEL ở INT8 [Y7Q tr.4, tr.5] (Hình 3.2)
- "Per-channel áp dụng cho activation như cho weight" -> NAGEL tr.8: per-channel cho activation khó vì phải rescale accumulator cho mỗi input channel; UG232 tr.120: trong RKNN-Toolkit2, per-channel chỉ áp dụng cho weight [NAGEL tr.8; UG232 tr.120] (Hình 3.2)
- "Lượng tử hóa 8 bit luôn mất dưới 1%" -> NAGEL tr.16 viết "within 0.7%" và tr.25 viết "within only 1%", nhưng Table 6 (tr.17) cho EfficientDet-D1 (COCO mAP) FP32 40.08 và W8A8 per-tensor 38.29, tức giảm 1.79 điểm (4.5% tương đối; phép tính của bộ hình). Đây là EfficientDet, không phải YOLO [NAGEL tr.16, 17, 25] (Hình 3.2)
- "QYOLO nói weight luôn gây sụt nhiều hơn activation" -> QYOLO tr.10 viết "consistently", nhưng Table 3 ở 6 bit cho activation tệ hơn weight (YOLOv5s -0.8 so với -0.7; YOLOv5m -0.8 so với -0.4); chỉ ở 4 bit weight mới tệ hơn (YOLOv5s -16.3 so với -5.3; YOLOv5m -9.4 so với -6.3) [QYOLO tr.10] (Hình 3.5)
- "MinMax là chuẩn hóa về [-1, 1]" -> QYOLO tr.4 mô tả như vậy, nhưng Eq. 6 của chính bài (tr.6) dùng l_x = min(x) và u_x = max(x); dùng NAGEL Eq. 14, 15 [QYOLO tr.4, 6; NAGEL tr.9] (Hình 3.3)
- "Chỉ activation cần dữ liệu calibration, và cần đúng 500 đến 1000 ảnh" -> NAGEL tr.9 viết weight "usually" không cần dữ liệu, và AdaRound dùng dữ liệu cho weight; 500 đến 1000 ảnh là khuyến nghị cho pipeline của bài, Q-YOLO dùng 1500 ảnh; đều là điều kiện thí nghiệm [NAGEL tr.9, 16; QYOLO tr.8] (Hình 3.3)
- "SiLU là nguyên nhân chứng minh được của sụt độ chính xác YOLO" -> QYOLO tr.7 viết hiện tượng "can be attributed to" SiLU; đó là quan sát của tác giả, không phải chứng minh [QYOLO tr.7] (Hình 3.4)
- "Có kết quả lượng tử hóa YOLOv8 trong bộ nguồn" -> không nguồn nào có YOLOv8; QYOLO chỉ báo cáo YOLOv5 và YOLOv7, nên mọi nhận định về YOLOv8 là unknown [QYOLO tr.9] (Hình 3.4, Hình 3.5)
- "Simulated quantization chỉ có một nghĩa" -> NAGEL tr.6 dùng cho công cụ mô phỏng lúc train và đánh giá (khối Quantizer, dữ liệu float nằm trên lưới); GHOLAMI tr.12 dùng cho kiểu triển khai suy luận lưu tham số bit thấp, tính bằng float và phải dequantize, khác integer-only [NAGEL tr.6; GHOLAMI tr.12] (Hình 3.5)
- "RepVGG mất đúng khoảng 20% khi INT8" -> abstract QAREP viết "more than 20%"; Table 5 cho mức giảm từ 20.2 điểm (A0: 72.4 xuống 52.2) đến 77.05 điểm (B1g4: 77.6 xuống 0.55), và YOLOv6s-RepVGG giảm 7.4 mAP. Thiết lập là 8-bit symmetric bằng PyTorch-Quantization, không phải RKNN [QAREP tr.1, 6, 7] (Hình 3.5)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao phép nhân INT8 x INT8 phải cộng dồn vào accumulator 32 bit, và vì sao sau đó cần bước requantization?
Đáp án: Nhiều tích được cộng dồn nên accumulator cần bit-width cao hơn (thường 32 bit), nếu không có nguy cơ tràn số; kết quả 32 bit phải ghi ra bộ nhớ cho lớp sau, nên được lượng tử hóa ngược về INT8 bằng requantization. Scale của weight và activation áp cho cả tensor nên tách được ra khỏi tổng và phép MAC chạy trên số nguyên [NAGEL tr.3] (Hình 3.4)
### Câu 2 (phân biệt)
Phân biệt per-tensor với per-channel, và giải thích vì sao per-channel cho weight thực hiện được còn per-channel cho activation thì khó.
Đáp án: Per-tensor dùng một quantizer cho cả tensor nên mọi accumulator có cùng scale s_w s_x; per-channel dùng một quantizer cho mỗi output channel của weight. Với weight, scale riêng mỗi channel áp được mà không cần rescale; với activation không tách được scale ra khỏi tổng nên phải rescale accumulator cho mỗi input channel. Không phải phần cứng nào cũng hỗ trợ per-channel [NAGEL tr.5, 8] (Hình 3.2)
### Câu 3 (áp dụng)
Với RKNN-Toolkit2 trên RK3588, tài liệu vendor nói granularity của weight và của activation là gì, và điều đó khớp với lý do phần cứng của NAGEL ra sao?
Đáp án: UG232 tr.120 ghi per-channel chỉ áp dụng cho weight, còn activation và giá trị trung gian vẫn per-layer. Điều này phù hợp với lập luận của NAGEL rằng per-channel cho activation phải rescale accumulator; đó là suy ra của bộ hình, UG232 không nêu lý do. Chi tiết RKNN ở Hình 4.1 [UG232 tr.120; NAGEL tr.8] (Hình 3.2)
### Câu 4 (áp dụng)
Model YOLO sau khi lượng tử hóa INT8 có mAP thấp hơn nhiều so với FP32. Theo lưu đồ debug của NAGEL, làm gì trước, và nguồn nào cho biết nguyên nhân là SiLU hay C2f của YOLOv8?
Đáp án: Trước hết đặt bit-width weight và activation về 32 và kiểm tra sai số xấp xỉ 0 (FP32 sanity check), rồi lượng tử hóa riêng tensor weight, riêng tensor activation để xem phần nào gây sụt, sửa bằng range setting, AdaRound, per-channel, CLE, bias correction, sau đó đi từng lớp, và chỉ khi vẫn chưa đạt mới dùng QAT. Không nguồn nào nêu nguyên nhân cho YOLOv8: QYOLO tr.7 chỉ gắn sụt độ chính xác của YOLOv5, YOLOv7 với SiLU như quan sát của tác giả, nên với YOLOv8 là unknown. Số INT8 mAP thật chờ pipeline, xem Hình 10.7 [NAGEL tr.17, 18, 19; QYOLO tr.7, 9] (Hình 3.5, Hình 3.4)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 3.1 | Ba tham số của lượng tử hóa affine | T2 | NAGEL tr.4 | is defined by three quantization parameters: the scale factor s, the zero-point z and the bit-width b |
| 3.1 | Scale là bước của quantizer | T2 | NAGEL tr.4 | specifies the step-size of the quantizer |
| 3.1 | Zero-point là số nguyên, số 0 thực lượng tử hóa không sai số | T2 | NAGEL tr.4 | The zero-point is an integer that ensures that real zero is quantized without error. |
| 3.1 | Padding bằng 0 và ReLU không gây sai số lượng tử hóa | T2 | NAGEL tr.4 | zero padding or ReLU do not induce quantization error |
| 3.1 | Ánh xạ sang lưới số nguyên không dấu {0, ..., 2^b - 1} | T2 | NAGEL tr.4 | we first map it to the unsigned integer grid |
| 3.1 | Eq. 4: x_int = clamp(round(x/s) + z; 0, 2^b - 1) | T2 | NAGEL tr.4 | + z; 0, 2b − 1 , (4) |
| 3.1 | round là round-to-nearest | T2 | NAGEL tr.4 | is the round-to-nearest operator |
| 3.1 | Eq. 6: x^ = s (x_int - z) | T2 | NAGEL tr.4 | s (xint − z) (6) |
| 3.1 | q_min = -s z, q_max = s (2^b - 1 - z) | T2 | NAGEL tr.4 | qmin = −sz and qmax = s(2b − 1 − z) |
| 3.1 | Giá trị ngoài range bị cắt, gây clipping error | T2 | NAGEL tr.4 | will be clipped to its limits, incurring a clipping error |
| 3.1 | Sai số làm tròn nằm trong [-s/2, s/2] | T2 | NAGEL tr.4 | the rounding error lies in the range |
| 3.1 | Tăng s làm tăng sai số làm tròn | T2 | NAGEL tr.4 | the scale factor leads to increased rounding error |
| 3.1 | Symmetric hạn chế zero-point bằng 0 | T2 | NAGEL tr.4 | The symmetric quantizer restricts the zero-point to 0. |
| 3.1 | Lưới symmetric unsigned (Eq. 8b) và signed (Eq. 8c) | T2 | NAGEL tr.5 | for unsigned integers |
| 3.1 | Symmetric signed: lưới có dấu | T2 | NAGEL tr.5 | for signed integers |
| 3.1 | Unsigned hợp với phân bố một phía như ReLU | T2 | NAGEL tr.5 | Unsigned symmetric quantization is well suited for one-tailed distributions, such as ReLU activations |
| 3.1 | Signed hợp với phân bố gần đối xứng quanh 0 | T2 | NAGEL tr.5 | signed symmetric quantization can be chosen for distributions that are roughly symmetric about zero |
| 3.1 | Tên hình: ba lưới lượng tử đều với bit-width 8 | T2 | NAGEL tr.5 | A visual explanation of the different uniform quantization grids for a bit-width of 8 |
| 3.1 | Asymmetric biểu đạt hơn nhờ tham số offset nhưng có thể tốn tính toán | T2 | NAGEL tr.8 | asymmetric quantization is more expressive because there is an extra offset parameter, but on the other hand there is a possible computational overhead |
| 3.1 | Số hạng phụ thuộc dữ liệu phải tính cho mỗi batch | T2 | NAGEL tr.8 | for each batch of data we need to compute an additional term during inference |
| 3.1 | Asymmetric có offset, có thể tốn tính toán; số hạng phụ thuộc dữ liệu | T2 | NAGEL tr.8 | The second term, however, depends on the input data x. |
| 3.1 | Weight symmetric, activation asymmetric thường dùng | T2 | NAGEL tr.8 | it is a common approach to use asymmetric activation quantization and symmetric weight quantization that avoids the additional data-dependent term |
| 3.1 | Số hạng phụ thuộc dữ liệu tốn độ trễ và điện năng | T2 | NAGEL tr.8 | This can lead to significant overhead in both latency and power |
| 3.1 | Khuyến nghị trong pipeline PTQ chuẩn | T2 | NAGEL tr.16 | we recommend using symmetric quantizers for the weights and asymmetric quantizers for the activations |
| 3.1 | GHOLAMI Eq. 2: Q(r) = Int(r/S) - Z | T2 | GHOLAMI tr.5 | Q(r) = Int r/S − Z, (2) |
| 3.1 | GHOLAMI Eq. 3: r~ = S (Q(r) + Z) | T2 | GHOLAMI tr.5 | S(Q(r) + Z). (3) |
| 3.1 | S là scale thực, Z là zero point số nguyên | T2 | GHOLAMI tr.5 | is a real valued scaling |
| 3.1 | Restricted range [-127, 127], full range [-128, 127] cho 8 bit | T2 | GHOLAMI tr.5 | Symmetric quantization with restricted range maps real values to [-127, 127], and full range maps to [-128, 127] for 8-bit quantization. |
| 3.1 | Asymmetric cắt range chặt hơn symmetric | T2 | GHOLAMI tr.5 | often results in a tighter clipping range |
| 3.1 | QYOLO Eq. 3 cộng zp_x khi lượng tử hóa | T2 | QYOLO tr.6 | + zpx , 0, 2b − 1), (3) |
| 3.1 | QYOLO Eq. 5 trừ zp_x khi giải lượng tử hóa | T2 | QYOLO tr.6 | − zpx ) × sx . (5) |
| 3.1 | QYOLO Table 2: real-valued 37.4 AP (YOLOv5s) | T2 | QYOLO tr.9 | Real-valued - 37.4 57.1 40.1 21.6 42.3 48.9 |
| 3.1 | QYOLO Table 2, 6-6: asymmetric 35.9 AP | T2 | QYOLO tr.9 | Asymmetric 35.9 55.7 38.3 20.4 41.0 47.6 |
| 3.1 | QYOLO Table 2, 6-6: symmetric 34.4 AP | T2 | QYOLO tr.9 | Symmetric 34.4 53.9 37.0 19.3 39.8 45.0 |
| 3.1 | QYOLO Table 2, 4-4: asymmetric 14.0 AP | T2 | QYOLO tr.9 | Asymmetric 14.0 26.2 13.5 7.9 17.6 19.0 |
| 3.1 | QYOLO Table 2, 4-4: symmetric 2.7 AP | T2 | QYOLO tr.9 | Symmetric 2.7 5.9 2.2 1.3 4.2 4.6 |
| 3.1 | Chênh lệch asymmetric so với symmetric lớn hơn khi bit giảm | T2 | QYOLO tr.10 | this decline becomes more pronounced as the quantization bit number decreases |
| 3.1 | Điều kiện Table 2: activation, YOLOv5s | T2 | QYOLO tr.9 | A comparison of Symmetrical Analysis of Activation Value Quantization. |
| 3.1 | Điều kiện: COCO val2017 | T2 | QYOLO tr.8 | the performance evaluation took place on the COCO val2017 dataset |
| 3.1 | Liên hệ RKNN: zero point của INT8 là 0 ở linear symmetric | T1 | UG232 tr.120 | the zero point of INT8 is 0 |
| 3.1 | Liên hệ RKNN: linear asymmetric tính zero point theo công thức | T1 | UG232 tr.120 | In linear asymmetric quantization, the zero point is calculated based on equation (6-5) |
| 3.1 | Hình vẽ: vị trí điểm trên trục, bước và kích thước vùng là minh họa khái niệm | T2 | NAGEL tr.5 | (đọc từ hình) |
| 3.2 | Per-tensor: một quantizer cho cả tensor | T2 | NAGEL tr.5 | This is called per-tensor quantization. |
| 3.2 | Mọi accumulator dùng cùng scale s_w s_x | T2 | NAGEL tr.5 | all accumulators in equation (3) use the same scale factor |
| 3.2 | Per-channel: một quantizer cho mỗi output channel của weight | T2 | NAGEL tr.5 | we can specify a different quantizer per output channel. This is known as per-channel quantization |
| 3.2 | Quantizer riêng cho từng nhóm | T2 | NAGEL tr.5 | apply separate quantizers per group of weights or activations |
| 3.2 | Nhóm mịn hơn thêm overhead vì accumulator có scale khác nhau | T2 | NAGEL tr.5 | The overhead is associated with accumulators handling sums of values with varying scale factors. |
| 3.2 | Đa số bộ tăng tốc chưa hỗ trợ logic nhóm | T2 | NAGEL tr.5 | Most existing fixed-point accelerators do not currently support such logic |
| 3.2 | Per-channel weight cải thiện khi phân bố weight khác nhau giữa các channel | T2 | NAGEL tr.8 | per-channel quantization of the weights can improve accuracy, especially when the distribution of weights varies significantly from channel to channel |
| 3.2 | Per-channel weight áp được mà không rescale | T2 | NAGEL tr.8 | by applying a separate per-channel weight scale factor without requiring rescaling |
| 3.2 | Per-channel activation phải rescale accumulator | T2 | NAGEL tr.8 | Per-channel quantization of activations is much harder to implement because we cannot factor the scale factor out of the summation |
| 3.2 | Phải rescale accumulator cho mỗi input channel | T2 | NAGEL tr.8 | would, therefore, require rescaling the accumulator for each input channel |
| 3.2 | Không phải phần cứng thương mại nào cũng hỗ trợ per-channel | T2 | NAGEL tr.8 | not all commercial hardware supports it |
| 3.2 | GHOLAMI: layerwise dùng chung range cho mọi filter của lớp | T2 | GHOLAMI tr.6 | In layerwise quantization, the same clipping range is applied to all the filters that belong to the same layer. |
| 3.2 | GHOLAMI: range hẹp mất độ phân giải khi chung quantizer | T2 | GHOLAMI tr.6 | This can result in bad quantization resolution for the channels that have narrow distributions |
| 3.2 | GHOLAMI: channelwise là một giá trị cho mỗi filter | T2 | GHOLAMI tr.7 | A popular choice of the clipping range is to use a fixed value for each convolutional filter |
| 3.2 | GHOLAMI: mỗi channel có scale riêng | T2 | GHOLAMI tr.7 | each channel is assigned a dedicated scaling factor |
| 3.2 | GHOLAMI: channelwise là chuẩn cho kernel convolution | T2 | GHOLAMI tr.7 | Channelwise quantization is currently the standard method |
| 3.2 | GHOLAMI: groupwise gộp nhiều channel trong một lớp | T2 | GHOLAMI tr.7 | Groupwise Quantization: One could group mul |
| 3.2 | GHOLAMI: sub-channelwise có overhead lớn, chưa là chuẩn | T2 | GHOLAMI tr.7 | significant overhead and is not |
| 3.2 | Y7Q: các granularity của Figure 3 | T2 | Y7Q tr.3 | layer-wise, filter-wise, C-shape-wise, F-shape-wise, and channel-wise granularities |
| 3.2 | Y7Q: filter-wise lượng tử hóa từng filter | T2 | Y7Q tr.4 | The widely used filter-wise quantization considers all the weights of a convolutional filter as a group and quantizes each filter individually |
| 3.2 | Y7Q: channel-wise lượng tử hóa từng channel của một filter | T2 | Y7Q tr.4 | This approach quantizes each channel of a convolutional filter independently |
| 3.2 | Y7Q: nhiều lớp YOLOv7 kernel 1x1 không lượng tử hóa được kiểu channel-wise | T2 | Y7Q tr.4 | many convolutional layers in YOLOv7 cannot get quantized using this granularity since they have a kernel size of (1, 1) |
| 3.2 | Y7Q: channel-wise làm giảm tỉ lệ tiết kiệm bộ nhớ | T2 | Y7Q tr.4 | channel-wise quantization for YOLOv7 hurts the memory-saving ratio |
| 3.2 | Y7Q: thí nghiệm 4 bit với bốn granularity | T2 | Y7Q tr.4 | We perform 4-bit uniform and non-uniform quantization with four different quantization granularities |
| 3.2 | Y7Q: baseline FP16 mAP 0.691 | T2 | Y7Q tr.4 | Yolov7 16 0.724 0.635 0.691 |
| 3.2 | Y7Q Table I: filter-wise (uniform) 0.491, tiết kiệm ~3.97 | T2 | Y7Q tr.4 | Uniform Filter-wise 4 0.605 0.464 0.491 ~ 3.97 |
| 3.2 | Y7Q Table I: channel-wise (uniform) 0.621, tiết kiệm ~1.68 | T2 | Y7Q tr.4 | Uniform Channel-wise 4 0.686 0.573 0.621 ~ 1.68 |
| 3.2 | Y7Q Table I: C-shape-wise (uniform) 0.657, ~3.93 | T2 | Y7Q tr.4 | Uniform C-shape-wise 4 0.708 0.604 0.657 ~ 3.93 |
| 3.2 | Y7Q Table I: F-shape-wise (uniform) 0.635, ~3.93 | T2 | Y7Q tr.4 | Uniform F-shape-wise 4 0.704 0.579 0.635 ~ 3.93 |
| 3.2 | Y7Q chỉ lượng tử hóa weight | T2 | Y7Q tr.5 | variety of granularities to the pre-trained weights of YOLOv7 |
| 3.2 | NAGEL Table 1: tiêu đề FP32 ResNet18 69.68, MobileNetV2 71.72 | T2 | NAGEL tr.9 | Model (FP32 accuracy) ResNet18 (69.68) MobileNetV2 (71.72) |
| 3.2 | NAGEL Table 1: Min-Max (per-tensor) 69.57, 0.12, 71.16, 0.59 | T2 | NAGEL tr.9 | Min-Max 69.57 63.90 0.12 71.16 64.48 0.59 |
| 3.2 | NAGEL Table 1: Min-Max per-channel 69.60, 44.49, 71.21, 18.40 | T2 | NAGEL tr.9 | Min-Max (Per-channel) 69.60 69.08 44.49 71.21 68.52 18.40 |
| 3.2 | Hai hàng đầu Table 1 không ghi "Per-channel"; bộ hình gọi là per-tensor (suy ra của bộ hình) | T2 | NAGEL tr.9 | MSE (Per-channel) 69.66 69.24 54.67 71.46 68.89 27.17 |
| 3.2 | Điều kiện Table 1: weight symmetric, activation FP32, ImageNet, 5 lần | T2 | NAGEL tr.9 | quantizers while keeping the activations in FP32. Average ImageNet validation accuracy (%) over 5 runs. |
| 3.2 | NAGEL Table 6: EfficientDet-D1 FP32 40.08, W8A8 38.29 và 38.67, W4A8 0.31 và 35.08 | T2 | NAGEL tr.17 | EfficientDet-D1 40.08 38.29 0.31 38.67 35.08 |
| 3.2 | Điều kiện Table 6: EfficientDet-D1 trên COCO 2017 (mAP) | T2 | NAGEL tr.17 | EfficientDet-D1 on COCO 2017 (mean average precision) |
| 3.2 | Liên hệ RKNN: per-channel chỉ áp dụng cho weight | T1 | UG232 tr.120 | Per-Channel quantization is only applied to the weights, while the activation values and intermediate values are still quantized using Per-Layer quantization. |
| 3.2 | Liên hệ RKNN: per-layer dùng chung tham số cho mọi channel | T1 | UG232 tr.120 | Per-Layer quantization quantizes all channels of a network layer as a whole |
| 3.2 | Range F1 đến F4 trong hình là dữ liệu minh họa, không phải số đo | T2 | GHOLAMI tr.6 | (đọc từ hình) |
| 3.3 | Mở rộng range bằng cách tăng s giảm sai số clipping | T2 | NAGEL tr.4 | we can expand the quantization range by increasing the scale factor |
| 3.3 | Tăng s làm tăng sai số làm tròn | T2 | NAGEL tr.4 | the scale factor leads to increased rounding error |
| 3.3 | Cần cân bằng clipping và rounding | T2 | NAGEL tr.4 | to achieve the right trade-off between clipping and rounding errors |
| 3.3 | Lưới số nguyên có kích thước phụ thuộc bit-width | T2 | NAGEL tr.4 | to map a floating point value to the integer grid, whose size depends on the bit-width |
| 3.3 | Đánh đổi chính của range setting là clipping và rounding | T2 | NAGEL tr.9 | The key trade-off in range setting is between clipping and rounding error |
| 3.3 | Min-max: Eq. 14 q_min = min V | T2 | NAGEL tr.9 | qmin = min V, (14) |
| 3.3 | Min-max: Eq. 15 q_max = max V | T2 | NAGEL tr.9 | qmax = max V, (15) |
| 3.3 | Min-max không clipping error, nhạy outlier | T2 | NAGEL tr.9 | This leads to no clipping error. However, this approach is sensitive to outliers as strong outliers may cause excessive rounding errors. |
| 3.3 | MSE giảm ảnh hưởng của outlier lớn | T2 | NAGEL tr.9 | One way to alleviate the issue of large outliers is to use MSE-based range setting. |
| 3.3 | MSE: tìm q_min, q_max cực tiểu MSE giữa tensor gốc và đã lượng tử hóa | T2 | NAGEL tr.9 | we find qmin and qmax that minimize the MSE between the original and the quantized tensor |
| 3.3 | MSE dùng chuẩn Frobenius (Eq. 16) | T2 | NAGEL tr.9 | is the Frobenius norm |
| 3.3 | MSE giải bằng grid search, golden section hoặc giải tích | T2 | NAGEL tr.9 | commonly solved using grid search, golden section method or analytical approximations with closed-form solution |
| 3.3 | Weight không cần calibration, activation cần vài batch | T2 | NAGEL tr.9 | Weights can usually be quantized without any need for calibration data. However, determining parameters for activation quantization often requires a few batches of calibration data. |
| 3.3 | Cross-entropy cho lớp cuối | T2 | NAGEL tr.10 | it is beneficial to minimize the following cross-entropy loss function |
| 3.3 | H là cross-entropy, psi là softmax, v là logits | T2 | NAGEL tr.10 | ψ is the softmax function, and v is the logits vector |
| 3.3 | Cần giữ thứ tự giá trị lớn nhất của logits | T2 | NAGEL tr.10 | it is important to preserve the order of the largest value after quantization |
| 3.3 | MSE coi mọi giá trị như nhau | T2 | NAGEL tr.10 | it weighs all the values in a tensor equally regardless of their order |
| 3.3 | BN-based: Eq. 18 q_min = min(β - αγ) | T2 | NAGEL tr.10 | qmin = min (β − αγ) (18) |
| 3.3 | BN-based: Eq. 19 q_max = max(β + αγ) | T2 | NAGEL tr.10 | qmax = max (β + αγ) (19) |
| 3.3 | BN-based dùng alpha = 6 | T2 | NAGEL tr.10 | uses α = 6 so that only large outliers are clipped |
| 3.3 | BN-based cho pipeline data-free | T2 | NAGEL tr.16 | we can use the BN based range setting to have a fully data-free pipeline |
| 3.3 | Percentile thay cho min/max | T2 | GHOLAMI tr.6 | One approach to address this is to use percentile instead of min/max of the signal |
| 3.3 | Percentile dùng giá trị lớn/nhỏ thứ i | T2 | GHOLAMI tr.6 | the i-th largest/smallest values are used as |
| 3.3 | Min-max dễ bị outlier làm tăng range, giảm độ phân giải | T2 | GHOLAMI tr.6 | this approach is susceptible to outlier data in the activations |
| 3.3 | KL divergence giữa giá trị thực và đã lượng tử hóa | T2 | GHOLAMI tr.6 | to minimize KL divergence (i.e., information loss) between the real values and the quantized values |
| 3.3 | NAGEL không nêu KL divergence và percentile | T2 | (không có) | (unknown) |
| 3.3 | QYOLO: đánh đổi giữa clipping và rounding | T2 | QYOLO tr.6 | The crucial trade-off in range setting lies in the balance between two types of errors: clipping error and rounding error. |
| 3.3 | QYOLO Eq. 6: l_x = min(x), u_x = max(x) | T2 | QYOLO tr.6 | lx = min(x), ux = max(x). (6) |
| 3.3 | QYOLO Eq. 7: argmin MSE(x, Q) | T2 | QYOLO tr.6 | arg min MSE(x, Qlx ,ux ), (7) |
| 3.3 | QYOLO tr.4 mô tả MinMax là chuẩn hóa về [-1, 1] | T2 | QYOLO tr.4 | MinMax normalizes the weights and bias values in the model to a predefined range, such as [-1, 1] |
| 3.3 | UH: asymmetric, activation | T2 | QYOLO tr.7 | we introduce an asymmetric quantization approach called Unilateral Histogram-based (UH) activation quantization |
| 3.3 | UH: giữ giá trị nhỏ nhất cố định -0.2785 | T2 | QYOLO tr.7 | keeping the minimum truncation value fixed at -0.2785 |
| 3.3 | UH: u_x = argmin MSE, l_x = -0.2785 | T2 | QYOLO tr.7 | ux = arg min MSE(x, Qlx ,ux ), lx = −0.2785. |
| 3.3 | UH: histogram 2048 bin | T2 | QYOLO tr.7 | Input: FP32 Histogram H with 2048 bins |
| 3.3 | Q-YOLO áp dụng cho YOLOv5 và YOLOv7 | T2 | QYOLO tr.9 | We apply our proposed Q-YOLO to quantize YOLOv5s [33], YOLOv5m [33], YOLOv7 [34] and YOLOv7x [34] |
| 3.3 | Table 1 NAGEL: MSE per-tensor 69.45, 18.82, 71.15, 13.77 | T2 | NAGEL tr.9 | MSE 69.45 64.64 18.82 71.15 65.43 13.77 |
| 3.3 | Table 2 NAGEL: điều kiện activation asymmetric, weight FP32 | T2 | NAGEL tr.10 | range setting of (asymmetric uniform) activation quantizers while keeping the weights in FP32 |
| 3.3 | Table 2 NAGEL: Min-Max 69.60, 18.82, 70.96, 0.53 | T2 | NAGEL tr.10 | Min-Max 69.60 68.19 18.82 70.96 64.58 0.53 |
| 3.3 | Table 2 NAGEL: MSE 69.59, 31.40, 71.35, 13.57 | T2 | NAGEL tr.10 | MSE 69.59 67.84 31.40 71.35 67.55 13.57 |
| 3.3 | Table 2 NAGEL: MSE + Xent 69.60, 59.07, 71.36, 30.94 | T2 | NAGEL tr.10 | MSE + Xent 69.60 68.91 59.07 71.36 68.85 30.94 |
| 3.3 | Table 2 NAGEL: BN (alpha = 6) 69.54, 23.83, 71.32, 0.66 | T2 | NAGEL tr.10 | BN (α = 6) 69.54 68.73 23.83 71.32 65.20 0.66 |
| 3.3 | AdaRound dùng dữ liệu calibration nhỏ | T2 | NAGEL tr.16 | In case we have a small calibration dataset |
| 3.3 | 500 đến 1000 ảnh không nhãn là đủ (khuyến nghị) | T2 | NAGEL tr.16 | Usually, between 500 and 1000 unlabeled images are sufficient as a calibration set. |
| 3.3 | Q-YOLO dùng 1500 ảnh COCO train2017 | T2 | QYOLO tr.8 | We randomly selected 1500 training images from the COCO train2017 dataset |
| 3.3 | Liên hệ RKNN: ba algorithm Normal, KL-Divergence, MMSE | T1 | UG232 tr.120 | three algorithms for solving the quantization range: Normal, KL-Divergence, and MMSE |
| 3.3 | Liên hệ RKNN: Normal không truncation error, nhạy outlier | T1 | UG232 tr.121 | does not introduce truncation error but is sensitive to outliers |
| 3.3 | Liên hệ RKNN: MMSE giảm ảnh hưởng của outlier | T1 | UG232 tr.121 | It mitigates the quantization accuracy loss caused by large outliers to some extent. |
| 3.3 | Liên hệ RKNN: MMSE bằng tìm kiếm lặp vét cạn | T1 | UG232 tr.121 | implemented through a brute-force iterative search |
| 3.3 | Đường cong (a): sai số clipping giảm, làm tròn tăng; tổng của hai đường minh họa và vị trí cực tiểu là phép tính của bộ hình trên dữ liệu minh họa | tính | NAGEL tr.4 | (số học) |
| 3.3 | MSE chọn range tối thiểu hóa sai số tổng gồm cả clipping và rounding (suy ra của bộ hình) | tính | NAGEL tr.9 | (số học) |
| 3.3 | Biểu đồ (b): phân bố, outlier, số mức bằng nhau vì cùng bit-width; vẽ minh họa, không phải số đo | T2 | NAGEL tr.9 | (đọc từ hình) |
| 3.4 | Scale tách khỏi tổng, MAC chạy dạng fixed-point | T2 | NAGEL tr.3 | this scheme allows us to factor the scale factors out of the summation in equation (3) and perform MAC operations in fixed-point format |
| 3.4 | Scale riêng cho weight và activation | T2 | NAGEL tr.3 | Note that we used a separate scale factor for weights, sw , and activations, sx . |
| 3.4 | Accumulator rộng hơn, thường 32 bit, tránh tràn | T2 | NAGEL tr.3 | It is important to maintain a higher bit-width for the accumulators, typical 32-bits wide. Otherwise, we risk incurring loss due to overflow as more products are accumulated during the computation. |
| 3.4 | Bias thường lưu 32 bit | T2 | NAGEL tr.3 | the bias is normally stored in higher bit-width (32-bits) |
| 3.4 | Activation trong accumulator 32 bit phải ghi ra bộ nhớ | T2 | NAGEL tr.3 | The activations stored in the 32-bit accumulators need to be written to memory before they can be used by the next layer. |
| 3.4 | Lượng tử hóa ngược về INT8 bằng requantization | T2 | NAGEL tr.3 | these activations are quantized back to INT8. This requires a requantization step |
| 3.4 | Tên hình 2: nhân ma trận cho suy luận lượng tử hóa | T2 | NAGEL tr.4 | A schematic of matrix-multiply logic in an neural network accelerator for quantized inference. |
| 3.4 | Nhãn hình 2: INT8, INT32, Requantization, Memory | T2 | NAGEL tr.4 | (đọc từ hình) |
| 3.4 | Accumulator nằm trong khối engine của một core NPU | T1 | TRM1 tr.1985 | This unit include convolution pre-process controller, internal buffer, mac array, accumulator. |
| 3.4 | BN gộp vào lớp tuyến tính liền trước hoặc sau | T2 | NAGEL tr.6 | these operations are folded into the previous or next linear layers in a step called batch normalization folding |
| 3.4 | BN folding loại hẳn BN khỏi mạng | T2 | NAGEL tr.6 | This removes the batch normalization operations entirely from the network |
| 3.4 | Tránh thêm chuyển dữ liệu và lượng tử hóa đầu ra lớp | T2 | NAGEL tr.6 | this prevents extra data movement and the quantization of the layer's output |
| 3.4 | Lúc suy luận, BN là phép affine | T2 | NAGEL tr.7 | batch normalization is defined as an affine map of the output x |
| 3.4 | BN gộp được vào lớp tuyến tính | T2 | NAGEL tr.7 | we can rewrite the terms such that the batch normalization operation is fused with the linear layer itself |
| 3.4 | Eq. 11 và Eq. 12 của W~ và b~ | T2 | NAGEL tr.7 | (đọc từ hình) |
| 3.4 | Phần cứng có đơn vị áp non-linearity trước requantization | T2 | NAGEL tr.7 | many hardware solutions come with a hardware unit that applies the non-linearity before the requantization step |
| 3.4 | Chỉ mô phỏng requantization sau non-linearity | T2 | NAGEL tr.7 | we only have to simulate requantization that happens after the non-linearity |
| 3.4 | ReLU: giá trị nhỏ nhất của activation quantizer bằng 0 | T2 | NAGEL tr.7 | just set the minimum representable value of that activation quantization to 0 |
| 3.4 | Sigmoid, Swish cần hỗ trợ riêng | T2 | NAGEL tr.7 | such as sigmoid or Swish (Ramachandran et al., 2017), require more dedicated support |
| 3.4 | Không có hỗ trợ thì thêm quantize trước và sau non-linearity | T2 | NAGEL tr.7 | we need to add a quantization step before and after the non-linearity in the graph |
| 3.4 | Có thể ảnh hưởng lớn tới độ chính xác | T2 | NAGEL tr.7 | This can have a big impact on the accuracy of quantized model. |
| 3.4 | QYOLO gắn sụt độ chính xác với SiLU | T2 | QYOLO tr.7 | This phenomenon can be attributed to the frequent utilization of the Swish (SILU) activation function in the YOLO series. |
| 3.4 | Max pooling không cần lượng tử hóa activation | T2 | NAGEL tr.7 | Activation quantization is not required because the input and output values are on the same quantization grid. |
| 3.4 | Average pooling: trung bình số nguyên chưa chắc là số nguyên | T2 | NAGEL tr.7 | The average of integers is not necessarily an integer. |
| 3.4 | Average pooling: cần bước quantize sau, dùng chung quantizer | T2 | NAGEL tr.7 | a quantization step is required after average-pooling. However, we use the same quantizer for the inputs and outputs |
| 3.4 | Phép cộng: range hai đầu vào phải khớp chính xác | T2 | NAGEL tr.7 | During addition, the quantization ranges of both inputs have to match exactly. |
| 3.4 | Phép cộng: thêm requantization hoặc buộc chung lưới | T2 | NAGEL tr.8 | adding a requantization step can simulate the added noise coarsely |
| 3.4 | Buộc chung lưới có thể cần fine-tune | T2 | NAGEL tr.8 | This would prevent the requantization step but may require fine-tuning. |
| 3.4 | Concat: hai nhánh thường không chung tham số, lưới có thể không chồng nhau | T2 | NAGEL tr.8 | The two branches that are being concatenated generally do not share the same quantization parameters. This means that their quantization grids may not overlap making a requantization step necessary. |
| 3.4 | Concat: có thể tối ưu để chung tham số | T2 | NAGEL tr.8 | it is possible to optimize your network to have shared quantization parameters for the branches being concatenated |
| 3.4 | Lưới của hai đầu vào phép cộng trong hình là minh họa, không phải số đo | T2 | NAGEL tr.7 | (đọc từ hình) |
| 3.4 | QYOLO chỉ báo cáo YOLOv5 và YOLOv7 | T2 | QYOLO tr.9 | quantize YOLOv5s [33], YOLOv5m [33], YOLOv7 [34] and YOLOv7x [34] |
| 3.4 | Số liệu lượng tử hóa của Add, Concat, C2f, SPPF của YOLOv8 | T2 | (không có) | (unknown) |
| 3.4 | Lượng tử hóa YOLOv8 (SiLU, C2f, DFL, detect head) | T2 | (không có) | (unknown) |
| 3.5 | GHOLAMI Figure 4: so sánh QAT và PTQ | T2 | GHOLAMI tr.8 | Comparison between Quantization-Aware Training (QAT, Left) and Post-Training Quantization (PTQ, Right). |
| 3.5 | QAT: model đã train được lượng tử hóa rồi finetune bằng dữ liệu train | T2 | GHOLAMI tr.8 | In QAT, a pre-trained model is quantized and then finetuned using training data |
| 3.5 | PTQ: calibrate bằng calibration data rồi lượng tử hóa | T2 | GHOLAMI tr.8 | In PTQ, a pre-trained model is calibrated using calibration data |
| 3.5 | Nhãn hộp Figure 4: Retraining / Finetuning | T2 | GHOLAMI tr.8 | Retraining / Finetuning |
| 3.5 | PTQ không cần pipeline train gốc | T2 | NAGEL tr.8 | without the need for the original training pipeline |
| 3.5 | Activation thường cần vài batch dữ liệu calibration | T2 | NAGEL tr.9 | determining parameters for activation quantization often requires a few batches of calibration data |
| 3.5 | 500 đến 1000 ảnh không nhãn là đủ (khuyến nghị) | T2 | NAGEL tr.16 | between 500 and 1000 unlabeled images are sufficient as a calibration set |
| 3.5 | PTQ hạn chế khi lượng tử hóa activation 4 bit trở xuống | T2 | NAGEL tr.19 | especially when aiming for low-bit quantization of activations, such as 4-bit and below |
| 3.5 | QAT mô hình hóa nhiễu lượng tử khi train | T2 | NAGEL tr.19 | QAT models the quantization noise source (see section 2.3) during training. |
| 3.5 | QAT tốn train lâu, cần dữ liệu có nhãn, tìm siêu tham số | T2 | NAGEL tr.19 | longer training times, need for labeled data and hyper-parameter search |
| 3.5 | QAT chuẩn bắt đầu từ model pretrained và các bước PTQ để hội tụ nhanh | T2 | NAGEL tr.23 | we always start from a pre-trained model and follow some PTQ steps in order to have faster convergence and higher accuracy |
| 3.5 | CLE cân bằng dynamic range giữa các lớp liên tiếp | T2 | NAGEL tr.12 | achieves this by equalizing dynamic ranges across consecutive layers |
| 3.5 | Khối Quantizer trong đồ thị mô phỏng | T2 | NAGEL tr.6 | we introduce quantizer blocks in the compute graph to induce quantization effects |
| 3.5 | Vào và ra của Quantizer đều float, ra nằm trên lưới | T2 | NAGEL tr.6 | Both the input and output of the quantizer are in floating-point format but the output lies on the quantization grid. |
| 3.5 | Quantizer giữa weight và conv, sau activation; bias thường không lượng tử hóa | T2 | NAGEL tr.6 | Quantizer blocks are added in between the weights and the convolution to simulate weight quantization, and after the activation function to simulate activation quantization. |
| 3.5 | Bias không lượng tử hóa vì lưu độ chính xác cao hơn | T2 | NAGEL tr.6 | The bias is often not quantized because it is stored in higher-precision. |
| 3.5 | Mô phỏng để thử tùy chọn và tăng tốc QAT trên GPU | T2 | NAGEL tr.6 | it enables GPU acceleration for quantization-aware training |
| 3.5 | Nhãn Figure 4b: Weights, Quantizer, Conv, Biases, Activation, Output | T2 | NAGEL tr.6 | (đọc từ hình) |
| 3.5 | Đạo hàm của làm tròn bằng 0 hoặc không xác định | T2 | NAGEL tr.19 | is either zero or undefined everywhere, which makes gradient-based training impossible |
| 3.5 | STE xấp xỉ đạo hàm của làm tròn bằng 1 (Eq. 36) | T2 | NAGEL tr.19 | which approximates the gradient of the rounding operator as 1 |
| 3.5 | Backward bỏ qua khối Quantizer do giả định STE | T2 | NAGEL tr.20 | in the backward pass we effectively skip the quantizer block due to the STE assumption |
| 3.5 | Eq. 37: đạo hàm bằng 1 nếu q_min <= x <= q_max, ngược lại 0 | T2 | NAGEL tr.20 | (đọc từ hình) |
| 3.5 | GHOLAMI: STE xấp xỉ phép làm tròn bằng hàm đồng nhất | T2 | GHOLAMI tr.9 | STE essentially ignores the rounding operation and approximates it with an identity function |
| 3.5 | GHOLAMI: simulated quantization lưu tham số bit thấp, tính bằng float | T2 | GHOLAMI tr.12 | the quantized model parameters are stored in low-precision |
| 3.5 | GHOLAMI: phải dequantize trước phép tính float | T2 | GHOLAMI tr.12 | need to be dequantized before |
| 3.5 | GHOLAMI: integer-only mọi phép tính bằng số nguyên | T2 | GHOLAMI tr.12 | However, in integer-only quantization, all |
| 3.5 | Figure 8: caption pipeline PTQ chuẩn; hộp xanh bắt buộc, hộp ngọc khuyến nghị | T2 | NAGEL tr.16 | Standard PTQ pipeline. Blue boxes represent required steps and the turquoise boxes recommended choices. |
| 3.5 | Figure 8: nhãn các hộp (Pre-trained FP Model, CLE, Add Quantizers, Weight Range Setting, Use Data?, AdaRound, Bias Correction, Activation Range Setting) | T2 | NAGEL tr.16 | (đọc từ hình) |
| 3.5 | CLE là bước tiền xử lý model đầy đủ độ chính xác | T2 | NAGEL tr.16 | which is a pre-processing step for the full precision model |
| 3.5 | Weight symmetric, activation asymmetric; per-channel cho weight nếu hỗ trợ | T2 | NAGEL tr.16 | If supported by the HW/SW stack then it is favorable to use per-channel quantization for weights. |
| 3.5 | Range weight bằng MSE theo lớp | T2 | NAGEL tr.16 | we recommend using the layer-wise MSE based criteria |
| 3.5 | AdaRound khi có tập calibration nhỏ | T2 | NAGEL tr.16 | we next apply AdaRound in order to optimize the rounding of the weights |
| 3.5 | Bias correction phân tích khi không có dữ liệu và mạng dùng BN | T2 | NAGEL tr.16 | we can use analytical bias correction instead |
| 3.5 | Range activation bằng MSE cho phần lớn lớp | T2 | NAGEL tr.16 | We use the MSE based criteria for most of the layers |
| 3.5 | CLE: phần tử trong cùng tensor có độ lớn khác nhau | T2 | NAGEL tr.10 | elements in the same tensor can have significantly different magnitudes |
| 3.5 | CLE dựa trên tính chất scaling equivariance của ReLU | T2 | NAGEL tr.11 | a positive scaling equivariance holds |
| 3.5 | CLE Table 3: MobileNetV2 FP32 71.72, INT8 0.12 | T2 | NAGEL tr.12 | Original model 71.72 0.12 |
| 3.5 | CLE Table 3: thêm CLE, INT8 69.91 | T2 | NAGEL tr.12 | + CLE 71.70 69.91 |
| 3.5 | Điều kiện Table 3: MobileNetV2, ImageNet, 8 bit | T2 | NAGEL tr.12 | Impact of cross-layer equalization (CLE) for MobileNetV2. ImageNet validation accuracy (%), evaluated at full precision and 8-bit quantization. |
| 3.5 | Bias correction: sai số lượng tử hóa thường lệch | T2 | NAGEL tr.12 | quantization error is often biased |
| 3.5 | Bias correction: hiệu chỉnh gộp vào bias, không tốn thêm khi suy luận | T2 | NAGEL tr.13 | can thus be absorbed into the bias without any additional overhead at inference time |
| 3.5 | Bias correction Table 4: Original 71.72, 0.12 | T2 | NAGEL tr.14 | Original Model 71.72 0.12 |
| 3.5 | Bias correction Table 4: thêm bias correction, INT8 52.02 | T2 | NAGEL tr.14 | + bias correction 71.72 52.02 |
| 3.5 | Điều kiện Table 4: MobileNetV2 | T2 | NAGEL tr.14 | Impact of bias correction for MobileNetV2. |
| 3.5 | AdaRound: làm tròn gần nhất chưa tối ưu cho task loss | T2 | NAGEL tr.13 | showed that rounding-to-nearest is not optimal in terms of the |
| 3.5 | AdaRound chỉ cần ít dữ liệu không nhãn, không tuning siêu tham số | T2 | NAGEL tr.15 | It requires only a small amount of unlabeled data samples, no hyperparameter tuning or end-to-end finetuning |
| 3.5 | Table 5: Nearest, mọi lớp 23.99 | T2 | NAGEL tr.15 | Nearest 52.29 23.99 |
| 3.5 | Table 5: AdaRound (Eq. 35), mọi lớp 68.60 | T2 | NAGEL tr.15 | AdaRound (equation 35) 69.58 68.60 |
| 3.5 | Điều kiện Table 5: ResNet18, ImageNet, trung bình 5 lần | T2 | NAGEL tr.15 | validation accuracy (%) for ResNet18 averaged over 5 runs |
| 3.5 | QAREP: RepVGG-A0 từ 72.4% xuống 52.2% với PTQ chuẩn | T2 | QAREP tr.1 | A standard post-training quantization scheme tremendously degrades the accuracy of RepVGG-A0 from 72.4% to 52.2%. |
| 3.5 | QAREP abstract: hơn 20% top-1 | T2 | QAREP tr.1 | more than 20% top-1 accuracy drop on ImageNet |
| 3.5 | QAREP Table 5: RepVGG-A0 FP32 72.4, INT8 52.2 | T2 | QAREP tr.6 | RepVGG-A0‡ 72.4 52.2 3256 8.30 1.4 |
| 3.5 | QAREP Table 5: RepVGG-B1g4 FP32 77.6, INT8 0.55 | T2 | QAREP tr.6 | RepVGG-B1g4‡ 77.6 0.55 868 36.12 7.3 |
| 3.5 | QAREP: 8-bit, gồm lớp đầu và cuối, symmetric uniform, PyTorch-Quantization | T2 | QAREP tr.6 | the quantization scheme is set to symmetric uniform |
| 3.5 | QAREP Table 8: YOLOv6s-RepVGG FP32 42.4, INT8 35.0 | T2 | QAREP tr.7 | YOLOv6s-RepVGG⋆ 42.4 35.0 (7.4↓) 300 |
| 3.5 | QAREP: YOLOv6s-RepVGG sụt 7.4% mAP qua PTQ | T2 | QAREP tr.7 | Noticeably, YOLOv6s-RepVGG suffers a huge quantization degradation for about 7.4% mAP via PTQ. |
| 3.5 | Các mức giảm 20.2 và 77.05 điểm: 72.4 - 52.2, 77.6 - 0.55 (phép tính của bộ hình) | tính | QAREP tr.6 | (số học) |
| 3.5 | Lượng tử hóa YOLOv8 (SiLU, C2f, DFL, detect head) | T2 | (không có) | (unknown) |
| 3.5 | Điều kiện Table 3 của QYOLO: metric COCO chuẩn | T2 | QYOLO tr.8 | we employed standard COCO metrics on the bounding box detection task |
| 3.5 | QYOLO Table 3: real-valued YOLOv5s 37.4 | T2 | QYOLO tr.10 | Real-valued - 37.4 57.1 40.1 21.6 42.3 48.9 |
| 3.5 | Debug: FP32 sanity check, đặt bit-width 32 | T2 | NAGEL tr.17 | Set the quantized model bit-width to 32 bits for both weights and activation |
| 3.5 | Debug: xem weight hay activation ảnh hưởng độc lập | T2 | NAGEL tr.17 | identify how activation or weight quantization impact the performance independently |
| 3.5 | Debug: sửa weight bằng CLE, per-channel, bias correction, AdaRound | T2 | NAGEL tr.17 | Fixing weight quantization If the previous step shows that weight quantization does cause significant accuracy drop |
| 3.5 | Debug: sửa activation bằng range setting khác hoặc chỉnh CLE | T2 | NAGEL tr.19 | we can also try using different range setting methods or adjust CLE |
| 3.5 | Debug: phân tích từng lớp, các lớp còn lại giữ 32 bit | T2 | NAGEL tr.19 | We set each quantizer sequentially, to the target bit-width while keeping the rest of the network to 32 bits |
| 3.5 | Debug: trực quan hóa tensor | T2 | NAGEL tr.19 | we recommended visualizing the tensor distribution at different granularities |
| 3.5 | Debug: cuối cùng mới dùng QAT | T2 | NAGEL tr.19 | we may have to resort to other methods, such as quantization-aware training (QAT) |
| 3.5 | Figure 9: sai số là chênh lệch độ chính xác float và lượng tử | T2 | NAGEL tr.18 | Error is the difference between floating-point and quantized model accuracy. |
| 3.5 | Figure 9: nhãn và chiều mũi tên của lưu đồ | T2 | NAGEL tr.18 | (đọc từ hình) |
| 3.5 | Giá trị ngưỡng ε của Figure 9 | T2 | (không có) | (unknown) |
| 3.5 | QYOLO Table 3: real-valued YOLOv5s 37.4, YOLOv5m 45.1 | T2 | QYOLO tr.10 | Real-valued - 45.1 64.1 49.0 28.1 50.6 57.8 |
| 3.5 | QYOLO Table 3 YOLOv5s: 6-32 chỉ weight 36.7 (-0.7) | T2 | QYOLO tr.10 | 6-32 only weights 36.7(-0.7) 56.6 39.3 20.9 41.4 48.4 |
| 3.5 | QYOLO Table 3 YOLOv5s: 32-6 chỉ activation 36.6 (-0.8) | T2 | QYOLO tr.10 | 32-6 only activation 36.6(-0.8) 56.2 39.3 21.0 42.0 47.9 |
| 3.5 | QYOLO Table 3 YOLOv5s: 4-32 chỉ weight 19.6 (-16.3) | T2 | QYOLO tr.10 | 4-32 only weights 19.6(-16.3) 35.6 19.3 11.3 22.5 25.7 |
| 3.5 | QYOLO Table 3 YOLOv5s: 32-4 chỉ activation 30.6 (-5.3) | T2 | QYOLO tr.10 | 32-4 only activation 30.6(-5.3) 49.1 32.6 17.0 36.7 40.7 |
| 3.5 | QYOLO Table 3 YOLOv5m: 6-32 chỉ weight 44.7 (-0.4) | T2 | QYOLO tr.10 | 6-32 only weights 44.7(-0.4) 63.9 48.6 28.0 50.3 57.3 |
| 3.5 | QYOLO Table 3 YOLOv5m: 32-6 chỉ activation 44.3 (-0.8) | T2 | QYOLO tr.10 | 32-6 only activation 44.3(-0.8) 63.4 48.1 28.4 50.3 57.2 |
| 3.5 | QYOLO Table 3 YOLOv5m: 4-32 chỉ weight 34.6 (-9.4) | T2 | QYOLO tr.10 | 4-32 only weights 34.6(-9.4) 54.0 37.3 20.0 39.2 45.3 |
| 3.5 | QYOLO Table 3 YOLOv5m: 32-4 chỉ activation 37.7 (-6.3) | T2 | QYOLO tr.10 | 32-4 only activation 37.7(-6.3) 57.3 41 .8 23.7 44.1 51.0 |
| 3.5 | QYOLO viết weight "consistently" gây sụt nhiều hơn | T2 | QYOLO tr.10 | quantizing the weights consistently induces larger performance degradation |
| 3.5 | Điều kiện Table 3: weight, activation hoặc cả hai được lượng tử hóa | T2 | QYOLO tr.10 | A comparison of Quantization type. |
| 3.5 | QAREP: QAT chỉ áp dụng cho RepVGG ở deploy mode | T2 | QAREP tr.10 | QAT methods can only be applied for RepVGG in deploy mode |
| 3.2 | NAGEL tr.16: 8 bit within 0.7% | T2 | NAGEL tr.16 | (within 0.7%) |
| 3.2 | NAGEL tr.25: 8 bit within only 1% | T2 | NAGEL tr.25 | within only 1% of |
| 3.2 | NAGEL tr.16: EfficientDet trên COCO 2017 trong thí nghiệm | T2 | NAGEL tr.16 | for object detection, EfficientDet (Tan et al., 2020) on COCO 2017 |
| 3.2 | Mức giảm 1.79 = 40.08 - 38.29 và 4.5% tương đối = 1.79 / 40.08 (phép tính của bộ hình) | tính | NAGEL tr.17 | (số học) |
