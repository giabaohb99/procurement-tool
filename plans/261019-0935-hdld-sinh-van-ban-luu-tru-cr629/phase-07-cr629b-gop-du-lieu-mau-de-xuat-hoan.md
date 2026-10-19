# Phase 07 — CR-629b (bước B): gộp BẢNG mẫu HĐLĐ vào `tab_document_template` — schema, migration dữ liệu, backend

**Sub-scope:** CR-629b bước B · **Ưu tiên:** P2 · **Trạng thái:** done 19/10/2026 (chưa deploy) · **Effort:** 6.5h
**Phụ thuộc:** 01–06 đã commit (bước A đang CHƯA commit trong cây làm việc — commit trước khi bắt đầu); `alembic heads` = đúng 1 head `lbrct02` (kiểm lại ngay trước khi viết migration — plan CR-628 nhập Excel nhân sự có thể chen migration).
**Tên tệp giữ `...-de-xuat-hoan.md`** cho link cũ không gãy; nội dung nay là phase đang làm.

> ⚠️ **Phối hợp duoc-CR-630** (`plans/261019-1100-bien-mau-hdld-crud-cr630/`, thêm 19/10/2026): CR-630 chen migration **`lbvar01`** (`down_revision="lbrct02"`: bảng `tab_labor_contract_variable` + cột `tab_labor_contract.custom_values`). Nếu CR-630 lên trước ⇒ `lbrct03` phải khai **`down_revision="lbvar01"`** và mọi chỗ «`downgrade lbrct02`» trong phase này/phase 08 đọc thành «`downgrade lbvar01`». Kiểm `alembic heads` = 1 trước khi viết. CR-630 cũng sửa `labor_contract/generate_service.py` (hàm `generate`, không đụng `_pick_template`) ⇒ rebase, xung đột chữ tối thiểu. CR-630 đọc mẫu qua `LaborContractTemplate.placeholders` (STI trong suốt — không cần sửa thêm).

## Quyết định khóa (đã cân nhắc phương án)

| # | Vấn đề | Chọn | Bỏ | Lý do |
|---|---|---|---|---|
| Q1 | Tách 2 loại mẫu trong 1 bảng | **Single-table inheritance (STI)** của SQLAlchemy: lớp gốc `TemplateRecord` (giữ `__tablename__="tab_document_template"`, `polymorphic_on=template_kind`), 2 lớp con `DocumentTemplate` (=1) và `LaborContractTemplate` (=2) | Thêm `WHERE kind=…` tay ở từng truy vấn | Mọi `db.query(X)`, `db.get(X,id)`, `apply_scope`, `get_scoped`, `names_map(db, X, …)`, `Reference(X, …)` **tự** thêm điều kiện loại ⇒ 0 chỗ quên lọc. Đã thử trên SQLAlchemy 2.0.35 trong container: `get(Lct, id_mẫu_VB)` → None (kể cả đang ở identity map), `query(Lct.id, Lct.name)` chỉ ra dòng loại 2 |
| Q2 | Chiến lược id | **GIỮ NGUYÊN id mẫu HĐLĐ**; nếu trùng id thì **dời id mẫu văn bản thường** (`id += M`, `M = max(max id HĐLĐ, max id mẫu VB)`) | Chèn id mới + bảng ánh xạ + `UPDATE tab_labor_contract.template_id` | Mẫu văn bản thường **không ai trỏ về** (nội dung chép vào phiên bản 1.0; đã grep backend + FE). `tab_labor_contract` — bảng chứng từ pháp lý — **không bị đụng một dòng nào** ở cả 2 chiều migration. Đánh đổi: lịch sử thao tác `document_template` cũ trỏ id cũ (không remap `tab_audit_log`, YAGNI — mở id cũ ra 404, không lộ gì) |
| Q3 | `doc_type_id` của mẫu HĐLĐ | **0** | Gán id loại `HDLD` | Loại `HDLD` seed insert-only CHẠY SAU `alembic upgrade` (start.prod.sh) ⇒ lúc migration có thể chưa có; admin còn đổi/tắt được. Nhận diện bằng `template_kind`, không bằng mã loại (cùng tinh thần CR-629). Chốt xóa loại văn bản (`doc_catalog/references.py`) không bị ảnh hưởng |
| Q4 | API | **Giữ `/api/labor-contract-templates` y nguyên** (đường, JSON, khóa `labor_contract_template`, phạm vi `company`); `/api/document-templates` y nguyên hình dạng | FE chuyển sang `doc_template` API + lọc kind | 0 thay đổi FE; quyền HĐLĐ không phải ghép vào controller `doc_template` |
| Q5 | Bảng cũ | Đổi tên `tab_labor_contract_template` → `tab_labor_contract_template_bak629`, **không model, không code đọc**; xóa ở `lbrct04` của **lần phát hành sau** (phase 08) | View đọc-chỉ | Không script/raw SQL nào đọc bảng cũ (grep `backend/scripts` sạch); view làm autogenerate rối thêm. Bản bak chỉ để đối chiếu tay |
| Q6 | `note` của HĐLĐ | Dùng cột `description` sẵn có, lớp con khai `note = synonym("description")` | Thêm cột `note` | DRY; schema HĐLĐ vẫn chặn 500 ký tự |
| Q7 | Mã `template_kind` | `IntEnum DocumentTemplateKind` (1 `HTML`, 2 `LABOR_CONTRACT_DOCX`) ở `app/core/document_template_codes.py`, đăng ký `CodeSet` + chạy `gen_status_ts` (luật R2) | Chuỗi | Luật R2; API không trả trường này (không lộ) |

## Luồng dữ liệu sau khi gộp

```
tab_document_template (1 bảng)
 ├─ template_kind=1  ← DocumentTemplate      ← /api/document-templates  (doc_template, PUBLIC)  ← Thiết lập › Văn bản mẫu, ô «Chọn mẫu» khi soạn
 │     cột dùng: doc_type_id>0, name, description, content_html, is_active
 └─ template_kind=2  ← LaborContractTemplate ← /api/labor-contract-templates (labor_contract_template, phạm vi company)
       cột dùng: company_id, contract_type, name, description(=note), file_id→tab_file, original_filename, placeholders, is_active
       ↑ tab_labor_contract.template_id (FK mềm, id KHÔNG đổi) ← generate_service · serializer · chốt xóa · templates_for_* · editor CR-606
```
Không lớp nào được `db.query(TemplateRecord)` ngoài migration/test (test grep chặn — ca T13).

## Schema đích `tab_document_template`
Thêm: `template_kind SMALLINT NOT NULL DEFAULT 1` · `company_id BIGINT NOT NULL DEFAULT 0` · `contract_type SMALLINT NOT NULL DEFAULT 0` · `file_id BIGINT NOT NULL DEFAULT 0` · `original_filename VARCHAR(255) NOT NULL DEFAULT ''` · `placeholders JSON NULL`.
Bỏ unique `uq_document_template_type_name`; thêm unique `uq_document_template_kind_scope_name (template_kind, doc_type_id, company_id, name)` (loại 1: ≡ (doc_type_id,name) cũ vì company_id=0; loại 2: ≡ (company_id,name) cũ vì doc_type_id=0).
Thêm index `ix_document_template_lct_pick (template_kind, company_id, contract_type, is_active)`; giữ `ix_document_template_type_active`.

## Migration `lbrct03_gop_mau_hdld_vao_thu_vien_van_ban.py` (viết tay, `down_revision="lbrct02"`)
Không import mã ứng dụng (hằng 1/2 chép tay, như `test_hop_dong_b02`). MySQL: DDL tự commit ngầm ⇒ thứ tự DDL → DML (1 giao dịch) → rename; mỗi bước tự gác để chạy lại sau sự cố an toàn.

**upgrade()**
1. DDL cột — `op.batch_alter_table` (SQLite dựng lại bảng, MySQL ra ALTER thường), thêm cột nào thiếu (gác bằng `inspect`).
2. DDL ràng buộc — gác theo tên: drop `uq_document_template_type_name` nếu còn; tạo unique + index mới nếu chưa có.
3. DML — CHỈ khi bảng `tab_labor_contract_template` còn VÀ chưa có dòng `template_kind=2`:
   - `n, max_lct` = đếm / max id bảng cũ; `max_doc` = max id mẫu VB; `orphan_truoc` = số `tab_labor_contract.template_id>0` không có trong bảng cũ (HĐ xóa mềm có thể trỏ mẫu đã xóa — ai-CR-177).
   - Có id trùng (`EXISTS doc.id IN lct.id`) ⇒ `M = max(max_lct, max_doc)`; `UPDATE tab_document_template SET id = id + :M WHERE template_kind = 1` (mọi id mới > M ≥ mọi id hiện có ⇒ không đụng khóa giữa câu lệnh, thứ tự duyệt không quan trọng).
   - `INSERT INTO tab_document_template (id, template_kind, doc_type_id, name, description, content_html, is_active, company_id, contract_type, file_id, original_filename, placeholders, created_at, created_by, updated_at, updated_by) SELECT id, 2, 0, name, note, '', is_active, company_id, contract_type, file_id, original_filename, placeholders, created_at, created_by, updated_at, updated_by FROM tab_labor_contract_template` — tập hợp, chạy được với số dòng bất kỳ; **chép `file_id`, KHÔNG chép byte, KHÔNG đụng `tab_file`**.
   - Kiểm: số dòng loại 2 = `n` VÀ `orphan_sau` (so với id loại 2) = `orphan_truoc`; lệch ⇒ `raise RuntimeError` (DML rollback, `alembic_version` không đổi).
4. Rename `tab_labor_contract_template` → `tab_labor_contract_template_bak629` nếu bảng cũ còn và bak chưa có.
- MySQL 8: `UPDATE` id lên giá trị lớn hơn bộ đếm thì bộ đếm `AUTO_INCREMENT` tự nâng; INSERT id tường minh cũng vậy ⇒ không cần `ALTER … AUTO_INCREMENT` (vẫn kiểm tay ở diễn tập, phase 08).

**downgrade()** — nguồn sự thật là bảng GỘP (giữ cả sửa đổi + mẫu tạo sau khi lên):
1. Nếu `template_kind` còn và có dòng loại 2: trong 1 giao dịch — `DELETE FROM …_bak629`; `INSERT INTO …_bak629 (…) SELECT id, company_id, contract_type, name, SUBSTR(description,1,500), file_id, original_filename, placeholders, is_active, audit… FROM tab_document_template WHERE template_kind=2`; kiểm số dòng; `DELETE FROM tab_document_template WHERE template_kind=2`.
2. Rename bak → `tab_labor_contract_template` (nếu bak còn).
3. DDL ngược: drop index/unique mới, tạo lại `uq_document_template_type_name`, drop 6 cột (batch).
- id mẫu VB đã dời **giữ nguyên** khi xuống (không ai trỏ về). `tab_labor_contract` không đụng.
- Ca biên đã biết: mọi mẫu HĐLĐ bị xóa sau khi lên ⇒ bước 1 bỏ qua ⇒ bảng khôi phục mang dòng cũ của bak (tệp đã xóa). Xử lý tay: `DELETE` các dòng có `file_id` không còn trong `tab_file` (ghi ở runbook phase 08).

## Thay đổi mã (backend)
- `app/core/document_template_codes.py` (MỚI): `DocumentTemplateKind` + `register(CodeSet…)` theo khuôn `labor_contract_codes.py`; nạp tệp ở chỗ các code set khác được nạp; chạy `python -m scripts.gen_status_ts` (tệp TS sinh ra đổi theo — chỉ sinh, không tay).
- `app/modules/document/template_model.py`: `TemplateRecord(Base, AuditMixin)` mang TẤT CẢ cột + `__table_args__` mới + `__mapper_args__={"polymorphic_on": template_kind}`; `doc_type_id` thêm `default=0`; `DocumentTemplate(TemplateRecord)` chỉ có `{"polymorphic_identity": DocumentTemplateKind.HTML}`. Docstring ghi rõ: CẤM truy vấn `TemplateRecord` ngoài migration.
- `app/modules/labor_contract/template_model.py`: `LaborContractTemplate(TemplateRecord)` — bỏ `__tablename__`/cột/`__table_args__`, thêm `polymorphic_identity=LABOR_CONTRACT_DOCX`, `note = synonym("description")`.
- `app/modules/document/template_service.get_or_404` và `labor_contract/generate_service._pick_template`: đổi `db.get` → `db.query(Model).filter(Model.id == id).first()` (tường minh, không phụ thuộc chi tiết identity map — lưới thứ hai).
- KHÔNG sửa (STI lo): `template_controller/service/serializer/web_editor` HĐLĐ, `service.templates_for_*`, `serializer.py` (tên mẫu), `company/references.py`, `doc_catalog/references.py`, `document/template_controller.py`, `scoping.SCOPE_FIELDS` (`labor_contract_template: company`, `doc_template: PUBLIC` giữ), `all_models.py` (vẫn import 2 tệp model).
- `seed*.py`: không seed mẫu HĐLĐ ⇒ không đổi; `seed_document_demo` tạo `DocumentTemplate` ⇒ tự loại 1.

## Ma trận cách ly quyền (mọi cửa đọc `doc_template`)
| Cửa | Vì sao không thấy mẫu HĐLĐ | Ca test |
|---|---|---|
| `GET /api/document-templates` (bảng Thiết lập, ô chọn mẫu khi soạn `doc_type_id=…&is_active=true`) | `query(DocumentTemplate)` ⇒ `template_kind=1`; `doc_type_id=0` cũng rỗng | T8 |
| `GET/PATCH/DELETE /api/document-templates/{id}` với id HĐLĐ | `get_or_404` loại 1 ⇒ 404; dòng + tệp còn nguyên | T9 |
| Chốt xóa loại văn bản / pháp nhân | `Reference(DocumentTemplate…)` chỉ đếm loại 1; `Reference(LaborContractTemplate,"company_id")` chỉ loại 2 | T12 |
| Trợ lý AI, tìm kiếm toàn văn, báo cáo, dashboard, import_tool | Đã grep: không ai đọc bảng mẫu | T13 (grep `TemplateRecord`) |
| Chiều ngược: `/api/labor-contract-templates` lộ mẫu VB (company_id=0, phạm vi `all`) | `query(LaborContractTemplate)` ⇒ loại 2 | T11 |

## Tệp
- Tạo: `backend/app/core/document_template_codes.py`, `backend/migrations/versions/lbrct03_gop_mau_hdld_vao_thu_vien_van_ban.py`, `test/backend/test_hdld_gop_bang_mau_migration_cr629b.py`, `test/backend/test_hdld_gop_bang_mau_cach_ly_cr629b.py`
- Sửa: `backend/app/modules/document/template_model.py`, `backend/app/modules/document/template_service.py`, `backend/app/modules/labor_contract/template_model.py`, `backend/app/modules/labor_contract/generate_service.py`, tệp TS sinh từ `gen_status_ts` (frontend-v2, chỉ sinh)
- Có thể phải sửa (chỉ khi đỏ): `test/backend/test_canh_do_dai_o_chu_cr538.py` (helper `_same` dò cột theo tên trường — `note` giờ là synonym), `test/backend/scope_factory.py` (không cần nếu chỉ map entity → lớp con)
- Sở hữu: phase 07 độc quyền các tệp trên; phase 08 không đụng.

## Các bước
1. Commit bước A; `docker compose exec api alembic heads` = 1 head `lbrct02`.
2. Code set + model STI + 2 chỗ `db.get` → chạy ngay hồi quy HĐLĐ + mẫu VB (bước 6) để bắt lỗi ánh xạ sớm, TRƯỚC khi viết migration.
3. Viết migration (tay; KHÔNG autogenerate — repo trôi ~650 dòng). Nếu muốn đối chiếu thì autogenerate ra tệp nháp rồi xóa.
4. Test migration trên SQLite (T1–T7), test cách ly (T8–T14).
5. Local MySQL: `alembic upgrade head` → `downgrade lbrct02` → `upgrade head` với dữ liệu local (5 HĐ có mẫu) — bảng kiểm tay ở phase 08 §Diễn tập.
6. Chạy ĐÚNG các tệp test dưới (không quét cả `test/backend`).

## Test (pytest, SQLite in-memory)
**`test_hdld_gop_bang_mau_migration_cr629b.py`** — engine SQLite RIÊNG, dựng schema TRƯỚC migration bằng DDL chép từ `b62f3c8d1a04` + `lbrct01` (3 bảng: mẫu VB, mẫu HĐLĐ, HĐLĐ tối giản), chạy `mig.upgrade()/downgrade()` qua `MigrationContext` + `Operations.context` (khuôn `test_hop_dong_b02.py:168`):
- T1 `test_len_giu_nguyen_id_mau_hdld_va_doi_id_mau_van_ban_khi_trung` — VB id {1,2}, HĐLĐ id {1,2,3} ⇒ loại 2 id {1,2,3} đủ trường (note→description, placeholders, file_id); VB id {4,5} nội dung y nguyên; `tab_labor_contract.template_id` byte-y-nguyên.
- T2 `test_khong_trung_id_thi_khong_doi_id_mau_van_ban` (+ ca bảng HĐLĐ rỗng ⇒ chỉ đổi schema + rename).
- T3 `test_chay_len_hai_lan_khong_nhan_doi` — gọi `upgrade()` lần 2 (mô phỏng chạy lại sau sự cố) ⇒ số dòng, id không đổi.
- T4 `test_xuong_dong_bo_sua_doi_va_mau_tao_sau_khi_len` — sau khi lên: đổi tên 1 mẫu HĐLĐ, thêm 1 mẫu HĐLĐ mới ⇒ xuống: bảng cũ có cả 2 thay đổi, đúng id; bảng VB không còn loại 2, mất 6 cột, có lại `uq_document_template_type_name`.
- T5 `test_xuoi_nguoc_xuoi_on_dinh` — lên/xuống/lên ⇒ trạng thái lần 2 = lần 1.
- T6 `test_schema_sau_migration_khop_model` — tập cột + tên unique/index của bảng sau `upgrade()` = `TemplateRecord.__table__` (bắt lệch model ↔ migration).
- T7 `test_chi_mot_head_alembic` — `ScriptDirectory.get_heads()` dài 1 (bỏ nếu repo đã có test này).

**`test_hdld_gop_bang_mau_cach_ly_cr629b.py`** — fixture `db/world/client_as` + `hdld_factory`:
- T8 `test_danh_sach_van_ban_mau_khong_co_mau_hdld` — văn thư (`doc_template.read` all) và admin: `total`/`items` chỉ loại 1; lọc `doc_type_id=0` ⇒ rỗng.
- T9 `test_get_sua_xoa_van_ban_mau_bang_id_hdld_tra_404` — người có `doc_template.write/delete`; sau đó dòng HĐLĐ + `tab_file` còn nguyên.
- T10 `test_get_va_get_scoped_khong_lan_loai` — `db.get(DocumentTemplate, id_hdld)` None (cả khi đã nạp vào session); `get_scoped(LaborContractTemplate, id_vb)` phạm vi all ⇒ None; `names_map(db, LaborContractTemplate, {id_vb})` ⇒ `{}`.
- T11 `test_api_mau_hdld_khong_tra_mau_van_ban` — admin phạm vi all: list không có dòng company_id=0; `GET /api/labor-contract-templates/{id_vb}` 404.
- T12 `test_chot_xoa_loai_van_ban_va_phap_nhan_dem_dung_loai`.
- T13 `test_khong_ma_ung_dung_nao_truy_van_lop_goc` — grep `backend/app`: `TemplateRecord` chỉ xuất hiện ở 2 tệp model.
- T14 `test_trung_ten_giua_hai_loai_duoc_phep` — mẫu VB và mẫu HĐLĐ cùng tên tạo được; HĐLĐ trùng tên cùng pháp nhân vẫn 400.

**Hồi quy bắt buộc xanh, KHÔNG sửa nội dung** (nếu đỏ là lỗi gộp): `test_hdld_mau_hop_dong_api.py` (20 ca: phạm vi pháp nhân, chốt xóa 409 khi HĐ dùng, thay tệp, tải tệp), `test_hdld_sinh_tai_tep.py` (sinh từ mẫu, `_pick_template` khác pháp nhân/loại/ngừng dùng), `test_hdld_soan_mau_tren_web.py` (editor CR-606), `test_hdld_hop_dong_api.py` (`template_name`, ô chọn mẫu theo nhân sự), `test_hdld_nen_du_lieu.py`, `test_van_thu_nhan_su_xoa_mem_cr177.py`, `test_document_template.py`, `test_hdld_van_ban_luu_tru_dong_bo_cr629.py`, `test_hdld_van_ban_luu_tru_quyen_xem_cr629.py`, `test_pham_vi_luat_bat_bien.py`, `test_pham_vi_khai_du_b07.py`, `test_canh_do_dai_o_chu_cr538.py`, `test_status_catalog_b01.py`, `test_dong_bo_giao_dien_v2.py` (TS sinh khớp).
```bash
docker compose exec -T api python -m pytest -q test/backend/test_hdld_gop_bang_mau_migration_cr629b.py test/backend/test_hdld_gop_bang_mau_cach_ly_cr629b.py
docker compose exec -T api python -m pytest -q test/backend/test_hdld_mau_hop_dong_api.py test/backend/test_hdld_sinh_tai_tep.py test/backend/test_hdld_soan_mau_tren_web.py test/backend/test_hdld_hop_dong_api.py test/backend/test_document_template.py test/backend/test_hdld_nen_du_lieu.py test/backend/test_van_thu_nhan_su_xoa_mem_cr177.py
docker compose exec -T api python -m pytest -q test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py test/backend/test_hdld_van_ban_luu_tru_quyen_xem_cr629.py test/backend/test_pham_vi_luat_bat_bien.py test/backend/test_pham_vi_khai_du_b07.py test/backend/test_canh_do_dai_o_chu_cr538.py test/backend/test_status_catalog_b01.py test/backend/test_dong_bo_giao_dien_v2.py
```

## Tiêu chí xong (đo được)
- Chỉ còn MỘT bảng mẫu có model (`tab_document_template`); `tab_labor_contract_template` không còn model/route trỏ tới.
- 14 ca mới + toàn bộ tệp hồi quy trên xanh; 0 dòng `tab_labor_contract` bị đổi bởi migration (T1).
- Local MySQL lên/xuống/lên sạch; `AUTO_INCREMENT` > `MAX(id)`; sinh lại 1 HĐ có sẵn bằng mẫu cũ thành công.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Rò mẫu HĐLĐ qua `doc_template` (mọi vai trò `read`) | TB × Cao | STI tự lọc ở mọi truy vấn lớp con; `get_or_404` tường minh; T8–T13 |
| Code mới lỡ `query(TemplateRecord)` / core `__table__` / bulk `update()` không lọc loại | Thấp × Cao | T13 grep; docstring cấm; review |
| HĐ đã sinh mất tên mẫu / sinh lại báo «mẫu không tồn tại» | Thấp × Cao | Giữ id ⇒ không remap; kiểm orphan trước = sau, lệch thì rollback; T1, hồi quy sinh tệp |
| Migration hỏng giữa chừng trên MySQL (DDL tự commit) | Thấp × TB | Mỗi bước tự gác; DML 1 giao dịch; T3; diễn tập bản sao prod |
| Unique mới chặn dữ liệu thật | Rất thấp × TB | Tương đương ràng buộc cũ từng loại (chứng minh ở §Schema); diễn tập |
| Test cũ dò cột theo tên (`note` thành synonym) | TB × Thấp | Chỉ sửa helper test, không nới luật |
| Link/bookmark `/document/templates/{id}` cũ của mẫu VB 404 sau khi dời id | Cao × Thấp | Chấp nhận (vài mẫu, mở từ danh sách là có); ghi change-log |

## Rollback
`alembic downgrade lbrct02` (mục downgrade trên) + revert commit phase 07. Không có thao tác nào với `tab_file`, `tab_labor_contract`. Lưới cuối: bản sao lưu trước deploy (phase 08).

## Bảo mật
Không thêm entity/quyền; khóa `labor_contract_template` + phạm vi `company` giữ nguyên; schema xuất của `doc_template` không thêm trường (không lộ `company_id/file_id`). Tệp mẫu vẫn riêng tư, không `FileLink`.

## Kết quả triển khai (19/10/2026) — lệch so với kế hoạch gốc
- Migration `lbrct03` có `down_revision="lbvar01"` (CR-630 đã vào); downgrade về `lbvar01`.
- 4 quyết định sản phẩm: (1) dời id mẫu văn bản ⇒ dời luôn `tab_audit_log.entity_id` của entity `document_template`; (2) mẫu HĐLĐ nhận `doc_type_id` = loại `HDLD` nếu có lúc migrate, không thì 0, `seed_document_phase1` điền bù ô đang 0, mẫu tạo mới gắn loại HDLD, chốt xóa loại văn bản (`doc_catalog/references.py`) đếm thêm `LaborContractTemplate`; (3) bảng `..._bak629` giữ 1 lần phát hành; (4) ca biên downgrade xử lý tay.
- Downgrade dừng (RuntimeError) nếu còn mẫu HĐLĐ mà thiếu bảng bak, tránh mất dữ liệu im lặng.
- Test: `test_hdld_gop_bang_mau_migration_cr629b.py` (13 ca), `test_hdld_gop_bang_mau_cach_ly_cr629b.py` (12 ca).
