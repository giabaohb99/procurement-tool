# 05 — Màn Vai trò & quyền, hộp thoại Phạm vi, cảnh báo tự loại trừ

> **bao-CR-428** (màn Vai trò & quyền đọc được) · **bao-CR-427** (hai tầng phạm vi
> gộp làm một khối) · **bao-CR-430** (cảnh báo vàng khi loại trừ phòng của chính chủ
> tài khoản). Cả ba chỉ có ở giao diện mới `frontend-v2`, đã lên dev chiều 19/09/2026
> (`8d2c52a2`, doc `f7698f10`). Không có migration, không đổi luật lọc ở máy chủ.

## Hai màn liên quan

| Màn | Đường dẫn trên deverp | Dùng cho |
|---|---|---|
| Phân quyền, tab **Vai trò** | `/system/permissions` | CR-428 |
| Phân quyền, tab **Người dùng** → bấm một tài khoản | `/system/permissions/users/<id>` | CR-427 · CR-430 (nút **Phạm vi** cạnh vai trò đã lưu) |

## Tài khoản cần chuẩn bị

Chọn theo VAI TRÒ, không chép tên:

| Ký hiệu trong ca | Vai trò | Cần có gì |
|---|---|---|
| **QT** | quản trị (`admin`) | đủ `role.read/write`, `employee.read`, `department.read`, `company.read` |
| **TK-NM** | một tài khoản của **nhà máy** (bậc `dept_proc`, ví dụ `pur_dept_manager`) | ĐÃ gắn hồ sơ nhân sự, hồ sơ có công ty + phòng ban |
| **TK-TRỐNG** | một tài khoản **chưa gắn hồ sơ nhân sự** (badge *Thiếu hồ sơ* ở tab Người dùng) | dùng cho ca hồ sơ trống |
| **TK-KHAI** | một tài khoản có `role.write` nhưng **KHÔNG** có `employee.read` | dùng cho ca thiếu quyền; nếu dev chưa có thì tạo vai trò tạm rồi xóa sau |

Trước khi bắt đầu: đăng nhập QT, tab Người dùng, ghi lại **tên phòng chính** của TK-NM
(mở hồ sơ nhân sự nếu cần) và **một phòng kiêm nhiệm** nếu có. Mấy ca CR-430 cần đúng
hai tên đó.

Thêm một điều phải nhớ khi chấm: tài khoản **đang đăng nhập giữ map quyền cũ** tới khi
đăng xuất. Đổi quyền / đổi phạm vi xong mà TK-NM vẫn thấy như cũ thì đăng xuất đăng nhập
lại rồi mới chấm.

---

## A. CR-428 — màn Vai trò & quyền

**TC-428-01 — Cột trái không cắt tên bằng "..."**
1. QT vào `/system/permissions`, tab Vai trò.
2. Nhìn dòng có tên dài nhất (ví dụ *Nhân sự — Hồ sơ nhân viên*, *Quản lý thu mua của phòng*).
- Mong đợi: tên **xuống dòng**, đọc trọn, không có dấu "..." ở cuối; cột trái rộng hơn bản
  cũ rõ rệt (320px).
- Kết quả:

**TC-428-02 — Mỗi dòng vai trò in đủ bốn thứ**
1. Cùng màn, nhìn bất kỳ dòng nào chưa chọn.
- Mong đợi theo thứ tự từ trên xuống: **tên** · **mã** (chữ mono nhỏ) · **một câu mô tả**
  · dãy **chip phân hệ**; góc phải trên có biểu tượng người + **số tài khoản đang giữ**.
- Vai trò chưa tick ô nào thì thay chip bằng chữ *Chưa cấp quyền*.
- Kết quả:

**TC-428-03 — Số người giữ đúng**
1. Chọn một vai trò có ít người (1-3), ghi số trên dòng.
2. Sang tab Người dùng, lọc / đếm tài khoản đang mang vai trò đó.
- Mong đợi: hai con số khớp. Rê chuột lên số thấy câu *"n tài khoản đang giữ vai trò này"*.
- Kết quả:

**TC-428-04 — Dòng xen kẽ sọc nền**
1. Nhìn cột trái, mọi dòng chưa chọn.
- Mong đợi: dòng lẻ / chẵn khác nền, đủ thấy bằng mắt (cùng tông sọc với bảng ma trận bên
  phải). Gõ tìm để danh sách còn 3-4 dòng thì sọc **vẫn đều** theo thứ tự đang hiện.
- Kết quả:

**TC-428-05 — Chip phân hệ nói đúng việc**
1. Đọc chip của ba vai trò: một của Thu mua, một của Đặt xe, một của Nhân sự.
- Mong đợi: chip đầu tiên là phân hệ chính của vai trò đó (nhiều ô tick nhất). Vai trò
  Đặt xe **không** bị gắn chip *Nhân sự* / *Dự án* chỉ vì ai cũng có mấy ô nền đó.
  Quá 3 phân hệ thì có chip *+n*, rê chuột lên đọc được phần dư.
- Kết quả:

**TC-428-06 — Tìm theo câu mô tả**
1. Ô tìm vai trò, gõ một chữ CHỈ có trong mô tả, không có trong tên (ví dụ `công nợ`,
   `điều phối`, `con dấu`).
- Mong đợi: vai trò có mô tả chứa chữ đó hiện ra. Đang gõ tìm thì tay cầm kéo biến mất và
  có dòng *"Xóa từ khóa tìm để kéo đổi thứ tự."*
- Kết quả:

**TC-428-07 — Mô tả có sẵn cho vai trò chuẩn, không đè câu đã sửa**
1. Đọc mô tả của 5 vai trò chuẩn bất kỳ (`admin`, `pur_staff`, `dept_head`,
   `booking_driver`, `hr_leave`).
- Mong đợi: mỗi vai trò đã có một câu mô tả tổng quát, **không gắn tên phân hệ vào nhãn
  bậc**, không câu nào trống.
2. Sửa mô tả của một vai trò (ca TC-428-08), rồi nhờ người trực dev **restart api** (seed
   chạy lại lúc khởi động) hoặc chờ lần deploy dev kế tiếp.
- Mong đợi: câu vừa sửa **còn nguyên**, seed không đè lại.
- Kết quả:

**TC-428-08 — Sửa mô tả ngay tại tiêu đề khung bên phải**
1. Chọn một vai trò. Ở đầu khung ma trận, dưới tên + mã, bấm vào câu mô tả (có bút chì).
2. Gõ câu mới, nhấn **Enter**.
- Mong đợi: lưu, câu mới hiện ở cả tiêu đề lẫn dòng cột trái; tải lại trang vẫn còn.
3. Bấm sửa lần nữa, gõ gì đó, nhấn **Esc**.
- Mong đợi: bỏ, giữ câu cũ. Rời ô bằng cách bấm ra ngoài **không** lưu.
4. Xóa hết chữ rồi Enter.
- Mong đợi: lưu được câu rỗng; chỗ đó đổi thành chữ nghiêng *"Chưa có mô tả — bấm để viết
  một câu vai trò này lo việc gì."*; dòng cột trái không còn dòng mô tả.
- Kết quả:

**TC-428-09 — Sửa tên và sửa mô tả là hai việc riêng**
1. Bấm sửa tên (bút chì cạnh tên), đang gõ dở thì nhìn phần mô tả bên dưới.
- Mong đợi: mô tả vẫn đọc bình thường, mã vai trò vẫn nằm nguyên chỗ; nhấn Esc thoát
  sửa tên thì mô tả không đổi.
- Kết quả:

**TC-428-10 — Tạo vai trò mới có ô mô tả**
1. Bấm **Thêm**, điền mã `tc428_tam`, tên `TC428 tạm`, mô tả `Vai trò tạm để kiểm thử`.
2. Bấm **Tạo**.
- Mong đợi: vai trò mới được chọn ngay, dòng cột trái có đủ mô tả và chữ *Chưa cấp quyền*;
  ma trận bên phải **mở hết mọi nhóm** (vai trò chưa tick gì thì không gập).
3. Xóa vai trò tạm sau khi xong (hoặc để lại cho TC-428-12).
- Kết quả:

**TC-428-11 — Ma trận chỉ mở nhóm có tick**
1. Chọn `booking_driver` (hoặc vai trò nào ít quyền).
- Mong đợi: nhóm có ô tick **mở sẵn**, nhóm trống **gập lại**; không phải cuộn qua hai
  chục nhóm trắng.
2. Chọn tiếp `admin`.
- Mong đợi: tập gập tính lại theo vai trò mới (admin gần như mở hết).
3. Quay lại `booking_driver`, mở tay một nhóm đang gập, tick một ô, Lưu.
- Mong đợi: lưu bình thường; tick / bỏ tick, chọn cả dòng, chọn cả cột vẫn chạy như cũ.
- Kết quả:

**TC-428-12 — Nhóm mới không rơi vào «Khác»**
1. Chọn vai trò tạm ở TC-428-10 (mở hết nhóm), đọc tên các nhóm trong ma trận.
- Mong đợi: có nhóm riêng cho **Nghỉ phép**, **Hồ sơ**, **Đặt phòng họp**, **Điểm cà phê**,
  **Diễn đàn** (bảng), **Đồng bộ** (sổ đồng bộ); nhóm **Khác** (nếu còn) không chứa mấy
  đối tượng đó.
- Kết quả:

**TC-428-13 — Nhãn bậc mới ở cột Phạm vi**
1. Chọn `pur_staff`, nhìn cột Phạm vi của dòng *Yêu cầu mua hàng*; rồi `pur_dept_manager`.
- Mong đợi: hai bậc đọc là **«Được giao + đã duyệt»** và **«Được giao + đã duyệt trong
  phòng»**. Không còn chữ *Thu mua* trong nhãn bậc. Mở ô chọn bậc thấy đủ 7 bậc theo thứ tự
  hẹp → rộng.
- Kết quả:

**TC-428-14 — Rê chuột lên huy hiệu vai trò ở tab Người dùng**
1. Tab Người dùng, rê chuột lên một huy hiệu vai trò trong cột Vai trò.
- Mong đợi: tooltip là **câu mô tả** của vai trò đó. Vai trò vừa xóa mô tả (TC-428-08 bước 4)
  thì **không có tooltip**, không in lại tên.
- Kết quả:

**TC-428-15 — Kéo đổi thứ tự vẫn chạy (hồi quy)**
1. Xóa ô tìm, kéo một vai trò lên hai dòng, tải lại trang.
- Mong đợi: thứ tự mới còn; sọc xen kẽ vẫn đều sau khi kéo.
- Kết quả:

---

## B. CR-427 — hộp thoại Phạm vi: một khối "tài khoản này thấy gì"

**TC-427-01 — Khối tóm tắt in tên công ty / phòng thật**
1. QT vào tab Người dùng, mở TK-NM, bấm **Phạm vi** cạnh vai trò `dept_proc` đã lưu.
- Mong đợi: hộp mở với tiêu đề *Phạm vi — <tên vai trò>*; khối đầu tiên có biểu tượng con
  mắt, tiêu đề *"Tài khoản này thấy gì với vai trò «…»"*, bên dưới mỗi bậc một dòng dạng
  *YCMH, ĐMH, … — chứng từ ĐÃ DUYỆT của phòng <TÊN PHÒNG THẬT>, kể cả phiếu phòng khác
  nhờ phòng này mua giúp…*. Tên phòng phải đúng phòng trong hồ sơ TK-NM, không phải chữ
  "phòng ban người này".
- Không còn hai khối *Tầng 1 / Tầng 2* nằm cạnh nhau.
- Kết quả:

**TC-427-02 — Nhóm bậc «Tất cả» gom nhiều mục thì cắt còn 4 + "và n mục khác"**
1. Mở Phạm vi của một tài khoản mang `pur_manager` hoặc `admin`.
- Mong đợi: dòng bậc «Tất cả» chỉ liệt kê 4 nhãn rồi *"và n mục khác"*; rê chuột lên đọc
  được danh sách đầy đủ.
- Kết quả:

**TC-427-03 — Liên kết sang ma trận mở đúng vai trò**
1. Trong khối tóm tắt, bấm *"Sửa bậc ở màn Ma trận quyền"*.
- Mong đợi: sang `/system/permissions?role=<id>`, vai trò đó **đã được chọn sẵn**, ma trận
  gập theo đúng vai trò đó (TC-428-11).
- Kết quả:

**TC-427-04 — Tài khoản chưa gắn hồ sơ: cảnh báo đỏ ngay trong khối**
1. Mở TK-TRỐNG, gán tạm một vai trò bậc `company` hoặc `dept` (ví dụ `dept_head`), lưu,
   rồi bấm Phạm vi.
- Mong đợi: dưới dòng bậc có câu đỏ *"Tài khoản chưa gắn hồ sơ nhân sự nên không biết công
  ty / phòng ban của người này — bậc trên sẽ chặn sạch…"*. Cảnh báo hiện **không cần** mở
  mục Ngoại lệ.
2. Gỡ vai trò tạm sau khi xong.
- Kết quả:

**TC-427-05 — Hồ sơ có nhưng thiếu công ty / thiếu phòng**
1. Chọn (hoặc tạo tạm) một nhân sự **chưa gắn phòng ban**, gắn tài khoản, gán `dept_head`.
2. Mở Phạm vi.
- Mong đợi: câu đỏ *"Hồ sơ nhân sự của tài khoản chưa gắn phòng ban — bậc trên sẽ chặn
  sạch… Vào Nhân sự gắn phòng ban cho người này, đừng khai bù ở dưới."* Tương tự với
  thiếu công ty nếu kiểm được.
- Kết quả:

**TC-427-06 — Vai trò chưa tick quyền XEM nào**
1. Gán vai trò tạm `tc428_tam` (chưa tick gì) cho một tài khoản, lưu, bấm Phạm vi.
- Mong đợi: khối tóm tắt in câu đỏ *"Vai trò này chưa được tick quyền XEM ở đối tượng nào —
  gán vai trò xong tài khoản vẫn không thấy gì…"*.
- Kết quả:

**TC-427-07 — Năm ô tick nằm trong mục «Ngoại lệ» gập, mặc định đóng**
1. Mở Phạm vi của TK-NM (chưa khai ngoại lệ gì).
- Mong đợi: dưới khối tóm tắt chỉ có một nút *Ngoại lệ* (không số), mũi tên xuống; **không
  thấy** ô tick nào cho tới khi bấm.
2. Bấm mở.
- Mong đợi: có câu giải thích *"Chỉ dùng khi người này cần khác mặc định ở trên…"* và năm ô:
  **Chỉ trong công ty** · **Xem THÊM phòng ban** · **Chỉ xem chứng từ do nhân sự tạo** ·
  **Loại trừ phòng ban** (đỏ) · **Loại trừ nhân sự** (đỏ). Tên cũ *"Công ty được xem"* /
  *"Phòng ban được xem"* không còn.
- Kết quả:

**TC-427-08 — Đếm ngoại lệ trên nút và tóm tắt dù đã gập**
1. Mở Ngoại lệ, tick 1 công ty và 2 phòng ở *Xem THÊM phòng ban*, gập lại.
- Mong đợi: nút đọc *"Ngoại lệ (3)"* — đếm từng mục, tick thêm phòng thứ ba thì thành (4).
- Khối tóm tắt phía trên có phần *"Ngoại lệ đang khai cho riêng tài khoản này:"* với hai
  dòng: *"Chỉ trong công ty <MÃ CÔNG TY>."* và *"Xem THÊM chứng từ của phòng A, B."*
2. Bấm **Hủy**, mở lại.
- Mong đợi: về trạng thái đã lưu (chưa có gì), số trên nút biến mất.
- Kết quả:

**TC-427-09 — Câu tóm tắt loại trừ nói đúng chiều**
1. Mở Ngoại lệ, tick một phòng KHÁC phòng của TK-NM ở *Loại trừ phòng ban*; tick một nhân
   sự ở *Loại trừ nhân sự*.
- Mong đợi: hai dòng *"Bỏ chứng từ của phòng X (trừ phiếu phòng đó nhờ phòng mình mua
  giúp)."* và *"Bỏ chứng từ do <tên nhân sự> lập."*. Không có cảnh báo vàng (phòng X không
  phải phòng của TK-NM).
- Kết quả:

**TC-427-10 — «Xem THÊM phòng ban» mờ đi khi vai trò đã ở bậc Tất cả**
1. Mở Phạm vi của tài khoản mang vai trò mà **mọi** dòng đọc đều bậc Tất cả (`admin`
   hoặc `pur_admin`).
- Mong đợi: ô *Xem THÊM phòng ban* mờ (60%) với câu *"Vai trò đã ở bậc «Tất cả» nên cộng
  thêm phòng ban không đổi được gì."*; chip **vẫn bấm được** (để gỡ giá trị cũ).
2. Mở Phạm vi của TK-NM.
- Mong đợi: ô này **không** mờ, câu hint là *"CỘNG THÊM, không thu hẹp…"*.
- Kết quả:

**TC-427-11 — Cùng phòng ở cả hai ô: câu đỏ, nằm ngoài mục gập**
1. Tick phòng Y ở *Xem THÊM phòng ban* và cũng tick Y ở *Loại trừ phòng ban*.
- Mong đợi: câu đỏ *"Phòng Y đang nằm ở cả ô xem thêm lẫn ô loại trừ. Loại trừ thắng…"*
  hiện **giữa khối tóm tắt và nút Ngoại lệ**; gập mục lại thì câu **vẫn còn**.
2. Bỏ tick một bên.
- Mong đợi: câu biến mất ngay, không cần Lưu.
- Kết quả:

**TC-427-12 — Bậc là chỉ đọc trong hộp thoại**
1. Trong khối tóm tắt, thử bấm vào chữ bậc / nhãn đối tượng.
- Mong đợi: không có ô chọn nào, không đổi được bậc từ đây; muốn đổi phải theo liên kết
  sang ma trận (TC-427-03).
- Kết quả:

**TC-427-13 — Thiếu `role.read`: khối vẫn hiện, nói rõ lý do**
1. Đăng nhập TK-KHAI (nếu dựng được một tài khoản có `user.write` mà không có `role.read`),
   mở Phạm vi của ai đó.
- Mong đợi: khối tóm tắt in *"Bạn không có quyền xem vai trò nên không đọc được phạm vi của
  vai trò này. Phần Ngoại lệ bên dưới vẫn khai được…"* — **không** phải toast lỗi, không
  khung trắng. Không có liên kết sang ma trận.
- Kết quả (ghi *Không dựng được tài khoản* nếu bỏ qua):

**TC-427-14 — Thiếu `employee.read`: không cảnh báo sai**
1. Đăng nhập TK-KHAI (có `role.read`, không `employee.read`), mở Phạm vi của TK-NM.
- Mong đợi: dòng bậc nói *"…của phòng ban người này"* (không tên thật) và dòng xám *"Bạn
  không có quyền xem nhân sự nên chưa thay được tên công ty / phòng ban thật vào câu
  trên."*; **không** có câu đỏ "chưa gắn hồ sơ". Mở DevTools tab Network: không có lời gọi
  `/api/employees/<id>` hay `/api/employees/<id>/departments`, không 403.
- Kết quả:

**TC-427-15 — Lưu ngoại lệ vẫn ghi đúng (hồi quy)**
1. Với TK-NM: tick 1 công ty + 1 phòng loại trừ (khác phòng mình), bấm **Lưu phạm vi**.
- Mong đợi: hộp đóng sau khi lưu xong (không đóng trước), mở lại thấy đúng hai mục, nút
  *Ngoại lệ (2)*.
2. Mở lại, bỏ hết, Lưu.
- Mong đợi: về rỗng.
- Kết quả:

---

## C. CR-430 — cảnh báo vàng khi tự loại trừ phòng mình

**TC-430-01 — Loại trừ đúng phòng chính của chủ tài khoản**
1. QT mở Phạm vi của TK-NM (vai trò `dept_proc`), mở Ngoại lệ, ở *Loại trừ phòng ban* tick
   **đúng tên phòng chính** đã ghi lúc chuẩn bị.
- Mong đợi: câu **vàng** (không đỏ) hiện ngay, ngoài mục gập: *"Phòng <tên> là phòng của
  chính người này. Loại trừ thắng mọi bậc phạm vi, nên với mọi vai trò có gắn phạm vi này,
  phiếu của phòng đó sẽ không còn thấy — chỉ còn phiếu phòng khác nhờ phòng này xử lý. Vẫn
  lưu được nếu đó là ý muốn."*
- Nút **Lưu phạm vi** vẫn bấm được (không bị khóa).
- Kết quả:

**TC-430-02 — Phòng kiêm nhiệm cũng được coi là phòng mình**
1. Nếu TK-NM có phòng kiêm nhiệm: tick phòng kiêm nhiệm đó ở Loại trừ.
- Mong đợi: cùng câu vàng, tên phòng kiêm nhiệm. Tick cả hai phòng thì câu liệt kê cả hai,
  cách nhau dấu phẩy.
- Kết quả (ghi *Không có kiêm nhiệm* nếu không kiểm được):

**TC-430-03 — Bỏ tick thì cảnh báo biến mất; phòng khác thì không cảnh báo**
1. Bỏ tick phòng mình.
- Mong đợi: câu vàng mất ngay.
2. Tick một phòng bất kỳ khác.
- Mong đợi: không có câu vàng; chỉ có dòng tóm tắt *"Bỏ chứng từ của phòng …"*.
- Kết quả:

**TC-430-04 — Gập mục Ngoại lệ lại, cảnh báo vẫn còn**
1. Tick phòng mình, bấm gập *Ngoại lệ*.
- Mong đợi: câu vàng **vẫn hiện** dưới khối tóm tắt, cùng chỗ với câu đỏ mâu thuẫn ở
  TC-427-11.
- Kết quả:

**TC-430-05 — Tài khoản chưa gắn hồ sơ: không cảnh báo**
1. Mở Phạm vi của TK-TRỐNG, tick bất kỳ phòng nào ở Loại trừ.
- Mong đợi: **không** có câu vàng (không biết phòng của ai để mà so). Câu đỏ "chưa gắn hồ
  sơ" ở khối tóm tắt vẫn hiện nếu bậc cần hồ sơ.
- Kết quả:

**TC-430-06 — Thiếu `employee.read`: không cảnh báo, không gọi thêm API**
1. Đăng nhập TK-KHAI, mở Phạm vi của TK-NM, tick đúng phòng chính của TK-NM ở Loại trừ.
- Mong đợi: **không** câu vàng; Network không có lời gọi `/departments` của nhân sự đó.
- Kết quả:

**TC-430-07 — Lưu tự loại trừ rồi kiểm hậu quả thật (ca chính, đi hết vòng)**
1. Bằng QT: ghi lại TK-NM đang thấy bao nhiêu YCMH ở `/procurement/purchase-requests`
   (đăng nhập TK-NM đếm trước, hoặc lọc theo phòng bằng QT).
2. QT mở Phạm vi của TK-NM, tick phòng chính ở Loại trừ, **Lưu phạm vi**.
- Mong đợi: lưu thành công, mở lại còn tick, câu vàng hiện lại khi mở.
3. Đăng xuất, đăng nhập **TK-NM**, vào Yêu cầu mua hàng.
- Mong đợi: phiếu **của phòng mình biến mất**; chỉ còn phiếu của phòng khác đã **chuyển
  cho phòng mình xử lý** (cột phòng xử lý = phòng mình, CR-414). Nếu không có phiếu nào
  được nhờ thì bảng rỗng.
4. Mở thẳng URL một phiếu của phòng mình (lấy id từ bước 1).
- Mong đợi: *Không tìm thấy*, không trang trắng.
5. QT vào gỡ tick, Lưu; TK-NM đăng nhập lại.
- Mong đợi: số phiếu về như bước 1.
- Kết quả (ghi: số phiếu trước · sau · sau khi gỡ):

**TC-430-08 — Bản ghi trên DB (chỉ khi cần soi)**
1. Sau bước 2 của TC-430-07, nhờ người trực dev đọc `tab_user_scope` của cặp (user, role).
- Mong đợi: một dòng loại **loại trừ phòng ban** trỏ **id** của phòng chính (bảng lưu id từ
  CR-086, tên chỉ dùng trên giao diện). Không thêm cột / bảng mới.
- Kết quả:

---

## D. Hồi quy nhanh (5 phút)

**TC-HQ-01** — Tab Người dùng: tick thêm / bỏ một vai trò, Lưu — vẫn chạy, `Phạm vi` chỉ
hiện cạnh vai trò ĐÃ LƯU.
- Kết quả:

**TC-HQ-02** — Màn ma trận: đổi bậc ở cột Phạm vi của một dòng rồi Lưu, mở lại còn.
- Kết quả:

**TC-HQ-03** — Giao diện cũ `devthumua` màn Phân quyền không đổi gì (ba CR chỉ ở v2).
Nhãn bậc ở v1 **có đổi** thành «Được giao + đã duyệt» vì nhãn do máy chủ cấp — đó là
chủ ý, không phải lỗi.
- Kết quả:

---

## Ca đã có máy chạy thay

Đừng kiểm tay mấy chỗ này, đã có bài kiểm tự động (chạy dưới máy, cây `procurement-tool`):

| Chỗ | Bài kiểm | Chạy bằng |
|---|---|---|
| Dịch bậc ra lời thường, thay tên thật, cảnh báo thiếu hồ sơ / công ty / phòng, đếm ngoại lệ, phòng mâu thuẫn, phòng của chính mình (so tên, bỏ tên rỗng) | `utils/scope-summary.test.ts` | `docker compose exec -T erp npx vitest run src/modules/system` |
| Chip phân hệ: loại ô nền ≥75% khi ≥4 vai trò, vai trò chỉ toàn ô nền thì đếm thô, xếp nhiều ô trước | `utils/role-module-summary.test.ts` | cùng lệnh |
| Tập nhóm gập: nhóm trống gập, chưa tick gì thì mở hết | `utils/permission-matrix-cells.test.ts` | cùng lệnh |
| Hộp thoại Phạm vi: khối tóm tắt, mục gập, câu vàng CR-430 hiện / không hiện theo quyền và theo hồ sơ, không gọi API khi thiếu quyền | `components/user-scope-dialog.test.tsx` | cùng lệnh |
| Sửa mô tả Enter lưu / Esc bỏ, hai ô sửa độc lập; cột trái tìm theo mô tả, sọc xen kẽ, ô mô tả khi tạo | `components/role-name-inline-edit.test.tsx` · `components/role-side-panel.test.tsx` | cùng lệnh |

Lần đo 19/09/2026 trước khi đẩy lên dev: vitest `src/modules/system` xanh hết; `typecheck`
+ `lint` 0 lỗi.

**Chỗ CHƯA có máy canh**, nên ca tay ở trên là chỗ duy nhất kiểm:

 · seed điền mô tả cho vai trò chuẩn và **không đè** câu đã sửa (TC-428-07) — chưa có bài
   pytest cho `ROLE_DESCRIPTIONS` / `fill_role_description`;
 · `GET /api/roles` trả `user_count` đúng (TC-428-03);
 · hậu quả thật sau khi lưu tự loại trừ (TC-430-07) — bài Vitest chỉ chứng minh câu vàng
   hiện, không chứng minh máy chủ lọc đúng sau khi lưu.

## Thứ tự nên chạy nếu chỉ có 15 phút

1. TC-428-01 · 02 · 08 · 11 · 13 (màn Vai trò).
2. TC-427-01 · 07 · 08 · 11 (hộp thoại).
3. TC-430-01 · 03 · 07 (cảnh báo + hậu quả thật).
