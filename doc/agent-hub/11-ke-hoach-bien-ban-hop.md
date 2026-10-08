# 11 — Kế hoạch phase 10: biên bản họp từ ghi âm / video

> Bản 1.0 — 07/10/2026. Viết lại thiết kế cũ ở `meeting-recap/doc/` (28–29/08, app Python riêng chạy trên máy CEO,
> chưa có mã) theo nền Agent Hub hiện có. Kho `ida-zalo-assistant` **không có** phần này: rà cả ba nhánh `dev`,
> `dev1`, `main` (cùng commit `b598e06`) chỉ thấy đọc pdf / ảnh / docx / xlsx, âm thanh và video trả «chưa hỗ trợ».

## 1. Đầu vào → đầu ra

```
Tệp họp ──► nhận tệp ──► tách tiếng ──► chép lời ──► biên bản theo mẫu ──► gửi + lưu ──► việc + lịch (duyệt)
 mp3/m4a     Telegram     ffmpeg        Gemini         4 mẫu (dữ liệu)     Telegram       Công việc ERP
 mp4         link Drive   (mp4 → âm)    File API                           Word + Drive   thẻ cá nhân
                                                                           kho ghi chú    Google Calendar
```

## 2. Cái đã có, dùng lại

| Có sẵn | Ở đâu | Dùng cho |
|---|---|---|
| Google cá nhân của từng người (OAuth, có `drive.readonly` + `drive.file` + `calendar.events`) | `google_link.py`, ai-CR-064 | Tải tệp mp4 / ghi âm dài từ Drive của chính họ; đẩy Word lên Drive; tạo lịch |
| Chép lời tin thoại ngắn bằng Gemini | `manager.transcribe`, ai-CR-061 | Mẫu cho đường chép lời (tệp dài đổi sang File API) |
| Khóa AI từng người, tự đổi khóa khi hỏng | `ai_keys.py`, ai-CR-098 | Chi phí tính vào khóa của người gửi tệp |
| Soạn nháp việc ERP + thẻ xác nhận «tạo» | `draft_create.py` (`work_task`), ai-CR-080 | Việc rút ra từ biên bản |
| Thẻ cá nhân | `personal_items.py`, ai-CR-103 | Việc của riêng người gửi |
| Tạo / dời lịch Google | `google_tool.py`, ai-CR-064/084 | Cuộc hẹn tiếp theo nhắc trong họp |
| Kho ghi chú có vector | `personal_memory.py`, ai-CR-095 | Lưu biên bản để hỏi lại sau («họp tuần trước chốt gì») |
| Xuất Word | lệnh «xuất Word», ai-CR-044 | Biên bản Word |

## 3. Đường đi chi tiết

1. **Nhận tệp.** Hai cửa:
   - Gửi thẳng tệp âm thanh vào chat bot. Telegram chỉ cho bot tải tệp **≤ 20 MB** (khoảng 20–40 phút ghi âm m4a).
   - Tệp lớn hơn, hoặc **mọi tệp mp4**: tải lên Google Drive của mình rồi gửi link cho bot, hoặc nhắn «tóm tắt cuộc họp
     mới nhất trong thư mục Họp». Bot tải bằng token Google của chính người đó.
2. **Tách tiếng.** mp4 thì dùng `ffmpeg` lấy riêng âm thanh (mono 16 kHz). Gemini đọc được cả video, nhưng tính token
   cho từng khung hình nên đắt hơn nhiều; họp cần lời nói, không cần hình. Image `api` hiện **chưa có ffmpeg**, phải
   thêm vào Dockerfile.
3. **Chép lời.** Đẩy tệp âm thanh lên **Gemini File API** (nhận tệp tới 2 GB, âm thanh tới khoảng 9,5 giờ), một lượt
   chép lời có mốc giờ và tách người nói. Họp dài hơn khoảng 90 phút thì cắt bằng ffmpeg thành đoạn 30 phút, chép từng
   đoạn rồi nối, vì đầu ra một lượt có trần.
4. **Biên bản.** Lượt thứ hai đọc bản chép, viết theo mẫu người dùng chọn. Bốn mẫu là **dữ liệu** (QĐ-M6 cũ), không
   phải mã: biên bản chính thức · gạch đầu dòng nhanh · danh sách việc · đầy đủ theo giờ. Thêm mẫu không cần sửa mã.
5. **Gửi + lưu.** Gửi bản tóm tắt ngắn vào chat, kèm tệp Word theo mẫu DEGO; đẩy Word lên Drive của người đó; lưu
   biên bản vào kho ghi chú để hỏi lại sau.
6. **Việc + lịch.** Rút danh sách việc (ai làm, hạn) và cuộc hẹn tiếp theo, đưa **một thẻ duyệt**: «tạo» thì thành việc ở
   phân hệ Công việc ERP (hoặc thẻ cá nhân nếu là việc của chính người gửi) và sự kiện Google Calendar. Không tự tạo khi
   chưa duyệt.
7. **Theo dõi tiến độ.** Tệp dài chạy nền (Celery), bot sửa một tin «đang chép… 40%» thay vì im lặng.

## 4. Lưu trữ

Một bảng mới `tab_agent_meeting`: người gửi, tiêu đề, nguồn (id tệp Telegram / Drive), thời lượng, trạng thái (SMALLINT:
chờ · đang chép · đang viết · xong · hỏng), bản chép (văn bản dài), biên bản, mẫu dùng, id ghi chú trong kho, id tệp
Word trên Drive, danh sách việc đã tạo. Tệp âm thanh **không giữ** trên máy chủ sau khi xong (xóa tệp tạm); bản gốc nằm
ở Drive / Telegram của người gửi.

## 5. Lộ trình

| Bước | Việc | Cỡ |
|---|---|---|
| 10.0 | **Thử thật một tệp họp** (Q5): chép + một mẫu biên bản bằng tay qua mã thử; đo chất lượng tiếng Việt, thời gian, token. Không qua thì dừng, không làm tiếp | 1 ngày |
| 10.1 | Nhận tệp ≤ 20 MB qua Telegram + link Drive (mp3 · m4a · mp4); ffmpeg; File API; chép lời; một mẫu biên bản; gửi tóm tắt + lưu kho; bảng `tab_agent_meeting` | 3 ngày |
| 10.2 | Bốn mẫu biên bản dạng dữ liệu, chọn bằng lời («biên bản chính thức»); Word mẫu DEGO, đẩy lên Drive | 2 ngày |
| 10.3 | Tách việc + hẹn → một thẻ duyệt → việc ERP / thẻ cá nhân / lịch Google | 2 ngày |
| 10.4 | Thư mục «Họp» trên Drive: tự nhặt tệp mới; gộp nhiều tệp của cùng một cuộc họp (nhiều điện thoại cùng ghi) | 2 ngày |

Tổng khoảng **10 ngày công**, thay cho 25 ngày của bản app riêng (nhờ dùng lại Google, khóa AI, nháp việc, kho ghi chú).

## 6. Đã chốt (đại ca 07/10/2026: «làm theo đề xuất của em, mọi người dùng được»)

Q1 mọi người đã đăng nhập bot dùng, chạy bằng khóa AI của chính họ · Q7 video chỉ lấy tiếng · Q8 biên bản chỉ người gửi
xem · Q9 việc rút ra thì bot hỏi một câu kèm danh sách dự án. Còn chờ Q5 (một tệp họp thật để chạy bước 10.0).

**Bước 10.1 XONG 07/10 (ai-CR-104)** — `agent_hub/meetings.py`, bảng `tab_agent_meeting` (migration `meet01`), task
`agent.meeting_process`, ffmpeg trong `docker/Dockerfile.api`. Gửi tệp vào chat riêng (audio / video / document âm
thanh-video / tin thoại > 3 phút, ≤ 20 MB) hoặc link Drive kèm chữ «họp / biên bản / ghi âm / tóm tắt». Chọn mẫu bằng
lời trong chú thích: «chính thức», «danh sách việc», «theo giờ» (mặc định tóm tắt nhanh). 4 mẫu đã có trong mã
(`TEMPLATES`); bước 10.2 đưa ra cấu hình để sửa không cần mã.

**Bước 10.0 thử bằng tệp GIẢ 07/10 (đại ca chưa có tệp thật):** dựng một cuộc họp giao ban 88 giây bằng giọng đọc máy
(gTTS, ba giọng đổi cao độ, ba người Hùng · Mai · Tuấn bàn giá thép, phạt nhà cung cấp xi măng, ngân sách quý 4, lịch họp
tuần sau), chạy trên dev bằng khóa của đại ca. Chép lời (Gemini Flash) gần như nguyên văn, đổi số thành chữ số
(14.200.000, 10/10, 60%), đoán đúng tên người nói theo nội dung. Bốn mẫu viết đúng ý, đúng người, đúng hạn. Hai lỗi tìm ra
và đã vá ở ai-CR-112: (1) DeepSeek v4.1 flash qua trạm modelapi một lần trong bốn trả lẫn cả đoạn «nghĩ» rác vào biên bản
→ `openai_compat.clean_reply` bỏ khối <think> và phần trước «Final answer:»; (2) model suy luận tiêu 3–4 nghìn token cho
phần nghĩ, trần 4000 cũ có thể cắt cụt biên bản → `RECAP_MAX_TOKENS` 12000. Giọng máy rõ hơn họp thật nhiều: vẫn cần
một tệp họp thật để đo tiếng ồn, nói chồng, giọng địa phương.

**Bước 10.2 XONG 07/10 (ai-CR-112)** — mẫu là dữ liệu: 4 mẫu sẵn (`BUILTIN`) + mẫu RIÊNG từng người là một dòng
«Mẫu biên bản «tên»: lời dặn» trong sổ ghi nhớ (tool `save_meeting_template`, «quên» được như mọi dòng sổ) + lời dặn tại
chỗ trong chú thích («theo mẫu: …»). Phiên chép lại mẫu đã dùng (`template_label`, `template_prompt`, migration `meet02`).
Tool `list_my_meetings` · `rewrite_meeting_minutes` (viết lại theo mẫu khác, KHÔNG chép lời lại) — 65 tool. Word theo mẫu
DEGO: Times New Roman 13, lề 3/2 cm, đầu trang công ty, bảng thông tin (ngày lập · thời lượng · mẫu · người lập), bảng
Markdown thành bảng Word, chữ đậm giữ đậm, số trang; mẫu chính thức thêm quốc hiệu, «Số: …/BB-HĐ» và chỗ ký Thư ký /
Chủ trì. Word lên Drive vào thư mục «Biên bản họp» (tự tạo lần đầu).

**Chạy trọn trên dev 07/10 (ai-CR-113):** tệp giả gửi vào chat đại ca → biên bản chính thức + Word + Drive đúng; bước chép
lời treo 12 phút vì model chính quá tải → trần chờ theo độ dài đoạn (2 phút + 1/3 độ dài) + thử một lần model dự phòng.

**Bước 10.3 XONG 07/10 (ai-CR-114)** — `agent_hub/meeting_actions.py`, cột `tab_agent_meeting.actions` (migration
`meet03`). Biên bản gửi xong → một lượt model rút JSON việc (tên · người làm · hạn) + lịch hẹn (tên · giờ · độ dài · nơi),
ngày tương đối tính theo ngày xử lý → MỘT thẻ đánh số, không tạo gì khi chưa duyệt. Người gửi nhắn «tạo hết», «tạo 1 3»,
kèm «dự án 2» khi có nhiều dự án (Q9: thẻ liệt kê sẵn dự án, thiếu thì hỏi lại đúng một câu), hoặc «bỏ». Việc → phân hệ
Dự án qua đường «tạo» của nháp việc (kiểm quyền work_task.create, báo chuông người được giao); người làm khớp đúng một nhân
sự thì gán, không thì ghi tên vào mô tả. Không quyền / không ở dự án nào → thẻ cá nhân. Lịch → Google Calendar, chưa nối
Google → thẻ cá nhân. Mỗi mục ghi trạng thái, «tạo» lần hai không tạo trùng; thẻ mới thay thẻ cũ còn treo; thẻ sống 48 giờ.

**Bước 10.4 + Word chuẩn DEGO XONG 08/10 (ai-CR-116).** Đại ca: *"họp xong anh đưa file mới nhất lên thư mục họp trên
Drive, em nhận thông tin và hỏi anh, hoặc anh nói cần report cuộc họp mới nhất, em tìm và trả, kèm công việc trích xuất"*.

- `agent_hub/meeting_drive.py`: vòng `agent.meeting_drive_scan` mỗi 5 phút, với mỗi người đã nối Google + có chat riêng: tìm
  tệp âm thanh / video mới trong thư mục tên «Họp» (scope drive.readonly; mốc từng người ở `tab_agent_cursor`
  `drive_hop:<user>`; lần đầu chỉ đặt mốc). Có tệp mới → một thẻ HỎI (không tự chạy, vì tốn khóa AI của họ): «làm biên bản»
  gộp mọi tệp thành một cuộc họp nối theo giờ tạo (họp ghi nhiều phần), «làm tệp 2» chọn tệp (hai máy cùng ghi thì chọn tệp
  rõ nhất), thêm tên mẫu được, «bỏ qua». Câu thường có chữ «làm» («làm sao để…») không bị thẻ nuốt.
- Nhiều tệp Drive: `source_ref` = các id cách dấu phẩy (≤ 8), mỗi tệp tách tiếng rồi `concat_audio` nối lại.
- Tool `latest_meeting_report` (66 tool): thư mục «Họp» có tệp mới hơn cuộc họp đã làm → làm luôn; không thì gửi lại biên
  bản + Word + thẻ việc / lịch còn chờ (`meetings.resend`, thẻ dùng lại mục đã rút, không tốn lượt model).
- Word theo chuẩn DEGO (STD-RECAP-DEGO-v1.0): chép nguyên thư viện `dego_docx.py` của skill dego-docx + logo
  (`agent_hub/assets/dego_logo.png`) — đầu trang logo + «RECAP HỌP / BIÊN BẢN HỌP» + mã văn bản `RECAP-yyyy.mm.dd-<id>`,
  tiêu đề in hoa, bảng thông tin (ngày lập · thời lượng · người ghi · nguồn · thành phần lấy từ mục NGƯỜI THAM DỰ), ghi chú AI,
  hộp TL;DR, thanh mục teal, đề mục con, nhãn Ý CHÍNH / ĐÃ CHỐT (✓), bảng việc có chip Ưu tiên, mẫu chính thức thêm khối XÉT
  DUYỆT ký, phụ lục bản chép lời, chân trang lặp có số trang. Mẫu mặc định mới «Recap DEGO» (khóa `dego`) viết đúng các mục
  của chuẩn. Tệp mẫu đã dựng thử ở thư mục `mau-bien-ban/` cạnh các kho mã.
- ai-CR-117 (08/10): thư mục «Họp» báo cả TÀI LIỆU (pdf / Word / Excel / Google Docs); «tóm tắt tệp n» hoặc «phân tích tệp n …» đọc rồi trả lời. `export_text` bóc chữ PDF / Word / Excel thay vì trả byte.

## 7. Câu chờ đại ca chốt (bản đầu)

| Mã | Câu | Em đề xuất |
|---|---|---|
| Q1 | Ai được dùng: chỉ đại ca, hay mọi người đã đăng nhập bot (chạy bằng khóa AI của chính họ)? | Mọi người, chi phí theo khóa người gửi |
| Q5 | Một tệp họp thật để thử bước 10.0 (để trong thư mục trên máy hoặc Drive, không gửi qua chat công khai) | — |
| Q7 | Video: chỉ lấy tiếng (rẻ), hay đọc cả hình để bắt chữ trên slide? | Chỉ lấy tiếng; cần slide thì làm sau |
| Q8 | Biên bản lưu ở đâu, ai xem: chỉ người gửi, hay chia cho người dự họp có tên trong ERP? | Chỉ người gửi; muốn chia thì gửi tay |
| Q9 | Việc rút ra: tạo vào dự án nào trong phân hệ Công việc? | Bot hỏi một câu kèm danh sách dự án của người gửi |
