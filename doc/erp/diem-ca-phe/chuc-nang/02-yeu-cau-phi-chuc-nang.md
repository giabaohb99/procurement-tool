# YÊU CẦU PHI CHỨC NĂNG — ĐIỂM CÀ PHÊ (POS365)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Mỗi yêu cầu một mã `PCN-CP-NN`. Nguồn: [10-danh-sach-tinh-nang.md](10-danh-sach-tinh-nang.md) (*DS10*),
[02-bang-du-lieu.md](../tai-lieu-ky-thuat/02-bang-du-lieu.md), [03-tich-hop-pos365.md](../tai-lieu-ky-thuat/03-tich-hop-pos365.md)
(*TH03*), [04-phan-quyen.md](../tai-lieu-ky-thuat/04-phan-quyen.md) (*PQ04*), [lộ trình](../plans/06-lo-trinh-phase.md) (*LT06*)
và mã được ghi rõ ở từng dòng. Không có nguồn thì ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-CP-01 | Hiệu năng | Quầy trừ điểm một người thì dòng tiêu có trong sổ trong vòng 10 phút; đơn hủy ở quầy thì điểm hoàn trong vòng 1 giờ (điều kiện đủ CP4, tiêu chí 2 và 6 của LT06) | Thí điểm CP4 trên quán thật | Chưa đo (CP4 chưa chạy) |
| PCN-CP-02 | Phân quyền | Bốn entity `coffee_policy`, `coffee_member`, `coffee_ledger`, `pos_order` khai đủ `ENTITIES` và `SCOPE_FIELDS`; sổ và thành viên lọc theo `employee_id` để phạm vi `own` chạy thật; đọc lẻ theo id qua `get_scoped`. Ba quyền tách: xem sổ người khác, điều chỉnh tay, chạy đồng bộ; một vai trò không ôm cả ba trừ quản trị hệ thống. Ví của tôi chỉ cần đăng nhập (PQ04 §1–3) | `test_diem_ca_phe.py`, `test_pham_vi_khai_du_b07.py` | **Lệch đã biết:** menu đòi `coffee_member.delete` mà backend không gác hành động này, làm đỏ `test_dong_bo_giao_dien_v2.py` (LT06 nợ 16/09/2026) |
| PCN-CP-03 | Dữ liệu nhạy cảm | Tra cứu quầy chỉ trả `{tên, số dư}`, không ký tự đại diện, tối đa một người; tìm khách POS365 đã lọc trường `Password`; mật khẩu tài khoản API POS365 chỉ ở biến môi trường, không vào mã nguồn (PQ04 §4, DS10 N-01, api.md) | Chưa có bài kiểm riêng | Chưa đo |
| PCN-CP-04 | Giới hạn đầu vào | Điều chỉnh tay bắt buộc lý do (DS10 A-07); tự đặt nước chặn đặt quá số dư, trừ cấp vô hạn (LT06 bổ sung 08/09). Trần độ dài từng trường: theo `.claude/rules/backend-input-limits.md` | Kiểm ở tầng schema | Chưa đo |
| PCN-CP-05 | Nhật ký và truy vết | Mọi thay đổi số dư là một dòng sổ có người ghi; mọi thao tác (chính sách, thành viên, điều chỉnh, xử lý, chạy tay) ghi `audit`; mỗi lần đồng bộ một dòng `tab_pos_sync_run` (PQ04 §4, DS10 D-05) | `test_diem_ca_phe.py` | Chưa đo riêng |
| PCN-CP-06 | Lưu trữ và dọn dữ liệu | Sổ không UPDATE, không DELETE, sửa sai bằng dòng đảo ngược; không xóa cứng thành viên (DS10 C-01, B-04). Thời gian giữ: Chưa có | Chưa có | Chưa đo |
| PCN-CP-07 | Sao lưu và khôi phục | ERP là sổ cái duy nhất, POS365 không giữ số dư — mất CSDL ERP là mất số dư. Nằm trong bản sao lưu CSDL chung `backup.run` (`backend/app/core/celery_app.py`). Đường lui của thí điểm: bật lại `POS365_HARD_OFF`, sổ giữ nguyên (LT06 CP4) | Chưa có | Chưa đo |
| PCN-CP-08 | Đồng thời | Cột `uniq_key` gánh mọi lời hứa chống trùng: một người một kỳ đúng một dòng `grant`; UNIQUE `pos_order_id` nên kéo trùng vô hại; `refund` duy nhất theo đơn (DS10 A-04, D-01, D-03; [02-bang-du-lieu.md §4](../tai-lieu-ky-thuat/02-bang-du-lieu.md#4-tab_coffee_ledger--sổ-cái-điểm-c-01--chỉ-insert)) | `test_diem_ca_phe.py` | Chưa đo |
| PCN-CP-09 | Tích hợp | Mọi lời gọi POS365 đi qua một tệp `pos365_client.py`; gặp 401 đăng nhập lại đúng một lần rồi mới lỗi; cầu dao `POS365_HARD_OFF` từ chối mọi lời gọi ra ngoài; ba lần đồng bộ hỏng liên tiếp thì báo người phụ trách (TH03 §1–3, DS10 D-06). Kịch bản hỏng và đáp án ở [TH03 §6](../tai-lieu-ky-thuat/03-tich-hop-pos365.md#6-kịch-bản-hỏng--đáp-án-soát-lại-lúc-code-review-cp2) | `test_diem_ca_phe.py` | Chưa đo |
| PCN-CP-10 | Khả dụng và thiết bị | Chưa có yêu cầu | Chưa có | Chưa đo |
| PCN-CP-11 | Pháp lý | Thuế TNCN cho phúc lợi điểm: chưa trả lời, quyết định khuôn bàn giao kế toán (DS10 E-02) | Kế toán trả lời | Chưa có |
| PCN-CP-12 | Vận hành | Celery beat chỉ đăng khi `POS365_HARD_OFF` tắt: `coffee.pull_orders` mỗi `POS365_PULL_MINUTES` phút, `coffee.check_voids` phút 15 mỗi giờ, `coffee.monthly_reset` ngày 1 lúc 00:05, `coffee.reconcile` 06:00 (`backend/app/core/celery_app.py`) | `/api/system/jobs`; `GET /api/coffee/sync/runs` | Chưa đo |
