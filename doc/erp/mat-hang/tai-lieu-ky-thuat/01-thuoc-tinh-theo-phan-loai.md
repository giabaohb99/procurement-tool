# THUỘC TÍNH THEO PHÂN LOẠI MẶT HÀNG — PHÂN TÍCH TỪ DANH MỤC VTBB ĐANG DÙNG

| | |
|---|---|
| Bản | 1.1 — 02/11/2026 (phân tích + kiến trúc, **chưa làm**) |
| Câu hỏi | Mỗi phân loại mặt hàng có bộ thuộc tính khác nhau (chai có dung tích, cổ chai; thùng có kích thước thùng, số lớp carton…). Thiết kế theo dạng đó được không? |
| Nguồn | Sheet danh mục VTBB đang dùng (tab DM CHAI, DM THÙNG, DM TÚI/NHÃN, QUY TẮC ĐẶT MÃ…), [mô hình dữ liệu sản phẩm](mo-hinh-du-lieu-san-pham.md) mục 5–8, [nghiên cứu mặt hàng](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) |

---

## 1. Kết luận

**Được, và thiết kế này đã có sẵn, đã duyệt** ở tài liệu mô hình dữ liệu sản phẩm mục 5. Nó đúng dạng *thuộc tính động theo phân loại*: chọn phân loại **Chai** thì form hiện Dung tích, Cổ chai, Màu sắc…; chọn **Thùng** thì hiện Kích thước thùng, Số lớp, Cán màng…. Chưa làm vì các giai đoạn M1–M4 chưa chạy.

Bốn bảng, không đụng luật `tab_product` là bảng SKU:

| Bảng | Vai trò | Ví dụ |
|---|---|---|
| `tab_attribute` | Từ điển thuộc tính dùng chung toàn hệ, có kiểu dữ liệu | `co_chai` (chọn), `dung_tich` (số, ml), `mau_sac` (chọn), `kich_thuoc_thung` |
| `tab_attribute_option` | Giá trị chọn sẵn cho thuộc tính kiểu chọn | Cổ chai: 28, 35, 38, 43; Chất liệu: PET, HDPE, Carton 5 lớp |
| `tab_item_group_attribute` | **Phần động**: phân loại nào dùng thuộc tính nào, bắt buộc không, thứ tự | Chai → dung tích, trọng lượng, cổ chai, hình dạng, màu, chất liệu |
| `tab_product_attribute` | Giá trị thuộc tính của từng mã | `CPT0234`: cổ 44, 500 ml, 45 g, tròn, trắng, PET |

So với ERPNext: ERPNext gắn thuộc tính vào **mẫu mặt hàng** (Item Template) rồi sinh biến thể. Bên mình gắn vào **phân loại**, vì mã VTBB đã là biến thể sẵn (mỗi mã là một SKU). Họ sản phẩm (tầng cha) để sau, đặt **ở trên** theo đúng luật.

---

## 2. Ánh xạ từ sheet đang dùng

### 2.1. Chai và nắp (tab DM CHAI)

| Cột trong sheet | Thuộc tính | Kiểu | Ghi chú |
|---|---|---|---|
| Dung tích | `dung_tich` | Số (ml) hoặc khoảng | Sheet ghi khoảng *450ml-500ml*: lưu hai số `dung_tich_min`, `dung_tich_max`, hoặc một ô chọn *khoảng dung tích*. Đề xuất hai số để lọc được |
| Kích thước / Trọng lượng | `trong_luong` | Số (g) | 40 g, 45 g, 4,3 g, 6,3 g |
| Cổ chai | `co_chai` | Chọn | 35, 43…; **dùng chung cho chai và nắp** để ghép nắp hợp chai |
| Màu sắc | `mau_sac` | Chọn | Nắp đang ghi *Chai Cam, nắp đỏ*: tách thành màu nắp và *dùng cho chai màu* |
| Chất liệu | `chat_lieu` | Chọn | Chai PET, Nắp PET, HDPE |
| Hình dạng | `hinh_dang` | Chọn | Tròn, vuông — hiện chỉ có trong tên viết tắt, nên tách ra |
| Khách hàng / Thương hiệu | `thuong_hieu` | Chọn | Dùng chung, IDA, DC…; về sau có thể lên tầng họ sản phẩm |
| Sử dụng cho sản phẩm | `dung_cho_sp` | Chọn hoặc chữ | 3.6… (mã quy cách thành phẩm) |
| Tên viết tắt | — | **Sinh tự động** | Theo mẫu của phân loại, ví dụ `Chai PET {hinh_dang} {co_chai} {dung_tich} {mau_sac}` |

### 2.2. Thùng carton (tab DM THÙNG)

| Cột trong sheet | Thuộc tính | Kiểu | Ghi chú |
|---|---|---|---|
| Kích thước / Kích thước thùng | `thung_dai`, `thung_rong`, `thung_cao` | Ba số (cm) | Sheet ghi *62.5x38.5x20* lẫn chữ *KT DRC*; tách ba số để lọc và so trùng |
| (cột số) | `co_chai` | Chọn | Thùng dùng cho chai cổ 35 hoặc 43 — cùng thuộc tính với chai |
| Màu sắc | `mau_sac` | Chọn | Dùng chung từ điển màu |
| Chất liệu | `chat_lieu` | Chọn | Carton 5 lớp cán màng — có thể tách `so_lop` (số) và `can_mang` (có/không) |
| Ghi chú *Đang đóng SP 3.6*, *Citizen, Chito* | `dung_cho_sp` | Chọn nhiều hoặc chữ | Sản phẩm đóng bằng thùng này |
| Tình trạng khai báo | — | Không phải thuộc tính | Là trạng thái của mã, để cột riêng hoặc bỏ |
| *Tăng chiều cao 2 cm từ 6/10/22* | — | Không phải thuộc tính | Đổi kích thước là **mã mới** (SKU khác), hoặc ghi lịch sử thay đổi; không sửa đè thuộc tính của mã cũ |

### 2.3. Phân loại khác (gợi ý, cần người phụ trách danh mục xác nhận)

| Phân loại | Thuộc tính gợi ý |
|---|---|
| Nhãn, túi | Kích thước (dài × rộng), chất liệu màng, số màu in, kiểu in, dùng cho sản phẩm, thương hiệu |
| Nguyên liệu | Hàm lượng hoạt chất (%), dạng (bột, hạt, lỏng), quy cách bao (kg/bao), xuất xứ, có hạn dùng |
| Thành phẩm | Quy cách (ml, kg), số đăng ký lưu hành, thương hiệu, đóng thùng bao nhiêu |

---

## 3. Lợi ích khi làm

- **Form tự đổi theo phân loại**, không phải thêm cột vào bảng sản phẩm mỗi khi có loại hàng mới.
- **Lọc và tìm theo thuộc tính**: *chai cổ 43, 500 ml, trắng*; *thùng dài 60–63 cm*.
- **Ghép phụ kiện hợp nhau** qua thuộc tính dùng chung: nắp cổ 43 cho chai cổ 43, thùng cho chai cổ 35.
- **Tên viết tắt sinh tự động** theo mẫu, hết cảnh mỗi người viết một kiểu (*Chai PET tròn 35 500ml trắng* và *Chai Pet 35 tròn trắng 500*).
- **Cảnh báo trùng mã**: cùng phân loại, cùng bộ thuộc tính là nghi trùng trước khi tạo mã mới.
- Cột `specs` của sản phẩm thành trường **suy diễn** từ thuộc tính (đã có trong thiết kế mục 6.3).

---

## 4. Các điểm đã chốt (02/11/2026)

| # | Điểm | Chốt |
|---|---|---|
| 1 | Ai sửa từ điển thuộc tính | Ai có quyền sửa sản phẩm (`product.write`) thì sửa được thuộc tính và giá trị chọn. Không thêm khóa quyền mới |
| 2 | Thuộc tính bắt buộc | Chưa cần. Khi tạo mã, bộ thuộc tính cấu hình sẵn cho phân loại được **gán vào luôn** (ô trống để điền), mã nào cũng thêm hoặc bỏ được |
| 3 | Dung tích | **Luôn là khoảng** (min, max). Một giá trị thì min = max, ví dụ 1 lít → 1000–1000 ml |
| 4 | Đổi quy cách | Dùng thay được cho nhau thì giữ mã + ghi lịch sử; không thay được thì tạo mã mới (mục 4a). Tài liệu trước, chưa làm |
| 5 | Thương hiệu / khách hàng | Là **thuộc tính**, nhưng kiểu **liên kết** tới danh mục có sẵn (`tab_brand`, pháp nhân, NCC, mã thành phẩm) để tìm và báo cáo được, không phải chữ gõ tay |
| 6 | Nạp dữ liệu | Chưa làm. **Chốt kiến trúc trước**, ổn rồi mới đồng bộ dữ liệu |

## 4a. Đổi quy cách là gì

Sheet DM THÙNG có dòng ghi *Tăng chiều cao 2 cm từ 6/10/22*: cùng một mã thùng, trước ngày đó cao 20 cm, sau đó cao 22 cm. Thuộc tính chỉ lưu **giá trị hiện tại**, nên nếu sửa thẳng 20 → 22 thì các đơn mua, phiếu nhận hàng, tồn kho **trước** ngày đó mở ra cũng thấy 22 cm — sai lịch sử.

Có ba cách:

| Cách | Làm gì | Được | Mất |
|---|---|---|---|
| A. Sửa thẳng trên mã cũ | Đổi 20 → 22 | Nhanh, không phải đổi mã ở YCMH, tồn kho | Mất lịch sử quy cách cũ |
| B. Tạo mã mới | Mã cũ ngưng dùng, mã mới mang 22 cm | Lịch sử đúng tuyệt đối, tồn kho cũ và mới tách bạch | Phải chuyển người dùng sang mã mới; báo cáo phải gom hai mã |
| C. Giữ mã, ghi lịch sử | Sửa trên mã cũ, hệ thống tự lưu *giá trị cũ, giá trị mới, ngày đổi, ai đổi* | Không đổi mã, vẫn tra được quy cách tại một ngày bất kỳ | Thêm một bảng lịch sử |

Đề xuất luật: **dùng thay được cho nhau thì giữ mã + ghi lịch sử (C); không thay được thì tạo mã mới (B)**. Ví dụ thùng cao thêm 2 cm vẫn đóng được cùng sản phẩm → C; nắp đổi cổ 35 sang 43 thì không lắp được chai cũ → B. Cách C làm sẵn trong thiết kế (bảng lịch sử giá trị thuộc tính), nên chọn luật nào sau này cũng không phải sửa cấu trúc.

---

## 4b. Chốt 02/11/2026: phân loại chỉ là bộ GỢI Ý

- Chọn phân loại thì form **tự gán sẵn** bộ thuộc tính mặc định của phân loại đó (cho tiện), nhưng **từng mã được thêm hoặc bỏ thuộc tính** — vì cùng một loại vẫn có mã mang thuộc tính khác nhau. `tab_item_group_attribute` vì thế chỉ là *bộ gợi ý*, không phải ràng buộc; giá trị thật nằm ở `tab_product_attribute` và mã nào gắn thuộc tính nào cũng được.
- Thuộc tính và giá trị chọn **tạo sẵn trước** (kèm dữ liệu thử) để người dùng chỉ chọn, không gõ tự do; thêm giá trị mới thì qua người giữ danh mục.

## 4c. Mã hàng hóa và tên trên hóa đơn — KHÔNG làm thuộc tính

| Trường | Đang có | Cách xử lý |
|---|---|---|
| Mã VTBB/NL (`code`) | Có | **Giữ nguyên, không sinh từ thuộc tính.** Mã là chìa nối 7 bảng nên không được đổi; nếu nhét thuộc tính vào mã thì sửa thuộc tính sẽ đòi đổi mã. Mã mới cấp theo quy tắc đặt mã: tiền tố theo phân loại + số chạy (ví dụ `CPT0234`) |
| Tên VTBB (`name`) | Có | Có thể **gợi ý sinh từ mẫu** của phân loại khi tạo mã mới, người dùng sửa lại được |
| Tên trên hóa đơn (`invoice_name`) | Có | **Ô chữ riêng**, không sinh từ thuộc tính: đây là chữ in trên hóa đơn VAT của NCC, phải khớp hóa đơn để đối chiếu. Mặc định gợi ý bằng tên VTBB, người dùng sửa |
| Tên pháp lý (`legal_name`) | Có | Ô chữ riêng, giống tên trên hóa đơn |
| Mã HH / Tên SP (`hh_code`, `hh_name`) | Có | Thuộc tầng thành phẩm, giữ nguyên |

Về sau, nếu **mỗi NCC ghi một tên khác nhau** cho cùng một mã, thêm bảng *tên hàng theo NCC* (mã hàng + NCC + tên trên hóa đơn của NCC đó), tương tự Item Supplier của ERPNext; ô `invoice_name` trên mã hàng khi đó là tên mặc định.

---

## 5. Kiến trúc để sửa gì cũng không phải sửa mã

Mục tiêu: thêm thuộc tính, đổi tên, đổi bộ gợi ý của phân loại, đổi mẫu tên… đều là **sửa dữ liệu trên màn hình**, không migration, không sửa mã nguồn.

### 5.1. Mười luật

1. **Thuộc tính là dữ liệu, không phải cột.** Thêm *Cổ chai* = thêm một dòng `tab_attribute`. Bảng sản phẩm không bao giờ thêm cột vì một thuộc tính mới.
2. **Mã nguồn chỉ biết KIỂU, không biết TỪNG thuộc tính.** Bộ kiểu cố định, nhỏ:

   | Kiểu | Lưu ở | Ví dụ |
   |---|---|---|
   | `text` | `value_text` | Ghi chú quy cách |
   | `number` | `value_num` | Trọng lượng 45 g |
   | `range` | `value_num`, `value_num_max` | Dung tích 450–500 ml; 1 lít = 1000–1000 |
   | `select` | `value_option_id` | Cổ 43, màu trắng |
   | `multi_select` | nhiều dòng `value_option_id` | Dùng cho chai cổ 35 và 43 |
   | `bool` | `value_num` 0/1 | Có cán màng |
   | `ref` | `value_ref_id` + `ref_entity` của thuộc tính | Thương hiệu → `tab_brand`; pháp nhân; NCC; thành phẩm |

   Kiểu `ref` là thứ làm cho *thương hiệu, khách hàng* nối được sang phân hệ khác để tìm và báo cáo. Danh sách `ref_entity` được phép khai ở một sổ đăng ký trong mã (thêm danh mục mới = thêm một dòng sổ).
3. **Lưu theo id hoặc mã, hiển thị theo nhãn.** Giá trị chọn có `code` cố định + `label` sửa được; đổi *Trắng* thành *Trắng sữa* không đụng dữ liệu đã lưu.
4. **Số lưu theo đơn vị gốc.** Thuộc tính có `base_unit` (ml, g, cm); người dùng gõ *1 lít* thì quy ra 1000 ml khi lưu. Lọc và so trùng luôn đúng dù người nhập dùng đơn vị nào.
5. **Bộ thuộc tính của phân loại là MẪU, chép khi tạo mã.** `tab_item_group_attribute` chỉ dùng lúc tạo mã (gán sẵn ô trống). Sửa mẫu về sau không động vào mã đã có; muốn áp lại cho mã cũ thì có nút *Áp bộ mẫu* chạy chủ động.
6. **Mẫu chữ cũng là dữ liệu.** Mẫu tên viết tắt, mẫu gợi ý tên VTBB lưu ở phân loại dạng `Chai PET {hinh_dang} {co_chai} {dung_tich}`; đổi mẫu không phải sửa mã.
7. **Ngưng dùng, không xóa.** Thuộc tính hoặc giá trị đang có mã dùng thì chỉ cho tắt (`is_active`), xóa bị chặn bằng `reference_guard` sẵn có.
8. **Một cửa đọc ghi.** Mọi nơi (form, nhập Excel, MCP / trợ lý AI, báo cáo) gọi chung một service `get_attributes / set_attributes`; kiểm kiểu, quy đơn vị, ghi lịch sử nằm một chỗ.
9. **Tìm và lọc chung một kiểu.** API danh sách sản phẩm nhận `attr.<mã thuộc tính>=…` (bằng, trong khoảng, nằm trong danh sách) cho mọi thuộc tính; bảng giá trị có chỉ mục theo `(attribute_id, value_num)` và `(attribute_id, value_option_id)`. Thêm thuộc tính là lọc được ngay.
10. **Ghi lịch sử mọi thay đổi giá trị** (bảng `tab_product_attribute_log`: mã, thuộc tính, giá trị cũ, giá trị mới, ai, lúc nào). Đây là nền cho luật đổi quy cách ở mục 4a.

### 5.2. Bảng sau khi bổ sung

| Bảng | Cột chính (bổ sung so với mục 1 in đậm) |
|---|---|
| `tab_attribute` | code, name, data_type, **base_unit**, **ref_entity**, is_filterable, sort_order, is_active |
| `tab_attribute_option` | attribute_id, **code**, label, sort_order, is_active |
| `tab_item_group_attribute` | item_group_id, attribute_id, sort_order, **default_option_id** (bỏ is_required theo chốt 2) |
| `tab_item_group` (có sẵn) | **name_template**, **short_name_template** |
| `tab_product_attribute` | product_id, attribute_id, value_text, value_num, **value_num_max**, value_option_id, **value_ref_id** |
| `tab_product_attribute_log` | **bảng mới**: product_id, attribute_id, old_value, new_value, changed_by, changed_at |

### 5.3. Chỗ phải giữ CỨNG (cố ý)

- **Mã hàng `code`** không bao giờ sinh từ thuộc tính, không đổi (mục 4c).
- **Thuộc tính mang nghiệp vụ** (ví dụ *cổ chai* để ghép nắp với chai) không gọi thẳng bằng chữ `co_chai` trong mã, mà qua một cấu hình *thuộc tính dùng để ghép* lưu trong cài đặt; đổi tên mã thuộc tính không làm gãy phép ghép.
- **Báo cáo nặng** (gom theo thương hiệu hàng nghìn mã) đọc qua một bảng phẳng làm sẵn hoặc cột `specs` suy diễn, không ghép bảng giá trị mỗi lần — tránh chậm, cái yếu cố hữu của kiểu lưu thuộc tính động.

### 5.4. Cách kiểm kiến trúc trước khi nạp dữ liệu

Viết bài kiểm theo **kiểu**, không theo từng thuộc tính: mỗi kiểu một bộ (lưu, đọc, lọc, quy đơn vị, ghi lịch sử). Rồi chạy thử trên một nhóm nhỏ dữ liệu thử (5 chai, 5 nắp, 5 thùng): thêm thuộc tính mới, đổi nhãn giá trị, đổi mẫu tên, tắt một giá trị — tất cả phải chạy **không sửa một dòng mã**. Qua được thì mới tới đồng bộ dữ liệu thật.

---

## 6. Vị trí trong kế hoạch

Thuộc việc **MH-2.1 → MH-2.3** của [nghiên cứu mặt hàng](../nghien-cuu/00-nghien-cuu-mat-hang-erpnext.md) mục 6 (M2, M3, M4 của tài liệu mô hình dữ liệu), sau MH-1.2 (`item_group_id`). Không chặn sổ kho; làm song song với giai đoạn 2–3 của [báo cáo 12](../../../plans/12-muc-do-module-kho-mat-hang-va-ke-hoach.md).
