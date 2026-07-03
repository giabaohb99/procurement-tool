# TESTCASE-001 — Yêu cầu Thu mua (PYC) & Phân quyền

> Bộ test đầu tiên: tập trung luồng **Yêu cầu mua** và **phân quyền / phạm vi dữ liệu**.
> Các bộ sau tăng dần: `testcase-002`, `testcase-003`…
> URL Web: http://localhost:8080 · Đăng nhập bằng **Mã nhân viên** hoặc **Email** + mật khẩu.

---

## 1. Tài khoản test

Nhân viên: **username = mật khẩu = Mã nhân viên**. Admin: mật khẩu theo `.env` (`ADMIN_PASSWORD`, mặc định `dego2026`).

| # | Username | Mật khẩu | Họ tên | Vai trò | Phạm vi (PYC) | Quyền trên PYC |
|---|---|---|---|---|---|---|
| 1 | `degoadmin` | `dego2026` | Quản trị viên | Admin hệ thống | Tất cả | read, create, write, approve, cancel, delete |
| 2 | `TESTREQ` | `TESTREQ` | Nguyễn Văn Yêu Cầu | Nhân sự cơ bản (phòng **Kế toán**) | Của mình (own) | read, create |
| 3 | `NSU171` | `NSU171` | Nguyễn Minh Toàn | **Trưởng phòng Kế toán** | Phòng Kế toán (dept) | read, create, **approve** |
| 4 | `NSU211` | `NSU211` | Võ Trọng Tín | NV thu mua (phòng **Thu mua**) | Được giao (assigned) | read, create, write |
| 5 | `NSU215` | `NSU215` | Phạm Khánh Ngân | Quản lý thu mua | Tất cả | read, create, write, approve, **cancel** |
| 6 | `NSU224` | `NSU224` | Lâm Bích Dư | Admin thu mua | Tất cả | read, create, write, approve, cancel, delete |

> Ghi chú: TESTREQ thuộc phòng **Kế toán**; trưởng phòng Kế toán là **NSU171**. NSU211/NSU215 thuộc phòng **Sản xuất - Thu mua** (dùng để phân bổ NSTM).

---

## 2. Ma trận nút hành động mong đợi (trên màn chi tiết PYC)

| Nút | TESTREQ | NSU171 (TP) | NSU211 (NV TM) | NSU215 (QL TM) | admin |
|---|:--:|:--:|:--:|:--:|:--:|
| Lưu / Gửi duyệt (khi Nháp) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Duyệt / Từ chối** (khi Chờ duyệt) | ❌ | ✅ | ❌ | ✅ | ✅ |
| Phân bổ NSTM | ❌ | ✅ | ❌ | ✅ | ✅ |
| Đổi trạng thái dòng | ❌ | ✅ | ✅ (chỉ dòng của mình) | ✅ | ✅ |
| **Trả về / Hủy / Hoàn thành** | ❌ | ❌ | ❌ | ✅ | ✅ |
| Nhân bản | ✅ | ✅ | ✅ | ✅ | ✅ |
| Xóa phiếu | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 3. Test cases

Mỗi ca ghi: **Kết quả: ☐ Đạt / ☐ Không đạt** (điền khi chạy).

### Nhóm A — Tạo phiếu & tự động điền (tài khoản: `TESTREQ`)

**TC-A1 — Tự động điền khi tạo phiếu**
1. Đăng nhập `TESTREQ`. Vào **Yêu cầu mua → + Tạo mới**.
2. Quan sát các trường đầu phiếu.
- KQ mong đợi:
  - **Nhân sự YC** = "Nguyễn Văn Yêu Cầu", **bị khóa** (không sửa được).
  - **Bộ phận YC** = "Kế toán" (tự điền, khóa).
  - **Trưởng bộ phận (TBP)** = "Nguyễn Minh Toàn" (tự điền, khóa).
  - **Công ty nhận hóa đơn** = dropdown chọn được, có danh sách công ty.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-A2 — Thêm sản phẩm bằng tìm kiếm + ràng buộc bắt buộc**
1. Ở bảng sản phẩm, cột **Mã hàng**: gõ vài ký tự (mã hoặc tên) → chọn 1 SP.
2. Kiểm tra Tên/ĐVT/Phân loại tự điền; chọn **Kho nhận**, nhập **SL > 0**, **Đơn giá**.
3. Bấm **Lưu nháp**.
- KQ: lưu thành công, sinh **Mã phiếu** dạng `PYC…`. Nếu bỏ trống Kho nhận hoặc SL=0 → báo lỗi bắt buộc.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-A3 — Người yêu cầu KHÔNG có nút duyệt**
1. Mở lại phiếu vừa tạo bằng `TESTREQ`.
- KQ: **không thấy** nút Duyệt / Từ chối / Trả về / Hủy / Hoàn thành / Phân bổ. Chỉ có Lưu, Gửi duyệt, In, Nhân bản.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-A4 — Gửi duyệt**
1. Bấm **Gửi duyệt** phiếu ở TC-A2.
- KQ: trạng thái phiếu → **Chờ duyệt**; phiếu bị khóa sửa.
- Kết quả: ☐ Đạt / ☐ Không đạt

### Nhóm B — Duyệt theo phòng (tài khoản: `NSU171` — Trưởng phòng Kế toán)

**TC-B1 — Trưởng phòng thấy & duyệt phiếu phòng mình**
1. Đăng nhập `NSU171`. Vào **Yêu cầu mua**.
- KQ: thấy phiếu của `TESTREQ` (phòng Kế toán). Mở ra thấy nút **Duyệt / Từ chối**, **không** thấy Hủy / Trả về (chỉ có approve, không cancel).
2. Bấm **Duyệt**.
- KQ: trạng thái → **Đã duyệt**.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-B2 — Trưởng phòng KHÔNG thấy phiếu phòng khác (scope dept)**
1. (Chuẩn bị) Dùng admin tạo nhanh 1 phiếu ở phòng khác (vd bộ phận Thu mua).
2. Đăng nhập `NSU171`, xem danh sách Yêu cầu mua.
- KQ: **không** thấy phiếu thuộc phòng khác.
- Kết quả: ☐ Đạt / ☐ Không đạt

### Nhóm C — Phân bổ NSTM & trạng thái theo dòng (`NSU215`, `NSU211`)

**TC-C1 — Phân bổ nhân sự thu mua**
1. Đăng nhập `NSU215`, mở phiếu đã duyệt ở TC-B1.
2. Mở **chi tiết dòng** → ô **Nhân sự phụ trách**: dropdown chỉ hiện nhân sự **phòng Thu mua**, hiển thị **tên** (lưu mã). Chọn "Võ Trọng Tín" (NSU211). Lưu.
- KQ: lưu thành công, dòng gắn NSTM = NSU211.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-C2 — NV thu mua chỉ sửa dòng được giao & chỉ thấy dòng của mình**
1. Đăng nhập `NSU211`, mở phiếu đó.
- KQ: chỉ **thấy dòng được giao cho mình** (scope assigned). Trên bảng ngoài, ô **Trạng thái** của dòng đó là dropdown đổi được; dòng người khác không hiện/không sửa.
2. Đổi trạng thái dòng của mình sang "Đã đặt hàng".
- KQ: lưu tức thì.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-C3 — Trạng thái phiếu tự suy theo dòng**
1. Với 1 dòng ≠ "Chưa đặt hàng" → phiếu chuyển **Đang xử lý**.
2. Đưa **tất cả** dòng về "Hoàn thành" → phiếu tự **Hoàn thành**.
3. Đặt 1 dòng = "Hủy đơn" → ở **danh sách phiếu**, dòng phiếu bị **tô đỏ**.
- Kết quả: ☐ Đạt / ☐ Không đạt

### Nhóm D — Trả về / Hủy / Hoàn thành / Nhân bản (`NSU215` hoặc admin)

**TC-D1 — Trả về phiếu (về Nháp, reset)**
1. `NSU215` mở phiếu đang xử lý → **Trả về**, nhập lý do.
- KQ: phiếu → **Nháp**; **NSTM bị xóa**; **mọi dòng** về "Chưa đặt hàng".
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-D2 — Hủy phiếu = khóa cứng, không "Mở lại"**
1. `NSU215` mở 1 phiếu → **Hủy đơn**, nhập lý do.
- KQ: phiếu → **Đã hủy**, **không sửa được**, và **không có nút "Mở lại"**.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-D3 — Nhân bản phiếu đã hủy**
1. Ở phiếu đã hủy, bấm **Nhân bản**.
- KQ: mở **phiếu Nháp mới**, giữ nguyên dòng hàng, **NSTM rỗng**, trạng thái dòng = "Chưa đặt hàng", **mã PYC mới**.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-D4 — Hoàn thành phiếu**
1. `NSU215`/admin mở 1 phiếu đã duyệt/đang xử lý → **Hoàn thành**.
- KQ: phiếu → **Hoàn thành**.
- Kết quả: ☐ Đạt / ☐ Không đạt

### Nhóm E — Phạm vi dữ liệu & Menu theo quyền

**TC-E1 — Dropdown nhân sự bị giới hạn theo phòng**
1. `NSU211`/`NSU215` mở form phân bổ NSTM → dropdown chỉ có nhân sự **phòng Thu mua**.
2. `admin` mở → thấy **toàn bộ** nhân sự.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-E2 — Danh sách phiếu theo phạm vi**
1. `TESTREQ` xem Yêu cầu mua → chỉ thấy **phiếu do mình tạo** (own).
2. `admin` → thấy **tất cả** phiếu.
- Kết quả: ☐ Đạt / ☐ Không đạt

**TC-E3 — Menu ẩn theo quyền**
1. `TESTREQ` xem sidebar.
- KQ: thấy **Yêu cầu mua** + vài danh mục (Sản phẩm/Kho/ĐVT/Phân loại/Phòng ban/Công ty); **không** thấy Khảo sát / Hợp đồng / NCC / Công nợ / Phân quyền.
2. `admin` → thấy đầy đủ menu.
- Kết quả: ☐ Đạt / ☐ Không đạt

---

## 4. Bảng tổng hợp kết quả

| Mã | Nội dung | Đạt | Không đạt | Ghi chú |
|---|---|:--:|:--:|---|
| TC-A1 | Tự động điền khi tạo | ☐ | ☐ | |
| TC-A2 | Thêm SP + bắt buộc | ☐ | ☐ | |
| TC-A3 | Người YC không có nút duyệt | ☐ | ☐ | |
| TC-A4 | Gửi duyệt | ☐ | ☐ | |
| TC-B1 | TP duyệt phiếu phòng mình | ☐ | ☐ | |
| TC-B2 | TP không thấy phòng khác | ☐ | ☐ | |
| TC-C1 | Phân bổ NSTM | ☐ | ☐ | |
| TC-C2 | NV TM chỉ sửa/thấy dòng của mình | ☐ | ☐ | |
| TC-C3 | Trạng thái phiếu tự suy | ☐ | ☐ | |
| TC-D1 | Trả về phiếu | ☐ | ☐ | |
| TC-D2 | Hủy = khóa cứng | ☐ | ☐ | |
| TC-D3 | Nhân bản | ☐ | ☐ | |
| TC-D4 | Hoàn thành | ☐ | ☐ | |
| TC-E1 | Dropdown NS theo phòng | ☐ | ☐ | |
| TC-E2 | Danh sách phiếu theo scope | ☐ | ☐ | |
| TC-E3 | Menu ẩn theo quyền | ☐ | ☐ | |
