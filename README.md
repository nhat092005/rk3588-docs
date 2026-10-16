# rk3588-docs

Tài liệu nghiên cứu phát hiện PPE (YOLO) trên NPU của RK3588S. Sphinx, định dạng `.rst`, theme `sphinx_rtd_theme`.

Repo này được gắn vào repo chính `rk3588` bằng git submodule tại `docs/`.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `guide.rst` | Bản đồ site, cách đọc nguồn |
| `de-tai/` | Bài toán, dữ liệu, board, câu hỏi nghiên cứu |
| `kien-thuc/` | NPU, lượng tử hóa, toolchain, bộ nhớ, thiết kế model, YOLO |
| `bai-bao/` | 35 bài báo, mỗi bài một trang |
| `quy-trinh/` | Runbook, các phase, bản đồ code, xử lý lỗi |
| `thi-nghiem/` | Protocol, bảng kết quả, so sánh |
| `tai-lieu-hang/` | Datasheet, TRM, RKNN |
| `thuat-ngu.rst` | Thuật ngữ |
| `_assets/` | PDF nguồn và hình |
| `tools/` | Lint, bộ sinh hình `visual_guide` (chưa lên site) |

## Build

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make check        # lint + sphinx-build -W
python3 -m http.server -d _build/html 8000
```

## Quy ước

- Sidebar 3 tầng: mục lớn, thư mục con, trang. Đề mục H2 đến H4 chỉ nằm trong trang.
- Tiêu đề trang: `*` overline và underline, một lần mỗi file. Cấp tiếp theo: `=`, `-`, `^`.
- Mỗi trang trả lời một câu hỏi, giới hạn 450 dòng (lint kiểm).
- Mọi khẳng định có tier và nguồn: T1 tài liệu hãng, T2 bài báo, T3 phép đo của dự án. Chưa có nguồn thì ghi `unknown`.
