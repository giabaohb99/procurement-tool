# YÊU CẦU CHỨC NĂNG — CRM

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Đọc trước:** phân hệ mới có kế hoạch ([`00`](../plans/00-ke-hoach-crm.md), 02/11/2026), chưa làm. Danh sách dưới là các
chức năng **đề xuất** theo bảy phân hệ con CRM-1..CRM-7 của kế hoạch, chưa phải phạm vi đã duyệt; phạm vi chốt sau khi trả
lời tám câu ở [`00`](../plans/00-ke-hoach-crm.md) §6 (giai đoạn GĐ0). Mọi dòng trạng thái là **Chưa**.

## 1. Người dùng và vai trò

Chưa có mã vai trò. Đề xuất theo [`00`](../plans/00-ke-hoach-crm.md) CRM-3:

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân viên CSKH (chưa có mã) | Nhận và trả lời hội thoại của mình, gọi điện, tạo phiếu khiếu nại |
| Trưởng nhóm CSKH (chưa có mã) | Thấy hội thoại cả nhóm, nhận việc đẩy lên khi trễ SLA, quản lý ca trực |
| Quản lý theo thương hiệu (chưa có mã) | Thấy khách và hội thoại theo thương hiệu, báo cáo CSKH |
| Phòng ban khác (kho, sản xuất, thu mua) | Nhận việc giao từ phiếu khiếu nại qua việc Dự án |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-CRM-01 | Khách hàng (cá nhân / tổ chức), liên hệ, địa chỉ, nhóm khách, thương hiệu và người phụ trách, nhãn — [`00`](../plans/00-ke-hoach-crm.md) CRM-1 | CSKH | chưa có | Chưa | — |
| CN-CRM-02 | Danh tính kênh (số điện thoại, Zalo, Telegram) để nhận ra khách; chưa có thì tạo khách tiềm năng; gộp khách trùng — [`00`](../plans/00-ke-hoach-crm.md) CRM-1 | Hệ thống, CSKH | chưa có | Chưa | — |
| CN-CRM-03 | Dòng thời gian của khách: tin nhắn, cuộc gọi, phiếu, ghi chú — [`00`](../plans/00-ke-hoach-crm.md) CRM-1 | CSKH | Hồ sơ khách | Chưa | — |
| CN-CRM-04 | Hộp thư hợp nhất Zalo OA và Telegram: lọc, trả lời đúng kênh gốc, nhận / chuyển hội thoại, ghi chú nội bộ, mẫu trả lời nhanh, gửi ảnh / tệp — [`00`](../plans/00-ke-hoach-crm.md) CRM-2 | CSKH | chưa có | Chưa | — |
| CN-CRM-05 | AI gợi ý câu trả lời và tóm tắt hội thoại dài, nhân viên bấm duyệt mới gửi — [`00`](../plans/00-ke-hoach-crm.md) CRM-2 | CSKH | Hộp thư | Chưa | — |
| CN-CRM-06 | Sổ kênh (Zalo OA, bot Telegram, hotline), nhóm CSKH, thành viên, trạng thái trực, lịch ca — [`00`](../plans/00-ke-hoach-crm.md) CRM-3 | Quản lý CSKH | chưa có | Chưa | — |
| CN-CRM-07 | Luật phân công (vòng tròn, ít việc nhất, theo thương hiệu, giữ người cũ) và SLA (phản hồi đầu, xử lý, cảnh báo, đẩy lên trưởng nhóm) — [`00`](../plans/00-ke-hoach-crm.md) CRM-3 | Hệ thống, trưởng nhóm | chưa có | Chưa | — |
| CN-CRM-08 | Tổng đài ảo: bấm số từ hồ sơ khách, cuộc gọi đến hiện thông tin khách, ghi âm, tự ghi vào dòng thời gian — [`00`](../plans/00-ke-hoach-crm.md) CRM-4 | CSKH | chưa có | Chưa | — |
| CN-CRM-09 | Gọi nhỡ tự tạo việc gọi lại cho người trực — [`00`](../plans/00-ke-hoach-crm.md) CRM-4 | CSKH | chưa có | Chưa | — |
| CN-CRM-10 | Báo cáo cuộc gọi và cước theo người / ngày, đối chiếu hóa đơn nhà cung cấp — [`00`](../plans/00-ke-hoach-crm.md) CRM-4 | Quản lý | Phân hệ Báo cáo | Chưa | — |
| CN-CRM-11 | Phiếu khiếu nại / yêu cầu của khách: loại, ưu tiên, SLA, giao việc phòng khác, duyệt đền bù / đổi trả, khảo sát hài lòng — [`00`](../plans/00-ke-hoach-crm.md) CRM-5 | CSKH, phòng ban liên quan | chưa có | Chưa | — |
| CN-CRM-12 | Báo cáo CSKH (theo kênh, giờ cao điểm, phản hồi đầu, trễ SLA, hiệu suất, hài lòng, lý do khiếu nại) — [`00`](../plans/00-ke-hoach-crm.md) CRM-6 | Quản lý | Phân hệ Báo cáo | Chưa | — |
| CN-CRM-13 | Phễu bán hàng (khách tiềm năng → cơ hội → báo giá → đơn bán) và chiến dịch gửi tin ZNS — [`00`](../plans/00-ke-hoach-crm.md) CRM-7 | Bán hàng | chưa có | Chưa | — |

## 3. Chi tiết từng chức năng

### CN-CRM-02 — Danh tính kênh

- **Mục đích:** một khách có nhiều số điện thoại / Zalo / Telegram; tin hoặc cuộc gọi tới thì nhận ra ngay là ai.
- **Luật đề xuất:** chưa có danh tính thì tạo khách tiềm năng; gộp khách trùng theo cùng số điện thoại. Chi tiết:
  [`00`](../plans/00-ke-hoach-crm.md) CRM-1.

### CN-CRM-04 — Hộp thư hợp nhất

- **Mục đích:** một màn gom mọi hội thoại, trả lời ngay trong ERP.
- **Luật đề xuất:** kênh Zalo cho CSKH **phải dùng Zalo OA**, không dùng tài khoản Zalo cá nhân qua `zalo-listener` (không
  chính thức, dễ bị khóa); Telegram dùng bot của công ty; làm Telegram trước rồi Zalo OA (GĐ1). Chi tiết:
  [`00`](../plans/00-ke-hoach-crm.md) CRM-2, §5.
- **Liên quan:** dùng lại lớp kênh của dịch vụ AI ([`00`](../plans/00-ke-hoach-crm.md) §3; [Trợ lý AI](../../tro-ly-ai/README.md)).

### CN-CRM-07 — Phân công và SLA

- **Mục đích:** chia hội thoại cho đúng người và đo được thời gian phản hồi.
- **Luật đề xuất:** vòng tròn, ít việc nhất, theo thương hiệu, giữ người cũ khi khách quay lại; cảnh báo trước khi trễ, trễ
  thì đẩy lên trưởng nhóm; báo qua chuông và Web Push có sẵn. Chi tiết: [`00`](../plans/00-ke-hoach-crm.md) CRM-3.
- **Quyền đề xuất:** nhân viên thấy hội thoại của mình; trưởng nhóm thấy cả nhóm; quản lý thấy theo thương hiệu.

### CN-CRM-08 — Tổng đài ảo

- **Mục đích:** nhiều nhân viên gọi chung một / vài số hotline, cước trừ một tài khoản trả trước của công ty.
- **Luật đề xuất:** nhà cung cấp gửi sự kiện cuộc gọi về ERP qua webhook; ERP gọi API nhà cung cấp để bấm số; bọc trong
  một lớp trung gian để đổi nhà cung cấp không phải sửa phần còn lại. Nhà cung cấp tham khảo cần so sánh ở GĐ0. Chi tiết:
  [`00`](../plans/00-ke-hoach-crm.md) CRM-4.

## 4. Luồng trạng thái chứng từ (nếu có)

Hội thoại (đề xuất, [`00`](../plans/00-ke-hoach-crm.md) CRM-2):

```
Mới → Đang xử lý → Chờ khách → Đã xong
Đã xong → Đang xử lý (khách nhắn tiếp)
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | CSKH cho ai (khách lẻ các thương hiệu, đại lý, hay cả hai); mỗi thương hiệu một đội hay dùng chung | chưa có | chưa có |
| 2 | Công ty đã có Zalo OA chưa, đã xác thực chưa, mỗi thương hiệu một OA hay chung; có hotline nào đang dùng | chưa có | chưa có |
| 3 | Quy mô: số nhân viên CSKH, trực ngoài giờ, lượng tin và cuộc gọi mỗi ngày | chưa có | chưa có |
| 4 | Dữ liệu khách hiện nằm ở đâu để nạp ban đầu | chưa có | chưa có |
| 5 | Có cần ghi âm cuộc gọi không, giữ bao lâu | chưa có | chưa có |
| 6 | Quyền xem khách theo thương hiệu, theo nhóm hay ai trong CSKH cũng xem hết | chưa có | chưa có |
| 7 | Ngân sách tổng đài hằng tháng | chưa có | chưa có |
| 8 | AI được tự trả lời ngoài giờ hay chỉ gợi ý | chưa có | chưa có |
| C8 | Mâu thuẫn mảng bán hàng (danh mục chờ C8), chốt trước vòng bán hàng | Ban lãnh đạo | chưa có |

Câu 1–8 ở [`00`](../plans/00-ke-hoach-crm.md) §6; C8 ở [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) §14.
