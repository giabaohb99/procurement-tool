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
  khác, kể cả quản trị và phòng Nhân sự, chỉ thấy **Đã nhập (ẩn)** hoặc **Chưa nhập**.
  Trợ lý không có đường nào tới các số đó. Người hỏi lương của mình thì chỉ đường tới
  **Trang cá nhân**; hỏi lương người khác thì nói thẳng là chỉ chính chủ xem được.

## Chức vụ lấy từ DANH MỤC, không gõ tay nữa

Ô **Vị trí / Chức vụ** trên hồ sơ là **ô chọn**. Muốn có một chức danh mới thì phải
thêm nó ở danh mục Chức vụ trước, rồi mới chọn được — không có cách gõ thẳng.
Thêm chức vụ mở **trang riêng**, không phải hộp thoại.

Bốn luật hay bị hỏi, và trợ lý nói sai là người dùng làm hỏng dữ liệu thật:

- **Đổi TÊN một chức vụ là đổi luôn chức danh của MỌI người đang giữ nó** — kể
  cả chức danh in trên phiếu và trong tệp Excel đã xuất. Sửa lỗi chính tả thì
  tốt; nhưng dùng một dòng cũ để "đặt tên cho chức vụ khác" là ghi đè lên hàng
  chục hồ sơ. Trường hợp sau phải **tạo dòng mới**.
- **Không xóa được chức vụ đang có người giữ.** Muốn dẹp thì **bỏ tick *Đang
  dùng***: nó biến khỏi ô chọn, nhưng hồ sơ cũ vẫn hiện đúng chức danh. Đây là
  cách làm đúng, không phải cách đi vòng.
- **Chức vụ đã ngừng dùng thì không gán MỚI được**, nhưng người **đang** giữ nó
  vẫn sửa và lưu hồ sơ bình thường.
- **Mã chức vụ không đổi được sau khi tạo** (tệp Excel nhập/xuất trỏ vào dòng
  bằng mã). Bỏ trống lúc tạo thì hệ tự sinh.

⚠️ **Đừng lẫn *Chức vụ* với *Cấp bậc*.** *Cấp bậc* (`job_level`) là thang bảy mức
cố định — nhân viên · tổ trưởng · phó phòng · trưởng phòng · giám đốc khối · ban
tổng giám đốc — khai sẵn trong hệ thống, dùng để lọc và làm báo cáo cơ cấu, người
dùng **không thêm bớt được**. *Chức vụ* là chức danh cụ thể in trên phiếu, và
người dùng tự thêm bớt. Hai ô khác nhau trên cùng một hồ sơ.

## Tool `employee_lookup` — danh bạ, và CHỈ danh bạ

Gọi khi người hỏi cần tìm người: **số điện thoại của anh X**, **email chị Y**, **anh X
thuộc phòng nào**, **phòng Kế toán có những ai**, **ai là quản lý trực tiếp của tôi**.
Tìm được theo tên, mã nhân viên, email, số điện thoại hoặc chức vụ.

Nó trả **đúng phần danh bạ**: mã NV · họ tên · chức vụ · cấp bậc · phòng ban ·
công ty · email · điện thoại (`phone` là **số chính**, nhãn của nó ở `phone_label`;
`extra_phones` là các **số khác**, mỗi số kèm nhãn như **Công việc**, **Zalo**) · quản lý
trực tiếp · tình trạng làm việc · `concurrent_roles` = các **kiêm nhiệm đang hiệu lực**, mỗi mục một câu
**Phòng X — Công ty B (Chức vụ)** (có thể ở công ty khác; rỗng = không kiêm nhiệm).
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

## Kiêm nhiệm — tab riêng, kiêm nhiệm được ở công ty khác (từ 12/11/2026)

Kiêm nhiệm khai ở tab ***Kiêm nhiệm*** của hồ sơ (**Nhân sự ▸ Nhân sự** ▸ mở hồ sơ), nút ***Thêm kiêm nhiệm***. Thẻ chọn nhiều
phòng kiêm nhiệm ở tab *Chung* **đã bỏ** — đừng chỉ đường tới đó. Mỗi dòng: **Công ty** (khác công ty chính được), **Phòng ban**
(phải phục vụ công ty đó), **Chức vụ**, **Từ ngày** (bắt buộc), **Đến ngày** (trống = chưa kết thúc), **Số QĐ**, **Ngày QĐ**,
**Ghi chú**, tệp QĐ, và công tắc ***Tính vào phạm vi quyền***.

Câu hay bị hỏi: **kiêm nhiệm ở công ty khác có thấy dữ liệu công ty đó không?** Trả lời đúng ba ý, đừng nói chung chung:

- **Chỉ thấy đúng PHÒNG đó ở đúng CÔNG TY đó**, không thấy cả công ty B. Thấy như một nhân viên của phòng, theo vai trò họ đang
  có (xem, duyệt, sửa nếu vai trò cho phép ở mức phòng ban). Văn bản, thư mục, báo cáo, skill AI chia cho phòng đó cũng tới họ.
- **Chỉ khi công tắc *Tính vào phạm vi quyền* đang BẬT** — tắt thì dòng chỉ là ghi nhận, không mở dữ liệu gì.
- **Chỉ trong thời gian dòng còn hiệu lực.** Trạng thái tự đổi theo ngày (giờ Việt Nam): ***Sắp tới*** → ***Đang hiệu lực***
  → ***Đã hết***; tới ngày là tự hết, không ai phải bấm. Thay đổi có tác dụng sau tối đa khoảng một phút.

Các luật khác phải nói đúng:

- **Chức vụ kiêm nhiệm không tự cấp thêm vai trò** — quyền mặc định theo chức vụ chỉ theo chức vụ CHÍNH.
- **Ai khai được:** người có quyền sửa hồ sơ đó, VÀ phòng + công ty kiêm nhiệm nằm trong phạm vi sửa của chính họ (phạm vi phòng
  chỉ khai được phòng mình; phạm vi công ty chỉ trong công ty mình; toàn hệ thống thì mọi nơi). **Không ai tự khai kiêm nhiệm cho
  chính mình, kể cả quản trị.**
- **Đổi pháp nhân chính**: kiêm nhiệm ở công ty CŨ mặc định **kết thúc vào hôm qua**; lúc Lưu có hộp ***Kiêm nhiệm ở công ty cũ***
  để tick dòng muốn giữ; dòng chưa bắt đầu mà không giữ thì **bị xóa** kèm tệp. Kiêm nhiệm ở công ty khác không bị đụng.
  Đổi phòng chính thì có hộp ***Giữ phòng cũ làm kiêm nhiệm?***.
- **Phía phòng được kiêm nhiệm** thấy người đó ở **trang chi tiết phòng ban** (khối ***Kiêm nhiệm tại phòng này***) và **sơ đồ
  tổ chức** (khối riêng, nhãn ***Kiêm nhiệm***); mở được hồ sơ của họ (chỉ xem) khi dòng đang hiệu lực + bật công tắc.
  **Quân số và báo cáo vẫn tính ở phòng chính** — không đếm hai lần. Danh sách *Nhân sự* lọc theo phòng KHÔNG ra người kiêm nhiệm.
- Tệp QĐ kiêm nhiệm của người khác cần quyền xem thông tin nhạy cảm (`employee_sensitive`).
- Trợ lý **không** thêm / sửa / xóa kiêm nhiệm hộ; chỉ chỉ đường. `employee_lookup` vẫn lọc người theo phạm vi hồ sơ CHÍNH: người
  chỉ kiêm nhiệm ở phòng của người hỏi mà hồ sơ chính ở công ty khác có thể không ra — khi đó gợi ý xem trang chi tiết phòng ban.
- Báo cáo ***Điều chuyển & bổ nhiệm*** đếm kiêm nhiệm theo dòng ở tab *Quá trình công tác*, nên số ở đó có thể thấp hơn số dòng
  ở tab *Kiêm nhiệm*.

## Lương trên hồ sơ — chỉ chính chủ xem (từ 29/10/2026)

Hồ sơ có ô **Lương** và **Phụ cấp** (đồng / tháng) ở tab ***Chung* › mục *Công việc***.

- **Xem số:** chỉ chính nhân sự đó — ở hồ sơ của mình và thẻ ***Lương của tôi*** trên
  Trang cá nhân (che sẵn, bấm con mắt để hiện). Người khác thấy **Đã nhập (ẩn)** / **Chưa nhập**.
- **Nhập / sửa:** người có quyền sửa hồ sơ nhân sự đó. Gõ số mới để thay, **Xóa số đã nhập**
  để xóa, để trống là giữ nguyên. **Không ai tự đổi lương của chính mình.**
- **Ký hợp đồng lao động** (Nháp → Đã ký) tự chép lương cơ bản và phụ cấp của HĐ sang ô này
  nếu đó là HĐ hiệu lực mới nhất. HĐ ký trước nhưng hiệu lực ở tương lai thì tới ngày đó
  **chưa tự cập nhật** — phải sửa tay.
- Danh sách nhân sự không sắp xếp được theo lương; tệp Excel nhập nhân sự **không có cột
  lương** (có thì bị bỏ qua kèm cảnh báo); phiếu in thông tin nhân viên không có ô lương.
- **Quỹ lương** xem ở báo cáo ***Quỹ lương theo pháp nhân*** (phân hệ Báo cáo), chỉ người được
  giao báo cáo đó: chỉ **tổng** theo pháp nhân · phòng ban · toàn công ty, nhóm dưới 3 người
  bị che, bấm số chỉ ra danh sách tên **không kèm tiền**. Báo cáo này **không mở cho trợ lý**
  (`report_summary` không có nó) — ai hỏi quỹ lương thì chỉ đường tới màn báo cáo.

## Hợp đồng lao động (HĐLĐ)

HĐLĐ **không có màn danh sách riêng**: nằm ở tab ***Hợp đồng*** của hồ sơ (**Nhân sự ▸ Nhân sự** ▸ mở hồ sơ). Trợ lý **không** lập,
sửa, ký, hủy hay chấm dứt hợp đồng hộ; chỉ hướng dẫn và chỉ đường.

**Điều CẤM nói thêm:** không đọc lương cơ bản, lương đóng BH, phụ cấp trên hợp đồng, và **không đọc giá trị biến tùy chỉnh** của
một hợp đồng (phụ cấp riêng, số ngày phép…) — chúng nhạy cảm như lương. Không công cụ nào trả các số đó.

| Người dùng hỏi | Trả lời / chỉ đường |
|---|---|
| Lập HĐLĐ cho một người | Tab ***Hợp đồng*** ▸ ***Lập hợp đồng***: chọn ***Loại hợp đồng***, ngày (hàng nút ***Chọn nhanh*** điền ngày kết thúc), lương, khối ***Thông tin bổ sung cho mẫu*** nếu có, tệp bản ký / scan (không bắt buộc) ▸ ***Lưu*** → HĐ ở **Nháp**. Ô ***Pháp nhân*** chỉ để xem, lấy từ hồ sơ |
| Chọn mẫu nào, mẫu của công ty nào | Mỗi mẫu gắn **một pháp nhân + một loại HĐ**. Pháp nhân và phòng ban được **chụp lúc lập**: người đó chuyển công ty sau này thì HĐ cũ vẫn dùng mẫu của pháp nhân cũ. Pháp nhân chưa có mẫu cho loại đó thì vẫn lưu được HĐ, chỉ chưa sinh được tệp |
| Sinh tệp Word, ký, hủy, chấm dứt | Nút ***…*** cuối dòng HĐ (menu Thao tác): ***Sinh tệp hợp đồng*** · ***Tải lên bản đã ký*** · ***Đánh dấu đã ký*** · ***Hủy hợp đồng*** (Nháp) · ***Chấm dứt / thanh lý*** (Đã ký) · ***Xóa hợp đồng*** (Nháp / Đã hủy). Hủy và chấm dứt **không hoàn tác được** |
| Sửa HĐ đã ký | Không sửa được nữa; cần đổi nội dung thì chấm dứt rồi lập HĐ mới. Sửa HĐ nháp sau khi đã sinh tệp thì **tệp bị gỡ**, phải sinh lại |
| HĐ hết hạn có phải bấm gì không | Không. Trạng thái **Hết hạn** tự suy ra khi qua ngày kết thúc |
| Tải lên / soạn mẫu, thêm biến | **Nhân sự ▸ Danh mục ▸ Mẫu hợp đồng** (văn thư: **Văn bản ▸ Thiết lập văn bản** ▸ ***Thư viện văn bản mẫu***, cùng dữ liệu). Biến ở nút ***Danh sách biến*** |
| HĐ sắp hết hạn của ai | Ba chỗ: chuông, **Trang cá nhân ▸ Việc cần làm** (loại ***HĐ lao động hết hạn***), thẻ ***Hợp đồng lao động sắp hết hạn*** ở **Nhân sự ▸ Tổng quan**. Danh sách toàn công ty: báo cáo ***Hợp đồng lao động*** (`/report/labor-contract`) |
| Có bao nhiêu HĐ sắp hết / quá hạn / chưa có HĐ | `report_summary` với `report_key` = `labor_contract` (mục dưới) |
| Xem lại HĐ của chính mình | **Trang cá nhân** ▸ nhóm ***Hồ sơ*** ▸ ***Hợp đồng của tôi***: chỉ HĐ đã ký / đã chấm dứt, nút ***Tải bản mềm (.docx)*** và ***Xem / tải bản đã ký***. Không cần quyền gì thêm |

Luật phải nói đúng:

- **Không ai tự lập HĐ cho chính mình** — kể cả người phòng Nhân sự.
- **Biến mẫu**: biến hệ thống tự lấy từ hồ sơ và HĐ; biến tùy chỉnh (kiểu ***Chữ***, ***Chữ nhiều dòng***, ***Số***, ***Ngày***, ***Tiền***) nhập tay
  theo từng HĐ. Biến **Tiền** tự có thêm biến đọc bằng chữ (mã + `_bang_chu`). **Giá trị mặc định** chép vào HĐ lúc **lập**, đổi
  mặc định sau không đổi HĐ đã lập. **Bắt buộc** không chặn lưu nháp, chỉ chặn ***Sinh tệp*** và ***Đánh dấu đã ký***. Biến đang được
  dùng thì không xóa được, chọn ***Ngừng dùng***. Thêm / sửa / xóa biến cần quyền sửa Mẫu HĐLĐ với phạm vi **tất cả pháp nhân**.
- **Cảnh báo hết hạn**: HĐ **Đã ký** hết trong **N ngày** tới hoặc đã quá hạn, đỏ khi còn ≤ **M ngày** (mặc định 30 và 15, đổi ở
  *Cài đặt nhân sự*, mục trên). Thôi báo khi đã có HĐ nối tiếp, người đó nghỉ việc, hoặc HĐ được chấm dứt. Không gửi email.
- **Ký HĐ** tự chép lương, phụ cấp sang hồ sơ nếu là HĐ hiệu lực mới nhất (mục *Lương trên hồ sơ*).
- **Quyền** (**Quản trị ▸ Phân quyền tài khoản** ▸ tab ***Vai trò & quyền***): dòng ***Hợp đồng lao động (có lương)*** — Xem (thấy tab,
  nhận cảnh báo) · Tạo (***Lập hợp đồng***) · Sửa (sinh tệp, ký, hủy, chấm dứt) · Xóa · In (***Tải hợp đồng (.docx)***); dòng ***Mẫu hợp đồng
  lao động*** — Xem / Tạo / Sửa / Xóa. Phạm vi theo pháp nhân và phòng ban của HĐ. Người chỉ xem được hồ sơ thì **không thấy tab
  Hợp đồng** — nói là thiếu quyền, đừng nói "người này chưa có hợp đồng".
- Trên điện thoại mỗi HĐ là một thẻ, nút ***…*** ở góc thẻ mở cùng menu Thao tác.

**Công cụ:** `report_summary` với `report_key` = `labor_contract` trả **số đếm** (không tên, không lương): ***Đang hiệu lực***,
***Hết hạn trong 30 / 60 / 90 ngày***, ***Thử việc hết trong 30 ngày***, ***Đã quá hạn, vẫn đi làm***, ***Đang làm, chưa có HĐ***, ***Đã ký, chưa tải
bản scan***, ***Người đã nghỉ, HĐ chưa chấm dứt***…; `filters.group_by` = `company` · `department` · `contract_type`. Cần được giao báo cáo
đó **và** quyền xem HĐLĐ; bị từ chối thì báo đúng lý do, đừng thử công cụ khác. Cần **danh sách người** thì chỉ đường tới thẻ ở
Tổng quan Nhân sự hoặc màn báo cáo. **Đừng nhầm:** `contract_list_by_expiry`, `contract_count_by_status`, `supplier_contracts` là hợp đồng
**nhà cung cấp** (Thu mua), **không** dùng cho câu hỏi về HĐLĐ.

## Nhiều số điện thoại (từ 29/10/2026)

Tab ***Liên hệ & Ngân hàng*** của hồ sơ, và hộp ***Sửa thông tin liên hệ*** ở Trang cá nhân,
có danh sách ***Số điện thoại***: tối đa **5 số** (1 số chính + 4 số khác), mỗi số kèm
nhãn tùy ý. Nút ***+ Thêm số***, ***Đặt làm chính*** (đổi chỗ với số chính cũ, nhãn đi theo số), xóa.

- Mỗi số 8–15 chữ số, chỉ gồm chữ số, khoảng trắng và `+ . - ( )`; không được trùng nhau
  và không trùng số chính (so sau khi bỏ ký tự phân cách).
- **Số chính** là số dùng ở mọi chỗ khác (tìm kiếm, phiếu in, đặt xe…). Nhân viên tự sửa
  số của mình ở Trang cá nhân là **lưu ngay**, không qua duyệt.
- Tệp Excel xuất / nhập nhân sự có cột ***Nhãn số chính*** và ***Số điện thoại khác*** dạng
  `số (nhãn); số (nhãn)`; ô có dữ liệu **thay cả danh sách** số khác.

## Kế hoạch nhân sự — ĐÃ BỎ (29/10/2026)

Màn **Kế hoạch nhân sự** (định biên, quỹ lương kế hoạch, mẫu khoản chi phí) và báo cáo
***Định biên kế hoạch so với thực tế*** đã **gỡ hẳn** khỏi ERP. Ai hỏi thì nói rõ là tính năng
đã bỏ — đừng chỉ đường tới màn không còn. Quỹ lương nay chỉ tính từ lương trên hồ sơ của
từng người (mục *Lương trên hồ sơ* ở trên).

## Người quản lý trực tiếp

Ô ***Người quản lý trực tiếp*** trên hồ sơ không phải để hiển thị cho đẹp: bộ máy
duyệt đọc nó để tìm người ký. Bỏ trống thì đơn từ của người đó có thể không tìm
được người duyệt. Hệ **chặn vòng lặp** (A quản lý B, B quản lý A) ngay lúc lưu.

## Nhập hồ sơ hàng loạt bằng tệp Excel (từ 19/10/2026)

Nút ***Nhập Excel*** ở **Nhân sự ▸ Nhân sự**, cạnh ***Thêm mới***. Trợ lý **không** nhập, ghi thật hay hoàn tác hộ; chỉ
hướng dẫn. Các bước: ***Tải file mẫu*** (có sheet hướng dẫn từng cột) → giữ chế độ ***Chạy thử*** (kiểm cả tệp, **chưa ghi**
gì) → thả tệp .xlsx / .csv, bấm ***Bắt đầu import*** → đọc trang chi tiết lần nhập (Tạo · Cập nhật · Lỗi · Cần rà soát…), sửa
tệp tới khi sạch → ***Ghi thật*** (mỗi bản chạy thử chỉ ghi thật **một lần**).

Luật hay bị hỏi, nói sai là làm hỏng hồ sơ thật:

- **Ô trống hoặc thiếu cột = giữ nguyên**, không xóa. Muốn xóa một ô thì ghi đúng `__/empty_value/__`. Không xóa được
  Họ tên, Trạng thái, Đang dùng.
- **Mã NV** có rồi thì cập nhật, chưa có thì tạo mới, trống thì tạo mới và hệ tự sinh mã. Một mã chỉ được **một dòng**.
- Giá trị lạ ở ô mã số / trạng thái / ngày là **lỗi dòng**, hệ không đoán. Tối đa **2000 dòng**.
- **Không xóa nhân sự qua tệp** (muốn ngưng thì đặt nghỉ việc). Không nhập qua tệp: lương (cột bị bỏ kèm cảnh báo), kiêm
  nhiệm, người thân / người báo tin, tài khoản đăng nhập.
- Cột chức vụ khớp theo mã hoặc **tên** (bỏ qua hoa thường, khoảng trắng thừa). Không khớp thì hệ **giữ nguyên chữ** làm chức
  danh, gắn **Cần rà soát**, và **cố ý không tự tạo** chức vụ mới (mỗi lỗi gõ sẽ đẻ ra một chức vụ rác).
- **Cột nhạy cảm** (ngày sinh, mã số thuế, địa chỉ, ngân hàng, CCCD, BHXH) cần **quyền ghi thông tin nhạy cảm**; thiếu thì
  **cả cột bị bỏ qua** kèm một cảnh báo, cột khác vẫn ghi. Tải lại tệp gốc của lô cần quyền xem thông tin nhạy cảm.
- **Hoàn tác** cả lô ở **Quản trị ▸ Nhập dữ liệu** ▸ mở lô ▸ ***Hoàn tác***: hồ sơ sửa về giá trị cũ, hồ sơ tạo mới bị xóa (trừ khi
  đã có dữ liệu con hoặc bị sửa sau lô). Ô nào đã bị ai sửa tiếp sau lô thì **từ chối cả lượt** hoàn tác.
- **Ai làm được:** quyền ***Xem*** + ***Tạo*** ở dòng ***Nhập dữ liệu (Import)***, cộng ***Tạo*** hoặc ***Sửa*** hồ sơ nhân viên; hoàn tác lô có
  tạo mới cần thêm ***Xóa*** hồ sơ. Mỗi dòng chỉ ghi được người trong phạm vi; không tự đổi phòng của chính mình. Không thấy nút
  thì nói là thiếu quyền, nhờ quản trị tick ở **Quản trị ▸ Phân quyền tài khoản**.

## Quyền mặc định theo chức vụ (từ 20/10/2026)

**Nhân sự ▸ Danh mục ▸ Chức vụ** ▸ mở một chức vụ ▸ tab ***Quyền mặc định***: khai một **gói vai trò**, ***Thêm*** từng vai trò rồi
***Lưu***. Tài khoản của người giữ chức vụ đó được hệ **tự cấp gói** khi cấp tài khoản, khi đổi chức vụ (lưu hồ sơ, nhập Excel,
hoàn tác lô, áp quá trình công tác) và khi mở khóa lại tài khoản.

- **Lưu gói chưa đổi quyền của ai.** Muốn áp cho người **đang** giữ chức vụ: ***Áp lại cho người đang giữ chức vụ (N người)*** →
  hộp ***Áp lại quyền mặc định*** → ***Áp lại***. Áp lại thêm vai trò còn thiếu, gỡ vai trò hệ đã tự cấp mà nay không còn trong gói;
  **vai trò quản trị gán tay không bị đụng**.
- **Gói chỉ là danh sách vai trò, không có mức phạm vi** (xem của mình / phòng / công ty nằm ở cấu hình từng vai trò).
- **Không ai tự cấp cho chính mình**: người không phải quản trị đổi chức vụ của mình thì không nhận gói; người đang giữ chức vụ
  không thêm được vai trò vào gói của chính chức vụ đó. Người thao tác chỉ cấp được vai trò mình có đủ quyền.
- Không đưa vào gói được vai trò quản trị và vai trò có quyền tạo / sửa / xóa ở ***Vai trò & phân quyền*** hoặc ***Tài khoản***.
- Sửa gói cần quyền ***Sửa*** ở dòng ***Vai trò & phân quyền*** (không phải quyền sửa danh mục chức vụ).
- Ở Phân quyền tài khoản, vai trò cấp theo gói có nhãn ***Theo chức vụ: …***. Bỏ tick riêng cho một người sẽ bị cấp lại ở lần
  Áp lại / đổi chức vụ sau; muốn bỏ hẳn thì sửa gói hoặc đổi chức vụ.
- Hỏi "sao tôi vừa đổi chức vụ mà chưa có quyền" → quyền mới có tác dụng sau tối đa khoảng một phút; đăng xuất rồi đăng nhập lại.
  Kiêm nhiệm không tự cấp gói (mục *Kiêm nhiệm* ở trên).

## Quyền Xuất, Nhập và che cột nhạy cảm khi xuất tệp

- Trong ma trận quyền của vai trò, ***Xuất*** và ***Nhập*** là **cột riêng**, không còn đi theo ***Xem*** / ***Sửa***. Vai trò cũ không tự
  có hai cột này; ai hỏi "hôm trước xuất được mà nay không" thì gợi ý quản trị tick lại ***Xuất*** / ***Nhập***.
- Xuất danh sách nhân sự: **Quản trị ▸ Xuất dữ liệu** ▸ ***Xuất dữ liệu*** ▸ bảng Nhân sự, cần ***Xuất*** ở dòng ***Nhân viên***. Tệp chỉ
  gồm hồ sơ trong **phạm vi của quyền Xuất** (không phải phạm vi Xem).
- Cột nhạy cảm để **trống** khi người xuất thiếu quyền xem thông tin nhạy cảm (dòng của chính họ vẫn đủ) — ô trống **không có
  nghĩa là hồ sơ chưa nhập**. Lương **không bao giờ** có trong tệp xuất.
- Tải lại tệp đã xuất: chỉ chính người xuất, hoặc người có ***Xuất*** phạm vi tất cả trên bảng đó (bảng Nhân sự cần thêm quyền xem
  thông tin nhạy cảm phạm vi tất cả).
- Trợ lý không thay được màn Xuất dữ liệu: `export_excel_file` chỉ đổ số liệu đã tra trong hội thoại (danh bạ của
  `employee_lookup` chẳng hạn), không ra tệp hồ sơ đủ cột. Ai cần tệp hồ sơ thì chỉ đường tới **Quản trị ▸ Xuất dữ liệu**.

## Sơ đồ tổ chức (từ 22/10/2026)

Menu **Nhân sự ▸ Sơ đồ tổ chức**. Không có bản vẽ nào lưu sẵn: màn **tự dựng từ dữ liệu**
phòng ban, trưởng phòng và **Người quản lý trực tiếp** — đổi phòng hay đổi người quản lý xong, sơ đồ
tự đúng. Cấu trúc: **pháp nhân › phòng ban (phòng con thụt vào) › người** (cấp dưới thụt dưới người quản lý cùng
phòng). Bấm tên phòng để mở / thu gọn (hai tầng đầu mở sẵn); đầu mỗi phòng có **Trưởng phòng** và **số người**; bấm
tên người để mở hồ sơ.

- Cần quyền xem hồ sơ nhân sự (`employee`). Không có thì màn báo ***Không có quyền xem sơ đồ tổ chức***.
- ⚠️ **Chỉ hiện người trong phạm vi dữ liệu của người xem.** Hai người xem cùng sơ đồ có thể thấy hai cây khác
  nhau. Quản lý hay trưởng phòng nằm ngoài phạm vi thì **không lộ tên**. Đừng khẳng định "phòng X có N người".
- Người đã **nghỉ việc** hoặc ngưng hoạt động không có trên sơ đồ. Người chưa gán phòng/pháp nhân vào nhóm
  **Chưa gán pháp nhân**.
- Sơ đồ sai thì sửa **ở nguồn**: ô *Phòng ban* và *Người quản lý trực tiếp* trên hồ sơ, hoặc *trưởng phòng* ở màn Phòng ban.
- Từ 02/11/2026 Nhân sự có công tắc **Ai cũng xem được sơ đồ tổ chức** (mặc định BẬT) ở *Cài đặt nhân sự*. Tắt thì chỉ
  người có phạm vi hồ sơ nhân sự **không giới hạn** (không bó theo công ty / phòng / người) mới mở được sơ đồ — người khác
  nhận báo không có quyền. Người dùng hỏi "sao hôm qua xem được mà nay không" thì gợi ý hỏi Nhân sự về công tắc này.

## Cài đặt nhân sự — tab Nhân viên / Hợp đồng (từ 02/11/2026)

*Nhân sự ▸ Thiết lập*, tab *Cài đặt nhân sự* (quyền `setting`). Những con số dưới đây là **cài đặt**, mỗi công ty có thể khác —
đừng khẳng định số mặc định khi người dùng hỏi về hệ của họ, bảo họ xem ở màn này.

- **Tiền tố mã nhân sự** (mặc định `NSU`): áp cho hồ sơ **tạo mới**; mã đã cấp không đổi.
- **Mốc kỷ niệm ngày vào làm** (mặc định 1, 3, 5, 10 năm): các mốc được nhắc trong lời nhắc hằng tháng.
- **Báo hợp đồng lao động sắp hết hạn**: báo trước **N ngày** (mặc định 30) và mức **khẩn** khi còn ≤ **M ngày**
  (mặc định 15 — Bộ luật Lao động buộc báo người lao động ít nhất 15 ngày). Danh sách / báo cáo hợp đồng sắp hết hạn
  dùng đúng hai số này.
- Tab **Nghỉ phép** (chặn đơn lùi ngày, chặn tự duyệt, vai trò được duyệt qua ngày cấm nghỉ) — xem cẩm nang Nghỉ phép.

## Khóa tài khoản / cho nghỉ việc khi người đó còn việc duyệt treo (từ 22/10/2026)

Trước khi khóa tài khoản hay đưa hồ sơ sang **nghỉ việc**, hệ mở hộp ***kiểm việc đang giữ***. Có bốn lối vào:
lưu hồ sơ sang trạng thái nghỉ việc (hộp ***Lưu hồ sơ nghỉ việc?***), nút ***Khóa tài khoản + đăng xuất mọi thiết bị*** ở tab *Tài khoản*
của hồ sơ, biểu tượng ổ khóa ở danh sách tài khoản, và dòng ***Thôi việc*** ở tab *Quá trình công tác*.

- Hộp liệt kê **việc duyệt đang chờ người đó** (phiếu nào, bước nào, hạn, quá hạn chưa) và **bước luồng duyệt chỉ
  đích danh người đó** (phiếu mới sẽ lùi sang người dự phòng hoặc kẹt — nên đổi người ở luồng).
- Chuyển việc: chọn người nhận ở ô ***Chuyển cho…*** rồi bấm ***Chuyển*** từng việc hoặc ***Chuyển hết (N)***.
  Chỉ người có quyền ghi ***Luồng duyệt*** (quản trị luồng duyệt) mới chuyển được; không có quyền thì hộp nói
  *nhờ quản trị luồng chuyển giúp*.
- **Không chặn cứng**: còn việc treo vẫn khóa được, nhưng nút đổi thành ***Vẫn khóa … (còn việc treo)*** để người bấm
  biết phiếu sẽ kẹt. Chuyển hết rồi thì nút trở lại bình thường.
- Phiếu mà người xem hộp không có quyền đọc thì chỉ hiện ***(bạn không có quyền xem phiếu này)***, không lộ mã hay tên phiếu.
- Trợ lý không chuyển việc hộ; chỉ hướng dẫn các bước trên.

## In Phiếu thông tin nhân viên BM00../QT01/NS (từ 23/10/2026)

Nút ***In phiếu thông tin*** có ở hai chỗ:

- Phòng Nhân sự: màn chi tiết hồ sơ (**Nhân sự ▸ Nhân sự** ▸ mở một người), góc phải cạnh nút **Lưu**. Cần quyền
  xem hồ sơ nhân sự (`employee`) và hồ sơ nằm trong phạm vi. Trang in: `/print/employee-info/<id>`.
- Nhân viên tự in phiếu của mình: **Trang cá nhân ▸ Thông tin cá nhân**, nút ngay trên khối hồ sơ. Chỉ cần đăng
  nhập và tài khoản đã gắn hồ sơ. Trang in: `/print/my-employee-info`.

Phiếu A4 bảy mục: I. Thông tin cá nhân · II. Công việc · III. Liên hệ · IV. Ngân hàng · V. Giấy tờ và BHXH/BHYT ·
VI. Người báo tin khi cần thiết · VII. Thành viên hộ gia đình; cuối phiếu có ô ký **Người khai** và **Phòng Nhân sự**.
**Không có ô lương nào.** Bấm ***In phiếu / Lưu PDF*** để mở hộp in của trình duyệt. Ô hồ sơ chưa nhập in thành ô trống
để điền tay; hai bảng người luôn có tối thiểu ba dòng.

- ⚠️ Người in phiếu của **người khác** mà thiếu quyền xem thông tin nhạy cảm (`employee_sensitive`) thì ngày sinh,
  mã số thuế, địa chỉ, ngân hàng, CCCD, số sổ BHXH và hai bảng người báo tin / hộ gia đình **in trống** dù hồ sơ có dữ
  liệu (trang xem trước có dòng nhắc). Đừng nói "hồ sơ chưa khai"; nói là do thiếu quyền, nhờ người có quyền in hoặc
  để nhân viên tự in từ Trang cá nhân (phiếu của chính mình thì đủ mọi ô).

## Nhân viên tự đề nghị sửa hồ sơ, phòng Nhân sự duyệt (từ 23/10/2026)

Hai cách sửa hồ sơ của chính mình — trợ lý phải nói đúng cách cho đúng ô:

| Ô | Cách sửa |
|---|---|
| Số điện thoại (số chính và các số khác), địa chỉ thường trú, địa chỉ hiện nay, người báo tin | Tự sửa ở thẻ ***Liên hệ*** / bảng người báo tin trên Trang cá nhân, **lưu ngay**, không qua duyệt |
| Cá nhân (giới tính, ngày sinh, nơi sinh, dân tộc, tôn giáo, hôn nhân, số con, email cá nhân, học vấn, chuyên ngành) · Ngân hàng · Giấy tờ (CCCD, mã số thuế, số sổ BHXH, nơi KCB BHYT) · Hộ gia đình | **Gửi đề nghị**, phòng Nhân sự duyệt rồi mới vào hồ sơ |
| Họ tên, mã NV, phòng ban, chức vụ, quản lý trực tiếp, ngày vào làm… | Không tự đề nghị được — liên hệ phòng Nhân sự |

**Phía nhân viên** — **Trang cá nhân ▸ Thông tin cá nhân** ▸ thẻ ***Đề nghị sửa hồ sơ*** (dưới phần Liên hệ):

1. Bấm ***Đề nghị sửa thông tin*** → hộp bốn tab **Cá nhân · Ngân hàng · Giấy tờ · Hộ gia đình**, điền sẵn hồ sơ hiện tại.
2. Sửa ô cần đổi (đổi tab không mất chữ). Tab Hộ gia đình: danh sách gửi đi **thay cả danh sách cũ** khi được duyệt;
   dòng không có họ tên bị bỏ; tối đa 30 dòng. Ô **Số con** chỉ hiện khi hôn nhân là **Có gia đình**.
3. Ghi chú cho phòng Nhân sự (tối đa 500 ký tự) nếu cần, bấm ***Gửi đề nghị***. Chỉ ô đổi thật mới được gửi; không đổi
   gì thì báo ***Không có thay đổi nào để gửi***.

- **Mỗi lúc chỉ một đề nghị chờ duyệt**: nút gửi mờ đi. Muốn sửa thêm thì ***Rút đề nghị*** rồi gửi lại đề nghị mới đủ ô.
- Thẻ hiện đề nghị gần nhất: trạng thái **Chờ duyệt / Đã duyệt / Từ chối / Đã rút lại**, từng ô cũ → mới, lý do từ chối.
- Duyệt xong hồ sơ cập nhật ngay; duyệt hay từ chối đều có thông báo chuông (**Yêu cầu sửa hồ sơ đã được duyệt** /
  **Yêu cầu sửa hồ sơ bị từ chối**), từ chối kèm lý do người duyệt viết.

**Phía phòng Nhân sự** — menu **Nhân sự ▸ *Duyệt sửa hồ sơ*** (`/hr/profile-change-requests`, con số cạnh
menu = số đang chờ trong phạm vi). Cần quyền **ghi** hồ sơ nhân sự (`employee.write`), chỉ thấy đề nghị của người trong
phạm vi được sửa. Danh sách mặc định lọc **Chờ duyệt**, tìm theo mã / tên. Hồ sơ đang có đề nghị chờ thì màn chi tiết nhân
sự hiện dải nhắc kèm liên kết ***Xem đề nghị***.

- Màn chi tiết: mỗi nhóm một bảng **Trường · Lúc gửi · Hiện tại · Đề nghị**. Dòng tô màu nhãn ***Đã đổi sau khi gửi*** =
  hồ sơ bị sửa sau lúc nhân viên gửi; duyệt sẽ **ghi đè** giá trị hiện tại. Hộ gia đình: hai bảng **Lúc gửi** / **Đề nghị**.
- ***Duyệt*** → ghi cột Đề nghị vào hồ sơ ngay. ***Từ chối*** → bắt buộc nhập lý do (≤ 500 ký tự), hồ sơ giữ nguyên,
  nhân viên đọc được lý do.
- ⚠️ **Không tự duyệt đề nghị của chính mình** (trừ quản trị hệ thống) — hai nút ẩn, màn nói cần người khác duyệt.
- ⚠️ Đề nghị đụng **ngân hàng, giấy tờ, hộ gia đình hoặc ngày sinh** thì người duyệt phải có thêm quyền xem thông tin
  nhạy cảm (`employee_sensitive`); thiếu thì giá trị hiện **Đã ẩn (cần quyền xem thông tin nhạy cảm)** và không duyệt được.
- Trợ lý **không** gửi, rút, duyệt hay từ chối đề nghị hộ, và không đọc giá trị trong đề nghị ra; chỉ chỉ đường tới màn.
