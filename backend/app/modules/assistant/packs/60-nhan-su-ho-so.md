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
công ty · email và điện thoại công việc · quản lý trực tiếp · tình trạng làm việc.
**Không** có ngày sinh, CCCD, địa chỉ nhà, tài khoản ngân hàng, BHXH, lương —
những thứ đó không đi qua trợ lý bằng bất kỳ đường nào, đúng mục *Điều CẤM nói* ở
trên.

Hai điều phải nói đúng khi đọc kết quả:

- **Kết quả rỗng KHÔNG có nghĩa là công ty không có người đó.** Tool đã lọc theo
  phạm vi dữ liệu của người hỏi, nên rất có thể người đó nằm ngoài phạm vi. Nói cả
  hai khả năng, đừng khẳng định một.
- Mặc định chỉ ra **người đang làm việc**. Ai hỏi về người đã nghỉ thì nói rõ là
  cần tra riêng, đừng kết luận "không có người tên đó".

## Người quản lý trực tiếp

Ô **«Người quản lý trực tiếp»** trên hồ sơ không phải để hiển thị cho đẹp: bộ máy
duyệt đọc nó để tìm người ký. Bỏ trống thì đơn từ của người đó có thể không tìm
được người duyệt. Hệ **chặn vòng lặp** (A quản lý B, B quản lý A) ngay lúc lưu.

## Nhập bằng tệp CSV

Cột chức vụ trong tệp khớp theo **tên**, bỏ qua hoa thường và khoảng trắng thừa.
Tên không khớp dòng nào trong danh mục thì hệ **giữ nguyên chữ đã gõ** và để
trống liên kết — nó **cố ý không tự tạo** chức vụ mới, vì như vậy mỗi lỗi gõ
trong một tệp sẽ đẻ ra một chức vụ rác. Nhập xong nên rà lại danh mục.
