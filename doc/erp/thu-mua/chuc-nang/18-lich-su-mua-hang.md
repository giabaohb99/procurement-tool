# Lịch sử mua hàng

Tài liệu mô tả **Lịch sử mua hàng** — sổ ghi lại **từng lần mua** của từng mã hàng, để lần lập đơn sau có căn cứ: lần trước mua của ai, ngày nào, số lượng bao nhiêu, giá bao nhiêu.

Vấn đề gốc: người lập đơn không nhớ lần trước mua mặt hàng này thế nào, nên mỗi lần lại đi hỏi người khác hoặc mở file Excel cũ. Giá cả thì thay đổi theo thời gian, không có mốc so sánh thì không biết NCC báo giá lần này là đắt hay rẻ.

**Không phải màn hình riêng, không có mục menu.** Đây là một khối dữ liệu dùng chung, hiện ở 3 chỗ (mục 1). Ghi vào **tự động**, không ai nhập tay.

> **Khác với báo cáo mua hàng (`08-he-thong-bao-cao.md`)**: báo cáo là số liệu tổng hợp theo kỳ để nhìn xu hướng. Lịch sử mua hàng là **từng dòng giao dịch một**, phục vụ đúng một việc: tra lại một mã hàng cụ thể lúc đang lập đơn.

---

## 1. Có ở những đâu

| Nơi | Thành phần | Hiện cái gì |
|---|---|---|
| Chi tiết **Sản phẩm** → tab *Lịch sử mua hàng* | `PurchaseHistoryTable` | Mọi lần mua của **mã hàng đó**, cột thứ 3 là **Nhà cung cấp** |
| Chi tiết **Nhà cung cấp** → tab *Lịch sử mua hàng* | `PurchaseHistoryTable` | Mọi lần mua **từ NCC đó**, cột thứ 3 là **Sản phẩm** |
| Lập **ĐMH** và **YCMH** → nút lịch sử trong ô Mã hàng | `PurchaseHistoryPickerModal` | Popup *"Lịch sử mua hàng gần nhất"* của đúng mã hàng trên dòng đó, để **lấy giá xuống dòng đang lập** |

Nút mở popup nằm **trong ô Mã hàng** của dòng hàng, chỉ hiện khi dòng **đã chọn mã hàng** và dòng đó **còn sửa được**.

---

## 2. Người dùng thấy gì

### 2a. Bảng lịch sử (tab ở chi tiết SP / NCC)

Tiêu đề ghi kèm tổng số lần mua — *"Lịch sử mua hàng (37)"*. Các cột: **Ngày đặt · Mã PO · NCC hoặc Sản phẩm · ĐVT · SL đặt · Đơn giá · VAT% · Thành tiền · Công ty**. Sắp xếp **mới nhất trước** (theo ngày đặt, cùng ngày thì bản ghi mới hơn đứng trên). 20 dòng/trang.

- **Bấm vào dòng là mở thẳng Đơn mua hàng** tương ứng. Dòng **Dữ liệu cũ** không bấm được — không tồn tại đơn nào để mở (mục 3).
- **Ngày hiển thị `dd/mm/yyyy`**. Cố ý **không đi qua `new Date`** của trình duyệt: chuỗi ngày trần (`2026-03-12`) không mang múi giờ, đưa qua `new Date` là bị quy đổi và **lệch mất 1 ngày**. Dùng hàm riêng `fmtDateStr` trong `frontend/src/utils/datetime.ts`.
- **Đơn giá giữ đủ 4 số lẻ**, tiền làm tròn về đồng (`fmtPrice` / `fmtVND`, xem CR-039 và CR-046).
- Chưa có dữ liệu thì ghi *"Chưa có lịch sử mua hàng"*, không để bảng trống trơn.

### 2b. Popup tham chiếu giá khi lập đơn

Mở từ dòng hàng đang lập, tiêu đề phụ ghi `MÃ HÀNG · Tên hàng · N lần mua đã hoàn thành`.

- **Ô tìm kiếm** ở đầu popup: tìm gần đúng theo **Mã PO / Nhà cung cấp / Công ty**. Gõ xong **300ms mới gọi API** (không bắn request mỗi ký tự), đổi từ khóa thì về trang 1.
- Mỗi dòng có nút **"Dùng giá này"**; bấm vào bất kỳ đâu trên dòng cũng chọn được.
- **`Esc` để đóng**, nền bị khóa cuộn — theo lệ chung của các popup khác trong app.
- Chân popup ghi rõ sẽ điền những gì và câu **"Đơn chưa được lưu — bấm Lưu để ghi nhận"**.

**Không lọc theo NCC của đơn đang lập** — mục đích chính là **so giá giữa các NCC**, lọc đi thì mất luôn ý nghĩa.

### 2c. Chọn một dòng thì điền gì xuống

Hai màn điền **khác nhau**, vì cấu trúc dòng hàng của chúng khác nhau:

| Màn | Điền xuống |
|---|---|
| **ĐMH** | ĐVT · SL đặt · Đơn giá · VAT% **+ 7 trường Chi tiết dòng**: tên trên hóa đơn, phân loại, xuất xứ/TSKT/chất liệu, mã HH, tên HH, kho nhận, ghi chú dòng (CR-050) |
| **YCMH** | ĐVT · SL · Đơn giá · VAT% (dòng hàng YCMH không có hộp Chi tiết dòng) |

- **Chỉ ghi đè khi lịch sử CÓ giá trị.** Ô nào trong lịch sử để trống thì **giữ nguyên** thứ đang có trên dòng — thứ đã tự điền từ danh mục Sản phẩm hoặc người dùng vừa gõ. Không xóa trắng.
- **VAT ở YCMH được kiểm trước khi gán**: chỉ nhận số `>= 0` và `< 100`, ngoài khoảng đó thì giữ VAT cũ của dòng.
- **KHÔNG bê sang** dù lịch sử có: **ngày yêu cầu có hàng · số hóa đơn · ngày hóa đơn · SL đã nhận**. Đó là dữ liệu riêng của lần mua cũ, chép sang đơn mới là sai.
- **Không tự lưu** — chỉ điền vào màn hình, người dùng còn soát lại rồi mới bấm Lưu.

---

## 3. Hai nguồn dữ liệu — đọc kỹ mục này

Bảng lịch sử chứa **hai loại dòng khác hẳn nhau về bản chất**, phân biệt bằng cột `source`:

| | `source = "system"` | `source = "legacy"` |
|---|---|---|
| Từ đâu ra | Hệ thống **tự chốt** khi một dòng ĐMH vào trạng thái **"Hoàn thành"** | **Nhập từ file Excel** `khaosatsanpham.xlsx` — các lần mua có thật của giai đoạn **trước khi có hệ thống** |
| Có ĐMH không | Có — bấm vào dòng mở được đơn | **Không hề có**, vì lúc đó chưa có hệ thống |
| Cột Mã PO | Mã đơn thật | Nhãn xám **"Dữ liệu cũ"** |
| Cột `extra` | Đầy đủ (mục 5) | Rỗng — chỉ giữ nguồn file/sheet/dòng Excel |

**Nhãn "Dữ liệu cũ" không phải lỗi thiếu dữ liệu.** Đây từng bị hiểu nhầm (CR-055: khách chụp màn hình 5 dòng đều ghi "Dữ liệu cũ" và tưởng hệ thống hỏng). Xử lý:

- Nhãn ở dạng **badge xám**, và **rê chuột lên hiện tooltip** ghi rõ: *"Lần mua trước khi dùng hệ thống — không có đơn mua hàng. Nguồn: `<file>` · `<sheet>` · dòng `<số>`"*. Không truy được sang đơn, **nhưng vẫn truy được nguồn** — đủ để mở file Excel gốc đối chiếu khi ai đó thắc mắc con số.
- Áp cho **cả bảng lịch sử lẫn popup tham chiếu giá**. Trước đó popup để ô **trống**, không nhất quán với bảng.
- Đã thử đổi tên nhãn thành *"Trước hệ thống"* rồi **quay lại "Dữ liệu cũ"** — thứ giải quyết hiểu nhầm là **tooltip**, không phải cái tên.

**Vì sao phần lớn dòng legacy không có mã PO:** chạy dò ngược trên dev cho ra **6.418 dòng legacy: khớp 61 · mơ hồ 12 · không khớp 6.345 (98,9%)**. Tức đại đa số thật sự **không tồn tại ĐMH nào để trỏ tới**. Gán mã bằng mọi giá là bịa dữ liệu.

---

## 4. Ai xem được — và vì sao NCC bị che

Hai đường vào, **hai quyền khác nhau**, cố ý:

| Đường | Quyền cần |
|---|---|
| `/api/products/{mã}/purchase-history` (tab ở SP + popup lập đơn) | `product.read` |
| `/api/suppliers/{mã}/purchase-history` (tab ở NCC) | `supplier.read` |

**Không áp `apply_scope`** — ai có quyền đọc thì thấy toàn bộ lịch sử. Đã chốt trong thiết kế: đây là **dữ liệu tham chiếu giá nội bộ**, cắt theo phạm vi thì mất đúng cái công dụng so giá.

**Che Nhà cung cấp ở màn Sản phẩm (CR-060).** Màn Sản phẩm chỉ đòi `product.read` nên **người yêu cầu** cũng vào được, mà NCC là thông tin riêng của khối thu mua. Nên với người **không có `supplier.read`**:

1. **Backend xóa `supplier_code` và `supplier_name` khỏi payload** — không phải chỉ ẩn cột ở giao diện. Ẩn ở giao diện thì gọi thẳng API vẫn đọc được nguyên tên NCC.
2. **Bỏ luôn tên NCC khỏi vế tìm kiếm.** Đây là chỗ tinh: chỉ che cột thì người dùng gõ tên một NCC vào ô tìm rồi xem có ra dòng nào không là **suy ngược ra được ai bán mã hàng đó**. Che cột thôi chưa đủ.
3. FE ẩn hẳn cột cho bảng khỏi thừa một cột rỗng — **chỉ là trang trí**, chốt chặn nằm ở server.

Đường `/api/suppliers/...` không cần chặn gì thêm: vào được là đã có `supplier.read`.

**Không có API tạo / sửa / xóa.** Bảng này chỉ đọc.

---

## 5. Trường dữ liệu

Bảng `tab_purchase_history`. **1 bản ghi = 1 dòng hàng** của ĐMH (đơn có 2 dòng thì sinh 2 bản ghi), **không phải 1 bản ghi = 1 đơn**.

Nguyên tắc chia cột: **cột phẳng = thứ được lọc / sắp xếp / hiển thị trên bảng**; phần "thông tin chung" còn lại gói vào `extra` (chuỗi JSON) — theo đúng quy ước sẵn có của repo.

### Cột phẳng

| Cột | Ý nghĩa |
|---|---|
| `po_item_id` | id dòng ĐMH gốc — **unique**, là lớp chống ghi trùng. **NULL** với dòng legacy |
| `source` | `system` (tự chốt) hoặc `legacy` (nhập từ Excel) — có index |
| `legacy_key` | khóa nguồn của dòng cũ (file + sheet + số dòng), **unique** — vừa truy ngược được, vừa chống nhập trùng. NULL với dòng hệ thống |
| `po_id` / `po_code` | đơn mua hàng gốc; `0` / rỗng với dòng legacy |
| `product_code` / `product_name` | nối với màn Sản phẩm |
| `supplier_code` / `supplier_name` | nối với màn Nhà cung cấp |
| `company_id` / `company_name` | pháp nhân mua |
| `order_date` | ngày đặt — **khóa sắp xếp mặc định** (giảm dần) |
| `unit` · `qty_order` · `price` · `vat` · `amount` | ĐVT, SL đặt, đơn giá, %VAT của dòng, thành tiền |
| `completed_at` | ngày dòng vào "Hoàn thành" |
| `extra` | phần còn lại, dạng JSON |

**Index**: 2 composite `(product_code, order_date)` và `(supplier_code, order_date)` — phủ đúng 2 màn dùng thật. Hai cột mã **không cần index đơn** vì đã là leftmost prefix của composite.

**`price` để 4 số lẻ** (`Numeric(18,4)`, migration `c1f7b9d34e02`) cho khớp `tab_po_item.price`. Nếu để 2 số lẻ thì MySQL làm tròn **ngay lúc chụp snapshot** và số lẻ mất vĩnh viễn — không cứu được.

### Bên trong `extra`

Phần Thông tin chung của đơn: `pr_code` · `misa_code` · `nspt` · `payment_terms` · `is_urgent` · `po_note` · `department`.

Phần còn lại của dòng hàng: `item_group` · `spec` · `invoice_name` · `fg_code` · `fg_name` · `qty_received` · `required_date` · `invoice_no` · `invoice_date` · `warehouse_code` · `item_note`.

Riêng dòng legacy, `extra` giữ nguồn Excel: `nguon` · `sheet` · `dong_excel` (và `linked_po_item_id` nếu đã dò được đơn).

API trả `extra` **dạng object** chứ không phải chuỗi (parse ở `PurchaseHistoryOut`, JSON hỏng thì trả `{}`) — nhờ vậy popup mới điền được phần Chi tiết dòng.

---

## 6. Ghi vào lúc nào

**Đúng một chỗ ghi**: `purchase_order/service.py::auto_advance_line`, khi một dòng hàng **chuyển sang "Hoàn thành"**. Đặt hook ở đó nên **phủ luôn luồng import Excel**, không phải đi vá thêm chỗ nào.

Ba tính chất phải giữ:

- **Bất biến** — ghi 1 lần, không sửa không xóa. **Sửa đơn về sau không làm đổi lịch sử**: đây là bản chụp *tại thời điểm mua*, đó mới là thứ có giá trị tham chiếu.
- **Idempotent** — đã có bản ghi cho `po_item_id` đó thì thoát ngay, không ghi lần hai. Cột `unique` là lớp bảo hiểm ở tầng CSDL.
- **Lỗi ghi lịch sử KHÔNG được chặn luồng tiến độ mua hàng** — bọc trong `snapshot_line_safe`, hỏng thì ghi log rồi đi tiếp. Không ai chấp nhận việc dòng hàng không chuyển được trạng thái chỉ vì sổ tham chiếu ghi trượt.

Tên công ty được **denormalize** vào bảng (không join `tab_company` lúc đọc) để bảng lịch sử **tự đứng được**, không phụ thuộc việc danh mục công ty về sau có đổi hay không.

---

## 7. Công cụ vận hành (script)

Bốn script trong `backend/scripts/`, đều **mặc định chạy thử, chỉ ghi khi có `--apply`**. Chạy dạng module trong container api:

```
docker compose exec -T api python -m scripts.<tên_script>
```

| Script | Việc |
|---|---|
| `backfill_purchase_history.py` | Dựng lại lịch sử cho **dòng ĐMH đã "Hoàn thành" từ trước** khi có tính năng (hoặc do import Misa gán thẳng cột tiến độ nên không đi qua hook). Dùng chính `snapshot_line` nên bản ghi giống hệt luồng thật |
| `import_purchase_history_legacy.py` | Đổ **lịch sử cũ từ Excel** vào bảng với `source='legacy'` |
| `backfill_legacy_po_code.py` | Dò ngược xem dòng legacy có ĐMH tương ứng không rồi **điền mã PO** |
| `import_legacy_data.py` | Nạp dữ liệu cũ nói chung |

**`backfill_purchase_history` — các cờ đáng nhớ:**

- `--stats` in phân bố *tiến độ dòng × thiếu lịch sử* để rà **trước** khi ghi.
- Mặc định chỉ nhận `progress_status = "Hoàn thành"`. Đơn cũ import từ Misa có SL nhận nhưng cột tiến độ không chuẩn nên bị bỏ qua sạch — dùng **`--include-received`** (lấy theo **thực tế đã nhận hàng**) hoặc `--status "..."` tự chỉ định.
- **Luôn loại dòng đã hủy** (tiến độ / `line_status` = "Hủy đơn", hoặc đơn `status = cancelled`), kể cả khi đã lỡ nhận hàng.
- `completed_at` **suy ra theo dữ liệu, không đóng dấu ngày chạy script**.
- **Đường lùi**: `--csv` xuất danh sách sẽ ghi; khi chạy `--apply` file này mang thêm cột `history_id` và chính là **vé hoàn tác** — `--undo <file>` xóa đúng các bản ghi lần chạy đó tạo.

**`backfill_legacy_po_code` — cách khớp:**

- Bắt buộc **cùng mã NCC + cùng mã sản phẩm**, đơn không bị hủy.
- Chấm điểm: **ngày đặt lệch ít nhất** → rồi tới **SL đặt lệch ít nhất**. Ngưỡng ngày mặc định 30 (`--days`).
- **Nhiều ứng viên bằng điểm nhau thì BỎ QUA** và liệt kê là "mơ hồ" — không đoán bừa.
- Chỉ ghi `po_id` / `po_code` + vết `extra.linked_po_item_id`. **KHÔNG đụng `po_item_id`** — cột đó unique và dành cho dòng `source='system'`; gán vào sẽ đụng khóa khi ĐMH đó cũng đã tự chốt lịch sử.
- `--clear --apply` gỡ lại mã PO đã gán; `--delete-dup` dọn dòng legacy trùng với lịch sử hệ thống (**chỉ xóa khi trùng cả SL và đơn giá**).

**Cảnh báo đã gặp thật:** 61 dòng legacy "khớp được" trên dev thì đều khớp vào dòng ĐMH **đã có lịch sử tự chốt**. Gán mã PO cho chúng sẽ khiến **mỗi lần mua hiện 2 dòng cùng mã PO** — tệ hơn là để trống. Nên **không chạy `--apply`** trong tình huống đó.

---

## 8. Lịch sử thay đổi chính

| CR | Nội dung |
|---|---|
| **CR-040** | Ra đời: bảng `tab_purchase_history`, 2 tab hiển thị, 2 endpoint, popup tham chiếu giá, và cột `source`/`legacy_key` cho dữ liệu cũ |
| **CR-046** | Vá sót của CR-041: `price` nới lên 4 số lẻ (trước bị làm tròn còn 2 ngay lúc chụp) |
| **CR-050** | Popup điền luôn 7 trường Chi tiết dòng, nhờ schema parse `extra` ra object |
| **CR-051** | `--include-received` / `--status` / `--stats` / `--undo` cho backfill; thêm script dò mã PO cho dòng legacy |
| **CR-055** | Nhãn "Dữ liệu cũ" thành badge + tooltip chỉ nguồn Excel; ngày đổi sang `dd/mm/yyyy` bằng `fmtDateStr`; thêm `--delete-dup` |
| **CR-060** | Che NCC ở màn Sản phẩm cho người không có `supplier.read` — cả payload lẫn vế tìm kiếm |
| **CR-061** | Điền bù "Xuất xứ / TSKT / chất liệu" cho `extra.spec` của dòng hệ thống còn trống (**không đụng dòng legacy** — dán thông số hôm nay lên lần mua năm xưa là bịa dữ liệu) |

---

## 9. Quyết định đã chốt

| Quyết định | Lý do |
|---|---|
| 1 bản ghi = **1 dòng hàng**, không phải 1 đơn | Người ta tra giá theo **mã hàng**, không tra theo đơn. Gộp theo đơn thì mỗi lần xem lại phải bóc dòng ra |
| **Snapshot bất biến**, sửa đơn không làm đổi lịch sử | Giá trị của sổ này nằm ở chỗ nó ghi **đúng cái đã xảy ra lúc đó**. Cho nó chạy theo đơn thì không còn là lịch sử |
| Chốt tại `auto_advance_line` chứ không ở controller | Một chỗ ghi duy nhất, và **phủ luôn luồng import Excel** — không phải nhớ vá thêm chỗ nào |
| Lỗi ghi lịch sử **không** chặn luồng tiến độ | Sổ tham chiếu hỏng thì sửa sau; chặn dòng hàng chuyển trạng thái là chặn việc thật của người dùng |
| Denormalize tên NCC / SP / công ty vào bảng | Bảng tự đứng được, không phụ thuộc danh mục về sau đổi tên hay xóa |
| Cột phẳng cho thứ lọc/sắp xếp, phần còn lại vào `extra` JSON | Không đẻ 18 cột chỉ để hiển thị tham khảo; nhưng cái nào cần index thì phải là cột thật |
| **Không** `apply_scope` cho lịch sử | Đây là dữ liệu tham chiếu giá nội bộ; cắt theo phạm vi là mất đúng công dụng so giá |
| Che NCC **ở backend**, không chỉ ẩn cột | Ẩn ở giao diện thì gọi thẳng API vẫn đọc được nguyên tên |
| Che NCC thì **bỏ luôn khỏi ô tìm kiếm** | Gõ tên NCC rồi xem có ra dòng nào là suy ngược ra được ai bán mã hàng đó — che cột thôi chưa đủ |
| Popup **không lọc theo NCC** của đơn đang lập | Mục đích chính là so giá **giữa các** NCC |
| Popup **không tự lưu**, chỉ điền vào màn hình | Giá cũ là gợi ý, không phải quyết định. Người lập đơn còn phải soát |
| Chỉ ghi đè ô nào lịch sử **có** giá trị | Ô trống trong lịch sử mà ghi đè xuống là **xóa trắng** thứ vừa tự điền từ danh mục SP |
| Không bê ngày cần hàng / số & ngày hóa đơn / SL đã nhận | Dữ liệu riêng của lần mua cũ, chép sang đơn mới là sai ngay từ đầu |
| Giữ dòng **legacy** trong cùng một bảng, phân biệt bằng `source` | Người dùng tra giá không quan tâm nó đến từ đâu; tách 2 bảng thì mọi truy vấn phải union |
| Dòng legacy **để trống mã PO** thay vì đoán | 98,9% thật sự không có ĐMH nào tồn tại. Gán bừa là bịa dữ liệu có vẻ đáng tin |
| Nhãn giữ tên **"Dữ liệu cũ"**, giải quyết bằng **tooltip** | Đã thử đổi thành "Trước hệ thống" rồi quay lại: thứ chữa hiểu nhầm là câu giải thích, không phải cái tên |
| Tooltip chỉ **file · sheet · số dòng Excel** | Không truy được sang đơn thì ít nhất phải truy được **nguồn**, để đối chiếu khi có người thắc mắc con số |
| Ngày định dạng **không đi qua `new Date`** | Chuỗi ngày trần không mang múi giờ; quy đổi timezone là lệch mất 1 ngày |
| Mọi script mặc định **chạy thử**, phải `--apply` mới ghi | Đây là dữ liệu lịch sử — ghi sai thì không có người dùng nào phát hiện giúp |
| `backfill` có `--undo` bằng chính file CSV đã xuất | Script chỉ INSERT nên không mất dữ liệu, nhưng ghi nhầm thì phải gỡ được đúng lần chạy đó |
| CR-061 **không** điền TSKT cho dòng legacy | Dán thông số kỹ thuật hôm nay lên lần mua năm xưa là bịa dữ liệu |

---

## 10. Lần rà soát gần nhất

**2026-08-11** — viết mới, đối chiếu trực tiếp với mã nguồn:

`backend/app/modules/purchase_history/` (`model.py` · `schema.py` · `service.py` · `controller.py`) · `frontend/src/components/PurchaseHistoryTable.tsx` · `PurchaseHistoryPickerModal.tsx` · `frontend/src/pages/PurchaseOrderDetail.tsx` (`applyHistory`) · `PurchaseRequestDetail.tsx` (`applyHistory`) · `SupplierDetail.tsx` · `frontend/src/config/cruds.tsx` (tab ở Sản phẩm) · 4 script trong `backend/scripts/`.
