# VĂN THƯ — PHASE 0→3 · KẾ HOẠCH TRIỂN KHAI

> Full-stack (backend `backend/app` + frontend `frontend-v2`) · nguồn: `van-thu/00`–`05`
> Phạm vi: **P0 vá nền · P1 danh mục+số hiệu · P2 soạn thảo+phiên bản · P3 bộ máy phê duyệt**
> Ngoài phạm vi: P4 ban hành/clone, P5 quyền+tra cứu (chờ câu B3/B5/B6) — sẽ lên plan riêng.

## Tiến độ

| Phase | Tệp | Task | Trạng thái |
|---|---|---|---|
| 0 · Vá nền | [phase-00-va-nen.md](./phase-00-va-nen.md) | 13 | ☐ Chưa bắt đầu |
| 1 · Danh mục và số hiệu | [phase-01-danh-muc-va-so-hieu.md](./phase-01-danh-muc-va-so-hieu.md) | 14 | ☐ Chưa bắt đầu |
| 2 · Soạn thảo và phiên bản | [phase-02-soan-thao-va-phien-ban.md](./phase-02-soan-thao-va-phien-ban.md) | 18 | ☐ Chưa bắt đầu |
| 3 · Bộ máy phê duyệt dùng chung | [phase-03-bo-may-phe-duyet.md](./phase-03-bo-may-phe-duyet.md) | 18 | ☐ Chưa bắt đầu |

**63 task.** Mã task: `P{phase}-T{nn}`. Cột **L** trong từng phase: `BE` backend · `FE` frontend-v2 · `DB` migration · `∞` cả hai.

## Phụ thuộc

```
P0 ──▶ P1 ──▶ P2 ──▶ P3 ──▶ (P4)
                └────────────▶ (P5, song song được với P3)
```

- **P0 không làm song song với phase nào khác** — đụng vào nền của hệ đang chạy thật (`02` mục 15).
- P0-T01 (kiểm thử 5 luồng duyệt Thu mua) **làm đầu tiên**, không chờ trả lời câu hỏi nào.
- P2 duyệt **nội dung văn bản** bằng luồng một bước viết tay tạm thời; P3-T17 mới chuyển sang bộ máy chung.
- P1–P3 **không bị chặn** bởi 17 câu hỏi ở `00` mục 8 (chỉ chặn P4 trở đi).

## Điều kiện chuyển phase

| Từ | Sang | Điều kiện |
|---|---|---|
| P0 | P1 | 5 kiểm thử luồng duyệt xanh · link tệp cũ dán vào tab ẩn danh **không mở được** · đổi tên phòng ban không mất quyền · loại trừ phòng ban có tác dụng thật · gọi API nhật ký không quyền bị từ chối · thu hồi vai trò mất quyền trong vài giây · bản vá đã chạy prod ổn định |
| P1 | P2 | **Bài kiểm 100 kết nối cấp số** ra đúng 100 số liên tiếp · hủy văn bản không trả số về · sang năm mới sổ theo năm reset, sổ mã bất biến không reset |
| P2 | P3 | Một người đi hết đường tạo → soạn → gửi duyệt → phiên bản 2 trên dev · 5 phép thử ở `02` mục 6 đạt · ≥3 người ngoài đội phần mềm bấm thử |
| P3 | P4 | 6 bài kiểm ở `02` mục 7 đạt · **chạy lại 5 kiểm thử Thu mua vẫn xanh** |

## Quyết định đã chốt trong plan này

| # | Quyết định | Vì sao |
|---|---|---|
| 1 | `tab_file_access_log` tạo **sớm ở M1 (phase 0)** thay vì M10 | H03 "ghi nhật ký mọi lượt xem/tải" thuộc phase 0; không có bảng thì không ghi được |
| 2 | Backend đặt ở **3 module mới**: `doc_catalog`, `document`, `approval` | Theo `module pattern` của `CLAUDE.md`; không nhét vào module có sẵn |
| 3 | FE dựng trong `frontend-v2/src/modules/document` (đã có) + module mới `approval` | Tái dùng 3 danh mục (loại · mức mật/khẩn · đối tác) + data-table + conditional-filter + rich-text-editor đã có |
| 4 | `store/local-collection.ts` **gỡ dần theo từng task**, không gỡ một lần | Mỗi màn nối API xong thì bỏ collection tương ứng; tránh một PR khổng lồ |
| 5 | Bộ máy duyệt **đứng cạnh** 5 luồng viết tay của Thu mua, bật bằng cờ `I26` | `00` mục 4.7 — đường lui trong một lần bấm |
| 6 | **Soạn thảo = gõ thẳng trên web.** Bỏ cả `C02` tệp mẫu Word lẫn bộ trường nhập động | Chốt 14/08/2026: việc cơ bản nhất là người dùng **nhập văn bản bằng tay**. Không làm bảng `tab_doc_template`, không có cột `template_id`; gỡ danh mục "Trường thông tin động" đang có trong `frontend-v2`. Nội dung nằm ở `tab_document_version.content_html`, soạn bằng `rich-text-editor` (tiptap) đã có. Vẫn **giữ đính kèm tệp** — chỉ bỏ phần khai form |
| 7 | **Bỏ hẳn bước xin phép (nhóm B *Yêu cầu văn bản*).** Ai có quyền `document.create` thì tạo văn bản trực tiếp | Chốt 14/08/2026. Mất đi chốt chặn mà `00` mục 4.1 coi là quan trọng nhất — ngăn ai cũng đẻ ra quy trình rồi không ai biết cái nào đang hiệu lực; bù lại bằng **B05** (form hiện luôn văn bản cùng loại cùng phòng đang hiệu lực) và bằng chính bước duyệt nội dung ở P3. Để thêm lại sau mà không phải `ALTER` bảng nóng: **vẫn tạo bảng `tab_document_request` rỗng** ở M6, **vẫn khai** `tab_document.document_request_id` + `tab_document_version.created_from_request_id` (luôn `NULL`) và cột `doc_type.needs_request` (mặc định `FALSE`, ẩn khỏi form) |

## Rủi ro chặn cả plan

| Rủi ro | Giảm bằng |
|---|---|
| P0 làm gián đoạn Thu mua (~300 tài khoản) | P0-T01 trước tiên · mỗi task một lần deploy · dev trước prod ít nhất 1 tuần · cờ bật tắt |
| Cấp số trùng | 3 lớp: khóa dòng · UNIQUE tầng DB · cùng transaction. Bài kiểm 100 kết nối là điều kiện chuyển phase |
| Quên lọc `origin = 1` | Bộ lọc nằm ở hàm dựng truy vấn dùng chung + bài kiểm tự động (P2-T04) |
| Quên khai `SCOPE_FIELDS` cho bảng mới | Guard lúc khởi động (P0-T13): bảng có `company_id` mà chưa khai → chết ngay lúc chạy |
| Mô hình luồng duyệt không đủ mềm | **Khai thử 7 luồng ra giấy trước khi viết mã** (P3-T01) |

## Câu hỏi chưa trả lời (không chặn P0–P3)

1. ~~**B1** — form chuẩn là mẫu Word hay form web?~~ **Đã chốt 14/08/2026: không cả hai.** Người soạn gõ thẳng nội dung trên web bằng trình soạn thảo + bộ trường chung cố định `C01`. `C02` tệp mẫu Word và `C09` form web sinh thể thức đều **bỏ khỏi bản 1** — muốn làm thì đưa vào P9.
2. **B3** — 4 mức mật chốt tên gì? Plan dùng `1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật` theo `04` mục 5.2. FE hiện đang là Thường/Mật/Tối mật/Tuyệt mật → P1-T13 nắn lại.
3. **B12** — có làm loại thứ 33 *Trích lục* (C20) không? Plan chỉ làm bản trích nội bộ C19.
4. **B6** — 32 mã loại + 13 mã pháp nhân đã ai duyệt chưa? Cấp số rồi thì **không đổi mã được** (P1-T05 khóa cột).
5. ~~`frontend-v2` đã chốt thay `frontend/` chưa?~~ **Đã chốt: `frontend-v2` là FE chính thức, `frontend/` đóng băng chỉ sửa lỗi.** Cả bộ `van-thu` viết trước quyết định này nên không nhắc tới `frontend-v2` chỗ nào — đọc `01` thấy nói "màn hình của Thu mua" thì hiểu là `frontend-v2`.
   ⚠️ **Quyết định này chưa được ghi vào `doc/tai-lieu-ky-thuat/change-log.md`** — bảng quyết định hiện dừng ở **D-025**, không có D-026, và không tệp nào trong `doc/` nhắc tới `frontend-v2`. Cần ghi một dòng D-026 để lần sau không ai phải hỏi lại.

## Mức tái dùng của module `document` đang có trong `frontend-v2`

Module này dựng theo **trục sổ đến/đi** (`direction` · `book_no` · `partner_id` · `processing_status`) — thuộc nhóm S, van-thu xếp **phase 9**. Nói "đập đi làm lại" thì quá, nói "dùng lại được nhiều" cũng sai. Phân ra cho rõ:

| Phần | Số phận |
|---|---|
| 3 danh mục: loại văn bản · mức mật/khẩn · đối tác | **Giữ**, sửa trường (P1-T10, T11, T13) |
| Vỏ trang: list · detail · create · settings, breadcrumb, layout | **Giữ**, thay nội dung |
| Hạ tầng dùng chung: `data-table`, `conditional-filter`, `rich-text-editor`, `use-document-autosave`, `audit-timeline`, `notification-bell` | **Giữ nguyên**, không đụng |
| Bộ trường trên form văn bản (`DocumentRecord` ~40 trường) | **Đổi trục** (P2-T14) — phần viết lại thật sự nằm ở đây |
| Trường nhập động | **Xóa** (P2-T14b) |
| Sổ văn bản đến/đi + `direction`/`book_no`/`partner_id`/`processing_*` | **Tạm ẩn khỏi menu**, giữ mã, chờ câu A1 |
| `store/local-collection.ts` + 3 store | **Xóa dần** khi từng màn nối API |
