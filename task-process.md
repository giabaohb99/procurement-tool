# Đánh giá tiến độ Phase 1–4 (Văn thư) trên `frontend-v2`

- Chấm lần đầu 15/08/2026 · **cập nhật 17/08/2026** (dựng lại màn Quy tắc đánh số, và đóng Phase 1)
- Nhánh: `erp-v2`
- Nguồn yêu cầu: `quan-ly-van-thu-bo-tai-lieu.pdf`, tài liệu **02 · Lộ trình phát triển**, mục 5–8 (trang PDF 47–51)
- Phạm vi chấm: `frontend-v2/src/modules/document` + phần phụ thuộc ở `modules/hr` (mã số hiệu pháp nhân/phòng ban)
- Backend chỉ nhắc để nói rõ tính năng có chạy thật hay không; **không tính vào %**

## Kết luận một dòng

| Phase | Nội dung | % làm được | Đủ điều kiện chuyển phase? |
|---|---|---|---|
| 1 | Danh mục và số hiệu | **100%** | **ĐẠT** — cả 3 bài nghiệm thu xanh |
| 2 | Yêu cầu, soạn thảo, phiên bản | **~75%** | chưa |
| 3 | Bộ máy phê duyệt dùng chung | **~5%** | chưa |
| 4 | Ban hành, phạm vi, clone | **~90%** | chưa |
| **Tổng 4 phase** | trọng số theo khối lượng (15/30/35/20) | **≈ 58%** | |

Đọc nhanh: **Phase 1 ĐÓNG, Phase 2 xong đúng phần lõi (soạn thảo + phiên bản), Phase 3 và 4 chưa bắt đầu.**
Con số 58% thấp chủ yếu vì Phase 3 là phase nặng nhất (20 tính năng) và hoàn toàn chưa động tới.

> **Đổi gì so với lần chấm 15/08 — ba đợt:**
>
> *Đợt 1 (giao diện).* Màn Quy tắc đánh số dựng lại cho khớp khuôn Sổ văn bản (tab ra ngoài card,
> dùng `CatalogTable`, thêm/sửa sang trang riêng thay vì hộp thoại) + 6 test đầu tiên của phân hệ.
> Sửa chất lượng, **không** thêm tính năng lộ trình nào — % không đổi.
>
> *Đợt 2 (đóng Phase 1).* Dựng nốt hai bảng còn thiếu, vá một lỗi chặn phase, viết 8 test cho ba bài
> nghiệm thu. Phase 1 đi từ ~90% lên **100%**, tổng từ 30% lên 31%.
>
> *Đợt 3 (Phase 2 · C14 và C03/C06).* Màn báo ai đang giữ bản nháp; đính kèm văn bản thôi phát link
> công khai và có mã băm toàn vẹn. Phase 2 từ ~45% lên **~52%**, tổng lên **~33%**.
>
> *Đợt 4 (Phase 2 · nhóm E + C19).* Quan hệ cha–con trọn bộ E01–E06, bản trích nội bộ C19 và quan hệ
> «trích từ» E11 với ba ràng buộc khóa cứng. Phase 2 từ ~52% lên **~75%**, tổng lên **~40%**.
>
> *Đợt 5 (Phase 4 · phạm vi + tác động cha).* Phạm vi áp dụng F01–F05 và tác động khi văn bản cha đổi
> E07/E08. **Bỏ qua phần phụ thuộc Phase 3** theo yêu cầu. Phase 4 từ ~6% lên **~35%**, tổng lên **~46%**.

---

## 1. Phase 1 · Danh mục và số hiệu — 100% ✅ ĐÓNG (17/08/2026)

| Việc (theo PDF) | Mã | Trạng thái | Bằng chứng |
|---|---|---|---|
| Bảng loại văn bản, nhập 32 loại | A01, A02 | ✅ | `document-type-catalog.tsx`, `document-type-form.tsx`; seed `backend/app/seed_data/document_phase1.py` |
| Loại thứ 33 Trích lục (`id_scheme=2`, `needs_decision=FALSE`) | C20 | ✅ | `TRICH_LUC_DOC_TYPE` trong seed |
| Mã số hiệu 13 pháp nhân + phòng ban | A04, A05 | ✅ | `modules/hr/.../company-form-dialog.tsx`, `department-form-dialog.tsx` (`issue_code`) |
| Bảng nối phòng ban ↔ pháp nhân, trưởng phòng theo từng pháp nhân | A06 | ✅ | `department-company-card.tsx` (`issue_code_override`) |
| Bộ cấp số chống trùng, hai kiểu định danh | D01–D04 | ✅ | `document-numbering-rules-page.tsx`, `document-number-preview.tsx`; BE khóa dòng `with_for_update()` |
| Văn bản hủy vẫn giữ số, cấm đổi mã sau khi cấp số | D05, D07 | ✅ | FE có nút Bãi bỏ; BE `service.revoke()` giữ nguyên số + `issue_code_guard.py`; test `test_document_revoke_keeps_number.py` |
| Danh mục đối tác, cơ quan gửi nhận | A07 | ✅ | `document-partner-catalog.tsx` |
| Tạo trước bảng: sổ đi | S01 | ✅ | Mục 9.1 bỏ bảng `tab_outgoing_register` — sổ đi là **truy vấn** trên `tab_document`. Đã thêm 3 cột còn thiếu: `recipient_summary`, `copies`, `register_note` |
| Tạo trước bảng: sổ đến | S02 | ✅ | `incoming_register_model.py` → `tab_incoming_register`, `UNIQUE(pháp nhân, năm, số)`. Có sẵn cả `tab_document_book` + UI (vượt yêu cầu) |
| Tạo trước bảng: xác nhận đã đọc | J06 | ✅ | `recipient_model.py` → `tab_document_recipient`, gắn vào **phiên bản** chứ không vào văn bản |
| Tạo trước bảng: văn bản pháp luật | A09 | ✅ | Mục 9.3 bỏ bảng `tab_legal_reference` — gom vào `tab_document` với `origin = 2` + `legal_issuer`/`legal_url`. Đã thêm `issued_at` |

Cả hai bảng mới **chưa có service, chưa có router, chưa có màn hình** — đúng yêu cầu "chỉ bảng, chưa màn hình".
Migration: `85fd48d984db_bang_nguoi_nhan_va_so_van_ban_den.py`.

> **Đính chính lần chấm 15/08.** A09 và S01 bị chấm ❌ nhầm: tài liệu `04` mục 9.1 và 9.3 **cố ý bỏ**
> hai bảng đó, không phải quên làm. Sổ đi là báo cáo; văn bản pháp luật gom vào `tab_document` vì
> quan hệ "căn cứ theo" trỏ khóa ngoại vào `tab_document` — dòng ở bảng riêng không bao giờ làm
> đích của quan hệ được.

### Ba bài nghiệm thu chuyển phase — 3/3 ĐẠT

| Bài kiểm (theo PDF trang 48) | Kết quả | Ở đâu |
|---|---|---|
| 100 kết nối cùng xin số một loại một pháp nhân → đúng 100 số liên tiếp | **ĐẠT** — 0 trùng, 0 thiếu, chạy MySQL thật | `check_number_sequence_concurrency.py` |
| Hủy một văn bản → số của nó không quay lại cho văn bản sau | **ĐẠT** | `test_document_revoke_keeps_number.py` (4 test, mới) |
| Năm mới: sổ theo năm đếm lại từ 1, **mã tài liệu bất biến thì không** | **ĐẠT** sau khi vá | `test_ma_tai_lieu_khong_dem_lai_theo_nam.py` (4 test, mới) |

**Lỗi chặn phase tìm ra ngày 17/08 (đã vá).** `next_number()` đặt lại bộ đếm mỗi khi `row.year` lệch
năm truyền vào, trong khi bộ đếm mã tài liệu bất biến (`doc:DEGO:QC`) và sổ tắt `reset_yearly`
(`book:SD002`) đều **không có năm trong khóa** — một dòng dùng cho mọi năm. Hậu quả: 0h ngày 1/1,
văn bản đầu tiên nhận lại `DEGO-QC-001`, đụng `UNIQUE(doc_code)` → **không ai cấp số được nữa** cho
tới khi có người sửa tay bộ đếm. Nguyên nhân gốc là hợp đồng ngầm "nơi gọi phải nhớ truyền năm của
dòng vào" — cả `next_book_number` lẫn `numbering.assign` đều đã lỡ phá. Đã đổi thành cờ
`reset_yearly` tường minh trên `next_number()`, sửa kèm `peek_book_number()` (không sửa thì màn xem
trước và số cấp thật lệch nhau đầu tháng Giêng).

Làm thêm ngoài yêu cầu: **quyền theo sổ** và **quy tắc đánh số theo mẫu token** — thứ tài liệu xếp ở phase sau.

### Căn cứ chấm 100% — từng dòng, từ FE tới BE

Ba lớp căn cứ, xếp theo độ tin cậy giảm dần:

1. **Ba bài nghiệm thu trong PDF** — chạy được, xanh (bảng trên). Đây là thứ tài liệu ghi là điều kiện chuyển phase.
2. **Test tự động** cho từng dòng tính năng — bảng dưới.
3. **Đọc mã** — nơi không có test. Đây là lớp yếu nhất, đã đánh dấu rõ.

| # | Việc (mã) | Test case cụ thể | Tầng |
|---|---|---|---|
| 1 | Bảng loại VB, 32 loại + Trích lục thứ 33 (A01, A02, C20) | `test_document_phase1_seed.py::test_phase1_catalog_has_32_official_types_and_trich_luc_33`<br>`::test_phase1_seed_is_idempotent_and_backfills_primary_department_company` | BE |
| 2 | Mã số hiệu pháp nhân + phòng ban (A04, A05) | `test_department_company.py::test_department_company_keeps_manager_and_issue_code_per_legal_entity` | BE |
| 3 | Bảng nối phòng ban ↔ pháp nhân, trưởng phòng theo từng pháp nhân (A06) | `::test_department_company_soft_disables_omitted_legal_entity`<br>`::test_department_company_rejects_manager_from_another_legal_entity` | BE |
| 4 | Bộ cấp số chống trùng (D01–D04) | `test_number_sequence.py` — 7 test: `test_cap_so_tang_dan_lien_tuc` · `test_sang_nam_moi_dem_lai_tu_dau` · `test_so_khong_reset_thi_dem_tiep_qua_nam` · `test_start_no_ap_dung_khi_chuyen_tu_so_giay` · `test_xem_truoc_khong_chiem_so` · `test_khoa_scope_key_la_duy_nhat` · `test_chuoi_so_hien_thi` | BE |
| 5 | Hai kiểu định danh + quy tắc theo mẫu (D01–D04) | `test_document_numbering_rule.py` — 4 test: `test_rule_scope_serialize_and_resolve` · `test_rule_drives_preview_and_real_number` · `test_rule_rejects_book_from_other_direction` · `test_manual_number_requires_rule_permission_and_keeps_audit_sequence` | BE |
| 6 | Chuỗi số hiệu hiển thị trên form (D01–D04) | `numbering-rule-sample.test.ts` — 6 test: thay hết token · đệm `08` không phải `8` · không cắt số ba chữ số · thay MỌI lần xuất hiện · giữ nguyên chữ người dùng gõ · token sai tên giữ nguyên | **FE** |
| 7 | Văn bản hủy vẫn giữ số (D05) | `test_document_revoke_keeps_number.py` — 4 test: `test_bai_bo_van_ban_thi_so_cua_no_khong_duoc_cap_lai` · `test_bai_bo_lan_hai_bi_tu_choi` · `test_cap_so_lai_tren_van_ban_da_co_so_thi_khong_lam_gi` · `test_ngay_bai_bo_dong_luon_ngay_het_hieu_luc` | BE |
| 8 | Năm mới không đá bộ đếm mã bất biến (D01) | `test_ma_tai_lieu_khong_dem_lai_theo_nam.py` — 4 test: `test_ma_tai_lieu_bat_bien_dem_tiep_qua_nam_moi` · `test_xem_truoc_va_cap_that_khong_lech_nhau_qua_nam` · `test_so_tat_reset_yearly_cung_dem_tiep_qua_nam` · `test_so_bat_reset_yearly_van_dem_lai_tu_dau` | BE |
| 9 | 100 kết nối cùng cấp số | `check_number_sequence_concurrency.py` — chạy tay trên **MySQL thật**, không nằm trong `pytest` (SQLite khóa cả tệp nên không mô phỏng được tranh chấp dòng) | BE |
| 10 | **Cấm đổi mã sau khi cấp số (D07)** | ⚠️ **KHÔNG CÓ TEST** — chỉ đọc `issue_code_guard.py` | — |
| 11 | **Danh mục đối tác, cơ quan gửi nhận (A07)** | ⚠️ **KHÔNG CÓ TEST** — chỉ bấm tay trên `document-partner-catalog.tsx` | — |
| 12 | **Bốn bảng dựng trước (S01, S02, J06, A09)** | ⚠️ **KHÔNG CÓ TEST** — kiểm bằng `alembic upgrade head` + `inspect(engine)` đọc cột. Chấp nhận được vì bảng rỗng, chưa mã nào ghi vào | — |

Ngoài yêu cầu phase 1 nhưng cùng vùng mã: `test_document_access.py` — 22 test quyền theo văn bản và
**quyền theo sổ**, trong đó `test_vao_so_thi_duoc_cap_so_thu_tu_trong_so` chạm thẳng vào bộ cấp số.

### "100%" nghĩa là gì, và không nghĩa là gì

**Có nghĩa:** đủ 10/10 dòng tính năng của bảng phase 1, và 3/3 bài nghiệm thu tài liệu đặt ra đều xanh.

**KHÔNG có nghĩa là đã kiểm hết.** Ba chỗ đang dựa vào đọc mã chứ không phải test (dòng 10, 11, 12),
và **phía giao diện gần như trắng**: cả `frontend-v2` chỉ có 10 tệp test, trong đó đúng **một** tệp
thuộc phân hệ Văn thư, và tệp đó chỉ kiểm hàm ghép chuỗi xem trước — không kiểm form, không kiểm
danh mục, không kiểm luồng bấm nào.

Muốn "100%" mang nghĩa **đã kiểm**, còn thiếu 4 nhóm test (chưa làm, không tính vào %):

- [ ] [P1][TEST-BE] `issue_code_guard`: đổi mã pháp nhân / phòng ban / loại VB sau khi bộ đếm đã có dòng → bị chặn, câu báo nói rõ lý do — **S**
- [ ] [P1][TEST-BE] Danh mục đối tác: tạo / sửa / vô hiệu hóa, chặn trùng mã — **S**
- [ ] [P1][TEST-FE] `document-numbering-rule-schema`: mẫu thiếu `{STT}` bị chặn · chọn "Chọn loại văn bản" mà để rỗng bị chặn · tương tự cho sổ — **S**
- [ ] [P1][TEST-FE] Form quy tắc đánh số: đổi chiều văn bản thì danh sách sổ chọn được **đặt lại**, quy tắc đã cấp số thì các ô sinh số bị khóa — **S**

---

## 2. Phase 2 · Yêu cầu, soạn thảo, phiên bản — ~75%

| Việc | Mã | FE v2 | Ghi chú |
|---|---|---|---|
| Yêu cầu văn bản: ba loại, lý do bắt buộc | B01 | ❌ | Bỏ ở bản 1 — `needs_request` luôn `false` |
| Gợi ý văn bản đã có | B05 | ✅ | `document-suggestion-list.tsx` |
| Chặn soạn khi chưa có yêu cầu duyệt; loại được bỏ qua | B03, B06 | ❌ | Trường có trong DB, chưa có màn |
| Sinh bản nháp từ yêu cầu, theo dõi yêu cầu | B04, B07 | ❌ | `tab_document_request` có bảng, FE không có màn |
| Bản ghi văn bản, bộ trường chung, tệp mẫu theo loại | C01, C02 | ✅ | `document-record-form.tsx`, `document-template-catalog.tsx` |
| Phiên bản bất biến, lý do sửa, khóa sửa sau duyệt | C04, C05, C07 | ✅ | `document-version-tab.tsx`, `content_sha256` |
| Sửa văn bản đã ban hành | C13–C18 | ✅ | `document-version-dialog.tsx`, `document-version-banner.tsx`; **C14 xong 17/08**: `document-draft-holder-notice.tsx` nêu tên người giữ + nút sang bản nháp, và lỗi 409 lúc thua đường đua ở lại trong hộp thoại thay vì bay theo toast |
| Tệp đính kèm đường riêng tư, mã băm | C03, C06 | 🟡 ~80% | **Nâng 17/08.** Ứng dụng không còn phát link công khai cho đính kèm văn bản (`PRIVATE_ENTITIES`), tải qua `GET /attachments/{id}/download` có kiểm quyền bằng `downloadFile`; mã băm SHA-256 tính lúc tải lên và hiện trên danh sách. **Còn lại là việc hạ tầng** — xem ghi chú dưới |
| Ghi số hiệu cũ của văn bản giấy | C12 | ✅ | `legacy_code` |
| Quan hệ cha con | E01–E06 | ✅ | `tab_doc_type_link_rule` + `tab_document_link`; màn Quy tắc quan hệ, tab Quan hệ trên trang văn bản, cây tài liệu |
| Bản trích nội bộ | C19 | ✅ | `excerpt_service.py`, `document-excerpt-dialog.tsx`; mang đúng loại của gốc, **không cấp số riêng** |
| Quan hệ "trích từ" | E11 | ✅ | `is_system` + `source_version_id` bắt buộc; ba ràng buộc khóa cứng ở tầng dịch vụ |
| Ảnh → văn bản, ảnh gốc cạnh nháp, cờ tắt AI | L01, L02, L07 | 🟡 ~25% | Có nhập .doc/.docx/.pdf/.md/.html + truy vết chuyển đổi — **không phải ảnh/OCR** |
| Luồng duyệt yêu cầu tạm một bước | — | 🟡 50% | `submit/approve/reject` đặt trên văn bản, không phải trên yêu cầu |

### Làm ngày 17/08 — C14 và C03/C06

**C14 · ai đang giữ bản nháp.** Ràng buộc "một văn bản một bản nháp" đã ép ở tầng dữ liệu từ trước
(cột sinh `open_slot` + `UNIQUE`), backend cũng đã trả 409 kèm TÊN người giữ. Thủng nằm hết ở giao diện,
hai chỗ:

1. Đường thường — tab phiên bản chỉ ghi *"đang có bản nháp mở"*, không nói ai, không có lối sang xem.
   Nay là `document-draft-holder-notice.tsx`: bản số mấy, ai giữ, mở từ lúc nào, kèm nút **Xem bản nháp**.
2. Đường đua — hai người cùng bấm, người thua nhận 409 dưới dạng **toast bay mất sau vài giây**, trong
   khi đó chính là câu chứa tên người cần hỏi. Nay câu đó ở lại ngay trong hộp thoại; và danh sách
   phiên bản được nạp lại **cả khi lỗi** (`onSettled`), nếu không màn hình vẫn hiện nút "Mở phiên bản
   mới" và bấm bao nhiêu lần cũng hỏng.

Test: `document-draft-holder-notice.test.tsx` — 6 test, **component test đầu tiên của phân hệ**.

**C03/C06 · đính kèm riêng tư + mã băm.** Đã có sẵn `GET /api/attachments/{link_id}/download` kiểm quyền
đàng hoàng, nhưng giao diện lại dùng `file.url` — đường đọc thẳng kho lưu trữ. Chạy local đường đó là
`StaticFiles`, **không hỏi đăng nhập**; chạy thật là URL công khai của bucket. Sửa ba lớp:

- `PRIVATE_ENTITIES` trong `core/file_registry.py` — API trả `url` RỖNG cho `document_version`.
  Giữ nguyên `url` cho mọi entity Thu mua vì `frontend/` đóng băng đang đọc nó.
- `downloadFile` (`@/core/api`) tải bằng `httpClient` rồi dựng liên kết tạm — `<a href>` không gắn được
  token Bearer nên đi thẳng vào 401.
- `tab_file.sha256` tính lúc tải lên, hiện 12 ký tự đầu trên danh sách, rê chuột ra chuỗi đầy đủ.

Test: `test_dinh_kem_van_ban_rieng_tu.py` — 6 test, trong đó một test canh riêng bẫy `seek(0)`: quên trả
con trỏ về đầu sau khi băm thì `upload_fileobj` đọc được 0 byte và **đẩy lên kho một tệp rỗng, không lỗi
nào bật lên**.

> ⚠️ **Vì sao C03 là ~80% chứ không phải xong.** Ứng dụng thôi phát link công khai, nhưng object trên kho
> lưu trữ **vẫn đọc được** nếu ai đó đã có URL từ trước (mọi tệp tải lên trước 17/08/2026) hoặc đoán đúng
> key. Bịt hẳn = chuyển bucket sang riêng tư + đổi TOÀN BỘ phân hệ sang link tạm, tức là P0-N02/N03,
> đụng cả `frontend/` đang đóng băng — không nằm trong phạm vi task này. **Tới lúc đó vẫn chưa được đưa
> văn bản Tuyệt mật thật vào hệ thống.**

---

## 3. Phase 3 · Bộ máy phê duyệt dùng chung — ~5%

Chưa bắt đầu. Không có bảng luồng/bước/phiên chạy/việc/hành động, không màn khai luồng, không "Việc của tôi".
Thứ duy nhất có là 3 nút cứng `submit → approve/reject` trên trang chi tiết — đúng bằng "luồng một bước
viết tay tạm thời" mà tài liệu xếp vào phase 2.

Chưa có: **I01–I26**. Bản 1 gồm 20 tính năng (I01–I12, I15–I18, I20, I21, I23, I26); sáu cái còn lại
(I13, I14, I19, I22, I24, I25) tài liệu xếp bản 2.

Sáu bảng phải dựng: `tab_approval_flow` · `_node` · `_instance` · `_task` · `_action` · `tab_delegation`.
Chúng **không dành riêng cho văn bản** — nhận mọi loại chứng từ, và sau này thay 5 luồng duyệt viết tay
của Thu mua.

⚠️ **Chưa được bắt đầu.** Ràng buộc số 4 của cam kết "không ảnh hưởng Thu mua" là phải có kiểm thử tự
động cho 5 luồng duyệt hiện tại TRƯỚC — đó là lưới an toàn duy nhất, và nó đang thiếu. Danh sách task
đầy đủ ở phần cuối tài liệu này.

---

## 4. Phase 4 · Ban hành, phạm vi, clone — ~90%

| Việc | Mã | FE v2 |
|---|---|---|
| Vòng đời văn bản 8 trạng thái | J01 | ✅ |
| Ban hành (cấp số, đóng phiên bản) | J04 | ✅ | Màn ban hành có bản xem trước: số sắp cấp, bản sắp khóa, ngày hiệu lực, văn bản sắp bị thay thế. Tách **chặn** khỏi **cảnh báo**. Còn thiếu J05 gửi thông báo |
| Ký điện tử nội bộ, ghi rõ loại chữ ký | J02, J03 | ✅ | `tab_signature` chỉ ghi thêm; câu giá trị pháp lý do backend cấp, hiện ngay cạnh chữ ký |
| Phạm vi ba kiểu, bao gồm/loại trừ, áp cho đơn vị con | F01–F04 | ✅ | `tab_document_scope` + CHECK ép phòng ban phải kèm pháp nhân; `document-scope-card.tsx` |
| Màn "văn bản áp dụng cho tôi" | F05 | ✅ | `documents-applied-to-me-page.tsx`. Thông báo theo phạm vi (J05) chưa — cần bộ thông báo |
| Clone xuống pháp nhân con | F06–F08 | ✅ | `clone_service.py` — bốn điều kiện bắt buộc đều có test riêng |
| Gửi thư kèm nháp, bảng theo dõi clone | F09, F10 | ✅ | `clone_notification.py` (chuông + thư) và `document-clone-card.tsx` trả lời đủ bốn câu |
| Bản gốc lên phiên bản → con cần rà lại | F11 | ✅ | `mark_clones_for_review` + báo người phụ trách qua chuông |
| Màn chọn cơ chế lúc ban hành | F13 | ✅ | `document-issue-dialog.tsx` — bảng so sánh hai cơ chế lấy thẳng từ `00` mục 2.2; cảnh báo khi gắn phạm vi mà chưa khai dòng nào |
| Cảnh báo tác động sửa cha, xử lý bãi bỏ cha | E07, E08 | ✅ | `parent_change_service.py`; hai cột `on_parent_*` giờ mới thật sự điều khiển hành vi |
| Nhãn "đã bị sửa đổi" | J10 | ✅ | `supersede_service.py` + `document-amended-banner.tsx`; ba tác động tự động của quan hệ thay thế/sửa đổi/bãi bỏ |
| Quyết định ban hành kiểm ở mức phiên bản | J11 | 🟡 ~60% | Loại khai `needs_decision` mà thiếu quan hệ «Kèm theo» → **chặn ban hành**. Phần *mỗi lần sửa lớn phải kèm Quyết định MỚI* chưa làm — xem câu hỏi 8 |

Sáu bài kiểm chuyển phase 4: chưa chạy chính thức, nhưng phần clone đã có 15 test tự động phủ cả bốn điều kiện bắt buộc.

---

## 5. Rủi ro

1. **Object trên kho lưu trữ vẫn đọc được bằng URL.** Ứng dụng đã thôi phát link công khai cho đính kèm
   văn bản (17/08), nhưng bucket còn để công khai nên URL cũ vẫn mở được, và tệp tải lên trước 17/08 thì
   URL đó đã phát ra rồi. Phase 0 (N02/N03/H01) chưa xong → chưa đưa văn bản Tuyệt mật thật vào hệ thống.
2. **Test phía giao diện gần như trắng.** Cả phân hệ FE ~9.900 dòng, mới có 1 tệp test (6 test).
   Backend khá hơn: 500 test xanh, trong đó 8 test cấp số viết ngày 17/08 — nhưng phần **màn hình**
   (form văn bản, phiên bản, quyền theo văn bản) vẫn chưa có lưới an toàn nào.
3. **Bỏ bước yêu cầu (B01–B07) đã thực thi trong mã** nhưng lộ trình vẫn xếp là việc phase 2 — cần chốt bỏ hẳn hay hoãn.
4. **Phase 4 phụ thuộc phase 3**, đừng hứa mốc phase 4 trước khi bộ máy duyệt có mô hình dữ liệu.

---

## 6. Code xong thì kiểm thế nào

### 6.1 Ba lệnh phải chạy trước khi báo xong việc

```bash
# BACKEND — pytest KHÔNG có sẵn trong image, lần đầu phải cài
docker compose exec -T api pip install pytest
docker compose exec -T api python -m pytest test/backend -q          # phải xanh hết
docker compose exec -T api python -m pytest test/backend/test_x.py -q # chạy một tệp

# FRONTEND — ba cổng, gộp trong một lệnh
docker compose exec erp npm run check     # = typecheck + lint + test
# tách lẻ khi cần soi lỗi:
docker compose exec erp npm run typecheck # tsc --noEmit, phải 0 lỗi
docker compose exec erp npm run lint      # eslint, phải 0 lỗi
docker compose exec erp npm run test      # vitest run
```

⚠️ `npm run format:check` **không** nằm trong cổng và đang đỏ ~381 tệp. Đừng chạy
`npm run format` giữa chừng — nó đẻ diff khổng lồ đè lên việc người khác đang làm dở.

### 6.2 Hai thứ pytest không kiểm được, phải chạy tay

```bash
# Bài 100 kết nối — chạy trên MySQL THẬT. pytest dùng SQLite in-memory, mà SQLite
# khóa cả tệp nên không mô phỏng được hai transaction tranh nhau một dòng.
docker compose exec -T api python -m test.backend.check_number_sequence_concurrency
# ĐẠT khi in ra: Trùng 0 · Thiếu số: không · KẾT QUẢ: ĐẠT

# Migration — sau khi sửa bất kỳ model.py nào
docker compose exec api alembic revision --autogenerate -m "mo_ta"
#   → MỞ FILE VỪA SINH RA VÀ DỌN. Autogenerate luôn bắt kèm drift cũ của
#     tab_comment_* và tab_ticket* — gỡ hết, chỉ giữ phần mình vừa đổi.
#   → Cột NOT NULL thêm vào bảng đã có dữ liệu PHẢI có server_default.
docker compose exec api alembic upgrade head
docker compose exec -T api alembic check   # còn báo drift tab_comment_*/tab_ticket* là bình thường
```

### 6.3 Sửa chỗ nào thì chạy test nào

| Sửa gì | Chạy gì |
|---|---|
| `doc_catalog/number_service.py` | `test_number_sequence.py` + `test_ma_tai_lieu_khong_dem_lai_theo_nam.py` + **bài 100 kết nối** |
| `document/numbering.py` | 2 tệp trên + `test_document_numbering_rule.py` + `test_document_revoke_keeps_number.py` |
| `doc_catalog/numbering_rule_*.py` | `test_document_numbering_rule.py` |
| `document/service.py` (bãi bỏ, đổi trạng thái) | `test_document_revoke_keeps_number.py` |
| `attachment/controller.py`, `core/file_registry.py` | `test_dinh_kem_van_ban_rieng_tu.py` |
| `document/link_service.py`, `link_serializer.py`, `doc_catalog/link_rule_*.py` | `test_document_quan_he_cha_con.py` |
| `document/excerpt_service.py`, `service.revoke/approve` | `test_ban_trich_noi_bo.py` |
| `document/scope_service.py`, `scope_controller.py` | `test_pham_vi_ap_dung.py` |
| `document/parent_change_service.py` | `test_document_quan_he_cha_con.py` |
| `document/signature_service.py` | `test_chu_ky_van_ban.py` |
| `document/supersede_service.py`, `service.approve` | `test_nhan_da_bi_sua_doi.py` |
| `document/issue_service.py` | `test_ban_hanh_van_ban.py` |
| `document/clone_service.py`, `clone_notification.py` | `test_clone_phap_nhan_con.py` |
| `document-draft-holder-notice.tsx`, `document-version-*.tsx` | `document-draft-holder-notice.test.tsx` + kịch bản bấm tay 6.5 |
| `document/access_service.py`, quyền theo sổ | `test_document_access.py` (22 test) |
| `seed_data/document_phase1.py` | `test_document_phase1_seed.py` |
| bất kỳ `model.py` nào | `alembic check` + cả bộ `pytest` |
| bất kỳ tệp nào trong `frontend-v2/src` | `npm run check` |

### 6.4 Đặt test mới ở đâu

| | Backend | Frontend |
|---|---|---|
| Chỗ đặt | `test/backend/test_<viec>.py` — thư mục phẳng, không mirror cây mã | **cạnh tệp nó kiểm**: `x.ts` → `x.test.ts`. Không có thư mục `__tests__` |
| Cơ sở dữ liệu | SQLite in-memory, fixture `db` / `seed` ở `conftest.py`, mỗi test một phiên sạch | jsdom; gọi API thì `vi.mock` ở tầng `@/core/api`, **không** mock `axios` |
| Đặt tên | `test_<hanh_vi_bang_tieng_viet>` | `it('mô tả hành vi bằng tiếng Việt')` — tả hành vi, không tả tên hàm |
| Nhắc lại lỗi cũ | Ghi rõ lỗi đó trong docstring để người sau biết vì sao không được xóa | Ghi trong comment ngay trên `it(...)` |

Múi giờ khi chạy test FE cố định `Asia/Ho_Chi_Minh`. Đừng viết khẳng định phụ thuộc
"hôm nay" — truyền ngày cụ thể vào.

### 6.5 Kịch bản bấm tay — phần FE chưa có test tự động

Giao diện Văn thư gần như không có test, nên đến khi lấp xong 4 task `TEST-FE` thì
những màn dưới đây **phải bấm tay** sau mỗi lần sửa. Đăng nhập vào <http://localhost:8083>.

**Quy tắc đánh số** (`/document/numbering-rules`)

1. Đổi tab chiều văn bản → URL đổi theo, danh sách đổi theo, tab 1 thì URL **không** kèm `?direction=`.
2. Bấm *Thêm mới* → phải **sang trang riêng**, không mở hộp thoại; chiều văn bản nhận sẵn tab đang đứng.
3. Xoá `{STT}` khỏi mẫu số → lưu bị chặn, báo "Mẫu số phải có {STT}".
4. Chọn *Chọn loại văn bản* rồi không tick gì → lưu bị chặn.
5. **Đổi chiều văn bản → danh sách sổ chọn được phải đặt lại**, không giữ sổ của chiều cũ.
6. Mở một quy tắc **đã cấp số** → chiều / mẫu / số bắt đầu / đếm lại theo năm bị khoá, nút Xoá biến mất.
7. Bấm *Quay lại* → về đúng tab vừa đứng.

**Sổ văn bản** (`/document/books`) và **Loại văn bản** — cùng khuôn: tạo, sửa, vô hiệu hoá, tìm kiếm, xem nhật ký thao tác ở trang chi tiết.

**Cấp số thật** — tạo một văn bản loại `id_scheme = 2`, xem trước số hiệu trên form, lưu, rồi đối chiếu: **số hiển thị lúc xem trước phải trùng số được cấp**. Bãi bỏ nó rồi tạo văn bản kế tiếp → số phải đi tiếp, không nhặt lại số vừa bãi bỏ.

**Bản nháp một người giữ (C14)** — cần HAI trình duyệt, hai tài khoản khác nhau, cùng mở một văn bản đã duyệt.

1. Người A bấm *Mở phiên bản mới*, khai lý do, lưu.
2. Người B tải lại trang → tab phiên bản phải hiện băng vàng ghi **đúng tên người A** và bản số mấy; nút *Mở phiên bản mới* biến mất; bấm *Xem bản nháp* thì nhảy sang đúng bản đó.
3. Đường đua: cả hai cùng mở sẵn hộp thoại *trước khi* A lưu, rồi A lưu xong B mới bấm → B phải thấy câu **"Bản nháp 2.0 đang do A giữ"** nằm lại NGAY TRONG hộp thoại (không phải toast bay mất), và sau khi đóng hộp thoại thì tab phiên bản đã tự cập nhật.

**Đính kèm riêng tư (C03/C06)** — mở tab Mạng của trình duyệt ở trang chi tiết văn bản.

1. Gọi `GET /api/attachments?entity=document_version&...` → mọi phần tử phải có **`url` rỗng**. Còn thấy chuỗi `http...` là hồi quy.
2. Bấm tải một tệp → phải thấy request `GET /api/attachments/{id}/download` có header `Authorization`, không phải điều hướng ra kho lưu trữ.
3. Chép URL request đó, dán sang cửa sổ ẩn danh → phải bị **401**, không tải được.
4. Tệp mới tải lên phải hiện 12 ký tự mã băm cạnh dung lượng; rê chuột ra chuỗi đầy đủ. Tải tệp về rồi chạy `shasum -a 256 <tệp>` → phải trùng.

---

# DANH SÁCH TASK — copy thẳng lên Lark

Mỗi dòng là một task độc lập, đã kèm mã tính năng để tra ngược tài liệu.
Độ nặng: **S** ≤ 1 ngày · **M** 2–4 ngày · **L** ≥ 1 tuần (ước lượng thô, chưa tính review).

## Nhóm 0 · Việc nền, làm trước hoặc song song

- [ ] [P0][N02/N03/H01] Kho tệp riêng tư + link tạm có kiểm quyền, ngừng ghi link công khai — **L** — CHẶN việc đưa văn bản mật thật vào hệ thống
- [x] [P0][C03/C06] Chuyển đính kèm văn bản sang đường tải riêng tư, hiện mã băm toàn vẹn — **M** — xong 17/08 phần ứng dụng; phần kho lưu trữ nằm ở task trên
- [ ] [P0][TEST] Viết test cho phần đã có: form văn bản, phiên bản, quyền theo văn bản — **M** — làm trước khi code thêm

## Phase 1 · Danh mục và số hiệu — XONG 17/08/2026

- [x] [P1][J06] Tạo bảng "xác nhận đã đọc" — chỉ bảng, chưa màn hình — **S**
- [x] [P1][S02] Tạo bảng sổ văn bản đến `tab_incoming_register` — chỉ bảng — **S**
- [x] [P1][S01/A09] Bổ sung cột gom về `tab_document` (sổ đi + văn bản pháp luật) — **S**
- [x] [P1][D01] Vá lỗi bộ đếm tự đếm lại đầu năm với mã tài liệu bất biến — **S**
- [x] [P1][TEST] 8 test cho 2 bài nghiệm thu chưa từng được kiểm — **S**

## Phase 2 · Yêu cầu, soạn thảo, phiên bản (còn 2 việc)

- [x] [P2][E01/E02] Bảng quy tắc quan hệ cha–con + 10 loại quan hệ — **M** — xong 17/08
- [x] [P2][E03/E04] Form tự hiện ô quan hệ theo loại + chặn gửi duyệt khi thiếu quan hệ bắt buộc — **M** — xong 17/08
- [x] [P2][E05/E06] Cấm vòng lặp quan hệ + màn cây tài liệu — **M** — xong 17/08
- [x] [P2][C19] Soạn bản trích nội bộ — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn — **M** — xong 17/08
- [x] [P2][E11] Quan hệ "trích từ" + 3 ràng buộc khóa cứng + cột ghi trích từ phiên bản nào của gốc — **M** — xong 17/08
- [x] [P2][C14] Màn báo "ai đang giữ bản nháp" khi người thứ hai bấm mở phiên bản mới — **S** — xong 17/08
- [ ] [P2][L01/L02] Chuyển ảnh thành văn bản (OCR) + đặt ảnh gốc cạnh bản nháp để đối chiếu — **L** — CẦN chốt câu hỏi 2 bên dưới
- [ ] [P2][L07] Cờ tắt AI — tắt là hệ thống chạy bình thường không có phần AI — **S**
- [ ] [P2][B01/B03/B04/B06/B07] Yêu cầu văn bản: 3 loại, lý do bắt buộc, chặn soạn khi chưa duyệt, sinh nháp từ yêu cầu, màn theo dõi — **L** — CHỜ chốt câu hỏi 1 bên dưới

## Phase 3 · Bộ máy phê duyệt dùng chung — phase nặng nhất

**20 tính năng bản 1** (I01–I12, I15–I18, I20, I21, I23, I26). Sáu tính năng còn lại của nhóm I
xếp bản 2, liệt kê riêng ở cuối — đừng kéo vào bản 1.

Đây là phase **duy nhất chạm vào Thu mua**. Bộ máy mới đứng CẠNH mã duyệt cũ, bật/tắt theo từng
loại chứng từ bằng cờ, không thay chỗ.

### 3.0 · Trước khi viết dòng mã đầu tiên (2 việc — chặn tất cả)

- [ ] [P3][N01] Viết kiểm thử tự động cho **5 luồng duyệt hiện tại của Thu mua** — **M** — CHẶN CỨNG. Tài liệu nói thẳng: đây là lưới an toàn duy nhất, *"không có nó thì mọi cam kết còn lại chỉ là lời hứa"*. Không có bộ này thì không được đụng dòng mã nào của phase 3
- [ ] [P3][GIẤY] Khai thử **8 luồng thật ra giấy** bằng đúng mô hình định làm: 5 luồng Thu mua + 3 luồng văn thư (duyệt yêu cầu · duyệt nội dung · duyệt bản clone) — **S** — chỗ nào khai không nổi là mô hình còn thiếu. Sửa trên giấy rẻ hơn nhiều so với sửa khi đã có phiếu chạy trong đó

### 3.1 · Mô hình dữ liệu — 6 bảng (nền của mọi việc còn lại)

- [ ] [P3][I01/I02] `tab_approval_flow` + `tab_approval_node` — luồng và các bước — **L** — `flow.entity` nhận MỌI loại chứng từ, không riêng văn bản. `node.flow_role`: đề xuất · thực hiện · kiểm tra · phê duyệt
- [ ] [P3][I21] `tab_approval_instance` với cột **`flow_snapshot` JSON** — **M** — phiếu chạy theo BẢN CHỤP của chính nó, không tham chiếu tới bản luồng đang sống. Đây là cách duy nhất để "sửa luồng khi có 5 phiếu đang chạy" không làm hỏng 5 phiếu đó
- [ ] [P3][I17] `tab_approval_task` + **`INDEX(assignee_employee_id, status)`** — **M** — chỉ mục quan trọng nhất của cả hệ thống: đó là truy vấn màn "Việc của tôi", chạy mỗi lần có người mở trang chủ
- [ ] [P3][I20] `tab_approval_action` — **chỉ ghi thêm, không sửa, không xóa** — **M** — ba cột `actor_employee_id` / `on_behalf_of_id` / `delegation_id` để bản in ghi đúng câu *"ông B duyệt thay ông A theo ủy quyền số 12"*. Ghi một người là sau này không phân biệt được ai chịu trách nhiệm
- [ ] [P3][I12] `tab_delegation` — ủy quyền có thời hạn — **S** — `from_date`/`to_date` BẮT BUỘC. Cấm ủy quyền dây chuyền ở tầng dịch vụ: A ủy cho B thì B không ủy tiếp cho C phần việc nhận từ A

### 3.2 · Khai luồng bằng giao diện (6 việc)

- [ ] [P3][I01] Màn khai luồng: bước, thứ tự, tên bước — **không sửa mã, không deploy lại** — **L**
- [ ] [P3][I03] Sáu cách chọn người duyệt: người cụ thể · vai trò · trưởng phòng người nộp · lên N cấp · người đại diện pháp nhân · lấy từ một ô trên phiếu — **L** — tài liệu còn cách thứ 7 (cả phòng ban) trong `approver_kind`, cần chốt có làm bản 1 không
- [ ] [P3][I04] Rẽ nhánh theo điều kiện (số tiền · loại VB · phòng ban · pháp nhân · mức mật) + **`is_default_branch`** — **M** — cột chống mất phiếu. Không có nó thì phiếu rơi vào trạng thái không nhánh nào nhận, biến mất khỏi mọi danh sách, tới lúc có người đi hỏi mới phát hiện
- [ ] [P3][I05] Nhiều người trong một bước — 4 chế độ: một người là đủ · tất cả phải duyệt · lần lượt · đủ tỷ lệ (`quorum`) — **M**
- [ ] [P3][I21] Phiên bản của luồng: `version_no` tăng mỗi lần sửa, phiếu đang chạy giữ nguyên bản cũ tới khi kết thúc — **M**
- [ ] [P3][I26] Cờ bật/tắt theo từng loại chứng từ — **tắt là quay về đường duyệt cũ ngay, không cần deploy** — **S** — đây là đường lui của cả phase

### 3.3 · Chạy phiên duyệt (5 việc)

- [ ] [P3][I09/I10/I11] Trả lại (về người nộp hoặc về một bước cụ thể) · Từ chối · Rút lại — **L** — cả ba **bắt buộc nhập lý do**; rút lại chỉ khi chưa ai duyệt
- [ ] [P3][I06] Trùng thao tác thì bỏ qua — 3 mức: trùng liền kề · trùng bất kỳ chỗ nào phía trước · không bỏ qua — **M** — task phải mang **trạng thái 5 riêng** ("tự động qua vì trùng người"), KHÔNG được ghi thành "đã duyệt": bản in dấu vết cần phân biệt người này ký với bước này tự qua
- [ ] [P3][I08] Chặn tự duyệt — **M** — người nộp không duyệt phiếu của chính mình; luồng bắt buộc trùng thì chuyển lên cấp trên
- [ ] [P3][I18] Hạn duyệt (`sla_hours`) + nhắc + quá lâu thì leo lên cấp trên — **M**
- [ ] [P3][I16] Ý kiến và tệp đính kèm khi duyệt — trao đổi ngay trên phiếu, không qua chat riêng — **M**

### 3.4 · Người vắng mặt / nghỉ việc (3 việc)

- [ ] [P3][I07] Người duyệt nghỉ việc thì chỉ định người khác (`fallback_employee_id` theo bước) — **M** — ⚠️ `on_no_approver` **cố ý không có giá trị "tự động duyệt qua"**. Lark có tùy chọn đó; với văn bản nó tạo ra văn bản có hiệu lực mà không ai chịu trách nhiệm. Không khai giá trị thì sau này không ai bật nhầm được
- [ ] [P3][I12] Ủy quyền có thời hạn — nhật ký ghi CẢ HAI danh tính — **M**
- [ ] [P3][I23] Bàn giao hàng loạt khi nghỉ việc: 30 phiếu đang chờ chuyển hết sang người khác trong một lần — **M**

### 3.5 · Màn hình người dùng (3 việc)

- [ ] [P3][I17] **Việc của tôi** — một chỗ gom mọi thứ đang chờ tôi, của cả văn thư lẫn thu mua — **L** — màn được mở nhiều nhất của cả hệ
- [ ] [P3][I15] Người nhận bản sao — chỉ nhận thông báo, không duyệt (`node_kind = 2`) — **S**
- [ ] [P3][I20] Bản in dấu vết duyệt: ai duyệt lúc nào, ý kiến gì — **M** — *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái này», câu trả lời phải là một tờ giấy in ra được, không phải một ảnh chụp màn hình"*

### 3.6 · Chuyển đổi (2 việc, làm cuối)

- [ ] [P3][CHUYỂN] Chuyển luồng duyệt văn bản của phase 2 sang bộ máy mới — **M** — hiện là 3 nút cứng `submit → approve/reject` trên trang chi tiết. Bật bằng cờ I26, giữ đường lui
- [ ] [P3][CHUYỂN] Chuyển luồng duyệt **yêu cầu văn bản** sang bộ máy mới — **S** — ⚠️ phụ thuộc câu hỏi 1: B01–B07 bỏ hẳn hay hoãn. Bỏ hẳn thì task này biến mất

### Sáu bài nghiệm thu — điều kiện chuyển phase

| # | Bài kiểm | Canh cái gì |
|---|---|---|
| 1 | Khai luồng 4 bước bằng giao diện, **không sửa dòng mã nào, không deploy lại** → phiếu chạy đúng qua 4 người | I01 có thật là "khai bằng giao diện" không |
| 2 | Người ở bước 1 cũng là người ở bước 3 → tự bỏ qua bước 3, **nhật ký ghi rõ lý do bỏ qua** | I06 + trạng thái 5 riêng |
| 3 | Tắt trạng thái một nhân sự đang giữ 3 phiếu → 3 phiếu chuyển người thay thế, **không phiếu nào tự động duyệt qua** | I07 + `on_no_approver` |
| 4 | Sửa luồng khi có 5 phiếu đang chạy → 5 phiếu đó vẫn đi theo luồng cũ tới khi kết thúc | `flow_snapshot` |
| 5 | Tạo phiếu không khớp điều kiện nhánh nào → rơi vào nhánh mặc định, **không biến mất khỏi mọi danh sách** | `is_default_branch` |
| 6 | Chạy lại 5 kiểm thử Thu mua ở N01 → **vẫn xanh** | Bộ máy mới chưa bật cho Thu mua nên không được phép ảnh hưởng gì |

### Bản 2 — KHÔNG làm trong bản 1

- [ ] [P3-v2][I13] Chuyển tiếp — người duyệt đẩy phiếu cho người khác xử lý — **M**
- [ ] [P3-v2][I14] Thêm người duyệt trước hoặc sau mình — **M**
- [ ] [P3-v2][I19] Duyệt hàng loạt — tick nhiều phiếu cùng loại — **M**
- [ ] [P3-v2][I22] Sao chép và mô phỏng luồng (chạy thử xem phiếu đi qua ai) — **M**
- [ ] [P3-v2][I24] Báo cáo duyệt: bao nhiêu phiếu, thời gian trung bình, ai tồn đọng nhiều nhất — **M**
- [ ] [P3-v2][I25] Áp cho đối tượng không phải văn bản — bật cho 5 luồng Thu mua bằng cờ — **L**

### Rủi ro riêng của phase 3

1. **Phase duy nhất có thể làm hỏng việc đang chạy.** Sáu ràng buộc bắt buộc: chỉ thêm bảng/cột — không đổi, không xóa cột đang có; bộ máy mới đứng cạnh mã cũ; mỗi việc một lần deploy riêng chứ không dồn cuối phase; deploy dev trước, theo dõi vài ngày; mỗi đợt gộp mã phải chạy đủ bộ hồi quy, đỏ là không gộp.
2. **Không có N01 thì đừng bắt đầu.** Đây là ràng buộc số 4 trong cam kết "không ảnh hưởng Thu mua", và là thứ đang thiếu.
3. **Phase 4 phụ thuộc phase 3.** Đừng hứa mốc phase 4 trước khi bộ máy duyệt có mô hình dữ liệu chạy được.

### Câu chưa có lời đáp — riêng phase 3

1. `approver_kind = 7` (cả phòng ban) có làm bản 1 không? Tài liệu liệt kê trong bảng dữ liệu nhưng I03 chỉ nói "sáu cách".
2. `multi_mode = 4` (đủ tỷ lệ `quorum`) có thật sự cần bản 1 không, hay ba chế độ đầu là đủ? I05 chỉ nói "ba chế độ".
3. Chuyển 5 luồng Thu mua sang bộ máy mới (I25) là bản 2 — vậy bản 1 bộ máy chỉ chạy cho văn thư. Có đúng ý không, hay muốn chuyển sớm một luồng Thu mua để thử thật?

## Phase 4 · Ban hành, phạm vi, clone (còn 1 việc bản 1)

- [x] [P4][F01/F02] Phạm vi áp dụng ba kiểu + bao gồm và loại trừ — **L** — xong 17/08
- [x] [P4][F03/F04] Bắt buộc kèm pháp nhân khi chọn phòng ban + áp cho cả đơn vị con — **M** — xong 17/08
- [x] [P4][F05] Màn "văn bản áp dụng cho tôi" — **S** — xong 17/08
- [ ] [P4][J05] Thông báo theo phạm vi — **S** — cần bộ thông báo, chưa làm
- [x] [P4][J02/J03] Ký điện tử nội bộ, bản ghi ký, mã băm, ghi rõ loại chữ ký — **L** — xong 17/08. J08 (ký số thật, cần USB) vẫn là dịch vụ riêng chưa làm
- [x] [P4][J04] Màn ban hành: cấp số, đóng phiên bản — **M** — xong 17/08
- [x] [P4][F06/F07/F08] Clone xuống pháp nhân con: tạo nháp, giữ liên kết ngược, số hiệu riêng — **L** — xong 17/08
- [x] [P4][F09/F10] Gửi thư kèm bản nháp + bảng theo dõi các bản clone — **M** — xong 17/08
- [x] [P4][F11] Bản gốc lên phiên bản thì đánh dấu con cần rà lại — **M** — xong 17/08
- [ ] [P4-v2][F12] Nhắc hạn với bản clone chưa xử lý — **M** — bản 2, và chờ câu B6
- [x] [P4][F13] Màn chọn cơ chế lúc ban hành: gắn phạm vi hay clone — **S** — xong 17/08
- [x] [P4][E07/E08] Cảnh báo tác động khi sửa cha + xử lý khi bãi bỏ cha — **M** — xong 17/08
- [x] [P4][J10] Nhãn "đã bị sửa đổi" trên bản cũ + tác động tự động của quan hệ thay thế/bãi bỏ — **M** — xong 17/08
- [ ] [P4][J11] Quyết định ban hành kiểm ở mức PHIÊN BẢN — **S** — phần chặn khi thiếu Quyết định đã xong 17/08; còn phần ràng buộc "sửa lớn phải kèm Quyết định mới"

## Thứ tự đề nghị

1. ~~Phase 1 — đóng phase~~ **xong 17/08**
2. Nhóm 0 (nền + test) — làm ngay, song song được với mọi thứ
3. Phase 2: quan hệ cha–con trước (E01–E06), vì nó chặn E07/E08 của phase 4
4. Phase 3 bắt đầu bằng task CHUẨN BỊ khai luồng ra giấy
5. Phase 4 chỉ khởi động sau khi phase 3 có mô hình dữ liệu

---

## Câu chưa có lời đáp

1. Bước "yêu cầu văn bản" (B01–B07) bỏ hẳn hay chỉ hoãn? Nếu bỏ hẳn thì phase 2 tính lại mẫu số, % thật sẽ lên ~55% và bớt được 1 task **L**.
2. L01 "chuyển ảnh thành văn bản" có còn trong bản 1 không, hay phần nhập .docx/.pdf đã được coi là thay thế?
3. Câu B3 (mấy mức mật, ai được cấp mức cao) đã chốt chưa — `security-level.ts` đang ghi "đang chờ chốt B3".
4. Câu B5 (bản clone có phải duyệt lại) và B6 (pháp nhân con im lặng quá lâu) đã chốt chưa — hai câu này chặn phase 4.
5. Phần "sổ văn bản" làm sớm hơn lộ trình: có kéo phase 6 (nhập sổ giấy đang dở) lên sớm không?
6. **Nghiệp vụ có phân biệt "hủy" với "bãi bỏ" không?** Tài liệu liệt kê 9 trạng thái, mã đang có 8 —
   thiếu `status = 9 đã hủy`, khác `7 bãi bỏ`. Chưa thêm vì hằng số không có nút bấm thì tạo ra trạng
   thái nửa vời. Chốt xong thì làm trọn cả luồng.
7. **Văn bản hiệu lực trong TƯƠNG LAI thì tác động thay thế bị treo.** Ba tác động tự động của J10 chỉ
   chạy khi văn bản mới thật sự có hiệu lực — ban hành hôm nay mà áp dụng từ tháng sau thì văn bản cũ
   phải còn hiệu lực nguyên tháng đó. Nhưng hiện **không có gì chạy vào ngày hiệu lực** để đổi trạng
   thái, nên nó sẽ không bao giờ chuyển. Cần một việc chạy theo lịch (mỗi ngày quét văn bản tới ngày
   hiệu lực). Băng cảnh báo trên văn bản cũ thì đã hiện đúng ngay từ lúc ban hành nên chưa gây hại.
8. **J11 mới làm được nửa.** Đã chặn: loại khai `needs_decision` mà không có quan hệ «Kèm theo» thì không
   ban hành được. Chưa làm: *"mỗi lần sửa lớn phải kèm một Quyết định MỚI, không dùng lại Quyết định ban
   hành lần đầu"* — `tab_document_link` không có chiều phiên bản nên hiện không biết Quyết định nào đã
   dùng cho bản nào. Cần chốt cách buộc: thêm `version_id` vào dòng quan hệ «Kèm theo», hay so ngày ban
   hành của Quyết định với ngày duyệt bản trước?
9. **`tab_company` chưa có cột cha.** Cờ "gồm đơn vị con" (F04) hiện hiểu là *mọi pháp nhân có `level`
   lớn hơn* — đúng với cây một tầng đang có, sai ngay khi xuất hiện tầng ba thuộc hai nhánh khác nhau.
   Muốn đúng hẳn phải thêm `parent_id` vào `tab_company`. Có 13 pháp nhân thì cây có bao giờ sâu quá
   hai tầng không?
10. **Có đổi tên `legal_issuer`/`legal_url` thành `issuer`/`external_url` như tài liệu ghi không?**
   Đang giữ tên cũ: rõ nghĩa hơn, đổi thì phải sửa cả FE mà không được thêm gì.
