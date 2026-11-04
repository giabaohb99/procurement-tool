# Phase 01 — BE nền: bảng, khóa quyền, công thức quỹ, chốt xem YCTT

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Nháp | duoc-CR-719 |

## Context
- [plan.md](plan.md) D1, D3, D4. Nghiên cứu: [reports/research-erpnext-encashment.md](reports/research-erpnext-encashment.md).
- Khuôn: thêm khóa `leave_comp_request` ở commit `f9589aad` (permissions, scoping, entity_models, seed, scope_factory, b07);
  migration mẫu `lvcmp715_*.py`, `lvcmp716_*.py`; ngoại lệ đặc biệt trong `scoping.scope_condition` (nhánh `department`).
- Luật: `.claude/rules/hr-leave.md`, `.claude/rules/backend-input-limits.md`, `.claude/rules/chung-dat-ten-va-quy-uoc.md`.

## Tổng quan
P1. Dựng mọi thứ các phase sau đứng lên: bảng + cột, model, bộ mã, khóa quyền `leave_encashment`, cột `encashed_days` vào
công thức còn lại, và chốt chặn xem YCTT nguồn nghỉ phép (D1a). Không có đường API mới ở phase này.

## Mô hình dữ liệu — migration `lvenc719` (down = đầu thật sau `git merge origin/erp-v2`; 03/11 là `hqx718b`)
```
tab_leave_type        + allow_encashment Bool default 0 · max_encashable_days Float default 0 (0 = không trần, TRẦN THEO NĂM)
                      + non_encashable_days Float default 0
tab_leave_balance     + encashed_days Float default 0          (khoản TRỪ, vào công thức còn lại)
tab_payment_request   + payee_employee_id BIGINT default 0 · source_ref_id BIGINT default 0
                      + INDEX ix_payment_request_source_ref (source_type, source_ref_id)
tab_leave_encashment  id, code String(30) UNIQUE (TTP…), company_id, department_id, employee_id BIGINT,
                      leave_type_id BIGINT, balance_year SMALLINT, reason_kind SMALLINT, encashment_date Date,
                      days Float, balance_snapshot Float, encashable_snapshot Float, note String(1000) default '',
                      status SMALLINT default 1, approval_instance_id BIGINT default 0, decided_at DateTime NULL,
                      decision_note String(500) default '', payment_request_id BIGINT default 0,
                      active_key String(60) NULL, is_deleted Bool default 0, AuditMixin
                      INDEX (employee_id, balance_year) · UNIQUE uq_leave_encash_active_key (active_key)
```
Chỉ thêm khi thiếu (`_has_column`, `get_table_names`); downgrade bỏ đúng những gì thêm. Autogenerate quét ra ~650 dòng trôi —
viết tay, không autogenerate (memory: cắt tay migration).

## Bộ mã (`leave/constants.py`, R2)
- `LeaveEncashmentStatus(IntEnum)`: 1 Nháp · 2 Chờ duyệt · 3 Đã duyệt · 4 Từ chối · 5 Trả về chỉnh sửa · 6 Đã hủy (cùng số
  `LeaveCompStatus`) + `LEAVE_ENCASHMENT_STATUS_LABELS`, `ENCASH_EDITABLE_STATUSES = (1, 5)`, `ENCASH_ACTIVE_STATUSES = (1,2,3,5)`.
- `LeaveEncashmentReason(IntEnum)`: 1 Phép dư cuối năm · 2 Nghỉ việc + `LEAVE_ENCASHMENT_REASON_LABELS`.
- Hằng nguồn YCTT `PAYMENT_SOURCE_LEAVE_ENCASHMENT = "leave_encashment"` đặt ở `payment_request/hr_payout_guard.py` (một chỗ).

## Việc
1. **Model**: `leave/catalog_model.py` (3 cột loại nghỉ, chú thích tiếng Việt ghi nghĩa ERPNext + khác biệt trần theo năm);
   `leave/balance_model.py` (`encashed_days`, sửa docstring công thức, `remaining_days` trừ thêm `encashed_days or 0`);
   tệp mới `leave/encashment_model.py` (`LeaveEncashment`); `payment_request/model.py` (2 cột + chú thích "chỉ dùng khi
   `source_type = leave_encashment`"); khai `core/all_models.py`.
2. **Schema số dư**: `leave/schema.py` `LeaveBalanceResponse.encashed_days: float = 0.0`. Loại nghỉ: `LeaveTypeBase/Update/Response`
   thêm 3 trường (`max_encashable_days`, `non_encashable_days` `Field(ge=0, le=366)`).
3. **Chốt loại nghỉ** (`leave/catalog_controller.py`): `allow_encashment=True` mà `counts_balance=False` → 422
   *Loại nghỉ không trừ quỹ thì không có số dư để thanh toán — bật "Trừ vào quỹ phép" trước*. `_block_delete_used_type` hỏi thêm
   `tab_leave_encashment`.
4. **Báo cáo quỹ** (`leave/balance_report_spec.py`): thêm `encashed_days` vào `BAL_COLS`, trừ ở dòng tính còn lại (`:120`), chỉ số
   mới `encashed` *Đã thanh toán ra tiền* (kind days) — không thêm truy vấn (giữ bài đếm truy vấn xanh).
5. **Khóa quyền**: `core/permissions.py` ENTITIES + nhãn `"leave_encashment": "Nghỉ phép › Thanh toán nghỉ phép"`;
   `core/scoping.py` `SCOPE_FIELDS["leave_encashment"] = {company, dept_id, owner: created_by, self: employee_id}`;
   `core/entity_models.py`; `seed.py`: `_SYS_ENTITIES` thêm khóa, vòng `setdefault` cấp `(["read","create","write","delete"],"own")`,
   `dept_head` `(["read","export"],"dept")`, `company_head` `(["read","export"],"company")`, `hr_leave`
   `(["read","create","write","delete","approve","cancel","export"],"all")` (D3a). Không đụng `seed_prod.py` logic (D-018).
6. **Chốt xem YCTT (D1a)** — tệp mới `payment_request/hr_payout_guard.py`:
   `payout_visibility_cond(model, user, profile)` = `or_(model.source_type != "leave_encashment",
   model.source_ref_id.in_(select(LeaveEncashment.id).where(<scope_condition(LeaveEncashment, "leave_encashment", user, profile, "read")>)))`;
   phạm vi `leave_encashment` là `None` → trả `None`; là `false()` → chỉ còn nhánh `!=`.
   Gắn vào `scoping.scope_condition` (cùng kiểu nhánh `department`): `if entity == "payment_request"` → AND chốt này vào kết quả,
   **kể cả khi kết quả là `None` (thấy tất cả)**. Nhập trong hàm (tránh vòng nhập). Vì `apply_scope` + `get_scoped` + chuông
   duyệt (`get_approvers_for_entity` lọc theo phạm vi) đều qua `scope_condition`, một chỗ phủ mọi đường đọc.
7. **Bài kiểm** `test/backend/test_thanh_toan_nghi_phep_nen_cr719.py`: công thức còn lại trừ `encashed_days`; `available_days`
   MONTHLY vẫn đúng; chốt loại nghỉ 422; xóa loại đã có phiếu → chặn; chốt xem: pur_staff (YCTT company) không thấy YCTT nguồn nghỉ
   phép qua `apply_scope` + `get_scoped`; vai trò có `payment_request` + `leave_encashment.read company` thấy; admin thấy; YCTT
   thường không đổi. Sửa `test_pham_vi_khai_du_b07.py` (79 → 80, ghi lý do), `test/backend/scope_factory.py` thêm model.

## Tệp sở hữu
Sửa: `backend/app/modules/leave/{catalog_model,balance_model,schema,catalog_controller,balance_report_spec,constants}.py`,
`backend/app/modules/payment_request/model.py`, `backend/app/core/{all_models,permissions,scoping,entity_models}.py`,
`backend/app/seed.py`, `test/backend/{test_pham_vi_khai_du_b07,scope_factory}.py`.
Tạo: `backend/migrations/versions/lvenc719_thanh_toan_nghi_phep.py`, `backend/app/modules/leave/encashment_model.py`,
`backend/app/modules/payment_request/hr_payout_guard.py`, `test/backend/test_thanh_toan_nghi_phep_nen_cr719.py`.

## Xong khi
`alembic upgrade head` rồi `downgrade -1` rồi `upgrade` sạch trên local; bài kiểm phase + b07 + bài báo cáo quỹ hiện có
(`grep -l balance_report test/backend`) xanh; `alembic heads` ra MỘT đầu.

## Rủi ro
| Rủi ro | Khả năng × Tác động | Giảm |
|---|---|---|
| Chốt ở `scope_condition` làm chậm mọi danh sách YCTT (subquery) | Thấp × TB | `IN (SELECT id …)` có chỉ mục `source_ref`; chỉ áp cho `payment_request` |
| Quên một đường đọc YCTT không qua `scope_condition` | TB × Cao (lộ lương) | Phase 02 rà danh sách đường đọc (mục 7 nghiên cứu) + bài kiểm |
| Hai đầu alembic (nhánh khác cũng thêm migration) | TB × TB | `alembic heads` trước commit; đổi `down_revision` khi merge |
| Chỗ cộng tay `allocated + … − carried_out` ngoài model bỏ sót `encashed_days` | TB × TB | grep `carried_out_days` (6 tệp BE, 12 tệp FE) — bảng đã rà ở nghiên cứu |

## Bảo mật
Khóa mới nằm trong `_SYS_ENTITIES` → Quản lý thu mua không tự có. Chốt D1 mặc định ĐÓNG với YCTT nghỉ phép.
