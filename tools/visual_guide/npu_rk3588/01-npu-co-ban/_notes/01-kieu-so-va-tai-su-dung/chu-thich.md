# Ghi chú chuyên đề: Kiểu số, utilization và tái sử dụng dữ liệu

## Câu hỏi mở đầu
Cùng một mảng MAC, vì sao có lớp chạy gần đỉnh còn lớp khác chỉ đạt một phần nhỏ, và phần cứng dùng lại dữ liệu cùng che độ trễ nạp weight bằng cách nào?

## Hình U.1 (hu-1-kieu-so-va-utilization) [T2 chung]
Có hai lý do khiến mảng MAC không đạt đỉnh: kiểu số rộng hơn làm giảm số phép MAC mỗi chu kỳ, và lớp có ít kênh để trống một phần MAC. Matrix Unit 256x256 của TPU chạy nửa tốc khi trộn 8-bit với 16-bit, và một phần tư tốc khi cả hai là 16-bit. Theo Table 3 của TPU, CNN0 dùng có ích 78.2% chu kỳ và đạt 86.0 trên đỉnh 92 TOPS. CNN1 chỉ dùng có ích 22.5%, vì 23.7% chu kỳ chạy với MAC trống do lớp nông, nên chỉ đạt 14.1 TOPS. MLP0 lại mất 53.9% chu kỳ để chờ nạp weight. Với RK3588, TRM chỉ cho số MAC mỗi chu kỳ theo từng kiểu: INT16, FP16 và BF16 đều bằng nửa INT8. Cách RK3588 chạy kiểu trộn, và cách nó lấp mảng MAC khi lớp có ít kênh, đều là unknown. Cột MacUsage(%) của eval_perf là chỗ đo được utilization trên board.
Đọc thêm: 01_ mục 1.4, 1.8. Khái niệm: Hình 1.4, Hình 2.3, Hình 7.3

## Hình U.2 (hu-2-tai-su-dung-va-double-buffering) [T2 chung]
Spatial architecture giảm truy cập bộ nhớ đắt bằng cách dùng lại dữ liệu giữa các PE nối trực tiếp với nhau, còn double buffering che thời gian nạp weight. EYE nêu ba kiểu input data reuse. Convolutional reuse dùng lại mỗi weight E² lần trên một mặt ifmap và mỗi pixel thường R² lần; kiểu này không có ở lớp FC. Filter reuse dùng lại weight qua N ảnh của batch. Ifmap reuse dùng lại pixel qua M filter. Ví dụ của bộ hình: với N = 1 thì filter reuse chỉ còn 1 lần. TPU giữ một tile weight 64 KiB cộng một tile nữa để double-buffering, nhằm che 256 chu kỳ dịch một tile vào. Accumulator cũng được nhân đôi để compiler dùng double buffering. Trong TRM1 tr.1984 đến 2060, RK3588 chỉ có ping-pong cho thanh ghi cấu hình, nên việc RK3588 có double buffering dữ liệu hay không là unknown.
Đọc thêm: 01_ mục 1.2, 1.3, 1.6. Khái niệm: Hình 1.1, Hình 1.2, Hình 1.3, Hình 2.5

## Hiểu sai thường gặp
- "Đổi INT8 sang INT16 chỉ làm file lớn hơn, tốc độ như cũ" -> TPU chạy nửa tốc khi trộn 8-bit với 16-bit, và một phần tư tốc khi cả hai 16-bit; RK3588 có 512 MAC mỗi chu kỳ cho INT16, so với 1024 cho INT8 [TPU tr.3; TRM1 tr.1984] (Hình U.1)
- "Mô hình có cường độ tính toán cao thì luôn chạy gần đỉnh" -> CNN1 có cường độ cao nhưng chỉ đạt 14.1 TOPS, vì khoảng một nửa số MAC không giữ weight có ích do lớp nông [TPU tr.6, tr.7] (Hình U.1)
- "NPU load 100% nghĩa là MAC dùng hết" -> UG232 nói load không biểu diễn trực tiếp MAC utilization; MacUsage(%) là cột riêng của eval_perf [UG232 tr.32, tr.137] (Hình U.1)
- "Lớp FC cũng có convolutional reuse như CONV" -> EYE ghi FC không có kiểu reuse này; FC chỉ có filter reuse và ifmap reuse [EYE tr.3, tr.4] (Hình U.2)
- "Ping-pong của RK3588 là double buffering weight" -> ping-pong trong TRM là chế độ nạp thanh ghi của PC task; double buffering dữ liệu của RK3588 là unknown [TRM1 tr.1997] (Hình U.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Theo TPU Table 3, vì sao CNN1 chỉ đạt 14.1 TOPS trong khi CNN0 đạt 86.0?
Đáp án: Ở CNN1, array active cycles là 46.2%, nhưng chỉ 22.5% chu kỳ có MAC giữ weight có ích; 23.7% là unused MACs, do một số lớp có feature depth nông. Ngoài ra 28.1% chu kỳ là weight stall. CNN0 có 78.2% useful MACs và 0% weight stall [TPU tr.6, tr.7] (Hình U.1)

### Câu 2 (phân biệt)
Phân biệt convolutional reuse, filter reuse và ifmap reuse; kiểu nào có ở lớp FC?
Đáp án: Convolutional reuse dùng lại weight E² lần trên một mặt ifmap và pixel R² lần trên một mặt filter, chỉ có ở CONV. Filter reuse dùng lại weight qua N ifmap của batch. Ifmap reuse dùng lại pixel qua M filter. Hai kiểu sau có ở cả CONV và FC [EYE tr.3, tr.4] (Hình U.2)

### Câu 3 (áp dụng)
Một camera chạy N = 1. Kiểu reuse nào của weight còn lại cho lớp conv 3x3 có ofmap 80x80?
Đáp án: Filter reuse chỉ còn 1 lần, nên chỉ còn convolutional reuse: mỗi weight dùng lại E² = 6400 lần. Đây là phép tính của bộ hình theo công thức của EYE [EYE tr.3, tr.4] (Hình U.2)

### Câu 4 (giải thích)
TPU dùng tile weight thứ hai để làm gì?
Đáp án: Để double-buffering: nạp tile kế tiếp trong khi tính tile hiện tại, che 256 chu kỳ dịch một tile vào [TPU tr.3] (Hình U.2)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| U.1 | Matrix Unit 256x256 MAC, 8-bit | T2 | TPU tr.3 | It contains 256x256 MACs that can perform 8-bit multiply-and-adds |
| U.1 | Trộn 8-bit với 16-bit: nửa tốc | T2 | TPU tr.3 | When using a mix of 8-bit weights and 16-bit activations (or vice versa), the Matrix Unit computes at half-speed |
| U.1 | Cả hai 16-bit: một phần tư tốc | T2 | TPU tr.3 | computes at a quarter-speed when both are 16 bits |
| U.1 | RK3588: INT8 1024 MAC mỗi chu kỳ mỗi core, 3 core | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| U.1 | RK3588: INT16 512 MAC | T1 | TRM1 tr.1984 | 512x3 integer 16 MAC operations per cycle |
| U.1 | RK3588: FP16 512 MAC | T1 | TRM1 tr.1984 | 512x3 float 16 MAC operations per cycle |
| U.1 | RK3588: BF16 512 MAC | T1 | TRM1 tr.1984 | 512x3 bfloat 16 MAC operations per cycle |
| U.1 | Tỉ lệ 512 / 1024 = 1/2 | T1 | TRM1 tr.1984 | (số học) |
| U.1 | RK3588 chạy kiểu trộn 8 và 16-bit ở tốc độ nào: TRM chỉ liệt kê từng kiểu | T1 | TRM1 tr.1984 | (unknown) |
| U.1 | Table 3: array active cycles theo ứng dụng | T2 | TPU tr.7 | Array active cycles 12.7% 10.6% 8.2% 10.5% 78.2% 46.2% |
| U.1 | Table 3: useful MACs | T2 | TPU tr.7 | Useful MACs in 64K matrix (% peak) 12.5% 9.4% 8.2% 6.3% 78.2% 22.5% |
| U.1 | Table 3: unused MACs | T2 | TPU tr.7 | Unused MACs 0.3% 1.2% 0.0% 4.2% 0.0% 23.7% |
| U.1 | Table 3: weight stall | T2 | TPU tr.7 | Weight stall cycles 53.9% 44.2% 58.1% 62.1% 0.0% 28.1% |
| U.1 | Table 3: weight shift | T2 | TPU tr.7 | Weight shift cycles 15.9% 13.4% 15.8% 17.1% 0.0% 7.0% |
| U.1 | Table 3: non-matrix | T2 | TPU tr.7 | Non-matrix cycles 17.5% 31.9% 17.9% 10.3% 21.8% 18.7% |
| U.1 | Table 3: TOPS đạt, đỉnh 92 | T2 | TPU tr.7 | TeraOps/sec (92 Peak) 12.3 9.7 3.7 2.8 86.0 14.1 |
| U.1 | Hàng 1, 4, 5, 6 cộng lại 100%; hàng 2 và 3 tách hàng 1 | T2 | TPU tr.7 | Rows 2 and 3 further break down the fraction of 64K weights in the matrix |
| U.1 | Hàng 1, 4, 5, 6 cộng lại 100% | T2 | TPU tr.7 | Rows 1, 4, 5, and 6 total 100% |
| U.1 | CNN1: khoảng một nửa MAC không giữ weight có ích vì lớp nông | T2 | TPU tr.6 | only about half of the 65,536 MACs hold useful weights because some layers in CNN1 have shallow feature depths |
| U.1 | Cột MacUsage(%) của eval_perf là MAC usage | T1 | UG232 tr.32 | MacUsage(%) MAC usage |
| U.1 | NPU load không biểu diễn trực tiếp MAC utilization | T1 | UG232 tr.137 | the NPU load does not directly represent the actual MAC utilization |
| U.1 | Đường dẫn đọc NPU load | T1 | UG232 tr.137 | cat /sys/kernel/debug/rknpu/load |
| U.1 | RK3588 lấp mảng MAC thế nào khi lớp có ít kênh: TRM không mô tả | T1 | TRM1 tr.1984 | (unknown) |
| U.2 | Định nghĩa spatial architecture | T2 | EYE tr.2 | direct communication between an array of relatively simple processing engines (PEs) |
| U.2 | SA so với SIMD/SIMT | T2 | EYE tr.2 | Compared with SIMD/SIMT architectures, SAs are particularly suitable for applications |
| U.2 | SA hợp với quan hệ producer-consumer hoặc chia sẻ dữ liệu giữa các PE | T2 | EYE tr.2 | exhibits producer-consumer relationships or can leverage |
| U.2 | Hình gốc Figure 1 | T2 | EYE tr.2 | Block diagram of a general CNN accelerator system consisting of a spatial architecture accelerator and an off-chip DRAM |
| U.2 | Bốn cấp lưu trữ | T2 | EYE tr.2 | four levels of storage hierarchy for data accesses, including DRAM, global buffer, array (inter-PE communication) and RF |
| U.2 | DRAM đắt nhất, RF rẻ nhất | T2 | EYE tr.2 | with the highest cost at DRAM and the lowest cost at RF |
| U.2 | Global buffer khai thác input data reuse và che độ trễ DRAM | T2 | EYE tr.2 | used to exploit input data reuse and hide DRAM access latency |
| U.2 | Global buffer thường 100 đến 300kB | T2 | EYE tr.2 | is around 100–300kB |
| U.2 | Ký hiệu N | T2 | EYE tr.3 | batch size of 3D fmaps |
| U.2 | Ký hiệu M | T2 | EYE tr.3 | # of ofmap channels |
| U.2 | Ký hiệu H | T2 | EYE tr.3 | ifmap plane width/height |
| U.2 | Ký hiệu R | T2 | EYE tr.3 | plane width/height (= H in FC) |
| U.2 | Ký hiệu E | T2 | EYE tr.3 | ofmap plane width/height (= 1 in FC) |
| U.2 | Convolutional reuse: weight E² lần trên một mặt ifmap | T2 | EYE tr.3 | is reused E 2 times in the same ifmap plane |
| U.2 | Convolutional reuse: pixel thường R² lần | T2 | EYE tr.3 | is usually reused R2 times |
| U.2 | FC không có convolutional reuse | T2 | EYE tr.3 | FC layers, however, do not have this type of data reuse |
| U.2 | Filter reuse: weight qua N ifmap của batch, CONV và FC | T2 | EYE tr.4 | the batch of N ifmaps in both CONV and FC layers |
| U.2 | Ifmap reuse: pixel qua M filter, CONV và FC | T2 | EYE tr.4 | Each ifmap pixel is further reused across M |
| U.2 | Ví dụ R = 3, E = 80, M = 64, N = 1: 6400, 9, 64, 1 | T2 | EYE tr.3 | (số học) |
| U.2 | TPU: một tile 64 KiB cộng một tile để double-buffering, che 256 chu kỳ | T2 | TPU tr.3 | one 64 KiB tile of weights plus one for double-buffering (to hide the 256 cycles it takes to shift a tile in) |
| U.2 | Accumulator làm tròn lên 2048 rồi nhân đôi cho double buffering | T2 | TPU tr.3 | duplicated it so that the compiler could use double buffering |
| U.2 | Accumulator: làm tròn lên 2048 | T2 | TPU tr.3 | so we rounded that up to 2048 |
| U.2 | Trục thời gian shift và tính là minh họa của bộ hình | T2 | TPU tr.3 | (đọc từ hình) |
| U.2 | RK3588: ping-pong là chế độ nạp thanh ghi của PC task | T1 | TRM1 tr.1997 | PC task ping-pong mode enable |
| U.2 | RK3588 double buffering dữ liệu trong buffer 384KB: không có trong TRM1 tr.1984-2060 | T1 | TRM1 tr.1984 | (unknown) |
