:tocdepth: 1

****************
ISP và vòng 3A
****************

.. admonition:: Trang này trả lời

   - ISP có những cổng nào, nhận gì và trả gì?
   - Những khối xử lý nào đang bật khi chụp?
   - Vòng 3A nối ISP, CPU và cảm biến ra sao?

.. admonition:: Tóm tắt

   1. ISP nhận RAW ``SBGGR10_1X10`` 4224x3136, trả ``YUYV8_2X8`` 4224x3136 ở cổng nguồn, rồi ghi ra nhánh ``rkisp_mainpath`` (tối đa 4224x3136) hoặc ``rkisp_selfpath`` (tối đa 1920 rộng) [T3 board, ``media-ctl``, ``v4l2-ctl --list-formats-ext``, ``--try-fmt-video``].
   2. ISP xuất trực tiếp NV12 640x360 (cả hai nhánh) và 640x640 (selfpath) ở 29.95 fps, nên có thể thu nhỏ ngay tại ISP [T3 board, ``v4l2-ctl --stream-mmap``].
   3. Đang bật: DPCC, BLS, LSC, DEBAYER, CCM, GAMMA_OUT, CPROC, BAYNR, BAY3D, YNR, CNR, SHARP, DHAZ, GAIN và các khối thống kê. HDR và 3DLUT đang tắt [T3 board, ``/proc/rkisp0-vir1``].
   4. Vòng 3A: ISP ghi thống kê, tiến trình ``rkaiq_3A_server`` đọc rồi ghi tham số. Tiến trình chạy trên CPU là suy luận [SL] [T3 board, ``media-ctl``, ``pgrep``].
   5. Luồng chạy trên ISP0 (``fdcb0000``): thuộc tính ``rockchip,hw`` của ``rkisp0-vir1`` trỏ tới nút này [T3 board, ``/proc/device-tree``].
   6. ISP cắt được 16:9 bằng ``VIDIOC_S_SELECTION``: ``Dcrop(0,380|4224x2376)`` ra 1920x1080 ở 29.95 fps [T3 board, ``v4l2-ctl --set-selection``, ``/proc/rkisp0-vir1``].
   7. Chưa biết: thứ tự các khối trong chip, nội dung tệp IQ, việc ``librkaiq`` dùng ``librga.so`` vào việc gì.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cổng của ISP
===============

.. code:: text

     rkcif-mipi-lvds1 (VICAP)
           |  RAW10 SBGGR10 4224x3136 @30, online
           v
   +----------------------------------------------------+
   | rkisp-isp-subdev (v4l-subdev3)                     |
   | pad0 sink   <- ảnh RAW                             |
   | pad1 sink   <- rkisp-input-params (video19)        |
   | pad2 source -> ảnh YUV, YUYV8_2X8 4224x3136        |
   | pad3 source -> rkisp-statistics (video18)          |
   +----------------------------------------------------+

           | pad2, cả bốn đích đều ENABLED
           +--> rkisp_mainpath (video11): tối đa 4224x3136
           +--> rkisp_selfpath (video12): tối đa 1920 rộng, 3136 cao
           +--> rkisp_fbcpath  (video13)
           +--> rkisp_iqtool   (video14)

     Không bật: rkisp_rawrd0_m, rkisp_rawrd1_l, rkisp_rawrd2_s (đọc lại RAW từ DDR)

Nguồn: [T3 board, ``media-ctl -d /dev/media1 -p``]. Định dạng ra nhánh ``rkisp_mainpath``: UYVY, NV16, NV61, NV21, NV12, NM21, NM12. Nhánh ``rkisp_selfpath`` thêm GREY và RGBP [T3 board, ``v4l2-ctl -d /dev/video11 --list-formats-ext``, ``-d /dev/video12``]. Driver khai báo trong ``capture.c`` các định dạng FBC0, FBC2, FBCG, GREY, NV12, NV12M, NV16, NV21, NV21M, NV61, UYVY, VYUY, YUV420, YUV422P, YUV444M, YUYV, YVU420, YVU422M, YVYU [Mã nguồn kernel, ``drivers/media/platform/rockchip/isp/capture.c``]. RGBP không có trong tệp này.

``YUYV8_2X8`` là định dạng trên pad của subdev ISP, còn NV12, UYVY... là định dạng ghi ra bộ nhớ trên nút video. Hai tầng khác nhau, nên pad ra ``YUYV8_2X8`` mà nút video vẫn cho NV12 [T3 board, ``media-ctl -d /dev/media1 -p``, ``v4l2-ctl --list-formats-ext``].

Giới hạn kích thước của selfpath có một mâu thuẫn chưa giải quyết. Board liệt kê tối đa 1920 rộng, 3136 cao. Mã nguồn kernel khai báo hằng ``STREAM_MAX_SP_RSZ_OUTPUT_*`` là 1920x1080 [Mã nguồn kernel, ``isp/capture.h:63-64``]. Lý do khác biệt: unknown.

Các trích dẫn mã nguồn kernel trong trang này chưa ghi cây kernel và commit, nên số dòng chưa chắc khớp bản 6.1.99-rockchip-rk3588 đang chạy trên board: unknown.

2. Thông lượng theo kích thước
==============================

.. list-table::
   :header-rows: 1
   :widths: 30 24 24 22

   * - Kích thước NV12
     - mainpath
     - selfpath
     - Nguồn
   * - 1920x1080
     - 29.94 fps
     - 29.94 fps
     - [T3 board, ``v4l2-ctl --stream-mmap --stream-count=120``]
   * - 640x360
     - 29.95 fps
     - 29.95 fps
     - [T3 board, ``--stream-count=90``]
   * - 640x640
     - chưa đo
     - 29.95 fps
     - [T3 board, ``v4l2-ctl --stream-mmap --stream-count=90``]
   * - 1920x1080, đã cắt ``Dcrop(0,380|4224x2376)``
     - chưa đo
     - 29.95 fps, ``frameloss:0``
     - [T3 board, ``v4l2-ctl --set-selection``, ``/proc/rkisp0-vir1``]

Cắt và thu nhỏ: ``VIDIOC_S_SELECTION`` trên ``rkisp_selfpath`` đặt vùng cắt ``top=380, height=2376`` (4224x2376, tỉ lệ 16:9, khoảng 10,04 triệu điểm ảnh [SL, phép nhân]). Sau đó ``/proc/rkisp0-vir1`` ghi ``Output rkisp_selfpath Format:NV12 Size:1920x1080 Dcrop(0,380|4224x2376) frameloss:0``. Vùng cắt giữ nguyên giữa các lần mở nút, nên phải đặt lại ``top=0, height=3136`` sau khi dùng (đã đặt lại và đọc lại xác nhận) [T3 board, ``v4l2-ctl --set-selection``, ``--get-selection``]. Thu nhỏ 4224x2376 xuống 1920x1080 cùng hệ số 0.4545 cho cả hai chiều [SL].

Kích thước ảnh một khung NV12 640x360 là 345600 byte [T3 board, ``v4l2-ctl --try-fmt-video``]. Cảm biến vẫn chạy 4224x3136 ở 30 fps và ``Dcrop(0,0|4224x3136)`` là cả khung [T3 board, ``/proc/rkisp0-vir1``]. Suy ra ISP thu nhỏ cả khung xuống kích thước đầu ra, và giới hạn 30 fps đến từ cảm biến [SL].

3. Khối xử lý đang bật
======================

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Trạng thái
     - Khối
   * - Bật
     - DPCC0, DPCC1, DPCC2, BLS, LSC, AWBGAIN, DEBAYER, CCM, GAMMA_OUT, CPROC, BAYNR, BAY3D, YNR, CNR, SHARP, DHAZ, CSM, GAIN
   * - Bật (thống kê)
     - RAWAF, RAWAWB, RAWAE0, RAWAE1, RAWAE2, RAWAE3, RAWHIST0, RAWHIST1, RAWHIST2, RAWHIST3
   * - Tắt
     - FPN, CMSK, SDG, IE, HDRDRC, HDRMGE, GIC, 3DLUT, LDCH, CAC
   * - Chế độ
     - ``BigMode`` ghi ON (0x30000018). Là bit 28 của thanh ghi ``ISP_CTRL1``, driver tự đặt theo kích thước ảnh vào. Khi bật, stride của ảnh ra căn 32 thay vì 16 [Mã nguồn kernel, ``isp/procfs.c:340``, ``isp/isp_params_v3x.c:4203-4433``, ``isp/capture.c:768``]

Nguồn: [T3 board, ``/proc/rkisp0-vir1`` lúc đang chụp]. Xung ``clk_isp_core`` là 702 MHz lúc chụp và 300 MHz lúc nghỉ [T3 board, ``/proc/rkisp0-vir1``]. Danh sách do ``rkaiq`` đặt theo tệp IQ ``ov13855_CMK-OT2016-FV1_default.json`` nên không phải giới hạn phần cứng [SL] [T3 board, ``ls /etc/iqfiles``]. Thứ tự xử lý thật trong chip: unknown. Datasheet ghi ISP là phần cứng hoàn toàn:

   "RK3588S introduces a new generation totally hardware-based maximum 48-Megapixel ISP (image signal processor)." [T1 DS V1.7 tr.7]

TRM1 và TRM2 không có chương ISP. Datasheet chỉ có danh sách tính năng ISP (tr.12), không nêu định dạng ra. Định dạng ra ở trên chỉ có nguồn T3. Hai mục CSM (bật) và SDG (tắt) chưa được kiểm lại lần hai.

Datasheet giải nghĩa được một phần tên khối:

- "DPCC: Static/Dynamic defect pixel cluster correction" [T1 DS V1.7 tr.12]
- "LSC: Lens shading correction" [T1 DS V1.7 tr.12]
- "Bayer-2DNR: Spatial Bayer-raw De-noising" và "Bayer-3DNR: Temporal Bayer-raw De-noising" [T1 DS V1.7 tr.12]
- "YUV-2DNR: Spatial YUV De-noising" [T1 DS V1.7 tr.12]
- "CCM/CSM: Color correction matrix; RGB2YUV etc" [T1 DS V1.7 tr.12]
- "Gamma: Gamma out correction" [T1 DS V1.7 tr.12]
- "Dehaze/Enhance: Automatic Dehaze and Effect enhancement" [T1 DS V1.7 tr.12]
- "HDR: 3-Frame Merge into High-Dynamic Range" [T1 DS V1.7 tr.12]

Ghép tên khối với tên trong datasheet là suy luận theo tên [SL]: BAYNR là Bayer-2DNR, BAY3D là Bayer-3DNR, YNR và CNR là YUV-2DNR, DHAZ là Dehaze, GAMMA_OUT là Gamma, HDRMGE là HDR 3-frame merge, các khối RAWAE, RAWAF, RAWAWB, RAWHIST là thống kê cho 3A. DEBAYER không có trong danh sách datasheet, theo tên là nội suy màu từ ảnh Bayer. Các khối còn lại (BLS, AWBGAIN, CPROC, SHARP, GAIN, GIC, 3DLUT, LDCH, CAC, FPN, CMSK, SDG, IE, HDRDRC): datasheet không giải nghĩa, unknown.

4. Vòng 3A
==========

3A là nhóm ba bài toán tự động của camera: phơi sáng (AE), cân bằng trắng (AWB) và lấy nét (AF) [SL, theo cách gọi thông dụng]. Datasheet ghi ISP xuất thống kê cho chúng:

   "3A: include AE/Histogram, AF, AWB statistics output" [T1 DS V1.7 tr.12]

.. code:: text

    khung RAW vào ISP
       |
       v
    ISP xử lý ---------------------------------> NV12 vào DDR (mainpath hoặc selfpath)
       |
       +--> khối thống kê: RAWAE0-3, RAWAF, RAWAWB, RAWHIST0-3
                 |
                 v
           bộ đệm thống kê, nút rkisp-statistics (video18)
                 |
                 v
           rkaiq_3A_server (CPU [SL]) tính AE, AWB, AF
                 |
                 +--> tham số ISP, nút rkisp-input-params (video19) ----> về ISP
                 |
                 +--> exposure, gain, focus qua I2C ----------------------> cảm biến, VCM  [SL]

``rkaiq_3A_server`` là tiến trình người dùng đang chạy [T3 board, ``pgrep``]. ``ldd`` không thấy thư viện OpenCL hay Mali nhưng không loại trừ thư viện nạp lúc chạy, và ``/proc/<pid>/maps`` bị chặn quyền root [T3 board, ``ldd``]. Thời gian CPU tích lũy của các luồng là 00:00:00 [T3 board, ``ps -L``]. ``ps`` chỉ hiển thị đến giây nên con số này chỉ cho biết tổng dưới 1 giây. Lúc đo có luồng chụp đang chạy hay không chưa ghi lại, nên không dùng làm bằng chứng: unknown. Chạy trên CPU là suy luận [SL]: ``readelf -d /lib/librkaiq.so`` chỉ liệt kê libdl, libdrm, libpthread, libstdc++, libm, libgcc_s, libc, ``strings`` không thấy OpenCL, Mali, GLES, EGL và có chuỗi ``librga.so`` [T3 board, ``readelf -d``, ``strings``]. Việc ``rkaiq`` đặt exposure, gain và focus qua I2C là suy luận [SL].

5. Hai nút ISP phần cứng
========================

Dmesg ghi hai nút ``rkisp_hw`` đã probe: ``fdcb0000.rkisp`` (nhóm IOMMU 15) và ``fdcc0000.rkisp`` (nhóm IOMMU 16) [T3 board, ``dmesg``]. Thuộc tính ``rockchip,hw`` của ``rkisp0-vir1`` trong device-tree bằng 0x64, đúng phandle của ``rkisp@fdcb0000``. Nút ``fdcc0000`` có phandle 0x68 và ``rkisp0-vir1`` không trỏ tới nó [T3 board, ``/proc/device-tree``]. Vậy luồng camera chạy trên ISP0 (``fdcb0000``). Device-tree còn có nút ``rkisp-unite@fdcb0000``, trạng thái chưa đọc [T3 board, ``/proc/device-tree``].
