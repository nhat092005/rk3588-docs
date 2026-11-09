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
   2. Model INT8 mặc định có ``T_post`` 0.662 ms (trung vị, một context, khóa xung). Model tách đầu cần giải mã thêm 8.02 ms bằng numpy [T3 board, ``results/npu/throughput/thr_p3.json``, ``results/npu/operator_support/q2j_split.json``]. Trên khung camera thật không có hộp, ``postprocess`` mất 1.501 ms ở điều kiện không khóa xung. Khóa xung: 0.476 ms với 0 hộp và 2.043 ms với 34 hộp (ảnh test ppe5 phóng lên 1080p) [T3 board, ``board_pipeline_test.py``, ``board_pipeline_test2.py``].
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

Tham số ``track_high_thresh`` 0.25, ``track_low_thresh`` 0.1, ``new_track_thresh`` 0.25, ``track_buffer`` 30, ``match_thresh`` 0.8 lấy từ ``bytetrack.yaml`` của Ultralytics [Mã nguồn repo, ``.venv/lib/python3.12/site-packages/ultralytics/cfg/trackers/bytetrack.yaml``]. Tách hộp điểm cao và thấp ở ``byte_tracker.py`` dòng 316 và 317, ghép lần hai ở ``_second_association``. Lớp hiển thị dùng ``--smooth 5``, ``--vote 15``, ``--min-hits 3``, ``--hold 5`` mặc định [Mã nguồn repo ``scripts/demo/video/track.py:97-105``]. Đầu vào tracker là mọi hộp từ ``DET_CONF`` trở lên [Mã nguồn repo ``scripts/demo/video/track.py:3-5, 98``, ``scripts/demo/common.py:28``].

Đo ngày 2026-11-07 trên board, CPU, NPU, DDR khóa ``performance`` bằng ``lock_freq.sh``, 600 khung sau 30 khung khởi động [T3 board, ``track_bench.py``, ``build_trk_pkg.py``]. Mã tracker là ``byte_tracker.py``, ``basetrack.py``, ``kalman_filter.py``, ``matching.py``, ``stracks.py`` của Ultralytics 8.4.154, chép nguyên văn sang board. Board không có ``ultralytics`` và ``torch`` nên ``ultralytics.utils`` được thay bằng bản nhỏ (``LOGGER``, ``xywh2ltwh``, ``bbox_ioa`` trích nguyên từ mã gốc). ``lap`` 0.5.14 cài vào thư mục tạm bằng ``pip --target``. Lớp hiển thị là ``TrackDisplay`` chép từ ``track.py``. Dữ liệu là hộp người giả (chuyển động ngẫu nhiên, 10% khung điểm tụt xuống 0.12 đến 0.24, thêm hộp dương giả bằng một phần năm số người), không phải đầu ra của model. Trung vị ms:

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

Điều kiện: A76 là ``taskset -c 6``, A55 là ``taskset -c 0``, cả hai với ``OPENBLAS_NUM_THREADS=1`` và ``OMP_NUM_THREADS=1``. Cột BLAS mặc định không ghim và không đặt biến môi trường, chỉ chạy 60 khung. Số track ra bằng số người, số mã số duy nhất chỉ hơn 1 hoặc 6 (6 mã cho 5 người, 35 cho 34, 66 cho 60), nên tracker nhận đúng hộp [T3 board, ``track_bench.py``].

Chi phí ở cột BLAS mặc định không đến từ thuật toán: ``cProfile`` ở 34 người ghi 45.4 s trong ``numpy.linalg`` trên tổng 46.4 s, qua 3025 lần cập nhật Kalman (khoảng 15 ms mỗi lần) [T3 board, ``cProfile``]. ``OPENBLAS_NUM_THREADS=1`` đưa ``update`` từ 447 ms xuống 4.4 ms. Nguyên nhân là nhiều luồng BLAS tranh nhau trên ma trận rất nhỏ [SL]. Ở lõi A76, tracker cộng hiển thị chiếm 5.6 ms (17% chu kỳ 33.3 ms) với 34 người và 9.4 ms (28%) với 60 người. Ở lõi A55 cùng tải 34 người mất 51.2 ms, vượt chu kỳ camera, nên tracker phải chạy trên A76 [SL, phép so sánh]. Chưa đo khi NPU, RGA và hậu xử lý chạy cùng.

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

Nguồn ``videotestsrc`` tự tốn gần 3 s CPU nên che chi phí của VPU: chỉ kết luận được VPU không chậm hơn 100 khung/giây ở 1080p, không đo được trần. Nội dung giả và bitrate mặc định của ``mpph264enc`` khác ``crf 20`` nên không so được chất lượng. Cột suy ra là 300 chia thời gian thực [SL]. libx264 mặc định dùng khoảng 4.9 lõi CPU (41.812 chia 8.583) [SL]. Ở 4K UHD từ camera thật, ``rkvenc2`` ghi đủ nhịp thời gian thực (mục 3.1, quyết định 16 trong :doc:`../00-tong-quan/04-gioi-han-va-huong-phat-trien` mục 3.1).

3.1. Mã hóa 4K, H.264 và H.265
------------------------------

Đo ngày 2026-11-08. Khung NV12 3840x2160 lấy từ mainpath ``/dev/video11`` (cảnh trong nhà có người, 30 khung lặp 4 lần thành 120 khung), GStreamer ``mpph264enc`` và ``mpph265enc``, CBR, GOP 30, ghim lõi A76, xung khóa. Chất lượng là PSNR và SSIM so với khung gốc, giải mã bằng ffmpeg phần mềm [T3 board, ``experiments/camera/enc_rga_2026-11-08/``].

.. list-table::
   :header-rows: 1
   :widths: 20 20 20 20 20

   * - Bitrate đích
     - PSNR trung bình H.264
     - PSNR trung bình H.265
     - SSIM All H.264
     - SSIM All H.265
   * - 4 Mbps
     - 35.59 dB
     - 36.78 dB
     - 0.9050
     - 0.9141
   * - 8 Mbps
     - 36.40 dB
     - 37.44 dB
     - 0.9139
     - 0.9224
   * - 16 Mbps
     - 37.31 dB
     - 38.47 dB
     - 0.9248
     - 0.9347
   * - 32 Mbps
     - 38.47 dB
     - 39.62 dB
     - 0.9390
     - 0.9487

- Cùng bitrate, H.265 hơn H.264 từ 1.04 đến 1.18 dB PSNR trung bình (riêng kênh Y từ 1.22 đến 1.42 dB) và từ 0.008 đến 0.010 SSIM.
- H.265 ở một nửa bitrate xấp xỉ H.264: PSNR trung bình H.265 hơn từ 0.00 đến 0.37 dB, SSIM từ +0.0002 đến -0.0042 (kém ở hai cặp bitrate cao). Chỉ nên đọc là "gần tương đương ở khoảng nửa bitrate".
- Giới hạn: một cảnh, 30 khung lặp lại nên dự đoán theo thời gian chỉ trong 30 khung, cấu hình mặc định của plugin. Chưa đo cảnh nhiều chuyển động hay thiếu sáng.
- Chi phí như nhau. Từ tệp, 120 khung mất 3.5 đến 3.8 s (31.6 đến 34.4 khung/giây) với cả hai codec, nguồn không mã hóa 2.16 s nên chưa phải trần của bộ mã hóa. CPU 3.7 đến 4.0 s, phần lớn là thời gian hệ thống. Tải DDR (``dmc``) 17.9 đến 19.9% ở mọi ca kể cả ca không mã hóa, không phân biệt được giữa hai codec.
- Từ camera qua dma-buf, 300 khung: cả hai codec mất 10.28 đến 10.30 s (30 khung/giây thời gian thực), CPU 4.17 đến 4.22 s mỗi lần chạy (khoảng 41% một lõi). Tệp ra chỉ khoảng 4.9 MB cho 10 s dù đích 16 Mbps, tức CBR chưa đạt đích ở đường này. Chưa tìm nguyên nhân nên không dùng kích thước tệp ở ca này để so sánh.
- Hỗ trợ trình duyệt (caniuse, đọc 2026-11-08): H.264 "Supported" ở Chrome, Edge, Firefox, Safari, Chrome Android và Safari iOS ở các phiên bản hiện tại [Web caniuse.com/mpeg4]. H.265 chỉ hỗ trợ một phần: Chrome từ 107, Edge từ 79, Firefox tắt mặc định ở 121 đến 136 và hỗ trợ một phần từ 137, Safari từ 13 và Safari iOS từ 11 hỗ trợ đầy đủ [Web caniuse.com/hevc]. Trang ghi lý do: "hard for browsers to universally support HEVC because it is complex and expensive to license". Điều kiện chi tiết của mức "một phần" (giải mã phần cứng, hệ điều hành) chưa đọc được từ caniuse, một nguồn thứ ba nói Chrome và Edge phụ thuộc giải mã phần cứng, chưa kiểm.

Kết luận cho quyết định 16: chọn H.265, tiết kiệm khoảng một nửa dung lượng ở chất lượng gần tương đương [SL, từ số đo một cảnh]. Cái giá là trình duyệt chỉ hỗ trợ một phần, nên xem video bằng player. Cần phát trên trình duyệt thì chuyển sang H.264, bộ VPU làm được cả hai.

4. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Điều chưa biết
     - Cần để xác minh
   * - ByteTrack với hộp thật từ model, và khi NPU, RGA chạy cùng lúc
     - Đo bằng hộp giả khi chạy riêng. ``ai/board/app/camera.py --track`` đã chạy cùng pipeline với 0 hộp (ByteTrack 0.190 ms) và với người đứng trong khung tối (trung bình 0.59 hộp mỗi khung, ByteTrack 0.727 ms trung vị, :doc:`07-chay-lien-tuc-tren-board`). Chưa đo với nhiều người trong phòng đủ sáng
   * - Trần mã hóa của VPU (nguồn tệp ở 4K chỉ đạt 55 khung/giây không mã hóa, che trần), so với libx264 ở cùng chất lượng, và H.265 so với H.264 ở nhiều cảnh (chuyển động, thiếu sáng)
     - Nạp khung vào bộ đệm dma-buf dựng sẵn thay cho ``fdsrc``, đặt bitrate tương đương, thêm cảnh
   * - ``postprocess`` với khung camera thật có người
     - Đã đo với 34 hộp từ ảnh test phóng lên. Chưa đo với khung camera thật có người, cần người đứng trước camera
   * - Có cần theo dõi ở nhịp 30 khung/giây của camera không
     - Quyết định của người dùng về yêu cầu bài toán
