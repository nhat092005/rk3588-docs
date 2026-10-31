:tocdepth: 1

********************
Luồng ONNX sang RKNN
********************

.. admonition:: Trang này trả lời

   - các bước nào biến một file ONNX thành file ``.rknn`` cho RK3588?
   - những bước biến đổi đồ thị nào trong toolkit đã có bằng chứng?
   - điều gì về pass và thứ tự pass vẫn chưa có nguồn?

.. admonition:: Tóm tắt

   - Luồng convert gồm khởi tạo ``RKNN()``, ``config``, ``load_onnx``, ``build``, ``export_rknn`` rồi ``release`` [T1 UG232 tr.9] [T1 UG232 tr.21].
   - Phải đặt ``target_platform='rk3588'``. Nếu bỏ trống, model chỉ chạy được trên RK3566 và RK3568 [T1 UG232 tr.173].
   - Ví dụ ``yolov5/test.py`` trong SDK mặc định ``target_platform='rk3566'`` và gọi ``init_runtime()`` không có ``target`` [T1 EX examples/onnx/yolov5/test.py:242] [T1 EX examples/onnx/yolov5/test.py:271].
   - Sơ đồ phần mềm của toolkit có hai khối tối ưu: Graph Optimizer (Const Fold, OP Fuse, OP Convert) và Compiler (OP Fuse, Tiling, Memory Planning, RKNN Generator) [T1 UG232 tr.7, Figure 1-2].
   - Tên hàm và tên pass thật lộ ra trong log lỗi: ``fold_constant``, ``fuse_ops``, ``RKNNTilingPass``, ``OpEmit`` và vài tên khác [T1 UG232 tr.166] [T1 UG232 tr.168] [T1 UG232 tr.169].
   - ``optimization_level`` mặc định là 3. Mức 2 và 1 tắt một số rule, mức 0 tắt tất cả [T1 API232 tr.8].
   - Các pass nội bộ của compiler được đóng gói trong thư viện nhị phân của toolkit và chỉ lộ một phần qua sơ đồ khối, log debug và changelog [T1 UG232 tr.7, tr.166-169].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _onnx-rknn-cac-buoc-convert:

1. Các bước convert
===================

Nền. File ``.rknn`` là file nhị phân chạy trên RKNPU [T1 UG232 tr.10]. Toolkit trên PC đọc model gốc, tối ưu đồ thị, lượng tử hóa nếu được yêu cầu, rồi ghi ra file này. Trang này chỉ mô tả phần convert. Phần chạy thử (simulator, board nối PC) ở :doc:`02-toolkit-pc-va-lite2-board`.

1.1 Năm lời gọi và thứ tự
-------------------------

UG232 mô tả giai đoạn convert gồm cấu hình, nạp, build và export [T1 UG232 tr.9]:

   "Model Building: Build the RKNN model using the rknn.build() interface. Users can choose whether to perform quantization to improve the model's performance on the hardware." [T1 UG232 tr.9]

.. _fig-luong-convert-ug232:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/03-toolchain-runtime/luong-onnx-sang-rknn/ug232-fig3-1-model-conversion-flow.png
   :align: center
   :alt: Lưu đồ convert model: RKNN init, config, load_xxx, build, export_rknn, RKNN release

   Lưu đồ convert: RKNN init, config, một trong các ``load_*``, build, export_rknn, RKNN release. Nguồn: [T1 UG232 tr.21, Figure 3-1]

.. list-table::
   :header-rows: 1
   :widths: 14 24 46 16

   * - Bước
     - Lời gọi
     - Việc làm và tham số đáng chú ý
     - Nguồn
   * - Khởi tạo
     - ``RKNN(verbose, verbose_file)``
     - Phải gọi trước mọi API khác. ``verbose=True`` in log chi tiết khi nạp và build. Hết việc thì gọi ``release()``
     - [T1 API232 tr.6] [T1 UG232 tr.21] [T1 UG232 tr.22]
   * - Cấu hình
     - ``rknn.config(...)``
     - Đặt tham số convert trước khi build: mean, std, quantization, target platform
     - [T1 API232 tr.6] [T1 UG232 tr.22]
   * - Nạp ONNX
     - ``rknn.load_onnx(model, inputs, input_size_list, input_initial_val, outputs)``
     - ``model`` là đường dẫn ``.onnx``. ``inputs`` và ``outputs`` mặc định ``None`` nghĩa là lấy từ model. Nếu đặt ``inputs`` thì phải đặt cả ``input_size_list``
     - [T1 API232 tr.12]
   * - Build
     - ``rknn.build(do_quantization, dataset, rknn_batch_size, auto_hybrid)``
     - ``do_quantization`` mặc định ``True``. ``dataset`` là file văn bản, mỗi dòng một ảnh jpg, png hoặc npy để hiệu chỉnh tham số lượng tử hóa
     - [T1 API232 tr.14] [T1 UG232 tr.24]
   * - Export
     - ``rknn.export_rknn(export_path)``
     - Ghi file có hậu tố ``.rknn``. Tham số ``cpp_gen_cfg`` có thể sinh ví dụ C++ triển khai
     - [T1 API232 tr.15] [T1 UG232 tr.25]

Thứ tự ``config`` trước ``load_onnx`` theo Figure 3-1 và mọi ví dụ đã đọc. API232 tr.6 chỉ nói "Before the RKNN model is built" nên chưa có câu nào cấm thứ tự ngược lại (suy ra).

Nếu ``build`` có ``do_quantization=True`` thì lượng tử hóa nằm trong lời gọi này. Cách chọn thuật toán, granularity và dữ liệu hiệu chỉnh ở :doc:`../02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa` và :doc:`../02-rknn-luong-tu-hoa/02-tap-calibration-va-quy-trinh-qat`.

1.2 Tham số quyết định kết quả convert
--------------------------------------

UG232 liệt kê tám việc cần xác nhận trước khi convert [T1 UG232 tr.157] [T1 UG232 tr.158]. Bảng dưới gộp những tham số có tác dụng rõ nhất với ONNX trên RK3588.

.. list-table::
   :header-rows: 1
   :widths: 22 52 26

   * - Tham số
     - Tác dụng theo nguồn
     - Nguồn
   * - ``target_platform``
     - Chọn chip đích. Mặc định ``None``. Danh sách hỗ trợ gồm ``rk3566``, ``rk3568``, ``rk3576``, ``rk3588`` và các chip khác. Model build cho RK3588 dùng được trên RK3588S
     - [T1 API232 tr.8] [T1 UG232 tr.22] [T1 UG232 tr.158]
   * - ``mean_values``, ``std_values``
     - Giá trị trung bình và chuẩn hóa của đầu vào. Được áp trong lúc lượng tử hóa nên ảnh không cần trừ mean và chia std lại khi suy luận bằng C API
     - [T1 UG232 tr.22]
   * - ``quant_img_RGB2BGR``
     - Có đổi RGB sang BGR khi nạp ảnh hiệu chỉnh hay không. Mặc định ``False``. Chỉ có tác dụng ở bước hiệu chỉnh, không tác dụng ở suy luận
     - [T1 UG232 tr.22]
   * - ``optimization_level``
     - Mặc định 3. Xem mục 2.3
     - [T1 API232 tr.8] [T1 UG232 tr.22]
   * - ``quantized_algorithm``, ``quantized_method``
     - Thuật toán (``normal``, ``mmse``, ``kl_divergence``) và granularity (``layer``, ``channel``). Mặc định ``normal`` và ``channel``
     - [T1 UG232 tr.22] [T1 UG232 tr.28]
   * - ``dynamic_input``
     - Mô phỏng đầu vào động theo nhiều bộ shape do người dùng đưa vào
     - [T1 UG232 tr.23]

Hậu quả của ``target_platform``:

   "when target_platform in the rknn.config() interface is not set, the generated RKNN model can only run on RK3566/RK3568." [T1 UG232 tr.173]

Một lỗi liên quan ở runtime: khi không đặt, mặc định là ``rk3566`` và ``rknn_init`` báo ``Invalid RKNN format`` hoặc ``RKNN_ERR_MODEL_INVALID`` [T1 UG232 tr.173] [T1 UG232 tr.175].

Ví dụ số (suy ra). Ví dụ yolov5 trong SDK đặt ``mean_values=[[0, 0, 0]]`` và ``std_values=[[255, 255, 255]]`` [T1 EX examples/onnx/yolov5/test.py:242]. Pixel 255 đi vào NPU thành :math:`(255 - 0) / 255 = 1.0`, pixel 0 thành 0.0. Nghĩa là model gốc được huấn luyện với ảnh chuẩn hóa về khoảng 0 đến 1.

1.3 Ví dụ trong SDK và công cụ dòng lệnh
----------------------------------------

Ví dụ ``examples/onnx/yolov5/test.py`` gọi theo thứ tự ``RKNN(verbose=True)`` (dòng 238), ``rknn.config(...)`` (242), ``rknn.load_onnx(...)`` (247), ``rknn.build(...)`` (255), ``rknn.export_rknn(...)`` (263), ``rknn.init_runtime()`` (271) và ``rknn.release()`` (314) [T1 EX examples/onnx/yolov5/test.py:238]. Hai chỗ phải sửa khi dùng cho RK3588: ``target_platform='rk3566'`` ở dòng 242 và ``init_runtime()`` không có ``target`` ở dòng 271. Gọi không có ``target`` nghĩa là suy luận trên simulator [T1 API232 tr.17].

Ví dụ ``examples/functions/onnx_edit/test.py`` đặt ``target_platform='rk3588'`` rồi lặp đúng chuỗi ``load_onnx``, ``build``, ``export_rknn`` hai lần, trước và sau khi sửa ONNX bằng ``rknn.utils.onnx_edit`` [T1 EX examples/functions/onnx_edit/test.py:5] [T1 EX examples/functions/onnx_edit/test.py:22]. README đi kèm nói việc đổi reshape và transpose ở đầu vào, đầu ra giúp pass tối ưu đồ thị của toolkit cho ra model gọn hơn [T1 EX examples/functions/onnx_edit/README_EN.md:29].

Công cụ ``rknn_convert`` bọc các lời gọi trên, đọc file YAML và nhận ``-t`` cho target platform [T1 UG232 tr.25]:

   "python -m rknn.api.rknn_convert -t rk3588 -i ./model_config.yml -o ./output_path" [T1 UG232 tr.25]

File YAML khai báo ``platform: onnx``, ``model_file_path``, ``quantize``, ``dataset`` và khối ``configs`` ánh xạ sang ``rknn.config()`` [T1 UG232 tr.26] [T1 UG232 tr.27].

Đường xuất ONNX của Ultralytics cho YOLO và cờ ``end2end`` nằm ở :doc:`../05-yolo-tren-rk3588/01-do-thi-xuat-va-duong-rknn`.

.. _onnx-rknn-cac-pass-da-biet:

2. Các pass đã biết
===================

Nền. Pass là một bước biến đổi đồ thị tính toán, ví dụ gộp hai node thành một hoặc thay node này bằng node tương đương. Tài liệu của hãng không có chương nào liệt kê pass của toolkit. Mục này gom những gì lộ ra từ sơ đồ, log lỗi, bảng rule, changelog và Operator List. Mỗi nguồn chỉ trả lời một phần nhỏ.

.. _fig-toolkit2-software-diagram:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/03-toolchain-runtime/luong-onnx-sang-rknn/ug232-fig1-2-toolkit2-software-diagram.png
   :align: center
   :alt: Sơ đồ phần mềm RKNN-Toolkit2 gồm Frontend Loader, Graph Optimizer, Quantizer, Compiler, Debugger

   Sơ đồ phần mềm RKNN-Toolkit2. Graph Optimizer có Const Fold (hình in ``Const Flod``), OP Fuse, OP Convert. Compiler có OP Fuse, Tiling, Memory Planning, RKNN Generator. Nguồn: [T1 UG232 tr.7, Figure 1-2]

Hình chỉ cho biết tên khối và việc ``OP Fuse`` xuất hiện ở cả hai tầng. Văn bản UG232 không giải thích từng khối (xem mục 3).

2.1 Tên hàm và pass lộ ra trong log
-----------------------------------

Phần "Troubleshooting" của UG232 in nguyên traceback và log của các lỗi convert. Từ đó đọc được một số tên thật.

.. list-table::
   :header-rows: 1
   :widths: 30 44 26

   * - Tên
     - Thấy ở đâu
     - Nguồn
   * - ``GraphOptimizer.run``, ``GraphOptimizer.fuse_ops``, ``_fuse_ops``
     - Traceback lỗi ``infer_shapes`` khi ``build``, đi qua ``rknn/api/graph_optimizer.py``
     - [T1 UG232 tr.166]
   * - ``IRGraph.rebuild``, ``_clean_model``, ``infer_shapes``
     - Cùng traceback, trong ``rknn/api/ir_graph.py``. ``infer_shapes`` gọi ``onnx.shape_inference``
     - [T1 UG232 tr.166]
   * - ``_p_fuse_two_mul``, ``_p_fuse_mul_into_conv``
     - Traceback lỗi broadcast. Tên có tiền tố ``_p_fuse_`` chỉ tới các rule gộp riêng lẻ: gộp hai ``Mul``, gộp ``Mul`` vào ``Conv``
     - [T1 UG232 tr.167]
   * - ``fold_constant``, ``_fold_constant``
     - Log ``_fold_constant remove nodes = [...]`` và traceback ``GraphOptimizer.fold_constant`` đi qua ``Session.run`` của ONNX Runtime
     - [T1 UG232 tr.167] [T1 UG232 tr.169]
   * - ``RKNNInitCastConst``, ``RKNNMultiSurfacePass``, ``RKNNTilingPass``, ``RKNNProfileAnalysisPass``, ``OpEmit``
     - Log ``D RKNN`` có dòng ``start`` và ``end`` cho từng pass, theo đúng thứ tự này, ngay trước lỗi ``Meet unsupported dims in reducesum``
     - [T1 UG232 tr.168]

Ba điều suy ra từ bảng, không phải câu của hãng:

- Có hai tầng mã. Tầng Python (``rknn/api/graph_optimizer.py``, ``ir_graph.py``) làm gộp rule, folding và suy luận shape. Tầng C++ (tên dạng ``N4rknn14RKNNTilingPassE``, đọc là ``rknn::RKNNTilingPass``) chạy sau, gồm tiling và phát lệnh ``OpEmit``. Cách chia này khớp với hai khối Graph Optimizer và Compiler trong Figure 1-2, nhưng UG232 không nói ánh xạ này.
- Constant folding thực thi các node hằng bằng ONNX Runtime. Lỗi ``invalid expand shape`` xảy ra ở ``Expand`` có kích thước phụ thuộc đầu vào [T1 UG232 tr.169].
- Thứ tự năm tên ở dòng cuối bảng chỉ là thứ tự trong một log lỗi. Đó chưa phải đặc tả pipeline.

2.2 Rule và biến đổi có công bố
-------------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 48 26

   * - Loại
     - Nội dung
     - Nguồn
   * - Fusion do phần cứng hỗ trợ
     - Bảng "Supported fusion rules": Conv+Relu, Conv+PRelu(LeakyRelu), Conv+Clip, Conv+Sigmoid(Tanh/Elu/Silu...), Conv+Add, Conv+Activation+Add. Cột "future plans" gồm Activation+Add(Mul), Add(Mul)+Activation, Conv+Mul, Conv+Activation+Mul, Conv+Activation+Pooling, Conv+Activation+Add(Mul)+Pooling. Bảng đầy đủ và cách tận dụng ở :doc:`05-fusion-va-layout-nc1hwc2`
     - [T1 UG232 tr.142]
   * - Fusion subgraph
     - ``Split + Sigmoid + Mul`` thành ``GLU``. ``ReduceMean + Sub + Pow + ReduceMean + Add + Sqrt + Div (+ Mul + Add)`` thành ``LayerNorm``
     - [T1 UG232 tr.148]
   * - Đổi Resize
     - Toolkit đổi ``Resize`` thành ``ConvTranspose`` vì NPU chưa có Resize cấp phần cứng. Đặt ``optimization_level=2`` thì ``Resize`` dùng CPU
     - [T1 UG232 tr.176]
   * - Op có mục NPU riêng cho dạng đã gộp (RK3588)
     - ``ConvolutionRelu`` (mục 3.2.7), ``ConvolutionSwish`` (3.2.17), ``ConvolutionAddRelu`` (3.2.19), ``ConvTransposeRelu`` (3.2.21, in là ``ConvTranpose``), ``MulRelu`` (3.2.42). Cùng nhóm còn Clip, PRelu, Add, Sigmoid, Tanh, Softplus, HardSigmoid, HardSwish, Elu, Mish
     - [T1 OPL tr.60] [T1 OPL tr.63] [T1 OPL tr.65] [T1 OPL tr.78]

Điều kiện kích thước và kiểu dữ liệu của từng op nằm ở :doc:`04-operator-list`. Với Resize, hai tài liệu T1 chưa thống nhất và được phân tích ở trang đó.

UG232 nhấn mạnh toolkit không tự làm hết:

   "In the RKNN-Toolkit2 toolchain, the software stack already performs graph optimization to a certain extent during the model conversion process. However, this process is not omnipotent and perfect." [T1 UG232 tr.141]

Cùng chương, UG232 đưa các cách chỉnh tay: đổi op không chạy NPU thành op chạy được, đổi thứ tự ``Transpose`` và ``Clip`` để ``Conv + Clip`` gộp được, gộp các ``Reshape`` hoặc ``Transpose`` liên tiếp [T1 UG232 tr.141] [T1 UG232 tr.142] [T1 UG232 tr.143].

2.3 Điều khiển bằng optimization_level
--------------------------------------

   "By modifying the model optimization level, you can turn off some or all of the optimization rules used in the model conversion process. The default value of this parameter is 3, and all optimization options are turned on." [T1 API232 tr.8]

.. list-table::
   :header-rows: 1
   :widths: 14 56 30

   * - Mức
     - Hành vi đã biết
     - Nguồn
   * - 3
     - Mặc định, bật mọi rule. UG232 gọi là ưu tiên tốc độ và nói một số rule ảnh hưởng nhẹ đến độ chính xác được bật ở mức này
     - [T1 API232 tr.8] [T1 UG232 tr.133]
   * - 2
     - Tắt một số rule có thể ảnh hưởng độ chính xác. Hai tác dụng cụ thể: ``Resize`` chạy CPU, và từ bản v1.3.4b5 tắt gộp ``Conv + Add``
     - [T1 UG232 tr.176] [T1 EX changelog-2.3.2.txt:957-958]
   * - 1
     - Cùng câu mô tả với mức 2 ("some optimization options that may affect the accuracy of some models"), tài liệu API không tách danh sách rule riêng giữa mức 1 và mức 2
     - [T1 API232 tr.8]
   * - 0
     - Tắt mọi tối ưu
     - [T1 API232 tr.8] [T1 UG232 tr.22]

2.4 Dấu vết trong changelog
---------------------------

Changelog SDK không liệt kê pass, nhưng ghi lại khi nào một rule hoặc nhóm rule được thêm hay sửa. Bảng chọn các dòng liên quan đến đồ thị. Phiên bản nhỏ (b14, b15...) là bản beta của nhánh 2.0.

.. list-table::
   :header-rows: 1
   :widths: 18 56 26

   * - Phiên bản
     - Thay đổi liên quan
     - Nguồn
   * - v1.3.4b5
     - ``optimization_level=2`` tắt gộp ``Conv + Add``
     - [T1 EX changelog-2.3.2.txt:957-958]
   * - v1.5.0
     - Thêm fuse NPU cho Conv-Silu, Conv-Swish, Conv-Hardswish, Conv-Sigmoid, Conv-Gelu
     - [T1 EX CHANGELOG.md:100]
   * - v2.0.0b14
     - Thêm gộp ``ConvTranspose + Relu/LeakyRelu``. Cải thiện constant folding với tensor rỗng
     - [T1 EX changelog-2.3.2.txt:193-194]
   * - v2.0.0b15, b16
     - Thêm rule gộp BatchNorm vào ``Conv``/``Deconv`` và hoàn thiện rule BN với ``Deconv``
     - [T1 EX changelog-2.3.2.txt:184] [T1 EX changelog-2.3.2.txt:177]
   * - v2.0.0b21
     - Thêm gộp ``ConvTranspose + Sigmoid``. Thêm rule loại ``ReduceMean``/``ReduceSum`` vô hiệu. Hỗ trợ ưu tiên nhiều cấp cho rule tối ưu đồ thị
     - [T1 EX changelog-2.3.2.txt:127] [T1 EX changelog-2.3.2.txt:128] [T1 EX changelog-2.3.2.txt:132]
   * - v2.0.0b23
     - Sửa lỗi gộp ``Add + Relu`` mất tác dụng khi bật ``global_fuse``
     - [T1 EX changelog-2.3.2.txt:103]
   * - v2.3.2
     - Sửa lỗi và treo trong tối ưu đồ thị. Hoàn thiện cơ chế loại ``Transpose`` (TP). Thêm loại chiều dư thừa. Tối ưu quy tắc hoán đổi op. Dòng tóm tắt: "Enhanced graph optimization capabilities"
     - [T1 EX changelog-2.3.2.txt:4] [T1 EX changelog-2.3.2.txt:12] [T1 EX changelog-2.3.2.txt:13] [T1 EX changelog-2.3.2.txt:19] [T1 EX CHANGELOG.md:11]

Một dấu vết khác: Toolkit1 từng có các công tắc ``deconv_merge``, ``conv_mul_merge`` và ``need_horizontal_merge`` trong ``config``. Danh sách tham số Toolkit2 không còn các công tắc này, ``optimization_level`` là công tắc duy nhất liên quan đến rule [T1 APIDIFF:30-32] [T1 APIDIFF:49-62]. Suy ra: người dùng không bật tắt riêng từng rule gộp.

.. _onnx-rknn-dieu-chua-ro:

3. Ranh giới thông tin của tài liệu hãng
========================================

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Chủ đề
     - Ranh giới thông tin theo nguồn T1
   * - Danh sách pass của tầng Python và C++
     - Tài liệu chỉ công bố sơ đồ khối ở Figure 1-2 và các tên pass/hàm xuất hiện trong log lỗi ở mục 2.1 [T1 UG232 tr.7, tr.166-169]
   * - Thuật toán của Tiling, Memory Planning, OP Convert, OpEmit
     - Nằm trong thư viện biên dịch đóng gói sẵn, tài liệu chỉ nêu tên khối trong Figure 1-2 và log ``RKNNTilingPass`` / ``OpEmit`` [T1 UG232 tr.7, tr.168]
   * - Chi tiết từng mức ``optimization_level``
     - API232 dùng chung mô tả cho mức 1 và mức 2 [T1 API232 tr.8]. Hai rule cụ thể của mức 2 được xác nhận ở mục 2.3 là đưa ``Resize`` về CPU và tắt gộp ``Conv + Add`` [T1 UG232 tr.176] [T1 EX changelog-2.3.2.txt:957-958]
   * - Cơ chế ``global_fuse`` và bảng "future plans"
     - Tên ``global_fuse`` xuất hiện trong dòng sửa lỗi ``Add + Relu`` của changelog [T1 EX changelog-2.3.2.txt:103], còn các tổ hợp ở cột "future plans" của Figure 8-7 chưa có mục riêng trong OPL 3.2 [T1 UG232 tr.142]
   * - Phiên bản ONNX và opset hỗ trợ
     - API232 ghi gói ``onnx`` ``1.7.0 ~1.17.0`` cho toolkit 2.3.2 [T1 API232 tr.5] (UG232 còn giữ khuyến nghị cũ ``1.7.0~1.10.0`` [T1 UG232 tr.21]), còn về opset thì changelog và bảng op xác nhận hỗ trợ đến opset 19 [T1 EX CHANGELOG.md:71] [T1 OPSUP:4]
   * - Ví dụ nạp ONNX trong UG232
     - Mục "ONNX loading" ở UG232 tr.24 in nhầm dòng ``rknn.load_tflite(model='./mobilenet_v1.tflite')`` thay vì ``load_onnx`` (ví dụ đúng nằm ở [T1 API232 tr.12-13])

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 50 22

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Không đặt ``target_platform`` thì model vẫn chạy trên RK3588
     - Model chỉ chạy được trên RK3566 và RK3568. Mặc định khi không đặt là ``rk3566``
     - [T1 UG232 tr.173] [T1 UG232 tr.175]
   * - Chạy nguyên ví dụ ``yolov5/test.py`` là đã thử trên NPU RK3588
     - Ví dụ đặt ``rk3566`` và gọi ``init_runtime()`` không có ``target``, nên suy luận chạy trên simulator
     - [T1 EX examples/onnx/yolov5/test.py:242] [T1 EX examples/onnx/yolov5/test.py:271] [T1 API232 tr.17]
   * - ``do_quantization=False`` giữ model ở FP32
     - Với model float, tham số này đổi trọng số từ float32 sang float16. NPU chưa hỗ trợ tính toán FP32 nên simulator cũng dùng FP16
     - [T1 UG232 tr.165] [T1 UG232 tr.131]
   * - Toolkit đã tối ưu đồ thị nên không cần chỉnh model
     - UG232 nói quá trình này "not omnipotent and perfect" và hướng dẫn chỉnh tay đồ thị
     - [T1 UG232 tr.141]
   * - Tắt rule gộp riêng lẻ được bằng ``config``
     - ``config`` của Toolkit2 chỉ còn ``optimization_level``. Các công tắc gộp riêng của Toolkit1 đã bỏ
     - [T1 API232 tr.8] [T1 APIDIFF:30-32] [T1 APIDIFF:49-62]

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 62
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 18
   * - ``OPL``
     - T1
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`. Số trang là số trang PDF
     - 4
   * - ``EX``
     - T1
     - Ví dụ và changelog trong SDK. ``examples/...`` và ``changelog-2.3.2.txt`` (trong ``doc/``) tính từ ``3rdparty/rknn-toolkit2/rknn-toolkit2/``. ``CHANGELOG.md`` nằm ở ``3rdparty/rknn-toolkit2/``. Số sau dấu hai chấm là số dòng
     - 27
   * - ``OPSUP``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/RKNNToolKit2_OP_Support-2.3.2.md``
     - 1
   * - ``APIDIFF``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/RKNNToolKit2_API_Difference_With_Toolkit1-2.3.2.md``
     - 4

Số trang UG232 và API232 là số trang PDF, trùng số in. Hình Figure 3-1 và Figure 1-2 lấy từ UG232 và nằm ở ``_assets/img/02-nen-tang-rk3588/03-toolchain-runtime/luong-onnx-sang-rknn/``.
