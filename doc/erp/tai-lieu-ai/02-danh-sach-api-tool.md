# Danh sách API / tool cho bot (loại A - dữ liệu có cấu trúc)

Phiên bản: 25/08/2026. Trạng thái: nháp để bàn, chưa code.
Liên quan: kiến trúc ở `01-kien-truc-tro-ly-ai.md`.

Đây là danh sách "công cụ" (tool) mà Claude được phép gọi khi câu hỏi thuộc loại A. Mỗi tool
ánh xạ đúng một hàm service. Bot KHÔNG sinh SQL, chỉ chọn tool + điền tham số theo schema.

Quy tắc chung cho MỌI tool (chi tiết ở tài liệu 01 mục 4.2):
- Chạy DƯỚI danh tính người hỏi (JWT của họ). Bot không có tài khoản riêng.
- Gác hai lớp: `require(entity, action)` + `apply_scope(...)`. Cột "Quyền" là entity + action.
- Read-only giai đoạn đầu (action luôn là `read`).
- Giới hạn số dòng trả về (mặc định gợi ý: 50), có tham số `limit`.

Ký hiệu cột "Tình trạng": TÁI DÙNG = đã có endpoint list/filter, chỉ bọc lại; MỚI = cần viết
truy vấn tổng hợp mới (thường là group-by / min-max).

---

## Nhóm 1 - Hợp đồng NCC

### T1. contract_list_by_expiry - Hợp đồng theo trạng thái hạn
- Mục đích: trả lời "HĐ với NCC nào còn hạn / đã hết hạn, bao nhiêu cái".
- Tham số: `status` (active | expired | all), `supplier_code` (tùy chọn), `as_of_date`
  (tùy chọn, mặc định hôm nay).
- Đầu ra: danh sách HĐ (số HĐ, NCC, ngày ký, ngày hết hạn, trạng thái) + tổng số.
- Nguồn: bảng `contract` (`end_date` có index, `status`, cột `expiry` máy tính).
- Quyền: `contract` + `read`.
- Tình trạng: TÁI DÙNG (đã có filter theo status/ngày), thêm tham số `as_of_date`.

### T2. contract_count_by_status - Đếm HĐ còn hạn / hết hạn
- Mục đích: câu tổng hợp "còn hạn bao nhiêu, hết hạn bao nhiêu", có thể theo NCC.
- Tham số: `group_by` (supplier | none), `as_of_date` (tùy chọn).
- Đầu ra: số lượng theo trạng thái, kèm phân rã theo NCC nếu group_by=supplier.
- Nguồn: `contract`.
- Quyền: `contract` + `read`.
- Tình trạng: MỚI (group-by/count).

### T3. supplier_contracts - Một NCC có những HĐ nào
- Mục đích: "NCC X mình đang có HĐ nào, còn hạn không".
- Tham số: `supplier_code` (bắt buộc), `status` (tùy chọn).
- Đầu ra: danh sách HĐ của NCC đó.
- Nguồn: `contract` (lọc theo NCC).
- Quyền: `contract` + `read`.
- Tình trạng: TÁI DÙNG.

---

## Nhóm 2 - Giá và lịch sử mua

### T4. product_best_price - Giá tốt nhất của một mã hàng
- Mục đích: "mã A giá ổn nhất là bao nhiêu, của NCC nào, MOQ nào".
- Tham số: `product_code` (bắt buộc), `date_from` / `date_to` (tùy chọn, giới hạn kỳ),
  `top_n` (mặc định 3).
- Đầu ra: top NCC theo giá thấp nhất, kèm giá, số lượng (qty_order), VAT, ngày mua gần nhất.
- Nguồn: `purchase_history` (`product_code`, `price`, `qty_order`, `vat`, `order_date`).
- Quyền: `purchase_history` + `read`.
- Tình trạng: MỚI (min-price group-by NCC). Lưu ý so giá phải cùng đơn vị/quy đổi - ghi rõ
  giả định trong kết quả, không tự quy đổi âm thầm.

### T5. product_purchase_history - Lịch sử mua của một mã hàng
- Mục đích: "mã A đã mua của những ai, giá bao nhiêu, khi nào".
- Tham số: `product_code` (bắt buộc), `limit` (mặc định 50), sắp theo `order_date` desc.
- Đầu ra: danh sách dòng mua (NCC, giá, số lượng, VAT, ngày, mã PO).
- Nguồn: `purchase_history`.
- Quyền: `purchase_history` + `read`.
- Tình trạng: TÁI DÙNG (đã có list + filter theo product_code).

### T6. suppliers_for_product - Các NCC từng bán một mã hàng
- Mục đích: "gợi ý danh sách NCC cho mã A".
- Tham số: `product_code` (bắt buộc).
- Đầu ra: danh sách NCC từng bán mã đó, kèm số lần mua + giá gần nhất.
- Nguồn: `purchase_history` join `supplier`.
- Quyền: `purchase_history` + `read`.
- Tình trạng: MỚI (distinct NCC theo mã + tổng hợp).

---

## Nhóm 3 - Tra danh mục (giúp bot map câu hỏi mô tả sang mã)

### T7. product_search - Tra mã hàng theo mã / tên / mô tả
- Mục đích: người hỏi gõ mô tả ("thùng carton 5 lớp") -> bot tìm ra `product_code` để gọi
  các tool trên.
- Tham số: `keyword` (bắt buộc), `limit` (mặc định 20).
- Đầu ra: danh sách sản phẩm khớp (code, name, item_group, unit, hh_code).
- Nguồn: bảng `product`.
- Quyền: `product` + `read`.
- Tình trạng: TÁI DÙNG (đã có tìm kiếm sản phẩm).

### T8. supplier_search - Tra NCC theo tên / mã / MST
- Mục đích: map tên NCC lộn xộn sang `supplier_code`.
- Tham số: `keyword` (bắt buộc), `limit` (mặc định 20).
- Đầu ra: danh sách NCC khớp (code, name, tax_code, supplier_type, còn hoạt động).
- Nguồn: bảng `supplier`.
- Quyền: `supplier` + `read`.
- Tình trạng: TÁI DÙNG.

---

## Nhóm 4 - Tổng hợp toàn hệ (bổ sung sau khi test UI 25/08/2026)

Bộ 8 tool trên tra theo MÃ cụ thể / hợp đồng; người dùng còn hỏi loại "tổng hợp toàn hệ theo
thời gian" nên thêm 4 tool. Tất cả tổng hợp NGAY trong SQL (không nạp hết bảng vào RAM).

### T9. recent_purchases - Lần mua gần nhất toàn hệ
- Mục đích: "mua gì gần nhất", "lần mua mới nhất là gì".
- Tham số: `date_from`, `date_to` (tùy chọn), `limit` (mặc định 20).
- Đầu ra: các dòng lịch sử mua mới nhất (ngày, mã hàng, SL, giá, thành tiền, PO; NCC nếu có quyền).
- Nguồn: `purchase_history` (sort `order_date` desc).
- Quyền: `product` + `read` (tên NCC cần thêm `supplier.read`).

### T10. top_suppliers_by_purchase - NCC mua nhiều nhất
- Mục đích: "NCC nào mua hàng nhiều nhất".
- Tham số: `date_from`, `date_to` (tùy chọn), `top_n` (mặc định 5).
- Đầu ra: xếp hạng NCC kèm CẢ tổng giá trị (`total_amount`) lẫn số lần mua (`times`).
- Nguồn: `purchase_history`, group theo `supplier_code`, `SUM(amount)` + `COUNT(*)`.
- Quyền: `supplier` + `read`.

### T11. recent_purchase_orders - Đơn mua hàng (PO) gần nhất + giá trị
- Mục đích: "đơn hàng gần nhất là gì, giá trị bao nhiêu".
- Tham số: `supplier_code`, `date_from`, `date_to` (tùy chọn), `limit` (mặc định 20).
- Đầu ra: PO mới nhất (mã, ngày, NCC, trạng thái, giá trị = tổng thành tiền các dòng).
- Nguồn: `purchase_order` + `po_item` (SUM amount theo `po_id`).
- Quyền: `purchase_order` + `read` (có `apply_scope` theo pháp nhân).

### T12. purchase_report - Báo cáo tổng quan mua hàng
- Mục đích: tổng chi tiêu, số dòng mua, số mã hàng / NCC, top mã theo chi tiêu; kèm chi tiêu
  theo tháng khi `group_by=month`.
- Tham số: `group_by` (`month` | `none`), `date_from`, `date_to` (tùy chọn).
- Nguồn: `purchase_history` (nhiều truy vấn tổng hợp SQL).
- Quyền: `product` + `read` (số lượng NCC chỉ hiện khi có `supplier.read`).

---

## Nhóm 5 - Thống kê TÙY BIẾN (một công cụ tham số rộng, bổ sung 25/08/2026)

Người dùng còn hỏi vô số biến thể "chỉ số theo chiều theo kỳ" mà đẻ tool riêng cho từng câu thì
không xuể. Thêm MỘT tool nhận tham số rộng, nhưng "rộng về câu hỏi - khóa về dữ liệu": mọi lựa
chọn nằm trong enum khai sẵn, bot KHÔNG sinh SQL, không chọn được bảng/cột ngoài luồng.

### T13. analytics_query - Thống kê mua hàng tùy biến
- Mục đích: câu thống kê KHÔNG khớp T1-T12, ví dụ "chi tiêu của NCC X theo từng tháng", "số
  lượng mã Y mua trong quý 1", "đơn giá trung bình mã Z".
- Tham số:
  - `metric`: `total_amount` (chi tiêu, gồm VAT) | `count` (số dòng mua) | `qty` (tổng số
    lượng) | `avg_price` (đơn giá TB). Mặc định `total_amount`.
  - `dimension`: `supplier` | `product` | `month` | `none` (tổng gộp một số). Mặc định `none`.
  - `date_from`, `date_to`, `supplier_code`, `product_code` (đều tùy chọn).
  - `sort`: `value_desc` | `value_asc` | `dimension` (chỉ áp khi có dimension). `top_n` (mặc
    định 10, trần 50).
- Đầu ra: `dimension=none` -> một `value`; có dimension -> danh sách `{group, group_name, value}`.
- Nguồn: `purchase_history`, tổng hợp NGAY trong SQL (group-by + sum/count/avg).
- Quyền: `product` + `read`; **`dimension=supplier` đòi thêm `supplier.read`** (lộ danh tính NCC).
- Ghi chú: `count` phải tham chiếu một cột của bảng để suy ra FROM khi `dimension=none` (nếu
  không SQLAlchemy ra 1 thay vì đếm dòng) — đã dùng `func.count(PurchaseHistory.id)`.

Nay bộ tool loại A có **13 cái** (T1-T13).

---

## Ghi chú mở rộng (để sau, chưa đưa vào giai đoạn đầu)

- Công nợ NCC (`payable`), tồn kho (`inventory`) - cùng khuôn: một tool read-only bọc service
  có sẵn, gác `require` + `apply_scope`.
- Nếu tool nào truy vấn quá nặng: tối ưu bằng bảng tổng hợp / cache, KHÔNG vector hóa
  (xem tài liệu 01 mục 2).

---

## Việc cần chốt

- Xác nhận danh sách 8 tool trên đủ cho giai đoạn đầu chưa, có cần thêm/bớt.
- Với mỗi tool MỚI (T2, T4, T6): xác nhận cách xử lý quy đổi đơn vị / kỳ so sánh giá.
- Đặt giới hạn số dòng trả về mặc định (gợi ý 50) và trần cứng.
