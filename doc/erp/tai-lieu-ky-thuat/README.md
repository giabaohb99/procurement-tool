# TÀI LIỆU KỸ THUẬT — NỀN ERP V2

Bộ này mô tả **hệ thống SAU khi update** — nền ERP nhiều phân hệ chạy trên nhánh `erp-v2`
(giao diện `frontend-v2/`, backend dùng chung với bản cũ). Nó là bản song hành của
[`doc/tai-lieu-ky-thuat/`](../../tai-lieu-ky-thuat/README.md) — bộ đó mô tả **Mini Tool Thu mua v1**
(giao diện `frontend/`, 39 bảng thời điểm viết) và vẫn đúng cho phần lõi chưa đổi.

## Nội dung

| Tệp | Loại | Mô tả |
|---|---|---|
| [01-kien-truc-tong-the.md](01-kien-truc-tong-the.md) | TDD (tổng quan) | Kiến trúc v2: hai nhánh hai giao diện, các service Docker, khuôn module backend, bảng đăng ký phân hệ frontend, các luật nền đã chốt |
| [02-danh-muc-module.md](02-danh-muc-module.md) | Danh mục | 46 module backend + 20 phân hệ frontend-v2 — mỗi cái một dòng, thuộc cụm nào, trạng thái bật/tắt |
| [03-phan-quyen-va-hien-thi.md](03-phan-quyen-va-hien-thi.md) | Thiết kế | Hai trục phân quyền (hành động × phạm vi), hai bản seed, và tầng HIỂN THỊ: thẻ phân hệ mở/khóa theo quyền như thế nào |
| [04-so-do-kien-truc.md](04-so-do-kien-truc.md) | Sơ đồ | Sơ đồ Mermaid: triển khai ba môi trường, đường đi từ quyền trong DB tới thẻ phân hệ trên màn hình |
| [05-tu-dien-du-lieu.md](05-tu-dien-du-lieu.md) | LLD (chi tiết) | **Từ điển dữ liệu 101 bảng**, chia 5 tệp `05a`–`05e` theo cụm: đủ cột + kiểu + ý nghĩa + khóa nối + logic nghiệp vụ chính của từng bảng |
| [06a-man-hinh-nghiep-vu.md](06a-man-hinh-nghiep-vu.md) | Danh sách màn | **50 màn** phân hệ nghiệp vụ (Thu mua 20, Sản xuất 11, Kho 4, Tài chính 6, Nhân sự 9): route, tệp, mô tả, logic, quyền gác |
| [06b-man-hinh-van-thu-cong-tac-he-thong.md](06b-man-hinh-van-thu-cong-tac-he-thong.md) | Danh sách màn | **53 màn** Văn thư (24), Phê duyệt (4), Diễn đàn (5), Hỗ trợ, Trợ lý AI, Quản trị (9), Giao diện + màn ngoài phân hệ (đăng nhập, chọn phân hệ, thông báo...) |

## Quan hệ với các tài liệu khác — đọc cái nào khi nào

- **Nhật ký thay đổi (change-log / CR) DÙNG CHUNG một chỗ:** [`doc/tai-lieu-ky-thuat/change-log.md`](../../tai-lieu-ky-thuat/change-log.md).
  Bộ này KHÔNG có change-log riêng — hai nhật ký cho một kho mã là hai nguồn sự thật, sớm muộn lệch nhau.
- **Quy trình nhánh + deploy:** [`doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md`](../../tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md) — bắt buộc đọc trước khi đụng `main` hoặc VPS. Không chép lại ở đây.
- **Kế hoạch và quyết định** (vì sao làm, làm theo thứ tự nào) nằm ở các tệp đánh số của
  [`doc/erp/`](../README.md) (`07` vỏ ERP, `11`–`13` đa pháp nhân + màn còn lại, `15` đổ bê tông nền).
  Bộ này chỉ mô tả **hiện trạng kỹ thuật** — cái ĐÃ chạy, không phải cái SẼ làm.
- **Chi tiết từng bảng dữ liệu:** ở [`05-tu-dien-du-lieu.md`](05-tu-dien-du-lieu.md) (chỉ mục) +
  5 tệp `05a`–`05e` — 101 bảng sau 151 migration, đủ cột + ý nghĩa + logic. Khi từ điển lệch với
  `model.py` thì **mã đúng, từ điển sai**. Bản LLD 39 bảng của v1
  ([`thiet-ke-ky-thuat-chi-tiet.md`](../../tai-lieu-ky-thuat/thiet-ke-ky-thuat-chi-tiet.md)) giữ làm tham chiếu lịch sử.

## Nguyên tắc viết của bộ này

1. **Tầng kiến trúc (01–04) viết mức luật và VÌ SAO**, trỏ đường xuống mã; **tầng chi tiết (05–06)
   chép đủ cột/màn kèm ý nghĩa** — nhưng nguồn sự thật vẫn là mã nguồn, lệch nhau thì sửa tài liệu.
2. **Cái gì đổi cấu trúc thì có dòng CR** ở change-log chung, và cập nhật tệp tương ứng ở đây
   trong cùng đợt — đừng để dồn. Thêm bảng mới = thêm mục ở đúng tệp `05x`; thêm màn = thêm dòng ở `06x`.
3. Sơ đồ dùng **Mermaid**, xem trực tiếp trên GitHub/VS Code.
