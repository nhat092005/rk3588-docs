:tocdepth: 1

************************
RKNN: calibration và QAT
************************

.. admonition:: Trang này trả lời

   - dùng bao nhiêu ảnh, định dạng gì, tiền xử lý thế nào?
   - khi PTQ không đủ chính xác thì làm gì?

.. admonition:: Tóm tắt

   - Dataset calibration khuyến nghị 20-200 images [T1 UG232 tr.122], nhưng API232 tr.8 và UG232 tr.28 nêu 20-100 cho `normal` và `kl_divergence`, nên UG232 tự mâu thuẫn.
   - Mỗi dòng của `dataset.txt` là một mẫu, và với model không phải ảnh RGB hoặc BGR nên dùng npy [T1 UG232 tr.158].
   - Ảnh khác kích thước input được resize tự động, nhưng resize có thể ảnh hưởng độ chính xác nên nên dùng ảnh đúng kích thước [T1 UG232 tr.165].
   - Đo T3 trên PC cho thấy một phần chi tiết resize và `.npy` đã rõ, còn model NHWC (tflite), ảnh xám hoặc có alpha, model thật chưa thử.
   - Vendor khuyến nghị QAT chỉ khi PTQ và hybrid quantization đều không đạt yêu cầu [T1 UG232 tr.126].
   - Chọn calibration set cho domain hẹp như PPE là `unknown`.

.. _45-dataset-calibration:

Dataset calibration
===================

**Câu hỏi:** dùng bao nhiêu ảnh, định dạng gì, tiền xử lý thế nào?

**Nguồn nói gì**

   "dataset: A input dataset for rectifying quantization parameters. Currently supports text file format, the user can place the path of picture( jpg or png ) or npy file which is used for rectification. A file path for each line." [T1 API232 tr.14]

..

   "It is generally recommended to select the quantization image which is consistent with the prediction scene." [T1 API232 tr.14]

   "The quantization calibration set is used to compute the quantization range of activation values." [T1 UG232 tr.122]

..

   "It is generally recommended to use a quantization calibration set of 20-200 images, which can be adjusted based on the runtime of the quantization algorithm." [T1 UG232 tr.122]

   "It should be noted that increasing the number of images in the quantization calibration set will increase the runtime of the quantization algorithm but may not necessarily improve quantization accuracy." [T1 UG232 tr.122]

..

   "There are two formats for quantization data. One is the image(jpg, png), RKNN-Toolkit2 will call the OpenCV interface to read; the other is npy format, RKNN-Toolkit2 will call the numpy to read." [T1 UG232 tr.158]

   "For models with non-RGB/BGR image input, it is recommended to use numpy's npy format to provide quantization data." [T1 UG232 tr.158]

..

   "The rule is that one line serves as a set of inputs." [T1 UG232 tr.158]

   "Unnecessary. RKNN-Toolkit2 will automatically resize these images. However, the resize operation may also change the image information and have a certain impact on the quantization accuracy, so it is best to use images matching the input size." [T1 UG232 tr.165]

..

   "The rknn_batch_size parameter of rknn.build() will only modify the batch dimension of the finally exported RKNN model (from 1 to rknn_batch_size ), and will not affect the process of the quantization stage." [T1 UG232 tr.165]

   "During the model quantization process, RKNN-Toolkit2 will allocate partitioned system memory, which may cause the program to be killed or stuck." [T1 UG232 tr.165]

..

   "Initially, use a single image for quantization (leave only one line in dataset.txt) and perform inference using this image." [T1 UG232 tr.134]

Số ảnh theo thuật toán (API232 tr.8):

.. list-table::
   :header-rows: 1

   * - Thuật toán
     - Số ảnh đề xuất (API232 tr.8)
   * - ``normal``
     - "about 20-100 pieces"
   * - ``mmse``
     - "about 20-50 pieces"
   * - ``kl_divergence``
     - "about 20-100 pieces"
   * - ``gdq``
     - "more than 200 pieces" (không áp dụng cho RK3588)

**Ý chính**

- Mỗi dòng của ``dataset.txt`` là một mẫu; model nhiều input thì các file cùng dòng cách nhau bằng dấu cách (UG232 tr.158).
- Ảnh được resize tự động nếu khác kích thước input, nhưng resize có thể ảnh hưởng độ chính xác. Nên dùng ảnh đúng kích thước (UG232 tr.165).
- Với model không phải ảnh RGB hoặc BGR, nên dùng ``.npy`` (UG232 tr.158).
- Dữ liệu calibration không cần chuẩn bị theo batch dù dùng ``rknn_batch_size`` (UG232 tr.165).
- Ví dụ chính thức không theo khuyến nghị này: ``examples/onnx/yolov5/dataset.txt`` có 1 ảnh, ví dụ ``accuracy_analysis``, ``hybrid_quant``, ``quantize_algorithm_mmse`` cũng 1 ảnh, còn ``caffe/mobilenet_v2/dataset.txt`` có 20 dòng. Lý do ví dụ dùng ít ảnh không được tài liệu nêu.

**Giới hạn**

- Số ảnh: API232 tr.8 và UG232 tr.28 nêu 20-100 cho ``normal`` và ``kl_divergence``; UG232 tr.122, 133, 134 và 159 nêu 20-200. UG232 tự mâu thuẫn; file này giữ cả hai khoảng, không chọn một.
- Cách resize (stretch hay letterbox, interpolation), layout và dtype của ``.npy``, và việc mean/std có áp dụng lên ``.npy`` hay không: UG232 tr.132 chỉ nói "the quantization correction dataset will undergo normalization first". Đóng một phần (T3): Đo T3 trên PC (toolkit 2.3.2, ``target_platform='rk3588'``, một model ONNX NCHW đồng nhất, đọc ``quant_tab`` trong file ``.rknn``; log và script: ``tmp/04_debug-logs/2026-10-10_t3-calibration-pc/README.md``): ảnh calibration khác kích thước model được resize cả ảnh về kích thước model (không cắt, không đệm letterbox: ảnh rộng 128x64 và cao 64x128 đều giữ nguyên dải giá trị), và nội suy có lấy trung bình điểm ảnh (loại được nearest, chưa phân biệt bilinear, area, antialias); ``.npy`` nhận float32 hoặc uint8, dạng ``[1,C,H,W]`` hoặc ``[C,H,W]`` theo layout NCHW; ``[1,H,W,C]`` và sai kích thước bị từ chối (``ValueError``, không tự resize); ``mean`` và ``std`` được áp dụng lên ``.npy`` (npy 150 đến 250 với ``mean=250 std=2`` ra dải -50 đến 0). Chưa thử: model NHWC (tflite), ảnh xám hoặc có alpha, RGB/BGR, model thật, ảnh hưởng lên accuracy. Suy luận (không đo): nếu inference dùng letterbox thì ảnh calibration nên được letterbox trước, vì toolkit không đệm.
- Chọn calibration set cho domain hẹp như PPE: ``unknown`` (cũng là một mục chưa có nguồn ở file ``03_``).

--------------

.. _46-qat-build-fp16-và-nạp-model-đã-lượng-tử-hóa:

QAT, build FP16 và nạp model đã lượng tử hóa
============================================

**Câu hỏi:** khi PTQ không đủ chính xác thì làm gì?

**Nguồn nói gì**

   "it is recommended to consider using QAT when both of the following conditions are met:" [T1 UG232 tr.126]

Hai điều kiện (UG232 tr.126): PTQ của RKNN không đạt yêu cầu độ chính xác (xem chương 7), và hybrid quantization của RKNN không đạt yêu cầu độ chính xác và hiệu năng (xem :ref:`Fusion và tối ưu đồ thị <63-fusion-và-tối-ưu-đồ-thị>`).

   "RKNN currently supports quantized models generated from the FX interface, specifically the prepare_qat_fx interface and its associated interfaces." [T1 UG232 tr.127]

..

   "When the imported model is a floating-point model, do_quantization=False will not perform quantization operations, but will convert the weights from float32 to float16, with almost no accuracy loss." [T1 UG232 tr.165]

   "Support the Quantization Aware Training (QAT) model, but need update torch version to '1.9.0' or higher." [T1 API232 tr.13]

**Ý chính**

- Thứ tự vendor đề xuất: PTQ, rồi hybrid, rồi QAT. QAT chỉ khi hai bước trước không đạt (UG232 tr.126).
- Với PyTorch, RKNN-Toolkit2 hỗ trợ model QAT sinh ra từ giao diện FX (``prepare_qat_fx``) (UG232 tr.127).
- ``do_quantization=False`` có hai nghĩa tùy model nạp vào: model float thì convert weight sang FP16, model đã lượng tử hóa thì dùng tham số trong model (UG232 tr.165).

**Giới hạn.** Chưa trích mục 6.4.4 UG232 (cấu hình cụ thể cho từng framework) ngoài ví dụ PyTorch. API232 tr.22: nếu model gốc là QAT thì ``accuracy_analysis`` với ``target=None`` sẽ lỗi.

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 13
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 3
