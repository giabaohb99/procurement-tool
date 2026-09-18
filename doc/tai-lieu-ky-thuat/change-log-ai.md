# NHẬT KÝ THAY ĐỔI — DẢI `ai`

Sổ CR riêng cho mảng **tự động hóa bằng AI** (Agent Hub), tách ngày **18/09/2026** theo lệnh
đại ca.

**Vì sao tách.** Ba lý do, không phải chỉ để tránh xung đột merge như lần tách `change-log-bao.md`:

- Mảng này **không phải nghiệp vụ thu mua**. Nó là bộ máy *làm ra* phần mềm, không phải một
  phân hệ của phần mềm. Trộn vào sổ nghiệp vụ thì người tra sổ để tìm "YCMH đổi gì" phải lội
  qua một đống dòng chẳng liên quan.
- Nó **có thể bị dừng hẳn** ở bậc 1 nếu con bot quản lý không đủ khôn. Một mảng có khả năng bị
  bỏ thì để riêng, dừng là gấp sổ lại, không phải đi xóa dòng rải rác trong sổ chung.
- Sau này một phần lớn dòng trong sổ này **do máy tự ghi**, không phải người. Dòng máy ghi và
  dòng người ghi để chung một chỗ thì không còn phân biệt được ai chịu trách nhiệm.

**Tệp này chứa gì.** Mọi CR mang tiền tố `ai-`, mọi quyết định `QĐ-AI-x`, và nhật ký triển khai
của Agent Hub.

**Tệp này KHÔNG chứa gì.** Thay đổi nghiệp vụ của ERP, kể cả khi do bot làm ra — cái đó vẫn ghi
vào `change-log.md` / `change-log-bao.md` như thường, và ghi thêm một dòng đối chiếu ở đây.

---

## Luật ghi

**Trạng thái:** `Đề xuất` → `Đã duyệt` → `Đang làm` → `Hoàn tất` (hoặc `Từ chối` / `Hoãn` / `Bỏ`).

**ID đầy đủ = `ai-CR-<số>-<slug>`**, slug kebab 3-5 chữ tóm tắt việc.

**Dải số `ai-CR-*` là DẢI RIÊNG**, bắt đầu từ `001`, **không chung** với `CR-*` và `bao-CR-*`.
Cấp số mới chỉ cần grep đúng tệp này:

```bash
grep -oh "ai-CR-[0-9]\+" doc/tai-lieu-ky-thuat/change-log-ai.md | sort -t- -k3 -n | tail -3
```

**ĐẶT CHỖ NGAY KHI NHẬN VIỆC** — cấp số xong ghi ngay một dòng `Đang làm` rồi mới bắt tay làm.

**Dòng do bot tự ghi** phải để `Người đề xuất` = `Bot (ai-CR-xxx)` và ghi rõ đại ca duyệt lúc nào.

---

## Quyết định đã chốt

| Mã | Ngày | Quyết định | Lý do |
|---|---|---|---|
| **QĐ-AI-1** | 2026-09-18 | Nguồn ticket = **Phiếu hỗ trợ ERP v2** (`tab_ticket`) **+ tin nhắn Telegram của đại ca**. Hai nguồn nhưng **một bảng, một luồng**. | Không đẻ hai nhánh mã cho cùng một việc. `tab_ticket` đã có sẵn, không dựng bảng ticket mới. |
| **QĐ-AI-2** | 2026-09-18 | Agent Hub là **service mới trong repo `procurement-tool`**, không dựng repo hay VPS riêng. | Tận dụng Celery + Redis + Qdrant + DB + lớp provider AI (`assistant/provider/gemini.py`) đã chạy sẵn. Ổ cứng VPS vừa dọn, không dựng hệ thứ hai. |
| **QĐ-AI-3** | 2026-09-18 | Bot quản lý dùng **Gemini API**; bot code dùng **Claude Code CLI chạy trên máy đại ca** bằng subscription. **Không dùng API key Anthropic.** | Bot code là chỗ đốt tiền nhất thì ăn vào subscription; bot quản lý chỉ tóm tắt nên Gemini Flash gần như miễn phí. Biến phí cả hệ thống xấp xỉ bằng không. |
| **QĐ-AI-4** | 2026-09-18 | Hệ quả của QĐ-AI-3: **hub chạy trên máy đại ca**, không đặt ở VPS. Telegram dùng **long-polling**, ticket từ ERP prod thì **quét theo mốc sửa**. | Khỏi cần địa chỉ công khai, khỏi tunnel, khỏi webhook, khỏi ký HMAC trên nút bấm. Đổi lại máy tắt thì hệ thống đứng — chấp nhận được vì trạm nào cũng chờ đại ca duyệt. |
| **QĐ-AI-5** | 2026-09-18 | **Hai chỗ dừng bắt buộc không được cấu hình bỏ qua**: giữa PLAN và CODE, giữa REVIEW và PROD. | Đây là toàn bộ lý do hệ thống này an toàn. Không bao giờ thêm cờ "tự duyệt" cho hai chỗ đó. |
| **QĐ-AI-6** | 2026-09-18 | Bot code **cấm tuyệt đối tự sinh migration**. Cần đổi cấu trúc DB thì dừng và leo thang cho người. | Migration hỏng trên một cơ sở dữ liệu 141 bảng đang chạy thật không cứu được bằng revert commit. |
| **QĐ-AI-10** | 2026-09-18 | Bot Telegram **kiêm luôn cửa vào của Trợ lý AI sẵn có**: tin bắt đầu bằng `/hoi` chuyển thẳng cho `assistant.service.ask()`, trả lời tại chỗ, **không** tạo task. Chạy dưới **một tài khoản ERP khai cứng** ở `AGENT_ASSISTANT_USER`; để trống = tắt hẳn lệnh đó. | Đại ca hỏi "sao không dùng luôn trợ lý qua Telegram". Đúng là rẻ — cầu nối Telegram đã dựng, `ask()` đã có đủ tool-calling — và hỏi đáp với giao việc cùng đi qua một cái điện thoại, tách hai bot thì phải nhớ đang chat với con nào. ⚠️ Trợ lý lọc dữ liệu theo **người đăng nhập** mà Telegram thì không đăng nhập, nên bắt buộc chỉ đích danh một tài khoản; chạy không người dùng là chạy không phạm vi. Hàng rào còn lại vẫn là `AGENT_TELEGRAM_CHAT_ID`, nên **đừng khai tài khoản quản trị**. |
| **QĐ-AI-9** | 2026-09-18 | Bot quản lý dùng **kho vector RIÊNG** `agent_docs`, không dùng chung `kb_docs` của Trợ lý AI. | Cân nhắc dùng chung theo đề nghị của đại ca rồi bỏ. `kb_docs` hiện chỉ có `help_article` + `faq` — HDSD cho người dùng cuối, không có change-log, không có mã CR, tức không có đúng thứ bot cần. Còn nạp tài liệu kỹ thuật vào đó thì `rag/search.py` **không lọc theo `source`**, người dùng cuối hỏi nghiệp vụ sẽ nhận về nhật ký deploy — muốn chặn phải sửa đường tra cứu đang chạy thật. Tách kho tốn đúng một tham số `VectorStore(collection=...)`. |
| **QĐ-AI-8** | 2026-09-18 | **Lệch có chủ ý so với bản thiết kế §5**: bảng nối đổi từ `tab_agent_task_ticket(ticket_id)` thành **`tab_agent_task_item(source, ref_id)`**, và thêm bảng thứ năm **`tab_agent_cursor`**. | Bậc 1 không có `tab_ticket` nào (QĐ-AI-7), nên bảng chỉ trỏ được sang `tab_ticket` sẽ **rỗng suốt bậc 1** — mà "bot gom việc được không" lại đúng là một trong hai câu bậc 1 sinh ra để trả lời. Cặp `(source, ref_id)` chạy được cho cả Telegram lẫn `tab_ticket` sau này, nối thêm nguồn là thêm dòng chứ không sửa bảng. `tab_agent_cursor` giữ con trỏ `getUpdates`: Telegram ôm tin chưa xác nhận tới 24h, không lưu con trỏ xuống DB thì mỗi lần restart là bot đọc lại tin cũ và đẻ một loạt task trùng. |
| **QĐ-AI-7** | 2026-09-18 | **Phạm vi bậc 1 co lại còn lõi nhất**: chỉ nhận ticket từ **Telegram**, **không** dựng màn hình quản lý trong ERP v2 (xem sổ bằng Adminer), dùng **key Gemini riêng** `AGENT_GEMINI_API_KEY`. | Bậc 1 có thể bị bỏ hẳn nếu con quản lý không đủ khôn — nên cắt mọi thứ không phục vụ câu hỏi đó. Nối `tab_ticket` và dựng màn hình đều là việc cộng thêm sau, không phải sửa lại. Key riêng để bot đốt hết hạn mức thì Trợ lý AI đang chạy thật không chết theo, và đo được riêng chi phí của bot. |

---

## Việc còn nợ

Bốn câu `AN-001`…`AN-004` đại ca đã trả lời hết ngày 18/09/2026, gói vào `QĐ-AI-7` ở trên.

| Mã | Nội dung | Trạng thái |
|---|---|---|
| **AN-001** | Bot Telegram | **Xong** — đại ca đã có sẵn bot, tự điền `AGENT_TELEGRAM_BOT_TOKEN` + `AGENT_TELEGRAM_CHAT_ID` vào `.env`. Token KHÔNG đi qua chat, KHÔNG commit |
| **AN-002** | Key Gemini | **Xong** — tách riêng `AGENT_GEMINI_API_KEY`, không dùng chung với Trợ lý AI |
| **AN-003** | Nguồn ticket bậc 1 | **Xong** — chỉ Telegram. Nối `tab_ticket` để dành bậc sau |
| **AN-004** | Màn hình quản lý | **Xong** — chưa dựng. Bậc 1 xem sổ bằng Adminer |
| **AN-005** | Nối `tab_ticket` của ERP làm nguồn vào (vòng quét theo mốc sửa, khuôn `pull_updated` của `legacy_datxe`) | Hoãn tới sau bậc 1 |
| **AN-006** | Màn danh sách + chi tiết task trong ERP v2 (xem sổ, lịch sử gọi model, chi phí) | Hoãn tới bậc 2 |

---

| CR | Ngày | Người đề xuất | Nội dung | Ảnh hưởng scope | Trạng thái | Tài liệu liên quan |
|---|---|---|---|---|---|---|
| **ai-CR-002-dung-bac-1-quan-ly** | 2026-09-18 | Trợ lý (đề xuất) | **Dựng bậc 1 của Agent Hub.** Phạm vi đã co lại theo `QĐ-AI-7`: **chỉ nguồn Telegram, không dựng màn hình**. Gồm: **năm** bảng sổ `tab_agent_task` · `tab_agent_task_item` · `tab_agent_run` · `tab_agent_message` · `tab_agent_cursor` (xem `QĐ-AI-8`); cầu nối Telegram **kéo tin mỗi 10 giây** (không long-polling — `celery-worker` chạy `-c 1`, giữ một kết nối treo là chặn hết mọi việc nền khác) kèm nút Duyệt/Sửa/Bỏ và khóa theo `chat_id`; bot quản lý Gemini chạy hai trạm TRIAGE (gom tin cùng loại + tóm tắt) và PLAN (đề xuất cách sửa + `plan_files`); index kho tài liệu dự án vào Qdrant (collection riêng `agent_docs`, xem `QĐ-AI-9`) làm trí nhớ; thêm nhánh `/hoi` gọi thẳng Trợ lý AI có sẵn (`QĐ-AI-10`). **Đầu ra bậc 1 chỉ là in bản PLAN ra Telegram và ghi vào sổ — chưa gọi `claude -p`, chưa đụng một dòng mã nào của hệ thống.** | Thêm 1 module backend + 5 bảng + 1 bộ mã trạng thái. **Không đụng** phân hệ nghiệp vụ nào đang chạy. Cầu dao `AGENT_HUB_ENABLED` mặc định tắt. | **Đang làm** — đại ca duyệt thiết kế 18/09/2026 | `doc/agent-hub/01-thiet-ke-ky-thuat.md` §10 bậc 1 |
| **ai-CR-001-thiet-ke-agent-hub** | 2026-09-18 | Đại ca (*"tôi định làm 1 hệ thống... khi tôi có ticket thì tôi cần 1 chổ nào đó có thể thông qua 1 AI kiểu như quản lý, nhận thông tin đó, tóm gọn lại dựa trên memory hoặc là thông tin từ hệ thống, sau đó nhắn qua tele cho tôi..."*, sau đó *"vậy thì phải có 1 bộ quy tắt đúng không, em có thể ghi nhận thiết kế đi em, sổ CR thì em tách ra 1 sổ nữa riêng cho phần AI này em nhé"*) | **Viết bản thiết kế kỹ thuật + bộ quy tắc cho Agent Hub, và tách sổ CR riêng cho mảng AI.** Ba tệp mới: bản thiết kế (kiến trúc, bảy trạm, mô hình dữ liệu, cấu hình, lộ trình bốn bậc, bảng rủi ro), bộ quy tắc cho bot (ba luật trùm, luật cho từng con bot, điều kiện dừng và leo thang, danh sách cấm cứng), và chính tệp sổ này. Chốt được sáu quyết định `QĐ-AI-1`…`QĐ-AI-6`. Rà lại hạ tầng có sẵn và xác nhận **phần lớn việc là ráp chứ không phải xây**: provider Gemini, Qdrant/RAG, `tab_ticket`, Celery, sổ `tab_sync_log` đều đã chạy. | Chỉ tài liệu. Không một dòng mã nào. | **Hoàn tất** | `doc/agent-hub/README.md` · `01-thiet-ke-ky-thuat.md` · `02-bo-quy-tac-bot.md` |
