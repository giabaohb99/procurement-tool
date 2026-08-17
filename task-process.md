# Đánh giá tiến độ Phase 1–4 (Văn thư) trên `frontend-v2`

- Chấm lần đầu 15/08/2026 · **cập nhật 17/08/2026** (sau khi dựng lại màn Quy tắc đánh số)
- Nhánh: `erp-v2`
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

> **Đổi gì so với lần chấm 15/08:** màn Quy tắc đánh số được dựng lại cho khớp khuôn Sổ văn bản
> (tab ra ngoài card, dùng `CatalogTable`, thêm/sửa sang trang riêng thay vì hộp thoại) và có
> 6 test đầu tiên của phân hệ. Đây là **sửa chất lượng, không thêm tính năng nào của lộ trình**
> — nên % giữ nguyên.

---

## 1. Phase 1 · Danh mục và số hiệu — ~90%

| Việc (theo PDF) | Mã | FE v2 | Bằng chứng |
|---|---|---|---|
| Bảng loại văn bản, nhập 32 loại | A01, A02 | ✅ | `document-type-catalog.tsx`, `document-type-form.tsx`; seed `backend/app/seed_data/document_phase1.py` |
| Loại thứ 33 Trích lục (`id_scheme=2`, `needs_decision=FALSE`) | C20 | ✅ | `TRICH_LUC_DOC_TYPE` trong seed |
| Mã số hiệu 13 pháp nhân + phòng ban | A04, A05 | ✅ | `modules/hr/.../company-form-dialog.tsx`, `department-form-dialog.tsx` (`issue_code`) |
| Bảng nối phòng ban ↔ pháp nhân, trưởng phòng theo từng pháp nhân | A06 | ✅ | `department-company-card.tsx` (`issue_code_override`) |
| Bộ cấp số chống trùng, hai kiểu định danh | D01–D04 | ✅ | `document-numbering-rules-page.tsx`, `document-number-preview.tsx`; BE khóa dòng `with_for_update()` |
| Văn bản hủy vẫn giữ số, cấm đổi mã sau khi cấp số | D05, D07 | 🟡 | FE có nút Bãi bỏ + trạng thái `revoked`; chặn đổi mã ở BE `issue_code_guard.py`, FE chỉ hiện lỗi |
| Danh mục đối tác, cơ quan gửi nhận | A07 | ✅ | `document-partner-catalog.tsx` |
| Tạo trước bảng phase sau: sổ đi, sổ đến | S01, S02 | ✅ (vượt yêu cầu) | Có cả UI: `document-book-page.tsx`, `book-counter-card.tsx` |
| Tạo trước bảng: xác nhận đã đọc | J06 | ❌ | Không có bảng, không có màn |
| Tạo trước bảng: văn bản pháp luật | A09 | ❌ | Chỉ có enum `origin = 2`, ghi chú "màn hình chỉ thấy 1" |

Làm thêm ngoài yêu cầu: **quyền theo sổ** và **quy tắc đánh số theo mẫu token** — thứ tài liệu xếp ở phase sau.

---

## 2. Phase 2 · Yêu cầu, soạn thảo, phiên bản — ~45%

| Việc | Mã | FE v2 | Ghi chú |
|---|---|---|---|
| Yêu cầu văn bản: ba loại, lý do bắt buộc | B01 | ❌ | Bỏ ở bản 1 — `needs_request` luôn `false` |
| Gợi ý văn bản đã có | B05 | ✅ | `document-suggestion-list.tsx` |
| Chặn soạn khi chưa có yêu cầu duyệt; loại được bỏ qua | B03, B06 | ❌ | Trường có trong DB, chưa có màn |
| Sinh bản nháp từ yêu cầu, theo dõi yêu cầu | B04, B07 | ❌ | `tab_document_request` có bảng, FE không có màn |
| Bản ghi văn bản, bộ trường chung, tệp mẫu theo loại | C01, C02 | ✅ | `document-record-form.tsx`, `document-template-catalog.tsx` |
| Phiên bản bất biến, lý do sửa, khóa sửa sau duyệt | C04, C05, C07 | ✅ | `document-version-tab.tsx`, `content_sha256` |
| Sửa văn bản đã ban hành | C13–C18 | 🟡 ~90% | `document-version-dialog.tsx`, `document-version-banner.tsx`; **C14 thiếu màn báo "ai đang giữ bản nháp"** |
| Tệp đính kèm đường riêng tư, mã băm | C03, C06 | 🟡 ~50% | Gắn theo phiên bản ✅, nhưng **vẫn dùng link công khai** `/api/attachments` |
| Ghi số hiệu cũ của văn bản giấy | C12 | ✅ | `legacy_code` |
| Quan hệ cha con | E01–E06 | ❌ | Không có bảng, không có màn |
| Bản trích nội bộ | C19 | ❌ | — |
| Quan hệ "trích từ" | E11 | ❌ | — |
| Ảnh → văn bản, ảnh gốc cạnh nháp, cờ tắt AI | L01, L02, L07 | 🟡 ~25% | Có nhập .doc/.docx/.pdf/.md/.html + truy vết chuyển đổi — **không phải ảnh/OCR** |
| Luồng duyệt yêu cầu tạm một bước | — | 🟡 50% | `submit/approve/reject` đặt trên văn bản, không phải trên yêu cầu |

---

## 3. Phase 3 · Bộ máy phê duyệt dùng chung — ~5%

Chưa bắt đầu. Không có bảng luồng/bước/phiên chạy/việc/hành động, không màn khai luồng, không "Việc của tôi".
Thứ duy nhất có là 3 nút cứng `submit → approve/reject` trên trang chi tiết — đúng bằng "luồng một bước
viết tay tạm thời" mà tài liệu xếp vào phase 2.

Chưa có: **I01–I26**.

---

## 4. Phase 4 · Ban hành, phạm vi, clone — ~6%

| Việc | Mã | FE v2 |
|---|---|---|
| Vòng đời văn bản 8 trạng thái | J01 | ✅ |
| Ban hành (cấp số, đóng phiên bản) | J04 | 🟡 có `approve → effective`, chưa có màn ban hành riêng |
| Ký điện tử nội bộ, ghi rõ loại chữ ký | J02, J03 | ❌ |
| Phạm vi ba kiểu, bao gồm/loại trừ, áp cho đơn vị con | F01–F04 | ❌ |
| Màn "văn bản áp dụng cho tôi", thông báo theo phạm vi | F05, J05 | ❌ |
| Clone xuống pháp nhân con | F06–F08 | ❌ |
| Gửi thư kèm nháp, bảng theo dõi clone | F09, F10 | ❌ |
| Bản gốc lên phiên bản → con cần rà lại | F11 | 🟡 có cờ `requires_reconfirm`, chưa có clone để áp |
| Màn chọn cơ chế lúc ban hành | F13 | ❌ |
| Cảnh báo tác động sửa cha, xử lý bãi bỏ cha | E07, E08 | ❌ |
| Nhãn "đã bị sửa đổi" | J10 | ❌ |
| Quyết định ban hành kiểm ở mức phiên bản | J11 | 🟡 chỉ có cờ `needs_decision` |

Sáu bài kiểm chuyển phase 4: **0/6**.

---

## 5. Rủi ro

1. **Đính kèm vẫn đi link công khai** (`document-attachment-list.tsx` tự ghi chú), trong khi form đã cho chọn mức "Tuyệt mật". Phase 0 (N02/N03/H01) chưa xong.
2. **Test gần như trắng.** Cả phân hệ ~9.900 dòng, mới có 1 tệp test (6 test, thêm ngày 17/08).
3. **Bỏ bước yêu cầu (B01–B07) đã thực thi trong mã** nhưng lộ trình vẫn xếp là việc phase 2 — cần chốt bỏ hẳn hay hoãn.
4. **Phase 4 phụ thuộc phase 3**, đừng hứa mốc phase 4 trước khi bộ máy duyệt có mô hình dữ liệu.

---

# DANH SÁCH TASK — copy thẳng lên Lark

Mỗi dòng là một task độc lập, đã kèm mã tính năng để tra ngược tài liệu.
Độ nặng: **S** ≤ 1 ngày · **M** 2–4 ngày · **L** ≥ 1 tuần (ước lượng thô, chưa tính review).

## Nhóm 0 · Việc nền, làm trước hoặc song song

- [ ] [P0][N02/N03/H01] Kho tệp riêng tư + link tạm có kiểm quyền, ngừng ghi link công khai — **L** — CHẶN việc đưa văn bản mật thật vào hệ thống
- [ ] [P0][C03/C06] Chuyển đính kèm văn bản sang đường tải riêng tư, hiện mã băm toàn vẹn — **M** — phụ thuộc task trên
- [ ] [P0][TEST] Viết test cho phần đã có: form văn bản, phiên bản, quyền theo văn bản — **M** — làm trước khi code thêm

## Phase 1 · Danh mục và số hiệu (còn 2 việc)

- [ ] [P1][J06] Tạo bảng "xác nhận đã đọc" — chỉ bảng, chưa màn hình — **S**
- [ ] [P1][A09] Tạo bảng "văn bản pháp luật ngoài" — chỉ bảng, chưa màn hình — **S**

## Phase 2 · Yêu cầu, soạn thảo, phiên bản (còn 9 việc)

- [ ] [P2][E01/E02] Bảng quy tắc quan hệ cha–con + 10 loại quan hệ — **M**
- [ ] [P2][E03/E04] Form tự hiện ô quan hệ theo loại + chặn gửi duyệt khi thiếu quan hệ bắt buộc — **M**
- [ ] [P2][E05/E06] Cấm vòng lặp quan hệ + màn cây tài liệu — **M**
- [ ] [P2][C19] Soạn bản trích nội bộ — tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn — **M**
- [ ] [P2][E11] Quan hệ "trích từ" + 3 ràng buộc khóa cứng + cột ghi trích từ phiên bản nào của gốc — **M**
- [ ] [P2][C14] Màn báo "ai đang giữ bản nháp" khi người thứ hai bấm mở phiên bản mới — **S**
- [ ] [P2][L01/L02] Chuyển ảnh thành văn bản (OCR) + đặt ảnh gốc cạnh bản nháp để đối chiếu — **L** — CẦN chốt câu hỏi 2 bên dưới
- [ ] [P2][L07] Cờ tắt AI — tắt là hệ thống chạy bình thường không có phần AI — **S**
- [ ] [P2][B01/B03/B04/B06/B07] Yêu cầu văn bản: 3 loại, lý do bắt buộc, chặn soạn khi chưa duyệt, sinh nháp từ yêu cầu, màn theo dõi — **L** — CHỜ chốt câu hỏi 1 bên dưới

## Phase 3 · Bộ máy phê duyệt dùng chung (14 việc — phase nặng nhất)

- [ ] [P3][CHUẨN BỊ] Khai thử 8 luồng thật ra giấy (5 luồng Thu mua + 3 luồng văn thư) bằng đúng mô hình định làm — **S** — LÀM TRƯỚC KHI VIẾT DÒNG MÃ ĐẦU TIÊN
- [ ] [P3][I01/I02] Mô hình dữ liệu: luồng, bước, phiên chạy, việc, hành động — **L**
- [ ] [P3][I21] Phiên bản của luồng — phiếu đang chạy giữ nguyên luồng cũ — **M**
- [ ] [P3][I03] Sáu cách chọn người duyệt — **L**
- [ ] [P3][I09/I10/I11] Chạy phiên: cấp việc, duyệt, từ chối, trả lại đúng bước, rút lại — **L**
- [ ] [P3][I05] Nhiều người trong một bước, ba chế độ — **M**
- [ ] [P3][I04] Rẽ nhánh theo điều kiện, có nhánh mặc định — **M**
- [ ] [P3][I06] Trùng thao tác thì bỏ qua — ba mức cấu hình — **M**
- [ ] [P3][I07] Người duyệt nghỉ việc thì chỉ định người khác — **M**
- [ ] [P3][I08/I12] Chặn tự duyệt + ủy quyền có thời hạn — **M**
- [ ] [P3][I15/I16/I17] Người nhận bản sao, ý kiến và tệp khi duyệt, màn "Việc của tôi" — **M**
- [ ] [P3][I18/I20] Hạn duyệt và nhắc + bản in dấu vết duyệt — **M**
- [ ] [P3][I23] Bàn giao hàng loạt khi có người nghỉ việc — **M**
- [ ] [P3][I26] Cờ bật tắt theo loại chứng từ — **S**
- [ ] [P3][CHUYỂN] Chuyển luồng duyệt yêu cầu văn bản ở phase 2 sang bộ máy mới — **M**

## Phase 4 · Ban hành, phạm vi, clone (12 việc)

- [ ] [P4][F01/F02] Phạm vi áp dụng ba kiểu + bao gồm và loại trừ — **L**
- [ ] [P4][F03/F04] Bắt buộc kèm pháp nhân khi chọn phòng ban + áp cho cả đơn vị con — **M**
- [ ] [P4][F05/J05] Màn "văn bản áp dụng cho tôi" + thông báo theo phạm vi — **M**
- [ ] [P4][J02/J03] Ký điện tử nội bộ, bản ghi ký, mã băm, ghi rõ loại chữ ký — **L**
- [ ] [P4][J04] Màn ban hành: cấp số, đóng phiên bản — **M**
- [ ] [P4][F06/F07/F08] Clone xuống pháp nhân con: tạo nháp, giữ liên kết ngược, số hiệu riêng — **L** — CHỜ chốt câu hỏi 4
- [ ] [P4][F09/F10] Gửi thư kèm bản nháp + bảng theo dõi các bản clone — **M**
- [ ] [P4][F11/F12] Bản gốc lên phiên bản thì đánh dấu con cần rà lại + nhắc hạn — **M**
- [ ] [P4][F13] Màn chọn cơ chế lúc ban hành: gắn phạm vi hay clone — **S**
- [ ] [P4][E07/E08] Cảnh báo tác động khi sửa cha + xử lý khi bãi bỏ cha — **M**
- [ ] [P4][J10] Nhãn "đã bị sửa đổi" trên bản cũ + tác động tự động của quan hệ thay thế/bãi bỏ — **M**
- [ ] [P4][J11] Quyết định ban hành kiểm ở mức phiên bản — **S**

## Thứ tự đề nghị

1. Nhóm 0 (nền + test) — làm ngay, song song được với mọi thứ
2. Phase 1 hai task nhỏ — đóng phase
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
