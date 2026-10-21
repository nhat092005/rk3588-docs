:tocdepth: 1

*******************************
Vì sao cần NPU, MAC và PE array
*******************************

.. admonition:: Trang này trả lời

   - Suy luận CNN tốn bao nhiêu phép tính và vì sao CPU hay GPU không phải lựa chọn tự nhiên?
   - MAC và PE là gì, một mảng PE được ghép ra sao?
   - Một lớp conv cần bao nhiêu chu kỳ trên mảng NxN và vì sao mảng lớn chưa chắc nhanh hơn?
   - NPU đánh đổi điều gì để đạt hiệu suất cao?

.. admonition:: Tóm tắt

   - Convolution chiếm trên 90% số phép tính của CNN và quyết định thời gian chạy [T2 Chen 2016 tr.1]. Tính lại trên các lớp AlexNet trong Table II của paper ra 91.9% (suy ra, mục 1.1).
   - Mỗi phần tử ofmap cần :math:`C \cdot R^2` MAC. Lớp CONV3 của AlexNet cần 149,520,384 MAC cho một ảnh (suy ra từ [T2 Chen 2016 tr.3] và Table II ở [T2 Chen 2016 tr.4]).
   - Di chuyển dữ liệu có thể đắt hơn tính toán, và lấy dữ liệu từ DRAM ngoài chip tốn năng lượng hơn nhiều bậc so với bộ nhớ trên chip [T2 Chen 2016 tr.1].
   - Nhân 8 bit có thể tốn ít năng lượng và diện tích hơn 6 lần so với nhân dấu phẩy động 16 bit IEEE 754 [T2 Jouppi 2017 tr.1].
   - Một PE của Eyeriss gồm ALU (làm MAC và cộng), register file (RF) và FIFO [T2 Chen 2016 tr.2]. TPU nói theo MAC và không dùng chữ PE [T2 Jouppi 2017 tr.3].
   - Mảng lớn không tự đảm bảo nhanh. Ở TPU, lớp có ít kênh làm nhiều MAC trong mảng không chứa trọng số hữu ích [T2 Jouppi 2017 tr.6]. Mục 2.3 tính con số cụ thể.
   - NPU nhanh vì cứng: TPU chỉ hỗ trợ ma trận dày, bỏ sparsity [T2 Jouppi 2017 tr.3]. Mọi số liệu 15X đến 30X của TPU là so với K80 và Haswell ở datacenter, không áp dụng cho NPU biên [T2 Jouppi 2017 tr.1].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _npu-vi-sao-can:

1. Vì sao không dùng CPU hay GPU
================================

Câu hỏi này có ba lập luận, mỗi nguồn nêu một lập luận. Trang ghép ba lập luận lại: khối lượng tính rất lớn nhưng đều đặn (mục 1.1), chi phí nằm ở việc di chuyển dữ liệu chứ không phải phép nhân (mục 1.2), và phần cứng chuyên dụng đổi tính linh hoạt lấy hiệu suất (mục 1.3).

1.1 Khối lượng tính của suy luận CNN: đếm MAC
---------------------------------------------

MAC (multiply-and-accumulate) là một phép nhân rồi cộng vào tổng. Cách đếm MAC cho tích chập, kèm ví dụ nhỏ, nằm ở :doc:`../01-nen-tang-ai/03-convolution-va-cnn` (mục 4). Ở đây chỉ lấy lại kết quả để đếm cho một mạng thật.

Chen 2016 định nghĩa một lớp CONV bằng phương trình (1) với các tham số hình dạng ở Table I: N là batch, M là số filter (bằng số kênh ofmap), C là số kênh ifmap, H là kích thước ifmap, R là kích thước filter, E là kích thước ofmap [T2 Chen 2016 tr.3]. Mỗi phần tử ofmap là tổng của :math:`C \cdot R^2` tích. Một lớp có :math:`M \cdot E^2` phần tử ofmap cho mỗi ảnh nên (suy ra từ phương trình (1)):

.. math::

   \text{MAC}_{\text{CONV/FC}} = N \cdot M \cdot E^2 \cdot C \cdot R^2

Lớp FC dùng cùng công thức với :math:`E = 1` và :math:`H = R` [T2 Chen 2016 tr.3]. Bảng sau áp dụng công thức lên 8 lớp của AlexNet, cột hình dạng lấy từ Table II [T2 Chen 2016 tr.4], còn cột MAC và số trọng số do trang tính bằng script (N = 1).

.. csv-table::
   :header-rows: 1
   :widths: 10 6 6 8 8 18 16 14

   Lớp,R,E,C,M,MAC mỗi ảnh,Số trọng số,MAC mỗi trọng số
   CONV1,11,55,3,96,"105,415,200","34,848",3025
   CONV2,5,27,48,256,"223,948,800","307,200",729
   CONV3,3,13,256,384,"149,520,384","884,736",169
   CONV4,3,13,192,384,"112,140,288","663,552",169
   CONV5,3,13,192,256,"74,760,192","442,368",169
   FC1,6,1,256,4096,"37,748,736","37,748,736",1
   FC2,1,1,4096,4096,"16,777,216","16,777,216",1
   FC3,1,1,4096,1000,"4,096,000","4,096,000",1

Tổng 724,406,816 MAC mỗi ảnh, trong đó 5 lớp CONV chiếm 665,784,864 (91.9%). Con số này khớp với câu của paper:

   "Convolutions account for over 90% of the CNN operations and dominates runtime" [T2 Chen 2016 tr.1]

Hai điều rút ra từ bảng. Thứ nhất, hầu hết khối lượng tính là phép MAC đều đặn, cùng một công thức lặp lại, rất hợp với phần cứng song song. Thứ hai, cột cuối (MAC mỗi trọng số) rất khác nhau giữa CONV và FC. Lớp FC dùng mỗi trọng số đúng một lần cho một ảnh, vì lớp FC "does not have the weight sharing property" như CONV [T2 Chen 2016 tr.3]. Cột này là đầu vào của roofline ở :doc:`02-dataflow-va-phan-cap-bo-nho`.

Giới hạn: AlexNet chỉ là ví dụ của paper. Số MAC của YOLO nằm ở khối 07 (:doc:`../07-yolo/01-kien-truc-va-khoi-cau-thanh-yolo`).

1.2 CPU, GPU, NPU khác nhau ở đâu
---------------------------------

Chen 2016 nêu vấn đề của song song kiểu SIMD/SIMT: phép tính song song được, nhưng băng thông đi kèm làm throughput không tăng tương ứng.

   "Although these operations can leverage highly-parallel compute paradigms, such as SIMD/SIMT, throughput may not scale accordingly due to the accompanying bandwidth requirement" [T2 Chen 2016 tr.1]

Cùng đoạn đó nói thêm rằng năng lượng vẫn cao vì di chuyển dữ liệu có thể đắt hơn tính toán, và lấy dữ liệu từ DRAM ngoài chip tốn năng lượng hơn nhiều bậc so với bộ nhớ trên chip [T2 Chen 2016 tr.1]. Con số cụ thể ở :doc:`02-dataflow-va-phan-cap-bo-nho`.

Bảng sau so sánh theo các điểm mà nguồn nêu. Cột CPU và GPU là lời của các paper, không phải đo trên thiết bị của repo.

.. list-table::
   :header-rows: 1
   :widths: 16 30 30 24

   * - Tiêu chí
     - CPU, GPU (theo nguồn)
     - NPU dạng mảng PE hoặc ASIC (theo nguồn)
     - Nguồn
   * - Kiểu song song
     - SIMD/SIMT, băng thông đi kèm hạn chế throughput
     - Mảng PE đơn giản nối trực tiếp với nhau: "an array of relatively simple processing engines (PEs)"
     - [T2 Chen 2016 tr.1] [T2 Chen 2016 tr.2]
   * - Điều khiển
     - Control lớn hơn nhiều và khó thiết kế hơn
     - Control chỉ chiếm 2% diện tích die TPU
     - [T2 Jouppi 2017 tr.3]
   * - Thực thi
     - Cache, out-of-order, multithreading, prefetching giúp throughput trung bình hơn là độ trễ đảm bảo
     - Mô hình thực thi tất định, phù hợp yêu cầu độ trễ phân vị 99
     - [T2 Jouppi 2017 tr.1]
   * - Bộ nhớ
     - Có cache và các tối ưu thay đổi theo thời gian (out-of-order, multithreading)
     - Bộ nhớ trên chip do phần mềm quản lý (TPU: 28 MiB)
     - [T2 Jouppi 2017 tr.1]
   * - Số MAC (TPU so với K80)
     - K80 là mốc so sánh
     - TPU có số MAC gấp 25 lần và bộ nhớ trên chip gấp 3.5 lần K80
     - [T2 Jouppi 2017 tr.2]

Về động lực, Jouppi 2017 mở đầu bằng nhận định rằng cải thiện lớn về chi phí, năng lượng, hiệu năng cần đến từ phần cứng chuyên biệt theo miền bài toán (domain-specific):

   "Many architects believe that major improvements in cost-energy-performance must now come from domain-specific hardware." [T2 Jouppi 2017 tr.1]

Lý do kiểu số nhỏ có lợi nằm ở câu sau (xem thêm :doc:`../03-luong-tu-hoa/01-luong-tu-hoa-affine-va-granularity`):

   "Eight-bit integer multiplies can be 6X less energy and 6X less area than IEEE 754 16-bit floating-point multiplies" [T2 Jouppi 2017 tr.1]

Với thiết bị di động, Jung 2023 nêu thêm ràng buộc diện tích. NPU di động có bộ nhớ cục bộ nhỏ, chỉ đủ cho tensor vào, ra và trọng số của một lớp:

   "Mobile NPUs typically have a small amount of local memory (or scratch pad memory, SPM) that provides space only enough for input/output tensors and weights of one layer operation in deep neural networks (DNNs)." [T2 Jung 2023 tr.1]

Giới hạn: TPU là ASIC "deployed in datacenters since 2015" [T2 Jouppi 2017 tr.1]. Các tỷ lệ "about 15X - 30X faster" so với GPU và CPU cùng thời [T2 Jouppi 2017 tr.1] và tỷ lệ MAC ở bảng trên là của máy datacenter, không dùng cho NPU biên.

1.3 Đánh đổi của NPU: nhanh nhưng cứng, chỉ chạy được một tập op
----------------------------------------------------------------

Phần cứng càng chuyên biệt thì càng bị ràng buộc. Ba ràng buộc có nguồn:

- **Chỉ ma trận dày.** Matrix unit của TPU "is designed for dense matrices", phần hỗ trợ sparse bị bỏ vì thời gian triển khai [T2 Jouppi 2017 tr.3].
- **Tập lệnh và op hữu hạn.** TPU có khoảng một chục lệnh, trong đó 5 lệnh chính [T2 Jouppi 2017 tr.3]. Lệnh Activate chỉ cung cấp các lựa chọn như ReLU, Sigmoid và pooling bằng phần cứng riêng [T2 Jouppi 2017 tr.4]. Tập op mà NPU RK3588 hỗ trợ xem :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/04-operator-list`.
- **Phải hợp với hình dạng lớp.** Mỗi lớp CNN có hình dạng khác nhau (Table II ở trên), nên phần cứng không thể chỉ xử lý một số hình dạng cố định:

   "the dataflow must be efficient for different shapes, and the hardware architecture must be programmable to dynamically map to an efficient dataflow." [T2 Chen 2016 tr.4]

Hệ quả nhìn thấy trong số liệu của TPU: CNN1 có operational intensity rất cao nhưng chỉ đạt 14.1 TOPS, còn CNN0 đạt 86 TOPS, vì ở CNN1 "only about half of the 65,536 MACs hold useful weights because some layers in CNN1 have shallow feature depths" [T2 Jouppi 2017 tr.6]. Mục 2.3 dựng lại hiện tượng này bằng số.

2. MAC và PE array
==================

2.1 Một PE làm gì trong một chu kỳ
----------------------------------

Chen 2016 mô tả PE trong bộ tăng tốc dạng spatial architecture như sau:

   "The PE includes an ALU datapath, which is capable of doing multiply-and-accumulate (MAC) and addition, a register file (RF) as a local scratchpad, and a PE FIFO (pFIFO) used to control the traffic going in and out of the ALU." [T2 Chen 2016 tr.2]

Vậy một PE có ba phần: ALU làm MAC, RF là bộ nhớ cục bộ nhỏ, FIFO điều phối dữ liệu vào ra. RF thường dưới 1 kB mỗi PE [T2 Chen 2016 tr.2]. Paper không nêu rõ một PE làm đúng một MAC mỗi chu kỳ. Chen 2016 chỉ giả định throughput tỷ lệ với số PE đang hoạt động [T2 Chen 2016 tr.7]. Trang này dùng giả định (của trang, suy ra) rằng **một PE hoàn thành một MAC mỗi chu kỳ khi có đủ dữ liệu**, để đếm chu kỳ ở mục 2.3.

2.2 Mảng PE và cách ghép nhiều PE
---------------------------------

Spatial architecture (SA) là lớp bộ tăng tốc dùng nhiều PE đơn giản nối trực tiếp với nhau:

   "Spatial architectures (SAs) are a class of accelerators that can exploit high compute parallelism using direct communication between an array of relatively simple processing engines (PEs)." [T2 Chen 2016 tr.2]

Một bộ tăng tốc CNN gồm mảng PE, global buffer trên chip và DRAM ngoài chip. Các tầng giao tiếp qua FIFO vào và ra. Global buffer cho CNN thường khoảng 100 đến 300 kB và các PE nối với nhau qua một mạng trên chip (NoC) tùy dataflow [T2 Chen 2016 tr.2].

.. _fig-npu-spatial-arch:

.. figure:: ../../../_assets/img/npu/01_npu_fundamentals/eyeriss_fig1.png
   :align: center
   :alt: Sơ đồ khối bộ tăng tốc CNN dạng spatial architecture và phóng to một PE

   Bộ tăng tốc CNN gồm mảng PE, global buffer và DRAM ngoài chip, phóng to một PE (RF, pFIFO). Nguồn: [T2 Chen 2016 tr.2, Figure 1]

TPU ghép theo cách khác: một khối nhân ma trận 256x256 MAC nhân cộng số nguyên 8 bit [T2 Jouppi 2017 tr.3].

   "It contains 256x256 MACs that can perform 8-bit multiply-and-adds on signed or unsigned integers." [T2 Jouppi 2017 tr.3]

.. _fig-npu-tpu-block:

.. figure:: ../../../_assets/img/npu/01_npu_fundamentals/tpu_fig1.png
   :align: center
   :alt: Sơ đồ khối của TPU với Matrix Multiply Unit

   Sơ đồ khối TPU: Matrix Multiply Unit lấy đầu vào từ Weight FIFO và Unified Buffer, đầu ra vào Accumulators. Nguồn: [T2 Jouppi 2017 tr.3, Figure 1]

Hai thiết kế này cho thấy PE không nhất thiết là một MAC trơn. Bảng sau đặt hai chip cạnh nhau, số trong cột thứ ba và thứ tư lấy từ paper, hai dòng cuối là phép suy ra của trang (giả định 1 MAC mỗi PE mỗi chu kỳ).

.. list-table::
   :header-rows: 1
   :widths: 28 24 24 24

   * - Thông số
     - Eyeriss (chip chế tạo)
     - TPU
     - Nguồn
   * - Công nghệ
     - 65nm CMOS
     - 28 nm
     - [T2 Chen 2016 tr.5] [T2 Jouppi 2017 tr.5]
   * - Số PE hoặc MAC
     - 168 PE
     - 65,536 MAC (256x256)
     - [T2 Chen 2016 tr.5] [T2 Jouppi 2017 tr.3]
   * - Xung nhịp
     - 200 MHz
     - 700 MHz
     - [T2 Chen 2016 tr.5] [T2 Jouppi 2017 tr.5]
   * - Độ chính xác
     - 16-bit fixed-point
     - 8 bit số nguyên
     - [T2 Chen 2016 tr.5] [T2 Jouppi 2017 tr.3]
   * - Bộ nhớ cục bộ và đệm
     - RF 0.5 kB mỗi PE, buffer 108 kB
     - Unified Buffer 24 MiB, Accumulators 4 MiB
     - [T2 Chen 2016 tr.5] [T2 Jouppi 2017 tr.3]
   * - Tốc độ MAC đỉnh (suy ra)
     - 168 x 200 MHz = 33.6 GMAC/s
     - 65,536 x 700 MHz = 45.9 TMAC/s
     - tính bằng script
   * - Công bố của paper
     - không có trong các trang đã đọc
     - 92 TOPS. Suy ra: bằng 2 x 45.9 TMAC/s, tức mỗi MAC tính là hai phép
     - [T2 Jouppi 2017 tr.1] [T2 Jouppi 2017 tr.5]

Lưu ý: nếu so con số "92 TOPS" với số MAC thì phải nhân đôi (suy ra: 65,536 x 700 MHz x 2 = 91.75 TOPS khớp 92 của paper). Hai chip khác hẳn nhau về quy mô và nằm ở hai công nghệ khác nhau, nên các số này không đại diện cho RK3588. Số MAC, xung nhịp và bộ nhớ của NPU RK3588 xem :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/02-vi-kien-truc-va-khoi-tinh-toan-core`.

2.3 Ví dụ số: một lớp conv cần bao nhiêu chu kỳ trên mảng NxN
-------------------------------------------------------------

Để thấy kích thước mảng ảnh hưởng thế nào, trang dựng một mô hình đếm chu kỳ cho mảng :math:`N \times N` MAC. Mô hình dựa trên cách TPU ánh xạ một lớp conv, như Jouppi 2017 mô tả bằng thuật ngữ của Eyeriss:

   "a TPU convolutional layer maps C and M to the rows and columns of the matrix unit, taking HWN cycles to perform one pass." [T2 Jouppi 2017 tr.14]

Cùng đoạn đó nói với C và M lớn thì cần RS lượt (pass) để xử lý lớp [T2 Jouppi 2017 tr.14]. Từ đó trang suy ra mô hình sau (không phải công thức do paper nêu, và chưa tính thời gian nạp tile trọng số vì TPU che nó bằng double buffering [T2 Jouppi 2017 tr.3]):

.. math::

   \text{chu kỳ} \approx R^2 \cdot \lceil C / N \rceil \cdot \lceil M / N \rceil \cdot E^2 \qquad
   \text{hiệu suất} = \frac{\text{MAC}}{N^2 \cdot \text{chu kỳ}}

Giải thích: kênh vào C trải trên các hàng, kênh ra M trải trên các cột. Mỗi trong :math:`R^2` vị trí của filter là một lượt, mỗi lượt đẩy :math:`E^2` vị trí ofmap qua mảng, mỗi chu kỳ một vị trí (batch N = 1). Bảng dưới tính cho ba lớp đầu của AlexNet và ba cỡ mảng bằng script. Cột "lý tưởng" là :math:`\text{MAC} / N^2`, tức mọi MAC đều bận.

.. csv-table::
   :header-rows: 1
   :widths: 24 12 22 24 18

   Lớp,Cỡ mảng N,Chu kỳ lý tưởng,Chu kỳ theo mô hình,Hiệu suất
   "CONV1 (C=3, M=96)",16,"411,779","2,196,150",18.8%
   CONV1,32,"102,945","1,098,075",9.4%
   CONV1,256,"1,609","366,025",0.4%
   "CONV2 (C=48, M=256)",16,"874,800","874,800",100%
   CONV2,32,"218,700","291,600",75.0%
   CONV2,256,"3,418","18,225",18.8%
   "CONV3 (C=256, M=384)",16,"584,064","584,064",100%
   CONV3,32,"146,016","146,016",100%
   CONV3,256,"2,282","3,042",75.0%

Ba nhận xét (đều suy ra từ bảng):

- Với CONV1, :math:`C = 3` nên chỉ 3 trong N hàng có việc. Mảng càng lớn thì càng lãng phí: tăng N từ 16 lên 256 giảm chu kỳ lý tưởng 256 lần nhưng chu kỳ theo mô hình chỉ giảm khoảng 6 lần.
- Từ CONV3 trở đi, C và M đủ lớn để chia đều. Hiệu suất hạ xuống 75% ở N = 256 vì :math:`\lceil 384 / 256 \rceil = 2` lượt cột nhưng lượt thứ hai chỉ dùng 128 trong 256 cột.
- Đây cũng là lý do trong paper TPU: lớp có ít kênh sâu làm "only about half of the 65,536 MACs hold useful weights" [T2 Jouppi 2017 tr.6]. Với kênh vào ít, các kỹ thuật như đóng gói nhiều vị trí lại là chủ đề riêng, paper chỉ nói chung rằng "a number of techniques reduce passes and improve utilization" [T2 Jouppi 2017 tr.14].

Giới hạn: đây là mô hình minh họa dựa trên cách ánh xạ mà paper TPU nêu cho TPU. Cách NPU RK3588 ánh xạ lớp conv lên mảng MAC là chủ đề của trang phần cứng RK3588, không suy ra từ đây.

3. Thuật ngữ nền cần có trước khi sang dataflow
===============================================

3.1 Bảng thuật ngữ MAC, PE, psum, reuse
---------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 52 28

   * - Thuật ngữ
     - Nghĩa theo nguồn
     - Nguồn
   * - MAC
     - Phép nhân cộng. ALU của PE làm được MAC và phép cộng
     - [T2 Chen 2016 tr.2]
   * - PE
     - Processing engine: ALU, RF và FIFO
     - [T2 Chen 2016 tr.2]
   * - RF
     - Register file, bộ nhớ cục bộ trong PE (thường dưới 1 kB)
     - [T2 Chen 2016 tr.2]
   * - Spatial architecture
     - Lớp bộ tăng tốc dùng mảng PE đơn giản nối trực tiếp với nhau
     - [T2 Chen 2016 tr.2]
   * - ifmap, ofmap, filter
     - Feature map đầu vào, đầu ra và bộ trọng số của lớp CONV
     - [T2 Chen 2016 tr.3]
   * - psum (partial sum)
     - Dữ liệu trung gian do các MAC song song sinh ra, gây áp lực lưu trữ nếu không được cộng dồn ngay
     - [T2 Chen 2016 tr.3]
   * - Convolutional reuse, filter reuse, ifmap reuse
     - Ba kiểu dùng lại dữ liệu đầu vào, định nghĩa ở :doc:`02-dataflow-va-phan-cap-bo-nho`
     - [T2 Chen 2016 tr.3] [T2 Chen 2016 tr.4]
   * - Tile, tiling
     - Chia tính toán một lớp thành các phép nhỏ trên các tile dữ liệu vì dữ liệu cả lớp quá lớn để đưa vào NPU một lần
     - [T2 Min 2023 tr.2]

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 26 52 22

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - NPU nhanh hơn GPU 15 đến 30 lần
     - Đó là kết quả của TPU so với K80 và Haswell trong datacenter, trên 6 ứng dụng NN của Google. Không phải số cho NPU biên hay RK3588
     - [T2 Jouppi 2017 tr.1]
   * - Một PE là một MAC
     - PE của Eyeriss gồm ALU, RF và FIFO. TPU không dùng chữ PE mà nói theo MAC
     - [T2 Chen 2016 tr.2] [T2 Jouppi 2017 tr.3]
   * - Chi phí chính của CNN là phép nhân
     - Paper nhấn mạnh di chuyển dữ liệu có thể đắt hơn tính toán
     - [T2 Chen 2016 tr.1]
   * - Mảng MAC càng lớn càng nhanh
     - Tốc độ phụ thuộc cả hình dạng lớp. Ở TPU, CNN1 chỉ đạt 14.1 TOPS dù mạng có operational intensity cao. Mục 2.3 cho thấy lớp 3 kênh chỉ dùng một phần nhỏ mảng 256x256 (suy ra)
     - [T2 Jouppi 2017 tr.6]
   * - NPU chạy được mọi mạng
     - TPU chỉ có khoảng một chục lệnh và không hỗ trợ sparse. Phần cứng phải hợp hình dạng từng lớp
     - [T2 Jouppi 2017 tr.3] [T2 Chen 2016 tr.4]

Nguồn
=====

Số trang là số trang PDF, trùng số in của bài báo gốc. Các con số MAC, chu kỳ và tốc độ đỉnh trong trang do script tính từ số liệu của paper (xem từng mục).

.. list-table::
   :header-rows: 1
   :widths: 14 8 62 16

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``Chen 2016``
     - T2
     - :download:`eyeriss_dataflow_2016chen.pdf <../../../_assets/pdf/papers/01_hardware/eyeriss_dataflow_2016chen.pdf>`
     - 37
   * - ``Jouppi 2017``
     - T2
     - :download:`tpu_datacenter_2017jouppi.pdf <../../../_assets/pdf/papers/01_hardware/tpu_datacenter_2017jouppi.pdf>`
     - 36
   * - ``Jung 2023``
     - T2
     - :download:`mobile_multicore_npu_2023jung.pdf <../../../_assets/pdf/papers/01_hardware/mobile_multicore_npu_2023jung.pdf>`
     - 1
   * - ``Min 2023``
     - T2
     - :download:`flexer_multi_npu_2023min.pdf <../../../_assets/pdf/papers/01_hardware/flexer_multi_npu_2023min.pdf>`
     - 1
