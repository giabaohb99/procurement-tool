# THU MUA (TM)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 (dựng bộ tài liệu bắt buộc) · CR chính của phân hệ: CR-034, CR-068, CR-108, CR-268, bao-CR-310, bao-CR-388, bao-CR-414, bao-CR-422 |

## Phân hệ này là gì

Phân hệ Thu mua phục vụ người yêu cầu ở các phòng, trưởng bộ phận, quản lý thu mua và nhân sự thu mua (NSTM). Nó đi
trọn luồng mua hàng: Yêu cầu báo giá (YCBG) và phiếu khảo sát, Yêu cầu mua hàng (YCMH), Đơn mua hàng (ĐMH) kèm lần giao,
công nợ phải trả và Yêu cầu thanh toán (YCTT), cộng các danh mục và báo cáo đi kèm. Trên giao diện v2 các màn nằm dưới
nhóm `/procurement/...` (ví dụ `/procurement/purchase-requests/:id`); tài liệu chức năng cũ còn ghi đường dẫn của giao
diện v1 (`/purchase-requests`, `/purchase-orders`…).

## Tới đâu rồi

Tài liệu cũ không ghi trạng thái lên prod cho từng mảng. Bảng dưới chỉ ghi điều tài liệu nói rõ; độ phủ so với chuẩn
lấy từ [bảng fit-gap 30/10/2026](nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) (soát mã nhánh `erp-v2`).

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Hỏi giá, chọn NCC (YCBG, phiếu khảo sát, phương án) | chưa ghi | Độ phủ 90 % theo doc 11 mục 5 |
| Yêu cầu mua hàng, điều phối hai chặng | chưa ghi | Độ phủ chặng yêu cầu mua 40 % (thiếu mức tồn tối thiểu, ngân sách) |
| Đơn mua hàng và duyệt | chưa ghi | Độ phủ 81 %; khóa sửa sau duyệt CR-108 |
| Phương án trên dòng YCMH | Trên dev (tài liệu ghi deploy dev 15/09/2026) | bao-CR-310, [12 mục H.10](chuc-nang/12-yeu-cau-mua-hang.md) |
| Báo cáo thực hiện trên YCBG | Đã lên prod (theo [brief](nghien-cuu/01-brief-bao-cao-thuc-hien-ycbg.md)) | bao-CR-388..393 |
| Công nợ, YCTT, tiền treo | chưa ghi | Độ phủ chặng hóa đơn, công nợ 50 % |
| Báo cáo thu mua | chưa ghi | Độ phủ 90 % |

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · các nhóm `purchase_request`, `survey_request`, `survey`, `purchase_order`, `payable`, `payment_request`, `supplier`, `contract`… trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/](tai-lieu-ky-thuat/tdd-bao-cao-thuc-hien-ycbg.md) và mô tả từng trường trong `chuc-nang/10..20` |
| So sánh, khảo sát, câu hỏi chờ chốt | [nghien-cuu/11 Độ phủ so với ERPNext](nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md), [nghien-cuu/09 Nghiệp vụ mua hàng](nghien-cuu/09-nghiep-vu-mua-hang.md) |
| Kế hoạch đang làm / đã xong | Chưa có thư mục `plans/` riêng; kế hoạch chung ở [doc/plans/01 Luồng chuẩn mua hàng, kho, sản xuất](../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md) |
| Kịch bản kiểm thử tay | [kiem-thu/00-muc-luc.md](kiem-thu/00-muc-luc.md) |
| Hướng dẫn người dùng | Trung tâm trợ giúp, nhóm *Dành cho Nhân viên Mua hàng*: `backend/scripts/seed_help_xu_ly_phuong_an.py`, `seed_help_chi_tiet_yc_mua_hang.py`, `seed_help_chi_phi_thu_mua.py`, `seed_help_thu_mua_cap_nhat.py`, `seed_help_lap_bo_tai_khoan_phong_tu_mua.py` |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Danh sách chức năng CN-TM-01..24, chi tiết sáu chức năng chính | Nháp |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng PCN-TM-01..12 | Nháp |
| [chuc-nang/10-phieu-khao-sat.md](chuc-nang/10-phieu-khao-sat.md) | Phiếu khảo sát NCC và sản phẩm: vòng đời, từng trường | chưa ghi |
| [chuc-nang/11-yeu-cau-khao-sat.md](chuc-nang/11-yeu-cau-khao-sat.md) | Yêu cầu báo giá (YCBG): vòng đời, phương án ẩn danh, quyền, xuất Excel, Tiến độ báo giá | chưa ghi |
| [chuc-nang/12-yeu-cau-mua-hang.md](chuc-nang/12-yeu-cau-mua-hang.md) | Yêu cầu mua hàng: điều phối hai chặng, dòng hàng, bản in, phương án, chứng từ liên quan | chưa ghi |
| [chuc-nang/13-don-mua-hang.md](chuc-nang/13-don-mua-hang.md) | Đơn mua hàng: khóa sau duyệt, lần giao, tiến độ dòng, lịch sử mua, chi phí thu mua | chưa ghi |
| [chuc-nang/14-yeu-cau-thanh-toan.md](chuc-nang/14-yeu-cau-thanh-toan.md) | Yêu cầu thanh toán, phiếu in, tiền treo (CR-268) | chưa ghi |
| [chuc-nang/15-ton-kho-cong-no.md](chuc-nang/15-ton-kho-cong-no.md) | Màn Tồn kho, điều chỉnh tồn, công nợ phải trả và ba luồng sinh nợ | chưa ghi |
| [chuc-nang/16-danh-muc.md](chuc-nang/16-danh-muc.md) | Danh mục: NCC, sản phẩm, hợp đồng, kho, ĐVT, phân loại, thương hiệu, phòng ban, phân công phụ trách, công ty | chưa ghi |
| [chuc-nang/17-he-thong-bao-cao.md](chuc-nang/17-he-thong-bao-cao.md) | Nhân sự, tài khoản, vai trò, cấu hình hệ thống, Báo cáo mua hàng, Báo cáo khảo sát | chưa ghi |
| [chuc-nang/18-lich-su-mua-hang.md](chuc-nang/18-lich-su-mua-hang.md) | Lịch sử mua hàng theo mã hàng và theo NCC, che NCC (CR-060) | chưa ghi |
| [chuc-nang/19-bao-cao-thuc-hien-ycbg.md](chuc-nang/19-bao-cao-thuc-hien-ycbg.md) | Khối Báo cáo thực hiện trên chi tiết YCBG | chưa ghi (đầu tệp: bản 1.0, 12/09/2026) |
| [chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md](chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md) | Hướng dẫn lập bộ tài khoản phòng tự mua hàng và công ty con | chưa ghi |
| [du-lieu/erpnext-01-huong-dan-mua-hang-den-thanh-toan-va-kho.pdf](du-lieu/erpnext-01-huong-dan-mua-hang-den-thanh-toan-va-kho.pdf) | Bản PDF của hướng dẫn ERPNext 01 | chưa ghi |
| [kiem-thu/00-muc-luc.md](kiem-thu/00-muc-luc.md) | Mục lục kịch bản kiểm thử tay dải `bao` | chưa ghi |
| [kiem-thu/01-chung-tu-lien-quan-ycmh.md](kiem-thu/01-chung-tu-lien-quan-ycmh.md) | Thẻ Chứng từ liên quan trên YCMH (bao-CR-422) | chưa ghi |
| [kiem-thu/02-nut-tao-don-va-in-phieu.md](kiem-thu/02-nut-tao-don-va-in-phieu.md) | Nút Tạo đơn, nút In phiếu, hộp hỏi gom đơn (bao-CR-420, 421) | chưa ghi |
| [kiem-thu/03-phuong-an-va-chuong.md](kiem-thu/03-phuong-an-va-chuong.md) | Chuông luồng phương án (bao-CR-419) | chưa ghi |
| [kiem-thu/04-pham-vi-va-bang-rong.md](kiem-thu/04-pham-vi-va-bang-rong.md) | Phạm vi dữ liệu và câu chữ khi bảng rỗng | chưa ghi |
| [kiem-thu/05-vai-tro-va-pham-vi.md](kiem-thu/05-vai-tro-va-pham-vi.md) | Màn Vai trò và quyền, hộp thoại Phạm vi (bao-CR-427, 428, 430) | chưa ghi |
| [kiem-thu/06-luong-duyet-cau-hinh-dat-xe-duyet-dau.md](kiem-thu/06-luong-duyet-cau-hinh-dat-xe-duyet-dau.md) | Đặt xe và Duyệt dấu theo luồng duyệt cấu hình (bao-CR-577) | chưa ghi |
| [nghien-cuu/01-brief-bao-cao-thuc-hien-ycbg.md](nghien-cuu/01-brief-bao-cao-thuc-hien-ycbg.md) | Brief nghiệp vụ Báo cáo thực hiện YCBG | chưa ghi |
| [nghien-cuu/09-nghiep-vu-mua-hang.md](nghien-cuu/09-nghiep-vu-mua-hang.md) | Giáo trình nghiệp vụ mua hàng chuẩn | Tài liệu nghiên cứu, chưa phải tài liệu yêu cầu |
| [nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md](nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) | Fit-gap thu mua và kho so với ERPNext v16, 52 chức năng | chưa ghi (đầu tệp: bản 1.0, 30/10/2026) |
| [nghien-cuu/erpnext-01-huong-dan-mua-hang-den-thanh-toan-va-kho.md](nghien-cuu/erpnext-01-huong-dan-mua-hang-den-thanh-toan-va-kho.md) | Hướng dẫn thao tác mua hàng tới thanh toán trên site học ERPNext | chưa ghi |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp |
| [tai-lieu-ky-thuat/tdd-bao-cao-thuc-hien-ycbg.md](tai-lieu-ky-thuat/tdd-bao-cao-thuc-hien-ycbg.md) | Thiết kế kỹ thuật Báo cáo thực hiện YCBG | chưa ghi (đầu tệp: bản 1.0, 12/09/2026) |

## Mã nguồn

- Backend: `backend/app/modules/purchase_request/`, `survey_request/`, `survey/`, `survey_progress/`, `purchase_order/`,
  `purchase_progress/`, `purchase_history/`, `payable/`, `payment_request/`, `supplier/`, `contract/`,
  `category_assignee/`, `goods_receipt/`; báo cáo ở `report/`.
- Giao diện v2: `frontend-v2/src/modules/procurement/`.
- Giao diện v1 (đóng băng, chỉ vá lỗi): `frontend/` — luật ở `.claude/rules/frontend-v1-frozen.md`.
- Luật cho người viết mã: `.claude/rules/backend-input-limits.md` (trần độ dài), mục phân quyền hai trục trong `CLAUDE.md`.
