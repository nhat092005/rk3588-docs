:tocdepth: 1

************************************
Kiến trúc và các khối cấu thành YOLO
************************************

.. admonition:: Tóm tắt

   - YOLOv8n dùng C2f và SPPF với Detect có reg_max 16 (có DFL), còn YOLO26n dùng C3k2, SPPF, C2PSA với Detect có reg_max: 1 (không DFL) và end2end: True trong yaml.
   - Sau khi fuse (nc=5), YOLOv8n có 3,006,623 tham số và 8.087 GFLOPs, YOLO26n có 2,375,811 tham số và 5.314 GFLOPs [T1 tính].
   - YOLO26n có 2 khối attention (C2PSA ở lớp 10, C3k2 ở lớp 22) cho 4 MatMul và 2 Softmax trong ONNX, và 8 depthwise 3x3 mà YOLOv8n không có.
   - Nhánh lớp dùng depthwise chỉ xuất hiện khi yaml có C3k2, A2C2f hoặc C2fCIB vì cờ legacy bị đặt False [T1 ULT nn/tasks.py].
   - Về nhánh mặc định của YOLO26, YOFF tr.6 và UDOC mâu thuẫn nhau. đường RKNN dùng nhánh một-nhiều bất kể mặc định.
   - FLOPs của YOLO26n: chú thích yaml ghi 6.1 còn get_flops ra 6.240, và phép thop ở 32x32 không tính đúng phần attention [T1].

.. _91-so-sánh-tổng-quan:

So sánh tổng quan
=================

.. list-table::
   :header-rows: 1

   * - Hạng mục
     - YOLOv8n
     - YOLO26n
     - Nguồn
   * - Hệ số co giãn ``n`` (depth, width, max_channels)
     - 0.33, 0.25, 1024
     - 0.50, 0.25, 1024
     - ULT ``cfg/models/v8/yolov8.yaml:11``, ``cfg/models/26/yolo26.yaml:13``
   * - Khối backbone
     - ``C2f``, ``SPPF``
     - ``C3k2``, ``SPPF`` (đối số ``5, 3, True``), ``C2PSA``
     - yaml ``v8:22-29``, ``26:24-32``
   * - Khối neck
     - ``C2f``
     - ``C3k2`` (cuối cùng ở P5 có cờ attention)
     - yaml ``v8:35-47``, ``26:38-50``
   * - Đầu
     - ``Detect``, ``reg_max`` 16 (có DFL), mặc định ``end2end`` tắt
     - ``Detect``, ``reg_max: 1`` (không DFL), ``end2end: True``
     - yaml ``26:9-10``. ULT ``nn/modules/head.py:107-138``
   * - Tham số, ``nc=80``, chưa fuse
     - 3,157,200
     - 2,572,280
     - T1 tính (``flops_check.py``), khớp chú thích trong yaml
   * - Tham số, ``nc=5``, đã fuse, đường xuất RKNN
     - 3,006,623
     - 2,375,811
     - T1 tính (``layer_table.py``)
   * - GFLOPs, 640x640, ``nc=5``, đã fuse
     - 8.087
     - 5.314
     - T1 tính
   * - GFLOPs, ``nc=80``: chưa fuse, như dựng ban đầu / đã fuse
     - 8.855 / 8.744
     - 6.240 / 5.480
     - T1 tính (``get_flops``), chú thích yaml ghi 8.9 và 6.1
   * - Tham số và FLOPs của riêng đầu (``nc=5``, đã fuse)
     - 751,519 và 2.965
     - 120,443 và 0.435
     - T1 tính
   * - Conv trong ONNX (số này không phụ thuộc opset hay simplify): 1x1 / 3x3 s1 / 3x3 s2 / depthwise 3x3
     - 25 / 32 / 7 / 0
     - 55 / 32 / 7 / 8
     - T1 tính (``structure_and_ops.py``)
   * - Số lần có attention (``MatMul``, ``Softmax``)
     - 0 (chỉ 1 ``Softmax`` của DFL)
     - 2 (``C2PSA`` ở lớp 10, ``C3k2`` ở lớp 22)
     - T1 tính, 4 ``MatMul``, 2 ``Softmax`` trong ONNX

Về FLOPs của YOLO26n: chú thích yaml (6.1) không khớp với ``get_flops`` của chính ultralytics (6.240 khi chưa fuse và còn cả hai đầu, 5.480 khi fuse và chỉ giữ một đầu), chú thích yaml khớp phép tính thop ở ảnh 32x32 rồi nhân (640/32)^2 (6.117 khi chưa fuse, 8.855 cho YOLOv8n. T1 tính bằng ``thop``), còn ``get_flops`` ở 640x640 cho 6.240. Chênh 0.123 giữa hai cách khớp với chú thích trong mã nguồn: "Attention costs are quadratic in image area, so disable THOP's affine proxy" (ULT ``utils/torch_utils.py:656-661``), tức ``get_flops`` bỏ phép ngoại suy theo diện tích khi model có attention, phép thop ở 32x32 nhân (640/32)^2 vì vậy không tính đúng phần attention [T1]. Con số tương ứng với đồ thị triển khai là 5.480 (``nc=80``) hoặc 5.314 (``nc=5``) ở 640x640 thật. Y26B ghi chú ở Bảng 4 (tr.17): "Parameter counts and FLOPs denote the fused inference architecture, which merges Conv/BatchNorm layers and removes the auxiliary one-to-many detection head used during training." [T2 Y26B tr.17]. Số 2.4M tham số của YOLO26n (Y26A Bảng 2 tr.8) và 3.2M của YOLOv8n (YEVO Bảng 3 tr.12) khớp số tham số bản đã fuse, 8.7 B FLOPs của YOLOv8n khớp 8.744. Số 5.4 B của YOLO26n khớp phép thop 32x32 đã fuse (5.357), không khớp 5.480 của ``get_flops`` ở 640x640 (làm tròn 5.5).

--------------

.. _92-khối-cấu-thành:

Khối cấu thành
==============

.. _921-c2f-yolov8n-và-c3k2-yolo26n:

``C2f`` (YOLOv8n) và ``C3k2`` (YOLO26n)
---------------------------------------

- ``C2f``: ``cv1`` (1x1) tạo ``2c`` kênh, tách đôi, mỗi ``Bottleneck`` đọc nửa cuối, nối tất cả rồi ``cv2`` (1x1) [T1 ULT ``nn/modules/block.py:313-315``]. ``Bottleneck`` của ``C2f`` dùng hai conv 3x3 [ULT ``block.py:309``, cấu trúc in từ model dựng: ``Conv2d(16,16,3x3)`` hai lần ở lớp 2 của YOLOv8n].
- ``C3k2`` kế thừa ``C2f``, chỉ thay phần tử trong ``self.m`` [ULT ``block.py:1072-1109``]: nếu ``attn`` thì ``Sequential(Bottleneck, PSABlock)`` (dòng 1100-1104), nếu ``c3k`` thì ``C3k`` (dòng 1105-1106), còn lại là ``Bottleneck``.
- Trong YOLO26n: lớp 2 và 4 dùng ``C3k2`` với ``c3k=False``, ``e=0.25``, lớp 6, 8 và các khối neck lớp 13, 16, 19 dùng ``c3k=True``, lớp 22 dùng ``[1024, True, 0.5, True]`` nên ``attn=True`` [yaml ``26:24-50``]. Vì ``attn`` được xét trước ``c3k``, lớp 22 là ``Bottleneck`` rồi ``PSABlock``, không phải ``C3k``.
- Bottleneck của ``C3k2`` ở lớp 2 giảm kênh (3x3: 16 xuống 8, rồi 8 lên 16, cấu trúc in từ model dựng), khác ``C2f`` giữ nguyên số kênh.
- ``C3k`` lớp 6 và 8 có ``cv1``, ``cv2``, ``cv3`` (1x1) và 2 ``Bottleneck`` (3x3) (cấu trúc in từ model dựng, ``structure_and_ops.log``).
- Hệ quả đếm: cùng số conv 3x3 stride 1 (32) và stride 2 (7), YOLO26n có nhiều conv 1x1 hơn (55 so với 25) [T1 tính].

.. _922-sppf:

``SPPF``
--------

Cả hai model dùng ``SPPF`` với ``MaxPool2d(kernel 5, stride 1, padding 2)`` lặp ``n`` lần (mặc định 3) rồi nối [ULT ``block.py:231-240``]. YOLO26n truyền thêm ``shortcut=True``.``self.add = shortcut and c1 == c2`` (dòng 233), nên khi số kênh vào bằng ra thì có cộng residual (dòng 240) [yaml ``26:31``]. Ở YOLOv8n không có đối số này nên không có residual.

.. _923-c2psa-psablock-attention-chỉ-yolo26n:

``C2PSA``, ``PSABlock``, ``Attention`` (chỉ YOLO26n)
----------------------------------------------------

- ``C2PSA``: ``cv1`` (1x1) tách đôi, một nửa qua ``PSABlock``, nối lại rồi ``cv2`` (1x1) [ULT ``block.py:1444-1496``]. Số đầu attention là ``max(c // 64, 1)`` (dòng 1483).
- ``PSABlock``: ``x = x + attn(x)`` rồi ``x = x + ffn(x)`` (dòng 1384-1385), ``ffn`` là hai conv 1x1 (dòng 1372).
- ``Attention``: ``qkv`` (conv 1x1, không activation), ``pe`` (**depthwise 3x3**, ``g=dim``, dòng 1311), ``proj`` (conv 1x1). Tính ``attn = ((q * scale).transpose(-2,-1) @ k).softmax(dim=-1)`` rồi ``v @ attn.transpose(-2,-1)`` cộng ``pe(v)`` (dòng 1333-1334) [T1].
- Ở đầu vào 640x640, hai khối attention hoạt động trên lưới P5 20x20, tức 400 token, trong khối in ra: ``qkv`` 128 vào, 256 ra, ``pe`` 128 kênh depthwise [cấu trúc in, ``structure_and_ops.log``].
- Hai khối attention (lớp 10 và lớp 22) cho 4 ``MatMul`` và 2 ``Softmax`` trong ONNX [T1 tính, mọi thiết lập ở :ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`].

.. _924-đầu-detect:

Đầu ``Detect``
--------------

.. list-table::
   :header-rows: 1

   * - Thuộc tính
     - YOLOv8n (``legacy=True``)
     - YOLO26n (``legacy=False``)
   * - Nhánh hộp
     - Conv3x3 (cin vào 64), Conv3x3 (64), Conv1x1 ra 64 kênh = 4 x ``reg_max`` 16
     - Conv3x3 (cin vào 16), Conv3x3 (16), Conv1x1 ra 4 kênh = 4 x ``reg_max`` 1
   * - Giải mã hộp
     - Qua ``DFL`` (Conv1x1 16 kênh trên softmax 16 bin)
     - ``dfl`` là ``nn.Identity()``
   * - Nhánh lớp
     - Conv3x3 (cin vào 64), Conv3x3 (64), Conv1x1 ra ``nc``
     - ``DWConv`` 3x3 + Conv1x1, hai lần, rồi Conv1x1 ra ``nc``
   * - Nguồn
     - ULT ``head.py:122-137``, ``nn/tasks.py:2011``
     - cùng, ``nn/tasks.py:2126-2127, 2169``

- Cờ ``legacy`` mặc định ``True`` [ULT ``nn/tasks.py:2011``] và bị đặt ``False`` khi yaml có ``C3k2`` (dòng 2126-2127), ``A2C2f`` (2130-2131) hoặc ``C2fCIB`` (2134-2135) [ULT ``nn/tasks.py``], vì vậy nhánh lớp dùng depthwise chỉ xuất hiện ở model có một trong các khối đó (YOLO26n có ``C3k2``).
- ``self.dfl = DFL(self.reg_max) if self.reg_max > 1 else nn.Identity()`` [ULT ``head.py:138``].
- Khi ``end2end``, đầu sao chép ``cv2`` và ``cv3`` thành ``one2one_cv2`` và ``one2one_cv3`` [ULT ``head.py:140-142``].``fuse()`` xóa nhánh không dùng khi suy luận [ULT ``head.py:280-285``].
- Suy luận: ``forward`` chạy nhánh một-nhiều rồi nhánh một-một nếu có (dòng 179-187), giải mã hộp bằng ``_inference`` (dòng 195-206), và nếu ``end2end`` thì gọi thêm ``postprocess`` (dòng 190-192) gồm ``split``, hai lần ``topk`` qua ``_grouped_topk`` và ``gather`` (dòng 241-278) [T1].
- Hình S2 của YOFF (tr.23) vẽ đầu ``Detect`` gồm nhánh một-nhiều (nhãn "train-only (topk=10)") và nhánh một-một (nhãn "inference (topk=1, NMS-free)"), cả hai có nhánh hộp ``Conv -> Conv -> 1x1`` và nhánh lớp ``(DWConv + Conv) x2 -> 1x1``, khớp mã nguồn (mục trên). Hình S1 (tr.23) ghi khối cuối của neck là ``C3k2 / 1024, e=0.5, / attn=True``, khớp ``yolo26.yaml:50``. Tr.11 §4.2: "We further apply a light backbone/neck refinement by inserting one additional attention layer in the detection neck, which improves accuracy while keeping latency essentially unchanged." [T2 YOFF tr.11, tr.23]
- Về nhánh mặc định, YOFF và UDOC mâu thuẫn: YOFF tr.6 viết "One-to-One Head (default)" và tr.6 cũng viết nhánh một-nhiều "uses NMS at inference and typically yields slightly higher accuracy". UDOC (``ultralytics_docs_models_yolo26.txt`` dòng 81, 142, 156) viết "The default one-to-many path uses NMS for accuracy" và "Prediction and validation default to the one-to-many head for accuracy". Đường RKNN dùng nhánh một-nhiều bất kể mặc định (:ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`).
- T2: "By removing the computational burden of DFL and adopting a native one-to-one prediction head, YOLO26 achieves deterministic inference times" [T2 Y26B tr.5]."One of the most significant architectural simplifications in YOLO26 is the removal of the Distribution Focal Loss (DFL) module" [T2 Y26A tr.6]."YOLO26 fundamentally redesigns the prediction head to produce direct, non-redundant bounding box predictions without the need for NMS" [T2 Y26A tr.7].

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
   * - ``Y26B``
     - T2
     - :download:`yolo26_nmsfree_2026chakrabarty.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_nmsfree_2026chakrabarty.pdf>`
     - 2
   * - ``Y26A``
     - T2
     - :download:`yolo26_arch_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_arch_2025sapkota.pdf>`
     - 2
   * - ``ULT``
     - T1
     - ultralytics (gói Python, mã nguồn)
     - 1
   * - ``YOFF``
     - T2
     - :download:`yolo26_official_2026jocher.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_official_2026jocher.pdf>`
     - 1
