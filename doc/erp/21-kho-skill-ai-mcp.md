# 21 — KHO SKILL AI QUA MCP (hướng B: xây trên ERP của mình)

| | |
|---|---|
| Bản | 1.4 — 19/10/2026 (1.1: §2.1 đối chiếu + chồng chéo, §6.5 sắp lại Trang cá nhân, 5 phase. 1.2: §5.5 ba tầng công cụ dữ liệu, §5.6 chuẩn dữ liệu cho AI ngoài, K11–K13 + phase P1b, mục Đã chốt ở §9. 1.3: §7.1 chuyển hướng 17/10 — MCP là đường chính, gác bot Telegram. 1.4: §7.2 hiện trạng 19/10 + đối chiếu màn CoreSkill, ba đợt mới P6 OAuth · P7 K9 · P8 K7, Q4/Q7 chốt) |
| Người yêu cầu | Đại ca (Gia Bảo) — *"mình làm lại trên của mình, hướng B; viết kế hoạch chi tiết, còn giao diện định hướng như thế nào"* |
| Tham khảo | coreskill.app (trang giới thiệu công khai, đọc 15/10/2026) |
| Trạng thái | **P0 · P1 · P1b · P2 · P4 XONG trên DEV (bao-CR-620..625, ai-CR-207..217); lên PROD trưa 19/10/2026.** Còn P6 OAuth · P7 K9 · P8 K7 (§7.2) |
| Nền đã có | Cổng MCP + khóa MCP cá nhân **ai-CR-063** (`agent_hub/mcp.py`, `mcp_keys.py`, `doc/agent-hub/06-cong-mcp.md`) — đang chạy DEV, prod chưa mở |

---

## 1. Bài toán và đích đến

Công ty có nhiều "cẩm nang" mà AI nên làm theo: quy trình thu mua, cách lập phiếu, giọng văn, sổ tay vận hành nhà máy,
quy định nghỉ phép… Hiện chúng nằm rải rác: Help Center, gói tri thức của Trợ lý (`assistant/packs/*.md`,
`assistant/knowledge-source/*.md`), tệp Word gửi qua Zalo. Mỗi người dùng một ứng dụng AI khác nhau (Claude, ChatGPT,
Cursor, Gemini) và không ai biết AI của ai đang đọc bản nào.

**Đích đến:** ERP có phân hệ **Kho skill AI**. Soạn một lần trên web, gán theo sơ đồ tổ chức; mỗi nhân sự dán **một địa
chỉ + một khóa** vào ứng dụng AI của mình là AI đó đọc được đúng skill của phòng mình **và** tra được dữ liệu ERP theo
đúng quyền của chính người đó. Quản trị thấy ai dùng gì, thu hồi tức thì.

Ba lợi ích theo thứ tự quan trọng:

1. **Tiền model chuyển về tài khoản AI của từng người.** Nhân sự hỏi bằng Claude / ChatGPT của chính họ thì công ty
   không trả token qua ví trạm modelapi.vn (ví đang trừ ~27 USD/ngày khi chạy thử, xem `doc/agent-hub/20`). Đây cũng là
   lời giải cho câu hỏi đang gác 14/10: *người nhận việc nhắn bot thì trừ token của ai*.
2. **Một nguồn chân lý cho cẩm nang.** Sửa một lần, lượt gọi kế tiếp đã đọc bản mới; bot Telegram cũng đọc cùng kho.
3. **Kiểm soát + nhật ký.** Mỗi người một khóa, có hạn, thu hồi được; mọi lượt gọi đều ghi lại kể cả lượt bị từ chối.

## 2. Đối chiếu: CoreSkill có gì — DEGO đã có gì — phải xây gì

| Năng lực (CoreSkill) | DEGO hiện có | Phải xây |
|---|---|---|
| Sơ đồ tổ chức nhiều cấp, trưởng phòng | `tab_department` (cột `parent`, `manager_id`), `tab_department_company`, chức vụ `tab_job_position`, cấp bậc `tab_employee.job_level` | Không xây mới. Chỉ dùng lại |
| Bốn vai (chủ, quản trị, trưởng phòng, thành viên) | RBAC hai trục: vai trò × phạm vi (`core/auth.py`, `core/scoping.py`) | Khai entity mới (§4.4) |
| Gán skill cho công ty / phòng / người, phòng con kế thừa | Khuôn bảng quyền chủ thể `tab_report_access`, `tab_doc_folder_access` + `core/subject_match.py` (người · phòng ban · pháp nhân · vai trò, cấm thắng, có hạn, thu hồi) | Bảng `tab_ai_skill_access` theo đúng khuôn đó + luật kế thừa theo cây phòng ban |
| Soạn skill trên web, tải gói .zip/.skill, tệp đính kèm | Help Center có trình soạn; frontend-v2 có `@tiptap/*`, `react-markdown` | Bảng skill + phiên bản + tệp; màn soạn |
| Địa chỉ MCP chung + khóa cá nhân | **Có** — `POST /api/mcp`, khóa `dego_mcp_…` băm SHA-256, hạn tối đa 365 ngày, tối đa 5 khóa, hai mức chỉ đọc / được ghi, khóa đóng khi nghỉ việc | Thêm: quản trị **phát hộ** khóa cho người / cả phòng, khóa **chờ nhận**, chọn hạn |
| Công cụ đọc skill qua MCP | Chưa — cổng hiện chỉ có tool ERP (`assistant.tools`, 73 tool) | Ba tool: `list_skills`, `read_skill`, `read_skill_file` |
| Nhật ký mọi lượt gọi, kể cả bị từ chối | Chỉ có `last_used_at` của khóa + audit từng tool ERP (`tab_audit_log`) | Bảng nhật ký lượt gọi MCP + màn nhật ký + xuất CSV |
| Tổng quan: biểu đồ 14 ngày, top skill, top khóa | Chưa | Màn tổng quan |
| AI quản trị giúp (tạo skill, phát khóa, xác nhận khi xóa) | Bot Telegram core_v2 có khuôn *nháp → xác nhận* | Công cụ quản trị cho bot / khóa quản trị |
| Mức bảo mật skill (tắt / bảo vệ / khóa) | Chưa | Cờ trên từng skill (§4.5) |
| Demo sản phẩm theo chương trên trang giới thiệu | Chưa | Thành phần *demo theo chương* (§6.4) |

### 2.1 Đối chiếu với hệ đang có của mình — khác nhau và chồng chéo (bản 1.1, sau khi đọc `coreskill.app/help`)

**Hai thứ khác bản chất, không thay nhau:**

| | Trợ lý cá nhân (bot Telegram + Trợ lý web) — đang chạy | Kho skill + MCP — kế hoạch này |
|---|---|---|
| Ai chạy model | Mình chạy (dịch vụ AI, ví trạm / khóa AI) | Ứng dụng AI của từng người, tiền của họ |
| Cách dùng | Nhắn trên Telegram / web, bot **chủ động**: nhắc, bản tin, thông báo, nháp phiếu, lịch, sửa mã | Người dùng **tự hỏi** trong Claude / ChatGPT / Cursor trên máy tính |
| Có trí nhớ cá nhân | Có (sổ nhớ, thói quen) | Không |
| Dữ liệu ERP | Có, theo quyền người dùng | Có, **cùng bộ tool, cùng quyền** |
| Cẩm nang công ty | Gói tri thức cố định trong mã (`assistant/packs`, `knowledge-source`) | Kho skill sửa trên web |

CoreSkill **chỉ phát cẩm nang (chỉ đọc), không có dữ liệu nghiệp vụ, không làm việc thay ai**. Mình hơn họ ở chỗ cổng MCP
đã trả được dữ liệu ERP theo quyền. Mình thua họ ở chỗ chưa có kho cẩm nang, nhật ký, phát khóa hộ, màn quản trị.

**Hiện trạng cổng MCP của mình (đo 16/10/2026):** cổng + khóa tự tạo + 73 tool + hai mức + tạo phiếu hai bước đã có
trên DEV từ ai-CR-063, nhưng **chưa ai dùng — 0 khóa từng được tạo**; prod chưa mở; lối vào duy nhất là một khối
*"Nâng cao"* nằm cuối tab *Khóa AI* của Trang cá nhân.

**Năm chỗ chồng chéo phải gỡ:**

| # | Chồng chéo | Cách gỡ |
|---|---|---|
| C1 | **Ba nơi giữ tri thức cho AI:** `assistant/packs` (5 tệp), `assistant/knowledge-source` (11 tệp nhà máy), Help Center + RAG | Kho skill thành nơi DUY NHẤT giữ cẩm nang cho AI; packs / knowledge-source chuyển vào kho (đợt K7) rồi xóa khỏi mã. Help Center giữ vai HDSD cho người đọc; skill trỏ link sang khi cần |
| C2 | **Ba thứ cùng gọi là "khóa"** trên Trang cá nhân: khóa model AI (Gemini / Claude qua trạm — trả tiền model), khóa MCP (cho AI ngoài vào ERP), mã liên kết Telegram | Đổi tên cho rõ: **Khóa model AI** (bot dùng để suy nghĩ) · **Khóa kết nối ERP** (AI riêng của bạn dùng để vào ERP) · **Liên kết Telegram**. Gom chung một khu *Trợ lý AI của tôi* (§6.5) |
| C3 | **Hai cửa vào cùng một việc:** hỏi bot Telegram và hỏi AI riêng qua MCP đều tra được phiếu, nháp được phiếu | Giữ cả hai, chia vai: bot cho việc **chủ động + trên điện thoại** (nhắc, bản tin, duyệt nhanh); MCP cho **làm việc trên máy tính** với AI người đó quen. Hai cửa gọi cùng bộ tool nên kết quả giống nhau |
| C4 | **Quản trị qua AI:** CoreSkill có khóa riêng `cmk_` cho AI của admin; mình đã có bot Telegram sửa dữ liệu bằng lời (thẻ xác nhận + sổ thay đổi + hoàn tác 24 giờ) | Không làm khóa quản trị thứ hai. Đợt K9 thêm công cụ quản trị kho skill vào **bot hiện có** |
| C5 | **Nhật ký:** `tab_audit_log` (thao tác ERP) + `tab_agent_run` (lượt bot) + nhật ký MCP mới | Nhật ký MCP chỉ ghi lượt gọi cổng; thao tác thật vẫn vào `tab_audit_log` như cũ. Màn Nhật ký có nút nhảy sang dấu vết thao tác tương ứng |

Những điều học thêm từ `/help` của họ, đưa vào thiết kế: tên skill chỉ chữ không dấu + số + `-` `_` (AI gọi bằng tên);
*Thay gói* là thay toàn bộ tệp đính kèm còn *Thêm tệp* thì cộng dồn — phải nói rõ trên màn; tệp đính kèm chỉ nhận văn
bản (md, json, csv, txt, yaml); trần MCP 120 lượt / phút / khóa; khóa đã thu hồi vẫn để lại dòng *Đã thu hồi* để đối
soát, gọi bằng nó vẫn ghi nhật ký *Từ chối*; công tắc *nhân sự được tự phát khóa* đặt ở Cấu hình; skill dặn AI *áp dụng
vào việc, không đọc lại nguyên văn*.

**Không lấy của CoreSkill:** mô hình nhiều doanh nghiệp tự đăng ký (mình là một tập đoàn, đa pháp nhân đã có),
đăng nhập Facebook, gói cước. Không lấy khái niệm "skill server" riêng — dùng **Bộ skill** (§4.1) cho gọn.

## 3. Kiến trúc

```
Ứng dụng AI của nhân sự (Claude / ChatGPT / Cursor / Gemini CLI / Claude Code)
        │  Authorization: Bearer dego_mcp_…           (một địa chỉ cho cả công ty)
        ▼
ERP  /api/mcp  ──proxy──▶  DỊCH VỤ AI (agent-hub, AGENT_MODE)  ──cổng B ký──▶  ERP /api/agent-gw/*
                            · xác thực khóa (tab_agent_mcp_key)               · skill người này được đọc
                            · ghi nhật ký lượt gọi (tab_agent_mcp_call)        · nội dung skill / tệp
                            · tool skill + tool ERP                           · tool ERP chạy dưới quyền người đó
```

Nguyên tắc (giữ luật ai-CR-119 / ai-CR-153 đang có):

- **Nội dung skill + quyền xem nằm ở ERP** (module mới `ai_skill`), vì nó gắn sơ đồ tổ chức và RBAC của ERP. Dịch vụ AI
  không có bảng skill riêng, chỉ hỏi ERP qua cổng B.
- **Khóa + nhật ký lượt gọi nằm ở dịch vụ AI** (nơi cổng MCP đang sống). Màn ERP đọc qua proxy `/api/agent-hub/*`
  như màn khóa MCP hiện nay.
- **Mỗi lượt gọi kiểm lại từ đầu:** khóa còn hạn, tài khoản còn hoạt động, skill còn trong phạm vi. Không cache quyền
  quá 60 giây (khớp `_PERM_CACHE`).
- **Bot Telegram và Trợ lý web đọc cùng kho skill** qua cùng hàm resolve — không có bản cẩm nang thứ hai.

## 4. Thiết kế dữ liệu (ERP, module `ai_skill`)

Luật nền: tên bảng/cột tiếng Anh; trạng thái là `SMALLINT` + `IntEnum` (R2); mọi bảng có `company_id`; cột `String(n)`
phải có `max_length` ở schema.

### 4.1 Bảng

| Bảng | Vai trò | Cột chính |
|---|---|---|
| `tab_ai_skill_set` | **Bộ skill** — nhóm skill theo chủ đề / phòng (vd *Thu mua*, *Văn thư*, *Nhà máy*) | `code`, `name`, `description`, `company_id`, `owner_department_id`, `status` (SkillSetStatus: nháp / đang dùng / lưu trữ), `security_level` (§4.5) |
| `tab_ai_skill` | Một skill | `skill_set_id`, `slug` (tên máy, duy nhất trong bộ), `title`, `summary` (≤ 500 ký tự — **AI dùng để chọn skill**, phải viết kỹ), `current_version_id`, `status`, `sort_order` |
| `tab_ai_skill_version` | Nội dung theo phiên bản (chỉ thêm, không sửa) | `skill_id`, `version_no`, `body_md` (Text, trần 200 KB), `change_note`, `published_at`, `published_by` |
| `tab_ai_skill_file` | Tệp đi kèm một phiên bản (mẫu biểu, bảng tra) | `version_id`, `filename`, `mime`, `size` (≤ 2 MB), `storage_key`, `text_extract` (bản chữ để trả qua MCP) |
| `tab_ai_skill_access` | Ai được đọc **bộ** hoặc **skill** | Khuôn `tab_report_access`: `target_kind` (bộ / skill), `target_id`, `subject_kind` (người · phòng ban · pháp nhân · vai trò · **chức vụ** · **cấp bậc**), `subject_id`, `effect` (cho phép / cấm), `include_children` (phòng ban: kể cả phòng con), `valid_until`, `revoked_at` |

Chỉ hai chủ thể mới so với khuôn hiện có là **chức vụ** và **cấp bậc**. Thêm vào `core/subject_match.py` một lần, có
bài kiểm riêng, để văn bản / thư mục / báo cáo sau này cũng dùng được.

### 4.2 Luật "ai đọc được skill nào"

1. Skill đọc được khi **bộ** của nó đọc được **và** skill không bị thu hẹp. Một skill có dòng quyền riêng thì quyền
   riêng đó **thay** quyền bộ (thu hẹp), không cộng thêm.
2. Phòng ban có `include_children = true` thì phòng con theo cột `parent` cũng nhận. **Đổi phòng là đổi skill, khóa giữ
   nguyên** — vì quyền tính theo hồ sơ nhân sự lúc gọi, không chép vào khóa.
3. **Cấm thắng cho phép** (như văn bản / báo cáo).
4. Chỉ skill `status = đang dùng` của bộ `đang dùng` mới lộ ra MCP. Nháp chỉ người soạn thấy.
5. Hàm duy nhất: `ai_skill.service.visible_skills(db, user) -> list[SkillRef]`. MCP, bot, Trợ lý web, màn *AI của tôi*
   đều gọi hàm này.

### 4.3 Bảng ở dịch vụ AI

| Bảng | Thay đổi |
|---|---|
| `tab_agent_mcp_key` (đã có) | Thêm `issued_by` (người phát hộ), `claimed_at` (lúc chủ khóa bấm nhận), `raw_sealed` (khóa thô mã hóa Fernet **chỉ giữ tới khi nhận**, nhận xong xóa), `batch_id` (phát cả phòng một lượt) |
| `tab_agent_mcp_call` (mới) | Mỗi lượt JSON-RPC một dòng: `key_id`, `user_id`, `employee_id`, `department_id`, `company_id` (chụp lúc gọi), `client_name` (từ `initialize.clientInfo`), `method`, `tool`, `skill_id`, `status` (CallStatus: thành công / bị từ chối / lỗi), `deny_reason`, `duration_ms`, `created_at`. Lượt khóa sai cũng ghi (`key_id = 0`, `deny_reason`) — có trần tần suất để không bị dội đầy bảng |

Giữ nhật ký 180 ngày; quá hạn gom thành bảng đếm theo ngày rồi xóa dòng chi tiết (beat Celery có sẵn).

### 4.4 Quyền (RBAC)

| Entity mới | Hành động | Phạm vi (`SCOPE_FIELDS`) |
|---|---|---|
| `ai_skill` | read · create · write · delete · approve (xuất bản) | theo `owner_department_id` của bộ → trưởng phòng soạn được bộ của nhánh mình (`dept`), quản trị `all` |
| `ai_mcp_key_admin` | read · create (phát hộ) · delete (thu hồi) | theo phòng ban của **chủ khóa** |
| `ai_usage_log` | read · export | theo phòng ban của người gọi; nhân sự luôn xem được nhật ký **của chính mình** ở *AI của tôi* |

Ba entity phải khai đủ ở `SCOPE_FIELDS` (test B-07 đếm lại). Thêm ba vai trò seed: *Quản trị kho skill*, *Biên tập skill
phòng ban*, *Xem nhật ký AI* — đúng luật một vai trò = một chức năng (CR-428). Seed prod **không ghi đè** phân quyền đã sửa.

### 4.5 Mức bảo mật của bộ skill

| Mức | MCP trả gì |
|---|---|
| Mở (mặc định) | Nội dung + tệp đi kèm |
| Bảo vệ | Nội dung, **không** trả tệp đi kèm |
| Khóa | Chỉ tên + tóm tắt; nội dung chỉ bot / Trợ lý nội bộ đọc |

Nói thật trong màn hình như CoreSkill: *ai cầm khóa hợp lệ thì đọc được thứ khóa đó trả về; nhật ký cho biết ai đã đọc
gì*. Không hứa chống sao chép.

## 5. Cổng MCP — phần thêm

### 5.1 Ba tool skill (khóa chỉ đọc cũng có)

| Tool | Vào | Ra |
|---|---|---|
| `list_skills` | `query?` (lọc chữ), `skill_set?` | Danh sách `{slug, title, summary, skill_set, version_no, updated_at}` người này đọc được |
| `read_skill` | `slug` | `body_md` phiên bản hiện hành + danh sách tệp (tên, cỡ) |
| `read_skill_file` | `slug`, `filename` | `text_extract` của tệp (bộ mức Bảo vệ / Khóa thì từ chối) |

`INSTRUCTIONS` của server thêm một câu: *trước khi làm việc nghiệp vụ, gọi `list_skills` để xem cẩm nang công ty liên
quan rồi `read_skill` đúng cái cần*. Có thể mở thêm `prompts/list` để ứng dụng hỗ trợ hiện skill như lệnh gõ tắt (đợt sau).

### 5.2 Tool ERP qua MCP

Đang có sẵn (ai-CR-063). Kế hoạch chỉ siết:

- Khóa **chỉ đọc**: chỉ tool tra cứu (đã vậy).
- Khóa **được ghi**: giữ khuôn hai bước `draft_*` → `confirm_draft`. Không mở đề nghị thanh toán, không mở `propose_*`.
- Danh sách tool lộ ra MCP do **quản trị bật / tắt theo nhóm** ở màn Cấu hình (vd tắt nhóm Công nợ cho MCP), mặc định
  bật nhóm tra cứu phiếu của chính mình + nghỉ phép + danh bạ.

### 5.3 Phát khóa

| Đường | Ai | Cách giao khóa |
|---|---|---|
| Tự tạo (đã có) | Mọi người, ở Trang cá nhân | Hiện một lần trên màn |
| **Phát hộ một người** | Có `ai_mcp_key_admin.create` trong phạm vi | Khóa ở trạng thái **chờ nhận**; chủ khóa nhận thông báo chuông (+ Telegram nếu đã liên kết), vào *AI của tôi* bấm **Nhận khóa** để xem đúng một lần |
| **Phát cả phòng** | như trên | Tối đa 50 người một lượt, cùng hạn, mỗi người một khóa chờ nhận |

Không gửi khóa qua email vì prod đang tắt gửi thư (bell-only). Hạn chọn 7 / 30 / 90 / 180 / 365 ngày. Thu hồi: một
khóa, mọi khóa của một người, hoặc cả lượt phát. Nghỉ việc vẫn đóng hết như hiện nay.

### 5.4 Nhật ký và chặn dội

- Mỗi lượt ghi một dòng `tab_agent_mcp_call` (§4.3), kể cả `initialize` / `tools/list` (để biết ứng dụng nào đang nối).
- Trần tần suất hai lớp: theo IP và theo khóa (vd 60 lượt / phút / khóa). Vượt trần trả lỗi JSON-RPC rõ ràng, ghi nhật
  ký `bị từ chối: quá tần suất`.

### 5.5 Ba tầng công cụ dữ liệu cho AI (bản 1.2 — đại ca chốt 17/10/2026)

Câu hỏi gốc của đại ca: *làm công cụ cho từng báo cáo, hay cho AI gọi thẳng API rồi tự ghép báo cáo?* — Chốt: **không
chọn hẳn một bên, làm ba tầng**. Báo cáo mới từ nay chủ yếu là **viết skill** (mẫu trình bày) + AI lấy số qua tầng 1
hoặc 2, Claude / ChatGPT tự dựng Excel / Word; code chỉ viết ở tầng 2, mỗi bộ dữ liệu khai một lần.

**Vì sao không để AI gọi API thô hoàn toàn** (quyền thì an toàn, vì mọi API đã `require` + `apply_scope`):
số lớn phải gọi hàng chục trang rồi AI tự cộng — dễ sai, sai một số là hỏng báo cáo; dữ liệu API làm cho màn hình nên
thừa trường, tốn token phía người dùng; AI phải đoán API nào / lọc gì; phải chặn kỹ API có ghi hoặc có tác dụng phụ.

| Tầng | Là gì | Dùng khi | Ghi chú kỹ thuật |
|---|---|---|---|
| **T1 — Báo cáo gom sẵn** | MỘT công cụ `report_summary(report_key, filters)` mở 13 báo cáo của phân hệ Báo cáo (`core/report_keys.py`: mua hàng, chi tiết YCMH, tiến độ báo giá, tiến độ mua hàng, khảo sát, biến động nhân sự, nghỉ phép, quỹ phép, đặt xe, đóng dấu, văn bản, phê duyệt, công việc) — gọi thẳng hàm dịch vụ đứng sau `/summary` | Báo cáo chuẩn công ty — số khớp 100% màn web | Đi qua đúng hai lớp gác của `/summary`: `require(entity, action)` + `apply_scope` **và** `require_report(ReportKey)`. Thay dần các tool báo cáo riêng lẻ (`purchase_report`…) để còn một đường. Bộ lọc nhận đúng tham số màn web nhận (kỳ, pháp nhân, phòng ban…), mô tả từng bộ lọc trong `inputSchema` |
| **T2 — Truy vấn tổng hợp linh hoạt** | Mở rộng `analytics_query` (hiện chỉ mua hàng: đo tổng tiền / số dòng / số lượng / giá TB theo NCC / sản phẩm / tháng) thành **sổ bộ dữ liệu khai báo**: mỗi bộ khai một lần *đo được gì* (measures) × *chia theo gì* (dimensions) × *lọc được gì* (filters), máy chủ tự tính trong phạm vi quyền, trả bảng nhỏ | Báo cáo mới chưa có trang web. Thêm bộ dữ liệu = khai báo, không viết tool | Khai ở `assistant/datasets/<tên>.py` (model, cột được phép, entity gác + `SCOPE_FIELDS`, ReportKey nếu có). KHÔNG sinh SQL từ model — chỉ chọn trong danh sách đã khai. Trần 500 nhóm / lượt; vượt trần trả `truncated` + gợi ý lọc hẹp. Bộ làm trước (đại ca chốt): **mua hàng** (đã có — chuyển sang khuôn mới), **công nợ phải trả**, **yêu cầu thanh toán** |
| **T3 — Đọc API danh sách và chi tiết** | MỘT công cụ chỉ đọc `erp_read(resource, id?, filters?, page?)` gọi các API GET trong **danh sách trắng** (danh sách / chi tiết của YCMH, YCBG, ĐMH, nhận hàng, NCC, sản phẩm, hợp đồng…) | Đào sâu: *mở chi tiết PO00358*, *phiếu đang chờ duyệt của phòng X* | Gọi hàm dịch vụ trong tiến trình (không HTTP vòng), dưới quyền chủ khóa. Tối đa 5 trang × 100 dòng mỗi lượt; gọt trường thừa theo bộ trường khai cho từng resource. Không GET nào có tác dụng phụ được vào danh sách (vd đường xuất Excel có ghi `export_log` → loại) |

**Skill là "mẫu báo cáo".** Ví dụ skill `bao-cao-mua-hang-thang`: cột nào, nhóm theo gì, tính VAT ra sao, cảnh báo khi
giá tăng quá 10 %, gọi T1 với `report_key = PURCHASE_REPORT` hay T2 với bộ `purchase`. Đổi mẫu = sửa skill trên web.
Công cụ xuất tệp mẫu DEGO (`export_*_file`, đường tải một lần ai-CR-207) chỉ dùng khi cần đúng nhận diện công ty.

**Áp chung ba cửa:** T1–T3 nằm trong `assistant.tools` như mọi tool khác → bot Telegram, Trợ lý web và MCP dùng chung;
T1–T3 thuộc danh sách trắng `READ_TOOLS` (khóa chỉ đọc thấy).

### 5.6 Chuẩn dữ liệu công cụ cho AI bên ngoài (bản 1.2)

Áp cho mọi tool mới, sửa dần tool cũ bắt đầu từ T1–T3:

1. **Đường dẫn tuyệt đối** — `https://erp.degoholding.vn/...` (dev: `deverp`), không trả `/purchase-orders/123` trơn.
2. **Có tổng + phân trang** — trả `total`, `page`, `page_size`, `has_more`; kèm `note` dặn cách xem thêm / lọc hẹp.
3. **Khai dạng kết quả** — `outputSchema` + trả kèm `structuredContent` theo chuẩn MCP 2025-06-18, bên cạnh bản chữ.
4. **Đơn vị rõ** — tiền có `currency` (mặc định VND) và nói rõ trước / sau VAT; số lượng có `unit`; ngày ISO `YYYY-MM-DD`.
5. **Mã + nhãn** — trạng thái trả cả mã lẫn nhãn tiếng Việt (luật R2).
6. **Từ chối nói rõ** — `{denied, error}` nêu thiếu quyền gì và nhờ ai mở, không trả rỗng lặng lẽ (khuôn `base.denied`).
7. **Gọn** — chỉ trường AI cần; không trả HTML, không trả trường kỹ thuật nội bộ.

## 6. Giao diện (frontend-v2)

### 6.1 Định hướng chung

- **Không chép nhận diện CoreSkill** (màu cam, font). Dùng đúng hệ ERP v2 hiện có: shadcn / Radix + Tailwind 4, token màu
  của theme v2, icon cùng bộ đang dùng, `DataTable` cho mọi bảng (`docs/ui/table.md`), luật biểu mẫu ở
  `.claude/rules/frontend-v2-ui-conventions.md`. Chỉ lấy **cách tổ chức** của họ: rõ việc của từng vai, mỗi màn trả lời
  một câu hỏi, số liệu đặt trước chữ.
- **Ba lớp người dùng, ba lối vào:**
  - Nhân sự → **AI của tôi** (trong Trang cá nhân): nối AI, xem mình đọc được gì.
  - Trưởng phòng / biên tập → **Kho skill**: soạn và gán cho nhánh mình.
  - Quản trị → **Tổng quan**, **Khóa nhân sự**, **Nhật ký**, **Cấu hình**.
- Phân hệ mới trong `module-registry.ts`: **Kho skill AI** (nhóm Hệ thống / AI). Thẻ phân hệ chỉ hiện với người có
  `ai_skill.read` hoặc `ai_usage_log.read`; *AI của tôi* thì ai cũng có.
- Mọi chữ hướng dẫn trên màn viết như nói với nhân viên văn phòng, không dùng chữ "MCP", "JSON-RPC" ở lớp nhân sự —
  gọi là **"Kết nối AI của bạn với ERP"**.

### 6.2 Danh sách màn

| # | Màn | Ai | Nội dung chính |
|---|---|---|---|
| G1 | **Tổng quan** | Quản trị, trưởng phòng (nhánh mình) | Hàng 5 thẻ số: *Bộ skill* · *Skill đang dùng* · *Người đã nối AI* · *Lượt gọi 7 ngày* (kèm % so với 7 ngày trước) · *Từ chối & lỗi 7 ngày*. Biểu đồ cột lượt gọi 14 ngày (recharts, một màu, có tooltip theo ngày). Hai bảng nhỏ *Skill được đọc nhiều* và *Người dùng nhiều*. Khối cảnh báo: khóa sắp hết hạn trong 7 ngày, skill chưa ai đọc 30 ngày, lượt từ chối tăng bất thường |
| G2 | **Bộ skill** (danh sách) | Có `ai_skill.read` | Bảng: tên bộ · phòng chủ quản · số skill · phạm vi đọc (tóm tắt: *Toàn công ty* / *3 phòng ban* …) · mức bảo mật · cập nhật · trạng thái. Nút *Tạo bộ*, *Tải gói lên* |
| G3 | **Chi tiết bộ skill** | như trên | Tab *Skill* (bảng skill, kéo thả thứ tự) · tab *Ai được đọc* (cây phòng ban có ô tick *kể cả phòng con*, thêm chức vụ / cấp bậc / người / vai trò, dòng cấm tô đỏ; ô xem trước **"Ai đang thấy bộ này: 37 người"** bấm ra danh sách) · tab *Lịch sử* |
| G4 | **Soạn skill** | `ai_skill.write` | Hai cột: trái là trình soạn Markdown (thanh công cụ gọn, Ctrl+S lưu nháp, cảnh báo rời trang khi chưa lưu), phải là *Xem như AI đọc* (react-markdown). Ô *Tóm tắt cho AI* bắt buộc, có bộ đếm và gợi ý viết. Khối *Tệp đi kèm* (kéo thả, ≤ 2 MB). Nút *Xuất bản* (cần `approve`) tạo phiên bản mới kèm ghi chú thay đổi; tab *Phiên bản* so sánh hai bản cạnh nhau |
| G5 | **Khóa nhân sự** | `ai_mcp_key_admin.read` | Bảng mọi khóa trong phạm vi: người · phòng · tên khóa · mức · hạn · lần dùng cuối · trạng thái (chờ nhận / đang dùng / hết hạn / thu hồi). Lọc theo phòng, trạng thái. Nút *Phát khóa* mở hộp: chọn người hoặc cả phòng, mức, hạn. Chọn nhiều → *Thu hồi* (hộp xác nhận ghi rõ số khóa) |
| G6 | **Nhật ký sử dụng** | `ai_usage_log.read` | `DataTable` có bộ lọc: ngày · phòng ban · người · khóa · bộ / skill · công cụ · trạng thái · ứng dụng AI. Dòng bị từ chối có nhãn lý do. Xuất CSV (`export`). Trưởng phòng chỉ thấy nhánh mình |
| G7 | **Cấu hình** | Quản trị | Bật / tắt nhóm công cụ ERP qua MCP; trần tần suất; số ngày giữ nhật ký; câu dặn mặc định cho AI |
| G8 | **AI của tôi** (tab mới trong Trang cá nhân, thay tab *Kết nối MCP* hiện có) | Mọi người | Bước 1 *Chọn ứng dụng AI bạn đang dùng* (ô chọn có biểu tượng: Claude Desktop · claude.ai · Claude Code · ChatGPT · Cursor · Gemini CLI) → hiện đúng đoạn cấu hình của ứng dụng đó, nút *Sao chép*, ảnh chụp chỉ chỗ dán. Bước 2 *Khóa của bạn*: khóa đang có, khóa chờ nhận (nút *Nhận khóa*), tạo khóa mới. Bước 3 *Kiểm tra kết nối*: hiện lượt gọi gần nhất từ ứng dụng nào. Khối *AI của bạn đang đọc được*: danh sách skill. Khối *Lịch sử của bạn*: 20 lượt gọi gần nhất |

### 6.3 Trạng thái rỗng và thông báo

- Chưa có bộ skill: hình minh họa nhỏ + một câu *"Bắt đầu bằng một bộ skill cho phòng của bạn — ví dụ quy trình thu mua"*
  + nút *Tạo từ mẫu* (mồi sẵn từ `assistant/packs/*.md`).
- Nhân sự chưa nối AI: G8 mở thẳng bước 1, không bắt đọc gì trước.
- Phát khóa xong: toast *"Đã phát 12 khóa, mỗi người sẽ nhận thông báo để lấy khóa"*.

### 6.4 Demo theo chương (thứ đại ca thích ở CoreSkill)

Mục đích: trang giới thiệu Kho skill AI (và sau này mọi phân hệ lớn) có một khung **demo tự chạy theo chương**, người
mới xem 2 phút là hiểu.

- **Hình thức:** khung trình chiếu 16:9 phía trên; dưới là **dải chương đánh số** (01 … 09) — chương đang chạy có gạch
  tiến độ chạy ngang; bên dưới dải là **tiêu đề chương + một câu giải thích**. Nút tạm dừng / chạy tiếp bên trái dải; bấm
  chương nào nhảy tới chương đó.
- **Nội dung khung là giao diện thật thu nhỏ, không phải video:** dựng lại màn bằng chính component v2 với **dữ liệu
  giả**, nền phía sau làm mờ, hộp thoại đang thao tác nổi lên; con trỏ giả di chuyển + gõ chữ bằng thư viện `motion` đã
  có. Lợi: đổi giao diện thì demo đổi theo, không phải quay lại video; nhẹ; có chữ để máy đọc.
- **Chín chương đề xuất cho Kho skill AI:** 01 Chọn phòng ban sẽ dùng · 02 Tạo bộ skill · 03 Soạn hoặc tải skill lên ·
  04 Gán ai được đọc · 05 Phát khóa cho từng người · 06 Nối AI của nhân sự · 07 Hỏi AI một câu nghiệp vụ (AI đọc skill +
  tra ERP) · 08 Xem ai dùng gì · 09 Thu hồi khóa tức thì.
- **Tôn trọng `prefers-reduced-motion`:** người tắt hiệu ứng thì chỉ hiện ảnh tĩnh từng chương + chữ.
- **Dùng lại:** làm thành component chung `shared/ui/chapter-demo` (nhận danh sách chương: tiêu đề, mô tả, kịch bản các
  bước), để Help Center và trang giới thiệu các phân hệ khác dùng được.

### 6.5 Sắp xếp lại Trang cá nhân (bản 1.1)

Hiện trạng: **14 tab nằm ngang một hàng** — Thông tin cá nhân · Quá trình công tác · Quyết định bổ nhiệm · Việc cần làm
· Thông báo · Yêu cầu hỗ trợ · Thiết bị · Lịch sử đăng nhập · Telegram · Khóa AI · Bot nhớ gì · Bot vừa làm gì · Giao
diện (+ khối MCP giấu trong Khóa AI). Hàng tab tràn ngang, các phần AI rải rác, không có chỗ cho *AI của tôi*.

Đề xuất: đổi sang **bố cục cài đặt có thanh bên trái** (như trang cài đặt của các ứng dụng quen), bốn nhóm:

| Nhóm | Mục bên trong |
|---|---|
| **Hồ sơ** | Thông tin cá nhân · Quá trình công tác · Quyết định bổ nhiệm · Chữ ký |
| **Việc của tôi** | Việc cần làm · Thông báo · Yêu cầu hỗ trợ |
| **Trợ lý AI của tôi** | *Tổng quan* (đang nối kênh nào, khóa nào còn hạn, tiền model tháng này) · Liên kết Telegram · Khóa model AI · **Kết nối AI riêng** (G8 — thay khối MCP *Nâng cao*) · Bot nhớ gì · Bot vừa làm gì · *Cẩm nang AI đọc được* (sau K7) |
| **Bảo mật & hiển thị** | Đổi mật khẩu · Thiết bị · Lịch sử đăng nhập · Giao diện · Thông báo email |

- Đường dẫn giữ được từng mục (`/profile?tab=ai-connect`), nên link cũ trong thông báo / bot vẫn mở đúng chỗ (ánh xạ tên
  tab cũ → mục mới).
- Trên điện thoại thanh bên thành ô chọn nhóm ở đầu trang.
- Không đổi dữ liệu, không đổi API — chỉ dời và đổi tên giao diện. Làm được độc lập, trước K1.

### 6.6 Đặt ở đâu

- G1–G7: `frontend-v2/src/modules/ai-skill/` (thư mục phân hệ mới).
- G8: `frontend-v2/src/app/components/profile/` (thay `profile-ai-key-tab.tsx`).
- Demo theo chương: `frontend-v2/src/shared/ui/chapter-demo/` + kịch bản ở `modules/ai-skill/demo/`.
- `frontend/` (v1) **không làm** — đóng băng (D-026).

## 7. Lộ trình

Không đặt ngày; mỗi đợt nghiệm thu riêng được, dừng giữa chừng không để hệ nửa vời. Ngày công là ước lượng một người.

| Đợt | Việc | Điều kiện đủ | Ước |
|---|---|---|---|
| **K0** Chốt | Đại ca trả lời §9; cấp số CR | Có đáp án Q1–Q8 | — |
| **K1** Nền dữ liệu skill | Module `ai_skill`: 5 bảng + migration, IntEnum, schema có trần, CRUD bộ / skill / phiên bản / tệp, nhập gói .zip / .skill (SKILL.md có phần đầu `name` / `description`), 3 entity + `SCOPE_FIELDS` + 3 vai trò seed, chủ thể chức vụ / cấp bậc trong `subject_match`, hàm `visible_skills` | Bài kiểm: kế thừa phòng con, cấm thắng, thu hẹp theo skill, nháp không lộ, B-07 xanh | 4–5 |
| **K2** Skill qua MCP | Cổng B: 3 đường đọc skill cho người X; dịch vụ AI: 3 tool, câu dặn mới | Claude Desktop thật nối dev, hỏi một câu thu mua → AI tự `list_skills` → `read_skill` | 2 |
| **K3** Nhật ký lượt gọi | `tab_agent_mcp_call`, ghi mọi lượt kể cả từ chối, trần tần suất, beat gom nhật ký cũ | Bài kiểm khóa sai / hết hạn / quá trần đều có dòng | 1,5–2 |
| **K4** Phát khóa hộ | Cột mới `tab_agent_mcp_key`, khóa chờ nhận, phát cả phòng ≤ 50, thông báo chuông + Telegram, thu hồi theo lượt | Phát cho một phòng thử trên dev; người nhận lấy được khóa đúng một lần | 2 |
| **K5** Giao diện quản trị | G2–G7 | Typecheck + lint + vitest phân hệ xanh; thử trên dev đủ luồng tạo bộ → gán → phát khóa → xem nhật ký | 5–6 |
| **K6** AI của tôi + Tổng quan | G8 (thay tab Kết nối MCP), G1 | Nhân sự tự nối được Claude / ChatGPT theo hướng dẫn trên màn, không cần hỏi IT | 3 |
| **K7** Bot đọc chung kho | core_v2 + Trợ lý web gọi `visible_skills` thay `assistant/packs`; chuyển 5 gói hiện có + bộ nhà máy thành skill mẫu | Bot trả lời câu quy trình bằng skill trong kho; sửa skill thì lượt sau đã khác | 1,5–2 |
| **K8** Demo theo chương | `chapter-demo` + 9 chương Kho skill + trang giới thiệu trong Help Center | Xem hết 9 chương không lỗi, tắt hiệu ứng vẫn đọc được | 3 |
| **K9** Quản trị qua AI | Công cụ cho bot của quản trị: tạo / sửa skill dạng nháp → xác nhận, phát / thu hồi khóa → xác nhận | Mọi thao tác xóa / thu hồi đều qua thẻ xác nhận, có sổ thay đổi + hoàn tác 24 giờ | 2 |
| **K11** T1 báo cáo gom sẵn | `report_summary` mở 13 báo cáo qua hàm sau `/summary`, giữ đủ hai lớp gác; chuẩn §5.6 cho tool này; gỡ dần tool báo cáo riêng trùng việc | Người chưa được giao báo cáo bị từ chối; số khớp màn web trên 3 báo cáo thử | 1–1,5 |
| **K12** T2 sổ bộ dữ liệu | Khuôn khai báo `assistant/datasets/`; chuyển `analytics_query` mua hàng sang khuôn; thêm bộ **công nợ phải trả** + **yêu cầu thanh toán** | Bài kiểm phạm vi từng bộ (người phòng A không ra số phòng B); trần nhóm; không có đường sinh SQL | 3–4 |
| **K13** T3 đọc API danh sách | `erp_read` + danh sách trắng resource + bộ trường gọt; chuẩn §5.6 | Bài kiểm: resource ngoài danh sách bị từ chối; quá 5 trang báo `has_more` | 2–2,5 |
| **K10** Lên prod | Phụ thuộc Q7 | — | — |

### 7.1 Chuyển hướng 17/10/2026 — MCP là đường chính (bản 1.3)

Đại ca chốt: *"tạm thời bot tele là oke rồi, mình chuyển hướng qua mcp luôn, các phần liên quan tới tele bỏ qua một bên;
phần mới là một đường sử dụng thông qua các gói AI của người dùng, và họ tự trả tiền cho nó."*

- **Đường chính:** nhân sự dùng gói AI của chính họ (Claude, ChatGPT, Cursor, Gemini…) nối vào ERP qua cổng MCP. Tiền
  model do người dùng trả; công ty chỉ chịu máy chủ ERP.
- **Bot Telegram (dịch vụ AI, lõi core_v2): đóng băng tính năng** — vẫn chạy như hiện tại, chỉ vá khi hỏng thật hoặc
  lộ bảo mật. Không thêm công cụ / luật / đo đạc mới; không chạy gì tốn ví trạm modelapi.vn.
- **Gác lại các mục gắn Telegram:** thông báo khóa qua Telegram ở K4 (chỉ còn chuông); **K7** bot đọc chung kho; **K9**
  quản trị qua bot. Nếu sau này cần quản trị bằng lời thì làm thành công cụ quản trị cho **khóa được ghi của quản trị
  qua MCP** (mọi thao tác xóa / thu hồi bắt xác nhận tường minh), không qua bot.
- **P0** vẫn làm, nhưng khu *Trợ lý AI của tôi* đưa **Kết nối AI riêng** lên đầu; Telegram, Khóa model AI, Bot nhớ gì,
  Bot vừa làm gì xếp sau.

**Thứ tự mới:**

| Thứ tự | Phase | Ghi chú |
|---|---|---|
| 1 | **P0** Dọn Trang cá nhân | Lối vào *Kết nối AI riêng* rõ ràng |
| 2 | **K11** (đầu P1b) báo cáo gom sẵn | 1–1,5 ngày, giá trị ngay cho người đã nối MCP |
| 3 | **P1** Kho skill chạy được (K1 → K2 → K3) | |
| 4 | **P1b** còn lại (K12 → K13) | |
| 5 | **P2** Quản trị + AI của tôi (K4 bỏ phần Telegram, K5, K6) | |
| 6 | **P4** chỉ còn K8 Demo theo chương | |
| — | **P3 / K7, K9** | Gác cùng bot |
| — | **P5** Lên prod | Theo Q7 |

**Gom thành 5 phase (bản 1.1, thứ tự đã thay bằng §7.1)** — mỗi phase xong là dùng được một thứ trọn vẹn:

| Phase | Gồm | Xong thì có gì | Ước |
|---|---|---|---|
| **P0 — Dọn Trang cá nhân** | §6.5 | Trang cá nhân 4 nhóm, khu *Trợ lý AI của tôi* gom đủ phần AI, khối MCP ra khỏi chỗ giấu | 1,5–2 |
| **P1 — Kho skill chạy được** | K1 + K2 + K3 | Quản trị soạn skill, gán phòng ban; AI riêng của nhân sự đọc được skill + tra ERP; mọi lượt có nhật ký (DEV) | 8–9 |
| **P1b — Dữ liệu ba tầng** | K11 → K12 → K13 | AI lấy được báo cáo chuẩn, báo cáo tự ghép (mua hàng / công nợ / thanh toán) và chi tiết phiếu — đúng quyền, số do máy chủ tính | 6–8 |
| **P2 — Quản trị + AI của tôi** | K4 + K5 + K6 | Phát khóa hộ cả phòng, đủ màn quản trị, tổng quan, nhân sự tự nối AI theo hướng dẫn trên màn | 10–11 |
| **P3 — Một kho tri thức** | K7 | Bot + Trợ lý web đọc chung kho; xóa packs / knowledge-source khỏi mã (gỡ C1) | 1,5–2 |
| **P4 — Demo + quản trị bằng lời** | K8 + K9 | Trang giới thiệu có demo 9 chương; quản trị kho qua bot Telegram | 5 |
| **P5 — Lên prod** | K10 | Theo Q7 | — |

Tổng K1–K9 ≈ **24–27 ngày công** (cộng P0 ≈ 26–29; cộng P1b ba tầng ≈ 32–37). Thứ tự tối thiểu để có giá trị sớm: **K1 → K2 → K3 → K6** (≈ 11 ngày) là nhân sự đã
dùng được trên dev với skill quản trị nhập tay.

Chia người (đề xuất): Agent 4 giữ phía dịch vụ AI (K2 phần tool, K3, K4, K7, K9); một Agent ERP làm K1 + K5; một Agent
giao diện làm K6 + K8; Agent 1 gộp nhánh, dựng dev, kiểm và đo.

### 7.2 Hiện trạng 19/10/2026 và ba đợt mới (bản 1.4)

**Đối chiếu từng màn của CoreSkill (thanh bên bản demo) với mình:**

| Màn CoreSkill | Mình | Trạng thái |
|---|---|---|
| Tổng quan | G1 `/ai-skill/overview` | Xong (bao-CR-624) |
| Skill server | Bộ skill G2 + chi tiết G3 + soạn G4 (`/ai-skill/sets`) | Xong (bao-CR-621/623) |
| Quyền của tôi | Thẻ *Skill bạn được đọc* trong G8 AI của tôi | Xong (bao-CR-624) |
| Nhật ký sử dụng | G6 `/ai-skill/calls` | Xong (ai-CR-209 + bao-CR-623) |
| Nhân sự · Phòng ban · Chức vụ · Cấp bậc | Dùng lại HRM của ERP; gán quyền đọc theo 6 chủ thể, phòng con kế thừa | Xong (K1) — không dựng màn mới |
| Mời nhân sự / Lời mời | Không cần — tài khoản ERP có sẵn; thay bằng **phát khóa hộ** K4 | Xong (ai-CR-212/215) |
| Key nhân sự | G5 `/ai-skill/keys` | Xong (bao-CR-623) |
| MCP cho admin | **K9** quản trị bằng lời qua khóa được ghi | **Chưa — P7** |
| Gói cước | Không làm (một tập đoàn) | — |
| Cài đặt Biz | G7 `/ai-skill/settings` (nhóm công cụ, trần, câu dặn) | Xong (ai-CR-216 + bao-CR-624) |
| Hướng dẫn sử dụng | `/ai-skill/intro` + demo 9 chương (ai-CR-214); bài HDSD Help Center | Demo xong; **bài HDSD đang làm (Agent 2)** |
| Nối ChatGPT / claude.ai web | Cổng chỉ nhận khóa Bearer; hai nơi đó đòi OAuth | **Chưa — P6** |

**Đại ca chốt 19/10:** làm OAuth cho ChatGPT, làm K9, làm K7. Q4 chốt: prod bật 7 nhóm (mặc định 5 + thu mua + công nợ).
Q7 chốt: lên prod trưa 19/10 cùng đợt gộp erp-v2 → main (không chờ thí điểm 2–4 tuần).

| Đợt | Gồm | Nội dung | Ai | Ước |
|---|---|---|---|---|
| **P6 — OAuth cho cổng MCP** | K14 | ERP làm *authorization server* tối thiểu cho MCP: `/.well-known/oauth-authorization-server` + `/.well-known/oauth-protected-resource` (JSON, hết trả 404 của bao-CR-625 — nginx chuyển hai đường này sang api), `POST /api/oauth/register` (đăng ký client động RFC 7591, ChatGPT / claude.ai / Claude Desktop đều dùng), `GET /api/oauth/authorize` (màn ERP: đăng nhập nếu chưa, hiện *Ứng dụng X xin đọc ERP thay bạn — mức Chỉ đọc / Được ghi*, bấm Cho phép → mã), `POST /api/oauth/token` (PKCE S256 bắt buộc, refresh token xoay vòng), thu hồi. Token truy cập = một **khóa MCP loại OAuth** trong `tab_agent_mcp_key` (cùng mức, hạn, nhật ký, màn Khóa của tôi / Khóa nhân sự hiện dòng *qua ChatGPT*), nên `mcp.py` không đổi cách gác. `mcp_setup` mở `supported = true` cho claude.ai + ChatGPT với bước: *Thêm kết nối tùy chỉnh → dán địa chỉ → đăng nhập ERP → Cho phép*. Bài kiểm: PKCE sai bị chặn, mã dùng một lần, token hết hạn → 401 có `WWW-Authenticate` trỏ resource metadata, thu hồi là chặn ngay | Agent 4 | 3–4 |
| **P7 — K9 quản trị bằng lời** | K9 | Tool cho **khóa Được ghi** của người có `ai_skill.write` / `ai_mcp_key_admin.write`, theo đúng khuôn *nháp → `confirm_draft`* đang có: `draft_skill` (tạo / sửa skill nháp trong bộ), `draft_skill_publish`, `draft_skill_access` (gán / thu hồi), `draft_key_issue` / `draft_key_revoke`. Mọi lượt xác nhận đi qua service của `ai_skill` (phạm vi + cấm thắng giữ nguyên), ghi sổ thay đổi + hoàn tác 24 giờ (grp14) nơi áp được. Khóa Chỉ đọc không thấy các tool này. Bài kiểm: không có quyền → tool không liệt; xóa / thu hồi không xác nhận → không chạy | Agent 3 | 2 |
| **P8 — K7 một kho tri thức** | K7 | core_v2 + Trợ lý web đọc cẩm nang qua `visible_skills` (cổng B `skill_list/read`) thay `assistant/packs` + `knowledge-source`; chuyển 5 gói + bộ nhà máy thành **skill mẫu** (bộ *Cẩm nang hệ thống*, mức Mở, cả công ty) bằng script nhập gói; xóa packs / knowledge-source khỏi mã (gỡ C1). Bot vẫn đóng băng tính năng khác | Agent 4 (sau P6) | 1,5–2 |

Thứ tự: P6 và P7 song song (hai người, hai khu mã), P8 sau P6. Trong lúc prod đang gộp (11h30–12h15 ngày 19/10) không ai đẩy `erp-v2`.

## 8. Rủi ro và đường lui

| Rủi ro | Giảm thiểu |
|---|---|
| Nhân sự đọc dữ liệu ERP từ AI bên ngoài (dữ liệu rời khỏi máy chủ mình sang Anthropic / OpenAI) | Mặc định chỉ mở nhóm tra cứu phiếu của chính mình; nhóm nhạy cảm (công nợ, lương sau này) tắt qua MCP; mỗi lượt có nhật ký; ghi rõ trong quy định dùng AI của công ty |
| Lộ khóa | Băm, hạn ngắn mặc định 90 ngày, trần tần suất, thu hồi tức thì, cảnh báo khi một khóa gọi từ ứng dụng / IP lạ |
| Skill viết dở làm AI làm sai | Bắt buộc ô *Tóm tắt cho AI*; quyền xuất bản tách khỏi quyền soạn; phiên bản + so sánh + quay về bản trước |
| Ứng dụng AI không tự gọi `list_skills` | Câu dặn server; bước 3 của G8 có câu mẫu *"Hãy xem cẩm nang công ty trước khi trả lời"*; đợt sau mở `prompts` |
| Dịch vụ AI chưa có ở prod | K10 là quyết định riêng (Q7); trong lúc chờ, thí điểm trên dev với nhóm nhỏ |
| Đường lui | Mỗi đợt có cờ cấu hình tắt (tool skill khỏi MCP, phát khóa hộ, demo); bảng mới không đụng bảng cũ nên gỡ được |

## 9. Câu hỏi chờ đại ca chốt

| # | Câu hỏi | Em đề nghị |
|---|---|---|
| Q1 | Tên phân hệ hiển thị | **Kho skill AI** (nhân sự thấy *AI của tôi*) |
| Q2 | Ai được soạn / xuất bản skill | Quản trị toàn quyền; trưởng phòng soạn + xuất bản bộ của nhánh mình |
| Q3 | Cây phòng ban có dùng cột `parent` thật chưa (doc `01` từng ghi bỏ cây phòng ban) | Dùng cột `parent` sẵn có cho *kể cả phòng con*; phòng nào không có cha thì như phòng gốc |
| Q4 | Mở tool ERP qua MCP cho ai | Đợt đầu: chỉ nhóm tra cứu của chính mình + nghỉ phép + danh bạ; nhóm công nợ / tài chính tắt |
| Q5 | Khóa được ghi (tạo phiếu qua MCP) có cho phát hộ không | Không — khóa được ghi chỉ người dùng tự tạo |
| Q6 | Mức bảo mật mặc định của bộ mới | Mở; bộ nhạy cảm chọn Bảo vệ |
| Q7 | Khi nào lên prod — prod đang tạm dừng (19/09) và dịch vụ AI chưa chạy prod | Thí điểm dev với một phòng 2–4 tuần, đo, rồi trình riêng kế hoạch lên prod |
| Q8 | Nội dung mồi ban đầu | 5 gói `assistant/packs` (thu mua, văn thư, dự án, nghỉ phép, phòng họp) + bộ tri thức nhà máy |

Lưu ý Q4 với T2: bộ dữ liệu công nợ / thanh toán vẫn gác bằng quyền vai trò của người hỏi; Q4 chỉ quyết thêm có **mở
nhóm đó qua cổng MCP** (AI bên ngoài) hay chỉ cho bot / Trợ lý nội bộ.

**Đã chốt (không hỏi lại):**

| Ngày | Nội dung |
|---|---|
| 16/10 | Hướng B — xây trên ERP của mình, không dùng CoreSkill |
| 16/10 | Cho Agent 4 vá 4 lỗi cổng MCP → ai-CR-207 (d17329bc, DEV): liệt tool theo chủ khóa, khóa đọc theo danh sách trắng, tool báo cáo đòi quyền xem báo cáo, đường tải tệp một lần |
| 17/10 | Tra cứu thị trường: **giữ quyền vai trò** `customs_price.read` (hướng 1), không thêm khóa báo cáo riêng |
| 17/10 | **Ba tầng công cụ dữ liệu** (§5.5) + chuẩn dữ liệu (§5.6); bộ T2 làm trước: mua hàng, công nợ phải trả, yêu cầu thanh toán |

## 10. Liên quan

- `doc/agent-hub/06-cong-mcp.md` — cổng MCP bản 2.0 (ai-CR-063 + 207…216): một chỗ đọc đủ hợp đồng API cho giao diện và việc lên prod.
- `doc/agent-hub/14-cong-erp-api.md` — cổng B, nơi thêm 3 đường đọc skill.
- `doc/agent-hub/20-loi-hoi-thoai-moi.md` — lõi bot, chi phí trạm.
- `doc/erp/tai-lieu-ai/04-bao-mat-va-van-hanh.md` — bảng quyền từng tool; cập nhật khi mở tool qua MCP.
- `backend/app/core/subject_match.py`, `backend/app/modules/report_access/` — khuôn bảng quyền chủ thể.
