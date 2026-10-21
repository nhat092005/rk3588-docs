# Figure Generation Tools for Docs

Thư mục chứa các script sinh hình minh họa (diagrams, graphs, charts) bằng Python (SVG viết tay qua `figlib.py`, PIL) để nhúng trực tiếp vào tài liệu Sphinx.

## Cấu trúc lưu trữ và luồng xuất ảnh

1. **Mã nguồn sinh ảnh**: Nằm tại `docs/tools/figure_gen/<nhóm>/<chủ_đề>/gen.py`, trong đó `<nhóm>` và `<chủ_đề>` trùng tên thư mục của trang `.rst` tương ứng (ví dụ `docs/tools/figure_gen/01-kien-thuc-nen/08-evaluation-metrics/gen.py`).
2. **Thư viện dùng chung**: `docs/tools/figure_gen/figlib.py` (lớp `Fig`, hàm `run`, `source`, các hằng màu `BLUE`, `GREEN`, `RED`, `GRAY`, `INK`).
3. **Thư mục đầu ra**: Mỗi `gen.py` tự xuất `.svg` sang `docs/_assets/generated/<nhóm>/<mục>/<chủ_đề>/`, với `<mục>` là thư mục mục con nằm giữa nhóm và chủ đề (ví dụ `01-nen-tang-ai`). Ví dụ: `docs/_assets/generated/01-kien-thuc-nen/01-nen-tang-ai/08-evaluation-metrics/`.
4. **Nhúng vào tài liệu**: Các trang tài liệu `.rst` tham chiếu ảnh bằng directive sau (đường dẫn tương đối tính từ vị trí file `.rst`):
   ```rst
   .. figure:: ../../../_assets/generated/01-kien-thuc-nen/01-nen-tang-ai/<chủ_đề>/<tên_ảnh>.svg
      :align: center
      :width: 75%
      :alt: Mô tả hình ảnh

      Chú thích hình ảnh
   ```

## Chạy script

```bash
python3 docs/tools/figure_gen/01-kien-thuc-nen/<chủ_đề>/gen.py [outdir] [tên_ảnh ...] [--png]
```

- Không truyền tham số: sinh toàn bộ ảnh của chủ đề vào thư mục đầu ra mặc định ở trên.
- `outdir`: ghi sang thư mục khác (dùng để so sánh trước khi ghi đè).
- `tên_ảnh`: chỉ sinh các ảnh được chọn.
- `--png`: sinh thêm `.png` bằng Chrome headless (cần `google-chrome` hoặc `chromium`). Script của `03-convolution-va-cnn` chỉ xuất SVG.

## Kiểm tra bố cục: lint.py

Chạy sau mỗi lần sinh hình. Cần `google-chrome` hoặc `chromium`.

```bash
python3 docs/tools/figure_gen/lint.py docs/_assets/generated/01-kien-thuc-nen   # quét cả thư mục
python3 docs/tools/figure_gen/lint.py <file.svg> --min-font 7 --json            # một file, ngưỡng chữ 7 px, JSON có level và hộp bao x,y,w,h
python3 -m unittest docs/tools/figure_gen/test_lint.py                          # kiểm thử: mỗi luật có một SVG chứa đúng lỗi đó
```

**Nguyên tắc.** Lint báo mọi dấu hiệu nghi ngờ và không im lặng bỏ qua điều gì (trừ nền phủ kín canvas). Lint không biết ý đồ của hình, nên agent đọc từng dòng và tự quyết:

- Lỗi thật: sửa `gen.py`, sinh lại hình, chạy lại lint.
- Cố ý: giữ nguyên và ghi lý do (ví dụ nhãn đặt trên viền, đường chéo cố ý xuyên hộp để minh họa khái niệm).
- Khi bố cục đẹp xung đột với độ chính xác nội dung (số liệu, công thức, quan hệ hình học, thứ tự bước), luôn ưu tiên độ chính xác nội dung. Không đổi hay bớt nội dung chỉ để lint hết báo. Lint sạch không có nghĩa là hình đúng.

Mỗi dòng kết quả có dạng `<file>: <MỨC> <LUẬT> @(x,y,wxh) "<chữ hoặc hình>" <chi tiết>`, cuối cùng là `N file, X lỗi, Y cảnh báo, Z cần xem lại`. Mã thoát là 1 nếu có ERROR, 0 nếu không (WARN và REVIEW không đổi mã thoát). Hình được nhận diện bằng số thứ tự phần tử trong SVG (`#12 path ...`) và hộp bao `x,y,w,h` để cắt vùng ra xem.

### ERROR: gần như chắc chắn là lỗi

| Luật | Ý nghĩa |
|---|---|
| `OVERLAP` | hai dòng chữ chồng lên nhau |
| `CROSS_EDGE` | chữ vắt qua viền một khung |
| `COVERED` | chữ bị hình tô đặc vẽ sau che từ 20% diện tích |
| `LINE_THROUGH` | đường thẳng, đường cong hoặc viền đa giác đậm đi xuyên qua chữ |
| `OUT_OF_CANVAS` | chữ ra ngoài mép hình |
| `SHAPE_OUT_OF_CANVAS` | hình vẽ ra ngoài mép hình quá 2 px |
| `ARROW_TOO_SHORT` | mũi tên không còn thân: chiều dài path trừ phần đầu mũi tên (tính từ `refX`, kích thước marker) dưới 1 px |
| `SHAPE_CROSS_EDGE` | đường hoặc hình vẽ có nét (không phải chữ, không có đầu mũi tên) nằm từ 50% chiều dài trở lên trong một khung nhưng thò ra ngoài viền hơn 4 px |

### WARN

| Luật | Ý nghĩa |
|---|---|
| `SMALL_FONT` | chữ nhỏ hơn `--min-font` (mặc định 6.5 px trên viewBox) |
| `EMPTY_SPACE` | khung dư khoảng trống đáy lớn hơn 2 lần đệm trên/trái của chính nó |
| `TIGHT_TEXT` | chữ cách viền khung chứa nó dưới 2.5 px (khung cao và rộng trên 8 px, kể cả ô lưới nhỏ) |
| `BIG_GAP` | khoảng trống dọc trên 22 px giữa hai khối nội dung liên tiếp |
| `LOW_CONTRAST` | chữ có tương phản dưới 3:1 so với nền (chỉ tính nền tô đặc `#hex`, `white`, `black`) |

### REVIEW: agent tự phán đoán cố ý hay lỗi

Gồm mọi thứ trước đây bị bỏ qua ngầm và các dấu hiệu chưa đủ chắc để thành ERROR.

| Luật | Ý nghĩa |
|---|---|
| `HALO_CROSS_EDGE`, `HALO_LINE_THROUGH`, `HALO_COVERED` | chữ có halo (nhãn cố ý đặt trên viền hoặc nét) mà lẽ ra bị báo `CROSS_EDGE`, `LINE_THROUGH`, `COVERED` |
| `GRID_THROUGH` | nét mờ (sáng hoặc mảnh dưới 0.5 px, thường là lưới) xuyên qua chữ, gộp mọi nét của một dòng chữ thành một dòng |
| `LINE_UNDER_CHIP` | nét xuyên qua chữ nhưng đoạn đó bị chip nền đặc che |
| `COVERED_PARTIAL` | chữ bị hình tô đặc vẽ sau che dưới 20% |
| `TEXT_TOUCH` | hộp bao đầy đủ của hai dòng chữ chạm hoặc chồng nhẹ |
| `TEXT_NEAR_EDGE` | chữ nằm ngoài khung nhưng cách viền dưới 1.5 px, hoặc vắt qua viền dưới ngưỡng `CROSS_EDGE` (bỏ cạnh chung với ô chứa chính chữ) |
| `TEXT_NEAR_STROKE` | nét đậm sượt sát chữ (dưới 1 px) nhưng chưa xuyên qua |
| `SHAPE_ENTERS_EDGE` | đường hoặc hình vẽ cắt viền một khung nhưng dưới 50% chiều dài nằm trong khung đó |
| `SHAPE_UNDER_FILL` | đường hoặc hình vẽ nằm trong khung tô đặc vẽ sau, phần trong bị che |
| `ARROW_SHORT_SHAFT` | mũi tên có thân thấy được từ 1 đến 4 px |
| `DANGLING_ARROW` | đầu hoặc đuôi mũi tên cách mọi hình và chữ hơn 10 px |
| `ARROW_THROUGH_BOX` | mũi tên đi xuyên một khung mà cả hai đầu nằm ngoài khung đó |
| `ARROWHEAD_ON_TEXT` | đầu mũi tên đè lên chữ |
| `NOT_EVALUATED` | hình dùng `transform`, `clipPath`, `use`, `mask`, `filter`, `foreignObject`, `svg` lồng hoặc `marker-start`/`marker-mid`: lint không tính phần đó, phải xem bằng mắt |

### Lint không làm được

- Ngoại lệ có chủ ý: mũi tên bắt đầu trong khung và kết thúc ngoài khung (nối giữa các khối) không bị báo. Nét lưới mờ chỉ sượt gần chữ không bị báo, và không dùng làm đích của mũi tên.
- Nội dung: số liệu, công thức, hình minh họa có khớp lời giải thích hay không, màu, thẩm mỹ. Ví dụ hình họ IoU thiếu ρ, c hoặc α·v so với công thức là lỗi nội dung, lint không thấy. Vẫn phải xem hình bằng mắt.

## Các chủ đề hiện có

| Chủ đề | Mã nguồn | Ảnh xuất ra (trong `01-nen-tang-ai/`) |
|---|---|---|
| Mạng nơ-ron | `01-kien-thuc-nen/01-mang-no-ron/gen.py` | `01-mang-no-ron/mnr-*.svg` |
| Tensor và kiểu dữ liệu | `01-kien-thuc-nen/02-tensor-va-kieu-du-lieu/gen.py` | `02-tensor-va-kieu-du-lieu/tk-*.svg` |
| Convolution và CNN | `01-kien-thuc-nen/03-convolution-va-cnn/gen.py` | `03-convolution-va-cnn/cv-*.svg` |
| Chuẩn hóa và activation | `01-kien-thuc-nen/04-chuan-hoa-va-activation/gen.py` | `04-chuan-hoa-va-activation/act-*.svg` |
| Evaluation metrics | `01-kien-thuc-nen/08-evaluation-metrics/gen.py` | `08-evaluation-metrics/hm-*.svg` |
