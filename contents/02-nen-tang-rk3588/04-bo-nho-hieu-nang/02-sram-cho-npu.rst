:tocdepth: 1

************
SRAM cho NPU
************

.. admonition:: Trang này trả lời

   - Bật SRAM cho NPU bằng cách nào, và kiểm tra nó đã được cấp chưa?
   - Khi nào SRAM đáng dùng, đọc con số nào để ước lượng lợi ích?
   - SRAM có những giới hạn và điểm chưa rõ nào?

.. admonition:: Tóm tắt

   - Phần cứng SRAM (1MB, vùng cấp được 956KB, chia sẻ với codec) nằm ở trang gốc :ref:`system-sram-dung-chung-npu`. Trang này chỉ nói cách dùng.
   - Cần ba điều kiện: driver từ 0.8.0, kernel bật ``CONFIG_ROCKCHIP_RKNPU_SRAM=y``, và DTS cấp một vùng SRAM cho node NPU [T1 SRAM-zh 21-22] [T1 UG232 tr.106].
   - Có hai đường bật: biến môi trường (Internal và Weight, có chỉ định kích thước) và cờ ``RKNN_FLAG_ENABLE_SRAM`` trong ``rknn_init()`` (chỉ nói Internal Tensor) [T1 SRAM-zh 83-111] [T1 UG232 tr.107].
   - Mục đích là giảm áp lực băng thông DDR, nhưng "it may have a certain impact on inference time", nên phải đánh giá từng mô hình [T1 UG232 tr.106].
   - Log ``RKNN_LOG_LEVEL=3`` in sẵn ``SramHit`` từng lớp và ``Predict SRAM Hit RW Amount`` (số dự đoán lượng đọc ghi DDR tiết kiệm mỗi frame) [T1 UG232 tr.110].
   - Context khác không dùng lại vùng SRAM đã bị một context chiếm, và ``RKNN_FLAG_SHARE_SRAM`` chưa được implement [T1 UG232 tr.108].
   - Hai tài liệu ghi hai ngưỡng ``librknnrt.so`` khác nhau (">=1.3.4b14" và ">=1.6.0"), nguồn không giải thích [T1 SRAM-zh 76] [T1 UG232 tr.107].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _sram-cho-npu:

1. Cấu hình
===========

Nền. NPU đọc ghi tensor qua DDR theo mặc định. System SRAM nằm trong SoC, nên một phần tensor đặt vào SRAM thì phần đó không đi qua DDR. Dung lượng, địa chỉ, ví dụ DTS cấp 956KB và việc SRAM dùng chung với decoder đã có ở :ref:`system-sram-dung-chung-npu`, không lặp lại ở đây.

1.1 Điều kiện phía kernel
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Điều kiện
     - Nội dung
     - Nguồn
   * - Phiên bản driver
     - RKNPU driver từ 0.8.0
     - [T1 SRAM-zh 21] [T1 UG232 tr.106]
   * - Cấu hình kernel
     - ``CONFIG_ROCKCHIP_RKNPU_SRAM=y``
     - [T1 SRAM-zh 22] [T1 UG232 tr.106]
   * - DTS
     - Cấp SRAM từ system SRAM cho NPU, tối đa 956KB, kích thước và địa chỉ đầu căn 4K, vùng của các IP không chồng lấn. Gắn bằng ``rockchip,sram = <&rknpu_sram>;`` trong node NPU
     - [T1 SRAM-zh 36-39, 58-72] [T1 UG232 tr.106] [T1 UG232 tr.107]

Mã driver 0.9.8 cho thấy các điều kiện này được kiểm ở đâu:

- Tùy chọn Kconfig ``ROCKCHIP_RKNPU_SRAM`` ghi ``depends on NO_GKI`` [T1 DRV Kconfig:32-36].
- Bộ quản lý SRAM chỉ được tạo khi cả ``CONFIG_NO_GKI``, ``CONFIG_ROCKCHIP_RKNPU_SRAM`` và IOMMU đang bật. Nếu tìm không thấy tài nguyên SRAM thì driver chỉ cảnh báo ``could not find sram resource!`` [T1 DRV rknpu_drv.c:1478-1488].
- Driver đọc thuộc tính ``rockchip,sram`` bằng ``of_parse_phandle``. Không có thuộc tính thì ``sram_size = 0``. Đầu vùng được làm tròn lên và cuối vùng làm tròn xuống theo ``PAGE_SIZE`` [T1 DRV rknpu_drv.c:1155-1169].
- Vùng SRAM được chia thành các chunk kích thước ``PAGE_SIZE`` [T1 DRV rknpu_drv.c:1481]. Bitmap trong ví dụ của hãng ghi ``1bit = 4KB`` [T1 SRAM-zh 135] [T1 UG232 tr.108].

1.2 Điều kiện phía runtime
--------------------------

Bản ``librknnrt.so`` tối thiểu có hai giá trị:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Tài liệu
     - Ngưỡng ``librknnrt.so``
     - Nguồn
   * - SRAM-zh
     - ">=1.3.4b14"
     - [T1 SRAM-zh 76]
   * - UG232
     - ">=1.6.0"
     - [T1 UG232 tr.107]

Hai tài liệu không giải thích khác biệt này. Chưa thể chọn ngưỡng nào đúng. Xem mục 3.

1.3 Bật SRAM từ ứng dụng
------------------------

Có hai đường. Chúng không tương đương nhau.

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Đường
     - Cách bật
     - Phạm vi nguồn nói
   * - Biến môi trường, Internal
     - ``export RKNN_INTERNAL_MEM_TYPE=sram`` (tự tính kích thước, thử cấp đủ phần SRAM còn lại) hoặc ``sram#256`` (chỉ định 256KB) [T1 SRAM-zh 83-91]
     - Internal
   * - Biến môi trường, Weight
     - ``export RKNN_SEPARATE_WEIGHT_MEM=1`` kèm ``export RKNN_WEIGHT_MEM_TYPE=sram`` hoặc ``sram#128`` (128KB) [T1 SRAM-zh 93-103]
     - Weight
   * - Dùng cả hai
     - Đặt ``RKNN_INTERNAL_MEM_TYPE=sram#256`` cùng ``RKNN_SEPARATE_WEIGHT_MEM=1`` và ``RKNN_WEIGHT_MEM_TYPE=sram#128`` [T1 SRAM-zh 105-111]
     - Internal và Weight
   * - Cờ C API
     - Truyền ``RKNN_FLAG_ENABLE_SRAM`` vào tham số ``flags`` của ``rknn_init()``: ``ret = rknn_init(&ctx, rknn_model, size, RKNN_FLAG_ENABLE_SRAM, NULL);`` [T1 UG232 tr.107]
     - Internal Tensor

Về cờ C API, UG232 viết:

   "When RKNN_FLAG_ENABLE_SRAM is set, as much memory as possible will be allocated from the system's available SRAM as the model's Internal Tensor memory." [T1 UG232 tr.107]

Cờ không có tham số kích thước, nên khác dạng ``sram#N`` của biến môi trường (suy ra từ hai đoạn nguồn trên).

Phân loại bộ nhớ: bộ nhớ chạy của mô hình gồm weight và internal tensor, register configuration, input tensor và output tensor [T1 UG232 tr.148]. Phần internal memory không gồm input và output [T1 UG232 tr.148]. Suy ra: Internal là các tensor trung gian giữa các lớp.

1.4 Kiểm tra SRAM đã được cấp
-----------------------------

Bốn cách, theo thứ tự từ driver lên ứng dụng:

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - Cách
     - Cho biết gì
     - Nguồn
   * - ``dmesg | grep rknpu -i``
     - Dòng ``sram region: [0x00000000ff001000, 0x00000000ff0f0000), sram size: 0xef000`` khi driver nhận vùng SRAM
     - [T1 UG232 tr.108] [T1 SRAM-zh 118-125]
   * - ``cat /sys/kernel/debug/rknpu/mm``
     - Bitmap, mỗi bit 4KB, ``*`` là đã dùng, ``.`` là còn trống, kèm dòng ``SRAM total size: ..., used: ..., free: ...`` (đơn vị Byte)
     - [T1 UG232 tr.108] [T1 SRAM-zh 127-160]
   * - ``rknn_query`` với ``RKNN_QUERY_MEM_SIZE``
     - ``total_sram_size`` (tổng SRAM hệ thống cấp cho RKNPU) và ``free_sram_size`` (phần RKNPU còn dùng được), cùng đơn vị Byte. Giá trị SRAM trả về 0 nếu SRAM không bật hoặc không có chức năng này
     - [T1 UG232 tr.109] [T1 UG232 tr.148]
   * - ``export RKNN_LOG_LEVEL=3``
     - In bảng SRAM từng lớp và tổng dự đoán (xem mục 2)
     - [T1 UG232 tr.109] [T1 UG232 tr.110]

Hai ghi chú từ mã driver:

- Node debugfs ``mm`` chỉ được đăng ký khi ``CONFIG_ROCKCHIP_RKNPU_SRAM`` bật [T1 DRV rknpu_debugger.c:313-315]. Không bật cấu hình thì không có node này.
- Ví dụ ``SRAM total size: 978944`` trong tài liệu bằng ``0xef000`` (suy ra), khớp vùng 956KB.

Log chạy với ``RKNN_LOG_LEVEL=3`` ra terminal trên Linux và ra logcat trên Android [T1 UG232 tr.110].

1.5 Phía driver: cấp SRAM cho từng buffer
-----------------------------------------

Đường cấp trong kernel là cờ ``RKNPU_MEM_TRY_ALLOC_SRAM`` (``1 << 8``) khi tạo GEM object [T1 DRV include/rknpu_ioctl.h:74]. Tên cờ có chữ ``TRY``. Mã cấp phát cho thấy lý do:

- Điều kiện vào nhánh SRAM gồm config bật, cờ được đặt và ``sram_size > 0`` [T1 DRV rknpu_gem.c:720-721]. Nếu không đủ điều kiện, buffer đi nhánh còn lại và nằm ở DDR (suy ra từ cấu trúc ``if ... else if`` và đoạn ``remain_ddr_size > 0`` ở [T1 DRV rknpu_gem.c:791-795]).
- Lượng SRAM thực cấp bằng số nhỏ nhất trong ba giá trị: phần còn lại của buffer, kích thước người dùng yêu cầu (khi khác 0, đã làm tròn lên ``PAGE_SIZE``), và SRAM còn trống [T1 DRV rknpu_gem.c:725-737].
- Cấp phát thất bại thì driver ghi cảnh báo ``mm allocate ... failed`` rồi đặt lượng SRAM về 0 [T1 DRV rknpu_gem.c:738-747].
- Phần SRAM và phần DDR của một buffer được ánh xạ liên tiếp vào một dải IOVA, theo sơ đồ chú thích trong mã [T1 DRV rknpu_gem.c:524-546].
- Bộ cấp phát chunk tìm chunk trống đầu tiên rồi cố lấy các chunk liền nhau đủ kích thước [T1 DRV rknpu_mm.c:81] [T1 DRV rknpu_mm.c:98].

Suy ra: yêu cầu SRAM là cố gắng tốt nhất. Hết SRAM thì buffer rơi về DDR, không báo lỗi cho ứng dụng.

2. Khi nào đáng dùng
====================

2.1 Câu của hãng về lợi ích và cái giá
--------------------------------------

   "SRAM can help RKNPU applications reduce DDR bandwidth pressure, but it may have a certain impact on inference time." [T1 UG232 tr.106]

Nguồn chỉ nêu hướng giảm băng thông DDR. Nguồn không nói chiều của tác động lên thời gian suy luận, và không có con số tốc độ. Vì vậy trang này không khẳng định SRAM làm nhanh hơn hay chậm hơn. Đó là việc phải đánh giá cho từng mô hình.

2.2 Đọc ước lượng lợi ích trước khi đo
--------------------------------------

UG232 đưa một log mẫu với ``RKNN_LOG_LEVEL=3``. Các trường cần đọc:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Trường trong log
     - Ý nghĩa theo nguồn
   * - ``SramHit`` (từng lớp)
     - Kích thước SRAM mà tensor của lớp đó chiếm. Nguồn nói so với không bật SRAM, lượng đọc ghi DDR tương ứng với kích thước này được tiết kiệm [T1 UG232 tr.110]
   * - ``Predict SRAM Hit RW Amount``
     - Dự đoán đọc ghi SRAM của cả mô hình, cho biết lượng đọc ghi DDR tiết kiệm được mỗi frame so với không bật SRAM [T1 UG232 tr.110]
   * - ``Predict Internal Memory RW Amount``, ``Predict Weight Memory RW Amount``
     - Mẫu số để so. Tài liệu không định nghĩa riêng hai trường này (``unknown``, đã tìm ở: UG232 tr.109-110, UG152, API232, từ khóa: ``Predict Internal``, ``RW Amount``)
   * - ``Total allocated Internal SRAM Size``
     - Lượng SRAM đã cấp cho Internal, ở log mẫu là 524288 [T1 UG232 tr.109]

Bản SRAM-zh nói tương tự và gọi ``Predict SRAM Hit RW Amount`` là con số "可近似估计每帧节省的带宽" (dùng để ước chừng băng thông tiết kiệm mỗi frame) [T1 SRAM-zh 239]. Đây là số dự đoán của runtime, không phải số đo.

Ví dụ số trên log mẫu của UG232 (log không ghi đơn vị. Tính như Byte thì 524288 là 512KB, suy ra):

.. list-table::
   :header-rows: 1
   :widths: 46 24 30

   * - Đại lượng
     - Giá trị
     - Nguồn
   * - Total Internal Memory Size
     - 2157568
     - [T1 UG232 tr.110]
   * - Total allocated Internal SRAM Size
     - 524288 (512KB)
     - [T1 UG232 tr.109]
   * - Predict Internal Memory RW Amount
     - 11068320
     - [T1 UG232 tr.110]
   * - Predict SRAM Hit RW Amount
     - 6688768
     - [T1 UG232 tr.110]
   * - SRAM cấp / Internal (suy ra)
     - 524288 / 2157568 là khoảng 24%
     - suy ra
   * - Hit / Internal RW (suy ra)
     - 6688768 / 11068320 là khoảng 60%
     - suy ra

Đọc theo cách suy ra: ở mô hình mẫu, khoảng một phần tư dung lượng Internal nằm trong SRAM nhưng dự đoán chiếm khoảng 60% lượng đọc ghi của Internal. Đây là một mô hình của hãng, không nói gì về mô hình khác. Suy ra: tử số không gồm Weight, vì log mẫu chỉ cấp SRAM cho Internal [T1 UG232 tr.109].

2.3 Vì sao một số lớp có SramHit bằng 0
---------------------------------------

Log mẫu cho Internal SRAM dải ``[0xff3e0000, 0xff460000)`` [T1 UG232 tr.109]. Một vài dòng:

.. list-table::
   :header-rows: 1
   :widths: 10 22 30 18 20

   * - ID
     - Tensor
     - Dải ``[Start, End)``
     - Size
     - SramHit
   * - 2
     - output2
     - ``0xff404c00`` đến ``0xff466c00``
     - ``0x62000``
     - ``0x5b400``
   * - 3
     - output4
     - ``0xff466c00`` đến ``0xff52ac00``
     - ``0xc4000``
     - ``0x0``
   * - 8
     - output14
     - ``0xff3e0000`` đến ``0xff442000``
     - ``0x62000``
     - ``0x62000``

Nguồn: [T1 UG232 tr.109]. Cả ba dòng đối chiếu với dải SRAM ở trên (suy ra):

- Dòng 8 nằm trọn trong dải nên ``SramHit`` bằng ``Size``.
- Dòng 2 vượt cuối dải 0xff460000 một đoạn ``0xff466c00 - 0xff460000 = 0x6c00``, và ``0x62000 - 0x6c00 = 0x5b400`` đúng bằng ``SramHit``. Hit là phần tensor nằm trong dải SRAM.
- Dòng 3 bắt đầu sau cuối dải nên hit bằng 0.

Hệ quả suy ra: lợi ích phụ thuộc vào việc tensor trung gian lớn nhất có lọt vào lượng SRAM cấp được hay không. Mô hình có nhiều feature map lớn ở các lớp đầu sẽ nhận ít lợi ích ở các lớp đó, dù SRAM có 956KB. Bảng này chỉ là một mô hình mẫu, không đo thêm.

2.4 Trình tự quyết định
-----------------------

Đây là cách dùng các công cụ ở mục 1 (suy ra, không phải khuyến nghị của hãng):

1. Chạy mô hình không bật SRAM, ghi thời gian suy luận của chính mình.
2. Bật SRAM bằng một đường ở mục 1.3 và chạy với ``RKNN_LOG_LEVEL=3``. Đọc ``Predict SRAM Hit RW Amount`` chia cho tổng đọc ghi để biết lợi ích băng thông dự đoán.
3. Đo thời gian suy luận lại, vì nguồn nói thời gian có thể bị ảnh hưởng.
4. Chỉ giữ SRAM khi cả hai chiều đều có lợi cho mục tiêu đang theo đuổi.

Hai yếu tố khác làm kết quả khác đi:

- SRAM dùng chung với codec nên không thể giả định cấp đủ. Xem DTS mặc định ở :ref:`system-sram-dung-chung-npu`.
- Một context chiếm SRAM thì context khác không dùng lại vùng đó, phần chưa chiếm thì dùng được [T1 UG232 tr.108]. Khi chạy nhiều mô hình cùng lúc, mô hình nạp trước có thể lấy hết SRAM (suy ra).

3. Giới hạn
===========

3.1 Giới hạn đã có trong nguồn
------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 46 24

   * - Giới hạn
     - Nội dung
     - Nguồn
   * - ``RKNN_FLAG_SHARE_SRAM``
     - Có trong ``rknn_api.h`` nhưng chưa được implement
     - [T1 UG232 tr.108]
   * - Dùng lại giữa các context
     - Context khác không dùng lại vùng SRAM mà một context đã chiếm
     - [T1 UG232 tr.108]
   * - Cờ C API chỉ có Internal
     - Đoạn mô tả cờ chỉ nói Internal Tensor
     - [T1 UG232 tr.107]
   * - Kích thước cấp
     - Tối đa 956KB cho NPU và căn 4K
     - [T1 SRAM-zh 38] [T1 UG232 tr.106]
   * - Chồng lấn với IP khác
     - Vùng SRAM của các IP không được chồng lấn, nếu không dữ liệu có thể hỏng khi đọc ghi đồng thời
     - [T1 SRAM-zh 39] [T1 UG232 tr.106]
   * - Cần IOMMU và ``NO_GKI``
     - Bộ quản lý SRAM không được tạo nếu thiếu
     - [T1 DRV rknpu_drv.c:1478-1488]
   * - Thiếu SRAM thì rơi về DDR
     - Cấp phát lỗi chỉ ghi cảnh báo trong log kernel
     - [T1 DRV rknpu_gem.c:738-747]

3.2 Điều chưa biết
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Mục
     - Kết quả
   * - Ngưỡng ``librknnrt.so`` đúng
     - unknown. Hai nguồn mâu thuẫn (SRAM-zh 76 ghi ">=1.3.4b14", UG232 tr.107 ghi ">=1.6.0"). Đã tìm ở: SRAM-zh, UG232, UG152, API232, từ khóa: ``1.3.4b14``, ``1.6.0``, ``librknnrt``. Không có ghi chú giải thích
   * - Weight vào SRAM bằng cờ C API
     - unknown. Đã tìm ở: UG232, UG152, API232, từ khóa: ``RKNN_FLAG_ENABLE_SRAM``, ``Weight``, ``SRAM``. Chỉ có đường biến môi trường [T1 SRAM-zh 93-103]
   * - Biến môi trường và cờ C API dùng cùng lúc
     - unknown. Đã tìm ở: SRAM-zh, UG232 tr.106-110, từ khóa: ``RKNN_INTERNAL_MEM_TYPE``, ``RKNN_FLAG_ENABLE_SRAM``. Nguồn không nói thứ tự ưu tiên
   * - Runtime chọn tensor nào vào SRAM
     - unknown. Đã tìm ở: UG232, SRAM-zh, mã driver, từ khóa: ``SramHit``, ``allocate``. Kế hoạch đặt tensor nằm trong ``librknnrt.so``, không có trong driver. Driver chỉ cấp chunk khi được yêu cầu
   * - Địa chỉ trong bảng log
     - unknown. Dải ``[0xff3e0000, 0xff460000)`` ở log mẫu [T1 UG232 tr.109] khác dải ``[0xff001000, 0xff0f0000)`` ở dòng ``dmesg`` mẫu [T1 UG232 tr.108]. Nguồn không giải thích. Đã tìm ở: UG232 tr.106-110, SRAM-zh, từ khóa: ``0xff3e0000``, ``Addr``
   * - Độ trễ và băng thông SRAM so với DDR nhìn từ NPU
     - unknown. Đã tìm ở: các nguồn của trang :ref:`system-sram-dung-chung-npu` (xem mục 2.3 của trang đó). Không có con số
   * - Mức tăng hay giảm thời gian suy luận khi bật SRAM
     - unknown. Nguồn chỉ nói "may have a certain impact" [T1 UG232 tr.106], không nêu chiều và độ lớn

Gợi ý tìm tiếp: bài báo về hiệu quả của on-chip SRAM cho tensor trung gian trong suy luận CNN trên NPU edge, từ khóa ``on-chip SRAM activation tiling DRAM traffic NPU``.

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần).

.. list-table::
   :header-rows: 1
   :widths: 14 8 68 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``SRAM-zh``
     - T1
     - :doc:`SRAM usage (zh) </contents/06-tai-lieu-hang/04-sram-usage>`. Số sau nhãn là số dòng của tệp này
     - 17
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 43
   * - ``DRV``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (rknpu_drv.c, rknpu_gem.c, rknpu_mm.c, rknpu_debugger.c, Kconfig, include/rknpu_ioctl.h)
     - 15
