# Danh sách API / tool cho bot (loại A - dữ liệu có cấu trúc)

Phiên bản: 12/09/2026 (bản đầu 25/08/2026). Trạng thái: **ĐÃ CODE 36 tool** (T1-T34 + T35 +
T45) — mã nguồn ở `backend/app/modules/assistant/tools/`. T1-T34 đang chạy dev và prod; **T35
`my_leave_summary` và T45 `employee_lookup` mới xong local 12/09 (bao-CR-386), chưa deploy**.
**Còn nợ 12 tool** (T36-T44, T46-T48) cho các phân hệ mọc sau 28/08 — xem mục *Đợt 3* gần
cuối tài liệu.
Liên quan: kiến trúc ở `01-kien-truc-tro-ly-ai.md`; bảo mật và vận hành thực tế ở
`04-bao-mat-va-van-hanh.md`.

⚠️ **Tool chỉ là một nửa.** Nửa kia là **gói tri thức** ở `backend/app/modules/assistant/packs/`
— nội dung nhồi thẳng vào `system` mỗi lượt hỏi, không qua RAG. Có tool mà không có gói thì
model biết gọi nhưng không biết khi nào nên gọi. Gói mới nhất cập nhật 08/09/2026 và hiện
**chưa có mảng nào** cho Diễn đàn · Phiếu hỗ trợ · Kho · Đơn hàng nhập khẩu; riêng gói Thu mua
(`10-quy-trinh-thu-mua.md`) vẫn tự ghi là **bản MẪU**, chưa thay bằng tài liệu thật của công ty.
Ngoài tool, chat còn nhận **tệp đính kèm** (ảnh/PDF, CR-204) — không phải tool nên không
liệt kê ở đây, xem tài liệu 04 mục 7.

Đây là danh sách "công cụ" (tool) mà Claude được phép gọi khi câu hỏi thuộc loại A. Mỗi tool
ánh xạ đúng một hàm service. Bot KHÔNG sinh SQL, chỉ chọn tool + điền tham số theo schema.

Quy tắc chung cho MỌI tool (chi tiết ở tài liệu 01 mục 4.2):
- Chạy DƯỚI danh tính người hỏi (JWT của họ). Bot không có tài khoản riêng.
- Gác hai lớp: `require(entity, action)` + `apply_scope(...)`. Cột "Quyền" là entity + action.
- Read-only giai đoạn đầu (action luôn là `read`). Ngoại lệ DUY NHẤT: T31
  `propose_document_update` thuộc tầng GHI có xác nhận (xem "Đợt CR-218" cuối tài liệu) —
  tool vẫn chỉ trả đề xuất, việc ghi nằm ở endpoint `confirm-update` sau khi người dùng bấm.
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

### T22. draft_leave_request - Soạn nháp đơn nghỉ phép [SỬA 12/09/2026, bao-CR-387]
- Quyền: `leave_request` + `create`.
- ⚠️ **Trỏ vào phân hệ Nhân sự ▸ Nghỉ phép, KHÔNG phải Văn thư.** Bản đầu (CR-159) ra đời
  trước phân hệ Nghỉ phép nên soạn một **văn bản «Giấy nghỉ phép»** ở Văn thư, gác bằng
  `document.create` và dẫn người dùng sang form tạo văn bản. Từ CR-259 giấy GNP do
  `leave/approval_bridge.py` **tự sinh sau khi đơn được duyệt** (QĐ-NP5), nên đường cũ tạo
  ra một tờ giấy không gắn với quỹ phép nào. Đừng nối lại.
- Tham số: `from_date` · `to_date` · `reason` (bắt buộc), `leave_type` (**mã** loại nghỉ,
  enum gắn từ danh mục thật lúc chạy), `from_session`/`to_session`
  (`full|morning|afternoon|hourly`), `from_time`/`to_time` (`HH:MM`, chỉ khi nghỉ theo giờ),
  `days`, `contact_phone`.
- Đầu ra: `draft` mang hình dạng form đơn nghỉ phép (`kind: "leave_request"`, `lines`,
  buổi là **SMALLINT**) + `total_days` · `remaining_days` · `warnings` · `reminder`.
- ⚠️ Số ngày tính qua **`workday_service.count_leave_days`/`count_hourly_days`** — nơi duy
  nhất của công thức đó. Bản cũ gọi `suggested_days()` của giấy GNP (đếm cả cuối tuần) nên
  cùng một tờ đơn ra hai con số khác nhau.
- ⚠️ `draft` **cố ý không có `employee_id`**: form mặc định người nghỉ là chính người lập
  đơn. Để trợ lý điền ô đó là mở đường nộp đơn **hộ người khác** qua chat.
- `warnings` gom trước ba chốt backend sẽ chặn lúc lưu: trùng đơn cũ (`HOLDING_STATUSES`) ·
  vượt `max_days_per_request` · không đủ quỹ. Chỉ cảnh báo, **không** tự sửa.
- Quỹ phép đọc bằng `balance_service.remaining()` (chỉ ĐỌC); tuyệt đối không gọi
  `ensure_balance()` — hàm đó **ghi**.

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
  `date_from`/`date_to` (ngày phát sinh), `due_from`/`due_to` (HẠN TRẢ — "cần thanh toán
  tháng này", bao-CR-273), `group_by` (supplier | company — trả tổng hợp nhóm thay vì liệt
  kê, bao-CR-273), `limit` (trần 30).
- Đầu ra: `summary` (tổng nợ / đã trả / còn lại / quá hạn) tính trên TOÀN BỘ kết quả lọc +
  danh sách từng khoản kèm `payable_id` để nối sang T26. Có `group_by` thì thay danh sách
  bằng `groups` (mỗi NCC/công ty một dòng: số khoản + còn nợ + quá hạn, xếp còn-nợ giảm
  dần, trần 30 nhóm nhưng `group_count`/`summary` vẫn tính trên toàn bộ).
- Nguồn: cùng `apply_scope("payable")` + công thức quá hạn với màn Công nợ (`/api/payables`).
- Quyền: `payable` + `read`.

### T26. draft_payment_request - Soạn nháp Yêu cầu thanh toán (YCTT)
- Mục đích: "làm yêu cầu thanh toán cho NCC X" sau khi tra công nợ.
- Tham số: `payable_ids` (từ T25, chính xác nhất) HOẶC `supplier` bắt buộc +
  `company`/`date_from`/`date_to`/`due_from`/`due_to` tùy chọn ("trả các khoản tới hạn
  tháng này" = lọc theo HẠN TRẢ, bao-CR-273); không có cả hai thì tool bắt hỏi lại,
  không gom nợ cả hệ.
- Đầu ra: bản nháp `kind=payment_request` gồm danh sách `payable_ids` hợp lệ + tổng còn lại
  theo NCC. Giao diện hiện nút "Tạo đề nghị thanh toán" mở form tạo YCTT qua đường
  `?payables=<ids>` của màn Công nợ - form TỰ NẠP LẠI các khoản dưới quyền người đăng nhập
  (backend kiểm lại phạm vi lần nữa — từ bao-CR-274 endpoint tạo phiếu cũng chặn 403
  payable_id ngoài phạm vi), người dùng rà rồi tự bấm Lưu; khi lưu hệ thống tự tách mỗi
  cặp NCC + CÔNG TY nhận hóa đơn một phiếu (bao-CR-274) — nhiều công ty thì bản nháp kèm
  `draft.companies` và reminder báo trước việc tách.
- Luật cứng: CHỈ chọn khoản `remaining > 0` - khoản đã tất toán bị loại và báo trong
  `skipped_ids` (bài học lỗi phân bổ thanh toán, fix `82ce6ad`); trần 50 khoản/bản nháp.
- Quyền: `payment_request` + `create` VÀ `payable` + `read` - thiếu một trong hai là denied
  (bản nháp lộ số nợ + tên NCC nên không được vòng qua hàng rào của T25).

**Nâng cấp bao-CR-273 (03/09/2026) — ĐÃ LÀM**, chi tiết đã gộp vào mô tả T25/T26 ở trên:
① lọc hạn trả `due_from`/`due_to`; ② tổng hợp nhóm `group_by=supplier|company`;
③ nhắc khi nợ trải nhiều công ty — phần ③ được **bao-CR-274** (cùng ngày, theo yêu cầu
khách) nâng tiếp: backend tách phiếu theo cả công ty nhận hóa đơn + gác phạm vi khoản nợ
ngay ở endpoint tạo phiếu, reminder đổi từ "hỏi có tách không" thành "báo trước sẽ tách".

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

## Nhóm 11 - Đợt CR-218: sửa phiếu có xác nhận + phiếu hỗ trợ (`update_tool.py` / `ticket_tool.py`, thêm 28/08/2026)

Tool GHI đầu tiên của trợ lý (T31) + ba tool đọc/nháp đi kèm. Thiết kế gốc và điều kiện
an toàn xem mục "Đợt CR-218" cuối tài liệu.

### T31. propose_document_update - Đề xuất sửa chứng từ (tầng GHI có xác nhận)
- Mục đích: "sửa mục đích YCMH này thành...", "đổi ngày cần hàng phiếu X", "sửa nội dung
  bản in YCTT". Tool KHÔNG ghi gì - chỉ trả BẢN ĐỀ XUẤT (cũ -> mới) để FE dựng thẻ so
  sánh + nút Xác nhận / Hủy; người dùng bấm Xác nhận thì FE mới gọi
  `POST /api/assistant/confirm-update`.
- Tham số: `entity` (purchase_request | survey_request | payment_request) + `code` hoặc
  `id` + `changes` (map trường -> giá trị mới).
- Whitelist trường đợt 1 (CHỈ đầu phiếu, chưa đụng dòng hàng): YCMH `purpose` /
  `need_date` / `note`; YCBG `purpose` / `note`; YCTT `print_content` / `print_line_desc`
  / `print_transfer` (ánh xạ vào `print_texts`, tái dùng khe PATCH CR-149 nên
  submitted/approved vẫn sửa được đúng luật form). Trường ngoài whitelist -> error kèm
  danh sách hợp lệ; giá trị mới trùng giá trị cũ bị loại khỏi đề xuất.
- Đề xuất kèm `confirm_token` (Fernet, khóa dẫn xuất từ `JWT_SECRET`): gắn user + entity +
  id phiếu + đúng map thay đổi, hạn dùng 15 phút. Lúc xác nhận backend KIỂM LẠI TOÀN BỘ
  (không tin đề xuất cũ): token đúng chủ (sai chủ = 403) -> `require(entity, write)` +
  `apply_scope(action="write")` -> trạng thái còn sửa được -> whitelist lần nữa -> ghi qua
  đúng service của form (update_pr / update_sr / update_request) nên validation + audit
  ăn nguyên.
- Quyền: `entity` + `write` - kiểm CẢ lúc đề xuất lẫn lúc xác nhận.

### T32. payment_request_read - Đọc chi tiết một YCTT theo mã
- Mục đích: "phiếu YCTT-xxx ghi gì", và hiện giá trị cũ trước khi nhờ sửa bản in qua T31
  (trước đây chỉ có T25 tra công nợ, không đọc được phiếu).
- Tham số: `code` (tool tự upper) hoặc `id`.
- Đầu ra: đầu phiếu (trạng thái + nhãn, NCC, hình thức thanh toán trả NHÃN tiếng Việt,
  tổng tiền, `print_texts` đã parse, `url`) + tối đa 30 dòng (mã ĐMH, số hóa đơn, ngày
  hóa đơn, số tiền).
- Quyền: `payment_request` + `read`, lấy phiếu qua `apply_scope` (ngoài phạm vi =
  "không tìm thấy").

### T33. ticket_create - Soạn nháp phiếu hỗ trợ
- Mục đích: "báo lỗi màn X", "tạo phiếu hỗ trợ xin cấp quyền". Theo khuôn draft_tool:
  KHÔNG ghi DB, trả bản nháp `kind="ticket"` để FE mở dialog tạo phiếu điền sẵn, người
  dùng tự bấm gửi.
- Tham số: `subject` + `body` (bắt buộc, thiếu là error mềm), `department` (nhóm tiếp
  nhận - ngoài danh mục form thì về mặc định "Hệ thống / CNTT"), `priority` (ngoài bộ mã
  thì về `normal`). Ảnh chụp màn hình đi theo đính kèm CR-204, không qua tool.
- Quyền: `ticket` + `create`.

### T34. my_tickets - Phiếu hỗ trợ của chính người hỏi
- Mục đích: "phiếu hỗ trợ của tôi tới đâu rồi", nền cho việc bổ sung/đóng ticket đợt sau.
- Tham số: `status` (lọc, giá trị lạ thì bỏ lọc) + `limit` (mặc định 10, trần 30).
- Phạm vi "CỦA TÔI" theo CẢ hai cột như T29: `created_by` = tài khoản HOẶC
  `requester_id` = ID nhân sự (phiếu người khác tạo HỘ vẫn thấy) - kể cả khi scope là
  `all` vẫn chỉ trả phiếu mình đứng tên. Mới nhất trước, mỗi phiếu kèm nhãn trạng thái +
  `url`.
- Quyền: `ticket` + `read`.

---

Nay bộ tool có **36 cái**: T1-T13 loại A tra cứu thu mua, T14-T19 văn bản + phê
duyệt, T20-T22 soạn nháp, T23-T24 + T30 tiện ích (xuất Word / tra HDSD / xuất Excel),
T25-T26 công nợ + YCTT, T27-T29 trợ lý cho quản lý và người trình phiếu (recap chứng từ +
phiếu chờ duyệt + phiếu của tôi), T31-T34 đợt CR-218 (sửa phiếu có xác nhận + đọc YCTT +
phiếu hỗ trợ), và hai tool đầu tiên của Đợt 3 — **T35** quỹ phép + đơn nghỉ của chính mình,
**T45** danh bạ nhân sự (bao-CR-386, 12/09/2026).

---

## Đợt CR-218 — hỏi-trước-khi-tạo + tầng GHI có xác nhận (ĐÃ CODE đợt 1 ngày 28/08/2026)

Chốt với khách qua chat: trợ lý không chỉ tra cứu mà hỗ trợ TẠO và SỬA phiếu, với hai khuôn
dùng lại cho mọi loại chứng từ. Đợt 1 đã code xong (BE + FE + test); phần "đợt sau" bên
dưới giữ nguyên làm danh sách chờ.

**Khuôn 1 — hỏi-trước-khi-tạo (nâng cấp các tool soạn nháp T20–T22):** [ĐÃ CODE]
- Schema tool soạn nháp thêm trường còn thiếu: YCBG thêm **ngày yêu cầu kết quả**
  (`result_due_date` theo dòng), YCMH thêm **kho nhận** (`warehouse` theo dòng); form FE
  đọc args điền sẵn như cũ. Riêng "hạn chi YCTT": bản nháp YCTT dựng từ khoản công nợ chứ
  không có trường hạn chi ở form, nên KHÔNG làm — ghi nhận là giới hạn đã biết.
- TOOL_GUIDE thêm checklist: trước khi chốt bản nháp, hỏi gộp MỘT LƯỢT các trường quan
  trọng còn trống; người dùng nói chưa cần thì bỏ qua và tạo bình thường; cái gì họ đã nói
  rồi thì CẤM hỏi lại. Các trường này vốn không bắt buộc lúc lưu nháp (chỉ chặn lúc gửi
  duyệt) nên hỏi trước chỉ là đỡ một lần quay lại sửa phiếu.

**Khuôn 2 — sửa/ghi qua khung xác nhận (tool GHI đầu tiên, phá lệ read-only CÓ KIỂM SOÁT):**
[ĐÃ CODE — thành T31, chi tiết ở Nhóm 11]
- Luồng hai bước: tool `propose_document_update` chỉ trả **BẢN ĐỀ XUẤT** (loại phiếu, mã,
  danh sách thay đổi cũ → mới); FE hiện thẻ so sánh + nút **Xác nhận / Hủy**; người dùng
  bấm Xác nhận thì FE mới gọi `POST /api/assistant/confirm-update` — model không bao giờ
  tự ghi. Đề xuất gắn user + có hạn dùng ngắn (token Fernet 15 phút, sai chủ = 403); lúc
  bấm xác nhận backend KIỂM LẠI TOÀN BỘ (không tin đề xuất cũ).
- Điều kiện ghi thống nhất, chốt ở backend: `require(entity, write)` + `apply_scope` (nên
  "chính chủ phiếu nháp" tự rơi ra từ scope `own`, người có quyền rộng hơn sửa được theo
  đúng quyền form của họ) + **trạng thái còn sửa được theo luật sẵn có của từng loại phiếu**
  + **whitelist trường theo từng handler**. Ghi đi qua đúng service của form nên validation
  + audit ăn nguyên.
- Mỗi loại phiếu một handler. Đợt 1 ĐÃ CODE: **YCMH** (mục đích, ngày cần hàng, ghi chú)
  + **YCBG** (mục đích, ghi chú) — CHƯA đụng dòng hàng — + **YCTT nội dung bản in** (tái
  dùng đúng khe PATCH `print_texts` của CR-149 — whitelist có sẵn ở service, nên
  submitted/approved vẫn sửa được đúng luật form). Đợt sau: ĐMH / khảo sát / nhận hàng khi
  còn nháp (theo đúng quyền write của người hỏi), nghỉ phép, bổ sung/đóng ticket của mình.

**Tool mới kèm đợt này:** [ĐÃ CODE — thành T32-T34, chi tiết ở Nhóm 11]
- `ticket_create` (T33) — soạn nháp phiếu hỗ trợ qua chat theo khuôn đề xuất + nút (hỏi
  phân loại, mức độ, mô tả; nhận ảnh chụp màn hình qua đính kèm CR-204).
- `my_tickets` (T34) — nền tra cứu cho việc bổ sung/đóng ticket đợt sau.
- `payment_request_read` (T32) — đọc chi tiết một YCTT theo mã (trước chỉ có
  `payable_lookup` tra công nợ, chưa đọc được phiếu YCTT để hiện giá trị cũ trước khi sửa).

Việc kèm khi code (ĐÃ LÀM 28/08/2026): bảng quyền `04-bao-mat-va-van-hanh.md` mục 5 đã
thêm hàng cho T31-T34 + endpoint confirm-update; danh sách trên đã đánh số T31-T34
(Nhóm 11). Test: `test/backend/test_assistant_update_tool.py` (12 case, phủ đủ sai chủ
token / token hết hạn / ngoài scope ghi / sai trạng thái / trường ngoài whitelist / token
giả) + `test_assistant_ticket_tool.py` + phần T32 trong `test_assistant_payable_tool.py`;
FE có test thẻ so sánh cũ/mới + parse bản nháp phiếu hỗ trợ.

---

## Đợt 3 - tool cho các phân hệ CHƯA có (ghi nợ 12/09/2026 — ĐÃ LÀM T35 + T45)

Từ 28/08/2026 hệ thống mọc thêm nhiều phân hệ nhưng trợ lý **không được cấp tool nào cho
chúng**, nên nó không trả lời nổi những câu người dùng hỏi hằng ngày ("tôi còn mấy ngày
phép", "phòng họp chiều mai còn trống không", "việc nào tới hạn tuần này"). Mục này ghi nợ
danh sách đó. Chưa cấp số CR - khi nào làm thì re-grep `change-log.md` + `change-log-bao.md`
lấy số kế tiếp (luật `<tên>-CR-<số>-<slug>`).

Thứ tự đề nghị làm, theo mức người dùng thật đang hỏi mà bot chịu thua. **Đợt 12/09/2026
(bao-CR-386) đã lấy T35 và T45** — khách gọi tên đúng hai cái đó, nên T36 vẫn nằm nguyên
trong hàng chờ chứ không đi kèm T35:

| Ưu tiên | Nhóm | Tool | Vì sao xếp ở đó |
|---|---|---|---|
| 1 | Nghỉ phép | ~~T35~~ **xong 12/09**, còn T36 | Bot **soạn được** đơn nghỉ (T22) nhưng không biết người hỏi còn bao nhiêu ngày - soạn xong mới biết không đủ phép |
| 2 | Công việc | T43, T44 | Phân hệ dùng hằng ngày, dữ liệu đã có sẵn service |
| 3 | Đặt phòng họp / đặt xe | T39-T42 | Câu hỏi ngắn, tra nhanh, đúng thứ người ta lười mở màn hình để xem |
| 4 | Kho và giao nhận | T37, T38 | Đã ghi nợ từ 25/08, chưa ai làm |
| 5 | Diễn đàn | T46, T47 | Đã có đề xuất riêng chốt hướng, chỉ chờ xếp lịch |
| 6 | Hồ sơ nhân sự | ~~T45~~ **xong 12/09** | Rủi ro cao nhất của cả đợt - cách hạ rủi ro là danh sách trắng trường ra, xem nhóm 16 |
| 7 | Đóng dấu | T48 | Ít người dùng, để cuối |

### Bảy luật áp cho MỌI tool của đợt này

Viết trước khi liệt kê tool, vì đây mới là chỗ dễ hỏng - bản thân truy vấn thì nhẹ.

1. **Entity phải có trong `SCOPE_FIELDS`** (`core/scoping.py`). Thiếu khai là `apply_scope`
   trả `false()` chặn sạch và chỉ ghi cảnh báo vào log `app.scoping` - tool im lặng trả rỗng,
   người dùng đọc thành "hệ thống chưa có dữ liệu". Có test canh đủ 44/44, thêm entity mà
   quên khai thì suite đỏ.
2. **Phân hệ mới lưu trạng thái SMALLINT + IntEnum (R2/QĐ-11) - tool phải trả CẢ số LẪN
   nhãn.** Trả số trần thì model tự đoán nghĩa và nói sai; trả nhãn trần thì mất khả năng lọc.
3. **Tool "của tôi" phải lọc theo CẢ HAI cột** như T29/T34 đã làm: `created_by` (ID tài
   khoản) HOẶC `requester_id`/`employee_id`/`assignee_id` (ID **nhân sự**). Hai thứ đó khác
   nhau - lấy nhầm là người được lập hộ không thấy phiếu của chính mình. Và phải ép lọc kể
   cả khi phạm vi người hỏi là `all`.
4. **Con số dẫn xuất KHÔNG được tính lại trong tool.** Gọi đúng hàm mà màn hình đang gọi.
   Ví dụ số phép còn lại chỉ có một nơi tính là `balance_service.remaining()`, số ngày nghỉ
   chỉ ở `workday_service.count_leave_days()`. Chép công thức sang tool là hai nguồn sự thật,
   và cái sai sẽ là cái bot đọc cho người dùng nghe.
5. **Mỗi tool mới phải kèm một mảng trong gói tri thức** (`assistant/packs/`). Có tool mà
   không có gói thì model biết gọi nhưng không biết *khi nào nên gọi* và dùng sai từ khóa
   nghiệp vụ. Ngược lại gói chỉ ghi thứ **nói sai là hỏng dữ liệu thật**, các bước bấm nút
   để ở Help Center.
6. **Cập nhật bảng quyền ở `04-bao-mat-va-van-hanh.md` mục 5** cùng lúc với code, không để
   sau. Bảng đó là thứ duy nhất khách đọc khi hỏi "AI có lòi thông tin vượt quyền không".
7. **Read-only.** Đợt này không tool nào ghi DB. Cần ghi thì đi đường `propose_*` +
   `confirm-update` như T31 - trả đề xuất kèm `confirm_token`, người dùng bấm nút mới ghi.

---

## Nhóm 12 - Nghỉ phép (`leave_tool.py`)

Lỗ này **đã lấp** (12/09/2026): trước đó T22 `draft_leave_request` soạn được đơn nhưng không
tool nào đọc được quỹ phép, người dùng hỏi "tôi còn mấy ngày phép" thì bot chịu. Nay T35 đọc
quỹ, và chính T22 cũng tự cảnh báo khi không đủ phép (bao-CR-387).

### T35. my_leave_summary - Quỹ phép + đơn nghỉ của chính người hỏi [ĐÃ CODE 12/09/2026, bao-CR-386]
- Mục đích: "tôi còn bao nhiêu ngày phép", "đơn nghỉ tuần sau của tôi duyệt chưa".
- Tham số: `year` (mặc định năm hiện tại), `status` (tùy chọn, **số** 1-6 theo
  `LEAVE_REQUEST_STATUS_LABELS`), `limit` (mặc định 10, trần 30 - chỉ kẹp danh sách đơn,
  quỹ phép luôn trả đủ mọi loại).
- Đầu ra: `balances` - mỗi **loại nghỉ** một dòng (tên loại, tổng quỹ, đã dùng, đang giữ
  chỗ, chuyển sang từ năm trước, còn lại) + `requests` - đơn của chính người hỏi kèm số
  trạng thái, nhãn trạng thái, các **dòng loại nghỉ** và `url` + `glossary` giải nghĩa ba
  con số để model khỏi diễn đạt sai.
- ⚠️ Số còn lại đọc từ `LeaveBalance.remaining_days`, KHÔNG tự trừ. Và trả **cột giữ
  chỗ `pending_days` riêng** - gộp vào "đã dùng" thì người dùng tưởng đơn đã duyệt.
- ⚠️ **Một đơn khai nhiều loại nghỉ** (`tab_leave_request_line`, 07/09/2026): `total_days`
  và `leave_type_id` ở đầu đơn là **dẫn xuất**. Tool trả nguyên `lines`, và cố ý KHÔNG trả
  `leave_type_id` đầu đơn - không thì đơn 2 ngày phép năm + 1 ngày không lương hiện thành
  "3 ngày phép năm".
- ⚠️ **Read-only nghĩa là không được gọi `balance_service.ensure_balance()`** - hàm đó vừa
  đọc vừa **cấp phát** một dòng quỹ mới. Loại nghỉ chưa ai cấp quỹ thì trả về với cờ
  `allocated: false` kèm câu giải thích, chứ không tự đẻ dòng và cũng không im lặng bỏ qua
  (bỏ qua thì người hỏi đọc ra "công ty không có loại nghỉ đó").
- ⚠️ **Chỉ lọc `employee_id`, cố ý KHÔNG lọc `created_by`** - khác khuôn "my X" của
  `my_tickets`/`my_procurement_requests` ở luật 3 bên trên. Ở phân hệ này `created_by`
  nghĩa là "tôi lập hộ NGƯỜI KHÁC", tức dữ liệu nghỉ phép của người ta; gộp vào là vừa trả
  lời sai câu hỏi vừa phát dữ liệu người khác qua một tool không đi qua `apply_scope`.
  Hành chính muốn xem đơn mình lập hộ thì vào màn Nghỉ phép.
- Quyền: `leave_request.read` - cùng lý lẽ với `GET /api/leave-requests/tools/my-balance`
  (quỹ của CHÍNH người hỏi, ai nộp được đơn thì phải thấy được số còn lại; bắt thêm khóa
  `leave_balance` là chắc chắn có người quên cấp rồi con số hiện 0 vĩnh viễn).
- Tài khoản chưa gắn hồ sơ nhân sự (`employee_id = 0`) nhận **lỗi mềm bằng lời**, không trả
  quỹ của "nhân sự số 0".
- Test: `test/backend/test_assistant_leave_tool.py` (6 ca).

### T36. team_leave_calendar - Ai nghỉ trong khoảng ngày [CHƯA CODE]
- Mục đích: "tuần sau phòng tôi ai nghỉ", "ngày 20 có ai vắng không" - câu của quản lý khi
  xếp việc.
- Tham số: `date_from`/`date_to` (bắt buộc, trần 90 ngày), `department_id` (tùy chọn),
  `limit` (trần 50).
- Đầu ra: danh sách (họ tên, phòng ban, loại nghỉ, từ ngày - đến ngày, số ngày, trạng thái).
  Chỉ đơn **đã duyệt** và đơn **đang chờ duyệt**; đơn nháp không tính vì chưa chắc xảy ra.
- Quyền: `leave_request.read` + `apply_scope`. ⚠️ Nhánh `own` của entity này hợp CẢ
  `created_by` LẪN `employee_id` (entity đầu tiên khai cả `owner` lẫn `self`) - dùng đúng
  `apply_scope`, đừng tự viết điều kiện, kẻo lọt đơn của người khác do hành chính lập hộ.
- ⚠️ Đây là tool trả **tên người + ngày vắng mặt** nên phạm vi phải chặt. Người scope `own`
  hỏi tool này chỉ ra chính họ - đúng ý đồ, không phải lỗi.

---

## Nhóm 13 - Kho và giao nhận (`inventory_tool.py`, CHƯA CODE)

Nợ này ghi từ 25/08/2026, chưa ai làm.

### T37. inventory_lookup - Tra tồn kho một mã hàng / một kho
- Mục đích: "mã X còn bao nhiêu", "kho A đang giữ những gì".
- Tham số: `product_code` HOẶC `warehouse` (ít nhất một, không cho quét cả hệ),
  `limit` (trần 50).
- Đầu ra: từng dòng (mã hàng, tên, kho, số lượng, đơn vị tính) + `summary` tổng theo mã.
- ⚠️ Nối bằng **chuỗi `product_code`** chứ không bằng khóa - `tab_product` là bảng variant,
  không có FK nào trỏ vào nó (D-025). Gõ sai mã thì trả danh sách mã gần đúng chứ đừng trả rỗng.
- Quyền: `inventory.read` + `apply_scope`.

### T38. pending_deliveries - Hàng đã đặt mà chưa về
- Mục đích: "đơn nào trễ giao", "tuần này hàng gì về" - câu hỏi Thu mua hỏi mỗi sáng.
- Tham số: `overdue_only` (mặc định false), `date_from`/`date_to` (theo ngày giao dự kiến),
  `supplier` (tùy chọn), `limit` (trần 50).
- Đầu ra: dòng ĐMH còn thiếu hàng (mã ĐMH, NCC, mã hàng, SL đặt / đã nhận / còn lại, ngày
  giao dự kiến, số ngày trễ) + `url` mở chi tiết đơn.
- ⚠️ Tái dùng đúng công thức của màn *Tiến độ mua hàng* (`purchase_progress`), đừng cộng lại
  từ `tab_po_delivery`.
- Quyền: `purchase_order.read` + `apply_scope`; thiếu `supplier.read` thì ẩn cột NCC kèm ghi
  chú, giống luật đã áp cho T9/T12.

---

## Nhóm 14 - Đặt phòng họp và đặt xe (`booking_tool.py`, CHƯA CODE)

Hai phân hệ cùng khuôn đặt chỗ theo khung giờ nên gom một tệp.

### T39. meeting_room_availability - Phòng họp còn trống
- Mục đích: "chiều mai 2h có phòng nào trống", "phòng A tuần này ai đặt".
- Tham số: `date` (bắt buộc) hoặc `date_from`/`date_to` (trần 14 ngày), `room_id` (tùy chọn),
  `capacity_min` (tùy chọn).
- Đầu ra: mỗi phòng một dòng kèm các **khoảng đã kín** trong ngày - để model tự diễn giải ra
  khoảng trống, đừng bắt API tính hộ.
- Quyền: `meeting_room.read`.

### T40. draft_room_booking - Soạn nháp phiếu đặt phòng họp
- Mục đích: nối tiếp T39 - "đặt giúp tôi phòng A 2-3h chiều mai".
- Đầu ra: bản nháp `kind=room_booking`, giao diện mở form điền sẵn; **người dùng tự bấm Lưu**.
- ⚠️ Kiểm trùng lịch ở tool chỉ là cảnh báo sớm cho dễ chịu - chốt thật vẫn nằm ở service
  lúc lưu, vì giữa lúc soạn nháp và lúc bấm Lưu có người khác đặt mất.
- Quyền: `meeting_room.create` (không có quyền đặt thì không soạn hộ, giống T20/T21).

### T41. vehicle_booking_lookup - Tra lịch xe / chuyến của chính mình
- Mục đích: "xe nào rảnh thứ 5", "chuyến đi Cần Thơ của tôi duyệt chưa".
- Tham số: `date_from`/`date_to` (trần 30 ngày), `mine_only` (mặc định true), `vehicle_id`.
- Đầu ra: chuyến (xe, tài xế, điểm đi - điểm đến, giờ, trạng thái + nhãn, `url`).
- Quyền: `vehicle_booking.read` + `apply_scope`; `mine_only=true` thì ép lọc theo luật 3.

### T42. draft_vehicle_booking - Soạn nháp phiếu đặt xe
- Cùng khuôn T40. Quyền: `vehicle_booking.create`.

---

## Nhóm 15 - Công việc (`work_tool.py`, CHƯA CODE)

Phân hệ Công việc (clone Lark, CR-216) đã có gói tri thức `30-du-an-cong-viec.md` nhưng
không có tool nào - tức bot **giải thích được quy trình mà không đọc được việc thật**.

### T43. my_tasks - Việc của chính người hỏi
- Mục đích: "tôi đang có việc gì", "việc nào tới hạn tuần này", "việc nào quá hạn".
- Tham số: `status` (tùy chọn), `due_before` (tùy chọn), `overdue_only`, `limit` (trần 30).
- Đầu ra: việc (tiêu đề, dự án/bảng, trạng thái + nhãn, hạn, số ngày còn lại hoặc đã trễ,
  `url`), xếp hạn gần nhất trước.
- ⚠️ Cột người phụ trách là **ID nhân sự**, không phải ID tài khoản (luật 3).
- Quyền: `work.read` (đối chiếu tên khóa thật lúc code) + ép lọc chính chủ.

### T44. task_search - Tìm việc theo từ khóa / dự án
- Mục đích: "có ai đang làm việc gì về nhà máy chưa", "việc X tới đâu rồi".
- Tham số: `query` (tùy chọn), `project_id` (tùy chọn), `assignee_id`, `status`, `limit`.
- Đầu ra: danh sách GỌN + `url`; nội dung dài không trả ở đây.
- Quyền: `work.read` + `apply_scope` - đây là tool đọc việc **của người khác** nên phạm vi
  phải đi qua `apply_scope`, không được ép lọc lỏng.

---

## Nhóm 16 - Hồ sơ nhân sự (`employee_tool.py`)

⚠️ **Nhóm rủi ro cao nhất của cả đợt.** Đọc kỹ trước khi gõ dòng đầu tiên.

### T45. employee_lookup - Tra thông tin nhân sự [ĐÃ CODE 12/09/2026, bao-CR-386]
- Mục đích: "số điện thoại của anh X", "anh X thuộc phòng nào", "phòng kế toán có ai",
  "ai là quản lý trực tiếp của tôi".
- Tham số: `query` (tên / mã NV / email / điện thoại / chức vụ), `department_id`,
  `active_only` (mặc định `true`), `limit` (mặc định 10, trần 30).
- Đầu ra: **đúng 12 trường danh bạ** - id, mã NV, họ tên, chức vụ, cấp bậc, phòng ban, công
  ty, email và điện thoại công việc, quản lý trực tiếp, nhãn tình trạng, còn làm việc hay
  không.
- ⚠️ **Chốt đã chọn: DANH SÁCH TRẮNG, không phải che sau.** `_OUT_FIELDS` liệt kê thẳng 12
  trường được ra; dựng kết quả theo danh sách đó chứ không `model_dump()` cả hồ sơ rồi xóa
  bớt. Khuôn ngược (chép hết rồi xóa) nghĩa là thêm một cột ở `model.py` là nó tự lọt ra
  trợ lý AI, im lặng. Vì danh sách trắng đã loại sạch 15 trường nhạy cảm nên hôm nay tool
  **không cần** `employee_sensitive.read`; vẫn chạy thêm một lượt `sensitive.mask_many` làm
  **chốt dự phòng** cho ngày có người thêm trường vào đây mà quên rằng trợ lý AI cũng là một
  đường ra dữ liệu (đúng bài học ghi ở đầu `sensitive.py`).
- ⚠️ Trước tool này trợ lý mới chỉ đọc **5 trường** của chính người hỏi (`service.py`
  `_caller_context`) và `full_name` người duyệt. **T45 phá vỡ điều đó** - nó là tool đầu
  tiên đọc hồ sơ NGƯỜI KHÁC, nên `apply_scope` ở đây là lớp chặn thật chứ không phải nghi
  thức: người khai phạm vi phòng ban chỉ thấy phòng mình.
- ⚠️ `Employee.avatar` là `@property` chứ không phải cột - đưa vào `with_entities` là
  `ArgumentError` lúc chạy. Tool này không trả ảnh.
- ⚠️ `department_id = 0` là **giá trị thật** (chưa gắn phòng ban), không phải "tất cả" -
  "tất cả" là không truyền tham số.
- Nạp kèm 3 quan hệ bằng `joinedload` (phòng ban · công ty · quản lý trực tiếp): ba trường
  đó là property đọc qua quan hệ, không nạp trước thì mỗi dòng thêm 3 truy vấn.
- Mô tả tool dặn model **nói rõ "rỗng có thể là ngoài phạm vi"**, đừng khẳng định công ty
  không có người đó; và dặn thẳng: ai hỏi ngày sinh / CCCD / địa chỉ nhà / ngân hàng / lương
  thì trả lời là phải vào màn Hồ sơ nhân sự.
- Quyền: `employee.read` + `apply_scope`.
- Test: `test/backend/test_assistant_employee_tool.py` (6 ca, trong đó một ca khẳng định
  **theo tên trường** rằng không một trường nhạy cảm nào lọt ra).

---

## Nhóm 17 - Diễn đàn (`forum_tool.py`, CHƯA CODE)

### T46. forum_search · T47. forum_post_read
Đã có đề xuất chốt hướng đầy đủ ở **`doc/erp/dien-dan/03-de-xuat-ai-doc-dien-dan.md`**
(03/09/2026) - tham số, ranh giới, và luật "bài diễn đàn KHÔNG phải nguồn tri thức ngang
tài liệu, phải rào nguồn khi trích". Không chép lại ở đây; chỉ cấp số T46/T47 để danh sách
tool liền mạch. Việc backend mới duy nhất: mở rộng search sang **nội dung bình luận**.

---

## Nhóm 18 - Văn thư: đóng dấu (`seal_tool.py`, CHƯA CODE)

### T48. my_seal_requests - Phiếu xin đóng dấu của chính người hỏi
- Mục đích: "phiếu đóng dấu của tôi duyệt chưa", "văn thư nhận chưa".
- Tham số: `status` (tùy chọn), `limit` (mặc định 10, trần 30).
- Đầu ra: phiếu (số, loại con dấu, nội dung tóm tắt, trạng thái + nhãn, `url`).
- Quyền: `seal_request.read` + ép lọc chính chủ theo luật 3.

---

## Chưa xếp lịch, chưa cấp số

- **Điểm cà phê** (`coffee_point`) - chờ POS365 chạy thật rồi mới biết câu hỏi nào đáng hỏi.
- **Nhật ký import/export** (`import_tool`, `export_log`) - việc của quản trị, không phải
  câu hỏi nghiệp vụ; mở cho model là mở thêm bề mặt mà không ai cần.
- **Thông báo / cảnh báo** (`notification`, `alert`, `push`) - trùng việc với chuông trên
  giao diện.
- **Quản trị** (`role`, `user`, `audit`, `login_session`, `backup`) - **cố ý không mở**.
  Trợ lý không được là một đường vòng vào phân quyền.

---

## Ghi chú mở rộng (để sau, chưa đưa vào giai đoạn đầu)

- Nếu tool nào truy vấn quá nặng: tối ưu bằng bảng tổng hợp / cache, KHÔNG vector hóa
  (xem tài liệu 01 mục 2).

---

## Việc cần chốt (đã chốt trong lúc code - giữ lại làm vết)

- Danh sách giai đoạn đầu chốt ở 30 tool (nay 34 sau đợt CR-218); thêm tool mới thì cập
  nhật tài liệu này và bảng quyền ở `04-bao-mat-va-van-hanh.md` mục 5.
- Quy đổi đơn vị: KHÔNG tự quy đổi - kết quả trả nguyên đơn vị lưu trong lịch sử mua, phần
  diễn giải nêu rõ giả định.
- Giới hạn số dòng: mỗi tool có mặc định riêng (20-50) và trần cứng ép bằng `_clamp` trong
  code - tham số `limit` vượt trần bị cắt xuống, không tin giá trị model gửi.
