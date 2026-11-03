# NGHIÊN CỨU MẶT HÀNG (ITEM): ERPNEXT V16 SO VỚI ERP DEGO

| | |
|---|---|
| Bản | 1.0 — 02/11/2026 |
| Mục đích | Hiểu ERPNext quản mặt hàng thế nào, đối chiếu với ERP DEGO, chấm tỷ lệ phủ và lập kế hoạch theo nấc cho việc làm kho |
| Mốc so sánh | ERPNext trên site học `erpnext.degoholding.vn` (container `erpnext-hoc-backend-1`, `__version__` = `16.53.0`, site `frontend`); DocType JSON và `item.py` đọc thẳng trong container; docs.erpnext.com mục Stock (Item, Item Variants, Item Price, UOM) |
| Mã soát | nhánh `erp-v2` ngày 02/11/2026 (commit `601ec718`): `backend/app/modules/product`, `catalog`, `supplier`, `survey`, `purchase_history`, `inventory`, `category_assignee`; v2 `frontend-v2/src/modules/production`, `inventory` |
| Số đo dữ liệu | DB local (bản sao gần prod, 6.803 mã) và site học (7.004 mã đồng bộ từ ERP DEGO); chỉ chạy câu đọc |
| Đọc kèm | [`mo-hinh-du-lieu-san-pham.md`](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) (luật bất biến, BẮT BUỘC) · [11 Độ phủ thu mua, kho](../nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) · [10 Nghiệp vụ kho](../nghien-cuu/10-nghiep-vu-kho.md) · [00 Kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md) |

## Mục lục

1. [Kết luận trong một trang](#1-kết-luận-trong-một-trang)
2. [ERPNext làm mặt hàng thế nào](#2-erpnext-làm-mặt-hàng-thế-nào)
3. [ERP DEGO hiện có gì](#3-erp-dego-hiện-có-gì)
4. [Bảng fit-gap và tỷ lệ phủ](#4-bảng-fit-gap-và-tỷ-lệ-phủ)
5. [Đề xuất cho DEGO](#5-đề-xuất-cho-dego)
6. [Kế hoạch theo nấc](#6-kế-hoạch-theo-nấc)
7. [Câu cần chủ dự án chốt](#7-câu-cần-chủ-dự-án-chốt)

---

## 1. Kết luận trong một trang

- Tính trên **38 chức năng** của mặt hàng (không tính số serial, xem mục 4), ERP DEGO phủ **14 / 38 = 37 %** so với ERPNext v16. Tài liệu 11 chấm cả danh mục mặt hàng là một dòng **Có**; bản này soi kỹ hơn nên thấp hơn nhiều.
- Phần **định danh** làm tốt (mã bất biến, tên hóa đơn, ảnh, nhập file, chặn xóa khi còn chứng từ, lịch sử mua ngay trên mặt hàng). Phần **phục vụ kho** gần như trống: không quy đổi đơn vị, không biến thể hay thuộc tính, không cờ loại hàng, không lô hay hạn dùng, không mức đặt hàng lại.
- **Ba chỗ hở lớn nhất:**
  1. **Đơn vị tính.** **94 %** mã (6.424 / 6.803) để trống ĐVT; không có quy đổi. Khi đồng bộ sang ERPNext, 6.420 mã phải nhận ĐVT tạm `Nos`. Sổ kho không thể chạy đúng khi không biết một dòng tồn đang đếm bằng gì.
  2. **Thuộc tính và biến thể.** Quy cách bị nhốt trong chuỗi tên (`[Nhãn] GC - II - 24 - Aqua Gold ... 1kg -25`); cột `specs` có nhưng **0 mã** điền. Thiết kế thuộc tính đã duyệt từ lâu ở tài liệu mô hình sản phẩm mục 5 nhưng **chưa dựng**.
  3. **Cờ kho trên mặt hàng.** Không phân biệt hàng tồn kho, phi kho, dịch vụ, tài sản; không lô, hạn dùng (phân bón, hóa chất gần như bắt buộc); không mức đặt hàng lại.
- **Đề xuất chính:** giữ nguyên luật `tab_product` là bảng SKU. Học ERPNext ở **bảng con quanh mặt hàng** (quy đổi đơn vị, mã hàng của NCC, mức đặt lại, giá kế hoạch có hiệu lực), **không** chép mô hình mẫu biến thể là một dòng Item. Việc đầu tiên rẻ nhất và quyết định nhất là **dọn ĐVT tồn kho** theo khuôn đề xuất, duyệt, nạp rồi khóa ĐVT sau phát sinh kho đầu tiên.

---

## 2. ERPNext làm mặt hàng thế nào

ERPNext coi **Item** là một chứng từ lớn (khoảng 80 trường và 9 bảng con) đặt tên theo `item_code`. Mọi chứng từ mua, bán, kho nối vào Item bằng khóa Link là `item_code`. Phần dưới đi từng khái niệm theo cùng một khuôn: nó là gì, dùng khi nào, trường chính, ràng buộc.

### 2.1. Item: mặt hàng

| | |
|---|---|
| **Là gì** | Một thứ mua, bán, sản xuất hoặc giữ trong kho được. Đơn vị giao dịch trên mọi chứng từ |
| **Dùng khi** | Luôn luôn: không có Item thì không lập được Material Request, Purchase Order, Purchase Receipt |
| **Trường chính** | `item_code` (bắt buộc, duy nhất, là tên bản ghi), `item_name`, `item_group` (bắt buộc), `stock_uom` (bắt buộc), `description`, `image`, `disabled`, `end_of_life` (mặc định 2099-12-31) |
| **Cờ loại hàng** | `is_stock_item` (mặc định 1), `is_fixed_asset`, `is_purchase_item`, `is_sales_item`, `is_sub_contracted_item`, `is_customer_provided_item`, `delivered_by_supplier` |
| **Trường mua** | `purchase_uom`, `min_order_qty`, `safety_stock`, `lead_time_days`, `last_purchase_rate` (chỉ đọc, hệ tự cập nhật), `country_of_origin`, `customs_tariff_number` |
| **Trường kho** | `valuation_method` (FIFO, Moving Average, LIFO), `valuation_rate`, `weight_per_unit` + `weight_uom`, `allow_negative_stock`, `over_delivery_receipt_allowance` |
| **Ràng buộc** | `cant_change()`: khi đã có chứng từ đã ghi sổ thì **không đổi được** `is_stock_item`, `has_serial_no`, `has_batch_no`, `valuation_method` (chỉ cho đổi FIFO sang Moving Average). `has_serial_no` không được bật cho hàng phi kho. Đổi tên mã được (`before_rename`, `after_rename`) và **gộp hai mã** được, gộp thì cộng lại tồn, kiểm trùng phiếu kiểm kê |

Cách đặt mã do Stock Settings quyết: `item_naming_by` = `Item Code` (gõ tay, site học đang dùng) hoặc `Naming Series` (tự sinh theo mẫu `STO-ITEM-.YYYY.-`).

### 2.2. Item Group: nhóm hàng dạng cây

| | |
|---|---|
| **Là gì** | Cây phân loại mặt hàng (nested set `lft`, `rgt`), gốc là `All Item Groups`. Nút có `is_group = 1` mới có con |
| **Dùng khi** | Lọc báo cáo, phân quyền, quy tắc giá, và **cấp giá trị mặc định cho mặt hàng mới** |
| **Trường chính** | `item_group_name` (duy nhất), `parent_item_group`, `is_group`, `image`, `item_group_defaults` (bảng Item Default), `taxes` (bảng Item Tax) |
| **Ràng buộc** | Mặt hàng nên gắn vào nút lá. `update_defaults_from_item_group()`: mặt hàng **mới** chưa có mặc định thì chép kho, bảng giá, NCC, trung tâm chi phí, tài khoản và mẫu thuế từ nhóm. Chép **một lần** lúc tạo, sửa nhóm sau đó không hồi tố |

Ví dụ thật trên site học: 100 nhóm, **chỉ một nút cha** là gốc; mọi nhóm đồng bộ từ ERP DEGO đều nằm phẳng dưới gốc (`Chai`, `Chai Pet`, `Chai Hdpe`, `Chai Pet giả nhôm` là anh em chứ không phải cha con). Nghĩa là dữ liệu bên mình có tầng cây ngầm mà chưa ai dựng.

### 2.3. Biến thể: Item Template, Item Attribute, Item Variant

| | |
|---|---|
| **Là gì** | Một mặt hàng **mẫu** (`has_variants = 1`) gom nhiều **biến thể** (`variant_of` = mã mẫu). Biến thể khác nhau ở giá trị thuộc tính, ví dụ cùng chai PET khác dung tích và màu |
| **Dùng khi** | Hàng có nhiều quy cách cùng gốc, cần lọc, báo cáo theo họ, cần sinh mã có quy luật |
| **Item Attribute** | Từ điển thuộc tính: `attribute_name` (duy nhất), `numeric_values` (kiểu số thì có `from_range`, `to_range`, `increment`), bảng `item_attribute_values` gồm `attribute_value` + `abbr` (viết tắt, bắt buộc) |
| **Item Variant Attribute** | Bảng con trên Item: `attribute` + `attribute_value`. Trên mẫu thì khai thuộc tính nào được dùng; trên biến thể thì ghi giá trị cụ thể |
| **Sinh mã** | `make_variant_item_code()` trong `controllers/item_variant.py`: mã biến thể = **mã mẫu + gạch nối + viết tắt từng giá trị** theo thứ tự thuộc tính, ví dụ `CHAI-PET-500-TR`. Thuộc tính kiểu số thì dùng chính con số. Tên biến thể sinh cùng kiểu |
| **Item Variant Settings** | `fields`: danh sách trường được **chép từ mẫu xuống mọi biến thể** mỗi lần sửa mẫu (`update_variants`, quá 30 biến thể thì chạy nền). `do_not_update_variants` tắt việc chép. `allow_different_uom`: mặc định biến thể **phải cùng `stock_uom`** với mẫu |
| **Ràng buộc** | Mẫu **không giao dịch được** (không có tồn kho). Giá trị thuộc tính phải nằm trong từ điển. `variant_based_on` (Item Attribute hoặc Manufacturer) không đổi được khi đã có biến thể. **Đã có phát sinh kho thì không đổi được thuộc tính** của biến thể, muốn đổi phải tạo mã mới rồi chuyển tồn |

Điểm cần ghi nhớ: trong ERPNext **mẫu là một dòng Item** cùng bảng với biến thể, chỉ khác cờ. Đây chính là chiều mà luật mô hình sản phẩm của DEGO cấm làm ngược (xem mục 5.2).

### 2.4. Đơn vị tính và quy đổi

| Khái niệm | Là gì | Trường chính | Ràng buộc |
|---|---|---|---|
| **UOM** | Danh mục đơn vị | `uom_name` (duy nhất), `must_be_whole_number`, `symbol`, `common_code` (mã UN/ECE), `category` | `must_be_whole_number` chặn số lẻ trên chứng từ |
| **UOM Category** + **UOM Conversion Factor** | Bảng quy đổi **chung** giữa các đơn vị cùng loại (khối lượng, độ dài...) | `category`, `from_uom`, `to_uom`, `value` | Site học có sẵn 249 đơn vị, 235 hệ số, 17 nhóm. `get_uom_conv_factor()` tìm thẳng, tìm ngược (1 / hệ số), rồi tìm qua đơn vị trung gian cùng nhóm |
| **UOM Conversion Detail** | Bảng con `uoms` trên **từng mặt hàng**: một đơn vị khác quy ra bao nhiêu đơn vị tồn | `uom`, `conversion_factor` | Đơn vị tồn luôn có dòng hệ số 1 (tự thêm); không trùng đơn vị; hệ số phải lớn hơn 0; để trống thì tự lấy từ bảng chung |
| **ĐVT tồn, mua, bán** | `stock_uom` (sổ kho luôn ghi theo đơn vị này), `purchase_uom`, `sales_uom` (mặc định khi lập chứng từ) | | **Đổi `stock_uom` bị chặn** khi đã có Stock Ledger Entry khác đơn vị hoặc còn số đang đặt, đang giữ (`check_stock_uom_with_bin`). Đổi được thì bảng `uoms` bị xóa, phải khai lại |

Trên mỗi dòng chứng từ ERPNext lưu **cả ba**: `uom` + `qty` (theo đơn vị giao dịch), `conversion_factor`, `stock_qty` (= qty × hệ số). Sổ kho chỉ đọc `stock_qty`. Đây là thứ làm cho mua theo thùng, tồn theo cái chạy được.

### 2.5. Item Default: mặc định theo công ty

| | |
|---|---|
| **Là gì** | Bảng con `item_defaults` trên Item, Item Group và Brand, **một dòng cho một công ty** |
| **Dùng khi** | Nhiều pháp nhân dùng chung danh mục nhưng kho nhận, NCC quen, tài khoản khác nhau |
| **Trường chính** | `company` (bắt buộc), `default_warehouse`, `default_price_list`, `default_supplier`, `buying_cost_center`, `expense_account`, `income_account`, `default_inventory_account`, `default_cogs_account` và các tài khoản chi phí mua |
| **Ràng buộc** | Không được hai dòng cùng công ty; kho và tài khoản phải thuộc đúng công ty (`validate_item_default_company_links`). Thứ tự lấy mặc định khi lập chứng từ: Item, rồi Item Group, rồi Brand |

### 2.6. Item Price và Price List: bảng giá

| | |
|---|---|
| **Price List** | Tên bảng giá (`price_list_name`), `currency` (bắt buộc), cờ `buying` / `selling`, `price_not_uom_dependent`. Site học có `Standard Buying`, `Standard Selling` bằng VND |
| **Item Price** | Một dòng giá: `item_code`, `price_list`, `uom` (bắt buộc), `price_list_rate`, `supplier` (bảng mua) hoặc `customer` (bảng bán), `valid_from` (mặc định hôm nay), `valid_upto`, `lead_time_days`, `batch_no`, `packing_unit`, `reference` |
| **Dùng khi** | Lập đơn mua tự điền giá theo bảng giá của NCC; giá hợp đồng có hiệu lực; giá chuẩn để so |
| **Ràng buộc** | Giá **gắn với đơn vị**: lập đơn bằng đơn vị khác thì tìm đúng đơn vị đó, không có thì quy theo hệ số. Khác với `last_purchase_rate` trên Item (giá mua gần nhất, hệ tự ghi khi đơn mua, phiếu nhập được duyệt). Trường `standard_rate` lúc tạo Item chỉ là lối tắt sinh một dòng Item Price |

Site học: 387 dòng Item Price, tất cả ở `Standard Buying`, chưa gắn NCC.

### 2.7. Item Supplier: mã hàng của nhà cung cấp

Bảng con `supplier_items` trên Item: `supplier` (bắt buộc) + `supplier_part_no`. Dùng để in mã hàng của NCC lên đơn mua và để tìm mặt hàng theo mã NCC gửi trong báo giá. Đơn giản, không có giá, không có ưu tiên. Site học: 0 dòng.

### 2.8. Mã vạch

Bảng con `barcodes` (Item Barcode): `barcode` (bắt buộc, **duy nhất toàn hệ**), `barcode_type` (EAN, EAN-13, UPC-A, GS1, GTIN...), `uom` (mã vạch của thùng khác mã vạch của cái). `validate_barcode()` kiểm định dạng theo loại. Quét mã vạch trên phiếu nhập, xuất tự chọn mặt hàng và đơn vị.

### 2.9. Item Tax Template: thuế theo mặt hàng

| | |
|---|---|
| **Item Tax Template** | Mẫu thuế: `title`, `company` (bắt buộc), bảng `taxes` (tài khoản thuế + thuế suất) |
| **Item Tax** | Bảng con `taxes` trên Item hoặc Item Group: `item_tax_template`, `tax_category`, `valid_from`, `minimum_net_rate`, `maximum_net_rate` |
| **Dùng khi** | Cùng một đơn có dòng 5 %, dòng 8 %, dòng 10 %; hoặc thuế suất đổi theo thời điểm (giảm thuế có thời hạn) nhờ `valid_from` |
| **Ràng buộc** | Mức tối đa không nhỏ hơn mức tối thiểu; biến thể nhận thuế của mẫu. Site học có 8 mẫu thuế |

### 2.10. Item Reorder: mức đặt hàng lại

Bảng con `reorder_levels`: `warehouse` (bắt buộc), `warehouse_group`, `warehouse_reorder_level`, `warehouse_reorder_qty`, `material_request_type` (Purchase, Transfer, Material Issue, Manufacture). Một việc chạy hằng ngày (bật bằng `auto_indent` ở Stock Settings, site học đang bật) tính **số dự kiến** = tồn + đang đặt + đang yêu cầu − đã giữ; dưới mức thì **tự sinh Material Request** với số lượng đặt lại. Ràng buộc: kho không trùng, phải bật cấu hình. Biến thể chép mức đặt lại của mẫu nếu chưa khai.

### 2.11. Quality Inspection Template gắn mặt hàng

Item có `inspection_required_before_purchase` / `_before_delivery` và `quality_inspection_template`. Mẫu gồm các chỉ tiêu (`specification`), mỗi chỉ tiêu là số (`min_value`, `max_value`), chữ (`value`) hoặc công thức (`acceptance_formula`). Bật cờ thì phiếu nhập **không duyệt được** khi thiếu phiếu kiểm đạt. Site học có 1 mẫu từ bài tập.

### 2.12. Lô, số serial, hạn dùng

| Trường | Ý nghĩa | Ràng buộc |
|---|---|---|
| `has_batch_no` | Theo dõi lô; mỗi lần nhập, xuất phải ghi lô | Chỉ cho hàng tồn kho; không đổi được sau phát sinh |
| `create_new_batch` + `batch_number_series` | Tự sinh số lô khi nhập | |
| `has_expiry_date` + `shelf_life_in_days` | Lô có hạn dùng; hạn = ngày sản xuất + số ngày | Bật cả ba cờ thì `shelf_life_in_days` phải lớn hơn 0 |
| `retain_sample` + `sample_quantity` | Giữ mẫu lưu theo lô | Tự xóa khi tắt lô |
| `has_serial_no` + `serial_no_series` | Theo dõi từng cái | Không cho hàng phi kho; không đổi được sau phát sinh |

v16 gom lô và serial của một dòng chứng từ vào **Serial and Batch Bundle**.

### 2.13. Brand và Manufacturer

- **Brand**: `brand` (duy nhất), `description`, `image`, `brand_defaults` (bảng Item Default). Là thương hiệu **của hàng hóa**, dùng lọc và cấp mặc định.
- **Manufacturer**: `short_name`, `full_name`, `country`, `website`. **Item Manufacturer** là bảng riêng (không phải bảng con): `item_code` + `manufacturer` + `manufacturer_part_no` (bắt buộc) + `is_default`. Dùng khi cùng một mặt hàng mua được của nhiều hãng; biến thể có thể dựa theo hãng (`variant_based_on = Manufacturer`).

### 2.14. Các bảng phụ khác đáng biết

| DocType | Việc | Ghi chú |
|---|---|---|
| **Item Alternative** | Hàng thay thế (`item_code`, `alternative_item_code`, `two_way`) | Item phải bật `allow_alternative_item` |
| **Item Customer Detail** | Mã hàng theo khách (`customer_name`, `ref_code`) | Giống hàng gia công in nhãn riêng từng khách |
| **Item Lead Time** | Thời gian mua, thời gian sản xuất, năng lực trên ngày | Phục vụ kế hoạch |
| **Customs Tariff Number** | Mã HS | Link từ Item |

---

## 3. ERP DEGO hiện có gì

### 3.1. Luật nền phải giữ

Tóm từ [`mo-hinh-du-lieu-san-pham.md`](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md):

- **`tab_product` là bảng VARIANT (SKU).** Mỗi dòng là một quy cách cụ thể, đặt mua được, nhập kho được.
- **`product_code` là hạt nối 7 bảng** bằng chuỗi, không có khóa ngoại: dòng YCMH, dòng ĐMH, nhận hàng, tồn kho, phát sinh kho, lịch sử mua hàng, phương án khảo sát.
- **Cấm** thêm `tab_product_variant` phía dưới; **cấm** đổi hoặc tái dùng `product_code`; **cấm** đặt cột giá lên sản phẩm. Gom nhóm thì thêm `tab_product_family` **Ở TRÊN**, chỉ khi có ít nhất hai mã thật nên chung họ.
- Chứng từ là **bản chụp**: chọn mã thì điền tên, ĐVT, phân loại, TSKT vào dòng; sửa danh mục sau không hồi tố.
- Bảng mới: tham chiếu bằng ID, hằng kỹ thuật bằng `SMALLINT` + `IntEnum` (luật R2 ở `CLAUDE.md`).

### 3.2. Hiện trạng từng chức năng

| Chức năng | Mức | Ở đâu | Ghi chú |
|---|---|---|---|
| Mã, tên, tên hóa đơn, tên pháp lý | **Có** | `product/model.py` (`code` duy nhất, `name`, `invoice_name`, `legal_name`) | `ProductUpdate` không có `code` nên API không đổi được mã, đúng luật |
| Thông số kỹ thuật | **Một phần** | cột `specs` String(255), tự điền sang ô TSKT của dòng ĐMH | **0 / 6.803 mã điền**; quy cách nằm trong tên |
| Nhóm hàng | **Một phần** | `catalog/model.py` `tab_item_group` (73 nhóm, phẳng); `tab_product.item_group` là **chuỗi tên** | 685 mã ghi phân loại không khớp tên trong danh mục (lệch hoa thường, `Nhãn Thùng` so với `Nhãn thùng`); `lead_time.norm_group` vá lúc đọc. Cột `item_group_id` (mục 5.0 của tài liệu mô hình) **chưa làm** |
| Mặc định theo nhóm hàng | **Một phần** | `tab_item_group.std_days`, `std_days_unavail` (số ngày quy định có hàng, hai mốc có sẵn, không sẵn) qua `catalog/lead_time.py`; `tab_category_assignee` phân NSTM chính và dự phòng theo **phòng × nhóm hàng** | Mạnh hơn ERPNext ở phân công người mua; thiếu kho mặc định, thuế mặc định |
| Đơn vị tính | **Một phần** | `tab_unit` (11 đơn vị, chỉ `code`, `name`); `tab_product.unit` là **chuỗi tên**, không bắt buộc | **6.424 / 6.803 mã (94 %) để trống**; còn lại `Gram` 350, `Cái` 27, `Kg` 2. Dòng ĐMH có những đơn vị không ai khai ở mã (`Bịch`, `cuộn`, `Cây`) |
| Quy đổi đơn vị | **Chưa** | Không có bảng | Phiếu khảo sát có `quote_unit`, `internal_unit`, `amount_converted` gõ tay, chỉ 4 / 5.150 dòng dùng; phương án chụp `snap_quote_unit`. Công cụ AI `product_best_price` tự cảnh báo giá chưa quy đổi đơn vị |
| Thuộc tính, biến thể, họ sản phẩm | **Chưa** | Thiết kế đủ ở tài liệu mô hình mục 5 và 10 (`tab_attribute`, `tab_attribute_option`, `tab_item_group_attribute`, `tab_product_attribute`, `tab_product_family`) | Lộ trình GĐ 1 tới GĐ 6 đều **Chưa làm**. Mã kiểu `NTN0033` và `NTN0033.1` là dấu hiệu họ sản phẩm |
| Cờ loại hàng (tồn kho, phi kho, dịch vụ, tài sản) | **Chưa** | | Dịch vụ vận chuyển chỉ phân biệt bằng phân loại; NCC có `supplier_type` goods / transport |
| Ngưng dùng | **Có** | `is_active`; nhập file có cột Hành động | |
| Ảnh | **Có** | `attachment` `FileLink(entity="product")`, nhiều ảnh, `thumbnail_url` nạp theo lô | Hơn ERPNext (một ảnh) |
| Chặn xóa khi còn chứng từ | **Có** | `product/service.count_references` đếm đủ 7 bảng (ai-CR-169); `catalog/references.py` chặn xóa ĐVT, nhóm hàng, kho đang dùng | Không có khóa đổi ĐVT hay phân loại sau khi đã phát sinh kho |
| Nhập, xuất file | **Có** | `product/controller.py` `/import/csv`, `/export/csv`; khớp tiêu đề linh hoạt, chỉ ghi đè cột có trong file, gộp mã trùng trong file | |
| Giá mua gần nhất, giá cao nhất | **Có** | `tab_purchase_history` (6.503 dòng, 6.418 dữ liệu cũ); `tab_survey_product_line.last_purchase_price`, `max_purchase_price` tự điền; công cụ AI `product_best_price`, `suppliers_for_product` (`assistant/tools/catalog.py`) | Chưa quy đổi đơn vị nên so giá có thể sai |
| Bảng giá có hiệu lực | **Chưa** (có thay thế) | Giá nằm ở báo giá khảo sát `price_by_volume` + `volume_range` và lịch sử mua | Tài liệu mô hình mục 11 đã chừa chỗ: `tab_product_price` có `valid_from` / `valid_to` |
| Mã hàng của NCC | **Một phần** | `tab_survey_product_line.internal_code` gõ tay theo từng phiếu (2.684 mã khác nhau) | Không có danh mục mặt hàng × NCC; không chép sang đơn |
| Thuế | **Một phần** | `tab_supplier.vat` (mặc định 8 %) và `vat` trên từng dòng | Thuế theo NCC chứ không theo mặt hàng |
| Xuất xứ, mã HS | **Một phần** | `origin` trên dòng khảo sát; ô "Xuất xứ / TSKT" trên dòng ĐMH; phân hệ `customs` tra theo mã HS nhưng không nối mã hàng | |
| Khối lượng, kích thước | **Một phần** | `tab_po_item.weight_kg`, `dimension` để chia chi phí nhập khẩu | Không nằm trên mặt hàng, mỗi đơn gõ lại |
| MOQ | **Một phần** | `moq` trên dòng khảo sát theo từng NCC | Không có tồn an toàn |
| Gắn vật tư với thành phẩm | **Một phần** | `hh_code`, `hh_name` (5.145 mã có) | Chuỗi tự do, không phải định mức |
| Thương hiệu | **Chưa** | `tab_brand` thực chất là **bộ phận đặt hàng** (`department`, `manager_id`), không bảng nào trỏ tới, không có màn v2 | Trùng tên dễ hiểu nhầm, xem mục 5.3 |
| Mã vạch, mức đặt lại, lô, hạn dùng, mẫu kiểm chất lượng, hàng thay thế, mã theo khách | **Chưa** | | Phiếu khảo sát có mẫu và `lab_result` nhưng là kiểm mẫu khi chọn NCC, không phải kiểm khi nhận hàng |
| Phương pháp tính giá tồn | **Một phần** | `inventory/model.py` `avg_cost` bình quân gia quyền cho mọi mã | Không chọn theo mặt hàng |
| Màn hình v2 | **Có** | `frontend-v2/src/modules/production/config/product-crud.tsx` (danh sách, chi tiết, tab Lịch sử mua hàng), `item-group-crud.tsx`, `unit-crud.tsx`; `procurement/pages/category-assignee-*` | Bộ lọc là ô chữ; chưa có lọc theo thuộc tính |

Phạm vi dữ liệu: `product` khai `PUBLIC` trong `SCOPE_FIELDS`, mọi công ty dùng chung một danh mục, giống ERPNext.

---

## 4. Bảng fit-gap và tỷ lệ phủ

Điểm: **Có = 1**, **Một phần = 0,5**, **Chưa = 0**. Số serial **không tính** vào mẫu số vì hàng của DEGO (bao bì, nhãn, nguyên liệu) không theo dõi từng cái; máy móc thiết bị nếu cần thì thuộc phân hệ tài sản.

### A. Định danh và mô tả

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| A1 | Mã duy nhất, bất biến | `item_code` duy nhất, đổi tên có kiểm | `code` duy nhất, API không cho đổi | 1 | Luật cấm đổi mã là cố ý |
| A2 | Tên, tên hóa đơn, mô tả kỹ thuật | `item_name`, `description` | `name`, `invoice_name`, `legal_name`, `specs` | 1 | `specs` chưa ai điền |
| A3 | Nhóm hàng dạng cây | Item Group cây | Danh mục phẳng, nối bằng tên | 0,5 | 685 mã lệch tên |
| A4 | Ngưng dùng, hết vòng đời | `disabled`, `end_of_life` | `is_active` | 1 | |
| A5 | Cờ loại hàng | `is_stock_item`, `is_fixed_asset`, `is_purchase_item`, `is_sales_item` | Không có | 0 | |
| A6 | Ảnh | `image` một ảnh | Nhiều ảnh, ảnh đại diện | 1 | DEGO hơn |
| A7 | Thương hiệu | Brand | `tab_brand` là bộ phận đặt hàng | 0 | |
| A8 | Nhà sản xuất, mã của hãng | Manufacturer, Item Manufacturer | Không có | 0 | |
| A9 | Xuất xứ, mã HS | `country_of_origin`, `customs_tariff_number` | Chữ tự do trên khảo sát và ĐMH | 0,5 | |
| A10 | Khối lượng, kích thước | `weight_per_unit`, `weight_uom` | Trên dòng ĐMH | 0,5 | |

### B. Đơn vị tính

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| B1 | ĐVT tồn kho bắt buộc, khóa sau phát sinh | `stock_uom` bắt buộc, `check_stock_uom_with_bin` | `unit` tùy chọn, 94 % trống, không khóa | 0,5 | |
| B2 | Danh mục ĐVT có thuộc tính | UOM: số nguyên, ký hiệu, nhóm | `tab_unit` mã + tên | 0,5 | |
| B3 | Quy đổi theo từng mặt hàng | UOM Conversion Detail | Không có | 0 | |
| B4 | Bảng quy đổi chung | UOM Conversion Factor + Category | Không có | 0 | |
| B5 | ĐVT mua, bán mặc định khác ĐVT tồn; chứng từ lưu hệ số | `purchase_uom`, `sales_uom`, `conversion_factor`, `stock_qty` trên dòng | Gõ tay trên khảo sát | 0 | |

### C. Thuộc tính và biến thể

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| C1 | Từ điển thuộc tính và giá trị | Item Attribute | Đã thiết kế, chưa dựng | 0 | |
| C2 | Mẫu, biến thể, sinh mã | Template, Variant, `make_variant_item_code` | Chưa | 0 | |
| C3 | Thông tin chung của họ dùng chung cho biến thể | Item Variant Settings chép xuống | Chưa | 0 | |

### D. Mặc định, giá, thuế

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| D1 | Mặc định theo công ty | Item Default | Không có | 0 | |
| D2 | Kế thừa mặc định từ nhóm hàng | `item_group_defaults`, `taxes` | Số ngày quy định, NSTM phụ trách theo nhóm | 0,5 | Phân công theo phòng × nhóm là thế mạnh riêng |
| D3 | Thời gian giao hàng | `lead_time_days` trên Item và Item Price | Theo nhóm hàng, hai mốc | 0,5 | Không theo mặt hàng, không theo NCC |
| D4 | Bảng giá có hiệu lực | Price List, Item Price | Báo giá khảo sát, lịch sử mua | 0,5 | Như tài liệu 11 A6 |
| D5 | Giá mua gần nhất | `last_purchase_rate` | Lịch sử mua, giá gần nhất và cao nhất tự điền, công cụ AI | 1 | |
| D6 | Mã hàng của NCC | Item Supplier | Gõ tay trên từng phiếu khảo sát | 0,5 | |
| D7 | Thuế theo mặt hàng | Item Tax Template | VAT theo NCC và theo dòng | 0,5 | |
| D8 | Mã vạch | Item Barcode | Không có | 0 | |

### E. Kho và chất lượng

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| E1 | Mức đặt hàng lại, tự sinh yêu cầu | Item Reorder + `auto_indent` | Không có | 0 | Tài liệu 11 B2 |
| E2 | Số lượng đặt tối thiểu, tồn an toàn | `min_order_qty`, `safety_stock` | MOQ theo báo giá NCC | 0,5 | |
| E3 | Lô, hạn dùng, hạn sử dụng theo ngày | `has_batch_no`, `has_expiry_date`, `shelf_life_in_days` | Không có | 0 | Chờ câu C5 |
| E4 | Mẫu kiểm chất lượng theo mặt hàng | Quality Inspection Template | Không có | 0 | |
| E5 | Phương pháp tính giá tồn | `valuation_method` theo mặt hàng | Bình quân gia quyền chung | 0,5 | |
| — | Số serial | `has_serial_no` | Không có | không tính | |

### F. Quan hệ và toàn vẹn

| # | Chức năng | ERPNext | ERP DEGO | Điểm | Ghi chú |
|---|---|---|---|---|---|
| F1 | Hàng thay thế | Item Alternative | Không có | 0 | |
| F2 | Mã hàng theo khách | Item Customer Detail | Tên khách nằm trong tên nhãn | 0 | |
| F3 | Gắn vật tư với thành phẩm | BOM | `hh_code`, `hh_name` chữ tự do | 0,5 | |
| F4 | Khóa trường và chặn xóa khi đã phát sinh | `cant_change`, kiểm liên kết | Chặn xóa đủ 7 bảng; không khóa trường | 0,5 | |
| F5 | Gộp hai mã trùng | Rename có merge | Không có | 0 | |
| F6 | Nhập, xuất hàng loạt | Data Import | CSV có khớp tiêu đề linh hoạt | 1 | |
| F7 | Tra cứu, lịch sử mua ngay trên mặt hàng | Dashboard liên kết | Tab Lịch sử mua hàng, tìm theo mã, tên, mã HH | 1 | |

### Tỷ lệ phủ

| Nhóm | Số chức năng | Điểm | Tỷ lệ |
|---|---|---|---|
| A. Định danh và mô tả | 10 | 5,5 | 55 % |
| B. Đơn vị tính | 5 | 1 | 20 % |
| C. Thuộc tính và biến thể | 3 | 0 | 0 % |
| D. Mặc định, giá, thuế | 8 | 3,5 | 44 % |
| E. Kho và chất lượng | 5 | 1 | 20 % |
| F. Quan hệ và toàn vẹn | 7 | 3 | 43 % |
| **Cộng** | **38** | **14** | **37 %** |

Đọc bảng: mặt hàng của DEGO hiện được dựng để **phục vụ thu mua** (tìm mã, điền dòng, so giá đã mua), chưa dựng để **phục vụ kho**. Ba nhóm B, C, E chính là nền mà phiếu nhập, xuất, kiểm kê sẽ đứng lên.

---

## 5. Đề xuất cho DEGO

### 5.1. Nên học gì

1. **ĐVT tồn kho là trường bắt buộc và bị khóa sau phát sinh kho đầu tiên.** ERPNext chặn đổi `stock_uom` khi đã có sổ kho (`check_stock_uom_with_bin`). Đây là luật đơn giản nhưng giữ cho số tồn luôn có nghĩa.
2. **Quy đổi theo từng mặt hàng, sổ kho chỉ đọc số lượng theo ĐVT tồn.** Mỗi dòng chứng từ có `uom`, `qty`, `conversion_factor`, `stock_qty`. Mua theo cuộn, thùng, bao; tồn theo cái, kg.
3. **Bảng quy đổi chung cho đơn vị đo lường** (kg, gram, lít, ml) để khỏi khai lặp trên 7.000 mã; bảng theo mặt hàng chỉ cần cho đơn vị đóng gói (thùng 40 chai, cuộn 1.000 nhãn).
4. **Thuộc tính có viết tắt** (`abbr`) để *gợi ý* mã mới có quy luật. Chỉ gợi ý cho mã mới, không áp lên mã cũ.
5. **Đã có phát sinh kho thì không đổi thuộc tính** của mã; muốn khác quy cách thì tạo mã mới. Khớp tuyệt đối với luật bất biến `product_code` của DEGO.
6. **Kế thừa mặc định từ nhóm hàng chép một lần lúc tạo**, không hồi tố. DEGO đã làm đúng kiểu này với số ngày quy định; mở rộng cho ĐVT gợi ý, thuế gợi ý, kho nhận gợi ý.
7. **Bảng con quanh mặt hàng thay cho cột trên mặt hàng**: mã hàng của NCC, mức đặt lại theo kho, giá có hiệu lực. Đúng tinh thần cấm cột giá của DEGO.
8. **Mức đặt hàng lại sinh yêu cầu mua nháp**, tính trên số dự kiến chứ không chỉ tồn thực.

### 5.2. Không nên chép gì

| Không chép | Vì sao |
|---|---|
| **Mẫu biến thể là một dòng cùng bảng Item** (`has_variants`, `variant_of`) | Ở DEGO nghĩa là thêm dòng không giao dịch được vào `tab_product`, làm `ProductPicker`, nhập file, đếm tham chiếu, báo cáo đều phải lọc bỏ dòng mẫu. Luật DEGO đặt họ sản phẩm ở **bảng riêng phía trên** (`tab_product_family`), sạch hơn |
| **Sinh mã biến thể bằng mã mẫu + viết tắt và sinh lại khi đổi** | Mã DEGO đã có ý nghĩa với người dùng và đối tác (`NTN5132`), không được đổi. Chỉ dùng viết tắt để gợi ý mã mới |
| **Item Variant Settings chép trường từ mẫu xuống biến thể** | Chép là nhân bản dữ liệu; DEGO giữ thông tin cấp họ ở họ (luật mục 10 của tài liệu mô hình), biến thể đọc qua họ khi cần |
| **Tài khoản kế toán trên mặt hàng** (`expense_account`, `default_inventory_account`...) | Sổ cái của DEGO nằm ở MISA; gắn tài khoản trên mặt hàng là dựng nguồn sự thật thứ hai cho kế toán |
| **`standard_rate`, `valuation_rate`, `opening_stock` trên form mặt hàng** | Trái luật cấm giá trên sản phẩm; tồn đầu phải đi bằng phiếu kiểm kê có người chịu trách nhiệm |
| **Lấp ĐVT trống bằng một đơn vị mặc định** (như script đồng bộ đã gán `Nos` cho 6.420 mã) | Che mất lỗi dữ liệu. Thà để trống và chặn nhập kho còn hơn ghi sai đơn vị |
| **Một form 80 trường, 9 bảng con** | Người mua của DEGO chỉ cần mười trường. Bảng con nên là tab riêng, chỉ hiện khi có quyền và có việc |
| **Gộp mã trùng tự động** | Gộp chạm cả 7 bảng nối bằng chuỗi, cần CR riêng có diễn tập; không làm như thao tác thường ngày |

### 5.3. Đưa biến thể và quy đổi đơn vị vào mà giữ luật mô hình sản phẩm

**Biến thể và thuộc tính** (đi đúng lộ trình đã duyệt, không thêm gì mới):

```
tab_product_family  (họ, chỉ dựng khi đủ điều kiện kích hoạt)
        ^ family_code (nullable)
tab_product         (SKU, KHÔNG ĐỔI hạt, KHÔNG thêm bảng con kiểu variant)
        ^ product_id
tab_product_attribute ── tab_attribute ── tab_attribute_option
                               ^
                     tab_item_group_attribute (nhóm hàng nào dùng thuộc tính nào)
```

- Nấc đầu chỉ cần **thuộc tính trên SKU** (M1 tới M4 của tài liệu mô hình). Họ sản phẩm chỉ làm khi có ít nhất hai mã thật nên chung họ, ví dụ `NTN0033` và `NTN0033.1`.
- **Thương hiệu, khách gia công** là thông tin cấp họ hoặc là thuộc tính, **không** dùng lại `tab_brand` (bảng đó là bộ phận đặt hàng). Nếu dựng thương hiệu thật thì đặt tên bảng khác, ví dụ `tab_product_brand`, và nên đổi nhãn hiển thị của `tab_brand` thành *Bộ phận đặt hàng*.

**Quy đổi đơn vị** (bảng mới, ID theo luật mục 4 của tài liệu mô hình):

| Bảng, cột | Nội dung | Ghi chú |
|---|---|---|
| `tab_unit` thêm `must_be_whole_number`, `category` (`SMALLINT` + `IntEnum`: đếm, khối lượng, thể tích, độ dài) | Thuộc tính đơn vị | Không đổi khóa chuỗi `name` mà chứng từ đang chép |
| `tab_unit_conversion` (`from_unit_id`, `to_unit_id`, `factor`) | Quy đổi chung kg, gram, lít, ml | Vài chục dòng |
| `tab_product_uom` (`product_id`, `unit_id`, `factor`, `is_purchase_default`, `UNIQUE(product_id, unit_id)`) | Một đơn vị đóng gói quy ra bao nhiêu ĐVT tồn | ĐVT tồn không cần dòng (hệ số 1 ngầm định) |
| `tab_product.unit` | **Giữ là ĐVT tồn**, nay bắt buộc với mã mới, khóa đổi sau phát sinh kho | Không đổi nghĩa trường, đúng luật `ProductOut` chỉ được thêm |
| `tab_product.unit_id` (tùy chọn, như `item_group_id`) | Bản ID song song với chuỗi | Chỉ khi chủ dự án muốn đổi tên ĐVT mà không đứt |

Phía chứng từ: hôm nay dòng ĐMH, giao hàng, nhập kho chỉ có `unit` + số lượng. Muốn mua theo thùng mà tồn theo cái thì các bảng đó **phải thêm** `conversion_factor` và `stock_qty`, và `tab_inventory_move` ghi theo `stock_qty`. Đây là thay đổi chứng từ, **trái điều 3 mục 7 của tài liệu mô hình** (điều đó viết cho thuộc tính, nhưng tinh thần "chứng từ không thêm cột" là chung), nên phải là **CR riêng có chủ dự án gật**. Cách an toàn: cột mới có mặc định `conversion_factor = 1`, `stock_qty = qty`; dòng cũ giữ nguyên nghĩa; chỉ dòng mới chọn đơn vị khác ĐVT tồn mới có hệ số khác 1.

**Các bảng con khác** đều treo bằng `product_id` (hoặc `product_code` nếu cần nối với 7 bảng cũ), không đụng hạt:

- `tab_product_supplier` (`product_id`, `supplier_id`, `supplier_item_code`, `is_default`, `lead_time_days`): nạp ban đầu từ 2.684 mã `internal_code` trên khảo sát và từ lịch sử mua.
- `tab_product_price` (đã chừa chỗ ở mục 11 của tài liệu mô hình): `product_id`, `supplier_id`, `unit_id`, `price`, `currency`, `valid_from`, `valid_to`, `source` (`SMALLINT`: hợp đồng khung, báo giá đã duyệt, nhập tay). Giá của chứng từ vẫn là bản chụp.
- `tab_product_reorder` (`product_id`, `company_id`, `warehouse_code`, `reorder_level`, `reorder_qty`).
- Cờ trên `tab_product`: `item_type` (`SMALLINT` + `IntEnum`: hàng tồn kho, phi kho, dịch vụ, tài sản), về sau `has_batch`, `shelf_life_days`. Cờ là thuộc tính kỹ thuật của SKU, không phải giá, nên đặt trên SKU được.

### 5.4. Rủi ro chuyển đổi dữ liệu

| Rủi ro | Mức | Cách giảm |
|---|---|---|
| **Điền ĐVT hàng loạt sai** cho 6.424 mã. Sau khi khóa ĐVT thì sai là sai vĩnh viễn với mã đã có phát sinh kho | Cao | Khuôn **đề xuất, duyệt, nạp** (như M4): script đoán theo nhóm hàng và tên (`1kg`, `500ml`, nhãn đếm cái), xuất Excel có độ tin cậy, người phụ trách danh mục duyệt; chỉ khóa sau khi duyệt |
| **83 dòng tồn kho và sổ phát sinh hiện có** đang ghi `unit` theo chuỗi; nếu ĐVT mới khác thì số tồn đổi nghĩa | Cao | Trước khi khóa, đối chiếu từng mã có tồn; mã nào lệch thì kiểm kê lại bằng phiếu điều chỉnh, không sửa thẳng số |
| **Lịch sử mua 6.418 dòng cũ** trộn đơn vị (cái, cuộn, bịch) cho cùng một mã | Vừa | Không sửa bản chụp. So giá chỉ so các dòng cùng đơn vị, hoặc quy đổi lúc đọc khi đã có `tab_product_uom`; giữ câu cảnh báo của `product_best_price` |
| **Nhóm hàng lệch tên** (685 mã) làm sai số ngày quy định, sai NSTM | Vừa | Làm M1 `item_group_id` + backfill hai lượt như tài liệu mô hình mục 8 trước mọi việc khác về nhóm |
| **Đoán thuộc tính từ tên** sai hàng loạt | Vừa | Đã có luật bắt buộc bước duyệt ở M4 |
| **Tách họ sản phẩm** khi dữ liệu cấp họ đã bị gõ lặp trên nhiều SKU | Vừa | Giữ kỷ luật mục 10: không nhét thông tin cấp họ vào SKU từ hôm nay |
| **Đồng bộ sang ERPNext** (site học) gán `Nos` che lỗi | Thấp | Chỉ là site học; ghi chú để không ai lấy số đó làm căn cứ |

---

## 6. Kế hoạch theo nấc

Độ lớn: **Nhỏ** dưới 1 ngày, **Vừa** 2 tới 4 ngày, **Lớn** trên 1 tuần (một người, gồm bài kiểm).

### Nấc 1: vá nhanh, chưa đổi chứng từ

| # | Việc | Độ lớn | Phụ thuộc |
|---|---|---|---|
| 1.1 | Màn Sản phẩm v2 thêm bộ lọc nhanh *Chưa có ĐVT* và *Phân loại lệch danh mục*, kèm số đếm ở đầu màn để người phụ trách thấy việc phải dọn | Nhỏ | Không |
| 1.2 | M1 của tài liệu mô hình: `tab_product.item_group_id` + backfill hai lượt + in số mã còn `0` | Nhỏ | Không |
| 1.3 | Bắt buộc ĐVT với mã **tạo mới** và khi sửa mã đang trống ĐVT (schema), không hồi tố mã cũ | Nhỏ | Câu Q1 |
| 1.4 | Thêm `item_type` (`SMALLINT` + `IntEnum`) trên sản phẩm, mặc định hàng tồn kho; nhóm Vận chuyển, dịch vụ gán phi kho | Nhỏ | Câu Q2 |
| 1.5 | Script đề xuất ĐVT cho 6.424 mã theo nhóm hàng và tên, xuất Excel, duyệt, nạp có chạy thử | Vừa | 1.1, Q1 |
| 1.6 | Khóa đổi ĐVT và `item_type` khi mã đã có dòng `tab_inventory_move` (giống `check_stock_uom_with_bin`) | Nhỏ | 1.5 |

### Nấc 2: chuẩn hóa, làm nền cho kho

| # | Việc | Độ lớn | Phụ thuộc |
|---|---|---|---|
| 2.1 | M2, M3: bốn bảng thuộc tính, phân hệ `attribute`, hai màn danh mục, form Sản phẩm có trường động | Vừa | 1.2 |
| 2.2 | M4: nạp giá trị thuộc tính từ tên hàng (đề xuất, duyệt, nạp), bắt đầu với nhóm Nhãn (khoảng 4.000 mã) | Lớn | 2.1 |
| 2.3 | `specs` suy diễn từ thuộc tính (GĐ 5 của tài liệu mô hình) | Nhỏ | 2.2 |
| 2.4 | Thuộc tính đơn vị (`must_be_whole_number`, `category`), `tab_unit_conversion`, `tab_product_uom` + tab Quy đổi trên chi tiết sản phẩm | Vừa | 1.5, Q3 |
| 2.5 | Dòng ĐMH, giao hàng, nhập kho mang `conversion_factor` + `stock_qty`; sổ kho ghi theo `stock_qty` | Lớn | 2.4, Q4, phiếu nhập của thủ kho (tài liệu 11 mục 6) |
| 2.6 | `tab_product_supplier` mã hàng của NCC + nạp từ khảo sát và lịch sử mua; tự điền mã NCC lên đơn | Vừa | Không |
| 2.7 | Cây nhóm hàng: `parent_id` trên `tab_item_group`; nhóm con chưa khai thì kế thừa số ngày quy định và NSTM của nhóm cha | Vừa | 1.2, Q5 |
| 2.8 | `tab_product_price` giá kế hoạch có hiệu lực, nguồn từ hợp đồng khung hoặc báo giá đã duyệt | Vừa | Q6, việc hợp đồng khung (tài liệu 11 mục 6 số 9) |

### Nấc 3: mở rộng

| # | Việc | Độ lớn | Phụ thuộc |
|---|---|---|---|
| 3.1 | `tab_product_family` + `family_code` (GĐ 6), thương hiệu và khách gia công ở tầng họ | Vừa | 2.1, điều kiện kích hoạt, Q7 |
| 3.2 | Mức đặt hàng lại theo công ty, kho + việc chạy hằng ngày sinh YCMH nháp | Vừa | 2.5, sổ kho có xuất và chuyển kho |
| 3.3 | Lô và hạn dùng: cờ trên sản phẩm, số lô và hạn trên phiếu nhập, xuất | Lớn | Câu C5 của kế hoạch theo module, 2.5 |
| 3.4 | Mẫu kiểm chất lượng theo nhóm hàng hoặc mặt hàng, chặn nhập kho khi chưa đạt | Vừa | Phiếu nhập có bước kiểm (tài liệu 11) |
| 3.5 | Thuế suất VAT gợi ý theo nhóm hàng hoặc mặt hàng, có ngày hiệu lực | Nhỏ | Q8 |
| 3.6 | Mã vạch theo mặt hàng và theo đơn vị đóng gói | Nhỏ | Kho có máy quét |
| 3.7 | Kho nhận mặc định theo công ty, nhóm hàng | Nhỏ | Danh mục kho thật (SX2-2) |
| 3.8 | Hàng thay thế | Nhỏ | Không |

Nếu làm đủ nấc 1 và nấc 2, tỷ lệ phủ ước lên khoảng **60 %** (23 / 38: B lên 100 %, C lên 50 % vì chưa có họ, D lên 63 %). Nấc 3 đưa lên khoảng **85 %** (32,5 / 38); phần còn lại là thứ DEGO cố ý không chép (mục 5.2), như tài khoản kế toán trên mặt hàng.

---

## 7. Câu cần chủ dự án chốt

| # | Câu hỏi | Vì sao phải chốt | Em nghiêng về |
|---|---|---|---|
| Q1 | Từ ngày nào bắt buộc ĐVT với mã mới, và ai duyệt Excel ĐVT của 6.424 mã cũ? | Không có người duyệt thì script chỉ là đoán | Bắt buộc ngay; người phụ trách danh mục ở phòng Thu mua duyệt theo từng nhóm |
| Q2 | Có tách cờ loại hàng (tồn kho, phi kho, dịch vụ, tài sản) không? | Quyết định dòng nào được vào sổ kho | Có, làm cùng nấc 1 |
| Q3 | Nhóm hàng nào thật sự mua một đơn vị, tồn một đơn vị khác? Cần danh sách thật từ kho | Tránh dựng quy đổi cho 7.000 mã khi chỉ vài trăm mã cần | Hỏi kho và phòng mua trước khi dựng 2.4 |
| Q4 | Có chấp nhận thêm hai cột `conversion_factor`, `stock_qty` vào dòng ĐMH, giao hàng, nhập kho không? | Thay đổi chứng từ, ngoài luật "chứng từ không thêm cột" | Có, với mặc định 1 cho dòng cũ |
| Q5 | Nhóm hàng có cần cây cha con không, và nhóm con có kế thừa số ngày quy định, NSTM phụ trách của nhóm cha không? | Đụng phân công người mua đang chạy | Có cây, kế thừa khi con để trống |
| Q6 | Giá kế hoạch lấy từ đâu: hợp đồng khung, báo giá đã duyệt, hay nhập tay? | Quyết định bảng giá có nguồn sự thật rõ không | Hợp đồng khung trước, báo giá đã duyệt sau |
| Q7 | Đã có ít nhất hai mã nên chung họ chưa (ví dụ `NTN0033` và `NTN0033.1`)? Thương hiệu sản phẩm có cần quản không? | Điều kiện kích hoạt tầng họ | Chờ kết quả M4 rồi mới quyết |
| Q8 | VAT gợi ý theo mặt hàng hay giữ theo NCC? | Hàng bao bì, nguyên liệu có thuế suất khác nhau và có đợt giảm thuế có thời hạn | Theo nhóm hàng, có ngày hiệu lực |
| Q9 | Đổi nhãn `tab_brand` thành *Bộ phận đặt hàng* để khỏi nhầm với thương hiệu? | Tránh người sau dùng nhầm bảng | Có, chỉ đổi nhãn hiển thị |

Câu **C5** (lô, hạn dùng, vị trí kho) đã nằm trong [00 Kế hoạch theo module](../../plans/00-ke-hoach-theo-module.md), không lặp lại ở đây; việc 3.3 chờ câu đó.
