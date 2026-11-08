:tocdepth: 1

*********************
Hậu xử lý và đầu ra
*********************

.. admonition:: Trang này trả lời

   - Tensor thô của NPU thành hộp phát hiện qua những bước nào?
   - Theo dõi gán mã số cho hộp ra sao, chạy ở đâu?
   - Khung ảnh có hộp ra màn hình hoặc luồng nén bằng phần cứng nào?

.. admonition:: Tóm tắt

   1. Hậu xử lý của repo chạy trên CPU bằng numpy: argmax lớp, lọc ``conf > 0.25``, NMS theo lớp IoU 0.7, tối đa 300 hộp [Mã nguồn repo ``ai/board/common.py:24-27, 84-123``].
   2. Model INT8 mặc định có ``T_post`` 0.662 ms (trung vị, một context, khóa xung). Model tách đầu cần giải mã thêm 8.02 ms bằng numpy [T3 board, ``results/thr_p3.json``, ``results/q2j_split.json``]. Trên khung camera thật không có hộp, ``postprocess`` mất 1.501 ms ở điều kiện không khóa xung. Khóa xung: 0.476 ms với 0 hộp và 2.043 ms với 34 hộp (ảnh test ppe5 phóng lên 1080p) [T3 board, ``board_pipeline_test.py``, ``board_pipeline_test2.py``].
   3. Theo dõi dùng ``BYTETracker`` của Ultralytics, hai lần ghép (hộp điểm cao, hộp điểm thấp). Đầu vào của tracker là mọi hộp có conf >= 0.1 (``DET_CONF``). Trong repo chạy offline trên ``detections.npz``, chưa nằm trong luồng thời gian thực [Mã nguồn repo ``scripts/demo/common.py:28``, ``scripts/demo/video/track.py``]. Trên board, với hộp giả và khóa xung, tracker cộng lớp hiển thị mất 5.6 ms cho 34 người trên lõi A76 khi đặt ``OPENBLAS_NUM_THREADS=1``, và 447 ms nếu để số luồng BLAS mặc định (mục 2) [T3 board, ``track_bench.py``].
   4. Ghi video của repo dùng libx264 qua PyAV trên CPU. Mã hóa 300 khung 1080p: libx264 ``crf 20`` mất 8.583 s (41.8 s thời gian CPU), còn ``mpph264enc`` của VPU không chậm hơn nguồn ảnh giả (3.05 s so với 3.00 s) [T3 board, ``gst-launch-1.0``, ``ffmpeg``]. VPU có bộ mã hóa H.264 và H.265, repo chưa dùng [Mã nguồn repo ``scripts/demo/common.py``] [T1 DS V1.7 tr.10].
   5. ``HDMI-A-1`` và ``DP-1`` đều ``disconnected`` lúc đọc [T3 board, ``/sys/class/drm``].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Hậu xử lý
============

.. code:: text

    tensor thô (1, 4 + nc, 8400)       nc = 5 lớp, 8400 = 80x80 + 40x40 + 20x20
       |
       v
    chuyển vị, lấy lớp có điểm cao nhất (argmax) của từng anchor
       |
       v
    giữ anchor có conf > 0.25, tối đa 30000 ứng viên
       |
       v
    đổi (cx, cy, w, h) sang (x1, y1, x2, y2)
       |
       v
    NMS theo từng lớp, IoU 0.7, giữ tối đa 300 hộp
       |
       v
    đổi về tọa độ ảnh gốc: trừ viền, chia hệ số r, cắt vào khung ảnh

Các hằng số: ``CONF = 0.25``, ``IOU = 0.7``, ``MAX_DET = 300``, ``MAX_NMS = 30000`` [Mã nguồn repo ``ai/board/common.py:24-27``]. Các bước theo thứ tự trong ``postprocess`` [Mã nguồn repo ``ai/board/common.py:84-123``]. Model chuẩn đã giải mã hộp trong đồ thị NPU. Model tách đầu bỏ phần đó nên CPU giải mã thêm (:doc:`../03-phuong-phap/03-tang-npu-don-bay/09-pre-post-processing`). Số 8400 là phép tính 80x80 + 40x40 + 20x20 với ảnh 640 và stride 8, 16, 32 [SL].

2. Theo dõi
===========

.. code:: text

    hộp của khung t (conf >= 0.1, DET_CONF)
       |
       v
    BYTETracker (ultralytics)
       |-- ghép lần 1: track hiện có với hộp conf >= 0.25 (track_high_thresh)
       |-- ghép lần 2: track còn lại với hộp 0.1 < conf < 0.25 (track_low_thresh)
       |-- hộp chưa ghép và conf >= 0.25 (new_track_thresh): mở track mới
       |-- track mất vẫn giữ track_buffer = 30 khung
       v
    hộp + mã số
       |
       v
    lớp hiển thị của repo: làm mượt 5 hộp, bỏ phiếu lớp 15 khung,
                           chỉ vẽ sau 3 lần khớp, giữ 5 khung sau khi mất

Tham số ``track_high_thresh`` 0.25, ``track_low_thresh`` 0.1, ``new_track_thresh`` 0.25, ``track_buffer`` 30, ``match_thresh`` 0.8 lấy từ ``bytetrack.yaml`` của Ultralytics [Mã nguồn repo, ``.venv/lib/python3.12/site-packages/ultralytics/cfg/trackers/bytetrack.yaml``]. Tách hộp điểm cao và điểm thấp nằm ở ``byte_tracker.py`` dòng 316 và 317, ghép lần hai ở ``_second_association``. Lớp hiển thị dùng ``--smooth 5``, ``--vote 15``, ``--min-hits 3``, ``--hold 5`` mặc định [Mã nguồn repo ``scripts/demo/video/track.py:97-105``]. ``track.py`` có tham số ``--conf`` mặc định 0.25, và đầu vào tracker là mọi hộp từ ``DET_CONF`` trở lên [Mã nguồn repo ``scripts/demo/video/track.py:3-5, 98``, ``scripts/demo/common.py:28``].

Đo ngày 2026-11-07 trên board với CPU, NPU, DDR khóa ``performance`` bằng ``lock_freq.sh``, 600 khung sau 30 khung khởi động [T3 board, ``track_bench.py``, ``build_trk_pkg.py``]. Mã tracker là các tệp ``byte_tracker.py``, ``basetrack.py``, ``kalman_filter.py``, ``matching.py``, ``stracks.py`` của Ultralytics 8.4.154 trong repo, chép nguyên văn sang board. Board không có ``ultralytics`` và ``torch`` nên ``ultralytics.utils`` được thay bằng bản nhỏ (``LOGGER``, ``xywh2ltwh`` và ``bbox_ioa`` trích nguyên từ mã gốc). Thư viện ``lap`` 0.5.14 cài vào thư mục tạm bằng ``pip --target``, không đổi venv của board. Lớp hiển thị là ``TrackDisplay`` chép từ ``track.py``. Dữ liệu là hộp người giả (chuyển động ngẫu nhiên, 10% khung điểm tụt xuống 0.12 đến 0.24, thêm hộp dương giả bằng một phần năm số người), không phải đầu ra của model. Trung vị ms:

.. list-table::
   :header-rows: 1
   :widths: 14 14 14 14 14 14 16

   * - Người (hộp mỗi khung)
     - A76 ``update``
     - A76 hiển thị
     - A76 tổng
     - A55 ``update``
     - A55 tổng
     - BLAS mặc định ``update``
   * - 5 (6)
     - 1.079
     - 0.214
     - 1.293
     - 4.403
     - 5.310
     - 66.263
   * - 15 (18)
     - 2.298
     - 0.555
     - 2.858
     - 22.522
     - 25.275
     - không đo
   * - 34 (40)
     - 4.418
     - 1.200
     - 5.619
     - 32.895
     - 51.239
     - 447.315
   * - 60 (72)
     - 7.343
     - 2.105
     - 9.447
     - 59.651
     - 82.253
     - không đo

Điều kiện các cột: A76 là ``taskset -c 6``, A55 là ``taskset -c 0``, cả hai với ``OPENBLAS_NUM_THREADS=1`` và ``OMP_NUM_THREADS=1``. Cột BLAS mặc định không ghim lõi và không đặt biến môi trường, chỉ chạy 60 khung. p95 ở lõi A76 chỉ hơn trung vị tối đa 0.2 ms ở dòng tổng 5 người. Ở lõi A55, p95 của dòng 5 người là 18.769 ms (trung vị 5.310 ms) và dòng 34 người là 51.955 ms. Số track ra bằng số người và số mã số duy nhất chỉ hơn 1 hoặc 6 (6 mã cho 5 người, 35 cho 34, 66 cho 60), nên tracker nhận đúng hộp [T3 board, ``track_bench.py``].

Cột BLAS mặc định cho thấy chi phí không đến từ thuật toán: ``cProfile`` ở 34 người ghi 45.4 s trong ``numpy.linalg`` trên tổng 46.4 s, qua 3025 lần gọi cập nhật Kalman (khoảng 15 ms mỗi lần) [T3 board, ``cProfile``]. Đặt ``OPENBLAS_NUM_THREADS=1`` đưa ``update`` từ 447 ms xuống 4.4 ms. Nguyên nhân là nhiều luồng BLAS tranh nhau trên ma trận rất nhỏ là suy luận [SL], chưa tách riêng từng yếu tố. Ở lõi A76, tracker cộng hiển thị chiếm 5.6 ms (17% chu kỳ 33.3 ms của camera) với 34 người và 9.4 ms (28%) với 60 người. Ở lõi A55 cùng tải 34 người mất 51.2 ms, vượt chu kỳ camera, nên tracker phải chạy trên lõi A76 [SL, phép so sánh]. Chưa đo khi NPU, RGA và hậu xử lý chạy cùng lúc.

3. Đầu ra
=========

.. code:: text

    khung ảnh + hộp + mã số
       |
       v
    vẽ khung và nhãn (CPU)
       |
       +--> hiển thị: VOP -> HDMI hoặc DP   (hiện cả hai đều disconnected)
       |
       +--> lưu hoặc phát: mã hóa H.264
                 repo: libx264 qua PyAV, chạy trên CPU
                 phần cứng: VPU rkvenc (H.264, H.265) hoặc JPEG, repo chưa dùng

Hiển thị: VOP2 tại ``fdd90000``, cổng ``HDMI-A-1`` và ``DP-1`` [T3 board, ``dmesg``, ``/sys/class/drm``]. Datasheet ghi bộ mã hóa phần cứng:

   "Real-time H.265/H.264 video encoding" [T1 DS V1.7 tr.10]

Repo ghi video bằng ``VideoWriter`` lớp PyAV libx264 [Mã nguồn repo ``scripts/demo/common.py:154-155``]. Truyền luồng qua mạng (RTSP hoặc tương tự): repo chưa có.

Đo trên board với ảnh giả, 300 khung NV12 1920x1080 ở 30 khung/giây, chưa khóa xung, governor ``ondemand`` [T3 board, ``gst-launch-1.0``, ``ffmpeg``]:

.. list-table::
   :header-rows: 1
   :widths: 46 18 18 18

   * - Việc
     - Thời gian thực (s)
     - CPU người dùng (s)
     - Suy ra (khung/giây)
   * - GStreamer nguồn ``videotestsrc``, ``fakesink``
     - 3.005
     - 2.984
     - 100 (nguồn)
   * - GStreamer ``mpph264enc`` (VPU)
     - 3.046
     - 2.975
     - không chậm hơn nguồn
   * - GStreamer ``mpph265enc`` (VPU)
     - 3.047
     - 3.008
     - không chậm hơn nguồn
   * - ``ffmpeg`` nguồn ``testsrc2``, ``null``
     - 1.017
     - 0.886
     - 295 (nguồn)
   * - ``ffmpeg`` ``libx264 -crf 20`` (mặc định như repo)
     - 8.583
     - 41.812
     - 35
   * - ``ffmpeg`` ``libx264 -crf 20 -preset ultrafast``
     - 1.583
     - 8.413
     - 190

Nguồn ``videotestsrc`` tự tốn gần 3 s CPU nên che chi phí mã hóa của VPU: chỉ kết luận được VPU không chậm hơn 100 khung/giây ở 1080p, không đo được trần của nó. Nội dung ảnh giả và bitrate mặc định của ``mpph264enc`` khác ``crf 20`` nên không so được chất lượng. Cột suy ra là 300 chia thời gian thực [SL]. libx264 mặc định dùng khoảng 4.9 lõi CPU (41.812 chia 8.583) [SL].

4. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Điều chưa biết
     - Cần để xác minh
   * - ByteTrack với hộp thật từ model, và khi NPU, RGA chạy cùng lúc
     - Đo bằng hộp giả khi chạy riêng. ``ai/board/camera.py --track`` đã chạy cùng pipeline với 0 hộp (ByteTrack 0.190 ms) và với người đứng trong khung tối (trung bình 0.59 hộp mỗi khung, ByteTrack 0.727 ms trung vị, :doc:`07-chay-lien-tuc-tren-board`). Chưa đo với nhiều người trong phòng đủ sáng
   * - Trần mã hóa của VPU, và so với libx264 ở cùng chất lượng và nội dung thật
     - Dùng nguồn là tệp NV12 đã ghi sẵn thay cho ``videotestsrc``, đặt bitrate tương đương
   * - ``postprocess`` với khung camera thật có người
     - Đã đo với 34 hộp từ ảnh test phóng lên. Chưa đo với khung camera thật có người, cần người đứng trước camera
   * - Có cần theo dõi ở nhịp 30 khung/giây của camera không
     - Quyết định của người dùng về yêu cầu bài toán
