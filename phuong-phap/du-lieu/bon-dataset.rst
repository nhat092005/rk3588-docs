:tocdepth: 1

***********
Bốn dataset
***********

.. admonition:: Tóm tắt

   - Lựa chọn 1 (SFCHD đơn lẻ, 5 lớp) đang được chọn. Baseline cũ train 7 lớp nên cần train lại 5 lớp.
   - Lựa chọn 2 (gộp SHEL5K + SFCHD + CHV đã lọc) đang cân nhắc, vẫn 5 lớp. Bộ dữ liệu `sfchd_shel5k` chưa từng train hoặc eval lần nào (xác nhận 2026-09-29).
   - Số instance đếm trực tiếp: SHEL5K 75.570, SFCHD 50.552, CHV 9.209, CHVG 11.604, SH17 75.994. CHV chỉ dùng 474/1.330 ảnh sau lọc.
   - CHVG chưa nằm trong Option 1/2 vì nguồn, license, paper chưa rõ, và 1.328/1.330 ảnh CHV có trong CHVG theo dHash.
   - `data/sh17/classes.txt` liệt kê sai tên và thứ tự class so với nhãn thật, cần sửa nhưng chưa sửa. SH17 quyết định không dùng.
   - Tỷ lệ Person 27,2% và Hardhat 15,6% trong DATA_CARD của SH17 lệch số đếm trực tiếp, nguyên nhân chưa rõ `[unverified]`.

.. _02-dataset:

Dataset
=======

.. list-table::
   :header-rows: 1

   * - Lựa chọn
     - Trạng thái
     - Phạm vi
     - Class
     - Vì sao
   * - 1. SFCHD đơn lẻ
     - Đang chọn
     - 5 lớp
     - ``person``\ \ ``helmet``\ \ ``safety_clothes``\ \ ``self_clothes``\ \ ``head``\ (lọc từ 7 lớp raw SFCHD, bỏ ``blur_head``/``blur_clothes``)
     - Dataset có sẵn trong repo, không cần gộp. Baseline cũ train 7 lớp, cần train lại 5 lớp
   * - 2. Gộp SHEL5K + SFCHD + CHV (đã lọc)
     - Cân nhắc
     - 5 lớp, mapping đề xuất bên dưới
     - ``person``, ``helmet``, ``head``, ``safety_clothes``, ``self_clothes`` (giống hệt Option 1, trong đó CHV chỉ đóng góp thêm instance cho ``person``/``helmet``/``safety_clothes``, không thêm class mới)
     - Xem trích dẫn nguồn bên dưới. **Cập nhật 2026-09-29**: bản trước của mục này (Option 2 = chỉ SHEL5K+SFCHD, loại hẳn CHV) dựa trên rủi ro dedup bị phóng đại, xem đính chính ở 0.2.2

**Việc cần làm cho lựa chọn 1:**

- ☒ Dataset 5 class ``scripts/data/prepare_sfchd_5class.py`` → ``data/sfchd_5class/processed/`` (giữ split 80/10/10 của ``sfchd``, cùng thứ tự class với ``sfchd_shel5k``)
- ☒ Thêm config ``ai/automation/configs/sfchd_5class_yolov8n_baseline.yaml`` + ``sfchd_5class_yolov8s_baseline.yaml``
- ☐ Leaderboard ``ai/automation/leaderboards/sfchd_5class.csv``: ``ai/automation/run.py`` tự tạo khi train run đầu tiên
- ☐ Train lại baseline (yolov8n + yolov8s) trên ``sfchd_5class`` (mục 8, Phase 2)

**Việc cần làm cho lựa chọn 2:** (chi tiết lý do/số liệu từng dòng xem 0.2.1, 0.2.2)

- ☒ ``data/CLASS_MAPPING.md`` (bản SHEL5K+SFCHD): **cần cập nhật thêm phần CHV**, chưa làm
- ☒ Script gộp ``scripts/data/prepare_sfchd_shel5k.py`` → ``data/sfchd_shel5k/processed/``: **cần sửa để thêm CHV đã lọc**, chưa làm
- ☒ Thêm config ``ai/automation/configs/sfchd_shel5k_yolov8n_baseline.yaml`` + ``sfchd_shel5k_yolov8s_baseline.yaml``
- ☒ Danh sách ảnh test riêng của SHEL5K ``data/sfchd_shel5k/processed/test_shel5k.txt`` (500 ảnh, eval set ``shel5k_test``), do ``prepare_sfchd_shel5k.py`` sinh ra
- ☐ Danh sách ảnh test riêng của CHV ``test_chv.txt`` (44 ảnh, eval set ``chv_test``): mới, chưa làm
- ☐ Quyết định tên identifier dataset: giữ ``sfchd_shel5k`` dù có thêm CHV, hay đổi tên (ví dụ ``sfchd_shel5k_chv``) cho đúng thành phần thật (chưa chốt)
- ☐ Leaderboard ``ai/automation/leaderboards/sfchd_shel5k.csv``: ``ai/automation/run.py`` tự tạo khi train run đầu tiên
- ☐ Train lại baseline (yolov8n + yolov8s) trên ``sfchd_shel5k`` (mục 8, Phase 2): **xác nhận thật (2026-09-29): chưa từng train/eval lần nào**, không có run/leaderboard nào tồn tại cho dataset này

**Nguồn cho lựa chọn 2:** :download:`_assets/pdf/papers/07_ppe_detection/shel5k_helmet_2022otgonbold.pdf <../../_assets/pdf/papers/07_ppe_detection/shel5k_helmet_2022otgonbold.pdf>`, Table 2, tr.9 (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>` "Three-Class Results"):

   So sánh cùng tập ảnh, model YOLOv5x train trên nhãn thiếu sót (SHD) vs nhãn đầy đủ (SHEL5K), lớp Person: Precision 0.0345 → 0.9203, Recall 0.0052 → 0.8409, mAP@0.5 **0.03% → 83.11%**. mAP@0.5 trung bình 3 lớp (Helmet/Head/Person): 59.50% → 85.28%.

Kết luận của paper (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>`): nhãn Person bị bỏ sót nghiêm trọng trong SHD khiến YOLOv5x gần như không phát hiện được người, và việc bổ sung nhãn đầy đủ trên SHEL5K khắc phục hoàn toàn vấn đề này.

.. _021-class-gốc-của-từng-dataset:

Class gốc của từng dataset
--------------------------

Số lượng instance đếm trực tiếp từ file nhãn (toàn bộ train+val+test), không phải số paper báo cáo. SHEL5K, CHV, SFCHD, SH17 đếm từ ``data/<name>/processed/labels/*.txt`` (SH17 đếm trên nhãn thật, xem cảnh báo ở 0.2.1.5). CHVG đếm từ ``data/chvg/CHVG-Dataset/*.xml``. Cùng phương pháp với 0.2.2.

**Tổng quan:**

.. list-table::
   :header-rows: 1

   * - #
     - Dataset
     - Số ảnh
     - Số class
     - Số instance
     - Vai trò trong dự án
   * - 0.2.1.1
     - SHEL5K
     - 5.000
     - 6
     - 75.570
     - Option 2
   * - 0.2.1.2
     - SFCHD
     - 12.372
     - 7 raw (dùng 5)
     - 50.552
     - Option 1, Option 2
   * - 0.2.1.3
     - CHV
     - 1.330
     - 6
     - 9.209
     - Option 2, sau khi lọc (474 ảnh)
   * - 0.2.1.4
     - CHVG
     - 1.699
     - 8
     - 11.604
     - Mới thêm, chưa đánh giá
   * - 0.2.1.5
     - SH17
     - 8.099
     - 17
     - 75.994
     - Không dùng (giữ lại vì có bug class order)

.. _0211-shel5k:

SHEL5K
^^^^^^

6 class, 75.570 instance.

.. list-table::
   :header-rows: 1

   * - Class
     - Ý nghĩa
     - Số lượng
   * - ``helmet``
     - Mũ bảo hộ, box hẹp, chỉ riêng cái mũ
     - 19.252
   * - ``head``
     - Đầu trần, không đội mũ. Tín hiệu vi phạm
     - 6.120
   * - ``head_with_helmet``
     - Vùng đầu bao gồm cả mũ, box rộng hơn, lồng với ``helmet``
     - 16.048
   * - ``person_with_helmet``
     - Toàn thân người, có đội mũ
     - 14.767
   * - ``person_no_helmet``
     - Toàn thân người, không đội mũ. Tín hiệu vi phạm
     - 5.248
   * - ``face``
     - Khuôn mặt (mắt/mũi/miệng), phục vụ nghiên cứu privacy blur, không phải PPE
     - 14.135

.. _0212-sfchd:

SFCHD
^^^^^

7 class raw, 50.552 instance. Option 1 và Option 2 chỉ dùng 5 class, bỏ ``blur_head`` và ``blur_clothes``.

.. list-table::
   :header-rows: 1

   * - Class
     - Ý nghĩa
     - Số lượng
   * - ``person``
     - Toàn thân người
     - 17.009
   * - ``helmet``
     - Mũ bảo hộ (an toàn)
     - 14.297
   * - ``safety_clothes``
     - Áo bảo hộ chống hóa chất (tuân thủ)
     - 14.812
   * - ``self_clothes``
     - Quần áo thường. Tín hiệu vi phạm (paper gọi là "Other Clothing")
     - 779
   * - ``head``
     - Đầu trần, không đội mũ. Tín hiệu vi phạm
     - 1.199
   * - ``blur_head``
     - Vùng đầu bị mờ/nhiễu do camera, lỗi chất lượng ảnh, không phải trạng thái thật
     - 1.133
   * - ``blur_clothes``
     - Vùng quần áo bị mờ/nhiễu do camera, lỗi chất lượng ảnh, không phải trạng thái thật
     - 1.323

.. _0213-chv:

CHV
^^^^

6 class, 9.209 instance raw. Đưa vào Option 2 sau khi lọc dedup và lọc nhiễu nhãn (0.2.2), chỉ còn 474/1.330 ảnh được dùng. Số raw dưới đây không phải số dùng thật.

.. list-table::
   :header-rows: 1

   * - Class
     - Ý nghĩa
     - Số lượng (raw, 1.330 ảnh)
   * - ``person``
     - Toàn thân người, không phân biệt tuân thủ/vi phạm
     - 3.887
   * - ``vest``
     - Áo phản quang (an toàn)
     - 1.784
   * - ``blue helmet``
     - Mũ bảo hộ màu xanh dương
     - 508
   * - ``red helmet``
     - Mũ bảo hộ màu đỏ
     - 536
   * - ``white helmet``
     - Mũ bảo hộ màu trắng
     - 1.195
   * - ``yellow helmet``
     - Mũ bảo hộ màu vàng
     - 1.299

Màu mũ mã hóa vai trò công nhân (chuẩn Build UK), không phải trạng thái tuân thủ.

.. _0214-chvg:

CHVG
^^^^

8 class, 11.604 instance. Có tại ``data/chvg/`` (``raw/``, ``processed/``, ``DATA_CARD.md``), đã qua ``scripts/data/prepare_chvg.py``, chưa nằm trong Option 1/2. Ý nghĩa class dưới đây suy từ tên, chưa kiểm bằng ảnh.

.. list-table::
   :header-rows: 1

   * - Class
     - Ý nghĩa
     - Số lượng
   * - ``person``
     - Người
     - 4.674
   * - ``vest``
     - Áo phản quang
     - 2.137
   * - ``white``
     - Mũ bảo hộ màu trắng
     - 1.292
   * - ``yellow``
     - Mũ bảo hộ màu vàng
     - 1.200
   * - ``blue``
     - Mũ bảo hộ màu xanh dương
     - 543
   * - ``red``
     - Mũ bảo hộ màu đỏ
     - 496
   * - ``head``
     - Đầu trần
     - 730
   * - ``glass``
     - Kính
     - 532

.. list-table::
   :header-rows: 1

   * - Thuộc tính
     - Giá trị
   * - Số ảnh
     - 1.699 jpg, 1.699 xml (1 ảnh không có box)
   * - Kích thước ảnh
     - 640x640 (toàn bộ)
   * - Định dạng nhãn
     - Pascal VOC xml (``raw/annotations/``), đã đổi sang YOLO txt ở ``processed/``
   * - Split
     - Không có sẵn, ``prepare_chvg.py`` chia ngẫu nhiên 80/10/10, seed 42 (1.359 / 169 / 171)
   * - Quan hệ với CHV
     - dHash: 1.328/1.330 ảnh CHV có trong CHVG, CHVG thêm khoảng 366 ảnh. Không gộp cả hai
   * - Tên file
     - Dạng Roboflow (``<id>_jpg.rf.<hash>.jpg``), 1.699 id gốc không trùng nhau
   * - Nguồn, license, paper
     - **Chưa rõ**, thư mục không có README/DATA_CARD

So với CHV: thêm ``head`` (dùng được làm tín hiệu vi phạm, cùng ý nghĩa ``head`` của SFCHD/SHEL5K) và ``glass`` (không thuộc PPE của bài toán, bỏ). Tên class mũ là tên màu trần, không có chữ "helmet".

Việc còn thiếu trước khi dùng:

- ☐ Xác định nguồn và license
- ☐ Kiểm trùng ảnh với SHEL5K/SFCHD bằng dHash, tương tự bước đã làm cho CHV ở 0.2.2 (với CHV đã làm, xem trên)
- ☒ Vẽ box lên ảnh để xác nhận nghĩa từng class (2026-09-30, mẫu nhỏ: 16 crop/class cho ``head``, ``glass``, ``vest``, ``white``, ``blue``, ``person`` và 12 ảnh đầy đủ có ``head``/``glass``, chưa duyệt toàn bộ). Kết quả:

  - ``head`` là đầu trần (không mũ bảo hộ), box nhỏ (median 44px trên ảnh 640px). Có cả ảnh không thuộc công nghiệp (học sinh trong lớp, ảnh chân dung), và có đầu đội mũ thường (mũ phớt) vẫn gán ``head``
  - ``glass`` là kính bảo hộ/kính, box ôm sát vùng mắt, median 79px
  - ``vest``, mũ 4 màu, ``person`` đúng tên class trên mẫu đã xem

- ☐ Kiểm nhiễu nhãn thiếu (người không có nhãn PPE) cho CHVG: bộ lọc ``person <= vest`` (như mục 4 của CHV) chỉ giữ 720/1.699 ảnh, thêm ``person <= helmet`` còn 586. Nếu tính cả ``head`` vào phía mũ (``person <= helmet + head``) thì 1.339/1.699 ảnh qua được, nhưng qua cả hai điều kiện chỉ 613 ảnh. Vế ``vest`` là nút thắt chính, chưa quyết định cách xử lý

.. _0215-sh17:

SH17
^^^^

17 class, 75.994 instance. Có sẵn trong repo (``data/sh17/``). Đã cân nhắc làm nguồn ``vest`` nhưng quyết định **không dùng** (2026-09-29), chọn CHV thay thế. Giữ lại vì phát hiện bug class order đáng ghi nhớ.

**Cảnh báo:** ``data/sh17/classes.txt`` (và ``processed/classes.txt``, ``DATA_CARD.md``) liệt kê **sai** tên/thứ tự class so với nhãn thật trong ``raw/labels/*.txt``. Bảng dưới đã sửa theo thứ tự xác nhận đúng, đối chiếu 3 nguồn độc lập:

1. File gốc tác giả ```sh17.yaml`` <https://github.com/ahmadmughees/SH17dataset/blob/master/sh17.yaml>`__
2. Hình học box: vị trí/kích thước box khớp với tên class thật khi vẽ thử lên ảnh, xem ``tmp/2026-09-29_vest-class-visual-check/``
3. Số đếm trực tiếp khớp gần như tuyệt đối với TABLE II của paper, ghi ở ``docs/_notes/07_ppe_detection/sh17_ppe_2025ahmad.md`` dòng 91-107

Paper gốc không có class ``No-X`` riêng. Trạng thái mặc/không mặc là **tag phụ** (``on``/``off``) đi kèm 1 class duy nhất, không phải 2 class tách biệt như ``data/sh17/classes.txt`` ghi sai. ``data/sh17/classes.txt`` cần sửa, chưa sửa (ngoài phạm vi đang bàn).

.. list-table::
   :header-rows: 1

   * - Class (đúng)
     - Ý nghĩa
     - Số lượng
   * - ``person``
     - Toàn thân người
     - 13.802
   * - ``ear``
     - Tai người, phục vụ phát hiện thiết bị bảo hộ tai
     - 7.730
   * - ``ear-mufs``
     - Chụp tai chống ồn
     - 318
   * - ``face``
     - Khuôn mặt (nhìn thấy khi mũi nhìn thấy)
     - 8.950
   * - ``face-guard``
     - Tấm che mặt bảo hộ
     - 134
   * - ``face-mask``
     - Khẩu trang y tế
     - 670
   * - ``foot``
     - Bàn chân (nhìn thấy khi không đi giày)
     - 759
   * - ``tool``
     - Dụng cụ cầm tay
     - 4.647
   * - ``glasses``
     - Kính bảo hộ/kính thị lực
     - 1.945
   * - ``gloves``
     - Găng tay bảo hộ
     - 2.790
   * - ``helmet``
     - Mũ bảo hộ (kèm tag màu)
     - 927
   * - ``hands``
     - Bàn tay, phục vụ phát hiện găng tay
     - 15.850
   * - ``head``
     - Đầu (mọi góc nhìn)
     - 11.985
   * - ``medical-suit``
     - Bộ đồ y tế phòng dịch
     - 157
   * - ``shoes``
     - Giày (safety/other)
     - 4.560
   * - ``safety-suit``
     - Đồ bảo hộ toàn thân kiểu hazmat/tyvek, khác ``vest``, gần ``safety_clothes`` (SFCHD) hơn
     - 240
   * - ``safety-vest``
     - Áo phản quang, đã verify bằng ảnh, giống ``vest`` của CHV
     - 530

Ghi chú:

- **Đối chiếu hình ảnh** (``tmp/2026-09-29_vest-class-visual-check/``): ``safety-vest`` (SH17) và ``vest`` (CHV) giống nhau, là áo phản quang mỏng khoác ngoài quần áo thường. ``safety-suit`` (SH17) gần ``safety_clothes`` (SFCHD) hơn, là đồ bảo hộ toàn thân/tyvek/hazmat. Hai khái niệm khác nhau rõ về hình dạng dù cùng nhóm "đồ bảo hộ".
- **Tỷ lệ trong DATA_CARD:** ``data/sh17/DATA_CARD.md`` ghi paper báo cáo "Person 27,2%, Hardhat 15,6%, Safety Vest 11,7%". Đối chiếu với số đếm trực tiếp, chỉ ``Safety Vest`` khớp (8.950/75.994 = 11,8%), còn ``Person`` (18,2%) và ``Hardhat`` (10,2%) lệch. Chưa rõ nguyên nhân ``[unverified]``. Không dùng % của DATA_CARD, chỉ dùng số đếm ở bảng trên.
