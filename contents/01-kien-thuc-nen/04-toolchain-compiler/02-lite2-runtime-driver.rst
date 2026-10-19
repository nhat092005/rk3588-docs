:tocdepth: 1

************************
Lite2, runtime và driver
************************

.. admonition:: Trang này trả lời

   - phía board chạy RKNN model bằng gì?
   - làm sao biết phiên bản driver, tải và nguồn của NPU?
   - PC nói chuyện với board như thế nào?

.. admonition:: Tóm tắt

   - Board chạy RKNN model bằng Python qua RKNN-Toolkit-Lite2 hoặc bằng C qua RKNPU2 C API, cả hai dựa trên librknnrt.so [T1 UG232 tr.155].
   - RKNN-Toolkit-Lite2 chỉ nạp và chạy model có sẵn, không có simulator, và core_mask hợp lệ cho RK3576 và RK3588 [T1 API232 tr.17].
   - Đa lõi giúp ít với model nhỏ và có thể làm chậm hơn [T1 UG232 tr.72].
   - Khuyến nghị driver RKNPU ">= 0.9.2" [T1 UG232 tr.16], node load không biểu diễn trực tiếp MAC utilization [T1 UG232 tr.137].
   - Lite2 có cần rknn_server hay không là unknown, suy luận rằng không cần chưa có T3 và không có câu T1 nói trực tiếp.
   - Bản RKNN-Toolkit2 ARM64 chạy trực tiếp trên board không cần rknn_server hay adb, còn bản x86_64 cần, phiên bản rknn_server, librknnrt và Toolkit2 phải khớp nhau [T1 UG232 tr.17].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _53-rknn-toolkit-lite2-và-librknnrt-trên-board:

RKNN-Toolkit-Lite2 và librknnrt trên board
==========================================

**Câu hỏi:** phía board chạy RKNN model bằng gì?

**Nguồn nói gì**

   "RKNN-Toolkit Lite2 provides users with a Python interface for board-side model inference, making it convenient for users to use Python language for AI application development." [T1 UG232 tr.36]

..

   "RKNN-Toolkit-Lite2 provides Python programming interfaces for Rockchip NPU platform to help users deploy RKNN models and accelerate the implementation of AI applications." [T1 README.md:12]

   "RKNN Runtime is mainly responsible for loading the RKNN model and calling the NPU driver to infer the RKNN model on the NPU." [T1 UG232 tr.8]

..

   "RKNPU2 Runtime library (librknnrt.so): The main responsibility is to load the RKNN model in the system and perform inference operations of the RKNN model by calling a dedicated neural processing unit (NPU)." [T1 QS232 tr.15]

   "librknnrt.so: The Runtime library for RK3562/RK3566/RK3568/RK3576/RK3588/RV1126B development boards." [T1 UG232 tr.17]

..

   "The init_runtime must call before model inference." [T1 UG232 tr.38]

   "core_mask: Sets the NPU cores at runtime. The supported platform is RK3588 / RK3576" [T1 API232 tr.17]

..

   "Note: This parameter is only valid for RK3576/RK3588" [T1 UG232 tr.39]

   "When setting this parameter on RKNN-Toolkit Lite2, RKNNLite must be added in front of the value, such as RKNNLite.NPU_CORE_AUTO; if this parameter is set on RKNN-Toolkit2, RKNN must be added in front of the value, such as RKNN.NPU_CORE_AUTO." [T1 UG232 tr.73]

..

   "Multi-core operation is suitable for networks with a large amount of calculations. A little improvement for small networks, and may even lead to performance degradation due to single-core and multi-core switching (this switching requires CPU intervention)." [T1 UG232 tr.72]

   "The existing operators that support multi-core task segmentation include: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu." [T1 UG232 tr.75]

Code:

.. list-table::
   :header-rows: 1

   * - Nguồn
     - Nội dung
   * - ``rknn_lite.py:13``
     - ``class RKNNLite:``
   * - ``rknn_lite.py:57``
     - ``def load_rknn(self, path):``
   * - ``rknn_lite.py:115``
     - ``def init_runtime(self, target=None, device_id=None, async_mode=False, core_mask=NPU_CORE_AUTO):``
   * - ``rknn_lite.py:133-137``
     - nếu ``target is None`` và máy không phải aarch64 hoặc armv7l thì báo lỗi "RKNN Toolkit Lite2 does not support simulator, please specify the target"
   * - ``rknn_api.h:246-256``
     - ``RKNN_NPU_CORE_AUTO = 0``, ``_CORE_0 = 1``, ``_CORE_1 = 2``, ``_CORE_2 = 4``, ``_CORE_0_1``, ``_CORE_0_1_2``, ``_CORE_ALL = 0xffff``
   * - ``rknn-toolkit-lite2/examples/resnet18/test.py:75, 79, 94, 104, 110``
     - ``RKNNLite()``, ``load_rknn(...)``, ``init_runtime(core_mask=RKNNLite.NPU_CORE_0)``, ``inference(inputs=[img])``, ``release()``

|UG232 Figure 3-5| *Hình 5.3. Luồng dùng RKNN-Toolkit Lite2 trên board: tạo ``RKNNLite``, ``load_rknn``, ``init_runtime``, ``inference``, ``release``. Nguồn: [T1 UG232 tr.37, Figure 3-5]*

**Ý chính**

- Hai đường chạy trên board: Python qua RKNN-Toolkit-Lite2, hoặc C qua RKNPU2 C API. Cả hai dựa trên ``librknnrt.so`` (UG232 tr.155: "RKNN-Toolkit Lite2 and RKNPU2 C API relies on this file to use NPU resources").
- RKNN-Toolkit-Lite2 chỉ nạp và chạy model có sẵn, không convert và không có simulator (``rknn_lite.py:133-137``. UG232 tr.36). ``rknn_lite.py`` chỉ có các hàm ``load_rknn``, ``list_devices``, ``init_runtime``, ``inference``, ``get_sdk_version``, ``list_support_target_platform``, ``release``: không có ``eval_perf`` và ``eval_memory``.
- ``core_mask`` chọn NPU core, hợp lệ cho RK3576 và RK3588 (API232 tr.17. UG232 tr.39). Thêm tiền tố ``RKNNLite.`` cho Lite2, ``RKNN.`` cho Toolkit2 (UG232 tr.73).
- Đa lõi giúp ít với model nhỏ và có thể làm chậm hơn (UG232 tr.72).

**Giới hạn**

- Tên: chuỗi "RKNNLite2" không xuất hiện trong nguồn T1 nào. Các nguồn dùng "RKNN-Toolkit Lite2", "RKNN-Toolkit-Lite2", lớp ``RKNNLite`` và gói pip ``rknn-toolkit-lite2`` (xem :doc:`/thuat-ngu`).
- Phạm vi chip của ``core_mask`` khác theo phiên bản tài liệu: UG152 tr.26 "it only works at the RK3588", API232 tr.17 "RK3588 / RK3576".
- Comment trong ``rknn_lite.py:19`` (``NPU_CORE_0_1``: "core 1 and core 2") và ``:20`` (``NPU_CORE_0_1_2``: "core 1 and core 2 and core 3") đánh số core lệch so với API232 tr.17 và ``rknn_api.h``. Dùng API232 và ``rknn_api.h``.
- Lite2 dựa vào ``/usr/lib/librknnrt.so`` (UG232 tr.155: "RKNN-Toolkit Lite2 and RKNPU2 C API relies on this file to use NPU resources"). Thứ tự và cách Lite2 tìm thư viện (biến ``LIBRKNNRT_PATH`` chỉ có dưới dạng chuỗi trong binary) là ``unknown``.
- Lite2 có cần ``rknn_server`` hay không: ``unknown``, không có câu trực tiếp.

--------------

.. _54-driver-rknpu-và-các-node-trạng-thái:

Driver rknpu và các node trạng thái
===================================

**Câu hỏi:** làm sao biết phiên bản driver, tải và nguồn của NPU?

**Nguồn nói gì**

   "It is recommended that the RKNPU driver version is >= 0.9.2." [T1 UG232 tr.16]

..

   "RKNPU kernel driver is responsible for interacting with NPU hardware. It has been open source and can be found in the Rockchip kernel code." [T1 README.md:16]

   "/dev/dri/renderD129 is RK3588's NPU device node. Runtime relies on this node to enable NPU." [T1 UG232 tr.155]

..

   "The command to query the NPU load is as follows: cat /sys/kernel/debug/rknpu/load # or cat /proc/debug/rknpu/load" [T1 UG232 tr.137]

   "It is important to note that the NPU load does not directly represent the actual MAC utilization." [T1 UG232 tr.137]

..

   "If the NPU driver version is after 0.7.2, you can query the NPU version, the utilization of different NPU cores and manually switch the NPU power supply through the node." [T1 UG152 tr.73]

   "echo on > /sys/kernel/debug/rknpu/power" [T1 UG152 tr.74]

..

   "echo userspace > /sys/class/devfreq/fdab0000.npu/governor" [T1 UG152 tr.73]

Lệnh hỏi phiên bản (UG232 tr.15): ``dmesg | grep -i rknpu``, ``cat /sys/kernel/debug/rknpu/version``, ``cat /sys/kernel/debug/rknpu/driver_version`` hoặc ``cat /proc/debug/rknpu/driver_version``.

**Ý chính**

- Node ``load`` cho biết phần trăm thời gian NPU chạy tác vụ, không phải MAC utilization (UG232 tr.137).
- Các node ``power``, ``freq``, ``volt``, ``delayms`` chỉ có trong UG152. UG232 (mới hơn) không nhắc lại. Driver 0.9.8 vẫn còn các node này (xem bảng "Còn thiếu nguồn" bên dưới), lý do UG232 không nhắc vẫn ``unknown``.
- Mã nguồn driver 0.9.8 nằm ở ``3rdparty/rknpu-driver-0.9.8/`` (fork Orange Pi. đã diff với ``rockchip-linux/kernel`` nhánh ``develop-6.1`` commit ``77168c8d`` (2026-07-29): cùng chuỗi phiên bản 0.9.8 20240828.``rknpu_debugger.c``, ``rknpu_job.c``, ``include/rknpu_job.h``, ``include/rknpu_ioctl.h``, ``Makefile``, ``Kconfig`` giống hệt, 5 file khác (``rknpu_drv.c``, ``rknpu_devfreq.c``, ``rknpu_iommu.c``, ``rknpu_mem.c``, ``include/rknpu_mem.h``) do bản Rockchip thêm chip RV1126B, đổi cách ánh xạ dma-buf và thêm ``kern_addr_valid``, không chạm các đoạn được trích, số dòng sau các hunk thêm (từ ``rknpu_drv.c:288``, ``rknpu_devfreq.c:123``) lệch trong bản Rockchip), các câu về driver ở mục này không có dòng DRV thì chỉ biết hành vi qua tài liệu.

**Giới hạn**

- Khuyến nghị phiên bản driver: UG232 tr.16, UG232 tr.155 và QS232 tr.15 nêu ">= 0.9.2", chỉ UG232 tr.136 nêu "0.8.8 or later". QS232 tr.14 chỉ lấy 0.8.8 làm ví dụ trong ảnh.
- UG152 tr.73 nói có thể hỏi "the utilization of different NPU cores" qua các node. định dạng đầu ra chính xác của ``rknpu/load`` là ``unknown``, cần T3 trên board. Đóng một phần (T1 DRV, T3. DRV xem mục Nguồn cuối trang): ``rknpu/load`` in ``NPU load:``, rồi với mỗi lõi (khi ``num_irqs`` > 1) ``Core%d:`` và ``%2.d%%,``. Khi ``num_irqs`` = 1 chỉ in ``%2.d%%``. Phần trăm = ``total_busy_time / (RKNPU_LOAD_INTERVAL / 100)``, chặn trên 100 (``rknpu_debugger.c:39-76``). Lúc đầu user thường không đọc được ``/sys/kernel/debug/rknpu/*`` (``Permission denied``), sau đó đọc được bằng sudo của người dùng, xem mệnh đề sau. Đóng một phần (T3 board, đọc bằng sudo 2026-10-10, log T3 board 2026-10-10 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``)): ``load`` lúc nhàn rỗi ra ``NPU load:  Core0:  0%, Core1:  0%, Core2:  0%,``, khớp ``rknpu_debugger.c:39-76`` kể cả dấu phẩy sau lõi cuối.``version`` ra ``RKNPU driver: v0.9.8``. Chu kỳ lấy mẫu của ``load`` vẫn chưa đo (chỉ đọc lúc nhàn rỗi).
- Ngữ nghĩa chính xác của node ``power`` và ``delayms`` là ``unknown``. Đóng một phần (T1 DRV): ``power`` đọc ra ``on`` nếu ``power_refcount`` > 0, ngược lại ``off``, ghi ``on`` tăng ``cmdline_power_refcount`` rồi gọi ``rknpu_power_get``, ghi ``off`` (khi ``power_refcount`` > 0 và ``cmdline_power_refcount`` > 0) trừ phần ``cmdline_power_refcount`` còn lại khỏi ``power_refcount``, đặt ``cmdline_power_refcount`` về 0 rồi gọi ``rknpu_power_put``, tức hủy toàn bộ các lần ghi ``on`` trước đó (suy ra từ code) (``rknpu_debugger.c:78-130``). ``delayms`` đọc và ghi ``power_put_delay`` (đơn vị ms theo log ``%lums``, ``rknpu_debugger.c:132-175``), mặc định 3000 (``rknpu_drv.c:1467``).``rknpu_power_put_delay`` dùng ``msecs_to_jiffies`` (``rknpu_drv.c:375-384``). Đóng một phần (T3 board, đọc bằng sudo 2026-10-10, log T3 board 2026-10-10): ``power`` = ``off`` (lúc nhàn rỗi), ``delayms`` = 3000, khớp mặc định ``rknpu_drv.c:1467``.

--------------

.. _55-quy-trình-pc-và-board-rknn_server-adb-và-mạng:

Quy trình PC và board: rknn_server, adb và mạng
===============================================

**Câu hỏi:** PC nói chuyện với board như thế nào?

**Nguồn nói gì**

   "It is a background proxy service running on the device, responsible for receiving commands and data transmitted from the computer via USB, executing the corresponding interfaces, and returning results to the computer." [T1 UG232 tr.16]

..

   "ARM64 does not need to use RKNN Server for debugging, skipping this step if you were using ARM64 for RKNN Toolkit2." [T1 UG232 tr.16]

   "It is important to ensure consistency among the versions of RKNN Server, Runtime library and RKNN-Toolkit2." [T1 UG232 tr.17]

..

   "If perform model inference on a device using ADB over the network, the user needs to manually execute the command "adb connect [IP]" to connect to the device, and then enter the device identifier, typically in the form of an IP address or IP address followed by a port number." [T1 UG232 tr.29]

   "some development boards may not have the rknn_server service started by default after power on or reboot. This can result in errors such as E init_runtime: The rknn_server on the connected device is abnormal when running RKNN Python Demo." [T1 QS232 tr.29]

Lệnh khởi động trên Linux RK3588 (UG232 tr.16): ``nohup /usr/bin/rknn_server >/dev/null&``.

Tài liệu ``doc/rknn_server_proxy.md`` (tiếng Trung) dòng 6: "RKNN Toolkit2的连板功能一般需要更新板端的 rknn_server 和 librknnrt.so/librknnmrt.so，并且手动启动 rknn_server 才能正常工作。" (Tạm dịch: chức năng nối board của RKNN Toolkit2 thường cần cập nhật ``rknn_server`` và ``librknnrt.so`` trên board, và khởi động ``rknn_server`` thủ công.)

**Ý chính**

- Có hai bản RKNN-Toolkit2: x86_64 dùng adb và ``rknn_server`` để nối board, bản ARM64 chạy trực tiếp trên board và không cần cả hai (UG232 tr.11, tr.16, tr.17). UG232 tr.2 (revision V2.3.0) ghi "Add support for ARM64 version of RKNN-Toolkit2", nên câu "No ARM Linux version" ở UG232 tr.157 là mô tả cũ.
- Phiên bản ``rknn_server``, ``librknnrt`` và RKNN-Toolkit2 phải khớp nhau (UG232 tr.17).
- Tổng hợp của file này: khi chạy RKNN-Toolkit-Lite2 trực tiếp trên board (``target=None`` trên máy aarch64) thì có vẻ không cần ``rknn_server``, chỉ đường điều khiển board từ PC mới cần. Đây là suy luận, chưa có T3 và không có câu T1 nói trực tiếp "Lite2 không cần rknn_server". Căn cứ gián tiếp: QS232 tr.15 nói tính năng on-board debugging của RKNN-Toolkit2 cần "the initiation of the rknn_server service". UG232 tr.171 nói "RKNN-Toolkit2 will communicate with the rknn_server on the board side".``rknn_server_proxy.md`` dòng 7 mô tả ``rknn_server`` là dịch vụ nhận giao thức từ PC qua USB, các bước chạy demo Lite2 ở UG232 tr.37 và ví dụ ``rknn-toolkit-lite2/examples/resnet18/test.py:91`` ("do not need specify target") không nhắc ``rknn_server``. Điều không loại trừ: docstring và ``list_devices()`` của ``rknn_lite.py`` còn có các đường ``target``, ``device_id``, adb và ntb.

**Giới hạn.** Chỗ đặt ``librknnrt.so``: UG232 tr.18 lệnh ``adb push ... /usr/lib64``. QS232 tr.17 và ``rknn_server_proxy.md`` dòng 103 dùng ``/usr/lib``. UG232 tr.155 cũng nhắc ``/usr/lib/librknnrt.so``. Kiểm trên board.

--------------

.. |UG232 Figure 3-5| image:: ../../../_assets/img/npu/05_toolchain/ug232_p37_fig3-5.png

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
     - 17
   * - ``UG152``
     - T1
     - :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`
     - 3
   * - ``QS232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/01_Rockchip_RKNPU_Quick_Start_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 2
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 1
