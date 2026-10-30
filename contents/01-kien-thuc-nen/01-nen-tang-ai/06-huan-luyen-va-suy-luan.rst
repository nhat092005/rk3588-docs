:tocdepth: 1

**********************
Huấn luyện và suy luận
**********************

.. admonition:: Trang này trả lời

   - Huấn luyện khác suy luận ở đâu, và vì sao khác biệt này quan trọng khi triển khai?
   - Lệnh nào chuyển mạng giữa hai chế độ, và lớp nào bị ảnh hưởng?
   - Pipeline suy luận gồm những chặng nào?
   - Khi xuất mô hình sang ONNX cần chuẩn bị gì ở phía PyTorch?

.. admonition:: Tóm tắt

   - Huấn luyện lặp lại forward, tính loss, backward và cập nhật tham số. Suy luận chỉ chạy forward với tham số cố định (xem :doc:`05-loss-va-backpropagation` mục 1) [T2 D2L tr.105, tr.180].
   - ``model.train()`` và ``model.eval()`` đổi chế độ của mạng và chỉ ảnh hưởng một số lớp, ví dụ Dropout và BatchNorm [T1 PTMOD].
   - ``torch.no_grad()`` tắt tính gradient, giảm bộ nhớ khi chắc chắn không gọi ``backward()``. Đây là cơ chế khác với ``eval()`` [T1 PTGRAD, T1 PTMOD].
   - Dropout chỉ bật lúc huấn luyện [T2 D2L tr.196]. BatchNorm dùng thống kê mini-batch lúc huấn luyện và thống kê tích lũy lúc suy luận (xem :doc:`04-chuan-hoa-va-activation` mục 3).
   - Pipeline suy luận có ba chặng: tiền xử lý, forward và hậu xử lý. Giá trị cụ thể của dự án trên board nằm ở mục Bảng tra.
   - Xuất ONNX cần đặt chế độ mạng trước khi xuất, cung cấp đầu vào mẫu (bộ xuất ghi lại shape của đầu vào mẫu) và chọn opset theo runtime hoặc compiler đích [T1 PTONNX].
   - Bộ xuất của Ultralytics gọi ``model.eval()`` rồi ``fuse()`` (gộp Conv và BatchNorm) trước khi xuất [T1 ultralytics 8.4.154 engine/exporter.py:859 đến 863].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Hai chế độ của cùng một mạng
===============================

Cùng một bộ trọng số có thể chạy ở hai chế độ làm việc khác nhau. Một vòng huấn luyện gồm forward, tính loss, backward và cập nhật tham số (:doc:`05-loss-va-backpropagation`, mục 1). Suy luận chỉ giữ chặng forward, tham số không đổi.

Forward propagation được sách định nghĩa là việc tính và lưu các biến trung gian, kể cả đầu ra, từ lớp đầu vào đến lớp đầu ra. [T2 D2L tr.180] Backpropagation là cách tính gradient của tham số mạng [T2 D2L tr.181], nên suy ra chặng backward chỉ cần khi có bước cập nhật.

PyTorch tách việc này thành hai cơ chế độc lập, mỗi cái trả lời một câu hỏi khác nhau.

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Cơ chế
     - Tác dụng
     - Nguồn
   * - ``model.train()`` và ``model.eval()``
     - Đặt chế độ của module. Chỉ ảnh hưởng một số lớp, ví dụ Dropout và BatchNorm. ``eval()`` tương đương ``train(False)``.
     - [T1 PTMOD]
   * - ``torch.no_grad()``
     - Tắt tính gradient. Kết quả mọi phép tính có ``requires_grad=False``, giảm bộ nhớ so với trường hợp bật.
     - [T1 PTGRAD]

..

   "Set the module in evaluation mode. This has an effect only on certain modules. See the documentation of particular modules for details of their behaviors in training/evaluation mode, i.e. whether they are affected, e.g. Dropout, BatchNorm, etc." [T1 PTMOD]

..

   "Disabling gradient calculation is useful for inference, when you are sure that you will not call Tensor.backward(). It will reduce memory consumption for computations that would otherwise have requires_grad=True." [T1 PTGRAD]

Hai cơ chế không thay thế nhau. Tài liệu `eval()` còn dẫn sang mục so sánh với các cơ chế dễ nhầm. [T1 PTMOD] Một mạng ở ``eval()`` vẫn tính gradient nếu không bọc ``no_grad()``, và một mạng trong ``no_grad()`` vẫn dùng hành vi train của Dropout và BatchNorm nếu chưa gọi ``eval()``. Hai ý này suy ra từ hai định nghĩa trên, tài liệu không viết thành câu riêng.

.. _fig-hl-1-ma-tran-eval-vs-nograd:

.. figure:: ../../../_assets/generated/01-kien-thuc-nen/01-nen-tang-ai/06-huan-luyen-va-suy-luan/hl-1-ma-tran-eval-vs-nograd.svg
   :alt: Ma trận phối hợp giữa trạng thái layer (model.train / eval) và autograd engine (enable_grad / no_grad)
   :align: center
   :width: 75%

   Hình 6.1: Ma trận phối hợp giữa trạng thái layer (``model.train()`` / ``model.eval()``) và trạng thái engine Autograd (``torch.enable_grad()`` / ``torch.no_grad()``). Hai cơ chế hoàn toàn độc lập, tránh nhầm lẫn giữa việc khóa đồ thị gradient và việc đổi hành vi Dropout/BatchNorm [T1 PTMOD, T1 PTGRAD].

2. Các điểm khác nhau
=====================

Bảng dưới gom các điểm khác nhau. Chi tiết của từng điểm nằm ở trang đã viết, trang này chỉ nêu kết luận và trỏ tới.

.. list-table::
   :header-rows: 1
   :widths: 16 28 28 28

   * - Tiêu chí
     - Huấn luyện
     - Suy luận
     - Chi tiết
   * - Gradient
     - Tính ở mỗi bước, cần lưu giá trị trung gian của forward [T2 D2L tr.183]
     - Không cần. Có thể bọc ``no_grad()`` [T1 PTGRAD]
     - :doc:`05-loss-va-backpropagation` mục 5
   * - BatchNorm
     - Thống kê của mini-batch, cập nhật running mean và running var
     - Cố định running mean và running var
     - :doc:`04-chuan-hoa-va-activation` mục 4
   * - Dropout
     - Bật, loại ngẫu nhiên một phần nút [T2 D2L tr.194]
     - Tắt: "Typically, we disable dropout at test time." [T2 D2L tr.196]
     - :doc:`05-loss-va-backpropagation` mục 8
   * - Batch size
     - Là tham số của minibatch SGD, ảnh hưởng thống kê BN và nhiễu gradient
     - Thường xử lý từng ảnh. Giá trị của dự án nằm ở :doc:`/contents/07-bang-tra/01-ban-do-code`
     - :doc:`05-loss-va-backpropagation` mục 7
   * - Độ chính xác số
     - FP32 hoặc mixed precision
     - Có thể chạy kiểu ít bit hơn, ví dụ FP16 hoặc INT8 sau lượng tử hóa
     - :doc:`02-tensor-va-kieu-du-lieu`

Hình dưới ở trang 04 cho thấy cơ chế BatchNorm ở hai chế độ, xem :ref:`fig-act-7-co-che-batchnorm-train-vs-inference`. Hình dropout trước và sau khi loại nút ở trang 05, xem :ref:`fig-dropout-truoc-sau`.

3. Pipeline suy luận
====================

Suy luận một ảnh gồm ba chặng nối tiếp.

.. list-table::
   :header-rows: 1
   :widths: 18 40 42

   * - Chặng
     - Việc làm
     - Nội dung chi tiết
   * - Tiền xử lý
     - Đưa ảnh gốc về đúng kích thước, thứ tự kênh và kiểu dữ liệu mà mạng nhận
     - :doc:`02-tensor-va-kieu-du-lieu`
   * - Forward
     - Chạy mạng với tham số cố định, ra đầu ra thô
     - Mục 1, và :doc:`01-mang-no-ron`
   * - Hậu xử lý
     - Giải mã đầu ra thô thành box, lọc ngưỡng và NMS
     - :doc:`07-bai-toan-phat-hien-vat-the` mục 6 và 7

Khi đo độ trễ, chặng forward thường được tách thêm phần nạp dữ liệu vào bộ tăng tốc, thành bốn chặng. Cách tách và cách đo nằm ở :doc:`../05-bo-nho-hieu-nang/01-do-do-tre-va-profiling` mục 1.

4. Xuất mô hình sang ONNX
=========================

ONNX là định dạng trung gian giữa PyTorch và trình biên dịch của NPU. Luồng ONNX sang RKNN nằm ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/01-luong-onnx-sang-rknn`. Mục này chỉ nêu phần phía PyTorch.

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - Việc
     - Nội dung
     - Nguồn
   * - Đặt chế độ mạng
     - Tùy chọn ``training`` của ``torch.onnx.export`` bị đánh dấu deprecated, tài liệu bảo đặt chế độ của mô hình trước khi xuất
     - [T1 PTONNX]
   * - Cung cấp đầu vào mẫu
     - ``args`` là các đầu vào mẫu, đối số Tensor thành đầu vào của mô hình xuất
     - [T1 PTONNX]
   * - Shape cố định hay động
     - Bộ xuất ghi lại shape của đầu vào mẫu. Muốn nhận shape động phải khai báo ``dynamic_shapes`` (hoặc ``dynamic_axes`` với bộ xuất TorchScript)
     - [T1 PTONNX]
   * - Chọn opset
     - Đặt ``opset_version`` theo bản opset mà runtime hoặc compiler đích hỗ trợ
     - [T1 PTONNX]

..

   "opset_version (int | None) – The version of the default (ai.onnx) opset to target. You should set opset_version according to the supported opset versions of the runtime backend or compiler you want to run the exported model with." [T1 PTONNX]

Tài liệu cũng nêu bộ xuất mới dựa trên ``torch.export`` là bộ xuất mới nhất cho PyTorch 2.6 trở lên. [T1 PTONNX]

5. Hệ quả khi triển khai
========================

Các điểm ở trên dẫn tới ba hệ quả khi đưa model lên board.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Hệ quả
     - Lý do và nguồn
   * - Phải xuất ở chế độ ``eval``
     - Nếu BN còn ở chế độ train, đầu ra phụ thuộc thống kê của batch hiện tại thay vì thống kê tích lũy (:doc:`04-chuan-hoa-va-activation` mục 3). PyTorch cho biết ``eval()`` đổi hành vi của BatchNorm và Dropout [T1 PTMOD]. Bộ xuất của Ultralytics gọi ``eval()`` trước khi xuất [T1 ultralytics 8.4.154 engine/exporter.py:861]
   * - BN gộp được vào Conv
     - Ở ``eval``, BN là phép affine cố định nên có thể gộp vào Conv đứng trước (:doc:`04-chuan-hoa-va-activation` mục 5). Ultralytics làm bước này lúc xuất [T1 ultralytics 8.4.154 engine/exporter.py:863]
   * - Tiền xử lý và hậu xử lý phải khớp huấn luyện và đánh giá
     - Nếu LetterBox, thứ tự kênh hoặc phép chia 255 bị lệch thì đầu vào mạng khác đầu vào lúc đánh giá (suy luận, chưa đo). Cách dự án xử lý nằm ở :doc:`/contents/07-bang-tra/01-ban-do-code`

Hệ quả cuối là suy luận, không phải suy ra từ nguồn trích dẫn: khi hai đường chạy (PC và board) có layout và chuẩn hóa khác nhau, việc kiểm lại bằng cùng một ảnh trên cả hai đường là cách duy nhất để chắc chắn chúng cho cùng kết quả.

Số trang D2L là số trang in (bằng số trang PDF trừ 40). PTMOD, PTGRAD và PTONNX là ba trang tài liệu PyTorch bản 2.14 (``torch.nn.Module``, ``torch.no_grad``, ``torch.onnx``) tải ngày 2026-10-20 về ``_assets/pdf/papers/11_pytorch_train_infer/``, dạng trang web nên không có số trang. Nguồn "T1 Ultralytics RKNN doc" là ``_assets/pdf/papers/09_yolo_architecture/ultralytics_docs_integrations_rockchip-rknn.txt``. Theo ``GLOSSARY.md``, T1 là tài liệu hãng hoặc mã nguồn chính thức (ở đây là PyTorch và Ultralytics).
