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

## 6. Câu chờ đại ca chốt

| Mã | Câu | Em đề xuất |
|---|---|---|
| Q1 | Ai được dùng: chỉ đại ca, hay mọi người đã đăng nhập bot (chạy bằng khóa AI của chính họ)? | Mọi người, chi phí theo khóa người gửi |
| Q5 | Một tệp họp thật để thử bước 10.0 (để trong thư mục trên máy hoặc Drive, không gửi qua chat công khai) | — |
| Q7 | Video: chỉ lấy tiếng (rẻ), hay đọc cả hình để bắt chữ trên slide? | Chỉ lấy tiếng; cần slide thì làm sau |
| Q8 | Biên bản lưu ở đâu, ai xem: chỉ người gửi, hay chia cho người dự họp có tên trong ERP? | Chỉ người gửi; muốn chia thì gửi tay |
| Q9 | Việc rút ra: tạo vào dự án nào trong phân hệ Công việc? | Bot hỏi một câu kèm danh sách dự án của người gửi |
