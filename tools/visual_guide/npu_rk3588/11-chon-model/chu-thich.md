# Phần 11: Chọn model

## Câu hỏi mở đầu
Với YOLOv8n SiLU, YOLOv8n ReLU và YOLO26n, quy tắc nào quyết định model triển khai trên RK3588, và hiện còn thiếu đầu vào nào để áp dụng nó?

## Hình 11.1 (h11-1-quy-tac) [T3 đo]
Quy tắc chọn model được chốt trước khi có số: chọn model nhanh nhất theo trung vị độ trễ tier 1 ở core_mask AUTO trong số các model có mAP50-95 INT8 chạy trên board không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm; nếu không model nào nhanh hơn rõ ràng thì giữ YOLOv8n SiLU. Hiện mới có mAP FP32 của bốn model và độ trễ cấu trúc trên trọng số ngẫu nhiên, cả hai không dùng để chọn; mAP INT8 trên board, độ trễ tier 1 của model đã huấn luyện và độ trải giữa các phiên đo đều chưa có, nên chưa có khuyến nghị. Mọi lựa chọn về sau chỉ là tạm vì chỉ có seed 42; phase 10 thêm seed 43 và 44 cho model được chọn. Cách tính "độ trải" và mức "rõ ràng" chưa được chốt (todo mục 3.4); ba phiên đo xen kẽ là đề xuất, chưa quyết.
Khái niệm: Hình 7.2
Số đo: Hình 10.4, Hình 10.5, Hình 10.7, Hình 10.8
Đọc thêm: 09_ mục 9.5.5; 00_index mục 10.

## Hình 11.2 (h11-2-unknown) [T3 đo]
Bản đồ này gom chỗ còn unknown hoặc mâu thuẫn theo khối 01 đến 09 và các việc T3 đang chờ, mỗi mục gắn nhãn "chặn quyết định chọn model" hoặc "không chặn" kèm hình nơi mục đó được giải thích. Chỉ có ba mục chặn (mAP INT8 trên board, độ trễ tier 1 của model đã huấn luyện, độ trải giữa các phiên), cộng hai mục unknown thuộc khối 08 và 09 phụ thuộc cùng phép đo INT8; phần còn lại không làm quy tắc ở Hình 11.1 mất khả năng áp dụng. Hình chỉ nêu vài mục mỗi khối và số dòng unknown còn lại (đếm từ bảng nguồn của từng phần). Hộp D chỉ liệt kê các ghi chú cũ trong 00_index và 01_ đến 08_ đã được kiểm lại trên nguồn gốc là sai hoặc thiếu; chưa sửa các file .md. Hình lấy tier hỗn hợp: nhãn tier ở từng hàng.
Khái niệm: Hình 6.2, Hình 8.2, Hình 9.4
Số đo: Hình 10.1, Hình 10.4
Đọc thêm: 00_index mục 8, 9, 10.

## Hiểu sai thường gặp
- "YOLO26n chậm hơn nên bị loại" -> mới có độ trễ trên trọng số ngẫu nhiên (chậm hơn khoảng 13 đến 16%), quy tắc không dùng số này; loại hay không do mAP INT8 và trung vị tier 1 của model đã huấn luyện [REPO model-selection-rule.md; LOG phaseA README.md] (Hình 11.1, Hình 10.4)
- "mAP FP32 quyết định model" -> quy tắc dùng mAP50-95 INT8 chạy trên board; FP32 chỉ để biết trước [REPO model-selection-rule.md; REPO todo-npu-model-selection.md] (Hình 11.1, Hình 10.5)
- "Chênh 0.0025 mAP là có ý nghĩa" -> chênh lệch giữa YOLOv8n SiLU 0.5908 và YOLO26n 0.5883 là 0.0025, chỉ có seed 42 nên chưa biết nhiễu giữa các seed (phép tính của bộ hình) [REPO sfchd_5class.csv; REPO model-selection-rule.md] (Hình 11.1, Hình 10.5)
- "ReLU thấp hơn SiLU 0.0073 nên ReLU kém" -> ReLU khởi tạo từ yolov8n.pt (SiLU); "cận dưới thực tế" là nhận định chưa kiểm [REPO args.yaml; LOG errata #25] (Hình 11.1, Hình 11.2)
- "Chạy make phase4 là có số cho cả ba model" -> phase4 chỉ chạy YOLOv8n và YOLOv8s; YOLO26n và ReLU cần target riêng [REPO pipeline.py:19] (Hình 11.1)
- "Độ trễ của một model là một số cố định" -> cùng file .rknn cho trung vị 19.154 rồi 22.021 ms ở hai lượt, nên cần độ trải giữa các phiên trước khi gọi một model là nhanh hơn [LOG summary.json, summary2.json] (Hình 11.2)
- "Đã đo thì đã có khuyến nghị" -> chưa có khuyến nghị: thiếu ba đầu vào ở Hình 11.1 [REPO 00_index.md] (Hình 11.1)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao quy tắc được chốt trước khi có số INT8?
Đáp án: Nếu chọn ngưỡng sau khi thấy số, ngưỡng dễ bị kéo theo kết quả; chưa có AP INT8 của model nào khi chốt [REPO model-selection-rule.md] (Hình 11.1)
### Câu 2 (phân biệt)
Phân biệt số đã có và số quy tắc cần.
Đáp án: Đã có: mAP50-95 FP32 test (0.5908, 0.6152, 0.5883, 0.5835 cho YOLOv8n, YOLOv8s, YOLO26n, ReLU) và độ trễ trên trọng số ngẫu nhiên; cả hai không dùng để chọn. Cần: mAP50-95 INT8 trên board (make phase3), trung vị tier 1 ở AUTO (make phase4 và target riêng) và độ trải giữa các phiên [REPO sfchd_5class.csv; REPO model-selection-rule.md] (Hình 11.1)
### Câu 3 (áp dụng)
Giả sử sau phase3 và phase4, ReLU nhanh hơn YOLOv8n SiLU 0.3 ms nhưng độ trải giữa các phiên là khoảng 2.5 ms. Quy tắc cho kết quả gì?
Đáp án: Chênh lệch nằm trong độ trải nên không model nào nhanh hơn rõ ràng: giữ YOLOv8n SiLU, và đó vẫn là quyết định tạm vì chỉ có seed 42. Con số 2.5 ms là độ lệch đã thấy giữa các phiên đo trên trọng số ngẫu nhiên (YOLOv8n AUTO: 19.399, 21.66, 19.152 ms, lớn nhất trừ nhỏ nhất 2.508), chưa phải độ trải chính thức [REPO model-selection-rule.md; LOG stats_latency.txt] (Hình 11.1, Hình 11.2)
### Câu 4 (áp dụng)
Mục "độ chính xác INT8 của khối attention chưa đo" chặn quyết định không, và đóng bằng cách nào?
Đáp án: Có, vì YOLO26n cần mAP INT8 trên board; đóng bằng make phase3 rồi đo mAP FP32 so INT8 [REPO 00_index.md mục 9 khối 09] (Hình 11.2)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 11.1 | Quy tắc: không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:25 | không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm |
| 11.1 | Chỉ số tốc độ: trung vị tier 1 ở AUTO | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:24 | Trung vị độ trễ tier 1 |
| 11.1 | Khi không rõ giữ YOLOv8n SiLU | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:26 | giữ YOLOv8n SiLU |
| 11.1 | Quyết định tạm, phase 10 seed 43 và 44 | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:29 | Phase 10 thêm seed 43 và 44 cho model được chọn |
| 11.1 | Số trọng số ngẫu nhiên không dùng để chọn | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:32 | không dùng chúng để chọn model |
| 11.1 | Ngưỡng chốt trước vì dễ bị kéo theo kết quả | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:15 | ngưỡng dễ bị kéo theo kết quả |
| 11.1 | Lớp vi phạm PPE sụt mạnh cần xem riêng | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:31 | cần xem riêng trước khi triển khai |
| 11.1 | Ứng viên và giao thức: seed 42, 100 epoch, calibration 300 ảnh | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:22 | calibration 300 ảnh, seed 42 |
| 11.1 | mAP50-95 FP32 YOLOv8n 0.5908 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:2 | 0.8924,0.5908,0.7186 |
| 11.1 | mAP50-95 FP32 YOLOv8s 0.6152 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:3 | 0.9035,0.6152,0.7381 |
| 11.1 | mAP50-95 FP32 YOLO26n 0.5883 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:4 | 0.8865,0.5883,0.7207 |
| 11.1 | mAP50-95 FP32 YOLOv8n ReLU 0.5835 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:5 | 0.8845,0.5835,0.7161 |
| 11.1 | Chênh 0.0025 giữa YOLOv8n SiLU và YOLO26n (phép tính của bộ hình) | tính | REPO ai/automation/leaderboards/sfchd_5class.csv | (số học) |
| 11.1 | phase4 chỉ chạy YOLOv8n và YOLOv8s | T3 | REPO ai/automation/pipeline.py:19 | MODELS = ["yolov8n_baseline", "yolov8s_baseline"] |
| 11.1 | seed 43 và 44 chỉ cho phase 10 | T3 | REPO ai/automation/pipeline.py:21 | EXTRA_SEEDS = [43, 44] |
| 11.1 | Tier 1 là 5 lần lặp mỗi phiên, trung vị | T3 | REPO ai/core/rknn/benchmark.py:23 | PERF_REPEATS = 5 |
| 11.1 | Đề xuất 3 phiên xen kẽ, chưa quyết | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:87 | Cần quyết khi tới bước này |
| 11.1 | Điều kiện board và sudo | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:39 | Người dùng nhập mật khẩu sudo trong tmux |
| 11.1 | Board offline lúc viết | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:18 | Offline từ 2026-10-11 |
| 11.1 | Phase 10 lệnh MODELS=<model> | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:96 | make phase10 DATASET=sfchd_5class MODELS=<model> |
| 11.1 | ReLU khởi tạo từ yolov8n.pt | T3 | REPO ai/automation/runs/sfchd_5class_yolov8n_relu_100ep_s42/args.yaml:18 | pretrained: yolov8n.pt |
| 11.1 | Transferred 322/355 ở ReLU | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/logs/train_20261011-030722.log | Transferred 322/355 items from pretrained weights |
| 11.1 | Transferred 322/355 ở baseline | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/logs/train_20260927-021114.log | Transferred 322/355 items from pretrained weights |
| 11.1 | YOLO26n chậm hơn khoảng 13 đến 16% (trọng số ngẫu nhiên) | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Chậm hơn khoảng 13 đến 16% |
| 11.1 | Chưa có khuyến nghị về chọn model | T3 | REPO docs/npu_study/00_index.md:21 | Không có khuyến nghị |
| 11.1 | Chưa có run nào có số INT8 và tier 1 (kiểm tay: gen.py dừng nếu file xuất hiện) | T3 | (không có) | (unknown) |
| 11.2 | Độ lệch phiên YOLOv8n AUTO: 19.399, 21.66, 19.152 | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | [19.399, 21.66, 19.152] |
| 11.2 | 21.66 trừ 19.152 bằng 2.508 (phép tính của bộ hình) | tính | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | (số học) |
| 11.2 | SiLU silu_opt3 AUTO lượt 1: 19.154 ms | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "silu_opt3": { "npu_latency_ms": 19.154 |
| 11.2 | SiLU silu_opt3 AUTO lượt 2: 22.021 ms | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|AUTO": { "ms": 22.021 |
| 11.2 | Truy vấn đề xuất INT8 YOLOv8 | T2 | REPO docs/npu_study/00_index.md:499 | YOLOv8 post-training quantization INT8 accuracy drop |
| 11.2 | Truy vấn đề xuất SiLU so ReLU | T3 | REPO docs/npu_study/00_index.md:565 | SiLU vs ReLU latency RKNN RK3588 INT8 YOLOv8 |
| 11.2 | Cách đóng khối 09: huấn luyện, xuất INT8, đo mAP | T3 | REPO docs/npu_study/00_index.md:577 | Huấn luyện YOLO26n 5 lớp, xuất INT8, đo mAP FP32 so INT8 |
| 11.2 | make phase4 cộng target riêng cho YOLO26n và ReLU | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:71 | Phase 4 cho YOLO26n và ReLU |
| 11.2 | T3 còn lại không chặn: fix_freq, SiLU dao động, ConvExSwish đa lõi | T3 | REPO tmp/2026-10-11_todo-npu-model-selection.md:106 | Cơ chế `fix_freq=True` |
| 11.2 | Mâu thuẫn Resize: UG232 tr.176 | T1 | UG232 tr.176 | will convert Reszie to ConvTranspose |
| 11.2 | Mâu thuẫn Resize: OPL có mục Resize cho RK3588 | T1 | OPL tr.86 | 3.2.54 Resize |
| 11.2 | PRelu: UG152 liệt kê trong danh sách đa core | T1 | UG152 tr.27 | Prelu, LeakyRelu |
| 11.2 | PRelu: OPL ghi 暂不支持 | T1 | OPL tr.85 | 3.2.51 PRelu |
| 11.2 | INT16: UG152 Table 4-6 cột Int16 cho RK3588 | T1 | UG152 tr.56 | RK3588 16 8 8 |
| 11.2 | INT16: API232 w16a16i chỉ RV1103 và RV1106 | T1 | API232 tr.7 | Only RV1103/RV1106 supported |
| 11.2 | Calibration normal 20-100 ảnh | T1 | API232 tr.8 | The recommended quantization data is generally about 20-100 pieces. |
| 11.2 | Calibration 20-200 ở UG232 tr.159 | T1 | UG232 tr.159 | For normal or kl_divergence, 20-200 sets of data are recommended. |
| 11.2 | Hybrid hàng 5, 6, 8 không có nguồn phân xử | T1 | REPO docs/tools/visual_guide/npu_rk3588/04-luong-tu-rknn/chu-thich.md:23 | Hàng 5, 6, 8 không có code hay nguồn thứ ba phân xử |
| 11.2 | 17 sự kiện ngắt | T1 | TRM1 tr.2053 | one of the 17 possible events that the RKNN can signal to the host processor |
| 11.2 | Bit 13 là bit cuối được mô tả | T1 | TRM1 tr.1995 | mask[13]: DMA write error; |
| 11.2 | Errata #1: PD_NPUTOP còn BIU_NPUTOP | T1 | TRM1 tr.1093 | BIU_NPUTOP |
| 11.2 | Errata #4: UG232 phát hành 2025-04-03 | T1 | UG232 tr.1 | Release Date: 2025-04-03 |
| 11.2 | Errata #5: API232 nói step2 'generated' (không nói có ghi file; 'không ghi file' là suy ra) | T1 | API232 tr.21 | the hybrid quantized RKNN model is generated |
| 11.2 | Errata #9: truncation error ở UG232 tr.121 | T1 | UG232 tr.121 | does not introduce truncation error but is sensitive to outliers |
| 11.2 | Errata #14: 0.8.8 không bắt buộc | T1 | UG232 tr.136 | This step is not mandatory. |
| 11.2 | Errata #12: QYOLO YOLOv5s 6-bit activation -0.8 | T2 | QYOLO tr.10 | 32-6 only activation 36.6(-0.8) |
| 11.2 | Errata #12: QYOLO YOLOv5s 6-bit weight -0.7 | T2 | QYOLO tr.10 | 6-32 only weights 36.7(-0.7) |
| 11.2 | Errata #13: driver_version không có trong rknpu_debugger.c | T1 | DRV rknpu_debugger.c | (unknown) |
| 11.2 | Danh sách errata lấy các hàng "có" của file errata | T3 | LOG 2026-10-11_independent-verification/visual-guide_md-errata.md | Đã kiểm lại |
| 11.2 | Errata #24: SiLU độ trải lớn nhất 4.907 ms | T3 | LOG 2026-10-11_independent-verification/visual-guide_md-errata.md | 4.907 ms |
| 11.2 | Errata #25: ReLU cận dưới không nguồn nào kiểm | T3 | LOG 2026-10-11_independent-verification/visual-guide_md-errata.md | không nguồn nào kiểm |
| 11.2 | Hỏi RK3588 dùng dataflow nào (Hình 1.2) | T1 | (không có) | (unknown) |
| 11.2 | Ridge point của RK3588 (Hình 1.4) | T1 | (không có) | (unknown) |
| 11.2 | "PE" của RK3588 là gì (Hình 1.1) | T1 | (không có) | (unknown) |
| 11.2 | Cách userspace chia việc giữa các core (Hình 2.4) | T1 | (không có) | (unknown) |
| 11.2 | Quy ước đếm 6 TOPS (Hình 2.3) | T1 | (không có) | (unknown) |
| 11.2 | Khai triển CNA, BS, BN, CBUF (Hình 2.2) | T1 | (không có) | (unknown) |
| 11.2 | Lượng tử hóa YOLOv8 không có trong paper của bộ (Hình 3.4, 3.5) | T2 | (không có) | (unknown) |
| 11.2 | NAGEL không nêu KL divergence và percentile (Hình 3.3) | T2 | (không có) | (unknown) |
| 11.2 | Giá trị epsilon của Figure 9 (Hình 3.5) | T2 | (không có) | (unknown) |
| 11.2 | Số ảnh calibration cho miền hẹp (Hình 4.1) | T1 | (không có) | (unknown) |
| 11.2 | int8, int16 trong custom_quantize_layers trên RK3588 (Hình 4.2) | T1 | (không có) | (unknown) |
| 11.2 | Ngưỡng cosine đạt (Hình 4.3) | T1 | (không có) | (unknown) |
| 11.2 | Lite2 có cần rknn_server không (Hình 5.2) | T1 | (không có) | (unknown) |
| 11.2 | eval_perf qua PC so với C API (Hình 5.2) | T1 | (không có) | (unknown) |
| 11.2 | Vì sao UG232 không nhắc node power, freq (Hình 5.3) | T1 | (không có) | (unknown) |
| 11.2 | OPL không nêu quy tắc rơi về CPU (Hình 6.1) | T1 | (không có) | (unknown) |
| 11.2 | Luật ghép SiLU, ConvExSwish (Hình 6.2, 6.3) | T1 | (không có) | (unknown) |
| 11.2 | Thuật toán fusion, thứ tự pass (Hình 6.3) | T1 | (không có) | (unknown) |
| 11.2 | Ranh giới Total Time(us) (Hình 7.2) | T1 | (không có) | (unknown) |
| 11.2 | Log T3 tier 2 chưa có (Hình 7.2) | T3 | (không có) | (unknown) |
| 11.2 | Hiệu lực fix_freq chưa đo (Hình 7.3) | T3 | (không có) | (unknown) |
| 11.2 | AP INT8 của ReLU trên board chưa có (Hình 8.2, 10.7) | T3 | (không có) | (unknown) |
| 11.2 | AP của ReLU là cận dưới: nhận định chưa kiểm (Hình 8.2, 10.5) | T3 | (không có) | (unknown) |
| 11.2 | Re-param trên RK3588 INT8 chưa biết (Hình 8.2) | T2 | (không có) | (unknown) |
| 11.2 | Độ chính xác INT8 của khối attention chưa đo (Hình 9.4) | T3 | (không có) | (unknown) |
| 11.2 | Tên ConvExSwish không có trong OPL, UG232 (Hình 9.3) | T1 | (không có) | (unknown) |
| 11.2 | Quy tắc nhận exSDPAttention (Hình 9.3) | T1 | (không có) | (unknown) |
| 11.2 | Số dòng unknown mỗi phần (phép đếm của bộ hình trên bảng nguồn các phần 1 đến 10) | tính | REPO docs/tools/visual_guide/npu_rk3588/11-chon-model/gen.py | (số học) |
