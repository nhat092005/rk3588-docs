:tocdepth: 1

*******
Runbook
*******

.. admonition:: Tóm tắt

   - Runbook có 13 bước chạy từ trên xuống, trong đó cột "Kết quả đúng" là thứ cần thấy trước khi sang bước sau.
   - `make phase2/3/4/10` bỏ qua bước đã có file kết quả, dừng ở lỗi đầu tiên và kết thúc bằng `make tables`.
   - Phase 2 train baseline seed 42 mất khoảng 17 giờ GPU cho cả 2 dataset, còn Phase 3 chỉ cần ssh tới board.
   - Phase 4 cần `start_rknn_server.sh` (bước 4) và `lock_freq.sh lock` (bước 9) trước. Tầng 1 FP16 mất khoảng 30 phút/model.
   - Sau bước 10 chạy `lock_freq.sh unlock` để governor về `ondemand`, và đọc `results/<ds>/SOURCES.md` sau mỗi phase để mục "Errors" ghi `none`.

.. _80-tổng-quan:

Tổng quan
=========

.. list-table::
   :header-rows: 1

   * - Phase
     - Tên
     - Lệnh
     - Cần board
     - Bảng được sinh
   * - 0
     - Chuẩn bị môi trường và board
     - lệnh lẻ (8.1, bước 1–4)
     - Có
     - C
   * - 1
     - Khoá protocol v1
     - ``make golden-test``, ``make test-parsers``
     - Không
     - -
   * - 2
     - Train baseline YOLOv8n/s, seed 42
     - ``make phase2 DATASET=<ds>``
     - Không
     - A, B, D
   * - 3
     - Quantization FP16 / INT8
     - ``make phase3 DATASET=<ds>``
     - Có
     - E, F
   * - 4
     - Benchmark trên board
     - ``make phase4 DATASET=<ds>``
     - Có, khoá tần số
     - G, H, I, K, L
   * - 5
     - Multi-model YOLO11n/s
     - như Phase 2–4 sau khi thêm model
     - Có
     - D–L (dòng YOLO11)
   * - 6
     - Bottleneck analysis
     - đọc ``table_K_layers.md``
     - Không
     - K
   * - 7
     - Proposed optimization
     - như Phase 2–4 cho candidate
     - Có
     - J
   * - 8
     - Ablation
     - như Phase 2–4
     - Có
     - M
   * - 9
     - Camera / real-world
     - code viết ở Phase 9
     - Có
     - -
   * - 10
     - Chốt số liệu: seed 43, 44 cho model chính
     - ``make phase10 DATASET=<ds> MODELS=...``
     - Có
     - D, F, J, M (mean ± std)

``make phase2/3/4/10`` chạy lần lượt mọi bước của phase, **bỏ qua bước đã có file kết quả**, dừng ở lỗi đầu tiên, và kết thúc bằng ``make tables``. Bị ngắt (mất điện, lỗi mạng) thì sửa lỗi rồi chạy lại đúng lệnh đó.

--------------

.. _81-runbook:

Runbook
=======

Chạy từ trên xuống. Cột "Kết quả đúng" là thứ cần thấy trước khi sang bước sau.

.. list-table::
   :header-rows: 1

   * - #
     - Lệnh
     - Chạy khi
     - Kết quả đúng
   * - 1
     - ``make sync``\ \ ``make check``
     - 1 lần trên PC
     - In ``rknn.api.RKNN OK``
   * - 2
     - ``make board-sync``
     - 1 lần, và sau mỗi lần sửa ``ai/board/``
     - Board có ``~/rk3588/ai/board/`` và 1,238 ảnh ``sfchd_test``
   * - 3
     - ``make board-setup``
     - 1 lần
     - In ``RKNNLite OK``
   * - 4
     - [board, sudo] ``sudo bash ai/board/start_rknn_server.sh``
     - Sau mỗi lần khởi động lại board, trước Phase 4 (tầng 1 cần)
     - In ``adbd listening on 5555`` và pid ``rknn_server``
   * - 5
     - ``make golden-test``\ \ ``make test-parsers``
     - Trước khi sinh số liệu, và sau mỗi lần sửa code đo
     - ``GOLDEN TEST PASSED``, ``PARSERS OK``
   * - 6
     - ``make phase2 DATASET=sfchd_5class``\ \ ``make phase2 DATASET=sfchd_shel5k``
     - Train baseline seed 42 (khoảng 17 giờ GPU cho cả 2)
     - ``phase2 complete``, đồng thời ``results/<ds>/table_D_fp32.md`` đủ 2 dòng
   * - 7
     - Chọn dataset, ghi vào ``tmp/02_decisions/``
     - Sau bước 6
     - Quyết định có số từ Table D
   * - 8
     - ``make phase3 DATASET=<ds>``
     - Sau bước 7 (chỉ cần ssh tới board)
     - ``phase3 complete``, đồng thời Table E, F không còn ``[TBD]``
   * - 9
     - [board, sudo] ``sudo bash ai/board/lock_freq.sh lock``
     - Trước bước 10
     - Mọi dòng in ``performance``
   * - 10
     - ``make phase4 DATASET=<ds>``
     - Sau bước 4 và 9 (tầng 1 FP16 mất khoảng 30 phút/model)
     - ``phase4 complete``, đồng thời Table G, H, I, K, L không còn ``[TBD]``
   * - 11
     - [board, sudo] ``sudo bash ai/board/lock_freq.sh unlock``
     - Sau bước 10
     - Governor về ``ondemand``
   * - 12
     - Đọc ``results/<ds>/SOURCES.md``
     - Sau mỗi phase
     - Mục "Errors" ghi ``none``
   * - 13
     - ``make phase10 DATASET=<ds> MODELS=yolov8n_baseline,<model đề xuất>``
     - Cuối đề tài, sau Phase 7–9
     - ``phase10 complete``, đồng thời Table D, F có mean ± std cho các model chính

Phase 5–9 dùng lại đúng các lệnh trên cho model mới (xem từng phase).
