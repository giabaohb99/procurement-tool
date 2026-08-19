# ĐƠN TỪ VÀ BỘ MÁY DUYỆT

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 7 (5 loại đơn + cấu hình loại đơn + bộ máy duyệt) |

---

## Tóm tắt mục này

Đơn từ là phần nhân viên bình thường chạm vào hằng tuần. Cả công ty dùng, không phải chỉ phòng Nhân sự dùng. Vì vậy đây là mục có tỷ lệ "số người được lợi trên số công bỏ ra" cao nhất trong toàn bộ hệ thống HRM.

Họ làm **năm loại đơn thành năm màn hình riêng**, mỗi loại một tập trường khác nhau, không gộp chung thành một màn hình "đơn từ" có ô chọn loại. Nhìn tập trường thì hiểu vì sao: đơn nghỉ phép hỏi quỹ phép, đơn tăng ca hỏi hệ số và giờ quy đổi, đơn bổ sung công hỏi giờ quẹt thẻ. Không có mẫu số chung đáng kể.

Nhưng cái đứng sau năm màn hình đó mới là phần đáng học. Có **một bảng cấu hình loại đơn** với gần 50 cột, khai được: đơn này có tính công không, tính theo ca hay không theo ca, tối đa bao nhiêu ngày một năm, tối đa bao nhiêu lần một tháng, áp dụng cho giới tính nào, cho người trong nước hay người nước ngoài, và **số ngày phép tăng theo thâm niên khai bằng bảng chứ không viết cứng**. Và có **một bộ máy duyệt dùng chung cho 88 loại công việc** — không phải chỉ đơn từ.

Đối chiếu với mình: hệ thống Thu mua hiện nay duyệt bằng mã nguồn cứng cho từng loại chứng từ. Đổi luồng duyệt là sửa mã nguồn, chờ đợt phát hành. Cách đó đang chịu được vì mới có vài loại chứng từ. Sang ERP nhiều phân hệ thì số loại chứng từ lên hàng chục, cách đó gãy.

**Kết luận sớm cho mục này:** bộ máy duyệt không thuộc HRM. Nó thuộc phần nền dùng chung, và nên làm trước HRM chứ không phải làm trong HRM.

---

## Danh sách chức năng

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| DT1 | Nghỉ phép | `/NghiPhep/Index` | Nhân viên nộp đơn nghỉ, hệ thống trừ quỹ phép | `[ ]` |
| DT2 | Bổ sung công | `/BoSungCong/Index` | Quên quẹt thẻ thì nộp đơn bù | `[ ]` |
| DT3 | Công tác | `/CongTac/Index` | Đăng ký đi công tác, tính là ngày công | `[ ]` |
| DT4 | Tăng ca | `/TangCa/Index` | Đăng ký tăng ca cá nhân, có hệ số | `[ ]` |
| DT5 | Tăng ca phòng ban | `/TangCaPhongBan/Index` | Đăng ký tăng ca cho cả nhóm trong một phiếu | `[ ]` |
| DT6 | Cấu hình loại đơn từ | Trong `/CauHinhHeThong/Index`, bấm mục "Cấu hình loại đơn từ" | Khai luật của từng loại đơn: hạn mức, cách tính công, phạm vi áp dụng | `[ ]` |
| DT7 | Quy trình duyệt | `/QuiTrinhDuyet/Index` | Bộ máy duyệt dùng chung cho 88 loại công việc | `[~]` duyệt cứng trong mã nguồn |

---

## DT1. Nghỉ phép

| | |
|---|---|
| Đường dẫn | `/NghiPhep/Index`, tạo mới `/NghiPhep/Create` |
| Dùng để làm gì | Nhân viên nộp đơn xin nghỉ. Hệ thống đối chiếu với quỹ phép năm và trừ vào bảng công |
| Ai dùng | Toàn bộ nhân viên nộp; quản lý duyệt; phòng Nhân sự theo dõi |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — bốn thẻ: Nghỉ phép · Lịch nghỉ · Export · Import.

Thẻ "Lịch nghỉ" là phần đáng chú ý — cùng dữ liệu nhưng nhìn theo dạng lịch, để quản lý thấy tuần tới ai nghỉ.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | Khóa nghiệp vụ dạng chuỗi |
| `maNhanVien` | Người xin nghỉ | |
| `phongBan` | Phòng ban | Điền tự động theo nhân viên |
| `lsNhanVienBanGiao` | Danh sách người nhận bàn giao việc | Chọn nhiều. Có kèm `lsNhanVienBanGiaoOld` để so sánh khi sửa |
| `loaiNghiPhep` | Loại nghỉ | Lấy từ bảng cấu hình DT6 |
| `maPhanCa` | Ca làm việc áp dụng | Cần vì nghỉ nửa ngày phụ thuộc ca |
| `soNgayNghiPhep` | Số ngày xin nghỉ | |
| `soPhepConLai` | Số phép còn lại | **Hiện ngay trên form lúc nộp** |
| `phepConLai` | Phép còn lại | Trường hiển thị riêng |
| `phepUng` | Phép ứng trước | Cho nghỉ vượt quỹ, ghi nợ |
| `soGioNghiBuConLai` | Giờ nghỉ bù còn lại | Sinh ra từ đơn tăng ca |
| `ngayBatDau`, `ngayKetThuc` | Khoảng nghỉ | |
| `soGioNghiPhep` | Số giờ nghỉ | Dùng khi nghỉ theo giờ |
| `soNgayNghiPhepThucTe` | Số ngày thực tế | Trừ ngày lễ và ngày nghỉ tuần ra khỏi khoảng |
| `lyDo` | Lý do | |
| `tong`, `tongTrongNam` | Tổng đã nghỉ, tổng trong năm | Để kiểm hạn mức |
| `chinhSach` | Chính sách áp dụng | Văn bản hiện lên cho người nộp đọc |
| `ghiChuPhepNam` | Ghi chú quỹ phép | |
| `fileDinhKem`, `filePDF` | Tệp đính kèm và bản PDF | |
| `chooseNguoiKy`, `optionAddChungNhan` | Người ký và tùy chọn chứng nhận | Liên quan tới ký số |

**Nút trên form:** Lưu thêm mới · Xác nhận · Thoát · Gửi yêu cầu ký · Chữ ký nháy · Chữ ký 1:1 · Chữ ký.

**Chỗ đáng chú ý — ba cái:**

1. **`soPhepConLai` và `soGioNghiBuConLai` hiện ngay trên form.** Nhân viên biết mình còn bao nhiêu trước khi bấm nộp. Chi tiết nhỏ, nhưng nó cắt phần lớn số đơn sai và phần lớn câu hỏi gửi về phòng Nhân sự.
2. **`lsNhanVienBanGiao`** — bàn giao việc cho ai khi nghỉ. Trường này xuất hiện cả ở đây và ở quyết định thôi việc. Đúng nghiệp vụ, và rẻ để làm.
3. **`phepUng`** — cho phép nghỉ vượt quỹ và ghi nợ. Đây là quy tắc chính sách, không phải quy tắc kỹ thuật. Nếu công ty mình không cho ứng phép thì bỏ trường này; nếu có cho thì phải hỏi rõ ứng tối đa bao nhiêu và thu hồi khi thôi việc thế nào.

---

## DT2. Bổ sung công

| | |
|---|---|
| Đường dẫn | `/BoSungCong/Index`, tạo mới `/BoSungCong/Create` |
| Dùng để làm gì | Quên quẹt thẻ, máy hỏng, quẹt lệch giờ — nhân viên nộp đơn để sửa dòng công |
| Ai dùng | Toàn bộ nhân viên |
| Mình có chưa | `[ ]` |

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `maNhanVien`, `maPhongBan`, `phongBan` | Người và phòng ban | |
| `txtNgayLamViec` | Ngày cần bổ sung | |
| `idPhanCaNhanVien` | Ca của người đó hôm ấy | Lấy từ bảng phân ca |
| `gioVaoCuaCa`, `gioRaCuaCa`, `gioKetThucCa` | Giờ chuẩn của ca | Hiển thị để đối chiếu |
| `txtQuetVao`, `txtQuetRa` | Giờ quẹt thực tế | Lấy từ dữ liệu máy chấm công |
| `txtNgayBatDau`, `txtNgayKetThuc` | Khoảng bổ sung | Cho phép bổ sung nhiều ngày một phiếu |
| `lyDoDieuChinh` | Lý do | Danh mục chọn, không phải nhập tay |
| `noiDung` | Diễn giải | |
| `tong` | Tổng | |

**Chỗ đáng chú ý:** form hiện **cả giờ chuẩn của ca lẫn giờ quẹt thực tế** ngay cạnh nhau. Người duyệt nhìn một màn hình là quyết được, không phải mở bảng công ra tra. Đây là kiểu thiết kế "đưa dữ liệu tới chỗ ra quyết định" — đáng lấy nguyên tắc, không chỉ lấy màn hình.

Và `lyDoDieuChinh` là **danh mục** chứ không phải ô nhập tự do. Nhờ vậy mới thống kê được "tháng này có bao nhiêu đơn bổ sung do máy hỏng" — tức mới biết máy chấm công có vấn đề hay nhân viên có vấn đề.

---

## DT3. Công tác

| | |
|---|---|
| Đường dẫn | `/CongTac/Index`, tạo mới `/CongTac/Create` |
| Dùng để làm gì | Đăng ký đi công tác. Ngày công tác vẫn tính là ngày công |
| Ai dùng | Nhân viên đi công tác |
| Mình có chưa | `[ ]` |

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `maNhanVien`, `phongBan` | Người và phòng ban | |
| `maCongTac`, `noiCongTac` | Mã và nơi công tác | |
| `TxtngayBatDau`, `TxtngayKetThuc` | Khoảng thời gian | |
| `maCa` | Ca áp dụng | |
| `soNgayCongTac`, `soGioCongTac` | Số ngày và số giờ | |
| `quangDuong` | Quãng đường | Phỏng đoán dùng để tính công tác phí theo km |
| `latNoiDi`, `lngNoiDi` | Tọa độ nơi đi | Vĩ độ và kinh độ |
| `maPhongBan`, `tenPhongBan`, `treefilter2` | Chọn phòng ban theo cây | Có nút "Chọn phòng ban" |
| `lyDo`, `noiDung` | Lý do và nội dung | |

**Chỗ đáng chú ý:** có `latNoiDi` và `lngNoiDi` — tọa độ. Phỏng đoán: dùng để tính khoảng cách tự động, hoặc để nới điều kiện chấm công theo vị trí trong những ngày đi công tác. Chi tiết này gợi ra một câu hỏi phải mang đi phỏng vấn: **khi nhân viên đi công tác thì chấm công thế nào** — vì đây là chỗ mọi hệ thống chấm công theo GPS đều vướng.

---

## DT4. Tăng ca

| | |
|---|---|
| Đường dẫn | `/TangCa/Index`, tạo mới `/TangCa/Create` |
| Dùng để làm gì | Đăng ký tăng ca cho một người, có hệ số, có quy đổi ra nghỉ bù |
| Ai dùng | Nhân viên, quản lý trực tiếp |
| Mình có chưa | `[ ]` |

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maPhieu` | Số phiếu | |
| `maNhanVien`, `maPhongBan`, `treefilter` | Người và phòng ban | |
| `tinhTheoGioChamCong` | Cờ: lấy giờ thực quẹt hay lấy giờ đăng ký | **Trường quyết định cách tính** |
| `ngayTangCa` | Ngày tăng ca | |
| `txtGioBatDau`, `txtGioKetThuc` | Giờ bắt đầu và kết thúc | |
| `loaiTangCa` | Loại tăng ca | Ngày thường / cuối tuần / ngày lễ, phỏng đoán |
| `hinhThucTangCa` | Hình thức | |
| `heSoTangCa` | Hệ số | |
| `thoiGianNghiGiuaCa` | Nghỉ giữa ca | Trừ ra khỏi số giờ tính |
| `soGioTangCa` | Số giờ thực | |
| `soGioTangCaCHS` | Số giờ đã nhân hệ số | |
| `soGioTangCaTrongThang`, `soGioTangCaTrongNam` | Lũy kế tháng và năm | Để chặn vượt trần luật lao động |
| `soGioQuiDoi` | Số giờ quy đổi | |
| `soNgayTangCa` | Số ngày | |
| `soNgayNghiBu` | Số ngày nghỉ bù sinh ra | Nối sang DT1 qua `soGioNghiBuConLai` |
| `loaiTangCaTuDong` | Cờ tự nhận loại | |
| `chinhSach`, `cauH`, `chinhS`, `ghiChu`, `noiDung` | Chính sách và ghi chú | |

**Chỗ đáng chú ý — hai cái:**

1. **`soGioTangCaTrongThang` và `soGioTangCaTrongNam` hiện ngay trên form.** Luật lao động có trần giờ tăng ca theo tháng và theo năm. Hệ thống đưa con số lũy kế lên form để người duyệt biết mình sắp duyệt vượt trần. Đây là chi tiết tuân thủ pháp luật, không phải chi tiết tiện dụng — nếu tự làm mà không nhìn thấy trước thì chắc chắn bỏ sót.
2. **Tăng ca sinh ra nghỉ bù, nghỉ bù tiêu ở đơn nghỉ phép.** Hai màn hình rời nhau nhưng có một quỹ chung. Phải thiết kế quỹ đó ngay từ đầu, không thể ghép sau.

---

## DT5. Tăng ca phòng ban

| | |
|---|---|
| Đường dẫn | `/TangCaPhongBan/Index`, tạo mới `/TangCaPhongBan/Create` |
| Dùng để làm gì | Một phiếu đăng ký tăng ca cho cả nhóm người |
| Ai dùng | Quản lý phòng ban |
| Mình có chưa | `[ ]` |

**Cấu trúc màn hình** — phần đầu là thông tin chung của cả phiếu, phần dưới là bảng danh sách nhân viên.

Cột bảng nhân viên: STT · Mã nhân viên · Họ và tên · Phòng ban · Chức danh · Tổng giờ tăng ca trong tháng · Tổng giờ tăng ca trong năm · Nhân viên xác nhận.

**Trường dữ liệu** — dùng lại gần hết tập trường của DT4, cộng thêm:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `checkThayDoiChiTiet` | Cho sửa riêng từng dòng | Mặc định mọi người cùng giờ, ai khác thì sửa dòng đó |
| `nhanVienXacNhan` | Nhân viên xác nhận | |
| `ngayKetThucTB`, `trangThaiTB`, `noiDungTB` | Bộ ba trường thông báo | Phỏng đoán là thông báo gửi tới từng người trong danh sách |

**Chỗ đáng chú ý:** cột "Nhân viên xác nhận" và trường `nhanVienXacNhan`. Quản lý đăng ký tăng ca thay cho cả nhóm, nhưng **từng người vẫn phải xác nhận**. Đây là nghiệp vụ, không phải giao diện: tăng ca là thỏa thuận hai bên theo luật, không phải lệnh một chiều. Nếu tự làm mà bỏ bước xác nhận thì phiếu tăng ca không có giá trị pháp lý.

Và cột "Tổng giờ tăng ca trong tháng / trong năm" nằm ngay trên từng dòng nhân viên — cùng logic chặn trần như DT4, nhưng nhìn được cho cả nhóm một lúc.

---

## DT6. Cấu hình loại đơn từ

| | |
|---|---|
| Đường dẫn | Không có đường dẫn riêng. Vào `/CauHinhHeThong/Index` rồi bấm mục "Cấu hình loại đơn từ" |
| Dùng để làm gì | Khai luật của từng loại đơn: tính công thế nào, hạn mức bao nhiêu, ai được dùng |
| Ai dùng | Phòng Nhân sự, quản trị hệ thống |
| Mình có chưa | `[ ]` |

**Mười lăm loại đơn có sẵn trong bản demo**, kèm mã:

| Mã | Tên |
|---|---|
| `DIHOC` | Đi học |
| `BOSUNGCONG` | Bổ sung công |
| `DILAM` | Đi làm |
| `TANGCA` | Tăng ca |
| `HIEUHI` | Hiếu / Hỉ |
| `PHEPNAM` | Phép năm |
| `NGHIBU` | Nghỉ bù tăng ca |
| `ONSITE` | Onsite |
| `NGHIKLUONG` | Nghỉ không lương |
| `WFH` | Làm việc tại nhà |
| `THAISAN` | Nghỉ thai sản |
| `NGHILE` | Nghỉ lễ |
| `TANGCAPHONGBAN` | Tăng ca phòng ban |
| `DITREVESOM` | Đi trễ về sớm |
| `CHEDO` | Nghỉ chế độ |

**Trường dữ liệu** — khoảng 50 trường, chia bốn nhóm.

Nhóm nhận dạng:

| Trường | Nghĩa |
|---|---|
| `maLoaiNghiPhep` | Mã loại |
| `loaiDonTu` | Đơn này thuộc nhóm nào: Nghỉ phép / Bổ sung công / Công tác / Tăng ca / Tăng ca phòng ban / Đi làm / Làm việc từ xa / Nghỉ bảo hiểm xã hội |
| `tenLoaiNghiPhep`, `tenTiengAnh` | Tên hiển thị |
| `kiHieu` | Ký hiệu in trên bảng công |
| `thuTu` | Thứ tự hiển thị |
| `trangThai` | Còn dùng hay đã ngừng |

Nhóm cách tính công:

| Trường | Nghĩa |
|---|---|
| `tinhCong` | Loại nghỉ này có tính là ngày công không |
| `theoCaLamViec` / `khongTheoCaLamViec` | Tính theo ca hay tính theo ngày trơn |
| `tyLeHuongBH` | Tỷ lệ hưởng bảo hiểm |
| `uuTienTruocNghiLe` | Ưu tiên trước ngày lễ khi trùng |
| `khongCheckTrungDon` | Cho phép trùng với đơn khác |
| `congDonNam` | Cộng dồn sang năm sau |
| `giaoDuMuc` | Giao đủ mức |
| `chinhSach` | Văn bản chính sách hiện cho người nộp đọc |

Nhóm hạn mức:

| Trường | Nghĩa |
|---|---|
| `soNghiToiDaTrenNam`, `tgNghiToiDaTrenNam` | Tối đa trên năm |
| `soNgayNghiToiDa`, `thoiGianNgayNghiToiDa` | Tối đa số ngày một lần |
| `soLanNghiToiDa`, `thoiGianLanNghiToiDa` | Tối đa số lần trong một khoảng |
| `soLanDangKiToiDa` | Tối đa số lần đăng ký |
| `soNgayTu`, `soNgayDen`, `soNgayRB` | Bảng bậc số ngày |
| `thamNienTu`, `thamNienDen`, `soNgayRBTN` | **Bảng bậc số ngày theo thâm niên** |

Nhóm phạm vi áp dụng:

| Trường | Nghĩa |
|---|---|
| `gioiTinh` | Chỉ áp dụng cho giới tính nào |
| `nguoiTrongNuoc`, `nguoiNuocNgoai` | Áp dụng cho ai |
| `lsPhongBanApDung`, `lsChucDanhApDung`, `lsCapBacCVApDung`, `lsNhanVienApDung`, `lsHinhThucNVApDung` | Danh sách áp dụng |
| `lsNhanVienLoaiTru` | Danh sách loại trừ |
| `toanTuApDung` | Toán tử ghép các điều kiện: And hoặc Or |

**Chỗ đáng chú ý — ba cái, và cả ba đều quan trọng:**

1. **`thamNienTu` / `thamNienDen` / `soNgayRBTN` — phép năm tăng theo thâm niên khai bằng bảng.** Bộ luật Lao động quy định cứ 5 năm làm việc thì thêm 1 ngày phép. Họ không viết cứng con số 5 vào mã nguồn mà làm thành bảng bậc. Đây là chi tiết phải lấy: quy định đổi thì sửa dữ liệu, không sửa mã nguồn.
2. **Cặp `lsXApDung` + `lsNhanVienLoaiTru` + `toanTuApDung`.** Khuôn "danh sách áp dụng, danh sách loại trừ, toán tử And/Or" lặp lại ở đây, ở cấu hình bảng lương, và ở quy trình duyệt. Ba chỗ khác nhau cùng một khuôn — tức đây là một thành phần dùng lại được, không phải ba lần viết riêng. **Nếu mình làm, nên làm thành một thành phần dùng chung ngay từ lần đầu.**
3. **`tinhCong` là cờ trên cấu hình, không phải luật viết trong mã.** Nghĩa là câu hỏi "nghỉ ốm có tính công không" trả lời bằng cách sửa một ô, không phải bằng cách mở phiếu yêu cầu sửa phần mềm. Với một công ty đang chuẩn hóa lại nghiệp vụ, chỗ này sẽ đổi nhiều lần trong năm đầu.

---

## DT7. Quy trình duyệt

| | |
|---|---|
| Đường dẫn | `/QuiTrinhDuyet/Index` |
| Dùng để làm gì | Khai luồng duyệt cho từng loại chứng từ, dùng chung toàn hệ thống |
| Ai dùng | Quản trị hệ thống |
| Mình có chưa | `[~]` — có duyệt, nhưng luồng viết cứng trong mã nguồn |

**Cấu trúc màn hình** — một danh sách. Cột bảng: STT · Tên qui trình · Trạng thái · Người duyệt · Phòng ban áp dụng · Chức vụ áp dụng · Nhân viên áp dụng · Phòng ban loại trừ · Chức vụ loại trừ · Nhân viên loại trừ · Thao tác.

Thao tác trên mỗi dòng: Sửa · Xóa · **Copy** · Xem.

**Bộ lọc:** `trangThaiSearch`, `congViec` (loại công việc), `qSearch`, `clsQSearchCV`, `trangThaiDong`, `pageSize`.

**Cột "Người duyệt"** hiển thị nguyên chuỗi bước theo thứ tự, dạng `1: X => 2: Y => 3: Z`. Mỗi bước là một trong hai kiểu:

- **Người cụ thể** — gọi đích danh một nhân viên.
- **Vai tương đối** — "Người lập phiếu", "Người quản lý trực tiếp", "Quản lý phòng ban của người lập phiếu", "Chức danh &lt;tên chức danh&gt;".

**Số loại công việc:** ô chọn `congViec` có **89 mục, tức 88 loại công việc thật** (một mục là dòng trống). Trong đó có cả những loại rõ ràng do người dùng tự dựng — "Form HTML", "Đề xuất chủ trương", "Yêu cầu mua hàng" — nghĩa là hệ thống có bộ dựng biểu mẫu, và mọi biểu mẫu tự dựng đều dùng chung bộ máy duyệt này.

**Chỗ đáng chú ý — bốn cái:**

1. **Vai tương đối là điểm mấu chốt của cả bộ máy.** Nếu chỉ khai được người đích danh thì mỗi lần đổi trưởng phòng phải sửa lại toàn bộ quy trình, và sẽ có quy trình bị quên, và đơn sẽ nằm chờ một người đã nghỉ việc. Vai tương đối làm quy trình tự đúng theo sơ đồ tổ chức.
2. **Vai tương đối chỉ chạy đúng nếu trường "Người quản lý" trên hồ sơ nhân viên đúng.** Dữ liệu nền sai thì luồng duyệt sai, và sai kiểu im lặng. Đây là ràng buộc giữa hai mục — xem thêm [`01` Nhân sự](./01-nhan-su.md).
3. **Nút Copy trên từng dòng.** 88 loại công việc, phần lớn luồng giống nhau. Copy rồi sửa là cách duy nhất để việc khai cấu hình không thành cực hình. Chi tiết nhỏ nhưng nói lên là họ đã chạy thật với số lượng lớn.
4. **Một bộ máy phục vụ 88 loại, không phải 88 đoạn mã.** Đây là khác biệt kiến trúc lớn nhất giữa họ và mình ở thời điểm này.

**Đối chiếu với hệ thống Thu mua:** hiện nay mỗi loại chứng từ có luồng duyệt riêng viết trong mã nguồn. Muốn thêm một bước duyệt là sửa mã, chạy migration nếu đổi trạng thái, phát hành lại. Với số loại chứng từ hiện tại thì chịu được. Với ERP nhiều phân hệ thì không.

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `LoaiDonTu` | `maLoaiNghiPhep`, `loaiDonTu`, `tenLoaiNghiPhep`, `kiHieu`, `tinhCong`, `theoCaLamViec`, các cột hạn mức, các cột `lsXApDung`, `toanTuApDung` | Chắc |
| `LoaiDonTuThamNien` | `maLoaiNghiPhep`, `thamNienTu`, `thamNienDen`, `soNgayRBTN` | Khá — có thể nằm luôn trong `LoaiDonTu` nếu chỉ một bậc |
| `DonNghiPhep` | `maPhieu`, `maNhanVien`, `loaiNghiPhep`, `maPhanCa`, `ngayBatDau`, `ngayKetThuc`, `soNgayNghiPhep`, `soNgayNghiPhepThucTe`, `lyDo`, `lsNhanVienBanGiao`, `trangThai` | Chắc |
| `DonBoSungCong` | `maPhieu`, `maNhanVien`, `ngayLamViec`, `idPhanCaNhanVien`, `quetVao`, `quetRa`, `lyDoDieuChinh` | Chắc |
| `DonCongTac` | `maPhieu`, `maNhanVien`, `maCongTac`, `noiCongTac`, `ngayBatDau`, `ngayKetThuc`, `soNgayCongTac`, `quangDuong`, `latNoiDi`, `lngNoiDi` | Chắc |
| `DonTangCa` | `maPhieu`, `maNhanVien`, `ngayTangCa`, `gioBatDau`, `gioKetThuc`, `loaiTangCa`, `heSoTangCa`, `soGioTangCa`, `soGioTangCaCHS`, `soGioQuiDoi`, `soNgayNghiBu` | Chắc |
| `DonTangCaPhongBan` + bảng con dòng nhân viên | Phiếu cha giữ thông tin chung, bảng con một dòng một người, có cột xác nhận | Khá |
| `QuyTrinhDuyet` | `tenQuyTrinh`, `loaiCongViec`, `trangThai`, các cột áp dụng và loại trừ theo phòng ban / chức vụ / nhân viên | Chắc |
| `QuyTrinhDuyetBuoc` | `idQuyTrinh`, `thuTu`, `loaiNguoiDuyet` (đích danh / người lập / quản lý trực tiếp / quản lý phòng ban của người lập / theo chức danh), `maNhanVien` hoặc `maChucDanh` | Chắc |
| `LichSuDuyet` | `loaiChungTu`, `maPhieu`, `buoc`, `nguoiDuyet`, `thoiDiem`, `hanhDong`, `yKien` | Khá |

`LichSuDuyet` là bảng dùng chung cho mọi loại chứng từ, khóa bằng cặp `loaiChungTu` + `maPhieu`. Cơ sở để tin: trong phần cấu hình hệ thống có màn hình riêng tên "Xóa lịch sử duyệt" — chỉ có nghĩa nếu lịch sử duyệt nằm ở một chỗ.

**Không quan sát được:** quỹ nghỉ bù sinh ra từ tăng ca lưu ở đâu. Có thể là một bảng riêng, có thể tính lại mỗi lần từ các đơn tăng ca đã duyệt. Đây là câu hỏi thiết kế phải trả lời trước khi làm DT4.

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| DT7 Quy trình duyệt | **Lấy ngay** | Đây là hạng mục có giá trị cao nhất trong cả tài liệu này, và nó **không thuộc HRM** — nó thuộc phần nền. Làm xong thì mọi phân hệ sau đều dùng | Không cần 88 loại. Bắt đầu bằng đúng các loại chứng từ đang có ở Thu mua, cộng đơn từ. Giữ nguyên ý tưởng vai tương đối. Bỏ phần bộ dựng biểu mẫu |
| DT1 Nghỉ phép | **Lấy ngay** | Cả công ty dùng. Rẻ để làm nếu bộ máy duyệt đã có. Hiệu quả thấy được ngay | Bỏ `phepUng` nếu công ty không cho ứng phép. Giữ `soPhepConLai` hiện trên form — đây là phần đáng giá nhất của màn hình |
| DT6 Cấu hình loại đơn | **Lấy ngay**, nhưng gọn hơn | Không có nó thì mọi luật nghỉ phép nằm trong mã nguồn | Bỏ bớt: bản 1 chỉ cần `tinhCong`, `theoCaLamViec`, hạn mức năm, và bảng bậc thâm niên. Khoảng 12 trường thay vì 50 |
| DT2 Bổ sung công | **Lấy sau** | Chỉ có nghĩa khi đã có chấm công. Trước đó không có gì để bổ sung | Giữ nguyên ý tưởng hiện giờ chuẩn của ca cạnh giờ quẹt thực tế. Giữ `lyDoDieuChinh` là danh mục |
| DT4 Tăng ca | **Lấy sau** | Phụ thuộc chấm công và phụ thuộc quyết định có làm lương hay không | Bắt buộc giữ lũy kế giờ tăng ca tháng và năm — đây là ràng buộc pháp luật, không phải tiện dụng |
| DT5 Tăng ca phòng ban | **Lấy sau** | Phần mở rộng của DT4 | Bắt buộc giữ bước nhân viên xác nhận |
| DT3 Công tác | **Lấy sau** | Ít người dùng hơn ba loại kia | Cân nhắc bỏ tọa độ và quãng đường nếu chưa làm công tác phí |

**Thứ tự đề nghị trong mục này:** DT7 trước, rồi DT6 và DT1 cùng nhau. Ba cái còn lại chờ kết quả quyết định về phạm vi chấm công (mục C2 trong [danh mục chờ quyết](../04-danh-muc-cho.md)).

Lý do xếp DT7 lên đầu: nó không phụ thuộc gì cả, và mọi thứ khác phụ thuộc nó. Làm DT1 trước DT7 thì phải viết luồng duyệt cứng cho nghỉ phép, rồi vứt đi lúc làm DT7.
