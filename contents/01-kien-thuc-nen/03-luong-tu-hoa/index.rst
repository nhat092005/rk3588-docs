************
Lượng tử hóa
************

Lý thuyết lượng tử hóa: affine, PTQ, QAT, hybrid và cách đo sai số. Phần RKNN nằm ở Nền tảng RK3588.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-luong-tu-hoa-affine-va-granularity`
     - Vì sao lượng tử hóa, ánh xạ affine bằng scale và zero-point, symmetric so với asymmetric, per-tensor so với per-channel.
   * - 02
     - :doc:`02-chien-luoc-ptq-qat-va-hon-hop`
     - PTQ với calibration, QAT mô phỏng lượng tử hóa lúc train, và khi nào dùng nhiều mức bit.
   * - 03
     - :doc:`03-phan-tich-sai-so-va-dac-thu-yolo`
     - Đo và chẩn đoán sai số lượng tử hóa, và vấn đề riêng của detector như YOLO.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-luong-tu-hoa-affine-va-granularity
   02-chien-luoc-ptq-qat-va-hon-hop
   03-phan-tich-sai-so-va-dac-thu-yolo
