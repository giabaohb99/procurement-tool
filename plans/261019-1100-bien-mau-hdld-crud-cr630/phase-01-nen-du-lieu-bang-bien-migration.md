# Phase 01 — Nền: mã số, bảng biến, migration `lbvar01`, seed, luật thuần, registry

**Ưu tiên:** P2 · **Status:** pending · **Effort:** 3h · **Phụ thuộc:** CR-629 (`lbrct02`) đã commit; `alembic heads` = đúng 1 head `lbrct02` (kiểm ngay trước khi viết migration).

## Bối cảnh
- Nguồn hiện tại: `backend/app/modules/labor_contract/placeholder_catalog.py` (50 biến, `KNOWN_KEYS`, `sample_context`), tiêu thụ ở `docx_engine.py`, `context_builder.py` (assert `set(ctx) == KNOWN_KEYS`), `template_controller.py` (`/placeholders`), test `test_hdld_bo_may_docx.py`, `test_hdld_sua_loi_review.py`.
- Mẫu đã lưu sẵn tập biến đã dùng: `tab_labor_contract_template.placeholders` (JSON list[str], trần `MAX_PLACEHOLDERS=200`).
- Luật: R2 (SMALLINT + IntEnum, đăng ký CodeSet, `gen_status_ts.py`), backend-input-limits (max_length khớp `String(n)`, JSON có trần kích thước), D-018 (seed không ghi đè sửa trên UI), migration viết tay (autogenerate trôi ~650 dòng).

## Quyết định: giá trị theo HĐ = cột JSON `custom_values`, KHÔNG bảng con
| Tiêu chí | JSON trên `tab_labor_contract` | Bảng con `(contract_id, code, value)` |
|---|---|---|
| Đọc khi sinh tệp / serializer danh sách | 0 truy vấn thêm | +1 truy vấn/trang (hoặc N+1) |
| Ghi | gán dict mới cùng giao dịch PATCH sẵn có | đường ghi riêng, xóa/chèn dòng |
| Xóa mềm HĐ (ai-CR-177) | tự giữ | phải nhớ không dọn |
| «Có HĐ nào giữ giá trị mã X» | `json_extract(...) IS NOT NULL` — thao tác hiếm (xóa/đổi mã biến) | index thường |
| Tiền lệ repo | `tab_employee.extra_fields`, `template.placeholders` | — |
Không có nhu cầu báo cáo/lọc theo giá trị ⇒ YAGNI chọn JSON. Trần: ≤ 100 khóa, mỗi giá trị theo kiểu (≤ 2000 ký tự), **tổng chuỗi JSON ≤ 20 000 ký tự** (luật JSON cần trần KÍCH THƯỚC).

## Kiến trúc
**Mã số** — thêm vào `app/core/labor_contract_codes.py` (thuần stdlib, đã nạp trong `code_sets.py`):
- `LaborContractVariableSource(IntEnum)`: `SYSTEM=1`, `CUSTOM=2`.
- `LaborContractVariableType(IntEnum)`: `TEXT=1` (chữ), `MULTILINE=2` (chữ nhiều dòng), `NUMBER=3` (số), `DATE=4` (ngày), `MONEY=5` (tiền). Biến hệ thống lưu `1`, FE hiện «—».
- Nhãn + `register(CodeSet("labor_contract_variable_source"/"labor_contract_variable_type", ...))` cùng khuôn chuỗi-số hiện có → chạy `python -m scripts.gen_status_ts`.

**Bảng `tab_labor_contract_variable`** (`variable_model.py`, `Base` + `AuditMixin`):
| Cột | Kiểu | Ghi chú |
|---|---|---|
| `code` | `String(40)` NOT NULL, unique `uq_labor_contract_variable_code` | snake_case; 40 để `code + "_bang_chu"` ≤ 49 |
| `source` | `SmallInteger` NOT NULL | IntEnum trên |
| `value_type` | `SmallInteger` NOT NULL default 1 | |
| `label` | `String(200)` NOT NULL | |
| `description` | `String(500)` default '' | |
| `example` | `String(255)` default '' | |
| `default_value` | `String(2000)` default '' | lưu dạng CHUẨN của kiểu (xem luật dưới); chỉ biến tùy chỉnh |
| `is_required` | `Boolean` default False | «bắt buộc khi sinh tệp», chỉ tùy chỉnh |
| `is_active` | `Boolean` default True | chỉ tùy chỉnh (hệ thống luôn True) |
| `is_hidden` | `Boolean` default False | chỉ hệ thống: ẩn khỏi danh sách hướng dẫn/khung chèn, VẪN hợp lệ |
| `sort_order` | `SmallInteger` default 0 | schema chặn 0..9999 |
Index `ix_labor_contract_variable_pick (source, is_active, sort_order)`.

**Cột mới** `tab_labor_contract.custom_values JSON NULL` (`model.py`; `None` ≡ `{}`). Docstring: CHỈ gán dict MỚI (không sửa tại chỗ — không có `MutableDict`, sửa tại chỗ SQLAlchemy không thấy thay đổi).

**Luật thuần** `variable_rules.py` (không DB, test rẻ):
- `CODE_RE = ^[a-z][a-z0-9_]{1,39}$`, cấm `__`, cấm đuôi `_`, cấm đuôi `_bang_chu`; `RESERVED` = `keyword.kwlist` hạ chữ ∪ `{true,false,none,loop,self,super,caller,varargs,kwargs,range,dict,lipsum,cycler,joiner,namespace}`; cấm trùng `KNOWN_KEYS` hệ thống. `check_code(code) -> str` ném `ValueError` câu tiếng Việt.
- `money_word_key(code) = f"{code}_bang_chu"`.
- `normalize_value(vtype, raw) -> str` (rỗng → ""): TEXT strip, đổi xuống dòng thành khoảng trắng, ≤255 · MULTILINE `\r\n`→`\n`, ≤2000 · NUMBER nhận `,` hoặc `.` thập phân, chuẩn `^\d{1,13}(\.\d{1,2})?$` (không âm, ≤ 2 số lẻ) · DATE ISO `YYYY-MM-DD`, năm 1900..2100 · MONEY số nguyên 0..10^12 (nhận int hoặc chuỗi chữ số), lưu chuỗi chữ số.
- `format_value(vtype, stored) -> str`: DATE `dd/mm/yyyy` (dùng `context_builder.fmt_date`), MONEY `fmt_money` (15.000.000), NUMBER ngăn nghìn `.` + thập phân `,` (`1234.5` → `1.234,5`), chữ giữ nguyên.
- `MAX_CUSTOM_VARIABLES = 100`, `MAX_CUSTOM_VALUES_CHARS = 20_000`.

**Registry** `variable_registry.py` (đọc DB, dùng chung cho 02 và 03 — để 02 ∥ 03):
- `custom_rows(db, active_only=False) -> list[LaborContractVariable]`.
- `allowed_template_keys(db, keep: Iterable[str] = ()) -> tuple[frozenset, frozenset]` → (`allowed`, `inactive`): `KNOWN_KEYS` ∪ mã tùy chỉnh đang dùng ∪ `_bang_chu` của biến tiền đang dùng ∪ (mã ngừng dùng ∩ `keep`); `inactive` = mã ngừng dùng ∉ `keep` (để báo câu riêng).
- `sample_context_for(rows) -> dict` = `sample_context()` ∪ {mã: example hoặc label} ∪ companion.
- `custom_context(rows, values: dict) -> dict[str,str]`: mọi biến tùy chỉnh (kể cả ngừng dùng): giá trị HĐ → `default_value` → ""; `format_value`; biến tiền thêm `_bang_chu` = `read_amount_vi` (rỗng nếu không có giá trị).
- `template_usage(db, code) -> list[(id, name, company_id)]` — quét `LaborContractTemplate(id, name, company_id, placeholders)` trong Python (bảng nhỏ; STI của CR-629b tự lọc loại ⇒ không phải sửa khi phase 07 lên). Mã tiền: khớp cả `code` lẫn `code_bang_chu`.
- `contract_value_count(db, code) -> int` — `func.json_extract(LaborContract.custom_values, bindparam(path))` `IS NOT NULL`, path `$."<code>"` (mã đã qua regex). ⚠️ KHÔNG dùng `LaborContract.custom_values[code]` — trên SQLite SQLAlchemy biên dịch thành `JSON_QUOTE(JSON_EXTRACT(..))` ⇒ khóa vắng ra chuỗi `'null'` chứ không ra NULL ⇒ đếm sai. Đếm CẢ HĐ xóa mềm (dữ liệu vẫn còn).

**Seed** `variable_seed.py`: `ensure_system_variables(db) -> int` — chèn dòng `source=SYSTEM` cho mã trong `PLACEHOLDERS` chưa có; **không bao giờ cập nhật** dòng đã có (D-018). Gọi ở `seed.py` và `seed_prod.py` cạnh `seed_document_phase1`. Dòng hệ thống có mã không còn trong code ⇒ bị bỏ qua ở mọi chỗ đọc (không xóa).

## Migration `backend/migrations/versions/lbvar01_bien_mau_hdld_cr630.py` (viết tay)
`revision="lbvar01"`, `down_revision="lbrct02"`. Không import mã ứng dụng, không chèn dữ liệu (seed lo — tránh chữ Việt trong migration + giữ D-018).
- upgrade: tạo bảng nếu chưa có (gác `inspect`), tạo unique + index; thêm `custom_values JSON NULL` vào `tab_labor_contract` nếu thiếu.
- downgrade: drop cột nếu còn; drop bảng nếu còn.
- Thêm `variable_model` vào `backend/app/core/all_models.py`.

## Tệp
- Tạo: `backend/app/modules/labor_contract/variable_model.py`, `variable_rules.py`, `variable_registry.py`, `variable_seed.py`, `backend/migrations/versions/lbvar01_bien_mau_hdld_cr630.py`, `test/backend/test_hdld_bien_mau_nen_cr630.py`
- Sửa: `backend/app/core/labor_contract_codes.py`, `backend/app/core/all_models.py`, `backend/app/modules/labor_contract/model.py` (1 cột), `backend/app/seed.py`, `backend/app/seed_prod.py` (1 dòng gọi mỗi tệp), TS sinh từ `gen_status_ts` (chỉ sinh)
- KHÔNG đổi: `placeholder_catalog.py` (giữ `PLACEHOLDERS/KNOWN_KEYS/sample_context` làm nguồn biến hệ thống + nhãn mặc định để seed).

## Các bước
1. `alembic heads` = `lbrct02`. 2. Mã số + gen TS. 3. Model + cột. 4. `variable_rules` + test thuần. 5. Registry + seed. 6. Migration tay; local `upgrade head` → `downgrade lbrct02` → `upgrade head`. 7. Chạy test.

## Test — `test/backend/test_hdld_bien_mau_nen_cr630.py`
- `check_code`: hợp lệ; rỗng, 1 ký tự, 41 ký tự, chữ hoa, có dấu tiếng Việt, số đầu, `__`, đuôi `_`, đuôi `_bang_chu`, từ cấm (`range`, `loop`, `class`), trùng `ho_ten` ⇒ ValueError.
- `normalize_value`/`format_value` mỗi kiểu + biên: tiền âm/10^12+1/«1.000»; số `1,5`→`1.5`→`1,5`; `1234567.25`→`1.234.567,25`; 3 số lẻ ⇒ lỗi; ngày `0001-01-01`, `2101-01-01` ⇒ lỗi; `31/12/2026` (sai định dạng) ⇒ lỗi; chữ 256 ký tự ⇒ lỗi.
- `ensure_system_variables`: lần 1 chèn 50; sửa nhãn rồi chạy lại ⇒ 0 chèn, nhãn giữ (D-018); `seed_prod.run` có gọi (soi mã nguồn hoặc mock).
- `allowed_template_keys`: biến ngừng dùng ∉ allowed trừ khi ở `keep`; biến tiền đang dùng có `_bang_chu`.
- `contract_value_count`: SQLite chạy đúng (khóa vắng = 0, có = 1, HĐ xóa mềm vẫn đếm); biên dịch sang dialect MySQL ra `JSON_EXTRACT(` không có `JSON_QUOTE`.
- Schema DB sau `Base.metadata` có bảng + cột `custom_values`; một head alembic.
```bash
docker compose exec -T api python -m pytest -q test/backend/test_hdld_bien_mau_nen_cr630.py test/backend/test_hdld_bo_may_docx.py test/backend/test_status_catalog_b01.py test/backend/test_dong_bo_giao_dien_v2.py
```

## Tiêu chí xong
Migration lên/xuống/lên sạch trên MySQL local; seed chèn đúng 50 dòng hệ thống, chạy lại 0; test trên xanh; `alembic heads` = `lbvar01`.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Đếm giá trị HĐ sai trên SQLite (JSON_QUOTE) ⇒ test xanh giả | TB × Cao | Dùng `func.json_extract`; test biên dịch MySQL |
| Phase 07 CR-629b cũng tạo migration sau `lbrct02` ⇒ 2 head | TB × TB | Ghi chú đã đặt trong phase 07: `lbrct03.down_revision="lbvar01"`; test 1 head |
| Sửa JSON tại chỗ không được lưu | TB × TB | Docstring + luôn gán dict mới (phase 03) + test |

## Bảo mật
Bảng biến không chứa dữ liệu cá nhân; `custom_values` có thể nhạy cảm (kiểu lương) ⇒ che ở phase 03.
