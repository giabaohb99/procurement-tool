# Báo cáo thực hiện — khối trên chi tiết Yêu cầu báo giá (YCBG)

| | |
|---|---|
| Bản | 1.0 — 12/09/2026 (dựng khối + nút thao tác trên chi tiết YCBG) |
| Giao diện | **cả hai bản**: `frontend-v2/` (cổng 8083) tại `/procurement/survey-requests/:id`, và từ bao-CR-390 (12/09/2026) cả màn cũ `frontend/` (cổng 8080) tại `/survey-requests/:id` — cùng API, cùng hành vi; bản v1 là `components/SurveyReportCard.tsx` + `utils/surveyReportHelpers.ts` |
| Khóa quyền | dùng lại **`survey_request`** — không thêm entity mới (luật «một khóa = một màn hình», CR-157) |
| Brief nghiệp vụ | [`doc/erp/18-bao-cao-thuc-hien-ycbg.md`](../erp/18-bao-cao-thuc-hien-ycbg.md) |
| Thiết kế kỹ thuật | [`doc/tai-lieu-ky-thuat/tdd-bao-cao-thuc-hien-ycbg.md`](../tai-lieu-ky-thuat/tdd-bao-cao-thuc-hien-ycbg.md) |
| Tài liệu YCBG gốc | [`02-yeu-cau-khao-sat.md`](02-yeu-cau-khao-sat.md) |

---

## Mục đích

Một phiếu YCBG được duyệt xong **không có nghĩa là thương vụ xong**. Phía sau nó là
một chuỗi việc kéo dài hàng tuần tới hàng tháng — xin giấy phép, ký hợp đồng, sản
xuất, vận chuyển, kiểm tra chất lượng, thông quan, về kho. Trước đây chuỗi này nằm
trong file Excel / tin nhắn của từng nhân sự thu mua (NSTM); người yêu cầu muốn biết
«hàng của tôi tới đâu rồi» thì phải đi hỏi.

Khối **Báo cáo thực hiện** đưa chuỗi việc đó **lên ngay trang chi tiết YCBG**: NSTM
khai và cập nhật, mọi người liên quan tới phiếu mở ra là thấy — cùng một nguồn sự
thật, có dấu vết trong Lịch sử thao tác.

Đây **không phải** một màn hình riêng, không có mã chứng từ, không nằm trong menu.
Nó là một **thẻ (card)** đặt trong trang chi tiết YCBG, ngay dưới bảng *Danh sách
Sản phẩm cần Khảo sát* và trên khối *Trao đổi*.

## Vai trò tham gia

| Vai | Quyền trên `survey_request` | Làm được gì với khối |
|---|---|---|
| **Người yêu cầu** (người lập phiếu, TBP duyệt, người được xem phiếu) | `read` + phạm vi dữ liệu tới được phiếu | **Chỉ XEM.** Không thấy nút thêm/sửa/xóa; khối rỗng thì tự ẩn với họ |
| **Người thực hiện — NS Thu mua** | `process` (NSTM / Quản lý TM / Admin TM) | **Toàn quyền** khởi tạo, thêm/sửa/xóa giai đoạn · nút dòng hàng · hồ sơ; cập nhật trạng thái |

> Đây là hai KHUNG NHÌN của cùng một khối, không phải hai màn — xem chi tiết ở phần
> [Hai khung nhìn](#hai-khung-nhìn).

## Ba khái niệm — đừng lẫn

| Thứ | Bảng | Là gì |
|---|---|---|
| **Nút dòng hàng** (item) | `tab_survey_request_report_item` | Nhãn lọc theo mặt hàng của phiếu (vd «K₂SO₄», «KNO₃»). Thêm/đổi tên/xóa tự do |
| **Giai đoạn** (phase) | `tab_survey_request_report_phase` | Một chặng của tiến trình (vd «Pháp lý & Giấy phép»), có tên + diễn giải/nơi thực hiện |
| **Hồ sơ** (doc) | `tab_survey_request_report_doc` | Một đầu việc/chứng từ cần hoàn thành. Đơn vị nhỏ nhất; thuộc đúng 1 giai đoạn, gắn 1 nút dòng hàng hoặc «Chung» |

**Vì sao nút dòng hàng là BẢNG chứ không suy từ dòng của phiếu:** người dùng được
thêm/sửa/xóa nút và đặt tên tùy ý — một nút có thể gom nhiều dòng, hoặc chẳng ứng
với dòng nào. Hồ sơ không gắn nút nào (`item_id = 0`) là hồ sơ **Chung** — hiện ở
mọi nút.

## Nút «Báo cáo thực hiện» xuất hiện thế nào

Khối luôn nằm ở chi tiết YCBG (với người có quyền xem). Trạng thái đầu tiên phụ
thuộc phiếu đã có báo cáo hay chưa:

| Trạng thái khối | Người yêu cầu thấy | NS Thu mua thấy |
|---|---|---|
| **Chưa có báo cáo** (phiếu mới) | *Khối ẩn hẳn* | Lời mời + **hai nút**: «Khởi tạo báo cáo mẫu» và «Thêm giai đoạn» |
| **Đã có báo cáo** | Danh sách hồ sơ theo giai đoạn (chỉ xem) | Đầy đủ thanh công cụ thao tác |

- **Khởi tạo báo cáo mẫu** — dựng theo **MẪU CHUNG** (bao-CR-388): **5 giai đoạn
  nhập khẩu** (Pháp lý & Giấy phép · Đặt hàng & Hợp đồng · Sản xuất & Vận chuyển ·
  Kiểm tra & Thông quan · Nhận hàng & Về kho) + **bộ hồ sơ chung của mẫu** (15 hồ sơ
  xếp đúng giai đoạn, có cờ bắt buộc và tiên quyết nối sẵn, gắn «Chung» nên hiện ở
  mọi nút) + **một nút dòng hàng cho mỗi dòng của phiếu** (tên lấy từ mô tả dòng).
  Bấm lặp lại **không nhân đôi** khung (đã có giai đoạn/nút thì bỏ qua). Trước
  bao-CR-388 nút này chỉ dựng khung rỗng — "bấm xong không có gì hết".
- **Thêm giai đoạn** — dựng tay từ đầu, không dùng khung mẫu.
- **Tạo mẫu** (bao-CR-388) — sau khi đã có báo cáo, đổ **thêm** mẫu chung vào đúng
  chỗ đang đứng, không phải làm lại từ đầu:
  - dạng xem **Theo dòng hàng**: dải sổ của mỗi dòng có nút «Tạo mẫu cho "‹tên
    dòng›"» (dòng Chung là «Tạo mẫu vào hồ sơ chung») → đổ **cả bộ mẫu** vào nút đó;
    giai đoạn nào của mẫu chưa có trên phiếu thì tự dựng thêm;
  - dạng xem **Xem tổng**: biểu tượng tia sáng ở đầu mỗi giai đoạn (và nút «Tạo theo
    mẫu» khi giai đoạn rỗng) → đổ **riêng phần của giai đoạn đó** vào hồ sơ Chung.
    Giai đoạn tự đặt tên (không có trong mẫu) thì báo lỗi kèm danh sách tên hợp lệ.
  - Luôn **cộng thêm, bỏ qua hồ sơ trùng tiêu đề** trong cùng nút + giai đoạn, nên bấm
    hai lần không nhân đôi; toast nói rõ «Đã tạo n hồ sơ» hay «Mẫu chung đã có đủ».
  - Mẫu hiện **nằm trong mã nguồn** (`report_constants.py`), chưa có màn quản lý — xem
    [Những thứ CHƯA có](#những-thứ-chưa-có-ngoài-phạm-vi-bản-10).

## Hai khung nhìn

### A. Người YÊU CẦU (chỉ xem)

Ai **mở được phiếu YCBG** thì xem được khối. Ba câu hỏi họ cần trả lời trong 10 giây:

- **«Tới đâu rồi?»** — thanh tóm tắt `x/y hồ sơ · z%` trên đầu khối; khung **Tiến
  trình** bên phải cho biết mỗi mặt hàng đang đứng ở giai đoạn nào (điểm nhấp nháy,
  đánh số theo nút dòng hàng, trùng chặng thì gộp «+n»).
- **«Đang tắc ở đâu, vì sao?»** — hồ sơ bị **khóa** mờ đi kèm biểu tượng 🔒, rê chuột
  đọc danh sách những hồ sơ tiên quyết chưa xong.
- **«Cái gì bắt buộc mà chưa làm?»** — tag «Bắt buộc» + pill trạng thái từng dòng;
  lọc nhanh theo nút dòng hàng / trạng thái, tìm theo mọi ô chữ.

Người xem **không thấy**: nút Khởi tạo, mọi nút thêm/sửa/xóa, bút chì; nút ✓ (đánh
dấu hoàn thành) bị vô hiệu. Phiếu **chưa có báo cáo thì khối tự ẩn**. Đây là tiện
ích giao diện — chốt thật nằm ở backend (xem [Quyền thao tác](#quyền-thao-tác-rbac)).

### B. Người THỰC HIỆN (NS Thu mua — cờ `process`)

Toàn quyền dựng và cập nhật báo cáo ngay trên trang chi tiết phiếu:

1. **Quản lý nút dòng hàng** — dấu `+` để thêm; **bút chì nằm chung khung** với tên
   nút để đổi tên/xóa. Xóa nút thì hồ sơ gắn nó **chuyển về «Chung», không bị xóa**.
2. **Quản lý giai đoạn** — «Thêm giai đoạn» / bút chì để sửa tên + diễn giải; giai
   đoạn **còn hồ sơ thì bị chặn xóa** (câu chặn nói rõ còn bao nhiêu hồ sơ).
3. **Quản lý hồ sơ** — «Thêm hồ sơ» / bút chì từng dòng mở **hộp thoại** (theo case
   C-01: chỉ đóng bằng Hủy/X, form dở thì hỏi xác nhận). Nội dung hộp thoại: xem
   [Trường của Hồ sơ](#c-trường-của-hồ-sơ). **Thùng rác cạnh bút chì** xóa thẳng
   hồ sơ đó sau một hộp xác nhận (bao-CR-388) — mẫu chung đổ ra hàng chục dòng, dọn
   bớt mà phải mở hộp sửa từng dòng thì không ai dọn; hộp sửa vẫn giữ nút Xóa.
4. **Cập nhật nhanh** — nút ✓ đầu dòng gạt **Hoàn thành ↔ Đang làm** không cần mở
   hộp thoại; biểu tượng 📎 mở thẳng hộp sửa khi hồ sơ chưa có tệp. Hồ sơ đang **khóa**
   thì ✓ bị vô hiệu — phải xong tiên quyết trước (hoặc gỡ tiên quyết trong hộp sửa).
5. **Mọi thao tác ghi đều vào Lịch sử thao tác** của phiếu («Báo cáo: thêm hồ sơ…»,
   «Báo cáo: xóa nút…») — ai làm gì lúc nào đều tra được.

### C. Hành vi dùng chung cho cả hai khung nhìn

- **Lọc & tìm** (thanh công cụ trên đầu khối):
  - **Dãy nút dòng hàng**: «Tất cả» + từng nút. Hồ sơ «Chung» hiện ở mọi nút.
  - **Ô tìm kiếm**: khớp **theo từng từ**, **bỏ dấu** tiếng Việt, soi tiêu đề + mô tả
    + tệp + nhãn trạng thái + tên nút (gõ `kno3` khớp «KNO₃»; «giay phep cong an»
    khớp «Giấy phép… Bộ Công An»).
  - **Lọc trạng thái**: Mọi trạng thái / Chưa bắt đầu / Đang làm / Chờ duyệt / Hoàn thành.
  - Rỗng-vì-bộ-lọc có **câu riêng** («Không có hồ sơ nào khớp…»), không lẫn với «Chưa
    có hồ sơ».
- **Thu gọn / mở**: nút gấp-mở **tất cả** trên header + chevron **từng giai đoạn**;
  giai đoạn gấp hiện tóm tắt `n hồ sơ · %`. Đang tìm kiếm / lọc trạng thái thì tự
  mở hết để kết quả không bị giấu.
- **Mỗi hồ sơ MỘT dòng**: ✓ · tiêu đề · tag dòng hàng · «Bắt buộc» · mô tả (cắt bớt,
  rê chuột đọc đủ) · 🔒 · 📎 · pill trạng thái · ✎ · thùng rác (hai nút chỉ có icon,
  chỉ người thực hiện thấy).
- **Khung Tiến trình** (bên phải, ẩn dưới khổ `lg`): mỗi giai đoạn một điểm từ trên
  xuống; chặng xong = xanh ✓; chặng hiện tại của mỗi track **nhấp nháy**; tiến độ
  tính theo **nút đang lọc**, cố ý không đổi theo từ khóa đang gõ.

## Vòng đời trạng thái hồ sơ & cơ chế khóa

Mỗi hồ sơ có **4 trạng thái** (mã số theo R2/QĐ-11):

| Mã | Nhãn | Màu viền / pill |
|---|---|---|
| 0 | Chưa bắt đầu | xám |
| 1 | Đang làm | hổ phách |
| 2 | Chờ duyệt | xanh dương |
| 3 | Hoàn thành | xanh lá + ✓ |

**Tiên quyết & khóa:** một hồ sơ có thể khai danh sách hồ sơ khác (cùng phiếu) là
**tiên quyết**. Hồ sơ còn tiên quyết **chưa Hoàn thành** thì bị **khóa** — không tick
✓ được, hiện mờ + 🔒 + «Chờ: …». Ngoại lệ: hồ sơ **đã Hoàn thành** thì không bao giờ
khóa ngược lại (dữ liệu cũ đánh dấu xong trước khi khai tiên quyết vẫn gạt lại được).

## Trường trên hộp thoại

### A. Trường của Nút dòng hàng

| Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|
| Tên nút (`name`) | Nhập tay | Có | Tối đa 100 ký tự. VD «K₂SO₄», «KNO₃» |

### B. Trường của Giai đoạn

| Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|
| Tên giai đoạn (`name`) | Nhập tay | Có | Tối đa 255 ký tự |
| Diễn giải / nơi thực hiện (`location`) | Nhập tay | Không | Tối đa 255 ký tự. VD «Việt Nam — trước khi đặt hàng» |

### C. Trường của Hồ sơ

| Trường | Kiểu nhập | Bắt buộc | Nguồn / Giá trị | Ghi chú |
|---|---|---|---|---|
| Tiêu đề hồ sơ (`title`) | Nhập tay | **Có** | — | Tối đa 255 ký tự |
| Mô tả chi tiết (`description`) | Nhập nhiều dòng | Không | — | Tối đa 4000 ký tự |
| Dòng hàng (`item_id`) | Chọn | Không | Danh sách nút của phiếu + «Chung» | Mặc định = nút đang lọc, hoặc «Chung» khi đang ở «Tất cả» |
| Trạng thái (`status`) | Chọn | Không | 0..3 (bảng trên) | Mặc định *Chưa bắt đầu* |
| Giai đoạn (`phase_id`) | Chọn | **Có** | Các giai đoạn của phiếu | — |
| Bắt buộc? (`required`) | Chọn | Không | Bắt buộc / Không bắt buộc | Mặc định *Bắt buộc*. Chỉ là NHÃN, backend không ép hồ sơ bắt buộc phải xong |
| Tệp đính kèm (`file_note`) | Nhập tay | Không | — | Tên tệp **hoặc** link (VD link Drive). Là chuỗi tự do — chưa nối kho đính kèm thật. Tối đa 500 ký tự. Nếu là `http(s)://…` thì biểu tượng 📎 thành link mở tab mới |
| Tiên quyết (`depends`) | Checkbox nhiều dòng | Không | Các hồ sơ khác của phiếu | Tối đa 30 hồ sơ. Chọn thành **vòng lặp** (A chờ B, B chờ A) bị **chặn ngay lúc lưu** |
| Ngày bắt đầu (`start_date`) | Chọn ngày | Không | — | Ngày bắt đầu thực hiện. Để trống = chưa đặt |
| Ngày hết hiệu lực / hạn (`expires_at`) | Chọn ngày | Không | — | Dùng để cảnh báo hồ sơ **quá hạn** (hồ sơ chưa xong có hạn sớm nhất nổi lên đầu). Để trống = chưa đặt |
| Nhân sự thực hiện (`assignee_id`) | Chọn | Không | Bảng Nhân viên (`tab_employee`) | Người phụ trách hồ sơ. Để trống = «Chưa cử». Xóa nhân sự không xóa hồ sơ |

> Ba trường **Ngày bắt đầu · Ngày hết hiệu lực · Nhân sự thực hiện** là phần mở rộng
> 12/09/2026: dữ liệu + API đã sẵn, **ô nhập trên hộp thoại và cách hiển thị trên
> dòng** đang được bổ sung cùng đợt.

## Quyền thao tác (RBAC)

Entity: `survey_request` (dùng lại, không thêm entity mới). Khối nằm trong màn chi
tiết YCBG.

| Thao tác | Quyền yêu cầu | Ghi chú scope |
|---|---|---|
| Xem khối báo cáo | `survey_request:read` | Phạm vi qua `_in_scope` của phiếu cha — ngoài phạm vi là **404**, kể cả gõ thẳng id vào URL/API |
| Khởi tạo báo cáo mẫu | `survey_request:process` | Idempotent — bấm lặp không nhân đôi; dựng cả hồ sơ của mẫu chung |
| Tạo mẫu vào nút / giai đoạn | `survey_request:process` | Cộng thêm, bỏ qua trùng; không thêm gì thì **không ghi** Lịch sử thao tác |
| Thêm/sửa/xóa nút dòng hàng | `survey_request:process` | Xóa nút → hồ sơ về «Chung» |
| Thêm/sửa/xóa giai đoạn | `survey_request:process` | Giai đoạn còn hồ sơ thì **chặn xóa** |
| Thêm/sửa/xóa hồ sơ, đổi trạng thái ✓ | `survey_request:process` | — |

> `process` là **cờ suy ra** «là NS Thu mua» (không phải action có trong grant), nên
> **phạm vi luôn hỏi theo `read`** qua `_in_scope`. Chi tiết: TDD §Phân quyền.

## Quy tắc nghiệp vụ

1. **Xóa nút KHÔNG xóa hồ sơ** — hồ sơ đang gắn nút bị xóa được chuyển `item_id = 0`
   (Chung). Nút chỉ là nhãn lọc, hồ sơ là công sức nhập liệu.
2. **Xóa hồ sơ tự gỡ tham chiếu** — id hồ sơ bị xóa được gỡ khỏi danh sách tiên quyết
   của mọi hồ sơ khác. Để lại id chết là hồ sơ khác khóa vĩnh viễn theo một thứ không
   còn tồn tại.
3. **Chặn xóa giai đoạn còn hồ sơ** — muốn bỏ thì chuyển hồ sơ sang giai đoạn khác trước.
4. **Chặn vòng tiên quyết + tiên quyết chéo phiếu** — kiểm ngay lúc lưu; vòng lặp làm
   cả cụm hồ sơ khóa lẫn nhau vĩnh viễn.
5. **Trần dữ liệu** — mỗi phiếu tối đa 50 nút · 50 giai đoạn · 500 hồ sơ; mỗi hồ sơ
   tối đa 30 tiên quyết (chống tràn số thứ tự và payload rác).
6. **Mọi thao tác ghi vào Lịch sử thao tác** của phiếu (`survey_request`), nội dung
   dạng «Báo cáo: …».

## Những thứ CHƯA có (ngoài phạm vi bản 1.0)

- **Ô nhập ngày + chọn nhân sự trên hộp thoại** và cách hiển thị ngày/người trên
  dòng hồ sơ — đang bổ sung (dữ liệu + API đã sẵn, xem ghi chú ở bảng trường Hồ sơ).
- **Nhắc hạn chủ động** (thông báo khi hồ sơ sắp/đã quá hạn) — hiện chỉ cảnh báo bị
  động bằng ngày hết hiệu lực sớm nhất.
- **Tệp đính kèm thật**: ô 📎 hiện là chuỗi tự do (tên tệp hoặc link) — chưa nối kho
  `attachment` của hệ. Upload trực tiếp là việc đợt sau.
- **Nhớ trạng thái gấp/mở** theo người dùng (`localStorage`) — hiện là state trong màn.
- **Quản lý mẫu** (nhiều mẫu, sửa/thêm hồ sơ mẫu trên giao diện, lưu báo cáo đang có
  thành mẫu) — cố ý **chưa làm** (bao-CR-388): mẫu chung là một danh sách trong mã
  nguồn, đổi nội dung là sửa `DEFAULT_TEMPLATE_DOCS` rồi deploy. Khi có bảng mẫu thì
  thay nguồn đọc trong `report_service.apply_template`, nút bấm và API giữ nguyên.
  Danh sách ~22 hồ sơ thật của Phòng Thu mua **chưa gửi** — bộ 15 hồ sơ hiện tại là
  bản tạm theo artifact nhập khẩu.
- **Điều kiện rẽ nhánh theo trạng thái**, bộ máy duyệt — chưa có.
- **Cấp số CR + ghi `change-log.md`** cho tính năng — chờ chốt.
