:tocdepth: 1

********************
Luồng ONNX sang RKNN
********************

.. admonition:: Trang này trả lời

   - các bước nào biến một file ONNX thành file ``.rknn``?
   - một model ``.rknn`` chạy ở đâu trong quá trình phát triển?

.. admonition:: Tóm tắt

   - Luồng chuyển đổi gồm config, nạp model, rknn.build() và rknn.export_rknn() để tạo file .rknn [T1 UG232 tr.9].
   - Phải đặt target_platform='rk3588'. Nếu không, model chỉ chạy được trên RK3566/RK3568 [T1 UG232 tr.173].
   - Ví dụ yolov5/test.py mặc định target_platform='rk3566' và gọi init_runtime() không có target, nên suy luận chạy trên simulator.
   - target=None chạy trên simulator, đặt target='rk3588' chạy trên NPU của board nối PC [T1 API232 tr.16, 17].
   - Board-connected có hiệu năng thấp hơn on-board inference bằng RKNPU2 C API vì truyền dữ liệu qua adb [T1 UG232 tr.171].
   - Mức lệch của simulator so với board và cách NTB khác ADB là unknown, phiên bản ONNX giữa API232 và UG232 chưa có nguồn phân xử.

.. _51-luồng-chuyển-onnx-sang-rknn-model:

Luồng chuyển ONNX sang RKNN model
=================================

**Câu hỏi:** các bước nào biến một file ONNX thành file ``.rknn``?

**Nguồn nói gì**

   "Model Configuration: Fill in the necessary configuration parameters in RKNN-Toolkit2, such as mean values, normalization, quantization option, target platform, etc." [T1 UG232 tr.9]

..

   "Model Building: Build the RKNN model using the rknn.build() interface. Users can choose whether to perform quantization to improve the model's performance on the hardware." [T1 UG232 tr.9]

   "Model Export: Export the RKNN model as a file (.rknn format) using the rknn.export_rknn() interface for future deployment." [T1 UG232 tr.9]

..

   "Before the RKNN model is built, the model needs to be configured first through the config interface." [T1 API232 tr.6]

   "Load ONNX model. Parameter model: The path of ONNX model file (suffixed with ".onnx")." [T1 API232 tr.12]

..

   "Save RKNN model in the specified file (suffixed with ".rknn")." [T1 API232 tr.15]

   "when target_platform in the rknn.config() interface is not set, the generated RKNN model can only run on RK3566/RK3568." [T1 UG232 tr.173]

..

   "RK3588's RKNN model can be used on RK3588s." [T1 UG232 tr.158]

   "python -m rknn.api.rknn_convert -t rk3588 -i ./model_config.yml -o ./output_path" [T1 UG232 tr.25]

Ví dụ chính thức ``examples/onnx/yolov5/test.py`` gọi theo thứ tự: ``RKNN(verbose=True)`` (dòng 238), ``rknn.config(...)`` (242), ``rknn.load_onnx(...)`` (247), ``rknn.build(...)`` (255), ``rknn.export_rknn(...)`` (263).

|UG232 Figure 3-1| *Hình 5.1. Luồng chuyển đổi model: RKNN init, config, load_xxx, build, export_rknn, release. Nguồn: [T1 UG232 tr.21, Figure 3-1]*

**Ý chính**

- Thứ tự trong tài liệu là: khởi tạo, ``config``, nạp model, ``build``, ``export_rknn``, ``release`` (UG232 tr.9, tr.21). Tổng hợp của file này: mọi nguồn và ví dụ đã đọc đều đặt ``config`` trước ``load_onnx``. API232 tr.6 chỉ nói "Before the RKNN model is built" và không cấm thứ tự ngược.
- Phải đặt ``target_platform='rk3588'``. Nếu không, model chỉ chạy được trên RK3566 và RK3568 (UG232 tr.173).
- Model đã build cho RK3588 dùng được trên RK3588S (UG232 tr.158), khớp với board Orange Pi 5.
- Ngoài API Python còn có công cụ dòng lệnh ``rknn_convert`` đọc file YAML (UG232 tr.25).

**Giới hạn**

- Ví dụ ``examples/onnx/yolov5/test.py:242`` mặc định ``target_platform='rk3566'`` và ``:271`` gọi ``init_runtime()`` không có ``target``, nên suy luận chạy trên simulator (xem 5.2). Phải sửa cả hai khi dùng cho RK3588.
- Phiên bản framework: API232 tr.5 ghi ONNX "1.7.0 ~1.17.0", UG232 tr.21 ghi "recommended version is 1.7.0~1.10.0". Cả hai giá trị đều được nêu ở trên, chưa có nguồn nào phân xử.

--------------

.. _52-toolkit-trên-pc-api-simulator-và-board-kết-nối:

Toolkit trên PC: API, simulator và board kết nối
================================================

**Câu hỏi:** một model ``.rknn`` chạy ở đâu trong quá trình phát triển?

**Nguồn nói gì**

   "The RKNN() must be called before using all the API interfaces of RKNN-Toolkit2, and call the release() method to release the object when task finished." [T1 API232 tr.6]

..

   "means model runs on simulator. Note: When target is set to None, the build or hybrid_quantization interface needs to be called first." [T1 API232 tr.16]

   "If the target is set to Rockchip NPU when initializing the runtime environment, the inference of model is performed on the specified hardware platform. If the target is not set, the inference of model is performed on the simulator." [T1 API232 tr.17]

..

   "the loaded model is limited to connecting to the NPU hardware for inference or performance data acquisition. It can not be used for simulator or accuracy analysis." [T1 API232 tr.15]

   "perf_debug: Debug mode option for performance evaluation. In debug mode, the running time of each layer can be obtained, otherwise, only the total running time of model can be given." [T1 API232 tr.16]

..

   "fix_freq: Whether to fix hardware frequency. The default value is True." [T1 API232 tr.18]

   "There are currently two device connection modes: ADB and NTB. Make sure their modes are the same when connecting multiple devices." [T1 API232 tr.23]

Ba chế độ suy luận (UG232 tr.171):

   "Simulator inference: RKNN-Toolkit2 provides a simulator function on the Linux x86_64 platform, which can perform model inference and obtain inference results without a development board." [T1 UG232 tr.171]

..

   "Inference with board-connected: When the board is connected to the PC, use the RKNN-Toolkit2 Python API to infer the model and obtain the inference results." [T1 UG232 tr.171]

   "On-board inference: using RKNPU2's C API interface to obtain inference results." [T1 UG232 tr.171]

..

   "Since inference with board-connected involves additional data copying and transmission processes, the performance is not as good as the on-board inference with RKNPU2 C API." [T1 UG232 tr.171]

   "rknn.inference is slower than rknn.eval_perf Because rknn.inference uses PC & adb for inference with board-connected, there is some fixed data transmission overhead, which is inconsistent with the theoretical speed of rknn.eval_perf." [T1 UG232 tr.175]

|UG232 Figure 1-1| *Hình 5.2a. Ngăn xếp phần mềm RKNN: model từ framework, RKNN-Toolkit2 trên PC, rồi RKNN model chạy qua AI Apps, RKNN API, RKNPU Driver, RKNPU Hardware. Nguồn: [T1 UG232 tr.7, Figure 1-1]*

|UG232 Figure 1-2| *Hình 5.2b. Cấu trúc RKNN-Toolkit2: Frontend Loader, Graph Optimizer (Const Fold, OP Fuse, OP Convert), Quantizer, Compiler (OP Fuse, Tiling, Memory Planning, RKNN Generator), Debugger (Inference, Accuracy Analysis, Performance Eval, Memory Usage Eval). Nguồn: [T1 UG232 tr.7, Figure 1-2]*

Mẫu chuẩn cho RK3588: ``examples/functions/npu_device_test/test.py`` có ``target_platform='rk3588'`` (dòng 30), ``accuracy_analysis(..., target='rk3588')`` (52), ``list_devices()`` (89), ``init_runtime(target='rk3588', perf_debug=True, eval_mem=True)`` (93), ``get_sdk_version()`` (100), ``eval_perf()`` (105), ``eval_memory()`` (109), ``inference(...)`` (113).

**Ý chính**

- ``target=None`` nghĩa là chạy trên simulator trên PC. đặt ``target='rk3588'`` thì chạy trên NPU của board nối với PC (API232 tr.16, 17).
- ``eval_perf`` và ``eval_memory`` chỉ có khi model chạy trên phần cứng nối PC, không có simulator (API232 tr.18, 19).
- Hiệu năng đo qua board-connected thấp hơn so với chạy trực tiếp trên board bằng C API vì có truyền dữ liệu qua adb (UG232 tr.171, 175). Tổng hợp của file này: con số FPS dùng báo cáo nên đo bằng C API trên board, còn ``eval_perf`` dùng để phân tích từng lớp. UG232 tr.171, 175 chỉ so board-connected với C API. đường chạy RKNN-Toolkit-Lite2 (Python) trên board không được so sánh trong các trang này.
- Hình Figure 1-2 vẽ toolkit có khối Compiler với OP Fuse, Tiling, Memory Planning. Tài liệu không mô tả thuật toán của chúng (xem :doc:`Toolchain và compiler </contents/01-kien-thuc-nen/04-toolchain-compiler/index>`).

**Giới hạn**

- Simulator "không đảm bảo kết quả giống hệt board" (UG232 tr.171). Mức lệch là ``unknown``.
- UG232 tr.31 mô tả ``fix_freq`` là "try to fix the frequency of the hardware (including CPU/NPU/DDR)", chỉ cách đặt qua node nào là ``unknown``.
- Giao thức NTB khác ADB thế nào: ``unknown`` (API232 tr.23 chỉ nêu có hai chế độ).

--------------

.. |UG232 Figure 3-1| image:: ../../../_assets/img/npu/05_toolchain/ug232_p21_fig3-1.png

.. |UG232 Figure 1-1| image:: ../../../_assets/img/npu/05_toolchain/ug232_p7_fig1-1.png

.. |UG232 Figure 1-2| image:: ../../../_assets/img/npu/05_toolchain/ug232_p7_fig1-2.png

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 14
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 10
