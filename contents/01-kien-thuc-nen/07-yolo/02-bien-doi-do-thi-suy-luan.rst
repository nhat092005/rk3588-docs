:tocdepth: 2

**************************************
Biến đổi đồ thị suy luận từ huấn luyện
**************************************

Trang này phân tích mối quan hệ giữa pha huấn luyện và cấu trúc đồ thị suy luận trong các mô hình YOLO, tập trung vào sự chuyển dịch từ YOLOv8 sang YOLO26. Nhiều cải tiến thuật toán hiện đại chỉ can thiệp vào giai đoạn tối ưu hóa tham số mà không để lại bất kỳ chi phí tính toán nào trong đồ thị xuất khẩu. Ngược lại, việc loại bỏ phân phối hộp DFL và áp dụng nhánh gán nhãn một-một làm biến đổi căn bản cấu trúc các toán tử suy luận trên phần cứng biên. Độc giả quan tâm đến việc chuyển đổi đồ thị này sang định dạng RKNN trên vi xử lý RK3588 có thể tham khảo :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`.

.. contents:: Mục lục trang
   :local:
   :depth: 2

Huấn luyện tác động gì lên đồ thị suy luận
==========================================

Quá trình huấn luyện mô hình học sâu và quá trình suy luận thực tế phục vụ hai mục tiêu hoàn toàn khác nhau, dẫn tới sự phân tách rõ rệt về cấu trúc đồ thị tính toán:

- Ranh giới giữa đồ thị huấn luyện và đồ thị suy luận:
  - Đồ thị huấn luyện (training graph): Chứa đầy đủ các nhánh tính toán phục vụ lan truyền thuận và ngược. Đồ thị này bao gồm các tầng chuẩn hóa động (BatchNorm lưu trữ các thống kê trung bình trượt running mean và phương sai trượt running variance), các phép ngẫu nhiên hóa (Dropout, Data Augmentation), các nhánh dự đoán phụ trợ (auxiliary heads), các hàm tổn thất phức tạp (CIoU, BCE, Focal Loss), và các biến trạng thái của thuật toán tối ưu (momentum buffers, second-order moments).
  - Đồ thị suy luận (inference graph): Là một đồ thị có hướng không chu trình (DAG) tĩnh, chỉ giữ lại các phép tính tất định cần thiết để biến đổi tensor hình ảnh đầu vào thành tensor dự đoán đầu ra. Mọi thành phần phục vụ tính đạo hàm, cập nhật trọng số và tính hàm mất mát đều bị loại bỏ hoàn toàn nhằm giải phóng bộ nhớ và tối ưu tốc độ xử lý.

- Chuyển đổi trạng thái mô hình (Train sang Eval):
  - Khi chuyển từ chế độ huấn luyện sang suy luận (thông qua lệnh ``model.eval()`` trong PyTorch), các lớp ngẫu nhiên bị vô hiệu hóa hoặc chuyển thành phép đồng nhất (Identity).
  - Các tham số thống kê của lớp chuẩn hóa BatchNorm2d ngừng cập nhật, chuyển sang sử dụng giá trị kỳ vọng :math:`\mu` và phương sai :math:`\sigma^2` cố định đã học được qua toàn bộ tập dữ liệu huấn luyện.
  - Các nhánh tính toán gradient bị vô hiệu hóa hoàn toàn (tương đương với bối cảnh ``torch.no_grad()``), cho phép giải phóng toàn bộ bộ nhớ đệm lưu trữ các trạng thái kích hoạt trung gian phục vụ lan truyền ngược.
  - Kích thước tensor đầu vào thường được cố định từ dạng động đa tỷ lệ (dynamic multi-scale từ 320 đến 640 pixel) thành một kích thước tĩnh duy nhất :math:`(1, 3, 640, 640)` nhằm tạo điều kiện cho trình biên dịch phần cứng cấp phát trước bộ nhớ đệm tĩnh.

- Cơ chế toán học của phép gộp lớp (Conv-BN Fusion):
  - Trong quá trình huấn luyện, lớp tích chập Conv và lớp chuẩn hóa BatchNorm2d hoạt động tuần tự. Với đầu vào :math:`x`, lớp Conv tính :math:`y = W x + b`, sau đó BatchNorm chuẩn hóa theo:

    .. math::

       z = \gamma \cdot \frac{y - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta

    trong đó :math:`\mu` và :math:`\sigma^2` là kỳ vọng và phương sai thống kê qua các batch, còn :math:`\gamma, \beta` là các tham số co giãn và dịch chuyển học được.

  - Khi chuyển sang chế độ suy luận, do :math:`\mu, \sigma^2, \gamma, \beta` đã hội tụ thành các hằng số tĩnh, hai phép biến đổi tuyến tính liên tiếp này được gộp toán học thành một lớp tích chập duy nhất:

    .. math::

       W_{fused} = \frac{\gamma}{\sqrt{\sigma^2 + \epsilon}} W, \quad b_{fused} = \frac{\gamma}{\sqrt{\sigma^2 + \epsilon}} (b - \mu) + \beta

    Phép dung hợp này triệt tiêu hoàn toàn các toán tử BatchNorm trong đồ thị ONNX xuất ra, giúp tiết kiệm đáng kể băng thông truy cập bộ nhớ DRAM và loại bỏ chi phí lưu trữ các tensor trung gian giữa Conv và BN.

- Các biến đổi đồ thị khi chuyển sang pha suy luận:
  - Cắt tỉa nhánh phụ trợ (Auxiliary Branch Pruning): Trong các kiến trúc huấn luyện nâng cao như YOLO26, mạng duy trì đồng thời nhánh một-nhiều và nhánh một-một. Khi chuyển sang suy luận, tác giả khẳng định: "Parameter counts and FLOPs denote the fused inference architecture, which merges Conv/BatchNorm layers and removes the auxiliary one-to-many detection head used during training." [T2 Y26A tr.17]. Nhánh phụ trợ bị cắt bỏ hoàn toàn để tinh gọn đồ thị.
  - Khóa hằng số (Constant Folding): Các giá trị siêu tham số và ma trận trọng số được cố định thành các hằng số tĩnh, giúp bộ biên dịch phần cứng dễ dàng lập lịch bộ nhớ và phân bổ đệm SRAM.
  - Tách bỏ nhánh tính toán hàm mất mát: Toàn bộ các toán tử phục vụ tính toán loss như phép tạo lưới anchor, so khớp nhãn ground truth, và tính sai lệch IoU đều bị cắt đứt khỏi đồ thị xuất khẩu.
  - Tối ưu hóa thứ tự tensor và loại bỏ phép chuyển vị (Transpose Optimization): Các framework huấn luyện PyTorch mặc định định dạng bộ nhớ NCHW, trong khi nhiều kiến trúc NPU phần cứng biên ưa chuộng định dạng NHWC để tối ưu hóa việc nạp dữ liệu vào mảng PE. Quá trình tối ưu hóa đồ thị suy luận thường sắp xếp lại các phép chuyển vị nhằm giảm thiểu số lần hoán vị trục tensor giữa các tầng liền kề.
  - Khử bỏ các toán tử vô hiệu (Dead Code Elimination): Các nhánh tính toán hoặc biến trung gian chỉ phục vụ mục đích kiểm thử (logging, trích xuất đặc trưng trung gian) trong quá trình huấn luyện đều bị loại bỏ triệt để, đảm bảo đồ thị chỉ chứa đường dẫn tối thiểu từ input đến output.

.. list-table:: Phân loại tác động của các thành phần huấn luyện lên đồ thị suy luận
   :header-rows: 1
   :widths: 25 35 40

   * - Thành phần huấn luyện
     - Tác động lên đồ thị suy luận
     - Cơ chế xử lý khi xuất khẩu mô hình
   * - Phép gộp Conv + BatchNorm
     - Thay đổi cấu trúc (rút gọn)
     - Gộp tham số toán học vào một lớp Conv duy nhất có bias
   * - Nhánh phụ trợ (One-to-many)
     - Bị loại bỏ hoàn toàn
     - Cắt tỉa nhánh thừa qua phương thức ``model.fuse()`` [T2 Y26A tr.17]
   * - Module phân phối hộp DFL
     - Bị bãi bỏ trong YOLO26
     - Thay bằng nhánh hồi quy trực tiếp tuyến tính 4 kênh [T2 Y26A tr.8]
   * - Đầu một-một (One-to-one Head)
     - Giữ lại làm đầu ra chính
     - Xuất trực tiếp dự đoán đơn nhất, hỗ trợ NMS-free [T2 Y26B tr.7]
   * - Hàm mất mát (ProgLoss, TAL)
     - Hoàn toàn không tác động
     - Chỉ dùng để tính đạo hàm ngược, không sinh ra node ONNX [T2 Y26B tr.4]
   * - Bộ tối ưu hóa (MuSGD, AdamW)
     - Hoàn toàn không tác động
     - Cập nhật trọng số tĩnh trong checkpoint, bị gỡ khi export [T2 Y26B tr.7]

Bỏ DFL và tích hợp nhánh một-một (One-to-one Head)
==================================================

Sự biến đổi đồ thị rõ rệt nhất giữa YOLOv8 và YOLO26 nằm ở việc tái cấu trúc đầu dự đoán (Detect Head), tác động trực tiếp đến tính khả thi và độ trễ khi triển khai trên phần cứng biên.

Bãi bỏ module phân phối hộp DFL:
  - Trong YOLOv8, việc ước lượng tọa độ hộp biên dựa trên cơ chế Distribution Focal Loss đòi hỏi mạng phải xuất ra 16 kênh phân phối xác suất rời rạc cho mỗi cạnh hộp [T2 UEVOL tr.10]. Cấu trúc này tạo ra trong đồ thị suy luận các cụm toán tử phức tạp:
    1. Toán tử ``Reshape`` và ``Transpose`` để tổ chức lại tensor đầu ra từ kích thước đa kênh thành cấu trúc ma trận thuận tiện cho tính toán phân phối xác suất.
    2. Toán tử ``Softmax`` áp dụng trên từng đoạn 16 bin tọa độ để chuyển đổi các giá trị logit thô thành phân phối xác suất hợp lệ.
    3. Toán tử tích vô hướng hoặc Conv :math:`1 \times 1` nhân phân phối xác suất với vector hằng số :math:`[0, 1, \dots, 15]` nhằm thu được kỳ vọng tọa độ khoảng cách.
  - Tác động tiêu cực của DFL trên phần cứng: Các toán tử Softmax yêu cầu tính toán hàm mũ và phép chia dấu phẩy động liên tục trên hàng ngàn điểm ảnh (8,400 anchor ở độ phân giải 640x640), gây khó khăn lớn cho việc lượng tử hóa số nguyên: "On specialized edge hardware (NPUs and DSPs), these Softmax layers are notoriously difficult to quantize and often become the primary latency bottleneck [30]." [T2 Y26A tr.8].
  - Trong YOLO26, module DFL bị loại bỏ hoàn toàn: "One of the most significant architectural simplifications in YOLO26 is the removal of the Distribution Focal Loss (DFL) module" [T2 Y26B tr.6]. Mô hình quay trở lại chiến lược hồi quy trực tiếp: "YOLO26 reverts to a Direct Regression Strategy, removing this module entirely (see Fig. 4)." [T2 Y26A tr.8].
  - Hệ quả trên đồ thị: Đầu ra tọa độ hộp của YOLO26 là một phép chiếu affine thuần túy qua lớp tích chập với số kênh ra bằng 4 (tương ứng tham số cấu hình ``reg_max=1``) [T1 yolo26.yaml:10]. Đồ thị suy luận trở nên hoàn toàn tuyến tính, không còn các toán tử Softmax phân mảnh, cho phép bộ biên dịch dung hợp các lớp tính toán một cách tối ưu và tạo điều kiện thuận lợi cho việc lượng tử hóa INT8 thuần số nguyên.

So sánh luồng giải mã tọa độ hộp trên đồ thị:
  - Đường ống giải mã của YOLOv8:

    .. code-block:: text

       Conv(64 kênh) --> Reshape(4, 16) --> Softmax(dim=16) --> MatMul([0..15]) --> Box(4)

    Tại mỗi bước, tensor trung gian phải được cấp phát trên bộ nhớ, tạo thành rào cản phụ thuộc dữ liệu khiến NPU không thể gộp toán tử.
  - Đường ống giải mã của YOLO26:

    .. code-block:: text

       Conv(4 kênh) -------------------------------------------------------------> Box(4)

    Đầu ra từ lớp tích chập cuối cùng chính là khoảng cách biên hộp thực tế, loại bỏ hoàn toàn khâu giải mã xác suất trung gian.

Tác động đến lượng tử hóa số nguyên (INT8 Quantization):
  - Khi lượng tử hóa mạng YOLOv8 sang INT8, phân phối kích hoạt của 16 bin trước Softmax có dải động rộng và phân tán. Việc chuyển đổi Softmax sang số nguyên đòi hỏi các bảng tra cứu (LUT) phức tạp hoặc buộc phải giải lượng tử ngược về FP32, phá vỡ tính liên tục của luồng tính toán INT8 trên NPU.
  - Với YOLO26, do giá trị hộp được xuất trực tiếp từ Conv :math:`1 \times 1`, toán tử này tuân theo công thức lượng tử hóa chuẩn của phép tích chập: :math:`q_{out} = M \cdot (q_{in} \ast q_{w}) + Z_{out}`. Toàn bộ khâu tính tọa độ hộp có thể thực thi trọn vẹn trên các mảng nhân cộng tích lũy số nguyên (INT8 MACs) của NPU mà không cần bất kỳ toán tử phi tuyến đặc thù nào.
  - Mỗi kênh hộp của YOLO26 chỉ cần xác định một cặp tham số lượng tử hóa :math:`(S, Z)` tĩnh thông qua phương pháp hiệu chuẩn phân kỳ KL (Kullback-Leibler) hoặc MSE trên tập dữ liệu đại diện. Điều này giúp loại bỏ hoàn toàn hiện tượng bão hòa hoặc sai số tràn số thường gặp khi lượng tử hóa các hàm phi tuyến tính như Softmax.

Tích hợp nhánh một-một và cơ chế NMS-free:
  - Ở các mô hình truyền thống, cơ chế gán nhãn một-nhiều khiến đồ thị suy luận luôn tạo ra nhiều hộp chồng lấn, buộc phải ghép thêm thuật toán Non-Maximum Suppression (NMS) ở khâu hậu kỳ để lọc bỏ hộp dư thừa [T2 Y26A tr.7]. NMS có độ phức tạp thuật toán biến thiên theo số lượng đối tượng trong ảnh, gây dao động độ trễ và khó thực thi hiệu quả trên các nhân tính toán song song tĩnh của NPU.
  - YOLO26 áp dụng cơ chế huấn luyện đối sánh một-một: "By redesigning the prediction head to support one-to-one label assignment [24], the model learns to output a single, definitive box per object instance during training." [T2 Y26A tr.7].
  - Nhờ cơ chế này, mô hình học được cách dự đoán chính xác một hộp giới hạn duy nhất cho mỗi đối tượng: "YOLO26 fundamentally redesigns the prediction head to produce direct, non-redundant bounding box predictions without the need for NMS" [T2 Y26B tr.7].
  - Hệ quả kiến trúc: Đồ thị suy luận đạt được tính chất thời gian thực đơn định (deterministic latency), triệt tiêu hoàn toàn sự phụ thuộc vào các thuật toán NMS hậu kỳ: "By removing the computational burden of DFL and adopting a native one-to-one prediction head, YOLO26 achieves deterministic inference times" [T2 Y26A tr.5].
  - Cơ chế lọc hậu kỳ tĩnh: Khi xuất mô hình với cờ ``end2end: True`` [T1 yolo26.yaml:9], khâu hậu kỳ chỉ bao gồm việc nhân ngưỡng tin cậy và trích chọn :math:`K` dự đoán hàng đầu thông qua hàm ``topk`` cố định (như 100 hoặc 300 đối tượng) [T1 ultralytics/nn/modules/head.py]. Các toán tử này có khối lượng tính toán cố định và hoàn toàn độc lập với mật độ vật thể trong cảnh quay.
  - Đánh giá độ chính xác: Trên tập dữ liệu COCO val, nhánh một-một của YOLO26n đạt 40.1% mAP (theo đánh giá end-to-end), trong khi nhánh một-nhiều khi dùng NMS truyền thống đạt 40.9% mAP [T2 YOFF tr.14]. Sự chênh lệch 0.8% mAP là mức đánh đổi hợp lý để đổi lấy khả năng thực thi thời gian thực ổn định và đơn giản hóa đồ thị triển khai.

Các cải tiến chỉ ở pha huấn luyện không đổi đồ thị suy luận (ProgLoss, STAL, MuSGD)
===================================================================================

Bên cạnh các thay đổi về cấu trúc mạng, YOLO26 giới thiệu ba kỹ thuật huấn luyện đột phá nhằm cải thiện độ chính xác và tốc độ hội tụ mà hoàn toàn không làm phát sinh thêm bất kỳ chi phí tính toán hay thay đổi nào trong đồ thị suy luận ONNX xuất ra.

- **Progressive Loss (ProgLoss)**:
  - Khái niệm: Trong quá trình huấn luyện mô hình end-to-end có cả hai nhánh, việc cân bằng tín hiệu giám sát giữa nhánh một-nhiều và nhánh một-một là thách thức lớn. ProgLoss giải quyết vấn đề này bằng chiến lược điều chỉnh động trọng số hàm tổn thất theo thời gian: "ProgLoss adaptively reweights objectives to prevent domination by easy examples late in training, while STAL prioritizes assignment for tiny or occluded instances" [T2 Y26B tr.4].
  - Cơ chế hoạt động: Ở những epoch đầu tiên, ProgLoss gán trọng số lớn hơn cho nhánh một-nhiều để cung cấp tín hiệu gradient dày đặc giúp backbone học biểu diễn không gian nhanh chóng. Càng về các epoch cuối, trọng số giám sát chuyển dần sang nhánh một-một nhằm rèn luyện mạng khả năng ra quyết định dứt khoát trên từng đối tượng [T2 YOFF tr.11].
  - Bù đắp độ chính xác khi bỏ DFL: Nghiên cứu thực nghiệm chỉ ra rằng: "Table 2 shows that removing DFL alone costs 0.6 AP on the YOLO11s baseline (47.0 to 46.4), but this gap is fully recovered by L1 supervision (+0.2), STAL (+0.2), and the backbone/neck refinement (+0.2)" [T2 YOFF tr.11]. Nhờ sự kết hợp của ProgLoss và giám sát L1, độ chính xác định vị hộp được bù đắp hoàn toàn mà đồ thị suy luận vẫn giữ nguyên tính chất nhẹ của phép hồi quy trực tiếp.
  - Tính chất đối với đồ thị suy luận: ProgLoss chỉ là một hệ số tỷ lệ trong biểu thức tính đạo hàm ngược của PyTorch. Khi xuất mô hình sang ONNX hoặc định dạng suy luận phần cứng, toàn bộ mã nguồn của ProgLoss bị loại bỏ hoàn toàn.

- **Small-Target-Aware Label Assignment (STAL)**:
  - Khái niệm: Các bộ gán nhãn truyền thống như Task-Aligned Assigner (TAL) thường thiên vị các đối tượng có kích thước lớn, dẫn tới việc các vật thể nhỏ hoặc bị che khuất không được gán đủ số lượng anchor tích cực trong quá trình huấn luyện [T2 YOFF tr.8].
  - Cơ chế hoạt động: STAL đưa vào một kích thước chuẩn hóa tham chiếu :math:`s_{ref}=16` pixel để cân chỉnh lại điểm căn chỉnh (alignment metric), đảm bảo các vật thể nhỏ vẫn nhận được số lượng mẫu huấn luyện dương tương xứng [T2 YOFF tr.8, tr.14].
  - Bảo toàn không gian ứng viên: Khác với các phương pháp làm phình dữ liệu giám sát, tác giả nhấn mạnh: "Importantly, STAL modifies only the candidate-selection mask." [T2 YOFF tr.8]. Hộp nhãn gốc :math:`g_i` vẫn được bảo toàn trọn vẹn cho việc tính điểm căn chỉnh và hồi quy hộp thực tế. Điều này: "makes STAL deliberately conservative: it does not alter localization targets or inflate supervision for ordinary objects" [T2 YOFF tr.8].
  - Tính chất đối với đồ thị suy luận: STAL chỉ thực hiện logic so khớp hình học giữa bounding box nhãn thực tế và các anchor trong pha huấn luyện. Thuật toán này không tạo ra bất kỳ tham số hay toán tử nào trong đồ thị suy luận.

- **Bộ tối ưu hóa MuSGD (Muon-assisted SGD)**:
  - Khái niệm: YOLO26 giới thiệu bộ tối ưu hóa lai kết hợp giữa SGD truyền thống và thuật toán tối ưu ma trận Muon: "the introduction of the MuSGD optimizer (Figure 4d), which combines the strengths of Stochastic Gradient Descent (SGD) with the recently proposed Muon optimizer" [T2 Y26B tr.7].
  - Cơ chế hoạt động: MuSGD khai thác khả năng tổng quát hóa tốt của SGD-momentum trên các lớp tích chập thông thường, đồng thời áp dụng các bước cập nhật trực giao hóa ma trận thông qua thuật toán lặp Newton-Schulz từ Muon lên các ma trận trọng số 2 chiều [T2 YOFF tr.7], [T2 Y26B tr.7].
  - Phân tách tham số ma trận và vector: Trong triển khai thực tế, Muon chỉ áp dụng cho các trọng số 2 chiều hoặc tensor tích chập đa chiều sau khi trải phẳng thành ma trận :math:`(C_{out}, C_{in} \times K_h \times K_w)`. Các tham số 1 chiều như vector bias hoặc các tham số chuẩn hóa vẫn được tối ưu hóa bằng thuật toán SGD momentum truyền thống [T2 YOFF tr.7]. Thuật toán lặp xấp xỉ ma trận trực giao :math:`O_t \approx U V^T` từ gradient :math:`G` theo công thức:

    .. math::

       X_{k+1} = X_k \left(a I + b X_k^T X_k + c (X_k^T X_k)^2\right)

    với các hệ số thực nghiệm cố định :math:`a=3.4445, b=-4.7750, c=2.0315`, giúp giới hạn giá trị kỳ dị của ma trận cập nhật, ngăn chặn hiện tượng bùng nổ gradient mà không cần giảm learning rate toàn cục.

  - Hiệu quả huấn luyện: MuSGD giúp mô hình đạt độ chính xác cao hơn với số lượng epoch ít hơn (giảm từ 600 epoch xuống còn 500 epoch trên tập COCO), rút ngắn chu kỳ huấn luyện và tiết kiệm năng lượng tính toán [T2 YOFF tr.12].
  - Tính chất đối với đồ thị suy luận: Sau khi hoàn thành huấn luyện, bộ tối ưu hóa MuSGD được giải phóng khỏi bộ nhớ, chỉ còn lại các giá trị trọng số tĩnh được lưu trong tệp mô hình. Đồ thị suy luận không chứa bất kỳ dấu vết nào của thuật toán tối ưu.

Điều chưa biết (unknown: hành vi suy luận cụ thể trên các runtime độc quyền)
============================================================================

Mặc dù các tài liệu công bố chính thức đã chứng minh ưu thế lý thuyết của kiến trúc YOLO26 trên môi trường GPU và CPU chuẩn, việc ứng dụng mô hình này trên các bộ xử lý thần kinh biên (Edge NPU) vẫn tồn tại các điểm chưa được làm sáng tỏ trong y văn:

- Sự đánh đổi giữa nhánh một-một và nhánh một-nhiều sau lượng tử hóa INT8:
  - unknown. Đã tìm ở: YOFF tr.14, Y26A tr.8, Y26B tr.5, từ khóa: "NPU runtime", "INT8 quantization degradation", "proprietary compiler".
  - Hiện tại, các tài liệu T2 mới chỉ cung cấp số liệu so sánh mAP giữa nhánh một-một (40.1%) và một-nhiều (40.9%) ở độ chính xác số thực FP32 trên GPU máy chủ [T2 YOFF tr.14]. Mức độ suy giảm độ chính xác khi lượng tử hóa INT8 (PTQ/QAT) đối với nhánh một-một nhạy cảm trên các trình biên dịch NPU độc quyền của từng hãng sản xuất chip vẫn chưa được công bố bằng thực nghiệm độc lập.

- Mức độ tối ưu hóa phần cứng cho các toán tử Pointwise Self-Attention:
  - unknown. Đã tìm ở: YOFF tr.11, Y26A tr.22, từ khóa: "attention NPU acceleration", "MatMul fusion", "SRAM buffer allocation".
  - Mặc dù cơ chế Attention trong C2PSA và C3k2 chỉ hoạt động trên lưới :math:`20 \times 20` (400 token) nhằm hạn chế FLOPs, khả năng các trình biên dịch NPU độc quyền có dung hợp hiệu quả toán tử ``MatMul`` và ``Softmax`` vào bộ nhớ đệm SRAM trên chip hay không phụ thuộc hoàn toàn vào kiến trúc nội bộ của từng bộ tăng tốc.
  - Thao tác hoán vị trục bộ nhớ (transpose và reshape) cần thiết cho Attention có nguy cơ phá vỡ luồng truyền dữ liệu liên tục (streaming dataflow) vốn được tối ưu hóa cho các toán tử tích chập truyền thống trên phần cứng NPU.

- Khả năng tương thích của nhánh gán nhãn một-một trên các pipeline suy luận lai:
  - unknown. Đã tìm ở: YOFF tr.6, Y26A tr.5, từ khóa: "hybrid inference pipeline", "raw output export", "NPU driver postprocessing".
  - Các tài liệu T2 tập trung vào đường suy luận end-to-end trên nền tảng PyTorch/TensorRT. Tuy nhiên, khi triển khai trên các hệ thống nhúng thực tế, việc xuất toàn bộ đầu dự đoán lên NPU hay chỉ xuất các tensor đặc trưng thô để CPU xử lý hậu kỳ là một quyết định kiến trúc phụ thuộc vào năng lực của từng driver phần cứng. Vấn đề khảo sát thực nghiệm và các điểm nghẽn chuyển đổi cụ thể của YOLO trên vi xử lý Rockchip RK3588 được trình bày chi tiết tại chuyên đề :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`.

Nguồn tài liệu tham khảo
========================

Các tài liệu kỹ thuật và bài báo hội thảo chính thức được sử dụng để đối chiếu dữ liệu trong trang này:

.. list-table:: Danh mục tài liệu tham khảo và đối soát trích dẫn
   :header-rows: 1
   :widths: 14 10 60 16

   * - Nhãn
     - Phân loại
     - Tên tài liệu / Đường dẫn lưu trữ
     - Ghi chú
   * - ``YOFF``
     - T2
     - :download:`yolo26_official_2026jocher.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_official_2026jocher.pdf>`
     - Jocher et al. (2026), bài báo chính thức về họ mô hình YOLO26
   * - ``Y26A``
     - T2
     - :download:`yolo26_nmsfree_2026chakrabarty.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_nmsfree_2026chakrabarty.pdf>`
     - Chakrabarty (2026), phân tích cơ chế NMS-free và giải mã không DFL
   * - ``Y26B``
     - T2
     - :download:`yolo26_arch_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_arch_2025sapkota.pdf>`
     - Sapkota et al. (2025), khảo sát cấu trúc mạng và tối ưu hóa phần cứng
   * - ``UEVOL``
     - T2
     - :download:`ultralytics_yolo_evolution_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/ultralytics_yolo_evolution_2025sapkota.pdf>`
     - Sapkota et al. (2025), tổng quan tiến trình tiến hóa họ mạng Ultralytics
   * - ``T1``
     - T1
     - Tệp cấu hình ``yolo26.yaml`` và mã nguồn Ultralytics
     - Cấu hình mạng gốc trong thư viện ``ultralytics``
