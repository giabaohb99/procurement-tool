# Phase 02 — API quản lý biến `/api/labor-contract-variables`

**Ưu tiên:** P2 · **Status:** pending · **Effort:** 3h · **Phụ thuộc:** 01 · **Song song với:** 03

## Quyền (PO chốt, không entity mới)
| Đường | Gác |
|---|---|
| `GET ""`, `GET /{id}` | `require("labor_contract_template","read")` |
| `GET /input-fields` | `labor_contract_template.read` HOẶC `labor_contract.create` HOẶC `labor_contract.write` (khuôn `/placeholders`) |
| `POST ""`, `PATCH /{id}` | `require("labor_contract_template","write")` (PO: write cho cả tạo) |
| `DELETE /{id}` | `require("labor_contract_template","delete")` |
Danh mục biến là toàn hệ thống ⇒ KHÔNG `apply_scope` lên bảng biến. Riêng danh sách mẫu đang dùng biến thì lọc phạm vi `labor_contract_template.read` của người xem; phần ngoài phạm vi chỉ báo SỐ (`hidden_template_count`) — không lộ tên mẫu pháp nhân khác. Chốt chặn xóa vẫn đếm TOÀN hệ thống (toàn vẹn dữ liệu, khuôn chức vụ CR-426).

## Endpoint (khai `/input-fields` TRƯỚC `/{id}`)
| Method · đường | Vào | Ra |
|---|---|---|
| `GET ""` | `q` (mã/nhãn, ≤100), `source`, `value_type`, `is_active`, `pagination` | `{total, items: VariableOut[]}`; sắp `source, sort_order, code`; `template_count` tính 1 lượt quét mẫu cho cả trang |
| `GET /input-fields` | — | biến TÙY CHỈNH đang dùng: `{code,label,description,value_type,default_value,is_required,sort_order}` |
| `GET /{id}` | — | `VariableOut` + `usage: {templates:[{id,name,company_name}], hidden_template_count, contract_count}` + `code_locked` |
| `POST ""` | `VariableCreate` | 201 `VariableOut`; luôn `source=CUSTOM` |
| `PATCH /{id}` | `VariableUpdate` (exclude_unset) | `VariableOut` |
| `DELETE /{id}` | — | 200; 409 nếu hệ thống / đang dùng |
`VariableOut`: `id, code, source, value_type, label, description, example, default_value, is_required, is_active, is_hidden, sort_order, template_count, group (hệ thống: nhóm từ code; tùy chỉnh: «Biến tùy chỉnh»), created_at, created_by_name`. Dòng hệ thống có mã không còn trong `KNOWN_KEYS` ⇒ không trả.

## Schema (`variable_schema.py`, `extra="forbid"`, `max_length` khớp ĐÚNG model)
- `VariableCreate`: `code` (strip, lower? — KHÔNG tự hạ chữ, sai là 422 rõ ràng) → `variable_rules.check_code`; `label` 1..200; `description` ≤500; `example` ≤255; `value_type` ∈ IntEnum; `default_value` ≤2000 rồi `normalize_value(value_type, …)`; `is_required`, `is_active`; `sort_order` 0..9999.
- `VariableUpdate`: mọi trường tùy chọn; `model_validator` chuẩn hóa `default_value` theo `value_type` GỘP (ở service vì cần giá trị cũ).

## Luật nghiệp vụ (`variable_service.py`)
1. **Tạo**: đếm biến tùy chỉnh ≥ `MAX_CUSTOM_VARIABLES` ⇒ 422; trùng mã ⇒ 400 «Mã biến đã tồn tại»; đua tạo trùng ⇒ bắt `IntegrityError` ⇒ 409 (unique là chốt thật).
2. **Sửa biến HỆ THỐNG**: chỉ nhận `label`, `description`, `is_hidden`; gửi trường khác ⇒ 422 «Biến hệ thống chỉ sửa được tên hiển thị, mô tả và ẩn/hiện» (nêu tên trường).
3. **Sửa biến TÙY CHỈNH**: `is_hidden` ⇒ 422 (dùng «Ngừng dùng»). Đổi `code` hoặc `value_type` khi `code_locked` ⇒ 409 nêu lý do (số mẫu + số HĐ). `code_locked` = `template_usage` ≠ ∅ HOẶC `contract_value_count` > 0. Đổi mã khi chưa dùng ⇒ `check_code` lại + unique. Đổi `value_type` ⇒ chuẩn hóa lại `default_value` theo kiểu mới (sai ⇒ 422).
4. **Xóa**: hệ thống ⇒ 409 «Biến hệ thống không xóa được — dùng «Ẩn»». Khóa dòng `FOR UPDATE` rồi kiểm `code_locked` ⇒ 409, `details={templates:[…trong phạm vi], hidden_template_count, contract_count}`, câu: «Biến đang dùng trong N mẫu / M hợp đồng — không xóa được, hãy chọn «Ngừng dùng»». Không dùng ⇒ xóa cứng.
5. **Ngừng dùng / bật lại**: PATCH `is_active`. Ngừng không chạm mẫu/HĐ.
6. Audit: `audit_record(db, user.id, "labor_contract_variable", id, action, «Thêm/Sửa/Xóa biến mẫu HĐLĐ «code»»)` — kiểm `core/audit.record` không đòi entity ∈ `ENTITIES` (nếu đòi thì dùng `labor_contract_template` + `parent`).
7. Mọi lệnh ghi xong: không có cache phía server cần xóa (registry đọc DB mỗi lần).

## `/api/labor-contract-templates/placeholders` (sửa `template_controller.py`)
Đổi nguồn sang `variable_service.guide_list(db)`: biến hệ thống KHÔNG ẩn (nhãn/mô tả từ DB nếu có, nhóm + ví dụ từ code) + biến tùy chỉnh đang dùng (nhóm «Biến tùy chỉnh») + dòng `_bang_chu` cho biến tiền (nhãn «<nhãn> (bằng chữ)»). Hình dạng giữ `{key,label,group,example}` + thêm `description` ⇒ khung chèn biến CR-606 không đổi code.

## Tệp
- Tạo: `backend/app/modules/labor_contract/variable_schema.py`, `variable_service.py`, `variable_serializer.py`, `variable_controller.py`, `test/backend/test_hdld_bien_mau_api_cr630.py`
- Sửa: `backend/app/main.py` (include router, cạnh 2 router HĐLĐ), `backend/app/modules/labor_contract/template_controller.py` (chỉ hàm `list_placeholders`)
- File < 200 dòng mỗi tệp; controller mỏng.

## Test — `test/backend/test_hdld_bien_mau_api_cr630.py` (fixture `client_as`, `hdld_factory`)
- Quyền: không `template.read` ⇒ 403 list; có `labor_contract.create` mà không `template.read` ⇒ `/input-fields` 200, list 403; `read` mà POST ⇒ 403; `write` mà DELETE ⇒ 403.
- Tạo: hợp lệ 201; mã trùng hệ thống `ho_ten` ⇒ 422; trùng tùy chỉnh ⇒ 400; quá 100 biến ⇒ 422; nhãn 201 ký tự / mô tả 501 / ví dụ 256 / mặc định 2001 ⇒ 422 ở **tầng schema** (`pytest.raises(ValidationError)` — SQLite không ép VARCHAR); mặc định sai kiểu (tiền «abc», ngày «32/13») ⇒ 422; `extra` lạ ⇒ 422.
- Biến hệ thống: PATCH nhãn/mô tả/ẩn 200; PATCH `code`/`value_type`/`is_active`/`default_value` ⇒ 422; DELETE ⇒ 409.
- Tùy chỉnh đang dùng trong mẫu (đặt `placeholders`) ⇒ đổi mã 409, đổi kiểu 409, DELETE 409 kèm `details.templates` CHỈ mẫu trong phạm vi + `hidden_template_count` đúng (người phạm vi pháp nhân A, mẫu ở A và B).
- Biến tiền dùng qua `_bang_chu` duy nhất ⇒ vẫn tính đang dùng.
- Có HĐ (kể cả xóa mềm) giữ giá trị ⇒ DELETE 409; không ai dùng ⇒ DELETE 200, đổi mã 200.
- Ngừng dùng ⇒ biến biến mất khỏi `/input-fields` và `/placeholders`, vẫn ở list.
- `/placeholders`: biến hệ thống bị ẩn không có; nhãn đã sửa hiện nhãn mới; biến tiền có dòng `_bang_chu`.
```bash
docker compose exec -T api python -m pytest -q test/backend/test_hdld_bien_mau_api_cr630.py test/backend/test_hdld_mau_hop_dong_api.py test/backend/test_hdld_soan_mau_tren_web.py
```

## Tiêu chí xong
Bảng endpoint trên chạy đúng mã HTTP; mọi ca test xanh; `test_hdld_mau_hop_dong_api.py` không đổi nội dung vẫn xanh.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| HR phạm vi 1 pháp nhân sửa nhãn/mặc định ảnh hưởng mọi pháp nhân | TB × TB | Câu hỏi mở Q2; audit ghi người sửa |
| Đua: tải mẫu dùng biến X đúng lúc X bị xóa | Rất thấp × TB | Lưới ở sinh tệp: mẫu dùng biến không tồn tại ⇒ 422 rõ ràng (phase 03) |
| Lộ tên mẫu pháp nhân ngoài phạm vi qua thông báo chặn xóa | TB × Thấp | Chỉ trả tên trong phạm vi + số đếm |

## Bảo mật
Không thêm quyền; mọi đường `require()`; `example`/`default_value` là dữ liệu danh mục, không che nhật ký.
