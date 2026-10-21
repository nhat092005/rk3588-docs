:tocdepth: 1

***********************************
Toolkit trên PC và Lite2 trên board
***********************************

.. admonition:: Trang này trả lời

   - một model ``.rknn`` được chạy thử ở đâu trong lúc phát triển?
   - phía board chạy model bằng gì và dựa vào thư viện nào?
   - hai đường (Toolkit2 trên PC, Lite2 trên board) khác nhau ở điểm nào?

.. admonition:: Tóm tắt

   - UG232 phân biệt ba cách suy luận: simulator trên Linux x86_64, board nối PC (Python API của Toolkit2) và on-board bằng RKNPU2 C API [T1 UG232 tr.171].
   - ``init_runtime(target=None)`` chạy simulator. Đặt ``target='rk3588'`` thì chạy trên NPU của board nối PC [T1 API232 tr.16] [T1 API232 tr.17].
   - Board nối PC đi qua ``rknn_server`` trên board. Phiên bản ARM64 của Toolkit2 không dùng ``rknn_server`` và ``adb`` [T1 UG232 tr.11] [T1 UG232 tr.16].
   - Board nối PC có hiệu năng thấp hơn on-board bằng C API vì phải truyền dữ liệu. UG232 coi số liệu NPU thực là số đo bằng C API [T1 UG232 tr.171].
   - RKNN-Toolkit Lite2 là giao diện Python để suy luận trên board. Lite2 và RKNPU2 C API cùng dựa vào ``librknnrt.so`` [T1 UG232 tr.36] [T1 UG232 tr.155].
   - Lite2 không có simulator, không convert và không có ``eval_perf``, ``eval_memory``, ``accuracy_analysis`` trong mã ``rknn_lite.py`` [T1 EX rknnlite/api/rknn_lite.py:133] [T1 EX rknnlite/api/rknn_lite.py:13].
   - ``core_mask`` hợp lệ cho RK3576 và RK3588. Lite2 dùng tiền tố ``RKNNLite.``, Toolkit2 dùng ``RKNN.`` [T1 UG232 tr.39] [T1 UG232 tr.73].
   - Lite2 có cần ``rknn_server`` hay không: unknown (mục 3).

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _toolkit-pc-api-simulator:

1. Toolkit2 trên PC
===================

Nền. RKNN-Toolkit2 là bộ công cụ Python chạy trên máy tính. Nó convert model, lượng tử hóa, suy luận thử, đo hiệu năng và bộ nhớ, phân tích độ chính xác theo từng lớp và mã hóa model [T1 UG232 tr.7] [T1 UG232 tr.8]. Luồng convert ở :doc:`01-luong-onnx-sang-rknn`. Trang này nói về phần chạy thử và nối board.

.. _fig-rknn-software-stack:

.. figure:: ../../../_assets/img/npu/05_toolchain/ug232_p7_fig1-1.png
   :align: center
   :alt: Ngăn xếp phần mềm RKNN từ model framework qua RKNN-Toolkit2 đến AI Apps, RKNN API, RKNPU Driver, RKNPU Hardware

   Ngăn xếp phần mềm RKNN. Model từ framework đi qua RKNN-Toolkit2 trên PC, model ``.rknn`` chạy trên board qua AI Apps, RKNN API, RKNPU Driver và RKNPU Hardware. Nguồn: [T1 UG232 tr.7, Figure 1-1]

Toolkit2 có hai bản, x86 và ARM64. Bản ARM64 chỉ convert được model ONNX và PyTorch, không có ``adb`` và ``rknn_server`` [T1 UG232 tr.11].

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Mục
     - x86
     - ARM64
     - Nguồn
   * - ONNX, PyTorch
     - có
     - có
     - [T1 UG232 tr.11]
   * - Caffe, TensorFlow, TF Lite, DarkNet
     - có
     - không
     - [T1 UG232 tr.11]
   * - ``adb``, ``rknn_server``
     - có
     - không
     - [T1 UG232 tr.11]
   * - rknn runtime (``librknnrt.so``)
     - có
     - có
     - [T1 UG232 tr.11]

Ở bản ARM64, các chức năng debug như suy luận và phân tích độ chính xác chỉ cần ``librknnrt.so`` nằm ở ``/usr/lib64``. Chúng chạy ngay trên board đó vì không có ``adb`` [T1 UG232 tr.11]. Bản x86 cần cập nhật và chạy ``rknn_server`` trên board, đồng thời ``adb`` phải dùng được [T1 UG232 tr.11].

UG232 định nghĩa ba cách suy luận:

   "Simulator inference: RKNN-Toolkit2 provides a simulator function on the Linux x86_64 platform, which can perform model inference and obtain inference results without a development board." [T1 UG232 tr.171]

..

   "Inference with board-connected: When the board is connected to the PC, use the RKNN-Toolkit2 Python API to infer the model and obtain the inference results." [T1 UG232 tr.171]

   "On-board inference: using RKNPU2's C API interface to obtain inference results." [T1 UG232 tr.171]

1.1 API và simulator
--------------------

Bảng dưới xếp các API theo việc cần board hay không.

.. list-table::
   :header-rows: 1
   :widths: 24 50 12 14

   * - API
     - Việc làm
     - Cần board
     - Nguồn
   * - ``RKNN()``, ``release()``
     - Tạo và giải phóng đối tượng. Phải gọi ``RKNN()`` trước mọi API khác
     - không
     - [T1 API232 tr.6]
   * - ``config``, ``load_onnx``, ``build``, ``export_rknn``
     - Các bước convert, xem trang trước
     - không
     - [T1 API232 tr.6] [T1 API232 tr.15]
   * - ``load_rknn``
     - Nạp model đã build. Không cần config, load, build. Model nạp theo cách này chỉ dùng được với phần cứng nối PC, không dùng cho simulator hay phân tích độ chính xác
     - có
     - [T1 API232 tr.15]
   * - ``init_runtime(target=None)``
     - Chạy simulator. Phải gọi ``build`` hoặc ``hybrid_quantization`` trước
     - không
     - [T1 API232 tr.16]
   * - ``init_runtime(target='rk3588', device_id, perf_debug, eval_mem, core_mask, fallback_prior_device)``
     - Chạy trên phần cứng. ``perf_debug`` bật thời gian từng lớp. ``eval_mem`` bật chế độ đo bộ nhớ. ``fallback_prior_device`` mặc định ``cpu``
     - có
     - [T1 API232 tr.16] [T1 API232 tr.17]
   * - ``inference``
     - Suy luận trên phần cứng nếu có ``target``, ngược lại trên simulator. ``data_format`` mặc định coi mọi đầu vào là ``nhwc``
     - tùy ``target``
     - [T1 API232 tr.17]
   * - ``eval_perf``, ``eval_memory``
     - Đo hiệu năng và bộ nhớ. Model phải chạy trên phần cứng nối PC
     - có
     - [T1 API232 tr.18] [T1 API232 tr.19]
   * - ``accuracy_analysis``
     - ``target`` mặc định ``None`` thì chỉ dùng simulator. Có ``target`` thì lấy kết quả từng lớp lúc chạy trên board
     - tùy ``target``
     - [T1 UG232 tr.30]
   * - ``list_devices``
     - Liệt kê thiết bị nối PC ở hai chế độ ADB và NTB
     - có
     - [T1 API232 tr.23]

Simulator có ba đặc điểm đáng nhớ.

- Chạy trên Linux x86_64, không cần board [T1 UG232 tr.171].
- Khi không lượng tử hóa, simulator tính bằng FP16 vì RKNPU chưa hỗ trợ FP32. Muốn mô phỏng FP16, build với ``do_quantization=False`` rồi gọi ``init_runtime(target=None)`` [T1 UG232 tr.131].
- Kết quả không bảo đảm giống board. UG232 viết "The output result of this function may not be consistent with the board end" và khuyến nghị dùng board nối PC hoặc on-board [T1 UG232 tr.171]. Mức lệch cụ thể là unknown (mục 3).

UG232 đặt simulator ở thứ tự đầu của quy trình gỡ lỗi độ chính xác: phải đúng trên simulator rồi mới xét kết quả trên board [T1 UG232 tr.131]. Quy trình đầy đủ ở :doc:`../02-rknn-luong-tu-hoa/03-hybrid-va-accuracy-analysis`.

Board nối PC hoạt động như sau theo UG232. Toolkit2 trao đổi với ``rknn_server`` trên board, gửi model và đầu vào sang board, rồi gọi RKNPU2 C API ở đó, kết quả gửi ngược về PC [T1 UG232 tr.171]. ``rknn_server`` là dịch vụ nền nhận lệnh từ máy tính qua USB và thực thi giao diện runtime tương ứng [T1 UG232 tr.16]. Phiên bản ``rknn_server``, ``librknnrt.so`` và Toolkit2 phải khớp nhau [T1 UG232 tr.17]. Việc khởi động, cập nhật ``rknn_server`` và cấu hình ``adb`` ở :doc:`03-driver-rknpu-va-rknn-server`. Nhật ký chi tiết khi board nối PC chủ yếu sinh ở phía board [T1 UG232 tr.171].

Hai hệ quả về hiệu năng:

   "Since inference with board-connected involves additional data copying and transmission processes, the performance is not as good as the on-board inference with RKNPU2 C API." [T1 UG232 tr.171]

UG232 giải thích thêm: ``rknn.inference`` chậm hơn ``rknn.eval_perf`` vì ``inference`` dùng PC và ``adb`` nên có phần chi phí truyền dữ liệu cố định [T1 UG232 tr.175]. Hãng khuyên dùng C API trực tiếp trên board để có tốc độ khung hình thực tế [T1 UG232 tr.175]. ``eval_perf`` có tham số ``fix_freq`` mặc định ``True`` [T1 API232 tr.18], UG232 mô tả là cố gắng cố định tần số CPU, NPU và DDR [T1 UG232 tr.31]. Cách cố định thực hiện qua node nào là unknown (mục 3).

Ví dụ số (suy ra từ API232). Mẫu đầu ra ``eval_memory`` của ví dụ ``caffe/mobilenet_v2`` trên RK3588 có ``weight_memory`` 3698688 byte, ``internal_memory`` 1756160, ``other_memory`` 484352 và ``total_memory`` 5939200 [T1 API232 tr.19]. Cộng ba thành phần: :math:`3698688 + 1756160 + 484352 = 5939200`, khớp với tổng. Chia cho :math:`1024^2` ra khoảng 5.66 MiB, khớp dòng ``Total Memory: 5.66 MiB`` ở cùng trang.

Mẫu chuẩn cho RK3588 trong SDK là ``examples/functions/npu_device_test/test.py``. File đặt ``target_platform='rk3588'`` (dòng 30), gọi ``accuracy_analysis(..., target='rk3588')`` (52), ``list_devices()`` (89), ``init_runtime(target='rk3588', perf_debug=True, eval_mem=True)`` (93), ``get_sdk_version()`` (100), ``eval_perf()`` (105), ``eval_memory()`` (109) và ``inference(...)`` (113) [T1 EX examples/functions/npu_device_test/test.py:30] [T1 EX examples/functions/npu_device_test/test.py:93].

.. _lite2-librknnrt-tren-board:

2. Lite2 và librknnrt trên board
================================

Nền. Runtime là thư viện nạp model và gọi driver NPU để chạy model [T1 UG232 tr.8]. Trên RK3588 thư viện này là ``librknnrt.so`` (RV1103 và RV1106 dùng ``librknnmrt.so``) [T1 UG232 tr.17]. RKNN-Toolkit Lite2 bọc runtime đó bằng giao diện Python:

   "RKNN-Toolkit Lite2 provides users with a Python interface for board-side model inference, making it convenient for users to use Python language for AI application development." [T1 UG232 tr.36]

Điều kiện chạy theo UG232: Debian 10 hoặc 11 (aarch64), Python 3.7 đến 3.11, phụ thuộc ``numpy``, ``ruamel.yaml``, ``psutils`` [T1 UG232 tr.36]. Gói cài là file ``.whl`` trong thư mục ``rknn-toolkit-lite2/packages`` của SDK [T1 UG232 tr.36] [T1 UG232 tr.37]. Thư mục này của bản 2.3.2 có thêm gói ``cp312`` [T1 EX rknn-toolkit-lite2/packages/]. Changelog ghi Lite2 cài được bằng pip từ v2.3.0 [T1 EX CHANGELOG.md:19]. Model phải được convert trước bằng Toolkit2 [T1 UG232 tr.36].

.. _fig-lite2-flow:

.. figure:: ../../../_assets/img/npu/05_toolchain/ug232_p37_fig3-5.png
   :align: center
   :alt: Lưu đồ dùng RKNN-Toolkit Lite2: tạo RKNNLite, load_rknn, init_runtime, inference, release

   Lưu đồ dùng Lite2 trên board: tạo ``RKNNLite``, ``load_rknn``, ``init_runtime``, ``inference``, ``release``. Nguồn: [T1 UG232 tr.37, Figure 3-5]

Các API Lite2 theo UG232 gồm ``RKNNLite()``, ``load_rknn``, ``init_runtime``, ``inference``, ``get_sdk_version`` và ``list_support_target_platform`` [T1 UG232 tr.38] [T1 UG232 tr.39] [T1 UG232 tr.40]. Mã ``rknn_lite.py`` của wheel 2.3.2 có các hàm ``load_rknn``, ``list_devices``, ``init_runtime``, ``inference``, ``get_sdk_version``, ``list_support_target_platform``, ``release`` và không có ``eval_perf``, ``eval_memory``, ``accuracy_analysis`` [T1 EX rknnlite/api/rknn_lite.py:57] [T1 EX rknnlite/api/rknn_lite.py:81] [T1 EX rknnlite/api/rknn_lite.py:266]. Khi ``target`` là ``None`` và máy không phải ``aarch64`` hay ``armv7l``, ``init_runtime`` in lỗi "RKNN Toolkit Lite2 does not support simulator, please specify the target" [T1 EX rknnlite/api/rknn_lite.py:133].

Quan hệ với ``librknnrt.so`` và các tệp hệ thống, theo phần chạy trong Docker của UG232:

   "/usr/lib/librknnrt.so is the Runtime file. RKNN-Toolkit Lite2 and RKNPU2 C API relies on this file to use NPU resources." [T1 UG232 tr.155]

Cùng trang nêu thêm ``/dev/dri/renderD129`` là node NPU của RK3588 mà runtime dựa vào, và ``/proc/device-tree/compatible`` ghi mã SoC mà các thành phần như Lite2 đọc để biết SoC hiện tại [T1 UG232 tr.155]. Model build bởi Toolkit2 phiên bản 2.0.0 hoặc 2.1.0 cần runtime cùng hoặc mới hơn (``>=2.0.0``, ``>=2.1.0``) [T1 UG232 tr.155]. Hàng 2.3.x không có trong bảng đó (unknown), nên dùng quy tắc chung: giữ ``rknn_server``, runtime và Toolkit2 cùng phiên bản [T1 UG232 tr.17].

Chọn lõi NPU bằng ``core_mask`` của ``init_runtime``:

.. list-table::
   :header-rows: 1
   :widths: 24 12 44 20

   * - Giá trị
     - Số nguyên
     - Ý nghĩa
     - Nguồn
   * - ``NPU_CORE_AUTO``
     - 0
     - Tự lập lịch, chạy trên lõi đang rảnh. Mặc định
     - [T1 UG232 tr.39] [T1 EX rknnlite/api/rknn_lite.py:15]
   * - ``NPU_CORE_0``, ``_1``, ``_2``
     - 1, 2, 4
     - Chạy trên một lõi
     - [T1 UG232 tr.39] [T1 EX rknnlite/api/rknn_lite.py:16-18]
   * - ``NPU_CORE_0_1``
     - 3
     - Chạy cùng lúc lõi 0 và 1
     - [T1 UG232 tr.39] [T1 EX rknnlite/api/rknn_lite.py:19]
   * - ``NPU_CORE_0_1_2``
     - 7
     - Chạy cùng lúc ba lõi
     - [T1 UG232 tr.39] [T1 EX rknnlite/api/rknn_lite.py:20]
   * - ``NPU_CORE_ALL``
     - 0xffff
     - Số lõi tùy nền tảng
     - [T1 UG232 tr.39] [T1 EX rknnlite/api/rknn_lite.py:21]

Các số nguyên là bitmask (suy ra từ giá trị): lõi 0, 1, 2 lần lượt là bit 1, 2, 4, nên ``0_1`` là :math:`1 + 2 = 3` và ``0_1_2`` là :math:`1 + 2 + 4 = 7`. Tham số này chỉ hợp lệ cho RK3576 và RK3588 [T1 UG232 tr.39] [T1 API232 tr.17]. RK3576 chỉ có hai lõi nên không đặt được ``NPU_CORE_2`` và ``NPU_CORE_0_1_2`` [T1 API232 tr.17]. Ở Lite2 phải ghi ``RKNNLite.NPU_CORE_AUTO``, ở Toolkit2 ghi ``RKNN.NPU_CORE_AUTO`` [T1 UG232 tr.73].

Lịch sử trong changelog Lite2: ``NPU_CORE_0_1`` và ``NPU_CORE_0_1_2`` được thêm ở v1.4.0, ``NPU_CORE_ALL`` và hỗ trợ RK3576 ở v2.0.0b0 [T1 EX rknn-toolkit-lite2/CHANGELOG.txt:43] [T1 EX rknn-toolkit-lite2/CHANGELOG.txt:20] [T1 EX rknn-toolkit-lite2/CHANGELOG.txt:21].

Đa lõi không phải lúc nào cũng nhanh hơn:

   "Multi-core operation is suitable for networks with a large amount of calculations. A little improvement for small networks, and may even lead to performance degradation due to single-core and multi-core switching (this switching requires CPU intervention)." [T1 UG232 tr.72]

Chỉ một số op được chia tác vụ đa lõi: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, LeakyRelu [T1 UG232 tr.75]. Trang :doc:`04-operator-list` ghi cột "多核联合" cho từng op của RK3588.

.. _khac-biet-hai-duong-chay:

3. Khác biệt giữa hai đường
===========================

.. list-table::
   :header-rows: 1
   :widths: 22 34 34 10

   * - Tiêu chí
     - Toolkit2 trên PC
     - Lite2 trên board
     - Nguồn
   * - Chạy ở đâu
     - Linux x86_64, hoặc ARM64 Linux với bản ARM64
     - Board aarch64, Debian 10 hoặc 11
     - [T1 UG232 tr.11] [T1 UG232 tr.36]
   * - Convert và lượng tử hóa
     - Có
     - Không, chỉ nạp và chạy model ``.rknn`` có sẵn
     - [T1 UG232 tr.7] [T1 UG232 tr.36]
   * - Simulator
     - Có (``target=None``)
     - Không, báo lỗi nếu thiếu ``target`` trên máy không phải ARM
     - [T1 API232 tr.16] [T1 EX rknnlite/api/rknn_lite.py:133]
   * - Đường tới NPU
     - Qua ``rknn_server`` và ``adb`` trên board (bản x86)
     - Gọi ``librknnrt.so`` ngay trên board (suy ra từ UG232 tr.155, tr.36)
     - [T1 UG232 tr.171] [T1 UG232 tr.155]
   * - Đo hiệu năng, bộ nhớ, độ chính xác
     - ``eval_perf``, ``eval_memory``, ``accuracy_analysis``
     - Không có trong ``rknn_lite.py``
     - [T1 API232 tr.18] [T1 EX rknnlite/api/rknn_lite.py:266]
   * - Tiền tố ``core_mask``
     - ``RKNN.``
     - ``RKNNLite.``
     - [T1 UG232 tr.73]
   * - Chữ ký ``inference``
     - ``inputs``, ``data_format``, ``inputs_pass_through``
     - Thêm ``data_type`` và ``get_frame_id`` trong mã
     - [T1 API232 tr.17] [T1 API232 tr.18] [T1 EX rknnlite/api/rknn_lite.py:193]
   * - Tốc độ so với C API
     - Thấp hơn do truyền dữ liệu qua PC
     - Không có nguồn so sánh với C API (unknown)
     - [T1 UG232 tr.171]

Cả hai đường dùng chung hai thứ: file ``.rknn`` do Toolkit2 tạo và ``librknnrt.so`` làm runtime [T1 UG232 tr.36] [T1 UG232 tr.155]. Khi board nối PC, phần suy luận thực chất chạy RKNPU2 C API trên board, nên kết quả về lý thuyết giống C API. Nếu lệch nhiều thì kiểm tra tiền xử lý đầu vào, kiểu dữ liệu và cách sắp xếp NCHW hay NHWC [T1 UG232 tr.171].

Điều chưa rõ:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Câu hỏi
     - Trạng thái
   * - Lite2 trên board có cần ``rknn_server`` không
     - unknown. UG232 chỉ nói đường board nối PC của Toolkit2 cần ``rknn_server`` (tr.16, tr.171) và Lite2 dựa vào ``librknnrt.so`` (tr.155). Suy ra Lite2 không cần, chưa có câu trực tiếp. Đã tìm ở: UG232, API232, UG152, ``rknn_lite.py``, từ khóa: ``rknn_server``, ``Lite2``
   * - Mức lệch giữa simulator và board
     - unknown. UG232 tr.171 chỉ nói "may not be consistent". Đã tìm ở: UG232 tr.131 đến tr.135 và tr.171, từ khóa: ``simulator``
   * - NTB khác ADB ở điểm nào
     - unknown. API232 tr.23 chỉ nêu có hai chế độ và phải dùng cùng chế độ khi nối nhiều thiết bị. Đã tìm ở: UG232, API232, ``rknn_server_proxy.md``, từ khóa: ``NTB``
   * - ``fix_freq`` cố định tần số qua cơ chế nào
     - unknown. UG232 tr.31 chỉ mô tả mục đích. Đã tìm ở: UG232, API232, từ khóa: ``fix_freq``
   * - Cách Lite2 tìm ``librknnrt.so`` (thứ tự đường dẫn)
     - unknown. UG232 tr.155 chỉ nêu ``/usr/lib/librknnrt.so``. Đã tìm ở: UG232, ``rknn_lite.py``, từ khóa: ``librknnrt``
   * - Tốc độ Lite2 so với C API
     - unknown. UG232 tr.171 và tr.175 so board nối PC với C API. Đã tìm ở: UG232, từ khóa: ``Lite2``

Các chỗ tài liệu chưa nhất quán, đã nêu để không hiểu nhầm:

- UG232 tr.11 và tr.12 mô tả bản ARM64 của Toolkit2, còn mục hỏi đáp tr.156 đến tr.157 trả lời "No ARM Linux version". Changelog ghi Toolkit2 hỗ trợ ARM64 từ v2.3.0 [T1 EX CHANGELOG.md:17]. Suy ra mục hỏi đáp là nội dung cũ.
- Tên gọi: chuỗi "RKNNLite2" không có trong nguồn đã đọc. Các nguồn dùng "RKNN-Toolkit Lite2", "RKNN-Toolkit-Lite2", lớp ``RKNNLite`` và gói ``rknn_toolkit_lite2``. Xem :doc:`/thuat-ngu`.
- Chú thích trong ``rknn_lite.py`` ghi ``NPU_CORE_0_1`` là "core 1 and core 2" và ``NPU_CORE_0_1_2`` là "core 1 and core 2 and core 3" [T1 EX rknnlite/api/rknn_lite.py:19] [T1 EX rknnlite/api/rknn_lite.py:20]. Đánh số này lệch với UG232 tr.39 (lõi 0, 1, 2). Dùng UG232 và API232.
- Danh sách Python của Lite2 ở UG232 tr.36 dừng ở 3.11 trong khi thư mục gói có ``cp312`` (xem mục 2).

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 50 22

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Lite2 chạy được model trên PC bằng simulator
     - Lite2 báo lỗi không hỗ trợ simulator khi ``target`` là ``None`` trên máy không phải ARM. Simulator là của Toolkit2 bản x86
     - [T1 EX rknnlite/api/rknn_lite.py:133] [T1 UG232 tr.171]
   * - Tốc độ ``rknn.inference`` trên PC phản ánh tốc độ NPU
     - Có chi phí truyền dữ liệu cố định. UG232 coi số đo bằng C API trên board là hiệu năng thực
     - [T1 UG232 tr.171] [T1 UG232 tr.175]
   * - ``eval_perf`` chạy được trên simulator
     - Model phải chạy trên phần cứng nối PC
     - [T1 API232 tr.18]
   * - ``librknnrt.so`` chỉ dành cho chương trình C
     - Lite2 cũng dựa vào file này để dùng NPU
     - [T1 UG232 tr.155]
   * - Toolkit2 không có bản ARM64
     - Có bản ARM64, chỉ convert ONNX và PyTorch, không có ``adb`` và ``rknn_server``
     - [T1 UG232 tr.11] [T1 EX CHANGELOG.md:17]
   * - Bật đa lõi luôn nhanh hơn
     - Model nhỏ cải thiện ít và có thể chậm đi vì chuyển đổi đơn lõi và đa lõi cần CPU
     - [T1 UG232 tr.72]

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 75
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 22
   * - ``EX``
     - T1
     - Ví dụ, changelog và gói trong SDK. Đường dẫn ``examples/...`` tính từ ``3rdparty/rknn-toolkit2/rknn-toolkit2/``. ``CHANGELOG.md``, ``rknn-toolkit-lite2/CHANGELOG.txt`` và ``rknn-toolkit-lite2/packages/`` tính từ ``3rdparty/rknn-toolkit2/``. ``rknnlite/api/rknn_lite.py`` là file nằm trong wheel ``rknn_toolkit_lite2-2.3.2-cp310`` của thư mục ``packages``. Số sau dấu hai chấm là số dòng
     - 26

Số trang UG232 và API232 là số trang PDF, trùng số in. Các Figure 1-1 và Figure 3-5 lấy từ UG232 và nằm ở ``_assets/img/npu/05_toolchain/``.
