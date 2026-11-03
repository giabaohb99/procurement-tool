# Phase 02 — Backend: gác 26 đường, `report_keys` trong `/auth/me`, API cấu hình

**Ưu tiên:** P1 · **Effort:** 3h · **Trạng thái:** done · **Phụ thuộc:** 01

## Context
- `core/auth.py` (`require`, `get_perm_profile`), `core/subject_match.py`, `core/audit.record`
- `modules/doc_catalog/folder_access_{grant,bulk,view}_service.py`, `folder_access_schema.py` (khuôn)
- `modules/auth/controller.py::_me_payload` (đã 462 dòng — chỉ thêm 2 dòng, không tách trong phạm vi này)

## Luồng dữ liệu
```
Request /…/summary ─► require_report(K) ─► get_perm_profile (cache 60s) ─► subject_pairs
                      └► 1 SELECT tab_report_access (khớp chủ thể ∧ còn hiệu lực ∧ key=K)
                         allow={effect=1} deny={effect=2}; cho qua ⇔ allow ∧ ¬deny, ngược lại 403
                   ─► require(entity, action) có sẵn ─► apply_scope có sẵn ─► số liệu
/auth/me ─► viewable_keys(db,user) ─► "report_keys": [1,3,…] ─► FE useNavContext
```

## Thiết kế
`report_access/service.py`:
- `viewable_keys(db, user, profile=None) -> set[int]`: 1 truy vấn `report_key, effect` theo `subject_match_condition` + `still_live_condition`; trả `allow - deny`. Không chủ thể nào để khớp → `set()`.
- `can_view_report(db, user, key) -> bool` = `int(key) in viewable_keys(...)` (gọn; 13 khóa thì lọc thêm `report_key == key` cũng được — chọn 1 cách, số truy vấn cố định = 1).

`report_access/guard.py`:
```python
def require_report(key: ReportKey):
    def dep(user=Depends(get_current_user), db: Session = Depends(get_db)):
        if not can_view_report(db, user, key):
            raise HTTPException(403, f"Chưa được giao xem báo cáo: {REPORT_META[key][0]}")
    dep.report_key = key        # để test soi route
    return dep
```
- Gắn bằng `dependencies=[Depends(require_report(ReportKey.X))]` trên decorator của CẢ `/summary` lẫn `/summary/export` — **không sửa tham số `user=Depends(require(...))`** (giữ nguyên gác phân hệ + phạm vi). Test gọi thẳng hàm controller (không qua HTTP) vì thế không bị ảnh hưởng.
- Không cache riêng: 1 truy vấn có chỉ mục/lượt, số truy vấn CỐ ĐỊNH (đúng luật «API báo cáo nhanh nhất»).

Bảng 26 đường (khóa ↔ tệp):
| Khóa | Tệp:dòng (hiện tại) | Entity giữ nguyên |
|---|---|---|
| PURCHASE_REPORT | `report/summary_controller.py` /procurement/summary(+export) | report |
| PR_LINES | `report/controller.py:217,239` | report |
| SURVEY_PROGRESS | `survey_progress/controller.py:430,457` | survey_request |
| PURCHASE_PROGRESS | `purchase_progress/controller.py:388,417` | purchase_request |
| SURVEY_REPORT | `survey/controller.py:442,466` (`report_router`) | survey |
| HR_HEADCOUNT | `employee/report_controller.py` | employee |
| LEAVE_USAGE | `leave/report_controller.py` | leave_request |
| LEAVE_BALANCE | `leave/balance_report_controller.py` | leave_balance |
| VEHICLE_BOOKING | `vehicle_booking/report_controller.py` | vehicle_booking |
| SEAL_REQUEST | `seal_request/report_controller.py` | seal_request |
| DOCUMENT | `document/report_controller.py` | document |
| APPROVAL | `approval/report_controller.py` | approval_flow |
| WORK | `work/report_controller.py` | work_task |
KHÔNG gác (không thuộc phân hệ Báo cáo): `/api/payables/summary`, `/api/system-logs/summary`, `/imports/{bid}/rows/summary`, `/leave-balances/tools/summary`.

Ghi chú hành vi cũ: `/survey-progress/summary?year=`, `/survey-report/summary` không `preset` là nhánh cũ — đã grep, không còn nơi gọi ở v1/v2 ngoài `modules/report`; bị gác chung, KHÔNG xóa trong phạm vi này.

`/auth/me`: thêm `"report_keys": sorted(viewable_keys(db, user))` vào `_me_payload` (login/refresh/me dùng chung hàm → đồng bộ).

**Vì sao `/auth/me` thay vì `GET /api/report-access/me`:** menu/route gác ĐỒNG BỘ trong `useNavContext` (tiền lệ `is_driver`); một query riêng thì `canAccessRoute` chạy trước khi dữ liệu về → hoặc 403 nhầm, hoặc mở nhầm, phải thêm trạng thái chờ ở 3 chỗ (layout, sidebar, launcher). Một nguồn duy nhất, không thêm vòng gọi.

API cấu hình `report_access/controller.py` (`/api/report-access`, đăng ký ở `main.py`):
| Route | Gác | Ghi chú |
|---|---|---|
| `GET /api/report-access` | `require("role","read")` | 13 mục theo thứ tự khóa: `{key,label,group,grants:[{id,subject_kind,subject_id,subject_name,effect,reason,valid_from,valid_to,created_at}]}` — chỉ dòng CÒN SỐNG; số truy vấn cố định (1 dòng + ≤4 tra tên) |
| `POST /api/report-access/{key}/grants` | `require("role","write")` | body `{subjects[1..200], effect, reason≤500}`; trùng (key,kind,id,effect) còn sống → cập nhật; chủ thể không tồn tại → skip; trả `{created,updated,skipped}`; `key` ngoài `ReportKey` → 404 |
| `DELETE /api/report-access/grants/{id}` | `require("role","write")` | body `{reason≤500}`; đã thu hồi → 400; đánh dấu `revoked_*` |
- `schema.py`: `ReportAccessGrantIn`, `ReportAccessRevokeIn`; `max_length=500` khớp `String(500)`; kiểm `subject_kind ∈ SUBJECT_LABELS`, `effect ∈ {1,2}`, `subject_id > 0`.
- Audit: `record(db, actor, "report_access", int(key), "update", "Cho phép|Cấm xem «<nhãn>» cho N đối tượng" / "Thu hồi …")`.
- DRY tên chủ thể: nâng `_subject_names` từ `doc_catalog/folder_access_view_service.py` thành `subject_names(db, rows)` ở `core/subject_match.py`; tệp thư mục gọi lại hàm chung (hành vi giữ nguyên).
- Không chặn tự gán cho chính mình/vai trò mình: gán không mở rộng dữ liệu (vẫn qua `require` + `apply_scope`) — ghi lý do trong docstring.
- Không entity mới → không đụng `ENTITIES`/`SCOPE_FIELDS`. Controller mới phải thêm vào `BB4_CONTROLLER_MIEN_TRU` của `test_pham_vi_luat_bat_bien.py` (phase 03) kèm lý do: «cấu hình quyền, gác role.read/write, không phải dữ liệu nghiệp vụ».

## Sở hữu tệp
Tạo: `report_access/{service,guard,schema,grant_service,controller}.py` (mỗi tệp <200 dòng). Sửa: 13 controller ở bảng trên (chỉ decorator), `auth/controller.py`, `main.py`, `core/subject_match.py`, `doc_catalog/folder_access_view_service.py`.

## Các bước
1. service + guard. 2. Gắn 26 decorator (import `ReportKey` + `require_report`). 3. `_me_payload`. 4. schema + grant_service + controller + `main.py`. 5. Nâng `subject_names`. 6. `restart api`, thử bằng `/docs`.

## Todo
- [x] service/guard
- [x] 26 decorator
- [x] report_keys trong /auth/me
- [x] API cấu hình + audit
- [x] subject_names nâng lên core

## Tiêu chí xong
Tài khoản đủ quyền entity nhưng chưa gán: 26 đường → 403; admin → 200. `/auth/me` có `report_keys`. CRUD chạy, audit có dòng.

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Sót 1 trong 26 đường | TB×Cao | Test soi `app.routes` (phase 03) |
| Thứ tự router `/summary` vs `/{id}` | Thấp×TB | Chỉ thêm `dependencies`, không đổi path/thứ tự |
| CẤM khóa luôn admin | Thấp×Thấp | Màn cấu hình gác `role`, không gác báo cáo → admin tự thu hồi được |

## Bảo mật
403 không lộ dữ liệu; thông báo chỉ nêu tên báo cáo. Gác kép đảm bảo gán nhầm không mở rộng phạm vi.
