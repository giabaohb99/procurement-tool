# Lộ trình phase - Trợ lý AI cho ERP DEGO

Phiên bản: 25/08/2026. Không đặt mốc thời gian (theo lối tài liệu dự án).
Liên quan: kiến trúc `01-kien-truc-tro-ly-ai.md`, danh sách tool `02-danh-sach-api-tool.md`.

Nguyên tắc xếp phase: ra kết quả cho sếp sớm nhất, rủi ro thấp trước, phần khó (vector,
quản trị nguồn) sau. Mỗi phase chạy được và có ích độc lập, không phải chờ phase sau.

---

## Phase 0 - Nền: lớp provider + khung module  [ĐÃ XONG]

Trạng thái: module `app/modules/assistant` đã có `provider/` (base + claude + gemini qua REST,
chưa dùng SDK), `service.py` routing theo loại câu, `controller.py`, `schema.py`. Cấu hình ở
`core/config.py` (AI_ENABLED, ANTHROPIC_API_KEY, GEMINI_API_KEY, AI_DEFAULT_PROVIDER,
AI_CLAUDE_MODEL, AI_GEMINI_MODEL). Đã test sống Gemini. Streaming để lại P2 (đổi ruột provider
sang SDK). Ghi chú chi phí: Gemini 3.x flash không tắt hẳn suy nghĩ bằng thinkingBudget=0 -
muốn kiểm soát chi phí loại A thì ghim `gemini-2.5-flash`.

Mục tiêu: có bộ khung để mọi phase sau cắm vào; gọi được model của cả hai nhà.

Đầu việc:
- Tạo module backend `assistant` (controller, service, schema).
- Lớp provider `ask(messages, tools, model) -> answer` + adapter Claude (`anthropic`) và
  adapter Gemini (Google GenAI). Đọc `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` từ `.env`.
- Cấu hình routing model theo loại câu (bảng cấu hình: loại A -> model rẻ, loại B -> model mạnh).
- Bật streaming trả lời.

Phụ thuộc: có 2 API key (mục lấy key ở tài liệu chi phí).
Định nghĩa xong: gọi thử một câu qua cả Claude lẫn Gemini, đổi nhà chỉ bằng đổi cấu hình.

---

## Phase 1 - Trợ lý gói tri thức (AI-1) qua API  [ĐÃ XONG]

Mục tiêu: sếp hỏi - đáp được ngay trên nền gói tri thức. Chưa cần tool, chưa cần vector.

Đầu việc:
- [x] Phân quyền: thêm entity `assistant` (permissions + scoping PUBLIC + test B-07 lên 40),
  seed `assistant.read` cho ban lãnh đạo (admin, pur_manager tự có, company_head thêm tay),
  controller đổi sang `require('assistant','read')`. Bot chạy dưới JWT người hỏi.
- [x] File định nghĩa (system prompt) ở `assistant/knowledge.py`: vai trò, ranh giới "chỉ đề
  xuất không tự ban hành", chống prompt-injection (dữ liệu != mệnh lệnh), không lộ system prompt.
- [x] Nạp gói tri thức làm context (`assistant/packs/*.md`, bộ nạp đọc lại đĩa mỗi lượt) +
  prompt caching (Claude cache_control trên khối system; Gemini 2.5+ cache ngầm).
- [x] Endpoint `POST /assistant/chat` + CRUD hội thoại (`GET/DELETE /assistant/conversations`).
  Lịch sử lưu ở `tab_assistant_conversation` + `tab_assistant_message` (role SMALLINT theo
  IntEnum), riêng tư theo `created_by`. Streaming để lại P2.
- [x] Trang Trợ lý riêng (frontend-v2) `modules/assistant`, gác quyền `assistant.read`:
  hội thoại bên trái + luồng chat bên phải, hội thoại đang mở đeo `?c=`, chọn nhà cung cấp
  khi có nhiều nhà, tự báo "chưa sẵn sàng" khi `AI_ENABLED` tắt (endpoint trả 403).

Phụ thuộc: Phase 0.
Định nghĩa xong: sếp mở trang, hỏi về quy trình nhà máy, nhận trả lời có trích nguồn từ gói.

---

## Phase 2 - Tool loại A (tra cứu dữ liệu có cấu trúc)  [ĐÃ XONG]

Mục tiêu: hỏi được số liệu thật (hợp đồng còn hạn, giá tốt nhất, NCC theo mã hàng).

Đầu việc:
- Khung tool-calling: đăng ký allowlist tool, thực thi DƯỚI JWT người hỏi.
- Bảo mật 7 tầng (tài liệu 01 mục 4.2) + audit log. Read-only.
- Cắm tool theo thứ tự: tái dùng trước (T1, T3, T5, T7, T8), rồi tool mới (T2, T4, T6).
- Bot tự chọn gọi tool khi câu hỏi thuộc loại A.

Phụ thuộc: Phase 1 (khung chat đã có).
Định nghĩa xong: hỏi "mã A giá tốt nhất của NCC nào" -> bot gọi tool -> trả số đúng, đúng
quyền người hỏi.

Đã làm (chạy trên Gemini `gemini-3.5-flash-lite`):
- `provider/base.py` thêm `ToolDef` + `run_tools()` trung lập; `gemini.py` và `claude.py`
  cùng hiện thực vòng lặp tool-calling (Gemini `functionCall`/`functionResponse`,
  Claude `tool_use`/`tool_result`), `supports_tools=True`.
- `modules/assistant/tools/`: `base.py` (ToolContext gác `ctx.can` + `apply_scope`),
  `catalog.py` (8 tool T1-T8), `__init__.py` (`tool_defs()` + `run_tool()` allowlist + audit).
- `service.py` routing bật tool cho `lookup`/`general`, tool chạy DƯỚI danh tính người hỏi.
- Gác quyền thực tế: hợp đồng theo entity `contract` (có scope pháp nhân); sản phẩm/NCC theo
  `product`/`supplier`; lịch sử mua/giá gác `product.read` (tên NCC cần thêm `supplier.read`)
  vì `purchase_history` KHÔNG phải entity.
- Test: `test/backend/test_assistant_tools.py` (gác quyền + allowlist + nhất quán đếm/liệt kê).
- Đã sửa lỗi: hợp đồng KHÔNG ghi ngày hết hạn phải là `unknown` ở CẢ `count` lẫn `list`
  (trước đây `list active` gộp nhầm `end_date == ""` vào còn hạn).
- Bổ sung sau khi test UI: 4 tool tổng hợp toàn hệ (T9 recent_purchases, T10
  top_suppliers_by_purchase, T11 recent_purchase_orders, T12 purchase_report) cho nhóm câu
  "mua gì gần nhất / NCC mua nhiều nhất / PO gần nhất / báo cáo chi tiêu" — xem tài liệu 02.
  Tổng hợp trong SQL, không nạp hết bảng. Nay bộ tool loại A có 12 cái.
- Đợt "bot thông minh + dễ hỏi hơn" (25/08/2026, làm A+B+C theo yêu cầu sếp):
  - A. Nâng bộ não: viết lại `TOOL_GUIDE` (service.py) thành BẢN ĐỒ NĂNG LỰC + chiến lược gọi
    tool (chủ động tra mã trước, được gọi NHIỀU tool nối tiếp, tự quy "năm nay/quý 1" ra ngày,
    khi câu ngoài phạm vi thì nêu tra được gì thay vì chỉ xin lỗi). Nạp NGÀY HÔM NAY vào system
    (đặt sau prefix cache nên không phá prompt caching) để model suy khoảng thời gian.
  - B. Frontend-v2: màn trống Trợ lý hiện DÃY CÂU HỎI MẪU bấm-là-hỏi (message-thread.tsx) để
    người dùng biết hỏi gì.
  - C. Thêm T13 `analytics_query` — một tool thống kê tùy biến tham số rộng (metric x dimension
    x kỳ x lọc), enum khai sẵn, không sinh SQL, vẫn gác quyền. Nay bộ tool loại A có 13 cái.
    Đã verify sống trên Gemini: "chi tiêu theo tháng năm nay" -> purchase_report; "đơn giá TB
    năm nay" -> analytics_query, cả hai tự suy đúng khoảng ngày từ hôm nay.

---

## Phase 2b - Hỏi-trước-khi-tạo + tầng GHI có xác nhận (CR-218)  [ĐÃ CODE đợt 1 - 28/08/2026]

Mục tiêu: từ trợ lý CHỈ ĐỌC + đề xuất nháp, nâng lên hỗ trợ tạo/sửa chứng từ có kiểm soát.
Thiết kế chi tiết ở tài liệu `02` mục "Đợt CR-218". Hai khuôn:

- Khuôn 1 - hỏi-trước-khi-tạo: các tool nháp (YCBG/YCMH/YCTT/nghỉ phép) nhận thêm trường
  quan trọng (ngày cần hàng, ngày yêu cầu kết quả, kho nhận, hạn chi YCTT); TOOL_GUIDE bắt
  hỏi gộp MỘT LƯỢT các trường còn thiếu, người dùng nói "chưa cần" thì bỏ qua tạo luôn,
  CẤM hỏi lại thông tin đã đưa.
- Khuôn 2 - sửa/ghi qua khung xác nhận: tool `propose_document_update` trả đề xuất (cũ -> mới),
  frontend hiện thẻ so sánh + nút Xác nhận/Hủy, CHỈ khi người bấm Xác nhận mới gọi
  `POST /api/assistant/confirm-update`; backend KIỂM LẠI TOÀN BỘ tại thời điểm xác nhận
  (quyền `require(entity, write)` + `apply_scope` + trạng thái còn sửa + whitelist trường
  theo handler), ghi qua đúng service của form nên validation + audit giữ nguyên.

Đợt 1 ĐÃ CODE (28/08/2026): trường mới (YCBG ngày yêu cầu kết quả, YCMH kho nhận) +
checklist hỏi-trước trong TOOL_GUIDE; tool bổ sung `payment_request_read` (T32),
`ticket_create` (T33), `my_tickets` (T34); khung xác nhận T31 `propose_document_update` +
endpoint `confirm-update` với 3 handler đầu (YCMH mục đích/ngày cần hàng/ghi chú, YCBG mục
đích/ghi chú, YCTT print_texts tái dùng CR-149). Hạn chi YCTT KHÔNG làm — bản nháp YCTT
dựng từ khoản công nợ, form không có trường này (giới hạn đã biết). Đợt sau: handler
ĐMH/khảo sát/nhận hàng khi còn nháp hoặc theo quyền ghi, nghỉ phép, ticket bổ sung/đóng.

Phụ thuộc: Phase 2. Bảng quyền tài liệu `04` mục 5 + đánh số T31-T34 ở `02` đã cập nhật
cùng đợt code. Định nghĩa xong (ĐÃ ĐẠT ở mức test backend + FE): nhờ bot sửa ngày cần hàng
một YCMH nháp của mình -> bot hiện thẻ cũ/mới -> bấm Xác nhận -> phiếu đổi thật, audit ghi
nhận; người không có quyền / sai chủ token / token hết hạn thì bị chặn ở backend.

---

## Phase 3 - Kho vector Qdrant (loại B)

Mục tiêu: hỏi trên nội dung văn bản (HDSD, quy trình) có trích dẫn.

Đầu việc:
- Docker Qdrant (1 container) + embedding qua **API Gemini** (KHÔNG local — xem QĐ đổi bên dưới).
- Bộ index nguồn có sẵn: Trung tâm HDSD (`help_center` / `tab_help_article`) + FAQ. Cắt
  đoạn (chunk).
- Móc reindex khi bài viết / câu FAQ sửa / xóa (ràng buộc cứng, nuốt lỗi để không vỡ nghiệp vụ).
- Tool loại B `search_docs` cho bot: tìm đoạn -> lọc ngưỡng -> trả kèm trích nguồn.

Phụ thuộc: Phase 0 (provider), độc lập với Phase 2.
Định nghĩa xong: hỏi "quy trình nghiệm thu hàng mấy bước" -> bot trả theo HDSD, có link bài gốc.

### QĐ đổi (26/08/2026): embedding dùng API Gemini, KHÔNG local

Bản đầu định chạy model nhúng LOCAL (bge-m3 ~2.5-4GB, hoặc e5-small ~1GB resident). Bỏ vì VPS
đang **chật RAM**: 7.8Gi tổng, còn trống ~1.4Gi, swap đã dùng 441Mi, 4 core, không GPU — nhét
thêm một model thường trú là đẩy stack vào swap. Nút thắt là RAM chứ không phải độ trễ, nên:

- **Nhúng qua API Gemini** (`gemini-embedding-001`, REST bằng `requests`, cùng khuôn provider
  chat, KHÔNG kéo SDK). 0 RAM thường trú trên VPS. Nội dung loại B (HDSD/FAQ) là **công khai**
  với mọi người đăng nhập nên gửi đi nhúng không phát sinh rủi ro lộ dữ liệu mới.
- Bọc sau **giao diện `Embedder`** (`rag/embedder.py`): sau này muốn giữ trong nhà (khi có Văn
  thư nhạy cảm) chỉ cần thêm `LocalEmbedder` và đổi `get_embedder()`, không đụng chỗ khác.
- Chiều vector 768 (Gemini cho cắt chiều Matryoshka) — đủ chính xác, nhẹ Qdrant.
- **Khóa API:** dev/test dùng chung `GEMINI_API_KEY` hiện có; **prod đổi key riêng** trước khi
  bật thật; qua giai đoạn test sẽ đổi lại API theo yêu cầu sếp.
- Không gắn nhãn quyền theo `apply_scope` cho loại B như bản đầu dự tính: nội dung này vốn công
  khai với mọi người đăng nhập (đúng thứ họ đọc ở Trung tâm HDSD), nên tool `search_docs` không
  gác quyền theo dòng.

Cờ bật: `AI_RAG_ENABLED` (mặc định tắt). Tắt thì tool `search_docs` không hiện cho bot và hook
reindex không chạy — môi trường chưa dựng Qdrant vẫn lưu HDSD/FAQ bình thường.

### QĐ đổi (26/08/2026): nạp chỉ mục chạy NỀN qua Celery

Nhúng đoạn gọi Gemini qua mạng, lúc nghẽn mất vài giây — không giữ request lưu bài / bấm nút chờ.
Toàn bộ việc nạp chỉ mục đẩy sang **celery-worker**:

- Hook HDSD/FAQ (sửa/xóa) chỉ **xếp hàng** (`.delay`) rồi trả ngay; lỗi broker (Redis) được nuốt,
  không làm vỡ việc lưu bài. Task `assistant.rag.reindex_source` / `remove_source` chạy nền, mở
  `SessionLocal` riêng, retry backoff 5 lần cho lỗi tạm thời (Gemini hết quota, Qdrant chập).
- **Đường A (nạp lại toàn bộ)**: `POST /api/assistant/rag/reindex` (gác `help_article.write`) nay
  **chỉ xếp hàng** task `assistant.rag.rebuild_all` rồi trả `task_id` + "đã xếp hàng" — không chờ
  nhúng xong (tránh treo/timeout). Nút bấm nằm ở **Cấu hình hệ thống** của ERP v2 (`/system/settings`,
  thẻ "Trợ lý AI"). `rebuild_all` KHÔNG nạp cả mẻ trong một task mà **rải ra** — liệt kê mọi nguồn
  rồi xếp mỗi nguồn một task `reindex_source` riêng, để trần request/phút của bên nhúng không làm
  hỏng cả mẻ (nguồn nào 429 chỉ mình nó retry; worker `-c 2` tự tiết lưu lượng dưới trần).
- Task đăng ký ở `celery_app.conf.imports`; deploy backend phải **dựng lại celery-worker** vì thêm
  phụ thuộc `qdrant-client`, và worker phải nằm trong mạng tới được `qdrant:6333`.

Mã nguồn: `backend/app/modules/assistant/rag/` (`chunker` · `embedder` · `store` · `indexer` ·
`search` · `hooks` · `tasks`) + tool `tools/rag_tool.py` + nút `frontend-v2/.../system/pages/setting-page.tsx`.
Test: `test/backend/test_rag_chunker.py`, `test_rag_search_docs.py`, `test_rag_tasks.py`.

---

## Phase 4 - Quản lý nguồn tri thức + hoàn thiện

Mục tiêu: vận hành được lâu dài, kiểm soát chi phí, thêm lối vào nhanh.

Đầu việc:
- [ ] Màn "Quản lý nguồn tri thức": khai báo nguồn, bật - tắt, trạng thái index, nút reindex,
  đánh version gói tri thức nhà máy. (HOÃN LÀM SAU CÙNG theo yêu cầu sếp.)
- [x] Bong bóng chat nổi ở góc (lối vào nhanh, dùng lại API Phase 1).
- [x] Guard chi phí: routing model theo loại câu + theo dõi usage.
- [ ] Mở rộng tool loại A khi cần (payable / purchase_order / inventory).

Phụ thuộc: Phase 1-3.
Định nghĩa xong: quản trị viên tự thêm - sửa nguồn tri thức và reindex mà không cần lập trình.

Đã làm:
- Bong bóng chat (P4-B): `modules/assistant/components/assistant-widget.tsx` — bong bóng nổi
  góc phải-dưới, gắn ở cả `LauncherLayout` (màn chọn phân hệ) lẫn `ModuleLayout`, chỉ hiện khi
  `can('assistant','read')` nên không bắn 403. Dùng lại nguyên hook/API Phase 1; giữ MỘT hội
  thoại trong state cục bộ, nút "Mở toàn trang" giữ nguyên `?c=`. Devtools react-query dời sang
  góc trái-dưới để nhường chỗ. Đã đồng bộ với bộ giao diện chat dựng lại (MessageThread /
  ChatComposer / ChatEmptyState) — hiệu ứng gõ máy chỉ chạy cho câu VỪA nhận (`idGoDan`).
- Guard chi phí (P4-C): trần số câu hỏi/người/ngày `AI_DAILY_MSG_LIMIT` (config, 0 = tắt) +
  routing model rẻ `AI_LOOKUP_MODEL` cho câu lookup/general (advice giữ model mạnh). Chặn
  TRƯỚC khi gọi model ở `conversation.chat()` (`usage.check_daily_limit`, quá trần trả HTTP 429).
  `assistant/usage.py`: đếm câu trong ngày, tổng hợp token/số câu theo ngày & theo người đọc
  thẳng các cột `*_tokens` (không thêm bảng). Endpoint `GET /assistant/usage/mine` (mọi người có
  quyền, xem hạn mức còn lại) và `GET /assistant/usage` (chỉ admin qua `assistant.export`, soi
  chi phí). Test: `test/backend/test_assistant_usage.py`.

---

## Để sau (ngoài phạm vi đợt này) - AI-2 RAG toàn hệ

RAG toàn hệ có lọc quyền per-record + backend Văn thư + adapter model mở tự nhúng docker
(Qwen / Llama) làm phương án B khi cần cắt chi phí hoặc chạy tài liệu tuyệt mật trong nhà.

---

## Điểm còn phải chốt trước / trong khi làm

- Đồng ý DPA - no-retention với Anthropic và Google; danh mục tài liệu tuyệt mật loại khỏi
  phạm vi gửi ra API.
- Kích thước gói tri thức nạp kèm mỗi câu (biến chi phí lớn nhất).
- Danh sách 8 tool đã duyệt (tài liệu 02) - có thêm bớt không.
- App riêng hay phân hệ trong ERP.
