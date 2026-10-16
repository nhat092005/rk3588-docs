# Ghi chú chuyên đề: Lượng tử hóa trong NPU RK3588 (Per-Layer, Per-Channel & Đánh đổi thực tế)

## Câu hỏi mở đầu
Scale factor (s) và Zero-point (z) ánh xạ số thực sang số nguyên INT8 như thế nào, tại sao việc lựa chọn phạm vi lượng tử theo từng tầng (Per-Layer) hay theo từng kênh (Per-Channel) lại quyết định độ chính xác và khả năng tương thích phần cứng, và quy tắc đánh đổi giữa mAP và tốc độ khi lượng tử hóa INT8 trên NPU RK3588 ra sao?

## Hình Q.1 (hq-1-per-layer-quantization) [T2 chung]
Lượng tử hóa theo tầng (Per-Layer Quantization, hay Per-Tensor Quantization):
Ánh xạ Affine lượng tử hóa biến đổi giá trị số thực dấu phẩy động x sang số nguyên hẹp q (INT8):
q = clamp(round(x / s) + z, q_min, q_max)
x ≈ s · (q - z)
Trong đó:
- Scale factor (s): Là một số thực dương biểu diễn kích thước bước nhảy (step size) của lưới lượng tử, s = (x_max - x_min) / (q_max - q_min).
- Zero-point (z): Là một số nguyên biểu diễn điểm 0 thực tế được ánh xạ vào lưới số nguyên để đảm bảo giá trị 0 thực được biểu diễn chính xác (không gây sai số khi đệm zero-padding).

Quy mô Per-Layer: Đúng 1 bộ tham số (s, z) duy nhất được dùng chung cho toàn bộ tensor kích thước [H, W, C] (hoặc toàn bộ ma trận trọng số/kích hoạt của cả một tầng mạng).
Ưu điểm: Đơn giản nhất về mặt phần cứng. Mọi phần tử đều có chung scale, nên khi thực hiện phép tính nhân-cộng trên mảng MAC, toàn bộ tích lũy bên trong (psums) đều chung hệ số tỷ lệ mà không cần thao tác rescale giữa chừng. Mọi phần cứng NPU (bao gồm RK3588 cho cả activation và weight) đều hỗ trợ Per-Layer (UG232 tr.120).

Vấn đề Outlier kênh: Nếu trong cùng một layer, có một kênh chứa giá trị cực đoan (outlier, ví dụ dải [-50, 50]) trong khi phần lớn các kênh còn lại chỉ dao động trong dải nhỏ [-1, 1], thì giá trị s của cả layer bị kéo giãn rất lớn để bao trùm [-50, 50]. Hệ quả là dải [-1, 1] của các kênh nhỏ bị nén co cụm chỉ trong vài mức rời rạc của INT8 (bad quantization resolution), gây mất mát độ phân giải nghiêm trọng và làm sụt giảm độ chính xác của toàn bộ mô hình (GHOLAMI tr.6).
Đọc thêm: 03_ mục 3.1, 3.2; 04_ mục 4.1. Khái niệm: Hình 3.1, Hình 3.2, Hình 4.1

## Hình Q.2 (hq-2-per-channel-quantization) [T1 RK3588]
Lượng tử hóa theo kênh (Per-Channel Quantization) và Cơ chế Rescale phần cứng:
Nguyên lý: Mỗi kênh (thường là Output Channel c trong [1, Cout] của tensor trọng số Weight) được phân bổ một cặp (s_w,c, z_w,c) riêng biệt:
q_w,c = round(w_c / s_w,c) + z_w,c
Kênh có dải giá trị rộng dùng scale lớn, kênh có dải giá trị hẹp dùng scale nhỏ. Nhờ đó, mỗi kênh đều tận dụng trọn vẹn 256 mức độ phân giải của INT8, loại bỏ hoàn toàn hiện tượng outlier của kênh này chèn ép độ phân giải của kênh khác (NAGEL tr.8; GHOLAMI tr.7).

Cơ chế toán học & Rescale trên mảng MAC:
Xét phép tính chập cho kênh đầu ra c:
y_c = Σ_j (w_c,j · x_j) ≈ Σ_j [ s_w,c · (q_w,c,j - z_w) · s_x · (q_x,j - z_x) ]
Do s_w,c và s_x không phụ thuộc vào chỉ số kênh vào j, ta tách hoàn toàn hệ số scale ra ngoài dấu tổng:
y_c ≈ (s_w,c · s_x) · Σ_j [ (q_w,c,j - z_w) · (q_x,j - z_x) ]
Mảng MAC chỉ cần thực hiện phép nhân-cộng số nguyên trên thanh ghi tích lũy Accumulator INT32. Sau khi hoàn tất toàn bộ tích lũy, phần cứng nhân với hệ số Rescale M_c = (s_w,c · s_x) / s_y tại đầu ra để đưa kết quả INT32 về thang đo INT8 của tầng tiếp theo mà không cần rescale trung gian (NAGEL tr.8).

Tại sao RKNN và NPU RK3588 chỉ hỗ trợ Per-Channel cho Weight mà KHÔNG cho Activation? (UG232 tr.120):
Nếu Activation cũng lượng tử hóa per-channel, mỗi kênh đầu vào j sẽ có một scale s_x,j khác nhau. Khi đó, phép tính thành Σ_j [ s_x,j · s_w,c · (...) ], hệ số s_x,j nằm bên trong dấu tổng Σ_j và thay đổi theo từng kênh j. Mảng MAC không thể cộng dồn tự do mà buộc phải rescale từng tích lũy từng phần (psums) của từng kênh đầu vào trước khi cộng. Phần cứng NPU thương mại thông thường không có mạch rescale tại từng PE của mảng MAC, do đó RKNN-Toolkit2 chỉ hỗ trợ Per-Channel cho Weight, còn Activation và các giá trị trung gian vẫn bắt buộc là Per-Layer (UG232 tr.120; NAGEL tr.8).
Đọc thêm: 03_ mục 3.2; 04_ mục 4.1. Khái niệm: Hình Q.1, Hình 3.2, Hình 4.1

## Hình Q.3 (hq-3-danh-doi-luong-tu-va-quy-tac-chon-model) [T2 chung]
Đánh đổi Lượng tử hóa INT8 so với FP16 và Quy tắc chọn model triển khai của đề tài:
- Lợi ích phần cứng khi lượng tử hóa INT8 trên RK3588:
  - Mảng MAC silicon: Mỗi core NPU hỗ trợ 1024 MACs/chu kỳ ở kiểu INT8, nhưng chỉ hỗ trợ 512 MACs/chu kỳ ở kiểu FP16/BF16.
  - Sức mạnh tính toán: Ở tần số ví dụ 1 GHz, tổng 3 core đạt 1024 x 3 x 2 x 1 GHz = 6.144 TOPS (INT8), gấp đôi năng lực 3.072 TFLOPS của FP16.
  - Băng thông và bộ nhớ: Trọng số INT8 chỉ chiếm 1 byte/tham số (thay vì 2 bytes ở FP16 hoặc 4 bytes ở FP32), giảm 50% áp lực truyền dữ liệu qua DRAM và vừa vặn hơn trong bộ nhớ đệm nội bộ SRAM (384 KB mỗi core).
- Đánh đổi độ chính xác (mAP Degradation):
  - Thu nhỏ miền giá trị từ số thực (Float) về số nguyên 8-bit [-128, 127] không tránh khỏi sai số làm tròn (quantization noise).
  - Độ sụt giảm: Delta_mAP = mAP_FP32 - mAP_INT8.
- Quy tắc chọn model triển khai của đề tài (Chốt trước khi có số):
  - 3 mô hình ứng viên trên tập dữ liệu sfchd_5class: YOLOv8n SiLU (baseline), YOLOv8n ReLU (tối ưu đa lõi NPU), và YOLO26n (kiến trúc không NMS).
  - Tiêu chuẩn tốc độ: Trung vị độ trễ Tier 1 (eval_perf) ở core_mask=AUTO trên board RK3588.
  - Tiêu chuẩn độ chính xác: Điểm mAP50-95 INT8 đo thực nghiệm trực tiếp trên board RK3588 (tập test sfchd).
  - Quy tắc quyết định: Chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm mAP (tuyệt đối).
  - Điều kiện an toàn: Nếu không có model nào nhanh hơn rõ ràng (chênh lệch nằm trong biên độ nhiễu giữa các phiên đo), tiếp tục giữ nguyên YOLOv8n SiLU.
Đọc thêm: 00_index mục 10; 02_ mục 2.3; 11_ mục 11.1, 11.2. Khái niệm: Hình 2.3, Hình 11.1, Hình 11.2

## Hiểu sai thường gặp
- "Scale và Zero-Point là hai số nguyên giống như dữ liệu INT8" -> Dữ liệu lượng tử q là số nguyên (INT8), nhưng Scale s là số thực dấu phẩy động biểu diễn bước lưới, và Zero-point z là số nguyên làm tròn để dịch chuyển mức 0 [NAGEL tr.4; GHOLAMI tr.5] (Hình Q.1)
- "Per-Channel quantization áp dụng bình đẳng cho cả Weight và Activation trên NPU" -> UG232 tr.120 nêu rõ RKNN-Toolkit2 chỉ áp dụng Per-Channel cho weights, còn activation và giá trị trung gian vẫn là Per-Layer vì phần cứng không hỗ trợ rescale accumulator cho từng input channel [NAGEL tr.8; UG232 tr.120] (Hình Q.2)
- "Per-Layer luôn cho độ chính xác tương đương Per-Channel" -> Per-Layer bị nhạy cảm mạnh với outlier giữa các kênh; trong mạng thị giác, Per-Channel cho weight giúp giữ độ chính xác cao hơn rõ rệt mà không tốn chi phí rescale nội bộ [NAGEL tr.8; GHOLAMI tr.6] (Hình Q.1, Hình Q.2)
- "Rescale là một lớp mạng nơ-ron riêng biệt" -> Rescale chỉ là phép nhân hệ số tỉ lệ M = (s_w * s_x) / s_y và dịch bit được tích hợp vào khối DPU hoặc đầu ra accumulator để đưa kết quả INT32 về INT8 [NAGEL tr.8] (Hình Q.2)
- "Lượng tử hóa INT8 luôn làm hỏng độ chính xác của mô hình phát hiện vật thể" -> Với calibration tốt (300 ảnh chuẩn), độ sụt giảm mAP thường dưới 1.0 điểm trong khi tốc độ tăng gần gấp đôi và dung lượng giảm một nửa [REPO tmp/02_decisions/2026-10-11_model-selection-rule.md] (Hình Q.3)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Tại sao khi một tensor có một kênh mang giá trị outlier rất lớn, phương pháp Per-Layer lại làm suy giảm độ chính xác của các kênh còn lại?
Đáp án: Vì Per-Layer dùng chung một giá trị scale s cho toàn bộ các kênh. Khi một kênh có outlier lớn, dải min-max của tensor bị kéo giãn, dẫn đến bước nhảy scale s = (max - min) / 255 rất lớn. Các kênh có dải giá trị nhỏ sẽ bị nén vào chỉ 1-2 mức rời rạc của INT8, làm mất gần như toàn bộ thông tin đặc trưng (Hình Q.1).

### Câu 2 (phân biệt)
Phân biệt Per-Layer và Per-Channel về vị trí lưu trữ và số lượng tham số Scale/ZP.
Đáp án: Per-Layer chỉ lưu 1 cặp (s, z) duy nhất cho cả tensor (áp dụng cho mọi kênh). Per-Channel lưu Cout cặp (s_c, z_c) riêng biệt, mỗi kênh ra có một bộ tham số độc lập (Hình Q.1, Hình Q.2).

### Câu 3 (áp dụng)
Theo tài liệu quyết định của đề tài, điều kiện để chấp nhận một mô hình thay thế (như YOLOv8n ReLU hoặc YOLO26n) thay cho YOLOv8n SiLU là gì?
Đáp án: Mô hình thay thế phải là mô hình nhanh nhất (trung vị độ trễ Tier 1 ở core_mask=AUTO) có điểm mAP50-95 INT8 đo thực nghiệm trên board không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm mAP (tuyệt đối). Nếu không có mô hình nào nhanh hơn rõ ràng, hệ thống sẽ giữ nguyên YOLOv8n SiLU [REPO tmp/02_decisions/2026-10-11_model-selection-rule.md] (Hình Q.3).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| Q.1 | Lưới lượng tử đều | T2 | NAGEL tr.4 | map it to the unsigned integer grid |
| Q.1 | Per-tensor quantization | T2 | NAGEL tr.5 | This is called per-tensor quantization. |
| Q.1 | Layerwise dùng chung range | T2 | GHOLAMI tr.6 | In layerwise quantization, the same clipping range is applied to all the filters that belong to the same layer. |
| Q.1 | Range hẹp mất độ phân giải khi chung quantizer | T2 | GHOLAMI tr.6 | This can result in bad quantization resolution for the channels that have narrow distributions |
| Q.1 | Per-layer quantization trong RKNN | T1 | UG232 tr.120 | Per-Layer quantization quantizes all channels of a network layer as a whole |
| Q.2 | Per-channel quantization | T2 | NAGEL tr.5 | we can specify a different quantizer per output channel. This is known as per-channel quantization |
| Q.2 | Mỗi channel có scale riêng | T2 | GHOLAMI tr.7 | each channel is assigned a dedicated scaling factor |
| Q.2 | Per-channel cải thiện khi phân bố khác nhau | T2 | NAGEL tr.8 | per-channel quantization of the weights can improve accuracy, especially when the distribution of weights varies significantly from channel to channel |
| Q.2 | Per-channel weight áp được không rescale | T2 | NAGEL tr.8 | by applying a separate per-channel weight scale factor without requiring rescaling |
| Q.2 | Không phải phần cứng nào cũng hỗ trợ | T2 | NAGEL tr.8 | not all commercial hardware supports it |
| Q.2 | RKNN chỉ per-channel cho weight | T1 | UG232 tr.120 | Per-Channel quantization is only applied to the weights, while the activation values and intermediate values are still quantized using Per-Layer quantization. |
| Q.3 | 1024 MACs INT8 mỗi chu kỳ trên mỗi lõi NPU | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| Q.3 | Datasheet NPU ghi lên tới 6 TOPS | T1 | DS tr.7 | up to 6TOPs |
| Q.3 | Quy tắc chọn model: nhanh nhất có mAP50-95 INT8 không thấp hơn SiLU quá 1.0 điểm | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:25 | không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm |
| Q.3 | Tốc độ ReLU thấp hơn SiLU 35% trên NPU | T3 | REPO tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md:74 | ReLU thấp hơn 35.0% |
