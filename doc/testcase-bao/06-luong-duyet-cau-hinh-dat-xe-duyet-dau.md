# 06 — Đặt xe và Duyệt dấu chạy theo LUỒNG DUYỆT CẤU HÌNH

> **bao-CR-577.** Thử trên **máy dưới** (local) trước khi tính chuyện bật ở dev/prod.
> Đặt xe và Duyệt dấu đã nối sẵn với bộ máy duyệt dùng chung. Chỉ cần khai luồng và bật
> công tắc là phiếu đi theo luồng, không sửa mã. Lượt thử 03/10/2026 lòi ra một lỗi có sẵn
> của bộ máy: bước khai người duyệt «theo vai trò» nổ lỗi 500. Đã vá ở
> `approval/approver_resolver.py`, bản vá phải có trong mã thì bộ kịch bản này mới chạy được.

## Môi trường

Giao diện mới: http://localhost:8083. Stack local phải chạy đủ (`docker compose ps` thấy
`api`, `erp`, `db`). Dữ liệu thử dựng bằng script, chạy lại bao nhiêu lần cũng không sinh trùng:

```bash
docker compose exec -T api python scripts/local_test/setup_flow_test_booking_seal.py
```

## Hai luồng đã khai

| Luồng | Bước 1 | Bước 2 | Sau luồng |
|---|---|---|---|
| `THU-DX-2B` Đặt xe | Trưởng bộ phận của người tạo | Vai trò «Quản lý điều phối» | Điều phối viên gán xe, tài xế nhận chuyến |
| `THU-DX-3B` Đặt xe **giao hàng** (luồng có điều kiện, xét trước) | Trưởng bộ phận | Giám đốc (`DEMOTP3` đóng vai), rồi bước 3 «Quản lý điều phối» | Như trên |
| `THU-DD-2B` Duyệt dấu | Trưởng bộ phận của người tạo | Vai trò «Giám đốc duyệt dấu» | Văn thư công ty đóng dấu |

Công tắc ở màn **Phê duyệt › Bật bộ máy duyệt** đang BẬT cho cả hai.

## Tài khoản

Mật khẩu = mã đăng nhập.

| Mã | Người | Đóng vai |
|---|---|---|
| `TESTREQ` | Nguyễn Kỷ Thảo Thơ, phòng Lập trình & IT nội bộ | người tạo phiếu |
| `DEMOTP` | Trần Trưởng Phòng, trưởng phòng đó | bước 1 của cả hai luồng |
| `DEMOQL` | Lê Quản Lý TM | bước 2: Quản lý điều phối, Giám đốc duyệt dấu |
| `DEMOAD` | Phạm Admin TM | điều phối viên, bấm thay tài xế |
| `TESTMEDEGO` | Văn thư DEGO HOLDING | văn thư công ty DEGO, đóng dấu |
| `DEMOTP3` | Hồ Quyền Trưởng Phòng | đóng vai Giám đốc ở luồng giao hàng |
| `admin` | quản trị | xem và sửa cấu hình luồng |

Đổi vai thì đăng xuất rồi đăng nhập tài khoản kia, hoặc mở một cửa sổ ẩn danh cho mỗi vai.

## Trên dev (https://deverp.degoholding.vn)

Đã khai sẵn ngày 03/10/2026, đại ca vào sửa thử thoải mái:

| Luồng | Áp cho | Bước 1 | Bước 2 |
|---|---|---|---|
| #4 `DATXE` Đặt xe công tác | mặc định, mọi phiếu đặt xe không khớp luồng khác | Trưởng bộ phận người nộp | Vai trò «Quản lý điều phối» |
| #5 `DX-GIAO-HANG` Giao hàng | Loại phiếu là Giao hàng, ưu tiên 10 | Trưởng bộ phận người nộp | Vai trò «Quản lý điều phối» |
| #6 `DD-MAC-DINH` Duyệt dấu | mặc định | Trưởng bộ phận người tạo chọn trên phiếu | Vai trò «Giám đốc duyệt dấu» |

Công tắc Đặt xe và Duyệt dấu đã bật. Vai trò thử đã gán: `DEMONV` người tạo phiếu (phòng Demo Thu Mua,
trưởng phòng là `DEMOTP`), `DEMOTP` trưởng bộ phận, `DEMOQL` quản lý điều phối + giám đốc duyệt dấu, `DEMOAD`
điều phối viên, `VTDEGOHOLDING` văn thư công ty DEGO. Bước 2 giao cho cả `NSU001` (người thật đang giữ hai vai trò
đó trên dev) lẫn `DEMOQL`, ai duyệt cũng được.

⚠️ Trên dev, mật khẩu của `DEMOTP` khác mã đăng nhập — cần mật khẩu dev của tài khoản đó, hoặc đổi trưởng phòng
của phòng Demo Thu Mua sang một tài khoản đăng nhập được, thì mới chạy được bước 1.

Phiếu thử trên dev (tạo 03/10, người tạo `DEMONV`):

| Phiếu | Loại | Luồng | Đang chờ |
|---|---|---|---|
| DX933 | Đặt xe công tác | #4 DATXE | chặng 1/2, `DEMOTP` |
| DX934 | Giao hàng | #5 DX-GIAO-HANG | chặng 1/2, `DEMOTP` |
| DX935 | Đặt xe công tác | — | nháp, để tự gửi duyệt |
| DD866 | Duyệt dấu | #6 DD-MAC-DINH | chặng 1/2, `DEMOTP2` (người tạo chọn) |
| DD867 | Duyệt dấu | — | nháp có tệp, để tự gửi duyệt |

Đặt xe chỉ khai được bước «trưởng bộ phận người nộp», chưa khai được «người tạo chọn người duyệt»: form đặt xe chưa
có ô chọn người duyệt.

## Phiếu mẫu có sẵn

| Phiếu | Loại | Trạng thái lúc giao | Dùng cho ca |
|---|---|---|---|
| DX1218 | Đặt xe công tác | Chờ duyệt, chặng 1/2 | B1 → B3 |
| DX1219 | Đặt xe công tác | Chờ duyệt, chặng 1/2 | B4 |
| DX1220 | Giao hàng | Chờ duyệt, chặng 1/2 | B5 |
| DX1221 | Đặt xe công tác | Nháp | B6 |
| DD1618 | Duyệt dấu | Chờ duyệt, chặng 1/2 | C1, C2 |
| DD1619 | Duyệt dấu | Chờ duyệt, chặng 1/2 | C3, C4 |
| DD1620 | Duyệt dấu | Nháp, đã có tệp | C5 |

Bảy phiếu này tạo bằng script nên thẻ «Lịch sử thao tác» trống. Phiếu đại ca tự tạo trên
màn hình thì thẻ đó có đủ.

---

## A. Cấu hình luồng

**TC-577-A1 — Hai luồng hiện ở màn danh sách luồng**
1. `admin` vào `/approval/flows`.
- Mong đợi: thấy hai luồng `THU-DX-2B` và `THU-DD-2B`, mỗi luồng hai bước, đang hoạt động.
- Kết quả:

**TC-577-A2 — Công tắc bộ máy đang bật**
1. `admin` vào `/approval/engine`.
- Mong đợi: dòng «Đặt xe» và «Duyệt dấu» đang bật, có ghi số luồng đang hoạt động.
- Kết quả:

**TC-577-A3 — Đổi cách duyệt bằng màn hình, không sửa mã**
1. `admin` mở luồng `THU-DX-2B`, đổi bước 2 sang người duyệt cụ thể là `DEMOAD`, lưu.
2. `TESTREQ` tạo một phiếu đặt xe mới và gửi duyệt. `DEMOTP` duyệt bước 1.
- Mong đợi: bước 2 giao cho `DEMOAD`, không phải `DEMOQL`. Phiếu đang chạy từ trước (DX1218)
  vẫn giữ bước 2 cũ là `DEMOQL`.
3. Trả bước 2 về vai trò «Quản lý điều phối» sau khi chấm.
- Kết quả:

**TC-577-A4 — Tắt công tắc thì quay về duyệt một bước**
1. `admin` tắt công tắc «Đặt xe» ở `/approval/engine`.
2. `TESTREQ` tạo phiếu mới, chọn người duyệt là `DEMOTP`, gửi duyệt.
- Mong đợi: phiếu KHÔNG có dòng «Đang ở chặng n/n». `DEMOTP` nhận chuông «có phiếu cần
  duyệt» và duyệt thẳng trên phiếu. Lưu ý: `DEMOTP` hiện chưa có quyền duyệt thẳng đặt xe
  nên sẽ báo thiếu quyền, đúng như phân quyền đang có.
3. Bật lại công tắc sau khi chấm.
- Kết quả:

---

## B. Đặt xe

**TC-577-B1 — Trưởng bộ phận duyệt bước 1**
1. `DEMOTP` bấm chuông, mở thông báo «Chờ bạn duyệt» của DX1218.
2. Bấm **Duyệt**, ghi ý kiến.
- Mong đợi: phiếu chuyển sang «Đang ở chặng 2/2 · Lê Quản Lý TM». `DEMOQL` nhận chuông.
  `DEMOTP` không còn nút Duyệt trên phiếu này.
- Kết quả:

**TC-577-B2 — Quản lý điều phối duyệt bước 2**
1. `DEMOQL` mở DX1218 từ chuông, bấm **Duyệt**.
- Mong đợi: phiếu sang «Đã duyệt». `DEMOAD` nhận chuông «có chuyến xe cần điều phối».
  `TESTREQ` nhận chuông «đã được duyệt». Khối tiến trình ghi tên người ký ở cả hai bước.
- Kết quả:

**TC-577-B3 — Điều phối và chạy chuyến**
1. `DEMOAD` mở DX1218, bấm **Điều phối**, chọn một xe và một tài xế.
2. Cũng `DEMOAD` bấm thay tài xế: **Nhận chuyến**, **Bắt đầu**, **Hoàn tất** (nhập km, chi phí).
- Mong đợi: lần lượt «Đã điều phối» → «Hoàn thành». `TESTREQ` nhận chuông «đã hoàn tất».
- Kết quả:

**TC-577-B4 — Trả về cho người tạo sửa**
1. `DEMOTP` mở DX1219, bấm **Trả về**, ghi lý do.
2. `TESTREQ` mở DX1219.
- Mong đợi: trạng thái «Yêu cầu chỉnh sửa», thấy lý do. Sửa một ô (ví dụ giờ đi) rồi
  **Gửi duyệt** lại thì luồng chạy lại từ chặng 1/2, `DEMOTP` nhận việc mới.
- Kết quả:

**TC-577-B5 — Từ chối ở bước 2**
1. `DEMOTP` duyệt DX1220. `DEMOQL` mở DX1220, bấm **Từ chối**, ghi lý do.
- Mong đợi: phiếu «Từ chối», khóa, không sửa không gửi lại được. `TESTREQ` nhận chuông kèm lý do.
- Kết quả:

**TC-577-B6 — Người tạo rút lại phiếu**
1. `TESTREQ` mở DX1221 (nháp), bấm **Gửi duyệt**.
2. Trước khi ai duyệt, `TESTREQ` bấm **Rút lại**, ghi lý do.
- Mong đợi: phiếu về «Nháp», sửa và gửi lại được. Làm lại lần nữa nhưng để `DEMOTP` duyệt
  bước 1 trước: lúc đó **Rút lại** bị chặn, câu báo nói đã có người duyệt.
- Kết quả:

**TC-577-B7 — Không ai duyệt vượt lượt**
1. Với một phiếu đang ở chặng 1/2, `DEMOQL` mở phiếu.
- Mong đợi: `DEMOQL` không có nút Duyệt cho tới khi `DEMOTP` duyệt xong bước 1.
  `TESTREQ` không bao giờ thấy nút Duyệt trên phiếu của chính mình.
- Kết quả:

**TC-577-B8 — Ca lớn thêm lớp Giám đốc**
1. `TESTREQ` tạo một phiếu **giao hàng** mới và gửi duyệt.
- Mong đợi: phiếu ghi «Đang ở chặng 1/3». Thứ tự ký: `DEMOTP` → `DEMOTP3` → `DEMOQL`, xong
  là «Đã duyệt đủ 3/3 chặng» rồi sang điều phối. Phiếu **đặt xe công tác** gửi cùng lúc
  vẫn chỉ 2/2 chặng.
- Ghi chú: phiếu đặt xe chưa có ô «giá trị tài sản», nên lượt thử mượn loại «giao hàng» làm
  điều kiện. Điều kiện này em khai thẳng dưới máy; màn cấu hình hiện chưa cho khai điều
  kiện với đặt xe (xem mục D).
- Kết quả:

**TC-577-B9 — Sửa luồng thì phiếu gửi sau đi theo luồng mới**
1. Gửi một phiếu đặt xe công tác (phiếu X).
2. `admin` sửa bước 2 của `THU-DX-2B` sang vai trò «Điều phối viên», lưu.
3. Gửi thêm một phiếu đặt xe công tác (phiếu Y). `DEMOTP` duyệt cả hai.
- Mong đợi: bước 2 của X vẫn ở `DEMOQL`, bước 2 của Y sang `DEMOAD`.
4. Trả bước 2 về «Quản lý điều phối».
- Kết quả:

---

## C. Duyệt dấu

**TC-577-C1 — Hai bước phê duyệt**
1. `DEMOTP` mở DD1618, bấm **Duyệt**.
2. `DEMOQL` mở DD1618 từ chuông, bấm **Duyệt**.
- Mong đợi: sau bước 1 phiếu ở «chặng 2/2», sau bước 2 phiếu «Đã duyệt».
  `TESTMEDEGO` nhận chuông.
- Kết quả:

**TC-577-C2 — Văn thư đóng dấu**
1. `TESTMEDEGO` mở DD1618, bấm **Hoàn thành đóng dấu**, ghi chú số bản đã đóng.
- Mong đợi: phiếu «Hoàn thành». `TESTREQ` nhận chuông «đã đóng dấu xong».
- Kết quả:

**TC-577-C3 — Văn thư không đóng dấu khi phiếu chưa duyệt xong**
1. `TESTMEDEGO` tìm DD1619, lúc phiếu còn ở chặng 1/2 hoặc 2/2.
- Mong đợi: không thấy nút đóng dấu, hoặc không mở được phiếu.
- Kết quả:

**TC-577-C4 — Trả về ở bước 2**
1. `DEMOTP` duyệt DD1619. `DEMOQL` bấm **Trả về**, ghi lý do.
- Mong đợi: phiếu «Yêu cầu chỉnh sửa». `TESTREQ` sửa rồi gửi lại thì chạy lại từ chặng 1/2.
- Kết quả:

**TC-577-C5 — Gửi phiếu nháp có tệp, và chặn khi thiếu tệp**
1. `TESTREQ` mở DD1620, bấm **Gửi duyệt**.
- Mong đợi: phiếu vào chặng 1/2, `DEMOTP` nhận chuông.
2. Tạo một phiếu dấu mới, KHÔNG đính kèm tệp, bấm Gửi duyệt.
- Mong đợi: bị chặn với câu «Cần đính kèm ít nhất 1 chứng từ có chữ ký sống».
- Kết quả:

**TC-577-C6 — Văn thư trả về hoặc từ chối ở bước đóng dấu**
1. Đưa một phiếu tới «Đã duyệt» như C1. `TESTMEDEGO` bấm **Trả về** (hoặc **Từ chối**).
- Mong đợi: trả về thì người tạo sửa và gửi lại được; từ chối thì phiếu khóa.
- Kết quả:

---

## D. Điều đã biết, không tính là lỗi của lượt này

- **Màn cấu hình chưa cho khai điều kiện** với Đặt xe và Duyệt dấu, ở cả mức luồng lẫn mức
  bước. Bộ máy thì đã chạy được điều kiện (TC-577-B8). Muốn hành chính tự khai «ca nào thêm
  Giám đốc» thì phải mở bộ chọn điều kiện cho hai loại phiếu này.

- Phiếu đến từ app cũ (mang mã app cũ) vẫn duyệt bên app cũ. Bật công tắc không đổi gì với chúng.
- `DEMOTP` mở phiếu đặt xe thấy ô «Trao đổi» báo không tải được. Em đã thấy, chưa tra
  nguyên nhân; nhiều khả năng do phiếu nằm ngoài phạm vi dữ liệu của `DEMOTP`, chỉ được
  nới quyền đọc vì đang có việc duyệt.
- Giờ «Tạo lúc» trên phiếu mẫu lệch 7 tiếng so với giờ máy, cần đối chiếu với phiếu tạo trên màn hình.

## Đã chạy máy thay (03/10/2026)

Một vòng đầy đủ qua API, mỗi loại phiếu một phiếu riêng (DX1223, DD1621). Thêm DX1224..DX1227
cho ba ca B8, B9 và luồng 2 lớp:
đặt xe đi hết TBP → Quản lý điều phối → điều phối → nhận → chạy → hoàn thành;
duyệt dấu đi hết TBP → Giám đốc → văn thư đóng dấu. Hai chốt chặn đúng: TBP không duyệt
thẳng được phiếu đang chạy luồng, văn thư không đóng dấu sớm được. Chuông đến đúng người ở
từng bước.
