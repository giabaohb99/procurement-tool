# ĐIỂM CÀ PHÊ (POS365)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

## Phân hệ này là gì

Phúc lợi điểm cho quầy cà phê công ty: quầy bán trên POS365, nhân sự order và thanh toán bằng phương thức **Trừ điểm**
trên tài khoản điểm cá nhân; điểm cấp lại đầu mỗi tháng theo cấp nhân sự, không cộng dồn. ERP là sổ cái duy nhất,
POS365 không giữ số dư. Giao diện trên `frontend-v2`, gốc `/dego-coffee` (Ví của tôi, Chính sách, Thành viên và ghép,
Sổ và đối soát, Tra cứu quầy, Quản lý POS, Tự đặt nước; đường lấy từ `frontend-v2/src/shared/constants/app-routes.ts`,
tài liệu giao diện cũ còn ghi gốc `/retail/...`) — chi tiết ở [giao diện](chuc-nang/11-giao-dien.md) và
[lộ trình, phần bổ sung 08/09/2026](plans/06-lo-trinh-phase.md#bổ-sung-chiều-08092026--sếp-chốt-nghiệp-vụ--3-tính-năng-mới).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| CP0 POC trên cửa hàng thật `degocode` · CP1 nền dữ liệu và phân quyền · CP2 client POS365, sổ cái, tác vụ đồng bộ · CP3 giao diện | Đã có trong mã (08/09/2026); CP3 chưa đi trọn vòng dùng thử | [lộ trình](plans/06-lo-trinh-phase.md) |
| Quản lý POS, Tự đặt nước, cấp phát kỳ có người duyệt | Đã có trong mã (08/09/2026) | Đơn tự đặt đã chạy thật `HD080926-0007` |
| CP4 thí điểm trên quán thật | Chưa làm | Chặn cứng bởi các câu nghiệp vụ còn treo |
| CP5 mở rộng (soi gương số dư, menu, báo cáo, bàn giao kế toán, nhập CSV) | Chưa làm | |
| Lên prod | chưa ghi | Dev được đặt làm môi trường thí điểm (`POS365_HARD_OFF=false` ở dev, 08/09/2026) |

README cũ (08/09/2026) ghi *CHƯA viết code*; thông tin đó đã cũ, nay mã đã có (xem [api.md](tai-lieu-ky-thuat/api.md)).

**Câu nghiệp vụ còn treo** (cập nhật theo phần bổ sung 08/09/2026 của lộ trình): bộ cấp đã chốt 5 cấp nhưng **chưa có mức
điểm / tháng của 4 cấp thường**; cấp phát từng kỳ đã chốt **phải có người duyệt**; còn treo **âm điểm** (C-05) và **thuế
TNCN** (E-02).

**Ba luật một dòng (giữ từ README cũ):** sổ chỉ ghi thêm, mọi thay đổi số dư là một dòng sổ, kể cả sửa sai · không tự sửa
khi lệch, lệch lên màn hình cho người xử lý · `POS365_HARD_OFF` mặc định bật, chỉ môi trường được phép mới tắt.

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `coffee_point` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [tai-lieu-ky-thuat/02-bang-du-lieu.md](tai-lieu-ky-thuat/02-bang-du-lieu.md), [tai-lieu-ky-thuat/03-tich-hop-pos365.md](tai-lieu-ky-thuat/03-tich-hop-pos365.md), [tai-lieu-ky-thuat/04-phan-quyen.md](tai-lieu-ky-thuat/04-phan-quyen.md) |
| So sánh, khảo sát, câu hỏi chờ chốt | [chuc-nang/12-phuc-loi-diem-va-pos.md](chuc-nang/12-phuc-loi-diem-va-pos.md) (bản định hướng), [plans/17-ke-hoach-trien-khai-pos365-diem-ca-phe.md](plans/17-ke-hoach-trien-khai-pos365-diem-ca-phe.md) (bản quyết định phương án) |
| Kế hoạch đang làm / đã xong | [plans/06-lo-trinh-phase.md](plans/06-lo-trinh-phase.md) |
| Kịch bản kiểm thử tay | chưa có (điều kiện đủ của CP4 ở [lộ trình](plans/06-lo-trinh-phase.md#cp4--thí-điểm-trên-quán-thật--1-tháng-lịch-3-ngày-công-vận-hành)) |
| Hướng dẫn người dùng | chưa có bài trên Trung tâm trợ giúp |

Thứ tự ưu tiên khi các bản lệch nhau (giữ từ README cũ): bản định hướng `12` < bản quyết định `17` < bộ thiết kế thực thi
(`10`, `11`, `02`, `03`, `04`, `06`).

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-CP-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-CP-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-danh-sach-tinh-nang.md](chuc-nang/10-danh-sach-tinh-nang.md) | 31 tính năng chia 7 nhóm (N, A, B, C, D, E, G) | Bản 1.0, 08/09/2026 (kế hoạch) |
| [chuc-nang/11-giao-dien.md](chuc-nang/11-giao-dien.md) | Giao diện các màn của phân hệ | Bản 1.0, 08/09/2026 |
| [chuc-nang/12-phuc-loi-diem-va-pos.md](chuc-nang/12-phuc-loi-diem-va-pos.md) | Bản định hướng: phương án, câu nghiệp vụ, chỗ mất tiền thật | Bản 1.0, 12/08/2026 |
| [plans/06-lo-trinh-phase.md](plans/06-lo-trinh-phase.md) | Lộ trình CP0–CP5, phần bổ sung 08/09/2026, nợ phải dọn | Bản 1.0, 08/09/2026 |
| [plans/17-ke-hoach-trien-khai-pos365-diem-ca-phe.md](plans/17-ke-hoach-trien-khai-pos365-diem-ca-phe.md) | Bản quyết định phương án: thanh toán Trừ điểm, reset tháng | Bản 1.0, 07/09/2026 |
| [tai-lieu-ky-thuat/02-bang-du-lieu.md](tai-lieu-ky-thuat/02-bang-du-lieu.md) | 5 bảng, IntEnum, cấu hình, API | Bản 1.0, 08/09/2026 |
| [tai-lieu-ky-thuat/03-tich-hop-pos365.md](tai-lieu-ky-thuat/03-tich-hop-pos365.md) | Client POS365, thuật toán tác vụ, POC, kịch bản hỏng | Bản 1.0, 08/09/2026 |
| [tai-lieu-ky-thuat/04-phan-quyen.md](tai-lieu-ky-thuat/04-phan-quyen.md) | 4 entity, ma trận hành động, vai trò seed, chỗ dễ hở | Bản 1.0, 08/09/2026 |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |

## Mã nguồn

- Backend: `backend/app/modules/coffee_point/` (client POS365 nằm riêng ở `pos365_client.py`)
- Giao diện v2: `frontend-v2/src/modules/dego-coffee/`
- Luật cho người viết mã: chưa có tệp luật riêng
