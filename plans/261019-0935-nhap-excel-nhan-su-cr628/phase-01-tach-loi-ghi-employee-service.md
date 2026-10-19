# Pha 01 — Tách lõi ghi của employee service (không commit)

**Ưu tiên:** P1 · **Trạng thái:** completed · **Công:** 0.5d · **Chặn bởi:** —

## Vì sao
`create_employee` / `update_employee` / `delete_employee` tự `db.commit()` và gọi `record()` — mà
`record()` **luôn commit** (cố ý, BM-013, `core/audit.py`). Gọi thẳng trong batch import là phá
dry-run (rollback cuối lô) và phá savepoint từng dòng. Adapter cũ né bằng `setattr` trần → mất hết chốt
nghiệp vụ. Giải: tách phần **kiểm + gán + flush** thành hàm lõi; hàm công khai = lõi + commit + audit +
xóa cache. Màn hồ sơ giữ nguyên hành vi.

## Thiết kế
`backend/app/modules/employee/service.py` (sửa tại chỗ, không đổi chữ ký hàm công khai):

```python
@dataclass
class WriteOutcome:          # kết quả lõi — bên gọi tự quyết commit/audit
    obj: Employee
    notes: list[str]          # «Đổi pháp nhân — gỡ…», «Nghỉ việc — khóa N TK…»
    left_company: bool        # has_left_company(...) đúng ở lần ghi này
    scope_changed: bool       # (company_id, department_id) đổi → cần clear_perm_cache_of

def create_employee_core(db, data: EmployeeCreate, user_id) -> Employee          # flush, KHÔNG commit/record
def update_employee_core(db, obj, data: EmployeeUpdate, user_id, *, lock_users: bool = True) -> WriteOutcome
def delete_employee_core(db, eid, user_id) -> int                                # cho hoàn tác lô (pha 03)
```
- `update_employee_core`: thân hiện tại của `update_employee` từ chụp `old_*` tới hết khối
  `_sync_user_email_from_employee` + `lock_linked_users`, **bỏ** `try/except rollback` (bên gọi lo) và
  bỏ `commit/refresh/record/clear_perm_cache_of`. `lock_users=False` → không gọi `lock_linked_users`
  (dry-run không được đá phiên / gọi dịch vụ AI thật), nhưng vẫn trả `left_company=True`.
- `create_employee` / `update_employee` / `delete_employee` công khai = gọi lõi → commit → refresh →
  `record` → (update) `record` từng TK bị khóa → `clear_perm_cache_of` nếu `scope_changed`. Thứ tự
  «xóa cache SAU commit» giữ nguyên.
- Dời `_status_code` từ `employee/controller.py` sang tệp mới `employee/status_parse.py` (tên hàm
  `status_code_from_text`), controller không còn dùng (pha 04 gỡ thân CSV). Cập nhật import ở
  `test/backend/test_nhan_su_ncc_b03.py`.

## Tệp
- Sửa: `backend/app/modules/employee/service.py`, `backend/app/modules/employee/controller.py` (gỡ `_status_code`)
- Tạo: `backend/app/modules/employee/status_parse.py`
- Sửa test: `test/backend/test_nhan_su_ncc_b03.py` (đường import)
- ⚠️ `service.py` đã 518 dòng — KHÔNG tách tệp ở CR này (nhiều nơi import `service.has_left_company`,
  `service.lock_linked_users`…); ghi nợ kỹ thuật.

## Các bước
1. Thêm `WriteOutcome` + 3 hàm lõi; viết lại 3 hàm công khai thành vỏ gọi lõi.
2. Dời `_status_code` → `status_parse.status_code_from_text`.
3. Chạy test hồi quy đích (dưới).

## Todo
- [x] `create_employee_core` / `update_employee_core` / `delete_employee_core`
- [x] Vỏ công khai giữ y hành vi (commit, audit, khóa TK, xóa cache sau commit)
- [x] `status_parse.py` + sửa import test b03
- [x] Test hồi quy xanh

## Test (chỉ chạy đúng các tệp này)
```bash
docker compose exec -T api python -m pytest -q test/backend/test_nghi_viec_da_phien_cr400.py \
  test/backend/test_employee_email_trung_cr368.py test/backend/test_employee_position.py \
  test/backend/test_kiem_nhiem_phong_ban.py test/backend/test_employee_delete_account.py \
  test/backend/test_nhan_su_ncc_b03.py test/backend/test_qua_trinh_cong_tac_thoi_viec.py
```
Thêm (ở tệp test mới của pha 06): lõi `update_employee_core` KHÔNG commit (rollback xong DB y cũ);
`lock_users=False` không đổi `User.is_active` nhưng `left_company=True`.

## Thành công khi
Test hồi quy trên xanh không sửa assert; grep `db.commit` trong 3 hàm lõi = 0.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Đổi nhịp commit làm lệch hành vi màn hồ sơ | TB×Cao | Vỏ công khai giữ đúng thứ tự cũ; chạy 7 tệp hồi quy |
| `work_history_apply_service` gọi `update_employee` | Thấp×TB | Không đổi chữ ký; chạy `test_qua_trinh_cong_tac_thoi_viec.py` |

## Rollback
Revert commit; không dữ liệu nào đổi.
