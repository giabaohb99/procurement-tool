# LÔ, SỐ SERIAL, HẠN DÙNG VÀ TRUY XUẤT: ERPNEXT V16 SO VỚI ERP DEGO

| | |
|---|---|
| Bản | 1.0 — 02/11/2026 |
| Mục đích | Hiểu ERPNext v16 làm lô, serial, hạn dùng, truy xuất thế nào; đo ERP DEGO đang ở đâu; đề xuất mức tối giản đủ dùng cho DEGO và kế hoạch theo nấc |
| Mốc so sánh | ERPNext **v16.53.0** trên site học (VPS 2, container `erpnext-hoc-backend-1`, site `frontend`), mã nguồn `apps/erpnext/erpnext/stock/doctype/batch`, `serial_no`, `serial_and_batch_bundle`, `serial_and_batch_entry`, `pick_list`, `manufacturing/doctype/work_order`; tài liệu chính thức ở `docs.frappe.io/erpnext` (trước đây `docs.erpnext.com`) |
| Mã soát | nhánh `erp-v2` ngày 02/11/2026, `backend/app/modules/inventory`, `goods_receipt`, `product`, `purchase_order`, `dossier` |
| Tính chất | Tài liệu nghiên cứu. Không sửa mã, không đổi dữ liệu |
| Đọc kèm | [01 Luồng chuẩn mua hàng, kho, sản xuất](../../nghien-cuu/01-luong-chuan-mua-hang-kho-san-xuat.md) mục 4.6 và 8.2 việc 2.10 · [10 Nghiệp vụ kho](../../nghien-cuu/10-nghiep-vu-kho.md) tình huống A4, B3 · [11 Độ phủ thu mua, kho](../../nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) dòng A3 · [san-xuat/00](../../san-xuat/00-tong-quan-nghiep-vu.md) câu A3 · [Mô hình dữ liệu sản phẩm](../../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) |

## Mục lục

1. [Kết luận trong một trang](#1-kết-luận-trong-một-trang)
2. [Từ ngữ: ba thứ cùng gọi là lô](#2-từ-ngữ-ba-thứ-cùng-gọi-là-lô)
3. [ERPNext v16 làm thế nào](#3-erpnext-v16-làm-thế-nào)
4. [ERP DEGO hiện có gì](#4-erp-dego-hiện-có-gì)
5. [Bên sản xuất và luật ngành có đòi lô, hạn dùng không](#5-bên-sản-xuất-và-luật-ngành-có-đòi-lô-hạn-dùng-không)
6. [Bảng fit-gap và tỷ lệ phủ](#6-bảng-fit-gap-và-tỷ-lệ-phủ)
7. [Đề xuất cho DEGO](#7-đề-xuất-cho-dego)
8. [Kế hoạch theo nấc](#8-kế-hoạch-theo-nấc)
9. [Câu cần chốt](#9-câu-cần-chốt)
10. [Nguồn](#10-nguồn)

---

## 1. Kết luận trong một trang

- **ERP DEGO hiện không có khái niệm lô, hạn dùng hay serial ở bất cứ bảng kho nào.** `tab_product`, `tab_goods_receipt`, `tab_po_delivery`, `tab_inventory`, `tab_inventory_move` đều không có cột lô hay hạn dùng. Tỷ lệ phủ mảng này so với ERPNext v16 là **0,5 / 18 = 3 %** (nửa điểm duy nhất là kết quả QC theo lần giao).
- **DEGO cần lô và hạn dùng, không cần serial.** Luật nhãn bắt buộc in **ngày sản xuất và hạn sử dụng** trên phân bón và thuốc bảo vệ thực vật; riêng thuốc bảo vệ thực vật còn phải in **số lô sản xuất**. Bên sản xuất đang ghi tay số lô, ngày sản xuất, hạn dùng vào bảng tính *Kết quả KCS Kho Dr Xanh* mỗi lần nhận thành phẩm, và đã có quy trình *sự cố sau sản xuất* dẫn tới **thu hồi hàng**. Nhu cầu là có thật, chỉ là đang nằm ngoài ERP.
- **Áp cho ai:** thành phẩm bắt buộc; nguyên liệu có hạn dùng hoặc cần truy xuất (hoạt chất thuốc bảo vệ thực vật, humic dạng lỏng, chế phẩm vi sinh) nên bật; nguyên liệu rời ổn định (urê, KCl, MAP) để Q-L1 chốt; **bao bì (chai PET, nắp, nhãn, thùng) không theo lô.**
- **Mức tối giản đủ dùng:** một bảng lô mới (`tab_stock_lot`), ba cột cờ trên `tab_product`, hai cột lô trên sổ kho, một bảng tồn theo lô. **Một dòng chứng từ một lô**, không dựng cơ chế *Serial and Batch Bundle*. **Không tính giá theo lô**, giá vẫn bình quân theo mã và kho. Lô là một chiều của tồn kho, **không phải biến thể sản phẩm**, nên không phạm luật cấm thêm bảng dưới `tab_product`.
- **Thời điểm:** lô phải vào **cùng lúc** với phiếu nhập kho thật (việc 2.1 nấc 2 của doc 01). Làm sau thì phải sửa lại phiếu nhập và kiểm kê đầu kỳ lần hai. Truy xuất ngược thành phẩm về nguyên liệu phải chờ phân hệ Sản xuất; truy xuất xuôi tới khách phải chờ bán hàng hoặc nối MISA.
- **Kế hoạch bốn nấc** (mục 8): L1 lô ở cửa nhập và tồn theo lô, L2 xuất theo FEFO và chặn hết hạn, L3 lô trong sản xuất và truy xuất ngược, L4 truy xuất xuôi tới khách. Làm xong L1 và L2 thì phủ **11 / 14 = 79 %** phần DEGO cần.

---

## 2. Từ ngữ: ba thứ cùng gọi là lô

Trong tài liệu và mã của DEGO, chữ *lô* đang được dùng cho ba thứ khác nhau. Phải tách ngay từ đầu để không đặt nhầm tên bảng.

| Gọi là | Nghĩa | Đang ở đâu | Tài liệu này |
|---|---|---|---|
| **Lô hàng** | Một chuyến giao, một lần giao của đơn mua, hoặc một lô nhập khẩu theo vận đơn | `tab_po_delivery`; thẻ *Lô hàng quá hạn giao* ở `dashboard/controller.py`; *lô hàng nhập khẩu* ở doc 09 | Không bàn |
| **Lô nhập dữ liệu** | Một lần nạp tệp Excel vào hệ thống | `tab_import_batch` ở `import_tool/model.py` | Không bàn, nhưng **chiếm mất chữ batch** |
| **Lô sản xuất** (*batch*, *lot*) | Nhóm hàng cùng một lần sản xuất, cùng ngày sản xuất, cùng hạn dùng, in cùng một số lô trên bao bì | Chưa có | **Đây là chủ đề** |

**Hệ quả đặt tên:** bảng mới nên gọi `tab_stock_lot`, cột gọi `lot_id`, `lot_no`. Không dùng `batch` để khỏi lẫn với `tab_import_batch`.

**Serial** (số seri) là mã riêng của **từng chiếc** hàng, không phải của một nhóm. Một lô 10.000 chai có một số lô; nếu theo serial thì có 10.000 số seri.

---

## 3. ERPNext v16 làm thế nào

### 3.1. Công tắc chung

Từ v15, tính năng lô và serial **tắt mặc định**. Phải bật `enable_serial_and_batch_no_for_item` (*Activate Serial / Batch No for Item*) trong **Stock Settings** thì ô *Has Batch No*, *Has Serial No* trên mặt hàng mới hiện ra. Cùng màn đó có các luật dùng chung:

| Trường ở Stock Settings | Mặc định | Ý nghĩa |
|---|---|---|
| `pick_serial_and_batch_based_on` | `FIFO` | Khi xuất, máy tự chọn lô theo `FIFO`, `LIFO` hoặc `Expiry` (hết hạn trước xuất trước, tức **FEFO**) |
| `auto_create_serial_and_batch_bundle_for_outward` | Bật | Phiếu xuất không cần ai chọn lô: máy tự lấy lô theo luật trên khi ghi sổ |
| `use_serial_batch_fields` | Bật | Giữ ô `batch_no`, `serial_no` kiểu cũ ngay trên dòng chứng từ; máy tự đóng gói thành *bundle* khi ghi sổ (mục 3.4) |
| `disable_serial_no_and_batch_selector` | Tắt | Tắt hộp thoại chọn lô, bắt gõ tay |
| `use_naming_series`, `naming_series_prefix` | Tắt, `BATCH-` | Mẫu đánh số lô chung khi mặt hàng không có mẫu riêng |
| `do_not_use_batchwise_valuation` | Tắt | Tắt tính giá theo từng lô (mục 3.2) |
| `allow_negative_stock_for_batch` | Tắt | Cho lô âm. Chính ERPNext ghi rõ là dễ làm sai giá |
| `auto_reserve_serial_and_batch` | Bật | Giữ chỗ hàng thì giữ luôn lô cụ thể |
| `auto_map_raw_materials_to_finished_goods` | Tắt | Khi ghi phiếu sản xuất, tự gắn lô nguyên liệu chưa gắn vào lô thành phẩm theo thứ tự |

### 3.2. Batch (lô)

**Là gì:** một bản ghi danh mục cho mỗi lô của một mặt hàng. Khóa chính là chính số lô (`autoname = field:batch_id`), nên số lô **duy nhất toàn hệ thống**, không chỉ trong một mặt hàng.

**Dùng khi nào:** hàng cần biết *cái đang cầm trên tay thuộc lần sản xuất nào*: thuốc, hóa chất, thực phẩm, phân bón, hàng có hạn dùng.

**Trường trên mặt hàng (Item):**

| Trường | Ý nghĩa |
|---|---|
| `has_batch_no` | Mặt hàng theo dõi lô. Đã có giao dịch thì không đổi được |
| `create_new_batch` | Cho máy tự tạo lô mới khi nhập |
| `batch_number_series` | Mẫu số lô riêng của mặt hàng, ví dụ `UREA-.YY.MM.-.###` |
| `has_expiry_date` | Lô của mặt hàng này bắt buộc có hạn dùng |
| `shelf_life_in_days` | Số ngày sử dụng, để máy tự tính hạn dùng |
| `retain_sample`, `sample_quantity` | Giữ mẫu lưu theo lô, tối đa bao nhiêu |

**Trường trên lô (Batch):** `batch_id`, `item`, `manufacturing_date`, `expiry_date`, `supplier`, `reference_doctype` và `reference_name` (chứng từ sinh ra lô), `parent_batch` (lô gốc khi tách lô), `batch_qty` (tồn hiện tại, tính lại được), `qty_to_produce` và `produced_qty` (khi lô sinh từ lệnh sản xuất), `use_batchwise_valuation`, `disabled`, `description`.

**Luật chính (đọc từ `batch.py`):**

- **Đánh số:** có gõ số lô thì lấy số gõ. Bỏ trống thì máy theo thứ tự: mẫu riêng của mặt hàng, rồi mẫu chung ở Stock Settings, cuối cùng là chuỗi ngẫu nhiên. Mặt hàng không bật `create_new_batch` mà bỏ trống số lô thì báo lỗi *Batch ID is mandatory*.
- **Ngày sản xuất:** bỏ trống thì lấy ngày ghi sổ của chứng từ sinh ra lô, không có thì lấy hôm nay.
- **Hạn dùng:** bỏ trống mà mặt hàng có `shelf_life_in_days` thì máy tính `hạn dùng = ngày sản xuất + số ngày`. Mặt hàng bật `has_expiry_date` mà không có số ngày và không ai gõ hạn thì **chặn lưu**.
- **Giá theo lô:** lô mới **mặc định tính giá riêng từng lô** (`use_batchwise_valuation = 1`). Chỉ khi mặt hàng dùng bình quân di động **và** bật `do_not_use_batchwise_valuation` thì lô mới theo bình quân chung. Đây là điểm DEGO phải chủ động tắt (mục 7.4).
- **Tách lô:** `split_batch` tạo lô con có `parent_batch`, chép ngày sản xuất, hạn dùng, nhà cung cấp từ lô gốc.
- **Khóa lô:** `disabled = 1` thì mọi phiếu xuất dùng lô đó bị chặn.

**Chi phí vận hành:** khi nhập, thủ kho gõ hoặc quét **số lô**, gõ **ngày sản xuất** (hoặc để máy lấy ngày nhập), gõ **hạn dùng** (hoặc để máy tính từ số ngày sử dụng). Lô nội bộ thì không gõ gì, máy tự sinh. Khi xuất, nếu bật tự chọn lô thì **không gõ gì**, chỉ kiểm lại lô máy chọn.

### 3.3. Serial No (số seri)

**Là gì:** một bản ghi cho **từng chiếc** hàng. Trường chính: `serial_no`, `item_code`, `batch_no` (một chiếc có thể nằm trong một lô), `warehouse`, `status`, `purchase_rate`, `customer`, `work_order`, `warranty_period`, `warranty_expiry_date`, `amc_expiry_date`, `maintenance_status`, `asset`, `employee`, `location`.

**Vòng đời (`status`):** `Active` (đang trong kho), `Inactive` (đã tạo, chưa nhập), `Delivered` (đã giao khách), `Consumed` (đã dùng vào sản xuất), `Expired` (hết bảo hành). Trạng thái do máy cập nhật theo chứng từ, không ai sửa tay.

**Dùng khi nào:** hàng giá trị cao, bảo hành từng chiếc, bảo trì theo hợp đồng (AMC), tài sản: máy móc, điện thoại, thiết bị.

**Luật chính:** mặt hàng có `serial_no_series` thì máy tự sinh số seri khi nhập; `use_serial_no_wise_valuation` (mặc định bật) tính giá từng chiếc; `allow_existing_serial_no` cho một số seri đã xuất được nhập lại.

**Chi phí vận hành:** **mỗi chiếc một mã**, thường phải quét mã vạch từng chiếc khi nhập và khi xuất. Một lần nhập 10.000 chai là 10.000 lần quét hoặc một danh sách 10.000 dòng.

### 3.4. Serial and Batch Bundle (gói lô và seri, từ v15)

**Vì sao có:** trước v15, ô `serial_no` trên dòng chứng từ là ô chữ dài, một ô chứa nhiều số seri cách nhau xuống dòng, còn ô `batch_no` chỉ chứa được **một** lô. Hệ quả: không xuất được hai lô trên một dòng, sổ kho phải tách chuỗi để biết chiếc nào đi đâu, chậm và dễ sai. Từ v15 ERPNext đưa toàn bộ phần lô và seri ra một chứng từ con riêng.

**Cấu trúc:**

| Phần | Trường chính |
|---|---|
| Đầu gói (`Serial and Batch Bundle`, số `SABB-########`, có ghi sổ) | `item_code`, `warehouse`, `company`, `has_batch_no`, `has_serial_no`, `type_of_transaction` (`Inward`, `Outward`, `Maintenance`, `Asset Repair`), `voucher_type`, `voucher_no`, `voucher_detail_no` (dòng chứng từ gốc), `total_qty`, `avg_rate`, `total_amount`, `is_rejected` (hàng bị từ chối trên phiếu nhập), `returned_against`, `posting_datetime` |
| Dòng gói (`Serial and Batch Entry`) | `batch_no` hoặc `serial_no`, `qty`, `warehouse`, `incoming_rate`, `outgoing_rate`, `stock_value_difference`, `stock_queue`, `fg_batch_no` và `fg_serial_no` (lô, seri thành phẩm mà dòng nguyên liệu này đi vào) |

Mỗi dòng chứng từ kho (phiếu nhập, phiếu xuất, phiếu giao, phiếu kho) và mỗi dòng sổ kho trỏ tới **một gói**. Một gói chứa **nhiều lô** hoặc nhiều seri với số lượng của từng cái.

**Đỡ gánh cho người dùng:** `use_serial_batch_fields` bật mặc định nên trên màn vẫn thấy ô `batch_no` như cũ; khi ghi sổ máy tự dựng gói. Ai cần nhiều lô trên một dòng thì bấm *Add Serial / Batch No* để mở hộp thoại gói. Bản patch `enable_old_serial_batch_fields` của v15 bật lại các ô cũ cho site nâng cấp.

**Chi phí vận hành:** với lô, người dùng gần như không thấy gói, vì máy tự dựng. Với seri, gói là nơi dán danh sách seri hoặc quét. Chi phí thật nằm ở **mã nguồn và dữ liệu**: thêm hai bảng, mọi báo cáo kho phải nối qua gói.

### 3.5. Chọn lô khi xuất, FEFO, Pick List

**Tự chọn lô:** khi phiếu xuất không ghi lô, máy gọi `get_auto_batch_nos` theo `pick_serial_and_batch_based_on`:

- `FIFO`: lô tạo sớm nhất trước.
- `LIFO`: lô tạo muộn nhất trước.
- `Expiry`: sắp theo `expiry_date` tăng dần, lô không có hạn xếp cuối. Đây là FEFO.

Cả ba cách đều **bỏ qua lô đã hết hạn** (chỉ lấy lô có `expiry_date >= hôm nay` hoặc không có hạn).

**Chặn lô hết hạn và lô khóa:** `stock_controller.validate_batch_is_usable` chặn mọi phiếu xuất dùng lô đã khóa, hoặc lô có hạn dùng trước ngày ghi sổ, báo *The batch ... has already expired*. **Ngoại lệ:** phiếu xuất loại *Material Issue* (xuất dùng, xuất hủy) không bị chặn hạn, để còn tiêu hủy được hàng hết hạn. Trên phiếu kho có nút lấy danh sách **toàn bộ lô hết hạn còn tồn** (`get_expired_batch_items`) để lập phiếu hủy một lần.

**Pick List (phiếu soạn hàng):** chứng từ có ghi sổ, ba mục đích: *Material Transfer for Manufacture* (soạn vật tư cho lệnh sản xuất), *Material Transfer*, *Delivery* (soạn hàng giao khách). Nút *Get Item Locations* tự rải số lượng cần lấy ra từng kho, từng lô theo đúng luật FIFO/LIFO/Expiry ở trên. Có quét mã vạch, cho phép soạn tay (`pick_manually`), dung sai soạn vượt (`over_picking_allowance`). Ghi sổ soạn hàng thì lại kiểm lô hết hạn một lần nữa. Từ phiếu soạn tạo ra phiếu kho hoặc phiếu giao với lô đã điền sẵn.

**Chi phí vận hành:** người soạn chỉ xác nhận số thực lấy; muốn lấy trái lô gợi ý thì sửa ô lô trên dòng.

### 3.6. Lô trong sản xuất

| Bước | ERPNext làm gì |
|---|---|
| Bật | Manufacturing Settings `make_serial_no_batch_from_work_order`. Thành phẩm phải bật `has_batch_no` và `create_new_batch` |
| Lệnh sản xuất (Work Order) | Lệnh mang `has_batch_no`, `batch_size`. Khi duyệt lệnh, `create_batch_for_finished_good` **tạo sẵn lô thành phẩm**: lệnh 1.000 chai, `batch_size` 400 thì sinh ba lô 400, 400, 200; mỗi lô trỏ về lệnh (`reference_doctype = Work Order`), mang `qty_to_produce` |
| Không bật | Lô thành phẩm sinh lúc ghi phiếu *Manufacture* (nhập thành phẩm) |
| Cấp vật tư | Phiếu *Material Transfer for Manufacture* (hoặc Pick List) mang lô nguyên liệu, máy tự chọn theo FIFO/Expiry. Lô nguyên liệu hết hạn bị chặn ở các phiếu *Manufacture*, *Repack*, *Send to Subcontractor* |
| Nhập thành phẩm | Phiếu *Manufacture* có dòng nguyên liệu (xuất) và dòng thành phẩm (nhập). Dòng nguyên liệu trong gói mang `fg_batch_no`: **lô nguyên liệu này đã đi vào lô thành phẩm nào**. Bật `auto_map_raw_materials_to_finished_goods` thì máy tự gắn |
| Gia công ngoài | Phiếu *Send to Subcontractor* mang lô nguyên liệu gửi đi, nhập lại thành phẩm theo *Subcontracting Receipt* có lô |

**Chi phí vận hành:** người lập lệnh gõ thêm `batch_size` nếu muốn chia lô. Thủ kho cấp vật tư không gõ lô nếu bật tự chọn. Người báo hoàn thành không gõ lô thành phẩm nếu lô sinh từ lệnh.

### 3.7. Báo cáo

| Báo cáo | Trả lời câu gì | Lọc, cột chính |
|---|---|---|
| **Batch-Wise Balance History** | Mỗi lô ở mỗi kho: đầu kỳ, nhập, xuất, cuối kỳ | Lọc công ty, từ ngày đến ngày (bắt buộc), mặt hàng, loại kho, kho, lô (bắt buộc chọn một trong mặt hàng, kho, loại kho). Cột: tồn đầu, nhập, xuất, tồn cuối, đơn giá, giá trị |
| **Batch Item Expiry Status** | Lô nào hết hạn trong khoảng ngày, còn bao nhiêu ngày, còn tồn bao nhiêu ở kho nào | Lọc theo **khoảng hạn dùng**, sắp theo hạn tăng dần, cột số ngày còn lại |
| **Available Batch Report** | Hiện còn lô nào, bao nhiêu | Theo mặt hàng, kho |
| **Serial No Ledger** | Một số seri đã đi qua những chứng từ nào | Lọc mặt hàng, kho, số seri |
| **Serial No Status**, **Warranty Expiry**, **Service Contract Expiry** | Trạng thái seri, hạn bảo hành, hạn hợp đồng bảo trì | Theo seri |
| **Serial and Batch Summary** | Gói lô, seri của từng chứng từ | Theo chứng từ |
| **Serial No and Batch Traceability** (mới ở v16) | Truy xuất ngược, xuôi (mục 3.8) | Mặt hàng, lô, seri, hướng `Backward` / `Forward` / `Both` |
| **Stock Qty vs Batch Qty**, **Negative Batch Report**, **Incorrect Serial and Batch Bundle** | Soát lệch giữa tồn chung và tồn theo lô | Dùng cho người quản trị |

### 3.8. Truy xuất ngược và xuôi

ERPNext không có bảng truy xuất riêng. Báo cáo *Serial No and Batch Traceability* đọc **gói lô của sổ kho** rồi lần theo chứng từ:

- **Ngược** (*Backward*, từ thành phẩm về nguồn): lô thành phẩm X sinh từ phiếu *Manufacture* hoặc *Repack* nào; trong phiếu đó dòng nguyên liệu nào có `fg_batch_no = X`; mỗi lô nguyên liệu đó lại nhập từ phiếu nhận hàng nào, của nhà cung cấp nào; nếu nguyên liệu là bán thành phẩm thì lần tiếp một cấp nữa (báo cáo thụt lề theo cấp).
- **Xuôi** (*Forward*, từ nguồn đi ra): lô nguyên liệu Y đã xuất ra những phiếu nào; phiếu nào là phiếu sản xuất thì ra lô thành phẩm nào; lô thành phẩm đó giao cho khách nào theo phiếu giao nào. Đây là danh sách cần khi **thu hồi**.

Điều kiện để truy xuất chạy được: **mọi chứng từ nhập, xuất, sản xuất, giao hàng đều nằm trong ERPNext và đều mang lô.** Thiếu một khâu (ví dụ bán hàng làm ở phần mềm khác) thì chuỗi đứt ở khâu đó.

### 3.9. Liên quan khác

- **Quality Inspection** (phiếu kiểm chất lượng) có trường `batch_no`: kết quả kiểm gắn với lô, không chỉ với phiếu nhập.
- **Giữ mẫu lưu** (`retain_sample`): lô có số mẫu tối đa, phiếu kho chuyển mẫu sang kho mẫu lưu.
- **Giữ chỗ hàng** (Stock Reservation) có thể giữ theo lô cụ thể.

### 3.10. Tổng hợp chi phí vận hành mỗi lần

| Khoảnh khắc | Lô | Serial |
|---|---|---|
| Khai mặt hàng (một lần) | Bật lô, bật hạn dùng, số ngày sử dụng, mẫu số lô | Bật seri, mẫu số seri |
| Nhận hàng mua | Gõ hoặc quét số lô của NCC, ngày sản xuất, hạn dùng (3 ô mỗi dòng; hạn tự tính nếu có số ngày). Hai lô trên một lần giao thì tách dòng hoặc mở hộp thoại gói | Quét **từng chiếc** |
| Xuất (cấp vật tư, bán, chuyển) | Không gõ nếu bật tự chọn; kiểm lô máy gợi ý | Quét từng chiếc, hoặc máy tự chọn |
| Sản xuất | `batch_size` trên lệnh nếu chia lô | Máy sinh seri thành phẩm |
| Kiểm kê | Đếm **theo từng lô** | Đếm và quét từng chiếc |
| Hủy hàng hết hạn | Một nút lấy danh sách lô hết hạn | Không áp dụng |

---

## 4. ERP DEGO hiện có gì

### 4.1. Mã nguồn

Tìm các tên `lot_no`, `lot_code`, `batch_no`, `expiry_date`, `mfg_date`, `shelf_life`, `số lô`, `hạn dùng` trong toàn `backend/app`: **không có kết quả nào thuộc phần hàng hóa và kho.** Mọi chỗ khớp `expiry_date` đều thuộc hồ sơ giấy tờ (`dossier`), nghỉ phép (`leave`) hoặc khóa phiên làm việc.

| Bảng | Có gì | Thiếu gì cho lô |
|---|---|---|
| `tab_product` (`product/model.py`) | Mã SKU, tên, phân loại, ĐVT, thông số kỹ thuật, `is_active` | Không có cờ theo dõi lô, cờ hạn dùng, số ngày sử dụng |
| `tab_po_delivery` (`purchase_order/model.py`) | Một lần giao của một dòng đơn: kho, số giao, số nhận, ngày nhận, số hóa đơn, `qc_result` (Đạt, Thiếu, Lỗi) | Không có số lô, ngày sản xuất, hạn dùng. Một lần giao một kết quả QC |
| `tab_goods_receipt` (`goods_receipt/model.py`) | Phiếu nhập **sinh ngầm** từ lần giao: một phiếu, một mặt hàng, một số lượng | Không có lô; không có phiếu nhập do thủ kho lập |
| `tab_inventory` (`inventory/model.py`) | Tồn theo khóa (công ty, kho, mã hàng), số lượng, giá bình quân, giá trị | Không có chiều lô |
| `tab_inventory_move` | Sổ phát sinh: số lượng, đơn giá, `ref_type` chỉ có `gr` (nhận hàng) và `adjust` (điều chỉnh) | Không có cột lô; **chưa có phiếu xuất** nên chưa có gì để chọn lô |
| `tab_warehouse` (`catalog/model.py`) | Danh mục kho | Không có kho cách ly, kho mẫu lưu |

### 4.2. Thứ dùng lại được

- **Luật tình trạng hiệu lực của hồ sơ** (`dossier/expiry.py`): *hết hạn* và *sắp hết hạn* **suy ra từ ngày**, không lưu cột; một hàm duy nhất trả về (mã tình trạng, số ngày còn lại), nhận `today` làm tham số để bài kiểm không phụ thuộc ngày chạy. Hạn dùng của lô nên đi đúng khuôn này, kể cả lời dặn *không chép luật ngày sang TypeScript*.
- **Thẻ cảnh báo trên bảng điều khiển** (`dashboard/controller.py`) đã có khuôn *quá hạn* và *sắp tới hạn*; thêm thẻ *lô sắp hết hạn* theo cùng khuôn.
- **Luật trạng thái `SMALLINT` + `IntEnum`** cho trạng thái lô (dùng được, tạm giữ, khóa).

### 4.3. Thứ làm ngoài ERP

- Sheet **Kết quả KCS Kho Dr Xanh**: mỗi lần nhận thành phẩm, kho ghi ngày nhận, mã và tên hàng, số yêu cầu và số thực nhận, **ngày sản xuất, số lô, hạn dùng**, phụ kiện, ngoại dạng, chứng từ NCC, số đạt và không đạt ([08 câu C54](../../nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md)).
- **Sự cố sau sản xuất**: Kinh doanh gửi ảnh, mã, **ngày sản xuất**, số lượng; người xử lý sự cố đưa phương án; Kinh doanh **thu hồi hàng** ([07 mục 6](../../nghien-cuu/07-san-xuat-khao-sat-tra-loi-chung-2610.md)). Không có lô trên hệ thống thì không trả lời được câu *lô đó đã bán cho ai*.
- **Xuất kho mẫu cho Lab** đi qua MISA, do Kinh doanh xuất ([08 câu C63](../../nghien-cuu/08-san-xuat-cau-tra-loi-trich-duoc-2610.md)).

---

## 5. Bên sản xuất và luật ngành có đòi lô, hạn dùng không

### 5.1. Câu A3 đang ở đâu

Câu A3 (*có theo dõi lô và hạn dùng không, khách có đòi truy xuất ngược không*) có ở [san-xuat/00 mục 14](../../san-xuat/00-tong-quan-nghiep-vu.md), là câu S2 ở doc 01 và câu C5 ở [kế hoạch theo module](../../../plans/00-ke-hoach-theo-module.md). Doc 01 việc 2.10 chỉ làm lô *nếu* A3 là có. Khảo sát 24/10 ([02 mục 7](../../nghien-cuu/02-phan-tich-khao-sat-hien-trang-san-xuat.md)) ghi *chưa ai nói*, đã đặt câu hỏi lại H-J cho CV Điều phối NL/BTP và Kế toán. Khảo sát 26/10 cũng chưa trả lời thẳng câu này.

**Nhưng câu trả lời gián tiếp đã có:** kho đang ghi số lô, ngày sản xuất, hạn dùng cho từng lần nhận thành phẩm (mục 4.3), và luật bắt buộc in chúng trên nhãn (mục 5.2). Câu còn phải hỏi không phải là *có cần không* mà là **áp tới đâu** (mục 9).

### 5.2. Mô hình sản xuất ảnh hưởng thế nào

| Đường | Ai đặt số lô | ERP cần gì |
|---|---|---|
| **Gia công tại NCC** (hình thức chính, khoảng 42 đơn thành phẩm mỗi tháng, NCC như Hà Long, Yamato, An Nông, Basel) | NCC gia công in số lô, ngày sản xuất, hạn dùng lên bao bì | **Ghi lại** lô của NCC lúc nhận thành phẩm về kho. Truy ngược tới nguyên liệu, bao bì DEGO gửi NCC chỉ làm được nếu phiếu gửi gia công cũng mang lô |
| **Nhà máy Dego Organic** (chiết rót, đóng gói) | Nhà máy tự đặt số lô theo lệnh, ca hoặc ngày | **Sinh** lô thành phẩm từ lệnh hoặc phiếu nhập thành phẩm; ánh xạ lô nguyên liệu vào lô thành phẩm |

### 5.3. Luật ghi nhãn và truy xuất

| Văn bản | Nội dung liên quan | Ảnh hưởng tới ERP |
|---|---|---|
| **Nghị định 43/2017/NĐ-CP** về nhãn hàng hóa, sửa đổi bởi **Nghị định 111/2021/NĐ-CP**, Phụ lục I | **Phân bón** (mục 56): loại phân bón, mã số phân bón, định lượng, **ngày sản xuất, hạn sử dụng**, thành phần, cảnh báo, hướng dẫn. **Thuốc bảo vệ thực vật** (mục 20): định lượng, **ngày sản xuất, hạn sử dụng**, thành phần hàm lượng, cảnh báo, hướng dẫn. **Hóa chất** (mục 55): ngày sản xuất, hạn sử dụng (nếu có) | Mỗi đơn vị thành phẩm bán ra phải có ngày sản xuất và hạn dùng. ERP phải biết hai ngày này **theo lô** thì mới đối chiếu được nhãn, báo hết hạn, và chọn xuất đúng |
| **Thông tư 21/2015/TT-BNNPTNT** về quản lý thuốc bảo vệ thực vật, phần ghi nhãn | Quy định cách ghi ngày sản xuất, hạn sử dụng, và **số lô sản xuất** (*Số lô sản xuất: XXXX* hoặc *Số lô SX: XXXX*) trên nhãn thuốc | Thuốc bảo vệ thực vật bắt buộc có số lô trên bao bì, nên kho nhận hàng gia công luôn có số lô để ghi |
| **Thông tư 02/2024/TT-BKHCN** về quản lý truy xuất nguồn gốc sản phẩm, hàng hóa (ban hành 28/03/2024, hiệu lực 01/06/2024) | Khung quản lý hệ thống truy xuất nguồn gốc và mã truy vết sản phẩm | Không bắt mọi doanh nghiệp phải có hệ thống truy xuất, nhưng nếu thương hiệu dùng tem truy xuất hoặc khách lớn đòi thì đơn vị truy vết thực tế là **lô** |
| **Nghị định 84/2019/NĐ-CP** về quản lý phân bón, sửa đổi bởi **Nghị định 130/2022/NĐ-CP** | Điều kiện sản xuất, buôn bán, công bố hợp quy, kiểm tra chất lượng phân bón | Kiểm tra chất lượng và xử lý vi phạm thường làm theo lô hàng; cần pháp chế xác nhận điều khoản cụ thể |

**Giới hạn của mục này:** tra trên nguồn nhà nước và trang pháp luật công khai ngày 02/11/2026. Thông tư 21/2015 và Nghị định 84/2019 có thể đã được sửa hoặc thay sau khi sáp nhập Bộ Nông nghiệp và Môi trường năm 2025. **Chị Nguyễn Ngọc Bảo Thi (Pháp lý, sự cố) nên xác nhận bản hiện hành** trước khi đưa vào tài liệu yêu cầu. Kết luận *phải có ngày sản xuất, hạn dùng trên thành phẩm* thì vững vì nằm trong cả hai nghị định về nhãn.

---

## 6. Bảng fit-gap và tỷ lệ phủ

Cách chấm theo [doc 11 mục 2](../../nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md#2-cách-chấm): **Có** = 1, **Một phần** = 0,5, **Chưa** = 0. Cột *DEGO cần* là đề xuất của mục 7.

| # | Chức năng | ERPNext v16 | ERP DEGO | Điểm | DEGO cần |
|---|---|---|---|---|---|
| 1 | Cờ theo dõi lô theo mã hàng | `has_batch_no` | Chưa | 0 | Cần |
| 2 | Cờ hạn dùng và số ngày sử dụng | `has_expiry_date`, `shelf_life_in_days` | Chưa | 0 | Cần |
| 3 | Danh mục lô có ngày sản xuất, hạn dùng, NCC, chứng từ gốc | `Batch` | Chưa | 0 | Cần |
| 4 | Đánh số lô tự động theo mẫu | `create_new_batch`, `batch_number_series` | Chưa | 0 | Cần (lô nội bộ, lô nhà máy) |
| 5 | Ghi lô khi nhận hàng mua | Phiếu nhập + gói lô | Chưa (chỉ có ở sheet KCS ngoài hệ thống) | 0 | Cần |
| 6 | Tồn kho theo lô | Sổ kho + gói lô | Chưa | 0 | Cần |
| 7 | Xuất kho chọn lô, gợi ý FEFO | `pick_serial_and_batch_based_on = Expiry` | Chưa (chưa có phiếu xuất) | 0 | Cần |
| 8 | Chặn lô hết hạn, khóa lô | `validate_batch_is_usable`, `disabled` | Chưa | 0 | Cần |
| 9 | Kiểm chất lượng gắn lô | `Quality Inspection.batch_no` | **Một phần**: `qc_result` theo lần giao; một lần giao thường là một lô nhưng không ghi lô nào | 0,5 | Cần |
| 10 | Báo cáo lô sắp hết hạn | Batch Item Expiry Status | Chưa (luật cảnh báo hạn chỉ có cho hồ sơ giấy tờ) | 0 | Cần |
| 11 | Nhập xuất tồn theo lô | Batch-Wise Balance History | Chưa | 0 | Cần |
| 12 | Lô thành phẩm sinh từ lệnh sản xuất | Work Order + `make_serial_no_batch_from_work_order` | Chưa (chưa có lệnh sản xuất) | 0 | Cần (nhà máy Dego Organic) |
| 13 | Ánh xạ lô nguyên liệu vào lô thành phẩm | `fg_batch_no`, `auto_map_raw_materials_to_finished_goods` | Chưa | 0 | Cần |
| 14 | Truy xuất ngược và xuôi | Serial No and Batch Traceability | Chưa | 0 | Cần |
| 15 | Phiếu soạn hàng theo lô | Pick List | Chưa | 0 | Để sau |
| 16 | Nhiều lô trên một dòng chứng từ | Serial and Batch Bundle | Chưa | 0 | **Không** (tách dòng, mục 7.4) |
| 17 | Số seri từng chiếc, vòng đời, bảo hành | Serial No | Chưa | 0 | **Không** (mục 7.3) |
| 18 | Giữ mẫu lưu theo lô | `retain_sample` | Chưa (mẫu Lab xuất qua MISA) | 0 | Để sau |

**Tỷ lệ phủ:**

| Phạm vi | Điểm | Tỷ lệ |
|---|---|---|
| Toàn bộ 18 chức năng của ERPNext | 0,5 / 18 | **3 %** |
| 14 chức năng DEGO cần (dòng 1 đến 14) | 0,5 / 14 | **4 %** |
| Sau nấc L1 (dòng 1 đến 6, 9, 10, 11) | 9 / 14 | 64 % |
| Sau nấc L2 (thêm dòng 7, 8) | 11 / 14 | **79 %** |
| Sau nấc L3 (thêm 12, 13, nửa dòng 14 phần truy ngược) | 13,5 / 14 | 96 % |
| Sau nấc L4 (truy xuôi tới khách) | 14 / 14 | 100 % phần cần; 14 / 18 = 78 % so với ERPNext, **cố ý** không làm 15 đến 18 |

Doc 11 dòng A3 chấm *Chưa 0* cho cả cụm; bảng này tách cụm đó ra 18 dòng và khớp kết luận.

---

## 7. Đề xuất cho DEGO

### 7.1. Có cần lô và hạn dùng không

**Có.** Ba lý do, xếp từ cứng tới mềm:

1. **Luật:** thành phẩm phân bón và thuốc bảo vệ thực vật phải in ngày sản xuất, hạn dùng; thuốc bảo vệ thực vật phải in số lô (mục 5.3).
2. **Thu hồi:** quy trình sự cố sau sản xuất đã có bước thu hồi hàng. Không có lô thì thu hồi theo mã hàng, tức là thu cả những lô không lỗi.
3. **Hàng hết hạn nằm kho:** không có hạn dùng trên hệ thống thì không ai thấy lô sắp hết hạn cho tới khi khách trả về.

### 7.2. Áp cho nhóm hàng nào

| Nhóm | Ví dụ | Theo lô | Hạn dùng | Lý do |
|---|---|---|---|---|
| **Thành phẩm** | Phân bón lá đóng chai, thuốc bảo vệ thực vật đóng gói | **Bắt buộc** | **Bắt buộc** | Luật nhãn, thu hồi |
| **Bán thành phẩm** phối trộn | Dung dịch phối trộn chờ chiết | Bắt buộc nếu có tồn qua ngày | Theo công thức | Mắt xích giữa nguyên liệu và thành phẩm khi truy ngược |
| **Nguyên liệu có hạn hoặc nhạy** | Hoạt chất thuốc bảo vệ thực vật, humic dạng lỏng, chế phẩm vi sinh, phụ gia | **Nên bật** | Theo nhãn NCC | Hàng có hạn thật; lỗi thành phẩm thường truy về đây |
| **Nguyên liệu rời ổn định** | Urê, KCl, MAP, K₂SO₄ bao 50 kg | **Q-L1 chốt** | Thường không | Gần như không hết hạn; nhưng nhập khẩu theo lô có chứng thư chất lượng riêng, có thể cần cho truy ngược |
| **Bao bì, vật tư** | Chai PET, nắp, nhãn, thùng, màng co, cốc đong | **Không** | Không | Giá trị thấp, không hết hạn, không nằm trong yêu cầu nhãn. Lỗi bao bì truy theo NCC và lần giao là đủ |

Cờ đặt **theo từng mã** nhưng nên có **mặc định theo phân loại** (`tab_item_group`) để khai một lần cho cả nhóm.

### 7.3. Serial có cần không

**Không.** Giải thích:

- Hàng của DEGO là hàng **đồng loạt**: một mẻ chiết hàng nghìn chai giống hệt nhau, cùng ngày sản xuất, cùng hạn. Đơn vị cần phân biệt là **lô**, không phải từng chai.
- Không có **bảo hành từng chiếc** hay hợp đồng bảo trì, là hai lý do chính để có serial trong ERPNext.
- Luật nhãn không đòi số seri cho phân bón, thuốc bảo vệ thực vật (danh mục Phụ lục I chỉ đòi số lô hoặc số seri ở nhóm trang thiết bị y tế).
- Chi phí vận hành rất lớn: mỗi chai một mã, quét lúc nhập và lúc xuất.
- Nếu một thương hiệu muốn **tem QR chống giả hoặc truy xuất từng chai**, đó là hệ thống tem riêng (in, kích hoạt, tra cứu), **trỏ về số lô** của ERP; ERP không cần quản từng mã tem.
- Thứ duy nhất có thể cần seri là máy móc, thiết bị của nhà máy, và đó là việc của phân hệ tài sản, không phải kho hàng.

### 7.4. Mức tối giản đủ dùng

**Năm quyết định thiết kế:**

1. **Lô là chiều của tồn kho, không phải biến thể sản phẩm.** `tab_product` vẫn là SKU, `product_code` vẫn là hạt của bảy bảng. Lô thêm một chiều cho **sổ kho và tồn kho** như kho đang là một chiều. Không thêm bảng nào **dưới** `tab_product` theo nghĩa biến thể, đúng [mục 11 của mô hình dữ liệu sản phẩm](../../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md#11-cấm-làm). ERPNext cũng làm vậy: `Batch` trỏ tới `Item`, không thay `Item`.
2. **Một dòng chứng từ một lô.** Một lần giao có hai lô thì tách hai dòng. Không dựng *Serial and Batch Bundle*: ERPNext cần nó chủ yếu vì serial; với lô thuần, tách dòng là đủ và báo cáo không phải nối thêm hai bảng.
3. **Không tính giá theo lô.** Giá vẫn bình quân theo (công ty, kho, mã hàng) như `tab_inventory` hiện tại, cho tới khi kế toán chốt câu K3 ở doc 01. Lô chỉ theo dõi **số lượng, ngày, nguồn gốc**. Đây chính là cấu hình `do_not_use_batchwise_valuation` của ERPNext.
4. **Hết hạn suy ra từ ngày, không lưu cột.** Đi đúng khuôn `dossier/expiry.py`. Trạng thái do người đặt (dùng được, tạm giữ chờ kiểm, khóa) lưu `SMALLINT` + `IntEnum`.
5. **Chứng từ là bản chụp.** Dòng sổ kho chép cả `lot_id` lẫn `lot_no`, như `product_code` đang được chép.

**Phác thảo dữ liệu** (để Agent 1 duyệt, chưa phải thiết kế chốt):

| Chỗ | Thêm gì | Ghi chú |
|---|---|---|
| `tab_product` | `track_lot` (bool, mặc định tắt), `track_expiry` (bool, mặc định tắt), `shelf_life_days` (số nguyên, để trống được) | Ba cột, đều là thuộc tính của **SKU**: hạn dùng phụ thuộc cả công thức lẫn bao bì (chai và bao cùng công thức có thể khác hạn), nên đặt ở SKU là đúng hạt, không phạm luật *không nhét thông tin cấp họ vào dòng variant*. `ProductOut` chỉ **thêm** trường |
| `tab_item_group` | Ba cột mặc định cùng tên | Khai mã mới thì chép mặc định theo phân loại |
| `tab_stock_lot` (mới) | `product_code`, `lot_no`, `mfg_date`, `expiry_date`, `supplier_code`, `source_type` (nhận hàng, sản xuất, đầu kỳ, nội bộ), `source_id`, `status`, `note`; duy nhất theo (`product_code`, `lot_no`) | Khác ERPNext: số lô **duy nhất trong một mã**, không duy nhất toàn hệ, vì hai NCC khác nhau có thể cùng in số lô `2410` |
| `tab_inventory_move` | `lot_id`, `lot_no` (mặc định 0 và rỗng) | Luật *CSDL cũ chỉ thêm, không sửa* giữ được: mã không theo lô có `lot_id = 0` |
| `tab_inventory_lot` (mới) | Tồn theo (công ty, kho, mã hàng, lô): số lượng | Không có giá. Tổng theo lô phải bằng `tab_inventory.qty`, có bài kiểm canh |
| Dòng phiếu nhập, phiếu xuất (nấc 2 doc 01) | Ô lô, ngày sản xuất, hạn dùng trên dòng | Ô chỉ hiện khi mã có `track_lot` |

**Chi phí vận hành DEGO sau khi làm:**

| Ai | Lúc nào | Phải nhập gì |
|---|---|---|
| Thủ kho | Nhận hàng mã có lô | Số lô in trên bao bì, ngày sản xuất, hạn dùng (bỏ trống thì máy tính từ số ngày sử dụng). Bao bì không có lô: bấm *tạo lô nội bộ*, máy sinh số theo ngày nhập (tình huống A4 doc 10) |
| Thủ kho | Xuất | Không gõ: máy gợi ý lô theo FEFO, thủ kho xác nhận hoặc đổi |
| QC, Lab | Kết luận kiểm | Kết luận gắn vào lô, đổi trạng thái lô sang dùng được hoặc khóa |
| Kho | Kiểm kê | Đếm theo từng lô cho mã có lô |
| Người quản danh mục | Một lần | Bật cờ theo phân loại, nhập số ngày sử dụng cho thành phẩm |

---

## 8. Kế hoạch theo nấc

Đặt **sau kho lõi**, cụ thể là gắn vào nấc 2 *Kho đúng chuẩn* của [doc 01 mục 8.2](../../nghien-cuu/01-luong-chuan-mua-hang-kho-san-xuat.md#82-nấc-2--kho-đúng-chuẩn). Độ lớn ước theo ngày làm của một người, chưa tính viết tài liệu yêu cầu và HDSD.

| Nấc | Nội dung | Phụ thuộc | Độ lớn | Phủ sau nấc |
|---|---|---|---|---|
| **L0** | Chốt các câu ở mục 9; pháp chế xác nhận văn bản hiện hành; lấy mẫu số lô đang dùng ở NCC gia công và nhà máy; danh sách số ngày sử dụng của thành phẩm | Không | Nhỏ, 1 đến 2 ngày họp và gom số liệu | 4 % |
| **L1** | Cờ lô và hạn dùng trên sản phẩm và phân loại; `tab_stock_lot`; ô lô trên **phiếu nhập kho thật**; sổ kho và tồn theo lô; QC kết luận theo lô; báo cáo nhập xuất tồn theo lô; báo cáo và thẻ *lô sắp hết hạn* 30, 60, 90 ngày; **kiểm kê đầu kỳ theo lô** | **Làm cùng** việc 2.1 (phiếu nhập thật), 2.2 (trạng thái tồn), 2.3 (sổ kho chỉ ghi thêm). Không làm trước, vì phiếu nhập hiện sinh ngầm từ lần giao | Vừa, 6 đến 8 ngày | 64 % |
| **L2** | Phiếu xuất và chuyển kho mang lô; gợi ý FEFO; chặn lô hết hạn và lô khóa (trừ xuất hủy); nút lấy danh sách lô hết hạn để lập phiếu hủy; kiểm kê theo lô; xử lý xuất nhầm lô bằng phiếu đảo (tình huống B3 doc 10) | Việc 2.5 (phiếu xuất), 2.6 (chuyển kho), 2.7 (kiểm kê) | Vừa, 4 đến 6 ngày | 79 % |
| **L3** | Lô thành phẩm sinh từ lệnh sản xuất của nhà máy theo mẫu số; ghi lô NCC khi nhận thành phẩm gia công; phiếu gửi vật tư đi gia công mang lô; ánh xạ lô nguyên liệu vào lô thành phẩm; báo cáo **truy ngược** | SX2-1 (BOM, lệnh sản xuất, phiếu xuất sản xuất, nhập thành phẩm) và đơn gia công | Vừa, 5 đến 7 ngày | 96 % |
| **L4** | **Truy xuôi** tới khách và danh sách thu hồi | Phân hệ bán hàng trên ERP, hoặc nạp phiếu xuất bán có lô từ MISA | Nhỏ đến vừa, tùy đường MISA | 100 % phần cần |
| Không làm | Serial, gói nhiều lô trên một dòng, giá theo lô | | | |
| Để sau | Phiếu soạn hàng theo lô; mẫu lưu theo lô | Khi có kho thành phẩm đủ lớn, khi Lab muốn quản mẫu lưu trên ERP | | |

**Vì sao không làm sớm hơn:** hôm nay chưa có phiếu xuất nào, nên tồn theo lô chỉ có chiều nhập. Làm lô trên phiếu nhập sinh ngầm hiện tại rồi tới nấc 2 bỏ phiếu ngầm thì làm hai lần.

**Vì sao không làm muộn hơn:** doc 01 đã nói rõ, số lô phải có **từ lúc nhận hàng**. Bật lô sau khi kho đã chạy thì tồn cũ không có lô, phải kiểm kê lại theo lô lần hai, và mọi phiếu nhập đã ghi phải coi là *lô không rõ*.

**Rủi ro chính:**

- Kiểm kê đầu kỳ theo lô tốn công gấp nhiều lần kiểm kê theo mã. Phương án dự phòng: tồn cũ gom vào một lô *ĐẦU KỲ* cho mỗi mã, hạn dùng lấy theo lô cũ nhất còn trên kệ; lô thật bắt đầu từ phiếu nhập đầu tiên sau ngày chốt.
- Hàng đang nằm ở **kho NCC gia công** (bao bì, nguyên liệu DEGO gửi đi) không đếm theo lô được nếu NCC không ghi lô. Bao bì đã không theo lô nên ít ảnh hưởng.

---

## 9. Câu cần chốt

Theo luật 19/10, các câu cách làm hỏi Agent 1 trước; câu nghiệp vụ hỏi đúng người ở cột *Hỏi ai*.

| # | Câu hỏi | Hỏi ai | Nghiêng về | Chặn nấc |
|---|---|---|---|---|
| Q-L1 | Nguyên liệu rời ổn định (urê, KCl, MAP, K₂SO₄) có theo lô không, hay chỉ theo lô nguyên liệu có hạn? | CV Điều phối NL/BTP, R&D, Lab | Theo lô nếu là hàng nhập khẩu có chứng thư chất lượng riêng; không thì tắt | L1 |
| Q-L2 | Xác nhận bao bì không theo lô | Điều phối bao bì | Không theo lô | L1 |
| Q-L3 | Mẫu số lô nhà máy Dego Organic đang dùng (theo ngày, ca, lệnh?) và mẫu NCC gia công hay in | Nhà máy, Điều phối thành phẩm | Lấy đúng mẫu đang in, không đặt mẫu mới | L1, L3 |
| Q-L4 | Hạn dùng gõ theo bao bì hay tính từ ngày sản xuất cộng số ngày sử dụng? Ai giữ danh sách số ngày sử dụng của từng thành phẩm | Pháp lý, R&D | Tính tự động, cho sửa tay khi bao bì ghi khác | L1 |
| Q-L5 | FEFO là **gợi ý** hay **bắt buộc**? Ai được xuất trái FEFO | Trưởng kho, Kinh doanh | Gợi ý; xuất trái phải ghi lý do | L2 |
| Q-L6 | Lô hết hạn: chặn hẳn hay cho xuất có duyệt (hạ cấp, tái chế, xuất hủy)? | Pháp lý, Trưởng phòng Sản xuất | Chặn mọi đường trừ xuất hủy và xuất tái chế có duyệt | L2 |
| Q-L7 | Ngưỡng cảnh báo sắp hết hạn: 30, 60, 90 ngày hay theo từng nhóm hàng | Kinh doanh, kho | 90/60/30 chung, sửa được trong cấu hình | L1 |
| Q-L8 | Bán hàng nằm ở MISA. Truy xuôi tới khách lấy số liệu từ đâu: nạp phiếu xuất bán có lô từ MISA, hay chờ phân hệ bán hàng? | Kế toán, đại ca | Chờ tích hợp MISA ở nấc 3 doc 01; trước đó truy xuôi dừng ở *đã xuất bán ngày nào, phiếu nào* | L4 |
| Q-L9 | Kiểm kê đầu kỳ: đếm thật theo lô hay gom lô *ĐẦU KỲ*? | Trưởng kho, Kế toán | Đếm thật cho thành phẩm; gom cho nguyên liệu | L1 |
| Q-L10 | Một lần giao có nhiều lô: chấp nhận tách nhiều dòng trên phiếu nhập không? | Thủ kho | Chấp nhận | L1 |
| Q-L11 | Bảng lô dùng `Date` (như `tab_dossier.expiry_date`) hay `String(10)` (như ngày trên chứng từ thu mua)? | Agent 1 | `Date`, vì cần cộng ngày và lọc theo khoảng hạn | L1 |
| Q-L12 | Kết quả Lab theo lô có đổi trạng thái lô (chờ kiểm sang dùng được) không, hay chỉ ghi chú? | Lab, Trưởng nhóm Điều phối (câu H-I doc 02) | Đổi trạng thái, nối việc 2.2 doc 01 | L1 |

---

## 10. Nguồn

**ERPNext (đọc trực tiếp, chỉ đọc):**

- Site học, bản `16.53.0`: `apps/erpnext/erpnext/stock/doctype/batch/batch.json`, `batch.py` (`autoname`, `set_batchwise_valuation`, `set_manufacturing_date`, `set_expiry_date`, `split_batch`); `serial_no/serial_no.json`; `serial_and_batch_bundle/serial_and_batch_bundle.json`, `serial_and_batch_bundle.py` (`get_auto_batch_nos`, `get_non_expired_batches`, thứ tự theo `Expiry`); `serial_and_batch_entry.json`; `item/item.json`; `stock_settings/stock_settings.json`; `pick_list/pick_list.py` (`validate_expired_batches`, `get_available_item_locations_for_batched_item`); `controllers/stock_controller.py` (`validate_batch_is_usable`); `stock_entry/stock_entry.py` (`get_expired_batch_items`, chặn lô hết hạn ở phiếu sản xuất); `manufacturing/doctype/work_order/work_order.py` (`create_serial_no_batch_no`, `create_batch_for_finished_good`); `manufacturing_settings.json`; các báo cáo ở `stock/report/` nêu tại mục 3.7.
- Tài liệu chính thức: `https://docs.frappe.io/erpnext/serial-and-batch`, `https://docs.frappe.io/erpnext/user/manual/en/batch`, `https://docs.frappe.io/erpnext/serial-no`, `https://docs.frappe.io/erpnext/serial-and-batch-bundle`, `https://docs.frappe.io/erpnext/serial-and-batch-traceability-report`.
- Mã nguồn công khai: `github.com/frappe/erpnext`, nhánh `version-16`, cùng các đường dẫn trên.

**ERP DEGO:** `backend/app/modules/product/model.py`, `goods_receipt/model.py`, `inventory/model.py`, `inventory/service.py`, `purchase_order/model.py` (`PODelivery`), `catalog/model.py`, `dossier/expiry.py`, `import_tool/model.py`, `dashboard/controller.py`.

**Tài liệu nội bộ:** doc 01 mục 4.6, 7, 8.2, 9; doc 02 mục 7, 8; doc 07 mục 6; doc 08 câu C54, C63; doc 10 mục kho và tình huống A4, B3; doc 11 dòng A3; `san-xuat/00` mục 13.2, 14; `00-ke-hoach-theo-module.md` câu C5, việc SX2-2; `tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md` mục 1, 2, 10, 11.

**Văn bản nhà nước (tra 02/11/2026):**

- Nghị định 111/2021/NĐ-CP sửa đổi Nghị định 43/2017/NĐ-CP về nhãn hàng hóa, Phụ lục I: bản trên `vcci.com.vn` và `thuvienphapluat.vn`; bản PDF gốc trên `vfa.gov.vn`.
- Thông tư 21/2015/TT-BNNPTNT về quản lý thuốc bảo vệ thực vật: `vbpl.vn` (Cơ sở dữ liệu quốc gia về pháp luật), `thuvienphapluat.vn`.
- Thông tư 02/2024/TT-BKHCN về quản lý truy xuất nguồn gốc sản phẩm, hàng hóa: `vanban.chinhphu.vn` (docid 209961).
- Nghị định 84/2019/NĐ-CP về quản lý phân bón: `vanban.chinhphu.vn` (docid 198327); Nghị định 130/2022/NĐ-CP sửa đổi: `chinhphu.vn` (docid 207115).
