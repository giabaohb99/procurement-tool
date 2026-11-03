# YÊU CẦU PHI CHỨC NĂNG — DIỄN ĐÀN NỘI BỘ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-DD-NN`. Nguồn: [10-giao-dien-va-logic-hien-thi.md](10-giao-dien-va-logic-hien-thi.md) (*GD10*),
[phạm vi và kế hoạch](../plans/00-pham-vi-va-ke-hoach.md) (*KH00*), [lộ trình](../plans/02-lo-trinh-phase.md) (*LT02*),
[api.md](../tai-lieu-ky-thuat/api.md) và mã được ghi rõ ở từng dòng. Không có nguồn thì ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-DD-01 | Hiệu năng | Quy mô thiết kế khoảng 300 tài khoản, giả định 15 000 bài / năm (GD10 đầu tệp). Ràng buộc: phân trang con trỏ, cấm OFFSET; không COUNT từng dòng; dữ liệu kèm bài gom theo trang, không hỏi từng bài (GD10 §4.3–4.4); ảnh thu nhỏ sinh lúc tải lên (LT02 nhật ký 27/08/2026). Mức thời gian phản hồi: Chưa có | `test_forum_api.py` | Chưa đo thời gian phản hồi |
| PCN-DD-02 | Phân quyền | Khóa quyền: `forum_post`, `forum_board` (chỉ cho thao tác quản trị); người dùng thường không cần vai trò. `forum_post` khai `PUBLIC` ở phạm vi dữ liệu, quyền đọc theo luật đối tượng xem lọc trong SQL; thiếu phòng ban / pháp nhân thì chặn (LT02 F1). Bài trong box theo đối tượng xem của box (QĐ-D7a) | `test_forum.py`, `test_forum_api.py`, `test_forum_board.py` | Có bài kiểm giữ |
| PCN-DD-03 | Dữ liệu nhạy cảm | Bài ẩn chỉ tác giả và quản trị thấy (LT02 F5); kết quả tìm kiếm tự lọc theo quyền xem (api.md) | `test_forum_search.py` | Có bài kiểm giữ |
| PCN-DD-04 | Giới hạn đầu vào | Bài chữ trơn tối đa 10 000 ký tự; bài có định dạng tối đa 40 000 ký tự tính cả thẻ; tiêu đề thread / tên box tối đa 255; tối đa 10 tệp mỗi bài; tệp ảnh hoặc `mp4` / `webm`, tối đa 50 MB mỗi tệp; dải ghim tối đa 50 bài (`backend/app/modules/forum/service.py`, `backend/app/core/file_registry.py`, KH00 D-Q3) | Bài kiểm ở `test_forum_api.py` | Đã khai trong mã; các trường còn lại theo `.claude/rules/backend-input-limits.md`: Chưa đo |
| PCN-DD-05 | Nhật ký và truy vết | Mọi lần ẩn / xóa / khôi phục ghi `tab_forum_moderation_log` kèm lý do và lúc báo tác giả (KH00 mục 4, LT02 F5) | `test_forum_api.py` | Có. Lịch sử sửa nội dung bài: Chưa có |
| PCN-DD-06 | Lưu trữ và dọn dữ liệu | Xóa kiểm duyệt chỉ đổi trạng thái sang *Đã xóa*, khác tác giả tự xóa (api.md); xóa nhóm / box chỉ khi rỗng; ẩn box là rút khỏi mắt, không xóa. Thời gian giữ: Chưa có | Chưa có | Chưa đo |
| PCN-DD-07 | Sao lưu và khôi phục | Điều kiện đủ của F6: bản sao lưu R2 đã phủ bảng mới (LT02 F6). Sao lưu CSDL chung `backup.run` (`backend/app/core/celery_app.py`) | Chưa có | Chưa đo |
| PCN-DD-08 | Đồng thời | Bày tỏ cảm xúc duy nhất theo (bài, người), không bấm đúp được (KH00 mục 4) | Chưa có | Chưa đo |
| PCN-DD-09 | Tích hợp | Hệ bình luận chung (CR-033), kho tệp chung, chuông và web push; Văn thư tạo bài thông báo khi ban hành (CR-200); Trung tâm trợ giúp sẽ thành tab (QĐ-D4, chưa làm) | `test_dang_thong_bao_dien_dan_khi_ban_hanh.py` | Chưa đo |
| PCN-DD-10 | Khả dụng và thiết bị | Ưu tiên điện thoại: các màn `/forum/*` phải co giãn tử tế, cột giữa về toàn chiều rộng, tab thành thanh dưới đáy; màn 375 px giấu dòng bài mới nhất (GD10 §1, LT02 F13b). Cài lên điện thoại qua PWA của ERP v2 | [Kịch bản dùng thử](../kiem-thu/04-kich-ban-dung-thu.md) trên điện thoại | Chưa ghi kết quả dùng thử |
| PCN-DD-11 | Pháp lý | Chưa có | Chưa có | Chưa có |
| PCN-DD-12 | Vận hành | Không có tác vụ Celery riêng của diễn đàn trong `backend/app/core/celery_app.py` | Không áp dụng | Không áp dụng |
