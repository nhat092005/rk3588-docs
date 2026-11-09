:tocdepth: 1

****************************
Điều chưa rõ: Luồng camera
****************************

.. admonition:: Tóm tắt

   - Trang gom các điều chưa biết của mục :doc:`../../10-luong-camera-den-phat-hien/index`, kèm truy vấn tìm nguồn.
   - Đã làm rõ ngày 2026-11-07 bằng đo trên board và đọc mã nguồn driver: số lane (4), chế độ VICAP với ISP (online), ISP chạy luồng (ISP0), ý nghĩa ``BigMode``, cắt 16:9 ở ISP, định dạng ra của ISP (theo driver), vùng điểm ảnh của OV13855 (4256x3168), GPU không dùng trong bước 0 đến 6, thời gian RGA (khóa xung, có và không có NPU chạy cùng), NV12 sang BGR, ``postprocess`` với nhiều hộp, mã hóa VPU và ByteTrack (5.6 ms cho 34 người trên lõi A76, cần ``OPENBLAS_NUM_THREADS=1``).
   - RSS của ``camera.py`` tăng 2 MiB mỗi phút đã tìm ra nguyên nhân: rác vòng tham chiếu của ``rknnlite`` và bản ghi của chính chương trình đo, không thấy rò rỉ trong pipeline. Sau khi sửa còn 0.33 MiB mỗi phút (:doc:`../01-phase/05-phase-9-10`). Các bậc và đỉnh RSS tạm thời trong lần chạy dài vẫn chưa rõ nguyên nhân.
   - Còn lại 7 điều chưa biết ở bảng dưới.

Điều chưa biết
==============

.. list-table::
   :header-rows: 1
   :widths: 6 28 36 30

   * - #
     - Điều chưa biết
     - Đã tìm
     - Truy vấn đề xuất
   * - 1
     - Cổng vật lý ứng với ``ov13855-c1``, ``c2``, ``c3``
     - README overlay trên board chỉ 1 dòng. Wiki Orange Pi 5 chỉ ghi ``MIPI CSI 4Lane``. Tìm web không ra nguồn. Repo không có sơ đồ mạch
     - ``"Orange Pi 5" schematic CAM1 CAM2 MIPI CSI connector``, sơ đồ mạch Orange Pi 5 trong Google Drive của hãng
   * - 2
     - Thứ tự khối trong ISP
     - ``/proc/rkisp0-vir1`` chỉ liệt kê trạng thái bật tắt, TRM không có chương ISP. Rockchip Development Guide ISP30 V1.2.5 (RK-KF-GX-612, bản đăng trên diễn đàn Khadas) tr.18 Figure 1-1 chỉ vẽ ``ISP HW`` thành một khối. Có thứ tự từng phần: thống kê AWB lấy "after Raw-BLC-LSC" (tr.388), thống kê AE lấy "before Debayer" và trong HDR là khung đã tổng hợp (tr.395), khối RGB nằm "before gamma" (tr.395). Suy ra BLC, LSC, tổng hợp HDR, Debayer, gamma [SL từ tài liệu hãng]. Vị trí DPCC, CCM, các khối khử nhiễu, sharpen: unknown
     - ``rkisp v30 ISP block diagram DPCC BLS LSC DEBAYER order``
   * - 3
     - Chiều chia một lớp cho ba lõi NPU, compiler có bật zero-skipping cho YOLOv8n không, tensor skip nhỏ (b, c, d) có ở lại trên chip không
     - UG232 tr.75, ``rknpu_ioctl.h``, TRM1 tr.1985, dữ liệu từng lớp ``RW(KB)``
     - ``RKNN multi-core task split dimension subcore_task``, ``RKNN zero-skipping enable compiler``
   * - 4
     - ``librkaiq`` dùng ``librga.so`` vào việc gì
     - ``librkaiq.so`` không liên kết tĩnh với ``librga`` (``readelf -d`` không có ``NEEDED``), mà có lớp bọc tự ``dlopen`` và phân giải ``wrapbuffer_*``, ``imresize_t``, ``imcrop_t``, ``imcvtcolor_t``, ``imrotate_t``, ``imflip_t``, ``imcopy_t`` [T3 board, ``strings``]. ``rkaiq_3A_server`` lúc camera không chạy chưa nạp ``librga`` (0 dòng trong ``/proc/<pid>/maps``). Sách hướng dẫn ISP30 V1.2.5 không có từ RGA. Module nào gọi lớp bọc này: unknown
     - Đọc ``/proc/<pid>/maps`` của ``rkaiq_3A_server`` khi camera đang chạy, ``rkaiq librga ldch fec rga usage``
   * - 5
     - Trần mã hóa VPU, thời gian RGA và ByteTrack khi NPU và CPU cùng chạy, ByteTrack với hộp thật
     - ``videotestsrc`` che chi phí VPU. ``rga_bench`` và ``track_bench.py`` chạy riêng, hộp tracker là hộp giả
     - Nguồn NV12 từ tệp cho VPU. ``ai/board/app/camera.py`` đã có (:doc:`../../10-luong-camera-den-phat-hien/07-chay-lien-tuc-tren-board`), cần thêm RGA vào luồng và người trước camera
   * - 6
     - Ảnh méo tỉ lệ làm giảm độ chính xác bao nhiêu trên khung camera thật, và màu viền RGA có đúng 114
     - Trên ảnh tĩnh ppe2286 (FP32, PC), letterbox và ép vuông chưa phân biệt được: khoảng tin cậy 95% chứa 0 ở cả hai tập (:doc:`../../10-luong-camera-den-phat-hien/04-tien-xu-ly`). Màu viền RGA chưa đo
     - Bộ khung OV13855 có nhãn, so cắt 16:9 với không cắt. Đọc lại bộ đệm RGB888 sau ``imfill``
   * - 7
     - Mã nguồn driver (nhánh ``orange-pi-6.1-rk35xx``, commit ``f6eedab0cbe9``) có trùng bản build kernel 6.1.99 trên board không
     - Lane, ``BigMode`` và định dạng ISP đều đọc từ mã nguồn này. Rất có thể trùng [SL]: kernel build lúc 08:59:18 UTC ngày 2026-08-20 (``uname -v``, gói ``linux-image-current-rockchip-rk3588`` 1.2.4), commit tạo lúc 07:39:59 UTC cùng ngày, là commit cuối của nhánh trước lúc build, Makefile ở commit đó là 6.1.99 [T3 board, T1 GitHub API]. Bản build không nhúng mã hash nên chưa chứng minh được
     - Build lại kernel từ commit này rồi so ``vmlinuz`` với bản trên board, hoặc đối chiếu chuỗi riêng của commit trong ảnh kernel
