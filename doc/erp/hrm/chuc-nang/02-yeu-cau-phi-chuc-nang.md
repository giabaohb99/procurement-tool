# YÊU CẦU PHI CHỨC NĂNG — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 12/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mới viết phần Kiêm nhiệm (duoc-CR-755); các mục cho hồ sơ, nghỉ phép, hợp đồng, báo cáo chưa viết |
| CR liên quan | duoc-CR-755 |

Mỗi yêu cầu một mã `PCN-HRM-NN`, ghi **mức đo được** và **cách kiểm**. Mục nào không áp dụng thì ghi *Không áp dụng* kèm lý do.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-HRM-01 | Hiệu năng | Dựng hồ sơ quyền đọc dòng kiêm nhiệm bằng MỘT truy vấn, số truy vấn không đổi theo số dòng; danh sách hồ sơ bật nhánh kiêm nhiệm vẫn một câu SQL (subquery tương quan); `GET /api/employee-concurrents` số truy vấn cố định, trần 200 dòng | Bài đếm truy vấn trong `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`, `test_kiem_nhiem_pham_vi_cap_cr755.py`, `test_kiem_nhiem_hien_thi_cr755.py` | Đạt (local) |
| PCN-HRM-02 | Phân quyền | Không entity mới, dùng `employee` / `employee_sensitive`. Phạm vi theo CẶP (phòng, công ty): cặp khác công ty chỉ vào nhánh có ràng công ty; `include_concurrent` chỉ ở đường ĐỌC hồ sơ một người, mặc định tắt. Ghi qua L1 / L2 cặp / L3 | `test_kiem_nhiem_pham_vi_cap_cr755.py`, `test_pham_vi_*`, `test_pham_vi_luat_bat_bien.py` (BB4) | Đạt (local) |
| PCN-HRM-03 | Dữ liệu nhạy cảm | Tệp QĐ kiêm nhiệm của người khác cần `employee_sensitive.read`; bảng phòng B và danh bạ AI không có điện thoại / email / ngày sinh / lương | `test_kiem_nhiem_hien_thi_cr755.py` (soi khóa trả về) | Đạt (local) |
| PCN-HRM-04 | Giới hạn đầu vào | `decision_no` ≤ 50, `note` ≤ 500 (422), ngày 1900–2100, tối đa 30 dòng / người, `keep_concurrent_ids` ≤ 30, tệp ≤ 50MB | Kiểm ở tầng schema, `test_canh_do_dai_o_chu_cr538.py` | Đạt (local) |
| PCN-HRM-05 | Nhật ký và truy vết | Thêm / sửa / xóa dòng ghi audit trên hồ sơ (`employee` update, câu *Thêm / Sửa / Xóa kiêm nhiệm: …*); đổi pháp nhân ghi số dòng đã kết thúc; lô Nhập Excel hoàn tác được nhờ `_concurrent_ended` | `test_kiem_nhiem_luong_ghi_cr755.py` | Đạt (local) |
| PCN-HRM-06 | Lưu trữ và dọn dữ liệu | Dòng đã hết GIỮ làm lịch sử (không dọn tự động); xóa hồ sơ dọn dòng + tệp | `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py` | Đạt (local) |
| PCN-HRM-07 | Sao lưu và khôi phục | Bảng trong DB chính; migration `kn755a` hạ được nhưng mất dòng khác công ty, ngày, QĐ — sao lưu bảng trước khi hạ | `test_kiem_nhiem_migration_cr755.py` | Đạt (local) |
| PCN-HRM-08 | Đồng thời | Chống chồng giai đoạn ở service (409), không có UNIQUE (phòng dùng chung cần cùng phòng ở hai công ty) | `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py` | Đạt (local); hai lượt ghi cùng lúc chưa có khóa hàng |
| PCN-HRM-09 | Tích hợp | MCP `employee_lookup` trả `concurrent_roles` (không đổi tên / tham số) | Bài canh cổng MCP | Đạt (local) |
| PCN-HRM-10 | Khả dụng và thiết bị | Tab Kiêm nhiệm có thẻ khổ điện thoại; đã soát 1440 và 390 | Ảnh `plans/reports/cr755-p04-*.png` | Đạt (local); trang phòng ban + sơ đồ chưa soát bằng mắt |
| PCN-HRM-11 | Pháp lý | Không áp dụng riêng cho kiêm nhiệm | | |
| PCN-HRM-12 | Vận hành | Không có việc chạy ngầm: trạng thái và phạm vi tính theo ngày lúc đọc; hết hạn lúc 0h còn tác dụng tối đa 60 giây (cache hồ sơ quyền) | | Đạt (thiết kế) |
