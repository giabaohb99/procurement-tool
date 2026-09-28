# MÔ TẢ LUỒNG NGHIỆP VỤ — THƯ MỤC VĂN BẢN

| | |
|---|---|
| **Phân hệ** | Văn bản (Văn thư) → Thư mục văn bản |
| **Dành cho** | Ban lãnh đạo · Trưởng bộ phận · Văn thư · Người quản lý thư mục · Quản trị phân quyền · Đội triển khai |
| **Cập nhật** | 26/09/2026 |
| **Tài liệu liên quan** | Hướng dẫn sử dụng — Thư mục văn bản (cách bấm từng màn hình) · Mô tả luồng nghiệp vụ — Quản lý Văn bản (§24–27 là bản tóm tắt, tài liệu này là bản đầy đủ) |

**Cách đọc tài liệu này**

- Tài liệu mô tả **thư mục được tổ chức thế nào, ai làm gì, theo quy tắc gì** — không hướng dẫn
  bấm nút. Thao tác cụ thể xem *Hướng dẫn sử dụng — Thư mục văn bản*.
- Mỗi quy trình có mã **TM-xx**; mỗi quy tắc có mã **QT-TMxx** (tách khỏi bộ mã QĐ-xx của luồng văn
  bản để khỏi lẫn).
- Trong sơ đồ: mỗi **hàng** là một bên thực hiện; **màu mũi tên** cho biết loại chuyển (xanh = đi
  tiếp, cam = trường hợp riêng, đỏ = chặn / xóa, nét đứt = tùy chọn).

---

## MỤC LỤC

**PHẦN I. TỔNG QUAN**

1. [Mục đích và phạm vi](#1-mục-đích-và-phạm-vi)
2. [Các bên tham gia](#2-các-bên-tham-gia)
3. [Khái niệm dùng trong tài liệu](#3-khái-niệm-dùng-trong-tài-liệu)
4. [Bản đồ quy trình](#4-bản-đồ-quy-trình)

**PHẦN II. CẤU TRÚC CÂY**

5. [Các loại thư mục](#5-các-loại-thư-mục)
6. [Trạng thái thư mục](#6-trạng-thái-thư-mục)
7. [Văn bản và thư mục](#7-văn-bản-và-thư-mục)

**PHẦN III. CÁC QUY TRÌNH**

8. [TM-01 Dựng cây thư mục](#8-tm-01-dựng-cây-thư-mục)
9. [TM-02 Xếp văn bản khi tạo](#9-tm-02-xếp-văn-bản-khi-tạo)
10. [TM-03 Sắp xếp lại văn bản](#10-tm-03-sắp-xếp-lại-văn-bản)
11. [TM-04 Tổ chức lại cây](#11-tm-04-tổ-chức-lại-cây)
12. [TM-05 Ngừng dùng và khôi phục](#12-tm-05-ngừng-dùng-và-khôi-phục)
13. [TM-06 Xóa thư mục](#13-tm-06-xóa-thư-mục)
14. [TM-07 Chia sẻ và thu hồi quyền](#14-tm-07-chia-sẻ-và-thu-hồi-quyền)
15. [TM-08 Tìm văn bản theo thư mục](#15-tm-08-tìm-văn-bản-theo-thư-mục)
16. [TM-09 Phản ứng theo văn bản](#16-tm-09-phản-ứng-theo-văn-bản)

**PHẦN IV. QUY TẮC NGHIỆP VỤ**

17. [Bảng quy tắc](#17-bảng-quy-tắc)
18. [Giới hạn và con số](#18-giới-hạn-và-con-số)

**PHẦN V. PHÂN QUYỀN**

19. [Hai lớp quyền](#19-hai-lớp-quyền)
20. [Cách tính mức quyền trên một thư mục](#20-cách-tính-mức-quyền-trên-một-thư-mục)
21. [Quyền chung và kế thừa](#21-quyền-chung-và-kế-thừa)
22. [Việc gì cần quyền gì](#22-việc-gì-cần-quyền-gì)
23. [Thấy một phần](#23-thấy-một-phần)

**PHẦN VI. ĐIỂM CẦN LƯU Ý**

24. [Hệ quả dễ bất ngờ](#24-hệ-quả-dễ-bất-ngờ)
25. [Câu hỏi còn mở](#25-câu-hỏi-còn-mở)

---

## PHẦN I. TỔNG QUAN

### 1. Mục đích và phạm vi

Thư mục văn bản cho phép **xếp văn bản theo cách tổ chức làm việc** (theo phòng, theo loại hồ
sơ, theo năm, theo dự án) để tìm lại nhanh — thay cho việc chỉ lọc theo loại, trạng thái, số hiệu.

**Trong phạm vi**

- Một cây thư mục dùng chung cả tập đoàn, mỗi pháp nhân một nhánh, thêm các thư mục dùng chung
  nhiều pháp nhân.
- Một văn bản nằm ở nhiều thư mục, một thư mục chính.
- Phân quyền riêng cho thư mục (ba mức, cho / cấm, có thời hạn, kế thừa theo nhánh).
- Tìm, lọc, tìm toàn văn trong một thư mục hoặc cả nhánh.
- Tạo văn bản ngay trong thư mục, kể cả văn bản chỉ gồm tệp.

**Ngoài phạm vi (hiện tại)**

- Thư mục **không** thay phân quyền văn bản: có quyền thư mục không đọc được văn bản (QT-TM20).
- Thư mục **không** ảnh hưởng luồng soạn — duyệt — ban hành, số hiệu, sổ văn bản.
- Không có thùng rác cho thư mục: xóa là mất thư mục (văn bản không mất).
- Chưa có hạn mức dung lượng theo thư mục, chưa có thống kê theo thư mục.

### 2. Các bên tham gia

| Bên | Vai trò |
|---|---|
| **Người dùng** | Mở cây, tìm văn bản. Có mức Đóng góp thì xếp văn bản vào / ra, tạo thư mục con, tạo văn bản ngay trong thư mục |
| **Người quản lý thư mục** | Có mức **Quản lý** trên một nhánh: đổi tên, chuyển, sắp thứ tự, ngừng dùng, xóa, chia sẻ nhánh đó. Thường là trưởng bộ phận hoặc văn thư của phòng |
| **Quản trị thư mục** | Vai trò có quyền **Sửa «Văn thư › Cây thư mục»** — luôn mức Quản lý trên mọi thư mục thuộc pháp nhân trong phạm vi vai trò, không bị dòng Cấm chặn |
| **Người thiết lập** | Khai **thư mục mặc định** cho từng loại văn bản ở danh mục Loại văn bản |
| **Quản trị phân quyền** | Giao quyền «Cây thư mục» cho vai trò ở màn Phân quyền |
| **Hệ thống** | Tự tạo nhóm «Công ty» và thư mục pháp nhân, tự xếp văn bản mới vào thư mục mặc định, chống văn bản mồ côi, tính mức quyền, lọc số đếm theo quyền |

### 3. Khái niệm dùng trong tài liệu

| Khái niệm | Nghĩa |
|---|---|
| **Cây thư mục** | Toàn bộ thư mục, xếp cha — con. Một cây chung cho cả tập đoàn |
| **Nhóm «Công ty»** | Thư mục hệ thống ở gốc cây, chứa các thư mục pháp nhân |
| **Thư mục pháp nhân** | Thư mục hệ thống, mỗi pháp nhân một cái, là nơi mặc định của văn bản pháp nhân đó |
| **Thư mục tự do** | Thư mục người dùng tạo ở gốc cây, không thuộc pháp nhân nào |
| **Nhánh** | Một thư mục cùng mọi thư mục con cháu của nó |
| **Liên kết thư mục** | Việc một văn bản «nằm trong» một thư mục. Không phải bản sao |
| **Thư mục chính** | Liên kết được đánh dấu chính của một văn bản — đường dẫn hiện ở danh sách Văn bản |
| **Văn bản mồ côi** | Văn bản không còn nằm ở thư mục nào. Hệ thống không để xảy ra, trừ văn bản chưa gắn pháp nhân |
| **Mức quyền** | Xem · Đóng góp · Quản lý (mức sau gồm mức trước). «Riêng tư» = không mức nào |
| **Quyền chung** | Mức mặc định cho mọi người «với tới» pháp nhân của thư mục |
| **Dòng quyền** | Một lần chia sẻ: đối tượng (người / phòng ban / pháp nhân / vai trò), chiều (Cho / Cấm), mức, hiệu lực từ – đến, lý do |
| **Với tới pháp nhân** | Phạm vi quyền **Xem văn bản** của người đó bao trùm pháp nhân ấy |

### 4. Bản đồ quy trình

<p align="center"><img src="hinh/tm-nv-02-ban-do-quy-trinh.png" width="760" alt="Bản đồ quy trình thư mục"></p>

*Hình 1. Chín quy trình của thư mục văn bản và ai làm*

- **Người quản lý** dựng cây (TM-01), chia quyền (TM-07), tổ chức lại khi cần (TM-04), ngừng dùng
  hoặc xóa thư mục hết dùng (TM-05, TM-06).
- **Người dùng** xếp văn bản lúc tạo (TM-02), sắp xếp lại sau (TM-03), tìm văn bản (TM-08).
- **Hệ thống** lo phần nền: tạo thư mục pháp nhân khi cần, không để văn bản mồ côi, cập nhật thư
  mục khi văn bản đổi pháp nhân / được sao chép / bị xóa (TM-09).

---

## PHẦN II. CẤU TRÚC CÂY

### 5. Các loại thư mục

<p align="center"><img src="hinh/tm-nv-01-cau-truc-cay.png" width="760" alt="Cấu trúc cây"></p>

*Hình 2. Bốn loại thư mục và quan hệ văn bản — thư mục*

| Loại | Ai tạo | Thuộc pháp nhân | Quyền chung mặc định | Đổi tên | Chuyển | Ngừng dùng | Xóa |
|---|---|---|---|---|---|---|---|
| **Nhóm «Công ty»** | Hệ thống | Không | Xem | Được* | Không | Được* | Không |
| **Thư mục pháp nhân** | Hệ thống, khi cần | Có (đúng một) | Đóng góp | Được | Được | Được | Không |
| **Thư mục thường** | Người dùng | Theo thư mục cha lúc tạo | Kế thừa | Được | Được | Được | Được, khi hết thư mục con |
| **Thư mục tự do** | Người dùng | Không | Riêng tư | Được | Được | Được | Được, khi hết thư mục con |

\* Chỉ quản trị toàn hệ thống có mức Quản lý trên nhóm «Công ty». Xem §24.

**Tên hiển thị**: thư mục pháp nhân chưa đặt tên riêng thì hiện **tên ngắn** của pháp nhân (chưa
khai tên ngắn thì hiện tên đầy đủ); đặt tên riêng thì tên riêng thắng. Đường dẫn, kết quả tìm vẫn
ghi tên đầy đủ của pháp nhân.

**Độ sâu**: tối đa **100 cấp** tính cả gốc (mở từ 7 lên 100 ngày 26/09/2026, ngang Google Drive). Nhóm «Công ty» là cấp 1, thư mục pháp nhân cấp 2 → nhánh
công ty còn 98 cấp cho người dùng; thư mục tự do bắt đầu ở cấp 1 → dùng được đủ 100 cấp.

### 6. Trạng thái thư mục

| Trạng thái | Nghĩa | Thấy trên cây | Nhận văn bản mới | Tạo thư mục con |
|---|---|---|---|---|
| **Đang dùng** | Bình thường | Có | Có | Có |
| **Ngừng dùng** | Hết dùng, giữ để tra cứu | Chỉ khi bật «Hiện thư mục ngừng dùng» | Không | Không |

- Ngừng dùng **kéo theo cả nhánh**; khôi phục chỉ bật lại **đúng thư mục đó** (QT-TM11).
- Văn bản đang nằm trong thư mục ngừng dùng vẫn giữ nguyên liên kết; văn bản đó vẫn lưu được
  thông tin bình thường.

### 7. Văn bản và thư mục

| Nguyên tắc | Nội dung |
|---|---|
| **Liên kết, không sao chép** | Văn bản có một bản duy nhất; mỗi thư mục chứa nó là một liên kết |
| **Nhiều thư mục** | Một văn bản nằm ở bao nhiêu thư mục cũng được, kể cả thư mục của pháp nhân khác và thư mục tự do |
| **Một thư mục chính** | Đúng một liên kết là chính. Gỡ thư mục chính → liên kết **sớm nhất** còn lại lên làm chính |
| **Không mồ côi** | Gỡ liên kết cuối cùng → văn bản tự về thư mục pháp nhân của nó |
| **Ngoại lệ mồ côi** | Văn bản **chưa gắn pháp nhân** (ví dụ giấy nghỉ phép cá nhân) không có thư mục pháp nhân để về, nên có thể không nằm ở thư mục nào — cố ý |
| **Không phụ thuộc trạng thái** | Thêm / gỡ / chuyển thư mục làm được ở **mọi trạng thái** văn bản, kể cả đã ban hành, bãi bỏ — thư mục không phải nội dung văn bản |

---

## PHẦN III. CÁC QUY TRÌNH

### 8. TM-01 Dựng cây thư mục

| | |
|---|---|
| **Mục đích** | Tạo khung thư mục phù hợp cách làm việc của từng phòng / pháp nhân |
| **Người thực hiện** | Người có quyền Tạo «Cây thư mục» + mức Đóng góp trên thư mục cha |
| **Bắt đầu khi** | Phòng / pháp nhân cần chỗ xếp văn bản |
| **Kết quả** | Thư mục mới, đang dùng, quyền chung kế thừa (hoặc Riêng tư nếu ở gốc cây) |

**Các bước**

| # | Bước | Người làm | Ghi chú |
|---|---|---|---|
| 1 | Chọn thư mục cha (hoặc gốc cây) | Người dùng | Thư mục cha phải đang dùng |
| 2 | Đặt tên | Người dùng | 1–150 ký tự, không trùng anh em đang dùng (QT-TM03) |
| 3 | Tạo | Hệ thống | Kế thừa pháp nhân của cha; xếp cuối danh sách anh em |
| 4 | (Ở gốc cây) Cấp mức Quản lý cho người tạo | Hệ thống | Ghi dòng quyền đích danh, lý do «Người tạo thư mục» |
| 5 | Chia quyền nếu cần | Người quản lý | Xem TM-07 |

**Ngoại lệ**

- Thư mục cha ngừng dùng → chặn: *«Thư mục cha đang ngừng dùng, không tạo thư mục con được»*.
- Vượt 100 cấp → chặn: *«Cây thư mục sâu tối đa 100 cấp (tính cả gốc)»*.
- Tạo ở gốc cây mà tài khoản chưa gắn hồ sơ nhân sự → chặn (không có ai để cấp mức Quản lý).
- Thư mục pháp nhân **không** tạo tay được — hệ thống tạo ở TM-02 / TM-09.

**Quy tắc áp dụng**: QT-TM01, QT-TM02, QT-TM03, QT-TM04.

### 9. TM-02 Xếp văn bản khi tạo

| | |
|---|---|
| **Mục đích** | Mỗi văn bản mới có ngay chỗ trong cây |
| **Người thực hiện** | Người soạn; hệ thống khi người soạn không chọn |
| **Bắt đầu khi** | Tạo văn bản (trang tạo 3 bước, «Văn bản mới tại đây», «Tạo nhanh từ tệp») |
| **Kết quả** | Văn bản có ít nhất một thư mục (trừ văn bản chưa gắn pháp nhân) |

**Các bước**

| # | Bước | Người làm | Ghi chú |
|---|---|---|---|
| 1 | Chọn một hoặc nhiều thư mục, đánh dấu một thư mục chính | Người soạn | Chỉ chọn được thư mục mình có mức Đóng góp. Tạo từ trong thư mục thì điền sẵn |
| 2 | Kiểm tra: thư mục tồn tại, đang dùng, người soạn đủ mức Đóng góp | Hệ thống | Thư mục không thấy và thư mục không tồn tại báo **cùng một câu** — không dò được thư mục ẩn |
| 3 | Không chọn → chọn thư mục mặc định | Hệ thống | Theo bảng dưới |
| 4 | Lưu văn bản và liên kết thư mục **trong cùng một lần lưu** | Hệ thống | Lỗi thư mục thì văn bản cũng không được tạo |

**Thư mục mặc định khi người soạn không chọn**

| Thứ tự | Nguồn | Điều kiện |
|---|---|---|
| 1 | Thư mục mặc định của **loại văn bản** | Loại có khai; thư mục đang dùng; **cùng pháp nhân** với văn bản |
| 2 | **Thư mục pháp nhân** của văn bản | Chưa có thì hệ thống tạo ngay |
| — | Không thư mục nào | Văn bản chưa gắn pháp nhân |

Thư mục mặc định của loại **không** thể là thư mục tự do (vì thư mục tự do không cùng pháp nhân
với văn bản nào). Hệ thống không kiểm thư mục mặc định lúc khai loại văn bản — khai sai thì chỉ
lặng lẽ rơi xuống bước 2.

**Quy tắc áp dụng**: QT-TM05, QT-TM06, QT-TM07.

### 10. TM-03 Sắp xếp lại văn bản

| | |
|---|---|
| **Mục đích** | Thêm văn bản vào thư mục khác, chuyển chỗ, gỡ ra, đổi thư mục chính |
| **Người thực hiện** | Người có quyền **Sửa** văn bản đó + mức **Đóng góp** trên thư mục liên quan |
| **Nơi làm** | Màn Thư mục (kéo thả, thanh thao tác), màn Văn bản (tick → Thêm vào thư mục), chi tiết văn bản (Sửa thư mục) |

**Bốn thao tác**

| Thao tác | Tác động | Điều kiện riêng |
|---|---|---|
| **Thêm** | Gắn thêm liên kết; thành chính chỉ khi văn bản chưa có thư mục chính | Đóng góp trên thư mục đích |
| **Chuyển** | Thêm vào đích, **thành công rồi mới** gỡ khỏi thư mục nguồn | Đóng góp trên đích và nguồn |
| **Gỡ** | Xóa liên kết; gỡ chính → liên kết sớm nhất lên chính; gỡ cuối cùng → về thư mục pháp nhân | Đóng góp trên thư mục bị gỡ |
| **Đặt lại toàn bộ** (hộp Sửa thư mục) | Thay danh sách thư mục + thư mục chính | Đóng góp trên mỗi thư mục **mới thêm** và mỗi thư mục **bị gỡ** |

**Làm hàng loạt**: tối đa 500 văn bản một lượt. Văn bản không đủ quyền bị **từ chối riêng**, các văn
bản còn lại vẫn làm; kết quả báo «đã làm n · bị từ chối m» mà không nêu lý do chi tiết.

**Liên kết tới thư mục người dùng không thấy được giữ nguyên** khi họ đặt lại thư mục cho văn
bản (QT-TM09). Nếu thư mục chính cũ nằm trong số đó, nó vẫn là chính.

**Quy tắc áp dụng**: QT-TM08, QT-TM09, QT-TM10, QT-TM20.

### 11. TM-04 Tổ chức lại cây

| | |
|---|---|
| **Mục đích** | Đổi cha, đổi thứ tự khi cách tổ chức thay đổi |
| **Người thực hiện** | Mức **Quản lý** trên thư mục chuyển + **Đóng góp** trên cha mới; đổi thứ tự cần **Quản lý** trên cha chung |

**Chuyển thư mục**

- Chuyển được **tới bất kỳ đâu**: sang nhánh pháp nhân khác, ra gốc cây, kể cả chuyển thư mục pháp
  nhân. Cả nhánh (thư mục con + liên kết văn bản) đi theo.
- Bị chặn khi: chuyển vào chính nó / con cháu của nó; đích ngừng dùng; vượt 100 cấp (tính theo độ cao
  cả nhánh); trùng tên ở chỗ mới; chuyển nhóm «Công ty».
- **Pháp nhân của thư mục KHÔNG đổi** khi chuyển (QT-TM12) — quyền chung vẫn tính theo pháp nhân gốc.
- Thư mục tự do chuyển ra gốc cây → người chuyển được tự cấp mức Quản lý.
- Trước khi chuyển nhánh có văn bản, giao diện nhắc số văn bản sẽ đi theo.

**Đổi thứ tự**: chỉ giữa các thư mục **cùng cha**. Đổi thứ tự các thư mục pháp nhân = quản lý
nhóm «Công ty» → chỉ quản trị toàn hệ thống.

**Quy tắc áp dụng**: QT-TM02, QT-TM03, QT-TM12.

### 12. TM-05 Ngừng dùng và khôi phục

| | |
|---|---|
| **Mục đích** | Cất thư mục hết dùng mà vẫn giữ cho tra cứu |
| **Người thực hiện** | Mức **Quản lý** |

- **Ngừng dùng** áp cho thư mục **và mọi thư mục con cháu**. Nhật ký ghi «(cùng n thư mục con)».
- **Khôi phục** chỉ áp cho đúng thư mục được bấm.
- Liên kết văn bản giữ nguyên. Văn bản không thể được **thêm mới** vào thư mục ngừng dùng.
- Không có bước hỏi lại.

**Quy tắc áp dụng**: QT-TM11.

### 13. TM-06 Xóa thư mục

| | |
|---|---|
| **Mục đích** | Bỏ hẳn một thư mục mà không làm mất văn bản |
| **Người thực hiện** | Quyền **Xóa «Cây thư mục»** + mức **Quản lý**; nếu chọn nơi nhận văn bản thì cần **Đóng góp** ở đó |
| **Kết quả** | Thư mục bị xóa vĩnh viễn; mọi văn bản vẫn còn, có chỗ ở |

<p align="center"><img src="hinh/tm-nv-04-luong-xoa.png" width="760" alt="Luồng xóa thư mục"></p>

*Hình 3. Xóa một thư mục thì văn bản trong đó đi đâu*

**Các bước**

| # | Bước | Người làm | Ghi chú |
|---|---|---|---|
| 1 | Bấm Xóa | Người xóa | |
| 2 | Kiểm chặn | Hệ thống | Thư mục pháp nhân / nhóm «Công ty» → *«Thư mục công ty do hệ thống quản lý, không xóa được»*. Còn thư mục con (kể cả ngừng dùng) → *«Thư mục còn thư mục con, không xóa được»* |
| 3 | Xem trước: đếm văn bản và văn bản sẽ mồ côi | Hệ thống | Đếm **toàn hệ thống**, không lọc theo quyền người xóa (QT-TM13) |
| 4 | Chọn nơi nhận văn bản mồ côi | Người xóa | Chỉ khi có văn bản mồ côi. Không được là chính thư mục đang xóa, không được là thư mục ngừng dùng |
| 5 | Với văn bản còn ở thư mục khác: gỡ liên kết; nếu là thư mục chính → liên kết sớm nhất lên chính | Hệ thống | |
| 6 | Với văn bản mồ côi: gắn vào nơi nhận, làm thư mục chính | Hệ thống | Không chọn nơi nhận (xóa hàng loạt) → về **thư mục pháp nhân** của từng văn bản |
| 7 | Xóa thư mục, ghi nhật ký | Hệ thống | Nhật ký: «Xóa thư mục X (n văn bản), chuyển k văn bản sang «Y»» |

**Ngoại lệ**

- Văn bản chưa gắn pháp nhân mà mồ côi, không có nơi nhận → không còn thư mục nào.
- Hệ thống **không kiểm quyền sửa từng văn bản** khi chuyển văn bản mồ côi — người đủ quyền xóa thư
  mục được coi là đủ quyền dọn chỗ cho văn bản trong đó.

**Quy tắc áp dụng**: QT-TM08, QT-TM13, QT-TM14.

### 14. TM-07 Chia sẻ và thu hồi quyền

| | |
|---|---|
| **Mục đích** | Quyết định ai thấy / ai xếp được văn bản / ai quản lý một nhánh |
| **Người thực hiện** | Quyền **Sửa «Cây thư mục»** + mức **Quản lý** trên thư mục |

**Các bước**

| # | Bước | Ghi chú |
|---|---|---|
| 1 | Đặt **quyền chung** nếu cần (Kế thừa / Riêng tư / Xem / Đóng góp) | Riêng tư = khóa nhánh khỏi người chỉ có quyền theo pháp nhân |
| 2 | Chọn một hoặc nhiều đối tượng: người, phòng ban, pháp nhân, vai trò | Tối đa 200 đối tượng một lượt, trộn loại được |
| 3 | Chọn chiều **Cho** (kèm mức) hoặc **Cấm** | Dòng Cấm không có mức |
| 4 | (Tùy chọn) hiệu lực từ – đến, lý do | Ngày đến phải sau ngày từ |
| 5 | Cấp | Đối tượng đã có dòng **cùng chiều** còn hiệu lực → cập nhật dòng đó, không tạo trùng. Đối tượng không tồn tại → bỏ qua, có báo |
| 6 | Đổi mức / thu hồi về sau | Thu hồi = **đánh dấu** kèm người và thời điểm, dòng vẫn lưu |

- Dòng quyền đặt ở một thư mục **áp xuống cả nhánh**. Muốn sửa dòng kế thừa thì sửa ở thư mục cha
  đã đặt nó.
- Một đối tượng có thể có **cả** dòng Cho lẫn dòng Cấm trên cùng thư mục — Cấm thắng.
- Đổi quyền có hiệu lực **ngay** ở lần mở kế tiếp (mức thư mục không lưu tạm).

**Quy tắc áp dụng**: QT-TM15 → QT-TM19.

### 15. TM-08 Tìm văn bản theo thư mục

| Cách | Phạm vi | Ghi chú |
|---|---|---|
| Duyệt cây | Thư mục thấy được; văn bản hiện trên cây (tối đa 100 / thư mục, còn lại «Xem thêm») | |
| Mở thư mục | Văn bản nằm **trực tiếp** trong thư mục | Bật «Gồm thư mục con» để lấy cả nhánh |
| Tìm trong thư mục | Tên, số hiệu; từ 2 ký tự → cả nội dung soạn thảo và chữ trong tệp | Không dấu, cụm «…», loại trừ bằng dấu trừ đầu từ |
| Lọc ở màn Văn bản | Ô «Thư mục» + «Gồm cả văn bản trong thư mục con» | Cột «Thư mục» hiện đường dẫn thư mục chính |
| Tìm tên thư mục | Ô lọc trên cây, ô chọn thư mục | Không dấu, tối đa 50 kết quả |

- Mọi cách đều **chỉ trả văn bản người đó được đọc** (QT-TM20).
- «Gồm thư mục con» chỉ gom các thư mục con **thấy được**.
- Thư mục không thấy được → kết quả rỗng, không báo lỗi (không dò được thư mục ẩn).
- Tìm toàn văn không đọc được PDF scan (không nhận dạng chữ) và tệp quá 20 MB.

### 16. TM-09 Phản ứng theo văn bản

Hệ thống tự cập nhật thư mục khi văn bản có sự kiện:

| Sự kiện của văn bản | Hệ thống làm gì với thư mục |
|---|---|
| **Tạo** | Theo TM-02; thư mục pháp nhân chưa có thì tạo ngay |
| **Đổi pháp nhân ban hành** (chỉ khi chưa có số hiệu) | Văn bản đang nằm **đúng một** thư mục và đó là thư mục pháp nhân cũ → chuyển sang thư mục pháp nhân mới. Đã được xếp vào thư mục khác → giữ nguyên |
| **Sao chép · tạo bản trích · tạo bản riêng cho công ty con** | Văn bản mới vào **thư mục pháp nhân** của nó (không theo thư mục của bản gốc, không theo thư mục mặc định của loại) |
| **Xóa văn bản** (nháp / trả về chưa có số) | Xóa mọi liên kết thư mục của nó |
| **Bãi bỏ, hết hiệu lực, bị thay thế** | Không đổi gì — văn bản vẫn nằm ở thư mục cũ |
| **Được chia đích danh cho một người** | Người đó tự thấy (mức Xem) thư mục chứa văn bản và các thư mục cha — không tạo dòng quyền nào; thu hồi chia sẻ thì tự mất |

---

## PHẦN IV. QUY TẮC NGHIỆP VỤ

### 17. Bảng quy tắc

| Mã | Quy tắc |
|---|---|
| **QT-TM01** | Cả tập đoàn dùng **một cây**. Gốc cây gồm đúng một nhóm «Công ty» và các thư mục tự do |
| **QT-TM02** | Cây sâu tối đa **100 cấp**, tính cả gốc. Áp cả khi tạo lẫn khi chuyển (tính theo độ cao cả nhánh) |
| **QT-TM03** | Tên thư mục 1–150 ký tự, **không trùng** thư mục anh em **đang dùng** — so không phân biệt hoa/thường, bỏ dấu, «đ» = «d» |
| **QT-TM04** | Mỗi pháp nhân có **tối đa một** thư mục pháp nhân, do hệ thống tạo, nằm trong nhóm «Công ty» |
| **QT-TM05** | Mỗi văn bản có pháp nhân luôn có **ít nhất một** thư mục (không mồ côi) |
| **QT-TM06** | Không chọn thư mục khi tạo → thư mục mặc định của loại (cùng pháp nhân, đang dùng), không có thì thư mục pháp nhân |
| **QT-TM07** | Văn bản chưa gắn pháp nhân **không** tự vào thư mục nào |
| **QT-TM08** | Mỗi văn bản có **đúng một** thư mục chính; mất thư mục chính → liên kết sớm nhất còn lại lên thay |
| **QT-TM09** | Người dùng sửa thư mục của văn bản **không làm mất** liên kết tới thư mục họ không thấy |
| **QT-TM10** | Thêm / gỡ / chuyển văn bản cần **cả** quyền Sửa văn bản **và** mức Đóng góp trên thư mục |
| **QT-TM11** | Ngừng dùng kéo theo cả nhánh; khôi phục chỉ một thư mục. Thư mục ngừng dùng không nhận văn bản mới, không nhận thư mục con |
| **QT-TM12** | Chuyển thư mục **không đổi** pháp nhân của thư mục |
| **QT-TM13** | Xóa thư mục **không xóa văn bản**; chỉ xóa được thư mục không còn thư mục con; không xóa được thư mục pháp nhân và nhóm «Công ty» |
| **QT-TM14** | Số đếm lúc xóa thư mục tính **toàn hệ thống** — văn bản người xóa không thấy vẫn là văn bản thật cần chỗ ở |
| **QT-TM15** | Ba mức Xem ⊂ Đóng góp ⊂ Quản lý; quyền đặt ở cha **áp xuống** cả nhánh |
| **QT-TM16** | **Cấm thắng Cho**: một dòng Cấm ở thư mục hoặc tổ tiên → thư mục biến mất với người đó |
| **QT-TM17** | Quản trị thư mục (Sửa «Cây thư mục») luôn mức **Quản lý** trong phạm vi pháp nhân của vai trò, **không bị Cấm chặn** |
| **QT-TM18** | Người không có quyền ghi nào (tạo/sửa thư mục, tạo/sửa văn bản) → mức tối đa **Xem** |
| **QT-TM19** | Được chia đích danh một văn bản → thấy (Xem) thư mục chứa nó và tổ tiên, trừ khi bị Cấm |
| **QT-TM20** | **Quyền thư mục không mở quyền đọc văn bản.** Mọi số đếm, bảng, kết quả tìm lọc theo quyền đọc từng văn bản |

### 18. Giới hạn và con số

| Giới hạn | Giá trị |
|---|---|
| Độ sâu cây | 100 cấp (tính cả gốc) |
| Độ dài tên thư mục · mã · mô tả | 150 · 50 · 500 ký tự |
| Văn bản mỗi lượt thao tác hàng loạt | 500 |
| Thư mục mỗi lượt chuyển hàng loạt | 50 |
| Đối tượng mỗi lượt cấp quyền | 200 |
| Thư mục mỗi lần sắp thứ tự | 500 |
| Thư mục chọn cho một văn bản | 500 |
| Văn bản hiện dưới một thư mục trên cây | 100 (còn lại «Xem thêm») |
| Kết quả tìm tên thư mục | 50, xếp: trùng hẳn tên → bắt đầu bằng → chứa; cùng hạng thì thư mục gần gốc trước |
| Tìm toàn văn | từ 2 ký tự; tệp ≤ 20 MB; không đọc PDF scan |
| Bề rộng khung cây | 200–480 điểm ảnh (mặc định 288) |

---

## PHẦN V. PHÂN QUYỀN

### 19. Hai lớp quyền

Mỗi thao tác trên thư mục qua **hai cửa**:

1. **Quyền vai trò** ở màn Phân quyền — dòng **«Văn thư › Cây thư mục»** (và «Văn bản» cho việc xếp
   văn bản). Trả lời câu hỏi *«người này có được làm loại việc này không»*.
2. **Mức trên thư mục cụ thể** — Xem / Đóng góp / Quản lý. Trả lời câu hỏi *«trên thư mục này thì
   sao»*.

Thiếu cửa 1 → không có nút / bị từ chối. Không thấy thư mục → báo *không tìm thấy* (không lộ thư
mục tồn tại). Thấy nhưng thiếu mức → *«Cần quyền … trở lên trên thư mục này — bạn đang ở mức …»*.

Vai trò có sẵn: mọi vai trò **Xem** «Cây thư mục» (phạm vi Tất cả); vai trò **«Văn bản — soạn & sửa
(không xóa, không duyệt)»** có Xem / Tạo / Sửa / Xóa trong phạm vi **Công ty**. «Cây thư mục» cố ý
**không** nằm trong bộ quyền đầy đủ của Quản lý thu mua. Trên hệ đang chạy, vai trò cũ không tự có
quyền mới — phải tick ở màn Phân quyền.

### 20. Cách tính mức quyền trên một thư mục

<p align="center"><img src="hinh/tm-nv-03-tinh-muc-quyen.png" width="760" alt="Cách tính mức quyền"></p>

*Hình 4. Sáu bước hệ thống xét cho mỗi người, trên mỗi thư mục*

| # | Bước | Chi tiết |
|---|---|---|
| 1 | **Quyền chung** | Chỉ áp nếu người đó **với tới** pháp nhân của thư mục (§21). Lấy quyền chung của thư mục gần nhất (tự nó → cha → ông…) có khai; không ai khai = Riêng tư |
| 2 | **Dòng Cho** | Mọi dòng Cho còn hiệu lực trên thư mục và tổ tiên, khớp **người / phòng ban (kể cả kiêm nhiệm) / pháp nhân chính / vai trò** của họ → lấy mức cao nhất, so với bước 1 lấy cao hơn. Dòng Cho mở được thư mục cho người **không** với tới pháp nhân |
| 3 | **Dòng Cấm** | Có một dòng Cấm còn hiệu lực trên thư mục hoặc tổ tiên → **không thấy** |
| 4 | **Quản trị thư mục** | Vai trò có Sửa «Cây thư mục» với tới pháp nhân của thư mục → **Quản lý**, bỏ qua bước 3. Phạm vi *Tất cả* → Quản lý cả thư mục tự do |
| 5 | **Trần vai trò** | Không có quyền nào trong: Tạo/Sửa «Cây thư mục», Tạo/Sửa «Văn bản» → hạ xuống tối đa **Xem**. Trần chỉ hạ, không làm mất quyền thấy |
| 6 | **Xem ngầm định** | Được chia đích danh một văn bản (còn hiệu lực, không bị chặn) → thư mục chứa nó và mọi tổ tiên ít nhất **Xem** — trừ thư mục bị Cấm |

**Nhóm «Công ty»**: quản trị toàn hệ → Quản lý; thấy ít nhất một thư mục pháp nhân → Xem; còn lại
→ ẩn.

### 21. Quyền chung và kế thừa

| Thư mục | Quyền chung mặc định | Hệ quả |
|---|---|---|
| Nhóm «Công ty» | Xem | Ai thấy một pháp nhân đều thấy nhóm |
| Thư mục pháp nhân | **Đóng góp** | Ai với tới pháp nhân (và có quyền ghi) đều xếp văn bản vào được |
| Thư mục thường | Kế thừa | Theo cha |
| Thư mục tự do | **Riêng tư** | Chỉ người tạo (được cấp Quản lý) và người được chia thấy — kể cả người có quyền Xem văn bản *Tất cả* cũng không thấy |

**«Với tới pháp nhân»** tính từ phạm vi quyền **Xem văn bản** của người đó:

- Phạm vi *Tất cả* (không kèm danh sách công ty riêng) → mọi pháp nhân.
- Phạm vi hẹp hơn → pháp nhân của chính mình.
- Cộng các công ty được **thêm riêng**, trừ các công ty bị **loại riêng** ở màn Phân quyền.

**Khóa một nhánh**: đặt quyền chung = Riêng tư ở thư mục đầu nhánh; rồi chia Cho cho đúng người.

### 22. Việc gì cần quyền gì

| Việc | Quyền vai trò | Mức trên thư mục |
|---|---|---|
| Xem cây, mở thư mục, tìm | Xem «Cây thư mục» | Xem |
| Tạo thư mục con | Tạo «Cây thư mục» | Đóng góp trên cha |
| Tạo thư mục tự do ở gốc | Tạo «Cây thư mục» | — (tài khoản phải gắn hồ sơ nhân sự) |
| Đổi tên, mã, mô tả, quyền chung, ngừng dùng, khôi phục | Sửa «Cây thư mục» | Quản lý |
| Chuyển thư mục | Sửa «Cây thư mục» | Quản lý (nguồn) + Đóng góp (cha mới) |
| Đổi thứ tự | Sửa «Cây thư mục» | Quản lý trên cha |
| Chia sẻ, đổi mức, thu hồi | Sửa «Cây thư mục» | Quản lý |
| Xóa thư mục | Xóa «Cây thư mục» | Quản lý (+ Đóng góp trên nơi nhận văn bản) |
| Thêm / chuyển / gỡ văn bản | Sửa «Văn bản» + quyền sửa đúng văn bản đó | Đóng góp |
| Tạo văn bản trong thư mục | Tạo «Văn bản» | Đóng góp |
| Xem ai có quyền trên thư mục | Xem «Cây thư mục» | Quản lý mới thấy đủ danh sách kế thừa |

### 23. Thấy một phần

Thư mục có 5 văn bản mà một người chỉ đọc được 2 thì **mọi chỗ** chỉ nói về 2 văn bản đó:

- số đếm trên cây (thư mục và cả nhánh — **đã khử trùng**, văn bản nằm ở hai thư mục trong nhánh
  đếm một lần);
- bảng nội dung, kết quả tìm, tab Tệp;
- thẻ «Thư mục (n)» ở chi tiết văn bản, cột «Thư mục» ở màn Văn bản (thư mục chính không thấy →
  hiện thư mục phụ đầu tiên thấy được).

Ngoại lệ **cố ý**: hộp xóa thư mục đếm toàn hệ thống (QT-TM14); thao tác hàng loạt báo «bị từ chối
m» không nêu lý do từng văn bản.

---

## PHẦN VI. ĐIỂM CẦN LƯU Ý

### 24. Hệ quả dễ bất ngờ

| # | Hiện tượng | Vì sao | Cách xử lý |
|---|---|---|---|
| 1 | Chuyển thư mục của Cty A vào nhánh Cty B: người Cty B không thấy, người Cty A vẫn thấy | Pháp nhân của thư mục không đổi khi chuyển (QT-TM12) | Chia sẻ thêm cho người Cty B, hoặc tạo thư mục mới trong nhánh B |
| 2 | Thư mục công ty chuyển ra gốc cây thành «riêng tư» với mọi người thường | Ra gốc thì không còn tổ tiên để kế thừa quyền chung; người chuyển **không** tự được cấp Quản lý (chỉ thư mục tự do mới được) | Đặt quyền chung cho nó sau khi chuyển; quản trị thư mục của pháp nhân vẫn thấy |
| 3 | Thư mục pháp nhân chuyển được (vào pháp nhân khác, ra gốc) | Chưa có luật chặn | Chỉ giao mức Quản lý nhóm «Công ty» cho quản trị toàn hệ |
| 4 | Nhóm «Công ty» đổi tên / ngừng dùng được | Chưa có luật chặn theo loại; ngừng dùng nhóm = ngừng cả nhánh công ty | Như trên |
| 5 | Khôi phục thư mục có thể sinh tên trùng anh em | Chỉ kiểm trùng lúc tạo / đổi tên / chuyển | Đổi tên sau khi khôi phục |
| 6 | Khôi phục thư mục con dưới cha đang ngừng dùng → thư mục «treo» | Khôi phục không kéo theo cha | Khôi phục từ trên xuống |
| 7 | Được chia một văn bản → thấy tên các thư mục cha, kể cả nhánh riêng tư | Xem ngầm định (QT-TM19) để người đó tìm ra văn bản | Chấp nhận; muốn giấu thì Cấm thư mục với người đó |
| 8 | Người chỉ có quyền Xem văn bản không xếp được vào thư mục pháp nhân dù quyền chung là Đóng góp | Trần vai trò (QT-TM18) | Cấp quyền Tạo hoặc Sửa văn bản cho vai trò |
| 9 | Chọn văn bản rồi bấm **Xóa** trên thanh thao tác = **xóa hẳn** văn bản; **Xóa** trong menu chuột phải của văn bản = **gỡ khỏi thư mục** | Hai lối vào khác nghĩa | Đọc hộp xác nhận; HDSD mục 13, 16 ghi rõ |
| 10 | Xóa hàng loạt thư mục: văn bản mồ côi về thư mục pháp nhân, không về thư mục cha | Không có bước chọn nơi nhận | Muốn chọn nơi nhận thì xóa từng thư mục |
| 11 | Thư mục mặc định của loại văn bản khai sai pháp nhân → lặng lẽ không dùng | Hệ thống không kiểm lúc khai | Khai đúng thư mục trong nhánh pháp nhân |
| 12 | Hai người mở cùng thư mục thấy số văn bản khác nhau | Thấy một phần (§23) | Đúng thiết kế |

### 25. Câu hỏi còn mở

- Có nên **chặn** chuyển / đổi tên / ngừng dùng thư mục pháp nhân và nhóm «Công ty» (điểm 3, 4
  §24), hay giữ như hiện nay và chỉ khống chế bằng quyền?
- Chuyển thư mục sang nhánh pháp nhân khác có nên **đổi luôn pháp nhân** của thư mục (và cả nhánh)
  không (điểm 1 §24)?
- Hai lối «Xóa» khác nghĩa trên màn Thư mục (điểm 9 §24): có nên đổi nhãn mục trong menu chuột phải
  thành **«Gỡ khỏi thư mục»** cho khỏi nhầm?
- Có cần thùng rác / khôi phục thư mục đã xóa không?
