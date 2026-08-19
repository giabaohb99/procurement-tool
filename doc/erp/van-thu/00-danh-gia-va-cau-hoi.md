# 00 · ĐÁNH GIÁ CÁCH LÀM & CÂU HỎI CẦN CHỐT

> Quản lý văn thư xây trên nền mã nguồn Thu mua · bản 1.0 · 13/08/2026
> Đọc trước khi đọc `01` danh sách tính năng.

---

## 1. Tóm tắt trong một trang

Yêu cầu mới: đẩy quản lý văn thư lên làm trước, và **xây thẳng trên mã nguồn Thu mua đang chạy** thay vì dựng một hệ riêng.

Ý kiến của tôi: **làm được, và nên làm**, nhưng có một điều kiện không thương lượng được — phải vá ba lỗ hổng bảo mật của phần lõi **trước khi** đưa văn bản mật vào hệ thống. Nếu bỏ qua bước này thì phần "quyền truy cập" và "văn bản bảo mật" chỉ là hình vẽ trên giao diện, còn file thật vẫn nằm sau một đường link ai có cũng mở được.

Ba việc chốt lại:

| | Nội dung | Kết luận |
|---|---|---|
| 1 | Xây trong hệ Thu mua thay vì hệ riêng | Đồng ý. Tiết kiệm khoảng 24 bảng dữ liệu và toàn bộ phần tổ chức, tài khoản, phân quyền. Đổi lại phải sửa phần lõi trên hệ đang chạy thật |
| 2 | Clone văn bản Tập đoàn xuống từng pháp nhân | Đồng ý, nhưng **là một hành động có kiểm soát, không phải mặc định**. Mặc định vẫn là một văn bản gắn phạm vi áp dụng |
| 3 | Link R2 công khai — "để phase sau" | **Không đồng ý để phase sau.** Đây là việc đầu tiên phải làm, chi tiết ở mục 4.6 |

---

## 2. Hai quyết định cũ bị đảo — cần ghi nhận rõ

Bộ tài liệu thiết kế văn thư ở `D:\New folder\quanlytailieu\docs\` (18 tệp, chốt ngày 04/08/2026) có hai quyết định nay đã khác. Ghi ra đây để sau này không ai đọc nhầm tài liệu cũ.

### 2.1 · Trước: hệ thống độc lập — Nay: xây chung

Quyết định cũ (ADR-01): *"Hệ thống văn thư hoàn toàn độc lập — cơ sở dữ liệu riêng, người dùng riêng, phân quyền riêng. Quan hệ duy nhất với Thu mua là clone mã nguồn một lần."*

**Được gì khi xây chung:**

| | Nếu làm hệ riêng | Nếu xây chung |
|---|---|---|
| Danh mục 13 pháp nhân, 18 phòng ban | Nhập lại, rồi phải đồng bộ mãi mãi | Dùng luôn |
| Tài khoản người dùng | Mỗi người 2 tài khoản, hoặc phải làm đăng nhập Google cho cả hai | Một tài khoản |
| Nhân sự nghỉ việc | Phải tắt ở hai nơi, quên một nơi là lỗ hổng | Tắt một chỗ |
| Bảng cần tạo mới | 42 bảng | Khoảng 24 bảng |
| Bộ máy duyệt | Viết riêng cho văn thư | Viết một lần, Thu mua dùng lại được |
| Thời gian dựng nền | 3–4 tuần | 0 |

**Mất gì:**

| # | Vấn đề | Mức độ |
|---|---|---|
| 1 | Danh sách đối tượng phân quyền tăng từ 28 lên khoảng 40. Màn hình phân quyền dài gấp rưỡi, người quản trị dễ tick nhầm | Trung bình. Xử lý bằng cách nhóm đối tượng theo phân hệ trên giao diện |
| 2 | Mỗi lần cập nhật văn thư là deploy lại hệ Thu mua đang chạy thật | Trung bình. Xử lý bằng cờ tính năng và bộ test hồi quy bắt buộc xanh |
| 3 | Một cơ sở dữ liệu gánh hai nghiệp vụ, số bảng từ 57 lên khoảng 81 | Thấp. Vẫn trong tầm của MySQL 8.4 |
| 4 | **Ba lỗi của phần lõi trước đây "chấp nhận được với Thu mua" thì nay không chấp nhận được nữa** | **Cao. Đây là điểm nặng nhất, xem mục 3** |

Trước đây ba lỗi này định sửa trên **bản clone**, tức là sửa trên mã nguồn mới, không ai đang dùng, sai cũng không sao. Nay phải sửa **trên hệ đang chạy thật với gần 300 tài khoản**. Đây là chỗ chuyển toàn bộ rủi ro từ dự án mới sang hệ đang vận hành.

### 2.2 · Trước: không nhân bản văn bản mẹ — Nay: clone xuống từng pháp nhân

Quyết định cũ (04/08/2026): *"Tuyệt đối không nhân bản văn bản mẹ thành 12 bản y hệt cho 12 công ty con. Sau 6 tháng sẽ có 12 bản khác nhau và không ai biết bản nào đúng."*

Yêu cầu mới: clone thông tin văn bản, gửi email cho từng pháp nhân kèm bản nháp vừa clone; họ để nguyên hoặc soạn lại cho đúng pháp nhân của mình.

**Hai cách này không mâu thuẫn — chúng dùng cho hai tình huống khác nhau:**

| Tình huống | Cách | Kết quả |
|---|---|---|
| Nội dung giống hệt cho mọi công ty con (thông báo nghỉ Tết, quy chế bảo mật thông tin) | **Một văn bản, gắn phạm vi áp dụng** | Một số hiệu, một nơi sửa, sửa một lần là 13 công ty thấy bản mới ngay |
| Pháp luật buộc pháp nhân con tự đứng tên, hoặc nội dung phải khác (hạn mức khác, ngành nghề khác) | **Clone thành bản nháp riêng** | Mỗi công ty một số hiệu riêng, người ký riêng, hiệu lực riêng |

Đề xuất: **giữ cả hai, để phạm vi áp dụng làm mặc định**, và bổ sung clone như một nút bấm có điều kiện.

**Bốn điều kiện bắt buộc để clone không thành thảm họa** — nếu thiếu bất kỳ điều nào thì đúng như tài liệu cũ cảnh báo, sau hai năm sẽ có 12 bản lệch nhau:

1. Bản clone **luôn giữ liên kết ngược** về bản gốc (quan hệ *căn cứ theo*). Không có nút nào xóa được liên kết này.
2. Bản clone **mang số hiệu của pháp nhân con**, không dùng lại số của Tập đoàn.
3. Khi bản gốc lên phiên bản mới, **mọi bản clone tự động bị đánh dấu "cần rà lại"**, người phụ trách nhận thông báo, và trạng thái này hiện ngay trên danh sách.
4. Có **một màn hình trả lời được câu "12 công ty con đang ở phiên bản nào của quy chế này"** — ai đã ban hành, ai còn nháp, ai chưa đụng tới, ai đang lệch bản.

Nếu bốn điều trên có đủ thì clone là tính năng tốt. Thiếu điều 3 và 4 thì đây chính là cái vấn đề mà hệ thống sinh ra để giải quyết.

---

## 3. Ba lỗ hổng phải vá trước — không phải việc "làm sau"

Ba lỗi này đã được ghi trong tài liệu thiết kế cũ với ghi chú *"chấp nhận được với hệ thu mua, không chấp nhận được với hệ tài liệu có phân loại mật"*. Nay hai hệ là một, nên phải sửa.

| # | Lỗi hiện tại | Hậu quả khi có văn bản mật | Cách sửa |
|---|---|---|---|
| **1** | `tab_file` có cột `url` lưu **link công khai vĩnh viễn**; kho R2 đang bật đường dẫn công khai | Ai có link đều mở được, kể cả người đã nghỉ việc, kể cả link bị chuyển tiếp trong Zalo. **Toàn bộ phân quyền bị vô hiệu** | Tắt hẳn đường dẫn công khai cho file văn thư. Chỉ cấp link tạm sống 60–120 giây, sinh sau khi đã kiểm quyền và ghi nhật ký |
| **2** | Bộ nhớ đệm quyền nằm trong tiến trình, sống 60 giây; chạy nhiều tiến trình thì mỗi tiến trình một bản riêng | Thu hồi quyền xem văn bản mật có thể trễ tới 60 giây và **không đều giữa các tiến trình** | Chuyển sang Redis (đã có sẵn) kèm kênh xóa đệm tức thì |
| **3** | Phạm vi phòng ban khớp bằng **tên chuỗi**, không phải bằng ID | Đổi tên phòng ban là **mất quyền hàng loạt, im lặng, không báo lỗi**. Tái cơ cấu là chuyện thường ở tập đoàn | Khớp bằng `department_id`. Tên chỉ để hiển thị |

Ngoài ba lỗi trên, khi rà mã nguồn ngày 12/08/2026 còn hai chỗ đang hở thật, phải vá cùng đợt:

| # | Chỗ hở | Hậu quả |
|---|---|---|
| **4** | Nhật ký thao tác đọc được không cần quyền; để trống mã bản ghi thì trả về nhật ký của mọi bản ghi | Người bình thường đọc được dấu vết thao tác trên văn bản mật |
| **5** | Loại trừ phòng ban trong phân quyền **lưu được nhưng không có tác dụng** — mã nguồn tra một tên trường, cấu hình lại khai một tên khác | Người quản trị tick "loại trừ phòng X" rồi yên tâm, nhưng phòng X vẫn xem được |

---

## 4. Đánh giá từng nhóm tính năng đã nêu

### 4.1 · Soạn thảo, form chuẩn, AI chuyển ảnh thành văn bản

**Yêu cầu văn bản phải được duyệt mới cho soạn** — đồng ý hoàn toàn. Đây là chốt chặn quan trọng nhất: nó ngăn tình trạng ai cũng đẻ ra quy trình rồi không ai biết cái nào đang có hiệu lực. Thiết kế cũ đã có bảng cho việc này, chỉ cần cho nó chạy qua bộ máy duyệt chung.

**"Mỗi loại văn bản có một form chuẩn riêng"** — chỗ này cần làm rõ, vì có hai cách hiểu và chi phí chênh nhau nhiều lần:

| Cách hiểu | Nội dung | Chi phí | Đề nghị |
|---|---|---|---|
| **A. Mẫu tệp** | Mỗi loại gắn một tệp Word mẫu. Người soạn tải về, điền, tải lên lại. Hệ thống quản lý phần thông tin bên ngoài (tiêu đề, loại, số hiệu, phạm vi, mức mật) | Thấp — khoảng 3 ngày cho cả 32 loại | **Làm ở bản 1** |
| **B. Form nhập trên web** | Mỗi loại có một bộ ô nhập trên màn hình; điền xong hệ thống tự sinh ra văn bản đúng thể thức | Cao — mỗi loại là một màn hình riêng. 32 loại là 32 lần thiết kế và 32 lần đi hỏi nghiệp vụ | Chỉ làm cho **3–5 loại dùng nhiều nhất**, ở đợt sau |

Bản 1 nên đi cách A cộng với một bộ trường chung bắt buộc cho mọi loại. Cách B đúng hơn về lâu dài nhưng nếu làm ngay từ đầu thì dự án sẽ đứng ở khâu thiết kế form suốt vài tháng.

**AI chuyển ảnh thành văn bản** — làm được, và đúng như đã nêu: **người phải sửa lại trên form**. Nói rõ kỳ vọng để sau này không ai thất vọng:

- Ảnh chụp điện thoại hơi nghiêng, văn bản tiếng Việt có dấu: nhận đúng khoảng 85–95% ký tự. Bảng biểu và con dấu đè lên chữ thì thấp hơn nhiều.
- Nghĩa là AI để **đỡ phải gõ lại**, không phải để tin. Người soạn vẫn phải đọc đối chiếu với ảnh gốc.
- Ràng buộc cứng: **AI chỉ được ghi vào bản nháp**, không có đường nào cho AI duyệt, ban hành hay đổi trạng thái văn bản. Kết quả AI luôn kèm ảnh gốc để đối chiếu.
- Nên có nút "so sánh ảnh gốc và văn bản" đặt cạnh nhau, không bắt người dùng mở hai cửa sổ.

### 4.2 · Số văn bản

Phần này thiết kế cũ đã làm xong và làm đúng. Ba lớp chống trùng:

1. Khóa dòng bộ đếm khi cấp số (`SELECT ... FOR UPDATE`), nằm **trong cùng giao dịch** với việc ghi bản ghi.
2. Ràng buộc duy nhất ở tầng cơ sở dữ liệu.
3. Không bao giờ dùng `MAX(số)+1`, không dùng bộ đếm Redis cho số hiệu pháp lý — hai cách này trùng số khi hai người bấm cùng lúc, và số hiệu trùng nghĩa là hồ sơ pháp lý vô hiệu.

Hai điều bổ sung cần biết:

- **Văn bản bị hủy vẫn giữ số**, chỉ đổi trạng thái thành đã hủy. Trả số về để dùng lại là sai nguyên tắc sổ sách.
- Có **hai kiểu định danh, không thay thế nhau**: mã tài liệu bất biến (`DEGO-QC-012`, cho nhóm quy chế/quy trình sống lâu, không đổi kể cả khi lên bản 5) và số hiệu theo sổ (`08/2026/TB-NS-DEGO`, cho nhóm sự vụ, đếm lại từ 1 mỗi năm). Một văn bản có thể mang cả hai.

**AI kiểm tra trùng nội dung** — đồng ý để phase sau. Việc này cần thêm hạ tầng tìm kiếm (OpenSearch hoặc tương đương) vì tìm toàn văn tiếng Việt bằng MySQL không tốt. Trước khi có AI, vẫn nên có bước rẻ tiền: khi tạo văn bản mới, hệ thống hiện ngay danh sách văn bản cùng loại cùng phòng ban đang hiệu lực để người soạn tự nhìn.

### 4.3 · Cấu hình cha–con theo loại văn bản

Đây là phần được yêu cầu đề xuất. Viết riêng ở **mục 5** bên dưới.

### 4.4 · Phạm vi ban hành và clone

Đã nêu ở mục 2.2. Bổ sung ba chỗ dễ vỡ:

- **Phòng ban dùng chung cho 13 pháp nhân.** Nếu chọn phạm vi "Phòng Nhân sự" mà không kèm pháp nhân thì văn bản lan sang phòng Nhân sự của cả 13 công ty. Phải chặn ở tầng dữ liệu, không chặn bằng nhắc nhở.
- **Không có dòng phạm vi nào = không ai thuộc phạm vi.** Mặc định là không, không phải tất cả.
- **Loại trừ luôn thắng bao gồm.**

### 4.5 · Quyền truy cập

Đồng ý toàn bộ. Bốn lớp, xếp theo thứ tự kiểm tra:

| Lớp | Câu hỏi | Cơ chế |
|---|---|---|
| 1 | Vai trò này được làm gì | Quyền theo vai trò — đã có sẵn trong Thu mua |
| 2 | Người này đụng được dữ liệu của ai | Phạm vi theo (người × vai trò) — đã có sẵn |
| 3 | Người này xem được đến mức mật nào | **Mới** — mức mật cấp cho từng người, có hạn |
| 4 | Văn bản này có chia sẻ riêng cho ai không | **Mới** — chia sẻ đích danh trên từng văn bản |

Hai quy tắc vàng, viết vào mã nguồn chứ không viết vào quy trình:

- **Cấm luôn thắng cho phép.** Một dòng cấm ở bất kỳ lớp nào là chặn, dù các lớp khác đều cho.
- **Chia sẻ đích danh không bao giờ vượt được mức mật.** Chia sẻ một văn bản Tuyệt mật cho người chỉ có mức Nội bộ thì người đó vẫn không xem được. Nếu không có ràng buộc này thì lớp mức mật vô nghĩa.

**"Duyệt hoặc ban hành rồi thì không sửa được"** — đồng ý, và phải khóa ở **tầng dịch vụ**, không phải ẩn nút trên giao diện. Sửa văn bản đã ban hành = tạo phiên bản mới, kèm lý do sửa bắt buộc nhập. Phiên bản cũ không bao giờ bị ghi đè — đây là nền tảng của mọi cuộc thanh tra sau này.

### 4.6 · Lưu trữ trên R2 và link công khai

Câu hỏi đã nêu: *"lưu trên R2 nhưng có link công khai, có cách nào nhúng quyền không?"*

**Trả lời: có, và không khó.** Nhưng đây không phải việc phase sau.

Cách làm:

1. Kho R2 để **riêng tư hoàn toàn**, tắt đường dẫn công khai. Không lưu link công khai vào cơ sở dữ liệu nữa.
2. Khi người dùng bấm xem, máy chủ **kiểm quyền trước** (đủ 4 lớp ở mục 4.5), rồi mới sinh một **link tạm có chữ ký, sống 60–120 giây**, và ghi một dòng nhật ký "ai xem file nào lúc nào".
3. Hết 120 giây link tự chết. Người đã nghỉ việc không xin được link mới.

**Nói rõ giới hạn để không ai hiểu nhầm là đã chống rò rỉ triệt để:**

- Trong 120 giây đó link vẫn sao chép được. Chống được người lấy link cũ, không chống được người đang xem cố tình phát tán ngay lúc đó.
- Người xem vẫn chụp được màn hình. Không có phần mềm nào chặn được việc này.
- Muốn siết thêm thì: xem trên web dưới dạng ảnh/PDF chứ không cho tải tệp gốc, và **đóng dấu chìm động** in tên người xem cộng thời điểm lên từng trang. Ai chụp màn hình phát tán thì dấu chìm chỉ ra người đó. Đây là mức thực tế nhất, cũng là mức các hệ tài liệu nghiêm túc dừng lại.
- Tách riêng **quyền xem** và **quyền tải về** — cho xem trên trình duyệt mà không cho lưu về máy. Đây là điểm hệ HrOnline làm và đáng lấy.

**Vì sao không để phase sau:** hiện tại hệ đang lưu link công khai vĩnh viễn vào cơ sở dữ liệu. Nếu đợt 1 đưa văn bản vào rồi mới sửa ở đợt sau, thì tất cả file đã tải lên trong khoảng thời gian đó đã có link công khai nằm trong cơ sở dữ liệu — dọn về sau tốn hơn nhiều và không lấy lại được những link đã bị phát tán.

### 4.7 · Phê duyệt kiểu Lark Approver

Đây là phần **giá trị nhất** và cũng **rủi ro nhất**.

Giá trị: hệ Thu mua hiện có **5 luồng duyệt viết tay** nằm rải trong 5 mô-đun (yêu cầu mua hàng, khảo sát, yêu cầu khảo sát, đơn mua hàng, yêu cầu thanh toán). Mỗi luồng là một đoạn mã riêng, một bước duyệt, không có ủy quyền, không có nhắc hạn, không cấu hình được bằng giao diện. Muốn đổi người duyệt phải sửa mã nguồn và deploy. Làm một bộ máy duyệt chung là trả xong món nợ này.

Rủi ro: đây chính là chỗ dễ làm hỏng Thu mua nhất.

**Cách làm an toàn — bốn nguyên tắc:**

1. **Bộ máy mới chạy song song, không thay chỗ bộ máy cũ.** Mã duyệt hiện tại của Thu mua giữ nguyên, không đụng vào.
2. **Bật theo từng loại chứng từ bằng cờ.** Ví dụ bật cho yêu cầu thanh toán trước, chạy hai tuần, ổn thì bật tiếp cho đơn mua hàng.
3. **Có đường lui trong một lần bấm.** Tắt cờ là quay về đường cũ ngay, không cần deploy.
4. **Bộ kiểm thử hồi quy Thu mua phải xanh** mới cho gộp mã. Hiện có 27 tệp kiểm thử — trước khi bắt đầu phải bổ sung phần kiểm thử cho 5 luồng duyệt hiện tại, vì đó là lưới an toàn duy nhất.

Hai điểm cụ thể đã nêu, đều có trong Lark và đều nên lấy:

- **Trùng thao tác thì bỏ qua** — nếu người ở bước 3 chính là người vừa duyệt ở bước 2 thì tự động qua bước, không bắt bấm hai lần. Cần cấu hình được ba mức: bỏ qua khi trùng liền kề, bỏ qua khi trùng bất kỳ chỗ nào phía trước, không bỏ qua.
- **Người duyệt đã nghỉ việc thì chỉ định người khác** — đây là "phương án 2" đã nêu. Trong Lark còn có phương án 1 là tự động duyệt qua và phương án 3 là chuyển cho quản trị viên. Đề nghị: **mặc định là phương án 2**, và **cấm dùng phương án 1** cho văn bản, vì tự động duyệt qua nghĩa là một bước kiểm soát biến mất mà không ai biết.

### 4.8 · Thông báo tách theo app

Đồng ý, và cách rẻ nhất là **thêm một cột `app` vào bảng thông báo đang có** (mặc định là `thumua`), chuông chỉ hiện thông báo của app đang mở. Sau này muốn bỏ thì xóa cột và bỏ điều kiện lọc, một buổi là xong.

**Đừng tạo bảng thông báo thứ hai.** Hai bảng nghĩa là hai đường gửi, hai chỗ đánh dấu đã đọc, hai lần sửa khi làm web push, và cuối cùng vẫn phải gộp lại.

---

## 5. Đề xuất tính năng cha–con theo loại văn bản

Yêu cầu: *"mỗi loại văn bản sẽ được cấu hình là loại đó có cha không, hoặc văn bản hướng dẫn thì phải có hướng dẫn cái gì"*.

Đề xuất tách thành **hai thứ khác nhau** mà người ta hay lẫn:

| | Là gì | Nằm ở đâu | Ai đặt |
|---|---|---|---|
| **Quy tắc** | Loại "Hướng dẫn công việc" **bắt buộc** phải khai nó hướng dẫn cho Quy trình nào | Cấu hình theo **loại văn bản** | Pháp chế / quản trị, đặt một lần |
| **Quan hệ** | Văn bản `HDCV-005` hướng dẫn cho `QT-012` | Dữ liệu trên **từng văn bản** | Người soạn, mỗi lần soạn |

### 5.1 · Bảng quy tắc — cấu hình một lần

Mỗi dòng là một câu: *"loại X có quan hệ Y tới loại Z, bắt buộc hay không, được mấy cái"*.

| Loại nguồn | Quan hệ | Loại đích được phép | Bắt buộc | Số lượng | Nghĩa |
|---|---|---|---|---|---|
| Hướng dẫn công việc | hướng dẫn | Quy trình | Có | Đúng 1 | Hướng dẫn thì phải hướng dẫn cho một quy trình cụ thể |
| Biểu mẫu | thuộc về | Quy trình, Quy chế | Có | 1 trở lên | Biểu mẫu không đứng một mình |
| Quy chế | kèm theo | Quyết định | Có | Đúng 1 | Quy chế ban hành kèm quyết định ban hành |
| Quy định | căn cứ theo | Chính sách | Không | 0 trở lên | Có thì tốt, không có cũng được |
| Quyết định | thay thế | Quyết định | Không | 0 trở lên | Quyết định mới thay quyết định cũ |
| Bất kỳ | tham chiếu | Bất kỳ | Không | 0 trở lên | Liên kết mềm |

Bảy loại quan hệ dùng chung: *thay thế · sửa đổi · bổ sung · hướng dẫn · kèm theo · thuộc về · căn cứ theo · tham chiếu · bãi bỏ*.

### 5.2 · Hệ thống làm gì với bảng quy tắc đó

| Lúc nào | Hành vi |
|---|---|
| **Khi chọn loại văn bản lúc soạn** | Form **tự hiện ô** "Hướng dẫn cho văn bản nào", và danh sách chọn **chỉ lọc đúng loại đích cho phép**, chỉ hiện văn bản đang hiệu lực. Người soạn không phải nhớ quy tắc |
| **Khi bấm gửi duyệt** | Quan hệ bắt buộc mà chưa khai thì **chặn, không cho gửi**, kèm câu báo rõ ràng. Chặn ở tầng dịch vụ, không chặn bằng giao diện |
| **Khi lưu quan hệ** | **Cấm vòng lặp**: A hướng dẫn B mà B lại hướng dẫn A thì chặn. Kiểm tra chu trình ngay lúc lưu, không để lọt vào dữ liệu |
| **Khi xem một văn bản** | Hiện **cây tài liệu**: mở một Quy trình thì thấy ngay các Hướng dẫn công việc và Biểu mẫu thuộc nó, mỗi cái kèm trạng thái và phiên bản |
| **Khi sửa văn bản cha** | Liệt kê các văn bản con và hỏi xử lý. **Hệ thống chỉ cảnh báo và liệt kê, không tự sửa gì cả.** Người sửa quyết định, và quyết định đó ghi vào nhật ký |
| **Khi bãi bỏ văn bản cha** | Theo cấu hình của quan hệ, chọn một trong ba: không làm gì · đánh dấu con "cần rà lại" · con hết hiệu lực theo cha. Mặc định nên là "cần rà lại" |

### 5.3 · Hai tùy chọn thêm, nên có nhưng không bắt buộc ở bản 1

- **Thừa kế số hiệu.** Hướng dẫn công việc của `DEGO-QC-012` đánh số `DEGO-QC-012-HD01`. Nhìn số là biết thuộc ai. Bật/tắt theo từng dòng quy tắc.
- **Thừa kế mức mật.** Con không được thấp hơn cha. Biểu mẫu của một quy chế Mật thì mặc định cũng Mật, muốn hạ phải có người đủ thẩm quyền hạ tường minh.

### 5.4 · Vì sao tách thành quy tắc riêng thay vì cho một cột "loại cha" trên bảng loại văn bản

Một cột `loại cha` chỉ diễn tả được một quan hệ, một chiều, không nói được bắt buộc hay không, không nói được số lượng. Thực tế cần nhiều hơn: Biểu mẫu vừa thuộc Quy trình vừa thuộc Quy chế; Quyết định vừa thay thế Quyết định cũ vừa kèm theo Quy chế mới. Bảng quy tắc là một bảng nhỏ, khoảng 15–25 dòng, khai một lần, đổi được bằng giao diện mà không sửa mã nguồn.

---

## 6. Về cam kết "khi xong thì không ảnh hưởng gì tới Thu mua"

Cam kết này giữ được, với sáu ràng buộc cụ thể:

| # | Ràng buộc |
|---|---|
| 1 | **Chỉ thêm bảng mới, chỉ thêm cột mới. Không đổi, không xóa bất kỳ cột nào đang có** |
| 2 | **Chỉ thêm đối tượng phân quyền mới. Không đổi tên, không đổi ý nghĩa đối tượng cũ.** Thêm giá trị phạm vi mới thì giá trị cũ giữ nguyên hành vi |
| 3 | Bộ máy duyệt mới **đứng cạnh** mã duyệt cũ, không thay chỗ. Bật/tắt theo từng loại chứng từ bằng cờ |
| 4 | **Trước khi bắt đầu**, bổ sung kiểm thử tự động cho 5 luồng duyệt hiện tại của Thu mua. Đây là lưới an toàn duy nhất |
| 5 | Mỗi đợt gộp mã đều phải chạy đủ bộ kiểm thử hồi quy; đỏ là không gộp |
| 6 | Việc vá 3 lỗ hổng lõi **triển khai lên môi trường dev trước ít nhất một tuần**, có người dùng thật xác nhận, rồi mới lên prod |

Ràng buộc số 4 là chỗ hiện đang thiếu và cần làm ngay từ tuần đầu. Không có nó thì mọi cam kết còn lại chỉ là lời hứa.

---

## 7. Sáu việc nặng chưa thấy nhắc tới

Nêu ra để cân nhắc, không phải để làm hết.

| # | Việc | Vì sao đáng nhắc |
|---|---|---|
| 1 | **Nhập kho văn bản giấy cũ** | Thường là việc tốn công nhất của mọi dự án văn thư, và **không phải việc của người viết mã**. Cần biết: bao nhiêu văn bản, ai gõ, gõ đến đâu thì dừng |
| 2 | **Ký ban hành** | Ký điện tử nội bộ (bản ghi ký + mã băm + dấu thời gian) chỉ đủ giá trị trong nội bộ. Muốn giá trị pháp lý với bên thứ ba phải mua chữ ký số của nhà cung cấp và tách một dịch vụ riêng vì cần thiết bị USB |
| 3 | **Xác nhận đã đọc** | Đây là thứ khác biệt lớn nhất so với một thư mục chia sẻ: ban hành xong biết được ai đã đọc, ai chưa, ai quá hạn. Nếu cần thì phải thiết kế từ đầu |
| 4 | **Rà soát định kỳ và hết hiệu lực** | Quy chế đặt chu kỳ rà 12 tháng, tới hạn hệ thống tự nhắc người phụ trách. Không có cái này thì sau 3 năm không ai biết văn bản nào còn dùng được |
| 5 | **Sổ văn bản đến** | Yêu cầu mới chỉ nói về văn bản do mình soạn ra. Công văn, chứng nhận, phiếu an toàn hóa chất từ bên ngoài gửi vào là một luồng khác hẳn: vào sổ, phân người xử lý, có hạn xử lý |
| 6 | **Xem trên web không cho tải** | Cần thêm bộ chuyển đổi tệp Word sang PDF và bộ đóng dấu chìm. Là hạ tầng thêm, không phải một tính năng nhỏ |

---

## 8. Câu hỏi cần trả lời

Đánh dấu `[CHẶN]` nghĩa là chưa có câu trả lời thì không viết mã được phần liên quan.

### Nhóm A · Phạm vi bản đầu tiên

| # | Câu hỏi | Chặn việc gì |
|---|---|---|
| A1 | Bản đầu tiên cần chạy được đến đâu: chỉ **yêu cầu → soạn → duyệt → ban hành → tra cứu**, hay phải có cả sổ văn bản đến? | `[CHẶN]` toàn bộ lộ trình |
| A2 | Ký ban hành: **ký điện tử nội bộ đủ chưa**, hay phải ký số có giá trị pháp lý với bên thứ ba ngay từ bản đầu? | `[CHẶN]` đợt ban hành. Nếu cần ký số thì phải chọn nhà cung cấp và mua thiết bị, tự nó mất 4–6 tuần |
| A3 | Có cần **xác nhận đã đọc** không? Ban hành xong có phải biết ai đã đọc, ai chưa không? | Ảnh hưởng thiết kế phần ban hành |
| A4 | **Văn bản giấy cũ** có nhập vào hệ thống không? Khoảng bao nhiêu? Ai gõ? | Ảnh hưởng nhân lực, không ảnh hưởng mã nguồn |

### Nhóm B · Nghiệp vụ

| # | Câu hỏi | Chặn việc gì |
|---|---|---|
| B1 | "Form chuẩn" là **mẫu tệp Word tải về điền** hay **form nhập trên web**? Nếu là form nhập thì **loại nào làm trước** (đề nghị chọn 3–5 loại) | `[CHẶN]` đợt soạn thảo |
| B2 | **Yêu cầu văn bản do ai duyệt**: một người cố định, theo loại văn bản, hay theo phòng ban của người xin? Có cần nhiều bước không? | `[CHẶN]` bộ máy duyệt |
| B3 | Dùng **mấy mức mật**? Đề nghị 4 mức: Công khai · Nội bộ · Mật · Tuyệt mật. **Ai có quyền cấp** mức 3 và 4 cho người khác? | `[CHẶN]` phần quyền truy cập |
| B4 | Sau khi ban hành muốn sửa: **bắt buộc tạo phiên bản mới**, hay cho phép "đính chính" nhỏ tại chỗ? | Đề nghị: luôn tạo phiên bản mới. Cần xác nhận |
| B5 | Bản **clone xuống công ty con** có phải chạy lại toàn bộ luồng duyệt của công ty con không? Nếu công ty con không đụng tới trong 30 ngày thì hệ thống làm gì? | `[CHẶN]` tính năng clone |
| B6 | **Mã 13 pháp nhân, 32 mã loại văn bản, 18 mã phòng ban** hiện đang là đề xuất, đã ai duyệt chưa? | `[CHẶN]` cứng phần cấp số. Cấp số rồi thì **không đổi mã được nữa** |
| B7 | Hộ kinh doanh DR XANH và Nhà phân phối DR XANH **có ban hành văn bản riêng** không, hay chỉ nhận? | Ảnh hưởng số sổ cần mở |
| B8 | Ba pháp nhân chưa có người đại diện (DEGO HOLDING, SAM, AGRIPLANT) — ai ký ban hành? | `[CHẶN]` luồng ký của ba pháp nhân đó |

### Nhóm C · Kỹ thuật và vận hành

| # | Câu hỏi | Chặn việc gì |
|---|---|---|
| C1 | Vá 3 lỗ hổng lõi phải triển khai lên hệ đang chạy thật. **Được dừng hệ thống vào khung giờ nào?** Hay phải làm không dừng? | `[CHẶN]` đợt 0 |
| C2 | Duyệt của Thu mua **có chuyển sang bộ máy mới không**, hay giữ mã cũ vĩnh viễn? | Đề nghị: chuyển, nhưng sau khi văn thư chạy ổn ít nhất một tháng |
| C3 | **Ai là chủ sở hữu nghiệp vụ** phía Pháp chế/Văn thư — người chốt danh mục, chốt luồng duyệt, nghiệm thu? | `[CHẶN]` mọi thứ. Không có người này thì mỗi câu hỏi ở trên đều treo |
| C4 | Có cần **tìm toàn văn tiếng Việt không dấu** (gõ "quy che chi tieu" ra "Quy chế Chi tiêu") không? | Nếu có thì phải thêm một thành phần hạ tầng tìm kiếm, cộng 2–3 tuần |
| C5 | Bao nhiêu người sẽ dùng phần văn thư, và trong đó bao nhiêu người **chỉ đọc**? | Ảnh hưởng thiết kế màn hình chính và cách gán quyền mặc định |

---

## 9. Kết luận

| | |
|---|---|
| Cách làm | Xây trên mã nguồn Thu mua — **đồng ý** |
| Điều kiện bắt buộc | Vá 3 lỗ hổng lõi cộng 2 chỗ hở, **trước khi** đưa văn bản mật vào |
| Chỗ phản đối | Để việc "link R2 công khai" sang phase sau. Phải làm ngay ở đợt đầu |
| Chỗ cần làm rõ nhất | "Form chuẩn" hiểu theo nghĩa nào (B1) — chênh nhau vài tháng công việc |
| Chỗ rủi ro nhất | Bộ máy duyệt chung đụng vào 5 luồng duyệt đang chạy của Thu mua |
| Việc phải làm ngay tuần đầu, không cần chờ trả lời câu hỏi nào | Viết kiểm thử tự động cho 5 luồng duyệt hiện tại của Thu mua |

Tiếp theo: [`01` Danh sách tính năng](./01-danh-sach-tinh-nang.md)
