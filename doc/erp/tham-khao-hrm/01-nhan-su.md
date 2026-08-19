# NHÂN SỰ VÀ HỒ SƠ

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 5 chức năng chính, 10 báo cáo liên quan |

## Tóm tắt mục này

Mục này gồm 5 chức năng chính: Hồ sơ nhân viên (NS1), Sơ đồ tổ chức (NS2), Hợp đồng lao động (NS3), Bảo hiểm xã hội (NS4), và Lộ trình sự nghiệp (NS5). NS1 là lõi — toàn bộ các chức năng còn lại trong hệ thống đều tham chiếu đến mã nhân viên từ NS1. Trường `nguoiQuanLy` trong NS1 có vai trò đặc biệt: đây là dữ liệu nguồn mà bộ máy phê duyệt đơn từ dùng để xác định luồng ký, nhập sai trường này khiến toàn bộ đơn từ của nhân viên đi sai đường. NS3 phụ thuộc NS1 (hợp đồng gắn với nhân viên cụ thể); NS4 phụ thuộc cả NS1 lẫn NS3 (mức đóng bảo hiểm lấy từ lương trong hợp đồng). NS5 ít phụ thuộc hơn, chỉ cần tham chiếu phòng ban từ NS1. Hồ sơ nhân viên (NS1) có khoảng 90 trường chia 7 nhóm, trong đó nhóm trường tùy biến cho phép công ty tự thêm trường mà không sửa code. Khối phân quyền chấm công đặt ngay bên trong màn hình hồ sơ nhân viên, không tách thành màn hình quản trị riêng. Hệ thống Thu mua hiện tại chỉ lưu mã, tên, phòng ban, email nhân viên, nên phần lớn mục này chưa có.

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| NS1 | Hồ sơ nhân viên | `/HoSoNhanVien/` | Lưu toàn bộ thông tin cá nhân, công việc, giấy tờ, ngân hàng, và phân quyền chấm công của từng nhân viên | `[~]` |
| NS2 | Sơ đồ tổ chức | `/SoDoToChuc/Index` | Xem cấu trúc phòng ban và nhân sự | `[ ]` |
| NS3 | Hợp đồng lao động | `/HopDongLaoDong/` | Quản lý hợp đồng lao động theo nhân viên, hỗ trợ ký số nhiều hợp đồng cùng lúc | `[ ]` |
| NS4 | Bảo hiểm xã hội | `/BaoHiem/Index` | Quản lý tăng giảm BHXH, quá trình đóng, lịch sử giải quyết chế độ | `[ ]` |
| NS5 | Lộ trình sự nghiệp | `/LoTrinhSuNghiep/Index` | Xây dựng lộ trình phát triển nghề nghiệp gắn với phòng ban | `[ ]` |

---

## NS1. Hồ sơ nhân viên

| | |
|---|---|
| Đường dẫn | `/HoSoNhanVien/`, chi tiết `/HoSoNhanVien/Detail?maPhieu=<mã NV>` |
| Dùng để làm gì | Lưu toàn bộ thông tin cá nhân, công việc, giấy tờ, ngân hàng, và phân quyền chấm công của từng nhân viên |
| Ai dùng | phỏng đoán: HR nhập và cập nhật; nhân viên xem hồ sơ cá nhân; quản lý xem hồ sơ cấp dưới |
| Mình có chưa | `[~]` — Thu mua có bảng nhân sự nhưng chỉ lưu mã, tên, phòng ban, email |

**Cấu trúc màn hình** — hai màn hình chính: danh sách (26 cột, hộp tạo nhanh 12 trường) và chi tiết (8 thẻ).

---

**Trường dữ liệu — màn hình danh sách (26 cột)**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| TẠO USER | Thao tác tạo tài khoản đăng nhập | phỏng đoán: tạo tài khoản hệ thống từ hồ sơ nhân viên |
| Chữ ký | Ảnh chữ ký | |
| ẢNH | Ảnh đại diện | |
| `maNhanVien` | Mã nhân viên | |
| `tenNhanVien` | Tên nhân viên | |
| Tên gọi khác | Tên thường gọi | |
| `tenDangNhap` | Tên đăng nhập | |
| `trangThai` | Trạng thái | Đang làm việc / Đã nghỉ việc / Đã xin nghỉ / Nghỉ thai sản |
| `ngaySinh` | Ngày sinh | |
| Độ tuổi | | phỏng đoán: tính tự động từ `ngaySinh` |
| `ngayVaoLam` | Ngày vào làm | |
| `ngayThoiViec` | Ngày thôi việc | |
| `tenChucDanh` | Tên chức danh | |
| `donVi` | Đơn vị | |
| `tenPhongBan` | Tên phòng ban | |
| `nguoiQuanLy` | Người quản lý trực tiếp | Dùng để bộ máy duyệt đơn xác định luồng ký; sai trường này thì đơn từ chạy sai đường |
| `soDienThoai` | Số điện thoại | |
| `email` | Email công việc | |
| `phapNhan` | Pháp nhân | Danh sách 17 mục |
| `maChamCong` | Mã chấm công | |
| `hinhThucNhanVien` | Hình thức nhân viên | CTV / Thời vụ / Part time / Full time |
| `quocTich` | Quốc tịch | |
| `capBac` | Cấp bậc / Chức vụ | |
| `tinhTrangTiemVacXin` | Tình trạng tiêm vắc xin Covid | phỏng đoán: trường tồn tại từ giai đoạn Covid, có thể đã lỗi thời |
| THAO TÁC | Các nút hành động trên dòng | |

---

**Trường dữ liệu — hộp tạo nhanh (12 trường)**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maNhanVien` | Mã nhân viên | |
| `hoNhanVien` | Họ và tên đệm | |
| `tenNhanVien` | Tên | |
| `tenDonVi` | Tên đơn vị | |
| `maChucDanh` | Mã chức danh | |
| `ngaySinhCreate` | Ngày sinh | Hậu tố `Create` phân biệt với trường cùng tên trên danh sách |
| `ngayVaoLam` | Ngày vào làm | |
| `soDienThoai` | Số điện thoại | |
| `email` | Email | |
| `maChamCong` | Mã chấm công | |
| `gioiTinh` | Giới tính | |
| `trangThai` | Trạng thái | |

---

**Trường dữ liệu — hồ sơ đầy đủ (~90 trường, 7 nhóm)**

Nhóm 1 — Thông tin cá nhân:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Họ tên đệm / Tên | | |
| Ngày sinh | | |
| Tên thường gọi | | |
| Nơi sinh | | |
| Quốc tịch | | |
| Dân tộc | | |
| Tôn giáo | | |
| Trình độ học vấn | | |
| Trình độ chuyên môn | | |
| Chuyên ngành | | |
| Tình trạng hôn nhân | | |
| `maSoThue` | Mã số thuế cá nhân | |
| Số sổ BHXH | | |
| Ngày bắt đầu đóng BHXH | | |
| Hình thức chi lương | | |
| Ghi chú | | |

Nhóm 2 — Thông tin công việc:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Cấp bậc | | |
| Hình thức làm việc | | |
| Nơi làm việc | | |
| Đơn vị | | |
| Mã phân ca | | |
| `maChamCong` | Mã chấm công | |
| Điện thoại cơ quan | | |
| Người giới thiệu | | |
| Đơn vị kiêm nhiệm | | |
| Phòng ban kiêm nhiệm | | |
| Chức danh kiêm nhiệm | | |
| Mô tả công việc | | |
| Ngày bắt đầu tính thâm niên | | |
| Thời gian làm việc tại công ty | | phỏng đoán: tính tự động |
| Loại HĐLĐ | Loại hợp đồng lao động | |
| Ngày chấm dứt HĐLĐ | | |

Nhóm 3 — Thông tin liên hệ:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Địa chỉ thường trú | tỉnh / phường / địa chỉ | 3 trường |
| Địa chỉ tạm trú | tỉnh / phường / địa chỉ | 3 trường lặp cùng cấu trúc |
| Nguyên quán | tỉnh / phường / địa chỉ | 3 trường lặp cùng cấu trúc |
| Skype | | |
| Facebook | | |
| Email cá nhân | | Khác với email công việc |

Nhóm 4 — Thông tin ngân hàng:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Số tài khoản | | |
| Tên tài khoản | | |
| Ngân hàng | | |
| Chi nhánh | | |

Nhóm 5 — Giấy tờ:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Số CMND/CCCD | | |
| Ngày cấp CMND/CCCD | | |
| Ngày hết hạn CMND/CCCD | | |
| Nơi cấp CMND/CCCD | | |
| Ảnh mặt trước CMND/CCCD | | |
| Ảnh mặt sau CMND/CCCD | | |
| Loại hộ chiếu | | |
| Số hộ chiếu | | |
| Ngày cấp hộ chiếu | | |
| Ngày hết hạn hộ chiếu | | |
| Nơi cấp hộ chiếu | | |

Nhóm 6 — Thông tin khác:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Ngày kết nạp Đảng | | |
| Ngày tham gia công đoàn | | |
| Ngày vào Đoàn | | |
| Cư trú | | |
| Nghĩa vụ quân sự | | |
| Thương binh | | |
| Gia đình liệt sĩ | | |
| Cựu chiến binh | | |
| Quân nhân dự bị | | |

Nhóm 7 — Trường tùy biến:

| Trường quan sát | Suy luận từ tên | Ghi chú |
|---|---|---|
| `vanbanngan17_5_0` | Kiểu văn bản ngắn, màn hình 17 (hồ sơ nhân viên), vị trí 5-0 | Tên sinh tự động theo mẫu `<kiểu><mã màn hình>_<số>_<số>` |
| `danhsachtuychonmotluachon17_11_0` | Kiểu danh sách một lựa chọn, màn hình 17, vị trí 11-0 | |
| `songuyen16_16_0` | Trường trên màn hình hợp đồng lao động (màn hình 16), vị trí 16-0 | Quan sát thấy trên NS3 |
| `sizeao_3_0` | Do người dùng tự đặt tên (không sinh tự động) | Tên không theo mẫu `<kiểu><màn hình>` — người dùng nhập tên thủ công |

---

**Trường dữ liệu — khối phân quyền chấm công (đặt ngay trong hồ sơ nhân viên)**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `chamCongGPS` | Cho phép chấm công qua GPS | |
| `chamCongWifi` | Cho phép chấm công qua Wifi | |
| `chamCongMay` | Cho phép chấm công qua máy | |
| `chamCongHo` | Cho phép chấm hộ | |
| `chamCongDuocNhieuLan` | Cho phép chấm nhiều lần | |
| `quetKhongTheoKhungGioQuyDinh` | Cho phép quét ngoài khung giờ quy định | |
| `quetLinhHoatTheoViTriLamViec` | Quét linh hoạt theo vị trí làm việc | |
| `canhBaoVuotBK` | Cảnh báo vượt bán kính | |
| `faceID` | Cho phép nhận diện khuôn mặt | |
| `chamCongQuaAPP` | Cho phép chấm công qua app | |
| `checkThietBiChamCong` | Kiểm tra thiết bị chấm công | |

Ngoài các cờ trên, trong hồ sơ còn có mục Phân quyền dữ liệu và mục Phân quyền người dùng — nội dung chi tiết hai mục này chưa quan sát được.

---

**Tám thẻ trên màn hình chi tiết:**

| Thẻ | Nội dung quan sát |
|---|---|
| 1. Thông tin chính | Bảy nhóm trường hồ sơ đầy đủ |
| 2. Hồ sơ | Quyết định khác, Quá trình học tập, Chứng chỉ, Lịch sử đảng viên, Quan hệ gia đình, Kinh nghiệm làm việc, Hồ sơ sức khỏe |
| 3. Năng lực | Khung năng lực, Lộ trình công danh, Đánh giá, Nhân sự kế cận |
| 4. Phúc lợi | Diễn biến lương, Tiền lương, Bảo hiểm |
| 5. Quyết định | Điều chuyển & bổ nhiệm, Khen thưởng & kỷ luật, Thành tích & vi phạm, Thôi việc, Đi làm lại |
| 6. Đào tạo | (nội dung chi tiết chưa quan sát) |
| 7. Tài sản | Lịch sử cấp phát |
| 8. Nghỉ phép | Thống kê quỹ phép theo từng loại: Tổng có / Đã dùng / Còn lại |

---

**Bộ lọc trên danh sách:** chưa quan sát được từ nguồn khảo sát.

**Chỗ đáng chú ý:**
- Trường `nguoiQuanLy` là điểm giao giữa dữ liệu nhân sự và bộ máy duyệt đơn — đây không phải trường thông tin thuần túy mà là trường có tác dụng nghiệp vụ trực tiếp: bộ máy quy trình đọc trường này để tính ra ai là "người quản lý trực tiếp" khi định tuyến đơn từ.
- Khối phân quyền chấm công đặt trong hồ sơ nhân viên thay vì ở màn hình quản trị riêng — thiết kế này cho phép cá nhân hóa theo từng người nhưng khó điều chỉnh hàng loạt.
- Trường tùy biến có hai kiểu đặt tên: sinh tự động theo mẫu `<kiểu><màn hình>_<số>_<số>` và tên do người dùng nhập thủ công (ví dụ: `sizeao_3_0`); hai kiểu này cùng tồn tại.

---

## NS2. Sơ đồ tổ chức

| | |
|---|---|
| Đường dẫn | `/SoDoToChuc/Index` |
| Dùng để làm gì | Xem cấu trúc tổ chức phòng ban và nhân sự |
| Ai dùng | phỏng đoán: Ban lãnh đạo và HR |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — màn hình dạng bảng có bộ lọc.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `loaiSoDo` | Loại sơ đồ | Bộ lọc |
| `loaiPhongBan` | Loại phòng ban | Bộ lọc |
| Họ tên | | Cột bảng |
| Chức danh | | Cột bảng |
| Phòng ban | | Cột bảng |
| Tổng điểm | | Cột bảng |
| Xếp loại | | Cột bảng |
| Mức độ phù hợp (%) | | Cột bảng |
| Tên khóa học | | Cột bảng |
| Chủ đề | | Cột bảng |
| Tác giả | | Cột bảng |
| Hình thức | | Cột bảng |
| Kỹ năng | | Cột bảng |

**Bộ lọc trên danh sách:** `loaiSoDo`, `loaiPhongBan`.

**Chỗ đáng chú ý:**
- Các cột quan sát được (Tổng điểm, Xếp loại, Mức độ phù hợp (%), Tên khóa học, Chủ đề, Tác giả, Hình thức, Kỹ năng) không điển hình cho một màn hình sơ đồ tổ chức. Có thể đây là chế độ xem kết hợp năng lực hoặc đào tạo, hoặc dữ liệu ghi chép nhầm màn hình — cần xác nhận lại khi phỏng vấn phòng Nhân sự.

---

## NS3. Hợp đồng lao động

| | |
|---|---|
| Đường dẫn | `/HopDongLaoDong/`, tạo mới `/HopDongLaoDong/Create` |
| Dùng để làm gì | Quản lý hợp đồng lao động theo nhân viên; hỗ trợ ký số nhiều hợp đồng cùng lúc |
| Ai dùng | phỏng đoán: HR tạo và theo dõi; nhân viên ký số |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — 4 thẻ trên màn hình danh sách: Hợp đồng đang hiệu lực, Chưa lên hợp đồng, Hợp đồng hết hạn, Đơn giá lương theo giờ.

**Trường dữ liệu — form tạo mới**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maHopDong` | Mã hợp đồng | |
| `soPhuLuc` | Số phụ lục | |
| `maPhapNhan` | Mã pháp nhân | |
| `luongNet` | Lương net | |
| `lyDo` | Lý do ký hợp đồng | |
| `maLoaiHopDong` | Mã loại hợp đồng | |
| `hopDongThuViec` | Hợp đồng thử việc | phỏng đoán: cờ boolean |
| `maLoaiThue` | Mã loại thuế thu nhập cá nhân | |
| `ngayKy` | Ngày ký | |
| `ngayBatDau` | Ngày bắt đầu | |
| `ngayKetThuc` | Ngày kết thúc | |
| `ngayBatDauTinhPhep` | Ngày bắt đầu tính phép | |
| `maThangTinhLuong` | Mã tháng tính lương | phỏng đoán: kỳ lương bắt đầu |
| `heSoLuong` | Hệ số lương | |
| `luongThoaThuan` | Lương thỏa thuận | Mức 1 trong 3 mức lương tách riêng |
| `tyLeLuong` | Tỷ lệ lương | |
| `tongLuong` | Tổng lương | |
| `luongCoBan` | Lương cơ bản | Mức 2 trong 3 mức lương tách riêng |
| `khoanBoSungLuong` | Khoản bổ sung lương | |
| `luongDongBaoHiem` | Lương đóng bảo hiểm | Mức 3 trong 3 mức lương tách riêng |
| `quiNoiBo` | Quỹ nội bộ | |
| `doanPhi` | Đoàn phí | |
| `dangPhi` | Đảng phí | |
| `lsMauIns` | phỏng đoán: danh sách mẫu in hợp đồng | tên trường chưa rõ nghĩa đầy đủ |
| `ghiChu` | Ghi chú | |
| `songuyen16_16_0` | Trường tùy biến trên màn hình hợp đồng (màn hình 16) | |
| `FileUpload` | Tệp đính kèm | |

**Trường dữ liệu — bảng con phụ cấp**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhuCap` | Mã phụ cấp | |
| `soTien` | Số tiền phụ cấp | |
| `ghiChuPhuCap` | Ghi chú phụ cấp | |

**Bộ lọc trên danh sách:** chưa quan sát được từ nguồn khảo sát.

**Chỗ đáng chú ý:**
- Ba mức lương tách thành ba trường riêng biệt: `luongThoaThuan`, `luongCoBan`, `luongDongBaoHiem`. Trong thực tế Việt Nam, ba con số này thường khác nhau và không tính ra được từ nhau — thiết kế tách riêng là đúng.
- Chức năng ký số cho phép ký nhiều hợp đồng cùng lúc — cơ chế kỹ thuật cụ thể chưa quan sát được.

---

## NS4. Bảo hiểm xã hội

| | |
|---|---|
| Đường dẫn | `/BaoHiem/Index` |
| Dùng để làm gì | Quản lý tăng giảm BHXH, theo dõi quá trình đóng, lịch sử giải quyết chế độ; hỗ trợ import/export dữ liệu bảo hiểm |
| Ai dùng | phỏng đoán: HR chuyên trách bảo hiểm |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — nhiều thẻ và thao tác chức năng.

Các thẻ và thao tác quan sát được: Danh sách bảo hiểm, Báo tăng, Báo giảm, Quá trình đóng, Lịch sử giải quyết chế độ, Export, Import bảo hiểm, Update bảo hiểm, Cấu hình bảo hiểm, Import lịch sử thay đổi BH, Export lịch sử thay đổi BH.

**Trường dữ liệu — bộ lọc quan sát được theo từng thẻ**

| Trường | Nghĩa | Thuộc thẻ |
|---|---|---|
| `loaiNgay-baohiem` | Loại ngày lọc | Danh sách bảo hiểm |
| `maPhapNhan-baohiem` | Mã pháp nhân | Danh sách bảo hiểm |
| `trangThaiBaoHiem-baohiem` | Trạng thái bảo hiểm | Danh sách bảo hiểm |
| `trangThaiNhanVien-baohiem` | Trạng thái nhân viên | Danh sách bảo hiểm |
| `maLoaiBaoHiem-baohiem` | Mã loại bảo hiểm | Danh sách bảo hiểm |
| `trangThaiKhaiBao` | Trạng thái khai báo | Danh sách bảo hiểm |
| `hienThi` | Hiển thị | phỏng đoán: bộ lọc ẩn/hiện |
| `ngayBatDauCapNhat` | Ngày bắt đầu cập nhật | Danh sách bảo hiểm |
| `ngayKetThucCapNhat` | Ngày kết thúc cập nhật | Danh sách bảo hiểm |
| `trangThaiKhaiBaoBH` | Trạng thái khai báo BH | Danh sách bảo hiểm |
| `maPhapNhan-baotang` | Mã pháp nhân | Báo tăng |
| `noiDungBaoTang` | Nội dung báo tăng | Báo tăng |
| `maTrangThaiBaoTang` | Mã trạng thái báo tăng | Báo tăng |
| `trangThaiKhaiBaoBT` | Trạng thái khai báo báo tăng | Báo tăng |
| `ngayCapNhat` | Ngày cập nhật | Báo tăng |
| `mucDongBaoTang` | Mức đóng báo tăng | Báo tăng |
| `ghiChuBaoTang` | Ghi chú báo tăng | Báo tăng |
| `loai-baogiam` | Loại báo giảm | Báo giảm |
| `thang-quatrinhdong` | Tháng | Quá trình đóng |
| `nam-quatrinhdong` | Năm | Quá trình đóng |
| `maPhapNhan-quatrinhdong` | Mã pháp nhân | Quá trình đóng |

**Bộ lọc trên danh sách:** xem bảng trên.

**Chỗ đáng chú ý:**
- Báo tăng và Báo giảm là hai chứng từ riêng biệt, không phải hai trạng thái của cùng một bản ghi bảo hiểm.

---

## NS5. Lộ trình sự nghiệp

| | |
|---|---|
| Đường dẫn | `/LoTrinhSuNghiep/Index` |
| Dùng để làm gì | Xây dựng và theo dõi lộ trình phát triển nghề nghiệp gắn với phòng ban |
| Ai dùng | phỏng đoán: HR và quản lý trực tiếp |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — bảng danh sách.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Tên lộ trình | | Cột bảng |
| Phòng ban áp dụng | | Cột bảng |
| Mục tiêu | | Cột bảng |
| Người lập | | Cột bảng |
| Ngày lập | | Cột bảng |
| `pageSize` | Kích thước trang | Bộ lọc phân trang |
| `qSearch` | Từ khóa tìm kiếm | Bộ lọc |

**Bộ lọc trên danh sách:** `pageSize`, `qSearch`.

---

## Báo cáo liên quan

Đường dẫn chung: `/BC_NhanSu/Index`

| # | Tên báo cáo |
|---|---|
| 1 | BC Hồ sơ nhân viên |
| 2 | BC Bằng cấp nhân viên |
| 3 | BC Kinh nghiệm nhân viên |
| 4 | Báo cáo thôi việc |
| 5 | Sinh nhật nhân viên |
| 6 | BC Tình trạng sức khỏe nhân viên |
| 7 | BC Tình hình sử dụng lao động |
| 8 | Báo cáo giấy phép lao động sắp hết hạn |
| 9 | BC giới thiệu nhân viên |
| 10 | Hợp đồng sắp hết hạn |

---

## Danh mục dùng chung quan sát được

| Danh mục | Giá trị quan sát |
|---|---|
| Cấp bậc chức vụ | Quản lý, Chuyên viên, Giám đốc, Nhân viên, Phó Giám Đốc, Trưởng phòng, Cộng tác viên, Trợ lý TGĐ, Trưởng nhóm, Thực tập sinh, Tổng Giám đốc |
| Hình thức nhân viên | CTV, Thời vụ, Part time, Full time |
| Trạng thái nhân viên | Đang làm việc, Đã nghỉ việc, Đã xin nghỉ, Nghỉ thai sản |
| Pháp nhân | 17 mục (tên cụ thể chưa ghi lại được) |

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `nhan_vien` | `ma_nhan_vien`, `ho_nhan_vien`, `ten_nhan_vien`, `ma_phong_ban` (FK), `ma_chuc_danh` (FK), `ngay_sinh`, `ngay_vao_lam`, `ngay_thoi_viec`, `trang_thai`, `ma_cham_cong`, `ma_phap_nhan` (FK), `nguoi_quan_ly` (FK tự tham chiếu), `gioi_tinh`, `quoc_tich`, `hinh_thuc_nhan_vien`, `ten_dang_nhap` | Chắc |
| `nhan_vien_lien_he` | `ma_nhan_vien` (FK), địa chỉ thường trú/tạm trú/nguyên quán (mỗi loại 3 trường: tỉnh, phường, địa chỉ), `email_ca_nhan`, `skype`, `facebook` | Khá |
| `nhan_vien_ngan_hang` | `ma_nhan_vien` (FK), `so_tai_khoan`, `ten_tai_khoan`, `ngan_hang`, `chi_nhanh` | Khá |
| `nhan_vien_giay_to` | `ma_nhan_vien` (FK), số/ngày cấp/ngày hết hạn/nơi cấp CMND/CCCD, ảnh 2 mặt, thông tin hộ chiếu tương tự | Khá |
| `nhan_vien_cham_cong` | `ma_nhan_vien` (FK), `chamCongGPS`, `chamCongWifi`, `chamCongMay`, `chamCongHo`, `chamCongDuocNhieuLan`, `quetKhongTheoKhungGioQuyDinh`, `quetLinhHoatTheoViTriLamViec`, `canhBaoVuotBK`, `faceID`, `chamCongQuaAPP`, `checkThietBiChamCong` | Khá |
| `truong_tuy_bien` hoặc cột JSON | tên trường sinh tự động theo `<kiểu><màn hình>_<số>_<số>` hoặc tên người dùng đặt thủ công, giá trị tương ứng | Đoán |
| `phong_ban` | `ma_phong_ban`, `ten_phong_ban`, `ma_phong_ban_cha` (FK tự tham chiếu) | Chắc |
| `chuc_danh` | `ma_chuc_danh`, `ten_chuc_danh`, `cap_bac` | Chắc |
| `phap_nhan` | `ma_phap_nhan`, `ten_phap_nhan` | Chắc |
| `hop_dong` | `ma_hop_dong`, `ma_nhan_vien` (FK), `ma_phap_nhan` (FK), `ma_loai_hop_dong`, `ngay_ky`, `ngay_bat_dau`, `ngay_ket_thuc`, `luong_thoaThuan`, `luong_co_ban`, `luong_dong_bao_hiem`, `luong_net`, `he_so_luong`, `tong_luong` | Chắc |
| `hop_dong_phu_cap` | `ma_hop_dong` (FK), `ma_phu_cap`, `so_tien`, `ghi_chu` | Chắc |
| `bao_hiem` | `ma_nhan_vien` (FK), `ma_loai_bao_hiem`, `ma_phap_nhan` (FK), `trang_thai`, `trang_thai_khai_bao` | Khá |
| `bao_tang` | Chứng từ riêng: `ma_nhan_vien` (FK), `noi_dung`, `trang_thai`, `muc_dong`, `ngay_cap_nhat`, `ghi_chu` | Khá |
| `bao_giam` | Chứng từ riêng (không phải trạng thái của `bao_tang`): `ma_nhan_vien` (FK), `loai` | Khá |
| `lo_trinh_su_nghiep` | `ten_lo_trinh`, `ma_phong_ban` (FK), `muc_tieu`, `nguoi_lap`, `ngay_lap` | Khá |

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| NS1 — Hồ sơ nhân viên (phần cơ bản) | Lấy sau | Thu mua hiện chỉ lưu 4 trường nhân sự; khi mở rộng cần ít nhất nhóm 1-2 và trường `nguoiQuanLy` để bộ máy duyệt hoạt động đúng | Không cần 90 trường ngay — bắt đầu với ~30 trường thiết yếu. Bỏ nhóm 6 (thông tin Đảng/quân sự) nếu không cần. Tách khối phân quyền chấm công thành màn hình quản trị riêng hoặc bỏ hẳn |
| NS1 — Trường tùy biến | Lấy sau | Cho phép từng công ty tự mở rộng schema mà không sửa code | Cần quyết định kiểu lưu trữ (cột JSON hay bảng EAV) phù hợp với MySQL hiện tại |
| NS1 — Khối phân quyền chấm công | Không lấy | Thu mua không có module chấm công | — |
| NS2 — Sơ đồ tổ chức | Lấy sau | Cấu trúc phòng ban đã có một phần trong Thu mua; sơ đồ trực quan hữu ích khi hệ thống mở rộng | Cần xác nhận lại nội dung màn hình (cột bảng quan sát không khớp kỳ vọng của một sơ đồ tổ chức thông thường) trước khi thiết kế |
| NS3 — Hợp đồng lao động | Lấy sau | Thông tin lương trong hợp đồng có thể cần khi tính chi phí nhân sự cho dự án hoặc đơn hàng | Giữ nguyên thiết kế 3 mức lương tách riêng — đúng thực tế Việt Nam. Có thể bỏ tính năng ký số nếu chưa cần |
| NS4 — Bảo hiểm xã hội | Không lấy | Nghiệp vụ chuyên biệt, ngoài phạm vi thu mua; cần tích hợp cổng BHXH điện tử riêng | — |
| NS5 — Lộ trình sự nghiệp | Không lấy | Ngoài phạm vi thu mua | — |
