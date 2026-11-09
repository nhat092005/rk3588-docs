:tocdepth: 1

***************
Chạy liên tục
***************

.. admonition:: Trang này trả lời

   - Chương trình ``ai/board/app/camera.py`` chạy luồng camera, ISP, NPU, hậu xử lý liên tục ra sao, và đo những gì?
   - Luồng này có theo kịp camera 30 khung/giây không, mất khung hay không, độ trễ bao nhiêu?
   - Chương trình đã khóa những điều kiện đo nào, còn gì chưa làm?

.. admonition:: Tóm tắt

   1. ``camera.py`` chạy liên tục: ``v4l2-ctl`` lấy NV12 640x360 từ ``selfpath`` của ISP (cắt 16:9 ở ISP), CPU đổi NV12 sang BGR, ``preprocess``, suy luận RKNN, ``postprocess_raw``, ByteTrack tùy chọn (``--track``). Kết quả ra JSON, ``--save-dir`` lưu ảnh mẫu có vẽ hộp, ``--save-video`` ghi video MP4 (mục 1).
   2. Cả ba lần kiểm (60 giây không khóa xung, 120 giây khóa xung, 60 giây khóa xung kèm ByteTrack) chạy 29.95 đến 29.96 khung/giây, bằng tốc độ camera. Không khung nào bị ghi đè, ISP báo ``frameloss`` 0 [T3 board, ``camera.py``].
   3. Độ trễ phần mềm đầu cuối (từ lúc đọc đủ một khung đến hết hậu xử lý) là 18.97 ms trung vị và 19.21 ms p95 khi khóa xung, 26.10 và 27.33 ms khi không khóa. Cả hai nhỏ hơn chu kỳ camera 33.3 ms [T3 board, ``camera.py``].
   4. ``v4l2-ctl`` đệm khối ``stdout`` khi ghi vào ống, làm khung đến theo cặp trễ và sớm. ``stdbuf -o0`` khắc phục (mục 4).
   5. Lần chạy ``--until-stable`` ngày 2026-11-07 với model baseline (45 phút, ổn định ở phút 14, 30 phút ổn định không lỗi, FPS 29.95, đầu cuối p95 19.17 ms) ghi ở :doc:`../09-tien-do/01-phase/05-phase-9-10`. Đó là mốc nhiệt của baseline, chưa phải nghiệm thu cho model đề xuất.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cách chạy
============

Chạy trên board, ghim vào các lõi A76 vì khi không ghim ``preprocess`` chậm hơn 3.3 lần (:doc:`01-buc-tranh-tong-the` mục 5):

.. code:: text

   taskset -c 4-7 .venv-board/bin/python -m ai.board.app.camera \
       --model <thư mục rknn_<độ chính xác>> --core-mask CORE_0 --duration-s 60 \
       --out <json> --run-id <id> --git-commit <sha> --git-dirty true [--track]

Từ máy chủ: ``make board-sync`` rồi ``make bench-camera RUN=<id> PREC=int8 DURATION=60 BOARD=minhnhat@192.168.137.49``, ghi ``experiments/runs/<id>/bench/camera_<ngày>.json`` [Mã nguồn repo, ``Makefile``, :doc:`../09-tien-do/01-phase/05-phase-9-10`]. Các lần kiểm dưới đây ghi ra ``/tmp`` rồi chép ra, để không lẫn với tệp nghiệm thu của Phase 9. Model là ``ppe5_yolov8n_baseline_100ep_s0`` (``rknn_int8``). ``--track`` cần ``ultralytics.trackers`` và ``lap`` trên ``PYTHONPATH`` vì board không có ``ultralytics``, thiếu thì chương trình dừng với thông báo rõ và không đụng vào crop của ISP.

**Lưu ảnh mẫu.** ``--save-dir <thư mục>`` (hoặc ``SAVE=1`` với ``make bench-camera``). Chương trình lưu khung 640x360 có vẽ hộp và nhãn ``tên điểm`` thành JPEG ``frame_<số thứ tự>_<số hộp>det.jpg``, chỉ khi khung có phát hiện, tối đa một ảnh mỗi ``--save-interval-s`` (mặc định 1 giây) và ``--save-max`` ảnh (mặc định 200). Vẽ và mã hóa JPEG chạy ở luồng nền, vòng lặp chỉ sao chép khung. Đo bằng một ảnh test của ppe5 qua cùng model (34 hộp, 5 ảnh) [T3 board, ``Saver``]:

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Việc
     - Thời gian
   * - ``offer`` khi khung được nhận (sao chép khung và hộp), trong vòng lặp
     - tối đa 0.873 ms trong 5 lần
   * - ``offer`` khi bị bỏ qua
     - 0.0006 ms
   * - Vẽ hộp và ghi JPEG, ở luồng nền, trung vị và tối đa
     - 3.76 ms và 21.97 ms

Luồng nền dùng cùng các lõi nên khi cần số đo chính xác hãy chạy không có ``--save-dir``.

**Lưu video.** ``--save-video <tệp.mp4>`` (``VIDEO=1`` với ``make bench-camera``). Chương trình ghi mọi khung 640x360, kể cả khung không có hộp, đã vẽ hộp và nhãn (thêm ``#mã số`` của ByteTrack khi có ``--track``), vào MP4 H.264 (``libx264``, ``ultrafast``, ``crf 23``) qua tiến trình ``ffmpeg``. MP4 phân mảnh nên xem được tới đoạn cuối cùng kể cả khi lần chạy bị ngắt. ``--video-fps`` mặc định 30, camera thật cho 29.95 nên video nhanh hơn thực tế 0.17%. Vẽ và ghi chạy ở luồng nền, hàng đợi 60 khung, đầy thì bỏ khung và đếm. ``ffmpeg`` ghim vào lõi 0 đến 3 khi chạy ``taskset -c 4-7`` [T3 board, ``taskset -cp``]. Kiểm 60 giây, khóa xung, ``--track``, phòng trống tối, so với lần C ở mục 3 (cùng điều kiện, không ghi video) [T3 board, ``camera.py``, ``ffprobe``]:

.. list-table::
   :header-rows: 1
   :widths: 50 25 25

   * - Chỉ số
     - Có ``--save-video``
     - Lần C
   * - FPS xử lý, khung đo
     - 29.96, 1798
     - 29.96, 1798
   * - Đầu cuối trung vị và p95 (ms)
     - 19.273 và 19.768
     - 19.176 và 19.377
   * - CPU tiến trình, hệ thống (%)
     - 18.7, 17.9
     - 16.7, 15.0
   * - RSS đỉnh (MiB)
     - 142.9
     - 140.4
   * - Khung ghi vào video, bỏ vì hàng đợi đầy
     - 1828, 0
     - không có

Video có 1828 khung (gồm 30 khung khởi động), ``ffmpeg`` thoát mã 0, ``ffprobe`` ghi H.264 640x360, 30 khung/giây, 60.93 giây, 708331 byte (nhỏ vì cảnh tối và tĩnh), OpenCV đọc đủ 1828 khung [T3 board, ``ffprobe``]. ``ffmpeg`` dùng khoảng 21.5% một lõi ở giây thứ 20 [T3 board, ``ps``]. Chênh với lần C là 0.10 ms ở trung vị và 0.39 ms ở p95, mỗi bên một lần chạy, chưa lặp [SL].

2. Luồng trong chương trình
===========================

.. code:: text

   v4l2-ctl (qua stdbuf -o0)           luồng đọc                       vòng xử lý
   ISP selfpath, cắt 16:9      NV12    giữ đúng 1 khung mới nhất       NV12 sang BGR (cv2)
   640x360 NV12            ----------> đếm khung bị ghi đè     ------> preprocess
                           qua ống     ghi thời điểm đến               suy luận RKNN
                                                                       postprocess_raw
                                                                       ByteTrack (tùy chọn)
                                                                       ghi số đo từng khung
   Khi kết thúc: dừng v4l2-ctl, đặt lại crop ISP về 4224x3136, ghi JSON

Độ trễ đầu cuối tính từ lúc khung được đọc đủ khỏi ống đến hết hậu xử lý, không gồm thời gian phơi sáng và xử lý trong ISP. Nhiệt độ và CPU đọc tại mỗi mốc một phút. Cửa sổ cuối ngắn hơn 5 giây không được báo.

3. Kết quả
==========

Ghim lõi 4 đến 7, ``CORE_0``, 30 khung khởi động bỏ đi. ``Khóa xung`` là ``lock_freq.sh lock`` (CPU, NPU, DDR ở ``performance``), đã trả ``ondemand`` sau mỗi lần [T3 board, ``camera.py``]. Lần A, B, C phòng không có người nên ``postprocess`` nhận 0 hộp. Lần D (90 giây, khóa xung, ``--track --save-dir``) có người đứng trước camera. Trung vị ms nếu không ghi khác.

.. list-table::
   :header-rows: 1
   :widths: 28 18 18 18 18

   * - Chỉ số
     - A: không khóa, 60 s
     - B: khóa, 120 s
     - C: khóa, ByteTrack, 60 s
     - D: có người, 90 s
   * - FPS xử lý
     - 29.95
     - 29.95
     - 29.96
     - 29.95
   * - Khung đo
     - 1798
     - 3595
     - 1798
     - 2696
   * - Khung đọc từ ống, ISP đếm
     - 1828, 1827
     - 3625, 3624
     - 1828, 1827
     - 2726, 2725
   * - ISP ``frameloss``, khung bị ghi đè, khoảng cách quá 1.5 chu kỳ
     - 0, 0, 0
     - 0, 0, 0
     - 0, 0, 0
     - 0, 0, 0
   * - NV12 sang BGR
     - 0.391
     - 0.166
     - 0.164
     - 0.168
   * - ``preprocess``
     - 0.353
     - 0.297
     - 0.298
     - 0.299
   * - NPU
     - 23.647
     - 17.973
     - 17.978
     - 18.006
   * - ``postprocess``
     - 1.502 (0 hộp)
     - 0.482 (0 hộp)
     - 0.486 (0 hộp)
     - 0.580
   * - ByteTrack
     - không có
     - không có
     - 0.190 (0 hộp)
     - 0.727
   * - Đầu cuối, trung vị và p95
     - 26.101 và 27.333
     - 18.974 và 19.207
     - 19.176 và 19.377
     - 19.835 và 20.581
   * - Chu kỳ camera, trung vị và p95
     - 33.380 và 34.134
     - 33.389 và 33.429
     - 33.391 và 33.429
     - không ghi
   * - Nhiệt NPU đầu, cuối (°C)
     - 49.0, 54.5
     - 54.5, 56.4 (cao nhất 57.3)
     - 49.9, 55.5 (cao nhất 56.4)
     - 44.4, 54.5 (cao nhất 58.2)
   * - CPU tiến trình, hệ thống (%)
     - 41.0, 18.8
     - 16.1, 14.8
     - 16.7, 15.0
     - 18.7, 16.7
   * - RSS đỉnh (MiB)
     - 138.8
     - 138.4
     - 140.4
     - 143.6

Ghi chú:

- Khung ISP đếm và khung đọc lệch 1. Chu kỳ camera 33.39 ms ứng với 29.95 khung/giây, thấp hơn 30 danh nghĩa của cảm biến [T3 board, ``v4l2-ctl --verbose``].
- Cột A: cuối lần chạy xung lõi 6 là 600 MHz (đầu là 1608 MHz) và DDR từ 528 lên 2112 MHz. So với cột B, NV12 sang BGR chậm hơn 2.4 lần, ``postprocess`` chậm hơn 3.1 lần, ``preprocess`` 1.2 lần, NPU chậm hơn 5.7 ms. Do xung DDR, xung CPU hay cả hai: unknown, chưa tách riêng.
- Cột C: ByteTrack tốn 0.190 ms vì khung không có hộp. Với 34 người là 5.6 ms (:doc:`06-sau-npu` mục 2), không phải số của lần chạy này.
- CPU thấp (16%) vì mỗi khung xử lý 19 ms trong chu kỳ 33 ms và NPU chạy ngoài CPU.
- Cột D: trung bình 0.59 hộp mỗi khung, lưu 80 ảnh (1 đến 2 hộp mỗi ảnh, bỏ vì hàng đợi đầy 0). Đầu cuối cao hơn cột C 0.66 ms, gần bằng phần chênh của ``postprocess`` và ByteTrack (0.094 và 0.537 ms), nên ghi 80 ảnh gần như không làm tăng trung vị [SL, phép trừ]. P95 cao hơn 1.2 ms, có thể do bước sao chép khung (tối đa 0.9 ms) cộng chi phí hộp [SL], chưa tách riêng.
- Ảnh mẫu của cột D rất tối: điểm ảnh trung bình 7.1 trên thang 0 đến 255 (4.7 đến 12.2). Sau lần chạy cảm biến ở ``exposure`` 2893 (tối đa 3210) và ``analogue_gain`` 1984 (tối đa), tức tự động phơi sáng chạm giới hạn gain [T3 board, ``v4l2-ctl --list-ctrls``]. Hộp phủ gần cả khung (``Person`` 0.32 đến 0.76, ``NoVest`` 0.56), nên không dùng làm ảnh mẫu đúng, sót, nhầm. Nghi do phòng thiếu sáng và người đứng quá gần [SL]. Ảnh là ảnh người thật nên nằm ở ``experiments/camera/camera_runs/with_person/images``, không đưa vào docs hay commit.

4. Hai phát hiện khi viết chương trình
=======================================

**Khung đến theo cặp trễ và sớm.** Lần chạy đầu cho 228 khoảng cách trên 1.5 chu kỳ trong 1827 khoảng, đúng 228 ở cả hai lần chạy (mẫu lặp mỗi 8 khung), p95 đầu cuối 51.8 ms. Dấu thời gian kernel của ``rkisp_selfpath`` lại đều: 33.39 ms ở cả 239 khoảng [T3 board, ``v4l2-ctl --verbose``]. Đọc ống bằng chương trình tối giản không có model vẫn cho 59 khoảng trễ trên 50 ms và 60 khoảng sớm dưới 15 ms trong 480 khung. Với ``stdbuf -o0 v4l2-ctl`` mọi khoảng nằm giữa 32.2 và 34.5 ms [T3 board]. Vậy ``v4l2-ctl`` đệm khối ``stdout`` khi ghi vào ống. Nới ống lên 1 MiB và giảm ``switchinterval`` không đổi số 228 nên đã bỏ. Chương trình dùng ``stdbuf -o0`` trong ``capture_command``.

**Khoảng cách khung không phải số khung mất.** Một khoảng trễ thường kèm một khoảng sớm, nên đếm khoảng cách ước lượng mất khung sai. Chương trình ghi ``late_intervals`` chỉ như chỉ báo dao động, và lấy mất khung từ bộ đếm ISP (``isp_frames``, ``isp_frameloss`` trong ``/proc/rkisp0-vir1``) đối chiếu với số khung đọc được [T3 board].

5. Điều kiện chương trình tự khóa
==================================

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Điều kiện
     - Cách xử lý
   * - Crop của ISP là trạng thái của board, giữ qua các lần mở nút
     - Đặt crop tường minh khi bắt đầu, kể cả ``--no-crop``. Đặt lại 4224x3136 ở khối ``finally`` và khi nhận SIGTERM (mục 5.1)
   * - Ống không có khung ranh giới
     - Kiểm ``bytesperline`` bằng chiều rộng và ``sizeimage`` bằng 640x360x1.5 trước khi chạy, đọc đúng ``sizeimage`` byte mỗi khung
   * - ``numpy.linalg`` chậm khoảng 100 lần với số luồng BLAS mặc định
     - ``OPENBLAS_NUM_THREADS=1`` ở câu lệnh đầu tiên, trước khi import ``numpy`` (:doc:`06-sau-npu` mục 2)
   * - Số đo phụ thuộc lõi và xung
     - JSON ghi ``sched_getaffinity``, số luồng ``cv2``, ``OPENBLAS_NUM_THREADS``, ``frequency_state`` trước và sau
   * - RSS tăng 2 MiB mỗi phút trong lần chạy 45 phút đầu
     - ``rknnlite`` để lại cấu trúc ctypes (bộ đệm đầu vào 1.2 MB) trong vòng tham chiếu. ``gc.freeze()`` trước khi mở camera, ``gc.collect()`` mỗi phút (cột ``gc_collect_ms``), bản ghi từng khung lưu bằng ``array('d')``. ``mallopt(M_MMAP_THRESHOLD)`` làm đầu cuối chậm thêm 2.3 ms nên đã bỏ (:doc:`../09-tien-do/01-phase/05-phase-9-10`)
   * - Không có khung nào sau khởi động
     - Thoát với thông báo rõ thay vì ghi JSON rỗng

5.1. Kết quả kiểm đường dừng
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tình huống
     - Kết quả trên board
   * - Chạy bình thường (60 đến 120 s)
     - Crop về 0, 0, 4224, 3136 và không còn ``v4l2-ctl``
   * - SIGTERM sau 12 s
     - Mã thoát 143, crop về 4224x3136, không còn ``v4l2-ctl``. Trong lúc chạy crop là 0, 380, 4224, 2376
   * - SIGKILL tiến trình Python
     - Crop còn 0, 380, 4224, 2376 (``finally`` không chạy), ``v4l2-ctl`` tự thoát. Lần sau với ``--no-crop`` đặt lại tường minh về 4224x3136
   * - Thiếu ``ultralytics.trackers`` với ``--track``
     - Thoát với thông báo rõ trước khi đổi crop, crop giữ 4224x3136

Nguồn: [T3 board, ``v4l2-ctl --get-selection``, ``/proc/rkisp0-vir1``, ``pgrep``]. Sau SIGKILL crop kẹt ở 16:9 đến lần chạy kế, nên mọi lần chạy đều đặt crop tường minh.

6. Giới hạn và điều chưa biết
==============================

- Video mới thử với phòng trống tối. Ảnh lần D quá tối làm ảnh mẫu (mục 3). Chọn ảnh đúng, sót, nhầm theo yêu cầu Phase 9 cần người xem và phòng đủ sáng.
- Phase 9 yêu cầu chạy tới khi nhiệt độ ổn định rồi thêm 30 phút [Mã nguồn repo, :doc:`../09-tien-do/01-phase/05-phase-9-10`]. ``--until-stable`` làm việc đó, nhưng chỉ có một lần chạy dài, model baseline, phòng trống. Hộp kiểm Phase 9 chưa đánh dấu.
- Đầu vào model do bộ thu nhỏ trong ISP tạo ra, không phải ``cv2.INTER_LINEAR`` của bộ đánh giá [SL]. Ảnh hưởng lên độ chính xác: unknown.
- ``postprocess`` và ByteTrack chưa đo với nhiều người trong phòng đủ sáng (34 người bằng hộp giả: 5.6 ms, :doc:`06-sau-npu` mục 2).
- Chương trình đi đường CPU cho đổi màu và thêm viền. RGA đo riêng ở :doc:`04-tien-xu-ly`, chưa nằm trong luồng liên tục.
- Chỉ chạy một context ở ``CORE_0``. Chưa đo ``CORE_0_1_2`` trong luồng camera.
- Độ trễ không gồm thời gian từ phơi sáng đến khi ISP ghi xong khung. ISP báo ``delay:29ms`` ở dòng ``Output`` của ``/proc/rkisp0-vir1`` [T3 board], ý nghĩa chính xác: unknown.
