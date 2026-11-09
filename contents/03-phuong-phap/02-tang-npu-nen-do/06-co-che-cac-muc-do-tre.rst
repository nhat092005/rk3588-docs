*********************
Cơ chế các mức độ trễ
*********************

.. admonition:: Trang này trả lời

   - Ở mỗi vị trí (CPU của tiến trình đo, CPU nhận ngắt NPU), thời gian của một lần ``rknn_run`` gồm những phần nào, và phần nào mang chênh lệch giữa mức nhanh, mức giữa và mức chậm?
   - Tắt ``cpu-sleep`` ở một CPU, hoặc hạ xung nhịp CPU4, có làm mất phần chênh lệch đó không?
   - Nhịp gọi khoảng 0.22 giây của ``eval_perf`` có giải thích chênh lệch giữa đường ``eval_perf`` và đường C API không?

.. admonition:: Tóm tắt

   - Mỗi lần chạy được tách bằng ftrace thành bốn phần: C (tiến trình đo đang chạy trên CPU), N (từ lúc tiến trình ngủ chờ NPU tới lúc trình xử lý ngắt NPU bắt đầu), D (từ lúc trình xử lý ngắt bắt đầu tới lúc tiến trình chạy lại), P (bị chiếm CPU khi đang sẵn sàng). Bốn phần cộng lại khớp thời gian đo ở 100% số lần chạy của cả 28 khối X1 và X2.
   - Khi chỉ dời ngắt NPU từ CPU4 sang CPU0 (ứng dụng ở CPU4 hoặc ở CPU1), phần tăng nằm chủ yếu ở N (93% và 92% chênh lệch ở nửa 1). Tắt ``cpu-sleep`` riêng ở CPU0 làm phần tăng ở N giảm từ 2.59 xuống 0.15 ms (nhãn "làm mất" theo quy tắc viết trước).
   - Khi chỉ dời ứng dụng từ CPU4 sang CPU1 (ngắt ở CPU4), phần tăng chia giữa C và D. D mỗi ngắt tăng từ trung vị 2 µs lên 48 µs. Tắt ``cpu-sleep`` ở CPU1 làm phần tăng ở D giảm từ 1.95 xuống 0.39 ms, nhưng tỉ lệ còn lại là 0.200 và 0.201, vượt ngưỡng 0.2 ở một nửa, nên theo quy tắc là "chưa kết luận".
   - Hạ CPU4 về 1.8 GHz làm C tăng 1.58 lần, nằm giữa tỉ lệ xung nhịp 1.25 và tỉ lệ C giữa CPU1 và CPU4 (2.33), nên "chưa kết luận" về việc xung nhịp có giải thích phần C hay không.
   - Chạy C API với nhịp nghỉ 220 ms (X3) chỉ làm thời gian đổi 0.01 đến 0.25 ms, không tiến về thời gian ``eval_perf``. Theo quy tắc là "chưa kết luận" (một ô có f = 0.34, vượt ±0.25).
   - Đây là phát biểu về thời gian và vị trí, kèm kết quả can thiệp. Cơ chế phần cứng vẫn chưa biết. Mọi số đo có trace kèm lưu ý "đo khi có trace" (ô A lệch -2.45 ms so với E2d, các ô ghim lệch tối đa 0.61 ms).

Trang này là phần đo cơ chế của nhóm. Kết quả vị trí (E2 đến E2e) nằm ở :doc:`05-thu-ghim-cpu-va-ngat`, các mức độ trễ ở :doc:`04-cac-muc-do-tre`. Quy ước nhãn ở :doc:`04-cac-muc-do-tre`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cách đo
==========

X1 và X2 chạy trên đường C API (``rknn_perf_bench``, ``CORE_0``, ảnh đầu vào toàn 0), ``irqbalance`` dừng, tần số khóa, ftrace với đồng hồ ``mono`` (cùng đồng hồ với cột ``t_us`` của CSV), bộ đệm tối thiểu 32768 KB mỗi CPU. Sự kiện ghi: ``irq_handler_entry`` và ``irq_handler_exit`` lọc theo ngắt 36, ``sched_wakeup`` và ``sched_switch`` lọc theo luồng ``rknn_perf_bench``, ``cpu_idle`` trên mọi CPU. Một phép thử 7 lần chạy (chỉ ghi tên luồng, không ghi thời gian) cho thấy ``rknn_perf_bench`` là luồng duy nhất được chuyển vào CPU, khoảng 63 lần mỗi lần chạy, khớp 63 ngắt NPU mỗi lần chạy. Mỗi khối 50 lần làm nóng rồi 300 lần đo, nửa 2 là thứ tự đảo ngược của nửa 1.

Cách tách một lần chạy (định nghĩa trong ``experiments/npu/latency/onboard_x1/rule.txt``, viết trước dữ liệu): C là thời gian luồng ở trên CPU. Khi luồng ngủ (trạng thái S hoặc D) rồi được chuyển vào lại, ngắt kết thúc khoảng chờ là ngắt 36 cuối cùng trong khoảng đó: N là từ lúc ngủ tới ngắt đó, D là từ ngắt đó tới lúc chạy lại. P là thời gian bị chiếm CPU khi đang sẵn sàng (trạng thái R). Khối thực hiện đúng khi ứng dụng và ngắt ở đúng CPU (ít nhất 99%), bốn phần cộng lại khớp thời gian đo trong 2% ở ít nhất 95% số lần chạy, và trace không mất sự kiện nào. Các ngưỡng 0.8, 1.2, 0.9, 0.1, 2% và 95% là ngưỡng mới chọn cho quy tắc này, chưa qua người dùng duyệt. X2 thêm kiểm can thiệp: file ``state1/disable`` và governor của ``policy4`` đọc lại trước và sau mỗi khối, và trong trace tỉ lệ lần CPU đích vào ``cpu-sleep`` phải không quá 0.01.

2. X1: thời gian tăng nằm ở phần nào
====================================

.. list-table::
   :header-rows: 1
   :widths: 12 9 9 9 9 9 14 15 15

   * - Ô (ứng dụng, ngắt)
     - T (ms)
     - C (ms)
     - N (ms)
     - D (ms)
     - P (ms)
     - D mỗi ngắt, trung vị (µs)
     - Tỉ lệ CPU ứng dụng vào cpu-sleep khi chờ
     - Tỉ lệ CPU ngắt ở cpu-sleep khi ngắt tới
   * - A
     - 18.048
     - 0.905
     - 16.797
     - 0.342
     - 0.000
     - 6
     - 0.00
     - 0.51
   * - a4i4
     - 16.418
     - 0.901
     - 15.375
     - 0.143
     - 0.000
     - 2
     - 0.00
     - 0.00
   * - a4i0
     - 19.169
     - 0.907
     - 17.928
     - 0.324
     - 0.000
     - 5
     - 0.00
     - 0.98
   * - a1i4
     - 19.360
     - 2.109
     - 15.159
     - 2.093
     - 0.000
     - 48
     - 0.63
     - 0.00
   * - a0i0
     - 19.267
     - 2.061
     - 16.632
     - 0.576
     - 0.000
     - 9
     - 0.52
     - 0.52
   * - a1i0
     - 22.155
     - 2.123
     - 17.754
     - 2.342
     - 0.000
     - 49
     - 0.68
     - 1.00

Số là trung bình của trung vị hai khối (một khối mỗi nửa). Cột "cpu-sleep" là trung vị theo lần chạy của tỉ lệ các khoảng chờ mà CPU tương ứng vào trạng thái ``cpu-sleep`` (mô tả, R2 không dùng để kết luận).

Theo quy tắc R1 (so từng cặp với một ô, ở cả hai nửa, phần nào chiếm 0.8 đến 1.2 chênh lệch thời gian):

.. list-table::
   :header-rows: 1
   :widths: 16 14 30 14 26

   * - Cặp
     - Chênh T nửa 1 (ms)
     - Tỉ lệ C, N, D, P nửa 1
     - Chênh T nửa 2 (ms)
     - Kết luận theo quy tắc
   * - a1i0 vs a4i4
     - +5.787
     - C 0.21, N 0.41, D 0.38, P 0.00
     - +5.686
     - chưa kết luận
   * - a0i0 vs a4i4
     - +2.844
     - C 0.41, N 0.44, D 0.15, P 0.00
     - +2.855
     - chưa kết luận
   * - a4i0 vs a4i4
     - +2.803
     - C 0.00, N 0.93, D 0.07, P 0.00
     - +2.699
     - chênh lệch thời gian chạy của cặp này nằm chủ yếu ở phần N
   * - a1i4 vs a4i4
     - +2.968
     - C 0.41, N -0.07, D 0.66, P 0.00
     - +2.915
     - chưa kết luận
   * - a1i0 vs a1i4
     - +2.820
     - C 0.00, N 0.92, D 0.08, P 0.00
     - +2.771
     - chênh lệch thời gian chạy của cặp này nằm chủ yếu ở phần N

- Hai cặp chỉ dời ngắt (``a4i0`` so với ``a4i4``, ``a1i0`` so với ``a1i4``): phần tăng nằm chủ yếu ở N. Trong hai ô ``a4i0`` và ``a1i0`` (ngắt ở CPU0, ứng dụng ở CPU khác), CPU0 đang ở ``cpu-sleep`` khi ngắt tới ở 0.96 đến 1.00 số lần, còn khi ngắt ở CPU4 là 0 (mô tả).
- Cặp chỉ dời ứng dụng (``a1i4`` so với ``a4i4``): chênh lệch chia giữa C (0.41) và D (0.66), không phần nào đạt 0.8, nên "chưa kết luận". Ô chậm ``a1i0`` mang cả hai loại tăng.
- R2: tỉ lệ CPU ứng dụng vào ``cpu-sleep`` khi chờ ở ô ``a1i0`` là 0.68 ở cả hai khối, dưới ngưỡng 0.9, nên chỉ báo số.
- R3: trung vị T có trace so với E2d: A 18.05 so với 20.50, a1i0 22.15 so với 21.54, a0i0 19.27 so với 18.82, a4i0 19.17 so với 18.86, a1i4 19.36 so với 19.04, a4i4 16.42 so với 16.31 ms. Ô A lệch quá 1.25 ms (ô A không ghim, dao động mạnh ở mọi thí nghiệm), nên theo quy tắc mọi phát biểu của X1 kèm lưu ý "đo khi có trace, mức có thể khác khi không trace".

3. X2: can thiệp từng yếu tố
============================

X2 dùng cùng cách đo, thêm các ô can thiệp: ``a4i0s`` (tắt ``cpu-sleep`` riêng ở CPU0), ``a1i4s`` (tắt riêng ở CPU1), ``a1i0s`` (tắt ở CPU0 và CPU1), ``a4i4f`` (CPU4 và CPU5 ở 1.8 GHz với governor ``userspace``). Cả 16 khối thực hiện đúng, kể cả kiểm can thiệp (tỉ lệ CPU đích vào ``cpu-sleep`` trong trace bằng 0 ở mọi khối có tắt).

.. list-table::
   :header-rows: 1
   :widths: 14 12 12 12 12 18

   * - Ô
     - T (ms)
     - C (ms)
     - N (ms)
     - D (ms)
     - D mỗi ngắt, trung vị (µs)
   * - a4i4
     - 16.407
     - 0.899
     - 15.369
     - 0.139
     - 2
   * - a4i0
     - 19.206
     - 0.909
     - 17.972
     - 0.324
     - 5
   * - a4i0s
     - 16.675
     - 0.903
     - 15.511
     - 0.261
     - 4
   * - a1i4
     - 19.353
     - 2.100
     - 15.155
     - 2.094
     - 47
   * - a1i4s
     - 17.544
     - 1.810
     - 15.203
     - 0.531
     - 8
   * - a4i4f
     - 18.563
     - 1.421
     - 16.824
     - 0.320
     - 6
   * - a1i0
     - 22.085
     - 2.121
     - 17.748
     - 2.324
     - 49
   * - a1i0s
     - 17.748
     - 1.805
     - 15.358
     - 0.584
     - 9

Kết luận theo quy tắc viết trước (``experiments/npu/latency/onboard_x2/rule.txt``):

- S1 (ngắt ở CPU0): phần tăng ở N so với ``a4i4`` là 2.59 và 2.61 ms ở hai nửa, còn 0.15 và 0.14 ms khi tắt ``cpu-sleep`` ở CPU0. Nhãn: **làm mất**.
- S2 (ứng dụng ở CPU1): phần tăng ở D là 1.95 và 1.96 ms, còn 0.39 và 0.39 ms khi tắt ``cpu-sleep`` ở CPU1. Tỉ lệ còn lại 0.200 và 0.201, ngưỡng là 0.2 và nhãn cần cả hai nửa cùng không vượt, nên nhãn là **chưa kết luận**. Ngưỡng không sửa sau khi thấy dữ liệu.
- S3 (xung nhịp): C của ``a4i4f`` gấp 1.58 và 1.58 lần ``a4i4``, trong khi tỉ lệ xung nhịp là 1.25 và C của ``a1i4`` gấp 2.33 lần. Nhãn: **chưa kết luận**. Phép tách này chỉ làm được một chiều vì cụm nhỏ không lên được 2.256 GHz. Ở ``a4i4f`` CPU nhận ngắt cũng bị hạ xung nhịp, nên N và D cũng đổi (mô tả, S3 chỉ đọc C).
- S4 (mô tả): T của ``a1i0s`` là 17.75, 17.75 ms so với 22.06, 22.11 ms của ``a1i0`` và 16.41, 16.41 ms của ``a4i4``.

Theo bảng nhãn ghi trước trong quy tắc: độ trễ từng ngắt (U1a) và nơi thời gian tăng (U2) là "trả lời bằng đo". Câu "mức chậm mất khi tắt ``cpu-sleep`` ở CPU tương ứng" (U1b) cần cả S1 và S2 cùng "làm mất", nên là "vẫn chưa biết". Tách xung nhịp khỏi vị trí (U3) là "vẫn chưa biết". Cơ chế phần cứng (vì sao thoát ``cpu-sleep`` làm chậm ngắt và đánh thức) không được đo và vẫn chưa biết. Từ khóa đề xuất để tìm tài liệu: "ARM cpuidle exit latency interrupt latency RK3588", "PSCI CPU suspend wakeup latency Cortex-A55", "NPU interrupt affinity latency embedded Linux".


4. X3: nhịp gọi và chênh lệch giữa hai đường đo
===============================================

Đường ``eval_perf`` (E2e) và đường C API (E2d) lệch nhau từ -1.20 đến 0.29 ms ở cùng ô. Các lần gọi ``eval_perf`` cách nhau khoảng 0.22 giây, còn C API chạy liên tiếp. X3 chạy lại C API ở sáu ô của E2e, mỗi ô một khối liên tiếp (B) và một khối nghỉ 220 ms sau mỗi lần chạy (G, chu kỳ khoảng 240 ms), đảo thứ tự ở nửa 2. Một ô chỉ được xét khi B còn khớp E2d trong 0.25 ms. Tỉ số f = (G - B) / (E - B), với E là trung vị ``eval_perf`` của ô ở E2e. Quy tắc ``experiments/npu/latency/onboard_x3/rule.txt`` (ngưỡng 0.25 ms, 0.5, 1.5 và 0.25 là số mới, chưa qua người dùng duyệt).

.. list-table::
   :header-rows: 1
   :widths: 10 16 16 18 14 10

   * - Ô
     - B, liên tiếp (ms)
     - G, nghỉ 220 ms (ms)
     - E, eval_perf ở E2e (ms)
     - R, E2d (ms)
     - f
   * - a4i4
     - 16.312
     - 16.323
     - 16.587
     - 16.309
     - 0.04
   * - a0i0
     - 18.908
     - 19.081
     - 17.852
     - 18.818
     - -0.16
   * - a4i0
     - 18.711
     - 18.862
     - 19.150
     - 18.863
     - 0.34
   * - a0i4
     - 18.790
     - 19.009
     - 17.874
     - 18.743
     - -0.24
   * - a1i0
     - 21.577
     - 21.823
     - 20.343
     - 21.544
     - -0.20
   * - a1i4
     - 19.055
     - 19.269
     - 17.851
     - 19.043
     - -0.18

Cả 24 khối thực hiện đúng và cả sáu ô đều xét được. Theo quy tắc: **chưa kết luận**, vì f nằm trong khoảng ±0.25 ở 5 trên 6 ô nhưng ô ``a4i0`` là 0.34. Mô tả: giãn nhịp làm thời gian C API đổi từ 0.01 đến 0.25 ms, không tiến về thời gian ``eval_perf`` ở các ô có ứng dụng ở CPU0 hoặc CPU1 (ở đó ``eval_perf`` thấp hơn khoảng 1 ms). Vì sao hai đường lệch nhau vẫn chưa biết.

5. Điều chưa biết và giới hạn
=============================

- Phần N mà việc tắt ``cpu-sleep`` ở CPU0 loại bỏ là 2.45 ms mỗi lần chạy, chia cho 63 ngắt là khoảng 39 µs mỗi ngắt (số suy ra, không đo trực tiếp từng ngắt). N gồm cả thời gian NPU chạy, nên trace phần mềm ở đây không phân biệt được phần tăng nằm ở NPU hay ở việc ngắt được phục vụ muộn. Cơ chế phần cứng hoặc firmware vẫn chưa biết.
- Phần tăng ở D khi ứng dụng ở CPU1 có mất hẳn khi tắt ``cpu-sleep`` ở CPU1 không: S2 còn 0.200 đến 0.201 so với ngưỡng 0.2.
- Xung nhịp có giải thích phần C giữa CPU1 và CPU4 không (S3 chưa kết luận, chỉ tách được một chiều).
- Vì sao đường ``eval_perf`` lệch đường C API (X3 chưa kết luận, nhịp gọi không đưa C API về gần ``eval_perf``).
- Mọi số ở mục 2 và 3 đo khi có trace. Các ô ghim lệch E2d tối đa 0.61 ms.
- Ảnh hưởng của tải CPU khác (ứng dụng khác chạy cùng lúc) lên các mức chưa được đo trong giai đoạn 1 (U27). Từ khóa đề xuất: "NPU latency CPU contention interrupt affinity RK3588".
- Một board, một lần khởi động (E2b đến X3), ``CORE_0``, một mô hình.

6. Nguồn
========

- T3 board: ``results/npu/latency/onboard_x1_*``, ``results/npu/latency/onboard_x2_*``, ``results/npu/latency/onboard_x3_*`` và ``experiments/npu/latency/onboard_x1/``, ``onboard_x2/``, ``onboard_x3/`` (mỗi thư mục có ``rule.txt``, ``progress.txt``, script chạy, trace nén hoặc CSV). Mã phân tích: ``ai/npu/latency/analyze_trace_x1.py`` (X1 và X2), ``ai/npu/latency/analyze_x3.py``.
- T1 mã nguồn: không có trích dẫn trong trang này.

