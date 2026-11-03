# CÔNG VIỆC (DỰ ÁN, KIỂU LARK TASKS)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-216, CR-217, CR-218 (gốc phân hệ) |

## Phân hệ này là gì

Phân hệ giao việc, theo dõi tiến độ và trao đổi quanh từng công việc, dựng theo Lark Tasks: dự án (danh sách công việc)
mời thành viên, kanban cột tùy biến, việc con, người phụ trách, trường tùy biến, độ ưu tiên, bình luận, Gantt. Tên hiển
thị cho người dùng là **Dự án**, đường `/project`; mã nguồn, API và bảng vẫn mang tên `work`
([tài liệu chức năng §1](chuc-nang/10-du-an-cong-viec.md#1-các-khái-niệm--đọc-trước-đừng-đoán-theo-tên)). Chỉ có trên `frontend-v2`.

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| W0 nền dữ liệu và phân quyền · W1 API lõi | Đã có trong mã (28/08/2026) | CR-217, CR-218 |
| W2 giao diện: cây bên trái, kanban, danh sách, panel chi tiết | Phần lớn xong (28/08/2026); có kịch bản dùng thử trên dev để đóng mốc MVP | [lộ trình](plans/03-lo-trinh-phase.md), [kịch bản dùng thử](kiem-thu/06-kich-ban-dung-thu.md) |
| Gantt, cột mốc, phụ thuộc · tab Hoạt động · bình luận và đính kèm | Đã có trong mã | CR-219, CR-226, CR-249, CR-253 |
| Thông báo giao việc, việc vào tab *Việc cần làm*, thùng rác, sửa bình luận, ghim dự án | Đã có trong mã | duoc-CR-666, duoc-CR-667 |
| Dashboard dự án, màn *Việc của tôi*, chuyển việc sang dự án khác, gom nhóm kanban theo trường khác | Chưa làm | [tài liệu chức năng §9](chuc-nang/10-du-an-cong-viec.md#9-những-thứ-chưa-có) |
| Lên prod | chưa ghi | Lộ trình ghi: prod chỉ sau khi W3 xong |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `work` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/02-bang-du-lieu.md](tai-lieu-ky-thuat/02-bang-du-lieu.md), [tai-lieu-ky-thuat/04-phan-quyen.md](tai-lieu-ky-thuat/04-phan-quyen.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [chuc-nang/11-danh-sach-tinh-nang.md](chuc-nang/11-danh-sach-tinh-nang.md) §4, §4b (đối chiếu Lark và QLDA), §7 (Q1–Q10 đã chốt) |
| Kế hoạch đang làm / đã xong | [plans/03-lo-trinh-phase.md](plans/03-lo-trinh-phase.md) |
| Kịch bản kiểm thử tay | [kiem-thu/06-kich-ban-dung-thu.md](kiem-thu/06-kich-ban-dung-thu.md) |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Hướng dẫn sử dụng Dự án và Công việc* (`backend/scripts/seed_help_cong_viec.py`) |

## Điều cần nhớ (giữ từ README cũ)

- **QĐ-T1:** làm riêng, độc lập với Project-M. **QĐ-T2:** *Dự án* là danh sách công việc kiểu dự án (A-10), không dựng cặp
  bảng project / task riêng.
- Ba chỗ bản thi công lệch thiết kế, cố ý: IntEnum khai ở `backend/app/modules/work/model.py`; 12 bảng thay vì 14 vì bình
  luận và đính kèm dùng hạ tầng chung (`tab_comment`, `tab_file_link`); người tạo việc ở cột `creator_employee_id`, còn
  `created_by` giữ nghĩa id tài khoản.
- Cột kanban **khác** trạng thái công việc: kéo vào cột tên *Xong* không làm việc thành *Hoàn thành*
  ([tài liệu chức năng §2](chuc-nang/10-du-an-cong-viec.md#2-cột-kanban-khác-trạng-thái-công-việc)).

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-CV-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-CV-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-du-an-cong-viec.md](chuc-nang/10-du-an-cong-viec.md) | Tài liệu chức năng cho người dùng: khái niệm, khung nhìn, panel, quyền hai lớp, thông báo, thứ chưa có | chưa ghi |
| [chuc-nang/11-danh-sach-tinh-nang.md](chuc-nang/11-danh-sach-tinh-nang.md) | Danh sách tính năng nhóm A–H, ưu tiên P0 / P1 / P2, đáp án Q1–Q10 | Bản 1.4, 28/08/2026 (danh sách đã duyệt) |
| [chuc-nang/12-giao-dien.md](chuc-nang/12-giao-dien.md) | Đặc tả giao diện clone Lark: thanh công cụ, kanban, panel, Gantt | Bản 1.0, 28/08/2026 |
| [kiem-thu/06-kich-ban-dung-thu.md](kiem-thu/06-kich-ban-dung-thu.md) | Kịch bản một đội dùng thử trọn vòng trên dev | Bản 0.1, 22/10/2026 |
| [plans/03-lo-trinh-phase.md](plans/03-lo-trinh-phase.md) | Lộ trình W0–W5, điều kiện cần / đủ | Bản 1.1, 28/08/2026 |
| [tai-lieu-ky-thuat/02-bang-du-lieu.md](tai-lieu-ky-thuat/02-bang-du-lieu.md) | Bảng `tab_work_*`, IntEnum, phác API | Bản 1.1, 28/08/2026 |
| [tai-lieu-ky-thuat/04-phan-quyen.md](tai-lieu-ky-thuat/04-phan-quyen.md) | Phân quyền hai tầng, ma trận vai trò trong dự án | Bản 1.0, 28/08/2026 |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |

## Mã nguồn

- Backend: `backend/app/modules/work/`
- Giao diện v2: `frontend-v2/src/modules/work/`
- Luật cho người viết mã: chưa có tệp luật riêng
