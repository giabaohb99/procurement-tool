# ĐẶT XE NỘI BỘ (DEGO BOOKING AUTO)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · duoc-CR-681, duoc-CR-706 (công ty và người duyệt trên phiếu) · bao-CR-596 (đồng bộ chiều ERP sang app cũ) |

## Phân hệ này là gì

Số hóa việc đặt xe nội bộ: nhân sự tạo yêu cầu đặt xe (công tác chở người, giao hàng chở hàng), người có quyền duyệt,
điều phối viên phân một xe và một tài xế, tài xế nhận, bắt đầu, hoàn tất chuyến. Kèm hai danh mục Xe và Tài xế (nội bộ
và thuê ngoài). Giao diện chỉ có trên `frontend-v2`, menu **Đặt xe**, đường `/vehicle-booking`
([tài liệu chức năng](chuc-nang/10-dat-xe.md)). Phân hệ nối hai chiều với app đặt xe cũ (Firebase) theo
[bộ tài liệu đồng bộ](tai-lieu-ky-thuat/dong-bo-app-cu/README.md).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Phiếu, duyệt, điều phối, tài xế, danh mục Xe / Tài xế, luồng duyệt nhiều bước, Chuyến của tôi, chống trùng giờ, thông báo, bản in (PHA 0–6) | Đã lên prod | [Đồng bộ app cũ §1](tai-lieu-ky-thuat/dong-bo-app-cu/README.md#1-bối-cảnh) ghi đã lên `main` (15/09/2026) |
| Công ty và người duyệt chọn trên phiếu; người cùng quyền cũng duyệt được | Đã có trong mã; môi trường chưa ghi | duoc-CR-681 (24–26/10/2026), duoc-CR-706 (31/10/2026) |
| Đồng bộ app cũ sang ERP | Đang chạy trên dev và prod | [vận hành §1](tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#1-bản-đồ-hệ-thống--dev-và-prod-là-hai-bộ-riêng-không-chung-gì) |
| Đồng bộ ERP sang app cũ (P3) | Đã dựng, công tắc tắt ở dev và prod | bao-CR-596; chốt 05/10/2026: chưa triển khai, chưa có hạn |
| E2E trình duyệt cho kịch bản 6 bước | Chưa làm | [tiến độ PHA 6](plans/dat-xe-duyet-dau/tien-do.md) |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `vehicle_booking`, `vehicle`, `driver`, `legacy_datxe` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [chuc-nang/10-dat-xe.md](chuc-nang/10-dat-xe.md) mục *Luồng duyệt nhiều bước* (sáu luật đã trả giá) · [plans/dat-xe-duyet-dau/README.md](plans/dat-xe-duyet-dau/README.md) |
| Đồng bộ app đặt xe cũ | [tai-lieu-ky-thuat/dong-bo-app-cu/README.md](tai-lieu-ky-thuat/dong-bo-app-cu/README.md), sổ tay trực [van-hanh.md](tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | Mục 3 *Những gì đã chốt* của [tài liệu đồng bộ](tai-lieu-ky-thuat/dong-bo-app-cu/README.md#3-những-gì-đã-chốt) |
| Kế hoạch đang làm / đã xong | [plans/dat-xe-duyet-dau/tien-do.md](plans/dat-xe-duyet-dau/tien-do.md), [phase-6-con-lai.md](plans/dat-xe-duyet-dau/phase-6-con-lai.md) |
| Kịch bản kiểm thử tay | [kiem-thu/test-phan-quyen.md](kiem-thu/test-phan-quyen.md) |
| Hướng dẫn người dùng | Trung tâm trợ giúp, bài *Đặt xe: chọn Công ty và Người duyệt trên phiếu* (`backend/scripts/seed_help_dat_xe_chon_nguoi_duyet.py`) |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-DX-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-DX-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-dat-xe.md](chuc-nang/10-dat-xe.md) | Tài liệu chức năng: vai trò, vòng đời, luồng duyệt nhiều bước, từng trường, danh mục, phân quyền | chưa ghi |
| [kiem-thu/test-phan-quyen.md](kiem-thu/test-phan-quyen.md) | Kịch bản kiểm phân quyền bằng tay với bảy tài khoản | chưa ghi |
| [plans/dat-xe-duyet-dau/README.md](plans/dat-xe-duyet-dau/README.md) | Kế hoạch tổng: mô hình dữ liệu, chi tiết chức năng, quyết định | Đã xong PHA 0–5 (03/09/2026) |
| [plans/dat-xe-duyet-dau/tien-do.md](plans/dat-xe-duyet-dau/tien-do.md) | Tick từng đầu việc PHA 0–6 | chưa ghi |
| [plans/dat-xe-duyet-dau/phase-0-nen-mo-hinh.md](plans/dat-xe-duyet-dau/phase-0-nen-mo-hinh.md) | PHA 0 — nền và mô hình dữ liệu | ĐÃ XONG |
| [plans/dat-xe-duyet-dau/phase-1-mvp-phieu.md](plans/dat-xe-duyet-dau/phase-1-mvp-phieu.md) | PHA 1 — phiếu tạo và theo dõi | ĐÃ XONG (hồi cứu) |
| [plans/dat-xe-duyet-dau/phase-2-danh-muc-xe-tai-xe.md](plans/dat-xe-duyet-dau/phase-2-danh-muc-xe-tai-xe.md) | PHA 2 — danh mục Xe và Tài xế | ĐÃ XONG (hồi cứu) |
| [plans/dat-xe-duyet-dau/phase-3-dieu-phoi-luong-nghiep-vu.md](plans/dat-xe-duyet-dau/phase-3-dieu-phoi-luong-nghiep-vu.md) | PHA 3 — điều phối và luồng theo vai trò | ĐÃ XONG (hồi cứu) |
| [plans/dat-xe-duyet-dau/phase-4-5-dong-bo-ui-va-len-trang.md](plans/dat-xe-duyet-dau/phase-4-5-dong-bo-ui-va-len-trang.md) | PHA 4–5 — đồng bộ giao diện, Thêm / Sửa lên trang | ĐÃ XONG (hồi cứu) |
| [plans/dat-xe-duyet-dau/phase-6-con-lai.md](plans/dat-xe-duyet-dau/phase-6-con-lai.md) | PHA 6 — nâng cấp: runtime duyệt, Chuyến của tôi, chống trùng giờ, thông báo, bản in | chưa ghi ở đầu tệp (README kế hoạch: xong trừ E2E trình duyệt) |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/README.md](tai-lieu-ky-thuat/dong-bo-app-cu/README.md) | Đồng bộ app đặt xe cũ: bối cảnh, mục tiêu, quyết định QĐ-A..N, ai làm chủ dữ liệu | Bản 1.0, 15/09/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/danh-sach-phase.md](tai-lieu-ky-thuat/dong-bo-app-cu/danh-sach-phase.md) | Chín pha đồng bộ | Bản 1.0, 15/09/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/doi-chieu-truong.md](tai-lieu-ky-thuat/dong-bo-app-cu/doi-chieu-truong.md) | Đối chiếu từng trường app cũ và ERP | Bản 1.0, 15/09/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/mo-ta-ky-thuat.md](tai-lieu-ky-thuat/dong-bo-app-cu/mo-ta-ky-thuat.md) | Hợp đồng webhook, chữ ký, sổ đồng bộ | Bản 1.0, 15/09/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/p3-erp-sang-app-cu.md](tai-lieu-ky-thuat/dong-bo-app-cu/p3-erp-sang-app-cu.md) | Chiều ERP sang app cũ (bản dựng) | Bản 1.0, 05/10/2026 |
| [tai-lieu-ky-thuat/dong-bo-app-cu/tien-do.md](tai-lieu-ky-thuat/dong-bo-app-cu/tien-do.md) | Tiến độ đồng bộ | chưa ghi (trạng thái chung 16/09/2026) |
| [tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md](tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md) | Sổ tay vận hành cho người trực | Bản 1.0, 23/10/2026 |

## Mã nguồn

- Backend: `backend/app/modules/vehicle_booking/`, đồng bộ app cũ `backend/app/modules/legacy_datxe/` và `backend/app/modules/sync_log/`
- Giao diện v2: `frontend-v2/src/modules/vehicle-booking/`
- Luật cho người viết mã: chưa có tệp luật riêng; sáu luật luồng duyệt ghi ở [tài liệu chức năng](chuc-nang/10-dat-xe.md)
