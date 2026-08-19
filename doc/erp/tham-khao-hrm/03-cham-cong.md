# CHẤM CÔNG

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 7 |

## Tóm tắt mục này

Chấm công trong HrOnline chia thành hai lớp tách biệt: dữ liệu thô từ máy chấm công (không sửa được) và bảng công đã tổng hợp (sửa được). Luồng tính công chính nằm ở Bảng công động, gồm ba bước bấm tay theo thứ tự: tải dữ liệu thô, tổng hợp với ca và đơn từ đã duyệt, sau đó tính công để ra số ngày công và giờ tăng ca. Kết thúc chu kỳ là thao tác Chốt công — sau đó bảng bị khóa và mọi thay đổi phải qua bước mở lại có ghi log. Ba bước tách rời, không gộp thành một nút, vì mỗi bước có thể hỏng vì lý do khác nhau và cần chạy lại riêng.

Để bảng công chạy được, hệ thống cần hai nền tảng riêng: Thiết lập ca (định nghĩa ca làm việc, máy chấm công, GPS) và Phân ca xếp lịch (gán nhân viên vào ca từng ngày). Hệ thống hỗ trợ nhiều phương thức chấm công cho từng nhân viên: GPS, Wifi, máy chấm công vật lý, Face ID, và chấm qua app — cấu hình riêng cho từng người qua màn hình CC7.

Quản lý phép năm là một mô-đun riêng theo dõi quỹ phép từng nhân viên, kết chuyển năm cũ, và phép bù tăng ca. Ngày nghỉ lễ cũng là mô-đun riêng với hệ số lương lễ và lịch làm bù. Cả hai phải cấu hình trước khi tính công, vì bước tổng hợp sẽ ghép đơn nghỉ phép đã duyệt vào bảng công.

Báo cáo chấm công tách hẳn ra một nhóm URL riêng (`/BC_ChamCong/Index`), bao gồm các báo cáo theo dõi tình trạng chấm công, đi trễ, quên chấm, tăng ca, và thiết bị quét. Nhân viên có màn hình riêng xem bảng công và lịch làm việc của chính mình.

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| CC1 | Bảng công động | `/BangCongDong/Index` | Tải dữ liệu thô, tổng hợp, tính công, chốt công theo chu kỳ | [ ] |
| CC2 | Phân ca xếp lịch | `/QuanLyCa/Index` | Gán nhân viên vào ca làm việc từng ngày | [ ] |
| CC3 | Thiết lập ca | `/ThietLapCa/Index` | Định nghĩa ca, kết nối máy chấm công, định vị GPS | [ ] |
| CC4 | Quản lý phép năm | `/PhepNamDong/Index` | Theo dõi quỹ phép, kết chuyển, phép bù tăng ca | [ ] |
| CC5 | Quản lý ngày nghỉ lễ | `/NghiLe/Index` | Khai ngày lễ, hệ số lương lễ, lịch làm bù | [ ] |
| CC6 | Cấu hình bảng công | `/CauHinhHeThong/Index` — mục bảng công | Cấu hình chu kỳ, từ khóa cột, pháp nhân cho bảng công | [ ] |
| CC7 | Cấu hình loại chấm công | `/CauHinhHeThong/Index` — mục loại chấm công | Gán phương thức chấm công cho từng nhân viên | [ ] |

---

## CC1. Bảng công động

| | |
|---|---|
| Đường dẫn | `/BangCongDong/Index` |
| Dùng để làm gì | Tải dữ liệu thô từ máy chấm công, tổng hợp thành bảng công, tính ngày công và giờ tăng ca, chốt công cuối kỳ |
| Ai dùng | Phỏng đoán: bộ phận Nhân sự hoặc Hành chính phụ trách chấm công |
| Mình có chưa | [ ] |

**Cấu trúc màn hình** — mười một thẻ:
- Bảng tổng hợp công
- Bảng công tăng ca
- Bảng công chi tiết
- Dữ liệu chấm công
- Lịch sử chốt công
- Lịch sử phản ánh
- Các lỗi dữ liệu
- Tính công
- Chốt công
- Ứng công
- Cấu hình bảng công

**Trường dữ liệu**

Không có trường raw quan sát được trực tiếp ở màn hình này ngoài cấu trúc thẻ. Phỏng đoán: mỗi bản ghi bảng công có `maNhanVien`, `thang`, `nam`, `ngayCong`, `gioTangCa`, `diTre`, `veSom`, trạng thái chốt.

**Luồng chạy**

Bước 1 — Tải dữ liệu: kéo dữ liệu thô từ máy chấm công vào hệ thống.
Bước 2 — Tổng hợp: ghép dữ liệu thô với ca làm việc và các đơn từ đã duyệt (nghỉ phép, tăng ca...).
Bước 3 — Tính công: ra số ngày công, giờ tăng ca, đi trễ, về sớm.
Sau đó: Chốt công — khóa bảng. Mở lại phải thực hiện thủ công và được ghi vào Lịch sử chốt công.

**Chỗ đáng chú ý:**

Thẻ "Các lỗi dữ liệu" là một màn hình riêng xử lý dữ liệu bẩn từ máy chấm công: quẹt thiếu, quẹt trùng, người không có trong hệ thống. Không có màn hình này thì mỗi kỳ tính công phải làm thủ công bằng Excel.

Thẻ "Lịch sử phản ánh" cho phép nhân viên khiếu nại số công ngay trong hệ thống, có vết — không cần qua email hay giấy tờ riêng.

Ba bước tách rời nhau, không gộp thành một nút, vì mỗi bước có thể hỏng vì lý do khác nhau và cần chạy lại riêng.

Dữ liệu thô (thẻ "Dữ liệu chấm công") và bảng công là hai bảng riêng: dữ liệu thô không sửa được; bảng công sau khi tổng hợp thì sửa được. Đây không phải một bảng có cột trạng thái.

Mã chấm công (`maChamCong`) khác mã nhân viên (`maNhanVien`). Dữ liệu thô từ máy chỉ có `maChamCong`; bước tổng hợp phải ánh xạ sang `maNhanVien` để ghép.

---

## CC2. Phân ca xếp lịch

| | |
|---|---|
| Đường dẫn | `/QuanLyCa/Index` |
| Dùng để làm gì | Gán ca làm việc cho từng nhân viên hoặc phòng ban theo ngày; xem lịch làm việc; theo dõi nhân viên chưa có lịch |
| Ai dùng | Phỏng đoán: quản lý trực tiếp hoặc Hành chính |
| Mình có chưa | [ ] |

**Cấu trúc màn hình** — các thẻ và thao tác:
- Ca làm việc
- Xếp lịch
- Lịch làm việc
- Lịch sử phân ca
- Nhân viên chưa phân ca
- Export
- Cập nhật lịch làm việc
- Export xóa lịch theo ngày
- Import xóa lịch theo ngày

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `tenPhanCa` | Tên lần phân ca | |
| `batDau` | Ngày bắt đầu áp dụng | |
| `ketThuc` | Ngày kết thúc áp dụng | |
| `lsPhongBanApDung` | Danh sách phòng ban áp dụng | Phỏng đoán: mảng ID phòng ban |
| `xacNhan` | Trạng thái xác nhận phân ca | |
| `phanCaSearch-danhsachnhanvienphanca` | Ô tìm kiếm nhân viên trong màn hình phân ca | Tên trường là ID của input |
| `idImport` | ID bản import | |
| `ngayBatDau` | Ngày bắt đầu lịch | |
| `ngayKetThuc` | Ngày kết thúc lịch | |
| `tenCa` | Tên ca làm việc | |
| `thang-lichlamviec` | Tháng xem lịch làm việc | Tên trường là ID của input |
| `nam-lichlamviec` | Năm xem lịch làm việc | Tên trường là ID của input |
| `calamviec` | Ca làm việc được chọn | |
| `thangCapNhat` | Tháng cập nhật lịch | |
| `namCapNhat` | Năm cập nhật lịch | |
| `ngayDong` | Ngày đóng/xóa lịch | |
| `FileUpload` | File import phân ca | |

---

## CC3. Thiết lập ca

| | |
|---|---|
| Đường dẫn | `/ThietLapCa/Index` |
| Dùng để làm gì | Định nghĩa ca làm việc, kết nối máy chấm công vật lý, thiết lập ca định mức, cấu hình máy định vị GPS |
| Ai dùng | Phỏng đoán: quản trị hệ thống HRM hoặc Hành chính cấp cao |
| Mình có chưa | [ ] |

**Cấu trúc màn hình** — bốn thẻ:
- Ca làm việc
- Máy chấm công
- Thiết lập ca định mức
- Máy định vị GPS

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `loaiMayCham` | Loại máy chấm công | Quan sát được ở thẻ Máy chấm công |

Thẻ Máy định vị GPS có bốn thông tin: vĩ độ, kinh độ, bán kính, địa chỉ IP. Các tên trường cụ thể không quan sát được từ dữ liệu thô.

---

## CC4. Quản lý phép năm

| | |
|---|---|
| Đường dẫn | `/PhepNamDong/Index` |
| Dùng để làm gì | Theo dõi quỹ phép từng nhân viên trong năm, kết chuyển phép và tăng ca sang năm mới, cấu hình và tính phép bù |
| Ai dùng | Phỏng đoán: Nhân sự |
| Mình có chưa | [ ] |

**Cấu trúc màn hình** — các thẻ:
- Phép năm qui định
- Phép bù tăng ca
- Báo cáo loại nghỉ
- Cấu hình ứng phép
- Tính phép
- Export
- Import

Các nút thao tác hàng loạt: Reset phép năm, Kết chuyển phép năm, Reset tăng ca, Kết chuyển tăng ca, Cấu hình tăng ca, Thêm.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `soNgayPhepConLaiNamCu` | Số ngày phép còn lại của năm trước | |
| `soNgayPhepTonDuocDuyet` | Số ngày phép tồn được duyệt để chuyển sang năm mới | |
| `soNgayPhepQuiDinh` | Số ngày phép theo quy định năm hiện tại, thường 12 | |
| `soNgayPhepThamNien` | Số ngày phép cộng thêm theo thâm niên | |
| `phepDaNghiTruocHeThong` | Số ngày đã nghỉ trước khi dùng phần mềm | Trường phục vụ di dân dữ liệu; không có trường này thì số phép sai ngay tháng đầu đưa vào sử dụng |
| `tongNgayDaNghi` | Tổng số ngày đã nghỉ trong năm | |
| `soNgayPhepDacBiet` | Số ngày phép đặc biệt | |
| `soNgayPhepNamHienTai` | Số ngày phép còn lại năm hiện tại | |

**Chỗ đáng chú ý:**

`phepDaNghiTruocHeThong` tồn tại để xử lý trường hợp công ty bắt đầu dùng phần mềm giữa năm. Không có trường này thì số phép hiển thị sai ngay tháng đầu triển khai.

---

## CC5. Quản lý ngày nghỉ lễ

| | |
|---|---|
| Đường dẫn | `/NghiLe/Index` |
| Dùng để làm gì | Khai báo ngày lễ và áp dụng theo từng nhóm nhân viên; cấu hình hệ số lương cho ngày lễ; quản lý lịch làm bù |
| Ai dùng | Phỏng đoán: Nhân sự hoặc quản trị hệ thống |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Màn hình khai báo ngày lễ có các tiêu chí áp dụng: nhân viên, phòng ban, chức danh, cấp bậc, ca. Bộ lọc bổ sung: giới tính, tôn giáo, người trong nước hay ngoài nước. Mỗi ngày lễ có hệ số lương riêng. Kèm theo là phần Lịch làm bù.

**Trường dữ liệu**

Các tên trường cụ thể không quan sát được từ dữ liệu thô. Phỏng đoán: có `tenNghiLe`, `ngayLe`, `heSoLuong`, và danh sách đối tượng áp dụng.

---

## CC6. Cấu hình bảng công

| | |
|---|---|
| Đường dẫn | `/CauHinhHeThong/Index` — mục "Cấu hình bảng công" |
| Dùng để làm gì | Định nghĩa cấu trúc bảng công (cột, chu kỳ, pháp nhân), khai từ khóa cột bảng công |
| Ai dùng | Phỏng đoán: quản trị hệ thống HRM |
| Mình có chưa | [ ] |

**Cấu trúc màn hình** — bốn thẻ:
- CẤU HÌNH BẢNG CÔNG
- TỪ KHÓA BẢNG CÔNG
- CẤU HÌNH CHU KỲ
- CẤU HÌNH BẢNG CÔNG CHI TIẾT

Danh sách cấu hình có các cột: STT, TÊN BẢNG CÔNG, NGƯỜI LẬP, NGƯỜI CẬP NHẬT, NGÀY CẬP NHẬT, THAO TÁC. Bản demo có một bản ghi tên "Bảng công động demo".

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `qSearch-cauhinhbangcong` | Ô tìm kiếm cấu hình bảng công | ID của input |
| `pageSize-cauhinhtukhoa` | Số dòng mỗi trang ở thẻ từ khóa | ID của input |
| `qSearch-cauhinhtukhoa` | Ô tìm kiếm từ khóa bảng công | ID của input |
| `thang-cauhinhchuky` | Tháng cấu hình chu kỳ | |
| `nam-cauhinhchuky` | Năm cấu hình chu kỳ | |
| `maPhapNhan-cauhinhchuky` | Mã pháp nhân cho chu kỳ | |
| `ngayBatDau` | Ngày bắt đầu chu kỳ | |
| `ngayKetThuc` | Ngày kết thúc chu kỳ | |
| `thangBatDau` | Tháng bắt đầu | |
| `namBatDau` | Năm bắt đầu | |
| `namKetThuc` | Năm kết thúc | |
| `namChuKyLayTheo` | Năm làm gốc để lấy theo chu kỳ | |
| `maPhapNhan` | Mã pháp nhân | |
| `qSearch-bangcongchitietcauhinh` | Ô tìm kiếm trong thẻ cấu hình chi tiết | ID của input |

**Chỗ đáng chú ý:**

Thẻ TỪ KHÓA BẢNG CÔNG cho thấy bảng công cũng theo lối "khai cột bằng từ khóa" — tương tự bảng lương. Cấu trúc cột không cố định mà do người quản trị khai báo; điều này tạo linh hoạt nhưng cũng tăng độ phức tạp khi triển khai.

---

## CC7. Cấu hình loại chấm công

| | |
|---|---|
| Đường dẫn | `/CauHinhHeThong/Index` — mục "Cấu hình loại chấm công" |
| Dùng để làm gì | Gán phương thức chấm công được phép cho từng nhân viên; bật/tắt từng kênh: GPS, Wifi, máy chấm công, Face ID, app |
| Ai dùng | Phỏng đoán: quản trị hệ thống HRM |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Bảng một dòng một nhân viên. Cột thông tin: STT, MÃ NHÂN VIÊN, TÊN NHÂN VIÊN, CHỨC DANH, PHÒNG BAN. Cột cấu hình: GPS, WIFI, MÁY CHẤM CÔNG, CC HỘ, CC ĐƯỢC NHIỀU LẦN, KHÔNG THEO QĐ GIỜ, KHÔNG RÀNG BUỘC VỊ TRÍ, CẢNH BÁO VƯỢT QUÁ BK, FACE ID, CC QUA APP, CHECK THIẾT BỊ KHI CHẤM CÔNG.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `chamCongGPS` | Cho phép chấm công qua GPS | |
| `chamCongWifi` | Cho phép chấm công qua Wifi | |
| `chamCongMay` | Cho phép chấm công qua máy vật lý | |
| `chamCongHo` | Cho phép chấm công hộ | |
| `chamCongDuocNhieuLan` | Cho phép chấm nhiều lần trong ngày | |
| `quetKhongTheoKhungGioQuyDinh` | Cho phép quẹt ngoài khung giờ quy định | |
| `quetLinhHoatTheoViTriLamViec` | Không ràng buộc vị trí khi quẹt | |
| `canhBaoVuotBK` | Cảnh báo khi quẹt vượt quá bán kính | |
| `faceID` | Cho phép chấm công bằng Face ID | |
| `chamCongQuaAPP` | Cho phép chấm công qua app di động | |
| `checkThietBiChamCong` | Kiểm tra thiết bị khi chấm công | |
| `checkAllGPS` | Chọn tất cả cột GPS | Ô chọn hàng loạt |
| `checkAllWifi` | Chọn tất cả cột Wifi | Ô chọn hàng loạt |
| `checkAllVT` | Chọn tất cả cột vị trí | Ô chọn hàng loạt |
| `checkAllCCH` | Chọn tất cả cột chấm công hộ | Ô chọn hàng loạt |
| `checkAllCCNL` | Chọn tất cả cột chấm nhiều lần | Ô chọn hàng loạt |
| `checkAllKG` | Chọn tất cả cột không theo khung giờ | Ô chọn hàng loạt |
| `checkAllRB` | Chọn tất cả cột không ràng buộc | Ô chọn hàng loạt |
| `checkAllCB` | Chọn tất cả cột cảnh báo | Ô chọn hàng loạt |

---

## Báo cáo và màn hình cá nhân liên quan

Nhóm báo cáo tại `/BC_ChamCong/Index` gồm:
- Theo dõi nhân viên đi làm
- Theo dõi tình trạng chấm công
- Lịch làm việc tổng hợp
- BC Số giờ đi trễ
- BC Số lần quên chấm công
- BC Số giờ tăng ca
- Báo cáo thiết bị quét

Màn hình cá nhân:
- `/LichSuChamCong/BangCongCaNhan` — nhân viên xem bảng công của chính mình
- `/LichSuChamCong/LichLamViec` — nhân viên xem lịch làm việc của chính mình

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `du_lieu_cham_cong` | `maChamCong`, `thoiGianQuet`, `loaiQuet` | Khá |
| `bang_cong_dong` | `maNhanVien`, `thang`, `nam`, `ngayCong`, `gioTangCa`, `diTre`, `veSom`, `trangThai` | Khá |
| `ca_lam_viec` | `maCa`, `tenCa`, `gioBatDau`, `gioKetThuc` | Chắc |
| `phan_ca` | `maNhanVien`, `maCa`, `ngayApDung`, `ngayKetThuc` | Chắc |
| `phep_nam` | `maNhanVien`, `nam`, `soNgayPhepQuiDinh`, `soNgayPhepThamNien`, `phepDaNghiTruocHeThong`, `tongNgayDaNghi`, `soNgayPhepNamHienTai` | Chắc |
| `lich_su_chot_cong` | `maBangCong`, `thoiGianChot`, `nguoiChot`, `thoiGianMoLai`, `nguoiMoLai` | Khá |
| `nghi_le` | `tenNghiLe`, `ngayLe`, `heSoLuong`, `doiTuongApDung` | Đoán |
| `loai_cham_cong_nhanvien` | `maNhanVien`, `chamCongGPS`, `chamCongWifi`, `chamCongMay`, `faceID`, `chamCongQuaAPP` | Chắc |
| `may_cham_cong` | `maMay`, `loaiMayCham`, `viDo`, `kinhDo`, `banKinh` | Khá |

Ánh xạ `maChamCong` sang `maNhanVien` phải có bảng riêng — phỏng đoán tên `cau_hinh_may_cham_cong_nhanvien` hoặc cột trên bảng nhân viên. Không có ánh xạ này thì bước tổng hợp không biết bản ghi chấm công thuộc ai.

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| CC1. Bảng công động | Lấy sau | Cần CC2+CC3 trước; là lõi tính công nhưng không chạy được nếu chưa có ca và phân ca | Thiết kế lại màn hình Các lỗi dữ liệu cho phù hợp thiết bị thực tế của công ty |
| CC2. Phân ca xếp lịch | Lấy sau | Cần CC3 trước; phức tạp vì có import/export và xóa lịch theo ngày | Cân nhắc bỏ Export xóa lịch nếu không cần |
| CC3. Thiết lập ca | Lấy sau | Nền tảng bắt buộc; phải làm trước CC1 và CC2 | Chỉ lấy GPS nếu có nhân viên làm việc ngoài văn phòng |
| CC4. Quản lý phép năm | Lấy sau | Quan trọng nhưng cần dữ liệu nhân sự đầy đủ trước | Giữ nguyên `phepDaNghiTruocHeThong` vì chắc chắn sẽ triển khai giữa năm |
| CC5. Quản lý ngày nghỉ lễ | Lấy sau | Ảnh hưởng trực tiếp đến bảng công; cần cấu hình trước mỗi năm | Hệ số lương lễ cần kiểm tra lại với quy chế lương nội bộ |
| CC6. Cấu hình bảng công | Lấy sau | Cơ chế từ khóa cột linh hoạt nhưng phức tạp để triển khai | Có thể đơn giản hóa: cột bảng công cố định thay vì từ khóa động |
| CC7. Cấu hình loại chấm công | Lấy ngay | Không có bảng cấu hình này thì không biết nhân viên nào được dùng kênh nào | Bật/tắt theo nhóm là đủ nếu không cần cấu hình từng người |
