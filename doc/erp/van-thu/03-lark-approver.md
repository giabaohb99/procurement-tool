# 03 · TÍNH NĂNG LARK APPROVER — LẤY GÌ, BỎ GÌ

> Dùng làm bảng đối chiếu khi thiết kế bộ máy phê duyệt dùng chung (phase 3 trong [`02`](./02-lo-trinh-phat-trien.md))
> **Đây là bảng đối chiếu, không phải bản mô tả yêu cầu.** Chốt lấy gì rồi mới viết yêu cầu.

---

## 1. Lark Approver làm được gì, tóm trong năm dòng

Lark Approver là một công cụ cho phép **người không biết lập trình tự dựng ra một quy trình duyệt**: kéo thả các ô để tạo biểu mẫu, kéo thả các nút để tạo đường đi của phiếu, chọn ai duyệt bước nào, đặt điều kiện rẽ nhánh. Xong là dùng được ngay, không cần đội phần mềm.

Hiện tại Thu mua có **5 luồng duyệt viết tay trong mã nguồn**. Muốn đổi người duyệt phải sửa mã và deploy lại. Đó là thứ cần thay.

**Chú ý:** phần dưới mô tả theo hiểu biết chung về sản phẩm Lark Approver, chưa phải kết quả bấm thử từng nút. Trước khi chốt, nên **mở tài khoản Lark dùng thử** và xem thật ba nhóm: **E trùng người duyệt**, **F người duyệt đã nghỉ việc**, **J2 phiên bản của luồng**. Ba chỗ này là ba chỗ dễ mô tả khác với thực tế nhất, và cũng là ba chỗ tốn công nhất nếu thiết kế sai.

---

## 2. Cách đọc bảng

| Kết luận | Nghĩa |
|---|---|
| **Lấy — bản 1** | Bắt buộc có ngay ở bản đầu tiên |
| **Lấy — bản sau** | Có giá trị nhưng không chặn ai làm việc |
| **Lấy nhưng làm khác** | Ý tưởng đúng, cách Lark làm không hợp với mình |
| **Không lấy** | Không phù hợp, hoặc đắt hơn giá trị mang lại |

---

## 3. Nhóm A · Thiết kế biểu mẫu

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| A1 | Kéo thả ô nhập | Người quản trị tự tạo biểu mẫu bằng cách kéo các ô: chữ ngắn, chữ dài, số, tiền, ngày, chọn một, chọn nhiều, người, phòng ban, tệp, ảnh | **Không lấy** ở bản 1 |
| A2 | Bảng con trong biểu mẫu | Một phiếu có nhiều dòng chi tiết, ví dụ danh sách hàng hóa | **Không lấy** |
| A3 | Ô tính toán | Ô tự cộng từ các ô khác | **Không lấy** |
| A4 | Ô hiện theo điều kiện | Chọn "có" thì mới hiện ô lý do | **Lấy — bản sau** |
| A5 | Ô bắt buộc và quy tắc kiểm tra | | **Lấy — bản 1**, nhưng khai trong mã nguồn |
| A6 | Bản nháp phiếu | Điền dở lưu lại, mai điền tiếp | **Lấy — bản 1** |

**Vì sao không lấy bộ kéo thả biểu mẫu:** đây là phần tốn công nhất trong cả Lark Approver, và mình **không cần**. Phiếu của mình không phải phiếu tự do — nó là văn bản, đơn mua hàng, yêu cầu thanh toán, mỗi thứ đã có bảng dữ liệu riêng với các trường cố định. Làm bộ kéo thả biểu mẫu nghĩa là tự dựng thêm một cơ sở dữ liệu thứ hai bên trong cơ sở dữ liệu đang có, dữ liệu nằm trong ô JSON, không truy vấn được, không báo cáo được, không ràng buộc được.

Thứ mình cần từ Lark là **phần đường đi của phiếu**, không phải phần biểu mẫu.

---

## 4. Nhóm B · Thiết kế đường đi của phiếu

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| B1 | Nút phê duyệt | Một bước, có người xử lý, phải bấm duyệt hoặc từ chối | **Lấy — bản 1** |
| B2 | Nút nhận bản sao | Chỉ nhận thông báo, không phải bấm gì | **Lấy — bản 1** |
| B3 | Nút điều kiện rẽ nhánh | Trên 50 triệu thì qua giám đốc, dưới thì không | **Lấy — bản 1** |
| B4 | Nhánh song song | Kế toán và Pháp chế xem cùng lúc, ai xong trước cũng được | **Lấy — bản 1** |
| B5 | Nút xử lý việc | Bước không phải duyệt mà là làm một việc rồi báo đã xong | **Lấy — bản sau** |
| B6 | Nhánh mặc định khi không điều kiện nào đúng | | **Lấy — bản 1**, bắt buộc |
| B7 | Luồng con gọi luồng khác | Duyệt xong đơn mua hàng thì tự khởi tạo luồng thanh toán | **Lấy — bản sau** |
| B8 | Xem trước đường đi trước khi nộp | Người nộp thấy phiếu sẽ qua những ai | **Lấy — bản 1** |

B6 nhìn nhỏ nhưng là chỗ dễ hỏng nhất: một phiếu rơi vào trạng thái không nhánh nào nhận thì nó **biến mất khỏi mọi danh sách** — không ai thấy, không ai xử lý, tới lúc có người hỏi mới phát hiện. Phải có nhánh mặc định, và phải có màn hình liệt kê phiếu đang kẹt.

---

## 5. Nhóm C · Cách chọn người duyệt

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| C1 | Người cụ thể | Chỉ đích danh một hoặc vài người | **Lấy — bản 1** |
| C2 | Theo vai trò | Ai đang giữ vai trò "Trưởng phòng Nhân sự" thì người đó duyệt | **Lấy — bản 1** |
| C3 | Trưởng phòng của người nộp | Tự tìm theo cây tổ chức | **Lấy nhưng làm khác** |
| C4 | Lên n cấp trên | Đi lên 2 cấp trong cây tổ chức | **Lấy nhưng làm khác** |
| C5 | Lên tới một cấp bậc nhất định | Đi lên tới khi gặp người từ cấp Giám đốc trở lên | **Lấy — bản sau** |
| C6 | Lấy từ một ô trên phiếu | Người soạn chọn ai duyệt | **Lấy — bản 1**, nhưng chỉ cho vài loại phiếu, và người chọn phải nằm trong danh sách cho phép |
| C7 | Cả phòng ban | Ai trong phòng đó cũng duyệt được | **Lấy — bản 1** |
| C8 | Người nộp tự duyệt | | **Không lấy** — xem mục 8 |

**Vì sao C3 và C4 phải làm khác:** cây tổ chức của mình không phải một cây. Một phòng ban có mặt ở nhiều pháp nhân, và **trưởng phòng ở mỗi pháp nhân có thể là người khác nhau**. Lark giả định mỗi người có đúng một cấp trên. Mình phải hỏi thêm một câu: "trưởng phòng của phòng nào, **tại pháp nhân nào**". Đây chính là lý do cần bảng nối phòng ban với pháp nhân ở tính năng A06.

Nếu bỏ qua chỗ này thì hậu quả rất cụ thể: phiếu của nhân viên phòng Kế toán ở công ty A bay sang trưởng phòng Kế toán của công ty B duyệt.

---

## 6. Nhóm D · Nhiều người trong một bước

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| D1 | Một người duyệt là xong | Ba người cùng nhận, ai bấm trước thì phiếu đi tiếp | **Lấy — bản 1** |
| D2 | Tất cả phải duyệt | Đủ ba chữ ký mới đi tiếp | **Lấy — bản 1** |
| D3 | Duyệt lần lượt | A xong mới tới B, B xong mới tới C | **Lấy — bản 1** |
| D4 | Đủ tỷ lệ là qua | 2 trên 3 người đồng ý | **Lấy — bản sau** |
| D5 | Một người từ chối là hỏng cả bước | | **Lấy — bản 1**, đặt mặc định như vậy |

---

## 7. Nhóm E · Trùng người duyệt

Đây là một trong hai thứ được nêu đích danh khi giao việc.

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| E1 | Bỏ qua khi trùng liền kề | Bước 2 và bước 3 cùng một người thì bước 3 tự qua | **Lấy — bản 1** |
| E2 | Bỏ qua khi trùng bất kỳ chỗ nào phía trước | Người đó đã duyệt ở bất kỳ bước nào trước đó thì các bước sau của người đó tự qua | **Lấy — bản 1** |
| E3 | Không bỏ qua, phải bấm đủ | | **Lấy — bản 1** |
| E4 | Bỏ qua khi người nộp cũng là người duyệt | Người nộp trùng người duyệt thì bước đó tự qua | **Lấy nhưng làm khác** — xem mục 8 |

Ba mức E1, E2, E3 khai **theo từng luồng**, không phải một cấu hình chung cho cả hệ thống. Với văn bản có thể chọn E1, với đơn mua hàng nhỏ có thể chọn E2, với văn bản mật thì E3.

**Bắt buộc:** khi hệ thống tự bỏ qua một bước, nhật ký phải ghi rõ **"bước 3 tự động qua vì ông X đã duyệt ở bước 2"**. Không được để bản in dấu vết duyệt trông như thể ông X đã ký hai lần, cũng không được để trống như thể bước 3 không tồn tại.

---

## 8. Nhóm F · Người duyệt không có hoặc đã nghỉ việc

Đây là thứ thứ hai được nêu đích danh, và là chỗ **phải cẩn thận nhất trong cả tài liệu này**.

Lark có ba tùy chọn khi hệ thống tìm không ra người duyệt cho một bước:

| # | Tùy chọn của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| F1 | **Tự động duyệt qua** | Không tìm ra người thì coi như đã duyệt, phiếu đi tiếp | **CẤM** với văn bản. Chỉ cân nhắc cho phiếu nội bộ giá trị thấp, và phải ghi rõ trong nhật ký |
| F2 | **Chuyển cho quản trị viên** | Không tìm ra người thì đẩy cho quản trị hệ thống xử lý | **Lấy — bản 1** |
| F3 | **Chỉ định người thay thế** | Khai sẵn người thay cho từng bước | **Lấy — bản 1** — đây là lựa chọn được yêu cầu |
| F4 | Người nộp tự duyệt khi không tìm ra ai | | **Không lấy** |

**Vì sao cấm F1:** một văn bản tự duyệt qua vì "không tìm thấy người duyệt" là một văn bản **có hiệu lực mà không ai chịu trách nhiệm**. Trên giấy tờ nó giống hệt văn bản được duyệt đúng quy trình. Khi có tranh chấp, không phân biệt được. Với đơn xin nghỉ phép thì tùy chọn này tiện; với quyết định của Tập đoàn thì nó là một lỗ hổng.

**Cách làm đề nghị**, xếp theo thứ tự:
1. Người duyệt của bước còn làm việc → giao cho người đó.
2. Người đó đã nghỉ hoặc bị tắt tài khoản → giao cho **người thay thế khai sẵn ở bước đó** (F3).
3. Không khai người thay thế → giao cho **trưởng phòng của người đó tại pháp nhân đó**.
4. Vẫn không có → giao cho **quản trị văn thư** (F2), kèm cảnh báo đỏ trên màn hình phiếu.
5. **Không có bước 5.** Phiếu đứng lại chứ không tự đi tiếp.

Kèm theo:

| # | Việc phải có | Kết luận |
|---|---|---|
| F5 | Bàn giao hàng loạt khi có người nghỉ việc | **Lấy — bản 1** |
| F6 | Cảnh báo trước khi tắt tài khoản: "người này đang giữ 12 phiếu" | **Lấy — bản 1** |
| F7 | Màn hình phiếu đang kẹt không ai xử lý | **Lấy — bản 1** |

F6 giải quyết vấn đề ở gốc: chặn ngay lúc Nhân sự bấm nút tắt tài khoản, thay vì để phát hiện ra sau vài tuần khi có người đi tìm phiếu.

---

## 9. Nhóm G · Người duyệt làm được gì

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| G1 | Duyệt | | **Lấy — bản 1** |
| G2 | Từ chối | Kết thúc phiếu | **Lấy — bản 1**, bắt buộc nhập lý do |
| G3 | Trả lại người nộp | Sửa rồi nộp lại | **Lấy — bản 1**, bắt buộc nhập lý do |
| G4 | Trả lại một bước cụ thể | Trả về đúng bước 2 chứ không về đầu | **Lấy — bản 1** |
| G5 | Nộp lại sau khi bị trả | Phiếu đi lại từ bước bị trả hay từ đầu — cấu hình được | **Lấy — bản 1** |
| G6 | Chuyển tiếp cho người khác | Đẩy việc sang người khác xử lý | **Lấy — bản sau** |
| G7 | Thêm người duyệt trước mình | Cần hỏi ý một bên trước khi mình ký | **Lấy — bản sau** |
| G8 | Thêm người duyệt sau mình | | **Lấy — bản sau** |
| G9 | Ý kiến kèm tệp và ảnh | | **Lấy — bản 1** |
| G10 | Nhắc tên người khác trong ý kiến | | **Lấy — bản sau** |
| G11 | Duyệt hàng loạt | Tick nhiều phiếu, duyệt một lần | **Lấy — bản sau**, và **cấm với văn bản mật** |
| G12 | Người nộp rút phiếu | Khi chưa ai duyệt | **Lấy — bản 1** |
| G13 | Người nộp thúc giục | Bấm nút nhắc người đang giữ phiếu | **Lấy — bản sau** |

G6, G7, G8 để bản sau vì chúng làm dấu vết duyệt phức tạp hẳn lên: đường đi thực tế không còn giống đường đi đã khai. Chưa cần thì chưa làm.

---

## 10. Nhóm H · Ủy quyền và thay mặt

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| H1 | Ủy quyền có thời hạn | Từ ngày tới ngày, mọi phiếu của tôi chuyển cho người này | **Lấy — bản 1** |
| H2 | Ủy quyền theo loại phiếu | Chỉ ủy quyền phiếu dưới 20 triệu | **Lấy — bản sau** |
| H3 | Quản trị viên đặt ủy quyền hộ | Sếp quên khai trước khi đi | **Lấy — bản 1** |
| H4 | Nhật ký ghi cả hai danh tính | "B duyệt thay A theo ủy quyền số 12" | **Lấy — bản 1**, bắt buộc |
| H5 | Ủy quyền dây chuyền | A ủy cho B, B lại ủy cho C | **Không lấy** — chặn ở tầng dịch vụ |

H5 nghe hợp lý nhưng tạo ra vòng lặp và tạo ra tình huống không ai biết ai đang thật sự có quyền. Chặn thẳng, báo lỗi rõ ràng.

---

## 11. Nhóm I · Theo dõi và nhắc

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| I1 | Việc của tôi | Một chỗ gom mọi thứ đang chờ tôi | **Lấy — bản 1** |
| I2 | Phiếu tôi đã nộp, đang ở đâu | | **Lấy — bản 1** |
| I3 | Phiếu tôi đã duyệt | | **Lấy — bản 1** |
| I4 | Hạn xử lý theo bước | | **Lấy — bản 1** |
| I5 | Nhắc khi sắp quá hạn và khi đã quá hạn | | **Lấy — bản 1** |
| I6 | Leo lên cấp trên khi quá hạn quá lâu | | **Lấy — bản sau** |
| I7 | Thông báo trong ứng dụng | | **Lấy — bản 1** — dùng lại chuông đang có |
| I8 | Thông báo qua thư | | **Lấy — bản 1** — dùng lại đường gửi thư đang có |
| I9 | Duyệt ngay trong tin nhắn chat | Bấm duyệt không cần mở ứng dụng | **Không lấy** — mình không có nền tảng chat |
| I10 | Duyệt trên điện thoại | | **Lấy — bản 1** — giao diện web đã chạy được trên điện thoại |
| I11 | Bản in dấu vết duyệt | In ra kèm ai duyệt lúc nào, ý kiến gì | **Lấy — bản 1** |

I11 quan trọng hơn vẻ ngoài của nó: khi kiểm toán hoặc thanh tra hỏi "ai duyệt cái này", câu trả lời phải là một tờ giấy in ra được, không phải một ảnh chụp màn hình.

---

## 12. Nhóm J · Quản trị luồng

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| J1 | Bật tắt một luồng | | **Lấy — bản 1** |
| J2 | Phiên bản của luồng | Sửa luồng thì phiếu đang chạy vẫn theo bản cũ | **Lấy — bản 1**, bắt buộc |
| J3 | Sao chép luồng để sửa | | **Lấy — bản sau** |
| J4 | Giới hạn luồng theo phòng ban hoặc pháp nhân | Cùng loại văn bản nhưng công ty A duyệt khác công ty B | **Lấy — bản 1** |
| J5 | Chạy thử luồng | Nhập thử dữ liệu, xem phiếu sẽ qua ai, không tạo phiếu thật | **Lấy — bản sau** |
| J6 | Ai được sửa luồng | Phân quyền riêng cho việc thiết kế luồng | **Lấy — bản 1** |
| J7 | Nhật ký ai sửa luồng, sửa gì | | **Lấy — bản 1** |
| J8 | Nhập xuất luồng ra tệp | | **Không lấy** |

J2 là ràng buộc cứng, không có đường vòng. Nếu sửa luồng mà phiếu đang chạy nhảy sang luồng mới thì sẽ có phiếu đã qua bước 3 bỗng phải quay lại bước 2 của luồng mới, hoặc tệ hơn là nhảy thẳng tới bước cuối. Cách làm: mỗi phiếu khi khởi tạo **chép luôn định nghĩa luồng vào phiên chạy của nó**, không tham chiếu tới bản luồng đang sống.

J4 là chỗ Lark yếu và mình bắt buộc phải mạnh — mình có 13 pháp nhân.

---

## 13. Nhóm K · Báo cáo và nối ra ngoài

| # | Tính năng của Lark | Nó làm gì | Kết luận |
|---|---|---|---|
| K1 | Đếm số phiếu theo luồng, theo trạng thái | | **Lấy — bản sau** |
| K2 | Thời gian duyệt trung bình mỗi bước | | **Lấy — bản sau** |
| K3 | Ai đang tồn đọng nhiều nhất | | **Lấy — bản sau** |
| K4 | Xuất danh sách phiếu ra Excel | | **Lấy — bản sau**, có kiểm quyền và ghi nhật ký |
| K5 | Gọi ra hệ thống khác khi phiếu được duyệt | | **Lấy — bản sau** — đã có kế hoạch module webhook |
| K6 | Giao diện lập trình để hệ ngoài tạo phiếu | | **Không lấy** ở bản 1 |
| K7 | Nối với chấm công, nghỉ phép, công tác phí | | **Không lấy** — thuộc HRM, làm sau |

K2 và K3 nhìn thì phụ nhưng lại là lý do bộ máy này tồn tại được lâu: khi có người hỏi "vì sao duyệt chậm", có số liệu chứ không phải cảm giác.

---

## 14. Ba chỗ Lark có mà mình cố ý làm khác

| Chỗ | Lark làm | Mình làm | Vì sao |
|---|---|---|---|
| Biểu mẫu | Kéo thả tự do, dữ liệu nằm trong ô JSON | Mỗi loại phiếu là một bảng dữ liệu thật, luồng duyệt gắn vào bảng đó | Cần báo cáo, cần ràng buộc, cần truy vấn. Ô JSON không làm được |
| Không tìm ra người duyệt | Có tùy chọn tự động duyệt qua | Phiếu đứng lại, đẩy cho quản trị | Văn bản tự duyệt là văn bản không ai chịu trách nhiệm |
| Cây tổ chức | Mỗi người một cấp trên | Trưởng phòng theo **cặp phòng ban và pháp nhân** | Một phòng ban có mặt ở nhiều pháp nhân, trưởng phòng mỗi nơi khác nhau |

---

## 15. Bốn chỗ mình cần mà Lark không có

| Việc | Vì sao cần | Ở đâu trong `01` |
|---|---|---|
| Duyệt xong thì **cấp số văn bản** trong cùng một giao dịch | Số hiệu không được trùng, không được nhảy cóc. Cấp sau khi duyệt xong là có kẽ hở | D02, D06 |
| Duyệt xong thì **đóng băng phiên bản và khóa sửa** | Văn bản đã ban hành mà sửa được nội dung là hỏng toàn bộ giá trị pháp lý | C04, C07 |
| Luồng duyệt phải **tôn trọng mức mật** | Người duyệt bước 3 không đủ mức mật thì không được nhìn thấy nội dung, kể cả khi họ là người duyệt | G03, G04, G07 |
| Duyệt xong thì **clone xuống các pháp nhân con** và mở luồng duyệt mới ở từng nơi | Cơ chế đặc thù của mô hình tập đoàn | F06–F11 |

Bốn việc trên là lý do **không dùng thẳng Lark mà tự làm**: chúng không phải là tính năng thêm vào bên cạnh bộ máy duyệt, chúng phải nằm **bên trong cùng một giao dịch** với hành động duyệt. Gọi sang một hệ ngoài rồi chờ nó báo về thì luôn có khoảng thời gian ở giữa, và trong khoảng đó dữ liệu sai.

---

## 16. Tổng kết

Đã rà 82 mục:

| Kết luận | Số mục |
|---|---|
| Lấy — bản 1 | 48 |
| Lấy — bản sau | 20 |
| Lấy nhưng làm khác | 3 |
| Không lấy | 10 |
| Cấm | 1 |

Nhóm "lấy bản 1" chính là 20 tính năng I01–I26 đánh dấu bản 1 trong [`01`](./01-danh-sach-tinh-nang.md) — phase 3 trong [`02`](./02-lo-trinh-phat-trien.md).

**Việc nên làm trước khi viết dòng mã đầu tiên của phase 3:** lấy 5 luồng duyệt thật đang chạy của Thu mua, cộng 3 luồng của văn thư (duyệt yêu cầu văn bản, duyệt nội dung văn bản, duyệt bản clone ở pháp nhân con), **khai thử cả 8 luồng ra giấy** bằng đúng mô hình dữ liệu định làm. Chỗ nào khai không nổi thì mô hình còn thiếu, và sửa lúc còn trên giấy rẻ hơn sửa sau khi đã có 200 phiếu chạy trong đó.

---

Tiếp theo: [`04` Các bảng dữ liệu](./04-bang-du-lieu.md)
