# 13 — Lộ trình bot trợ lý cá nhân «Lạc Lạc» và kiến trúc đích nhiều bot

> Bản 1.0 · 08/10/2026 · đối chiếu mã `agent-hub-bac-1` @ `3c228a7f` (đang chạy trên dev, erp-v2 đã gộp tới đây).
> Viết theo khuôn của `ida-zalo-assistant/doc/06-lo-trinh.md` (bot IDA) để hai bot nhìn cùng một kiểu, nhưng **hai
> bot là hai sản phẩm riêng**: IDA phục vụ một khách, Lạc Lạc là trợ lý cá nhân trên nền ERP. Chỉ mượn ý, không chung mã.
>
> Thay cho bảng «Lộ trình theo phase» ở cuối [`04-danh-sach-tinh-nang.md`](04-danh-sach-tinh-nang.md) (bảng đó dừng
> ở 05/10). Danh sách tính năng chi tiết từng mã (A, N, P, M, K, D, V, O, L, T, R, C) vẫn ở doc 04; doc này chỉ giữ
> **trạng thái theo phase**, **bộ chức năng của một trợ lý cá nhân**, **kiến trúc đích** và **việc kế tiếp**.
>
> **Cách đọc:** mỗi việc một trạng thái — **Xong** · **Một phần** · **Chưa** · **Chờ đại ca** · **Để sau**. Xong việc
> nào thì sửa đúng dòng đó và ghi ngày.

## 0. Đang ở đâu

| Phase | Nội dung | Trạng thái | Ghi chú |
|---|---|---|---|
| 0 | Bot sửa mã gốc (nhận việc, rà, sửa, kiểm, gộp, deploy dev) | **Xong** | ai-CR-001…050 |
| 1 | Khóa quyền sửa mã (K) | Một phần | K-01, K-04 xong; K-02 khóa riêng bot, K-03 bảo vệ `main`: tay đại ca trên GitHub |
| 2 | Bot lên dev, máy sửa mã tách rời (D) | **Xong** 25/09 | D-07 bot dev tự deploy để sau |
| 3 | Trợ lý từng người: chuông, nhắc, tin thoại, trần lượt (P, T-07…T-11) | **Xong** 25/09 | |
| 4 | Cổng MCP (M-01…M-05) | **Xong** 25/09 | chưa ai thử bằng ứng dụng thật |
| 5 | Google cá nhân (M-06) | **Xong** | đại ca đã nối Google trên dev |
| 6 | Quy trình code hai máy chủ (V) | Một phần | V-07 preview, V-08 VPS 2 thật chờ máy |
| 7 | Tự vận hành (O) | **Xong** 05/10 | O-01 còn thiếu đếm 5xx + hàng đợi |
| 7b | Trợ lý cá nhân: luật, sổ ghi nhớ, khóa AI nhiều hãng, thẻ cá nhân (C) | **Xong** 06–08/10 | ai-CR-093…110 |
| 8 | Lõi mở: MCP ngoài, A2A, ngân sách, sổ sự kiện (M-09, N-06…N-08) | **Chưa** | gắn với phase S bên dưới |
| 9 | Nhiều kênh: lớp kênh + bot Zalo chính thức (B1, Z-1, Z-2) | **Xong mã** 07/10 (ai-CR-111) | **Chờ đại ca**: token bot Zalo |
| 10 | Thư ký biên bản họp (T-01…T-06, T-12) | **Xong** 07–08/10 | ai-CR-104, 112, 113, 114, 116, 117; T-01 mới thử tệp giả |
| 11 | Đọc nhóm Telegram + đọc / viết báo cáo (G) | **Xong đợt 1** 07–08/10 | ai-CR-105, 115; đợt 2 ở §5 |
| **S** | **Tách dịch vụ AI thành nhiều bot nói chuyện với nhau (A2A)** — §3 | **Chưa** — chờ đại ca chốt §3.4 | |
| Z-3/Z-4 | Zalo hướng B: tài khoản riêng ghi lặng nhóm, đọc nhóm Zalo | **Chưa** | chờ tài khoản Zalo riêng |

**Một câu:** phần «trợ lý cá nhân hỏi gì đáp nấy» (ERP, sổ nhớ, khóa AI riêng, lịch, Drive, biên bản họp, đọc báo cáo,
tóm tắt nhóm Telegram) đã chạy thật trên dev cho mọi người đã đăng nhập; phần «bot tự theo dõi, tự báo» (tin quan trọng
trong nhóm, VIP, nhắc hạn việc rút từ họp) và phần **tách dịch vụ ra VPS riêng** chưa có — đó là hai hướng của §5.

## 1. Đã chốt (bổ sung từ 06/10/2026)

| Ngày | Quyết định | Ảnh hưởng |
|---|---|---|
| 06/10 | Bot là **trợ lý cá nhân** của từng người trên nền công ty, **token người dùng tự trả** (khóa riêng) | Nhóm C, mọi tính năng mới lọc theo người |
| 07/10 | Không làm tổng hợp nhóm tự động cuối ngày; chỉ tổng hợp khi được hỏi | §5 G |
| 07/10 | Zalo làm **cả A và B**; **không đụng** kho `ida-zalo-assistant`, chỉ mượn ý | Phase 9, Z-3/Z-4 |
| 07/10 | Xưng hô theo sổ ghi nhớ riêng từng người; «đại ca» chỉ cho chat chủ bot | ai-CR-106 |
| 07/10 | Tra mạng không phụ thuộc Google Search của Gemini (DuckDuckGo → Bing) | ai-CR-110 |
| 08/10 | Biên bản Word theo **chuẩn recap DEGO** (STD-RECAP-DEGO-v1.0, skill dego-docx); mẫu mặc định «Recap DEGO» | ai-CR-116 |
| 08/10 | Họp xong đưa tệp lên thư mục «Họp» trên Drive → bot **hỏi** rồi mới làm (không tự chạy, tốn khóa người đó) | ai-CR-116, 117 |
| 08/10 | **Tách phần AI thành dịch vụ riêng**, trước mắt cùng VPS nhưng Docker riêng, sau sang VPS riêng; kiến trúc **A2A nhiều bot** (§3) | Phase S |
| 08/10 | Kho tin nhắn / nhóm sẽ **rất lớn** (một người 50 nhóm, thêm khách hàng) → lưu trữ phải tách tầng (§4) | §4 |
| 08/10 | **Chưa** làm master/replica, **chưa** chia đọc/ghi; có số đo rồi mới quyết, và hướng mở rộng tự nhiên là **chia theo công ty** | §4 |

## 2. Bộ chức năng của MỘT trợ lý cá nhân

Đây là «một IDA thì cần bao nhiêu chức năng» nhìn từ phía Lạc Lạc: mọi thứ một người dùng cần ở trợ lý riêng, gom theo
nhóm, kèm trạng thái và đối chiếu với bot IDA (cột cuối: IDA **có** / **chưa** / **không cần**). Nhóm nào IDA có mà ta
chưa thì là ứng viên cho §5.

### 2.1 Kênh nhắn tin

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Telegram: chat riêng, tin thoại, ảnh, tệp, nút bấm | Xong | không (Zalo) |
| Zalo bot chính thức: chat riêng, đăng nhập bằng mã, cùng lõi | Xong mã, chờ token | có (tài khoản cá nhân) |
| Zalo tài khoản riêng ghi lặng nhóm (hướng B) | Chưa | có |
| Web (Trợ lý AI trong ERP), cổng MCP cho ứng dụng AI ngoài | Xong | có (web riêng) |
| Nhiều bot một nền, mỗi bot một token, cách ly khóa (N-01, N-05) | Chưa | có (nhiều tài khoản bot) |

### 2.2 Hỏi đáp và thao tác trên dữ liệu công ty (ERP)

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Hỏi số liệu ERP dưới đúng quyền của người hỏi (66 công cụ, lọc phạm vi) | Xong | chưa (nối ERP là giai đoạn sau) |
| Soạn nháp + tạo + gửi duyệt phiếu từ chat (YCMH, YCBG, nghỉ phép, phiếu hỗ trợ, việc Dự án) | Xong | không cần |
| Chuông ERP (phiếu chờ duyệt, việc được giao) đẩy sang chat | Xong | chưa |
| Sửa dữ liệu bằng lời qua cổng duyệt (ai-CR-073) | Xong | không cần |
| Lập bộ tài khoản bằng AI (CR-435) | Xong | không cần |

### 2.3 Sổ riêng của từng người

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Sổ ghi nhớ lõi + kho ghi chú có vector, dòng có hạn, tóm tắt cuối buổi, tìm lại hội thoại cũ | Xong | chưa |
| Thẻ cá nhân: lịch trình, chi tiêu, mua sắm | Xong | chưa |
| Khóa AI riêng nhiều hãng (Gemini, Claude, OpenAI, OpenRouter, DeepSeek, xAI, trạm tùy chỉnh), tự đổi khóa khi hỏng, trần ngày | Xong | có |
| Mẫu biên bản riêng lưu bằng lời | Xong | chưa |
| Cách xưng hô, nơi ở, sở thích lấy từ sổ | Xong | chưa |

### 2.4 Lịch, nhắc việc, bản tin

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Lịch Google cá nhân: xem, tạo, dời, hủy bằng câu nói | Xong | có (Meet) |
| Nhắc bằng câu nói; nhắc trước họp 15 phút | Xong | có (trong nhóm) |
| Bản tin 8h sáng: lịch, việc đến hạn, phiếu chờ duyệt, việc riêng | Xong | chưa (bản tin 07:30 / 17:30 chưa) |
| Bản tin cuối ngày | Chưa | chưa |
| Nhắc hạn việc rút từ biên bản / checklist 3 mốc (trước hạn, đúng hạn, quá hạn) | Chưa (việc Dự án có hạn, chưa nhắc 3 mốc) | chưa |
| Ô «Lịch hôm nay» trên Trang chủ ERP (T-13) | Để sau | không cần |

### 2.5 Thư ký họp

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Nhận ghi âm / video qua chat (≤ 20 MB), link Drive, thư mục «Họp» trên Drive (tự nhặt, hỏi trước) | Xong | có (Meet + ghi âm) |
| Chép lời Gemini File API, cắt đoạn, nối nhiều tệp một cuộc họp | Xong | có |
| 4 mẫu sẵn + mẫu riêng + lời dặn tại chỗ; viết lại theo mẫu khác không chép lời lại | Xong | một phần |
| Word chuẩn DEGO, đẩy vào thư mục «Biên bản họp» trên Drive; «report cuộc họp mới nhất» | Xong | có (PDF) |
| Thẻ việc + lịch hẹn rút từ biên bản → việc Dự án / thẻ cá nhân / lịch Google, duyệt rồi mới tạo | Xong | chưa (checklist phase 7) |
| Thử bằng tệp họp THẬT (ồn, nói chồng, giọng vùng miền) | Chờ đại ca | — |

### 2.6 Đọc và viết báo cáo, tệp

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Đọc pdf / Word / Excel / văn bản gửi riêng, trả lời theo câu hỏi (một lần, chi tiết); Excel tự tính công thức | Xong | có |
| Đọc tệp Drive (pdf / Word / Excel / Google Docs) | Xong | có (đọc link) |
| Xuất Word / Excel từ kết quả công cụ; biên bản Word DEGO | Xong | có (Excel / Sheets / PDF) |
| Tra mạng (không cần Gemini), kiểm chứng, tài liệu nội bộ | Xong | có (tìm web) |
| Khuôn báo cáo tuần / tháng tự gửi | Chưa | chưa (chờ form) |

### 2.7 Nhóm (Telegram nay, Zalo sau)

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Ghi lặng tin + tệp nhóm, chủ nhóm, quyền đọc theo thành viên, giữ 30 ngày | Xong | có (24 tháng, tệp 6 tháng) |
| Nhắn riêng nhờ tóm tắt nhóm / tệp trong nhóm / viết báo cáo | Xong | có |
| Tìm tin theo từ khóa + người + nhóm + ngày; xem tin trước / sau | Chưa (mới có tìm hội thoại riêng) | một phần |
| Tin quan trọng / khẩn / VIP / @nhắc tên → báo ngay, gộp 2 phút, trần số lần báo / ngày, giờ yên lặng | Chưa | chưa (phase 5 IDA) |
| Đồng hồ chờ: câu hỏi của khách chưa ai trả lời sau n giờ | Chưa | chưa |
| Gửi tin vào nhóm theo lệnh: xem trước → xác nhận → gửi, hẹn giờ | Chưa (bot không nói trong nhóm — chốt 07/10) | một phần |
| Nhãn Mật cho nhóm, che SĐT / STK trước khi gửi AI | Chưa | chưa |

### 2.8 Sửa mã và vận hành (chỉ chat chủ bot + người được cấp)

| Chức năng | Trạng thái | IDA |
|---|---|---|
| Gom việc, lập kế hoạch, rà soát, sửa, kiểm, gộp, deploy dev; máy sửa mã tách rời | Xong | không cần |
| Thao tác VPS có duyệt + sao lưu + hoàn tác; tự chẩn đoán và tự khôi phục; sổ sự cố | Xong | không cần |
| Bot **tự cập nhật chính nó** (deploy stack AI) | Chưa — cần phase S (§3.3) | không cần |

Đếm: **8 nhóm · 44 chức năng · 31 Xong · 2 Xong mã chờ bật · 1 Để sau · 10 Chưa.** Mười việc «Chưa» nằm gọn ở nhóm 2.7
(nhóm) và 2.4 (nhắc hạn, bản tin cuối ngày) — đúng chỗ IDA đang làm (phase 5–7 của IDA), nên §5 mượn lại thứ tự.

## 3. Kiến trúc đích: nhiều bot nói chuyện với nhau (A2A)

Đại ca 08/10: *"bot cá nhân ở VPS khác, bot phần dữ liệu công ty ERP ở VPS chính, bot code ở một chỗ khác, tin nhắn
ở một chỗ khác… để bot có thể tự cập nhật lại chính nó"*.

### 3.1 Bốn nút

| Nút | Làm gì | Giữ gì | Ở đâu (đích) |
|---|---|---|---|
| **A · Bot cá nhân** (Lạc Lạc) | Nhận tin Telegram / Zalo, sổ ghi nhớ, khóa AI riêng, thẻ cá nhân, lịch Google, biên bản họp, đọc tệp, tra mạng, gọi B khi cần số liệu công ty | Token Telegram / Zalo, khóa AI từng người (mã hóa), token Google từng người, Qdrant riêng | **VPS AI** (riêng) |
| **B · Bot dữ liệu công ty** (cổng ERP) | Mọi công cụ đọc / ghi ERP có lọc phạm vi, cổng MCP, Trợ lý AI trên web, chuông ERP | Khóa công ty, DB ERP; **không** giữ khóa cá nhân | **VPS chính** (cùng ERP) |
| **C · Bot code** (runner) | Sửa mã, kiểm, gộp, deploy dev; thao tác VPS có duyệt; tự chữa sự cố; **deploy cả A** | Claude Code, khóa GitHub, SSH đường hầm | Máy đại ca → VPS 2 khi có |
| **D · Kho tin nhắn** (ingest) | Nhận và lưu tin nhóm / tệp từ Telegram và Zalo (kể cả hướng B tài khoản riêng), dọn theo hạn, tìm toàn văn, cung cấp cho A tổng hợp | DB tin nhắn + kho tệp R2, tài khoản Zalo B | Cùng VPS AI lúc đầu, tách khi lớn |

Nguyên tắc giữ từ doc 04: **chia theo quyền**. Nút đọc nội dung lạ (D, phần tra mạng của A) không giữ khóa sửa mã;
nút giữ khóa công ty (B) không nhận tin lạ trực tiếp; nút sửa mã (C) không có token nhắn tin.

### 3.2 Nói chuyện với nhau

- A ↔ B: HTTP, **token ngắn hạn cấp theo từng người** (B phát hành khi người đó đăng nhập bằng mã; B là bên kiểm quyền,
  không tin A). Lượt gọi công cụ ERP = một yêu cầu A → B kèm token người đó. Đây là N-06 A2A: thẻ năng lực + giao việc +
  báo tiến độ + trả kết quả; dùng giao thức A2A chuẩn (Linux Foundation) thay hàng đợi tự viết.
- A ↔ D: HTTP nội bộ (cùng VPS) hoặc cùng DB lúc đầu; khi tách thì D cung cấp API «tin của nhóm X từ giờ Y» + tìm toàn văn.
- B/A → C: hàng đợi sửa mã như hiện nay (C kéo việc về qua đường hầm SSH); C deploy A bằng `deploy.sh` với **môi trường
  mới «agent»** trong sổ môi trường (V-01) — đó chính là «bot tự cập nhật chính nó».
- Sổ sự kiện chung (N-08): mọi bước của mọi nút một dòng cùng khuôn, để truy vết khi bốn nút ở bốn chỗ.

### 3.3 Đường đi (phase S)

| Bước | Việc | Cỡ | Điều kiện |
|---|---|---|---|
| S-0 | Viết hợp đồng API A ↔ B (danh sách công cụ, token theo người, mã lỗi), đo tải hiện tại (QPS DB, lượt model / ngày, dung lượng bảng) | 2 ngày | — |
| S-1 | **Stack AI riêng cùng VPS**: compose `agent-hub` (api-agent, worker, beat, poller, redis, qdrant), **DB riêng** cho bảng `tab_agent_*` + nhóm, `.env` riêng, deploy riêng (`deploy.sh agent`). Mã vẫn chung kho | 4 ngày | S-0 |
| S-2 | Lớp «cổng ERP» trong mã: hai cách chạy — gọi trực tiếp (như nay) và gọi HTTP qua B — chuyển **từng công cụ** sang HTTP, công cụ nào xong thì tắt đường trực tiếp | 8–10 ngày | S-1 |
| S-3 | Trợ lý AI trên web và cổng MCP chuyển sang gọi A (hoặc B giữ bản mình) | 2 ngày | S-2 |
| S-4 | Bot code deploy được stack AI (môi trường «agent» trong sổ V-01); O-01 theo dõi sức khỏe thêm nút A | 1 ngày | S-1 |
| S-5 | **Dời stack AI sang VPS riêng**: chép DB + Qdrant + R2 + token, đổi DNS, bật lại poller | 1 ngày | VPS mua xong |
| S-6 | Tách D (kho tin nhắn) khi số đo §4 chạm ngưỡng | 3 ngày | số đo |

Ước tổng **3–4 tuần công**, có thể xen kẽ với việc khác. S-1 làm được ngay sau khi đại ca chốt §3.4.

### 3.4 Chờ đại ca chốt

| Mã | Câu | Em đề xuất |
|---|---|---|
| S1 | S-1 tách DB riêng ngay (cùng MySQL, schema khác) hay dùng chung DB ERP tới S-5 | Tách ngay: dời sau tốn hơn, và bảng nhóm sẽ lớn |
| S2 | Thứ tự: phase S trước hay sau Zalo A (chỉ còn chờ token) và đợt lên prod đang giữ | Zalo A bật ngay khi có token (không tốn công); S-0 + S-1 làm trước đợt prod kế để prod nhận stack đã tách |
| S3 | Nút D ở cùng VPS AI lúc đầu (đề xuất) hay tách từ đầu | Cùng VPS AI, tách khi chạm ngưỡng §4 |
| S4 | VPS AI cấu hình đề xuất: 4 lõi, 8 GB RAM, 80 GB SSD + R2 cho tệp; worker ffmpeg + Qdrant ăn RAM nhiều nhất | — |

## 4. Lưu trữ: kho tin nhắn lớn thì làm gì

Số đại ca nêu: 100 người × 50 nhóm × 200 tin / ngày ≈ **1 triệu tin / ngày** (~1 GB chữ / ngày trước nén), chưa kể tệp.

| Tầng | Giữ gì | Ở đâu | Hạn |
|---|---|---|---|
| Nóng | Tin nhóm thô 30 ngày (như nay), tin riêng, trạng thái phiên | MySQL của nút D/A, bảng tin chia **partition theo tháng** | 30 ngày (nhóm), 24 tháng (riêng) |
| Ấm | Bản tổng hợp theo ngày / tuần của từng nhóm (do A viết khi được hỏi hoặc khi dọn) | MySQL + Qdrant (để hỏi «tháng trước nhóm X bàn gì») | 24 tháng |
| Lạnh | Tệp đính kèm, ghi âm gốc, Word đã xuất | **R2** (không nhét MySQL), chỉ lưu đường dẫn | 6 tháng tệp nhóm, biên bản giữ |

Luật: ghi tin nhóm theo **lô** (gom 1–2 giây rồi ghi một lần); chỉ số trên (nhóm, thời gian); vòng dọn hằng đêm chuyển
tin quá hạn thành tổng hợp rồi xóa thô; **đo** QPS, truy vấn chậm, kích thước bảng từ ngày đầu (S-0).

**Khi nào nâng:** máy trước (RAM cho bộ đệm) → **bản phụ chỉ cho báo cáo / sao lưu** khi đọc nặng (bot vẫn đọc máy chính,
tránh trễ bản phụ) → **chia theo công ty** khi có khách (mỗi công ty hoặc nhóm công ty một kho). Không chia đọc/ghi cho
đường bot: bot ghi rồi đọc liền, bản phụ trễ là thiếu tin.

## 5. Việc kế tiếp (sau phase S)

Thứ tự mượn từ IDA phase 5 → 7 (họ đã hỏi khách 27 câu, ta hưởng ké), nhưng giữ luật «bot không tự lên tiếng trong nhóm».

| Phase | Việc | Cỡ |
|---|---|---|
| G-2 | **Tin cần để ý trong nhóm**: từ khóa khẩn / quan trọng (so nguyên từ, đúng dấu), @nhắc tên, VIP trong danh bạ riêng từng người; báo riêng ngay, gộp 2 phút, trần số lần / ngày, giờ yên lặng theo sổ ghi nhớ | 1 tuần |
| G-3 | **Tìm tin nhóm**: chỉ mục toàn văn, công cụ tìm theo từ + người + nhóm + ngày, «xem tin trước / sau» | 3 ngày |
| G-4 | **Đồng hồ chờ**: câu hỏi của khách / của sếp chưa ai trả lời sau n giờ làm việc → nhắc người phụ trách | 2 ngày |
| T-14 | **Nhắc hạn 3 mốc** cho việc rút từ biên bản và thẻ cá nhân; bản tin cuối ngày | 2 ngày |
| Z-3/Z-4 | Zalo hướng B: tiến trình phụ ghi lặng nhóm Zalo → kho D; đọc nhóm Zalo qua 3 công cụ nhóm | 4 ngày |
| N-01/N-05 | Nhiều bot một nền (Thư ký, Nghiên cứu tách token), cách ly khóa | 3 ngày |
| M-07 | Khóa AI cá nhân cho Trợ lý trên web | 2 ngày |
| Prod | Đưa toàn bộ phase 7b–11 lên prod theo stack đã tách (S-1) — hiện prod đang giữ từ 19/09 | 1 ngày |
| Khách | Tách theo công ty (tenant) trên nút A và D khi có khách đầu tiên | sau |

## 6. Đang chờ

| Ai | Việc |
|---|---|
| Đại ca | Chốt S1–S4 (§3.4) |
| Đại ca | Token bot Zalo chính thức (Zalo Bot Manager → Tạo bot), gửi qua tệp |
| Đại ca | Một tệp họp THẬT để thử T-01 thật; thử đường Drive «Họp» với tệp ghi âm |
| Đại ca | VPS AI riêng (cấu hình S4); tài khoản Zalo riêng cho hướng B |
| Đại ca | K-02 / K-03 trên GitHub; bật OTP prod khi muốn |
