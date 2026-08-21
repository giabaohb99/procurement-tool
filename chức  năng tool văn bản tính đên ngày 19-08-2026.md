# BÁO CÁO — PHÂN HỆ VĂN THƯ (QUẢN LÝ VĂN BẢN)

**Ngày lập:** 19/08/2026 · **Cập nhật gần nhất:** 21/08/2026 · **Sản phẩm:** ERP DEGO Holding · **Nhánh:** `erp-v2`

Ký hiệu trạng thái: **✅ xong** · **⚠️ một phần** · **❌ chưa làm**

---

## I. Quy mô (mốc 19/08/2026)

| Hạng mục                              | Số lượng |
| ------------------------------------- | -------- |
| Màn hình                              | 16       |
| API                                   | 68       |
| Bảng dữ liệu                          | 20       |
| Ca kiểm tự động — riêng phân hệ này   | 245      |
| Ca kiểm tự động — toàn hệ (đang xanh) | 918      |

---

## II. Danh sách chức năng

### 1. Soạn thảo

| #    | Chức năng                       | Mô tả                                                                         | TT  |
| ---- | ------------------------------- | ----------------------------------------------------------------------------- | --- |
| 1.1  | Trình soạn thảo A4 trên web     | Tờ giấy A4 như Word ngay trong trình duyệt, tự chia trang                     | ✅  |
| 1.2  | Thể thức Nghị định 30           | Times New Roman 14pt, lề trái 30mm / phải 20mm / trên dưới 20mm               | ✅  |
| 1.3  | Định dạng chữ                   | Đậm, nghiêng, gạch chân, gạch ngang, chỉ số trên/dưới, màu chữ, màu nền       | ✅  |
| 1.4  | Định dạng đoạn                  | Canh lề 4 kiểu, giãn dòng chuẩn Word (1,0–3,0 + tùy chỉnh), thụt lề           | ✅  |
| 1.5  | Phông và cỡ chữ                 | 6 phông thông dụng, cỡ 10–32pt, có xem trước phông                            | ✅  |
| 1.6  | Bảng biểu                       | Chèn lưới 10×10, thêm/xóa hàng cột, gộp/tách ô; dán vùng Excel vào bảng đang chọn | ✅  |
| 1.7  | Viền và nền bảng                | Độ dày 0,5–2,25pt, nét liền/đứt/chấm, màu, 8 kiểu viền (kể cả **không viền**) | ✅  |
| 1.8  | Ảnh và liên kết                 | Chèn ảnh (URL hoặc tệp ≤1MB), chèn/gỡ liên kết                                | ✅  |
| 1.9  | Danh sách, trích dẫn, đường kẻ  | Dấu chấm, đánh số, trích dẫn, đường kẻ ngang                                  | ✅  |
| 1.10 | Mục lục tự động                 | Cột trái đọc thẳng tiêu đề trong bài, bấm là nhảy tới                         | ✅  |
| 1.11 | Thước chỉnh lề                  | Kéo con trượt đổi lề trái/phải, lưu theo từng phiên bản                       | ✅  |
| 1.12 | Mức phóng                       | 50% – 200%                                                                    | ✅  |
| 1.13 | Menu chuột phải                 | Cắt/dán, định dạng nhanh, nhóm lệnh bảng đầy đủ                               | ✅  |
| 1.14 | Tự lưu                          | Lưu sau 1,5 giây ngừng gõ, hiện trạng thái "Đã lưu lúc…"                      | ✅  |
| 1.15 | Đầu trang – chân trang tùy biến |                                                                               | ❌  |
| 1.16 | Đánh số mục tự động (I, 1., a.) |                                                                               | ❌  |
| 1.17 | Chú thích chân trang            |                                                                               | ❌  |
| 1.18 | Tab stop / dấu chấm dẫn         | Thay tạm bằng bảng không viền                                                 | ❌  |

### 2. Nhập và xuất

| #    | Chức năng                | Mô tả                                                      | TT  |
| ---- | ------------------------ | ---------------------------------------------------------- | --- |
| 2.1  | Nhập tệp Word            | `.doc` và `.docx`, giữ định dạng đoạn, chữ, bảng, ảnh      | ✅  |
| 2.2  | Nhập tệp PDF             | PDF có lớp chữ dựng lại thành văn bản sửa được             | ✅  |
| 2.3  | Nhập Markdown / HTML     |                                                            | ✅  |
| 2.4  | Báo cáo đối chiếu PDF    | Chỉ rõ trang nào cần soát lại, bấm là nhảy tới trang nguồn | ✅  |
| 2.5  | Nhập vào bản đang có     | Chọn chèn tại con trỏ hoặc ghi đè toàn bộ nội dung hiện tại | ✅  |
| 2.6  | Trang in                 | Khổ A4, lề theo bản ghi, xem trước trên màn hình           | ✅  |
| 2.7  | Đánh số trang khi in     | Canh giữa lề trên, bỏ trang đầu — đúng Nghị định 30        | ✅  |
| 2.8  | Chữ chìm "BẢN NHÁP"      | Bản chưa ban hành in ra tự đóng chữ chìm                   | ✅  |
| 2.9  | Xuất PDF                 | Qua hộp in của trình duyệt (In / Lưu PDF)                  | ✅  |
| 2.10 | Xuất ra tệp Word (.docx) |                                                            | ❌  |

### 3. Phiên bản

| #   | Chức năng                                 | Mô tả                                                    | TT  |
| --- | ----------------------------------------- | -------------------------------------------------------- | --- |
| 3.1 | Mở phiên bản mới                          | Sửa lớn lên 2.0, sửa nhỏ lên 1.1; giữ đúng chuỗi tài liệu, không sinh dòng gốc mới | ✅  |
| 3.2 | Bắt khai lý do sửa                        | "Sửa gì" bắt buộc từ phiên bản thứ hai                   | ✅  |
| 3.3 | Khóa bản đã duyệt                         | Khóa vĩnh viễn, không có đường mở lại                    | ✅  |
| 3.4 | Mã kiểm tra nội dung                      | SHA-256 tính lúc khóa, để đối chiếu bản in với bản đã ký | ✅  |
| 3.5 | Bản cũ vẫn hiệu lực khi bản mới đang soạn | Không có khoảng trống pháp lý                            | ✅  |
| 3.6 | Một người giữ bản nháp                    | Người thứ hai được báo rõ ai đang giữ                    | ✅  |
| 3.7 | So sánh hai phiên bản (diff)              |                                                          | ❌  |

### 4. Phê duyệt

| #   | Chức năng                          | Mô tả                                                               | TT  |
| --- | ---------------------------------- | ------------------------------------------------------------------- | --- |
| 4.1 | Gửi duyệt                          | Kiểm đủ điều kiện trước khi cho gửi                                 | ✅  |
| 4.2 | Luồng duyệt nhiều bước             | Trưởng bộ phận → ban chuyên môn → lãnh đạo; bản clone dùng luồng riêng của pháp nhân nhận | ✅  |
| 4.3 | Theo dõi tiến trình                | Việc đang chờ ở đầu, sau đó là hoạt động từ mới nhất về cũ          | ✅  |
| 4.4 | Dấu vết phê duyệt                  | Timeline có người làm, chặng, ý kiến, thời gian, đường nối và bản in | ✅  |
| 4.5 | Cảnh báo phiếu kẹt                 | Không tìm ra người duyệt thì báo đỏ                                 | ✅  |
| 4.6 | Trả lại bản nháp                   | Kèm lý do, văn bản về Nháp                                          | ✅  |
| 4.7 | Rút phiếu duyệt                    | Người soạn tự rút, văn bản về Nháp                                  | ✅  |
| 4.8 | Đóng băng khi đang duyệt           | Khóa nội dung, thông tin, đính kèm — người duyệt ký đúng bản họ đọc | ✅  |
| 4.9 | Duyệt thay khi vắng mặt (ủy quyền) | Bộ máy chung có, chưa dùng cho văn bản                              | ⚠️  |

### 5. Ban hành và số hiệu

| #    | Chức năng                    | Mô tả                                                                     | TT  |
| ---- | ---------------------------- | ------------------------------------------------------------------------- | --- |
| 5.1  | Xem trước trước khi ban hành | Số sẽ cấp, bản sẽ khóa, văn bản nào bị thay thế, tách lỗi chặn / cảnh báo | ✅  |
| 5.2  | Cấp số hiệu tự động          | Hệ cấp, không ai gõ tay                                                   | ✅  |
| 5.3  | Hai kiểu định danh           | Mã bất biến `DEGO-QC-012` · số theo sổ `08/2026/TB-NS-DEGO`               | ✅  |
| 5.4  | Quy tắc đánh số              | Thẻ có highlight, kéo thả; hỗ trợ `/`, `-`, `(`, `)` và mã tùy chỉnh của phòng/pháp nhân | ✅  |
| 5.5  | Chống trùng số               | Ba lớp bảo vệ, cấp một lần, hủy không trả số về                           | ✅  |
| 5.6  | Xem trước số hiệu            | Xem lúc đang soạn, không chiếm số                                         | ✅  |
| 5.7  | Sửa số hiệu thủ công         | Chỉ khi quy tắc cho phép, bắt buộc có lý do                               | ✅  |
| 5.8  | Sổ văn bản                   | Sổ theo chiều đến/đi/nội bộ, bộ đếm riêng theo năm                        | ✅  |
| 5.9  | Thành viên sổ                | Người quản lý sổ (đọc + sửa), người xem sổ (chỉ đọc)                      | ✅  |
| 5.10 | Hiệu lực theo ngày           | Ban hành hôm nay, hiệu lực tháng sau — hệ tự chuyển khi tới ngày          | ✅  |
| 5.11 | Bãi bỏ văn bản               | Kèm lý do, giữ nguyên số hiệu trong sổ                                    | ✅  |

### 6. Phạm vi áp dụng

| #   | Chức năng                        | Mô tả                                               | TT  |
| --- | -------------------------------- | --------------------------------------------------- | --- |
| 6.1 | Khai phạm vi ba chiều            | Pháp nhân · phòng ban · cá nhân                     | ✅  |
| 6.2 | Bao gồm / loại trừ               | Cá nhân > phòng ban > pháp nhân; cùng cấp thì loại trừ thắng | ✅  |
| 6.3 | Mặc định theo pháp nhân ban hành | Không khai gì = áp cho cả công ty ban hành          | ✅  |
| 6.4 | Màn "Văn bản áp dụng cho tôi"    | Mỗi nhân viên thấy đúng văn bản mình phải theo      | ✅  |
| 6.5 | Gồm cả đơn vị con                | Đang là phép xấp xỉ, sai khi có tầng công ty thứ ba | ⚠️  |
| 6.6 | Xác nhận đã đọc                  | Ai đã đọc quy chế này rồi                           | ❌  |
| 6.7 | Danh sách nơi nhận               |                                                     | ❌  |

### 7. Quyền truy cập

| #   | Chức năng                           | Mô tả                                                    | TT  |
| --- | ----------------------------------- | -------------------------------------------------------- | --- |
| 7.1 | Phân quyền theo vai trò             | Đọc, tạo, sửa, xóa, duyệt, bãi bỏ, in, xuất              | ✅  |
| 7.2 | Chia quyền từng văn bản             | Cho người · phòng ban · pháp nhân · vai trò              | ✅  |
| 7.3 | Cấm đích danh                       | Cấm thắng tất cả, kể cả quản trị viên                    | ✅  |
| 7.4 | Hạn hiệu lực + lý do                | Lý do chia sẻ là ô bắt buộc                              | ✅  |
| 7.5 | Thu hồi quyền                       | Đánh dấu, không xóa dòng — tra lại được ai từng có quyền | ✅  |
| 7.6 | Không được đọc thì không lộ tồn tại | Trả về "không tìm thấy", không phải "bị từ chối"         | ✅  |
| 7.7 | Người duyệt luôn đọc được           | Không ai ký thứ mình không mở ra xem được                | ✅  |
| 7.8 | Kiểm quyền theo mức mật             | Có cột và ràng buộc, **chưa có lớp chặn**                | ❌  |

### 8. Quan hệ giữa văn bản

| #   | Chức năng                                         | Mô tả                                                                                           | TT  |
| --- | ------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --- |
| 8.1 | Mười loại quan hệ                                 | Thay thế, sửa đổi, bổ sung, hướng dẫn, kèm theo, thuộc về, căn cứ, tham chiếu, bãi bỏ, trích từ | ✅  |
| 8.2 | Quy tắc quan hệ                                   | Khai loại nào nối được với loại nào, bắt buộc hay tùy chọn                                      | ✅  |
| 8.3 | Chặn gửi duyệt khi thiếu quan hệ bắt buộc         |                                                                                                 | ✅  |
| 8.4 | Cấm quan hệ vòng lặp                              | Kiểm cả chuỗi, không chỉ hai bước                                                               | ✅  |
| 8.5 | Cây tài liệu                                      | Mở Quy trình thấy Hướng dẫn và Biểu mẫu treo dưới                                               | ✅  |
| 8.6 | Tự chuyển trạng thái văn bản bị thay thế / bãi bỏ |                                                                                                 | ✅  |
| 8.7 | Nhãn "đã bị sửa đổi bởi…"                         | Hiện ở mọi tab, không tắt được                                                                  | ✅  |
| 8.8 | Đánh dấu văn bản con cần rà lại                   | Khi cha lên bản mới hoặc bị bãi bỏ                                                              | ✅  |
| 8.9 | Cảnh báo văn bản trùng khi tạo                    | Cùng loại, cùng phòng, còn hiệu lực                                                             | ✅  |

### 9. Bản trích và bản riêng

| #   | Chức năng                   | Mô tả                                                                        | TT  |
| --- | --------------------------- | ---------------------------------------------------------------------------- | --- |
| 9.1 | Bản trích nội bộ            | Tách một phần nội dung, mức mật thấp hơn                                     | ✅  |
| 9.2 | Ràng buộc bản trích         | Mức mật ≤ gốc · gốc lên bản mới thì cần rà lại · gốc bãi bỏ thì hết hiệu lực | ✅  |
| 9.3 | Bản riêng cho pháp nhân con | Công ty con xem được gốc, sửa và ban hành bản riêng; tự chọn phạm vi và luồng duyệt | ✅  |
| 9.4 | Kế hoạch nhân bản           | Khai lúc tạo, sinh bản nháp sau khi gốc ban hành                             | ✅  |
| 9.5 | Báo cho pháp nhân con       | Chuông trong ứng dụng + email (nếu môi trường bật email)                     | ✅  |
| 9.6 | Màn theo dõi bản riêng      | 12 công ty con đang ở phiên bản nào, ai đã ban hành                          | ⚠️  |
| 9.7 | Trích lục chính thức        | Loại riêng, số riêng — chờ chốt nghiệp vụ                                    | ❌  |

### 10. Chữ ký

| #    | Chức năng                          | Mô tả                                                                 | TT  |
| ---- | ---------------------------------- | --------------------------------------------------------------------- | --- |
| 10.1 | Ký điện tử nội bộ                  | Có giá trị trong nội bộ tập đoàn                                      | ✅  |
| 10.2 | Ghi nhận ký số có chứng thư        | Ghi số chứng thư + nhà cung cấp; **việc ký thật làm ở dịch vụ ngoài** | ⚠️  |
| 10.3 | Ghi nhận chữ ký giấy đã quét       |                                                                       | ✅  |
| 10.4 | In rõ giá trị pháp lý cạnh chữ ký  | Để không ai nhầm ba loại với nhau                                     | ✅  |
| 10.5 | Chữ ký chỉ ghi thêm                | Không sửa, không xóa                                                  | ✅  |
| 10.6 | Phát hiện nội dung lệch sau khi ký | So mã kiểm tra nội dung                                               | ✅  |

### 11. Tra cứu và tổng quan

| #     | Chức năng                  | Mô tả                                               | TT  |
| ----- | -------------------------- | --------------------------------------------------- | --- |
| 11.1  | Danh sách văn bản          | Lọc, tìm, phân trang ở máy chủ                      | ✅  |
| 11.2  | Tìm nhanh                  | Theo tên, số hiệu, **số hiệu cũ bản giấy**, từ khóa | ✅  |
| 11.3  | Bộ lọc nâng cao            | 17 trường, nối nhiều điều kiện                      | ✅  |
| 11.4  | Gom bản riêng dưới bản gốc | Bản clone và phiên bản mới nằm đúng nhóm xổ xuống, không sinh dòng ngang hàng | ✅  |
| 11.5  | Tùy chỉnh cột hiển thị     | Ẩn/hiện, ghim cột                                   | ✅  |
| 11.6  | Trang tổng quan            | 5 chỉ số + việc cần xử lý + văn bản gần đây         | ✅  |
| 11.7  | Biểu đồ ban hành 12 tháng  |                                                     | ✅  |
| 11.8  | Cơ cấu theo loại văn bản   |                                                     | ✅  |
| 11.9  | Ma trận ưu tiên            | Quan trọng × khẩn cấp                               | ✅  |
| 11.10 | Cảnh báo sắp hết hiệu lực  | Trong 30 ngày                                       | ✅  |
| 11.11 | Xuất danh sách ra Excel    |                                                     | ❌  |

### 12. Danh mục và thiết lập

| #    | Chức năng            | Mô tả                                                                        | TT  |
| ---- | -------------------- | ---------------------------------------------------------------------------- | --- |
| 12.1 | Loại văn bản         | Mã, nhóm, kiểu định danh, thời điểm cấp số, mức mật mặc định, chu kỳ rà soát | ✅  |
| 12.2 | Thư viện văn bản mẫu | Mẫu trắng đúng thể thức, khối đầu hai cột                                    | ✅  |
| 12.3 | Quy tắc đánh số      | Theo chiều, loại, sổ; mã tùy chỉnh đặt ngay trong form mẫu số hiệu           | ✅  |
| 12.4 | Quy tắc quan hệ      | Loại nào nối loại nào, số lượng tối thiểu/tối đa                             | ✅  |
| 12.5 | Sổ văn bản           | Mở sổ, thành viên, bộ đếm                                                    | ✅  |
| 12.6 | Đơn vị gửi nhận      | Cơ quan nhà nước, đối tác, khách hàng, đơn vị nội bộ                         | ✅  |
| 12.7 | Mức mật và độ khẩn   | Chỉ đọc — thang cố định                                                      | ✅  |
| 12.8 | Nhật ký thao tác     | Ai sửa gì lúc nào trên từng văn bản                                          | ✅  |
| 12.9 | Sổ văn bản **đến**   | Văn bản từ ngoài gửi vào                                                     | ❌  |

---

## III. Việc làm trong đợt này (19/08/2026)

| #   | Nội dung                                                                                   | Vì sao cần                                                                           |
| --- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| 1   | Bịt lỗ hổng: đang trình duyệt vẫn sửa được văn bản                                         | Người duyệt đọc bản A, người soạn sửa thành bản B, ban hành ra bản B mà không ai đọc |
| 2   | Bịt lỗ hổng: rút phiếu duyệt để văn bản treo lơ lửng                                       | Dựng lại được ca văn bản lên "Có hiệu lực", có số hiệu, mà không ai ký bước nào      |
| 3   | Bắt buộc chọn phòng chủ trì khi tạo                                                        | Thiếu phòng thì luồng duyệt không tìm ra người duyệt, phiếu kẹt cứng                 |
| 4   | Thể thức trang Nghị định 30 + trang in + xuất PDF                                          | Soạn xong không đưa lên giấy đúng thể thức được; lề trái 20mm không đủ chỗ đóng gáy  |
| 5   | Nhập tệp Word/PDF vào trang soạn thảo                                                      | Phần lớn văn bản soạn sẵn ngoài Word mới đưa vào hệ                                  |
| 6   | Bộ lọc nâng cao cho danh sách                                                              | Màn này thiếu, các phân hệ khác đều đã có                                            |
| 7   | Bộ mẫu đúng thể thức + mẫu Biên bản họp                                                    | Mẫu cũ xếp dọc căn giữa, sai thể thức hành chính                                     |
| 8   | Sửa giãn dòng lệch chuẩn Word, mục lục không bấm được, thanh công cụ cắt chữ, lề không lưu | Lỗi giao diện người dùng báo                                                         |
| 9   | Cảnh báo hai luồng duyệt mặc định cùng bật                                                 | Phòng ngừa: luồng thứ hai nằm im vĩnh viễn mà không có gì báo                        |
| 10  | Gỡ kẹt chuỗi cập nhật cơ sở dữ liệu                                                        | Nếu để nguyên, môi trường nào cập nhật mã cũng không khởi động được hệ thống         |

Toàn bộ đã kiểm bằng **trình duyệt thật** (đăng nhập, thao tác, in ra PDF đếm số trang), không chỉ chạy kiểm thử tự động.

---

## IV. Cập nhật tiến độ ngày 20–21/08/2026

| #  | Hạng mục | Kết quả hiện tại | Kiểm chứng |
| -- | -------- | ---------------- | ---------- |
| 1  | Bản clone xem lại văn bản gốc | Pháp nhân nhận mở được bản gốc để đối chiếu, nhưng chỉ sửa và ban hành trên bản clone của mình | Commit `7ce5670`; test quyền truy cập clone |
| 2  | Tự điền phạm vi cho bản clone | Khi sinh clone, hệ tự thêm phạm vi pháp nhân nhận; pháp nhân con vẫn được sửa lại phạm vi trước khi ban hành | Test `test_clone_phap_nhan_con.py` và `test_pham_vi_ban_hanh_theo_phap_nhan.py` |
| 3  | Dán bảng từ Excel | Dán trực tiếp dữ liệu clipboard vào bảng trong trình soạn thảo, giữ cấu trúc ô thay vì chèn ảnh | Commit `e22f9d7`; test spreadsheet paste và Chrome DevTools |
| 4  | Nhập thêm tệp vào văn bản đang soạn | Có hai lựa chọn rõ ràng: **chèn tại con trỏ** hoặc **ghi đè toàn bộ** | Commit `e22f9d7`; test import editor và Chrome DevTools |
| 5  | Phiên bản của bản clone | Ban hành phiên bản mới vẫn thuộc đúng chuỗi tài liệu/bản clone, không tạo thêm dòng độc lập trong danh sách | Test vòng đời clone và danh sách gom bản riêng |
| 6  | Luồng duyệt riêng theo pháp nhân | Form luồng duyệt có trường pháp nhân; bản clone bắt buộc tìm luồng riêng của nơi nhận, không dùng luồng của bản gốc | Test bộ máy duyệt, clone tự sinh và văn bản qua luồng duyệt |
| 7  | Phạm vi người xem sau ban hành | Đã phủ 4 ca cho cả bản gốc và clone: toàn pháp nhân; trừ cá nhân; trừ phòng; trừ phòng nhưng cho phép lại một cá nhân | Test tham số hóa `test_pham_vi_ban_hanh_theo_phap_nhan.py` |
| 8  | Thiết lập mẫu số hiệu | Chuyển cấu hình mã tùy chỉnh vào đúng form quy tắc; đổi nhãn thành **Tùy chỉnh thêm**; thẻ được highlight, kéo thả và chèn dấu phân cách | Test form quy tắc đánh số và Chrome DevTools |
| 9  | Tiến trình và lịch sử phê duyệt | Khối các chặng và activity history đều dùng timeline dọc; chờ xử lý nằm đầu, mới nhất trước, title/subtitle rõ và có rail nối node | Chrome đúng URL `localhost:5174/document/documents/212?tab=approval`; rail chặng 2px và rail lịch sử 2px màu `#00aeef` |

### Trạng thái mã nguồn tại thời điểm cập nhật

- Hai nhóm **bản clone xem gốc/tự điền phạm vi** và **dán Excel/nhập tệp** đã có commit trên nhánh `erp-v2`.
- Nhóm **luồng duyệt riêng, phạm vi ban hành, thiết lập số hiệu và timeline phê duyệt** đã hoàn tất mã và ca kiểm trong working tree; chưa tạo commit mới tại thời điểm cập nhật báo cáo này.

### Kết quả kiểm tra ngày 21/08/2026

- Backend trọng điểm: **99/99 ca đạt** cho phạm vi ban hành, bản clone, quyền truy cập và bộ máy duyệt.
- Frontend: **72 tệp kiểm thử, 448/448 ca đạt**; TypeScript và ESLint đạt.
- Chrome DevTools trên đúng `localhost:5174/document/documents/212?tab=approval`: timeline chặng và lịch sử đều có rail 2px, không tràn ngang, không có lỗi console hay request thất bại.

---
