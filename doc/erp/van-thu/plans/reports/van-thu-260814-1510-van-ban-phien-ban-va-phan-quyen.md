# VĂN THƯ — VĂN BẢN, PHIÊN BẢN VÀ PHÂN QUYỀN THEO TỪNG VĂN BẢN

> Ngày 14/08/2026 · nhánh `frontend-v2` · theo [plan P0–P3](../260814-1036-van-thu-p0-p3/plan.md) bước 3b + 3c
> Trạng thái: **chạy được đầu–cuối trên dev.** 484/484 test backend xanh · typecheck + build frontend sạch.

## 1. Làm được gì

Một người đi hết đường: **tạo văn bản → chọn loại → gõ nội dung trên web → đính tệp → gửi duyệt → duyệt (hệ cấp số) → mở phiên bản 2.0**, bản 1.0 khóa vĩnh viễn mà văn bản vẫn có hiệu lực.

Kèm hai thứ vốn thuộc P5, làm sớm theo yêu cầu trong lúc chạy: **quyền trên từng văn bản** và **quyền theo sổ**.

| Đường đã thông | Kiểm chứng trên dev |
|---|---|
| Xem trước số hiệu | `01/2026/TB-DEGO` hiện ngay khi chọn loại + pháp nhân, **không chiếm số** |
| Cấp số lúc duyệt | Nháp không có số → duyệt xong mang `01/2026/TB-DEGO`; văn bản sau lấy số kế tiếp |
| Mã tài liệu bất biến | Loại `id_scheme = 1` ra `DEGO-QC-001`, không đếm lại theo năm |
| Vào sổ | Cấp thêm số thứ tự trong sổ `VBĐ 02/2026` — **hai số khác nhau, cố ý** |
| Phiên bản | Mở 2.0 → chép nội dung + đính kèm; người thứ hai bấm nhận *"Bản nháp 2.0 đang do Dego Admin giữ"* |
| Bất biến hóa | `PATCH` lên bản đã duyệt → **409**, kể cả gọi thẳng API |
| Không nhầm trạng thái | Bản 2.0 đang duyệt → văn bản **vẫn "Có hiệu lực"**, vẫn hiện bản 1.0 |
| Chia quyền | Chia cho một người ngoài phạm vi → họ thấy; cấm đích danh → biến mất khỏi danh sách của chính người tạo |

## 2. Ba lớp quyền, thứ tự quyết định

```
CẤM đích danh          →  KHÔNG được, dừng luôn (kể cả người tạo, kể cả admin)
CHO PHÉP đích danh     →  được
THÀNH VIÊN SỔ chứa nó  →  được (quản lý sổ: xem + sửa · người xem sổ: xem)
phạm vi vai trò        →  được
còn lại                →  không được
```

| Lớp | Trả lời câu hỏi | Ở đâu |
|---|---|---|
| Vai trò | được đụng vào *loại việc* văn bản không | `core/permissions.py` — entity `document` |
| Phạm vi | trong đó thấy *nhóm* nào | `core/scoping.py` — pháp nhân ban hành · phòng chủ trì · người tạo |
| **Từng văn bản** | riêng *văn bản này* mở thêm / khóa bớt cho ai | `document/access_service.py` |

Bốn điều cố ý:

1. **Cấm thắng cho phép** và thắng cả phạm vi vai trò — cấm mà vẫn đọc được vì tình cờ có một vai trò rộng thì nút "cấm" vô nghĩa.
2. **Không đọc được → 404, không phải 403.** 403 đã là xác nhận "có văn bản này" — riêng việc đó đã lộ (K03).
3. **Thu hồi là đánh dấu, không xóa dòng** — câu người ta hỏi khi có chuyện là *"hồi tháng 7 ai đọc được văn bản này"*.
4. **Cấp cho bốn loại đối tượng** (người · phòng · pháp nhân · vai trò) + **theo sổ** — chia cho cả phòng mà phải chọn từng người thì người mới vào phòng không có quyền, người chuyển đi vẫn còn.

Áp ở **cả hai chỗ**: `visible_condition()` cho danh sách, `ensure_can()` cho từng bản ghi. Lọc danh sách mà quên kiểm chi tiết thì gõ id lên URL là mở được.

## 3. Tệp đã đụng

**Backend mới** — `modules/document/`: `model.py` · `version_model.py` · `request_model.py` (bảng rỗng, cố ý) · `access_model.py` · `query.py` · `numbering.py` · `service.py` · `version_service.py` · `access_service.py` · `serializer.py` · `schema.py` · `controller.py`
**Backend sửa**: `core/{permissions,scoping,all_models,file_registry,crud}.py` · `main.py` · `seed.py` · `company/{model,schema,service}.py` · `department/{model,schema,service}.py` · `doc_catalog/{controller,model,book_model}.py` + `issue_code_guard.py` (mới)
**Migration**: `32f20b5057fc` (M6 + `issue_code` cho pháp nhân/phòng ban) · `a41c7d5e9b02` (bảng quyền)
**Test mới**: `test_document.py` (15) · `test_document_version.py` (11) · `test_document_access.py` (22)

**Frontend** — mới: `api/document-api.ts` · `hooks/use-document-{versions,access}.ts` · `types/document-access.ts` · `components/document-{version-tab,version-dialog,version-banner,access-card,access-dialog,suggestion-list,number-preview}.tsx`
Viết lại: 3 trang (danh sách/tạo/chi tiết) · `document-record-form` · `document-{main,extra}-info-fields` · `document-attachment-list` (nối API thật) · `book-entries-card` · `types/document-record.ts` · `schemas` · `helpers`
Xóa: `store/document-record-store.ts` · `helpers/document-number.ts` (client tự sinh số) · 5 component của trục sổ đến/đi cũ

## 4. Chỗ cố ý làm khác, ghi để khỏi tưởng là sai

| Chỗ | Làm gì | Vì sao |
|---|---|---|
| `open_slot` | Cột SINH + UNIQUE ở tầng dữ liệu | Hai người bấm "mở phiên bản mới" cùng lúc thì hai câu kiểm trong mã đều thấy trống rồi cùng ghi |
| `tab_document_access` | **Không** có UNIQUE cho "một dòng đang sống" | `revoked_at IS NULL` thì UNIQUE không chặn được; cột sinh thì hàm nối chuỗi MySQL ≠ SQLite nên test không chạy. Chống trùng ở `grant()` |
| Ngày hiệu lực tương lai | `activate_due_versions()` gọi ở đường đọc chi tiết + một endpoint bảo trì | Hệ chưa có bộ chạy định kỳ; việc cần làm chỉ là một câu lọc theo ngày |
| Đính kèm | Treo vào **phiên bản**, không vào văn bản | Bản đã duyệt phải tra ra đúng bộ tệp lúc duyệt, kể cả sau khi bản mới gỡ bớt |
| Migration M6 | Viết tay, có `DROP TABLE IF EXISTS` | Vài máy dev còn sót ba bảng `tab_document*` của bản dựng thử theo trục sổ (migration đã revert, tệp không còn trong git nhưng bảng vẫn nằm trong DB) |

## 5. Việc dev tôi đã đụng vào, cần biết

- **DB local lệch revision.** Máy này đang ở `6e12efeff5af` — một migration **không có trong git**, do bản dựng thử trước để lại kèm 1 văn bản mẫu. Đã trỏ `alembic_version` về `7c31d0a94ef5` rồi chạy tiếp; migration mới tự dọn ba bảng cũ. **Máy khác cũng dính thì làm y vậy.** Dev/prod không ảnh hưởng — migration đó chưa từng lên.
- Dữ liệu mẫu localStorage (`erp.document-records.v2`) không dùng nữa; mẫu giờ nằm ở `app/seed.py` (chỉ local, `seed_prod.py` không gọi).
- `company.issue_code` được seed tự điền từ `code` khi mã đó vốn chỉ có chữ và số. Mã có dấu thì để trống — Hành chính khai tay, và **khai xong cấp số rồi thì khóa** (P1-T05).

## 6. Chưa làm — theo đúng thứ tự nên làm tiếp

| Việc | Mã | Ghi chú |
|---|---|---|
| Quan hệ cha–con + cây tài liệu | P1-T08, P1-T12, P2-T02, P2-T17, P2-T19 | Bước 3d của plan. `tab_document_link` chưa tạo |
| Bản trích nội bộ | P2-T18, P2-T20 | Chờ 3d |
| OCR ảnh → nháp | P2-T21 | Tùy chọn, bỏ không ảnh hưởng nghiệp vụ nào |
| **Kho tệp riêng tư + link tạm** | P0-T02…T04 | Đính kèm đang đi `/api/attachments` chung, link công khai |
| 7 task P0 chặn prod | P0-T01, T05–T09, T13 | **Chưa động tới.** Chưa xong thì không mở tài khoản văn thư trên prod |
| Lớp kiểm mức mật | P5 | Cột `secrecy_level` đã ghi nhưng **chưa ai chặn theo nó** |
| Bộ máy duyệt dùng chung | P3 | Đang dùng luồng một bước viết tay, gói trong 3 hàm `submit`/`approve`/`reject` |

⚠️ **Ràng buộc không đổi:** cho tới khi 7 task P0 xong và lớp mức mật (P5) chạy — **không đưa văn bản mật thật vào hệ thống**, kể cả trên dev.

## 7. Câu hỏi chưa trả lời

1. **B6** — 32 mã loại + 13 mã pháp nhân đã ai duyệt chưa? Cấp số trên prod rồi là khóa mã, không đổi được (đã cài chặn ở `issue_code_guard.py`).
2. **A1** — sổ văn bản đến có vào bản đầu không? Sổ đã giữ lại và đã thành nguồn quyền, nhưng `direction` / `external_party_id` / `processing_*` trên văn bản thì vẫn chưa làm.
3. Vai trò văn thư (`van_thu_admin` mà `van-thu/01` nhắc tới) **chưa seed** — hiện chỉ `admin` và `pur_manager` có quyền trên entity `document`. Có cần một vai trò riêng không?
4. Người **quản lý sổ** hiện chỉ được xem + sửa văn bản trong sổ, **không được xóa**. Đúng ý chưa?
5. Ai được bấm "Duyệt và ban hành"? Hiện là bất cứ ai có `document.approve` và đọc được văn bản — chưa có khái niệm "người duyệt của phiếu này" (đó là P3).
