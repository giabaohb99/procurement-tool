# WORKSPACE VÀ TÀI SẢN

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 13 (WS1–WS9 + TS1–TS4) |

## Tóm tắt mục này

Tài liệu này ghi lại hai khối rời nhau: **Workspace** (WS1–WS9) và **Tài sản** (TS1–TS4). Hai khối không có quan hệ nghiệp vụ trực tiếp với nhau và chỉ nằm chung một tài liệu vì cùng nằm ngoài lõi HRM.

Workspace bao gồm mạng xã hội nội bộ, lịch họp, chat, tài liệu, công văn, ký số, dự án và quản lý công việc. Đây là nhóm công cụ cộng tác chứ không phải nghiệp vụ quản trị nhân sự. Gộp toàn bộ khối này vào phạm vi dự án HRM sẽ làm phạm vi phình gấp đôi mà không phục vụ mục tiêu chính là quản lý con người, hợp đồng, lương và chấm công.

Hệ thống hiện có của nhóm đã có thông báo trong chuông và web push `[x]`, Trung tâm hướng dẫn sử dụng riêng `[~]` (gần với WS4 Tài liệu), và Project-M `[~]` (gần với WS7 Dự án và WS8 Công việc). Những chức năng còn lại trong Workspace đều chưa có.

Khối Tài sản có giá trị thực hơn vì liên kết trực tiếp với hồ sơ nhân viên (thẻ Tài sản trên hồ sơ) và đi qua bộ máy quy trình duyệt. Đây là khối nên đánh giá kỹ hơn trong buổi phỏng vấn phòng Nhân sự.

Mục tiêu tài liệu này: liệt kê đủ để buổi khảo sát có câu hỏi cụ thể, không phải để cam kết lấy bất kỳ chức năng nào trong Workspace.

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| WS1 | Truyền thông nội bộ | `/MangXaHoi/Index` | Bảng tin, đăng bài nội bộ | `[ ]` |
| WS2 | Lịch biểu | `/LichHop/Index` | Đặt lịch họp, đặt phòng, gửi nhắc | `[ ]` |
| WS3 | Chat | `/Chat/Index` | Nhắn tin nội bộ | `[ ]` |
| WS4 | Tài liệu | `/TaiLieu/Index` | Lưu trữ, phân quyền, chia sẻ tài liệu | `[~]` |
| WS5 | Công văn | `/CongVan/Index` | Quản lý công văn đến/đi/nội bộ | `[ ]` |
| WS6 | Ký số | `/ChuKySo/Index` | Ký duyệt hồ sơ bằng chữ ký số | `[ ]` |
| WS7 | Dự án | `/DuAn/Index` | Quản lý danh sách dự án | `[~]` |
| WS8 | Quản lý công việc | `/QLCongViec/Index` | Task theo nhiều góc nhìn, giao việc | `[~]` |
| WS9 | Báo cáo công việc theo nhân viên | `/BaoCaoCongViecTheoNhanVien/Index` | Báo cáo tiến độ công việc | `[ ]` |
| TS1 | Danh sách tài sản | `/DSTaiSan/Index` | Danh mục tài sản, thuộc tính, nhóm | `[ ]` |
| TS2 | Phiếu nhập tài sản | `/NhapTaiSan/Index` | Ghi nhận nhập kho tài sản | `[ ]` |
| TS3 | Phiếu xuất tài sản | `/XuatTaiSan/Index` | Ghi nhận xuất kho cho nhân viên/phòng ban | `[ ]` |
| TS4 | Biên bản bàn giao tài sản | `/BienBanBanGiaoTaiSan/Index` | Bàn giao tài sản qua quy trình duyệt | `[ ]` |

---

## Phần 1 — Workspace

## WS1. Truyền thông nội bộ

| | |
|---|---|
| Đường dẫn | `/MangXaHoi/Index` |
| Dùng để làm gì | Đăng bài tin nội bộ dạng bảng tin (mạng xã hội nội bộ), có Export |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Một trang danh sách bài đăng. Có nút Export.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `clsQSearch` | Ô tìm kiếm bài đăng | Trường lọc duy nhất quan sát được |

---

## WS2. Lịch biểu

| | |
|---|---|
| Đường dẫn | `/LichHop/Index` |
| Dùng để làm gì | Tạo lịch họp, đặt phòng họp, gửi nhắc nhở, xác nhận tham dự |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Trang danh sách lịch biểu với bộ lọc nhiều chiều. Các nút hành động: Tạo lịch biểu, Tìm kiếm, Xóa, Gửi email, Xác nhận, Lưu.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `phongBanSeach` | Lọc theo phòng ban | Trường bộ lọc |
| `nhanVienSearch` | Lọc theo nhân viên | Trường bộ lọc |
| `phongHopSearch` | Lọc theo phòng họp | Trường bộ lọc |
| `subject` | Tiêu đề lịch biểu | |
| `timeBegin` | Thời gian bắt đầu | |
| `timeFinish` | Thời gian kết thúc | |
| `loaiLichBieu` | Phân loại lịch biểu | |
| `phongHop` | Phòng họp được đặt | Kết hợp chức năng đặt phòng vào lịch |
| `nhacTruoc` | Thời lượng nhắc trước | Số |
| `loaiNhacTruoc` | Đơn vị thời gian nhắc trước | Phút/giờ — phỏng đoán |
| `ngayDong` | Ngày đóng/hết hạn lịch | |
| `tbQuaEmail` | Gửi thông báo qua email | Cờ bật/tắt — phỏng đoán |
| `lsNhanVien` | Danh sách nhân viên tham dự | |
| `lsChucVu` | Danh sách chức vụ tham dự | |
| `lsPhongBan` | Danh sách phòng ban tham dự | |
| `body` | Nội dung/mô tả lịch biểu | |

**Chỗ đáng chú ý:** `phongHop` xuất hiện ngay trong form lịch biểu, nghĩa là đặt phòng họp và đặt lịch là một thao tác duy nhất. Hệ thống nhắc nhở tách đôi thành `nhacTruoc` (số) và `loaiNhacTruoc` (đơn vị), linh hoạt hơn nhắc cố định.

---

## WS3. Chat

| | |
|---|---|
| Đường dẫn | `/Chat/Index` |
| Dùng để làm gì | Nhắn tin nội bộ theo thời gian thực |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Giao diện chat. Không có trường dữ liệu form nào quan sát được trong dữ liệu thô ngoài đường dẫn.

---

## WS4. Tài liệu

| | |
|---|---|
| Đường dẫn | `/TaiLieu/Index` |
| Dùng để làm gì | Lưu trữ tài liệu theo thư mục, phân quyền xem/tải/sửa/xóa theo nhân viên hoặc phòng ban, giới hạn quyền theo khoảng thời gian |
| Mình có chưa | `[~]` Trung tâm hướng dẫn sử dụng phục vụ mục đích gần nhưng không có phân quyền chi tiết theo thư mục |

**Cấu trúc màn hình**

Trang danh sách thư mục và tệp. Có tìm kiếm toàn văn. Hỗ trợ cả tệp tải lên (`FileUpload`) và liên kết ngoài (`link_upload`). Xóa tài liệu yêu cầu xác thực bổ sung.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `inputSearch` | Tìm kiếm toàn bộ tài liệu | |
| `nameFolder` | Tên thư mục | |
| `noiDungFolder` | Mô tả thư mục | |
| `hasTagFolder` | Thẻ tag của thư mục | |
| `noiDungFile` | Mô tả tệp | |
| `hasTagFile` | Thẻ tag của tệp | |
| `name_link_upload` | Tên hiển thị cho liên kết | |
| `link_upload` | URL liên kết ngoài | |
| `noiDungLink` | Mô tả liên kết | |
| `hasTagLink` | Thẻ tag của liên kết | |
| `nameNew` | Tên thư mục con mới | |
| `noiDungFileFolder` | Mô tả tệp trong thư mục | |
| `hasTagFileFolder` | Thẻ tag tệp trong thư mục | |
| `matKhauImport` | Mật khẩu đăng nhập để xác nhận xóa | Bắt buộc nhập khi xóa |
| `lyDoXoa` | Lý do xóa tài liệu | Bắt buộc nhập khi xóa |
| `hinhAnh` | Ảnh đính kèm | |
| `FileUpload` | Tệp tải lên | |
| `lsNhanVien` | Danh sách nhân viên được cấp quyền | Thuộc khối phân quyền thư mục |
| `lsPhongBan` | Danh sách phòng ban được cấp quyền | Thuộc khối phân quyền thư mục |
| `lsChucVu` | Danh sách chức vụ được cấp quyền | Thuộc khối phân quyền thư mục |
| `toanTuApDung` | Toán tử áp dụng (AND/OR) giữa các điều kiện quyền | Phỏng đoán |
| `permissionWatch` | Quyền xem | Cờ quyền |
| `permissionUpload` | Quyền tải lên | Cờ quyền |
| `permissionTaiVe` | Quyền tải về | Cờ quyền, tách riêng khỏi xem |
| `permissionDelete` | Quyền xóa | Cờ quyền |
| `permissionEdit` | Quyền sửa | Cờ quyền |
| `permissionAdmin` | Quyền quản trị thư mục | Cờ quyền |
| `ngayXemTu` | Ngày bắt đầu được phép xem | Giới hạn thời gian xem |
| `ngayXemDen` | Ngày kết thúc được phép xem | Giới hạn thời gian xem |
| `khungGioTu` | Giờ bắt đầu được phép xem trong ngày | Giới hạn khung giờ |
| `khungGioDen` | Giờ kết thúc được phép xem trong ngày | Giới hạn khung giờ |
| `ngayXemTuEditPQ` | Ngày bắt đầu khi sửa quyền | Phiên bản sửa của trường trên |
| `ngayXemDenEditPQ` | Ngày kết thúc khi sửa quyền | |
| `khungGioTuEditPQ` | Giờ bắt đầu khi sửa quyền | |
| `khungGioDenEditPQ` | Giờ kết thúc khi sửa quyền | |

**Chỗ đáng chú ý:** Quyền tải về (`permissionTaiVe`) tách riêng khỏi quyền xem (`permissionWatch`) — có thể cho xem trên trình duyệt mà không cho lưu về máy. Quyền xem giới hạn được theo khoảng ngày và theo khung giờ trong ngày, chi tiết hơn hầu hết hệ thống tài liệu thông thường. Xóa tài liệu bắt buộc nhập lại mật khẩu đăng nhập và lý do — cơ chế kiểm soát xóa nhầm.

---

## WS5. Công văn

| | |
|---|---|
| Đường dẫn | `/CongVan/Index` |
| Dùng để làm gì | Theo dõi công văn đến, công văn đi, công văn nội bộ; quản lý sổ công văn và danh bạ đơn vị nhận/gửi |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Năm thẻ: Công văn đến, Công văn đi, Công văn nội bộ, Sổ công văn, Danh bạ. Có Export và Import.

**Trường dữ liệu**

Bộ lọc dùng chung cho ba thẻ đầu (mỗi thẻ thêm hậu tố riêng vào tên trường):

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `trangThai` | Trạng thái công văn | |
| `loaiNgay` | Loại ngày lọc (ngày tạo/ngày nhận...) | |
| `loaiCongVan` | Phân loại công văn | |
| `loaiToTrinh` | Loại tờ trình | |
| `doKhan` | Độ khẩn | Gắn trực tiếp lên từng công văn |
| `baoMat` | Mức độ bảo mật | Gắn trực tiếp lên từng công văn |
| `qSearch` | Tìm kiếm toàn văn | |

Thẻ Sổ công văn bổ sung:

| Trường | Nghĩa |
|---|---|
| `loaiSo-socongvan` | Loại sổ công văn |
| `trangThai-socongvan` | Trạng thái sổ |

Thẻ Danh bạ bổ sung:

| Trường | Nghĩa |
|---|---|
| `trangThai-danhba` | Trạng thái đơn vị trong danh bạ |

**Chỗ đáng chú ý:** `doKhan` và `baoMat` là hai trường độc lập trên từng công văn — hỗ trợ phân loại độ khẩn và mức bảo mật song song, phù hợp cơ quan có quy định về xử lý hồ sơ mật.

---

## WS6. Ký số

| | |
|---|---|
| Đường dẫn | `/ChuKySo/Index` |
| Dùng để làm gì | Quản lý hồ sơ trình ký, hồ sơ mẫu, chữ ký số phần cứng (USB token) và chứng nhận chữ ký |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Năm thẻ: Hồ sơ trình ký, Hồ sơ mẫu, Chữ ký số, Chứng nhận chữ ký, Import chữ ký nhân viên. Màn hình cá nhân bổ sung tại `/ChuKySo/Index_Signature` (chữ ký cá nhân của từng người dùng).

Nút hành động: Thêm, Lấy thông tin usb, Save, Thực hiện, Thoát.

**Chỗ đáng chú ý:** Nút "Lấy thông tin usb" xác nhận hệ thống hỗ trợ USB token (chữ ký số phần cứng), không chỉ chữ ký số phần mềm. Thẻ "Import chữ ký nhân viên" cho thấy có thể nạp hàng loạt chữ ký từ file.

---

## WS7. Dự án

| | |
|---|---|
| Đường dẫn | `/DuAn/Index` |
| Dùng để làm gì | Quản lý danh sách dự án, xem theo ba chế độ hiển thị |
| Mình có chưa | `[~]` Project-M phục vụ mục đích tương tự |

**Cấu trúc màn hình**

Ba thẻ: Danh sách, KanBan, Grid. Không có trường dữ liệu form nào quan sát được trong dữ liệu thô ngoài ba chế độ xem này.

---

## WS8. Quản lý công việc

| | |
|---|---|
| Đường dẫn | `/QLCongViec/Index` |
| Dùng để làm gì | Giao việc, theo dõi tiến độ công việc theo bốn góc nhìn người dùng, xem theo nhiều chế độ hiển thị |
| Mình có chưa | `[~]` Project-M có tính năng gần, nhưng bốn hộp việc phân theo vai trò là khác biệt |

**Cấu trúc màn hình**

Sáu thẻ: Danh sách, KanBan, Lịch biểu, Sơ đồ Gantt, Export, Import. Bốn hộp việc: "Liên quan tới tôi", "Việc cần làm", "Việc giao cho tôi", "Việc tôi giao" — mỗi hộp có bộ lọc riêng cùng cấu trúc.

**Trường dữ liệu** (mỗi trường dưới đây tồn tại bốn biến thể theo tên hộp việc, ví dụ `theoNgayLienQuanToi`, `theoNgayViecCanLam`, v.v.)

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `theoNgay` | Lọc theo ngày | |
| `khanCap` | Độ khẩn | Chiều riêng |
| `quanTrong` | Mức độ quan trọng | Chiều riêng, tách khỏi `khanCap` |
| `trangThai` | Trạng thái công việc | |
| `tinhTrang` | Tình trạng | |
| `duAn` | Dự án liên kết | |
| `nhomCV` | Nhóm công việc | |
| `nhanVien` | Nhân viên thực hiện | |
| `tinhTrangHoanThanh` | Tình trạng hoàn thành | |
| `qSearch` | Tìm kiếm | |

**Chỗ đáng chú ý:** `khanCap` và `quanTrong` là hai chiều độc lập — một task có thể quan trọng mà không khẩn, hoặc khẩn mà không quan trọng. Điều này phản ánh ma trận Eisenhower. Sơ đồ Gantt là chế độ xem mà Project-M hiện chưa có.

---

## WS9. Báo cáo công việc theo nhân viên

| | |
|---|---|
| Đường dẫn | `/BaoCaoCongViecTheoNhanVien/Index`, `/BC_CongViec/Index` |
| Dùng để làm gì | Tổng hợp tiến độ công việc theo nhân viên, xem biểu đồ, Export |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Bốn thẻ tại `/BaoCaoCongViecTheoNhanVien/Index`: Báo cáo công việc theo nhân viên, Biểu đồ báo cáo công việc, Export, Cập nhật. Tại `/BC_CongViec/Index`: hai báo cáo — Báo cáo công việc theo nhân viên và Báo cáo nhật ký công việc theo ngày.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `hinhThucBC` | Hình thức báo cáo | |
| `hinhThucChart` | Loại biểu đồ | |
| `qSearchBC` | Tìm kiếm trong báo cáo | |

---

## Phần 2 — Tài sản

## TS1. Danh sách tài sản

| | |
|---|---|
| Đường dẫn | `/DSTaiSan/Index`, tạo mới `/DSTaiSan/Create` |
| Dùng để làm gì | Danh mục toàn bộ tài sản của tổ chức, phân loại theo nhóm, theo thuộc tính động; sinh mã tự động từ thuộc tính |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Ba thẻ: Danh sách tài sản, Thuộc tính, Nhóm tài sản. Có Export, Import, Import Update (cập nhật hàng loạt), In.

Bộ lọc quan sát được: nhóm tài sản, phân loại (CCDC / Tài sản), loại tài sản (Tiêu hao / Không tiêu hao), năm sử dụng, thương hiệu, nhà phân phối, thông số, kích thước, màu sắc, kho, tình trạng tài sản.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `loaiTaiSan` | Loại tài sản | |
| `maNhomTaiSan` | Mã nhóm tài sản | |
| `maTaiSan` | Mã tài sản | Có thể được sinh tự động |
| `tenTaiSan` | Tên tài sản | Có thể được sinh tự động |
| `donViTinh` | Đơn vị tính | |
| `soLuong` | Số lượng | |
| `maKho` | Mã kho | |
| `khongThuHoi` | Cờ tài sản không thu hồi | |
| `ngayMuaMoi` | Ngày mua mới | |
| `maTinhTrang` | Mã tình trạng tài sản | |
| `tuDongTachMa` | Tự động tách mã theo số lượng | Phỏng đoán |
| `hinhAnh` | Hình ảnh tài sản | |
| `namSuDung` | Năm sử dụng / tuổi thọ | |
| `maNSX` | Mã nhà sản xuất | |
| `maNPP` | Mã nhà phân phối | |
| `thongSo` | Thông số kỹ thuật | |
| `kichThuoc` | Kích thước | |
| `mauSac` | Màu sắc | |
| `thongSoKyThuat` | Thông số kỹ thuật chi tiết | Khác với `thongSo` — phỏng đoán là hai mức chi tiết khác nhau |
| `thoiGianBaoHanh` | Thời gian bảo hành | |
| `chuKiBaoHanh` | Chu kỳ bảo hành | Đơn vị thời gian |
| `donGia` | Đơn giá | |
| `soHoaDon` | Số hóa đơn mua | |
| `soThangKhauHao` | Số tháng khấu hao | |
| `maNhaCungCap` | Mã nhà cung cấp | |
| `sanPhamThamChieu` | Sản phẩm tham chiếu | |
| `ghiChu` | Ghi chú | |
| `maNhomThuocTinh` | Mã nhóm thuộc tính động | Thuộc khối thuộc tính |
| `nhomTS` | Nhóm tài sản liên kết thuộc tính | Thuộc khối thuộc tính |
| `maThuocTinh` | Mã thuộc tính | Thuộc khối thuộc tính |
| `maGanNhat` | Mã gần nhất | Thuộc khối thuộc tính — phỏng đoán là mã được gán gần đây |
| `tenThuocTinh` | Tên thuộc tính | Thuộc khối thuộc tính |
| `tuDongDuaVaoMaTS` | Thuộc tính này tự ghép vào mã tài sản | Cờ trong khối thuộc tính |
| `tuDongDuaVaoTenTS` | Thuộc tính này tự ghép vào tên tài sản | Cờ trong khối thuộc tính |

**Chỗ đáng chú ý:** Cơ chế sinh mã từ thuộc tính (`tuDongDuaVaoMaTS`, `tuDongDuaVaoTenTS`) cho phép mã và tên tài sản được cấu thành tự động từ các thuộc tính động (màu sắc, kích thước, thông số...). Đây là thiết kế linh hoạt hơn mã cứng thông thường. `soThangKhauHao` và `donGia` cho thấy module tính toán khấu hao được tích hợp ngay trong danh mục tài sản.

---

## TS2. Phiếu nhập tài sản

| | |
|---|---|
| Đường dẫn | `/NhapTaiSan/Index`, tạo mới `/NhapTaiSan/Create` |
| Dùng để làm gì | Ghi nhận tài sản nhập kho, liên kết với đối tượng nhận và nơi sử dụng |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Form phiếu nhập với bảng dòng chi tiết bên dưới.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maDanhMuc` | Mã danh mục | |
| `loaiDoiTuong` | Loại đối tượng nhận | Nhân viên hoặc phòng ban — phỏng đoán |
| `doiTuong` | Đối tượng nhận cụ thể | Ghép với `loaiDoiTuong` |
| `noiSuDung` | Nơi sử dụng tài sản | |
| `ngayHoachToan` | Ngày hạch toán | |
| `maKho` | Mã kho | |
| `nguoiNhan` | Người nhận | Trường riêng trên phiếu nhập, không có trên phiếu xuất |
| `ghiChu` | Ghi chú | |

Bảng dòng chi tiết: STT, Mã tài sản, Tên tài sản, Thông số Kỹ Thuật, Đơn vị tính, Số lượng, Ghi chú.

---

## TS3. Phiếu xuất tài sản

| | |
|---|---|
| Đường dẫn | `/XuatTaiSan/Index`, tạo mới `/XuatTaiSan/Create` |
| Dùng để làm gì | Ghi nhận tài sản xuất kho cho nhân viên hoặc phòng ban |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Form phiếu xuất với bảng dòng chi tiết bên dưới.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `loaiDoiTuong` | Loại đối tượng nhận | Nhân viên hoặc phòng ban |
| `doiTuong` | Đối tượng nhận cụ thể | Ghép với `loaiDoiTuong` |
| `noiSuDung` | Nơi sử dụng | |
| `ngayHoachToan` | Ngày hạch toán | |
| `maKho` | Mã kho | |
| `maDanhMuc` | Mã danh mục | |
| `ghiChu` | Ghi chú | |

Bảng dòng chi tiết: STT, Mã tài sản, Tên tài sản, Thông số kỹ thuật, Đơn vị tính, Số lượng, Ghi chú.

Phỏng đoán: phiếu xuất không có trường `nguoiNhan` riêng như phiếu nhập. Thay vào đó dùng cặp `loaiDoiTuong` + `doiTuong` để xác định người/đơn vị nhận — cho phép xuất cho cả nhân viên lẫn phòng ban mà không cần hai loại phiếu riêng.

---

## TS4. Biên bản bàn giao tài sản

| | |
|---|---|
| Đường dẫn | `/BienBanBanGiaoTaiSan/Index` |
| Dùng để làm gì | Lập và theo dõi biên bản bàn giao tài sản, chạy qua quy trình duyệt nhiều bước |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình**

Bảng danh sách biên bản với bộ lọc. Không thấy form tạo mới trong dữ liệu thô.

**Trường dữ liệu**

Cột bảng: STT, Số phiếu, Trạng thái, Mã đối tượng bàn giao, Đối tượng bàn giao, Phòng ban, Chức danh, Đối tượng nhận bàn giao, Ngày bàn giao, Nội dung, Thao tác.

| Trường lọc | Nghĩa | Ghi chú |
|---|---|---|
| `idBuocDuyet` | Bước duyệt hiện tại | Biên bản chạy qua bộ máy quy trình duyệt |
| `qSearch` | Tìm kiếm | |

**Chỗ đáng chú ý:** Biên bản bàn giao tài sản nằm trong danh sách 88 loại công việc của bộ máy quy trình duyệt — có nghĩa là bàn giao tài sản không phải thao tác đơn giản mà phải qua phê duyệt. Hồ sơ nhân viên có thẻ "Tài sản" hiển thị toàn bộ lịch sử cấp phát tài sản cho người đó.

Các loại công việc liên quan đến tài sản trong bộ máy quy trình duyệt (danh sách 88): Phiếu Nhập Tài Sản, Phiếu Xuất Tài Sản, Bàn giao tài sản, Tài Sản Bị Mất, Phiếu báo Tình trạng tài sản, Cấp phát Tài sản tiêu hao, Kiểm kê tài sản, Biên bản kiểm kê.

Các loại công việc Workspace trong bộ máy quy trình duyệt: Duyệt Công văn, Quản lý công việc, Báo cáo tuần, Quản lý Hồ sơ.

Báo cáo tài sản có tại `/BC_TaiSan/Index`: Đang sử dụng, Đang tồn kho, Lịch sử nhập xuất tài sản, Báo cáo nhập xuất tồn, BC Khấu Hao Tài Sản, BC Kiểm kê tài sản.

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| LichHop | id, subject, timeBegin, timeFinish, loaiLichBieu, phongHop, nhacTruoc, loaiNhacTruoc, ngayDong, body | Khá |
| LichHop_NhanVien | idLichHop, idNhanVien, idChucVu, idPhongBan | Đoán |
| TaiLieu_ThuMuc | id, nameFolder, noiDungFolder, hasTagFolder | Chắc |
| TaiLieu_File | id, idThuMuc, noiDungFile, hasTagFile, FileUpload, hinhAnh | Chắc |
| TaiLieu_Link | id, idThuMuc, name_link_upload, link_upload, noiDungLink, hasTagLink | Chắc |
| TaiLieu_PhanQuyen | idThuMuc, loaiDoiTuong, idDoiTuong, permissionWatch, permissionUpload, permissionTaiVe, permissionDelete, permissionEdit, permissionAdmin, ngayXemTu, ngayXemDen, khungGioTu, khungGioDen | Khá |
| CongVan | id, loaiCongVan, loaiToTrinh, doKhan, baoMat, trangThai, loaiNgay | Khá |
| DanhSachTaiSan | id, maNhomTaiSan, maTaiSan, tenTaiSan, donViTinh, soLuong, maKho, khongThuHoi, ngayMuaMoi, maTinhTrang, namSuDung, maNSX, maNPP, thongSo, kichThuoc, mauSac, thongSoKyThuat, thoiGianBaoHanh, chuKiBaoHanh, donGia, soHoaDon, soThangKhauHao, maNhaCungCap, sanPhamThamChieu, ghiChu | Chắc |
| TaiSan_ThuocTinh | id, maTaiSan, maNhomThuocTinh, maThuocTinh, tenThuocTinh, tuDongDuaVaoMaTS, tuDongDuaVaoTenTS | Khá |
| PhieuNhapTaiSan | id, maDanhMuc, loaiDoiTuong, doiTuong, noiSuDung, ngayHoachToan, maKho, nguoiNhan, ghiChu | Chắc |
| PhieuNhapTaiSan_ChiTiet | id, idPhieuNhap, maTaiSan, tenTaiSan, thongSoKyThuat, donViTinh, soLuong, ghiChu | Chắc |
| PhieuXuatTaiSan | id, maDanhMuc, loaiDoiTuong, doiTuong, noiSuDung, ngayHoachToan, maKho, ghiChu | Chắc |
| PhieuXuatTaiSan_ChiTiet | id, idPhieuXuat, maTaiSan, tenTaiSan, thongSoKyThuat, donViTinh, soLuong, ghiChu | Chắc |
| BienBanBanGiao | id, soPhieu, trangThai, maDoiTuongBanGiao, doiTuongBanGiao, phongBan, chucDanh, doiTuongNhanBanGiao, ngayBanGiao, noiDung, idBuocDuyet | Khá |

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| WS1 Truyền thông nội bộ | Không lấy | Chuông + web push đủ cho quy mô hiện tại; mạng xã hội nội bộ thêm gánh nặng vận hành không tương xứng | — |
| WS2 Lịch biểu | Lấy sau | Hữu ích khi đủ người dùng, nhưng không phải ưu tiên hiện tại | Bỏ `tbQuaEmail` nếu VPS đang tắt email; kiểm tra `phongHop` có cần quản lý phòng họp riêng không |
| WS3 Chat | Không lấy | Chat thường dùng công cụ bên ngoài (Zalo, Teams); tự xây chat tốn nguồn lực không thu lại giá trị | — |
| WS4 Tài liệu | Lấy sau | Trung tâm HDSD hiện có nhưng không có phân quyền theo thư mục hoặc giới hạn khung giờ | Đánh giá kỹ `permissionTaiVe` tách khỏi `permissionWatch`; cân nhắc giữ hay bỏ giới hạn khung giờ |
| WS5 Công văn | Không lấy | Nghiệp vụ công văn thuộc khối hành chính, ngoài phạm vi phần mềm Thu mua | — |
| WS6 Ký số | Không lấy | Đòi hỏi hạ tầng USB token; chi phí tích hợp cao so với lợi ích với quy mô hiện tại | — |
| WS7 Dự án | Không lấy | Project-M đang phục vụ nhu cầu này | — |
| WS8 Quản lý công việc | Lấy sau | Sơ đồ Gantt và bốn hộp việc theo vai trò là điểm khác biệt so với Project-M; xem xét bổ sung vào Project-M thay vì lấy nguyên bản | Cần đánh giá xem Project-M có thể mở rộng thêm Gantt không trước khi quyết định |
| WS9 Báo cáo công việc | Lấy sau | Phụ thuộc vào WS8; chỉ có giá trị nếu WS8 được triển khai | — |
| TS1 Danh sách tài sản | Lấy | Không có module tài sản; liên kết với hồ sơ nhân viên là nhu cầu thực | Cân nhắc bỏ `soThangKhauHao` nếu không cần tính khấu hao; giữ cơ chế sinh mã từ thuộc tính |
| TS2 Phiếu nhập tài sản | Lấy | Cần thiết để nhập tài sản vào hệ thống | Giữ nguyên |
| TS3 Phiếu xuất tài sản | Lấy | Cần để ghi nhận cấp phát tài sản cho nhân viên | Kiểm tra lại logic `loaiDoiTuong` + `doiTuong` xem có tương thích cấu trúc nhân sự hiện tại không |
| TS4 Biên bản bàn giao | Lấy | Cắm vào bộ máy duyệt được ngay **khi nào bộ máy duyệt dùng chung đã có** — hiện Thu mua vẫn duyệt cứng trong mã nguồn | Kiểm tra `idBuocDuyet` tương thích với bộ máy duyệt sẽ làm |

**Về cột "Nên lấy" của bốn dòng tài sản:** xét riêng trong mục này thì bốn chức năng tài sản là nhóm đáng lấy nhất, vì đây là mảng duy nhất trong cả mục mà hệ thống hiện tại chưa có gì và nhu cầu là thật. Nhưng **thứ tự trên toàn cảnh do [`10` Đề xuất áp dụng](./10-de-xuat-ap-dung.md) quyết định** — ở đó tài sản xếp sau hồ sơ nhân viên và sau bộ máy duyệt, vì nó phụ thuộc cả hai.
