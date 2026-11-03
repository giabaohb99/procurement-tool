# YÊU CẦU PHI CHỨC NĂNG — DUYỆT DẤU

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-DDAU-NN`. Nguồn: [10-duyet-dau.md](10-duyet-dau.md) (*TL10*), [tiến độ](../plans/duyet-dau-phase/tien-do.md),
[api.md](../tai-lieu-ky-thuat/api.md), tài liệu đồng bộ app cũ ở
[dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/README.md) và mã được ghi rõ ở từng
dòng. Không có nguồn thì ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-DDAU-01 | Hiệu năng | Chưa có | Chưa có | Chưa đo |
| PCN-DDAU-02 | Phân quyền | Khóa quyền: `seal_request` (read / create / write / approve / delete / export), `seal_type`; màn phân công văn thư dùng quyền `seal_type`. Phạm vi `seal_request` theo `company_id` / `department_id` / `created_by`; `seal_type` công khai (TL10 *Phạm vi dữ liệu*). Văn thư thấy phiếu theo bảng phân công văn thư. Người đang được giao duyệt đọc được chi tiết phiếu dù ngoài phạm vi (bao-CR-584, api.md) | `test_duyet_dau_phan_quyen.py` (ma trận nhân viên own · trưởng bộ phận dept · văn thư company · admin all), `test_duyet_dau_gom_cong_ty.py` | Có bài kiểm giữ (tiến độ PHA 5) |
| PCN-DDAU-03 | Dữ liệu nhạy cảm | Tệp chứng từ chữ ký sống chỉ xem qua đường có kiểm quyền, kế thừa quyền phiếu (`seal_request` read + phạm vi) (TL10 mục B) | Chưa có bài kiểm riêng | Chưa đo |
| PCN-DDAU-04 | Giới hạn đầu vào | Tệp `seal_request`: đuôi chứng từ chung, tối đa 50 MB (`backend/app/core/file_registry.py`). Loại con dấu: tên tối đa 100 ký tự, mô tả 255; lý do và ghi chú thao tác tối đa 1 000 ký tự (`backend/app/modules/seal_request/schema.py`). Số bản ≥ 1 (TL10 mục A.7). Luật chung: `.claude/rules/backend-input-limits.md` | Kiểm ở tầng schema | Chưa đo đủ mọi trường |
| PCN-DDAU-05 | Nhật ký và truy vết | Mọi thao tác ghi `audit`, hiện bằng khối *Lịch sử thao tác*; lý do yêu cầu chỉnh sửa / từ chối ghi thêm vào ghi chú (TL10 mục C) | Chưa có bài kiểm riêng cho nhật ký; luồng có `test_duyet_dau.py` (7 ca theo tiến độ) | Chưa đo. Hoàn tác: Chưa có |
| PCN-DDAU-06 | Lưu trữ và dọn dữ liệu | Có đường xóa phiếu (`seal_request.delete`); xóa mềm hay xóa cứng, thời gian giữ: Chưa có | Chưa có | Chưa đo |
| PCN-DDAU-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`). Tệp nằm ở kho tệp chung (R2 hoặc đĩa, TL10 mục B). Tệp của phiếu sang từ app cũ không chép nội dung, chỉ lưu liên kết về app cũ (QĐ-E của tài liệu đồng bộ) | Chưa có | Chưa đo |
| PCN-DDAU-08 | Đồng thời | Mỗi bước chuyển trạng thái kiểm trạng thái nguồn (TL10). Cấp mã `DD###` bằng lấy số lớn nhất cộng một (TL10 mục A.1); khả năng trùng mã khi nhiều người tạo cùng lúc: Chưa đo | Chưa có | Chưa đo |
| PCN-DDAU-09 | Tích hợp | Đồng bộ app đặt xe cũ: chiều nhận bật trên dev và prod, chiều gửi tắt; không mất phiếu, không trùng, không lệch trạng thái; lỗi nằm lại sổ đồng bộ để chạy lại ([tài liệu đồng bộ mục 2](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/README.md#2-mục-tiêu), [vận hành](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md)). Bộ máy duyệt dùng chung qua `ApprovalSwitch`. Thông báo chuông và email best-effort (tiến độ PHA 3) | `test_duyet_dau_luong_duyet_runtime.py`, `test_duyet_dau_thong_bao.py` | Sổ đồng bộ prod (23/10/2026, chung Đặt xe và Duyệt dấu): 11 356 thành công, 48 lỗi, đã xử 23/10/2026 (bao-CR-661, vận hành §7) |
| PCN-DDAU-10 | Khả dụng và thiết bị | Chỉ có trên `frontend-v2`. Điện thoại: Chưa có yêu cầu | Chưa có | Chưa đo. E2E trình duyệt cho luồng hai cổng chưa làm (tiến độ PHA 5) |
| PCN-DDAU-11 | Pháp lý | Hệ không sinh dấu điện tử; văn thư đóng dấu ngoài thực tế (quyết định đã chốt số 5). Văn bản luật áp dụng: Chưa có | Chưa có | Chưa có |
| PCN-DDAU-12 | Vận hành | Không có tác vụ Celery riêng; phiếu từ app cũ đi qua các vòng `datxe.*` dùng chung và chuông sổ đồng bộ 08:00 cho dòng lỗi quá 24 giờ ([vận hành §2](../../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md#2-hai-chiều-chạy-thế-nào-để-biết-tắt-cái-gì-khi-có-sự-cố)) | `/api/system/jobs` | Đang chạy theo tài liệu vận hành |
