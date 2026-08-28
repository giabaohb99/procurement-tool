# PHÂN HỆ QUẢN LÝ CÔNG VIỆC (kiểu Lark Tasks) — CHỈ MỤC

Phân hệ mới trong ERP v2 (28/08/2026, CR-216): task list mời thành viên, kanban cột tùy
biến, việc con, PIC, tag, nhãn tùy biến, độ ưu tiên, bình luận. **QĐ-T1: làm riêng, độc
lập với Project-M.** Hướng đã chốt: **clone Lark Tasks**, các câu Q1–Q10 chốt hết
28/08/2026.

| Tệp | Nội dung | Bản |
|---|---|---|
| [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md) | 8 nhóm A–H chấm P0/P1/P2, khái niệm dữ liệu, đối chiếu ảnh Lark, đáp án Q1–Q10 | 1.3 |
| [`02` Bảng dữ liệu](./02-bang-du-lieu.md) | 14 bảng `tab_work_*`, 4 IntEnum, phác API `/api/work`, 4 quyết định xuyên suốt (employee_id, ngày chuỗi, SMALLINT, company_id) | 1.0 |
| [`03` Lộ trình phase](./03-lo-trinh-phase.md) | W0–W5 điều kiện cần/đủ, không mốc thời gian; W2 là mốc nghiệm thu MVP | 1.0 |
| [`04` Phân quyền](./04-phan-quyen.md) | Hai tầng: entity `work_task` (SCOPE_FIELDS = PUBLIC + lọc thành viên bắt buộc ở service), ma trận OWNER/ADMIN/MEMBER/VIEWER, kế thừa từ nhóm, cửa quản trị có audit, 7 bài test khóa | 1.0 |
| [`05` Đặc tả giao diện](./05-giao-dien.md) | Clone giao diện Lark: bố cục, tab khung nhìn (List/Kanban P0 · Dashboard/Activities P1 · Gantt P2), thanh công cụ (Việc mới, Tất cả, Lọc, Sắp xếp, Gom nhóm, Tùy chỉnh), giải phẫu thẻ kanban, panel chi tiết, dashboard 4 khối, tham khảo DHTMLX Gantt cho D-05 | 1.0 |

Trạng thái: tài liệu đã duyệt, CHƯA viết code. Bước kế: W0 trong `03`.
