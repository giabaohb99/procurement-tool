# 20 — Hướng dẫn lập hai bộ tài khoản: phòng tự mua hàng và thu mua trừ phòng đó

> Áp dụng cho giao diện mới (ERP v2: `deverp` trên dev, cổng 8083 dưới máy).
> Thiết kế gốc: `doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` mục 5.1 (bao-CR-414).
> Ca đầu tiên là nhà máy **Dego Organic**, nhưng cách làm dưới đây dùng cho **mọi phòng tự mua**.

## 1. Hiểu trước khi bấm

Từ 17/09/2026, hệ thống **không có ô cấu hình** nào tên là "phòng tự mua hàng". Công tắc
nằm hoàn toàn ở **vai trò + phạm vi của từng tài khoản**:

| Bộ | Ai giữ | Vai trò | Phạm vi | Thấy gì |
|---|---|---|---|---|
| **A. Nhà máy** (phòng tự mua) | người đang thuộc phòng đó | *Quản lý thu mua phòng* (`pur_dept_manager`) + *Nhân viên thu mua* (`pur_staff`) | bậc **Được giao + đã duyệt trong phòng** (`dept_proc`) | phiếu đã duyệt **của phòng mình** và phiếu phòng khác **nhờ** phòng mình xử lý |
| **B. Thu mua trừ nhà máy** | người phòng Thu mua chung | *Quản lý thu mua* (`pur_manager`), *Admin thu mua* (`pur_admin`), *Nhân viên thu mua* (`pur_staff`) | như hiện tại + ô **Loại trừ phòng ban** = phòng tự mua | mọi phiếu **trừ** phiếu của phòng tự mua; phiếu phòng tự mua **nhờ** Thu mua chung thì vẫn thấy |

Bốn điều quyết định kết quả:

- **Phòng ban trong hồ sơ nhân sự** là thứ máy dùng để tính "phòng mình". Người của bộ A
  phải có phòng ban chính (hoặc phòng kiêm nhiệm) đúng là phòng tự mua.
- **Pháp nhân trong hồ sơ nhân sự KHÔNG thu hẹp gì** (từ 21/09/2026, bao-CR-434). Nó chỉ
  là công ty ký hợp đồng lao động. Người của Dego Organic ký với Dego Holding vẫn thấy và
  xử lý phiếu của phòng mình **đứng tên bất kỳ pháp nhân nào**, vì nhà máy mua cho nhiều
  công ty. Pháp nhân trên phiếu do người lập phiếu tự chọn, không cần trùng pháp nhân của
  họ. Muốn nhốt một tài khoản vào đúng một pháp nhân thì mới khai ô *Chỉ trong công ty*
  trong hộp Phạm vi. **Hai bộ trong hướng dẫn này không khai ô đó.**
- **Loại trừ thắng mọi bậc**. Ô *Loại trừ phòng ban* trừ ra khỏi cả bậc `all`, nên bộ B
  giữ nguyên bậc đang có, chỉ khai thêm ô loại trừ.
- **Ô "Xem THÊM phòng ban" là cộng thêm, không thu hẹp.** Đừng dùng nó để giới hạn bộ A;
  giới hạn đã nằm sẵn trong bậc `dept_proc` của vai trò.

Bộ mẫu đã có trên dev (`seed_tai_khoan_cr414.py`, mật khẩu = mã tài khoản theo quy ước
demo). Làm tay theo đúng khuôn này:

| Bộ | Mã | Họ tên gợi ý | Phòng ban | Vai trò |
|---|---|---|---|---|
| A | `NM_YC` | Nhân sự nhà máy | Dego Organic | Nhân sự (`employee`) |
| A | `NM_TP` | Trưởng phòng nhà máy | Dego Organic | Trưởng phòng (duyệt PYC) (`dept_head`) |
| A | `NM_MUA` | Quản lý thu mua nhà máy | Dego Organic | Quản lý thu mua phòng (`pur_dept_manager`) |
| A | `NM_NV` | Nhân viên thu mua nhà máy | Dego Organic | Nhân viên thu mua (`pur_staff`) |
| B | `TM_QL` | Quản lý thu mua trừ nhà máy | Sản xuất -Thu mua | Quản lý thu mua (`pur_manager`) + loại trừ Dego Organic |
| B | `TM_AD` | Admin thu mua trừ nhà máy | Sản xuất -Thu mua | Admin thu mua (`pur_admin`) + loại trừ Dego Organic |
| B | `TM_NV` | Nhân viên thu mua chung | Sản xuất -Thu mua | Nhân viên thu mua (`pur_staff`) |

Với người thật đang làm việc, **không tạo hồ sơ mới**: bỏ qua bước 2, đi thẳng từ bước 3
trên hồ sơ có sẵn của họ.

## 2. Chuẩn bị

| Cần | Kiểm ở đâu |
|---|---|
| Tài khoản quản trị (vai trò *Quản trị hệ thống*, hoặc vai trò có `role` quản lý + `user` ghi + `employee` tạo) | menu **Quản trị › Phân quyền tài khoản** mở được là đủ |
| Phòng tự mua và phòng Thu mua chung đã có trong danh mục | **Nhân sự › Phòng ban** |
| Vai trò *Quản lý thu mua phòng* có trong danh sách vai trò | **Quản trị › Phân quyền tài khoản › tab Vai trò & quyền**; thiếu thì hệ chưa chạy seed sau CR-414, báo kỹ thuật |
| Không tự sửa quyền của chính mình | màn hồ sơ và màn phân quyền **khóa** khi mở đúng tài khoản đang đăng nhập; nhờ một quản trị khác |

## 3. Bốn bước chung cho MỖI tài khoản

Bảy tài khoản trên đều đi qua đúng bốn bước này; mục 4 và 5 chỉ nói phần khác nhau.

### Bước 1 — Tạo hồ sơ nhân sự

1. Menu trái **Nhân sự › Nhân sự**, bấm **Thêm mới**.
2. Hộp *Thêm nhân sự*, điền:
   - **Mã NV**: gõ mã theo bảng trên (để trống thì hệ tự sinh, khó nhớ khi test).
   - **Họ tên**.
   - **Email**: bắt buộc điền ngay. Email này là **tên đăng nhập** của tài khoản sẽ tạo ở
     bước 2; tài khoản test dùng dạng `<mã viết thường>@dego.test`.
   - **Pháp nhân**: chọn công ty ký hợp đồng lao động (Dego Holding). Ô này **không**
     giới hạn phiếu người đó thấy (xem mục 1).
   - **Phòng ban**: chọn đúng phòng của bộ (Dego Organic cho bộ A, Sản xuất -Thu mua cho bộ B).
     Ô này chỉ hiện phòng của pháp nhân vừa chọn.
   - **Vị trí / Chức vụ**: chọn chức danh in trên phiếu (Trưởng phòng, Nhân viên thu mua...).
     Chức vụ **chỉ là nhãn**, không cấp quyền gì.
   - **Tình trạng làm việc**: Chính thức. **Trạng thái hồ sơ**: Đang hoạt động.
3. Bấm **Lưu**.

Người phụ trách thu mua cho **nhiều phòng tự mua** thì mở hồ sơ vừa tạo, tab **Chung**, kéo
xuống thẻ **Kiêm nhiệm**, chọn thêm phòng rồi bấm **Lưu kiêm nhiệm** (nút riêng, không phải
nút Lưu ở đầu trang). Bậc `dept_proc` tính cả phòng kiêm nhiệm.

### Bước 2 — Tạo tài khoản đăng nhập

1. Mở hồ sơ vừa tạo (**Nhân sự › Nhân sự**, bấm vào dòng), sang tab **Tài khoản**.
2. Thẻ *Tài khoản đăng nhập* báo "Nhân sự này chưa có tài khoản đăng nhập". Bấm
   **Tạo tài khoản đăng nhập**.
3. Hộp *Tạo tài khoản & đặt mật khẩu*: nhập **Mật khẩu mới** và **Nhập lại mật khẩu**, bấm
   **Xác nhận**. Luật mật khẩu: tối thiểu 8 ký tự, có cả chữ và số, không trùng mã nhân
   viên hay email.
4. Tài khoản mới **tự nhận vai trò Nhân sự**. Với `NM_YC` thế là xong bước 3; các tài khoản
   khác đi tiếp.

Nếu nút không hiện mà thẻ báo "Hãy nhập Email ở hồ sơ và lưu trước" thì quay lại bước 1
điền email.

### Bước 3 — Gán vai trò

1. Trên cùng thẻ *Tài khoản đăng nhập*, bấm nút **Phân quyền tài khoản** (hoặc menu
   **Quản trị › Phân quyền tài khoản › tab Người dùng**, tìm theo mã NV, bấm vào dòng).
2. Thẻ *Vai trò & phạm vi*: **tick** vai trò theo bảng ở mục 1, **bỏ tick** *Nhân sự* nếu
   người đó không lập phiếu (`NM_MUA`, `NM_NV`, `TM_QL`, `TM_AD`, `TM_NV` giữ đúng một vai
   trò thu mua là đủ; `NM_TP` giữ *Trưởng phòng (duyệt PYC)*).
3. Bấm **Lưu vai trò** ở góc trên phải. Chưa lưu thì cạnh vai trò chỉ có chữ
   "Lưu vai trò trước để đặt phạm vi".

### Bước 4 — Phạm vi (chỉ khi bảng ở mục 1 ghi "loại trừ")

1. Sau khi lưu, cạnh vai trò đã lưu hiện nút **Phạm vi**. Bấm vào.
2. Hộp *Phạm vi — {tên vai trò}*. Phần trên tóm tắt tài khoản này đang thấy gì với vai trò
   đó; **không cần khai gì thêm** cho bộ A.
3. Bộ B: mở mục gập **Ngoại lệ**, xuống ô **Loại trừ phòng ban** (khung đỏ), chọn phòng tự
   mua (Dego Organic). Các ô còn lại **để trống**, nhất là *Chỉ trong công ty*: khai vào
   là bộ B mất phiếu đứng tên các pháp nhân khác.
4. Bấm **Lưu phạm vi**.

### Làm nhanh Bước 3 và 4 bằng Trợ lý AI (từ 21/09/2026)

Xong Bước 1 và 2 bằng tay rồi, hai bước còn lại có thể nhờ Trợ lý AI: gõ vào ô chat, ví dụ
*"lập bộ tài khoản nhân viên thu mua cho Nguyễn Văn A, loại trừ phòng Dego Organic"*. Trợ lý
dò trước (đã có tài khoản chưa, đang giữ vai trò gì, phạm vi đang khai gì) rồi hiện **thẻ đề
xuất** liệt kê từng dòng *thêm / bỏ / không đổi*. Đọc kỹ thẻ, đúng ý thì bấm **Xác nhận** —
tới lúc đó hệ thống mới gán vai trò và ghi phạm vi, và vẫn kiểm lại quyền của chính bạn y như
lúc bấm tay trên màn Phân quyền. Thẻ báo *"đã đúng bộ"* thì không có gì để xác nhận.

Trợ lý **không** tạo tài khoản đăng nhập, **không** đặt mật khẩu, **không** tạo vai trò mới
và **không** tick thêm quyền vào vai trò — ba việc đó vẫn phải làm tay ở Bước 1-2 hoặc ở màn
*Vai trò & quyền*. Người chưa có tài khoản thì trợ lý chỉ chỉ đường sang màn Người dùng.
Cảnh báo vàng trên thẻ về ô *Chỉ trong công ty* còn khai là lời nhắc của điểm 3 trong Bước 4
ở trên; muốn gỡ thì nói rõ với trợ lý, nó không tự gỡ.

Bài tương ứng cho người dùng cuối trên Trung tâm HDSD: *Các chức năng khác › Trợ lý AI › Lập bộ
tài khoản thu mua bằng Trợ lý AI* (bao-CR-441, seed bằng
`backend/scripts/seed_help_tro_ly_ai_lap_bo_tai_khoan.py`). Đổi hành vi tool thì sửa cả mục này
lẫn bài đó.

## 4. Bộ A — Nhà máy (phòng tự mua hàng)

### 4.1 Bốn tài khoản

| Mã | Bước 1 | Bước 3 | Bước 4 |
|---|---|---|---|
| `NM_YC` | phòng Dego Organic | giữ *Nhân sự* (mặc định) | không |
| `NM_TP` | phòng Dego Organic, chức vụ Trưởng phòng | *Trưởng phòng (duyệt PYC)* | không |
| `NM_MUA` | phòng Dego Organic, chức vụ Quản lý thu mua phòng | *Quản lý thu mua phòng* | không |
| `NM_NV` | phòng Dego Organic, chức vụ Nhân viên thu mua | *Nhân viên thu mua* | không |

`NM_MUA` không cần Ngoại lệ nào: bậc `dept_proc` gắn sẵn trong vai trò đã giới hạn đúng
phòng trong hồ sơ. Mở hộp *Phạm vi* chỉ để đọc phần tóm tắt cho chắc: câu tóm tắt phải nêu
tên phòng Dego Organic.

### 4.2 Phân công phụ trách riêng cho phòng

Khi `NM_MUA` bấm **Điều phối** một phiếu của phòng, máy tra bảng phân công **theo phòng
đang xử lý phiếu**. Người bậc `dept_proc` **không được rơi về bộ "Thu mua chung"** (nếu
không là tự gán người ngoài vào phiếu nhà máy), nên phải khai bộ riêng:

1. Menu **Thu mua › Cấu hình › Phân công phụ trách**, bấm **Gán phân công mới**.
2. **Phòng áp dụng**: chọn *Dego Organic* (không để *Thu mua chung*).
3. **Phân loại VTBB**: tick các phân loại phòng hay mua.
4. **NSTM chính**: chọn `NM_NV` (hoặc người thu mua thật của phòng). **NSTM dự phòng**: tùy chọn.
5. **Lưu phân công**. Lặp lại cho từng nhóm phân loại.

Không khai bảng này thì điều phối vẫn chạy nhưng **mọi dòng đều trống người**, quản lý phòng
phải gán tay từng dòng bằng nút *Phân bổ*.

## 5. Bộ B — Thu mua trừ nhà máy

| Mã | Bước 1 | Bước 3 | Bước 4 |
|---|---|---|---|
| `TM_QL` | phòng Sản xuất -Thu mua | *Quản lý thu mua* | **Loại trừ phòng ban = Dego Organic** |
| `TM_AD` | phòng Sản xuất -Thu mua | *Admin thu mua* | **Loại trừ phòng ban = Dego Organic** |
| `TM_NV` | phòng Sản xuất -Thu mua | *Nhân viên thu mua* | không (bậc *Được giao* chỉ thấy dòng được gán, không rò gì thêm) |

Ghi chú khi khai ô loại trừ:

- Hộp thoại **không hiện cảnh báo vàng** ở ca này: cảnh báo "phòng của chính người này"
  (bao-CR-430) chỉ bật khi phòng bị trừ trùng phòng trong hồ sơ. Nếu thấy vàng, nghĩa là
  đang mở nhầm hồ sơ của một người thuộc Dego Organic.
- Hộp thoại **báo mâu thuẫn** nếu cùng một phòng nằm ở cả ô *Xem THÊM* lẫn ô *Loại trừ*.
  Bỏ bên *Xem THÊM*.
- Với người Thu mua chung **đã có tài khoản thật**, chỉ làm bước 4 cho **từng vai trò thu
  mua** họ đang giữ (mỗi vai trò một hộp Phạm vi riêng). Bỏ sót một vai trò là vai trò đó
  vẫn thấy phiếu nhà máy.

## 6. Kiểm tra sau khi làm

Đăng xuất tài khoản quản trị. Người đang đăng nhập **giữ bản quyền cũ** tới khi đăng nhập
lại, và máy chủ còn nhớ bản cũ tối đa một phút, nên kiểm bằng cửa sổ ẩn danh, đăng nhập
bằng email (hoặc mã NV) của từng tài khoản.

| Tài khoản | Phải thấy | Không được thấy |
|---|---|---|
| `NM_YC` | lập được Yêu cầu mua hàng; danh sách chỉ có phiếu mình lập | nhà cung cấp, đơn mua hàng |
| `NM_TP` | phiếu **Đã gửi duyệt** của phòng Dego Organic, nút *Duyệt* | phiếu phòng khác |
| `NM_MUA` | phiếu **Đã duyệt** trở đi của Dego Organic **đứng tên bất kỳ pháp nhân nào**; nút *Điều phối*; phiếu phòng khác có ô *Nhờ phòng xử lý* = Dego Organic | phiếu đã duyệt của phòng khác; danh sách trống khi chưa có phiếu nào của phòng được duyệt |
| `NM_NV` | dòng đã được gán cho mình | dòng gán người khác |
| `TM_QL` | mọi phiếu đã duyệt của mọi phòng, **mọi pháp nhân**, **trừ** Dego Organic; phiếu Dego Organic **nhờ** Sản xuất -Thu mua | phiếu Dego Organic thông thường (kể cả gõ thẳng id lên URL: phải ra *Không tìm thấy*) |
| `TM_AD` | như `TM_QL`, không có nút duyệt | như `TM_QL` |
| `TM_NV` | dòng được gán | phiếu chưa gán |

Đường chạy thử ngắn nhất: `NM_YC` lập một phiếu, `NM_TP` duyệt, `NM_MUA` thấy và điều phối,
`TM_QL` **không** thấy phiếu đó. Rồi `NM_YC` lập phiếu thứ hai chọn *Nhờ phòng xử lý* =
Sản xuất -Thu mua, `NM_TP` duyệt: lúc này `TM_QL` thấy, `NM_MUA` vẫn thấy.

## 7. Bẫy hay gặp

- **Đổi email trên hồ sơ không đổi tên đăng nhập** của tài khoản đã cấp. Điền đúng email
  trước khi bấm *Tạo tài khoản đăng nhập*.
- **Không thấy nút Phạm vi**: chưa bấm *Lưu vai trò*.
- **Đổi quyền xong vẫn thấy như cũ**: người đó chưa đăng xuất, hoặc chưa qua một phút.
- **Sửa hồ sơ hoặc quyền của chính mình bị khóa**: cố ý, nhờ quản trị khác.
- **Hai phòng trùng tên ở hai công ty**: ô loại trừ khớp theo **tên**, sẽ trừ cả hai.
  Đặt tên phòng khác nhau trước.
- **Không thấy phiếu đứng tên pháp nhân khác**: có người đã khai *Chỉ trong công ty* trong
  hộp Phạm vi của vai trò đó. Xóa ô đó. Pháp nhân trong hồ sơ nhân sự **không** phải
  nguyên nhân (từ bao-CR-434 hồ sơ không thu hẹp gì).
- **Nhờ nhầm sang phòng không có ai giữ vai trò thu mua**: phiếu chỉ còn phòng lập thấy.
  Sửa lại ô *Nhờ phòng xử lý* khi phiếu còn Nháp / Bị trả lại, hoặc dùng nút
  *Trả về phòng lập* trên phiếu đã duyệt.
- **Chuyển đi giữa chừng**: nút *Chuyển phòng xử lý* / *Trả về phòng lập* trên chi tiết
  YCMH và YCBG chỉ hiện cho quản lý thu mua của phòng đang giữ phiếu (hoặc quản lý thu mua
  toàn hệ), và chỉ khi chưa dòng nào lên đơn mua hàng.

## 8. Mở thêm một phòng tự mua khác

Không sửa mã, không sửa cấu hình. Lặp lại:

1. Mục 4 cho phòng mới (hồ sơ ở phòng đó, cấp *Quản lý thu mua phòng* + *Nhân viên thu
   mua*, khai *Phân công phụ trách* với *Phòng áp dụng* = phòng đó).
2. Mục 5 bước 4: mở **từng** tài khoản Thu mua chung, thêm phòng mới vào ô *Loại trừ phòng
   ban* của **từng** vai trò thu mua họ giữ.

Bước 2 là chỗ dễ quên nhất và quên thì **lủng im lặng**: Thu mua chung vẫn thấy phiếu phòng
mới mà không ai báo lỗi. Ghi phòng mới vào danh sách kiểm định kỳ của quản trị.
