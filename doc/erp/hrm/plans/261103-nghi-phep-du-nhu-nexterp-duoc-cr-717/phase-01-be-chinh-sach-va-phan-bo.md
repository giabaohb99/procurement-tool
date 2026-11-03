# Phase 01 — BE: Chính sách nghỉ phép + Phân bổ chính sách

## Context
- ERPNext: `hrms/hr/doctype/leave_policy*`, `leave_policy_assignment/leave_policy_assignment.py` (overlap `:70`, cấp quỹ
  `:111`, tỷ lệ `:505`, hàng loạt `:523`), `leave_control_panel.py`.
- DEGO: `leave/balance_service.ensure_balance` (điểm cấp quỹ DUY NHẤT), `leave/accrual_service.py` (`resolve_quota`,
  `prorate_allocation`, `first_month_in_year`, `round_half_up`), `leave/balance_controller.allocate/close_year` (mẫu gác
  phạm vi `apply_scope(Employee, "employee")`), `leave/catalog_controller.py` (mẫu `quota_router` thay-cả-danh-sách,
  `_block_delete_used_type`), migration mẫu `lvcmp716_*.py`.
- Quyết định áp theo phương án (a) của D1–D6 ở `plan.md`. Đổi phương án → sửa mục **Luật** dưới đây trước khi code.

## Tổng quan
Ưu tiên P2. Gói chính sách = danh sách (loại nghỉ, số ngày/năm). Phân bổ = gán gói cho một nhân sự trong `[từ, đến]`
(đến trống = không thời hạn). Quỹ vẫn theo NĂM DƯƠNG LỊCH: phân bổ chỉ đổi cách tính `allocated_days`.

## Mô hình dữ liệu (migration `lvpol717`, down `lvcmp716`)
```
tab_leave_policy            id, code String(30) UNIQUE, name String(150), note String(500) default '',
                            is_active Bool default 1, AuditMixin
tab_leave_policy_line       id, policy_id BIGINT idx, leave_type_id BIGINT, annual_days Float default 0, AuditMixin
                            UNIQUE(policy_id, leave_type_id)
tab_leave_policy_assignment id, employee_id BIGINT, company_id BIGINT (chép từ hồ sơ lúc tạo — cho apply_scope),
                            policy_id BIGINT idx, effective_from Date NOT NULL, effective_to Date NULL (= không thời hạn),
                            note String(500) default '', AuditMixin
                            UNIQUE(employee_id, effective_from)  -- chống bấm đúp; chồng ngày chặn ở service
                            INDEX(employee_id, effective_from, effective_to)
```
Không đổi `tab_leave_balance`. Thêm 3 model vào `core/all_models.py`.

## Luật
1. **Hạn mức theo tháng (D1+D2)** — hàm thuần mới `leave/policy_allocation_math.py`:
   - Tháng `m` của năm `Y` thuộc phân bổ `A` ⇔ `A.from ≤ date(Y,m,15) ≤ (A.to or ∞)`.
   - `q(m)` = `annual_days` của dòng chính sách khớp loại nghỉ nếu tháng đó có phân bổ VÀ chính sách có dòng loại đó; còn
     lại `q(m)` = `resolve_quota(type, employee)` (luật cũ hình thức > cấp bậc > mặc định).
   - Tập tháng tính: FULL_YEAR → 1..12; PRORATA_HIRE / MONTHLY → `first_month_in_year(hire, Y)`..12 (rỗng nếu 13).
   - Không tháng nào có phân bổ khớp loại đó, hoặc mọi `q(m)` bằng nhau → trả **đúng** `prorate_allocation(q, mode, hire, Y)`
     (giữ nguyên làm tròn cũ, kể cả hạn mức lẻ như 12.25). Ngược lại `round_half_up(Σ q(m) / 12)`.
   - Ví dụ chốt test: 12 → 15 từ 01/07 = 13.5; từ 16/07 (tháng 7 còn chính sách cũ) = 13.25 → 13.5; vào làm 10/03, PRORATA,
     chính sách 15 cả năm = 12.5; FULL_YEAR vào làm giữa năm, chính sách 15 cả năm = 15; phân bổ kết thúc 14/09 → tháng 9
     về luật loại.
   - Thâm niên, mang sang, điều chỉnh, nghỉ bù KHÔNG đổi. MONTHLY: `accrual_holdback` giữ nguyên công thức tỷ lệ tháng trên
     `allocated_days` (xấp xỉ khi đổi chính sách giữa năm — ghi rõ trong docstring, chấp nhận).
2. **`ensure_balance`** thay `prorate_allocation(resolve_quota(...))` bằng `policy_allocation.allocated_days(db, type,
   employee, year)` (module DB mới `leave/policy_allocation.py`: 1 truy vấn nạp phân bổ chồng năm `Y` của người + dòng
   chính sách loại đó, rồi gọi hàm thuần). `resolve_quota` giữ nguyên chữ ký.
3. **Chính sách**: dòng phải là loại `counts_balance=True`, `is_compensatory=False` (422 kèm tên loại); `annual_days`
   0–366, bước 0.5; ≤ 50 dòng. `is_active=False` chỉ chặn phân bổ MỚI; phân bổ đang có vẫn áp. Xóa chính sách khi còn phân
   bổ → 409 **Chính sách đang được phân bổ cho N nhân sự — kết thúc / xóa phân bổ trước**. Sửa dòng chính sách KHÔNG tự tính
   lại quỹ đã cấp (luật CR-715), chỉ áp lần cấp sau / lần tính lại.
4. **Phân bổ — chốt khi tạo** (thứ tự): nhân sự tồn tại + trong `apply_scope(Employee, "employee", ..., "write")` (ngoài
   phạm vi → 404) · không phải chính mình trừ admin (403, D5) · chính sách đang dùng (422) · `to ≥ from`, năm 2000–2100
   (schema) · khóa hàng `tab_employee` của người đó `FOR UPDATE` (MySQL; SQLite bỏ qua) rồi kiểm chồng ngày → 409
   **Nhân sự X đã có chính sách Y từ dd/mm/yyyy đến dd/mm/yyyy | không thời hạn**. Ngoại lệ D6: `close_previous=true` và
   lượt chồng DUY NHẤT bắt đầu TRƯỚC `from` → đặt `to` của nó = `from − 1 ngày`. UNIQUE vỡ → 409.
5. **Áp ngay vào quỹ năm nay** (`Y = vn_today().year`), chỉ khi phân bổ (mới hoặc cũ bị đóng) chồng năm `Y`; loại xét =
   hợp các loại trong (chính sách mới ∪ chính sách của lượt bị đóng), chỉ loại đang dùng + trừ quỹ:
   - chưa có dòng quỹ → `ensure_balance` (tự ra số theo luật 1) — đếm `created`;
   - có dòng, `recalc_current_year=true` (D3) → `allocated_days` = số mới nếu khác; ghi `audit_record(..., commit=False)`
     **Phân bổ chính sách P: hạn mức loại X năm Y a → b ngày**; đếm `recalculated` kèm `[{leave_type_id, before, after}]`;
   - có dòng, không tính lại → giữ nguyên, đếm `kept`. Năm đã qua: không bao giờ đụng.
   - Kết quả có `negative_after` = các dòng mà `available_days` < `-max_negative_days` sau tính lại (cảnh báo, không chặn).
6. **Sửa phân bổ**: chỉ `effective_to`, `note` (+ `recalc_current_year`). Đổi chính sách / ngày bắt đầu = xóa rồi tạo
   lại. Kiểm chồng ngày lại khi kéo dài. **Xóa**: được, kèm `?recalc_current_year=` (tính lại các loại của chính sách đó).
7. **Hàng loạt**: tối đa 500 `employee_ids`; mỗi người một `db.begin_nested()`; lỗi chốt (409/403/404/422) → vào
   `skipped[{employee_id, name, reason}]`, không hỏng cả lô; một commit cuối + một dòng audit tổng. Lỗi CSDL không phải
   chốt nghiệp vụ → cuộn cả lô, chỉ trả tên lớp lỗi.
8. **Xem trước** (`/preview`) dùng CHUNG hàm `plan_change(...)` với đường ghi (dựng danh sách phân bổ sau thay đổi trong bộ
   nhớ → tính trước/sau bằng hàm thuần), KHÔNG ghi gì. Số truy vấn cố định với mọi số người: hồ sơ (1) + phân bổ của cả
   nhóm (1) + dòng chính sách liên quan (1) + dòng quỹ năm `Y` (1) + luật hạn mức theo nhóm (1/loại) + loại nghỉ (1).

## API (phong bì chuẩn; `String(n)` có `max_length`)
| Đường | Gác | Ghi chú |
|---|---|---|
| `GET/POST /api/leave-policies`, `GET/PATCH/DELETE /api/leave-policies/{id}` | `leave_type` read/create/write/delete | `make_crud_router`, hook chặn xóa (luật 3), `code` không đổi sau khi tạo |
| `GET /api/leave-policies/{id}/lines` · `PUT …/lines` | `leave_type` read / write | thay cả danh sách `[{leave_type_id, annual_days}]`, mẫu `quota_router` |
| `GET /api/leave-policy-assignments` | `leave_balance.read` + `apply_scope(Assignment, "leave_balance")` | lọc `employee_id, policy_id, company_id, active_on, search` (tên/mã — dùng lại `apply_employee_search` kiểu dịch sang id); trả `employee_name, employee_code, policy_name, state` (1 sắp tới · 2 hiệu lực · 3 đã kết thúc — IntEnum `LeavePolicyAssignmentState`, DẪN XUẤT theo `vn_today`) |
| `GET /api/leave-policy-assignments/{id}` | `leave_balance.read` + `get_scoped` | |
| `POST /api/leave-policy-assignments` | `leave_balance.write` | `{employee_id, policy_id, effective_from, effective_to?, note?, recalc_current_year=true, close_previous=false}` → `{assignment, balances:{created, recalculated[], kept, negative_after[]}}` |
| `POST /api/leave-policy-assignments/preview` | `leave_balance.write` | `{policy_id, effective_from, effective_to?, close_previous, employee_ids? \| company_id?, department_id?, employment_type?, job_level?, only_without_active=true}` → `{items:[{employee_id, code, name, department_name, hire_date, current:{policy_name, from, to}?, conflict: null\|'overlap'\|'self'\|'inactive', changes:[{leave_type_id, before, after}]}], total, truncated}` (trần 500) |
| `POST /api/leave-policy-assignments/bulk` | `leave_balance.write` | `{policy_id, effective_from, effective_to?, employee_ids ≤500, recalc_current_year, close_previous}` → `{created, skipped[], balances:{created, recalculated, kept}}` |
| `PATCH /api/leave-policy-assignments/{id}` · `DELETE …/{id}?recalc_current_year=` | `leave_balance.write` + `get_scoped(..., "write")` | luật 6 |

Đăng ký router trong `main.py` cạnh `leave_balance_router` (không có đường tĩnh nào bị `/{id}` nuốt vì `preview`/`bulk` là
POST; vẫn khai `preview`/`bulk` TRƯỚC `/{id}` trong cùng tệp).

## Tệp
Tạo: `leave/policy_model.py` · `leave/policy_schema.py` · `leave/policy_allocation_math.py` (thuần) ·
`leave/policy_allocation.py` · `leave/policy_controller.py` (chính sách + dòng) · `leave/policy_assignment_service.py`
(`plan_change`, `apply_change`, `bulk`) · `leave/policy_assignment_controller.py` ·
`migrations/versions/lvpol717_chinh_sach_nghi_phep.py` · `test/backend/test_nghi_phep_chinh_sach_cr717.py` (thuần +
dịch vụ) · `test/backend/test_nghi_phep_phan_bo_hang_loat_cr717.py`.
Sửa: `leave/balance_service.py` (chỉ 2 dòng trong `ensure_balance` + import) · `leave/constants.py` (IntEnum trạng
thái dẫn xuất) · `core/all_models.py` · `main.py`.
KHÔNG đụng: `accrual_service.py` (trừ khi cần xuất hàm), `scoping.py`, `permissions.py`, `seed.py`, mọi tệp FE.

## Các bước
1. Model + migration viết tay (idempotent, kiểm bảng có chưa — mẫu `lvcmp716`); `alembic upgrade head` + `downgrade -1` +
   `upgrade` trên DB local.
2. Hàm thuần `policy_allocation_math` + bài kiểm bảng ví dụ (luật 1) TRƯỚC khi nối vào `ensure_balance`.
3. `policy_allocation.allocated_days` + sửa `ensure_balance`; chạy ngay bộ cũ `-k "nghi_phep or leave or cr715"` phải xanh
   nguyên (chứng minh không phân bổ = như cũ).
4. Controller chính sách + dòng. 5. Service phân bổ (`plan_change` dùng chung) + controller đơn lẻ / sửa / xóa.
6. Preview + bulk (savepoint từng người). 7. Bài kiểm đếm truy vấn cho list + preview (1 người vs 30 người cùng số câu).

## Bài kiểm (tối thiểu)
- Thuần: bảng ví dụ luật 1; **không phân bổ** == `prorate_allocation` cho 3 mode × (vào làm trước năm / giữa năm / năm sau /
  chưa có ngày) × hạn mức lẻ 12.25.
- Dịch vụ: tạo → dòng thiếu được cấp theo chính sách; dòng có sẵn giữ nguyên khi tắt tính lại; bật → chỉ `allocated_days`
  đổi, 7 cột còn lại nguyên, có dòng audit; loại không có trong chính sách → luật loại; chồng ngày 409; `close_previous`
  đóng đúng ngày và tính lại cả loại của chính sách cũ; tự phân bổ 403 (admin qua); ngoài phạm vi 404; chính sách ngừng
  422; dòng loại không trừ quỹ / loại nghỉ bù 422; xóa chính sách còn phân bổ 409; xóa phân bổ + tính lại → về luật loại;
  phân bổ bắt đầu năm sau → không đụng quỹ năm nay, `ensure_balance` năm sau ra số chính sách; năm đã qua không đổi.
- Hàng loạt: 3 người (1 chồng ngày) → 2 tạo, 1 skipped có lý do; 501 người → 422; preview không ghi (đếm dòng trước/sau).
- Phạm vi: list với nhân viên `own` chỉ thấy phân bổ của mình; người phòng khác không thấy.
- Hồi quy: `-k "nghi_phep or leave or cr715 or cr713 or quy_phep"` xanh; `test_pham_vi_khai_du_b07.py` xanh (không entity mới).

## Xong khi
- Toàn bộ bài kiểm trên xanh; migration lên/xuống/lên sạch trên MySQL local.
- `POST /api/leave-policy-assignments` với 1 người hạn mức 12 → chính sách 15 từ 01/07 năm nay, tính lại → `allocated_days`
  = 13.5 (gọi API thật qua `curl` trên local).
- Không có dòng phân bổ nào → mọi con số quỹ y hệt trước CR (bài kiểm hồi quy).

## Rủi ro
| Rủi ro | Khả năng × Tác động | Giảm |
|---|---|---|
| Hồi quy làm tròn khi không có phân bổ | TB × Cao | nhánh "mọi q bằng nhau → `prorate_allocation`" + bài kiểm 12.25 |
| Hai HR phân bổ cùng người cùng lúc → chồng ngày | Thấp × TB | khóa hàng `tab_employee` + UNIQUE(employee_id, from) |
| Tính lại làm quỹ âm | TB × TB | trả `negative_after`, FE hiện cảnh báo; số cũ trong audit |
| `apply_scope(Assignment, "leave_balance")` gãy nếu sau này `SCOPE_FIELDS["leave_balance"]` thêm cột Assignment không có | Thấp × Cao | bài kiểm phạm vi trên Assignment; docstring model ghi ràng buộc |
| Bulk 500 người chậm (ensure_balance + resolve_quota mỗi dòng) | TB × Thấp | nạp sẵn ở preview; ghi chấp nhận O(n×loại) câu, đo trên local 300 người |
| Đụng tệp CR-715 chưa commit | Cao × TB | điều kiện: CR-715 commit trước khi bắt đầu |

## Bảo mật
Phân bổ = cho thêm ngày phép → `leave_balance.write` + phạm vi `employee` + cấm tự phân bổ. Không lộ trường nhạy cảm (chỉ
mã, tên, phòng, ngày vào làm — ngày vào làm đã hiện ở màn Quỹ phép).
