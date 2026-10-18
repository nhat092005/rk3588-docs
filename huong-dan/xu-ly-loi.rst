:tocdepth: 1

*********
Xử lý lỗi
*********

.. admonition:: Tóm tắt

   - `adb cannot reach the board` hoặc `rknn_server is not running` xảy ra khi board vừa khởi động lại hoặc `adbd` tự thoát, trong đó nguyên nhân ngày 2026-09-27 là chưa rõ.
   - Lỗi adb sửa bằng `sudo bash ai/board/start_rknn_server.sh` rồi chạy lại phase. Lỗi `frequencies not locked` sửa bằng `sudo bash ai/board/lock_freq.sh lock`.
   - Lỗi `... already exists; move it away` do run bị ngắt giữa lúc train. Xoá thư mục run đó rồi chạy lại `make phase2`.
   - `STOPPED at step i` nghĩa là lệnh make của bước i lỗi. Cần đọc log mới nhất trong `runs/<run_id>/logs/` rồi chạy lại phase.
   - Không chạy lệnh `adb` nào khác khi `benchmark-npu` đang chạy, vì đo thử ngày 2026-09-26 cho thấy phiên đo bị treo sau khi `adb connect` chen vào.

.. _83-khi-có-lỗi:

Khi có lỗi
==========

.. list-table::
   :header-rows: 1

   * - Thông báo
     - Nguyên nhân
     - Cách sửa
   * - ``adb cannot reach the board`` hoặc ``rknn_server is not running``
     - Board vừa khởi động lại, hoặc ``adbd`` tự thoát (gặp ngày 2026-09-27: board chạy liên tục nhưng ``adbd`` mất, log trống, chưa rõ nguyên nhân)
     - [board, sudo] ``sudo bash ai/board/start_rknn_server.sh``, rồi chạy lại phase
   * - ``frequencies not locked``
     - Chưa khoá tần số trước Phase 4
     - [board, sudo] ``sudo bash ai/board/lock_freq.sh lock``
   * - ``... already exists; move it away``
     - Run bị ngắt giữa lúc train (có ``weights/`` nhưng chưa có ``eval/``)
     - Xoá thư mục run đó, chạy lại ``make phase2``
   * - ``STOPPED at step i``
     - Lệnh make của bước i lỗi
     - Đọc log mới nhất trong ``runs/<run_id>/logs/``, sửa, chạy lại phase
   * - ``ERROR:`` khi ``make tables``
     - Một kiểm ở 8.2 không đạt
     - Chạy lại lệnh sinh file bị báo (xoá file đó rồi chạy lại phase)

Không chạy lệnh ``adb`` nào khác (kể cả ``make board-check``) khi lệnh tầng 1 (``benchmark-npu``) đang chạy: đo thử ngày 2026-09-26, phiên đang đo bị treo sau khi có lệnh ``adb connect`` chen vào. Tầng 1 FP16 chậm là bình thường: ``init_runtime`` khoảng 4.7 phút (upload model qua ``rknn_server``), mỗi ``eval_perf`` 1.5–2 phút.
