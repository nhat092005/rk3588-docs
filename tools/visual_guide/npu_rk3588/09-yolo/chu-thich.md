# Phần 9: YOLO

## Câu hỏi mở đầu
YOLOv8n và YOLO26n khác nhau ở khối nào, và mỗi khối đó đi qua đường xuất RKNN thành lớp nào trên NPU RK3588?

## Hình 9.1 (h9-1-v8n-26n) [T1 RK3588]
YOLOv8n và YOLO26n có cùng khung backbone, neck và Detect ba mức P3, P4, P5, nhưng YOLO26n đổi C2f thành C3k2, thêm C2PSA ở cuối backbone và bỏ DFL ở Detect. Với nc=5, đầu vào 640x640, sau fuse và end2end tắt (đường RKNN), YOLOv8n có 3,006,623 tham số và 8.087 GFLOPs, YOLO26n có 2,375,811 và 5.314; hình đọc từng hàng từ bảng lớp do layer_table.py tính từ model dựng bằng yaml, trọng số ngẫu nhiên. Lớp Detect chiếm 36.7% GFLOPs của YOLOv8n và 8.2% của YOLO26n (phép tính của bộ hình), nên phần lớn mức giảm FLOPs nằm ở đầu. Ranh giới backbone, neck, head theo hai danh sách của yaml; độ trễ không suy được từ FLOPs, xem Hình 10.4.
Đọc thêm: 09_ mục 9.1, 9.3. Số đo: Hình 10.4, Hình 10.5
Khái niệm: Hình 9.2

## Hình 9.2 (h9-2-cac-khoi) [T1 RK3588]
C3k2 giữ khung của C2f và chỉ đổi phần tử bên trong theo hai cờ: Bottleneck thu kênh, C3k, hoặc Bottleneck cộng PSABlock khi attn=True. SPPF khác nhau ở hai chỗ: YOLO26n có cv1 không activation và cộng nối tắt khi số kênh vào bằng ra, còn YOLOv8n thì không. Attention chỉ có ở YOLO26n (lớp 10 là C2PSA, lớp 22 là C3k2 với attn=True), mỗi khối 2 đầu trên 400 token của lưới P5. Detect của YOLOv8n có DFL và đầu ra [1, 9, 8400] cần NMS ngoài đồ thị; Detect của YOLO26n bỏ DFL, và chỉ khi end2end bật (nms=False) mới ra [1, 300, 6] qua topk và gather, chế độ mà exporter tắt lại với rknn. YOFF tr.6 gọi nhánh một-một là mặc định, còn mã nguồn và UDOC cho nhánh một-nhiều khi không đặt nms; hình theo mã nguồn.
Đọc thêm: 09_ mục 9.2, 9.6. Số đo: Hình 10.2, Hình 10.4
Khái niệm: Hình 8.2, Hình 9.1

## Hình 9.3 (h9-3-duong-xuat) [T1 RK3588]
Đường xuất của repo là YOLO(pt).export(format="rknn", quantize=8): Ultralytics tắt end2end, đổi forward của C2f, bọc _NormalizeCoords, xuất ONNX opset 19 rồi onnxslim, sau đó toolkit build INT8. Hai bảng so op ONNX (format=onnx và ONNX thật đưa vào onnx2rknn, khác nhau ở Concat, Slice, Div do _NormalizeCoords) với lớp RKNN đo trên board: YOLO26n có 182 lớp (180 trên NPU, ngoài Input và Output không có lớp CPU, 2 exSDPAttention), YOLOv8n có 119 lớp với 1 Transpose CPU. Số Conv trong ONNX bằng tổng ConvExSwish, Conv và ConvAdd (64 và 102); bảng RKNN không có lớp MatMul, Softmax, Transpose của attention. Số lớp T3 là cấu trúc và độ trễ của trọng số ngẫu nhiên, không phải độ chính xác.
Đọc thêm: 09_ mục 9.4, 9.5.5. Số đo: Hình 10.2, Hình 10.4
Khái niệm: Hình 6.2, Hình 6.3

## Hình 9.4 (h9-4-ma-tran-tieu-chi) [T1 RK3588]
Mỗi khối kiến trúc được đọc theo năm tiêu chí: mục NPU trong OPL, điều kiện OPL so với đồ thị, dòng đa lõi, quy tắc ghép của UG232 và lớp RKNN quan sát được (T3). Ô cuối xanh là lớp chạy trên NPU với cấu trúc đó (YOLO26n: trọng số ngẫu nhiên; YOLOv8n: ngẫu nhiên và model đã huấn luyện ở lượt 3 có cùng ánh xạ); ô hồng là unknown hoặc nơi OPL không khớp đồ thị, ví dụ Resize asymmetric và floor vẫn chạy NPU. Đầu end2end với TopK chỉ có mục CPU trong OPL và không nằm trong đường RKNN. Chưa biết độ chính xác INT8 của khối attention, và ma trận không giải thích vì sao YOLO26n chậm hơn: xem Hình 10.4 và Hình 10.7.
Đọc thêm: 09_ mục 9.5, 9.7, 9.8. Số đo: Hình 10.4, Hình 10.7
Khái niệm: Hình 6.2, Hình 6.3, Hình 8.2
Thay đổi chỉ khi huấn luyện: bỏ DFL (reg_max 1) và đầu một-một làm đổi đồ thị xuất (Hình 9.2); ProgLoss, STAL và MuSGD không đổi đồ thị suy luận theo mô tả của YOFF và Y26A.

## Hiểu sai thường gặp
- "Attention của YOLO26n rơi về CPU trên RK3588" -> T3 (YOLO26n, INT8, trọng số ngẫu nhiên, chỉ cấu trúc): 180 lớp NPU, 0 lớp CPU ngoài Input và Output, mỗi khối attention thành một lớp exSDPAttention INT8 NPU; lớp này chỉ chạy lõi 0 vì OPL ghi đa lõi 不支持 [LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt; OPL tr.105] (Hình 9.3, Hình 9.4)
- "NMS-free nghĩa là không có hậu xử lý" -> chế độ end2end bật (nms=False) vẫn tính topk và gather trong đồ thị, ra tối đa 300 hộp [1, 300, 6]; với rknn exporter tắt end2end, nên đồ thị ra [1, 9, 8400] và cần NMS ngoài [ULT nn/modules/head.py:241-256; engine/exporter.py:683-688; cfg/default.yaml:61] (Hình 9.2, Hình 9.3)
- "YOLO26n xuất ra mặc định là đầu một-một" -> exporter đặt end2end = (nms is False), mặc định nms không đặt nên là False và đồ thị dùng nhánh một-nhiều; YOFF tr.6 nói ngược lại, mâu thuẫn chưa phân xử bằng nguồn thứ ba, hình theo mã nguồn và UDOC [ULT engine/exporter.py:683; YOFF tr.6; UDOC dòng 156] (Hình 9.2)
- "C3k2 chỉ là C2f đổi tên" -> C3k2 kế thừa C2f nhưng phần tử m đổi theo cờ (Bottleneck thu kênh, C3k, hoặc Bottleneck cộng PSABlock), và shortcut mặc định True thay vì False [ULT nn/modules/block.py:1072-1109, 294] (Hình 9.2)
- "SPPF giống nhau ở hai model" -> SPPF của YOLO26n có shortcut=True (cộng nối tắt khi c1 == c2) và cv1 không activation, còn hàng yaml cũ của YOLOv8n được gán lại SiLU cho cv1; trên board cv1 là Conv trơn ở YOLO26n và ConvExSwish ở YOLOv8n [ULT nn/modules/block.py:229-240; nn/tasks.py:2194-2196; LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt, layers_yolov8n_AUTO.txt] (Hình 9.2, Hình 9.4)
- "Mỗi op ONNX ứng với đúng một lớp RKNN" -> số lớp lệch số nút: ví dụ ONNX có Div 2 nhưng bảng lớp RKNN không có lớp Div, và Concat ONNX 24 so 23 lớp ở YOLO26n; cách trình biên dịch gộp hoặc tách không có trong nguồn [data/rknn_path_onnx.json; LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt] (Hình 9.3)
- "Op không thỏa điều kiện của OPL thì chạy CPU" -> Resize của cả hai model có coordinate_transformation_mode asymmetric và nearest_mode floor, ngoài các giá trị OPL liệt kê, nhưng trên board cả hai Resize chạy INT8 trên NPU; UG232 tr.176 lại nói toolkit đổi Resize thành ConvTranspose, hai tài liệu T1 và T3 chưa khớp nhau [OPL tr.87; data/rknn_path_onnx.json; LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt; UG232 tr.176] (Hình 9.4)
- "Op có mục NPU trong OPL thì chia được ba lõi" -> đa lõi là một dòng riêng của từng op: ConvolutionSwish ghi 暂不支持 và ConvExSwish ở T3 chỉ lõi 0 (87 trên 87 ở YOLO26n, 57 trên 57 ở YOLOv8n); Mul OPL ghi 支持 nhưng UG232 tr.75 không liệt kê và 2 lớp Mul ở T3 chỉ lõi 0 [OPL tr.63, 77; UG232 tr.75; LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt] (Hình 9.4)
- "TopK, GatherElements của đầu end2end chạy được trên NPU" -> OPL chỉ có mục CPU cho TopK, GatherElements, ReduceMax, Mod, Cast, Flatten và OPSUP ghi TopK Not Supported; đầu này không nằm trong đường RKNN [OPL tr.333, 330; OPSUP dòng 189] (Hình 9.4)
- "Depthwise 3x3 là lý do YOLO26n chậm hơn" -> chưa biết: đo được 8 lớp depthwise có MacUsage thấp (0.30 đến 1.24%) nhưng nguyên nhân chậm hơn chưa tách được, và độ trễ thuộc Hình 10.4 [LOG 2026-10-10_yolo-phaseA/README.md] (Hình 9.4)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao ONNX thật đưa vào onnx2rknn có Concat 18, Slice 4, Div 2 ở YOLOv8n, trong khi YOLO(...).export(format="onnx") cho Concat 17, Slice 2, Div 1?
Đáp án: với format="rknn", quantize=8, task detect và end2end tắt, Exporter bọc model bằng _NormalizeCoords, chia 4 tọa độ hộp cho [w, h, w, h] rồi slice và concat lại; comment trong mã nói lý do là để scale INT8 theo tensor giữ được điểm lớp. format="onnx" không bọc [ULT engine/exporter.py:1100-1117; utils/export/engine.py:17-48; data/rknn_path_onnx.json; data/ops_via_exporter.json] (Hình 9.3)
### Câu 2 (phân biệt)
So Detect của YOLOv8n với Detect của YOLO26n ở nhánh hộp và nhánh lớp, với nc=5.
Đáp án: YOLOv8n (legacy=True, reg_max 16): nhánh hộp Conv 3x3, Conv 3x3 rồi Conv2d 1x1 ra 64 kênh (4 x 16), giải mã qua DFL; nhánh lớp Conv 3x3, Conv 3x3, Conv2d 1x1 ra 5. YOLO26n (legacy=False, reg_max 1): nhánh hộp ra 4 kênh với 16 kênh trung gian, dfl là Identity; nhánh lớp dùng DWConv 3x3 và Conv 1x1 hai lần rồi Conv2d 1x1 ra 5 [ULT nn/modules/head.py:122-138; nn/tasks.py:2126-2127; LOG 2026-10-10_yolo-arch/out/structure_and_ops.log] (Hình 9.2)
### Câu 3 (phân biệt)
Phân biệt MatMul và exSDPAttention theo OPL, và nói T3 thấy gì ở hai khối attention của YOLO26n.
Đáp án: OPL không có mục NPU cho MatMul, chỉ có mục CPU 4.33 không giới hạn; NPU có exMatMul (3.2.76, đa lõi 不支持) và exSDPAttention (3.2.78, channel trong (0, 8192], đa lõi 不支持). Trên board (trọng số ngẫu nhiên, chỉ cấu trúc) bảng lớp không có MatMul, Softmax, Transpose mà có 2 exSDPAttention INT8 NPU, cả hai chỉ lõi 0 ở CORE_0_1_2; quy tắc nhận chuỗi MatMul, Softmax, MatMul không có trong T1 [OPL tr.324, 102, 105; LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt] (Hình 9.3, Hình 9.4)
### Câu 4 (áp dụng)
Bạn xuất YOLO26n 5 lớp bằng export(format="rknn", quantize=8) và không truyền nms. Đầu ra của .rknn là gì và host cần làm gì thêm?
Đáp án: nms không đặt nên end2end bị đặt False (và với rknn còn bị tắt nếu nms=False), metadata ghi end2end: false và đồ thị ra [1, 9, 8400] (4 hộp xywh và 5 lớp); NMS nằm ngoài đồ thị nên chạy ở host [ULT engine/exporter.py:683-688; cfg/default.yaml:61; LOG 2026-10-10_yolo-phaseA/raw/metadata_yolo26n.yaml; LOG 2026-10-10_yolo-arch/out/table_26n.md] (Hình 9.2, Hình 9.3)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 9.1 | Ý nghĩa cột from của yaml | T1 | ULT cfg/models/v8/yolov8.yaml:19 | [from, repeats, module, args] |
| 9.1 | YOLOv8n: scale n [depth, width, max_channels] | T1 | ULT cfg/models/v8/yolov8.yaml:11 | n: [0.33, 0.25, 1024] |
| 9.1 | YOLO26n: scale n [depth, width, max_channels] | T1 | ULT cfg/models/26/yolo26.yaml:13 | n: [0.50, 0.25, 1024] |
| 9.1 | YOLOv8n: danh sách backbone của yaml | T1 | ULT cfg/models/v8/yolov8.yaml:18 | backbone: |
| 9.1 | YOLOv8n: danh sách head của yaml (neck và Detect) | T1 | ULT cfg/models/v8/yolov8.yaml:32 | head: |
| 9.1 | YOLO26n: danh sách backbone của yaml | T1 | ULT cfg/models/26/yolo26.yaml:20 | backbone: |
| 9.1 | YOLO26n: danh sách head của yaml (neck và Detect) | T1 | ULT cfg/models/26/yolo26.yaml:35 | head: |
| 9.1 | YOLOv8n: lớp Conv đầu | T1 | ULT cfg/models/v8/yolov8.yaml:20 | - [-1, 1, Conv, [64, 3, 2]] # 0-P1/2 |
| 9.1 | YOLOv8n: C2f backbone (có shortcut True) | T1 | ULT cfg/models/v8/yolov8.yaml:22 | - [-1, 3, C2f, [128, True]] |
| 9.1 | YOLOv8n: SPPF | T1 | ULT cfg/models/v8/yolov8.yaml:29 | - [-1, 1, SPPF, [1024, 5]] # 9 |
| 9.1 | YOLOv8n: Upsample nearest | T1 | ULT cfg/models/v8/yolov8.yaml:33 | - [-1, 1, nn.Upsample, [None, 2, "nearest"]] |
| 9.1 | YOLOv8n: Concat với lớp 6 | T1 | ULT cfg/models/v8/yolov8.yaml:34 | - [[-1, 6], 1, Concat, [1]] # cat backbone P4 |
| 9.1 | YOLOv8n: C2f ở neck | T1 | ULT cfg/models/v8/yolov8.yaml:35 | - [-1, 3, C2f, [512]] # 12 |
| 9.1 | YOLOv8n: Detect lấy lớp 15, 18, 21 | T1 | ULT cfg/models/v8/yolov8.yaml:49 | - [[15, 18, 21], 1, Detect, [nc]] # Detect(P3, P4, P5) |
| 9.1 | YOLO26n: C3k2 ở backbone (c3k=False, e=0.25) | T1 | ULT cfg/models/26/yolo26.yaml:24 | - [-1, 2, C3k2, [256, False, 0.25]] |
| 9.1 | YOLO26n: SPPF có thêm đối số 3 và True | T1 | ULT cfg/models/26/yolo26.yaml:31 | - [-1, 1, SPPF, [1024, 5, 3, True]] # 9 |
| 9.1 | YOLO26n: C2PSA ở lớp 10 | T1 | ULT cfg/models/26/yolo26.yaml:32 | - [-1, 2, C2PSA, [1024]] # 10 |
| 9.1 | YOLO26n: C3k2 ở lớp 22 có attn=True | T1 | ULT cfg/models/26/yolo26.yaml:50 | - [-1, 1, C3k2, [1024, True, 0.5, True]] # 22 (P5/32-large) |
| 9.1 | YOLO26n: Detect lấy lớp 16, 19, 22 | T1 | ULT cfg/models/26/yolo26.yaml:52 | - [[16, 19, 22], 1, Detect, [nc]] # Detect(P3, P4, P5) |
| 9.1 | YOLO26n: end2end True trong yaml | T1 | ULT cfg/models/26/yolo26.yaml:9 | end2end: True # whether to use end-to-end mode |
| 9.1 | YOLO26n: reg_max 1 | T1 | ULT cfg/models/26/yolo26.yaml:10 | reg_max: 1 # DFL bins |
| 9.1 | reg_max mặc định 16 khi yaml không đặt | T1 | ULT nn/tasks.py:2014 | reg_max = d.get("reg_max", 16) |
| 9.1 | Đầu ra Detect là hộp cộng sigmoid của điểm lớp: 4 + nc kênh | T1 | ULT nn/modules/head.py:206 | return torch.cat((dbox, x["scores"].sigmoid()), 1) |
| 9.1 | Bảng lớp: GFLOPs đo bằng FlopCounterMode, 2 FLOP mỗi MAC | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:2 | GFLOPs (torch FlopCounterMode, 2 FLOPs per MAC) |
| 9.1 | Bảng lớp: nc=5 | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:21 | m = DetectionModel(cfg, nc=5, verbose=False).eval() |
| 9.1 | Bảng lớp: đầu vào 640x640 | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:27 | x = torch.zeros(1, 3, 640, 640) |
| 9.1 | Bảng lớp: đã fuse, end2end tắt (đường xuất RKNN) | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:55 | table(copy.deepcopy(cfg), tag + '_export_rknn', end2end_export=False) |
| 9.1 | Bảng lớp: fuse model trước khi đếm | T1 tính | LOG 2026-10-10_yolo-arch/layer_table.py:24 | m.fuse(verbose=False) if hasattr(m, 'fuse') else None |
| 9.1 | YOLOv8n: Conv trong ONNX theo loại (1x1, 3x3 s1, 3x3 s2, depthwise) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "3x3 s2": 7, "1x1": 25, "3x3 s1": 32 |
| 9.1 | YOLO26n: Conv trong ONNX theo loại (1x1, 3x3 s1, 3x3 s2, depthwise) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "3x3 s2": 7, "1x1": 55, "3x3 s1": 32, "depthwise 3x3": 8 |
| 9.1 | Đầu ra [1, 9, 8400] gồm 4 hộp cộng 5 lớp | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | (số học) |
| 9.1 | Phần trăm tham số của Detect: 751519 / 3006623 = 25.0%, 120443 / 2375811 = 5.1% | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | (số học) |
| 9.1 | Phần trăm GFLOPs của Detect: 2.965 / 8.087 = 36.7%, 0.435 / 5.314 = 8.2% | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | (số học) |
| 9.1 | Mức giảm FLOPs: 2.965 - 0.435 = 2.530 trên 8.087 - 5.314 = 2.773 | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | (số học) |
| 9.1 | Khối attention: lớp 10 (C2PSA) và lớp 22 (C3k2, attn=True); YOLOv8n không có | T1 | ULT cfg/models/26/yolo26.yaml:50 | - [-1, 1, C3k2, [1024, True, 0.5, True]] # 22 (P5/32-large) |
| 9.2 | C2f: c = int(c2 * e) | T1 | ULT nn/modules/block.py:306 | self.c = int(c2 * e)  # hidden channels |
| 9.2 | C2f: cv1 Conv 1x1 c1 -> 2c | T1 | ULT nn/modules/block.py:307 | self.cv1 = Conv(c1, 2 * self.c, 1, 1) |
| 9.2 | C2f: cv2 Conv 1x1 (2+n)c -> c2 | T1 | ULT nn/modules/block.py:308 | self.cv2 = Conv((2 + n) * self.c, c2, 1)  # optional act=FReLU(c2) |
| 9.2 | C2f: n Bottleneck 3x3, e=1.0 | T1 | ULT nn/modules/block.py:309 | self.m = nn.ModuleList(Bottleneck(self.c, self.c, shortcut, g, k=((3, 3), (3, 3)), e=1.0) for _ in range(n)) |
| 9.2 | C2f: tách đôi, mỗi Bottleneck đọc nửa cuối, nối tất cả | T1 | ULT nn/modules/block.py:313 | y = list(self.cv1(x).chunk(2, 1)) |
| 9.2 | C2f: nối mọi đầu ra rồi cv2 | T1 | ULT nn/modules/block.py:315 | return self.cv2(torch.cat(y, 1)) |
| 9.2 | C2f: shortcut mặc định False | T1 | ULT nn/modules/block.py:294 | def __init__(self, c1: int, c2: int, n: int = 1, shortcut: bool = False, g: int = 1, e: float = 0.5): |
| 9.2 | Bottleneck: cộng x khi shortcut và c1 == c2 | T1 | ULT nn/modules/block.py:480 | self.add = shortcut and c1 == c2 |
| 9.2 | Bottleneck: hai Conv liên tiếp, cộng x nếu add | T1 | ULT nn/modules/block.py:484 | return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x)) |
| 9.2 | YOLOv8n: backbone C2f truyền shortcut True | T1 | ULT cfg/models/v8/yolov8.yaml:22 | - [-1, 3, C2f, [128, True]] |
| 9.2 | YOLOv8n: neck C2f không truyền shortcut | T1 | ULT cfg/models/v8/yolov8.yaml:35 | - [-1, 3, C2f, [512]] # 12 |
| 9.2 | C2f.forward_split: split thay chunk | T1 | ULT nn/modules/block.py:319 | y = self.cv1(x).split((self.c, self.c), 1) |
| 9.2 | Exporter chọn C2f (C3k2 là lớp con) | T1 | ULT engine/exporter.py:908 | elif isinstance(m, C2f) and not is_tf_format: |
| 9.2 | Exporter gán forward_split | T1 | ULT engine/exporter.py:910 | m.forward = m.forward_split |
| 9.2 | Ví dụ YOLOv8n lớp 2: cv1 32 -> 32 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:5 | Conv2d(32, 32, kernel_size=(1, 1) |
| 9.2 | Ví dụ YOLOv8n lớp 2: cv2 48 -> 32 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:10 | Conv2d(48, 32, kernel_size=(1, 1) |
| 9.2 | Ví dụ YOLOv8n lớp 2: Bottleneck Conv 3x3 16 -> 16 (hai lần) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:17 | Conv2d(16, 16, kernel_size=(3, 3) |
| 9.2 | C3k2 kế thừa C2f | T1 | ULT nn/modules/block.py:1072 | class C3k2(C2f): |
| 9.2 | C3k2: khởi tạo khung C2f | T1 | ULT nn/modules/block.py:1098 | super().__init__(c1, c2, n, shortcut, g, e) |
| 9.2 | C3k2: shortcut mặc định True | T1 | ULT nn/modules/block.py:1084 | shortcut: bool = True, |
| 9.2 | C3k2: attn=True thì phần tử là Sequential(Bottleneck, PSABlock) | T1 | ULT nn/modules/block.py:1102 | PSABlock(self.c, attn_ratio=0.5, num_heads=max(self.c // 64, 1)), |
| 9.2 | C3k2: c3k=True thì phần tử là C3k | T1 | ULT nn/modules/block.py:1105 | else C3k(self.c, self.c, 2, shortcut, g) |
| 9.2 | C3k2: còn lại là Bottleneck | T1 | ULT nn/modules/block.py:1107 | else Bottleneck(self.c, self.c, shortcut, g) |
| 9.2 | Bottleneck: kernel mặc định (3, 3), e mặc định 0.5 | T1 | ULT nn/modules/block.py:464 | self, c1: int, c2: int, shortcut: bool = True, g: int = 1, k: tuple[int, int] = (3, 3), e: float = 0.5 |
| 9.2 | Bottleneck: kênh giữa c_ = int(c2 * e) | T1 | ULT nn/modules/block.py:477 | c_ = int(c2 * e)  # hidden channels |
| 9.2 | C3k: n Bottleneck 3x3, e=1.0 | T1 | ULT nn/modules/block.py:1130 | self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, k=(k, k), e=1.0) for _ in range(n))) |
| 9.2 | C3 (cha của C3k): cv1 Conv 1x1 | T1 | ULT nn/modules/block.py:341 | self.cv1 = Conv(c1, c_, 1, 1) |
| 9.2 | C3: cv3 Conv 1x1 trên 2c_ | T1 | ULT nn/modules/block.py:343 | self.cv3 = Conv(2 * c_, c2, 1)  # optional act=FReLU(c2) |
| 9.2 | C3: nối hai nhánh rồi cv3 | T1 | ULT nn/modules/block.py:348 | return self.cv3(torch.cat((self.m(self.cv1(x)), self.cv2(x)), 1)) |
| 9.2 | YOLO26n lớp 4: C3k2 c3k=False | T1 | ULT cfg/models/26/yolo26.yaml:26 | - [-1, 2, C3k2, [512, False, 0.25]] |
| 9.2 | YOLO26n lớp 6: C3k2 c3k=True | T1 | ULT cfg/models/26/yolo26.yaml:28 | - [-1, 2, C3k2, [512, True]] |
| 9.2 | YOLO26n lớp 8: C3k2 c3k=True | T1 | ULT cfg/models/26/yolo26.yaml:30 | - [-1, 2, C3k2, [1024, True]] |
| 9.2 | YOLO26n lớp 13: C3k2 c3k=True | T1 | ULT cfg/models/26/yolo26.yaml:38 | - [-1, 2, C3k2, [512, True]] # 13 |
| 9.2 | YOLO26n lớp 16: C3k2 c3k=True | T1 | ULT cfg/models/26/yolo26.yaml:42 | - [-1, 2, C3k2, [256, True]] # 16 (P3/8-small) |
| 9.2 | YOLO26n lớp 19: C3k2 c3k=True | T1 | ULT cfg/models/26/yolo26.yaml:46 | - [-1, 2, C3k2, [512, True]] # 19 (P4/16-medium) |
| 9.2 | C3k2 đặt legacy=False cho Detect | T1 | ULT nn/tasks.py:2126 | if m is C3k2:  # for M/L/X sizes |
| 9.2 | Ví dụ YOLO26n lớp 2: cv1 32 -> 32 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:122 | Conv2d(32, 32, kernel_size=(1, 1) |
| 9.2 | Ví dụ YOLO26n lớp 2: cv2 48 -> 64 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:127 | Conv2d(48, 64, kernel_size=(1, 1) |
| 9.2 | Ví dụ YOLO26n lớp 2: Bottleneck Conv 3x3 16 -> 8 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:134 | Conv2d(16, 8, kernel_size=(3, 3) |
| 9.2 | Ví dụ YOLO26n lớp 2: Bottleneck Conv 3x3 8 -> 16 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:139 | Conv2d(8, 16, kernel_size=(3, 3) |
| 9.2 | SPPF: cv1 Conv 1x1 c1 -> c1/2, không activation | T1 | ULT nn/modules/block.py:229 | self.cv1 = Conv(c1, c_, 1, 1, act=False) |
| 9.2 | SPPF: cv2 Conv 1x1 trên (n+1) lần c_ | T1 | ULT nn/modules/block.py:230 | self.cv2 = Conv(c_ * (n + 1), c2, 1, 1) |
| 9.2 | SPPF: MaxPool 5x5 stride 1 pad k//2 | T1 | ULT nn/modules/block.py:231 | self.m = nn.MaxPool2d(kernel_size=k, stride=1, padding=k // 2) |
| 9.2 | SPPF: cộng nối tắt khi shortcut và c1 == c2 | T1 | ULT nn/modules/block.py:233 | self.add = shortcut and c1 == c2 |
| 9.2 | SPPF: n lần MaxPool, nối, cv2, cộng x nếu add | T1 | ULT nn/modules/block.py:240 | return y + x if getattr(self, "add", False) else y |
| 9.2 | SPPF: hàng yaml cũ được gán lại activation mặc định cho cv1 | T1 | ULT nn/tasks.py:2194 | if m is SPPF and len(args) <= 3:  # Legacy YAML rows predate the unactivated YOLO26 SPPF. |
| 9.2 | SPPF: gán act cho cv1 | T1 | ULT nn/tasks.py:2196 | block.cv1.act = Conv.default_act |
| 9.2 | YOLOv8n: SPPF chỉ truyền 1024, 5 | T1 | ULT cfg/models/v8/yolov8.yaml:29 | - [-1, 1, SPPF, [1024, 5]] # 9 |
| 9.2 | YOLO26n: SPPF truyền 1024, 5, 3, True | T1 | ULT cfg/models/26/yolo26.yaml:31 | - [-1, 1, SPPF, [1024, 5, 3, True]] # 9 |
| 9.2 | T3 YOLO26n: cv1 của SPPF là Conv trơn | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:63 | Conv INT8 NPU (1,256,20,20),(128,256,1,1),(128) |
| 9.2 | T3 YOLOv8n: cv1 của SPPF là ConvExSwish | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:55 | ConvExSwish INT8 NPU (1,256,20,20),(128,256,1,1),(128) |
| 9.2 | T3 YOLO26n: có Add sau cv2 của SPPF (nối tắt) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:69 | Add INT8 NPU (1,256,20,20),(1,256,20,20) |
| 9.2 | T3 YOLOv8n: Concat 512 kênh của SPPF | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:59 | (1,128,20,20),(1,128,20,20),... (1,512,20,20) |
| 9.2 | T3 YOLOv8n: cv2 của SPPF 512 -> 256 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:60 | (1,512,20,20),(256,512,1,1),(256) |
| 9.2 | Attention: key_dim = int(head_dim * attn_ratio) | T1 | ULT nn/modules/block.py:1305 | self.key_dim = int(self.head_dim * attn_ratio) |
| 9.2 | Attention: qkv Conv 1x1 không activation | T1 | ULT nn/modules/block.py:1309 | self.qkv = Conv(dim, h, 1, act=False) |
| 9.2 | Attention: proj Conv 1x1 không activation | T1 | ULT nn/modules/block.py:1310 | self.proj = Conv(dim, dim, 1, act=False) |
| 9.2 | Attention: pe là Conv depthwise 3x3 (g=dim), không activation | T1 | ULT nn/modules/block.py:1311 | self.pe = Conv(dim, dim, 3, 1, g=dim, act=False) |
| 9.2 | Attention: tách q, k, v theo key_dim, key_dim, head_dim | T1 | ULT nn/modules/block.py:1325 | qkv.view(B, self.num_heads, self.key_dim * 2 + self.head_dim, N).split( |
| 9.2 | Attention: softmax của (q * scale)^T k | T1 | ULT nn/modules/block.py:1333 | attn = ((q * self.scale).transpose(-2, -1) @ k).softmax(dim=-1) |
| 9.2 | Attention: v nhân attn^T cộng pe(v) | T1 | ULT nn/modules/block.py:1334 | x = (v @ attn.transpose(-2, -1)).view(B, C, H, W) + self.pe(v.reshape(B, C, H, W)) |
| 9.2 | Attention: N = H * W | T1 | ULT nn/modules/block.py:1323 | N = H * W |
| 9.2 | Attention: qua proj | T1 | ULT nn/modules/block.py:1335 | x = self.proj(x) |
| 9.2 | PSABlock: attn rồi ffn hai Conv 1x1 (Conv đầu c -> 2c, Conv sau không act) | T1 | ULT nn/modules/block.py:1372 | self.ffn = nn.Sequential(Conv(c, c * 2, 1), Conv(c * 2, c, 1, act=False)) |
| 9.2 | PSABlock: hai phép cộng residual | T1 | ULT nn/modules/block.py:1384 | x = x + self.attn(x) if self.add else self.attn(x) |
| 9.2 | PSABlock: cộng residual của ffn | T1 | ULT nn/modules/block.py:1385 | x = x + self.ffn(x) if self.add else self.ffn(x) |
| 9.2 | C2PSA: c = int(c1 * e) | T1 | ULT nn/modules/block.py:1479 | self.c = int(c1 * e) |
| 9.2 | C2PSA: cv1 Conv 1x1 c1 -> 2c | T1 | ULT nn/modules/block.py:1480 | self.cv1 = Conv(c1, 2 * self.c, 1, 1) |
| 9.2 | C2PSA: cv2 Conv 1x1 2c -> c1 | T1 | ULT nn/modules/block.py:1424 | self.cv2 = Conv(2 * self.c, c1, 1) |
| 9.2 | C2PSA: n PSABlock, số đầu max(c // 64, 1) | T1 | ULT nn/modules/block.py:1483 | self.m = nn.Sequential(*(PSABlock(self.c, attn_ratio=0.5, num_heads=max(self.c // 64, 1)) for _ in range(n))) |
| 9.2 | C2PSA: split (c, c), nửa b qua PSABlock | T1 | ULT nn/modules/block.py:1438 | a, b = self.cv1(x).split((self.c, self.c), dim=1) |
| 9.2 | C2PSA: nối a và b rồi cv2 | T1 | ULT nn/modules/block.py:1441 | return self.cv2(torch.cat((a, b), 1)) |
| 9.2 | C2PSA lớp 10: cv1 256 -> 256 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:265 | Conv2d(256, 256, kernel_size=(1, 1) |
| 9.2 | Attention lớp 10: qkv 128 -> 256 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:278 | Conv2d(128, 256, kernel_size=(1, 1) |
| 9.2 | Attention lớp 10: pe depthwise 128 kênh | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:288 | Conv2d(128, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), groups=128 |
| 9.2 | Attention lớp 10: proj 128 -> 128 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:283 | Conv2d(128, 128, kernel_size=(1, 1) |
| 9.2 | Attention lớp 10: ffn 256 -> 128 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:300 | Conv2d(256, 128, kernel_size=(1, 1) |
| 9.2 | C3k2 lớp 22: Bottleneck Conv 3x3 128 -> 64 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:324 | Conv2d(128, 64, kernel_size=(3, 3) |
| 9.2 | C3k2 lớp 22: Bottleneck Conv 3x3 64 -> 128 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:329 | Conv2d(64, 128, kernel_size=(3, 3) |
| 9.2 | Đầu vào khối attention là lưới 20 x 20, N = 400 token | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | (số học) |
| 9.2 | Số đầu: max(128 // 64, 1) = 2 | T1 tính | ULT nn/modules/block.py:1483 | (số học) |
| 9.2 | ONNX YOLO26n (đường RKNN): Transpose 4, MatMul 4 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Transpose": 4, "MatMul": 4 |
| 9.2 | ONNX YOLO26n (đường RKNN): Softmax 2 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Softmax": 2 |
| 9.2 | T3: lớp exSDPAttention thứ nhất (lớp 10) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:77 | exSDPAttention INT8 NPU (2,32,1,400),(2,32,1,400) |
| 9.2 | T3: lớp exSDPAttention thứ hai (lớp 22) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:162 | exSDPAttention INT8 NPU (2,32,1,400),(2,32,1,400) |
| 9.2 | Detect: c2, c3 là kênh trung gian của nhánh hộp và nhánh lớp | T1 | ULT nn/modules/head.py:122 | c2, c3 = max((16, ch[0] // 4, self.reg_max * 4)), max(ch[0], min(self.nc, 100))  # channels |
| 9.2 | Detect: nhánh hộp Conv 3x3, Conv 3x3, Conv2d 1x1 ra 4 * reg_max | T1 | ULT nn/modules/head.py:124 | nn.Sequential(Conv(x, c2, 3), Conv(c2, c2, 3), nn.Conv2d(c2, 4 * self.reg_max, 1)) for x in ch |
| 9.2 | Detect legacy: nhánh lớp Conv 3x3, Conv 3x3, Conv2d 1x1 ra nc | T1 | ULT nn/modules/head.py:127 | nn.Sequential(Conv(x, c3, 3), Conv(c3, c3, 3), nn.Conv2d(c3, self.nc, 1)) for x in ch |
| 9.2 | Detect không legacy: nhánh lớp DWConv 3x3 + Conv 1x1 | T1 | ULT nn/modules/head.py:131 | nn.Sequential(DWConv(x, x, 3), Conv(x, c3, 1)), |
| 9.2 | Detect không legacy: lần hai DWConv 3x3 + Conv 1x1 | T1 | ULT nn/modules/head.py:132 | nn.Sequential(DWConv(c3, c3, 3), Conv(c3, c3, 1)), |
| 9.2 | Detect không legacy: Conv2d 1x1 ra nc | T1 | ULT nn/modules/head.py:133 | nn.Conv2d(c3, self.nc, 1), |
| 9.2 | Detect: dfl là DFL khi reg_max > 1, ngược lại Identity | T1 | ULT nn/modules/head.py:138 | self.dfl = DFL(self.reg_max) if self.reg_max > 1 else nn.Identity() |
| 9.2 | DFL: Conv 1x1 c1 -> 1 cố định | T1 | ULT nn/modules/block.py:73 | self.conv = nn.Conv2d(c1, 1, 1, bias=False).requires_grad_(False) |
| 9.2 | DFL: softmax trên c1 bin rồi Conv | T1 | ULT nn/modules/block.py:81 | return self.conv(x.view(b, 4, self.c1, a).transpose(2, 1).softmax(1)).view(b, 4, a) |
| 9.2 | Detect: end2end sao chép cv2, cv3 thành one2one | T1 | ULT nn/modules/head.py:141 | self.one2one_cv2 = copy.deepcopy(self.cv2) |
| 9.2 | Detect: fuse xóa nhánh không dùng | T1 | ULT nn/modules/head.py:281 | """Remove the unused detection branch for inference.""" |
| 9.2 | Detect: forward chạy nhánh một-nhiều trước | T1 | ULT nn/modules/head.py:183 | preds = self.forward_head(x, **self.one2many) |
| 9.2 | Detect: chọn nhánh theo end2end | T1 | ULT nn/modules/head.py:190 | y = self._inference(preds["one2one" if self.end2end else "one2many"] if "one2one" in preds else preds) |
| 9.2 | Detect: end2end gọi postprocess | T1 | ULT nn/modules/head.py:192 | y = self.postprocess(y.permute(0, 2, 1)) |
| 9.2 | Detect: giải mã qua DFL, anchors, stride | T1 | ULT nn/modules/head.py:215 | dbox = self.decode_bboxes(self.dfl(x["boxes"]), self.anchors.unsqueeze(0)) * self.strides |
| 9.2 | Detect: điểm lớp qua sigmoid, nối với hộp | T1 | ULT nn/modules/head.py:206 | return torch.cat((dbox, x["scores"].sigmoid()), 1) |
| 9.2 | Detect: hộp xywh khi không end2end, xyxy khi end2end | T1 | ULT nn/modules/head.py:237 | xywh=xywh and not self.end2end and not self.xyxy, |
| 9.2 | Detect.postprocess: split hộp và điểm | T1 | ULT nn/modules/head.py:254 | boxes, scores, *extra = preds.split( |
| 9.2 | Detect.postprocess: top-k theo max_det | T1 | ULT nn/modules/head.py:255 | scores, conf, idx = self.get_topk_index(scores, self.max_det) |
| 9.2 | Detect.postprocess: gather hộp theo chỉ số | T1 | ULT nn/modules/head.py:256 | return torch.cat([self._gather(boxes, idx), scores, conf, *(self._gather(e, idx) for e in extra)], dim=-1) |
| 9.2 | Detect.postprocess: định dạng [x1, y1, x2, y2, max_class_prob, class_index] | T1 | ULT nn/modules/head.py:246 | [x1, y1, x2, y2, class_probs, extra] |
| 9.2 | Detect.postprocess: ra min(max_det, số anchor) hộp | T1 | ULT nn/modules/head.py:250 | (torch.Tensor): Processed predictions with shape (batch_size, min(max_det, num_anchors), 6 + extra) and last |
| 9.2 | Detect.postprocess: cột cuối là max_class_prob, class_index | T1 | ULT nn/modules/head.py:251 | dimension format [x1, y1, x2, y2, max_class_prob, class_index, extra]. |
| 9.2 | Detect: max_det mặc định 300 | T1 | ULT nn/modules/head.py:82 | max_det = 300  # max_det |
| 9.2 | legacy mặc định True trong tasks.py | T1 | ULT nn/tasks.py:2011 | legacy = True  # backward compatibility for v3/v5/v8/v9 models |
| 9.2 | C3k2 đặt legacy = False | T1 | ULT nn/tasks.py:2127 | legacy = False |
| 9.2 | Detect nhận legacy từ tasks.py | T1 | ULT nn/tasks.py:2169 | m.legacy = legacy |
| 9.2 | Validator: end2end = (nms is False) | T1 | ULT engine/validator.py:163 | model.end2end = self.args.nms is False |
| 9.2 | Exporter: end2end = (nms is False) | T1 | ULT engine/exporter.py:683 | model.end2end = self.args.nms is False |
| 9.2 | Exporter: rknn nằm trong danh sách tắt end2end | T1 | ULT engine/exporter.py:685 | if fmt in {"rknn", "ncnn", "executorch", "paddle", "imx", "edgetpu", "qnn"}: |
| 9.2 | Exporter: tắt end2end vì không có top-k | T1 | ULT engine/exporter.py:686 | # Disable the end2end branch for formats without top-k support |
| 9.2 | nms mặc định: NMS ngoài đồ thị | T1 | ULT cfg/default.yaml:61 | None: external NMS (default) |
| 9.2 | nms=False: head NMS-free nếu có | T1 | ULT cfg/default.yaml:61 | False: NMS-free head if available |
| 9.2 | YOFF: nhánh một-một là mặc định, tối đa 300 hộp, shape (N, 300, 6) | T2 | YOFF tr.6 | One-to-One Head (default). |
| 9.2 | YOFF: nhánh một-một không cần NMS, ra tối đa 300 hộp | T2 | YOFF tr.6 | outputting at most 300 detections per image (shape (N, 300, 6) |
| 9.2 | YOFF: nhánh một-nhiều dùng NMS khi suy luận | T2 | YOFF tr.6 | This head uses NMS at inference |
| 9.2 | YOFF: nhánh một-nhiều ra (N, nc + 4, 8400) | T2 | YOFF tr.6 | producing outputs of shape (N, nc + 4, 8400) |
| 9.2 | UDOC: nhánh một-nhiều là mặc định, dùng NMS | T1 | UDOC ultralytics_docs_models_yolo26.txt:81 | The default one-to-many path uses NMS for accuracy. |
| 9.2 | UDOC: nhánh một-một khi nms=False ra (N, 300, 6) | T1 | UDOC ultralytics_docs_models_yolo26.txt:143 | Produces end-to-end predictions without NMS, outputting (N, 300, 6) |
| 9.2 | UDOC: predict và validation mặc định nhánh một-nhiều | T1 | UDOC ultralytics_docs_models_yolo26.txt:156 | Prediction and validation default to the one-to-many head for accuracy. |
| 9.2 | Đầu ra end2end bật: [1, 300, 6] | T1 tính | LOG 2026-10-10_yolo-arch/out/yolo26n_export_end2end.json | "out": [ [ 1, 300, 6 ] ] |
| 9.2 | Đầu ra end2end tắt: [1, 9, 8400] | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 23 \| [16, 19, 22] \| Detect \| 120,443 \| 0.435 \| [1, 9, 8400] \| |
| 9.2 | Detect YOLOv8n (log): Conv2d(64, 64, kernel_size=(3, 3) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:34 | Conv2d(64, 64, kernel_size=(3, 3) |
| 9.2 | Detect YOLOv8n (log): Conv2d(64, 64, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:43 | Conv2d(64, 64, kernel_size=(1, 1) |
| 9.2 | Detect YOLOv8n (log): Conv2d(64, 5, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:84 | Conv2d(64, 5, kernel_size=(1, 1) |
| 9.2 | Detect YOLOv8n (log): Conv2d(128, 64, kernel_size=(3, 3) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:47 | Conv2d(128, 64, kernel_size=(3, 3) |
| 9.2 | Detect YOLOv8n (log): Conv2d(256, 64, kernel_size=(3, 3) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:60 | Conv2d(256, 64, kernel_size=(3, 3) |
| 9.2 | Detect YOLOv8n (log): Conv2d(16, 1, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:114 | Conv2d(16, 1, kernel_size=(1, 1) |
| 9.2 | Detect YOLO26n (log): Conv2d(64, 16, kernel_size=(3, 3) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:373 | Conv2d(64, 16, kernel_size=(3, 3) |
| 9.2 | Detect YOLO26n (log): Conv2d(16, 16, kernel_size=(3, 3) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:378 | Conv2d(16, 16, kernel_size=(3, 3) |
| 9.2 | Detect YOLO26n (log): Conv2d(16, 4, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:382 | Conv2d(16, 4, kernel_size=(1, 1) |
| 9.2 | Detect YOLO26n (log): Conv2d(64, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), groups=64 | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:415 | Conv2d(64, 64, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), groups=64 |
| 9.2 | Detect YOLO26n (log): Conv2d(64, 64, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:420 | Conv2d(64, 64, kernel_size=(1, 1) |
| 9.2 | Detect YOLO26n (log): Conv2d(64, 5, kernel_size=(1, 1) | T1 tính | LOG 2026-10-10_yolo-arch/out/structure_and_ops.log:437 | Conv2d(64, 5, kernel_size=(1, 1) |
| 9.2 | 8400 vị trí = 80 x 80 + 40 x 40 + 20 x 20 | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | (số học) |
| 9.2 | NMS chạy ở host: cfg nms mặc định là NMS ngoài | T1 | ULT cfg/default.yaml:61 | None: external NMS (default) |
| 9.3 | Exporter: nhánh end2end tắt cho rknn | T1 | ULT engine/exporter.py:687 | model.end2end = False |
| 9.3 | Exporter: _NormalizeCoords khi rknn, quantize 8, detect, end2end tắt | T1 | ULT engine/exporter.py:1063 | self.args.format == "rknn" |
| 9.3 | Exporter: điều kiện quantize == 8 | T1 | ULT engine/exporter.py:1064 | and self.args.quantize == 8 |
| 9.3 | Exporter: điều kiện task detect, segment, pose, obb | T1 | ULT engine/exporter.py:1105 | and self.model.task in {"detect", "segment", "pose", "obb"} |
| 9.3 | Exporter: điều kiện end2end tắt | T1 | ULT engine/exporter.py:1106 | and not self.metadata["end2end"] |
| 9.3 | Exporter: lý do chuẩn hóa tọa độ | T1 | ULT engine/exporter.py:1101 | # Normalize coordinates by input size so RKNN's per-tensor INT8 scale preserves class scores. |
| 9.3 | Exporter: import _NormalizeCoords | T1 | ULT engine/exporter.py:1108 | from ultralytics.utils.export.engine import _NormalizeCoords |
| 9.3 | Exporter: torch2onnx với input images | T1 | ULT engine/exporter.py:1125 | input_names=["images"], |
| 9.3 | torch2onnx: output mặc định output0 | T1 | ULT utils/export/engine.py:98 | output_names = ["output0"] |
| 9.3 | Exporter: opset = min(opset or 19, 19) | T1 | ULT engine/exporter.py:1538 | self.args.opset = min(self.args.opset or 19, 19)  # rknn-toolkit expects opset<=19 |
| 9.3 | cfg: simplify mặc định True | T1 | ULT cfg/default.yaml:90 | simplify: True |
| 9.3 | Exporter: onnxslim.slim | T1 | ULT engine/exporter.py:1139 | model_onnx = onnxslim.slim(model_onnx) |
| 9.3 | Exporter: INT8 xóa file ONNX sau khi build | T1 | ULT engine/exporter.py:1565 | if self.args.quantize == 8:  # INT8 graphs hold normalized coordinates, so they are not reusable |
| 9.3 | Exporter: dataset.txt ghi danh sách ảnh calibration | T1 | ULT engine/exporter.py:1551 | rknn_dataset = output_dir / "dataset.txt" |
| 9.3 | _NormalizeCoords: chia 4 tọa độ hộp cho [w, h, w, h] | T1 | ULT utils/export/engine.py:34 | box_wh = torch.tensor([self.w, self.h, self.w, self.h], dtype=det.dtype, device=det.device).view(1, 4, 1) |
| 9.3 | _NormalizeCoords: lấy 4 kênh đầu chia cho box_wh | T1 | ULT utils/export/engine.py:35 | parts = [det[:, :4] / box_wh] |
| 9.3 | _NormalizeCoords: nối lại bằng concat | T1 | ULT utils/export/engine.py:47 | det = torch.cat(parts, dim=1) |
| 9.3 | onnx2rknn: config mean 0, std 255, target_platform | T1 | ULT utils/export/rknn.py:74 | config = {"mean_values": [[0, 0, 0]], "std_values": [[255, 255, 255]], "target_platform": name} |
| 9.3 | onnx2rknn: load_onnx | T1 | ULT utils/export/rknn.py:76 | rknn.load_onnx(model=onnx_file) |
| 9.3 | onnx2rknn: build với dataset khi INT8 | T1 | ULT utils/export/rknn.py:79 | build_kwargs["dataset"] = str(dataset) |
| 9.3 | onnx2rknn: build gọi rknn_batch_size | T1 | ULT utils/export/rknn.py:80 | rknn.build(**build_kwargs, rknn_batch_size=batch) |
| 9.3 | onnx2rknn: export_rknn ghi file .rknn | T1 | ULT utils/export/rknn.py:81 | rknn.export_rknn( |
| 9.3 | YOLOv8n: op ONNX của YOLO(...).export(format="onnx"), opset 19, onnxslim | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Conv": 64, "Sigmoid": 58, "Mul": 58, "Concat": 17, "Split": 8, "Add": 8, "Reshape": 8, "MaxPool": 3, "Resize": 2, "Slice": 2, "Sub": 2, "Transpose": 1, "Softmax": 1, "Div": 1 |
| 9.3 | YOLOv8n: tổng nút ONNX (số học: cộng các op ở dòng trên) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | (số học) |
| 9.3 | YOLO26n: op ONNX của YOLO(...).export(format="onnx"), opset 19, onnxslim | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Conv": 102, "Mul": 90, "Sigmoid": 88, "Concat": 23, "Add": 22, "Reshape": 12, "Split": 11, "Transpose": 4, "MatMul": 4, "MaxPool": 3, "Softmax": 2, "Resize": 2, "Slice": 2, "Sub": 2, "Div": 1 |
| 9.3 | YOLO26n: tổng nút ONNX (số học: cộng các op ở dòng trên) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | (số học) |
| 9.3 | YOLOv8n: op ONNX thật đưa vào onnx2rknn (có _NormalizeCoords) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Conv": 64, "Sigmoid": 58, "Mul": 58, "Concat": 18, "Split": 8, "Add": 8, "Reshape": 8, "Slice": 4, "MaxPool": 3, "Resize": 2, "Sub": 2, "Div": 2, "Transpose": 1, "Softmax": 1 |
| 9.3 | YOLOv8n: tổng nút ONNX đường RKNN (số học: cộng các op ở dòng trên) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | (số học) |
| 9.3 | YOLOv8n: đầu ra ONNX đường RKNN [1, 9, 8400] | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "output": [ [ 1, 9, 8400 ] ] |
| 9.3 | YOLO26n: op ONNX thật đưa vào onnx2rknn (có _NormalizeCoords) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "Conv": 102, "Mul": 90, "Sigmoid": 88, "Concat": 24, "Add": 22, "Reshape": 12, "Split": 11, "Transpose": 4, "MatMul": 4, "Slice": 4, "MaxPool": 3, "Softmax": 2, "Resize": 2, "Sub": 2, "Div": 2 |
| 9.3 | YOLO26n: tổng nút ONNX đường RKNN (số học: cộng các op ở dòng trên) | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | (số học) |
| 9.3 | YOLO26n: đầu ra ONNX đường RKNN [1, 9, 8400] | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "output": [ [ 1, 9, 8400 ] ] |
| 9.3 | YOLOv8n: số lớp RKNN loại ConvExSwish (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | ConvExSwish 57 0 0 11184 11184 59.87% |
| 9.3 | YOLOv8n: số lớp RKNN loại exSoftmax13 (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | exSoftmax13 1 0 0 2105 2105 11.27% |
| 9.3 | YOLOv8n: số lớp RKNN loại Concat (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Concat 17 0 0 1625 1625 8.70% |
| 9.3 | YOLOv8n: số lớp RKNN loại Transpose (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Transpose 1 799 0 0 799 4.28% |
| 9.3 | YOLOv8n: số lớp RKNN loại Split (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Split 9 0 0 684 684 3.66% |
| 9.3 | YOLOv8n: số lớp RKNN loại Conv (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Conv 7 0 0 634 634 3.39% |
| 9.3 | YOLOv8n: số lớp RKNN loại Add (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Add 8 0 0 470 470 2.52% |
| 9.3 | YOLOv8n: số lớp RKNN loại Reshape (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Reshape 7 0 0 406 406 2.17% |
| 9.3 | YOLOv8n: số lớp RKNN loại Resize (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Resize 2 0 0 200 200 1.07% |
| 9.3 | YOLOv8n: số lớp RKNN loại Mul (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Mul 2 0 0 183 183 0.98% |
| 9.3 | YOLOv8n: số lớp RKNN loại Sub (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Sub 2 0 0 180 180 0.96% |
| 9.3 | YOLOv8n: số lớp RKNN loại MaxPool (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | MaxPool 3 0 0 103 103 0.55% |
| 9.3 | YOLOv8n: số lớp RKNN loại Sigmoid (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | Sigmoid 1 0 0 87 87 0.47% |
| 9.3 | YOLOv8n: số lớp RKNN loại OutputOperator (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | OutputOperator 1 12 0 0 12 0.06% |
| 9.3 | YOLOv8n: số lớp RKNN loại InputOperator (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | InputOperator 1 10 0 0 10 0.05% |
| 9.3 | YOLO26n: số lớp RKNN loại ConvExSwish (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | ConvExSwish 87 0 0 17094 17094 60.73% |
| 9.3 | YOLO26n: số lớp RKNN loại Concat (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Concat 23 0 0 2681 2681 9.53% |
| 9.3 | YOLO26n: số lớp RKNN loại exSDPAttention (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | exSDPAttention 2 0 0 2455 2455 8.72% |
| 9.3 | YOLO26n: số lớp RKNN loại Add (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Add 18 0 0 1384 1384 4.92% |
| 9.3 | YOLO26n: số lớp RKNN loại Split (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Split 12 0 0 1219 1219 4.33% |
| 9.3 | YOLO26n: số lớp RKNN loại Reshape (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Reshape 13 0 0 1052 1052 3.74% |
| 9.3 | YOLO26n: số lớp RKNN loại Conv (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Conv 11 0 0 912 912 3.24% |
| 9.3 | YOLO26n: số lớp RKNN loại ConvAdd (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | ConvAdd 4 0 0 303 303 1.08% |
| 9.3 | YOLO26n: số lớp RKNN loại Resize (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Resize 2 0 0 282 282 1.00% |
| 9.3 | YOLO26n: số lớp RKNN loại Mul (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Mul 2 0 0 227 227 0.81% |
| 9.3 | YOLO26n: số lớp RKNN loại MaxPool (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | MaxPool 3 0 0 220 220 0.78% |
| 9.3 | YOLO26n: số lớp RKNN loại Sub (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Sub 2 0 0 169 169 0.60% |
| 9.3 | YOLO26n: số lớp RKNN loại Sigmoid (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | Sigmoid 1 0 0 127 127 0.45% |
| 9.3 | YOLO26n: số lớp RKNN loại OutputOperator (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | OutputOperator 1 12 0 0 12 0.04% |
| 9.3 | YOLO26n: số lớp RKNN loại InputOperator (bảng xếp hạng thời gian của eval_perf) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | InputOperator 1 9 0 0 9 0.03% |
| 9.3 | YOLOv8n: tổng 119 lớp | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:133 | 119 OutputOperator |
| 9.3 | YOLO26n: tổng 182 lớp | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:196 | 182 OutputOperator |
| 9.3 | YOLOv8n: lớp Transpose chạy CPU, tên lớp thuộc dfl | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:118 | Transpose:/model/model.22/dfl/Reshape_1_output_0_rs |
| 9.3 | Ba core_mask (AUTO, CORE_0, CORE_0_1_2) cho cùng số lớp theo loại, ở cả hai model (script của bộ hình so ba file) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0.txt | (số học) |
| 9.3 | YOLO26n: 180 lớp NPU, 0 lớp CPU ngoài Input và Output (đếm cột Target) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.3 | YOLOv8n: 116 lớp NPU, 1 lớp CPU ngoài Input và Output (đếm cột Target) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | (số học) |
| 9.3 | Conv ONNX = ConvExSwish + Conv + ConvAdd: 64 = 57 + 7 + 0; 102 = 87 + 11 + 4 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.3 | Add ONNX YOLO26n = Add + ConvAdd: 22 = 18 + 4; YOLOv8n 8 = 8 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.3 | Số lớp RKNN lệch số nút ONNX: ví dụ Div 2 ở ONNX, không có lớp Div | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.3 | Điều kiện T3: 40 ảnh calibration, trọng số ngẫu nhiên, nc=5 | T3 | LOG 2026-10-10_yolo-phaseA/README.md | Calibration 40 ảnh letterbox |
| 9.3 | metadata của YOLO26n xuất qua repo ghi end2end: false | T3 | LOG 2026-10-10_yolo-phaseA/raw/metadata_yolo26n.yaml:29 | end2end: false |
| 9.3 | Đường xuất qua ai.core.rknn.baseline.export_rknn (opset 19 + onnxslim) | T3 | LOG 2026-10-10_yolo-phaseA/build_real_path.py:2 | which calls ultralytics export(format='rknn'): opset 19 + onnxslim |
| 9.3 | UG232: quy tắc ghép chỉ liệt kê Conv+Sigmoid(Tanh/Elu/Silu...) | T1 | UG232 tr.142 | Conv+Sigmoid(Tanh/Elu/Silu...) |
| 9.3 | UG232: quy tắc ghép subgraph chỉ có GLU và LayerNorm | T1 | UG232 tr.148 | Split + Sigmoid + Mul -> GLU |
| 9.3 | Tên ConvExSwish không có trong OPL và UG232 | T1 | (không có) | (unknown) |
| 9.3 | Quy tắc nhận chuỗi MatMul, Softmax, MatMul thành exSDPAttention | T1 | (không có) | (unknown) |
| 9.3 | Cách gộp hoặc tách Concat, Slice, Div, Reshape của trình biên dịch | T1 | (không có) | (unknown) |
| 9.4 | Concat: mục NPU 3.2.4, int8, float16 | T1 | OPL tr.58 | T: int8(Tensor), float16(Tensor) |
| 9.4 | Concat: axis ∈ {0, 1, 2, 3} | T1 | OPL tr.58 | axis ∈ {0, 1, 2, 3} |
| 9.4 | Convolution: mục NPU 3.2.5 | T1 | OPL tr.58 | 3.2.5 Convolution |
| 9.4 | Convolution: kernel_h ∈ [1, 31] | T1 | OPL tr.58 | kernel_h ∈ [1, 31] |
| 9.4 | Convolution: stride_h ∈ [1, 7] | T1 | OPL tr.59 | stride_h ∈ [1, 7] |
| 9.4 | Convolution: int8, float16 | T1 | OPL tr.59 | T1: int8(Tensor), float16(Tensor) |
| 9.4 | Convolution: đa lõi 支持 | T1 | OPL tr.59 | 3.2.6 Depthwise Convolution |
| 9.4 | Depthwise Convolution: mục NPU 3.2.6, kernel_h ∈ [1, 8] | T1 | OPL tr.59 | kernel_h ∈ [1, 8] |
| 9.4 | Depthwise Convolution: đa lõi 支持 | T1 | OPL tr.60 | 多核联合: 支持 |
| 9.4 | ConvolutionSwish: mục NPU 3.2.17, Convolution với Swish | T1 | OPL tr.63 | 3.2.17 ConvolutionSwish |
| 9.4 | ConvolutionSwish: đa lõi 暂不支持 | T1 | OPL tr.63 | Output = Swish(Conv(Input)) 说明及规格限制同Convolution 其他支持 多核联合: 暂不支持 |
| 9.4 | Add: mục NPU 3.2.1, đa lõi 支持 | T1 | OPL tr.56 | 3.2.1 Add |
| 9.4 | Add: đa lõi 支持 | T1 | OPL tr.56 | 多核联合: 支持 |
| 9.4 | Mul: mục NPU 3.2.41 | T1 | OPL tr.77 | 3.2.41 Mul |
| 9.4 | Mul: đa lõi 支持 (UG232 tr.75 không liệt kê Mul) | T1 | OPL tr.77 | C = A * B |
| 9.4 | Sub: broadcast chỉ [b, c, 1, 1] hoặc scalar | T1 | OPL tr.91 | 3.2.60 Sub |
| 9.4 | Sub: đa lõi 不支持 | T1 | OPL tr.92 | 多核联合: 不支持 |
| 9.4 | Div: T1 chỉ float16, đa lõi 不支持 | T1 | OPL tr.67 | T1: float16(Tensor) |
| 9.4 | MaxPool: mục NPU 3.2.44 | T1 | OPL tr.79 | 3.2.44 MaxPool |
| 9.4 | MaxPool: kernel_h ∈ (0, 7] | T1 | OPL tr.79 | kernel_h ∈ (0, 7] |
| 9.4 | MaxPool: strides_h ∈ (0, 8] | T1 | OPL tr.79 | strides_h ∈ (0, 8] |
| 9.4 | MaxPool: ceil_mode không hỗ trợ | T1 | OPL tr.79 | 使用 ceil 或 floor 的方式计算输出的 shape : 不支持 |
| 9.4 | MaxPool: pad_top ∈ [0, 7] | T1 | OPL tr.80 | pad_top ∈ [0, 7] |
| 9.4 | MaxPool: ONNX kernel 5, pads 2, strides 1, ceil_mode 0 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "maxpool_attrs": [ { "ceil_mode": 0, "dilations": [ 1, 1 ], "kernel_shape": [ 5, 5 ], "pads": [ 2, 2, 2, 2 ], "strides": [ 1, 1 ] } ] |
| 9.4 | Resize: mục NPU 3.2.54, int8, float16 | T1 | OPL tr.86 | 3.2.54 Resize |
| 9.4 | Resize: coordinate_transformation_mode chỉ half_pixel, pytorch_half_pixel, align_corners | T1 | OPL tr.87 | 目前仅支持 half_pixel，pytorch_half_pixel，align_corners 三种 |
| 9.4 | Resize: nearest_mode không hỗ trợ đặt | T1 | OPL tr.87 | nearest_mode : strings（默认值为”round_prefer_floor”） – 目前不支持设置 |
| 9.4 | Resize: chỉ phóng nguyên lần 2 đến 8 | T1 | OPL tr.87 | 缩放倍数为 2‑8 的整数倍 |
| 9.4 | Resize: đa lõi 不支持 | T1 | OPL tr.87 | 多核联合: 不支持 |
| 9.4 | Resize ONNX: nearest, asymmetric, floor, scale 2 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "coordinate_transformation_mode": "asymmetric", "cubic_coeff_a": -0.75, "mode": "nearest", "nearest_mode": "floor" |
| 9.4 | Upsample chỉ có mục CPU 4.67 | T1 | OPL tr.329 | 4.67 Upsample |
| 9.4 | UG232: toolkit đổi Resize thành ConvTranspose | T1 | UG232 tr.176 | the RKNN-Toolki2 will convert Reszie to ConvTranspose |
| 9.4 | UG232: optimization_level=2 đưa Resize về CPU | T1 | UG232 tr.176 | At this time, the Resize Op will use the CPU |
| 9.4 | Split: mục NPU 3.2.59, axis ∈ {0, 1, 2, 3} | T1 | OPL tr.91 | 3.2.59 Split |
| 9.4 | Slice: mục NPU 3.2.55, NPU khi steps == [1, 1, 1, 1] | T1 | OPL tr.88 | 只有 steps == [1,1,1,1] 时，才可 通过 NPU 运行 Slice OP |
| 9.4 | Softmax: mục NPU 3.2.56, axis 1 hoặc 3, đa lõi 尚不支持 | T1 | OPL tr.89 | 做 softmax 的轴: 1,3，即 channel 和 width 方向 |
| 9.4 | exSoftmax13: mục NPU 3.2.57, đa lõi 尚不支持 | T1 | OPL tr.89 | 3.2.57 exSoftmax13 |
| 9.4 | Sigmoid: mục NPU 3.2.63, đa lõi 尚不支持 | T1 | OPL tr.95 | 3.2.63 Sigmoid |
| 9.4 | Sigmoid: đa lõi 尚不支持 | T1 | OPL tr.95 | 多核联合: 尚不支持 |
| 9.4 | Transpose: mục NPU 3.2.62, điều kiện theo perm | T1 | OPL tr.93 | 3.2.62 Transpose |
| 9.4 | Transpose: perm=[0,1,3,2]: h1%16=0, h1*w1<16*p | T1 | OPL tr.93 | perm=[0,1,3,2] * T1: h1%16=0, h1*w1<16*p, h1*w1<2*q |
| 9.4 | Transpose: đa lõi 暂不支持 | T1 | OPL tr.95 | 多核联合: 暂不支持 |
| 9.4 | Reshape: mục NPU 3.2.53, đa lõi 尚不支持 | T1 | OPL tr.86 | 3.2.53 Reshape |
| 9.4 | MatMul: chỉ có mục CPU 4.33, không giới hạn | T1 | OPL tr.324 | 4.33 MatMul –描述: 多维矩阵相乘 –规格约束: 无限制 |
| 9.4 | exMatMul: mục NPU 3.2.76, đa lõi 不支持 | T1 | OPL tr.102 | 3.2.76 exMatMul |
| 9.4 | exSDPAttention: mục NPU 3.2.78, channel ∈ (0, 8192] | T1 | OPL tr.104 | 3.2.78 exSDPAttention |
| 9.4 | exSDPAttention: đa lõi 不支持 | T1 | OPL tr.105 | 多核联合: 不支持 |
| 9.4 | exSwish: mục NPU 3.2.69 (rời) | T1 | OPL tr.98 | 3.2.69 exSwish |
| 9.4 | TopK: chỉ có mục CPU 4.96 | T1 | OPL tr.333 | 4.96 TopK |
| 9.4 | GatherElements: chỉ có mục CPU 4.75 | T1 | OPL tr.330 | 4.75 GatherElements |
| 9.4 | ReduceMax: chỉ có mục CPU 4.44 | T1 | OPL tr.325 | 4.44 ReduceMax |
| 9.4 | Mod: chỉ có mục CPU 4.72 | T1 | OPL tr.329 | 4.72 Mod |
| 9.4 | Cast: chỉ có mục CPU 4.7 | T1 | OPL tr.320 | 4.7 Cast |
| 9.4 | Flatten: chỉ có mục CPU 4.19 | T1 | OPL tr.322 | 4.19 Flatten |
| 9.4 | OPSUP: TopK Not Supported | T1 | OPSUP dòng 189 | TopK \| Not Supported |
| 9.4 | ONNX end2end bật: TopK | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "TopK": 2 |
| 9.4 | ONNX end2end bật: GatherElements | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "GatherElements": 3 |
| 9.4 | ONNX end2end bật: ReduceMax | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "ReduceMax": 1 |
| 9.4 | ONNX end2end bật: Mod | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Mod": 1 |
| 9.4 | ONNX end2end bật: Cast | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Cast": 1 |
| 9.4 | ONNX end2end bật: Flatten | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/ops_via_exporter.json | "Flatten": 1 |
| 9.4 | UG232 tr.75: danh sách op đã có chia nhiệm vụ đa lõi | T1 | UG232 tr.75 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu |
| 9.4 | UG232 Table 8-2: Depthwise Conv INT8 kênh 64 | T1 | UG232 tr.145 | Int8 32 32 64 16 |
| 9.4 | UG232 tr.142: Conv+Sigmoid(Tanh/Elu/Silu...) | T1 | UG232 tr.142 | Conv+Sigmoid(Tanh/Elu/Silu...) |
| 9.4 | UG232 tr.142: Conv+Add | T1 | UG232 tr.142 | Conv+Add |
| 9.4 | UG232 tr.142: Conv+Activation+Add | T1 | UG232 tr.142 | Conv+Activation+Add |
| 9.4 | UG232 tr.142: Conv+Activation+Pooling thuộc cột kế hoạch tương lai | T1 | UG232 tr.142 | Conv+Activation+Pooling |
| 9.4 | API232: enable_flash_attention mặc định False, nhắc exSDPAttention | T1 | API232 tr.10 | enable_flash_attention: Whether to enable Flash Attention. default is False. |
| 9.4 | API232: mô tả exSDPAttention trong Operator List | T1 | API232 tr.10 | please see the 'exSDPAttention' description in 'RKNN Compiler Support Operator List' |
| 9.4 | T3: ConvExSwish chỉ lõi 0 ở CORE_0_1_2 (YOLO26n, 87 lớp; đếm cột WorkLoad) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt | (số học) |
| 9.4 | T3: ConvExSwish chỉ lõi 0 ở CORE_0_1_2 (YOLOv8n, 57 lớp; đếm cột WorkLoad) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_CORE_0_1_2.txt | (số học) |
| 9.4 | T3: bản đã huấn luyện (lượt 3) cùng số lớp và cùng WorkLoad theo loại với YOLOv8n ngẫu nhiên (script kiểm) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/trained_silu_5c_CORE_0_1_2_layers.txt | (số học) |
| 9.4 | T3: ví dụ một lớp ConvExSwish chỉ lõi 0 ở CORE_0_1_2 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt:16 | 100.0%/0.0%/0.0% |
| 9.4 | T3: ví dụ một lớp Concat chia ba lõi | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt:61 | 35.0%/35.0%/30.0% |
| 9.4 | T3: Concat, Add, Conv, ConvAdd chia ba lõi; Split, MaxPool, Resize, Mul, Sub, exSDPAttention lõi 0 (đếm WorkLoad của file CORE_0_1_2) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_CORE_0_1_2.txt | (số học) |
| 9.4 | T3: YOLOv8n Conv trơn 6/7, Concat 15/17, Add 8/8 chia ba lõi; Split 9/9, MaxPool 3/3, Resize 2/2, Sub 2/2, Mul 2/2, exSoftmax13 1/1 lõi 0 (đếm WorkLoad) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_CORE_0_1_2.txt | (số học) |
| 9.4 | T3: depthwise 3x3 của YOLO26n: 8 lớp, 6 ConvExSwish và 2 Conv, MacUsage 0.30 đến 1.24% (đếm từ AUTO) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.4 | T3: một lớp depthwise ConvExSwish ở nhánh lớp, MacUsage 1.24 | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:120 | (1,64,80,80),(1,64,3,3),(64) |
| 9.4 | T3: lớp pe của attention là Conv | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:76 | Conv:/model/model.10/m/m.0/attn/pe/conv/Conv |
| 9.4 | T3: ConvAdd ở proj của attention | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:80 | Conv:/model/model.10/m/m.0/attn/proj/conv/Conv_ConvAdd |
| 9.4 | T3: ConvAdd ở ffn.1 của attention | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:82 | Conv:/model/model.10/m/m.0/ffn/ffn.1/conv/Conv_ConvAdd |
| 9.4 | T3: Conv trơn ở đầu ra của Detect (cv2.0.2) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:124 | Conv:/model/model.23/cv2.0/cv2.0.2/Conv |
| 9.4 | T3: lớp DFL conv trơn của YOLOv8n | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:117 | Conv:/model/model.22/dfl/conv/Conv |
| 9.4 | T3: lớp exSoftmax13 của YOLOv8n | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt:116 | exSoftmax13 INT8 NPU |
| 9.4 | T3: Resize INT8 NPU (YOLO26n) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt:85 | Resize INT8 NPU |
| 9.4 | T3: Resize ở optimization_level 1 vẫn NPU (YOLOv8n) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt1_layers.txt:61 | Resize INT8 NPU |
| 9.4 | T3: Resize ở optimization_level 2 vẫn NPU (YOLOv8n) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt2_layers.txt:61 | Resize INT8 NPU |
| 9.4 | T3: Resize ở optimization_level 3 vẫn NPU (YOLOv8n) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:61 | Resize INT8 NPU |
| 9.4 | T3: model đã huấn luyện (lượt 3) là best.pt YOLOv8n 5 lớp | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | (YOLOv8n 5 lớp, SiLU, đã huấn luyện) |
| 9.4 | T3: lượt 3 ánh xạ op giống hệt model ngẫu nhiên | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Giống hệt model ngẫu nhiên: 119 lớp, 57 `ConvExSwish` |
| 9.4 | T3: YOLO26n trọng số ngẫu nhiên, chỉ cấu trúc và độ trễ | T3 | LOG 2026-10-10_yolo-phaseA/README.md | trọng số ngẫu nhiên (cấu trúc và độ trễ, không có accuracy) |
| 9.4 | T3: nguyên nhân YOLO26n chậm hơn chưa tách được | T3 | LOG 2026-10-10_yolo-phaseA/README.md | chưa tách được phần đóng góp của từng yếu tố |
| 9.4 | Độ chính xác INT8 của khối attention chưa đo | T3 | (không có) | (unknown) |
| 9.4 | Hành vi đầu end2end bật trên board chưa đo | T3 | (không có) | (unknown) |
| 9.4 | Concat axis -1 trên tensor 3 chiều: OPL ghi shape 4 chiều, điều kiện unknown | T1 | (không có) | (unknown) |
| 9.4 | Điều kiện steps của hai nút Slice từ _NormalizeCoords chưa kiểm được | T1 | (không có) | (unknown) |
| 9.4 | Concat ONNX: axis 1 và axis -1 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "concat_axes": { "1": 22, "-1": 2 } |
| 9.4 | Split ONNX YOLO26n: axis 1 và axis 2 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "split_axes": { "1": 9, "2": 2 } |
| 9.4 | Softmax ONNX YOLO26n: axis -1 | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "softmax_axes": { "-1": 2 } |
| 9.4 | Training-only: bỏ DFL, reg_max 1 (YOFF) | T2 | YOFF tr.6 | YOLO26 removes the Distribution Focal Loss (DFL) module from the detection head. |
| 9.4 | Training-only: ProgLoss, STAL (Y26A, không đổi đồ thị theo mô tả) | T2 | Y26A tr.4 | ProgLoss adaptively reweights objectives to prevent domination by easy examples late in training |
| 9.4 | Training-only: MuSGD là bộ tối ưu hóa | T2 | Y26A tr.7 | the introduction of the MuSGD optimizer |
| 9.4 | OPL: mục Concat (3.2.4) không có dòng 多核联合 (đã đọc cả mục) | T1 | OPL tr.58 | (đọc từ hình) |
| 9.4 | OPL: mục Split (3.2.59) không có dòng 多核联合 (đã đọc cả mục) | T1 | OPL tr.91 | (đọc từ hình) |
| 9.4 | OPL: mục MaxPool (3.2.44) không có dòng 多核联合 (đã đọc cả mục, tr.79 và 80) | T1 | OPL tr.80 | (đọc từ hình) |
| 9.4 | UG232 tr.142: bảng quy tắc ghép không có MaxPool, Split, Concat, Resize | T1 | UG232 tr.142 | (đọc từ hình) |
| 9.4 | exSDPAttention: channel ∈ (0, 8192] | T1 | OPL tr.104 | channel ∈ (0, 8192] |
| 9.4 | T3 với SiLU: Add đứng riêng (YOLOv8n 8 Add cạnh 57 ConvExSwish, không có ConvAdd) | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolov8n_AUTO.txt | (số học) |
| 9.4 | T3: YOLO26n không có lớp exSoftmax13 và không có lớp Transpose; không còn MatMul, Softmax | T3 | LOG 2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt | (số học) |
| 9.4 | Concat ONNX YOLOv8n: axis 1 ở 16 nút, axis -1 ở 2 nút | T1 tính | REPO docs/tools/visual_guide/npu_rk3588/09-yolo/data/rknn_path_onnx.json | "concat_axes": { "1": 16, "-1": 2 } |
| 9.4 | Tên ConvExSwish không có trong OPL và UG232 | T1 | (không có) | (unknown) |
| 9.2 | Số đầu 2: head_dim = 128 // 2 = 64, key_dim = int(64 * 0.5) = 32, q 32, k 32, v 64 kênh mỗi đầu | T1 tính | ULT nn/modules/block.py:1305 | (số học) |
| 9.2 | Attention: head_dim = dim // num_heads | T1 | ULT nn/modules/block.py:1304 | self.head_dim = dim // num_heads |
| 9.2 | Số lần lặp: n = max(round(n * depth), 1) nếu n > 1 | T1 | ULT nn/tasks.py:2107 | n = n_ = max(round(n * depth), 1) if n > 1 else n  # depth gain |
| 9.2 | C2PSA nằm trong repeat_modules (n được chèn vào args) | T1 | ULT nn/tasks.py:2088 | C2PSA, |
| 9.2 | C2PSA lớp 10: yaml lặp 2, depth 0.50 nên n = 1 | T1 tính | ULT cfg/models/26/yolo26.yaml:32 | (số học) |
| 9.4 | exMatMul: đa lõi 不支持 | T1 | OPL tr.102 | 多核联合: 不支持 |
| 9.1 | YOLOv8n lớp 0: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 0 \| -1 \| Conv \| 448 \| 0.088 \| [1, 16, 320, 320] \| |
| 9.1 | YOLOv8n lớp 1: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 1 \| -1 \| Conv \| 4,640 \| 0.236 \| [1, 32, 160, 160] \| |
| 9.1 | YOLOv8n lớp 2: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 2 \| -1 \| C2f \| 7,264 \| 0.367 \| [1, 32, 160, 160] \| |
| 9.1 | YOLOv8n lớp 3: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 3 \| -1 \| Conv \| 18,496 \| 0.236 \| [1, 64, 80, 80] \| |
| 9.1 | YOLOv8n lớp 4: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 4 \| -1 \| C2f \| 49,408 \| 0.629 \| [1, 64, 80, 80] \| |
| 9.1 | YOLOv8n lớp 5: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 5 \| -1 \| Conv \| 73,856 \| 0.236 \| [1, 128, 40, 40] \| |
| 9.1 | YOLOv8n lớp 6: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 6 \| -1 \| C2f \| 197,120 \| 0.629 \| [1, 128, 40, 40] \| |
| 9.1 | YOLOv8n lớp 7: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 7 \| -1 \| Conv \| 295,168 \| 0.236 \| [1, 256, 20, 20] \| |
| 9.1 | YOLOv8n lớp 8: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 8 \| -1 \| C2f \| 459,520 \| 0.367 \| [1, 256, 20, 20] \| |
| 9.1 | YOLOv8n lớp 9: SPPF, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 9 \| -1 \| SPPF \| 164,224 \| 0.131 \| [1, 256, 20, 20] \| |
| 9.1 | YOLOv8n lớp 10: Upsample, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 10 \| -1 \| Upsample \| 0 \| 0.000 \| [1, 256, 40, 40] \| |
| 9.1 | YOLOv8n lớp 11: Concat, from [-1, 6], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 11 \| [-1, 6] \| Concat \| 0 \| 0.000 \| [1, 384, 40, 40] \| |
| 9.1 | YOLOv8n lớp 12: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 12 \| -1 \| C2f \| 147,840 \| 0.472 \| [1, 128, 40, 40] \| |
| 9.1 | YOLOv8n lớp 13: Upsample, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 13 \| -1 \| Upsample \| 0 \| 0.000 \| [1, 128, 80, 80] \| |
| 9.1 | YOLOv8n lớp 14: Concat, from [-1, 4], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 14 \| [-1, 4] \| Concat \| 0 \| 0.000 \| [1, 192, 80, 80] \| |
| 9.1 | YOLOv8n lớp 15: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 15 \| -1 \| C2f \| 37,056 \| 0.472 \| [1, 64, 80, 80] \| |
| 9.1 | YOLOv8n lớp 16: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 16 \| -1 \| Conv \| 36,928 \| 0.118 \| [1, 64, 40, 40] \| |
| 9.1 | YOLOv8n lớp 17: Concat, from [-1, 12], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 17 \| [-1, 12] \| Concat \| 0 \| 0.000 \| [1, 192, 40, 40] \| |
| 9.1 | YOLOv8n lớp 18: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 18 \| -1 \| C2f \| 123,264 \| 0.393 \| [1, 128, 40, 40] \| |
| 9.1 | YOLOv8n lớp 19: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 19 \| -1 \| Conv \| 147,584 \| 0.118 \| [1, 128, 20, 20] \| |
| 9.1 | YOLOv8n lớp 20: Concat, from [-1, 9], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 20 \| [-1, 9] \| Concat \| 0 \| 0.000 \| [1, 384, 20, 20] \| |
| 9.1 | YOLOv8n lớp 21: C2f, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 21 \| -1 \| C2f \| 492,288 \| 0.393 \| [1, 256, 20, 20] \| |
| 9.1 | YOLOv8n lớp 22: Detect, from [15, 18, 21], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| 22 \| [15, 18, 21] \| Detect \| 751,519 \| 2.965 \| [1, 9, 8400] \| |
| 9.1 | YOLOv8n: tổng tham số và GFLOPs | T1 tính | LOG 2026-10-10_yolo-arch/out/table_v8n.md | \| tổng \| \| \| 3,006,623 \| 8.087 \| |
| 9.1 | YOLO26n lớp 0: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 0 \| -1 \| Conv \| 448 \| 0.088 \| [1, 16, 320, 320] \| |
| 9.1 | YOLO26n lớp 1: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 1 \| -1 \| Conv \| 4,640 \| 0.236 \| [1, 32, 160, 160] \| |
| 9.1 | YOLO26n lớp 2: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 2 \| -1 \| C3k2 \| 6,520 \| 0.328 \| [1, 64, 160, 160] \| |
| 9.1 | YOLO26n lớp 3: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 3 \| -1 \| Conv \| 36,928 \| 0.472 \| [1, 64, 80, 80] \| |
| 9.1 | YOLO26n lớp 4: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 4 \| -1 \| C3k2 \| 25,840 \| 0.328 \| [1, 128, 80, 80] \| |
| 9.1 | YOLO26n lớp 5: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 5 \| -1 \| Conv \| 147,584 \| 0.472 \| [1, 128, 40, 40] \| |
| 9.1 | YOLO26n lớp 6: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 6 \| -1 \| C3k2 \| 86,528 \| 0.275 \| [1, 128, 40, 40] \| |
| 9.1 | YOLO26n lớp 7: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 7 \| -1 \| Conv \| 295,168 \| 0.236 \| [1, 256, 20, 20] \| |
| 9.1 | YOLO26n lớp 8: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 8 \| -1 \| C3k2 \| 345,088 \| 0.275 \| [1, 256, 20, 20] \| |
| 9.1 | YOLO26n lớp 9: SPPF, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 9 \| -1 \| SPPF \| 164,224 \| 0.131 \| [1, 256, 20, 20] \| |
| 9.1 | YOLO26n lớp 10: C2PSA, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 10 \| -1 \| C2PSA \| 248,320 \| 0.259 \| [1, 256, 20, 20] \| |
| 9.1 | YOLO26n lớp 11: Upsample, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 11 \| -1 \| Upsample \| 0 \| 0.000 \| [1, 256, 40, 40] \| |
| 9.1 | YOLO26n lớp 12: Concat, from [-1, 6], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 12 \| [-1, 6] \| Concat \| 0 \| 0.000 \| [1, 384, 40, 40] \| |
| 9.1 | YOLO26n lớp 13: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 13 \| -1 \| C3k2 \| 119,296 \| 0.380 \| [1, 128, 40, 40] \| |
| 9.1 | YOLO26n lớp 14: Upsample, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 14 \| -1 \| Upsample \| 0 \| 0.000 \| [1, 128, 80, 80] \| |
| 9.1 | YOLO26n lớp 15: Concat, from [-1, 4], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 15 \| [-1, 4] \| Concat \| 0 \| 0.000 \| [1, 256, 80, 80] \| |
| 9.1 | YOLO26n lớp 16: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 16 \| -1 \| C3k2 \| 34,048 \| 0.432 \| [1, 64, 80, 80] \| |
| 9.1 | YOLO26n lớp 17: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 17 \| -1 \| Conv \| 36,928 \| 0.118 \| [1, 64, 40, 40] \| |
| 9.1 | YOLO26n lớp 18: Concat, from [-1, 13], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 18 \| [-1, 13] \| Concat \| 0 \| 0.000 \| [1, 192, 40, 40] \| |
| 9.1 | YOLO26n lớp 19: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 19 \| -1 \| C3k2 \| 94,720 \| 0.301 \| [1, 128, 40, 40] \| |
| 9.1 | YOLO26n lớp 20: Conv, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 20 \| -1 \| Conv \| 147,584 \| 0.118 \| [1, 128, 20, 20] \| |
| 9.1 | YOLO26n lớp 21: Concat, from [-1, 10], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 21 \| [-1, 10] \| Concat \| 0 \| 0.000 \| [1, 384, 20, 20] \| |
| 9.1 | YOLO26n lớp 22: C3k2, from -1, tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 22 \| -1 \| C3k2 \| 461,504 \| 0.429 \| [1, 256, 20, 20] \| |
| 9.1 | YOLO26n lớp 23: Detect, from [16, 19, 22], tham số, GFLOPs, đầu ra | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| 23 \| [16, 19, 22] \| Detect \| 120,443 \| 0.435 \| [1, 9, 8400] \| |
| 9.1 | YOLO26n: tổng tham số và GFLOPs | T1 tính | LOG 2026-10-10_yolo-arch/out/table_26n.md | \| tổng \| \| \| 2,375,811 \| 5.314 \| |
