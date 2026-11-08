*************************
Compiler và tối ưu đồ thị
*************************

Từ đồ thị mạng đến lệnh phần cứng: các tầng biểu diễn, fusion và tiling.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-bieu-dien-trung-gian-va-ha-bac-do-thi`
     - Các tầng biểu diễn trung gian từ đồ thị mạng đến lệnh phần cứng, và phần nào compiler hay người dùng can thiệp được.
   * - 02
     - :doc:`02-toi-uu-do-thi-va-operator-fusion`
     - Operator fusion, constant folding và hiệu quả giảm lượt truy cập DRAM.
   * - 03
     - :doc:`03-tiling-va-lap-lich-thuc-thi`
     - Tiling theo SRAM on-chip, vùng biên halo, thứ tự vòng lặp và giới hạn khi đối chiếu với RK3588.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-bieu-dien-trung-gian-va-ha-bac-do-thi
   02-toi-uu-do-thi-va-operator-fusion
   03-tiling-va-lap-lich-thuc-thi
