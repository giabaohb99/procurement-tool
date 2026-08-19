# QUYẾT ĐỊNH NHÂN SỰ

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 6 |

---

## Tóm tắt mục này

Quyết định nhân sự là những thay đổi trên hồ sơ một người mà **không được phép sửa trực tiếp vào hồ sơ**: điều chuyển, bổ nhiệm, tăng lương, kỷ luật, thôi việc, đi làm lại. Phải có phiếu, có số quyết định, có ngày hiệu lực, có bản ký lưu lại.

Đây là chỗ mà một hệ thống nhân sự khác hẳn một danh bạ nhân viên. Danh bạ chỉ cần biết hôm nay ai ở phòng nào. Hệ thống nhân sự phải trả lời được **tháng 3 năm ngoái người này thuộc phòng nào, theo quyết định số mấy** — vì câu hỏi đó xuất hiện lúc tính lương truy lĩnh, lúc thanh tra lao động, và lúc có tranh chấp.

Họ làm sáu màn hình cho sáu loại quyết định. Nhìn tập trường thì thấy rõ **cả sáu dùng chung một khuôn**: số tờ trình và ngày tờ trình, số quyết định và ngày quyết định, ngày áp dụng và ngày kết thúc, nội dung, tệp PDF bản ký, trạng thái. Phần khác nhau chỉ là bảng chi tiết bên dưới.

Bốn trong sáu màn hình có **bảng danh sách nhân viên bên dưới** — tức một quyết định áp cho nhiều người cùng lúc. Đợt tăng lương không phải làm 40 phiếu.

**Kết luận sớm cho mục này:** khuôn quyết định lặp lại đủ đều để làm thành một khuôn dùng chung, và cặp "tờ trình → quyết định" là chi tiết đáng lấy nguyên vẹn. Nhưng cả mục này chỉ có nghĩa sau khi hồ sơ nhân viên và hợp đồng đã chạy thật — quyết định là thứ tác động lên chúng.

---

## Danh sách chức năng

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| QĐ1 | Quyết định điều chuyển và bổ nhiệm | `/DieuChuyen/Index` | Chuyển phòng ban, đổi chức danh, bổ nhiệm, kiêm nhiệm | `[ ]` |
| QĐ2 | Quyết định thôi việc | `/ThoiViec/Index` | Nghỉ việc, kèm toàn bộ việc bàn giao | `[ ]` |
| QĐ3 | Quyết định điều chỉnh lương | `/PhieuDieuChinhLuong/Index` | Đợt tăng lương, áp cho nhiều người một phiếu | `[ ]` |
| QĐ4 | Đi làm lại | `/DiLamLai/Index` | Người đã nghỉ quay lại làm việc | `[ ]` |
| QĐ5 | Thành tích và vi phạm | `/GhiNhanThanhTichVaViPham/Index` | Khen thưởng, kỷ luật | `[ ]` |
| QĐ6 | Điều chỉnh hợp đồng | `/PhieuDieuChinhHopDong/Index` | Sửa điều khoản hợp đồng bằng quyết định | `[ ]` |

---

## Khuôn chung của mọi quyết định

Trước khi vào từng màn hình, ghi lại phần dùng chung, vì nó là kết luận quan trọng nhất của mục này.

| Trường | Nghĩa | Xuất hiện ở |
|---|---|---|
| `maPhieu` | Số phiếu trong hệ thống | Mọi màn hình |
| `soToTrinh`, `ngayToTrinh` | Số và ngày tờ trình | QĐ1, QĐ3 |
| `soQuyetDinh`, `ngayQuyetDinh` | Số và ngày quyết định | QĐ1, QĐ2, QĐ3 |
| `ngayApDung` | Ngày bắt đầu có hiệu lực | QĐ1, QĐ3 |
| `ngayKetThuc` | Ngày hết hiệu lực | QĐ1, QĐ2, QĐ3 |
| `noiDung` | Nội dung quyết định | Mọi màn hình |
| `filePDF` | Bản ký lưu lại | Mọi màn hình |
| `fileDinhKem` | Tệp đính kèm khác | Mọi màn hình |
| `STATUS` | Trạng thái duyệt | Mọi màn hình |
| `chooseNguoiKy`, `optionAddChungNhan`, `optionAddChungNhanTiengAnh` | Ký số | Mọi màn hình |

**Ba chi tiết đáng lấy:**

1. **Cặp tờ trình → quyết định.** Tờ trình là văn bản đề nghị, quyết định là văn bản phê duyệt. Hai văn bản, hai số, hai ngày, lưu trên cùng một phiếu. Đây là cách công ty Việt Nam thực sự làm việc, và nếu chỉ lưu một trong hai thì hồ sơ không đủ khi cần đối chiếu.
2. **`ngayApDung` tách khỏi `ngayQuyetDinh`.** Quyết định ký ngày 25/03 nhưng hiệu lực từ 01/04 là chuyện bình thường. Trộn hai ngày này làm một là lỗi thiết kế sẽ trả giá ở kỳ tính lương đầu tiên.
3. **`filePDF` — bản ký scan lưu ngay trên phiếu.** Dữ liệu trong hệ thống là để tra cứu; bản ký là bằng chứng. Cả hai phải nằm cùng chỗ.

**Chỗ chưa rõ, phải hỏi:** cả sáu màn hình đều có `ngayApDung` nhưng không quan sát được **hệ thống có tự cập nhật hồ sơ nhân viên vào đúng ngày đó hay không**, hay phải có người bấm. Đây là câu hỏi mang đi phỏng vấn, và cũng là câu hỏi thiết kế cho mình: nếu tự động thì phải có công việc chạy nền hằng ngày.

---

## QĐ1. Quyết định điều chuyển và bổ nhiệm

| | |
|---|---|
| Đường dẫn | `/DieuChuyen/Index`, tạo mới `/DieuChuyen/Create` |
| Dùng để làm gì | Chuyển người sang phòng ban khác, đổi chức danh, bổ nhiệm, giao kiêm nhiệm |
| Ai dùng | Phòng Nhân sự lập, lãnh đạo duyệt |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — phần đầu là thông tin quyết định, phần dưới là bảng danh sách nhân viên được điều chuyển.

**Trường phần đầu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `loaiDieuChuyen` | Loại điều chuyển | Điều chuyển / bổ nhiệm / kiêm nhiệm, phỏng đoán theo tên |
| `lyDoDieuChuyen` | Lý do | Danh mục |
| `soQuyetDinh`, `ngayQuyetDinh` | Số và ngày quyết định | |
| `soToTrinh`, `ngayToTrinh` | Số và ngày tờ trình | |
| `ngayApDung`, `ngayKetThuc` | Hiệu lực từ ngày nào tới ngày nào | `ngayKetThuc` cho phép điều chuyển có thời hạn |
| `nguoiTheoDoi` | Người theo dõi | |
| `noiDung` | Nội dung quyết định | |
| `filePDF`, `fileDinhKem` | Tệp | |

**Cột bảng nhân viên:** STT · Mã nhân viên · Tên nhân viên · Ngày áp dụng · Ngày kết thúc · **Thay thế cho** · Phòng ban · Chức danh · Cấp bậc · Pháp nhân · Phòng ban kiêm nhiệm · Chức danh kiêm nhiệm · Hình thức nhân viên · Nơi làm việc · Ghi chú.

**Chỗ đáng chú ý — bốn cái:**

1. **`ngayApDung` và `ngayKetThuc` có trên TỪNG DÒNG nhân viên**, không chỉ trên phiếu. Một quyết định điều chuyển 5 người, mỗi người có thể hiệu lực một ngày khác nhau.
2. **Cột "Thay thế cho".** Bổ nhiệm ai đó vào vị trí của ai. Chi tiết này làm được hai việc: lịch sử vị trí liền mạch, và biết vị trí nào đang trống.
3. **Có cả phòng ban chính lẫn phòng ban kiêm nhiệm, chức danh chính lẫn chức danh kiêm nhiệm.** Kiêm nhiệm là chuyện phổ biến ở công ty Việt Nam. Nếu mô hình dữ liệu chỉ cho một người thuộc một phòng ban thì không mô tả được, và sẽ phải chắp vá sau.
4. **Có cột "Pháp nhân"** — điều chuyển được giữa các pháp nhân. Với một tập đoàn nhiều công ty con thì đây là nghiệp vụ thật, không phải trường thừa.

---

## QĐ2. Quyết định thôi việc

| | |
|---|---|
| Đường dẫn | `/ThoiViec/Index`, tạo mới `/ThoiViec/Create` |
| Dùng để làm gì | Chấm dứt lao động, và quản lý toàn bộ phần bàn giao đi kèm |
| Ai dùng | Phòng Nhân sự, quản lý trực tiếp, các bộ phận nhận bàn giao |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — đây là màn hình nhiều thẻ nhất trong mục này. Bảy thẻ:

| Thẻ | Bên trong |
|---|---|
| Thông tin phiếu thôi việc | Trường chính của quyết định |
| Tài sản bàn giao | Tài sản đang cấp phát cho người này |
| Bảo hiểm | Thủ tục báo giảm bảo hiểm |
| Công việc bàn giao | Việc đang làm dở, giao lại cho ai |
| Phòng ban phụ trách | Các phòng ban người này đang phụ trách |
| Qui trình phụ trách | Các quy trình duyệt người này đang là người duyệt |
| Công việc đang chờ duyệt | Chứng từ đang nằm ở bước duyệt của người này |

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `maNhanVien`, `phongBan`, `hinhThucNhanVien`, `ngayVaoLam` | Thông tin người nghỉ | Điền tự động |
| `maLyDoThoiViec` | Lý do thôi việc | Danh mục |
| `soQuyetDinh`, `txtNgayQuyetDinh` | Số và ngày quyết định | |
| `txtNgayThoiViec` | Ngày thôi việc | |
| `txtNgayDuyetThoiViec` | Ngày duyệt | |
| `txtTinhLuongDenNgay` | **Tính lương đến ngày nào** | Tách riêng khỏi ngày thôi việc |
| `lsNhanVienBanGiao` | Người nhận bàn giao | Có kèm `lsNhanVienBanGiaoOld` |
| `tenThemNhanhCV`, `thucHien`, `trangThai`, `ngayKetThuc` | Dòng công việc bàn giao | Thêm nhanh từng việc |
| `quyenAdmin` | Cờ quyền quản trị | |
| `ghiChu` | Ghi chú | |

**Chỗ đáng chú ý — đây là màn hình đáng học nhất của cả mục:**

1. **Ba thẻ "Phòng ban phụ trách", "Qui trình phụ trách", "Công việc đang chờ duyệt" giải một bài toán mà hầu hết hệ thống tự làm đều bỏ sót.** Khi một người nghỉ, nếu người đó đang là bước duyệt trong 12 quy trình và đang giữ 7 chứng từ chờ duyệt, thì lúc khóa tài khoản, **12 quy trình đứng và 7 chứng từ kẹt vĩnh viễn**. Không ai biết cho tới khi có người kêu. Họ đưa cả ba danh sách đó lên ngay màn hình thôi việc, buộc phải xử lý trước khi đóng phiếu.

   Hệ thống Thu mua hiện nay có đúng rủi ro này, và chưa có màn hình nào cảnh báo. Đây là chi tiết đáng lấy về **ngay cả khi chưa làm HRM**.

2. **`txtTinhLuongDenNgay` tách khỏi `txtNgayThoiViec`.** Ngày thôi việc là ngày pháp lý; ngày tính lương là ngày kế toán. Có thể lệch nhau vì phép chưa nghỉ hết, vì bàn giao kéo dài, vì lương tháng cuối tính theo ngày công.

3. **Thẻ "Tài sản bàn giao" nối thẳng sang mục tài sản.** Người nghỉ mà chưa trả laptop thì phiếu không đóng được.

---

## QĐ3. Quyết định điều chỉnh lương

| | |
|---|---|
| Đường dẫn | `/PhieuDieuChinhLuong/Index`, tạo mới `/PhieuDieuChinhLuong/Create` |
| Dùng để làm gì | Một đợt điều chỉnh lương, áp cho nhiều người trong một phiếu |
| Ai dùng | Phòng Nhân sự lập, lãnh đạo duyệt |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — hai thẻ: "Thông tin phiếu điều chỉnh lương" và "Danh sách nhân viên".

**Trường phần đầu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieuDieuChinh` | Số phiếu | |
| `tenDotDieuChinhLuong` | Tên đợt | Ví dụ "Điều chỉnh lương quý 1/2026" |
| `soQuyetDinh`, `ngayQuyetDinh` | Số và ngày quyết định | |
| `soToTrinh`, `ngayToTrinh` | Số và ngày tờ trình | |
| `tenNguoiLap`, `ngayLap` | Người lập và ngày lập | |
| `lyDoDieuChinh` | Lý do | |
| `loaiQuyetDinh` | Loại quyết định | |
| `maThamChieu` | Mã tham chiếu | Phỏng đoán: trỏ tới quyết định trước đó |
| `ngayApDung`, `ngayKetThuc` | Hiệu lực | |
| `ketThucHieuLucHDLD` | Cờ kết thúc hiệu lực hợp đồng lao động | Điều chỉnh lương có thể kéo theo phụ lục hợp đồng |
| `canCuQuyetDinh` | Căn cứ ban hành | Văn bản viện dẫn |
| `noiDung` | Nội dung | |

**Cột bảng nhân viên** — 31 cột, và đây là danh sách đáng đọc kỹ vì nó lộ ra toàn bộ cấu trúc lương của họ:

STT · Mã nhân viên · Tên nhân viên · Ngày áp dụng · Ngày kết thúc · Số hợp đồng · Số phụ lục · Thang tính lương · Bậc lương · Hệ số lương · Tổng lương · Lương cơ bản · Lương đóng BH · Khoản bổ sung lương · Quỹ nội bộ · Phí công đoàn · Hỗ trợ ăn ca · Hỗ trợ xăng xe/điện thoại khác · Cập nhật số ngày công · Trợ cấp đi lại · Phụ cấp di chuyển CTR · Trợ cấp điện thoại · Hỗ trợ vị trí công việc · Phụ cấp nhà ở · Phụ cấp di chuyển · Hỗ trợ làm thêm giờ · Hỗ trợ khác · Lương Hiệu Suất · Hỗ trợ điều động/Kiêm nhiệm/khác · Kết quả đánh giá · Ghi chú.

**Chỗ đáng chú ý — ba cái:**

1. **Một phiếu áp cho nhiều người.** Đợt tăng lương thường là 20 tới 100 người cùng lúc, cùng một quyết định. Nếu mô hình bắt một phiếu một người thì phòng Nhân sự sẽ không dùng, họ sẽ quay lại dùng Excel.
2. **Danh sách cột phụ cấp cho thấy phần lớn là do người dùng khai, không phải cột cứng.** "PHỤ CẤP DI CHUYỂN CTR" viết hoa lẫn lộn, "Hỗ trợ xăng xe/điện thoại khác", "Hỗ trợ điều động/Kiêm nhiệm/khác" — đây là tên do khách hàng của họ tự đặt, không phải tên do nhà cung cấp thiết kế. Bằng chứng thêm cho kết luận ở mục [`04` Tiền lương](./04-tien-luong.md): cấu trúc lương phải khai được, không viết cứng.
3. **Có cột "Kết quả đánh giá" ngay trong phiếu điều chỉnh lương.** Nối đánh giá với lương. Nếu công ty muốn tăng lương theo kết quả đánh giá thì hai mục này phải làm gần nhau về thời gian.

---

## QĐ4. Đi làm lại

| | |
|---|---|
| Đường dẫn | `/DiLamLai/Index`, tạo mới `/DiLamLai/Create` |
| Dùng để làm gì | Người đã nghỉ — nghỉ thai sản, nghỉ không lương dài, hoặc thôi việc rồi quay lại | 
| Ai dùng | Phòng Nhân sự |
| Mình có chưa | `[ ]` |

**Trường dữ liệu** — điểm đặc trưng là **mọi trường đều có cặp cũ và mới**:

| Trường cũ | Trường mới | Nghĩa |
|---|---|---|
| `phongBanCu`, `maPhongBanCu` | `maPhongBan`, `treefilter` | Phòng ban |
| `phongBanKiemNhiemCu` | `phongBanKiemNhiemMoi` | Phòng ban kiêm nhiệm |
| `chucDanhCu`, `maChucDanhCu` | `maChucDanhMoi` | Chức danh |
| `hinhThucCu`, `hinhThucNhanVienCu` | `hinhThucNhanVienMoi` | Hình thức nhân viên |
| `diaChiNoiLamViecCu`, `noiLamViecCu` | `noiLamViecMoi` | Nơi làm việc |

Kèm: `maPhieu`, `maNhanVien`, `txtNgayDieuChuyen`, `txtNgayDiLamLai`, `ghiChu`.

**Chỗ đáng chú ý:** lưu cả giá trị cũ lẫn giá trị mới **ngay trên phiếu**, không chỉ ghi giá trị mới rồi đè lên hồ sơ. Nhờ vậy đọc phiếu là biết đã đổi gì, không phải so hai bản hồ sơ.

Đây là kiểu lưu vết đáng lấy, và rẻ hơn nhiều so với làm bảng lịch sử thay đổi cho toàn bộ hồ sơ.

---

## QĐ5. Thành tích và vi phạm

| | |
|---|---|
| Đường dẫn | `/GhiNhanThanhTichVaViPham/Index` |
| Dùng để làm gì | Ghi nhận khen thưởng và kỷ luật |
| Ai dùng | Phòng Nhân sự |
| Mình có chưa | `[ ]` |

**Chưa khảo sát được tập trường.** Đường dẫn `/GhiNhanThanhTichVaViPham/Create` trả về trang rỗng — phỏng đoán là màn hình này mở form bằng cách khác, không qua đường dẫn `Create`.

Điều biết chắc: hồ sơ nhân viên có thẻ "Quyết định", bên trong liệt kê "khen thưởng và kỷ luật" và "thành tích và vi phạm" là hai mục riêng. Tức có phân biệt giữa quyết định chính thức và ghi nhận nội bộ.

**Việc cần làm nếu đi khảo sát tiếp:** mở màn hình này trực tiếp trên giao diện và chụp lại tập trường.

---

## QĐ6. Điều chỉnh hợp đồng

| | |
|---|---|
| Đường dẫn | `/PhieuDieuChinhHopDong/Index`, tạo mới `/PhieuDieuChinhHopDong/Create` |
| Dùng để làm gì | Sửa mức lương trên hợp đồng bằng một phiếu có lưu vết |
| Ai dùng | Phòng Nhân sự |
| Mình có chưa | `[ ]` |

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `maNhanVien` | Nhân viên | |
| `tongLuongCu` | Tổng lương trước điều chỉnh | |
| `mucLuongDieuChinh` | Mức điều chỉnh | |
| `tongLuongSauDieuChinh` | Tổng lương sau điều chỉnh | Tính ra từ hai trường trên |
| `noiDung` | Nội dung | |
| `isUpdate` | Cờ phân biệt tạo mới hay sửa | |
| `fileDinhKem` | Tệp đính kèm | |

**Chỗ đáng chú ý:** màn hình này gọn hơn hẳn QĐ3 và trùng chức năng một phần. Phỏng đoán: QĐ3 dùng cho đợt điều chỉnh hàng loạt có quyết định chính thức, QĐ6 dùng cho điều chỉnh lẻ một người.

Nếu mình làm, **không nên bê cả hai về** — trùng chức năng là nguồn gốc của việc mỗi người làm một kiểu rồi số liệu lệch nhau. Chọn một.

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `DieuChuyen` | `maPhieu`, `loaiDieuChuyen`, `lyDoDieuChuyen`, `soQuyetDinh`, `ngayQuyetDinh`, `soToTrinh`, `ngayToTrinh`, `ngayApDung`, `ngayKetThuc`, `noiDung`, `nguoiTheoDoi`, `filePDF`, `trangThai` | Chắc |
| `DieuChuyenChiTiet` | `maPhieu`, `maNhanVien`, `ngayApDung`, `ngayKetThuc`, `thayTheCho`, `maPhongBan`, `maChucDanh`, `maCapBac`, `maPhapNhan`, `maPhongBanKiemNhiem`, `maChucDanhKiemNhiem`, `hinhThucNhanVien`, `noiLamViec`, `ghiChu` | Chắc |
| `ThoiViec` | `maPhieu`, `maNhanVien`, `maLyDoThoiViec`, `soQuyetDinh`, `ngayQuyetDinh`, `ngayThoiViec`, `ngayDuyetThoiViec`, `tinhLuongDenNgay`, `lsNhanVienBanGiao`, `filePDF`, `trangThai` | Chắc |
| `ThoiViecBanGiaoCongViec` | `maPhieu`, `tenCongViec`, `nguoiThucHien`, `trangThai`, `ngayKetThuc` | Khá |
| `ThoiViecBanGiaoTaiSan` | `maPhieu`, `maTaiSan`, `trangThai` | Khá — có thể chỉ là truy vấn từ bảng tài sản, không lưu riêng |
| `PhieuDieuChinhLuong` | `maPhieuDieuChinh`, `tenDotDieuChinhLuong`, `soQuyetDinh`, `ngayQuyetDinh`, `soToTrinh`, `ngayToTrinh`, `lyDoDieuChinh`, `loaiQuyetDinh`, `maThamChieu`, `ngayApDung`, `ngayKetThuc`, `ketThucHieuLucHDLD`, `canCuQuyetDinh` | Chắc |
| `PhieuDieuChinhLuongChiTiet` | `maPhieuDieuChinh`, `maNhanVien`, `ngayApDung`, `soHopDong`, `soPhuLuc`, `maThangTinhLuong`, `bacLuong`, `heSoLuong`, `tongLuong`, `luongCoBan`, `luongDongBaoHiem`, và một tập cột phụ cấp | Khá — **tập cột phụ cấp nhiều khả năng không cố định**, mà sinh từ danh mục phụ cấp |
| `DiLamLai` | `maPhieu`, `maNhanVien`, `ngayDieuChuyen`, `ngayDiLamLai`, và các cặp cột cũ/mới cho phòng ban, chức danh, hình thức, nơi làm việc | Chắc |
| `ThanhTichViPham` | Theo khuôn quyết định chung | Đoán — chưa khảo sát được tập trường |
| `PhieuDieuChinhHopDong` | `maPhieu`, `maNhanVien`, `tongLuongCu`, `mucLuongDieuChinh`, `tongLuongSauDieuChinh`, `noiDung` | Chắc |

**Điểm thiết kế cần quyết trước khi viết mã:** tập cột phụ cấp trong `PhieuDieuChinhLuongChiTiet`. Nếu là cột cứng thì thêm một khoản phụ cấp là một lần đổi bảng — vi phạm quy tắc 1 của bộ tài liệu. Nếu là dòng-thuộc-tính thì linh hoạt nhưng báo cáo phức tạp hơn. Đây là cùng một câu hỏi đã nêu ở [`04` Tiền lương](./04-tien-luong.md), và nên trả lời một lần cho cả hai chỗ.

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| Ba thẻ kiểm tra trước khi khóa người dùng (từ QĐ2) | **Lấy ngay** | Rủi ro này đang có ở Thu mua hôm nay, không cần chờ HRM. Người nghỉ việc mà đang là bước duyệt thì chứng từ kẹt im lặng | Không cần cả màn hình thôi việc. Chỉ cần: trước khi khóa tài khoản, hiện danh sách chứng từ đang chờ người này duyệt và các quy trình có người này |
| QĐ1 Điều chuyển và bổ nhiệm | **Lấy sau** — cùng vòng với hồ sơ nhân viên | Đây là loại quyết định phát sinh nhiều nhất, và là thứ giữ cho sơ đồ tổ chức đúng | Giữ nguyên: một phiếu nhiều người, ngày hiệu lực trên từng dòng, cột "Thay thế cho", có kiêm nhiệm |
| Khuôn quyết định dùng chung | **Lấy sau**, nhưng thiết kế ngay từ đầu | Sáu màn hình cùng một khuôn. Viết sáu lần là lãng phí và sẽ lệch nhau | Làm một khuôn: tờ trình, quyết định, ngày hiệu lực, nội dung, PDF, trạng thái duyệt. Mỗi loại chỉ khai thêm bảng chi tiết riêng |
| QĐ2 Thôi việc (đầy đủ) | **Lấy sau** | Cần có tài sản, bảo hiểm, công việc thì các thẻ mới có nội dung | Bản đầu chỉ cần thẻ thông tin và thẻ công việc đang chờ duyệt. Bốn thẻ còn lại thêm dần theo mức độ sẵn sàng của các mục khác |
| QĐ3 Điều chỉnh lương | **Lấy sau**, chờ quyết định về phạm vi lương | Nếu không làm lương trong bản 1 thì phiếu này không có chỗ để tác động vào | Bắt buộc giữ: một phiếu nhiều người. Tập cột phụ cấp phải khai được, không viết cứng |
| QĐ4 Đi làm lại | **Lấy sau** | Ít phát sinh | Cách lưu cặp cũ/mới thì đáng lấy làm nguyên tắc chung cho mọi quyết định, không riêng màn hình này |
| QĐ5 Thành tích và vi phạm | **Lấy sau** | Chưa đủ dữ liệu để đánh giá | Khảo sát lại trước khi quyết |
| QĐ6 Điều chỉnh hợp đồng | **Không lấy** | Trùng chức năng với QĐ3 | Gộp vào QĐ3 bằng cách cho phép phiếu có đúng một dòng nhân viên |

**Thứ tự đề nghị trong mục này:** ba thẻ kiểm tra trước khi khóa tài khoản làm ngay, tách rời khỏi HRM. Phần còn lại đi sau hồ sơ nhân viên và hợp đồng, vì quyết định là thứ tác động lên hai cái đó — không có hai cái đó thì quyết định không có đích để tác động.
