:tocdepth: 1

*******************
Phase 0-1: chuẩn bị
*******************

.. admonition:: Tóm tắt

   - Phase 0 đã xong phần lớn ngày 2026-09-26: board có RKNN-Toolkit-Lite2 2.3.2, driver RKNPU 0.9.8, start_rknn_server.sh chạy được và lock_freq.sh lock khoá được CPU, NPU, DDR.
   - Việc còn mở ở Phase 0 là ghi cách tản nhiệt và nhiệt độ phòng vào Table C.
   - Phase 1 khoá protocol v1: make golden-test pass và make crosscheck với model 7 class cũ cho 24 metric, lệch lớn nhất 0.0001.
   - Parser eval_perf khớp output thật RKNN 2.3.2 (tổng thời gian 119 layer), và tiền xử lý trên board trùng từng pixel với evaluator (md5 4 ảnh).
   - Accuracy .rknn FP16 đo trên board cho mAP50-95 0.3677, sát FP32 0.3669 (model nháp), md5 input trùng ở cả 1,238 ảnh.

.. _phase-0-chuẩn-bị-môi-trường-và-board:

Phase 0. Chuẩn bị môi trường và board
=====================================

**Mục tiêu:** PC và board sẵn sàng, có đủ thông tin cho Table C.

**Lệnh:** Runbook bước 1–4.

- ☒ Bước 2, 3: ``make board-sync``, ``make board-setup`` (2026-09-26: numpy 1.26.4, OpenCV 4.11.0, onnxruntime 1.23.2, RKNN-Toolkit-Lite2 2.3.2)
- ☒ Bước 4: ``start_rknn_server.sh`` chạy được (2026-09-26, sau khi sửa lỗi ``adbd`` khởi động trước khi bản cũ thoát hẳn)
- ☒ ``lock_freq.sh lock`` khoá được CPU, NPU, DDR ở tần số tối đa (2026-09-26)
- ☒ Table C (Guide): OS, kernel, RAM, RKNN-Toolkit-Lite2, driver RKNPU 0.9.8, ONNX Runtime, governor, thermal zone
- ☐ Ghi cách tản nhiệt và nhiệt độ phòng vào Table C

**Tiêu chí xong:** ``make board-check LOCK=1`` in ``adb: ok, rknn_server: ok, frequencies locked: True``.

--------------

.. _phase-1-khoá-protocol-v1:

Phase 1. Khoá protocol v1
=========================

**Mục tiêu:** mọi công cụ đo đúng protocol v1 (mục 5) trước khi sinh số liệu.

**Lệnh:** ``make golden-test``, ``make test-parsers``. Kiểm chéo với ``model.val()`` chạy tự động trong ``make phase2``.

- ☒ ``make golden-test`` pass (2026-09-26, log ``ai/automation/golden/logs/``). Golden file ``ai/automation/golden/evaluator_v1.json``
- ☒ ``make crosscheck`` với model 7 class cũ: 24 metric, lệch lớn nhất 0.0001
- ☒ Parser ``eval_perf`` khớp output thật của RKNN 2.3.2: tổng thời gian 119 layer đúng bằng tổng board in ra (``tests/test_parsers.py``)
- ☒ Tiền xử lý trên board trùng từng pixel với evaluator (md5 4 ảnh). Ảnh calibration trùng input evaluator (sai khác 0)
- ☒ Accuracy ``.rknn`` đo trên board: FP16 cho mAP50-95 0.3677, sát FP32 0.3669 (model nháp), md5 input trùng ở cả 1,238 ảnh
- ☒ Chạy thử qua ``make`` với model nháp (kết quả nháp đã xoá): train 1 epoch (có log, chạy lại bị chặn), export FP16/INT8, evaluate PyTorch/ONNX/RKNN INT8, tầng 1 INT8, tầng 2 FP16/INT8, ``bench-gpu``, ``make tables`` (117 ô, sinh đúng)
- ☒ Chạy thử qua ``make`` phần còn lại (2026-09-27): ``evaluate BACKEND=rknn PREC=fp16`` (mAP50-95 0.3677, trùng lần trước), ``bench-board-cpu``, ``bench-board-throughput`` (1 và 3 context), ``benchmark-npu PREC=fp16`` (median 29.89 ms, 5 lần 28.0–30.0 ms, bộ nhớ NPU 23.86 MiB), ``make phase3`` (lần 1 làm đúng các bước thiếu, lần 2 bỏ qua hết)
- ☒ ``make tables`` báo lỗi đúng khi file tầng 2 đo lúc chưa khoá tần số

**Tiêu chí xong:** 2 lệnh trên pass trên commit sẽ dùng để sinh số liệu.
