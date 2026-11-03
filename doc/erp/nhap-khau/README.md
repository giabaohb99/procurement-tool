# NHẬP KHẨU (NK)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · CR chính: bao-CR-319, bao-CR-321, bao-CR-347, bao-CR-453, bao-CR-602 |

## Phân hệ này là gì

Phân hệ Nhập khẩu phục vụ Phòng Thu mua khi mua hàng từ nước ngoài: đơn mua hàng loại nhập khẩu (ngoại tệ, tỷ giá, tờ
khai hải quan), chi phí thu mua ba giai đoạn (dự toán, tạm tính, quyết toán) phân bổ về dòng hàng, công nợ cho từng khoản
chi phí, giá vốn lô hàng, và hồ sơ, tiến độ nhập khẩu theo từng lô. Phân hệ **không có màn riêng**: mọi thứ nằm trên chi
tiết Đơn mua hàng (`/procurement/purchase-orders/:id`) và danh mục `/procurement/po-cost-types`; chưa có mã backend riêng,
đường API đi qua `purchase_order` (xem [api.md](tai-lieu-ky-thuat/api.md)).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Đơn nhập khẩu: ngoại tệ, tỷ giá, tờ khai, ETD, bản in nhập khẩu | chưa ghi | bao-CR-319, bao-CR-347; mô tả ở [thu mua 13](../thu-mua/chuc-nang/13-don-mua-hang.md) mục A.18..26 |
| Chi phí thu mua ba giai đoạn | Trên dev (tài liệu ghi code xong 22/09/2026, prod chưa lên lúc viết) | bao-CR-453, [11-chi-phi-thu-mua.md](chuc-nang/11-chi-phi-thu-mua.md) |
| Hồ sơ và tiến độ nhập khẩu | Chưa làm (tạm dừng từ 12/09/2026) | Một phần đã có qua Báo cáo thực hiện trên ĐMH (bao-CR-602), xem [10-danh-sach-tinh-nang.md](chuc-nang/10-danh-sach-tinh-nang.md) nhóm B |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `purchase_order`, `purchase_cost_type` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [chuc-nang/11-chi-phi-thu-mua.md](chuc-nang/11-chi-phi-thu-mua.md) mục 6; [thu mua 13](../thu-mua/chuc-nang/13-don-mua-hang.md) mục K |
| So sánh, khảo sát, câu hỏi chờ chốt | [chuc-nang/10-danh-sach-tinh-nang.md](chuc-nang/10-danh-sach-tinh-nang.md) mục 11, 14; [chuc-nang/11-chi-phi-thu-mua.md](chuc-nang/11-chi-phi-thu-mua.md) mục 11 |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/` |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Chi phí thu mua trên đơn mua hàng* (`backend/scripts/seed_help_chi_phi_thu_mua.py`) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-NK-01..11 | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-NK-01..12 | Nháp |
| [chuc-nang/10-danh-sach-tinh-nang.md](chuc-nang/10-danh-sach-tinh-nang.md) | Hồ sơ và tiến độ nhập khẩu: yêu cầu, 59 tính năng, phân quyền, chia đợt | Tạm dừng 12/09/2026 |
| [chuc-nang/11-chi-phi-thu-mua.md](chuc-nang/11-chi-phi-thu-mua.md) | Thiết kế chi phí thu mua ba giai đoạn bao-CR-453 | Đã code đủ năm đợt ngày 22/09/2026 (dev) |
| [du-lieu/ra-soat-ho-so-nhap-khau-v1.xlsx](du-lieu/ra-soat-ho-so-nhap-khau-v1.xlsx) | Bảng rà soát hồ sơ nhập khẩu, bản 1 | chưa ghi |
| [du-lieu/ra-soat-ho-so-nhap-khau-v2.xlsx](du-lieu/ra-soat-ho-so-nhap-khau-v2.xlsx) | Bảng rà soát hồ sơ nhập khẩu, bản 2 | chưa ghi |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Tài liệu API (chưa có đường riêng) | Nháp |

## Mã nguồn

- Backend: chưa có phân hệ riêng; nằm trong `backend/app/modules/purchase_order/` (bảng `tab_po_cost`,
  `tab_po_cost_type`), báo cáo giá vốn ở `backend/app/modules/report/import_landed_cost.py`.
- Giao diện v2: `frontend-v2/src/modules/procurement/` (khối Chi phí thu mua trên chi tiết ĐMH, danh mục Loại chi phí).
- Liên quan: tra cứu giá hải quan ở `backend/app/modules/customs/`, tài liệu ở [`../hai-quan/`](../hai-quan/README.md).
