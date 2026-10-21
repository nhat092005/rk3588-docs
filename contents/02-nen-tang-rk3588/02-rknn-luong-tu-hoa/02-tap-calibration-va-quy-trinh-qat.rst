:tocdepth: 1

**************************************
Tập dữ liệu chuẩn hóa và quy trình QAT
**************************************

.. admonition:: Trang này trả lời

   - Dataset calibration viết thế nào, cần bao nhiêu ảnh và chọn ảnh ra sao?
   - Khi nào nên dùng QAT, và build FP16 (không lượng tử hóa) làm gì?
   - Nạp model đã lượng tử hóa vào RKNN-Toolkit2 thì ``do_quantization=False`` có nghĩa gì?

.. admonition:: Tóm tắt

   - Calibration set dùng để tính dải lượng tử hóa của activation, nên phải phủ các phân bố dữ liệu của tình huống dùng thật [T1 UG232 tr.122].
   - ``dataset`` là file văn bản, mỗi dòng là một mẫu. Model nhiều input thì các file của một mẫu nằm cùng dòng, cách nhau bằng dấu cách [T1 UG232 tr.122] [T1 UG232 tr.158].
   - Hai định dạng dữ liệu: ảnh (jpg, png, đọc bằng OpenCV) và ``.npy`` (đọc bằng numpy). Input không phải ảnh RGB/BGR thì nên dùng ``.npy`` [T1 UG232 tr.158].
   - Số ảnh khuyến nghị không thống nhất giữa các đoạn: 20-100 cho ``normal`` và ``kl_divergence`` ở [T1 API232 tr.8] [T1 UG232 tr.28], nhưng 20-200 ở [T1 UG232 tr.122] [T1 UG232 tr.159]. Trang giữ cả hai khoảng.
   - ``do_quantization=False`` với model float không lượng tử hóa mà đổi weight từ float32 sang float16. Với model đã lượng tử hóa thì dùng tham số lượng tử hóa có sẵn trong model [T1 UG232 tr.165].
   - QAT chỉ nên cân nhắc khi PTQ của RKNN và hybrid quantization đều không đạt yêu cầu [T1 UG232 tr.126].
   - Với PyTorch, RKNN hỗ trợ model QAT sinh từ giao diện FX (``prepare_qat_fx``) [T1 UG232 tr.127]. ``qconfig`` cần ``reduce_range=False`` và ``qscheme=torch.per_channel_affine`` [T1 UG232 tr.128].
   - Chọn calibration set riêng cho miền hẹp (ví dụ phát hiện PPE) thì unknown. Đã tìm ở: UG232 tr.122, tr.134, tr.158-159, API232 tr.8, tr.14, từ khóa: ``calibration``, ``quantization data``, ``scene``.

.. contents:: Trong trang này
   :local:
   :depth: 1


.. _calibration-dataset:

1. Dataset calibration
======================

Nền. Lượng tử hóa INT8 ánh xạ giá trị float sang số nguyên bằng một cặp scale và zero_point. Với weight, cặp này tính được từ chính weight. Với activation, giá trị thay đổi theo dữ liệu vào, nên toolkit phải chạy thử một số mẫu để quan sát dải giá trị. Tập mẫu đó là calibration set. Kiểu số và ý nghĩa scale, zero_point nằm ở :doc:`01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`.

Hãng mô tả mục đích và yêu cầu về độ phủ như sau:

   "The quantization calibration set is used to compute the quantization range of activation values. When selecting the quantization calibration set, it should cover different data distributions in the actual application scenarios of the model." [T1 UG232 tr.122]

Tài liệu API nhắc ngắn gọn trong mô tả tham số ``dataset``: nên chọn ảnh lượng tử hóa nhất quán với cảnh dự đoán [T1 API232 tr.14].

.. _calibration-chuan-bi-file:

1.1 Cách chuẩn bị file
----------------------

``dataset`` là tham số của ``rknn.build()``, dùng cùng ``do_quantization=True`` [T1 API232 tr.14] [T1 UG232 tr.122]. Giá trị là đường dẫn tới một file văn bản, mỗi dòng ghi đường dẫn của một mẫu. Mẫu có thể là ảnh jpg, png hoặc file ``.npy`` [T1 API232 tr.14].

Với model một input, mỗi dòng một file. Với model nhiều input, các file tương ứng của một mẫu nằm trên cùng dòng:

   "The rule is that one line serves as a set of inputs. When the model has multiple inputs, multiple inputs are written on the same line and separated by spaces." [T1 UG232 tr.158]

Ví dụ model ba input, hai mẫu (theo ví dụ của hãng) [T1 UG232 tr.158]:

.. code-block:: text

   sampleA_in0.npy sampleA_in1.npy sampleA_in2.npy
   sampleB_in0.npy sampleB_in1.npy sampleB_in2.npy

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Nội dung
     - Quy định theo nguồn
   * - Định dạng đọc
     - Ảnh (jpg, png) đọc bằng OpenCV, ``.npy`` đọc bằng numpy [T1 UG232 tr.158]
   * - Input không phải ảnh RGB/BGR
     - Nên dùng ``.npy`` [T1 UG232 tr.158]
   * - Kích thước ảnh
     - Không bắt buộc bằng kích thước input, toolkit tự resize. Resize có thể đổi thông tin ảnh và ảnh hưởng độ chính xác nên tốt nhất dùng ảnh đúng kích thước [T1 UG232 tr.165]
   * - Kích thước ``.npy``
     - Phải khớp shape input của model [T1 UG232 tr.165]
   * - ``rknn_batch_size``
     - Chỉ đổi chiều batch của file RKNN xuất ra, không ảnh hưởng bước lượng tử hóa, nên chuẩn bị dữ liệu như model không batch [T1 UG232 tr.165]
   * - ``quant_img_RGB2BGR``
     - Chỉ tác động khi đọc ảnh ở bước lượng tử hóa. Đặt ``True`` nếu model huấn luyện bằng ảnh BGR. Với ``.npy`` hãng khuyên không dùng tham số này để tránh nhầm [T1 UG232 tr.158]
   * - ``mean_values``, ``std_values``
     - Calibration set được chuẩn hóa trước khi lượng tử hóa, nên hai tham số phải khớp với chuẩn hóa lúc huấn luyện [T1 UG232 tr.132]

Lượng bộ nhớ cũng cần tính trước. Hãng ghi rằng trong lúc lượng tử hóa, toolkit cấp phát bộ nhớ hệ thống theo phân vùng, có thể khiến chương trình bị kill hoặc treo. Cách xử lý được nêu là tăng RAM hoặc swap [T1 UG232 tr.165].

Điều chưa có trong nguồn: cách resize cụ thể (stretch hay letterbox, kiểu nội suy), layout và dtype chấp nhận của ``.npy``, và việc mean/std có áp lên ``.npy`` hay không. Tất cả là unknown. Đã tìm ở: UG232 tr.122, tr.132, tr.158, tr.165, API232 tr.14, từ khóa: ``resize``, ``npy``, ``letterbox``, ``interpolation``. Suy ra: vì chưa biết toolkit có letterbox hay không, ảnh calibration nên được tiền xử lý giống hệt đường inference thật rồi lưu ``.npy``.

.. _calibration-so-anh:

1.2 Số ảnh và cách chọn
-----------------------

Hãng khuyến nghị số ảnh theo thuật toán ``quantized_algorithm`` (mặc định ``normal``) nhưng các đoạn tài liệu không khớp nhau:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Thuật toán
     - Đoạn nêu 20-100 hoặc 20-50
     - Đoạn nêu 20-200
   * - ``normal``
     - 20-100 [T1 API232 tr.8] [T1 UG232 tr.28]
     - 20-200 [T1 UG232 tr.159]
   * - ``kl_divergence``
     - 20-100 [T1 API232 tr.8] [T1 UG232 tr.28]
     - 20-200 [T1 UG232 tr.159]
   * - ``mmse``
     - 20-50 [T1 API232 tr.8] [T1 UG232 tr.28]
     - 20-50 [T1 UG232 tr.159]
   * - ``gdq``
     - "more than 200 pieces", chỉ hợp lệ với ``w4a16`` và ``w8a16`` [T1 API232 tr.8]
     - không nêu

Ngoài bảng, UG232 còn khuyến nghị chung 20-200 ảnh, điều chỉnh theo thời gian chạy của thuật toán lượng tử hóa [T1 UG232 tr.122].

Tài liệu không nói đoạn nào đúng hơn. Cách đọc hợp lý (suy ra): lấy 20 làm cận dưới chung, và coi 100 (hoặc 50 với ``mmse``) là mức bắt đầu an toàn, vì đó là mức API232 gắn với từng thuật toán.

Nhiều ảnh hơn chưa chắc tốt hơn:

   "It should be noted that increasing the number of images in the quantization calibration set will increase the runtime of the quantization algorithm but may not necessarily improve quantization accuracy." [T1 UG232 tr.122]

API232 nói tương tự cho ``normal``: "with more data, the accuracy may not be further improved" [T1 API232 tr.8]. Ngược lại, quá ít hoặc quá nhiều ảnh đều có thể ảnh hưởng độ chính xác (hãng khuyên 20 đến 200 ảnh) [T1 UG232 tr.133].

**Cách chọn ảnh.** Nguồn đưa ra các nguyên tắc sau:

- Ảnh phải phủ các phân bố dữ liệu của tình huống dùng thật. Ví dụ của hãng: model phân loại thì calibration set gồm ảnh của nhiều lớp [T1 UG232 tr.122].
- Ảnh nên giống cảnh dự đoán [T1 API232 tr.14]. Calibration set lệch nhiều so với cảnh triển khai có thể làm giảm độ chính xác [T1 UG232 tr.133].
- Kiểm tra tập đã chọn: lượng tử hóa thử bằng đúng một ảnh (dataset chỉ một dòng) rồi inference trên ảnh đó. Nếu độ chính xác trên ảnh đơn tăng rõ rệt thì tập cũ có thể chưa tối ưu và nên chọn lại ảnh sát cảnh triển khai hơn [T1 UG232 tr.134]. Nếu cải thiện không rõ, vấn đề có thể không nằm ở dataset [T1 UG232 tr.134].
- Nếu ban đầu chỉ dùng một ảnh, thử tăng lên khoảng 20 đến 200 ảnh [T1 UG232 tr.134].

Cách chọn cho miền hẹp như PPE (tỷ lệ lớp, ảnh âm, số ảnh mỗi lớp) là unknown. Đã tìm ở: UG232 tr.122, tr.133-134, tr.159, API232 tr.8, tr.14, từ khóa: ``scene``, ``distribution``, ``categories``, ``calibration set``. Bước tiếp theo khi lượng tử hóa kém được trình bày ở :doc:`03-hybrid-quantization-va-accuracy-analysis`.


.. _qat-va-build-fp16:

2. QAT và build FP16
====================

Nền. Post Training Quantization (PTQ) chỉ cần model đã huấn luyện và một ít dữ liệu không nhãn. Quantization-Aware Training (QAT) huấn luyện lại model có tính đến lỗi lượng tử hóa. Hãng mô tả:

   "During QAT training, the quantization error is incorporated into the training loss function, allowing the training of a model with quantization parameters." [T1 UG232 tr.125]

Bảng so sánh của hãng:

.. list-table::
   :header-rows: 1
   :widths: 32 34 34

   * - Tiêu chí
     - PTQ của RKNN
     - QAT
   * - Huấn luyện lại trên framework gốc
     - Không
     - Có
   * - Dữ liệu
     - Một lượng nhỏ dữ liệu không nhãn
     - Toàn bộ dataset huấn luyện
   * - Điều chỉnh weight
     - Không
     - Có
   * - Hiệu năng
     - Tối ưu
     - Hơi kém PTQ nếu có operator không hỗ trợ QAT

Nguồn của bảng: [T1 UG232 tr.126].

Về cơ chế, QAT giữ weight và tính toán ở dạng float để backpropagation chạy được, và chèn module FakeQuantize tại các vị trí có thể lượng tử hóa để mô phỏng mất mát khi chuyển sang số nguyên [T1 UG232 tr.126].

2.1 Khi nào dùng QAT
--------------------

Lý do hãng đưa ra để không dùng QAT mặc định là cần thêm mã huấn luyện và có thể xung đột với một số repo mã nguồn mở. Vì vậy chỉ nên cân nhắc khi thỏa cả hai điều kiện:

   "it is recommended to consider using QAT when both of the following conditions are met" [T1 UG232 tr.126]

Hai điều kiện là: PTQ của RKNN không đạt yêu cầu độ chính xác (kiểm tra theo chương 7), và hybrid quantization của RKNN không đạt yêu cầu về độ chính xác hoặc hiệu năng [T1 UG232 tr.126]. Chương 7 cũng lặp lại thứ tự này: nếu sau hybrid vẫn thiếu chính xác, hoặc đủ chính xác nhưng hiệu năng không đạt vì hybrid, thì cân nhắc QAT [T1 UG232 tr.135]. Quy trình xử lý lỗi độ chính xác đầy đủ nằm ở :doc:`03-hybrid-quantization-va-accuracy-analysis`.

2.2 Cấu hình QAT cho RKNPU (PyTorch)
------------------------------------

RKNN hỗ trợ model lượng tử hóa sinh từ giao diện FX của PyTorch, cụ thể ``prepare_qat_fx`` và các giao diện đi kèm [T1 UG232 tr.127]. Với Paddle và TensorFlow, hãng chỉ đưa link tài liệu chính thức [T1 UG232 tr.127]. Ví dụ của hãng dành cho ``1.10 <= torch <= 1.13`` [T1 UG232 tr.127] và hiệu chỉnh ``qconfig`` ở hai chỗ:

.. list-table::
   :header-rows: 1
   :widths: 28 30 42

   * - Thành phần
     - Thiết lập
     - Lý do theo hãng
   * - Activation
     - ``reduce_range=False``
     - Khoảng hiệu dụng là -128 đến 127. Với ``True`` chỉ còn -64 đến 63 và kết quả lượng tử hóa kém hơn. Phần cứng RKNN hỗ trợ ``False`` [T1 UG232 tr.128]
   * - Weight
     - ``qscheme=torch.per_channel_affine``
     - Mặc định ``per_channel_symmetric`` cố định zero_point bằng 0, còn phần cứng RKNN hỗ trợ zero_point khác 0 [T1 UG232 tr.128]

Ví dụ của hãng dùng ``MovingAverageMinMaxObserver`` cho activation với ``quant_min=0``, ``quant_max=255``, và ``MovingAveragePerChannelMinMaxObserver`` cho weight với ``quant_min=-128``, ``quant_max=127``, ``dtype=torch.qint8`` [T1 UG232 tr.127].

2.3 Operator float trong model QAT
----------------------------------

Với PyTorch, Conv và Linear có weight được lượng tử hóa theo luật QAT trước. Operator khác nếu thỏa luật lượng tử hóa thường thì lượng tử hóa thường, nếu không thì giữ tính toán FP32 [T1 UG232 tr.128]. Khi chuyển sang RKNN có hai trường hợp:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Trường hợp
     - Kết quả theo hãng
   * - Operator float nằm giữa hai operator đã lượng tử hóa (ví dụ gelu giữa hai conv2d)
     - Được đổi thành operator lượng tử hóa để tăng hiệu năng, không mất độ chính xác [T1 UG232 tr.129]
   * - Operator float thiếu tham số lượng tử hóa ở trước hoặc sau (ví dụ gelu và softmax)
     - Giữ dạng float. Toolkit chèn ``exDataConvert`` để dequantize trước ``exGelu`` và quantize sau Softmax, và các operator chèn thêm này làm tăng độ trễ [T1 UG232 tr.130]

Hãng còn ghi hai kinh nghiệm: cấu hình QAT nên chỉnh theo đặc điểm phần cứng (tham chiếu mục 2.2), và tham số lượng tử hóa lưu trong model có thể không phải tham số dùng thật khi inference (ví dụ sigmoid), nên RKNN-Toolkit2 điều chỉnh các tham số này lúc chuyển đổi để kết quả gần inference PyTorch hơn [T1 UG232 tr.130].

2.4 Build FP16 (không lượng tử hóa)
-----------------------------------

Khi ``do_quantization=False`` với model float, toolkit không lượng tử hóa:

   "do_quantization=False will not perform quantization operations, but will convert the weights from float32 to float16, with almost no accuracy loss." [T1 UG232 tr.165]

Hãng giải thích thêm: RKNPU hiện không hỗ trợ tính toán FP32, nên khi tắt lượng tử hóa, simulator mặc định tính bằng FP16 [T1 UG232 tr.131]. ``float_dtype`` (kiểu float khi không lượng tử hóa) chỉ hỗ trợ ``float16`` và mặc định là ``float16`` [T1 API232 tr.8]. Tham số ``quantize_weight`` cho phép giảm kích thước file RKNN bằng cách lượng tử hóa một phần weight khi ``do_quantization=False``, mặc định ``False`` [T1 API232 tr.9].

Vai trò của FP16 trong xử lý lỗi: FP16 phải đúng thì lượng tử hóa mới có thể đúng, nên khi nghi ngờ độ chính xác, kiểm FP16 trước (``do_quantization=False``, ``init_runtime(target=None)``) rồi mới kiểm lượng tử hóa [T1 UG232 tr.131].

Giới hạn của FP16: tensor trung gian vượt dải ``-65504`` đến ``65504`` sẽ tràn và cho kết quả bất thường [T1 UG232 tr.133]. Hãng ghi một trường hợp kết quả ``nan`` khi ``do_quantization=False`` do đầu ra lớp trung gian (ví dụ -51597 đến 75642) vượt dải FP16 [T1 UG232 tr.176]. Cách xử lý nêu ở [T1 UG232 tr.133] và [T1 UG232 tr.176] là sửa cấu trúc model sao cho tensor không tràn (thường thêm lớp BN).

Giá trị mặc định của ``do_quantization`` không thống nhất giữa hai tài liệu cùng phiên bản 2.3.2: API232 ghi mặc định ``True`` [T1 API232 tr.14], UG232 ghi mặc định ``'False'`` [T1 UG232 tr.122]. Các ví dụ của hãng luôn truyền giá trị tường minh, nên nên luôn đặt rõ tham số này [T1 UG232 tr.92].


.. _nap-model-luong-tu-hoa:

3. Nạp model đã lượng tử hóa
============================

Model đã lượng tử hóa (từ QAT hoặc PTQ ngoài toolkit) mang sẵn scale và zero_point. Lúc nạp vào RKNN-Toolkit2, những tham số này được dùng thay cho bước calibration.

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Tình huống
     - Hành vi theo nguồn
   * - Nạp model đã lượng tử hóa, ``do_quantization=False``
     - Dùng tham số lượng tử hóa có sẵn trong model [T1 UG232 tr.165]
   * - Nạp model float, ``do_quantization=False``
     - Đổi weight float32 sang float16, không lượng tử hóa [T1 UG232 tr.165]
   * - Nạp model đã lượng tử hóa, bước chọn ``quantized_dtype`` và ``quantized_algorithm``
     - Có thể bỏ qua [T1 UG232 tr.157]
   * - Hai trường hợp ``do_quantization=False`` ở trên
     - Đều làm file model nhỏ hơn [T1 UG232 tr.165]

Về giao diện nạp: ``load_pytorch`` hỗ trợ model QAT nhưng cần torch từ 1.9.0 trở lên [T1 API232 tr.13]. Về phiên bản, hãng khuyên dùng PyTorch 1.10 đến 1.13.1 để xuất model lượng tử hóa (QAT, PTQ) và nâng PyTorch mà toolkit phụ thuộc lên cùng khoảng đó [T1 UG232 tr.156].

Hai lưu ý khi dùng model QAT:

- ``rknn.accuracy_analysis(..., target=None)`` gọi trên model gốc là QAT sẽ lỗi [T1 API232 tr.22]. Chi tiết công cụ này ở :doc:`03-hybrid-quantization-va-accuracy-analysis`.
- Kết quả PyTorch và RKNN có thể khác nhau nếu PyTorch chưa đặt ``engine='qnnpack'``. Hãng giải thích inference của RKNN gần với qnnpack hơn [T1 UG232 tr.176].

Phần cấu hình QAT cho Paddle và TensorFlow ngoài việc dẫn link tài liệu chính thức: unknown. Đã tìm ở: UG232 tr.126-130, từ khóa: ``Paddle``, ``TensorFlow``, ``QAT``.


4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Càng nhiều ảnh calibration càng chính xác
     - Tăng số ảnh làm thuật toán chạy lâu hơn nhưng không chắc tăng độ chính xác
     - [T1 UG232 tr.122]
   * - Ảnh calibration phải đúng kích thước input
     - Không bắt buộc vì toolkit tự resize, nhưng nên đúng kích thước để tránh ảnh hưởng độ chính xác. File ``.npy`` thì phải khớp shape input
     - [T1 UG232 tr.165]
   * - Dùng ``rknn_batch_size`` thì phải chuẩn bị calibration theo batch
     - Không cần, ``rknn_batch_size`` không tác động bước lượng tử hóa
     - [T1 UG232 tr.165]
   * - ``do_quantization=False`` luôn cho model float
     - Với model đã lượng tử hóa thì dùng tham số có sẵn trong model, không đổi sang float
     - [T1 UG232 tr.165]
   * - QAT là bước đầu tiên khi INT8 kém chính xác
     - Hãng đề nghị kiểm PTQ và hybrid quantization trước, QAT chỉ khi cả hai không đạt
     - [T1 UG232 tr.126]
   * - Mọi operator float trong model QAT đều bị lượng tử hóa
     - Operator không có tham số lượng tử hóa ở trước hoặc sau giữ dạng float, toolkit chèn operator đổi kiểu và tăng độ trễ
     - [T1 UG232 tr.130]


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
     - 74
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 15
