# ĐỘ PHỦ NGHIỆP VỤ THU MUA VÀ KHO CỦA ERP DEGO SO VỚI CHUẨN (MỐC ERPNEXT V16)

| | |
|---|---|
| Bản | 1.0 — 30/10/2026 |
| Mục đích | Trả lời câu hỏi "luồng thu mua, kho hiện tại nằm được bao nhiêu phần trăm so với chuẩn" bằng một bảng fit-gap có chấm điểm |
| Mốc so sánh | ERPNext v16 (site học `erpnext.degoholding.vn`, bài tập ở `ERPNext/erpnext-bai-tap-thu-mua-nhap-kho.md`) |
| Mã soát | nhánh `erp-v2` ngày 30/10/2026 (`backend/app/modules`, `frontend-v2/src/modules`) |
| Đọc kèm | [01 Luồng chuẩn mua hàng, kho, sản xuất](01-luong-chuan-mua-hang-kho-san-xuat.md) (mục 7 hiện trạng, mục 8 lộ trình ba nấc) · [09 Nghiệp vụ mua hàng](09-nghiep-vu-mua-hang.md) · [10 Nghiệp vụ kho](10-nghiep-vu-kho.md) |

## Mục lục

1. [Kết luận trong một trang](#1-kết-luận-trong-một-trang)
2. [Cách chấm](#2-cách-chấm)
3. [Luồng chuẩn và các chức năng quanh nó](#3-luồng-chuẩn-và-các-chức-năng-quanh-nó)
4. [Bảng fit-gap](#4-bảng-fit-gap)
5. [Tỷ lệ phủ theo chặng](#5-tỷ-lệ-phủ-theo-chặng)
6. [Mười chỗ hở đáng làm nhất](#6-mười-chỗ-hở-đáng-làm-nhất)
7. [Những chỗ ERP DEGO đi xa hơn ERPNext](#7-những-chỗ-erp-dego-đi-xa-hơn-erpnext)
8. [Ghi chú cách đọc và giới hạn của bản này](#8-ghi-chú-cách-đọc-và-giới-hạn-của-bản-này)

---

## 1. Kết luận trong một trang

- Tính trên **52 chức năng** của chuỗi mua hàng và kho (từ dữ liệu gốc tới báo cáo), ERP DEGO phủ **30,5 / 52 = 59 %** so với ERPNext v16.
- Phần **trước khi hàng về** làm tốt, nhiều chỗ hơn hẳn ERPNext: hỏi giá và chọn nhà cung cấp 90 %, đơn mua hàng và duyệt 81 %, báo cáo 90 %.
- Phần **từ cửa kho trở đi** là chỗ hở: nhận hàng và kiểm chất lượng 43 %, kho 38 %, hóa đơn và công nợ 50 %. Nguyên nhân gốc đã nêu ở [01 mục 7](01-luong-chuan-mua-hang-kho-san-xuat.md#7-so-với-hiện-trạng-erp-dego): phiếu nhập kho sinh ngầm từ dòng giao của đơn, công nợ sinh theo giá đơn chứ không theo hóa đơn, sổ kho chỉ có nhập và điều chỉnh tay.
- Dữ liệu gốc 50 %, yêu cầu mua 40 %: thiếu mức tồn tối thiểu tự đề nghị mua, thiếu lô và hạn dùng, thiếu ngân sách.
- Muốn lên **75 %** thì làm bảy việc đầu trong mục 6 (trả hàng, số lượng từ chối, phiếu nhập của thủ kho, xuất và chuyển kho, hóa đơn nhà cung cấp, mức tồn tối thiểu, chi phí vào giá vốn). Đây cũng chính là nấc 1 và nấc 2 của lộ trình ở doc 01 mục 8.

## 2. Cách chấm

- Mỗi chức năng chấm một trong ba mức: **Có** = 1 điểm, **Một phần** = 0,5 điểm, **Chưa** = 0 điểm.
- **Có**: người dùng làm được việc đó trên màn hình, có chứng từ hoặc dữ liệu riêng, không phải đi vòng.
- **Một phần**: làm được nhưng thiếu một mảnh quan trọng (ví dụ có dữ liệu mà không có màn, có màn mà không chặn ở máy chủ, có một kết quả cho cả lô thay vì từng dòng).
- **Chưa**: không có, hoặc chỉ làm được bằng cách sửa xóa dữ liệu khác.
- Mốc là ERPNext v16 bản chuẩn, không tính app ngoài. Chức năng ERPNext không có mà ERP DEGO có thì vẫn tính 1 điểm cho ERP DEGO và ghi riêng ở mục 7.
- Tỷ lệ theo chặng = tổng điểm của chặng chia cho số chức năng trong chặng. Tỷ lệ chung chia cho 52. Không gán trọng số khác nhau giữa các chức năng, vì mục đích là nhìn độ phủ, không phải xếp hạng giá trị; giá trị xếp riêng ở mục 6.

## 3. Luồng chuẩn và các chức năng quanh nó

Luồng mua hàng chuẩn (Procure-to-Pay) gồm bảy chặng, ERPNext đặt tên chứng từ tương ứng trong ngoặc:

```
Yêu cầu mua (Material Request)
  -> Hỏi giá nhiều NCC (Request for Quotation) -> Báo giá NCC (Supplier Quotation) -> So sánh
  -> Đơn mua hàng (Purchase Order) -> Duyệt theo luồng và hạn mức (Workflow)
  -> Nhận hàng (Purchase Receipt) -> Kiểm chất lượng (Quality Inspection) -> Nhập kho (Stock Ledger)
  -> Hóa đơn NCC (Purchase Invoice) -> Công nợ (Accounts Payable)
  -> Thanh toán (Payment Entry)
```

Quanh luồng chính còn các chức năng mà một phòng thu mua và kho thật sự dùng hằng ngày:

| Nhóm | Chức năng chuẩn | ERPNext làm thế nào |
|---|---|---|
| Nhu cầu | Mức tồn tối thiểu tự sinh yêu cầu mua | Re-order Level trên mặt hàng theo kho; job hằng ngày sinh Material Request khi số lượng dự kiến (tồn + đang đặt + đang yêu cầu − đã giữ) dưới mức |
| Nhu cầu | Yêu cầu từ kế hoạch sản xuất | Production Plan sinh Material Request theo BOM |
| Nhu cầu | Ngân sách | Budget theo trung tâm chi phí, chặn hoặc cảnh báo khi đơn vượt |
| Nhận hàng | Nhận thiếu, nhận nhiều lần | Nhiều Purchase Receipt cho một đơn, đơn hiện % đã nhận, lần sau tự điền phần còn lại, nút Close để chốt phần không giao nữa |
| Nhận hàng | Số lượng từ chối | Rejected Qty + Rejected Warehouse trên dòng biên nhận: hàng hỏng vào kho riêng, không cộng tồn dùng được |
| Nhận hàng | Trả hàng NCC | Purchase Receipt Return (số lượng âm) và Debit Note trên hóa đơn |
| Giá | Chi phí nhập khẩu vào giá vốn | Landed Cost Voucher: cước, thuế, phí cảng phân bổ theo giá trị hoặc số lượng, cộng thẳng vào giá vốn từng kg trong sổ kho |
| Giá | Tỷ giá | Tỷ giá trên đơn và hóa đơn; thanh toán khác tỷ giá thì tự ghi lãi hoặc lỗ tỷ giá |
| Hợp đồng | Hợp đồng khung | Blanket Order: số lượng và giá cam kết theo kỳ, đơn mua trừ dần |
| NCC | Đánh giá NCC | Supplier Scorecard: tiêu chí, chu kỳ, điểm, tự chặn tạo đơn khi điểm thấp |
| Báo cáo | Phân tích mua hàng, tồn kho, sổ kho, sổ cái | Purchase Order Analysis, Stock Balance, Stock Ledger, General Ledger |

## 4. Bảng fit-gap

Cột **ERP DEGO** ghi mức và điểm. Cột **Ở đâu bên mình** chỉ màn hoặc mã nguồn để người sau kiểm lại được.

### A. Dữ liệu gốc

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| A1 | Danh mục mặt hàng: mã, tên, nhóm, đơn vị, quy cách | Item, Item Group, UOM | **Có** 1 | `product/`, `catalog/` (phân loại, đơn vị tính); v2 `production/pages/product-*`, `item-group-*`, `unit-*`. `tab_product` là bảng SKU, nối chứng từ bằng chuỗi `product_code` |
| A2 | Nhiều đơn vị tính và quy đổi cho một mặt hàng | UOM Conversion trên Item | **Chưa** 0 | Mỗi sản phẩm một `unit`; phiếu khảo sát chỉ chụp đơn vị báo giá (`snap_quote_unit`), không quy đổi |
| A3 | Lô, số serial, hạn dùng | Batch, Serial No, Expiry | **Chưa** 0 | Không có cột lô, hạn dùng ở sản phẩm, lần giao hay sổ kho (doc 01 điểm k) |
| A4 | Danh mục nhà cung cấp: pháp lý, ngân hàng, điều khoản thanh toán | Supplier, Payment Terms | **Có** 1 | `supplier/model.py`: mã số thuế, loại pháp nhân, tài khoản ngân hàng, `payment_terms`, số ngày kiểm hàng, số ngày trả hàng, hạn xuất hóa đơn; v2 `production/pages/supplier-detail-page` 5 tab |
| A5 | Danh mục kho, vị trí, loại kho (chờ kiểm, cách ly, hàng lỗi) | Warehouse cây, Rejected Warehouse | **Một phần** 0,5 | `tab_warehouse` (`catalog/`), v2 `inventory/pages/warehouse-*`; chưa có vị trí, loại kho, kho hàng lỗi (doc 01 điểm j) |
| A6 | Bảng giá nhà cung cấp, giá mua gần nhất | Item Price, Price List | **Một phần** 0,5 | Không có bảng giá; có lịch sử mua (`purchase_history/`, tab trên sản phẩm) và công cụ giá tốt nhất (`product_best_price`) suy từ đơn đã mua |
| A7 | Hợp đồng khung: số lượng, giá cam kết, kỳ hạn, trừ dần theo đơn | Blanket Order | **Một phần** 0,5 | `contract/`: hợp đồng theo đối tác có loại, ngày hiệu lực, hết hạn, cảnh báo sắp hết (`contract_list_by_expiry`); không có số lượng hay giá cam kết, đơn mua không trừ vào hợp đồng |

### B. Yêu cầu mua

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| B1 | Yêu cầu mua hàng có duyệt, phạm vi theo phòng và pháp nhân | Material Request + Workflow | **Có** 1 | `purchase_request/`, `approval/` (luồng theo loại chứng từ, điều kiện so sánh số, duyệt theo quyền duoc-CR-680); phòng tự mua hàng `dept_proc` (bao-CR-414) |
| B2 | Mức tồn tối thiểu tự sinh yêu cầu mua | Re-order Level + Auto Material Request | **Chưa** 0 | Không có cột mức tồn trên sản phẩm hay kho; không có job quét tồn |
| B3 | Yêu cầu mua từ kế hoạch sản xuất (BOM, MRP) | Production Plan | **Chưa** 0 | Phân hệ Sản xuất v2 chưa có BOM hay lệnh sản xuất (doc 01 mục 7.0) |
| B4 | Theo dõi từng dòng yêu cầu tới đơn, tới nhận hàng | Cột Ordered Qty, Received Qty trên Material Request | **Có** 1 | `line_status` sáu trạng thái, `qty_ordered`, `qty_received` trên dòng YCMH; màn Chi tiết YC mua hàng (bao-CR-691) ghép mã đơn, NCC, hẹn giao |
| B5 | Ngân sách, hạn mức chi theo phòng hoặc kỳ | Budget | **Chưa** 0 | Không có; chữ "ngân sách" trong mã chỉ là loại chi phí thuế nộp ngân sách nhà nước |

### C. Hỏi giá và chọn nhà cung cấp

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| C1 | Gửi yêu cầu báo giá cho nhiều NCC từ yêu cầu mua | Request for Quotation | **Có** 1 | `survey_request/` (YCBG) tạo từ YCMH, mỗi dòng nhiều NCC; Tiến độ báo giá |
| C2 | Lưu báo giá từng NCC, so sánh, chọn phương án | Supplier Quotation + báo cáo so sánh | **Có** 1 | `SurveyRequestOption`, `PurchaseRequestItemOption` (giá, MOQ, giao hàng, mẫu, kết quả lab), chọn `is_chosen`; luồng phương án (bao-CR-449); Báo cáo khảo sát |
| C3 | Khảo sát, thẩm định NCC mới và sản phẩm mới | Supplier onboarding (thủ công) | **Có** 1 | `survey/` phiếu khảo sát NCC và sản phẩm, kết quả duyệt |
| C4 | Chấm điểm NCC định kỳ theo giá, đúng hạn, chất lượng; chặn NCC kém | Supplier Scorecard | **Một phần** 0,5 | Chỉ có công cụ AI `supplier_scorecard` (giá 40, ổn định 20, đúng hạn 20, pháp lý 20) tính lúc hỏi; không có màn, không có kỳ, không chặn tạo đơn |
| C5 | Tra cứu giá thị trường để đối chiếu báo giá | Không có | **Có** 1 | `customs/` tra cứu tờ khai hải quan, thống kê giá, thời điểm mua (bao-CR-470 tới 603) |

### D. Đơn mua hàng và duyệt

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| D1 | Lập đơn từ yêu cầu hoặc báo giá, dữ liệu chép sang | Create từ Supplier Quotation | **Có** 1 | `purchase_order/service.py` tạo từ phương án đã chọn; dòng đơn giữ `src_pr_item_id` |
| D2 | Duyệt theo luồng, điều kiện theo số tiền, người duyệt theo quyền | Workflow với điều kiện | **Có** 1 | `approval/flow_model.py` loại `purchase_order`, `condition_service.py`; chuông và thư khi gửi duyệt |
| D3 | Khóa đơn sau duyệt, sửa đổi có phiên bản | Submit khóa, Amend tạo bản mới | **Một phần** 0,5 | `block_edit_approved_order` chặn sửa giá, số lượng, NCC; muốn sửa chỉ có Hủy duyệt về nháp, không giữ phiên bản (doc 01 điểm i) |
| D4 | Ngoại tệ và tỷ giá trên đơn | Currency, Exchange Rate | **Có** 1 | `exchange_rate` ở đầu đơn và từng dòng, `base_amount` (bao-CR-436, 437) |
| D5 | Thuế theo dòng, mẫu thuế dùng lại | Taxes and Charges Template | **Một phần** 0,5 | VAT % từng dòng; không có mẫu thuế, thuế nhập khẩu đi theo dòng chi phí thu mua |
| D6 | Điều khoản và hạn thanh toán, nhắc trước hạn | Payment Terms, Payment Schedule | **Có** 1 | `supplier.payment_terms`, `payable.due_date`, `payable/due_alerts.py` nhắc tới hạn, `payment_due_date` cho từng khoản chi phí |
| D7 | Đóng phần còn lại của đơn không giao nữa | Close Purchase Order | **Một phần** 0,5 | Trạng thái đơn đổi tay sang Hoàn thành; không có thao tác đóng phần dư riêng cho dòng, không có dung sai |
| D8 | Chi phí mua hàng ngoài giá hàng (cước, thuế, phí) gắn vào đơn | Landed Cost sau nhận hàng | **Có** 1 | `tab_po_cost` ba giai đoạn dự toán, tạm tính, quyết toán; năm cách chia về dòng hàng; công nợ riêng cho đơn vị vận chuyển (bao-CR-319, 453 tới 478). Đi trước ERPNext ở khâu dự toán |

### E. Nhận hàng và kiểm chất lượng

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| E1 | Phiếu nhập kho là chứng từ riêng, thủ kho lập và gửi | Purchase Receipt | **Một phần** 0,5 | `goods_receipt/` sinh ngầm khi người sửa đơn gõ số nhận trên dòng giao (doc 01 điểm d); không có màn nhập riêng, không tách người đặt và người nhận |
| E2 | Nhận thiếu, nhận nhiều lần, theo dõi phần còn lại | Nhiều Purchase Receipt, % đã nhận | **Có** 1 | `tab_po_delivery` nhiều lần giao một dòng, `progress_status`, Tiến độ đơn mua hàng theo lần giao, thẻ nhận đủ hay chưa |
| E3 | Dung sai nhận vượt số đặt | Over Receipt Allowance | **Chưa** 0 | Máy chủ không chặn số nhận vượt số đặt (doc 01 điểm h) |
| E4 | Kiểm chất lượng theo chỉ tiêu, chặn nhập khi không đạt | Quality Inspection, Inspection Required | **Một phần** 0,5 | `qc_result` một ô chữ cho cả lần giao (Đạt, Thiếu, Lỗi); Lỗi chỉ đổi trạng thái lần giao, hàng vẫn vào tồn và sinh công nợ (doc 01 điểm b) |
| E5 | Số lượng từ chối, kho hàng lỗi riêng | Rejected Qty, Rejected Warehouse | **Chưa** 0 | Không ghi được 92 đạt 8 lỗi; không có kho hàng lỗi |
| E6 | Trả hàng nhà cung cấp, giảm tồn và giảm nợ | Purchase Receipt Return, Debit Note | **Chưa** 0 | Không có phiếu; cách duy nhất là xóa lần giao, kéo theo xóa phiếu nhập và công nợ (doc 01 điểm f) |
| E7 | Lịch hẹn giao, cảnh báo trễ, thông báo giao hàng | Required By, báo cáo trễ | **Có** 1 | `promised_date`, `expected_date` trên lần giao; Tiến độ đơn mua hàng thẻ trễ hạn; bản biểu đồ giao đúng hạn |

### F. Kho

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| F1 | Sổ kho và tồn theo kho, theo mặt hàng | Stock Ledger, Stock Balance | **Có** 1 | `inventory/` `tab_inventory_move`, tồn `qty`, `avg_cost`, `value`; v2 `inventory-list-page`, bảng tổng quan |
| F2 | Giá vốn bình quân có kỳ, có khóa sổ | Moving Average hoặc FIFO theo thời điểm, khóa kỳ | **Một phần** 0,5 | Bình quân tính lại trên toàn bộ lịch sử mỗi lần lưu; dòng sổ sửa xóa được; không có ngày ghi sổ, không khóa kỳ (doc 01 điểm c) |
| F3 | Chi phí nhập khẩu cộng vào giá vốn tồn kho | Landed Cost Voucher cập nhật Stock Ledger | **Một phần** 0,5 | Chi phí đã phân bổ về dòng hàng (D8) nhưng giá kho vẫn bằng đơn giá đơn nhân tỷ giá (doc 01 điểm e) |
| F4 | Xuất kho cho sản xuất, bán, hao hụt | Stock Entry Material Issue, Delivery Note | **Chưa** 0 | `ref_type` chỉ có `gr` và `adjust`; tồn chỉ tăng |
| F5 | Chuyển kho | Stock Entry Material Transfer | **Chưa** 0 | Không có; phải điều chỉnh âm một bên, dương một bên |
| F6 | Kiểm kê và điều chỉnh có duyệt | Stock Reconciliation | **Một phần** 0,5 | `POST /api/inventory/adjust` điều chỉnh tay, đơn giá tùy ý, không có phiếu kiểm kê, không duyệt |
| F7 | Mức tồn tối thiểu, cảnh báo thiếu hàng | Re-order Level, báo cáo Stock Projected Qty | **Chưa** 0 | Như B2 |
| F8 | Báo cáo tồn, sổ chi tiết, định giá tồn | Stock Balance, Stock Ledger, Stock Valuation | **Một phần** 0,5 | Màn tồn và phát sinh, tab Tồn kho trong Báo cáo mua hàng; không có sổ theo kỳ, không có định giá theo mốc ngày |

### G. Hóa đơn, công nợ và thanh toán

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| G1 | Hóa đơn nhà cung cấp là chứng từ riêng, đối chiếu ba chiều đơn, nhận, hóa đơn | Purchase Invoice, so khớp số lượng và giá | **Một phần** 0,5 | Công nợ sinh ngay lúc nhận theo giá đơn; số và ngày hóa đơn chỉ là ô ghi chú trên lần giao (doc 01 điểm a); không có chứng từ hóa đơn, không so giá |
| G2 | Công nợ theo nhà cung cấp, tuổi nợ, hạn trả | Accounts Payable, Payable Aging | **Có** 1 | `payable/` theo nguồn hàng, cước, chi phí; tuổi nợ ở trang chủ; cảnh báo tới hạn; xuất Excel (bao-CR-275) |
| G3 | Đề nghị thanh toán có duyệt, phân bổ vào từng khoản nợ | Payment Entry phân bổ | **Có** 1 | `payment_request/` chọn khoản nợ, duyệt, in; đối trừ đúng khoản (vá 82ce6ad) |
| G4 | Thanh toán trước, đối trừ với nợ hàng về sau | Advance Payment | **Có** 1 | `apply_prepay_offsets` (CR-268) gắn đúng đơn |
| G5 | Lãi, lỗ tỷ giá khi thanh toán ngoại tệ | Exchange Gain/Loss tự sinh | **Chưa** 0 | Thanh toán theo tỷ giá dòng đơn, không ghi chênh lệch |
| G6 | Giảm trừ công nợ: trả hàng, chiết khấu, phiếu ghi nợ | Debit Note | **Chưa** 0 | Không có; chiết khấu trên hóa đơn không ghi được |
| G7 | Bút toán kế toán tự sinh, sổ cái, nối phần mềm kế toán | General Ledger | **Chưa** 0 | ERP DEGO không làm kế toán; đối chiếu MISA bằng tay qua `misa_code` trên đơn; nối MISA là nấc 3 của doc 01 |

### H. Báo cáo và phân tích

| # | Chức năng | ERPNext | ERP DEGO | Ở đâu bên mình |
|---|---|---|---|---|
| H1 | Phân tích mua hàng theo NCC, nhóm hàng, người phụ trách, bộ phận | Purchase Analytics | **Có** 1 | Báo cáo mua hàng 8 tab; Chi tiết YC mua hàng; Báo cáo khảo sát (`report/`) |
| H2 | Tiến độ báo giá, tiến độ đơn, giao đúng hạn | Purchase Order Analysis | **Có** 1 | Tiến độ báo giá, Tiến độ đơn mua hàng, bản biểu đồ; trang chủ thẻ giao đúng hạn |
| H3 | Lịch sử giá mua, giá tốt nhất, xu hướng | Purchase Price History (báo cáo) | **Có** 1 | `purchase_history/`, tab trên sản phẩm, công cụ AI `product_purchase_history`, `product_best_price` |
| H4 | Báo cáo tồn và định giá tồn theo kỳ | Stock Balance, Stock Ageing | **Một phần** 0,5 | Như F8 |
| H5 | Phân quyền từng báo cáo, giao theo người hoặc phòng | Role Permission | **Có** 1 | `report_access/` khóa từng báo cáo (duoc-CR-562), tab Báo cáo ở Phân quyền; đi xa hơn ERPNext |

## 5. Tỷ lệ phủ theo chặng

| Chặng | Số chức năng | Có | Một phần | Chưa | Điểm | Tỷ lệ |
|---|---|---|---|---|---|---|
| A. Dữ liệu gốc | 7 | 2 | 3 | 2 | 3,5 | 50 % |
| B. Yêu cầu mua | 5 | 2 | 0 | 3 | 2,0 | 40 % |
| C. Hỏi giá, chọn NCC | 5 | 4 | 1 | 0 | 4,5 | 90 % |
| D. Đơn mua hàng, duyệt | 8 | 5 | 3 | 0 | 6,5 | 81 % |
| E. Nhận hàng, kiểm chất lượng | 7 | 2 | 2 | 3 | 3,0 | 43 % |
| F. Kho | 8 | 1 | 4 | 3 | 3,0 | 38 % |
| G. Hóa đơn, công nợ, thanh toán | 7 | 3 | 1 | 3 | 3,5 | 50 % |
| H. Báo cáo | 5 | 4 | 1 | 0 | 4,5 | 90 % |
| **Chung** | **52** | **23** | **15** | **14** | **30,5** | **59 %** |

Đọc theo luồng: ba chặng đầu (yêu cầu, hỏi giá, đơn) đạt **72 %** (13 / 18); ba chặng sau (nhận hàng, kho, công nợ) đạt **43 %** (9,5 / 22). Chỗ cần đầu tư rõ ràng là nửa sau của luồng.

## 6. Mười chỗ hở đáng làm nhất

Xếp theo giá trị cho phòng thu mua và kho: chặn mất tiền trước, rồi tới cái mở đường cho sản xuất, rồi tới tiện dụng. Cột **Nấc** trỏ về lộ trình ở doc 01 mục 8.

| # | Chỗ hở | Vì sao đáng làm | Việc cụ thể | Nấc |
|---|---|---|---|---|
| 1 | **Số lượng từ chối và kiểm chất lượng chặn nhập** (E4, E5) | Hàng lỗi hiện vẫn vào tồn và sinh công nợ đủ; kế toán có thể chi đủ tiền cho lô có 30 bao rách | Thêm số lượng chấp nhận và số lượng từ chối trên lần giao; `qc_result` thành bộ mã cố định; tồn và công nợ tính theo số chấp nhận; lần giao Lỗi chưa có số chấp nhận thì không sinh công nợ | 1 |
| 2 | **Trả hàng nhà cung cấp** (E6, G6) | Không có phiếu, phải xóa lần giao và mất luôn dấu vết công nợ, phiếu nhập | Phiếu trả hàng tham chiếu lần giao: giảm tồn, sinh khoản giảm trừ công nợ, giữ nguyên phiếu nhập gốc | 2 |
| 3 | **Phiếu nhập kho do thủ kho lập** (E1) | Người mua vừa đặt vừa khai đã nhận; kho không có chứng từ của mình để đối chiếu khi lệch | Màn nhập kho riêng, thủ kho xác nhận số thực nhận; đơn chỉ hiện số nhận từ phiếu kho; tách quyền nhận hàng khỏi quyền sửa đơn | 2 |
| 4 | **Xuất kho và chuyển kho** (F4, F5) | Tồn chỉ tăng nên vài tháng nữa con số không còn nghĩa; chặn mọi việc của phân hệ Sản xuất | Phiếu xuất (sản xuất, bán, hao hụt) và phiếu chuyển kho ghi sổ chỉ thêm, có ngày ghi sổ; giá xuất theo bình quân tại thời điểm | 2 |
| 5 | **Hóa đơn nhà cung cấp và đối chiếu ba chiều** (G1) | Công nợ lệch MISA khi giá hóa đơn khác giá đơn, khi hóa đơn ra sau, khi có chiết khấu; đề nghị thanh toán có thể chi trước cho phần chưa có hóa đơn | Nấc 1: báo cáo hàng về chưa có hóa đơn, cảnh báo khi đề nghị thanh toán chọn khoản chưa có số hóa đơn. Nấc 3: hóa đơn là chứng từ, công nợ sinh từ hóa đơn, so khớp số lượng và giá với đơn và phiếu nhập | 1, 3 |
| 6 | **Mức tồn tối thiểu và tự đề nghị mua** (B2, F7) | Hiện phòng mua chỉ biết thiếu khi sản xuất kêu; ERPNext làm việc này bằng một job hằng ngày | Cột mức đặt hàng lại và số lượng đề nghị trên sản phẩm theo kho; job đêm so tồn dự kiến (tồn + đang đặt) với mức, sinh YCMH nháp cho phòng mua; màn danh sách hàng dưới mức | 2 |
| 7 | **Chi phí nhập khẩu vào giá vốn** (F3) | Số đã phân bổ về dòng hàng rồi mà giá kho vẫn thiếu 5 % với lô nhập khẩu; sai giá thành khi bắt đầu tính giá vốn sản xuất | Khi quyết toán chi phí, ghi một dòng sổ kho điều chỉnh giá trị cho lô đó; chi phí về muộn ghi vào lô còn tồn | 2 |
| 8 | **Sổ kho có ngày ghi sổ và khóa kỳ** (F2, F8) | Sửa số nhận tháng trước làm đổi tồn cuối tháng đã gửi kế toán; không ai biết | Ngày ghi sổ riêng, khóa kỳ theo tháng, sửa sau khóa phải qua phiếu điều chỉnh có duyệt; báo cáo tồn theo mốc ngày | 2 |
| 9 | **Hợp đồng khung có số lượng và giá** (A7) | Nhiều mặt hàng mua lặp lại theo giá đã thỏa thuận cả năm; hiện mỗi đơn gõ lại giá, không ai thấy đã dùng hết hạn mức chưa | Thêm dòng hàng, số lượng, giá, kỳ hạn vào hợp đồng; đơn mua chọn hợp đồng thì chép giá và trừ dần; cảnh báo vượt | 2 |
| 10 | **Chấm điểm nhà cung cấp định kỳ trên màn** (C4) | Công cụ AI đã có cách tính; thiếu màn, thiếu kỳ, thiếu hậu quả (cảnh báo khi chọn NCC điểm thấp) | Màn điểm NCC theo quý từ đúng công thức của `supplier_scorecard`; hiện điểm cạnh tên NCC khi chọn phương án và lập đơn | 2 |

Hai chỗ hở nữa đáng ghi nhưng xếp sau vì phụ thuộc kế toán: **ngân sách theo phòng** (B5) và **lãi lỗ tỷ giá** (G5). Cả hai chỉ có nghĩa khi ERP DEGO nối được với sổ kế toán (nấc 3).

## 7. Những chỗ ERP DEGO đi xa hơn ERPNext

Để nhìn công bằng, phần này liệt kê thứ ERPNext v16 không có hoặc làm thô hơn:

- **Chi phí thu mua ba giai đoạn** (dự toán, tạm tính, quyết toán) ngay từ lúc lập đơn, năm cách phân bổ; ERPNext chỉ có Landed Cost sau khi đã nhận hàng.
- **Tra cứu giá thị trường từ tờ khai hải quan** để đối chiếu báo giá; ERPNext không có nguồn giá ngoài.
- **Khảo sát nhà cung cấp và sản phẩm** thành chứng từ có duyệt, kết quả lab, mẫu; ERPNext để việc này ngoài hệ thống.
- **Luồng phương án trên yêu cầu mua**: người yêu cầu chọn phương án, thu mua chốt, áp một NCC cho nhiều dòng (bao-CR-449).
- **Phòng tự mua hàng** với phạm vi `dept_proc`: một phòng vừa yêu cầu vừa mua trong khuôn khổ riêng (bao-CR-414).
- **Phân quyền từng báo cáo** cho người hoặc phòng (duoc-CR-562).
- **Trợ lý AI và cổng MCP**: hỏi tiến độ, giá tốt nhất, chấm điểm NCC, soạn YCMH bằng lời.

Những điểm này không bù được cho nửa sau của luồng; chúng là lợi thế ở khâu chọn mua, còn khâu nhận và giữ hàng vẫn phải làm cho đủ.

## 8. Ghi chú cách đọc và giới hạn của bản này

- Chấm theo mã nguồn và tài liệu đang có, có đối chiếu với phần soát mã ngày 23/10 ở doc 01 mục 7. Không chạy thử từng màn trên dev cho bản này.
- "Có" không có nghĩa là làm giống ERPNext; chỉ có nghĩa là nghiệp vụ đó làm được trên ERP DEGO.
- Số 59 % là độ phủ chức năng, không phải mức độ dùng thật của các phòng. Mức dùng thật tra ở báo cáo Mức dùng chức năng (duoc-CR-655).
- Khi làm xong một việc ở mục 6, cập nhật dòng tương ứng ở bảng mục 4 và tính lại mục 5 để con số còn đúng.
