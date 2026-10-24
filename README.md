# rk3588-docs

Tài liệu nghiên cứu phát hiện PPE (YOLO) trên NPU của RK3588S. Sphinx, định dạng `.rst`, theme `sphinx_rtd_theme`.

Repo này được gắn vào repo chính `rk3588` bằng git submodule tại `docs/`.

## Cấu trúc

Bản đồ các mục nằm ở `index.rst` (trang chủ của site). Kiến thức tách làm hai mục: `01-kien-thuc-nen` (lý thuyết chung, chủ yếu T2) và `02-nen-tang-rk3588` (riêng RK3588S và RKNN, chủ yếu T1). Ngoài nội dung: `_assets/` chứa PDF nguồn và hình, `tools/` chứa lint và bộ sinh hình `visual_guide` (chưa lên site).

## Build

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check        # lint + sphinx-build -W
python3 -m http.server -d _build/html 8000   # hoặc từ repo chính: make docs
```

## Quy ước

- Sidebar 3 tầng: mục lớn, thư mục con, trang (lint kiểm; tầng 4 không hiện với `navigation_depth: 3`). Nhãn nhóm chỉ đặt bằng `:caption:` ở `index.rst` gốc. Đề mục H2 đến H4 chỉ nằm trong trang.
- Tiêu đề trang không trùng nhau trên toàn site (lint kiểm).
- Số liệu sống ở repo chính (`data/*/DATA_CARD.md`, `results/<ds>/table_*.md`); docs giữ đặc tả và diễn giải, chỉ chép số tại điểm đóng băng, kèm file và commit.
- Tiêu đề trang: `*` overline và underline, một lần mỗi file. Cấp tiếp theo: `=`, `-`, `^`.
- Mỗi trang trả lời một câu hỏi, mục tiêu 250 đến 450 dòng, lint chặn ở 1000 dòng.
- Mục con H3 đánh số `N.M` theo mục H2 cha (ví dụ `2.1` nằm dưới `2.`).
- Mỗi khái niệm có một trang chủ, trang khác chỉ link kèm tóm tắt tối đa 2 dòng. Trạng thái dự án và số đo T3 không nằm trong Kiến thức nền hay Nền tảng RK3588, mà ở `09-tien-do/03-khoang-trong`.
- Mọi khẳng định có tier và nguồn: T1 tài liệu hãng, T2 bài báo, T3 phép đo của dự án. Chưa có nguồn thì ghi `unknown`.
