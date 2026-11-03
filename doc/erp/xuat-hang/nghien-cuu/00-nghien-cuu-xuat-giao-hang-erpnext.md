# NGHIÊN CỨU XUẤT KHO, GIAO HÀNG VÀ KẾT NỐI BÁN HÀNG — SO ERPNEXT V16 VỚI ERP DEGO

| | |
|---|---|
| Bản | 1.0 — 02/11/2026 |
| Mục đích | Mô tả chiều **ra** của kho theo chuẩn ERPNext v16 (xuất dùng nội bộ, xuất cho sản xuất ở mức chứng từ kho, giao hàng bán), đối chiếu với ERP DEGO bằng bảng fit-gap có chấm điểm, rồi đề xuất thứ tự làm theo nấc |
| Mốc so sánh | ERPNext **v16.53.0** trên site học (`erpnext-hoc-backend-1`, site `frontend`, chỉ đọc), tài liệu `docs.frappe.io/erpnext`, mã `frappe/erpnext` nhánh `version-16` |
| Mã soát | nhánh `erp-v2` ngày 02/11/2026 (`backend/app/modules`, `frontend-v2/src/modules`) |
| Đọc kèm | [`../nghien-cuu/01`](../../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md) mục 4.3, 5.3–5.4, 7, 8 · [`../nghien-cuu/10`](../../kho/nghien-cuu/10-nghiep-vu-kho.md) mục 7, 9, 10, 15 nhóm B · [`../nghien-cuu/11`](../../thu-mua/nghien-cuu/11-do-phu-thu-mua-kho-so-voi-erpnext.md) dòng F4, F5 · [`../00-ke-hoach-theo-module.md`](../../../plans/00-ke-hoach-theo-module.md) TM-GN-4, SX2-1, KH3-1 · `ke-hoach/02-danh-sach-cong-viec.md` mục 30.4 (ngoài repo, thư mục cha) |
| Trạng thái | Chỉ nghiên cứu. Không sửa mã, không ghi dữ liệu |

## Mục lục

1. [Kết luận trong một trang](#1-kết-luận-trong-một-trang)
2. [Phạm vi và cách chấm](#2-phạm-vi-và-cách-chấm)
3. [ERPNext v16: chiều ra của kho](#3-erpnext-v16-chiều-ra-của-kho)
4. [ERP DEGO hiện có gì](#4-erp-dego-hiện-có-gì)
5. [Bảng fit-gap và tỷ lệ phủ](#5-bảng-fit-gap-và-tỷ-lệ-phủ)
6. [Đề xuất cho DEGO](#6-đề-xuất-cho-dego)
7. [Kế hoạch theo nấc](#7-kế-hoạch-theo-nấc)
8. [Câu hỏi cần chốt](#8-câu-hỏi-cần-chốt)
9. [Nguồn](#9-nguồn)

---

## 1. Kết luận trong một trang

- ERP DEGO **chưa có chiều ra của kho**. Sổ kho `tab_inventory_move` chỉ có hai loại phát sinh: `gr` (nhận hàng từ đơn mua) và `adjust` (điều chỉnh tay). Mọi lần lấy hàng ra hiện phải đi bằng *điều chỉnh âm*, không có chứng từ, không có mục đích chi phí, không chặn tồn âm.
- Phân hệ **Bán hàng** và **Khách hàng** trên giao diện v2 mới là **vỏ** (`enabled: false`), máy chủ không có bảng khách hàng, đơn bán hay phiếu giao.
- Mảnh mạnh nhất DEGO đang có là **Đặt xe giao hàng** (`vehicle_booking`, `request_type = TYPE_DELIVERY`): xe có tải trọng tấn, tài xế nội bộ và thuê ngoài, nhiều điểm dừng có người liên hệ, điều phối, trạng thái tài xế, giờ chạy thực tế, km, chi phí, màn *Chuyến của tôi*, báo cáo. Đây là nền tốt cho **Delivery Trip** của ERPNext, chỉ thiếu sợi nối sang chứng từ kho.
- Tính trên **31 chức năng** của mảng xuất và giao hàng, ERP DEGO phủ **6,5 / 31 = 21 %**. Riêng phần xuất nội bộ và xuất cho sản xuất (nền và nhóm B) chỉ đạt **3,5 / 13 = 27 %**; phần giao hàng bán 14 %.
- Đề xuất thứ tự: **xuất dùng nội bộ và đề nghị lĩnh vật tư trước**, rồi **xuất cho sản xuất** khi có lệnh sản xuất, **giao hàng bán sau cùng** và chỉ khi ban lãnh đạo chốt công ty bán hàng qua ERP (câu hỏi đã treo ở `ke-hoach/02` mục 30.4, hạn 30/11/2026).
- **Có nên tận dụng đặt xe làm chuyến giao?** Có, theo cách **nối chứ không gộp**: phiếu xuất hoặc phiếu chuyển kho gắn vào phiếu đặt xe giao hàng, từng điểm dừng trỏ tới một phiếu giao. Đặt xe không bao giờ tự trừ kho.
- Mọi việc ở đây đứng **sau kho lõi** (doc 01 nấc 2: sổ kho chỉ thêm, có ngày ghi sổ, chặn tồn âm, giá bình quân di động, phiếu nhập do thủ kho lập). Làm phiếu xuất trên sổ kho hiện tại là đổ thêm sai lệch vào công thức bình quân toàn lịch sử (doc 01 điểm c).

## 2. Phạm vi và cách chấm

**Trong phạm vi:** đề nghị lĩnh vật tư, phiếu xuất dùng nội bộ, xuất hủy, chuyển kho, xuất cho sản xuất ở **mức chứng từ kho** (không bàn BOM, lệnh sản xuất, giá thành), giữ hàng, soạn hàng, đóng gói, phiếu giao hàng bán, trả hàng bán, chuyến giao, gửi qua hãng vận chuyển, nối sang hóa đơn bán ở mức khái niệm, báo cáo của mảng.

**Ngoài phạm vi:** báo giá bán, bảng giá, chiết khấu, công nợ phải thu, hóa đơn điện tử chi tiết (thuộc mảng Bán hàng và Kế toán).

**Cách chấm:** giống doc 11. **Có** = 1 điểm (làm được trên màn, có chứng từ hoặc dữ liệu riêng), **Một phần** = 0,5 (làm được nhưng thiếu một mảnh quan trọng), **Chưa** = 0 (không có, hoặc chỉ làm được bằng cách đi vòng như điều chỉnh tay). Không gán trọng số.

---

## 3. ERPNext v16: chiều ra của kho

### 3.0. Bản đồ chứng từ

```
Bán hàng:
  Sales Order (đơn bán, có thể giữ hàng: Stock Reservation Entry)
    -> Pick List (soạn hàng theo kho, lô)          [không trừ kho]
    -> Delivery Note (phiếu giao, TRỪ KHO)          [giao nhiều lần, trả hàng = DN return]
         -> Packing Slip (phiếu đóng gói)          [không trừ kho]
         -> Shipment (gửi hãng vận chuyển)          [không trừ kho]
         -> Delivery Trip (chuyến xe nhiều điểm)    [không trừ kho]
    -> Sales Invoice (hóa đơn bán)                  [ghi doanh thu, công nợ phải thu]

Nội bộ và sản xuất:
  Material Request loại Material Issue / Material Transfer (đề nghị lĩnh, đề nghị chuyển)
    -> (tùy chọn) Pick List
    -> Stock Entry (phiếu kho, TRỪ hoặc CHUYỂN KHO)
         Material Issue: xuất dùng, xuất hủy, hao hụt
         Material Transfer: chuyển kho một bước hoặc hai bước (qua kho đang chuyển)
         Material Transfer for Manufacture / Material Consumption for Manufacture / Manufacture: theo lệnh sản xuất
```

Luật chung cho mọi chứng từ có dấu *submittable*: **Nháp** (sửa tự do, không ảnh hưởng tồn) → **Gửi** (`docstatus = 1`, ghi sổ kho và sổ cái, khóa sửa) → muốn sửa phải **Hủy** (đảo bút toán) rồi **Sửa đổi** (*Amend*, sinh bản mới hậu tố `-1`). Sổ kho (*Stock Ledger Entry*) không bao giờ bị sửa trực tiếp.

### 3.1. Sales Order — đơn bán ở mức khái niệm

- **Là gì:** cam kết bán cho khách: mặt hàng, số lượng, giá, ngày giao hẹn, kho xuất. Gửi đơn **không** trừ kho, **không** ghi sổ cái.
- **Dùng khi nào:** mọi bán hàng có giao sau, giao nhiều lần, hoặc cần giữ hàng.
- **Trường và luật chính:**
  - Dòng hàng: `delivery_date` riêng từng dòng (giao theo lịch), `warehouse` (kho xuất), `delivered_qty`, `picked_qty`, `reserve_stock`, `stock_reserved_qty`, `delivered_by_supplier` (nhà cung cấp giao thẳng).
  - Đầu đơn: `per_delivered`, `per_billed`, `per_picked`, `delivery_status` (*Not Delivered, Partly Delivered, Fully Delivered, Closed, Not Applicable*), `billing_status`, `status` (*To Deliver and Bill, To Bill, To Deliver, Completed, Closed, On Hold*...), `skip_delivery_note` (dịch vụ, không giao).
  - **Close** đơn để chốt phần còn lại không giao nữa; **On Hold** để tạm dừng.

### 3.2. Delivery Note — phiếu giao hàng

- **Là gì:** chứng từ ghi hàng rời kho công ty đi tới khách. Đây là chứng từ **trừ kho** của luồng bán. Khi bật kế toán kho liên tục, gửi phiếu sinh bút toán *Nợ giá vốn / Có hàng tồn kho* theo giá xuất tính tại thời điểm ghi sổ.
- **Dùng khi nào:** giao hàng cần chứng từ đi kèm xe, cần giao nhiều lần cho một đơn, hoặc cần tách thời điểm giao khỏi thời điểm xuất hóa đơn. Selling Settings cho phép bỏ phiếu giao (`dn_required = No`: lập hóa đơn thẳng từ đơn, hóa đơn có `update_stock` để trừ kho luôn — hợp với bán lẻ giao ngay).
- **Tạo từ đâu:** từ Sales Order (lấy phần còn lại), từ Pick List đã gửi (tự gộp mỗi khách một phiếu), hoặc lập đứng riêng nếu `so_required = No`.
- **Trường chính:**
  - Đầu phiếu: `customer`, `company`, `posting_date`, `posting_time`, `set_warehouse`, `shipping_address_name`, `dispatch_address_name`, `contact_person`, `po_no` (số đơn của khách), `project`, `cost_center`, `incoterm`.
  - Vận chuyển: `transporter` (nhà vận chuyển là một Supplier), `driver`, `driver_name`, `vehicle_no`, `lr_no` và `lr_date` (số và ngày vận đơn), `delivery_trip`.
  - Dòng hàng: `item_code`, `qty`, `uom`, `conversion_factor`, `stock_qty`, `warehouse`, `target_warehouse` (khách nội bộ), `against_sales_order` + `so_detail`, `against_pick_list` + `pick_list_item`, `batch_no` / `serial_and_batch_bundle`, `expense_account`, `cost_center`, `returned_qty`, `billed_amt`, `packed_qty`, `incoming_rate`, `quality_inspection`.
  - Theo dõi: `per_billed`, `per_returned`, `per_installed`, `status` (*Draft, To Bill, Partially Billed, Completed, Return, Return Issued, Cancelled, Closed*).
  - Dãy số: `MAT-DN-.YYYY.-` cho giao, `MAT-DN-RET-.YYYY.-` cho trả.
- **Giao nhiều lần:** mỗi phiếu giao lấy *số đặt − số đã giao*; đơn bán cập nhật `delivered_qty` từng dòng và `per_delivered`. Giao vượt bị chặn trừ khi đặt dung sai `over_delivery_receipt_allowance` (%) ở Item hoặc Stock Settings. Không giao nữa thì **Close** đơn.
- **Trả hàng bán:** lập *Delivery Note Return* từ phiếu gốc: `is_return = 1`, `return_against` trỏ phiếu gốc, số lượng âm, hàng **cộng lại** kho theo giá xuất gốc (không theo giá hiện tại). `issue_credit_note` để sinh luôn giấy giảm trừ (Credit Note) nếu phiếu gốc đã có hóa đơn. Phiếu gốc cập nhật `returned_qty`, `per_returned`.
- **Luật:** không cho tồn âm (trừ khi bật `allow_negative_stock`); hàng quản lý lô bắt buộc chọn lô; lô gợi ý theo `pick_serial_and_batch_based_on` (*FIFO, LIFO, Expiry*).

### 3.3. Pick List — phiếu soạn hàng

- **Là gì:** lệnh cho người kho biết **lấy gì, ở kho nào, lô nào, bao nhiêu**. Bản thân phiếu **không trừ kho**.
- **Dùng khi nào:** kho có nhiều kho con hoặc nhiều lô, nhiều đơn soạn cùng lúc, hoặc cần tách người soạn khỏi người lập phiếu giao.
- **Trường và luật chính:**
  - `purpose`: *Delivery* (cho đơn bán), *Material Transfer* (cho đề nghị chuyển), *Material Transfer for Manufacture* (cho lệnh sản xuất, kèm `work_order`, `for_qty`).
  - Nguồn: Sales Order, Work Order, Material Request. `parent_warehouse` giới hạn vùng tìm hàng.
  - Bảng `locations`: `item_code`, `warehouse`, `batch_no`, `qty`, `picked_qty`, `stock_reserved_qty`, `sales_order`, `material_request`, `delivered_qty`, `transferred_qty`. Máy tự gợi ý kho theo **FIFO** (hoặc theo hạn dùng), `pick_manually` để tự chọn.
  - Quét mã vạch (`scan_mode`), dung sai soạn vượt `over_picking_allowance`.
  - Chỉ lập được cho đơn có `per_picked < 100`. Phải **gửi** Pick List rồi mới lập phiếu giao hoặc phiếu kho. Nút *Update Current Stock* làm mới gợi ý khi tồn đã đổi.
  - Trạng thái: *Draft, Open, Partly Delivered, Partially Transferred, Completed, Cancelled*; `delivery_status`, `per_delivered`.
  - Có thể **giữ hàng** ngay từ Pick List (nút *Stock Reservation → Reserve*).

### 3.4. Packing Slip — phiếu đóng gói

- **Là gì:** danh sách hàng trong từng kiện, dán kèm thùng. **Không trừ kho**.
- **Dùng khi nào:** một phiếu giao chia nhiều thùng, khách hoặc hãng vận chuyển cần biết thùng nào chứa gì, cân nặng bao nhiêu.
- **Trường và luật chính:** `delivery_note` (bắt buộc, phiếu giao phải đang ở **Nháp**), `from_case_no`, `to_case_no` (số thùng), dòng hàng lấy từ phiếu giao, `net_weight_pkg`, `gross_weight_pkg` và đơn vị cân. Một phiếu giao có nhiều phiếu đóng gói; tổng số đã đóng ghi vào `packed_qty` trên dòng giao.

### 3.5. Shipment — lô gửi hãng vận chuyển

- **Là gì:** hồ sơ một lô gửi đi qua đơn vị vận chuyển: lấy ở đâu, giao tới đâu, bao nhiêu kiện, giá trị hàng, mã vận đơn, tình trạng.
- **Dùng khi nào:** giao qua hãng chuyển phát hoặc nhà xe, cần theo dõi mã vận đơn và cước.
- **Trường chính:** `pickup_from_type` và `delivery_to_type` (*Company, Customer, Supplier*) kèm địa chỉ và người liên hệ hai đầu; `shipment_parcel` (kích thước, cân nặng, số kiện, mẫu kiện `parcel_template`); `value_of_goods`, `description_of_content`, `shipment_type` (*Goods, Documents*), `pickup_type` (*Pickup, Self delivery*), `pickup_date`, khung giờ `pickup_from` – `pickup_to`; `carrier`, `carrier_service`, `awb_number`, `shipment_amount`, `tracking_url`, `tracking_status` (*In Progress, Delivered, Returned, Lost*); bảng `shipment_delivery_note` nối nhiều phiếu giao.
- **Luật:** không trừ kho. Bản lõi chỉ ghi tay; đặt hãng và lấy mã vận đơn tự động cần ứng dụng tích hợp ngoài.

### 3.6. Delivery Trip — chuyến giao

- **Là gì:** một chuyến xe chở hàng cho nhiều khách, mỗi khách là một điểm dừng gắn phiếu giao. **Không trừ kho**.
- **Dùng khi nào:** công ty có xe và tài xế riêng, mỗi chuyến giao nhiều điểm, cần báo khách giờ đến và ghi điểm nào đã giao.
- **Trường chính:**
  - Đầu chuyến: `company`, `vehicle` (bắt buộc, danh mục Vehicle), `driver` (danh mục Driver, có thể nối `employee`), `departure_time` (bắt buộc), `total_distance` + `uom`, `status` (*Draft, Scheduled, In Transit, Completed, Cancelled*).
  - Bảng `delivery_stops` (bắt buộc): `customer`, `address` (bắt buộc), `contact`, `delivery_note`, `grand_total`, `visited` (đã ghé), `distance`, `estimated_arrival`, `lat`, `lng`, `details`, `locked` (giữ thứ tự khi tối ưu tuyến).
- **Luật và thao tác:** lập từ phiếu giao đã gửi (*Create → Delivery Trip*) hoặc gom nhiều phiếu; nút tối ưu tuyến và tính giờ đến dùng Google Maps (cần khóa API); *Notify Customers* gửi thư theo mẫu ở Delivery Settings (`dispatch_template`, đính kèm bản in `dispatch_attachment`, độ trễ `stop_delay`). Tài xế đánh dấu `visited` từng điểm.

### 3.7. Stock Entry — phiếu kho cho xuất dùng, chuyển kho, sản xuất

- **Là gì:** chứng từ kho đa năng cho mọi biến động **không phải mua bán**. Loại do `stock_entry_type` quyết định, mỗi loại trỏ về một `purpose`. Site học có 13 loại mặc định: *Material Issue, Material Receipt, Material Transfer, Material Transfer for Manufacture, Material Consumption for Manufacture, Manufacture, Repack, Disassemble, Send to Subcontractor, Receive from Customer, Return Raw Material to Customer, Subcontracting Delivery, Subcontracting Return* (bốn loại cuối là gia công cho khách, mới ở v16). Công ty tự thêm loại riêng, ví dụ *Xuất hủy*, *Xuất mẫu*, đều mang `purpose = Material Issue`.
- **Material Issue — xuất dùng nội bộ, hủy, hao hụt:**
  - Chỉ có kho đi (`from_warehouse` / `s_warehouse` trên dòng).
  - Mỗi dòng có `expense_account` (*Difference Account*: tài khoản chi phí nhận giá trị xuất, ví dụ 627, 641, 642, 632, 811) và `cost_center` (bộ phận chịu chi phí). Đây chính là **mục đích chi phí** mà doc 10 mục 9.3 bắt buộc.
  - Giá xuất lấy theo cách tính giá của mặt hàng (*Moving Average* hoặc *FIFO*), không gõ tay.
  - Dòng có thể trỏ `material_request` + `material_request_item` để cập nhật đề nghị.
- **Material Transfer — chuyển kho:** có cả `s_warehouse` và `t_warehouse`. Chuyển **hai bước** bằng `add_to_transit = 1`: phiếu thứ nhất đưa hàng vào kho đang chuyển, kho đến lập phiếu thứ hai (*End Transit*, `outgoing_stock_entry` trỏ phiếu đầu); `per_transferred` cho biết đã nhận bao nhiêu.
- **Cho sản xuất ở mức chứng từ kho:**
  - *Material Transfer for Manufacture*: từ lệnh sản xuất (`work_order`), chuyển vật tư từ kho nguyên liệu sang kho sản xuất dở dang. Có thể đi qua Pick List.
  - *Material Consumption for Manufacture*: ghi tiêu hao thực tế tách khỏi lúc báo hoàn thành.
  - *Manufacture*: tiêu vật tư và nhập thành phẩm trong một phiếu, theo `bom_no` × `fg_completed_qty` (kiểu *backflush*), có `process_loss_qty`.
  - Trả vật tư thừa: phiếu chuyển ngược hoặc `is_return`.
- **Luật:** chặn tồn âm theo `allow_negative_stock`; `posting_date` + `posting_time` quyết định thứ tự tính giá (ghi lùi ngày thì máy tính lại giá các phiếu sau); hàng có lô bắt buộc chọn lô; `is_opening` cho tồn đầu kỳ.

### 3.8. Material Request loại Material Issue và Material Transfer — đề nghị lĩnh vật tư

- **Là gì:** phiếu **đề nghị**, chưa động tới kho. Cùng một chứng từ Material Request, loại do `material_request_type` quyết định: *Purchase* (đề nghị mua), *Material Transfer* (đề nghị chuyển), *Material Issue* (đề nghị xuất dùng), *Manufacture*, *Subcontracting*, *Customer Provided*.
- **Dùng khi nào:**
  - *Material Issue*: phòng ban, xưởng xin lĩnh vật tư, văn phòng phẩm, phụ tùng để dùng.
  - *Material Transfer*: nhà máy xin kho tổng chuyển hàng sang; hoặc xưởng xin cấp vật tư từ kho về kho xưởng.
- **Trường chính:** `transaction_date`, `schedule_date` (cần lúc nào), `set_warehouse` (kho đích hoặc kho xuất), `set_from_warehouse` (kho nguồn khi chuyển), `items` (mặt hàng, số lượng, kho từng dòng), `work_order`, `job_card`, `customer`, `status` (*Draft, Pending, Partially Received, Issued, Transferred, Stopped, Cancelled*...), `per_ordered`, `transfer_status` (*Not Started, In Transit, Completed*).
- **Luật:** gửi đề nghị (duyệt bằng *Workflow* nếu cấu hình) → *Create → Issue Material* hoặc *Material Transfer* sinh Stock Entry, hoặc *Create → Pick List*. Mỗi lần xuất cập nhật phần đã xuất; vượt đề nghị bị chặn trừ dung sai `mr_qty_allowance`. Mức tồn tối thiểu (`auto_indent`) có thể tự sinh đề nghị chuyển, không chỉ đề nghị mua.
- **Site học:** 320 Material Request đều là loại *Purchase*; chưa ai thực hành loại *Material Issue* hay *Material Transfer*.

### 3.9. Stock Reservation — giữ hàng cho đơn

- **Là gì:** dành một phần tồn cho một chứng từ cụ thể, để chứng từ khác không lấy mất. **Không** sinh dòng sổ kho, không đổi tồn sổ sách; chỉ giảm **tồn khả dụng** với người khác.
- **Dùng khi nào:** hàng khan, nhiều đơn tranh nhau một lô; hoặc giữ vật tư cho lệnh sản xuất đã phát hành (doc 01 mục 5.3).
- **Bật ở Stock Settings:** `enable_stock_reservation` (mặc định tắt, site học đang tắt), `allow_partial_reservation`, `auto_reserve_stock` (tự giữ khi gửi đơn), `auto_reserve_stock_for_sales_order_on_purchase` (hàng mua về cho đơn nào thì tự giữ cho đơn đó), `auto_reserve_serial_and_batch`.
- **Chứng từ Stock Reservation Entry:** `voucher_type` (*Sales Order, Work Order, Production Plan, Subcontracting Order, Subcontracting Inward Order*), `voucher_no`, `voucher_detail_no`, `item_code`, `warehouse`, `reserved_qty`, `delivered_qty`, `consumed_qty`, `transferred_qty`, `reservation_based_on` (*Qty* hoặc *Serial and Batch*), `from_voucher_type` (giữ từ *Pick List, Purchase Receipt, Stock Entry*...), `status` (*Reserved, Partially Reserved, Partially Delivered, Delivered, Cancelled, Closed*).
- **Luật:** phiếu giao của chính đơn đó tiêu phần đã giữ trước; hủy giữ được bằng tay; báo cáo **Reserved Stock** liệt kê phần đang giữ theo mặt hàng, kho, chứng từ.

### 3.10. Sales Order → Delivery Note → Sales Invoice

| Bước | Kho | Sổ cái (khi bật kế toán kho liên tục) | Cờ điều khiển |
|---|---|---|---|
| Sales Order | Không đổi (có thể giữ hàng) | Không | `reserve_stock` |
| Delivery Note | Trừ kho | Nợ giá vốn / Có hàng tồn kho | `so_required` |
| Sales Invoice | Không đổi (trừ khi `update_stock`) | Nợ phải thu / Có doanh thu, thuế đầu ra | `dn_required` |

- Hóa đơn lập từ phiếu giao kéo đúng dòng đã giao; phiếu giao ghi `billed_amt` từng dòng, `per_billed`, chuyển *To Bill → Partially Billed → Completed*.
- Có thể đi ngược: lập hóa đơn trước rồi giao sau (hóa đơn không trừ kho), khi đó phiếu giao trỏ `against_sales_invoice`.
- `maintain_same_sales_rate` ép giá giữ nguyên suốt chuỗi.

### 3.11. Báo cáo của mảng

| Báo cáo | Vị trí mã | Dùng để |
|---|---|---|
| **Delivered Items To Be Billed** | `accounts/report/delivered_items_to_be_billed` | Liệt kê dòng phiếu giao đã gửi mà số tiền đã lập hóa đơn còn nhỏ hơn số tiền dòng: khách, phiếu, mặt hàng, số tiền chưa lập hóa đơn. Cuối tháng dùng để giục lập hóa đơn và để kế toán thấy doanh thu chưa ghi. Bản đối xứng của *Received Items To Be Billed* bên mua |
| **Delivery Note Trends** | `stock/report/delivery_note_trends` | Số lượng và giá trị phiếu giao theo kỳ (tháng, quý, năm), nhóm theo mặt hàng, nhóm hàng, khách, nhóm khách, vùng. Cùng khuôn với *Sales Order Trends*, *Purchase Receipt Trends* |
| **Reserved Stock** | `stock/report/reserved_stock` | Phần tồn đang giữ cho chứng từ nào |
| Sales Order Analysis | `selling/report` | Dòng đơn chưa giao, trễ hẹn, chưa lập hóa đơn |
| Stock Ledger | `stock/report/stock_ledger` | Lọc theo loại chứng từ để xem tổng xuất dùng, xuất bán, chuyển kho |

### 3.12. Cài đặt ảnh hưởng chiều ra

| Cài đặt | Ở đâu | Mặc định | Ý nghĩa |
|---|---|---|---|
| `so_required` | Selling Settings | No | Có bắt phiếu giao, hóa đơn phải đi từ đơn bán |
| `dn_required` | Selling Settings | No | Có bắt hóa đơn phải đi từ phiếu giao |
| `allow_negative_stock` | Stock Settings | Tắt | Cho tồn âm hay không |
| `over_delivery_receipt_allowance` | Item / Stock Settings | 0 % | Dung sai giao vượt |
| `over_picking_allowance` | Stock Settings | 0 % | Dung sai soạn vượt |
| `mr_qty_allowance` | Stock Settings | 0 % | Dung sai chuyển vượt so với đề nghị |
| `pick_serial_and_batch_based_on` | Stock Settings | FIFO | Gợi ý lô theo FIFO, LIFO hay hạn dùng |
| `enable_stock_reservation` và các cờ tự giữ | Stock Settings | Tắt | Bật giữ hàng |

### 3.13. Ghi nhận trên site học (chỉ đọc, 02/11/2026)

- Bản cài: ERPNext `16.53.0`, site `frontend`.
- Chiều ra chưa có dữ liệu: 0 Customer, 0 Sales Order, 0 Delivery Note, 0 Pick List, 0 Packing Slip, 0 Shipment, 0 Delivery Trip, 0 Vehicle, 0 Driver, 0 Stock Reservation Entry. Giữ hàng đang tắt.
- Có 2 Stock Entry (1 *Material Issue*, 1 *Material Transfer*) từ bài tập kho trước.
- Muốn thực hành chiều ra cần **ghi dữ liệu học** lên site (khách, đơn bán, giao hai lần, trả hàng, chuyến giao, đề nghị lĩnh). Bản này không ghi; nếu cần thì xin gật riêng và viết thành bài tập như `doc/erp/nghien-cuu/erpnext/01`.

---

## 4. ERP DEGO hiện có gì

| Thành phần | Mức | Ở đâu | Ghi chú |
|---|---|---|---|
| Phân hệ Bán hàng v2 | **Chưa** (vỏ) | `frontend-v2/src/modules/sales/routes.tsx`, `pages/sales-dashboard-page.tsx` | `enabled: false`, chỉ một trang tổng quan rỗng. Máy chủ không có module bán hàng |
| Phân hệ Khách hàng v2 | **Chưa** (vỏ) | `frontend-v2/src/modules/customer/routes.tsx` | `nav: []`, `routes: []`. Không có bảng `tab_customer` |
| Tồn kho và sổ phát sinh | **Một phần** | `backend/app/modules/inventory/model.py`, `service.py`, `controller.py`; v2 `inventory/pages/inventory-list-page.tsx` | `tab_inventory` theo công ty + kho + mã hàng; `tab_inventory_move.ref_type` chỉ `gr` hoặc `adjust`. Giá bình quân tính lại trên **toàn bộ lịch sử** mỗi lần (`_recompute`), không có ngày ghi sổ, không có loại xuất |
| Điều chỉnh tay | **Có** (dùng thay xuất) | `POST /api/inventory/adjust`, `inventory-adjust-dialog.tsx` | Số âm hoặc dương, ghi chú tự do, đơn giá mặc định là bình quân hiện tại. **Không chặn tồn âm**, không duyệt, không mục đích chi phí. Quyền `inventory.write`, chốt pháp nhân ở `_writable_company` |
| Nhật ký nhập xuất | **Một phần** | `GET /api/inventory/moves` | Lọc theo kho, mã hàng, công ty; không lọc theo loại phát sinh vì chỉ có hai loại |
| Danh mục kho | **Có** | `catalog/model.py` `Warehouse`; v2 `inventory/config/warehouse-crud.tsx` | Mã, tên, địa chỉ, cờ dùng. Không có loại kho (vật tư, thành phẩm, đang chuyển, cách ly), không có vị trí, không gắn pháp nhân |
| Phiếu nhập kho | **Một phần** | `goods_receipt/model.py` | Sinh ngầm từ dòng giao của ĐMH; là gương của chiều vào, chưa có chiều ra tương ứng |
| Đặt xe giao hàng | **Có** (nền chuyến giao) | `vehicle_booking/model.py` (`TYPE_DELIVERY`), `schema.py` `StopItem`; v2 `vehicle-booking/pages/*` gồm `my-trips-page.tsx`, `vehicle-booking-print-page.tsx`, `timeline-page.tsx` | Hàng (`goods_name`, `goods_size`), người gửi, người nhận, điểm dừng JSON (`location`, `contact_name`, `contact_phone`, `notes`), điều phối xe + tài xế, `driver_status` 6 trạng thái, giờ chạy thực tế, `distance_km`, `cost`, tự lái, xe và tài xế thuê ngoài (doanh nghiệp hoặc cá nhân). Hàng là **chữ tự do**, không nối mặt hàng, không nối chứng từ kho. Điểm dừng không có cờ *đã giao* |
| Duyệt đặt xe | **Có** | `vehicle_booking/approval_bridge.py` | Đi qua bộ máy duyệt chung sau cờ `ApprovalSwitch` |
| Báo cáo đặt xe | **Có** | `vehicle_booking/report_controller.py`, `report_service.py`, `dashboard_service.py` | Tổng hợp theo kỳ, nhóm, xuất Excel; trang chủ đếm riêng phiếu giao hàng |
| Đồng bộ app đặt xe cũ | **Có** | `legacy_datxe/` (`builder.py`, `outbound.py`, cờ `erp_action_at`) | Ràng buộc khi thêm cột vào phiếu đặt xe: chiều nhận từ app cũ không được chép đè |
| Bộ máy duyệt chung | **Có** | `backend/app/modules/approval/` | Dùng lại được cho đề nghị lĩnh vật tư |
| Phòng ban | **Có** | `department/` | Dùng làm bộ phận chịu chi phí; chưa có danh mục mục đích chi phí hay tài khoản |
| Loại tài liệu *Biên bản giao nhận / Phiếu giao hàng* | **Một phần** | `core/document_types.py` (`delivery_note`), dùng ở `attachment/controller.py` | Chỉ là nhãn loại tệp đính kèm, không phải chứng từ |
| Yêu cầu mua hàng | Ngoài phạm vi | `purchase_request/model.py` | Chỉ là đề nghị **mua**; cột `warehouse` là kho nhận. Không có lựa chọn *cấp từ kho* |
| Công nợ phải thu, hóa đơn bán | **Chưa** | — | `payable/` chỉ có phải trả |
| Điểm cà phê / POS365 | Ngoài phạm vi | `coffee_point/` | Ví điểm nội bộ, nối POS365 của quán; không đi qua kho ERP |

Kế hoạch đã ghi nhận chỗ hở này ở ba nơi: `TM-GN-4` (phiếu xuất, chuyển kho — *chỉ ghi, chưa làm*), `SX2-1` (thêm loại phiếu xuất sản xuất, trả vật tư, xuất hủy), `KH3-1` / `BH4` (xuất kho bán, giao hàng — vòng 4, chờ câu C8).

---

## 5. Bảng fit-gap và tỷ lệ phủ

### A. Nền dùng chung

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| A1 | Danh mục khách hàng, địa chỉ giao, người liên hệ | Customer, Address, Contact | **Chưa** 0 | Module `customer` v2 là vỏ; không có bảng |
| A2 | Kho xuất và mặt hàng | Warehouse, Item | **Có** 1 | `tab_warehouse`, `tab_product`; tồn theo công ty + kho + mã |
| A3 | Vị trí, lô, hạn dùng để soạn FEFO | Batch, Serial, `pick_serial_and_batch_based_on` | **Chưa** 0 | Không có cột lô, hạn dùng (doc 01 điểm k) |
| A4 | Mục đích chi phí, bộ phận chịu chi phí khi xuất dùng | `expense_account`, `cost_center` trên dòng | **Một phần** 0,5 | Có phòng ban; không có danh mục mục đích chi phí |
| A5 | Duyệt đề nghị theo luồng | Workflow | **Có** 1 | `approval/` bộ máy duyệt chung |

### B. Xuất nội bộ và xuất cho sản xuất (mức chứng từ kho)

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| B1 | Đề nghị lĩnh vật tư (xuất dùng) | Material Request *Material Issue* | **Chưa** 0 | YCMH chỉ là đề nghị mua |
| B2 | Đề nghị chuyển kho | Material Request *Material Transfer* | **Chưa** 0 | — |
| B3 | Phiếu xuất dùng nội bộ, xuất hủy, hao hụt | Stock Entry *Material Issue* | **Chưa** 0 | Chỉ đi vòng bằng điều chỉnh âm (`ref_type = adjust`) |
| B4 | Xuất vật tư cho lệnh sản xuất, trả vật tư thừa | *Material Transfer for Manufacture*, *Consumption*, *Manufacture* | **Chưa** 0 | Chưa có lệnh sản xuất (SX2-1) |
| B5 | Chuyển kho một bước, hai bước | Stock Entry *Material Transfer*, `add_to_transit` | **Chưa** 0 | Phải điều chỉnh âm một bên, dương một bên |
| B6 | Chặn tồn âm | `allow_negative_stock = 0` | **Chưa** 0 | `service.adjust` không kiểm số tồn |
| B7 | Giá xuất tự tính theo cách tính giá | Moving Average / FIFO | **Một phần** 0,5 | Điều chỉnh lấy bình quân hiện tại, nhưng bình quân tính lại trên toàn lịch sử nên giá xuất cũ trôi (doc 01 điểm c) |
| B8 | Sổ chỉ thêm, ngày ghi sổ, hủy bằng đảo | Submit / Cancel / Amend, `posting_date` | **Một phần** 0,5 | Dòng `adjust` chỉ thêm; dòng `gr` sửa xóa được; không có ngày ghi sổ riêng, không có đảo |

### C. Giao hàng bán

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| C1 | Đơn bán làm nguồn giao | Sales Order | **Chưa** 0 | — |
| C2 | Phiếu giao hàng trừ kho | Delivery Note | **Chưa** 0 | — |
| C3 | Giao nhiều lần, % đã giao, đóng phần còn lại | `delivered_qty`, `per_delivered`, Close | **Chưa** 0 | Bên mua đã có khuôn này (`tab_po_delivery`), bên bán chưa |
| C4 | Trả hàng bán | Delivery Note Return | **Chưa** 0 | — |
| C5 | Soạn hàng theo kho, lô | Pick List | **Chưa** 0 | — |
| C6 | Đóng gói, số thùng, cân nặng | Packing Slip | **Chưa** 0 | — |
| C7 | Giữ hàng cho đơn | Stock Reservation Entry | **Chưa** 0 | — |
| C8 | Gửi qua hãng vận chuyển: điểm lấy, điểm giao, hàng, cước | Shipment | **Một phần** 0,5 | Phiếu đặt xe giao hàng có người gửi, người nhận, mô tả hàng, xe và tài xế thuê ngoài, chi phí; thiếu kiện, mã vận đơn, tình trạng vận chuyển |
| C9 | Chuyến giao: xe, tài xế, nhiều điểm dừng, km | Delivery Trip | **Một phần** 0,5 | Đặt xe có đủ xe, tài xế, điểm dừng, km, chi phí, trạng thái tài xế; điểm dừng **không** trỏ phiếu giao |
| C10 | Xác nhận đã giao từng điểm, chứng từ ký nhận | `visited`, bản in phiếu giao | **Một phần** 0,5 | Tài xế hoàn tất cả chuyến trên *Chuyến của tôi*; đính kèm được *Biên bản giao nhận*; không xác nhận từng điểm |
| C11 | In phiếu xuất kho, phiếu giao theo mẫu | Print Format | **Chưa** 0 | Chỉ có bản in phiếu đặt xe |

### D. Nối hóa đơn, kế toán, báo cáo

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| D1 | Hóa đơn bán lập từ phiếu giao | Sales Invoice, `billed_amt` | **Chưa** 0 | — |
| D2 | Hàng đã giao chưa lập hóa đơn | Delivered Items To Be Billed | **Chưa** 0 | — |
| D3 | Xu hướng giao hàng theo kỳ | Delivery Note Trends | **Chưa** 0 | — |
| D4 | Báo cáo hàng đang giữ | Reserved Stock | **Chưa** 0 | — |
| D5 | Sổ xuất theo loại, theo bộ phận | Stock Ledger lọc loại chứng từ | **Một phần** 0,5 | `/api/inventory/moves` xem được dòng điều chỉnh âm, không có loại xuất để lọc |
| D6 | Báo cáo chuyến xe theo tài xế, km, chi phí | Không có báo cáo riêng | **Có** 1 | Báo cáo Đặt xe (`report_controller.py`), trang chủ đặt xe. Chỗ DEGO đi xa hơn ERPNext |
| D7 | Giá trị xuất đẩy sang kế toán theo tài khoản đối ứng | Bút toán tự động | **Chưa** 0 | Chưa có kế toán, chưa nối MISA (doc 01 nấc 3.7) |

### Tỷ lệ phủ

| Nhóm | Số chức năng | Điểm | Tỷ lệ |
|---|---:|---:|---:|
| A. Nền dùng chung | 5 | 2,5 | 50 % |
| B. Xuất nội bộ và cho sản xuất | 8 | 1,0 | 13 % |
| C. Giao hàng bán | 11 | 1,5 | 14 % |
| D. Hóa đơn, kế toán, báo cáo | 7 | 1,5 | 21 % |
| **Cả mảng** | **31** | **6,5** | **21 %** |
| Riêng nội bộ và sản xuất (A + B) | 13 | 3,5 | 27 % |

Cách đọc: điểm có được gần như toàn bộ nằm ở **nền** (kho, mặt hàng, bộ máy duyệt) và **đặt xe**. Phần chứng từ kho chiều ra gần như bằng 0. Con số khớp doc 11 dòng F4, F5 (xuất kho, chuyển kho đều *Chưa*).

---

## 6. Đề xuất cho DEGO

### 6.1. Thứ tự: nội bộ và sản xuất trước, bán sau

| Thứ tự | Việc | Vì sao |
|---|---|---|
| 1 | **Phiếu xuất kho chung** cho xuất dùng nội bộ, xuất hủy, chuyển kho | Đây là nhu cầu có thật ngay hôm nay (đang đi vòng bằng điều chỉnh âm). Không phụ thuộc câu hỏi bán hàng. Là điều kiện cần của Sản xuất bản số lượng (doc 01 mục 8.2 việc 2.5, 2.6) |
| 2 | **Đề nghị lĩnh vật tư** (kiểu Material Request *Issue* / *Transfer*) đi qua bộ máy duyệt chung | Tách người xin, người duyệt, người phát (doc 10 mục 4 và 7.2). Dùng lại `approval/`, rẻ |
| 3 | **Xuất cho sản xuất** theo lệnh, trả vật tư thừa, giữ chỗ cho lệnh | Chỉ làm khi có lệnh sản xuất (SX2-1) và chốt câu S3 = B4 (phiếu xuất hay trừ tự động) |
| 4 | **Giao hàng bán** (phiếu giao, giao nhiều lần, trả hàng bán) nối với đặt xe | Chỉ khi ban lãnh đạo chốt công ty bán qua ERP. Nếu đơn bán nằm ở công ty N2 hoặc sàn thương mại thì đơn đến từ đồng bộ (Đ2), ERP chỉ cần phiếu giao trỏ đơn ngoài |
| 5 | Soạn hàng, đóng gói, giữ hàng, gửi hãng, hóa đơn bán, báo cáo hàng chưa lập hóa đơn | Khi có khối lượng đơn đủ lớn và đã có phân hệ Kế toán hoặc đầu nối |

Một **chứng từ kho chung** kiểu Stock Entry (một bảng phiếu, một bảng dòng, trường loại phiếu `SMALLINT` + `IntEnum` theo luật trạng thái) là lựa chọn rẻ nhất: xuất dùng, xuất hủy, chuyển kho, xuất sản xuất, nhập trả vật tư đều là **loại** của cùng một phiếu. Phiếu giao bán nên là chứng từ **riêng** như Delivery Note, vì nó mang khách, địa chỉ, đơn bán, giá bán và sau này hóa đơn — trộn vào phiếu kho chung sẽ làm phiếu kho phình.

### 6.2. Tận dụng đặt xe làm chuyến giao

**Nên tận dụng**, theo hướng nối:

- Phiếu đặt xe giao hàng (`TYPE_DELIVERY`) đóng vai **Delivery Trip**: xe, tài xế, giờ đi, điểm dừng, km, chi phí đã có sẵn và đang chạy trên prod.
- Thêm sợi nối hai chiều: phiếu xuất / phiếu chuyển / phiếu giao có ô `vehicle_booking_id`; mỗi điểm dừng có thể trỏ `delivery_ref` (loại + id chứng từ kho). Hàng trên phiếu đặt xe lấy từ chứng từ kho thay vì gõ chữ tự do (giữ ô chữ cho phiếu không có chứng từ).
- Thêm xác nhận **từng điểm** trên *Chuyến của tôi*: đã giao, người nhận, ảnh biên bản ký (đính kèm loại `delivery_note` đã có).
- **Không** để đặt xe trừ kho. Kho trừ lúc thủ kho xác nhận phiếu xuất. Xác nhận giao ở điểm dừng chỉ đổi trạng thái giao, hoặc chuyển *hàng gửi đi* sang *đã giao* nếu công ty dùng tài khoản 157 (doc 10 mục 9.2).
- Ca dùng sớm nhất **không phải bán hàng** mà là **chuyển kho hai bước giữa các nhà máy**: xe chạy vài ngày, kho đi xuất, kho đến xác nhận số thực nhận, lệch số lộ ra (doc 10 mục 10, trường hợp C1). Đây là chỗ đặt xe giao hàng tạo giá trị ngay khi có phiếu chuyển.
- Ràng buộc kỹ thuật: thêm cột vào `tab_vehicle_booking` phải qua `legacy_datxe` (chiều nhận không chép đè, cờ `erp_action_at`); điểm dừng là JSON nên thêm khóa không cần migration, nhưng muốn lọc và đếm theo chứng từ thì cần bảng nối riêng.

### 6.3. Quan hệ với phần mềm bán hàng, kế toán đang có

- **MISA (kế toán):** câu gốc vẫn là K1 doc 01: *sổ kho chính thức nằm ở ERP hay MISA*. Nếu MISA giữ sổ, phiếu xuất ERP là **chứng từ nghiệp vụ** (ai xin, ai duyệt, ai phát, số thực), đẩy sang MISA bằng tệp hoặc đầu nối, và **giá xuất phải tính cùng cách với MISA** (K3). Nếu ERP giữ sổ thì ERP phải tự tính giá xuất đúng chuẩn, MISA chỉ nhận bút toán tổng. Không nên để hai bên cùng tính giá xuất độc lập.
- **Hóa đơn bán, hóa đơn điện tử:** bắt buộc qua nhà cung cấp được cơ quan thuế chấp nhận; công ty đang xuất hóa đơn ở đâu thì giữ nguyên ở đó trong bản đầu. ERP chỉ cần báo cáo *hàng đã giao chưa lập hóa đơn* để đối chiếu.
- **POS365:** đang dùng cho quán cà phê và ví điểm; bán lẻ quán không đi qua kho ERP. Không kéo POS vào phiếu giao. Nếu sau này quán cần trừ nguyên liệu thì làm một phiếu xuất tổng hằng ngày từ báo cáo POS, không nối từng đơn.
- **Công ty N2 và sàn thương mại:** kế hoạch đã có Đ2 *kéo đơn hàng N2 về hệ chính*. Nếu doanh thu chủ yếu qua đó, đơn bán ERP có thể chỉ là **bản sao đơn ngoài** để làm nguồn cho phiếu giao, không cần màn lập đơn bán đầy đủ.

---

## 7. Kế hoạch theo nấc

Đơn vị: người-ngày (pd), ước lượng thô để xếp lịch, chưa phải cam kết. Mọi nấc từ XG1 trở đi đứng **sau kho lõi**.

**Kho lõi (điều kiện trước, không thuộc mảng này):** doc 01 nấc 2 việc 2.1 phiếu nhập do thủ kho lập, việc 2.3–2.4 sổ kho chỉ thêm có ngày ghi sổ, giá bình quân di động, chặn tồn âm; tương ứng `TM-GN-3` và phần sổ kho của `TM-GN-4`.

| Nấc | Mã | Việc | Độ lớn | Phụ thuộc | Điều kiện xong |
|---|---|---|---|---|---|
| 0 | XG0 | Chốt câu hỏi mục 8 (X1–X6 trước), chọn thủ kho từng kho, chọn danh sách mục đích chi phí với kế toán | 2 pd khảo sát | — | Có câu trả lời bằng văn bản cho X1–X6 |
| 1 | XG1 | **Phiếu kho chung**: loại *xuất dùng nội bộ*, *xuất hủy*, *chuyển kho một bước*; dòng có mục đích chi phí + bộ phận; Nháp → Đã ghi sổ → Đã đảo; chặn tồn âm; giá xuất tự lấy từ sổ; in phiếu xuất kho theo mẫu kế toán dùng; entity quyền riêng | 10–12 pd | Kho lõi, XG0 | Tồn giảm được bằng chứng từ; điều chỉnh tay chỉ còn cho kiểm kê |
| 1 | XG2 | **Đề nghị lĩnh vật tư** (xuất dùng, chuyển kho) qua `approval/`; thủ kho lập phiếu từ đề nghị; theo dõi đã phát bao nhiêu, chặn phát vượt | 6–8 pd | XG1, bộ máy duyệt chung | Phòng xin, trưởng phòng duyệt, thủ kho phát; đề nghị hiện phần còn lại |
| 2 | XG3 | **Chuyển kho hai bước** qua kho đang chuyển, kho đến xác nhận số thực nhận, xử lý thiếu | 5 pd | XG1, loại kho *đang chuyển* trong danh mục kho | Lệch số giữa hai đầu hiện trên màn |
| 2 | XG4 | **Nối đặt xe**: phiếu chuyển / phiếu xuất gắn phiếu đặt xe giao hàng, điểm dừng trỏ chứng từ, tài xế xác nhận từng điểm kèm ảnh biên bản | 4–6 pd | XG3 (hoặc XG6), soát `legacy_datxe` | Một chuyến nhiều điểm, mỗi điểm biết đã giao chứng từ nào |
| 3 | XG5 | **Xuất cho sản xuất** theo lệnh (gợi ý theo định mức, xuất vượt có lý do và duyệt), nhập trả vật tư thừa, giữ chỗ vật tư cho lệnh | 8–10 pd | SX2-1 (BOM, lệnh), câu S3 = B4, XG1 | Báo cáo tiêu hao thực tế so với định mức theo lệnh |
| 4 | XG6 | **Giao hàng bán bản 1**: khách hàng tối thiểu, đơn bán (lập tay hoặc nhận từ đồng bộ N2), phiếu giao trừ kho, giao nhiều lần, đóng phần còn lại, trả hàng bán | 25–30 pd (tương đương BH1 + BH3 + BH4 ở `ke-hoach/02` mục 30.4) | X1 = có bán qua ERP, XG1, câu C8 | Một đơn giao hai lần, trả một phần, tồn và đơn khớp |
| 5 | XG7 | Giữ hàng cho đơn, phiếu soạn hàng theo kho, đóng gói | 8 pd | XG6; lô và hạn dùng nếu câu C5 = có | Hai đơn tranh một lô không lấy mất của nhau |
| 5 | XG8 | Báo cáo *hàng đã giao chưa lập hóa đơn*, xu hướng giao hàng theo kỳ, đầu nối phiếu xuất và phiếu giao sang MISA | 6–8 pd (chưa gồm hóa đơn điện tử) | XG6, phân hệ Kế toán hoặc câu C7 | Kế toán nhận được danh sách cuối tháng và số khớp |
| 5 | XG9 | Gửi hãng vận chuyển: kiện, mã vận đơn, tình trạng, cước thành công nợ cho hãng | 4 pd | XG6, câu X9 | Theo dõi được mã vận đơn từ phiếu giao |

Ghi chú xếp lịch:

- **XG1 + XG2** (16–20 pd) là phần đáng làm sớm nhất và nên đi chung đợt với `TM-GN-4`.
- **XG3 + XG4** cho ngay giá trị nếu các nhà máy chuyển hàng qua lại bằng xe công ty.
- **XG5** đi cùng đợt Sản xuất, không làm trước.
- **XG6 trở đi** chỉ mở khi có câu X1. Nếu X1 = không bán qua ERP thì dừng ở XG4, mảng này đạt khoảng 45–50 %.

Ước tỷ lệ phủ sau từng mốc (chấm lại cùng 31 chức năng): sau XG1–XG2 khoảng **37 %**; sau XG3–XG5 khoảng **48 %**; sau XG6 khoảng **68 %**; sau XG7–XG9 khoảng **85 %**.

---

## 8. Câu hỏi cần chốt

| # | Câu hỏi | Ai trả lời | Ảnh hưởng |
|---|---|---|---|
| X1 | Công ty có bán hàng qua ERP không? Đơn bán hiện chạy ở đâu (tự bán trực tiếp, công ty N2, sàn thương mại, phần mềm khác)? Trùng câu 8 `ke-hoach/02`, hạn 30/11/2026 | Ban lãnh đạo | Có làm XG6 trở đi hay không |
| X2 | Ai lập phiếu xuất ở từng kho, từng nhà máy? Thủ kho có tách khỏi người mua, người dùng không? (trùng Đ3 doc 01) | Ban lãnh đạo, trưởng kho | Quyền và luồng của XG1, XG2 |
| X3 | Xuất dùng nội bộ có cần trưởng phòng duyệt không, có hạn mức theo giá trị không? Xuất hủy duyệt theo hạn mức nào? | Ban lãnh đạo, kế toán | Luồng duyệt XG2, XG1 |
| X4 | Sổ kho chính thức ở ERP hay MISA? (K1 doc 01) | Kế toán, ban lãnh đạo | Ai tính giá xuất, ERP đẩy gì sang MISA |
| X5 | MISA đang tính giá xuất kho bằng cách nào ở từng pháp nhân? (K3 doc 01) | Kế toán | Cách tính giá trong kho lõi và XG1 |
| X6 | Danh sách mục đích chi phí khi xuất dùng: theo phòng ban hay theo tài khoản 627, 641, 642, 242? | Kế toán | Trường bắt buộc trên dòng XG1 |
| X7 | Cấp vật tư sản xuất bằng phiếu xuất theo lệnh hay trừ tự động sau khi báo hoàn thành? (S3 = B4) | Sản xuất | Thiết kế XG5 |
| X8 | Có quản lý lô, hạn dùng không? (C5) | Sản xuất, kho | XG7 soạn hàng FEFO |
| X9 | Có giao qua hãng vận chuyển, nhà xe không, hay chỉ xe công ty và xe thuê? | Kinh doanh, hành chính | Có làm XG9 không |
| X10 | Chuyến giao hàng có phải duyệt như đặt xe công tác không? Ai điều phối chuyến giao? | Hành chính | Dùng lại luồng duyệt đặt xe hay bỏ duyệt cho chuyến có chứng từ kho |
| X11 | Có dùng *hàng gửi đi bán* (tài khoản 157) khi khách nhận sau không? | Kế toán | Thêm trạng thái giữa xuất kho và khách xác nhận |
| X12 | Hóa đơn bán, hóa đơn điện tử đang xuất ở phần mềm nào? | Kế toán | Ranh giới XG8 |

Theo luật hỏi việc: câu cách làm (thiết kế phiếu kho chung, cách nối đặt xe) hỏi Agent 1 trước; X1, X2, X3 cần ban lãnh đạo; X4–X6, X11, X12 cần kế toán.

---

## 9. Nguồn

- ERPNext v16.53.0 trên site học: định nghĩa doctype đọc trực tiếp từ `apps/erpnext/erpnext/stock/doctype/{delivery_note, delivery_note_item, pick_list, pick_list_item, packing_slip, shipment, delivery_trip, delivery_stop, stock_entry, stock_entry_detail, material_request, stock_reservation_entry, stock_settings, delivery_settings}`, `selling/doctype/{sales_order, sales_order_item, selling_settings}`, danh sách báo cáo ở `accounts/report`, `stock/report`, `selling/report`. Số bản ghi đọc bằng `frappe.db.count` ngày 02/11/2026.
- Tài liệu chính thức: https://docs.frappe.io/erpnext/delivery-note · https://docs.frappe.io/erpnext/pick-list · https://docs.frappe.io/erpnext/packing-slip · https://docs.frappe.io/erpnext/delivery-trip · https://docs.frappe.io/erpnext/stock-entry · https://docs.frappe.io/erpnext/stock-reservation · https://docs.frappe.io/erpnext/sales-order · https://docs.frappe.io/erpnext/stock-transactions
- Mã nguồn: https://github.com/frappe/erpnext/tree/version-16
- ERP DEGO: các tệp nêu ở mục 4; kế hoạch `doc/plans/00-ke-hoach-theo-module.md` (TM-GN-4, SX2-1, KH3-1, DX); `ke-hoach/02-danh-sach-cong-viec.md` mục 21 (Đ2) và 30.4; `ke-hoach/erp/02-dai-han.md` mục 3.5.
