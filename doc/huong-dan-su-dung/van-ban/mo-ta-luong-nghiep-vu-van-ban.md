# MÔ TẢ LUỒNG NGHIỆP VỤ — QUẢN LÝ VĂN BẢN

| | |
|---|---|
| **Phân hệ** | Văn bản (Văn thư) |
| **Dành cho** | Ban lãnh đạo · Trưởng bộ phận · Văn thư · Người phụ trách quy trình · Đội triển khai |
| **Cập nhật** | 23/09/2026 |
| **Tài liệu liên quan** | Hướng dẫn sử dụng — Quản lý Văn bản (cách bấm từng màn hình) |

**Cách đọc tài liệu này**

- Tài liệu mô tả **văn bản đi qua những bước nào, ai làm bước nào, theo quy tắc gì** — không
  hướng dẫn bấm nút. Muốn biết thao tác cụ thể, xem tài liệu *Hướng dẫn sử dụng*.
- Mỗi quy trình có mã **QT-xx**; mỗi quy tắc nghiệp vụ có mã **QĐ-xx** để tiện trao đổi.
- Trong sơ đồ: mỗi **hàng** là một bên thực hiện; **màu mũi tên** cho biết loại chuyển
  (xanh lá = đi tiếp, cam = trả lại / cần rà, đỏ = từ chối / bãi bỏ, nét đứt = trường hợp riêng).

---

## MỤC LỤC

**PHẦN I. TỔNG QUAN**

1. [Mục đích và phạm vi](#1-mục-đích-và-phạm-vi)
2. [Các bên tham gia](#2-các-bên-tham-gia)
3. [Khái niệm dùng trong tài liệu](#3-khái-niệm-dùng-trong-tài-liệu)
4. [Bản đồ quy trình](#4-bản-đồ-quy-trình)

**PHẦN II. VÒNG ĐỜI VĂN BẢN**

5. [Các trạng thái](#5-các-trạng-thái)
6. [Chuyển trạng thái](#6-chuyển-trạng-thái)

**PHẦN III. CÁC QUY TRÌNH**

7. [QT-01 Soạn thảo](#7-qt-01-soạn-thảo)
8. [QT-02 Trình duyệt](#8-qt-02-trình-duyệt)
9. [QT-03 Ban hành](#9-qt-03-ban-hành)
10. [QT-04 Phân phối cho công ty con](#10-qt-04-phân-phối-cho-công-ty-con)
11. [QT-05 Sửa đổi văn bản](#11-qt-05-sửa-đổi-văn-bản)
12. [QT-06 Tác động dây chuyền](#12-qt-06-tác-động-dây-chuyền)
13. [QT-07 Rà soát](#13-qt-07-rà-soát)
14. [QT-08 Bãi bỏ](#14-qt-08-bãi-bỏ)
15. [QT-09 Trích và sao chép](#15-qt-09-trích-và-sao-chép)

**PHẦN IV. QUY TẮC NGHIỆP VỤ**

16. [Bảng quy tắc nghiệp vụ](#16-bảng-quy-tắc-nghiệp-vụ)

**PHẦN V. THIẾT LẬP ẢNH HƯỞNG TỚI LUỒNG**

17. [Loại văn bản](#17-loại-văn-bản)
18. [Số hiệu và sổ văn bản](#18-số-hiệu-và-sổ-văn-bản)
19. [Quy tắc liên kết](#19-quy-tắc-liên-kết)
20. [Quy trình duyệt](#20-quy-trình-duyệt)

**PHẦN VI. AI ĐƯỢC LÀM GÌ**

21. [Phân quyền trong luồng](#21-phân-quyền-trong-luồng)

---

## PHẦN I. TỔNG QUAN

### 1. Mục đích và phạm vi

Phân hệ Văn bản số hóa toàn bộ vòng đời **văn bản nội bộ do tập đoàn và các công ty thành
viên ban hành**: soạn → duyệt → ban hành (cấp số, vào sổ) → phổ biến tới người phải làm theo →
theo dõi hiệu lực → sửa đổi, thay thế, bãi bỏ.

**Trong phạm vi**

- Văn bản nội bộ: công văn, thông báo, quyết định, quy chế, quy trình, hướng dẫn, biểu mẫu,
  giấy nghỉ phép…
- Ban hành ở công ty mẹ và phân phối để từng công ty con tự ban hành bản của mình.
- Liên kết giữa các văn bản (thay thế, sửa đổi, kèm theo, hướng dẫn…) và tác động tự động.

**Ngoài phạm vi (hiện tại)**

- Công văn đến từ bên ngoài (tiếp nhận, vào sổ đến, giao xử lý).
- Ký số có giá trị pháp lý thực hiện ngay trên hệ thống — hệ thống chỉ **ghi nhận** chữ ký.
- Theo dõi «ai đã đọc văn bản».

### 2. Các bên tham gia

| Bên | Vai trò trong luồng |
|---|---|
| **Người soạn** | Tạo văn bản, soạn nội dung, khai phạm vi áp dụng và liên kết, gửi duyệt, sửa khi bị trả lại |
| **Người chịu trách nhiệm nội dung** | Người trả lời về nội dung văn bản; cùng người soạn có quyền bấm *Ban hành* ở loại «chờ người soạn ban hành» |
| **Người duyệt** | Đọc và quyết định ở từng chặng: duyệt, trả lại, từ chối, ghi ý kiến. Thường là trưởng bộ phận của phòng chủ trì, rồi tới lãnh đạo |
| **Người được ủy quyền** | Duyệt thay người duyệt khi được ủy quyền |
| **Văn thư** | Quản lý sổ văn bản, số hiệu, lưu trữ bản giấy; ở công ty con là người nhận và ban hành bản riêng |
| **Người phải làm theo** | Nhân sự nằm trong phạm vi áp dụng — nhận thông báo, xem văn bản ở mục *Văn bản đến* |
| **Người thiết lập** | Khai loại văn bản, sổ, quy tắc đánh số, quy tắc liên kết, quy trình duyệt |
| **Quản trị phân quyền** | Giao vai trò và phạm vi cho từng tài khoản |
| **Hệ thống** | Tự cấp số, vào sổ, khóa nội dung, gửi thông báo, tạo bản riêng, xử lý văn bản cũ, đánh dấu cần rà lại |

### 3. Khái niệm dùng trong tài liệu

| Khái niệm | Nghĩa |
|---|---|
| **Văn bản** | Một hồ sơ gồm thông tin chung (tên, loại, công ty ban hành, phòng chủ trì…) và một hoặc nhiều **phiên bản** nội dung |
| **Phiên bản** | Một lần nội dung được soạn và duyệt: 1.0, 1.1 (sửa nhỏ), 2.0 (sửa lớn). Phiên bản đã duyệt bị khóa vĩnh viễn |
| **Công ty ban hành** | Pháp nhân **đứng tên** ban hành, quyết định số hiệu |
| **Phạm vi áp dụng** | Ai **phải làm theo** văn bản: theo công ty, phòng ban, cá nhân; có dòng bao gồm và loại trừ |
| **Quyền truy cập** | Ai **được mở ra xem / sửa** — khác với phạm vi áp dụng |
| **Số hiệu** | Số chính thức cấp khi ban hành. Hai kiểu: *theo sổ* (đếm lại mỗi năm) và *mã tài liệu bất biến* (đếm mãi) |
| **Sổ văn bản** | Sổ đến / đi / nội bộ, có bộ đếm riêng; thành viên sổ xem được văn bản trong sổ |
| **Liên kết (quan hệ)** | Mối nối giữa hai văn bản: thay thế, sửa đổi, bổ sung, hướng dẫn, kèm theo, thuộc về, căn cứ theo, tham chiếu, bãi bỏ, trích từ |
| **Bản riêng** | Bản nháp sinh cho từng công ty con khi văn bản gốc ban hành, để công ty con tự ban hành |
| **Bản trích** | Văn bản chứa một phần nội dung của văn bản gốc, mức mật không cao hơn gốc |
| **Cần rà lại** | Nhãn hệ thống gắn cho văn bản khi văn bản gốc / cha của nó thay đổi |

### 4. Bản đồ quy trình

<p align="center"><img src="hinh/nv-01-ban-do-quy-trinh.png" width="760" alt="Bản đồ quy trình"></p>

*Hình 1. Chín quy trình của phân hệ Văn bản và cách chúng nối nhau*

- **Luồng chính**: QT-01 Soạn thảo → QT-02 Trình duyệt → QT-03 Ban hành → QT-06 Tác động dây
  chuyền → QT-04 Phân phối cho công ty con (khi có). Trình duyệt có thể **trả lại** về soạn thảo.
- **Sau khi ban hành**: QT-05 Sửa đổi (sửa nội dung thì đi lại từ trình duyệt), QT-08 Bãi bỏ,
  QT-07 Rà soát (khi văn bản gốc thay đổi), QT-09 Trích và sao chép.
- **Thiết lập nền** quyết định cách các quy trình chạy — xem Phần V.

---

## PHẦN II. VÒNG ĐỜI VĂN BẢN

### 5. Các trạng thái

<p align="center"><img src="hinh/nv-02-vong-doi-trang-thai.png" width="760" alt="Vòng đời trạng thái"></p>

*Hình 2. Các trạng thái của một văn bản và đường chuyển giữa chúng*

Cách đọc sơ đồ:

- **Hàng giữa là đường đi chính**: *Nháp* → *Đang duyệt* → *Có hiệu lực* → một trong ba trạng
  thái kết thúc (*Đã thay thế*, *Hết hiệu lực*, *Bãi bỏ*).
- **Đường vòng phía trên**: duyệt xong nhưng ngày hiệu lực ở tương lai → văn bản nằm ở *Đã
  duyệt*, tới ngày tự chuyển *Có hiệu lực*.
- **Đường vòng phía dưới (nét đứt)**: riêng loại «chờ người soạn ban hành» — duyệt xong dừng ở
  *Chờ ban hành*, người soạn bấm *Ban hành* mới sang *Có hiệu lực*.
- **Phía dưới bên trái**: hai kết quả không duyệt — *Trả về* (sửa rồi gửi lại, mũi tên đi lên)
  và *Đã từ chối* (dừng hẳn).

| Nhóm | Trạng thái | Ý nghĩa | Sửa thông tin | Sửa nội dung | Xóa |
|---|---|---|---|---|---|
| Đang soạn | **Nháp** | Đang soạn | Được | Được | Được, nếu chưa có số |
| | **Trả về** | Người duyệt trả lại để sửa | Được | Được | Được, nếu chưa có số |
| Đang trình | **Đang duyệt** | Chờ người duyệt | Không | Không | Không |
| | **Chờ ban hành** | Đã ký đủ, chờ người soạn bấm ban hành | Không | Không | Không |
| Kết thúc trình | **Đã từ chối** | Bị từ chối hẳn | Không | Không | Không — làm lại bằng Sao chép |
| Đã ban hành | **Đã duyệt** | Có số hiệu, chưa tới ngày hiệu lực | Được | Mở phiên bản mới | Không — chỉ bãi bỏ |
| | **Có hiệu lực** | Đang áp dụng | Được | Mở phiên bản mới | Không — chỉ bãi bỏ |
| Hết hiệu lực | **Đã thay thế** | Có văn bản mới thay | Được | Không | Không |
| | **Hết hiệu lực** | Quá hạn, hoặc cha bị bãi bỏ kéo theo | Được | Không | Không |
| | **Bãi bỏ** | Đã thu hồi | Được | Không | Không |
| | **Lưu trữ** | Đóng hồ sơ | Được | Không | Không |

Ngoài trạng thái, văn bản còn có thể mang nhãn **Cần rà lại** (QT-07) và cảnh báo **«Đã bị sửa
đổi bởi…»** (QT-06). Nhãn không làm đổi trạng thái.

### 6. Chuyển trạng thái

| Từ | Sự kiện | Sang | Ai gây ra |
|---|---|---|---|
| — | Tạo văn bản | Nháp | Người soạn |
| Nháp / Trả về | Gửi duyệt | Đang duyệt | Người soạn |
| Đang duyệt | Rút phiếu | Nháp | Người soạn |
| Đang duyệt | Trả lại | Trả về | Người duyệt |
| Đang duyệt | Từ chối | Đã từ chối | Người duyệt |
| Đang duyệt | Duyệt chặng cuối — loại tự ban hành | Có hiệu lực / Đã duyệt | Người duyệt → hệ thống |
| Đang duyệt | Duyệt chặng cuối — loại chờ người soạn | Chờ ban hành | Người duyệt |
| Chờ ban hành | Bấm Ban hành | Có hiệu lực / Đã duyệt | Người soạn / người chịu trách nhiệm |
| Đã duyệt | Tới ngày hiệu lực | Có hiệu lực | Hệ thống |
| Có hiệu lực | Văn bản mới «thay thế» có hiệu lực | Đã thay thế | Hệ thống |
| Có hiệu lực | Văn bản mới «bãi bỏ» có hiệu lực | Bãi bỏ | Hệ thống |
| Có hiệu lực | Bấm Bãi bỏ | Bãi bỏ | Người có quyền bãi bỏ |
| Có hiệu lực | Quá ngày hết hiệu lực | Hết hiệu lực | Hệ thống |
| Có hiệu lực | Văn bản cha bị bãi bỏ (quy tắc «hết hiệu lực theo») | Hết hiệu lực | Hệ thống |
| Nháp / Trả về chưa có số | Xóa | (không còn) | Người có quyền xóa |

**Phiên bản thứ hai trở đi** đi duyệt riêng: văn bản vẫn giữ **Có hiệu lực** bằng phiên bản cũ
trong suốt lúc phiên bản mới được soạn và duyệt — không có khoảng trống hiệu lực.

---

## PHẦN III. CÁC QUY TRÌNH

### 7. QT-01 Soạn thảo

| | |
|---|---|
| **Mục đích** | Tạo văn bản với đủ thông tin để duyệt và ban hành |
| **Người thực hiện** | Người soạn (có quyền tạo văn bản) |
| **Bắt đầu khi** | Có nhu cầu ban hành văn bản |
| **Kết thúc khi** | Văn bản được gửi duyệt, hoặc bị xóa |
| **Kết quả** | Văn bản ở trạng thái *Nháp*, phiên bản 1.0 |

**Các bước**

| # | Bước | Người làm | Ghi chú |
|---|---|---|---|
| 1 | Khai **thông tin chính**: tên, loại, công ty ban hành, phòng chủ trì, người chịu trách nhiệm, sổ | Người soạn | Hệ thống lưu bản nháp ngay sau bước này |
| 2 | Khai **phạm vi áp dụng** và **quyền truy cập** | Người soạn | Bỏ trống phạm vi = áp cho toàn bộ công ty ban hành |
| 3 | Khai **thông tin bổ sung**: mức mật, độ khẩn, người ký, ngày hiệu lực, hết hạn, nơi lưu bản giấy, tệp đính kèm | Người soạn | |
| 4 | **Soạn nội dung**: gõ trực tiếp, dùng văn bản mẫu, hoặc nhập tệp Word/PDF | Người soạn | Tự lưu liên tục |
| 5 | Khai **liên kết** với văn bản khác (bắt buộc hay tùy chọn theo loại) | Người soạn | Chỉ liên kết tới văn bản đang hiệu lực |

**Ngoại lệ**

- Loại văn bản yêu cầu văn bản cha mà chưa có → hệ thống **cảnh báo** lúc tạo nhưng vẫn cho tạo;
  chỉ **chặn ở lúc gửi duyệt**.
- Loại cấp số «khi tạo bản nháp» → văn bản nhận số ngay ở bước 1; bỏ dở vẫn chiếm số.
- Loại «Giấy nghỉ phép» có thêm thông tin nghỉ (người nghỉ, loại nghỉ, từ ngày – đến ngày, lý do).

**Quy tắc áp dụng**: QĐ-01, QĐ-02, QĐ-10, QĐ-11.

### 8. QT-02 Trình duyệt

| | |
|---|---|
| **Mục đích** | Người có thẩm quyền xem xét và chấp thuận nội dung |
| **Người thực hiện** | Người soạn (gửi), người duyệt từng chặng, hệ thống |
| **Bắt đầu khi** | Người soạn bấm *Gửi duyệt* |
| **Kết thúc khi** | Duyệt hết chặng (→ QT-03), bị trả lại (→ QT-01) hoặc bị từ chối |

Có **hai cách duyệt**, chọn theo thiết lập của từng công ty:

- **Duyệt một bước**: người có quyền duyệt văn bản bấm *Duyệt và ban hành* hoặc *Trả lại*.
- **Duyệt nhiều bước** theo quy trình đã khai (ví dụ trưởng bộ phận → giám đốc):

<p align="center"><img src="hinh/nv-03-trinh-duyet-nhieu-buoc.png" width="760" alt="Trình duyệt nhiều bước"></p>

*Hình 3. Trình duyệt theo quy trình nhiều chặng*

| # | Bước | Người làm | Ghi chú |
|---|---|---|---|
| 1 | Gửi duyệt; văn bản khóa | Người soạn | Kiểm tra: nội dung không rỗng, đủ liên kết bắt buộc |
| 2 | Chọn quy trình duyệt phù hợp và **chụp lại** tại thời điểm gửi | Hệ thống | Chọn theo loại, công ty, phòng, mức mật, độ khẩn… |
| 3 | Tìm người duyệt của chặng | Hệ thống | Không tìm được → người dự phòng, hoặc dừng và báo quản trị |
| 4 | Báo việc cho người duyệt | Hệ thống | Chuông, email; mục *Chờ tôi duyệt* |
| 5 | Đọc và quyết định | Người duyệt | Duyệt · Trả lại · Từ chối · Ghi ý kiến |
| 6 | Còn chặng thì quay lại bước 3 | Hệ thống | |
| 7 | Hết chặng → ban hành hoặc *Chờ ban hành* | Hệ thống | |

**Quy tắc áp dụng**: QĐ-03, QĐ-04, QĐ-05, QĐ-06, QĐ-07.

### 9. QT-03 Ban hành

| | |
|---|---|
| **Mục đích** | Biến văn bản đã duyệt thành văn bản chính thức |
| **Người thực hiện** | Hệ thống (sau chặng duyệt cuối) hoặc người soạn (loại «chờ người soạn ban hành») |
| **Kết quả** | Văn bản có số hiệu, phiên bản khóa, người liên quan được báo |

| # | Việc hệ thống làm |
|---|---|
| 1 | Kiểm tra lần cuối: đủ liên kết bắt buộc; loại «cần quyết định ban hành» phải có quyết định kèm theo |
| 2 | **Cấp số hiệu** (nếu chưa cấp lúc tạo) và **số vào sổ** (nếu có sổ) |
| 3 | **Khóa** phiên bản, lưu dấu nội dung để đối chiếu về sau |
| 4 | Ngày hiệu lực là hôm nay → *Có hiệu lực* và chạy **QT-06**; ngày ở tương lai → *Đã duyệt*, tới ngày mới chạy |
| 5 | Có công ty con trong phạm vi → chạy **QT-04** |
| 6 | Báo cho người trong phạm vi áp dụng (chuông, email); tùy chọn đăng bài lên diễn đàn nội bộ; gửi thư danh nghĩa hộp thư phòng ban nếu người ban hành được cấp |

**Loại «chờ người soạn ban hành»**: người duyệt chỉ duyệt nội dung; **người soạn** quyết thời
điểm phát hành và địa chỉ gửi thông báo. Trong lúc chờ, văn bản khóa như đang duyệt.

**Quy tắc áp dụng**: QĐ-08, QĐ-09, QĐ-12, QĐ-13.

### 10. QT-04 Phân phối cho công ty con

| | |
|---|---|
| **Mục đích** | Mỗi công ty con tự ban hành văn bản của mình với số hiệu, người ký, ngày hiệu lực riêng |
| **Bắt đầu khi** | Văn bản gốc ban hành và phạm vi có công ty khác công ty ban hành |
| **Người thực hiện** | Hệ thống, văn thư công ty con, người duyệt của công ty con |

<p align="center"><img src="hinh/15-luong-ban-hanh-phap-nhan-con.png" width="760" alt="Phân phối cho công ty con"></p>

*Hình 4. Phân phối văn bản cho công ty con*

| # | Bước | Người làm |
|---|---|---|
| 1 | Khai phạm vi *Bao gồm · Pháp nhân* gồm công ty mẹ và các công ty con | Người soạn ở công ty mẹ |
| 2 | Duyệt và ban hành văn bản gốc; hộp ban hành báo trước sẽ sinh bao nhiêu bản riêng | Người duyệt công ty mẹ |
| 3 | Tạo **một bản nháp riêng cho mỗi công ty con**: chép nội dung, tệp, phạm vi; gắn liên kết «căn cứ theo» về văn bản gốc | Hệ thống |
| 4 | Báo cho văn thư công ty con | Hệ thống |
| 5 | Đối chiếu bản gốc, chỉnh cho đúng công ty mình | Văn thư công ty con |
| 6 | Trình duyệt theo quy trình **của công ty con** | Văn thư, người duyệt công ty con |
| 7 | Ban hành với **số hiệu của công ty con** | Hệ thống |
| 8 | Công ty mẹ theo dõi tình trạng từng bản: Đã gửi → Đang soạn → Đang duyệt → Đã ban hành | Công ty mẹ |

**Quy tắc áp dụng**: QĐ-14, QĐ-15.

### 11. QT-05 Sửa đổi văn bản

Có hai mức sửa, **khác hẳn nhau**:

| Sửa gì | Cách làm | Có phải duyệt lại? |
|---|---|---|
| **Thông tin** (tên, phòng, người chịu trách nhiệm, ngày hết hạn, nơi lưu, tệp, phạm vi, quyền…) | Sửa trực tiếp, lưu lại; hệ thống ghi lịch sử thao tác | Không |
| **Nội dung** | Mở **phiên bản mới** (sửa lớn → 2.0, sửa nhỏ → 1.1), ghi «sửa gì», soạn, rồi đi lại QT-02 → QT-03 | Có |

- Không sửa được **loại văn bản** và **công ty ban hành** khi đã có số hiệu.
- Phiên bản cũ vẫn có hiệu lực tới khi phiên bản mới ban hành; có thể đặt ngày hiệu lực tương
  lai cho phiên bản mới.
- **Sửa lớn** yêu cầu người đã đọc bản cũ xác nhận đọc lại.
- Phiên bản mới ban hành → văn bản con, bản riêng, bản trích được xử lý theo **QT-07**.

**Quy tắc áp dụng**: QĐ-02, QĐ-16, QĐ-17.

### 12. QT-06 Tác động dây chuyền

Khi văn bản mới **thật sự có hiệu lực**, hệ thống tự xử lý các văn bản cũ mà nó liên kết tới:

<p align="center"><img src="hinh/nv-04-tac-dong-day-chuyen.png" width="760" alt="Tác động dây chuyền và rà soát"></p>

*Hình 5. Tác động dây chuyền (trên) và rà soát (dưới)*

| Liên kết của văn bản mới | Văn bản cũ |
|---|---|
| **Thay thế** | Chuyển *Đã thay thế* |
| **Bãi bỏ** | Chuyển *Bãi bỏ*, người xem thu hẹp |
| **Sửa đổi / Bổ sung** | Vẫn hiệu lực, gắn cảnh báo «Đã bị sửa đổi bởi…» không tắt được |
| Hướng dẫn, Kèm theo, Thuộc về, Căn cứ theo, Tham chiếu | Không đổi |

Ban hành hôm nay mà hiệu lực tháng sau → **chưa** xử lý; tới đúng ngày mới xử lý, để văn bản cũ
không «chết sớm».

**Quy tắc áp dụng**: QĐ-18, QĐ-19.

### 13. QT-07 Rà soát

| | |
|---|---|
| **Mục đích** | Văn bản dẫn xuất (con, bản riêng, bản trích) không lệch với văn bản gốc |
| **Bắt đầu khi** | Văn bản cha lên phiên bản mới, hoặc bị bãi bỏ |

| Văn bản cha | Văn bản con bị xử lý theo **quy tắc liên kết** |
|---|---|
| Lên phiên bản mới | Không làm gì · Đánh dấu *cần rà lại* · Hỏi người ban hành rồi ghi nhật ký |
| Bị bãi bỏ | Không làm gì · Đánh dấu *cần rà lại* · **Hết hiệu lực theo cha** |

Văn bản bị đánh dấu *cần rà lại* → người phụ trách mở bản gốc đối chiếu, ghi **kết luận rà**
và chọn:

- **Phải sửa theo bản gốc** → mở phiên bản mới, đi lại QT-02 → QT-03;
- **Giữ nguyên** → chỉ gỡ dấu, ghi nhật ký.

**Quy tắc áp dụng**: QĐ-20, QĐ-21.

### 14. QT-08 Bãi bỏ

| | |
|---|---|
| **Mục đích** | Thu hồi văn bản đã ban hành |
| **Người thực hiện** | Người có quyền bãi bỏ; hoặc tự động khi văn bản mới «bãi bỏ» có hiệu lực |
| **Điều kiện** | Văn bản đang *Đã duyệt* hoặc *Có hiệu lực*; bắt buộc ghi lý do |

Kết quả:

1. Văn bản chuyển *Bãi bỏ*, hết hiệu lực từ ngày bãi bỏ; **số hiệu giữ nguyên trong sổ**.
2. Người xem thu hẹp: chỉ người tạo, người chịu trách nhiệm, người bãi bỏ, văn thư và người có
   phạm vi xem toàn công ty trở lên.
3. Văn bản con xử lý theo QT-07; bản trích hết hiệu lực theo.
4. Các công ty con có bản riêng được báo.

**Quy tắc áp dụng**: QĐ-01, QĐ-22.

### 15. QT-09 Trích và sao chép

| | Bản trích | Sao chép |
|---|---|---|
| **Dùng khi** | Cần đưa **một phần** văn bản cho người không được đọc bản đầy đủ | Cần văn bản mới giống văn bản sẵn có; hoặc làm lại văn bản **đã bị từ chối** |
| **Điều kiện** | Văn bản gốc đã ban hành | Bất kỳ |
| **Kết quả** | Văn bản mới cùng loại, mức mật **không cao hơn gốc**, **không có số hiệu riêng** | Bản nháp mới: cùng nội dung, thông tin, tệp, phạm vi, quyền; **không** mang số hiệu, sổ, lịch sử duyệt |
| **Liên hệ về sau** | Gốc lên bản mới → bản trích cần rà lại; gốc bị bãi bỏ → bản trích hết hiệu lực | Không liên hệ với văn bản cũ |

---

## PHẦN IV. QUY TẮC NGHIỆP VỤ

### 16. Bảng quy tắc nghiệp vụ

| Mã | Quy tắc |
|---|---|
| **QĐ-01** | Số hiệu cấp một lần, không cấp lại. Văn bản đã có số **không xóa được**, chỉ bãi bỏ |
| **QĐ-02** | Đã có số hiệu thì không đổi **loại văn bản** và **công ty ban hành** |
| **QĐ-03** | Đang duyệt và chờ ban hành thì **khóa toàn bộ** nội dung, thông tin, tệp — người duyệt ký đúng bản họ đọc |
| **QĐ-04** | Không gửi duyệt được khi nội dung rỗng, hoặc thiếu liên kết bắt buộc của loại văn bản |
| **QĐ-05** | Trả lại và từ chối **bắt buộc ghi lý do** |
| **QĐ-06** | Quy trình duyệt được chụp lại lúc gửi; đổi **cấu trúc** quy trình không ảnh hưởng phiếu đang chạy, nhưng đổi **người duyệt** của một chặng thì phiếu đang chờ ở chặng đó chuyển sang người mới |
| **QĐ-07** | Không tìm được người duyệt thì không tự đẩy lên cấp trên: chỉ chuyển cho người dự phòng đã khai, hoặc dừng và báo quản trị |
| **QĐ-08** | Loại «chờ người soạn ban hành»: chỉ người soạn / người chịu trách nhiệm được bấm ban hành, quyền duyệt không thay được |
| **QĐ-09** | Loại «cần quyết định ban hành» phải có liên kết «kèm theo» tới một Quyết định mới ban hành được |
| **QĐ-10** | Không khai phạm vi = áp cho toàn bộ công ty ban hành. Khai bất kỳ dòng nào là tắt mặc định này |
| **QĐ-11** | Phạm vi: dòng cụ thể hơn thắng (cá nhân > phòng ban > công ty); cùng cấp thì loại trừ thắng |
| **QĐ-12** | Ngày hiệu lực ở tương lai: văn bản chờ tới đúng ngày mới có hiệu lực và mới xử lý văn bản cũ |
| **QĐ-13** | Chữ ký chỉ ghi thêm, không sửa, không xóa; nội dung đổi sau khi ký thì chữ ký bị báo lệch |
| **QĐ-14** | Mỗi công ty con nhận **một** bản riêng; không tạo bản riêng cho chính công ty ban hành |
| **QĐ-15** | Liên kết «căn cứ theo» giữa bản riêng và văn bản gốc do hệ thống tạo, không gỡ được |
| **QĐ-16** | Mỗi văn bản chỉ có **một phiên bản đang sửa** tại một thời điểm |
| **QĐ-17** | Phiên bản đã duyệt khóa vĩnh viễn; phiên bản cũ không bao giờ bị xóa |
| **QĐ-18** | Liên kết không được tạo vòng (A thay B, B thay C, C thay A đều bị chặn) |
| **QĐ-19** | Chỉ liên kết tới văn bản đang hiệu lực |
| **QĐ-20** | Hệ thống **không tự sửa nội dung** văn bản con — chỉ đánh dấu để con người quyết |
| **QĐ-21** | Bản trích luôn: mức mật ≤ bản gốc; gốc bản mới → cần rà lại; gốc bãi bỏ → hết hiệu lực |
| **QĐ-22** | Dòng quyền «Không cho phép» thắng mọi quyền khác, kể cả người tạo và quản trị |

---

## PHẦN V. THIẾT LẬP ẢNH HƯỞNG TỚI LUỒNG

### 17. Loại văn bản

| Thiết lập | Ảnh hưởng tới luồng |
|---|---|
| **Kiểu định danh** | *Số hiệu theo sổ* (đếm lại mỗi năm — công văn, thông báo, quyết định) hoặc *Mã tài liệu bất biến* (đếm mãi — quy chế, quy trình, biểu mẫu) |
| **Cấp số lúc nào** | Khi tạo nháp, hoặc khi được duyệt (khuyến nghị) |
| **Cần quyết định ban hành** | Chặn ban hành nếu chưa có quyết định kèm theo (QĐ-09) |
| **Bảo mật** | Mức mật mặc định tối thiểu là *Mật* |
| **Chờ người soạn ban hành** | Duyệt xong dừng ở *Chờ ban hành* (QĐ-08) |
| **Cần duyệt · Cần ký số** | Nhãn phân loại và thống kê; hiện **không chặn** luồng |
| **Mức mật mặc định** | Tự điền khi tạo văn bản |
| **Chu kỳ rà soát · Thời hạn lưu trữ** | Hiện chỉ ghi nhận, chưa tự nhắc |

### 18. Số hiệu và sổ văn bản

- **Quy tắc đánh số** ghép số từ: số thứ tự, ngày/tháng/năm, mã loại, mã phòng, mã công ty, mã
  sổ. Nhiều quy tắc cùng khớp thì xét **mức ưu tiên**, rồi quy tắc **cụ thể hơn** thắng.
- Có thể cho phép **văn thư sửa số tay** (bắt ghi lý do, không trùng số trong cùng công ty, năm).
- **Sổ văn bản** có bộ đếm riêng theo năm, người quản lý (sửa được) và người xem sổ (chỉ xem).
- Quy tắc và sổ **đã cấp số** thì khóa mẫu số và số bắt đầu, không xóa được.

### 19. Quy tắc liên kết

Mỗi quy tắc khai: loại văn bản nguồn, loại liên kết, loại văn bản đích, **bắt buộc hay tùy
chọn**, số lượng, và cách xử lý khi văn bản đích lên phiên bản mới / bị bãi bỏ (QT-07).

Ví dụ đang dùng: *Quy chế / Quy trình, Chính sách, Quy định, Quy trình* phải **kèm theo đúng 1
Quyết định**; *Biểu mẫu* phải **thuộc về** ít nhất 1 Quy trình; *Hướng dẫn công việc* phải
**hướng dẫn** đúng 1 Quy trình.

### 20. Quy trình duyệt

- Bật **bộ máy duyệt nhiều bước** riêng cho văn bản; tắt thì dùng duyệt một bước.
- Mỗi quy trình gồm các chặng; mỗi chặng chỉ định cách tìm người duyệt (trưởng bộ phận của
  phòng chủ trì, người cụ thể…), người dự phòng, hạn xử lý.
- Điều kiện chọn quy trình: loại văn bản, công ty, phòng, mức mật, độ khẩn, người soạn / chịu
  trách nhiệm / ký.
- Bản riêng ở công ty con phải có quy trình duyệt **của chính công ty con**.

---

## PHẦN VI. AI ĐƯỢC LÀM GÌ

### 21. Phân quyền trong luồng

<p align="center"><img src="hinh/31-ba-lop-quyen.png" width="760" alt="Ai được mở và sửa một văn bản"></p>

*Hình 6. Hai thứ quyết định quyền, và thứ tự hệ thống xét*

| Việc trong luồng | Quyền cần có |
|---|---|
| Xem danh sách, mở văn bản | Xem |
| Tạo, sao chép, tạo bản trích, gửi bản riêng cho công ty con | Tạo |
| Sửa, gửi duyệt, mở phiên bản mới, khai phạm vi / quyền / liên kết, rà lại | Sửa |
| Xóa bản nháp chưa có số | Xóa |
| Duyệt một bước, trả lại, ghi nhận chữ ký | Duyệt |
| Bãi bỏ | Hủy |
| In · Xuất Excel | In · Xuất |
| Duyệt theo quy trình nhiều bước | Được quy trình chỉ định — **không cần** quyền Duyệt |
| Ban hành loại «chờ người soạn ban hành» | Là người soạn / người chịu trách nhiệm |
| Xem văn bản mình phải làm theo | Nằm trong phạm vi áp dụng — không cần vai trò Văn bản |

Mỗi quyền còn đi kèm **phạm vi**: văn bản của mình, của phòng, của công ty hay tất cả. Muốn
«chỉ người tạo được sửa văn bản của mình» thì đặt phạm vi quyền Sửa là *Của mình*.
