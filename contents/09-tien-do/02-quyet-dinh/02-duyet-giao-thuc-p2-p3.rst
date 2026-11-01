************************************************************
Duyệt giao thức đo P2 và P3
************************************************************

.. admonition:: Trang này trả lời

   - Người dùng đã quyết định gì về giao thức P2 và P3 ngày 2026-11-01, và quyết định áp cho phạm vi nào?

.. admonition:: Tóm tắt

   - Ngày 2026-11-01, người dùng trả lời "approve" cho câu hỏi ba hướng, được hiểu là hướng 1: duyệt cả P2 và P3 nguyên trạng. Các ngưỡng số mới của từng thí nghiệm vẫn ghi "chưa duyệt".

Định nghĩa hai giao thức, mức thực hiện đúng đã quan sát, nhãn phụ thuộc và giới hạn ở :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/07-giao-thuc-p2-p3`.

1. Quyết định của người dùng
==============================

Ngày 2026-11-01, trả lời "approve" cho câu hỏi có ba hướng dưới đây (hướng 1 là đề xuất), người dùng duyệt. Câu trả lời được hiểu là hướng 1.

1. **Duyệt cả hai nguyên trạng.** Bỏ dòng "chưa qua người dùng duyệt" khỏi các nhãn ở mục 5 của :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/07-giao-thuc-p2-p3`. Điều kiện: các hạn chế ở mục 6 của trang đó vẫn được ghi. **Được hiểu là hướng được chọn.**
2. Duyệt P2, sửa P3 (ví dụ đổi phân bổ CPU, số lần chạy hoặc ngưỡng 99%). Mọi nhãn S2, S3 và ba tiến trình so với ba luồng phải đo lại. Không chọn.
3. Giữ chưa duyệt. Mọi nhãn ở mục 5 của trang giao thức tiếp tục ghi "dưới giao thức chưa duyệt". Không chọn.

Cách hiểu về phạm vi (do tác giả trang, người dùng chỉ trả lời "approve" và có thể chỉnh): việc duyệt áp cho hai giao thức P2 và P3 (cách đặt ngắt, ghim, helper, điều kiện thực hiện đúng). Câu trả lời không nêu riêng các ngưỡng số mới của từng thí nghiệm ghi "chưa duyệt" ở chỗ khác (ví dụ 20% của X10, 0.5 điểm của kiểm tra `int8h5`, 48.41 của tiêu chí 2d, 0.8 đến 1.2 của quy tắc ở :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/06-co-che-cac-muc-do-tre`) nên chúng vẫn ghi "chưa duyệt", và không đổi số seed hay mức kết luận của các nhãn.
