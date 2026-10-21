:tocdepth: 1

***********************
Op của YOLOv8 trên RKNN
***********************

.. admonition:: Trang này trả lời

   - Các khối kiến trúc của YOLOv8 (Backbone, C2f, SPPF, Neck, Head, DFL) chứa những toán tử nào?
   - Những toán tử nào trong YOLOv8 được NPU Rockchip RK3588 hỗ trợ trực tiếp theo danh mục OPL chương 3.2?
   - Những toán tử nào trong detector có nguy cơ bị rơi về thực thi trên CPU và nguyên nhân kỹ thuật là gì?
   - Tại sao toán tử Transpose trong khối DFL và các toán tử chọn lọc hộp trong NMS không chạy được trên NPU?

.. admonition:: Tóm tắt

   - Các tầng tích chập trong Backbone và Neck sử dụng khối CBS (Conv + BatchNorm + SiLU), trong đó SiLU được hỗ trợ dưới dạng ConvolutionSwish hợp nhất [T1 OPL tr.63] hoặc toán tử đứng riêng exSwish [T1 OPL tr.98].
   - Khối C2f và C3k2 phân nhánh và gom luồng dữ liệu thông qua các toán tử Concat [T1 OPL tr.58], Split [T1 OPL tr.91] cùng phép cộng phần tử Add trong nhánh residual [T1 OPL tr.56].
   - Khối SPPF trích xuất ngữ cảnh đa tỷ lệ bằng chuỗi 3 toán tử MaxPool kích thước 5x5 stride 1 [T1 OPL tr.79-80] kết hợp phép nối Concat [T1 OPL tr.58].
   - Tầng phân giải trong Neck sử dụng toán tử Resize phóng to kích thước 2 lần theo thuật toán nearest hoặc linear [T1 OPL tr.86-87], tuy nhiên UG232 lưu ý NPU chưa có nhân phần cứng Resize chuyên dụng mà chuyển đổi qua ConvTranspose [T1 UG232 tr.176].
   - Nhánh phân loại của Head kết thúc bằng Sigmoid [T1 OPL tr.95], trong khi nhánh hồi quy hộp chứa khối DFL gồm Reshape [T1 OPL tr.86], Softmax theo trục channel/width [T1 OPL tr.88-89] và Conv 1x1 [T1 OPL tr.58].
   - Toán tử Transpose trong khối DFL rơi về CPU do các chiều tensor vượt quá ngưỡng tham số hoán vị p=8192 quy định trong OPL [T1 OPL tr.93-95].
   - Các toán tử phục vụ lọc hộp end-to-end NMS gồm TopK và GatherElements hoàn toàn không có mục NPU trong chương 3.2 của OPL mà chỉ tồn tại ở chương 4 CPU OPs [T1 OPL tr.330, tr.333].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _62-các-op-của-detector-kiểu-yolov8-trên-rk3588:

1. Bảng op theo từng khối chức năng
===================================

Kiến trúc mạng phát hiện đối tượng YOLOv8 bao gồm ba phần chính: Backbone đảm nhiệm trích xuất đặc trưng đa tầng, Neck (PAN-FPN) thực hiện dung hợp đặc trưng giữa các tỷ lệ không gian, và Decoupled Head thực hiện dự đoán độc lập giữa nhãn lớp và tọa độ hộp bao. Việc xác định tình trạng hỗ trợ phần cứng NPU của từng toán tử trong các khối này căn cứ trực tiếp vào tài liệu danh mục toán tử RKNN Compiler Support Operator List (OPL) chương 3.2 dành riêng cho SoC RK3588 [T1 OPL tr.56-107].

1.1 Khối Backbone và trích xuất đặc trưng
-----------------------------------------

Backbone của YOLOv8 kế thừa thiết kế của CSPNet với khối cấu thành chính là CBS (Convolution, Batch Normalization, SiLU) và C2f:

1. Tích chập tiêu chuẩn (Convolution):
   Các tầng Conv 3x3 (stride 2 để giảm chiều không gian) và Conv 1x1 (thay đổi số kênh) được hỗ trợ hoàn toàn bởi phần cứng NPU theo mục 3.2.5 [T1 OPL tr.58-59]. OPL quy định kích thước nhân ``kernel_h, kernel_w ∈ [1, 31]``, bước trượt ``stride_h, stride_w ∈ [1, 7]``, đệm ``pads ∈ [0, 15]``, và giãn nở ``dilations ∈ [1, 31]``. Khối hỗ trợ cả hai kiểu dữ liệu số nguyên INT8 và dấu phẩy động FP16, đồng thời hỗ trợ thực thi song song trên cả 3 lõi NPU (cột đa lõi ghi "支持") [T1 OPL tr.58]. Lớp Batch Normalization được compiler gấp trực tiếp vào trọng số của Convolution (Conv-BN folding) trong quá trình tối ưu đồ thị.

2. Hàm kích hoạt SiLU (Swish):
   Trong OPL của RK3588, hàm SiLU xuất hiện dưới hai dạng toán tử:
   - Toán tử hợp nhất ConvolutionSwish (mục 3.2.17) [T1 OPL tr.63]:

   ..

      "Convolution 与 Swish 融合计算, Output = Swish(Conv(Input))" [T1 OPL tr.63]

   Mục này có các ràng buộc hình học và kiểu dữ liệu tương tự như Convolution tiêu chuẩn, giúp thực thi phép tính tích chập và hàm kích hoạt trong cùng một lượt trên phần cứng mà không phải ghi dữ liệu trung gian ra bộ nhớ. Cột đa lõi của mục này ghi "暂不支持" (tạm thời chưa hỗ trợ đa lõi) [T1 OPL tr.63].
   - Toán tử rời rạc exSwish (mục 3.2.69) [T1 OPL tr.98]:

   ..

      "按元素应用 Sigmoid 线性单元函数, Swish 函数也称为 SiLU 函数, y = x * sigmoid(x)" [T1 OPL tr.98]

   Được sử dụng khi hàm kích hoạt đứng độc lập mà không thể hợp nhất với lớp Conv liền trước. Trạng thái đa lõi ghi "尚不支持" [T1 OPL tr.98].

3. Khối C2f (và C3k2):
   Khối C2f thực hiện chia kênh đặc trưng bằng toán tử Split (mục 3.2.59) [T1 OPL tr.91]:

   ..

      "将向量沿着 axis 方向分成 num_outputs 个向量" [T1 OPL tr.91]

   Các nhánh đặc trưng đi qua các khối Bottleneck (chứa 2 tầng Conv 3x3 liên tiếp kèm đường tắt residual sử dụng phép cộng phần tử Add theo mục 3.2.1 [T1 OPL tr.56]). Sau đó, toàn bộ các luồng tensor được gom lại bằng phép nối Concat (mục 3.2.4 [T1 OPL tr.58]) và đưa qua một tầng Conv 1x1 cuối khối. Cả Add và Concat đều là các toán tử NPU cốt lõi, trong đó Add hỗ trợ chạy đa lõi "支持" [T1 OPL tr.56].

4. Khối SPPF (Spatial Pyramid Pooling - Fast):
   Nằm ở cuối Backbone nhằm mở rộng trường tiếp nhận (receptive field). SPPF gồm một lớp Conv 1x1, tiếp nối bởi 3 tầng MaxPool liên tiếp có kích thước cửa sổ 5x5 và stride 1, sau đó nối (Concat) toàn bộ các đầu ra lại với nhau. Toán tử MaxPool được quy định tại mục 3.2.44 [T1 OPL tr.79-80]:

   ..

      "pad 的方式: 仅支持 NOTSET" [T1 OPL tr.79]

   Quy cách của MaxPool trên RK3588 yêu cầu kích thước nhân nằm trong khoảng ``(0, 7]`` và bước trượt trong khoảng ``(0, 8]``. Kích thước 5x5 stride 1 của SPPF hoàn toàn thỏa mãn ràng buộc này và chạy trọn vẹn trên NPU [T1 OPL tr.79].

1.2 Khối Neck và Head
---------------------

Khối Neck và Head đảm nhận việc tái tạo thông tin không gian và giải mã dự đoán:

1. Phóng đại đặc trưng trong Neck (Resize):
   Để kết hợp đặc trưng mức cao với mức thấp, Neck sử dụng các tầng nội suy phóng to bản đồ đặc trưng lên 2 lần. OPL cung cấp mục NPU 3.2.54 Resize [T1 OPL tr.86-87]:

   ..

      "目前仅支持宽高方向的整数倍缩放, 且缩放倍数为 2‑8 的整数倍" [T1 OPL tr.87]

   OPL hỗ trợ hai phương thức nội suy là ``nearest`` và ``linear``, cùng ba chế độ chuyển đổi tọa độ gồm ``half_pixel``, ``pytorch_half_pixel``, và ``align_corners`` [T1 OPL tr.87]. Tầng nội suy nearest hệ số 2 trong YOLOv8 nằm trong phạm vi hỗ trợ của OPL. Tuy nhiên, User Guide UG232 đưa ra ghi chú về mặt triển khai phần cứng [T1 UG232 tr.176]:

   ..

      "The decrease in accuracy is because the NPU does not currently support hardware-level Resize (will be supported in the future), and the RKNN-Toolki2 will convert Reszie to ConvTranspose, which will cause a little loss of accuracy." [T1 UG232 tr.176]

   Do đó, trên phần cứng RK3588, compiler ánh xạ toán tử Resize sang dạng ConvTranspose (mục 3.2.20 [T1 OPL tr.63]) để thực thi trên engine tích chập của NPU.

2. Nhánh phân loại (Classification Head):
   Bao gồm các tầng Conv 3x3 và Conv 1x1 để đưa số kênh về bằng số lớp ``nc``. Đầu ra cuối cùng đi qua hàm kích hoạt Sigmoid (mục 3.2.63 [T1 OPL tr.95]) để tính toán xác suất độc lập cho từng lớp đối tượng:

   ..

      "给定输入张量，函数 y = 1 / (1 + exp(‑x)) 按元素应用于输入张量，得到输出张量" [T1 OPL tr.95]

3. Nhánh hồi quy và khối DFL (Distribution Focal Loss):
   Nhánh hồi quy xuất ra tensor chứa phân phối khoảng cách biên (gồm ``4 * reg_max`` kênh, thông thường là 64 kênh với ``reg_max=16``). Khối DFL chuyển đổi phân phối này thành tọa độ thực tế:
   - Sử dụng Reshape (mục 3.2.53 [T1 OPL tr.86]) để định hình lại tensor từ ``[1, 64, 8400]`` thành ``[1, 4, 16, 8400]``.
   - Áp dụng Softmax (mục 3.2.56 [T1 OPL tr.88-89]) dọc theo trục 16 giá trị rời rạc:

   ..

      "做 softmax 的轴: 1,3，即 channel 和 width 方向" [T1 OPL tr.89]

   - Sử dụng Conv 1x1 không có bias với trọng số cố định ``[0, 1, 2, ..., 15]`` để tính kỳ vọng tích phân, rút gọn về 4 giá trị khoảng cách biên.
   - Sử dụng các phép toán Add, Sub, Div (mục 3.2.1, 3.2.60, 3.2.33 [T1 OPL tr.56, tr.67, tr.91]) để chuyển đổi khoảng cách biên thành tọa độ hộp bao tâm-kích thước (xywh).

.. list-table:: Tổng hợp toán tử theo từng khối chức năng của YOLOv8 trên RK3588
   :header-rows: 1
   :widths: 15 20 15 15 35

   * - Khối kiến trúc
     - Toán tử ONNX
     - Mục OPL 3.2
     - Hỗ trợ NPU
     - Ràng buộc chính theo OPL
   * - Backbone (CBS)
     - Conv
     - 3.2.5
     - Có (đa lõi)
     - Kernel in [1, 31], stride in [1, 7], dtype INT8/FP16 [T1 OPL tr.58]
   * - Backbone (CBS)
     - SiLU (Swish)
     - 3.2.17 / 3.2.69
     - Có
     - Hợp nhất ConvolutionSwish hoặc dùng rời exSwish [T1 OPL tr.63, tr.98]
   * - C2f / C3k2
     - Split, Add, Concat
     - 3.2.59, 3.2.1, 3.2.4
     - Có
     - Split theo 4 trục, Add hỗ trợ broadcast mọi chiều [T1 OPL tr.56, tr.58, tr.91]
   * - SPPF
     - MaxPool
     - 3.2.44
     - Có
     - Kernel in (0, 7], auto_pad=NOTSET, không hỗ trợ ceil_mode [T1 OPL tr.79]
   * - Neck (FPN)
     - Resize
     - 3.2.54
     - Có điều kiện
     - Hệ số phóng 2-8, toolkit chuyển đổi thành ConvTranspose [T1 OPL tr.87, UG232 tr.176]
   * - Head (Cls)
     - Sigmoid
     - 3.2.63
     - Có
     - Áp dụng theo từng phần tử, kiểu INT8/FP16 [T1 OPL tr.95]
   * - Head (DFL)
     - Reshape, Softmax, Conv
     - 3.2.53, 3.2.56, 3.2.5
     - Có
     - Softmax giới hạn trên trục 1 hoặc 3 [T1 OPL tr.86, tr.88]
   * - Head (DFL)
     - Transpose
     - 3.2.62
     - Rơi về CPU
     - Vi phạm giới hạn kích thước hoán vị p=8192 [T1 OPL tr.93]

2. Op rơi về CPU và nguyên nhân
===============================

Mặc dù phần lớn đồ thị YOLOv8 thực thi trọn vẹn trên NPU, một số toán tử cấu trúc nhất định bị compiler đẩy về chạy trên CPU của SoC. Hiện tượng rơi về CPU (CPU fallback) tạo ra sự gián đoạn luồng dữ liệu, phát sinh chi phí sao chép bộ nhớ và đồng bộ hóa qua lại giữa NPU và CPU [T1 UG232 tr.139].

2.1 Toán tử Transpose và ràng buộc hoán vị trục
-----------------------------------------------

Toán tử hoán vị trục Transpose được định nghĩa tại mục 3.2.62 của OPL với bảng điều kiện ràng buộc hết sức khắt khe theo từng cấu hình tham số hoán vị ``perm`` [T1 OPL tr.93-95]:

..

   "不同 perm 参数限制如下：(其中 p=8192, q=2048 )" [T1 OPL tr.93]

Tài liệu OPL xác lập hai ngưỡng kích thước phần cứng cơ sở là ``p = 8192`` và ``q = 2048``. Tùy thuộc vào hoán vị cụ thể của các chiều, OPL áp đặt các ràng buộc toán học lên tích các chiều không gian của tensor:

- Đối với hoán vị ``perm = [0, 3, 1, 2]``: Yêu cầu ``h1 * w1 < p``, ``w1 < 8192``, và ``h1 * c1 < p`` [T1 OPL tr.93].
- Đối với hoán vị ``perm = [0, 1, 3, 2]`` với dữ liệu INT8: Yêu cầu ``h1 % 16 == 0``, ``h1 * w1 < 16 * p``, và ``h1 * w1 < 2 * q`` [T1 OPL tr.94].
- Cột chạy đa lõi của toán tử Transpose trên RK3588 ghi nhận trạng thái "暂不支持" [T1 OPL tr.93].

Nguyên nhân Transpose trong DFL rơi về CPU:

Trong đồ thị ONNX xuất từ PyTorch, trước khi đưa qua lớp Softmax và Conv 1x1 để giải mã kỳ vọng tọa độ, tensor đầu ra của nhánh hồi quy thường được định hình lại và hoán vị trục. Đối với ảnh đầu vào 640x640, tổng số điểm neo là 8400. Tensor trung gian có kích thước ``[1, 4, 16, 8400]`` (gồm batch=1, 4 cạnh tọa độ, 16 mức rời rạc của DFL, và 8400 vị trí không gian).

Để đưa trục phân bố 16 vào vị trí tính Softmax và nhân ma trận với vector trọng số, đồ thị ONNX chèn toán tử Transpose hoán vị giữa chiều phân bố và chiều không gian (ví dụ ``perm = [0, 3, 1, 2]`` hoặc các cấu hình tương đương). Khi đó, chiều không gian phẳng hóa ``w1 = 8400`` hoặc tích chiều ``h1 * w1 = 16 * 8400 = 134400``.

Giá trị tích chiều 134400 này vượt xa ngưỡng trần ``p = 8192`` quy định trong mục 3.2.62 [T1 OPL tr.93]. Do vượt quá dung lượng thanh ghi hoán vị và bộ đệm phần cứng nội bộ của NPU, compiler RKNN không thể tạo mã lệnh NPU cho node Transpose này và bắt buộc phải chuyển toán tử sang thực thi trên CPU máy host [T1 UG232 tr.139].

2.2 Các toán tử TopK và GatherElements trong NMS
------------------------------------------------

Khi người phát triển cố gắng triển khai mô hình theo mô hình end-to-end (nhúng trực tiếp bước hậu xử lý NMS vào đồ thị mạng), hàng loạt toán tử phi tuyến phức tạp được chèn vào đồ thị. Các toán tử này hoàn toàn không có sự hỗ trợ của phần cứng NPU:

1. Toán tử TopK:
   Nhiệm vụ của TopK là tìm kiếm và sắp xếp K phần tử có giá trị điểm số phân loại lớn nhất (ví dụ chọn 300 hộp tiềm năng nhất từ 8400 ứng viên).
   - Trong bảng hỗ trợ toán tử của toolkit (tệp ``RKNNToolKit2_OP_Support-2.3.2.md`` dòng 189), TopK được công bố rõ ràng là "Not Supported" ở cấp độ toolkit.
   - Trong toàn bộ 344 trang của OPL, TopK hoàn toàn vắng mặt trong chương 3.2 (danh mục NPU của RK3588) và chỉ xuất hiện duy nhất ở chương 4 CPU OPs tại mục 4.96 [T1 OPL tr.333].
   - Phần cứng NPU của RK3588 được tối ưu hóa cho mảng systolic nhân ma trận và xử lý khối tensor song song (SIMD/DPU), không tích hợp mạch logic rẽ nhánh để thực hiện thuật toán sắp xếp (sorting network) trên tập dữ liệu lớn.

2. Toán tử GatherElements:
   Sau khi TopK xác định chỉ số của các hộp bao có điểm cao nhất, GatherElements được sử dụng để trích xuất tọa độ hình học tương ứng từ tensor tọa độ thô.
   - OPL không có mục NPU cho GatherElements trong chương 3.2 [T1 OPL tr.56-107].
   - Toán tử này chỉ được liệt kê ở chương 4 CPU OPs tại mục 4.75 [T1 OPL tr.330].

3. Các toán tử logic và định hình trong đồ thị NMS:
   Chuỗi logic tính toán IoU và khử trùng lặp còn đòi hỏi các toán tử sau:
   - Mod (phép chia lấy dư để giải mã chỉ số lớp): mục CPU 4.72 [T1 OPL tr.329].
   - ReduceMax (tìm điểm cực đại giữa các lớp): mục CPU 4.44 [T1 OPL tr.325].
   - Equal (so sánh mặt nạ nhị phân): mục CPU 4.17 [T1 OPL tr.321].
   - Cast (chuyển đổi kiểu chỉ số sang int64): mục CPU 4.7 [T1 OPL tr.320]. OPL không hỗ trợ đích chuyển đổi int64 trên NPU.
   - Flatten (làm phẳng tensor chỉ số): mục CPU 4.19 [T1 OPL tr.322].

.. list-table:: Các toán tử có nguy cơ rơi về CPU trong đồ thị YOLOv8
   :header-rows: 1
   :widths: 20 20 20 40

   * - Toán tử
     - Vị trí trong mô hình
     - Vị trí trong OPL
     - Nguyên nhân kỹ thuật rơi về CPU
   * - Transpose
     - Khối DFL (Head)
     - 3.2.62 (NPU) / 4.63 (CPU)
     - Tích kích thước chiều phẳng hóa (134400) vượt ngưỡng trần p=8192 [T1 OPL tr.93]
   * - TopK
     - Nhánh NMS (End-to-End)
     - 4.96 (chỉ có CPU)
     - NPU không có khối phần cứng sắp xếp; OPSUP ghi Not Supported [T1 OPL tr.333]
   * - GatherElements
     - Nhánh NMS (End-to-End)
     - 4.75 (chỉ có CPU)
     - Không có mục NPU trong chương 3.2 [T1 OPL tr.330]
   * - Mod / Equal
     - Nhánh NMS (End-to-End)
     - 4.72, 4.17 (chỉ có CPU)
     - Toán tử số học nguyên và logic không được hỗ trợ trên NPU [T1 OPL tr.321, tr.329]
   * - Cast (đích int64)
     - Nhánh NMS (End-to-End)
     - 4.7 (chỉ có CPU)
     - NPU chỉ hỗ trợ kiểu dữ liệu số nguyên 8-bit và dấu phẩy động 16-bit [T1 OPL tr.320]

Do đó, việc duy trì cấu hình chuẩn (xuất tensor thô không có NMS nội suy) và loại bỏ các bước hoán vị trục không cần thiết trong Head là giải pháp tối ưu để đảm bảo 100% đồ thị được xử lý trọn vẹn trên NPU.

3. Hiểu sai thường gặp
======================

.. list-table:: Các hiểu sai phổ biến về việc hỗ trợ toán tử YOLOv8 trên RKNN
   :header-rows: 1
   :widths: 28 44 28

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Mọi toán tử Transpose trong mô hình YOLO đều chạy được trên NPU RK3588 vì OPL có mục 3.2.62.
     - OPL quy định điều kiện kích thước khắt khe theo từng cấu hình perm với các ngưỡng p=8192 và q=2048. Transpose trong DFL có tích chiều vượt ngưỡng nên bị đẩy về CPU.
     - [T1 OPL tr.93-95] [T1 UG232 tr.139]
   * - NPU RK3588 có thể tăng tốc toàn bộ quy trình phát hiện đối tượng bao gồm cả khâu chọn lọc TopK và NMS.
     - TopK và GatherElements không có mục NPU trong OPL chương 3.2, chỉ có ở chương 4 CPU. NPU không có phần cứng hỗ trợ các toán tử này.
     - [T1 OPL tr.330, tr.333]
   * - Phép kích hoạt SiLU luôn chạy dưới dạng các toán tử rời rạc gây lãng phí bộ nhớ trung gian.
     - OPL hỗ trợ mục 3.2.17 ConvolutionSwish cho phép hợp nhất phép tích chập và hàm kích hoạt SiLU trong cùng một lượt tính toán trên phần cứng NPU.
     - [T1 OPL tr.63]
   * - NPU RK3588 tích hợp nhân phần cứng chuyên dụng để xử lý toán tử phóng to Resize trong Neck.
     - Tài liệu UG232 xác nhận NPU chưa hỗ trợ Resize ở cấp độ phần cứng, và toolkit phải chuyển đổi Resize thành ConvTranspose để chạy trên NPU.
     - [T1 UG232 tr.176]
   * - Các toán tử trong khối C2f như Split và Add không thể thực thi song song trên phần cứng đa lõi.
     - Toán tử Add trong nhánh residual được OPL đánh dấu hỗ trợ đa lõi đầy đủ (cột đa lõi ghi "支持").
     - [T1 OPL tr.56]

Nguồn
=====

.. list-table:: Các nguồn tài liệu kỹ thuật được sử dụng trong trang
   :header-rows: 1
   :widths: 15 10 60 15

   * - Nhãn
     - Tier
     - Tệp / Tài liệu
     - Số lần trích
   * - ``OPL``
     - T1
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`
     - 27
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 4
