# NHẬN HÀNG VÀ CHẤT LƯỢNG (NH)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · chưa có CR làm mã riêng |

## Phân hệ này là gì

Phân hệ Nhận hàng và Chất lượng lo chiều vào của kho khi mua hàng: phiếu nhập kho, kiểm chất lượng đầu vào, số chấp
nhận và số từ chối, kho hàng lỗi, trả hàng nhà cung cấp, khoản giảm nợ, đẩy chi phí thu mua vào giá kho. Người dùng dự
kiến là thủ kho, QC, thu mua, kế toán. **Hiện chưa có màn riêng**: việc nhận hàng đang nằm trong lần giao của Đơn mua hàng
(`tab_po_delivery`), lưu đơn là sinh ngầm phiếu nhập `tab_goods_receipt`, dòng sổ kho và công nợ. Phân hệ đang ở mức
**nghiên cứu**.

## Tới đâu rồi

Độ phủ lấy từ [nghiên cứu nhận hàng và chất lượng](nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) (soát
`erp-v2` commit `601ec718`, 02/11/2026): **35 %** (8 / 23 chức năng so với ERPNext v16).

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Lần giao nhiều đợt, hẹn giao, cảnh báo trễ, đính kèm phiếu giao (trên ĐMH) | chưa ghi (có mã) | Đặc tả ở [thu mua 13 mục C](../thu-mua/chuc-nang/13-don-mua-hang.md) |
| Phiếu nhập ngầm, ô kết quả kiểm một chữ | chưa ghi (có mã một phần) | Bảng lần giao v2 chưa có ô kiểm (nghiên cứu mục 1) |
| Số chấp nhận, từ chối, dung sai, trả hàng NCC, phiếu nhập của thủ kho | Chưa làm | Kế hoạch ba nấc ở nghiên cứu mục 7 |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) (chưa có đường riêng; nhận hàng đi qua đường `purchase_order`) |
| Thiết kế, bảng dữ liệu, bẫy | [nghiên cứu mục 4, 6](nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md](nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) mục 5, 6.11 |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/`; kế hoạch chung ở [doc/plans/12](../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md) và [doc/plans/01](../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md) |
| Kịch bản kiểm thử tay | Chưa có |
| Hướng dẫn người dùng | Chưa có |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-NH-01..18 (phần lớn dự kiến, nguồn nghiên cứu) | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-NH-01..12 | Nháp |
| [nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md](nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Nhận hàng, kiểm chất lượng, trả hàng, chi phí nhập: ERPNext v16 so với ERP DEGO, đề xuất, kế hoạch ba nấc | chưa ghi (đầu tệp: bản 1.0, 02/11/2026) |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Tài liệu API (chưa có đường riêng) | Nháp |

## Mã nguồn

- Backend: `backend/app/modules/goods_receipt/` (phiếu nhập ngầm, chỉ có `model.py`, `service.py`); luồng sinh hiệu ứng
  ở `backend/app/modules/purchase_order/service.py` (`recompute_effects`, `_cleanup_delivery`).
- Giao diện v2: chưa có màn riêng; bảng lần giao ở `frontend-v2/src/modules/procurement/components/`.
- Luật cho người viết mã: chưa có.
