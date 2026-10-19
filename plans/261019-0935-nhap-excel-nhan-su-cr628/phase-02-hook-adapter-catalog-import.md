# Pha 02 — Khung `catalog_import`: thêm hook adapter

**Ưu tiên:** P1 · **Trạng thái:** completed · **Công:** 0.5d · **Chặn bởi:** —

## Vì sao
Vòng lặp `catalog_import.run` (dòng 451-582) dựng `data` rồi `setattr` trần, ô trống ghi đè (`""` /
`default`), xóa được bản ghi, hoàn tác chỉ khôi phục cột có trong file. Không sửa hành vi 10 danh mục
khác — chỉ mở **điểm cắm** để adapter nào cần thì tự xử lý dòng.

## Thiết kế (khóa tùy chọn trong `ADAPTERS[module]`)
| Khóa | Chữ ký | Dùng ở |
|---|---|---|
| `allow_delete` | `bool` (mặc định `True`) | `False` → dòng `__/delete/__` = ERROR `delete_not_allowed`, không xóa |
| `prepare` | `(db, batch, field_col, apply) -> ctx` | Đầu `run`, sau `ensure_file_matches`; được raise `ImportValidationError` (vd người tạo lô không còn hoạt động) |
| `apply_row` | `(db, ctx, row_no, code, raw: dict[attr, value], log) -> RowResult` | Thay khối «kiểm bắt buộc → dựng data → setattr» cho adapter đó |
| `finalize` | `(db, ctx) -> None` | Sau `db.commit()` của apply (audit, xóa cache quyền); dry-run không gọi |
| `revert` | `(db, changes, user_id) -> (deleted, restored)` | Thay `catalog_import.revert` chung |
| `revert_blockers` | `(db, changes) -> list[str]` | `service.revert_batch` gọi TRƯỚC khi đụng gì, có lỗi → từ chối cả lượt (khuôn ai-CR-169) |
| `template_notes` | `list[tuple[str, str]]` | `build_template` thêm sheet «Huong dan» (cột → giá trị nhận) |
| `template_action_col` | `bool` (mặc định `True`) | `False` → mẫu không có cột «Hành động» |

`RowResult` = `{"outcome": "created"|"updated"|"unchanged"|"error", "target_id", "snapshot", "was_new"}`.
Khung lo: đếm `counts`, ghi `changes` (chỉ khi apply), log `created/updated` theo `outcome`.
`raw` = giá trị ô thô của **những cột có trong file** (cột vắng → không có khóa).

## Thay đổi cụ thể
- `catalog_import.run`: sau nhánh dò dòng trắng + `action`:
  - nếu `action == DELETE_SENTINEL and not adapter.get("allow_delete", True)` → log ERROR
    «Không xóa {label} qua nhập Excel — chuyển Trạng thái/Đang dùng để ngưng» → `skipped += 1` → `continue`.
  - nếu có `apply_row` → **bỏ** nhánh mã tự sinh `_gen_code` + kiểm bắt buộc chung, gọi hook, `continue`.
- Cuối `run`: `if apply: db.commit(); finalize(...)` (bọc `try`, lỗi finalize chỉ log WARNING lô, không làm FAILED).
- `catalog_import.revert`: nếu adapter có `revert` → ủy quyền.
- `import_tool/service.revert_batch`: nhánh `catalog_import.is_catalog_module` → gọi `revert_blockers`
  nếu có (cùng khuôn chặn `problems` của doc_import).
- `build_template`: tôn trọng `template_action_col`, thêm sheet «Huong dan» khi có `template_notes`
  (cột A tiêu đề, cột B giá trị nhận / ghi chú). Sheet nhập vẫn là `adapter["sheet"]`.
- Trần số dòng chung cho adapter có `max_rows` (Nhân sự: 2000) → vượt = `ImportValidationError`
  (luật trần danh sách, `backend-input-limits.md`).

## Tệp
- Sửa: `backend/app/modules/import_tool/catalog_import.py` (661 dòng → +~50; KHÔNG tách tệp ở CR này)
- Sửa: `backend/app/modules/import_tool/service.py` (`revert_batch`)

## Todo
- [x] `allow_delete`, `prepare`, `apply_row`, `finalize`, `revert`, `revert_blockers`
- [x] `build_template`: `template_action_col`, sheet «Huong dan»
- [x] `max_rows`
- [x] Hồi quy 10 danh mục cũ không đổi

## Test (chỉ chạy)
```bash
docker compose exec -T api python -m pytest -q test/backend/test_import_catalog.py test/backend/test_import_datxe_duyetdau.py
```
(Hai test EMPLOYEE cũ trong `test_import_catalog.py` sẽ sửa ở pha 03 khi adapter đổi.)

## Thành công khi
Adapter không khai hook → hành vi y cũ (test cũ xanh nguyên assert, trừ 2 test EMPLOYEE).

## Rủi ro
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Hook làm lệch đếm/log danh mục khác | Thấp×TB | Nhánh hook tách hẳn bằng `if adapter.get("apply_row")` |
| `finalize` lỗi sau khi đã commit | Thấp×TB | Bọc try; chỉ WARNING; dữ liệu đã đúng, chỉ thiếu audit/cache (cache tự hết 60s) |
