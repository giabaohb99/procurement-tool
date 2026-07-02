# Plan phân quyền — Phiếu Yêu cầu mua (PYC) + rà soát toàn hệ thống

> Làm PYC trước làm mẫu, sau đó rà các module khác. Đọc kèm `doc/Thiet_Ke_Phan_Quyen.md`.

## A. Mô hình quyền cho PYC

### A1. Ẩn/hiện phần "Phân bổ NSTM" (gán nhân sự thu mua)
- Cột **"Phân bổ NSTM"** (gán NSTM cho từng dòng hàng) + ô chọn người duyệt **chỉ hiện với: Admin, Quản lý thu mua, người có quyền DUYỆT PYC** (`can('purchase_request','approve')`).
- **Nhân sự thường** (chỉ tạo yêu cầu) và **Nhân viên thu mua khi tự tạo** → KHÔNG thấy cột này.
- Ô chọn NSTM (danh sách để phân bổ) = **chỉ nhân sự thuộc phòng Thu mua** ("Sản xuất -Thu mua"), không phải toàn bộ nhân viên. (Hiện đang lọc theo `role_name` chứa "thu mua" → đổi sang lọc theo phòng ban.)

### A2. Xem danh sách (ai thấy phiếu nào) — theo scope vai trò
| Đối tượng | Phạm vi | Ghi chú |
|---|---|---|
| Nhân sự (employee) | **Của mình** (own) | chỉ phiếu do mình tạo |
| Trưởng phòng | **Phòng ban** (dept) | phiếu cùng phòng |
| Quản lý công ty | **Công ty** (company) | phiếu cùng công ty |
| Quản lý/Admin thu mua | **Tất cả** (all) | |
| **Nhân viên thu mua** | **Được giao** (mới) | phiếu **của mình** HOẶC **được phân bổ cho mình** |

- Ba mức own/dept/company/all **đã chạy**. Cần thêm mức **"assigned" (được giao)** cho nhân viên thu mua:
  - Phiếu hiện nếu `created_by == mình` **hoặc** có dòng hàng `assignee == họ tên mình` **hoặc** `assignee_id == mã NV mình`.
  - Đây là scope RIÊNG cho PYC (và có thể PO), không nằm trên thang own→all.

### A3. Vào chi tiết — lọc dòng hàng theo phân bổ
- Nhân viên thu mua mở 1 phiếu (không phải do mình tạo) → **chỉ thấy các dòng hàng được phân bổ cho mình** (`item.assignee == họ tên mình`).
- Người tạo phiếu / quản lý / admin → thấy **tất cả** dòng.

### A4. Tạo yêu cầu
- Mọi nhân sự có quyền `create` → tạo được. (Nhân sự cơ bản đã có create PYC scope own.)

## B. Rà soát toàn hệ thống (các module khác)
Nguyên tắc: **API nào trả dữ liệu ra đều phải qua `require(entity, action)`; thao tác nào cũng gắn quyền tương ứng; FE ẩn nút theo quyền.**
- **Khảo sát (survey):** list/detail gate `require('survey','read')`; scope theo own/all (người khảo sát thấy của mình; quản lý thấy tất cả). Nút Tạo/Sửa/Duyệt theo quyền.
- **Hợp đồng, Nhà cung cấp, Sản phẩm, Kho, ĐVT, Phân loại, Phòng ban, Công ty:** là **danh mục dùng chung** → chỉ cần gate `read` (đã có); ẩn nút Thêm/Sửa/Xóa theo `create/write/delete`. Không lọc theo phạm vi (mọi người có quyền xem đều thấy đủ).
- **Đơn mua hàng / Công nợ / Tồn / Thanh toán:** đã áp scope; rà thêm nút thao tác trên FE theo quyền.
- **Dropdown/nguồn dữ liệu** (chọn NCC, sản phẩm, kho…): các endpoint này đã có `require(...,'read')`; người không có quyền xem entity đó sẽ không lấy được list → cần đảm bảo FE các form vẫn chạy (nếu 1 vai trò cần tạo PYC nhưng không có quyền xem sản phẩm thì phải cấp read sản phẩm cho vai trò đó — đã cấp trong seed).

## C. Cần chốt trước khi code
1. **"Phân bổ NSTM"** = cột gán nhân sự thu mua cho từng dòng hàng — chỉ Admin/Quản lý/người duyệt thấy. Đúng không?
2. **Khớp "được phân bổ cho mình"**: hiện `item.assignee` lưu **họ tên**. Match theo họ tên user. (Đề xuất dài hạn: đổi sang **mã NV** cho chắc — nhưng cần sửa chỗ lưu.) Tạm match họ tên OK chứ?
3. **Nhân viên thu mua** dùng scope mới **"Được giao"** thay cho "Phòng ban" hiện tại. OK?

## D. Thứ tự triển khai (sau khi chốt)
1. FE PYC: ẩn cột "Phân bổ NSTM" + ô duyệt nếu không có quyền `approve`; nguồn NSTM = phòng thu mua.
2. BE: thêm scope **"assigned"**; đổi vai trò `pur_staff` PYC sang scope này; enforce list (`apply_scope`).
3. BE: lọc dòng hàng trong chi tiết PYC theo `assignee` cho nhân viên thu mua.
4. Rà FE ẩn nút theo `can()` ở các màn; rà `require()` ở mọi endpoint list/detail còn thiếu.
5. (Sau) chuyển `item.assignee` sang mã NV nếu chốt.
