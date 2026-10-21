:tocdepth: 1

**********************
Evaluation Protocol v1
**********************

.. admonition:: Tóm tắt

   - Mọi model phải đo qua cùng 1 evaluator với tham số khoá. Protocol hiện là v1 và kết quả lưu kèm phiên bản protocol và git commit.
   - Golden test chạy `yolov8n.pt` chính thức trên `sfchd_test` (1,238 ảnh), trên CPU, sai khác cho phép 0.0005 trên mỗi metric.
   - Kiểm chéo giữa evaluator và `model.val()` phải lệch không quá 0.001. Với model 7 class cũ, 24 metric lệch lớn nhất 0.0001.
   - Đổi bất kỳ tham số nào thì lên v2 và đo lại toàn bộ. Nếu chỉ thêm metric mới mà không đổi số cũ thì lên v1.1.

.. _50-evaluation-protocol-v1:

Evaluation Protocol v1
======================

Mọi model (FP32 hay INT8, Lựa chọn 1 hay 2, baseline hay model đề xuất) phải đo qua **cùng 1 evaluator** với tham số khoá ở các :ref:`AI Quality <51-ai-quality>` đến 5.4. Khác biệt duy nhất giữa 2 lần đo là model.

Quy tắc khoá:

- Protocol có số phiên bản, hiện là **v1**. Mọi kết quả lưu kèm phiên bản protocol và git commit của evaluator.
- **Golden test**: evaluator chạy trên 1 bộ ảnh và 1 model cố định phải ra đúng số đã lưu. Sửa code làm lệch số thì test báo lỗi.

  - Model cố định: ``yolov8n.pt`` chính thức của Ultralytics (ai cũng tải lại được, kiểm bằng sha256). Model này train trên COCO nên mAP trên PPE không có ý nghĩa, chỉ cần số không đổi.
  - Bộ ảnh: eval set ``sfchd_test`` (1,238 ảnh), kiểm cả dấu vân tay dataset. Chạy trên CPU vì GPU có thể lệch ở chữ số thứ 4 giữa các máy. Sai khác cho phép: 0.0005 trên mỗi metric.
  - Số đã lưu: ``ai/automation/golden/evaluator_v1.json``. Lệnh: ``make golden-test`` (khoảng 3 phút).

- **Kiểm chéo**: evaluator và ``model.val()`` (cùng ``rect=False``) trên cùng weights phải lệch không quá 0.001 trên mọi metric. Lệnh: ``make crosscheck RUN=<run_id>`` (ghi ``runs/<run_id>/eval/crosscheck_sfchd_test.json``). Đã chạy với model 7 class cũ (``2026-09-17_sfchd_yolov8n_baseline_100ep``) trên ``sfchd_test``: 24 metric lệch lớn nhất 0.0001.
- Code: ``ai/core/evaluator.py`` (protocol), ``ai/core/backends.py`` (PyTorch/ONNX/RKNN), ``ai/automation/check_evaluator.py`` (golden, kiểm chéo).
- Đổi bất kỳ tham số nào thì lên phiên bản mới (v2) và đo lại toàn bộ model đang so sánh. Không đặt số của 2 phiên bản khác nhau trong cùng 1 bảng. Chỉ thêm metric mới mà không đổi số cũ thì lên phiên bản phụ (v1.1).
