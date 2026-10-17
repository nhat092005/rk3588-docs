# rk3588-docs

Tài liệu nghiên cứu phát hiện PPE (YOLO) trên NPU của RK3588S. Sphinx, định dạng `.rst`, theme `sphinx_rtd_theme`.

Repo này được gắn vào repo chính `rk3588` bằng git submodule tại `docs/`.

## Cấu trúc

Bản đồ các mục nằm ở `index.rst` (trang chủ của site). Ngoài nội dung: `_assets/` chứa PDF nguồn và hình, `tools/` chứa lint và bộ sinh hình `visual_guide` (chưa lên site).

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
- Mỗi trang trả lời một câu hỏi, giới hạn 450 dòng (lint kiểm).
- Mọi khẳng định có tier và nguồn: T1 tài liệu hãng, T2 bài báo, T3 phép đo của dự án. Chưa có nguồn thì ghi `unknown`.
