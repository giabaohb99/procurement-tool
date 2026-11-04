# DIỄN ĐÀN NỘI BỘ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-199, CR-200, CR-261, CR-263, CR-269, CR-271 (theo lộ trình) |

## Phân hệ này là gì

Diễn đàn nội bộ cho toàn công ty, kiểu Facebook cộng chuyên mục kiểu VOZ: đăng bài kèm ảnh / video, chọn đối tượng xem
(phòng ban / công ty / toàn tập đoàn), bình luận, bày tỏ cảm xúc, trang cá nhân, ghim thông báo, chuyên mục nhóm → box →
thread, quản trị ẩn / xóa bài kèm lý do. Là một phân hệ trong ERP v2 (QĐ-D6), gốc đường dẫn `/forum`, layout riêng một
cột, ưu tiên điện thoại ([phạm vi và kế hoạch](plans/00-pham-vi-va-ke-hoach.md), [giao diện](chuc-nang/10-giao-dien-va-logic-hien-thi.md)).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Đợt 1 MVP F0–F5: dữ liệu, API, bảng tin, đăng bài, trang cá nhân, tương tác, quản trị | Đã có trong mã (27/08/2026) | [lộ trình](plans/02-lo-trinh-phase.md) |
| F6 chạy thử với nhóm IT + HR | chưa ghi kết quả | [kịch bản dùng thử](kiem-thu/04-kich-ban-dung-thu.md) |
| Ghim bài, bài tự động khi đổi ảnh đại diện, thông báo từ Văn thư, video | Đã có trong mã | F9a, F10, F12, D-Q3 |
| Chuyên mục kiểu VOZ, sidebar, tìm kiếm, rich text | Đã có trong mã (03/09/2026) | F13a–c, CR-261, CR-263 |
| Sửa bài kèm nhãn đã chỉnh sửa | Đã có trong mã | bao-CR-707 (theo api.md) |
| Tab Hướng dẫn, bật duyệt bài, tự chọn bố cục ảnh, Trợ lý AI đọc diễn đàn | Chưa làm | F7, F8, F11, [đề xuất AI](nghien-cuu/03-de-xuat-ai-doc-dien-dan.md) |
| Lên prod | chưa ghi | |

Đầu tệp [00-pham-vi-va-ke-hoach.md](plans/00-pham-vi-va-ke-hoach.md) vẫn ghi *chưa viết dòng mã nào* (26/08/2026); thông
tin đó đã cũ, lấy theo nhật ký của [02-lo-trinh-phase.md](plans/02-lo-trinh-phase.md).

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `forum` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [chuc-nang/10-giao-dien-va-logic-hien-thi.md](chuc-nang/10-giao-dien-va-logic-hien-thi.md) (logic feed khi dữ liệu lớn), [plans/00-pham-vi-va-ke-hoach.md](plans/00-pham-vi-va-ke-hoach.md) mục 4 (mô hình dữ liệu) |
| So sánh, khảo sát, câu hỏi chờ chốt | [plans/00-pham-vi-va-ke-hoach.md](plans/00-pham-vi-va-ke-hoach.md) mục 1 (QĐ-D1..D7) và mục 6 (câu hỏi), [nghien-cuu/03-de-xuat-ai-doc-dien-dan.md](nghien-cuu/03-de-xuat-ai-doc-dien-dan.md) |
| Kế hoạch đang làm / đã xong | [plans/02-lo-trinh-phase.md](plans/02-lo-trinh-phase.md) |
| Kịch bản kiểm thử tay | [kiem-thu/04-kich-ban-dung-thu.md](kiem-thu/04-kich-ban-dung-thu.md) |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Hướng dẫn sử dụng Diễn đàn nội bộ* (`backend/scripts/seed_help_dien_dan.py`) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-DD-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-DD-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-giao-dien-va-logic-hien-thi.md](chuc-nang/10-giao-dien-va-logic-hien-thi.md) | Khung màn hình, trang cá nhân, đăng bài, logic bảng tin và bình luận khi dữ liệu lớn | chưa ghi (lập 26/08/2026) |
| [kiem-thu/04-kich-ban-dung-thu.md](kiem-thu/04-kich-ban-dung-thu.md) | Kịch bản nhóm IT + HR dùng thử trên điện thoại (F6) | Bản 0.1, 22/10/2026 |
| [nghien-cuu/03-de-xuat-ai-doc-dien-dan.md](nghien-cuu/03-de-xuat-ai-doc-dien-dan.md) | Đề xuất Trợ lý AI đọc diễn đàn | Đã chốt hướng, chưa xếp lịch (03/09/2026) |
| [plans/00-pham-vi-va-ke-hoach.md](plans/00-pham-vi-va-ke-hoach.md) | Phạm vi, quyết định QĐ-D1..D7, câu hỏi mở, chia đợt | Chốt phạm vi sơ bộ (26/08/2026, phần trạng thái đã cũ) |
| [plans/02-lo-trinh-phase.md](plans/02-lo-trinh-phase.md) | Lộ trình F0–F13 và nhật ký thi công | chưa ghi (lập 26/08/2026, nhật ký tới 03/09/2026) |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |

## Mã nguồn

- Backend: `backend/app/modules/forum/`
- Giao diện v2: `frontend-v2/src/modules/forum/`
- Luật cho người viết mã: chưa có tệp luật riêng
