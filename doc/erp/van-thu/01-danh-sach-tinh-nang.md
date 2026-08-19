# 01 · DANH SÁCH TÍNH NĂNG QUẢN LÝ VĂN THƯ

> Xây trên mã nguồn Thu mua đang chạy · bản 1.3 · 13/08/2026
> Đọc `00` trước — có phần đánh giá và các câu hỏi đang chặn.

**Đã bổ sung sau khi rà lại (bản 1.1 đến 1.3):**

| Bổ sung | Mã | Vì sao thiếu |
|---|---|---|
| Sửa văn bản **đã ban hành** | C13–C18, J10, J11 | Bốn tệp đầu có nói tới phiên bản nhưng không nói luồng. Hai loại văn bản sửa theo hai cách khác nhau: tài liệu hệ thống thì lên bản 2.0 giữ nguyên mã, văn bản hành chính thì ra một văn bản mới sửa đổi văn bản cũ. Chi tiết ở [`05`](./05-vong-doi-phien-ban.md) |
| **Chia sẻ và thu hồi** | G14–G24, G09 chuyển lên bản 1 | Chỉ có G07 "chia sẻ không vượt được mức mật" thì giám đốc bấm chia sẻ xong không ai thấy gì và không biết làm tiếp thế nào. Chi tiết nằm ngay trong nhóm G |
| **Bản trích** xếp lại cho đúng chỗ | C19, C20, E11; G18 thành dòng trỏ | Bản trích trước nằm ở G18 trong nhóm quyền truy cập, vì cái *làm nó phát sinh* là bài toán chia sẻ. Nhưng việc phải làm là **soạn thảo** cộng **quan hệ cha–con**, người đọc nhóm C và nhóm E không bao giờ thấy nó. Kèm theo, G18 cũ dùng lại quan hệ *thuộc về* là sai — bản trích cần **quan hệ thứ mười, *trích từ*** |

---

## Cách đọc bảng

| Cột | Nghĩa |
|---|---|
| Mã | Dùng để nhắc tới tính năng trong lộ trình và trong tài liệu bàn giao |
| Bản | **1** = bản đầu tiên phải có · **2** = làm sau · **?** = chờ trả lời câu hỏi ở `00` mục 8 hoặc `05` mục 9 |
| Có sẵn | `[x]` dùng lại được ngay từ Thu mua · `[~]` có nhưng phải sửa · `[ ]` phải làm mới |

Tổng: **174 tính năng**, trong đó **132 thuộc bản đầu tiên**.

---

# NHÓM N · VIỆC NỀN — phải xong trước khi đưa văn bản thật vào

> Đây là phần trả nợ kỹ thuật trên hệ Thu mua. Không có phần này thì phần quyền truy cập của văn thư chỉ là hình vẽ.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| N01 | Kiểm thử 5 luồng duyệt hiện tại | Viết kiểm thử tự động cho duyệt yêu cầu mua hàng, khảo sát, yêu cầu khảo sát, đơn mua hàng, yêu cầu thanh toán. **Làm đầu tiên, không chờ ai trả lời gì** | 1 | `[ ]` |
| N02 | Tắt link công khai của kho file | Kho R2 để riêng tư hoàn toàn. Ngừng ghi link công khai vào cơ sở dữ liệu | 1 | `[~]` |
| N03 | Link tạm có kiểm quyền | Xem/tải file phải qua máy chủ: kiểm đủ quyền, sinh link sống 60–120 giây, ghi nhật ký ai xem file nào lúc nào | 1 | `[ ]` |
| N04 | Bộ nhớ đệm quyền chuyển sang Redis | Kèm kênh xóa đệm tức thì để thu hồi quyền có hiệu lực ngay trên mọi tiến trình | 1 | `[~]` |
| N05 | Phạm vi phòng ban khớp bằng ID | Không khớp bằng tên nữa. Đổi tên phòng ban không được làm mất quyền | 1 | `[~]` |
| N06 | Vá nhật ký thao tác | Đọc nhật ký phải có quyền và phải theo phạm vi. Bỏ trống mã bản ghi không được trả về nhật ký của mọi bản ghi | 1 | `[~]` |
| N07 | Vá loại trừ phòng ban | Cấu hình "loại trừ phòng X" hiện lưu được nhưng không có tác dụng | 1 | `[~]` |
| N08 | Thông báo tách theo app | Thêm cột `app` vào bảng thông báo đang có, mặc định `thumua`. Chuông lọc theo app đang mở. **Không tạo bảng thông báo thứ hai** | 1 | `[~]` |
| N09 | Nhóm đối tượng phân quyền theo phân hệ | Màn hình phân quyền tăng từ 28 lên khoảng 40 đối tượng. Gom theo phân hệ để không rối | 1 | `[~]` |
| N10 | Quét virus trước khi ghi file | Tệp chưa quét sạch thì không cho tải về | 2 | `[ ]` |
| N11 | Cột pháp nhân trên các bảng còn thiếu | Hiện 15/57 bảng có cột pháp nhân. Bảng văn thư phải có đủ ngay từ đầu | 1 | `[~]` |

---

# NHÓM A · DANH MỤC VÀ CẤU HÌNH

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| A01 | Danh mục loại văn bản | 32 loại, 6 nhóm A–F. Mỗi loại có mã viết tắt, định nghĩa, dùng khi nào, cấp nào được ban hành | 1 | `[ ]` |
| A02 | Cấu hình theo loại | Mỗi loại khai: kiểu đánh số, mức mật mặc định, có cần quyết định ban hành kèm không, chu kỳ rà soát, thời hạn lưu trữ, luồng duyệt mặc định, tệp mẫu | 1 | `[ ]` |
| A03 | Quy tắc cha–con theo loại | Loại nào bắt buộc phải khai quan hệ tới loại nào. Chi tiết ở nhóm E | 1 | `[ ]` |
| A04 | Mã số hiệu của pháp nhân | 13 pháp nhân, mỗi pháp nhân một mã chỉ gồm chữ và số, không dấu, không khoảng trắng. **Khác với mã hiển thị đang dùng** | 1 | `[~]` |
| A05 | Mã số hiệu của phòng ban | Chỉ phòng chức năng mới xuất hiện trong số hiệu, đơn vị kinh doanh thì không | 1 | `[~]` |
| A06 | Phòng ban dùng chung nhiều pháp nhân | Bảng nối "phòng ban này có mặt ở pháp nhân nào", kèm trưởng phòng **của phòng đó tại pháp nhân đó** | 1 | `[ ]` |
| A07 | Danh mục đối tác, cơ quan gửi nhận | Dùng cho ô "nơi nhận" của văn bản đi và "nơi gửi" của văn bản đến | 1 | `[ ]` |
| A08 | Danh mục chức danh và cấp bậc | 10 chức danh, có thứ bậc. Dùng để **gợi ý** người duyệt, **không tự sinh ra quyền** | 2 | `[~]` |
| A09 | Danh mục văn bản pháp luật | Theo dõi nghị định, thông tư mà quy chế nội bộ căn cứ theo. Luật đổi thì liệt kê ngay quy chế nào phải rà | 2 | `[ ]` |
| A10 | Cấu hình hệ thống theo pháp nhân | Đuôi tệp cho phép, thời gian tự đăng xuất, địa chỉ gửi thư. Đọc theo thứ tự: cấu hình pháp nhân, rồi cấu hình chung, rồi mặc định trong mã | 2 | `[~]` |

---

# NHÓM B · YÊU CẦU VĂN BẢN — duyệt rồi mới được soạn

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| B01 | Tạo yêu cầu văn bản | Ba loại yêu cầu: **soạn mới · sửa văn bản đang có · bãi bỏ**. Bắt buộc nhập lý do | 1 | `[ ]` |
| B02 | Yêu cầu chạy qua luồng duyệt | Người duyệt cấu hình được theo loại văn bản hoặc theo phòng ban. Ban đầu có thể là giám đốc | 1 | `[ ]` |
| B03 | Duyệt rồi mới cho soạn | Chưa có yêu cầu được duyệt thì **không tạo được văn bản**. Chặn ở tầng dịch vụ | 1 | `[ ]` |
| B04 | Sinh bản nháp từ yêu cầu | Yêu cầu được duyệt thì hệ thống tự tạo bản nháp, điền sẵn loại, phòng ban, người phụ trách, và **giữ liên kết về yêu cầu gốc** | 1 | `[ ]` |
| B05 | Gợi ý văn bản đã có khi tạo yêu cầu | Hiện danh sách văn bản cùng loại cùng phòng ban đang hiệu lực, để người xin tự thấy đã có hay chưa | 1 | `[ ]` |
| B06 | Bỏ qua bước yêu cầu | Một số loại (biên bản, đơn cá nhân) không cần xin phép mới được soạn. Cấu hình theo loại | 1 | `[ ]` |
| B07 | Theo dõi yêu cầu | Danh sách yêu cầu của tôi, đang chờ ai, bao lâu rồi | 1 | `[ ]` |

---

# NHÓM C · SOẠN THẢO VÀ PHIÊN BẢN

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| C01 | Bộ trường chung của mọi văn bản | Tiêu đề, loại, pháp nhân ban hành, phòng ban chủ trì, người chịu trách nhiệm nội dung, ngày hiệu lực, mức mật, độ khẩn, từ khóa | 1 | `[ ]` |
| C02 | Tệp mẫu theo loại | Mỗi loại gắn một tệp Word mẫu, người soạn tải về điền rồi tải lên lại | 1 | `[ ]` |
| C03 | Tải tệp lên và gắn vào văn bản | Dùng lại cơ chế tệp của Thu mua, nhưng đi qua đường riêng tư ở N02–N03 | 1 | `[~]` |
| C04 | Phiên bản bất biến | Một văn bản qua nhiều phiên bản. **Phiên bản đã duyệt không bao giờ bị ghi đè** — sửa là tạo phiên bản mới | 1 | `[ ]` |
| C05 | Lý do sửa bắt buộc | Mỗi phiên bản mới phải trả lời "sửa gì so với bản trước" và "vì sao sửa". Đây chính là biên bản sửa đổi | 1 | `[ ]` |
| C06 | Mã kiểm tra toàn vẹn tệp | Lưu mã băm của tệp để chứng minh về sau tệp không bị đổi | 1 | `[ ]` |
| C07 | Khóa sửa sau khi duyệt hoặc ban hành | Chặn ở tầng dịch vụ, không phải ẩn nút | 1 | `[ ]` |
| C08 | So sánh hai phiên bản | Xem cạnh nhau, chỉ ra chỗ khác | 2 | `[ ]` |
| C09 | Form nhập trên web cho loại dùng nhiều | Điền ô trên màn hình, hệ thống sinh ra văn bản đúng thể thức. **Chỉ làm 3–5 loại** | 2 | `[ ]` |
| C10 | Xem tệp trên web không cần tải | Chuyển Word sang PDF rồi xem trong trình duyệt | 2 | `[ ]` |
| C11 | Đóng dấu chìm động khi in hoặc tải | In tên người xem và thời điểm lên từng trang | 2 | `[ ]` |
| C12 | Ghi số hiệu cũ của văn bản giấy | Khi nhập kho giấy vào hệ thống, tìm kiếm chấp nhận cả số cũ | 1 | `[ ]` |
| C13 | Mở phiên bản mới từ văn bản đã ban hành | Chép nội dung bản hiện tại làm điểm xuất phát, bắt khai lý do sửa. **Chỉ áp cho loại có mã tài liệu bất biến** | 1 | `[ ]` |
| C14 | Một văn bản chỉ một bản nháp | Không cho hai người cùng mở bản 2.0. Ép bằng ràng buộc duy nhất ở tầng dữ liệu, không chỉ kiểm trong mã | 1 | `[ ]` |
| C15 | Phân loại sửa lớn hay sửa nhỏ | Người soạn chọn, người duyệt xác nhận. Quyết định luồng duyệt, việc bắt xác nhận lại, việc đánh dấu văn bản con | 1 | `[ ]` |
| C16 | Bản cũ vẫn hiệu lực trong lúc soạn bản mới | Không có khoảng trống. Chỉ đổi tại giây ban hành, trong một giao dịch | 1 | `[ ]` |
| C17 | Ngày hiệu lực riêng của từng phiên bản | Duyệt trước, hiệu lực sau. Tác vụ định kỳ tự chuyển đúng ngày | 1 | `[ ]` |
| C18 | Băng cảnh báo trên phiên bản cũ | "Đã bị thay thế bởi bản 2.0 ngày ...", kèm nút sang bản mới. Bản cũ **không xóa, không ẩn** — tranh chấp cũ phải xử theo bản cũ | 1 | `[ ]` |
| C19 | Soạn **bản trích nội bộ** | Mở bản gốc, chọn phần nội dung cần tách, sinh một văn bản mới mức mật thấp hơn. Dùng để chia xuống nhà máy, lab, dây chuyền. **Không cấp số hiệu riêng, không có người ký xác nhận** — chỉ có giá trị nội bộ tập đoàn | 1 | `[ ]` |
| C20 | **Trích lục chính thức** | Bản trích có giá trị đối ngoại: là **một loại văn bản riêng trong danh mục**, có số hiệu riêng, có người ký xác nhận "đúng với bản gốc", đi qua luồng duyệt riêng. Dùng khi gửi ra ngoài tập đoàn. Chờ câu B12 | ? | `[ ]` |

**C19 và C20 khác nhau ở đâu** — hai việc khác nhau, đừng gộp:

| | C19 · bản trích nội bộ | C20 · trích lục chính thức |
|---|---|---|
| Dùng để | Chia một phần nội dung xuống nhà máy, lab, dây chuyền | Gửi ra ngoài tập đoàn: ngân hàng, kiểm toán, cơ quan, đối tác |
| Là gì trong hệ thống | Một văn bản thường, loại giống bản gốc | **Một loại văn bản riêng** trong danh mục nhóm A |
| Số hiệu | Không có số riêng, gọi theo bản gốc | Có số hiệu riêng, cấp theo sổ |
| Người ký | Không có | Có, ký xác nhận "sao đúng với bản gốc" |
| Luồng duyệt | Người ban hành bản gốc đồng ý là xong | Đi luồng duyệt riêng như một văn bản phát hành ra ngoài |
| Nối về gốc | Quan hệ *trích từ* (E11) | Quan hệ *trích từ* (E11) |
| Bản | 1 | Chờ B12 |

Điểm chung, cả hai đều bị E11 ràng: mức mật không vượt gốc, gốc lên phiên bản thì bị đánh dấu cần rà lại, gốc bãi bỏ thì hết hiệu lực theo.

---

# NHÓM D · SỐ VĂN BẢN

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| D01 | Hai kiểu định danh | **Mã tài liệu bất biến** (`DEGO-QC-012`) cho nhóm A/B/C sống lâu · **số hiệu theo sổ** (`08/2026/TB-NS-DEGO`) cho nhóm D/E sự vụ. Khai theo loại văn bản | 1 | `[ ]` |
| D02 | Cấp số chống trùng | Khóa dòng bộ đếm khi cấp, nằm trong cùng giao dịch với việc ghi bản ghi. **Cấm dùng số lớn nhất cộng một, cấm dùng bộ đếm ngoài cơ sở dữ liệu** | 1 | `[ ]` |
| D03 | Ràng buộc duy nhất ở tầng dữ liệu | Lớp chặn cuối cùng, độc lập với mã nguồn | 1 | `[ ]` |
| D04 | Mỗi pháp nhân một sổ riêng | 13 bộ đếm độc lập, đếm lại từ 1 mỗi năm với kiểu số hiệu theo sổ | 1 | `[ ]` |
| D05 | Văn bản hủy vẫn giữ số | Chỉ đổi trạng thái. **Không trả số về để dùng lại** | 1 | `[ ]` |
| D06 | Cấp số vào lúc nào | Cấu hình theo loại: cấp khi tạo nháp, hay chỉ cấp khi được duyệt. Đề nghị mặc định là khi được duyệt | 1 | `[ ]` |
| D07 | Không cho đổi mã sau khi đã cấp số | Mã pháp nhân và mã loại đã dùng để cấp số thì khóa lại | 1 | `[ ]` |
| D08 | Xem trước số hiệu | Lúc soạn hiện "số sẽ là khoảng 09/2026/TB-NS-DEGO" để người soạn yên tâm, kèm ghi chú số thật cấp lúc duyệt | 2 | `[ ]` |

---

# NHÓM E · QUAN HỆ CHA–CON

> Phần này được yêu cầu đề xuất. Thiết kế đầy đủ ở [`00` mục 5](./00-danh-gia-va-cau-hoi.md#5-đề-xuất-tính-năng-cha–con-theo-loại-văn-bản).

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| E01 | Bảng quy tắc quan hệ theo loại | Mỗi dòng: loại nguồn, quan hệ, loại đích cho phép, bắt buộc hay không, số lượng. Khoảng 15–25 dòng, đổi bằng giao diện | 1 | `[ ]` |
| E02 | Mười loại quan hệ | thay thế · sửa đổi · bổ sung · hướng dẫn · kèm theo · thuộc về · căn cứ theo · tham chiếu · bãi bỏ · **trích từ** | 1 | `[ ]` |
| E03 | Form tự hiện ô theo quy tắc | Chọn loại "Hướng dẫn công việc" thì tự hiện ô "hướng dẫn cho quy trình nào", danh sách chỉ lọc đúng loại đích và chỉ văn bản đang hiệu lực | 1 | `[ ]` |
| E04 | Chặn gửi duyệt nếu thiếu quan hệ bắt buộc | Chặn ở tầng dịch vụ, kèm câu báo rõ thiếu gì | 1 | `[ ]` |
| E05 | Cấm vòng lặp | A hướng dẫn B mà B lại hướng dẫn A thì chặn ngay lúc lưu | 1 | `[ ]` |
| E06 | Cây tài liệu | Mở một Quy trình thấy ngay các Hướng dẫn công việc và Biểu mẫu thuộc nó, kèm trạng thái và phiên bản | 1 | `[ ]` |
| E07 | Cảnh báo tác động khi sửa cha | Liệt kê văn bản con và hỏi xử lý. **Hệ thống chỉ liệt kê, không tự sửa gì.** Quyết định ghi vào nhật ký. Cấu hình bằng cột `on_parent_new_version` trong bảng quy tắc | 1 | `[ ]` |
| E08 | Xử lý khi bãi bỏ văn bản cha | Theo cấu hình quan hệ: không làm gì · đánh dấu con cần rà lại · con hết hiệu lực theo cha. **Khác với E07** — bãi bỏ và lên phiên bản mới là hai việc, hai cột cấu hình riêng | 1 | `[ ]` |
| E09 | Thừa kế số hiệu | `DEGO-QC-012-HD01`. Bật tắt theo từng dòng quy tắc | 2 | `[ ]` |
| E10 | Thừa kế mức mật | Con không được thấp hơn cha, muốn hạ phải có người đủ thẩm quyền hạ tường minh | 2 | `[ ]` |
| E11 | Quan hệ *trích từ* và ba ràng buộc kéo theo | Nối bản trích (C19, C20) về bản gốc. **Không dùng chung với *thuộc về*** — *thuộc về* là hai văn bản khác nội dung, *trích từ* là cùng nội dung nhưng ít hơn. Ba ràng buộc riêng: (a) gốc lên phiên bản mới thì **mọi bản trích bị đánh dấu cần rà lại**, không cho tắt trong quy tắc; (b) gốc bị bãi bỏ thì **bản trích hết hiệu lực theo**, không có lựa chọn "không làm gì"; (c) mức mật bản trích **luôn ≤ gốc**, và không được thấp hơn mức thật của phần nội dung được trích | 1 | `[ ]` |

---

# NHÓM F · PHẠM VI BAN HÀNH VÀ CLONE XUỐNG PHÁP NHÂN CON

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| F01 | Phạm vi áp dụng ba kiểu | **Pháp nhân · phòng ban · cá nhân.** Không có kiểu chức danh — điều kiện dạng "trưởng phòng trở lên" viết trong nội dung văn bản | 1 | `[ ]` |
| F02 | Bao gồm và loại trừ | Các dòng bao gồm cộng dồn. **Loại trừ luôn thắng.** Không có dòng nào thì không ai thuộc phạm vi | 1 | `[ ]` |
| F03 | Bắt buộc kèm pháp nhân khi chọn phòng ban | Phòng ban dùng chung 13 pháp nhân, chọn trơ trọi là văn bản lan sang cả 13 công ty. Chặn ở tầng dữ liệu | 1 | `[ ]` |
| F04 | Áp cho cả đơn vị con | Chọn Tập đoàn kèm cờ "gồm đơn vị con" thì áp cho mọi công ty con **hiện tại và tương lai** | 1 | `[ ]` |
| F05 | Danh sách "văn bản áp dụng cho tôi" | Màn hình mỗi người thấy văn bản đang áp dụng cho mình | 1 | `[ ]` |
| F06 | **Clone thành bản nháp cho pháp nhân con** | Chọn một hoặc nhiều pháp nhân, hệ thống tạo bản nháp riêng cho từng nơi, sao chép nội dung và tệp | 1 | `[ ]` |
| F07 | Bản clone giữ liên kết ngược | Luôn có quan hệ *căn cứ theo* về bản gốc. **Không có nút nào xóa được liên kết này** | 1 | `[ ]` |
| F08 | Bản clone mang số hiệu riêng | Cấp theo mã pháp nhân con, không dùng lại số của Tập đoàn | 1 | `[ ]` |
| F09 | Gửi thư thông báo kèm bản nháp | Mỗi pháp nhân nhận một thư: có bản gốc, có bản nháp đã clone, có hạn xử lý | 1 | `[ ]` |
| F10 | Bảng theo dõi các bản clone | Một màn hình trả lời "12 công ty con đang ở phiên bản nào": ai đã ban hành, ai còn nháp, ai chưa đụng tới, ai lệch bản | 1 | `[ ]` |
| F11 | Bản gốc lên phiên bản thì đánh dấu con cần rà | Tự động, kèm thông báo cho người phụ trách từng bản clone | 1 | `[ ]` |
| F12 | Nhắc hạn với bản clone chưa xử lý | Quá hạn thì nhắc, quá lâu thì leo lên cấp trên | 2 | `[ ]` |
| F13 | Chọn cơ chế lúc ban hành | Màn hình ban hành hỏi rõ: **một văn bản gắn phạm vi** (mặc định) hay **clone xuống từng pháp nhân**, kèm giải thích ngắn hai cách khác nhau chỗ nào | 1 | `[ ]` |

---

# NHÓM G · QUYỀN TRUY CẬP

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| G01 | Quyền theo vai trò | Đối tượng × hành động. Dùng lại nguyên của Thu mua, chỉ thêm đối tượng mới | 1 | `[x]` |
| G02 | Phạm vi dữ liệu theo (người × vai trò) | Dùng lại nguyên. Thêm một giá trị phạm vi mới: **pháp nhân của mình và toàn bộ công ty con** | 1 | `[~]` |
| G03 | Mức mật của văn bản | 4 mức: Công khai · Nội bộ · Mật · Tuyệt mật. Đặt mặc định theo loại văn bản, sửa được trên từng văn bản | 1 | `[ ]` |
| G04 | Mức mật được phép của từng người | Cấp tường minh, **có hạn và phải gia hạn**. Chưa cấp thì mặc định là Nội bộ. Mức Mật và Tuyệt mật luôn phải cấp riêng | 1 | `[ ]` |
| G05 | Chia sẻ đích danh trên từng văn bản | Chia cho một người, một phòng, một pháp nhân hoặc một vai trò. Có cho phép và có cấm. **Chia sẻ có hạn** | 1 | `[ ]` |
| G06 | Cấm luôn thắng cho phép | Một dòng cấm ở bất kỳ lớp nào là chặn | 1 | `[ ]` |
| G07 | Chia sẻ không vượt được mức mật | Chia văn bản Tuyệt mật cho người mức Nội bộ thì người đó vẫn không xem được | 1 | `[ ]` |
| G08 | Tách quyền xem và quyền tải về | Cho xem trên trình duyệt mà không cho lưu về máy | 2 | `[ ]` |
| G09 | Chặn tải với mức Tuyệt mật | Chỉ xem trên web, có dấu chìm mang tên người xem. **Chuyển lên bản 1** — với tài liệu như công thức sản xuất thì đây là thứ duy nhất còn kiểm soát được sau khi đã chia sẻ | 1 | `[ ]` |
| G10 | Loại văn bản bảo mật | Cả loại được đánh dấu bảo mật thì mọi văn bản thuộc loại đó mặc định ở mức cao, chỉ người có thẩm quyền thấy | 1 | `[ ]` |
| G11 | Nghỉ việc là mất quyền ngay | Tắt nhân sự thì mọi quyền, mọi chia sẻ đích danh, mọi ủy quyền đều mất hiệu lực trong vài giây | 1 | `[~]` |
| G12 | Giới hạn xem theo khoảng ngày và khung giờ | Lấy ý tưởng từ HrOnline. Hữu ích với tài liệu nhạy cảm cho nhà thầu, tư vấn | 2 | `[ ]` |
| G13 | Xóa phải nhập lý do và xác thực lại | Lấy từ HrOnline: xóa tài liệu bắt buộc nhập lại mật khẩu và lý do | 2 | `[ ]` |

## G14–G24 · Chia sẻ và thu hồi

> Phần này giải bài toán: **văn bản Tuyệt mật chỉ giám đốc thấy, giờ cần chia xuống nhà máy, lab và dây chuyền.**
> G07 nói "chia sẻ không vượt được mức mật" — đúng về an toàn nhưng chỉ có G07 thì giám đốc bấm chia sẻ xong không ai thấy gì, và không biết phải làm gì tiếp. Mười một mục dưới đây là phần còn thiếu.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| G14 | Nhóm chia sẻ tự đặt | Chia cho "tổ dự án sản phẩm X" gồm 6 người ở 3 phòng khác nhau. Không phải phòng ban, không phải vai trò. Thiếu cái này thì người ta chia tay 6 lần rồi quên thu hồi 6 lần | 1 | `[ ]` |
| G15 | Chia sẻ đặc cách vượt mức mật | Chia đúng **một** văn bản cho người chưa đủ mức mật. **Bắt buộc có hạn, bắt buộc ghi lý do, bắt buộc có người duyệt.** Không nâng mức mật chung của người đó | 1 | `[ ]` |
| G16 | Màn hình chọn cách xử lý, không phải báo lỗi | Chia cho người không đủ mức mật thì hiện **bốn lựa chọn** kèm hệ quả từng cái: nâng mức mật người nhận · chia đặc cách có hạn · hạ mức mật văn bản · tách bản trích. Không hiện câu "không đủ quyền" rồi hết | 1 | `[ ]` |
| G17 | Hạ mức mật phải qua duyệt | Đổi từ Tuyệt mật xuống Mật là mở cho cả một nhóm người cùng lúc. Phải có luồng duyệt riêng, ghi lý do, vào nhật ký | 1 | `[ ]` |
| G18 | Bản trích mức mật thấp hơn | **Việc thật nằm ở C19, C20 và E11** — đây chỉ là dòng trỏ sang, vì bản trích phát sinh từ bài toán chia sẻ nhưng phần phải làm là soạn thảo cộng quan hệ. Mở bản gốc thấy hết các bản trích và ai đang xem cái nào | 1 | `[ ]` |
| G19 | Chia sẻ không lan và không chia tiếp | Chia văn bản cha **không** tự chia văn bản con — con có thể mật hơn cha. Người được chia **không** được chia tiếp, trừ khi bật riêng | 1 | `[ ]` |
| G20 | Thu hồi giữ nguyên dấu vết | Thu hồi là đánh dấu, **không xóa dòng chia sẻ**. Xóa thì mất luôn thông tin ai từng được xem — thứ cần nhất khi có sự cố rò rỉ | 1 | `[ ]` |
| G21 | Thu hồi hiện ngay ai đã kịp tải | Bấm thu hồi thì hiện luôn "3 người đã tải tệp về trước khi bị thu hồi: ...". **Tệp đã về máy thì hệ thống không thu hồi được** — cái làm được là cho biết phải đi nói chuyện với ai | 1 | `[ ]` |
| G22 | Thu hồi tự động | Hết hạn · nghỉ việc · chuyển phòng thì mất phần chia theo phòng ban nhưng giữ phần chia đích danh. Thu hồi tay thì luôn có người quên | 1 | `[ ]` |
| G23 | Rà soát chia sẻ định kỳ | Mỗi quý gửi cho người chịu trách nhiệm nội dung danh sách "văn bản của anh đang chia cho những ai", bấm một nút gia hạn hoặc thu hồi | 2 | `[ ]` |
| G24 | Nhật ký chia sẻ và thu hồi | Ai chia, cho ai, quyền gì, lý do, ai duyệt phần đặc cách, ai thu hồi, lúc nào. **Chỉ thêm, không sửa không xóa** | 1 | `[ ]` |

**Bốn cách ở G16, hệ quả khác hẳn nhau:**

| Cách | Phạm vi ảnh hưởng | Rủi ro chính |
|---|---|---|
| Nâng mức mật người nhận | **Mọi văn bản** ở mức đó, không chỉ văn bản này | Dễ làm nhất nên hay bị dùng nhất. Vài năm sau có vài chục người mức Tuyệt mật mà không ai nhớ vì sao |
| Chia đặc cách có hạn (G15) | Đúng một văn bản, đúng những người được nêu tên | Phải nhớ gia hạn. Bù lại bằng G22, G23 |
| Hạ mức mật văn bản (G17) | Mở cho tất cả người đủ mức mới | Không đảo ngược được về mặt thực tế — hạ xuống rồi thì người ta đã đọc rồi |
| Tách bản trích (C19) | Chỉ phần nội dung được tách | Tốn công soạn thêm. Nhưng là cách duy nhất giữ được bản gốc ở mức cũ |

---

# NHÓM H · LƯU TRỮ TỆP

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| H01 | Kho riêng tư hoàn toàn | Xem N02 | 1 | `[~]` |
| H02 | Link tạm sau khi kiểm quyền | Xem N03 | 1 | `[ ]` |
| H03 | Ghi nhật ký mọi lượt xem và tải | Ai, file nào, lúc nào, từ địa chỉ nào | 1 | `[ ]` |
| H04 | Chống trùng tệp bằng mã băm | Cùng một tệp tải lên nhiều lần thì lưu một bản | 2 | `[ ]` |
| H05 | Khóa chống xóa cho hồ sơ lưu trữ | Bật chế độ chỉ ghi một lần trên kho, không sửa không xóa được kể cả quản trị viên | 2 | `[ ]` |
| H06 | Phong tỏa pháp lý | Đang thanh tra thì chặn mọi lệnh xóa trong phạm vi, kể cả quản trị viên | 2 | `[ ]` |

---

# NHÓM I · BỘ MÁY PHÊ DUYỆT DÙNG CHUNG

> Danh sách đầy đủ tính năng của Lark Approver và phần nào lấy, phần nào không, ở [`03`](./03-lark-approver.md).

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| I01 | Khai luồng duyệt bằng giao diện | Không sửa mã nguồn, không deploy lại. Mỗi luồng gắn với một loại văn bản hoặc một loại chứng từ | 1 | `[ ]` |
| I02 | Các bước tuần tự | Mỗi bước có vai trò trong luồng: đề xuất · thực hiện · kiểm tra · phê duyệt | 1 | `[ ]` |
| I03 | Sáu cách chọn người duyệt | Người cụ thể · theo vai trò · trưởng phòng của người nộp · lên n cấp trên · người đại diện pháp nhân · lấy từ một ô trên phiếu | 1 | `[ ]` |
| I04 | Rẽ nhánh theo điều kiện | Theo số tiền, loại văn bản, phòng ban, pháp nhân, mức mật | 1 | `[ ]` |
| I05 | Nhiều người trong một bước | Ba chế độ: một người duyệt là xong · tất cả phải duyệt · duyệt lần lượt | 1 | `[ ]` |
| I06 | **Trùng thao tác thì bỏ qua** | Ba mức cấu hình: bỏ qua khi trùng liền kề · bỏ qua khi trùng bất kỳ chỗ nào phía trước · không bỏ qua | 1 | `[ ]` |
| I07 | **Người duyệt nghỉ việc thì chỉ định người khác** | Cấu hình người thay thế theo bước. **Cấm tùy chọn tự động duyệt qua** với văn bản | 1 | `[ ]` |
| I08 | Chặn tự duyệt | Người nộp không duyệt phiếu của chính mình. Nếu luồng bắt buộc trùng thì phải chuyển lên cấp trên | 1 | `[ ]` |
| I09 | Trả lại | Trả về người nộp hoặc về một bước cụ thể. **Bắt buộc nhập lý do** | 1 | `[ ]` |
| I10 | Từ chối | Kết thúc luồng, bắt buộc nhập lý do | 1 | `[ ]` |
| I11 | Rút lại | Người nộp rút phiếu khi chưa ai duyệt | 1 | `[ ]` |
| I12 | Ủy quyền có thời hạn | Sếp đi công tác thì hồ sơ không đứng im. Nhật ký ghi cả hai danh tính: "B duyệt thay A theo ủy quyền số 12" | 1 | `[ ]` |
| I13 | Chuyển tiếp | Người duyệt đẩy phiếu cho người khác xử lý, ghi rõ ai chuyển | 2 | `[ ]` |
| I14 | Thêm người duyệt trước hoặc sau mình | Xử lý tình huống cần hỏi thêm một bên | 2 | `[ ]` |
| I15 | Người nhận bản sao | Chỉ nhận thông báo, không duyệt | 1 | `[ ]` |
| I16 | Ý kiến và tệp đính kèm khi duyệt | Trao đổi ngay trên phiếu, không qua chat riêng | 1 | `[ ]` |
| I17 | Việc của tôi | Một chỗ gom mọi thứ đang chờ tôi, của cả văn thư và thu mua | 1 | `[ ]` |
| I18 | Hạn duyệt và nhắc | Mỗi bước có hạn. Quá hạn thì nhắc, quá lâu thì leo lên cấp trên | 1 | `[ ]` |
| I19 | Duyệt hàng loạt | Tick nhiều phiếu cùng loại, duyệt một lần | 2 | `[ ]` |
| I20 | Bản in dấu vết duyệt | In ra phiếu kèm đầy đủ ai duyệt lúc nào, ý kiến gì | 1 | `[ ]` |
| I21 | Phiên bản của luồng | Sửa luồng thì phiếu đang chạy vẫn theo luồng cũ cho tới khi xong | 1 | `[ ]` |
| I22 | Sao chép và mô phỏng luồng | Nhân bản một luồng để sửa, và chạy thử xem phiếu sẽ đi qua ai | 2 | `[ ]` |
| I23 | Bàn giao hàng loạt khi nghỉ việc | Người nghỉ việc còn 30 phiếu đang chờ, chuyển hết sang người khác trong một lần | 1 | `[ ]` |
| I24 | Báo cáo duyệt | Bao nhiêu phiếu, thời gian duyệt trung bình, ai đang tồn đọng nhiều nhất | 2 | `[ ]` |
| I25 | Áp cho đối tượng không phải văn bản | Bộ máy nhận mọi loại chứng từ. Bật cho 5 luồng của Thu mua bằng cờ | 2 | `[ ]` |
| I26 | Cờ bật tắt theo từng loại chứng từ | Tắt cờ là quay về đường duyệt cũ ngay, không cần deploy | 1 | `[ ]` |

---

# NHÓM J · BAN HÀNH VÀ PHÂN PHỐI

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| J01 | Vòng đời văn bản | nháp → đang duyệt → đã duyệt → có hiệu lực → bị thay thế / hết hiệu lực / bãi bỏ → lưu trữ | 1 | `[ ]` |
| J02 | Ký điện tử nội bộ | Bản ghi ký, mã băm tệp, thời điểm, địa chỉ. Đủ giá trị nội bộ | 1 | `[ ]` |
| J03 | Ghi rõ loại chữ ký trên giao diện | Không để người dùng nhầm giá trị pháp lý giữa ký nội bộ và ký số | 1 | `[ ]` |
| J04 | Ban hành | Cấp số, đóng phiên bản, chuyển sang có hiệu lực, gửi thông báo theo phạm vi | 1 | `[ ]` |
| J05 | Thông báo theo phạm vi áp dụng | Ai thuộc phạm vi thì nhận, qua chuông và tùy chọn qua thư | 1 | `[ ]` |
| J06 | Xác nhận đã đọc | Yêu cầu người trong phạm vi bấm xác nhận, có hạn. **Gắn với phiên bản cụ thể — bản mới ra thì phải xác nhận lại** | ? | `[ ]` |
| J07 | Báo cáo ai đã đọc ai chưa | Theo phòng ban, theo pháp nhân, kèm danh sách quá hạn | ? | `[ ]` |
| J08 | Ký số có giá trị pháp lý | Qua nhà cung cấp chứng thư số Việt Nam, tách một dịch vụ riêng vì cần thiết bị USB | ? | `[ ]` |
| J09 | Thu hồi văn bản đã ban hành | Có luồng duyệt riêng, giữ nguyên bản gốc, đánh dấu bị thu hồi và ghi lý do | 2 | `[ ]` |
| J10 | Nhãn "đã bị sửa đổi" trên văn bản hành chính | Mở Quyết định 15 phải thấy ngay nó đã bị sửa bởi Quyết định 47. **Bắt buộc, không phải tùy chọn** — không thấy thì người ta đọc điều khoản cũ và làm sai mà không ai phát hiện | 1 | `[ ]` |
| J11 | Quyết định ban hành kiểm ở mức phiên bản | Loại có khai "ban hành phải kèm Quyết định" thì mỗi lần sửa lớn phải kèm một Quyết định mới, không dùng lại Quyết định ban hành lần đầu | 1 | `[ ]` |

---

# NHÓM K · TRA CỨU

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| K01 | Danh sách và bộ lọc | Theo pháp nhân, loại, phòng ban, trạng thái, mức mật, khoảng ngày, người phụ trách | 1 | `[~]` |
| K02 | Tìm theo tiêu đề, số hiệu, số hiệu cũ | Đủ dùng cho bản đầu | 1 | `[ ]` |
| K03 | Kết quả tìm luôn qua kiểm quyền | Văn bản không được xem thì **không hiện cả trong kết quả**, kể cả tiêu đề | 1 | `[ ]` |
| K04 | Trang chi tiết văn bản | Thông tin, phiên bản, quan hệ cha con, phạm vi áp dụng, dấu vết duyệt, danh sách bản clone | 1 | `[ ]` |
| K05 | Tìm toàn văn tiếng Việt không dấu | Cần thêm hạ tầng tìm kiếm. Chờ trả lời câu hỏi C4 ở `00` | ? | `[ ]` |
| K06 | Trang chủ theo vai | Việc của tôi, văn bản áp dụng cho tôi, văn bản mới ban hành, sắp hết hiệu lực | 1 | `[ ]` |
| K07 | Xuất danh sách ra Excel | Có kiểm quyền xuất, ghi nhật ký | 2 | `[~]` |

---

# NHÓM L · AI

> Ràng buộc chung: **AI chỉ đọc, chỉ ghi vào bản nháp, không có đường nào để AI duyệt hay ban hành.** Tắt AI thì hệ thống vẫn chạy đủ nghiệp vụ.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| L01 | Chuyển ảnh thành văn bản | Người soạn chụp hoặc quét, AI nhận chữ, kết quả vào bản nháp để người sửa lại | 1 | `[ ]` |
| L02 | Đặt ảnh gốc cạnh văn bản để đối chiếu | Không bắt mở hai cửa sổ | 1 | `[ ]` |
| L03 | Trích thông tin từ tệp quét | Đoán loại văn bản, số hiệu, ngày, nơi ban hành để điền sẵn | 2 | `[ ]` |
| L04 | Cảnh báo trùng nội dung | So nội dung văn bản mới với văn bản đang hiệu lực, chỉ ra chỗ giống | 2 | `[ ]` |
| L05 | Tóm tắt và gợi ý từ khóa | Vào bản nháp, người duyệt lại | 2 | `[ ]` |
| L06 | Hỏi đáp trên kho văn bản | Truy hồi **trong phạm vi quyền của người đang hỏi**, mọi câu trả lời phải trích dẫn văn bản và điều khoản. Không trích dẫn được thì trả lời không tìm thấy căn cứ | 2 | `[ ]` |
| L07 | Cờ tắt AI | Tắt là hệ thống chạy bình thường, không lỗi màn hình nào | 1 | `[ ]` |

---

# NHÓM M · NHẬT KÝ, BÁO CÁO, THÔNG BÁO

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| M01 | Nhật ký chỉ ghi thêm | Không có đường sửa, không có đường xóa. Tài khoản ứng dụng ở cơ sở dữ liệu chỉ được cấp quyền thêm và đọc trên bảng này | 1 | `[~]` |
| M02 | Ghi cả hành động xem, tải, in, tìm | Không chỉ ghi sửa xóa | 1 | `[~]` |
| M03 | Màn hình xem nhật ký có phân quyền | Xem N06 | 1 | `[ ]` |
| M04 | Ghi cả hai danh tính khi làm theo ủy quyền | | 1 | `[ ]` |
| M05 | Thông báo trong chuông | Dùng lại của Thu mua, thêm cột app | 1 | `[~]` |
| M06 | Thông báo qua thư | Dùng lại đường gửi thư hiện có. Môi trường dev vẫn tắt thư | 1 | `[x]` |
| M07 | Nhắc rà soát định kỳ | Loại văn bản khai chu kỳ 12 hoặc 24 tháng, tới hạn nhắc người chịu trách nhiệm nội dung | 2 | `[ ]` |
| M08 | Cảnh báo sắp hết hiệu lực | | 2 | `[ ]` |
| M09 | Bảng điều khiển văn thư | Số văn bản theo loại, theo pháp nhân, đang chờ duyệt, quá hạn, chưa xác nhận đọc | 2 | `[ ]` |

---

# NHÓM S · SỔ VĂN BẢN ĐI VÀ ĐẾN

> Chờ trả lời câu hỏi A1 ở `00`. Nếu bản đầu không làm thì vẫn phải tạo bảng dữ liệu từ đầu, vì thêm cột vào bảng đã có vài chục nghìn dòng tốn hơn nhiều.

| Mã | Tính năng | Nội dung | Bản | Có sẵn |
|---|---|---|---|---|
| S01 | Sổ văn bản đi | Mỗi pháp nhân một sổ. Số thứ tự, năm, loại, người ký, ngày ban hành, nơi nhận | ? | `[ ]` |
| S02 | Sổ văn bản đến | Số đến, nơi gửi, số hiệu bên gửi, ngày nhận, người được giao xử lý, hạn xử lý | ? | `[ ]` |
| S03 | Theo dõi văn bản đến quá hạn | | ? | `[ ]` |
| S04 | Danh bạ đơn vị gửi nhận | Xem A07 | 1 | `[ ]` |

---

## Tổng hợp

| Nhóm | Số tính năng | Thuộc bản đầu |
|---|---|---|
| N · Việc nền | 11 | 10 |
| A · Danh mục và cấu hình | 10 | 7 |
| B · Yêu cầu văn bản | 7 | 7 |
| C · Soạn thảo và phiên bản | 20 | 15 |
| D · Số văn bản | 8 | 7 |
| E · Quan hệ cha con | 11 | 9 |
| F · Phạm vi và clone | 13 | 12 |
| G · Quyền truy cập | 24 | 20 |
| H · Lưu trữ tệp | 6 | 3 |
| I · Bộ máy duyệt | 26 | 20 |
| J · Ban hành và phân phối | 11 | 7 |
| K · Tra cứu | 7 | 5 |
| L · AI | 7 | 3 |
| M · Nhật ký báo cáo thông báo | 9 | 6 |
| S · Sổ đi đến | 4 | 1 |
| **Tổng** | **174** | **132** |

Hai nhóm chiếm gần một nửa khối lượng là **I bộ máy duyệt** và **F phạm vi cộng clone**. Đây cũng là hai nhóm dùng lại được nhiều nhất về sau: bộ máy duyệt sẽ thay 5 luồng viết tay của Thu mua, còn phần phạm vi là nền cho mọi phân hệ nhiều pháp nhân sau này.

Tiếp theo: [`02` Lộ trình phát triển](./02-lo-trinh-phat-trien.md) · [`05` Vòng đời phiên bản](./05-vong-doi-phien-ban.md)
