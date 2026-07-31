# Mục lục chức năng — Mini Tool Quản lý Thu Mua

Danh sách toàn bộ tính năng trong hệ thống, lấy từ menu chính (`frontend/src/layouts/AppLayout.tsx`).
Mỗi dòng ghi trạng thái tài liệu và link tới file `.md` tương ứng trong thư mục `tai-lieu-chuc-nang/`.

---

## Nhóm: Tổng quan

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 1 | Trang chủ (Dashboard) | `/` | chưa có tài liệu |
| 2 | Báo cáo mua hàng | `/reports` | [08-he-thong-bao-cao.md](08-he-thong-bao-cao.md) — đã có tài liệu |

## Nhóm: Mua hàng

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 3 | Yêu cầu mua hàng (PYC) | `/purchase-requests` | [03-yeu-cau-mua-hang.md](03-yeu-cau-mua-hang.md) — đã có tài liệu |
| 4 | Yêu cầu báo giá (YCBG) | `/survey-requests` | [02-yeu-cau-khao-sat.md](02-yeu-cau-khao-sat.md) — đã có tài liệu (tên cũ: Yêu cầu khảo sát) |
| 5 | Đơn mua hàng (PO) | `/purchase-orders` | [04-don-mua-hang.md](04-don-mua-hang.md) — đã có tài liệu |

## Nhóm: Khảo sát

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 6 | Phiếu khảo sát | `/surveys` | [01-phieu-khao-sat.md](01-phieu-khao-sat.md) — đã có tài liệu |
| 7 | Báo cáo khảo sát | `/survey-report` | [08-he-thong-bao-cao.md](08-he-thong-bao-cao.md) — đã có tài liệu |

## Nhóm: Kho & Công nợ

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 8 | Tồn kho | `/inventory` | [06-ton-kho-cong-no.md](06-ton-kho-cong-no.md) — đã có tài liệu |
| 9 | Công nợ | `/payables` | [06-ton-kho-cong-no.md](06-ton-kho-cong-no.md) — đã có tài liệu |
| 10 | Yêu cầu thanh toán | `/payment-requests` | [05-yeu-cau-thanh-toan.md](05-yeu-cau-thanh-toan.md) — đã có tài liệu |

## Nhóm: Danh mục

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 11 | Nhà cung cấp | `/suppliers` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 12 | Sản phẩm | `/products` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 13 | Hợp đồng | `/contracts` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 14 | Kho | `/warehouses` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 15 | Đơn vị tính | `/units` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 16 | Phân loại | `/item-groups` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 17 | Phòng ban | `/departments` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 18 | Phân công phụ trách | `/category-assignees` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |

## Nhóm: Hệ thống

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 19 | Công ty | `/companies` | [07-danh-muc.md](07-danh-muc.md) — đã có tài liệu |
| 20 | Nhân sự | `/employees` | [08-he-thong-bao-cao.md](08-he-thong-bao-cao.md) — đã có tài liệu |
| 21 | Vai trò & Phân quyền | `/roles` | [08-he-thong-bao-cao.md](08-he-thong-bao-cao.md) — đã có tài liệu |
| 22 | Cấu hình hệ thống | `/settings` | [08-he-thong-bao-cao.md](08-he-thong-bao-cao.md) — đã có tài liệu |

## Nhóm: Người dùng cá nhân

| # | Chức năng | Đường dẫn | Tài liệu chức năng |
|---|-----------|-----------|-------------------|
| 23 | Thông báo (chuông + trang) | `/notifications` | [09-thong-bao-va-trang-ca-nhan.md](09-thong-bao-va-trang-ca-nhan.md) — đã có tài liệu |
| 24 | Trang cá nhân (thông tin + việc cần làm) | `/me` | [09-thong-bao-va-trang-ca-nhan.md](09-thong-bao-va-trang-ca-nhan.md) — đã có tài liệu |

---

## Ghi chú

- "đã có tài liệu" — file `.md` tương ứng đã tồn tại trong thư mục `tai-lieu-chuc-nang/`.
- "chưa có tài liệu" — chức năng đã hoạt động nhưng chưa viết tài liệu chi tiết.
- Danh mục (mục 11–18) và một phần Hệ thống là màn hình CRUD chuẩn, render tự động qua `CrudList` / `CrudDetail` theo cấu hình trong `frontend/src/config/cruds.tsx`.
- Tài liệu phân quyền chi tiết xem tại `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`.
- Nguồn danh sách: `frontend/src/layouts/AppLayout.tsx` — mảng `NAV_GROUPS`.
