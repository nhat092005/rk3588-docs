:tocdepth: 1

***********
Đồ thị xuất
***********

.. admonition:: Tóm tắt

   - Mặc định nms là None nên end2end = False cho mọi định dạng: YOLO26n xuất ra đầu ra [1, 9, 8400] và cần NMS ngoài đồ thị [T1 ULT engine/exporter.py:682-688].
   - Đường RKNN của repo không truyền nms nên end2end tắt. ONNX thật đưa vào onnx2rknn có thêm _NormalizeCoords nên khác bảng (B) ở Concat, Slice và Div.
   - Đo T3 board trên YOLOv8n (nc=5): bảng lớp có 119 lớp, gồm InputOperator và OutputOperator, ngoài hai op đó, op duy nhất chạy CPU là 1 Transpose gắn với DFL, các lớp còn lại chạy NPU.
   - OPSUP liệt kê TopK là "Not Supported" ở mức toolkit. OPL không có mục NPU cho TopK, GatherElements, Mod, ReduceMax, Equal, Cast, Flatten.
   - Ultralytics đo YOLO26n trên Radxa Rock 5B (RK3588): FP16 58.5 ms, INT8 41.2 ms trên COCO128, không so trực tiếp được với eval_perf của repo vì phương pháp đo khác và điều kiện không rõ.

Đồ thị xuất và đường RKNN
=========================

- Mặc định ``nms`` là ``None`` (ULT ``cfg/default.yaml:61``), nên ``model.end2end = self.args.nms is False`` (ULT ``engine/exporter.py:683``) đặt ``end2end = False`` cho mọi định dạng: YOLO26n xuất ra dùng nhánh một-nhiều, đầu ra ``[1, 9, 8400]`` (4 hộp + 5 lớp), cần NMS ngoài đồ thị. Chỉ khi truyền ``nms=False`` thì end2end bật (đầu ra ``[1, 300, 6]``), và với ``rknn`` các dòng 684-688 tắt lại vì "formats without top-k support" [T1 ULT ``engine/exporter.py:682-688``]. Đường RKNN của repo (``ai/core/rknn/baseline.py``) không truyền ``nms``, nên end2end tắt.``metadata.yaml`` của YOLO26n xuất qua repo ghi ``end2end: false`` (T3 PC).
- Đường xuất RKNN của repo: ``export(format="rknn")`` ghi ``dataset.txt`` rồi ``onnx2rknn`` với ``mean=[0,0,0]``, ``std=[255,255,255]`` (``ai/core/rknn/baseline.py``, ULT ``engine/exporter.py:1532-1563``, trong đó ``dataset.txt`` chỉ ghi khi ``quantize == 8`` (dòng 1543-1552).``utils/export/rknn.py:74``).
- OPSUP liệt kê ``TopK`` là "Not Supported" ở mức toolkit (dòng 189). OPL không có mục NPU cho ``TopK``, ``GatherElements``, ``Mod``, ``ReduceMax``, ``Equal``, ``Cast``, ``Flatten``, chỉ có mục CPU ở chương 4 (xem :ref:`Op không có mục NPU trong OPL <953-op-không-có-mục-npu-trong-opl>`).

Danh sách op trong ONNX xuất qua đúng ``Exporter`` của Ultralytics (``YOLO(...).export(format="onnx")``, 640x640, batch 1, ``nc=5``, trọng số ngẫu nhiên. T1 tính bằng ``ops_via_exporter.py``, ``Identity`` và ``Constant`` không liệt kê). ``Exporter`` đặt ``C2f.forward = forward_split`` (ULT ``engine/exporter.py:908-910``: điều kiện ``isinstance(m, C2f) and not is_tf_format`` ở dòng 908, phép gán ở dòng 910.``C3k2`` kế thừa ``C2f``) nên số ``Split`` và ``Slice`` khác với xuất trực tiếp bằng ``torch.onnx.export``. Hai thiết lập:

**(B) Đường xuất mặc định của repo:** opset ``min(opset or 19, 19)`` (ULT ``engine/exporter.py:1536-1538``), ``simplify: True`` (ULT ``cfg/default.yaml:90``) chạy ``onnxslim`` (ULT ``engine/exporter.py:1134-1139``).

.. list-table::
   :header-rows: 1

   * - Op
     - YOLOv8n
     - YOLO26n (``end2end`` tắt, mặc định)
     - YOLO26n (``nms=False``, ``end2end`` bật)
   * - Conv
     - 64
     - 102
     - 102
   * - Mul / Sigmoid
     - 58 / 58
     - 90 / 88
     - 90 / 88
   * - Add / Sub / Div
     - 8 / 2 / 1
     - 22 / 2 / 1
     - 21 / 1 / 1
   * - Concat / Slice / Split
     - 17 / 2 / 8
     - 23 / 2 / 11
     - 24 / 2 / 12
   * - Reshape / Transpose
     - 8 / 1
     - 12 / 4
     - 12 / 5
   * - MaxPool / Resize
     - 3 / 2
     - 3 / 2
     - 3 / 2
   * - Softmax / MatMul
     - 1 / 0
     - 2 / 4
     - 2 / 4
   * - TopK / GatherElements / ReduceMax / Mod / Flatten / Cast / Expand / Unsqueeze
     - 0
     - 0
     - 2 / 3 / 1 / 1 / 1 / 1 / 2 / 4

**Đường RKNN thật khác bảng (B) một chút.** Với ``format="rknn"``, ``quantize=8`` và ``end2end`` tắt, ``Exporter`` bọc thêm ``_NormalizeCoords`` (chia 4 tọa độ hộp cho ``[w, h, w, h]``, rồi slice và concat) trước khi xuất ONNX [T1 ULT ``engine/exporter.py:1100-1117``, ``utils/export/engine.py:17-48``]. ONNX thật đưa vào ``onnx2rknn`` (opset 19. T1 tính, bắt file trước ``onnx2rknn``) khác bảng (B) ở ba op: YOLOv8n ``Concat`` 18, ``Slice`` 4, ``Div`` 2. YOLO26n (``end2end`` tắt) ``Concat`` 24, ``Slice`` 4, ``Div`` 2, các op còn lại giống bảng (B). Bảng (B) đúng cho ``format="onnx"``.

**(A) Opset 12, chưa simplify:** thiết lập của các phép đo T3 board trước (``build_variants.py``, ``build_noadd.py``, ``build_trained.py``).

.. list-table::
   :header-rows: 1

   * - Op
     - YOLOv8n
     - YOLO26n (``end2end`` tắt)
     - YOLO26n (``nms=False``, ``end2end`` bật)
   * - Conv
     - 64
     - 102
     - 102
   * - Mul / Sigmoid
     - 60 / 58
     - 92 / 88
     - 94 / 88
   * - Add / Sub / Div
     - 9 / 2 / 2
     - 23 / 2 / 2
     - 22 / 1 / 2
   * - Concat / Slice / Split
     - 17 / 2 / 8
     - 23 / 2 / 11
     - 24 / 2 / 12
   * - Reshape / Transpose
     - 8 / 2
     - 12 / 4
     - 12 / 5
   * - MaxPool / Resize
     - 3 / 2
     - 3 / 2
     - 3 / 2
   * - Softmax / MatMul
     - 1 / 0
     - 2 / 4
     - 2 / 4
   * - Shape / Gather
     - 1 / 1
     - 1 / 1
     - 1 / 1
   * - TopK / GatherElements / ReduceMax / Mod / Flatten / Equal / Where / Cast / ConstantOfShape / Expand / Unsqueeze
     - 0
     - 0
     - 2 / 3 / 1 / 1 / 1 / 2 / 2 / 3 / 2 / 2 / 4

Đầu ra: ``[1, 9, 8400]`` ở mọi cột ``end2end`` tắt, ``[1, 300, 6]`` ở cột ``nms=False``. Cột ``nms=False`` của thiết lập (A) không do ``ops_via_exporter.py`` tạo ra, số được dựng lại độc lập ở lượt kiểm ba bằng script riêng. Hai thiết lập khác nhau ở số ``Mul``, ``Add``, ``Div``, ``Transpose`` và ở các op chỉ có trong opset 12 (``Shape``, ``Gather``, và ở cột ``end2end`` bật thêm ``Equal``, ``Where``, ``ConstantOfShape``) mà ``onnxslim`` gộp hoặc xóa. Bảng lớp RKNN đo trên board của YOLOv8n có cùng số lớp theo từng loại với bảng lớp trong ``tests/fixtures/eval_perf_2.3.2_layers.txt`` (đầu ra ``eval_perf`` 2.3.2 của pipeline, commit ``a79457a``, tham số lúc chụp không ghi lại): 57 ``ConvExSwish``, 17 ``Concat``, 9 ``Split``, 8 ``Add``, 7 ``Reshape``, 7 ``Conv``, 3 ``MaxPool``, 2 ``Sub``, 2 ``Resize``, 2 ``Mul``, 1 ``Transpose``, 1 ``Sigmoid``, 1 ``exSoftmax13``. Lưu ý: 9 lớp ``Split`` trên board tương ứng 8 ``Split`` cộng 2 ``Slice`` của ONNX (không phải 18 ``Slice``).

Đã đo trên board (T3 board, YOLOv8n, ``nc=5``, trọng số ngẫu nhiên và đã huấn luyện, ``eval_perf`` 2.3.2, đồ thị ONNX thiết lập (A) ở trên, nhật ký T3 board, các mục "Kết quả" và "Lượt 2"): bảng lớp có 119 lớp, trong đó 57 ``ConvExSwish``, 8 ``Add``, 17 ``Concat``, 9 ``Split``, 3 ``MaxPool``, 2 ``Resize``, 2 ``Mul``, 2 ``Sub``, 7 ``Reshape``, 1 ``Sigmoid``, 1 ``exSoftmax13``, 7 ``Conv`` đều chạy NPU, ngoài ``InputOperator`` và ``OutputOperator``, op duy nhất chạy CPU là 1 ``Transpose`` (tên lớp ``/model.22/dfl/Reshape_1_output_0_rs``, gắn với DFL). ONNX thiết lập (A) (opset 12 chưa simplify, dùng cho phép đo này) có 2 ``Transpose``, thiết lập (B) (opset 19 sau ``onnxslim``) có 1, và đồ thị RKNN có 1. Với YOLO26n xem :ref:`Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên) <955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên>`.

Số đo của chính Ultralytics trên RK3588 (UDOC ``ultralytics_docs_integrations_rockchip-rknn.txt`` dòng 178-194): "YOLO26 benchmarks below were run by the Ultralytics team on Radxa Rock 5B based on Rockchip RK3588 with rknn model format measuring speed and accuracy", "Benchmarked with ultralytics 8.4.60", "Validation for the above benchmarks was done using the COCO128 dataset. Inference time does not include pre/post-processing." Hàng YOLO26n (ranh giới ô đọc từ file ``.html``): FP16 7.2 MB, mAP50-95(B) 0.477, 58.5 ms. INT8 4.1 MB, 0.463, 41.2 ms. Trang không nêu tần số NPU, số lõi, runtime, batch hay nhánh dùng, mAP trên COCO128 không so được với COCO val. Trang YOLOv8 (``ultralytics_docs_models_yolov8.txt``) không có mục RKNN. Con số 41.2 ms không so trực tiếp được với phép đo ``eval_perf`` của chúng ta (:ref:`Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên) <955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên>`) vì phương pháp đo khác và không rõ điều kiện của Ultralytics.

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
   * - ``ULT``
     - T1
     - ultralytics (gói Python, mã nguồn)
     - 2
