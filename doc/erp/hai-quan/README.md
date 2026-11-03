# TRA CỨU THỊ TRƯỜNG — GIÁ HẢI QUAN (HQ)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-470 (HQ1..HQ6) · bao-CR-481 (công cụ AI) · bao-CR-493..496, bao-CR-503 (yêu cầu phòng Thu mua) · bao-CR-500 (đổi tên) · bao-CR-541 (chống trùng) · bao-CR-603 · bao-CR-608 · duoc-CR-684 |

## Phân hệ này là gì

Màn tra cứu dữ liệu tờ khai hải quan nhập khẩu (kết xuất GTT02, nạp bằng Excel) để phòng Thu mua biết mặt hàng / hoạt
chất đang được nhập về Việt Nam với giá nào, lượng bao nhiêu, ai nhập, tháng nào giá tốt — làm căn cứ quyết định mua lúc
nào và có ôm hàng trước không. Kèm danh mục hóa chất theo văn bản, biểu thuế, danh mục thuốc BVTV và công cụ cho trợ lý
AI. Tên trên màn đã đổi từ *Tra cứu giá hải quan* thành **Tra cứu thị trường** (bao-CR-500). Nằm trong menu Thu mua: bản
v2 ở `/procurement/customs-prices/<mục>` (Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý · Thuế · Thuốc BVTV ·
Lịch sử nạp · Cấu hình), bản v1 ở `/customs-prices`.

Ranh giới đã chốt: **không nối** danh mục VTBB, tồn kho, lịch sử mua hàng của mình
([`10`](chuc-nang/10-danh-sach-tinh-nang.md) §1).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| HQ1..HQ5 (nạp, tra cứu, biểu đồ, hoạt chất, nhà nhập khẩu, so sánh, công cụ AI) và cụm yêu cầu chị Mi, bộ lọc đã lưu | Đã lên prod | Prod 01/10/2026 theo [kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) §3 |
| HQ6 P-01, P-03, P-04 (bảng ngưỡng NĐ 24, tra nghĩa vụ, biểu thuế) | chưa ghi | Kế hoạch ghi *đã có mã*, chưa ghi lên môi trường nào |
| P-02 cảnh báo tồn kho chạm ngưỡng | Chưa làm | Cần cầu nối VTBB với hoạt chất (NK2-1) |
| Excel theo mẫu công ty, in báo giá / PDF, biểu đồ theo tuần | Chưa làm | Chờ mẫu của chị Mi / chờ chốt có cần không ([`06`](nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md) §7) |
| Bài HDSD mục IX | chưa ghi | Phải chạy lại seed rồi nạp lại chỉ mục RAG (NK1-1, cần kiểm lại trên dev / prod) |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) · nhóm `customs`, `customs_price`, `customs_regulation` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [`tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md`](tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) (hai cột ngày, chống trùng, dung lượng) |
| So sánh, khảo sát, câu hỏi chờ chốt | [`nghien-cuu/`](nghien-cuu/) · câu Q1..Q6 ở [`10`](chuc-nang/10-danh-sach-tinh-nang.md) §9 |
| Kế hoạch đang làm / đã xong | [`plans/`](plans/) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Tra cứu giá hải quan* dưới nhóm *Dành cho Nhân viên Mua hàng* ([`seed_help_customs_prices.py`](../../../backend/scripts/seed_help_customs_prices.py)) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [`chuc-nang/01-yeu-cau-chuc-nang.md`](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-HQ-NN, tóm tắt và liên kết | Nháp |
| [`chuc-nang/02-yeu-cau-phi-chuc-nang.md`](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-HQ-01..12 | Nháp |
| [`chuc-nang/10-danh-sach-tinh-nang.md`](chuc-nang/10-danh-sach-tinh-nang.md) | Danh sách tính năng gốc N, T, B, A, P, Y; câu hỏi còn mở; số đo dữ liệu thật | Kế hoạch + tình trạng (bản 1.1, 23/09/2026) |
| [`chuc-nang/11-giao-dien.md`](chuc-nang/11-giao-dien.md) | Màn hình M1..M4 cho cả v1 và v2, luật hiển thị, bản dựng khác đề xuất | Thiết kế + đã dựng (bản 1.2, 23/09/2026) |
| [`nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md`](nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md) | Đối chiếu yêu cầu FR-PROC-2026-001 của phòng Thu mua với bản chạy dev 28/09/2026; rủi ro R1; việc còn lại | chưa ghi |
| [`plans/03-lo-trinh-phase.md`](plans/03-lo-trinh-phase.md) | Lộ trình HQ0..HQ6, ước lượng ngày công | chưa ghi (bản 1.1, 23/09/2026) |
| [`plans/05-giao-viec-cr496-luu-bo-loc-log-dong.md`](plans/05-giao-viec-cr496-luu-bo-loc-log-dong.md) | Giao việc bao-CR-496: lưu bộ lọc riêng, log từng dòng khi nạp | chưa ghi |
| [`tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md`](tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) | Lược đồ, đường nạp, chống trùng, dung lượng, bài kiểm, nạp cấu hình | Thiết kế + đã dựng (bản 1.5, 23/09/2026) |
| [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md) | Bảng đường API (dựng tự động từ mã) | Nháp |

## Mã nguồn

- Backend: `backend/app/modules/customs/`; danh mục dựng bằng `make_crud_router` (`/api/customs-regulations`,
  `/api/customs-kind-keywords`, `/api/customs-search-synonyms`, `/api/customs-formulation-codes`).
- Giao diện v2: `frontend-v2/src/modules/procurement/pages/customs-price-page.tsx`, khai mục ở
  `frontend-v2/src/modules/procurement/config/customs-sections.ts`.
- Giao diện v1 (đóng băng, chỉ sửa khi có lệnh): `frontend/`.
- Công cụ trợ lý AI: `backend/app/modules/assistant/tools/customs_tool.py`.
