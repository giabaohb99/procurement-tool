# Phase 06 — CR-628b (bước A): gộp GIAO DIỆN mẫu HĐLĐ vào «Thư viện văn bản mẫu»

**Sub-scope:** «CR-628b gộp mẫu HĐLĐ vào Thư viện văn bản mẫu» · **Ưu tiên:** P2 · **Trạng thái:** done · **Effort:** 4h
**Phụ thuộc:** CR-610 đã commit (`labor-contract-template-row-actions.tsx` đang CHƯA commit trong cây làm việc — không được ghi đè/mất). Độc lập với 01–05 (không chung tệp với phase 04).
**Sở hữu tệp:** xem «Tệp». Backend **không đổi**.

## Kết luận nghiên cứu — vì sao CHỈ gộp giao diện (bước A), không gộp bảng
`tab_document_template` (`document/template_model.py`) **không** đỡ được mẫu HĐLĐ:
| Khía cạnh | Thư viện văn bản mẫu (`doc_template`) | Mẫu HĐLĐ (`labor_contract_template`) |
|---|---|---|
| Nội dung | `content_html` (HTML soạn thảo, chép vào phiên bản 1.0) | tệp `.docx` (`file_id` → `tab_file`), biến `{{ }}` + `placeholders` JSON, render `docxtpl` |
| Khóa phân loại | `doc_type_id`, unique (`doc_type_id`,`name`) | `company_id` + `contract_type`, unique (`company_id`,`name`) |
| Phạm vi dữ liệu | không có (seed cấp `read` cho MỌI vai trò để đổ ô chọn) | `SCOPE_FIELDS` theo `company` |
| Tham chiếu ngược | không ai trỏ về | `tab_labor_contract.template_id` (FK mềm), `generate_service._pick_template`, `serializer` (tên mẫu), chặn xóa khi đang dùng |
| Màn phụ | trình soạn văn bản | «Soạn nội dung mẫu trên web» (CR-606, `template_web_editor.py`), «⋯» (CR-610), danh sách biến |

Gộp bảng = thêm 6 cột + đổi unique + tách quyền theo dòng trong controller `doc_template` + đổi id hàng loạt `template_id` của HĐ + sửa engine/editor/serializer + lọc mẫu dạng tệp khỏi ô chọn khi soạn văn bản. Rủi ro cao (rò mẫu HĐLĐ cho mọi vai trò qua `/api/document-templates`, gãy HĐ đã sinh), mà người dùng **không thấy khác gì** so với bước A. ⇒ **Làm bước A; bước B tách riêng, đề xuất KHÔNG làm** (phase 07).

## Yêu cầu (bước A)
- URL mới: `/document/settings?tab=templates&kind=labor-contract` — chỉ hiện mẫu HĐLĐ (bảng, lọc, nút «Tải lên mẫu», «Danh sách biến», «⋯» giữ nguyên hành vi, gọi đúng `/api/labor-contract-templates`).
- Menu HR «Mẫu hợp đồng» + link trong hộp «Lập hợp đồng» (`labor-contract-form-dialog.tsx:76`) và «Sinh tệp» (`labor-contract-generate-dialog.tsx:69`) → URL mới.
- `/hr/labor-contract-templates` → `<Navigate replace>` sang URL mới. Trình soạn `/hr/labor-contract-templates/:id/edit` **giữ đường** (link cũ, CR-606), «Về danh sách» trỏ URL mới.
- Quyền = quyền HIỆN CÓ `labor_contract_template` (backend đã gác `/api/labor-contract-templates` bằng khóa này + phạm vi `company`, không đổi).
  - HR có `labor_contract_template` mà KHÔNG quản lý danh mục Văn bản nào ⇒ vào được trang, **chỉ thấy** mục mẫu HĐLĐ (ẩn 4 tab Văn bản — chúng vốn `read` cho mọi vai trò).
  - Văn thư không có `labor_contract_template.read` ⇒ không thấy mục HĐLĐ; `kind=labor-contract` trên URL bị bỏ qua (về thư viện văn bản mẫu thường).
  - Người có cả hai ⇒ tab «Thư viện văn bản mẫu» có công tắc 2 mục «Văn bản mẫu | Mẫu hợp đồng lao động».

## Kiến trúc
```
Document nav «Thiết lập văn bản» entities += 'labor_contract_template' (manage)  ← cửa route /document/settings
HR nav «Mẫu hợp đồng»  path = appRoutes.document.laborContractTemplates, crossModule: true, entity lct
HR nav (hidden)        path = /hr/labor-contract-templates, entity lct  ← giữ hàng rào cho route trình soạn (gác điều hướng mặc định MỞ)
DocumentSettingsPage
  docManager = ['doc_type','doc_template','security_level','external_party'].some(canManageEntity)
  canLct     = can('labor_contract_template','read')
  !docManager && canLct  → chỉ 1 tab «Thư viện văn bản mẫu», kind ép = labor-contract
  tab templates + kind=labor-contract + canLct → <LaborContractTemplateCatalog/> ; còn lại → <DocumentTemplateCatalog/>
```
- `LaborContractTemplateCatalog` (hr/components) = thân của `labor-contract-template-list-page.tsx` bỏ `PageContainer/PageHeader`; nút «Danh sách biến» / «Tải lên mẫu» dời vào `toolbar` (tab này không dùng `newPath`). Trang list cũ **xóa**.
- Import chéo `document → hr/components` chấp nhận được (đã có tiền lệ `document-template-catalog.tsx` import `@/modules/hr/utils/list-sticky`); KHÔNG đưa vào `shared/`.
- `document-settings-page.tsx` đang 198 dòng ⇒ tách `TABS` + luật chọn tab sang `document/config/document-settings-tabs.ts` (hàm thuần, dễ test).

## Tệp
- Sửa: `frontend-v2/src/shared/constants/app-routes.ts` (+`document.laborContractTemplates`; giữ `hr.laborContractTemplates` cho redirect/hàng rào)
- Sửa: `frontend-v2/src/modules/document/routes.tsx` (entities +`labor_contract_template`)
- Sửa: `frontend-v2/src/modules/document/pages/document-settings-page.tsx` (+test)
- Tạo: `frontend-v2/src/modules/document/config/document-settings-tabs.ts` (+`.test.ts`)
- Sửa: `frontend-v2/src/modules/hr/routes.tsx` (mục menu crossModule, mục ẩn, route list → `Navigate`)
- Tạo: `frontend-v2/src/modules/hr/components/labor-contract-template-catalog.tsx` (+test — chuyển từ `labor-contract-template-list-page.test.tsx`)
- Xóa: `frontend-v2/src/modules/hr/pages/labor-contract-template-list-page.tsx` + `.test.tsx`
- Sửa: `hr/components/labor-contract-form-dialog.tsx`, `hr/components/labor-contract-generate-dialog.tsx`, `hr/pages/labor-contract-template-editor-page.tsx` (link/«Về danh sách»)
- Không đụng: `hr/config/labor-contract-template-columns.tsx`, `hr/components/labor-contract-template-row-actions.tsx` (CR-610), hook/api HĐLĐ, toàn bộ backend.

## Các bước
1. Chờ CR-610 commit; `git status` sạch phần `labor-contract-template-*`.
2. Tách `document-settings-tabs.ts` (luật `docManager`/`canLct`/`kind`) + test thuần.
3. Tạo `LaborContractTemplateCatalog` từ trang list; chuyển test.
4. Cắm vào trang Thiết lập; công tắc 2 mục chỉ khi có cả hai quyền.
5. Route/menu/redirect/link; mục ẩn giữ hàng rào trình soạn.
6. Ba cổng: `typecheck`, `lint`, `vitest run src/modules/document src/modules/hr src/app/router`.

## Test (vitest)
1. `document-settings-tabs`: HR-only ⇒ 1 tab, kind = labor-contract; văn thư ⇒ 4 tab, kind bị bỏ qua; cả hai ⇒ 4 tab + kind giữ.
2. Trang Thiết lập: HR-only mở `?tab=types` ⇒ vẫn chỉ thấy mẫu HĐLĐ; văn thư mở `?tab=templates&kind=labor-contract` ⇒ thấy thư viện văn bản mẫu, KHÔNG gọi `/api/labor-contract-templates`.
3. `module-visibility`: «Thiết lập văn bản» hiện với người chỉ có `labor_contract_template` (create/write/delete); `canAccessRoute('/document/settings')` true; `canAccessRoute('/hr/labor-contract-templates/5/edit')` false khi thiếu khóa.
4. `module-registry.test.ts` xanh với mục crossModule có query (`?tab=…`) — nếu bộ test tách path theo `?` sai thì sửa test, không bỏ qua.
5. Redirect `/hr/labor-contract-templates` ⇒ URL mới.
6. Hộp «Lập hợp đồng» / «Sinh tệp» khi chưa có mẫu: link trỏ URL mới (mở rộng `labor-contract-form-dialog.test.tsx`).
7. `LaborContractTemplateCatalog` giữ nguyên các ca của test trang list cũ (lọc, nút theo quyền, «⋯»).

Backend: không đổi; hồi quy `pytest test/backend/test_hdld_mau_hop_dong_api.py -q` (đã có ca văn thư thiếu quyền ⇒ 403).

## Tiêu chí xong
- HR (vai trò `hr_profile`) bấm «Mẫu hợp đồng» ⇒ `/document/settings?tab=templates&kind=labor-contract`, chỉ thấy mẫu HĐLĐ, tải lên / sửa thông tin / thay tệp / soạn trên web / ngừng dùng / xóa chạy như cũ.
- Văn thư (quản lý `doc_template`, không có `labor_contract_template`) không thấy mẫu HĐLĐ ở bất kỳ đâu; gõ URL `kind=labor-contract` ⇒ thư viện thường.
- Link cũ `/hr/labor-contract-templates` và trình soạn cũ vẫn mở được.
- Ba cổng FE xanh, không thêm cảnh báo lint.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Đè mất thay đổi chưa commit của CR-610 | TB × Cao | Bước 1; không sửa 2 tệp CR-610 |
| Bỏ mục menu cũ ⇒ route trình soạn mất hàng rào (gác điều hướng mặc định MỞ) | TB × TB | Mục `hidden` giữ path cũ + test 3 |
| HR giờ thấy thẻ phân hệ Văn bản mở (vì «Thiết lập văn bản») | Cao × Thấp | Chấp nhận; trong đó chỉ có mục HĐLĐ + mục công khai sẵn có — xem câu hỏi mở |
| Người chỉ có `labor_contract_template.read` (không create/write/delete) mất lối vào (cửa `manage`) | Thấp × Thấp | Seed hiện không có vai trò như vậy; câu hỏi mở — nếu cần thì nới `module-visibility` (lớp dùng chung) ở CR riêng |
| Hai bảng có `storageKey` khác nhau trên cùng trang | Thấp × Thấp | Giữ `hr.labor-contract-templates` để không mất bố cục cột người dùng đã chỉnh |

## Rollback
Revert 1 commit FE. Không có dữ liệu/migration.
