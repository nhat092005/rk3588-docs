************
Chuẩn int8h5
************

.. admonition:: Trang này trả lời

   - Chuẩn INT8 mới ``int8h5`` là gì, xuất và kiểm chứng thế nào, và nó khác ``int8`` mặc định ở đâu?
   - Lệnh nào tái lập từng kết quả của giai đoạn 2 và dữ liệu, mã phân tích nằm ở đâu?
   - Điều kiện thiết bị, quyết định đã chốt và điều chưa làm là gì?

.. admonition:: Tóm tắt

   - ``int8h5`` là INT8 mặc định của Ultralytics với đúng 15 tensor của nhánh giải mã box giữ FP16 (công thức ``h5`` ở :doc:`05-ket-qua-luong-tu-hoa`). Nhãn ``PREC=int8h5``, thư mục ``weights/rknn_int8h5/``, tệp ``export_int8h5.json``. ``int8`` mặc định và mọi kết quả của nó không đổi (sha256 của file seed 0 trước và sau khi xuất giống nhau).
   - Xuất bằng ``make export-npu PREC=int8h5`` cho đúng danh sách tensor và AP50-95 của bản dựng thử ``h5`` (chênh 0.00 điểm trên ``css_test``). File xuất có sha256 khác bản dựng thử, nên latency được đo lại.
   - ``css_test`` AP50-95 của ``int8h5``: SiLU seed 0, 1, 2 là 49.66, 50.79, 50.69 (FP16: 49.76, 51.01, 51.00, ``int8``: 36.75, 38.10, 37.74), ReLU seed 0 là 46.98 (FP16 46.49).
   - Latency của ``int8h5`` so với ``int8`` (P2, một lần chạy xen kẽ): SiLU ``CORE_0`` -0.103 ms, ReLU ``CORE_0_1_2`` -0.109 ms, độ phủ đa nhân của ReLU 98.8%.
   - ``int8h5`` đã nối vào ``ai/automation/pipeline.py``, ``tables.py`` (Bảng F) và ``make benchmark-npu`` và ``bench-board`` (2026-11-01). Mọi số là 1 seed mỗi model, latency chính thức dưới P2 (đã duyệt, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Quyết định đã chốt
=====================

Các quyết định của người dùng trong giai đoạn 2 (ngày 2026-10-31), ghi lại vì không nằm ở trang kết quả nào khác:

.. list-table::
   :header-rows: 1
   :widths: 20 90 34

   * - Quyết định
     - Nội dung
     - Nơi áp dụng
   * - Giao thức latency
     - P2 dùng cho điều kiện B của G4 và S1, ngưỡng 5% giữ nguyên. P2 và P3 được người dùng duyệt nguyên trạng ngày 2026-11-01 (:doc:`/contents/09-tien-do/02-quyet-dinh/02-duyet-giao-thuc-p2-p3`)
     - :doc:`01-ket-qua-g4`, :doc:`03-ket-qua-da-nhan`
   * - Seed và mAP
     - ReLU seed 0 so baseline seed 0, nhãn 1 seed. mAP chấm bằng RKNNLite trên board (INT8 kết luận, FP16 tham chiếu, FP32 mô tả). Sau đó mở rộng: thêm ReLU seed 1, 2 để mô tả nhiễu
     - :doc:`01-ket-qua-g4`
   * - Biến thể activation
     - Làm đủ LeakyReLU, ReLU6, ReLU 200 epoch kèm đối chứng SiLU 200 epoch (Hardswish, GELU, Mish không thử vì không nằm trong danh sách op đa nhân của T1)
     - :doc:`02-ket-qua-bien-the-activation`
   * - Chẩn đoán lượng tử hóa
     - Làm tuần tự: tài liệu, chẩn đoán từng lớp, công thức, rồi QAT và kiến trúc thân thiện lượng tử hóa (người dùng duyệt ngày 2026-10-31 và đã chạy)
     - :doc:`05-ket-qua-luong-tu-hoa`, :doc:`07-ket-qua-qat-kien-truc`
   * - Chuẩn INT8
     - ``int8h5`` là nhãn mới song song với ``int8`` (không thay thế)
     - mục 2 trang này
   * - Quản lý repo
     - Không commit, không push. ``tmp/`` giữ nguyên (bị ``.gitignore``), trọng số ``weights/rknn_*`` cũng bị ``.gitignore`` và chỉ có sha256 trong ``export_*.json``
     - toàn bộ

Nguồn của bảng: các quyết định này được ghi từ hội thoại với người dùng, không có tệp quyết định riêng ngoài các quy tắc ``rule*.txt`` viết trước dữ liệu (xác nhận từng phép đo, P2 và P3 viết khi chưa duyệt và được duyệt ngày 2026-11-01) và ``results/phase2b_variants_design.md``. Sổ theo dõi ở ``tmp/`` bị ``.gitignore``.

2. Chuẩn int8h5
===============

``int8h5`` dùng cùng ONNX có tọa độ box chuẩn hóa mà bộ xuất Ultralytics đưa cho toolkit (xem ``baseline.py`` và ``hybrid.py``), cùng cấu hình (mean 0, std 255, mặc định của toolkit) và cùng danh sách hiệu chuẩn như ``int8`` (``--calib-from`` danh sách của seed 0, ``stems_md5`` ``11d6a5c69414a6eafd8b98f99724b0b2``, ``png_md5`` ``6652576adb7608ddf8ff326c57851732``). Khác biệt duy nhất là 15 tensor giữ FP16 qua ``hybrid_quantization_step1`` và ``step2`` (API V2.3.2 tr.20 đến 21, tên tensor trong ``custom_quantize_layers``, UG V2.3.2 tr.124): bốn tensor ``dfl/Reshape_output_0``, ``dfl/Transpose_output_0_sw``, ``dfl/Softmax_output_0_sw``, ``dfl/Reshape_1_output_0_rs``, rồi ``Slice_output_0-rs``, ``Slice_1_output_0-rs``, ``Sub_output_0-rs``, ``Add_1_output_0-rs``, ``Sub_1_output_0-rs``, ``Add_2_output_0-rs``, ``Div_1_output_0-rs``, ``Concat_2_output_0-rs``, ``/Div_output_0-rs``, ``output0-rs``, ``output0_int8``. Mã dùng chung ở ``ai/core/rknn/hybrid.py`` (có ``assert`` đúng 15 tensor), ``ai/core/rknn/baseline.py`` và ``ai/automation/export_npu.py`` (cờ ``--recipe h5``). ``build_recipe.py`` (công thức chẩn đoán ``h1`` đến ``h6`` và ``c_all``) dùng cùng mã công thức. ``diagnose_quant.py`` chỉ dựng INT8 mặc định và chạy ``accuracy_analysis``, không dùng ``hybrid.py``.

Lệnh chuẩn (``CALIB_FROM`` mặc định là ``ppe5_yolov8n_baseline_100ep_s0``):

.. list-table::
   :header-rows: 1
   :widths: 24 100

   * - Việc
     - Lệnh
   * - Xuất
     - ``make export-npu RUN=<run> PREC=int8h5``
   * - Chấm mAP trên board
     - ``make evaluate RUN=<run> BACKEND=rknn PREC=int8h5 BOARD=<ssh>``
   * - Đo latency tầng 1
     - ``make benchmark-npu RUN=<run> PREC=int8h5 CORE_MASK=<mask>`` (chưa chạy thử qua Make, ``benchmark_npu.py --precision int8h5`` đã chạy trực tiếp trong ``onboard_q2i``)
   * - Đo trên board tầng 2
     - ``make bench-board RUN=<run> PREC=int8h5`` (chưa chạy thử)

Kiểm chứng (quy tắc viết trước ``bench/onboard_q2c/rule_int8h5.txt``): V-1, bản xuất chuẩn có cùng 15 tensor FP16 với bản dựng thử và AP50-95 ``css_test`` chênh 0.00 điểm (giới hạn 0.5 điểm là số mới chưa duyệt), kết quả: export reproduces h5. V-2, sha256 của ``weights/rknn_int8`` seed 0 (so với hằng số viết trong quy tắc trước khi xuất, tệp có thời điểm sửa 2026-10-30) trước và sau khi xuất giống nhau. V-3 (mô tả, ``css_test``, điểm):

.. list-table::
   :header-rows: 1
   :widths: 14 10 10 10 16 16 24 22

   * - Run
     - int8
     - int8h5
     - FP16
     - int8h5 trừ int8
     - int8h5 trừ FP16
     - AP NoHelmet: int8h5 trừ FP16
     - AP Vest: int8h5 trừ FP16
   * - SiLU seed 0
     - 36.75
     - 49.66
     - 49.76
     - +12.91
     - -0.10
     - -2.09
     - -0.04
   * - SiLU seed 1
     - 38.10
     - 50.79
     - 51.01
     - +12.69
     - -0.22
     - -0.57
     - -0.42
   * - SiLU seed 2
     - 37.74
     - 50.69
     - 51.00
     - +12.95
     - -0.31
     - +0.99
     - +0.11
   * - ReLU seed 0
     - 33.24
     - 46.98
     - 46.49
     - +13.74
     - +0.49
     - +0.87
     - +1.68

Khoảng trải AP50-95 giữa ba seed SiLU: ``int8h5`` 1.13 điểm, ``int8`` 1.35, FP16 1.25. Ở AP NoHelmet khoảng trải của ``int8h5`` (3.70 điểm) lớn hơn của FP16 (0.62), ở AP Vest (3.98) gần FP16 (4.36). Ba seed chưa đủ để nói chênh ở AP NoHelmet là nhiễu hay khác biệt.

3. Latency và đa nhân của int8h5
================================

Một lần chạy xen kẽ 16 phiên dưới P2 (``bench/onboard_q2i``, quy tắc viết trước ``bench/onboard_q2i/rule.txt``): SiLU và ReLU seed 0, ``int8`` và ``int8h5``, ``CORE_0`` và ``CORE_0_1_2``, hai vòng cùng thứ tự. Cả 16 phiên thực hiện đúng P2. Vì đo lại file xuất chuẩn nên số này thay cho số của bản dựng thử ở :doc:`05-ket-qua-luong-tu-hoa`, hai số cùng cỡ.

.. list-table::
   :header-rows: 1
   :widths: 8 14 12 14 14 12 24 8

   * - Model
     - Mask
     - int8 (ms)
     - int8h5 (ms)
     - Chi phí (ms)
     - Chi phí (%)
     - Chênh hai phiên lớn nhất (ms)
     - Từ 5%
   * - SiLU
     - ``CORE_0``
     - 16.684
     - 16.581
     - -0.103
     - -0.62
     - 0.006
     - không
   * - SiLU
     - ``CORE_0_1_2``
     - 16.148
     - 16.045
     - -0.103
     - -0.64
     - 0.002
     - không
   * - ReLU
     - ``CORE_0``
     - 12.995
     - 12.886
     - -0.110
     - -0.85
     - 0.013
     - không
   * - ReLU
     - ``CORE_0_1_2``
     - 8.663
     - 8.554
     - -0.109
     - -1.26
     - 0.010
     - không

Điều kiện B: ReLU ``int8h5`` 33.6% (``int8``: 33.3%), SiLU ``int8h5`` 3.2%. Điều kiện A: ReLU ``int8h5`` 98.8%, SiLU 1.8%. Bảng layer dùng để kiểm tổng cycles của ``int8h5`` là bảng của bản dựng thử ``h5`` cùng đồ thị (log xuất của ``int8h5`` được ghi khi ``RKNN`` chạy ở chế độ không in bảng, đã sửa trong ``hybrid.py`` cho các lần xuất sau). Op CPU ngoài ``InputOperator`` và ``OutputOperator``: ['Transpose'].

4. Tái lập từng kết quả
=======================

.. list-table::
   :header-rows: 1
   :widths: 24 60 36 28 8

   * - Kết quả
     - Chạy
     - Dữ liệu và quy tắc
     - Phân tích
     - Trang
   * - Nhiễu seed, cổng C
     - ``make evaluate RUN=<run> BACKEND=rknn PREC=int8`` (SiLU seed 0, 1, 2 và ReLU)
     - ``bench/eval_g4/rule*.txt``, ``eval/``
     - ``analyze_g4c.py``
     - 10, 12
   * - Cổng A, B (G4), S1
     - ``bench/onboard_g4b/g4b_driver.py`` (cần helper P2)
     - ``bench/onboard_g4b/``
     - ``analyze_g4.py``
     - 10, 11
   * - Latency biến thể
     - ``bench/onboard_g4v*/g4v_driver.py`` (thí nghiệm 1, 2)
     - ``bench/onboard_g4v/``, ``onboard_g4v2/``
     - ``analyze_g4v.py [--sub onboard_g4v2]``
     - 12
   * - Throughput S2, S3
     - ``bench/onboard_thr/thr_driver.py`` (cần helper P3)
     - ``bench/onboard_thr/``
     - ``analyze_thr.py``
     - 11
   * - Chẩn đoán từng lớp
     - ``diagnose_quant.py <run> --images calib:<dir> test:<dir> --n 5 --out <dir>``
     - ``bench/onboard_q2c/diag/``, ``rule_diag.txt``
     - ``analyze_q2c_diag.py``
     - 13
   * - Công thức lượng tử hóa
     - ``build_recipe.py <run> <recipe>``, rồi ``evaluate.py --variant <recipe>``
     - ``bench/onboard_q2c/``, ``rule_recipes.txt``
     - ``analyze_q2c_recipes.py``
     - 13
   * - Chi phí ``h5``
     - ``bench/onboard_q2h/q2h_driver.py``, ``bench/onboard_q2i/q2i_driver.py``
     - ``bench/onboard_q2h/``, ``onboard_q2i/``
     - ``analyze_q2h.py``, ``analyze_q2i.py``
     - 13, 14
   * - Chuẩn ``int8h5``
     - ``make export-npu PREC=int8h5``, ``make evaluate PREC=int8h5``
     - ``bench/onboard_q2c/rule_int8h5.txt``
     - ``analyze_int8h5.py``
     - 14
   * - Mọi trang sinh
     - ``.venv/bin/python docs/tools/gen_phase2_results_pages.py``
     - ``results/*.json``
     - (có ``assert`` mỗi số)
     - 10 đến 14

5. Điều kiện thiết bị và công cụ
================================

- **Helper trên board.** ``ai/board/lock_freq.sh`` (khóa tần số), ``bench/onboard_x4/x4_hold.sh`` (giao thức P2) và ``bench/onboard_thr/p3_hold.sh`` (giao thức P3) trong thư mục chạy của seed 0 được cài thành bản root-owned ở ``/usr/local/sbin`` kèm một tệp ``/etc/sudoers.d/rk3588-measure`` cho phép chạy đúng ba script này không cần mật khẩu. Bản trong repo là nguồn: sửa xong phải cài lại bằng ``sudo install -o root -g root -m 755 <file> /usr/local/sbin/`` trong một terminal có tty. Helper ghi trạng thái vào ``~/x4`` hoặc ``~/p3`` (script tự tạo thư mục, xóa sau khi đo là việc làm tay), và khôi phục affinity ngắt, ``irqbalance`` rồi đọc lại khi kết thúc.
- **Một việc board mỗi lần.** Chấm mAP trên board không chạy cùng lúc với phép đo thời gian.
- **Bộ chấm.** ``ai/core/evaluator.py`` truyền ``max_time_img=60`` cho NMS. Giá trị cũ của Ultralytics (2 giây cộng 0.05 giây mỗi ảnh) cắt NMS khi hàng nghìn hộp qua ngưỡng 0.001. Kết quả cũ không đổi (chấm lại bốn dump).
- **Hiệu chuẩn.** Mọi export INT8 của seed 1, 2, ReLU và các biến thể dùng ``--calib-from ppe5_yolov8n_baseline_100ep_s0`` (seed 0 là nguồn, tự lấy mẫu với ``seed`` 0 và 20 ảnh mỗi class, md5 danh sách tính lại cho cùng giá trị). ``make export-npu PREC=int8h5`` đặt ``--calib-from`` mặc định, ``PREC=int8`` không truyền cờ này. Sampler ``ai/core/rknn/calibration.py`` đã sửa (``sorted``), có ``tests/test_calibration.py``, nhưng export cũ của seed 0 không bị sửa. Export cũ của seed 1 giữ tên ``rknn_int8_ownlist``. Từ 2026-11-01 ``make export-npu PREC=int8 CALIB_FROM=<run>`` truyền ``--calib-from`` (không có ``CALIB_FROM`` thì lấy mẫu mới như trước) và ``pipeline.py`` truyền ``CALIB_FROM`` cho cả ``int8`` và ``int8h5``.
- **Bộ nhớ.** ``mmse`` với 300 ảnh bị hệ điều hành dừng (máy 15.6 GB). Dựng thử ``kl`` chạy dưới ``systemd-run --user --scope -p MemoryMax=9G`` (``rule_recipes.txt``), các lần dựng công thức sau đó dưới ``MemoryMax=11G``.
- **ONNX FP32 của run.** Mỗi lần chạy ``export_npu.py`` (kể cả ``int8h5``) xuất lại ``weights/best.onnx``. Xuất ONNX không tất định theo byte: hai lần xuất cùng trọng số seed 0 cho hai sha256 khác nhau, cùng 233 nút và cùng histogram op. Vì vậy ``onnx_sha256`` ghi trong ``export_int8.json`` cũ khác sha hiện tại của ``best.onnx`` ở cả bốn run, và khớp với ``export_int8h5.json`` mới. Không mã nào trong repo so ``onnx_sha256`` (``tables.py`` chỉ kiểm ``rknn_sha256``). Bảng H dùng ONNX này cho cột CPU của board, đồ thị không đổi.
- **Kiểm sau khi chuyển mã.** Sau khi chuyển logic công thức sang ``hybrid.py`` và bật ``verbose``, ``build_hybrid`` được dựng thử trực tiếp (không ghi đè file đã đo) cho 15 tên tensor và in bảng layer. Các file ``int8h5`` và ``rknn_int8_h5`` đã đo được dựng trước thay đổi đó. Log xuất ``int8h5`` của seed 0 (chạy trực tiếp ``export_npu.py``) không được giữ, log của seed 1, 2 và ReLU nằm trong ``runs/<run>/logs/``.
- **Bằng chứng ngoài git.** Trọng số ``.rknn`` và ``tmp/`` không vào git. Mỗi mô hình có ``export_*.json`` (sha256, danh sách hiệu chuẩn, tensor FP16). Cấu hình lượng tử hóa bước 1 ở ``bench/onboard_q2c/step1_silu.quantization.cfg`` và ``step1_relu.quantization.cfg``, log quét thử của các công thức ở ``bench/onboard_q2c/logs/``.

6. Điều chưa làm
================

- Đã làm 2026-11-01: ``pipeline.py`` có bước ``int8h5`` cho phase3 và phase4 (model không có DFL, ví dụ ``nodfl``, bỏ qua vì công thức ``h5`` cần 4 tensor DFL). ``tables.py`` sửa ba lỗi sẵn có để ``make tables DATASET=ppe5`` chạy được: danh sách ``CLASSES`` cũ lệch tên class ppe5 (nay đọc từ yaml dataset), thư mục nhãn của tập ``ppe2286_ext`` (nay theo tên split) và run 200 epoch ghi đè run 100 epoch cùng seed trong cùng một hàng model (nay là hàng riêng ``_200ep``). Hàng ``INT8H5`` của Bảng F khớp số đã biết (trung bình ba seed của SiLU 50.38 AP50-95 trên ``css_test``). ``make benchmark-npu PREC=int8h5`` và ``make bench-board PREC=int8h5`` đã chạy một lần trên board (không dưới P2).
- Đã sửa 2026-11-01: ``MODELS`` của ``pipeline.py`` có ``yolov8s_baseline`` nhưng thư mục ``configs`` không có ``ppe5_yolov8s_baseline.yaml``, nên ``phase2`` và ``phase4`` lỗi ``FileNotFoundError``. Nay ``models_for(ds)`` chỉ lấy model có config, ``phase2``, ``phase3`` và ``phase4`` dựng được danh sách bước cho ppe5.
- Latency của ``int8h5`` với seed khác chưa đo. Ngoài P2 có một phiên ``make benchmark-npu`` ``CORE_0`` (20.513 ms, trung vị 5 lần, một phiên, không chạy helper P2, chỉ để kiểm đường Make. Trang :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3` dùng nó làm ví dụ cỡ số, không phải kết luận).
- Nguyên nhân giữ FP16 nhánh giải mã box lấy lại điểm vẫn chưa biết (:doc:`05-ket-qua-luong-tu-hoa` mục 7).
- QAT và kiến trúc thân thiện lượng tử hóa đã chạy một seed ở :doc:`07-ket-qua-qat-kien-truc`. Còn chưa làm: A2 tách đầu, QAT với torch 1.10 đến 1.13.1, thời gian NPU của bản QAT.
- Mã mới chưa được commit. ``tests`` mới: ``test_calibration``, ``test_throughput_rep``.

