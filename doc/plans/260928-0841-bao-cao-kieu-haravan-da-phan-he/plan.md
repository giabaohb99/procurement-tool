---
title: "Báo cáo kiểu Haravan Analytics — đa phân hệ"
description: "Khung báo cáo chung (kỳ + so sánh + Xem theo + Xuất Excel), dời 5 trang Thu mua, thêm báo cáo Nhân sự/Nghỉ phép, Hành chính, Công việc."
status: pending
priority: P2
effort: 46h
branch: erp-v2
tags: [report, frontend-v2, backend, analytics, haravan]
created: 2026-09-28
---

# Báo cáo kiểu Haravan — đa phân hệ

## Mục tiêu
Một KHUNG báo cáo dùng chung (backend + frontend) rồi mọi báo cáo chỉ là cấu hình:
bộ lọc kỳ (10 preset) + So sánh với → thẻ KPI (giá trị · ±% · sparkline) → biểu đồ xu hướng
kỳ này vs kỳ so sánh (tự chọn ngày/tuần/tháng) → bảng gom nhóm cùng trang ("Xem theo",
dòng Tổng, cột so sánh, Xuất Excel). Toàn bộ trạng thái lọc nằm trên URL.

## Nguyên tắc khóa
- Mỗi báo cáo: đường `/summary` nằm Ở PHÂN HỆ NGUỒN, cùng `require` + `apply_scope` (hoặc
  chốt riêng: `visible_condition`, `visible_list_ids`) với bảng gốc. Không đường nào lỏng hơn bảng.
- Backend là nguồn DUY NHẤT của: kỳ so sánh, độ hạt thời gian, nhãn chỉ số/chiều, nhãn mã
  trạng thái. Frontend dựng bảng/KPI từ `meta` trả về → không gõ tay danh sách trạng thái ở TS.
- Gom nhóm bằng Python (khuôn sẵn có của `compute_pr_lines_summary`) → chạy y hệt SQLite/MySQL.
- `Tổng` do server tính độc lập, KHÔNG cộng các nhóm (chiều nhiều-giá-trị: PIC, loại nghỉ, công ty dấu).

## Phases
| # | Phase | Effort | Status | Phụ thuộc |
|---|-------|--------|--------|-----------|
| 01 | [Khung backend: kỳ · so sánh · gom nhóm · Excel · thời gian duyệt](phase-01-backend-report-framework.md) | 6h | pending | — |
| 02 | [Khung frontend: bộ chọn kỳ · trang báo cáo chung · bảng Xem theo](phase-02-frontend-report-framework.md) | 8h | pending | 01 (hợp đồng) |
| 03 | [Dời 5 trang Thu mua + trang Tổng quan](phase-03-migrate-procurement-and-overview.md) | 9h | pending | 01, 02 |
| 04 | [Nhân sự + Nghỉ phép](phase-04-hr-leave-reports.md) | 7h | pending | 01, 02 |
| 05 | [Hành chính: Đặt xe · Đóng dấu · Văn bản · Phê duyệt](phase-05-admin-reports.md) | 9h | pending | 01, 02 |
| 06 | [Công việc / Dự án](phase-06-work-reports.md) | 4h | pending | 01, 02 |
| 07 | [Kiểm thử chéo · tài liệu · nhật ký task](phase-07-tests-docs-journal.md) | 3h | pending | 03–06 |

04 · 05 · 06 chạy SONG SONG được: 01 dựng sẵn router rỗng + đăng ký `main.py`, 02 dựng sẵn tệp
danh mục theo nhóm + hằng số route → không phase nào chung tệp.

## Luồng dữ liệu
URL (`preset|from,to · compare · group_by · company_id · lọc riêng`) → `useReportFilters`
→ `GET /api/<nguồn>/summary` → `parse_period` → truy vấn đã scope (kỳ này + kỳ so sánh)
→ `aggregate()` (tổng · xu hướng · nhóm · breakdowns) → JSON hợp đồng chung → `ReportAnalyticsPage`.
Xuất Excel: `GET .../summary/export` (cùng hàm tính, `require(entity,'export')`) → `xlsx_response`.

## Rủi ro chính
- Lộ dữ liệu qua tổng hợp (employee_sensitive, văn bản mật, NCC) → test scope từng báo cáo.
- Ngày lưu 3 kiểu (chuỗi `YYYY-MM-DD`, `Date`, `DateTime` giờ UTC) → helper lọc/bucket duy nhất, quy giờ VN.
- Đổi hợp đồng `/summary` Thu mua → cập nhật 2 file test backend cũ cùng phase 03.

## Rollback
Mỗi phase một commit riêng; báo cáo mới chỉ là route + mục danh mục → revert commit là gỡ sạch.
Phase 03 giữ tham số `year` ở các `/summary` cũ → trang bảng gốc không ảnh hưởng.

## Quyết định đã chốt (28/09/2026)
- Nhịp: làm **01–03 trước**, đại ca xem giao diện rồi mới làm 04–06. Vì vậy 01 KHÔNG dựng sẵn
  router rỗng cho 04–06 và chưa làm helper thời gian duyệt (YAGNI — dựng khi tới phase đó).
- Q0.1 Kỳ mặc định: **Tháng này**, so sánh mặc định: **Kỳ trước** (= tháng trước).
- Q0.2 Không ghi Excel báo cáo vào `tab_export_log`.
- Q3.1 Tiến độ mua hàng: chỉ số giao theo `received_date`, số dòng theo `order_date` (đề xuất).
- Q3.2 Chi phí mua theo `Payable.incur_date`.
- Q4.1 Đơn nghỉ vắt kỳ: tính theo **ngày bắt đầu**.
- Q4.2 Không lịch sử điều chuyển: dùng phòng ban hiện tại + ghi chú "Phòng ban theo hiện tại" trên trang.

## Câu hỏi còn mở
Q4.3, Q5.x, Q6.1, Q0.3 — hỏi lại trước khi làm 04–06. Danh sách ở
[phase-07](phase-07-tests-docs-journal.md#câu-hỏi-còn-mở-tổng-hợp).
