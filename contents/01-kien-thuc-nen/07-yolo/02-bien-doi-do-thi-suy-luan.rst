:tocdepth: 1

**************************************
Biến đổi đồ thị suy luận từ huấn luyện
**************************************

.. admonition:: Tóm tắt

   - Phần huấn luyện chỉ đổi đồ thị xuất ở chỗ bỏ DFL và đầu một-một. ProgLoss, STAL và MuSGD không đổi đồ thị suy luận theo mô tả của paper.
   - Nhánh một-nhiều của YOLO26n đạt mAP50-95 40.9 và nhánh một-một 40.1 trên COCO val ở FP32 [T2 YOFF Bảng 7 tr.14], chất lượng sau INT8 và trên dữ liệu PPE là unknown.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _96-phần-huấn-luyện-chỉ-ở-chỗ-nó-đổi-đồ-thị:

Phần huấn luyện chỉ ở chỗ nó đổi đồ thị
=======================================

Chỉ chép nguyên văn câu định nghĩa, không giải thích thêm.

.. list-table::
   :header-rows: 1

   * - Thay đổi
     - Nguyên văn
     - Có đổi đồ thị xuất ra không
   * - Bỏ DFL
     - "YOLO26 reverts to a Direct Regression Strategy, removing this module entirely (see Fig. 4)." [T2 Y26B tr.8]
     - Có: bỏ ``Reshape``, ``Transpose``, ``Softmax``, Conv1x1 của DFL.``reg_max`` 1 (T1 :ref:`Đầu Detect <924-đầu-detect>`)
   * - Đầu một-một
     - "By redesigning the prediction head to support one-to-one label assignment [24], the model learns to output a single, definitive box per object instance during training." [T2 Y26B tr.7]
     - Có, nhưng không bật ở đường xuất mặc định (:ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`)
   * - ProgLoss, STAL
     - "ProgLoss adaptively reweights objectives to prevent domination by easy examples late in training, while STAL prioritizes assignment for tiny or occluded instances" [T2 Y26A tr.4]
     - Không đổi đồ thị suy luận theo mô tả của paper, chưa đọc mã loss
   * - MuSGD
     - "the introduction of the MuSGD optimizer (Figure 4d), which combines the strengths of Stochastic Gradient Descent (SGD) with the recently proposed Muon optimizer" [T2 Y26A tr.7]
     - Không

Mã nguồn tự chọn hàm mất mát: ``E2ELoss`` khi đầu có ``one2one_cv2``, ngược lại ``v8DetectionLoss`` (T1 ``nn/tasks.py:604``), nên huấn luyện YOLO26n chỉ cần dùng ``yolo26.yaml``. Tổng hợp của file này: trọng số YOLOv8n không dùng lại được cho YOLO26n vì khối và đầu khác nhau (:ref:`Khối cấu thành <92-khối-cấu-thành>`), và đầu YOLO26n có hai nhánh (một-một và một-nhiều) cùng tồn tại trong lúc huấn luyện (T1 ``head.py:140-142``. T2 Y26B tr.17 gọi nhánh một-nhiều là "auxiliary ... used during training"). Đường RKNN dùng chính nhánh một-nhiều. YOFF (chú thích Bảng 7, tr.14) viết: "'mAP' denotes standard validation of the one-to-many branch with NMS ('end2end=False'), whereas 'mAP (E2E)' denotes true end-to-end validation of the default one-to-one branch." Vậy với YOLO26n trên COCO val, nhánh một-nhiều có mAP50-95 là 40.9 và nhánh một-một là 40.1 (YOFF Bảng 7 tr.14, trùng Y26A và Y26B). YEVO Bảng 3 tr.12 ghi 39.8 và 40.3 (khác số và chiều ngược), nên không dùng. Đây là mAP PyTorch ở FP32 trên COCO, chất lượng nhánh một-nhiều sau lượng tử hóa INT8 và trên dữ liệu PPE chưa đo (``unknown``).

Y26B tr.8 cũng viết: "On specialized edge hardware (NPUs and DSPs), these Softmax layers are notoriously difficult to quantize and often become the primary latency bottleneck [30]", trích một bài khảo sát lượng tử hóa chung, không phải phép đo trên YOLO hay RKNN [T2 Y26B tr.8, ghi chú độ tin cậy ở đầu file]. Dùng như giả thuyết, không như kết quả.

--------------


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
     - 3
   * - ``Y26A``
     - T2
     - :download:`yolo26_arch_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_arch_2025sapkota.pdf>`
     - 2
