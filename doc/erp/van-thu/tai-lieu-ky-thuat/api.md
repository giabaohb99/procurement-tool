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

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `document`, `doc_catalog`, `dossier`; danh mục dựng bằng `make_crud_router`: `/api/doc-types`, `/api/dossier-types`, `/api/dossiers`, `/api/external-parties`, `/api/security-levels`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| POST | `/api/doc-folders` | create folder | `doc_folder.create` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/documents/link` | link documents | `document.write` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/documents/unlink` | unlink documents | `document.write` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/reorder` | reorder folders | `doc_folder.write` |  | tự dò: v2 `document` |
| GET | `/api/doc-folders/search` | search folders | `doc_folder.read` |  | tự dò: v2 `document` |
| GET | `/api/doc-folders/tree` | get tree | `doc_folder.read` |  | tự dò: v2 `document` |
| GET | `/api/doc-folders/{folder_id}` | get folder | `doc_folder.read` |  | tự dò: v2 `document` |
| PATCH | `/api/doc-folders/{folder_id}` | update folder | `doc_folder.write` |  | tự dò: v2 `document` |
| DELETE | `/api/doc-folders/{folder_id}` | delete folder | `doc_folder.delete` |  | tự dò: v2 `document` |
| GET | `/api/doc-folders/{folder_id}/access` | list access | `doc_folder.write` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/{folder_id}/access` | grant access | `doc_folder.write` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/{folder_id}/access/bulk` | Hộp "Chia sẻ" kiểu Drive — cấp CÙNG một mức cho CẢ danh sách chủ thể trong một lượt (phase 10B, đặc tả §C). | `doc_folder.write` |  | tự dò: v2 `document` |
| PATCH | `/api/doc-folders/{folder_id}/access/{access_id}` | Đổi MỨC tại chỗ — menu thả xuống trên dòng "Người có quyền" của hộp "Chia sẻ", không phải thu hồi rồi cấp lại. | `doc_folder.write` |  | tự dò: v2 `document` |
| DELETE | `/api/doc-folders/{folder_id}/access/{access_id}` | revoke access | `doc_folder.write` |  | tự dò: v2 `document` |
| GET | `/api/doc-folders/{folder_id}/delete-preview` | Số văn bản trong thư mục + số văn bản sẽ mồ côi nếu xóa — cho hộp xác nhận. | `doc_folder.delete` |  | tự dò: v2 `document` |
| POST | `/api/doc-folders/{folder_id}/move` | move folder | `doc_folder.write` |  | tự dò: v2 `document` |
| GET | `/api/doc-type-link-rules` | list rules | `doc_link_rule.read` |  | tự dò: v2 `document` |
| POST | `/api/doc-type-link-rules` | create rule | `doc_link_rule.create` |  | tự dò: v2 `document` |
| GET | `/api/doc-type-link-rules/options` | Danh sách giá trị cho form — để giao diện khỏi chép cứng nhãn tiếng Việt. | `doc_link_rule.read` |  | tự dò: v2 `document` |
| GET | `/api/doc-type-link-rules/{rule_id}` | get rule | `doc_link_rule.read` |  | tự dò: v2 `document` |
| PATCH | `/api/doc-type-link-rules/{rule_id}` | update rule | `doc_link_rule.write` |  | tự dò: v2 `document` |
| DELETE | `/api/doc-type-link-rules/{rule_id}` | delete rule | `doc_link_rule.delete` |  | tự dò: v2 `document` |
| GET | `/api/doc-types` | Danh sách văn thư › Thiết lập › Loại văn bản, có lọc và phân trang. | `doc_type.read` | `apply_scope` | tự dò: v2 `document` |
| POST | `/api/doc-types` | Thêm một dòng văn thư › Thiết lập › Loại văn bản; chặn trùng mã, ghi nhật ký. | `doc_type.create` |  | tự dò: v2 `document` |
| GET | `/api/doc-types/export/csv` | Xuất văn thư › Thiết lập › Loại văn bản ra tệp CSV theo bộ lọc đang chọn. | `doc_type.export` | `apply_scope` |  |
| GET | `/api/doc-types/{oid}` | Xem một dòng văn thư › Thiết lập › Loại văn bản theo id. | `doc_type.read` | `get_scoped` | tự dò: v2 `document` |
| PATCH | `/api/doc-types/{oid}` | Sửa một dòng văn thư › Thiết lập › Loại văn bản; chỉ ghi các ô gửi lên, ghi nhật ký. | `doc_type.write` | `get_scoped` | tự dò: v2 `document` |
| DELETE | `/api/doc-types/{oid}` | Xóa một dòng văn thư › Thiết lập › Loại văn bản; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `doc_type.delete` | `get_scoped` | tự dò: v2 `document` |
| GET | `/api/document-approvals/legacy-decisions` | legacy decisions | `document.approve` |  | tự dò: v2 `document` |
| GET | `/api/document-approvals/legacy-pending` | legacy pending | `document.approve` |  | tự dò: v2 `document` |
| GET | `/api/document-books` | list books | đăng nhập |  | tự dò: v2 `document` |
| POST | `/api/document-books` | create book | `document_book.create` |  | tự dò: v2 `document` |
| GET | `/api/document-books/{book_id}` | get book | đăng nhập |  | tự dò: v2 `document` |
| PATCH | `/api/document-books/{book_id}` | update book | `document_book.write` |  | tự dò: v2 `document` |
| DELETE | `/api/document-books/{book_id}` | delete book | `document_book.delete` |  | tự dò: v2 `document` |
| GET | `/api/document-books/{book_id}/counter` | Tình trạng bộ đếm của sổ trong một năm — dùng cho khối "Bộ đếm" trên trang chi tiết. | đăng nhập |  | tự dò: v2 `document` |
| GET | `/api/document-numbering-rules` | list rules | `doc_numbering_rule.read` |  | tự dò: v2 `document` |
| POST | `/api/document-numbering-rules` | create rule | `doc_numbering_rule.create` |  | tự dò: v2 `document` |
| GET | `/api/document-numbering-rules/{rule_id}` | get rule | `doc_numbering_rule.read` |  | tự dò: v2 `document` |
| PATCH | `/api/document-numbering-rules/{rule_id}` | update rule | `doc_numbering_rule.write` |  | tự dò: v2 `document` |
| DELETE | `/api/document-numbering-rules/{rule_id}` | delete rule | `doc_numbering_rule.delete` |  | tự dò: v2 `document` |
| GET | `/api/document-templates` | list templates | `doc_template.read` |  | tự dò: v2 `document` |
| POST | `/api/document-templates` | create template | `doc_template.create` |  | tự dò: v2 `document` |
| GET | `/api/document-templates/{template_id}` | get template | `doc_template.read` |  | tự dò: v2 `document` |
| PATCH | `/api/document-templates/{template_id}` | update template | `doc_template.write` |  | tự dò: v2 `document` |
| DELETE | `/api/document-templates/{template_id}` | delete template | `doc_template.delete` |  | tự dò: v2 `document` |
| GET | `/api/documents` | list documents | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents` | create document | `document.create` |  | tự dò: v2 `document` |
| GET | `/api/documents/applies-to-me` | F05 — danh sách văn bản đang áp dụng cho chính người đang đăng nhập. | đăng nhập |  | tự dò: v2 `document`, v2 dùng chung |
| POST | `/api/documents/approval-preview` | Xem trước luồng duyệt SẼ áp nếu gửi duyệt ngay bây giờ. | `document.create` | `get_scoped` | tự dò: v2 `document` |
| GET | `/api/documents/dashboard` | Đủ số liệu cho cả trang trong MỘT lần gọi. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/export/xlsx` | Xuất danh sách văn bản ra Excel. | `document.export` |  | tự dò: v2 `document` |
| POST | `/api/documents/import/parse` | Đọc tệp trên máy người dùng, trả HTML để chèn tại con trỏ. | đăng nhập |  | tự dò: v2 `document` |
| POST | `/api/documents/maintenance/activate-due` | Chuyển các phiên bản đã duyệt sang hiệu lực khi tới ngày, cho TOÀN bảng. | `document.approve` |  |  |
| GET | `/api/documents/number-preview` | Số hiệu SẼ cấp — chỉ để xem trước (D08), **không chiếm số**. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/prerequisite-check` | E04b — loại này bắt buộc trỏ tới loại nào mà kho chưa có văn bản nào? | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/scope-options` | Nhãn tiếng Việt do backend cấp — giao diện không chép cứng. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/search` | Tìm trên siêu dữ liệu + nội dung soạn thảo + chữ trong tệp đính kèm. | `document.read` |  | tự dò: v2 `document`, v2 dùng chung |
| GET | `/api/documents/sign-kinds` | Ba loại chữ ký kèm CÂU GIÁ TRỊ PHÁP LÝ của từng loại. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/storage-locations` | Các NƠI LƯU TRỮ CỨNG đã từng nhập — gợi ý cho ô nhập ở form văn bản. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/suggestions` | Văn bản cùng loại cùng phòng đang hiệu lực — hiện ngay trong form soạn (B05). | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/summary` | document summary | `báo cáo 11`, `document.read` |  | tự dò: v2 `report` |
| GET | `/api/documents/summary/export` | document summary export | `báo cáo 11`, `document.export` |  | tự dò: v2 `report` |
| GET | `/api/documents/{document_id}` | get document | đăng nhập |  | tự dò: v2 `document` |
| PATCH | `/api/documents/{document_id}` | update document | `document.write` |  | tự dò: v2 `document` |
| DELETE | `/api/documents/{document_id}` | delete document | `document.delete` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/access` | Bảng chia sẻ: đang chia cho ai, hết hạn khi nào, ai đã bị thu hồi. | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/access` | Chia quyền (hoặc cấm) cho một người / phòng ban / pháp nhân / vai trò. | `document.write` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/access/{access_id}/revoke` | revoke access | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/amended-by` | J10 — văn bản này đã bị sửa đổi / thay thế / bãi bỏ bởi những văn bản nào. | đăng nhập |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/approve` | approve document | `document.approve` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/attachments` | Tệp của MỌI phiên bản — dùng cho tab Tệp (rẽ 0/1/nhiều, cây theo phiên bản). | đăng nhập |  | tự dò: v2 `document` |
| DELETE | `/api/documents/{document_id}/ban-nhap` | Nút "Hủy" ở màn Tạo văn bản — dọn bản nháp mà chính mình vừa mở. | `document.create` |  | tự dò: v2 `document` |
| PUT | `/api/documents/{document_id}/clone-plan` | Khai TRƯỚC những pháp nhân sẽ nhận bản riêng, ngay từ lúc lập văn bản. | `document.write` |  | tự dò: v2 `document` |
| PATCH | `/api/documents/{document_id}/clone-status` | Pháp nhân con cập nhật tình trạng xử lý bản clone của mình. | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/clones` | F10 — *"12 công ty con đang ở phiên bản nào của quy chế này"*. | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/clones` | F06–F09 — sinh bản nháp cho từng pháp nhân con và báo cho họ. | `document.create` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/copy` | Tạo bản nháp độc lập cùng pháp nhân để dựng nhanh dữ liệu thử. | `document.create` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/excerpts` | list excerpts | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/excerpts` | C19 — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn. | `document.create` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/export/docx` | Xuất một phiên bản văn bản ra tệp Word (.docx). | đăng nhập |  |  |
| PUT | `/api/documents/{document_id}/folders` | set document folders | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/impact` | E07 — LIỆT KÊ trước khi bấm: sửa/bãi bỏ văn bản này thì con nào bị gì. | `document.read` |  |  |
| POST | `/api/documents/{document_id}/issue` | NÚT "BAN HÀNH" CỦA NGƯỜI SOẠN — gác bằng quyền SỬA, không phải quyền Duyệt. | `document.write` |  | tự dò: v2 `document` |
| PATCH | `/api/documents/{document_id}/issue-number` | Văn thư sửa số khi chính quy tắc đã bật quyền, luôn ghi lý do vào nhật ký. | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/issue-preview` | J04 — mọi thứ sắp xảy ra khi bấm Ban hành. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/link-slots` | E03 — các ô quan hệ form phải tự hiện cho loại của văn bản này. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/links` | Quan hệ hai chiều của một văn bản, cộng phần khai còn thiếu để gửi duyệt. | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/links` | add link | `document.write` |  | tự dò: v2 `document` |
| DELETE | `/api/documents/{document_id}/links/{link_id}` | delete link | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/mailboxes` | Những hộp thư TÔI được gửi danh nghĩa khi ban hành văn bản này. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/permissions` | Tôi được làm gì trên ĐÚNG văn bản này — để giao diện ẩn nút cho đỡ vướng. | đăng nhập |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/reject` | reject document | `document.approve` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/reviewed` | Xác nhận ĐÃ RÀ SOÁT xong — tắt cờ "cần rà lại". | `document.write` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/revoke` | Bãi bỏ văn bản ĐÃ ban hành. | `document.cancel` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/scopes` | list scopes | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/scopes` | add scope | `document.write` |  | tự dò: v2 `document` |
| DELETE | `/api/documents/{document_id}/scopes/{scope_id}` | delete scope | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/signatures` | list signatures | `document.read` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/signatures` | sign document | `document.approve` |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/submit` | submit document | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/tree` | E06 — mở một Quy trình thấy ngay Hướng dẫn công việc và Biểu mẫu thuộc nó. | `document.read` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/versions` | list versions | đăng nhập |  | tự dò: v2 `document` |
| POST | `/api/documents/{document_id}/versions` | create version | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/documents/{document_id}/versions/{version_id}` | Kèm nội dung — chỉ trang soạn thảo gọi, danh sách phiên bản thì không. | đăng nhập |  | tự dò: v2 `document` |
| PATCH | `/api/documents/{document_id}/versions/{version_id}` | Ghi nội dung bản nháp. | `document.write` |  | tự dò: v2 `document` |
| GET | `/api/dossier-types` | Danh sách danh mục Loại hồ sơ, có lọc và phân trang. | `dossier_type.read` | `apply_scope` | tự dò: v2 `dossier` |
| POST | `/api/dossier-types` | Thêm một dòng danh mục Loại hồ sơ; chặn trùng mã, ghi nhật ký. | `dossier_type.create` |  | tự dò: v2 `dossier` |
| GET | `/api/dossier-types/export/csv` | Xuất danh mục Loại hồ sơ ra tệp CSV theo bộ lọc đang chọn. | `dossier_type.export` | `apply_scope` |  |
| POST | `/api/dossier-types/import/csv` | Nhập danh mục Loại hồ sơ hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `dossier_type.import` | `scope_condition` |  |
| GET | `/api/dossier-types/stats` | Đếm NGƯỢC: mỗi loại có bao nhiêu hồ sơ đang dùng. | `dossier_type.read` | `apply_scope` | tự dò: v2 `dossier` |
| GET | `/api/dossier-types/{oid}` | Xem một dòng danh mục Loại hồ sơ theo id. | `dossier_type.read` | `get_scoped` |  |
| PATCH | `/api/dossier-types/{oid}` | Sửa một dòng danh mục Loại hồ sơ; chỉ ghi các ô gửi lên, ghi nhật ký. | `dossier_type.write` | `get_scoped` |  |
| DELETE | `/api/dossier-types/{oid}` | Xóa một dòng danh mục Loại hồ sơ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `dossier_type.delete` | `get_scoped` |  |
| GET | `/api/dossiers` | Danh sách hồ sơ (giấy tờ công ty), có lọc và phân trang. | `dossier.read` | `apply_scope` | tự dò: v2 `dossier` |
| POST | `/api/dossiers` | Thêm một dòng hồ sơ (giấy tờ công ty); chặn trùng mã, ghi nhật ký. | `dossier.create` |  | tự dò: v2 `dossier` |
| GET | `/api/dossiers/applicable` | Các hồ sơ phải kèm theo chứng từ này, kèm câu lý do vì sao khớp. | `dossier.read` | `get_scoped` | tự dò: v2 `dossier`, v2 `procurement`, v2 dùng chung |
| PATCH | `/api/dossiers/applicable/{dossier_id}/progress` | Đặt tiến độ của MỘT tờ hồ sơ TRÊN MỘT chứng từ. | `dossier.read` | `get_scoped` | tự dò: v2 `dossier` |
| GET | `/api/dossiers/export/csv` | Xuất hồ sơ (giấy tờ công ty) ra tệp CSV theo bộ lọc đang chọn. | `dossier.export` | `apply_scope` |  |
| GET | `/api/dossiers/{oid}` | Xem một dòng hồ sơ (giấy tờ công ty) theo id. | `dossier.read` | `get_scoped` | tự dò: v2 `dossier`, v2 `procurement`, v2 dùng chung |
| PATCH | `/api/dossiers/{oid}` | Sửa một dòng hồ sơ (giấy tờ công ty); chỉ ghi các ô gửi lên, ghi nhật ký. | `dossier.write` | `get_scoped` | tự dò: v2 `dossier`, v2 `procurement`, v2 dùng chung |
| DELETE | `/api/dossiers/{oid}` | Xóa một dòng hồ sơ (giấy tờ công ty); danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `dossier.delete` | `get_scoped` | tự dò: v2 `dossier`, v2 `procurement`, v2 dùng chung |
| GET | `/api/external-parties` | Danh sách văn thư › Thiết lập › Đơn vị gửi nhận, có lọc và phân trang. | `external_party.read` | `apply_scope` | tự dò: v2 `document` |
| POST | `/api/external-parties` | Thêm một dòng văn thư › Thiết lập › Đơn vị gửi nhận; chặn trùng mã, ghi nhật ký. | `external_party.create` |  | tự dò: v2 `document` |
| GET | `/api/external-parties/export/csv` | Xuất văn thư › Thiết lập › Đơn vị gửi nhận ra tệp CSV theo bộ lọc đang chọn. | `external_party.export` | `apply_scope` |  |
| POST | `/api/external-parties/import/csv` | Nhập văn thư › Thiết lập › Đơn vị gửi nhận hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `external_party.import` | `scope_condition` |  |
| GET | `/api/external-parties/{oid}` | Xem một dòng văn thư › Thiết lập › Đơn vị gửi nhận theo id. | `external_party.read` | `get_scoped` | tự dò: v2 `document` |
| PATCH | `/api/external-parties/{oid}` | Sửa một dòng văn thư › Thiết lập › Đơn vị gửi nhận; chỉ ghi các ô gửi lên, ghi nhật ký. | `external_party.write` | `get_scoped` | tự dò: v2 `document` |
| DELETE | `/api/external-parties/{oid}` | Xóa một dòng văn thư › Thiết lập › Đơn vị gửi nhận; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `external_party.delete` | `get_scoped` | tự dò: v2 `document` |
| GET | `/api/issue-codes` | Mọi mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu. | `doc_numbering_rule.read` |  | tự dò: v2 `document` |
| PATCH | `/api/issue-codes` | update issue code | `doc_numbering_rule.write` |  | tự dò: v2 `document` |
| GET | `/api/security-levels` | Danh sách văn thư › Thiết lập › Mức mật / Độ khẩn, có lọc và phân trang. | `security_level.read` | `apply_scope` | tự dò: v2 `document` |
| POST | `/api/security-levels` | Thêm một dòng văn thư › Thiết lập › Mức mật / Độ khẩn; chặn trùng mã, ghi nhật ký. | `security_level.create` |  | tự dò: v2 `document` |
| GET | `/api/security-levels/export/csv` | Xuất văn thư › Thiết lập › Mức mật / Độ khẩn ra tệp CSV theo bộ lọc đang chọn. | `security_level.export` | `apply_scope` |  |
| POST | `/api/security-levels/import/csv` | Nhập văn thư › Thiết lập › Mức mật / Độ khẩn hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `security_level.import` | `scope_condition` |  |
| GET | `/api/security-levels/{oid}` | Xem một dòng văn thư › Thiết lập › Mức mật / Độ khẩn theo id. | `security_level.read` | `get_scoped` | tự dò: v2 `document` |
| PATCH | `/api/security-levels/{oid}` | Sửa một dòng văn thư › Thiết lập › Mức mật / Độ khẩn; chỉ ghi các ô gửi lên, ghi nhật ký. | `security_level.write` | `get_scoped` | tự dò: v2 `document` |
| DELETE | `/api/security-levels/{oid}` | Xóa một dòng văn thư › Thiết lập › Mức mật / Độ khẩn; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `security_level.delete` | `get_scoped` | tự dò: v2 `document` |

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
