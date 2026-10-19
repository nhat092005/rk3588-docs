:tocdepth: 1

*********************
Class mapping 5-class
*********************

.. admonition:: Tóm tắt

   - Quyết định mới (2026-09-29): đưa CHV vào Option 2 sau khi lọc, vì dHash thật chỉ tìm 4 cặp trùng CHV × SHEL5K và 0 cặp CHV × SFCHD.
   - `vest` của CHV gộp vào `safety_clothes` thay vì tách class thứ 6, và CHV được lọc bằng điều kiện `person_count ≤ positive_class_count`, còn 474 ảnh.
   - 5 class cuối gồm 96.753 instance: `person` 38.103, `helmet` 34.651, `head` 7.319, `safety_clothes` 15.901, `self_clothes` 779.
   - `self_clothes` chỉ có nhãn từ SFCHD. SHEL5K không có class này nên dạy model "không có" một cách chủ động, hướng loss masking chưa implement.
   - Bị loại khỏi taxonomy: `head_with_helmet`, `face`, `blur_head`, `blur_clothes` và toàn bộ SH17.
   - Test tách riêng: `sfchd_test` 1.238 ảnh là tập chung, `shel5k_test` 500 ảnh và `chv_test` 44 ảnh chỉ báo cáo thêm cho Lựa chọn 2.

.. _022-đề-xuất-class-mapping-cho-lựa-chọn-2:

Đề xuất Class Mapping cho Lựa chọn 2
====================================

Ràng buộc: ``ai/core/dataset.py`` dùng ``dataset.yaml`` kiểu Ultralytics chuẩn (flat class list, 1 nhãn/box, không hỗ trợ multi-attribute). Mọi thông tin muốn giữ phải nằm gọn trong 1 tên class duy nhất.

**Đính chính (2026-09-29):** bản trước của mục này loại **toàn bộ** CHV, lý do chính là "trùng ảnh gốc đã xác nhận với SHEL5K", nhưng không có script/log verify kèm theo trong repo tại thời điểm viết. Đã chạy dHash 64-bit thật (cùng phương pháp/ngưỡng hamming ≤5 dùng cho SHEL5K×SFCHD ở dưới): CHV(1.330 ảnh) × SHEL5K(5.000 ảnh) → **chỉ 4 cặp trùng thật** (xác nhận bằng mắt, ví dụ ``ppe_0754.jpg``/``hard_hat_workers774.png``, ảnh giống hệt). Kết quả so khớp CHV × SFCHD(12.372 ảnh) → **0 cặp trùng**. Rủi ro trùng ảnh có thật nhưng rất nhỏ (0,3% số ảnh CHV), nên có thể xử lý bằng cách bỏ ảnh trùng mà không cần loại cả dataset. License annotation CHV vẫn không ghi rõ (``data/chv/DATA_CARD.md``) nhưng dự án chấp nhận rủi ro này cho mục đích nghiên cứu/đồ án. Quyết định mới: **đưa CHV vào Option 2**, sau khi lọc kỹ. Chi tiết đầy đủ (dHash, kỹ thuật lọc, bằng chứng ảnh, cơ chế lỗi label): ``tmp/02_decisions/2026-09-29_ppe-vest-class-merge-chv.md``.

**Vì sao không tách ``vest`` thành class thứ 6:** ``safety_clothes``/``self_clothes`` là 1 cặp nhị phân cho cùng 1 vùng thân người (compliant/không compliant). Vest thường mặc chồng lên quần áo thường, không phải vùng tách biệt, do đó việc tách class riêng tạo mâu thuẫn nhãn thật (1 vùng vừa giống self_clothes vừa giống vest). Gộp ``vest`` (CHV) vào ``safety_clothes`` giải quyết mâu thuẫn này gọn nhất, đúng mục tiêu ứng dụng (biết có PPE hay không, không cần phân loại PPE).

**Lọc dữ liệu CHV trước khi gộp (2 lớp, dùng kỹ thuật ``person_count ≤ positive_class_count``):** vùng ảnh không có box bị Ultralytics dạy tường minh "không có object nào ở đây" cho mọi class (``TaskAlignedAssigner.get_targets`` ở ``ultralytics/utils/tal.py``, và ``bce_loss`` tính trên toàn bộ điểm lưới ở ``ultralytics/utils/loss.py``), chứ không phải bị bỏ qua trung lập. Nếu ảnh CHV có người không được ``vest``/mũ nào "phủ", người đó rất có thể là 1 instance ``self_clothes``/``head`` thật bị bỏ trống nhãn. Lọc: chỉ giữ ảnh có ``person_count ≤ vest_count`` VÀ ``person_count ≤ tổng 4 màu mũ``. Bằng chứng ảnh thật cho cả 2 lớp lọc (ảnh mập mờ bị loại đúng): ``tmp/02_decisions/2026-09-29_ppe-vest-class-merge-chv.md`` mục 4.

.. list-table::
   :header-rows: 1

   * - Bước lọc CHV
     - Ảnh
     - ``vest``\ →\ ``safety_clothes``
     - 4 màu mũ→\ ``helmet``
     - ``person``
   * - Gốc (mọi ảnh có vest)
     - 696
     - 1.784
     - —
     - —
   * - Sau lọc (2 lớp)
     - **474**
     - **1.089**
     - **1.102**
     - **1.079**

Phân bố theo split (giữ nguyên split gốc của tác giả CHV, không re-split): train 387 ảnh (870 person / 879 vest / 886 helmet), val 43 ảnh (102/103/104), test 44 ảnh (107/107/112) ``[source: tính trực tiếp từ data/chv/processed/labels/, 2026-09-29]``.

Nguyên tắc chung (cho cả SHEL5K + SFCHD + CHV): giữ trục dù chỉ 1 dataset đóng góp nếu đó là tín hiệu vi phạm cốt lõi (``self_clothes``), bỏ trục không phục vụ compliance (``face``) hoặc box lồng gây nhiễu (``head_with_helmet``), và không lấy ``head`` từ nguồn có định nghĩa khác dự án (CHV không có ``head``, không suy ra được nên không lấy).

Số liệu đếm trực tiếp từ ``data/<name>/processed/labels/`` (không phải số paper báo cáo).

**5 class cuối:**

.. list-table::
   :header-rows: 1

   * - Class cuối
     - Nguồn → instance
     - Tổng
     - Ghi chú
   * - ``person``
     - SFCHD 17.009 + SHEL5K (person_with_helmet 14.767 + person_no_helmet 5.248) + CHV 1.079
     - 38.103
     - Gộp bỏ trạng thái with/no_helmet của SHEL5K
   * - ``helmet``
     - SFCHD 14.297 + SHEL5K 19.252 + CHV (4 màu gộp) 1.102
     - 34.651
     - CHV bỏ trục màu, chỉ giữ "có mũ"
   * - ``head``
     - SFCHD 1.199 + SHEL5K 6.120
     - 7.319
     - Đầu trần không mũ, tín hiệu vi phạm. CHV không đóng góp (không có class này)
   * - ``safety_clothes``
     - SFCHD 14.812 + CHV ``vest`` 1.089
     - 15.901
     - CHV là nguồn ``vest`` (áo phản quang), khác hình dạng nhưng cùng khái niệm compliance với ``safety_clothes`` gốc
   * - ``self_clothes``
     - SFCHD 779
     - 779
     - Chỉ SFCHD, vi phạm quần áo (giữ dù ít mẫu vì là tín hiệu vi phạm trực tiếp)
   * - **Tổng cộng**
     - 
     - **96.753**
     - 

**Bằng chứng giữ ``self_clothes`` dù ít mẫu:** :download:`_assets/pdf/papers/07_ppe_detection/sfchd_scale_2023yu.pdf <../../../_assets/pdf/papers/07_ppe_detection/sfchd_scale_2023yu.pdf>`, Table V, tr.10. Paper tự gọi ``self_clothes`` là "Other Clothing", benchmark YOLOv5 đạt AP(50:95) **0.549**, cao hơn cả ``Head`` (0.507), dù mẫu ít hơn nhiều. Paper viết nguyên văn (tr.9):

   "despite their limited proportion within the dataset, the pronounced divergence in their features from the Safety Clothing and Safety Helmet facilitates the network's capability to distinguish and assimilate these variations."

**Hạn chế đã biết (2026-09-29):** ``safety_clothes``/``self_clothes`` chỉ có nhãn thật từ domain SFCHD. SHEL5K không có class nào cho trục này (không phải thiếu một phần mà 100% ảnh), nên mọi ảnh SHEL5K đang dạy model "không có 2 class này ở đây" một cách chủ động (``target_scores=0``, cơ chế Ultralytics). Model có nguy cơ không tổng quát hóa tốt 2 class này sang domain SHEL5K/công trường. Hướng sửa đúng gốc (loss masking theo nguồn dataset, có tiền lệ học thuật ECCV 2020) đã research nhưng **chưa implement** (việc rủi ro cao, tách riêng). Chi tiết: ``tmp/02_decisions/2026-09-29_ppe-vest-class-merge-chv.md`` mục 6.

**Bị loại khỏi taxonomy:**

.. list-table::
   :header-rows: 1

   * - Bị loại
     - Nguồn
     - Instance
     - Lý do
   * - CHV, phần bị lọc bỏ (696−474 = 222 ảnh)
     - CHV
     - 695 vest + phần person/helmet tương ứng
     - Không đạt điều kiện ``person_count ≤ positive_count`` (rủi ro nhiễu nhãn ``self_clothes``/``head``, xem bằng chứng ở ``tmp/02_decisions/2026-09-29_ppe-vest-class-merge-chv.md``)
   * - CHV, 4 ảnh trùng SHEL5K (``ppe_0754``, ``ppe_1192``, ``ppe_1121``, ``ppe_1255``)
     - CHV
     - nhỏ
     - Trùng ảnh gốc đã verify dHash. Trong đó 3/4 không có box vest nên đã tự động bị loại bởi bộ lọc trên, còn ``ppe_1255`` từng gây leak với ``shel5k_test`` nếu không lọc
   * - ``person_with_helmet``/``person_no_helmet`` riêng
     - SHEL5K
     - đã gộp vào ``person``
     - Chỉ SHEL5K có trạng thái này, SFCHD không suy ra được mà không đoán
   * - ``head_with_helmet``
     - SHEL5K
     - 16.048
     - Box lồng gần trùng với ``helmet``, gây nhiễu NMS/loss nếu tách riêng
   * - ``face``
     - SHEL5K
     - 14.135
     - Không liên quan PPE compliance
   * - ``blur_head`` / ``blur_clothes``
     - SFCHD
     - 1.133 / 1.323
     - Ảnh nhiễu/mờ do camera, không phải object class thật
   * - SH17 (toàn bộ)
     - SH17
     - —
     - Cân nhắc làm nguồn vest nhưng không chọn, do CHV tốt hơn sau khi đo lại dedup risk. Phát hiện phụ: ``data/sh17/classes.txt`` có bug thứ tự class (xem 0.2.1)

**Tổng sau gộp:** ~96.753 instance qua 5 class, từ 3 dataset ~17.846 ảnh (SHEL5K 5.000 + SFCHD 12.372 + CHV đã lọc 474).

**Rủi ro trùng ảnh (đã verify đầy đủ, không chỉ SHEL5K×SFCHD):**

.. list-table::
   :header-rows: 1

   * - Cặp
     - Số ảnh so sánh
     - Trùng thật (hamming≤5)
   * - SHEL5K × SFCHD
     - 5.000 × 12.372 = 61,86 triệu phép
     - 0
   * - CHV × SHEL5K
     - 1.330 × 5.000 = 6,7 triệu phép
     - 4 (đã xử lý, xem bảng "Bị loại" trên)
   * - CHV × SFCHD
     - 1.330 × 12.372 = 16,5 triệu phép
     - 0

**Cấu trúc tập test (3 thành phần, không gộp chung 1 số):**

``sfchd_test`` (1.238 ảnh) là tập test chung, giữ nguyên giữa Lựa chọn 1 và 2 để so sánh công bằng. ``shel5k_test`` (500 ảnh) và **``chv_test``** (44 ảnh, mới, theo đúng nguyên tắc đã áp dụng cho SHEL5K: domain khác, Lựa chọn 1 chưa từng thấy, nên báo riêng, không gộp vào số chung) chỉ báo cáo thêm cho model Lựa chọn 2, mỗi domain 1 dòng riêng.

.. list-table::
   :header-rows: 1

   * - Split
     - SFCHD
     - SHEL5K
     - CHV (đã lọc)
     - Tổng
   * - Train
     - 9.897
     - 4.000
     - 387
     - 14.284
   * - Val
     - 1.237
     - 500
     - 43
     - 1.780
   * - Test
     - 1.238 (``sfchd_test``, chung)
     - 500 (``shel5k_test``, phụ)
     - 44 (``chv_test``, phụ, mới)
     - 1.782

Checklist việc cần làm: xem "Việc cần làm cho lựa chọn 2" ngay đầu :ref:`Dataset <02-dataset>` (đã chuyển lên đó để song song với Lựa chọn 1, tránh trùng lặp nội dung).
