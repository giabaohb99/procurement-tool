# 20 — Lõi hội thoại mới: bot nói chuyện như người

> Bản 0.1 · 14/10/2026 · Trạng thái: **đề xuất, chờ đại ca duyệt**. Người viết: Agent 1.
> Đại ca chốt sáng 14/10: *"a chấp nhận có thể đập đi xây lại cũng được, model tốt hơn cũng được… a chưa cần tối ưu
> token đâu, nhưng a cần nó ổn định và con người hơn"*. Tài liệu này tách riêng khỏi doc 15 (kế hoạch tổng) để làm một
> việc duy nhất: thay lõi hội thoại. Phase 24 (doc 18/19) và các phase còn lại sẽ xây trên lõi này.

## 1. Vấn đề (nói thẳng)

Bot hiện tại trả lời đúng nhưng **cứng**: không hỏi lại khi thiếu, không gợi ý, không xác nhận cách hiểu, lệnh phải gõ
đúng mẫu (*tạo*, *thôi*, *xong việc 5*, *hoàn tác 1*), nút bấm là đường chính. Đại ca ví: *"nó không giống như em (Agent
1), bị robot quá"*. Nguyên nhân nằm ở cách dựng, không phải ở một lỗi lẻ:

| Nguyên nhân | Bằng chứng (đo 13–14/10 trên dev) |
|---|---|
| **Một lần gọi model rồi cắt.** Soạn nháp xong là dừng (`stop_on_draft`), không có vòng hỏi – nghe – chỉnh – xác nhận. | Lượt tạo task: model gọi `draft_work_task` rồi trả thẻ; muốn sửa phải gõ lại cả câu. |
| **Luồng theo luật và mẫu câu.** Mỗi tính năng là một máy trạng thái riêng với regex (`_DONE`, `_PROGRESS`, lệnh «tạo»/«thôi», `LINKED_CHAT_CALLBACKS`). | 8 nút Nhận việc của anh Được rơi im lặng (14/10); «tao task đó igups anh» không khớp mẫu → mở nhầm việc sửa mã (13/10). |
| **Prompt quá lớn cho model quá nhỏ.** Prompt hệ thống 35–97 nghìn ký tự, 9–73 công cụ, chạy trên DeepSeek flash qua trạm hoặc Gemini flash free. | Trước ai-CR-183: 150–200 nghìn token/lượt, 0,35–0,44 USD, 28–32 s. Sau: 24 nghìn token nhưng vẫn ~7–10 s/lần gọi vì trạm chờ 6–7 s mới ra chữ đầu. |
| **Ngữ cảnh ngắn, trạng thái nằm ngoài model.** Lịch sử nén còn ~13 lượt; nháp, kế hoạch, việc đang chờ nằm trong bảng + regex, model không thấy. | Bot trả lời đại ca *"không có dấu vết nhận việc"* trong khi tính năng có — model không được cho biết. |
| **Nhiều tay cùng đắp.** 2–3 agent đẩy 5–8 CR/ngày vào cùng `service.py` (hơn 5.000 dòng). | 3 sự cố trong 24 giờ: thiếu tệp `change_undo.py` (bot sập 15 phút), provider bot thiếu `stop_when`, cổng nút chặn người khác. |

## 2. Đích

Bot phải nói chuyện được như một trợ lý người thật biết việc: **hỏi lại khi thiếu, gợi ý 2–3 phương án, xác nhận cách
hiểu trước khi ghi, nhớ việc đang dở, nhận đúng ý dù gõ sai chính tả hay nói vòng**. Nghiệm thu bằng **bộ hội thoại mẫu**
(mục 7), không bằng cảm tính. Chưa tối ưu tiền ở giai đoạn này; ưu tiên **ổn định** rồi **tự nhiên**.

Sáu tiêu chí nghiệm thu:

1. Câu thiếu thông tin → bot hỏi đúng cái thiếu (tối đa 2 câu hỏi một lượt), không đoán bừa, không ra thẻ rỗng.
2. Người dùng sửa bằng lời (*đổi hạn thứ sáu*, *giao cho Giang*, *bỏ việc 2*) → nháp cập nhật, không phải gõ lại.
3. Đồng ý bằng bất kỳ cách nào (*ok*, *được*, *tạo đi*, *tao task đó giúp anh*) → ghi; không đồng ý (*khoan*, *thôi*, *để anh xem*) → giữ nháp.
4. Hỏi về việc đang dở (*nháp hồi nãy đâu*, *Được nhận chưa*) → trả lời đúng trạng thái thật.
5. Một lượt từ gõ tới trả lời ≤ 8 giây với câu thường, ≤ 20 giây khi phải tra ERP/web; luôn có báo nhận ngay.
6. 30 ngày không có sự cố loại "bot im lặng" hay "bot chết" do lỗi lập trình; mọi lỗi phải thành một câu người đọc hiểu.

## 3. Lõi mới — cách dựng

```
Tin vào ──► Báo nhận ngay ──► [Ngữ cảnh: nhân cách + hồ sơ người dùng + việc đang dở + 30–40 lượt] ──► Model mạnh
                                                                                                        │
            ◄── trả lời / hỏi lại / thẻ (dữ liệu do tool trả) ◄── vòng công cụ (nhiều vòng, model tự quyết) ◄┘
```

1. **Một model mạnh cho hội thoại**: Claude Sonnet 5.5 qua API chính thức của Anthropic (provider `claude` đã có trong
   mã, hỗ trợ công cụ + prompt caching). Opus 5.5 cho lượt lập kế hoạch dài nếu cần. Gemini chỉ còn cho chép lời họp,
   YouTube, đọc ảnh/tệp. DeepSeek trạm rút khỏi đường chat chính.
2. **Vòng tác tử thật**: trong một lượt, model được gọi công cụ nhiều vòng và **tự quyết** hỏi lại hay làm tiếp. Nháp
   là một đối tượng model nhìn thấy (`draft_id` + nội dung) và sửa bằng công cụ `update_draft`, ghi bằng `commit_draft`
   khi hiểu là người dùng đồng ý. Không còn `stop_on_draft`, không còn regex «tạo»/«thôi» làm cổng chính (giữ làm lối tắt).
3. **Ngữ cảnh đủ**: 30–40 lượt gần nhất + bản tóm tắt dài hạn (ai-CR-136 giữ); hồ sơ người dùng và thói quen (phase 13)
   luôn có mặt; **việc đang dở** (nháp, kế hoạch đang hỏi nhận, thẻ chờ ok) được đưa vào ngữ cảnh dưới dạng một khối
   «Đang dở» ngắn. Prompt caching để phần tĩnh không tính tiền lại.
4. **Một nhân cách, một giọng**: một prompt phong cách duy nhất cho mọi kênh (Telegram, Zalo, web): xưng hô, hỏi lại khi
   thiếu, gợi ý, xác nhận trước khi ghi, nói ngắn, không câu mẫu. Thẻ (nháp, kế hoạch, bảng số) chỉ là **dữ liệu do tool
   trả**; lời dẫn quanh thẻ do model viết.
5. **Bộ công cụ lõi ~15**: đọc ERP (việc, phiếu, nhân sự, tồn kho, giá), soạn/sửa/ghi nháp (một bộ chung cho mọi loại
   phiếu), kế hoạch việc, tìm web, hỏi nhận việc, ghi tiến độ, sổ thay đổi/hoàn tác, nhớ/quên. Công cụ chuyên sâu (hải
   quan, biên bản họp, nghiên cứu sâu…) để trong **kho**, model gọi `find_tool` khi cần — hết cảnh 73 công cụ trong một prompt.
6. **Xác nhận tự nhiên với người đưa việc**: mọi thao tác ghi đều qua `commit_draft` sau khi model xác nhận bằng lời.
   Phía **người nhận việc** ở giai đoạn này **chỉ nhận thông báo** (tin mẫu, không tốn model) — đại ca chốt 14/10: chưa
   mở hội thoại nhận / từ chối / đồng lập với người nhận vì **chưa xác định điểm giao thoa trừ token** (người nhận đang
   chat bằng khóa riêng, việc sếp giao xuống thì trừ của ai, xác nhận xong trừ của ai). Phần này cùng luật khóa công ty /
   cá nhân để vào một kế hoạch riêng sau (ý đại ca: chức vụ cao có thể dùng chung khóa với người đó).
7. **Ổn định là tính năng**: một provider cho chat + trần thời gian 20 s + đổi model dự phòng; mọi lỗi → một câu rõ cho
   người dùng kèm mã lượt; bộ hội thoại mẫu chạy tự động trước mỗi lần lên dev; kiểm import toàn gói trước khi đẩy.

## 3b. Chuẩn hành vi «con người» — cái gì cụ thể làm bot khác đi

Đây là phần đại ca hỏi 14/10 chiều: *"cập nhật cái gì để bot con người hơn"*. Mỗi dòng là một hành vi đo được, đưa vào
prompt phong cách + bộ hội thoại mẫu; thiếu dòng nào thì chưa gọi là xong B1.

| # | Hành vi | Hiện tại | Lõi mới làm thế nào |
|---|---|---|---|
| 1 | **Báo nhận ngay** rồi mới nghĩ | Có từ ai-CR-194 | Giữ; tin báo tự xóa khi có câu trả lời |
| 2 | **Hỏi lại đúng cái thiếu**, tối đa 2 câu, kèm **gợi ý từ dữ liệu thật** (*dự án ERP v2 hay Nhập khẩu? giao Được hay Giang?*) | Không hỏi, ra thẻ rỗng hoặc đoán | Model được phép hỏi; công cụ tra nhanh danh sách dự án / người / cột để gợi ý trước khi hỏi |
| 3 | **Biết hôm nay là ngày nào, ai đang nói**: ngày giờ, tên, giới tính, chức vụ, phòng ban từ hồ sơ; gọi đúng *anh Được / chị Mi*, không *anh/chị* chung chung | Thiếu — đo 14/10 cả 3 model ghi hạn «17/10/**2025**» vì không được cho ngày | Khối ngữ cảnh cố định: ngày giờ VN, hồ sơ người chat, cách xưng hô |
| 4 | **Nhớ việc đang dở** và nhắc lại được (*nháp hồi nãy em còn giữ, anh muốn đổi gì?*) | Nháp nằm trong bảng, model không thấy | Khối «Đang dở» trong ngữ cảnh + 30–40 lượt lịch sử |
| 5 | **Sửa bằng lời** (*đổi hạn thứ năm*, *giao Giang thay Được*, *bỏ việc 2*) | Phải gõ lại cả câu | Công cụ `update_draft`; nháp là đối tượng model cầm được |
| 6 | **Hiểu đồng ý / không đồng ý theo mọi cách nói**, kể cả sai chính tả, viết tắt, nói vòng (*ok*, *được đó*, *tao task đó giúp anh*, *khoan*, *để anh xem*) | Regex mẫu câu | Model quyết, công cụ `commit_draft` chỉ gọi khi model hiểu là đồng ý; luôn nhắc lại ngắn cái sắp ghi |
| 7 | **Một giọng**: xưng *em*, gọi theo hồ sơ, câu ngắn, **không emoji**, không câu mẫu lặp («Em nhận rồi…» chỉ ở tin báo nhận), không dấu đầu dòng khi 1–2 ý | Mỗi tính năng một kiểu; model trạm hay thêm emoji (đo 14/10) | Một prompt phong cách; cấm emoji trong prompt; bộ mẫu chấm giọng |
| 8 | **Chủ động vừa phải**: xong một việc thì gợi bước kế (*em báo anh Được luôn nhé?*), sáng nhắc việc dở; không hỏi han thừa | Không có / chỉ bản tin sáng | Mỗi lượt có một câu «bước tiếp» khi hợp lý; luật không hỏi quá 1 câu phụ |
| 9 | **Nói thật khi không biết / lỗi**: *em không tra được số cột vì…*, *gọi AI lỗi mã #N*, không bịa | Có từ ai-CR-162/183 cho vài chỗ | Luật chung: công cụ lỗi → nói nguyên nhân một câu + cách khác |
| 10 | **Tóm tắt khi hội thoại dài**, hỏi *em hiểu vậy đúng không?* trước việc lớn (kế hoạch, xóa) | Chỉ thẻ | Trước `commit` việc lớn: một đoạn «Em hiểu là…» |
| 11 | **Đọc được tin dài, nhiều ý, ảnh chụp màn hình** và trả lời theo từng ý | Có một phần (Gemini đọc ảnh) | Giữ Gemini cho ảnh; model chính nhận bản chữ |
| 12 | **Không «dạy» người dùng gõ lệnh**: không bắt nhớ cú pháp; lệnh chỉ là lối tắt | Hướng dẫn liệt kê lệnh | Bỏ câu nhắc cú pháp khỏi trả lời thường; «hướng dẫn» vẫn có khi hỏi |

## 3c. Một cửa cho ba việc: trò chuyện · lên việc · sửa mã (đại ca hỏi 14/10 chiều)

Hiện nay bot có **ba máy riêng** và người dùng phải rơi đúng máy: trò chuyện / tra cứu (Trợ lý), lên việc (thẻ nháp +
lệnh «tạo»), sửa mã (vé AI-000x → máy sửa mã, dây chuyền gom → kế hoạch → sửa → kiểm → gộp → deploy). Bước đọc ý định từng
làm việc chia máy; nó đoán sai thì cả lượt sai (AI-0007 mở nhầm từ câu «tao task đó igups anh»). Mỗi máy lại có ngữ cảnh
riêng, nhỏ, không nhìn thấy nhau — đúng cái đại ca gọi là *"content nó nhỏ quá"*.

Lõi mới: **một cuộc hội thoại, một ngữ cảnh, model tự chọn công cụ**.

| Việc | Lõi mới | Gì vẫn giữ |
|---|---|---|
| Trò chuyện / tra cứu | Model trả lời thẳng, gọi công cụ đọc ERP / web khi cần | — |
| Lên việc / phiếu | Công cụ `draft_*` → nháp trong «Đang dở» → sửa bằng lời → `commit_draft` khi đồng ý | Luật quyền, sổ thay đổi / hoàn tác |
| **Sửa mã** | Công cụ `code_task.create(mô tả, phạm vi)` — model chỉ gọi khi người dùng **nói rõ muốn sửa phần mềm** hoặc xác nhận gợi ý của bot; trước khi tạo vé, model **nhắc lại cách hiểu** (*em hiểu là sửa màn X để Y, đúng không?*). Vé vẫn đi máy sửa mã như cũ (runner VPS 2, kế hoạch → ok → gộp → deploy). Trạng thái vé nằm trong «Đang dở» nên hỏi *tới đâu rồi* / *bỏ việc này* / *đổi hướng* trả lời được ngay trong cùng cuộc. | Dây chuyền gọn ai-CR-154/155, khóa quyền sửa mã, bài canh ranh giới |
| Chuyển qua lại | Không cần lệnh; cùng một câu có thể vừa hỏi vừa giao việc (*việc này giao Được làm tay, còn chỗ nút bị kẹt thì em sửa mã luôn*) → model tách thành hai hành động, xác nhận từng cái | — |

Về **trợ lý cá nhân** (phase 4 / 9 — sổ nhớ, nhắc việc, tóm tắt buổi, hồi ức, Google Lịch / Drive): **không ảnh hưởng, chỉ
tốt lên** — sổ nhớ cá nhân và thói quen đi thẳng vào ngữ cảnh (§3b.3–4), nhắc / ghi nhớ / lịch thành công cụ model gọi tự
nhiên (*nhắc anh 3h chiều* không cần cú pháp). Mọi lệnh «/…» và câu mẫu **giữ làm lối tắt**, không còn là đường bắt buộc.

«Content nhỏ» còn một nghĩa nữa: **model không được cho đủ dữ liệu** — hôm 14/10 nó không biết ngày hôm nay, không biết
sổ kế hoạch, không thấy vé sửa mã. Lõi mới quy định khối ngữ cảnh tối thiểu mỗi lượt: ngày giờ · hồ sơ người chat · sổ nhớ
cá nhân · «Đang dở» (nháp, kế hoạch, vé sửa mã, thẻ chờ) · 30–40 lượt gần nhất · tóm tắt dài hạn. Giới hạn chỉ còn là
cửa sổ của model (Claude Sonnet: 200 nghìn token), không phải do mình cắt.

## 4. Giữ — bỏ — thay

| Phần | Quyết định |
|---|---|
| Cổng B, DB `agent_hub` tách, runner trên VPS 2, sổ nhớ phase 13, nén hội thoại, sổ thay đổi/hoàn tác, biên bản họp, Gemini cho tệp | **Giữ** |
| Bước đọc ý định (stage 20) | **Bỏ hẳn** (đã tắt từ 13/10) — ý định là việc của model chính; nhãn do người dùng gắn nếu muốn |
| Regex lệnh (`_DONE`, «tạo», «thôi», «hoàn tác n»…), `stop_on_draft`, `LINKED_CHAT_CALLBACKS` | **Thay** bằng công cụ + xác nhận tự nhiên; regex giữ làm lối tắt không bắt buộc |
| 73 công cụ nạp theo nhóm | **Thay** bằng 15 công cụ lõi + kho công cụ có `find_tool` |
| Prompt hệ thống 35–97k ký tự ghép từ nhiều gói | **Viết lại** còn một prompt phong cách + khối «Đang dở» + gói tri thức theo yêu cầu |
| DeepSeek trạm làm chat chính | **Bỏ** khỏi chat; có thể giữ làm dự phòng |
| `service.py` hơn 5.000 dòng | **Tách** thành lõi hội thoại (một tệp nhỏ) + từng gói công cụ; mã cũ giữ nguyên cho tới khi gói mới thay xong |
| Tính năng mới trong 2 tuần | **Đóng băng** — chỉ sửa lỗi; mọi agent dồn vào lõi mới |

## 5. Tài nguyên cần đại ca cấp

| Thứ | Vì sao | Cách cấp |
|---|---|---|
| **Khóa API Anthropic** (console.anthropic.com → API Keys), nạp trước ~100 USD | Model chính cho hội thoại. Tài khoản Claude Code đang dùng cho runner là gói cá nhân cho người dùng tương tác, **không được dùng** làm máy chủ chat nhiều người; qua trạm DeepSeek đổi tên model thành Claude thì không có prompt caching, chậm 6–7 s và dữ liệu công ty đi qua bên thứ ba — không khuyên. | Đại ca dán vào `ANTHROPIC_API_KEY` trong `~/agent-hub/.env.agent` trên VPS 2 (SSH), **không gửi qua chat**. |
| **Gemini bật thanh toán** cho khóa công ty | Hết 429, chép lời họp / đọc tệp ổn định | Google AI Studio → Billing; khóa giữ nguyên |
| **Đóng băng tính năng mới 2 tuần** (từ ngày duyệt) | Để lõi mới ổn trước khi chất thêm | Đại ca thông báo Agent 2 / 4: chỉ sửa lỗi + làm theo doc này |
| **3–5 người dùng thử** (đại ca, anh Được, anh Giang…) | Chấm hội thoại mẫu bằng người thật | Mỗi người 10 phút/ngày trong tuần 2–3 |
| VPS | **Không cần thêm** — máy 2 còn ~4 GB RAM + swap | — |
| Kênh | Telegram trước, Zalo sau (như đã chốt 09/10) | — |

Ước tính chi phí chạy: prompt ~20–30 nghìn token có cache + 1–2 vòng công cụ ≈ **0,03–0,08 USD/lượt**, 4–8 giây. 100
lượt/ngày ≈ 3–8 USD/ngày. Khi ổn định mới làm gọn (phase 16 quay lại).

## 6. Lộ trình (4 bước, ~3 tuần)

| Bước | Làm gì | Nghiệm thu |
|---|---|---|
| **B1 — Lõi** (tuần 1) | Provider Claude + caching; vòng tác tử; khối «Đang dở»; prompt phong cách; 15 công cụ lõi (ưu tiên: hỏi đáp ERP, nháp phiếu chung, việc Dự án, tìm web); bộ 20 hội thoại mẫu chạy tự động; báo nhận + báo lỗi rõ | 20/20 hội thoại mẫu đạt; tiêu chí 1–3, 5 |
| **B2 — Dời tính năng lên lõi** (tuần 2) | Kế hoạch việc (phase 24.1) và hỏi nhận việc theo kiểu hội thoại; sổ thay đổi/hoàn tác; nhắc hạn; thẻ chỉ còn là dữ liệu; gỡ regex cổng chính; kho công cụ + `find_tool` | Tiêu chí 4, 6 bắt đầu đếm; anh Được chạy trọn vòng nhận → xong → bản tin sáng |
| **B3 — Phase 24 phía sếp** (tuần 3) | Trên lõi mới, chỉ phần với NGƯỜI ĐƯA VIỆC: trò chuyện làm rõ trước khi lập, xác nhận kế hoạch, sửa bằng lời, link sơ đồ (cây / Gantt / danh sách), báo cáo kết thúc, học từ phản hồi của sếp. Người nhận: **chỉ thông báo**. Đồng lập với người nhận + vòng tuần hoàn hai chiều + lịch hai bên: **gác**, chờ kế hoạch riêng kèm luật trừ token | Một kế hoạch thật của đại ca đi trọn vòng phía sếp |
| **B4 — Dọn** | Xóa mã cũ không còn gọi, cập nhật doc 15/16, mở lại đóng băng | Bộ bài kiểm xanh, không còn đường cũ |

Mỗi bước lên dev xong mới qua bước sau; prod chỉ lên sau B2 và khi đại ca mở prod.

## 7. Bộ hội thoại mẫu (nghiệm thu)

Mỗi mẫu = câu người dùng + câu trả lời mong đợi (ý, không cần nguyên văn) + thao tác ghi mong đợi. Ví dụ ban đầu:

1. *"tạo cho anh task nghiên cứu luồng agent"* → bot hỏi dự án nào, giao ai, hạn (gợi ý 2–3 lựa chọn từ dữ liệu thật).
2. *"ERP v2, Được, thứ sáu"* → thẻ nháp đủ; *"đổi hạn thứ năm"* → nháp đổi; *"ok"* → ghi + báo anh Được.
3. *"tao task đó igups anh đi nhé"* (sai chính tả) → hiểu là đồng ý.
4. *"Được nhận việc chưa?"* → trả đúng trạng thái từ ERP.
5. *"lập kế hoạch thử bot, hạn 15/10, 2 việc giao Được"* → bot hỏi 1–2 câu làm rõ rồi mới ra kế hoạch; tự chia việc con + tiêu chí, nói rõ phần tự nghĩ.
6. (Gác — chờ kế hoạch riêng) Anh Được: *"việc 2 em làm chiều mai được không, tách thành 2 phần"* → bot cập nhật, hỏi lại đại ca duyệt. Giai đoạn này anh Được chỉ nhận tin thông báo việc.
7. *"hello"* → trả lời ngắn như người, không nạp gì nặng.
8. *"giá vàng hôm nay"* → số + nguồn, hỏi có muốn bản đầy đủ không.
9. Lỗi model → *"Em gọi AI bị lỗi (mã lượt #N, hết hạn mức). Đại ca nhắn lại sau 1 phút giúp em."*
10. Người chưa liên kết → hướng dẫn liên kết, không im lặng.

Bộ đầy đủ 20–30 mẫu do đại ca + anh Được góp trong tuần 1; chạy tự động bằng model chấm (so ý) trước mỗi lần lên dev.

## 8. Rủi ro

- **Chi phí** tăng so với DeepSeek: chấp nhận ở giai đoạn này (đại ca chốt), đo hằng ngày ở `tab_agent_run`, báo khi vượt 10 USD/ngày.
- **Hạn mức API** lúc đầu thấp (tier mới): nạp tiền trước, tăng dần; có dự phòng Gemini trả phí.
- **Model tự quyết nhiều hơn** → nguy cơ ghi nhầm: mọi ghi đều qua `commit_draft` có xác nhận + sổ thay đổi/hoàn tác (phase 15) đã có.
- **Dời tính năng** có thể làm hỏng cái đang chạy: lõi mới chạy song song dưới cờ `AGENT_CORE_V2`, bật theo từng chat thử trước.

## 9. Quyết định của đại ca (cập nhật 14/10 trưa)

1. Model: đại ca chọn **đi qua trạm modelapi.vn**, đã thêm 4 khóa (14/10 14:30, hiện ở sổ khóa cá nhân đại ca, ai-CR-197
   cho phép nhiều gói một trạm). **Số đo 14/10 15:03** (prompt phong cách ngắn, 3 tình huống: thiếu thông tin · đủ thông
   tin gọi công cụ · xã giao):

   | Model qua trạm | Chữ đầu | Hỏi lại khi thiếu | Gọi công cụ | Nhận xét |
   |---|---|---|---|---|
   | claude-sonnet-5-5 (giá 2x) | 4,0 · 6,5 · 11,5 s | Tốt, 3 câu rõ | Đúng | Giọng chuẩn nhất; có emoji khi chưa cấm |
   | kimi-k3 (1,2x) | 8,0 · 6,3 · 7,3 s | Tốt, 2 câu | Đúng | Sát Claude, rẻ hơn; có emoji |
   | deepseek-v4.1-flash (7x?) | 8,4 · 7,6 · 5,0 s | Khá, hơi dài | Đúng (ngày để nguyên chữ) | Ổn, kém tự nhiên hơn |
   | gemini-3.1-flash-lite (0,9x) | — | HTTP 500 «upstream error» cả 3 lần | — | Gói trạm chưa chạy, cần hỏi trạm |

   Cả ba model đều ghi hạn «17/10/**2025**» vì chưa được cho ngày hôm nay → lõi mới bắt buộc có khối ngày giờ (§3b.3).
   **Chốt đề nghị:** lõi = **Claude Sonnet 5.5 qua trạm**, dự phòng **Kimi K3**; DeepSeek giữ cho việc rẻ; Gemini trạm bỏ
   nếu trạm không sửa 500. **Nói thật về tốc độ:** qua trạm chữ đầu 4–11 s dù model nào — mục tiêu «gần như lập tức» (≤ 3 s)
   chỉ đạt được với API chính thức; với trạm, mục tiêu thực tế là ≤ 8 s một lượt + báo nhận ngay.
2. **Gác**: luật khóa công ty / cá nhân và hội thoại với người nhận việc (điểm giao thoa trừ token) — kế hoạch riêng sau.
3. Còn chờ đại ca: đóng băng tính năng mới 2 tuần; danh sách 3–5 người thử; bật thanh toán Gemini chính thức.

## 10. Bàn giao cho Agent 4 (15/10/2026, đại ca chốt: «đưa việc này cho Agent 4, Agent 1 nhận việc đồng bộ lên dev»)

Từ 15/10: **Agent 4 làm mã lõi hội thoại** (doc này), **Agent 1 chỉ gộp + dựng dev + đo**. Agent 4 đẩy `agent-hub-bac-1`
như mọi CR (fetch erp-v2 ngay trước khi đẩy), báo Agent 1 dựng.

**Hiện trạng trên dev (erp-v2 3a6742b9):** `backend/app/modules/agent_hub/core_v2.py` bật cho chat đại ca
(`AGENT_CORE_V2_ENABLED=true`, `AGENT_CORE_V2_CHATS` = chat đại ca trong `~/agent-hub/.env.agent` VPS 2). Đã có: vòng tác
tử; khối ngữ cảnh (nhân cách + STYLE_RULES + CORE_RULES + lịch 15 ngày có thứ + người đang nhắn + DRAFT_FACTS + NEWS_RULES
+ ĐANG DỞ + sổ nhớ cắt 1,2k + thói quen); lịch sử 40 lượt / 24 h / 12k ký tự, bỏ tin bot nói tới thẻ; phân luồng model
bằng luật (`lane_of`, `AGENT_CORE_V2_ROUTES`: xã giao / tra nhanh → DeepSeek, thường + việc nặng → Claude); công cụ lõi
`update_draft` / `commit_draft` / `drop_draft` / `search_web` / `news_today` / `my_saved_drafts`; nháp trình bày ngay
trong chat (không thẻ riêng, `_offer_draft(silent=True)`); chặn «thẻ ma» và «em đã làm» khi không gọi công cụ
(`PHANTOM_CARD`, `CLAIMED_DONE`); cảnh báo khóa hết tiền (`key_alerts.py`, ai-CR-200). Bài kiểm:
`test_agent_hub_core_v2.py` (23 bài), `test_agent_hub_canh_bao_khoa_cr200.py`.

**Bài học đo được (đừng lặp lại):**
- Kimi K3 qua trạm **không gọi công cụ** trong ngữ cảnh thật (nói «đã soạn nháp» mà không soạn) → chỉ dùng cho câu không
  cần công cụ. Claude gọi đúng.
- Claude qua trạm modelapi.vn: trạm chèn **~14k token ẩn mỗi lần gọi**, bỏ qua `max_tokens`, không có prompt caching,
  không nhận `temperature` (Claude đời 5). Một lượt soạn nháp = 2 lần gọi model → ~88k token báo về (2 × (14k trạm +
  ~30k của mình)). Ví 3 khóa trạm dùng chung — ví âm thì cả 3 hỏng cùng lúc.
- Tiếng Việt trên Claude ~1 token / ký tự. Phần lớn nhất của mình: mô tả công cụ (~12k ký tự với 15 công cụ;
  `draft_work_plan` 3,5k — nay chỉ nạp khi câu nói «kế hoạch»), lời dặn hệ thống ~10k.
- Mô hình chép câu cũ trong lịch sử thay vì gọi công cụ — mọi câu «giả» ghi vào lịch sử (ví dụ «(đã soạn bản nháp, xem
  thẻ bên dưới)» của đường cũ, `service.py` ~4284) phải lọc.

**Việc giao Agent 4 (theo thứ tự):**
1. **B2 — nối nốt tính năng cũ vào lõi:** đăng ký bản tin sáng (`manage_briefs`), «nghiên cứu sâu: …» (`deep_research`,
   có thẻ chờ ok), biên bản họp, nhắc việc, hoàn tác («bot vừa làm gì», «hoàn tác n»), sửa mã (`code_task.create` nhắc lại
   cách hiểu trước khi tạo vé; trạng thái vé đã có trong ĐANG DỞ), kế hoạch việc phía sếp (24.1 — phía người nhận GÁC).
   Mỗi cái: một bài kiểm hội thoại trong `test_agent_hub_core_v2.py`.
2. **Gọn token tiếp:** rút mô tả 10 công cụ lớn nhất; cân nhắc gộp hai lần gọi (tool + trả lời) khi công cụ trả nháp
   (model tự trình bày từ `tom_tat_se_luu` ngay lượt hai — đang tốn gấp đôi); đo trước / sau ở `tab_agent_run`.
3. **Bộ hội thoại mẫu tự chạy** (§7) — 20 mẫu, chấm bằng model, chạy trước mỗi lần đẩy.
4. Đổi dòng cuối nháp thành câu tự nhiên (đã làm trong core v2; đường cũ còn «Trả lời: tạo / thôi»).

**Tiến độ Agent 4:**
- 15/10 — việc 1 (B2) phần nối: **ai-CR-201** — `core_v2.shortcut` chạy lại chuỗi lối tắt chữ của đường cũ trước vòng tác tử
  (bỏ `_draft_by_text` + đọc ý định); công cụ lõi mới `bot_changes`, `undo_change`, `set_reminder`, `create_code_task`.

**Agent 1 làm:** gộp `agent-hub-bac-1` → erp-v2, dựng ERP api (nếu đổi `assistant/*`) rồi `~/agent-hub` trên VPS 2
(`vps2_ssh.py`, kiểm việc dở + flock), đo lượt thật ở `tab_agent_run` (`artifact.core = v2`, `artifact.lane`), báo đại ca.
