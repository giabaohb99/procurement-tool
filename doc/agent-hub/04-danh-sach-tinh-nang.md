# AGENT HUB — DANH SÁCH TÍNH NĂNG CẦN LÀM

**Bản 1.0 · 24/09/2026.** Gom mọi việc còn lại của Đậu Đậu và các trợ lý mới đại ca muốn thêm
(biên bản họp, lịch và nhắc việc, nghiên cứu). Việc đã xong xem `change-log-ai.md`; thiết kế
bot sửa mã xem `01-thiet-ke-ky-thuat.md`; thiết kế biên bản họp gốc (28-29/08, chưa có mã) ở
`meeting-recap/doc/` trên máy.

**Tổng: 43 tính năng** — A 8 · N 5 · P 2 · M 8 · K 4 · T 12 · R 4. **Đã xong 12** (24/09/2026): A-01 … A-07 + N-02 (ai-CR-032 … 038) + R-01 … R-04 (ai-CR-044, phần Drive chờ N-03); A-08 vẫn chờ 4 câu của AN-007. Cỡ: **S** = một ngày trở xuống · **M** = hai
đến ba ngày · **L** = từ bốn ngày. Cỡ là ước thô, đo lại sau từng việc (A-01).

## Nguyên tắc chia bot

Chia bot theo **quyền**, không chỉ theo chức năng. Bot nào đọc nội dung lạ (web, tệp người
khác gửi) thì không được giữ khóa nào, vì nội dung đó có thể chứa lệnh cài sẵn.

| Bot | Làm gì | Giữ quyền gì |
|---|---|---|
| **Đậu Đậu** | Sửa mã, gộp, deploy dev | Khóa GitHub, SSH lên VPS |
| **Thư ký** | Biên bản họp, lịch, nhắc việc | Google Drive + Calendar, đọc ERP |
| **Nghiên cứu** | Research, tìm tài liệu, kiểm chứng nội dung | Không giữ khóa nào, chỉ đọc web và kho tài liệu |

Cả ba chạy chung một nền (sổ ghi, khóa Gemini trả phí, bộ hẹn giờ, theo dõi chi phí), mỗi bot
một token Telegram riêng.

## Nhóm A — Đậu Đậu (bot sửa mã), phần còn lại

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| A-01 | Đo thời gian: thẻ kết quả ghi tổng thời gian và thời gian từng bước | S | **Xong** ai-CR-032 |
| A-02 | Dọn nhánh `bot/*` sau khi gộp | S | **Xong** ai-CR-033 — Q3 em chọn: dọn lúc việc ĐÓNG («xong»/«bỏ») |
| A-03 | Cổng kiểm cho `frontend/` (bản v1) | S | **Xong** ai-CR-034 — Q4 em chọn: chỉ chặn lỗi kiểu trong tệp bot vừa sửa |
| A-04 | Nhận ảnh chụp lỗi gửi kèm yêu cầu sửa, đưa cho bước rà soát và sửa mã | S | **Xong** ai-CR-035 |
| A-05 | Màn quản lý việc của bot trong ERP v2: danh sách, lịch sử, chi phí (AN-006) | M | **Xong** ai-CR-036 — `/system/agent-tasks`, khóa `agent_task`; **đang ẩn khỏi menu** (ai-CR-039, đại ca hỏi bot thay vì mở màn) |
| A-06 | Phiếu hỗ trợ trong ERP làm nguồn việc, không chỉ Telegram (AN-005) | M | **Xong** ai-CR-037 — giao cho tài khoản bot hoặc nhãn bộ phận |
| A-07 | Mỗi người tự đăng nhập tài khoản ERP trong Telegram (ai-CR-004) | M | **Xong** ai-CR-038 — mã một lần ở tab Telegram của `/me` |
| A-08 | Xem thử bản sửa trên máy local qua Cloudflare tunnel (AN-007) | L | Còn 4 câu chờ đại ca |

## Nhóm N — Nền chung cho nhiều bot

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| N-01 | Nhiều bot một nền: mỗi bot một token, sổ ghi rõ tin nào của bot nào | M | |
| N-02 | Tải tệp từ Telegram: ảnh, tin thoại, tệp nhỏ (trần 20 MB của Telegram) | S | **Xong phần ảnh** ai-CR-035; tin thoại để T-07 |
| N-03 | Kết nối tài khoản Google một lần (Drive + Calendar), khóa lưu mã hóa | M | Chờ Q2 |
| N-04 | Chi phí theo từng bot, từng ngày, có trần ngày | S | |
| N-05 | Cách ly quyền: mỗi bot chỉ thấy khóa của nó | M | Bắt buộc trước khi bật bot Nghiên cứu |

## Nhóm P — Phục vụ từng người đã đăng nhập (thêm 24/09/2026)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| P-01 | Đẩy thông báo ERP (chuông) sang Telegram của từng người đã đăng nhập: phiếu chờ họ duyệt, việc giao cho họ | M | Chờ đại ca chọn: toàn bộ chuông hay chỉ «chờ bạn duyệt / việc giao cho bạn» |
| P-02 | Trần lượt hỏi / chi phí theo từng người mỗi ngày | S | Để một người không dùng hết hạn mức Gemini của cả công ty |

## Nhóm M — Trợ lý mở: MCP, AI tự chọn, nhiều kênh (thêm 24/09/2026)

**Đại ca chốt 24/09/2026:** mỗi người **tự do chọn ứng dụng AI** và tự gắn khóa của mình (Claude,
ChatGPT, Gemini, Cursor…); hệ thống chỉ cung cấp công cụ. Đại ca chấp nhận rủi ro dữ liệu ERP đi sang
nhà cung cấp AI do từng người chọn. Làm trên **web trước**, rồi mở rộng kênh Telegram và Zalo dùng chung
lõi. Cổng MCP phải nằm trong backend ERP có tên miền thật (dev rồi prod), không đặt trên máy cá nhân.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| M-01 | Cổng MCP trên backend ERP (Streamable HTTP) — dùng CHUNG bộ tool với Trợ lý web và Telegram, không viết lại | L | Cần gộp phần bot vào `erp-v2` |
| M-02 | Khóa kết nối cá nhân lấy ở Trang cá nhân: có hạn, gỡ được, tách chỉ đọc / được ghi, nhật ký từng lượt gọi | M | Tool chạy đúng phạm vi dữ liệu của người đó |
| M-03 | Tool chỉ đọc qua MCP: tra số liệu, tình trạng phiếu, báo cáo | M | Bước thử đầu tiên, 1-2 người |
| M-04 | Tool tạo / gửi duyệt qua MCP, xác nhận hai bước phía server (dùng lại `draft_create`) | M | Đề nghị thanh toán chỉ trên web |
| M-05 | Tool báo lỗi qua MCP → phiếu hỗ trợ → Đậu Đậu | S | Duyệt / gộp vẫn theo nhóm K |
| M-06 | Mỗi người tự nối Google của mình (Drive, Lịch), tool lịch / Drive đọc dữ liệu của chính họ | L | Thay N-03 theo hướng từng người; khóa OAuth lưu mã hóa |
| M-07 | Trợ lý trên web chạy bằng AI + khóa do từng người chọn (khóa lưu mã hóa, chỉ người đó dùng) | M | Công ty thôi trả tiền model theo lượt |
| M-08 | Kênh Zalo OA dùng chung lõi với Telegram | M | Zalo đẩy webhook: dùng tên miền ERP |

## Nhóm K — Ai được ra lệnh sửa mã (KHÔNG lên giao diện web, thêm 24/09/2026)

Tách hai câu hỏi: **ai được RA LỆNH** cho bot (danh sách người) và **bot được LÀM gì** (khóa của riêng bot).
Người ra lệnh không cần SSH hay quyền GitHub riêng — họ chỉ nhắn bot; khóa nằm ở bot và bị giới hạn.
Lập trình viên tự sửa tay thì dùng quyền GitHub của chính họ, quản lý trên GitHub, không qua ERP.
**Đại ca chốt 24/09/2026 (cách 3):** cấu hình quyền KHÔNG ở web, KHÔNG phải build hay khởi động lại — đại ca
nhắn cho bot, bot ghi sổ. Ba nơi đã cân: tệp trên máy chạy bot (không lịch sử) · biến `.env` (phải khởi động
lại) · **nhắn Telegram + sổ của bot (chọn: có lịch sử, gốc quyền vẫn là chat đại ca như hiện nay)**.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| K-01 | **XONG 24/09/2026 (ai-CR-051).** Cấp quyền sửa mã bằng CÂU NHẮN của đại ca trên Telegram («cho anh Được quyền gộp dev», bot hỏi lại rồi «đúng»), lưu sổ của bot (`tab_agent_grant`): tài khoản ERP + chat Telegram + cấp (`duyet_ke_hoach` · `gop_dev`); mỗi lần cấp/gỡ đều ghi sổ và báo lại; hỏi «ai đang được sửa mã» là bot liệt kê | S | **Cách 3, đại ca chốt 24/09/2026.** Chỉ chat đại ca (khai cứng `AGENT_TELEGRAM_CHAT_ID` trong `.env`) mới cấp được và chat đó không gỡ được qua chat. Không lên web, không build, không khởi động lại. Dự phòng: tệp trên máy chạy bot, bot đọc mỗi lượt. Báo lỗi thì ai cũng được (M-05); prod không cấp cho ai |
| K-02 | Khóa của RIÊNG bot thay khóa của đại ca: GitHub App / deploy key chỉ đẩy `bot/*` + `erp-v2`; SSH lên VPS bằng khóa riêng bị khóa cứng đúng lệnh deploy dev (`command=` trong `authorized_keys`) | M | Hiện bot đang mượn khóa SSH của đại ca |
| K-03 | Bảo vệ nhánh trên GitHub: `main` bắt buộc PR + duyệt; bot không có quyền đẩy `main` | S | Đại ca bật trên GitHub, không phải mã |
| K-04 | **XONG 24/09/2026 (ai-CR-051)** — người có cấp phải NÊU MÃ VIỆC, câu «xong rồi» trơn không đóng việc. Lệnh nhạy cảm (duyệt kế hoạch, gộp, deploy, thu hồi) kiểm cấp theo K-01; người không đủ cấp nhắn thì bot từ chối và báo đại ca | S | Hiện chỉ một chat đại ca |

## Nhóm T — Thư ký (biên bản họp, lịch, nhắc việc)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| T-01 | **Thử trước (M0):** chạy một tệp họp thật qua Gemini ra biên bản, đo chất lượng và chi phí | S | Chốt chặn: không qua thì dừng cụm biên bản. Chờ Q1, Q5 |
| T-02 | Đọc thư mục ghi âm trên Drive, gom nhiều tệp của một cuộc họp thành một phiên | M | Tệp họp dài không gửi qua bot được, phải qua Drive |
| T-03 | Chuẩn hóa và cắt âm thanh dài cho vừa model | M | |
| T-04 | Gỡ băng từng tệp, nối theo thứ tự thời gian | M | |
| T-05 | Mẫu biên bản là dữ liệu (chính thức · gạch đầu dòng · danh sách việc · đầy đủ theo giờ), chọn mẫu bằng chữ | M | Thêm mẫu không phải sửa mã |
| T-06 | Xuất Word theo mẫu DEGO lên Drive, gửi bản tóm tắt ngay trong chat kèm link | M | |
| T-07 | Tin thoại ngắn thành lời nhắc hoặc việc | S | Cần N-02 |
| T-08 | Bản tin 8h sáng: lịch hôm nay, việc đến hạn, phiếu chờ đại ca duyệt | M | Cần N-03 |
| T-09 | Nhắc trước mỗi cuộc họp 15 phút | S | Cần N-03 |
| T-10 | «Nhắc anh 3h gọi nhà cung cấp X»: tạo lời nhắc bằng câu nói | S | Dùng bộ hẹn giờ và phần hiểu giờ sẵn có |
| T-11 | Tạo lịch Google Calendar bằng câu nói, hỏi lại trước khi tạo | S | Cần N-03 |
| T-12 | Việc rút ra từ biên bản thành lời nhắc và việc trong phân hệ Công việc của ERP | M | Chỗ hai cụm cộng lại đáng giá nhất |

## Nhóm R — Nghiên cứu (research, tìm tài liệu, kiểm chứng)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| R-01 | Research một chủ đề: Gemini tìm Google, trả bản tóm tắt kèm nguồn | S | **Xong** ai-CR-044 (`/tim`); lượt tìm không có công cụ tác động nên chưa cần N-05 |
| R-02 | Kiểm chứng một nhận định: đúng · sai · chưa đủ căn cứ, kèm nguồn | S | **Xong** ai-CR-044 (`/kiemchung`) |
| R-03 | Tìm tài liệu nội bộ: kho tài liệu đã nạp + thư mục Drive | M | **Xong phần kho tài liệu** ai-CR-044 (`/tailieu`); phần Drive chờ N-03 |
| R-04 | Xuất báo cáo nghiên cứu ra Word lên Drive | S | **Xong phần Word gửi qua Telegram** ai-CR-044 (`/word`); lên Drive chờ N-03 |

## Lộ trình theo phase (sắp lại 24/09/2026 theo hướng «trợ lý mở»)

Cỡ là ước THÔ theo ngày công của một người, đo lại sau mỗi phase (A-01 đã có số đo từng bước).

| Phase | Tên | Gồm | Cần đại ca quyết / cung cấp | Cỡ ước |
|---|---|---|---|---|
| **0** | Đang chạy | Đậu Đậu trên máy đại ca: nhận việc, rà, sửa, kiểm, gộp, deploy dev; đăng nhập bằng mã; tạo + gửi duyệt phiếu từ chat; nghiên cứu; chi phí | — | xong |
| **1** | Khóa quyền sửa mã | K-01 cấp quyền bằng câu nhắn (cách 3) **xong** · K-04 kiểm cấp trước lệnh nhạy cảm **xong** · K-03 bảo vệ nhánh `main` · K-02 khóa riêng của bot | K-03: đại ca bật trên GitHub; K-02: tạo khóa deploy riêng cho bot | 3–4 ngày |
| **2** | Bot lên ERP dev | Gộp phần bot vào `erp-v2`, chạy trên server dev (phiếu bot tạo là phiếu thật, link bấm được trên điện thoại, người khác dùng Telegram được) · bật phiếu hỗ trợ làm nguồn việc (A-06) | Cho bot tạo phiếu thật trên dev; tài khoản ERP của bot; khóa Telegram/Gemini trên server | 3–5 ngày |
| **3** | Trợ lý theo từng người trên web | M-07 AI + khóa do từng người chọn · M-02 khóa kết nối cá nhân · P-02 trần chi phí theo người · P-01 đẩy thông báo ERP sang Telegram cá nhân · T-10 nhắc việc bằng câu nói · T-07 tin thoại | P-01: đẩy toàn bộ chuông hay chỉ «chờ bạn duyệt / việc giao cho bạn» | 2 tuần |
| **4** | Cổng MCP | M-01 cổng MCP dùng chung bộ tool · M-03 tool đọc · M-04 tool tạo/gửi duyệt có xác nhận · M-05 báo lỗi → Đậu Đậu | Thử với 1–2 người trước; chạy dev rồi prod | 2 tuần |
| **5** | Kết nối Google của từng người | M-06 Drive + Lịch riêng từng người → T-08 bản tin sáng, T-09 nhắc trước họp, T-11 tạo lịch bằng câu nói, R-03/R-04 phần Drive | Cá nhân hay Workspace công ty (Q2); đăng ký ứng dụng Google của công ty | 2 tuần |
| **6** | Nhiều kênh, nhiều bot | M-08 kênh Zalo OA · N-01 nhiều bot một nền · N-04 chi phí theo bot · N-05 cách ly khóa | Tạo bot/OA và đặt tên (Q6) | 1–2 tuần |
| **7** | Thư ký biên bản họp | T-01 thử một tệp họp thật (M0) → T-02 … T-06, T-12 | Cho ai dùng (Q1), một tệp ghi âm thật (Q5); chỉ làm tiếp khi M0 đạt | 3 tuần |
| sau | Để sau | A-08 xem thử qua tunnel (AN-007, 4 câu chờ) | — | — |

Phase 1 và 2 là nền cho mọi phase sau: 1 để mở cho nhiều người mà không lo ai đụng mã, 2 để bot
làm việc trên dữ liệu thật. Phase 3 → 6 mở dần theo hướng đại ca chốt: web trước, MCP, Google từng
người, rồi Zalo. Phase 7 độc lập, làm khi có tệp thử.

**Năng lực:** đội làm được khoảng 24 ngày công mỗi tháng và phần lõi ERP còn thiếu 156 ngày
công (số của `meeting-recap/doc/04`). Các trợ lý này là việc cộng thêm, giành giờ với ERP.

## Câu chờ đại ca

| Mã | Câu | Chặn |
|---|---|---|
| Q1 | Biên bản họp làm cho đại ca dùng, hay cho CEO như yêu cầu gốc (bản gốc: chạy trên máy riêng của CEO, chỉ CEO thao tác) | T-01 … T-06 |
| Q2 | Nối tài khoản Google nào: cá nhân hay Google Workspace công ty | N-03 |
| Q3 | ~~Nhánh `bot/*` xóa lúc gộp hay lúc «xong»~~ — em chọn lúc việc đóng (ai-CR-033), đại ca đổi thì báo | — |
| Q4 | ~~Cổng kiểm v1~~ — em chọn chặn lỗi kiểu trong tệp bot sửa (ai-CR-034; `frontend/` không có eslint) | — |
| Q5 | Một tệp ghi âm họp thật để thử (đặt vào thư mục trên máy, không gửi qua chat) | T-01 |
| Q6 | Tên cho bot Thư ký và bot Nghiên cứu | N-01 |
