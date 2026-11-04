# Kịch bản test phân quyền — Phiếu Yêu cầu mua (PYC)

Đăng nhập bằng **mã NV** (hoặc email), **mật khẩu = mã NV**.

## Tài khoản test
| Vai trò | Đăng nhập | Mật khẩu | Kỳ vọng |
|---|---|---|---|
| Nhân sự thường (người yêu cầu) | `TESTREQ` | `TESTREQ` | Chỉ xem phiếu của mình; không thấy cột "Phân bổ NSTM" |
| Nhân viên thu mua | `NSU211` | `NSU211` | Xem phiếu của mình + được giao; chi tiết chỉ dòng của mình |
| Nhân viên thu mua | `NSU212` | `NSU212` | Tương tự NSU211 |
| Quản lý thu mua (duyệt, xem tất cả) | `NSU215` | `NSU215` | Xem tất cả; thấy & gán "Phân bổ NSTM"; có nút Duyệt |
| Admin thu mua | `NSU224` | `NSU224` | Như quản lý, toàn quyền mua hàng |
| Admin hệ thống | `degoadmin` | `dego2026` | Toàn quyền |

## Dữ liệu mẫu
- **PYCTEST1** — do TESTREQ tạo, trạng thái *Chờ duyệt*. 3 dòng:
  - Hàng A → phân bổ **NSU211**
  - Hàng B → phân bổ **NSU212**
  - Hàng C → *chưa phân bổ*
- **PYCTEST2** — do **NSU211** tự tạo, trạng thái *Nháp*. 1 dòng.

## Kịch bản & kết quả kỳ vọng
1. **TESTREQ** (nhân sự thường): danh sách **chỉ PYCTEST1**; mở chi tiết thấy **đủ 3 dòng** (phiếu của mình) nhưng **không có cột "Phân bổ NSTM"**; tạo phiếu mới được, chỉ mình thấy.
2. **NSU211**: danh sách thấy **PYCTEST2 (của mình) + PYCTEST1 (được giao)**; mở PYCTEST1 **chỉ thấy dòng Hàng A**; không có cột Phân bổ NSTM; không có nút Duyệt.
3. **NSU212**: chỉ thấy **PYCTEST1**, chi tiết **chỉ dòng Hàng B**.
4. **NSU215 / NSU210** (quản lý thu mua): thấy **tất cả phiếu, đủ dòng**; **thấy cột "Phân bổ NSTM"** và gán được; có **nút Duyệt** (PYCTEST1 đang chờ duyệt).
5. **degoadmin / NSU224**: toàn quyền, như quản lý.

## Kịch bản luồng (hay để test động)
- Đăng nhập **NSU215** → mở **PYCTEST1** → gán **Hàng C** cho **NSU211** → Lưu.
  → Đăng nhập lại **NSU211**: PYCTEST1 giờ hiện **thêm Hàng C**.
- Đăng nhập **NSU215** → **Duyệt** PYCTEST1 (nếu muốn test luồng duyệt).
- Đăng nhập **TESTREQ** → tạo 1 PYC mới → chỉ TESTREQ (và quản lý/admin) thấy.

> Lưu ý: mật khẩu tạm = mã NV — nhắc đổi sau khi test.
