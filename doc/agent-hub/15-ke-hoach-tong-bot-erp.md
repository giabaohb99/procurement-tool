# Kế hoạch tổng — Bot AI của ERP (Agent Hub + Trợ lý AI)

Bản 09/10/2026, viết theo yêu cầu của đại ca: gom lại **đã làm gì · làm tiếp theo phase nào · định hướng về sau**, để
đại ca đọc một chỗ rồi chốt hướng làm tiếp. Chỉ nói **bot ERP**. Bot Zalo của IDA (kho `ida-zalo-assistant`) có lộ
trình riêng ở `doc/06-lo-trinh.md` của kho đó.

Chi tiết từng mảng vẫn nằm ở các tệp cũ — tệp này không chép lại:
- Danh sách tính năng + trạng thái: `04-danh-sach-tinh-nang.md`
- Lộ trình tách dịch vụ / A2A: `13-lo-trinh.md` (ở đó gọi là «phase S» — từ nay là **phase 11**)
- Cấu trúc + kỹ thuật (bot tự sửa phần mềm + AI của ERP): `16-kien-truc-ky-thuat.md`
- Sổ CR: `doc/tai-lieu-ky-thuat/change-log-ai.md` (ai-CR-001 … 135)

---

## 0. Đang ở đâu (một đoạn)

Bot ERP đã là một **agent** đúng nghĩa: tự chọn công cụ trong ~62 công cụ ERP (gác đúng quyền của người hỏi), chạy
trên web, Telegram và Zalo (dev), có trí nhớ cá nhân hai tầng, tra web / đọc link / đọc tệp, làm việc với Google Lịch /
Drive / biên bản họp, và có hẳn một **dây chuyền tự sửa phần mềm** (ticket → kế hoạch → máy sửa mã → kiểm → đại ca
duyệt). Từ 08/10 dịch vụ AI **tách riêng** khỏi ERP (DB `agent_hub`, chỉ nói chuyện với ERP qua cổng B có chữ ký).

Mọi thứ đang chạy trên **DEV**. Prod giữ nguyên từ 19/09 (luật tạm dừng prod) — chưa CR `ai-` nào lên prod.

---

## Đánh số phase thống nhất (đại ca chốt 09/10/2026: chỉ dùng SỐ)

Trước đây có ba kiểu đánh số chồng nhau: «bậc 1–4» (doc 01), «phase 0–10 + 7b» (doc 04), «phase S / S-0…S-6» (doc 13).
Từ nay **chỉ dùng một dãy số dưới đây**. Doc 04 và doc 13 giữ nguyên chữ cũ để tra lịch sử; khi nói chuyện / ghi CR mới
thì dùng số mới.

| Phase mới | Tên | Số cũ | Trạng thái |
|---|---|---|---|
| 1 | Bot sửa mã gốc (nhận việc, rà, sửa, kiểm, gộp, deploy dev) | phase 0 | Xong |
| 2 | Khóa quyền sửa mã | phase 1 | Còn K-02 / K-03 (tay đại ca trên GitHub) |
| 3 | Bot lên dev (Lạc Lạc, máy sửa mã tách rời) | phase 2 | Xong 25/09 |
| 4 | Trợ lý từng người (chuông, nhắc việc, tin thoại) | phase 3 | Xong 25/09 |
| 5 | Cổng MCP | phase 4 | Xong 25/09, chưa ai dùng thật |
| 6 | Google cá nhân (Lịch, Drive) | phase 5 | **Xong** — đại ca đã cấu hình và dùng (10/10); mở cho nhiều người: xem §Cập nhật 10/10 |
| 7 | Quy trình code hai máy chủ | phase 6 | Phần chính xong 05/10; còn xem thử qua tunnel, chờ VPS |
| 8 | Tự vận hành (OPS / HEAL) | phase 7 | Xong 05/10, công tắc mặc định TẮT |
| 9 | Trợ lý cá nhân (sổ nhớ, tóm tắt buổi, thẻ cá nhân) | phase 7b | Xong 06–07/10 |
| 10 | Thư ký biên bản họp | phase 10 | **Xong** — đại ca thử tệp họp thật 10/10 |
| 11 | Tách dịch vụ AI khỏi ERP (DB riêng, cổng B) | phase S (S-0…S-6) | S-0…S-4 xong dev 08/10; S-5 / S-6 chờ VPS AI |
| 12 | Kênh Zalo công ty, màn Nhóm chat, đọc link / tệp, quyền dùng bot | (gom ai-CR-120…135) | Xong dev 08–09/10 |
| **13** | **Hiểu ý định + tự ghi nhớ** | mới | **Xong dev 09/10** — ai-CR-137 (đợt A) + ai-CR-138 (đợt B); logic ở `17-tri-nho-va-y-dinh.md` |
| **14** | **Nén hội thoại** | mới | **Xong dev 09/10** — ai-CR-136 (84faee30) |
| **15** | **Một lớp duyệt chung khi ghi** | mới | Kế hoạch |
| **16** | **Gọn và đo** | mới | Kế hoạch |
| 17 | Lên prod (stack tách) | mới | Chờ đại ca mở prod |
| 18 | Nhóm chat + nhắc việc (phần còn treo) | mới | Kế hoạch |
| 19 | Kho tri thức cấp công ty | mới | Kế hoạch |
| 20 | Lõi mở (gọi MCP ngoài, A2A, giao việc tính ngân sách) | phase 8 | Ghi nhận |
| 21 | Nhiều kênh, nhiều bot (Zalo OA, bot riêng từng người) | phase 9 | Ghi nhận |

**«Bậc 1–4» không phải phase**: đó là **mức tự chủ** của bot sửa phần mềm (1 chỉ lập kế hoạch · 2 sửa + PR, gộp khi đại
ca đồng ý — đang ở đây · 3 tự gộp khi kiểm xanh · 4 lên prod có người duyệt). Giữ tên «bậc» để khỏi lẫn với phase.

---

## Cập nhật 10/10/2026 — đợt 09-10/10 (ai-CR-139 … 159, tất cả DEV)

- **Phase 13, 14 xong**, thêm sao lưu DB bot (139), bản tin bật/tắt trong chat (140), quay lại DB bot qua thẻ (141).
- **Phiếu qua bot** (bảng tiến độ: nhóm G ở `04-danh-sach-tinh-nang.md`): hỏi lại khi thiếu ý (142), phiếu nháp của tôi +
  xóa nháp (143), dùng lại YCMH/YCBG nháp (156), sửa phiếu (lý do / ngày / loại nghỉ, dòng hàng) + xóa phiếu nháp của mình
  (151, gom AI-0006), nút xác nhận qua cổng B (152), thẻ dùng một lần (153), *quyền của tôi* + hướng dẫn mới (157), chi
  phí từng biên bản họp (158), bài Help Center (159).
- **Phase 15 (duyệt chung) làm được một phần:** sửa / xóa phiếu đã đi chung một kiểu thẻ *cũ → mới → Xác nhận*, kiểm lại
  từ đầu lúc bấm, mỗi thẻ dùng một lần. Còn thiếu: gom thẻ nháp «tạo» và cổng sửa hàng loạt về cùng lớp, nhật ký có
  **hoàn tác một chạm**.
- **Phase 6 và 10 xong** (đại ca 10/10): Google đã cấu hình và đọc được tệp họp; biên bản họp thử tệp thật xong.
  Mở Google cho nhiều người: mỗi người tự **Nối Google** ở Trang cá nhân; ứng dụng Google đang ở chế độ *Testing* thì
  từng Gmail phải nằm trong danh sách Test users (tối đa 100) và cứ 7 ngày phải nối lại — muốn bỏ thì *Publish app*
  (chưa xác minh, dưới 100 người) hoặc chuyển *Internal* nếu công ty dùng Google Workspace.
- **Dây chuyền sửa mã gọn** (bot tự sửa phần mềm): rà mã → thẻ xác nhận có *xong thì làm được gì* → ok → Claude Code làm →
  bài kiểm không đỏ thì tự gộp + lên dev, dựng lại cả bot khi cần (149, 150, 153, 154, 155); bỏ luật lệch 30%, thêm canh
  ranh giới bot / ERP.

## 1. Đã làm (10 mảng)

| # | Mảng | Đã có | CR chính |
|---|---|---|---|
| 1 | Kênh | Web Trợ lý AI · Telegram (chữ, thoại, ảnh, tệp; mỗi người tự nối bằng mã) · Zalo tài khoản công ty (dev, chờ quét QR) · cổng MCP · dùng bot phải có quyền `assistant.read` · màn «Người dùng bot» | 038, 061, 063, 111, 122, 129–131 |
| 2 | Tra cứu ERP | ~62 công cụ theo nhóm (thu mua, công nợ, nghỉ phép, hải quan, văn bản, việc, nhân sự, duyệt…), mỗi công cụ gác quyền + phạm vi của người hỏi, không cho AI tự viết SQL · chuông ERP đẩy sang chat · giới hạn lượt theo người | 009, 059, 062, 120 |
| 3 | Soạn nháp / tạo chứng từ | Nghỉ phép, YCBG, YCMH, phiếu hỗ trợ, việc Dự án: AI soạn nháp → người dùng xác nhận mới tạo · sửa dữ liệu hàng loạt qua cổng duyệt · đề nghị thanh toán CẤM tạo từ chat | 046–049, 073, 074, 080 |
| 4 | Trí nhớ + học | Sổ nhớ cá nhân hai tầng (lõi luôn nạp + kho tìm theo nghĩa) · tóm tắt buổi tự động · tìm lại tin cũ 180 ngày · sổ thuật ngữ theo phòng ban, bot tự đề xuất thuật ngữ / báo thiếu tính năng · sổ khóa AI nhiều hãng, tự lùi khóa | 077–079, 095, 098, 102, 106 |
| 5 | Tra web / đọc | Tìm web (Gemini, hỏng thì DuckDuckGo / Bing — không cần khóa) · kiểm chứng · đọc PDF / Word / Excel · đọc bài theo link · đọc tệp theo link (Drive công khai, arXiv) | 044, 105, 110, 115, 133, 134 |
| 6 | Nhóm chat | Ghi lặng tin nhóm Telegram / Zalo · công cụ đọc + tóm tắt nhóm · màn «Nhóm chat» trên ERP v2 (quản lý AI thấy hết, có nhật ký xem) | 105, 123, 126 |
| 7 | Họp + Google | Lịch / Drive cá nhân · bản tin 8h · nhắc trước họp · dời / hủy lịch · biên bản họp → rút việc + lịch → Word chuẩn DEGO | 060, 064, 083, 084, 104, 112–117 |
| 8 | Bot sửa phần mềm | Ticket → rà mã → kế hoạch → máy sửa mã (máy đại ca) → cổng kiểm → PR → đại ca duyệt; hai chỗ dừng bắt buộc · máy tự cập nhật · nhặt lại lượt bị ngắt | 001–030, 054–058, 076, 081, 082, 124, 127 |
| 9 | Vận hành | `deploy.sh` · thao tác VPS có duyệt + sao lưu + hoàn tác · tự vận hành O-01…O-06 (công tắc mặc định TẮT) · quyền `agent_ops` nhận tin vận hành · Zalo văng chỉ báo một lần | 067–069, 072, 085, 132, 135 |
| 10 | Tách dịch vụ AI | `AGENT_MODE` 3 chế độ · DB riêng · cổng B `/api/agent-gw/*` chữ ký HMAC · sổ JSON qua cổng · vá treo / lỗi model khi tách | 119, 128 (+ hai bản vá 08/10) |

---

## 2. Chỗ còn hở (vì sao cần kế hoạch này)

1. **Bot hiểu ý định để CHỌN ĐƯỜNG, chưa hiểu để HỌC NGƯỜI DÙNG.** Bộ phân loại có sẵn 6 nhãn (`hoi`, `viec`,
   `thao_tac`, `tra_cuu`, `du_lieu`, `mo_ho`) + phạm vi cá nhân / công ty (003, 007, 028, 095). Nhưng kết quả phân loại
   dùng xong là bỏ — không ai biết người này hay hỏi gì, về đối tượng nào, lúc nào.
2. **Trí nhớ chỉ đầy khi người dùng / model chủ động.** Lõi nhớ chỉ ghi khi model tự gọi `remember_fact` trong lượt
   trả lời. Thực tế người dùng không bao giờ nói «nhớ giúp anh» → bảng lõi trên dev đang **0 dòng**. Đại ca muốn bot
   **tự rút** điều đáng nhớ từ cách người ta hỏi.
3. **Không có nén hội thoại.** Web giữ 20 lượt, Telegram 8 lượt / 2 giờ / 6.000 ký tự — quá thì CẮT BỎ. Việc dài nhiều
   bước sẽ quên đầu câu chuyện.
4. **Ghi dữ liệu mỗi chỗ một kiểu duyệt** (form nháp trên web, «tạo» trên Telegram, cổng duyệt sửa hàng loạt). Chưa có
   một lớp chung «xem thay đổi → duyệt → ghi → hoàn tác».
5. **Chưa đo được chi phí / chất lượng theo từng lượt** đủ để quyết định (gửi bao nhiêu khai báo công cụ mỗi lượt, lượt
   nào tốn, câu nào phải hỏi lại).
6. **Chưa lên prod.** Sổ CR có vài dòng lệch (002 vẫn «Đang làm», 004 vẫn «Đề xuất», thiếu 090, 089 ghi hai lần) —
   dọn khi chuẩn bị lên prod.

---

## 3. Các phase làm tiếp

Đánh số nối tiếp bảng trên. Thứ tự theo ý đại ca 09/10: **hiểu ý định trước**, rồi tới những thứ làm bot «khôn» khi việc dài, rồi an toàn khi ghi,
rồi mới lên prod và mở rộng.

### Phase 13 — Hiểu ý định + tự ghi nhớ (ưu tiên số 1) — xong dev 09/10 (ai-CR-137, ai-CR-138)

Mục tiêu: người dùng chỉ việc hỏi như thường; bot tự hiểu họ là ai, hay làm gì, và dùng điều đó cho lần sau.

| Việc | Cách làm |
|---|---|
| 13.1 Sổ ý định | Mỗi câu hỏi ghi một dòng: người hỏi, nhãn ý định, **đối tượng nhắc tới** (NCC, pháp nhân, dự án, phòng, mã chứng từ), công cụ đã dùng, thành công / phải hỏi lại / lỗi, giờ. Không lưu nguyên văn câu hỏi (chỉ nhãn + đối tượng) để nhẹ và đỡ lộ. |
| 13.2 Nhãn chi tiết hơn | Giữ 6 nhãn lớn, thêm **nhãn con theo nghiệp vụ** (vd `tra_cuu.cong_no`, `thao_tac.tao_ycmh`, `du_lieu.bao_cao_mua_hang`) — lấy từ nhóm công cụ đã chọn, không bắt mô hình đoán thêm. |
| 13.3 Tự rút trí nhớ | Vòng nền chạy cùng «tóm tắt buổi» (102): sau mỗi buổi, đọc sổ ý định + tóm tắt buổi → rút **sự thật bền** (vd «hay hỏi công nợ NCC X, pháp nhân DEGO», «thích xem bảng», «gọi YCMH là phiếu đề nghị») → ghi vào lõi **có độ tin cậy + hạn dùng**; thấy lặp lại nhiều lần mới nâng thành chắc chắn. Không ghi bí mật, không ghi điều chỉ nói một lần. |
| 13.4 Người dùng xem / xóa | Màn «Bot đang nhớ gì về tôi» trên ERP v2 + lệnh trên chat: xem, sửa, xóa từng dòng. Bắt buộc có — bot tự nhớ thì người ta phải thấy được. |
| 13.5 Dùng ý định để đỡ việc | Hỏi tắt mà thiếu đối tượng → điền theo thói quen («công nợ tháng này» = của pháp nhân hay hỏi); gợi ý chủ động (sáng thứ 2 hay hỏi báo cáo tuần → đề xuất bản tin, người dùng bật mới gửi). |
| 13.6 Đo | Gắn nhãn tay ~200 câu hỏi thật trên dev → tỷ lệ phân loại đúng; số câu phải hỏi lại trước / sau. |

Ước lượng: 3–4 ngày (1.1–1.3 trước, 1.4–1.6 sau). Cần đại ca chốt: trí nhớ tự rút có cần **người dùng bấm đồng ý**
từng dòng không, hay ghi luôn và cho xóa sau (em đề xuất: ghi luôn, cho xem / xóa, nhắc một lần ở lần đầu).

### Phase 14 — Nén hội thoại (3 mức) — xong dev 09/10, ai-CR-136

Thay «cắt sau 20 lượt» bằng: đầy ~50% thì xóa **kết quả công cụ cũ** (giữ 3 lượt gần nhất) → ~70% thì **tóm tắt các
lượt cũ** bằng một lần gọi mô hình rẻ, lưu vào cột `summary` của cuộc hội thoại → ~90% mới bỏ lượt cũ nhất. Mỗi lần gửi
cho AI = luật + lõi nhớ + **bản tóm tắt** + các lượt gần + câu mới. Áp cho cả web và Telegram / Zalo.
Ước lượng: ~1 ngày.

**Nén theo đơn vị nào:** theo **từng cuộc hội thoại** — mỗi người một cuộc trên web / Telegram / Zalo riêng, và **mỗi
nhóm chat một cuộc** (bot trả lời trong nhóm thì ngữ cảnh là tin của nhóm đó, bản tóm tắt lưu theo nhóm, dùng lại được
bảng tóm tắt nhóm sẵn có). **Không nén theo pháp nhân / phòng ban** — cái chung theo pháp nhân / phòng ban là **trí
nhớ cấp tổ chức** (phase 13: ý định lặp của nhiều người; phase 19: kho tri thức; sổ thuật ngữ đã lọc theo phòng ban),
không phải nén hội thoại. Bản tóm tắt của một cuộc riêng KHÔNG được đọc sang cuộc của người khác.

### Phase 15 — Một lớp duyệt chung cho mọi thao tác ghi

Mọi công cụ ghi (tạo / sửa / gửi duyệt / xóa) đi qua một lớp: bot đưa **bản xem thay đổi** (trước → sau) → người dùng
duyệt → ghi + **nhật ký thay đổi có hoàn tác một chạm**. Gom ba kiểu duyệt hiện có về một. Làm xong mới mở thêm công cụ
ghi mới (hóa đơn, công nợ…).
Ước lượng: 2–3 ngày.

### Phase 16 — Gọn và đo

- **Nạp công cụ theo nhu cầu**: luôn gửi nhóm lõi; nhóm theo nghiệp vụ chỉ nạp khi nhãn ý định (phase 13) chạm tới →
  bớt token, bớt chọn nhầm. Đo trước số khai báo đang gửi mỗi lượt rồi mới làm.
- **Bảng chi phí / chất lượng**: token, tiền, thời gian, số vòng công cụ, tỷ lệ hỏi lại — theo người, theo nhãn ý định,
  theo ngày.

Ước lượng: 2 ngày.

### Phase 17 — Lên prod (stack tách)

Theo runbook S-5 / S-6 ở `13-lo-trinh.md` (bước cuối của phase 11): dọn sổ CR, gom các đợt dev thành một đợt prod, dựng `agent_hub` trên prod,
cổng B, quyền mới (`agent_group`, `agent_ops`, `assistant.read`), sao lưu + ngưỡng quay đầu. **Chỉ làm khi đại ca mở
lại prod.**

### Phase 18 — Nhóm chat + nhắc việc (phần còn treo ở doc 13)

Tin cần để ý trong nhóm (G-2), tìm tin nhóm (G-3), đồng hồ chờ trả lời (G-4), bản tin cuối ngày, nhắc hạn 3 mốc
(T-14), khuôn báo cáo tuần / tháng. Một phần đã làm ở bot IDA (cảnh báo, đồng hồ chờ, ticket) — làm phía ERP thì chép
cách, không viết lại từ đầu.

### Phase 19 — Kho tri thức cấp công ty

Mở rộng RAG từ HDSD sang **quy trình nội bộ, chính sách, tài liệu kỹ thuật** (đã duyệt); nhân viên hỏi đáp nhanh, câu
trả lời trích đúng tài liệu. Kết hợp sổ thuật ngữ (077–079) và trí nhớ cấp tổ chức (ý định lặp của nhiều người ở phase 13
→ gợi ý tài liệu nên viết thêm).

---

## 4. Định hướng về sau

- **Một nền tảng AI cho nhiều công ty / nhiều bot**: dịch vụ AI đã tách (phase 11) là nền. Về sau gom bot IDA về đây,
  tách theo công ty (đã chốt hướng ở bot IDA: phục vụ IDA trước, gom sau). Từ giờ tính năng nào làm ở một bên thì ghi
  rõ «đã có ở bên kia» để lúc gom khỏi viết lại.
- **Bot làm thay nhiều bước** («đính kèm A, B vào hợp đồng X rồi xuất hóa đơn nháp») — chỉ sau phase 15 (duyệt chung).
- **Bot riêng cho từng người** (N-01) và **A2A** giữa các bot (doc 13) — phase 20, 21; giữ ở mức ghi nhận cho tới khi phase 13–16 xong.
- **VPS AI riêng** khi tải tăng (doc 13 §6 — chưa mua).
- **Bộ đánh giá tự động**: bộ câu hỏi mẫu + đáp án đúng chạy mỗi lần đổi mô hình / đổi luật, để biết bot khôn lên hay
  dở đi trước khi lên prod.

---

## 5. Đại ca cần chốt

1. Thứ tự phase 13 → 19 như trên có đúng ý không. (Phase 14 nén hội thoại đã giao Agent 4 song song, 09/10.)
2. Trí nhớ tự rút (13.3): áp **ghi luôn + cho xem / xóa**, báo người dùng một lần ở lần tự ghi đầu tiên (09/10, khi giao
   phase 13 — đại ca muốn đổi sang «bấm đồng ý từng dòng» thì báo).
3. Sổ ý định (13.1): áp **không lưu nguyên văn câu hỏi**, chỉ nhãn + đối tượng, giữ 180 ngày (09/10).
4. Ai làm: em đề xuất giao Agent 4 (đang giữ nhánh `agent-hub-bac-1`), em dựng dev + kiểm như các đợt trước.
