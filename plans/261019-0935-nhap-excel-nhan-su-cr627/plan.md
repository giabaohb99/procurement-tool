---
title: "duoc-CR-627 — Nhập Excel nhân sự (frontend-v2) qua import_tool"
description: "Nút «Nhập Excel» ở màn Nhân sự v2, adapter EMPLOYEE đi qua employee service, đủ hồ sơ kể cả nhạy cảm, cấm xóa, tắt Import CSV cũ."
status: pending
priority: P1
effort: 3.5d
branch: erp-v2
tags: [hr, import, employee, security, frontend-v2]
created: 2026-10-19
---

# duoc-CR-627 — Nhập Excel nhân sự

## Mục tiêu
HR nhập/cập nhật hàng loạt hồ sơ nhân sự bằng `.xlsx` từ `/hr/employees` → chạy thử → ghi → hoàn tác
trên khung `import_tool` sẵn có. Mọi dòng đi qua **cùng lõi ghi** với màn hồ sơ (email trùng, vòng quản
lý, nhãn chức vụ, phòng chính, khóa TK khi nghỉ việc, xóa cache quyền), có **phạm vi dữ liệu** và
**`employee_sensitive.write`**. Tắt Import CSV cũ của Nhân sự + Phòng ban (giữ Export).

## Luồng dữ liệu
```
[FE] EmployeeImportButton → ImportUploadDialog(lockedModule=12) → POST /api/imports (gác import.create + employee.create|write)
  → precheck tiêu đề → StoredFile + ImportBatch(QUEUED) → Celery run_import
[Worker] catalog_import.run → adapter EMPLOYEE có hook → employee_import.prepare(ctx: user, profile, sensitive_ok)
  → mỗi dòng: parse ô (trống = giữ, __/empty_value/__ = xóa) → tra mã CT/PB/QL/CV → gác quyền + phạm vi
  → SAVEPOINT: employee service *_core (flush, không commit) → kiểm phạm vi SAU ghi → snapshot đủ cột
  → cuối: dry-run rollback / apply commit + finalize (audit, xóa cache quyền) → _persist log + ImportChange
[FE] điều hướng /system/imports/{id} xem log → «Ghi thật» / «Hoàn tác»
```

## Các pha
| # | Pha | Chặn bởi | Chạy song song với | Trạng thái |
|---|-----|----------|--------------------|-----------|
| 01 | [Tách lõi ghi employee service (không commit)](phase-01-tach-loi-ghi-employee-service.md) | — | 02, 05 | pending |
| 02 | [Khung catalog_import: hook adapter](phase-02-hook-adapter-catalog-import.md) | — | 01, 05 | pending |
| 03 | [Adapter Nhân sự mới (cột, parse, ghi, hoàn tác)](phase-03-adapter-nhan-su.md) | 01, 02 | 05 | pending |
| 04 | [Gác quyền import_tool + tắt CSV cũ](phase-04-gac-quyen-va-tat-csv-cu.md) | 03 | 05 | pending |
| 05 | [Frontend: nút Nhập Excel v2 + ẩn Import CSV v1](phase-05-frontend-nut-nhap-excel.md) | — | 01–04 | pending |
| 06 | [Kiểm thử đích + tài liệu](phase-06-kiem-thu-va-tai-lieu.md) | 01–05 | — | pending |

## Sở hữu tệp (không pha song song nào chung tệp)
- 01: `backend/app/modules/employee/service.py`, `employee/status_parse.py` (mới), `employee/controller.py` (chỉ dời `_status_code`)
- 02: `backend/app/modules/import_tool/catalog_import.py`, `import_tool/service.py`
- 03: `import_tool/employee_import_fields.py` (mới), `import_tool/employee_import.py` (mới)
- 04: `import_tool/controller.py`, `employee/controller.py` (CSV), `department/controller.py`
- 05: `frontend-v2/src/modules/hr/**`, `frontend/src/config/cruds.tsx`, `frontend/src/components/CrudList.tsx`
- 06: `test/backend/*cr627*`, test cũ bị ảnh hưởng, `doc/**`, `.claude/rules/hr-employee-profile.md`
- ⚠️ KHÔNG đụng `employee/position_service.py`, `test_danh_muc_chuc_vu.py`, `employee-detail-page.tsx` — đang có thay đổi chưa commit của việc khác.

## Ràng buộc môi trường
Máy tài nguyên hạn chế: **chỉ chạy test đích** (liệt kê ở từng pha), KHÔNG chạy cả `test/backend`,
KHÔNG `npm run check`/`npm run test`. `restart` thay `up --build`. Không migration (không đổi schema).

## Định nghĩa XONG (đo được)
1. Từ `/hr/employees` bấm «Nhập Excel» → tải mẫu → nhập 1 tệp ~40 cột → batch DONE, log đúng dòng.
2. Ô trống KHÔNG đổi giá trị cũ (test: người `resigned` nhập lại tệp thiếu ô Trạng thái → vẫn `resigned`).
3. Người thiếu `employee_sensitive.write`: cột nhạy cảm bị bỏ + 1 cảnh báo lô; DB không đổi cột đó.
4. Mã ngoài phạm vi → dòng lỗi, không tạo bản trùng; `__/delete/__` → dòng lỗi.
5. Hoàn tác khôi phục đủ mọi cột adapter ghi (kể cả nhạy cảm, ngày); bản ghi mới bị xóa hoặc chặn có lý do.
6. `POST /api/employees/import/csv` & `/api/departments/import/csv` → 410; v1 không còn nút Import CSV ở 2 màn.
7. Test đích xanh; `typecheck` + `lint` frontend-v2 0 lỗi.

## Rollback
Không migration → revert commit là đủ. Pha 01 giữ nguyên chữ ký `create/update/delete_employee`.
Pha 04 tắt CSV độc lập (revert riêng được). Dữ liệu đã nhập: dùng «Hoàn tác» của từng lô.

## Câu hỏi còn treo → xem cuối `phase-06`.
