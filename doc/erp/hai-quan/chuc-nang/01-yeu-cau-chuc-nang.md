# YÊU CẦU CHỨC NĂNG — TRA CỨU THỊ TRƯỜNG (GIÁ HẢI QUAN)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-470 · bao-CR-481 · bao-CR-493..496 · bao-CR-500 · bao-CR-503 · bao-CR-541 · bao-CR-603 · bao-CR-608 |

Tệp này là **mục lục chức năng**: mỗi dòng gom một hoặc vài mã tính năng gốc (N-xx, T-xx, B-xx, A-xx, P-xx, Y-xx) của
[`10-danh-sach-tinh-nang.md`](10-danh-sach-tinh-nang.md) và trỏ tới chỗ giữ chi tiết. Mã gốc giữ nguyên, không đổi số.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người được tick quyền xem (`customs_price.read`) | Tra cứu, lọc, xem biểu đồ, so sánh, xuất Excel; thấy **toàn bộ** dữ liệu, không lọc theo phòng / công ty. Đại ca tick cho Quản lý thu mua, Admin thu mua, Nhân sự thu mua ([`10`](10-danh-sach-tinh-nang.md) §9 Q1, Q3) |
| Người được nạp dữ liệu (`customs_price.import` / `write`) | Nạp tệp GTT02, chạy thử, hoàn tác lô, sửa / xóa từng dòng |
| Người giữ danh mục pháp lý (`customs_regulation.*`) | Sửa danh mục hóa chất theo văn bản khi văn bản đổi |
| Người giữ danh mục thuốc BVTV (`customs_pesticide.*`) | Nạp, sửa danh mục thuốc BVTV |
| Quản trị | Sửa từ khóa nhãn Thành phẩm / Nguyên liệu, từ đồng nghĩa, mã công thức ở thẻ Cấu hình |

Hệ thống không tự cấp vai trò nào: đại ca tự tick trên màn Phân quyền (Q1, chốt 23/09/2026).

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**. *chưa ghi* = tài liệu nguồn
không nói rõ. Các dòng *Có* lấy từ mục *Đã có* §3 của [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md):
HQ1..HQ5 và cụm yêu cầu chị Mi lên prod 01/10/2026, có bộ lọc đã lưu.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-HQ-01 | Nạp tệp GTT02 theo lô: đọc `.xls` đời cũ, vá cột ngày đăng ký bị đảo, quy đơn vị / tiền, chạy thử, hoàn tác lô, tải lại tệp gốc, log từng dòng — [`10`](10-danh-sach-tinh-nang.md) N-01..N-05, N-08, Y-04, Y-05, Y-13; [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §3.1, §4 | Người nạp | Hộp nạp, thẻ Lịch sử nạp | Có | bao-CR-470 · bao-CR-493 · bao-CR-496 |
| CN-HQ-02 | Chống trùng bằng mã băm và gộp dòng trùng — [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §4.5 | Hệ thống | Lúc nạp; việc chạy ngầm | chưa ghi | bao-CR-541 |
| CN-HQ-03 | Cột tùy chọn trên tệp nạp (hoạt chất, hàm lượng, hai giá VND) — [`10`](10-danh-sach-tinh-nang.md) N-09 | Người nạp | Hộp nạp | chưa ghi | bao-CR-603 |
| CN-HQ-04 | Tra cứu và lọc: tên hàng, mã HS, xuất xứ, thời gian, đơn vị, doanh nghiệp / đối tác chọn nhiều, hàng *Lọc thêm*, tìm *Có các từ* / *Không có từ*, quy đổi cách viết nồng độ, từ đồng nghĩa — [`10`](10-danh-sach-tinh-nang.md) T-01, Y-06, Y-07, Y-09..Y-11; [`11`](11-giao-dien.md) §2 | Người xem | Thẻ Danh sách | Có | bao-CR-470 · bao-CR-493 · bao-CR-495 · bao-CR-503 |
| CN-HQ-05 | Gom số theo kết quả tìm (giá thấp / cao / bình quân gia quyền theo lượng, lượng cộng dồn, số dòng hàng, lần nhập gần nhất) — [`10`](10-danh-sach-tinh-nang.md) T-02 | Người xem | Thẻ Danh sách | Có | bao-CR-470 |
| CN-HQ-06 | Chi tiết một dòng hàng đủ 32 trường — [`10`](10-danh-sach-tinh-nang.md) T-03; [`11`](11-giao-dien.md) §3 M2 | Người xem | Hộp chi tiết dòng | Có | bao-CR-470 |
| CN-HQ-07 | Cột ID, sửa / xóa từng dòng, ghi đè theo ID khi nạp, hoàn tác lô trả lại dòng đã ghi đè — [`10`](10-danh-sach-tinh-nang.md) Y-17 | Người nạp | Bảng Giá thị trường, tệp nạp | chưa ghi | bao-CR-608 |
| CN-HQ-08 | Chọn giá hiệu lực (ưu tiên giá điều chỉnh) và hai cột đơn giá quy đổi VND — [`10`](10-danh-sach-tinh-nang.md) N-06, Y-01, Y-02 | Người xem | Bảng, chi tiết dòng, Excel | Có | bao-CR-493 |
| CN-HQ-09 | Biểu đồ giá và lượng theo kỳ tháng / quý / năm, cảnh báo độ tin cậy mùa vụ, dải tháng đã phủ — [`10`](10-danh-sach-tinh-nang.md) B-01..B-04, Y-03; [`11`](11-giao-dien.md) §2.2, §4 | Người xem | Thẻ Biểu đồ (chỉ hiện khi đã lọc) | Có | bao-CR-470 · bao-CR-493 |
| CN-HQ-10 | So sánh 2–5 mặt hàng trên cùng biểu đồ — [`10`](10-danh-sach-tinh-nang.md) B-05 | Người xem | Thẻ So sánh | Có | bao-CR-470 |
| CN-HQ-11 | Tra theo hoạt chất và nhãn tự động Thành phẩm / Nguyên liệu — [`10`](10-danh-sach-tinh-nang.md) T-04, Y-08; [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §10.1 | Người xem | Thẻ Danh sách | Có | bao-CR-470 · bao-CR-494 |
| CN-HQ-12 | Bảng xếp hạng nhà nhập khẩu — [`10`](10-danh-sach-tinh-nang.md) T-05 | Người xem | Thẻ Nhà nhập khẩu | Có | bao-CR-470 |
| CN-HQ-13 | Xuất Excel kết quả tra cứu: **xuất ngay** tới 50.000 dòng, hoặc **xuất toàn bộ chạy nền** (theo bộ lọc đang chọn, bỏ trống = cả bảng) chia tệp 50.000 dòng, chuông khi xong, màn tải từng tệp — [`10`](10-danh-sach-tinh-nang.md) T-06 | Người có `customs_price.export` | Thẻ Danh sách; màn Lô xuất | Có | bao-CR-470 · bao-CR-718 |
| CN-HQ-14 | Lưu bộ lọc riêng từng người (có sẵn cột dùng chung, mặc định tắt) — [`10`](10-danh-sach-tinh-nang.md) Y-12; [`05`](../plans/05-giao-viec-cr496-luu-bo-loc-log-dong.md) | Người xem | Thanh lọc | Có | bao-CR-496 |
| CN-HQ-15 | Danh mục hóa chất theo văn bản có ngưỡng (NĐ 24/2026 phụ lục I–IV, TT 75/2025, TT 01/2026), màn duyệt cả danh mục — [`10`](10-danh-sach-tinh-nang.md) P-01; [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §10.2 | Người xem; người giữ `customs_regulation` | Thẻ Pháp lý | chưa ghi | bao-CR-470 |
| CN-HQ-16 | Tra nghĩa vụ theo hoạt chất / CAS / công thức — [`10`](10-danh-sach-tinh-nang.md) P-03 | Người xem | Thẻ Pháp lý | chưa ghi | bao-CR-470 |
| CN-HQ-17 | Biểu thuế XNK theo mã HS — [`10`](10-danh-sach-tinh-nang.md) P-04 | Người xem | Thẻ Thuế | chưa ghi | bao-CR-470 |
| CN-HQ-18 | Cảnh báo pháp lý ngay lúc tra khi từ khóa trùng hóa chất cấm / có ngưỡng / phải công bố — [`10`](10-danh-sach-tinh-nang.md) P-02 (phần làm thay) | Người xem | Dải cảnh báo trên màn tra cứu | chưa ghi | bao-CR-470 |
| CN-HQ-19 | Cảnh báo khi tồn kho chạm ngưỡng — [`10`](10-danh-sach-tinh-nang.md) P-02 | Thu mua, kho | — | Chưa | — |
| CN-HQ-20 | Danh mục thuốc BVTV và phạm vi sử dụng, nạp tệp ngay trên màn — [`11`](11-giao-dien.md) đầu tệp (cập nhật 29/09/2026) | Người xem; người giữ `customs_pesticide` | Thẻ Thuốc BVTV | chưa ghi | duoc-CR-486..488 |
| CN-HQ-21 | Công cụ trợ lý AI: tra giá, thời điểm mua và đánh giá *có nên mua lúc này*, thị trường, pháp lý — [`10`](10-danh-sach-tinh-nang.md) A-01..A-03, A-05..A-08; [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §10.4 | Trợ lý web, MCP (nhóm `customs`) | Trong câu trả lời | Có | bao-CR-470 · bao-CR-481 |
| CN-HQ-22 | Bài hướng dẫn sử dụng — [`10`](10-danh-sach-tinh-nang.md) A-04 | Mọi người | Trung tâm trợ giúp | chưa ghi | bao-CR-470 |
| CN-HQ-23 | Cấu hình: từ khóa nhãn, từ đồng nghĩa, mã công thức; nạp cấu hình bằng script — [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §11 | Quản trị | Thẻ Cấu hình | chưa ghi | duoc-CR-684 |
| CN-HQ-24 | Excel theo mẫu công ty — [`10`](10-danh-sach-tinh-nang.md) Y-14 | Người xem | — | Chưa | — |
| CN-HQ-25 | In báo giá, xuất PDF — [`10`](10-danh-sach-tinh-nang.md) Y-15 | Người xem | — | Chưa | — |
| CN-HQ-26 | Biểu đồ theo tuần — [`10`](10-danh-sach-tinh-nang.md) Y-16 | Người xem | — | Chưa | — |
| CN-HQ-27 | Khối lịch sử thao tác trên trang (xuất Excel, sửa cấu hình, gắn lại nhãn) — [`06`](../nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md) §7 N5 | Người xem | — | Chưa | — |

## 3. Chi tiết từng chức năng

### CN-HQ-01 — Nạp tệp GTT02 theo lô

- **Mục đích:** đưa dữ liệu tờ khai do bên ngoài kết xuất vào hệ, không sai im lặng.
- **Luồng chính:** chọn một hoặc nhiều tệp (một lô = một tệp) → chạy thử, xem số dòng sẽ thêm / thay → ghi thật → xem
  lịch sử lô, log từng dòng (Thêm mới / Lỗi / Bỏ qua vì trùng), hoàn tác lô nếu sai.
- **Luật nghiệp vụ:** dữ liệu không có số tờ khai nên không có khóa duy nhất; nạp lô mới trùng khoảng ngày thì xóa khoảng đó
  rồi nạp lại. Chỉ vá cột *Ngày đăng ký* (ô kiểu số đảo ngày / tháng), **không** vá cột *Ngày hợp đồng*. Tiền dùng thẳng
  cột giá USD; đơn vị không quy đổi trừ `TNE → KGM`. Chi tiết: [`10`](10-danh-sach-tinh-nang.md) N-03..N-05 và
  [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §4.
- **Dữ liệu:** dùng lại `tab_import_batch` + `tab_import_log` của khung nhập chung (`ImportModule.CUSTOMS_DECLARATION = 3`),
  lô hiện cả ở màn `/system/imports` ([Nền tảng](../../nen-tang/chuc-nang/01-yeu-cau-chuc-nang.md) CN-NT-10).
- **Quyền:** `customs_price.import` / `write`.
- **Ngoại lệ:** hai tệp cùng khoảng ngày nhưng khác nhóm hàng thì tệp sau xóa dòng của tệp trước (rủi ro R1,
  [`06`](../nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md) §6).

### CN-HQ-04 — Tra cứu và lọc

- **Mục đích:** tìm nhanh mặt hàng / hoạt chất trong dữ liệu chữ tự do (tên hàng trung bình 165 ký tự).
- **Luật nghiệp vụ:** không gom theo tên hàng từng chữ (83% tên chỉ xuất hiện một lần); gom theo tập dòng khớp lần tìm.
  Trạng thái rỗng phải nói đúng lý do. Chi tiết: [`11`](11-giao-dien.md) §2, §6.
- **Quyền:** `customs_price.read`, khai `PUBLIC` trong `SCOPE_FIELDS` (dữ liệu thị trường bên ngoài, không thuộc phòng ban
  hay pháp nhân nào).

### CN-HQ-09 — Biểu đồ giá và lượng theo kỳ

- **Mục đích:** trả lời *tháng nào giá tốt nhất* và *có nên ôm hàng không*.
- **Luật nghiệp vụ:** kỳ gom là tham số truy vấn, không lưu bảng tổng hợp; luôn vẽ giá điều chỉnh; màn phải nói rõ đang dựa
  trên bao nhiêu năm và bao nhiêu lần nhập (dữ liệu hiện chỉ một năm, chưa kết luận được mùa vụ). Chi tiết:
  [`10`](10-danh-sach-tinh-nang.md) B-01..B-04, [`11`](11-giao-dien.md) §2.2, §4.

### CN-HQ-11 — Tra theo hoạt chất, nhãn Thành phẩm / Nguyên liệu

- **Mục đích:** thu mua mua theo hoạt chất chứ không theo tên thương mại.
- **Luật nghiệp vụ:** hoạt chất suy ra từ tên hàng (nhận ra khoảng 51% số dòng mẫu); giá trị lấy từ tệp nạp mang cờ
  `*_from_file` thì nút *Gắn lại hoạt chất* không ghi đè; nhãn theo từ khóa (TC, TECH, TG, *kỹ thuật*, *nguyên liệu*),
  không khớp thì là Thành phẩm. Chi tiết: [`10`](10-danh-sach-tinh-nang.md) §0, N-09, Y-08.

### CN-HQ-13 — Xuất toàn bộ chạy nền (bao-CR-718)

- **Mục đích:** lấy được TOÀN BỘ dữ liệu (prod 328 nghìn dòng) hoặc toàn bộ dòng khớp bộ lọc ra Excel mà không treo màn
  và không làm chậm hệ thống; nút xuất ngay cũ chặn ở 50.000 dòng.
- **Luồng:** bấm *Xuất toàn bộ (chạy nền)* → hệ báo ngay tổng dòng + số tệp dự kiến (50.000 dòng / tệp) → chạy nền, màn lô
  hiện tiến độ *tệp xong / tổng* → xong thì chuông *Xuất tra cứu thị trường xong — N tệp*; bấm chuông mở màn lô, tải từng tệp.
- **Luật nghiệp vụ:** mỗi người một lô đang chạy (lô thứ hai báo 409 tới khi lô trước xong / dừng); dòng nạp SAU lúc bấm
  không lọt vào; tệp cùng cột với nút xuất ngay (có cột ID + Thao tác) nên sửa xong nạp lại được; dòng trong tệp xếp
  theo thứ tự nạp. Người xuất dừng được lô giữa chừng (tệp đã xong vẫn tải được). Tệp giữ `customs_export_keep_days`
  ngày (mặc định 7) rồi tự dọn; mỗi tệp ghi một dòng nhật ký xuất (`tab_export_log`, màn Hệ thống › Xuất dữ liệu).
- **Quyền:** `customs_price.export`. Xem / tải lô: chính người xuất, hoặc người có `customs_price.export` phạm vi tất cả.
- **Thiết kế:** [kế hoạch CR-718](../plans/261103-tim-nhanh-xuat-lo-bao-cr-718/ke-hoach.md) §6; [`02-thiet-ke-ky-thuat.md`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §12.

### CN-HQ-15 — Danh mục hóa chất theo văn bản

- **Mục đích:** tra nghĩa vụ pháp lý và ngưỡng khối lượng theo văn bản hiện hành.
- **Luật nghiệp vụ:** nạp từ phần mềm ngoài thành `tab_customs_regulation` (PL1 39 · PL2 787 · PL3 164 · PL4 29 có ngưỡng ·
  hoạt chất cấm 31 · phải công bố 10); sửa tay khi văn bản đổi; cần người chịu trách nhiệm cập nhật. Chi tiết:
  [`10`](10-danh-sach-tinh-nang.md) P-01.
- **Quyền:** `customs_regulation.read/create/write/delete/import/export`.

### CN-HQ-21 — Công cụ trợ lý AI

- **Mục đích:** trợ lý trả lời giá / thời điểm mua / thị trường / pháp lý dựa trên số thật.
- **Luật nghiệp vụ:** đi qua đúng khóa `customs_price`; câu trả lời bắt buộc kèm độ tin cậy; kết luận dạng *dữ liệu giá
  nghiêng về...* và phải nói không biết tồn kho, nhu cầu, hạn dùng, dòng tiền; không có mức phạt trong dữ liệu nên trợ lý
  cấm tự nêu; không thấy trong danh mục thì không được kết luận là được phép. Chi tiết: [`10`](10-danh-sach-tinh-nang.md)
  §6 và [`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §10.4.
- **Liên quan:** [Trợ lý AI](../../tro-ly-ai/chuc-nang/01-yeu-cau-chuc-nang.md) CN-AI-04; trên cổng MCP nhóm `customs` mặc
  định tắt ([`10` của Trợ lý AI](../../tro-ly-ai/chuc-nang/10-ket-noi-ai-rieng-va-kho-skill.md) §5).

## 4. Luồng trạng thái chứng từ (nếu có)

Lô nạp ([`02`](../tai-lieu-ky-thuat/02-thiet-ke-ky-thuat.md) §3.1, §3.1b):

```
Chạy thử → Ghi thật → (Hoàn tác lô)
Mỗi dòng trong lô: Thêm mới / Lỗi / Bỏ qua vì trùng
```

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| Q2 | Nạp bao lâu một lần, mỗi lần phủ khoảng nào | Phòng Thu mua | chưa có |
| Q4 | Có lấy được dữ liệu các năm trước không (cần cho kết luận mùa vụ) | Phòng Thu mua | chưa có |
| Q6 | GTT02 có xuất kèm số tờ khai không | Phòng Thu mua | chưa có |
| R1 | Kết xuất GTT02 chia theo thời gian hay theo nhóm mã HS (quyết định có mất dòng khi nạp không) | Chị Mi | chưa có |
| N6 | Có cần biểu đồ theo tuần không | Đại ca | chưa có |
| N8 | Quy tắc quy đổi nồng độ có ngoại lệ cần thêm không | Chị Mi | chưa có |
| — | Ai cập nhật bảng ngưỡng, biểu thuế hằng năm; danh mục BVTV có được dùng và cập nhật định kỳ không | Đại ca chỉ định | chưa có |

Nguồn: [`10`](10-danh-sach-tinh-nang.md) §9, [`06`](../nghien-cuu/06-doi-chieu-yeu-cau-fr-proc-2026-001.md) §6–§7,
[kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md) §3.
