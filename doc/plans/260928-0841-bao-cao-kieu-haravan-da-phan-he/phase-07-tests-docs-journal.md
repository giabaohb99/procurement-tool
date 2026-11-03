# Phase 07 — Kiểm thử chéo · tài liệu · nhật ký task

## Context links
- `CLAUDE.md` (cổng kiểm frontend-v2, luật nhật ký), `doc/tai-lieu-ky-thuat/nhat-ky-task.md` (mục mẫu `duoc-CR-481`), `doc/tai-lieu-ky-thuat/change-log.md`, `frontend-v2/.claude/rules/testing.md`

## Overview
- Priority: P2 · Status: pending · Effort: 3h · Phụ thuộc: P03–P06 xong.

## Requirements / Test matrix tổng
| Tầng | Nội dung | Lệnh |
|---|---|---|
| Unit BE | khung kỳ/so sánh/độ hạt/UTC; aggregate distinct; xlsx; turnaround | `pytest test/backend/test_bao_cao_khung_ky_so_sanh.py test/backend/test_bao_cao_thoi_gian_duyet.py -q` |
| Tích hợp BE | mỗi báo cáo: scope (world/cap_quyen), chiều nhiều giá trị, `/summary` không bị `/{id}` nuốt, export 403 khi thiếu `export` | chỉ các tệp `test_bao_cao_*` mới + 2 tệp Thu mua cũ |
| Canh bảo mật | test duyệt đệ quy JSON mọi báo cáo HR không chứa khóa `SENSITIVE_FIELDS`; NCC/NSPT 403 khi thiếu quyền | trong tệp tương ứng |
| Unit FE | preset, URL state, bảng Tổng/±%, format metric, danh mục (luật entity) | `npx vitest run src/modules/report` |
| Tĩnh FE | typecheck + lint cả cây | `npm run typecheck`, `npm run lint` |
| E2E tay | trên `localhost:8083`: mỗi báo cáo đổi preset/so sánh/Xem theo, F5, copy link, Xuất Excel mở được; điện thoại dùng emulate (không resize) | trình duyệt |
| MySQL thật | gọi mỗi `/summary` trên stack Docker (SQLite không bắt lỗi hàm ngày/độ dài) | `curl` qua API docs |
KHÔNG chạy full `test/backend` hay `npm run check` (luật 17/09/2026).

## Implementation steps
1. Chạy bảng trên, sửa lỗi (đẩy về phase chủ).
2. Tài liệu: thêm mục "Phân hệ Báo cáo — khung Haravan" vào `CLAUDE.md` (luật: `/summary` ở phân hệ nguồn, cùng scope; hợp đồng JSON; Tổng tính riêng; cấm chiều nhạy cảm; router báo cáo đăng ký trước router chính); cập nhật `doc/tai-lieu-ky-thuat/change-log.md` (CR mới); HDSD ngắn `doc/huong-dan-su-dung/bao-cao/` (nếu thư mục HDSD dùng cho phân hệ khác).
3. Nhật ký: mục `duoc-CR-<số mới>` trong `nhat-ky-task.md`, câu tiếng Việt trọn vẹn, việc con `###` theo phase, dòng cuối `Mã nguồn:`/`Commit:`.
4. Cập nhật status plan.md.

## Todo
- [ ] chạy ma trận test · [ ] E2E tay + MySQL thật · [ ] CLAUDE.md + change-log · [ ] nhật ký task · [ ] status plan

## Success criteria
Mọi lệnh trong bảng xanh; 13 trang báo cáo (Thu mua 5 · Nhân sự 3 · Hành chính 4 · Công việc 1) + Tổng quan mở được với quyền phù hợp và ẩn với người thiếu quyền; nhật ký đồng bộ được (`sync_task_journal.py` không lỗi định dạng).

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Lỗi chỉ lộ trên MySQL | TB×TB | bước gọi thật trên Docker |
| Vai trò đang chạy thiếu `export` trên entity mới | TB×Thấp | ghi chú: tick ở màn Phân quyền (D-018), không đổi seed |

## Security considerations
Soát lại checklist: mỗi `/summary` có `require` + chốt scope đúng bảng nguồn; Excel có `export`.

## Câu hỏi còn mở (tổng hợp)
- Q0.1 Kỳ mặc định khi mở báo cáo: 30 ngày qua (đề xuất) hay Tháng này?
- Q0.2 Có ghi Excel báo cáo vào `tab_export_log` (màn `/system/exports`) không? Đề xuất: không (YAGNI).
- Q3.1 Tiến độ mua hàng theo ngày nhận hay ngày đặt? · Q3.2 Chi phí mua theo `incur_date`?
- Q4.1 Đơn nghỉ vắt kỳ: theo `from_date` hay chia ngày? · Q4.2 Lịch sử điều chuyển? · Q4.3 Định nghĩa "đang làm việc"?
- Q5.1 Đặt xe theo ngày đi? · Q5.2 Văn bản theo ngày tạo + ban hành theo `issued_at`? · Q5.3 Báo cáo Văn bản cần `document.read`? · Q5.4 Ai được xem báo cáo Phê duyệt?
- Q6.1 Đếm việc con / mốc?
- Q0.3 Đặt phòng họp (`room_booking`) có cần báo cáo riêng không? (chưa nằm trong phạm vi)
