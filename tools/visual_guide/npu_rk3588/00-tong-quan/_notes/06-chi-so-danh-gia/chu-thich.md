# Ghi chú chuyên đề: Các chỉ số đánh giá mô hình phát hiện vật thể (06-chi-so-danh-gia)

## Câu hỏi mở đầu
IoU, Precision, Recall, AP và mAP50-95 được định nghĩa như thế nào trong bài toán phát hiện vật thể, tại sao mAP50-95 lại khắt khe hơn nhiều so với mAP50, và các chỉ số này thể hiện ra sao trên tập dữ liệu bảo hộ lao động (PPE) của đề tài?

## Hình M.1 (hm-1-iou-va-phan-loai-du-doan) [T2 chung]
Chỉ số IoU và Phân loại kết quả dự đoán (TP, FP, FN):
- Bản chất hình học của IoU (Intersection over Union): IoU đo lường mức độ trùng khớp giữa bounding box dự đoán của mô hình (Prediction B_p) và bounding box nhãn thực tế (Ground Truth B_gt). Công thức là tỷ số giữa diện tích vùng giao nhau chia cho diện tích vùng hợp nhất: IoU = Area(B_p ∩ B_gt) / Area(B_p ∪ B_gt). Khi hai hộp trùng khít hoàn toàn, IoU = 1.0; khi hai hộp không chạm nhau, IoU = 0.
- Ba mức độ trùng khớp trực quan:
  - Khớp rất tốt (IoU = 0.88): Hai hộp gần như trùng khít viền.
  - Vừa đạt ngưỡng (IoU = 0.52): Hai hộp đè nhau khoảng 50% diện tích, vừa đủ để vượt qua ngưỡng cơ bản 0.50.
  - Trượt ngưỡng (IoU = 0.15): Hai hộp chỉ chạm mép nhẹ (< 0.50), bị xem là định vị sai đối tượng.
- Phân loại kết quả trên bài toán bảo hộ lao động:
  - True Positive (TP - Đúng): Mô hình dự đoán có nhãn (ví dụ mũ bảo hộ helmet) và hộp dự đoán khớp với hộp nhãn thật có IoU ≥ ngưỡng quy định.
  - False Positive (FP - Báo động giả / Đoán nhầm): Mô hình tạo ra một hộp dự đoán nhưng không có nhãn thật ở đó (nhận nhầm đầu trần hoặc nền thành mũ), hoặc có nhãn thật nhưng hộp bị lệch vị trí khiến IoU < ngưỡng.
  - False Negative (FN - Bỏ sót): Có vật thể thật trên ảnh nhưng mô hình hoàn toàn không tạo ra hộp dự đoán nào bao quanh.
- Định nghĩa Precision và Recall:
  - Precision = TP / (TP + FP): Trong tất cả các hộp mô hình báo là có mũ, có bao nhiêu phần trăm thực sự là mũ?
  - Recall = TP / (TP + FN): Trong toàn bộ số mũ thực tế ngoài công trường, mô hình phát hiện được bao nhiêu phần trăm?
Đọc thêm: 10_ mục 10.5; 11_ mục 11.1. Khái niệm: Hình 10.5, Hình 11.1

## Hình M.2 (hm-2-co-che-duong-cong-pr-va-ap) [T2 chung]
Cơ chế Đường cong Precision-Recall (P-R Curve), Average Precision (AP) và gom trung bình mAP:
- Sự đánh đổi khi trượt ngưỡng tin cậy (Confidence Threshold):
  - Ngưỡng cao (Confidence ≥ 0.90): Mô hình cực kỳ cẩn trọng, chỉ giữ lại các hộp chắc chắn nhất. Ít báo nhầm nên Precision rất cao (~1.0), nhưng bỏ sót hầu hết vật thể che khuất nên Recall rất thấp.
  - Ngưỡng trung bình (Confidence ≈ 0.50): Cân bằng giữa việc phát hiện và hạn chế báo động giả.
  - Ngưỡng thấp (Confidence ≤ 0.10): Mô hình giữ lại toàn bộ hộp nghi ngờ. Bắt trọn hầu hết vật thể ngoài công trường nên Recall rất cao, nhưng lẫn nhiều hộp rác/dương tính giả làm Precision tụt dốc.
- Đường cong P-R và Diện tích Average Precision (AP):
  - Mỗi ngưỡng tin cậy cho một cặp tọa độ (Recall, Precision). Nối các điểm này từ trái sang phải tạo thành đường cong P-R dốc xuống.
  - Diện tích nằm dưới đường cong chính là Average Precision: AP = ∫ P(R) dR. Điểm AP càng gần 1.0 chứng minh mô hình duy trì Precision cao ngay cả khi đẩy Recall lên tối đa.
- Cơ chế gom trung bình mAP (Mean Average Precision):
  - Mỗi lớp vật thể (Person, Helmet, Head, Clothes) có phân bố đặc trưng riêng và một đường cong P-R độc lập, sinh ra AP_1, AP_2, ..., AP_C.
  - Điểm tổng hợp mAP là trung bình cộng số học của AP trên tất cả các lớp: mAP = (1/C) * Σ AP_c.
Đọc thêm: 11_ mục 11.1, 11.2. Khái niệm: Hình 11.1, Hình 11.2

## Hình M.3 (hm-3-map50-95-va-phan-tich-5-lop-ppe) [T2 chung]
Bản chất khắt khe của mAP50-95, Biểu đồ 5 lớp PPE và Độ nhạy IoU của vật thể nhỏ:
- Cơ chế co rút của P-R Curve qua 10 mốc IoU (Chuẩn COCO):
  - mAP50 chỉ đo tại mốc IoU = 0.50: Hộp chỉ cần ôm 50% là tính TP, đường cong P-R mở rộng, AP đạt rất cao (0.8924).
  - Khi nâng ngưỡng IoU lên 0.70, 0.85, 0.95: Các hộp dự đoán bị lệch nhẹ viền lập tức bị phán là False Positive. Số lượng TP giảm mạnh, làm đường cong P-R sụt nhanh và co rúm lại.
  - mAP50-95 lấy trung bình cộng AP tại 10 mốc: 0.50, 0.55, 0.60, ..., 0.95. Do các mốc cao (0.80 - 0.95) có AP tụt dốc nên điểm trung bình kéo về 0.5908.
- Biểu đồ thanh ngang 5 lớp PPE của đề tài (YOLOv8n baseline trên sfchd_5class):
  - person (0.7186 / 71.9%): Cao nhất nhờ diện tích lớn và đường nét cơ thể người rõ rệt.
  - safety_clothes (0.6494 / 64.9%): Khá cao do màu huỳnh quang phản quang tách biệt khỏi môi trường.
  - helmet (0.6210 / 62.1%): Tốt nhờ dạng vòm mũ và bề mặt cứng đặc trưng.
  - self_clothes (0.5764 / 57.6%): Trung bình vì họa tiết áo thường phục dễ lẫn vào hậu cảnh.
  - head (0.3884 / 38.8%): Thấp nhất.
- Lý giải hình học độ nhạy IoU của vật thể nhỏ:
  - Cùng độ lệch định vị 10 pixel:
    - Với hộp lớn person (300x500 px): Độ lệch 10 px chỉ chiếm phần rất nhỏ diện tích, IoU vẫn đạt > 0.90 (vượt qua hầu hết các mốc IoU).
    - Với hộp nhỏ head (30x40 px): Độ lệch 10 px làm mất hơn một nửa diện tích giao nhau, IoU tụt xuống dưới 0.45 và rớt khỏi toàn bộ các mốc tính điểm từ 0.50 đến 0.95!
Đọc thêm: 11_ mục 11.1, 11.2. Khái niệm: Hình 11.1, Hình 11.2

## Hiểu sai thường gặp
- "mAP50 và mAP50-95 là hai cách viết khác nhau của cùng một chỉ số" -> mAP50 chỉ đo tại một mốc IoU=0.50; mAP50-95 lấy trung bình tại 10 mốc IoU từ 0.50 đến 0.95 nên điểm số luôn thấp hơn nhiều và đánh giá độ ôm khít của box chặt chẽ hơn [REPO sfchd_5class.csv:2] (Hình M.3)
- "Chỉ cần Precision cao là mô hình đã hoạt động tốt ngoài thực tế" -> Precision cao nhưng Recall thấp nghĩa là mô hình rất nhát, chỉ dự đoán vài trường hợp cực kỳ rõ và bỏ sót hầu hết công nhân vi phạm bảo hộ lao động (Hình M.1, Hình M.2)
- "IoU chỉ cần đạt 0.5 là đủ cho mọi tiêu chuẩn công nghiệp" -> Ngưỡng 0.50 chỉ là điều kiện cần tối thiểu; khi cần định vị chính xác bộ phận nhỏ (như gắn kết vị trí mũ lên đầu người), IoU thấp sẽ làm sai lệch phân tích vi phạm (Hình M.1, Hình M.3)
- "Các lớp đối tượng khác nhau đều có độ chính xác mAP tương đương nhau" -> Trong cùng mô hình YOLOv8n, lớp person đạt 0.7186 mAP50-95 trong khi lớp head chỉ đạt 0.3884 do diện tích nhỏ và cực kỳ nhạy cảm với sai lệch pixel khi tính IoU [REPO sfchd_5class.csv:2] (Hình M.3)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Tại sao trong bảng kết quả của đề tài, điểm số mAP50 của mô hình YOLOv8n đạt tới 0.8924 trong khi mAP50-95 chỉ đạt 0.5908?
Đáp án: Vì mAP50 chỉ yêu cầu bounding box dự đoán chồng lấn từ 50% diện tích trở lên với nhãn thật (IoU ≥ 0.50) là được tính điểm tối đa. Ngược lại, mAP50-95 là trung bình cộng trên 10 mốc IoU từ 0.50 đến 0.95; ở các mốc IoU khắt khe như 0.80, 0.85, 0.90, 0.95, các box bị lệch nhẹ viền sẽ không còn được tính là TP, làm AP ở các mốc này giảm mạnh và kéo điểm trung bình chung xuống 0.5908 [REPO sfchd_5class.csv:2] (Hình M.3).

### Câu 2 (phân biệt)
Phân biệt hai loại sai lầm False Positive (FP) và False Negative (FN) trong bài toán giám sát an toàn lao động công trường. Loại nào gây nguy hiểm bỏ lọt vi phạm hơn?
Đáp án: FP là báo động giả (không có người vi phạm nhưng hệ thống báo có), gây phiền toái cho người giám sát. FN là bỏ sót vi phạm (công nhân thực tế không đội mũ bảo hộ nhưng hệ thống không phát hiện ra), trực tiếp dẫn đến nguy cơ mất an toàn lao động và tai nạn mà không được cảnh báo. Do đó, FN là sai lầm nguy hiểm hơn trong giám sát an toàn (Hình M.1).

### Câu 3 (áp dụng)
Tại sao lớp đầu trần (head) trong bài toán đồ bảo hộ lao động lại có điểm mAP50-95 thấp nhất (0.3884) so với lớp người (person đạt 0.7186)?
Đáp án: Do kích thước của đầu người trên ảnh camera công trường thường rất nhỏ (vài chục pixel). Khi tính toán IoU ở các mốc khắt khe (0.75 - 0.95), chỉ cần dự đoán lệch 5-10 pixel thì diện tích giao nhau của vật thể nhỏ sẽ tụt dốc nghiêm trọng khiến IoU rơi xuống dưới ngưỡng, bị chuyển thành False Positive và làm sụt giảm mạnh điểm AP của lớp này [REPO sfchd_5class.csv:2] (Hình M.3).

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| M.1 | Phân loại TP, FP, FN và công thức IoU, Precision, Recall | tính | REPO ai/automation/leaderboards/sfchd_5class.csv | (số học) |
| M.2 | Đường cong P-R và tính AP = ∫ P(R) dR | tính | REPO ai/automation/leaderboards/sfchd_5class.csv | (số học) |
| M.2 | mAP là trung bình cộng AP của các lớp | tính | REPO ai/automation/leaderboards/sfchd_5class.csv | (số học) |
| M.3 | Kết quả baseline YOLOv8n: Precision 0.9048, Recall 0.8394, mAP50 0.8924, mAP50-95 0.5908 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:2 | 0.9048,0.8394,0.8924,0.5908,0.7186,0.621,0.3884,0.6494,0.5764 |
| M.3 | AP50-95 của 5 lớp PPE: person 0.7186, helmet 0.6210, head 0.3884, safety_clothes 0.6494, self_clothes 0.5764 | T3 | REPO ai/automation/leaderboards/sfchd_5class.csv:2 | 0.7186,0.621,0.3884,0.6494,0.5764 |
| M.3 | Chỉ số đánh giá mô hình chọn lọc: mAP50-95 INT8 trên board | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | mAP50-95 INT8 chạy trên board |
| M.3 | Ngưỡng sụt giảm mAP chấp nhận được: không quá 1.0 điểm so với SiLU | T3 | REPO tmp/02_decisions/2026-10-11_model-selection-rule.md | không thấp hơn YOLOv8n SiLU INT8 quá 1.0 điểm |
| M.3 | YOLOv6 báo cáo APval, AP50, AP50-95 theo chuẩn COCO | T2 | Y6 tr.8 | 51.7% |
| M.3 | PTQ 4-bit sụt mAP nghiêm trọng trên YOLOv5s | T2 | QYOLO tr.2 | 4-bit quantized YOLOv5s employing Percentile achieves only 7.0% mAP |
