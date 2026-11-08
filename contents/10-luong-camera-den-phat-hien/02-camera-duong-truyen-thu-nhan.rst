:tocdepth: 1

**************************
Cảm biến và đường truyền
**************************

.. admonition:: Trang này trả lời

   - Cảm biến xuất định dạng gì, và đi qua D-PHY, CSI-2, VICAP thế nào để đến ISP?
   - Băng thông MIPI có đủ cho 4224x3136 ở 30 khung/giây không?
   - Chuỗi thực thể media trên board nối các khối ra sao?

.. admonition:: Tóm tắt

   1. Cảm biến chỉ liệt kê một mã định dạng ``SBGGR10_1X10``, một kích thước 4224x3136 và một chu kỳ khung 30 fps [T3 board, ``v4l2-ctl --list-subdev-mbus-codes``, ``--list-subdev-framesizes``, ``--list-subdev-frameintervals``].
   2. Tốc độ mỗi lane là 1080 Mbps và số lane hiệu dụng là 4. Device-tree ghi ``data-lanes = <1 2>`` nhưng khi bắt đầu phát luồng driver PHY ghi đè bằng số lane cảm biến báo, và driver ``ov13855`` báo 4 [T1 DRV ``phy-rockchip-csi2-dphy.c:448-461``, ``ov13855.c:1656-1661``] [T3 board, ``/proc/rkcif-mipi-lvds1``, ``dmesg``].
   3. VICAP chạy chế độ online, đưa RAW thẳng vào ISP và không cấp bộ đệm DDR [T3 board, ``/proc/rkcif-mipi-lvds1``].
   4. Chuỗi gồm hai thiết bị media: ``/dev/media0`` (rkcif) và ``/dev/media1`` (rkisp0). Thực thể ``rkcif-mipi-lvds1`` xuất hiện trong ``/dev/media1`` làm nguồn cho ISP [T3 board, ``media-ctl -p``].
   5. Chưa biết: cổng vật lý của overlay ``c3``, ảnh hưởng của cảnh báo vblank, và mã nguồn driver có trùng bản build kernel 6.1.99 trên board hay không.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Module camera và các bus
===========================

.. code:: text

   +--------------------------------------------------------------+
   | module camera OV13855                                        |
   | cảm biến ov13855 (I2C 0x36)      VCM dw9714 (I2C 0x0c)       |
   +--------------------------------------------------------------+
             | MIPI CSI-2 (số lane: mục 3)     | I2C bus 2
             v                                 v
     SoC: D-PHY                        SoC: bộ điều khiển I2C

OV13855 là cảm biến 13 megapixel của OmniVision:

   "13MP (4224x3136): 30 fps" [T1 OVT brief v1.2]

OVT brief v1.2 là bản brief của OmniVision lấy từ trang mirror của nhà phân phối (``https://www.micro-semiconductor.fr/datasheet/6d-OV13855-G04A.pdf``), chưa lưu trong ``docs/_assets/pdf``.

Cảm biến và VCM nằm trên I2C bus 2, địa chỉ 0x36 và 0x0c [T3 board, ``/sys/bus/i2c/devices/2-0036/name``, ``2-000c/name``]. Cổng FPC vật lý trên Orange Pi 5 ứng với overlay ``c3``: unknown.

2. Chuỗi thực thể media
=======================

.. code:: text

    /dev/media0 (rkcif)
    m02_b_ov13855 2-0036              v4l-subdev2
      pad0 source   SBGGR10_1X10 4224x3136 @30
           |
           v
    rockchip-csi2-dphy0               v4l-subdev1
      pad0 sink -> pad1 source        SBGGR10_1X10 4224x3136
           |
           v
    rockchip-mipi-csi2                v4l-subdev0
      pad0 sink -> pad1 source        SBGGR10_1X10 4224x3136
           |        -> stream_cif_mipi_id0..3 (video0..3), rkcif_scale_ch0..3 (video4..7)
           |        -> rkcif_tools_id0..2 (video8..10)
           v
      (liên kết nội bộ rkcif, không hiện trong media-ctl)
           |
           v
    /dev/media1 (rkisp0-vir1)
    rkcif-mipi-lvds1                  v4l-subdev4
      pad0 source   SBGGR10_1X10 4224x3136 @30
           |
           v
    rkisp-isp-subdev                  v4l-subdev3   (trang ISP)

Nguồn: [T3 board, ``media-ctl -d /dev/media0 -p``, ``media-ctl -d /dev/media1 -p``]. Các nút ``stream_cif_mipi_id0..3``, ``rkcif_scale_ch0..3`` và ``rkcif_tools_id0..2`` là nút của VICAP. Chưa thấy chúng dùng khi ISP chạy online (``dma enable: 0x0``) [SL].

3. Băng thông MIPI
==================

.. code:: text

    tải ảnh  = 4224 x 3136 x 30 khung/giây x 10 bit    = 3974 Mbps  (chưa tính blanking)
    đường MIPI:
      4 lane x 1080 Mbps                                 = 4320 Mbps  (đủ, dư 346 Mbps)
      2 lane x 1080 Mbps                                 = 2160 Mbps  (không đủ)

Số đo: ``link_frequency`` 540 MHz (DDR nên 1080 Mbps mỗi lane, khớp ``data_rate_mbps 1080``), ``format:SBGGR10_1X10/4224x3136@30`` và ``pixel_rate`` 432000000 [T3 board, ``v4l2-ctl --list-ctrls``, ``/proc/rkcif-mipi-lvds1``, ``dmesg``]. Số lane có hai giá trị ở hai thời điểm. Device-tree ghi ``data-lanes = <1 2>`` (hai lane) và driver PHY đọc giá trị này khi cảm biến được gắn (``sensor->lanes = s_asd->lanes``). Khi bắt đầu phát luồng, ``csi2_dphy_update_sensor_mbus`` gọi ``get_mbus_config`` của cảm biến rồi ghi đè ``sensor->lanes`` bằng ``num_data_lanes``, và driver ``ov13855`` trả ``OV13855_LANES`` bằng 4. Driver DC-PHY bật các lane theo ``sensor->lanes`` [T1 DRV ``drivers/phy/rockchip/phy-rockchip-csi2-dphy.c:448-461, 871, 986``, ``phy-rockchip-samsung-dcphy.c:2013-2054``, ``drivers/media/i2c/ov13855.c:82, 1656-1661``]. ``/proc/rkcif-mipi-lvds1`` báo ``lanes:4`` [T3 board, ``/proc/rkcif-mipi-lvds1``]. Vậy số lane hiệu dụng là 4. Mã nguồn lấy từ nhánh ``orange-pi-6.1-rk35xx``, commit ``f6eedab0cbe9``, chưa xác minh trùng bản build kernel 6.1.99 đang chạy. Phép tính băng thông cũng cần hơn 2 lane [SL]. Datasheet ghi giới hạn lane D-PHY:

   "Each MIPI DPHY V1.2, 4lanes, 2.5Gbps per lane" [T1 DS V1.7 tr.11]

4. Điều khiển của cảm biến
==========================

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Control
     - Giá trị
     - Nguồn
   * - ``exposure``
     - 4 đến 3210, mặc định 2048, đọc được 289 rồi 2893 ở hai lần đọc (đổi theo cảnh)
     - [T3 board, ``v4l2-ctl --list-ctrls``]
   * - ``analogue_gain``
     - 128 đến 1984, mặc định 128
     - như trên
   * - ``vertical_blanking``
     - 78 đến 29631
     - như trên
   * - ``link_frequency``
     - menu 0 đến 1, đang chọn 0 = 540000000
     - như trên
   * - ``test_pattern``
     - 0 đến 4, đang Disabled
     - như trên

5. Overlay ``ov13855-c3``
=========================

Overlay trên board nhắm các nút sau [T3 board, ``dtc -I dtb -O dts /boot/dtb/rockchip/overlay/rk3588-ov13855-c3.dtbo``]:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Nút device-tree
     - Vai trò theo tên
   * - ``csi2_dcphy1``
     - PHY MIPI
   * - ``mipi1_csi2``
     - CSI-2 host
   * - ``rkcif_mipi_lvds1`` và ``rkcif_mipi_lvds1_sditf``
     - VICAP và cầu nối sang ISP
   * - ``rkcif`` và ``rkcif_mmu``
     - Khối VICAP chung và IOMMU của nó
   * - ``rkisp0_vir1``, ``rkisp0`` và ``isp0_mmu``
     - ISP và IOMMU của nó
   * - ``i2c2``
     - Bus I2C có cảm biến và VCM

Dmesg ghi ``rockchip-csi2-dphy csi2-dcphy1: dphy0 matches m02_b_ov13855 2-0036`` và ``csi2 dphy0 probe successfully!``. Nút ``csi2_dcphy1`` của overlay tạo thực thể logic ``dphy0``, nên thực thể media ``rockchip-csi2-dphy0`` ứng với nút này [T3 board, ``dmesg``].

6. VICAP
========

Datasheet ghi VICAP nhận được các định dạng sau và cho RAW đi thẳng sang ISP:

   "Support five CSI data formats: RAW8/10/12/14, YUV422" [T1 DS V1.7 tr.12]

   "Support RAW data through to ISP0/1" [T1 DS V1.7 tr.12]

TRM mô tả hai đường ra của VICAP:

   "The Video Capture, receives the data from Camera via DVP/MIPI, and transfers the data into system main memory by AXI bus." [T1 TRM1 tr.2058]

   "The parsed video data can go straight to ISP0/1 for real-time processing." [T1 TRM1 tr.2062]

Trên board, ``/proc/rkcif-mipi-lvds1`` ghi ``Work Mode:ping pong``, ``rdbk_mode: online``, các xung ``aclk_cif`` 750 MHz, ``hclk_cif`` 198 MHz, ``dclk_cif`` 594 MHz [T3 board, ``/proc/rkcif-mipi-lvds1``].

Khi bật luồng, dmesg có cảnh báo:

   ``rkcif-mipi-lvds1: Warning: vblank need >= 1000us if isp work in online, cur 808 us`` [T3 board, ``dmesg``]

Cảnh báo này có gây mất khung hay không: unknown. ISP báo ``frameloss:0`` trong 114 khung đã đọc [T3 board, ``/proc/rkisp0-vir1``].
