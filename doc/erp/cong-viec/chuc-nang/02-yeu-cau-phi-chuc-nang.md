# YÊU CẦU PHI CHỨC NĂNG — CÔNG VIỆC (DỰ ÁN)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-CV-NN`. Nguồn: [04-phan-quyen.md](../tai-lieu-ky-thuat/04-phan-quyen.md) (*PQ04*),
[02-bang-du-lieu.md](../tai-lieu-ky-thuat/02-bang-du-lieu.md), [10-du-an-cong-viec.md](10-du-an-cong-viec.md) (*TL10*),
[lộ trình](../plans/03-lo-trinh-phase.md), [api.md](../tai-lieu-ky-thuat/api.md) và mã được ghi rõ ở từng dòng. Không có
nguồn thì ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-CV-01 | Hiệu năng | Chưa có mức chốt. Ràng buộc thiết kế: bảng kanban lấy cột, việc và mọi thứ vẽ trên thẻ trong một lượt gọi; cột nhiều việc tải theo trang (bao-CR-483); báo cáo gom bằng SQL ([api.md](../tai-lieu-ky-thuat/api.md)) | `test_bao_cao_cong_viec_gom_sql.py`, `test_stress_cong_viec_to_chuc_cr666_cr669.py`, `test_stress_viec_treo_cong_viec_cr665_667.py` | Chưa đo thời gian phản hồi |
| PCN-CV-02 | Phân quyền | Khóa quyền: `work_task` (gác cửa phân hệ); `setting.write` cho loại công việc. `SCOPE_FIELDS` khai `PUBLIC`, mọi truy vấn ở service bắt buộc tự lọc theo tư cách thành viên; `company_id` không còn là điều kiện đọc từ 15/09/2026 (PQ04 §1–2). Người ngoài bị chặn ở cả danh sách lẫn đọc theo id | Bảy bài kiểm bắt buộc ở PQ04 §5; `test_cong_viec_phan_quyen.py`, `test_pham_vi_khai_du_b07.py` | Có bài kiểm giữ (README cũ ghi 31 bài kiểm khóa tầng thành viên, 28/08/2026) |
| PCN-CV-03 | Dữ liệu nhạy cảm | Quản trị hệ thống chỉ thấy siêu dữ liệu dự án, muốn vào nội dung phải tự thêm mình và bị ghi audit (PQ04 §4). Tải tệp đính kèm bằng URL trần phải 401 / 403 (PQ04 §5 mục 4). Chuông chỉ tới người còn xem được việc ([lộ trình W3](../plans/03-lo-trinh-phase.md#w3--nối-vào-nền-thông-báo)) | `test_cong_viec_binh_luan_dinh_kem.py`, `test_cong_viec_chuong_cr666.py` | Cửa quản trị `/api/work/admin/...` của PQ04 §4 **chưa thấy** trong [api.md](../tai-lieu-ky-thuat/api.md): Chưa có |
| PCN-CV-04 | Giới hạn đầu vào | Tệp `work_task`: đuôi chứng từ và ảnh, tối đa 50 MB (`backend/app/core/file_registry.py`). Nhóm tối đa 2 cấp; việc con tối đa 2 cấp ([danh sách tính năng](11-danh-sach-tinh-nang.md) A-08, C-05). Trần độ dài từng trường: theo `.claude/rules/backend-input-limits.md` | Kiểm ở tầng schema | Chưa đo |
| PCN-CV-05 | Nhật ký và truy vết | Thao tác ghi qua `core/audit.py`, đọc ở tab Hoạt động cấp dự án; bình luận không ghi vào nhật ký này ([danh sách tính năng](11-danh-sach-tinh-nang.md) D-09). Quản trị tự thêm mình vào dự án phải ghi audit và hiện cho thành viên (PQ04 §4) | `test_cong_viec_hoat_dong.py` | Có. Lọc nhật ký theo một việc: Chưa có |
| PCN-CV-06 | Lưu trữ và dọn dữ liệu | *Xóa* dự án / nhóm là lưu trữ, không xóa hẳn; xóa việc là xóa mềm vào thùng rác, khôi phục được; việc con xóa cùng cha mang cùng mốc `deleted_at`; mũi tên phụ thuộc xóa cứng ([api.md](../tai-lieu-ky-thuat/api.md), lộ trình W3). Thời gian giữ thùng rác: Chưa có | `test_cong_viec_sua_binh_luan_thung_rac_cr667.py` | Chưa đo thời gian giữ |
| PCN-CV-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`); tệp ở kho tệp chung | Chưa có | Chưa đo |
| PCN-CV-08 | Đồng thời | Bất biến đúng một chủ sở hữu, chuyển quyền nguyên tử (PQ04 §5 mục 3); kéo thả đánh số lại cả cột đích ([api.md](../tai-lieu-ky-thuat/api.md)) | `test_cong_viec_keo_tha.py` | Hai người kéo cùng cột cùng lúc: Chưa đo |
| PCN-CV-09 | Tích hợp | Bình luận dùng `tab_comment` chung, đính kèm dùng `tab_file_link` chung, chuông ghi thẳng `tab_notification`, việc vào tab *Việc cần làm* qua `build_my_tasks`; lỗi chuông không làm hỏng thao tác chính (lộ trình W3). Nhắc hạn chạy ở dịch vụ AI (`agent.work_due`) | `test_cong_viec_chuong_cr666.py` | Chưa đo |
| PCN-CV-10 | Khả dụng và thiết bị | Chỉ có trên `frontend-v2`. Dùng trên điện thoại: Chưa có yêu cầu | [Kịch bản dùng thử](../kiem-thu/06-kich-ban-dung-thu.md) | Chưa đo |
| PCN-CV-11 | Pháp lý | Chưa có | Chưa có | Chưa có |
| PCN-CV-12 | Vận hành | Celery beat `agent.work_due` mỗi 5 phút, hết hạn sau 240 giây (`backend/app/core/celery_app.py`). Yêu cầu của lộ trình W4: nhắc hạn bắn đúng một lần mỗi ngưỡng, không lặp chuông mỗi lần beat chạy | `/api/system/jobs` | Chưa đo |
