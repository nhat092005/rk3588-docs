# Phần 0: Tổng quan

## Câu hỏi mở đầu
Đường học đi qua những phần nào theo thứ tự nào, và một model đi từ best.pt đến NPU RK3588 qua những tầng nào?

## Hình 0.1 (h0-1-ban-do-khoi) [T1 RK3588]
Bản đồ đường học gồm một ô cho mỗi phần 1 đến 11, mỗi ô ghi câu hỏi mở đầu rút gọn, số hình, huy hiệu tier và phần cần biết trước; mũi tên là quan hệ "cần biết trước". Màu ô theo tier: xanh lá là T2 chung (phần 1, 3), xanh dương là T1 RK3588 (phần 2, 4 đến 7, 9), nửa xanh lá nửa xanh dương là phần 8 (Hình 8.1 là T2, Hình 8.2 là T1), đỏ nhạt là T3 đo (phần 10), xám là quyết định (phần 11). Các mũi tên là suy ra của bộ hình từ dòng "Khái niệm" trong các `chu-thich.md` (Phần 4 và 5 tới Phần 9 là suy ra từ đường xuất của Hình 9.3). Ô cuối là câu hỏi của dự án: chọn YOLOv8n SiLU, YOLOv8n ReLU hay YOLO26n cho NPU RK3588, theo quy tắc đã chốt trước khi có số; mAP50-95 INT8 của ba model chưa có nên câu hỏi này chưa trả lời được (khung unknown). Hộp "Cách học": đi theo mũi tên, mỗi hình có huy hiệu tier, khung đỏ là unknown, phần 10 dự đoán trước khi xem, tích ô "đã học" trong trang HTML.
Đọc thêm: 00_ mục 10; quy tắc: `tmp/02_decisions/2026-10-11_model-selection-rule.md`. Số đo: Hình 10.8

## Hình 0.2 (h0-2-duong-di-model) [T1 RK3588]
Một model đi qua năm tầng: PC (Ultralytics xuất ONNX, rồi RKNN-Toolkit2 tạo file .rknn), runtime trên board (RKNN-Toolkit-Lite2 hoặc C API, qua librknnrt.so), driver rknpu 0.9.8 (ioctl, core_mask) rồi NPU 3 core và DDR. Mỗi tầng ghi "Giải thích ở" là hình khái niệm giải thích tầng đó, và "Có thể sai" là điểm đã có nguồn T1 hoặc số đo T3: ONNX đưa vào toolkit khác ONNX của format=onnx (Hình 9.3), sai số lượng tử hóa (Hình 4.3), op rơi sang CPU (Hình 6.1), lệch phiên bản runtime (Hình 5.2), SiLU không chia nhiều core (Hình 6.3, 10.3), SRAM chưa bật trên board (Hình 7.1). Việc đường Ultralytics dùng quantized_dtype mặc định w8a8 là suy ra của bộ hình từ hai dòng nguồn. Hình đánh dấu unknown ba điều: thứ tự ioctl của librknnrt, vai trò MCU_NPU, đường nối NPU tới system SRAM.
Đọc thêm: 09_ mục 9.4; 05_ mục 5.1, 5.3; 02_ mục 2.5. Số đo: Hình 10.3
Khái niệm: Hình 2.1, Hình 2.4, Hình 4.3, Hình 5.1, Hình 5.3, Hình 6.1, Hình 7.1, Hình 9.3

## Hiểu sai thường gặp
- "best.pt chạy thẳng trên NPU" -> model phải được chuyển qua ONNX rồi RKNN bằng RKNN-Toolkit2 (config, load_onnx, build, export_rknn) trước khi chạy [UG232 tr.36; UG232 tr.9] (Hình 0.2, 5.1)
- "Qua NPU nghĩa là mọi op chạy trên NPU và ba core chia đều" -> trong đo T3 của YOLOv8n INT8, Transpose chạy trên CPU và cả 57 lớp ConvExSwish chỉ chạy core 0 khi CORE_0_1_2 [LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt; LOG 2026-10-10_t3-board-silu-resize/README.md] (Hình 6.1, 6.3, 10.3)
- "Export ONNX rồi build INT8 là xong, độ chính xác tự giữ" -> độ chính xác lượng tử phải kiểm: simulator đúng là điều kiện cho runtime đúng, và chưa có mAP INT8 của model nào trong ba model [UG232 tr.131; tmp/02_decisions/2026-10-11_model-selection-rule.md] (Hình 4.3, 10.7)
- "ReLU nhanh hơn SiLU 29 đến 39% nên chọn ReLU" -> số đo đó trên trọng số ngẫu nhiên, chỉ là phép đo cấu trúc, không dùng để chọn model; quy tắc chọn dùng mAP50-95 INT8 [tmp/02_decisions/2026-10-11_model-selection-rule.md] (Hình 10.1, 0.1)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao ONNX do YOLO(...).export(format="onnx") khác ONNX thật đưa vào onnx2rknn, và khác ở những op nào của YOLOv8n?
Đáp án: với format rknn và quantize 8, Ultralytics bọc đầu ra bằng _NormalizeCoords để scale INT8 per-tensor của RKNN giữ được điểm số lớp; ONNX thật có thêm op: Concat 17 thành 18, Slice 2 thành 4, Div 1 thành 2 [ULT engine/exporter.py:1063, 1101; REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json] (Hình 9.3, 0.2)
### Câu 2 (phân biệt)
Hai nghĩa của "fallback" trong tài liệu RKNN là gì, và mỗi nghĩa nằm ở tầng nào của đường đi?
Đáp án: fallback_prior_device của config() nói về op NPU không hỗ trợ (rời NPU sang CPU hoặc GPU, tầng toolkit trên PC); UG152 nói các op ngoài danh sách đa core "fallback to Core0" (ở lại NPU, về core 0, tầng chọn core của runtime và driver) [API232 tr.17; UG152 tr.27] (Hình 6.1, 2.4)
### Câu 3 (áp dụng)
Bạn chạy model YOLOv8n SiLU INT8 với RKNN_NPU_CORE_0_1_2 và kỳ vọng nhanh gấp ba so với CORE_0. Đường đi ở Hình 0.2 và số đo cho biết điều gì?
Đáp án: không nên kỳ vọng: OPL ghi ConvolutionSwish là 多核联合 暂不支持 và ở T3 cả 57 lớp ConvExSwish chạy 100%/0%/0%, nên model SiLU không khác biệt ngoài độ trải giữa các core_mask, trong khi model ReLU (ConvRelu chia ba core) nhanh hơn CORE_0 khoảng 8%; kết quả chỉ cho YOLOv8n INT8 640x640, RK3588S, trọng số ngẫu nhiên [OPL tr.63; LOG 2026-10-10_t3-board-silu-resize/README.md] (Hình 2.4, 6.3, 10.3)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 0.1 | Câu hỏi mở đầu của Phần 1 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/01-npu-co-ban/chu-thich.md | tính convolution bằng những đơn vị nào |
| 0.1 | Câu hỏi mở đầu của Phần 1 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/01-npu-co-ban/chu-thich.md | vì sao cách giữ và di chuyển dữ liệu quan trọng hơn số phép nhân |
| 0.1 | Câu hỏi mở đầu của Phần 2 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/02-phan-cung-rk3588/chu-thich.md | gồm những khối nào, nối với SoC bằng đường nào |
| 0.1 | Câu hỏi mở đầu của Phần 3 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/03-ly-thuyet-luong-tu/chu-thich.md | biến thành số nguyên INT8 như thế nào, sai số đến từ đâu |
| 0.1 | Câu hỏi mở đầu của Phần 4 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/04-luong-tu-rknn/chu-thich.md | cho chọn những kiểu, thuật toán, phương pháp lượng tử nào, làm sao tìm lớp gây sai số |
| 0.1 | Câu hỏi mở đầu của Phần 5 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/05-toolchain/chu-thich.md | phải gọi những hàm nào ở đâu |
| 0.1 | Câu hỏi mở đầu của Phần 5 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/05-toolchain/chu-thich.md | phần mềm trên board xếp thành những tầng nào |
| 0.1 | Câu hỏi mở đầu của Phần 6 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/06-compiler-op/chu-thich.md | chạy trên NPU RK3588 hay rơi sang CPU |
| 0.1 | Câu hỏi mở đầu của Phần 6 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/06-compiler-op/chu-thich.md | được ghép với op đứng trước và chia cho ba core không |
| 0.1 | Câu hỏi mở đầu của Phần 7 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/07-bo-nho-hieu-nang/chu-thich.md | nằm ở những bộ nhớ nào, một con số độ trễ đo đoạn nào của một frame |
| 0.1 | Câu hỏi mở đầu của Phần 8 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/08-thiet-ke-model/chu-thich.md | tiêu chí nào đã có nguồn T1 (vendor), T2 (paper) hoặc T3 |
| 0.1 | Câu hỏi mở đầu của Phần 8 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/08-thiet-ke-model/chu-thich.md | vẫn là unknown trên RK3588 |
| 0.1 | Câu hỏi mở đầu của Phần 9 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | YOLOv8n và YOLO26n khác nhau ở khối nào |
| 0.1 | Câu hỏi mở đầu của Phần 9 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | đi qua đường xuất RKNN thành lớp nào trên NPU RK3588 |
| 0.1 | Câu hỏi mở đầu của Phần 10 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Những điều ở phần cứng và API (phần 2) |
| 0.1 | Câu hỏi mở đầu của Phần 10 (rút gọn trên hình) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | có thấy được trong số đo thật trên board RK3588S không, và số đo nào đủ chắc để kết luận |
| 0.1 | Phần 1: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/01-npu-co-ban/chu-thich.md | Hình 1.1 (h1-1-mac-pe) [T2 chung] |
| 0.1 | Phần 1: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/01-npu-co-ban/chu-thich.md | Hình 1.5 (h1-5-systolic-da-loi) |
| 0.1 | Phần 2: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/02-phan-cung-rk3588/chu-thich.md | Hình 2.1 (h2-1-npu-trong-soc) [T1 RK3588] |
| 0.1 | Phần 2: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/02-phan-cung-rk3588/chu-thich.md | Hình 2.5 (h2-5-mot-job) |
| 0.1 | Phần 3: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/03-ly-thuyet-luong-tu/chu-thich.md | Hình 3.1 (h3-1-affine) [T2 chung] |
| 0.1 | Phần 3: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/03-ly-thuyet-luong-tu/chu-thich.md | Hình 3.5 (h3-5-ptq-qat) |
| 0.1 | Phần 4: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/04-luong-tu-rknn/chu-thich.md | Hình 4.1 (h4-1-ho-tro-rk3588) [T1 RK3588] |
| 0.1 | Phần 4: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/04-luong-tu-rknn/chu-thich.md | Hình 4.4 (h4-4-mau-thuan-tai-lieu) |
| 0.1 | Phần 5: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/05-toolchain/chu-thich.md | Hình 5.1 (h5-1-chuoi-api) [T1 RK3588] |
| 0.1 | Phần 5: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/05-toolchain/chu-thich.md | Hình 5.3 (h5-3-stack-board) |
| 0.1 | Phần 6: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/06-compiler-op/chu-thich.md | Hình 6.1 (h6-1-npu-hay-cpu) [T1 RK3588] |
| 0.1 | Phần 6: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/06-compiler-op/chu-thich.md | Hình 6.4 (h6-4-layout) |
| 0.1 | Phần 7: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/07-bo-nho-hieu-nang/chu-thich.md | Hình 7.1 (h7-1-duong-du-lieu) [T1 RK3588] |
| 0.1 | Phần 7: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/07-bo-nho-hieu-nang/chu-thich.md | Hình 7.3 (h7-3-cong-cu-do) |
| 0.1 | Phần 9: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | Hình 9.1 (h9-1-v8n-26n) [T1 RK3588] |
| 0.1 | Phần 9: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | Hình 9.4 (h9-4-ma-tran-tieu-chi) |
| 0.1 | Phần 10: hình đầu và tier | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Hình 10.1 (h10-1-silu-relu) [T3 đo] |
| 0.1 | Phần 10: hình cuối (số hình của ô) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Hình 10.8 (h10-8-do-tre-map) |
| 0.1 | Phần 8: hình 8.1 là T2 chung (ô nửa xanh lá) | tính | REPO docs/tools/visual_guide/npu_rk3588/08-thiet-ke-model/chu-thich.md | Hình 8.1 (h8-1-reparam) [T2 chung] |
| 0.1 | Phần 8: hình 8.2 là T1 RK3588 (ô nửa xanh dương) | tính | REPO docs/tools/visual_guide/npu_rk3588/08-thiet-ke-model/chu-thich.md | Hình 8.2 (h8-2-checklist) [T1 RK3588] |
| 0.1 | Phần 11: hình 11.1 | tính | REPO docs/tools/visual_guide/npu_rk3588/README.md | h11-1-quy-tac |
| 0.1 | Phần 11: hình 11.2 | tính | REPO docs/tools/visual_guide/npu_rk3588/README.md | h11-2-unknown |
| 0.1 | Mũi tên 1 -> 2 (hình 1.1 nối về hình 2.2, 2.3) | tính | REPO docs/tools/visual_guide/npu_rk3588/01-npu-co-ban/chu-thich.md | Khái niệm: Hình 2.2, Hình 2.3 |
| 0.1 | Mũi tên 3 -> 4 (hình 3.1 nối về hình 4.1) | tính | REPO docs/tools/visual_guide/npu_rk3588/03-ly-thuyet-luong-tu/chu-thich.md | Khái niệm: Hình 4.1 |
| 0.1 | Mũi tên 4 -> 5 (hình 5.1 nối về hình 4.1) | tính | REPO docs/tools/visual_guide/npu_rk3588/05-toolchain/chu-thich.md | Khái niệm: Hình 4.1 |
| 0.1 | Mũi tên 2 -> 6 (hình 6.1 nối về hình 2.4) | tính | REPO docs/tools/visual_guide/npu_rk3588/06-compiler-op/chu-thich.md | Khái niệm: Hình 2.4, Hình 8.2, Hình 9.3 |
| 0.1 | Mũi tên 2 -> 7 (hình 7.1 nối về hình 2.1 đến 2.3) | tính | REPO docs/tools/visual_guide/npu_rk3588/07-bo-nho-hieu-nang/chu-thich.md | Khái niệm: Hình 2.1, Hình 2.2, Hình 2.3, Hình 5.2, Hình 5.3 |
| 0.1 | Mũi tên 3 -> 8 và ô 8 cần Hình 3.5, 6.3 (hình 8.1 nối về hình 3.5, 6.3) | tính | REPO docs/tools/visual_guide/npu_rk3588/08-thiet-ke-model/chu-thich.md | Khái niệm: Hình 3.5, Hình 6.3 |
| 0.1 | Mũi tên 6 -> 9 (hình 9.3 nối về hình 6.2, 6.3) | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | Khái niệm: Hình 6.2, Hình 6.3 |
| 0.1 | Mũi tên 4 -> 9 và 5 -> 9: suy ra của bộ hình từ đường xuất RKNN (Hình 9.3) đi qua toolkit (Phần 5) và lượng tử (Phần 4) | tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/chu-thich.md | (số học) |
| 0.1 | Mũi tên 7 -> 10 (hình 10.2 nối về hình 7.3, 6.2, 9.3) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Khái niệm: Hình 7.3, Hình 6.2, Hình 9.3 |
| 0.1 | Mũi tên 9 -> 10 (hình 10.4 nối về hình 9.1, 9.3, 1.4) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Khái niệm: Hình 9.1, Hình 9.3, Hình 1.4 |
| 0.1 | Mũi tên 10 -> 11 (hình 10.8 nối về hình 11.1) | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Khái niệm: Hình 11.1, Hình 7.2 |
| 0.1 | Phần 10 cần Phần 1 đến 9: suy ra của bộ hình | tính | REPO tmp/02_decisions/2026-10-11_hoc-theo-hinh.md | (số học) |
| 0.1 | Phần 10: mỗi biểu đồ có câu dự đoán và link hai chiều với hình khái niệm | tính | REPO tmp/02_decisions/2026-10-11_hoc-theo-hinh.md | link hai chiều với hình khái niệm |
| 0.1 | Câu hỏi dự án: ba ứng viên | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | chọn model triển khai trên RK3588: YOLOv8n SiLU, YOLOv8n ReLU, YOLO26n |
| 0.1 | Quy tắc: chọn model nhanh nhất | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | nhanh nhất |
| 0.1 | Quy tắc: mAP50-95 INT8 không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm |
| 0.1 | Quy tắc: không rõ thì giữ YOLOv8n SiLU | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | giữ YOLOv8n SiLU |
| 0.1 | Quy tắc chốt trước khi có số | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Vì vậy quy tắc được chốt trước |
| 0.1 | Chưa có mAP INT8 của model nào trong ba model | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Chưa có AP INT8 của bất kỳ model nào trong ba model |
| 0.1 | Hình 10.7 và 10.8 chờ pipeline phase3, phase4 | tính | REPO docs/tools/visual_guide/npu_rk3588/10-so-do-thuc-te/chu-thich.md | Trạng thái: chờ pipeline phase3 và phase4 |
| 0.1 | Cách học 2: huy hiệu tier | tính | REPO docs/tools/visual_guide/README.md | Huy hiệu tier |
| 0.1 | Cách học 3: khung đỏ là unknown, nguồn không cho | tính | REPO docs/tools/visual_guide/README.md | điều nguồn không cho; không đoán |
| 0.1 | Cách học 4: Phần 10 dự đoán trước khi xem | tính | REPO docs/tools/visual_guide/README.md | Dự đoán trước khi xem |
| 0.1 | Cách học 5: ô đã học trong trang HTML | tính | REPO tmp/02_decisions/2026-10-11_hoc-theo-hinh.md | ô "đã học" (localStorage) |
| 0.1 | Cách học 1: thứ tự học theo mũi tên (suy ra của bộ hình) | tính | REPO tmp/02_decisions/2026-10-11_hoc-theo-hinh.md | (số học) |
| 0.1 | Nội dung unknown: mAP INT8 chưa có | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Chưa có AP INT8 của bất kỳ model nào trong ba model |
| 0.2 | Lệnh chạy: trọng số best.pt của một run | tính | REPO ai/automation/bench_gpu.py:33 | weights = run_dir / "weights" / "best.pt" |
| 0.2 | Ultralytics: nhánh end2end tắt cho rknn | T1 | ULT engine/exporter.py:687 | model.end2end = False |
| 0.2 | Ultralytics: _NormalizeCoords khi format rknn | T1 | ULT engine/exporter.py:1063 | self.args.format == "rknn" |
| 0.2 | Ultralytics: và quantize 8 | T1 | ULT engine/exporter.py:1064 | and self.args.quantize == 8 |
| 0.2 | Ultralytics: lý do chuẩn hóa tọa độ | T1 | ULT engine/exporter.py:1101 | # Normalize coordinates by input size so RKNN's per-tensor INT8 scale preserves class scores. |
| 0.2 | _NormalizeCoords là mã Ultralytics | T1 | ULT engine/exporter.py:1108 | from ultralytics.utils.export.engine import _NormalizeCoords |
| 0.2 | Ultralytics: opset = min(opset or 19, 19) | T1 | ULT engine/exporter.py:1538 | self.args.opset = min(self.args.opset or 19, 19)  # rknn-toolkit expects opset<=19 |
| 0.2 | Ultralytics: onnxslim.slim | T1 | ULT engine/exporter.py:1139 | model_onnx = onnxslim.slim(model_onnx) |
| 0.2 | Ultralytics: INT8 xóa file ONNX sau khi build, đồ thị chứa tọa độ chuẩn hóa | T1 | ULT engine/exporter.py:1565 | if self.args.quantize == 8:  # INT8 graphs hold normalized coordinates, so they are not reusable |
| 0.2 | YOLOv8n ONNX của format=onnx: Concat 17 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Concat": 17, "Split": 8 |
| 0.2 | YOLOv8n ONNX của format=onnx: Slice 2 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Slice": 2, "Sub": 2 |
| 0.2 | YOLOv8n ONNX của format=onnx: Div 1 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Softmax": 1, "Div": 1 |
| 0.2 | YOLOv8n ONNX đưa vào toolkit: Concat 18 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Concat": 18, "Split": 8 |
| 0.2 | YOLOv8n ONNX đưa vào toolkit: Slice 4 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Slice": 4, "MaxPool": 3 |
| 0.2 | YOLOv8n ONNX đưa vào toolkit: Div 2 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Sub": 2, "Div": 2 |
| 0.2 | Ultralytics gọi config với mean, std, target_platform (không có quantized_dtype) | T1 | ULT utils/export/rknn.py:74 | "mean_values": [[0, 0, 0]], "std_values": [[255, 255, 255]], "target_platform": name |
| 0.2 | quantized_dtype không truyền nên dùng mặc định w8a8 (suy ra của bộ hình từ hai dòng) | T1 | ULT utils/export/rknn.py:74 | (số học) |
| 0.2 | quantized_dtype mặc định w8a8 | T1 | API232 tr.7 | The default value is "w8a8". |
| 0.2 | target_platform 'rk3588' được hỗ trợ | T1 | API232 tr.8 | 'rk3588' are currently supported. The default value is None. |
| 0.2 | Ultralytics: load_onnx | T1 | ULT utils/export/rknn.py:76 | rknn.load_onnx(model=onnx_file) |
| 0.2 | load_onnx nhận đường dẫn .onnx | T1 | API232 tr.12 | model: The path of ONNX model file (suffixed with ".onnx"). |
| 0.2 | Ultralytics: build với dataset khi INT8 | T1 | ULT utils/export/rknn.py:79 | build_kwargs["dataset"] = str(dataset) |
| 0.2 | build: do_quantization mặc định True | T1 | API232 tr.14 | do_quantization: Whether to quantize the model. The default value is True. |
| 0.2 | build: dataset hiệu chỉnh lượng tử | T1 | API232 tr.14 | dataset: A input dataset for rectifying quantization parameters. |
| 0.2 | Ultralytics: export_rknn ghi file .rknn | T1 | ULT utils/export/rknn.py:81 | rknn.export_rknn( |
| 0.2 | export_rknn lưu file .rknn | T1 | API232 tr.15 | Save RKNN model in the specified file (suffixed with ".rknn"). |
| 0.2 | Thứ tự Configuration, Loading, Building, Export | T1 | UG232 tr.9 | Model Configuration: Fill in the necessary configuration parameters in RKNN-Toolkit2 |
| 0.2 | Building bằng rknn.build() | T1 | UG232 tr.9 | Model Building: Build the RKNN model using the rknn.build() interface. |
| 0.2 | Export bằng rknn.export_rknn() | T1 | UG232 tr.9 | Model Export: Export the RKNN model as a file (.rknn format) using the rknn.export_rknn() interface |
| 0.2 | Sai ở toolkit: simulator đúng là điều kiện cho runtime đúng | T1 | UG232 tr.131 | Correct simulator inference results are the prerequisite for correct board-side runtime inference. |
| 0.2 | Sai ở toolkit: so từng lớp với golden (accuracy analysis) | T1 | UG232 tr.31 | The cosine distance and Euclidean distance from the beginning to the current layer simulator result compared with the golden result. |
| 0.2 | T3: Transpose Target CPU INT8 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Transpose INT8 CPU (4,1,1,8400) |
| 0.2 | T3: InputOperator Target CPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | InputOperator UINT8 CPU |
| 0.2 | T3: OutputOperator Target CPU | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | OutputOperator INT8 CPU |
| 0.2 | T3: Transpose là lớp duy nhất ngoài Input, Output trên CPU (Hình 6.1) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Transpose 1 809 0 0 809 |
| 0.2 | Không đặt target_platform thì model chỉ chạy trên RK3566/RK3568 | T1 | UG232 tr.173 | the generated RKNN model can only run on RK3566/RK3568. |
| 0.2 | Lite2: giao diện Python suy luận trên board | T1 | UG232 tr.36 | RKNN-Toolkit Lite2 provides users with a Python interface for board-side model inference |
| 0.2 | C API: rknn_init | T1 | HDR dòng 489 | int rknn_init(rknn_context* context, void* model, uint32_t size, uint32_t flag, rknn_init_extend* extend); |
| 0.2 | C API: rknn_run | T1 | HDR dòng 589 | int rknn_run(rknn_context context, rknn_run_extend* extend); |
| 0.2 | librknnrt.so là RKNPU2 Runtime | T1 | QS232 tr.15 | RKNPU2 Runtime library (librknnrt.so): The main responsibility is to load the RKNN model in the system |
| 0.2 | Lite2 và C API dựa vào librknnrt.so | T1 | UG232 tr.155 | RKNN-Toolkit Lite2 and RKNPU2 C API relies on this file to use NPU resources. |
| 0.2 | core_mask: AUTO | T1 | UG152 tr.26 | RKNN_NPU_CORE_AUTO : Referring to automatic mode, meaning that it will select the idle core inside the NPU; |
| 0.2 | core_mask: CORE_0 | T1 | UG152 tr.26 | RKNN_NPU_CORE_0 : Running on the NPU0 core; |
| 0.2 | core_mask: CORE_1 | T1 | UG152 tr.26 | RKNN_NPU_CORE_1: Runing on the NPU1 core; |
| 0.2 | core_mask: CORE_2 | T1 | UG152 tr.26 | RKNN_NPU_CORE_2: Runing on the NPU2 core; |
| 0.2 | core_mask: CORE_0_1 | T1 | UG152 tr.26 | RKNN_NPU_CORE_0_1: Running on both NPU0 and NPU1 core simultaneously; |
| 0.2 | core_mask: CORE_0_1_2 | T1 | UG152 tr.26 | RKNN_NPU_CORE_0_1_2: Running on both NPU0, NPU1 and NPU2 simultaneously. |
| 0.2 | Phiên bản RKNN Server, Runtime, Toolkit phải khớp | T1 | UG232 tr.17 | It is important to ensure consistency among the versions of RKNN Server, Runtime library and RKNN-Toolkit2. |
| 0.2 | T3: board có librknnrt 2.3.0 | T3 | LOG 2026-09-18_board-bringup-log.md:47 | librknnrt version: 2.3.0 |
| 0.2 | T3: PC dùng rknn-toolkit2 2.3.2 | T3 | LOG 2026-09-18_board-bringup-log.md:48 | rknn-toolkit2==2.3.2 |
| 0.2 | T3: log ghi lệch phiên bản là nguyên nhân lỗi kết nối | T3 | LOG 2026-09-18_board-bringup-log.md:49 | Đây chính là nguyên nhân gây lỗi kết nối |
| 0.2 | Node /dev/dri/renderD129 là node NPU của RK3588, Runtime dựa vào nó | T1 | UG232 tr.155 | /dev/dri/renderD129 is RK3588's NPU device node. Runtime relies on this node to enable NPU. |
| 0.2 | ioctl SUBMIT của driver | T1 | DRV rknpu_drv.c:671 | DRM_IOCTL_DEF_DRV(RKNPU_SUBMIT, __rknpu_submit_ioctl, DRM_RENDER_ALLOW), |
| 0.2 | Job xếp vào todo_list của từng core theo core_mask | T1 | DRV rknpu_job.c:547-549 | list_add_tail(&job->head[i], &subcore_data->todo_list); |
| 0.2 | Driver ghi thanh ghi khi commit job | T1 | DRV rknpu_job.c:272 | static inline int rknpu_job_subcore_commit_pc |
| 0.2 | Driver có trình xử lý ngắt | T1 | DRV rknpu_job.c:640 | static inline irqreturn_t rknpu_irq_handler(int irq, void *data, int core_index) |
| 0.2 | Mask AUTO 0x00 | T1 | DRV rknpu_job.h:24 | #define RKNPU_CORE_AUTO_MASK 0x00 |
| 0.2 | Mask 0x01, 0x02, 0x04 | T1 | DRV rknpu_job.h:25-27 | #define RKNPU_CORE0_MASK 0x01 #define RKNPU_CORE1_MASK 0x02 #define RKNPU_CORE2_MASK 0x04 |
| 0.2 | Mask 0x3 | T1 | DRV rknpu_job.c:404-424 | case RKNPU_CORE0_MASK \| RKNPU_CORE1_MASK: |
| 0.2 | Mask 0x7 | T1 | DRV rknpu_job.c:404-424 | case RKNPU_CORE0_MASK \| RKNPU_CORE1_MASK \| RKNPU_CORE2_MASK: |
| 0.2 | Mask khác báo lỗi | T1 | DRV rknpu_job.c:404-424 | Unknown core mask: %d |
| 0.2 | AUTO chọn core có task_num nhỏ nhất | T1 | DRV rknpu_job.c:508-538 | if (task_num > rknpu_dev->subcore_datas[i].task_num) { |
| 0.2 | AUTO: job chạy trên một core | T1 | DRV rknpu_job.c:508-538 | job->use_core_num = 1; |
| 0.2 | T3: driver trên board v0.9.8 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:45 | RKNPU driver: v0.9.8 |
| 0.2 | NPU có ba core | T1 | TRM1 tr.1984 | Include triple NPU CORE |
| 0.2 | Buffer 384KB trong mỗi core (x3) | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 0.2 | Engine gồm bộ tiền xử lý convolution, buffer, MAC array, accumulator | T1 | TRM1 tr.1985 | This unit include convolution pre-process controller, internal buffer, mac array, accumulator. |
| 0.2 | DPU xử lý hàm theo giá trị đơn | T1 | TRM1 tr.1985 | Data Processing Unit mainly process the single data calculate, such as leaky_relu, relu, relux, sigmoid, tanh |
| 0.2 | PPU: pooling trên đầu ra của DPU | T1 | TRM1 tr.1985 | Planar Processing Unit mainly provide planar function followed by output data from Data Processing Unit, such as average pooling, max pooling, min pooling |
| 0.2 | Khối CNA, thứ tự CNA, buffer, MAC array, accumulator, DPU, PPU | T1 | TRM1 tr.1985 | (đọc từ hình) |
| 0.2 | AXI master lấy dữ liệu từ bộ nhớ nối SoC interconnect | T1 | TRM1 tr.1985 | The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect. |
| 0.2 | Bốn DDR scheduler, nối DDR | T1 | TRM2 tr.16 | Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency |
| 0.2 | OPL 3.2.17 ConvolutionSwish: 多核联合 暂不支持 | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish Convolution 与 Swish 融合计算, Output = Swish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 0.2 | T3: cả 57 lớp ConvExSwish chạy 100%/0%/0% ở CORE_0_1_2 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | cả 57 lớp `ConvExSwish` đều `100%/0%/0%` |
| 0.2 | T3: board có CONFIG_ROCKCHIP_RKNPU_SRAM not set | T3 | REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7 | CONFIG_ROCKCHIP_RKNPU_SRAM not set |
| 0.2 | Kernel cần CONFIG_ROCKCHIP_RKNPU_SRAM=y để dùng SRAM cho NPU | T1 | UG232 tr.106 | Kernel config needs to enable CONFIG_ROCKCHIP_RKNPU_SRAM=y |
| 0.2 | unknown: librknnrt gọi ioctl nào theo thứ tự nào | T1 | UG232 tr.155 | (unknown) |
| 0.2 | unknown: vai trò MCU_NPU với một job NPU | T1 | (không có) | (unknown) |
| 0.2 | unknown: đường nối NPU tới system SRAM | T1 | (không có) | (unknown) |
