---
title: "duoc-CR-717 — Nghỉ phép đủ như nexterp"
description: "Chính sách nghỉ phép + phân bổ (từng người, hàng loạt), báo cáo làm việc ngày lễ, đóng các khoảng hở nhỏ của menu Nghỉ phép ERPNext"
status: pending
priority: P2
effort: 30h
branch: erp-v2
tags: [hr, leave, erpnext, report]
created: 2026-11-03
---

# duoc-CR-717 — Nghỉ phép đủ như nexterp

Anh Được (03/11/2026): «làm đủ theo như nexterp». Đối chiếu 12 mục menu: [reports/research-erpnext-vs-dego-12-muc.md](reports/research-erpnext-vs-dego-12-muc.md).
**Kỳ nghỉ phép (Leave Period): Không làm (anh Được bỏ 03/11/2026)** — quỹ giữ theo năm dương lịch.

| # | Giai đoạn | Chủ | Phụ thuộc | Giờ | Trạng thái |
|---|---|---|---|---|---|
| 01 | [BE — Chính sách + phân bổ](phase-01-be-chinh-sach-va-phan-bo.md) | backend | CR-715 đã commit | 9 | Chờ |
| 02 | [FE — Chính sách + phân bổ](phase-02-fe-chinh-sach-va-phan-bo.md) | giao-dien-v2 | 01 | 8 | Chờ |
| 03 | [BE — Báo cáo ngày lễ + hở nhỏ](phase-03-be-bao-cao-ngay-le-va-ho-nho.md) | backend | 01 (chung `main.py`) | 6 | Chờ |
| 04 | [FE — Báo cáo ngày lễ + hở nhỏ](phase-04-fe-bao-cao-ngay-le-va-ho-nho.md) | giao-dien-v2 | 02 (chung `app-routes.ts`), 03 | 5 | Chờ |
| 05 | [Tài liệu, HDSD, RAG](phase-05-tai-lieu-hdsd.md) | tai-lieu-kiem-thu | 02, 04 | 2 | Chờ |

Thứ tự: **01 → (02 ∥ 03) → 04 → 05**. 02 và 03 chạy song song được (không chung tệp).

## Luật chung
- Không có phân bổ nào = hành vi hiện tại, từng con số (`ensure_balance` trả đúng `prorate_allocation(resolve_quota)` cũ).
- Không thêm khóa quyền (ENTITIES giữ nguyên, không đụng `SCOPE_FIELDS`, không đụng seed) — xem D4.
- Bộ mã mới (nếu có) SMALLINT + `IntEnum` ở `leave/constants.py`; trạng thái phân bổ là DẪN XUẤT theo ngày, không lưu.
- ⚠️ Tệp `leave/leave_policy.py` ĐÃ CÓ (CR-713, chặn lùi ngày) — module mới đặt tên `policy_*.py`, đừng đè.
- Migration `lvpol717` (down `lvcmp716`), viết tay, chạy lại được; autogenerate phải gọt (~650 dòng trôi).
- Không chạm quỹ năm đã qua; chỉ quỹ năm nay (`vn_today().year`) được tính lại, chỉ cột `allocated_days`.
- Cổng: pytest đúng tệp liên quan trong `api` (trần 2GB — chia nhóm `-k`), `npm run typecheck` trên host, `npx eslint
  src/modules/hr src/modules/report`, `npx vitest run src/modules/hr` / `src/modules/report`. Không chạy full.
- ReportKey **30** — nhờ `dieu-phoi` xác nhận số chưa ai cấp trước khi phase 03 bắt đầu.

## DECISIONS — cần anh Được chốt (phương án khuyến nghị đứng đầu)
- **D1 Thứ tự hạn mức**: (a) phân bổ chính sách của người > hình thức NV > cấp bậc > mặc định; loại không có trong chính sách
  → rơi về luật của loại. (b) như ERPNext: loại không có trong chính sách = 0 ngày.
- **D2 Đổi chính sách giữa năm**: (a) chia theo tháng — tháng nào phân bổ có hiệu lực vào ngày 15 thì tính theo chính sách
  đó (cùng quy ước 1–15 của CR-715). (b) chính sách hiệu lực đầu năm áp cả năm. (c) như ERPNext: cấp đủ quỹ mới cho lượt gán.
- **D3 Quỹ năm nay đã cấp khi tạo / sửa / xóa phân bổ**: (a) ô «Tính lại hạn mức năm nay» MẶC ĐỊNH BẬT, có xem trước
  trước→sau, chỉ sửa `allocated_days`, ghi nhật ký. (b) ô đó mặc định TẮT. (c) không bao giờ tính lại (chỉ áp lần cấp sau).
- **D4 Quyền**: (a) không thêm khóa — chính sách theo `leave_type`, phân bổ theo `leave_balance` (read xem, write
  tạo/sửa/xóa). (b) khóa mới `leave_policy` (hệ đang chạy phải tick tay, D-018).
- **D5 Tự phân bổ cho chính mình**: (a) chặn, trừ admin (cùng luật C1 CR-653, phiếu nghỉ bù). (b) cho như điều chỉnh tay.
- **D6 Chồng ngày**: (a) chặn; ô «Kết thúc chính sách cũ» tự đặt ngày kết thúc lượt đang hiệu lực = ngày bắt đầu mới − 1;
  cho phép «Đến ngày» trống = không thời hạn. (b) chặn tuyệt đối, «Đến ngày» bắt buộc như ERPNext.
- **D7 Menu**: (a) «Chính sách nghỉ phép» = thẻ thứ 4 của Thiết lập; «Phân bổ chính sách» = mục con mới của Nghỉ phép (sau
  Quỹ phép năm). (b) Phân bổ thành thẻ trong màn Quỹ phép năm.
- **D8 Báo cáo ngày lễ**: (a) nguồn phiếu nghỉ bù — mặc định chỉ Đã duyệt, ô «Gồm phiếu chờ duyệt»; tính cả ngày nghỉ
  theo lịch (Holiday List ERPNext cũng gồm ngày nghỉ tuần); tên «Nhân viên làm việc vào ngày lễ». (b) chỉ ngày lễ.
- **D9 Hở nhỏ**: (a) làm cả ba — chỉ số «Nghỉ bù cộng thêm» ở báo cáo Quỹ phép, «Tổng hợp theo người» (ma trận), hộp
  «Cấp quỹ» có lọc. (b) chỉ làm ma trận.

## Rollback
Từng phase revert được độc lập theo thứ tự ngược. `alembic downgrade lvcmp716` xóa 3 bảng mới; quỹ đã bị tính lại không tự
về — số trước/sau nằm trong `tab_audit_log` (entity `leave_balance`), sửa lại bằng «Điều chỉnh» hoặc xóa phân bổ kèm tính
lại. Khóa báo cáo 30 bỏ thì để trống số (không tái dùng).
