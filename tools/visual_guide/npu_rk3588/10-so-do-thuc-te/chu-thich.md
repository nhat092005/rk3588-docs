# Phần 10: Số đo thực tế

## Câu hỏi mở đầu
Những điều ở phần cứng và API (phần 2) có thấy được trong số đo thật trên board RK3588S không, và số đo nào đủ chắc để kết luận?

## Hình 10.1 (h10-1-silu-relu) [T3 đo]
Dự đoán trước khi xem: UG232 tr.142 liệt kê "Conv+Relu", "Conv+Sigmoid(Tanh/Elu/Silu...)" và "Conv+Add" trong luật fusion phần cứng (Hình 6.3), UG232 tr.146 xếp "Non-Relu activation function" vào ba loại op kém hiệu quả, và UG152 tr.27 chỉ liệt kê Conv, Add, Concat, Relu... là nhanh hơn khi dùng nhiều core (Hình 2.4). Từ đó hãy dự đoán: khi đổi SiLU thành ReLU, các lớp Conv đổi thành op nào và độ trễ đổi theo chiều nào; và nếu model ReLU còn ghép luôn cả Add, làm sao biết phần giảm đến từ activation hay từ Add.
Trên YOLOv8n trọng số ngẫu nhiên, ReLU có độ trễ thấp hơn SiLU rõ ràng (28.9% ở lượt 1, 35.0% ở lượt 2 khi cả hai model đã bỏ Add), và ở model này phần giảm đến từ activation chứ không từ việc ghép Add. Lượt 1 trộn lẫn hai thay đổi: 57 lớp ConvExSwish thành 51 ConvRelu và 6 ConvReluAdd, đồng thời Add đứng riêng giảm từ 8 xuống 2, nên không tách được. Lượt 2 thêm biến thể noadd (shortcut=False ở 4 khối C2f của backbone), cả SiLU và ReLU đều còn 2 Add đứng riêng: so silu_noadd với relu_noadd chỉ đổi activation (21.431 so 13.929 ms ở AUTO), so relu_opt3 với relu_noadd chỉ đổi Add (13.963 so 13.929 ms, trong độ trải). Số SiLU dao động giữa các phiên: silu_opt3 là 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2 với cùng file .rknn, nên đọc như một khoảng. Kết quả chỉ đúng cho YOLOv8n INT8 640x640 nc=5, RK3588S, toolkit 2.3.2, eval_perf với fix_freq=True, trọng số ngẫu nhiên.
Khái niệm: Hình 6.3, Hình 2.4, Hình 8.2
Đọc thêm: 06_ mục 6.3; 08_ mục 8.2, 8.5; 02_ mục 2.5.

## Hình 10.2 (h10-2-do-tre-tung-lop) [T3 đo]
Dự đoán trước khi xem: UG232 tr.140 nói cột NPU Cycles hiện chỉ có Conv, UG232 tr.146 liệt kê ba loại op kém hiệu quả (chuyển dữ liệu, đổi kích thước, activation không phải Relu), và UG232 tr.177 nói perf_debug=True làm thời gian dài hơn vì một số cơ chế song song có thể bị tắt (Hình 7.3, Hình 6.2). Từ đó hãy dự đoán: loại op nào chiếm phần lớn thời gian của YOLOv8n, lớp đơn lẻ nào tốn nhất, và YOLO26n khác YOLOv8n ở đâu.
Trong cả ba bảng debug, ConvExSwish chiếm phần lớn thời gian (57.6 đến 60.7%), nhưng lớp đơn lẻ tốn nhất của YOLOv8n là exSoftmax13 (11.1% ở model ngẫu nhiên và 8.9% ở model đã huấn luyện), còn YOLO26n không có lớp này và có hai lớp exSDPAttention chiếm 8.7% tổng. Cảnh báo nổi bật: thời gian từng lớp lấy ở chế độ perf_debug có thể lớn hơn độ trễ thật (eval_perf tự in cảnh báo này), nên hình so sánh bằng tỉ lệ phần trăm, không so tổng tuyệt đối: cùng một đồ thị YOLOv8n cho tổng bảng debug 18606 us ở model ngẫu nhiên và 23598 us ở model đã huấn luyện (lệch 27%), trong khi tỉ lệ ConvExSwish là 59.6% và 57.6%. Mỗi bảng là một lần chạy, không có độ trải, nên chênh lệch vài điểm phần trăm không phải kết luận.
Khái niệm: Hình 7.3, Hình 6.2, Hình 9.3
Đọc thêm: 07_ mục 7.3; 09_ mục 9.5.5.

## Hình 10.3 (h10-3-da-loi) [T3 đo]
Dự đoán trước khi xem: UG152 tr.27 chỉ liệt kê Conv, Add, Concat, Relu... là nhanh hơn khi dùng nhiều core, và Operator List ghi ConvolutionSwish là "多核联合: 暂不支持" (không hỗ trợ ghép nhiều core). Từ đó hãy dự đoán lớp ConvExSwish (Conv + SiLU) được chia thế nào giữa ba core khi CORE_0_1_2, và model SiLU có nhanh hơn khi dùng 3 core không.
Khi dùng CORE_0_1_2, các lớp Conv + ReLU được chia gần đều ba core còn mọi lớp ConvExSwish chỉ chạy ở core 0, nên model ReLU nhanh hơn khoảng 8% so với CORE_0 còn model SiLU không khác biệt vượt độ trải của các lần đo. Panel A cho độ trễ trung vị (thanh sai số là nhỏ nhất đến lớn nhất của 5 lần) của năm model với ba giá trị core_mask; panel B là phần trăm khối lượng mỗi core nhận, lấy từ cột WorkLoad của bảng lớp. Số SiLU dao động giữa các phiên (silu_opt3 AUTO là 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2 với cùng file .rknn) nên chênh lệch nhỏ giữa các cột SiLU không phải kết luận. Kết quả chỉ đúng cho YOLOv8n INT8 640x640 nc=5, RK3588S, toolkit 2.3.2, eval_perf với fix_freq=True; trọng số ngẫu nhiên trừ trained_silu_5c.
Khái niệm: Hình 2.4, Hình 6.2
Đọc thêm: 02_ mục 2.5; 08_ mục 8.5.

## Hình 10.4 (h10-4-v8n-26n) [T3 đo]
Dự đoán trước khi xem: YOLO26n có ít FLOPs hơn YOLOv8n khoảng 34% (Hình 9.1), nhưng UG232 tr.146 nói hiệu năng của convolution "will be affected by both computing power and bandwidth" và liệt kê ba loại op kém hiệu quả (Hình 1.4, Hình 9.3). Từ đó hãy dự đoán: trên NPU, YOLO26n nhanh hay chậm hơn YOLOv8n, ở cả ba core_mask hay không, và chênh lệch có vượt độ trải giữa các phiên đo không.
YOLO26n chậm hơn YOLOv8n ở cả ba core_mask (trung vị 22.26 so 19.399 ms ở AUTO), dù ít FLOPs hơn khoảng 34%; chiều chênh lệch vững qua ba phiên nhưng độ lớn chưa chắc. Chênh lệch trung vị là 2.861, 2.538, 3.105 ms (CI 95% bootstrap 1.5 đến 4.498, 1.295 đến 2.883, 1.197 đến 5.363; Mann-Whitney p = 0.00031, 0.00246, 0.00187 cho AUTO, CORE_0, CORE_0_1_2). YOLO26n chậm hơn ở 8 trên 9 cặp (phiên, core_mask); cặp còn lại (CORE_0, phiên 1) YOLO26n nhanh hơn. Ba phiên có thứ tự model xen kẽ để tách hiệu ứng thứ tự. 15 giá trị mỗi nhóm không độc lập (5 lần lặp trong một phiên) và ở mức phiên chỉ có 3 so 3, nên p lạc quan. Trọng số ngẫu nhiên, chỉ cấu trúc và độ trễ: không có accuracy và không dùng để chọn model.
Khái niệm: Hình 9.1, Hình 9.3, Hình 1.4
Đọc thêm: 09_ mục 9.5.5.

## Hình 10.5 (h10-5-duong-cong-train) [T3 đo]
Dự đoán trước khi xem: Y6 tr.8 (T2, YOLOv6 chạy trên GPU T4, không phải RK3588) viết "Conv with SiLU performs the best in accuracy" và Table 4 tr.9 ghi Conv SiLU 36.6% so Conv ReLU 34.8% AP (chỉ YOLOv6-N, khối Conv; cùng bảng: RepConv 36.5 so 35.2, YOLOv6-M 48.9 so 47.7) (Hình 8.2); YOLOv8s lớn hơn YOLOv8n (Hình 9.1). Từ đó hãy dự đoán thứ hạng mAP50-95 của bốn model và vị trí của YOLOv8n ReLU so với YOLOv8n SiLU, biết ReLU được khởi tạo từ trọng số SiLU.
Trên cùng dữ liệu, seed 42 và 100 epoch, YOLOv8s có mAP50-95 test FP32 cao nhất (0.6152) và ba model nano nằm trong khoảng 0.5835 đến 0.5908; YOLOv8n ReLU thấp nhất; nó khởi tạo từ trọng số SiLU (yolov8n.pt) rồi fine-tune (log train: Transferred 322/355 items cho cả YOLOv8n baseline và ReLU), và nhận định "AP này có thể thấp hơn AP của ReLU train từ đầu" là của bộ hình, chưa kiểm bằng thí nghiệm. Panel A và A' là đường cong VAL (tập val, sau mỗi epoch trong lúc train); panel C là số TEST của leaderboard (tập test, best.pt, evaluator protocol v1) và kim cương là giá trị VAL ở epoch 100: hai loại số khác tập, khác evaluator, và best.pt không nhất thiết là epoch 100, nên không so trực tiếp. Chênh lệch giữa ba model nano (0.0073) nhỏ và chỉ có seed 42, nên chưa biết nhiễu giữa các seed; YOLOv8s dùng batch 8, các model còn lại batch 16.
Khái niệm: Hình 8.2, Hình 9.1
Đọc thêm: 08_ mục 8.2, 8.5.

## Hình 10.6 (h10-6-calibration) [T3 đo]
Dự đoán trước khi xem: UG232 tr.165 nói toolkit tự resize ảnh calibration nhưng resize "may also change the image information", nên tốt nhất dùng ảnh đúng kích thước, và dữ liệu npy "needs to be consistent with the shape input by the model"; UG232 tr.132 nói khi bật lượng tử hóa, tập calibration "will undergo normalization first"; API232 tr.7 ghi quantized_dtype mặc định "w8a8" còn UG232 tr.122 ghi 'asymmetric_quantized-8' (Hình 4.1, Hình 3.3). Từ đó hãy dự đoán: ảnh 128x64 đưa vào model 64x64 bị cắt, đệm hay dùng cả ảnh; npy NHWC có được nhận không; mean và std có áp dụng lên npy không; tên cũ asymmetric_quantized-8 còn được config() chấp nhận không.
Trên PC với toolkit 2.3.2 và một model thử (ONNX một Conv 1x1), ảnh calibration khác kích thước được dùng toàn ảnh (không cắt, không đệm) và hai cột kề nhau được lấy trung bình, npy phải ở layout NCHW và không bị tự resize, mean và std được áp dụng lên npy, và asymmetric_quantized-8 vẫn được config() chấp nhận. Mỗi dòng của hình đọc min và max của tensor x trong quant_tab của file .rknn; dải kỳ vọng sau chuẩn hóa là [-100, 0]. Kết quả chỉ trên một model và một phiên bản toolkit: chưa biết thuật toán nội suy chính xác (chỉ loại được nearest), cách xử lý RGB/BGR, ảnh xám, ảnh có alpha, model NHWC, kết quả trên model thật, và ảnh hưởng lên độ chính xác sau lượng tử. Chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ.
Khái niệm: Hình 4.1, Hình 3.3
Đọc thêm: 04_ mục 4.5.

## Hình 10.7 (h10-7-map-int8) [T3 đo]
Dự đoán trước khi xem: UG232 tr.165 nói build FP16 gần như không mất độ chính xác ("almost no accuracy loss"), UG232 tr.131 nói tác động cuối cùng của lượng tử hóa lên độ chính xác "still needs validation on the dataset", và UG232 tr.120 nói activation vẫn lượng tử hóa per-layer (Hình 4.3, Hình 4.1). Từ đó hãy dự đoán: sau INT8 mAP50-95 tổng giảm ít hay nhiều so với FP32 và lớp nào trong năm lớp giảm nhiều nhất. Hình chỉ có điểm xuất phát FP32.
Hình có số FP32 thật: mAP50-95 test của bốn model (0.5908, 0.6152, 0.5883, 0.5835) và AP50-95 của từng lớp; hai cột FP16 và INT8 là chỗ trống có chủ ý, chờ pipeline phase3, không điền số nào và không suy INT8 từ FP32. Lớp head thấp nhất ở cả bốn model (0.3884 đến 0.4532), và head (110 ví dụ) cùng self_clothes (74 ví dụ) có rất ít ví dụ trong tập test so với person (1688), nên chênh lệch nhỏ giữa model ở hai lớp này không phải kết luận khi chỉ có seed 42. Quy tắc chọn model dùng mAP50-95 INT8 tổng, không dùng AP từng lớp; nếu một lớp vi phạm PPE sụt mạnh sau INT8 thì cần xem riêng.
Khái niệm: Hình 4.3, Hình 4.1
Đọc thêm: 04_ mục 4.4, 4.7.
Trạng thái: chờ pipeline phase3 (mAP RKNN FP16/INT8 trên board)

## Hình 10.8 (h10-8-do-tre-map) [T3 đo]
Dự đoán trước khi xem: UG232 tr.142 liệt kê "Conv+Relu" là luật fusion phần cứng và UG232 tr.146 xếp "Non-Relu activation function" vào op kém hiệu quả (Hình 6.3), còn Y6 Table 4 tr.9 (T2, GPU T4) ghi Conv SiLU 36.6% so Conv ReLU 34.8% AP, tức thấp hơn 1.8 điểm (Hình 8.2). Từ đó hãy dự đoán: YOLOv8n ReLU có nằm trong vùng 1.0 điểm mAP50-95 INT8 dưới YOLOv8n SiLU không, và có nhanh hơn rõ ràng không.
Hình này chưa có số: nó sẽ vẽ độ trễ tier 1 (trung vị eval_perf ở core_mask AUTO, từ phase4) trên một trục và mAP50-95 INT8 chạy trên board (phase3, tập test sfchd) trên trục còn lại cho ba ứng viên YOLOv8n SiLU, YOLOv8n ReLU và YOLO26n, kèm vùng rộng 1.0 điểm mAP50-95 dưới YOLOv8n SiLU INT8. Quy tắc chọn đã chốt trước khi có số: chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm tuyệt đối (ví dụ 0.560 so 0.570); nếu không model nào nhanh hơn YOLOv8n SiLU một cách rõ ràng (chênh lệch nằm trong độ trải giữa các phiên đo) thì giữ YOLOv8n SiLU. Số đo trên trọng số ngẫu nhiên (Hình 10.1, 10.4) không được dùng để chọn.
Khái niệm: Hình 11.1, Hình 7.2
Đọc thêm: 09_ mục 9.5.5.
Trạng thái: chờ pipeline phase3 và phase4 (độ trễ tier 1 và mAP INT8 trên board)

## Hiểu sai thường gặp
- "CORE_0_1_2 luôn nhanh hơn CORE_0" -> chỉ model ReLU nhanh hơn khoảng 8% (12.854 so với 13.969 ms ở relu_opt3); với SiLU hai giá trị nằm trong độ trải của nhau [LOG summary2.json] (Hình 10.3)
- "Chọn CORE_0_1_2 thì mọi lớp chạy trên ba core" -> cả 57 lớp ConvExSwish có WorkLoad 100%/0%/0%, tức chỉ core 0 [LOG README.md] (Hình 10.3)
- "Độ trễ của model SiLU là một con số cố định" -> cùng file .rknn cho 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2; đọc như một khoảng [LOG README.md, summary.json, summary2.json] (Hình 10.3)
- "Kết quả này đúng cho mọi Conv + SiLU hoặc mọi model" -> chỉ một kiến trúc YOLOv8n, trọng số ngẫu nhiên và một bản đã huấn luyện; chưa có bản ReLU đã huấn luyện [LOG README.md] (Hình 10.3)
- "ReLU nhanh hơn SiLU 28.9% hoàn toàn nhờ activation" -> lượt 1 trộn hai thay đổi (activation và ghép Add); lượt 2 tách ra: so silu_noadd với relu_noadd (cùng 2 Add đứng riêng) ReLU vẫn thấp hơn 35.0%, còn ghép Add không đóng góp đo được [LOG README.md] (Hình 10.1)
- "Tổng thời gian trong bảng perf_debug là độ trễ của model" -> thời gian ở chế độ debug có thể lớn hơn thực tế; cùng đồ thị YOLOv8n cho 18606 us và 23598 us ở hai lần chạy, nên so bằng tỉ lệ [LOG README.md; UG232 tr.177] (Hình 10.2)
- "YOLO26n ít FLOPs hơn nên nhanh hơn trên NPU" -> trên trọng số ngẫu nhiên YOLO26n chậm hơn khoảng 13 đến 16% ở cả ba core_mask [LOG phaseA README.md] (Hình 10.4)
- "p = 0.00031 nghĩa là độ lớn chênh lệch đã chắc" -> 15 giá trị không độc lập và ở mức phiên chỉ có 3 so 3, nên p lạc quan; chiều chênh lệch vững, độ lớn chưa chắc [LOG phaseA README.md] (Hình 10.4)
- "Số đo trên trọng số ngẫu nhiên dùng được để chọn model" -> chúng chỉ là phép đo cấu trúc và độ trễ, quy tắc chọn không dùng chúng [REPO model-selection-rule.md] (Hình 10.4, Hình 10.8)
- "Đường cong val và số test của leaderboard là cùng một phép đo" -> khác tập (val so test), khác evaluator (protocol v1, không phải model.val()), và best.pt không nhất thiết là epoch 100 [REPO dataset.yaml; REPO run.py:125] (Hình 10.5)
- "mAP50-95 của YOLOv8n ReLU thấp hơn SiLU 0.0073 nên ReLU kém hơn" -> ReLU khởi tạo từ trọng số SiLU rồi fine-tune (nhận định "AP này có thể thấp hơn AP của ReLU train từ đầu" là của bộ hình, chưa kiểm bằng thí nghiệm), và chỉ có seed 42 [RUN args.yaml; REPO model-selection-rule.md] (Hình 10.5)
- "Ảnh calibration khác kích thước bị cắt hoặc đệm letterbox" -> trên model thử, toàn ảnh được dùng và hai cột kề nhau được lấy trung bình; UG232 vẫn khuyên dùng ảnh đúng kích thước [LOG calibration README.md; UG232 tr.165] (Hình 10.6)
- "asymmetric_quantized-8 được config() chấp nhận nên phần cứng hỗ trợ" -> chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ; API232 tr.7 ghi mặc định w8a8 [LOG calibration README.md; API232 tr.7] (Hình 10.6)
- "mAP FP32 trên test cho biết thứ hạng mAP INT8" -> số FP16 và INT8 chưa có (chờ phase3), AP lớp head (110 ví dụ) và self_clothes (74 ví dụ) dựa trên ít ví dụ, chỉ có seed 42 [RUN eval json; REPO model-selection-rule.md] (Hình 10.7)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao model ReLU nhanh hơn khi dùng 3 core còn model SiLU thì không?
Đáp án: Bảng lớp với CORE_0_1_2 cho thấy 51 lớp ConvRelu và 6 lớp ConvReluAdd được chia ba core (khoảng 35%/34%/32%), còn cả 57 lớp ConvExSwish chạy 100%/0%/0% (chỉ core 0); điều này phù hợp với ghi chú "多核联合: 暂不支持" của ConvolutionSwish trong Operator List (OPL không khẳng định ConvolutionSwish và ConvExSwish là cùng một op) [LOG README.md; OPL tr.63] (Hình 10.3, Hình 2.4)
### Câu 2 (phân biệt)
Phân biệt một chênh lệch là kết luận với một chênh lệch nằm trong độ trải, dùng panel A.
Đáp án: Ở mọi core_mask, giá trị lớn nhất của ReLU (14.120 ms) vẫn nhỏ hơn giá trị nhỏ nhất của SiLU (17.671 ms), nên "ReLU nhanh hơn SiLU" là kết luận cho model này; còn SiLU ở CORE_0 và CORE_0_1_2 (20.019 và 19.745 ms) có khoảng nhỏ nhất đến lớn nhất chồng lên nhau nên không phải kết luận [LOG README.md, summary2.json] (Hình 10.3)
### Câu 3 (áp dụng)
Bạn muốn biết model của mình có thật sự dùng ba core khi chọn CORE_0_1_2 không. Đọc gì, và dùng thời gian trong bảng đó để so sánh độ trễ được không?
Đáp án: Chạy eval_perf với perf_debug=True và đọc cột WorkLoad(0/1/2) của bảng lớp: lớp có 100%/0%/0% chỉ chạy ở core 0. Không dùng thời gian của chế độ debug để so sánh độ trễ vì nó có thể lớn hơn thực tế [LOG README.md, silu_opt3_CORE_0_1_2_layers.txt] (Hình 10.3)
### Câu 4 (áp dụng)
Model trained_silu_5c giảm từ 19.225 ms (CORE_0) xuống 18.024 ms (CORE_0_1_2). Có kết luận lợi ích đa core cho SiLU không?
Đáp án: Không. Mức giảm khoảng 6% nhỏ hơn độ trải giữa các phiên của SiLU (silu_opt3 AUTO lệch nhau 2.9 ms giữa lượt 1 và 2), và hai khoảng nhỏ nhất đến lớn nhất (18.836 đến 20.287 và 17.607 đến 19.021 ms) chồng lên nhau [LOG README.md, summary3.json] (Hình 10.3)
### Câu 5 (giải thích)
Vì sao so relu_opt3 với silu_opt3 ở lượt 1 chưa đủ để nói activation gây ra chênh lệch 28.9%, và lượt 2 tách hai yếu tố đó thế nào?
Đáp án: Ở lượt 1 hai thay đổi đi cùng nhau: 57 lớp ConvExSwish thành 51 ConvRelu và 6 ConvReluAdd, đồng thời Add đứng riêng giảm từ 8 xuống 2, nên không tách được phần của từng thay đổi. Lượt 2 bỏ phép cộng residual ở 4 khối C2f (silu_noadd, relu_noadd, cả hai còn 2 Add rời): so hai model này chỉ đổi activation (21.431 so 13.929 ms, thấp hơn 35.0%), còn relu_opt3 so relu_noadd chỉ đổi Add (13.963 so 13.929 ms, trong độ trải) [LOG README.md] (Hình 10.1)
### Câu 6 (phân biệt)
Ở Hình 10.4, phân biệt "chiều chênh lệch vững" với "độ lớn chênh lệch chắc" khi chỉ có 3 phiên mỗi model.
Đáp án: Ở AUTO, Mann-Whitney p = 0.00031 và CI 95% của chênh lệch trung vị là 1.5 đến 4.498 ms không chứa 0, và YOLO26n chậm hơn ở 8 trên 9 cặp (phiên, core_mask): chiều chênh lệch vững. Nhưng 15 giá trị không độc lập (5 lần lặp trong một phiên) và chỉ có 3 so 3 phiên, nên p lạc quan và độ lớn (từ 1.5 đến 4.498 ms) rộng; ở CORE_0 phiên 1 YOLO26n (21.11 ms) còn nhanh hơn YOLOv8n (21.848 ms) [LOG phaseA README.md, stats_latency.txt] (Hình 10.4)
### Câu 7 (phân biệt)
YOLOv8n baseline có val mAP50-95 0.596 ở epoch 100 nhưng test mAP50-95 0.5908 ở leaderboard. Hai số này khác nhau ở những điểm nào, và số nào dùng để xếp hạng model?
Đáp án: Khác tập (val so test), khác evaluator (leaderboard dùng evaluator protocol v1, không phải model.val()), và leaderboard dùng weights/best.pt, không nhất thiết là epoch 100. Xếp hạng dùng số test của leaderboard (cùng một protocol cho cả bốn model); đường cong val chỉ cho thấy diễn biến huấn luyện [REPO dataset.yaml; REPO run.py:125-129] (Hình 10.5)
### Câu 8 (áp dụng)
Bạn muốn chọn giữa YOLOv8n SiLU, YOLOv8n ReLU và YOLO26n. Có dùng Hình 10.1 và 10.4 (trọng số ngẫu nhiên) được không, và cần số nào để áp dụng quy tắc?
Đáp án: Không. Các số đó là phép đo cấu trúc và độ trễ trên trọng số ngẫu nhiên, không có accuracy, và quy tắc chọn không dùng chúng. Cần mAP50-95 INT8 chạy trên board (phase3, tập test sfchd) và trung vị độ trễ tier 1 ở core_mask AUTO (phase4) của ba model đã huấn luyện; chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm, và giữ YOLOv8n SiLU nếu không model nào nhanh hơn rõ ràng. Hiện chưa có số phase3 và phase4 (Hình 10.8); ReLU khởi tạo từ SiLU rồi fine-tune (nhận định "AP này có thể thấp hơn AP của ReLU train từ đầu" là của bộ hình, chưa kiểm bằng thí nghiệm) [REPO model-selection-rule.md] (Hình 10.8, Hình 10.5)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 10.1 | A, lượt 1: SiLU level 1 AUTO, trung vị 19.586 ms, 5 lần 17.881, 19.586, 19.289, 22.147, 22.277 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "silu_opt1": { "npu_latency_ms": 19.586, "all_ms": [ 17.881, 19.586, 19.289, 22.147, 22.277 ] |
| 10.1 | A, lượt 1: SiLU level 2 AUTO, trung vị 19.106 ms, 5 lần 19.123, 19.107, 19.026, 18.950, 19.106 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "silu_opt2": { "npu_latency_ms": 19.106, "all_ms": [ 19.123, 19.107, 19.026, 18.95, 19.106 ] |
| 10.1 | A, lượt 1: SiLU level 3 AUTO, trung vị 19.154 ms, 5 lần 17.769, 19.154, 19.432, 17.984, 19.628 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "silu_opt3": { "npu_latency_ms": 19.154, "all_ms": [ 17.769, 19.154, 19.432, 17.984, 19.628 ] |
| 10.1 | A, lượt 1: ReLU level 3 AUTO, trung vị 13.617 ms, 5 lần 13.482, 13.649, 13.668, 13.617, 13.481 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "relu_opt3": { "npu_latency_ms": 13.617, "all_ms": [ 13.482, 13.649, 13.668, 13.617, 13.481 ] |
| 10.1 | A, lượt 2: SiLU có Add AUTO, trung vị 22.021 ms, 5 lần 20.622, 22.253, 22.145, 21.922, 22.021 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|AUTO": { "ms": 22.021, "all_ms": [ 20.622, 22.253, 22.145, 21.922, 22.021 ] |
| 10.1 | A, lượt 2: SiLU không Add AUTO, trung vị 21.431 ms, 5 lần 20.025, 21.431, 21.779, 21.766, 18.638 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_noadd\|AUTO": { "ms": 21.431, "all_ms": [ 20.025, 21.431, 21.779, 21.766, 18.638 ] |
| 10.1 | A, lượt 2: ReLU có Add AUTO, trung vị 13.963 ms, 5 lần 13.934, 13.942, 13.967, 13.976, 13.963 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_opt3\|AUTO": { "ms": 13.963, "all_ms": [ 13.934, 13.942, 13.967, 13.976, 13.963 ] |
| 10.1 | A, lượt 2: ReLU không Add AUTO, trung vị 13.929 ms, 5 lần 13.787, 14.094, 13.929, 13.914, 13.941 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_noadd\|AUTO": { "ms": 13.929, "all_ms": [ 13.787, 14.094, 13.929, 13.914, 13.941 ] |
| 10.1 | B: SiLU có Add: 57 lớp ConvExSwish (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | ConvExSwish 57 0 0 11095 11095 59.63% |
| 10.1 | B: SiLU có Add: 8 lớp Add (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Add 8 0 0 501 501 2.69% |
| 10.1 | B: ReLU có Add: 51 lớp ConvRelu (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_layers.txt | ConvRelu 51 0 0 7391 7391 49.36% |
| 10.1 | B: ReLU có Add: 6 lớp ConvReluAdd (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_layers.txt | ConvReluAdd 6 0 0 711 711 4.75% |
| 10.1 | B: ReLU có Add: 2 lớp Add (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_layers.txt | Add 2 0 0 89 89 0.59% |
| 10.1 | B: SiLU không Add: 57 lớp ConvExSwish (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_noadd_CORE_0_layers.txt | ConvExSwish 57 0 0 13350 13350 60.33% |
| 10.1 | B: SiLU không Add: 2 lớp Add (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_noadd_CORE_0_layers.txt | Add 2 0 0 170 170 0.77% |
| 10.1 | B: ReLU không Add: 57 lớp ConvRelu (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_noadd_CORE_0_layers.txt | ConvRelu 57 0 0 10414 10414 53.54% |
| 10.1 | B: ReLU không Add: 2 lớp Add (bảng Operator Time Consuming Ranking, cột CallNumber) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_noadd_CORE_0_layers.txt | Add 2 0 0 169 169 0.87% |
| 10.1 | Điều kiện: độ trải (lớn nhất trừ nhỏ nhất) SiLU từ 0.173 đến 4.396 ms, ReLU từ 0.042 đến 0.307 ms (tính từ all_ms của summary.json và summary2.json, cột AUTO) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | (số học) |
| 10.1 | Gây nhiễu lượt 1: ReLU thấp hơn 28.9% (19.154 so 13.617 ms), hai thay đổi trộn lẫn | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | thí nghiệm này không tách được phần đóng góp của từng thay đổi |
| 10.1 | Lượt 1: ReLU thấp hơn SiLU 28.9% | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (thấp hơn 28.9%) |
| 10.1 | Lượt 2: silu_noadd so relu_noadd ở AUTO, ReLU thấp hơn 35.0% | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (ReLU thấp hơn 35.0%) |
| 10.1 | Lượt 2: cả hai biến thể noadd còn 2 Add đứng riêng | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Cả hai đều 113 lớp với 2 `Add` đứng riêng |
| 10.1 | Lượt 2: relu_opt3 so relu_noadd, ghép Add không đóng góp đo được | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | chênh lệch nằm trong độ trải |
| 10.1 | noadd: shortcut=False ở bốn khối C2f backbone | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | `shortcut=False` ở 4 khối C2f của backbone |
| 10.1 | optimization_level 1, 2, 3: bảng op giống nhau, độ trễ không khác biệt có ý nghĩa | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | độ trễ không khác biệt có ý nghĩa |
| 10.1 | Dao động giữa phiên: 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2, cùng file .rknn | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | ra 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2 |
| 10.1 | Trọng số ngẫu nhiên, chỉ đo cấu trúc, ánh xạ op và độ trễ, không đo accuracy | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Trọng số ngẫu nhiên: chỉ đo cấu trúc đồ thị, ánh xạ op và độ trễ, không đo accuracy |
| 10.1 | Điều kiện: RK3588S (Orange Pi 5) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Orange Pi 5 (RK3588S) |
| 10.1 | Điều kiện: rknn-toolkit2 2.3.2 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | PC `rknn-toolkit2` 2.3.2 |
| 10.1 | Điều kiện: eval_perf với fix_freq=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | eval_perf(fix_freq=True) |
| 10.1 | Điều kiện: 5 lần mỗi cột, lấy trung vị | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | 5 lần, lấy trung vị |
| 10.1 | Điều kiện: core_mask=AUTO | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | `core_mask=AUTO` |
| 10.1 | Điều kiện: YOLOv8n nc=5 640x640, INT8, khởi tạo ngẫu nhiên | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | khởi tạo ngẫu nhiên, INT8 (w8a8), calibration 40 ảnh |
| 10.1 | Dự đoán: luật fusion phần cứng Conv+Relu | T1 | UG232 tr.142 | Conv+Relu |
| 10.1 | Dự đoán: luật fusion phần cứng Conv+Sigmoid(Tanh/Elu/Silu...) | T1 | UG232 tr.142 | Conv+Sigmoid(Tanh/Elu/Silu...) |
| 10.1 | Dự đoán: luật fusion phần cứng Conv+Add | T1 | UG232 tr.142 | Conv+Add |
| 10.1 | Dự đoán: Non-Relu activation function là một trong ba loại op kém hiệu quả | T1 | UG232 tr.146 | Non-Relu activation function |
| 10.1 | Dự đoán: UG152 liệt kê op nhanh hơn khi nhiều core | T1 | UG152 tr.27 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. |
| 10.2 | Tổng thời gian bảng debug silu_opt3: 18606 us | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Total Operator Elapsed Per Frame Time(us): 18606 |
| 10.2 | A, silu_opt3: top 1 là lớp #102 exSoftmax13 model.22/dfl/Softmax, 2058 us, 11.1% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 102 exSoftmax13 INT8 NPU (4,16,1,8400),(1,16,1,1) (4,16,1,8400) 0/0/0 2058 |
| 10.2 | A, silu_opt3: top 2 là lớp #2 ConvExSwish model.0/conv/Conv, 1854 us, 10.0% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 2 ConvExSwish UINT8 NPU (1,3,640,640),(16,3,3,3),(16) (1,16,320,320) 121323/921600/921600 1854 |
| 10.2 | A, silu_opt3: top 3 là lớp #104 Transpose model.22/dfl/Reshape_1_output_…, 823 us, 4.4% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 104 Transpose INT8 CPU (4,1,1,8400) (1,4,1,8400) 0/0/0 823 |
| 10.2 | A, silu_opt3: top 4 là lớp #3 ConvExSwish model.1/conv/Conv, 522 us, 2.8% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 3 ConvExSwish INT8 NPU (1,16,320,320),(32,16,3,3),(32) (1,32,160,160) 104104/230400/230400 522 |
| 10.2 | A, silu_opt3: top 5 là lớp #10 ConvExSwish cv2/conv/Conv, 499 us, 2.7% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 10 ConvExSwish INT8 NPU (1,48,160,160),(32,48,1,1),(32) (1,32,160,160) 86658/102400/102400 499 |
| 10.2 | A, silu_opt3: top 6 là lớp #4 ConvExSwish cv1/conv/Conv, 472 us, 2.5% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 4 ConvExSwish INT8 NPU (1,32,160,160),(32,32,1,1),(32) (1,32,160,160) 69320/102400/102400 472 |
| 10.2 | A, silu_opt3: top 7 là lớp #7 ConvExSwish cv2/conv/Conv, 454 us, 2.4% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 7 ConvExSwish INT8 NPU (1,16,160,160),(16,16,3,3),(16) (1,16,160,160) 34741/230400/230400 454 |
| 10.2 | A, silu_opt3: top 8 là lớp #6 ConvExSwish cv1/conv/Conv, 453 us, 2.4% của 18606 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | 6 ConvExSwish INT8 NPU (1,16,160,160),(16,16,3,3),(16) (1,16,160,160) 34741/230400/230400 453 |
| 10.2 | Tổng thời gian bảng debug trained_silu_5c: 23598 us | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Total Operator Elapsed Per Frame Time(us): 23598 |
| 10.2 | A, trained_silu_5c: top 1 là lớp #102 exSoftmax13 model.22/dfl/Softmax, 2104 us, 8.9% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 102 exSoftmax13 INT8 NPU (4,16,1,8400),(1,16,1,1) (4,16,1,8400) 0/0/0 2104 |
| 10.2 | A, trained_silu_5c: top 2 là lớp #2 ConvExSwish model.0/conv/Conv, 1947 us, 8.3% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 2 ConvExSwish UINT8 NPU (1,3,640,640),(16,3,3,3),(16) (1,16,320,320) 121323/921600/921600 1947 |
| 10.2 | A, trained_silu_5c: top 3 là lớp #104 Transpose model.22/dfl/Reshape_1_output_…, 804 us, 3.4% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 104 Transpose INT8 CPU (4,1,1,8400) (1,4,1,8400) 0/0/0 804 |
| 10.2 | A, trained_silu_5c: top 4 là lớp #3 ConvExSwish model.1/conv/Conv, 567 us, 2.4% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 3 ConvExSwish INT8 NPU (1,16,320,320),(32,16,3,3),(32) (1,32,160,160) 104104/230400/230400 567 |
| 10.2 | A, trained_silu_5c: top 5 là lớp #10 ConvExSwish cv2/conv/Conv, 540 us, 2.3% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 10 ConvExSwish INT8 NPU (1,48,160,160),(32,48,1,1),(32) (1,32,160,160) 86658/102400/102400 540 |
| 10.2 | A, trained_silu_5c: top 6 là lớp #4 ConvExSwish cv1/conv/Conv, 512 us, 2.2% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 4 ConvExSwish INT8 NPU (1,32,160,160),(32,32,1,1),(32) (1,32,160,160) 69320/102400/102400 512 |
| 10.2 | A, trained_silu_5c: top 7 là lớp #6 ConvExSwish cv1/conv/Conv, 493 us, 2.1% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 6 ConvExSwish INT8 NPU (1,16,160,160),(16,16,3,3),(16) (1,16,160,160) 34741/230400/230400 493 |
| 10.2 | A, trained_silu_5c: top 8 là lớp #7 ConvExSwish cv2/conv/Conv, 493 us, 2.1% của 23598 (phép tính của bộ hình) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | 7 ConvExSwish INT8 NPU (1,16,160,160),(16,16,3,3),(16) (1,16,160,160) 34741/230400/230400 493 |
| 10.2 | Tổng thời gian bảng debug YOLO26n: 28146 us | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Total Operator Elapsed Per Frame Time(us): 28146 |
| 10.2 | A, YOLO26n: top 1 là lớp #2 ConvExSwish model.0/conv/Conv, 1924 us, 6.8% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 2 ConvExSwish UINT8 NPU (1,3,640,640),(16,3,3,3),(16) (1,16,320,320) 121323/921600/921600 1924 |
| 10.2 | A, YOLO26n: top 2 là lớp #63 exSDPAttention m.0/attn/MatMul_1#1_2sdpa, 1230 us, 4.4% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 63 exSDPAttention INT8 NPU (2,32,1,400),(2,32,1,400),... (2,64,1,400) 0/0/0 1230 |
| 10.2 | A, YOLO26n: top 3 là lớp #148 exSDPAttention m.0.1/attn/MatMul_1#1_2sdpa, 1225 us, 4.4% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 148 exSDPAttention INT8 NPU (2,32,1,400),(2,32,1,400),... (2,64,1,400) 0/0/0 1225 |
| 10.2 | A, YOLO26n: top 4 là lớp #10 ConvExSwish cv2/conv/Conv, 951 us, 3.4% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 10 ConvExSwish INT8 NPU (1,48,160,160),(64,48,1,1),(64) (1,64,160,160) 121366/204800/204800 951 |
| 10.2 | A, YOLO26n: top 5 là lớp #3 ConvExSwish model.1/conv/Conv, 563 us, 2.0% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 3 ConvExSwish INT8 NPU (1,16,320,320),(32,16,3,3),(32) (1,32,160,160) 104104/230400/230400 563 |
| 10.2 | A, YOLO26n: top 6 là lớp #4 ConvExSwish cv1/conv/Conv, 513 us, 1.8% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 4 ConvExSwish INT8 NPU (1,32,160,160),(32,32,1,1),(32) (1,32,160,160) 69320/102400/102400 513 |
| 10.2 | A, YOLO26n: top 7 là lớp #18 ConvExSwish cv2/conv/Conv, 501 us, 1.8% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 18 ConvExSwish INT8 NPU (1,96,80,80),(128,96,1,1),(128) (1,128,80,80) 61170/102400/102400 501 |
| 10.2 | A, YOLO26n: top 8 là lớp #6 ConvExSwish cv1/conv/Conv, 493 us, 1.8% của 28146 (phép tính của bộ hình) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | 6 ConvExSwish INT8 NPU (1,16,160,160),(8,16,3,3),(8) (1,8,160,160) 34693/230400/230400 493 |
| 10.2 | B, silu_opt3: ConvExSwish 59.63% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | ConvExSwish 57 0 0 11095 11095 59.63% |
| 10.2 | B, silu_opt3: Concat 8.92% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Concat 17 0 0 1659 1659 8.92% |
| 10.2 | B, silu_opt3: exSoftmax13 11.06% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | exSoftmax13 1 0 0 2058 2058 11.06% |
| 10.2 | B, silu_opt3: Transpose 4.42% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Transpose 1 823 0 0 823 4.42% |
| 10.2 | B, silu_opt3: Split 3.79% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Split 9 0 0 705 705 3.79% |
| 10.2 | B, silu_opt3: Conv 3.05% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Conv 7 0 0 568 568 3.05% |
| 10.2 | B, trained_silu_5c: ConvExSwish 57.63% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | ConvExSwish 57 0 0 13600 13600 57.63% |
| 10.2 | B, trained_silu_5c: Concat 9.91% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Concat 17 0 0 2338 2338 9.91% |
| 10.2 | B, trained_silu_5c: exSoftmax13 8.92% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | exSoftmax13 1 0 0 2104 2104 8.92% |
| 10.2 | B, trained_silu_5c: Transpose 3.41% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Transpose 1 804 0 0 804 3.41% |
| 10.2 | B, trained_silu_5c: Split 4.62% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Split 9 0 0 1091 1091 4.62% |
| 10.2 | B, trained_silu_5c: Conv 4.46% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Conv 7 0 0 1053 1053 4.46% |
| 10.2 | B, trained_silu_5c: Add 3.49% (cột TimeRatio) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | Add 8 0 0 823 823 3.49% |
| 10.2 | B, YOLO26n: ConvExSwish 60.73% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | ConvExSwish 87 0 0 17094 17094 60.73% |
| 10.2 | B, YOLO26n: Concat 9.53% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Concat 23 0 0 2681 2681 9.53% |
| 10.2 | B, YOLO26n: exSDPAttention 8.72% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | exSDPAttention 2 0 0 2455 2455 8.72% |
| 10.2 | B, YOLO26n: Split 4.33% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Split 12 0 0 1219 1219 4.33% |
| 10.2 | B, YOLO26n: Conv 3.24% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Conv 11 0 0 912 912 3.24% |
| 10.2 | B, YOLO26n: Add 4.92% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Add 18 0 0 1384 1384 4.92% |
| 10.2 | B, YOLO26n: Reshape 3.74% (cột TimeRatio) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Reshape 13 0 0 1052 1052 3.74% |
| 10.2 | B: phần khác = 100 trừ tổng các loại op đã vẽ (phép tính của bộ hình) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | (số học) |
| 10.2 | Cảnh báo in bởi eval_perf: kết quả chỉ để debug, có thể tệ hơn thực tế | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | Warning: The performance result is just for debugging, may worse than actual performance! |
| 10.2 | Chế độ debug có thể lớn hơn thực tế | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | thời gian ở chế độ debug có thể lớn hơn thực tế |
| 10.2 | Tổng bảng debug đổi theo lượt chạy: lệch giữa 18606 và 23598 us (phép tính của bộ hình) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_AUTO_layers.txt | (số học) |
| 10.2 | Bảng lớp từ một lần eval_perf với perf_debug=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | một lần `perf_debug=True` để đọc cột WorkLoad |
| 10.2 | YOLO26n: bảng lớp (perf_debug=True) lấy một lần ở phiên 1 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Bảng lớp (`perf_debug=True`) lấy một lần ở phiên 1 |
| 10.2 | Điều kiện: RK3588S, toolkit 2.3.2, fix_freq=True, INT8 640x640 nc=5 (YOLOv8n) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | eval_perf(fix_freq=True) |
| 10.2 | YOLO26n: eval_perf(fix_freq=True), nc=5, INT8 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | `eval_perf(fix_freq=True)` |
| 10.2 | YOLOv8n khởi tạo ngẫu nhiên và best.pt đã huấn luyện (trained_silu_5c) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (YOLOv8n 5 lớp, SiLU, đã huấn luyện) |
| 10.2 | exSoftmax13 của YOLOv8n nằm trong đầu DFL (tên lớp) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | exSoftmax13:/model.22/dfl/Softmax |
| 10.2 | YOLO26n có hai lớp exSDPAttention | T3 | LOG 2026-10-10_yolo-phaseA/README.md | \| `exSDPAttention` \| 0 \| 2 |
| 10.2 | Dự đoán: NPU Cycles chỉ hiện cho Conv | T1 | UG232 tr.140 | Currently, the NPU Cycles column only displays the Cycles required by Conv |
| 10.2 | Dự đoán: ba loại op kém hiệu quả (data transfer, size transformation, non-Relu activation) | T1 | UG232 tr.146 | Try to reduce the following three types of operators in the model |
| 10.2 | Dự đoán: perf_debug=True thêm mã debug, có thể tắt cơ chế song song, nên thời gian dài hơn | T1 | UG232 tr.177 | some parallel mechanisms may be disabled |
| 10.3 | A: silu_opt3 AUTO: trung vị 22.021 ms, nhỏ nhất 20.622, lớn nhất 22.253 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|AUTO": { "ms": 22.021, "all_ms": [ 20.622, 22.253, 22.145, 21.922, 22.021 ] |
| 10.3 | A: silu_opt3 CORE_0: trung vị 20.019 ms, nhỏ nhất 18.17, lớn nhất 22.257 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|CORE_0": { "ms": 20.019, "all_ms": [ 18.17, 22.257, 19.367, 20.019, 22.113 ] |
| 10.3 | A: silu_opt3 CORE_0_1_2: trung vị 19.745 ms, nhỏ nhất 17.671, lớn nhất 22.578 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|CORE_0_1_2": { "ms": 19.745, "all_ms": [ 17.671, 22.578, 22.363, 18.624, 19.745 ] |
| 10.3 | A: silu_noadd AUTO: trung vị 21.431 ms, nhỏ nhất 18.638, lớn nhất 21.779 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_noadd\|AUTO": { "ms": 21.431, "all_ms": [ 20.025, 21.431, 21.779, 21.766, 18.638 ] |
| 10.3 | A: silu_noadd CORE_0: trung vị 20.14 ms, nhỏ nhất 19.517, lớn nhất 21.718 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_noadd\|CORE_0": { "ms": 20.14, "all_ms": [ 20.1, 21.476, 21.718, 20.14, 19.517 ] |
| 10.3 | A: silu_noadd CORE_0_1_2: trung vị 21.025 ms, nhỏ nhất 18.093, lớn nhất 22.018 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_noadd\|CORE_0_1_2": { "ms": 21.025, "all_ms": [ 18.093, 19.388, 21.025, 21.688, 22.018 ] |
| 10.3 | A: relu_opt3 AUTO: trung vị 13.963 ms, nhỏ nhất 13.934, lớn nhất 13.976 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_opt3\|AUTO": { "ms": 13.963, "all_ms": [ 13.934, 13.942, 13.967, 13.976, 13.963 ] |
| 10.3 | A: relu_opt3 CORE_0: trung vị 13.969 ms, nhỏ nhất 13.91, lớn nhất 14.114 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_opt3\|CORE_0": { "ms": 13.969, "all_ms": [ 13.91, 14.114, 13.969, 13.949, 13.969 ] |
| 10.3 | A: relu_opt3 CORE_0_1_2: trung vị 12.854 ms, nhỏ nhất 11.301, lớn nhất 13.394 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_opt3\|CORE_0_1_2": { "ms": 12.854, "all_ms": [ 12.418, 11.301, 13.394, 12.854, 13.229 ] |
| 10.3 | A: relu_noadd AUTO: trung vị 13.929 ms, nhỏ nhất 13.787, lớn nhất 14.094 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_noadd\|AUTO": { "ms": 13.929, "all_ms": [ 13.787, 14.094, 13.929, 13.914, 13.941 ] |
| 10.3 | A: relu_noadd CORE_0: trung vị 13.955 ms, nhỏ nhất 13.898, lớn nhất 14.12 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_noadd\|CORE_0": { "ms": 13.955, "all_ms": [ 13.968, 13.949, 14.12, 13.898, 13.955 ] |
| 10.3 | A: relu_noadd CORE_0_1_2: trung vị 12.801 ms, nhỏ nhất 12.205, lớn nhất 13.311 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "relu_noadd\|CORE_0_1_2": { "ms": 12.801, "all_ms": [ 12.205, 12.801, 13.113, 12.694, 13.311 ] |
| 10.3 | A: trained_silu_5c AUTO: trung vị 21.936 ms, nhỏ nhất 18.175, lớn nhất 22.312 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary3.json | "trained_silu_5c\|AUTO": { "ms": 21.936, "all_ms": [ 18.175, 22.207, 19.831, 21.936, 22.312 ] |
| 10.3 | A: trained_silu_5c CORE_0: trung vị 19.225 ms, nhỏ nhất 18.836, lớn nhất 20.287 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary3.json | "trained_silu_5c\|CORE_0": { "ms": 19.225, "all_ms": [ 20.287, 19.203, 18.836, 19.225, 19.33 ] |
| 10.3 | A: trained_silu_5c CORE_0_1_2: trung vị 18.024 ms, nhỏ nhất 17.607, lớn nhất 19.021 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary3.json | "trained_silu_5c\|CORE_0_1_2": { "ms": 18.024, "all_ms": [ 17.695, 17.607, 18.847, 19.021, 18.024 ] |
| 10.3 | A: silu_opt3 AUTO ở lượt 1 là 19.154 ms (đường đứt) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "silu_opt3": { "npu_latency_ms": 19.154, |
| 10.3 | B: ví dụ một dòng bảng lớp ConvExSwish, cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | ConvExSwish UINT8 NPU (1,3,640,640),(16,3,3,3),(16) (1,16,320,320) 121323/921600/921600 1948 0.74/0.74/0.74 100.0%/0.0%/0.0% 1202 Conv:/model.0/conv/Conv |
| 10.3 | B: ví dụ một dòng bảng lớp Add, cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Add INT8 NPU (1,16,160,160),(1,16,160,160) (1,16,160,160) 0/0/0 108 33.7%/33.1%/33.1% 800 Add:/model.2/m.0/Add |
| 10.3 | B: ví dụ một dòng bảng lớp Concat, cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | Concat INT8 NPU (1,16,160,160),(1,16,160,160),... (1,48,160,160) 0/0/0 161 33.7%/33.1%/33.1% 1200 Concat:/model.2/Concat |
| 10.3 | B: ví dụ một dòng bảng lớp ConvRelu, cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvRelu UINT8 NPU (1,3,640,640),(16,3,3,3),(16) (1,16,320,320) 121323/921600/921600 496 2.90/2.90/2.90 33.4%/33.4%/33.1% 1202 Conv:/model.0/conv/Conv |
| 10.3 | B: ví dụ một dòng bảng lớp ConvReluAdd, cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/relu_opt3_CORE_0_1_2_layers.txt | ConvReluAdd INT8 NPU (1,16,160,160),(16,16,3,3),(16),... (1,16,160,160) 52058/230400/230400 163 11.78/11.78/11.78 33.7%/33.1%/33.1% 802 Conv:/model.2/m.0/cv2/conv/Conv |
| 10.3 | B: ConvExSwish: 57 lớp, 0 lớp chia, trung bình 100%/0%/0%; Add: 8 lớp, 8 lớp chia, trung bình 34%/33%/32%; Concat: 17 lớp, 15 lớp chia, trung bình 42%/30%/28%; ConvRelu: 51 lớp, 51 lớp chia, trung bình 35%/34%/32%; ConvReluAdd: 6 lớp, 6 lớp chia, trung bình 34%/33%/32% (trung bình cột WorkLoad do gen.py tính) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | (số học) |
| 10.3 | B: tiêu đề cột WorkLoad(0/1/2) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt | WorkLoad(0/1/2) |
| 10.3 | Điều kiện: Orange Pi 5 (RK3588S) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Orange Pi 5 (RK3588S) |
| 10.3 | Điều kiện: rknn-toolkit2 2.3.2 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | PC `rknn-toolkit2` 2.3.2 |
| 10.3 | Điều kiện: eval_perf với fix_freq=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | eval_perf(fix_freq=True) |
| 10.3 | Điều kiện: YOLOv8n nc=5 640x640, trọng số ngẫu nhiên, INT8, calibration 40 ảnh | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | khởi tạo ngẫu nhiên, INT8 (w8a8), calibration 40 ảnh |
| 10.3 | Điều kiện: 5 lần, lấy trung vị | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | 5 lần, lấy trung vị |
| 10.3 | Điều kiện: bảng lớp từ một lần eval_perf với perf_debug=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | một lần `perf_debug=True` để đọc cột WorkLoad |
| 10.3 | Điều kiện: thời gian ở chế độ debug có thể lớn hơn thực tế | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | thời gian ở chế độ debug có thể lớn hơn thực tế |
| 10.3 | trained_silu_5c là best.pt đã huấn luyện, SiLU | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (YOLOv8n 5 lớp, SiLU, đã huấn luyện) |
| 10.3 | trained_silu_5c: calibration 40 ảnh | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | calibration 40 ảnh letterbox từ `data/` |
| 10.3 | Dao động giữa phiên: 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | ra 19.154 ms ở lượt 1 và 22.021 ms ở lượt 2 |
| 10.3 | silu_noadd, relu_noadd: shortcut=False ở bốn khối C2f backbone | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | `shortcut=False` ở 4 khối C2f của backbone |
| 10.3 | Cả 57 lớp ConvExSwish chạy 100%/0%/0% | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | cả 57 lớp `ConvExSwish` đều `100%/0%/0%` |
| 10.3 | 51 ConvRelu và 6 ConvReluAdd chia ba core | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | cả 51 `ConvRelu` và 6 `ConvReluAdd` được chia ba lõi |
| 10.3 | Add và 15 trong 17 Concat chia ba core | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | và 15 trong 17 `Concat` được chia ba lõi |
| 10.3 | ReLU nhanh hơn CORE_0 khoảng 8% khi dùng 3 core | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | nhanh hơn `CORE_0` khoảng 8% |
| 10.3 | SiLU: không có khác biệt ngoài độ trải | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | không có khác biệt ngoài độ trải |
| 10.3 | Giá trị lớn nhất của ReLU nhỏ hơn giá trị nhỏ nhất của SiLU | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Giá trị lớn nhất của ReLU (14.120) vẫn nhỏ hơn giá trị nhỏ nhất của SiLU (17.671) ở mọi `core_mask` |
| 10.3 | Mức giảm khoảng 6% của model đã huấn luyện nhỏ hơn độ trải giữa các phiên | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | nhỏ hơn độ trải giữa các phiên của SiLU |
| 10.3 | Lượt 2 của silu_opt3 AUTO lệch lượt 1 khoảng 2.9 ms | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | lệch nhau 2.9 ms |
| 10.3 | Phần trăm 12.854 so với 13.969 là mức giảm khoảng 8% (tính từ hai trung vị trên) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | (số học) |
| 10.3 | 19.225 xuống 18.024 là mức giảm khoảng 6% (tính từ hai trung vị trên) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/summary3.json | (số học) |
| 10.3 | Một kiến trúc, trọng số ngẫu nhiên; chưa có bản ReLU đã huấn luyện | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Chỉ một kiến trúc, trọng số ngẫu nhiên, đầu vào 640x640 |
| 10.3 | Chưa có bản ReLU đã huấn luyện | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Không có bản ReLU đã huấn luyện |
| 10.3 | UG152: op nhanh hơn khi nhiều core | T1 | UG152 tr.27 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. |
| 10.3 | OPL 3.2.17 ConvolutionSwish: không hỗ trợ ghép nhiều core | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish Convolution 与 Swish 融合计算, Output = Swish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 10.4 | B và A: AUTO: trung vị 15 giá trị YOLO26n 22.26, YOLOv8n 19.399, chênh lệch 2.861, U 200.0, p 0.00031, CI 1.5 đến 4.498 | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | AUTO 15 15 22.26 19.399 2.861 200.0 0.00031 1.5 4.498 |
| 10.4 | C: AUTO: trung vị mỗi phiên YOLO26n [23.65, 22.26, 22.237], YOLOv8n [19.399, 21.66, 19.152] | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | [23.65, 22.26, 22.237] [19.399, 21.66, 19.152] |
| 10.4 | B và A: CORE_0: trung vị 15 giá trị YOLO26n 21.701, YOLOv8n 19.163, chênh lệch 2.538, U 186.0, p 0.00246, CI 1.295 đến 2.883 | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | CORE_0 15 15 21.701 19.163 2.538 186.0 0.00246 1.295 2.883 |
| 10.4 | C: CORE_0: trung vị mỗi phiên YOLO26n [21.11, 22.262, 21.521], YOLOv8n [21.848, 19.157, 19.064] | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | [21.11, 22.262, 21.521] [21.848, 19.157, 19.064] |
| 10.4 | B và A: CORE_0_1_2: trung vị 15 giá trị YOLO26n 22.09, YOLOv8n 18.985, chênh lệch 3.105, U 188.0, p 0.00187, CI 1.197 đến 5.363 | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | CORE_0_1_2 15 15 22.09 18.985 3.105 188.0 0.00187 1.197 5.363 |
| 10.4 | C: CORE_0_1_2: trung vị mỗi phiên YOLO26n [21.558, 23.311, 22.09], YOLOv8n [19.44, 19.325, 17.634] | T3 | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | [21.558, 23.311, 22.09] [19.44, 19.325, 17.634] |
| 10.4 | A: phiên 1, yolov8n, AUTO: 5 lần [17.796, 19.399, 19.68, 19.593, 19.237] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolov8n", "mask": "AUTO", "ms": 19.399, "all_ms": [ 17.796, 19.399, 19.68, 19.593, 19.237 ] |
| 10.4 | A: phiên 1, yolov8n, CORE_0: 5 lần [20.423, 22.15, 19.554, 21.848, 22.523] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolov8n", "mask": "CORE_0", "ms": 21.848, "all_ms": [ 20.423, 22.15, 19.554, 21.848, 22.523 ] |
| 10.4 | A: phiên 1, yolov8n, CORE_0_1_2: 5 lần [19.184, 19.44, 22.725, 18.564, 22.407] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolov8n", "mask": "CORE_0_1_2", "ms": 19.44, "all_ms": [ 19.184, 19.44, 22.725, 18.564, 22.407 ] |
| 10.4 | A: phiên 1, yolo26n, AUTO: 5 lần [20.777, 23.65, 25.503, 21.868, 25.446] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolo26n", "mask": "AUTO", "ms": 23.65, "all_ms": [ 20.777, 23.65, 25.503, 21.868, 25.446 ] |
| 10.4 | A: phiên 1, yolo26n, CORE_0: 5 lần [20.332, 20.849, 21.701, 21.11, 21.874] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolo26n", "mask": "CORE_0", "ms": 21.11, "all_ms": [ 20.332, 20.849, 21.701, 21.11, 21.874 ] |
| 10.4 | A: phiên 1, yolo26n, CORE_0_1_2: 5 lần [20.767, 21.558, 21.326, 22.997, 26.35] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 1, "model": "yolo26n", "mask": "CORE_0_1_2", "ms": 21.558, "all_ms": [ 20.767, 21.558, 21.326, 22.997, 26.35 ] |
| 10.4 | A: phiên 2, yolo26n, AUTO: 5 lần [21.873, 22.26, 22.266, 22.241, 22.276] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolo26n", "mask": "AUTO", "ms": 22.26, "all_ms": [ 21.873, 22.26, 22.266, 22.241, 22.276 ] |
| 10.4 | A: phiên 2, yolo26n, CORE_0: 5 lần [19.188, 22.262, 22.264, 22.38, 22.188] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolo26n", "mask": "CORE_0", "ms": 22.262, "all_ms": [ 19.188, 22.262, 22.264, 22.38, 22.188 ] |
| 10.4 | A: phiên 2, yolo26n, CORE_0_1_2: 5 lần [20.611, 23.311, 23.319, 18.695, 23.314] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolo26n", "mask": "CORE_0_1_2", "ms": 23.311, "all_ms": [ 20.611, 23.311, 23.319, 18.695, 23.314 ] |
| 10.4 | A: phiên 2, yolov8n, AUTO: 5 lần [21.072, 22.883, 20.084, 21.66, 22.456] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolov8n", "mask": "AUTO", "ms": 21.66, "all_ms": [ 21.072, 22.883, 20.084, 21.66, 22.456 ] |
| 10.4 | A: phiên 2, yolov8n, CORE_0: 5 lần [17.356, 19.157, 19.142, 19.163, 19.158] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolov8n", "mask": "CORE_0", "ms": 19.157, "all_ms": [ 17.356, 19.157, 19.142, 19.163, 19.158 ] |
| 10.4 | A: phiên 2, yolov8n, CORE_0_1_2: 5 lần [17.708, 23.129, 22.114, 19.325, 16.597] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 2, "model": "yolov8n", "mask": "CORE_0_1_2", "ms": 19.325, "all_ms": [ 17.708, 23.129, 22.114, 19.325, 16.597 ] |
| 10.4 | A: phiên 3, yolov8n, AUTO: 5 lần [17.319, 19.152, 19.14, 19.166, 19.367] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolov8n", "mask": "AUTO", "ms": 19.152, "all_ms": [ 17.319, 19.152, 19.14, 19.166, 19.367 ] |
| 10.4 | A: phiên 3, yolov8n, CORE_0: 5 lần [18.81, 19.69, 19.064, 18.815, 19.637] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolov8n", "mask": "CORE_0", "ms": 19.064, "all_ms": [ 18.81, 19.69, 19.064, 18.815, 19.637 ] |
| 10.4 | A: phiên 3, yolov8n, CORE_0_1_2: 5 lần [17.499, 18.985, 17.634, 18.284, 17.63] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolov8n", "mask": "CORE_0_1_2", "ms": 17.634, "all_ms": [ 17.499, 18.985, 17.634, 18.284, 17.63 ] |
| 10.4 | A: phiên 3, yolo26n, AUTO: 5 lần [20.162, 21.592, 22.237, 24.737, 25.781] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolo26n", "mask": "AUTO", "ms": 22.237, "all_ms": [ 20.162, 21.592, 22.237, 24.737, 25.781 ] |
| 10.4 | A: phiên 3, yolo26n, CORE_0: 5 lần [20.531, 22.04, 21.128, 21.859, 21.521] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolo26n", "mask": "CORE_0", "ms": 21.521, "all_ms": [ 20.531, 22.04, 21.128, 21.859, 21.521 ] |
| 10.4 | A: phiên 3, yolo26n, CORE_0_1_2: 5 lần [20.591, 22.09, 26.367, 27.248, 21.907] | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "session": 3, "model": "yolo26n", "mask": "CORE_0_1_2", "ms": 22.09, "all_ms": [ 20.591, 22.09, 26.367, 27.248, 21.907 ] |
| 10.4 | Nhiệt độ soc-thermal và npu-thermal tối đa 46.2 độ C (tính từ trường before, after của 18 nhóm đo) | tính | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | (số học) |
| 10.4 | Nhiệt độ tối đa 46.2 độ C | T3 | LOG 2026-10-10_yolo-phaseA/README.md | tối đa 46.2 độ C |
| 10.4 | NPU 1000000000 Hz ở cả 18 nhóm đo | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "NPU": [ 1000000000 ] |
| 10.4 | DDR 2112000000 Hz ở cả 18 nhóm đo | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json | "DDR": [ 2112000000 ] |
| 10.4 | NPU và DDR đọc từ đầu ra eval_perf của 18 nhóm đo | T3 | LOG 2026-10-10_yolo-phaseA/README.md | ở cả 18 nhóm đo |
| 10.4 | Thiết kế: 3 phiên cách nhau 180 giây, thứ tự model xen kẽ | T3 | LOG 2026-10-10_yolo-phaseA/README.md | 3 phiên cách nhau 180 giây; thứ tự model xen kẽ |
| 10.4 | Thứ tự trong từng phiên: v8n rồi 26n, 26n rồi v8n, v8n rồi 26n | T3 | LOG 2026-10-10_yolo-phaseA/README.md | (v8n rồi 26n, 26n rồi v8n, v8n rồi 26n) |
| 10.4 | Mỗi phiên 3 core_mask; mỗi nhóm 5 lần eval_perf lấy trung vị | T3 | LOG 2026-10-10_yolo-phaseA/README.md | mỗi (model, mask, phiên) là 5 lần `eval_perf` lấy trung vị |
| 10.4 | Model: nc=5, trọng số ngẫu nhiên, xuất bằng ultralytics export(format="rknn"), opset 19, onnxslim, INT8 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | opset 19, `onnxslim` |
| 10.4 | Calibration 40 ảnh | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Calibration 40 ảnh letterbox |
| 10.4 | Bootstrap 10000 lần, seed 42 | T3 | LOG 2026-10-10_yolo-phaseA/stats_latency.py | 10000 resamples, seed 42 |
| 10.4 | 15 giá trị không độc lập, p lạc quan | T3 | LOG 2026-10-10_yolo-phaseA/README.md | 15 giá trị không độc lập nên p lạc quan |
| 10.4 | Ở mức phiên chỉ có 3 so 3 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | ở mức phiên chỉ có 3 so 3 |
| 10.4 | YOLO26n chậm hơn ở 8 trong 9 cặp (phiên, mask); cặp còn lại là CORE_0, phiên 1 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Trong 9 cặp (phiên, mask), YOLO26n chậm hơn ở 8 cặp |
| 10.4 | Đếm 8 trên 9 cặp tính từ trung vị mỗi phiên (phép tính của bộ hình) | tính | LOG 2026-10-10_yolo-phaseA/out/stats_latency.txt | (số học) |
| 10.4 | YOLO26n chậm hơn khoảng 13 đến 16%, dù ít FLOPs hơn khoảng 34% | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Chậm hơn khoảng 13 đến 16% theo trung vị của 15 giá trị |
| 10.4 | YOLO26n ít FLOPs hơn khoảng 34% | T3 | LOG 2026-10-10_yolo-phaseA/README.md | dù ít FLOPs hơn khoảng 34% |
| 10.4 | Không dùng số đo ngẫu nhiên để chọn model (trọng số ngẫu nhiên là phép đo cấu trúc) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | không dùng chúng để chọn model |
| 10.4 | Dự đoán: hiệu năng của convolution chịu ảnh hưởng của sức tính và băng thông | T1 | UG232 tr.146 | Since the performance of convolution will be affected by both computing power and bandwidth |
| 10.4 | Dự đoán: ba loại op kém hiệu quả | T1 | UG232 tr.146 | Try to reduce the following three types of operators in the model |
| 10.5 | C: YOLOv8n (SiLU): test mAP50-95 0.5908 (FP32, best.pt, protocol v1, tập test) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_baseline_100ep_s42,yolov8n_baseline,100,42,sfchd_test,v1,0.9048,0.8394,0.8924,0.5908 |
| 10.5 | A: YOLOv8n (SiLU): cột metrics/mAP50-95(B) của metrics.csv, mỗi epoch một dòng | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/metrics.csv | metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B) |
| 10.5 | A, A', C: YOLOv8n (SiLU): epoch 100, val mAP50-95 0.59611 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/metrics.csv | 100,8383.11,0.86747,0.39672,0.90139,0.85594,0.86536,0.88452,0.59611 |
| 10.5 | Điều kiện: YOLOv8n (SiLU): batch 16 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/args.yaml | batch: 16 |
| 10.5 | C: YOLOv8s: test mAP50-95 0.6152 (FP32, best.pt, protocol v1, tập test) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8s_baseline_100ep_s42,yolov8s_baseline,100,42,sfchd_test,v1,0.9001,0.8422,0.9035,0.6152 |
| 10.5 | A: YOLOv8s: cột metrics/mAP50-95(B) của metrics.csv, mỗi epoch một dòng | T3 | RUN sfchd_5class_yolov8s_baseline_100ep_s42/metrics.csv | metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B) |
| 10.5 | A, A', C: YOLOv8s: epoch 100, val mAP50-95 0.61877 | T3 | RUN sfchd_5class_yolov8s_baseline_100ep_s42/metrics.csv | 100,17027.1,0.74121,0.3407,0.86035,0.91288,0.88134,0.90585,0.61877 |
| 10.5 | Điều kiện: YOLOv8s: batch 8 | T3 | RUN sfchd_5class_yolov8s_baseline_100ep_s42/args.yaml | batch: 8 |
| 10.5 | C: YOLO26n: test mAP50-95 0.5883 (FP32, best.pt, protocol v1, tập test) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolo26n_baseline_100ep_s42,yolo26n_baseline,100,42,sfchd_test,v1,0.8843,0.8477,0.8865,0.5883 |
| 10.5 | A: YOLO26n: cột metrics/mAP50-95(B) của metrics.csv, mỗi epoch một dòng | T3 | RUN sfchd_5class_yolo26n_baseline_100ep_s42/metrics.csv | metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B) |
| 10.5 | A, A', C: YOLO26n: epoch 100, val mAP50-95 0.59326 | T3 | RUN sfchd_5class_yolo26n_baseline_100ep_s42/metrics.csv | 100,10045.6,1.0562,0.38216,0.00251,0.91484,0.84263,0.88445,0.59326 |
| 10.5 | Điều kiện: YOLO26n: batch 16 | T3 | RUN sfchd_5class_yolo26n_baseline_100ep_s42/args.yaml | batch: 16 |
| 10.5 | C: YOLOv8n ReLU (khởi tạo từ SiLU): test mAP50-95 0.5835 (FP32, best.pt, protocol v1, tập test) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_relu_100ep_s42,yolov8n_relu,100,42,sfchd_test,v1,0.9218,0.8394,0.8845,0.5835 |
| 10.5 | A: YOLOv8n ReLU (khởi tạo từ SiLU): cột metrics/mAP50-95(B) của metrics.csv, mỗi epoch một dòng | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/metrics.csv | metrics/precision(B),metrics/recall(B),metrics/mAP50(B),metrics/mAP50-95(B) |
| 10.5 | A, A', C: YOLOv8n ReLU (khởi tạo từ SiLU): epoch 100, val mAP50-95 0.58564 | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/metrics.csv | 100,7949.79,0.92919,0.43369,0.92299,0.90251,0.83445,0.87687,0.58564 |
| 10.5 | Điều kiện: YOLOv8n ReLU (khởi tạo từ SiLU): batch 16 | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/args.yaml | batch: 16 |
| 10.5 | Điều kiện: seed 42 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/args.yaml | seed: 42 |
| 10.5 | Điều kiện: 100 epoch | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/args.yaml | epochs: 100 |
| 10.5 | Điều kiện: optimizer MuSGD | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/args.yaml | optimizer: MuSGD |
| 10.5 | Điều kiện: dataset_fingerprint 02bd631c7238 (cột dataset_fingerprint của leaderboard) | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_test,v1,0.9048,0.8394,0.8924,0.5908,0.7186,0.621,0.3884,0.6494,0.5764,02bd631c7238 |
| 10.5 | Điều kiện: dữ liệu sfchd_5class, tập val và tập test là hai tập riêng | T3 | REPO data/sfchd_5class/processed/dataset.yaml | val: images/val test: images/test |
| 10.5 | Điều kiện: yolov8n_baseline: log train ghi Transferred 322/355 items | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/logs/train_20260927-021114.log | Transferred 322/355 items from pretrained weights |
| 10.5 | Điều kiện: yolov8n_relu: log train ghi Transferred 322/355 items | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/logs/train_20261011-030722.log | Transferred 322/355 items from pretrained weights |
| 10.5 | YOLOv8n ReLU: khởi tạo từ yolov8n.pt (trường pretrained của args.yaml) | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/args.yaml | pretrained: yolov8n.pt |
| 10.5 | YOLOv8n ReLU khởi tạo từ yolov8n.pt SiLU rồi fine-tune | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | khởi tạo từ `yolov8n.pt` SiLU rồi fine-tune |
| 10.5 | Nhận định "AP này có thể thấp hơn AP của ReLU train từ đầu" là của bộ hình, chưa kiểm bằng thí nghiệm | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | (unknown) |
| 10.5 | Chỉ có seed 42 nên chưa biết nhiễu giữa các seed | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Chỉ có seed 42, nên chưa biết nhiễu giữa các seed |
| 10.5 | Số leaderboard từ evaluator protocol v1, không từ model.val() | T1 | REPO ai/automation/run.py:125-126 | Leaderboard numbers come from the protocol v1 evaluator, not from model.val() |
| 10.5 | Số leaderboard dùng weights/best.pt | T1 | REPO ai/automation/run.py:129 | run_dir / "weights" / "best.pt" |
| 10.5 | Chênh lệch giữa ba model nano 0.0073 (phép tính từ leaderboard) | tính | REPO ai/automation/leaderboards/sfchd_5class.csv | (số học) |
| 10.5 | Dự đoán: Y6, Conv SiLU tốt nhất về accuracy | T2 | Y6 tr.8 | Conv with SiLU performs the best in accuracy |
| 10.5 | Dự đoán: Y6 Table 4, Conv SiLU 36.6% AP | T2 | Y6 tr.9 | Conv SiLU 36.6% 963 |
| 10.5 | Dự đoán: Y6 Table 4, Conv ReLU 34.8% AP | T2 | Y6 tr.9 | Conv ReLU 34.8% 1246 |
| 10.6 | Hàng 1 (đối chứng): ta đưa vào jpg 64x64 (đúng kích thước model), đọc được -100 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | jpg 64x64 (đúng kích thước model) \| -100 / 0 |
| 10.6 | Hàng 1 (đối chứng): suy ra: Dải nguyên bản | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Dải nguyên bản |
| 10.6 | Hàng 1 (ảnh rộng): ta đưa vào jpg và png 128x64, đọc được -99 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | jpg và png 128x64 \| -99 / 0 |
| 10.6 | Hàng 1 (ảnh rộng): suy ra: Toàn ảnh được dùng, không cắt, không đệm | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Toàn ảnh được dùng, không cắt, không đệm |
| 10.6 | Hàng 1 (ảnh cao): ta đưa vào jpg 64x128, đọc được -99 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | jpg 64x128 \| -99 / 0 |
| 10.6 | Hàng 1 (ảnh cao): suy ra: Như trên | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Như trên |
| 10.6 | Hàng 2: ta đưa vào png 128x64, cột xen kẽ 150 và 250, đọc được -50 / -50 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | png 128x64, cột xen kẽ 150 và 250 \| -50 / -50 |
| 10.6 | Hàng 2: suy ra: Hai cột kề nhau được lấy trung bình: (150 + 250) / 2 = 200, trừ mean 250 ra -50; nearest sẽ cho -100 hoặc 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Hai cột kề nhau được lấy trung bình: (150 + 250) / 2 = 200, trừ `mean` 250 ra -50; nearest sẽ cho -100 hoặc 0 |
| 10.6 | Hàng 3 (NCHW float32 và uint8): ta đưa vào npy, đọc được -100 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | npy \| -100 / 0 |
| 10.6 | Hàng 3 (NCHW float32 và uint8): suy ra: Chấp nhận | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Chấp nhận |
| 10.6 | Hàng 3 ([3,64,64]): ta đưa vào npy, đọc được -100 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | npy \| -100 / 0 |
| 10.6 | Hàng 3 ([3,64,64]): suy ra: Chấp nhận (không có chiều batch) | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Chấp nhận (không có chiều batch) |
| 10.6 | Hàng 3 (NHWC): ta đưa vào npy, đọc được ValueError: "shape (1, 64, 64, 3) is wrong, expect 'nchw' like (1, 3, 64, 64)!" | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | npy \| `ValueError`: "shape (1, 64, 64, 3) is wrong, expect 'nchw' like (1, 3, 64, 64)!" |
| 10.6 | Hàng 3 (NHWC): suy ra: Từ chối | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Từ chối |
| 10.6 | Hàng 3 ([1,3,32,32]): ta đưa vào npy, đọc được ValueError: cùng dạng thông báo | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | npy \| `ValueError`: cùng dạng thông báo |
| 10.6 | Hàng 3 ([1,3,32,32]): suy ra: Không tự resize npy | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Không tự resize npy |
| 10.6 | Hàng 4: ta đưa vào npy giá trị 150 đến 250, mean=250 std=2, đọc được -50 / 0 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | npy giá trị 150 đến 250, `mean=250 std=2` \| -50 / 0 |
| 10.6 | Hàng 4: suy ra: mean và std được áp dụng lên npy | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | `mean` và `std` được áp dụng lên npy |
| 10.6 | Hàng 4 (đối chứng mean): ta đưa vào cùng npy, mean=0 std=1, đọc được 150 / 250 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | cùng npy, `mean=0 std=1` \| 150 / 250 |
| 10.6 | Hàng 4 (đối chứng mean): suy ra: Xác nhận đọc đúng | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Xác nhận đọc đúng |
| 10.6 | Hàng 5: ta đưa vào w8a8 so với asymmetric_quantized-8, đọc được cùng quant_tab (-99 / 0, asym, layer) | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | `w8a8` so với `asymmetric_quantized-8` \| cùng `quant_tab` (-99 / 0, `asym`, `layer`) |
| 10.6 | Hàng 5: suy ra: config() chấp nhận tên cũ; kết quả giống w8a8 trên model này | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | `config()` chấp nhận tên cũ; kết quả giống `w8a8` trên model này |
| 10.6 | Điều kiện: PC, toolkit 2.3.2 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | PC x86_64, `.venv` Python 3.12.3, `rknn-toolkit2 2.3.2` |
| 10.6 | Điều kiện: không board | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Không dùng board. |
| 10.6 | Điều kiện: một model thử, một phiên bản toolkit | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Chỉ một model, một phiên bản toolkit. |
| 10.6 | Điều kiện: model thử: ONNX một Conv 1x1 đồng nhất, input NCHW [1,3,64,64] | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | ONNX một Conv 1x1 đồng nhất, input NCHW `[1,3,64,64]` |
| 10.6 | Điều kiện: ảnh dùng là gradient 150 đến 250 | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Ảnh dùng gradient 150 đến 250 |
| 10.6 | Điều kiện: mean=250, std=1, dải kỳ vọng [-100, 0] | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | `mean=250`, `std=1`, nên dải kỳ vọng sau chuẩn hóa là [-100, 0] |
| 10.6 | Điều kiện: min và max của tensor x đọc từ file .rknn | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | lấy `min`/`max` của tensor `x` bằng regex trên file `.rknn` |
| 10.6 | Điều kiện: chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Chấp nhận ở `config()` chưa chứng minh phần cứng hỗ trợ. |
| 10.6 | Điều kiện: cách đọc quant_tab không phải API công bố | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Đây là cách đọc, không phải API công bố |
| 10.6 | unknown: Thuật toán nội suy chính xác (bilinear, area, antialias) | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Thuật toán nội suy chính xác (bilinear, area, antialias) |
| 10.6 | unknown: Cách xử lý ảnh RGB/BGR, ảnh xám, ảnh có alpha | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Cách xử lý ảnh RGB/BGR, ảnh xám, ảnh có alpha |
| 10.6 | unknown: Model NHWC (tflite) có chấp nhận npy NHWC không | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Model NHWC (tflite) có chấp nhận npy NHWC không |
| 10.6 | unknown: Ảnh calibration và npy có cho cùng kết quả trên model thật | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Ảnh calibration và npy có cho cùng kết quả trên model thật |
| 10.6 | unknown: Ảnh hưởng lên độ chính xác sau lượng tử | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Ảnh hưởng lên độ chính xác sau lượng tử |
| 10.6 | unknown: Hành vi trên toolkit phiên bản khác | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Hành vi trên toolkit phiên bản khác |
| 10.6 | Chỉ loại được nearest (thuật toán nội suy chính xác chưa phân biệt) | T3 | LOG 2026-10-10_t3-calibration-pc/README.md | Phép thử chỉ loại được nearest |
| 10.6 | Dự đoán: toolkit tự resize ảnh calibration, resize có thể đổi thông tin ảnh, tốt nhất dùng ảnh đúng kích thước | T1 | UG232 tr.165 | However, the resize operation may also change the image information |
| 10.6 | Dự đoán: dữ liệu npy phải khớp shape đầu vào của model | T1 | UG232 tr.165 | it needs to be consistent with the shape input by the model |
| 10.6 | Dự đoán: tập calibration được chuẩn hóa (mean, std) trước khi lượng tử | T1 | UG232 tr.132 | the quantization correction dataset will undergo normalization first |
| 10.6 | Dự đoán: quantized_dtype mặc định w8a8 (API232) | T1 | API232 tr.7 | The default value is "w8a8". |
| 10.6 | Dự đoán: UG232 ghi mặc định asymmetric_quantized-8 | T1 | UG232 tr.122 | the default value is 'asymmetric_quantized-8' |
| 10.7 | A: YOLOv8n (SiLU): mAP50-95 tổng 0.5908 và AP50-95 từng lớp person 0.7186, helmet 0.621, head 0.3884, safety_clothes 0.6494, self_clothes 0.5764 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_baseline_100ep_s42,yolov8n_baseline,100,42,sfchd_test,v1,0.9048,0.8394,0.8924,0.5908,0.7186,0.621,0.3884,0.6494,0.5764 |
| 10.7 | A: YOLOv8s: mAP50-95 tổng 0.6152 và AP50-95 từng lớp person 0.7381, helmet 0.6542, head 0.4532, safety_clothes 0.6701, self_clothes 0.5603 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8s_baseline_100ep_s42,yolov8s_baseline,100,42,sfchd_test,v1,0.9001,0.8422,0.9035,0.6152,0.7381,0.6542,0.4532,0.6701,0.5603 |
| 10.7 | A: YOLO26n: mAP50-95 tổng 0.5883 và AP50-95 từng lớp person 0.7207, helmet 0.6374, head 0.3962, safety_clothes 0.6517, self_clothes 0.5352 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolo26n_baseline_100ep_s42,yolo26n_baseline,100,42,sfchd_test,v1,0.8843,0.8477,0.8865,0.5883,0.7207,0.6374,0.3962,0.6517,0.5352 |
| 10.7 | A: YOLOv8n ReLU (khởi tạo từ SiLU): mAP50-95 tổng 0.5835 và AP50-95 từng lớp person 0.7161, helmet 0.6154, head 0.3885, safety_clothes 0.6428, self_clothes 0.5548 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv | sfchd_5class_yolov8n_relu_100ep_s42,yolov8n_relu,100,42,sfchd_test,v1,0.9218,0.8394,0.8845,0.5835,0.7161,0.6154,0.3885,0.6428,0.5548 |
| 10.7 | A: số ví dụ lớp person trên tập test: 1688 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "instances": 1688 |
| 10.7 | A: số ví dụ lớp helmet trên tập test: 1409 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "instances": 1409 |
| 10.7 | A: số ví dụ lớp head trên tập test: 110 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "instances": 110 |
| 10.7 | A: số ví dụ lớp safety_clothes trên tập test: 1459 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "instances": 1459 |
| 10.7 | A: số ví dụ lớp self_clothes trên tập test: 74 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "instances": 74 |
| 10.7 | Điều kiện: tập test 1238 ảnh | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "n_images": 1238 |
| 10.7 | Điều kiện: evaluator protocol v1, LetterBox 640x640, rect=False, scaleup=False, center, pad 114 | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | LetterBox 640x640, rect=False, scaleup=False, center, pad 114 |
| 10.7 | Điều kiện: conf 0.001, iou 0.7, max_det 300, multi_label | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "conf": 0.001, "iou": 0.7, "max_det": 300, "multi_label": true |
| 10.7 | Điều kiện: FP32 dùng weights/best.pt | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "model_file": "weights/best.pt" |
| 10.7 | Điều kiện: FP32 chạy bằng PyTorch | T3 | RUN sfchd_5class_yolov8n_baseline_100ep_s42/eval/pt_fp32_sfchd_test.json | "backend": "pytorch" |
| 10.7 | Điều kiện: chỉ seed 42 nên chưa biết nhiễu giữa các seed | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Chỉ có seed 42, nên chưa biết nhiễu giữa các seed |
| 10.7 | YOLOv8n ReLU khởi tạo từ yolov8n.pt (trường pretrained của args.yaml) | T3 | RUN sfchd_5class_yolov8n_relu_100ep_s42/args.yaml | pretrained: yolov8n.pt |
| 10.7 | Nhận định "AP này có thể thấp hơn AP của ReLU train từ đầu" là của bộ hình, chưa kiểm bằng thí nghiệm | tính | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | (unknown) |
| 10.7 | Quy tắc chọn model dùng mAP50-95 INT8 tổng, không dùng AP từng lớp | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Quy tắc không dùng AP từng lớp |
| 10.7 | Một lớp vi phạm PPE sụt mạnh sau INT8 cần xem riêng; chưa có số từng lớp | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Nếu một lớp vi phạm PPE sụt mạnh sau INT8, cần xem riêng trước khi triển khai |
| 10.7 | Cột FP16 và INT8: mAP RKNN trên board chờ phase3 (chữ trên hình, không có số) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | mAP50-95 INT8 chạy trên board (phase3, tập test `sfchd`) |
| 10.7 | Dự đoán: build FP16 gần như không mất độ chính xác | T1 | UG232 tr.165 | with almost no accuracy loss |
| 10.7 | Dự đoán: tác động cuối cùng của lượng tử hóa cần kiểm trên dataset | T1 | UG232 tr.131 | the final impact of quantization on accuracy still needs validation on the dataset |
| 10.7 | Dự đoán: activation vẫn lượng tử hóa per-layer | T1 | UG232 tr.120 | while the activation values and intermediate values are still quantized using Per-Layer quantization |
| 10.8 | Quy tắc: chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm (tuyệt đối) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | (tuyệt đối, ví dụ 0.560 so 0.570) |
| 10.8 | Chỉ số độ chính xác: mAP50-95 INT8 chạy trên board (phase3, tập test sfchd) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | mAP50-95 INT8 chạy trên board (phase3, tập test `sfchd`) |
| 10.8 | Chỉ số tốc độ: trung vị độ trễ tier 1 (eval_perf) ở core_mask AUTO (phase4) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Trung vị độ trễ tier 1 (`eval_perf`) ở `core_mask` AUTO (phase4) |
| 10.8 | Ba ứng viên: YOLOv8n SiLU, YOLOv8n ReLU, YOLO26n | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | YOLOv8n SiLU (`yolov8n_baseline`) |
| 10.8 | Khi không rõ: giữ YOLOv8n SiLU nếu chênh lệch nằm trong độ trải giữa các phiên đo | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | chênh lệch nằm trong độ trải giữa các phiên đo |
| 10.8 | Quy tắc chốt trước khi có số (Accepted 2026-10-11) | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | Chốt quy tắc chọn model trước khi có số |
| 10.8 | Số T3 trọng số ngẫu nhiên không dùng để chọn model | T1 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | không dùng chúng để chọn model |
| 10.8 | Dự đoán: luật fusion phần cứng Conv+Relu | T1 | UG232 tr.142 | Conv+Relu |
| 10.8 | Dự đoán: Non-Relu activation function kém hiệu quả | T1 | UG232 tr.146 | Non-Relu activation function |
| 10.8 | Dự đoán: Y6 Table 4, Conv SiLU 36.6% AP | T2 | Y6 tr.9 | Conv SiLU 36.6% 963 |
| 10.8 | Dự đoán: Y6 Table 4, Conv ReLU 34.8% AP | T2 | Y6 tr.9 | Conv ReLU 34.8% 1246 |
| 10.8 | Dự đoán: 36.6 trừ 34.8 là 1.8 điểm (phép tính của bộ hình) | tính | Y6 tr.9 | (số học) |
