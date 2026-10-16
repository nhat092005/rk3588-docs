# Bộ hình học (visual_guide)

Học bằng sơ đồ tự vẽ, mỗi chủ đề một thư mục con. Thư mục này bị gitignore (`docs/tools/visual_guide/`), không commit. Chủ đề hiện có: `npu_rk3588/` (xem `npu_rk3588/README.md`). Mẫu phong cách: `/home/nhat/workspace/prjs/aiot-edge/tmp/report/app/`. Quyết định thiết kế: `tmp/02_decisions/2026-10-11_hoc-theo-hinh.md` (quyết định 11 là vị trí này).

## Bố cục

```
docs/tools/visual_guide/
  README.md                         file này
  figlib.py  chartlib.py            helper vẽ sơ đồ (SVG) và biểu đồ (matplotlib), dùng chung
  kiem_nguon.py  build_html.py      cổng kiểm nguồn và bộ sinh trang, dùng chung
  <chủ_đề>/
    README.md                       danh sách hình, trạng thái, bảng "Tên các phần"
    index.html                      sinh bởi build_html.py
    NN-<tên>/  gen.py  chu-thich.md  hN-k-<slug>.svg  hN-k-<slug>.png
```

| File dùng chung | Việc |
|---|---|
| `figlib.py` | helper SVG (chép từ mẫu), thêm `tier()`, `original()`, `unknown()`; `original()` nhận đường dẫn tương đối so với thư mục chủ đề |
| `chartlib.py` | kiểu matplotlib cùng màu và font với `figlib` (`save`, `source_line`, `tier_label`) |
| `kiem_nguon.py` | kiểm từng dòng bảng `## Nguồn` với PDF, mã, DTS, log gốc; `--check-map` kiểm các mã viết tắt |
| `build_html.py` | sinh `<chủ_đề>/index.html` |

## Quy ước hình

| Thành phần | Quy ước |
|---|---|
| Huy hiệu tier | `T1 RK3588` (xanh dương): vendor hoặc mã nguồn chính thức. `T2 chung` (xanh lá): paper. `T3 đo` (đỏ): đo của chúng ta, có file log |
| Nét liền xanh dương | luồng dữ liệu, lời gọi, ghi thanh ghi |
| Nét liền đen | đường cấu hình, tín hiệu từ NPU về host |
| Nét đứt xám | phản hồi, dữ liệu trả về, giao diện mà nguồn không vẽ nơi nối |
| Khung nét đứt đen | miền nguồn (power domain) hoặc vị trí chưa rõ |
| Khung nét đứt đỏ nhạt, chữ `unknown` | điều nguồn không cho; không đoán |
| Khung nền xanh dương nhạt | phép tính của bộ hình (không phải câu của vendor) |
| Khung nền xanh lá nhạt | số đo T3 có file log |
| Panel "Hình gốc" | ảnh cắt từ PDF, nhúng dạng base64 trong SVG (SVG nạp qua `<img>` chặn tài nguyên ngoài); caption ghi nguồn và trang |
| Dòng nghiêng cuối hình | nguồn của hình |
| Chữ | font serif, nhãn tiếng Việt, thuật ngữ tiếng Anh giữ nguyên; không em dash, không emoji |

## Định dạng `chu-thich.md`

```
# Phần N: <tên>
## Câu hỏi mở đầu
<1 câu>
## Hình N.k (hN-k-slug) [T1 RK3588]
<caption: câu đầu là ý chính>
Đọc thêm: 0x_ mục y. Số đo: Hình 10.m (nếu có)
Hình gốc: ../../npu_study/images/<khối>/<file>.png (nếu có)
## Hiểu sai thường gặp
- <sai> -> <đúng> [nguồn]
## Câu hỏi tự kiểm
### Câu 1 (giải thích|phân biệt|áp dụng)
<câu hỏi>
Đáp án: <đáp án> [nguồn] (Hình N.k)
## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
```

Các dòng tùy chọn trong khối hình, do `build_html.py` hiểu:

| Dòng | Tác dụng |
|---|---|
| `Dự đoán trước khi xem: ...` | hiện trước hình; hình, caption và ô "Hiểu sai" ẩn đến khi bấm "Xem kết quả" (dùng cho phần số đo) |
| `Khái niệm: Hình 2.4, Hình 6.2` | liên kết hai chiều với hình khái niệm |
| `Số đo: Hình 10.3` (cùng dòng "Đọc thêm") | liên kết tới hình số đo |
| `Hình gốc: <đường dẫn> (<ghi chú>)` | đường dẫn tính từ thư mục chủ đề, ví dụ `../../npu_study/images/...`; trang có nút "Hiện hình gốc" |
| `Trạng thái: chờ <lý do>` | hình chưa có số: không cần file PNG, trang hiện thẻ "chưa có số: <lý do>"; không bịa số |

`Hình N.k` trong văn bản thành liên kết nếu hình đó tồn tại, nếu không thì hiện chữ thường kèm "(chưa làm)".

### Bảng `## Nguồn`

Mỗi chữ, số, câu trong hình, caption, câu hỏi, đáp án ứng với một dòng. Cột `Nguồn` dùng mã viết tắt (bảng ở `docs/npu_study/00_index.md` mục 0 và đầu mục 7); `kiem_nguon.py` tự kiểm nguyên văn trong PDF, mã, DTS, log gốc, không kiểm với file `.md` tổng hợp. Trang là chỉ số PDF (giá trị `-f` của `pdftotext`), không cộng độ lệch trang in.

| Dạng ô `Nguồn` | Ví dụ |
|---|---|
| PDF theo trang | `TRM1 tr.1984` (mọi mã PDF: TRM1 TRM2 DS UG152 API232 OPL UG232 QS232 RT232 EYE TPU JUNG FLEX LP SURV NAGEL GHOLAMI QYOLO Y7Q QAREP REPVGG MOBONE Y6 ACTNAS S3NAS DAHD EDGE LNB RK66 AGENT TVM LEE24 BAMB LENS MCU PHI YOFF Y26A Y26B YEVO) |
| File văn bản theo dòng | `DTS dòng 3478`, `DTS dòng 3534-3655`, `SRAM dòng 21`, `HDR dòng 10-20`, `OPSUP dòng 5`, `FIXTURE dòng 1-30` |
| Driver rknpu | `DRV rknpu_job.c:508-538` (tìm file đệ quy) |
| File trong wheel toolkit | `RKNNPY rknn/api/rknn.py:56-58` |
| Mã ultralytics | `ULT nn/modules/block.py:123` |
| Tài liệu Ultralytics (html, txt) | `UDOC ultralytics_docs_models_yolo26.txt`, thêm `:a-b` nếu cần |
| File bất kỳ trong repo | `REPO ai/automation/configs/x.yaml:10-20`, `REPO tmp/02_decisions/x.md`, `REPO <file.pdf> tr.5` |
| Run huấn luyện | `RUN sfchd_5class_yolo26n_baseline_100ep_s42/args.yaml` |
| Log T3 | `LOG 2026-10-10_t3-board-silu-resize/raw/summary2.json` |

Ô `Nguyên văn ngắn` phải xuất hiện trong văn bản định vị (bỏ khác biệt khoảng trắng, dấu gạch nối cuối dòng, hoa thường, dấu nháy); chọn đoạn đủ đặc trưng (khoảng 4 từ trở lên, hoặc một số kèm đơn vị hay ngữ cảnh). Dấu `|` trong ô viết là `\|`.

| Giá trị đặc biệt | Ý nghĩa |
|---|---|
| `(số học)`, `(đọc từ hình)` | kiểm tay, báo MANUAL |
| `(unknown)` | điều nguồn không cho, báo UNKNOWN |

Nhắc lại độ lệch trang in so với trang PDF (nguồn dẫn theo trang PDF, không cộng độ lệch): EYE in = PDF + 366, JUNG + 235, FLEX + 211; OPL in = PDF - 6; MOBONE + 7906, ACTNAS + 1838, RK66 + 125; LP, Y7Q, QAREP không in số trang. Với TRM, Datasheet, API Reference, User Guide hai số trùng nhau.

## Vẽ lại và kiểm

Chạy từ thư mục chủ đề (cần `pdftotext`; `google-chrome` cho PNG của sơ đồ; `.venv` có matplotlib 3.11.2 cho biểu đồ, nằm ba cấp trên thư mục chủ đề):

```bash
cd docs/tools/visual_guide/npu_rk3588
for d in [0-9]*/; do ../../../.venv/bin/python -B "$d/gen.py"; done
python3 ../kiem_nguon.py .          # thoát 1 nếu có FAIL; bỏ đối số để kiểm mọi chủ đề
python3 ../build_html.py .          # ghi index.html; bỏ đối số để dựng mọi chủ đề
python3 ../kiem_nguon.py --check-map   # mọi mã viết tắt trỏ tới file có thật
```

Một hình: `../../../.venv/bin/python -B 02-phan-cung-rk3588/gen.py h2-4-da-loi-core-mask`.

## Ghi chú tự học (`_notes/`)

Ghi chú chuyên đề của người dùng đặt ở `NN-*/_notes/<slug>/chu-thich.md` (cùng thư mục có `gen.py`, `.svg`, `.png` của note). `build_html.py` đưa chúng vào popup mở bằng nút "Ghi chú (n)" ở tiêu đề Phần NN; mục lục chỉ thêm "(n ghi chú)" cạnh tên phần. Ghi chú không tính vào tiến độ "đã học" và không có ô tích.

- Dòng đầu: `# Ghi chú chuyên đề: <tên>`; các mục còn lại như `chu-thich.md` của phần (`## Câu hỏi mở đầu`, `## Hiểu sai thường gặp`, `## Câu hỏi tự kiểm`, `## Nguồn`).
- Hình: `## Hình C.k (slug) [tier]` (chữ cái thay cho số phần; `C.k` là mã nội bộ của note). Bảng `## Nguồn` dùng cùng mã `C.k` ở cột "Hình".
- "Hình C.k" trong chú thích chuyển tab trong popup; "Hình N.k" (hình chính) đóng popup và cuộn tới hình đó.
- Popup mở danh sách note (có ô lọc khi hơn 8 note; chỉ có 1 note thì mở thẳng). Trong note: mỗi lần một mục (từng hình, rồi "Hiểu sai", "Tự kiểm"), đổi bằng tab, nút Trước/Sau (khi hơn 6 mục) hoặc phím mũi tên. Esc đóng lớp trên cùng.
- `kiem_nguon.py` chưa quét `_notes/`.

## Thêm chủ đề mới

1. Tạo `docs/tools/visual_guide/<chủ_đề>/` (tên tiếng Việt không dấu, gạch dưới).
2. Viết `README.md` của chủ đề: dòng đầu `# <tiêu đề trang>` (thành tiêu đề `index.html`), danh sách hình và trạng thái, và nếu muốn mục lục hiện cả phần chưa làm thì thêm mục `## Tên các phần` với bảng `| Phần | Tên |`.
3. Mỗi phần một thư mục `NN-<tên>/` với `gen.py` (đầu file: `sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))` rồi `from figlib import ...`) và `chu-thich.md` theo định dạng trên. Ảnh gốc nhúng bằng đường dẫn tính từ thư mục chủ đề.
4. Chạy `kiem_nguon.py` và `build_html.py` như ở trên. Mã nguồn mới không nằm trong bảng viết tắt: báo đề xuất (xem quy tắc dưới), không tự sửa script dùng chung.

## Quy tắc cho agent làm phần mới

- Script dùng chung (`figlib.py`, `chartlib.py`, `kiem_nguon.py`, `build_html.py`) bị đóng băng: không sửa. Ngoại lệ: 2026-10-12 người dùng cho phép sửa `build_html.py` một lần để thêm popup ghi chú; từ nay vẫn đóng băng.
- Agent làm một phần chỉ ghi trong thư mục `NN-*/` của phần đó (`gen.py`, `chu-thich.md`, `.svg`, `.png`). Không sửa README, `index.html` hay phần khác.
- Cần helper (vẽ, kiểu biểu đồ, mã nguồn mới cho `kiem_nguon.py`): viết vào `gen.py` của phần đó và nêu trong báo cáo như một đề xuất để gộp vào script dùng chung.
- Không thêm kiến thức ngoài nguồn: điều nguồn không cho ghi `unknown`; mỗi chữ và số trong hình ứng với một dòng bảng nguồn; số đo chỉ lấy từ file log có trên đĩa.
- Không commit; không đụng tiến trình huấn luyện đang chạy và GPU.
