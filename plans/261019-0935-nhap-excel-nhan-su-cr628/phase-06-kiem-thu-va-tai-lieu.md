# Pha 06 — Kiểm thử đích + tài liệu

**Ưu tiên:** P1 · **Trạng thái:** completed · **Công:** 0.5d · **Chặn bởi:** 01–05
(Test viết SONG SONG với pha 01/03/04; pha này là lượt chạy gom + tài liệu.)

## Test backend mới (pytest, SQLite — chỉ chạy đúng các tệp liệt kê)
`test/backend/test_nhap_excel_nhan_su_cr628.py` (nghiệp vụ, dùng `seed` + người tạo lô = admin):
1. Ô trống giữ nguyên: NV `resigned`, `is_active=0` → nhập tệp có cột Trạng thái/Đang dùng để trống → không đổi.
2. `__/empty_value/__` xóa `bank_branch`, `hire_date`, `manager_id`; trên `full_name`/`status` → ERROR.
3. Trạng thái nhận mã + nhãn + bỏ dấu; giá trị lạ → ERROR, không mặc định `official`.
4. Mã số (giới tính/cấp bậc/hình thức) nhận số + nhãn; sai → ERROR.
5. Ngày `dd/mm/yyyy`, ô ngày Excel, năm 0001 → ERROR (schema).
6. Chuỗi vượt trần (`tax_code` 21 ký tự, `phone` 26) → ERROR dòng, batch DONE (không 500).
7. Email trùng NV khác → ERROR (lõi `ensure_email_unique`).
8. Quản lý theo mã; tự quản lý mình / vòng A→B→A → ERROR (`block_manager_cycle`).
9. Phòng ban theo mã; tên trùng ở 2 công ty → ERROR; PB khác công ty → ERROR (L3).
10. Chức vụ theo mã/tên → `position` = tên danh mục (`sync_label`); không khớp → REVIEW, giữ chữ.
11. Đổi phòng chính → `tab_employee_department` khớp (`_sync_primary_department`).
12. `__/delete/__` → ERROR `delete_not_allowed`, bản ghi còn nguyên.
13. Dry-run chuyển `resigned` → DB không đổi, TK vẫn hoạt động, có WARNING «sẽ khóa»; apply → TK khóa + `token_version` tăng.
14. Hoàn tác lô sửa → khôi phục ĐỦ cột (gồm `id_number`, `date_of_birth`, `bank_account_no`, `position`); TK đã khóa KHÔNG mở lại.
15. Hoàn tác lô tạo: NV mới chưa ai tham chiếu → xóa (kể cả dòng `tab_employee_department`); NV mới đã gắn TK → từ chối cả lượt kèm mã.
16. Lõi `update_employee_core` không commit (rollback → DB y cũ); `lock_users=False` không khóa TK.
17. Tệp > 2000 dòng → `ImportValidationError`.
18. Mẫu: không có cột «Hành động», có sheet «Huong dan», đủ tiêu đề `EMPLOYEE_FIELDS`; tệp xuất 8 cột cũ
    (`Số điện thoại`, `Trạng thái NS`, `Vị trí`) nhập lại được nhờ alias.

`test/backend/test_nhap_excel_nhan_su_quyen_cr628.py` (quyền / phạm vi / nhạy cảm):
1. Phạm vi `company`: mã NV công ty khác → ERROR, không tạo bản trùng, không đổi.
2. Tạo NV vào công ty ngoài phạm vi → ERROR (kiểm phạm vi SAU ghi), savepoint lùi sạch.
3. Chỉ `employee.write` (không `create`): dòng mới ERROR, dòng sửa OK; ngược lại tương tự.
4. Thiếu `employee_sensitive.write`: cột **S** bị bỏ, 1 WARNING `sensitive_ignored`, DB cột S không đổi, cột thường vẫn ghi.
5. Có `employee_sensitive.write`: ghi được CCCD/STK.
6. Không `ImportLog.message`/`ref_key` nào chứa giá trị cột S (quét chuỗi CCCD/STK mẫu), kể cả khi lỗi độ dài.
7. Tự đổi phòng ban của chính mình qua tệp → ERROR (L1); gán PB ngoài phạm vi → ERROR (L2).
8. Upload lô EMPLOYEE thiếu `employee.create`+`write` → 403, không có `StoredFile` mới.
9. Tải tệp lô EMPLOYEE thiếu `employee_sensitive.read` → 403; lô WAREHOUSE → 200.
10. Revert lô EMPLOYEE thiếu `employee.write` → 403.
11. `POST /api/employees/import/csv` và `/api/departments/import/csv` → 410.

## Lệnh chạy (đích, KHÔNG quét cả `test/backend`)
```bash
docker compose exec -T api python -m pytest -q \
  test/backend/test_nhap_excel_nhan_su_cr628.py test/backend/test_nhap_excel_nhan_su_quyen_cr628.py \
  test/backend/test_import_catalog.py test/backend/test_chot_xoa_to_chuc_cr190.py \
  test/backend/test_nhan_su_ncc_b03.py test/backend/test_nghi_viec_da_phien_cr400.py \
  test/backend/test_employee_email_trung_cr368.py test/backend/test_employee_position.py \
  test/backend/test_kiem_nhiem_phong_ban.py test/backend/test_employee_delete_account.py \
  test/backend/test_ho_so_nhan_su_dot1.py test/backend/test_qua_trinh_cong_tac_thoi_viec.py
docker compose exec -T erp npm run typecheck && docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr/components/employee-import-button.test.tsx src/modules/hr/pages
```
Không cần `restart api` (bind-mount + `--reload`); worker Celery KHÔNG tự nạp lại → `docker compose restart celery-worker` trước khi thử tay.

## Thử tay (E2E nhẹ, không Playwright mới)
Tài khoản HR có `import.read/create` + `employee.*` + `employee_sensitive.read/write`: tải mẫu → điền 3 dòng
(1 mới, 1 sửa, 1 nghỉ việc) → chạy thử → xem log → ghi thật → hoàn tác. Lặp với tài khoản thiếu
`employee_sensitive.write`.

## Tài liệu phải cập nhật
- `doc/erp/nen-tang/16-quan-ly-import-export-v2.md`: §3.1 dòng `employee` (đủ hồ sơ, ref theo mã, cấm xóa); §9.1
  thêm mục «duoc-CR-628» (hook adapter, gác kép `import` × `employee`, tải tệp lô cần
  `employee_sensitive.read`); §1 ghi CSV Nhân sự + Phòng ban đã 410; §10 bẫy: ô trống = giữ, snapshot rõ.
- `.claude/rules/hr-employee-profile.md`: mục mới «NHẬP EXCEL NHÂN SỰ (duoc-CR-628)» — 5 gạch:
  (1) mọi đường ghi hàng loạt phải qua `*_core` của `service.py`, cấm `setattr` trần;
  (2) ô trống = giữ, chỉ `__/empty_value/__` xóa; (3) cột nhạy cảm cần `employee_sensitive.write` — lấy
  từ `SENSITIVE_FIELDS`, không gõ danh sách thứ hai; (4) tệp lô Nhân sự & `tab_import_change.snapshot`
  chứa bản rõ — tải tệp gác `employee_sensitive.read`; (5) vai trò cũ cần tick `import.read/create` +
  `employee_sensitive.write` (D-018). Thêm `import_tool/employee_import*.py` + `test/backend/*cr628*` vào `paths:`.
- `doc/tai-lieu-ky-thuat/change-log.md`: dòng `duoc-CR-628-nhap-excel-nhan-su` (đã đặt chỗ, dòng 43) →
  điền tệp/commit, trạng thái «Xong».
- `doc/tai-lieu-ky-thuat/nhat-ky-task.md`: một mục câu tiếng Việt trọn vẹn, mã mục duy nhất, dòng cuối
  `Mã nguồn:` / `Commit:`; `pic` NSU209.

## Todo
- [x] 2 tệp test mới (≈29 ca) + sửa test cũ (pha 01/03/04)
- [x] Lượt chạy gom ở trên xanh
- [ ] Thử tay 2 tài khoản (chưa làm — cần UI + celery, ghi trong báo cáo)
- [x] 4 tài liệu
- [ ] `code-reviewer` rà trước commit (để điều phối viên)

## Câu hỏi còn treo
1. Có thêm `import: [read, create]` + `employee_sensitive: [write]` vào vai trò mẫu `hr_profile` ở `seed.py`
   không? Lưu ý: `import.read` là toàn cục — HR sẽ thấy cả lô nhập Thu mua/Kho (danh sách + log). Mặc định
   kế hoạch: KHÔNG đổi seed, admin tick tay.
2. Có cần nút «Xuất Excel» ở màn Nhân sự không, hay giữ xuất tập trung `/system/exports` (CR-172)? Nếu cần,
   bản xuất có nên mở rộng đủ cột như mẫu nhập (khứ hồi) và ghi `ExportLog` không? Mặc định: không làm.
3. Bản chụp hoàn tác (`tab_import_change.snapshot`) giữ CCCD/STK bản rõ vĩnh viễn — có cần dọn sau N ngày
   (vd 30) hoặc khi lô hết hạn hoàn tác không? Mặc định: chưa dọn, ghi vào luật.
4. Thiếu `Mã NV` → tạo mới với mã `NSU` tự sinh (như màn nhập tay) hay bắt buộc mã? Mặc định: tự sinh +
   INFO nêu mã mới (nhập lại tệp cũ mà không điền mã sẽ đẻ trùng nếu không có email).
5. Lô có cột nhạy cảm mà người nhập thiếu quyền: bỏ cột + cảnh báo (mặc định) hay chặn cả tệp từ bước tải lên?
