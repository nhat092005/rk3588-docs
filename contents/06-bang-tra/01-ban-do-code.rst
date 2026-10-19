:tocdepth: 1

***********
Bản đồ code
***********

.. admonition:: Tóm tắt

   - Bảng liệt kê từng file code của pipeline, việc nó làm và lệnh make gọi nó, ví dụ ai/automation/pipeline.py chạy cả phase qua make phase2/3/4.
   - ai/core/evaluator.py thực hiện protocol v1 gồm LetterBox, NMS, AP và dấu vân tay dataset, được evaluate, run và check dùng.
   - Với .rknn, ai/automation/evaluate.py điều phối chạy trên board qua ssh, còn ai/board/infer_dump.py lưu output thô và md5 input.
   - Đo hiệu năng chia hai tầng: tầng 1 là benchmark_npu.py với 3 phiên eval_perf, tầng 2 là các script trong ai/board/ chạy trên board.
   - start_rknn_server.sh và lock_freq.sh là lệnh sudo trên board, chạy tay.

.. _8a1-bản-đồ-code:

Bản đồ code
===========

.. list-table::
   :header-rows: 1

   * - File
     - Làm gì
     - Gọi bởi
   * - ``ai/automation/pipeline.py``
     - Chạy cả phase, bỏ qua bước đã xong
     - ``make phase2/3/4``
   * - ``ai/automation/run.py``, ``ai/core/trainer.py``
     - Train, evaluator v1 trên ``best.pt``, ghi leaderboard
     - ``make train``
   * - ``ai/core/evaluator.py``
     - Protocol v1: LetterBox, NMS, AP, dấu vân tay dataset
     - evaluate, run, check
   * - ``ai/core/backends.py``
     - PyTorch/ONNX trên PC. Với ``.rknn``: đọc output board, kiểm md5 input
     - evaluator
   * - ``ai/core/provenance.py``
     - git commit, git_dirty, sha256, thời điểm
     - mọi file kết quả
   * - ``ai/automation/evaluate.py``
     - AI Quality 1 run × 1 backend, với ``.rknn`` điều phối chạy trên board qua ssh
     - ``make evaluate``
   * - ``ai/board/infer_dump.py``
     - Inference ``.rknn`` trên board, lưu output thô + md5 input
     - ``evaluate.py`` qua ssh
   * - ``ai/automation/check_evaluator.py``
     - Golden test, kiểm chéo
     - ``make golden-test``, ``make crosscheck``
   * - ``ai/automation/export_npu.py``, ``ai/core/rknn/baseline.py``, ``calibration.py``
     - Calibration, export ``.rknn``, ``.onnx``
     - ``make export-npu``
   * - ``ai/automation/complexity.py``
     - Params, GFLOPs, MACs, kích thước
     - ``make complexity``
   * - ``ai/automation/benchmark_npu.py``, ``ai/core/rknn/benchmark.py``
     - Tầng 1: 3 phiên ``eval_perf`` / layer / ``eval_memory``
     - ``make benchmark-npu``
   * - ``ai/automation/bench_gpu.py``
     - Latency GPU PC (tham chiếu)
     - ``make bench-gpu``
   * - ``ai/automation/board_check.py``
     - Kiểm adb, ``rknn_server``, khoá tần số
     - ``make board-check``
   * - ``ai/automation/tables.py``
     - Sinh bảng A–L, kiểm nhất quán
     - ``make tables``
   * - ``ai/board/common.py``
     - Pre/post giống evaluator, đo RAM/CPU/nhiệt độ, đọc governor
     - 3 script board
   * - ``ai/board/bench_npu.py``, ``bench_cpu_onnx.py``, ``bench_throughput.py``
     - Tầng 2 trên board
     - ``make bench-board*``
   * - ``ai/board/start_rknn_server.sh``, ``lock_freq.sh``
     - Lệnh sudo trên board
     - chạy tay
   * - ``scripts/logtee.py``
     - Chạy lệnh, lưu log đã làm gọn + header
     - mọi target sinh kết quả
   * - ``tests/test_parsers.py``, ``tests/fixtures/``
     - Kiểm parser với output thật RKNN 2.3.2
     - ``make test-parsers``
