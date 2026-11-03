# ERPNext học nghiệp vụ: bài tập thu mua và nhập kho

> **Từ 30/10/2026 dữ liệu mẫu đã được thay bằng dữ liệu thật từ ERP DEGO:** 7 công ty pháp nhân (DGH, IDA, ABA, ICR, BMB, ABS, DRX), danh mục hàng / NCC / kho thật, YCMH và ĐMH từ 01/08/2026. Các mã chứng từ mẫu nhắc trong bài (PUR-ORD-2026-00006, MAT-MR-2026-00002...) không còn; tìm chứng từ thật theo cột "Mã ERP". Công ty mẫu "erpnext" chỉ còn khung.

Trang: https://erpnext.degoholding.vn (bản học, dựng 30/10/2026). Giao diện tiếng Việt; tên tiếng Anh ghi trong ngoặc để tra tài liệu ERPNext.

Mẹo chung:
- Ô **Tìm kiếm** trên cùng (Ctrl+G): gõ tên màn, ví dụ *Đơn mua hàng*, *Purchase Order*, rồi Enter.
- Trên mỗi chứng từ đã gửi, nút **Tạo** (Create) sinh chứng từ kế tiếp và tự chép dữ liệu sang.
- Trạng thái chứng từ: **Nháp** (sửa được) -> **Gửi** (Submit, khóa lại, sinh bút toán và sổ kho) -> **Hủy** (Cancel) -> **Sửa đổi** (Amend, tạo bản mới).
- Đổi tài khoản: avatar góc trên phải -> **Đăng xuất**, rồi đăng nhập tài khoản khác. Muốn xem hai vai cùng lúc thì mở thêm một cửa sổ ẩn danh.

---

## 1. Tài khoản theo vai

Tất cả mật khẩu là **admin** (site học, không dùng cho dữ liệu thật).

| Tài khoản | Vai | Được làm |
|---|---|---|
| Administrator | Quản trị | Mọi thứ, bật tắt cấu hình |
| nguoi.de.nghi@erpnext.local | **Người đề nghị** (vai trò *Người đề nghị mua*) | Lập, gửi, hủy **Yêu cầu vật tư** của chính mình; KHÔNG thấy phiếu người khác, không thấy đơn mua hàng |
| thu.mua@erpnext.local | **Nhân viên thu mua** (Purchase User) | Yêu cầu báo giá, báo giá NCC, lập **Đơn mua hàng**, gửi duyệt; tự duyệt đơn nhỏ |
| truong.phong@erpnext.local | **Trưởng phòng thu mua** (Purchase Manager) | **Duyệt / Từ chối** đơn trên 50 triệu, hủy đơn đã duyệt |
| thu.kho@erpnext.local | **Thủ kho** (Stock User + Quality Manager) | **Biên nhận mua hàng** (nhập kho), **Kiểm tra chất lượng**, chuyển kho, xuất kho; chỉ đọc đơn mua hàng |

Đã kiểm thật: người đề nghị chỉ thấy phiếu mình; thủ kho không lập được đơn mua hàng; thu mua không làm được kiểm tra chất lượng.

### Bật / tắt tài khoản, thêm / bỏ vai trò
- Đường: Tìm kiếm **Người dùng** (User) -> mở tài khoản.
- **Tắt tài khoản**: bỏ tick **Đã bật** (Enabled) -> Lưu. Bật lại thì tick lại.
- **Thêm / bỏ vai trò**: tab **Vai trò** (Roles) -> tick hoặc bỏ tick từng vai trò -> Lưu. Người đó đăng xuất vào lại mới có hiệu lực.
- **Đổi mật khẩu**: tab **Cài đặt** (Settings) của người dùng -> ô **Đặt mật khẩu mới** (Set New Password).
- **Xem một vai trò được làm gì**: Tìm kiếm **Trình quản lý quyền vai trò** (Role Permissions Manager) -> chọn chứng từ, ví dụ *Material Request*, xem từng dòng vai trò (Đọc, Ghi, Tạo, Gửi, Hủy; ô *Chỉ khi là người tạo* = chỉ phiếu của mình).

---

## 2. Luồng duyệt Đơn mua hàng

Quy trình tên **Duyệt đơn mua hàng** (Workflow), áp cho **Đơn mua hàng**. Ngưỡng tính theo tổng tiền quy VND (đơn USD cũng đúng).

```
Nháp --(Gửi duyệt, đơn > 50 triệu, thu mua bấm)--> Chờ duyệt --(Duyệt, trưởng phòng)--> Đã duyệt (đơn được Gửi)
  |                                                    |
  |                                                    +--(Từ chối, trưởng phòng)--> Từ chối --(Gửi lại)--> Chờ duyệt
  +--(Duyệt luôn, đơn <= 50 triệu, thu mua bấm)--> Đã duyệt
Đã duyệt --(Hủy, trưởng phòng)--> Đã hủy
```

- Người lập đơn **không tự duyệt** được đơn của mình ở bước Chờ duyệt.
- Không gửi thư (site chưa có hộp thư); người duyệt thấy việc ở danh sách **Đơn mua hàng**, lọc trạng thái **Chờ duyệt**.
- Các đơn cũ đã gửi trước khi bật quy trình tự mang trạng thái **Đã duyệt**.

Đơn mẫu để thử:
- **PUR-ORD-2026-00006**: 5.000 kg MAP, 70 triệu, đang **Chờ duyệt**. Đăng nhập *truong.phong* -> mở đơn -> nút **Hành động** (Actions) góc trên -> **Duyệt** hoặc **Từ chối**.
- **PUR-ORD-2026-00007**: 1.000 kg KCl, 9,5 triệu, đang **Nháp**. Đăng nhập *thu.mua* -> mở đơn -> **Hành động** -> **Duyệt luôn**.

### Bật / tắt luồng duyệt
- Đường: Tìm kiếm **Quy trình làm việc** (Workflow) -> mở **Duyệt đơn mua hàng**.
- **Tắt**: bỏ tick **Đang hoạt động** (Is Active) -> Lưu. Đơn mua hàng quay về nút **Gửi** thường, ai có quyền gửi là gửi được.
- **Bật**: tick lại **Đang hoạt động** -> Lưu.
- **Đổi ngưỡng 50 triệu**: bảng **Chuyển đổi** (Transitions) -> cột **Điều kiện** (Condition) của các dòng *Gửi duyệt / Duyệt luôn / Gửi lại*: sửa số `50000000`.
- **Đổi người duyệt**: cột **Được phép** (Allowed) của dòng *Duyệt* / *Từ chối*.
- Sau khi đổi: Ctrl+Shift+R để tải lại trang.

---

## 3. Mức tồn tối thiểu và tự sinh Yêu cầu vật tư

Đã đặt ở kho **Stores - ET**:

| Mặt hàng | Mức đặt hàng lại | Số lượng tự đề nghị |
|---|---|---|
| NL-UREA Urê hạt | 1.000 kg | 2.000 kg |
| NL-HUMIC K-Humate | 2.000 kg | 3.000 kg |
| NL-MAP | 500 kg | 1.000 kg |

Đã mô phỏng: phiếu xuất kho sản xuất **MAT-STE-2026-00004** (xuất 400 kg urê, 300 kg humate) làm tồn xuống dưới mức -> hệ thống tự sinh **MAT-MR-2026-00002** (Yêu cầu vật tư loại Mua, 3 dòng urê / humate / MAP, đã gửi, chờ thu mua xử lý).

Cách hệ thống tính: so **số lượng dự kiến** (Projected Qty = tồn thực + đang đặt mua + đang yêu cầu - đã giữ cho đơn bán) với **mức đặt hàng lại**. Đơn mua đang mở cũng được cộng, nên đã có đơn đang về thì không sinh thêm.

Job chạy theo **lịch tự động** của máy chủ (scheduler, đang BẬT cho site này), **mỗi ngày một lần** (nhóm việc bảo trì hằng ngày). Muốn xem ngay thì quản trị chạy lại theo bài tập 6 bên dưới.

### Bật / tắt
- **Tự sinh Yêu cầu vật tư cho cả hệ thống**: Tìm kiếm **Cài đặt tồn kho** (Stock Settings) -> mục **Yêu cầu vật liệu tự động** (Auto Material Request) -> tick / bỏ tick ô *Raise Material Request When Stock Reaches Re-order Level* -> Lưu. Có thêm ô gửi thư báo khi sinh phiếu (để tắt, site không có hộp thư).
- **Mức tồn của từng mặt hàng**: mở **Mặt hàng** (Item), ví dụ NL-UREA -> tab **Hàng tồn kho** (Inventory) -> mục **Tự động đặt hàng lại** (Auto re-order) -> bảng mức theo kho: sửa **Mức đặt hàng lại** (Re-order Level), **Số lượng đặt hàng lại** (Re-order Qty); xóa dòng để tắt cho mặt hàng đó -> Lưu.

---

## 4. Kiểm tra chất lượng trước khi nhập kho

### Bật / tắt
- Mở **Mặt hàng** (Item) -> tab **Chất lượng** (Quality) -> tick / bỏ tick **Yêu cầu kiểm tra trước khi mua** (Inspection Required before Purchase) -> Lưu.
- Đang bật sẵn cho **NL-KCL** (Kali Clorua). Khi bật, **Biên nhận mua hàng** có mặt hàng đó KHÔNG gửi được nếu chưa có phiếu kiểm tra đạt.

---

## 5. Bài tập từng bước

### Bài 1: Mua thường đủ một vòng (4 vai)
1. *nguoi.de.nghi*: **Yêu cầu vật tư** -> **Thêm** -> Mục đích *Mua* (Purchase), ngày cần, dòng NL-KCL 500 kg, kho Stores - ET -> Lưu -> **Gửi**. (Có sẵn bản nháp **MAT-MR-2026-00003** để gửi luôn.)
2. *thu.mua*: mở yêu cầu đó -> **Tạo** -> **Yêu cầu báo giá** (Request for Quotation) -> thêm 2 nhà cung cấp -> Lưu -> Gửi.
3. *thu.mua*: với từng NCC, từ yêu cầu báo giá -> **Tạo** -> **Báo giá từ nhà cung cấp** (Supplier Quotation) -> nhập đơn giá -> Gửi. Xem báo cáo **So sánh báo giá từ nhà cung cấp** để chọn giá tốt.
4. *thu.mua*: từ báo giá thắng -> **Tạo** -> **Đơn mua hàng** -> Lưu -> **Hành động**: dưới 50 triệu thì **Duyệt luôn**, trên thì **Gửi duyệt**.
5. *truong.phong* (nếu đơn lớn): mở đơn -> **Hành động** -> **Duyệt**.
6. *thu.kho*: mở đơn đã duyệt -> **Tạo** -> **Biên nhận mua hàng** (Purchase Receipt) -> kiểm số lượng, kho -> Gửi. Vì KCl cần kiểm chất lượng, làm bài 3 trước bước Gửi.
7. *Administrator*: từ biên nhận -> **Tạo** -> **Hóa đơn mua hàng** (Purchase Invoice) -> nhập số hóa đơn NCC -> Gửi -> **Tạo** -> **Thanh toán** (Payment Entry) -> chọn tài khoản Vietcombank -> Gửi.
8. Xem kết quả: **Số dư tồn kho** (Stock Balance), **Sổ tồn kho** (Stock Ledger), **Phân tích Đơn Mua hàng** (Purchase Order Analysis), báo cáo **Sổ cái** (General Ledger) lọc theo số chứng từ.

### Bài 2: Nhận thiếu, nhận nhiều lần
1. *thu.mua*: lập đơn 1.000 kg urê (dưới 50 triệu -> Duyệt luôn).
2. *thu.kho*: **Tạo** -> **Biên nhận mua hàng** -> sửa số lượng thành **600** -> Gửi.
3. Mở lại đơn mua hàng: cột *Đã nhận* 600/1.000, trạng thái *Chờ nhận và lập hóa đơn*, thanh tiến độ 60%.
4. *thu.kho*: từ đơn lần nữa -> **Tạo** -> **Biên nhận mua hàng**: hệ thống tự điền **400** còn lại -> Gửi. Đơn lên 100%.
5. Hàng bị hỏng khi nhận: trên dòng biên nhận nhập **Số lượng bị từ chối** (Rejected Qty) và **Kho bị từ chối** (Rejected Warehouse) -> hàng hỏng vào kho riêng, không cộng tồn kho dùng được.
6. Đơn không giao hết nữa: trên đơn -> **Trạng thái** (Status) -> **Đóng** (Close) để chốt phần còn lại.

### Bài 3: Kiểm tra chất lượng trước nhập
1. *thu.kho*: lập **Biên nhận mua hàng** có NL-KCL (nháp, chưa gửi).
2. Trên dòng KCl -> nút **Kiểm tra chất lượng** (hoặc Tìm kiếm *Kiểm tra chất lượng* -> Thêm, loại *Incoming*, tham chiếu biên nhận đó) -> nhập chỉ tiêu, kết quả **Đạt** (Accepted) -> Gửi.
3. Quay lại biên nhận -> Gửi. Thử kết quả **Không đạt** (Rejected): biên nhận sẽ báo lỗi, không cho nhập.

### Bài 4: Trả hàng nhà cung cấp
1. Mở một **Biên nhận mua hàng** đã gửi -> **Tạo** -> **Trả lại** (Return).
2. Số lượng tự hiện số âm -> sửa số lượng trả -> Gửi. Tồn kho giảm, ghi chú lý do ở ô ghi chú.
3. Nếu đã có hóa đơn: từ **Hóa đơn mua hàng** -> **Tạo** -> **Trả lại / Phiếu ghi nợ** (Debit Note) để giảm công nợ NCC.

### Bài 5: Nhập khẩu có chi phí mua (Landed Cost)
1. Xem mẫu sẵn: đơn **PUR-ORD-2026-00005** (USD, NCC Shandong), biên nhận **MAT-PRE-2026-00006**, phiếu chi phí **MAT-LCV-2026-00001**.
2. Tự làm: sau khi gửi **Biên nhận mua hàng** hàng nhập -> Tìm kiếm **Phiếu chi phí vận chuyển** (Landed Cost Voucher) -> Thêm -> dòng biên nhận -> **Lấy vật phẩm từ biên nhận** -> bảng chi phí: cước, thuế nhập khẩu, phí cảng (chọn tài khoản chi phí) -> chọn phân bổ theo *Giá trị* (Amount) hoặc *Số lượng* (Qty) -> Gửi.
3. Xem **Sổ tồn kho**: giá vốn từng kg tăng lên đúng phần chi phí phân bổ.
4. Trả tiền USD theo tỷ giá khác ngày nhận hóa đơn -> hệ thống tự ghi **lãi / lỗ tỷ giá** (mẫu: lỗ 400.000 đ ở ACC-JV-2026-00004).

### Bài 6: Tự sinh Yêu cầu vật tư khi tồn thấp
1. *thu.kho*: **Bút toán tồn kho** (Stock Entry) -> Thêm -> loại **Xuất vật tư** (Material Issue) -> NL-UREA, kho nguồn Stores - ET, số lượng đủ để tồn dưới 1.000 kg -> Gửi.
2. Chờ job lịch tự động chạy, hoặc nhờ quản trị chạy ngay (trên máy chủ: `bench --site frontend execute erpnext.stock.reorder_item.reorder_item`).
3. Mở **Yêu cầu vật tư**: có phiếu mới do hệ thống lập, số lượng bằng *Số lượng đặt hàng lại*.
4. Nếu không sinh: kiểm **Cài đặt tồn kho** còn bật, và **số lượng dự kiến** còn dưới mức không (đơn mua đang mở được cộng vào).

---

## 6. Dọn dữ liệu bài tập

Chứng từ đã gửi không xóa thẳng được: **Hủy** trước rồi mới **Xóa** (chỉ Administrator). Muốn làm lại sạch toàn bộ, nhờ quản trị dựng lại site.
