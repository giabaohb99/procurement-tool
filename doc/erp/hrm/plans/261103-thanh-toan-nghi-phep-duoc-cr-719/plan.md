---
title: "duoc-CR-719 — Thanh toán nghỉ phép (Leave Encashment)"
description: "Đổi ngày phép chưa nghỉ ra tiền (cuối năm hoặc nghỉ việc): phiếu ghi số ngày, duyệt trừ quỹ, sinh YCTT để kế toán nhập tiền và chi"
status: in-progress
priority: P2
effort: 32h
branch: erp-v2
tags: [hr, leave, finance, payment-request, erpnext]
created: 2026-11-03
---

# duoc-CR-719 — Thanh toán nghỉ phép (Leave Encashment)
Trạng thái kế hoạch: **đang làm** · CR liên quan: duoc-CR-719

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | planner | Nháp | duoc-CR-719 |

Người chủ chốt (FINAL): (1) bật theo **loại nghỉ** + trần, dùng cho **phép dư cuối năm** và **nghỉ việc** (Đ113 k3 BLLĐ);
(2) phiếu chỉ ghi **số ngày**, số tiền do người có quyền tài chính nhập sau, **không lộ lương**; (3) duyệt xong **trừ quỹ** và
**sinh YCTT** ở Tài chính; (4) ai lập **y ERPNext**. Nghiên cứu: [reports/research-erpnext-encashment.md](reports/research-erpnext-encashment.md).

| # | Giai đoạn | Chủ | Phụ thuộc | Giờ | Trạng thái |
|---|---|---|---|---|---|
| 01 | [BE nền: bảng, quyền, quỹ, chốt xem YCTT](phase-01-be-nen-bang-quyen-quy.md) | backend | merge `origin/erp-v2` | 5 | Chờ |
| 02 | [BE YCTT nguồn nghỉ phép](phase-02-be-yctt-nguon-nghi-phep.md) | backend | 01 | 5 | Chờ |
| 03 | [BE phiếu thanh toán nghỉ phép + duyệt + AI](phase-03-be-phieu-thanh-toan-nghi-phep.md) | backend | 01; chạy test tích hợp sau 02 | 8 | Chờ |
| 04 | [FE Nghỉ phép: phiếu, loại nghỉ, quỹ](phase-04-fe-nghi-phep.md) | giao-dien-v2 | 03 (API) | 8 | Chờ |
| 05 | [FE Tài chính: YCTT nhân sự + bản in](phase-05-fe-tai-chinh-yctt.md) | giao-dien-v2 | 02; bước 1 của 04 (`app-routes.ts`) | 4 | Chờ |
| 06 | [Tài liệu, HDSD, cẩm nang AI, RAG](phase-06-tai-lieu-hdsd.md) | tai-lieu-kiem-thu | 04, 05 | 2 | Chờ |

Thứ tự: **01 → (02 ∥ 03) → (04 ∥ 05) → 06**. 02 và 03 không chung tệp; 03 gọi hợp đồng hàm của 02 (`phase-02` mục **Hợp đồng**).

## Luồng dữ liệu
Nhân viên / Nhân sự lập phiếu (loại, năm quỹ, lý do, số ngày) → gửi duyệt: khóa dòng quỹ, kiểm `days ≤ encashable`, `pending += days`
→ bộ máy duyệt (luôn chặn tự duyệt) → duyệt: `pending −= days`, `encashed_days += days`, sinh **YCTT Nháp** (nguồn
`leave_encashment`, người nhận = nhân sự, tiền 0) → kế toán nhập tiền, gửi duyệt, duyệt, ghi **Đã chi** → phiếu hiện trạng thái chi
(đọc từ YCTT, không lưu hai nơi). Từ chối / trả về / rút → trả `pending`. Hủy phiếu đã duyệt → chỉ khi YCTT Nháp hoặc Đã từ chối.

## Luật chung
- Còn lại = tổng − dùng − giữ chỗ − mang đi − **đã thanh toán** (`encashed_days`); `remaining_days` vẫn là nơi tính duy nhất.
- Mã số SMALLINT + `IntEnum` ở `leave/constants.py`; trạng thái YCTT giữ mã chuỗi thu mua cũ (QĐ-9, không đổi).
- Migration `lvenc719` viết tay, chạy lại được, `down_revision` = **đầu thật sau khi merge** (03/11 là `hqx718b`; chạy `alembic heads`).
- Cổng: pytest đúng tệp (`--timeout=120`, chia `-k` nếu cần), `npm run typecheck` trên host, eslint + vitest theo thư mục.

## DECISIONS — ĐÃ CHỐT 03/11/2026: tất cả theo phương án (a)
Anh Được chọn trực tiếp D1(a), D2(a), D5(a), D7(a); D3, D4, D6, D8, D9 lấy (a).

- **D1 Ai thấy YCTT thanh toán nghỉ phép** (số tiền ÷ số ngày = lương ngày): (a) chốt ở `scope_condition`: chỉ ai có quyền YCTT
  **và** `leave_encashment.read` phủ phiếu đó; Quản lý / Nhân viên thu mua mặc định KHÔNG thấy → phải tick vai trò Kế toán.
  (b) như mọi YCTT (cả thu mua thấy — trái QĐ 2). (c) không sinh YCTT, chi ngay trên phiếu (ERPNext Unpaid/Paid — trái QĐ 3).
- **D2 Số tài khoản trên bản in YCTT**: (a) chỉ in khi người in có `employee_sensitive.read` hoặc là chính chủ, không thì để
  trống + ghi **Kế toán tự điền**. (b) luôn in. (c) không bao giờ in.
- **D3 Ai lập / duyệt** (y ERPNext: Employee lập nháp, HR submit): (a) mọi vai trò lập phạm vi **của mình**, Nhân sự lập hộ;
  `approve` chỉ `hr_leave`; trưởng bộ phận / công ty chỉ xem; luôn chặn tự duyệt. (b) chỉ Nhân sự lập.
- **D4 Số phiếu**: (a) một phiếu còn hiệu lực / (người, loại, năm) — khóa UNIQUE `active_key`; trần tính trên năm. (b) nhiều
  phiếu, chỉ trần cộng dồn.
- **D5 Nghỉ việc**: (a) bỏ qua hai trần, tính cả phần mang sang (luật trả hết ngày chưa nghỉ); bắt hồ sơ có `resign_date`.
  (b) áp trần như cuối năm.
- **D6 Phần mang sang khi cuối năm**: (a) như ERPNext — không đổi phần mang sang chưa dùng. (b) đổi cả.
- **D7 Kế toán từ chối YCTT**: (a) phiếu giữ Đã duyệt, hiện **Kế toán từ chối chi**; Nhân sự hủy phiếu để trả ngày. (b) tự hủy
  phiếu + trả ngày.
- **D8 Trợ lý AI**: (a) chỉ `my_leave_summary` biết số đã thanh toán + phiếu + luật loại; không công cụ soạn nháp. (b) thêm
  `draft_leave_encashment`.
- **D9 Năm quỹ**: (a) năm nay hoặc năm trước (năm trước đã kết sổ thì số dùng được = 0, tự chặn). (b) chỉ năm nay.

## Không làm (YAGNI)
Tự lập nháp lúc hết kỳ (`auto_leave_encashment`), tính tiền theo lương, Full and Final Statement, báo cáo mới (ReportKey).

## Rollback
Đảo thứ tự phase. `alembic downgrade <đầu trước>` xóa bảng + 5 cột; trước khi hạ phải không còn phiếu Đã duyệt (ngày đã trừ
nằm ở `encashed_days` — hạ cột là trả ngày im lặng). YCTT nguồn nghỉ phép đã chi: giữ, không xóa (sổ chi tiền).
