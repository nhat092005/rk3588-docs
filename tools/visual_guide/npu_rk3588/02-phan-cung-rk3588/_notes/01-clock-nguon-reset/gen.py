#!/usr/bin/env python3
"""Ghi chu chuyen de 01-clock-nguon-reset (Phan 2): Hinh K.1, K.2 (tier T1 RK3588).

K.1 hk-1-clock-dvfs: mux clock cua RKNN trong CRU (TRM1 tr.82, 83), clock domain va clock gating (TRM1 tr.2052),
    cap tan so - dien ap cua npu_opp_table (DTS dong 3482-3657), governor rknpu_ondemand (DRV rknpu_devfreq.c).
K.2 hk-2-nguon-reset-iommu: VD_NPU va ba power domain (TRM1 tr.1091, 1093), thu tu bat tat trong driver
    (DRV rknpu_drv.c:904-1060), reset (TRM1 tr.2052, DTS, DRV rknpu_reset.c), IOMMU (DTS, DRV), MCU_NPU
    (TRM1 tr.19, 1276; DS tr.8).
Dien ap trong K.1 la gia tri dau cua opp-microvolt cho nhom "RK3588 npu OPPs" (khong phai nhom RK3588J/M).

Chay: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"
MUX = "#FFF8E1"


def tier(f):
    f.tier(800, 8, "T1 RK3588")


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{dash}/>')


def label(f, x, y, w, h, ls, size=12, fill="white", stroke="#333333", dashed=False, weight=400, mono=False):
    rect(f, x, y, w, h, fill, stroke, dashed=dashed)
    top = y + h / 2 - (len(ls) - 1) * (size + 3) / 2
    for i, ln in enumerate(ls):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", mono=mono)


def mux(f, x, y, h, name):
    """Trapezoid mux symbol, inputs on the left."""
    f.a(f'<path d="M{x} {y} L{x + 26} {y + 12} L{x + 26} {y + h - 12} L{x} {y + h} Z" fill="{MUX}" '
        f'stroke="#333333" stroke-width="1.2"/>')
    f.text(x + 13, y + h + 9, name, size=10.5, anchor="middle", fill=DARK)


def head(f, y, s):
    f.text(10, y, s, size=14, weight=700)


# ---------------------------------------------------------------------------------------------------------------
def fig_k1():
    f = Fig(W, 900)
    tier(f)
    f.text(10, 20, "Clock của NPU: mux trong CRU, cặp tần số - điện áp (DVFS) và governor của driver", size=16.5, weight=700)

    # ---- A. mux tree ----
    head(f, 50, "A. Các mux clock của RKNN trong CRU (TRM1 tr.82, 83)")
    plls = ["clk_gpll_mux", "clk_cpll_mux", "clk_aupll_mux", "clk_npll_mux", "clk_spll_mux"]
    for i, p in enumerate(plls):
        y = 78 + i * 24
        f.text(20, y, f"3'b{i:03b}", size=10.5, mono=True, fill=DARK)
        f.text(70, y, p, size=11.5, mono=True)
        f.line([(180, y), (220, y)], INK, THIN, head=False)
    mux(f, 220, 68, 116, "CLKSEL_CON73[9:7]")
    f.line([(246, 126), (266, 126)], INK, THIN)
    label(f, 266, 110, 92, 32, ["÷ (div_con + 1)"], size=11, fill="white")
    f.line([(358, 126), (390, 126)], INK, THIN, head=False)
    f.text(374, 116, "src_t", size=10, mono=True, anchor="middle", fill=DARK)
    # pvtpll mux
    mux(f, 420, 168, 60, "clk_npu_pvtpll_sel")
    f.line([(374, 126), (374, 186), (420, 186)], INK, THIN)
    f.text(410, 179, "0", size=10, mono=True, fill=DARK)
    f.line([(330, 212), (420, 212)], INK, THIN)
    f.text(325, 212, "xin_osc0_func", size=10.5, mono=True, anchor="end")
    f.text(410, 205, "1", size=10, mono=True, fill=DARK)
    f.text(452, 188, "clk_npu_pvtpll", size=10.5, mono=True)
    # dsu0 mux
    mux(f, 560, 96, 60, "clk_rknn_dsu0_sel")
    f.line([(390, 126), (390, 112), (560, 112)], INK, THIN)
    f.text(548, 104, "0", size=10, mono=True, fill=DARK)
    f.line([(446, 198), (530, 198), (530, 140), (560, 140)], INK, THIN)
    f.text(548, 132, "1", size=10, mono=True, fill=DARK)
    f.line([(586, 126), (630, 126)], INK, THIN)
    f.text(636, 126, "clk_rknn_dsu0", size=12, weight=700, mono=True)
    # hclk
    mux(f, 640, 168, 60, "hclk_rknn_root_sel")
    for i, s in enumerate(["200m", "100m", "50m", "osc0"]):
        f.text(632, 176 + i * 14, s, size=9.5, mono=True, anchor="end", fill=DARK)
    f.line([(666, 200), (700, 200)], INK, THIN)
    f.text(706, 200, "hclk_rknn_root", size=12, weight=700, mono=True)

    rect(f, 10, 250, 880, 92, fill="white", stroke="#999999", rx=5)
    txt(f, 22, 266, [
        [("Clock domain (TRM1 tr.2052): ", "b"), ("RKNN có hai clock domain, AHB clock cho giao tiếp AHB và AXI clock cho giao tiếp AXI;", "t")],
        [("AXI clock cũng là core clock của mọi Calculate Core và Control Core. Tần số do CRU điều khiển.", "t")],
        [("Clock gating: ", "b"), ("gần như mọi flip-flop đều được gate; block rảnh cùng giao tiếp thì tự gate clock, phần mềm tắt được.", "t")],
        [("Mặc định (DTS dòng 3459-3468): ", "b"), ("clock \"clk_npu\" là ", "t"), ("SCMI_CLK_NPU", "c"), (", assigned-clock-rates = 200000000.", "t")],
    ], size=12, dy=18)
    f.unknown(10, 350, ["clk_rknn_dsu0 có phải AXI hay core clock không, và SCMI_CLK_NPU (firmware) ứng với mux nào của CRU:",
                        "TRM và DTS không nối hai tên này với nhau."], w=880, size=12)

    # ---- B. OPP ----
    head(f, 412, "B. DVFS: cặp tần số - điện áp trong npu_opp_table, nhóm \"RK3588 npu OPPs\" (DTS dòng 3533-3657)")
    opps = [(300, 700), (400, 700), (500, 700), (600, 700), (700, 700), (800, 750), (900, 800), (1000, 850)]
    gx, gy, gw, gh = 90, 440, 500, 190
    rect(f, gx, gy, gw, gh, fill="white", stroke="#BBBBBB", sw=0.8, rx=0)
    vmin, vmax = 650, 875
    def py(v):
        return gy + gh - (v - vmin) / (vmax - vmin) * gh
    for v in (700, 750, 800, 850):
        f.a(f'<path d="M{gx} {py(v)} L{gx + gw} {py(v)}" stroke="#EEEEEE" stroke-width="0.8"/>')
        f.text(gx - 8, py(v), f"{v}", size=11, anchor="end", fill=DARK)
    f.text(gx - 60, gy + gh / 2, "mV", size=11.5, fill=DARK)
    bw = gw / len(opps)
    for i, (mhz, mv) in enumerate(opps):
        x = gx + i * bw + 8
        rect(f, x, py(mv), bw - 16, gy + gh - py(mv), fill="#C5D9F5" if mhz < 800 else BLUE, stroke=BLUE, sw=0.8, rx=1)
        f.text(x + (bw - 16) / 2, py(mv) - 9, f"{mv}", size=10.5, anchor="middle")
        f.text(x + (bw - 16) / 2, gy + gh + 14, f"{mhz}", size=11, anchor="middle")
    f.text(gx + gw / 2, gy + gh + 32, "opp-hz (MHz); cột là giá trị đầu của opp-microvolt (µV / 1000)", size=11.5,
           anchor="middle", fill=DARK)
    rect(f, 610, 440, 280, 190, fill="white", stroke="#999999", rx=5)
    txt(f, 622, 458, [
        [("DS tr.11 (mục NPU): ", "b")],
        [("\"One isolated voltage domain to", "t")],
        [("support DVFS\".", "t")],
        [("Tham số khác của bảng:", "b")],
        [("rockchip,init-freq", "c"), (" = 1000000 (KHz)", "t")],
        [("rockchip,high-temp", "c"), (" = 85000", "t")],
        [("rockchip,high-temp-max-freq", "c")],
        [("  = 800000", "t")],
        [("RK3588J/M có nhóm OPP riêng.", "t")],
        [("Bảng OPP đầy đủ: Hình 2.3.", "t")],
    ], size=11.5, dy=17)

    # ---- C. governor ----
    head(f, 692, "C. Driver: governor rknpu_ondemand và đường đổi tần số (DRV rknpu_devfreq.c, rknpu_debugger.c)")
    steps = [("debugfs rknpu/freq", "rknpu_freq_set ghi", "ondemand_freq"),
             ("governor", "rknpu_ondemand trả", "ondemand_freq hoặc previous_freq"),
             ("npu_devfreq_target", "gọi", "dev_pm_opp_set_rate"),
             ("OPP", "đặt tần số và", "điện áp theo bảng B")]
    for i, (t, a, b) in enumerate(steps):
        x = 10 + i * 222
        label(f, x, 708, 200, 58, [t, a, b], size=11.5, fill=CALC if i == 1 else "white", stroke=BLUE)
        if i < 3:
            f.line([(x + 200, 737), (x + 222, 737)], BLUE, THIN)
    txt(f, 10, 786, [
        [("Hàm governor (dòng 54-61) chỉ trả ", "t"), ("ondemand_freq", "c"), (" nếu đã đặt, ngược lại trả ", "t"), ("previous_freq", "c"),
         ("; trong hàm này không có phép đo tải.", "t")],
        [("UG232 tr.136 có mục \"Querying and setting CPU, DDR, and NPU frequencies\" (Hình 7.3).", "t")],
    ], size=12, dy=18)
    f.unknown(10, 826, "Tần số thực khi chạy model trên board của dự án: chưa đo trong ghi chú này.", w=880, size=12)
    source(f, 856, "Nguồn: TRM1 tr.82, 83, 2052; DS tr.11; DTS dòng 3459-3657; DRV rknpu_devfreq.c, rknpu_debugger.c; UG232 tr.136.")
    return f


# ---------------------------------------------------------------------------------------------------------------
def fig_k2():
    f = Fig(W, 980)
    tier(f)
    f.text(10, 20, "Nguồn điện, reset, IOMMU và MCU đi kèm NPU", size=17, weight=700)

    # ---- A. power domains + driver order ----
    head(f, 50, "A. VD_NPU gồm ba power domain (TRM1 tr.1091, Table 7-1 tr.1093) và thứ tự bật tắt của driver")
    rect(f, 10, 64, 330, 236, fill="white", stroke="#333333", dashed=True, rx=6)
    f.text(22, 80, "VD_NPU", size=13, weight=700)
    doms = [("PD_NPUTOP  (DTS: npu0)", ["RKNN_CORE0, MCU_NPU, BIU_NPUTOP,", "PVTM_NPU, PVTPLL_NPU, WDT_NPU, TIMER_NPU"]),
            ("PD_NPU1  (DTS: npu1)", ["RKNN_CORE1, BIU_NPU1"]),
            ("PD_NPU2  (DTS: npu2)", ["RKNN_CORE2, BIU_NPU2"])]
    y = 92
    for name, items in doms:
        h = 26 + 15 * len(items)
        rect(f, 22, y, 306, h, fill="#F5F5F5", stroke="#666666", dashed=True, rx=4)
        f.text(32, y + 13, name, size=12, weight=700)
        txt(f, 32, y + 30, [[(s, "t")] for s in items], size=11, dy=15)
        y += h + 8

    f.text(360, 80, "Bật (rknpu_power_on, DRV rknpu_drv.c)", size=12.5, weight=700, fill=BLUE)
    on = ["regulator_enable(vdd), rồi mem nếu có", "clk_bulk_prepare_enable (mọi clock)",
          "pm_runtime_get_sync: npu0, npu1, npu2", "pm_runtime_get_sync(dev)"]
    for i, s in enumerate(on):
        f.badge(372, 102 + i * 24, str(i + 1), BLUE)
        f.text(390, 102 + i * 24, s, size=12)
    f.text(360, 206, "Tắt (rknpu_power_off)", size=12.5, weight=700, fill=RED)
    off = ["pm_runtime_put_sync(dev)", "chờ IOMMU tắt (readx_poll_timeout)",
           "pm_runtime_put_sync: npu2, npu1, npu0", "clk_bulk_disable_unprepare"]
    for i, s in enumerate(off):
        f.badge(372, 228 + i * 24, str(i + 1), RED)
        f.text(390, 228 + i * 24, s, size=12)
    rect(f, 660, 90, 230, 210, fill="#FFF8E1", stroke="#C9A227", rx=5)
    txt(f, 670, 106, [
        [("Vì sao chờ IOMMU (chú thích", "b")],
        [("trong mã, dòng 1025-1031):", "b")],
        [("runtime suspend của IOMMU chạy", "t")],
        [("bất đồng bộ và có truy cập thanh", "t")],
        [("ghi; nếu PD/VD/CLK đã tắt thì", "t")],
        [("truy cập đó làm crash, nên driver", "t")],
        [("chỉ tắt PD sau khi IOMMU đã tắt.", "t")],
        [("", "t")],
        [("Đây là thứ tự của driver,", "i")],
        [("TRM không cho trình tự bật tắt.", "i")],
    ], size=11.5, dy=17)

    # ---- B. reset ----
    head(f, 330, "B. Reset: yêu cầu phần cứng (TRM1 tr.2052) và soft reset của driver (DRV rknpu_reset.c:98-148)")
    rect(f, 10, 344, 400, 150, fill="white", stroke="#999999", rx=5)
    txt(f, 22, 362, [
        [("Hai tín hiệu reset theo hai clock domain:", "b")],
        [("Aresetn", "c"), (": giao tiếp AXI và mọi Calculate/Control Core.", "t")],
        [("Hresetn", "c"), (": giao tiếp AHB, đồng bộ theo AHB clock.", "t")],
        [("Giữ cả hai ít nhất ", "t"), ("32 core clock cycles", "b"), (" theo clock", "t")],
        [("chậm hơn, rồi nhả cả hai cùng lúc.", "t")],
        [("DTS dòng 3469-3472: 6 reset ", "t"), ("srst_a0..2", "c"), (", ", "t"), ("srst_h0..2", "c")],
        [("(SRST_A_RKNN0..2, SRST_H_RKNN0..2).", "t")],
    ], size=12, dy=18)
    seq = ["reset_control_assert mọi srsts", "udelay(10)", "reset_control_deassert mọi srsts", "udelay(10)",
           "iommu_detach_device rồi iommu_attach_device"]
    f.text(430, 352, "rknpu_soft_reset", size=12.5, weight=700, mono=True)
    for i, s in enumerate(seq):
        f.badge(442, 374 + i * 22, str(i + 1), GRAY)
        f.text(460, 374 + i * 22, s, size=12)
    f.text(430, 488, "Gọi khi: job timeout (rknpu_job.c:604, 714), ioctl RKNPU_ACT_RESET (rknpu_drv.c:421),", size=11.5)
    f.text(430, 504, "ghi \"1\" vào debugfs rknpu/reset (rknpu_debugger.c:294-295).", size=11.5)

    # ---- C. IOMMU ----
    head(f, 540, "C. IOMMU của NPU (DTS dòng 3478, 3712-3727; DRV)")
    rect(f, 10, 554, 880, 92, fill="white", stroke="#999999", rx=5)
    txt(f, 22, 572, [
        [("DTS: ", "b"), ("node rknpu có ", "t"), ("iommus = <&rknpu_mmu>", "c"), ("; ", "t"), ("rknpu_mmu: iommu@fdab9000", "c"), (", ", "t"),
         ("compatible = \"rockchip,iommu-v2\"", "c"), (",", "t")],
        [("4 cửa sổ thanh ghi, 3 ngắt npu0_mmu, npu1_mmu, npu2_mmu; trong dtsi là ", "t"), ("status = \"disabled\"", "c"), (".", "t")],
        [("Driver: ", "b"), ("iommu_en", "c"), (" lấy từ thuộc tính \"iommus\" (rknpu_drv.c:798, 1294); bộ nhớ GEM được cấp IOVA và gọi ", "t"),
         ("iommu_map", "c")],
        [("(rknpu_gem.c:504, 549); soft reset gắn lại domain IOMMU (phần B, bước 5).", "t")],
    ], size=12, dy=18)

    # ---- D. MCU_NPU ----
    head(f, 674, "D. MCU_NPU (NPU_M0) nằm trong PD_NPUTOP")
    rect(f, 10, 688, 430, 150, fill="white", stroke="#999999", rx=5)
    f.table(20, 698, [130, 280], ["Thuộc tính", "Giá trị và nguồn"], [
        ["Lõi", "Cortex-M0 (TRM1 tr.1276)"],
        ["TCM / Cache", "64KB / 16KB (Table 9-1; DS tr.8)"],
        ["IRQ_NUM", "16 (Table 9-1)"],
        ["Mailbox", "MAILBOX2(MCU_NPU) (TRM1 tr.19)"],
    ], size=11.5, line_h=14)
    f.unknown(460, 688, ["Vai trò của MCU_NPU với một job", "NPU: TRM, DS, UG232 và mã driver",
                         "không nêu. Không suy đoán."], w=430, size=12)
    rect(f, 460, 768, 430, 70, fill=CALC, stroke="#90CAF9", rx=4)
    txt(f, 472, 792, [
        [("Driver ghi job vào thanh ghi PC của core (rknpu_job.c:346,", "t")],
        [("371; Hình 2.5); mã driver không có chữ mailbox hay mcu.", "t")],
    ], size=12, dy=17)
    f.unknown(10, 850, ["Ánh xạ tên reset của DTS (SRST_A_RKNN0) sang tên của CRU trong TRM; trình tự bật VD/PD do phần cứng",
                        "yêu cầu (TRM chỉ cho PMU bật tắt bằng phần mềm hoặc phần cứng)."], w=880, size=12)
    source(f, 896, "Nguồn: TRM1 tr.19, 1091, 1093, 1276, 2052; DS tr.8; DTS dòng 3459-3479, 3712-3727; DRV rknpu_drv.c, rknpu_reset.c, rknpu_gem.c, rknpu_job.c, rknpu_debugger.c.")
    return f


if __name__ == "__main__":
    run([("hk-1-clock-dvfs", fig_k1), ("hk-2-nguon-reset-iommu", fig_k2)], HERE)
