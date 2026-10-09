# 17 — Trí nhớ và ý định của bot

> Viết 09/10/2026 cùng ai-CR-137 (phase 13 đợt A, đại ca duyệt 09/10, Agent 1 giao). Gom về MỘT chỗ toàn bộ lôgic nhớ
> của Lạc Lạc / Trợ lý AI: nhớ gì, ở đâu, ai thấy, khi nào quên, và mỗi lượt gọi model nạp những gì theo thứ tự nào.
> Đợt B (ai-CR-138, 09/10): 13.4 màn «Bot nhớ gì về tôi» + thu hồi xóa sạch (§7), 13.5 điền đối tượng theo thói quen
> (§9), 13.6 đo độ đúng (§10).

## 1. Năm lớp nhớ

| Lớp | Bảng / nơi | Của ai | Ai ghi | Sống bao lâu | CR |
|---|---|---|---|---|---|
| Lõi sổ nhớ | `tab_agent_memory` (mỗi người một dòng Markdown bốn mục) | Một người | Người dùng («nhớ: …», tool `remember_fact`) + bot tự rút (đuôi «(tự rút)») | Tới khi «quên»; dòng có đuôi «(đến dd/mm/yyyy)» tự rút khi tới hạn | ai-CR-095, ai-CR-102, ai-CR-137 |
| Kho ghi chú | `tab_agent_note` + vector Qdrant `agent_personal` (payload `user_id`) | Một người | Người dùng («ghi chú: …») + vòng tóm tắt cuối buổi | Tới khi xóa (`revoked_at`) | ai-CR-095, ai-CR-102 |
| Tóm tắt cuộc | `tab_agent_conv_summary` (scope, scope_key) | Một cuộc (hội thoại web / chat riêng) | Nén hội thoại, tự động | Bot: cuộc mới sau 12 giờ im lặng thì bỏ; web: xóa theo hội thoại | ai-CR-136 |
| Sổ ý định | `tab_agent_intent` | Một người | Tự động mỗi câu hỏi | 180 ngày | ai-CR-137 |
| Điểm tự rút | `tab_agent_memory_candidate` | Một người | Vòng tự rút sau buổi | Đang đếm 45 ngày; đã ghi 120 ngày (gặp lại thì gia hạn); bia mộ 90 ngày | ai-CR-137 |

Không lớp nào gộp theo pháp nhân hay phòng ban — đó là trí nhớ TỔ CHỨC, làm ở phase khác. Mọi lớp lọc cứng theo
`user_id` lấy từ chat đã đăng nhập (bot) hoặc người đang đăng nhập (web), không bao giờ là tham số model điền.

## 2. Lõi và kho (ai-CR-095)

- Lõi: bốn mục cố định **Bản thân · Sở thích · Cách làm việc · Đã chốt**, trần 8.000 ký tự, nạp NGUYÊN VĂN vào mọi câu
  hỏi của người đó trên bot. Bộ đệm trong tiến trình 10 phút, ghi là xóa đệm.
- Kho: ghi chú dài, mỗi câu hỏi kéo 5 đoạn liên quan nhất (điểm ≥ 0,5). Qdrant / khóa hỏng thì ghi chú vẫn ở DB.
- Ba hàng rào dùng chung cho cả đường người dùng tự ghi lẫn đường bot tự rút: không ghi bí mật (`_SECRET_RE`: mật khẩu,
  khóa, token, số thẻ, số tài khoản, dãy ≥ 12 chữ số) · trùng thì không thêm (so không dấu) · `user_id` từ chat.

## 3. Tóm tắt cuối buổi (ai-CR-102)

Vòng nền 10 phút (`sessions.tick`): chat riêng đã đăng nhập im lặng ≥ 30 phút và có ≥ 3 câu hỏi thì một lượt model viết
3–8 gạch đầu dòng vào KHO với tiêu đề «Buổi dd/mm HH:MM–HH:MM». Dấu ranh giới là một dòng sổ tin `tom_tat_buoi`.
Từ ai-CR-137: vòng này bỏ qua chat nhóm (Telegram mã âm, Zalo `zg:`), và buổi nào tóm được thì chạy tiếp tự rút (§6).

## 4. Nén hội thoại (ai-CR-136)

Đơn vị nén là TỪNG cuộc, khóa (scope, scope_key): web = id hội thoại (scope 1), chat riêng = mã chat (scope 2), nhóm
(scope 3, chừa sẵn). Ba bậc theo ngân sách `ai_context_budget_tokens` (12.000): 50% lược kết quả công cụ cũ, 70% tóm nối
tiếp bằng một lượt model rẻ (lưu summary + `upto_id`), 90% mới bỏ lượt cũ. Hỏng / quá giờ → cửa sổ trượt cũ.
Chi tiết: `doc/agent-hub/15` (Agent 1 giữ) và change-log ai-CR-136.

## 5. Sổ ý định (ai-CR-137, 13.1 + 13.2)

Mỗi câu hỏi = một dòng `tab_agent_intent`:

| Cột | Ý nghĩa |
|---|---|
| `user_id` | Người hỏi (bot: tài khoản đã đăng nhập chat; web: người đăng nhập) |
| `channel` | 1 web · 2 Telegram · 3 Zalo (`intent_ledger.Channel`) |
| `scope`, `scope_key` | Khóa cuộc, dùng lại của nén hội thoại |
| `intent` | Nhãn lớn: 1 hoi · 2 viec · 3 mo_ho · 4 thao_tac · 5 tra_cuu · 6 du_lieu (`Intent`) |
| `sub_intent` | Nhãn con theo nghiệp vụ (`Sub`, bảng `SUB_CODES`), ví dụ `tra_cuu.cong_no`, `thao_tac.tao_ycmh` |
| `entities` | JSON `[{type, id \| code \| ref}]` — ncc · phap_nhan · du_an · phong · nhan_su · san_pham · chung_tu |
| `tools` | JSON tên công cụ đã gọi (≤ 12) |
| `outcome` | 1 trả lời được · 2 phải hỏi lại · 3 lỗi (`Outcome`) |
| `message_id` | Con trỏ tới TIN câu hỏi (`tab_agent_message` / `tab_assistant_message`) — chỉ để gắn nhãn tay trên dev (13.6); sổ vẫn không chép chữ |

Luật:

1. **Không lưu nguyên văn câu hỏi, không lưu câu trả lời.** Đối tượng chỉ lấy từ THAM SỐ ĐỊNH DANH của công cụ
   (`_ENTITY_ARGS`: `supplier_code`, `supplier`, `product_code`, `company`, `department(_id)`, `project`, `employee`,
   `code`) và mã chứng từ dò bằng mẫu trong câu (PO…, PYC…, YCMH…, YCBG…, YCTT…, ĐMH…). Tham số chữ tự do (`query`…) không
   bao giờ vào sổ. Tham số `entity` của công cụ là LOẠI chứng từ (purchase_order…), không phải pháp nhân.
2. **Ưu tiên id / mã hơn tên**: `department_id` lưu `id`, `*_code` và `code` lưu `code` in hoa; tên chỉ lưu (`ref`) khi
   công cụ chỉ nhận tên.
3. **Nhãn con TẤT ĐỊNH theo công cụ** (`TOOL_SUB`), không hỏi model: công cụ ghi / soạn nháp (50–79) thắng công cụ đọc
   (20–49); không gọi công cụ nào thì theo nhãn lớn (hoi → `hoi.chung`, tra_cuu → `nghien_cuu.web|link|tai_lieu` theo chế
   độ, viec → `viec.ghi`…). Công cụ lạ → `tra_cuu.khac`. Bài kiểm `test_moi_cong_cu_deu_co_nhan_con` đỏ khi thêm công cụ
   mới mà quên khai nhãn con.
4. **Kết cục «phải hỏi lại»** = câu trả lời KHÔNG gọi công cụ nào và dòng cuối kết bằng dấu hỏi (có gọi công cụ thì dấu
   hỏi cuối là lời mời, không tính).
5. Không ghi cho chat nhóm, không ghi khi chưa đăng nhập. Ghi hỏng thì nuốt lỗi — câu trả lời đã đi rồi.
6. Vòng dọn hằng ngày (`agent.group_purge`) xóa dòng quá 180 ngày.

Nơi ghi: bot `answer_question` (nhãn lớn từ bộ phân loại truyền xuống), `run_research`, đọc link (`_link_by_text`), nhánh
thao tác / sửa dữ liệu / giao việc của chat đại ca; web `conversation.chat` (nhãn lớn luôn `hoi` vì web không qua bộ phân
loại — nhãn con theo công cụ vẫn đúng).

## 6. Tự rút ghi nhớ (ai-CR-137, 13.3)

```
buổi chat RIÊNG im lặng 30' ──► tóm tắt cuối buổi (kho) ──► auto_memory.extract
                                                              │  đầu vào: bản tóm tắt + vài dòng đếm từ sổ ý định 30 ngày
                                                              │           + lõi hiện có + các điều đang theo dõi (có số)
                                                              ▼
                                         model rẻ (AGENT_MANAGER_MODEL, khóa của chính người đó) → ≤ 5 điều
                                                              ▼
                               observe: mỗi điều = một dòng tab_agent_memory_candidate, +1 lần gặp / buổi
                                                              ▼
                        ≥ 3 lần trên ≥ 2 ngày ──► GHI NGAY vào lõi: «… (tự rút) (đến dd/mm/yyyy)» (+120 ngày)
```

- **Điều nói một lần không bao giờ vào sổ.** Gặp lần đầu chỉ đếm. Ba lần cùng một ngày cũng chưa đủ.
- Model được đưa danh sách điều đang theo dõi kèm số; điều trùng ý thì trả lại SỐ (`{"id": n}`) thay vì viết lại, để đếm
  không trượt vì khác chữ. Số của người khác / số bịa → bỏ.
- Khử trùng: `key_hash` = sha1 của dòng đã bỏ dấu, đuôi «(tự rút)» và đuôi hạn. Điều người dùng đã tự ghi thì không rút đôi.
- `confidence` = min(1, lần/3) × min(1, ngày/2) — để màn đợt B hiển thị «đang để ý».
- Hết hạn: chưa đủ lần mà 45 ngày không gặp lại → `EXPIRED`. Đã ghi mà không gặp lại → dòng trong lõi tự rút khi tới hạn
  (cơ chế «(đến …)» sẵn có), vòng dọn đặt `EXPIRED`. Gặp lại khi còn < 30 ngày thì gia hạn đuôi.
- «quên: X» (lệnh chat hoặc tool `forget_fact`): xóa dòng khớp trong lõi VÀ mọi điều đang theo dõi / đã ghi khớp X thành
  **bia mộ** 90 ngày — buổi sau model có đề xuất lại cũng không đếm. Hết bia mộ thì đếm lại từ 0.
- **Không bao giờ rút từ tin NHÓM**: `sessions.tick` bỏ qua chat nhóm, `extract` từ chối chat nhóm, đầu vào chỉ là bản tóm
  tắt của chat riêng (bản tóm tắt nhóm ở `tab_agent_group_summary` không bao giờ được đọc).
- Báo một lần: lần đầu bot tự ghi cho một người, bot nhắn người đó một tin giải thích (đuôi «tự rút», xem «sổ nhớ», bỏ
  «quên: …»); con trỏ `auto_memory_notice:<user_id>` trong `tab_agent_cursor` chặn báo lại.
- Công tắc `agent_auto_memory_enabled` (sổ cấu hình, mặc định bật). Tắt thì sổ ý định vẫn ghi, chỉ thôi rút.
- Chi phí: một lượt model rẻ cho mỗi buổi đã tóm tắt (≥ 3 câu hỏi), ghi `tab_agent_run` bước 31 «Tự rút ghi nhớ».
- Web chưa có tự rút (web không có vòng tóm tắt cuối buổi) — chỉ ghi sổ ý định.

## 7. Riêng tư, xem và xóa (13.4, ai-CR-138)

| Việc | Trên chat | Trên ERP v2 — Trang cá nhân › tab «Bot nhớ gì về tôi» |
|---|---|---|
| Xem | «sổ nhớ» / «em (bot) nhớ gì về anh/chị/tôi/mình» — lõi + kho + tối đa 5 điều đang để ý · «xuất sổ nhớ» | Bốn mục lõi (dòng tự rút có nhãn + hạn), điều đang để ý (n/3 lần · n/2 ngày), thói quen + đề xuất, kho ghi chú |
| Thêm / sửa | «nhớ: …» | Thêm dòng từng mục; sửa từng dòng. Sửa dòng tự rút = dòng thành của người dùng (bỏ đuôi), điều gốc thành bia mộ |
| Xóa | «quên: …» | Xóa từng dòng (bia mộ), bỏ điều đang để ý, xóa ghi chú, **Xóa toàn bộ trí nhớ** |
| Quản trị xem sổ người khác | Không có đường nào | Không có — kể cả admin / quản lý |
| Thu hồi / nghỉ việc | `service.revoke_user_access` (ERP gọi khi khóa tài khoản, dịch vụ AI qua `/internal/revoke`) gọi `memory_view.wipe`: lõi, kho (kèm vector), điểm tự rút, sổ ý định, con trỏ báo tự rút | — |

API (chỉ đòi đăng nhập, người dùng lấy từ phiên, không tham số chọn người): `GET /api/agent-hub/me/memory` ·
`POST /me/memory/lines` · `PATCH /me/memory/lines` · `POST /me/memory/lines/delete` · `DELETE /me/memory/watching/{id}` ·
`DELETE /me/memory/notes/{id}` · `DELETE /me/memory`. Sửa / xóa chỉ dòng bằng (mục, NGUYÊN VĂN dòng cũ): dòng đã đổi ở
tab khác → 409, không sửa nhầm dòng bên cạnh.

## 8. Thứ tự nạp mỗi lượt gọi model

| Lượt gọi | Nạp (theo thứ tự) | Không nạp |
|---|---|---|
| Phân loại ý định (`manager.run_intent`) | Luật phân loại · vài tin gần nhất của chat (`_intent_context`) · việc đang mở (chat đại ca) · câu mới | Lõi, kho, tóm tắt cuộc |
| Trả lời bot (`answer_question`) | System: gói tri thức + hướng dẫn công cụ + thuật ngữ khớp câu + chân dung người hỏi → persona Lạc Lạc + luật trợ lý + luật nháp / đăng nhập + dòng tài khoản → **lõi sổ nhớ + 5 đoạn kho liên quan** → **thói quen từ sổ ý định (13.5)** → **bản tóm tắt cuộc** · Lượt: các lượt gần nhất (đã lược / cắt theo ngân sách) · câu mới | Nguyên văn sổ ý định |
| Trả lời web (`conversation.chat`) | System: gói tri thức + hướng dẫn công cụ + thuật ngữ + chân dung → `system` của trang → bản tóm tắt cuộc → thói quen từ sổ ý định (13.5) · Lượt: các lượt gần nhất · câu mới + tệp | Lõi / kho sổ nhớ (sổ nhớ là của bot) |
| Tóm tắt cuộc (nén, ai-CR-136) | Luật tóm · TÓM TẮT CŨ · các lượt từ mốc `upto_id` | Lõi, kho |
| Tóm tắt cuối buổi (ai-CR-102) | Luật tóm buổi · chép buổi (≤ 12.000 ký tự) | Lõi, kho |
| Tự rút ghi nhớ (ai-CR-137) | Luật rút · bản tóm tắt buổi · đếm 30 ngày từ sổ ý định · lõi hiện có · điều đang theo dõi | Tin nhóm, nguyên văn câu hỏi |
| Nghiên cứu / đọc link | Luật nghiên cứu theo chế độ · câu hỏi · nội dung trang | Lõi, kho, tóm tắt |

## 9. Dùng sổ ý định để đỡ việc (13.5, ai-CR-138)

- `intent_ledger.defaults_of`: trong 60 ngày, mỗi loại đối tượng (pháp nhân · NCC · dự án · phòng) lấy giá trị nhắc nhiều
  nhất nếu **≥ 3 lần VÀ ≥ 60%** số lần nhắc loại đó. Không áp đảo thì không đoán. Chỉ lấy mã / tên, không lấy id trần.
- `habit_block` chèn vào phần luật của lượt trả lời (bot + web): giá trị quen + luật «câu THIẾU đối tượng mà công cụ cần thì
  dùng giá trị quen VÀ nói rõ ngay câu đầu, ví dụ "Em hiểu là pháp nhân DEGO như mọi lần — khác thì anh/chị nói em nhé";
  câu đã nêu đối tượng thì theo câu».
- Đề xuất chủ động (`suggestions_of`): cùng một nhãn con TRA CỨU vào cùng một thứ trong tuần ở ≥ 3 tuần khác nhau (8 tuần
  gần nhất) → một dòng đề xuất trên màn «Bot nhớ gì về tôi». **Chỉ hiển thị, không bao giờ tự gửi**; nút bật bản tin
  theo đề xuất để đợt sau khi đại ca muốn.

## 10. Đo (13.6, ai-CR-138)

| Phép đo | Cách chạy | Ghi chú |
|---|---|---|
| Bộ câu mẫu cố định | `python scripts/intent_eval.py fixed` (cần khóa AI của chat chủ bot) · hoặc pytest với `AI_EVAL=1` | `test/backend/data/intent_samples.json`: 30 câu, mỗi nhãn ≥ 4, `min_accuracy` 0,85. Đổi model / luật phân loại thì chạy trước khi đưa lên |
| Gắn nhãn tay ~200 câu | `intent_eval.py export --out /tmp/y.csv` → điền `true_intent`, `true_sub`, `entities_ok` → `intent_eval.py score --file /tmp/y.csv` | Tệp xuất có NGUYÊN VĂN câu hỏi (lấy qua `message_id`) — chỉ để trên máy dev, gắn xong thì xóa, không commit |
| Tỷ lệ phải hỏi lại trước / sau | `intent_eval.py clarify --pivot YYYY-MM-DD [--days 14]` | Theo kênh; mốc nên là ngày 13.5 lên dev |

Bài kiểm luôn chạy: bộ mẫu hợp lệ (đủ nhãn, không trùng câu), bộ phân loại «trả hoi cho mọi câu» phải trượt ngưỡng
(chống xanh giả), chấm tệp nhãn tay, tỷ lệ hỏi lại, nhãn con theo công cụ (bộ mẫu `SAMPLES` của ai-CR-137).

## 10b. Sao lưu và lấy lại trí nhớ (ai-CR-139)

Cả năm lớp nhớ nằm trong DB của bot. Bot chạy tách DB thì DB `agent_hub` có lịch sao lưu riêng (01:20, prod thêm 13:20,
R2 `<env>/backup/agent_hub-*.sql.gz`), canh quá 26 giờ, khôi phục thử mỗi chủ nhật — xem `08-van-hanh-vps.md` §4.1.
Lấy lại trí nhớ của MỘT người bị xóa nhầm không cần dừng bot:
`agent_restore.sh <bản> --table tab_agent_memory --where "user_id=<id>"` (thêm `tab_agent_note`,
`tab_agent_memory_candidate`, `tab_agent_intent` nếu cần). Thu hồi tài khoản xóa sạch trí nhớ (§7) — bản sao lưu cũ vẫn
còn dữ liệu đó tới khi bị dọn theo `backup_keep`.

## 11. Mã nguồn

- `backend/app/modules/agent_hub/intent_ledger.py` — sổ ý định, nhãn con, đối tượng, kết cục, dọn.
- `backend/app/modules/agent_hub/auto_memory.py` — rút, đếm, ghi, gia hạn, bia mộ, hết hạn, báo một lần.
- `backend/app/modules/agent_hub/personal_memory.py` — lõi + kho; `forget` gọi `auto_memory.tombstone`.
- `backend/app/modules/agent_hub/sessions.py` — tóm tắt cuối buổi, gọi tự rút.
- `backend/app/modules/assistant/compaction.py` — nén hội thoại.
- `backend/app/modules/agent_hub/memory_view.py` — xem / sửa / xóa của chủ sổ, `wipe` khi thu hồi (ai-CR-138).
- `backend/app/modules/agent_hub/intent_eval.py` + `backend/scripts/intent_eval.py` — đo (ai-CR-138).
- `frontend-v2/src/app/components/profile/profile-memory-tab.tsx` — tab «Bot nhớ gì về tôi».
- Bảng: `tab_agent_intent`, `tab_agent_memory_candidate` (migration `grp05` + `agent0005`; cột `message_id` ở `grp06` +
  `agent0006`).
- Bài kiểm: `test/backend/test_agent_hub_y_dinh_tu_nho.py`, `test/backend/test_agent_hub_tri_nho_cua_toi.py`,
  `profile-memory-tab.test.tsx`.
