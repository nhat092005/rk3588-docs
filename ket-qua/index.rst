*******
Kết quả
*******

Số liệu của đề tài nằm ở repo chính, trong ``results/<dataset>/table_*.md`` do ``make tables`` sinh, không sửa tay. Mục này chỉ ghi số liệu đã đóng băng kèm file và commit. Kế hoạch là đóng băng sau Phase 10 (seed 43, 44), nên hiện chưa có bảng nào được đóng băng.

Tình trạng hiện tại của ``results/sfchd_5class/`` (commit ``0489831``, 2026-10-10, protocol v1, mỗi model một seed 42):

- ``SOURCES.md``: 203 ô, thiếu 158.
- Hai cảnh báo: kết quả đánh giá ``pt_fp32`` của hai run (``yolov8n_baseline``, ``yolov8s_baseline``) được tạo khi code chưa commit (``git_dirty``).

.. list-table::
   :header-rows: 1
   :widths: 14 40 26 20

   * - Bảng
     - File
     - Dòng còn ``TBD``
     - Đóng băng
   * - A
     - ``table_A_dataset.md``
     - 0
     - chưa
   * - B
     - ``table_B_training.md``
     - 0
     - chưa
   * - C
     - ``table_C_environment.md``
     - 1
     - chưa
   * - D
     - ``table_D_fp32.md``
     - 0
     - chưa
   * - E
     - ``table_E_complexity.md``
     - 2
     - chưa
   * - F
     - ``table_F_quantization.md``
     - 4
     - chưa
   * - G
     - ``table_G_latency.md``
     - 4
     - chưa
   * - H
     - ``table_H_hardware.md``
     - 8
     - chưa
   * - I
     - ``table_I_deployment.md``
     - 10
     - chưa
   * - J, M
     - ``table_J_M.md``
     - 0 (chỉ có ghi chú, chưa có hàng số)
     - chưa
   * - K
     - ``table_K_layers.md``
     - 2
     - chưa
   * - L
     - ``table_L_resource.md``
     - 4
     - chưa

Cột, cách đo và nơi sinh của từng bảng nằm ở :doc:`/phuong-phap/dac-ta-bang/index`.
