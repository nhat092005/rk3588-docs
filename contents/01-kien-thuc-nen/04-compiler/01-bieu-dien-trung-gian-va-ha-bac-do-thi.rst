:tocdepth: 1

*************************************
Biểu diễn trung gian và hạ bậc đồ thị
*************************************

.. admonition:: Trang này trả lời

   - Đồ thị mạng nơ-ron được biến thành lệnh phần cứng qua những tầng biểu diễn trung gian nào?
   - TVM và eIQ Neutron giải quyết bài toán hạ bậc và tối ưu ở từng tầng như thế nào?
   - Yếu tố nào cố định theo phần cứng và yếu tố nào compiler hoặc người dùng có thể can thiệp?

.. admonition:: Tóm tắt

   - Compiler AI hạ bậc mô hình qua 3 tầng biểu diễn: Đồ thị tính toán mức cao (Computational Graph IR), Biểu diễn mức vòng lặp (Loop-level IR), và Lệnh phần cứng (Hardware Instructions) [T2 TVM tr.3] [T2 BAMB tr.4].
   - Đồ thị mức cao xem xét luồng dữ liệu thô giữa các tensor nhiều chiều, cho phép thực hiện các phép tối ưu độc lập thiết bị như constant folding và operator fusion [T2 TVM tr.3].
   - Biểu diễn mức vòng lặp cụ thể hóa việc lặp qua tensor, xác định lịch trình tính toán (tiling, unroll, sắp xếp vòng lặp) theo dung lượng bộ đệm [T2 TVM tr.4].
   - TVM phân tách định nghĩa thuật toán khỏi lịch thực thi và dùng mô hình học máy (AutoTVM) để tự động tìm kiếm cấu hình lịch trình tối ưu [T2 TVM tr.8].
   - eIQ Neutron minh chứng cho phương pháp đồng thiết kế phần cứng và compiler (HW/SW co-design), dùng quy hoạch ràng buộc để đồng thời chia tile và hợp nhất lớp nhằm hạn chế nghẽn DRAM [T2 BAMB tr.4] [T2 BAMB tr.9].
   - Dung lượng SRAM, băng thông DRAM và tập lệnh phần cứng là cố định; chiến lược fusion, kích thước tile và lập lịch DMA là các quyết định do compiler lựa chọn.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Các tầng biểu diễn trung gian
================================

Quá trình chuyển đổi một mô hình học sâu từ framework (PyTorch, TensorFlow, ONNX) xuống phần cứng suy luận trải qua nhiều tầng biểu diễn trung gian (Intermediate Representation - IR). Mỗi tầng phản ánh một mức độ trừu tượng hóa khác nhau nhằm phục vụ các mục tiêu tối ưu chuyên biệt.

.. list-table::
   :header-rows: 1
   :widths: 22 26 30 22

   * - Tầng biểu diễn
     - Dữ liệu thao tác
     - Nhiệm vụ và tối ưu chính
     - Nguồn
   * - Đồ thị mức cao (Graph IR)
     - Toán tử thô, tensor đa chiều
     - Gộp toán tử (fusion), gấp hằng số (constant folding), chuẩn hóa layout
     - [T2 TVM tr.3]
   * - Mức vòng lặp (Loop-level IR)
     - Vòng lặp lồng nhau, bộ đệm tạm thời
     - Phân khối (tiling), duỗi vòng lặp (unroll), đổi thứ tự lặp (reorder)
     - [T2 TVM tr.4] [T2 BAMB tr.4]
   * - Lệnh phần cứng (Machine code / ISA)
     - Thanh ghi, địa chỉ bộ nhớ vật lý, lệnh DMA
     - Tensorization, phát sinh lệnh vi mã, cấu hình thanh ghi phần cứng
     - [T2 TVM tr.4] [T2 BAMB tr.4]

1.1 Đồ thị tính toán mức cao (High-level computation graph)
-----------------------------------------------------------

Ở tầng trên cùng, mô hình được biểu diễn dưới dạng đồ thị có hướng không chu trình (Directed Acyclic Graph - DAG). Mỗi nút đại diện cho một toán tử tính toán (như tích chập Conv2D, hàm kích hoạt ReLU, hoặc phép cộng Add) và mỗi cạnh đại diện cho luồng phụ thuộc dữ liệu của tensor nhiều chiều.

Khác với các IR truyền thống của trình biên dịch đa dụng (chẳng hạn LLVM IR vốn thao tác trên các giá trị vô hướng hoặc thanh ghi nhỏ), đồ thị mức cao giữ lại thông tin ngữ nghĩa toàn cục và shape của tensor. Tuy nhiên, nó trừu tượng hóa hoàn toàn chi tiết cài đặt của từng phép tính:

   "Computational graphs provide a global view of operators, but they avoid specifying how each operator must be implemented." [T2 TVM tr.3]

Nhờ góc nhìn toàn cục này, compiler có thể áp dụng các phép biến đổi đồ thị tương đương về mặt hàm số mà không phụ thuộc vào phần cứng cụ thể:

   "Like LLVM IRs, a computational graph can be transformed into functionally equivalent graphs to apply optimizations." [T2 TVM tr.3]

Trong các tác vụ học sâu thông thường, kích thước đầu vào thường được cố định từ trước (shape specificity) [T2 TVM tr.3]. Compiler tận dụng đặc điểm này để thực hiện lập kế hoạch bộ nhớ tĩnh (static memory planning), gán trước vùng nhớ đệm cho từng tensor trung gian nhằm triệt tiêu chi phí cấp phát động trong thời gian suy luận [T2 TVM tr.3].

Các phép tối ưu đồ thị phổ biến bao gồm gộp toán tử (operator fusion), tính toán trước các giá trị tĩnh (constant-folding), lập kế hoạch cấp phát bộ nhớ tĩnh cho tensor trung gian, và chuyển đổi layout dữ liệu giữa các toán tử [T2 TVM tr.3].

1.2 Biểu diễn mức vòng lặp (Loop-level IR)
------------------------------------------

Sau khi tối ưu ở cấp đồ thị, từng toán tử (hoặc cụm toán tử đã gộp) phải được hạ bậc (lowering) xuống biểu diễn mức vòng lặp. Tại tầng này, một phép toán trừu tượng như tích chập 4 chiều được cụ thể hóa thành các vòng lặp lồng nhau (nested loops) duyệt qua các trục kích thước: batch (N), kênh xuất (C_out), kênh nhập (C_in), chiều cao (H) và chiều rộng (W) [T2 BAMB tr.4].

Biểu diễn mức vòng lặp (chẳng hạn như cây cú pháp AST trong TVM dựa trên ý tưởng từ Halide) cho phép can thiệp vào cách tổ chức tính toán thông qua khái niệm lịch trình (schedule):

- **Tiling (chia khối)**: Chia các trục lặp lớn thành các khối nhỏ vừa vặn với dung lượng bộ đệm SRAM on-chip, ngăn ngừa hiện tượng tràn dữ liệu ra DRAM [T2 TVM tr.4] [T2 BAMB tr.4].
- **Reordering (đổi thứ tự vòng lặp)**: Hoán đổi thứ tự các vòng lặp ngoài và vòng lặp trong nhằm tối đa hóa việc tái sử dụng dữ liệu (data reuse) của trọng số hoặc activation trên thanh ghi và bộ đệm nội bộ.
- **Unrolling và Vectorization**: Duỗi các vòng lặp có số bước cố định để tận dụng các đơn vị tính toán SIMD hoặc giảm chi phí rẽ nhánh của vi điều khiển.
- **Quản lý bộ nhớ đệm**: Chèn các thao tác nạp dữ liệu từ bộ nhớ ngoài vào bộ đệm nội bộ và ghi kết quả trở lại (cache_read, cache_write) [T2 TVM tr.4].
- **Lồng ghép điểm tính (compute_at)**: Xác định vị trí vòng lặp cụ thể mà tensor trung gian sẽ được tính toán, cho phép tính toán theo từng phần nhỏ ngay trước khi toán tử tiêu thụ cần đến [T2 TVM tr.5].

1.3 Lệnh phần cứng (Hardware instructions)
------------------------------------------

Ở tầng thấp nhất, compiler hạ bậc biểu diễn mức vòng lặp thành luồng lệnh thực thi thực tế của mục tiêu phần cứng. Tùy thuộc vào kiến trúc vi xử lý, tầng này phát sinh mã máy cho CPU/GPU (qua backend LLVM hoặc CUDA), hoặc chuỗi lệnh cấu hình và điều khiển cho NPU [T2 TVM tr.4] [T2 BAMB tr.4]:

- **Tensorization**: Kỹ thuật mở rộng từ vector hóa (vectorization), ánh xạ các khối vòng lặp tính toán nhiều chiều trực tiếp vào các lệnh phần cứng chuyên dụng của bộ gia tốc (ví dụ: các lệnh nhân ma trận 8x8 GEMM hoặc chỉ thị mảng systolic) [T2 TVM tr.4].
- **Thiết lập DMA và thanh ghi**: Cấu hình các kênh DMA để nạp tensor, thiết lập kích thước bước nhảy (stride), kích hoạt ngắt, và chỉ đạo các engine tính toán trong core NPU [T2 BAMB tr.3] [T2 BAMB tr.4].

2. TVM
======

TVM là một hệ thống compiler mã nguồn mở tiêu biểu cho học sâu, cung cấp khung làm việc hoàn chỉnh từ đồ thị mức cao đến mã máy đa nền tảng [T2 TVM tr.3].

2.1 Tối ưu đồ thị và tối ưu toán tử
-----------------------------------

TVM tổ chức quá trình biên dịch thành hai giai đoạn phân định rõ ràng:

1. **Tối ưu cấp đồ thị**: Mô hình đầu vào được chuyển thành đồ thị tính toán. TVM phân loại các toán tử thành 4 nhóm chính [T2 TVM tr.3]:

   - *Injective*: Ánh xạ 1-1 từng phần tử (ví dụ: ReLU, Add, BiasAdd).
   - *Reduction*: Thu gọn tensor theo trục (ví dụ: Sum, Max pooling).
   - *Complex-out-fusable*: Toán tử tính toán phức tạp có khả năng gộp các phép toán từng phần tử ở ngõ ra (ví dụ: Conv2D, MatMul).
   - *Opaque*: Toán tử đặc thù không hỗ trợ gộp (ví dụ: Sort).

   Dựa trên phân loại này, TVM áp dụng các quy tắc hợp nhất: nhiều toán tử injective có thể gộp thành một injective mới; toán tử reduction có thể gộp với các injective ở đầu vào; và toán tử complex-out-fusable có thể gộp với các injective ở đầu ra [T2 TVM tr.3]. Kết quả là tạo ra các kernel gộp giúp tăng tốc từ 1.2x đến 2x nhờ giảm số lượt truy cập bộ nhớ ngoài [T2 TVM tr.4].

2. **Tối ưu cấp toán tử**: TVM sử dụng ngôn ngữ biểu thức tensor khai báo (Tensor Expression). Điểm mấu chốt là sự phân tách giữa đặc tả thuật toán (tính cái gì) và cấu hình lịch trình (tính như thế nào) [T2 TVM tr.4]. Kỹ sư hoặc hệ thống tự động có thể thử nghiệm nhiều lịch trình khác nhau (thay đổi kích thước tile, hoán đổi thứ tự vòng lặp) mà không sợ làm sai lệch kết quả toán học.

2.2 Tự tìm lịch tính toán bằng học máy (Auto-tuning / AutoTVM)
--------------------------------------------------------------

Không gian lịch trình (schedule space) cho mỗi toán tử là vô cùng rộng lớn: có hàng triệu cách kết hợp kích thước tile, hệ số duỗi lặp và thứ tự vòng lặp. Phương pháp dò tìm hộp đen truyền thống (blackbox auto-tuning) dựa vào việc chạy thử từng cấu hình trên phần cứng thực tế đòi hỏi số lượng phép đo khổng lồ và rất tốn kém [T2 TVM tr.8].

Để khắc phục nhược điểm này, TVM tích hợp bộ tối ưu tự động dựa trên mô hình học máy:

   "ML-based cost models strike a balance between auto-tuning and predefined cost modeling" [T2 TVM tr.8]

Mô hình chi phí học máy (thường dùng Gradient Boosted Trees - XGBoost hoặc Tree-RNN) nhận đầu vào là các đặc trưng trích xuất từ cây cú pháp của chương trình vòng lặp (Loop AST) và dự đoán độ trễ thực thi [T2 TVM tr.8] [T2 TVM tr.9]. Hệ thống tìm kiếm (schedule explorer) sử dụng mô hình chi phí này để định hướng không gian tìm kiếm, chỉ chọn lọc những cấu hình có triển vọng nhất để thẩm định trên phần cứng thực tế, giúp tăng tốc độ tìm kiếm lịch trình tối ưu lên nhiều lần [T2 TVM tr.8] [T2 TVM tr.9].

3. eIQ Neutron
==============

eIQ Neutron của NXP là một trường hợp nghiên cứu điển hình về việc xây dựng NPU song hành cùng công cụ biên dịch cho các hệ thống nhúng biên [T2 BAMB tr.1] [T2 BAMB tr.3].

3.1 Đồng thiết kế NPU và compiler
---------------------------------

Thay vì thiết kế phần cứng NPU trước rồi mới xây dựng compiler thích nghi sau, eIQ Neutron áp dụng phương pháp đồng thiết kế phần cứng và phần mềm (HW/SW co-design) [T2 BAMB tr.1] [T2 BAMB tr.9]:

- Phần cứng tích hợp mảng tính toán gần bộ nhớ, vi điều khiển nhẹ kiến trúc RISC-V, bộ điều khiển DMA và các khối bộ nhớ đệm nội bộ (SRAM / Tightly Coupled Memory - TCM) chia theo ngân hàng (banks) [T2 BAMB tr.3].
- Compiler eIQ Neutron chia thành 3 phần: frontend nhập đồ thị mô hình; mid-end chịu trách nhiệm hạ bậc và tối ưu đồ thị thông qua các kỹ thuật then chốt; backend phát sinh luồng lệnh điều khiển cho vi điều khiển RISC-V và bộ điều khiển DMA [T2 BAMB tr.4]:

   "the mid-end lowers and optimizes the graph through tiling, scheduling, and memory allocation" [T2 BAMB tr.4]

Mid-end của eIQ Neutron sử dụng thuật toán giải quy hoạch ràng buộc (Constraint Programming) để giải đồng thời bài toán phân khối không gian (spatial tiling), phân khối thời gian (temporal tiling) và hợp nhất lớp (layer fusion) nhằm đảm bảo toàn bộ tensor trung gian nằm trọn trong SRAM nội bộ [T2 BAMB tr.4] [T2 BAMB tr.7]. Trong đó, spatial tiling khai thác line parallelism (phân chia tính toán theo từng dòng chiều cao outH) để các engine chia sẻ chung trọng số thông qua cơ chế broadcast [T2 BAMB tr.4].

3.2 Bài học tổng quát và giới hạn suy diễn
------------------------------------------

Nghiên cứu về eIQ Neutron mang lại kết luận nền tảng cho việc thiết kế và đánh giá hệ thống suy luận biên:

   "confirm that intelligent HW/SW co-design, not raw TOPS, determines real-world edge-AI performance." [T2 BAMB tr.9]

Một bộ xử lý có chỉ số TOPS danh định cao nhưng thiếu sự phối hợp giữa dung lượng SRAM và thuật toán compiler sẽ liên tục bị nghẽn ở băng thông DRAM, dẫn đến hiệu năng thực tế kém hơn một bộ xử lý có TOPS thấp hơn nhưng compiler giữ được dữ liệu tính toán hoàn toàn trong SRAM on-chip [T2 BAMB tr.8] [T2 BAMB tr.9].

**Giới hạn suy diễn khi áp dụng cho phần cứng khác:** eIQ Neutron được xây dựng dựa trên kiến trúc vi điều khiển RISC-V riêng biệt và trình giải quy hoạch ràng buộc chuyên biệt. Kết cấu này không phản ánh toàn bộ các NPU thương mại khác trên thị trường. Các nền tảng thương mại như Rockchip RK3588 sở hữu cấu trúc phần cứng và chuỗi công cụ RKNN độc quyền, không công bố chi tiết thuật toán bên trong. Các kết luận từ eIQ Neutron chỉ dùng để hiểu nguyên lý co-design, không được tự ý gán thông số hay thuật toán sang SoC khác khi chưa có tài liệu kiểm chứng.

4. Cái gì cố định, cái gì chọn được ở compiler
==============================================

Khi triển khai mô hình học sâu lên phần cứng chuyên dụng, ranh giới giữa yếu tố phần cứng cố định và quyền quyết định của compiler/người dùng được phân định rõ:

.. list-table::
   :header-rows: 1
   :widths: 22 24 54

   * - Thành phần
     - Tính chất
     - Trách nhiệm và khả năng tác động
   * - Dung lượng SRAM on-chip
     - Cố định phần cứng
     - Kích thước bộ đệm nội bộ là bất biến vật lý (ví dụ: 1 MiB hoặc 2 MiB trong eIQ Neutron [T2 BAMB tr.8]).
   * - Băng thông và độ trễ DRAM
     - Cố định phần cứng
     - Băng thông vật lý của bus bộ nhớ và chuẩn DRAM trên bo mạch.
   * - Mảng tính toán và ISA
     - Cố định phần cứng
     - Số lượng PE, kiểu dữ liệu hỗ trợ (INT8, FP16) và tập lệnh phần cứng.
   * - Chiến lược Operator Fusion
     - Compiler quyết định
     - Quyết định gộp những toán tử nào để triệt tiêu việc ghi tensor trung gian ra bộ nhớ ngoài [T2 TVM tr.3].
   * - Kích thước Tile và lập lịch
     - Compiler quyết định
     - Chọn kích thước lát cắt không gian và thứ tự vòng lặp sao cho vừa khít với SRAM [T2 BAMB tr.4].
   * - Phân bổ bộ nhớ tĩnh
     - Compiler quyết định
     - Tính toán vòng đời của từng tensor để tái sử dụng vùng nhớ đệm on-chip [T2 TVM tr.3] [T2 BAMB tr.4].
   * - Kiến trúc mạng và Lượng tử hóa
     - Người dùng quyết định
     - Lựa chọn cấu trúc mô hình thân thiện với phần cứng, chọn kiểu số (INT8/FP16) và các cờ cấu hình khi export.

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 15 10 65 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``TVM``
     - T2
     - :download:`tvm_compiler_2018chen.pdf <../../../_assets/pdf/papers/03_compiler/tvm_compiler_2018chen.pdf>`
     - 11
   * - ``BAMB``
     - T2
     - :download:`npu_compiler_codesign_2025bamberg.pdf <../../../_assets/pdf/papers/03_compiler/npu_compiler_codesign_2025bamberg.pdf>`
     - 10
