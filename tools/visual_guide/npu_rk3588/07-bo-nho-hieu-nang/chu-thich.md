# Phần 7: Bộ nhớ và hiệu năng

## Câu hỏi mở đầu
Dữ liệu của NPU RK3588 nằm ở những bộ nhớ nào, một con số độ trễ đo đoạn nào của một frame, và mỗi công cụ đo cho biết điều gì (và không cho biết điều gì)?

## Hình 7.1 (h7-1-duong-du-lieu) [T1 RK3588]
NPU lấy dữ liệu qua AXI master từ bộ nhớ nối vào interconnect, còn SRAM của SoC là một bộ nhớ khác với buffer 384KB trong mỗi core và chỉ dùng cho NPU khi đủ ba lớp điều kiện: kernel, DTS, runtime. SoC có 1MB SRAM, 956KB cấp được cho các IP; NPU nhận tối đa 956KB, căn 4K, đặt được hai loại bộ nhớ (Internal và Weight) vào đó. Hai tài liệu mâu thuẫn về librknnrt tối thiểu (1.3.4b14 hay 1.6.0) và cách bật (biến môi trường cho cả Internal và Weight, hay cờ RKNN_FLAG_ENABLE_SRAM chỉ cho Internal Tensor). Trên board RK3588S, kernel đọc được CONFIG_ROCKCHIP_RKNPU_SRAM not set, nên driver không cấp SRAM cho NPU (suy ra từ rknpu_gem.c) và hiệu lực các cờ SRAM của C API là unknown; DTS lưu trong repo còn chia hết 956KB cho hai lõi rkvdec. Nửa dưới so general API (dữ liệu ngoài được copy vào bộ nhớ NPU mỗi frame) với zero-copy (dùng bộ nhớ cấp trước, chỉ có ở C API), kèm điều kiện căn lề 16 byte, cờ cấp phát và đồng bộ cache. Loại DRAM, số kênh và băng thông đỉnh của board là unknown; số T3 duy nhất ở hình là tần số DDR 2112000000 Hz do eval_perf in ra, không phải băng thông. Khung T2 chung chỉ là ngữ cảnh: hai paper vi điều khiển không có DRAM.
Đọc thêm: 07_ mục 7.1, 7.2, 7.4, 7.5. Số đo: Hình 10.2, Hình 10.3
Khái niệm: Hình 2.1, Hình 2.2, Hình 2.3, Hình 5.2, Hình 5.3

## Hình 7.2 (h7-2-thanh-phan-do-tre) [T1 RK3588]
Mỗi con số độ trễ chỉ đo một đoạn của frame: eval_perf (tier 1) lấy thời gian chạy model từ phần cứng của board, còn tier 2 trên board đo pre, npu (lời gọi rknn.inference), post và e2e bằng đồng hồ phần mềm. Vendor chia thời gian triển khai thành user application time, input-output copy time và inference time; hình xếp phép đo của repo lên cách chia đó, và việc lời gọi rknn.inference gồm cả copy là suy ra của bộ hình. Inference qua PC nối board chậm hơn eval_perf và hơn C API trên board vì thêm truyền dữ liệu. Tổng của bảng lớp perf_debug là thời gian chế độ debug, không phải độ trễ: với cùng model silu_opt3, một lần debug cho 18.606 ms (AUTO, lượt 1) so với trung vị 19.154 ms, và 23.482 ms (CORE_0, lượt 2) so với trung vị 20.019 ms. Dự án chưa có log T3 của tier 2.
Đọc thêm: 07_ mục 7.3. Số đo: Hình 10.2, Hình 10.3
Khái niệm: Hình 5.2, Hình 5.3

## Hình 7.3 (h7-3-cong-cu-do) [T1 RK3588]
Tám hàng công cụ đo, mỗi hàng ghi đo gì, điều kiện và dự án đã dùng chưa: eval_perf (không và có perf_debug) đã dùng và có log T3; rknpu/load và devfreq dùng một phần; eval_memory, rknn_query của C API, rknpu/mm và RKNN_LOG_LEVEL chưa đo hoặc không áp dụng được. rknpu/load là phần trăm thời gian NPU chạy task, không phải MAC utilization; MacUsage(%) là một cột khác của eval_perf. Cột DDRCycles và NPUCycles (chỉ Conv) cho biết lớp Conv bị giới hạn bởi băng thông hay bởi tính toán. Cửa sổ lấy mẫu của rknpu/load đọc từ mã là RKNPU_LOAD_INTERVAL = 1000000000 trong ktime_set(0, ...): chu kỳ 1 s là suy ra, chưa đo.
Đọc thêm: 07_ mục 7.3. Số đo: Hình 10.2, Hình 10.3
Khái niệm: Hình 5.3

## Hiểu sai thường gặp
- "384KB buffer và 956KB SRAM là cùng một bộ nhớ" -> 384KB x3 là buffer bên trong core; 956KB là mức tối đa SRAM của SoC cấp được cho NPU, dùng chung với IP khác như codec [TRM1 tr.1984; UG232 tr.106; SRAM dòng 21, 22] (Hình 7.1, Hình 2.3)
- "SRAM được NPU dùng mặc định" -> NPU chỉ dùng SRAM khi có kernel config, DTS cấp vùng và cờ hay biến môi trường; trên board này config not set [UG232 tr.106, 107; SRAM dòng 11, 48; REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7] (Hình 7.1)
- "NPU load % là MAC utilization" -> UG232 nói load không biểu diễn trực tiếp MAC utilization; MacUsage(%) là cột riêng của eval_perf [UG232 tr.32, 137] (Hình 7.3)
- "Tổng của bảng perf_debug là độ trễ" -> đó là thời gian chế độ debug, có thể dài hơn thật; repo dùng trung vị 5 lần eval_perf không debug làm độ trễ tier 1 [UG232 tr.177; REPO ai/core/rknn/benchmark.py:98; LOG t3-board-silu-resize/raw/silu_opt3_CORE_0_layers.txt] (Hình 7.2)
- "Số của eval_perf là tốc độ ứng dụng end-to-end" -> eval_perf chỉ lấy thời gian chạy model từ phần cứng; pre, post và copy nằm ngoài, và inference qua PC chậm hơn on-board [API232 tr.18; UG232 tr.171, 175; REPO ai/board/bench_npu.py:64-74] (Hình 7.2)
- "2112000000 là băng thông (hay speed grade) của DDR" -> đó là DDR Current Frequency List (Hz) do eval_perf in ra; loại DRAM, số kênh và băng thông của board là unknown [UG232 tr.31; LOG t3-board-silu-resize/raw/silu_opt3_layers.txt] (Hình 7.1)
- "RKNN_FLAG_SHARE_SRAM dùng được" -> header có định nghĩa và RT232 mô tả như dùng được, nhưng UG232 ghi chưa implement [HDR dòng 72; RT232 tr.19; UG232 tr.108] (Hình 7.1)
- "RKNNLite trên board có zero-copy" -> wheel Python 2.3.2 không có hàm cấp phát bộ nhớ hay zero-copy; zero-copy chỉ có ở C API [UG232 tr.64] (Hình 7.1)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao trên board RK3588S của dự án không thể coi SRAM là đang được NPU dùng, dù SoC có 956KB SRAM cấp được cho NPU?
Đáp án: Vì SRAM cho NPU cần ba lớp điều kiện (kernel config, DTS, runtime) và lớp kernel không thỏa: kernel board có CONFIG_ROCKCHIP_RKNPU_SRAM not set; trong rknpu_gem.c, SRAM chỉ được cấp khi IS_ENABLED của config đó. DTS lưu trong repo còn chia hết 956KB (0x78000 cộng 0x77000 bằng 0xef000) cho rkvdec0 và rkvdec1. Hiệu lực cờ SRAM của C API trên board là unknown [UG232 tr.106, 107; REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7; DRV rknpu_gem.c:720; DTS dòng 6868-6882] (Hình 7.1)
### Câu 2 (phân biệt)
Phân biệt "NPU 19.154 ms" của eval_perf (tier 1) và "e2e" của bench_npu.py (tier 2): mỗi số gồm và không gồm đoạn nào của frame?
Đáp án: 19.154 ms là trung vị 5 lần eval_perf (Total Time) chạy model do PC điều khiển board, lấy từ phần cứng, không gồm pre-process và post-process. e2e của bench_npu.py chạy trên board bằng RKNNLite, đo từ trước pre-process đến sau post-process (gồm lời gọi rknn.inference), không gồm đọc và giải mã file ảnh. Ranh giới giữa Total Time và copy input/output là unknown; hiện chưa có log T3 của tier 2 để so [API232 tr.18; REPO ai/core/rknn/benchmark.py:1-3, 23; REPO ai/board/bench_npu.py:3-4, 64-74] (Hình 7.2)
### Câu 3 (phân biệt)
Phân biệt rknpu/load với MacUsage(%) của eval_perf.
Đáp án: rknpu/load là phần trăm thời gian NPU chạy task trong một đơn vị thời gian (driver tính busy time của cửa sổ trước chia RKNPU_LOAD_INTERVAL / 100, tối đa 100), không phải MAC utilization. MacUsage(%) là cột "MAC usage" trong bảng lớp của eval_perf (cần perf_debug), phản ánh hiệu suất thực thi trong khối phần cứng NPU theo định nghĩa của UG232 cho MAC utilization [UG232 tr.32, 137; DRV rknpu_debugger.c:64-66] (Hình 7.3)
### Câu 4 (áp dụng)
Khi chạy YOLO trên board, rknpu/load đọc thấp. Theo UG232, cần kiểm những phần nào, và script nào của repo tách được các phần đó?
Đáp án: Load thấp nghĩa là NPU chờ nhận job; cần kiểm thời gian copy input/output, pre-process và post-process của ứng dụng, và có thể dùng đa luồng để tăng load. bench_npu.py tách pre, npu, post, e2e; bench_throughput.py chạy nhiều context RKNNLite song song, mỗi context một thread. Số đo rknpu/load khi chạy chưa có (mới đọc một lần bằng sudo, log không ghi NPU đang làm gì) [UG232 tr.137; REPO ai/board/bench_npu.py:64-74; REPO ai/board/bench_throughput.py:4; LOG t3-board-silu-resize/README.md:46] (Hình 7.2, Hình 7.3)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 7.1 | RK3588 có giao diện bộ nhớ ngoài LPDDR4, LPDDR4X, LPDDR5 | T1 | DS tr.7 | quad channel external memory interface (LPDDR4/LPDDR4X/LPDDR5) |
| 7.1 | DDR: 4 kênh, mỗi kênh rộng 16 bit | T1 | DS tr.8 | Support four channels, each channel 16bits data widths |
| 7.1 | DDR: tối đa 2 rank mỗi kênh | T1 | DS tr.8 | Support up to 2 ranks (chip selects) for each channel |
| 7.1 | Bốn DDR scheduler tích hợp | T1 | TRM2 tr.16 | Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency |
| 7.1 | scheduler0 đến 3 nối DDRCTL0 đến 3 | T1 | TRM2 tr.16 | (đọc từ hình) |
| 7.1 | Board: eval_perf in DDR Current Frequency List 2112000000 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:7-8 | DDR Current Frequency List: - 2112000000 |
| 7.1 | Tần số NPU và DDR tính bằng Hz | T1 | UG232 tr.31 | The NPU and DDR frequency units are both Hz |
| 7.1 | Loại DRAM, số kênh, băng thông đỉnh của board RK3588S | T1 | (không có) | (unknown) |
| 7.1 | SoC có 1MB SRAM, 956KB cấp cho các IP | T1 | UG232 tr.106 | RK3588 SOC contains 1MB of SRAM internally, of which 956KB can be used by various IPs on the SOC. |
| 7.1 | NPU nhận tối đa 956KB, căn 4K | T1 | SRAM dòng 21 | 最大可分配956KB，且大小需要4K对齐 |
| 7.1 | NPU đặt được hai loại bộ nhớ Internal và Weight vào SRAM | T1 | SRAM dòng 4 | 目前支持为Internal和Weight两种类型内存指定分配SRAM |
| 7.1 | SRAM dùng chung với IP khác (codec), vùng không chồng lấn | T1 | SRAM dòng 22 | 各IP分配的SRAM区域不能重叠 |
| 7.1 | Buffer 384KB x3 trong core | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 7.1 | NPU có ba core | T1 | TRM1 tr.1984 | Include triple NPU CORE |
| 7.1 | AXI master lấy dữ liệu từ bộ nhớ nối SoC AXI interconnect | T1 | TRM1 tr.1985 | The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect. |
| 7.1 | Đường nối NPU tới system SRAM | T1 | (không có) | (unknown) |
| 7.1 | Kernel: driver RKNPU từ 0.8.0 | T1 | SRAM dòng 10 | RKNPU驱动版本>=0.8.0 |
| 7.1 | Kernel: bật CONFIG_ROCKCHIP_RKNPU_SRAM=y | T1 | UG232 tr.106 | Kernel config needs to enable CONFIG_ROCKCHIP_RKNPU_SRAM=y |
| 7.1 | Board: CONFIG_ROCKCHIP_RKNPU_SRAM not set | T3 | REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7 | CONFIG_ROCKCHIP_RKNPU_SRAM not set |
| 7.1 | Board: driver rknpu 0.9.8 | T3 | REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:5 | Driver: rknpu 0.9.8 20240828 |
| 7.1 | Driver chỉ cấp SRAM trong rknpu_gem.c khi IS_ENABLED(CONFIG_ROCKCHIP_RKNPU_SRAM) | T1 | DRV rknpu_gem.c:719-721 | IS_ENABLED(CONFIG_ROCKCHIP_RKNPU_SRAM) && |
| 7.1 | rknpu_mem.c không có mã SRAM (kiểm bằng grep sram) | T1 | (không có) | (unknown) |
| 7.1 | rknpu_mm.o chỉ biên dịch khi bật config | T1 | DRV Makefile:14 | rknpu-$(CONFIG_ROCKCHIP_RKNPU_SRAM) += rknpu_mm.o |
| 7.1 | Nút rknpu/mm chỉ có khi bật config | T1 | DRV rknpu_debugger.c:313-315 | #ifdef CONFIG_ROCKCHIP_RKNPU_SRAM |
| 7.1 | Nút rknpu/mm không có trên board (suy ra từ hai dòng trên và config not set) | T1 | REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7 | (số học) |
| 7.1 | DTS: thêm rockchip,sram = rknpu_sram vào node rknpu | T1 | SRAM dòng 48 | rockchip,sram = <&rknpu_sram>; |
| 7.1 | DTS trong repo: syssram dài 0xef000 | T1 | DTS dòng 6868-6882 | reg = <0x0 0xff001000 0x0 0xef000>; |
| 7.1 | DTS trong repo: rkvdec0_sram 0x78000 | T1 | DTS dòng 6868-6882 | reg = <0x0 0x78000>; |
| 7.1 | DTS trong repo: rkvdec1_sram 0x77000 | T1 | DTS dòng 6868-6882 | reg = <0x78000 0x77000>; |
| 7.1 | 0x78000 cộng 0x77000 bằng 0xef000 (phép tính của bộ hình) | tính | DTS dòng 6868-6882 | (số học) |
| 7.1 | Node rknpu trong DTS repo không có rockchip,sram (grep toàn file: chỉ rkvdec0 và rkvdec1 dùng) | T1 | (không có) | (unknown) |
| 7.1 | Runtime tối thiểu 1.3.4b14 (SRAM md) | T1 | SRAM dòng 54 | RKNPU Runtime库(librknnrt.so)版本>=1.3.4b14 |
| 7.1 | Runtime tối thiểu 1.6.0 (UG232) | T1 | UG232 tr.107 | RKNPU Runtime library (librknnrt.so) version >=1.6.0 |
| 7.1 | Bật Internal bằng biến môi trường | T1 | SRAM dòng 61 | export RKNN_INTERNAL_MEM_TYPE=sram |
| 7.1 | Bật Weight bằng biến môi trường | T1 | SRAM dòng 68 | export RKNN_WEIGHT_MEM_TYPE=sram |
| 7.1 | Bật bằng cờ RKNN_FLAG_ENABLE_SRAM | T1 | UG232 tr.107 | Specify RKNN_FLAG_ENABLE_SRAM in the flags parameter of the rknn_init() interface to enable SRAM in this context. |
| 7.1 | Cờ ENABLE_SRAM cấp SRAM cho Internal Tensor memory | T1 | UG232 tr.107 | as the model's Internal Tensor memory |
| 7.1 | RKNN_FLAG_SHARE_SRAM có định nghĩa trong header | T1 | HDR dòng 72 | #define RKNN_FLAG_SHARE_SRAM 0x00001000 |
| 7.1 | RT232 mô tả SHARE_SRAM như dùng được | T1 | RT232 tr.19 | used for the current context to try to share the SRAM memory address space |
| 7.1 | UG232: SHARE_SRAM chưa implement | T1 | UG232 tr.108 | has not yet been implemented |
| 7.1 | RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM trong header | T1 | HDR dòng 385 | RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM = 1 << 2 |
| 7.1 | RT232 tr.34 không liệt kê TRY_ALLOC_SRAM (kiểm tay trên trang) | T1 | (không có) | (unknown) |
| 7.1 | SRAM giảm áp lực băng thông DDR nhưng có thể ảnh hưởng thời gian suy luận | T1 | UG232 tr.106 | SRAM can help RKNPU applications reduce DDR bandwidth pressure, but it may have a certain impact on inference time. |
| 7.1 | Hiệu lực cờ SRAM của C API trên board; A/B có và không SRAM | T3 | (không có) | (unknown) |
| 7.1 | General API: dữ liệu ngoài copy vào input memory của NPU mỗi frame | T1 | UG232 tr.64 | the data allocated externally needs to be copied to the input memory of the NPU during runtime |
| 7.1 | Zero-copy dùng bộ nhớ cấp trước (kể cả NPU hay DRM tạo) | T1 | UG232 tr.64 | while the zero-copy interface uses preallocated memory directly |
| 7.1 | Zero-copy giảm copy, hiệu năng tốt hơn, ít băng thông | T1 | UG232 tr.64 | reducing the cost of copying memory, better performance and less bandwidth |
| 7.1 | General API và zero-copy không gọi chung | T1 | UG232 tr.64 | General API and zero-copy API interface cannot be called together. |
| 7.1 | General API: normalize, quantize, đổi layout, dequantize chạy trên CPU, inference trên NPU | T1 | UG232 tr.65 | running on the CPU except for the inference of the model which runs on the NPU |
| 7.1 | General API: khi thỏa căn lề, normalize và quantize chạy trên NPU nhưng CPU vẫn copy input | T1 | UG232 tr.65 | the input data still needs to be copied to the model's input buffer using the CPU |
| 7.1 | Zero-copy: normalize, quantize, inference trên NPU | T1 | UG232 tr.65 | Zero-copy API normalization, quantization, and model inference are all running on the NPU. |
| 7.1 | Zero-copy: đầu ra đổi layout và dequantize trên CPU hoặc NPU | T1 | UG232 tr.65 | The output data format and dequantization process is running on the CPU or NPU. |
| 7.1 | Các hộp của Figure 5-5 và 5-6 (nhãn và thứ tự bước) | T1 | UG232 tr.65 | (đọc từ hình) |
| 7.1 | Căn lề input 4 chiều 1, 3, 4 kênh: Width 16-byte aligned (nhóm có RK3588) | T1 | UG232 tr.65 | Width 16-byte aligned |
| 7.1 | Căn lề input không phải 4 chiều: Total size 16-byte aligned | T1 | UG232 tr.65 | Total size 16-byte aligned |
| 7.1 | RK3588 thuộc nhóm cột RV1103, RV1106, RV1126B, RK3562, RK3576, RK3588 của Table 5-2 | T1 | UG232 tr.65 | RV1103/RV1106/RV1126B/RK3562/RK3576/RK3588 |
| 7.1 | Lý do quy tắc căn 16 byte | T1 | (không có) | (unknown) |
| 7.1 | Query layout input bằng RKNN_QUERY_NATIVE_INPUT_ATTR, không phải INPUT_ATTR | T1 | UG232 tr.69 | Use RKNN_QUERY_NATIVE_INPUT_ATTR to query related attributes (note, not |
| 7.1 | Ví dụ rknn_create_mem_demo.cpp dùng RKNN_QUERY_INPUT_ATTR | T1 | REPO 3rdparty/rknn-toolkit2/rknpu2/examples/rknn_api_demo/src/rknn_create_mem_demo.cpp:205 | rknn_query(ctx, RKNN_QUERY_INPUT_ATTR, &(input_attrs[i]), sizeof(rknn_tensor_attr)); |
| 7.1 | CACHEABLE = 1 << 0 | T1 | HDR dòng 381-386 | RKNN_FLAG_MEMORY_CACHEABLE = 1 << 0 |
| 7.1 | DEFAULT cùng nghĩa với CACHEABLE | T1 | HDR dòng 381-386 | Same with RKNN_FLAG_MEMORY_CACHEABLE |
| 7.1 | NON_CACHEABLE = 1 << 1 | T1 | HDR dòng 381-386 | RKNN_FLAG_MEMORY_NON_CACHEABLE = 1 << 1 |
| 7.1 | CPU ghi bộ nhớ cacheable rồi NPU truy cập: phải đồng bộ cache sang DDR | T1 | UG232 tr.112 | it must ensure that the data in the CPU cache is synchronized to the DDR |
| 7.1 | TO_DEVICE: từ CPU sang NPU | T1 | UG232 tr.112 | Indicates that the data synchronization direction is from CPU to NPU device |
| 7.1 | FROM_DEVICE: từ NPU sang CPU | T1 | UG232 tr.112 | Indicates that the data synchronization direction is from NPU device to CPU |
| 7.1 | rknn_mem_sync đồng bộ bộ nhớ tạo với cờ cacheable | T1 | RT232 tr.38 | synchronize a memory created with the cacheable flag |
| 7.1 | Wheel RKNN-Toolkit-Lite2 2.3.2 và Toolkit2 không có hàm cấp phát bộ nhớ, zero-copy, đồng bộ cache (kiểm tay: liệt kê def của rknn_lite.py và rknn.py) | T1 | (không có) | (unknown) |
| 7.1 | Ví dụ zero-copy chính thức nằm ở C API (rknpu2) | T1 | UG232 tr.64 | examples/rknn_zero_copy directory under the rknpu2 project |
| 7.1 | Tier 2 của repo dùng RKNNLite | T3 | REPO ai/board/bench_npu.py:15 | from rknnlite.api import RKNNLite |
| 7.1 | Tier 2 dùng general API (suy ra: Python không có zero-copy) | T3 | REPO ai/board/bench_npu.py:67 | (số học) |
| 7.1 | Tier 2 tách pre, npu, post (dùng ở Hình 7.2) | T3 | REPO ai/board/bench_npu.py:64-74 | out = rknn.inference(inputs=[inp])[0] |
| 7.1 | A/B SRAM, băng thông DDR đạt được, zero-copy so general, cacheable so non-cacheable, NC1HWC2 so NHWC, tranh chấp DDR: chưa có log T3 | T3 | (không có) | (unknown) |
| 7.1 | Băng thông đỉnh DDR (GB/s): không nguồn nào nêu | T1 | (không có) | (unknown) |
| 7.1 | Độ trễ, băng thông SRAM nhìn từ NPU; NPU nối cổng AXI slave nào | T1 | (không có) | (unknown) |
| 7.1 | MCU không có DRAM | T2 | MCU tr.1 | nor do they have DRAM |
| 7.1 | SRAM giới hạn kích thước activation, Flash giới hạn kích thước model | T2 | MCU tr.3 | SRAM constrains the activation size (read&write); Flash constrains the model size (read-only) |
| 7.1 | PhiNets tách computational cost, working memory, parameter memory | T2 | PHI tr.1 | decouple the computational cost, working memory, and parameter memory |
| 7.1 | Hai paper không đo băng thông DDR hay NPU | T2 | MCU tr.3 | (unknown) |
| 7.2 | Vendor chia thời gian triển khai thành ba phần | T1 | UG232 tr.137 | user application time, input-output data copy time, and model inference time |
| 7.2 | User application time gồm pre-processing, post-processing, logic code | T1 | UG232 tr.137 | it includes pre-processing, post-processing, and the execution time of logical code |
| 7.2 | General API có copy time giữa bộ nhớ vào ra và bộ nhớ NPU | T1 | UG232 tr.137 | there is a copy time involved between the input/output memory and the NPU memory |
| 7.2 | Thứ tự pre, copy vào, NPU, copy ra, post trên trục thời gian là sắp xếp của bộ hình | tính | UG232 tr.137 | (số học) |
| 7.2 | Tier 2: chạy trên board với RKNNLite | T3 | REPO ai/board/bench_npu.py:1 | run ON THE BOARD with RKNNLite |
| 7.2 | Tier 2: đọc và giải mã file không tính | T3 | REPO ai/board/bench_npu.py:3-4 | file read/decode excluded |
| 7.2 | Tier 2: ảnh đọc trước t0 | T3 | REPO ai/board/bench_npu.py:63-64 | bgr = cv2.imread(str(path)) |
| 7.2 | Tier 2: pre là t1 trừ t0 | T3 | REPO ai/board/bench_npu.py:71 | pre.append((t1 - t0) * 1e3) |
| 7.2 | Tier 2: npu là lời gọi rknn.inference, t2 trừ t1 | T3 | REPO ai/board/bench_npu.py:67-72 | npu.append((t2 - t1) * 1e3) |
| 7.2 | Tier 2: post là t3 trừ t2 | T3 | REPO ai/board/bench_npu.py:73 | post.append((t3 - t2) * 1e3) |
| 7.2 | Tier 2: e2e là t3 trừ t0 | T3 | REPO ai/board/bench_npu.py:74 | e2e.append((t3 - t0) * 1e3) |
| 7.2 | Tier 2: 20 warmup | T3 | REPO ai/board/common.py:27 | WARMUP = 20 |
| 7.2 | Tier 2: một lượt qua tập test | T3 | REPO ai/board/bench_npu.py:3 | one timed pass over the test set |
| 7.2 | Tier 2: mean, p50, p95, std | T3 | REPO ai/board/common.py:124-132 | "p95": round(float(np.percentile(a, 95)), 3), |
| 7.2 | Tier 2: ghi tần số trước và sau | T3 | REPO ai/board/bench_npu.py:93-94 | "frequency_after": frequency_state(), |
| 7.2 | Tier 2: đo VmRSS, CPU, nhiệt độ NPU | T3 | REPO ai/board/common.py:185 | Samples this process' VmRSS and CPU %, system CPU % and NPU temperature |
| 7.2 | FPS_latency = 1000 / E2E mean | T3 | REPO ai/automation/tables.py:288 | FPS_latency = 1000 / E2E mean. |
| 7.2 | Table G: cột NPU tier 1 là median của 5 lần eval_perf, các cột khác từ tier 2 | T3 | REPO ai/automation/tables.py:288 | NPU (tier 1) = median of 5 `eval_perf` calls; other columns from tier 2 on the board |
| 7.2 | Table G có cột NPU P50 (tier 2) | T3 | REPO ai/automation/tables.py:289 | NPU P50 (tier 2) |
| 7.2 | Tier 1: PC điều khiển board | T3 | REPO ai/core/rknn/benchmark.py:1 | driven from the PC |
| 7.2 | Tier 1: thời gian lấy từ phần cứng board, không chịu trễ mạng PC-board | T3 | REPO ai/core/rknn/benchmark.py:3 | Timing comes from board hardware via eval_perf(), unaffected by PC-board network delay. |
| 7.2 | Tier 1: cần rknn_server trên board | T3 | REPO ai/core/rknn/benchmark.py:4 | Needs adbd + rknn_server on the board |
| 7.2 | eval_perf không debug: thông tin lấy từ phần cứng, chỉ có tổng thời gian chạy model | T1 | API232 tr.18 | the performance information is obtained from hardware, which only contains the total running time of model |
| 7.2 | Tier 1: 5 lần eval_perf, lấy trung vị | T3 | REPO ai/core/rknn/benchmark.py:23 | PERF_REPEATS = 5 |
| 7.2 | Tier 1: fix_freq=True khi gọi eval_perf | T3 | REPO ai/core/rknn/benchmark.py:85 | rknn.eval_perf(is_print=False, fix_freq=True) |
| 7.2 | Tier 1: chữ Total Time(us) của đầu ra không debug | T3 | REPO ai/core/rknn/benchmark.py:25 | Total Time(us) |
| 7.2 | Tier 1: perf_debug và eval_mem ở phiên riêng vì đổi thời gian đo | T3 | REPO ai/core/rknn/benchmark.py:37-38 | Keep them in separate sessions: both change the measured time. |
| 7.2 | Tier 1: tổng bảng lớp là thời gian debug, không phải độ trễ | T3 | REPO ai/core/rknn/benchmark.py:98 | its total is debug-mode time, not the latency |
| 7.2 | perf_debug và eval_mem ảnh hưởng hiệu năng | T1 | RKNNPY rknn/api/rknn.py:290-291 | it will affect performance |
| 7.2 | PERF_RUN: thời gian chạy model, không gồm setting input/output | T1 | RT232 tr.25 | inference time of the model (not including setting input/output) |
| 7.2 | Inference qua PC nối board có thêm copy và truyền dữ liệu, chậm hơn on-board | T1 | UG232 tr.171 | involves additional data copying and transmission processes |
| 7.2 | Inference on-board nhanh hơn board-connected | T1 | UG232 tr.171 | Inference on-board is faster than inference with board-connected |
| 7.2 | rknn.inference chậm hơn eval_perf | T1 | UG232 tr.175 | rknn.inference is slower than rknn.eval_perf |
| 7.2 | Chế độ debug thêm mã, có thể tắt cơ chế song song nên dài hơn | T1 | UG232 tr.177 | some parallel mechanisms may be disabled |
| 7.2 | Tần số cố định là điều kiện để số đo có nghĩa | T1 | UG232 tr.136 | Only when the baselines are the same, the measured performance data becomes meaningful. |
| 7.2 | Cảnh báo của chính eval_perf khi perf_debug | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:9 | The performance result is just for debugging, may worse than actual performance! |
| 7.2 | T3: silu_opt3 AUTO lượt 1, 5 lần không debug | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | 17.769, 19.154, 19.432, 17.984, 19.628 |
| 7.2 | T3: silu_opt3 AUTO, perf_debug một lần, 18606 us | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:135 | Total Operator Elapsed Per Frame Time(us): 18606 |
| 7.2 | T3: tổng NPUTime 17761, TotalTime 18606 (hàng Total của bảng xếp hạng) | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:159 | Total 845 0 17761 18606 |
| 7.2 | T3: Transpose chạy CPU 823 us | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:146 | Transpose 1 823 0 0 823 |
| 7.2 | 18606 = 17761 + 845; 845 là CPUTime của hàng Total (phép tính của bộ hình) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:159 | (số học) |
| 7.2 | T3: silu_opt3 CORE_0 lượt 2, trung vị 20.019 ms | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | "silu_opt3\|CORE_0": { "ms": 20.019, |
| 7.2 | T3: silu_opt3 CORE_0 lượt 2, 5 lần từ 18.17 đến 22.257 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | 18.17, 22.257, 19.367, 20.019, 22.113 |
| 7.2 | T3: silu_opt3 CORE_0, perf_debug một lần, 23482 us | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_layers.txt:135 | Total Operator Elapsed Per Frame Time(us): 23482 |
| 7.2 | 23.482 ms lớn hơn mọi giá trị trong 5 lần không debug (phép so của bộ hình) | tính | LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json | (số học) |
| 7.2 | Lượt 1 và lượt 2 là hai lượt khác nhau của cùng thí nghiệm | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Lượt 2: tách ảnh hưởng của `Add`, và đa lõi |
| 7.2 | Tổng debug không phải độ trễ để báo cáo, chỉ để tìm lớp tốn thời gian | T1 | UG232 tr.177 | The main reason for perf_debug=True is to see if there are more time-consuming layers in the model |
| 7.2 | Ranh giới của Total Time(us): có gồm đặt input và lấy output hay không | T1 | (không có) | (unknown) |
| 7.2 | Tách copy khỏi chạy model bên trong rknn.inference của RKNNLite | T1 | (không có) | (unknown) |
| 7.2 | Log T3 của tier 2 (bench_npu.py, bench_throughput.py) chưa có (kiểm tay: tmp/04_debug-logs/ và ai/automation/runs/ không có file tier 2) | T3 | (không có) | (unknown) |
| 7.2 | Mức chênh perf_debug so với không debug chưa đo riêng | T3 | (không có) | (unknown) |
| 7.3 | eval_perf in Current Frequency List của CPU, NPU, DDR | T1 | UG232 tr.31 | CPU Current Frequency List: |
| 7.3 | fix_freq: thử cố định tần số CPU, NPU, DDR | T1 | UG232 tr.31 | whether you need to try to fix the frequency of the hardware (including CPU/NPU/DDR) |
| 7.3 | fix_freq mặc định True | T1 | API232 tr.18 | fix_freq: Whether to fix hardware frequency. The default value is True. |
| 7.3 | eval_perf chạy với board nối PC | T1 | API232 tr.18 | which connected to PC |
| 7.3 | RKNN-Toolkit-Lite2 không có eval_perf (kiểm tay: liệt kê def của rknn_lite.py) | T1 | (không có) | (unknown) |
| 7.3 | T3: silu_opt3 AUTO lượt 1, trung vị 19.154 ms | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/summary.json | "npu_latency_ms": 19.154, |
| 7.3 | Hiệu lực fix_freq chưa đo; cơ chế fix_freq đặt tần số qua nút nào | T3 | (không có) | (unknown) |
| 7.3 | perf_debug: thời gian từng lớp, nếu False chỉ tổng | T1 | API232 tr.16 | In debug mode, the running time of each layer can be obtained, otherwise, only the total running time of model can be given. |
| 7.3 | Cột DDRCycles | T1 | UG232 tr.32 | DDRCycles DDR reading and writing clock cycles |
| 7.3 | Cột NPUCycles | T1 | UG232 tr.32 | NPUCycles NPU counts clock cycles |
| 7.3 | Cột MaxCycles | T1 | UG232 tr.32 | MaxCycles Maximum values of DDR Cycles and NPU Cycles |
| 7.3 | Cột MacUsage(%) là MAC usage | T1 | UG232 tr.32 | MacUsage(%) MAC usage |
| 7.3 | Cột WorkLoad(0/1/2), chỉ RK3588 | T1 | UG232 tr.32 | 0/1/2 Core load condition (RK3588 platform only) |
| 7.3 | Cột RW(KB) | T1 | UG232 tr.32 | RW(KB) Total amount of data read and written (KB) |
| 7.3 | Total Memory Read/Write Per Frame Size(KB) là băng thông một frame | T1 | UG232 tr.32 | Total bandwidth consumption of a single frame for model inference |
| 7.3 | NPUCycles chỉ có cho Conv | T1 | UG232 tr.140 | the NPU Cycles column only displays the Cycles required by Conv |
| 7.3 | DDR Cycles lớn hơn nhiều NPU Cycles: Conv bị giới hạn băng thông | T1 | UG232 tr.140 | so the Conv bottleneck comes from bandwidth |
| 7.3 | DDR Cycles nhỏ hơn nhiều NPU Cycles: Conv bị giới hạn tính toán | T1 | UG232 tr.140 | so the Conv bottleneck comes from calculation |
| 7.3 | RW(KB) và DDRCycles là số đo hay tính từ mô hình | T1 | (không có) | (unknown) |
| 7.3 | T3: silu_opt3 39007.21 KB mỗi frame | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt:136 | Total Memory Read/Write Per Frame Size(KB): 39007.21 |
| 7.3 | eval_memory báo Weight, Internal Tensor, Other, Total Memory | T1 | UG232 tr.33 | Internal Tensor Memory: 7.42 MiB |
| 7.3 | eval_memory: total_memory là bộ nhớ model, không phải băng thông | T1 | API232 tr.19 | represents the memory footprint of the model |
| 7.3 | eval_memory cần eval_mem=True | T1 | API232 tr.16 | eval_mem: Whether enter memory evaluation mode. |
| 7.3 | Hàm measure_memory trong benchmark.py | T3 | REPO ai/core/rknn/benchmark.py:110-115 | def measure_memory(rknn: RKNN) -> dict: |
| 7.3 | eval_memory chưa có log T3 | T3 | (không có) | (unknown) |
| 7.3 | PERF_RUN: thời gian chạy model, không gồm set input/output | T1 | RT232 tr.25 | inference time of the model (not including setting input/output) |
| 7.3 | PERF_DETAIL: cần RKNN_FLAG_COLLECT_PERF_MASK lúc init | T1 | RT232 tr.25 | needs to include the RKNN_FLAG_COLLECT_PERF_MASK flag |
| 7.3 | PERF_DETAIL làm giảm frame rate | T1 | HDR dòng 42-45 | but it will reduce the frame rate. |
| 7.3 | MEM_SIZE có total_sram_size, free_sram_size | T1 | HDR dòng 349-356 | uint32_t total_sram_size; |
| 7.3 | C API rknn_query chưa dùng, chưa đo | T3 | (không có) | (unknown) |
| 7.3 | rknpu/load: phần trăm thời gian NPU chạy task | T1 | UG232 tr.137 | The NPU load represents the percentage of time the NPU is executing tasks within a unit of time. |
| 7.3 | Load không phải MAC utilization | T1 | UG232 tr.137 | the NPU load does not directly represent the actual MAC utilization |
| 7.3 | Load thấp: NPU chờ nhận job, kiểm copy, pre, post, đa luồng | T1 | UG232 tr.137 | it indicates that the NPU is waiting for task submissions for a longer duration |
| 7.3 | Đa luồng giúp tăng load | T1 | UG232 tr.137 | utilizing multi-threading in the application can help increase the NPU load |
| 7.3 | Driver: chia busy time cho RKNPU_LOAD_INTERVAL / 100 | T1 | DRV rknpu_debugger.c:64 | div_value = (RKNPU_LOAD_INTERVAL / 100); |
| 7.3 | Driver: tối đa 100 | T1 | DRV rknpu_debugger.c:66 | load = total_busy_time > 100 ? 100 : total_busy_time; |
| 7.3 | Driver: total_busy_time lấy busy_time của cửa sổ trước rồi đặt busy_time về 0 | T1 | DRV rknpu_drv.c:770-772 | subcore_data->timer.busy_time = 0; |
| 7.3 | RKNPU_LOAD_INTERVAL = 1000000000 | T1 | DRV rknpu_drv.h:40 | #define RKNPU_LOAD_INTERVAL 1000000000 |
| 7.3 | Chu kỳ hrtimer là ktime_set(0, RKNPU_LOAD_INTERVAL) | T1 | DRV rknpu_drv.c:783 | rknpu_dev->kt = ktime_set(0, RKNPU_LOAD_INTERVAL); |
| 7.3 | Chu kỳ 1 s: suy ra từ ktime_set (đối số thứ hai là ns), không kiểm được trong repo | T1 | DRV rknpu_drv.c:783 | (số học) |
| 7.3 | T3: load đọc một lần bằng sudo (2026-10-10), log không ghi NPU đang làm gì; giá trị 0% mỗi core | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:46 | NPU load:  Core0:  0%, Core1:  0%, Core2:  0%, |
| 7.3 | rknpu/load khi chạy chưa đo; chu kỳ lấy mẫu thực chưa đo | T3 | (không có) | (unknown) |
| 7.3 | devfreq: cur_freq của NPU RK3588 | T1 | UG152 tr.72 | cat /sys/class/devfreq/fdab0000.npu/cur_freq |
| 7.3 | devfreq: cur_freq của DDR | T1 | UG152 tr.72 | cat /sys/class/devfreq/dmc/cur_freq |
| 7.3 | RK3588 cần nâng firmware | T1 | UG152 tr.72 | For RK3588 (Need to upgrade firmware): |
| 7.3 | Cố định tần số NPU bằng governor userspace | T1 | UG152 tr.73 | echo userspace > /sys/class/devfreq/fdab0000.npu/governor |
| 7.3 | rknpu/freq: nút từ driver 0.8.2 | T1 | UG152 tr.74 | cat /sys/kernel/debug/rknpu/freq |
| 7.3 | lock_freq.sh dùng governor performance, không dùng userspace | T3 | REPO ai/board/lock_freq.sh:5-6 | this board's "performance" pins every clock at |
| 7.3 | T3: NPU cur_freq 1000000000 ghi trong phaseA.json (dòng 36) | T3 | LOG 2026-10-10_yolo-phaseA/raw/phaseA.json:36 | "npu_cur_freq": 1000000000.0, |
| 7.3 | T3: rknpu/freq đọc bằng sudo là 1000000000 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:47 | `freq` \| `1000000000` |
| 7.3 | DDR dmc cur_freq chưa có log | T3 | (không có) | (unknown) |
| 7.3 | rknpu/mm: bitmap SRAM, mỗi bit 4KB | T1 | SRAM dòng 94 | SRAM bitmap: "*" - used, "." - free (1bit = 4KB) |
| 7.3 | dmesg grep rknpu cho dòng sram region | T1 | SRAM dòng 86 | sram region: [0x00000000ff001000 |
| 7.3 | rknpu/mm chỉ có khi bật CONFIG_ROCKCHIP_RKNPU_SRAM | T1 | DRV rknpu_debugger.c:313-315 | #ifdef CONFIG_ROCKCHIP_RKNPU_SRAM |
| 7.3 | Board: config not set, nên rknpu/mm không có (suy ra) | T3 | REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7 | CONFIG_ROCKCHIP_RKNPU_SRAM not set |
| 7.3 | RKNN_LOG_LEVEL=4 in thời gian từng lớp | T1 | UG232 tr.138 | export RKNN_LOG_LEVEL=4 |
| 7.3 | Đo độ trễ một frame đặt log level 1 vì log tốn thời gian | T1 | UG232 tr.137 | the LOG level is set to 1 |
| 7.3 | RKNN_LOG_LEVEL chưa dùng | T3 | (không có) | (unknown) |
| 7.3 | Chưa đo: eval_memory, PERF_RUN và PERF_DETAIL, rknpu/load khi chạy, fix_freq, tranh chấp DDR, băng thông DDR đạt được | T3 | (không có) | (unknown) |
