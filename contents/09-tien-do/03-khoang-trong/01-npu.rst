:tocdepth: 1

******************************
Điều chưa rõ: NPU và phần cứng
******************************

.. admonition:: Tóm tắt

   - Kiểu dataflow, kích thước mỗi bank của buffer 384KB và chức năng firmware của MCU NPU_M0 đều là `unknown` vì TRM không nêu.
   - Kích thước PE array chỉ biết một phần: TRM có "Int8 mac array 32x32 mode" [T1 TRM1 tr.2001], chỉ cho INT8.
   - Tần số tối đa: Datasheet V1.3 (RK3588) và V1.7 (RK3588S) đã ghi rõ Max NPU frequency là 1000 MHz (bản V0.1 ghi TBD). OPP tối đa 1000 MHz khớp với DTS và thông số driver.
   - IOMMU của NPU: DTS khai báo node `rockchip,iommu-v2` và driver có module `rknpu_iommu.c`. Cửa sổ `FF000000` của `SYSTEM_SRAM` khớp TRM1 Ch.34 (tr.1965), còn `FD600000` chưa được TRM giải thích.
   - Chế độ cấu hình: Driver 0.9.8 chỉ chấp nhận job chạy chế độ PC (Program Counter) qua cờ `RKNPU_JOB_PC`, chế độ Non-PC không được hỗ trợ.

.. contents:: Trong trang này
   :local:
   :depth: 1

Còn thiếu nguồn (unknown) và truy vấn
=====================================

.. list-table::
   :header-rows: 1

   * - Chủ đề
     - Vì sao chưa có
     - Truy vấn đề xuất (chưa thực hiện)
   * - Một nguồn T2 dành riêng một đoạn phân tích lý do cần NPU
     - Chỉ có 3 lập luận rời trong khối này, cộng hai câu của BAMB tr.1
     - "efficient processing of deep neural networks: a tutorial and survey"."domain-specific architectures for deep learning survey"
   * - Roofline nguyên bản
     - TPU chỉ "adapt" (TPU trích là [Wil09])
     - "Roofline: an insightful visual performance model for multicore architectures"
   * - Cơ chế zero-skipping và nén
     - Chi tiết ở tài liệu ngoài corpus
     - "Cnvlutin ineffectual neuron free deep neural network computing"."Efficient Inference Engine EIE compressed deep neural network"."Eyeriss ISSCC 2016 energy-efficient reconfigurable accelerator"
   * - Liên hệ giữa khái niệm ở đây và RK3588
     - Không nguồn T2 nào nói về Rockchip
     - xem :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/01-vi-tri-soc-phan-vung-nguon-va-mcu` (T1)

Không dùng trong file này
=========================

- SURV Table 9 để phân loại thiết bị (xếp Jetson Xavier NX vào GPU và Jetson Nano vào NPU, mục Nguồn cuối trang).
- Con số TPU "15X-30X" và "30X-80X" như lợi ích chung của NPU: chỉ so với Haswell và K80 năm 2015.

.. _211-điều-trm-không-nói:

Điều TRM không nói
==================

Các từ khóa đã tìm trong TRM1 Ch.36, TRM2, Datasheet, UG152, API232, SRAM và Operator List: ``dataflow``, ``data flow``, ``stationary``, ``systolic``, ``tile``, ``tiling``, ``PE array``, ``processing element``, ``loop order``, ``im2col``, ``winograd``, ``NVDLA``. Không có kết quả liên quan kiến trúc ().

.. list-table::
   :header-rows: 1

   * - Chủ đề
     - Kết quả
     - Verdict
   * - Kiểu dataflow (weight, output, row stationary)
     - Không có từ khóa nào
     - unknown
   * - Tiling
     - TRM không có thuật ngữ. Có tham số thanh ghi ``feature_grains``, ``data_entries``, ``weight_reuse``, ``data_reuse`` (TRM1 tr.2000, 2004) và tên pass ``RKNNTilingPass`` trong log của User Guide (UG232 tr.168)
     - unknown cho khái niệm, một phần cho tham số
   * - Kích thước PE array
     - TRM không dùng chữ PE. Có "Int8 mac array 32x32 mode" (TRM1 tr.2001)
     - một phần: chỉ INT8
   * - Kích thước mỗi bank của buffer 384KB
     - Bank 0 đến 7 trong thanh ghi, không có kích thước
     - unknown
   * - Tần số tối đa, bảng OPP, quy ước 1 MAC = 2 phép tính trong tài liệu vendor
     - DS tr.11 "up to 6 TOPS". DS V1.3 và V1.7 ghi rõ "Max NPU frequency: 1000 MHz" (bản V0.1 cũ ghi TBD). OPP tối đa 1000 MHz (DTS dòng 3534-3655), chi tiết ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/04-xung-nhip-dvfs-va-reset`
     - Đã đóng: 1000 MHz
   * - Vai trò MCU NPU_M0
     - Ngắt ``C0_RKNN``..\ ``C2_RKNN`` và mailbox nối vào NPU_M0 (TRM1 tr.1298), chức năng firmware không được mô tả
     - unknown
   * - NPU có qua IOMMU không
     - Chương 36 TRM không nói. Đã đóng (T1 DTS và DRV): DTS khai báo ``iommus = <&rknpu_mmu>`` (dòng 3478), driver quản lý IOMMU v2 domain riêng, chi tiết ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/01-vi-tri-soc-phan-vung-nguon-va-mcu`
     - Đã đóng
   * - Hai cửa sổ ``SYSTEM_SRAM``
     - ``FF000000`` khớp TRM1 Ch.34 (tr.1965).``FD600000`` không được giải thích
     - một phần

**Truy vấn đề xuất** (chưa thực hiện, kết quả phải được mở và trích đúng trang trước khi dùng)

.. list-table::
   :header-rows: 1

   * - Câu hỏi
     - Truy vấn
   * - Dataflow, tiling, bố cục PE
     - "Rockchip RKNPU hardware architecture white paper"."RK3588 RKNN MAC array 32x32 int8 microarchitecture"
   * - Ý nghĩa CBUF, CSC, CMAC, CNA, DDMA, SDMA, BS, BN, EW, kích thước bank
     - mã nguồn driver ``rknpu`` chính thức của Rockchip
   * - Dual và triple co-work chia việc thế nào. Đóng một phần (T1 DRV, UG232 tr.75): chia việc theo khối lượng tính toán (workload), lập lịch trong driver (``todo_list`` mỗi lõi, AUTO chọn lõi ít task nhất), chi tiết ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram`
     - "Rockchip rknpu driver multi-core scheduling source"
   * - Bảng OPP, tần số tối đa. Đã đóng (T1 DS V1.3/V1.7, DTS, DRV): tần số tối đa 1000 MHz, chi tiết ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/04-xung-nhip-dvfs-va-reset`
     - Đã giải đáp
   * - Quy ước đếm phép tính cho 6 TOPS
     - "Rockchip RK3588 NPU 6 TOPS int8 calculation frequency"
   * - IOMMU. Đã đóng (T1 DRV, DTS): ``iommus = <&rknpu_mmu>``, chi tiết ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/01-vi-tri-soc-phan-vung-nguon-va-mcu`
     - Đã giải đáp

Không được viết
===============

- "NPU chạy 1GHz" như tần số tối đa hoặc mặc định, và "6 TOPS" như kết quả suy ra trong tài liệu vendor.
- "RK3588 chạy model INT4, BF16, TF32 qua ``rknn.config``" (Matmul C API có INT4, xem 2.4).
- "dual core = ``nn_mode`` 64x32".
- "Mỗi bank 48KB".
- "Zero-skipping là MAC bỏ phép nhân 0" hoặc ngược lại "MAC không bỏ phép nhân 0": TRM không nói.
