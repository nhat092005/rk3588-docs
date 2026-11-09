:tocdepth: 1

*********************
Phần cứng tăng tốc
*********************

.. admonition:: Trang này trả lời

   - RK3588S trên board Orange Pi 5 có những khối tăng tốc nào, khối nào bật, khối nào tắt?
   - Khối nào tham gia luồng camera đến phát hiện hiện tại, khối nào chưa dùng?
   - RGA làm được việc nào, đã đo được gì?

.. admonition:: Tóm tắt

   1. ``ai/board/camera.py`` chỉ dùng bốn khối phần cứng: MIPI D-PHY với CSI-2, VICAP, ISP và một trong ba lõi NPU. Tiền xử lý, hậu xử lý, theo dõi, vẽ khung, mã hóa video và JPEG chạy trên CPU [Mã nguồn repo, ``ai/board/camera.py``, :doc:`07-chay-lien-tuc-tren-board`].
   2. Trong lần chạy 20 giây ngày 2026-11-08, bộ đếm ngắt chỉ tăng ở NPU lõi 0, ISP và VICAP. RGA, VPU, JPEG, IEP giữ 0. GPU có 13 và 8 ngắt nhưng ``load`` đọc 0 [T3 board, ``/proc/interrupts``].
   3. Board có thêm các khối chạy được mà luồng không dùng: RGA (hai RGA3, một RGA2), ``rkvenc2``, bộ mã hóa JPEG, GPU Mali-G610. Bốn khối trong datasheet bị tắt trong device-tree, không khối nào liên quan đến ảnh phát hiện.
   4. CPU ngoài NPU tốn khoảng 0.945 ms trên độ trễ đầu cuối 18.97 ms (khóa xung). Không khối nào là nút thắt của 30 FPS, nên chuyển việc sang phần cứng là để giải phóng CPU, không phải tăng FPS [T3 board, ``camera.py``] [SL, phép cộng].
   5. RGA3 không tô màu được, nên tô viền và vẽ khung chỉ chạy trên RGA2 (mục 3.2).
   6. Luồng đề xuất dùng phần cứng tối đa nằm ở :doc:`../00-tong-quan/04-gioi-han-va-huong-phat-trien` mục 3.2. Chưa phần nào chạy liền thành một chương trình.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cách kiểm
============

Ngày 2026-11-08 trên board Orange Pi 5 (kernel 6.1.99-rockchip-rk3588), qua LAN. Nguồn gồm datasheet RK3588S V1.7, ``dmesg``, nút device-tree trong ``/sys/firmware/devicetree/base`` (``/proc/device-tree`` trả về rỗng), ``/sys/bus/platform``, ``/dev``, ``clinfo`` và ``/proc/interrupts``. Nhãn dùng như ở :doc:`01-buc-tranh-tong-the` mục 1. Số ngắt đo trên một lần chạy 20 giây ``camera.py`` ở model ``ppe5_yolov8n_baseline_100ep_s1`` INT8, ``CORE_0``, ghim lõi 4 đến 7, chưa khóa xung.

2. Danh sách khối tăng tốc
==========================

.. list-table::
   :header-rows: 1
   :widths: 16 46 38

   * - Khối
     - Datasheet và trên board
     - Trong ``camera.py``
   * - MIPI D-PHY, CSI-2, VICAP
     - Hai DCPHY combo, hai CSI DPHY [T1 DS V1.7 tr.11, tr.12]. ``mipi1-csi2`` và ``rkcif-mipi-lvds1`` ``okay``, năm nút CSI khác tắt [T3 board]
     - Dùng
   * - ISP (``rkisp``)
     - Tối đa 48 MP (dual), 16 MP@30 một ISP [T1 DS V1.7 tr.12]. Hai nút ``fdcb0000``, ``fdcc0000`` ``okay``, camera dùng ``rkisp0-vir1``, ``rkispp`` và ``rkisp-unite`` ``disabled`` [T3 board]
     - Dùng. FEC, HDR, dehaze không cần ở cảnh này [SL]
   * - NPU
     - 3 lõi, 6 TOPS, buffer 384 KB mỗi lõi [T1 DS V1.7 tr.11]. ``npu@fdab0000`` ``okay``, driver RKNPU 0.9.8, xung 300 đến 1000 MHz [T3 board]
     - Dùng ``CORE_0``, hai lõi nghỉ
   * - RGA
     - 2D engine: đổi định dạng, co giãn 1/8 đến 8, xoay, lật, pha trộn [T1 DS V1.7 tr.11]. ``rga3`` tại ``fdb60000``, ``fdb70000``, ``rga2`` tại ``fdb80000``, driver ``rga`` v1.3.7, ``librga.so.2.1.0`` [T3 board]
     - Không dùng
   * - GPU Mali-G610 MP4
     - OpenGL ES 3.2, OpenCL 2.2, Vulkan 1.2 [T1 DS V1.7 tr.11]. ``/dev/mali0``, ``clinfo`` báo OpenCL 3.0 (mục 5) [T3 board]
     - Không dùng
   * - Bộ mã hóa video (``rkvenc2``)
     - H.264 và H.265 tới 8K@30 [T1 DS V1.7 tr.10]. Hai lõi tại ``fdbd0000``, ``fdbe0000`` ``okay``, GStreamer có ``mpph264enc``, ``mpph265enc`` [T3 board]
     - Không dùng. ``--save-video`` chạy libx264 trên CPU
   * - Bộ mã hóa JPEG
     - Bốn đơn vị, 90 triệu điểm ảnh mỗi giây [T1 DS V1.7 tr.10]. Bốn ``jpege-core`` ``okay``, GStreamer có ``mppjpegenc`` [T3 board]
     - Không dùng. ``Saver`` mã hóa bằng ``cv2``
   * - Bộ giải mã video và JPEG
     - H.264, H.265, VP9, AV1, MJPEG [T1 DS V1.7 tr.10]. ``rkvdec``, ``vdpu``, ``av1d``, ``jpegd`` ``okay`` [T3 board]
     - Không có việc: camera MIPI ra ảnh thô
   * - IEP (``iep-v2``)
     - Giải xen kẽ, đổi 422 sang 420, tối đa 1920x1080 [T1 DS V1.7 tr.11]. TRM2 chương 8 chỉ liệt kê giải xen kẽ và đổi 422 sang 420, không có khử nhiễu hay làm nét [T1 TRM2 tr.1062]. ``iep@fdbb0000`` ``okay`` [T3 board]
     - Không có việc: ISP đã ra ảnh quét liên tục [SL]
   * - VOP2
     - Bốn cổng, tám lớp, scaler, write-back 1080p [T1 DS V1.7 tr.13, tr.14]. ``vop@fdd90000`` ``okay``, ``HDMI-A-1`` và ``DP-1`` ``disconnected`` [T3 board]
     - Không dùng khi không có màn hình
   * - DMA PL330, TRNG, Cortex-M0, NEON
     - Ba bộ DMA đã nạp, ``/dev/hwrng`` có, MCU chạy firmware của hãng ứng dụng không truy cập được [T1 DS V1.7 tr.8, tr.9] [T3 board]. NEON có trên mọi lõi A55 và A76 [T1 DS V1.7 tr.7]
     - Không liên quan ảnh. NEON là tập lệnh CPU, ``cv2`` dùng được
   * - Tắt trên board
     - Giải nén (GZIP, LZ4), cipher engine, ISPP, ISP ghép đôi (``rkisp-unite``), ``avsd-plus``, ba mailbox, ``vad``: ``status = "disabled"`` [T3 board]
     - Không liên quan ảnh. Một ISP đủ cho 13.2 MP ở 30 khung/giây [T1 DS V1.7 tr.12]

3. RGA
======

3.1. Hàm ``librga`` và việc trong dự án
---------------------------------------

``librga`` trên board xuất các hàm sau (RGA_API 1.9.3), đọc từ ``nm -D`` và ``/usr/include/rga/im2d_single.h`` [T3 board]. Khối nào làm được từng việc đã đo ở mục 3.2.

.. list-table::
   :header-rows: 1
   :widths: 24 24 52

   * - Việc
     - Hàm
     - Trong dự án
   * - Vẽ khung chữ nhật, tô đặc
     - ``imrectangle``, ``imfill``
     - Chỉ RGA2 chạy được. ``Saver`` và ``--save-video`` vẽ bằng ``cv2.rectangle``
   * - Chèn khối chữ (OSD)
     - ``imosd``
     - Chưa thử. Nhận khối chữ đã là ảnh (``rga_buffer_t``), không tự dựng chữ từ phông [T3 board]
   * - Pha trộn, làm mờ ô
     - ``imblend``, ``imcomposite``, ``immosaic``
     - ``imblend`` đã đo (mục 3.2). Còn lại chưa thử
   * - Xoay, lật
     - ``imrotate``, ``imflip``
     - Cảm biến và nút ISP không liệt kê điều khiển lật hoặc xoay [T3 board, ``v4l2-ctl --list-ctrls``]
   * - Thêm viền
     - ``immakeBorder``
     - Chỉ RGA2, 0.528 ms ở 640x640
   * - Cắt vùng
     - ``imcrop``
     - Chưa thử. ISP đã cắt 16:9

Chi phí CPU khi vẽ khung và chữ bằng ``cv2`` chưa có số đo riêng. Số có sẵn: ``Saver`` vẽ hộp và mã hóa JPEG 3.76 ms trung vị ở luồng nền, ``--save-video`` thêm khoảng 2 đến 3 điểm phần trăm CPU tiến trình (:doc:`07-chay-lien-tuc-tren-board` mục 1).

3.2. Khối RGA nào làm được việc nào
-----------------------------------

Đo ngày 2026-11-08 bằng ``imconfig`` ép từng khối chạy, bộ đệm dma-buf, 100 lần, trung vị, lõi A76. Khối thật sự chạy lấy từ bộ đếm ngắt (irq 40, 41, 111). "Từ chối" nghĩa là driver trả lỗi [T3 board, ``experiments/camera/rga_caps/rga_caps.cpp``, ``rga_caps2.cpp``].

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Việc
     - RGA3_0
     - RGA3_1
     - RGA2
   * - NV12 sang RGB888 640x360
     - 0.378 ms
     - 0.273 ms
     - 0.382 ms
   * - Đặt NV12 640x360 vào RGB888 640x640 (một lệnh ``improcess``, không tô nền)
     - 0.264 ms
     - 0.239 ms
     - 0.265 ms
   * - Như trên, đích 640x384
     - 0.184 ms
     - 0.238 ms
     - 0.283 ms
   * - Thu NV12 1920x1080 về 640x360
     - 1.862 ms
     - 1.821 ms
     - 1.627 ms
   * - RGB888 sang NV12 1920x1080
     - 1.389 ms
     - 1.331 ms
     - 1.803 ms
   * - RGB888 sang NV12 640x360
     - 0.172 ms
     - 0.174 ms
     - 0.281 ms
   * - ``imblend`` lớp RGBA 640x360 lên NV12
     - 0.408 ms
     - 0.302 ms
     - 0.295 ms
   * - ``imfill`` (hình chữ nhật 300x200 hoặc cả khung)
     - Từ chối
     - Từ chối
     - 0.137 đến 0.403 ms
   * - ``imrectangle`` trên NV12, RGB888, RGBA8888
     - Từ chối
     - Từ chối
     - 0.107 đến 0.386 ms mỗi hộp
   * - ``immakeBorder`` đến 640x640
     - Từ chối
     - Từ chối
     - 0.528 ms
   * - Letterbox cũ (``imfill`` rồi ``improcess``) đến 640x640, 640x384
     - Từ chối
     - Từ chối
     - 0.793 ms, 0.645 ms

Đọc kết quả:

- RGA3 không tô màu được, khớp với TRM2: chương RGA3 không liệt kê tô màu, ROP hay palette, còn RGA2 có [T1 TRM2 tr.701, tr.754]. Nên ``imfill``, ``imrectangle``, ``immakeBorder`` chạy trên RGA2.
- Vùng viền xám không đổi giữa các khung. Tô một lần lúc khởi tạo (RGA2) rồi dùng lại bộ đệm, mỗi khung chỉ cần lệnh đặt ảnh 0.184 đến 0.264 ms trên RGA3_0, nhanh hơn CPU (0.463 ms ở 640x640) [SL, cần bộ đệm dùng lại].
- Vẽ khung bằng RGA2, mỗi hộp một lệnh ``imrectangle``: 34 hộp mất 11.67 ms ở 640x360 và 12.78 ms ở 4K (0.107 đến 0.386 ms mỗi hộp). ``imrectangleArray`` không nhanh hơn, cùng thời gian và cùng ảnh ra từng byte. Gộp vào một job (``imbeginJob``, ``imrectangleTaskArray``, ``imendJob``) còn 1.60 ms ở 640x360 và 2.03 ms ở 4K, ảnh ra giống hệt vòng từng hộp. Một job tối đa 50 tác vụ, mỗi hộp 4 tác vụ nên mỗi job chứa tối đa 12 hộp, 34 hộp cần 3 job. Hộp vẽ đúng vị trí trên ảnh xuất ra (kiểm bằng mắt một ảnh 640x360) [T3 board, ``experiments/camera/enc_rga_2026-11-08/rga_ext.cpp``, 3 giây mỗi ca, xung khóa].
- Chèn 34 nhãn RGBA 96x20 bằng blend lên NV12 640x360, mỗi nhãn một lệnh: RGA2 3.04 ms, RGA3_0 3.28 ms, RGA3_1 1.25 ms. Gộp vào một job: RGA2 0.52 ms, RGA3_0 0.92 ms, RGA3_1 0.85 ms. RGA2 nhanh nhất nên không cần giao nhãn cho RGA3. Ảnh ra của job RGA2 khác lệnh đơn 85 trên 85008 byte, chưa rõ nguyên nhân [T3 board, cùng nguồn].
- Hai RGA3 chạy song song (mỗi lõi một tiến trình, lệnh đặt ảnh 640x360): 0.202 ms mỗi lệnh, tổng khoảng 9.9 nghìn lệnh mỗi giây, so với 4.1 nghìn (RGA3_0) và 5.6 nghìn (RGA3_1) khi chạy một lõi. Luồng chỉ cần 30 lệnh mỗi giây nên không cần chia. Cùng một việc nhưng RGA3_1 nhanh hơn RGA3_0 (0.178 so với 0.256 ms), chưa rõ nguyên nhân [T3 board, cùng nguồn].
- RGA2 không map được bộ nhớ trên 4 GB. ``dmesg`` ghi ``RGA_MMU unsupported memory larger than 4G!`` cho lõi RGA2, trong khi RGA3 nhận cùng bộ đệm. Cả 400 lần cấp phát đầu từ dma-heap ``system`` đều rơi trên 4 GB, chỉ thành công sau khi dùng hết các trang trống trên 4 GB (vùng Normal của board có 65536 trang, 256 MB). Heap chỉ có ``system`` và ``system-uncached``. Đã thử vẽ ``imfill`` và ``imrectangle`` bằng RGA2 trên bộ đệm 4K NV12 từ ba nguồn. Bộ đệm V4L2 mainpath (``/dev/video11``, xuất bằng ``VIDIOC_EXPBUF``, ba lần cấp 4, 8 và 16 bộ đệm): 28 trên 28 thành công. Bộ đệm MPP loại DRM (``mpp_buffer_group_get_internal``): 7 trên 10 thành công, 3 bộ đệm đầu lỗi 4 GB. Bộ đệm MPP loại ``DMA_HEAP``: 10 trên 10 lỗi vì ``dma_buf_get fail`` (``fd`` không dùng được, không phải lỗi 4 GB), loại ``DRM`` kèm cờ ``CONTIG`` làm chương trình thoát lỗi, chưa thử được. Kết quả chỉ cho board 4 GB này, chưa biết với board nhiều RAM hơn [T3 board, ``dmesg``, ``/proc/zoneinfo``, ``experiments/camera/enc_rga_2026-11-08/rga2_4g.cpp``].
- Chưa thử ``imosd`` và RGA khi CPU và NPU cùng bận. Chạy hai tiến trình cùng lúc cho số bất thường (RGA2 vẽ 34 hộp 3.06 ms khi RGA3_0 đặt ảnh song song, nhưng 11.89 ms khi RGA3_1 làm việc đó), chưa giải thích được nên không dùng.

4. Bộ đếm ngắt khi chạy camera
==============================

Chạy ``camera.py`` 20 giây (630 khung đọc, 600 khung đo), chụp ``/proc/interrupts`` trước và sau, cộng tám cột CPU [T3 board]:

.. list-table::
   :header-rows: 1
   :widths: 14 36 16 34

   * - Ngắt
     - Khối
     - Tăng
     - Ghi chú
   * - 36
     - NPU lõi 0 và IOMMU (chung dòng)
     - 39690
     - Ngắt 37 và 38 (lõi 1, 2) giữ 0. Số này gộp IOMMU nên không chia ra số khung được [SL]
   * - 86
     - VICAP (``rkcifhw``)
     - 1262
     - Gấp đúng hai lần số khung [SL]
   * - 99, 100
     - ISP (``rkisp_hw``)
     - 1262 và 631
     - Hai ngắt và một ngắt mỗi khung [SL]
   * - 125, 127
     - GPU (``fb000000.gpu``)
     - 13 và 8
     - Nguồn unknown. ``load`` đọc ``0@300000000Hz`` ở cả 8 mẫu cách 3 giây
   * - 40, 41, 111
     - RGA3, RGA3, RGA2
     - 0
     - Không chạy
   * - 112, 113, 119 đến 123
     - ``vdpu``, ``vepu``, hai ``rkvdec``, hai ``rkvenc``, ``av1d``
     - 0
     - Không chạy
   * - 114 đến 118, 47
     - Bốn lõi mã hóa JPEG, bộ giải mã JPEG, IEP
     - 0
     - Không chạy

Bộ đếm cho thấy khối đã tham gia hay chưa, không cho biết thời gian hay tải của khối.

5. GPU Mali-G610 và OpenCL
==========================

Trên board [T3 board, ``clinfo``, ``/sys/class/devfreq/fb000000.gpu``]:

- ``Mali-G610 r0p0``, OpenCL 3.0, 4 đơn vị tính toán, work group tối đa 1024. Có ``cl_khr_fp16``, không có số thực kép.
- Bộ nhớ toàn cục 3.817 GiB, là RAM hệ thống chia sẻ.
- Xung 300 đến 1000 MHz (8 mức), ``simple_ondemand``, đang 300 MHz.
- ``vulkaninfo`` không cài nên chưa kiểm Vulkan: unknown.

GPU chạy OpenCL được về mặt cài đặt. Chưa có kernel OpenCL nào được viết hay đo, nên thời gian chạy tiền xử lý hay hậu xử lý trên GPU là unknown.

Việc dự án dành cho GPU là dựng giao diện ứng dụng (cửa sổ, nút, đồ thị, bảng vi phạm, khung hình làm texture), vì đó là việc GPU được thiết kế để làm (OpenGL ES 3.2, Vulkan 1.2 [T1 DS V1.7 tr.11]) và RGA chỉ vẽ hình chữ nhật và khối ảnh. Các việc khác từng cân nhắc (giải mã hộp, tiền xử lý) có thể chuyển khoảng 0.8 ms (tiền xử lý 0.297 cộng hậu xử lý 0.482 ms, khóa xung) trên 18.97 ms [T3 board] [SL, phép cộng], nên không đáng. Chi phí sao chép giữa bộ nhớ CPU và GPU là unknown.

Board có ``libmali-valhall-g610-g13p0-x11-gbm`` 1.9, ``eglinfo``, ``es2_info`` và ``libgtk-3``. ``eglinfo`` báo ``eglInitialize failed`` ở cả nền GBM và X11, nguyên nhân unknown (không có màn hình, ``XDG_SESSION_TYPE=tty``) [T3 board].

6. Luồng hiện tại và việc chuyển sang phần cứng
===============================================

Luồng đang chạy của ``camera.py`` (khóa xung, trung vị) [T3 board, ``camera.py``]. ``[HW]`` là khối phần cứng, ``[CPU]`` là chạy trên CPU:

.. code:: text

    OV13855  RAW10 4224x3136, 30 khung/giây
        |  MIPI D-PHY, CSI-2
        v
    [HW] VICAP ----- RAW trực tiếp -----> [HW] ISP: debayer, khử nhiễu, gamma, cắt 16:9, thu về 640x360
                                               |  NV12 640x360 trong DDR (selfpath)
                                               v
                                          [CPU] v4l2-ctl và luồng đọc, giữ khung mới nhất
                                               v
                                          [CPU] NV12 sang BGR, cv2                       0.166 ms
                                               v
                                          [CPU] preprocess: viền 114, BGR sang RGB       0.297 ms
                                               v
                                          [CPU] RKNNLite: chuẩn hóa, lượng tử hóa, layout  (gộp trong thời gian NPU)
                                               v
                                          [HW] NPU, CORE_0, một context                 17.973 ms
                                               v
                                          [CPU] postprocess, numpy                       0.482 ms
                                               v
                                          [CPU] ByteTrack      0.190 ms (0 hộp), 5.6 ms (34 người)
                                               v
                                          [CPU] vẽ khung, libx264 (ffmpeg), JPEG bằng cv2

    Nghỉ: NPU lõi 1 và 2, RGA, VPU, JPEG encoder, GPU
    Tổng đầu cuối: 18.974 ms, chu kỳ camera 33.3 ms

Luồng đề xuất (quyết định 3, :doc:`../00-tong-quan/04-gioi-han-va-huong-phat-trien` mục 3.1) nằm ở mục 3.2 của trang đó. Bảng dưới là lý do và bằng chứng từng bước:

.. list-table::
   :header-rows: 1
   :widths: 14 20 66

   * - Bước
     - Đề xuất
     - Lý do và bằng chứng
   * - 0 đến 3
     - Giữ VICAP, ISP
     - ISP đã cắt 16:9 và thu về 640x360, ``frameloss`` 0 [T3 board, ``camera.py``]. Không khối nào thay được
   * - 4
     - RGA3 đặt ảnh mỗi khung, RGA2 tô viền một lần
     - Ở 640x360 hai lệnh ``imfill`` rồi ``improcess`` chậm hơn CPU 0.1 ms (0.569 so với 0.463 ms). Tô nền một lần thì mỗi khung chỉ còn lệnh đặt ảnh, 0.264 ms ở 640x640 và 0.184 ms ở 640x384 trên RGA3_0 (mục 3.2). RGA chậm tối đa 3.3% khi NPU chạy cùng. Ở 1080p RGA nhanh hơn CPU (2.015 so với 2.380 ms) nhưng luồng không chạy ở 1080p. Cần căn lề 16 byte, 640 và 360 đạt [T3 board, ``rga_bench.c``, ``camera.py``] [T1 RGA guide] [SL]
   * - 5
     - Zero-copy qua C API
     - Hãng ghi chuẩn hóa và lượng tử hóa chạy trên NPU ở zero-copy [T1 UG232 tr.65]. RKNNLite 2.3.2 không có API này nên phải viết bằng C. Lợi ích unknown vì thời gian sao chép chưa tách riêng
   * - 6, 7
     - Giữ trên lõi A76
     - Hậu xử lý 0.48 ms, ByteTrack 5.6 ms với 34 người. Lõi A55 làm ByteTrack mất 51.2 ms, vượt chu kỳ camera [T3 board, ``track_bench.py``]
   * - 8, ghi video
     - VPU ``rkvenc2``
     - libx264 chiếm khoảng 21.5% một lõi A55 ở 640x360. ``mpph264enc`` không chậm hơn nguồn ảnh giả ở 1080p. Ở 4K UHD từ camera, H.264 và H.265 đều đủ 30 khung/giây, cùng tải CPU. Chọn H.265 vì cùng chất lượng ở khoảng nửa bitrate, trình duyệt chỉ hỗ trợ một phần nên xem bằng player (:doc:`06-sau-npu` mục 3.1) [T3 board]. ``imrectangle`` vẽ ngay trên bộ đệm NV12 và RGB888 sang NV12 chạy cả ba khối (0.17 ms ở 640x360), nên không cần đổi sang BGR
   * - 8, vẽ khung
     - RGA2 vẽ hộp và chèn nhãn bằng job (``imbeginJob``, tối đa 12 hộp mỗi job)
     - 34 hộp 1.60 ms ở 640x360 và 2.03 ms ở 4K, so với 11.67 và 12.78 ms khi mỗi hộp một lệnh. 34 nhãn 0.52 ms (mục 3.2). Bộ đệm cho RGA2 phải nằm dưới 4 GB: bộ đệm camera đạt (28 trên 28), bộ đệm MPP DRM không đảm bảo (7 trên 10) [T3 board]
   * - 8, ảnh mẫu
     - JPEG encoder
     - ``cv2`` vẽ và mã hóa 3.76 ms trung vị ở luồng nền, chưa biết riêng phần mã hóa. ``mppjpegenc`` có trên board [T3 board]
   * - 8, giao diện, hiển thị
     - GPU rồi VOP2
     - Chỉ khi có giao diện và màn hình. ``HDMI-A-1`` và ``DP-1`` ``disconnected`` lúc đọc [T3 board, ``/sys/class/drm``]. Không có giao diện thì khung đã vẽ đi thẳng RGA sang VOP2

Không khối nào chặn 30 FPS vì 18.97 ms nhỏ hơn chu kỳ 33.3 ms. ``camera.py`` dùng khoảng 16% CPU tiến trình và 15% CPU hệ thống khi khóa xung, ghi video thêm 2 đến 3 điểm phần trăm [T3 board]. Chuyển sang phần cứng chỉ giảm các phần này, lợi ích đo được chưa có. Lõi A55 (cpu0 đến 3) chạy luồng nền ``ffmpeg``, lõi A76 (cpu4 đến 7) giữ vòng chính.

7. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 44 56

   * - Điều chưa biết
     - Cần để xác minh
   * - Tiền xử lý và hậu xử lý bằng OpenCL trên Mali-G610, kể cả chi phí sao chép
     - Viết kernel NV12 sang RGB cộng viền, đo cùng điều kiện ``camera.py``
   * - Vulkan chạy được không
     - Cài ``vulkan-tools``, chạy ``vulkaninfo``
   * - Nguồn của 13 và 8 ngắt GPU
     - Đọc ``/proc/interrupts`` hai lần khi board nghỉ, so với lần có camera
   * - RGA khi CPU và NPU cùng bận
     - Chạy ``rga_bench`` cùng ``camera.py``
   * - Lợi ích CPU của ``mpph264enc`` và ``mppjpegenc`` so với libx264 và ``cv2`` ở nội dung thật
     - Thay ``--save-video`` bằng GStreamer, đo CPU
   * - ``imosd``, RGA2 vẽ lên khung camera đang stream (đã thử bộ đệm chưa stream), và bộ đệm MPP loại ``DMA_HEAP`` hoặc ``DRM`` kèm ``CONTIG``
     - Stream camera vào bộ đệm EXPBUF rồi vẽ, kiểm ``dmesg`` và ảnh ra. Tìm vì sao ``DMA_HEAP`` cho ``fd`` không dùng được
   * - Chi phí CPU của riêng ``cv2.rectangle`` và ``cv2.putText`` trên khung 640x360 có 34 hộp
     - Đo riêng
   * - ``improcess`` thêm viền trong một lệnh, RGA đổi BGR sang NV12
     - Thử ``imcvtcolor`` và đích có viền
   * - Zero-copy qua C API có giảm ``T_npu`` không
     - :doc:`../03-phuong-phap/03-tang-npu-don-bay/06-memory-copy`
