# KẾ HOẠCH PHÂN HỆ CRM — CHĂM SÓC KHÁCH HÀNG ĐA KÊNH

| | |
|---|---|
| Bản | 1.0 — 02/11/2026 (kế hoạch, **chưa làm**) |
| Nhu cầu | Một chỗ gom tin nhắn **Zalo, Telegram**; **quản lý tài khoản và đội CSKH**; **gọi điện thoại** qua tổng đài, nhiều người dùng chung một số, cước trừ một tài khoản |
| Tham khảo | ERPNext 16 trên site học (danh sách thật ở mục 2.1), Frappe CRM (app riêng của cùng hãng, theo tài liệu hãng, **chưa cài thử**) |

---

## 1. Kết luận ngắn

- **Nên làm CRM trong ERP của mình**, không dùng ERPNext: phần khó nhất (lớp kênh Zalo, Telegram, trợ lý AI, phân quyền, chuông báo) **mình đã có sẵn** ở dịch vụ AI; ERPNext chỉ có sẵn tích hợp Twilio, Exotel (không cấp được đầu số Việt Nam) và không có Zalo.
- Làm **theo lõi CSKH trước, bán hàng sau**: Khách hàng → Hộp thư hợp nhất → Đội CSKH và phân công → Tổng đài → Phiếu khiếu nại + báo cáo. Phễu bán hàng (khách tiềm năng, cơ hội, báo giá) để giai đoạn cuối vì ERP chưa có phân hệ bán hàng.
- Ước lượng phần lõi (GĐ1–GĐ4): **khoảng 14–18 người-tuần**, chưa tính thời gian chờ nhà cung cấp tổng đài và Zalo OA.

---

## 2. ERPNext có gì (để tham khảo)

### 2.1. Danh sách thật trên site học (ERPNext 16.53)

| Phân hệ | Chứng từ / danh mục | Báo cáo có sẵn |
|---|---|---|
| **CRM** | Khách tiềm năng (Lead), Cơ hội (Opportunity), Khách triển vọng (Prospect), Chiến dịch (Campaign), Chiến dịch email, Lịch hẹn + cài đặt đặt lịch, Hợp đồng + mẫu hợp đồng, Giai đoạn bán hàng, Loại cơ hội, Lý do mất cơ hội, Đối thủ, Phân khúc thị trường, Cài đặt CRM | Hiệu quả chiến dịch; Thời gian phản hồi đầu cho cơ hội; Thời gian chuyển đổi khách tiềm năng; Chi tiết khách tiềm năng; Hiệu suất người phụ trách; Cơ hội bị mất; Cơ hội theo giai đoạn; Khách triển vọng chưa chuyển đổi; Phân tích phễu bán hàng |
| **Bán hàng** | Khách hàng, Báo giá, Đơn bán, Gói sản phẩm, Mặt hàng riêng theo khách, Ngành nghề, Loại đối tác bán hàng, Phiếu lắp đặt, Trung tâm SMS | Khách mới và khách trung thành; Công nợ khách; Giá theo khách; Khách không phát sinh giao dịch; Khách ngưng hoạt động; Lịch sử bán theo mặt hàng; Báo giá bị mất; Xu hướng báo giá / đơn bán; Doanh số theo nhân viên, đối tác, khu vực; Hoa hồng |
| **Hỗ trợ** | Phiếu hỗ trợ (Issue), Mức ưu tiên, Loại phiếu, Cam kết mức dịch vụ (SLA), Yêu cầu bảo hành | Thời gian phản hồi đầu; Phân tích phiếu; Tổng hợp phiếu; Phân bố giờ hỗ trợ |
| **Điện thoại** | Nhật ký cuộc gọi (Call Log), Cài đặt cuộc gọi đến, Loại cuộc gọi, Cài đặt gọi thoại | — |

### 2.2. Frappe CRM (app riêng, giao diện mới)

Theo tài liệu hãng: khách tiềm năng và thương vụ dạng bảng Kanban, liên hệ, tổ chức, ghi chú, việc cần làm, nhật ký cuộc gọi, hộp thư email, WhatsApp (qua app Frappe WhatsApp), tổng đài Twilio / Exotel, SLA, luật tự phân công, trường và màn tùy biến, nối sang khách hàng / báo giá / đơn bán của ERPNext. **Không có Zalo, không có Telegram, không có tổng đài Việt Nam.**

### 2.3. Lấy gì, bỏ gì

| Lấy ý tưởng | Lý do |
|---|---|
| Tách **Khách tiềm năng → Khách hàng**, **Liên hệ** tách khỏi **Tổ chức** | Một công ty có nhiều người liên hệ, một người có nhiều kênh |
| **SLA + thời gian phản hồi đầu** | Thước đo cốt lõi của CSKH |
| **Luật tự phân công** (vòng tròn, theo tải) | Đúng nhu cầu nhiều nhân viên CSKH |
| **Nhật ký cuộc gọi gắn vào khách** | Đúng nhu cầu gọi điện |
| Phễu bán hàng, chiến dịch, báo cáo hiệu quả người phụ trách | Để giai đoạn sau |
| **Bỏ**: SMS Center, email campaign kiểu cũ, Twilio / Exotel | Không hợp thị trường Việt Nam |

---

## 3. ERP mình đã có gì dùng lại được

| Đã có | Ở đâu | Dùng cho CRM |
|---|---|---|
| **Lớp kênh nhắn tin**: Telegram; Zalo Bot Platform (`zl:`); tài khoản Zalo công ty qua `zalo-listener` (`zu:` chat riêng, `zg:` nhóm) | `agent_hub/channels.py`, dịch vụ `zalo-listener` | Nhận và gửi tin cho Hộp thư hợp nhất — không viết lại từ đầu |
| **Trợ lý AI** (lõi `core_v2`, công cụ MCP, tri thức HDSD) | `agent_hub`, `assistant` | Gợi ý câu trả lời, tóm tắt hội thoại, tự trả lời ngoài giờ |
| **Chuông báo + Web Push** | `notification`, `push` | Báo tin mới, báo sắp trễ SLA |
| **Phân quyền hai trục** (vai trò × phạm vi dữ liệu) | `core/auth.py`, `core/scoping.py` | Nhân viên chỉ thấy khách / hội thoại của thương hiệu hoặc nhóm mình |
| **Phiếu hỗ trợ** (đang dùng cho IT nội bộ) | `ticket` | Làm mẫu cho phiếu khiếu nại của khách |
| **Luồng duyệt**, **việc Dự án**, **tệp đính kèm**, **nhật ký thao tác** | `approval`, `work`, `attachment`, `audit` | Duyệt đền bù / đổi trả; giao việc theo khách; lưu ghi âm, ảnh |
| **Thương hiệu**, **pháp nhân** | `tab_brand`, `tab_company` | Gắn khách và kênh theo thương hiệu |
| **Chưa có**: bảng khách hàng, liên hệ, hội thoại, cuộc gọi, bán hàng | — | Phải làm mới |

---

## 4. Các phân hệ con đề xuất

### CRM-1. Khách hàng và liên hệ (nền)
- Khách hàng (cá nhân hoặc tổ chức), liên hệ, địa chỉ, nhóm khách, thương hiệu phụ trách, người phụ trách, nhãn.
- **Danh tính kênh**: một khách có nhiều *số điện thoại, Zalo, Telegram*; tin hoặc cuộc gọi tới thì tra danh tính để nhận ra khách, chưa có thì tạo khách tiềm năng.
- Gộp khách trùng (cùng số điện thoại).
- Dòng thời gian của khách: tin nhắn, cuộc gọi, phiếu, ghi chú, (sau này) đơn hàng — xem một chỗ.

### CRM-2. Hộp thư hợp nhất (Zalo, Telegram)
- Một màn gom mọi hội thoại từ các kênh, lọc theo kênh / trạng thái / người phụ trách; trả lời ngay trong ERP, tin đi đúng kênh gốc.
- Nhận hội thoại, chuyển người, ghi chú nội bộ (khách không thấy), mẫu trả lời nhanh, gửi ảnh / tệp.
- Trạng thái hội thoại: mới → đang xử lý → chờ khách → đã xong; mở lại khi khách nhắn tiếp.
- AI gợi ý câu trả lời và tóm tắt hội thoại dài; nhân viên bấm duyệt mới gửi.
- **Kênh Zalo cho CSKH phải dùng Zalo OA (tài khoản chính thức)**, không dùng tài khoản Zalo cá nhân qua `zalo-listener`: đường cá nhân là không chính thức, dễ bị khóa tài khoản và không hợp điều khoản Zalo khi nhắn khách hàng số lượng lớn. `zalo-listener` giữ cho nhóm nội bộ như hiện nay. Lớp kênh hiện có Zalo Bot Platform (`zl:`); Zalo OA là một kênh mới cắm vào cùng lớp đó.
- Telegram: bot Telegram của công ty, khách nhắn vào bot.

### CRM-3. Tài khoản và đội CSKH
- **Sổ kênh**: mỗi Zalo OA, bot Telegram, số hotline là một *tài khoản kênh*, gắn thương hiệu, nhóm CSKH, người quản lý; khóa / thông tin kết nối lưu mã hóa, không hiện trên màn.
- **Nhóm CSKH** và thành viên; trạng thái *đang trực / tạm nghỉ / ngoài ca*; lịch ca trực (dùng lại lịch làm việc có sẵn nếu hợp).
- **Luật phân công**: vòng tròn, ít việc nhất, theo thương hiệu, giữ người cũ nếu khách quay lại.
- **SLA**: thời gian phản hồi đầu, thời gian xử lý; cảnh báo trước khi trễ; tự đẩy lên trưởng nhóm khi trễ.
- Phân quyền: nhân viên thấy hội thoại của mình; trưởng nhóm thấy cả nhóm; quản lý thấy theo thương hiệu.

### CRM-4. Tổng đài điện thoại
- Mô hình **tổng đài ảo**: thuê một / vài số hotline, mỗi nhân viên một máy lẻ, gọi và nghe bằng **app điện thoại hoặc trên trình duyệt**; cước mọi máy lẻ **trừ vào một tài khoản trả trước của công ty**.
- Nhà cung cấp tham khảo ở Việt Nam: Stringee, tổng đài ảo Viettel, OMICall, CareSoft (cần so sánh và hỏi báo giá ở GĐ0).
- Nối vào ERP: **bấm số để gọi** trong hồ sơ khách; **cuộc gọi đến hiện ngay thông tin khách**; mỗi cuộc gọi tự ghi vào dòng thời gian khách (thời lượng, người nghe, ghi âm, gọi nhỡ).
- Gọi nhỡ tự tạo việc *gọi lại* giao cho người trực.
- Báo cáo cuộc gọi và cước theo người, theo ngày; đối chiếu với hóa đơn nhà cung cấp.
- Cách nối: nhà cung cấp gửi sự kiện cuộc gọi về ERP qua webhook → ERP ghi nhật ký cuộc gọi; ERP gọi API của nhà cung cấp để bấm số. Bọc trong một **lớp trung gian** để đổi nhà cung cấp không phải sửa phần còn lại.

### CRM-5. Phiếu khiếu nại / yêu cầu của khách
- Tạo phiếu từ hội thoại hoặc cuộc gọi; loại phiếu (khiếu nại chất lượng, đổi trả, bảo hành, tư vấn), mức ưu tiên, SLA.
- Giao việc sang phòng ban khác (kho, sản xuất, thu mua) qua việc Dự án; duyệt đền bù / đổi trả qua luồng duyệt có sẵn.
- Khảo sát hài lòng sau khi đóng phiếu (gửi qua kênh khách đang dùng).

### CRM-6. Báo cáo CSKH
- Số hội thoại / cuộc gọi theo kênh, giờ cao điểm, thời gian phản hồi đầu, tỷ lệ trễ SLA, hiệu suất từng nhân viên, điểm hài lòng, lý do khiếu nại hàng đầu.
- Gắn vào phân hệ Báo cáo có sẵn (quyền xem từng báo cáo theo `require_report`).

### CRM-7. Phễu bán hàng và chiến dịch (giai đoạn sau)
- Khách tiềm năng → cơ hội → báo giá → đơn bán (cần phân hệ Bán hàng).
- Gửi tin hàng loạt có mẫu qua Zalo ZNS (tính phí mỗi tin), chiến dịch, đo chuyển đổi.

---

## 5. Lộ trình

| Giai đoạn | Nội dung | Ước lượng | Ghi chú |
|---|---|---|---|
| **GĐ0** Chốt và chuẩn bị | Trả lời câu hỏi mục 6; so sánh và chọn nhà cung cấp tổng đài; đăng ký / xác thực Zalo OA | 1 tuần | Phần chờ bên ngoài có thể lâu hơn |
| **GĐ1** Nền + hộp thư | CRM-1 khách hàng, danh tính kênh; CRM-2 hộp thư với **Telegram trước** (kênh có sẵn), rồi Zalo OA | 5–6 người-tuần | Dùng lại lớp kênh của dịch vụ AI |
| **GĐ2** Đội CSKH | CRM-3 sổ kênh, nhóm, ca trực, phân công, SLA, chuông báo | 3–4 người-tuần | |
| **GĐ3** Tổng đài | CRM-4 lớp trung gian + một nhà cung cấp; bấm số, cuộc gọi đến, ghi âm, gọi nhỡ | 3–4 người-tuần | Cần tài khoản thử của nhà cung cấp |
| **GĐ4** Phiếu + báo cáo | CRM-5, CRM-6; AI gợi ý trả lời | 3–4 người-tuần | |
| **GĐ5** Bán hàng | CRM-7, sau khi có phân hệ Bán hàng | Tính sau | |

Mỗi giai đoạn lên dev thử với một nhóm CSKH nhỏ trước khi lên prod.

---

## 6. Câu hỏi cần chốt trước khi làm

1. **CSKH cho ai**: khách mua lẻ của các thương hiệu (IDA, DC…), đại lý, hay cả hai? Mỗi thương hiệu một đội riêng hay dùng chung?
2. **Kênh hiện có**: công ty đã có **Zalo OA** chưa, đã xác thực chưa, mỗi thương hiệu một OA hay chung? Có số hotline nào đang dùng không?
3. **Quy mô**: bao nhiêu nhân viên CSKH, có trực ngoài giờ / cuối tuần không, lượng tin và cuộc gọi mỗi ngày ước chừng bao nhiêu?
4. **Dữ liệu khách hiện nằm ở đâu** (Excel, phần mềm kế toán, app cũ…) để nạp ban đầu?
5. **Ghi âm cuộc gọi**: có cần không, giữ bao lâu? Phải có lời thông báo ghi âm cho khách.
6. **Quyền xem khách**: theo thương hiệu, theo nhóm, hay ai trong CSKH cũng xem hết?
7. **Ngân sách tổng đài** hằng tháng (phí số, phí máy lẻ, cước phút) để chọn nhà cung cấp.
8. **AI tự trả lời** ngoài giờ có được phép không, hay AI chỉ gợi ý cho nhân viên?

---

## 7. Rủi ro và lưu ý

- **Dữ liệu cá nhân của khách** (số điện thoại, tin nhắn, ghi âm): phải tuân thủ quy định bảo vệ dữ liệu cá nhân (Nghị định 13/2023/NĐ-CP và luật mới về bảo vệ dữ liệu cá nhân — nhờ pháp chế kiểm lại điều khoản hiện hành): có sự đồng ý của khách, giới hạn người xem, nhật ký truy cập, thời hạn lưu.
- **Zalo**: điều kiện gửi tin chủ động cho khách và biểu phí gói OA / ZNS thay đổi theo thời kỳ — kiểm lại với Zalo lúc làm GĐ0, không dựa vào thông tin cũ.
- **Phụ thuộc nhà cung cấp tổng đài**: bọc lớp trung gian (mục CRM-4) để đổi nhà cung cấp không phải sửa ERP.
- **Tải hệ thống**: hội thoại và nhật ký cuộc gọi tăng nhanh; cần chính sách lưu trữ / dọn dữ liệu cũ giống nhật ký nạp (CR-698).
