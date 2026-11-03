# YÊU CẦU PHI CHỨC NĂNG — NHẬP KHẨU

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-453, bao-CR-538 |

Mỗi yêu cầu một mã `PCN-NK-NN`. Phân hệ chưa có mã backend riêng: phần đã làm nằm trong `purchase_order`, nên nhiều
dòng dưới đây đi theo yêu cầu của Đơn mua hàng ở [thu mua 02](../../thu-mua/chuc-nang/02-yeu-cau-phi-chuc-nang.md). Chỗ
chưa có nguồn ghi *Chưa có* / *Chưa đo*.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-NK-01 | Hiệu năng | Chưa có con số mục tiêu. Báo cáo giá vốn lô nhập khẩu tính lúc xem (`report/import_landed_cost.py`) | Chưa có | Chưa đo |
| PCN-NK-02 | Phân quyền | Không có entity riêng cho đơn nhập khẩu và hồ sơ: dùng lại `purchase_order` (`read`, `write`, `approve`); danh mục loại chi phí dùng `purchase_cost_type` (phạm vi `PUBLIC`). Phạm vi của `tab_po_cost` đi theo đơn cha (`purchase_order` trong `SCOPE_FIELDS`), không khai riêng | `test/backend/test_po_chi_phi_thu_mua_cr453.py`, `test_po_cong_no_chi_phi_cr319.py`; [11 mục 7](11-chi-phi-thu-mua.md) | Chưa đo (chưa chạy lại) |
| PCN-NK-03 | Dữ liệu nhạy cảm | Đơn giá và chi phí chỉ người có `purchase_order.read` thấy. Tài liệu 10 ghi rủi ro: nếu sau này cho Pháp lý, Logistics tự tick hồ sơ thì họ sẽ thấy đơn giá; cách giảm là phạm vi dữ liệu, chưa làm (nợ kỹ thuật) | [10 mục 9](10-danh-sach-tinh-nang.md) | Chưa đo |
| PCN-NK-04 | Giới hạn đầu vào | Trường chữ của schema ghi ĐMH phải chặn độ dài ở tầng schema theo `.claude/rules/backend-input-limits.md`; số dòng chi phí tối đa mỗi đơn: Chưa có | `test/backend/test_canh_do_dai_o_chu_cr538.py` (có `purchase_order`) | Chưa đo |
| PCN-NK-05 | Nhật ký và truy vết | Chốt tạm tính, chốt quyết toán, mở lại giai đoạn, quyết toán và mở lại riêng dòng có mã hành động riêng (`cost_stage_prov`, `cost_stage_final`, `cost_stage_reopen`, `cost_line_final`, `cost_line_reopen`); `tab_change_log` ghi trước, sau cho `POCost`. Mở lại bắt ghi lý do | [11 mục 6.5](11-chi-phi-thu-mua.md) | Chưa đo |
| PCN-NK-06 | Lưu trữ và dọn dữ liệu | Đi theo ĐMH (xóa mềm `SoftDeleteMixin` ở `PurchaseOrder`). Dữ liệu cũ của bảng chi phí lô nhập khẩu được chuyển bằng migration `05a62d38a47a` | [thu mua 13 mục K.7](../../thu-mua/chuc-nang/13-don-mua-hang.md) | Chưa đo |
| PCN-NK-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run` trong `backend/app/core/celery_app.py`); tệp hồ sơ đính kèm đi theo `FileLink` của đơn | Chưa có | Chưa đo |
| PCN-NK-08 | Đồng thời | Chưa có | Chưa có | Chưa đo |
| PCN-NK-09 | Tích hợp | Dòng chi phí đã quyết toán sinh công nợ `source_type = import_cost` ở phân hệ Công nợ và đi vào YCTT; báo cáo giá vốn đọc `tab_po_cost`. Chi phí chưa đẩy vào giá tồn kho (chú thích `AllocationMethod`); tra cứu giá hải quan (`customs/`) chưa nối mã hàng | [thu mua 15 Luồng 3](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md); [nhận hàng nghiên cứu mục 4.2](../../nhan-hang/nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Chưa đo |
| PCN-NK-10 | Khả dụng và thiết bị | Hồ sơ nhập khẩu dự kiến làm trên cả `frontend-v2` và `frontend` (QĐ-B, ngoại lệ có chủ đích của luật đóng băng v1); thiết bị di động: Chưa có | [10 mục 6 nhóm F](10-danh-sach-tinh-nang.md) | Chưa đo |
| PCN-NK-11 | Pháp lý | Hồ sơ nhập khẩu bám thủ tục pháp lý, giấy phép theo báo cáo của Phòng Thu mua 11/09/2026 (khuôn *Phân bón thường* cho K₂SO₄ HS 3104.21.00, khuôn *Tiền chất thuốc nổ* cho KNO₃ HS 3102.60.00); căn cứ pháp lý gắn vào dòng khuôn để ở bản 2 (A07) | [10 mục 12](10-danh-sach-tinh-nang.md) | Chưa làm |
| PCN-NK-12 | Vận hành | Nhắc trước hạn, nhắc quá hạn hằng ngày và tổng hợp hằng tuần (E02, E03, E06) sẽ cần việc chạy ngầm; hiện chưa có việc nào trong Celery beat | [10 mục 6 nhóm E](10-danh-sach-tinh-nang.md) | Chưa làm |
