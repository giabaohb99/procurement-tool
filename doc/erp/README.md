# NỀN TẢNG ERP — BỘ TÀI LIỆU

Hướng: **giữ code Thu mua, gia cố, chia thành ERP nhiều phân hệ.** Vào web thấy lưới biểu tượng phân hệ, ai có quyền tới đâu thấy tới đó.

**Đọc trước tiên: [`00-ke-hoach-theo-module.md`](00-ke-hoach-theo-module.md)** — kế hoạch còn lại của toàn hệ, chia theo module và theo phase, kèm danh sách câu đang chờ quyết. Đây là tệp duy nhất ở cấp này; mọi tài liệu khác nằm trong thư mục phân hệ.

> Gọn lại ngày 22/10/2026: các kế hoạch tháng 8–9 (`01` ngắn hạn, `02` dài hạn, `04` danh mục chờ, `06` lộ trình nền tảng và HRM, `08` task củng cố, `10` báo cáo WorkHub, `11` đa pháp nhân, `13` đối chiếu màn v1↔v2, `19` việc còn lại) đã gộp phần chưa làm vào `00` rồi xóa. Cần đọc lại bản cũ thì xem lịch sử git trước commit gọn tài liệu.

## Thư mục theo phân hệ

| Thư mục | Nội dung |
|---|---|
| [`nen-tang/`](./nen-tang/) | Nền ERP v2: kiến trúc vỏ (`07`), phạm vi theo phòng ban (`12`), bộ lọc và sắp xếp (`14`), đổ bê tông nền (`15`), quản lý import/export (`16`), rà soát xóa cứng (`20`) |
| [`tai-lieu-ky-thuat/`](./tai-lieu-ky-thuat/README.md) | Hiện trạng kỹ thuật ERP v2: kiến trúc, danh mục module, phân quyền, từ điển dữ liệu, danh sách màn |
| [`thu-mua/`](./thu-mua/) | Thu mua: khối Báo cáo thực hiện trên YCBG (`18`) |
| [`nhap-khau/`](./nhap-khau/01-danh-sach-tinh-nang.md) | Hồ sơ và tiến độ nhập khẩu, chi phí thu mua |
| [`hai-quan/`](./hai-quan/) | Tra cứu thị trường (giá hải quan) |
| [`hrm/`](./hrm/README.md) | Nhân sự: hồ sơ, nghỉ phép, lịch làm việc, câu hỏi khảo sát (`03`). Cửa vào là `hrm/README.md` |
| [`tham-khao-hrm/`](./tham-khao-hrm/README.md) | Khảo sát HrOnline và đề xuất áp dụng |
| [`van-thu/`](./van-thu/README.md) | Văn thư và văn bản: 174 tính năng, lộ trình 10 phase, câu hỏi chờ chốt |
| [`cong-viec/`](./cong-viec/README.md) | Quản lý công việc (Dự án, clone Lark Tasks) |
| [`dien-dan/`](./dien-dan/00-pham-vi-va-ke-hoach.md) | Diễn đàn nội bộ |
| [`diem-ca-phe/`](./diem-ca-phe/README.md) | Điểm cà phê và POS365, chính sách phúc lợi điểm (`09`, `17`) |
| [`tai-lieu-ai/`](./tai-lieu-ai/01-kien-truc-tro-ly-ai.md) | AI: trợ lý, danh sách tool, bảo mật; kho skill AI qua MCP (`21`, `21a`); AI kế hoạch và phân việc (`22`) |
| [`san-xuat/`](./san-xuat/README.md) | Quản lý sản xuất — giai đoạn nghiên cứu nghiệp vụ |

Duyệt dấu, đặt xe và đồng bộ app đặt xe cũ nằm ở `doc/duyet-dau/`, `doc/dat-xe-duyet-dau/`, `doc/dong-bo-dat-xe-duyet-dau/`; dịch vụ AI và bot ở `doc/agent-hub/`.

## Ba quy tắc xuyên suốt

1. **Cơ sở dữ liệu cũ: chỉ thêm, không sửa.** Thu mua đang chạy thật, không có cửa sổ dừng hệ thống.
2. **Thu mua không được gián đoạn.** Mọi thay đổi giao diện phải có đường lui.
3. **Khai một chỗ, dùng nhiều chỗ.** Danh sách phân hệ, entity, sự kiện webhook khai báo đúng một nơi trong code.
