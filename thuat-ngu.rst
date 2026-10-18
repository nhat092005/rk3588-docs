:tocdepth: 1

*********
Thuật ngữ
*********

Vocabulary for the NPU deep-study material on the Orange Pi 5 (RK3588S). Names follow the vendor documents where the vendor is consistent."NPU" is the single word for the hardware.

Thuật ngữ dự án
===============

**NPU**: The hardware accelerator block on RK3588, made of 3 NPU cores. The TRM Chapter 36 calls this block "RKNN" and the Datasheet 1.2.6 calls it "Neural Process Unit". *Avoid*: RKNN (for the hardware), RKNPU2 (for the hardware)

**NPU core**: One of the 3 identical compute cores inside the NPU (Core0, Core1, Core2). Each has its own CNA, MAC array, accumulator, DPU, PPU and 384KB buffer (TRM Fig. 36-2). *Avoid*: RKNN core

**RKNPU**: Rockchip's NPU family shared across several chips (RK3566, RK3568, RK3588, RV1103, RV1106, RK3562), as used in the RKNN User Guide Section 1 and 2. Not the RK3588 hardware by itself. *Avoid*: using it as a synonym for the RK3588 NPU

**RKNPU2**: The board-side SDK: runtime, driver and C API (``rknn_api.h``). Corresponds to ``3rdparty/rknn-toolkit2/rknpu2/``. *Avoid*: using it for the hardware (Master Guide 0.3 and 0.0.3 were corrected to this on 2026-10-10)

**RKNPU driver**: Linux kernel driver in ``drivers/rknpu/`` that submits jobs to the NPU and exposes the ``/sys/kernel/debug/rknpu/`` nodes. Read-only reference copy: ``3rdparty/rknpu-driver-0.9.8/`` (version and commit in its ``SOURCE.txt``). Not the userspace SDK (that is RKNPU2). *Avoid*: RKNPU2 (for the kernel driver), "NPU driver" (ambiguous with the vendor RKNPU family)

**RKNN model**: The binary file with suffix ``.rknn`` that runs on the NPU (RKNN User Guide Section 3). *Avoid*: RKNN (standing alone)

**RKNN-Toolkit2**: Python package that converts and quantizes a model into an RKNN model and drives measurements on the board. Name kept as in Master Guide 0.0.3.

**RKNN-Toolkit-Lite2**: Python package on the board (pip name ``rknn-toolkit-lite2``, Python class ``RKNNLite``) that only loads and runs an existing RKNN model. Cannot convert or quantize. Vendor spellings: "RKNN-Toolkit Lite2" (User Guide V2.3.2 p.36), "RKNN-Toolkit-Lite2" (``3rdparty/rknn-toolkit2/README.md`` line 12). *Avoid*: RKNNLite2 (not a vendor name)

**librknnrt**: C runtime library (``librknnrt.so``) on the board that executes an RKNN model on the NPU.

**ConvExSwish**: Op name that ``eval_perf`` prints in its layer table for a Conv followed by SiLU that the compiler fused. Not assumed to be the same op as **ConvolutionSwish**, the name in the Operator List. *Avoid*: ConvolutionSwish (for a layer-table row), "Swish conv"

**Fused op**: A layer-table op that merges several ops of the source graph, for example ``ConvExSwish``, ``ConvRelu``, ``ConvReluAdd``. The source graph and the layer table have different op counts for the same model. *Avoid*: "merged layer", "combined op"

**Export path**: The chain ``export(format="rknn")`` of ``ultralytics``, which writes an ONNX graph (opset at most 19, simplified with ``onnxslim`` by default) and converts it with ``onnx2rknn``. The repo's own T3 builds used opset 12 without simplifying, so the ONNX op counts of the two differ. *Avoid*: "RKNN graph" (that is the layer table after conversion, not the ONNX)

**End-to-end head (``end2end``)**: The NMS-free ``Detect`` mode of YOLO26 that keeps a one-to-one branch next to the one-to-many branch and adds top-k selection to the graph. ``ultralytics`` turns it off for the ``rknn`` format, so the export path uses the one-to-many branch and needs NMS outside the graph. *Avoid*: "NMS-free model" (for the deployed RKNN graph)

**Evidence tier**: Label on every claim in the study material. T1 = vendor document or official source code. T2 = paper or whitepaper under ``_assets/pdf/papers/``. T3 = measurement we ran ourselves, with a script and a log under ``tmp/04_debug-logs/``, every T3 claim states its environment ("T3 board" or "T3 PC") and is not treated as a document. A claim without a tier is not written, a gap is marked ``unknown`` with a search query. *Avoid*: citing ``docs/_notes``, ``docs/outputs``, blogs, forums or recalled knowledge

**Docs repo**: The separate git repository ``rk3588-docs`` holding all Sphinx ``.rst`` sources, figures and reference PDFs (papers, datasheets). Mounted in this repo as a git submodule. Private, so PDFs may be stored in it. *Avoid*: "docs folder" (the old unstructured ``docs/``), "wiki"

**Triage**: One-time per-file decision made while moving old ``docs/`` content into the Docs repo: keep (convert to ``.rst``), rewrite (rebuild from the cited PDF), or delete. Content that cannot be traced to a PDF page is rewritten or deleted, never carried over as is. *Avoid*: "migration" (implies content is copied unchanged)

**Docs backup**: Frozen copy of the old ``docs/`` at ``tmp/docs_backup/`` (taken 2026-10-16, verified identical with ``diff -rq``). The only recovery source for the gitignored folders. Deleted once the Docs repo is accepted.

.. _00-bảng-chú-giải-thuật-ngữ:

Bảng chú giải thuật ngữ
=======================

Các thuật ngữ dùng xuyên suốt tài liệu, phân theo nhóm chuyên môn. Nguồn công thức Precision, Recall, F1, mAP: :download:`_assets/pdf/papers/07_ppe_detection/shel5k_helmet_2022otgonbold.pdf <_assets/pdf/papers/07_ppe_detection/shel5k_helmet_2022otgonbold.pdf>`, tr.8 (Equation 1-4).

.. _001-độ-đo-và-pipeline-computer-vision:

Độ đo và Pipeline Computer Vision
---------------------------------

.. list-table::
   :header-rows: 1

   * - STT
     - Thuật ngữ
     - Công thức / Định nghĩa
     - Ý nghĩa
   * - 1
     - TP / FP / FN
     - True Positive / False Positive / False Negative
     - TP: box dự đoán đúng lớp + IoU ≥ ngưỡng. FP: dự đoán sai (lớp sai hoặc IoU thấp). FN: object thật bị bỏ sót
   * - 2
     - Precision
     - TP ÷ (TP + FP)
     - Trong số box mô hình dự đoán, bao nhiêu % là đúng (ít báo nhầm)
   * - 3
     - Recall
     - TP ÷ (TP + FN)
     - Trong số object thật có trong ảnh, mô hình tìm ra được bao nhiêu % (ít bỏ sót)
   * - 4
     - F1 Score
     - 2 × (Precision × Recall) ÷ (Precision + Recall)
     - Trung bình điều hòa Precision/Recall, cân bằng cả 2
   * - 5
     - IoU
     - Diện tích giao ÷ diện tích hợp của 2 box
     - Đo độ trùng khớp giữa box dự đoán và box ground-truth. Ngưỡng 0.5 nghĩa là chồng lấn ≥50% mới tính là đúng
   * - 6
     - AP
     - Diện tích dưới đường cong Precision-Recall của 1 class
     - Độ chính xác tổng hợp cho riêng 1 class, tại 1 ngưỡng IoU
   * - 7
     - mAP
     - Trung bình AP qua tất cả class
     - Độ chính xác tổng thể của mô hình trên toàn bộ class
   * - 8
     - mAP@0.5 (mAP50)
     - mAP tính tại ngưỡng IoU = 0.5
     - Cách đo phổ biến nhất, khoan dung hơn (chỉ cần chồng lấn 50%)
   * - 9
     - mAP@0.5:0.95 (mAP50-95)
     - Trung bình mAP qua các ngưỡng IoU 0.5 → 0.95, bước 0.05
     - Khắt khe hơn, phạt cả box lệch vị trí dù đúng lớp (theo chuẩn COCO)
   * - 10
     - LetterBox
     - Resize ảnh về khung vuông (vd 640×640) mà không bóp méo
     - Giữ tỉ lệ khung hình gốc, phần thiếu tô viền màu xám (114, 114, 114)
   * - 11
     - NMS
     - Non-Maximum Suppression
     - Bước hậu xử lý loại bớt các box trùng nhau trên cùng 1 object, giữ box có score cao nhất

.. _002-tối-ưu-hóa-mô-hình-và-lượng-tử-hóa:

Tối ưu hóa mô hình và Lượng tử hóa
----------------------------------

.. list-table::
   :header-rows: 1

   * - STT
     - Thuật ngữ
     - Công thức / Định nghĩa
     - Ý nghĩa
   * - 1
     - Params
     - Số tham số học được của model (triệu, M)
     - Tỉ lệ thuận với dung lượng file model
   * - 2
     - FLOPs / MACs
     - Floating-point Operations / Multiply-Accumulate operations
     - Ước lượng khối lượng tính toán lý thuyết, KHÔNG đồng nghĩa với latency thật trên NPU (mục 1). Ultralytics tính GFLOPs = MACs × 2 (:ref:`Model Complexity <52-model-complexity>`)
   * - 3
     - PTQ
     - Post-Training Quantization
     - Lượng tử hoá model đã train xong (FP32 → INT8), không train lại, chỉ cần 1 bộ ảnh calibration nhỏ
   * - 4
     - QAT
     - Quantization-Aware Training
     - Train lại model có mô phỏng lượng tử hoá ngay trong lúc train để model thích nghi với INT8, tốn công hơn PTQ

.. _003-phần-mềm-và-phần-cứng-rknpu-rockchip:

Phần mềm và Phần cứng RKNPU Rockchip
------------------------------------

.. list-table::
   :header-rows: 1

   * - STT
     - Thuật ngữ
     - Công thức / Định nghĩa
     - Ý nghĩa
   * - 1
     - RKNPU2
     - Bộ SDK phía board của Rockchip cho NPU: runtime ``librknnrt``, ``rknn_server``, C API ``rknn_api.h``
     - Không phải package Python, tương ứng thư mục ``3rdparty/rknn-toolkit2/rknpu2/``
   * - 2
     - librknnrt
     - Thư viện C runtime (``librknnrt.so``) trên board, thực thi model trên NPU
     - RKNN-Toolkit-Lite2 gọi trực tiếp. RKNN-Toolkit2 khi điều khiển board từ PC thì đi qua ``rknn_server`` trên board rồi mới tới thư viện này
   * - 3
     - RKNN-Toolkit2
     - Package Python để convert/quantize model sang ``.rknn``, và điều khiển board từ xa để đo
     - Có bản x86_64 và arm64. Project dùng bản x86_64 trên PC, kết nối board qua mạng
   * - 4
     - RKNN-Toolkit-Lite2 (``rknn-toolkit-lite2``, lớp Python ``RKNNLite``)
     - Package Python chạy trên board (bản aarch64), chỉ load và chạy model ``.rknn`` có sẵn
     - Không convert/quantize được, tên gần giống RKNN-Toolkit2 nhưng khác hẳn chức năng
   * - 5
     - core_mask
     - Tham số chọn core NPU chạy model: tự động (``AUTO``), 1 core (``CORE_0``), hoặc gộp nhiều core (``CORE_0_1_2``)
     - Đặt lúc gọi ``init_runtime()``, không phải lúc build model (``ai/core/rknn/benchmark.py``)
   * - 6
     - NPU, NPU core
     - NPU là khối phần cứng tăng tốc gồm 3 NPU core trên RK3588 (TRM Part1 Chương 36, tr.1984: "Include triple NPU CORE". TRM gọi khối này là "RKNN")
     - Dùng "NPU" cho phần cứng, "RKNPU2" chỉ SDK phía board (dòng 1), còn "RKNPU" là tên họ NPU của Rockchip dùng chung nhiều chip

.. _004-đánh-giá-hiệu-năng-và-hệ-thống:

Đánh giá hiệu năng và Hệ thống
------------------------------

.. list-table::
   :header-rows: 1

   * - STT
     - Thuật ngữ
     - Công thức / Định nghĩa
     - Ý nghĩa
   * - 1
     - FPS
     - Frames Per Second
     - Số ảnh xử lý được mỗi giây. Có 2 loại không so trực tiếp được với nhau: FPS_latency và Throughput FPS (:ref:`Hardware Performance <53-hardware-performance>`)
   * - 2
     - P50 / P95
     - Percentile 50 (trung vị) / Percentile 95
     - Với dãy số đo lặp lại (vd latency): P50 là giá trị ở giữa, 95% số lần đo thấp hơn P95. P95 cho biết mức chậm của những frame chậm, không chỉ trung bình
   * - 3
     - VmRSS / VmHWM
     - RAM thật (Resident Set Size) process đang dùng / mức cao nhất từng dùng
     - Đọc từ ``/proc/<pid>/status`` trên Linux. Man page ``proc_pid_status(5)`` ghi về VmHWM: *"This value is inaccurate"*, nên lấy mẫu VmRSS liên tục (:ref:`Resource & Energy <54-resource--energy>`)
   * - 4
     - Golden test
     - Bài test đối chiếu với số liệu đã lưu
     - Chạy evaluator trên 1 bộ ảnh và 1 model cố định. Nếu ra số khác số đã lưu nghĩa là code evaluator vừa bị đổi (:ref:`Evaluation Protocol v1 <50-evaluation-protocol-v1>`)
