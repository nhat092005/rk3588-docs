# Phần 2: Phần cứng RK3588

## Câu hỏi mở đầu
NPU của RK3588 gồm những khối nào, nối với SoC bằng đường nào, và phần mềm điều khiển nó theo trình tự nào?

## Hình 2.1 (h2-1-npu-trong-soc) [T1 RK3588]
NPU là một master trên interconnect của SoC: dữ liệu đi bằng AXI master, cấu hình đi bằng AHB slave. NPU (TRM gọi là RKNN) gồm ba core, mỗi core có địa chỉ nền 64KB và một ngắt riêng; ba core nằm trong ba power domain PD_NPUTOP, PD_NPU1, PD_NPU2, và MCU_NPU cùng domain với core 0. Interconnect có bốn DDR scheduler nối tới DDRCTL0 đến DDRCTL3; system SRAM của SoC là bộ nhớ riêng, dùng chung với các IP khác và NPU nhận tối đa 956KB. Hình đánh dấu unknown ba điều nguồn không cho: vai trò của MCU_NPU, đường nối NPU tới system SRAM, vị trí IOMMU trên đường dữ liệu.
Đọc thêm: 02_ mục 2.1, 2.2, 2.7.
Hình gốc: ../../npu_study/images/02_rk3588_npu_hardware/trm2_p16_fig1-1.png (TRM2 tr.16, Fig. 1-1; nhúng vì hình gốc cho thấy NPU là một master cùng CPU, GPU, VOP, ISP và bốn scheduler)

## Hình 2.2 (h2-2-ben-trong-loi) [T1 RK3588]
Một core gồm đường vào dữ liệu CNA, buffer 384KB, MAC array với accumulator, rồi DPU và PPU, cùng hai giao diện: AXI cho dữ liệu và AHB cho cấu hình. Dữ liệu đi theo thứ tự đánh số: CNA (Weight Decompress, Zero-Skipping, Weight Data Load, Feature Data Load), buffer, Sequence Controller, MAC array, accumulator, DPU (hàm theo từng giá trị đơn, softmax, transpose, đổi định dạng), PPU (pooling). Buffer 384KB chia thành bank giữa weight và feature theo hai thanh ghi weight_bank và data_bank; kích thước một bank không có trong nguồn. Zero-Skipping chỉ được TRM mô tả là không fetch weight khi feature bằng 0, không phải MAC bỏ phép nhân.
Đọc thêm: 02_ mục 2.3, 2.6.
Hình gốc: ../../npu_study/images/02_rk3588_npu_hardware/trm1_p1985_fig36-2.png (TRM1 tr.1985, Fig. 36-2; nhúng để đối chiếu hình vẽ lại với hình gốc, nhất là chiều các mũi tên)

## Hình 2.3 (h2-3-bang-so) [T1 RK3588]
Các con số phần cứng của NPU là MAC trên mỗi chu kỳ cho sáu kiểu số, 384KB buffer mỗi core và 956KB SRAM tối đa; số TOPS và tần số thì nguồn chỉ cho một phần. TRM ghi INT8 là 1024x3 MAC mỗi chu kỳ, Datasheet ghi "up to 6TOPs" nhưng tần số tối đa là TBD. Con số 6.144 TOPS trong hình là phép tính của bộ hình (1024 x 3 x 2 x 1 GHz), với quy ước 2 phép mỗi MAC lấy từ một paper T2, không phải từ tài liệu vendor. Trong SDK, danh sách quantized_dtype của API Reference chỉ có w8a8 không bị giới hạn sang chip khác, nên INT4, BF16, TF32 của TRM không có đường qua rknn.config. Khung T3 chỉ chứa giá trị có file log trên đĩa.
Đọc thêm: 02_ mục 2.4, 2.6, 2.7, 2.8.

## Hình 2.4 (h2-4-da-loi-core-mask) [T1 RK3588]
Ba chế độ phần cứng (triple core co-work, dual core co-work, work independently) được chọn qua core mask của API, và driver chọn core và xếp hàng đợi theo mask đó. Ở API, RKNN_NPU_CORE_AUTO chọn core đang rảnh, các mask còn lại gọi tên core; chỉ một danh sách op (Conv, Add, Concat, Relu...) được nêu là nhanh hơn khi dùng nhiều core, op khác chạy về Core0. Ở driver, chỉ năm mask 0x1, 0x2, 0x4, 0x3, 0x7 hợp lệ; mask 0x0 (AUTO) chọn một core có task_num nhỏ nhất, còn phần chia task theo core do userspace gửi sẵn trong subcore_task. Năm giá trị nn_mode (32x32, 64x32, 96x32, 32x64, 32x96) không được dùng làm nhãn cho dual hay triple vì TRM không gắn chúng với nhau.
Đọc thêm: 02_ mục 2.5. Số đo: Hình 10.3
Khái niệm liên quan: Hình 2.5

## Hình 2.5 (h2-5-mot-job) [T1 RK3588]
Ở PC mode, phần mềm chuẩn bị danh sách thanh ghi trong bộ nhớ hệ thống rồi chỉ ghi vài thanh ghi PC, còn NPU tự lấy danh sách qua AXI. Trình tự theo Fig. 36-3: khởi tạo thông tin thanh ghi, ghi pc_interrupt_clear và pc_interrupt_mask, ghi pc_amount, pc_addr, pc_task_number, pc_task_dma_base, rồi ghi pc_op_enable. Mỗi thanh ghi trong danh sách dài 64 bit và op_en đặt cuối danh sách; ping-pong cho phép cấu hình nhóm này khi nhóm kia chạy. NPU có 3 tín hiệu ngắt giữ cho đến khi host xóa; 17 sự kiện nhưng TRM chỉ mô tả bit 0 đến 13. Slave mode là cách còn lại: CPU ghi thanh ghi trực tiếp qua AHB. Không nhúng Fig. 36-3 vì hình đã được vẽ lại đầy đủ ở đây.
Đọc thêm: 02_ mục 2.9.

## Hiểu sai thường gặp
- "NPU chạy 1 GHz là tần số tối đa hoặc mặc định" -> Datasheet V0.1 ghi Max NPU frequency là TBD; 1 GHz là điểm OPP cao nhất trong DTS và là giá trị trong lệnh ví dụ của User Guide [DS tr.31; DTS dòng 3534-3655; UG152 tr.73] (Hình 2.3)
- "6 TOPS là kết quả vendor tự suy ra" -> Datasheet chỉ ghi "up to 6TOPs"; 6.144 = 1024 x 3 x 2 x 1 GHz là phép tính của bộ hình, quy ước 2 phép mỗi MAC đến từ T2 BAMB tr.1 [DS tr.7; BAMB tr.1] (Hình 2.3)
- "RK3588 chạy model INT4, BF16, TF32 qua rknn.config" -> trong danh sách quantized_dtype, chỉ w8a8 không bị giới hạn sang chip khác; w4a16, w8a16, w16a16i nêu chip khác [API232 tr.7] (Hình 2.3)
- "Dual core là nn_mode 64x32" -> TRM1 tr.2001 liệt kê 5 giá trị nn_mode dưới "co-work mode" (3'd0 Int8 mac array 32x32, 3'd1 64x32, 3'd2 96x32, 3'd4 32x64, 3'd5 32x96) và không gắn giá trị nào với dual hay triple [TRM1 tr.2001] (Hình 2.4)
- "Mỗi bank của buffer 384KB là 48KB" -> TRM chỉ có chỉ số bank trong thanh ghi weight_bank và data_bank, không có kích thước; 384/8 là suy luận không có nguồn [TRM1 tr.2004] (Hình 2.2)
- "Zero-skipping nghĩa là MAC bỏ phép nhân với 0" -> TRM chỉ nói weight tương ứng không được fetch khi feature bằng 0; không nói MAC array có bỏ phép nhân hay không [TRM1 tr.2006] (Hình 2.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao không được gộp "384KB" và "956KB" thành một bộ nhớ của NPU?
Đáp án: 384KB x3 là buffer bên trong core (Fig. 36-2 vẽ nó trong khung NPU CORE), còn 956KB là mức tối đa SRAM của SoC có thể cấp cho NPU, dùng chung với IP khác (ví dụ codec) và các vùng không được chồng lấn [TRM1 tr.1984, 1985; SRAM dòng 21, 22] (Hình 2.1, Hình 2.3)
### Câu 2 (phân biệt)
Phân biệt AXI master và AHB slave của NPU, và hai cách cấu hình pc_sel = 0 với pc_sel = 1.
Đáp án: AXI master lấy dữ liệu từ bộ nhớ nối vào SoC AXI interconnect; AHB slave dùng để truy cập thanh ghi cấu hình, debug và test. pc_sel = 0 là PC mode, dùng AXI DMA để lấy cấu hình thanh ghi; pc_sel = 1 là slave mode, dùng AHB để đặt thanh ghi [TRM1 tr.1985, 1994] (Hình 2.1, Hình 2.5)
### Câu 3 (áp dụng)
Một model có các op Conv, Add, Concat, MaxPool và Resize chạy với RKNN_NPU_CORE_0_1_2. Theo UG152, op nào nằm trong danh sách nhanh hơn khi nhiều core và op nào về Core0?
Đáp án: Conv, Add, Concat nằm trong danh sách; MaxPool và Resize không có trong danh sách nên theo câu "Other type of op will fallback to Core0 to continue running" chúng chạy về Core0. Số đo thực tế xem Hình 10.3 [UG152 tr.27] (Hình 2.4)
### Câu 4 (áp dụng)
Driver nhận một job có core_mask = 0x0 khi ba core có task_num lần lượt 5, 3, 3. Driver chọn core nào và job chạy trên mấy core?
Đáp án: Core 1. Vòng lặp bắt đầu với core 0 (task_num 5), so sánh bằng "lớn hơn": core 1 có 3 nhỏ hơn 5 nên được chọn, core 2 có 3 không nhỏ hơn 3 nên giữ core 1 (hòa thì core số nhỏ). Job chạy trên 1 core [DRV rknpu_job.c:508-538] (Hình 2.4)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 2.1 | AXI master lấy dữ liệu từ bộ nhớ nối SoC AXI interconnect | T1 | TRM1 tr.1985 | The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect. |
| 2.1 | AHB slave truy cập thanh ghi cấu hình, debug, test | T1 | TRM1 tr.1985 | The AHB slave interface is used to access the registers for configuration, debug and test. |
| 2.1 | Khối tên RKNN trong TRM, ba core | T1 | TRM1 tr.1984 | Include triple NPU CORE |
| 2.1 | AHB slave trong hình TRM không vẽ nơi nối ra ngoài | T1 | TRM1 tr.1985 | (đọc từ hình) |
| 2.1 | Interconnect là cross-bar | T1 | TRM2 tr.16 | Cross-bar exchange network |
| 2.1 | Bốn DDR scheduler tích hợp, sắp xếp lại giao dịch | T1 | TRM2 tr.16 | Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency |
| 2.1 | Danh sách master của interconnect | T1 | TRM2 tr.16 | CPU GPU NPU VOP ISP Other Masters |
| 2.1 | NPU là một master; scheduler0 đến 3 nối DDRCTL0 đến 3 | T1 | TRM2 tr.16 | (đọc từ hình) |
| 2.1 | Nhãn hình gốc | T1 | TRM2 tr.16 | Fig. 1-1 Interconnect Diagram |
| 2.1 | Core 0: FDAB0000, 64KB | T1 | TRM1 tr.18 | RKNN C0 FDAB0000 64KB |
| 2.1 | Core 1: FDAC0000, 64KB | T1 | TRM1 tr.18 | RKNN C1 FDAC0000 64KB |
| 2.1 | Core 2: FDAD0000, 64KB | T1 | TRM1 tr.18 | RKNN C2 FDAD0000 64KB |
| 2.1 | Ngắt core 0: 142 | T1 | TRM1 tr.24 | 142 irq_rknn_c0 High level |
| 2.1 | Ngắt core 1: 143 | T1 | TRM1 tr.24 | 143 irq_rknn_c1 High level |
| 2.1 | Ngắt core 2: 144 | T1 | TRM1 tr.24 | 144 irq_rknn_c2 High level |
| 2.1 | Ba power domain của VD_NPU | T1 | TRM1 tr.1091 | Support multi power domains in VD_NPU: PD_NPUTOP, PD_NPU1, PD_NPU2 |
| 2.1 | Thành viên PD_NPUTOP: MCU_NPU, PVTM_NPU, PVTPLL_NPU, WDT_NPU, TIMER_NPU, RKNN_CORE0 | T1 | TRM1 tr.1093 | MCU_NPU PVTM_NPU PVTPLL_NPU WDT_NPU TIMER_NPU RKNN_CORE0 |
| 2.1 | Ranh giới domain: RKNN_CORE1 thuộc PD_NPU1, RKNN_CORE2 thuộc PD_NPU2 (hàng của Table 7-1) | T1 | TRM1 tr.1093 | (đọc từ hình) |
| 2.1 | MCU trong VD_NPU: 16KB cache, 64KB TCM | T1 | DS tr.8 | MCU in VD_NPU integrate 16KB Cache and 64KB TCM |
| 2.1 | SoC có 1MB SRAM, 956KB cấp cho các IP | T1 | SRAM dòng 3 | RK3588 SOC内部含有1MB的SRAM，其中有956KB可供给SOC上各个IP所使用 |
| 2.1 | NPU nhận tối đa 956KB, 4K align | T1 | SRAM dòng 21 | 最大可分配956KB，且大小需要4K对齐 |
| 2.1 | Dùng chung với IP khác (codec), vùng không chồng lấn | T1 | SRAM dòng 22 | 默认系统中可能已为其他IP分配SRAM，比如编解码模块，各IP分配的SRAM区域不能重叠 |
| 2.1 | IOMMU gán cho node rknpu | T1 | DTS dòng 3478 | iommus = <&rknpu_mmu>; |
| 2.1 | Vai trò MCU_NPU với một job NPU | T1 | (không có) | (unknown) |
| 2.1 | Đường nối NPU tới system SRAM | T1 | (không có) | (unknown) |
| 2.1 | Vị trí IOMMU trên đường dữ liệu | T1 | (không có) | (unknown) |
| 2.2 | Tên hình | T1 | TRM1 tr.1985 | Fig. 36-2 RKNN Single Core Architecture |
| 2.2 | Các khối và mũi tên của Fig. 36-2: CNA chứa bốn khối, AXI nối CNA, DPU, PPU, Register File Fetch; DPU nối PPU | T1 | TRM1 tr.1985 | (đọc từ hình) |
| 2.2 | Thứ tự dữ liệu 1 đến 7 (CNA, buffer, Sequence Controller, MAC, accumulator, DPU, PPU) | T1 | TRM1 tr.1985 | (đọc từ hình) |
| 2.2 | Buffer 384KB | T1 | TRM1 tr.1984 | 384KBx3 internal buffer |
| 2.2 | Chương 36.3.2 gọi khối là Neural Network Accelerating Engine | T1 | TRM1 tr.1985 | Neural Network Accelerating Engine |
| 2.2 | Engine gồm bộ tiền xử lý convolution, buffer, MAC array, accumulator | T1 | TRM1 tr.1985 | This unit include convolution pre-process controller, internal buffer, mac array, accumulator. |
| 2.2 | DPU xử lý hàm theo giá trị đơn | T1 | TRM1 tr.1985 | Data Processing Unit mainly process the single data calculate, such as leaky_relu, relu, relux, sigmoid, tanh |
| 2.2 | DPU còn có softmax, transpose, đổi định dạng | T1 | TRM1 tr.1985 | It also provides function: softmax, transpose, data format conversion |
| 2.2 | PPU: pooling trên đầu ra của DPU | T1 | TRM1 tr.1985 | Planar Processing Unit mainly provide planar function followed by output data from Data Processing Unit, such as average pooling, max pooling, min pooling |
| 2.2 | Register File Fetch lấy thanh ghi từ bộ nhớ ngoài qua AXI | T1 | TRM1 tr.1986 | Register File Fetch Unit fetch register configuration from external system memory through AXI |
| 2.2 | AHB slave dùng cho cấu hình | T1 | TRM1 tr.1985 | The AHB slave interface is used to access the registers for configuration, debug and test. |
| 2.2 | Zero-Skipping: tên thanh ghi fc_skip_en | T1 | TRM1 tr.2006 | fc_skip_en FC zero skipping enable |
| 2.2 | Zero-Skipping: feature bằng 0 thì weight không được fetch | T1 | TRM1 tr.2006 | When one pixel feature data is 0, the corresponding weight data is not fetched from system memory. |
| 2.2 | INT8: MAC array 32x32 | T1 | TRM1 tr.2001 | Int8 mac array 32x32 mode |
| 2.2 | weight_bank: tối đa bank 1-7 | T1 | TRM1 tr.2004 | 4'd7: Bank 1-7 occupied by weight data |
| 2.2 | weight_bank: bắt đầu từ bank 7 | T1 | TRM1 tr.2004 | 4'd1: Bank 7 occupied by weight data |
| 2.2 | data_bank: tối đa bank 0-6 | T1 | TRM1 tr.2004 | 4'd6: Bank 0-6 occupied by feature data |
| 2.2 | data_bank: bắt đầu từ bank 0 | T1 | TRM1 tr.2004 | 4'd0: Bank 0 occupied by feature data |
| 2.2 | Tên hai thanh ghi weight_bank, data_bank | T1 | TRM1 tr.2004 | Bank numbers for weight data. |
| 2.2 | Tên thanh ghi data_bank | T1 | TRM1 tr.2004 | Bank numbers for feature data. |
| 2.2 | Dải chỉ số bank 0 đến 7 suy ra từ hai trường trên | T1 | TRM1 tr.2004 | (số học) |
| 2.2 | Nhãn hình gốc | T1 | TRM1 tr.1985 | Fig. 36-2 RKNN Single Core Architecture |
| 2.2 | Khai triển tên CNA, BS, BN, CBUF | T1 | (không có) | (unknown) |
| 2.2 | Kích thước một bank | T1 | (không có) | (unknown) |
| 2.2 | MAC array có bỏ phép nhân 0 hay không | T1 | (không có) | (unknown) |
| 2.2 | Định dạng nén weight của Weight Decompress | T1 | (không có) | (unknown) |
| 2.3 | INT8: 1024x3 MAC mỗi chu kỳ | T1 | TRM1 tr.1984 | 1024x3 integer 8 MAC operations per cycle |
| 2.3 | INT16: 512x3 | T1 | TRM1 tr.1984 | 512x3 integer 16 MAC operations per cycle |
| 2.3 | FP16: 512x3 | T1 | TRM1 tr.1984 | 512x3 float 16 MAC operations per cycle |
| 2.3 | BF16: 512x3 | T1 | TRM1 tr.1984 | 512x3 bfloat 16 MAC operations per cycle |
| 2.3 | TF32: 256x3 | T1 | TRM1 tr.1984 | 256x3 tf32 MAC operation per cycle |
| 2.3 | INT4: 2048x3 | T1 | TRM1 tr.1984 | 2048x3 integer 4 MAC operation per cycle |
| 2.3 | Cột Tổng: 1024x3 = 3072, 512x3 = 1536, 256x3 = 768, 2048x3 = 6144 | tính | TRM1 tr.1984 | (số học) |
| 2.3 | x3 khớp với ba core | T1 | TRM1 tr.1984 | Include triple NPU CORE |
| 2.3 | quantized_dtype w8a8, mặc định, RK2118 không hỗ trợ | T1 | API232 tr.7 | The default value is w8a8. |
| 2.3 | w8a8: RK2118 không hỗ trợ | T1 | API232 tr.7 | (RK2118 not supported) |
| 2.3 | w4a16: chỉ RK3576/RV1126B | T1 | API232 tr.7 | the activation value is 16bit floating point accuracy. (Only RK3576/RV1126B supported) |
| 2.3 | w8a16: chỉ RK3562 | T1 | API232 tr.7 | (Only RK3562 supported) |
| 2.3 | w4a8: chưa hỗ trợ | T1 | API232 tr.7 | (Not supported yet) |
| 2.3 | w16a16i: chỉ RV1103/RV1106 | T1 | API232 tr.7 | (Only RV1103/RV1106 supported) |
| 2.3 | w16a16i_dfp: chỉ RV1103/RV1106 | T1 | API232 tr.7 | w16a16i_dfp: The weight is 16bit dynamic fixed-point quantitative accuracy |
| 2.3 | Với RK3588 chỉ w8a8 không bị giới hạn sang chip khác (suy luận từ danh sách trên) | T1 | API232 tr.7 | (số học) |
| 2.3 | Matmul C API hỗ trợ int4, int8, float16 | T1 | UG232 tr.41 | support int4, int8 and float16 three commonly used input data |
| 2.3 | INT8: nn_mode 3'd0 là MAC array 32x32 | T1 | TRM1 tr.2001 | 3'd0: Int8 mac array 32x32 mode; |
| 2.3 | Kernel group INT8 32, INT16 và FP16 là 16 | T1 | TRM1 tr.2000 | In int8, 32 kernels form 1 group, in int16 or fp16, 16 kernels form 1 group. |
| 2.3 | Buffer 384KB x3 (Datasheet) | T1 | DS tr.11 | Embedded 384KBx3 internal buffer |
| 2.3 | SRAM tối đa 956KB, 4K align | T1 | SRAM dòng 21 | 最大可分配956KB，且大小需要4K对齐 |
| 2.3 | Datasheet: Max NPU frequency là TBD | T1 | DS tr.31 | Max NPU frequency NA NA TBD MHz |
| 2.3 | Datasheet: sức tính up to 6TOPs | T1 | DS tr.7 | computing power is up to 6TOPs |
| 2.3 | Tên bảng OPP của RK3588 | T1 | DTS dòng 3533 | RK3588 npu OPPs |
| 2.3 | OPP 300 MHz | T1 | DTS dòng 3534-3655 | opp-hz = /bits/ 64 <300000000>; |
| 2.3 | OPP 400 MHz | T1 | DTS dòng 3534-3655 | opp-hz = /bits/ 64 <400000000>; |
| 2.3 | OPP 1000 MHz (cao nhất của bảng) | T1 | DTS dòng 3534-3655 | opp-hz = /bits/ 64 <1000000000>; |
| 2.3 | Tên bảng OPP RK3588J/M | T1 | DTS dòng 3657 | RK3588J/M npu OPPs |
| 2.3 | OPP cao nhất của RK3588J/M là 950 MHz | T1 | DTS dòng 3658-3709 | opp-hz = /bits/ 64 <950000000>; |
| 2.3 | Phép tính 1024 x 3 x 2 x 1 GHz = 6.144 TOPS | tính | TRM1 tr.1984 | (số học) |
| 2.3 | Quy ước TOPS bằng hai lần số MAC nhân tần số | T2 | BAMB tr.1 | defined as twice the number of MAC units multiplied by the clock frequency |
| 2.3 | Lệnh ví dụ đặt tần số 1 GHz (không phải tần số tối đa) | T1 | UG152 tr.73 | echo 1000000000 > /sys/kernel/debug/clk/clk_npu_dsu0/clk_rate |
| 2.3 | Board: eval_perf báo NPU Current Frequency List 1000000000 | T3 | LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt | NPU Current Frequency List: - 1000000000 |
| 2.3 | Board RK3588S (Orange Pi 5) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | Orange Pi 5 (RK3588S) |
| 2.3 | eval_perf với fix_freq=True | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md | eval_perf(fix_freq=True) |
| 2.3 | Quy ước đếm phép tính của vendor cho 6 TOPS | T1 | (không có) | (unknown) |
| 2.3 | Bố cục MAC array cho INT16, FP16, INT4 | T1 | (không có) | (unknown) |
| 2.3 | Kích thước một bank của buffer 384KB | T1 | (không có) | (unknown) |
| 2.4 | Ba chế độ phần cứng | T1 | TRM1 tr.1984 | Support triple core co-work, dual core co-work, and work independently |
| 2.4 | nn_mode là co-work mode; 3'd0 32x32, 3'd1 64x32, 3'd2 96x32; không gắn dual hay triple | T1 | TRM1 tr.2001 | co-work mode. 3'd0: Int8 mac array 32x32 mode; 3'd1: 64x32 mode; 3'd2: 96x32 mode; |
| 2.4 | nn_mode 3'd4 là 32x64 | T1 | TRM1 tr.2001 | 3'd4: 32x64 mode; |
| 2.4 | nn_mode 3'd5 là 32x96 | T1 | TRM1 tr.2001 | 3'd5: 32x96 mode; |
| 2.4 | CORE_AUTO chọn core rảnh | T1 | UG152 tr.26 | RKNN_NPU_CORE_AUTO : Referring to automatic mode, meaning that it will select the idle core inside the NPU; |
| 2.4 | CORE_0 chạy trên NPU0 | T1 | UG152 tr.26 | RKNN_NPU_CORE_0 : Running on the NPU0 core; |
| 2.4 | CORE_1 chạy trên NPU1 | T1 | UG152 tr.26 | RKNN_NPU_CORE_1: Runing on the NPU1 core; |
| 2.4 | CORE_2 chạy trên NPU2 | T1 | UG152 tr.26 | RKNN_NPU_CORE_2: Runing on the NPU2 core; |
| 2.4 | CORE_0_1 chạy cùng lúc NPU0 và NPU1 | T1 | UG152 tr.26 | RKNN_NPU_CORE_0_1: Running on both NPU0 and NPU1 core simultaneously; |
| 2.4 | CORE_0_1_2 chạy cùng lúc ba core | T1 | UG152 tr.26 | RKNN_NPU_CORE_0_1_2: Running on both NPU0, NPU1 and NPU2 simultaneously. |
| 2.4 | Chế độ nhiều core: danh sách op nhanh hơn | T1 | UG152 tr.27 | the following ops have better acceleration |
| 2.4 | Danh sách op | T1 | UG152 tr.27 | Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu. Prelu, LeakyRelu. |
| 2.4 | Op khác fallback về Core0 | T1 | UG152 tr.27 | Other type of op will fallback to Core0 to continue running. |
| 2.4 | Mã mask lõi AUTO 0x00 | T1 | DRV rknpu_job.h:24 | #define RKNPU_CORE_AUTO_MASK 0x00 |
| 2.4 | Mã mask lõi 0x01, 0x02, 0x04 | T1 | DRV rknpu_job.h:25-27 | #define RKNPU_CORE0_MASK 0x01 #define RKNPU_CORE1_MASK 0x02 #define RKNPU_CORE2_MASK 0x04 |
| 2.4 | Mask 0x3 là core 0 và core 1 | T1 | DRV rknpu_job.c:404-424 | case RKNPU_CORE0_MASK \| RKNPU_CORE1_MASK: |
| 2.4 | Mask 0x7 là cả ba core | T1 | DRV rknpu_job.c:404-424 | case RKNPU_CORE0_MASK \| RKNPU_CORE1_MASK \| RKNPU_CORE2_MASK: |
| 2.4 | Mask khác báo lỗi | T1 | DRV rknpu_job.c:404-424 | Unknown core mask: %d |
| 2.4 | AUTO chọn core có task_num nhỏ nhất | T1 | DRV rknpu_job.c:508-538 | if (task_num > rknpu_dev->subcore_datas[i].task_num) { |
| 2.4 | AUTO: job chạy trên một core | T1 | DRV rknpu_job.c:508-538 | job->use_core_num = 1; |
| 2.4 | Mỗi core có todo_list riêng | T1 | DRV rknpu_job.c:545-552 | list_add_tail(&job->head[i], &subcore_data->todo_list); |
| 2.4 | Commit khi run_count về 0 | T1 | DRV rknpu_job.c:456 | if (atomic_dec_and_test(&job->run_count)) |
| 2.4 | Xong khi interrupt_count về 0 | T1 | DRV rknpu_job.c:485 | if (atomic_dec_and_test(&job->interrupt_count)) { |
| 2.4 | subcore_task có task_start và task_number | T1 | DRV rknpu_ioctl.h:241-244 | __u32 task_start; __u32 task_number; |
| 2.4 | rknpu_submit có subcore_task[5] | T1 | DRV rknpu_ioctl.h:277-279 | struct rknpu_subcore_task subcore_task[5]; |
| 2.4 | 1 hoặc 2 core: lấy subcore_task[i] | T1 | DRV rknpu_job.c:71-90 | job->args->subcore_task[core_index].task_number; |
| 2.4 | 3 core: lấy subcore_task[i + 2] | T1 | DRV rknpu_job.c:71-90 | job->args->subcore_task[core_index + 2] .task_number; |
| 2.4 | Cách userspace chia việc giữa các core | T1 | (không có) | (unknown) |
| 2.4 | Vì sao op ngoài danh sách về Core0 | T1 | (không có) | (unknown) |
| 2.5 | Fig. 36-3: khởi tạo thông tin thanh ghi trong bộ nhớ | T1 | TRM1 tr.2053 | Initial register information in system memory |
| 2.5 | Fig. 36-3: ghi pc_interrupt_clear và pc_interrupt_mask | T1 | TRM1 tr.2053 | Write pc_interrupt_clear and pc_interrupt_mask |
| 2.5 | Fig. 36-3: ghi pc_amount, pc_addr, pc_task_number, pc_task_dma_base | T1 | TRM1 tr.2053 | Write pc_amount/pc_addr/pc_task_number/pc_task_dma_base |
| 2.5 | Fig. 36-3: ghi pc_op_enable để bắt đầu | T1 | TRM1 tr.2053 | Write pc_op_enable to start a group of tasks |
| 2.5 | Hai chế độ làm việc | T1 | TRM1 tr.2053 | RKNN has two types of work mode: slave configured mode and pc work mode |
| 2.5 | PC mode cần khởi tạo thông tin thanh ghi trong bộ nhớ | T1 | TRM1 tr.2053 | Pc work mode need to initial register information to the system memory |
| 2.5 | Nhãn Fig. 36-3 | T1 | TRM1 tr.2053 | Fig. 36-3 PC flow |
| 2.5 | Mỗi thanh ghi 64 bit | T1 | TRM1 tr.1994 | Each register takes 64 bits |
| 2.5 | Bit 63:48 là block đích | T1 | TRM1 tr.1994 | bit[63:48] indicates which block the register forward to. |
| 2.5 | Bit 47:16 là giá trị | T1 | TRM1 tr.1994 | bit[47:16] the register's value |
| 2.5 | Bit 15:0 là offset | T1 | TRM1 tr.1994 | bit[15: 0] the register's offset address in each block. |
| 2.5 | op_en đặt cuối danh sách | T1 | TRM1 tr.1994 | op_en is strongly recommended set at the end of register list. |
| 2.5 | Block đích: CNA, CORE, DPU, PPU | T1 | TRM1 tr.1994 | bit[57]= 1 CNA |
| 2.5 | pc_sel = 0: PC mode dùng AXI DMA | T1 | TRM1 tr.1994 | 1'd0: PC mode, use AXI DMA to fetch register config; |
| 2.5 | pc_sel = 1: slave mode dùng AHB | T1 | TRM1 tr.1994 | 1'd1: Slave mode, use AHB to set register. |
| 2.5 | Register File Fetch lấy cấu hình qua AXI | T1 | TRM1 tr.1986 | Register File Fetch Unit fetch register configuration from external system memory through AXI |
| 2.5 | Ping-pong: cấu hình group này khi dùng group kia | T1 | TRM1 tr.2052 | Configure the group 0 when use the group 1, and configure the group 1 when use group 0. |
| 2.5 | Ghi S_POINTER để bật ping-pong | T1 | TRM1 tr.2052 | Writing S_POINTER of every block can enable this function. |
| 2.5 | Ba tín hiệu ngắt, giữ đến khi host xóa | T1 | TRM1 tr.2053 | RKNN has 3 interrupt output signal and it remains asserted until the host processor clears the interrupt. |
| 2.5 | 17 sự kiện ngắt | T1 | TRM1 tr.2053 | one of the 17 possible events that the RKNN can signal to the host processor |
| 2.5 | Bit 0 đến 5: CNA feature, weight, csc, group 0 và 1 | T1 | TRM1 tr.1995 | mask[0 ]: CNA feature group 0 interrupt mask. |
| 2.5 | Bit 4, 5: CNA csc | T1 | TRM1 tr.1995 | mask[5 ]: CNA csc group 1; |
| 2.5 | Bit 6, 7: CORE group 0 và 1 | T1 | TRM1 tr.1995 | mask[6 ]: CORE group 0; |
| 2.5 | Bit 8, 9: DPU group 0 và 1 | T1 | TRM1 tr.1995 | mask[8 ]: DPU group 0; |
| 2.5 | Bit 10, 11: PPU group 0 và 1 | T1 | TRM1 tr.1995 | mask[10]: PPU group 0; |
| 2.5 | Bit 12: DMA read error | T1 | TRM1 tr.1995 | mask[12]: DMA read error; |
| 2.5 | Bit 13: DMA write error | T1 | TRM1 tr.1995 | mask[13]: DMA write error; |
| 2.5 | Thanh ghi xóa ngắt pc_interrupt_clear | T1 | TRM1 tr.1995 | RKNN_pc_interrupt_clear |
| 2.5 | Bit 14 đến 16 không được mô tả | T1 | (không có) | (unknown) |
| 2.5 | Thứ tự bước 1 đến 8 và giai đoạn 1 đến 4 của hình | T1 | TRM1 tr.2053 | (đọc từ hình) |
