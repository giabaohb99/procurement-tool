# Danh sách API / tool cho bot (loại A - dữ liệu có cấu trúc)

Phiên bản: 28/08/2026 (bản đầu 25/08/2026). Trạng thái: **ĐÃ CODE đủ 30 tool** (T1-T30),
đang chạy dev — mã nguồn ở `backend/app/modules/assistant/tools/`.
Liên quan: kiến trúc ở `01-kien-truc-tro-ly-ai.md`; bảo mật và vận hành thực tế ở
`04-bao-mat-va-van-hanh.md`.
Ngoài tool, chat còn nhận **tệp đính kèm** (ảnh/PDF, CR-204) — không phải tool nên không
liệt kê ở đây, xem tài liệu 04 mục 7.

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
- Quyền: `product` + `read` VÀ `supplier` + `read` (bản chất câu trả lời là danh tính NCC).
- Tình trạng: MỚI (min-price group-by NCC). Lưu ý so giá phải cùng đơn vị/quy đổi - ghi rõ
  giả định trong kết quả, không tự quy đổi âm thầm.

### T5. product_purchase_history - Lịch sử mua của một mã hàng
- Mục đích: "mã A đã mua của những ai, giá bao nhiêu, khi nào".
- Tham số: `product_code` (bắt buộc), `limit` (mặc định 50), sắp theo `order_date` desc.
- Đầu ra: danh sách dòng mua (NCC, giá, số lượng, VAT, ngày, mã PO).
- Nguồn: `purchase_history`.
- Quyền: `product` + `read`; cột tên/mã NCC chỉ hiện khi có thêm `supplier.read`.
- Tình trạng: TÁI DÙNG (đã có list + filter theo product_code).

### T6. suppliers_for_product - Các NCC từng bán một mã hàng
- Mục đích: "gợi ý danh sách NCC cho mã A".
- Tham số: `product_code` (bắt buộc).
- Đầu ra: danh sách NCC từng bán mã đó, kèm số lần mua + giá gần nhất.
- Nguồn: `purchase_history` join `supplier`.
- Quyền: `product` + `read` VÀ `supplier` + `read`.
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

---

## Nhóm 6 - Văn bản và phê duyệt (bổ sung khi code, `document_tool.py` + `approval_tool.py`)

### T14. document_search - Tìm trong kho văn bản
- Mục đích: "công ty có quy định nào về công tác phí", tra số hiệu văn bản.
- Tham số: `keyword` (bắt buộc), `doc_type` (tùy chọn, tên/mã loại văn bản), `limit`
  (mặc định 20).
- Đầu ra: danh sách văn bản khớp (document_id, số hiệu, tiêu đề, loại, ngày ban hành).
- Nguồn: phân hệ Văn bản (`document`).
- Quyền: `document` + `read` (quét cả kho nên gác quyền phân hệ).

### T15. document_read - Đọc nội dung một văn bản
- Mục đích: đọc toàn văn để trả lời câu hỏi về điều khoản cụ thể.
- Tham số: `document_id` (lấy từ T14) hoặc `issue_number` (số hiệu, nhận cả số hiệu cũ
  bản giấy).
- Đầu ra: nội dung văn bản đã bóc HTML thành chữ thuần.
- Nguồn: `document` (nội dung trình soạn thảo).
- Quyền: kiểm quyền truy cập TỪNG văn bản (`access_service.can`); không có quyền thì trả
  CÙNG MỘT CÂU với "không tìm thấy" - không để lộ cả việc văn bản đó tồn tại.

### T16. my_documents - Văn bản áp dụng cho chính mình
- Mục đích: "tôi phải tuân theo quy định nào".
- Tham số: `keyword` (tùy chọn).
- Đầu ra: văn bản đang áp dụng cho người hỏi.
- Nguồn: như màn "áp dụng cho tôi" (`/api/documents/applies-to-me`).
- Quyền: chỉ cần đăng nhập (màn gốc ai cũng mở được).

### T17. approval_flow_lookup - Luồng phê duyệt của một loại chứng từ
- Mục đích: "YCMH phải qua những ai duyệt".
- Tham số: loại chứng từ (`purchase_request`...).
- Đầu ra: các bước duyệt theo cấu hình.
- Nguồn: phân hệ luồng phê duyệt.
- Quyền: `approval_flow` + `read` (đúng quyền của màn cấu hình luồng).

### T18. my_approval_tasks - Việc đang chờ CHÍNH MÌNH ký
- Mục đích: "tôi đang nợ chữ ký nào", xếp gần hạn lên trước, kèm cờ quá hạn + đường dẫn
  mở thẳng phiếu; ghi rõ việc ký THAY ai theo ủy quyền.
- Quyền: tự giới hạn vào người hỏi - không xem hộ hàng đợi của người khác được.

### T19. my_requests_status - Phiếu do CHÍNH MÌNH trình đang ở bước nào
- Mục đích: "phiếu của tôi tới đâu rồi, ai đang giữ"; phiếu bị trả lại có lý do.
- Quyền: tự giới hạn vào người hỏi.

---

## Nhóm 7 - Soạn nháp phiếu (`draft_tool.py`, KHÔNG ghi dữ liệu)

Cả ba tool chỉ trả về BẢN NHÁP; giao diện hiện nút mở form đã điền sẵn, người dùng tự rà và
tự bấm Tạo - phiếu không tự sinh. Schema hai tool đầu được gắn enum danh mục THẬT từ DB mỗi
lượt hỏi (phân loại VTBB/NL + pháp nhân nhận hóa đơn) để model không bịa tên ngoài danh mục;
form tự điền người yêu cầu / phòng ban / công ty theo hồ sơ người hỏi (khối NGƯỜI HỎI trong
system prompt), hỗ trợ mua cho pháp nhân khác qua tham số `company`.

### T20. draft_survey_request - Soạn nháp Yêu cầu báo giá (YCBG)
- Quyền: `survey_request` + `create` - không có quyền tạo phiếu thì không soạn hộ.

### T21. draft_purchase_request - Soạn nháp Yêu cầu mua hàng (YCMH)
- Quyền: `purchase_request` + `create`.

### T22. draft_leave_request - Soạn nháp đơn nghỉ phép
- Quyền: `document` + `create`.

---

## Nhóm 8 - Tiện ích (`export_tool.py`, `rag_tool.py`)

### T23. export_report_file - Xuất báo cáo dạng VĂN BẢN (Word .docx)
- Mục đích: "xuất cái báo cáo này ra file cho tôi" - bản trình bày có tiêu đề, hộp TL;DR,
  mục lục nội dung, bảng số liệu. Người dùng xin đích danh Excel/.xlsx thì model phải gọi
  T30, không dùng tool này.
- Quyền: chỉ đóng gói lại dữ liệu ĐÃ QUA LỌC QUYỀN ở tool báo cáo phía trước - không mở
  thêm đường dữ liệu mới.

### T24. search_docs - Tra cứu Hướng dẫn sử dụng (loại B - RAG)
- Mục đích: "làm sao tạo YCMH", trả lời kèm nguồn bài HDSD.
- Quyền: chỉ cần đăng nhập - CỐ Ý, vì Trung tâm HDSD vốn mở cho mọi người dùng đã đăng nhập.
- Ghi chú: chỉ đăng ký khi cờ `AI_RAG_ENABLED` bật.

### T30. export_excel_file - Xuất BẢNG TÍNH Excel (.xlsx) (CR-205, thêm 27/08/2026)
- Mục đích: "xuất danh sách này ra Excel" - dữ liệu dạng bảng để người dùng lọc/tính tiếp.
  Cặp với T23: T23 là văn bản trình bày, T30 là bảng tính; TOOL_GUIDE dặn model chọn theo
  lời xin của người dùng.
- Tham số: `filename` (không dấu, không đuôi) + `sheets` - tối đa **5 sheet x 15 cột x
  500 dòng/sheet**, mỗi sheet gồm `name` + `columns` + `rows`.
- Đầu ra: file .xlsx dựng bằng openpyxl (`render_xlsx` trong `export_tool.py`), giao diện
  hiện nút tải (FE `reply-offers.ts` nhận cả hai tên tool xuất file).
- Chi tiết kỹ thuật: ô là CHUỖI SỐ trần ("1500000") được đổi thành kiểu số thật của Excel
  để người nhận tính toán được; tên sheet cắt 31 ký tự + rửa ký tự Excel cấm; header in
  đậm + đóng băng dòng đầu + auto-width.
- Quyền: như T23 - chỉ đóng gói dữ liệu ĐÃ QUA LỌC QUYỀN ở các tool phía trước, không mở
  thêm đường dữ liệu mới; file lưu vào storage cùng khuôn `_store_report_file` với T23.

---

## Nhóm 9 - Công nợ + Yêu cầu thanh toán (`payable_tool.py`, thêm 27/08/2026)

### T25. payable_lookup - Tra công nợ phải trả
- Mục đích: "công nợ NCC X tháng này bao nhiêu, còn lại bao nhiêu", "khoản nào quá hạn".
- Tham số: `supplier` (mã/tên một phần), `company` (khớp danh mục, sai tên thì trả danh sách
  hợp lệ chứ KHÔNG lặng lẽ bỏ lọc), `status` (outstanding mặc định | paid | all),
  `date_from`/`date_to` (ngày phát sinh), `limit` (trần 30).
- Đầu ra: `summary` (tổng nợ / đã trả / còn lại / quá hạn) tính trên TOÀN BỘ kết quả lọc +
  danh sách từng khoản kèm `payable_id` để nối sang T26.
- Nguồn: cùng `apply_scope("payable")` + công thức quá hạn với màn Công nợ (`/api/payables`).
- Quyền: `payable` + `read`.

### T26. draft_payment_request - Soạn nháp Yêu cầu thanh toán (YCTT)
- Mục đích: "làm yêu cầu thanh toán cho NCC X" sau khi tra công nợ.
- Tham số: `payable_ids` (từ T25, chính xác nhất) HOẶC `supplier` bắt buộc +
  `company`/`date_from`/`date_to` tùy chọn; không có cả hai thì tool bắt hỏi lại,
  không gom nợ cả hệ.
- Đầu ra: bản nháp `kind=payment_request` gồm danh sách `payable_ids` hợp lệ + tổng còn lại
  theo NCC. Giao diện hiện nút "Tạo đề nghị thanh toán" mở form tạo YCTT qua đường
  `?payables=<ids>` của màn Công nợ - form TỰ NẠP LẠI các khoản dưới quyền người đăng nhập
  (backend kiểm lại phạm vi lần nữa), người dùng rà rồi tự bấm Lưu; nhiều NCC thì hệ thống
  tự tách mỗi NCC một phiếu như lập tay.
- Luật cứng: CHỈ chọn khoản `remaining > 0` - khoản đã tất toán bị loại và báo trong
  `skipped_ids` (bài học lỗi phân bổ thanh toán, fix `82ce6ad`); trần 50 khoản/bản nháp.
- Quyền: `payment_request` + `create` VÀ `payable` + `read` - thiếu một trong hai là denied
  (bản nháp lộ số nợ + tên NCC nên không được vòng qua hàng rào của T25).

---

## Nhóm 10 - Trợ lý cho quản lý (`procurement_doc_tool.py`, thêm 27/08/2026)

Cụm "trợ lý riêng" cho người duyệt: recap nhanh một chứng từ + đếm phiếu đang chờ chính
mình duyệt. Nguyên tắc cứng: **trợ lý KHÔNG duyệt hộ** - mọi kết quả chỉ kèm `url` mở màn
chi tiết, con người tự bấm Duyệt ở đó.

### T27. procurement_doc_read - Recap một chứng từ thu mua
- Mục đích: "đơn PO00123 tới đâu rồi", "recap đơn hàng X", "ai mua gì giá bao nhiêu".
- Tham số: `entity` (purchase_order | purchase_request | survey_request) + `code` hoặc `id`.
  MỘT tool generic cho cả ba loại, không đẻ tool theo màn.
- Đầu ra: đầu phiếu (trạng thái kèm nhãn tiếng Việt chép đúng chữ frontend-v2, người phụ
  trách, `url`), tối đa 30 dòng hàng (SL đặt/nhận, giá, nhãn tiến độ từ bộ mã
  `PO_PROGRESS_STATUS`/`PR_LINE_STATUS`), tổng giá trị tính trên ĐỦ dòng kể cả phần bị cắt.
  Riêng ĐMH kèm khối công nợ phát sinh theo `po_code` (chỉ khi có `payable.read`); riêng
  YCKS chỉ ĐẾM số phương án mỗi dòng - bảng option chứa NCC thuộc cơ chế ẩn nên không trả
  chi tiết. Muốn so giá: lấy `product_code` từng dòng gọi tiếp T5/T6 (product_best_price /
  suppliers_for_product).
- Quyền: `entity` + `read`, lấy phiếu qua `apply_scope` (mã đúng nhưng ngoài phạm vi =
  "không tìm thấy", không lộ tồn tại); thiếu `supplier.read` thì ẩn NCC kèm ghi chú
  (kể cả `suggested_supplier` của YCMH); YCMH đã xóa mềm coi như không tồn tại.

### T28. pending_procurement_approvals - Phiếu thu mua chờ chính người hỏi duyệt
- Mục đích: "tôi cần duyệt bao nhiêu phiếu khảo sát", "có đơn nào chờ tôi duyệt không".
- Tham số: `entity` lọc một loại (tùy chọn) + `limit` (mặc định 10, trần 30).
- Phạm vi: 5 loại phiếu trạng thái `submitted` - YCBG, Phiếu khảo sát, YCMH, ĐMH, YCTT.
  Mỗi loại CHỈ đếm khi người hỏi có `entity` + `approve`, và chỉ trong `apply_scope` của
  chính họ; loại không có quyền bị bỏ qua kèm ghi chú (hỏi đích danh loại không có quyền
  thì denied thẳng). Liệt kê phiếu trình sớm nhất trước, mỗi phiếu kèm `url`.
- Khác T18 (my_approval_tasks): T18 đọc BỘ MÁY PHÊ DUYỆT (hiện chỉ Văn bản chạy); chứng
  từ thu mua duyệt bằng nút trạng thái trên từng màn nên phải đếm thẳng cột `status`.
- Đầu ra luôn kèm `reminder` nhắc model: không duyệt hộ, đưa link để người dùng tự bấm.

### T29. my_procurement_requests - Phiếu thu mua của chính người hỏi + tiến độ mua
- Mục đích: "phiếu của tôi tới đâu rồi", "YCMH mới nhất của tôi", "hàng tôi đặt đã về
  chưa" - dành cho nhân viên yêu cầu, không cần quyền duyệt gì.
- Tham số: `entity` (survey_request | purchase_request, tùy chọn) + `limit` (mặc định 10,
  trần 30). Mới nhất trước.
- Phạm vi "CỦA TÔI": phiếu do chính người hỏi tạo (`created_by`) HOẶC đứng tên người yêu
  cầu (`requester_id` = ID nhân sự của họ) - kể cả khi scope của họ là `all` (quản lý hỏi
  "phiếu của tôi" vẫn chỉ nhận phiếu mình đứng tên, không đổ cả công ty). Vẫn qua
  `apply_scope` + lọc xóa mềm như thường.
- Recap tiến độ gộp NGAY trong SQL (group-by, không N+1): YCMH có số dòng theo từng bước
  mua (nhãn từ `PR_LINE_STATUS`: chưa tạo đơn / đã đặt / đã nhận...) + tổng SL yêu cầu /
  đã đặt / đã nhận; YCKS có số dòng đã khảo sát xong + đã sinh YCMH. Muốn xem sâu một
  phiếu -> chuỗi tiếp sang T27.
- TOOL_GUIDE kèm luật cho câu hỏi chung chung "hôm nay tôi có việc gì": việc nằm ở nhiều
  nhánh (T18 văn bản chờ ký, T28 thu mua chờ duyệt, T19/T29 phiếu mình trình) - model phải
  nêu SỐ LƯỢNG theo nhánh trước rồi hỏi người dùng muốn xem nhánh nào, không đổ nguyên
  mọi danh sách.

---

Nay bộ tool có **30 cái** (T1-T30): T1-T13 loại A tra cứu thu mua, T14-T19 văn bản + phê
duyệt, T20-T22 soạn nháp, T23-T24 + T30 tiện ích (xuất Word / tra HDSD / xuất Excel),
T25-T26 công nợ + YCTT, T27-T29 trợ lý cho quản lý và người trình phiếu (recap chứng từ +
phiếu chờ duyệt + phiếu của tôi).

---

## Ghi chú mở rộng (để sau, chưa đưa vào giai đoạn đầu)

- Tồn kho (`inventory`) - cùng khuôn: một tool read-only bọc service có sẵn, gác `require` +
  `apply_scope`. (Công nợ `payable` đã lên sóng thành T25/T26 ngày 27/08/2026.)
- Nếu tool nào truy vấn quá nặng: tối ưu bằng bảng tổng hợp / cache, KHÔNG vector hóa
  (xem tài liệu 01 mục 2).

---

## Việc cần chốt (đã chốt trong lúc code - giữ lại làm vết)

- Danh sách giai đoạn đầu chốt ở 30 tool như trên; thêm tool mới thì cập nhật tài liệu này
  và bảng quyền ở `04-bao-mat-va-van-hanh.md` mục 5.
- Quy đổi đơn vị: KHÔNG tự quy đổi - kết quả trả nguyên đơn vị lưu trong lịch sử mua, phần
  diễn giải nêu rõ giả định.
- Giới hạn số dòng: mỗi tool có mặc định riêng (20-50) và trần cứng ép bằng `_clamp` trong
  code - tham số `limit` vượt trần bị cắt xuống, không tin giá trị model gửi.
