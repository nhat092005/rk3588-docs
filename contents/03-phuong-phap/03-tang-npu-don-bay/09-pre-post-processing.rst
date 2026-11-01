*******************
Pre/post-processing
*******************

.. admonition:: Trang này trả lời

   - CPU làm gì quanh NPU trong pipeline của dự án, và mỗi việc tốn bao nhiêu thời gian đã đo?
   - Vendor và các bài báo nói gì về tiền xử lý và hậu xử lý, và phần nào dự án chưa tìm thấy nguồn?
   - Đòn bẩy nào (chồng lấp, giải mã bằng C hoặc NEON, RGA, bỏ NMS) đưa FPS lên 60, cái nào đã đo?

.. admonition:: Tóm tắt

   1. Tiền xử lý trên CPU gồm resize ``INTER_LINEAR``, viền 114, BGR sang RGB, trả tensor ``(1, 640, 640, 3)`` uint8. Hậu xử lý gồm argmax lớp, lọc ``conf > 0.25``, NMS numpy (IoU 0.7, tối đa 300 hộp). Mean 0 và std 255 nằm trong model [Mã nguồn repo ``ai/board/common.py:64-79, 99-123``, ``ai/automation/build_recipe.py:64``].
   2. Model INT8 mặc định (``int8``) ở một context ``CORE_0``: ``T_pre`` 0.216 ms, ``T_npu`` 17.161 ms, ``T_post`` 0.662 ms (trung vị), 54.66 FPS. Tiền xử lý và hậu xử lý cộng lại 0.878 ms [T3 board, ``results/thr_p3.json``].
   3. Model tách đầu đưa phần giải mã box ra CPU: numpy tốn 8.02 ms (trung vị, 200 lần, đầu vào ngẫu nhiên). Tổng ở ``CORE_0`` là 13.07 + 8.02 = 21.09 ms so với 16.44 ms của ``int8h5`` nếu cùng một luồng [T3 board, ``results/q2j_split.json``].
   4. Vendor định nghĩa thời gian ứng dụng gồm pre, post và code logic, và khuyên tối ưu hoặc dùng phần cứng chuyên dụng khi nó chiếm tỷ lệ lớn [T1 UG232 tr.137]. Chữ NEON không có trong T1 tiếng Anh đã tìm.
   5. P1 chồng lấp giải mã bằng pipeline: ĐO, 65.99 FPS ở một context ``CORE_0`` (:doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`). P2 giải mã bằng C hoặc NEON: không cần theo cách đọc thông lượng của mục tiêu 60 FPS ở cấu hình này (cách đọc thời gian mỗi khung chưa xét), chưa đo. P3 RGA: chưa thử. P4 bỏ NMS: ngoài phạm vi.
   6. Chưa biết: thời gian NMS riêng trên RK3588, giải mã trên ảnh thật ở model tách đầu trong pipeline, thứ tự đầu ra của pipeline, thời gian mỗi khung ở nhịp 60 FPS.

Kiến thức nền ở :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`. Kết quả FPS của các đòn bẩy ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không giải thích lại vì sao đầu ra của YOLOv8 trên RKNN là tensor thô ``[1, 4 + nc, 8400]`` cần lọc và NMS trên CPU, và không giải thích lớp ``_NormalizeCoords``. Phần đó ở :doc:`../../02-nen-tang-rk3588/05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`. Pipeline suy luận nói chung và hệ quả khi triển khai ở :doc:`../../01-kien-thuc-nen/01-nen-tang-ai/06-huan-luyen-va-suy-luan` (mục 3 và 5). Zero-copy và đường sao chép ở :doc:`06-memory-copy`, layout đầu vào ở :doc:`03-tensor-layout`, tách đầu ở :doc:`07-compiler-optimization` (K2 và K3) và :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`.

Trang chỉ ghi điều dự án cần cho quyết định: CPU làm gì, tốn bao nhiêu, đòn bẩy nào đã đo. Mục tiêu FPS là 60 (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Người dùng chưa xác nhận đó là một luồng hay tổng nhiều luồng, thông lượng hay thời gian mỗi khung. Mục 5 ghi cả hai cách đọc.

2. Việc CPU làm trong repo
==========================

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Khâu
     - Nội dung
     - Nguồn
   * - Tiền xử lý
     - Resize ``cv2.INTER_LINEAR`` về cạnh dài 640, ``copyMakeBorder`` viền giá trị 114, BGR sang RGB, trả ``(1, 640, 640, 3)`` uint8
     - [Mã nguồn repo ``ai/board/common.py:64-79``]
   * - Chuẩn hóa
     - ``mean_values`` 0, ``std_values`` 255 đặt lúc build, đầu vào uint8 vào thẳng ``rknn.inference``
     - [Mã nguồn repo ``ai/automation/build_split.py:47``]
   * - Hậu xử lý (model INT8 mặc định)
     - Argmax lớp, lọc ``conf > 0.25``, giữ tối đa ``MAX_NMS`` 30000 ứng viên, NMS numpy với IoU 0.7, tối đa ``MAX_DET`` 300
     - [Mã nguồn repo ``ai/board/common.py:24-27, 99-123``]
   * - Giải mã (model tách đầu)
     - Hai đầu ra thô (hộp DFL và điểm số), numpy làm softmax DFL, tọa độ và sigmoid, không lọc confidence. ``postprocess_raw`` chỉ gọi ``decode_split`` khi ``split=True``
     - [Mã nguồn repo ``ai/board/split_decode.py``, ``ai/board/common.py`` hàm ``postprocess_raw``]

Model chuẩn giải mã box trong đồ thị NPU nên hậu xử lý của nó bắt đầu từ tensor đã giải mã. Model tách đầu bỏ phần đó khỏi đồ thị (:doc:`07-compiler-optimization` K2), nên CPU phải làm thêm phép giải mã trước các bước còn lại. Trên cả hai model, ``T_post`` đo bằng ``postprocess_raw`` [Mã nguồn repo ``ai/board/bench_throughput_rep.py``].

Về chuẩn hóa, vendor ghi các giá trị này dùng trong lượng tử hóa và ảnh không cần chuẩn hóa lại ở C API: "These values are used in the quantification process, and the images no longer need to be averaged and normalized during the C API inferencing to reduce deployment time." [T1 UG232 tr.22]. UG232 cũng viết thứ tự trừ mean rồi chia std trước khi đưa vào mô hình [T1 UG232 tr.158]. Vendor không nói rõ phép này chạy ở đâu lúc suy luận: chưa tìm thấy ở tr.22, tr.69 và tr.158. Khi ``pass_through=1``, "NPU does not perform any mean/std processing and layout conversion." [T1 UG232 tr.69], và harness C của dự án bị từ chối ở chế độ này (:doc:`06-memory-copy` mục 3).

3. Thời gian đã đo
==================

3.1. Model chuẩn, harness P3
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 15 15 15 15

   * - Cấu hình (trung vị, ms)
     - ``T_pre``
     - ``T_npu``
     - ``T_post``
     - FPS
   * - T1: một context ``CORE_0``
     - 0.216
     - 17.161
     - 0.662
     - 54.66
   * - T4: hai context
     - 0.321
     - 18.24
     - 0.695
     - 102.0
   * - T5: ba context (S2)
     - 0.457
     - 19.526
     - 0.754
     - 141.18
   * - T6: S3 pipeline
     - 1.084
     - 20.138
     - 1.28
     - 147.39

Nguồn: [T3 board, ``results/thr_p3.json``, trường ``configs``]. Ở một context, ``T_pre`` cộng ``T_post`` là 0.878 ms trong tổng khoảng 18.04 ms (tính từ ba trung vị, xấp xỉ 4.9%). Khi nhiều context chạy cùng lúc, ``T_pre`` và ``T_post`` tăng (0.216 lên 1.084 ms và 0.662 lên 1.28 ms ở T6), mô tả của phép đo, nguyên nhân chưa biết. Bảng đầy đủ và điều kiện P3 ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 2 đến 5. ``T_pre`` đo từng khung bằng ``time.perf_counter`` và gộp cả letterbox, không tách riêng từng bước [Mã nguồn repo ``ai/board/bench_throughput_rep.py``].

3.2. Model tách đầu, giải mã CPU
--------------------------------

Giải mã numpy đo riêng: trung vị 8.02 ms, p95 8.246 ms, nhỏ nhất 7.88 ms qua 200 lần, đầu vào ngẫu nhiên (``default_rng(0)``, hộp ``N(0,4)`` hình ``(1,64,8400)``, điểm ``N(-3,3)`` hình ``(1,5,8400)``), tần số và CPU khóa [T3 board, ``results/q2j_split.json`` trường ``decode``, ``ai/board/bench_decode.py``]. Trên đầu ra thật của hai model tách đầu, trung vị giải mã là 8.261 ms (INT8) và 8.222 ms (FP16), số anchor giữ lại là 14805 và 15719. Số này đo trong lúc chấm và chưa ghim CPU [T3 board, ``results/q2j_split.json`` trường ``s4``].

Tổng nếu cùng một luồng: ở ``CORE_0`` là 13.07 + 8.02 = 21.09 ms so với 16.4425 ms của ``int8h5`` (chênh +4.6475 ms). Ở ``CORE_0_1_2`` là 12.557 + 8.02 = 20.577 ms so với 15.928 ms. Các so sánh này mang nhãn "chưa kết luận" vì ``all_realized`` là false (điều kiện ``int8`` ở ``CORE_0`` không thực hiện đúng) [T3 board, ``results/q2j_split.json``, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2].

Trong harness E2, khi giải mã nằm cùng luồng với hậu xử lý (điều kiện B), ``T_post`` trung vị là 8.94 ms và FPS là 42.05, thấp hơn ``int8h5`` tuần tự (54.79). Khi tách thành luồng riêng (điều kiện C), ``T_post`` là 11.61 ms trong lúc ``T_npu`` là 15.04 ms [T3 board, ``results/q2f_fps.json``, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 4].

4. Vendor và bài báo
====================

.. list-table::
   :header-rows: 1
   :widths: 14 56 30

   * - Tầng
     - Nội dung
     - Thẻ
   * - T1
     - Demo YOLOv5 chuyển hậu xử lý sang CPU: "Due to hardware limitations, the demo model moves the post-processing part of the yolov5 model to the cpu implementation by default."
     - [T1 EX ``rknn_yolov5_demo/README.md:13``]
   * - T1
     - Demo có hai nhánh: ``printf("resize image by rga\n");`` (RGA resize trực tiếp) và ``printf("resize image with letterbox\n");`` (hàm CPU ``letterbox(cv::Mat)``)
     - [T1 EX ``rknn_yolov5_demo/src/main.cc:265-280``, ``include/preprocess.h:12``]
   * - T1
     - Ví dụ zero-copy có ``preprocess_rga()`` (giao diện RGA dùng bộ nhớ do NPU cấp) và "postprocess_cpu()represents the CPU implementation of postprocessing."
     - [T1 UG232 tr.67]
   * - T1
     - Thời gian ứng dụng: "Typically, it includes pre-processing, post-processing, and the execution time of logical code."
     - [T1 UG232 tr.137]
   * - T1
     - Khuyến nghị khi chiếm tỷ lệ lớn: "If the application time is significantly high in proportion to the overall time, besides optimizing and simplifying the code, user can try to accelerate some operations using dedicated hardware."
     - [T1 UG232 tr.137]
   * - T1
     - NPU load thấp: "If the queried load is low, it indicates that the NPU is waiting for task submissions for a longer duration."
     - [T1 UG232 tr.137]
   * - T1
     - Sau khi gỡ subgraph không hỗ trợ (ví dụ ``NonMaxSuppression``): "The removed subgraphs are processed separately on the CPU side."
     - [T1 UG232 tr.168]
   * - T2
     - Bài đo YOLO11 trên RK3566 (Orange Pi 3B): "In the NPU configuration, inference ran on the RK3566 NPU (device), whereas preprocessing and postprocessing ran on the CPU (host)"
     - [T2 Limaran tr.4]
   * - T2
     - Cùng bài, Bảng 1(b), YOLO11n ảnh 1: tiền xử lý 35.90, suy luận 266.10, hậu xử lý 12.90, tổng 314.90 ms (số của bài trên RK3566, không phải của dự án)
     - [T2 Limaran tr.6]
   * - T2
     - YOLO26: "Ultralytics reports that YOLO26 achieves an inference speedup of approximately 43% on CPU targets compared to standard NMS-based baselines [13]."
     - [T2 Chakrabarty 2026 tr.7]
   * - T2
     - YOLO26: "This end-to-end NMS-free inference (Figure 3) eliminates post-processing overhead and accelerates deployment."
     - [T2 Sapkota 2025 tr.5]
   * - T2
     - YOLOv6 nêu thời gian hậu xử lý giảm nhờ đầu anchor-free: "The time cost of its post-processing is substantially reduced."
     - [T2 Li 2022 tr.4]
   * - T2
     - EDGE định nghĩa latency là thời gian đầu cuối mỗi khung tại NPU runtime, bài không nói rõ có tính pre và post: "we use the term latency (or equivalently, inference time) to denote the end-to-end per-frame processing time measured at the NPU runtime."
     - [T2 EDGE tr.2]

Hai ghi chú. Số 43% là số của Ultralytics được bài dẫn lại, đo trên CPU, không phải số trên RK3588 hay trên NPU. Bài EDGE nêu các ngưỡng 25, 30, 50 và 60 FPS cho YOLO nano chạy 21 đến 30 ms ở một lõi NPU: "Nano variants consistently operated between 21–30 ms, sufficient for 30 FPS" [T2 EDGE tr.5]. Tài liệu Ultralytics về RKNN ghi "Inference time does not include pre/post-processing." (tài liệu của bên thứ ba, ngoài ba tầng nguồn của dự án) [Mã nguồn repo ``docs/_assets/pdf/papers/09_yolo_architecture/ultralytics_docs_integrations_rockchip-rknn.txt:194``].

Chưa tìm thấy: chữ NEON trong UG232, API Reference, Operator List, Quick Start và mã demo YOLOv5 (grep không phân biệt hoa thường). Mô tả pre hay post chạy trên NPU: T1 không có, chỉ có câu về mean và std ở UG232 tr.69, và không có câu nào nói NMS chạy trên NPU. Chữ ``letterbox`` không có trong UG232 hay API Reference, chỉ trong demo YOLOv5. Phân bổ thời gian pre và post trên RK3588 ở T2: không có, bài EDGE không tách stage và bài DAHD không có số pre và post.

5. Đòn bẩy
==========

Nhãn: ĐO (số T3 của dự án), NGUỒN, CHƯA BIẾT. Các nhãn chưa phải cổng quyết định, ngưỡng số mới chưa duyệt, giao thức P3 đã duyệt (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).

.. list-table::
   :header-rows: 1
   :widths: 8 24 12 56

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng
   * - P1
     - Chồng lấp giải mã bằng pipeline (một luồng pre, một NPU, một post)
     - ĐO
     - Model tách đầu ở ``CORE_0``: 65.99 FPS (C), so với 42.05 FPS khi giải mã cùng luồng (B) và 54.79 FPS của ``int8h5`` tuần tự (A). Thêm luồng post (D, 65.74) hay ba lõi (E, 68.21) không phân biệt được với C. Pipeline không giúp ``int8h5`` (F, 56.62, không phân biệt được với A). CPU tiến trình khoảng 100% ở C so với 24% ở A [T3 board, ``results/q2f_fps.json``, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 4]
   * - P2
     - Giải mã bằng C hoặc NEON thay numpy
     - Chưa đo
     - Thí nghiệm E3 không chạy vì điều kiện kích hoạt viết trước không xảy ra (C đạt 60 FPS và ``T_post`` 11.61 ms nhỏ hơn ``T_npu`` 15.04 ms). Kết luận: không cần theo cách đọc thông lượng của mục tiêu 60 FPS ở cấu hình này, cách đọc thời gian mỗi khung chưa được xét. Lợi ích khi cần giảm CPU hoặc vượt 60 FPS: chưa biết [:doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 6]
   * - P3
     - RGA cho tiền xử lý
     - NGUỒN, chưa thử
     - Demo YOLOv5 của vendor có nhánh RGA resize và ví dụ zero-copy có ``preprocess_rga()`` [T1 EX ``main.cc:265-280``, T1 UG232 tr.67]. Repo không dùng RGA, ``T_pre`` hiện là 0.216 ms ở một context (mục 3.1), nên lợi ích FPS ở cấu hình này: chưa biết
   * - P4
     - Bỏ NMS (model NMS-free như YOLO26)
     - NGUỒN, ngoài phạm vi
     - Bài T2 nói bỏ NMS giảm overhead hậu xử lý, số 43% là của Ultralytics trên CPU (mục 4). Dự án giữ YOLOv8n nên đòn bẩy này đổi kiến trúc và nằm ngoài phạm vi. Số NMS trên RK3588: chưa biết

Hai điều rút ra từ số đo. Một, ở model INT8 mặc định tiền xử lý và hậu xử lý chỉ chiếm khoảng 4.9% thời gian một khung (mục 3.1), nên phần lớn FPS nằm ở ``T_npu``. Hai, giải mã CPU của model tách đầu là phần CPU lớn nhất đã đo (8.02 ms) và P1 là cách đã đo để che nó. Hai điều này là mô tả của phép đo, không phải cơ chế.

**Đọc theo thông lượng** (mặc định của :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8): P1 đạt 60 FPS với một context (65.99 FPS), P2 và P3 không cần. **Đọc theo thời gian mỗi khung** (16.67 ms): không điều kiện nào của P1 đạt, vì tổng ba giai đoạn của C là 27.6 ms (tổng trung vị từng giai đoạn dưới tranh chấp, không phải đo đầu cuối trực tiếp và không phải cực tiểu). Thời gian đầu cuối đo trong pipeline bão hòa lớn hơn 128 ms nhưng gồm chờ hàng đợi nên chỉ là cận trên. Thời gian mỗi khung ở nhịp 60 FPS chưa đo. Theo cách đọc này P2 và P3 mới có thể liên quan, vì giảm ``T_post`` hay ``T_pre`` rút ngắn tổng ba giai đoạn, nhưng mức rút ngắn đủ để đạt 16.67 ms: chưa biết (``T_npu`` một mình đã 15.04 ms ở C).

6. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 44 16 40

   * - Câu hỏi
     - Trạng thái
     - Đã tìm gì
   * - Thời gian NMS riêng trên RK3588
     - chưa biết
     - Không có số trong T1, T2, T3. Chỉ có ``T_post`` gộp (0.662 ms) và giải mã 8.02 ms
   * - Thời gian letterbox riêng
     - chưa biết
     - Gộp trong ``T_pre``, repo không đo riêng
   * - Giải mã trên ảnh thật trong pipeline E2
     - chưa biết
     - 8.02 ms đo trên dữ liệu ngẫu nhiên. Số trên đầu ra thật 8.261 ms đo trong lúc chấm, chưa ghim
   * - Thứ tự đầu ra của pipeline
     - chưa kiểm
     - Giữ theo cách xây dựng (một luồng mỗi giai đoạn, hàng đợi FIFO), harness không kiểm. Điều kiện D có hai luồng post nên có thể đảo
   * - Thời gian mỗi khung ở nhịp 60 FPS
     - chưa đo
     - :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps` mục 5
   * - Lợi ích của NEON hoặc C, và của RGA
     - chưa biết
     - NEON không có trong T1 tiếng Anh, RGA chỉ có ví dụ vendor, dự án chưa thử
   * - Mean và std chạy ở đâu lúc suy luận
     - chưa biết
     - UG232 tr.22, tr.69, tr.158 không nói rõ
   * - Cách hiểu mục tiêu 60 FPS
     - chưa xác nhận
     - :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8

7. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, UG232 tr.22, 67, 69, 137, 158, 168), ví dụ demo ``3rdparty/rknn-toolkit2/rknpu2/examples/rknn_yolov5_demo/`` (``README.md:13``, ``src/main.cc:265-280``, ``include/preprocess.h:12``, ``src/preprocess.cc:17``).
- T2: Limaran (``rk3566_npu_yolo11_2026limaran.pdf`` tr.4, 6), Chakrabarty (``yolo26_nmsfree_2026chakrabarty.pdf`` tr.7), Sapkota (``yolo26_arch_2025sapkota.pdf`` tr.5), Li 2022 (``yolov6_hwfriendly_2022li.pdf`` tr.4), EDGE (``edgesoc_benchmark_2026kong.pdf`` tr.2, 5).
- T3: ``results/thr_p3.json``, ``results/q2j_split.json``, ``results/q2f_fps.json``.
- Mã nguồn repo: ``ai/board/common.py:24-27, 64-79, 99-123``, ``ai/board/split_decode.py``, ``ai/board/bench_decode.py``, ``ai/board/bench_throughput_rep.py``, ``ai/automation/build_split.py:47``, ``ai/automation/build_recipe.py:64``.
- Trang liên quan: :doc:`03-tensor-layout`, :doc:`06-memory-copy`, :doc:`07-compiler-optimization`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
