# Đánh giá tiến độ Phase 1–4 (Văn thư) trên `frontend-v2`

- Ngày: 15/08/2026 · Nhánh: `erp-v2`
- Nguồn yêu cầu: `quan-ly-van-thu-bo-tai-lieu.pdf`, tài liệu **02 · Lộ trình phát triển**, mục 5–8 (trang PDF 47–51)
- Phạm vi chấm: `frontend-v2/src/modules/document` + phần phụ thuộc ở `modules/hr` (mã số hiệu pháp nhân/phòng ban)
- Backend chỉ nhắc để nói rõ tính năng có chạy thật hay không; **không tính vào %**

## Kết luận một dòng

| Phase | Nội dung | % làm được (FE v2) |
|---|---|---|
| 1 | Danh mục và số hiệu | **~90%** |
| 2 | Yêu cầu, soạn thảo, phiên bản | **~45%** |
| 3 | Bộ máy phê duyệt dùng chung | **~5%** |
| 4 | Ban hành, phạm vi, clone | **~6%** |
| **Tổng 4 phase** | trọng số theo khối lượng (15/30/35/20) | **≈ 30%** |

Đọc nhanh: **Phase 1 gần xong, Phase 2 xong đúng phần lõi (soạn thảo + phiên bản), Phase 3 và 4 chưa bắt đầu.**
Con số 30% thấp chủ yếu vì Phase 3 là phase nặng nhất (20 tính năng) và hoàn toàn chưa động tới.

---

## 1. Phase 1 · Danh mục và số hiệu — ~90%

| Việc (theo PDF) | Mã | FE v2 | Bằng chứng |
|---|---|---|---|
| Bảng loại văn bản, nhập 32 loại | A01, A02 | ✅ | `document-type-catalog.tsx`, `document-type-form.tsx`, `types/document-type.ts`; seed `backend/app/seed_data/document_phase1.py` |
| Loại thứ 33 Trích lục (`id_scheme=2`, `needs_decision=FALSE`) | C20 | ✅ | `TRICH_LUC_DOC_TYPE` trong seed, hiện như loại thường trên UI |
| Mã số hiệu 13 pháp nhân + phòng ban | A04, A05 | ✅ | `modules/hr/.../company-form-dialog.tsx`, `department-form-dialog.tsx` (`issue_code`) |
| Bảng nối phòng ban ↔ pháp nhân, trưởng phòng theo từng pháp nhân | A06 | ✅ | `department-company-card.tsx` (`issue_code_override`, `manager_employee_id` theo dòng) |
| Bộ cấp số chống trùng, hai kiểu định danh | D01–D04 | ✅ | `document-numbering-rules-page.tsx`, `document-number-preview.tsx`, `NUMBERING_TOKENS`; BE khóa dòng `with_for_update()` |
| Văn bản hủy vẫn giữ số, cấm đổi mã sau khi cấp số | D05, D07 | 🟡 | FE có nút Bãi bỏ + trạng thái `revoked`; chặn đổi mã nằm ở BE `issue_code_guard.py`, FE chỉ hiện lỗi trả về |
| Danh mục đối tác, cơ quan gửi nhận | A07 | ✅ | `document-partner-catalog.tsx`, `document-partner-detail-page.tsx` |
| Tạo trước bảng phase sau: sổ đi, sổ đến | S01, S02 | ✅ (vượt yêu cầu) | Có cả UI: `document-book-page.tsx`, `book-counter-card.tsx`, `BOOK_KIND` 1/2/3 |
| Tạo trước bảng: xác nhận đã đọc | J06 | ❌ | Không có bảng, không có màn |
| Tạo trước bảng: văn bản pháp luật | A09 | ❌ | Chỉ có enum `origin = 2`, ghi chú "màn hình chỉ thấy 1" |

Làm thêm ngoài yêu cầu phase 1: **quyền theo sổ** (thành viên sổ đọc được, quản lý sổ sửa được) và **quy tắc đánh số theo mẫu token** — thứ tài liệu xếp ở phase sau.

Thiếu để đóng phase: hai bảng dựng trước (J06, A09) và bài kiểm 100 kết nối (việc của BE/test, không phải FE).

---

## 2. Phase 2 · Yêu cầu, soạn thảo, phiên bản — ~45%

| Việc | Mã | FE v2 | Ghi chú |
|---|---|---|---|
| Yêu cầu văn bản: ba loại, lý do bắt buộc | B01 | ❌ | Bỏ hẳn ở bản 1 — `needs_request` luôn `false`, không hiện trên form |
| Gợi ý văn bản đã có | B05 | ✅ | `document-suggestion-list.tsx` + `useDocumentSuggestions` |
| Chặn soạn khi chưa có yêu cầu duyệt; cấu hình loại bỏ qua | B03, B06 | ❌ | Trường có sẵn trong DB, chưa có màn |
| Sinh bản nháp từ yêu cầu, theo dõi yêu cầu | B04, B07 | ❌ | `tab_document_request` có bảng, FE không có màn nào |
| Bản ghi văn bản, bộ trường chung, tệp mẫu theo loại | C01, C02 | ✅ | `document-record-form.tsx`, `document-template-catalog.tsx` |
| Phiên bản bất biến, lý do sửa bắt buộc, khóa sửa sau duyệt | C04, C05, C07 | ✅ | `document-version-tab.tsx`, `is_locked`, `content_sha256` |
| Sửa văn bản đã ban hành (mở bản mới, phân loại sửa lớn/nhỏ, bản cũ vẫn hiệu lực, ngày hiệu lực riêng, băng cảnh báo) | C13–C18 | 🟡 ~90% | `document-version-dialog.tsx`, `document-version-banner.tsx`; C14 "một văn bản một bản nháp" mới có dữ liệu (`created_by_name`), chưa thấy màn báo "ai đang giữ bản nháp" |
| Tệp đính kèm đường riêng tư, mã băm toàn vẹn | C03, C06 | 🟡 ~50% | Đính kèm gắn theo **phiên bản** ✅, nhưng vẫn dùng `/api/attachments` **link công khai** — comment trong `document-attachment-list.tsx` tự ghi "chưa làm, đừng đưa văn bản mật thật vào" |
| Ghi số hiệu cũ của văn bản giấy | C12 | ✅ | `legacy_code`, tìm kiếm chấp nhận |
| Quan hệ cha con: bảng quy tắc, form tự hiện ô, chặn thiếu, cấm vòng lặp, cây tài liệu | E01–E06 | ❌ | 0 tệp nhắc tới quan hệ; không có bảng `tab_document_relation` |
| Bản trích nội bộ | C19 | ❌ | — |
| Quan hệ "trích từ" + cột ghi trích từ phiên bản nào | E11 | ❌ | — |
| Chuyển ảnh thành văn bản, đặt ảnh gốc cạnh nháp, cờ tắt AI | L01, L02, L07 | 🟡 ~25% | Có nhập **.doc/.docx/.pdf/.md/.html** + `document-import-trace-dialog.tsx` (đối chiếu nguồn, nhảy tới trang PDF) — tinh thần giống L02 nhưng **không phải ảnh/OCR**; không có cờ tắt AI |
| Luồng duyệt yêu cầu tạm một bước | — | 🟡 50% | Có `submit/approve/reject` nhưng đặt trên **văn bản**, không phải trên yêu cầu |

Đường đi kiểm thử của phase 2 (xin phép → duyệt → soạn → chụp ảnh cho AI đọc → đính kèm → khai văn bản cha → tạo phiên bản 2) hiện **đứt ở 3 chỗ**: xin phép, ảnh/AI, văn bản cha.

Năm phép thử phụ: 1/5 chạy được (bản 2.0 đang duyệt vẫn thấy bản 1.0 có hiệu lực). Bốn phép còn lại đều thuộc phần chưa làm.

---

## 3. Phase 3 · Bộ máy phê duyệt dùng chung — ~5%

Chưa bắt đầu. Không có bảng luồng/bước/phiên chạy/việc/hành động, không có màn khai luồng, không có "Việc của tôi".

Thứ duy nhất tồn tại là **3 nút cứng** `submit → approve/reject` trên trang chi tiết văn bản (`document-detail-page.tsx:265`), gác bằng `PermissionGate entity="document" action="approve"` — đúng bằng thứ tài liệu gọi là "luồng một bước viết tay tạm thời của phase 2", nên gần như không tính vào phase 3.

Chưa có: I01–I26 (mô hình luồng, phiên bản luồng, 6 cách chọn người duyệt, rẽ nhánh, nhiều người một bước, trùng thao tác thì bỏ qua, ủy quyền, chặn tự duyệt, trả lại/rút lại, bản sao, hạn duyệt và nhắc, bản in dấu vết, bàn giao hàng loạt, cờ bật tắt theo loại chứng từ).

---

## 4. Phase 4 · Ban hành, phạm vi, clone — ~6%

| Việc | Mã | FE v2 |
|---|---|---|
| Vòng đời văn bản 8 trạng thái | J01 | ✅ `DOCUMENT_STATUS`, `helpers/document-status.ts` |
| Ban hành (cấp số, đóng phiên bản) | J04 | 🟡 có `approve → effective` + cấp số, chưa có màn ban hành riêng |
| Ký điện tử nội bộ, ghi rõ loại chữ ký | J02, J03 | ❌ chỉ có ô chọn `signer_employee_id`, không có bản ghi ký |
| Phạm vi ba kiểu, bao gồm/loại trừ, bắt buộc kèm pháp nhân, áp cho đơn vị con | F01–F04 | ❌ |
| Màn "văn bản áp dụng cho tôi", thông báo theo phạm vi | F05, J05 | ❌ |
| Clone xuống pháp nhân con (nháp, liên kết ngược, số hiệu riêng) | F06–F08 | ❌ (0 tệp nhắc "clone") |
| Gửi thư kèm nháp, bảng theo dõi clone | F09, F10 | ❌ |
| Bản gốc lên phiên bản → con cần rà lại | F11 | 🟡 có cờ `requires_reconfirm` trên phiên bản, nhưng không có bản clone để áp |
| Màn chọn cơ chế lúc ban hành (phạm vi hay clone) | F13 | ❌ |
| Cảnh báo tác động khi sửa cha, xử lý khi bãi bỏ cha | E07, E08 | ❌ (phụ thuộc E01–E06 chưa làm) |
| Nhãn "đã bị sửa đổi" + tác động thay thế/bãi bỏ | J10 | ❌ |
| Quyết định ban hành kiểm ở mức phiên bản | J11 | 🟡 chỉ có cờ `needs_decision` trên loại, chưa có kiểm |

Sáu bài kiểm chuyển phase 4: **0/6** chạy được.

---

## 5. Nhìn theo cách khác — chỗ đã làm nhiều hơn tài liệu đòi

Không phải cứ theo thứ tự phase mà đi. Những thứ này thuộc phase sau nhưng đã có trên FE v2:

- **Quyền trên từng văn bản** (`document-access-*.tsx`, 5 tệp) — G05/G06/G20/G24 của **phase 5**: chia đích danh, cấm thắng cho phép, thu hồi giữ dấu vết. Làm khá kỹ.
- **Sổ văn bản đầy đủ UI** (đi/đến/nội bộ, bộ đếm theo năm, thành viên sổ) — tài liệu chỉ yêu cầu "tạo bảng, chưa màn hình" ở phase 1.
- **Quy tắc đánh số theo mẫu token** (`{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}`) — chi tiết hơn D01–D04.
- **Nhập .docx/.pdf giữ cấu trúc + báo cáo truy vết chuyển đổi** — không có trong danh sách tính năng nào.
- **Mức mật / độ khẩn khai cứng trong mã** (`security-level.ts`) — quyết định đúng, chặn trước rủi ro G03.

Đổi lại, **ba thứ nền của phase 2 bị bỏ trắng**: quan hệ cha–con (E01–E06), bản trích (C19/E11), yêu cầu văn bản (B01–B07).

---

## 6. Rủi ro đáng chú ý

1. **Đính kèm vẫn đi link công khai.** Chính comment trong `document-attachment-list.tsx` ghi rõ. Phase 0 (N02/N03/H01) chưa xong mà FE đã có ô chọn mức "Tuyệt mật" — người dùng thật rất dễ hiểu nhầm là đã bảo mật.
2. **Không có test nào cho phân hệ Văn thư.** `find modules/document -name "*.test.*"` → 0 tệp, trong khi cổng `npm run check` bắt buộc Vitest xanh. ~9.900 dòng code không có lưới an toàn.
3. **Bỏ bước yêu cầu (B01–B07) là quyết định đã thực thi trong mã** (`needs_request` luôn `false`) nhưng lộ trình vẫn xếp nó là việc của phase 2. Nếu sau này bật lại thì phải sửa cả form, cả luồng duyệt.
4. **Phase 4 phụ thuộc phase 3.** Với tiến độ hiện tại, mọi thứ liên quan ban hành/phạm vi/clone còn cách khá xa; đừng hứa mốc phase 4 trước khi bộ máy duyệt có mô hình dữ liệu.

## 7. Việc nên làm tiếp, theo thứ tự

1. Đóng nốt phase 1: dựng 2 bảng còn thiếu (xác nhận đã đọc J06, văn bản pháp luật A09) — chỉ bảng, chưa màn.
2. Quan hệ cha–con E01–E06 — đây là thứ chặn E07/E08 của phase 4 và là phần lõi phase 2 còn trống.
3. Viết test cho phần đã có (form văn bản, phiên bản, quyền theo văn bản) trước khi code thêm.
4. Vá đường tải tệp riêng tư (phase 0) trước khi cho người thật nhập văn bản mật.
5. Khai thử 8 luồng ra giấy bằng mô hình dữ liệu định làm — đúng lời khuyên trong PDF trang 50 — trước khi viết dòng mã đầu tiên của phase 3.

---

## Câu chưa có lời đáp

1. Bước "yêu cầu văn bản" (B01–B07) bỏ hẳn hay chỉ hoãn? Nếu bỏ hẳn thì phase 2 nên tính lại mẫu số, % thật sẽ cao hơn (~55%).
2. L01 "chuyển ảnh thành văn bản" có còn trong bản 1 không, hay phần nhập .docx/.pdf đã được coi là thay thế?
3. Câu B3 (mấy mức mật, ai được cấp mức cao) đã chốt chưa — `security-level.ts` đang ghi "đang chờ chốt B3".
4. Câu B5 (bản clone có phải duyệt lại) và B6 (pháp nhân con im lặng quá lâu) đã chốt chưa — hai câu này chặn phase 4.
5. Phần "sổ văn bản" làm sớm hơn lộ trình: có tính là kéo phase 6 (nhập liệu sổ giấy đang dở) lên sớm không?
