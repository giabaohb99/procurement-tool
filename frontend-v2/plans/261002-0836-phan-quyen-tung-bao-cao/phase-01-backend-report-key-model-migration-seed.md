# Phase 01 — Backend nền: khóa báo cáo, bảng, migration, seed mặc định, sinh TS

**Ưu tiên:** P1 · **Effort:** 3h · **Trạng thái:** done · **Phụ thuộc:** —

## Context
- `backend/app/core/status_catalog.py`, `core/code_sets.py`, `core/forum_codes.py` (mẫu số-viết-dạng-chuỗi), `scripts/gen_status_ts.py`
- `backend/app/core/subject_match.py`, `modules/doc_catalog/folder_access_model.py` (khuôn bảng)
- `backend/app/seed.py::run/ensure_admin_role`, `app/seed_prod.py::run`
- Memory: migration autogenerate quét ra ~650 dòng trôi → viết tay / gọt.

## Quyết định: khóa SỐ, không phải chuỗi
- R2/QĐ-11: cột MỚI mang nghĩa loại/kiểu → `SMALLINT` + `IntEnum`. Ngoại lệ mã chuỗi (QĐ-9) chỉ cho Thu mua, «không phải giấy phép cho cột mới».
- Cái mất của mã số (khó đọc trong DB) bù bằng bộ mã đăng ký `report_key` (nhãn tiếng Việt) → `/meta/statuses` + `statuses.ts`.
- Luật bất biến (ghi ngay đầu tệp): **số đã cấp không đổi, không tái dùng**, báo cáo bỏ đi thì để trống số (giống luật `product_code`).

## Thiết kế
`app/core/report_keys.py` (thuần stdlib — `code_sets.py` phải chạy không cần SQLAlchemy):
```python
class ReportKey(IntEnum):
    PURCHASE_REPORT = 1; PR_LINES = 2; SURVEY_PROGRESS = 3; PURCHASE_PROGRESS = 4
    SURVEY_REPORT = 5; HR_HEADCOUNT = 6; LEAVE_USAGE = 7; LEAVE_BALANCE = 8
    VEHICLE_BOOKING = 9; SEAL_REQUEST = 10; DOCUMENT = 11; APPROVAL = 12; WORK = 13
REPORT_META: dict[ReportKey, tuple[str, str]]  # key -> (nhãn, nhóm phân hệ) — nhãn KHỚP label FE catalog
REPORT_KEY_SET = register(CodeSet("report_key", "Báo cáo", [Code(str(int(k)), label, sort_order=int(k)) ...]))
```
- Thêm `from app.core import report_keys` vào `code_sets.py`.

`app/modules/report_access/model.py` — `ReportAccess(Base, AuditMixin)`, `__tablename__ = "tab_report_access"`:
| Cột | Kiểu | Ghi chú |
|---|---|---|
| report_key | SmallInteger, not null | `ReportKey` |
| subject_kind | SmallInteger | 1 người(id NHÂN SỰ) · 2 phòng · 3 pháp nhân · 4 vai trò — số của `subject_match` |
| subject_id | BigInteger | |
| effect | SmallInteger | 1 cho phép · 2 cấm |
| valid_from / valid_to | Date null | giữ để dùng lại `still_live_condition`; UI chưa mở (câu hỏi treo) |
| reason | String(500) | |
| revoked_at / revoked_by / revoke_reason | DateTime null / BigInteger / String(500) | thu hồi = đánh dấu |
- Index: `ix_report_access_subject(subject_kind, subject_id)`, `ix_report_access_key(report_key, effect)`. Không UNIQUE (cùng lý do folder: `revoked_at IS NULL` không chặn trùng được) → chống trùng ở service.
- Thêm model vào `app/core/all_models.py`.

Migration `backend/migrations/versions/rptacc01_phan_quyen_tung_bao_cao.py` — **viết tay**, không autogenerate:
- `down_revision` = head hiện tại (`alembic heads` — nếu >1 head thì DỪNG, hỏi; không tự gộp).
- `upgrade`: `op.create_table(...)` + 2 index; rồi `SELECT id FROM tab_role WHERE code='admin'` — có thì `op.bulk_insert` 13 dòng (kind=4, effect=1, reason="Mặc định khi ra tính năng phân quyền báo cáo", created_by=0); không có (DB mới, seed chưa chạy) thì bỏ qua — seed lo.
- Danh sách 1..13 **đóng băng trong migration** (không import `ReportKey` — migration phải bất biến theo thời gian).
- `downgrade`: drop index + drop table.

`app/modules/report_access/seed_defaults.py::ensure_report_access_defaults(db) -> int`:
- Lấy role `admin`; không có → 0.
- `keys_with_any_row = {report_key có ÍT NHẤT MỘT dòng, kể cả đã thu hồi}`; với mỗi `ReportKey` ngoài tập đó → chèn dòng CHO PHÉP cho vai trò admin. Trả số dòng chèn.
- Gọi trong `seed.run()` và `seed_prod.run()` ngay sau `ensure_admin_role`. Không phụ thuộc `SEED_FORCE_SYNC`.
- Hệ quả cố ý: đại ca thu hồi dòng admin của khóa X → seed KHÔNG chèn lại (đã có dòng). Báo cáo mới (khóa 14…) → admin tự có.

Sinh TS: `REPORT_KEY` vào `frontend-v2/src/shared/constants/statuses.ts`. Container `api` không thấy `frontend-v2/` → chạy:
`docker compose run --rm --no-deps -v "$PWD":/repo -w /repo/backend api python -m scripts.gen_status_ts` (từ gốc repo), rồi `--check` để chắc.

## Sở hữu tệp
Tạo: `core/report_keys.py`, `modules/report_access/{__init__,model,seed_defaults}.py`, migration `rptacc01_*`. Sửa: `core/code_sets.py`, `core/all_models.py`, `seed.py`, `seed_prod.py`, `frontend-v2/src/shared/constants/statuses.ts` (SINH, không gõ tay).

## Các bước
1. Viết `core/report_keys.py` + nạp ở `code_sets.py`.
2. Model + `all_models.py`.
3. Migration viết tay; `docker compose exec api alembic upgrade head` → `downgrade -1` → `upgrade head` trên local.
4. `seed_defaults.py` + gọi ở 2 seed; restart api, kiểm 13 dòng admin trong Adminer.
5. Sinh `statuses.ts`, `--check` xanh.

## Todo
- [x] report_keys.py + đăng ký bộ mã
- [x] model + all_models
- [x] migration viết tay, lên/xuống/lên OK
- [x] seed_defaults + gọi ở seed/seed_prod
- [x] statuses.ts sinh lại

## Tiêu chí xong
- `alembic heads` = 1 head; bảng có đúng cột/index; DB local có 13 dòng admin; chạy seed lần 2 không thêm dòng.
- `gen_status_ts --check` OK; `/meta/statuses` có `report_key` 13 mã.

## Rủi ro
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Nhiều head alembic trên `erp-v2` | TB × Cao | Kiểm trước, dừng hỏi; không tự merge |
| Lệch nhãn BE/FE | TB × Thấp | Test khớp nhãn ở phase 05 |
| Ai đó tái dùng số khóa | Thấp × Cao (dòng gán cũ áp nhầm báo cáo) | Chú thích bất biến + test «khóa liên tục, không trùng» |

## Bảo mật
Không dữ liệu nhạy cảm; Vietnamese text chỉ qua migration/SQLAlchemy (không `mysql -e`).
