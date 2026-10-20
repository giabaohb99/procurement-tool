# 22 — AI KẾ HOẠCH VÀ PHÂN VIỆC (dùng dữ liệu cách làm việc qua Trợ lý và cổng MCP)

| | |
|---|---|
| Bản | 0.2 — 20/10/2026 (0.1 bản phác; 0.2: quyền chỉ quản trị, ghi nhận chức năng, đưa hoạt động AI vào hồ sơ — đợt A0 / D0) |
| Người yêu cầu | Đại ca — *"có 1 hệ AI chuyên dành cho phòng đó, rồi cho AI kế hoạch của công ty, các AI nói chuyện với nhau… phân tích, đưa ra quyết định đúng hơn dựa vào việc hằng ngày nhân sự làm hoặc data công ty, ra kế hoạch, ra tới danh sách công việc, phân cho ai luôn"*; *"mọi người dùng trợ lý hoặc qua MCP cũng tiếp cận được nguồn data này, cũng ghi nhận lại trên data này"* |
| Chia việc | **Chỉ số** (hồ sơ cách làm việc): anh Dược (duoc-CR-626/641/644). **Phần AI**: Agent 1 + Agent 4 (vai AI và MCP) |
| Nền đã có | Cổng MCP + Trợ lý web + bot ([`21`](./21-kho-skill-ai-mcp.md)), Kho skill theo phòng ban, bot lập kế hoạch việc vào Dự án (bao-CR-616, [`agent-hub/18`](../agent-hub/18-dieu-phoi-viec-theo-ke-hoach.md)), hồ sơ cách làm việc 58 chỉ số trên prod từ 20/10 |

---

## 1. Đích đến

Một người (trưởng phòng, ban điều hành) nói với AI của mình — Trợ lý web, bot, hay Claude / ChatGPT riêng qua MCP — một
**kế hoạch hoặc một mục tiêu**. AI trả về:

1. kế hoạch chia giai đoạn;
2. **danh sách việc** cụ thể, mỗi việc có tiêu chí xong, thời gian ước lượng;
3. **đề xuất người làm** cho từng việc, kèm lý do (đã làm loại việc này nhanh / ít bị trả lại, đang rảnh, không nghỉ phép
   trong khoảng đó);
4. **rủi ro**: ai đang quá tải, việc nào thường trễ.

Người hỏi **duyệt, sửa** rồi mới tạo thành task trong Dự án. Mọi đề xuất, chỗ người sửa và kết quả thật về sau đều được
**ghi lại** — đó là kho dữ liệu để lần sau AI đề xuất đúng hơn.

## 2. Nguyên tắc thiết kế (gợi ý của Agent 1)

1. **Máy tính số, AI viết chữ.** Thời gian trung bình theo loại việc, tải hiện tại, tỷ lệ trễ… do máy chủ tính bằng truy
   vấn cố định (như ba tầng dữ liệu §5.5 doc 21). Model chỉ đọc số đã tính sẵn để lập kế hoạch và giải thích. Model không
   tự đếm, không tự đoán số.
2. **"Học" = nhớ và so, không phải huấn luyện model.** Không train model riêng. "Học" ở đây là: lưu mọi đề xuất + chỉnh sửa
   + kết quả thật, rồi lần sau tra lại kế hoạch tương tự và hiệu chỉnh ước lượng theo số thực đo. Rẻ, minh bạch, sửa được.
3. **AI phòng ban = bộ skill + phạm vi dữ liệu, không phải một bot chạy riêng.** Một lõi AI dùng chung; "AI Thu mua" chỉ
   khác ở chỗ nạp bộ skill của phòng Thu mua và chỉ thấy dữ liệu phòng đó. "Các AI nói chuyện với nhau" làm thành **một
   lượt gọi công cụ** sang phòng khác (hỏi năng lực / tải của phòng đó), không phải nhiều bot nhắn qua lại — ít tốn tiền,
   ít hỏng, dễ kiểm.
4. **Chỉ đề xuất, người quyết.** Mọi việc tạo task / giao người đi qua khuôn *nháp → xác nhận* đang có (`draft_*` →
   `confirm_draft`), có sổ thay đổi và hoàn tác 24 giờ.
5. **Quyền giữ nguyên hai lớp.** Ai hỏi qua kênh nào (Trợ lý, bot, MCP) cũng chỉ thấy đúng phần vai trò + phạm vi của
   người đó cho phép. Dữ liệu hành vi chi tiết của từng người giữ chặt hơn dữ liệu năng lực tổng hợp (§6).

## 3. Kiến trúc

```
Người hỏi ── Trợ lý web / bot / Claude · ChatGPT qua MCP ──► lõi AI (core_v2 hoặc AI của người dùng)
                                                              │ gọi công cụ (đều gác quyền + ghi nhật ký)
        ┌─────────────────────────────┬───────────────────────┼──────────────────────────┬──────────────────────┐
        ▼                             ▼                       ▼                          ▼                      ▼
  plan_context (MỚI)          team_capacity (MỚI)     task_type_stats (MỚI)      list_skills / read_skill   draft_work_plan
  gom đủ bối cảnh một lần:    người · vai trò · tải    loại việc → trung vị       (cẩm nang phòng)           → confirm_draft
  phòng, người, tải, nghỉ,    đang ôm · nghỉ phép ·    thời gian, tỷ lệ trễ,                                  → task Dự án
  việc tương tự đã làm        lịch làm việc            bị trả lại, theo người
        │                             │                       │
        └──────────── số do MÁY CHỦ tính từ: Dự án · nhật ký thao tác · hồ sơ cách làm việc (Được) · nghỉ phép · lịch
                                                              │
                         ghi lại: tab_ai_plan_proposal (đề xuất) + phần người sửa + kết quả thật (MỚI)
```

## 4. Công cụ AI cần thêm (vai ai-mcp)

| Công cụ | Trả về | Gác quyền |
|---|---|---|
| `team_capacity(department, from, to)` | Mỗi người: vai trò, số việc đang mở, việc quá hạn, ngày nghỉ phép trong khoảng, giờ làm theo lịch | Trưởng phòng: phòng mình (+ phòng con). Quản trị: tất cả |
| `task_type_stats(task_type, department?, person?)` | Trung vị / p90 thời gian xong, tỷ lệ trễ, tỷ lệ phải làm lại, số mẫu | Như trên; số theo người chỉ khi đủ ≥ 5 mẫu |
| `usage_profile(person)` | Tóm tắt hồ sơ cách làm việc (58 chỉ số + nhãn) | **Chờ đại ca chốt §8 câu 1** |
| `plan_context(goal, department, deadline)` | Gom ba công cụ trên + việc tương tự đã làm (tra tab_ai_plan_proposal) thành một gói số liệu cho model | Hợp của các quyền trên |
| `draft_work_plan` (đã có) | Thêm: mỗi việc có `estimate_hours`, `task_type`, `assignee_reason` | Như hiện nay (khóa Được ghi / bot) |

Mọi công cụ theo chuẩn §5.6 doc 21: số đã tính sẵn, có đơn vị, có `has_more`, có link mở trên ERP.

## 5. Dữ liệu cần thêm

**Phần anh Dược (chỉ số)** — đề nghị thêm nhóm **3.7 Năng lực theo loại việc**:
- thời gian trọn vòng từng loại phiếu theo người (tạo → xong / được duyệt), trung vị và p90;
- số lần bị trả lại / làm lại trên mỗi loại;
- khối lượng theo tuần mỗi loại.

**Phần Dự án (task có cấu trúc)** — để AI học được "việc loại X mất bao lâu, ai làm tốt":
- `task_type` (danh mục loại việc của từng phòng, quản trị khai);
- `estimate_hours` (ước lượng lúc giao) và thời điểm bắt đầu / xong thật;
- kết quả: đạt / phải làm lại / hủy.

**Phần anh Dược — ghi nhận "dùng chức năng gì, dùng ra sao"** (đại ca 20/10: *"họ hay sử dụng chức năng gì, sử dụng ra
sao"*). Hiện biết người dùng ở màn nào bao lâu (khi bật công tắc) nhưng chưa biết trong màn họ bấm gì:
- loại sự kiện mới **Bấm chức năng** (`UI_ACTION`): nút / tính năng chính mỗi màn gắn **mã cố định** từ một danh mục
  (vd `filter_apply`, `column_toggle`, `print`, `export_excel`, `copy_line`, `bulk_approve`, `drag_kanban`); chỉ gửi mã,
  không gửi chữ người dùng gõ (giữ nguyên tắc không lưu từ khóa);
- theo dõi form mở rộng từ 6 form lên toàn bộ form chính (YCTT, nhận hàng, văn bản, đặt xe, duyệt dấu, phòng họp, việc dự án);
- báo cáo **theo chức năng** đặt cạnh báo cáo theo người: số người dùng, số lần dùng, tỷ lệ bỏ dở, tỷ lệ lỗi — để biết
  chức năng nào khó dùng mà sửa. Ước 3–4 ngày.

**Phần AI — đưa hoạt động AI vào hồ sơ cách làm việc** (soát 20/10: từ khi tách dịch vụ AI ngày 19/10, Trợ lý web, bot
Telegram và nhật ký cổng MCP đều nằm ở DB `agent_hub`; bộ chỉ số chỉ đọc DB ERP nên `assistant_questions` gần như luôn 0,
MCP và Telegram không được đếm; việc AI làm hộ ghi ở nhật ký thao tác là `entity=assistant`, bộ chỉ số chỉ đếm
`actor_kind = 1` nên không tách được *người tự làm* với *nhờ AI làm*):
- **(Agent 4)** dịch vụ AI gom **số đếm** theo người × ngày rồi đẩy sang ERP qua cổng B (chạy được cả chế độ nhúng): lượt
  dùng theo kênh (web / Telegram / MCP), ứng dụng (Claude / ChatGPT / khác, lấy từ `client_name`), nhóm công cụ (theo
  `mcp_settings.GROUPS`), số lượt bị từ chối quyền, số bản nháp tạo / được xác nhận. KHÔNG chuyển nội dung câu hỏi.
  Bảng đích phía ERP: `tab_ai_usage_daily` (người × ngày × kênh) để bộ chỉ số đọc như các nguồn khác;
- **(Agent 4)** đánh dấu thao tác **có AI làm hộ** trong `tab_audit_log` (cột / cờ `via_ai` + kênh) ở mọi đường
  `confirm_draft` và công cụ ghi, để tách được với thao tác người tự bấm;
- **(anh Dược)** nhóm chỉ số **3.8 Dùng AI**: kênh hay dùng, mức dùng theo tuần, nhóm việc hay nhờ AI, tỷ lệ phiếu soạn
  bằng AI so với tự làm, số lần bị từ chối quyền (gợi ý cấp thêm quyền). Ước Agent 4 2–3 ngày, anh Dược 1–2 ngày.

**Phần AI (kho học)** — bảng `tab_ai_plan_proposal`: người hỏi, kênh (Trợ lý / bot / MCP + ứng dụng), mục tiêu, gói số
liệu đã đưa model, kế hoạch đề xuất, bản sau khi người sửa (diff), task đã tạo, và sau khi xong: thời gian thật so với
ước lượng. Giữ lâu dài.

## 6. Quyền và quyền riêng tư

**Đại ca chốt 20/10/2026:** *"chỉ có quyền quản trị là cao nhất là được thao tác"* — dữ liệu hồ sơ cách làm việc chỉ
quản trị xem / thao tác; **AI thì ai cũng dùng được**.

| Loại dữ liệu | Ai thấy |
|---|---|
| Hồ sơ hành vi chi tiết (giờ vào ra, màn nào, ở bao lâu, nhãn kiểu làm việc) | **Chỉ quản trị** (khớp thiết kế anh Dược, ReportKey 14). Công cụ `usage_profile` chỉ hiện với người có quyền báo cáo 14 |
| Năng lực tổng hợp + tải (team_capacity, task_type_stats) | Quản trị. Người khác dùng AI lập kế hoạch vẫn được AI **dùng** số này để đề xuất, nhưng chỉ thấy kết quả đề xuất (ai làm, ước bao lâu), không xem được bảng số của từng người |
| Kế hoạch + đề xuất giao việc | Người hỏi và người được giao việc trong đó |

**Mục đích ghi nhận thao tác hằng ngày** (đại ca 20/10): biết nhân sự khó khăn ở đâu để sửa hệ thống cho hợp lý — tức
dùng để cải tiến phần mềm và hỗ trợ người dùng, không để chấm điểm / phạt tự động. Thông báo cho nhân viên đúng mục
đích này trước khi bật thu sự kiện giao diện (công tắc đang tắt trên prod từ 20/10).

## 7. Lộ trình

| Đợt | Nội dung | Ai | Ước |
|---|---|---|---|
| A0 | Đưa hoạt động AI vào hồ sơ: `tab_ai_usage_daily` qua cổng B + cờ `via_ai` trong nhật ký thao tác (§5) | Agent 4 | 2–3 ngày |
| D0 | Nhóm 3.8 Dùng AI + sự kiện Bấm chức năng + form mở rộng + báo cáo theo chức năng (§5) | Anh Dược | 4–6 ngày |
| A1 | `team_capacity` + `task_type_stats` (từ Dự án + nhật ký thao tác + nghỉ phép + lịch), qua Trợ lý / bot / MCP, gác quyền + nhật ký | Agent 4 | 4–5 ngày |
| A2 | `plan_context` + `draft_work_plan` có ước lượng / loại việc / lý do giao; `tab_ai_plan_proposal` ghi đề xuất + chỉnh sửa | Agent 4 (+ Agent 3 màn duyệt kế hoạch) | 1–1,5 tuần |
| D1 | Nhóm chỉ số 3.7 + Dự án có `task_type` / `estimate_hours` / kết quả | Anh Dược (+ Agent 3 màn Dự án) | 1–1,5 tuần |
| A3 | Vòng học: đóng task → so ước lượng với thực tế, hiệu chỉnh `task_type_stats`; tra kế hoạch tương tự | Agent 4 | 1 tuần |
| T1 | Thử với một phòng (đề xuất Thu mua): soạn bộ skill phòng, trưởng phòng dùng 2–4 tuần, đo | Agent 1 + phòng | 2–4 tuần |
| A4 | Hỏi chéo phòng (AI phòng A hỏi năng lực phòng B) nếu T1 cần | Agent 4 | sau T1 |

A1 và D1 chạy song song. Có bản dùng thử cho một phòng sau khoảng **5–6 tuần**; đề xuất giao việc đáng tin cần thêm
**4–8 tuần dữ liệu thật**.

## 8. Câu hỏi chờ đại ca chốt

1. ~~Ai được xem hồ sơ hành vi chi tiết qua AI?~~ **ĐÃ CHỐT 20/10: chỉ quản trị; AI ai cũng dùng được** (§6).
2. **Phòng thử đầu tiên** (đề xuất Thu mua — dữ liệu dày nhất, đã có cẩm nang). *Thử* = cho một phòng dùng AI lập kế
   hoạch / giao việc trước 2–4 tuần, đo đề xuất đúng sai, sửa, rồi mới mở cho cả công ty.
3. **Danh mục loại việc** do ai khai cho từng phòng (đề xuất: trưởng phòng, quản trị duyệt).
4. Kênh ưu tiên khi thử: Trợ lý web / bot / MCP (đề xuất: MCP + Trợ lý web, vì bot đang đóng băng tính năng).
