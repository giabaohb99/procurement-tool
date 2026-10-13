# 18 — Phase 24: Bot điều phối việc theo kế hoạch (trợ lý quản lý công việc cho sếp)

> Bản 1.0 · 13/10/2026 · theo ý tưởng của cấp trên do đại ca chuyển lại. Viết theo khuôn doc 11 và doc 15. Trạng thái:
> **thiết kế, chưa có mã**. Bộ tiêu chí ở §4 là **bản nháp để bot chạy được ngay**; sếp viết bản chính thức thì thay
> vào, không sửa mã.
>
> Đã chốt với đại ca ngày 13/10/2026: (1) kênh ưu tiên **Zalo tài khoản bot chung của công ty** (hướng B, doc 12 §7),
> Telegram là kênh phụ; (2) email công việc: bot được cấp quyền **đọc, không xóa** khi cấp trên duyệt, cấp qua OAuth
> chứ không cầm mật khẩu; (3) danh sách người nhận việc có Zalo hoặc số điện thoại có Zalo, **nhắn không được thì ghi
> lên việc**, không đoán kênh khác; (4) viết bộ tiêu chí nháp trước, sếp cập nhật sau.

## 1. Một câu

Sếp đưa một danh sách việc. Bot lập kế hoạch theo giai đoạn, việc cha và việc con, ai làm, tiêu chí đánh giá, mốc thời
gian. Bot nhắn từng người hỏi có nhận được không, ghi phản hồi, nhắc đúng mốc, hỏi tiến độ, xếp lại kế hoạch khi có
người báo giờ khác, báo sếp khi xong kèm so sánh kế hoạch với thực tế, xuất Word hoặc Excel, và ghi bài học cho lần sau.

## 2. Đầu vào → đầu ra

```
Danh sách việc ──► kế hoạch ──► sếp duyệt ──► hỏi nhận việc ──► theo dõi mốc ──► báo cáo kết thúc ──► bài học
 (chat / tệp)    (Dự án ERP)   (thẻ duyệt)   (Zalo / Telegram)  (nhắc, hỏi %)   (Word / Excel)       (sổ ghi nhớ)
                                                 │                    │
                                                 └── người báo giờ khác ──► bot đề xuất xếp lại ──► sếp duyệt
```

## 3. Cái đã có, dùng lại

| Có sẵn | Ở đâu | Dùng cho |
|---|---|---|
| Phân hệ Dự án: nhóm, danh sách, việc cha/con, trạng thái, hạn, người được giao, kanban | `modules/work/` (ai-CR-181 cột kanban khi tạo qua bot) | Chứa kế hoạch; mọi thứ bot làm đều ghi vào đây, màn ERP xem được |
| Soạn nháp việc ERP + thẻ duyệt | `draft_create.py` (`work_task`), ai-CR-080 | Kế hoạch do bot lập chỉ thành việc thật khi sếp bấm duyệt |
| Nhắc hạn việc Dự án ba mốc, một tin 08:00 | `work_due.py`, ai-CR-175 | Nền cho bước nhắc; thêm mốc *hỏi tiến độ* và *hỏi nhận việc* |
| Zalo tài khoản công ty: chat riêng, nút bấm, gửi tệp | `zalo_account.py` (`send`, `send_document`), ai-CR-122 | Kênh chính. Đang **chờ quét QR** |
| Telegram: chat riêng, nút bấm | `channels.py` | Kênh phụ, dùng ngay khi Zalo chưa quét QR |
| Hiểu ý định, sổ ghi nhớ cá nhân, nén hội thoại | ai-CR-137/138/136 | Hiểu câu trả lời tự do của người nhận việc; ghi bài học |
| Google từng người (OAuth) | `google_link.py`, ai-CR-064 | Thêm quyền đọc Gmail (§7) |
| Xuất Word mẫu DEGO, Excel | lệnh xuất Word ai-CR-044; skill dego-docx | Báo cáo kết thúc |
| Đọc nhóm chat, biên bản họp | ai-CR-105, phase 10 | Nguồn danh sách việc (rút từ họp) |

## 4. Bộ tiêu chí nháp (dữ liệu, không phải mã — sếp sửa trực tiếp)

Lưu ở bảng cấu hình `tab_agent_plan_policy` (một dòng JSON, có phiên bản, có người sửa và ngày sửa). Bản nháp:

| Nhóm | Quy tắc nháp |
|---|---|
| Ưu tiên | 3 mức: *Gấp* (làm trong ngày), *Ưu tiên* (trong 3 ngày), *Thường* (theo kế hoạch). Bot gán mặc định *Thường*, sếp đổi. |
| Chia việc | Mỗi việc cha ≤ 7 việc con; việc con ≤ 2 ngày công; việc nào > 2 ngày thì chia tiếp. |
| Người làm | Chọn theo phòng ban và chức vụ trên hồ sơ nhân sự; ưu tiên người đang có ít việc mở nhất trong Dự án. Không có ai phù hợp thì để trống và hỏi sếp. |
| Mốc thời gian | Việc con có *ngày bắt đầu* và *hạn*; việc cha lấy hạn muộn nhất của con; giai đoạn lấy hạn muộn nhất của việc cha. Không xếp việc vào Chủ nhật. |
| Tiêu chí đánh giá | Mỗi việc con có 1–3 tiêu chí đo được (ví dụ: *đã có tệp đính kèm*, *được người X xác nhận*, *số lượng ≥ n*). Thiếu thì bot sinh tiêu chí *hoàn thành đúng hạn và được người giao xác nhận*. |
| Hỏi nhận việc | Gửi ngay sau khi sếp duyệt kế hoạch. Người nhận trả lời trong 4 giờ làm việc; quá thì nhắc một lần; quá 1 ngày làm việc thì báo sếp. |
| Phản hồi | Ba lựa chọn: **Nhận** · **Nhận nhưng giờ khác** (ghi giờ) · **Từ chối** (bắt buộc lý do). Trả lời tự do thì bot hiểu rồi hỏi lại một câu để chốt. |
| Hỏi tiến độ | Đúng ngày hạn 15:00 và ngày sau hạn 08:00. Hỏi: xong chưa; chưa thì bao nhiêu % và tự chấm 1–10; chưa làm thì lý do. |
| Dời lịch | Việc *Thường* được dời ≤ 3 ngày không cần hỏi sếp nếu không đẩy hạn việc cha; việc *Ưu tiên* dời ≤ 1 ngày; việc *Gấp* không tự dời. Ngoài ngưỡng thì bot đề xuất bản xếp lại, sếp duyệt rồi mới gửi lại cho mọi người. |
| Nhắn không được | Thử 2 lần cách nhau 2 giờ; vẫn không được thì gắn nhãn *Nhắn không được* lên việc, báo sếp trong bản tin ngày. |
| Báo sếp | Một bản tin mỗi sáng 08:30 gom mọi thay đổi; việc *Gấp* bị từ chối hoặc trễ thì báo ngay. |

## 5. Đường đi chi tiết

1. **Nhận danh sách việc.** Sếp gửi cho bot bằng tin nhắn, tệp (Word, Excel, ảnh chụp) hoặc chọn một biên bản họp đã
   có. Bot hỏi tối đa 1 câu nếu thiếu thông tin bắt buộc (mục tiêu, hạn chót tổng).
2. **Lập kế hoạch.** Bot sinh cây giai đoạn → việc cha → việc con theo §4, gán người, tiêu chí, mốc. Hiện cho sếp dưới
   dạng thẻ duyệt tóm tắt, kèm tệp Excel bản đầy đủ. Sếp sửa bằng câu nhắn hoặc bấm *Duyệt*. Duyệt xong bot ghi vào Dự
   án ERP bằng đúng luồng tạo việc qua bot hiện có (`draft_create.py`, mở rộng thành một thẻ duyệt tạo cả cây):

   | Tầng trong kế hoạch | Tầng trong Dự án | Sếp thấy ở đâu |
   |---|---|---|
   | Kế hoạch | Danh sách (`tab_work_list`) trong nhóm của sếp | Màn Dự án, một bảng riêng |
   | Giai đoạn | Mục / cột kanban (`tab_work_section`) | Cột trên kanban, có thể kéo thẻ |
   | Việc cha | Việc (`tab_work_task`, `parent_id` rỗng) | Thẻ trên kanban, Gantt |
   | Việc con | Việc con (`parent_id` = việc cha) | Trong bảng chi tiết của việc cha |

   Phân hệ Dự án **chỉ cho hai tầng việc** (C-05: việc con không có con). Khi sếp cần chia sâu hơn, bot làm linh động:
   phần cần chia tiếp được **nâng lên thành việc cha mới trong cùng giai đoạn** (tên có tiền tố việc gốc, nối bằng liên
   kết *thuộc về* trong `tab_work_link`), rồi chia con bên dưới. Kế hoạch quá lớn thì mỗi giai đoạn thành một danh sách
   riêng. Bot nói rõ cho sếp khi nâng tầng, không tự im lặng đổi cấu trúc.
3. **Hỏi nhận việc.** Với từng người: tra Zalo theo số điện thoại trên hồ sơ nhân sự; có liên kết Telegram thì gửi song
   song. Tin mẫu do sếp duyệt một lần, bot điền tên việc, mức ưu tiên, mốc, tiêu chí. Ba nút trả lời. Bot ghi phản hồi
   vào việc (trường mới, §6) và báo sếp theo §4.
4. **Theo dõi.** Mở rộng `work_due.py`: thêm mốc *hỏi tiến độ*; người làm trả lời xong / % / điểm / lý do; bot cập nhật
   việc và báo sếp. Người làm cũng chủ động nhắn bot bất cứ lúc nào (*việc X xong rồi*, *việc X cần thêm 2 ngày*).
5. **Xếp lại.** Khi có người báo giờ khác hoặc từ chối: trong ngưỡng §4 thì bot tự dời, ngoài ngưỡng thì bot lập bản
   xếp lại (đổi người hoặc đổi mốc, chỉ rõ việc nào bị đẩy) và đưa thẻ duyệt cho sếp. Duyệt xong mới nhắn lại cho
   những người bị ảnh hưởng.
6. **Kết thúc.** Khi mọi việc con xong hoặc sếp chốt đóng: bot lập báo cáo so sánh kế hoạch với thực tế theo từng việc
   (hạn, ngày xong thật, điểm tự chấm, tiêu chí đạt hay không, số lần dời, lý do), chỉ ra việc nào kẹt và của ai. Xuất
   Word mẫu DEGO hoặc Excel theo yêu cầu, đẩy lên Drive của sếp.
7. **Bài học.** Bot ghi vào sổ ghi nhớ của sếp: việc loại nào hay trễ, ai hay quá tải, ước lượng nào sai. Lần lập kế
   hoạch sau, bot đọc bài học này trước và nói rõ đã áp dụng gì.

## 6. Dữ liệu cần thêm

| Bảng | Thêm gì | Vì sao |
|---|---|---|
| `tab_work_task` | `priority` (SMALLINT, 3 mức), `criteria` (JSON, danh sách tiêu chí), `planned_hours`, `progress_pct`, `self_score` (1–10), `accept_status` (SMALLINT: chưa hỏi · đã nhận · nhận giờ khác · từ chối · nhắn không được), `accept_note`, `reschedule_count` | Kế hoạch và phản hồi phải nằm trên việc để màn ERP xem được, không chỉ trong chat |
| `tab_agent_plan` (mới) | id, sếp, tiêu đề, trạng thái (nháp · đã duyệt · đang chạy · xong · đóng), list_id trong Dự án, phiên bản kế hoạch (JSON), phiên bản tiêu chí dùng, id tệp báo cáo | Một kế hoạch = một bản ghi; giữ lịch sử các lần xếp lại |
| `tab_agent_plan_policy` (mới) | JSON §4, phiên bản, người sửa | Sếp sửa tiêu chí mà không sửa mã |
| `tab_agent_outreach` (mới) | plan_id, task_id, employee_id, kênh, chat_id, tin đã gửi, trạng thái, phản hồi thô, phản hồi đã hiểu, thời điểm | Dấu vết từng lần bot nhắn ai, để sếp tra và để tránh nhắn trùng |

Trạng thái mới theo luật R2: SMALLINT + IntEnum, khai ở `modules/work/model.py` cạnh `WorkTaskStatus`.

## 7. Quyền và an toàn

- **Email công việc.** Cấp qua OAuth Google Workspace của công ty với đúng phạm vi `gmail.readonly` (đọc, không gửi,
  không xóa). Mỗi người tự nối ở Trang cá nhân như đã nối Drive và Lịch (ai-CR-064); cấp trên duyệt danh sách người
  phải nối. Bot không bao giờ nhận mật khẩu Google của ai. Dùng để: đọc thư liên quan việc đang theo dõi (tìm theo mã
  việc hoặc tiêu đề), tóm tắt cho người đó hoặc sếp. **Không** đọc thư không liên quan kế hoạch; mỗi lượt đọc ghi sổ.
- **Zalo.** Dùng tài khoản bot chung của công ty (hướng B). Bot chỉ nhắn riêng, không đăng nhóm. Người chưa có Zalo
  trong danh bạ tài khoản bot thì phải kết bạn trước; chưa kết bạn tính là *nhắn không được*.
- **Thao tác ghi** (tạo việc, dời hạn ngoài ngưỡng, đổi người, đóng kế hoạch) đi qua thẻ duyệt của sếp, cùng lớp duyệt
  chung ở phase 15.
- **Ai là sếp.** Người tạo kế hoạch là chủ kế hoạch; chỉ chủ kế hoạch và người được chủ thêm vào mới thấy phản hồi,
  điểm tự chấm và lý do của người khác. Người làm chỉ thấy việc của mình.
- **Câu chữ.** Mọi tin gửi người làm đều nhân danh chủ kế hoạch, theo mẫu chủ đã duyệt; bot không tự thêm lời nhắc kiểu
  giám sát.

## 8. Lộ trình (sửa 13/10 theo đại ca: đợt 1 chỉ ghi nhận việc, chưa nối phân hệ)

| Đợt | Nội dung | Điều kiện |
|---|---|---|
| 24.1 (song song 15.2) | **Chỉ việc, chưa nối phân hệ.** Sếp đưa danh sách việc → bot lập kế hoạch và ghi thành việc cha/con trong Dự án (sếp sửa trực tiếp trên màn Dự án hoặc nhắn bot sửa) → hỏi từng người nhận việc → sếp duyệt và khóa → bot báo bắt đầu. Mỗi việc **xác nhận xong ngay trên bot** bằng một câu hoặc một nút; bot ghi giờ bắt đầu, giờ xong, phần trăm, điểm tự chấm, lý do. Bản tin sáng: kế hoạch và lịch trình hôm nay. Kênh: Telegram. | Không |
| 24.2 | Nhắc mốc và hỏi tiến độ tự động; nhãn Nhắn không được; bản tin sáng cho từng người có việc. | 24.1 |
| 24.3 | Kênh Zalo cho 24.1–24.2; tìm Zalo theo số điện thoại hồ sơ. | **Quét QR tài khoản Zalo công ty** |
| 24.4 | Báo cáo kết thúc: kế hoạch so với thực tế, Word / Excel, đẩy Drive; bài học vào sổ ghi nhớ. | 24.1 |
| 24.5 | Xếp lại kế hoạch: tự động trong ngưỡng, đề xuất ngoài ngưỡng. | 24.2 chạy ổn 2 tuần |
| 24.6 | **Nối phân hệ ERP khi việc có công cụ tương ứng**: Đặt xe, Duyệt dấu, đề nghị thanh toán tạm ứng, nghỉ phép, lịch Google. Việc có công cụ thì bot soạn nháp và đưa duyệt; việc không có công cụ thì vẫn chỉ ghi nhận xong như 24.1. | 24.1 ổn |
| 24.7 | Đọc email công việc (chỉ đọc) gắn với việc đang theo dõi. | Cấp trên duyệt danh sách người nối |

Đợt 24.1 không phụ thuộc Zalo hay bất kỳ phân hệ nào ngoài Dự án, nên sếp dùng được sớm nhất.

## 9. Chỗ dễ hỏng, nói trước

- Bot lập kế hoạch hay dở là do tiêu chí. §4 chỉ là nháp; chạy thử 1–2 kế hoạch thật rồi sửa tiêu chí trước khi làm 24.5.
- Người nhận trả lời tự do (*để em xem lại*, *chắc được*) không rơi vào ba nút; bot phải hỏi lại đúng một câu để chốt,
  không tự suy thành *Nhận*.
- Hỏi tiến độ quá dày thì người ta tắt bot. Giữ đúng hai mốc ở §4, mọi mốc thêm do sếp bật.
- Số điện thoại trên hồ sơ nhân sự hiện có 25 hồ sơ chưa có chức vụ và 257 hồ sơ chưa gắn pháp nhân (rà 07/10); chọn
  người theo phòng ban vẫn chạy, nhưng chọn theo chức vụ sẽ thiếu. Nhân sự nên bổ sung hồ sơ song song với 24.1.

## 10. Đã chốt 13/10/2026 (đại ca trả lời)

1. **Chủ kế hoạch:** hiện là sếp; về sau là người giữ khóa quyền mới `agent_plan` (thêm vào `ENTITIES`, khai
   `SCOPE_FIELDS`, luật một vai trò = một chức năng). Ai không có khóa thì bot không nhận lệnh lập kế hoạch.
2. **Bản tin sáng:** dùng chung cơ chế bản tin Telegram hiện có (`work_due.py`, 08:00): nội dung là kế hoạch và lịch
   trình của ngày hôm nay, gửi cho chủ kế hoạch và cho từng người có việc trong ngày.
3. **Không dùng mẫu câu cố định.** Bot hỏi và đáp tự nhiên như bot Telegram hiện tại; nút bấm chỉ là lối tắt. Bước
   *hỏi lại một câu để chốt* ở §9 vẫn giữ.
4. **Vòng lặp:** lập kế hoạch → hỏi nhận việc → sếp duyệt (khóa, không chỉnh) → bot báo *bắt đầu* và xác nhận phần việc
   với từng bên → theo dõi → báo cáo → lặp lại.
5. **Thời điểm làm:** đại ca xác nhận sau.
6. **Đợt 1 không nối phân hệ.** Mọi quy trình chỉ cần xác nhận xong trên bot và ghi giờ; việc nào có công cụ trên ERP
   thì nối ở đợt 24.6, không có thì chỉ ghi nhận. Sếp sửa danh sách việc chi tiết trực tiếp trên màn Dự án hoặc qua bot.

**Ví dụ kiểm thử đầu tiên** (doc 19 §9): *ngày mai Bảo đi tiếp khách Trung Quốc với sếp* → Bảo bận cả ngày (lịch Google
+ việc) · kế toán tạm ứng (việc + nháp đề nghị thanh toán, xác nhận trên web) · xe đưa đón (tra xe, tài xế trống theo
`tab_vehicle_booking`, nháp phiếu Đặt xe, sếp duyệt → luồng duyệt cấu hình) · xác nhận với từng người. Thiếu: mẫu nháp
Đặt xe trong `draft_create.py` (thêm ở đợt 24.6; đợt 24.1 cả 4 việc chỉ ghi nhận xong trên bot).

## 11. Chèn vào kế hoạch AI hiện tại thì đổi gì (rà 13/10/2026)

**Một nguyên tắc nền phải nới.** Từ 06/10 bot là *trợ lý cá nhân*: chỉ nói chuyện với người đang chat, chạy bằng khóa AI
của người đó, và từ 10/10 *cá nhân không nhận tin hệ thống* (ai-CR-167). Phase 24 là lần đầu bot **nhắn người khác nhân
danh một người** (chủ kế hoạch). Nới như sau, không bỏ nguyên tắc:
- Tin hỏi nhận việc / hỏi tiến độ là **tin nhân danh chủ kế hoạch**, không phải tin hệ thống: ghi rõ *theo kế hoạch X của
  anh/chị Y* ở đầu tin; người nhận tắt được theo từng kế hoạch, không tắt được toàn bộ khi còn việc mở.
- Chi phí model của mọi lượt hỏi đáp trong một kế hoạch tính vào **khóa AI của chủ kế hoạch**, kể cả câu trả lời của
  người làm. Người làm không cần khóa riêng, không cần đăng nhập ERP qua bot; chỉ cần có Telegram liên kết hoặc Zalo.
- Thêm vào doc 09 (quy định hỏi và làm) một luật: bot chỉ nhắn người thứ ba khi kế hoạch **đã duyệt**, và chỉ về phần
  việc của người đó.

**Kiến trúc 4 nút (doc 13 §3) giữ nguyên, không thêm nút.** Phase 24 nằm ở **A** (hội thoại, lập kế hoạch, nhắn người
làm, bản tin) và gọi **B** để ghi / đọc Dự án qua cổng ERP có lọc phạm vi. Phần mới duy nhất về hạ tầng là một **bộ lập
lịch gửi tin tới người khác** trong A (mở rộng `work_due.py` từ *gửi cho chính mình* sang *gửi cho danh sách người của
kế hoạch*), có sổ `tab_agent_outreach` để tránh gửi trùng và để truy vết. Khi tách bot riêng từng người (phase 20/21),
bộ lập lịch này thành một **bot điều phối** riêng, nói chuyện với bot cá nhân của từng người qua A2A; thiết kế hiện tại
không cản đường đó vì mọi tin đi qua sổ outreach chứ không gọi thẳng kênh.

**Mượn 3 phase đang có, đổi thứ tự một chút:**

| Phase có sẵn | Phase 24 dùng gì | Hệ quả |
|---|---|---|
| 15 — lớp duyệt chung + sổ thay đổi, hoàn tác 24 giờ (15.1 xong ai-CR-182; 15.2/15.3 đang làm) | Tạo cả cây kế hoạch và mỗi lần xếp lại là **một bản ghi thay đổi** có hoàn tác | Đợt 24.1 làm **song song** với 15.2 (đại ca chốt 13/10): dùng thẻ duyệt `draft_create` đang có, ghi thay đổi qua `tab_assistant_change` của 15.1 (đã có); khi 15.2 lên dev thì nối lệnh *hoàn tác* vào, không viết cơ chế duyệt riêng |
| 18 — nhóm chat + nhắc việc (G-4 đồng hồ chờ trả lời, bản tin cuối ngày) | 24.2 chính là G-4 áp cho việc trong kế hoạch | Gộp 24.2 với phần nhắc việc của phase 18, không làm hai lần |
| 13 — hiểu ý định + tự nhớ (xong 09/10) | Hiểu câu trả lời tự do của người làm; bài học ghi vào sổ ghi nhớ của chủ kế hoạch | Thêm 4 nhãn ý định: *nhận việc*, *báo tiến độ*, *xin dời*, *từ chối* |

**Đụng tới số đo của phase 16.** Mỗi người làm trả lời là một lượt model tính cho chủ kế hoạch; kế hoạch 16 việc con
với 3 người như ví dụ doc 19 ≈ 40–60 lượt trong hai ngày. Bảng chi phí phase 16 phải thêm chiều *theo kế hoạch* để sếp
thấy một kế hoạch tốn bao nhiêu.

**Thứ tự sau khi chèn (đại ca chốt 13/10: làm song song):** 24.1 chạy **song song** 15.2 → 24.2 (gộp G-4 của 18) → 16 (đo
thêm theo kế hoạch) → 24.4 → 17 (lên prod, mang theo 24.1–24.2) → 24.3 khi có QR Zalo → 24.5 → 24.6 → 24.7. Phase 19
(kho tri thức) và 20/21 (bot riêng, A2A) không đổi. Điểm ráp giữa 24.1 và 15.2: mọi lần bot ghi vào Dự án đều đi qua
`tab_assistant_change` (có sẵn từ 15.1), nên khi 15.2 xong, lệnh *hoàn tác* tự áp cho kế hoạch mà không sửa 24.1.

**Quyền mới:** `agent_plan` (ENTITIES + SCOPE_FIELDS theo luật B-07, một vai trò = một chức năng). Chủ kế hoạch cần
`agent_plan.create`; người xem báo cáo của kế hoạch người khác cần `agent_plan.read` phạm vi `dept` hoặc `all`.

## 12. Tiến độ

| Đợt | Trạng thái | Ghi chú |
|---|---|---|
| 24.1 | **Mã xong 13/10/2026 (bao-CR-616), chưa commit / deploy** | Tool `draft_work_plan` → thẻ nháp → «tạo» dựng bảng Dự án (cột = giai đoạn, việc cha / con, trường tùy biến, mời thành viên) → hỏi nhận việc từng người (3 nút) → ghi câu trả lời, «xong việc N 8 điểm», «việc N 60% 7 điểm» → báo chủ kế hoạch. Bản tin 08:00 thêm «Đang làm hôm nay». Luật ở khóa `agent_plan_policy`. `work_plan.py` hai lớp: lớp ERP (`build` · `overview` · `reply`) mở qua cổng B `GET /plan/overview` + `POST /plan/reply`, lớp bot chỉ gọi `erp.plan_*` và bảng của bot — vì dịch vụ AI trên dev chạy tách DB. Khác thiết kế §6: KHÔNG thêm cột / bảng mới — mọi ô của kế hoạch là trường tùy biến của bảng; quyền tạm dùng `work_task.create`, khóa `agent_plan` để đợt sau. |
| 24.2 … 24.7 | Chưa | |
