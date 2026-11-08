:tocdepth: 1

************
Tiền xử lý
************

.. admonition:: Trang này trả lời

   - Từ khung NV12 của ISP đến tensor đầu vào NPU có những tuyến nào?
   - Mỗi tuyến dùng phần cứng nào, kích thước dữ liệu bao nhiêu, ràng buộc gì?
   - Điều gì đã đo, điều gì chưa đo?

.. admonition:: Tóm tắt

   1. NPU nhận tensor NHWC 1, 3 hoặc 4 kênh [T1 UG232 tr.69]. Đầu vào hiện tại của model là uint8 RGB 640x640 theo ``ai/board/common.py:64-79`` [Mã nguồn repo]. Quyết định đổi sang 384x640 ở :doc:`../00-tong-quan/04-gioi-han-va-huong-phat-trien` mục 3.1 (quyết định 6).
   2. Có ba tuyến: A (CPU, chuỗi hiện có của repo), B (ISP thu nhỏ rồi RGA hoặc CPU thêm viền), C (RGA đổi màu và thu nhỏ một lệnh, theo demo của hãng). Repo chỉ có tuyến A.
   3. RGA đổi NV12 1920x1080 sang RGB888 640x640 có viền mất 2.222 và 2.244 ms (bộ đệm dma-buf, hai lần đo) hoặc 3.605 và 3.219 ms (địa chỉ ảo). CPU đổi NV12 1080p sang BGR mất 0.915 ms với 8 luồng, 4.571 ms với 1 luồng [T3 board, ``rga_bench.c``, ``board_pipeline_test.py``].
   4. ISP xuất trực tiếp NV12 640x360 hoặc 640x640 ở 29.95 fps [T3 board, ``v4l2-ctl --stream-mmap``]. Mặc định ``Dcrop`` là cả khung 4224x3136 (tỉ lệ 1.347), nên đầu ra 16:9 hoặc vuông bị méo [SL] [T3 board, ``/proc/rkisp0-vir1``]. ISP cắt được 16:9 bằng ``VIDIOC_S_SELECTION`` (``Dcrop(0,380|4224x2376)``), khi đó thu nhỏ giữ đúng tỉ lệ (mục 7).
   5. Tiền xử lý CPU của repo đo 0.216 ms mỗi khung ở một context, trên 82 ảnh kiểm thử nạp sẵn, không gồm NV12 sang BGR. Chưa suy ra được cho khung camera [T3 board, ``results/thr_p3.json``, :doc:`../03-phuong-phap/03-tang-npu-don-bay/09-pre-post-processing`].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Ba tuyến
===========

.. code:: text

    Tuyến A: chuỗi preprocess hiện có của repo (CPU)
      NV12 trong DDR
        -> CPU đổi NV12 sang BGR (chưa viết)
        -> resize INTER_LINEAR về cạnh dài 640
        -> thêm viền 114 cho đủ 640x640
        -> BGR sang RGB
        -> tensor uint8 (1, 640, 640, 3)

    Tuyến B: ISP thu nhỏ trước
      ISP selfpath ghi NV12 640x360 vào DDR
        -> RGA hoặc CPU: NV12 sang RGB888, thêm viền 114 lên 640x640
        -> tensor uint8 (1, 640, 640, 3)

    Tuyến C: demo của hãng (rknn_yolov5_demo)
      NV12 từ bộ giải mã MPP
        -> RGA imresize: NV12 sang RGB888 và thu nhỏ trong một lệnh
        -> rknn_inputs_set, fmt = NHWC

Tuyến A là ``preprocess`` có sẵn: resize ``cv2.INTER_LINEAR`` về cạnh dài 640, ``copyMakeBorder`` giá trị 114, BGR sang RGB [Mã nguồn repo ``ai/board/common.py:64-79``]. Tuyến C: demo ``main_video.cc`` đổi ``RK_FORMAT_YCbCr_420_SP`` sang ``RK_FORMAT_RGB_888`` bằng ``imresize`` rồi gọi ``rknn_inputs_set`` với ``fmt = RKNN_TENSOR_NHWC``, kéo thẳng về kích thước model, không letterbox [T1 rknn-toolkit2 ``rknpu2/examples/rknn_yolov5_demo/src/main_video.cc:286-312``, ``main_video.cc:393``]. Dự án chọn tuyến B (quyết định 4 và 6).

2. Hình học letterbox
=====================

.. code:: text

    ảnh vào 1920x1080, hệ số r = 640 / 1920 = 1/3, sau resize còn 640 x 360

         640 cột
      +-----------------------------+
      |  viền 114, 140 hàng         |
      +-----------------------------+
      |                             |
      |  ảnh 640 x 360              |   640 hàng tổng
      |                             |
      +-----------------------------+
      |  viền 114, 140 hàng         |
      +-----------------------------+
      (hình không đúng tỉ lệ)

Công thức của repo: ``r = 640 / max(h0, w0)``, kích thước sau resize ``(min(ceil(w0 r), 640), min(ceil(h0 r), 640))``, viền ``round(dh - 0.1)`` và ``round(dh + 0.1)`` với ``dh = (640 - h) / 2`` [Mã nguồn repo ``ai/board/common.py:64-79``]. Với 1920x1080: ``r = 1/3``, ảnh 640x360, viền 140 hàng trên và dưới [SL, phép tính]. Hình học này đúng cho nguồn 16:9. Nếu ISP thu nhỏ cả khung 4:3 xuống 16:9 thì ảnh đã bị nén theo chiều dọc trước bước này [SL], nên phải cắt 4224x2376 ở ISP trước (mục 7). Với đầu vào 384x640 của quyết định 6, ảnh 640x360 chỉ cần 12 hàng viền mỗi bên. Cắt bằng RGA chưa thử.

3. Kích thước dữ liệu
=====================

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Dữ liệu
     - Byte mỗi khung
     - Ở 30 khung/giây
   * - NV12 4224x3136
     - 19869696
     - 596 MB/s
   * - NV12 1920x1080
     - 3110400
     - 93.3 MB/s
   * - NV12 640x360
     - 345600
     - 10.4 MB/s
   * - RGB888 640x640x3
     - 1228800
     - 36.9 MB/s
   * - RGB888 640x384x3
     - 737280
     - 22.1 MB/s

Các số là phép tính từ kích thước (NV12 là 1.5 byte mỗi pixel, RGB888 là 3 byte) [SL]. Riêng 345600 byte của NV12 640x360 khớp ``Size Image`` do driver báo [T3 board, ``v4l2-ctl --try-fmt-video``].

4. RGA
======

- Board: ``rga3`` tại ``fdb60000``, ``fdb70000``, ``rga2`` tại ``fdb80000`` [T3 board, ``dmesg``].
- RGA3: nguồn tối đa 8176x8176, đích tối đa 8128x8128, co giãn 1/8 đến 8 (phóng to bi-cubic, thu nhỏ lấy trung bình) [T1 RGA guide, Design Index]. Bộ nhớ raster trong DDR [T1 TRM2 tr.703].
- Căn lề: bề rộng stride căn 16. Định dạng ``YCbCr_420_SP``: offset, rộng, cao, cao stride căn 2 [T1 RGA guide, Image Format Supported].
- Loại bộ đệm: thứ tự hiệu năng là địa chỉ vật lý, fd, địa chỉ ảo, khuyến nghị fd [T1 RGA guide].
- Model zoo dùng RGA khi bề rộng nguồn và đích chia hết 16, ngược lại rơi về CPU [T1 rknn_model_zoo ``utils/image_utils.c:684``].

``RGA guide`` là ``docs/Rockchip_Developer_Guide_RGA_EN.md`` trong kho ``airockchip/librga`` (commit 2b32edcb97b6, đọc ngày 2026-11-07). Tệp này chưa nằm trong ``docs/_assets/pdf``. Với các kích thước ở trang này: 1920, 640 chia hết 16 và 1080, 360 chia hết 2 [SL].

5. Số đo trên board
===================

Điều kiện: board chưa khóa xung, governor ``ondemand``, ghim ``taskset -c 6`` cho RGA, 300 lần đo sau 30 lần khởi động, nội dung ảnh giả [T3 board, ``rga_bench.c``]. ``va`` là bộ đệm cấp bằng ``posix_memalign`` (địa chỉ ảo), ``fd`` là bộ đệm dma-buf từ ``/dev/dma_heap/system``. RGA tự chọn lõi. ``librga`` là RGA_api v1.9.3, báo ``RGA_2_Enhance RGA_3``.

.. list-table::
   :header-rows: 1
   :widths: 46 18 18 18

   * - Việc (RGA)
     - va, trung vị (p95) ms
     - fd, trung vị (p95) ms
     - Ghi chú
   * - NV12 1920x1080 sang RGB888 640x360 (``imresize``)
     - 2.917 (2.938)
     - 1.864 (1.891)
     - như demo hãng
   * - NV12 1920x1080 sang RGB888 1920x1080 (``imcvtcolor``)
     - 4.490 (4.562), lần 2: 4.268 (4.369)
     - 1.056 (1.869), lần 2: 1.867 (1.904)
     - không ổn định giữa hai lần đo
   * - NV12 640x360 sang RGB888 640x360 (``imcvtcolor``)
     - 0.561 (0.572)
     - 0.136 (0.263)
     -
   * - NV12 640x360 sang RGB888 640x640, thêm viền (``imfill`` rồi ``improcess``)
     - 1.414 (1.430)
     - 0.626 (0.664)
     - hai lệnh RGA
   * - NV12 1920x1080 sang RGB888 640x640, thêm viền
     - 3.605 (3.662)
     - 2.222 (2.256)
     - hai lệnh RGA
   * - NV12 4224x3136 sang RGB888 640x640 (``imresize``, ảnh méo)
     - 14.602 (14.802)
     - 9.264 (9.286)
     -

Mỗi ca chạy hai lần (mỗi lần 300 vòng). Các ca lệch nhau dưới 2% ở bộ đệm ``fd``, riêng ``va`` lệch đến 11%. Ca ``imcvtcolor`` 1080p bằng ``fd`` ra hai chế độ (1.056 và 1.867 ms), có thể do RGA tự chọn lõi RGA3 hoặc RGA2 khác nhau [SL], chưa kiểm. Số không khóa xung dao động theo xung DDR, đo lại khi khóa xung ở mục 6. Màu viền của ``imfill`` là 0x727272, chưa kiểm đúng 114 trên ảnh ra. CPU, trên khung NV12 thật chụp từ camera, ``cv2`` 4.11.0 [T3 board, ``board_pipeline_test.py``]:

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Việc (CPU)
     - 4224x3136
     - 1920x1080
     - 640x360
   * - ``cvtColor`` NV12 sang BGR, 8 luồng, trung vị ms
     - 10.896
     - 0.915
     - 0.105
   * - ``cvtColor`` NV12 sang BGR, 1 luồng, trung vị ms
     - 48.995
     - 4.571
     - 0.448
   * - ``preprocess`` của ``ai/board/common.py``, trung vị ms
     - 2.356
     - 1.124
     - 0.127

Đọc số: với ảnh 1080p, CPU làm NV12 sang BGR rồi ``preprocess`` hết khoảng 2.0 ms khi chạy riêng. Trong pipeline không khóa xung và không ghim hai việc này tốn 1.842 và 5.154 ms, khóa xung và ghim lõi 4 đến 7 thì 1.181 và 1.199 ms (:doc:`01-buc-tranh-tong-the` mục 5). RGA dma-buf làm cả đổi màu, resize và viền trong khoảng 2.2 ms và không dùng CPU. Với ảnh 640x360 từ ISP, CPU mất khoảng 0.23 ms còn RGA dma-buf 0.626 ms [SL, phép cộng]. RGA chưa đo khi NPU và CPU cùng chạy.

6. Đo lại khi khóa xung
=======================

Khóa CPU, NPU và DDR ở ``performance`` bằng ``lock_freq.sh`` (CPU 1800, 2256, 2304 MHz, NPU 1000 MHz, DDR 2112 MHz), chạy ``rga_bench`` ba lần, rồi một lần nữa trong lúc vòng suy luận NPU liên tục chạy ở ``CORE_0``. Điều kiện khác như mục 5 [T3 board, ``rga_bench.c``, ``npu_loop.py``]. Trung vị ms, ba lần đo khóa xung (riêng ``fd``, p95 chỉ hơn trung vị tối đa 0.2%, trừ ca 4224x3136 lần 3):

.. list-table::
   :header-rows: 1
   :widths: 36 16 16 16 16

   * - Việc (RGA)
     - fd, khóa xung (3 lần)
     - fd, NPU chạy cùng
     - va, khóa xung (3 lần)
     - va, NPU chạy cùng
   * - NV12 1920x1080 sang RGB888 640x360 (``imresize``)
     - 1.720, 1.720, 1.720
     - 1.720
     - 2.612 đến 2.618
     - 2.295
   * - NV12 1920x1080 sang RGB888 1920x1080 (``imcvtcolor``)
     - 1.004, 1.004, 1.004
     - 1.037
     - 2.465 đến 3.119
     - 2.963
   * - NV12 640x360 sang RGB888 640x360 (``imcvtcolor``)
     - 0.210, 0.210, 0.209
     - 0.213
     - 0.433 đến 0.445
     - 0.391
   * - NV12 640x360 sang RGB888 640x640, thêm viền
     - 0.569, 0.569, 0.569
     - 0.580
     - 1.073 đến 1.084
     - 0.991
   * - NV12 1920x1080 sang RGB888 640x640, thêm viền
     - 2.015, 2.016, 2.015
     - 2.017
     - 2.831 đến 3.098
     - 3.045
   * - NV12 4224x3136 sang RGB888 640x640 (ảnh méo)
     - 9.037, 9.037, 8.960
     - 8.963
     - 12.916 đến 13.152
     - 13.208

Đọc số: khi khóa xung, bộ đệm dma-buf cho kết quả ổn định (ba lần giống nhau đến 3 chữ số). Hai chế độ ở mục 5 nhiều khả năng do xung DDR dao động dưới ``ondemand`` (528 MHz lúc nghỉ, 2112 MHz khi khóa) [SL], chưa tách riêng. Bộ đệm địa chỉ ảo dao động rộng hơn (đến 27% ở ca 1080p ``imcvtcolor``). RGA dma-buf chậm hơn tối đa 3.3% khi NPU chạy cùng (1.004 lên 1.037 ms), các ca khác dưới 2%. Vòng NPU đo cùng lúc: trung vị 17.043 ms (p95 21.040 ms) trên cửa sổ 90 s, còn NPU chạy riêng 12 s là 19.997 ms (p95 20.812 ms), cả hai không ghim CPU [T3 board, ``npu_loop.py``]. Hai mức 17 và 20 ms trộn lẫn khi không ghim nên không tách được ảnh hưởng của RGA lên NPU.

7. Cắt 16:9 ở ISP
=================

Đặt vùng cắt ``top=380, left=0, width=4224, height=2376`` trên ``rkisp_selfpath`` rồi phát 1920x1080: ``/proc/rkisp0-vir1`` ghi ``Dcrop(0,380|4224x2376)``, 29.95 fps, ``frameloss:0``. Vùng cắt giữ nguyên giữa các lần mở nút, đã đặt lại và đọc lại xác nhận ``Left 0, Top 0, Width 4224, Height 3136`` [T3 board, ``v4l2-ctl --set-selection``, ``--get-selection``]. Chi tiết ở :doc:`03-isp-va-vong-3a`.

8. Ảnh méo tỉ lệ và độ chính xác (ảnh tĩnh)
===========================================

Đo ngày 2026-11-08 trên PC bằng evaluator protocol v1, model baseline FP32 (``best.pt``), không phải INT8 trên board. Nhãn YOLO chuẩn hóa không đổi khi co giãn theo trục nên giữ nguyên. Bản letterbox tái lập đúng số đã lưu của từng tập [T3 PC, ``tmp/camera-pipeline/distort/results.json``].

CSS v28 đã được hãng xử lý ``Resize to 640x640 (Stretch)`` cho mọi ảnh [T1, ``data/css/raw/README.roboflow.txt``], gồm cả tập train và ``css_test``. Vì vậy ``css_test`` không phải mốc tỉ lệ tự nhiên. Phép thử dùng được chỉ gồm ảnh tự nhiên không vuông của ppe2286, so letterbox với ép về 640x640 (như ISP xuất 640x640, nhưng từ tỉ lệ gốc của từng ảnh, không phải 4:3), bootstrap ghép cặp theo ảnh 1000 lần [T3 PC, ``tmp/camera-pipeline/stretch/results.json``]:

.. list-table::
   :header-rows: 1
   :widths: 30 16 16 38

   * - Tập (chỉ ảnh không vuông)
     - Letterbox, mAP50-95
     - Ép vuông, mAP50-95
     - Ép vuông trừ letterbox, khoảng tin cậy 95%
   * - ``ppe2286_ext``, 113 ảnh
     - 0.2842
     - 0.2694
     - -0.0158, từ -0.0361 đến +0.0028
   * - ``ppe2286_heldout``, 316 ảnh
     - 0.1084
     - 0.1105
     - +0.0024, từ -0.0123 đến +0.0173

Cả hai khoảng đều chứa 0, nên chưa phân biệt được hai cách đưa ảnh vào, và cũng chưa đủ để nói méo tỉ lệ vô hại. Khoảng tin cậy còn rộng tới 0.036. Pipeline giữ nguyên cắt 16:9 cộng letterbox vì đó là đầu vào của protocol.

Giới hạn: không phải khung camera, FP32 chứ không phải INT8, một seed, model có mAP thấp trên ppe2286 và nhãn ``Person`` của ``ppe2286_ext`` là nhãn giả. Lần thử kéo giãn toàn bộ ảnh (gồm cả ảnh đã vuông) cho kết quả trái chiều giữa các tập, không dùng làm kết luận vì ảnh đã ép vuông bị méo thêm một lần nữa.

9. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Điều chưa biết
     - Cần để xác minh
   * - Thời gian RGA khi CPU cũng bận (``cv2``, hậu xử lý) cùng lúc
     - Chạy ``rga_bench`` cùng ``board_pipeline_test2.py``
   * - Màu viền RGA bằng 114 trên ảnh ra
     - Đọc lại bộ đệm RGB888 sau ``imfill``
   * - Ảnh méo tỉ lệ từ ISP làm giảm độ chính xác bao nhiêu trên khung camera thật
     - Bộ khung OV13855 có nhãn, so cắt 16:9 với không cắt. Đã thử trên ảnh tĩnh, xem mục 8
   * - Cắt bằng RGA (``imcrop``) có dùng được không
     - Thử ``imcrop`` trên board
