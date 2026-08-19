# HỆ THỐNG, PHÂN QUYỀN VÀ CẤU HÌNH

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 5 khối, trong đó có 29 màn hình cấu hình và 9 màn hình báo cáo |

---

## Tóm tắt mục này

Đây là mục quan trọng nhất để trả lời câu hỏi của mình: **phần nền phân quyền hiện có của Thu mua có đủ dùng cho ERP không.**

Câu trả lời ngắn: **có, và mô hình của mình còn mạnh hơn của họ ở trục phạm vi dữ liệu.** Họ chỉ có ba mức cố định — Cá nhân, Quản lý, Toàn quyền. Mình có phạm vi nhiều chiều, cấp theo từng lượt (người dùng × vai trò). Không phải làm lại. Phần phải làm là **mở rộng cho đủ đối tượng**, không phải thiết kế lại.

Nhưng có hai chi tiết của họ nên lấy, và cả hai đều nhỏ so với giá trị mang lại:

- **Tách `XUẤT FILE` và `IMPORT FILE` thành hành động riêng.** Với dữ liệu nhân sự và lương, "được xem trên màn hình" và "được tải cả bảng về máy" là hai mức rủi ro khác hẳn nhau. Hiện nay ở Thu mua, xuất file đi chung với quyền xem.
- **Một màn hình cấu hình xem hồ sơ nhân viên riêng** (`CauHinhXemHSNV`). Tức phân quyền tới mức trường, không chỉ tới mức màn hình. Trưởng phòng xem được hồ sơ nhân viên phòng mình, nhưng không xem được lương và số căn cước.

Phần cấu hình thì họ có **29 màn hình**. Con số này là con số nên đưa vào buổi trình bày: nó cho thấy một hệ thống nhân sự chạy được không phải là "vài màn hình nhập liệu", mà là một bộ máy có phần khai báo lớn gần bằng phần nghiệp vụ.

---

## Danh sách chức năng

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| HT1 | Người dùng | `/NguoiDung/Index` | Tài khoản, mật khẩu, xác thực thiết bị | `[x]` |
| HT2 | Nhóm quyền | `/NhomQuyen/Index` | Ma trận quyền: đối tượng × hành động × phạm vi dữ liệu | `[x]` |
| HT3 | Cấu hình hệ thống | `/CauHinhHeThong/Index` | 29 màn hình khai báo | `[~]` |
| HT4 | Báo cáo | `/BC_*/Index` — 9 màn hình | Báo cáo theo từng mảng | `[~]` |
| HT5 | Dashboard động | `/DashboardDong/Index` | Nhúng báo cáo Power BI, phân quyền xem | `[ ]` |

Riêng quy trình duyệt (`/QuiTrinhDuyet/Index`) tuy thuộc khối hệ thống nhưng nằm ở [`02` Đơn từ và bộ máy duyệt](./02-don-tu-va-duyet.md), vì phần lớn giá trị của nó thể hiện qua đơn từ.

---

## HT1. Người dùng

| | |
|---|---|
| Đường dẫn | `/NguoiDung/Index` |
| Dùng để làm gì | Quản lý tài khoản đăng nhập, tách khỏi hồ sơ nhân viên |
| Ai dùng | Quản trị hệ thống |
| Mình có chưa | `[x]` |

**Cấu trúc màn hình** — bảy thẻ:

| Thẻ | Nội dung |
|---|---|
| Tài khoản đang hoạt động | Danh sách tài khoản còn dùng |
| Tài khoản đã ngưng | Danh sách đã đóng |
| Xác thực thiết bị | Thiết bị được phép dùng để chấm công |
| Import · Import Update · Export | Nhập xuất hàng loạt |
| Cấu hình | Quy tắc sinh tài khoản và mật khẩu |

**Bộ lọc** — dùng chung cho hai thẻ danh sách, mỗi thẻ có hậu tố riêng (`-taikhoandanghoatdong`, `-taikhoandangung`):

`maDanhMuc`, `maTrangThai`, `maPhongBanSearch`, `capBac`, `maChucDanh-filter`, `viewall`, `qSearch`, `pageSize`, và **`nhanVienChuaLogin`**.

**Trường của thẻ Cấu hình**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `loaiTenDangNhap` | Quy tắc sinh tên đăng nhập | Theo mã nhân viên, theo email, hoặc kiểu khác |
| `matKhauMacDinh` | Mật khẩu mặc định khi tạo hàng loạt | |
| `isBatBuocDoiPass` | Bắt đổi mật khẩu lần đăng nhập đầu | |
| `ngayDongTK` | Ngày đóng tài khoản | |
| `thoiGianLogout`, `loaiThoiGian` | Thời gian tự đăng xuất | |

**Trường của thẻ Xác thực thiết bị:** `maThietBi`, `idThietBi`, `trangThaiThietBi`, `tinhTrang`, lọc theo phòng ban và chức danh.

**Chỗ đáng chú ý — ba cái:**

1. **Bộ lọc `nhanVienChuaLogin`.** Lọc ra những người đã có tài khoản nhưng chưa bao giờ đăng nhập. Đây là chỉ số triển khai quan trọng nhất mà hầu hết hệ thống không có: nó trả lời câu "có bao nhiêu người thực sự đang dùng phần mềm". Với một công ty sắp đưa ERP cho hàng trăm người dùng, chỉ số này quyết định biết được triển khai thành công hay thất bại.
2. **Tài khoản tách khỏi hồ sơ nhân viên.** Danh sách hồ sơ nhân viên có cột riêng "tạo tài khoản" — tức không phải cứ có hồ sơ là có tài khoản. Đúng nghiệp vụ: công nhân thời vụ có hồ sơ nhưng không cần đăng nhập. Hệ thống Thu mua hiện nay cũng theo mô hình này.
3. **Xác thực thiết bị.** Chỉ có nghĩa khi chấm công qua điện thoại. Không cần nếu không làm chấm công.

---

## HT2. Nhóm quyền

| | |
|---|---|
| Đường dẫn | `/NhomQuyen/Index` |
| Dùng để làm gì | Khai quyền cho từng nhóm: làm được gì, trên đối tượng nào, thấy dữ liệu tới đâu |
| Ai dùng | Quản trị hệ thống |
| Mình có chưa | `[x]` — mô hình gần trùng |

**Cấu trúc màn hình** — chọn nhóm quyền ở ô `maNQuyen`, bấm tìm, hiện ra ma trận. Cột `viewall` để hiện toàn bộ.

**Cột của ma trận:**

| Nhóm cột | Các ô |
|---|---|
| Tên công việc | Tên đối tượng được phân quyền |
| Phân Quyền Theo Công Việc | **Xem · Tạo mới · Sửa · Xóa · Xuất file · Import file** |
| Phân Quyền Theo Dữ Liệu | **Cá nhân · Quản lý · Toàn quyền** |

Số dòng đối tượng: khoảng **118**.

**Mười nhóm quyền trong bản demo**, kèm mã:

| Mã | Tên |
|---|---|
| `Q_NhanVien` | Nhân Viên |
| `CCH` | Chấm công hộ |
| `Q_TinhCong` | Chấm Công |
| `Q_TinhLuong` | Tính Lương |
| `QLTS` | QL Tài sản |
| `Tuyendung` | QL Nhân sự tuyển dụng |
| `STV001` | Sau thôi việc |
| `Q_SAUTHOIVIEC` | Sau Thôi việc |
| `Q_Admin` | Admin HT |
| (một mã hỏng, xem bên dưới) | Tài sản |

**Chỗ đáng chú ý — bốn cái:**

1. **Mô hình hai trục của họ trùng với mô hình hai trục của mình.** Trục một là hành động theo nhóm quyền, trục hai là phạm vi dữ liệu. Đây là bằng chứng bên ngoài cho thấy hướng thiết kế hiện tại của Thu mua đúng, không phải chỉ là lựa chọn tình cờ.

2. **Nhưng trục phạm vi của họ yếu hơn của mình.** Ba mức cố định — Cá nhân, Quản lý, Toàn quyền. Không mô tả được "thấy dữ liệu của hai phòng ban nhưng không phải cả công ty", cũng không mô tả được phạm vi theo chiều khác chiều tổ chức. Mô hình của mình cấp phạm vi theo từng lượt (người dùng × vai trò) và theo nhiều chiều, nên mềm hơn.

3. **`XUẤT FILE` và `IMPORT FILE` là hành động riêng.** Đây là chi tiết đáng lấy nhất của màn hình này. Ở Thu mua hiện nay, ai xem được thì xuất được. Với dữ liệu nhân sự và lương, khác biệt giữa hai mức đó là khác biệt giữa "xem một hồ sơ" và "mang cả bảng lương công ty ra khỏi hệ thống".

4. **Có hai nhóm cùng nghĩa "Sau thôi việc" với hai mã khác nhau (`STV001` và `Q_SAUTHOIVIEC`), và một nhóm có mã bị lỗi mã hóa tiếng Việt** — mã hiển thị là `Qu?n lý xu?t tài s?n`. Hai quan sát này cùng nói một điều: **khóa nhóm quyền là chuỗi do người dùng tự đặt**, nên theo thời gian sẽ trùng lặp và sẽ dính lỗi mã hóa.

   Bài học này trùng đúng hai quy tắc mình đã có: không lấy tiếng Việt làm khóa, và không chèn tiếng Việt qua đường dòng lệnh. Chính hệ thống thương mại của họ cũng dính.

**Đối chiếu chi tiết với hệ thống Thu mua:**

| Mục | Họ | Mình |
|---|---|---|
| Trục hành động | 6 hành động cố định, khai theo nhóm quyền | Ma trận (đối tượng × hành động) theo vai trò, chặn bằng `require(entity, action)` |
| Trục phạm vi dữ liệu | 3 mức cố định | Cấp theo lượt (người dùng × vai trò), nhiều chiều, áp bằng `apply_scope(...)` |
| Số đối tượng | ~118 | 29 |
| Xuất file | Là hành động riêng | Chưa tách, đi chung với quyền xem |
| Khóa nhóm quyền | Chuỗi người dùng tự đặt, đã có lỗi mã hóa | Không dính lỗi này |
| Điểm yếu đã biết của mình | | `SCOPE_FIELDS` mới khai 9 trên 29 đối tượng, và **thiếu một chiều thì hệ thống im lặng không lọc** |

**Điểm yếu ở dòng cuối là việc phải xử lý trước khi mở rộng sang HRM, không phải sau.** Dữ liệu Thu mua rò rỉ giữa các phòng ban là chuyện khó chịu. Dữ liệu lương rò rỉ là chuyện khác hẳn về mức độ. Một đối tượng khai thiếu chiều phạm vi mà hệ thống không báo lỗi thì lỗi đó sẽ không ai phát hiện cho tới khi có người nhìn thấy thứ không được phép nhìn.

---

## HT3. Cấu hình hệ thống

| | |
|---|---|
| Đường dẫn | `/CauHinhHeThong/Index` |
| Dùng để làm gì | Toàn bộ phần khai báo của hệ thống |
| Ai dùng | Quản trị hệ thống, phòng Nhân sự |
| Mình có chưa | `[~]` — có phần danh mục, thiếu phần khai luật |

**Cách truy cập:** các mục cấu hình **không có đường dẫn riêng**. Mỗi mục là một ô trên lưới, đánh dấu bằng thuộc tính `ma`, phải bấm vào mới mở. Ghi lại đây vì nếu người khác đi khảo sát tiếp sẽ mất thời gian tìm.

**29 mục cấu hình**, kèm mã:

| # | Mã | Tên | Thuộc mảng |
|---|---|---|---|
| 1 | `ThongTinCongTy` | Thông tin công ty | Nền |
| 2 | `BaoMatNangCao` | Bảo mật nâng cao | Nền |
| 3 | `DanhMucChucVu` | Cấu hình chức vụ | Danh mục |
| 4 | `DanhMuc` | Cấu hình danh mục | Danh mục |
| 5 | `PhongBan` | Cấu hình phòng ban | Danh mục |
| 6 | `CauHinhDiaChi` | Cấu hình địa chỉ | Danh mục |
| 7 | `GroupTag` | Group nhân viên | Nhân sự |
| 8 | `CauHinhXemHSNV` | **Cấu hình xem hồ sơ nhân viên** | Phân quyền |
| 9 | `TruongDongDeXuat` | Cấu hình trường động | Nền |
| 10 | `CauHinhDeXuat` | **Cấu hình form** | Nền |
| 11 | `Onboarding` | Onboarding | Nhân sự |
| 12 | `Offboarding` | Offboarding | Nhân sự |
| 13 | `LoaiDonTu` | Cấu hình loại đơn từ | Đơn từ |
| 14 | `BC_LoaiChamCong` | Cấu hình loại chấm công | Chấm công |
| 15 | `BangCongCauHinh` | Cấu hình bảng công | Chấm công |
| 16 | `PhepNamCauHinh` | Cấu hình phép năm | Chấm công |
| 17 | `BangLuongCauHinh` | **Cấu hình bảng lương** | Tiền lương |
| 18 | `ThanhTinhThue` | Cấu hình thang tính thuế | Tiền lương |
| 19 | `CauHinhSinhNhat` | Cấu hình sinh nhật | Tiện ích |
| 20 | `ThongBaoDong` | **Cấu hình Automation** | Nền |
| 21 | `CauHinhDuAn_CongViec` | Cấu hình công việc | Workspace |
| 22 | `MauIn` | Cấu hình mẫu in | Nền |
| 23 | `MauInHTML` | Cấu hình mẫu email | Nền |
| 24 | `CauHinhDashBoard` | **Cấu hình icon home** | Nền |
| 25 | `CauHinhThongBaoMail` | Cấu hình thông báo | Nền |
| 26 | `Menu` | Menu hệ thống | Nền |
| 27 | `XoaLichSuDuyet` | Xóa lịch sử duyệt | Duyệt |
| 28 | `LichSuHoatDong` | Lịch sử hoạt động | Nền |
| 29 | `TongQuanCVCanDuyet` | Công việc cần duyệt | Duyệt |

Chi tiết của bốn mục nặng nhất nằm ở tài liệu tương ứng: `LoaiDonTu` ở [`02`](./02-don-tu-va-duyet.md), `BangCongCauHinh` và `PhepNamCauHinh` ở [`03`](./03-cham-cong.md), `BangLuongCauHinh` và `ThanhTinhThue` ở [`04`](./04-tien-luong.md).

**Chỗ đáng chú ý — năm mục cần nói riêng:**

**`CauHinhXemHSNV` — cấu hình xem hồ sơ nhân viên.** Có một màn hình cấu hình riêng chỉ để khai ai được xem trường nào trên hồ sơ nhân viên. Điều này nói lên rằng phân quyền theo màn hình là không đủ cho dữ liệu nhân sự — phải phân quyền tới mức trường. Trưởng phòng cần xem hồ sơ người phòng mình, nhưng không được xem lương, không được xem số căn cước, không được xem số tài khoản ngân hàng.

Hệ thống Thu mua hiện nay chưa có tầng phân quyền theo trường. **Đây là hạng mục phải đưa vào bảng chốt phạm vi HRM, không được để sót** — thêm sau khi hồ sơ đã chạy thật là việc đắt, vì phải rà lại từng chỗ hiển thị.

**`CauHinhDeXuat` — cấu hình form.** Kết hợp với việc trong danh sách 88 loại công việc của quy trình duyệt có những mục tên "Form HTML", "Đề xuất chủ trương", thì rõ là hệ thống có bộ dựng biểu mẫu: người dùng tự tạo một loại phiếu mới, gắn quy trình duyệt vào, không cần lập trình.

Đây là tính năng mạnh và cũng là cái bẫy. Mạnh vì mọi đề xuất lặt vặt trong công ty đều có chỗ chạy. Bẫy vì ba năm sau sẽ có 80 loại form không ai biết cái nào còn dùng. **Khuyến nghị: không làm trong bản 1.**

**`ThongBaoDong` — cấu hình Automation.** Khai luật "khi có sự kiện X thì làm việc Y". Đây là họ hàng gần của module webhook mà mình đã chốt làm trong năm nay (quyết định Đ4). Đáng đọc kỹ khi thiết kế phần lõi webhook, vì phần khó của cả hai giống nhau: khai sự kiện ở đâu, ai được khai, và làm sao chặn vòng lặp.

**`CauHinhDashBoard` — cấu hình icon home.** Chính là lưới biểu tượng phân hệ mà mình định làm ở nhóm FE10. Họ làm được cấu hình, không viết cứng. Đáng chụp màn hình để đối chiếu.

**`Onboarding` và `Offboarding`.** Khai bộ việc phải làm khi một người vào và khi một người ra. Nối trực tiếp với màn hình thôi việc ở [`05` Quyết định nhân sự](./05-quyet-dinh-nhan-su.md). Rẻ để làm, và là thứ phòng Nhân sự cảm nhận được ngay.

---

## HT4. Báo cáo

Chín màn hình báo cáo, mỗi màn hình là một danh sách các báo cáo con.

| Đường dẫn | Tên | Các báo cáo bên trong |
|---|---|---|
| `/BC_Dashboard/Index` | BC Dashboard | Bảng tổng quan |
| `/BC_NhanSu/Index` | BC Nhân sự | BC Hồ sơ nhân viên · BC Bằng cấp nhân viên · BC Kinh nghiệm nhân viên · Báo cáo thôi việc · Sinh nhật nhân viên · BC Tình trạng sức khỏe nhân viên · BC Tình hình sử dụng lao động · Báo cáo giấy phép lao động sắp hết hạn · BC giới thiệu nhân viên · Hợp đồng sắp hết hạn |
| `/BC_ChamCong/Index` | BC Chấm công | |
| `/BC_TienLuong/Index` | BC Tiền lương | |
| `/BC_BaoHiem/Index` | BC Bảo hiểm và thuế thu nhập cá nhân | |
| `/BC_CongViec/Index` | BC Công việc | Báo cáo công việc theo nhân viên · Báo cáo nhật ký công việc theo ngày |
| `/BC_TuyenDung/Index` | BC Tuyển dụng | |
| `/BC_TaiSan/Index` | BC Tài sản | Đang sử dụng · Đang tồn kho · Lịch sử nhập xuất tài sản · Báo cáo nhập xuất tồn · BC Khấu hao tài sản · BC Kiểm kê tài sản |
| `/BC_Elearning/Index` | BC E-Learning | **Ngoài phạm vi khảo sát** |

**Chỗ đáng chú ý:** trong danh sách báo cáo nhân sự có **hai báo cáo cảnh báo hạn**: "Báo cáo giấy phép lao động sắp hết hạn" và "Hợp đồng sắp hết hạn". Đây không phải báo cáo thống kê — đây là báo cáo phòng ngừa. Hợp đồng hết hạn mà không ai nhớ là rủi ro pháp lý thật, và là một trong những lý do rõ ràng nhất để phòng Nhân sự muốn có phần mềm.

Nếu phải chọn đúng một báo cáo làm trước cho HRM bản 1, chọn "Hợp đồng sắp hết hạn".

---

## HT5. Dashboard động

| | |
|---|---|
| Đường dẫn | `/DashboardDong/Index` |
| Dùng để làm gì | Nhúng báo cáo từ Power BI vào hệ thống, có phân quyền xem |
| Ai dùng | Quản trị hệ thống |
| Mình có chưa | `[ ]` |

**Cột bảng:** STT · Tên Dashboard · Loại · Quyền xem dữ liệu · Người lập · Ngày lập · Xem báo cáo · Thao tác.

**Trường:** `tenDashboard`, `loaidashboard`, `loai`, `lsPB` (danh sách phòng ban), `lsCD` (danh sách chức danh), `lsNV` (danh sách nhân viên), `qSearch`, `pageSize`.

**Chỗ đáng chú ý:** đây là cách xử lý đáng học đối với bài toán báo cáo. Thay vì viết mọi báo cáo trong phần mềm, họ để công cụ báo cáo bên ngoài làm phần vẽ, còn phần mềm chỉ làm hai việc: nhúng vào đúng chỗ, và **quản lý ai được xem** qua bộ ba `lsPB` / `lsCD` / `lsNV`.

Với mình, đây là lựa chọn nên cân nhắc thật sự khi tới phần báo cáo ERP: viết một trăm màn hình báo cáo trong ứng dụng là việc không bao giờ hết, vì mỗi người muốn một kiểu nhìn khác nhau.

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `NhomQuyen` | `maNhomQuyen` (chuỗi tự đặt), `tenNhomQuyen` | Chắc |
| `NhomQuyenChiTiet` | `maNhomQuyen`, `maDoiTuong`, `xem`, `taoMoi`, `sua`, `xoa`, `xuatFile`, `importFile`, `phamViDuLieu` | Chắc |
| `NguoiDung` | `tenDangNhap`, `maNhanVien`, `matKhau`, `trangThai`, `maNhomQuyen`, `ngayDongTK`, `batBuocDoiPass` | Chắc |
| `ThietBiXacThuc` | `maThietBi`, `idThietBi`, `maNhanVien`, `trangThai` | Khá |
| `LichSuLogin` | `tenDangNhap`, `thoiDiem`, địa chỉ | Chắc |
| `LichSuHoatDong` | Nhật ký thao tác toàn hệ thống | Chắc |
| `CauHinhXemHSNV` | `maNhomQuyen` hoặc `maChucDanh`, `maTruong`, `duocXem` | Khá — chưa mở được màn hình để xác nhận |
| `TruongDong` | `maMenu`, `maTruong`, `tenHienThi`, `kieuDuLieu`, `thuTu`, `batBuoc`, `hienThi`, `danhSachGiaTri` | Khá |
| `TruongDongGiaTri` | `maMenu`, `maPhieu` hoặc `maNhanVien`, `maTruong`, `giaTri` | Khá |
| `MauIn`, `MauInHTML` | Mẫu in và mẫu email theo loại chứng từ | Chắc |
| `DashboardDong` | `tenDashboard`, `loaiDashboard`, `duongDan`, `lsPB`, `lsCD`, `lsNV`, `nguoiLap`, `ngayLap` | Chắc |

**Về trường động** — quan sát được tên trường sinh theo mẫu `<kiểuDuLieu><maMenu>_<soThuTu>_<soThuTu>`, ví dụ `vanbanngan17_5_0`, `danhsachtuychonmotluachon17_11_0`, `songuyen16_16_0`. Mười một màn hình cho phép khai thêm trường.

Cơ chế này hợp với quy tắc 1 của bộ tài liệu (cơ sở dữ liệu cũ chỉ thêm, không sửa), nhưng có giá:

| Được | Mất |
|---|---|
| Người dùng tự thêm trường, không chờ đợt phát hành | Không đặt được ràng buộc dữ liệu ở tầng cơ sở dữ liệu |
| Không phải chạy lệnh đổi bảng trên hệ thống đang chạy | Truy vấn và báo cáo phức tạp hơn nhiều |
| Mỗi pháp nhân khai trường riêng được | Không đánh chỉ mục hiệu quả |
| | Ba năm sau có 200 trường không ai biết để làm gì |

**Khuyến nghị:** nếu làm, làm cho **đúng một đối tượng là hồ sơ nhân viên**, giới hạn số trường, bắt khai mô tả và người chịu trách nhiệm. Không mở cho mọi màn hình như họ.

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| Tách `XUẤT FILE` và `IMPORT FILE` thành hành động riêng | **Lấy ngay** | Sửa nhỏ, giá trị lớn. Làm trước khi có dữ liệu lương trong hệ thống, không phải sau | Thêm hai hành động vào ma trận sẵn có. Mặc định tắt cho mọi vai trò trừ vai trò quản trị, rồi mở dần |
| Khai đủ `SCOPE_FIELDS` cho toàn bộ đối tượng, và **báo lỗi khi thiếu** | **Lấy ngay** — đây là việc của mình, không phải của họ | Hiện chỉ khai 9 trên 29, và thiếu thì im lặng không lọc. Đây là lỗ hổng, không phải nợ kỹ thuật thường | Đổi hành vi: thiếu khai phạm vi thì chặn, không phải bỏ qua. Chấp nhận vỡ vài chỗ lúc triển khai còn hơn rò rỉ dữ liệu lương |
| `CauHinhXemHSNV` — phân quyền theo trường | **Lấy**, và phải nằm trong bảng chốt phạm vi HRM | Dữ liệu nhân sự có trường nhạy cảm nằm chung màn hình với trường bình thường. Phân quyền theo màn hình không giải được | Không cần màn hình cấu hình đầy đủ ngay. Bản đầu: khai cứng một nhóm trường nhạy cảm (lương, căn cước, tài khoản ngân hàng, sức khỏe) và một quyền riêng để xem nhóm đó |
| Bộ lọc `nhanVienChuaLogin` | **Lấy ngay** | Rẻ nhất trong cả danh sách. Là chỉ số đo triển khai ERP có thành công không | Không cần sửa gì |
| `Onboarding` / `Offboarding` | **Lấy sau** | Rẻ, và phòng Nhân sự thấy giá trị ngay | Làm dạng danh sách việc gắn với quyết định, không làm thành module riêng |
| Báo cáo "Hợp đồng sắp hết hạn" | **Lấy sau**, ngay khi có hợp đồng | Rủi ro pháp lý thật. Là lý do dễ giải thích nhất cho việc đầu tư phần mềm nhân sự | Kèm thông báo chủ động, không chỉ là báo cáo phải mở ra xem |
| `ThongBaoDong` — Automation | **Đọc tham khảo**, không lấy màn hình | Cùng bài toán với module webhook đã chốt làm trong T12 | Đọc để thiết kế phần lõi webhook, không bê màn hình |
| `DashboardDong` | **Lấy sau**, vòng sau | Giải bài toán "mỗi người muốn một báo cáo khác nhau" mà không phải viết vô hạn màn hình | Quyết định công cụ báo cáo trước, rồi mới làm phần nhúng |
| `CauHinhDeXuat` — bộ dựng form | **Không lấy trong bản 1** | Mạnh nhưng sinh ra 80 loại form vô chủ sau vài năm | Nếu sau này làm, bắt buộc có người chịu trách nhiệm cho mỗi form và cơ chế ngừng dùng |
| Trường động cho mọi màn hình | **Không lấy như họ** | Đánh đổi nêu ở trên | Chỉ mở cho hồ sơ nhân viên, có trần số trường |
| Nhóm quyền dùng chuỗi tiếng Việt làm khóa | **Không lấy** | Chính họ đã dính lỗi mã hóa và trùng nhóm | Giữ cách của mình |

**Việc cần làm ngay, không chờ HRM:** ba dòng đầu bảng trên. Cả ba đều nằm trong phần nền phân quyền, đều nhỏ, và đều đắt gấp nhiều lần nếu làm sau khi dữ liệu nhân sự đã vào hệ thống.
