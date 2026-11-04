# Mô hình dữ liệu Sản phẩm — variant, thuộc tính động, tầng họ sản phẩm

Tài liệu thiết kế. Ghi lại **vì sao** cấu trúc Sản phẩm hiện tại như vậy, **cấu trúc bảng mới
phải như thế nào**, **hợp đồng API nào không được phá**, và **kế hoạch chuyển dữ liệu**.
Viết ra để người vào sau không "sửa lại cho đúng" rồi phá hạt dữ liệu của cả hệ.

Liên quan: `technical-design.md` · `change-log.md` (D-025) · `../tai-lieu-chuc-nang/07-danh-muc.md`

---

## 1. Nguyên tắc bất biến

> **`tab_product` là bảng VARIANT. Mỗi dòng là một quy cách cụ thể, đặt mua được, nhập kho
> được, có giá riêng. `product_code` là ĐƠN VỊ GIAO DỊCH của toàn hệ thống — bất biến, không
> đổi, không tái sử dụng.**

Đây là quyết định có chủ ý, không phải di tích. Ai thấy tên bảng là `tab_product` mà tưởng nó
là "sản phẩm cha" thì đọc mục 2 trước khi sửa bất cứ thứ gì.

---

## 2. Hiện trạng — vì sao `product_code` là hạt của cả hệ

**Không có khóa ngoại nào trỏ vào `tab_product`.** Mọi module nối với sản phẩm bằng **chuỗi
`product_code`**:

| Bảng | Cột | Ghi chú |
|---|---|---|
| `tab_purchase_request_item` | `product_code` | dòng YCMH |
| `tab_po_item` | `product_code` | dòng ĐMH |
| `tab_goods_receipt` | `product_code` | nhận hàng |
| `tab_inventory` | `product_code` | tồn kho (có index) |
| `tab_inventory_move` | `product_code` | luân chuyển kho (có index) |
| `tab_purchase_history` | `product_code` | lịch sử mua hàng (index kép với `order_date`) |
| `tab_survey_request_option` | `system_product_code` | mã hệ thống NSTM gắn cho option khảo sát |

Ngoài ra `purchase_request/service.py` khớp dòng ĐMH ngược về dòng YCMH **bằng
`product_code`** để suy tiến độ và số lượng đã đặt/đã nhận. Tức là `product_code` không chỉ là
khóa tra cứu — nó là **khóa nối nghiệp vụ giữa hai chứng từ**.

**Hệ quả:** đổi ý nghĩa của `tab_product` là đổi hạt của 7 bảng, trong đó có tồn kho và lịch
sử mua hàng. Đây là thay đổi rủi ro cao nhất có thể làm với app này.

### Dữ liệu thật đã là variant

```
NTN5132  [Nhãn] GC – V – 5132 – CTY THỦY NHI – PIM.PIM 75WP (Bột cam) – 100gr – 100
```

Mỗi khối lượng / mỗi khách một mã riêng. Không ai đặt mua "nhãn PIM.PIM" chung chung. Vấn đề
của cấu trúc hiện tại **không phải** là thiếu bảng variant, mà là **thuộc tính đang bị nhốt
trong chuỗi tên** nên không lọc/so sánh được.

---

## 3. Ánh xạ sang mô hình Saleor

Trong Saleor, `ProductVariant` là đơn vị bán duy nhất — không bỏ `Product` vào giỏ hàng được.
"Sản phẩm đơn giản" chỉ là sản phẩm có đúng 1 variant mặc định. Hệ này chạy đúng mô hình đó:

| Saleor | Hệ này | Trạng thái |
|---|---|---|
| `ProductVariant` — SKU, đơn vị giao dịch | **`tab_product`** | Đang có, 7.5k+ dòng |
| `Product` — gom nhóm, trưng bày | `tab_product_family` | **Chưa có**, xem mục 10 |
| `ProductType` — quyết định bộ thuộc tính | `tab_item_group` (Phân loại) | Đang có |
| `Attribute` / `AttributeValue` | `tab_attribute` / `tab_product_attribute` | Chưa có, xem mục 5 |

---

## 4. Quy ước kiểu dữ liệu — khi nào ID, khi nào mã, khi nào text

Áp dụng cho **bảng mới**. Không hồi tố bảng cũ (xem cảnh báo cuối mục).

### 4.1 Bốn loại khóa, dùng đúng chỗ

| Loại | Kiểu | Dùng khi | Ví dụ |
|---|---|---|---|
| **ID** | `BigInteger` | Trỏ tới **một dòng của bảng khác**. Luôn dùng ID, không bao giờ dùng tên | `item_group_id`, `attribute_id`, `product_id`, `value_option_id` |
| **Mã (slug)** | `String(50)`, ASCII, `snake_case`, UNIQUE | Khóa **đối ngoại**: header CSV, tham số URL, khóa trong script import. Phải ổn định khi đổi tên hiển thị | `tab_attribute.code = "dung_tich"` |
| **Hằng kỹ thuật** | `String(20)` + Python `StrEnum` | Từ vựng **cố định do lập trình viên định nghĩa**, người dùng không thêm được | `data_type = "text" \| "number" \| "select" \| "bool" \| "date"` |
| **Text tự do** | `String(n)` / `Text` | Người dùng gõ, không lọc chính xác | `tab_attribute.name`, `value_text` |

**Nguyên tắc rút gọn:** *người dùng thêm/sửa được → bảng riêng + ID; lập trình viên định nghĩa
cứng → hằng chuỗi ngắn; còn lại mới là text.*

### 4.2 Vì sao KHÔNG dùng `ENUM` của MySQL

Dùng `String(20)` + `StrEnum` phía Python, **không** dùng kiểu `ENUM` native:

1. Thêm một giá trị vào `ENUM` là `ALTER TABLE` — MySQL dựng lại cả bảng.
2. Alembic autogenerate xử lý thay đổi `ENUM` rất tệ, dễ sinh migration sai.
3. Cả repo **không có một cột `ENUM` nào** — tiền lệ đang chạy là chuỗi ngắn:
   `tab_purchase_history.source = "system" | "legacy"` (`String(10)`).

An toàn kiểu vẫn có đủ: `StrEnum` ở Python + validate ở Pydantic schema → sai giá trị bị chặn
ở tầng API, không cần DB gác.

### 4.3 Giá trị select: lưu ID hay lưu chữ?

**Lưu cả hai, mỗi cái một việc:**

- `value_option_id` (ID) = **khóa truy vấn**. Đổi tên "PET" thành "Nhựa PET" thì mọi sản phẩm
  vẫn trỏ đúng, không phải update hàng loạt.
- `value_text` = **bản hiển thị denormalize**. Luôn có giá trị với **mọi** kiểu dữ liệu.

Lợi ích của `value_text` luôn có: mọi chỗ hiển thị chỉ cần đọc **một cột**, không join, không
rẽ nhánh theo `data_type`. Đây là điểm giảm code nhiều nhất trong toàn thiết kế.

Đánh đổi đã biết: đổi tên một option phải chạy kèm một câu `UPDATE tab_product_attribute SET
value_text = ... WHERE value_option_id = ...`. Việc này nằm trong `service.rename_option()`,
không được để lọt.

### 4.4 Ngày tháng

Toàn repo lưu ngày bằng `String(10)` dạng `YYYY-MM-DD` (`order_date`, `completed_at`,
`invoice_date`…). Thuộc tính kiểu `date` **theo đúng lệ đó**: cất trong `value_text`, không
thêm cột `Date`. Sắp xếp chuỗi `YYYY-MM-DD` vẫn đúng thứ tự thời gian.

### 4.5 Cảnh báo — KHÔNG hồi tố các cột trạng thái đang chạy

Trạng thái nghiệp vụ trong hệ này là **chuỗi tiếng Việt có chủ ý** (`line_status == "Hủy đơn"`,
`payable.status == "Đã TT"`), ghi rõ trong `CLAUDE.md`. Đổi chúng sang ID là thay đổi xuyên
suốt: whitelist `apply_filters`, seed, báo cáo, test, dữ liệu prod đã có. **Ngoài phạm vi.**
Quy ước ở mục 4 chỉ áp cho **bảng mới**.

---

## 5. Cấu trúc bảng chi tiết

**Tổng cộng thêm 4 bảng + 1 cột.** (Bảng thứ 5 — `tab_product_family` — đang hoãn, mục 10.)

### 5.0 Sửa `tab_product` — thêm đúng 1 cột

```python
# app/modules/product/model.py
item_group_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
```

**Vì sao bắt buộc:** `tab_product.item_group` đang là **chuỗi tên**, trong khi
`tab_category_assignee.item_group_id` đã dùng **ID**. Thuộc tính gắn theo phân loại — nếu gắn
bằng tên thì đổi tên phân loại là đứt hết binding. `0` = chưa map được.

**Giữ nguyên cột `item_group` chuỗi**, không xóa: nó đang được đọc ở autofill YCMH/ĐMH, ở CSV
import/export, ở `FILTERABLE`. Hai cột sống song song, cột chuỗi là bản hiển thị.

### 5.1 `tab_attribute` — từ điển thuộc tính

```python
code:          String(50),  unique=True          # "dung_tich" — ASCII slug, khóa đối ngoại
name:          String(100)                       # "Dung tích" — hiển thị
data_type:     String(20),  default="text"       # text|number|select|bool|date
unit_label:    String(20),  default=""           # "ml", "mm", "gsm" — chỉ để hiển thị
is_filterable: Boolean,     default=True         # có hiện ở thanh lọc không
sort_order:    Integer,     default=0
is_active:     Boolean,     default=True
# + AuditMixin
```

`unit_label` **không** tham gia tính toán — hệ này không quy đổi đơn vị. Nếu sau cần quy đổi
thì đó là bảng khác, không nhét vào đây.

### 5.2 `tab_attribute_option` — giá trị chọn sẵn

```python
attribute_id: BigInteger, index=True
value:        String(100)
sort_order:   Integer, default=0
is_active:    Boolean, default=True
__table_args__ = (UniqueConstraint("attribute_id", "value"),)
```

Chỉ dùng khi `data_type = "select"`.

### 5.3 `tab_item_group_attribute` — phần "động"

```python
item_group_id: BigInteger
attribute_id:  BigInteger
is_required:   Boolean, default=False
sort_order:    Integer, default=0
__table_args__ = (
    UniqueConstraint("item_group_id", "attribute_id"),
    Index("ix_iga_group_sort", "item_group_id", "sort_order"),
)
```

Đây là bảng quyết định **form Sản phẩm hiện field gì**: chọn phân loại Chai thì hiện Dung tích;
chọn Nhãn thì hiện Kích thước + Số màu. Bảng nhỏ (vài chục đến vài trăm dòng), nạp một lần vào
cache khi mở form.

### 5.4 `tab_product_attribute` — giá trị trên từng sản phẩm

```python
product_id:      BigInteger
attribute_id:    BigInteger
value_text:      String(255),   default=""    # LUÔN CÓ — bản hiển thị mọi kiểu
value_num:       Numeric(18,4), nullable=True # number; bool lưu 0/1
value_option_id: BigInteger,    default=0     # select; 0 = không dùng
__table_args__ = (
    UniqueConstraint("product_id", "attribute_id"),      # 1 thuộc tính = 1 giá trị
    Index("ix_pa_attr_num", "attribute_id", "value_num"),
    Index("ix_pa_attr_opt", "attribute_id", "value_option_id"),
    Index("ix_pa_product", "product_id"),
)
```

Cột nào có giá trị theo từng `data_type`:

| `data_type` | `value_text` | `value_num` | `value_option_id` |
|---|---|---|---|
| `text` | chuỗi người dùng nhập | NULL | 0 |
| `number` | bản đã định dạng ("500 ml") | **500** | 0 |
| `select` | tên option ("PET") | NULL | **id option** |
| `bool` | "Có" / "Không" | **1 / 0** | 0 |
| `date` | "2026-08-08" | NULL | 0 |

**Vì sao EAV (bảng dọc) chứ không phải JSON.** Cùng lập luận đã áp cho
`tab_purchase_history.extra`: cái gì cần **lọc / sắp xếp** thì phải nằm ở cột phẳng có index.
MySQL không index được field trong JSON nếu không dựng generated column. Tách `value_num`
riêng là bắt buộc — lọc "dung tích 500–1000ml" phải so bằng số, chứ so chuỗi thì `"1000" < "500"`.

**Giới hạn đã biết của v1:** `UNIQUE(product_id, attribute_id)` nghĩa là **một thuộc tính chỉ
có một giá trị**. Thuộc tính nhiều giá trị (vd "Chứng nhận: ISO, HACCP") chưa hỗ trợ. Nếu sau
cần: bỏ unique, thêm `sort_order`, và đổi hàm gom về dạng danh sách — đổi ở đúng một chỗ.

**Đánh đổi hiệu năng:** lọc theo N thuộc tính = N truy vấn con `EXISTS`. Ở quy mô ~7.6k sản
phẩm là không đáng kể. Nếu về sau chậm thì thêm cột `tab_product.attrs_json` denormalize **chỉ
để hiển thị** — nguồn sự thật vẫn là bảng này. Chưa làm cho tới khi đo được là chậm.

---

## 6. Hợp đồng API Sản phẩm — thêm gì, giữ gì

Đây là phần trả lời câu "trả thông tin thế nào để hạn chế sửa code".

### 6.1 Luật vàng: `ProductOut` chỉ được THÊM field

> Không đổi kiểu, không đổi ý nghĩa, không bỏ field nào đang có
> (`code, name, invoice_name, legal_name, item_group, unit, hh_code, hh_name, specs, is_active, id`).

Nhờ luật này, hai chỗ tiêu thụ nặng nhất **không phải sửa dòng nào**:

- `ProductPicker.tsx` truyền **nguyên object** sản phẩm ra ngoài (`prod: p`). Thêm field vào
  `ProductOut` là nó tự mang theo.
- `PurchaseOrderDetail.tsx` đọc `p.specs`, `p.hh_code`, `p.hh_name` — vẫn đúng.

### 6.2 Field thêm vào `ProductOut`

| Field | Kiểu | Khi nào có |
|---|---|---|
| `item_group_id` | `int` | Luôn |
| `attrs` | `list[{code, name, data_type, unit_label, value_text, value_num, value_option_id, sort_order}]` | Chi tiết: luôn. Danh sách: chỉ khi `?with_attrs=1` |
| `attrs_map` | `dict[code → value_text]` | Cùng điều kiện với `attrs` — dạng phẳng cho FE render nhanh |

**Vì sao danh sách phải có cờ `with_attrs`:** màn Sản phẩm có 7.5k dòng; nhét thuộc tính vào
mọi lần gọi là phình payload vô ích cho `ProductPicker` (đang gọi `page_size=30` mỗi lần gõ).

**Nạp theo lô, không N+1** — dùng đúng khuôn đã có sẵn trong `product/controller.py` chỗ gắn
`thumbnail_url`: gom `ids` của trang rồi **một** truy vấn `WHERE product_id IN (...)`.

### 6.3 `specs` trở thành trường suy diễn — điểm mấu chốt

```
ProductOut.specs = specs (người dùng gõ tay)  nếu KHÔNG rỗng
                 = chuỗi sinh từ attrs         nếu rỗng
```

Chuỗi sinh nối theo `sort_order`, dạng `Dung tích: 500 ml · Hình dạng: Tròn`, cắt về 255 ký tự
cho khớp `POItem.spec`.

Nhờ vậy **toàn bộ đường TSKT chảy vào ĐMH không phải sửa gì**: `PurchaseOrderDetail` vẫn viết
`spec: p.specs`, backend `purchase_order/service.py` vẫn điền lại `spec` cho dòng mới còn
trống — chỉ là giá trị nay chuẩn hóa hơn. Người dùng gõ tay vào `specs` thì bản gõ tay thắng.

### 6.4 Tham số lọc theo thuộc tính

| Tham số | Ý nghĩa | Áp cho |
|---|---|---|
| `attr_<code>=<text>` | khớp chính xác `value_text` | text, select |
| `attr_<code>_opt=<id>` | khớp `value_option_id` | select (ưu tiên hơn dạng text) |
| `attr_<code>_min` / `_max` | khoảng `value_num` | number, bool, date-as-num |

Cài bằng **`EXISTS` subquery, mỗi thuộc tính một cái** — không dùng `JOIN`, vì join nhiều bảng
thuộc tính sẽ nhân dòng và làm `count()` sai.

### 6.5 CSV import/export cột động

Cột thuộc tính mang tiền tố để bộ nhập phân biệt với cột cố định:

```
ID, Phân Loại, Mã VTBB/NL, Tên VTBB/NL, …, Thông số kỹ thuật, [TT] Dung tích, [TT] Hình dạng
```

Bộ nhập hiện tại đã có hàm `pick` / `pick_has` khớp header linh hoạt và quy tắc **"chỉ ghi đè
cột có trong file"** — quy tắc đó giữ nguyên cho cột thuộc tính: cột vắng mặt thì không đụng.

---

## 7. Hợp đồng "chọn mã VTBB → tự động điền"

Hành vi người dùng phụ thuộc hằng ngày. Mọi thay đổi cấu trúc Sản phẩm **phải giữ nguyên**.

| Màn | Chọn mã VTBB thì điền | Nguồn |
|---|---|---|
| **YCMH** | Mã hàng, Tên hàng, ĐVT, Phân loại, Thời gian quy định (suy từ phân loại) | `applyProduct` — `frontend/src/pages/PurchaseRequestDetail.tsx` |
| **ĐMH** | Mã hàng, Tên hàng, Tên trên hóa đơn, ĐVT, Phân loại, Xuất xứ/TSKT ← `product.specs`, Mã HH ← `product.hh_code`, Tên HH ← `product.hh_name` | `frontend/src/pages/PurchaseOrderDetail.tsx` |
| **ĐMH (backend)** | Điền lại `spec` cho dòng **MỚI còn trống** lúc lưu — để ĐMH tạo từ YCMH cũng có TSKT (YCMH không có cột spec) | `backend/app/modules/purchase_order/service.py` |

Ba điều bất biến:

1. Cả ba đều đọc **đúng một dòng `tab_product`**, tra bằng `code`. Không join, không suy diễn.
2. Điền xong thì các ô **vẫn sửa được**; giá trị đã ghi vào chứng từ là **bản chụp** — sửa
   danh mục sau này **không** hồi tố vào chứng từ cũ. Cố ý như vậy.
3. **Thuộc tính KHÔNG chảy vào chứng từ dưới dạng cột riêng.** Chúng gộp thành **một chuỗi
   `spec`** như hôm nay.

Điều 3 là lý do chính khiến toàn bộ thiết kế này rẻ: **`tab_po_item` và
`tab_purchase_request_item` không thêm cột nào.** Nếu ngày nào đó muốn chứng từ có cột thuộc
tính riêng thì đó là một CR khác, phải cân nhắc lại từ đầu.

---

## 8. Kế hoạch chuyển dữ liệu

### M1 — `item_group_id` (migration, tự chạy trên cả 3 môi trường)

1. `op.add_column("tab_product", item_group_id BIGINT NOT NULL DEFAULT 0)` + index.
2. Backfill **ngay trong migration**: `UPDATE tab_product p JOIN tab_item_group g
   ON g.name = p.item_group SET p.item_group_id = g.id`.
3. Khớp lần hai cho biến thể hoa/thường + ngoặc vuông, dùng đúng bảng chuẩn hóa `_GROUP_CANON`
   đã có trong `product/controller.py` (đừng viết lại bảng thứ hai).
4. In ra số dòng còn `item_group_id = 0` để biết còn bao nhiêu mã chưa map.

Lùi được (`downgrade` = drop cột). Không mất dữ liệu vì cột chuỗi vẫn còn nguyên.

### M2 — 4 bảng mới (migration, không có dữ liệu)

`create_table` cho 4 bảng ở mục 5. **Phải khai model trong
`backend/app/core/all_models.py`**, nếu không `alembic --autogenerate` sẽ không thấy bảng mới.

### M3 — Nạp định nghĩa thuộc tính (SCRIPT, không phải seed)

**Không nhét vào `seed.py` / `seed_prod.py`.** Danh mục thuộc tính là dữ liệu người dùng quản
trên giao diện — nhét vào seed thì mỗi lần deploy lại đè bản người ta vừa sửa, trái D-018 (và
đúng lý do đã dẫn tới D-024 cho nội dung Trung tâm HDSD).

Cách làm: `backend/scripts/import_attributes.py`, đọc file JSON, khớp theo `code`, **chỉ thêm
và cập nhật, không xóa**, có cờ chạy thử trước rồi mới `--nap` — cùng khuôn với
`import_help_content.py`.

### M4 — Nạp giá trị thuộc tính từ tên hàng cũ (phần tốn công nhất)

Thuộc tính đang nằm trong tên: `… – 100gr – 100`. Ba bước, **không tự ghi thẳng**:

1. **Đề xuất** — script quét theo mẫu tên của từng phân loại, xuất Excel: `mã | tên hiện tại |
   thuộc tính đoán được | độ tin cậy`.
2. **Duyệt** — người phụ trách danh mục sửa/xác nhận trong Excel.
3. **Nạp** — chạy lại script ở chế độ nhập, khớp theo `mã sản phẩm + code thuộc tính`, chạy
   thử trước.

Lý do bắt buộc có bước duyệt: tên hàng của dữ liệu thật có đủ kiểu viết. Đoán sai hàng loạt
rồi ghi thẳng còn tệ hơn để trống, vì sau đó không phân biệt được đâu là giá trị người ta xác
nhận và đâu là máy đoán bừa.

### Tổng kết di trú

| Bước | Loại | Đụng dữ liệu cũ | Lùi được |
|---|---|---|---|
| M1 | Migration | Có (backfill 1 cột mới) | Có |
| M2 | Migration | Không | Có |
| M3 | Script | Không (chỉ thêm dòng mới) | Xóa dòng vừa nạp |
| M4 | Script + duyệt tay | Không (chỉ thêm dòng mới) | Xóa dòng vừa nạp |

**Không có bước nào sửa dữ liệu chứng từ.** Đây là tính chất cần giữ bằng mọi giá.

---

## 9. File phải sửa và file KHÔNG phải sửa

### Phải sửa

| File | Sửa gì |
|---|---|
| `backend/app/modules/product/model.py` | +`item_group_id` |
| `backend/app/modules/product/schema.py` | `ProductOut` +3 field, `specs` suy diễn |
| `backend/app/modules/product/service.py` | `FILTERABLE` += `item_group_id`; hàm gom thuộc tính theo lô; hàm sinh chuỗi `specs` |
| `backend/app/modules/product/controller.py` | Gắn `attrs` theo lô (theo khuôn `thumbnail_url` đã có); lọc `attr_*`; CSV cột động |
| `backend/app/modules/attribute/` | **Module mới** — 4 file model/schema/service/controller |
| `backend/app/core/all_models.py` | Khai 4 model mới |
| `backend/app/main.py` | Nối router thuộc tính |
| `frontend/src/config/cruds.tsx` + 2 page mới | 2 màn danh mục: Thuộc tính, Thuộc tính theo phân loại |
| Form + danh sách Sản phẩm | Khối field động; thanh lọc động |

### KHÔNG phải sửa — đây là mục tiêu của thiết kế

| File / bảng | Vì sao yên |
|---|---|
| `frontend/src/components/ProductPicker.tsx` | Truyền nguyên object, field mới tự đi theo |
| `PurchaseRequestDetail.tsx` — `applyProduct` | Thuộc tính không chảy vào dòng YCMH |
| `PurchaseOrderDetail.tsx` — điền dòng hàng | `p.specs` vẫn đúng, chỉ giá trị tốt hơn |
| `backend/.../purchase_order/service.py` | Vẫn điền `spec` cho dòng mới còn trống như cũ |
| `tab_po_item`, `tab_purchase_request_item` | **Không thêm cột nào** |
| `tab_inventory`, `tab_inventory_move`, `tab_purchase_history`, `tab_goods_receipt` | Không đụng tới |
| Tích hợp MISA (`misa_code`, `fg_code`) | Không đụng tới |

---

## 10. Tầng họ sản phẩm — làm khi nào và làm theo chiều nào

| Chiều | Việc phải làm | Kết luận |
|---|---|---|
| **SAI** — biến `tab_product` thành cha, thêm `tab_product_variant` làm con | Đổi grain của 7 bảng ở mục 2, sửa cả autofill và tích hợp MISA | **Cấm.** Xem mục 11 |
| **ĐÚNG** — giữ `tab_product` là variant, thêm `tab_product_family` **ở TRÊN** | 1 bảng mới + 1 cột nullable `family_code` trên `tab_product` | Không sửa dòng nào ở YCMH / ĐMH / tồn kho / lịch sử |

Chiều đúng khả thi chính vì mục 2: không ai join bằng FK, nên **thêm một tầng ở TRÊN không ai
nhìn thấy**. Backfill 1-1 không bịa dữ liệu: mỗi mã tự sinh một họ riêng
(`family_code = product_code`). Đúng "1 product = 1 variant".

**Điều kiện kích hoạt: chưa dựng cho tới khi có ít nhất 2 mã hiện hữu thực sự nên nằm chung
một họ.** Thêm bảng này hôm nay hay 6 tháng nữa **tốn y hệt nhau** — một bảng không ai tham
chiếu cộng một cột nullable không ai đọc thì không có dữ liệu nào phải chuyển đổi. Dựng sớm
thì để lại một lớp trừu tượng **rỗng**: thêm một join, thêm một màn hình không làm gì, và
người vào sau bối rối không biết "sản phẩm" là bảng nào.

### Kỷ luật phải giữ NGAY từ bây giờ

Đây là thứ duy nhất **tốn kém nếu để lâu**, quan trọng hơn cả cấu trúc bảng:

> **Không nhét thông tin cấp HỌ vào dòng variant.** Ảnh sản phẩm, mô tả chung, thương hiệu,
> tài liệu kỹ thuật chung — gõ lặp trên 20 mã anh em thì ngày tách họ phải dọn tay. Cấu trúc
> bảng thêm lúc nào cũng được; dữ liệu đã bẩn thì không.

---

## 11. Cấm làm

| Cấm | Vì sao |
|---|---|
| Thêm `tab_product_variant` bên cạnh `tab_product` | Đẻ ra hạt dữ liệu thứ hai, phá 7 bảng đang nối bằng `product_code` |
| Đổi `product_code` của mã đã phát sinh chứng từ, hoặc tái dùng mã cũ cho hàng khác | Chứng từ, tồn kho, lịch sử đều nối bằng chuỗi này: đổi là mất dấu vết, tái dùng là trộn dữ liệu hai mặt hàng |
| Đặt cột `price` lên `tab_product` | Giá thuộc về bộ (sản phẩm × NCC × thời điểm × sản lượng), đã có ở khảo sát (`price_by_volume`) và lịch sử mua hàng. Thêm cột giá là dựng nguồn sự thật thứ ba, cũ ngay hôm sau. Cần **giá kế hoạch / giá trần** thì làm bảng riêng `tab_product_price` có `valid_from`/`valid_to` |
| Làm túi `metafields` JSON chung chung | Không lọc được, không index được, không ai dám dọn |
| Bỏ field khỏi `ProductOut` hoặc đổi ý nghĩa field cũ | Phá `ProductPicker` và cả hai màn autofill cùng lúc |
| Nhét danh mục thuộc tính vào `seed.py` / `seed_prod.py` | Deploy sau sẽ đè bản người dùng vừa sửa — trái D-018 |
| Đưa thuộc tính vào chứng từ bằng join động lúc đọc | Chứng từ phải là **bản chụp**; join động làm chứng từ cũ đổi nội dung khi danh mục đổi |
| Dùng kiểu `ENUM` của MySQL cho hằng kỹ thuật | Thêm giá trị = ALTER TABLE dựng lại bảng; Alembic xử lý tệ; trái tiền lệ cả repo |

---

## 12. Lộ trình

| GĐ | Nội dung | Schema | Trạng thái |
|---|---|---|---|
| 0 | Filter động + UI cho màn Lịch sử mua hàng | — | Chưa làm |
| 1 | **M1** — `tab_product.item_group_id` + backfill | 1 cột | Chưa làm |
| 2 | **M2** — 4 bảng thuộc tính + module `attribute` + 2 màn danh mục + form Sản phẩm field động | 4 bảng | Chưa làm |
| 3 | **M3** — nạp định nghĩa thuộc tính; lọc/cột động ở danh sách Sản phẩm; CSV cột động | — | Chưa làm |
| 4 | **M4** — nạp giá trị từ tên hàng cũ (đề xuất → duyệt → nạp) | — | Chưa làm |
| 5 | `specs` suy diễn từ thuộc tính (mục 6.3) | — | Chưa làm |
| 6 | `tab_product_family` + `family_code` — **chỉ khi thỏa điều kiện kích hoạt ở mục 10** | 1 bảng + 1 cột | Hoãn |

Hai màn danh mục của GĐ 2:

- **Danh mục › Thuộc tính** — CRUD `tab_attribute` + editor lồng cho `tab_attribute_option`.
  Phần option lồng bên trong nên phải viết page riêng, không dùng `make_crud_router` thuần.
- **Danh mục › Thuộc tính theo phân loại** — ma trận gán `tab_item_group_attribute`. Tiền lệ
  sát nhất là màn *Phân công phụ trách* (`tab_category_assignee`, cũng gán theo phân loại);
  bố cục ma trận mượn `RolePermissions.tsx`.

Phân quyền: **định nghĩa** thuộc tính = quyền danh mục (admin); **giá trị** trên sản phẩm = ai
sửa được sản phẩm thì sửa được. Không tạo entity RBAC mới cho giá trị.
