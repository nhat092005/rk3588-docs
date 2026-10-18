:tocdepth: 1

************
Bảng A đến E
************

.. admonition:: Tóm tắt

   - Accuracy đánh giá trên tập test chung của SFCHD (1,238 ảnh) cho mọi model, riêng model Lựa chọn 2 báo thêm `shel5k_test` (500 ảnh) và `chv_test` (44 ảnh).
   - Mọi phase train 1 seed (42), Phase 10 thêm seed 43, 44. Chênh lệch dưới 1% mAP50-95 coi là chưa phân biệt được, 1% là giá trị chọn trước.
   - Table A: `sfchd_5class` có 12,372 ảnh và 48,096 instance, `sfchd_shel5k` có 17,846 ảnh và 96,753 instance. Hai lớp `head` và `self_clothes` chỉ chiếm 2.5% và 1.6% số object.
   - Table B: Ultralytics 8.4.154, PyTorch 2.4.0+cu124, 100 epoch, input 640 × 640, optimizer MuSGD (lr0 0.01, momentum 0.9) ghi tường minh trong config.
   - Table C: Orange Pi 5 với RK3588S, RKNN-Toolkit2 2.3.2, RKNPU Driver 0.9.8, còn Board cooling và Ambient condition vẫn là [TBD].
   - Table D và E (accuracy FP32, Params, GFLOPs, MACs, kích thước) mới là khung với các ô số còn [TBD].

.. contents:: Trong trang này
   :local:
   :depth: 1

..

   Phần này được thiết kế để **điền số liệu dần trong quá trình làm**. Không nhất thiết đưa tất cả bảng vào paper cuối cùng, mục 9 ghi rõ bảng nào bắt buộc.

**Quy tắc chung cho mọi bảng:**

- Mọi số đo theo Evaluation Protocol v1 (:ref:`Evaluation Protocol v1 <50-evaluation-protocol-v1>`). Protocol lên phiên bản mới thì đo lại toàn bộ bảng, không trộn số của 2 phiên bản.
- Accuracy đánh giá trên **tập test chung là tập test của SFCHD (1,238 ảnh)** cho mọi model, dù train trên Lựa chọn 1 (``sfchd_5class``) hay Lựa chọn 2 (``sfchd_shel5k``). Split của SFCHD được giữ nguyên ở cả 2 dataset, và SHEL5K/CHV đều không trùng ảnh với SFCHD (:ref:`Đề xuất Class Mapping cho Lựa chọn 2 <022-đề-xuất-class-mapping-cho-lựa-chọn-2>`, trong đó cặp CHV×SFCHD đã dHash ra 0 cặp trùng), nên tập test này sạch cho cả 2. Model Lựa chọn 2 báo thêm 2 dòng kết quả riêng: tập test SHEL5K (``shel5k_test``, 500 ảnh) và tập test CHV (``chv_test``, 44 ảnh, mới từ 2026-09-29), với mỗi domain 1 dòng, không gộp vào số chung.
- **Seed:** mọi phase train **1 seed (42)**. Phase 10 (mục 8) train thêm **seed 43, 44** cho các model của bảng so sánh chính (YOLOv8n baseline và model đề xuất), báo mean ± std. Lý do: thời gian train có hạn (YOLOv8n 100 epoch khoảng 2.25 giờ, YOLOv8s khoảng 4.72 giờ trên RTX 3050 Laptop, theo ``tmp/05_training-logs/``).

  - **Seed là gì:** số khởi tạo cho bộ sinh số ngẫu nhiên. Trong Ultralytics, ``seed`` đặt đồng thời ``random.seed``, ``np.random.seed``, ``torch.manual_seed`` (``ultralytics/utils/torch_utils.py``, hàm ``init_seeds``), nên quyết định thứ tự xáo dữ liệu, các phép augmentation ngẫu nhiên và giá trị khởi tạo của các lớp mới. Cùng seed thì train lại ra kết quả gần như giống hệt (``deterministic: True`` là mặc định). Khi đổi seed thì ra model khác, AP lệch đi một chút.
  - **Lợi ích của 3 seed:** với 1 seed, nếu model A hơn model B 0.5% mAP thì không biết đó là cải tiến thật hay chỉ do may rủi. Với 3 seed có std: chênh lệch lớn hơn std mới coi là khác biệt thật. Quan trọng nhất với ``head`` và ``self_clothes`` vì tập test chỉ có 110 và 74 instance (Table A).
  - **Hệ quả của 1 seed trước Phase 10:** chọn dataset (sau Phase 2) và chọn candidate (Phase 7) dựa trên 1 seed, chưa biết std. Mọi kết luận trước Phase 10 ghi rõ "1 seed". Chênh lệch dưới 1% mAP50-95 coi là chưa phân biệt được. Mức 1% là giá trị chọn trước (chưa có std để căn cứ), thay bằng std thật sau Phase 10.
  - **Chỉ seed train thay đổi:** split dữ liệu luôn cố định bằng seed 42 của ``scripts/data/prepare_sfchd.py``, nên mọi lần train dùng đúng cùng tập train/val/test. Seed 42 là giá trị đang dùng trong ``ai/automation/configs/*.yaml``, còn 43 và 44 là 2 giá trị kế tiếp, chọn cố định trước khi train để không bị nghi chọn seed đẹp.
  - **Căn cứ:** 4 paper PPE trong ``_assets/pdf/papers/07_ppe_detection/`` đều không báo độ lệch chuẩn. DAHD-YOLO tự nhận việc chỉ dùng 1 seed là hạn chế (:download:`dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, tr.20):

..

   "While we employed a fixed random seed to ensure reproducibility and facilitate comparisons of improvements, this approach also imposes limitations on the statistical significance of our results."

--------------

.. _table-a-dataset-summary:

Table A. Dataset Summary
========================

**Mục đích:** chứng minh dữ liệu dùng để train/test được mô tả rõ và có thể reproduce.

.. list-table::
   :header-rows: 1

   * - Dataset
     - Dùng cho
     - #Images
     - #Train
     - #Val
     - #Test
     - Classes
     - #Instances
     - Nguồn ảnh
   * - ``sfchd_5class``
     - Lựa chọn 1
     - 12,372
     - 9,897
     - 1,237
     - 1,238
     - 5 class (:ref:`Application hiện tại <01-application-hiện-tại>`)
     - 48,096
     - Camera giám sát 2 nhà máy hóa chất
   * - ``sfchd_shel5k``
     - Lựa chọn 2
     - 17,846
     - 14,284
     - 1,780
     - 1,782 (1,238 SFCHD + 500 SHEL5K + 44 CHV)
     - 5 class
     - 96,753
     - Thêm ảnh công trường xây dựng (SHEL5K) + CHV đã lọc (áo phản quang, 474/1.330 ảnh, xem :ref:`Đề xuất Class Mapping cho Lựa chọn 2 <022-đề-xuất-class-mapping-cho-lựa-chọn-2>`)
   * - External test set (optional)
     - Cross-domain
     - [TBD]
     - -
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

``#Instances`` = số object được gán nhãn (số bounding box). Một ảnh có thể chứa nhiều instance.

.. list-table::
   :header-rows: 1

   * - Ghi chú
     - Chi tiết
     - Nguồn
   * - Split SFCHD
     - 80/10/10 (8:1:1), seed 42, tự tạo
     - ``scripts/data/prepare_sfchd.py``
   * - Split SHEL5K
     - 80/10/10, seed 42, tự tạo (bản tải về không kèm split)
     - ``scripts/data/prepare_shel5k.py``, ``data/shel5k/DATA_CARD.md``
   * - Dataset 5 class
     - ``sfchd_5class`` và ``sfchd_shel5k`` giữ nguyên split của từng dataset gốc
     - ``scripts/data/prepare_sfchd_5class.py``, ``prepare_sfchd_shel5k.py``
   * - So với paper
     - Paper SFCHD chia train:test 4:1, paper SHEL5K chia 4000:1000 (không có val). Cả hai không phát hành danh sách split, nên không so trực tiếp được với số của paper
     - :download:`sfchd_scale_2023yu.pdf <../../_assets/pdf/papers/07_ppe_detection/sfchd_scale_2023yu.pdf>` tr.1, và :download:`shel5k_helmet_2022otgonbold.pdf <../../_assets/pdf/papers/07_ppe_detection/shel5k_helmet_2022otgonbold.pdf>` tr.8
   * - Số ảnh SFCHD
     - Paper ghi 12,373, bản tải về có 12,372 (lệch 1 ảnh)
     - paper SFCHD tr.1, ``data/sfchd/DATA_CARD.md``
   * - Class
     - Bỏ ``blur_head``, ``blur_clothes`` của SFCHD
     - :ref:`Dataset <02-dataset>`
   * - Số instance
     - Đếm trực tiếp từ file nhãn
     - ``data/<dataset>/processed/labels/``

Class distribution trên tập test chung (SFCHD)
----------------------------------------------

.. list-table::
   :header-rows: 1

   * - Class
     - Train Instances
     - Val Instances
     - Test Instances
     - Total
     - Percentage
   * - person
     - 13,624
     - 1,697
     - 1,688
     - 17,009
     - 35.4%
   * - helmet
     - 11,442
     - 1,446
     - 1,409
     - 14,297
     - 29.7%
   * - head
     - 987
     - 102
     - 110
     - 1,199
     - 2.5%
   * - safety_clothes
     - 11,846
     - 1,507
     - 1,459
     - 14,812
     - 30.8%
   * - self_clothes
     - 641
     - 64
     - 74
     - 779
     - 1.6%
   * - **Tổng**
     - **38,540**
     - **4,816**
     - **4,740**
     - **48,096**
     - 100%

``head`` (đầu trần, không đội mũ) và ``self_clothes`` (quần áo thường) là 2 class báo vi phạm, nhưng chỉ chiếm 2.5% và 1.6% số object. Tập test chỉ có 110 và 74 object của 2 class này, nên bắt đúng hay bỏ sót 1 object đã làm recall của class đổi khoảng 0.9% và 1.4% (1/110, 1/74), so với khoảng 0.06% ở ``person`` (1/1,688). Vì vậy AP của 2 class này có thể lệch đáng kể giữa các lần train khác seed ``[suy luận, chưa đo]``. Đây là lý do bảng so sánh chính cần 3 seed ở Phase 10 (quy tắc chung đầu mục 7).

--------------

.. _table-b-training-configuration:

Table B. Training Configuration
===============================

**Mục đích:** người khác có thể train lại gần giống thí nghiệm của mình.

.. list-table::
   :header-rows: 1

   * - Item
     - Giá trị
     - Nguồn
   * - Framework
     - Ultralytics 8.4.154, PyTorch 2.4.0+cu124
     - ``.venv`` hiện tại
   * - Model / weights khởi tạo
     - YOLOv8n (``yolov8n.pt``), YOLOv8s (``yolov8s.pt``), weights pretrained chính thức của Ultralytics
     - ``ai/models/yolov8{n,s}_baseline.py``
   * - Input size
     - 640 × 640
     - ``ai/automation/configs/*.yaml``
   * - Batch size
     - 16 (YOLOv8n), 8 (YOLOv8s, cho vừa 4 GB VRAM như run cũ ``sfchd_yolov8s_100ep``)
     - ``ai/automation/configs/*.yaml``
   * - Epochs
     - 100
     - ``ai/automation/configs/*.yaml``
   * - Optimizer
     - MuSGD, lr0 0.01, momentum 0.9, ``warmup_bias_lr`` 0.0, ghi tường minh trong config
     - ``ai/automation/configs/*.yaml`` và ``ultralytics/engine/trainer.py`` ``build_optimizer``
   * - Weight decay
     - 0.0005
     - log train
   * - Data augmentation
     - Mặc định Ultralytics 8.4.154
     - ``ultralytics/cfg/default.yaml``
   * - Random seed
     - 42 cho mọi phase, thêm 43 và 44 ở Phase 10 cho model chính
     - quy tắc chung mục 7
   * - Train GPU
     - NVIDIA GeForce RTX 3050 Laptop (3762 MiB)
     - log train ``tmp/05_training-logs/``
   * - Dataset
     - ``sfchd_5class`` hoặc ``sfchd_shel5k``
     - Table A

- Config ghi đúng những gì ``optimizer=auto`` tự chọn, để kết quả không phụ thuộc logic tự chọn này (có thể đổi theo version):

  - ``auto`` chọn MuSGD (lr 0.01, momentum 0.9) khi số iteration > 10,000, còn lại AdamW (``build_optimizer``).
  - Số iteration = ``ceil(số ảnh train / max(batch, nbs=64)) × epochs`` (``engine/trainer.py`` dòng 312), cụ thể: ``sfchd_5class`` = 155 × 100 = 15,500, còn ``sfchd_shel5k`` = 224 × 100 = 22,400 (train 14,284 ảnh sau khi thêm CHV đã lọc, xem :ref:`Đề xuất Class Mapping cho Lựa chọn 2 <022-đề-xuất-class-mapping-cho-lựa-chọn-2>`, ``ceil(14284/64)=224``). Cả hai đều vượt ngưỡng, kể cả YOLOv8s batch 8 (vì dùng ``max(batch, 64)``).
  - ``auto`` còn tự đặt ``warmup_bias_lr = 0.0`` (mặc định 0.1), nên config ghi cả tham số này.
  - Log train 1 epoch ngày 2026-09-26 xác nhận: ``optimizer: MuSGD(lr=0.01, momentum=0.9)``, ``warmup_bias_lr=0.0``.

- Các run cũ 7 class được train bằng PyTorch 2.6.0 (log train), khác môi trường hiện tại nên không dùng lại số của chúng.

--------------

.. _table-c-hardware--software-environment:

Table C. Hardware / Software Environment
========================================

**Mục đích:** latency phụ thuộc rất mạnh vào board, OS, runtime và version.

.. list-table::
   :header-rows: 1

   * - Item
     - Configuration
   * - Board
     - Orange Pi 5 (``/proc/device-tree/model``)
   * - SoC
     - RK3588S
   * - RAM
     - 4 GB (hệ điều hành thấy 3,916 MiB)
   * - Accelerator
     - NPU, 3 NPU core
   * - OS
     - Orange Pi 1.2.4 Jammy (Ubuntu 22.04.5 LTS)
   * - Kernel
     - 6.1.99-rockchip-rk3588
   * - Python trên board
     - 3.10.12 (``.venv-board``)
   * - RKNN-Toolkit2 (PC)
     - 2.3.2
   * - RKNN-Toolkit-Lite2 (board)
     - 2.3.2
   * - librknnrt
     - 2.3.2
   * - RKNPU Driver
     - 0.9.8
   * - ONNX Runtime (CPU board, Table H)
     - 1.23.2
   * - numpy / OpenCV trên board
     - 1.26.4 / 4.11.0 (cùng version với PC)
   * - Tần số tối đa
     - CPU A55 1.8 GHz, A76 2.256 / 2.304 GHz, NPU 1 GHz, DDR 2112 MHz
   * - Governor mặc định
     - CPU ``ondemand``, NPU ``rknpu_ondemand``, DDR ``dmc_ondemand``
   * - Governor khi đo
     - ``performance`` cho CPU, NPU, DDR (``ai/board/lock_freq.sh``, :ref:`Hardware Performance <53-hardware-performance>`). Sau tầng 1, NPU và DDR ở ``userspace``, tần số tối đa (do ``eval_perf(fix_freq=True)``)
   * - NPU thermal zone
     - ``thermal_zone6`` (``npu-thermal``)
   * - Camera
     - OV13855
   * - Camera format
     - NV12
   * - Camera resolution
     - 1920 × 1080
   * - Model input
     - 640 × 640
   * - NPU core config
     - Theo từng thí nghiệm (Table I)
   * - Board cooling
     - [TBD]
   * - Ambient condition
     - [TBD]

Nguồn: librknnrt, ``rknn_server`` và API 2.3.2 verify qua ``get_sdk_version()`` (``tmp/04_debug-logs/2026-09-18_board-bringup-log.md``). Các dòng còn lại đọc trực tiếp trên board ngày 2026-09-26: RKNN-Toolkit-Lite2 và driver từ log ``init_runtime`` (``RKNN Driver Information, version: 0.9.8``) và ``get_sdk_version()`` (``API: 2.3.2``, ``DRV: 0.9.8``). OS đọc từ ``/etc/os-release``. Các thông số RAM, governor, tần số, thermal zone từ ``/proc`` và ``/sys``. Mỗi file kết quả tầng 2 tự ghi lại các thông tin này (``system``, ``sdk_version``, ``frequency_before/after``), nên nếu board đổi firmware thì thấy ngay trong kết quả. Model input 640×640 là default Ultralytics (paper SHEL5K không nêu kích thước input). Paper SFCHD tự dùng 1333×800 (tr.9) nên không so trực tiếp được với số của paper SFCHD.

--------------

.. _table-d-baseline-accuracy-fp32:

Table D. Baseline Accuracy (FP32)
=================================

**Mục đích:** accuracy gốc trước mọi tối ưu. FP32 PyTorch, tập test chung SFCHD (1,238 ảnh). Dùng seed 42. Dòng nào có Phase 10 thì báo mean ± std qua 3 seed. Bảng sinh tự động: ``results/<ds>/table_D_fp32.md``.

.. list-table::
   :header-rows: 1

   * - Model
     - Train trên
     - Precision
     - Recall
     - mAP50
     - mAP50-95
     - AP person
     - AP helmet
     - AP head
     - AP safety_clothes
     - AP self_clothes
   * - YOLOv8n
     - Lựa chọn 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8n
     - Lựa chọn 2
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - Lựa chọn 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - Lựa chọn 2
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLO11n
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLO11s
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Proposed
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

Model train trên Lựa chọn 2 báo thêm 2 dòng: tập test SHEL5K (500 ảnh) và tập test CHV (44 ảnh, mới), cùng các cột, ghi rõ mỗi dòng là tập test khác nhau.

--------------

.. _table-e-model-complexity:

Table E. Model Complexity
=========================

.. list-table::
   :header-rows: 1

   * - Model
     - Params (M)
     - GFLOPs
     - MACs (G)
     - ONNX FP32 Size (MB)
     - RKNN Size (MB)
   * - YOLOv8n
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLO11n
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLO11s
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Proposed
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

Đo theo :ref:`Model Complexity <52-model-complexity>`: model đã fuse, input 640×640, MACs = GFLOPs / 2. Không dùng kích thước file ``.pt`` vì Ultralytics lưu ``best.pt`` ở FP16.
