# CRM — CHĂM SÓC KHÁCH HÀNG ĐA KÊNH (CRM)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

## Phân hệ này là gì

Phân hệ dự kiến để **chăm sóc khách hàng đa kênh**: gom tin nhắn Zalo (Zalo OA) và Telegram vào một hộp thư trong ERP,
quản lý tài khoản kênh và đội CSKH (ca trực, phân công, SLA), gọi điện qua tổng đài ảo (nhiều người chung một số, cước trừ
một tài khoản), phiếu khiếu nại của khách và báo cáo CSKH; phễu bán hàng để giai đoạn sau. Hiện mới có **kế hoạch**
([`00`](plans/00-ke-hoach-crm.md), 02/11/2026), chưa làm. Trên giao diện v2 đã có ô phân hệ **Khách hàng** ở dạng *Sắp
có* (`frontend-v2/src/modules/customer/routes.tsx`, `enabled: false`).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Kế hoạch CRM-1..CRM-7, lộ trình GĐ0..GĐ5 | Đã có tài liệu | [`00`](plans/00-ke-hoach-crm.md), bản 1.0 02/11/2026 |
| GĐ0 chốt câu hỏi, chọn nhà cung cấp tổng đài, đăng ký Zalo OA | Chưa làm | Tám câu ở [`00`](plans/00-ke-hoach-crm.md) §6 |
| Mã nguồn | Chưa làm | Chưa có bảng khách hàng, liên hệ, hội thoại, cuộc gọi |
| Kênh Zalo nội bộ (bot Zalo chính thức, tài khoản Zalo công ty) | Trên dev | Mã đã xong trên dev, chờ token và quét QR ([kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §14) — là nền dùng lại, chưa phải CRM |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì (đề xuất) | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) (chưa có đường nào) |
| Thiết kế, bảng dữ liệu, bẫy | chưa có; ERP đã có gì dùng lại được ở [`00`](plans/00-ke-hoach-crm.md) §3 |
| So sánh, khảo sát, câu hỏi chờ chốt | ERPNext / Frappe CRM ở [`00`](plans/00-ke-hoach-crm.md) §2; câu chờ chốt §6 |
| Kế hoạch đang làm / đã xong | [`plans/`](plans/) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | chưa có |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng đề xuất CN-CRM-NN theo kế hoạch | Nháp |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-CRM-01..12 (phần lớn chưa có) | Nháp |
| [`plans/00-ke-hoach-crm.md`](plans/00-ke-hoach-crm.md) | Kế hoạch: kết luận, tham khảo ERPNext, thứ dùng lại, bảy phân hệ con, lộ trình, câu hỏi, rủi ro | Kế hoạch, chưa làm (bản 1.0, 02/11/2026) |
| [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) | Bảng đường API (dựng tự động; chưa có mã backend) | Nháp |

## Mã nguồn

- Backend: chưa có. Lớp kênh dùng lại: `backend/app/modules/agent_hub/` (kênh Telegram, Zalo).
- Giao diện v2: `frontend-v2/src/modules/customer/` (ô *Sắp có*).
