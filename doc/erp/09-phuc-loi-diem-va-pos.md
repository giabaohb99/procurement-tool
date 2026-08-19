# PHÚC LỢI ĐIỂM VÀ ĐẦU NỐI POS — QUÁN CAFE

| | |
|---|---|
| Bản | **1.0 — 12/08/2026** |
| Đối tượng đọc | Ban lãnh đạo · Người chủ trì · Đội phần mềm · Phòng Nhân sự · Kế toán |
| Trả lời câu hỏi | Mỗi tháng cấp cho nhân sự một số điểm theo chức danh, tiêu ở quán cafe của công ty, làm bằng cách nào; và nối với POS365 đang dùng tới đâu |
| Chưa có trong bản này | Số người-ngày, ngày giao cam kết, mức điểm cụ thể của từng chức danh (nghiệp vụ quyết, không phải đội phần mềm) |
| Liên quan | [`01` Ngắn hạn](./01-ngan-han-2026.md) bước 4 và bước 5 · [`02` Dài hạn](./02-dai-han.md) · [`04` Danh mục chờ quyết](./04-danh-muc-cho.md) C4 · [`07` Kiến trúc vỏ ERP](./07-kien-truc-vo-erp.md) mục 5 |

**Ba câu tóm tắt.** Việc này gồm **hai phần tách rời nhau**: một là **chính sách điểm** nằm trong HRM (ai được bao nhiêu điểm mỗi tháng, ai duyệt, tiêu tới đâu, nghỉ việc thì sao) — phần này tự chủ hoàn toàn; hai là **đầu nối POS365** để nhân viên quẹt điểm ngay tại quầy — phần này phụ thuộc vào việc POS365 có cho ghi điểm qua API hay không, mà **hôm nay chưa ai kiểm chứng**. Vì vậy việc đầu tiên không phải viết code, mà là **hai ngày gọi thử API POS365** để biết mình đang đứng ở ngã rẽ nào.

Và một câu nữa, nói trước để không hiểu nhầm: **không tự viết phần mềm POS cho quán trong năm 2026.** Lý do và điều kiện mở cổng ở mục 12.

---

## 1. Hai phần, và vì sao phải tách

| | Phần A — Chính sách điểm (HRM) | Phần B — Đầu nối POS365 |
|---|---|---|
| Làm gì | Khai mức điểm theo chức danh, chạy cấp phát hằng tháng, giữ sổ điểm, báo cáo, bàn giao số cho kế toán | Đẩy điểm sang POS365 để quầy tiêu được, kéo giao dịch tiêu điểm về, đối chiếu |
| Phụ thuộc bên ngoài | Không. Chỉ phụ thuộc HRM có danh mục chức danh | **Có.** Phụ thuộc năng lực API của POS365 |
| Nếu bên kia không cho ghi | Vẫn chạy được | Đổi thiết kế, xem mục 3 |
| Rủi ro lớn nhất | Quy tắc nghiệp vụ chưa chốt (mục 7) | Hai hệ cùng giữ một con số tiền, lệch nhau âm thầm |

Trộn hai phần này vào một là cách chắc chắn nhất để cả hai cùng đứng: phần A bị treo vì chờ câu trả lời của POS365, còn phần B bị viết dựa trên quy tắc nghiệp vụ đoán mò.

---

## 2. Quyết định lớn nhất: ai giữ số dư điểm

Điểm là tiền. Hai hệ thống cùng giữ một con số tiền mà không ai là nguồn đúng thì sớm muộn cũng lệch, và lúc lệch không ai chứng minh được bên nào sai.

| | P1 — POS365 giữ | P2 — ERP giữ sổ, POS365 giữ số dư quầy | P3 — ERP giữ tất, POS365 chỉ tra cứu |
|---|---|---|---|
| Nguồn đúng của **số dư** | POS365 | POS365 (số dư), ERP (sổ) | ERP |
| Nguồn đúng của **cấp phát** | ERP | ERP | ERP |
| Nguồn đúng của **tiêu dùng** | POS365 | POS365 | ERP, nhận từ POS365 |
| Quầy làm gì | Như hôm nay, không đổi | Như hôm nay, không đổi | **Thu ngân phải mở thêm một màn hình của ERP** |
| Trả lời được câu "tháng 7 anh A được cấp bao nhiêu, tiêu gì" | Không đầy đủ | **Có** | Có |
| Điểm có hạn dùng theo lô | Không làm được | Làm được, nhưng phải đẩy bút trừ | Làm được |
| Việc phải làm | Ít nhất | Vừa | Nhiều nhất, và đổi thói quen của quán |

**Khuyến nghị: P2.** ERP giữ **sổ cái điểm** — mỗi dòng là một lần cộng hoặc trừ, có lý do, có người, có kỳ, không sửa được. POS365 giữ **số dư để quầy trừ**, vì màn hình thu ngân là màn hình của POS365 và không nên bắt quán đổi cách làm việc.

Kèm theo P2 là ba quy tắc cứng, viết ra đây để về sau không ai phá:

1. **Một chiều ghi cho mỗi loại nghiệp vụ.** ERP ghi **cộng** (cấp phát, điều chỉnh, thu hồi). POS365 ghi **trừ** (tiêu tại quầy). Không có ngoại lệ nào ngoài mục 3 (điều chỉnh sau đối chiếu), và ngoại lệ đó phải có người bấm nút, có nhật ký.
2. **ERP không bao giờ ghi đè số dư tuyệt đối** trong lúc chạy tự động. Chỉ ghi **chênh lệch**. Ghi đè là cách xóa mất phần vừa tiêu ở quầy mà chưa kéo về.
3. **Đối chiếu mỗi ngày, không tự sửa.** Lệch thì lên màn hình cho người xử lý — đúng nguyên tắc WH17 ở [`01` mục 8.3](./01-ngan-han-2026.md): có màn hình đối chiếu lệch trước, mới cho ghi hai chiều.

---

## 3. Giai đoạn 0 — Kiểm chứng API POS365 (làm ngay, không chờ ai)

**Đây là việc phải làm trước tiên, và nó không phải việc lập trình — nó là việc gọi thử và ghi lại kết quả.** Cỡ hai ngày công. Không phụ thuộc HRM, không phụ thuộc lộ trình ERP, không chờ duyệt gì.

### 3.1 Cái đã biết, đọc từ ảnh chụp Postman ngày 12/08/2026

| Đã biết | Nội dung |
|---|---|
| Có endpoint đọc khách hàng | `GET https://mykythuyda.pos365.vn/api/autocomplete/partners?Keyword=...&Type=1&format=json&BranchId=283275` — trả 200, khoảng 30 ms |
| Trường trả về | `Id` · `Code` (KH-0002) · `Name` · `Phone` · `Type` · `Gender` · `TotalDebt` · `Loyalty` · `CreatedBy` · `CreatedDate` · `ModifiedBy` · `ModifiedDate` · `RetailerId` · `Password` · `Point` · `TransactionValue` · `PartnerGroupMembers` |
| Có sẵn khái niệm điểm | Bản ghi mẫu có `Point: 10989` |
| Có phân chi nhánh và gian hàng | `BranchId=283275`, `RetailerId=225873` |
| Tra được bằng số điện thoại | Ảnh trên cùng dùng `Keyword=0968840860` |

**Ba điều ảnh chụp này chưa chứng minh, và đừng suy ra:**

- Nó **không** chứng minh có API **ghi** điểm. Đọc được không có nghĩa là ghi được.
- Nó **không** chứng minh cách xác thực dùng được cho máy chạy nền. Ảnh chụp có `Cookies (3)`, tức nhiều khả năng đang đi bằng **phiên đăng nhập của người**. Một tác vụ hẹn giờ mà đi bằng cookie của một tài khoản người là thứ sẽ chết im lặng vào ngày người đó đổi mật khẩu.
- Nó **không** cho biết `Point` và `Loyalty` khác nhau thế nào. Hai trường cùng tồn tại, một cái 10989, một cái 0. Tiêu ở quầy là trừ vào cái nào — chưa biết.

### 3.2 Chín câu phải trả lời bằng kết quả gọi thật

Mỗi câu trả lời phải kèm **một lần gọi thành công có lưu lại**, không phải câu trả lời từ trí nhớ hay từ nhân viên hỗ trợ nói miệng.

| # | Câu hỏi | Vì sao nó quyết định thiết kế |
|---|---|---|
| K1 | Có tài liệu API chính thức và **khóa/token cấp cho máy** không, hay chỉ có phiên đăng nhập của người | Không có token máy thì không có tự động hóa. Đây là câu chặn tất cả các câu còn lại |
| K2 | Có endpoint **ghi điểm** cho một khách hàng không: cộng, trừ, hay đặt lại | Không có thì P2 sập, xem mục 3.3 |
| K3 | `Point` hay `Loyalty` mới là số dư quầy trừ khi thanh toán | Đẩy nhầm trường là cấp điểm vào một chỗ không ai tiêu được |
| K4 | Ghi điểm có nhận **mã tham chiếu của bên gọi** để chống ghi trùng không | Không có thì mỗi lần gọi lại sau lỗi mạng là nguy cơ cấp đôi. Phải thay bằng đọc lại số dư trước khi thử lại |
| K5 | Kéo được **giao dịch tiêu điểm** theo khoảng thời gian và theo khách hàng không, có phân trang không | Không kéo được thì không đối chiếu được, và không có báo cáo tiêu dùng |
| K6 | POS365 có **bắn webhook ra** khi có hóa đơn không | Có thì đối chiếu gần thời gian thực. Không thì chạy hẹn giờ, chấp nhận trễ |
| K7 | Có **chi nhánh thử** hoặc môi trường thử không | Không có thì mọi phép thử đều chạy trên quán thật, và mục 8 thành bắt buộc tuyệt đối |
| K8 | Giới hạn số lần gọi, số bản ghi mỗi trang | Quyết định cách chạy: đẩy cả trăm người một lượt hay rải |
| K9 | Đọc/ghi được **sản phẩm** (menu quán) không, chiều nào | Quyết định phần đồng bộ sản phẩm ở mục 6 |

Kèm một câu về an toàn, phát hiện khi đọc ảnh chụp: **phản hồi có trường `Password`.** Ở bản ghi mẫu nó rỗng, nhưng phải kiểm xem có bản ghi nào trả ra giá trị thật không. Nếu có, thì mọi tài khoản đọc được danh sách khách hàng đang đọc được cả thứ đó, và phần lưu trữ dữ liệu kéo về của mình phải loại bỏ trường này ngay từ đầu vào, không lưu, không ghi nhật ký.

### 3.3 Ba ngã rẽ, chốt sau khi trả lời xong

| Kết quả K1 và K2 | Đi đường nào |
|---|---|
| Có token máy, có API ghi điểm | **P2 như mục 2.** Toàn bộ kế hoạch dưới đây giữ nguyên |
| Có token máy, **không** có API ghi điểm | Đổi sang **P3**: ERP giữ tất, quầy tra cứu số dư trên một trang web nhỏ của ERP (tra bằng số điện thoại), thu ngân nhập số tiền trừ vào đó rồi thu phần còn lại trên POS365. Xấu hơn cho quầy, nhưng chạy được, và không lệ thuộc bên ngoài |
| **Không** có token máy | Không tự động hóa gì cả trong bản 1. Chạy **phương án 0** ở mục 9: cấp phát bằng tay mỗi tháng. Đồng thời hỏi POS365 về gói có API, vì đây là điều kiện của mọi thứ còn lại |

**Không viết một dòng code nào của phần B trước khi bảng này được điền.**

---

## 4. Dữ liệu: bảng mới và chỗ đứng trong ERP

Theo [`07` mục 5](./07-kien-truc-vo-erp.md), **mọi entity phải thuộc đúng một phân hệ, thiếu thì ứng dụng không khởi động được.** Việc này thêm bảy entity và một phân hệ.

| Entity | Phân hệ | Nội dung |
|---|---|---|
| `point_policy` | `nhan_su` | Chính sách: chức danh nào, pháp nhân nào, mỗi tháng bao nhiêu điểm, hiệu lực từ ngày nào |
| `point_grant` | `nhan_su` | Đợt cấp phát của một kỳ: kỳ nào, bao nhiêu người, tổng bao nhiêu điểm, ai duyệt, trạng thái |
| `point_ledger` | `nhan_su` | **Sổ cái điểm.** Mỗi dòng: nhân sự, kỳ, loại (cấp / thu hồi / điều chỉnh / tiêu), số điểm, lý do, chứng từ gốc, thời điểm. **Chỉ thêm dòng, không sửa, không xóa** |
| `pos_partner_map` | `ban_le` | Ánh xạ nhân sự ↔ khách hàng POS365: `employee_id`, `pos_partner_id`, chi nhánh, ai ghép, ghép lúc nào |
| `pos_outlet` | `ban_le` | Điểm bán: mã chi nhánh và gian hàng POS365, thuộc pháp nhân nào |
| `pos_product` | `ban_le` | Bản sao menu quán kéo về, chỉ đọc |
| `pos_sync_run` | `ban_le` | Mỗi lần chạy đồng bộ: chạy lúc nào, đẩy/kéo bao nhiêu dòng, lỗi gì, ai bấm |

**Phân hệ mới `ban_le` — "Bán lẻ và quán".** Ô thứ chín trên lưới biểu tượng, chỉ hiện với người có quyền. Bảng chia entity ở [`07` mục 5](./07-kien-truc-vo-erp.md) phải thêm một dòng, và tổng số entity đi từ 28 lên 35.

Năm ràng buộc bắt buộc, tất cả đều là quy tắc đã có sẵn của bộ tài liệu chứ không phải quy tắc mới:

| # | Ràng buộc | Vì sao |
|---|---|---|
| 1 | **Cả bảy entity phải khai phạm vi dữ liệu ngay khi tạo bảng** (`SCOPE_FIELDS`), không để sau | Đúng tinh thần PQ4/PQ5. Nhân viên chỉ được thấy sổ điểm **của mình**; hiện đã có 19 entity thiếu khai, không thêm cái thứ 20 |
| 2 | **Quyền và phạm vi khai trong `seed.py`**, không sửa tay trên cơ sở dữ liệu | Cơ sở dữ liệu là nguồn sự thật lúc chạy, nhưng khai báo phải nằm trong mã nguồn để môi trường mới dựng lại được |
| 3 | **Trạng thái lưu bằng số theo enum khai ở `core/enums.py`** (DB3, DB14), không lưu chuỗi tiếng Việt | Bảng mới thì không có lý do gì lặp lại nợ cũ |
| 4 | **Mọi bảng có cột pháp nhân** ngay từ migration đầu (DB10, DB12) | Quán cafe rất có thể thuộc một pháp nhân khác với công ty mẹ. Thêm sau là phải trả lời "dòng cũ thuộc pháp nhân nào" mà không còn dữ liệu để trả lời |
| 5 | **`pos_product` không được đụng vào `tab_product`**, và **không thêm cột giá vào bảng sản phẩm** | Quy tắc mô hình sản phẩm D-025. Menu quán là dữ liệu của POS365, giá đổi theo ngày; để nó ở bảng riêng, chỉ đọc |

Và một ràng buộc riêng của việc này: **`point_ledger` chỉ ghi thêm.** Sửa sai bằng một dòng đảo ngược, không bằng cách sửa dòng cũ. Sổ tiền mà sửa được thì không còn là sổ.

---

## 5. Phần A — Chính sách điểm trong HRM

| Mã | Việc | Xong là thế nào |
|---|---|---|
| **PL1** | **Danh mục chính sách điểm**: theo chức danh, theo pháp nhân, có ngày hiệu lực. Sửa trên giao diện, không sửa code | Đổi mức điểm của một chức danh không cần lập trình viên, và tra được mức của tháng trước |
| **PL2** | **Sổ cái điểm** `point_ledger` — chỉ thêm dòng. Mọi thay đổi số dư đều đi qua đây, kể cả phần kéo về từ POS365 | Cộng tất cả dòng của một người ra đúng số dư của người đó |
| **PL3** | **Chạy cấp phát theo kỳ**: chọn kỳ, hệ sinh bảng dự kiến (ai, chức danh nào, bao nhiêu điểm), người phụ trách xem trước rồi mới chốt | Bảng dự kiến xem được trước khi cấp, không phải cấp xong mới biết |
| **PL4** | **Duyệt bảng cấp phát** qua bộ máy duyệt dùng chung (DUY1–DUY6), không viết luồng duyệt riêng | Đây là chứng từ cấp phát tiền — không có ai duyệt thì không được cấp |
| **PL5** | **Chống cấp trùng**: một nhân sự trong một kỳ chỉ có đúng một dòng cấp phát, ràng buộc ở tầng cơ sở dữ liệu | Chạy lại đợt cấp phát của cùng một kỳ **không** làm điểm nhân đôi |
| **PL6** | **Vào và ra**: người mới vào trong tháng, người nghỉ việc, người đổi chức danh giữa tháng — quy tắc lấy từ mục 7, đọc từ quá trình công tác (HR2) | Người nghỉ việc **tự động bị thu hồi số dư**, không phải nhớ mà làm tay |
| **PL7** | **Màn hình của nhân viên**: số dư của tôi, tháng này được cấp bao nhiêu, đã tiêu gì. Nằm trong phần tự phục vụ HR9 | Nhân viên tự tra, phòng Nhân sự không phải trả lời từng người |
| **PL8** | **Điều chỉnh tay có lý do bắt buộc** — cộng bù, trừ nhầm, thu hồi. Có quyền riêng, có nhật ký | Không có đường nào đổi số dư mà không để lại dấu vết |
| **PL9** | **Báo cáo**: tổng cấp phát theo tháng, theo phòng ban, theo pháp nhân; tỷ lệ sử dụng; số dư còn tồn | Kế toán nhận được một con số mỗi tháng, không phải tự cộng |
| **PL10** | **Bàn giao cho kế toán**: chốt số cuối kỳ, xuất tệp theo mẫu kế toán yêu cầu | Kế toán ký nhận được, không phải hỏi lại |

**PL1 đến PL5 là phần lõi.** Bỏ PL4 hoặc PL5 thì có một cỗ máy phát tiền không ai duyệt và có thể chạy hai lần.

---

## 6. Phần B — Đầu nối POS365

| Mã | Việc | Xong là thế nào |
|---|---|---|
| **PS1** | **Cấu hình kết nối**: địa chỉ, token, chi nhánh, gian hàng. Token **không nằm trong mã nguồn**, lưu ở biến môi trường hoặc bảng cấu hình có mã hóa | Đổi token không cần dựng lại phần mềm, và token không nằm trong lịch sử mã nguồn |
| **PS2** | **Ghép nhân sự với khách hàng POS365** — tra theo số điện thoại, **người xác nhận từng cặp**, lưu `pos_partner_id` làm khóa ràng buộc | Ghép xong thì mọi lần sau đi theo `pos_partner_id`, **không bao giờ tra lại theo tên hay số điện thoại** |
| **PS3** | **Tạo khách hàng mới trên POS365** cho nhân sự chưa có, đặt nhóm khách hàng riêng để phân biệt với khách vãng lai | Nhân viên mới vào là quẹt được ngay, không phải nhờ quầy tạo tay |
| **PS4** | **Đẩy điểm**: mỗi dòng cấp phát đã duyệt thành một lần cộng điểm, ghi lại mã tham chiếu và phản hồi | Đẩy hỏng giữa chừng, chạy lại thì **chỉ đẩy phần chưa đẩy** |
| **PS5** | **Kéo giao dịch tiêu điểm** theo kỳ, ghi vào sổ cái dưới dạng dòng "tiêu" | Số dư trong ERP và số dư ở POS365 nói cùng một câu chuyện |
| **PS6** | **Đối chiếu hằng ngày**: so số dư từng người hai bên, lệch thì lên màn hình. **Không tự sửa** | Có màn hình danh sách lệch, có nút xử lý từng dòng, mỗi lần xử lý sinh một dòng điều chỉnh trong sổ |
| **PS7** | **Nhật ký đồng bộ** `pos_sync_run`: chạy lúc nào, bao nhiêu dòng, lỗi gì, nội dung gửi và nhận | Quán kêu thiếu điểm là tra ra trong một phút |
| **PS8** | **Đồng bộ menu quán** một chiều POS365 → ERP, chỉ đọc, phục vụ báo cáo "điểm tiêu vào món gì" | Báo cáo tiêu dùng có tên món, không phải mã số |
| **PS9** | **Hàng đợi và thử lại** dùng Celery đang chạy sẵn, hàng đợi riêng, giãn cách như WH6 | POS365 sập nửa ngày thì điểm vẫn tới nơi khi họ sống lại |
| **PS10** | **Cảnh báo**: đồng bộ hỏng liên tiếp, hoặc lệch vượt ngưỡng, thì báo người phụ trách | Không có lần đồng bộ nào chết im lặng |
| **PS11** | **Chốt an toàn môi trường** — xem mục 8. Môi trường dev **mặc định không đẩy gì** ra POS365 thật | Dev chạy thử cả ngày cũng không cộng cho ai một điểm nào ở quán thật |
| **PS12** | **Phân quyền phân hệ Bán lẻ**: ai xem được sổ điểm người khác, ai bấm đẩy, ai điều chỉnh | Quyền đẩy điểm và quyền điều chỉnh là hai quyền riêng, không gộp |

**PS4 và PS6 là cặp không tách được.** Có đẩy mà không có đối chiếu thì lệch sẽ tích lại và một ngày nào đó không ai lần ngược được nữa.

**Quan hệ với module webhook ở [`01` bước 5](./01-ngan-han-2026.md):** phần này **không phải** webhook đi ra — nó là **gọi API bên ngoài theo lịch**, tức là phần WH16 vốn đang xếp "để sang năm". Nhưng nó dùng lại đúng bốn thứ của bước 5: hàng đợi (HT4), thử lại có giãn cách (WH6), nhật ký gửi (WH8), cảnh báo hàng chờ chết (WH9). Làm PS9 và PS10 mà không mượn được bốn thứ đó là viết lại lần thứ hai.

**Việc này trả lời câu C4 trong [`04`](./04-danh-muc-cho.md)** — "tích hợp ra ngoài đầu tiên là với hệ thống nào". Nếu được duyệt thì C4 chốt: **POS365, một chiều đẩy điểm và một chiều kéo giao dịch, ERP là nguồn đúng của cấp phát, POS365 là nguồn đúng của tiêu dùng.** Đây là ca dùng thật nằm trong nhà, không phải chờ đối tác bên ngoài — đúng loại ca dùng mà `04` C4 gọi là ứng viên tốt.

---

## 7. Mười câu nghiệp vụ phải chốt trước

Không có câu trả lời cho những câu này thì viết code là viết mò. Đề nghị đưa thành **C16** trong [`04` Danh mục chờ quyết](./04-danh-muc-cho.md), người quyết là Ban lãnh đạo cùng phòng Nhân sự, chốt **trước khi bắt đầu PL1**.

| # | Câu hỏi | Mặc định nếu quá hạn | Hệ quả kỹ thuật |
|---|---|---|---|
| N1 | Một điểm bằng bao nhiêu tiền | 1 điểm = 1 đồng | Quyết cách ghi sổ và cách bàn giao kế toán |
| N2 | Điểm **không tiêu hết có cộng dồn sang tháng sau không** | **Có cộng dồn** | Nếu **hết hạn** thì phải theo dõi điểm theo lô, mà số dư một con số của POS365 **không diễn tả được lô**. Chọn hết hạn là kéo theo bút trừ cuối kỳ và một lớp phức tạp đáng kể |
| N3 | Có trần số dư không | Không có trần | Có trần thì phải xử lý ca "cấp vượt trần thì cắt hay giữ" |
| N4 | Người vào giữa tháng: cấp đủ hay cấp theo ngày công | **Cấp đủ**, không chia theo ngày | Chia theo ngày thì phải có dữ liệu công, mà chấm công chưa chốt là có làm (C2) |
| N5 | Người nghỉ việc: số dư còn lại xử lý thế nào | **Thu hồi về 0 vào ngày nghỉ việc** | Không thu hồi là người đã nghỉ vẫn quẹt được. Đây là lỗ thật, không phải giả định |
| N6 | Nghỉ không lương, nghỉ thai sản, tạm hoãn hợp đồng: có cấp không | **Không cấp**, giữ nguyên số dư đang có | Cần đọc trạng thái lao động từ HR2 |
| N7 | Điểm chuyển nhượng được cho người khác không | **Không** | Cho phép thì số dư mất quan hệ với chính sách, báo cáo theo chức danh vô nghĩa |
| N8 | Điểm dùng được ở đâu — chỉ quán cafe, hay còn chỗ khác | **Chỉ quán cafe** | Nhiều nơi thì phải có khái niệm ví theo điểm bán, khác thiết kế |
| N9 | Ai duyệt bảng cấp phát hằng tháng, và ai được điều chỉnh tay | Trưởng phòng Nhân sự duyệt, chỉ hai tài khoản được điều chỉnh | Quyết cấu hình luồng duyệt PL4 và quyền PL8 |
| N10 | **Phúc lợi này có phải tính thuế thu nhập cá nhân không** | Chưa có mặc định — **phải hỏi kế toán, đội phần mềm không tự trả lời câu này** | Nếu có, thì phần bàn giao PL10 phải xuất theo từng người theo tháng, không phải tổng gộp |

N2, N5 và N10 là ba câu đắt nhất. N2 đổi cả mô hình dữ liệu, N5 là một lỗ hổng tiền thật, N10 là nghĩa vụ pháp lý mà phần mềm không có quyền tự chọn.

---

## 8. An toàn — bốn chỗ hỏng thì mất tiền thật

| # | Chỗ | Xử lý |
|---|---|---|
| **A1** | **Dev đẩy điểm vào quán thật.** Hệ đang có hai môi trường dùng chung một máy chủ cơ sở dữ liệu, và đã từng phải cách ly bằng cờ tắt cứng cho thư điện tử | Làm lại đúng khuôn đó: **`POS365_HARD_OFF` bật mặc định ở mọi môi trường không phải bản chạy thật**. Bật được chỉ khi đã có chi nhánh thử (K7). Đây không phải khuyến nghị, đây là điều kiện của PS4 |
| **A2** | **Cấp trùng khi chạy lại.** Mạng lỗi giữa chừng, người chạy lại, mỗi người được hai lần điểm | Hai lớp: ràng buộc duy nhất theo (nhân sự, kỳ) ở cơ sở dữ liệu (PL5), và mã tham chiếu ở mỗi lần đẩy (PS4). Nếu K4 trả lời là POS365 không nhận mã tham chiếu, thì **bắt buộc đọc lại số dư trước khi thử lại**, không thử lại mù |
| **A3** | **Ghép nhầm người.** Số điện thoại trùng, số điện thoại rỗng, hoặc nhân sự dùng chung một số | Ghép **một lần, có người xác nhận**, khóa bằng `pos_partner_id`. **Không bao giờ tự ghép lại theo tên hoặc số điện thoại về sau.** Đây đúng bài học đã trả giá khi đồng bộ thư điện tử nhân sự sang tài khoản đăng nhập: chỉ khớp khi thật sự chắc, còn lại để người quyết |
| **A4** | **Token POS365 lộ.** Ai có token là đọc được toàn bộ khách hàng của quán và có thể cộng điểm cho chính mình | Token chỉ nằm ở biến môi trường của bản chạy thật, không vào mã nguồn, không vào tệp cấu hình chung. Quyền bấm đẩy điểm tách riêng khỏi quyền xem (PS12). Mọi lần đẩy có nhật ký người bấm |

---

## 9. Phương án 0 — chạy tay tháng đầu

Nói thẳng: nếu quán chỉ phục vụ vài chục người, thì **cấp phát bằng tay mỗi tháng mất khoảng nửa giờ**, còn phần mềm hóa mất vài tuần công. Phần mềm chỉ có lãi khi có ít nhất một trong ba thứ: số người đủ lớn, biến động nhân sự đủ nhiều, hoặc cần báo cáo và đối chiếu mà làm tay không nổi.

**Đề nghị: tháng đầu tiên chạy tay, dù có duyệt kế hoạch này hay không.** Một bảng tính có cột chức danh và mức điểm, cộng tay vào POS365 theo danh sách. Lý do không phải để tiết kiệm — mà vì tháng chạy tay đầu tiên là **cách rẻ nhất để tìm ra mười câu ở mục 7 đã trả lời đúng chưa**. Sai trong bảng tính thì sửa ô. Sai trong phần mềm đã đẩy điểm thì phải đi thu hồi.

Điều kiện để chuyển sang làm phần mềm: một tháng chạy tay xong, mười câu ở mục 7 đã có câu trả lời bằng văn bản, và giai đoạn 0 đã trả lời xong chín câu ở mục 3.2.

---

## 10. Phụ thuộc và chỗ đứng trong lịch

| Phải xong trước | Mới làm được | Vì sao |
|---|---|---|
| Giai đoạn 0 (mục 3) | **Toàn bộ phần B** | Chưa biết POS365 cho làm gì thì thiết kế nào cũng có thể sai hết |
| Mười câu ở mục 7 | **PL1** | Mức điểm theo chức danh mà chưa có quy tắc vào/ra thì bảng chính sách thiếu cột |
| **HR5** danh mục chức danh | PL1 | Chính sách theo chức danh mà chưa có danh mục chức danh thì không khai được. Hiện chức danh **chưa có trong hệ thống** |
| **HR1, HR2** hồ sơ và quá trình công tác | PL6 | Vào giữa tháng, đổi chức danh, nghỉ việc đều đọc từ quá trình công tác |
| **DUY1–DUY6** bộ máy duyệt chung | PL4 | Không thì sinh luồng duyệt viết tay thứ hai |
| **DB10, DB12** cột pháp nhân | Cả bảy bảng mới | Thêm sau là không trả lời được "dòng cũ thuộc pháp nhân nào" |
| **PQ4, PQ5** phạm vi dữ liệu | PL7, PS12 | "Nhân viên chỉ thấy sổ điểm của mình" là một phép áp phạm vi. Nền chưa vá thì câu đó không có hiệu lực thật |
| **HT4** hàng đợi | PS9, PS10 | Không hàng đợi thì không thử lại được |

**Chỗ đứng trong lịch của [`01` mục 10](./01-ngan-han-2026.md):**

| Khi nào | Làm gì |
|---|---|
| **Ngay bây giờ** | **Giai đoạn 0** — chín câu ở mục 3.2. Hai ngày công, không phụ thuộc gì. Song song: trình mười câu ở mục 7 để chốt |
| **T9 đến T10** | Không làm gì. Nền chưa xong, chức danh chưa có |
| **Tháng đầu sau khi chốt chính sách** | **Phương án 0** — chạy tay, kiểm chứng quy tắc |
| **Nửa sau T11**, ngay sau HR1–HR6 | PL1, PL2, PL3, PL5 |
| **Nửa đầu T12** | PL4, PL6, PL7. PS1, PS2, PS3 |
| **Nửa sau T12** | PS4, PS5, PS6, PS7, PS11, PS12. PL8 |
| **Sang năm** | PL9, PL10, PS8, PS9, PS10, và mục 12 |

**Nói trước một điều về lịch này, để không hứa nhầm:** nửa sau T12 trong [`01`](./01-ngan-han-2026.md) **đã đầy** — WH12, WH13, WH15, LC4, HR13, HT6, HT7, HT12, DB6. Thêm phần B vào đó là **thêm việc chứ không phải xếp việc**, và [`04` C15](./04-danh-muc-cho.md) — nhân lực làm lộ trình — vẫn chưa có câu trả lời. Cách trung thực để đọc bảng trên: đây là **thứ tự**, và nếu không có thêm người thì phần B rơi sang năm 2027, còn phần A chạy tay theo mục 9 trong lúc chờ. Đổi thứ tự ưu tiên là quyền của người chủ trì, nhưng phải là một quyết định nói ra, không phải một chỗ trượt lịch âm thầm.

---

## 11. Xong là thế nào

Kiểm được, không phải nhận xét.

**Phần A:**

1. Đổi mức điểm của một chức danh trên giao diện, chạy lại đợt cấp phát của kỳ sau: số mới có hiệu lực, số kỳ trước **không đổi**.
2. Chạy đợt cấp phát của cùng một kỳ **hai lần**: số dư không đổi sau lần thứ hai.
3. Cho một nhân sự nghỉ việc trong hệ thống: số dư của người đó **về 0**, và sổ có một dòng thu hồi ghi rõ lý do.
4. Một nhân viên đăng nhập: thấy đúng sổ điểm **của mình**, và **không** mở được sổ của người khác kể cả khi gõ thẳng địa chỉ.
5. Cộng toàn bộ dòng trong sổ của một người ra đúng số dư đang hiển thị.

**Phần B:**

6. Đẩy một đợt cấp phát, **rút mạng giữa chừng**, chạy lại: tổng điểm ở POS365 đúng bằng tổng đã duyệt, không hơn.
7. Quầy trừ điểm của một người: sau lần kéo dữ liệu kế tiếp, sổ trong ERP có dòng tiêu tương ứng.
8. Cố ý sửa lệch số dư ở một bên: sáng hôm sau người đó **có trên màn hình đối chiếu**, và hệ **không tự sửa**.
9. Chạy toàn bộ ở môi trường dev với `POS365_HARD_OFF` bật: **không một lời gọi nào ra POS365 thật**, kiểm bằng nhật ký.
10. Tra một lần đồng bộ bất kỳ trong nhật ký: biết ai bấm, gửi gì, nhận về gì.

---

## 12. Tự viết POS cho quán — chưa làm, và điều kiện mở cổng

Việc này có trong đề bài, nên trả lời rõ: **không tự viết POS trong năm 2026.** Không phải vì khó về mặt màn hình bán hàng — màn hình bán hàng là phần dễ nhất — mà vì phần còn lại:

| Phần | Vì sao đắt |
|---|---|
| Chạy khi mất mạng | Quán không được ngừng bán vì mạng chập. Đây là phần khó nhất của mọi POS, và nó quyết định kiến trúc từ đầu chứ không thêm sau được |
| In bill, két tiền, máy quét | Phần cứng thật, mỗi loại một cách nói chuyện |
| **Hóa đơn điện tử và thuế** | Theo quy định nhà nước, đổi theo văn bản pháp luật. Đúng loại rủi ro mà [`02` mục 5](./02-dai-han.md) đã kết luận là **nối chứ không tự viết** |
| Ca kíp, chốt ca, kiểm quỹ | Nghiệp vụ tiền mặt, sai là mất tiền và mất lòng tin giữa người với người |
| Trừ kho theo định lượng pha chế | Cần định mức nguyên vật liệu — chính là BOM của vòng 2, chưa có |

Và một lý do về giá trị: POS365 đang chạy, quán đang bán được. Tự viết lại để **bằng** cái đang có là bỏ vài tháng công đổi lấy con số không.

**Điều kiện mở cổng — khi nào bàn lại:** khi có **ít nhất hai** trong bốn điều sau. Ghi ra để lần bàn sau không bàn bằng cảm tính.

1. POS365 **không cho** làm điều mình cần (giai đoạn 0 trả lời là không), và phương án P3 chạy một thời gian thì quầy kêu không chịu nổi.
2. Số điểm bán đủ nhiều để chi phí thuê ngoài vượt chi phí tự làm.
3. Vòng 2 (MFM) đã chạy thật, tức đã có định mức và sổ kho đủ chặt để POS trừ kho có nghĩa.
4. Có nhu cầu bán ra ngoài thật sự, tức chuyển sang phạm vi CRM ở vòng 4 — mà [`02` mục 9](./02-dai-han.md) đang ghi rõ là **ngoài lộ trình**.

Trong lúc đó, cái nên làm là **phân hệ `ban_le` chỉ có phần đọc**: menu, doanh thu, giao dịch điểm kéo về từ POS365, và báo cáo. Không bán hàng trong đó. Như vậy ô "Bán lẻ" vẫn có mặt trên lưới biểu tượng, có nội dung thật, mà không gánh nghĩa vụ của một phần mềm bán hàng.

---

## 13. Cái này không làm

| Không làm | Vì sao |
|---|---|
| Tự viết POS cho quán trong 2026 | Mục 12 |
| Đồng bộ **hai chiều** số dư điểm | Mỗi loại nghiệp vụ chỉ có một bên được ghi (mục 2). Hai chiều mà chưa có WH17, WH18 là hỏng dữ liệu cả hai bên |
| Đẩy sản phẩm từ ERP sang POS365 | Menu quán đổi theo ngày và không nằm trong danh mục sản phẩm của ERP. Đẩy sang là dựng một tầng ánh xạ để phục vụ đúng con số không |
| Thêm cột giá vào bảng sản phẩm | Quy tắc D-025. Giá của POS365 nằm ở `pos_product` |
| Điểm hết hạn theo lô ở bản 1 | Số dư một con số của POS365 không diễn tả được lô. Làm được sau, khi ERP giữ sổ đủ lâu và đã đối chiếu ổn định — xem N2 |
| Điểm dùng ở nhiều nơi ngoài quán | N8. Mở phạm vi là đổi sang mô hình ví theo điểm bán |
| Ứng dụng di động cho nhân viên tra điểm | Web đã chạy trên điện thoại. PL7 nằm trong phần tự phục vụ HR9 |
| Cho nhân viên chuyển điểm cho nhau | N7 |

---

## 14. Việc này kéo theo gì ở tài liệu khác

Ghi ra để nếu kế hoạch được duyệt thì biết phải sửa những chỗ nào, không sót.

| Tài liệu | Sửa gì |
|---|---|
| [`07` mục 5](./07-kien-truc-vo-erp.md) | Thêm phân hệ **`ban_le`** và bảy entity mới vào bảng chia entity. Tổng entity **28 → 35**, tổng phân hệ **8 → 9** |
| [`01`](./01-ngan-han-2026.md) | Thêm nhóm **PL** vào bước 4 (HRM) và nhóm **PS** thành một nhánh của bước 5. Cập nhật lịch mục 10 theo mục 10 của tài liệu này |
| [`02`](./02-dai-han.md) | Mục 3: thêm phân hệ Bán lẻ ở mức đọc. Mục 9 "cái gì không nằm trong lộ trình": ghi rõ POS tự viết vẫn nằm ngoài, kèm điều kiện mở cổng ở mục 12 |
| [`04`](./04-danh-muc-cho.md) | Thêm **C16** — mười câu nghiệp vụ ở mục 7. Và ghi nhận **C4 có ứng viên mới**: POS365 |
| [`03`](./03-cau-hoi-khao-sat-hrm.md) | Thêm một câu vào phần phúc lợi: hiện đang cấp phúc lợi quán cafe theo cách nào, ai giữ danh sách, tháng vừa rồi cấp cho bao nhiêu người |

**Chưa sửa tài liệu nào trong bảng trên.** Sửa sau khi kế hoạch này được duyệt, để không phải sửa hai lần.
