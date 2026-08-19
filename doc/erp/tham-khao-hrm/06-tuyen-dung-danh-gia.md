# TUYỂN DỤNG VÀ ĐÁNH GIÁ

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 10 |

## Tóm tắt mục này

Mục này gồm hai khối liên tiếp: Tuyển dụng (TD1–TD6) và Đánh giá (DG1–DG4).

Khối tuyển dụng đi từ lập định biên (TD1) → tạo nhu cầu tuyển (TD2) → thu thập hồ sơ ứng viên (TD4) → ra quyết định nhận việc (TD5). Kết quả cuối cùng là ứng viên chuyển thành nhân viên. Phỏng đoán: hệ thống tự động chuyển dữ liệu ứng viên sang hồ sơ nhân viên vì tập trường của hai đối tượng trùng nhau và dùng cùng quy ước đặt tên.

Khối đánh giá bắt đầu khi nhân viên đã có trong hệ thống. Tiêu chí KPI (DG1) được gắn vào kế hoạch đánh giá (DG2) cùng với danh sách nhân viên và hội đồng đánh giá. Từng phiếu đánh giá (DG3) được thực hiện trong kỳ, kết quả tổng hợp tại DG4.

Hai điểm nối giữa đánh giá và các mô-đun khác: (1) kết quả đánh giá nối thẳng sang kỳ lương qua `kiLuongThang` và `kiLuongNam`; (2) điểm và xếp loại hiển thị trên màn hình sơ đồ tổ chức.

Cả hai khối có 9 loại quy trình duyệt riêng trong danh sách 88 loại của hệ thống.

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| TD1 | Định biên nhân sự | `/KeHoachNhanSu/Index` | Lập số lượng cần tuyển theo vị trí và năm | [ ] Chưa có |
| TD2 | Nhu cầu tuyển dụng | `/NhuCauTuyenDung/Index` | Tạo đợt tuyển, đăng tin công khai | [ ] Chưa có |
| TD3 | Thanh toán chi phí tuyển dụng | `/ThanhToanChiPhiTuyenDung/Index` | Theo dõi và thanh toán chi phí đăng tuyển | [ ] Chưa có |
| TD4 | Hồ sơ ứng viên | `/UngVien/Index` | Quản lý hồ sơ, lịch hẹn phỏng vấn, KanBan | [ ] Chưa có |
| TD5 | Quyết định nhận việc | `/PhieuQuyetDinhNhanViec/Index` | Ghi điều kiện nhận việc và hai bộ lương | [ ] Chưa có |
| TD6 | Cấu hình tuyển dụng | `/CauHinhTuyenDung/Index` | Bộ câu hỏi, mail tự động, mẫu in, mail server | [ ] Chưa có |
| DG1 | Tiêu chí đánh giá | `/TieuChi/Index` | Khai báo chỉ tiêu KPI | [ ] Chưa có |
| DG2 | Kế hoạch đánh giá | `/KeHoachDanhGia/Index` | Tạo kỳ đánh giá, gắn tiêu chí và nhân sự | [ ] Chưa có |
| DG3 | Phiếu đánh giá | `/PhieuDanhGia/Index` | Thực hiện và theo dõi từng phiếu | [ ] Chưa có |
| DG4 | Kết quả đánh giá | `/KetQuaDanhGia/Index` | Tổng hợp điểm, xếp loại, nối sang kỳ lương | [ ] Chưa có |

---

## Phần 1 — Tuyển dụng

---

## TD1. Định biên nhân sự

| | |
|---|---|
| Đường dẫn | `/KeHoachNhanSu/Index` |
| Dùng để làm gì | Lập kế hoạch số lượng nhân sự cần tuyển theo từng vị trí và năm; cấu hình nhắc nhở tự động qua email và ứng dụng |
| Ai dùng | phỏng đoán — phòng Nhân sự lập; ban lãnh đạo phê duyệt |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Index có hai thẻ: Định biên nhân sự và Kế hoạch định biên nhân sự. Có nút Import và Export. Màn hình tích hợp sẵn phần soạn nội dung thông báo qua email và ứng dụng, chia thành hai nhóm: thông báo gửi kèm dữ liệu và thông báo nhắc trước ngày.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maTrangThai-khnhansu` | Trạng thái bản kế hoạch nhân sự | Hậu tố `-khnhansu` phân biệt với trường cùng tên ở thẻ khác |
| `loaiDinhBien-khnhansu` | Loại định biên | phỏng đoán: tăng biên chế / thay thế / vị trí mới |
| `nam-khnhansu` | Năm kế hoạch nhân sự | |
| `nam-khtonghop` | Năm ở thẻ tổng hợp | Thẻ tổng hợp tách biệt với thẻ nhân sự |
| `loaiDinhBien-tonghop` | Loại định biên ở thẻ tổng hợp | |
| `maChucDanh-khtonghop` | Chức danh ở thẻ tổng hợp | |
| `tieuDeEmailData` | Tiêu đề email gửi kèm dữ liệu | Nhóm thông báo gửi dữ liệu |
| `noiDungEmailData` | Nội dung email gửi kèm dữ liệu | |
| `tieuDeAppData` | Tiêu đề thông báo ứng dụng gửi kèm dữ liệu | |
| `noiDungAppData` | Nội dung thông báo ứng dụng gửi kèm dữ liệu | |
| `nguoiLienQuan` | Người liên quan nhận thông báo | |
| `quaEmail` | Gửi qua email | |
| `quaApp` | Gửi qua ứng dụng | |
| `truocBaoNhieuNgayCT` | Số ngày nhắc trước so với ngày chỉ tiêu | Nhóm thông báo nhắc trước |
| `tieuDeEmail` | Tiêu đề email nhắc | |
| `noiDungEmail` | Nội dung email nhắc | |
| `tieuDeApp` | Tiêu đề thông báo ứng dụng nhắc | |
| `noiDungApp` | Nội dung thông báo ứng dụng nhắc | |
| `FileUpload` | File đính kèm | |

**Chỗ đáng chú ý:** Màn hình tách hai loại thông báo: gửi dữ liệu (`EmailData`/`AppData`) và nhắc trước ngày (`truocBaoNhieuNgayCT`). Tức có thể lên lịch nhắc tự động cho người liên quan mà không cần cấu hình bên ngoài.

---

## TD2. Nhu cầu tuyển dụng

| | |
|---|---|
| Đường dẫn | `/NhuCauTuyenDung/Index` — tạo mới: `/NhuCauTuyenDung/Create` |
| Dùng để làm gì | Tạo từng đợt tuyển dụng cụ thể, quản lý trạng thái ứng viên qua KanBan, đăng tin công khai lên landing page |
| Ai dùng | phỏng đoán — phòng Nhân sự tạo; quản lý phê duyệt |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Index có chế độ xem bảng danh sách và KanBan. Có phần cấu hình landing page tuyển dụng công khai. Form tạo mới bao gồm thông tin mô tả vị trí, yêu cầu ứng viên, và thông tin lương.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `tenNhuCau` | Tên đợt tuyển dụng | |
| `lyDo` | Lý do tuyển | |
| `maCongTy` | Công ty | |
| `maViTriTuyenDung` | Vị trí tuyển dụng | |
| `maChucDanh` | Chức danh | |
| `soLuongNhanSu` | Số lượng nhân sự hiện tại | phỏng đoán |
| `soLuongDinhBien` | Số lượng định biên | liên kết ngược về TD1 |
| `soLuong` | Số lượng cần tuyển | |
| `maHinhThuc` | Hình thức làm việc | phỏng đoán: toàn thời gian / bán thời gian |
| `tuyenTu` | Ngày bắt đầu tuyển | |
| `tuyenDen` | Ngày kết thúc tuyển | |
| `ngayBatDauLam` | Ngày bắt đầu làm việc dự kiến | |
| `isPublish` | Đăng lên landing page công khai | |
| `lsNhanVienBanGiao` | Danh sách nhân viên bàn giao | |
| `noiLamViec` | Nơi làm việc | |
| `mucDichTuyen` | Mục đích tuyển | |
| `moTaCongViec` | Mô tả công việc | |
| `yeuCauCongViec` | Yêu cầu công việc | |
| `quyenLoi` | Quyền lợi | |
| `maTrinhDo` | Trình độ học vấn yêu cầu | |
| `maChuyenNganh` | Chuyên ngành yêu cầu | |
| `maKinhNghiem` | Kinh nghiệm yêu cầu | |
| `gioiTinh` | Giới tính yêu cầu | |
| `chiPhiDuTru` | Chi phí tuyển dụng dự trù | |
| `hinhThucLuong` | Hình thức trả lương | |
| `donViTienTe` | Đơn vị tiền tệ | |
| `mucLuongTu` | Mức lương từ | |
| `mucLuongDen` | Mức lương đến | |
| `tuoiTu` | Tuổi tối thiểu | |
| `tuoiDen` | Tuổi tối đa | |
| `chieuCao` | Chiều cao tối thiểu | |
| `chieuCaoDen` | Chiều cao tối đa | |
| `canNang` | Cân nặng tối thiểu | |
| `canNangDen` | Cân nặng tối đa | |
| `maNangLuc` | Năng lực yêu cầu | |
| `thangDiem` | Thang điểm đánh giá năng lực | |
| `loaiThoiGian` | Loại thời gian | phỏng đoán: hữu hạn / không xác định |
| `soDiem` | Số điểm năng lực yêu cầu | |
| `maTrangThaiUV` | Trạng thái ứng viên mặc định khi tạo hồ sơ | phỏng đoán |
| `heSo` | Hệ số | phỏng đoán mục đích cụ thể |
| `chooseAavatar` | Ảnh đại diện cho tin đăng | Lỗi đánh máy trong tên trường: `Aavatar` |
| `FileUpload` | File đính kèm | |
| `filePDF` | File PDF mô tả vị trí | |

**Chỗ đáng chú ý:** `isPublish` cho phép đăng tin tuyển dụng ra ngoài Internet từ màn hình này mà không cần hệ thống quản lý nội dung riêng. Trường `soLuongDinhBien` liên kết trực tiếp về số lượng định biên từ TD1 — người tạo nhu cầu thấy ngay đang tuyển bao nhiêu so với kế hoạch.

---

## TD3. Thanh toán chi phí tuyển dụng

| | |
|---|---|
| Đường dẫn | `/ThanhToanChiPhiTuyenDung/Index` |
| Dùng để làm gì | Theo dõi và thanh toán chi phí đăng tuyển theo chiến dịch và nhà tuyển dụng, liên kết với từng nhu cầu tuyển dụng |
| Ai dùng | phỏng đoán — phòng Nhân sự tạo phiếu; kế toán duyệt |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Bảng danh sách phiếu thanh toán. Dữ liệu khảo sát không ghi nhận URL tạo mới.

**Cột bảng danh sách**

| Cột | Ghi chú |
|---|---|
| Số phiếu | |
| Trạng thái | |
| Người lập | |
| Ngày lập | |
| Gói tin TD | Gói tin tuyển dụng |
| Nhà tuyển dụng | Đơn vị đăng tuyển |
| Nhu cầu | Liên kết với TD2 |
| Vị trí | |
| Chi phí | |
| Từ ngày | |
| Đến ngày | |
| Ghi chú | |

**Trường lọc**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `viTriTuyenDung` | Vị trí tuyển dụng | |
| `nhaTuyenDung` | Nhà tuyển dụng | |
| `maTrangThai` | Trạng thái phiếu | |
| `qSearch` | Tìm kiếm nhanh | |

**Chỗ đáng chú ý:** Cột "Nhu cầu" trong bảng cho thấy phiếu thanh toán liên kết trực tiếp về một nhu cầu tuyển dụng cụ thể ở TD2 — chi phí đăng tuyển có thể quy về từng đợt tuyển.

---

## TD4. Hồ sơ ứng viên

| | |
|---|---|
| Đường dẫn | `/UngVien/Index` — tạo mới: `/UngVien/Create` |
| Dùng để làm gì | Lưu và quản lý hồ sơ ứng viên; theo dõi tiến trình qua KanBan; đặt lịch hẹn phỏng vấn; xem kết quả kiểm tra |
| Ai dùng | phỏng đoán — phòng Nhân sự và người phỏng vấn |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Index có các thẻ: Hồ sơ ứng viên, KanBan, Lịch hẹn, Đồng bộ ứng viên, Kết quả kiểm tra. Có nút "Thêm ứng viên từ CV".

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maNhuCau` | Nhu cầu tuyển dụng ứng viên ứng tuyển | liên kết với TD2 |
| `nguonDangTuyen` | Nguồn ứng viên | phỏng đoán: website / giới thiệu / sàn việc làm |
| `tenUngVien` | Tên ứng viên | |
| `gioiTinh` | Giới tính | |
| `danToc` | Dân tộc | |
| `viTriTuyenDung` | Vị trí ứng tuyển | |
| `ngayDangKy` | Ngày nộp hồ sơ | |
| `soDienThoai` | Số điện thoại | |
| `eMail` | Email | |
| `maChucDanh` | Chức danh | |
| `ngaySinh` | Ngày sinh | |
| `noiSinh` | Nơi sinh | |
| `soCMND` | Số CMND/CCCD | |
| `noiCapCMND` | Nơi cấp | |
| `ngayCapCMND` | Ngày cấp | |
| `maTrangThai` | Trạng thái ứng viên | phỏng đoán: mới / phỏng vấn / trúng tuyển / loại |
| `trinhDo` | Trình độ học vấn | |
| `chuyenNganh` | Chuyên ngành | |
| `quocTich` | Quốc tịch | |
| `tonGiao` | Tôn giáo | |
| `tenNhanVien` | phỏng đoán — nhân viên phụ trách hồ sơ | tên trường không rõ nghĩa trong dữ liệu thô |
| `diaChiThuongTru` | Địa chỉ thường trú | |
| `diaChiTamTru` | Địa chỉ tạm trú | |
| `ghiChu` | Ghi chú | |
| `FileUpload` | File đính kèm (CV, hồ sơ) | |

**Chỗ đáng chú ý:** Tập trường của ứng viên trùng với hồ sơ nhân viên và dùng cùng quy ước đặt tên — phỏng đoán hệ thống tự chuyển dữ liệu sang hồ sơ nhân viên khi ứng viên được nhận, không cần nhập lại. Thẻ "Đồng bộ ứng viên" và nút "Thêm ứng viên từ CV" cho thấy có tích hợp thêm nguồn từ ngoài hệ thống.

---

## TD5. Quyết định nhận việc

| | |
|---|---|
| Đường dẫn | `/PhieuQuyetDinhNhanViec/Index` — tạo mới: `/PhieuQuyetDinhNhanViec/Create` |
| Dùng để làm gì | Lập phiếu ghi điều kiện nhận việc gồm cả lương thử việc và lương chính thức trong một chứng từ |
| Ai dùng | phỏng đoán — phòng Nhân sự lập; ban giám đốc ký |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Form tạo mới kèm bảng con phụ cấp. Có trường `filePDF` cho phép đính kèm quyết định dạng PDF.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `soQuyetDinh` | Số quyết định | |
| `ngayBatDauNhanViec` | Ngày bắt đầu nhận việc | |
| `ngayKetThucThuViec` | Ngày kết thúc thử việc | |
| `noiLamViec` | Nơi làm việc | |
| `tenUngVien` | Tên ứng viên | |
| `nguoiQuanLy` | Người quản lý trực tiếp | |
| `maChucDanh` | Chức danh | |
| `ghiChu` | Ghi chú | |
| `thangTinhLuong` | Tháng bắt đầu tính lương | |
| `luongNhanViec` | Lương khi nhận việc | phỏng đoán: có thể là tổng lương gộp |
| `luongCBThuViec` | Lương cơ bản thử việc | |
| `khoanBoSungLuongThuViec` | Khoản bổ sung lương thử việc | |
| `maLoaiHopDong` | Loại hợp đồng lao động | |
| `luongChinhThuc` | Lương chính thức | phỏng đoán: có thể là tổng lương gộp |
| `luongCBChinhThuc` | Lương cơ bản chính thức | |
| `khoanBoSungLuongChinhThuc` | Khoản bổ sung lương chính thức | |
| `filePDF` | File PDF quyết định | |
| `maPhuCap` | Mã phụ cấp (bảng con) | |
| `soTien` | Số tiền phụ cấp (bảng con) | |
| `ghiChuPhuCap` | Ghi chú phụ cấp (bảng con) | |

**Chỗ đáng chú ý:** Một phiếu ghi cả hai bộ lương — thử việc và chính thức — nên người duyệt thấy toàn bộ cam kết lương ngay từ lần ký đầu. Bảng con phụ cấp nằm trong phiếu này, không phải cấu hình riêng.

---

## TD6. Cấu hình tuyển dụng

| | |
|---|---|
| Đường dẫn | `/CauHinhTuyenDung/Index` |
| Dùng để làm gì | Thiết lập bộ câu hỏi đánh giá ứng viên, cấu hình mail tự động theo giai đoạn tuyển dụng, mẫu in, mail server, và tùy chọn form |
| Ai dùng | phỏng đoán — quản trị hệ thống hoặc trưởng phòng Nhân sự |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Năm thẻ: Bộ câu hỏi đánh giá, Cấu hình mail tự động, Cấu hình mẫu in, Mail server, Option form.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `viTriTuyenDung-bocauhoi` | Lọc bộ câu hỏi theo vị trí tuyển dụng | |
| `maMenu-mauin` | Lọc mẫu in theo menu | |

Dữ liệu khảo sát chỉ ghi nhận hai trường lọc; nội dung từng thẻ không được liệt kê chi tiết.

**Chỗ đáng chú ý:** Bộ câu hỏi lọc theo `viTriTuyenDung` — phỏng đoán mỗi vị trí có bộ câu hỏi riêng. Mail server được cấu hình tại đây; không rõ có tách biệt với mail server chung của hệ thống hay không.

---

## BC. Báo cáo tuyển dụng

| | |
|---|---|
| Đường dẫn | `/BC_TuyenDung/Index` |
| Dùng để làm gì | Cung cấp 9 loại báo cáo và biểu đồ về tình trạng, tiến độ, ứng viên, vị trí, và hiệu quả nguồn tuyển |
| Mình có chưa | [ ] Chưa có |

| # | Tên báo cáo |
|---|---|
| 1 | BC Tình trạng tuyển dụng |
| 2 | Biểu đồ tình trạng tuyển dụng |
| 3 | Lịch sử quá trình tuyển dụng |
| 4 | BC Trạng thái và tiến độ |
| 5 | BC Trạng thái ứng viên |
| 6 | BC Lịch hẹn ứng viên |
| 7 | BC Vị trí tuyển dụng |
| 8 | BC Hiệu quả nguồn tuyển dụng |
| 9 | BC Nguồn tuyển dụng |

---

## Phần 2 — Đánh giá

---

## DG1. Tiêu chí đánh giá

| | |
|---|---|
| Đường dẫn | `/TieuChi/Index` |
| Dùng để làm gì | Khai báo và quản lý danh sách chỉ tiêu KPI; xem kết quả từng tiêu chí |
| Ai dùng | phỏng đoán — phòng Nhân sự hoặc trưởng bộ phận |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Hai thẻ: Danh sách chỉ tiêu KPI, Kết quả tiêu chí. Có Import và Export. Màn hình tải theo tham số `maloaiPhieu=KPI`.

**Trường dữ liệu**

Dữ liệu khảo sát không liệt kê trường cụ thể của màn hình này. Các trường liên quan thu thập được từ màn hình DG2:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `idTieuChi` | Mã tiêu chí | phỏng đoán là khóa chính |
| `maTuKhoaCT` | Từ khóa tiêu chí | phỏng đoán dùng trong công thức tính điểm |
| `heSoTieuChi` | Trọng số tiêu chí | |

**Chỗ đáng chú ý:** Tham số `maloaiPhieu=KPI` trên URL gợi ý màn hình này dùng chung cho nhiều loại phiếu đánh giá, không chỉ KPI. Cơ chế "Từ khóa" và "Công thức tính điểm" ở cột bảng tiêu chí (thấy từ DG2) phỏng đoán dùng cùng lối thiết kế với bảng lương và bảng công.

---

## DG2. Kế hoạch đánh giá

| | |
|---|---|
| Đường dẫn | `/KeHoachDanhGia/Index` — tạo mới: `/KeHoachDanhGia/Create` |
| Dùng để làm gì | Tạo kỳ đánh giá, gắn tiêu chí KPI với trọng số, chỉ định nhân sự được đánh giá và hội đồng đánh giá, cấu hình quy tắc điểm và xếp loại |
| Ai dùng | phỏng đoán — phòng Nhân sự |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Sáu thẻ khi tạo mới: Thông tin chung, Tiêu chí đánh giá, Nhân sự nhận đánh giá, Hội đồng đánh giá, Thông tin, Cấu hình.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `tenPhieuDanhGia` | Tên kế hoạch đánh giá | |
| `lsNguoiPhuTrach` | Danh sách người phụ trách | |
| `kiDanhGiaMau` | Kỳ đánh giá mẫu | phỏng đoán: bản template để sao chép |
| `ngayLap` | Ngày lập kế hoạch | |
| `thangDiem` | Thang điểm | |
| `txtNgayBatDau` | Ngày bắt đầu thực hiện đánh giá | |
| `txtNgayKetThuc` | Ngày kết thúc thực hiện đánh giá | |
| `txtNgayBatDauKiDG` | Ngày bắt đầu của kỳ được đánh giá | phỏng đoán: kỳ công việc được xét, khác với kỳ nhập điểm |
| `txtNgayKetThucKiDG` | Ngày kết thúc của kỳ được đánh giá | |
| `kiLuongThang` | Kỳ lương tháng nối sang | kết quả đánh giá tác động tới lương tháng |
| `kiLuongNam` | Kỳ lương năm nối sang | kết quả đánh giá tác động tới lương năm |
| `kiDanhGia` | Mã kỳ đánh giá | |
| `dinhKi` | Định kỳ | phỏng đoán: tháng / quý / năm |
| `txtNgayDong` | Ngày đóng phiếu | |
| `loaiDanhGia` | Loại đánh giá | |
| `loaiDanhGiaXepLoai` | Loại xếp loại | |
| `ghiChu` | Ghi chú | |
| `giaTriTu` | Giá trị điểm từ (ngưỡng xếp loại) | phỏng đoán |
| `giaTriDen` | Giá trị điểm đến (ngưỡng xếp loại) | phỏng đoán |
| `loai` | Loại xếp loại tương ứng với ngưỡng điểm | |
| `tuDongDuyet` | Tự động duyệt phiếu | |
| `batBuocNhanXet` | Bắt buộc nhập nhận xét | |
| `choPhepDGKDiem` | Cho phép đánh giá không điểm | |
| `choPhepKhongDG` | Cho phép bỏ qua không đánh giá | |
| `choPhepThemTieuChi` | Cho phép người đánh giá thêm tiêu chí | |
| `choPhepSuaDiem` | Cho phép sửa điểm sau khi nhập | |
| `tongHeSoTieuChi` | Tổng hệ số tiêu chí | phỏng đoán: hệ thống kiểm tra tổng = 100% |
| `idTieuChi` | Tiêu chí gắn vào kế hoạch | |
| `maTuKhoaCT` | Từ khóa công thức tính điểm | |
| `heSoTieuChi` | Trọng số tiêu chí | |

**Cột bảng tiêu chí trong kế hoạch**

| Cột | Ghi chú |
|---|---|
| Tiêu chí | |
| Từ khóa | |
| Trọng số | |
| Chỉ tiêu | |
| Công thức tính điểm | |
| Thêm tiêu chí | |

**Cột bảng nhân sự nhận đánh giá**

| Cột | Ghi chú |
|---|---|
| Mã nhân viên | |
| Tên nhân viên | |
| Chức danh | |
| Phòng ban | |
| Cấp bậc chức danh | |
| Đối tượng | phỏng đoán: nhóm / phân loại nhân sự |
| Ngày bắt đầu | |
| Ngày kết thúc | |
| Thứ tự | |
| Hệ số | |
| Giá trị | |
| Tiêu đề | |

**Chỗ đáng chú ý:** `kiLuongThang` và `kiLuongNam` trong kế hoạch nối thẳng điểm đánh giá sang bảng lương — tức đánh giá không chỉ xếp loại mà ảnh hưởng trực tiếp tới lương tháng và năm. Cột "Công thức tính điểm" và "Từ khóa" phỏng đoán dùng cơ chế biến số giống bảng lương và bảng công.

---

## DG3. Phiếu đánh giá

| | |
|---|---|
| Đường dẫn | `/PhieuDanhGia/Index` |
| Dùng để làm gì | Thực hiện từng phiếu đánh giá trong kỳ; theo dõi phiếu chưa hoàn thành; xuất dữ liệu |
| Ai dùng | phỏng đoán — nhân viên tự đánh giá và quản lý trực tiếp đánh giá |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Hai thẻ: Phiếu đánh giá và Chưa đánh giá. Có Export.

**Trường dữ liệu**

Dữ liệu khảo sát chỉ ghi nhận trường lọc:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `chucDanh` | Lọc theo chức danh | |
| `maKeHoach` | Lọc theo kế hoạch đánh giá | |
| `nhomDanhGia` | Lọc theo nhóm đánh giá | |
| `thang` | Lọc theo tháng | |
| `nam` | Lọc theo năm | |
| `trangThai-chuadanhgia` | Trạng thái của phiếu chưa đánh giá | |
| `qSearch` | Tìm kiếm nhanh | |

**Chỗ đáng chú ý:** Thẻ "Chưa đánh giá" tách biệt cho phép theo dõi nhanh phiếu còn tồn đọng mà không cần lọc thủ công.

---

## DG4. Kết quả đánh giá

| | |
|---|---|
| Đường dẫn | `/KetQuaDanhGia/Index` |
| Dùng để làm gì | Tổng hợp điểm và xếp loại theo kỳ; xem kết quả từng tiêu chí; Import/Export; nối sang kỳ lương |
| Ai dùng | phỏng đoán — phòng Nhân sự và ban lãnh đạo |
| Mình có chưa | [ ] Chưa có |

**Cấu trúc màn hình**

Các thẻ: Kết quả đánh giá, Kết quả tiêu chí. Có Export, Cập nhật, Import.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `tuNgay-ketqua` | Lọc từ ngày | |
| `denNgay-ketqua` | Lọc đến ngày | |
| `chucDanh-ketqua` | Lọc theo chức danh | |
| `maKeHoach-ketqua` | Lọc theo kế hoạch đánh giá | |
| `nhomDanhGia-ketqua` | Lọc theo nhóm đánh giá | |
| `phanLoai-ketqua` | Lọc theo phân loại | |
| `thang` | Tháng kết quả | |
| `nam` | Năm kết quả | |
| `idImportDanhSach` | ID danh sách import kết quả | |
| `idTieuChi-ketquatieuchi` | Lọc tiêu chí ở thẻ kết quả tiêu chí | |
| `maNhanVien_KetQua` | Mã nhân viên | |
| `maKeHoach_KetQua` | Mã kế hoạch đánh giá | |
| `tenKeHoach_KetQua` | Tên kế hoạch đánh giá | |
| `kiLuongThang_KetQua` | Kỳ lương tháng tương ứng | xác nhận nối sang bảng lương |
| `kiLuongNam_KetQua` | Kỳ lương năm tương ứng | xác nhận nối sang bảng lương |
| `soDiem_KetQua` | Số điểm tổng | |
| `xepLoai_KetQua` | Xếp loại | |
| `FileUpload` | File import kết quả | |

**Cột bảng kết quả tiêu chí**

| Cột | Ghi chú |
|---|---|
| Đối tượng | |
| Tên tiêu chí | |
| Số điểm | |
| Người cập nhật | |
| Ngày cập nhật | |

**Chỗ đáng chú ý:** `kiLuongThang_KetQua` và `kiLuongNam_KetQua` xác nhận kết quả đánh giá được chuyển thẳng vào kỳ lương tương ứng. Màn hình sơ đồ tổ chức (`/SoDoToChuc/Index`) hiển thị Tổng điểm, Xếp loại, Mức độ phù hợp (%) từ dữ liệu đánh giá — ban lãnh đạo thấy tình trạng đánh giá trực tiếp trên cây tổ chức.

---

## Vòng đời một ứng viên

1. Phòng Nhân sự lập định biên (TD1): xác định số lượng cần tuyển theo từng vị trí và năm. Hệ thống nhắc trước bằng email/ứng dụng theo `truocBaoNhieuNgayCT`.
2. Khi cần tuyển, phòng Nhân sự tạo nhu cầu tuyển dụng (TD2): liên kết về định biên qua `soLuongDinhBien`, khai báo yêu cầu đầy đủ, bật `isPublish` nếu muốn đăng ra ngoài.
3. Chi phí đăng tuyển trên các kênh được ghi nhận qua phiếu TD3, liên kết với nhu cầu tuyển dụng tương ứng.
4. Ứng viên nộp hồ sơ: nhập tay, từ CV, hoặc đồng bộ từ nguồn ngoài vào TD4. Hồ sơ gắn `maNhuCau`, trạng thái theo dõi qua KanBan và lịch hẹn phỏng vấn trong cùng màn hình.
5. Ứng viên trúng tuyển: phòng Nhân sự lập quyết định nhận việc (TD5) ghi lương thử việc, lương chính thức và phụ cấp.
6. Phỏng đoán: hệ thống chuyển dữ liệu ứng viên (TD4) sang hồ sơ nhân viên mà không nhập lại, vì tập trường hai bên trùng nhau. Từ đây nhân viên có thể được đưa vào kế hoạch đánh giá (DG2).

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| `KeHoachNhanSu` | `maTrangThai`, `loaiDinhBien`, `nam`, `maChucDanh` | Đoán |
| `NhuCauTuyenDung` | `maNhuCau`, `maCongTy`, `maViTriTuyenDung`, `soLuong`, `tuyenTu`, `tuyenDen`, `isPublish` | Khá |
| `ThanhToanChiPhiTuyenDung` | `soPhieu`, `maTrangThai`, `maNhuCau`, `nhaTuyenDung`, `chiPhi`, `tuNgay`, `denNgay` | Khá |
| `UngVien` | `maUngVien`, `maNhuCau`, `tenUngVien`, `soCMND`, `maTrangThai`, `nguonDangTuyen` | Khá |
| `QuyetDinhNhanViec` | `soQuyetDinh`, `maUngVien`, `ngayBatDauNhanViec`, `luongCBThuViec`, `luongCBChinhThuc`, `maLoaiHopDong` | Khá |
| `QuyetDinhNhanViec_PhuCap` | `maQuyetDinh`, `maPhuCap`, `soTien` | Đoán |
| `TieuChi` | `idTieuChi`, `maTuKhoaCT`, `loaiPhieu` | Đoán |
| `KeHoachDanhGia` | `maKeHoach`, `tenPhieuDanhGia`, `loaiDanhGia`, `kiLuongThang`, `kiLuongNam`, `txtNgayDong` | Khá |
| `KeHoachDanhGia_TieuChi` | `maKeHoach`, `idTieuChi`, `heSoTieuChi`, `maTuKhoaCT` | Đoán |
| `KeHoachDanhGia_NhanVien` | `maKeHoach`, `maNhanVien`, `ngayBatDau`, `ngayKetThuc` | Đoán |
| `PhieuDanhGia` | `maPhieu`, `maKeHoach`, `maNhanVien`, `trangThai` | Đoán |
| `KetQuaDanhGia` | `maNhanVien`, `maKeHoach`, `soDiem`, `xepLoai`, `kiLuongThang`, `kiLuongNam` | Chắc |

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| TD1 Định biên nhân sự | Lấy sau | Chưa có module nhân sự; cần xây hồ sơ nhân viên và cơ cấu tổ chức trước | Bỏ phần thông báo App nếu chưa tích hợp push notification |
| TD2 Nhu cầu tuyển dụng | Lấy sau | Phụ thuộc TD1 và danh mục chức danh | Landing page công khai cần domain và SSL riêng |
| TD3 Thanh toán chi phí | Lấy sau | Logic phiếu đơn giản; có thể xem xét dùng lại model phiếu chi của Thu mua | Xác nhận luồng phê duyệt và cách nối kế toán |
| TD4 Hồ sơ ứng viên | Lấy sau | Cần TD2 làm nền; cần thiết kế bước chuyển ứng viên sang nhân viên | Làm rõ nghĩa `tenNhanVien` trước khi thiết kế schema |
| TD5 Quyết định nhận việc | Lấy sau | Cần hồ sơ nhân viên và module lương trước để nối dữ liệu | Giữ nguyên cấu trúc hai bộ lương trong một phiếu |
| TD6 Cấu hình tuyển dụng | Lấy sau | Phụ thuộc TD1–TD5 | Dùng lại mail server và cấu hình SMTP hiện có của Thu mua |
| DG1 Tiêu chí đánh giá | Lấy sau | Cần hồ sơ nhân viên và cơ cấu tổ chức trước | Xác nhận cơ chế từ khóa/công thức tương thích với bảng lương |
| DG2 Kế hoạch đánh giá | Lấy sau | Phụ thuộc DG1 và module nhân sự | Cơ chế nối `kiLuongThang`/`kiLuongNam` cần module lương hoàn chỉnh trước |
| DG3 Phiếu đánh giá | Lấy sau | Phụ thuộc DG2 | Cần phân quyền xem phiếu đánh giá của nhân viên khác |
| DG4 Kết quả đánh giá | Lấy sau | Phụ thuộc DG1–DG3 | Tích hợp hiển thị điểm trên sơ đồ tổ chức nếu có module đó |
