---
title: "Hợp đồng lao động — mẫu .docx theo pháp nhân"
description: "Lập HĐLĐ cho nhân sự từ mẫu Word (docxtpl) do từng pháp nhân tải lên; lưu bản ghi + tệp sinh + bản scan đã ký ở tab «Hợp đồng» của hồ sơ."
status: pending
priority: P2
effort: 27h
branch: erp-v2
tags: [hr, labor-contract, docx, docxtpl, permissions, frontend-v2, backend]
created: 2026-10-05
---

# Hợp đồng lao động (HĐLĐ) — mẫu theo pháp nhân

Lộ trình HRM: mục **V1-5** (`doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md`). `modules/contract` là HĐ NCC/khách — KHÔNG dùng lại.

## Luồng dữ liệu

```
HR (labor_contract_template.*)                   HR (labor_contract.*)
  │ upload .docx + company_id + contract_type      │ tab «Hợp đồng» /hr/employees/:id?tab=labor-contracts
  ▼                                                ▼
docx_engine.validate ──422 nếu tệp hỏng/biến lạ   create (snapshot company_id, department_id của NV)
  │ (zip-bomb, macro, sandbox, dry-run render)     │ chọn mẫu: chỉ mẫu active của company_id NV + đúng loại
  ▼                                                ▼
tab_file (riêng tư) ◄── tab_labor_contract_template  generate: build_context(contract, employee, company, dept)
                                                   → docxtpl render (Sandboxed, autoescape) → tab_file (snapshot)
                                                   ▼
                                     tải .docx (print) · tải lên bản scan đã ký · chuyển trạng thái
```

## Phases

| # | Phase | Effort | Phụ thuộc | Status |
|---|---|---|---|---|
| 01 | [Nền dữ liệu, bộ mã, quyền](phase-01-nen-du-lieu-bo-ma-quyen.md) | 3h | — | done |
| 02 | [Bộ máy docx + danh mục biến](phase-02-bo-may-docx-danh-muc-bien.md) | 4h | 01 | done |
| 03 | [API Mẫu hợp đồng](phase-03-api-mau-hop-dong.md) | 3h | 02 | done |
| 04 | [API Hợp đồng lao động](phase-04-api-hop-dong-lao-dong.md) | 5h | 03 | done |
| 05 | [FE màn Mẫu hợp đồng](phase-05-fe-man-mau-hop-dong.md) | 4h | 03 | done |
| 06 | [FE tab «Hợp đồng» trong hồ sơ](phase-06-fe-tab-hop-dong-ho-so.md) | 5h | 04, 05 | done |
| 07 | [Kiểm thử chéo, tài liệu, triển khai](phase-07-kiem-thu-tai-lieu-trien-khai.md) | 3h | 01–06 | pending |

Chạy song song được: **05 ∥ 04** (05 chỉ cần API mẫu). 06 sau 05 vì 05 sở hữu `query-keys.ts`, `app-routes.ts`, `types/labor-contract*.ts`.

## Quyết định khóa (đã chốt với user + chốt kỹ thuật)

- Mẫu = **.docx tải lên**, biến `{{ ten_bien }}`; render bằng **`docxtpl==0.20.2`** (cần `jinja2`, `lxml`, `python-docx` — đã có 1.2.0; Python 3.12 ok).
- Mẫu gắn **company_id + contract_type**; nhiều mẫu / pháp nhân.
- 2 khóa quyền mới: `labor_contract` (lương = nhạy cảm, tách khỏi `employee`) và `labor_contract_template` (luật «một khóa = một màn hình», CR-157). ENTITIES **72 → 74**, cả hai vào `_SYS_ENTITIES`.
- Module backend mới `app/modules/labor_contract/` (không nhồi thêm vào `employee/` đã 29 tệp).
- Tệp (mẫu, bản sinh, bản scan) lưu `tab_file` + cột `*_file_id`, **không qua `FileLink`** → mọi đường tải đi qua endpoint riêng có `get_scoped`; không trả `url`.
- Trạng thái `HẾT HẠN` là **suy ra** (SIGNED + end_date < `vn_today()`), số 3 giữ chỗ, không ghi xuống DB (không cần job).

## Ngoài phạm vi (YAGNI)

Phụ lục HĐ · bảng con phụ cấp nhiều dòng · ký số · cảnh báo/báo cáo sắp hết hạn · nhân viên tự xem HĐ của mình (`/me`) · xuất PDF · đọc ké «loại HĐ hiện tại» lên tab Chung.

## Rollback

Mỗi phase 1 commit. Gỡ: revert commit FE → revert BE → `alembic downgrade wsched01` (drop 2 bảng). Tệp trên storage mồ côi vô hại. Dòng `tab_role_permission` của 2 khóa còn lại vô hại (khóa lạ bị bỏ qua) — xóa tay nếu cần.
