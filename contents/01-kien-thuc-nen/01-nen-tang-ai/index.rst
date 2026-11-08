***********
Nền tảng AI
***********

Kiến thức deep learning làm nền cho các mục sau: mạng nơ-ron, tensor, CNN, chuẩn hóa, activation, huấn luyện, bài toán phát hiện vật thể và các độ đo đánh giá mô hình.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-mang-no-ron`
     - Neuron, lớp và lan truyền xuôi hoạt động thế nào.
   * - 02
     - :doc:`02-tensor-va-kieu-du-lieu`
     - Tensor, channel và các kiểu số FP32, FP16, INT8.
   * - 03
     - :doc:`03-convolution-va-cnn`
     - Tích chập, pooling và các khối CNN, ghép thành mạng thế nào.
   * - 04
     - :doc:`04-chuan-hoa-va-activation`
     - Activation và chuẩn hóa giải quyết vấn đề gì, vì sao chuyển từ ReLU sang SiLU/GELU, và Conv-BN folding.
   * - 05
     - :doc:`05-loss-va-backpropagation`
     - Model học trọng số bằng loss, gradient và backpropagation thế nào, cùng optimizer và overfitting.
   * - 06
     - :doc:`06-huan-luyen-va-suy-luan`
     - Huấn luyện khác suy luận ở đâu, các chặng của pipeline suy luận và chuẩn bị xuất ONNX.
   * - 07
     - :doc:`07-bai-toan-phat-hien-vat-the`
     - Phát hiện vật thể từ ảnh đến danh sách box: định dạng box, anchor-based và anchor-free, NMS.
   * - 08
     - :doc:`08-evaluation-metrics`
     - IoU, Precision, Recall, F1, AP, mAP và nơi trình bày các độ đo phần cứng.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-mang-no-ron
   02-tensor-va-kieu-du-lieu
   03-convolution-va-cnn
   04-chuan-hoa-va-activation
   05-loss-va-backpropagation
   06-huan-luyen-va-suy-luan
   07-bai-toan-phat-hien-vat-the
   08-evaluation-metrics
