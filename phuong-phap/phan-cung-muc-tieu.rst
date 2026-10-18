:tocdepth: 1

**************
Board mục tiêu
**************

.. admonition:: Tóm tắt

   - Board mục tiêu là Orange Pi 5 với SoC RK3588S, RAM 4 GB (hệ điều hành thấy 3,916 MiB) và NPU 3 core, driver RKNPU 0.9.8.
   - OS là Orange Pi 1.2.4 Jammy (Ubuntu 22.04.5), kernel 6.1.99-rockchip-rk3588. Các thành phần RKNN-Toolkit2, RKNN-Toolkit-Lite2 và librknnrt đều 2.3.2.
   - Camera OV13855 NV12 1920×1080, model input 640×640 là default Ultralytics.
   - Paper SFCHD dùng 1333×800 nên baseline hiện tại không so trực tiếp được với số của paper SFCHD.
   - Các thông số cooling và ambient condition còn `[TBD]`.

.. _03-hardware:

Hardware
========

.. list-table::
   :header-rows: 1

   * - Item
     - Giá trị
   * - Board
     - Orange Pi 5
   * - SoC
     - RK3588S
   * - RAM
     - 4 GB (hệ điều hành thấy 3,916 MiB)
   * - Accelerator
     - NPU (3 NPU core), driver RKNPU 0.9.8
   * - OS / Kernel
     - Orange Pi 1.2.4 Jammy (Ubuntu 22.04.5) / 6.1.99-rockchip-rk3588
   * - RKNN-Toolkit2 / RKNN-Toolkit-Lite2 / librknnrt
     - 2.3.2
   * - Camera
     - OV13855, NV12, 1920×1080
   * - Model input
     - 640×640

RKNN-Toolkit2/librknnrt 2.3.2 đã verify thật trên board qua ``get_sdk_version()`` (xem ``tmp/04_debug-logs/2026-09-18_board-bringup-log.md``). RKNN-Toolkit-Lite2 2.3.2, driver RKNPU 0.9.8, OS, RAM đọc trực tiếp trên board ngày 2026-09-26 (log ``init_runtime`` của RKNN-Toolkit-Lite2: ``RKNN Driver Information, version: 0.9.8``, còn ``get_sdk_version()``: ``API: 2.3.2``, ``DRV: 0.9.8``).

Model input 640×640 là default Ultralytics (paper SHEL5K không nêu kích thước input khi train/test). Paper SFCHD tự dùng 1333×800 (:download:`sfchd_scale_2023yu.pdf <../_assets/pdf/papers/07_ppe_detection/sfchd_scale_2023yu.pdf>`, tr.9: *"the image size was adjusted to 1333 \* 800"*) nên baseline hiện tại không so trực tiếp được với số của paper SFCHD.

Đầy đủ + các thông số còn ``[TBD]`` (cooling, ambient condition): xem :ref:`Table C <table-c-hardware--software-environment>` ở mục 7.
