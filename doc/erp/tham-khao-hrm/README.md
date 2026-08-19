# THAM KHẢO HỆ THỐNG HRM HRONLINE

| | |
|---|---|
| Bản | 1.0 — 11/08/2026 |
| Nguồn | Khảo sát trực tiếp trên bản demo công khai, ngày 11/08/2026 |
| Phạm vi | Toàn bộ hệ thống trừ khối E-Learning |
| Số chức năng đã lập tài liệu | 59, chia 8 mục |
| Dùng để làm gì | **Bảng đối chiếu mang đi phỏng vấn**, và cơ sở để xếp thứ tự làm HRM |
| Ai đọc | Người đi khảo sát nghiệp vụ, đội phần mềm, người chủ trì |
| Liên quan | [`erp/01` Ngắn hạn](../01-ngan-han-2026.md) · [`erp/03` Câu hỏi khảo sát HRM](../03-cau-hoi-khao-sat-hrm.md) · [`erp/04` Danh mục chờ quyết](../04-danh-muc-cho.md) |

---

## Đọc bộ tài liệu này thế nào

Quyết định **Đ2** đã chốt ngày 10/08/2026: **không chép nghiệp vụ từ phần mềm ngoài.** Bộ tài liệu này không phá quyết định đó.

Đây là bảng đối chiếu. Mỗi dòng trong bảng tính năng là **một câu hỏi mang đi phỏng vấn**, không phải một dòng yêu cầu.

Ba cách dùng sai, nói rõ để tránh:

| Cách dùng sai | Vì sao sai |
|---|---|
| Coi đây là bản mô tả yêu cầu, giao cho lập trình viên làm theo | Đây là nghiệp vụ của công ty khác. Nghiệp vụ của mình phải sinh ra từ phỏng vấn ở bước 0 |
| Đưa cả danh sách 59 chức năng vào phạm vi HRM bản 1 | Phạm vi sẽ phình gấp bốn lần và không kịp trong năm nay |
| Hỏi phòng ban "mình có cần tính năng này không" | Ai cũng trả lời có. Phải hỏi "việc này đang làm bằng gì, mất bao lâu, sai bao nhiêu lần" |

Cách dùng đúng: in phần **bản đồ tính năng** ở dưới, mang theo lúc phỏng vấn, và với mỗi dòng hỏi **"cái này ở công ty mình đang làm bằng gì"**.

---

## Bộ tài liệu gồm những tệp nào

| Tệp | Nội dung | Số chức năng |
|---|---|---|
| [`01` Nhân sự](./01-nhan-su.md) | Hồ sơ nhân viên, sơ đồ tổ chức, hợp đồng lao động, bảo hiểm, lộ trình sự nghiệp | 5 |
| [`02` Đơn từ và bộ máy duyệt](./02-don-tu-va-duyet.md) | Năm loại đơn, cấu hình loại đơn, và quy trình duyệt dùng chung cho 88 loại chứng từ | 7 |
| [`03` Chấm công](./03-cham-cong.md) | Bảng công, phân ca, thiết lập ca, phép năm, ngày nghỉ lễ, hai màn hình cấu hình | 7 |
| [`04` Tiền lương](./04-tien-luong.md) | Cấu hình bảng lương và bộ máy công thức, bảng lương, phụ cấp, khoản cộng trừ, thuế | 6 |
| [`05` Quyết định nhân sự](./05-quyet-dinh-nhan-su.md) | Điều chuyển, thôi việc, điều chỉnh lương, đi làm lại, thành tích vi phạm, điều chỉnh hợp đồng | 6 |
| [`06` Tuyển dụng và đánh giá](./06-tuyen-dung-danh-gia.md) | Định biên, nhu cầu tuyển, chiến dịch, ứng viên, quyết định nhận việc, cấu hình; bốn màn hình đánh giá | 10 |
| [`07` Workspace và tài sản](./07-workspace-tai-san.md) | Khối dùng chung không thuộc nhân sự, và khối tài sản | 13 |
| [`08` Hệ thống và phân quyền](./08-he-thong-va-phan-quyen.md) | Người dùng, nhóm quyền, 29 màn hình cấu hình, 9 màn hình báo cáo, dashboard | 5 |
| [`09` Phỏng đoán cơ sở dữ liệu](./09-phong-doan-co-so-du-lieu.md) | Khoảng 50 bảng, quy ước đặt tên, bốn cơ chế xuyên suốt, **bốn câu hỏi phải trả lời trước khi viết mã** | — |
| [`10` Đề xuất áp dụng](./10-de-xuat-ap-dung.md) | **Lấy gì, theo thứ tự nào, sửa gì trên mã nguồn hiện có** | — |

**Nếu chỉ đọc được một tệp:** đọc [`10`](./10-de-xuat-ap-dung.md). Đó là phần kết luận.

**Nếu chỉ đọc được hai:** thêm [`09` mục 5](./09-phong-doan-co-so-du-lieu.md) — bốn câu hỏi thiết kế phải trả lời trước khi viết dòng mã đầu tiên.

---

## Ba kết luận của cả bộ tài liệu

**1. Phần nền phân quyền của mình không phải làm lại.** Mô hình hai trục của họ trùng với mô hình hai trục của Thu mua, và trục phạm vi dữ liệu của mình còn mềm hơn — cấp theo từng lượt, nhiều chiều, thay vì ba mức cố định. Giữ nguyên, chỉ mở rộng.

**2. Thứ đáng lấy nhất không phải một tính năng nhân sự — là bộ máy duyệt dùng chung.** Một màn hình cấu hình phục vụ 88 loại chứng từ, khai được vai tương đối thay vì gọi đích danh người duyệt. Nó thuộc phần nền, và phải làm **trước** HRM.

**3. Không làm lương trong bản 1, và giờ có bằng chứng.** Họ không viết cứng công thức lương — họ làm một bộ máy công thức có `IIF`, `isnull`, `round`, tham chiếu cột bằng từ khóa. Làm lương không phải làm một màn hình; là làm một ngôn ngữ kịch bản thu nhỏ cộng ba màn hình phụ trợ.

Chi tiết và hệ quả ở [`10`](./10-de-xuat-ap-dung.md).

---

## Bản đồ tính năng — in trang này mang đi phỏng vấn

Cột "Mình có chưa": `[x]` có · `[~]` có phần gần tương đương · `[ ]` chưa có.
Cột "Cần ngay?" để trống, điền tay lúc phỏng vấn.

### Nhân sự — [chi tiết](./01-nhan-su.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| NS1 | Hồ sơ nhân viên — khoảng 90 trường, 8 thẻ | `/HoSoNhanVien/` | `[~]` chỉ vài trường | |
| NS2 | Sơ đồ tổ chức | `/SoDoToChuc/Index` | `[ ]` | |
| NS3 | Hợp đồng lao động | `/HopDongLaoDong/` | `[ ]` | |
| NS4 | Bảo hiểm xã hội | `/BaoHiem/Index` | `[ ]` | |
| NS5 | Lộ trình sự nghiệp | `/LoTrinhSuNghiep/Index` | `[ ]` | |

### Đơn từ và duyệt — [chi tiết](./02-don-tu-va-duyet.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| DT1 | Nghỉ phép | `/NghiPhep/Index` | `[ ]` | |
| DT2 | Bổ sung công | `/BoSungCong/Index` | `[ ]` | |
| DT3 | Công tác | `/CongTac/Index` | `[ ]` | |
| DT4 | Tăng ca | `/TangCa/Index` | `[ ]` | |
| DT5 | Tăng ca phòng ban | `/TangCaPhongBan/Index` | `[ ]` | |
| DT6 | Cấu hình loại đơn từ — 15 loại, ~50 trường | Trong cấu hình hệ thống | `[ ]` | |
| DT7 | **Quy trình duyệt — 88 loại công việc** | `/QuiTrinhDuyet/Index` | `[~]` duyệt cứng trong mã | |

### Chấm công — [chi tiết](./03-cham-cong.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| CC1 | Bảng tổng hợp công | `/BangCongDong/Index` | `[ ]` | |
| CC2 | Phân ca xếp lịch | `/QuanLyCa/Index` | `[ ]` | |
| CC3 | Thiết lập ca | `/ThietLapCa/Index` | `[ ]` | |
| CC4 | Quản lý phép năm | `/PhepNamDong/Index` | `[ ]` | |
| CC5 | Quản lý ngày nghỉ lễ | `/NghiLe/Index` | `[ ]` | |
| CC6 | Cấu hình bảng công | Trong cấu hình hệ thống | `[ ]` | |
| CC7 | Cấu hình loại chấm công | Trong cấu hình hệ thống | `[ ]` | |

### Tiền lương — [chi tiết](./04-tien-luong.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| TL1 | **Cấu hình bảng lương — bộ máy công thức** | Trong cấu hình hệ thống | `[ ]` | |
| TL2 | Bảng lương | `/BangLuong/Index` | `[ ]` | |
| TL3 | Phụ cấp cố định | `/PhuCapCoDinh/Index` | `[ ]` | |
| TL4 | Khoản cộng trừ | `/KhoanCongTru/Index` | `[ ]` | |
| TL5 | Thuế thu nhập cá nhân | `/KhaiThueTheoKy/Index` | `[ ]` | |
| TL6 | Cấu hình thang tính thuế | Trong cấu hình hệ thống | `[ ]` | |

### Quyết định nhân sự — [chi tiết](./05-quyet-dinh-nhan-su.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| QĐ1 | Điều chuyển và bổ nhiệm | `/DieuChuyen/Index` | `[ ]` | |
| QĐ2 | Thôi việc — 7 thẻ bàn giao | `/ThoiViec/Index` | `[ ]` | |
| QĐ3 | Điều chỉnh lương | `/PhieuDieuChinhLuong/Index` | `[ ]` | |
| QĐ4 | Đi làm lại | `/DiLamLai/Index` | `[ ]` | |
| QĐ5 | Thành tích và vi phạm | `/GhiNhanThanhTichVaViPham/Index` | `[ ]` | |
| QĐ6 | Điều chỉnh hợp đồng | `/PhieuDieuChinhHopDong/Index` | `[ ]` | |

### Tuyển dụng và đánh giá — [chi tiết](./06-tuyen-dung-danh-gia.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| TD1 | Định biên nhân sự | `/KeHoachNhanSu/Index` | `[ ]` | |
| TD2 | Nhu cầu tuyển dụng | `/NhuCauTuyenDung/Index` | `[ ]` | |
| TD3 | Chiến dịch tuyển dụng | `/ThanhToanChiPhiTuyenDung/Index` | `[ ]` | |
| TD4 | Hồ sơ ứng viên | `/UngVien/Index` | `[ ]` | |
| TD5 | Quyết định nhận việc | `/PhieuQuyetDinhNhanViec/Index` | `[ ]` | |
| TD6 | Cấu hình tuyển dụng | `/CauHinhTuyenDung/Index` | `[ ]` | |
| DG1 | Tiêu chí đánh giá | `/TieuChi/Index` | `[ ]` | |
| DG2 | Kế hoạch đánh giá | `/KeHoachDanhGia/Index` | `[ ]` | |
| DG3 | Phiếu đánh giá | `/PhieuDanhGia/Index` | `[ ]` | |
| DG4 | Kết quả đánh giá | `/KetQuaDanhGia/Index` | `[ ]` | |

### Workspace và tài sản — [chi tiết](./07-workspace-tai-san.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| WS1 | Truyền thông nội bộ | `/MangXaHoi/Index` | `[ ]` | |
| WS2 | Lịch biểu, đặt phòng họp | `/LichHop/Index` | `[ ]` | |
| WS3 | Chat | `/Chat/Index` | `[ ]` | |
| WS4 | Tài liệu — phân quyền theo thư mục | `/TaiLieu/Index` | `[~]` Trung tâm HDSD | |
| WS5 | Công văn | `/CongVan/Index` | `[ ]` | |
| WS6 | Ký số | `/ChuKySo/Index` | `[ ]` | |
| WS7 | Dự án | `/DuAn/Index` | `[~]` Project-M | |
| WS8 | Quản lý công việc | `/QLCongViec/Index` | `[~]` Project-M | |
| WS9 | Báo cáo công việc theo nhân viên | `/BaoCaoCongViecTheoNhanVien/Index` | `[ ]` | |
| TS1 | Danh sách tài sản — thuộc tính động | `/DSTaiSan/Index` | `[ ]` | |
| TS2 | Phiếu nhập tài sản | `/NhapTaiSan/Index` | `[ ]` | |
| TS3 | Phiếu xuất tài sản | `/XuatTaiSan/Index` | `[ ]` | |
| TS4 | Biên bản bàn giao tài sản | `/BienBanBanGiaoTaiSan/Index` | `[ ]` | |

### Hệ thống — [chi tiết](./08-he-thong-va-phan-quyen.md)

| # | Chức năng | Đường dẫn | Mình có chưa | Cần ngay? |
|---|---|---|---|---|
| HT1 | Người dùng, xác thực thiết bị | `/NguoiDung/Index` | `[x]` | |
| HT2 | Nhóm quyền — ~118 đối tượng × 6 hành động × 3 mức phạm vi | `/NhomQuyen/Index` | `[x]` | |
| HT3 | Cấu hình hệ thống — 29 màn hình | `/CauHinhHeThong/Index` | `[~]` | |
| HT4 | Báo cáo — 9 màn hình | `/BC_*/Index` | `[~]` | |
| HT5 | Dashboard động, nhúng Power BI | `/DashboardDong/Index` | `[ ]` | |

### Không lập tài liệu chi tiết

| Chức năng | Đường dẫn | Lý do |
|---|---|---|
| Thông báo app | `/ThongBao/Index` | Mình đã có: chuông và web push `[x]` |
| Trang học tập, Khóa học và kỳ thi, Nội dung, Kết quả bài thi | `/KhoaHocHocVien/`, `/KhoaHoc/`, `/CauHinhNoiDung/`, `/KetQuaBaiThi/` | Khối E-Learning, ngoài phạm vi khảo sát ngay từ đầu |
| BC E-Learning | `/BC_Elearning/Index` | Như trên |

---

## Con số đáng nói trong buổi trình bày

| Con số | Ý nghĩa |
|---|---|
| **59** chức năng, chưa kể E-Learning | Quy mô một hệ thống HRM thương mại đầy đủ |
| Trong đó mình có sẵn hoặc gần tương đương **6** | Phần nền: thông báo, tài liệu, dự án, công việc, người dùng, nhóm quyền |
| Phần nghiệp vụ nhân sự mình có: **gần như bằng không** | |
| **29** màn hình cấu hình | Một hệ thống nhân sự chạy được không phải là vài màn hình nhập liệu. Phần khai báo lớn gần bằng phần nghiệp vụ |
| **88** loại chứng từ chạy qua **một** bộ máy duyệt | Khác biệt kiến trúc lớn nhất giữa họ và mình |
| Hồ sơ nhân viên: **90** trường, nhưng thêm mới chỉ hỏi **12** | Nếu bắt điền đủ ngay từ đầu thì không ai nhập |
| **15** loại đơn từ, khai bằng bảng ~50 cột | Luật nghỉ phép là dữ liệu, không phải mã nguồn |

Ý nghĩa gộp lại: **phần nền mình đã có, khối lượng nằm ở nghiệp vụ chứ không nằm ở hạ tầng.**

---

## Hình chụp — phần chưa xong

Trong phiên khảo sát này xem được màn hình nhưng **không ghi được tệp ảnh xuống đĩa**. Đây là danh sách chỗ cần chụp kèm đường đi, để người khảo sát tự chụp.

Tạo thư mục `img/` trong chính thư mục này rồi bỏ ảnh vào theo đúng tên tệp dưới đây.

| # | Tên tệp | Chụp màn hình nào | Đường đi | Chụp để làm gì |
|---|---|---|---|---|
| 1 | `hronline-01-trangchu.png` | Trang chủ, lưới biểu tượng phân hệ | Đăng nhập xong | Đối chiếu với lưới biểu tượng mình định làm |
| 2 | `hronline-02-hosonv-danhsach.png` | Danh sách hồ sơ nhân viên | Nhân sự > Hồ sơ nhân viên | 26 cột và bộ lọc |
| 3 | `hronline-03-hosonv-chitiet.png` | Hồ sơ một người, thẻ Thông tin chính | Bấm vào một dòng | Độ dày của hồ sơ |
| 4 | `hronline-04-hosonv-tabs.png` | Dải 8 thẻ chi tiết | Cùng màn hình trên | Cách gom thông tin |
| 5 | `hronline-05-bangcong.png` | Bảng công động, dải thẻ | Chấm công > Bảng tổng hợp công | Thuyết phục nhất về khối lượng chấm công |
| 6 | `hronline-06-bangcong-loi.png` | Thẻ "Các lỗi dữ liệu" | Cùng màn hình trên | Bằng chứng phải có màn hình xử lý lỗi |
| 7 | `hronline-07-cauhinh-bangluong.png` | Cấu hình bảng lương, bảng khai cột | Cấu hình > Cấu hình bảng lương > Sửa | **Ảnh quan trọng nhất.** Làm lương là làm bộ máy công thức |
| 8 | `hronline-08-congthuc.png` | Khung hướng dẫn toán tử và hàm | Cuộn xuống cuối màn hình trên | Ngôn ngữ công thức |
| 9 | `hronline-09-quytrinhduyet.png` | Danh sách quy trình duyệt | Hệ thống > Quy trình duyệt | Chuỗi bước và vai tương đối |
| 10 | `hronline-10-nhomquyen.png` | Ma trận nhóm quyền | Hệ thống > Nhóm quyền, chọn nhóm rồi bấm tìm | Đối chiếu mô hình hai trục |
| 11 | `hronline-11-donnghiphep.png` | Form nộp đơn nghỉ phép | Đơn từ > Nghỉ phép > Thêm | Chỗ hiện số phép còn lại |
| 12 | `hronline-12-thoiviec-tabs.png` | Bảy thẻ của phiếu thôi việc | Nhân sự > Quyết định thôi việc > Thêm | Ba thẻ kiểm tra trước khi khóa tài khoản |
| 13 | `hronline-13-cauhinh-hethong.png` | Toàn bộ 29 mục cấu hình | Cấu hình hệ thống | Khối lượng phần cấu hình |

Chèn vào tài liệu theo mẫu:

```markdown
![Cấu hình bảng lương](./img/hronline-07-cauhinh-bangluong.png)
```

**Lưu ý:** đây là bản demo công khai nhưng vẫn có tên người thật trong dữ liệu. Trước khi đưa ảnh vào tài liệu trình bày, **che tên và số điện thoại**.

---

## Giới hạn của bộ tài liệu này

Nói rõ để người đọc biết tin tới đâu.

| Giới hạn | Chi tiết |
|---|---|
| Không truy cập được cơ sở dữ liệu | Toàn bộ [`09`](./09-phong-doan-co-so-du-lieu.md) là phỏng đoán, có ghi mức tin cậy từng bảng |
| Bản demo, không phải bản chạy thật của một công ty | Có màn hình chưa có dữ liệu nên không quan sát được hành vi thật |
| Hai màn hình chưa khảo sát được tập trường | QĐ5 Thành tích và vi phạm; chi tiết bên trong một số màn hình cấu hình |
| Không xem được mã nguồn | Mọi nhận định về kiến trúc đều suy từ giao diện |
| Chưa có hình chụp | Xem mục trên |
