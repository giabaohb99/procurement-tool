# TÀI LIỆU API — VĂN THƯ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `doc-type-link-rule`, `doc_folder`, `doc_folder_access`, `doc_type`, `document`, `document-clone`, `document-dashboard`, `document-link`, `document-numbering-rule`, `document-scope`, `document-signature`, `document_book`, `document_template`, `dossier`, `dossier_type`, `external_party`, `issue-code`, `security_level`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `document`, `doc_catalog`, `dossier`; danh mục dựng bằng `make_crud_router`: `/api/doc-types`, `/api/dossier-types`, `/api/dossiers`, `/api/external-parties`, `/api/security-levels`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/document-approvals/legacy-decisions` | legacy decisions | `document.approve` |  | |
| GET | `/api/document-approvals/legacy-pending` | legacy pending | `document.approve` |  | |
| GET | `/api/document-templates` | list templates | `doc_template.read` |  | |
| POST | `/api/document-templates` | create template | `doc_template.create` |  | |
| DELETE | `/api/document-templates/{template_id}` | delete template | `doc_template.delete` |  | |
| GET | `/api/document-templates/{template_id}` | get template | `doc_template.read` |  | |
| PATCH | `/api/document-templates/{template_id}` | update template | `doc_template.write` |  | |
| GET | `/api/documents` | list documents | `document.read` |  | |
| POST | `/api/documents` | create document | `document.create` |  | |
| GET | `/api/documents/applies-to-me` | F05 — danh sách văn bản đang áp dụng cho chính người đang đăng nhập. | — |  | |
| POST | `/api/documents/approval-preview` | Xem trước luồng duyệt SẼ áp nếu gửi duyệt ngay bây giờ. | `document.create` | `get_scoped` | |
| GET | `/api/documents/dashboard` | Đủ số liệu cho cả trang trong MỘT lần gọi. | `document.read` |  | |
| GET | `/api/documents/export/xlsx` | Xuất danh sách văn bản ra Excel. | `document.export` |  | |
| POST | `/api/documents/import/parse` | Đọc tệp trên máy người dùng, trả HTML để chèn tại con trỏ. | — |  | |
| POST | `/api/documents/maintenance/activate-due` | Chuyển các phiên bản đã duyệt sang hiệu lực khi tới ngày, cho TOÀN bảng. | `document.approve` |  | |
| GET | `/api/documents/number-preview` | Số hiệu SẼ cấp — chỉ để xem trước (D08), **không chiếm số**. | `document.read` |  | |
| GET | `/api/documents/prerequisite-check` | E04b — loại này bắt buộc trỏ tới loại nào mà kho chưa có văn bản nào? | `document.read` |  | |
| GET | `/api/documents/scope-options` | Nhãn tiếng Việt do backend cấp — giao diện không chép cứng. | `document.read` |  | |
| GET | `/api/documents/search` | Tìm trên siêu dữ liệu + nội dung soạn thảo + chữ trong tệp đính kèm. | `document.read` |  | |
| GET | `/api/documents/sign-kinds` | Ba loại chữ ký kèm CÂU GIÁ TRỊ PHÁP LÝ của từng loại. | `document.read` |  | |
| GET | `/api/documents/storage-locations` | Các NƠI LƯU TRỮ CỨNG đã từng nhập — gợi ý cho ô nhập ở form văn bản. | `document.read` |  | |
| GET | `/api/documents/suggestions` | Văn bản cùng loại cùng phòng đang hiệu lực — hiện ngay trong form soạn (B05). | `document.read` |  | |
| GET | `/api/documents/summary` | document summary | `báo cáo 11`, `document.read` |  | |
| GET | `/api/documents/summary/export` | document summary export | `báo cáo 11`, `document.export` |  | |
| DELETE | `/api/documents/{document_id}` | delete document | `document.delete` |  | |
| GET | `/api/documents/{document_id}` | get document | — |  | |
| PATCH | `/api/documents/{document_id}` | update document | `document.write` |  | |
| GET | `/api/documents/{document_id}/access` | Bảng chia sẻ: đang chia cho ai, hết hạn khi nào, ai đã bị thu hồi. | `document.read` |  | |
| POST | `/api/documents/{document_id}/access` | Chia quyền (hoặc cấm) cho một người / phòng ban / pháp nhân / vai trò. | `document.write` |  | |
| POST | `/api/documents/{document_id}/access/{access_id}/revoke` | revoke access | `document.write` |  | |
| GET | `/api/documents/{document_id}/amended-by` | J10 — văn bản này đã bị sửa đổi / thay thế / bãi bỏ bởi những văn bản nào. | — |  | |
| POST | `/api/documents/{document_id}/approve` | approve document | `document.approve` |  | |
| GET | `/api/documents/{document_id}/attachments` | Tệp của MỌI phiên bản — dùng cho tab Tệp (rẽ 0/1/nhiều, cây theo phiên bản). | — |  | |
| DELETE | `/api/documents/{document_id}/ban-nhap` | Nút "Hủy" ở màn Tạo văn bản — dọn bản nháp mà chính mình vừa mở. | `document.create` |  | |
| PUT | `/api/documents/{document_id}/clone-plan` | Khai TRƯỚC những pháp nhân sẽ nhận bản riêng, ngay từ lúc lập văn bản. | `document.write` |  | |
| PATCH | `/api/documents/{document_id}/clone-status` | Pháp nhân con cập nhật tình trạng xử lý bản clone của mình. | `document.write` |  | |
| GET | `/api/documents/{document_id}/clones` | F10 — *"12 công ty con đang ở phiên bản nào của quy chế này"*. | `document.read` |  | |
| POST | `/api/documents/{document_id}/clones` | F06–F09 — sinh bản nháp cho từng pháp nhân con và báo cho họ. | `document.create` |  | |
| POST | `/api/documents/{document_id}/copy` | Tạo bản nháp độc lập cùng pháp nhân để dựng nhanh dữ liệu thử. | `document.create` |  | |
| GET | `/api/documents/{document_id}/excerpts` | list excerpts | `document.read` |  | |
| POST | `/api/documents/{document_id}/excerpts` | C19 — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn. | `document.create` |  | |
| GET | `/api/documents/{document_id}/export/docx` | Xuất một phiên bản văn bản ra tệp Word (.docx). | — |  | |
| GET | `/api/documents/{document_id}/impact` | E07 — LIỆT KÊ trước khi bấm: sửa/bãi bỏ văn bản này thì con nào bị gì. | `document.read` |  | |
| POST | `/api/documents/{document_id}/issue` | NÚT "BAN HÀNH" CỦA NGƯỜI SOẠN — gác bằng quyền SỬA, không phải quyền Duyệt. | `document.write` |  | |
| PATCH | `/api/documents/{document_id}/issue-number` | Văn thư sửa số khi chính quy tắc đã bật quyền, luôn ghi lý do vào nhật ký. | `document.write` |  | |
| GET | `/api/documents/{document_id}/issue-preview` | J04 — mọi thứ sắp xảy ra khi bấm Ban hành. Chỉ đọc, không đụng gì. | `document.read` |  | |
| GET | `/api/documents/{document_id}/link-slots` | E03 — các ô quan hệ form phải tự hiện cho loại của văn bản này. | `document.read` |  | |
| GET | `/api/documents/{document_id}/links` | Quan hệ hai chiều của một văn bản, cộng phần khai còn thiếu để gửi duyệt. | `document.read` |  | |
| POST | `/api/documents/{document_id}/links` | add link | `document.write` |  | |
| DELETE | `/api/documents/{document_id}/links/{link_id}` | delete link | `document.write` |  | |
| GET | `/api/documents/{document_id}/mailboxes` | Những hộp thư TÔI được gửi danh nghĩa khi ban hành văn bản này. | `document.read` |  | |
| GET | `/api/documents/{document_id}/permissions` | Tôi được làm gì trên ĐÚNG văn bản này — để giao diện ẩn nút cho đỡ vướng. | — |  | |
| POST | `/api/documents/{document_id}/reject` | reject document | `document.approve` |  | |
| POST | `/api/documents/{document_id}/reviewed` | Xác nhận ĐÃ RÀ SOÁT xong — tắt cờ "cần rà lại". | `document.write` |  | |
| POST | `/api/documents/{document_id}/revoke` | Bãi bỏ văn bản ĐÃ ban hành. Đây là lối thoát duy nhất cho văn bản đã cấp | `document.cancel` |  | |
| GET | `/api/documents/{document_id}/scopes` | list scopes | `document.read` |  | |
| POST | `/api/documents/{document_id}/scopes` | add scope | `document.write` |  | |
| DELETE | `/api/documents/{document_id}/scopes/{scope_id}` | delete scope | `document.write` |  | |
| GET | `/api/documents/{document_id}/signatures` | list signatures | `document.read` |  | |
| POST | `/api/documents/{document_id}/signatures` | sign document | `document.approve` |  | |
| POST | `/api/documents/{document_id}/submit` | submit document | `document.write` |  | |
| GET | `/api/documents/{document_id}/tree` | E06 — mở một Quy trình thấy ngay Hướng dẫn công việc và Biểu mẫu thuộc nó. | `document.read` |  | |
| GET | `/api/documents/{document_id}/versions` | list versions | — |  | |
| POST | `/api/documents/{document_id}/versions` | create version | `document.write` |  | |
| GET | `/api/documents/{document_id}/versions/{version_id}` | Kèm nội dung — chỉ trang soạn thảo gọi, danh sách phiên bản thì không. | — |  | |
| PATCH | `/api/documents/{document_id}/versions/{version_id}` | Ghi nội dung bản nháp. Bản đã duyệt → 409, kể cả gọi thẳng không qua UI. | `document.write` |  | |
| POST | `/api/doc-folders` | create folder | `doc_folder.create` |  | |
| POST | `/api/doc-folders/documents/link` | link documents | `document.write` |  | |
| POST | `/api/doc-folders/documents/unlink` | unlink documents | `document.write` |  | |
| POST | `/api/doc-folders/reorder` | reorder folders | `doc_folder.write` |  | |
| GET | `/api/doc-folders/search` | search folders | `doc_folder.read` |  | |
| GET | `/api/doc-folders/tree` | get tree | `doc_folder.read` |  | |
| DELETE | `/api/doc-folders/{folder_id}` | delete folder | `doc_folder.delete` |  | |
| GET | `/api/doc-folders/{folder_id}` | get folder | `doc_folder.read` |  | |
| PATCH | `/api/doc-folders/{folder_id}` | update folder | `doc_folder.write` |  | |
| GET | `/api/doc-folders/{folder_id}/access` | list access | `doc_folder.write` |  | |
| POST | `/api/doc-folders/{folder_id}/access` | grant access | `doc_folder.write` |  | |
| POST | `/api/doc-folders/{folder_id}/access/bulk` | Hộp "Chia sẻ" kiểu Drive — cấp CÙNG một mức cho CẢ danh sách chủ thể | `doc_folder.write` |  | |
| DELETE | `/api/doc-folders/{folder_id}/access/{access_id}` | revoke access | `doc_folder.write` |  | |
| PATCH | `/api/doc-folders/{folder_id}/access/{access_id}` | Đổi MỨC tại chỗ — menu thả xuống trên dòng "Người có quyền" của hộp | `doc_folder.write` |  | |
| GET | `/api/doc-folders/{folder_id}/delete-preview` | Số văn bản trong thư mục + số văn bản sẽ mồ côi nếu xóa — cho hộp xác nhận. | `doc_folder.delete` |  | |
| POST | `/api/doc-folders/{folder_id}/move` | move folder | `doc_folder.write` |  | |
| GET | `/api/doc-type-link-rules` | list rules | `doc_link_rule.read` |  | |
| POST | `/api/doc-type-link-rules` | create rule | `doc_link_rule.create` |  | |
| GET | `/api/doc-type-link-rules/options` | Danh sách giá trị cho form — để giao diện khỏi chép cứng nhãn tiếng Việt. | `doc_link_rule.read` |  | |
| DELETE | `/api/doc-type-link-rules/{rule_id}` | delete rule | `doc_link_rule.delete` |  | |
| GET | `/api/doc-type-link-rules/{rule_id}` | get rule | `doc_link_rule.read` |  | |
| PATCH | `/api/doc-type-link-rules/{rule_id}` | update rule | `doc_link_rule.write` |  | |
| GET | `/api/document-books` | list books | — | `apply_scope` | |
| POST | `/api/document-books` | create book | `document_book.create` |  | |
| DELETE | `/api/document-books/{book_id}` | delete book | `document_book.delete` |  | |
| GET | `/api/document-books/{book_id}` | get book | — |  | |
| PATCH | `/api/document-books/{book_id}` | update book | `document_book.write` |  | |
| GET | `/api/document-books/{book_id}/counter` | Tình trạng bộ đếm của sổ trong một năm — dùng cho khối "Bộ đếm" trên trang chi tiết. | — |  | |
| GET | `/api/document-numbering-rules` | list rules | `doc_numbering_rule.read` |  | |
| POST | `/api/document-numbering-rules` | create rule | `doc_numbering_rule.create` |  | |
| DELETE | `/api/document-numbering-rules/{rule_id}` | delete rule | `doc_numbering_rule.delete` |  | |
| GET | `/api/document-numbering-rules/{rule_id}` | get rule | `doc_numbering_rule.read` |  | |
| PATCH | `/api/document-numbering-rules/{rule_id}` | update rule | `doc_numbering_rule.write` |  | |
| PUT | `/api/documents/{document_id}/folders` | set document folders | `document.write` |  | |
| GET | `/api/issue-codes` | Mọi mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu. | `doc_numbering_rule.read` |  | |
| PATCH | `/api/issue-codes` | update issue code | `doc_numbering_rule.write` |  | |
| GET | `/api/dossier-types/stats` | Đếm NGƯỢC: mỗi loại có bao nhiêu hồ sơ đang dùng. | `dossier_type.read` | `apply_scope` | |
| GET | `/api/dossiers/applicable` | Các hồ sơ phải kèm theo chứng từ này, kèm câu lý do vì sao khớp. | `dossier.read` | `get_scoped` | |
| PATCH | `/api/dossiers/applicable/{dossier_id}/progress` | Đặt tiến độ của MỘT tờ hồ sơ TRÊN MỘT chứng từ. | `dossier.read` | `get_scoped` | |
| GET | `/api/doc-types` | list items | `doc_type.read` | `apply_scope` | |
| POST | `/api/doc-types` | create item | `doc_type.create` |  | |
| GET | `/api/doc-types/export/csv` | export csv | `doc_type.export` | `apply_scope` | |
| DELETE | `/api/doc-types/{oid}` | delete item | `doc_type.delete` | `get_scoped` | |
| GET | `/api/doc-types/{oid}` | get item | `doc_type.read` | `get_scoped` | |
| PATCH | `/api/doc-types/{oid}` | update item | `doc_type.write` | `get_scoped` | |
| GET | `/api/dossier-types` | list items | `dossier_type.read` | `apply_scope` | |
| POST | `/api/dossier-types` | create item | `dossier_type.create` |  | |
| GET | `/api/dossier-types/export/csv` | export csv | `dossier_type.export` | `apply_scope` | |
| POST | `/api/dossier-types/import/csv` | import csv | `dossier_type.import` | `scope_condition` | |
| DELETE | `/api/dossier-types/{oid}` | delete item | `dossier_type.delete` | `get_scoped` | |
| GET | `/api/dossier-types/{oid}` | get item | `dossier_type.read` | `get_scoped` | |
| PATCH | `/api/dossier-types/{oid}` | update item | `dossier_type.write` | `get_scoped` | |
| GET | `/api/dossiers` | list items | `dossier.read` | `apply_scope` | |
| POST | `/api/dossiers` | create item | `dossier.create` |  | |
| GET | `/api/dossiers/export/csv` | export csv | `dossier.export` | `apply_scope` | |
| DELETE | `/api/dossiers/{oid}` | delete item | `dossier.delete` | `get_scoped` | |
| GET | `/api/dossiers/{oid}` | get item | `dossier.read` | `get_scoped` | |
| PATCH | `/api/dossiers/{oid}` | update item | `dossier.write` | `get_scoped` | |
| GET | `/api/external-parties` | list items | `external_party.read` | `apply_scope` | |
| POST | `/api/external-parties` | create item | `external_party.create` |  | |
| GET | `/api/external-parties/export/csv` | export csv | `external_party.export` | `apply_scope` | |
| POST | `/api/external-parties/import/csv` | import csv | `external_party.import` | `scope_condition` | |
| DELETE | `/api/external-parties/{oid}` | delete item | `external_party.delete` | `get_scoped` | |
| GET | `/api/external-parties/{oid}` | get item | `external_party.read` | `get_scoped` | |
| PATCH | `/api/external-parties/{oid}` | update item | `external_party.write` | `get_scoped` | |
| GET | `/api/security-levels` | list items | `security_level.read` | `apply_scope` | |
| POST | `/api/security-levels` | create item | `security_level.create` |  | |
| GET | `/api/security-levels/export/csv` | export csv | `security_level.export` | `apply_scope` | |
| POST | `/api/security-levels/import/csv` | import csv | `security_level.import` | `scope_condition` | |
| DELETE | `/api/security-levels/{oid}` | delete item | `security_level.delete` | `get_scoped` | |
| GET | `/api/security-levels/{oid}` | get item | `security_level.read` | `get_scoped` | |
| PATCH | `/api/security-levels/{oid}` | update item | `security_level.write` | `get_scoped` | |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
