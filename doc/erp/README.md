# NỀN TẢNG ERP — BỘ TÀI LIỆU

Hướng: **giữ code Thu mua, gia cố, chia thành ERP nhiều phân hệ.** Vào web thấy lưới biểu tượng phân hệ, ai có quyền tới đâu thấy tới đó.

**Đọc trước tiên: [`00-ke-hoach-theo-module.md`](../plans/00-ke-hoach-theo-module.md)** — kế hoạch còn lại của toàn hệ, chia theo module và theo phase, kèm danh sách câu đang chờ quyết. Đây là tệp duy nhất ở cấp này; mọi tài liệu khác nằm trong thư mục phân hệ.

> Gọn lại ngày 22/10/2026: các kế hoạch tháng 8–9 (`01` ngắn hạn, `02` dài hạn, `04` danh mục chờ, `06` lộ trình nền tảng và HRM, `08` task củng cố, `10` báo cáo WorkHub, `11` đa pháp nhân, `13` đối chiếu màn v1↔v2, `19` việc còn lại) đã gộp phần chưa làm vào `00` rồi xóa. Cần đọc lại bản cũ thì xem lịch sử git trước commit gọn tài liệu.

## Thư mục theo phân hệ

Mỗi phân hệ một thư mục, cùng khuôn con `chuc-nang/ · tai-lieu-ky-thuat/ · nghien-cuu/ · plans/ · kiem-thu/ · du-lieu/`
và 4 tài liệu bắt buộc (`README.md`, `chuc-nang/01-yeu-cau-chuc-nang.md`, `chuc-nang/02-yeu-cau-phi-chuc-nang.md`,
`tai-lieu-ky-thuat/api.md`) — luật ở [`.claude/rules/chung-tai-lieu.md`](../../.claude/rules/chung-tai-lieu.md),
bảng toàn bộ phân hệ ở [`doc/README.md`](../README.md#phân-hệ-docerp).

| Thư mục | Nội dung |
|---|---|
| [`nen-tang/`](nen-tang/README.md) | Phần dùng chung giữa phân hệ: luồng duyệt, thông báo, phiếu hỗ trợ, bình luận, nhập / xuất, báo cáo, cấu hình, việc chạy ngầm; kiến trúc vỏ, đổ bê tông nền, bộ lọc |
| [`thu-mua/`](thu-mua/README.md) | Thu mua: YCBG, YCMH, ĐMH, công nợ, YCTT, danh mục, báo cáo thu mua, kịch bản kiểm thử |
| [`nhap-khau/`](nhap-khau/README.md) | Hồ sơ và tiến độ nhập khẩu, chi phí thu mua ba giai đoạn |
| [`kho/`](kho/README.md) · [`mat-hang/`](mat-hang/README.md) · [`nhan-hang/`](nhan-hang/README.md) · [`xuat-hang/`](xuat-hang/README.md) · [`lo-serial/`](lo-serial/README.md) | Kho và hàng hóa (mô hình dữ liệu sản phẩm ở `mat-hang/tai-lieu-ky-thuat/`), phần lớn đang ở mức nghiên cứu |
| [`hai-quan/`](hai-quan/README.md) | Tra cứu thị trường (giá hải quan) |
| [`hrm/`](hrm/README.md) | Nhân sự — người phụ trách HRM tự chuẩn hóa theo khuôn |
| [`tham-khao-hrm/`](tham-khao-hrm/README.md) | Khảo sát HrOnline và đề xuất áp dụng (chờ dời vào `hrm/nghien-cuu/`) |
| [`van-thu/`](van-thu/README.md) | Văn thư và văn bản |
| [`duyet-dau/`](duyet-dau/README.md) · [`dat-xe/`](dat-xe/README.md) | Duyệt dấu, đặt xe; đồng bộ app cũ ở `dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/` |
| [`cong-viec/`](cong-viec/README.md) | Dự án và công việc (clone Lark Tasks) |
| [`dien-dan/`](dien-dan/README.md) · [`diem-ca-phe/`](diem-ca-phe/README.md) | Diễn đàn nội bộ; điểm cà phê và POS365 |
| [`tro-ly-ai/`](tro-ly-ai/README.md) | Trợ lý AI, cổng MCP, Kho skill AI, AI kế hoạch và phân việc |
| [`san-xuat/`](san-xuat/README.md) | Quản lý sản xuất — giai đoạn nghiên cứu nghiệp vụ |
| [`crm/`](crm/README.md) | CRM — kế hoạch |
| [`nghien-cuu/`](nghien-cuu/) | Nghiên cứu ERPNext phần nhân sự còn chờ dời vào `hrm/nghien-cuu/` |

Dịch vụ AI và bot làm ra phần mềm ở `doc/agent-hub/`. Kế hoạch nhiều phân hệ ở `doc/plans/`.

## Ba quy tắc xuyên suốt

1. **Cơ sở dữ liệu cũ: chỉ thêm, không sửa.** Thu mua đang chạy thật, không có cửa sổ dừng hệ thống.
2. **Thu mua không được gián đoạn.** Mọi thay đổi giao diện phải có đường lui.
3. **Khai một chỗ, dùng nhiều chỗ.** Danh sách phân hệ, entity, sự kiện webhook khai báo đúng một nơi trong code.
