:tocdepth: 1

***************************
Driver rknpu và rknn_server
***************************

.. admonition:: Trang này trả lời

   - Làm sao biết phiên bản driver rknpu, node trạng thái nào có và nguồn driver nằm ở đâu?
   - PC nói chuyện với board bằng rknn_server, adb và mạng như thế nào?
   - Một job đi từ lệnh ioctl của userspace đến phần cứng NPU qua những bước nào trong mã driver?

.. admonition:: Tóm tắt

   - Hãng khuyến nghị driver RKNPU ">= 0.9.2" khi cài môi trường [T1 UG232 tr.16] và "0.8.8 or later" khi tối ưu hiệu năng [T1 UG232 tr.136]. Hai ngưỡng không mâu thuẫn. Driver trong repo là 0.9.8 [T1 DRV include/rknpu_drv.h:32-35].
   - Node ``load`` là phần trăm thời gian NPU chạy tác vụ trong một cửa sổ 1 giây, không phải MAC utilization [T1 UG232 tr.137] [T1 DRV include/rknpu_drv.h:40].
   - rknn_server chỉ cần khi điều khiển board từ PC x86_64 qua USB hoặc adb. Bản RKNN-Toolkit2 ARM64 không cần [T1 UG232 tr.16] [T1 UG232 tr.17].
   - Phiên bản rknn_server, librknnrt và RKNN-Toolkit2 phải khớp nhau [T1 UG232 tr.17].
   - Mã driver 0.9.8 chỉ có đường submit PC mode. Mỗi ioctl submit được bọc bằng ``rknpu_power_get`` và ``rknpu_power_put_delay`` [T1 DRV rknpu_job.c:394-397] [T1 DRV rknpu_drv.c:650-660].
   - Chế độ core AUTO trong driver chọn lõi có tổng task đang xếp hàng ít nhất, không đọc trạng thái rảnh của phần cứng (suy ra từ mã) [T1 DRV rknpu_job.c:508-523].
   - Job nhiều core chỉ được commit khi mọi core được chọn đều đã lấy job ra khỏi hàng đợi của mình (suy ra từ mã) [T1 DRV rknpu_job.c:146] [T1 DRV rknpu_job.c:456-457].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _54-driver-rknpu-và-các-node-trạng-thái:

.. _sec-driver-rknpu-node:

1. Driver rknpu và node trạng thái
==================================

Driver rknpu là kernel driver giao tiếp với phần cứng NPU. Runtime (``librknnrt``) trên board gọi xuống driver qua ioctl, phần cứng NPU xem tại :doc:`../01-phan-cung-npu/05-ban-do-thanh-ghi-va-co-che-cau-hinh`. Mục này trả lời ba việc: driver có phiên bản nào, đọc trạng thái của nó ở đâu, và hai node điều khiển nguồn (``power``, ``delayms``) làm gì.

1.1 Phiên bản driver: 0.9.2 hay 0.8.8
-------------------------------------

Hãng nêu hai con số trong cùng một tài liệu, ở hai ngữ cảnh khác nhau:

   "It is recommended that the RKNPU driver version is >= 0.9.2." [T1 UG232 tr.16]

..

   "It is recommended to update to version 0.8.8 or later. This step is not mandatory." [T1 UG232 tr.136]

.. list-table:: Các mức phiên bản driver trong nguồn
   :header-rows: 1
   :widths: 22 18 40 20

   * - Mức
     - Ngữ cảnh
     - Nội dung
     - Nguồn
   * - 0.9.2
     - Cài môi trường
     - Khuyến nghị driver ">= 0.9.2", firmware bên thứ ba có thể chưa có driver
     - [T1 UG232 tr.16]
   * - 0.9.2
     - Tương thích phiên bản
     - "upgrade the NPU kernel driver to version 0.9.2 or later" khi gặp sự cố
     - [T1 UG232 tr.155]
   * - 0.8.8
     - Tối ưu hiệu năng
     - Driver mới chứa các tối ưu mức thấp, nâng lên "0.8.8 or later", bước này không bắt buộc
     - [T1 UG232 tr.136]
   * - 0.7.2, 0.8.2
     - Node trạng thái
     - Node ``version``, ``load``, ``power`` có từ sau 0.7.2. Node ``freq``, ``volt``, ``delayms`` có từ sau 0.8.2
     - [T1 UG152 tr.73] [T1 UG152 tr.74] [T1 UG152 tr.75]
   * - 0.9.8
     - Mã trong repo
     - ``DRIVER_MAJOR`` 0, ``DRIVER_MINOR`` 9, ``DRIVER_PATCHLEVEL`` 8, ``DRIVER_DATE`` 20240828
     - [T1 DRV include/rknpu_drv.h:32-35]

Cách giải: 0.9.2 là khuyến nghị chung khi dựng môi trường, 0.8.8 là mốc cho riêng chuyện hiệu năng. Vì 0.9.2 lớn hơn 0.8.8, driver đạt 0.9.2 thì đạt cả hai (suy ra). Driver 0.9.8 trong repo vượt cả hai mốc. Nguồn driver ghi nhánh ``orange-pi-6.1-rk35xx`` của ``orangepi-xunlong/linux-orangepi``, commit ``f6eedab0cbe9b4be3f855661a0a7e7008812d40a``, thư mục ``drivers/rknpu/`` [T1 DRV SOURCE.txt:1-5]. Hãng nói driver là mã nguồn mở và nằm trong kernel Rockchip [T1 EX 3rdparty/rknn-toolkit2/README.md:16].

1.2 Hỏi phiên bản và các node
-----------------------------

UG232 liệt kê bốn cách hỏi phiên bản: ``dmesg | grep -i rknpu``, ``cat /sys/kernel/debug/rknpu/version``, ``cat /sys/kernel/debug/rknpu/driver_version`` và ``cat /proc/debug/rknpu/driver_version``. Kết quả có dạng ``RKNPU driver: vX.X.X`` [T1 UG232 tr.15]. Mã 0.9.8 tạo các node sau bằng debugfs (mặc định bật trong Kconfig) và procfs (không bật mặc định) [T1 DRV Kconfig:13-24]:

.. list-table:: Node của driver 0.9.8 so với tài liệu
   :header-rows: 1
   :widths: 14 40 46

   * - Node
     - Trong mã driver
     - Trong tài liệu
   * - ``version``
     - In ``RKNPU driver: v0.9.8`` theo ba macro phiên bản [T1 DRV rknpu_debugger.c:31-37] [T1 DRV rknpu_debugger.c:305]
     - UG232 gọi là ``version`` và ``driver_version`` [T1 UG232 tr.15]
   * - ``load``
     - Đọc tải từng core, mục 1.3 [T1 DRV rknpu_debugger.c:306]
     - [T1 UG232 tr.137]
   * - ``power``, ``delayms``
     - Đọc và ghi, mục 1.4 [T1 DRV rknpu_debugger.c:307] [T1 DRV rknpu_debugger.c:310-311]
     - [T1 UG152 tr.74] [T1 UG152 tr.75]
   * - ``freq``, ``volt``
     - Có trong bảng node [T1 DRV rknpu_debugger.c:308-309]
     - [T1 UG152 tr.74] [T1 UG152 tr.75]
   * - ``reset``
     - Có trong bảng node [T1 DRV rknpu_debugger.c:312]
     - Không thấy trong UG152, UG232, API232 (tìm ``rknpu/reset``)
   * - ``mm``
     - Chỉ có khi bật ``CONFIG_ROCKCHIP_RKNPU_SRAM`` [T1 DRV rknpu_debugger.c:313-314]
     - Có ví dụ ``cat /sys/kernel/debug/rknpu/mm`` để xem SRAM còn trống [T1 UG232 tr.108]

Hai điểm lệch giữa tài liệu và mã (suy ra từ so sánh):

- Mã chỉ có node ``version``, không có ``driver_version``. Tìm chuỗi ``driver_version`` trong ``3rdparty/rknpu-driver-0.9.8/*.c`` và ``include/`` không ra kết quả. Với driver này, lệnh ``driver_version`` trong UG232 tr.15 sẽ không có node tương ứng. Lệnh ``version`` thì có.
- Mã dùng ``proc_mkdir("rknpu", NULL)`` nên đường procfs là ``/proc/rknpu`` [T1 DRV rknpu_debugger.c:557]. UG232 nêu ``/proc/debug/rknpu/...`` [T1 UG232 tr.137] và ``/proc/rknpu/version`` cho RV1106 [T1 UG232 tr.137]. Vì sao có hai đường: unknown. Đã tìm ở: UG232 tr.15, tr.136-137, UG152 tr.73-74, từ khóa: ``/proc/debug``.

Hãng cũng nêu đường node thiết bị cho Docker: ``/dev/dri/renderD129`` là device node NPU của RK3588 và runtime dựa vào nó [T1 UG232 tr.155]. Điều này khớp biến thể DRM của driver, mục 3.1 (suy ra).

1.3 Node load
-------------

Hãng định nghĩa tải là phần trăm thời gian NPU chạy tác vụ trong một đơn vị thời gian, và dặn rõ không đồng nhất với hiệu suất MAC:

   "It is important to note that the NPU load does not directly represent the actual MAC utilization." [T1 UG232 tr.137]

Mã cho biết cách tính cụ thể. Một hrtimer chạy mỗi ``RKNPU_LOAD_INTERVAL`` = 1000000000 ns, tức 1 giây (suy ra từ ``ktime_set(0, ...)``) [T1 DRV include/rknpu_drv.h:40] [T1 DRV rknpu_drv.c:783]. Mỗi nhịp, driver cộng thêm phần đang chạy của job hiện tại vào ``busy_time``, chép ``busy_time`` sang ``total_busy_time`` rồi đặt ``busy_time`` về 0 [T1 DRV rknpu_drv.c:747-775]. Hàm ``rknpu_load_show`` đổi ``total_busy_time`` ra phần trăm bằng cách chia cho ``RKNPU_LOAD_INTERVAL / 100`` và chặn ở 100 [T1 DRV rknpu_debugger.c:64-66]. Khi cấu hình có nhiều hơn một IRQ (RK3588 có ba), mỗi core in một mục ``Core%d:`` kèm ``%2.d%%,`` [T1 DRV rknpu_debugger.c:50-71]. Vậy giá trị đọc được là tải của cửa sổ 1 giây đã khép gần nhất (suy ra), nên đọc nhanh lặp lại trong cùng một giây trả về cùng số.

1.4 Node power và delayms
-------------------------

Driver đếm tham chiếu nguồn bằng ``power_refcount``. Lần ``rknpu_power_get`` đầu tiên (refcount lên 1) gọi ``rknpu_power_on`` [T1 DRV rknpu_drv.c:345-355]. ``rknpu_power_put_delay`` không tắt ngay. Khi ``power_put_delay`` khác 0 và refcount bằng 1, nó xếp một delayed work sau ``power_put_delay`` ms. Nếu không, nó chỉ giảm refcount [T1 DRV rknpu_drv.c:375-389]. Giá trị mặc định là 3000 ms [T1 DRV rknpu_drv.c:1466-1467]. Nhờ vậy các job liên tiếp trong vài giây không phải bật và tắt nguồn nhiều lần (suy ra).

Hai node điều khiển phần này:

- ``power``: đọc ra ``on`` nếu ``power_refcount`` > 0, ngược lại ``off`` [T1 DRV rknpu_debugger.c:78-91]. Ghi ``on`` tăng ``cmdline_power_refcount`` rồi gọi ``rknpu_power_get``. Ghi ``off`` (khi cả hai bộ đếm dương) trừ phần ``cmdline_power_refcount`` còn lại khỏi ``power_refcount``, đặt nó về 0 rồi gọi ``rknpu_power_put``, tức hủy mọi lần ghi ``on`` trước đó (suy ra từ mã) [T1 DRV rknpu_debugger.c:93-130]. UG152 nêu ``echo on`` và ``echo off`` [T1 UG152 tr.74], đồng thời dặn từ sau 0.7.2 phải bật nguồn NPU trước khi đặt tần số [T1 UG152 tr.73].
- ``delayms``: đọc và ghi ``power_put_delay`` theo ms (log in ``%lums``) [T1 DRV rknpu_debugger.c:132-175]. UG152 mô tả là thời gian trễ trước khi tắt nguồn, đơn vị ms [T1 UG152 tr.75].

Hãng không nêu chu kỳ lấy mẫu của ``load`` ngoài những gì mã cho thấy ở mục 1.3: unknown. Đã tìm ở: UG232 tr.137, UG152 tr.73-75, từ khóa: ``load``, ``interval``.

.. _sec-rknn-server-adb:

2. rknn_server, adb và mạng
===========================

2.1 rknn_server làm gì
----------------------

RKNN-Toolkit2 trên PC có hai kiểu chạy mô hình trên NPU thật. Kiểu thứ nhất là kết nối board từ PC x86_64 (PC-to-board debugging) và cần rknn_server trên board:

   "It is a background proxy service running on the device, responsible for receiving commands and data transmitted from the computer via USB, executing the corresponding interfaces, and returning results to the computer." [T1 UG232 tr.16]

Luồng khi suy luận có board: RKNN-Toolkit2 giao tiếp với rknn_server, mô hình và dữ liệu vào được gửi từ PC sang board, sau đó RKNPU2 C API chạy suy luận trên board và gửi kết quả về PC [T1 UG232 tr.171]. Tài liệu đi kèm SDK mô tả cùng ý: rknn_server nhận giao thức từ PC qua USB rồi gọi hàm tương ứng của runtime trên board [T1 EX 3rdparty/rknn-toolkit2/doc/rknn_server_proxy.md:7].

Kiểu thứ hai là chạy trực tiếp trên board với RKNN-Toolkit2 bản ARM64. Bản này không cần rknn_server:

   "ARM64 version does not require the RKNN Server." [T1 UG232 tr.17]

UG232 tr.16 cũng cho phép bỏ bước kiểm tra rknn_server khi dùng ARM64 [T1 UG232 tr.16]. UG232 tr.2 (bản V2.3.0) ghi thêm hỗ trợ bản ARM64 [T1 UG232 tr.2], nên câu "No ARM Linux version" ở tr.157 là mô tả cũ [T1 UG232 tr.157]. Sự khác nhau giữa Toolkit2 trên PC và Lite2 trên board xem :doc:`02-toolkit-pc-va-lite2-board`.

2.2 Kiểm tra và khởi động
-------------------------

Firmware của Rockchip thường tích hợp và tự khởi động rknn_server khi boot [T1 UG232 tr.16]. Quy trình kiểm tra và khởi động thủ công trên Linux RK3588:

.. list-table:: Lệnh kiểm tra, khởi động và đọc log rknn_server
   :header-rows: 1
   :widths: 24 46 30

   * - Việc
     - Lệnh
     - Nguồn
   * - Kiểm tra tiến trình
     - ``adb shell`` rồi ``ps | grep rknn_server``
     - [T1 UG232 tr.16]
   * - Khởi động (Linux RK3588)
     - ``nohup /usr/bin/rknn_server >/dev/null&``
     - [T1 UG232 tr.16]
   * - Khởi động (Android)
     - ``su``, ``setenforce 0``, ``nohup /vendor/bin/rknn_server >/dev/null&``
     - [T1 UG232 tr.16]
   * - Kiểm tra phiên bản
     - ``strings /usr/bin/rknn_server | grep -i "rknn_server version"``
     - [T1 UG232 tr.18]
   * - Bật log chi tiết (Linux)
     - ``export RKNN_SERVER_LOGLEVEL=5`` rồi khởi động lại
     - [T1 UG232 tr.20]

Nếu ``ps`` không thấy tiến trình, tài liệu SDK yêu cầu khởi động thủ công [T1 EX 3rdparty/rknn-toolkit2/doc/rknn_server_proxy.md:12].

2.3 Khớp phiên bản và vị trí tệp
--------------------------------

Cần cập nhật khi board chưa cài rknn_server, thiếu thư viện runtime hoặc hai bên lệch phiên bản [T1 UG232 tr.16]. Quy tắc then chốt:

   "It is important to ensure consistency among the versions of RKNN Server, Runtime library and RKNN-Toolkit2." [T1 UG232 tr.17]

Các ngưỡng phiên bản riêng của rknn_server và runtime [T1 UG232 tr.17]:

- Mô hình có kích thước đầu vào động: rknn_server và RKNPU2 Runtime ``>= 1.5.0``.
- Mô hình lớn hơn 2 GB: rknn_server ``>= 2.0.0b0``.
- Nền tảng ít bộ nhớ (RV1103, RV1106 và các biến thể): khuyến nghị ``>= 2.1.0``.

Vị trí tệp theo hai tài liệu khác nhau ở thư mục đích của ``librknnrt.so`` trên Linux 64-bit:

- UG232 kiểm tra phiên bản ở ``/usr/lib/librknnrt.so`` rồi đẩy tệp vào ``/usr/lib64`` [T1 UG232 tr.18].
- Tài liệu SDK đẩy ``librknnrt.so`` vào ``/usr/lib`` [T1 EX 3rdparty/rknn-toolkit2/doc/rknn_server_proxy.md:103].
- UG232 tr.155 dùng ``/usr/lib/librknnrt.so`` trong lệnh Docker [T1 UG232 tr.155].

Thư mục nào board thật dùng: unknown. Đã tìm ở: UG232 tr.17-18, tr.155 và ``rknn_server_proxy.md``, từ khóa: ``/usr/lib``, ``/usr/lib64``. Kiểm bằng cách chạy lệnh ``strings`` ở cả hai đường dẫn khi cập nhật.

2.4 adb qua mạng
----------------

Mặc định ``init_runtime`` có ``target=None`` và chạy trên simulator. Khi cần kết quả từ board, người dùng điền ``target`` là tên nền tảng [T1 UG232 tr.29]. Với nhiều thiết bị, ``device_id`` chọn thiết bị. Nếu dùng adb qua mạng, người dùng chạy thủ công ``adb connect [IP]`` rồi nhập định danh thiết bị, thường là IP hoặc IP kèm cổng [T1 UG232 tr.29]. Cùng quy tắc áp dụng khi phân tích độ chính xác trên board [T1 UG232 tr.30]. Lệnh ``adb devices`` hoặc ``rknn.list_devices()`` cho biết thiết bị đã thấy hay chưa [T1 UG232 tr.174]. Giao thức bên dưới (cổng, mã hóa) không có trong nguồn đã mở: unknown. Đã tìm ở: UG232 tr.16-20, tr.29-30, tr.171, từ khóa: ``port``, ``tcp``.

.. _sec-driver-submit-job:

3. Luồng submit job trong mã driver
===================================

Mục này đọc mã driver 0.9.8 để mô tả đường đi của một job. Mã nằm ở ``3rdparty/rknpu-driver-0.9.8/`` (cây Orange Pi, cùng chuỗi phiên bản 0.9.8 20240828 với cây Rockchip, riêng ``rknpu_job.c`` và ``rknpu_debugger.c`` giống hệt [T1 DRV SOURCE.txt:9-11]). Thứ tự ghi thanh ghi trong ``rknpu_job_subcore_commit_pc`` và xử lý ngắt ở mức bit đã có tại :doc:`../01-phan-cung-npu/05-ban-do-thanh-ghi-va-co-che-cau-hinh` (mục :ref:`Hai chế độ cấu hình <sec-npu-hai-che-do>` và :ref:`Ngắt <sec-npu-ngat>`), trang này không lặp lại.

.. list-table:: Các bước của một job và hàm tương ứng
   :header-rows: 1
   :widths: 6 30 34 30

   * - Bước
     - Việc
     - Hàm
     - Dòng mã
   * - 1
     - ioctl vào, bật nguồn
     - ``rknpu_ioctl`` hoặc macro ``RKNPU_IOCTL``
     - [T1 DRV rknpu_drv.c:584-618] [T1 DRV rknpu_drv.c:650-660]
   * - 2
     - Kiểm tra tham số, tạo job
     - ``rknpu_submit``, ``rknpu_job_alloc``
     - [T1 DRV rknpu_job.c:746-766] [T1 DRV rknpu_job.c:128-174]
   * - 3
     - Chọn core, xếp hàng
     - ``rknpu_job_schedule``
     - [T1 DRV rknpu_job.c:525-559]
   * - 4
     - Lấy job ra, commit khi đủ core
     - ``rknpu_job_next``, ``rknpu_job_commit``
     - [T1 DRV rknpu_job.c:429-458] [T1 DRV rknpu_job.c:402-427]
   * - 5
     - Ghi thanh ghi PC mode
     - ``rknpu_job_subcore_commit_pc``
     - [T1 DRV rknpu_job.c:272-375]
   * - 6
     - Ngắt, hoàn tất đợt, đánh thức
     - ``rknpu_irq_handler``, ``rknpu_job_done``
     - [T1 DRV rknpu_job.c:640-682] [T1 DRV rknpu_job.c:460-506]
   * - 7
     - Chờ, timeout, reset
     - ``rknpu_job_wait``, ``rknpu_job_abort``
     - [T1 DRV rknpu_job.c:176-270] [T1 DRV rknpu_job.c:561-613]

3.1 Điểm vào: ioctl và nguồn
----------------------------

Kconfig cho chọn một trong hai bộ quản lý bộ nhớ, mặc định ``ROCKCHIP_RKNPU_DRM_GEM``, lựa chọn còn lại là ``ROCKCHIP_RKNPU_DMA_HEAP`` [T1 DRV Kconfig:38-55]. Hai biến thể có hai cửa vào cho cùng ``rknpu_submit``:

- Biến thể DRM: ioctl ``RKNPU_SUBMIT`` đăng ký trong bảng ``DRM_IOCTL_DEF_DRV`` với cờ ``DRM_RENDER_ALLOW`` [T1 DRV rknpu_drv.c:669-671]. Macro ``RKNPU_IOCTL`` gọi ``rknpu_power_get`` trước hàm và ``rknpu_power_put_delay`` sau hàm [T1 DRV rknpu_drv.c:650-660].
- Biến thể DMA heap: ``rknpu_ioctl`` rẽ nhánh theo ``_IOC_NR(cmd)`` với ``case RKNPU_SUBMIT`` [T1 DRV rknpu_drv.c:596-601], tự gọi ``rknpu_power_get`` và ``rknpu_power_put_delay`` quanh khối ``switch`` [T1 DRV rknpu_drv.c:594] [T1 DRV rknpu_drv.c:618], và chép struct từ userspace bằng ``copy_from_user`` [T1 DRV rknpu_job.c:865-870].

Biến thể nào chạy trên board là unknown. Đã tìm ở: ``SOURCE.txt`` và ``Kconfig`` trong repo, từ khóa: ``DRM_GEM``, ``DMA_HEAP``. Đường ``/dev/dri/renderD129`` trong UG232 tr.155 gợi ý biến thể DRM (suy ra).

Struct ``rknpu_submit`` mang các trường chính: ``flags``, ``timeout``, ``task_start``, ``task_number``, ``task_obj_addr``, ``task_base_addr``, ``core_mask`` và mảng ``subcore_task[5]`` [T1 DRV include/rknpu_ioctl.h:265-280]. Cờ job gồm ``RKNPU_JOB_PC`` (bit 0), ``RKNPU_JOB_NONBLOCK`` (bit 1), ``RKNPU_JOB_PINGPONG`` (bit 2), ``RKNPU_JOB_FENCE_IN`` (bit 3) và ``RKNPU_JOB_FENCE_OUT`` (bit 4) [T1 DRV include/rknpu_ioctl.h:97-103].

3.2 Kiểm tra, tạo job, chọn core
--------------------------------

``rknpu_submit`` từ chối job có ``task_number`` bằng 0 và job có ``core_mask`` lớn hơn ``core_mask`` của cấu hình. RK3588 đặt ``core_mask`` = 0x7 [T1 DRV rknpu_job.c:752-760] [T1 DRV rknpu_drv.c:183-197]. ``rknpu_job_alloc`` đếm số bit trong ``core_mask`` thành ``use_core_num`` rồi khởi tạo ``run_count`` và ``interrupt_count`` bằng giá trị này [T1 DRV rknpu_job.c:143-147]. Với job chặn (blocking), ``job->args`` trỏ thẳng vào struct của người gọi. Với job NONBLOCK, driver sao chép struct để dùng sau khi ioctl trả về [T1 DRV rknpu_job.c:157-169].

Khi cờ fence được đặt mà kernel không bật ``CONFIG_ROCKCHIP_RKNPU_FENCE``, driver log lỗi và trả ``-EINVAL`` [T1 DRV rknpu_job.c:799-802] [T1 DRV rknpu_job.c:816-819]. Cấu hình fence của board: unknown. Đã tìm ở: ``SOURCE.txt``, từ khóa: ``FENCE``.

``rknpu_job_schedule`` xử lý core theo ``core_mask``:

1. Nếu ``core_mask`` bằng ``RKNPU_CORE_AUTO_MASK`` (0x00), driver gọi ``rknpu_schedule_core_index``. Hàm này duyệt các core và chọn core có ``task_num`` nhỏ nhất, hòa thì giữ core có chỉ số thấp [T1 DRV rknpu_job.c:508-523]. Job được đổi thành job một core (``use_core_num`` = 1) [T1 DRV rknpu_job.c:532-538]. ``task_num`` là tổng task đã xếp hàng và đang chạy trên core đó [T1 DRV rknpu_job.c:550] [T1 DRV rknpu_job.c:479].
2. Driver chuyển IOMMU domain theo ``iommu_domain_id`` của job [T1 DRV rknpu_job.c:540-543].
3. Dưới ``irq_lock``, driver thêm job vào ``todo_list`` của từng core được chọn và cộng ``task_num`` [T1 DRV rknpu_job.c:545-553].
4. Driver gọi ``rknpu_job_next`` cho từng core được chọn [T1 DRV rknpu_job.c:555-558].

Hãng mô tả AUTO là "select the idle core inside the NPU" [T1 UG152 tr.26] và "automatically runs on the currently idle NPU core" [T1 API232 tr.17]. Trong mã, tiêu chí là tổng task xếp hàng ít nhất. Core đang chạy job dài nhưng có ít task nhất vẫn có thể được chọn trước core rảnh nếu ``task_num`` của core rảnh cao hơn, và ngược lại (suy ra). Hai mô tả không hẳn trùng nhau, nhưng khác biệt nào thể hiện ra ngoài: unknown. Đã tìm ở: UG152 tr.26, API232 tr.17, mã driver, từ khóa: ``AUTO``, ``idle``.

Số trường ``subcore_task[5]`` ứng với cách chia nhiều core trong ``rknpu_job_subcore_commit_pc``. Với job 1 hoặc 2 core, core ``i`` lấy ``subcore_task[i]``. Với job 3 core, core ``i`` lấy ``subcore_task[i + 2]`` [T1 DRV rknpu_job.c:313-325] (cùng quy tắc trong ``rknpu_get_task_number``) [T1 DRV rknpu_job.c:81-88]. Mỗi lần commit ghi tối đa ``max_submit_number`` task. RK3588 đặt giá trị này là (1 << 12) - 1 = 4095 [T1 DRV rknpu_job.c:333-337] [T1 DRV rknpu_drv.c:196]. Job lớn hơn được commit thành nhiều đợt, mỗi đợt kết thúc bằng một ngắt (mục 3.3).

3.3 Commit và hoàn tất
----------------------

``rknpu_job_next`` chạy sau khi xếp hàng và sau mỗi lần job xong. Nó bỏ qua nếu đang soft reset, nếu core đang có job hoặc nếu ``todo_list`` rỗng. Ngược lại nó lấy job đầu hàng đợi, gán vào ``subcore_data->job`` và ghi ``hw_commit_time`` [T1 DRV rknpu_job.c:435-454]. Sau đó ``atomic_dec_and_test(&job->run_count)``, và chỉ khi bộ đếm về 0 mới gọi ``rknpu_job_commit`` [T1 DRV rknpu_job.c:456-457]. Vì ``run_count`` khởi tạo bằng số core được chọn [T1 DRV rknpu_job.c:146], job nhiều core chỉ lên phần cứng sau khi mọi core đã lấy nó khỏi hàng đợi (suy ra). Nếu một core còn bận job khác, các core còn lại đã nhận job này vẫn chờ.

``rknpu_job_commit`` rẽ theo ``core_mask`` và gọi ``rknpu_job_subcore_commit`` cho từng core [T1 DRV rknpu_job.c:402-427]. Hàm commit chuyển sang slave mode rồi từ chối job không có cờ PC bằng ``-EINVAL``, nên driver này chỉ chạy PC mode [T1 DRV rknpu_job.c:385-399]. Chi tiết ghi thanh ghi xem trang thanh ghi đã link ở trên.

Mỗi core có một IRQ tên ``npu0_irq``, ``npu1_irq``, ``npu2_irq`` gắn với ba handler [T1 DRV rknpu_drv.c:84-88] đăng ký bằng ``devm_request_irq`` [T1 DRV rknpu_drv.c:1095-1098]. ``rknpu_job_done`` chạy sau khi handler xác nhận trạng thái ngắt [T1 DRV rknpu_job.c:677-679]:

1. Tăng ``submit_count`` của core. Nếu số đợt đã commit còn nhỏ hơn ``ceil(task / max_submit_number)``, commit đợt kế và thoát [T1 DRV rknpu_job.c:468-473].
2. Dọn trạng thái core: ``subcore_data->job = NULL``, trừ ``task_num``, tính ``hw_elapse_time`` và cộng ``busy_time`` [T1 DRV rknpu_job.c:475-483]. ``busy_time`` chính là đầu vào của node ``load`` ở mục 1.3 (suy ra).
3. Khi ``interrupt_count`` về 0 (core cuối của job báo xong): trả IOMMU domain, đặt ``RKNPU_JOB_DONE``, ghi ``job->ret``, báo fence nếu có, ``schedule_work`` dọn job ASYNC và ``wake_up`` hàng đợi chờ. Job nhiều core đánh thức hàng đợi của core 0, job một core đánh thức hàng đợi của chính core đó [T1 DRV rknpu_job.c:485-503].
4. Gọi ``rknpu_job_next`` để lấy job kế tiếp của core [T1 DRV rknpu_job.c:505].

3.4 Chờ, timeout và reset
-------------------------

Với job blocking, ``rknpu_submit`` gọi ``rknpu_job_schedule`` rồi ``rknpu_job_wait`` (khi có cờ PC), sau đó dọn job nếu thành công hoặc gọi ``rknpu_job_abort`` nếu lỗi [T1 DRV rknpu_job.c:832-843]. Job NONBLOCK đặt ``RKNPU_JOB_ASYNC``, gọi ``rknpu_job_timeout_clean`` rồi ``rknpu_job_schedule`` và trả về ngay [T1 DRV rknpu_job.c:823-831].

``rknpu_job_wait`` chờ trên ``job_done_wq`` của core chờ (core 0 cho mọi ``core_mask`` nhiều core, theo ``rknpu_wait_core_index``) với thời hạn ``args->timeout`` tính bằng ms [T1 DRV rknpu_job.c:27-48] [T1 DRV rknpu_job.c:193-197]. Khi hết hạn, vòng chờ tiếp tục tối đa ba lần nếu job chưa lên phần cứng (``hw_commit_time`` bằng 0) hoặc thời gian từ lúc commit chưa vượt ``timeout`` [T1 DRV rknpu_job.c:199-221]. Hết các lần chờ mà chưa xong, hàm đọc bộ đếm task (``pc_task_status_offset``, mặt nạ ``0xfff``) và trả ``-ETIMEDOUT`` [T1 DRV rknpu_job.c:244-261].

``rknpu_job_abort`` đợi 100 ms, gỡ job khỏi core nếu ngắt chưa kịp vào, và khi lỗi là ``-ETIMEDOUT`` thì log ``INT_STATUS``, ``INT_RAW_STATUS``, mask yêu cầu và bộ đếm task của từng core rồi gọi ``rknpu_soft_reset`` [T1 DRV rknpu_job.c:561-613]. ``rknpu_soft_reset`` đặt ``soft_reseting`` = true, ngủ 100 ms, đánh thức các hàng đợi, assert rồi deassert các đường reset lấy từ DTS (nhóm ``resets``) [T1 DRV rknpu_reset.c:98-132] [T1 DRV rknpu_reset.c:28-62]. Job NONBLOCK không có luồng chờ, nên lần submit kế tiếp gọi ``rknpu_job_timeout_clean`` để soft reset core có job quá hạn [T1 DRV rknpu_job.c:699-744]. Hàm này so ``ktime_us_delta`` (micro giây) với ``args->timeout`` trực tiếp [T1 DRV rknpu_job.c:711-713], trong khi ``rknpu_job_wait`` đổi ``timeout`` ms sang jiffies và nhân 1000 khi so với micro giây [T1 DRV rknpu_job.c:197] [T1 DRV rknpu_job.c:210]. Hai nơi dùng đơn vị khác nhau cho cùng trường (suy ra từ so sánh hai đoạn mã), ý đồ của tác giả: unknown. Đã tìm ở: ``include/rknpu_ioctl.h:265-280`` (chú thích chỉ ghi "submit timeout"), từ khóa: ``timeout``.

3.5 Điều chưa biết
------------------

- Ý nghĩa hai lần ghi ``0xe + 0x10000000 * i`` vào offset ``0x1004`` và ``0x3004`` trong ``rknpu_job_subcore_commit_pc`` khi ``num_irqs`` > 1 [T1 DRV rknpu_job.c:305-311]: unknown. Đã tìm ở: mã driver (không có chú thích), từ khóa: ``0x1004``, ``0x3004``. Chưa tra TRM.
- Cờ nào ``librknnrt`` thực sự truyền khi gọi ``RKNPU_SUBMIT`` (blocking hay NONBLOCK, có ping-pong hay không): unknown. Đã tìm ở: UG232, UG152, API232, từ khóa: ``RKNPU_SUBMIT``, ``ioctl``. Runtime là thư viện nhị phân, không có mã nguồn trong repo.

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 46 26

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Driver phải đạt 0.9.2 và 0.8.8 là hai yêu cầu riêng
     - Hai mốc là khuyến nghị ở hai ngữ cảnh. Đạt 0.9.2 thì đạt cả hai. Driver repo là 0.9.8
     - [T1 UG232 tr.16] [T1 UG232 tr.136] [T1 DRV include/rknpu_drv.h:32-35]
   * - Tải NPU cao nghĩa là MAC được dùng hết công suất
     - Tải là phần trăm thời gian chạy tác vụ, không phải hiệu suất MAC
     - [T1 UG232 tr.137]
   * - Lệnh ``cat .../rknpu/driver_version`` chạy được trên mọi bản driver
     - Mã 0.9.8 chỉ tạo node ``version`` (suy ra từ bảng node)
     - [T1 DRV rknpu_debugger.c:304-313]
   * - Chạy trên board bằng Toolkit2 ARM64 vẫn cần rknn_server
     - Bản ARM64 không cần rknn_server
     - [T1 UG232 tr.17]
   * - Chỉ cần cập nhật ``librknnrt.so`` là đủ
     - rknn_server, runtime và Toolkit2 phải cùng phiên bản
     - [T1 UG232 tr.17]
   * - AUTO nghĩa là NPU chọn core đang rảnh theo phần cứng
     - Mã driver chọn core có tổng ``task_num`` xếp hàng nhỏ nhất (suy ra)
     - [T1 DRV rknpu_job.c:508-523]
   * - Driver hỗ trợ cả slave mode lẫn PC mode
     - Commit từ chối job không có cờ PC
     - [T1 DRV rknpu_job.c:394-397]

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
     - 45
   * - ``UG152``
     - T1
     - :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`
     - 11
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 1
   * - ``DRV``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (commit f6eedab0 theo SOURCE.txt), không tải xuống
     - 99
   * - ``EX``
     - T1
     - Tài liệu và ví dụ đi kèm SDK trong ``3rdparty/rknn-toolkit2/`` (``README.md``, ``doc/rknn_server_proxy.md``), không tải xuống
     - 4
