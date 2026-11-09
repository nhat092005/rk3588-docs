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

Giới hạn kích thước của selfpath có một mâu thuẫn chưa giải quyết: board liệt kê tối đa 1920 rộng, 3136 cao, còn mã nguồn kernel khai báo ``STREAM_MAX_SP_RSZ_OUTPUT_*`` là 1920x1080 [Mã nguồn kernel, ``isp/capture.h:63-64``]. Lý do khác biệt: unknown.

**Chạy nhiều nhánh cùng lúc.** Ngày 2026-11-08, hai ``v4l2-ctl --stream-mmap`` song song trên ``rkisp_mainpath`` (video11) và ``rkisp_selfpath`` (video12), cả hai NV12 640x360, mỗi nhánh 300 khung: 29.95 khung/giây ở cả hai, đủ 300 khung, ``frameloss:0``. Hai nhánh có vùng cắt riêng (lúc đo ``Dcrop(0,0|1920x1080)`` ở mainpath, ``Dcrop(0,0|4224x3136)`` ở selfpath). Board có ba nút ghi ra bộ nhớ: mainpath, selfpath và ``rkisp_fbcpath`` (video13). Cả ba chạy cùng lúc: 200 khung mỗi nhánh, 29.95 khung/giây, ``frameloss:0`` (fbcpath ``FBC0`` 4224x3136) [T3 board, ``v4l2-ctl --stream-mmap``, ``/proc/rkisp0-vir1``]. Các phép thử ghi ra ``/dev/null``, chưa có NPU, RGA hay VPU chạy cùng, nên tải DDR khi cả ba nhánh ghi kèm NPU chưa đo.

**Đổi định dạng khi nhánh khác đang chạy.** Ghi 4K mainpath và 640x360 selfpath cùng lúc (cho VPU mã hóa) chạy được nếu cấu hình xong hai nút trước khi bắt đầu: ``S_FMT`` trên một nút bị từ chối (``EBUSY``) khi nút kia đang phát. GStreamer ``v4l2src`` trên selfpath đặt lại vùng cắt về (0,0|640x360), nên với selfpath phải dùng ``v4l2-ctl --stream-mmap`` [T3 board, ``v4l2-ctl``, ``gst-launch-1.0``].

**FBC.** FBC là nén khung ảnh (Frame Buffer Compress): mỗi khối 16x16 điểm ảnh có một đầu mục 128 bit kèm luồng dữ liệu nén, bộ nhớ cần tối đa bằng ảnh không nén [T1 TRM1 tr.372, mục 5.3.8]. ``fbcpath`` chỉ ra ảnh toàn khung 4224x3136 ở ``FBC0`` (YUV420) hoặc ``FBC2`` (YUV422), không có NV12 [T3 board, ``v4l2-ctl -d /dev/video13 --list-formats-ext``]. MPP gọi định dạng nén của ISP là ``AFBC_V1`` [T3 board, ``/usr/include/rockchip/mpp_frame.h``]. Khối đọc được ảnh nén: RGA3 (``FBCD -> RASTER``) [T1 TRM2 tr.701], VOP2 (``AFBCD``) [T1 DS V1.7 tr.13]. RGA2 không đọc FBC. Bộ mã hóa VPU (VEPU580) liệt kê "Frame Buffer Compression" trong định dạng đầu vào, cho H.265 và H.264 [T1 TRM1 tr.385, Table 5-18, tiêu đề cột bảng ghi "Decoder support", có vẻ là lỗi của TRM]. Chưa biết định dạng nén của ISP có đúng loại bộ mã hóa nhận không. Plugin GStreamer ``mpph265enc`` chỉ khai báo đầu vào NV12, I420, RGB và các định dạng thô khác, không có định dạng nén [T3 board, ``gst-inspect-1.0 mpph265enc``]. Mục đích nhánh này là giảm băng thông DDR khi cần ảnh toàn khung [SL]: NV12 4224x3136 nặng 19.9 MB mỗi khung, 596 MB/s ở 30 khung/giây. Mức nén của ``FBC0`` trên cảnh thực: unknown. 10 khung ``FBC0`` đọc ra mỗi khung 20,701,184 byte, lớn hơn NV12 cùng kích thước (19,869,696 byte). Đây là kích thước vùng cấp cố định, không cho biết mức nén [T3 board, ``v4l2-ctl --stream-mmap``]. Ép ``fbcpath`` ra 3840x2160 thì driver trả lại 4224x3136. Cắt 16:9 (``--set-selection`` đỉnh 380, cao 2376) được và ra 4224x2376 với 15,735,808 byte mỗi khung, nhưng không thu nhỏ về 3840x2160 [T3 board, ``v4l2-ctl -d /dev/video13``, 2026-11-08]. Thử trên khung ``FBC0`` thật 4224x3136 (khung thứ 6 của luồng, cảnh trong nhà) [T3 board, 2026-11-08, ``experiments/camera/enc_rga_2026-11-08/fbc_rga.cpp`` và ``fbc_mpp.cpp``]:

- RGA3_0 và RGA3_1 đọc FBC ra NV12 thô thành công, ảnh ra đúng (kiểm bằng mắt).
- RGA2 đọc FBC thất bại. ``imrectangle`` và ``imfill`` trên bộ đệm FBC thất bại ở cả ba lõi.
- Bộ mã hóa H.265 qua API MPP, đầu vào ``AFBC_V1`` (bố cục bộ nhớ khớp 20,701,184 byte của V4L2), chỉ ra một gói tiêu đề 305 byte, không có ảnh, và nhân ghi một lỗi IOMMU ``Page fault`` khi đọc. Cùng chương trình với NV12 thô cho khung IDR 383,120 byte và không có lỗi IOMMU. Nguyên nhân VPU không đọc được khung FBC chưa rõ, có thể do cách cấu hình MPP của tôi.

Dự án không dùng ``fbcpath`` (quyết định 12 trong :doc:`../00-tong-quan/04-gioi-han-va-huong-phat-trien`) vì ba điều đã đo: ``fbcpath`` không thu nhỏ về 3840x2160 như quyết định 4, RGA2 không vẽ được trên khung FBC, và VPU chưa nhận được khung FBC trong thử nghiệm này.

``/proc/rkisp0-vir1`` ghi ``Version:v02.09.00``, trùng với dòng ``rkisp driver version: v02.09.00`` trong dmesg. Đó là phiên bản driver, không phải phiên bản phần cứng ISP. Mã phần cứng (``ISP:0x60``) có nghĩa gì: unknown [T3 board, ``/proc/rkisp0-vir1``, ``dmesg``].

Các trích dẫn mã nguồn kernel ở trang này chưa ghi cây kernel và commit, nên số dòng chưa chắc khớp bản 6.1.99-rockchip-rk3588 trên board: unknown.

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

Datasheet giải nghĩa một phần tên khối [T1 DS V1.7 tr.12]: DPCC là sửa điểm ảnh lỗi tĩnh và động, LSC là sửa tối góc ống kính, Bayer-2DNR và Bayer-3DNR là khử nhiễu không gian và thời gian trên ảnh Bayer, YUV-2DNR là khử nhiễu không gian trên YUV, CCM/CSM là ma trận màu và đổi RGB sang YUV, Gamma là hiệu chỉnh gamma ra, Dehaze/Enhance là khử sương và tăng hiệu ứng, HDR là ghép 3 khung thành dải động cao. Ghép tên khối với tên trong datasheet là suy luận theo tên [SL]: BAYNR là Bayer-2DNR, BAY3D là Bayer-3DNR, YNR và CNR là YUV-2DNR, DHAZ là Dehaze, GAMMA_OUT là Gamma, HDRMGE là HDR 3-frame merge, RAWAE, RAWAF, RAWAWB, RAWHIST là thống kê cho 3A. DEBAYER không có trong danh sách datasheet, theo tên là nội suy màu từ ảnh Bayer. Các khối còn lại (BLS, AWBGAIN, CPROC, SHARP, GAIN, GIC, 3DLUT, LDCH, CAC, FPN, CMSK, SDG, IE, HDRDRC): datasheet không giải nghĩa, unknown.

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

``rkaiq_3A_server`` là tiến trình người dùng đang chạy [T3 board, ``pgrep``]. Nó chạy trên CPU và đặt exposure, gain, focus qua I2C là suy luận [SL]: ``librkaiq.so`` chỉ liên kết libdl, libdrm, libpthread, libstdc++, libm, libgcc_s, libc, ``strings`` không thấy OpenCL, Mali, GLES, EGL và có chuỗi ``librga.so`` [T3 board, ``readelf -d``, ``strings``]. Chưa loại trừ thư viện nạp lúc chạy vì ``/proc/<pid>/maps`` bị chặn quyền root. Chi tiết bằng chứng ở :doc:`01-buc-tranh-tong-the` mục 4.

5. Hai nút ISP phần cứng
========================

Dmesg ghi hai nút ``rkisp_hw`` đã probe: ``fdcb0000.rkisp`` (nhóm IOMMU 15) và ``fdcc0000.rkisp`` (nhóm IOMMU 16) [T3 board, ``dmesg``]. Thuộc tính ``rockchip,hw`` của ``rkisp0-vir1`` trong device-tree bằng 0x64, đúng phandle của ``rkisp@fdcb0000``. Nút ``fdcc0000`` có phandle 0x68 và ``rkisp0-vir1`` không trỏ tới nó [T3 board, ``/proc/device-tree``]. Vậy luồng camera chạy trên ISP0 (``fdcb0000``). Device-tree còn có nút ``rkisp-unite@fdcb0000``, trạng thái chưa đọc [T3 board, ``/proc/device-tree``].
