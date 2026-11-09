:tocdepth: 1

****************************
Giới hạn và hướng phát triển
****************************

.. admonition:: Trang này trả lời

   - Đề tài không làm được gì với NPU RK3588S, và làm được gì?
   - Đã đo được gì, đã chốt quyết định nào, luồng xử lý ra sao?
   - Còn những hướng phát triển nào?

.. admonition:: Tóm tắt

   - Giới hạn tùy biến: toolkit và ``librknnrt`` là file biên dịch, không viết được phép tính cho NPU. Thanh ghi có trong TRM, driver có mã nguồn mở.
   - Giới hạn tối ưu: ba lõi, tới 6 TOPS tổng, bộ đệm 384 KB mỗi lõi, System SRAM tối đa 956 KB. Lượng tử hóa bằng toolkit chỉ có kiểu ``w8a8``.
   - Mốc 30 FPS đã đạt vì camera chỉ có 30 khung/giây. Điểm yếu là độ chính xác trên camera.
   - Số đo là một board, phần lớn một seed.
   - Mục 3 ghi 17 quyết định đã chốt, sơ đồ luồng theo quyết định và hướng phát triển.

.. contents:: Trang này gồm
   :local:
   :depth: 2

1. Giới hạn
===========

1.1. Giới hạn tùy biến
----------------------

Đề tài chạy trên stack của hãng. Mỗi tầng cho chỉnh ở mức khác nhau:

.. code:: text

   PyTorch, ONNX        sửa được toàn bộ
        |
   toolkit (compiler)   file biên dịch, chỉ chỉnh qua tham số
        |
   file .rknn
        |
   librknnrt (runtime)  file biên dịch, chỉ gọi qua API
        |
   driver rknpu         có mã nguồn GPL-2.0, dự án chưa sửa
        |
   NPU                  chỉ cấu hình qua thanh ghi

**Không làm được trong stack này**

- Tự viết phép tính cho NPU. TRM không mô tả tập lệnh, NPU chạy theo danh sách thanh ghi nạp từ bộ nhớ [T1 TRM1 tr.1994].
- Sửa bước biên dịch. Toolkit và ``librknnrt`` phát hành dạng file ``.so``.
- Thêm op mới chạy trên NPU. Custom op chỉ có backend CPU và GPU [T1 UG232 tr.94]. Matmul API chạy trên NPU nhưng chỉ nhân ma trận [T1 UG232 tr.41] (:doc:`../02-nen-tang-rk3588/03-toolchain-runtime/04-operator-list` mục 5).
- Biết chắc bên trong NPU từ tài liệu hãng. Hãng không công bố dataflow và chức năng firmware của MCU, TRM và Mesa lệch nhau về số bank của bộ đệm (:doc:`../09-tien-do/03-khoang-trong/01-npu`). Mã gửi job của driver do CPU chính chạy và không nhắc tới MCU [T1 DRV rknpu_job.c:272-375].

**Làm được**

Sửa model [T1 UG232 tr.141], chỉnh ``rknn.config`` (API232 tr.7 đến tr.11), chọn lõi [T1 UG232 tr.73], zero-copy [T1 UG232 tr.64], cờ SRAM [T1 UG232 tr.107], dùng ISP, RGA, VPU, GPU, và tổ chức lại phần CPU quanh NPU. Sửa driver và DTS cũng làm được vì mã nguồn mở, bật SRAM cần bước này [T1 UG232 tr.106], dự án chưa làm.

**Ngoài stack của hãng**

Linux có driver mở ``accel/rocket`` cho NPU RK3588. Chưa dùng được ngay: nó nhận model TensorFlow Lite thay vì ``.rknn``, ``rkt_ml.c`` của Mesa chỉ xử lý Convolution, Add, Pooling, và driver có từ kernel 6.18 trong khi board chạy 6.1.99 (:doc:`../02-nen-tang-rk3588/01-phan-cung-npu/05-ban-do-thanh-ghi-va-co-che-cau-hinh` mục 6).

1.2. Giới hạn tối ưu
--------------------

- **Kiểu số.** Phần cứng có "integer 4, integer 8, integer 16, float 16, Bfloat 16 and tf32" [T1 TRM1 tr.1984], nhưng khi lượng tử hóa model, RK3588 chỉ dùng được ``w8a8``. ``w4a8`` ghi "(Not supported yet)", ``w16a16i`` ghi "(Only RV1103/RV1106 supported)" [T1 API232 tr.7]. Nên đề tài dùng INT8, FP16, hoặc trộn hai kiểu trong một đồ thị.
- **Sức tính.** Ba lõi, 1024 MAC int8 mỗi lõi mỗi chu kỳ [T1 TRM1 tr.1984], tối đa 1000 MHz [T1 DRV ``dts/rk3588s.dtsi:3482-3640``]. Hãng ghi tổng "computing power is up to 6TOPs" [T1 DS V1.7 tr.7], không ghi số mỗi lõi. Nên đọc giới hạn từ số đo, không tính từ TOPS.
- **Bộ nhớ trong SoC.** Bộ đệm 384 KB mỗi lõi [T1 TRM1 tr.1984], System SRAM tối đa 956 KB cho các IP, có thể đã cấp cho IP khác như codec [T1 UG232 tr.106]. Model INT8 mặc định có tổng 6.256 MiB tensor trong [T3 board], lớn hơn SRAM. Lượng cần giữ cùng lúc chưa biết.
- **Băng thông DDR.** Hãng không ghi theo GB/s. 34.1 GB/s là trần tính từ bộ điều khiển với LPDDR4/4X bốn kênh (:doc:`../02-nen-tang-rk3588/04-bo-nho-hieu-nang/01-ddr-tren-rk3588`). Băng thông thực chưa đo.
- **Đa nhân.** Ba lõi không nhanh gấp ba. Một khung chia cho ba lõi (một context) chỉ hơn một lõi 2.6% về FPS (56.1 so với 54.66). Mỗi lõi một khung (ba context) đạt 141.18 FPS [T3 board].
- **API.** Zero-copy chỉ có ở C API, RKNNLite 2.3.2 không có ``rknn_set_io_mem`` [T3 board, :doc:`../03-phuong-phap/03-tang-npu-don-bay/06-memory-copy`]. Python ba luồng 141.2 FPS và ba tiến trình 143.5 FPS gần như bằng nhau [T3 board].
- **Quy tắc kích thước của hãng.** Là khuyến nghị: "These rules are not mandatory." [T1 UG232 tr.144]. Model SiLU gốc có 55 trên 64 lớp Conv đã căn lề channel (:doc:`../03-phuong-phap/03-tang-npu-don-bay/07-compiler-optimization` mục 2.5).

2. Đã đo và chưa đo
===================

Cảm biến chỉ có một chế độ 30 khung/giây, nên mỗi khung có 33.3 ms [T3 board, :doc:`../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`]. Chạy liên tục với camera, model SiLU INT8 mặc định, một lõi NPU, khóa xung, phòng trống: 29.95 FPS, đầu cuối 18.97 ms, trong đó NPU 17.97 ms. Có người và bật tracking thì đầu cuối 19.84 ms. FPS đã đạt, phần dư khoảng 13 đến 14 ms. Điểm yếu là độ chính xác: bản INT8 mặc định chỉ đạt AP50-95 36.75 trên ``css_test``, bản gần cùng tốc độ đạt 49.66 nhưng chưa chạy trên camera. Độ chính xác trên ảnh camera chưa đo.

Mọi op hoặc thay đổi kiến trúc ứng viên phải qua bốn cổng G1 đến G4 (:doc:`../03-phuong-phap/03-tang-npu-don-bay/01-operator-support`). G4 có ba điều kiện: A, lớp chia từ hai lõi chiếm ít nhất 50% cycles ước tính. B, ba lõi giảm latency ít nhất 5% so với một lõi. C, AP50-95, AP NoHelmet, AP Vest mỗi cột giảm tối đa 1.0 điểm so với SiLU cùng kiểu số và seed. Nhãn "Loại" chỉ nghĩa là không qua cổng, không phải cấm dùng.

2.1. Đã đo, có lợi
-------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Việc
     - Kết quả
   * - Giữ FP16 đoạn tính tọa độ hộp (``h5``)
     - AP50-95 36.75 lên 49.66 (FP16: 49.76). Latency đổi dưới 5% (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`)
   * - Đưa giải mã box ra CPU
     - AP50-95 49.84. NPU 13.07 ms, giải mã numpy 8.02 ms. CPU chạy song song với NPU: 65.99 FPS trên ảnh nạp sẵn (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`)
   * - Mỗi lõi NPU một khung
     - Một lõi 54.69, hai lõi 101.90, ba lõi 141.13 FPS trên ảnh nạp sẵn (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`). Một camera 30 FPS chưa cần
   * - Input 384x640 thay 640x640 (ISP 640x360, thêm 12 hàng padding mỗi bên)
     - Khóa xung, trung vị ba lần chạy: ``CORE_0`` 17.085 xuống 12.060 ms (giảm 29.4%), ``CORE_0_1_2`` 16.654 xuống 11.934 ms (giảm 28.3%). Ba lõi nhanh hơn một lõi 2.52% ở 640x640 và 1.04% ở 384x640 [T3 board]. AP FP32 (không huấn luyện lại) trên 262 dải 640x360 cắt từ ``test`` và ``test_ext`` (1051 hộp): 640x640 0.3271, 384x640 0.3313 (+0.0042, chưa có khoảng tin cậy). AP INT8 trên NPU cùng 262 dải: chênh +0.0057 AP50-95 và -0.0089 AP50 giữa hai cỡ cùng cách hiệu chuẩn, bằng cỡ chênh do cách hiệu chuẩn (0.0055), nên coi là bằng nhau. Bắt vật thể sát mép trên và dưới: 0.786 ở 640x640, 0.788 ở 384x640. Một seed, một board, dải cắt từ ảnh vuông và 4:3, không phải khung camera [T3, ``experiments/npu/throughput/input_384x640/band_eval.py``, ``band_int8_eval.py``, ``band_edge.py``]
   * - ISP cắt 16:9, thu nhỏ
     - NV12 640x360 ở 29.95 fps (:doc:`../10-luong-camera-den-phat-hien/03-isp-va-vong-3a`). Ảnh ISP thu nhỏ khác bộ đánh giá, ảnh hưởng AP trên camera chưa đo (:doc:`../10-luong-camera-den-phat-hien/04-tien-xu-ly` mục 8)
   * - Khóa xung CPU, NPU, DDR
     - Trên camera, ghim lõi 4 đến 7: đầu cuối 18.97 ms so với 26.10 ms, CPU tiến trình 16.1% so với 41.0%. Nhiệt NPU cao nhất 58.2 °C (:doc:`../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`)
   * - Ghim CPU và ngắt NPU
     - Không ghim: mức chậm ở 43% và 46% số lần chạy. Ghim: ổn định quanh 16.3 ms ở bảy vị trí trên lõi lớn. Ngắt ở CPU0 hoặc ứng dụng ở CPU0 đến CPU3 không đạt (:doc:`../03-phuong-phap/02-tang-npu-nen-do/05-thu-ghim-cpu-va-ngat`)
   * - Tracking ByteTrack
     - Trên camera: 0.190 ms khi 0 hộp, 0.727 ms trung vị khi có người đứng trong khung tối. Hộp giả 34 người: 5.6 ms với ``OPENBLAS_NUM_THREADS=1``, riêng ``update`` 447 ms nếu để số luồng mặc định (:doc:`../10-luong-camera-den-phat-hien/06-sau-npu`)
   * - RGA
     - Đo từng lệnh, chưa nối vào chương trình. RGA3 đổi màu, thu phóng, đặt ảnh, không tô màu được. Tô nền và vẽ khung chỉ chạy trên RGA2 (:doc:`../10-luong-camera-den-phat-hien/08-phan-cung-tang-toc` mục 3.2)
   * - VPU mã hóa video
     - Đo riêng, chưa so được với ``libx264`` vì khác nguồn ảnh và cấu hình. ``camera.py`` đang dùng ``libx264`` (:doc:`../10-luong-camera-den-phat-hien/06-sau-npu`)

2.2. Đã đo, loại
----------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Việc
     - Kết quả
   * - Đổi SiLU sang ReLU, LeakyReLU, ReLU6
     - Latency nhanh hơn 20.9% đến 22.3% ở một lõi, nhưng AP50-95 kém 3.51, 2.64, 3.63 điểm (ngưỡng 1.0). ReLU 200 epoch kém SiLU 200 epoch 1.78 điểm (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/02-ket-qua-bien-the-activation`)
   * - Bỏ DFL
     - INT8 mặc định vẫn mất 12.58 điểm, có tách đầu thì 49.96. Không hơn tách đầu ngoài nhiễu
   * - QAT
     - 49.85, hơn cách đưa giải mã ra CPU 0.01 điểm, nằm trong nhiễu
   * - Đổi thuật toán lượng tử hóa
     - ``kl_divergence``, ``auto_hybrid`` không lấy lại điểm. ``mmse`` không dựng được với 300 ảnh hiệu chuẩn
   * - Thêm worker tiền xử lý và hậu xử lý cho ba lõi
     - +4.4%
   * - Một khung chia cho ba lõi
     - Giảm latency 2.9% với SiLU, dưới ngưỡng 5%. 57 trên 57 lớp ``ConvExSwish`` cùng ``Resize``, ``Split``, ``MaxPool`` chỉ chạy lõi 0, lớp chia từ hai lõi chỉ chiếm 1.8% cycles ước tính [T3 board]. Dự án vẫn chọn làm kiểu chạy NPU (mục 3.1, quyết định 7)

2.3. Chưa đo
------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Việc
     - Cần làm
   * - Độ chính xác trên ảnh camera, độ trễ đầu cuối, nhiệt, CPU còn dư khi dùng RGA và VPU
     - Chạy trên camera với model đã chọn, nhiều người, phòng đủ sáng
   * - Zero-copy qua C API
     - Viết chương trình C, đo thời gian copy và FPS. RK3588: đầu vào 4 chiều 1, 3, 4 channel cần width căn 16 byte
   * - System SRAM
     - Kernel board chưa bật. Cần đổi kernel config và DTS (UG232 tr.106), rồi đo FPS và lưu lượng DDR
   * - Hạ xung DDR (1560, 1068 MHz)
     - Cho biết DDR có phải nút thắt không, và zero-copy với SRAM có đáng làm không
   * - Giải mã box bằng C hoặc NEON
     - Đo so với 8.02 ms của numpy
   * - YOLOv8s
     - Huấn luyện, build, đo trong ngân sách 33.3 ms
   * - Huấn luyện lâu hơn
     - SiLU 200 epoch hơn 100 epoch 1.21 điểm, nhỏ hơn khoảng trải giữa seed 1.35. Cần thêm seed
   * - Cắt vùng quan tâm, tái tham số hóa (RepVGG, QARepVGG, DBB)
     - Đo trên camera. Tái tham số hóa có rủi ro khi INT8 (:doc:`../01-kien-thuc-nen/06-thiet-ke-model/01-tai-tham-so-hoa-cau-truc`)
   * - ``single_core_mode``, ``optimization_level`` thấp hơn, ``compress_weight``, ``model_pruning``
     - Build, đo latency và AP
   * - GPU Mali, VOP2
     - Chỉ cần khi có màn hình hoặc giao diện ứng dụng. GPU hiện tải 0
   * - Op ngoài NPU: ``op_target``, GPU dự phòng, custom op
     - Chưa cần. Model hiện chỉ có ``Transpose`` của DFL trên CPU, và cách đưa giải mã ra CPU không còn op này

3. Quyết định và hướng phát triển
=================================

3.1. Quyết định
---------------

Quyết định đã chốt (người dùng), chia theo nhóm. Mọi trang khác khi nói về phạm vi, mục tiêu hay hướng triển khai thì trỏ về đây.

3.1.1. Phạm vi và mục tiêu
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Phạm vi 5 lớp: Helmet, NoHelmet, NoVest, Vest, Person.
2. Mục tiêu 30 FPS, vì camera chỉ có 30 khung/giây.
3. Tận dụng đầy đủ các phần cứng tăng tốc trong pipeline phát triển.

3.1.2. Camera và ISP
~~~~~~~~~~~~~~~~~~~~

4. ISP cắt 16:9 rồi tách hai luồng: luồng 1 (video chính) 4K UHD, luồng 2 (đưa vào AI) 640x360. Kết quả AI vẽ lên luồng video chính (sơ đồ ở mục 3.2).
5. Xoay ảnh theo hướng camera: quay camera vật lý hoặc dùng RGA.

3.1.3. Model AI và NPU
~~~~~~~~~~~~~~~~~~~~~~

6. Huấn luyện giữ ở 640x640. Export input model là [1, 384, 640, 3] (NHWC, cao 384, rộng 640): ảnh ISP 640x360 thêm padding 12 hàng trên và 12 hàng dưới. Hiệu chuẩn INT8 bằng 300 ảnh train (ít nhất 20 ảnh mỗi lớp), letterbox về 384x640.
7. NPU chạy theo kiểu intra-frame (một khung chia cho ba lõi).
8. NPU nhận ảnh zero-copy qua C API (RKNN), không dùng RKNNLite.

3.1.4. CPU và phần mềm
~~~~~~~~~~~~~~~~~~~~~~

9. CPU làm: hậu xử lý (giải mã hộp, NMS), ByteTrack, dựng chữ nhãn, điều phối và logic ứng dụng. Hậu xử lý, ByteTrack và dựng chữ nhãn dùng NEON.
10. Chương trình chính viết bằng C hoặc C++.
11. Ghim vòng chính và ngắt NPU vào lõi lớn A76.

3.1.5. Phần cứng và luồng dữ liệu
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

12. Phần cứng làm: ISP (cắt, thu nhỏ), RGA3 (thêm viền), NPU (suy luận), RGA2 (vẽ khung, chèn nhãn), VPU (lưu video), bộ JPEG (lưu ảnh vi phạm), VOP2 (hiển thị, khi có màn hình), GPU (giao diện ứng dụng, khi có màn hình). IEP không dùng. ``fbcpath`` (FBC) không dùng: không thu nhỏ về 3840x2160 (chỉ cắt được 4224x2376), RGA2 không vẽ được trên khung FBC, và VPU chưa nhận được khung FBC khi thử (:doc:`../10-luong-camera-den-phat-hien/03-isp-va-vong-3a`).
13. Khung đi giữa các khối bằng dma-buf (fd), không sao chép qua CPU.

3.1.6. Vẽ, lưu và vi phạm
~~~~~~~~~~~~~~~~~~~~~~~~~

14. Giữ khung 4K lại một đến hai khung, chờ kết quả AI để vẽ khớp.
15. Vi phạm: có NoHelmet hoặc NoVest gắn với một Person, kéo dài 3 giây liên tục thì lưu ảnh vi phạm.
16. Lưu ảnh vi phạm từ luồng 4K qua bộ JPEG, lưu video bằng H.265 qua bộ VPU: cùng chất lượng ở khoảng nửa bitrate của H.264, đủ 30 khung/giây ở 4K (:doc:`../10-luong-camera-den-phat-hien/06-sau-npu` mục 3.1). Trình duyệt chỉ hỗ trợ H.265 một phần, xem bằng player.
17. Vẽ khung và chèn nhãn bằng job của RGA2, tối đa 12 hộp mỗi job: 34 hộp mất khoảng 2 ms thay vì 12 ms (:doc:`../10-luong-camera-den-phat-hien/08-phan-cung-tang-toc` mục 3.2). RGA2 chỉ map được bộ nhớ dưới 4 GB: vẽ trên bộ đệm camera (V4L2) được, không vẽ trên bộ đệm do MPP cấp.

3.2. Sơ đồ luồng theo quyết định
---------------------------------

Sơ đồ thể hiện các quyết định ở mục 3.1. Số trong ngoặc là số mục quyết định. Đây là sơ đồ ý định: dma-buf và zero-copy chưa kiểm trên board. RGA2 mới kiểm vẽ trên bộ đệm camera chưa stream, chưa vẽ trên khung đang chạy (:doc:`../10-luong-camera-den-phat-hien/08-phan-cung-tang-toc`).

.. code:: text

                    Cảm biến OV13855: RAW10 4224x3136, 30 FPS   (mục 2)
                                  |  MIPI CSI-2, VICAP
                                  v
                ISP: cắt 16:9 -> 4224x2376 (bỏ 380 hàng trên, 380 hàng dưới)   (mục 4)
                                  |
                +-----------------+---------------------+
                v                                       v
      LUỒNG 1: video chính                        LUỒNG 2: đưa vào AI
      mainpath, thu nhỏ -> 3840x2160 (4K UHD)     selfpath, thu nhỏ -> 640x360
                |                                       |
                v                                       v
      xoay theo hướng camera (mục 5)              xoay theo hướng camera (mục 5)
      quay camera vật lý hoặc RGA                 quay camera vật lý hoặc RGA
                |                                       |
                |                                       v
                |                                 RGA3: NV12 -> RGB888, đặt vào khung 640x384   (mục 6)
                |                                 viền xám 114 (12 hàng trên, 12 hàng dưới),
                |                                 tô sẵn một lần bằng RGA2
                |                                       |  [1, 384, 640, 3] NHWC
                |                                       v
                |                                 NPU: ba lõi (intra-frame), zero-copy qua C API   (mục 7, 8)
                |                                 model INT8, hiệu chuẩn 300 ảnh   (mục 6)
                |                                       |  tensor (1, 9, 5040)
                v                                       v
      hàng đợi: giữ 1 đến 2 khung 4K              CPU, ghim lõi A76   (mục 9, 11)
      (bộ đệm camera) chờ kết quả AI (mục 14)     hậu xử lý (giải mã hộp, NMS) -> ByteTrack
                |                                 -> hộp và mã số, dựng chữ nhãn (dùng NEON)
                |                                 quy tắc vi phạm   (mục 15)
                |                                       |  x4K = x640 * 6, y4K = (y384 - 12) * 6
                |                                       |
                +-----------------+---------------------+
                                  v
          RGA2: vẽ khung và chèn nhãn (imblend) bằng job, 12 hộp mỗi job,
          lên khung 4K trên bộ đệm camera (dưới 4 GB)   (mục 12, 17)
                                  |  khung 4K đã vẽ
                +-----------------+---------------------+
                v                 v                     v
           VPU: H.265     bộ JPEG: ảnh vi phạm          GPU: giao diện ứng dụng
           lưu video      lấy từ khung 4K               |
           (mục 16)       (mục 15, 16)                  v
                                                        VOP2: hiển thị
                                                        (khi có màn hình, mục 12)

    Khung đi giữa các khối bằng dma-buf (mục 13). Chương trình chính viết bằng C hoặc C++ (mục 10).
    IEP, FBC không dùng (mục 12).

3.3. Hướng phát triển
---------------------

Ba hướng đã cân nhắc, theo thứ tự nên làm.

.. list-table::
   :header-rows: 1
   :widths: 24 36 40

   * - Hướng
     - Việc phải làm
     - Rủi ro
   * - Hoàn thiện hệ thống 30 FPS thật
     - Thay model giữ độ chính xác, đo lại trên camera. Nối RGA, VPU. Chạy tracking với người thật, chạy dài, đo độ trễ, nhiệt, CPU còn dư. Đã có: chương trình camera chạy 45 phút với model INT8 mặc định, phòng trống, chưa phải nghiệm thu
     - Ít mới về NPU, đóng góp nằm ở tích hợp và số đo hệ thống thật
   * - Dùng phần dư để tăng độ chính xác
     - Thử YOLOv8s, huấn luyện lâu hơn, thêm seed. Phần dư khoảng 13 đến 14 ms
     - Tốn huấn luyện. Chưa chắc lọt 33.3 ms sau khi cộng tracking, mã hóa
   * - Đẩy thông lượng NPU
     - Nhiều lõi kết hợp đưa giải mã ra CPU, zero-copy, SRAM. Đã có 141.13 FPS ba lõi trên ảnh nạp sẵn
     - Một camera 30 FPS chưa cần. Chỉ có ý nghĩa khi có yêu cầu nhiều camera

Không còn theo: trọng số 4 bit (``w4a8``), custom op trên NPU, đổi activation sang ReLU, LeakyReLU, ReLU6. Chưa quyết: có thử driver ``accel/rocket`` không.
