# Pha 04 — Gác quyền ở import_tool + tắt Import CSV cũ

**Ưu tiên:** P1 · **Trạng thái:** pending · **Công:** 0.5d · **Chặn bởi:** 03 (tắt CSV thì độc lập)

## Quyết định gác (Đ-13c chưa làm — `ACTIONS` không có `import`)
Nhập Nhân sự = `import.<action>` **VÀ** quyền trên `employee`. Không thêm action mới, không migration.

| Đường | Gác hiện tại | Thêm cho `module == EMPLOYEE` |
|---|---|---|
| `POST /api/imports` | `import.create` | `employee.create` HOẶC `employee.write`, không thì 403 (trước khi lưu tệp) |
| `POST /api/imports/{bid}/commit` | `import.create` | như trên (người ghi thật có thể khác người chạy thử) |
| `POST /api/imports/{bid}/revert` | `import.delete` | `employee.write` |
| `GET /api/imports/{bid}/file` | `import.read` | `employee_sensitive.read` — tệp gốc chứa CCCD/STK; thiếu thì 403 «Tệp chứa thông tin nhạy cảm» |
| Worker (từng dòng) | — | đã làm ở pha 03 (`create`/`write` + `get_scoped` + `employee_sensitive.write`) |

Cài bằng một bảng nhỏ `_MODULE_GUARDS = {ImportModule.EMPLOYEE: {...}}` + hàm `_guard_module(db, user,
module, step)` trong `import_tool/controller.py` — chỗ cắm sẵn cho Đ-13c, không dựng khung.
Log/list batch giữ `import.read` (log không chứa giá trị nhạy cảm — pha 03).

## Tắt CSV cũ (giữ Export)
- `employee/controller.py:652-778` `import_employees_csv`: giữ route + tên hàm, thân thay bằng
  `raise HTTPException(410, "Nhập CSV nhân sự đã ngừng. Dùng «Nhập Excel» ở màn Nhân sự (ERP v2) — có chạy thử và hoàn tác.")`.
  Gỡ các import/khối không còn dùng.
- `department/controller.py:164-~240` `import_departments_csv`: tương tự, trỏ tới «Quản trị → Quản lý
  Import → Phòng ban».
- Giữ `require(...)` trên route (người không có quyền vẫn 403 như cũ — không lộ thêm gì).
- `export/csv`, `export/xlsx` KHÔNG đụng.

## Tệp
- Sửa: `backend/app/modules/import_tool/controller.py`, `backend/app/modules/employee/controller.py`,
  `backend/app/modules/department/controller.py`
- Sửa test: `test/backend/test_chot_xoa_to_chuc_cr190.py` — 2 test `test_csv_phong_ban_dong_xoa_qua_cung_chot`
  & `test_csv_nhan_su_dong_xoa_qua_cung_chot` đổi thành khẳng định 410 + DB không đổi (chốt xóa vẫn có
  test riêng qua `delete_employee`/nút xóa).

## Todo
- [ ] `_guard_module` + 4 điểm gác
- [ ] CSV nhân sự → 410; CSV phòng ban → 410
- [ ] Sửa 2 test cr190

## Test (chỉ chạy)
```bash
docker compose exec -T api python -m pytest -q test/backend/test_chot_xoa_to_chuc_cr190.py \
  test/backend/test_nhap_excel_nhan_su_quyen_cr628.py
```

## Thành công khi
- Có `import.create` mà thiếu cả `employee.create`/`write` → 403 ở upload, không tạo `StoredFile`.
- Thiếu `employee_sensitive.read` → 403 ở tải tệp lô Nhân sự; lô Kho vẫn tải bình thường.
- 2 đường CSV → 410, thông điệp tiếng Việt qua phong bì `{success:false,error}`.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Người dùng v1 đang quen Import CSV | Chắc×Thấp | 410 có câu chỉ đường; pha 05 ẩn nút |
| Script/ngoài gọi CSV | Thấp×Thấp | Không tìm thấy nơi gọi ngoài `CrudList.tsx` + 2 test |
| Vai trò `hr_profile` chưa có `import.*` / `employee_sensitive.write` (D-018) | Chắc×TB | Không đổi seed ở CR này; ghi hướng dẫn tick quyền ở luật HR (câu hỏi treo #1) |

## Rollback
Revert riêng commit pha này → CSV sống lại, gác import về như cũ.
