# PHASE 1 · DANH MỤC VÀ SỐ HIỆU

> [← plan.md](./plan.md) · Nguồn: `01` nhóm A + D, `02` mục 5, `04` mục 3.1–3.2 + 4
> Ra được: khai được 32 loại văn bản, **cấp được số không trùng**.

## Tổng quan

| | |
|---|---|
| Ưu tiên | Cao — chặn P2 |
| Trạng thái | ☐ Chưa bắt đầu |
| Mã `01` | A01–A07, D01–D08, C20 (chờ B12) |
| Migration | M2, M3, M4, M5 |

## Điểm cần biết trước

1. **`tab_company.code` KHÔNG dùng làm mã số hiệu được** — nó là mã hiển thị, chứa được dấu và khoảng trắng. Dùng nhầm sinh ra `Cty Dego-QC-012`. Phải thêm cột `issue_code` mới (chỗ dễ sai số 1).
2. **Hai kiểu định danh, không thay thế nhau:** `id_scheme = 1` mã tài liệu bất biến (`DEGO-QC-012`, không reset theo năm) · `id_scheme = 2` số hiệu theo sổ (`08/2026/TB-NS-DEGO`, reset mỗi năm). Một văn bản có thể mang cả hai.
3. **Cấp số: ba điều cấm** — cấm `MAX+1`, cấm bộ đếm ngoài DB (Redis), cấm cấp số ở giao dịch riêng rồi mới ghi bản ghi.
4. `tab_department.company_id` và `manager_id` đang có thì **giữ nguyên**, không bỏ. Bảng nối `tab_department_company` trả lời "phòng này còn có mặt ở đâu, trưởng phòng mỗi nơi là ai" — chính là thứ luồng duyệt "gửi trưởng phòng của người nộp" cần ở P3.
5. **Bảng của phase sau vẫn tạo ngay** (`tab_incoming_register`) — thêm cột vào bảng trống mất một phút, vào bảng vài chục nghìn dòng thì phải canh giờ dừng hệ thống.
6. FE hiện **tự sinh số ở client** bằng `MAX+1` (`helpers/document-number.ts`) → phải bỏ.

## Danh sách task

| Mã | L | Việc | Chi tiết |
|---|---|---|---|
| **P1-T01** | DB | **Migration M2** | `tab_company` + `issue_code VARCHAR(20) UNIQUE` (chỉ chữ và số), `short_name VARCHAR(100)`, `level TINYINT` (1 Tập đoàn · 2 công ty thành viên · 3 đơn vị trực thuộc). `tab_department` + `issue_code VARCHAR(20)`, `kind TINYINT` (1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án). Tạo `tab_department_company` (`department_id, company_id, manager_employee_id, issue_code_override, is_active`) + `UNIQUE(department_id, company_id)` |
| **P1-T02** | DB | **Migration M3** | `tab_doc_type` (**16 cột** — bỏ `template_id`, xem `04` 4.1) · `tab_doc_type_link_rule` (11 cột + `UNIQUE(source_type_id, relation, target_type_id)`) · `tab_external_party`. **Không tạo `tab_doc_template`** (quyết định 6 ở `plan.md` — soạn thảo gõ tay, không có tệp mẫu). Tất cả có `company_id` (trừ `doc_type` dùng chung) + 4 cột audit + khai vào `all_models.py` + khai `SCOPE_FIELDS` |
| **P1-T03** | DB | **Migration M4 + M5** | `tab_number_sequence` (`scope_key VARCHAR(150) UNIQUE, year SMALLINT, current_no INT`). `tab_incoming_register` — **tạo sớm, chưa có màn hình** |
| **P1-T04** | BE | **Bộ cấp số** | `modules/doc_catalog/number_service.py`: `next_number(db, scope_key, year)` dùng `with_for_update()`, tự tạo dòng khi chưa có, reset khi `row.year != year`. **Bắt buộc gọi trong cùng transaction với việc ghi bản ghi.** 3 dạng `scope_key`: `doc:{issue_code}:{mã loại}` · `out:{issue_code}:{năm}:{mã loại}` · `in:{issue_code}:{năm}` |
| **P1-T05** | BE | **Khóa mã sau khi đã cấp số** | Không cho sửa `company.issue_code` / `department.issue_code` / `doc_type.code` khi đã tồn tại `tab_number_sequence` mang mã đó. Chặn ở tầng dịch vụ + báo lỗi rõ ràng (D07) |
| **P1-T06** | BE | **Kiểm thử 100 kết nối cấp số** | `test/backend/test_number_sequence.py`: 100 luồng cùng xin cấp số cho **cùng một sổ** → đúng 100 số liên tiếp, không trùng, không nhảy cóc. **Điều kiện chuyển phase, không được bỏ qua vì "chắc là ổn"** |
| **P1-T07** | BE | **CRUD loại văn bản** | `modules/doc_catalog/{model,schema,service,controller}.py`. Loại văn bản dùng `make_crud_router` được, nhưng thêm kiểm: đổi `id_scheme` khi đã có văn bản thuộc loại → chặn. Entity `doc_type`, seed quyền cho vai trò `van_thu_admin` |
| **P1-T08** | BE | **CRUD quy tắc cha–con** | `tab_doc_type_link_rule`. **Quan hệ 10 *trích từ* khóa cứng ở tầng dịch vụ:** `on_parent_new_version = 2`, `on_parent_obsolete = 3`, `inherit_secrecy = TRUE` — API từ chối mọi giá trị khác, giao diện không cho sửa. Chặn tạo dòng trùng `(source_type_id, relation, target_type_id)` |
| **P1-T09** | BE | **CRUD đơn vị gửi nhận + phòng ban×pháp nhân** | 2 router theo `make_crud_router`. (Tệp mẫu đã bỏ khỏi bản 1 — quyết định 6) |
| **P1-T10** | FE | **Form loại văn bản mở rộng** | `modules/document/components/document-type-form.tsx` + `types/document-type.ts`: thay 6 cờ hiện tại bằng bộ trường thật của `tab_doc_type` — `group_code` (A–F), `id_scheme`, `needs_decision`, `default_secrecy`, `is_confidential_type`, `number_when`, `review_cycle_months`, `retention_months`, `default_flow_id`. **Bỏ hẳn cờ `has_template`** (không còn tệp mẫu) và **ẩn `needs_request`** (không còn bước xin phép — quyết định 7); `has_version` suy từ `id_scheme` |
| **P1-T11** | FE | **Danh mục 32 loại theo 6 nhóm** | `document-type-catalog.tsx`: gom theo `group_code`, thêm tìm kiếm. Nối react-query, **bỏ** `store/document-type-store.ts` |
| **P1-T12** | FE | **Màn quy tắc cha–con** | Màn mới `pages/link-rule-page.tsx` + `components/link-rule-table.tsx`. Mỗi dòng đọc thành một câu tiếng Việt: *"Hướng dẫn công việc — hướng dẫn — Quy trình — bắt buộc — đúng 1"*. Dòng *trích từ* hiện 3 cột khóa ở dạng chỉ đọc kèm giải thích vì sao |
| **P1-T13** | FE | **Nắn thang mức mật** | `types/security-level.ts`: thang `confidential` về đúng 4 mức `1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật`; thang `urgent` về 3 mức `1 thường · 2 khẩn · 3 hỏa tốc` theo `tab_document.urgency`. **Hai thang độc lập**, không gộp |
| **P1-T14** | FE | **Bỏ tự sinh số ở client** | Xóa `nextBookNo` khỏi `helpers/document-number.ts`, giữ `buildDocumentCode` **chỉ để xem trước** kèm nhãn "số thật cấp lúc được duyệt" (D08). Thêm ô `issue_code` vào form pháp nhân/phòng ban của module HR |

## Tệp đụng tới

**Tạo BE:** `backend/app/modules/doc_catalog/{__init__,model,schema,service,controller,number_service}.py` · `backend/migrations/versions/<M2..M5>.py` · `test/backend/test_number_sequence.py` · `test/backend/test_doc_type_link_rule.py`
**Sửa BE:** `core/all_models.py` · `core/permissions.py` · `core/scoping.py` · `app/main.py` (wire router) · `app/seed.py` + `seed_prod.py` (32 loại, 13 `issue_code`)
**Tạo FE:** `modules/document/pages/link-rule-page.tsx` · `components/link-rule-table.tsx` · `api/doc-catalog-api.ts` · `hooks/use-doc-types.ts`
**Sửa FE:** `components/document-type-form.tsx` · `document-type-catalog.tsx` · `types/document-type.ts` · `types/security-level.ts` · `helpers/document-number.ts` · `routes.tsx` · `shared/constants/app-routes.ts` · `modules/hr/components/{company,department}-form-dialog.tsx`
**Xóa FE:** `store/document-type-store.ts` (sau khi T11 xong)

## Todo

- [ ] P1-T01 · M2: `issue_code` cho pháp nhân/phòng ban + `tab_department_company`
- [ ] P1-T02 · M3: 3 bảng danh mục
- [ ] P1-T03 · M4 + M5: bộ đếm + sổ đến (tạo sớm)
- [ ] P1-T04 · `next_number()` khóa dòng, cùng transaction
- [ ] P1-T05 · Khóa mã sau khi đã cấp số
- [ ] P1-T06 · **Bài kiểm 100 kết nối — điều kiện chuyển phase**
- [ ] P1-T07 · CRUD loại văn bản
- [ ] P1-T08 · CRUD quy tắc cha–con, khóa cứng *trích từ*
- [ ] P1-T09 · CRUD đơn vị gửi nhận, phòng ban×pháp nhân
- [ ] P1-T10 · Form loại văn bản mở rộng
- [ ] P1-T11 · Danh mục 32 loại theo nhóm, nối API
- [ ] P1-T12 · Màn quy tắc cha–con
- [ ] P1-T13 · Nắn thang mức mật về 4 mức
- [ ] P1-T14 · Bỏ tự sinh số client, thêm ô `issue_code`
- [ ] Nhập 32 loại + 13 mã pháp nhân + mã phòng ban (**việc của người, làm song song được**)

## Nghiệm thu

| Bài kiểm | Kết quả phải là |
|---|---|
| 100 kết nối cùng lúc xin cấp số cho cùng một sổ | **Đúng 100 số liên tiếp**, không trùng, không nhảy cóc |
| Hủy một văn bản | Số của nó **không quay lại** cho văn bản sau (D05) |
| Đổi sang năm mới | Sổ `out:`/`in:` reset về 1 · sổ `doc:` **không reset** |
| Đổi `issue_code` của pháp nhân đã cấp số | Bị chặn, báo lỗi rõ |
| Tạo dòng quy tắc *trích từ* với `on_parent_obsolete = 1` | API từ chối |
| Tạo `tab_doc_type` nhưng quên khai `SCOPE_FIELDS` | App không khởi động (guard P0-T13) |

## Rủi ro

| Rủi ro | Mức | Giảm bằng |
|---|---|---|
| Mã 32 loại / 13 pháp nhân chưa được Pháp chế duyệt, cấp số rồi mới đổi | **Cao** | Không mở cấp số trên prod cho tới khi có bản chốt (câu B6). P1-T05 khóa cứng để không ai đổi được sau đó |
| Cấp số gọi ngoài transaction ở một chỗ nào đó | Trung bình | `next_number()` nhận `db` session đang mở và **raise nếu không trong transaction**; code review bắt buộc cho mọi chỗ gọi |
| Seed prod ghi đè danh mục đã sửa trên UI | Trung bình | Theo `CLAUDE.md`: `seed_prod.py` **không ghi đè**; chỉ áp lại khi bật `SEED_FORCE_SYNC=true` |
| Chữ tiếng Việt trong seed bị mojibake | Trung bình | Nạp bằng migration/script Python, **cấm** `docker compose exec db mysql -e "..."` |

## Bảo mật

- Bảng danh mục mới đều phải khai trong `SCOPE_FIELDS`, kể cả khi phạm vi là "mọi người đọc được" — khai tường minh chứ không để trống (chỗ dễ sai số 6).

## Tiếp theo

[Phase 2 · Soạn thảo và phiên bản](./phase-02-soan-thao-va-phien-ban.md) — chỉ bắt đầu khi bài kiểm 100 kết nối đạt.
