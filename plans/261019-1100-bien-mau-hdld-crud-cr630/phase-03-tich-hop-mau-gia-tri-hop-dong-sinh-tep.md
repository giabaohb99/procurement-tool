# Phase 03 — Tích hợp: kiểm mẫu theo danh mục động, giá trị biến theo HĐ, sinh tệp, che nhật ký

**Ưu tiên:** P2 · **Status:** pending · **Effort:** 3.5h · **Phụ thuộc:** 01 · **Song song với:** 02, 04

## Kiến trúc

### 3.1 `docx_engine.py` — giữ THUẦN (không DB)
`inspect_template(data, allowed: frozenset[str] = KNOWN_KEYS, sample: dict | None = None, inactive: frozenset[str] = frozenset())`:
- `unknown = used - allowed`. Chia 2 câu: mã ∈ `inactive` ⇒ «Mẫu dùng biến đã ngừng dùng: …»; còn lại «Mẫu dùng biến ngoài danh mục: …». `TemplateRejected.unknown` = cả hai (FE hiện chip như cũ).
- Render thử bằng `sample or sample_context()`. Mặc định tham số = hành vi cũ ⇒ test cũ không đổi.

### 3.2 Nơi gọi kiểm mẫu
- `template_service.read_and_inspect(db, fileobj, filename, keep=())` → `allowed, inactive = variable_registry.allowed_template_keys(db, keep)`; `sample = sample_context_for(custom_rows(db))`.
  - Tải mới: `keep=()` ⇒ biến ngừng dùng bị chặn.
  - Thay tệp + soạn web (`template_web_editor.save_content`): `keep=row.placeholders` ⇒ mẫu CŨ đang chứa biến đã ngừng dùng vẫn sửa được chữ khác (không thì HR không vá nổi lỗi chính tả mẫu nếu chưa gỡ biến).
- `template_schema.MAX_PLACEHOLDERS` 200 → **300** (50 hệ thống + 100 tùy chỉnh + 100 `_bang_chu`).

### 3.3 Giá trị theo HĐ — `schema.py`, `service.py`, `serializer.py`
- `CustomValuesIn = dict[str, str | int | None]`, trần ≤ 100 khóa ở schema; mỗi khóa khớp `CODE_RE`. Thêm `custom_values: CustomValuesIn | None = None` vào `LaborContractCreate` và `LaborContractUpdate`; `LaborContractOut.custom_values: dict[str, str] = {}`.
- `service._merge_custom_values(db, old: dict, incoming: dict) -> dict` (trả dict MỚI):
  - mã không tồn tại ⇒ 422 «Biến không tồn tại: …»; mã hệ thống ⇒ 422.
  - mã ngừng dùng: chỉ nhận nếu giá trị chuẩn hóa == giá trị đang lưu (FE không gửi; chặn ghi MỚI) ⇒ khác thì 422.
  - `normalize_value(type, v)`; rỗng/None ⇒ XÓA khóa; khóa không gửi ⇒ giữ nguyên (biến ngừng dùng giữ giá trị).
  - tổng `json.dumps(result, ensure_ascii=False)` > `MAX_CUSTOM_VALUES_CHARS` ⇒ 422.
- `create()`: nhận `custom_values` (gộp vào `{}`). `update()`: gộp vào giá trị cũ; so sánh dict cũ ≠ mới vào biến `changed` ⇒ **tệp đã sinh thành bản cũ, bị bỏ** (cùng luật lương/ngày). Chỉ Nháp (luật sẵn có 409).
- Serializer: `custom_values=dict(r.custom_values or {})`.

### 3.4 Sinh tệp — `generate_service.generate`
Sau `_pick_template`, trước `render`:
1. `rows = custom_rows(db)`; `ctx = build_context(...)` (hệ thống, assert cũ giữ) `| custom_context(rows, row.custom_values or {})` — assert 2 tập khóa rời nhau.
2. `missing = set(tpl.placeholders or []) - set(ctx)` ⇒ 422 «Mẫu dùng biến đã bị xóa khỏi danh mục: … — sửa lại mẫu» (lưới đua xóa/tải; render `StrictUndefined` sẽ nổ khó hiểu nếu để lọt).
3. Bắt buộc: biến `is_active` ∧ `is_required` ∧ (mã hoặc `_bang_chu` của nó ∈ `tpl.placeholders`) ∧ `ctx[mã] == ""` ⇒ 422 «Hợp đồng còn thiếu: <nhãn 1>, <nhãn 2> — mở «Sửa hợp đồng» để nhập». Biến ngừng dùng KHÔNG ép (ô nhập đã ẩn).
4. Mặc định: dùng lúc SINH khi HĐ không có giá trị (không chép vào HĐ lúc lập) ⇒ HĐ lập trước khi có biến vẫn sinh được.
5. Chữ nhiều dòng: kiểm docxtpl 0.20.2 đổi `\n` trong giá trị thành ngắt dòng `<w:br/>` (hàm `resolve_listing`). Nếu KHÔNG ⇒ trong `format_value` bọc MULTILINE bằng `docxtpl.Listing`/`RichText` tương đương — chốt bằng test ở dưới trước khi viết.
- ⚠️ Xung đột tệp với **phase 07 CR-629b**: phase 07 sửa `_pick_template` (db.get → query) cùng tệp này. CR-630 làm TRƯỚC (migration chain), phase 07 rebase — 2 hàm khác nhau, xung đột chữ tối thiểu.

### 3.5 Che nhật ký (giá trị có thể nhạy cảm như lương)
- `core/logging_policy.py`: thêm `"custom_values"` vào `_LABOR_CONTRACT_KEYS` (thân request `/api/labor-contracts/*` + `/api/employees/{id}/labor-contracts`).
- `core/change_tracker.py`: thêm `"custom_values"` vào bộ cột che của `tab_labor_contract`.
- `document_archive_sync._title/_summary`: KHÔNG đổi (không đọc `custom_values`) — chỉ thêm test canh.
- Thông điệp lỗi 422 chỉ nêu MÃ/NHÃN biến, không nêu GIÁ TRỊ.

## Tệp
- Sửa: `backend/app/modules/labor_contract/docx_engine.py`, `template_service.py`, `template_web_editor.py`, `template_schema.py` (hằng), `schema.py`, `service.py`, `serializer.py`, `generate_service.py`, `backend/app/core/logging_policy.py`, `backend/app/core/change_tracker.py`
- Tạo: `backend/app/modules/labor_contract/contract_custom_values.py` (hàm gộp + kiểm `merge_custom_values`, < 80 dòng — `service.py` đã 188 dòng, registry thuộc phase 01 nên không đặt vào đó), `test/backend/test_hdld_bien_mau_sinh_tep_cr630.py`

## Test — `test/backend/test_hdld_bien_mau_sinh_tep_cr630.py`
- Tải mẫu: dùng biến tùy chỉnh đang dùng ⇒ 201, `placeholders` có mã; biến ngừng dùng ⇒ 422 câu «đã ngừng dùng» + `details.unknown`; mã lạ ⇒ 422 cũ; `x_bang_chu` của biến tiền ⇒ nhận; `_bang_chu` của biến CHỮ ⇒ 422.
- Thay tệp / soạn web mẫu CŨ có biến đã ngừng dùng ⇒ nhận; thêm biến ngừng dùng KHÁC ⇒ 422.
- Lập/sửa HĐ: lưu giá trị chuẩn hóa (tiền «15000000», ngày ISO, số «1.5»); gửi rỗng ⇒ xóa khóa; không gửi ⇒ giữ; mã lạ / mã hệ thống ⇒ 422; ngừng dùng giá trị mới ⇒ 422, giá trị y cũ ⇒ 200; 101 khóa ⇒ 422 (schema); tổng > 20 000 ký tự ⇒ 422; HĐ đã ký ⇒ 409; đổi giá trị ⇒ `has_generated_file` thành False (tệp cũ bị bỏ); gửi lại y nguyên ⇒ tệp giữ.
- Sinh tệp: văn bản ra «01/10/2026», «15.000.000», «Mười lăm triệu đồng chẵn», «1.234,5»; trống ⇒ dùng mặc định; trống + không mặc định + không bắt buộc ⇒ chuỗi rỗng; bắt buộc thiếu ⇒ 422 nêu NHÃN, không nêu giá trị; bắt buộc nhưng mẫu không dùng ⇒ sinh được; biến ngừng dùng có trong mẫu cũ ⇒ sinh được bằng giá trị đã lưu; xóa thẳng dòng biến trong DB (mô phỏng đua) ⇒ 422 «đã bị xóa»; chữ nhiều dòng ⇒ tệp có `<w:br/>`.
- Che: `mask_payload` với đường `/api/employees/5/labor-contracts` che `custom_values`; change_tracker không ghi giá trị `custom_values`; `_title/_summary` của bản lưu trữ không chứa giá trị biến.
```bash
docker compose exec -T api python -m pytest -q test/backend/test_hdld_bien_mau_sinh_tep_cr630.py test/backend/test_hdld_bo_may_docx.py test/backend/test_hdld_sua_loi_review.py test/backend/test_hdld_sinh_tai_tep.py test/backend/test_hdld_hop_dong_api.py
docker compose exec -T api python -m pytest -q test/backend/test_hdld_soan_mau_tren_web.py test/backend/test_hdld_mau_hop_dong_api.py test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py test/backend/test_hdld_khoa_dong_xoa_mem_cr627.py test/backend/test_canh_do_dai_o_chu_cr538.py
```
(+ test hiện có của `logging_policy`/`change_tracker` — tìm bằng `grep -l "_LABOR_CONTRACT_KEYS\|tab_labor_contract" test/backend`.)

## Tiêu chí xong
Mọi test trên xanh, test cũ không sửa nội dung (trừ hằng `MAX_PLACEHOLDERS` nếu có test chốt số). Sinh tay 1 HĐ trên local có 5 kiểu biến ra đúng định dạng.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Mẫu đang chạy bị từ chối sau khi lên (danh mục động thiếu biến hệ thống) | Thấp × Cao | Biến hệ thống hợp lệ theo CODE, không theo DB |
| Giá trị biến lọt nhật ký request / change log | TB × Cao | 2 chỗ che + test |
| docxtpl không đổi `\n` thành ngắt dòng | TB × Thấp | Test trước; dự phòng `Listing` |
| Sửa giá trị biến không làm tệp cũ hết hiệu lực ⇒ in số liệu cũ | TB × Cao | Gộp vào `changed`; test |

## Bảo mật
Giá trị biến đi sau `labor_contract.read` như lương; 422 không lộ giá trị; bản lưu trữ Văn bản không mang giá trị ở tiêu đề/tóm tắt (nội dung tệp .docx thì có — đúng bản chất HĐ, cùng luật CR-629).
