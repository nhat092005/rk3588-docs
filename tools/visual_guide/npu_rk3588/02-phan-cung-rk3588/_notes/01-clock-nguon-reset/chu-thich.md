# Ghi chú chuyên đề: Clock, DVFS, nguồn điện, reset, IOMMU và MCU của NPU

## Câu hỏi mở đầu
Trước khi NPU chạy được một job, driver phải bật nguồn, bật clock, chọn tần số và gắn IOMMU theo thứ tự nào, và phần nào của chuỗi này TRM thật sự mô tả?

## Hình K.1 (hk-1-clock-dvfs) [T1 RK3588]
Tần số NPU được chọn qua các mux trong CRU, và bảng OPP ghép mỗi mức tần số với một mức điện áp: tần số càng cao thì điện áp càng cao. Mux `clk_rknn_dsu0_src_t` chọn một trong năm nguồn PLL rồi chia cho (div_con + 1). Sau đó `clk_rknn_dsu0` chọn giữa nguồn này và `clk_npu_pvtpll`. TRM nói RKNN có hai clock domain AHB và AXI, AXI clock cũng là core clock, và tần số do CRU điều khiển. DTS lại đặt clock `clk_npu` là `SCMI_CLK_NPU` với 200000000. TRM và DTS không nối hai cách gọi này với nhau. Trong nhóm "RK3588 npu OPPs", điện áp đầu là 700 mV từ 300 đến 700 MHz, rồi tăng lên 750, 800 và 850 mV ở 800, 900 và 1000 MHz. Governor `rknpu_ondemand` của driver chỉ trả `ondemand_freq` (đặt qua debugfs `rknpu/freq`) hoặc `previous_freq`, rồi `dev_pm_opp_set_rate` áp mức OPP tương ứng.
Đọc thêm: 02_ mục 2.6. Khái niệm: Hình 2.3, Hình 7.3

## Hình K.2 (hk-2-nguon-reset-iommu) [T1 RK3588]
VD_NPU có ba power domain, mỗi domain chứa một RKNN core: PD_NPUTOP chứa core 0 cùng MCU_NPU, PD_NPU1 chứa core 1, PD_NPU2 chứa core 2. Khi bật, driver bật regulator trước, rồi clock, rồi ba domain theo thứ tự npu0, npu1, npu2. Khi tắt, driver đi ngược lại, nhưng phải chờ IOMMU tắt hẳn rồi mới tắt các domain. TRM yêu cầu giữ Aresetn và Hresetn ít nhất 32 core clock cycles rồi nhả cùng lúc. Soft reset của driver assert cả 6 reset, chờ 10 µs, deassert, chờ 10 µs, rồi gắn lại domain IOMMU. Driver gọi soft reset khi job timeout, khi có ioctl RKNPU_ACT_RESET, hoặc khi ghi "1" vào debugfs. MCU_NPU là Cortex-M0 với TCM 64KB và cache 16KB; vai trò của nó với một job là unknown. Mã driver không có chữ mailbox hay mcu, và driver giao job bằng thanh ghi PC của core.
Đọc thêm: 02_ mục 2.1, 2.6, 2.7. Khái niệm: Hình 2.1, Hình 2.5, Hình 5.3

## Hiểu sai thường gặp
- "TRM cho biết NPU chạy ở bao nhiêu MHz" -> chương RKNN chỉ nói tần số do CRU điều khiển; các mức tần số và điện áp nằm trong `npu_opp_table` của DTS [TRM1 tr.2052; DTS dòng 3536-3537] (Hình K.1)
- "rknpu_ondemand tự tăng giảm tần số theo tải như ondemand của CPU" -> hàm governor chỉ trả `ondemand_freq` hoặc `previous_freq` [DRV rknpu_devfreq.c:54-61] (Hình K.1)
- "Thứ tự bật tắt nguồn NPU là quy định của TRM" -> thứ tự trong hình là của driver; TRM chỉ nói PMU bật tắt domain bằng phần mềm hoặc phần cứng [DRV rknpu_drv.c:904-1060; TRM1 tr.1091] (Hình K.2)
- "MCU_NPU điều khiển job của NPU" -> không nguồn nào nói vậy; driver ghi job vào thanh ghi PC của core [DRV rknpu_job.c:346, 371] (Hình K.2)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao rknpu_power_off phải chờ IOMMU tắt rồi mới tắt các power domain?
Đáp án: Runtime suspend của IOMMU chạy bất đồng bộ và có truy cập thanh ghi; nếu PD, VD hoặc CLK đã tắt thì truy cập đó làm crash, nên driver chờ IOMMU tắt rồi mới tắt PD [DRV rknpu_drv.c:1025-1031] (Hình K.2)

### Câu 2 (phân biệt)
Phân biệt yêu cầu reset của TRM với soft reset của driver.
Đáp án: TRM yêu cầu giữ Aresetn (AXI và các core) và Hresetn (AHB) ít nhất 32 core clock cycles theo clock chậm hơn, rồi nhả cùng lúc. Driver assert mọi reset trong DTS, chờ udelay(10), deassert, chờ udelay(10), rồi detach và attach lại IOMMU [TRM1 tr.2052; DRV rknpu_reset.c:125-146] (Hình K.2)

### Câu 3 (áp dụng)
Theo nhóm "RK3588 npu OPPs", chạy NPU ở 1000 MHz thay vì 700 MHz thì điện áp đầu đổi thế nào?
Đáp án: Từ 700 mV lên 850 mV (opp-microvolt 700000 và 850000) [DTS dòng 3600-3601, 3642-3643] (Hình K.1)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| K.1 | Mux clk_rknn_dsu0_src_t | T1 | TRM1 tr.82 | clk_rknn_dsu0_src_t clock mux. |
| K.1 | Năm nguồn của mux (ví dụ NPLL là 3'b011) | T1 | TRM1 tr.82 | 3'b011: clk_npll_mux |
| K.1 | Nguồn GPLL | T1 | TRM1 tr.82 | 3'b000: clk_gpll_mux |
| K.1 | Nguồn SPLL | T1 | TRM1 tr.82 | 3'b100: clk_spll_mux |
| K.1 | Bộ chia (div_con + 1) | T1 | TRM1 tr.82 | Divide clk_rknn_dsu0_src_t by (div_con + 1). |
| K.1 | Bit chọn của mux src_t là 9:7 trong CRU_CLKSEL_CON73 | T1 | TRM1 tr.82 | CRU_CLKSEL_CON73 |
| K.1 | Mux hclk_rknn_root: 200m, 100m, 50m, osc0 | T1 | TRM1 tr.82 | hclk_rknn_root clock mux. |
| K.1 | hclk_rknn_root có nguồn 50m | T1 | TRM1 tr.82 | 2'b10: clk_matrix_50m_src |
| K.1 | Mux clk_npu_pvtpll | T1 | TRM1 tr.83 | clk_npu_pvtpll clock mux. |
| K.1 | Mux clk_rknn_dsu0 chọn src_t hoặc clk_npu_pvtpll | T1 | TRM1 tr.83 | clk_rknn_dsu0 clock mux. |
| K.1 | clk_rknn_dsu0 chọn 1 là clk_npu_pvtpll | T1 | TRM1 tr.83 | 1'b1: clk_npu_pvtpll |
| K.1 | Hai clock domain AHB và AXI | T1 | TRM1 tr.2052 | RKNN has two clock domains, one is AHB clock, the other is AXI clock |
| K.1 | AXI clock cũng là core clock | T1 | TRM1 tr.2052 | also used for core clock for every Calculate Core and Control Core |
| K.1 | Tần số do CRU điều khiển | T1 | TRM1 tr.2052 | Clock frequency can be controlled by CRU |
| K.1 | Gần như mọi flip-flop được gate | T1 | TRM1 tr.2052 | Almost all of the flip-flops are clock gated in the design |
| K.1 | Block rảnh thì tự gate, phần mềm tắt được | T1 | TRM1 tr.2052 | then the clock of that block will be gated automatically. This feature can be disabled by software |
| K.1 | DTS: clock đầu là SCMI_CLK_NPU | T1 | DTS dòng 3459 | clocks = <&scmi_clk SCMI_CLK_NPU>, <&cru ACLK_NPU0>, |
| K.1 | DTS: tên clock đầu là clk_npu | T1 | DTS dòng 3463 | clock-names = "clk_npu", "aclk0", |
| K.1 | DTS: assigned-clock-rates 200000000 | T1 | DTS dòng 3468 | assigned-clock-rates = <200000000>; |
| K.1 | Ánh xạ SCMI_CLK_NPU sang mux CRU, và clk_rknn_dsu0 có phải core clock: không có trong TRM, DTS | T1 | TRM1 tr.2052 | (unknown) |
| K.1 | Nhóm "RK3588 npu OPPs" | T1 | DTS dòng 3533 | /* RK3588 npu OPPs */ |
| K.1 | 300 MHz, 700 mV | T1 | DTS dòng 3536-3537 | opp-hz = /bits/ 64 <300000000>; opp-microvolt = <700000 |
| K.1 | 400 MHz, 700 mV | T1 | DTS dòng 3552-3553 | opp-hz = /bits/ 64 <400000000>; opp-microvolt = <700000 |
| K.1 | 500 MHz, 700 mV | T1 | DTS dòng 3568-3569 | opp-hz = /bits/ 64 <500000000>; opp-microvolt = <700000 |
| K.1 | 600 MHz, 700 mV | T1 | DTS dòng 3584-3585 | opp-hz = /bits/ 64 <600000000>; opp-microvolt = <700000 |
| K.1 | 700 MHz, 700 mV | T1 | DTS dòng 3600-3601 | opp-hz = /bits/ 64 <700000000>; opp-microvolt = <700000 |
| K.1 | 800 MHz, 750 mV | T1 | DTS dòng 3612-3613 | opp-hz = /bits/ 64 <800000000>; opp-microvolt = <750000 |
| K.1 | 900 MHz, 800 mV | T1 | DTS dòng 3626-3627 | opp-hz = /bits/ 64 <900000000>; opp-microvolt = <800000 |
| K.1 | 1000 MHz, 850 mV | T1 | DTS dòng 3642-3643 | opp-hz = /bits/ 64 <1000000000>; opp-microvolt = <850000 |
| K.1 | mV = µV / 1000 | T1 | DTS dòng 3537 | (số học) |
| K.1 | init-freq 1000000 KHz | T1 | DTS dòng 3525 | rockchip,init-freq = <1000000>; /* KHz */ |
| K.1 | high-temp 85000 | T1 | DTS dòng 3530 | rockchip,high-temp = <85000>; |
| K.1 | high-temp-max-freq 800000 | T1 | DTS dòng 3531 | rockchip,high-temp-max-freq = <800000>; |
| K.1 | RK3588J/M có nhóm OPP riêng | T1 | DTS dòng 3657 | /* RK3588J/M npu OPPs */ |
| K.1 | DS mục NPU: một voltage domain riêng cho DVFS | T1 | DS tr.11 | One isolated voltage domain to support DVFS |
| K.1 | Governor tên rknpu_ondemand | T1 | DRV rknpu_devfreq.c:73 | .name = "rknpu_ondemand", |
| K.1 | Governor trả ondemand_freq nếu đã đặt | T1 | DRV rknpu_devfreq.c:54-61 | *freq = rknpu_dev->ondemand_freq; |
| K.1 | Ngược lại trả previous_freq | T1 | DRV rknpu_devfreq.c:54-61 | *freq = df->previous_freq; |
| K.1 | npu_devfreq_target gọi dev_pm_opp_set_rate | T1 | DRV rknpu_devfreq.c:281-307 | ret = dev_pm_opp_set_rate(dev, *freq); |
| K.1 | Bảng OPP nạp theo clock clk_npu | T1 | DRV rknpu_devfreq.c:337 | rockchip_init_opp_table(dev, info, "clk_npu", "rknpu"); |
| K.1 | debugfs freq ghi ondemand_freq | T1 | DRV rknpu_debugger.c:229 | rknpu_dev->ondemand_freq = freq; |
| K.1 | Node debugfs "freq" dùng rknpu_freq_set | T1 | DRV rknpu_debugger.c:308 | { "freq", rknpu_freq_show, rknpu_freq_set, NULL }, |
| K.1 | UG232 có mục đặt tần số NPU | T1 | UG232 tr.136 | Querying and setting CPU, DDR, and NPU frequencies |
| K.1 | Tần số thực khi chạy model của dự án: chưa đo | T3 | REPO docs/tools/visual_guide/README.md | (unknown) |
| K.2 | VD_NPU có ba power domain | T1 | TRM1 tr.1091 | Support multi power domains in VD_NPU: PD_NPUTOP, PD_NPU1, PD_NPU2 |
| K.2 | PMU bật tắt mọi power domain bằng phần mềm hoặc phần cứng | T1 | TRM1 tr.1091 | Support power down/up all power domains by software or hardware |
| K.2 | Table 7-1: PD_NPUTOP có BIU_NPUTOP, MCU_NPU, PVTM_NPU | T1 | TRM1 tr.1093 | BIU_NPUTOP MCU_NPU PVTM_NPU |
| K.2 | Table 7-1: TIMER_NPU, RKNN_CORE0 | T1 | TRM1 tr.1093 | TIMER_NPU RKNN_CORE0 |
| K.2 | Table 7-1: PD_NPU1 có BIU_NPU1, RKNN_CORE1 | T1 | TRM1 tr.1093 | BIU_NPU1 PD_NPU1 RKNN_CORE1 |
| K.2 | Table 7-1: PD_NPU2 có BIU_NPU2, RKNN_CORE2 | T1 | TRM1 tr.1093 | BIU_NPU2 PD_NPU2 RKNN_CORE2 |
| K.2 | Phân nhóm thành phần theo từng PD đọc theo vị trí dòng của Table 7-1 | T1 | TRM1 tr.1093 | (đọc từ hình) |
| K.2 | DTS: power-domains NPUTOP, NPU1, NPU2 tên npu0, npu1, npu2 | T1 | DTS dòng 3473-3476 | power-domains = <&power RK3588_PD_NPUTOP>, |
| K.2 | DTS: tên domain | T1 | DTS dòng 3476 | power-domain-names = "npu0", "npu1", "npu2"; |
| K.2 | Bật 1: regulator vdd | T1 | DRV rknpu_drv.c:911 | ret = regulator_enable(rknpu_dev->vdd); |
| K.2 | Bật 1: regulator mem nếu có | T1 | DRV rknpu_drv.c:922 | ret = regulator_enable(rknpu_dev->mem); |
| K.2 | Bật 2: mọi clock | T1 | DRV rknpu_drv.c:933 | ret = clk_bulk_prepare_enable(rknpu_dev->num_clks, rknpu_dev->clks); |
| K.2 | Bật 3: domain npu0 | T1 | DRV rknpu_drv.c:950 | pm_runtime_get_sync(rknpu_dev->genpd_dev_npu0); |
| K.2 | Bật 3: domain npu1 | T1 | DRV rknpu_drv.c:965 | pm_runtime_get_sync(rknpu_dev->genpd_dev_npu1); |
| K.2 | Bật 3: domain npu2 | T1 | DRV rknpu_drv.c:980 | pm_runtime_get_sync(rknpu_dev->genpd_dev_npu2); |
| K.2 | Bật 4: thiết bị | T1 | DRV rknpu_drv.c:991 | ret = pm_runtime_get_sync(dev); |
| K.2 | Tắt 1: thiết bị | T1 | DRV rknpu_drv.c:1020 | pm_runtime_put_sync(dev); |
| K.2 | Lý do chờ IOMMU: suspend bất đồng bộ | T1 | DRV rknpu_drv.c:1025-1031 | Because IOMMU's runtime suspend callback is asynchronous, |
| K.2 | Truy cập thanh ghi khi PD/VD/CLK tắt sẽ crash | T1 | DRV rknpu_drv.c:1025-1031 | If the PD/VD/CLK is closed, the register access will crash. |
| K.2 | Chỉ tắt PD sau khi IOMMU tắt | T1 | DRV rknpu_drv.c:1025-1031 | it's safe to close pd stuff until iommu disabled |
| K.2 | Tắt 2: chờ IOMMU bằng readx_poll_timeout | T1 | DRV rknpu_drv.c:1033 | ret = readx_poll_timeout(rockchip_iommu_is_enabled, dev, val, |
| K.2 | Tắt 3: npu2, npu1, npu0 | T1 | DRV rknpu_drv.c:1046-1051 | pm_runtime_put_sync(rknpu_dev->genpd_dev_npu2); |
| K.2 | Tắt 3: npu0 sau cùng | T1 | DRV rknpu_drv.c:1051 | pm_runtime_put_sync(rknpu_dev->genpd_dev_npu0); |
| K.2 | Tắt 4: clock | T1 | DRV rknpu_drv.c:1058 | clk_bulk_disable_unprepare(rknpu_dev->num_clks, rknpu_dev->clks); |
| K.2 | Hai tín hiệu reset: Aresetn | T1 | TRM1 tr.2052 | Aresetn, the reset signal for AXI interface and every Calculate Core and Control Core |
| K.2 | Hresetn | T1 | TRM1 tr.2052 | Hresetn is the AHB interface reset pin and which is synchronized to the AHB clock domain |
| K.2 | Giữ ít nhất 32 core clock cycles theo clock chậm hơn | T1 | TRM1 tr.2052 | must be asserted for a minimum of 32 core clock cycles, using the slowest of the two clocks |
| K.2 | Nhả cả hai cùng lúc | T1 | TRM1 tr.2052 | Then two signals must be release at the same time |
| K.2 | DTS: 6 reset SRST_A_RKNN0..2, SRST_H_RKNN0..2 | T1 | DTS dòng 3469-3470 | resets = <&cru SRST_A_RKNN0>, <&cru SRST_A_RKNN1>, <&cru SRST_A_RKNN2>, <&cru SRST_H_RKNN0> |
| K.2 | DTS: tên reset srst_a0..2, srst_h0..2 | T1 | DTS dòng 3471-3472 | reset-names = "srst_a0", "srst_a1", "srst_a2", "srst_h0", "srst_h1", "srst_h2"; |
| K.2 | Soft reset 1: assert mọi reset | T1 | DRV rknpu_reset.c:125 | ret \|= rknpu_reset_assert(rknpu_dev->srsts[i]); |
| K.2 | Soft reset 2 và 4: udelay(10) | T1 | DRV rknpu_reset.c:127 | udelay(10); |
| K.2 | Soft reset 3: deassert | T1 | DRV rknpu_reset.c:130 | ret \|= rknpu_reset_deassert(rknpu_dev->srsts[i]); |
| K.2 | Soft reset 5: gắn lại IOMMU | T1 | DRV rknpu_reset.c:145-146 | iommu_detach_device(domain, rknpu_dev->dev); iommu_attach_device(domain, rknpu_dev->dev); |
| K.2 | Gọi khi job timeout | T1 | DRV rknpu_job.c:584-604 | LOG_ERROR("job timeout, flags: %#x:\n", job->flags); |
| K.2 | Gọi khi job timeout (nhánh kiểm theo thời gian) | T1 | DRV rknpu_job.c:711-714 | job->args->timeout) { rknpu_soft_reset(rknpu_dev); |
| K.2 | Gọi qua ioctl RKNPU_ACT_RESET | T1 | DRV rknpu_drv.c:420-421 | case RKNPU_ACT_RESET: ret = rknpu_soft_reset(rknpu_dev); |
| K.2 | Gọi khi ghi "1" vào debugfs reset | T1 | DRV rknpu_debugger.c:293-295 | if (strcmp(buf, "1") == 0 && |
| K.2 | Node debugfs "reset" | T1 | DRV rknpu_debugger.c:312 | { "reset", rknpu_reset_show, rknpu_reset_set, NULL }, |
| K.2 | DTS: node rknpu có iommus | T1 | DTS dòng 3478 | iommus = <&rknpu_mmu>; |
| K.2 | DTS: rknpu_mmu là iommu-v2 tại fdab9000 | T1 | DTS dòng 3712-3713 | rknpu_mmu: iommu@fdab9000 { compatible = "rockchip,iommu-v2"; |
| K.2 | DTS: 4 cửa sổ thanh ghi | T1 | DTS dòng 3714-3717 | reg = <0x0 0xfdab9000 0x0 0x100>, |
| K.2 | DTS: 3 ngắt npu0_mmu, npu1_mmu, npu2_mmu | T1 | DTS dòng 3721 | interrupt-names = "npu0_mmu", "npu1_mmu", "npu2_mmu"; |
| K.2 | DTS: rknpu_mmu status disabled trong dtsi | T1 | DTS dòng 3727 | status = "disabled"; |
| K.2 | Driver đọc thuộc tính iommus | T1 | DRV rknpu_drv.c:798 | iommu = of_parse_phandle(dev->of_node, "iommus", 0); |
| K.2 | Driver đặt iommu_en | T1 | DRV rknpu_drv.c:1294 | rknpu_dev->iommu_en = rknpu_is_iommu_enable(dev); |
| K.2 | GEM lấy domain IOMMU | T1 | DRV rknpu_gem.c:504 | domain = iommu_get_domain_for_dev(rknpu_dev->dev); |
| K.2 | GEM gọi iommu_map với IOVA | T1 | DRV rknpu_gem.c:549 | ret = iommu_map(domain, rknpu_obj->iova_start, |
| K.2 | MCU subsystem là Cortex-M0 | T1 | TRM1 tr.1276 | one MCU processor(Cortex-M0,r0p0-03rel0) |
| K.2 | NPU_M0: TCM 64KB | T1 | TRM1 tr.1276 | TCM 16KB 64KB 32KB |
| K.2 | NPU_M0: cache 16KB | T1 | TRM1 tr.1276 | CACHE 16KB 16KB NA |
| K.2 | NPU_M0: IRQ_NUM 16 | T1 | TRM1 tr.1276 | IRQ_NUM 32 16 8 |
| K.2 | DS: MCU trong VD_NPU có 16KB cache, 64KB TCM | T1 | DS tr.8 | MCU in VD_NPU integrate 16KB Cache and 64KB TCM |
| K.2 | Mailbox2 gắn với MCU_NPU | T1 | TRM1 tr.19 | MAILBOX2(MCU_NPU) |
| K.2 | Driver giao job: ghi địa chỉ lệnh vào thanh ghi PC | T1 | DRV rknpu_job.c:346 | REG_WRITE(first_task->regcmd_addr, RKNPU_OFFSET_PC_DATA_ADDR); |
| K.2 | Driver giao job: bật PC_OP_EN | T1 | DRV rknpu_job.c:371 | REG_WRITE(0x1, RKNPU_OFFSET_PC_OP_EN); |
| K.2 | Mã driver không có chữ mailbox hay mcu (grep -ric mọi file .c, .h) | T1 | DRV rknpu_drv.c:1 | (unknown) |
| K.2 | Vai trò MCU_NPU với job NPU: TRM, DS, UG232, driver không nêu | T1 | TRM1 tr.1276 | (unknown) |
| K.2 | Ánh xạ tên reset DTS sang tên CRU trong TRM; trình tự bật VD/PD do phần cứng yêu cầu | T1 | TRM1 tr.1091 | (unknown) |
