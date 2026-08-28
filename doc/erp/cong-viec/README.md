# PHÂN HỆ QUẢN LÝ CÔNG VIỆC (kiểu Lark Tasks) — CHỈ MỤC

Phân hệ mới trong ERP v2 (28/08/2026, CR-216): task list mời thành viên, kanban cột tùy
biến, việc con, PIC, tag, nhãn tùy biến, độ ưu tiên, bình luận. **QĐ-T1: làm riêng, độc
lập với Project-M.** Hướng đã chốt: **clone Lark Tasks**, các câu Q1–Q10 chốt hết
28/08/2026. Bản 1.4 (CR-217, cùng ngày) đối chiếu tài liệu QLDA của Công cụ Văn thư
(DMS-PM-FEATURES): **QĐ-T2 — "Dự án" = task list kiểu dự án** (A-10), DB giữ khuôn
`tab_work_*`; nhóm F bên đó (lịch làm việc — ngày nghỉ) dời W5.

| Tệp | Nội dung | Bản |
|---|---|---|
| [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md) | 8 nhóm A–H chấm P0/P1/P2, khái niệm dữ liệu, đối chiếu ảnh Lark, **§4b đối chiếu tài liệu QLDA của DMS** (QĐ-T2 list kiểu dự án A-10, B-14/B-15, nhóm F dời W5), đáp án Q1–Q10 | 1.4 |
| [`02` Bảng dữ liệu](./02-bang-du-lieu.md) | 14 bảng `tab_work_*`, 4 IntEnum, phác API `/api/work`, 4 quyết định xuyên suốt (employee_id, ngày chuỗi, SMALLINT, company_id); mở rộng A-10 lên `tab_work_list` (kind + ngày + `WorkProjectStatus`) | 1.1 |
| [`03` Lộ trình phase](./03-lo-trinh-phase.md) | W0–W5 điều kiện cần/đủ, không mốc thời gian; W2 là mốc nghiệm thu MVP; W4 thêm A-10, W5 thêm cụm Gantt B-14/B-15 + lịch làm việc | 1.1 |
| [`04` Phân quyền](./04-phan-quyen.md) | Hai tầng: entity `work_task` (SCOPE_FIELDS = PUBLIC + lọc thành viên bắt buộc ở service), ma trận OWNER/ADMIN/MEMBER/VIEWER, kế thừa từ nhóm, cửa quản trị có audit, 7 bài test khóa | 1.0 |
| [`05` Đặc tả giao diện](./05-giao-dien.md) | Clone giao diện Lark: bố cục, tab khung nhìn (List/Kanban P0 · **Gantt xong sớm, CR-219** · Dashboard/Activities P1), thanh công cụ (Việc mới, Tất cả, Lọc, Sắp xếp, Gom nhóm, Tùy chỉnh), giải phẫu thẻ kanban, panel chi tiết, dashboard 4 khối, tham khảo DHTMLX Gantt cho D-05 | 1.0 |

Trạng thái (28/08/2026): **W0 xong** (CR-217) · **W1 xong** và **W2 phần lớn xong**
(CR-218) — chi tiết từng phase ở [`03`](./03-lo-trinh-phase.md).

- Backend: 12 bảng `tab_work_*` + migration `631070f1b801`, 4 IntEnum, entity `work_task`,
  25 endpoint `/api/work/...`, 31 test khóa tầng thành viên.
- Frontend: phân hệ `frontend-v2/src/modules/work/` ở `/work` — cây nhóm→list, **ba khung
  nhìn như Lark (Bảng · Danh sách · Gantt)**, panel chi tiết, hộp thoại thành viên/thiết lập.
  Gantt (D-05) vốn xếp P2/W5, làm sớm 28/08/2026 theo yêu cầu — CR-219.
- **Chưa có:** «Lọc» điều kiện (§3.3) · kéo đổi thứ tự cột · ghim list → ba mục này còn
  thuộc W2. Bình luận + thông báo giao việc là **W3**; Dashboard/Activities và các mục
  P1/P2 khác theo `03`. Gantt chưa có mũi tên phụ thuộc việc trước–sau (thiếu bảng
  `tab_work_task_link`).

Ba chỗ bản thi công lệch bản thiết kế, cố ý (chi tiết ở dòng CR-217 của
`doc/tai-lieu-ky-thuat/change-log.md`):

1. **IntEnum khai ở `app/modules/work/model.py`**, không vào `status_catalog.py` như `02`
   §0.3 ghi — khung đó là bộ mã **chuỗi** của QĐ-9 (`Code.value: str`), không chứa được số.
   Theo đúng khuôn `forum/model.py`, là module IntEnum gần nhất.
2. **12 bảng chứ không 14:** bỏ `tab_work_comment` và `tab_work_attachment` vì trùng hạ tầng
   dùng chung đã chạy (`tab_comment` + `core/comment_registry.py` · `tab_file_link` +
   `core/file_registry.py`) — mở cho phân hệ mới chỉ tốn một dòng đăng ký. **Chờ xác nhận**,
   muốn bảng riêng thì nói trước khi làm W3.
3. Người tạo task nằm ở cột riêng `creator_employee_id`; `created_by` của `AuditMixin` giữ
   nguyên nghĩa **user_id** như toàn hệ.
