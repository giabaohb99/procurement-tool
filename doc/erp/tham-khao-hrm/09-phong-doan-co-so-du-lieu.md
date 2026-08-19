# PHỎNG ĐOÁN CƠ SỞ DỮ LIỆU — TỔNG HỢP

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Suy ra từ khảo sát giao diện, ngày 11/08/2026 |
| Phạm vi | Khoảng 50 bảng, gom theo tám nhóm |

---

## Tóm tắt mục này

Toàn bộ mục này là **phỏng đoán**. Không truy cập được cơ sở dữ liệu của họ. Nhưng phỏng đoán không phải đoán mò — nó dựa trên bốn thứ quan sát trực tiếp được, và mỗi bảng đều ghi mức tin cậy.

Từng mục tính năng đã có bảng phỏng đoán riêng cho phần của mình. Tài liệu này làm ba việc mà các mục riêng không làm được:

1. **Gom lại một chỗ** để nhìn thấy quy mô: khoảng 50 bảng cho một hệ thống HRM đầy đủ, chưa kể E-Learning.
2. **Ghi lại các quy ước đặt tên và các cơ chế xuyên suốt** — những thứ lặp lại ở nhiều mục nên phải quyết một lần cho tất cả.
3. **Nêu bốn câu hỏi thiết kế phải trả lời trước khi viết dòng mã đầu tiên.** Đây là phần có giá trị nhất của tài liệu này.

---

## 1. Cơ sở của phỏng đoán

| Nguồn | Suy ra được gì |
|---|---|
| Thuộc tính `name` và `id` của các ô nhập liệu | Tên cột. Ứng dụng ASP.NET MVC thường đặt tên ô trùng tên thuộc tính của lớp dữ liệu, và lớp dữ liệu thường trùng tên cột |
| Cột hiển thị trên bảng danh sách | Cột nào thực sự tồn tại và cột nào được tính ra |
| Đường dẫn `/{Controller}/{Action}` | Mỗi controller thường tương ứng một bảng chính |
| Cách bố trí thẻ và bảng con trong màn hình tạo mới | Quan hệ cha con giữa các bảng |

**Cái không suy ra được:** kiểu dữ liệu chính xác, chỉ mục, ràng buộc khóa ngoại, và cách họ lưu kết quả bảng lương.

---

## 2. Quy ước đặt tên của họ

Ghi lại vì nó cho biết cách đọc phần còn lại, và vì có vài quy ước đáng lấy, vài quy ước đáng tránh.

| Quan sát | Ví dụ | Nhận xét |
|---|---|---|
| Tên cột là tiếng Việt không dấu, kiểu lạc đà | `soNgayPhepConLaiNamCu` | Dài nhưng đọc là hiểu ngay, không cần từ điển. Hệ thống Thu mua cũng đang theo lối này. **Giữ** |
| Khóa nghiệp vụ là chuỗi do người dùng đặt | `maNhanVien`, `maHopDong`, `maPhieu`, `maNhomQuyen` | Dễ nói chuyện với người dùng, nhưng khó đổi và dễ dính lỗi mã hóa. Chính họ đã có một nhóm quyền tên `Qu?n lý xu?t tài s?n`. **Không lấy làm khóa chính** — dùng khóa số, để mã nghiệp vụ là cột riêng có ràng buộc duy nhất |
| Tiền tố `ls` nghĩa là danh sách nhiều giá trị | `lsPhongBanApDung`, `lsNhanVienBanGiao` | Trên giao diện là ô chọn nhiều. Dưới cơ sở dữ liệu nhiều khả năng là chuỗi nối bằng dấu chấm phẩy, vì màn hình hiển thị dạng `Phòng Công nghệ thông tin;Ban Đầu Tư`. **Không lấy** — dùng bảng nối |
| Trường suy ra được vẫn lưu sẵn | `doTuoi`, `thoiGianLamViecTaiCongTy`, `loaiHDLD` trên hồ sơ | Đánh đổi lấy tốc độ hiển thị danh sách. Phải có công việc chạy nền cập nhật lại, nếu không sẽ lệch |
| Cặp cũ và mới lưu trên cùng một phiếu | `phongBanCu` / `maPhongBan` ở màn hình đi làm lại | Lưu vết rẻ tiền mà hiệu quả. **Đáng lấy** |
| Hậu tố theo thẻ trên tên ô lọc | `qSearch-taikhoandanghoatdong` | Chi tiết giao diện, không phải chi tiết dữ liệu |

---

## 3. Bản đồ bảng theo nhóm

Chi tiết cột nằm ở từng mục tính năng. Đây là bản đồ để nhìn tổng thể.

### Nhóm 1 — Nhân sự lõi

| Bảng | Vai trò | Tin cậy | Chi tiết ở |
|---|---|---|---|
| `NhanVien` | Bảng trung tâm, khoảng 90 cột | Chắc | [`01`](./01-nhan-su.md) |
| `NhanVienHocTap` · `NhanVienChungChi` · `NhanVienQuanHeGiaDinh` · `NhanVienKinhNghiem` · `NhanVienSucKhoe` · `NhanVienDangVien` · `NhanVienQuyetDinhKhac` | Bảng con, khóa ngoại `maNhanVien` | Chắc | [`01`](./01-nhan-su.md) |
| `PhongBan` (có cấp cha con) · `ChucDanh` · `CapBacChucVu` · `PhapNhan` · `HinhThucNhanVien` · `TrinhDo` · `ChuyenNganh` · `QuocTich` · `DanToc` · `TonGiao` · `DiaChinh` | Danh mục | Chắc | [`01`](./01-nhan-su.md) |

### Nhóm 2 — Hợp đồng và quyết định

| Bảng | Vai trò | Tin cậy | Chi tiết ở |
|---|---|---|---|
| `HopDongLaoDong` + `HopDongPhuCap` | Hợp đồng và phụ cấp theo hợp đồng | Chắc | [`01`](./01-nhan-su.md) |
| `ThangTinhLuong` | Thang bậc lương | Chắc | [`04`](./04-tien-luong.md) |
| `DieuChuyen` + `DieuChuyenChiTiet` | Điều chuyển, bổ nhiệm | Chắc | [`05`](./05-quyet-dinh-nhan-su.md) |
| `ThoiViec` + bảng bàn giao | Thôi việc | Chắc | [`05`](./05-quyet-dinh-nhan-su.md) |
| `PhieuDieuChinhLuong` + chi tiết | Đợt điều chỉnh lương | Chắc | [`05`](./05-quyet-dinh-nhan-su.md) |
| `DiLamLai` · `ThanhTichViPham` · `PhieuDieuChinhHopDong` | Các quyết định còn lại | Chắc / Đoán | [`05`](./05-quyet-dinh-nhan-su.md) |

### Nhóm 3 — Chấm công

`DuLieuChamCong` · `BangCongChiTiet` · `BangCongTongHop` · `BangCongTangCa` · `LichSuChotCong` · `PhanAnhCong` · `LoiDuLieuChamCong` · `Ca` · `PhanCa` · `MayChamCong` · `ViTriChamCong` · `NghiLe` · `LichLamBu` · `PhepNam`

Chi tiết ở [`03`](./03-cham-cong.md).

### Nhóm 4 — Đơn từ

`LoaiDonTu` (bảng cấu hình nhiều cột nhất quan sát được) · `DonNghiPhep` · `DonBoSungCong` · `DonCongTac` · `DonTangCa` · `DonTangCaPhongBan`

Chi tiết ở [`02`](./02-don-tu-va-duyet.md).

### Nhóm 5 — Tiền lương

`BangLuongCauHinh` · `BangLuongCot` · `BangLuongKy` · `BangLuongChiTiet` · `PhuCapCoDinh` · `KhoanCongTru` · `KhaiThueTheoKy` · `ThangThueGross` · `ThangThueNet`

Chi tiết ở [`04`](./04-tien-luong.md).

### Nhóm 6 — Quy trình duyệt

`QuyTrinhDuyet` · `QuyTrinhDuyetBuoc` · `LichSuDuyet`

Chi tiết ở [`02`](./02-don-tu-va-duyet.md).

### Nhóm 7 — Phân quyền và hệ thống

`NhomQuyen` · `NhomQuyenChiTiet` · `NguoiDung` · `ThietBiXacThuc` · `LichSuLogin` · `LichSuHoatDong` · `CauHinhXemHSNV` · `TruongDong` · `TruongDongGiaTri` · `MauIn` · `MauInHTML` · `DashboardDong`

Chi tiết ở [`08`](./08-he-thong-va-phan-quyen.md).

### Nhóm 8 — Tuyển dụng, đánh giá, tài sản

Chi tiết ở [`06`](./06-tuyen-dung-danh-gia.md) và [`07`](./07-workspace-tai-san.md).

---

## 4. Bốn cơ chế xuyên suốt

Bốn thứ này xuất hiện ở nhiều mục khác nhau. Phải quyết một lần, không quyết từng nơi.

### 4.1 Khuôn "áp dụng và loại trừ"

Xuất hiện ít nhất ở bốn chỗ: cấu hình loại đơn từ, cấu hình bảng lương, quy trình duyệt, phân quyền xem tài liệu.

Khuôn luôn giống nhau:

```
lsPhongBanApDung · lsChucDanhApDung · lsCapBacApDung · lsNhanVienApDung · lsHinhThucNVApDung
lsPhongBanLoaiTru · lsChucVuLoaiTru · lsNhanVienLoaiTru
toanTuApDung  (And / Or)
```

**Kết luận:** đây là một thành phần dùng lại được, không phải bốn lần viết riêng. Nếu mình làm, làm thành một bảng chung `PhamViApDung` gắn với `(loaiDoiTuong, maDoiTuong)`, và một hàm chung để đánh giá "người X có thuộc phạm vi này không". Viết bốn lần thì sẽ có bốn cách hiểu khác nhau về toán tử Or.

### 4.2 Trường động

Mười một màn hình cho phép người dùng khai thêm trường. Tên trường sinh theo mẫu `<kiểuDuLieu><maMenu>_<soThuTu>_<soThuTu>`:

| Ví dụ quan sát được | Đọc ra |
|---|---|
| `vanbanngan17_5_0` | Văn bản ngắn, màn hình 17 (hồ sơ nhân viên), trường thứ 5 |
| `danhsachtuychonmotluachon17_11_0` | Danh sách chọn một, màn hình 17, trường thứ 11 |
| `songuyen16_16_0` | Số nguyên, màn hình 16 (hợp đồng lao động), trường thứ 16 |
| `sizeao_3_0` | Trường tự đặt tên — cỡ áo |

Suy ra hai bảng, mức `Khá`:

- **`TruongDong`** — `maMenu` · `maTruong` · `tenHienThi` · `kieuDuLieu` · `thuTu` · `batBuoc` · `hienThi` · `danhSachGiaTri`
- **`TruongDongGiaTri`** — `maMenu` · `maPhieu` hoặc `maNhanVien` · `maTruong` · `giaTri`

Đánh đổi và khuyến nghị đã ghi ở [`08` mục phỏng đoán](./08-he-thong-va-phan-quyen.md): nếu làm thì chỉ mở cho hồ sơ nhân viên, có trần số trường, bắt khai mô tả.

### 4.3 Khuôn chứng từ

Mọi chứng từ trong hệ thống của họ đều có cùng một bộ trường nền:

`maPhieu` · `STATUS` · `fileDinhKem` · `filePDF` · `chooseNguoiKy` · `optionAddChungNhan` · `attrTaoMoi`

Cộng với `LichSuDuyet` dùng chung, khóa bằng cặp `loaiChungTu` + `maPhieu`.

**Đây là bằng chứng cho một kết luận kiến trúc:** họ coi "chứng từ" là một khái niệm chung của hệ thống, không phải mỗi phân hệ tự định nghĩa. Mọi thứ cắm vào bộ máy duyệt, bộ máy in, bộ máy ký, bộ máy đính kèm mà không phải viết lại.

Với ERP nhiều phân hệ, đây là quyết định kiến trúc quan trọng hơn bất kỳ chi tiết nghiệp vụ nào trong tài liệu này.

### 4.4 Khuôn quyết định

`soToTrinh` · `ngayToTrinh` · `soQuyetDinh` · `ngayQuyetDinh` · `ngayApDung` · `ngayKetThuc` · `noiDung` · `canCuQuyetDinh` · `filePDF`

Lặp lại ở sáu màn hình quyết định nhân sự. Chi tiết ở [`05`](./05-quyet-dinh-nhan-su.md).

---

## 5. Bốn câu hỏi phải trả lời trước khi viết mã

Đây là phần đáng đọc nhất của tài liệu này. Bốn câu hỏi dưới đây, nếu trả lời sai hoặc trả lời muộn, đều phải làm lại.

### Câu 1 — Bảng kết quả lương lưu thế nào

Số cột lương do người dùng khai. Bảng kết quả không thể có cột cố định. Ba đường:

| Đường | Được | Mất |
|---|---|---|
| Một dòng một ô — dòng thuộc tính | Linh hoạt hoàn toàn | Bảng phình nhanh. 500 người × 40 cột × 12 tháng = 240.000 dòng một năm. Báo cáo phải xoay bảng |
| Một dòng một người, giá trị trong một cột JSON | Gọn, đọc nhanh | Không lọc theo giá trị cột bằng SQL thường |
| Bảng rộng có sẵn 50 cột `col1`...`col50` | Nhanh, đơn giản | Bẩn, và có trần cứng |

Không quan sát được họ chọn đường nào.

**Đây là một lý do nữa để không làm lương trong bản 1** — không phải vì khó viết công thức, mà vì chọn sai kiểu lưu thì hai năm sau phải chuyển đổi dữ liệu lương lịch sử.

### Câu 2 — Tập cột phụ cấp là cố định hay khai được

Cùng một câu hỏi, xuất hiện ở phiếu điều chỉnh lương và ở hợp đồng lao động. Nếu là cột cứng thì thêm một khoản phụ cấp là một lần đổi bảng — vi phạm quy tắc 1 của bộ tài liệu ERP (cơ sở dữ liệu cũ chỉ thêm, không sửa).

Bằng chứng cho thấy họ khai được: danh sách cột trong phiếu điều chỉnh lương có những tên rõ ràng do khách hàng tự đặt — "PHỤ CẤP DI CHUYỂN CTR", "Hỗ trợ điều động/Kiêm nhiệm/khác".

### Câu 3 — Dữ liệu thô chấm công và bảng công có tách bảng không

Họ tách. `DuLieuChamCong` là dữ liệu máy, không sửa được. `BangCongChiTiet` là kết quả tổng hợp, sửa được.

**Trộn hai cái vào một bảng có cột trạng thái là lỗi thiết kế sẽ trả giá ở kỳ tính công đầu tiên** — vì lúc đó không còn phân biệt được số nào là máy ghi và số nào là người sửa, nên không giải quyết được khiếu nại.

### Câu 4 — Quyết định có ngày hiệu lực thì ai áp vào hồ sơ

Mọi quyết định đều có `ngayApDung` tách khỏi `ngayQuyetDinh`. Không quan sát được hệ thống tự áp vào hồ sơ nhân viên vào đúng ngày đó, hay phải có người bấm.

Hai đường đều dùng được, nhưng phải chọn trước:

- **Tự động** — cần công việc chạy nền hằng ngày, và cần cách xử lý khi quyết định bị hủy sau khi đã áp.
- **Thủ công** — đơn giản hơn, nhưng sẽ có quyết định quên áp, và hồ sơ sẽ lệch với văn bản.

Nếu chọn tự động thì hạ tầng chạy nền đã có sẵn (Celery đang chạy thật ở môi trường thật), nên chi phí không lớn.

---

## 6. Điều cần nói rõ về mức độ tin cậy

| Mức | Nghĩa | Dùng được để làm gì |
|---|---|---|
| `Chắc` | Tên cột đọc trực tiếp từ ô nhập liệu hoặc cột bảng | Đưa vào bản thiết kế nháp |
| `Khá` | Suy ra từ cấu trúc màn hình, hợp lý nhưng chưa xác nhận | Đưa vào để thảo luận, đánh dấu là giả định |
| `Đoán` | Chỉ có cơ sở gián tiếp | **Không đưa vào bản thiết kế.** Dùng làm câu hỏi mang đi phỏng vấn |

Toàn bộ tài liệu này là **tài liệu tham khảo**, không phải bản mô tả yêu cầu. Cấu trúc dữ liệu của mình phải sinh ra từ khảo sát nghiệp vụ của công ty mình, theo quyết định Đ2 ở [danh mục chờ quyết](../04-danh-muc-cho.md). Bảng phỏng đoán này chỉ dùng để **biết trước phải hỏi gì** và **biết trước chỗ nào sẽ khó**.
