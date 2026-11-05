# Phase 01 — BE nền thanh toán nghỉ phép (duoc-CR-719)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Hiệu lực | duoc-CR-719 |

Trạng thái: xong, chưa commit. Alembic: MỘT đầu `lvenc719` (down = `hqx718b`), upgrade → downgrade -1 → upgrade sạch trên local.

## Tệp đã đổi
Sửa: `leave/{catalog_model,balance_model,schema,catalog_controller,balance_report_spec,constants}.py`,
`payment_request/model.py`, `core/{all_models,permissions,scoping,entity_models}.py`, `seed.py`,
`test/backend/{test_pham_vi_khai_du_b07 (79 -> 80, ghi lý do),scope_factory}.py`.
Tạo: `migrations/versions/lvenc719_thanh_toan_nghi_phep.py`, `leave/encashment_model.py`,
`payment_request/hr_payout_guard.py`, `test/backend/test_thanh_toan_nghi_phep_nen_cr719.py` (16 bài).

## Hợp đồng cho phase 02 / 03

**Bộ mã** (`leave/constants.py`): `LeaveEncashmentStatus` (DRAFT 1, PENDING 2, APPROVED 3, REJECTED 4, RETURNED 5,
CANCELLED 6) + `LEAVE_ENCASHMENT_STATUS_LABELS`; `ENCASH_EDITABLE_STATUSES = (1, 5)`;
`ENCASH_ACTIVE_STATUSES = (1, 2, 3, 5)`; `LeaveEncashmentReason` (YEAR_END 1, RESIGNATION 2) +
`LEAVE_ENCASHMENT_REASON_LABELS`. Các tuple chứa member IntEnum (so sánh với int được).

**Hằng nguồn YCTT**: `payment_request.hr_payout_guard.PAYMENT_SOURCE_LEAVE_ENCASHMENT = "leave_encashment"`.
Lưu ý `tab_payment_request.source_type` là `String(20)`; "leave_encashment" = 16 ký tự, vừa.

**Model `LeaveEncashment`** (`leave/encashment_model.py`, bảng `tab_leave_encashment`): `code` (TTP…, UNIQUE, String 30),
`company_id`, `department_id`, `employee_id`, `leave_type_id`, `balance_year`, `reason_kind`, `encashment_date` (Date, NULL),
`days`, `balance_snapshot`, `encashable_snapshot`, `note` (1000), `status`, `approval_instance_id`, `decided_at`,
`decision_note` (500), `payment_request_id`, `active_key` (String 60, NULL, UNIQUE `uq_leave_encash_active_key`),
`is_deleted` (Boolean, KHÔNG dùng SoftDeleteMixin; tự lọc bằng `not_deleted_cond` / `apply_scope` đã tự loại),
AuditMixin. Chỉ mục `(employee_id, balance_year)`. `active_key` quy ước đề xuất `"<employee_id>:<leave_type_id>:<balance_year>"`
(<= 60 ký tự), NULL khi REJECTED/CANCELLED/xóa; phase 03 là nơi đặt/gỡ nó.

**Cột mới**:
- `LeaveType.allow_encashment` (bool, mặc định 0), `max_encashable_days` (trần THEO NĂM, 0 = không trần),
  `non_encashable_days` (số ngày giữ lại, chỉ lý do cuối năm). Schema `LeaveTypeBase/Update/Response` đã có 3 trường (`ge=0, le=366`).
- `LeaveBalance.encashed_days` (khoản TRỪ). `remaining_days` đã trừ `encashed_days or 0`; `LeaveBalanceResponse.encashed_days`.
  `available_days` / `available_days_map` đi qua `remaining_days` nên tự đúng (có bài kiểm MONTHLY). Phase 03 chỉ việc
  `row.encashed_days += days` khi duyệt, `-= days` khi hủy; KHÔNG sửa công thức ở chỗ khác.
- `PaymentRequest.payee_employee_id`, `PaymentRequest.source_ref_id` (BigInteger, mặc định 0) + chỉ mục
  `ix_payment_request_source_ref (source_type, source_ref_id)`. `PaymentRequestResponse` / schema YCTT CHƯA có hai trường
  này (thuộc phase 02, file `payment_request/schema.py` không nằm trong phase 01).

**Chốt loại nghỉ** (`catalog_controller`): `allow_encashment` mà `counts_balance = False` -> 422 (tạo và sửa; sửa lẻ lấy giá trị
đang có). `_block_delete_used_type` chặn xóa khi có phiếu `LeaveEncashment` ở bất kỳ trạng thái nào (400).

**Báo cáo quỹ**: `BAL_COLS` có `encashed_days`; `BalanceRow.encashed`; chỉ số `encashed` "Đã thanh toán ra tiền" (kind days);
dòng tính còn lại đã trừ `encashed_days`. Không thêm truy vấn.

**Khóa quyền `leave_encashment`**: có trong `ENTITIES` (80), nhãn "Nghỉ phép › Thanh toán nghỉ phép", `SCOPE_FIELDS`
(company, dept_id, owner `created_by`, self `employee_id`), `entity_models` (-> `LeaveEncashment`), `_SYS_ENTITIES`.
Seed: mọi vai trò `(read, create, write, delete)` `own`; `dept_head` `(read, export)` `dept`; `company_head`
`(read, export)` `company`; `hr_leave` `(read, create, write, delete, approve, cancel, export)` `all`.
Lưu ý: pur_manager cũng nhận `own` qua vòng `setdefault` (giống `leave_comp_request`), KHÔNG nhận `all`.
`seed_prod.py` không đụng (D-018): vai trò trên hệ chạy phải tick tay hoặc `SEED_FORCE_SYNC` một lần.

**Chốt xem YCTT (D1a)**: `scoping.scope_condition` nay là vỏ bọc; thân cũ đổi tên `_grant_scope_condition`. Với
`entity == "payment_request"` vỏ AND thêm `hr_payout_guard.payout_visibility_cond(model, user, profile)` (kể cả khi phạm vi
YCTT là None). Guard: phạm vi `leave_encashment.read` là None -> không thu hẹp; `false()` -> chỉ còn YCTT có
`source_type != "leave_encashment"`; còn lại `source_type != ... OR source_ref_id IN (SELECT id FROM tab_leave_encashment WHERE <phạm vi>)`.
Phủ `apply_scope`, `get_scoped`, `get_approvers_for_entity`.

## Việc phase 02 phải rà (đường đọc YCTT KHÔNG qua `scope_condition`)
Chưa rà trong phase này (ngoài tệp sở hữu). Cần grep trong `payment_request/*`, báo cáo công nợ/Tài chính, trợ lý AI/MCP,
thông báo duyệt, tìm kiếm toàn cục, xuất Excel: mọi chỗ `db.get(PaymentRequest, ...)` hoặc `db.query(PaymentRequest)` thẳng.
Kiểm `has_global_scope(profile, "payment_request", ...)` ở các controller: grep nhanh trong `backend/app` không thấy chỗ nào dùng
nó cho payment_request, nhưng phase 02 nên xác nhận lại. Hai trường `payee_employee_id` / `source_ref_id` cũng cần vào schema.

## Kiểm
- `test_thanh_toan_nghi_phep_nen_cr719.py` 16 bài xanh (công thức còn lại, MONTHLY, bộ mã, chốt loại nghỉ, xóa loại, khóa quyền,
  seed, chốt xem YCTT: nhân viên thu mua không thấy + 404 qua id, có cả hai khóa thấy, `leave_encashment` phạm vi own thu hẹp,
  `all` thấy hết, YCTT thường không đổi).
- `test_pham_vi_khai_du_b07.py` xanh (80/80).
- `test_pham_vi_duong_vong`, `test_pham_vi_luat_bat_bien`, `test_canh_do_dai_o_chu_cr538`: 107 xanh.
- 8 tệp YCTT/payment (`test_payment_*`, `test_yctt_*`, `test_thong_bao_duyet_dmh_yctt_cr662`): 106 xanh.
- `-k "(nghi_phep or cr715 or cr717 or quy_phep)"`: 788 xanh (gồm bài báo cáo quỹ).
- Lỗi có sẵn, không do phase này: `test_ton_kho_chan_trung_cr717.py::test_migration_kiem_trung_truoc_khi_them_rang_buoc`
  (đòi `down_revision == lvcmp716` nhưng đầu hiện là `hqx718`); bài customs/forum đã biết không chạy lần này.
- Chưa chạy: toàn bộ `test/backend` (máy yếu), `tsc` (không đụng frontend).

## Câu hỏi còn mở
1. `PaymentRequestResponse` thêm hai trường mới thuộc phase 02 (file không nằm trong phase 01) — xác nhận.
2. `tab_leave_encashment.is_deleted` dùng cột Boolean riêng như `LeaveCompRequest`, không SoftDeleteMixin — theo đúng spec.
3. `test_ton_kho_chan_trung_cr717` đỏ sẵn: cần người giữ CR-717 sửa kỳ vọng `down_revision`.

**Status:** DONE
**Summary:** Bảng/cột/model/bộ mã/khóa quyền/công thức quỹ/chốt xem YCTT (D1a) xong, migration `lvenc719` chạy lên-xuống-lên sạch, 16 bài mới + hồi quy liên quan xanh.
**Concerns/Blockers:** Phase 02 phải rà các đường đọc YCTT không đi qua `scope_condition`; một bài của CR-717 đỏ sẵn (không do phase này).
