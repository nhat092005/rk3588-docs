:tocdepth: 1

***********************
Tiêu chí thân thiện NPU
***********************

.. admonition:: Trang này trả lời

   - Những toán tử nào có mục hỗ trợ phần cứng NPU trong OPL chương 3.2 và những ràng buộc kỹ thuật đi kèm là gì?
   - Hướng dẫn hiệu năng UG232 đưa ra các tiêu chí gì về bố cục bộ nhớ, căn chỉnh kênh và hạn chế toán tử phụ trợ?
   - Những toán tử phổ biến nào trong mạng nơ-ron không có mục NPU trong OPL và bị đẩy về CPU?
   - Khi đối chiếu các khối kiến trúc detector (Conv, DWConv, C2f/C3k2, SPPF, DFL, Attention) với tiêu chí NPU, khối nào thân thiện và khối nào gây nghẽn hiệu năng?

.. admonition:: Tóm tắt

   - OPL chương 3.2 cung cấp danh mục toán tử NPU cho RK3588 gồm Conv [T1 OPL tr.58], ConvolutionSwish [T1 OPL tr.63], Add [T1 OPL tr.56], Mul [T1 OPL tr.77], MaxPool [T1 OPL tr.79], Concat [T1 OPL tr.58], Split [T1 OPL tr.91], Resize [T1 OPL tr.86] và exSDPAttention [T1 OPL tr.104].
   - Hướng dẫn tối ưu UG232 khuyến nghị hạn chế tối đa 3 nhóm toán tử kém hiệu quả: truyền chuyển dữ liệu (Concat, Split, Transpose, Reshape), biến đổi kích thước (Pooling, Resize) và hàm kích hoạt phi-ReLU (Sigmoid) [T1 UG232 tr.146].
   - Về căn chỉnh dữ liệu, Conv INT8 yêu cầu số kênh vào và ra là bội số của 32 phần tử, trong khi Depthwise Conv INT8 yêu cầu căn chỉnh 64 phần tử để đạt hiệu suất tính toán tối ưu của mảng systolic [T1 UG232 tr.145].
   - Ràng buộc căn chỉnh chiều rộng (width) tại lớp đầu tiên ở OPL mục 5.1.2 chỉ áp dụng cho API zero-copy và không áp đặt lên API thông thường [T1 OPL tr.335].
   - Các toán tử như MatMul chuẩn, TopK, GatherElements, Cast, Flatten và ReduceMax không có mục NPU trong chương 3.2 mà chỉ có trong chương 4 CPU OPs của OPL [T1 OPL tr.320-333].
   - Đối chiếu kiến trúc cho thấy các khối tích chập tiêu chuẩn và C2f/C3k2 rất thân thiện với NPU, trong khi khối DFL (chứa Transpose phẳng hóa) và các nhánh NMS nội suy (TopK, GatherElements) tạo điểm nghẽn nghiêm trọng khi triển khai [T1 OPL tr.93-95, tr.330-333].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _95-tiêu-chí-thân-thiện-npu-cho-rk3588-t1:

1. Op có mục NPU trong OPL
==========================

Việc đánh giá mức độ tương thích của một kiến trúc mạng đối với NPU Rockchip RK3588 bắt đầu từ danh mục toán tử được hỗ trợ chính thức. Trong tài liệu RKNN Compiler Support Operator List (OPL) phiên bản V2.3.2, chương 3.2 liệt kê toàn bộ các toán tử có khả năng ánh xạ trực tiếp lên nhân tính toán NPU của RK3588 [T1 OPL tr.56-107].

.. _951-op-có-mục-npu-trong-opl-chương-32:

1.1 Các toán tử tính toán và kích hoạt
--------------------------------------

Nhóm toán tử tính toán đại số tuyến tính và phi tuyến tính chiếm phần lớn khối lượng tính toán (MAC operations) của mô hình:

- Tích chập tiêu chuẩn (Convolution, mục 3.2.5): Hỗ trợ nhân tích chập với ``kernel_h, kernel_w ∈ [1, 31]``, bước trượt ``stride_h, stride_w ∈ [1, 7]``, khoảng đệm ``pads ∈ [0, 15]``, và độ giãn nở ``dilations ∈ [1, 31]`` [T1 OPL tr.58-59]. Kiểu dữ liệu hỗ trợ gồm số nguyên INT8 và dấu phẩy động FP16. Mục này hỗ trợ chạy song song trên cả ba lõi NPU (cột đa lõi ghi "支持") [T1 OPL tr.58].
- Tích chập theo chiều sâu (Depthwise Convolution, mục 3.2.6): Ràng buộc kích thước nhân ``kernel_h, kernel_w ∈ [1, 8]`` và độ giãn nở ``dilations_h, dilations_w ∈ [1, 32]`` [T1 OPL tr.59-60]. Hỗ trợ chạy đa lõi "支持".
- Tích chập hợp nhất SiLU (ConvolutionSwish, mục 3.2.17): Hợp nhất tầng Conv và hàm kích hoạt SiLU thành một lệnh thực thi phần cứng duy nhất [T1 OPL tr.63]. Các thông số ràng buộc tương đương Convolution, cột đa lõi ghi "暂不支持".
- Hàm kích hoạt Sigmoid (mục 3.2.63): Áp dụng hàm sigmoid theo từng phần tử trên tensor INT8 hoặc FP16 [T1 OPL tr.95]. Cột đa lõi ghi "尚不支持".
- Phép cộng và nhân theo phần tử (Add, mục 3.2.1 và Mul, mục 3.2.41): Hỗ trợ cơ chế mở rộng chiều (broadcasting) kiểu Numpy trên mọi trục, có khả năng chạy đa lõi "支持" [T1 OPL tr.56, tr.77].
- Phép trừ (Sub, mục 3.2.60): Hạn chế cơ chế broadcast, chỉ hỗ trợ khi tensor thứ hai có dạng ``[b, c, 1, 1]`` hoặc là đại lượng vô hướng (scalar), đa lõi "不支持" [T1 OPL tr.91-92].
- Phép chia (Div, mục 3.2.33): Chỉ hỗ trợ kiểu dữ liệu FP16, không hỗ trợ đa lõi [T1 OPL tr.67].

1.2 Các toán tử định hình và lấy mẫu
------------------------------------

Nhóm toán tử thao tác trên cấu trúc không gian và hoán đổi trục dữ liệu:

- Tích gộp cực đại (MaxPool, mục 3.2.44): Hỗ trợ kích thước nhân trong khoảng ``(0, 7]`` và bước trượt trong khoảng ``(0, 8]`` [T1 OPL tr.79-80]. Ràng buộc chỉ hỗ trợ ``auto_pad = NOTSET``, không hỗ trợ chế độ làm tròn trần ``ceil_mode`` [T1 OPL tr.79].
- Phóng to nội suy (Resize, mục 3.2.54): Chỉ hỗ trợ phóng to nguyên lần từ 2 đến 8 theo chiều cao và rộng; hỗ trợ hai thuật toán ``nearest`` và ``linear``; các chế độ chuyển đổi tọa độ hợp lệ gồm ``half_pixel``, ``pytorch_half_pixel``, ``align_corners`` [T1 OPL tr.86-87].
- Ghép nối và chia tách tensor (Concat, mục 3.2.4 và Split, mục 3.2.59): Hỗ trợ thao tác trên 4 trục tọa độ ``axis ∈ {0, 1, 2, 3}`` [T1 OPL tr.58, tr.91].
- Trích xuất tensor con (Slice, mục 3.2.55): Chỉ hỗ trợ thực thi trên NPU khi bước nhảy ``steps == [1, 1, 1, 1]`` [T1 OPL tr.88].
- Chuẩn hóa xác suất (Softmax, mục 3.2.56): Chỉ hỗ trợ thực hiện trên trục 1 (channel) hoặc trục 3 (width), đồng thời chịu sự ràng buộc bởi các giới hạn của toán tử Transpose [T1 OPL tr.88-89].
- Thay đổi hình dạng (Reshape, mục 3.2.53): Hỗ trợ thay đổi kích thước các chiều trên kiểu dữ liệu INT8 và FP16 mà không làm thay đổi thứ tự bộ nhớ gốc [T1 OPL tr.86].
- Hoán vị trục (Transpose, mục 3.2.62): Áp dụng các giới hạn kích thước nghiêm ngặt dựa trên hai tham số phần cứng ``p = 8192`` và ``q = 2048`` theo từng hoán vị ``perm`` cụ thể [T1 OPL tr.93-95].
- Toán tử Attention chuyên dụng (exSDPAttention, mục 3.2.78): Hỗ trợ tính toán cơ chế chú ý tích vô hướng (Scaled Dot-Product Attention) trực tiếp trên NPU với giới hạn số kênh ``channel ∈ (0, 8192]`` [T1 OPL tr.104-105].

.. list-table:: Danh mục các toán tử NPU tiêu biểu trong OPL chương 3.2 cho RK3588
   :header-rows: 1
   :widths: 20 15 45 20

   * - Toán tử
     - Mục OPL 3.2
     - Ràng buộc kỹ thuật chính
     - Đa lõi NPU
   * - Conv / Depthwise Conv
     - 3.2.5 / 3.2.6
     - Conv: kernel in [1, 31], stride in [1, 7]; DWConv: kernel in [1, 8] [T1 OPL tr.58-60]
     - 支持 (Hỗ trợ)
   * - ConvolutionSwish
     - 3.2.17
     - Hợp nhất Conv và SiLU, ràng buộc tương tự Conv [T1 OPL tr.63]
     - 暂不支持
   * - Add / Mul
     - 3.2.1 / 3.2.41
     - Hỗ trợ broadcast mọi chiều theo chuẩn Expand [T1 OPL tr.56, tr.77]
     - 支持 (Hỗ trợ)
   * - MaxPool
     - 3.2.44
     - Kernel in (0, 7], stride in (0, 8], auto_pad=NOTSET [T1 OPL tr.79]
     - Không có dòng
   * - Resize
     - 3.2.54
     - Phóng to 2-8 lần, chế độ nearest/linear [T1 OPL tr.87]
     - 不支持
   * - Concat / Split
     - 3.2.4 / 3.2.59
     - Thao tác trên trục axis in {0, 1, 2, 3} [T1 OPL tr.58, tr.91]
     - Không có dòng
   * - Softmax
     - 3.2.56
     - Giới hạn trên trục 1 (channel) hoặc 3 (width) [T1 OPL tr.89]
     - 尚不支持
   * - Transpose
     - 3.2.62
     - Ràng buộc theo từng perm với ngưỡng p=8192, q=2048 [T1 OPL tr.93]
     - 暂不支持
   * - exSDPAttention
     - 3.2.78
     - Tính attention hợp nhất, channel in (0, 8192] [T1 OPL tr.104]
     - 不支持

.. _952-tiêu-chí-hiệu-năng-ug232:

2. Tiêu chí hiệu năng theo UG232
================================

Việc một toán tử có tên trong danh mục NPU chỉ đảm bảo tính khả thi về mặt biên dịch, không đồng nghĩa với việc toán tử đó đạt hiệu suất phần cứng cao. Tài liệu hướng dẫn người dùng Rockchip RKNPU User Guide (UG232) chương 8 đưa ra các nguyên tắc định lượng để thiết kế mô hình đạt hiệu năng tối ưu [T1 UG232 tr.140-150].

2.1 Căn chỉnh bộ nhớ và kích thước kernel
-----------------------------------------

Hiệu suất của mảng systolic trong mỗi NPU core phụ thuộc chặt chẽ vào cấu trúc căn lề dữ liệu trong bộ nhớ:

1. Căn chỉnh số lượng kênh (Channel Alignment):
   Theo Bảng 8-2 trong UG232 [T1 UG232 tr.145], các lớp Convolution kiểu INT8 yêu cầu số kênh đầu vào và đầu ra là bội số của 32 phần tử, trong khi Depthwise Conv INT8 yêu cầu bội số của 64 phần tử (32 phần tử với FP16) [T1 UG232 tr.145]. Nếu số kênh không chia hết cho các ngưỡng này, phần cứng phải chèn padding số 0, gây lãng phí chu kỳ tính toán và làm giảm hiệu suất sử dụng mảng nhân cộng (MAC utilization).

2. Tỷ số kích thước nhân và bước trượt:
   UG232 chỉ ra rằng tỷ số giữa kích thước nhân tích chập và bước trượt (``Ksize / Kstride``) càng lớn thì khả năng tái sử dụng dữ liệu trong bộ nhớ đệm cục bộ (SRAM buffer 384KB mỗi core) càng cao, dẫn đến hiệu suất phần cứng cao hơn [T1 UG232 tr.147]. Ngược lại, các tầng tích chập có stride lớn nhưng kernel nhỏ (ví dụ kernel 1x1 stride 2) tiêu tốn nhiều băng thông đọc dữ liệu từ DDR nhưng tính toán ít.
   Đồng thời, hiệu suất tính toán được duy trì ở mức tối đa khi dung lượng tham số nhân thỏa mãn bất đẳng thức:

   .. math::

      \text{KH} \times \text{KW} \times \text{KC} \times \text{type\_bytes} < 6\,\text{KB}

   Điều kiện này đảm bảo toàn bộ trọng số của một phép tính tích chập nằm vừa vặn trong bộ nhớ đệm tốc độ cao của DPU [T1 UG232 tr.147].

3. Ràng buộc căn chỉnh chiều rộng lớp đầu tiên:
   OPL mục 5.1.2 đưa ra bảng ràng buộc căn chỉnh chiều rộng (width) cho lớp tích chập đầu tiên của mạng đối với RK3588 (yêu cầu width chia hết cho 16 khi số kênh vào là 1, 3 hoặc 4) [T1 OPL tr.336]. Tuy nhiên, ghi chú 1 tại mục 5.1 quy định rõ ràng buộc căn lề này "该对齐约束仅针对零拷贝 API，普通 API 无此对齐约束" (chỉ áp dụng đối với zero-copy API, API thông thường không có ràng buộc này) [T1 OPL tr.335]. Các ứng dụng sử dụng standard API không bị hạn chế bởi điều kiện này.

2.2 Hợp nhất toán tử và hạn chế op kém hiệu quả
-----------------------------------------------

UG232 phân loại và khuyến nghị tinh gọn đồ thị dựa trên mức độ tiêu hao tài nguyên phần cứng:

1. Ba nhóm toán tử cần giảm thiểu (Bảng 8-5 trong UG232) [T1 UG232 tr.146]:
   - Nhóm truyền chuyển dữ liệu (Data transfer): Gồm ``Concat``, ``Split``, ``Transpose``, ``Reshape``. Các toán tử này không thực hiện phép tính toán học mà chỉ tổ chức lại dữ liệu trong bộ nhớ, tiêu tốn băng thông bus interconnect và DDR.
   - Nhóm biến đổi kích thước không gian (Size transformation): Gồm ``Pooling`` và ``Resize``.
   - Nhóm kích hoạt phi-ReLU (Non-ReLU activation function): Tiêu biểu là ``Sigmoid`` và ``Tanh``. Do đòi hỏi mạch tính phi tuyến hoặc bảng tra phần cứng phức tạp, chúng tiêu tốn năng lượng và thời gian xử lý nhiều hơn so với ReLU hoặc LeakyReLU.

2. Chiến lược hợp nhất toán tử (Operator Fusion):
   Compiler của RKNN hỗ trợ tự động gộp các toán tử liên tiếp thành một khối tính toán đơn [T1 UG232 tr.141-142]:
   - Mô hình hợp nhất hiện tại: Chuỗi tích chập kết hợp hàm kích hoạt (``Conv + Sigmoid / Tanh / Elu / Silu``) được gộp hoàn toàn thành một toán tử NPU duy nhất [T1 UG232 tr.142].
   - Hợp nhất khối Attention: Nhằm tối ưu hóa cơ chế Multi-Head Attention, RKNN-Toolkit2 cung cấp tham số ``enable_flash_attention`` trong API cấu hình ``rknn.config`` [T1 API232 tr.10]. Khi kích hoạt cờ này, compiler sẽ nhận diện chuỗi tính toán chú ý và hợp nhất trực tiếp thành toán tử phần cứng ``exSDPAttention``, loại bỏ sự phân rã thành các phép nhân ma trận rời rạc [T1 OPL tr.104].

.. list-table:: Các tiêu chí hiệu năng NPU cốt lõi theo tài liệu UG232
   :header-rows: 1
   :widths: 25 25 50

   * - Tiêu chí
     - Tài liệu tham chiếu
     - Nội dung kỹ thuật và khuyến nghị
   * - Căn chỉnh kênh Conv
     - UG232 Bảng 8-2, tr.145
     - Số kênh vào/ra của Conv INT8 phải là bội số của 32 phần tử để mảng tính toán đạt hiệu suất tối đa.
   * - Căn chỉnh kênh Depthwise
     - UG232 Bảng 8-2, tr.145
     - Số kênh của Depthwise Conv INT8 phải là bội số của 64 phần tử (32 phần tử với FP16).
   * - Tỷ số Ksize / Kstride
     - UG232 tr.147
     - Tỷ số Ksize/Kstride càng lớn thì tái sử dụng dữ liệu trong buffer 384KB càng cao. Trọng số dưới 6KB nằm trọn trong cache DPU.
   * - Giảm toán tử kém hiệu quả
     - UG232 Bảng 8-5, tr.146
     - Hạn chế 3 nhóm: truyền chuyển dữ liệu (Concat, Split, Transpose), biến đổi kích thước (Resize), và phi-ReLU (Sigmoid).
   * - Hợp nhất kích hoạt
     - UG232 tr.141-142
     - Tận dụng quy tắc hợp nhất Conv + Activation (SiLU, Sigmoid) để tránh ghi tensor trung gian ra bộ nhớ.
   * - Hợp nhất Flash Attention
     - API232 tr.10, OPL tr.104
     - Cấu hình enable_flash_attention=True để gộp chuỗi chú ý thành toán tử exSDPAttention trên NPU.

.. _953-op-không-có-mục-npu-trong-opl:

3. Op không có mục NPU trong OPL
================================

Khi một mô hình chứa các toán tử không nằm trong danh mục chương 3.2, compiler RKNN buộc phải đẩy toán tử đó sang thực thi trên CPU thông qua chương trình con CPU OPs (được định nghĩa trong chương 4 của OPL) [T1 OPL tr.319-334].

3.1 Nhóm toán tử ma trận và chọn lọc cực đại
--------------------------------------------

Một số toán tử đại số và thuật toán quan trọng hoàn toàn thiếu vắng nhân phần cứng NPU tương ứng:

1. Toán tử nhân ma trận tiêu chuẩn (MatMul):
   - Trong chương 3.2, OPL hoàn toàn không có mục NPU tổng quát cho toán tử ``MatMul`` [T1 OPL tr.56-107].
   - Toán tử này chỉ xuất hiện trong chương 4 CPU OPs tại mục 4.33 (tr.324) với ghi chú "无限制" (không giới hạn hình dạng ma trận) [T1 OPL tr.324].
   - Mục NPU duy nhất liên quan là ``exMatMul`` (mục 3.2.76, tr.102), tuy nhiên mục này áp đặt điều kiện vô cùng khắt khe: ma trận A phải có dạng ``[b, k, 1, n]`` với số kênh thu gọn ``k ∈ (0, 8192]`` [T1 OPL tr.102]. Nếu một phép nhân ma trận đa chiều trong ONNX không khớp với khuôn mẫu của ``exMatMul`` hoặc không được hợp nhất qua cơ chế Attention, nó sẽ rơi về CPU.

2. Toán tử chọn lọc TopK và phân tán GatherElements:
   - Toán tử TopK chỉ có duy nhất mục CPU 4.96 [T1 OPL tr.333]. Bảng hỗ trợ của toolkit (tệp ``RKNNToolKit2_OP_Support-2.3.2.md``) đánh dấu TopK là "Not Supported". NPU không có nhân phần cứng để thực hiện thuật toán sắp xếp song song.
   - Toán tử GatherElements chỉ xuất hiện trong danh mục CPU tại mục 4.75 [T1 OPL tr.330].

3.2 Nhóm toán tử biến đổi kiểu và hình học động
-----------------------------------------------

Các toán tử phục vụ kiểm tra logic và chuyển đổi kiểu dữ liệu:

1. Chuyển đổi kiểu dữ liệu (Cast):
   - Toán tử Cast được quy định tại mục CPU 4.7 [T1 OPL tr.320].
   - Danh sách kiểu dữ liệu đích được hỗ trợ bao gồm ``float32``, ``int8``, ``int32``, và ``float16`` [T1 OPL tr.320]. OPL hoàn toàn không hỗ trợ đích chuyển đổi sang kiểu số nguyên 64-bit (``int64``) trên NPU.

2. Các toán tử logic và rút gọn:
   - Phép làm phẳng tensor (Flatten): chỉ có mục CPU 4.19 [T1 OPL tr.322].
   - Phép tìm cực đại theo trục (ReduceMax): chỉ có mục CPU 4.44 [T1 OPL tr.325].
   - Phép chia lấy phần dư (Mod): chỉ có mục CPU 4.72 [T1 OPL tr.329].
   - Phép so sánh bằng (Equal): chỉ có mục CPU 4.17 [T1 OPL tr.321].

3. Nhóm toán tử hình học hoàn toàn không có trong OPL:
   Các toán tử như ``Shape``, ``ConstantOfShape``, và ``Unsqueeze`` không có mục trong cả chương 3.2 lẫn chương 4 của OPL. Tài liệu UG232 chỉ ra rằng các toán tử này biểu diễn các bước tính toán hình dạng động và được compiler triệt tiêu tĩnh thông qua cơ chế gấp hằng số (``_fold_constant remove nodes``) trước khi sinh đồ thị thực thi [T1 UG232 tr.167].

.. list-table:: Các toán tử ONNX phổ biến không có mục NPU trong OPL chương 3.2
   :header-rows: 1
   :widths: 20 20 20 40

   * - Toán tử
     - Vị trí trong OPL
     - Tình trạng trên NPU
     - Tác động khi xuất hiện trong mô hình
   * - MatMul
     - CPU 4.33, tr.324
     - Không có mục NPU tổng quát
     - Rơi về CPU trừ khi khớp khuôn dạng exMatMul hoặc được gộp thành exSDPAttention [T1 OPL tr.102, tr.104, tr.324].
   * - TopK / GatherElements
     - CPU 4.96 / 4.75
     - Không hỗ trợ NPU
     - Bắt buộc chạy trên CPU host; toolkit tắt end2end khi xuất RKNN [T1 OPL tr.330, tr.333, ULT engine/exporter.py:685-688].
   * - Cast (đích int64)
     - CPU 4.7, tr.320
     - Không hỗ trợ int64
     - Gây phân rã đồ thị nếu tensor chỉ số đòi hỏi kiểu int64 [T1 OPL tr.320].
   * - Mod / Equal / ReduceMax
     - CPU 4.72, 4.17, 4.44
     - Không hỗ trợ NPU
     - Thường gặp trong logic lọc ngưỡng hộp, đẩy luồng tính toán về CPU [T1 OPL tr.321, tr.325, tr.329].

.. _97-đối-chiếu-khối-kiến-trúc-với-tiêu-chí:

4. Đối chiếu khối kiến trúc với tiêu chí
========================================

Căn cứ vào danh mục OPL và các tiêu chí hiệu năng của UG232, các khối chức năng trong các kiến trúc detector hiện đại (như YOLOv8 và các biến thể) được đánh giá theo mức độ thân thiện phần cứng.

4.1 Các khối thân thiện với NPU
-------------------------------

Những cấu trúc đạt hiệu suất tính toán tối đa và không gây gián đoạn luồng thực thi:

1. Tích chập tiêu chuẩn (Conv 3x3 và 1x1, stride 1 và 2):
   - Thân thiện tuyệt đối với NPU RK3588. Các tầng tích chập tiêu chuẩn tận dụng tối đa mảng systolic, hỗ trợ chạy song song trên cả 3 core NPU (cột đa lõi ghi "支持") [T1 OPL tr.58].
   - Khi kết hợp với SiLU, compiler tự động hợp nhất thành ConvolutionSwish [T1 OPL tr.63], loại bỏ chi phí truy cập bộ nhớ trung gian.

2. Khối C2f và C3k2:
   - Các phép tính cốt lõi bao gồm Conv 1x1, Split chia nhánh [T1 OPL tr.91], Bottleneck (Conv 3x3) và phép cộng phần tử Add trong nhánh residual [T1 OPL tr.56].
   - Toàn bộ các toán tử này đều có mục NPU hợp lệ trong OPL chương 3.2. Phép cộng Add hỗ trợ chạy đa lõi đầy đủ. Mặc dù Split và Concat thuộc nhóm truyền chuyển dữ liệu cần tiết giảm theo UG232 tr.146, chúng hoàn toàn không gây hiện tượng rơi về CPU.

3. Khối SPPF:
   - Sử dụng 3 tầng MaxPool kích thước 5x5 stride 1 kết hợp các phép nối Concat.
   - Kích thước nhân 5x5 thỏa mãn ràng buộc ``kernel in (0, 7]`` của OPL mục 3.2.44 [T1 OPL tr.79]. Toàn bộ khối SPPF chạy trọn vẹn trên NPU mà không gặp bất kỳ trở ngại nào về mặt phần cứng.

4.2 Các khối kém thân thiện và định hướng thiết kế
--------------------------------------------------

Những thành phần kiến trúc gây nghẽn hiệu năng hoặc làm phân rã đồ thị:

1. Khối Distribution Focal Loss (DFL):
   - Cấu trúc DFL sử dụng Reshape, Softmax và đặc biệt là toán tử Transpose để đảo trục phân bố trên tensor đã làm phẳng không gian (8400 điểm neo).
   - Tích các chiều phẳng hóa (ví dụ 16 * 8400 = 134400) vượt xa ngưỡng phần cứng ``p = 8192`` quy định trong mục 3.2.62 [T1 OPL tr.93], khiến toán tử Transpose bị đẩy về CPU.
   - Định hướng thiết kế: Loại bỏ hoàn toàn khối DFL trong các mô hình biên (edge detectors), thay thế bằng nhánh hồi quy tọa độ trực tiếp sử dụng Conv 1x1 xuất ra 4 kênh (như kiến trúc no-DFL hoặc anchor-free trực tiếp).

2. Tích chập Depthwise (DWConv):
   - Mặc dù OPL mục 3.2.6 hỗ trợ DWConv trên NPU [T1 OPL tr.59-60], nhưng UG232 Bảng 8-2 yêu cầu căn chỉnh kênh INT8 lên tới 64 phần tử [T1 UG232 tr.145]. Đồng thời, do không có sự kết hợp chéo giữa các kênh, tỷ số tái sử dụng trọng số rất thấp, dẫn đến hiệu suất phần cứng (MAC utilization) thực tế thấp hơn đáng kể so với Conv thông thường [T1 UG232 tr.147].
   - Định hướng thiết kế: Ưu tiên sử dụng tích chập tiêu chuẩn 3x3 hoặc cấu trúc Conv 1x1 kết hợp pooling thay cho DWConv trên RK3588.

3. Khối chú ý Attention:
   - Các phép tính Multi-Head Self-Attention rời rạc chứa nhiều node MatMul không tương thích NPU và các phép Softmax đa chiều.
   - Định hướng thiết kế: Cấu hình cờ ``enable_flash_attention`` trong quá trình chuyển đổi để kích hoạt toán tử hợp nhất ``exSDPAttention`` của NPU [T1 API232 tr.10, OPL tr.104].

4. Nhánh chọn lọc End-to-end NMS:
   - Chứa TopK, GatherElements và các phép logic kiểu int64, hoàn toàn không được NPU hỗ trợ [T1 OPL tr.320, tr.330, tr.333].
   - Định hướng thiết kế: Giữ nguyên mô hình xuất tensor thô không có NMS, đưa toàn bộ khâu lọc hộp ra ngoài đồ thị để chạy trên CPU máy host [T1 ULT engine/exporter.py:685-688].

.. list-table:: Tổng hợp đối chiếu các khối kiến trúc detector với tiêu chí NPU
   :header-rows: 1
   :widths: 18 22 25 35

   * - Khối kiến trúc
     - Toán tử cấu thành
     - Mức độ thân thiện NPU
     - Khuyến nghị thiết kế
   * - Conv tiêu chuẩn
     - Conv, BatchNorm, SiLU
     - Rất cao (Thân thiện)
     - Khai thác tối đa; tận dụng hợp nhất ConvolutionSwish và đa lõi [T1 OPL tr.58, tr.63].
   * - C2f / C3k2
     - Split, Conv, Add, Concat
     - Cao (Thân thiện)
     - Giữ số kênh là bội số của 32 để căn chỉnh tối ưu mảng systolic [T1 UG232 tr.145].
   * - SPPF
     - MaxPool 5x5, Concat, Conv
     - Cao (Thân thiện)
     - Duy trì kích thước kernel <= 7 và auto_pad=NOTSET theo đúng OPL [T1 OPL tr.79].
   * - Depthwise Conv
     - DWConv 3x3
     - Trung bình (Hiệu suất thấp)
     - Cần căn chỉnh 64 kênh INT8; cân nhắc thay bằng Conv tiêu chuẩn nếu kênh nhỏ [T1 UG232 tr.145].
   * - DFL
     - Reshape, Transpose, Softmax
     - Thấp (Gây rơi về CPU)
     - Loại bỏ DFL, chuyển sang hồi quy tọa độ trực tiếp bằng Conv 1x1 [T1 OPL tr.93].
   * - Attention
     - MatMul, Softmax, Transpose
     - Trung bình (Cần hợp nhất)
     - Bắt buộc bật enable_flash_attention để chuyển thành exSDPAttention [T1 API232 tr.10, OPL tr.104].
   * - End-to-end NMS
     - TopK, GatherElements, Cast
     - Rất thấp (Không hỗ trợ)
     - Đặt ngoài đồ thị; thực thi NMS trên CPU host sau suy luận [T1 ULT engine/exporter.py:685-688].

5. Hiểu sai thường gặp
======================

.. list-table:: Các hiểu sai phổ biến về tiêu chí thân thiện NPU trên RK3588
   :header-rows: 1
   :widths: 28 44 28

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Tích chập Depthwise (DWConv) luôn nhẹ hơn và chạy nhanh hơn tích chập thông thường trên NPU RK3588.
     - DWConv có tỷ lệ tái sử dụng tham số thấp và đòi hỏi căn chỉnh kênh INT8 tới 64 phần tử (so với 32 của Conv thường), dẫn đến hiệu suất phần cứng (MAC utilization) thực tế thấp hơn nhiều so với Conv tiêu chuẩn.
     - [T1 UG232 tr.145-147]
   * - Mọi mô hình có chứa phép nhân ma trận MatMul đều có thể chạy hoàn toàn trên phần cứng NPU.
     - OPL chương 3.2 chỉ hỗ trợ dạng exMatMul hạn chế (k <= 8192 và shape tensor đặc thù), còn MatMul tổng quát chỉ có mục CPU 4.33 và sẽ rơi về CPU nếu không được hợp nhất.
     - [T1 OPL tr.102, tr.324]
   * - Ràng buộc căn chỉnh chiều rộng lớp đầu tiên (width alignment) bắt buộc phải tuân thủ trong mọi dự án triển khai.
     - OPL mục 5.1 ghi chú rõ ràng ràng buộc căn lề chiều rộng này chỉ áp dụng đối với zero-copy API, còn API thông thường không bị ràng buộc.
     - [T1 OPL tr.335]
   * - Khối DFL chỉ gồm các phép tính toán học đơn giản nên không ảnh hưởng đến hiệu năng trên NPU.
     - Phép Transpose trong DFL thao tác trên tensor có chiều phẳng hóa 8400, vi phạm giới hạn kích thước hoán vị của NPU (p=8192) và rơi về CPU, gây chi phí đồng bộ hóa dữ liệu.
     - [T1 OPL tr.93-95] [T1 UG232 tr.139]
   * - Toán tử Resize phóng to ảnh luôn được NPU tăng tốc bằng nhân phần cứng chuyên dụng.
     - Tài liệu UG232 xác nhận NPU chưa có nhân phần cứng cho Resize và toolkit thực hiện chuyển đổi Resize thành ConvTranspose để chạy trên NPU.
     - [T1 UG232 tr.176]

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
     - 41
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 17
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 4
   * - ``ULT``
     - T1
     - Mã nguồn thư viện Ultralytics (engine/exporter.py)
     - 3
