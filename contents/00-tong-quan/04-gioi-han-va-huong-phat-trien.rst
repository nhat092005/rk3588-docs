:tocdepth: 1

****************************
Giới hạn và hướng phát triển
****************************

.. admonition:: Trang này trả lời

   - Đề tài không làm được gì với NPU RK3588S, và làm được gì?
   - Có những tầng nào để tối ưu, mỗi tầng tối ưu cái gì, đã đo hay chưa?
   - Trọng tâm của đề tài nên đặt ở đâu?

.. admonition:: Tóm tắt

   - Giới hạn tùy biến: TRM không mô tả tập lệnh, NPU chạy theo danh sách thanh ghi. Thanh ghi có trong TRM và có driver mã nguồn mở. Hãng không công bố kiểu dataflow và chức năng firmware của MCU. Toolkit và ``librknnrt`` phát hành ở dạng file biên dịch. Custom op của hãng có backend là CPU và GPU, không có NPU.
   - Giới hạn tối ưu: ba lõi, tới 6 TOPS tổng, bộ đệm trong 384 KB mỗi lõi, System SRAM tối đa 956 KB dùng chung. Với RK3588, khi lượng tử hóa model bằng toolkit chỉ có một kiểu dùng được: trọng số và activation đều 8 bit (``w8a8``).
   - YOLOv8n của dự án: 55 trên 64 lớp Conv đã căn lề channel theo bảng của hãng, không có lớp Depthwise.
   - Mốc là 30 FPS vì camera chỉ có 30 khung/giây. FPS đã đạt, điểm yếu là độ chính xác của model đang chạy trên camera.
   - Năm nhóm việc làm được: sửa model, xử lý op, chỉnh build, tận dụng phần cứng, chỉnh hệ thống.
   - Đã đo và có lợi: giữ FP16 cho nhánh giải mã box (về độ chính xác), đưa giải mã box ra CPU và chạy song song với NPU, mỗi lõi chạy một khung riêng, ghim CPU và ngắt (về độ ổn định). Đã đo và loại: ReLU, LeakyReLU, ReLU6, một khung chia cho ba lõi, thêm worker tiền xử lý và hậu xử lý, QAT (không hơn đưa giải mã ra CPU).
   - Mục 6 liệt kê 10 việc chỉ trả lời được bằng phép đo trên board.
   - Mục 4 liệt kê bốn hướng, người dùng chưa chọn.
   - Mục 5 đối chiếu hai đoạn đề xuất bên ngoài với nguồn: 25 điểm lệch hoặc thiếu điều kiện.
   - Số đo là một board. Phần lớn là một seed, riêng model SiLU gốc và ReLU có 3 seed để mô tả nhiễu.

.. contents:: Trang này gồm
   :local:
   :depth: 2

1. Giới hạn
===========

1.1. Giới hạn tùy biến
----------------------

Đề tài chạy trên stack của hãng. Mỗi tầng cho phép chỉnh ở mức khác nhau:

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

- Tự viết phép tính cho NPU. TRM không mô tả tập lệnh, NPU chạy theo danh sách thanh ghi nạp từ bộ nhớ [T1 TRM1 tr.1994]. UG232 và API232 không nhắc tới ``regcmd``.
- Sửa bước biên dịch. Toolkit và ``librknnrt`` phát hành dạng file ``.so``.
- Thêm op mới chạy trên NPU. Custom op chỉ có backend CPU và GPU [T1 UG232 tr.94]. Matmul API chạy trên NPU nhưng chỉ nhân ma trận [T1 UG232 tr.41] (:doc:`../02-nen-tang-rk3588/03-toolchain-runtime/04-operator-list` mục 5).
- Biết chắc bên trong NPU từ tài liệu hãng. Hãng không công bố dataflow và chức năng firmware của MCU, TRM và Mesa lệch nhau về số bank của bộ đệm (:doc:`../09-tien-do/03-khoang-trong/01-npu`). Về MCU, mã gửi job của driver do CPU chính chạy và không nhắc tới MCU [T1 DRV rknpu_job.c:272-375], còn việc MCU có chạy gì khác thì TRM không mô tả.

**Làm được**

- Sửa model: đổi activation, đưa giải mã box ra CPU, thay op ngoài NPU bằng phép tương đương [T1 UG232 tr.141].
- Chỉnh tham số build của ``rknn.config``, ví dụ ``quantized_dtype``, ``optimization_level``, ``op_target`` (API232 tr.7 đến tr.11).
- Chọn cách chạy: chọn lõi [T1 UG232 tr.73], zero-copy [T1 UG232 tr.64], cờ SRAM [T1 UG232 tr.107].
- Tận dụng khối phần cứng khác: ISP, RGA, VPU, GPU, System SRAM.
- Tổ chức lại phần CPU quanh NPU: tiền xử lý, hậu xử lý, ghim CPU, khóa xung.
- Sửa driver và DTS: mã nguồn GPL-2.0, và bật SRAM cần bước này [T1 UG232 tr.106]. Dự án chưa làm.

**Ngoài stack của hãng**

Linux có driver mở ``accel/rocket`` cho NPU RK3588, và Mesa đã tự sinh danh sách thanh ghi cho nó, nên hãng không phải đường duy nhất. Chưa dùng được ngay cho đề tài: nó nhận model TensorFlow Lite thay vì ``.rknn``, ``rkt_ml.c`` của Mesa chỉ xử lý Convolution, Add, Pooling, và driver có từ kernel 6.18 trong khi board chạy 6.1.99 (:doc:`../02-nen-tang-rk3588/01-phan-cung-npu/05-ban-do-thanh-ghi-va-co-che-cau-hinh` mục 6).

1.2. Giới hạn tối ưu
--------------------

Mỗi dòng: giới hạn, rồi nghĩa với đề tài.

- **Kiểu số.** Phần cứng có "integer 4, integer 8, integer 16, float 16, Bfloat 16 and tf32" [T1 TRM1 tr.1984], nhưng khi lượng tử hóa model, RK3588 chỉ dùng được kiểu trọng số và activation đều 8 bit (``w8a8``): trọng số 4 bit (``w4a8``) được ghi "(Not supported yet)", kiểu 16 bit (``w16a16i``) được ghi "(Only RV1103/RV1106 supported)" [T1 API232 tr.7]. Nên đề tài dùng INT8, FP16, hoặc trộn hai kiểu trong một đồ thị.
- **Sức tính.** Ba lõi, 1024 MAC int8 mỗi lõi mỗi chu kỳ [T1 TRM1 tr.1984], tối đa 1000 MHz [T1 DRV ``dts/rk3588s.dtsi:3482-3640``]. Hãng ghi tổng "computing power is up to 6TOPs" [T1 DS V1.7 tr.7], không ghi số mỗi lõi. Nên đề tài đọc giới hạn từ số đo, không tính từ TOPS.
- **Bộ nhớ trong SoC.** Bộ đệm 384 KB mỗi lõi [T1 TRM1 tr.1984], System SRAM cấp được tối đa 956 KB cho các IP, có thể đã cấp cho IP khác như codec [T1 UG232 tr.106]. Model INT8 mặc định có tổng 6.256 MiB dữ liệu trung gian giữa các lớp (tensor trong) [T3 board], lớn hơn phần SRAM đó. Lượng dữ liệu cần giữ cùng lúc thì chưa biết.
- **Băng thông DDR.** Hãng không ghi theo GB/s. 34.1 GB/s là trần tính từ thông số bộ điều khiển với LPDDR4/4X bốn kênh (:doc:`../02-nen-tang-rk3588/04-bo-nho-hieu-nang/01-ddr-tren-rk3588`). Băng thông thực trên board chưa đo.
- **Đa nhân.** Ba lõi không có nghĩa nhanh gấp ba. Một khung chia cho ba lõi (một context, tức một phiên suy luận độc lập) chỉ hơn một lõi 2.6% về FPS (56.1 so với 54.66). Mỗi lõi chạy một khung riêng (ba context) đạt 141.18 FPS [T3 board].
- **API.** Zero-copy chỉ có ở C API, RKNNLite 2.3.2 không có ``rknn_set_io_mem`` [T3 board, :doc:`../03-phuong-phap/03-tang-npu-don-bay/06-memory-copy`], nên muốn đo phải viết chương trình đo bằng C. Về Python: ba luồng 141.2 FPS và ba tiến trình 143.5 FPS gần như bằng nhau (chênh 1.7%) [T3 board], còn việc ``RKNNLite.inference`` có nhả GIL không thì chưa kết luận.
- **Quy tắc kích thước của hãng.** Là khuyến nghị, không phải giới hạn: "These rules are not mandatory." [T1 UG232 tr.144]. Model SiLU gốc của dự án có 55 trên 64 lớp Conv đã căn lề channel (:doc:`../03-phuong-phap/03-tang-npu-don-bay/07-compiler-optimization` mục 2.5).

1.3. Ràng buộc riêng của đề tài
-------------------------------

Các ràng buộc này do đề tài đặt, không phải do phần cứng.

- 5 lớp: Helmet, NoHelmet, NoVest, Vest, Person. Toolkit RKNN 2.3.2, một board Orange Pi 5 (RK3588S).
- Mục tiêu 30 FPS, người dùng đổi từ 60 FPS ngày 2026-11-08. Cảm biến chỉ có một chế độ 30 khung/giây [T3 board], nên FPS cao hơn của NPU không tạo thêm khung từ camera. Các trang kết quả đã đo lúc mốc còn là 60 FPS và đã đọc lại theo mốc 30 FPS (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8).
- Mọi op hoặc thay đổi kiến trúc ứng viên phải qua bốn cổng G1 đến G4. G1 và G3 hỏi op chạy được trên NPU không, G4 hỏi đổi có đáng không. G4 có ba điều kiện: A, phủ đa nhân (lớp chia từ hai lõi chiếm ít nhất 50% cycles ước tính của build INT8), B, latency (ba lõi giảm ít nhất 5% so với một lõi, và mức giảm lớn hơn chênh lệch giữa hai phiên), C, độ chính xác (AP50-95, AP NoHelmet, AP Vest mỗi cột giảm tối đa 1.0 điểm so với SiLU cùng kiểu số và seed). Đưa giải mã ra CPU, giữ FP16 nhánh box và QAT chưa qua cổng này mà có tiêu chí riêng (:doc:`../03-phuong-phap/03-tang-npu-don-bay/01-operator-support`).

2. Những gì làm được
====================

Mốc hiện tại là 30 FPS: cảm biến chỉ có một chế độ 30 khung/giây, nên mỗi khung có 33.3 ms [T3 board, :doc:`../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`]. Chạy liên tục với camera, model SiLU gốc INT8 mặc định, một lõi NPU, khóa xung: 29.95 FPS, đầu cuối 18.97 ms, trong đó NPU 17.97 ms. Số này là mức tốt nhất, đo trong phòng trống, 0 hộp. Có người đứng trước camera và bật tracking thì đầu cuối 19.84 ms. Vậy FPS đã đạt, và phần dư khoảng 13 đến 14 ms là thứ có thể đem dùng. Điểm yếu là độ chính xác: lần chạy camera dùng bản INT8 mặc định, bản này chấm trên tập test ``css_test`` chỉ đạt AP50-95 36.75, trong khi đã có bản gần cùng tốc độ đạt 49.66 nhưng chưa chạy trên camera. Độ chính xác trên chính ảnh camera thì chưa đo.

Các bảng dưới chia theo năm nhóm việc. Mỗi dòng ghi việc đó lợi gì, dự án đã có gì, còn thiếu gì. Số đo là một board, phần lớn một seed. Chi tiết ở :doc:`../03-phuong-phap/03-tang-npu-don-bay/index` và :doc:`../10-luong-camera-den-phat-hien/index`.

2.1. Sửa model
--------------

.. list-table::
   :header-rows: 1
   :widths: 24 24 28 24

   * - Việc
     - Lợi gì
     - Hiện trạng trong dự án
     - Còn thiếu
   * - Đổi SiLU sang ReLU, LeakyReLU, ReLU6
     - Latency nhanh hơn 20.9% đến 22.3% ở một lõi
     - Đã đo, **loại**. AP50-95 kém 3.51, 2.64, 3.63 điểm, ngưỡng 1.0. ReLU 200 epoch kém SiLU 200 epoch 1.78 điểm, cũng loại (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/02-ket-qua-bien-the-activation`)
     - Không còn việc
   * - Đưa giải mã box ra CPU (tách đầu, A1)
     - Độ chính xác INT8 về mức FP16, phần NPU nhẹ hơn
     - Đã đo. AP50-95 49.84. NPU 13.07 ms, giải mã numpy 8.02 ms. CPU chạy song song với NPU thì 65.99 FPS trên ảnh nạp sẵn (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`)
     - Chưa chạy trên camera. Thứ tự đầu ra chưa kiểm
   * - Bỏ DFL (A2)
     - Đơn giản đầu ra
     - Đã đo. INT8 mặc định vẫn mất 12.58 điểm, có tách đầu thì 49.96
     - Không hơn tách đầu ngoài nhiễu
   * - Huấn luyện lâu hơn
     - Độ chính xác, không tốn latency
     - SiLU 200 epoch hơn 100 epoch 1.21 điểm, nhỏ hơn khoảng trải giữa seed 1.35
     - Thêm seed mới kết luận được
   * - Dùng cỡ lớn hơn (YOLOv8s)
     - Tiêu phần dư để đổi lấy độ chính xác
     - Chưa đo trên NPU
     - Huấn luyện, build, đo trong ngân sách 33.3 ms
   * - Input hình chữ nhật 16:9, bội số 32
     - 640x384: khoảng 60% điểm ảnh, nhanh hơn, không mất chi tiết so với hiện tại. 832x480: khoảng 97% điểm ảnh, chi tiết hơn khoảng 1.7 lần (tự tính, chưa đo)
     - Chưa đo, đang dùng 640x640 với 44% diện tích là viền. 360 không chia hết cho 32, nên 640x360 phải đổi thành 640x352 hoặc 640x384
     - CSS đã bị kéo về 640x640, nên cần tập ảnh camera có nhãn mới so được AP. Sửa code đang giả định ảnh vuông. ISP chưa thử xuất 832x480
   * - Cắt vùng quan tâm thay vì thu nhỏ cả khung
     - Giữ chi tiết vật nhỏ, đổi lại mất phần ảnh bên ngoài vùng cắt
     - Chưa đo. ISP đã cắt được 16:9
     - Chọn vùng theo bài toán thực tế, đo trên camera
   * - Tái tham số hóa (RepVGG, QARepVGG, DBB)
     - Gộp nhánh lúc suy luận
     - Chưa đo. Rủi ro khi INT8 (:doc:`../01-kien-thuc-nen/06-thiet-ke-model/01-tai-tham-so-hoa-cau-truc`)
     - Huấn luyện lại, đo AP và latency ở INT8
   * - Căn lề channel theo bảng của hãng
     - Hãng ghi chạy hiệu quả hơn, không bắt buộc
     - 55 trên 64 lớp Conv đã căn, 9 lớp lệch (:doc:`../03-phuong-phap/03-tang-npu-don-bay/07-compiler-optimization` mục 2.5)
     - Chưa đo tác dụng

2.2. Xử lý op
-------------

Op chạy ngoài NPU vì ba lý do: vượt kích thước, chưa hỗ trợ, phần cứng không làm được [T1 UG232 tr.139]. Hiện model không vướng: op tính toán duy nhất trên CPU là ``Transpose`` của DFL, và cách đưa giải mã ra CPU không còn op này (:doc:`../03-phuong-phap/03-tang-npu-don-bay/03-tensor-layout`). Nhóm này chỉ cần lại khi đổi model.

Chạy ngoài NPU khác với chỉ chạy lõi 0. Khi một khung chia cho ba lõi, op không hỗ trợ đa nhân vẫn chạy trên NPU nhưng về lõi 0. Ở model SiLU, 57 trên 57 lớp ``ConvExSwish``, cùng ``Resize``, ``Split``, ``MaxPool`` chỉ chạy lõi 0, các lớp chia từ hai lõi chỉ chiếm 1.8% cycles ước tính [T3 board]. Vì vậy một khung chia ba lõi gần như không có lợi. Cách mỗi lõi một khung không vướng việc này (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/01-ket-qua-g4`).

.. list-table::
   :header-rows: 1
   :widths: 24 24 28 24

   * - Việc
     - Lợi gì
     - Hiện trạng trong dự án
     - Còn thiếu
   * - Thay op bằng phép tương đương
     - Đưa op về NPU
     - Chưa cần. Hãng có ví dụ [T1 UG232 tr.141]
     - Chỉ cần khi model mới có op ngoài NPU
   * - Ép đích chạy bằng ``op_target``
     - Chọn CPU, NPU hay GPU cho từng op [T1 API232 tr.9]
     - Chưa dùng
     - Chưa có nhu cầu
   * - Đổi thiết bị dự phòng sang GPU
     - Op không chạy NPU thì sang GPU thay CPU [T1 API232 tr.17]
     - Chưa dùng
     - Chưa thử trên board
   * - Custom op
     - Tự viết phép tính cho CPU hoặc GPU [T1 UG232 tr.94]
     - Chưa dùng (:doc:`../02-nen-tang-rk3588/03-toolchain-runtime/04-operator-list` mục 5)
     - Chưa có nhu cầu. Chi phí chưa đo
   * - Cắt đồ thị, đẩy phần tính ra CPU
     - NPU chỉ làm phần liên tục
     - Đã làm, chính là cách đưa giải mã ra CPU
     - Xem mục 2.1
   * - Gộp op
     - Bớt op rời
     - 57 trên 64 lớp Conv đã gộp với SiLU thành ``ConvExSwish``, toolkit tự làm
     - Không còn việc lớn

2.3. Chỉnh build
----------------

.. list-table::
   :header-rows: 1
   :widths: 24 24 28 24

   * - Việc
     - Lợi gì
     - Hiện trạng trong dự án
     - Còn thiếu
   * - Giữ FP16 cho đoạn tính tọa độ hộp, còn lại INT8 (``h5``)
     - Lấy lại độ chính xác INT8
     - Đã đo. AP50-95 36.75 lên 49.66 (FP16: 49.76), latency đổi dưới 5%, FPS gần như không đổi (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`)
     - Chưa chạy trên camera. Nguyên nhân lấy lại điểm chưa biết
   * - Huấn luyện có lượng tử hóa (QAT)
     - Độ chính xác INT8
     - Đã đo. 49.85, hơn cách đưa giải mã ra CPU 0.01 điểm, nằm trong nhiễu (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`)
     - Không thêm gì
   * - Đổi thuật toán lượng tử hóa
     - Độ chính xác INT8
     - ``kl_divergence``, ``auto_hybrid`` không lấy lại điểm. ``mmse`` không dựng được với 300 ảnh hiệu chuẩn
     - ``mmse`` chưa có kết quả
   * - ``optimization_level`` thấp hơn
     - Xem pass nào đáng giá
     - Chưa đo trên model của dự án, đang dùng mặc định. Có thử ``eval_perf`` ở mức 3 và 2 trên YOLOv8n trọng số ngẫu nhiên (:doc:`../09-tien-do/03-khoang-trong/03-toolchain-compiler`)
     - Build, đo latency và AP
   * - ``single_core_mode``
     - Giảm cỡ và bộ nhớ model (API232 tr.9)
     - Chưa đo
     - Build, đo. Có ích nếu chỉ dùng một lõi
   * - ``compress_weight``, ``remove_weight``, ``model_pruning``
     - Giảm cỡ model, bộ nhớ, hoặc phép tính nếu trọng số thưa (API232 tr.9)
     - Chưa đo
     - Cỡ file hiện không phải mục tiêu

2.4. Tận dụng phần cứng
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 24 24 28 24

   * - Việc
     - Lợi gì
     - Hiện trạng trong dự án
     - Còn thiếu
   * - NPU nhiều lõi: mỗi lõi chạy một khung riêng
     - Thông lượng
     - Đã đo trên ảnh nạp sẵn. Một lõi 54.69, hai lõi 101.90, ba lõi 141.13 FPS (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`). Số 54.66 và 141.18 ở mục 1.2 là một lần đo khác
     - Một luồng camera 30 FPS chưa cần. Có ích khi nhiều camera, hoặc kết hợp việc nặng khác
   * - NPU: một khung chia cho ba lõi
     - Latency một khung
     - Đã đo, **loại** với SiLU: giảm 2.9%
     - Không còn việc
   * - ISP thu nhỏ, cắt ảnh
     - Bớt việc cho CPU và RGA
     - Đang dùng. NV12 640x360 ở 29.95 fps, cắt 16:9 tại ISP (:doc:`../10-luong-camera-den-phat-hien/03-isp-va-vong-3a`)
     - Ảnh ISP thu nhỏ khác bộ đánh giá, ảnh hưởng AP trên camera chưa đo. Có so ảnh tĩnh FP32, thêm viền với kéo dãn, khoảng tin cậy chứa 0 (:doc:`../10-luong-camera-den-phat-hien/04-tien-xu-ly` mục 8)
   * - RGA đổi màu, thu nhỏ, thêm viền
     - Bớt CPU
     - Đo từng lệnh, chưa nối vào chương trình. Khóa xung, dma-buf: 640x360 sang 640x640 có viền 0.569 ms, 1080p 2.015 ms (:doc:`../10-luong-camera-den-phat-hien/04-tien-xu-ly`). CPU khi chạy thật, khóa xung, ghim lõi lớn: 0.463 ms và 2.380 ms, gồm đổi màu và ``preprocess``. Nên ở 640x360 CPU nhanh hơn, ở 1080p RGA nhanh hơn một ít. Hai bên không hoàn toàn cùng việc
     - Chưa đo CPU còn dư khi dùng RGA, và RGA khi CPU đang bận
   * - VPU mã hóa video
     - Chỉ cần khi lưu hoặc truyền video. Mã hóa H.264 hoặc H.265 bằng phần cứng, có thể bớt CPU
     - Đo riêng, chưa so được với ``libx264`` vì khác nguồn ảnh và cấu hình. 300 khung 1080p: ``mpph264enc`` 3.05 s, nhưng nguồn ảnh giả đã tốn gần 3 s, nên chỉ biết VPU không chậm hơn 100 khung/giây. ``libx264`` 1.583 s với ``ultrafast``, 8.583 s với preset mặc định (:doc:`../10-luong-camera-den-phat-hien/06-sau-npu`)
     - Chưa đo trần và CPU của VPU, chưa nối vào chương trình. ``camera.py`` đang dùng ``libx264`` ``ultrafast``, tốn khoảng 21.5% một lõi
   * - VPU giải mã
     - Nguồn là luồng nén
     - Không cần với camera MIPI
     - Chỉ cần nếu đổi nguồn
   * - GPU Mali
     - Chạy custom op, hoặc dự phòng khi NPU không chạy được
     - Đang không dùng: tải 0 khi chạy bước tiền xử lý, NPU, hậu xử lý bằng chương trình thử. Chưa đọc tải trong ``camera.py``
     - Chưa thử. Chưa có việc cần GPU
   * - System SRAM
     - Giảm truy cập DDR
     - Chưa dùng, kernel trên board chưa bật. Tối đa 956 KB, tổng dữ liệu trung gian 6.256 MiB, lượng cần giữ cùng lúc chưa biết
     - Cần đổi kernel config và DTS (UG232 tr.106), rồi đo
   * - VOP hiển thị
     - Xuất hình trực tiếp
     - Chưa dùng, không nối màn hình lúc đọc
     - Chỉ cần nếu có màn hình

2.5. Chỉnh hệ thống
-------------------

.. list-table::
   :header-rows: 1
   :widths: 24 24 28 24

   * - Việc
     - Lợi gì
     - Hiện trạng trong dự án
     - Còn thiếu
   * - Khóa xung CPU, NPU, DDR
     - Latency thấp hơn, ổn định hơn
     - Đã đo trên camera, cả hai đều ghim lõi 4 đến 7, chạy 120 giây và 60 giây. Đầu cuối 18.97 ms so với 26.10 ms, CPU tiến trình 16.1% so với 41.0% (:doc:`../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`)
     - Chưa tách phần chậm do DDR hay do CPU. Chưa đo công suất. Nhiệt NPU cao nhất 58.2 °C trong các lần chạy camera
   * - Chọn lõi CPU cho ứng dụng và ngắt NPU
     - Độ ổn định latency
     - Đã đo. Không ghim: mức chậm 43% và 46% số lần chạy. Ổn định quanh 16.3 ms ở bảy vị trí trên lõi lớn. Ngắt ở CPU0 hoặc ứng dụng ở CPU0 đến CPU3 không đạt (:doc:`../03-phuong-phap/02-tang-npu-nen-do/05-thu-ghim-cpu-va-ngat`)
     - Cơ chế chưa kết luận. Số này đo bằng chương trình C và ``eval_perf``, chưa đo riêng trong ``camera.py``
   * - Zero-copy
     - "reducing the cost of copying memory, better performance and less bandwidth" [T1 UG232 tr.64]. Chuẩn hóa, lượng tử hóa và suy luận chạy trên NPU [T1 UG232 tr.65]
     - Chưa dùng. Chỉ có ở C API. RK3588: đầu vào 4 chiều 1, 3, 4 channel cần width căn 16 byte, trường hợp khác cần tổng kích thước căn 16 byte
     - Viết chương trình C, đo. Thời gian copy hiện chưa tách
   * - CPU chạy song song với NPU (pipeline)
     - Thông lượng, không giảm thời gian mỗi khung
     - Đã đo. Model đưa giải mã ra CPU +56.9%, model lai +3.3%, ba lõi thêm worker +4.4% (loại). Các trang kết quả không kết luận nguyên nhân (:doc:`../03-phuong-phap/04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`)
     - Chưa chạy trên camera
   * - Giải mã box bằng C hoặc NEON
     - Giảm 8.02 ms của numpy
     - Chưa đo
     - Cần khi dùng cách đưa giải mã ra CPU
   * - Tracking (ByteTrack)
     - Theo dõi đối tượng
     - Đã chạy cùng camera: 0.190 ms khi 0 hộp, 0.727 ms trung vị khi có người đứng trong khung tối (trung bình 0.59 hộp mỗi khung). Riêng hộp giả 34 người, không camera: 5.6 ms cả hiển thị với ``OPENBLAS_NUM_THREADS=1``, và riêng lời gọi ``update`` 447 ms nếu để số luồng mặc định (:doc:`../10-luong-camera-den-phat-hien/06-sau-npu`, :doc:`../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`)
     - Chưa đo trên camera với nhiều người, phòng đủ sáng
   * - Hạ xung DDR để thử
     - Biết DDR có phải nút thắt không
     - Chưa đo. Một khung đọc ghi 39007.22 KB, chỉ một hàng có cycles DDR lớn hơn NPU, nhưng cột NPU Cycles chỉ có cho Conv [T1 UG232 tr.140]
     - Đo FPS ở 1560, 1068 MHz. Cho biết zero-copy và SRAM có đáng làm không

3. Mức bằng chứng
=================

.. list-table::
   :header-rows: 1
   :widths: 44 18 38

   * - Việc
     - Mức
     - Ghi chú
   * - Giữ FP16 đoạn tính tọa độ hộp, đưa giải mã ra CPU, mỗi lõi một khung, khóa xung, chọn lõi CPU
     - Đã đo, có lợi
     - Đo riêng từng việc, trên ảnh nạp sẵn, chương trình C hoặc camera như bảng mục 2
   * - ReLU, LeakyReLU, ReLU6, một khung chia ba lõi, thêm worker, QAT
     - Đã đo, không lợi
     - Mục 2
   * - RGA, VPU, tracking, huấn luyện lâu hơn, ISP thu nhỏ
     - Đo một phần
     - Chưa đo trong hệ thống thật, hoặc chưa đủ seed
   * - Các việc ở mục 6
     - Chưa đo
     - Cần chạy trên board
   * - Trọng số 4 bit (``w4a8``), custom op trên NPU
     - Hãng ghi không có
     - API232 tr.7, UG232 tr.94
   * - Dataflow, TOPS mỗi lõi, firmware MCU
     - Hãng không công bố
     - Mục 1.1 và 1.2

4. Chọn hướng
=============

**Người dùng chưa chọn trọng tâm**, đang đọc phần còn thiếu. Ngày 2026-11-08 người dùng đổi mục tiêu từ 60 xuống 30 FPS, nên phương án chọn trước đó không còn dùng.

.. list-table::
   :header-rows: 1
   :widths: 22 30 24 24

   * - Hướng
     - Việc phải làm
     - Đã có
     - Rủi ro
   * - Hoàn thiện hệ thống 30 FPS thật
     - Thay model giữ độ chính xác, đo lại trên camera. Nối RGA, VPU. Chạy tracking với người thật, chạy dài, đo độ trễ, nhiệt, CPU còn dư
     - Chương trình camera chạy 45 phút với model INT8 mặc định, khóa xung, phòng trống, không tracking. Chưa phải nghiệm thu
     - Ít mới về mặt NPU, đóng góp nằm ở tích hợp và số đo hệ thống thật
   * - Dùng phần dư để tăng độ chính xác
     - Thử YOLOv8s, huấn luyện lâu hơn, thêm seed
     - Phần dư khoảng 13 đến 14 ms, số 200 epoch
     - Tốn huấn luyện. Chưa chắc lọt 33.3 ms sau khi cộng tracking, mã hóa
   * - Đẩy thông lượng NPU
     - Nhiều lõi kết hợp đưa giải mã ra CPU, zero-copy, SRAM
     - 141.13 FPS ba lõi trên ảnh nạp sẵn
     - Một camera 30 FPS chưa cần. Chỉ có ý nghĩa khi có yêu cầu nhiều camera
   * - Kết hợp: hệ thống thật trước, rồi độ chính xác
     - Hai hướng đầu, theo thứ tự
     - Như hai hướng đầu
     - Tốn thời gian nhất

Không còn theo: trọng số 4 bit (``w4a8``), custom op trên NPU, đổi activation sang ReLU, LeakyReLU, ReLU6. Chưa quyết: driver mở ``accel/rocket``.

5. Đối chiếu hai đoạn đề xuất bên ngoài
=======================================

Hai đoạn này do người dùng dán ngày 2026-11-08. Bảng chỉ ghi chỗ lệch hoặc thiếu điều kiện.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Đoạn đề xuất
     - Nguồn và số đo nói gì
   * - Rockchip đóng kín 100%, không có cách viết kernel cho NPU
     - Quá rộng. TRM không mô tả tập lệnh, nhưng có thanh ghi. Driver đọc được mã nguồn, Linux có driver mở (mục 1.1). Phần đóng là toolkit và ``librknnrt``
   * - ReLU giảm 15 đến 20% latency, không giảm mAP
     - Latency: 22.3% ở một lõi, 46.8% ở ba lõi. mAP: ReLU 100 epoch mất 3.51 điểm. ReLU 200 epoch kém SiLU 200 epoch 1.78 điểm (mục 2.1)
   * - Ba lõi đẩy FPS gần 3 lần
     - Mỗi lõi một khung đạt 141.2 FPS, khoảng 2.5 lần so với 56.1 FPS (một context tốt nhất, một khung chia ba lõi), khoảng 2.6 lần so với 54.66 FPS (một lõi). Một khung chia cho ba lõi chỉ +2.6% so với một lõi
   * - ``AUTO`` chậm do driver khóa và đổi ngữ cảnh
     - ``AUTO`` so với một lõi chỉ chênh +0.031 ms (SiLU) và +0.025 ms (ReLU). Đoạn đề xuất không dẫn nguồn cho nguyên nhân này
   * - Quy tắc 6 KB do cache DPU
     - UG232 tr.147 chỉ ghi "the utilization rate is relatively high when KH* KW * KC * type_bytes < 6K Bytes", không nói về DPU cache
   * - Channel bội số 32 và 64 là quy tắc cứng
     - Con số đúng cho INT8, nhưng hãng ghi không bắt buộc (UG232 tr.144, tr.145). Về lý do, hãng ghi phần cứng cần "additional redundant operations" [T1 UG232 tr.144], không nói chèn số 0. Model dự án không có Depthwise
   * - Thay Mish bằng chuỗi có Tanh, Softplus, hoặc bằng Hardswish
     - Theo tài liệu thì không cần phân rã: Operator List có ``exMish`` (tr.98) và ``ConvolutionMish`` (tr.63), bảng op của toolkit liệt kê ``Mish`` và không ghi "Not Supported" (``RKNNToolKit2_OP_Support-2.3.2.md:109``). Dự án chưa chạy thử. Ngoài ra UG232 tr.146 xếp Tanh, Softplus, Hardswish vào nhóm activation kém hiệu quả ("Non-Relu activation function")
   * - Phân rã LayerNorm thành nhiều op nhỏ
     - UG232 ghi luật gộp "ReduceMean + Sub + Pow + ReduceMean + Add + Sqrt + Div (+ Mul + Add) -> LayerNorm" [T1 UG232 tr.148], và Operator List có ``exNorm`` (tr.103). Nghĩa là gộp thành một op, không phải chạy rời nhiều op nhỏ
   * - Tái tham số hóa triệt tiêu op lạ, là giải pháp tối ưu nhất
     - Cơ chế đúng, phạm vi sai: chỉ gộp nhánh Conv, BN, Identity. "Tối ưu nhất" không có số trên RK3588, và RepVGG sụt mạnh khi INT8 (mục 2.1)
   * - Custom op chạy CPU bằng NEON, NPU phải dừng và copy
     - Đúng phần không có NPU: UG232 tr.94 ghi backend là CPU và GPU, repo có demo ``cpu``, ``gpu``, ``pytorch``, không có demo NPU. Mục custom op của UG232 và mã demo không có chữ NEON, UG232 không nói về chi phí dừng và copy
   * - Custom op giữa model làm tụt 50 đến 80% FPS
     - UG232 và docs của dự án không có số này. Dự án chưa đo custom op
   * - Kiểu số gồm INT8, INT16, FP16, không có INT4
     - Đúng về INT4 khi lượng tử hóa model bằng toolkit (``w4a8`` chưa hỗ trợ). Nhưng phần cứng có INT4, và Matmul API có đầu vào int4 (UG232 tr.41). ``w16a16i`` chỉ cho RV1103 và RV1106 (API232 tr.7)
   * - DFL và Softmax chiếm 35.92% độ trễ
     - 35.92% là cả nhóm phi tích chập. Riêng ``exSoftmax13`` là 11.09% (:doc:`../02-nen-tang-rk3588/05-yolo-tren-rk3588/02-op-yolov8-tren-rknn`). Không kết luận được là memory-bound từ bảng này, vì "the NPU Cycles column only displays the Cycles required by Conv" [T1 UG232 tr.140]
   * - Cắt DFL, dùng đầu phát hiện như YOLO26
     - DFL không phải op lạ: ``exSoftmax13`` chạy trên NPU. Bỏ DFL vẫn mất 12.58 điểm khi giữ giải mã trong đồ thị INT8, còn đưa giải mã ra CPU đạt 49.84. YOLO26n chậm hơn YOLOv8n khoảng 13 đến 16% trên trọng số ngẫu nhiên (:doc:`../09-tien-do/03-khoang-trong/06-yolo`)
   * - ReLU mới gộp được với Conv, SiLU thì không
     - SiLU cũng gộp: UG232 tr.142 có Silu trong bảng gộp, model gốc có 57 op gộp Conv với SiLU (``ConvExSwish``). Khác biệt đo được là đa nhân: op này chỉ chạy lõi 0, op gộp Conv với ReLU (``ConvRelu``) chia nhiều lõi
   * - Tối ưu sâu không nằm ở cấu hình compiler
     - Giữ FP16 nhánh box (``h5``) là công thức lượng tử hóa lúc build, đưa AP50-95 từ 36.75 lên 49.66. FPS gần như không đổi so với INT8 (chênh dưới 5%)
   * - Kiến trúc model là tầng quan trọng nhất
     - Số đo không ủng hộ về FPS: mức tăng lớn nhất là ba lõi mỗi lõi một khung ở tầng runtime (+151.7% so với một context tốt nhất, +158.3% so với ``CORE_0``). Đưa giải mã ra CPU chạy song song (tầng model và tầng pipeline gộp lại) hơn model lai chạy lần lượt +20.4%, số này không tách riêng được cho tầng model. ReLU 100 epoch, LeakyReLU, ReLU6 đều bị loại
   * - NPU và DDR dùng ``dmc_ondemand``, khóa xung triệt tiêu cpuidle
     - Mặc định NPU là ``rknpu_ondemand``, chỉ DDR là ``dmc_ondemand`` (``ai/board/lock_freq.sh:6-7``). Lệnh khóa ``performance`` đúng. Khóa xung và tắt ``cpu-sleep`` là hai thao tác riêng, dự án đo riêng trong thí nghiệm ghim lõi
   * - Tách ngắt NPU sang một lõi riêng
     - Thiếu điều kiện. UG232 tr.75 khuyên buộc ngắt vào cùng lõi lớn với ứng dụng. Số đo: ứng dụng ở CPU4 đến CPU7 với ngắt ở CPU4 đạt mức nhanh, không vị trí nào có ngắt ở CPU0 đạt (mục 2.5)
   * - Ghim camera và RGA vào A55, giải mã vào A76
     - Chưa đo trên pipeline camera. Số đo liên quan: tiến trình suy luận ở CPU0 đến CPU3 không đạt mức nhanh (mục 2.5)
   * - Zero-copy qua ``dma-buf``, NPU đọc bằng con trỏ vật lý, không memcpy từ cảm biến đến NPU
     - ``rknn_create_mem_from_fd`` và ``rknn_create_mem_from_phys`` là hai API riêng [T1 UG232 tr.149], đoạn đề xuất gộp hai cách này vào một câu. NPU trên board nằm trong nhóm IOMMU theo ``dmesg`` (:doc:`../10-luong-camera-den-phat-hien/01-buc-tranh-tong-the`). Toàn bộ đường từ cảm biến đến NPU chưa đo (:doc:`../10-luong-camera-den-phat-hien/04-tien-xu-ly`)
   * - Toàn bộ tensor trung gian nằm gọn trong 956 KB SRAM
     - Hãng ghi cấp "as much memory as possible" (UG232 tr.107). Tổng dữ liệu trung gian của model là 6.256 MiB, lượng cần giữ cùng lúc chưa biết
   * - DDR LPDDR4X, trần 34 GB/s
     - 34.1 GB/s là phép tính, hãng không ghi GB/s. Datasheet ghi LPDDR4/LPDDR4X/LPDDR5, không ghi loại của board
   * - DRAM tốn năng lượng gấp 200 lần
     - Số này so DRAM với một phép MAC, tiến trình thương mại 65 nm [T2 Chen 2016 tr.8], không phải DRAM so với SRAM trên RK3588
   * - Python chậm do GIL, API thường tốn ít nhất 2 lần memcpy
     - GIL: ba luồng và ba tiến trình gần như bằng nhau, chưa kết luận về việc nhả GIL. Memcpy: UG232 tr.64 ghi có copy đầu vào, không ghi số lần

6. Việc chỉ trả lời được bằng phép đo
=====================================

Dự án chưa có số cho các việc dưới đây, và phải chạy trên board mới có. Trang này không ghi dự đoán cho chúng.

1. Model giữ độ chính xác trên camera: latency, FPS, độ trễ đầu cuối, khi dùng ``h5`` hoặc đưa giải mã ra CPU.
2. Hạ xung DDR: FPS ở 1560 và 1068 MHz, để biết DDR có phải nút thắt không.
3. Zero-copy qua C API: thời gian copy và FPS, so với đường thường.
4. System SRAM: FPS và lưu lượng DDR, so với không dùng.
5. Băng thông DDR thực trên board, và loại DRAM thực (LPDDR4 hay LPDDR4X).
6. RGA và VPU nối vào chương trình camera: CPU còn dư, độ trễ.
7. Tracking trên camera với nhiều người, phòng đủ sáng.
8. YOLOv8s, input 16:9 (640x384, 832x480), cắt vùng quan tâm, tái tham số hóa, ``single_core_mode``, ``optimization_level`` thấp hơn: latency và AP.
9. Giải mã bằng C hoặc NEON: thời gian so với 8.02 ms của numpy.
10. Công suất khi khóa xung so với không khóa.

Việc cần người dùng quyết: chọn hướng ở mục 4, và có thử driver ``accel/rocket`` không.
