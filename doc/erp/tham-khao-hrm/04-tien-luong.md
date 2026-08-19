# TIỀN LƯƠNG

| | |
|---|---|
| Thuộc bộ | Tham khảo hệ thống HRM HrOnline |
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo, ngày 11/08/2026 |
| Số chức năng | 6 (TL1–TL6) + báo cáo + quy trình duyệt |

## Tóm tắt mục này

Phần tiền lương của HrOnline không viết cứng cách tính lương. Họ xây dựng một bộ máy công thức, để khách tự khai cột (bao gồm tên cột, kiểu dữ liệu, công thức tính) và tự ghép các cột đó thành bảng lương của công ty mình. Một công ty có thể cùng lúc vận hành nhiều cấu hình bảng lương khác nhau (bản demo có 14 cấu hình), mỗi cấu hình áp cho một nhóm đối tượng khác nhau — theo phòng ban, chức danh, hình thức làm việc, pháp nhân.

Điều này giải thích tại sao toàn bộ mục này phải cấp trước một câu hỏi chưa có lời giải: kết quả bảng lương được lưu theo cấu trúc nào — một dòng một ô, JSON trong một cột, hay bảng rộng có trần? Câu trả lời quyết định toàn bộ thiết kế lớp dữ liệu và không thể thay đổi sau khi đã có dữ liệu thật.

Hai con đường xây dựng đều đắt: viết cứng công thức thì mỗi lần chính sách lương thay đổi là một lần sửa mã nguồn và chờ đợt phát hành; viết bộ máy công thức thì phải làm thêm màn hình khai công thức, kiểm tra công thức sai, và xử lý công thức tham chiếu vòng. Cách tính lương của mỗi công ty khác nhau, và ngay trong cùng một công ty cũng thường đổi cách tính mỗi năm.

**Kết luận nội bộ: không làm lương trong bản đầu.** Mục này là bằng chứng cho khuyến nghị đó.

| # | Chức năng | Đường dẫn | Dùng để làm gì | Mình có chưa |
|---|---|---|---|---|
| TL1 | Cấu hình bảng lương | `/CauHinhHeThong/Index` | Khai các cột của bảng lương, công thức, đối tượng áp dụng | [ ] |
| TL2 | Bảng lương | `/BangLuong/Index` | Tổng hợp dữ liệu và tính lương theo tháng/năm | [ ] |
| TL3 | Phụ cấp cố định | `/PhuCapCoDinh/Index` | Quản lý các khoản phụ cấp cố định gắn vào nhân viên | [ ] |
| TL4 | Khoản cộng trừ | `/KhoanCongTru/Index` | Khai các khoản cộng/trừ gắn vào từng cấu hình bảng lương | [ ] |
| TL5 | Thuế thu nhập cá nhân | `/KhaiThueTheoKy/Index` | Khai thuế theo kỳ và quyết toán thuế | [ ] |
| TL6 | Cấu hình thang tính thuế | `/CauHinhHeThong/Index` | Khai thang lương, thang thuế gross, thang thuế net | [ ] |

---

## TL1. Cấu hình bảng lương

| | |
|---|---|
| Đường dẫn | `/CauHinhHeThong/Index` > mục "Cấu hình bảng lương" |
| Dùng để làm gì | Định nghĩa một bảng lương: các cột cần có, công thức tính từng cột, đối tượng nhân viên được áp dụng, nhân viên phụ trách tính lương |
| Ai dùng | Bộ phận Nhân sự / Kế toán lương |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Màn hình danh sách có hai thẻ: CẤU HÌNH BẢNG LƯƠNG và TỪ KHÓA BẢNG LƯƠNG. Bản demo có 14 cấu hình bảng lương khác nhau cùng tồn tại.

**Trường dữ liệu**

Danh sách cấu hình bảng lương:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| ID BẢNG LƯƠNG | Mã định danh cấu hình | Hiển thị trên danh sách |
| TÊN BẢNG LƯƠNG | Tên mô tả cấu hình | Bắt buộc |
| HIỆU LỰC | Công tắc bật/tắt | Tắt thì không chạy tính lương |
| NHÂN VIÊN ÁP DỤNG | Danh sách nhân viên áp dụng | Có thể rỗng nếu áp theo phòng ban / chức danh |
| PHÒNG BAN ÁP DỤNG | Phòng ban áp dụng | |
| CHỨC DANH ÁP DỤNG | Chức danh áp dụng | |
| PHÁP NHÂN ÁP DỤNG | Pháp nhân áp dụng | |
| NHÂN VIÊN TÍNH LƯƠNG | Người phụ trách chạy tính lương | |
| NGƯỜI LẬP | Người tạo cấu hình | |
| NGƯỜI CẬP NHẬT | Người sửa cuối | |
| NGÀY CẬP NHẬT | Ngày sửa cuối | |

Màn hình sửa cấu hình — khối thông tin chung:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| Tên bảng lương | Tên cấu hình | Bắt buộc |
| `lsNhanVienTinhLuong` | Nhân viên phụ trách tính lương | Chọn nhiều |
| Chu kỳ lương tính theo ngày | Số ngày trong chu kỳ lương | |
| `idMauIn` | Mẫu phiếu lương nhân viên | Ví dụ: "Phiếu lương mặc định" |
| `hienThiMacDinh` | Kiểu nhóm hiển thị bảng lương | Group phòng ban / Group hình thức nhân viên / Không group |
| `loaiBangLuong` | Loại bảng lương | Tổng lương hàng tháng / Lương sản phẩm / Lương thưởng |

Màn hình sửa — khối TRẠNG THÁI ÁP DỤNG: tích chọn các trạng thái nhân viên được áp cấu hình này.

Màn hình sửa — khối ĐỐI TƯỢNG ÁP DỤNG:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `lsPhongBanApDung` | Danh sách phòng ban áp dụng | |
| `lsChucDanhApDung` | Danh sách chức danh áp dụng | |
| `lsCBChucVu` | Cấp bậc chức vụ áp dụng | |
| `lsNhanVienApDung` | Nhân viên áp dụng cụ thể | |
| `lsHinhThucApDung` | Hình thức làm việc | CTV / Thời vụ / Part time / Full time |
| `lsPhapNhanApDung` | Pháp nhân áp dụng | |
| `toanTuApDung` | Toán tử nối các điều kiện | And / Or |
| `toanTuPBHT` | Toán tử nối phòng ban và hình thức | And / Or |

Màn hình sửa — khối ĐỐI TƯỢNG LOẠI TRỪ:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `lsPhongBanLoaiTru` | Phòng ban bị loại trừ | |
| `lsChucDanhLoaiTru` | Chức danh bị loại trừ | |
| `lsNhanVienLoaiTru` | Nhân viên bị loại trừ cụ thể | |
| `toanTuLoaiTru` | Toán tử nối các điều kiện loại trừ | And / Or |

Màn hình sửa — bảng khai cột (mỗi dòng là một cột của bảng lương):

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| GIÁ TRỊ CỘT | Giá trị cột | Bắt buộc |
| `tenTieuDe` | Tiêu đề cột tiếng Việt | |
| `tenTieuDeTiengAnh` | Tiêu đề cột tiếng Anh | |
| `tuKhoaEdit` | Từ khóa cột, dùng để các công thức khác tham chiếu | |
| `congThuc` | Công thức tính giá trị cột này | Viết bằng cú pháp riêng của hệ thống |
| KIỂU | Kiểu dữ liệu cột | |
| HIỂN THỊ | Hiển thị trên bảng lương hay không | |
| BL | Hiển thị trên phiếu lương nhân viên hay không | |
| `align` | Căn chỉnh nội dung cột | Left / Center / Right |
| `nhanMau` | Màu nền cột | |
| `idNhom` | Nhóm cột | |
| `cachTinhDongTong` | Cách tính dòng tổng của cột này | Tổng các hàng / Công thức / Giá trị mới nhất |
| `cachTinhDongTongNhieuNoi` | Cách tính dòng tổng khi nhân viên làm nhiều nơi | Tổng các hàng / Công thức |
| `cachTinhDongDonNhieuNoi` | Cách tính dòng đơn khi nhân viên làm nhiều nơi | Không tính (=0) / Công thức |

**Luồng chạy**

1. Người dùng khai danh sách cột và công thức cho từng cột.
2. Lưu cấu hình (nút "Lưu Thay Đổi").
3. Khi chạy tính lương (TL2), hệ thống duyệt từng cột theo thứ tự, tính giá trị cột dựa trên công thức và các từ khóa đã khai.

**Chỗ đáng chú ý:**

Cú pháp công thức hệ thống hỗ trợ: toán tử toán học (+, -, *, /), toán tử quan hệ (=, !=, >, <, >=, <=), hàm `isnull(từ khóa, giá trị gán)`, hàm `round(từ khóa, số thập phân)`, hàm `IIF(biểu thức điều kiện, giá trị đúng, giá trị sai)`. Hàm `IIF` cho phép viết điều kiện phân nhánh nhưng không rõ có hỗ trợ lồng nhau hay không — phỏng đoán.

Bộ máy này nghĩa là: mỗi cột có thể tham chiếu từ khóa của cột khác. Nếu tham chiếu tạo vòng lặp (A tính theo B, B tính theo A), hệ thống phải phát hiện và báo lỗi — đây là phần không nhỏ trong chi phí xây dựng.

---

## TL2. Bảng lương

| | |
|---|---|
| Đường dẫn | `/BangLuong/Index` |
| Dùng để làm gì | Chạy tính lương cho một bảng lương theo tháng và năm; nhân viên xem phiếu lương cá nhân |
| Ai dùng | Nhân viên tính lương (chạy tổng hợp + tính lương); Nhân viên (xem phiếu cá nhân) |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Luồng hai bước rõ ràng: Bước 1 Tổng hợp dữ liệu → Bước 2 Tính lương. Mỗi lần chạy cần chọn `idBangLuong` và tháng / năm.

Màn hình cá nhân: `/BangLuong/BangLuongChiTietNhanVien` — nhân viên chỉ xem phiếu lương của chính mình.

**Trường dữ liệu**

Không quan sát được cấu trúc chi tiết màn hình này trên bản demo — phỏng đoán rằng các tham số đầu vào gồm ít nhất `idBangLuong`, tháng, năm.

**Luồng chạy**

1. Chọn bảng lương, tháng, năm.
2. Chạy Bước 1: tổng hợp dữ liệu (chấm công, phụ cấp, khoản cộng trừ, ngày công).
3. Chạy Bước 2: áp công thức từng cột từ cấu hình, ghi kết quả.
4. Quy trình duyệt: Phiếu Xác Nhận Bảng Lương, sau đó có thể sinh Đề nghị chi lương.

---

## TL3. Phụ cấp cố định

| | |
|---|---|
| Đường dẫn | `/PhuCapCoDinh/Index` |
| Dùng để làm gì | Quản lý các khoản phụ cấp được trả cố định hàng tháng, không phụ thuộc vào chấm công |
| Ai dùng | Bộ phận Nhân sự / Kế toán lương |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Bốn thẻ: Danh sách phụ cấp cố định, Chi tiết, Export, Import, Import Update.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `maLoaiPhuCap-ds` | Mã loại phụ cấp (lọc danh sách) | |
| `maJob-ds` | Mã vị trí công việc (lọc danh sách) | |
| `trangThai-ds` | Trạng thái (lọc danh sách) | |
| `idImportDanhSach` | Mã đợt import (lọc danh sách) | |
| `maLoaiPhuCap-ct` | Mã loại phụ cấp (lọc chi tiết) | |
| `maJob-ct` | Mã vị trí công việc (lọc chi tiết) | |
| `chucVu-ct` | Chức vụ (lọc chi tiết) | |
| `trangThai-ct` | Trạng thái (lọc chi tiết) | |
| `FileUpload` | File import | |

**Chỗ đáng chú ý:**

Hỗ trợ nhập hàng loạt qua file (Import / Import Update). Import Update cho phép cập nhật dữ liệu đã có mà không tạo mới — phỏng đoán rằng đây là update theo mã nhân viên hoặc mã phụ cấp.

---

## TL4. Khoản cộng trừ

| | |
|---|---|
| Đường dẫn | `/KhoanCongTru/Index` |
| Dùng để làm gì | Khai các khoản cộng hoặc trừ đặc biệt phát sinh trong kỳ lương, gắn vào một cấu hình bảng lương cụ thể |
| Ai dùng | Bộ phận Nhân sự / Kế toán lương |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Năm thẻ: Khoản cộng trừ, Khoản cộng trừ Chi Tiết, Khoản cộng trừ Tổng Hợp, Import, Export.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `thangSearch-phucloi` | Tháng lọc | |
| `namSearch-phucloi` | Năm lọc | |
| `maTrangThaiSearch-phucloi` | Mã trạng thái lọc | |
| `maDanhMucSearch-phucloi` | Mã danh mục lọc | |
| `idBangLuong-phucloi` | Bảng lương áp dụng | Khoản gắn trực tiếp vào một cấu hình bảng lương |
| `maChucDanh` | Chức danh (lọc chi tiết / tổng hợp) | |
| `khoanCongTruImport` | Loại import | |
| `FileUpload` | File import | |

**Chỗ đáng chú ý:**

`idBangLuong-phucloi` xác nhận rằng khoản cộng trừ gắn trực tiếp vào một cấu hình bảng lương cụ thể, không gắn chung cho mọi bảng lương. Nếu một nhân viên thuộc nhiều bảng lương, khoản phải khai cho từng bảng.

---

## TL5. Thuế thu nhập cá nhân

| | |
|---|---|
| Đường dẫn | `/KhaiThueTheoKy/Index` |
| Dùng để làm gì | Khai thuế TNCN theo từng kỳ; lập bảng quyết toán thuế cuối năm |
| Ai dùng | Kế toán thuế |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Hai thẻ: Khai thuế theo kỳ và Bảng quyết toán thuế.

**Trường dữ liệu**

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| `trangThai-khaithuetheoky` | Trạng thái kỳ khai thuế | |
| `maPhapNhan-khaithuetheoky` | Pháp nhân khai thuế | |
| `nam-khaithuetheoky` | Năm khai thuế | |

Bộ trường tương tự tồn tại cho thẻ Bảng quyết toán thuế.

**Chỗ đáng chú ý:**

Màn hình này có vẻ chỉ hiển thị kết quả thuế đã tính từ bảng lương và cho phép gửi/xuất báo cáo; không rõ có cho phép nhập tay hay không — phỏng đoán.

---

## TL6. Cấu hình thang tính thuế

| | |
|---|---|
| Đường dẫn | `/CauHinhHeThong/Index` > mục "Cấu hình thang tính thuế" |
| Dùng để làm gì | Khai bậc lương, thang tính thuế gross và net để hệ thống tra cứu khi tính lương và thuế |
| Ai dùng | Quản trị hệ thống / Bộ phận Nhân sự |
| Mình có chưa | [ ] |

**Cấu trúc màn hình**

Ba thẻ: THANG TÍNH LƯƠNG, THANG TÍNH THUẾ GROSS, THANG TÍNH THUẾ NET.

**Trường dữ liệu**

Bảng thang tính lương:

| Trường | Nghĩa | Ghi chú |
|---|---|---|
| MÃ | Mã bậc lương | |
| TÊN | Tên bậc lương | |
| CẤP BẬC LƯƠNG | Cấp bậc | |
| TRẠNG THÁI | Hiệu lực | |
| PHÒNG BAN | Phòng ban áp dụng | |
| CHỨC DANH | Chức danh áp dụng | |
| CẤP BẬC | Cấp bậc áp dụng | |
| TỔNG LƯƠNG | Tổng lương của bậc | Ví dụ: N2 = 10.000.000; NV1 = 15.000.000 |
| LƯƠNG CƠ BẢN | Lương cơ bản của bậc | Ví dụ: N2 = 7.000.000; NV1 = 5.000.000 |
| LƯƠNG ĐÓNG BẢO HIỂM | Mức lương để đóng BHXH của bậc | Ví dụ: N2 = 2.000.000; NV1 = 5.000.000 |
| NGÀY ÁP DỤNG | Ngày hiệu lực của bậc | |
| GHI CHÚ | Ghi chú thêm | |

**Chỗ đáng chú ý:**

Hợp đồng lao động (mục hồ sơ nhân sự) có trường `maThangTinhLuong` trỏ đến bậc lương trong bảng này. Hợp đồng cũng lưu ba mức riêng: `luongThoaThuan`, `luongCoBan`, `luongDongBaoHiem`. Ngoài ra trên hợp đồng còn có `khoanBoSungLuong`, `quiNoiBo`, `doanPhi`, `dangPhi`, `luongNet`, `maLoaiThue`, `heSoLuong`, `tyLeLuong`. Như vậy thang tính lương là giá trị tham khảo; giá trị thực tế ghi trên từng hợp đồng.

---

## Phỏng đoán cấu trúc dữ liệu của mục này

| Bảng | Cột chính | Mức tin cậy |
|---|---|---|
| BangLuongCauHinh | id, tenBangLuong, loaiBangLuong, hienThiMacDinh, idMauIn, hieuLuc, toanTuApDung, toanTuPBHT, toanTuLoaiTru | Chắc |
| BangLuongCauHinhCot | id, idBangLuongCauHinh, thuTu, tenTieuDe, tenTieuDeTiengAnh, tuKhoaEdit, congThuc, kieu, hienThi, hienThiPhieuLuong, align, nhanMau, idNhom, cachTinhDongTong, cachTinhDongTongNhieuNoi, cachTinhDongDonNhieuNoi | Khá |
| BangLuong (kết quả header) | id, idBangLuongCauHinh, thang, nam, trangThai | Chắc |
| BangLuongChiTiet (kết quả từng cột) | Chưa rõ — xem bảng so sánh đường lưu bên dưới | Đoán |
| PhuCapCoDinh | id, idNhanVien, maLoaiPhuCap, maJob, chucVu, soTien, trangThai, idImportDanhSach | Khá |
| KhoanCongTru | id, idBangLuong, idNhanVien, maDanhMuc, soTien, thang, nam, trangThai | Khá |
| ThangTinhLuong | id, ma, ten, capBac, phongBan, chucDanh, tongLuong, luongCoBan, luongDongBaoHiem, ngayApDung | Chắc |

---

## Ba đường lưu kết quả bảng lương và cái giá của từng đường

Nhóm không quan sát được HrOnline chọn đường nào. Bảng này là phân tích nội bộ.

| Đường | Mô tả | Ưu điểm | Nhược điểm |
|---|---|---|---|
| 1. Một dòng một ô (dòng-thuộc-tính) | Mỗi cặp (nhân viên, kỳ lương, tên cột) là một dòng riêng trong bảng | Linh hoạt hoàn toàn; thêm cột mới không cần sửa schema | Bảng phình rất nhanh: 500 người x 40 cột x 12 tháng = 240.000 dòng/năm; báo cáo phải xoay bảng (PIVOT) |
| 2. Một dòng một người, giá trị trong một cột JSON | Mỗi cặp (nhân viên, kỳ lương) là một dòng; tất cả giá trị cột nằm trong một cột kiểu JSON/Text | Gọn, đọc nhanh, thêm cột không cần sửa schema | Không lọc theo giá trị cột bằng SQL thường được; công cụ báo cáo khó dùng; debug khó |
| 3. Bảng rộng có sẵn N cột đánh số (`col1`...`colN`) | Bảng có cố định N cột; cột thứ i của cấu hình tương ứng với `colN` theo vị trí | Truy vấn đơn giản; tốc độ nhanh | Schema bẩn: tên cột vô nghĩa; có trần cứng (nếu cấu hình có nhiều hơn N cột thì không lưu được); khi cấu hình đổi vị trí cột, ánh xạ cũ bị lệch |

**Câu hỏi này phải được trả lời trước khi viết dòng mã lương đầu tiên.** Nó ảnh hưởng toàn bộ lớp dữ liệu, cách viết báo cáo, và khả năng nâng cấp về sau. Đây là một lý do nữa để không làm lương trong bản đầu.

---

## Nếu lấy về hệ thống mình

| Chức năng | Nên lấy | Vì sao | Cần sửa gì so với bản của họ |
|---|---|---|---|
| TL1. Cấu hình bảng lương | [ ] Không | Bộ máy công thức đòi hỏi thêm màn hình khai công thức, trình kiểm tra cú pháp, xử lý tham chiếu vòng — độ phức tạp ngang một ngôn ngữ kịch bản thu nhỏ | Nếu sau này làm, phải thiết kế lại từ đầu cho phù hợp loại hình công ty |
| TL2. Bảng lương (luồng hai bước) | [ ] Không | Phụ thuộc vào TL1; không có TL1 thì TL2 không có dữ liệu đầu vào | — |
| TL3. Phụ cấp cố định | [~] Có thể | Khái niệm đơn giản, có thể làm gọn bằng một bảng gắn phụ cấp vào nhân viên | Cần làm rõ: phụ cấp cố định có tham gia công thức bảng lương hay chỉ là khoản cộng thêm cuối kỳ |
| TL4. Khoản cộng trừ | [~] Có thể | Khái niệm đơn giản, nhưng phải quyết định trước cách gắn vào bảng lương hay ghi đơn giản vào sổ kế toán | Nên tách thành bảng tối giản: khoản, kỳ lương, nhân viên, số tiền, loại (+/-) |
| TL5. Thuế TNCN | [ ] Không | Phụ thuộc vào kết quả bảng lương; nếu không làm bảng lương thì không có dữ liệu thuế tự động | Có thể xuất dữ liệu thủ công sang phần mềm thuế riêng |
| TL6. Thang tính lương (danh mục bậc) | [~] Có thể | Phần danh mục bậc lương đơn giản, là dữ liệu tham khảo, có thể làm ngay từ đầu | Cột cần có: mã bậc, tên bậc, lương cơ bản, lương đóng bảo hiểm, lương thỏa thuận, ngày hiệu lực |

**Kết luận nhắc lại:** làm lương không phải là làm một màn hình. Đây là một bộ máy công thức. Mỗi công ty tính lương một kiểu; cùng một công ty thường đổi cách tính mỗi năm. Viết cứng công thức thì mỗi lần đổi chính sách lương là một lần sửa mã nguồn và chờ đợt phát hành. Viết bộ máy công thức thì phải làm thêm màn hình khai công thức, kiểm tra công thức sai, và xử lý công thức tham chiếu vòng. Cả hai con đường đều đắt và khó. Không làm lương trong bản đầu.
