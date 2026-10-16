# Phần 1: NPU cơ bản

## Câu hỏi mở đầu
Một NPU tính convolution bằng những đơn vị nào, vì sao cách giữ và di chuyển dữ liệu quan trọng hơn số phép nhân, và điều nào trong số đó đã biết cho RK3588?

## Hình 1.1 (h1-1-mac-pe) [T2 chung]
MAC, PE và ô MAC của TPU là ba khái niệm khác nhau: MAC là phép nhân rồi cộng dồn, PE của EYE là ALU cộng RF và pFIFO, còn Matrix Multiply Unit của TPU đếm theo 256x256 MAC. Trong Eyeriss, một PE array nằm giữa global buffer và DRAM, tạo bốn cấp lưu trữ DRAM, global buffer, array (liên PE) và RF; chip Eyeriss có 168 PE, 65nm. Vì PE còn chứa RF và pFIFO, không được viết một PE luôn bằng một MAC. Mọi số PE, MAC, 65 nm là của paper, không phải của RK3588.
Đọc thêm: 01_ mục 1.2.
Khái niệm: Hình 2.2, Hình 2.3

## Hình 1.2 (h1-2-dataflow) [T2 chung]
Mỗi dataflow chọn một thứ để giữ yên trong PE (weight, tích lũy ofmap, một cặp hàng, hoặc không giữ gì) nhằm giảm số lần đọc lại thứ đó từ cấp bộ nhớ đắt hơn. Weight stationary giữ weight trong RF, output stationary giữ psum của một pixel ofmap, row stationary giữ cặp hàng filter và ifmap của một primitive, no local reuse không dùng RF. EYE nói không dataflow nào tối đa hóa mọi thứ cùng lúc, nên đề xuất row stationary; LP lại chọn output stationary. Hình gốc Fig. 5 cho thấy một 1D convolution primitive: weight 1 2 3 trượt qua hàng ifmap, mỗi ba phép cho một psum.
Đọc thêm: 01_ mục 1.3.
Khái niệm: Hình 1.5, Hình 2.2
Hình gốc: ../../npu_study/images/01_npu_fundamentals/eyeriss_fig5.png (EYE tr.6, Fig. 5; nhúng vì hình gốc cho thấy cách weight và ifmap trượt vào một psum, khó vẽ lại đúng; đã cắt phần chữ thừa bên phải)

## Hình 1.3 (h1-3-chi-phi-bo-nho) [T2 chung]
Trong chip 65 nm của EYE, một lần truy cập DRAM tốn 200 lần năng lượng của một phép MAC, global buffer 6 lần, truyền giữa các PE 2 lần, RF 1 lần. Số này chỉ đúng với điều kiện in kèm Table IV: quy trình thương mại 65 nm, global buffer trên 100 kB, array 1 đến 2 mm, RF 0.5 kB. Panel B là phép tính của bộ hình theo Eq. (3): một giá trị được dùng lại 24 lần, chia 1, 2, 6, 24 lượt đọc ở DRAM, global buffer, array, RF, tốn tổng 248 đơn vị MAC, trong đó DRAM chiếm 200. Số năng lượng theo cấp bộ nhớ của RK3588 là unknown.
Đọc thêm: 01_ mục 1.4. Khái niệm: Hình 2.1, Hình 7.1

## Hình 1.4 (h1-4-roofline) [T2 chung]
Roofline chia hiệu năng thành vùng bị giới hạn bởi băng thông bộ nhớ (phần nghiêng) và vùng bị giới hạn bởi đỉnh tính toán (phần phẳng); ridge point là chỗ hai phần gặp nhau. Panel A là hình khái niệm với trục không có số, dữ liệu minh họa không phải số đo. TPU định nghĩa lại trục X thành integer operations per byte of weights read; kết quả MLP và LSTM bị giới hạn bộ nhớ, CNN bị giới hạn tính toán chỉ đúng cho 6 ứng dụng của TPU, và CNN1 dù cường độ cao chỉ đạt 14.1 TOPS. Ridge point của RK3588 là unknown.
Đọc thêm: 01_ mục 1.5.
Khái niệm: Hình 2.3

## Hình 1.5 (h1-5-systolic-da-loi) [T2 chung]
Systolic là cách dữ liệu chảy qua mảng, còn stationary là thứ PE giữ lại; hai khái niệm khác nhau và dùng chung được. Ở TPU, dữ liệu vào từ trái, weight nạp từ trên, partial sum chảy xuống accumulator như một wavefront chéo. Với nhiều core, JUNG chia một lớp theo không gian (input và output chia, kernel nhân bản) hoặc theo kênh (kernel và output chia, input nhân bản), rồi tiling trong từng core và chọn thứ tự lập lịch; FLEX và LP là hai cách lập lịch khác, trên mô hình bộ nhớ khác. RK3588 chia một lớp cho nhiều core thế nào là unknown.
Đọc thêm: 01_ mục 1.6, 1.8. Số đo: Hình 10.3
Khái niệm: Hình 2.4

## Hiểu sai thường gặp
- "Một PE luôn bằng một MAC" -> PE của EYE gồm ALU (MAC và cộng), RF và pFIFO; TPU đếm theo MAC và không dùng chữ PE [EYE tr.2; TPU tr.3] (Hình 1.1)
- "168 PE của Eyeriss hay 65,536 MAC của TPU là cỡ MAC array của RK3588" -> đó là số của paper; TRM1 ghi INT8 là "Int8 mac array 32x32 mode" [TRM1 tr.2001] (Hình 1.1)
- "Tỷ lệ 200x và 6x của EYE áp dụng cho RK3588" -> chúng chỉ đúng cho quy trình thương mại 65 nm với global buffer trên 100 kB; tỷ lệ cho RK3588 là unknown [EYE tr.8] (Hình 1.3)
- "TPU nhanh hơn 15X đến 30X nên NPU nào cũng hơn CPU và GPU cỡ đó" -> số này chỉ so với K80 và Haswell của năm 2015 trong datacenter [TPU tr.2, tr.5] (Hình 1.4)
- "MLP và LSTM luôn bị giới hạn bộ nhớ, CNN luôn bị giới hạn tính toán" -> chỉ đúng cho 6 ứng dụng của TPU; CNN1 có cường độ cao nhưng chỉ đạt 14.1 TOPS [TPU tr.2, tr.6] (Hình 1.4)
- "Roofline của TPU đo bằng FLOP trên byte DRAM" -> HPC dùng floating-point operations per DRAM byte; TPU dùng integer operations per byte of weights read [TPU tr.5, tr.6] (Hình 1.4)
- "TPU hỗ trợ sparsity nên zero-skipping là chuyện bình thường của NPU" -> TPU bỏ qua sparsity ("Sparse architectural support was omitted"); zero-skipping của RK3588 là khái niệm riêng của TRM, xem Hình 2.2 [TPU tr.3; TRM1 tr.2006] (Hình 1.1)
- "Systolic nghĩa là weight stationary" -> systolic là cách dữ liệu chảy; EYE mô hình WS như systolic array và LP dùng systolic array với output stationary, nên hai khái niệm độc lập [EYE tr.7; LP tr.2] (Hình 1.5)
- "Row stationary là dataflow mọi NPU dùng" -> EYE đề xuất RS cho Eyeriss; LP chọn output stationary vì "commonly used"; RK3588 dùng dataflow nào là unknown [EYE tr.5; LP tr.2] (Hình 1.2)
- "RK3588 chia lớp cho ba core theo không gian hay theo kênh như JUNG" -> JUNG là Samsung với SoC ba core; TRM không nói cách chia, nên là unknown [JUNG tr.1; TRM1 tr.1984] (Hình 1.5)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao các dataflow cố giữ dữ liệu ở RF, và con số nào của EYE cho thấy điều đó?
Đáp án: Table IV cho DRAM 200x, global buffer 6x, array 2x, RF 1x so với một phép MAC (chip 65 nm), nên đọc từ DRAM đắt hơn đọc từ RF nhiều lần. EYE nêu mục tiêu là thực hiện phần lớn truy cập bằng đường có chi phí thấp hơn. Ví dụ Eq. (3) của bộ hình: giá trị dùng lại 24 lần chia a=1, b=2, c=3, d=4 tốn 1x200 + 2x6 + 6x2 + 24x1 = 248, trong đó một lượt đọc DRAM đã chiếm 200 [EYE tr.8] (Hình 1.3, Hình 1.2)
### Câu 2 (phân biệt)
Phân biệt "systolic" với "stationary". Cho một ví dụ trong đó hai khái niệm đi cùng nhau.
Đáp án: Systolic mô tả cách dữ liệu chảy qua mảng theo nhịp đều (TPU: data từ trái, weight từ trên, partial sum xuống accumulator); stationary mô tả thứ PE giữ lại (weight, tích lũy ofmap, cặp hàng). Hai khái niệm đi cùng nhau: EYE mô hình weight stationary với PE array hoạt động như systolic array, và LP dùng systolic array với output stationary [TPU tr.4; EYE tr.4, tr.7; LP tr.2] (Hình 1.5, Hình 1.2)
### Câu 3 (áp dụng)
Một lớp convolution có rất ít kênh chạy trên NPU nhiều core. Theo JUNG, chia theo kênh có rủi ro gì, và với RK3588 có kết luận được lớp đó chia thế nào không?
Đáp án: JUNG: hướng kênh đòi alignment lớn hơn hướng không gian, và nếu số kênh quá nhỏ để chia đều cho các core thì mức dùng core giảm. Với RK3588 thì không kết luận được: TRM không nói cách chia, UG152 chỉ liệt kê op nhanh hơn khi nhiều core (Conv, Add, Concat...) và các op khác về Core0; số đo thật ở Hình 10.3 [JUNG tr.9; UG152 tr.27] (Hình 1.5, Hình 2.4)
### Câu 4 (áp dụng)
Một bài viết nói "YOLO chạy trên RK3588 là compute-bound vì là CNN". Nhận định này có đủ căn cứ từ phần này không, và cần thêm gì để kiểm?
Đáp án: Không. Kết luận "CNN compute-bound" chỉ đúng cho 6 ứng dụng của TPU với trục integer operations per byte of weights read, và CNN1 của TPU lại chỉ đạt 14.1 TOPS. Với RK3588 cần đỉnh tính toán và băng thông DDR mà NPU nhận được; TRM1 cho 1024x3 MAC mỗi chu kỳ INT8 nhưng tần số tối đa ở Datasheet là TBD, nên ridge point là unknown [TPU tr.2, tr.6; TRM1 tr.1984; DS tr.31] (Hình 1.4, Hình 2.3)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 1.1 | MAC là multiply-and-accumulate; ALU trong PE làm MAC và cộng | T2 | EYE tr.2 | capable of doing multiply-and-accumulate (MAC) and addition |
| 1.1 | PE gồm ALU, RF là scratchpad cục bộ, pFIFO điều khiển lưu lượng vào ra ALU | T2 | EYE tr.2 | a register file (RF) as a local scratchpad, and a PE FIFO (pFIFO) used to control the traffic going in and out of the ALU |
| 1.1 | Hình 1 phóng to một PE | T2 | EYE tr.2 | The zoom-in shows the high-level structure of a PE. |
| 1.1 | PE là processing engine trong spatial architecture | T2 | EYE tr.2 | an array of relatively simple processing engines (PEs) |
| 1.1 | C·R² psum cộng lại thành một pixel ofmap | T2 | EYE tr.4 | CR2 psums are reduced into one ofmap pixel |
| 1.1 | Accelerator gồm global buffer và PE array | T2 | EYE tr.2 | primarily composed of a global buffer and an array of PEs |
| 1.1 | DRAM, global buffer, PE array nối qua iFIFO/oFIFO | T2 | EYE tr.2 | communicate with each other through the input and output FIFOs (iFIFO/oFIFO) |
| 1.1 | Các PE nối bằng NoC | T2 | EYE tr.2 | The PEs in the array are connected via a network on chip (NoC) |
| 1.1 | Global buffer thường 100 đến 300kB | T2 | EYE tr.2 | is around 100–300kB |
| 1.1 | RF thường dưới 1kB mỗi PE | T2 | EYE tr.2 | Typical RF size is below 1kB per PE |
| 1.1 | Bốn cấp lưu trữ | T2 | EYE tr.2 | four levels of storage hierarchy for data accesses, including DRAM, global buffer, array (inter-PE communication) and RF |
| 1.1 | Chip Eyeriss: 65nm CMOS | T2 | EYE tr.5 | 65nm CMOS |
| 1.1 | Chip Eyeriss: 168 PE, RF 0.5 kB mỗi PE, buffer 108 kB | T2 | EYE tr.5 | # of PEs 168 RF Size/PE 0.5 kB Buffer Size 108 kB |
| 1.1 | Chip Eyeriss: 200 MHz, 16-bit fixed-point | T2 | EYE tr.5 | Clock Rate 200 MHz Precision 16-bit Fixed-Point |
| 1.1 | Nhãn bảng chip | T2 | EYE tr.5 | Die photo and spec of the Eyeriss chip |
| 1.1 | TPU: 256x256 MAC, 8-bit | T2 | TPU tr.3 | It contains 256x256 MACs that can perform 8-bit multiply-and-adds on signed or unsigned integers. |
| 1.1 | TPU: 65,536 MAC | T2 | TPU tr.1 | 65,536 8-bit MAC matrix multiply unit |
| 1.1 | TPU: tích 16-bit gom vào 4 MiB accumulator 32-bit | T2 | TPU tr.3 | 16-bit products are collected in the 4 MiB of 32-bit |
| 1.1 | Matrix unit dành cho ma trận dày, bỏ sparsity | T2 | TPU tr.3 | Sparse architectural support was omitted for time-to-deploy reasons. |
| 1.1 | Bài TPU không dùng chữ PE (đã tìm toàn bài bằng pdftotext) | T2 | (không có) | (unknown) |
| 1.1 | Hình vẽ 4x4 ô MAC là thu gọn của 256x256 | tính | TPU tr.3 | (số học) |
| 1.1 | Một PE có thêm RF và pFIFO ngoài ALU nên MAC chỉ là một phần của PE (suy ra của bộ hình) | tính | EYE tr.2 | (số học) |
| 1.1 | RK3588: 1024x3 MAC INT8 mỗi chu kỳ | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| 1.1 | RK3588: Int8 mac array 32x32 | T1 | TRM1 tr.2001 | Int8 mac array 32x32 mode |
| 1.1 | 32 x 32 = 1024 (phép tính của bộ hình, khớp số) | tính | TRM1 tr.2001 | (số học) |
| 1.1 | TRM không nói ô 32x32 là một PE | T1 | (không có) | (unknown) |
| 1.1 | "PE" của RK3588 là gì | T1 | (không có) | (unknown) |
| 1.1 | Bố cục MAC array cho INT16, FP16, INT4 | T1 | (không có) | (unknown) |
| 1.2 | WS: weight nằm yên trong RF | T2 | EYE tr.4 | Each filter weight remains stationary in the RF to maximize convolutional reuse and filter reuse. |
| 1.2 | WS: PE chạy hết N·E² phép dùng weight đó | T2 | EYE tr.4 | NE 2 operations that use the same filter weight |
| 1.2 | WS: ifmap broadcast tới các PE, psum cộng dồn qua PE | T2 | EYE tr.4 | Each pixel in an ifmap plane from the same channel is broadcast |
| 1.2 | WS: psum cộng dồn qua các PE | T2 | EYE tr.4 | the psums generated by each PE are further accumulated spatially across these PEs |
| 1.2 | WS: psum không luôn cộng ngay, tạm lưu ở global buffer | T2 | EYE tr.4 | psums are not always immediately reducible, and will be temporarily stored to the global buffer |
| 1.2 | WS: Table III tối đa hóa convolutional reuse và filter reuse | T2 | EYE tr.5 | Maximize convolutional reuse and filter reuse of weights in the RF. |
| 1.2 | OS: tích lũy mỗi pixel ofmap nằm yên trong PE | T2 | EYE tr.4 | The accumulation of each ofmap pixel stays stationary in a PE. |
| 1.2 | OS: psum lưu trong cùng RF | T2 | EYE tr.4 | The psums are stored in the same RF for accumulation |
| 1.2 | OS: tái dùng đầu vào ở mức array, RF chỉ cộng dồn psum | T2 | EYE tr.5 | The RF level only handles psum accumulation. |
| 1.2 | OS: ba biến thể | T2 | EYE tr.4 | SOC-MOP, MOC-MOP, and MOC-SOP |
| 1.2 | OS: Fig. 3 so sánh ba biến thể | T2 | EYE tr.5 | Comparison of the three different OS dataflow variants |
| 1.2 | OS: Table III tối đa hóa psum accumulation trong RF | T2 | EYE tr.5 | Maximize psum accumulation in RF. |
| 1.2 | RS: primitive là một hàng weight, một hàng ifmap, ra một hàng psum | T2 | EYE tr.5 | each primitive operates on one row of filter weights and one row of ifmap pixels, and generates one row of psums |
| 1.2 | RS: cặp hàng nằm yên trong PE | T2 | EYE tr.5 | the computation of each row pair stays stationary in the PE |
| 1.2 | RS: hàng filter dùng lại theo chiều ngang | T2 | EYE tr.7 | rows of filter weight are reused across PEs horizontally |
| 1.2 | RS: hàng ifmap dùng lại theo đường chéo | T2 | EYE tr.7 | rows of ifmap pixel are reused across PEs diagonally |
| 1.2 | RS: hàng psum cộng dồn theo chiều dọc | T2 | EYE tr.7 | rows of psum are accumulated across PEs vertically |
| 1.2 | RS: RF dùng cho mọi loại tái dùng | T2 | EYE tr.6 | the RF is used to exploit all types of data movements |
| 1.2 | NLR: không tái dùng ở mức RF | T2 | EYE tr.5 | it does not exploit data reuse at the RF level |
| 1.2 | NLR: tái dùng ifmap và cộng dồn psum bằng giao tiếp giữa PE | T2 | EYE tr.5 | it uses inter-PE communication for ifmap reuse and psum accumulation |
| 1.2 | NLR: các PE cùng nhóm đọc cùng pixel ifmap, khác weight | T2 | EYE tr.5 | PEs within the same group read the same ifmap pixel but with different filter weights from the same input channel |
| 1.2 | NLR: không RF, chừa diện tích cho global buffer lưu psum và dữ liệu vào | T2 | EYE tr.5 | it leaves a large area for the global buffer, which is used to store psums as well as input data for reuse |
| 1.2 | Tái dùng đầu vào tối đa không đạt đồng thời với cộng dồn psum ngay | T2 | EYE tr.4 | maximum input data reuse cannot be achieved simultaneously with immediate psum reduction |
| 1.2 | Các dataflow cũ không tính đồng thời mọi loại | T2 | EYE tr.5 | they fail to take all of them into account at once |
| 1.2 | LP chọn output stationary | T2 | LP tr.2 | we adopt the commonly used output stationary as the dataflow for this paper |
| 1.2 | FLEX phân loại lịch thực thi input, output, weight-stationary | T2 | FLEX tr.1 | these techniques can be classified into input, output, and weight-stationary schedules |
| 1.2 | Fig. 5: nhãn và R = 3, H = 5 | T2 | EYE tr.6 | Processing of an 1D convolution primitive in the PE. In this example, R = 3 and H = 5. |
| 1.2 | Fig. 5: weight 1 2 3 trượt qua ifmap 1 2 3 4 5, 9 phép Op1 đến Op9, 3 psum | T2 | EYE tr.6 | (đọc từ hình) |
| 1.2 | Systolic là cách dữ liệu chảy, stationary là thứ PE giữ (suy ra của bộ hình) | tính | EYE tr.7 | (số học) |
| 1.2 | RK3588: Int8 mac array 32x32 | T1 | TRM1 tr.2001 | Int8 mac array 32x32 mode |
| 1.2 | RK3588: buffer 384KBx3 | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 1.2 | RK3588 dùng dataflow nào; không có từ khóa dataflow, stationary, systolic, tiling, processing element trong TRM1 tr.1984-2060, TRM2, DS, UG152, API232 | T1 | (không có) | (unknown) |
| 1.3 | Table IV: DRAM 200x, global buffer 6x, array 2x, RF 1x | T2 | EYE tr.8 | 200× 6× 2× 1× |
| 1.3 | Table IV điều kiện: global buffer >100kB, array 1-2mm, RF 0.5kB | T2 | EYE tr.8 | (>100kB) (1-2mm) (0.5kB) |
| 1.3 | Table IV chuẩn hóa so với một phép MAC, quy trình thương mại 65nm | T2 | EYE tr.8 | Table IV shows the energy cost of accessing each level relative to a MAC operation under the listed conditions. The numbers are extracted from a commercial 65nm process. |
| 1.3 | DRAM và global buffer gồm cả iFIFO/oFIFO; array gồm iFIFO/oFIFO/pFIFO và điện dung dây | T2 | EYE tr.8 | The DRAM and global buffer energy costs aggregate the energy of accessing the storage and the iFIFO/oFIFO; the array energy cost includes the energy of accessing the iFIFO/oFIFO/pFIFO on both sides of the path as well as the cost from wiring capacitance. |
| 1.3 | Mục tiêu dataflow: phần lớn truy cập qua đường chi phí thấp | T2 | EYE tr.8 | perform most data accesses using the data movement paths with lower energy cost |
| 1.3 | Định nghĩa reuse ở mỗi cấp | T2 | EYE tr.8 | Reuse at each level is defined as the number of times each data value is read from this level to its lower-cost levels during its lifetime. |
| 1.3 | Eq. (3) | T2 | EYE tr.8 | a × EC(DRAM) + ab × EC(global buffer)+ abc × EC(array) + abcd × EC(RF) |
| 1.3 | Ví dụ 24 lần dùng lại chia a=1, b=2, c=3, d=4 | T2 | EYE tr.8 | the total number of reuse, 24, is split into a = 1, b = 2, c = 3 and d = 4 |
| 1.3 | Số lượt đọc 1, 2, 6, 24 (a, ab, abc, abcd) | tính | EYE tr.8 | (số học) |
| 1.3 | Năng lượng 1x200 = 200, 2x6 = 12, 6x2 = 12, 24x1 = 24 | tính | EYE tr.8 | (số học) |
| 1.3 | Tổng 248; DRAM chiếm 200/248 = 81% | tính | EYE tr.8 | (số học) |
| 1.3 | RK3588: buffer 384KBx3 trong NPU | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 1.3 | RK3588: system SRAM NPU nhận tối đa 956KB | T1 | SRAM dòng 21 | 最大可分配956KB，且大小需要4K对齐 |
| 1.3 | RK3588: interconnect có bốn DDR scheduler | T1 | TRM2 tr.16 | Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency |
| 1.3 | Hệ số năng lượng theo cấp bộ nhớ của RK3588; nối cấp T1 với bốn cấp EYE | T1 | (không có) | (unknown) |
| 1.4 | TPU điều chỉnh roofline từ HPC | T2 | TPU tr.5 | we adapt the Roofline Performance model from high-performance computing (HPC) |
| 1.4 | Giả định: ứng dụng không nằm vừa cache | T2 | TPU tr.5 | applications don't fit in on-chip caches, so they are either computation-limited or memory bandwidth-limited |
| 1.4 | HPC: trục X là floating-point operations per DRAM byte | T2 | TPU tr.5 | measured as floating-point operations per DRAM byte accessed |
| 1.4 | Phần phẳng là peak computation rate | T2 | TPU tr.5 | the peak computation rate forms the "flat" part of the roofline |
| 1.4 | Phần nghiêng là băng thông; cường độ thấp thì memory-bound | T2 | TPU tr.5 | Without sufficient operational intensity, a program is memory bandwidth-bound and lives under the slanted part of the roofline. |
| 1.4 | TPU: thay FLOP bằng integer operation do lượng tử | T2 | TPU tr.6 | when NN applications are quantized, we first replace floating-point operations with integer operations |
| 1.4 | TPU: trục X là integer operations per byte of weights read | T2 | TPU tr.6 | redefine operational intensity to be integer operations per byte of |
| 1.4 | MLP, LSTM memory bound; CNN computation bound | T2 | TPU tr.6 | the MLPs and LSTMs are memory bound, and CNNs are computation bound |
| 1.4 | CNN1 14.1 TOPS, CNN0 86 TOPS | T2 | TPU tr.6 | CNN1, despite a very high operational intensity, is running at only 14.1 TOPS while CNN0 runs at 86 TOPS |
| 1.4 | Ridge point 1350 operations per byte of weight memory fetched | T2 | TPU tr.6 | Its ridge point is far to the right at 1350 operations per byte of weight memory fetched. |
| 1.4 | Table 1: tên cột Ops/Weight Byte | T2 | TPU tr.2 | TPU Ops / TPU Batch % of Deployed |
| 1.4 | Table 1: MLP0 200 | T2 | TPU tr.2 | MLP0 100 5 5 ReLU 20M 200 200 |
| 1.4 | Table 1: MLP1 168 | T2 | TPU tr.2 | MLP1 1000 4 4 ReLU 5M 168 168 |
| 1.4 | Table 1: LSTM0 64 | T2 | TPU tr.2 | LSTM0 1000 24 34 58 sigmoid, tanh 52M 64 64 |
| 1.4 | Table 1: LSTM1 96 | T2 | TPU tr.2 | LSTM1 1500 37 19 56 sigmoid, tanh 34M 96 96 |
| 1.4 | Table 1: CNN0 2888 | T2 | TPU tr.2 | CNN0 1000 16 16 ReLU 8M 2888 8 |
| 1.4 | Table 1: CNN1 1750 | T2 | TPU tr.2 | CNN1 1000 4 72 13 89 ReLU 100M 1750 32 |
| 1.4 | Bốn trong sáu ứng dụng bị giới hạn băng thông trên TPU | T2 | TPU tr.2 | Four of the six NN apps are memory-bandwidth limited on the TPU |
| 1.4 | 15X - 30X nhanh hơn K80 và Haswell | T2 | TPU tr.2 | The TPU is about 15X - 30X faster at inference than the K80 GPU and the Haswell CPU. |
| 1.4 | K80 và Haswell là nền tảng sẵn có năm 2015 | T2 | TPU tr.5 | server-class computers that were available in 2015 when the TPUs were deployed |
| 1.4 | Panel A: đường, ridge point, chương trình A và B là minh họa, trục không có số | tính | TPU tr.5 | (số học) |
| 1.4 | RK3588: 1024x3 MAC INT8 mỗi chu kỳ | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| 1.4 | RK3588: Datasheet ghi up to 6TOPs | T1 | DS tr.7 | computing power is up to 6TOPs |
| 1.4 | RK3588: Max NPU frequency là TBD | T1 | DS tr.31 | Max NPU frequency NA NA TBD MHz |
| 1.4 | Ridge point của RK3588 | T1 | (không có) | (unknown) |
| 1.5 | TPU: systolic để giảm đọc ghi Unified Buffer | T2 | TPU tr.4 | the matrix unit uses systolic execution to save energy by reducing reads and writes of the Unified Buffer |
| 1.5 | TPU: dữ liệu từ nhiều hướng đến các ô đều đặn | T2 | TPU tr.4 | It relies on data from different directions arriving at cells in an array at regular intervals where they are combined. |
| 1.5 | TPU: dữ liệu vào từ trái, weight nạp từ trên | T2 | TPU tr.4 | data flows in from the left, and the weights are loaded from the top |
| 1.5 | TPU: wavefront chéo | T2 | TPU tr.4 | moves through the matrix as a diagonal wavefront |
| 1.5 | TPU: weight nạp trước | T2 | TPU tr.4 | The weights are preloaded, and take effect with the advancing wave alongside the first data of a new block. |
| 1.5 | TPU: một tile weight 64 KiB cộng một tile cho double-buffering | T2 | TPU tr.3 | The matrix unit holds one 64 KiB tile of weights plus one for double-buffering |
| 1.5 | Fig. 4: partial sum chảy xuống tới accumulator | T2 | TPU tr.4 | Systolic data flow of the Matrix Multiply Unit. |
| 1.5 | Chiều mũi tên dữ liệu phải, partial sum xuống, weight từ trên trong Fig. 4 | T2 | TPU tr.4 | (đọc từ hình) |
| 1.5 | Hình vẽ 4x4 ô là thu gọn của 256x256 | tính | TPU tr.4 | (số học) |
| 1.5 | EYE: WS chạy như systolic array | T2 | EYE tr.7 | the PE array operates as a systolic array with little local control |
| 1.5 | LP: NPU có systolic array | T2 | LP tr.2 | It mainly consists of a systolic array that completes the convolution computation |
| 1.5 | LP: dataflow chọn là output stationary | T2 | LP tr.2 | we adopt the commonly used output stationary as the dataflow for this paper |
| 1.5 | Bài TPU không dùng chữ stationary (đã tìm toàn bài bằng pdftotext) | T2 | (không có) | (unknown) |
| 1.5 | Systolic là cách truyền dữ liệu, stationary là thứ PE giữ (suy ra của bộ hình) | tính | EYE tr.7 | (số học) |
| 1.5 | JUNG: spatial chia input và output theo chiều cao hoặc rộng | T2 | JUNG tr.4 | input and output tensors are partitioned in spatial directions, that means images are segmented in half along the height or width |
| 1.5 | JUNG: spatial nhân bản kernel | T2 | JUNG tr.4 | kernel weights are replicated on both processors |
| 1.5 | JUNG: channel chia output theo kênh | T2 | JUNG tr.4 | Channel direction partitioning (Figure 5 (b)) produces an output image partitioned along channels. |
| 1.5 | JUNG: channel chia kernel và output, nhân bản input | T2 | JUNG tr.4 | the kernel weights and the output tensors are segmented in half along the channel directions, but the input tensors are replicated |
| 1.5 | JUNG: hàng có dấu * cần partial sum reduction | T2 | JUNG tr.4 | but they require extra communication and computation for partial sum reduction |
| 1.5 | JUNG: hai hàng đó không được ưa dùng | T2 | JUNG tr.4 | these methods are undesirable in parallel execution |
| 1.5 | JUNG: hướng chia ảnh hưởng cân bằng tải do alignment | T2 | JUNG tr.9 | the partitioning direction affects workload balancing due to the alignment constraints |
| 1.5 | JUNG: hướng kênh đòi alignment lớn hơn | T2 | JUNG tr.9 | channel direction imposes a relatively larger alignment requirement than the spatial direction |
| 1.5 | JUNG: số kênh quá nhỏ thì mức dùng core giảm | T2 | JUNG tr.9 | If the number of channels is too small to distribute evenly across the cores, core utilization can be degraded. |
| 1.5 | JUNG: SoC mobile ba core | T2 | JUNG tr.1 | flagship mobile SoC with three cores |
| 1.5 | JUNG: tác giả Samsung | T2 | JUNG tr.1 | Samsung Advanced Institute |
| 1.5 | JUNG: double buffering và pipeline load, compute, store | T2 | JUNG tr.4 | software pipeline of load, compute, and store |
| 1.5 | JUNG: DMA chồng lên tính toán | T2 | JUNG tr.4 | the global memory access via DMA can overlap with computations |
| 1.5 | FLEX: tiling là chia một lớp thành các phép trên tile nhỏ | T2 | FLEX tr.2 | operate on smaller data tiles |
| 1.5 | FLEX: tên quá trình là tiling | T2 | FLEX tr.2 | This process is called tiling. |
| 1.5 | Gantt tile 0, 1, 2 qua load, compute, store là minh họa của bộ hình | tính | JUNG tr.4 | (số học) |
| 1.5 | JUNG: depth-first tăng cơ hội tái dùng dữ liệu | T2 | JUNG tr.5 | scheduling layers in depth-first order, as shown in Figure 6 (a), increases chances of data reuse |
| 1.5 | JUNG: breadth-first loại bớt phụ thuộc giữa các lớp kế tiếp | T2 | JUNG tr.5 | eliminates some of the data dependencies among immediately following layers |
| 1.5 | FLEX: list scheduling động cho workload đã tile | T2 | FLEX tr.1 | Flexer employs a list scheduling algorithm to dynamically schedule the tiled workload to all NPUs |
| 1.5 | FLEX: out-of-order scheduler | T2 | FLEX tr.1 | an out-of-order (OoO) scheduler |
| 1.5 | LP: temporal-sharing | T2 | LP tr.1 | in which DNNs occupy the entire hardware resources layer by |
| 1.5 | LP: spatial-sharing | T2 | LP tr.1 | in which each DNN model is allocated fixed hardware resources |
| 1.5 | JUNG: bộ nhớ cục bộ cô lập theo core | T2 | JUNG tr.2 | distributed, isolated local memory per core |
| 1.5 | JUNG: local memory quản lý bằng load và store tới global memory | T2 | JUNG tr.2 | Local memory is explicitly managed by programmers through load and store operations to global memory |
| 1.5 | FLEX: global buffer dùng chung giữa các core | T2 | FLEX tr.2 | A shared on-chip scratchpad memory, labeled Global Buffer |
| 1.5 | LP: nhiều NPU đồng nhất nối router, dữ liệu qua NoC | T2 | LP tr.2 | It consists of multiple homogeneous NPUs, which are connected to routers. The data of each NPU is transmitted through the NoC. |
| 1.5 | LP: tắc nghẽn NoC và DRAM ảnh hưởng hiệu năng | T2 | LP tr.2 | congestion on NoC and DRAM is also a considerable factor in system performance |
| 1.5 | Không có một kiến trúc NPU đa core duy nhất (suy ra của bộ hình từ ba dòng trên) | tính | JUNG tr.2 | (số học) |
| 1.5 | RK3588: ba chế độ triple, dual, independent | T1 | TRM1 tr.1984 | Support triple core co-work, dual core co-work, and work independently |
| 1.5 | RK3588: core mask AUTO | T1 | UG152 tr.26 | RKNN_NPU_CORE_AUTO : Referring to automatic mode, meaning that it will select the idle core inside the NPU; |
| 1.5 | RK3588: op ngoài danh sách về Core0 | T1 | UG152 tr.27 | Other type of op will fallback to Core0 to continue running. |
| 1.5 | RK3588: cách chia một lớp cho nhiều core | T1 | (không có) | (unknown) |
| 1.5 | RK3588: dùng systolic hay tiling như paper; TRM không có các từ khóa này | T1 | (không có) | (unknown) |
