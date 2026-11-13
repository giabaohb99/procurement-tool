# YÊU CẦU PHI CHỨC NĂNG — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.2 (13/11/2026: phần Kiêm nhiệm sửa theo hai loại dòng — duoc-CR-756) · 0.1 |
| Ngày | 13/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mới viết phần Kiêm nhiệm (duoc-CR-755, duoc-CR-756); các mục cho hồ sơ, nghỉ phép, hợp đồng, báo cáo chưa viết |
| CR liên quan | duoc-CR-755, duoc-CR-756 |

Mỗi yêu cầu một mã `PCN-HRM-NN`, ghi **mức đo được** và **cách kiểm**. Mục nào không áp dụng thì ghi *Không áp dụng* kèm lý do.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-HRM-01 | Hiệu năng | Dựng hồ sơ quyền đọc dòng kiêm nhiệm bằng MỘT truy vấn, số truy vấn không đổi theo số dòng; danh sách hồ sơ bật nhánh kiêm nhiệm vẫn một câu SQL (subquery tương quan); `GET /api/employee-concurrents` số truy vấn cố định, trần 200 dòng; cột **Kiêm nhiệm** của `GET /api/employees` nạp gom theo id của trang (số truy vấn cố định, không N+1) | Bài đếm truy vấn trong `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`, `test_kiem_nhiem_pham_vi_cap_cr755.py`, `test_kiem_nhiem_hien_thi_cr755.py`, `test_kiem_nhiem_doc_lap_cr756.py`, `test_kiem_nhiem_cot_danh_sach_cr756.py` | Đạt (local) |
| PCN-HRM-02 | Phân quyền | Không entity mới, dùng `employee` / `employee_sensitive`. Loại Phòng ban vào `dept_ids`; loại Công ty vào `concurrent_companies`, chỉ cộng ở bậc `company` (cả công ty B) và `dept` (phòng của họ ở B); `own` / `all` / `dept_proc` không đổi; chủ thể ACL thêm công ty B. `include_concurrent` chỉ ở đường ĐỌC hồ sơ một người, mặc định tắt. Ghi qua L1 / L2 theo loại (loại Công ty cần quyền ghi toàn công ty) / L3 | `test_kiem_nhiem_doc_lap_cr756.py`, `test_kiem_nhiem_doc_lap_ghi_cr756.py`, `test_kiem_nhiem_pham_vi_cap_cr755.py`, `test_pham_vi_*`, `test_pham_vi_luat_bat_bien.py` (BB4) | Đạt (local) |
| PCN-HRM-03 | Dữ liệu nhạy cảm | Tệp QĐ kiêm nhiệm của người khác cần `employee_sensitive.read`; bảng phòng B và danh bạ AI không có điện thoại / email / ngày sinh / lương | `test_kiem_nhiem_hien_thi_cr755.py` (soi khóa trả về) | Đạt (local) |
| PCN-HRM-04 | Giới hạn đầu vào | `decision_no` ≤ 50, `note` ≤ 500 (422), ngày 1900–2100, tối đa 30 dòng / người, `kind` chỉ 1 / 2 và đúng ô theo loại (422), tệp ≤ 50MB | Kiểm ở tầng schema, `test_canh_do_dai_o_chu_cr538.py` | Đạt (local) |
| PCN-HRM-05 | Nhật ký và truy vết | Thêm / sửa / xóa dòng ghi audit trên hồ sơ (`employee` update, câu *Thêm / Sửa / Xóa kiêm nhiệm: …*); đổi pháp nhân ghi số dòng đã kết thúc; mỗi lần mở / đóng phạm vi dòng loại Công ty ghi một dòng nhật ký riêng (`concurrent_scope_open` / `concurrent_scope_close`, N3); lô Nhập Excel hoàn tác được nhờ `_concurrent_ended` | `test_kiem_nhiem_luong_ghi_cr755.py`, `test_kiem_nhiem_doc_lap_ghi_cr756.py` | Đạt (local) |
| PCN-HRM-06 | Lưu trữ và dọn dữ liệu | Dòng đã hết GIỮ làm lịch sử (không dọn tự động); xóa hồ sơ dọn dòng + tệp | `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py` | Đạt (local) |
| PCN-HRM-07 | Sao lưu và khôi phục | Bảng trong DB chính; migration `kn756a` hạ về `kn755a` bỏ cột `kind` (dòng loại Công ty ở lại với phòng 0, không mở quyền), phòng đã bỏ khi chia loại không dựng lại được; `kn755a` hạ được nhưng mất dòng khác công ty, ngày, QĐ — sao lưu bảng trước khi hạ | `test_kiem_nhiem_migration_cr755.py`, bài migration trong `test_kiem_nhiem_doc_lap_ghi_cr756.py` | Đạt (local) |
| PCN-HRM-08 | Đồng thời | Chống chồng giai đoạn ở service (409) theo cùng phòng (loại Phòng ban) / cùng công ty (loại Công ty), khóa hàng hồ sơ trước khi kiểm trần 30 dòng và chồng giai đoạn; không có UNIQUE | `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`, `test_kiem_nhiem_doc_lap_ghi_cr756.py` | Đạt (local) |
| PCN-HRM-09 | Tích hợp | MCP `employee_lookup` trả `concurrent_roles` (không đổi tên / tham số; câu mỗi mục *Phòng X (Chức vụ)* / *Công ty B (Chức vụ)*) | Bài canh cổng MCP | Đạt (local) |
| PCN-HRM-10 | Khả dụng và thiết bị | Tab Kiêm nhiệm và hộp Thêm / Sửa có bố cục khổ điện thoại; cột **Kiêm nhiệm** ở danh sách có dòng thẻ điện thoại; đã soát 1440 và 390 | Ảnh `plans/reports/cr756-p03-*.png` | Đạt (local); Trang cá nhân `/me` chưa soát bằng mắt |
| PCN-HRM-11 | Pháp lý | Không áp dụng riêng cho kiêm nhiệm | | |
| PCN-HRM-12 | Vận hành | Không có việc chạy ngầm: trạng thái và phạm vi tính theo ngày lúc đọc; hết hạn lúc 0h còn tác dụng tối đa 60 giây (cache hồ sơ quyền) | | Đạt (thiết kế) |
