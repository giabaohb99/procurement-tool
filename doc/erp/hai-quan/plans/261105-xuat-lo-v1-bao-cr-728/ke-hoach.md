# KẾ HOẠCH — TRA CỨU THỊ TRƯỜNG: XUẤT LÔ TRÊN v1 + TRẦN DUNG LƯỢNG NẠP (bao-CR-728)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 05/11/2026 |
| Người phụ trách | Agent 4 (A1 Điều phối giao, người chủ yêu cầu) |
| Trạng thái | Xong trên erp-v2 — chờ soát trên dev và người chủ gật lên prod |
| CR liên quan | bao-CR-728 (tiếp bao-CR-718) |

## 1. Việc

1. Đồng bộ xuất toàn bộ / theo bộ lọc chạy nền của bao-CR-718 sang giao diện v1 (`frontend/`, đang đóng băng — NGOẠI
   LỆ người chủ cho phép): menu *Xuất dữ liệu* ba mục, màn *Lô xuất của tôi*, màn chi tiết lô; chuông "xuất xong" bấm từ
   v1 phải tới được màn v1.
2. Cửa nạp tệp Tra cứu thị trường (`POST /api/customs/imports`) có trần dung lượng.
3. Thử trọn vòng xuất, sửa, nạp lại, hoàn tác trên ~50.000 dòng ở local, đo thời gian và bộ nhớ.

## 2. Giao diện v1

- `components/customs/CustomsLineExportMenu.tsx`: *Xuất ngay (tối đa 50.000 dòng)* (cũ; tắt khi quá trần) · *Xuất toàn
  bộ theo bộ lọc (chạy nền)* (hộp xác nhận nêu bộ lọc, số dòng, số tệp dự kiến, giữ 7 ngày; 409 thì báo và sang danh
  sách lô) · *Lô xuất của tôi*. Gọi đúng API v2: `GET /lines/export`, `POST /export-batches`.
- `pages/CustomsExportBatches.tsx` (`/customs-prices/exports`) và `pages/CustomsExportBatchDetail.tsx`
  (`/customs-prices/exports/:id`): tiến độ, tải từng tệp, dừng lô, câu lỗi, lô quá hạn; hỏi lại mỗi 3 giây khi lô còn
  chạy. Gác `customs_price.export`; menu trái sáng *Giá thị trường*.
- Chuông: backend ghi link đường v2 `/procurement/customs-prices/exports/<id>`. v1 thêm route cùng đường đó, chuyển
  thẳng sang `/customs-prices/exports/<id>` — chuông, trang Thông báo và thông báo đẩy (`push-sw.js`) đều tới đúng màn.
  Không đổi link backend nên v2 giữ nguyên.

## 3. Backend

- `reader.MAX_UPLOAD_BYTES` = 30 MB (bằng `pesticide_reader`), cửa nạp đọc tối đa trần + 1 byte, vượt thì 413
  *"tên tệp": tệp quá lớn (tối đa 30 MB mỗi tệp) — chia nhỏ tệp rồi nạp lại*. Tệp xuất 50.000 dòng 12,84 MB.
- Hai điểm nghẽn lộ ra khi thử trọn vòng, sửa luôn vì nhỏ:
  - `check_headers` đọc trọn lưới chỉ để xem tiêu đề, ngay trong lời gọi API: tệp 50.000 dòng mất **18,8 giây** và đẩy
    tiến trình api lên **~500 MB**. Nay .xlsx chỉ đọc dòng đầu: **0,02 giây**, bộ nhớ không tăng.
  - Bộ gắn hoạt chất theo tên thương mại duyệt từ bằng `set` — thứ tự đổi theo từng tiến trình, nên tên hàng chứa hai tên
    thương mại ra hoạt chất khác nhau giữa hai lần chạy. Hậu quả đo được: xuất rồi nạp lại tệp chỉ sửa 7 dòng mà lô báo
    11, 15, 19 dòng *Ghi đè* (mỗi lần một khác) và đổi hoạt chất của các dòng đó. Nay duyệt theo thứ tự từ trong tên hàng.
  - `Cell` của bộ đọc thêm `slots` (bớt ~60 MB khi đọc tệp 50.000 dòng).

## 4. Số đo thử trọn vòng (local, MySQL 8.0 riêng, bộ đệm 256 MB)

Dữ liệu: bảng hải quan của máy local (18.243 dòng) nhân thêm hai bản dời năm → **50.000 dòng**. Script:
[`do-vong-xuat-nap.py`](do-vong-xuat-nap.py), mỗi bước một tiến trình để đo bộ nhớ đỉnh riêng.

| Bước | Thời gian | Bộ nhớ đỉnh tiến trình | Ghi chú |
|---|---|---|---|
| Xuất lô cả bảng (vai worker) | 25,4 giây (qua Celery thật: 25 giây) | 273 MB | 1 tệp 50.000 dòng, 12,84 MB; gồm ~7,5 giây nghỉ giữa khối |
| Nạp: đọc có trần + kiểm tiêu đề + lưu (vai api) | 0,2–0,5 giây | ~255 MB (bằng nền tiến trình) | trước khi sửa: 19,3 giây, 497 MB |
| Chạy thử (vai worker) | 43–79 giây | ~1.010–1.060 MB | 7 ghi đè, 5 xóa, 49.988 bỏ qua (không đổi) |
| Ghi thật (vai worker) | 42–47 giây | ~1.010–1.070 MB | 7 ghi đè, 5 xóa |
| Hoàn tác lô | 0,1 giây | ~250 MB | trả 7 dòng ghi đè, dựng lại 5 dòng xóa |

Kiểm đúng: sau ghi thật, 7 dòng có đúng giá mới, 5 dòng biến mất, dấu kiểm (CRC) của 49.988 dòng còn lại không đổi;
sau hoàn tác, dấu kiểm cả bảng trùng hệt trước khi nạp (50.000 dòng).

## 5. Điểm nghẽn còn lại (chưa sửa, cần quyết)

- **Bộ nhớ tác vụ nạp ~1 GB cho tệp 50.000 dòng**: nền 250 MB + đọc tệp ~360 MB + `dedupe.load_existing` nạp mọi dòng
  trong khoảng ngày thành đối tượng ORM ~260 MB + so khớp ~110 MB. Worker local trần `mem_limit: 1g` → sát trần, dễ bị
  giết; prod không đặt trần nhưng chạy `-c 2` (hai lô cùng lúc ~2 GB). Sửa tận gốc là đọc theo khối trong `load_existing`
  (lõi chống trùng bao-CR-541) — việc vừa, nên tách CR riêng.
- Ghi đè đặt lại `date_fixed` = 0 (tệp xuất ghi ngày đã đúng nên lúc nạp lại không còn dấu "đã vá ngày"); dấu lịch cam
  trên màn mất ở các dòng đã sửa qua tệp. Nhỏ, chưa sửa.
- Dữ liệu hoạt chất ĐÃ LƯU được gắn bằng thứ tự ngẫu nhiên cũ: lần nạp lại đầu tiên sau bản này có thể còn báo ghi đè
  ở các dòng tên hàng chứa hai tên thương mại. Bấm *Gắn lại nhãn* (thẻ Cấu hình) một lần sau khi lên môi trường là hết.

## 6. Chênh tính năng v2 / v1 còn lại (ngoài lô xuất) — chờ người chủ chọn

Đối chiếu 05/11: mọi CR có ở v2 đều đã bê sang v1 (470, 477, 493–496, 501–503, 519, 541, 603, 605, 608, duoc-CR-490..494).
Còn lệch:

| Tính năng v2 | v1 hiện trạng | Cỡ việc |
|---|---|---|
| Bộ lọc dòng hàng nằm trên URL (gửi link, F5, Back giữ kết quả) | state cục bộ, F5 là mất | vừa |
| Bộ lọc tự áp (ô tìm chờ ngưng gõ, ô chọn áp ngay) | phải bấm Tìm / Enter | nhỏ (đi cùng dòng trên) |
| Link cũ `?tab=` tự chuyển sang `/customs-prices/<mục>` | rơi về Danh sách | nhỏ |
| Hàng Lọc thêm thu gọn được khi đang có giá trị | bị ép mở | nhỏ |
| Bảng Danh sách dùng DataTable chung (kéo thả cột, ghim cột, thẻ điện thoại) | chỉ ẩn / hiện, giãn cột | lớn (hạ tầng bảng chung) |
| Bảng thuốc BVTV có menu Cột, cột Lĩnh vực, ghim tên thuốc | 10 cột cố định | nhỏ–vừa |
| Hộp nạp: kéo thả, cộng dồn tệp, bỏ từng tệp; báo khi mọi tệp hỏng; nút Áp dụng khóa khi đang ghi | ô chọn tệp thường, thiếu ba câu báo | nhỏ |
| Nhật ký lô chia hai thẻ; chọn cỡ trang ở lịch sử / nhật ký | hai bảng xếp dọc, cỡ trang cố định | nhỏ |
| Hoàn tác lô chặn bấm đúp | chưa chặn | nhỏ |
| Hộp chi tiết dòng: khung chờ + câu báo khi dòng vừa bị hoàn tác | hộp tự đóng im lặng | nhỏ |
| Chi tiết thuốc BVTV trên màn hẹp: ngăn kéo Tra cứu | cột tra cứu đẩy xuống cuối | nhỏ |
| Câu mô tả dưới tiêu đề màn | không có | nhỏ |
