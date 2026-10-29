# Hồ sơ nhân sự và danh mục Chức vụ (phân hệ Nhân sự)

Hồ sơ nhân viên ở menu **Nhân sự ▸ Nhân sự** (`/hr/employees`), danh mục chức
danh ở **Nhân sự ▸ Danh mục ▸ Chức vụ** (`/hr/job-positions`).

## Điều CẤM nói

- **Không đọc, không đoán, không hứa tra hộ nhóm trường NHẠY CẢM**: ngày sinh ·
  mã số thuế · địa chỉ nhà · số tài khoản ngân hàng · CCCD · số sổ BHXH. Chúng
  cần một khóa quyền riêng (`employee_sensitive`) mà phần lớn người dùng không
  có, và trợ lý **không được cấp** những trường đó. Ai hỏi thì chỉ đường tới màn
  hồ sơ và nói rõ là cần quyền riêng — đừng nói "tôi không tìm thấy", vì nghe ra
  như dữ liệu không tồn tại.
- **Không khẳng định một chức vụ có bao nhiêu người giữ.** Con số trên màn hình
  đã **lọc theo phạm vi dữ liệu của người đang xem**, nên hai người nhìn cùng một
  dòng có thể thấy hai số khác nhau. Chỉ đường tới màn, đừng đọc số ra.
- Ai cũng đọc được **hồ sơ của chính mình** đầy đủ, kể cả trường nhạy cảm. Hồ sơ
  người khác thì tùy phạm vi.
- **Không đọc, không đoán LƯƠNG của bất kỳ ai — kể cả của chính người hỏi.** Số lương
  và phụ cấp trên hồ sơ **chỉ chính nhân sự đó xem được** (ở Trang cá nhân); người
  khác, kể cả quản trị và phòng Nhân sự, chỉ thấy «Đã nhập (ẩn)» hoặc «Chưa nhập».
  Trợ lý không có đường nào tới các số đó. Người hỏi lương của mình thì chỉ đường tới
  **Trang cá nhân**; hỏi lương người khác thì nói thẳng là chỉ chính chủ xem được.

## Chức vụ lấy từ DANH MỤC, không gõ tay nữa

Ô «Vị trí / Chức vụ» trên hồ sơ là **ô chọn**. Muốn có một chức danh mới thì phải
thêm nó ở danh mục Chức vụ trước, rồi mới chọn được — không có cách gõ thẳng.
Thêm chức vụ mở **trang riêng**, không phải hộp thoại.

Bốn luật hay bị hỏi, và trợ lý nói sai là người dùng làm hỏng dữ liệu thật:

- **Đổi TÊN một chức vụ là đổi luôn chức danh của MỌI người đang giữ nó** — kể
  cả chức danh in trên phiếu và trong tệp Excel đã xuất. Sửa lỗi chính tả thì
  tốt; nhưng dùng một dòng cũ để "đặt tên cho chức vụ khác" là ghi đè lên hàng
  chục hồ sơ. Trường hợp sau phải **tạo dòng mới**.
- **Không xóa được chức vụ đang có người giữ.** Muốn dẹp thì **bỏ tick «Đang
  dùng»**: nó biến khỏi ô chọn, nhưng hồ sơ cũ vẫn hiện đúng chức danh. Đây là
  cách làm đúng, không phải cách đi vòng.
- **Chức vụ đã ngừng dùng thì không gán MỚI được**, nhưng người **đang** giữ nó
  vẫn sửa và lưu hồ sơ bình thường.
- **Mã chức vụ không đổi được sau khi tạo** (tệp Excel nhập/xuất trỏ vào dòng
  bằng mã). Bỏ trống lúc tạo thì hệ tự sinh.

⚠️ **Đừng lẫn «Chức vụ» với «Cấp bậc».** *Cấp bậc* (`job_level`) là thang bảy mức
cố định — nhân viên · tổ trưởng · phó phòng · trưởng phòng · giám đốc khối · ban
tổng giám đốc — khai sẵn trong hệ thống, dùng để lọc và làm báo cáo cơ cấu, người
dùng **không thêm bớt được**. *Chức vụ* là chức danh cụ thể in trên phiếu, và
người dùng tự thêm bớt. Hai ô khác nhau trên cùng một hồ sơ.

## Tool `employee_lookup` — danh bạ, và CHỈ danh bạ

Gọi khi người hỏi cần tìm người: «số điện thoại của anh X», «email chị Y», «anh X
thuộc phòng nào», «phòng Kế toán có những ai», «ai là quản lý trực tiếp của tôi».
Tìm được theo tên, mã nhân viên, email, số điện thoại hoặc chức vụ.

Nó trả **đúng phần danh bạ**: mã NV · họ tên · chức vụ · cấp bậc · phòng ban ·
công ty · email · điện thoại (`phone` là **số chính**, nhãn của nó ở `phone_label`;
`extra_phones` là các **số khác**, mỗi số kèm nhãn như «Công việc», «Zalo») · quản lý
trực tiếp · tình trạng làm việc.
Tìm theo số điện thoại thì khớp cả số chính lẫn số khác. Đọc ra số chính trước; người
hỏi cần số Zalo / số khác thì đọc số có nhãn tương ứng.
**Không** có ngày sinh, CCCD, địa chỉ nhà, tài khoản ngân hàng, BHXH, lương —
những thứ đó không đi qua trợ lý bằng bất kỳ đường nào, đúng mục *Điều CẤM nói* ở
trên.

Hai điều phải nói đúng khi đọc kết quả:

- **Kết quả rỗng KHÔNG có nghĩa là công ty không có người đó.** Tool đã lọc theo
  phạm vi dữ liệu của người hỏi, nên rất có thể người đó nằm ngoài phạm vi. Nói cả
  hai khả năng, đừng khẳng định một.
- Mặc định chỉ ra **người đang làm việc**. Ai hỏi về người đã nghỉ thì nói rõ là
  cần tra riêng, đừng kết luận "không có người tên đó".

## Lương trên hồ sơ — chỉ chính chủ xem (từ 29/10/2026)

Hồ sơ có ô **Lương** và **Phụ cấp** (đồng / tháng) ở tab **«Chung» › mục «Công việc»**.

- **Xem số:** chỉ chính nhân sự đó — ở hồ sơ của mình và thẻ **«Lương của tôi»** trên
  Trang cá nhân (che sẵn, bấm con mắt để hiện). Người khác thấy «Đã nhập (ẩn)» / «Chưa nhập».
- **Nhập / sửa:** người có quyền sửa hồ sơ nhân sự đó. Gõ số mới để thay, «Xóa số đã nhập»
  để xóa, để trống là giữ nguyên. **Không ai tự đổi lương của chính mình.**
- **Ký hợp đồng lao động** (Nháp → Đã ký) tự chép lương cơ bản và phụ cấp của HĐ sang ô này
  nếu đó là HĐ hiệu lực mới nhất. HĐ ký trước nhưng hiệu lực ở tương lai thì tới ngày đó
  **chưa tự cập nhật** — phải sửa tay.
- Danh sách nhân sự không sắp xếp được theo lương; tệp Excel nhập nhân sự **không có cột
  lương** (có thì bị bỏ qua kèm cảnh báo); phiếu in thông tin nhân viên không có ô lương.
- **Quỹ lương** xem ở báo cáo **«Quỹ lương theo pháp nhân»** (phân hệ Báo cáo), chỉ người được
  giao báo cáo đó: chỉ **tổng** theo pháp nhân · phòng ban · toàn công ty, nhóm dưới 3 người
  bị che, bấm số chỉ ra danh sách tên **không kèm tiền**. Báo cáo này **không mở cho trợ lý**
  (`report_summary` không có nó) — ai hỏi quỹ lương thì chỉ đường tới màn báo cáo.

## Nhiều số điện thoại (từ 29/10/2026)

Tab **«Liên hệ & Ngân hàng»** của hồ sơ, và hộp **«Sửa thông tin liên hệ»** ở Trang cá nhân,
có danh sách **«Số điện thoại»**: tối đa **5 số** (1 số chính + 4 số khác), mỗi số kèm
nhãn tùy ý. Nút **«+ Thêm số»**, **«Đặt làm chính»** (đổi chỗ với số chính cũ, nhãn đi theo số), xóa.

- Mỗi số 8–15 chữ số, chỉ gồm chữ số, khoảng trắng và `+ . - ( )`; không được trùng nhau
  và không trùng số chính (so sau khi bỏ ký tự phân cách).
- **Số chính** là số dùng ở mọi chỗ khác (tìm kiếm, phiếu in, đặt xe…). Nhân viên tự sửa
  số của mình ở Trang cá nhân là **lưu ngay**, không qua duyệt.
- Tệp Excel xuất / nhập nhân sự có cột **«Nhãn số chính»** và **«Số điện thoại khác»** dạng
  `số (nhãn); số (nhãn)`; ô có dữ liệu **thay cả danh sách** số khác.

## Kế hoạch nhân sự — ĐÃ BỎ (29/10/2026)

Màn **Kế hoạch nhân sự** (định biên, quỹ lương kế hoạch, mẫu khoản chi phí) và báo cáo
**«Định biên kế hoạch so với thực tế»** đã **gỡ hẳn** khỏi ERP. Ai hỏi thì nói rõ là tính năng
đã bỏ — đừng chỉ đường tới màn không còn. Quỹ lương nay chỉ tính từ lương trên hồ sơ của
từng người (mục *Lương trên hồ sơ* ở trên).

## Người quản lý trực tiếp

Ô **«Người quản lý trực tiếp»** trên hồ sơ không phải để hiển thị cho đẹp: bộ máy
duyệt đọc nó để tìm người ký. Bỏ trống thì đơn từ của người đó có thể không tìm
được người duyệt. Hệ **chặn vòng lặp** (A quản lý B, B quản lý A) ngay lúc lưu.

## Nhập bằng tệp CSV

Cột chức vụ trong tệp khớp theo **tên**, bỏ qua hoa thường và khoảng trắng thừa.
Tên không khớp dòng nào trong danh mục thì hệ **giữ nguyên chữ đã gõ** và để
trống liên kết — nó **cố ý không tự tạo** chức vụ mới, vì như vậy mỗi lỗi gõ
trong một tệp sẽ đẻ ra một chức vụ rác. Nhập xong nên rà lại danh mục.

## Sơ đồ tổ chức (từ 22/10/2026)

Menu **Nhân sự ▸ Danh mục ▸ Sơ đồ tổ chức**. Không có bản vẽ nào lưu sẵn: màn **tự dựng từ dữ liệu**
phòng ban, trưởng phòng và «Người quản lý trực tiếp» — đổi phòng hay đổi người quản lý xong, sơ đồ
tự đúng. Cấu trúc: **pháp nhân › phòng ban (phòng con thụt vào) › người** (cấp dưới thụt dưới người quản lý cùng
phòng). Bấm tên phòng để mở / thu gọn (hai tầng đầu mở sẵn); đầu mỗi phòng có **Trưởng phòng** và **số người**; bấm
tên người để mở hồ sơ.

- Cần quyền xem hồ sơ nhân sự (`employee`). Không có thì màn báo **«Không có quyền xem sơ đồ tổ chức»**.
- ⚠️ **Chỉ hiện người trong phạm vi dữ liệu của người xem.** Hai người xem cùng sơ đồ có thể thấy hai cây khác
  nhau. Quản lý hay trưởng phòng nằm ngoài phạm vi thì **không lộ tên**. Đừng khẳng định "phòng X có N người".
- Người đã **nghỉ việc** hoặc ngưng hoạt động không có trên sơ đồ. Người chưa gán phòng/pháp nhân vào nhóm
  «Chưa gán pháp nhân».
- Sơ đồ sai thì sửa **ở nguồn**: ô *Phòng ban* và *Người quản lý trực tiếp* trên hồ sơ, hoặc *trưởng phòng* ở màn Phòng ban.

## Khóa tài khoản / cho nghỉ việc khi người đó còn việc duyệt treo (từ 22/10/2026)

Trước khi khóa tài khoản hay đưa hồ sơ sang **nghỉ việc**, hệ mở hộp **«kiểm việc đang giữ»**. Có bốn lối vào:
lưu hồ sơ sang trạng thái nghỉ việc (hộp **«Lưu hồ sơ nghỉ việc?»**), nút **«Khóa tài khoản + đăng xuất mọi thiết bị»** ở tab *Tài khoản*
của hồ sơ, biểu tượng ổ khóa ở danh sách tài khoản, và dòng **«Thôi việc»** ở tab *Quá trình công tác*.

- Hộp liệt kê **việc duyệt đang chờ người đó** (phiếu nào, bước nào, hạn, quá hạn chưa) và **bước luồng duyệt chỉ
  đích danh người đó** (phiếu mới sẽ lùi sang người dự phòng hoặc kẹt — nên đổi người ở luồng).
- Chuyển việc: chọn người nhận ở ô **«Chuyển cho…»** rồi bấm **«Chuyển»** từng việc hoặc **«Chuyển hết (N)»**.
  Chỉ người có quyền ghi **«Luồng duyệt»** (quản trị luồng duyệt) mới chuyển được; không có quyền thì hộp nói
  *nhờ quản trị luồng chuyển giúp*.
- **Không chặn cứng**: còn việc treo vẫn khóa được, nhưng nút đổi thành **«Vẫn khóa … (còn việc treo)»** để người bấm
  biết phiếu sẽ kẹt. Chuyển hết rồi thì nút trở lại bình thường.
- Phiếu mà người xem hộp không có quyền đọc thì chỉ hiện *«(bạn không có quyền xem phiếu này)»*, không lộ mã hay tên phiếu.
- Trợ lý không chuyển việc hộ; chỉ hướng dẫn các bước trên.

## In Phiếu thông tin nhân viên BM00../QT01/NS (từ 23/10/2026)

Nút **«In phiếu thông tin»** có ở hai chỗ:

- Phòng Nhân sự: màn chi tiết hồ sơ (**Nhân sự ▸ Nhân sự** ▸ mở một người), góc phải cạnh nút **Lưu**. Cần quyền
  xem hồ sơ nhân sự (`employee`) và hồ sơ nằm trong phạm vi. Trang in: `/print/employee-info/<id>`.
- Nhân viên tự in phiếu của mình: **Trang cá nhân ▸ Thông tin cá nhân**, nút ngay trên khối hồ sơ. Chỉ cần đăng
  nhập và tài khoản đã gắn hồ sơ. Trang in: `/print/my-employee-info`.

Phiếu A4 bảy mục: I. Thông tin cá nhân · II. Công việc · III. Liên hệ · IV. Ngân hàng · V. Giấy tờ và BHXH/BHYT ·
VI. Người báo tin khi cần thiết · VII. Thành viên hộ gia đình; cuối phiếu có ô ký **Người khai** và **Phòng Nhân sự**.
**Không có ô lương nào.** Bấm **«In phiếu / Lưu PDF»** để mở hộp in của trình duyệt. Ô hồ sơ chưa nhập in thành ô trống
để điền tay; hai bảng người luôn có tối thiểu ba dòng.

- ⚠️ Người in phiếu của **người khác** mà thiếu quyền xem thông tin nhạy cảm (`employee_sensitive`) thì ngày sinh,
  mã số thuế, địa chỉ, ngân hàng, CCCD, số sổ BHXH và hai bảng người báo tin / hộ gia đình **in trống** dù hồ sơ có dữ
  liệu (trang xem trước có dòng nhắc). Đừng nói "hồ sơ chưa khai"; nói là do thiếu quyền, nhờ người có quyền in hoặc
  để nhân viên tự in từ Trang cá nhân (phiếu của chính mình thì đủ mọi ô).

## Nhân viên tự đề nghị sửa hồ sơ, phòng Nhân sự duyệt (từ 23/10/2026)

Hai cách sửa hồ sơ của chính mình — trợ lý phải nói đúng cách cho đúng ô:

| Ô | Cách sửa |
|---|---|
| Số điện thoại (số chính và các số khác), địa chỉ thường trú, địa chỉ hiện nay, người báo tin | Tự sửa ở thẻ **«Liên hệ»** / bảng người báo tin trên Trang cá nhân, **lưu ngay**, không qua duyệt |
| Cá nhân (giới tính, ngày sinh, nơi sinh, dân tộc, tôn giáo, hôn nhân, số con, email cá nhân, học vấn, chuyên ngành) · Ngân hàng · Giấy tờ (CCCD, mã số thuế, số sổ BHXH, nơi KCB BHYT) · Hộ gia đình | **Gửi đề nghị**, phòng Nhân sự duyệt rồi mới vào hồ sơ |
| Họ tên, mã NV, phòng ban, chức vụ, quản lý trực tiếp, ngày vào làm… | Không tự đề nghị được — liên hệ phòng Nhân sự |

**Phía nhân viên** — **Trang cá nhân ▸ Thông tin cá nhân** ▸ thẻ **«Đề nghị sửa hồ sơ»** (dưới phần Liên hệ):

1. Bấm **«Đề nghị sửa thông tin»** → hộp bốn tab **Cá nhân · Ngân hàng · Giấy tờ · Hộ gia đình**, điền sẵn hồ sơ hiện tại.
2. Sửa ô cần đổi (đổi tab không mất chữ). Tab Hộ gia đình: danh sách gửi đi **thay cả danh sách cũ** khi được duyệt;
   dòng không có họ tên bị bỏ; tối đa 30 dòng. Ô «Số con» chỉ hiện khi hôn nhân là «Có gia đình».
3. Ghi chú cho phòng Nhân sự (tối đa 500 ký tự) nếu cần, bấm **«Gửi đề nghị»**. Chỉ ô đổi thật mới được gửi; không đổi
   gì thì báo **«Không có thay đổi nào để gửi»**.

- **Mỗi lúc chỉ một đề nghị chờ duyệt**: nút gửi mờ đi. Muốn sửa thêm thì **«Rút đề nghị»** rồi gửi lại đề nghị mới đủ ô.
- Thẻ hiện đề nghị gần nhất: trạng thái **Chờ duyệt / Đã duyệt / Từ chối / Đã rút lại**, từng ô cũ → mới, lý do từ chối.
- Duyệt xong hồ sơ cập nhật ngay; duyệt hay từ chối đều có thông báo chuông («Yêu cầu sửa hồ sơ đã được duyệt» /
  «Yêu cầu sửa hồ sơ bị từ chối»), từ chối kèm lý do người duyệt viết.

**Phía phòng Nhân sự** — menu **Nhân sự ▸ Danh mục ▸ «Duyệt sửa hồ sơ»** (`/hr/profile-change-requests`, con số cạnh
menu = số đang chờ trong phạm vi). Cần quyền **ghi** hồ sơ nhân sự (`employee.write`), chỉ thấy đề nghị của người trong
phạm vi được sửa. Danh sách mặc định lọc «Chờ duyệt», tìm theo mã / tên. Hồ sơ đang có đề nghị chờ thì màn chi tiết nhân
sự hiện dải nhắc kèm liên kết **«Xem đề nghị»**.

- Màn chi tiết: mỗi nhóm một bảng **Trường · Lúc gửi · Hiện tại · Đề nghị**. Dòng tô màu nhãn **«Đã đổi sau khi gửi»** =
  hồ sơ bị sửa sau lúc nhân viên gửi; duyệt sẽ **ghi đè** giá trị hiện tại. Hộ gia đình: hai bảng «Lúc gửi» / «Đề nghị».
- **«Duyệt»** → ghi cột Đề nghị vào hồ sơ ngay. **«Từ chối»** → bắt buộc nhập lý do (≤ 500 ký tự), hồ sơ giữ nguyên,
  nhân viên đọc được lý do.
- ⚠️ **Không tự duyệt đề nghị của chính mình** (trừ quản trị hệ thống) — hai nút ẩn, màn nói cần người khác duyệt.
- ⚠️ Đề nghị đụng **ngân hàng, giấy tờ, hộ gia đình hoặc ngày sinh** thì người duyệt phải có thêm quyền xem thông tin
  nhạy cảm (`employee_sensitive`); thiếu thì giá trị hiện «Đã ẩn (cần quyền xem thông tin nhạy cảm)» và không duyệt được.
- Trợ lý **không** gửi, rút, duyệt hay từ chối đề nghị hộ, và không đọc giá trị trong đề nghị ra; chỉ chỉ đường tới màn.
