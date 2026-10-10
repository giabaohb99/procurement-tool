# AGENT HUB — DANH SÁCH TÍNH NĂNG CẦN LÀM

**Bản 1.0 · 24/09/2026.** Gom mọi việc còn lại của Đậu Đậu và các trợ lý mới đại ca muốn thêm
(biên bản họp, lịch và nhắc việc, nghiên cứu). Việc đã xong xem `change-log-ai.md`; thiết kế
bot sửa mã xem `01-thiet-ke-ky-thuat.md`; thiết kế biên bản họp gốc (28-29/08, chưa có mã) ở
`meeting-recap/doc/` trên máy.

**Tổng: 79 tính năng** (06/10/2026) — A 8 · N 8 · P 2 · M 9 · K 4 · D 7 · V 9 · O 6 · T 12 · R 4 · L 1 · C 6. **Đã xong 44** (05/10/2026): V-01 + V-02 + V-05 (ai-CR-067) · V-03 + V-06 (ai-CR-068) · O-01 … O-06 (ai-CR-069, O-01 một phần) · M-06 + T-08 + T-09 + T-11 (ai-CR-064) · M-01..M-05 (ai-CR-063) · T-10 (ai-CR-060) · T-07 (ai-CR-061) · P-02 (ai-CR-062) · P-01 (ai-CR-059) · D-06 (ai-CR-056) · D-04 (ai-CR-055) · D-03 + D-05 (ai-CR-054) · D-01 + D-02 (ai-CR-053) · K-01 + K-04 (ai-CR-051); A-01 … A-07 + N-02 (ai-CR-032 … 038) + R-01 … R-04 (ai-CR-044, phần Drive chờ N-03); A-08 vẫn chờ 4 câu của AN-007. Cỡ: **S** = một ngày trở xuống · **M** = hai
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
| N-03 | **Thay bằng M-06 (Google từng người, ai-CR-064).** Kết nối tài khoản Google một lần (Drive + Calendar), khóa lưu mã hóa | M | Chờ Q2 |
| N-04 | Chi phí theo từng bot, từng ngày, có trần ngày | S | |
| N-05 | Cách ly quyền: mỗi bot chỉ thấy khóa của nó | M | Bắt buộc trước khi bật bot Nghiên cứu |
| N-06 | Giao thức **A2A** (Agent2Agent, Google 2025, nay Linux Foundation) giữa các bot: thẻ giới thiệu năng lực, giao việc, báo tiến độ, trả kết quả — thay hàng đợi Redis tự viết khi có bot thứ ba, thứ tư | M | Thêm 05/10. Học từ các khung orchestrator–worker mở |
| N-07 | **Giao việc có tính ngân sách**: bot tổng xem còn bao nhiêu lượt Claude / Gemini trước khi giao; gần trần thì xếp hàng hoặc hạ model | S | Thêm 05/10 |
| N-08 | **Sổ sự kiện chung**: mọi bước của mọi bot một dòng cùng khuôn (ai, việc, bước, model, chi phí, kết quả) để truy vết và dựng lại khi sự cố | M | Thêm 05/10. Gom từ sổ tin + sổ lượt chạy đang có |

## Nhóm P — Phục vụ từng người đã đăng nhập (thêm 24/09/2026)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| P-01 | **XONG 25/09/2026 (ai-CR-059).** Đẩy thông báo ERP (chuông) sang Telegram của từng người đã đăng nhập: phiếu chờ họ duyệt, việc giao cho họ | M | Mặc định «việc của tôi», mỗi liên kết tự đổi (tắt / tất cả) bằng câu nhắn hoặc ở Trang cá nhân |
| P-02 | **XONG 25/09/2026 (ai-CR-062).** Trần lượt hỏi / chi phí theo từng người mỗi ngày | S | Để một người không dùng hết hạn mức Gemini của cả công ty |

## Nhóm M — Trợ lý mở: MCP, AI tự chọn, nhiều kênh (thêm 24/09/2026)

**Đại ca chốt 24/09/2026:** mỗi người **tự do chọn ứng dụng AI** và tự gắn khóa của mình (Claude,
ChatGPT, Gemini, Cursor…); hệ thống chỉ cung cấp công cụ. Đại ca chấp nhận rủi ro dữ liệu ERP đi sang
nhà cung cấp AI do từng người chọn. Làm trên **web trước**, rồi mở rộng kênh Telegram và Zalo dùng chung
lõi. Cổng MCP phải nằm trong backend ERP có tên miền thật (dev rồi prod), không đặt trên máy cá nhân.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| M-01 | **XONG 25/09/2026 (ai-CR-063).** Cổng MCP trên backend ERP (Streamable HTTP) — dùng CHUNG bộ tool với Trợ lý web và Telegram, không viết lại | L | Cần gộp phần bot vào `erp-v2` |
| M-02 | **XONG 25/09/2026 (ai-CR-063).** Khóa kết nối cá nhân lấy ở Trang cá nhân: có hạn, gỡ được, tách chỉ đọc / được ghi, nhật ký từng lượt gọi | M | Tool chạy đúng phạm vi dữ liệu của người đó. Phần khóa Gemini cá nhân cho kênh chat đã kéo lên phase 2 (D-01) |
| M-03 | **XONG 25/09/2026 (ai-CR-063).** Tool chỉ đọc qua MCP: tra số liệu, tình trạng phiếu, báo cáo | M | Bước thử đầu tiên, 1-2 người |
| M-04 | **XONG 25/09/2026 (ai-CR-063).** Tool tạo / gửi duyệt qua MCP, xác nhận hai bước phía server (dùng lại `draft_create`) | M | Đề nghị thanh toán chỉ trên web |
| M-05 | **XONG 25/09/2026 (ai-CR-063).** Tool báo lỗi qua MCP → phiếu hỗ trợ → Đậu Đậu | S | Duyệt / gộp vẫn theo nhóm K |
| M-06 | **XONG 25/09/2026 (ai-CR-064).** Mỗi người tự nối Google của mình (Drive, Lịch), tool lịch / Drive đọc dữ liệu của chính họ | L | Thay N-03 theo hướng từng người; khóa OAuth lưu mã hóa |
| M-07 | **Một phần 07/10/2026 (ai-CR-098): sổ khóa chung; web vẫn dùng khóa công ty — khóa cá nhân cho web chưa làm.** Trợ lý trên web chạy bằng AI + khóa do từng người chọn (khóa lưu mã hóa, chỉ người đó dùng) | M | Công ty thôi trả tiền model theo lượt. Đại ca chốt 24/09: trên dev, web vẫn dùng khóa công ty; D-01 chỉ cho kênh chat |
| M-08 | Kênh Zalo OA dùng chung lõi với Telegram | M | Zalo đẩy webhook: dùng tên miền ERP |
| M-09 | **Lõi gọi công cụ MCP bên ngoài**: đại ca nhắn «thêm công cụ X tại địa chỉ Y» → bot ghi sổ, các lượt sau model thấy và gọi được, không build lại. Dùng thư viện MCP client chính thức (`mcp` SDK) | M | Thêm 05/10. Đúng ý «lõi chung, cần gì đấu vào» |

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

## Nhóm V — Quy trình code hai máy chủ: bot tổng (VPS 1) giao, bot code (VPS 2) làm (chốt 05/10/2026)

Thiết kế đầy đủ và sơ đồ: [`07-quy-trinh-va-so-do.md`](./07-quy-trinh-va-so-do.md). Bot code dùng tài khoản Claude riêng của
công ty (gói ~$100); máy đại ca tạm đóng vai VPS 2 cho tới khi có máy thật.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| V-01 | **Sổ môi trường**: «thêm môi trường staging: vps …, nhánh …, lệnh deploy …» → bot tổng ghi, truyền cho bot code mỗi lần giao việc | S | **Xong** ai-CR-067 — bảng `tab_agent_env` (nạp sẵn dev + prod), «môi trường», «thêm môi trường …: dir= compose= branch= health=» · xem [`08`](./08-van-hanh-vps.md) |
| V-02 | **`deploy.sh <đích> <commit>` + nhật ký deploy**: đúng commit đã kiểm, ai ra lệnh, trước/sau, kết quả, log; «lịch sử deploy» | M | **Xong** ai-CR-067 — `backend/scripts/deploy/deploy.sh`: khóa lượt, commit phải trên nhánh của đích, health hỏng tự quay về; «deploy prod <sha>», «lịch sử deploy». Đường gộp cũ cũng đi qua nó. Khóa SSH khóa cứng một lệnh: CHƯA (máy sửa mã cần SSH đầy đủ cho V-03) |
| V-03 | **Bot code thao tác trên VPS 1 qua cổng duyệt**: xem dev tự do (MySQL chỉ đọc); xem prod / sửa dev cần «đúng»; thẻ hiện nguyên văn lệnh → sao lưu trước → chạy → nhật ký + lệnh hoàn tác; «hoàn tác thao tác #n» | M | **Xong** ai-CR-068 — `tab_agent_op`; SQL sửa sao lưu đúng bảng trước, deploy prod sao lưu cả DB; lan can lệnh/SQL + che bí mật |
| V-04 | **OTP cho mọi thay đổi prod**; lệnh lên prod phát từ VPS 1, không từ VPS 2 | S | **Tạm bỏ OTP** (đại ca 05/10). Lệnh prod hiện chạy từ máy sửa mã có cờ deploy; chuyển về VPS 1 khi có VPS 2 thật |
| V-05 | **Ba luật tự cải thiện**: bot code không sửa sổ quyền, phần OTP / lệnh prod, danh sách tệp cấm của chính nó | S | **Xong** ai-CR-067 — danh sách cấm dời sang `guardrails.py`, khóa `grants.py`, `runners.py`, `ops.py`, `ops_runner.py`, `scripts/deploy/*`, `guardrails.py` |
| V-06 | **Báo tài nguyên hằng ngày**: RAM / CPU / đĩa từng máy, số việc, lượt Claude/Gemini, việc kẹt; «tình hình máy» | S | **Xong** ai-CR-068 — 07:35 mỗi sáng + «tình hình máy» |
| V-07 | **Preview đầy đủ từng việc**: be + fe + worker + redis + MySQL + qdrant riêng, dữ liệu tự seed, `ai-xxxx.preview.<tên miền>` qua Cloudflare Tunnel; 1 bộ một lúc trên máy hiện tại, 2–3 trên VPS preview 16 GB; tự tắt sau 24 giờ | L | Chờ tên miền + token tunnel |
| V-08 | **Chuyển bot code sang VPS 2 thật** khi mua máy (cài theo `05`, đổi tên máy trong sổ) | S | Chờ VPS + tài khoản Claude công ty |
| V-09 | Chép DB dev sang preview để test với dữ liệu thật | M | **Để sau** (đại ca 05/10) |

## Nhóm O — Tự vận hành: AI tự phát hiện sự cố và khôi phục (thêm 05/10/2026)

«Agentic»: bot tự hành động nhiều bước — thấy server có vấn đề thì tự tìm lỗi, khôi phục trong giới hạn được phép, rồi báo.
Dựa trên V-02 / V-03 / V-06 (nhật ký, cổng duyệt, sao lưu, hoàn tác).

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| O-01 | **Theo dõi sức khỏe** mỗi phút: api dev / prod trả 200, container chạy đủ, đĩa, RAM, hàng đợi, lỗi 5xx tăng đột biến | S | **Xong một phần** ai-CR-069 — health mỗi phút, 3 lượt hỏng liền mở sự cố; container/đĩa/RAM xem lúc chẩn đoán + báo sáng; CHƯA đếm 5xx, chưa canh hàng đợi |
| O-02 | **Tự chẩn đoán**: có sự cố thì gom log container, `docker ps`, migration hiện tại, commit vừa deploy → bot code (Claude) đọc và viết chẩn đoán ngắn: nguyên nhân khả dĩ + cách sửa đề xuất | M | **Xong** ai-CR-069 — Claude không trả lời được thì luật dự phòng |
| O-03 | **Tự khôi phục trên dev** trong danh sách thao tác an toàn: khởi động lại container, dọn bộ đệm, chạy lại migration đang dở, quay về commit trước nếu lỗi do lần deploy vừa rồi. Trần 3 lần / giờ, quá trần thì dừng và gọi người | M | **Xong** ai-CR-069 — 4 thao tác an toàn; «chạy lại migration» = khởi động lại api (start.prod.sh tự upgrade). Công tắc `AGENT_HEAL_ENABLED` |
| O-04 | **Prod: chỉ đề xuất**, đại ca «đúng» + OTP mới chạy (dùng V-03 / V-04) | S | **Xong** ai-CR-069 (chưa OTP) |
| O-05 | **Sổ sự cố** tự viết: lúc nào, triệu chứng, chẩn đoán, đã làm gì, kết quả, thời gian gián đoạn | S | **Xong** ai-CR-069 — `tab_agent_incident`, «sự cố» |
| O-06 | **Sự cố lặp lại** → bot đề xuất một việc sửa mã gốc rễ (giao bot code như mọi việc) | S | **Xong** ai-CR-069 — cùng nguyên nhân 3 lần / 7 ngày → việc nguồn «Sự cố lặp lại» |

## Nhóm L — Đối chiếu và học hỏi bên ngoài (thêm 05/10/2026)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| L-01 | Định kỳ đối chiếu hệ thống với các khung orchestrator–worker mở (mcp-agent, Agent Swarm, cli-agent-orchestrator, OpenAI Agents SDK); chỉ **học ý tưởng**, không clone thay lõi; mượn thư viện từng phần chỉ từ kho MIT / Apache, ghi nguồn; **tránh AGPL** | S | Bảng đối chiếu ở `07` §6 |

## Nhóm T — Thư ký (biên bản họp, lịch, nhắc việc)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| T-01 | **Thử bằng tệp giả 07/10/2026 (ai-CR-112): qua — chép lời đúng gần như nguyên văn, đoán đúng tên người nói; còn chờ một tệp họp thật (nhiều tiếng ồn, nói chồng).** **Thử trước (M0):** chạy một tệp họp thật qua Gemini ra biên bản, đo chất lượng và chi phí | S | Chốt chặn: không qua thì dừng cụm biên bản. Chờ Q1, Q5 |
| T-02 | **XONG 08/10/2026 (ai-CR-116):** vòng 5 phút tìm tệp mới trong thư mục «Họp» trên Drive của từng người → HỎI «làm biên bản» (gộp nhiều tệp nối theo giờ) / «làm tệp 2» / «bỏ qua»; «report cuộc họp mới nhất» tự làm tệp mới hoặc gửi lại biên bản + Word + thẻ việc. Đọc thư mục ghi âm trên Drive, gom nhiều tệp của một cuộc họp thành một phiên | M | Tệp họp dài không gửi qua bot được, phải qua Drive |
| T-03 | **XONG 07/10/2026 (ai-CR-104).** Chuẩn hóa và cắt âm thanh dài cho vừa model | M | |
| T-04 | **XONG 07/10/2026 (ai-CR-104), một tệp / phiên; gộp nhiều tệp một cuộc họp còn ở T-02.** Gỡ băng từng tệp, nối theo thứ tự thời gian | M | |
| T-05 | **XONG 07/10/2026 (ai-CR-112):** 4 mẫu sẵn + mẫu RIÊNG từng người lưu bằng lời («lưu mẫu biên bản …»), lời dặn tại chỗ («theo mẫu: …»), viết lại cuộc họp cũ theo mẫu khác không chép lời lại; Word mẫu DEGO vào thư mục «Biên bản họp» trên Drive. Mẫu biên bản là dữ liệu (chính thức · gạch đầu dòng · danh sách việc · đầy đủ theo giờ), chọn mẫu bằng chữ | M | Thêm mẫu không phải sửa mã |
| T-06 | **XONG 07/10/2026 (ai-CR-104).** Xuất Word lên Drive, gửi bản tóm tắt ngay trong chat kèm link | M | |
| T-07 | **XONG 25/09/2026 (ai-CR-061).** Tin thoại ngắn thành lời nhắc hoặc việc | S | Cần N-02 |
| T-08 | **XONG 25/09/2026 (ai-CR-064); bật / tắt trong chat DEV 09/10/2026 (ai-CR-140).** Bản tin sáng: lịch hôm nay, việc riêng, việc Dự án tới hạn / quá hạn (tool mới `my_work_tasks`), phiếu chờ duyệt — không còn đòi nối Google. Mỗi người tự «bật bản tin», «bản tin lúc 6h45 ngày thường», «bản tin hôm nay», «tắt bản tin 2»; bản tin CHỦ ĐỀ («sáng thứ hai gửi anh công nợ quá hạn của DEGO») qua tool `manage_briefs`; nút «Bật» trên đề xuất 13.5 và thẻ «Bản tin bot tự gửi» ở tab «Bot nhớ gì về tôi». Vòng 5 phút thay lịch cứng 07:30 | M | — |
| T-09 | **XONG 25/09/2026 (ai-CR-064).** Nhắc trước mỗi cuộc họp 15 phút | S | Cần N-03 |
| T-10 | **XONG 25/09/2026 (ai-CR-060).** «Nhắc anh 3h gọi nhà cung cấp X»: tạo lời nhắc bằng câu nói | S | Dùng bộ hẹn giờ và phần hiểu giờ sẵn có |
| T-11 | **XONG 25/09/2026 (ai-CR-064).** Tạo lịch Google Calendar bằng câu nói, hỏi lại trước khi tạo. Dời / đổi tên lịch đã có: `update_calendar_event` (ai-CR-084). **Hủy** lịch đã có: `delete_calendar_event` (AI-0003, 06/10/2026) — khớp không đúng một sự kiện thì hỏi lại, lịch lặp lại chỉ hủy buổi của ngày đó, có khách mời thì Google gửi thư báo hủy | S | Cần N-03 |
| T-12 | **XONG 07/10/2026 (ai-CR-114):** biên bản xong → một thẻ việc + lịch hẹn đánh số; «tạo hết» / «tạo 1 3 dự án 2» / «bỏ»; việc vào phân hệ Dự án (gán người khi khớp đúng một nhân sự), không có dự án thì thẻ cá nhân; lịch vào Google Calendar, chưa nối Google thì thẻ cá nhân. Việc rút ra từ biên bản thành lời nhắc và việc trong phân hệ Công việc của ERP | M | Chỗ hai cụm cộng lại đáng giá nhất |
| T-13 | Ô **«Lịch hôm nay»** trên Trang chủ ERP v2: sự kiện trong ngày từ Google của từng người + việc ở phân hệ Dự án đến hạn hôm nay; chưa nối Google thì hiện nút «Nối Google» | M | **Để sau** — đại ca dặn note lại 05/10/2026. Lịch hiện xem qua Google Calendar, Telegram («lịch hôm nay»), Trợ lý web, bản tin 7:30 |

## Nhóm C — Trợ lý cá nhân trên nền công ty, token người dùng tự trả (thêm 06/10/2026)

**Đại ca nhắc 06/10/2026:** định hướng là **AI trợ lý cá nhân** cho từng người, chạy trên nền tảng của công ty (sổ,
công cụ ERP, Google cá nhân), **token người dùng tự trả** (khóa riêng, D-01). Bot hôm đó còn hành xử như trợ lý ERP:
hỏi «lên lịch trình ăn + đi lại» thì nói chưa có công cụ rồi gạ tạo phiếu hỗ trợ gửi Hành chính / Nhân sự; hỏi «chỗ
ăn chiều» thì gợi ý trộn TP.HCM với Hà Nội vì không biết người hỏi ở đâu.

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| C-01 | **XONG 06/10/2026 (ai-CR-093, ai-CR-094).** Luật trợ lý cá nhân: việc bằng chữ (lịch trình, kế hoạch, gợi ý, soạn thảo, tư vấn) làm ngay không đòi công cụ; không gạ phiếu ERP cho nhu cầu cá nhân; câu cần nơi đang ở mà chưa biết thì hỏi một câu | S | |
| C-02 | **XONG đợt 1, 06/10/2026 (ai-CR-095).** Hai tầng theo khung Letta: LÕI (`tab_agent_memory`, mỗi người một dòng Markdown bốn mục, trần 8.000 ký tự, nạp mọi câu hỏi, bộ đệm 10 phút) + KHO (`tab_agent_note` + vector `agent_personal` lọc `user_id`, lấy 5 đoạn liên quan). Lệnh «nhớ: …» · «quên: …» · «ghi chú: tiêu đề \| nội dung» · «sổ nhớ» · «xuất sổ nhớ»; bot tự ghi qua `remember_fact` và báo «Em ghi nhớ: …». Không ghi bí mật. **Đợt 2 XONG 07/10/2026 (ai-CR-102):** tóm tắt cuối buổi (im lặng 30 phút, vòng nền 10 phút, cất vào kho, không nhắn), hồi ức `search_chat_history` (56 tool), dòng có hạn «nhớ tuần này / đến 15/10: …» + `remember_fact.until`. ~~**Sổ ghi nhớ riêng từng người**~~: khu hay ở, gia đình, thói quen, sở thích, cách xưng hô, điều đã chốt. Mọi lượt trả lời đọc sổ trước; người dùng dạy bằng «nhớ: …», xem «sổ nhớ», quên bằng «quên: …». Bot tự đề nghị ghi khi bị sửa lưng | M | Lưu theo user_id (tab_setting như sổ thuật ngữ), mã hóa phần nhạy cảm; KHÔNG dùng chung giữa người |
| C-03 | **BỎ 06/10/2026 (đại ca: lấy khu trong sổ ghi nhớ).** **Vị trí**: đọc tin «gửi vị trí» của Telegram, nhớ vài giờ; gợi ý quanh đó kèm khoảng cách; không có thì dùng khu quen trong C-02 | S | Cần C-02 cho khu quen |
| C-04 | **XONG 07/10/2026 (ai-CR-098).** Sổ khóa MỘT bảng `tab_ai_key` cho công ty (`owner_type` 1) lẫn cá nhân (2): Gemini · Claude · OpenAI · OpenRouter, `priority` (1 = chính), `model`, `daily_cap` riêng (đếm qua `tab_agent_run.key_id`). Bot dùng chuỗi cá nhân → công ty (→ `.env` chỉ cho chat đại ca); khóa hết tiền / hạn mức / sai thì tự nhảy khóa kế, KHÔNG nhắn (đại ca chốt); hỏi «còn khóa nào» thì liệt kê + lượt hôm nay. Màn: Trang cá nhân → Khóa AI (nhiều dòng, đổi ưu tiên, model, trần) + Cấu hình hệ thống → Trợ lý AI (khóa công ty). Adapter mới `openai_compat.py`. Tìm Google và nhúng vector vẫn cần một khóa Gemini trong chuỗi. ~~**Khóa riêng mọi nhà cung cấp**~~: ngoài Gemini (D-01), người dùng gắn khóa Claude / OpenAI của mình cho kênh chat và web; công ty không trả token thay | M | Gộp M-07; trần P-02 giữ cho người chưa gắn khóa |
| C-05 | **XONG 07/10/2026 (ai-CR-103).** Bảng `tab_agent_personal_item` (kind 1 lịch trình · 2 chi tiêu · 3 mua sắm; status còn / xong / đã bỏ), 3 tool `add_personal_item` · `list_personal_items` (chi tiêu có tổng + theo nhóm) · `mark_personal_item` (59 tool), lọc cứng theo người gọi, không có đường xóa; bản tin sáng có mục «Việc riêng». Màn web để sau. ~~**Thẻ cá nhân**: lịch trình, nhắc việc, chi tiêu cá nhân, danh sách mua sắm — lưu riêng từng người, không vào dữ liệu ERP | M | Nhắc việc T-10 đã có, mở rộng cho dữ liệu riêng |
| C-06 | **XONG 06/10/2026 (ai-CR-095).** Bộ phân loại ý định gán `scope` (1 công ty · 2 cá nhân) lên `tab_agent_message`, câu trả lời và câu nối tiếp kế thừa; việc sửa mã / sửa dữ liệu / thao tác luôn là công ty. ~~**Chế độ**: cùng một bot nhận biết~~ câu nào là việc công ty (ERP, dữ liệu, sửa mã) và câu nào là việc cá nhân; việc cá nhân không đi qua cổng duyệt ERP, không ghi sổ công ty | S | Dựa trên intent sẵn có |
| C-07 | **ĐỢT A XONG + DEV 09/10/2026 (ai-CR-137, phase 13.1–13.3).** Hiểu ý định + tự ghi nhớ: sổ ý định `tab_agent_intent` (một dòng mỗi câu hỏi, KHÔNG nguyên văn — nhãn lớn, nhãn con tất định theo công cụ như `tra_cuu.cong_no` / `thao_tac.tao_ycmh`, đối tượng từ tham số định danh, công cụ, kết cục; giữ 180 ngày) + tự rút ghi nhớ sau buổi chat riêng (`tab_agent_memory_candidate`; ≥ 3 lần trên ≥ 2 ngày mới ghi vào lõi với đuôi «(tự rút)», hết hạn nếu không gặp lại, «quên» thành bia mộ 90 ngày, không đọc nhóm, báo người dùng một lần). **Đợt B XONG + DEV 09/10/2026 (ai-CR-138):** 13.4 tab «Bot nhớ gì về tôi» ở Trang cá nhân (chỉ chủ sổ; sửa / xóa từng dòng, bỏ điều đang để ý, xóa toàn bộ; thu hồi tài khoản xóa sạch) · 13.5 thói quen đối tượng (≥ 3 lần, ≥ 60%) vào phần luật + nói rõ giả định, đề xuất chủ động chỉ hiển thị · 13.6 bộ câu mẫu cố định + script `intent_eval.py` (xuất gắn nhãn tay, chấm, tỷ lệ hỏi lại). Lôgic đầy đủ: [`17-tri-nho-va-y-dinh.md`](17-tri-nho-va-y-dinh.md) | M | Nút bật bản tin theo đề xuất: chờ đại ca |

## Nhóm R — Nghiên cứu (research, tìm tài liệu, kiểm chứng)

| Mã | Tính năng | Cỡ | Ghi chú |
|---|---|---|---|
| R-01 | Research một chủ đề: Gemini tìm Google, trả bản tóm tắt kèm nguồn | S | **Xong** ai-CR-044 (`/tim`); lượt tìm không có công cụ tác động nên chưa cần N-05 |
| R-02 | Kiểm chứng một nhận định: đúng · sai · chưa đủ căn cứ, kèm nguồn | S | **Xong** ai-CR-044 (`/kiemchung`) |
| R-03 | Tìm tài liệu nội bộ: kho tài liệu đã nạp + thư mục Drive | M | **Xong phần kho tài liệu** ai-CR-044 (`/tailieu`); phần Drive chờ N-03 |
| R-04 | Xuất báo cáo nghiên cứu ra Word lên Drive | S | **Xong phần Word gửi qua Telegram** ai-CR-044 (`/word`); lên Drive chờ N-03 |

## Nhóm G — Phiếu qua bot và dây chuyền sửa mã gọn (09-10/10/2026)

Tiến độ đợt 09-10/10/2026. Mọi dòng dưới đây đã **lên DEV**, prod chưa (đang tạm dừng deploy prod).

| Mã | Tính năng | Trạng thái |
|---|---|---|
| G-01 | Tạo phiếu nháp hỏi lại khi thiếu ý quan trọng; điều bot tự hiểu ghi riêng trên thẻ để xác nhận; bỏ ký tự « » trong tin bot | XONG DEV (ai-CR-142) |
| G-02 | Phiếu nháp của tôi, xóa phiếu nháp qua chat; đơn nghỉ trùng ngày tự sửa đè đơn nháp cũ | XONG DEV (ai-CR-143) |
| G-03 | YCMH / YCBG dùng lại phiếu nháp cũ: *thêm vào N* (gộp dòng, bỏ dòng trùng), *ghi đè N* (giữ mã) | XONG DEV (ai-CR-156) |
| G-04 | Sửa phiếu Nháp / Bị trả lại qua thẻ cũ → mới: đơn nghỉ (ngày, loại nghỉ, lý do), dòng hàng YCMH / YCBG; xóa phiếu nháp của mình (YCMH, YCBG, đơn nghỉ, việc Dự án) | XONG DEV (AI-0006 gom tay vào ai-CR-151) |
| G-05 | Nút xác nhận sửa / xóa trên Telegram đi qua cổng ERP; mỗi thẻ chỉ dùng một lần; chỉ sửa lý do thì giữ số ngày nghỉ | XONG DEV (ai-CR-152, ai-CR-153) |
| G-06 | Hướng dẫn bot tách nhóm *phiếu* / *sửa phiếu*; câu *quyền của tôi* trả bảng chức năng theo ma trận quyền ERP; bot gợi ý khi thiếu quyền | XONG DEV (ai-CR-157) |
| G-07 | Dây chuyền sửa mã gọn: Claude Code rà mã → thẻ xác nhận (em hiểu việc, *xong thì làm được gì*, rủi ro) → *ok* | XONG DEV (ai-CR-149, ai-CR-153) |
| G-08 | Câu giục *sửa nó đi* sau thẻ / chi tiết là giao làm luôn; bỏ luật dừng lệch 30% tệp | XONG DEV (ai-CR-150, ai-CR-151) |
| G-09 | Canh ranh giới bot / ERP: luật C11 + bài kiểm đọc mã; cổng kiểm tự chạy bài tách dịch vụ khi đụng bot | XONG DEV (ai-CR-153) |
| G-10 | *ok* trên thẻ = đồng ý luôn gộp + đưa lên dev khi bài kiểm không đỏ; prod không bao giờ tự đẩy | XONG DEV (ai-CR-154) |
| G-11 | Đưa lên dev dựng lại cả cụm bot khi bản sửa đụng mã bot (chờ việc dở, khóa chống đè, tự quay về) | XONG DEV (ai-CR-155) |
| G-12 | Lọc thẻ suy nghĩ `<thinking>` của model khỏi câu trả lời | XONG DEV (ai-CR-151) |
| G-15 | Hỏi chi phí token của một biên bản họp: từng bước chép lời / viết biên bản / rút việc | XONG DEV (ai-CR-158) |
| G-16 | Biên bản họp không bịa từ tệp không có tiếng; báo lỗi từng bước, tự thử lại, lệnh thử lại biên bản | XONG DEV (ai-CR-162) |
| G-17 | Biên bản sạch chữ thừa, tóm hai tầng khi họp dài, thẻ Ai là ai, bản chép lời .txt riêng | XONG DEV (ai-CR-164) |
| G-18 | Phase 22: đọc video YouTube công khai thành biên bản / tóm tắt (Gemini theo link, không tải video) + ước tính chi phí trước cho mọi tệp họp, từ 1 USD hoặc dài hơn 2 giờ thì hỏi ok | Chờ dev (ai-CR-163) |
| G-13 | Bài Help Center cho phần sửa / xóa phiếu, dùng lại nháp, xem quyền | XONG DEV (ai-CR-159, bài id 112) |
| G-14 | Dùng Claude Sonnet cho việc sửa mã nhỏ; cảnh báo khi máy sửa mã chạy bản cũ | Đại ca gác lại 09/10 |

## Lộ trình theo phase (viết lại 05/10/2026)

> **Bảng này dừng ở 05/10/2026.** Trạng thái mới nhất, kiến trúc đích A2A và việc kế tiếp xem [`13-lo-trinh.md`](13-lo-trinh.md).

Cỡ là ước THÔ theo ngày công của một người. Làm **lần lượt** (đại ca chốt 24/09).

| Phase | Tên | Gồm | Trạng thái / cần đại ca | Cỡ ước |
|---|---|---|---|---|
| 0 | Bot sửa mã gốc | Nhận việc, rà, sửa, kiểm, gộp, deploy dev; đăng nhập bằng mã; tạo + gửi duyệt phiếu; nghiên cứu; chi phí | Xong | — |
| 1 | Khóa quyền sửa mã | K-01, K-04 xong · K-02 khóa riêng của bot · K-03 bảo vệ `main` | Còn K-02/K-03: tay đại ca trên GitHub | — |
| 2 | Bot lên dev | Nhóm D: Lạc Lạc, khóa cá nhân, máy sửa mã tách rời, đường tắt, model theo làn | Xong 25/09 | — |
| 3 | Trợ lý từng người | Chuông, nhắc việc, tin thoại, trần lượt | Xong 25/09 | — |
| 4 | Cổng MCP | M-01..M-05 | Xong 25/09, chưa ai thử bằng ứng dụng thật | — |
| 5 | Google cá nhân | M-06, T-08, T-09, T-11 | Mã xong; **chờ đại ca**: redirect URI, «In production», bật Calendar + Drive API, `GOOGLE_CLIENT_SECRET` | — |
| **6** | **Quy trình code hai máy chủ** (nhóm V) | (a) V-01 + V-02 + V-03 · (b) V-04 + V-05 + V-06 · (c) V-07 preview · V-08 khi có VPS | (a) + V-05 + V-06 **xong 05/10** (ai-CR-067/068); V-04 tạm bỏ OTP. Còn V-07 chờ tên miền + token tunnel; V-08 chờ VPS + tài khoản Claude công ty | ~2 tuần (a 3 ngày · b 1–2 ngày · c 3 ngày) |
| **7** | **Tự vận hành** (nhóm O) | O-01 → O-06 | **Xong 05/10** (ai-CR-069); O-01 còn thiếu đếm 5xx + hàng đợi | ~1 tuần |
| **7b** | **Trợ lý cá nhân** (nhóm C) | C-01 · C-02 · C-04 · C-05 · C-06 **xong 06–07/10** (C-03 bỏ) | C-03 vị trí **bỏ** (đại ca 06/10: lấy khu trong sổ nhớ); đợt 2 + C-04/C-05 chờ đại ca | ~1,5 tuần (C-02+C-03+C-06 4 ngày · C-04 2 ngày · C-05 3 ngày) |
| **8** | **Lõi mở** | M-09 gọi MCP bên ngoài · N-06 A2A · N-07 giao việc tính ngân sách · N-08 sổ sự kiện chung · L-01 | — | ~1,5 tuần |
| 9 | Nhiều kênh, nhiều bot | M-08 Zalo OA · N-01 · N-04 · N-05 | Chờ Zalo OA + tên bot (Q6) | 1–2 tuần |
| 10 | Thư ký biên bản họp | T-01 thử tệp thật → T-02..T-06, T-12 — kế hoạch chi tiết `11-ke-hoach-bien-ban-hop.md` (07/10) | Chờ Q1 · Q5 · Q7 · Q8 · Q9 | ~10 ngày công |
| sau | Để sau | V-09 chép DB dev sang preview · A-08 xem thử qua tunnel cũ (thay bằng V-07) | — | — |

Vì sao thứ tự này: phase 6 là nền cho mọi đường lên dev/prod sau này và là thứ đại ca đang cần; phase 7 dùng lại
đúng nhật ký, cổng duyệt, sao lưu, hoàn tác của phase 6 nên làm ngay sau thì rẻ; phase 8 cần khi có bot thứ ba trở đi;
phase 9, 10 chờ dữ liệu từ đại ca nên đặt cuối, có dữ liệu sớm thì kéo lên.

**Năng lực:** đội làm được khoảng 24 ngày công mỗi tháng; trợ lý là việc cộng thêm, giành giờ với ERP. Phase 6 → 8
khoảng 4,5 tuần công.

## Câu chờ đại ca

| Mã | Câu | Chặn |
|---|---|---|
| Q1 | Biên bản họp làm cho đại ca dùng, hay cho CEO như yêu cầu gốc (bản gốc: chạy trên máy riêng của CEO, chỉ CEO thao tác) | T-01 … T-06 |
| Q2 | Nối tài khoản Google nào: cá nhân hay Google Workspace công ty | N-03 |
| Q3 | ~~Nhánh `bot/*` xóa lúc gộp hay lúc «xong»~~ — em chọn lúc việc đóng (ai-CR-033), đại ca đổi thì báo | — |
| Q4 | ~~Cổng kiểm v1~~ — em chọn chặn lỗi kiểu trong tệp bot sửa (ai-CR-034; `frontend/` không có eslint) | — |
| Q5 | Một tệp ghi âm họp thật để thử (đặt vào thư mục trên máy, không gửi qua chat) | T-01 |
| Q6 | Tên cho bot Thư ký và bot Nghiên cứu | N-01 |
