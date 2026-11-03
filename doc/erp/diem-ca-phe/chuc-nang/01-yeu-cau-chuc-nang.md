# YÊU CẦU CHỨC NĂNG — ĐIỂM CÀ PHÊ (POS365)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

Tệp này là chỉ mục yêu cầu: mỗi chức năng tóm tắt ngắn rồi trỏ về tài liệu cũ. Mã tính năng gốc (N-01, A-01…) ở
[10-danh-sach-tinh-nang.md](10-danh-sach-tinh-nang.md) (gọi tắt là *DS10*) vẫn giữ nguyên; mã `CN-CP-NN` gom các mã gốc theo
chức năng. Trạng thái thi công lấy từ [lộ trình](../plans/06-lo-trinh-phase.md) (*LT06*), giao diện ở
[11-giao-dien.md](11-giao-dien.md) (*GD11*).

## 1. Người dùng và vai trò

Nguồn: [04-phan-quyen.md §3](../tai-lieu-ky-thuat/04-phan-quyen.md#3-vai-trò-seed-std_roles), `backend/app/seed.py`.

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Mọi nhân viên (không cần vai trò riêng) | Xem ví điểm của mình, tự đặt nước |
| Quản trị điểm cà phê (`coffee_admin`) | Chính sách, thành viên và ghép POS365, sổ điểm, điều chỉnh tay, xử lý đơn chưa khớp, chạy đồng bộ, chốt cấp phát kỳ |
| Quầy cà phê (`coffee_counter`) | Chỉ tra cứu tên và số dư của một thành viên |
| Tài chính (`coffee_finance`, tùy chọn, bản 2) | Xem và xuất sổ phục vụ báo cáo, bàn giao kế toán — chưa khai |

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là lộ trình ghi đã làm
xong trong mã nhưng không nói môi trường.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-CP-01 | Kết nối POS365: cấu hình, cầu dao `POS365_HARD_OFF`, phiên làm việc, tài khoản thanh toán *Trừ điểm* (DS10 N-01–N-04; [03-tich-hop-pos365.md §1–2](../tai-lieu-ky-thuat/03-tich-hop-pos365.md)) | Hệ thống, quản trị | Biến môi trường | chưa ghi (CP0, CP2 xong 08/09/2026) | |
| CN-CP-02 | Chính sách điểm theo cấp, đổi mức bằng dòng hiệu lực mới; bộ cấp 5 cấp (có cấp vô hạn điểm) (DS10 A-01, A-02; LT06 bổ sung 08/09) | Quản trị | `/dego-coffee/policies` | chưa ghi (mức điểm 4 cấp thường chưa khai) | |
| CN-CP-03 | Cấp phát kỳ có người duyệt: beat ngày 1 chỉ chạy dự kiến và nhắc, người duyệt xem trước rồi chốt; chống cấp trùng (DS10 A-03, A-04, A-06) | Quản trị (`coffee_ledger.approve`) | Nút *Cấp phát kỳ* | chưa ghi (chốt 08/09/2026) | |
| CN-CP-04 | Thu hồi điểm khi nghỉ việc và khóa thành viên (DS10 A-05, B-04) | Hệ thống | — | chưa ghi | |
| CN-CP-05 | Điều chỉnh tay có lý do bắt buộc, thành dòng `adjust` (DS10 A-07) | Quản trị | `/dego-coffee/ledger` | chưa ghi | |
| CN-CP-06 | Thành viên: gán cấp, ghép nhân sự với khách POS365 có người xác nhận từng cặp, tạo khách mới trên POS365, gỡ ghép (DS10 B-01–B-04; [GD11 §3](11-giao-dien.md)) | Quản trị | `/dego-coffee/members` | chưa ghi | |
| CN-CP-07 | Sổ cái điểm chỉ ghi thêm, sáu loại dòng, số dư là tổng sổ (DS10 C-01) | Hệ thống | — | chưa ghi | |
| CN-CP-08 | Ví điểm của tôi: số dư, đã cấp, lịch sử tiêu (DS10 C-02) | Mọi nhân viên | `/dego-coffee` | chưa ghi | |
| CN-CP-09 | Sổ điểm và đối soát: danh sách sổ lọc theo người / kỳ / loại, hàng chờ đơn không khớp, đối chiếu ngày, xử lý từng dòng (DS10 C-03, D-02, D-04) | Quản trị | `/dego-coffee/ledger` | chưa ghi | |
| CN-CP-10 | Tra cứu số dư cho quầy: gõ mã nhân viên / số điện thoại, chỉ trả tên và số dư (DS10 C-04) | Quầy | `/dego-coffee/lookup` | chưa ghi | |
| CN-CP-11 | Đồng bộ POS365: kéo đơn *Trừ điểm* định kỳ, soát đơn hủy để hoàn điểm, nhật ký đồng bộ, chạy tay, cảnh báo đồng bộ chết (DS10 D-01, D-03, D-05, D-06; [03-tich-hop-pos365.md §4](../tai-lieu-ky-thuat/03-tich-hop-pos365.md)) | Hệ thống, quản trị | Sổ đồng bộ | chưa ghi | |
| CN-CP-12 | Quản lý POS: số liệu hôm nay, doanh thu 7 ngày, đơn gần đây đọc thẳng từ POS365 (LT06 bổ sung 08/09) | Người có `pos_order.read` | `/dego-coffee/pos` | chưa ghi | |
| CN-CP-13 | Tự đặt nước: menu và ảnh đọc từ POS365, giỏ hàng, tạo đơn trả bằng *Trừ điểm*, chặn đặt quá số dư (LT06 bổ sung 08/09) | Mọi nhân viên | `/dego-coffee/order` | chưa ghi (đã chạy thật một đơn 08/09/2026) | |
| CN-CP-14 | Xử lý âm điểm (DS10 C-05) | — | — | Chưa (chờ nghiệp vụ chốt) | |
| CN-CP-15 | Soi gương số dư lên hồ sơ khách POS365 (DS10 D-07) | — | — | Chưa (chờ POC P5, xếp CP5) | |
| CN-CP-16 | Gán cấp hàng loạt bằng CSV / nhập xuất thành viên và sổ điểm (DS10 B-05) | — | — | Chưa (bản 2) | |
| CN-CP-17 | Đồng bộ menu quán về bảng chỉ đọc và báo cáo tiêu theo món (DS10 D-08, E-03) | — | — | Chưa (bản 2) | |
| CN-CP-18 | Báo cáo cấp / tiêu theo kỳ (DS10 E-01) | — | — | Chưa (bản 2) | |
| CN-CP-19 | Bàn giao kế toán (DS10 E-02) | — | — | Chưa (chờ trả lời thuế TNCN) | |

## 3. Chi tiết từng chức năng

### CN-CP-03 — Cấp phát kỳ

- **Luật nghiệp vụ:** mỗi người một kỳ đúng một dòng `grant`, khóa duy nhất ở tầng dữ liệu (cột `uniq_key`); chạy lại cùng kỳ
  không nhân đôi điểm; cấp vô hạn không cấp / thu kỳ nào; dòng `grant` mang người chốt làm dấu vết duyệt (DS10 A-03, A-04,
  LT06 bổ sung 08/09, [api.md](../tai-lieu-ky-thuat/api.md)).
- **Quyền:** `coffee_ledger.approve` (seed cho `coffee_admin`).

### CN-CP-06 — Thành viên và ghép POS365

- **Luật nghiệp vụ:** ghép một lần có người xác nhận, về sau chỉ đi theo `pos_partner_id`, không bao giờ tự ghép lại theo tên
  hay số điện thoại; số điện thoại trùng / rỗng để người quyết; không xóa cứng thành viên (DS10 nhóm B).
- **Quyền:** `coffee_member.create` / `write`.

### CN-CP-07 — Sổ cái chỉ ghi thêm

- **Luật nghiệp vụ:** không UPDATE, không DELETE; sửa sai bằng dòng đảo ngược; đường ghi sổ duy nhất là service
  `ledger_service.append` ([04-phan-quyen.md §4](../tai-lieu-ky-thuat/04-phan-quyen.md#4-chỗ-dễ-hở--soát-lúc-review-cp1cp2)).

### CN-CP-10 — Tra cứu cho quầy

- **Luật nghiệp vụ:** không nhận ký tự đại diện, không phân trang danh sách, chỉ trả khi khớp đúng mã nhân viên hoặc số
  điện thoại đủ, tối đa một người; trả đúng tên và số dư.
- **Quyền:** `coffee_member.read`.

### CN-CP-11 — Đồng bộ POS365

- **Luật nghiệp vụ:** kéo đơn tăng dần từ mốc đã kéo, trùng thì vô hại nhờ UNIQUE `pos_order_id`; đơn không khớp người nằm hàng
  chờ, hệ không đoán người; đơn hủy sinh dòng `refund` duy nhất theo đơn; lệch thì lên màn hình, không tự sửa (DS10 nhóm D,
  [03-tich-hop-pos365.md](../tai-lieu-ky-thuat/03-tich-hop-pos365.md)).
- **Quyền:** chạy tay `pos_order.write`; xử lý đơn chưa khớp `coffee_ledger.write`.

## 4. Luồng trạng thái chứng từ

Không có chứng từ duyệt nhiều bước. Sáu loại dòng sổ: `grant` · `expire` · `spend` · `refund` · `adjust` · `revoke` (DS10 C-01).
Cấp phát kỳ: *dự kiến* (xem trước, chưa ghi) → *chốt* (ghi cặp `expire` + `grant`).

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Mức điểm / tháng của 4 cấp thường (khai ở màn Chính sách) | Nghiệp vụ | chưa có |
| 2 | Âm điểm xử lý thế nào: trừ kỳ sau hay thu tiền (C-05) | Nghiệp vụ | chưa có |
| 3 | Thuế TNCN cho phúc lợi này, quyết định khuôn xuất bàn giao kế toán (E-02) | Kế toán | chưa có |
| 4 | Menu có mục xóa thành viên (`coffee_member.delete`) nhưng backend không gác hành động này — bỏ mục menu hay viết endpoint xóa ([LT06 nợ 16/09/2026](../plans/06-lo-trinh-phase.md#nợ-phải-dọn-khi-quay-lại-phân-hệ-này-ghi-16092026)) | chưa giao | chưa có |
