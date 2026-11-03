# YÊU CẦU PHI CHỨC NĂNG — ĐẶT XE NỘI BỘ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-DX-NN`. Nguồn: [10-dat-xe.md](10-dat-xe.md) (*TL10*), [api.md](../tai-lieu-ky-thuat/api.md), bộ đồng
bộ app cũ ([README](../tai-lieu-ky-thuat/dong-bo-app-cu/README.md), [vận hành](../tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md))
và mã được ghi rõ ở từng dòng. Không có nguồn thì ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-DX-01 | Hiệu năng | Chưa có mức chốt. Ràng buộc thiết kế: nhãn xe / tài xế nối theo lô, tránh N+1 (TL10 mục C); báo cáo gom bằng SQL | `test_bao_cao_dat_xe_gom_sql.py`; ép tải `test_dat_xe_stress_luong_duyet.py` (30 ca) | Chưa đo thời gian phản hồi |
| PCN-DX-02 | Phân quyền | Khóa quyền: `vehicle_booking` (read / create / write / approve / delete / export), `vehicle`, `driver`. Phạm vi `vehicle_booking` theo `company_id` / `department_id` / `created_by`, nhánh `assigned` cho tài xế; công ty khớp cả `company_id` lẫn `requester_company_id`; `vehicle`, `driver` công khai (TL10 *Phạm vi dữ liệu*, mục A.10). Người đang giữ việc duyệt và người được chọn duyệt đọc được phiếu dù ngoài phạm vi, chỉ lúc việc còn treo | Kịch bản tay [kiem-thu/test-phan-quyen.md](../kiem-thu/test-phan-quyen.md); `test_dat_xe_chon_nguoi_duyet_cr681.py` | Có kịch bản kiểm |
| PCN-DX-03 | Dữ liệu nhạy cảm | Danh mục xe / tài xế thuê ngoài chứa mã số thuế, địa chỉ thuế, CCCD (TL10 mục D, E) và khai công khai trong phạm vi dữ liệu; ai được xem các trường này: Chưa có yêu cầu. Khóa bí mật đồng bộ chỉ nêu tên, màn cấu hình chỉ hiện *đã đặt / chưa đặt* (vận hành §3) | Chưa có | Chưa đo |
| PCN-DX-04 | Giới hạn đầu vào | Tiêu đề thư cắt 255 ký tự (TL10 mục A.10). Sự kiện đồng bộ lệch giờ quá 5 phút bị từ chối (vận hành §2). Trần độ dài từng trường: theo `.claude/rules/backend-input-limits.md` | Kiểm ở tầng schema | Chưa đo |
| PCN-DX-05 | Nhật ký và truy vết | Mọi thao tác ghi `audit`, hiện bằng *Lịch sử thao tác*; kết cục của luồng duyệt chép vào nhật ký của phiếu; mỗi sự kiện đồng bộ một dòng `tab_sync_log` (TL10, vận hành §2) | Chưa có bài kiểm riêng cho nhật ký | Chưa đo. Hoàn tác: Chưa có |
| PCN-DX-06 | Lưu trữ và dọn dữ liệu | Xóa phiếu là xóa mềm để không phá timeline và thống kê (api.md); xóa phiếu dọn luôn phiên duyệt trong cùng giao dịch (TL10 luật 5). Thời gian giữ: Chưa có | `test_dat_xe_stress_luong_duyet.py` | Chưa đo thời gian giữ |
| PCN-DX-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`). Dữ liệu app cũ nằm ở Firebase riêng dev và prod; tệp phiếu từ app cũ chỉ lưu liên kết (QĐ-E). Vòng `datxe.full_sweep` hằng đêm dựng lại dữ liệu suy ra | Chưa có | Chưa đo |
| PCN-DX-08 | Đồng thời | Cấp mã `DX` qua *cửa xoay* (khóa dòng + mã tạm duy nhất); trước khi sửa, 60 người gửi cùng lúc ra 57 lỗi 500 (TL10 mục A.10). Chống trùng giờ khi điều phối (PHA 6.3). Thư đẩy sau khi giao dịch ngoài cùng commit. Đồng bộ: nhận lại một việc đã làm thì không làm lại; đụng độ thì cú sau ghi đè theo giờ bấm (QĐ-J); lượt nhận khóa dòng trước khi phân xử (vận hành §8) | `test_dat_xe_chon_nguoi_duyet_cr681.py`, `test_dat_xe_thong_bao_va_chong_trung.py` | Sau sửa: Chưa đo lại bằng số |
| PCN-DX-09 | Tích hợp | App đặt xe cũ: webhook có chữ ký HMAC-SHA256, sổ đồng bộ hai đầu, ba vòng quét bù; mục tiêu không mất phiếu, không trùng, không lệch trạng thái ([đồng bộ mục 2](../tai-lieu-ky-thuat/dong-bo-app-cu/README.md#2-mục-tiêu)). Bộ máy duyệt dùng chung. Hàng thư Celery `notification.send_email`; worker chết thì dòng nằm `pending` | Tra phiếu theo [vận hành §4](../tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#4-tra-một-phiếu-sang-chưa-hỏng-vì-gì) | Sổ đồng bộ (vận hành bản 23/10/2026): dev 21 342 thành công, 0 lỗi; prod 11 356 thành công, 48 lỗi, đã xử 23/10/2026 (bao-CR-661) |
| PCN-DX-10 | Khả dụng và thiết bị | Chỉ có trên `frontend-v2`. Dùng trên điện thoại: Chưa có yêu cầu | E2E trình duyệt kịch bản 6 bước | Chưa làm E2E (tiến độ PHA 6) |
| PCN-DX-11 | Pháp lý | Chưa có | Chưa có | Chưa có |
| PCN-DX-12 | Vận hành | Celery beat: `datxe.pull_updated` (dev 3 phút, prod 5 phút), `datxe.retry_pending` (phút 3, 13, …), `datxe.full_sweep` 02:15, `datxe.retry_outbound` (phút 7, 17, …, kết thúc ngay khi công tắc gửi tắt), chuông sổ đồng bộ 08:00 cho dòng lỗi quá 24 giờ. Tắt khẩn cấp: công tắc `sync_datxe_enabled` (vận hành §2) | `/api/system/jobs`, `/system/sync-logs` | Đang chạy theo vận hành §1 |
