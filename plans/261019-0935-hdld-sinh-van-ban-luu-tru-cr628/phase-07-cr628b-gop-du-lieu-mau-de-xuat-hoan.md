# Phase 07 — CR-628b (bước B): gộp DỮ LIỆU mẫu HĐLĐ vào `tab_document_template` — ĐỀ XUẤT HOÃN

**Sub-scope:** CR-628b · **Trạng thái:** deferred (cần đại ca quyết, mặc định KHÔNG làm) · **Effort ước:** 10–12h · **Phụ thuộc:** 06 chạy ổn trên prod

## Khuyến nghị
Không làm. Bước A (phase 06) đã cho đúng trải nghiệm đại ca yêu cầu (một nơi, một URL, quyền theo `labor_contract_template`). Bước B chỉ đổi chỗ lưu, đổi lại rủi ro rò mẫu và gãy HĐ đã sinh. Chỉ mở lại khi có nhu cầu thật (vd soạn văn bản thường bằng mẫu `.docx` có biến).

## Nếu vẫn làm — phác thảo đã kiểm
1. **Schema** `tab_document_template` (migration viết tay): `content_kind` SMALLINT (1 HTML · 2 tệp DOCX, IntEnum + `status_catalog`), `file_id` BIGINT 0, `original_filename` VARCHAR(255), `placeholders` JSON, `company_id` BIGINT 0, `contract_type` SMALLINT 0; unique đổi thành (`doc_type_id`,`company_id`,`name`); index (`company_id`,`contract_type`,`is_active`).
2. **Quyền theo dòng**: controller `doc_template` rẽ nhánh — dòng thuộc loại `HDLD` gác bằng `labor_contract_template` + `apply_scope` theo `company_id`; danh sách `doc_template` loại trừ chúng cho người thiếu khóa (nếu không: mọi vai trò có `doc_template.read` đọc được mẫu HĐLĐ).
3. **Dữ liệu**: migration chép từng dòng `tab_labor_contract_template` → `tab_document_template` (doc_type = HDLD), giữ `file_id` (không chép byte); bảng ánh xạ id cũ→mới; `UPDATE tab_labor_contract SET template_id = <mới>`; giữ bảng cũ 1 vòng phát hành (đổi tên `_bak`) để quay đầu. Không biết số dòng prod ⇒ đếm trước, diễn tập trên bản sao.
4. **Mã**: `generate_service._pick_template`, `serializer` (tên mẫu), `template_web_editor`, `template_service` (chặn xóa khi HĐ dùng), `service.templates_for_*`, `context_builder` đổi model; ô chọn mẫu khi soạn văn bản thường loại `content_kind=2`.
5. **Test**: HĐ sinh trước migration vẫn hiện tên mẫu + sinh lại được; văn thư không đọc được mẫu HĐLĐ qua `/api/document-templates`; downgrade khôi phục id cũ.

## Rủi ro chính (lý do hoãn)
| Rủi ro | K×Ả |
|---|---|
| Rò mẫu HĐLĐ (có thể chứa mức lương mẫu, điều khoản nội bộ) cho mọi vai trò qua `doc_template.read` | TB × Cao |
| Sai ánh xạ `template_id` ⇒ HĐ đã sinh mất tên mẫu / sinh lại báo «mẫu không tồn tại» | TB × Cao |
| Downgrade phức tạp (đổi id ngược) | TB × TB |
