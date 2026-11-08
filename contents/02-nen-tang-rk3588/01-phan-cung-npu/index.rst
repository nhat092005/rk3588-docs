********************
Phần cứng NPU RK3588
********************

Vị trí trong SoC, cấu trúc core, nhiều core và SRAM, clock, thanh ghi và đường dữ liệu.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-vi-tri-soc-phan-vung-nguon-va-mcu`
     - NPU nằm đâu trong SoC, nối vào bus nào, thuộc miền nguồn nào, và MCU đi kèm là gì.
   * - 02
     - :doc:`02-vi-kien-truc-va-khoi-tinh-toan-core`
     - Một core gồm những khối nào, kiểu số và số MAC mỗi chu kỳ, buffer 384KB và vai trò của DPU.
   * - 03
     - :doc:`03-che-do-da-loi-va-system-sram`
     - Ba core chạy riêng hay cùng nhau, chọn chế độ bằng gì, và System SRAM (dung lượng, địa chỉ, ai dùng chung).
   * - 04
     - :doc:`04-xung-nhip-dvfs-va-reset`
     - Nguồn clock, các mức tần số, đổi mức thế nào, và cách reset NPU.
   * - 05
     - :doc:`05-ban-do-thanh-ghi-va-co-che-cau-hinh`
     - Tổ chức thanh ghi, hai chế độ cấu hình, ping-pong register, ngắt, và chỗ TRM tự mâu thuẫn hoặc bỏ trống.
   * - 06
     - :doc:`06-duong-truyen-du-lieu-iommu-va-ddr`
     - Dữ liệu đi từ DDR đến NPU qua những khối nào, QoS, IOMMU, giới hạn của DDR controller và DMAC.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-vi-tri-soc-phan-vung-nguon-va-mcu
   02-vi-kien-truc-va-khoi-tinh-toan-core
   03-che-do-da-loi-va-system-sram
   04-xung-nhip-dvfs-va-reset
   05-ban-do-thanh-ghi-va-co-che-cau-hinh
   06-duong-truyen-du-lieu-iommu-va-ddr
