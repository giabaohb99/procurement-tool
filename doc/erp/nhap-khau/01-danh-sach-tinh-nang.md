# 01 · HỒ SƠ & TIẾN ĐỘ NHẬP KHẨU — YÊU CẦU VÀ DANH SÁCH CHỨC NĂNG

| | |
|---|---|
| **Phiên bản** | **v1.1** · 12/09/2026 |
| **Loại tài liệu** | Yêu cầu rút gọn (BRD + PRD gộp) — chốt trước khi code |
| **Nguồn yêu cầu** | Báo cáo *"Thủ tục pháp lý & giấy phép nhập khẩu K₂SO₄ + KNO₃"* (Phòng Thu mua, 11/09/2026) và bản giao diện gợi ý 3 màn do khách dựng |
| **Xây trên** | Đơn mua hàng nhập khẩu đã có — `order_type = IMPORT` (bao-CR-319/347), điều khoản in (bao-CR-321), báo cáo giá vốn nhập khẩu |
| **CR** | Chưa cấp. Số trống kế tiếp tại thời điểm viết: **386** (grep cả `change-log.md` lẫn `change-log-bao.md` trước khi đặt chỗ) |
| **Trạng thái** | ⚠️ **TẠM DỪNG 12/09/2026** — đồng nghiệp đã dựng xong một bản màn *Báo cáo thực hiện* trên **Yêu cầu báo giá**. Chờ commit của bản đó, gộp lại, rà mã nguồn rồi mới sửa tài liệu này theo. **Không code theo tài liệu này trong lúc chờ.** Checklist rà ở mục 14 |

**Thay đổi ở bản 1.1** — khách trả lời đủ 6 câu hỏi H1–H6 ngày 12/09, ba đáp án đổi thiết kế:

| Đáp án | Đổi cái gì |
|---|---|
| **H1** — chặng **không cố định**, người dùng tự khai bộ hồ sơ kiểu checklist, mỗi dòng có số ngày tối đa, tổng hợp lên | Chặng từ **bộ mã cứng trong mã nguồn** thành **danh mục người dùng khai**. Số ngày **chỉ khai ở dòng hồ sơ**, chặng cộng lên. Xem mục 4 và A02 |
| **H3** — hồ sơ gắn vào **dòng hàng / mặt hàng** | Bảng checklist mang `po_item_id`, không phải chỉ `po_id`. Kéo theo mục 5 (lối vào) và mục 8 (mô hình dữ liệu) |
| **H2 + H5** — bản 1 **mở hết**, logic điều kiện để sau; **Thu mua là người tick** | Khóa theo tiền quyết (B09/B10) **hạ xuống bản 2**, bản 1 chỉ cảnh báo. Và **rủi ro phân quyền ở mục 9 biến mất** |

**Hai quyết định khách đã chốt trước đó:**

| # | Nội dung | Hệ quả |
|---|---|---|
| QĐ-A | Dùng lại khóa quyền **`purchase_order`**, không đẻ entity mới | Sau đáp án H5 thì đây thành lựa chọn **không có mặt trái** — xem mục 9 |
| QĐ-B | Làm trên **cả hai giao diện** — `frontend/` (thumua) và `frontend-v2/` (erp) | `frontend/` đang đóng băng theo D-026 (chỉ vá lỗi). Đây là **ngoại lệ có chủ đích** vì người dùng thật còn ở `thumua`. Mọi thay đổi làm hai lần, tài liệu bàn giao có hai bộ ảnh chụp màn hình |

---

## 1. Vì sao cần

Báo cáo pháp lý ngày 11/09 chỉ ra một việc mà hệ thống hiện **không nhìn thấy được**: hai mặt hàng cùng nhập từ Trung Quốc nhưng đi hai đường thủ tục dài ngắn khác hẳn nhau.

| | K₂SO₄ (Kali sunphat) | KNO₃ (Kali nitrat ≥ 98,5%) |
|---|---|---|
| Mã HS | 3104.21.00 | 3102.60.00 |
| Phân loại | Phân bón thường | **Tiền chất thuốc nổ** (NĐ 113/2017, sửa bởi NĐ 82/2022) |
| Giấy phép đặc biệt | Không | **Giấy phép Bộ Công An — 30÷45 ngày làm việc** |
| Kiểm hóa | Theo luồng | 100% kiểm thực tế |
| Tổng thời gian | ~30÷35 ngày | **~60÷75 ngày** |

Chặng xin giấy phép 45 ngày **xảy ra trước khi có đơn mua hàng**. Nghĩa là màn *Tiến độ mua hàng* (Task 7) — vốn đi từ đơn mua hàng xuống lần giao — về mặt cấu trúc **không thể thấy chặng đó**. Đó chính là lý do phải làm chức năng này chứ không phải mở rộng màn cũ.

Hệ quả thực tế đã xảy ra: hạn giao 12/09/2026 là **không khả thi** với KNO₃, và không ai biết điều đó cho tới khi có người ngồi tra luật rồi viết tay ra một tệp Word.

---

## 2. Mục tiêu — bốn câu hỏi phải trả lời được trên màn hình

1. **Lô hàng này đang tắc ở đâu?** — chặng nào chưa xong, ai đang giữ việc.
2. **Có trễ không, trễ mấy ngày?** — không phải "xong 12%", mà là "chậm 9 ngày so với kế hoạch".
3. **Hàng về kho khi nào?** — ngày dự kiến tính từ phần việc còn lại, tự cập nhật khi có việc xong sớm hoặc muộn.
4. **Chặng nào hay làm chậm cả lô?** — số liệu tích lũy qua nhiều lô, để lần sau đặt hàng biết đường chừa thời gian.

> ⚠️ **Câu 2 là câu quan trọng nhất và cũng là chỗ bản giao diện gợi ý đang hụt.** Bản đó đo tiến độ bằng **số hồ sơ** (`2/17 hồ sơ = 12%`), tức đặt tờ Packing List ngang hàng với giấy phép tiền chất 45 ngày. Đo kiểu đó thì màn hình **vĩnh viễn không nói được chữ "trễ"**. Xem công thức ở mục 7.1.

---

## 3. Phạm vi

### Làm

- Danh mục **chặng** (người dùng tự khai) và **khuôn hồ sơ** theo loại hàng / mã HS.
- **Checklist hồ sơ gắn vào từng dòng hàng** của đơn mua hàng nhập khẩu, có người phụ trách, hạn, tệp đính kèm — kiểu danh sách việc phải làm.
- Loại hồ sơ **một lần cho mặt hàng** (giấy đăng ký lưu hành, công bố hợp quy…): khai một lần, mọi lô sau tự thấy "Đã có".
- **Báo cáo tiến độ nhập khẩu** — 4 ô số + 4 đồ thị, có bảng số liệu và xuất Excel.
- Nhắc việc qua chuông và thư cho người phụ trách hồ sơ sắp tới hạn / quá hạn.
- Bổ sung danh mục loại chứng từ để đủ cho hàng nhập khẩu.

### KHÔNG làm (bản 1)

| Không làm | Vì sao |
|---|---|
| **Khóa cứng theo tiền quyết** | H2 chốt: bản 1 **mở hết**, ai tick gì cũng được. Hệ thống chỉ **cảnh báo** *"Hợp đồng NK chưa xong"*, không chặn tay người dùng. Luật điều kiện (kiểu *NCC xuất FOB thì phải có hợp đồng trước*) làm ở bản 2, khi đã đủ dữ liệu thật để biết luật nào đúng |
| **Bản đồ tuyến đường** (Quảng Châu → Cát Lái → Cần Thơ) | Trong bản gợi ý nó là hình vẽ chết, không lấy dữ liệu từ đâu. Thay bằng một dòng chữ *"Đang ở: Cảng Cát Lái"* |
| Tự nộp hồ sơ / nối API cơ quan nhà nước | Ngoài tầm |
| Theo dõi container theo thời gian thực (hãng tàu) | Chờ bản 2, cần hợp đồng dữ liệu với hãng tàu |
| Quy trình duyệt riêng cho hồ sơ nhập khẩu | Hồ sơ là việc phải làm, không phải phiếu phải ký. Duyệt vẫn nằm ở đơn mua hàng |

---

## 4. Khái niệm

| Khái niệm | Nghĩa | Ví dụ |
|---|---|---|
| **Hồ sơ** | Một dòng việc phải làm: một tờ giấy hoặc một thủ tục. Mỗi dòng mang **số ngày tối đa** | *Giấy phép nhập khẩu tiền chất — Bộ Công An · tối đa 45 ngày* |
| **Chặng** | Nhóm để xếp các hồ sơ đi cùng nhau. **Người dùng tự khai, thêm bớt được** — không cố định 5 chặng | *Xin giấy phép · Đặt hàng & hợp đồng · Sản xuất & vận chuyển · Thông quan · Về kho* |
| **Khuôn hồ sơ** | Bộ hồ sơ chuẩn của một loại hàng. Khai một lần, dùng cho mọi lô sau | Khuôn *"Tiền chất thuốc nổ"* gồm 20 dòng |
| **Hồ sơ một lần** | Hồ sơ cấp **mặt hàng**, không cấp lô. Có rồi thì mọi lô sau tự thấy "Đã có", **không tính vào số ngày** | *Giấy đăng ký lưu hành phân bón* |
| **Tiền quyết** | Hồ sơ A chưa xong thì hồ sơ B chưa nên bắt đầu. **Bản 1 chỉ cảnh báo, không khóa** | *Tờ khai hải quan* chờ *Vận đơn (B/L)* |
| **Chặng chặn** | Chặng có tổng số ngày dài nhất trong phần việc còn lại — thứ quyết định ngày hàng về | Với KNO₃ là chặng *Xin giấy phép* |

> ⚠️ **Số ngày chỉ khai ở DÒNG HỒ SƠ, chặng cộng lên** (theo H1: *"viết tổng quát rồi sum lại thôi"*). Không có ô "số ngày của chặng" để người dùng gõ — có hai chỗ gõ cùng một con số thì trước sau gì cũng lệch nhau.
>
> ⚠️ **Hạn chế đã biết của phép cộng:** các hồ sơ trong một chặng nếu làm **song song** thì cộng lên ra dài hơn thực tế. Bản 1 cứ cộng — thà ước lượng dư còn hơn hứa với khách một ngày không giữ được. Bản 2 thêm cờ *"làm song song"* cho từng dòng, lúc đó chặng lấy `max` thay vì `sum`.

---

## 5. Lối vào — Thu mua thao tác ở đâu

**Không có chuyện "đồng bộ qua".** Chỉ có **một bảng dữ liệu duy nhất**; mọi màn hình là cửa sổ nhìn vào bảng đó. Đồng bộ hai chiều giữa hai bản dữ liệu là thứ luôn luôn lệch, và lệch trong im lặng.

| Lối vào | Ai dùng | Làm gì ở đó |
|---|---|---|
| **1 · Tab _Hồ sơ nhập khẩu_ trên chi tiết Đơn mua hàng** | Thu mua, khi đang xử lý một lô | **Nơi thao tác chính.** Tick hoàn thành, gán người, đổi hạn, đính kèm tệp, thêm dòng phát sinh. Tab chỉ hiện khi `order_type = IMPORT` |
| **2 · Cột _Hồ sơ_ ngay trên bảng dòng hàng của Đơn mua hàng** | Thu mua, liếc nhanh | Mỗi dòng hàng một chấm màu + `3/12`. Bấm vào nhảy xuống tab 1, **đã lọc sẵn đúng dòng hàng đó**. Đây chính là "tab phụ" theo nghĩa nhìn thấy ngay mà không phải đi đâu |
| **3 · Màn _Báo cáo tiến độ nhập khẩu_** | Trưởng phòng, Ban giám đốc | **Chỉ đọc**, nhiều lô cùng lúc, có đồ thị. Bấm một lô là quay về lối 1 |
| **4 · Tab _Hồ sơ nhập khẩu_ trên chi tiết Sản phẩm** | Thu mua, một lần cho mỗi mặt hàng | Nơi khai **hồ sơ một lần** (đăng ký lưu hành, công bố hợp quy). Khai xong thì mọi lô sau của mặt hàng đó tự thấy "Đã có" |

### Vì sao tab nằm trên Đơn mua hàng chứ không phải màn riêng

Vì H3 chốt hồ sơ gắn vào **dòng hàng**. Dòng hàng chỉ tồn tại bên trong đơn, nên tách ra màn riêng thì người dùng phải tự nhớ lô nào chở mặt hàng nào — đúng việc mà máy phải làm hộ. Ngược lại, đặt trong đơn thì Thu mua đang mở đơn để làm việc khác cũng **thấy ngay** hồ sơ còn thiếu, không cần ai nhắc.

### Ba điểm kỹ thuật bắt buộc, không được bỏ qua

- ⚠️ **Chốt khóa sửa sau khi duyệt (CR-108) KHÔNG được áp cho checklist.** Đơn sang `approved` là khóa toàn bộ dòng hàng — nhưng hồ sơ là việc **phát sinh sau khi duyệt**, y hệt khối *Giao hàng nhiều lần* vốn đã được chừa. Không nới thì người dùng tick xong bấm lưu và **không có gì xảy ra**, lỗi lại im lặng. Phải khai checklist vào cùng danh sách ngoại lệ với 5 ô đang mở.
- ⚠️ **Xóa dòng hàng (lúc còn nháp) phải dọn hồ sơ của dòng đó theo.** Không dọn thì thành dữ liệu mồ côi, và mọi phép đếm `x/y` trên đơn đều sai mà không ai biết vì sao.
- ⚠️ **Hồ sơ một lần khóa theo `product_code` (chuỗi), không theo id sản phẩm.** `tab_product` là bảng biến thể (SKU), **không có FK nào trỏ vào nó** — cả bảy bảng nghiệp vụ hiện tại đều nối nhau bằng chuỗi `product_code`. Làm khác đi là đi ngược mô hình dữ liệu sản phẩm (D-025).

---

## 6. Danh sách chức năng

**Cách đọc:**

| Cột | Nghĩa |
|---|---|
| Bản | **1** = bản đầu · **2** = làm sau |
| Có sẵn | `[x]` dùng lại được ngay · `[~]` có nhưng phải sửa · `[ ]` phải làm mới |

Tổng: **59 chức năng**, trong đó **48 thuộc bản đầu**.

### NHÓM A · DANH MỤC, CHẶNG VÀ KHUÔN HỒ SƠ

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| A01 | Bổ sung danh mục loại chứng từ | `DOCUMENT_TYPES` hiện có **11 loại, toàn hàng nội địa**. Trong 22 hồ sơ của bản gợi ý chỉ khớp **4** (hợp đồng · CO/CQ · hóa đơn · chứng từ thanh toán). Thêm: Invoice, Packing List, Vận đơn B/L, Form E, Tờ khai hải quan, Giấy phép tiền chất, Giấy đăng ký lưu hành phân bón, Giấy kiểm tra chất lượng nhà nước, Chứng thư hun trùng, MSDS, Chứng từ bảo hiểm, L/C — **12 loại mới** | 1 | `[~]` |
| A02 | **Danh mục chặng** — người dùng tự khai | Bảng riêng, không phải bộ mã cứng (H1). Mỗi chặng: mã, tên, thứ tự, màu trên đồ thị, ngừng dùng. **Không có ô số ngày** — chặng cộng từ các dòng hồ sơ trong nó | 1 | `[ ]` |
| A03 | Danh mục **khuôn hồ sơ** | Màn danh sách + chi tiết. Mỗi khuôn: tên, áp cho mã HS nào / phân loại hàng nào, ghi chú căn cứ pháp lý | 1 | `[ ]` |
| A04 | Dòng trong khuôn | Mỗi dòng: tên hồ sơ, chặng, loại chứng từ (A01), **số ngày tối đa**, bắt buộc hay không, ghi chú hướng dẫn, tiền quyết trỏ tới dòng khác trong cùng khuôn | 1 | `[ ]` |
| A05 | Nhân bản khuôn | Khuôn KNO₃ khác khuôn K₂SO₄ đúng 3 dòng — bắt gõ lại 20 dòng là không ai làm | 1 | `[ ]` |
| A06 | Khuôn / chặng ngừng dùng | Đánh dấu ngừng: không gán cho lô mới, lô đang chạy vẫn giữ. Cùng luật với danh mục chức vụ | 1 | `[ ]` |
| A09 | Loại **hồ sơ một lần cho mặt hàng** | Cờ trên dòng khuôn. Dòng có cờ này **không đẻ ra bản sao cho mỗi lô** — nó đứng ở cấp mặt hàng, mọi lô đọc chung, và **không cộng vào số ngày của lô**. Đây là cách xử *Đăng ký lưu hành phân bón* theo H2 | 1 | `[ ]` |
| A07 | Căn cứ pháp lý gắn vào dòng khuôn | Trường chữ: *"NĐ 113/2017, sửa bởi NĐ 82/2022"*. Luật đổi thì tra ra ngay dòng nào phải sửa | 2 | `[ ]` |
| A08 | Cảnh báo khuôn lệch mã HS | Tạo đơn có mã HS chưa khuôn nào phủ thì báo, không chặn | 2 | `[ ]` |

### NHÓM B · CHECKLIST TRÊN ĐƠN NHẬP KHẨU

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| B01 | Tab **Hồ sơ nhập khẩu** trên chi tiết đơn | Chỉ hiện khi `order_type = IMPORT`. Đơn nội địa không thấy tab. Xem mục 5 | 1 | `[ ]` |
| B02 | Sinh checklist từ khuôn, **theo từng dòng hàng** | Chọn khuôn cho dòng hàng → đẻ ra các dòng hồ sơ của **dòng hàng đó** (H3). **Chép giá trị, không trỏ tới khuôn** — sửa khuôn về sau không được làm đổi lô đang chạy | 1 | `[ ]` |
| B03 | Thêm / sửa / xóa dòng hồ sơ thủ công | Lô nào cũng có việc phát sinh ngoài khuôn | 1 | `[ ]` |
| B04 | Đánh dấu hoàn thành | Ô tick. Ghi lại ai tick, lúc nào. Bỏ tick được, có ghi vết | 1 | `[ ]` |
| B05 | Trạng thái hồ sơ | Lưu **SMALLINT + IntEnum** (R2/QĐ-11): `1` Chưa bắt đầu · `2` Đang làm · `3` Chờ đối tác · `4` Hoàn thành · `5` Không áp dụng | 1 | `[ ]` |
| B06 | Người phụ trách từng dòng | Lưu **`assignee_id` = ID NHÂN SỰ**, không phải ID tài khoản. Mục VI của báo cáo pháp lý đã có sẵn cột này | 1 | `[~]` |
| B07 | Hạn xử lý từng dòng | Tự tính từ ngày bắt đầu chặng + số ngày tối đa; sửa tay đè lên được | 1 | `[ ]` |
| B08 | Đính kèm tệp vào dòng hồ sơ | **Không cần bảng mới.** `FileLink` đã có `entity` + `entity_id` + `purchase_order_id` + `doc_type`. Tick mà không kèm tệp thì không chứng minh được gì với hải quan — bản gợi ý để "chưa có file" là **chữ xám**, phải đổi thành **nút tải lên** | 1 | `[x]` |
| B11 | Hai cách nhóm, một tập dữ liệu | Nhóm theo **chặng** và nhóm theo **dòng hàng**. Là `group_by` của cùng một bảng, **không phải bộ dữ liệu thứ hai** — chỗ này bản gợi ý làm đúng | 1 | `[ ]` |
| B12 | Lọc theo mặt hàng | Chip *Tất cả · K₂SO₄ · KNO₃*. Sau H3 thì đây chỉ là cách trình bày lại của B11 | 1 | `[ ]` |
| B13 | Ghi chú theo dòng | Số công văn, ngày nộp, tên cán bộ tiếp nhận | 1 | `[ ]` |
| B14 | Suy ra `document_status` của đơn | `PO_DOCUMENT_STATUS` hiện chỉ `none / partial / full` — **không nói được thiếu tờ nào**. Có checklist rồi thì cột này **tự suy ra**, bỏ hẳn việc nhập tay | 1 | `[~]` |
| B15 | Mốc ngày chặng | Ngày bắt đầu và ngày kết thúc thực tế của mỗi chặng — tự lấy từ lần tick đầu và lần tick cuối trong chặng. **Không bắt ai gõ ngày** | 1 | `[ ]` |
| B18 | Cột **Hồ sơ** trên bảng dòng hàng | Chấm màu + `3/12` trên từng dòng hàng, bấm vào nhảy xuống tab đã lọc sẵn. Lối vào 2 ở mục 5. ⚠️ Bảng dòng hàng dùng chung `LinesTable` — khai cột mới ở đó, **không chép khung bảng** | 1 | `[ ]` |
| B19 | Checklist chạy được trên **đơn nháp** | Theo H4. Chặng xin giấy phép xảy ra trước khi đơn được duyệt — không cho khai từ nháp thì mất đúng 45 ngày đầu, tức mất chính thứ chức năng này sinh ra để thấy | 1 | `[ ]` |
| B20 | ⚠️ Nới chốt khóa sửa sau duyệt cho checklist | CR-108 khóa dòng hàng từ `approved`. Không khai ngoại lệ thì tick xong **không lưu được và không báo lỗi**. Xem mục 5 | 1 | `[~]` |
| B21 | Xóa dòng hàng thì dọn hồ sơ theo | Không dọn thì thành dữ liệu mồ côi và mọi phép đếm `x/y` đều sai | 1 | `[ ]` |
| B09 | Cảnh báo tiền quyết (**không khóa**) | Hiện dòng chữ *"Chờ: Hợp đồng NK + đặt cọc"* nhưng **vẫn cho tick**. Khóa cứng hạ xuống bản 2 theo H2 | 2 | `[ ]` |
| B10 | Chặn vòng tiền quyết | Đi cùng B09. A chờ B, B chờ A thì không ai bắt đầu được và màn hình im lặng. Dò có trần độ sâu; **chạm trần phải chặn**, không được trả về im lặng — đúng bài học `block_manager_cycle` | 2 | `[ ]` |
| B16 | Sao chép checklist sang đơn khác | Lô sau cùng mặt hàng cùng NCC | 2 | `[ ]` |
| B17 | Bản in danh mục hồ sơ | A4, đưa cho khai thuê hải quan | 2 | `[ ]` |

### NHÓM C · TIẾN ĐỘ

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| C01 | **Tiến độ tính theo NGÀY** | Công thức ở mục 7.1. Không dùng tỉ lệ số hồ sơ | 1 | `[ ]` |
| C02 | Số ngày trễ | `max(0, hôm nay − hạn của dòng chưa xong sớm nhất)`. Đây là con số sếp hỏi | 1 | `[ ]` |
| C03 | Ngày hàng về dự kiến | Hôm nay + tổng số ngày của phần việc còn lại. Bản 1 cộng dồn (xem ghi chú ở mục 4); tự đổi mỗi lần có dòng xong | 1 | `[ ]` |
| C04 | Chỉ ra **chặng chặn** | Bôi đỏ chặng dài nhất trong phần còn lại, kèm chữ *"chặng chặn tiến độ"* | 1 | `[ ]` |
| C05 | Cảnh báo mặt hàng có điều kiện | Băng đỏ đầu màn khi lô có mặt hàng thuộc danh mục quản lý đặc biệt. Giữ nguyên từ bản gợi ý | 1 | `[ ]` |
| C06 | Ghi lại số ngày thực tế theo chặng | Lưu khi lô đóng, để nuôi đồ thị Đ3 | 1 | `[ ]` |
| C07 | Lịch sử đổi hạn | Ai dời hạn, lúc nào, lý do. Không có thì kế hoạch trượt dần mà không ai chịu trách nhiệm | 2 | `[ ]` |

### NHÓM D · BÁO CÁO VÀ ĐỒ THỊ

Chi tiết thiết kế ở **mục 7**.

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| D01 | Màn **Báo cáo tiến độ nhập khẩu** | Đường dẫn `/procurement/import-progress`. Bộ lọc: khoảng thời gian · công ty · nhà cung cấp · mặt hàng · trạng thái lô | 1 | `[ ]` |
| D02 | Bốn ô số đầu màn | Lô đang chạy · **Lô trễ hạn** · Số ngày trung bình thực tế · Hồ sơ quá hạn | 1 | `[ ]` |
| D03 | Đ1 — Thanh ngang xếp chồng theo chặng | Thay cho biểu đồ Gantt. Mỗi lô một dòng, trục ngang là ngày | 1 | `[ ]` |
| D04 | Đ2 — Cột: số lô đang đứng ở mỗi chặng | Ảnh chụp hiện trạng | 1 | `[ ]` |
| D05 | Đ3 — Cột kép: kế hoạch với thực tế theo chặng | Trả lời *"chặng nào hay làm chậm cả lô"* | 1 | `[ ]` |
| D06 | Đ4 — Vành khuyên: tình trạng hồ sơ | Đủ · Thiếu · Quá hạn. Dùng **bảng màu trạng thái**, luôn kèm biểu tượng và chữ | 1 | `[ ]` |
| D08 | Bảng số liệu kèm mỗi đồ thị | Bắt buộc — vừa là lối thoát cho người không phân biệt màu, vừa là thứ người ta copy sang Excel | 1 | `[ ]` |
| D09 | Xuất Excel | Dùng lại khuôn xuất báo cáo sẵn có | 1 | `[~]` |
| D07 | Đ5 — Đường: số ngày thông quan trung bình theo tháng | Một chuỗi số liệu nên không cần chú giải | 2 | `[ ]` |
| D10 | Xuất Word qua trợ lý AI | `export_report_file` đã có sẵn. Chỉ cần nút *"Xuất báo cáo"* nạp số liệu thật vào — đây là **hướng 2** khách nhắc: sếp cần bản giấy thì bấm một nút | 2 | `[~]` |
| D11 | Khối tiến độ nhập khẩu trên Trang chủ | Chỉ hiện khi có lô nhập khẩu đang chạy | 2 | `[ ]` |

### NHÓM E · NHẮC VIỆC

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| E01 | Chuông khi được giao hồ sơ | Dùng lại hệ thông báo sẵn có | 1 | `[x]` |
| E02 | Nhắc trước hạn | Trước 3 ngày. Dòng dài (giấy phép 45 ngày) nhắc trước 7 ngày | 1 | `[ ]` |
| E03 | Nhắc quá hạn | Hằng ngày cho người phụ trách, hằng tuần gộp cho trưởng phòng | 1 | `[ ]` |
| E04 | Tiền quyết vừa xong thì báo người kế tiếp | Dù bản 1 không khóa, việc báo vẫn hữu ích | 1 | `[ ]` |
| E05 | ⚠️ Khai `ENTITY_LABELS` + `ENTITY_LINKS` | Thiếu thì thư vẫn gửi nhưng ghi tên trống và đường dẫn **rỗng** — bấm vào không đi đâu, mà `notify_new_tasks` **nuốt lỗi** nên không chỗ nào đỏ lên | 1 | `[~]` |
| E06 | Thư điện tử tổng hợp đầu tuần | Danh sách lô đang chạy và lô trễ, gửi trưởng phòng | 2 | `[ ]` |

### NHÓM F · HAI GIAO DIỆN (QĐ-B)

| Mã | Tính năng | Mô tả | Bản | Có sẵn |
|---|---|---|---|---|
| F01 | Bản `frontend-v2` (erp) | Làm **trước**. Là nơi màn hình sống lâu dài | 1 | `[ ]` |
| F02 | Bản `frontend` (thumua) | Làm **sau khi v2 chạy ổn**, bê nguyên luật nghiệp vụ. Đây là ngoại lệ của D-026, ghi rõ lý do trong CR | 1 | `[ ]` |
| F03 | API dùng chung | Một bộ endpoint cho cả hai giao diện. **Không được đẻ hai đường API** | 1 | `[ ]` |
| F04 | Kiểm thử backend | Công thức tiến độ · hồ sơ một lần · dọn hồ sơ khi xóa dòng hàng · nới chốt CR-108 · phạm vi dữ liệu. Chỉ chạy phần vừa sửa | 1 | `[ ]` |
| F05 | Tài liệu bàn giao hai bộ ảnh | `doc/tai-lieu-chuc-nang/19-ho-so-nhap-khau.md` + bài hướng dẫn trên Trung tâm HDSD | 1 | `[ ]` |

---

## 7. Thiết kế báo cáo và đồ thị

### 7.1 Công thức tiến độ — đây là phần lõi

Mỗi dòng hồ sơ mang `planned_days` (số ngày tối đa). Tiến độ **không** là số dòng đã tick chia tổng số dòng, mà là:

```
% hoàn tất  =  tổng planned_days của các dòng ĐÃ XONG
               ───────────────────────────────────────
               tổng planned_days của TOÀN BỘ dòng bắt buộc

số ngày trễ =  max(0, hôm nay − hạn của dòng chưa xong có hạn sớm nhất)

ngày về dự kiến = hôm nay + tổng planned_days của phần việc còn lại
```

Dòng có cờ **hồ sơ một lần** (A09) **không vào mẫu số** — nó không tiêu ngày của lô này.

So sánh trực tiếp trên lô KNO₃ (77 ngày kế hoạch, đã xong 2 hồ sơ nhỏ):

| Cách đo | Kết quả | Đọc ra |
|---|---|---|
| Theo số hồ sơ (bản gợi ý) | **10%** | Không nói gì. Tick thêm Packing List là nhảy lên 15% dù giấy phép chưa nộp |
| Theo ngày (đề xuất) | **2%, chặng chặn: Xin giấy phép, còn 45 ngày, trễ 9 ngày** | Đọc một dòng là biết phải làm gì |

> Hai tờ Invoice và Packing List **cộng lại 3 ngày trên 77** — đó mới là phần đóng góp thật của chúng vào ngày hàng về.

### 7.2 Bốn đồ thị của bản 1

| Mã | Đồ thị | Trục / dữ liệu | Trả lời câu hỏi |
|---|---|---|---|
| **Đ1** | **Thanh ngang xếp chồng** — mỗi lô một dòng | Trục ngang = **ngày**. Mỗi đoạn màu = một chặng, dài đúng bằng tổng số ngày của chặng. Phần đã qua tô đặc, phần còn lại tô nhạt. Vạch dọc = hôm nay | *"Lô nào đang tắc ở đâu, còn bao lâu"* — thay cho Gantt, `recharts` đã có sẵn thanh ngang, không cần thư viện mới |
| **Đ2** | **Cột dọc** — số lô ở mỗi chặng | Trục ngang = các chặng đang dùng, trục dọc = số lô | *"Hiện có mấy lô đang kẹt ở khâu giấy phép"* |
| **Đ3** | **Cột kép** — kế hoạch với thực tế | Trục ngang = các chặng, trục dọc = **số ngày trung bình**. Hai cột cạnh nhau | *"Chặng nào hay làm chậm cả lô"* — đây là thứ nuôi ngược lại số ngày kế hoạch cho lần sau |
| **Đ4** | **Vành khuyên** — tình trạng hồ sơ | 3 lát: Đủ · Thiếu · Quá hạn | *"Sổ sách có sạch không"* |

⚠️ **Chặng là danh mục mở (H1) nên hai đồ thị Đ2 và Đ3 phải gom theo `stage_id`, không gom theo TÊN.** Gom theo tên thì đổi tên chặng một lần là số liệu lịch sử vỡ làm đôi. Đây đúng bài học của bộ lọc chức vụ: lọc bằng chữ thì đổi tên là bộ lọc đã lưu trượt sạch.

⚠️ **Quá 8 chặng thì gom phần đuôi thành "Khác"**, không sinh thêm màu. Bảng màu có 8 vị trí cố định; đẻ màu thứ 9 là hai chặng nhìn giống nhau.

### 7.3 Luật vẽ — bắt buộc tuân thủ

| Luật | Vì sao |
|---|---|
| **Một trục dọc duy nhất.** Cấm hai thang đo trên cùng một đồ thị | Muốn đặt "số ngày" cạnh "số tiền" thì tách hai đồ thị, hoặc quy về cùng gốc. Đây là lỗi đồ thị phổ biến số một |
| **Màu gắn với CHẶNG theo `stage_id`, thứ tự cố định, không xoay vòng** | Lọc bỏ một lô mà các lô còn lại đổi màu thì người xem đọc sai |
| **Màu trạng thái là bộ riêng**, không bao giờ lấy làm màu chặng tiếp theo | Đỏ trên màn này chỉ có một nghĩa: trễ. Và luôn đi kèm **biểu tượng + chữ**, không bao giờ để màu tự nói |
| **Từ 2 chuỗi số liệu trở lên là phải có chú giải**; từ 4 trở xuống thì dán nhãn thẳng lên đồ thị | Không để người xem phải dò màu |
| **Chữ dùng màu chữ, không dùng màu của chuỗi số liệu** | Con số và nhãn giữ màu mực thường; chấm màu bên cạnh mới là thứ mang danh tính |
| **Mỗi đồ thị kèm một bảng số liệu** (D08) | Vừa là lối thoát cho người không phân biệt màu, vừa là thứ người ta copy sang Excel |
| **Chỉ báo trạng thái luôn là biểu tượng + chữ + màu**, không dùng emoji | Luật chung của dự án |

### 7.4 Bốn ô số đầu màn

Không vẽ đồ thị cho bốn số này — một con số lớn đọc nhanh hơn mọi biểu đồ.

| Ô | Nội dung | Tô đỏ khi |
|---|---|---|
| Lô đang chạy | Đếm đơn `order_type = IMPORT` chưa về đủ | — |
| **Lô trễ hạn** | Đếm lô có `số ngày trễ > 0` | Luôn đỏ nếu > 0 |
| Số ngày trung bình thực tế | Trung bình các lô đã đóng trong kỳ lọc | So với kỳ trước, tăng thì cảnh báo |
| Hồ sơ quá hạn | Đếm dòng chưa xong đã qua hạn | Luôn đỏ nếu > 0 |

---

## 8. Mô hình dữ liệu tóm tắt

Năm bảng mới. Không đụng vào bảng đơn mua hàng ngoài một cột suy ra.

| Bảng | Vai trò | Cột chính |
|---|---|---|
| `tab_import_doc_stage` | **Chặng** — danh mục mở (H1) | `code` · `name` · `sort_order` · `color_slot` · `is_active` |
| `tab_import_doc_template` | Khuôn | `name` · `hs_code` · `item_category` · `is_active` · `note` |
| `tab_import_doc_template_line` | Dòng của khuôn | `template_id` · `title` · `stage_id` · `doc_type` · `planned_days` · `is_required` · `is_once_per_product` · `depends_on_line_id` · `guide` |
| `tab_po_import_doc` | Checklist thật, **gắn vào dòng hàng** (H3) | `po_id` · **`po_item_id`** · `product_code` · `template_line_id` (dấu vết, không phải khóa sống) · `title` · `stage_id` · `doc_type` · `planned_days` · `due_date` · `status` (SMALLINT) · `assignee_id` (**ID nhân sự**) · `completed_at` · `completed_by` · `depends_on_id` · `note` · `sort_order` |
| `tab_product_import_doc` | **Hồ sơ một lần** của mặt hàng (A09) | **`product_code`** (chuỗi, không phải id — D-025) · `title` · `doc_type` · `issued_date` · `expire_date` · `status` · `note` |

**Không đẻ bảng đính kèm.** `FileLink` đã có `entity` + `entity_id` + `purchase_order_id` + `doc_type` — dùng `entity = "po_import_doc"`, `entity_id` = id dòng, `purchase_order_id` = id đơn để bộ chứng từ vẫn gom đúng theo đơn.

**Trạng thái lưu SMALLINT + IntEnum** theo R2/QĐ-11 — chức năng mới, không có ngoại lệ.

⚠️ Bốn cái bẫy đã biết, ghi sẵn để khỏi vấp lại:

- Cột `String(n)` mà schema không khai `max_length` thì trả **500 chứ không phải 422**. Và `test/backend` chạy SQLite — SQLite **không ép độ dài VARCHAR**, nên kiểm ở tầng ghi DB là xanh giả, phải kiểm ở tầng schema.
- `sort_order` kiểu SMALLINT tràn ở dòng 32768 — checklist cần trần số dòng.
- `planned_days` cần trần trên hợp lý. Không có trần thì một lần gõ nhầm làm ngày hàng về nhảy sang thế kỷ sau, mà con số đó lại đi thẳng ra báo cáo cho sếp.
- `po_item_id = 0` là **một giá trị thật** (dòng chưa gắn), không được lấy làm mốc "tất cả" trong bộ lọc — dùng `-1`.

---

## 9. Phân quyền — QĐ-A sau đáp án H5

Dùng lại khóa **`purchase_order`**:

| Thao tác | Đòi quyền |
|---|---|
| Xem tab Hồ sơ nhập khẩu, xem báo cáo | `purchase_order.read` |
| Tick hoàn thành, gán người, đổi hạn, đính kèm | `purchase_order.write` |
| Sửa danh mục chặng / khuôn | `purchase_order.write` |

**H5 chốt Phòng Thu mua là người tick** — nghĩa là **không phải cấp `purchase_order` cho ai thêm cả**. Thu mua vốn đã có đủ hai quyền này. Toàn bộ phần rủi ro của bản 1.0 (*Pháp lý / Logistics sẽ nhìn thấy đơn giá*) **biến mất**, vì họ không cần vào hệ thống.

Nếu về sau muốn cho Pháp lý / Logistics tự tick thì rủi ro đó quay lại — lúc đó mới bàn tiếp, và cách giảm là **phạm vi dữ liệu** (`scope = dept`, không cấp `all`) chứ không phải khóa quyền. Ghi lại thành nợ kỹ thuật, không làm bây giờ.

---

## 10. Chia đợt

| Đợt | Nội dung | Xong là gì |
|---|---|---|
| **Đ1** | A01…A06, A09 · nền dữ liệu + danh mục chặng + khuôn (backend + màn `frontend-v2`) | Khai được khuôn KNO₃ và K₂SO₄ |
| **Đ2** | B01…B08, B11…B15, B18…B21 · tab Hồ sơ nhập khẩu trên `frontend-v2` | Lô KNO₃ thật chạy được trên hệ thống |
| **Đ3** | C01…C06 · tiến độ theo ngày + chặng chặn | Trả lời được câu *"trễ mấy ngày"* |
| **Đ4** | D01…D06, D08, D09 · màn báo cáo và 4 đồ thị | Sếp mở một màn là thấy toàn cảnh |
| **Đ5** | E01…E05 · nhắc việc | Hồ sơ không còn rơi vì quên |
| **Đ6** | F02 · bê toàn bộ sang `frontend` (thumua) | Người dùng ở bản cũ dùng được |
| **Đ7** | Phần bản 2: A07 A08 · B09 B10 B16 B17 · C07 · D07 D10 D11 · E06 | Trong đó B09/B10 là phần **logic điều kiện** khách hẹn làm sau |

Không đặt mốc ngày trong tài liệu này. Mốc nằm ở dòng CR trong `change-log-bao.md`.

---

## 11. Đáp án H1–H6 (khách chốt 12/09/2026)

| # | Câu hỏi | Đáp án | Đổi gì trong tài liệu |
|---|---|---|---|
| H1 | Tập chặng chốt là 5 hay nhiều hơn? | **Nhiều hơn và thay đổi nhiều.** Viết tổng quát rồi cộng lại. Người dùng tự định nghĩa bộ hồ sơ cần những gì, mỗi hồ sơ có thời gian tối đa bao nhiêu — kiểu danh sách việc phải làm | A02 thành **danh mục mở**. Số ngày chỉ khai ở dòng hồ sơ. Đ2/Đ3 gom theo `stage_id`, quá 8 chặng thì gom "Khác" |
| H2 | Đăng ký lưu hành phân bón là chặng thứ 6 hay một hồ sơ? | **Một hồ sơ duy nhất.** Có rồi thì tick "Đã có", **khỏi nhập thời gian**. Điều kiện kiểu *NCC xuất FOB phải có hợp đồng trước* để làm sau — **bản 1 mở hết** | Thêm A09 (hồ sơ một lần, cấp mặt hàng) + bảng `tab_product_import_doc`. **B09/B10 hạ xuống bản 2**, bản 1 chỉ cảnh báo |
| H3 | Hồ sơ gắn vào đơn hay vào mặt hàng? | **Gắn vào dòng hàng / mặt hàng** | `tab_po_import_doc` mang `po_item_id`. Kéo theo cả mục 5 và B18, B21 |
| H4 | Cho tạo checklist trên đơn nháp không? | **Cho** — danh sách giấy phép khai được từ lúc còn nháp | B19 |
| H5 | Ai là người tick? | **Phòng Thu mua** | Mục 9: rủi ro phân quyền biến mất, không cấp quyền cho ai thêm |
| H6 | Số ngày kế hoạch lấy từ đâu cho lần đầu? | **Theo báo cáo pháp lý 11/09/2026** | Số liệu mồi ở mục 12 |

---

## 12. Số liệu mồi cho lần đầu (theo H6)

Lấy từ báo cáo pháp lý 11/09/2026. Sau vài lô thì đồ thị Đ3 tự nói cho biết con số nào phải sửa.

### Khuôn "Phân bón thường" — áp cho K₂SO₄, HS 3104.21.00

| Chặng | Hồ sơ | Ngày tối đa |
|---|---|---|
| Đặt hàng & hợp đồng | Hợp đồng ngoại thương · Đặt cọc / mở L/C · Xác nhận đơn hàng | 3 |
| Sản xuất & vận chuyển | Invoice · Packing List · Vận đơn B/L · Form E (C/O) · Chứng thư hun trùng | 18 |
| Thông quan | Tờ khai hải quan · Kiểm tra chất lượng nhà nước · Nộp thuế VAT 5% | 6 |
| Về kho | Lệnh giao hàng · Biên bản giao nhận · Phiếu nhập kho | 2 |
| **Cộng** | | **29** |

Hồ sơ một lần của mặt hàng: **Giấy đăng ký lưu hành phân bón** (3÷6 tháng nếu chưa có; đã có thì tick, không tính ngày).

### Khuôn "Tiền chất thuốc nổ" — áp cho KNO₃ ≥ 98,5%, HS 3102.60.00

| Chặng | Hồ sơ | Ngày tối đa |
|---|---|---|
| **Xin giấy phép** | Đơn đề nghị · Hồ sơ năng lực · Hợp đồng nguyên tắc · **Giấy phép NK tiền chất — Bộ Công An** | **45** |
| Đặt hàng & hợp đồng | (như khuôn trên) | 3 |
| Sản xuất & vận chuyển | (như khuôn trên) + MSDS | 18 |
| Thông quan | (như khuôn trên) + **kiểm hóa 100%** | 9 |
| Về kho | (như khuôn trên) + Sổ theo dõi tiền chất | 2 |
| **Cộng** | | **77** |

Nghĩa vụ định kỳ sau khi hàng về: **báo cáo tồn kho tiền chất 6 tháng một lần** — bản 1 ghi thành một dòng hồ sơ có hạn; nhắc tự động để bản 2.

> ⚠️ Con số **45 ngày** là *ngày làm việc* theo NĐ 113/2017, tức khoảng **9 tuần lịch**. Khi tính `due_date` phải quy đổi, nếu không thì hạn tính ra sớm hơn thực tế gần 3 tuần và màn hình báo trễ oan ngay từ lô đầu.

---

## 13. Đối chiếu với bản giao diện gợi ý của khách

| Trong bản gợi ý | Xử lý |
|---|---|
| Tab *Tổng quan* — băng cảnh báo tiền chất, hai thẻ mặt hàng, mốc thời gian dự kiến, căn cứ pháp lý | **Giữ**, nối vào dữ liệu thật. Mốc thời gian chuyển thành đồ thị Đ1 · căn cứ pháp lý thành A07 |
| Tab *Hồ sơ & Quy trình* — 22 dòng, nhóm 1/2/3, chip lọc mặt hàng, nút Sửa | **Giữ gần như nguyên**, chính là nhóm B |
| Khóa hồ sơ theo tiền quyết | **Giữ ý tưởng nhưng hạ xuống bản 2** (H2). Bản 1 chỉ hiện dòng chữ chờ, vẫn cho tick |
| Tab *Tracking tiến độ* — mốc theo vị trí vật lý | **Giữ** dưới dạng cách nhóm thứ hai (B11), không phải dữ liệu riêng |
| Bản đồ tuyến đường | **Bỏ** ở bản 1 — hình vẽ chết. Thay bằng dòng chữ *"Đang ở: …"* |
| Tiến độ `2/17 hồ sơ = 12%` | **Đổi** sang công thức theo ngày (7.1) |
| `chưa có file` (chữ xám) | **Đổi** thành nút tải lên thật (B08) |
| Dựng tay cho một lô | **Đổi** thành khuôn dùng lại (nhóm A) |
| Đứng riêng, không dính đơn mua hàng | **Đổi** thành tab trên đơn nhập khẩu, gắn vào dòng hàng (mục 5) |
| Không có người phụ trách, không có hạn | **Thêm** (B06, B07) — mục VI của báo cáo pháp lý vốn đã có sẵn hai cột này |

---

## 14. Chờ bản của đồng nghiệp — những chỗ phải soi khi gộp

Ngày 12/09 đồng nghiệp đưa ảnh chụp một bản đã dựng gần xong: khối **Báo cáo thực hiện** nằm **trên màn Yêu cầu báo giá**, ngay dưới *Danh sách sản phẩm cần khảo sát*. Tài liệu này **tạm dừng** cho tới khi có commit của bản đó. Quy trình: đợi commit → gộp → rà mã nguồn → sửa tài liệu theo mã nguồn thật, không sửa trước.

### Bản đó làm đúng chỗ mà tài liệu này đang sai

**Đặt trên Yêu cầu báo giá, không phải Đơn mua hàng.** Đây là điểm mạnh, không phải chỗ lệch. Chính mục 1 của tài liệu này nói *chặng xin giấy phép 45 ngày xảy ra trước khi có đơn mua hàng* — vậy mà mục 5 lại neo checklist vào đơn, tức vẫn muộn mất 45 ngày đầu. Neo vào **dòng sản phẩm của Yêu cầu báo giá** thì việc pháp lý bắt đầu được ngay từ lúc mới có nhu cầu. Khi sửa tài liệu, **sửa mục 5 và mục 8 theo bản đó**, đừng kéo bản đó về theo tài liệu.

Mấy chỗ khác cũng khớp sẵn: giai đoạn tự khai qua nút *Thêm giai đoạn* (đúng H1) · chip lọc theo mặt hàng + nhãn `CHUNG` cho hồ sơ dùng chung (đúng B11/B12) · căn cứ pháp lý ghi thẳng vào từng dòng (A07, vốn xếp bản 2) · biểu tượng kẹp giấy để đính kèm (B08).

### Bốn chỗ phải hỏi lại khi rà mã nguồn

| # | Thấy trên ảnh | Vì sao phải hỏi |
|---|---|---|
| 1 | `2/22 hồ sơ · 9%`, mỗi giai đoạn `1/3 · 33%` | **Đang đếm theo số hồ sơ**, đúng cách đo mà mục 7.1 chỉ ra là không nói được chữ "trễ". Giấy phép 45 ngày đang được tính ngang một tờ Packing List. Xem còn cột số ngày trong cơ sở dữ liệu không — nếu có thì chỉ là đổi công thức hiển thị, rẻ; nếu chưa có thì phải thêm cột |
| 2 | Ổ khóa + chú thích *"hồ sơ khóa = chờ hồ sơ tiền quyết hoàn thành trước"* | **Đã khóa cứng**, trong khi H2 khách chốt *bản 1 mở hết, logic để sau*. Hỏi khách: giữ khóa hay hạ thành cảnh báo. Nếu giữ thì phải có chặn vòng tiền quyết (B10) — A chờ B, B chờ A thì cả hai đứng im và màn hình không nói gì |
| 3 | Hai dòng *Giấy CN đăng ký lưu hành phân bón* tách riêng cho K₂SO₄ và KNO₃ | Đây là **hồ sơ một lần cấp mặt hàng** (A09). Xem nó lưu ở cấp lô hay cấp mặt hàng — lưu ở cấp lô thì lô sau lại phải tick lại từ đầu, và nó bị tính vào tiến độ dù thực tế không tốn ngày nào |
| 4 | Ba nút *Bảng rút gọn · Vừa nội dung · Cột* ở bảng sản phẩm | Xem có phải cấu hình cột dùng chung đã có sẵn không, hay bản này tự dựng riêng một bộ. Tự dựng riêng thì sau này sửa một chỗ phải nhớ sửa hai nơi |

### Rà kỹ thuật bắt buộc (đã dính trước đây)

- `requirements.txt` có bị đổi lặng lẽ không.
- Có kèm kiểm thử không, có bài hướng dẫn chức năng không.
- Trạng thái hồ sơ lưu **SMALLINT + IntEnum** hay lưu chữ — chức năng mới không có ngoại lệ (R2/QĐ-11).
- `assignee_id` là **ID nhân sự** hay bị nhầm sang ID tài khoản.
- Đính kèm dùng lại `FileLink` hay đẻ bảng mới.
- `ENTITY_LABELS` + `ENTITY_LINKS` đã khai chưa — thiếu thì thư vẫn gửi nhưng đường dẫn rỗng và lỗi bị nuốt.
- Danh sách hồ sơ có phân trang / có trần số dòng không, và `sort_order` kiểu gì (SMALLINT tràn ở dòng 32768).
- Chạy `docker compose exec erp npm run check` trước khi kết luận xong.
