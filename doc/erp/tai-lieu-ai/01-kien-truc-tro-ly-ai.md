# Trợ lý AI — Chức năng và phân quyền

Phiên bản: **15/09/2026** (bản đầu 25/08/2026). Trạng thái: **ĐÃ CODE, đang chạy dev + prod**.
Mã nguồn: `backend/app/modules/assistant/` · giao diện `frontend-v2/src/modules/assistant/`.
Bối cảnh lộ trình: `doc/erp/02-dai-han.md` §3.7 (AI-1 ở đây đã chạy; **AI-2** — RAG toàn hệ có lọc
quyền per-record — vẫn là kế hoạch).

> ⚠️ Bản trước của tệp này ghi *"thiết kế nền, chưa code"* và mô tả bốn tool gợi ý. Nay đã có
> **36 tool**, tầng ghi có xác nhận, kho vector và hạn mức chi phí. Ba chỗ bản cũ nói **ngược
> với mã đang chạy** đã sửa ở đây, đánh dấu «ĐÍNH CHÍNH» — đừng trích lại bản cũ.

Bốn tệp, đọc theo nhu cầu:

| Tệp | Trả lời câu hỏi |
|---|---|
| **`01` (tệp này)** | Trợ lý làm được gì, ai được dùng, quyền chặn ở đâu |
| `02-danh-sach-api-tool.md` | Từng tool: tham số, đầu ra, nguồn dữ liệu (T1…T48) |
| `03-lo-trinh-phase.md` | Phase nào xong, phase nào nợ, các quyết định đổi hướng |
| `04-bao-mat-va-van-hanh.md` | Bảng quyền **từng tool**, bảy tầng bảo vệ, test canh |

---

## 1. Phạm vi

Trợ lý hỏi–đáp tiếng Việt, nằm **trong** ERP (`/assistant`), không phải app riêng. Hai nhóm nhu cầu:

- Tra cứu dữ liệu nghiệp vụ trong **phạm vi người hỏi vốn được xem** (hợp đồng, giá, lịch sử mua,
  công nợ, văn bản, phiếu đang chờ ký…).
- Hiểu và vận dụng quy trình nhà máy / phân hệ, dựa trên gói tri thức biên soạn tay.

Hiện mở cho **ban lãnh đạo** (§6). Mở rộng cho nhân viên là việc của phase sau, chặn bằng chi phí
chứ không phải bằng kỹ thuật.

---

## 2. Nguyên tắc cốt tử — HAI loại câu hỏi, HAI cơ chế

Quyết định kiến trúc quan trọng nhất, vẫn nguyên giá trị:

| | Loại A — dữ liệu CÓ CẤU TRÚC | Loại B — văn bản TỰ DO |
|---|---|---|
| Ví dụ | *"HĐ nào còn hạn"*, *"mã A giá tốt nhất, mua của ai"* | *"quy trình nghiệm thu mấy bước"* |
| Nguồn | Bảng nghiệp vụ, qua **tool** | Bài HDSD + FAQ, qua **vector Qdrant** |
| Vector hóa | **KHÔNG** | CÓ |
| Phân quyền | `ctx.can` + `apply_scope` trong từng tool | ⚠️ **chưa có** — xem §6.5 |

Vì sao **không** vector hóa dữ liệu loại A: vector tìm theo "gần nghĩa", không lọc–tính–tổng hợp
chính xác được; số liệu đổi mỗi ngày còn vector là ảnh chụp cũ; và bản chụp vector **mất lớp
`apply_scope`**. Truy vấn nào quá nặng thì tối ưu bằng bảng tổng hợp / cache — vẫn là dữ liệu có
cấu trúc, tính lại được, gác quyền được — **không** bằng vector. (Chốt 25/08/2026, giữ nguyên.)

---

## 3. Luồng một lượt hỏi (đúng mã đang chạy)

```
Người hỏi (đã đăng nhập, mang JWT của CHÍNH MÌNH)
   │
   ├─ cổng 1: cờ AI_ENABLED           → tắt thì 403
   ├─ cổng 2: require("assistant","read") → thiếu thì 403
   ├─ cổng 3: hạn mức ngày (AI_DAILY_MSG_LIMIT) → vượt thì 429
   │
   v
[ system = DEFINITION + gói tri thức packs/ + ngữ cảnh người hỏi ]  ← prompt caching
   │
   v
[ Provider: Claude hoặc Gemini ]  ── function calling ──┐
   │                                                    │
   │  loại A → run_tool(db, user, name, args)           │  chạy DƯỚI danh tính người hỏi
   │             ├ allowlist 36 tool                    │  ctx.can(entity) + apply_scope
   │             └ audit: ai gọi tool nào, mấy dòng     │
   │  loại B → search_docs → Qdrant (HDSD + FAQ)        │
   v                                                    │
[ Model tổng hợp câu trả lời ] <─────────────────────────┘
   │
   v
Lưu vào tab_assistant_conversation / tab_assistant_message (kèm token đã dùng)
```

**Bot không có tài khoản riêng.** Không tồn tại service account đặc quyền — nếu có thì
`apply_scope` thành vô nghĩa. Cùng một câu hỏi, hai người khác quyền nhận hai kết quả khác nhau.

---

## 4. Chức năng — người dùng làm được gì

| Nhóm | Chi tiết | Endpoint |
|---|---|---|
| **Hỏi đáp** | Chat nhiều lượt, giữ ngữ cảnh hội thoại | `POST /api/assistant/chat` |
| **Hội thoại** | Danh sách · mở lại · xóa. **Chỉ chính chủ** (`created_by`) | `GET/DELETE /api/assistant/conversations…` |
| **Đính kèm** | Ảnh JPG/PNG/WebP ≤ 5MB, PDF ≤ 10MB; tải trước, gắn sau. Nhận dạng bằng **magic bytes**, không tin `content-type` của client | `POST /api/assistant/uploads` |
| **Soạn nháp phiếu** | YCBG · YCMH · đơn nghỉ phép · YCTT — trả **bản nháp**, người dùng tự rà rồi tự tạo | tool `draft_*` |
| **Sửa phiếu có xác nhận** | Trợ lý đề xuất, **người bấm nút** mới ghi (§6.4) | `POST /api/assistant/confirm-update` |
| **Xuất báo cáo** | Sinh tệp DOCX/Excel, **chỉ chủ tệp tải được** | tool `export_*` + `GET /files/{id}/download` |
| **Hạn mức của tôi** | "Còn N câu hôm nay" | `GET /api/assistant/usage/mine` |
| **Soi chi phí** | Token + số câu theo ngày / theo người | `GET /api/assistant/usage` |
| **Nạp lại chỉ mục** | Dựng lại vector HDSD + FAQ, chạy nền qua Celery | `POST /api/assistant/rag/reindex` |

Giao diện: một trang `/assistant` (`assistant-page.tsx`) + widget nổi. Phân hệ khai
`entity: 'assistant'` ở `module-registry.ts` nên **thẻ và mục menu tự ẩn** với người không có quyền.

---

## 5. Bốn thành phần

### 5.1. System prompt + gói tri thức (AI-1)

`knowledge.py` ghép `DEFINITION` (vai trò + rào an toàn) với **mọi tệp `.md`** trong
`packs/` theo thứ tự tên tệp (trừ `README.md`), nạp vào phần `system` mỗi lượt, bật prompt caching.

Bảy gói hiện có, ~24 000 token: thu mua · văn thư · dự án · nghỉ phép · đặt phòng họp · hồ sơ nhân
sự · nhà máy DEGO Organic.

⚠️ **Gói đi vào MỌI câu hỏi**, kể cả câu chẳng liên quan. Nên gói chỉ chứa **LUẬT mà trợ lý nói
sai thì người dùng làm hỏng dữ liệu thật** (ví dụ *"đổi tên một chức vụ là đổi luôn chức danh của
mọi người đang giữ nó"*). Các bước bấm nút nằm ở Help Center, trợ lý tra bằng `search_docs`.

⚠️ Bộ nạp **đọc lại đĩa mỗi lượt** — sửa gói là có hiệu lực ngay, không cần restart.
⚠️ Sửa tài liệu chức năng của một phân hệ thì xem luôn gói tương ứng (`doc/README.md` dòng 13):
lệch nhau là trợ lý trả lời sai mà không ai biết.

### 5.2. Bộ tool loại A — 36 tool

**ĐÍNH CHÍNH.** Bản cũ liệt kê 4 tool "gợi ý". Thực tế 36 tool, khai ở
`tools/catalog.py` + 12 tệp `*_tool.py`, chia theo nhóm:

| Nhóm | Tệp | Tool |
|---|---|---|
| Thu mua, giá, danh mục, thống kê | `catalog.py` | 13 |
| Văn bản + phê duyệt | `document_tool.py`, `approval_tool.py` | 6 |
| Soạn nháp phiếu | `draft_tool.py` | 3 |
| Xuất tệp | `export_tool.py` | 2 |
| Công nợ + YCTT | `payable_tool.py` | 3 |
| Chứng từ thu mua cho quản lý | `procurement_doc_tool.py` | 3 |
| Phiếu hỗ trợ | `ticket_tool.py` | 2 |
| Nghỉ phép · hồ sơ nhân sự | `leave_tool.py`, `employee_tool.py` | 2 |
| Sửa phiếu có xác nhận | `update_tool.py` | 1 |
| Tìm tài liệu (loại B) | `rag_tool.py` | 1 — chỉ khi `AI_RAG_ENABLED` |

Chi tiết từng tool: `02-danh-sach-api-tool.md`. Quyền từng tool: `04-…md` §5.

### 5.3. Kho vector Qdrant (loại B)

Nguồn index: **bài HDSD (`help_article`) + FAQ**, cắt đoạn ở `rag/chunker.py`, lưu Qdrant
(`QDRANT_URL`). Nạp lại chạy **nền qua Celery**, không chờ trong request.

⚠️ **ĐÍNH CHÍNH — embedding gọi API Gemini, KHÔNG chạy local.** Bản cũ ghi *"embedding chạy LOCAL
(bge-m3 / multilingual-e5) để không gửi văn bản nhạy cảm ra ngoài"*. Quyết định đổi ngày
26/08/2026 (`03-…md` §Phase 3): VPS chật RAM, mà nội dung loại B hiện là HDSD/FAQ — **công khai
với mọi người đăng nhập** — nên gửi đi nhúng không phát sinh rủi ro mới. Model
`AI_EMBED_MODEL = gemini-embedding-001`, `AI_EMBED_DIM = 768`.
Muốn giữ trong nhà (khi index Văn thư) thì thêm `LocalEmbedder` và đổi `get_embedder()`.

⚠️ **Đổi model nhúng ⇒ vector cũ không so được với vector mới ⇒ PHẢI reindex toàn bộ.**

### 5.4. Lớp provider — Claude và Gemini

App **không** gọi thẳng SDK nhà nào; luôn qua `provider/` (`base.py` + `claude.py` + `gemini.py`).

| Cờ | Mặc định |
|---|---|
| `AI_DEFAULT_PROVIDER` | `claude` |
| `AI_CLAUDE_MODEL` | `claude-sonnet-5` |
| `AI_GEMINI_MODEL` | `gemini-flash-latest` |
| `AI_LOOKUP_MODEL` | rỗng — đặt thì câu tra cứu rẻ đi model nhẹ hơn |

⚠️ `AI_LOOKUP_MODEL` phải là model **cùng nhà** với `AI_DEFAULT_PROVIDER` đang dùng.
(Bản cũ ghi mặc định `claude-opus-5` — không còn đúng.)

---

## 6. Phân quyền

### 6.1. Ba cổng vào

1. **Cờ máy chủ `AI_ENABLED`** — tắt thì **mọi** endpoint trả 403, kể cả admin. Công tắc tổng.
2. **Khóa quyền `assistant`** — `require("assistant", "read")` trên mọi endpoint chat.
3. **Hạn mức ngày** — `AI_DAILY_MSG_LIMIT` (mặc định **50** câu/người/ngày), kiểm **trước** khi
   gọi model, vượt thì **429**. Đây là guard chi phí, không phải guard bảo mật.

`assistant` khai **`PUBLIC`** ở `SCOPE_FIELDS` — `apply_scope` không lọc gì cho chính entity này,
vì phạm vi thật nằm ở entity của **dữ liệu được tra**, không ở bản thân con bot.

### 6.2. Ai có quyền (seed chuẩn)

| Vai trò | `assistant.read` | Đường cấp |
|---|---|---|
| **Admin** | có | `ensure_admin_role` cấp mọi action mọi entity |
| **Quản lý công ty** (`company_head`) | có | khai **tường minh** trong `STD_ROLES` |
| **Quản lý thu mua** (`pur_manager`) | có | **ngầm** qua `_PUR_MANAGER_PERMS` |
| Còn lại | không | — |

⚠️ **`pur_manager` có quyền ngầm vì `assistant` KHÔNG nằm trong `_SYS_ENTITIES`.**
`_PUR_MANAGER_PERMS = {e: (_ALL_ACTIONS, "all") for e in ENTITIES if e not in _SYS_ENTITIES}`, nên
vai trò đó nhận **cả 8 action** của `assistant`, trong đó có **`export`**. Hệ quả: docstring của
`GET /api/assistant/usage` ghi *"Chỉ admin"* là **SAI** — Quản lý thu mua cũng mở được bảng chi phí
toàn hệ (token + số câu **của mọi người**). Muốn đóng thì thêm `"assistant"` vào `_SYS_ENTITIES`
rồi cấp lại tường minh cho đúng vai trò.

⚠️ Trên hệ **đang chạy**, seed **không ghi đè** phân quyền đã sửa trên UI (D-018). Thêm/bớt ở đây
phải tick tay ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần rồi trả về `false`. Người
**đang đăng nhập** giữ map quyền cũ tới khi đăng xuất/đăng nhập lại.

### 6.3. Hai lớp quyền bên trong mỗi tool

`assistant.read` chỉ mở **cửa vào phòng chat**. Nó **không** cho xem thêm bất cứ dữ liệu nào:
mỗi handler tự kiểm lại bằng khóa của **phân hệ bị tra**.

| Tool nhóm | Khóa kiểm |
|---|---|
| Hợp đồng / NCC / sản phẩm / đơn mua | `contract` · `supplier` · `product` · `purchase_order` |
| Văn bản · luồng duyệt | `document` · `approval_flow` |
| Công nợ · YCTT | `payable` · `payment_request` (+ `.create` khi soạn nháp) |
| Soạn nháp | `purchase_request.create` · `survey_request.create` · `leave_request.create` |
| Phiếu hỗ trợ | `ticket.read` · `ticket.create` |
| Nghỉ phép · nhân sự | `leave_request` · `employee` |

Ba luật của tầng này:

- **Thiếu quyền trả `denied` tường minh**, không trả rỗng lặng lẽ — rỗng thì model tưởng "không có
  dữ liệu" và nói sai; `denied` thì model nói "bạn không đủ quyền".
- **Cắt cột thay vì chặn cả tool** khi hợp lý: thiếu `supplier.read` thì `product_purchase_history`
  vẫn chạy nhưng **tên/mã NCC bị cắt ngay ở backend** (`see_supplier` trong `catalog.py`) — dữ
  liệu NCC **không hề đi vào model**, nên model không thể lỡ miệng.
- **`apply_scope` nguyên vẹn**, kèm hàng rào B-07: entity thiếu khai scope là **chặn** (`false()`),
  không phải "thấy hết".

### 6.4. Tầng GHI — ĐÍNH CHÍNH luật "read-only"

Bản cũ ghi *"tầng 4: read-only, bot chỉ gọi tool ĐỌC, cấm ghi"*. **Không còn đúng** từ CR-218.
Luật hiện tại chặt hơn "read-only" ở chỗ nó nói rõ ai bấm nút:

- Tool `propose_document_update` **tự nó không ghi gì**: trả bản so sánh cũ → mới + một
  `confirm_token` (Fernet ký từ `JWT_SECRET`, **hết hạn 15 phút**, buộc vào đúng người hỏi).
- **NGƯỜI** bấm *Xác nhận sửa* thì FE mới gọi `POST /confirm-update`; backend **kiểm lại toàn bộ
  từ đầu** (quyền `<entity>.write` + phạm vi + trạng thái phiếu còn sửa được + whitelist trường)
  rồi ghi **qua đúng service của form** để validate + audit nguyên vẹn.
- Token là *tờ đề xuất có hạn dùng*, **không phải giấy thông hành** — phiếu đổi trạng thái hoặc
  quyền bị thu hồi giữa hai bước thì lần xác nhận vẫn trượt.
- Phạm vi đợt 1 chỉ **đầu phiếu**: YCMH (`purpose` · `need_date` · `note`) · YCBG (`purpose` ·
  `note`) · YCTT (3 câu chữ bản in). **Không đụng dòng hàng** — sửa dòng vẫn phải mở form.
- `ticket_create` cũng là đường ghi thật, gác bằng `ticket.create`.

### 6.5. ⚠️ Khoảng hở đã biết — RAG loại B KHÔNG lọc quyền

Bản cũ mô tả *"mỗi chunk nạp kèm nhãn quyền, lọc theo quyền TRƯỚC khi đưa cho Claude"*. Đó là
**thiết kế, chưa phải hiện thực**: `rag/search.py` **không nhận `user`**, không có nhãn quyền,
không gọi `apply_scope`. Ai qua được `assistant.read` thì `search_docs` trả về **mọi** đoạn đã
index.

Hiện **an toàn**, vì corpus chỉ có `help_article` + FAQ — chủ đích mở cho mọi người đăng nhập.

**Nhưng đây là bẫy nổ chậm.** Ngày ai đó index Văn thư / hợp đồng / tài liệu mật vào cùng bộ sưu
tập, nó rò cho mọi người có `assistant.read` **mà không có dòng mã nào đỏ lên** — không 403,
không log, không test đỏ. Điều kiện bắt buộc trước khi mở nguồn mới: gắn nhãn quyền vào payload
Qdrant + lọc theo quyền người hỏi trong `search_docs`, **dùng lại hệ hai trục sẵn có**, không đẻ
luật quyền song song.

### 6.6. Quyền riêng của vài endpoint

| Endpoint | Khóa | Ghi chú |
|---|---|---|
| `GET /usage` (chi phí toàn hệ) | `assistant.export` | Ý định là admin — thực tế `pur_manager` cũng có, xem §6.2 |
| `POST /rag/reindex` | **`help_article.write`** | Cố ý **không** dùng `assistant`: người quản nội dung HDSD mới là người cần bấm |
| `GET /uploads/{id}` | sở hữu | Chính chủ + key thuộc `assistant-upload/` |
| `GET /files/{id}/download` | sở hữu | `created_by` = người hỏi + key thuộc `assistant-report/` |
| `GET/DELETE /conversations` | sở hữu | Hội thoại của chính mình |

⚠️ Hai endpoint tệp gác bằng **quyền SỞ HỮU**, không qua module attachment (tệp không gắn chứng
từ nào nên không có `FileLink`). Kiểm thêm **tiền tố thư mục** để endpoint không thành lối tải
chung cho mọi tệp người đó từng đính kèm nơi khác.

### 6.7. Dấu vết

`run_tool` ghi audit **mỗi lần gọi tool**: ai gọi, tool nào, tham số, số dòng trả về, có bị
`denied` không — entity `assistant`, action `tool:<tên>`. Audit hỏng **không** làm sập lượt chat
(bọc `try` + `rollback`).

### 6.8. Hai luật khách chốt 15/09/2026 — tài khoản CHỈ CÓ QUYỀN XEM

Hai câu hỏi thực tế, trả lời bằng mã đang chạy chứ không bằng lời hứa. Test canh:
`test/backend/test_assistant_chi_co_quyen_xem.py` (13 ca).

**(a) Chỉ có quyền xem mà trong chat xin TẠO / SỬA / XÓA → chặn.**

Quyền nằm ở backend, **không** nằm ở câu chữ người dùng gõ. Model không có đường ghi nào
ngoài allowlist, và mọi tool ghi tự đòi đúng khóa **trước khi làm gì khác**:

| Tool | Đòi | Chốt tại |
|---|---|---|
| `propose_document_update` | `<entity>.write` | `update_tool.py` `_run_propose` |
| `confirm_update` (nút Xác nhận) | `<entity>.write` — **kiểm lại từ đầu** | `update_tool.py` `confirm_update` |
| `draft_purchase_request` · `draft_survey_request` · `draft_leave_request` | `<entity>.create` | `draft_tool.py` |
| `draft_payment_request` | `payment_request.create` | `payable_tool.py` |
| `ticket_create` | `ticket.create` | `ticket_tool.py` |

⚠️ **KHÔNG tool nào ghi dữ liệu nghiệp vụ** — kể cả `ticket_create`, tên nghe như tạo
phiếu nhưng nó chỉ trả bản nháp để giao diện mở form điền sẵn. Rà cả lớp `tools/`: chỗ
duy nhất `db.commit()` là `export_tool` ghi một dòng `StoredFile` cho tệp người dùng vừa
xuất. **Đường ghi duy nhất của cả phân hệ là endpoint `/api/assistant/confirm-update`,
và nó chỉ chạy khi NGƯỜI bấm nút Xác nhận.** Model không có nút nào để bấm.

**XÓA: chặn bằng cách KHÔNG CÓ tool nào xóa** — chắc hơn gác quyền. Lý do: xóa không lùi
được, mà lời gõ cho model thì luôn mơ hồ (*"bỏ cái phiếu kia đi"* là hủy, là xóa dòng, hay
xóa cả phiếu?). Có bài kiểm quét allowlist, ai thêm tool xóa thì đỏ và phải giải trình.

⚠️ **Soạn nháp cũng đòi `create`** dù bản thân tool không ghi gì xuống bảng: bản nháp mở
sẵn form kèm dữ liệu là **một nửa bước tạo phiếu**, mà người không có quyền tạo thì nửa
bước đó chỉ dẫn tới một nút bấm sẽ 403.

**(b) "Tóm tắt phiếu X" cũng phải đi qua phân quyền.**

Trợ lý **chỉ tóm tắt được thứ tool trả về**. Không có đường nào khác — model không nối vào
DB. Nên luật nằm ở chỗ tool lấy bản ghi:

- **Tuyệt đối không `db.get` trần** khi lấy một chứng từ theo mã/id. Đi qua
  `apply_scope` (`procurement_doc_tool._fetch_scoped`, `payable_tool`), `get_scoped`
  (`update_tool.confirm_update`), hoặc chốt per-record của phân hệ
  (`document_tool` dùng `access_service.can` cho từng văn bản).
- Ngoài phạm vi thì trả **"không tìm thấy… trong phạm vi dữ liệu của bạn"**, không trả
  nội dung — và **câu báo lỗi cũng không được chứa mẩu nào của phiếu đó**.
- Hai trục chặn **độc lập**: thiếu khóa phân hệ → `denied` (trục vai trò); có khóa nhưng
  ngoài phạm vi → "không tìm thấy" (trục dữ liệu). Gộp một là mất một lớp.

⚠️ Đây là chỗ **dễ tưởng an toàn mà không phải**. Chữ *"tóm tắt"* nghe như thao tác đọc vô
hại, nên tool tóm tắt hay được viết vội bằng `db.get(Model, id)`; lúc đó chỉ cần đọc đúng
mã phiếu là moi được nội dung của phòng khác, **qua miệng trợ lý**, không lần vết nào trên
màn hình.

---

## 7. Còn nợ

- **12 tool** cho các phân hệ mọc sau 28/08/2026: Kho · Đặt phòng họp · Đặt xe · Công việc ·
  Diễn đàn · Đóng dấu (`03-…md` §Phase 5). ⚠️ Chưa có tool nào đọc **tồn kho** — nên trợ lý
  hiện **không có đường** lấy số tồn thật.
- **Lọc quyền cho RAG** (§6.5) — bắt buộc trước khi index nguồn không công khai.
- **Trục GHI đã có hàng rào tự động** (15/09/2026): `test_assistant_chi_co_quyen_xem.py` khai
  bảng `TOOL_GHI` và bắt mọi tool "có mùi ghi" (`draft_` · `_create` · `propose_` · `_update`…)
  phải nằm trong bảng đó, rồi chạy từng tool dưới tài khoản chỉ có `read` — không tool nào được
  lọt. Thêm `draft_xyz` mà quên khai là **đỏ ngay**, đúng bài học B-07.
  ⚠️ Đã kiểm ngược bằng cách phá chốt (`ctx.can(entity, "write")` → `ctx.can(entity)`): bài kiểm
  đỏ 2 ca. Không phải xanh giả.
- **Trục ĐỌC cũng đã có hàng rào** (15/09/2026): `test_assistant_pham_vi_doc.py` bắt **mọi tool
  phải được phân loại** vào đúng một trong bốn bảng — ghi · đọc chứng từ (phải lọc phạm vi) ·
  danh mục dùng chung · cố ý không lọc (kèm lý do). Thêm tool mà quên khai là đỏ.
  ⚠️ **Không quét mã tĩnh** — đã thử và sai tới mức vô dụng: `procurement_doc_read` gọi
  `ctx.can(entity)` bằng BIẾN và lọc phạm vi nằm dưới helper ở tệp khác, quét nguồn handler thì
  kết luận ngược hẳn sự thật. Hàng rào kiểm **hành vi**: dựng hai chủ sở hữu rồi soi xem dữ liệu
  người kia có lọt không.
  ⚠️ **Mỗi ca bắt buộc có ĐỐI CHỨNG DƯƠNG.** "Không thấy dữ liệu người khác" một mình là khẳng
  định rỗng — xanh y hệt khi tool chạy đúng và khi tool không trả gì. Bản đầu dính đúng bẫy đó
  ở hai ca; kiểm ngược mới lòi ra.
  **Đã phủ KÍN 14/14 tool đọc chứng từ** (15/09/2026): 8 ca ngay trong tệp đó, 6 ca trỏ sang
  test riêng của từng tool (`CA_O_TEP_KHAC`, có bài canh cho con trỏ khỏi mục khi ai đổi tên).
  `CHUA_CO_CA_HANH_VI` nay **rỗng** — còn dòng nào trong đó là còn một lỗ đang mở.
  ⚠️ Sổ nợ bản đầu khai 8 tool "chưa có ca"; rà lại thì **5 trong số đó đã được canh sẵn** ở
  tệp test riêng. Ghi nợ sai theo hướng BI QUAN cũng hại như ghi sai theo hướng lạc quan — nó
  đẩy người sau đi viết trùng và làm mờ đúng chỗ thật sự hở.
- **Quyền theo gói tri thức** (mỗi nhóm thấy gói khác nhau) — hiện mọi người dùng chung một gói.

---

## 8. Thêm một tool mới — việc bắt buộc làm đủ

1. Viết handler trong `tools/<phân hệ>_tool.py`, khai `ToolSpec`, đăng vào `_active_specs()`.
2. Trong handler: `ctx.can(entity, action)` → thiếu thì `denied(...)`; rồi `apply_scope(...)`.
   Lấy một bản ghi theo id thì đi `get_scoped`, **không** `db.get`.
3. Kẹp `limit` (xem `catalog._clamp`) — đừng để model kéo cả nghìn dòng.
4. Cắt cột nhạy cảm theo khuôn `see_supplier` nếu kết quả có dữ liệu của phân hệ khác.
5. **Điền vào bảng §5 của `04-…md` CÙNG LÚC với code**, không để sau — đó là thứ duy nhất khách
   đọc khi hỏi *"AI có lòi thông tin vượt quyền không"*.
6. Thêm test ở `test/backend/test_assistant_*.py`: một ca **đủ quyền**, một ca **thiếu quyền**,
   một ca **ngoài phạm vi**.
7. Gói tri thức của phân hệ đó có cần nhắc tên tool mới không (`packs/`)?
