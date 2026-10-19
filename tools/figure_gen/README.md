# Figure Generation Tools for Docs

Thư mục chứa các script sinh hình minh họa (diagrams, graphs, charts) chất lượng cao bằng Python (Matplotlib, SVG, PIL) để nhúng trực tiếp vào tài liệu Sphinx.

## Cấu trúc lưu trữ và luồng xuất ảnh

1. **Mã nguồn sinh ảnh**: Nằm trong các thư mục con tương ứng tại `docs/tools/figure_gen/<nhóm_chủ_đề>/<chủ_đề>/gen.py` (ví dụ `docs/tools/figure_gen/kien-thuc-nen/evaluation_metrics/gen.py`).
2. **Thư mục đầu ra**: Toàn bộ ảnh sinh ra (`.png`, `.svg`) được xuất trực tiếp sang:
   `docs/_assets/generated/kien-thuc-nen/nen-tang-ai/<chủ_đề>/`
3. **Nhúng vào tài liệu**: Các trang tài liệu `.rst` tham chiếu ảnh bằng directive:
   ```rst
   .. figure:: ../../_assets/generated/kien-thuc-nen/nen-tang-ai/<chủ_đề>/<tên_ảnh>.svg
      :align: center
      :width: 75%
      :alt: Mô tả hình ảnh

      Chú thích hình ảnh
   ```

## Ví dụ: evaluation_metrics

- Mã nguồn: `docs/tools/figure_gen/kien-thuc-nen/evaluation_metrics/gen.py`
- Ảnh xuất ra: `docs/_assets/generated/kien-thuc-nen/nen-tang-ai/evaluation-metrics/`
  - `hm-1-iou-ban-chat-hinh-hoc.png`
  - `hm-2-co-che-duong-cong-pr-va-ap.png`
  - `hm-3-map50-95-va-phan-tich-5-lop-ppe.png`
