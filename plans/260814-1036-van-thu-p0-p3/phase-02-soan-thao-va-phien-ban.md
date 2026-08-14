# PHASE 2 · SOẠN THẢO VÀ PHIÊN BẢN

> [← plan.md](./plan.md) · Nguồn: `01` nhóm C + E + L, `02` mục 6, `04` mục 5, **`05` toàn bộ**
> Ra được: một người soạn được văn bản từ đầu tới cuối, lên được phiên bản 2 mà bản 1 vẫn còn nguyên.

⚠️ **Không có bước xin phép.** Chốt 14/08/2026: bỏ hẳn nhóm B *Yêu cầu văn bản* khỏi bản 1 — ai có quyền `document.create` thì **tạo văn bản trực tiếp**. Xem quyết định 7 ở [`plan.md`](./plan.md) để biết cái gì mất đi và cái gì giữ lại để sau thêm được.

## Tổng quan

| | |
|---|---|
| Ưu tiên | Cao — chặn P3, P4, P5 |
| Trạng thái | ☐ Chưa bắt đầu |
| Mã `01` | C01, C03–C07, C12–C19, D06, E01–E06, E11, L01, L02, L07 (**bỏ: B01–B07 yêu cầu văn bản · C02 tệp mẫu** — quyết định 6 và 7 ở `plan.md`) |
| Migration | M6, M7 |

Duyệt **nội dung văn bản** ở phase này dùng **luồng một bước viết tay tạm thời** — đúng kiểu 5 luồng Thu mua đang có. P3-T17 sẽ thay bằng bộ máy chung. Làm vậy để phase 2 cho người thật bấm thử được ngay.

## Điểm cần biết trước — 7 cái bẫy

1. **`tab_document` chứa 3 loại bản ghi** phân biệt bằng `origin`: 1 nội bộ · 2 pháp luật ngoài · 3 văn bản đến. **Mọi truy vấn danh sách/tìm kiếm/báo cáo phải lọc `origin = 1`**, và chỗ ép việc đó là **hàm dựng truy vấn dùng chung**, không phải từng màn hình tự nhớ (chỗ dễ sai số 12).
2. **Đừng nhầm `status` của văn bản với `status` của phiên bản.** Quy chế lên bản 2.0 thì `tab_document.status` **vẫn là 4 có hiệu lực**, chỉ dòng phiên bản 1.0 chuyển sang 4 bị thay thế. Nhầm chỗ này là cả công ty thấy quy chế lương biến mất (chỗ dễ sai số 7).
3. **Mỗi văn bản chỉ một phiên bản đang mở** — ép bằng cột sinh `open_slot` + `UNIQUE`, không chỉ kiểm trong mã. Hai người bấm cùng lúc thì hai câu kiểm trong mã đều thấy trống (chỗ dễ sai số 8).
4. **Phiên bản đã duyệt là bất biến.** `is_locked` bật rồi thì **không có đường nào tắt**. Sửa = tạo dòng mới.
5. **Quan hệ *trích từ* (10) khác *thuộc về* (6).** Dùng nhầm là mất cả ba ràng buộc: gốc lên bản mới mà bản trích không bị đánh dấu · gốc bãi bỏ mà bản trích còn sống · mức mật bản trích vượt gốc (chỗ dễ sai số 11). *Trích từ* **bắt buộc có `source_version_id`**.
6. `tab_document.doc_type_id`, `company_id`, `owner_employee_id`, `drafter_employee_id` **cho phép rỗng** (vì `origin = 2`), nhưng có `CHECK (origin <> 1 OR ...)` ép lại.
7. Tệp đính kèm **dùng lại `tab_file_link`** với `entity = 'document_version'`, không tạo bảng nối riêng.
8. **Soạn thảo là gõ tay trên web.** Nội dung nằm ở `tab_document_version.content_html`, soạn bằng `shared/ui/rich-text-editor` (tiptap, đã có sẵn phân trang + bảng + thước). **Không có tệp mẫu Word, không có trường nhập động** — bộ trường của văn bản là bộ chung cố định `C01`, khai trong mã. `version.file_id` / `pdf_file_id` vẫn giữ: đó là **đính kèm**, không phải mẫu.

## Danh sách task

### Nền dữ liệu

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P2-T01** | DB | **Migration M6** | `tab_document_request` (14 cột — **tạo rỗng, không có màn hình**, xem P2-T05) · `tab_document` (**~45 cột**, gồm 7 cột clone + 2 cột `origin=2` + 3 cột sổ đi) · `tab_document_version` (18 cột). Kèm đủ: `CHECK (origin<>1 OR ...)`, `UNIQUE(doc_code)`, `UNIQUE(company_id, issue_year, doc_type_id, seq_no)`, `UNIQUE(source_document_id, company_id)`, cột sinh `open_slot` + `uq_one_open_version`. **Không tách M6 làm hai** — các cột gom phải có ngay từ lúc tạo bảng |
| **P2-T02** | DB | **Migration M7** | `tab_document_link` + `UNIQUE(source_document_id, target_document_id, relation)` + `CHECK (source_document_id <> target_document_id)` + index cả hai chiều |
| **P2-T03** | BE | **Chỉ mục** | `(origin, company_id, doc_type_id, status)` · `(origin, status, effective_date)` · `(doc_code)` unique, `(issue_number)`, `(legacy_code)` · `(company_id, issue_year, doc_type_id, seq_no)` · `(source_document_id, clone_status)` · `tab_document_version(document_id, version_no)` |
| **P2-T04** | BE | **Hàm dựng truy vấn dùng chung + bài kiểm `origin`** | `modules/document/query.py::documents_query(db, origin=1)` — mọi controller đi qua đây. Test tự động: tạo bản ghi `origin = 2`, gọi **hết** các endpoint danh sách/tìm kiếm/thống kê, **không endpoint nào được trả về nó** |

### ~~Yêu cầu văn bản (nhóm B)~~ — đã cắt khỏi bản 1

5 task cũ (P2-T05 … P2-T09) **bỏ hết**. Thay bằng đúng một việc, gộp vào P2-T10:

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P2-T05** | ∞ | **Tạo văn bản trực tiếp** | Nút "Tạo văn bản" trên danh sách → thẳng vào form soạn, chỉ gác bằng `require("document", "create")` + `apply_scope`. **Giữ lại hai thứ để sau thêm bước xin phép mà không phải `ALTER` bảng nóng:** bảng `tab_document_request` vẫn tạo ở M6 (rỗng, không màn hình, không router) · hai cột `tab_document.document_request_id` và `tab_document_version.created_from_request_id` vẫn khai, luôn `NULL`. Cột `doc_type.needs_request` giữ trong DB, mặc định `FALSE`, **ẩn khỏi form loại văn bản** (sửa P1-T10). **Vẫn giữ B05**: lúc chọn loại + phòng ban, form hiện danh sách văn bản cùng loại cùng phòng đang hiệu lực để người soạn tự thấy đã có hay chưa — đây là thứ rẻ nhất còn lại chống việc đẻ trùng quy trình |

### Soạn thảo và phiên bản (nhóm C)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P2-T10** | BE | **Service văn bản + phiên bản** | CRUD `tab_document` (bộ trường chung C01) + `tab_document_version`. Cấp số theo `doc_type.number_when` (1 lúc tạo nháp · 2 lúc được duyệt, **mặc định 2**), gọi `next_number()` **trong cùng transaction** |
| **P2-T11** | BE | **Bất biến hóa phiên bản** | `is_locked = true` khi duyệt, **không có API nào tắt**. Mọi `PUT` lên version đã khóa → 409. `change_summary` + `change_reason` **bắt buộc từ phiên bản thứ hai**. `sha256` nội dung tính lúc khóa |
| **P2-T12** | BE | **Mở phiên bản mới** | `POST /documents/{id}/versions` → kiểm `open_slot` (bắt `IntegrityError` trả câu "bản nháp 2.0 đang do ông X giữ"), chép nội dung bản hiện tại, bắt `change_kind` (1 sửa lớn · 2 sửa nhỏ), set `prev_version_id`, `requires_reconfirm` mặc định theo `change_kind`. **Không đụng `tab_document.status`** |
| **P2-T13** | BE | **Ngày hiệu lực của phiên bản** | `effective_from` riêng từng phiên bản, khác ngày được duyệt. Tác vụ định kỳ chuyển `current_version_id` đúng ngày; **đổi trong một giao dịch**, không có khoảng trống (C16, C17) |
| **P2-T14** | FE | **Form văn bản dựng lại theo C01** | `components/document-record-form.tsx` + `types/document-record.ts`: đổi trục sang `doc_type_id` + `company_id` (pháp nhân **ban hành**) + `owner_employee_id` / `drafter_employee_id` / `signer_employee_id`, `secrecy_level`, `urgency`, `keywords`, `effective_date`, `legacy_code`. **Bộ trường cố định, khai trong mã.** `direction`/`book_no`/`partner_id`/`processing_*` **gỡ khỏi form chính** (thuộc sổ đến, phase 9) |
| **P2-T14b** | FE | **Gỡ bộ trường nhập động khỏi module văn bản** | Xóa `components/dynamic-field-catalog.tsx`, `components/document-dynamic-fields.tsx`, `pages/dynamic-field-detail-page.tsx`, `types/dynamic-field.ts`, tab `fields` trong `document-settings-page.tsx`, 2 route `fieldNew`/`fieldDetail` và `field_values` trên `DocumentRecord`. Danh mục "Thiết lập văn bản" còn 3 tab: loại văn bản · mức mật/khẩn · đối tác. **Lý do ghi vào commit** để sau này ai muốn khôi phục thì biết vì sao bỏ |
| **P2-T15** | FE | **Tab phiên bản trên trang chi tiết** | Danh sách phiên bản + trạng thái + `change_kind`; bản đã duyệt mở ra **chỉ đọc**; nút "mở phiên bản mới" (dialog bắt lý do + phân loại sửa); băng cảnh báo trên bản cũ *"Đã bị thay thế bởi bản 2.0 ngày …"* kèm nút sang bản mới — **bản cũ không xóa, không ẩn** (C18) |
| **P2-T16** | FE | **Trình soạn nội dung + đính kèm + số hiệu cũ** | Gắn `rich-text-editor` vào form văn bản, lưu vào `content_html`, tự động lưu bản nháp (tái dùng `use-document-autosave.ts`); phiên bản đã khóa thì editor ở chế độ **chỉ đọc**. Đính kèm tệp qua đường riêng tư P0-T04, hiện `sha256` (C06). Ô `legacy_code` + tìm kiếm chấp nhận số cũ (C12) |

### Quan hệ cha–con và bản trích (nhóm E)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P2-T17** | BE | **Service quan hệ + cấm vòng lặp** | Tạo/xóa `tab_document_link`. **Kiểm chu trình cả chuỗi dài**, không chỉ hai bước. `is_system = true` thì API xóa từ chối. Chặn gửi duyệt khi thiếu quan hệ `is_required` — báo rõ **thiếu quan hệ nào tới loại nào** (E04, E05) |
| **P2-T18** | BE | **Bản trích nội bộ + quan hệ *trích từ*** | `POST /documents/{id}/extracts`: tạo văn bản mới **cùng loại gốc**, mức mật **≤ gốc** (chặn nếu cao hơn), tự tạo link `relation = 10` với `is_system = true` và **bắt buộc `source_version_id`**. Gốc lên phiên bản → mọi bản trích chuyển "cần rà lại"; gốc bãi bỏ → bản trích **hết hiệu lực theo**. Cả hai chạy tự động, không cấu hình tắt được |
| **P2-T19** | FE | **Khối quan hệ trên form + cây tài liệu** | Chọn loại → **tự hiện ô** theo `tab_doc_type_link_rule`, danh sách chọn lọc đúng `target_type_id` và chỉ văn bản `status = 4`. Trang chi tiết có **cây tài liệu** (E06): quy trình → hướng dẫn → biểu mẫu, kèm trạng thái + phiên bản |
| **P2-T20** | FE | **Màn soạn bản trích** | Mở bản gốc trong `rich-text-editor`, chọn phần nội dung → sinh nháp mới; ô mức mật giới hạn `≤` mức gốc; hiện rõ "trích từ phiên bản 1.2 của DEGO-QC-012" |

### AI (nhóm L)

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P2-T21** | ∞ | **OCR ảnh → bản nháp** | BE: endpoint nhận ảnh → OCR → trả text, **chỉ ghi vào bản nháp**, không có đường nào cho AI duyệt/ban hành/đổi trạng thái. FE: ảnh gốc đặt **cạnh** bản nháp để đối chiếu (L02). Cờ `AI_ENABLED=false` → mọi nút AI biến mất, không màn nào lỗi (L07) |

## Tệp đụng tới

**Tạo BE:** `modules/document/{model,request_model,version_model,link_model,schema,service,version_service,link_service,extract_service,query,controller}.py` (`request_model.py` chỉ khai bảng rỗng, **không có service/controller**) · `migrations/versions/<M6,M7>.py` · `test/backend/test_document_origin_filter.py` · `test_document_version.py` · `test_document_link_cycle.py` · `test_document_extract.py`
**Tạo FE:** `pages/document-extract-page.tsx` · `components/document-version-tab.tsx` · `document-version-dialog.tsx` · `document-link-fields.tsx` · `document-tree.tsx` · `document-ocr-panel.tsx` · `hooks/use-document-versions.ts` · `use-document-links.ts` · `api/document-api.ts`
**Sửa FE:** `components/document-record-form.tsx` · `types/document-record.ts` · `pages/document-{list,detail,create,settings}-page.tsx` · `routes.tsx` · `app-routes.ts`
**Xóa FE:** `store/document-record-store.ts` (sau khi nối API) · `components/dynamic-field-catalog.tsx` · `components/document-dynamic-fields.tsx` · `pages/dynamic-field-detail-page.tsx` · `types/dynamic-field.ts` (P2-T14b)

## Todo

- [ ] P2-T01 · M6: 3 bảng chính + đủ CHECK/UNIQUE + `open_slot`
- [ ] P2-T02 · M7: `tab_document_link`
- [ ] P2-T03 · Chỉ mục theo `04` mục 10
- [ ] P2-T04 · Hàm truy vấn dùng chung + **bài kiểm `origin`**
- [ ] P2-T05 · Tạo văn bản trực tiếp + gợi ý văn bản đã có (B05)
- [ ] P2-T10 · Service văn bản + cấp số theo `number_when`
- [ ] P2-T11 · Bất biến hóa phiên bản, `is_locked` một chiều
- [ ] P2-T12 · Mở phiên bản mới, bắt `open_slot`
- [ ] P2-T13 · Ngày hiệu lực riêng của phiên bản
- [ ] P2-T14 · FE form văn bản theo C01
- [ ] P2-T14b · Gỡ bộ trường nhập động khỏi module văn bản
- [ ] P2-T15 · FE tab phiên bản + băng cảnh báo
- [ ] P2-T16 · FE trình soạn nội dung, đính kèm, số hiệu cũ
- [ ] P2-T17 · Quan hệ + cấm vòng lặp + chặn thiếu quan hệ bắt buộc
- [ ] P2-T18 · Bản trích + quan hệ *trích từ* + 3 ràng buộc
- [ ] P2-T19 · FE khối quan hệ + cây tài liệu
- [ ] P2-T20 · FE màn soạn bản trích
- [ ] P2-T21 · OCR ảnh → nháp, cờ tắt AI

## Nghiệm thu

Đi hết một đường: bấm tạo văn bản → chọn loại → gõ nội dung trên web (hoặc chụp ảnh văn bản giấy cho AI đọc rồi sửa lại) → đính kèm tệp → khai văn bản cha → gửi duyệt → tạo phiên bản 2 với lý do sửa. **Phiên bản 1 vẫn còn nguyên, không bị đè.**

| Bài kiểm | Kết quả phải là |
|---|---|
| Khai một Hướng dẫn công việc không chọn Quy trình nó hướng dẫn | **Không gửi duyệt được**, báo rõ thiếu gì |
| Hai người cùng bấm "mở phiên bản mới" | **Chỉ một người mở được**, người kia thấy ai đang giữ bản nháp |
| Bản 2.0 đang duyệt, mở văn bản ra xem | **Vẫn thấy bản 1.0, vẫn ghi là có hiệu lực** |
| Tạo bản trích mức mật **cao hơn** gốc | Bị chặn |
| Bản gốc lên 2.0 | Mọi bản trích **tự chuyển "cần rà lại"**, không ai bấm gì |
| Bãi bỏ bản gốc | Bản trích **hết hiệu lực theo** |
| Tạo bản ghi `origin = 2`, gọi hết endpoint danh sách | **Không endpoint nào trả về nó** |
| Sửa một phiên bản đã duyệt qua API | 409, kể cả gọi thẳng không qua UI |
| A hướng dẫn B, thử cho B hướng dẫn A | Bị chặn ngay lúc lưu |

**Điều kiện chuyển phase:** đường đi trên chạy hết trên dev, ≥3 người ngoài đội phần mềm bấm thử.

## Rủi ro

| Rủi ro | Mức | Giảm bằng |
|---|---|---|
| Quên lọc `origin = 1` ở một endpoint | **Cao** | P2-T04 — bài kiểm tự động gọi *hết* endpoint, không phải review bằng mắt |
| Nhầm status văn bản với status phiên bản | Cao | Test riêng: lên 2.0 xong, văn bản vẫn nằm trong danh sách `status = 4` |
| `tab_document` 45 cột khó đọc | Trung bình | Chia model thành mixin theo nhóm cột (clone / legal / register), comment tiếng Việt từng nhóm |
| FE đổi trục `DocumentRecord` làm hỏng màn đã dựng | Trung bình | Đổi type trước, để TypeScript chỉ ra hết chỗ hỏng; `npm run typecheck` phải sạch trước khi commit |
| OCR tiếng Việt chỉ đúng 85–95% | Đã biết | Nói rõ trong UI: AI để **đỡ phải gõ lại**, không phải để tin. Luôn kèm ảnh gốc |

## Bảo mật

- `secrecy_level` đã có trên bảng từ phase này nhưng **chưa được thực thi** — lớp kiểm mức mật là P5. Trong lúc chưa có: **không đưa văn bản mật thật vào dev**.
- Phiên bản đã duyệt phải khóa ở **tầng dịch vụ**, không phải ẩn nút. Bài kiểm gọi thẳng API.
- Tệp đính kèm đi đường riêng tư của P0-T04; mọi lượt xem/tải ghi `tab_file_access_log`.

## Tiếp theo

[Phase 3 · Bộ máy phê duyệt dùng chung](./phase-03-bo-may-phe-duyet.md).
