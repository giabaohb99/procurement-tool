# AGENT HUB — DANH SÁCH TÍNH NĂNG CẦN LÀM

**Bản 1.0 · 24/09/2026.** Gom mọi việc còn lại của Đậu Đậu và các trợ lý mới đại ca muốn thêm
(biên bản họp, lịch và nhắc việc, nghiên cứu). Việc đã xong xem `change-log-ai.md`; thiết kế
bot sửa mã xem `01-thiet-ke-ky-thuat.md`; thiết kế biên bản họp gốc (28-29/08, chưa có mã) ở
`meeting-recap/doc/` trên máy.

**Tổng: 50 tính năng** — A 8 · N 5 · P 2 · M 8 · K 4 · D 7 · T 12 · R 4. **Đã xong 24** (25/09/2026): T-10 (ai-CR-060) · T-07 (ai-CR-061) · P-02 (ai-CR-062) · P-01 (ai-CR-059) · D-06 (ai-CR-056) · D-04 (ai-CR-055) · D-03 + D-05 (ai-CR-054) · D-01 + D-02 (ai-CR-053) · K-01 + K-04 (ai-CR-051); A-01 … A-07 + N-02 (ai-CR-032 … 038) + R-01 … R-04 (ai-CR-044, phần Drive chờ N-03); A-08 vẫn chờ 4 câu của AN-007. Cỡ: **S** = một ngày trở xuống · **M** = hai
đến ba ngày · **L** = từ bốn ngày. Cỡ là ước thô, đo lại sau từng việc (A-01).

## Nguyên tắc chia bot

Chia bot theo **quyền**, không chỉ theo chức năng. Bot nào đọc nội dung lạ (web, tệp người
khác gửi) thì không được giữ khóa nào, vì nội dung đó có thể chứa lệnh cài sẵn.

| Bot | Làm gì | Giữ quyền gì |
|---|---|---|
| **Đậu Đậu** | Sửa mã, gộp, deploy dev | Không giữ khóa sửa mã nào; khóa GitHub + SSH nằm ở **máy sửa mã** (nhóm D), bot chỉ xếp việc |
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
| P-01 | **XONG 25/09/2026 (ai-CR-059).** Đẩy thông báo ERP (chuông) sang Telegram của từng người đã đăng nhập: phiếu chờ họ duyệt, việc giao cho họ | M | Mặc định «việc của tôi», mỗi liên kết tự đổi (tắt / tất cả) bằng câu nhắn hoặc ở Trang cá nhân |
| P-02 | **XONG 25/09/2026 (ai-CR-062).** | Trần lượt hỏi / chi phí theo từng người mỗi ngày | S | Để một người không dùng hết hạn mức Gemini của cả công ty |

## Nhóm M — Trợ lý mở: MCP, AI tự chọn, nhiều kênh (thêm 24/09/2026)

**Đại ca chốt 24/09/2026:** mỗi người **tự do chọn ứng dụng AI** và tự gắn khóa của mình (Claude,
ChatGPT, Gemini, Cursor…); hệ thống chỉ cung cấp công cụ. Đại ca chấp nhận rủi ro dữ liệu ERP đi sang
nhà cung cấp AI do từng người chọn. Làm trên **web trước**, rồi mở rộng kênh Telegram và Zalo dùng chung
lõi. Cổng MCP phải nằm trong backend ERP có tên miền thật (dev rồi prod), không đặt trên máy cá nhân.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| M-01 | Cổng MCP trên backend ERP (Streamable HTTP) — dùng CHUNG bộ tool với Trợ lý web và Telegram, không viết lại | L | Cần gộp phần bot vào `erp-v2` |
| M-02 | Khóa kết nối cá nhân lấy ở Trang cá nhân: có hạn, gỡ được, tách chỉ đọc / được ghi, nhật ký từng lượt gọi | M | Tool chạy đúng phạm vi dữ liệu của người đó. Phần khóa Gemini cá nhân cho kênh chat đã kéo lên phase 2 (D-01) |
| M-03 | Tool chỉ đọc qua MCP: tra số liệu, tình trạng phiếu, báo cáo | M | Bước thử đầu tiên, 1-2 người |
| M-04 | Tool tạo / gửi duyệt qua MCP, xác nhận hai bước phía server (dùng lại `draft_create`) | M | Đề nghị thanh toán chỉ trên web |
| M-05 | Tool báo lỗi qua MCP → phiếu hỗ trợ → Đậu Đậu | S | Duyệt / gộp vẫn theo nhóm K |
| M-06 | Mỗi người tự nối Google của mình (Drive, Lịch), tool lịch / Drive đọc dữ liệu của chính họ | L | Thay N-03 theo hướng từng người; khóa OAuth lưu mã hóa |
| M-07 | Trợ lý trên web chạy bằng AI + khóa do từng người chọn (khóa lưu mã hóa, chỉ người đó dùng) | M | Công ty thôi trả tiền model theo lượt. Đại ca chốt 24/09: trên dev, web vẫn dùng khóa công ty; D-01 chỉ cho kênh chat |
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

## Nhóm D — Bot lên dev: một bot cho mọi người, máy sửa mã tách rời (chốt 24/09/2026)

**Đại ca chốt 24/09/2026, sau ai-CR-051.** Chỉ có **MỘT Đậu Đậu, chạy trên server dev**; không còn bot local
và bot dev riêng (một token Telegram chỉ cho một tiến trình kéo tin). Với mọi người nó là trợ lý cá nhân:
ai đăng nhập (`/dangnhap`) thì chat dưới tài khoản ERP và **khóa Gemini của chính người đó**. Tài khoản đại ca
là **trường hợp đặc biệt** trong cấu hình dev (`AGENT_TELEGRAM_CHAT_ID`): chat đại ca, và ai được cấp theo K-01,
mới có mảng mã nguồn (gom việc, lập kế hoạch, hỏi về bản vá, duyệt, gộp, deploy). Tới bước sửa mã, bot trên
dev **gọi xuống máy sửa mã** (máy đại ca là máy số 1, thêm máy khác được), vì Claude Code, GitHub, SSH chỉ ở đó.

Ba loại khóa Gemini, không dùng chung: **khóa cá nhân** (Telegram / Zalo của người đó, kể cả lượt gom việc và
lập kế hoạch của đại ca) · **khóa công ty trên dev** (chỉ Trợ lý trên web) · không còn «khóa của bot».
Không lùi về khóa công ty: người chưa gắn khóa thì bot không trả lời câu hỏi AI, chỉ nhắc gắn khóa; đăng nhập,
xem tình trạng việc, ra lệnh trên việc vẫn dùng được vì không cần Gemini.

| | Trên dev | Máy sửa mã (máy đại ca + máy được đăng ký) |
|---|---|---|
| Chạy gì | Toàn bộ bot: nhận tin, Trợ lý, nghiên cứu, tạo phiếu, gom việc, lập kế hoạch, sổ quyền, sổ máy | **Chỉ runner**: Claude Code (gói của chủ máy) + worktree + khóa GitHub/SSH của máy |
| Khóa Gemini | Khóa cá nhân từng người; khóa công ty chỉ cho web | Không cần |
| Telegram | Một token, của bot trên dev | Không cần |
| Nối nhau | Hàng đợi sửa mã trên dev | Runner mở đường hầm SSH lên dev bằng khóa riêng của máy, tự xưng tên + mã máy, kéo việc về, ghi kết quả lên bằng tài khoản MySQL riêng chỉ đụng bảng của bot |
| Máy tắt | Mọi thứ khác vẫn chạy; việc sửa mã xếp hàng, bot báo «phần sửa mã đang tắt / đang chờ máy X» | — |

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| D-01 | **XONG 25/09/2026 (ai-CR-053).** **Khóa Gemini cá nhân**: Trang cá nhân → tab «Khóa AI» (web, KHÔNG qua chat vì Telegram giữ lịch sử vĩnh viễn), lưu mã hóa, gắn tài khoản ERP; lưu xong gọi thử một lượt nhỏ báo đúng/sai; nghỉ việc thì xóa cùng lúc khóa phiên (theo CR-400); một khóa dùng cho cả Telegram lẫn Zalo; «tháng này tốn bao nhiêu» tính theo khóa từng người | M | Gộp M-02 + M-07 phần kênh chat, kéo từ phase 3 lên phase 2. Web vẫn khóa công ty |
| D-02 | **XONG 25/09/2026 (ai-CR-053).** **Bỏ tài khoản chung**: `AGENT_ASSISTANT_USER` để trống trên dev, ai cũng `/dangnhap` kể cả đại ca; chưa đăng nhập thì bot chỉ nhắc cách lấy mã, không lỗi | S | Xóa «biến nguy hiểm nhất» của `01` §9 khỏi dev |
| D-03 | **XONG 25/09/2026 (ai-CR-054).** **Sổ máy sửa mã** `tab_agent_runner`: tên máy, chủ máy (tài khoản ERP), mã máy (băm), lần liên lạc cuối, cờ được deploy dev. Đăng ký bằng câu nhắn ở chat đại ca giống K-01 («thêm máy của anh Được» → bot phát mã máy một lần, dán vào `.env` runner); gỡ «tắt máy của anh Được» → runner bị từ chối ngay, không build lại. «máy nào đang bật» liệt kê | M | Hai sổ, hai câu hỏi: K-01 = ai được RA LỆNH, D-03 = máy nào được LÀM |
| D-04 | **XONG gói 25/09/2026 (ai-CR-055, chạy thật chờ D-06; hướng dẫn `05-may-sua-ma.md`).** **Runner tách rời**: chạy trên máy bất kỳ có Docker + Claude Code đăng nhập gói của chủ máy + khóa GitHub/SSH riêng của máy; nối lên dev qua đường hầm SSH, kéo việc từ hàng đợi, ghi kết quả bằng tài khoản MySQL riêng. Việc **dính máy** từ lúc bắt đầu tới hết (worktree, phiên Claude Code, «làm tiếp», «hỏi thêm» đều trên máy đó); máy tắt thì việc chờ, bot nói rõ chờ máy nào | L | Thay đường hầm bằng gọi API ERP có khóa riêng để sau (không chạm DB) |
| D-05 | **XONG 25/09/2026 (ai-CR-054).** **Chia việc giữa các máy**: việc mới → máy rảnh và đang bật nhận trước; chỉ định bằng «AI-0012 cho máy anh Được làm»; thẻ kết quả ghi máy nào đã làm | S | Deploy dev: chỉ máy đại ca và máy được bật cờ; máy mới mặc định KHÔNG deploy |
| D-06 | **XONG 25/09/2026 (ai-CR-056): bot Lạc Lạc chạy trong cụm dev, AI-0001 đi trọn vòng gộp + deploy dev từ máy đại ca.** **Stack bot trên dev**: compose riêng cho poller + api + worker + beat cạnh ERP dev, `.env` trên VPS giữ token Telegram của bot dev (bot mới tạo ở BotFather), `AGENT_TELEGRAM_CHAT_ID` = id chat đại ca (chat riêng: id = id người dùng, bot nào cũng vậy) | M | Gộp phần bot vào `erp-v2`; đại ca tự dán khóa, em chỉ soạn mẫu `.env` |
| D-07 | **Bot dev tự deploy dev** không cần máy sửa mã: bước deploy chạy ngay trên host dev (hook nhỏ trên host, không cấp docker socket cho container bot) | M | Để sau D-04 chạy ổn; trước đó deploy dev vẫn qua máy đại ca |

Thứ tự làm phase 2: **(a)** D-01 + D-02 (xong 25/09) → **(b)** D-03 + D-04 + D-05 (xong 25/09) → **(c)** D-06. D-07 để cuối.

## Nhóm T — Thư ký (biên bản họp, lịch, nhắc việc)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| T-01 | **Thử trước (M0):** chạy một tệp họp thật qua Gemini ra biên bản, đo chất lượng và chi phí | S | Chốt chặn: không qua thì dừng cụm biên bản. Chờ Q1, Q5 |
| T-02 | Đọc thư mục ghi âm trên Drive, gom nhiều tệp của một cuộc họp thành một phiên | M | Tệp họp dài không gửi qua bot được, phải qua Drive |
| T-03 | Chuẩn hóa và cắt âm thanh dài cho vừa model | M | |
| T-04 | Gỡ băng từng tệp, nối theo thứ tự thời gian | M | |
| T-05 | Mẫu biên bản là dữ liệu (chính thức · gạch đầu dòng · danh sách việc · đầy đủ theo giờ), chọn mẫu bằng chữ | M | Thêm mẫu không phải sửa mã |
| T-06 | Xuất Word theo mẫu DEGO lên Drive, gửi bản tóm tắt ngay trong chat kèm link | M | |
| T-07 | **XONG 25/09/2026 (ai-CR-061).** | Tin thoại ngắn thành lời nhắc hoặc việc | S | Cần N-02 |
| T-08 | Bản tin 8h sáng: lịch hôm nay, việc đến hạn, phiếu chờ đại ca duyệt | M | Cần N-03 |
| T-09 | Nhắc trước mỗi cuộc họp 15 phút | S | Cần N-03 |
| T-10 | **XONG 25/09/2026 (ai-CR-060).** | «Nhắc anh 3h gọi nhà cung cấp X»: tạo lời nhắc bằng câu nói | S | Dùng bộ hẹn giờ và phần hiểu giờ sẵn có |
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
| **2 ✔ xong 25/09** | Bot lên ERP dev (nhóm D) | (a) D-01 khóa Gemini cá nhân + D-02 bỏ tài khoản chung · (b) D-03 sổ máy + D-04 runner tách rời + D-05 chia việc · (c) D-06 stack bot trên dev, gộp vào `erp-v2` · bật phiếu hỗ trợ làm nguồn việc (A-06) · D-07 để cuối | **Đã chốt 24/09:** một bot trên dev, ai cũng tự đăng nhập, khóa cá nhân, không lùi khóa công ty. Đại ca làm tay: tạo bot mới ở BotFather, dán token + khóa vào `.env` trên VPS | ~2 tuần (a 3 ngày · b 5 ngày · c 2 ngày) |
| **3 (đang làm)** | Trợ lý theo từng người trên web | M-07 web chạy khóa cá nhân (nếu đại ca muốn, nay web = khóa công ty) · M-02 khóa kết nối MCP · P-02 trần chi phí theo người · P-01 đẩy thông báo ERP sang Telegram cá nhân · T-10 nhắc việc bằng câu nói · T-07 tin thoại | P-01: đẩy toàn bộ chuông hay chỉ «chờ bạn duyệt / việc giao cho bạn» | 2 tuần |
| **4** | Cổng MCP | M-01 cổng MCP dùng chung bộ tool · M-03 tool đọc · M-04 tool tạo/gửi duyệt có xác nhận · M-05 báo lỗi → Đậu Đậu | Thử với 1–2 người trước; chạy dev rồi prod | 2 tuần |
| **5** | Kết nối Google của từng người | M-06 Drive + Lịch riêng từng người → T-08 bản tin sáng, T-09 nhắc trước họp, T-11 tạo lịch bằng câu nói, R-03/R-04 phần Drive | Cá nhân hay Workspace công ty (Q2); đăng ký ứng dụng Google của công ty | 2 tuần |
| **6** | Nhiều kênh, nhiều bot | M-08 kênh Zalo OA · N-01 nhiều bot một nền · N-04 chi phí theo bot · N-05 cách ly khóa | Tạo bot/OA và đặt tên (Q6) | 1–2 tuần |
| **7** | Thư ký biên bản họp | T-01 thử một tệp họp thật (M0) → T-02 … T-06, T-12 | Cho ai dùng (Q1), một tệp ghi âm thật (Q5); chỉ làm tiếp khi M0 đạt | 3 tuần |
| sau | Để sau | A-08 xem thử qua tunnel (AN-007, 4 câu chờ) | — | — |

Phase 1 và 2 là nền cho mọi phase sau: 1 để mở cho nhiều người mà không lo ai đụng mã, 2 để bot
làm việc trên dữ liệu thật. Đại ca chốt 24/09/2026: **làm lần lượt**, không chạy song song nhiều phase
(đã cân phương án ba mạch A/B/C, bỏ vì ba luồng test dồn lên một người). Phase 3 → 6 mở dần theo hướng đại ca chốt: web trước, MCP, Google từng
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
