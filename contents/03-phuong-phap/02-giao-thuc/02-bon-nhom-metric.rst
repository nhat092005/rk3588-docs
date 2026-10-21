:tocdepth: 1

***************
Bốn nhóm metric
***************

.. admonition:: Tóm tắt

   - AI Quality khoá v1 theo mặc định val của Ultralytics 8.4.154: LetterBox 640×640 `rect=False`, NMS conf 0.001, IoU 0.7, max_det 300, AP nội suy 101 điểm.
   - Accuracy `.rknn` đo bằng inference trên board, NMS và AP chạy trên PC. Với model nháp, FP16 ra mAP50-95 0.3677 so với FP32 0.3669.
   - Số của `model.val()` in ra lúc train không dùng để điền bảng, vì với `.pt` Ultralytics tự bật `rect=True` còn model export thì tắt.
   - Model Complexity đo trên model đã fuse ở 640×640 với MACs = GFLOPs / 2, không dùng kích thước `.pt` vì `best.pt` lưu ở FP16.
   - Tầng 1 dùng `eval_perf(fix_freq=True)` với 3 phiên `init_runtime` riêng, còn tầng 2 chạy trên board với 20 lần warmup rồi toàn bộ ảnh `sfchd_test`.
   - FPS_latency và Throughput FPS đo hai thứ khác nhau. Cụ thể, DAHD-YOLO báo latency 79.1 ms nhưng 50.2 FPS vì dùng thread pool 3 core.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _51-ai-quality:

AI Quality
==========

.. code:: text

   Precision
   Recall
   mAP50
   mAP50-95
   AP_person
   AP_helmet
   AP_head
   AP_safety_clothes
   AP_self_clothes
   ΔmAP khi quantize = mAP (FP32) - mAP (INT8), kèm ΔAP từng class

``AP_head`` và ``AP_self_clothes`` là 2 tín hiệu vi phạm trong 5 class đã chốt (:ref:`Application hiện tại <01-application-hiện-tại>`). ΔmAP là metric trực tiếp của Case B (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>`).

**Cách đo (khoá v1)**, theo mặc định val của Ultralytics 8.4.154, đã kiểm trong ``.venv``:

.. list-table::
   :header-rows: 1

   * - Tham số
     - Giá trị
   * - Tập đánh giá
     - eval set ``sfchd_test`` (1,238 ảnh) cho mọi model. Thêm ``shel5k_test`` (500 ảnh) và ``chv_test`` (44 ảnh, mới) cho model Lựa chọn 2
   * - Resize
     - Resize cạnh dài về 640, rồi LetterBox 640×640 vuông (``rect=False``), không phóng to thêm, căn giữa, viền màu 114
   * - NMS
     - conf 0.001, IoU 0.7, max_det 300, tính riêng từng class, 1 box có thể mang nhiều class (``multi_label=True``)
   * - mAP
     - IoU 0.50 đến 0.95 bước 0.05, AP nội suy 101 điểm (chuẩn COCO)
   * - Precision / Recall
     - lấy tại ngưỡng conf cho F1 trung bình lớn nhất
   * - Model ``.rknn`` (FP16/INT8)
     - Inference chạy trên board bằng RKNNLite với đúng input của evaluator. Khâu NMS và AP chạy trên PC bằng cùng code như FP32

Nguồn trong ``.venv/lib/python3.12/site-packages/ultralytics/``: ``cfg/default.yaml`` (conf, iou, max_det), ``data/base.py`` ``load_image`` (resize cạnh dài), ``data/dataset.py`` dòng 320 (LetterBox khi val), ``models/yolo/detect/val.py`` ``postprocess`` (``multi_label=True``), ``utils/metrics.py`` (``compute_ap``: *"101-point interp (COCO)"*, ``ap_per_class``: *"max-F1 precision, recall"*).

**Accuracy của ``.rknn``:** ``ai/board/infer_dump.py`` chạy trên board, ghi output thô của mọi anchor có score lớn nhất > 0.001 (anchor khác không thể qua NMS ở conf 0.001, nên không mất thông tin) kèm md5 input từng ảnh. PC đọc lại bằng ``RknnDumpBackend``, kiểm md5 trùng input của evaluator, rồi NMS và AP như FP32. Không gọi ``rknn.inference()`` từ PC qua ``rknn_server``: đo ngày 2026-09-26 qua Tailscale, 1 ảnh FP16 mất khoảng 35 s (trên board 42 ms), tức khoảng 12 giờ cho 1,238 ảnh. Kiểm đường đo mới với model nháp: FP16 ra mAP50-95 0.3677 so với FP32 0.3669.

**Khác với ``model.val()`` mặc định:** gọi ``model.val()`` trên file ``.pt`` thì Ultralytics tự bật ảnh chữ nhật (``engine/model.py`` dòng 633: ``custom = {"rect": True}``), còn với model đã export (``.onnx``, ``.rknn``) thì tắt (``engine/validator.py``: ``self.args.rect = False``). Nếu dùng ``model.val()`` nguyên bản, FP32 và INT8 sẽ khác nhau cả ở cách resize chứ không chỉ ở model. NPU chỉ nhận input vuông 640×640, nên protocol v1 khoá ``rect=False`` cho mọi backend. Vì vậy số của ``model.val()`` in ra lúc train (thư mục ``plots/``) không dùng để điền bảng.

Lý do: đây là cách tính chuẩn COCO, và các paper trong ``_assets/pdf/papers/`` đều báo mAP theo kiểu này, không đặt ngưỡng conf triển khai. Precision/Recall tại ngưỡng conf dùng khi báo vi phạm trên camera sẽ thêm ở v1.1, sau khi chốt ngưỡng đó.

.. _52-model-complexity:

Model Complexity
================

.. code:: text

   Parameters (model đã fuse Conv + BN)
   GFLOPs ở 640×640
   MACs = GFLOPs / 2
   Model size: file .onnx (FP32) và file .rknn (chạy trên board)

**Cách đo (khoá v1):**

- Tính trên model đã fuse, vì Ultralytics tự fuse trước khi export: build log dòng 2 ghi ``Model summary (fused)``.
- GFLOPs lấy từ hàm ``get_flops`` của Ultralytics, công thức ``thop.profile(...)[0] / 1e9 * 2`` (số MACs nhân 2). Hàm này trả về 0.0 khi lỗi mà không báo gì, nên evaluator phải chặn trường hợp GFLOPs = 0.
- Không dùng kích thước file ``.pt``: Ultralytics lưu ``best.pt`` ở FP16 (``strip_optimizer``: ``x["model"].half()  # to FP16``).
- Code: ``ai/automation/complexity.py`` (``make complexity RUN=<run_id>``), báo lỗi nếu GFLOPs = 0.

.. _53-hardware-performance:

Hardware Performance
====================

.. code:: text

   Pre-processing latency
   Pure NPU inference latency (1 frame)
   Post-processing latency
   End-to-end latency
   FPS_latency = 1000 / E2E mean (tầng 2). Nếu tính từ tầng 1 thì = 1000 / NPU latency, ghi rõ tầng
   Throughput FPS (đo trên pipeline thật, ghi rõ số context/luồng và core_mask)

Hai loại FPS đo 2 thứ khác nhau, không đặt cạnh nhau như cùng một loại:

- **FPS_latency**: suy từ latency 1 frame. Latency đo bằng ``rknn.eval_perf()`` khi board kết nối PC, trong đó ``fix_freq=True`` (mặc định) cố định tần số phần cứng để đo lặp lại được (:download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`, API ``eval_perf``, trang PDF 18).
- **Throughput FPS**: số frame/giây của cả pipeline khi chạy nhiều context/luồng song song. Ví dụ DAHD-YOLO (:download:`dahd_yolo_rk3588_2025.pdf <../../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, tr.18): latency 1 ảnh 79.1 ms nhưng báo 50.2 FPS (trong khi 1000 / 79.1 ≈ 12.6), vì FPS đo với thread pool 3 core. Paper nguyên văn:

..

   "In Table 6, benefiting from the efficient scheduling of the NPU under the thread pool, the inference latency of the quantized model for a single image with a resolution of 1280 × 720 reaches 79.1 ms."

**Cách đo (khoá v1)**, chia 2 tầng:

.. list-table::
   :header-rows: 1

   * - Tầng
     - Đo gì
     - Cách đo
   * - 1. Từ PC
     - Latency NPU, thời gian từng layer, bộ nhớ NPU
     - ``eval_perf(fix_freq=True)`` qua board kết nối PC, 3 phiên ``init_runtime`` riêng (bảng dưới). Thời gian do phần cứng trên board đo, không bị ảnh hưởng bởi mạng. Code: ``ai/automation/benchmark_npu.py``
   * - 2. Trên board
     - Pre, NPU, post, E2E
     - Chạy trực tiếp trên board bằng ``rknn-toolkit-lite2``: 20 lần warmup, rồi 1 lượt qua toàn bộ ảnh ``sfchd_test``. Báo mean, P50, P95, std cho từng bước. Code: ``ai/board/bench_npu.py``

3 phiên của tầng 1 (khoá v1):

.. list-table::
   :header-rows: 1

   * - Phiên
     - ``init_runtime``
     - Lấy gì
     - Vì sao tách phiên
   * - 1
     - mặc định
     - NPU latency = median của 5 lần ``eval_perf`` (lưu cả 5 giá trị)
     - Đo thử ngày 2026-09-26 (INT8, 2 phiên × 5 lần): từng lần dao động 18.5–22.4 ms, median 2 phiên 19.25 và 19.56 ms
   * - 2
     - ``perf_debug=True``
     - Bảng từng layer: op, CPU/NPU, DDR/NPU cycles, thời gian
     - Chế độ debug in *"The performance result is just for debugging, may worse than actual performance!"*
   * - 3
     - ``eval_mem=True``
     - Bộ nhớ NPU (``eval_memory``)
     - Bắt buộc để ``eval_memory`` chạy (toolkit báo lỗi *"When init runtime, parameter <eval_mem> should be set to True"*). Đo thử: bật ``eval_mem`` làm ``eval_perf`` tăng từ 17.2 lên 22.9 ms

Định dạng output của bản 2.3.2 (lưu ở ``tests/fixtures/eval_perf_2.3.2_*.txt``, kiểm bằng ``make test-parsers``): phiên 1 in ``Total Time(us): <n>``, phiên 2 in ``Total Operator Elapsed Per Frame Time(us): <n>`` và bảng layer. ``fix_freq=True`` chuyển governor NPU và DDR sang ``userspace`` ở tần số tối đa (NPU 1 GHz, DDR 2112 MHz) và giữ nguyên sau khi đo.

Định nghĩa từng bước ở tầng 2 (khoá v1):

.. list-table::
   :header-rows: 1

   * - Bước
     - Gồm
     - Không gồm
   * - Pre
     - Resize + LetterBox + BGR→RGB, từ ảnh BGR đã giải mã trong RAM. Giống từng pixel input của evaluator (đã kiểm md5 trên 4 ảnh)
     - Đọc và giải mã file ảnh (pipeline camera không có bước này)
   * - NPU
     - ``RKNNLite.inference()``
     - 
   * - Post
     - NMS + đưa box về toạ độ ảnh gốc, theo mặc định **predict** của Ultralytics: conf 0.25, IoU 0.7, max_det 300, 1 class/box
     - NMS kiểu val (conf 0.001) chỉ dùng cho AI Quality
   * - E2E
     - Pre + NPU + Post
     - 

Post dùng conf 0.25 (``cfg/default.yaml``: *"defaults: predict=0.25, val=0.001"*) vì tầng 2 đo tốc độ lúc triển khai. Với conf 0.001 số box qua NMS lớn hơn nhiều và thời gian post không phản ánh lúc chạy thật.

- Không bấm giờ quanh ``rknn.inference()`` gọi từ PC: con số sẽ cộng cả thời gian truyền ảnh qua mạng.
- Tầng 2 dùng ảnh thật vì thời gian NMS phụ thuộc số object trong ảnh. So sánh NPU giữa các model thì dùng tầng 1, vì thời gian NPU không phụ thuộc nội dung ảnh.
- Khoá tần số CPU/DDR/NPU trước khi đo tầng 2, theo :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`, trang PDF 72–73. Tài liệu dùng governor ``userspace``, nhưng board này có sẵn governor ``performance`` cho cả CPU, NPU (``fdab0000.npu``) và DDR (``dmc``), giữ mọi clock ở tần số tối đa mà không cần đường debugfs, nên script ``ai/board/lock_freq.sh`` dùng ``performance``. Mọi file kết quả tầng 2 tự ghi governor và tần số trước/sau khi đo (``frequency_before``, ``frequency_after``, cờ ``locked``).
- Throughput FPS ghi rõ số context/luồng và ``core_mask``. Code: ``ai/board/bench_throughput.py`` (mỗi context 1 luồng Python, frame lấy từ 200 ảnh test đã giải mã sẵn trong RAM).

.. _54-resource--energy:

Resource & Energy
=================

.. code:: text

   RAM usage
   CPU utilization
   Thời gian từng layer, layer nào chạy CPU / NPU
   Temperature
   Power, Energy / frame (ngoài v1)

**Cách đo (khoá v1):**

- **RAM**: lấy mẫu ``VmRSS`` của process tầng 2 trong suốt lúc chạy, báo giá trị lớn nhất. Không dùng ``VmHWM`` vì man page Linux (``proc_pid_status(5)``) ghi *"This value is inaccurate"*. Bộ nhớ driver NPU cấp cho model có thể không tính trong RSS, nên lấy riêng bằng ``rknn.eval_memory()`` ở tầng 1, phiên 3 (``init_runtime(eval_mem=True)``) (:download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`, mục 2.10, trang PDF 19: *"Fetch memory usage when model is running on hardware platform"*, trả về ``weight_memory``, ``internal_memory``, ``other_memory``, ``total_memory``).
- **CPU utilization**: trung bình trong suốt tầng 2.
- **Thời gian từng layer, layer CPU/NPU**: tầng 1, ``eval_perf`` khi ``init_runtime(perf_debug=True)``. Toolkit2-API trang PDF 18:

..

   *"If the perf_debug is set to True, the running time of each layer will also be captured in detail."*

- **Nhiệt độ**: đọc lúc bắt đầu, kết thúc và lấy mẫu trong suốt tầng 2 từ thermal zone có ``type`` = ``npu-thermal`` (trên board này là ``/sys/class/thermal/thermal_zone6``, đã kiểm ngày 2026-09-26).
- **Power, Energy/frame**: chưa có cách đo đã kiểm chứng (cảm biến trên board hoặc thiết bị đo ngoài), nên để ngoài v1.

**Code của protocol v1 (đã có, chi tiết file và lệnh ở :ref:`Runbook <81-runbook>`):**

- ☒ Evaluator chung cho FP32 và NPU: ``ai/core/evaluator.py``, ``ai/core/backends.py``
- ☒ Bỏ ``measure_map_drop`` cũ trong ``ai/core/rknn/benchmark.py`` (lệch protocol ở 3 chỗ: ``cv2.resize`` kéo thẳng, NMS IoU 0.65, chỉ đọc ``*.jpg``). Accuracy NPU nay đo bằng evaluator với backend RKNN (inference trên board, NMS và AP trên PC, xem :ref:`AI Quality <51-ai-quality>`)
- ☒ Code tầng 2 trên board: ``ai/board/bench_npu.py``, ``bench_cpu_onnx.py``, ``bench_throughput.py``
- ☒ Golden test: ``ai/automation/check_evaluator.py``, số lưu ở ``ai/automation/golden/evaluator_v1.json``
