# Trợ lý AI — Bảo mật và vận hành (bản ghi nhận hiện trạng)

- Ngày lập: 27/08/2026 — cập nhật 28/08/2026 (bổ sung mục 7: đính kèm chat CR-204 + xuất Excel CR-205)
- Trạng thái: **ĐÃ CODE và đang chạy trên môi trường dev** (deverp.degoholding.vn), nhánh `erp-v2`
- Đối tượng đọc: Ban điều hành / cấp quản lý cần đánh giá rủi ro bảo mật, và người kỹ thuật tiếp quản
- Quan hệ với các tài liệu khác: tài liệu `01-kien-truc-tro-ly-ai.md` và `02-danh-sach-api-tool.md`
  là bản **thiết kế** (đầu trang còn ghi "chưa code" — dòng đó đã cũ, phần loại A trong đó nay đã
  code xong). Tài liệu 04 này ghi nhận **những gì thực tế đang chạy trong mã nguồn**, đối chiếu
  trực tiếp với code chứ không chép lại thiết kế.

---

## 1. Câu trả lời ngắn cho mối lo "AI lòi thông tin vượt quyền"

Mối lo được nêu: *"Nhân viên không có quyền xem kho / tồn kho, hoặc không có quyền xem nhà cung
cấp, nhưng hỏi AI thì AI trả ra số tồn kho hoặc thông tin nhà cung cấp."*

Trả lời theo đúng hiện trạng mã nguồn:

1. **AI không nối thẳng vào database.** Model ngôn ngữ (Claude / Gemini) không có kết nối SQL,
   không đọc được bảng nào cả. Nó chỉ được phép **xin** dữ liệu qua một danh sách tool đóng
   (30 tool, liệt kê ở mục 5) do backend của mình viết và kiểm soát. Tool không có trong danh
   sách thì gọi cũng bị từ chối ngay ở backend (`run_tool` kiểm tra allowlist trước khi chạy).

2. **Về tồn kho: hiện KHÔNG tồn tại tool nào đọc tồn kho.** Trong 30 tool không có tool nào
   truy vấn bảng kho / tồn kho. Nghĩa là kể cả model "muốn" trả lời số tồn kho, nó không có
   đường nào lấy được số thật — cùng lắm nó nói "tôi không tra được", hoặc nếu bịa thì là số
   không có nguồn (đã có luật trong system prompt cấm bịa số liệu, và mọi con số đều phải đến
   từ kết quả tool). Tài liệu 02 có ghi tồn kho là **hạng mục mở rộng tương lai** — khi nào làm
   thì tool đó cũng phải qua đúng các tầng kiểm quyền ở mục 4.

3. **Về nhà cung cấp: danh tính NCC bị gác bằng quyền `supplier.read`.** Người hỏi không có
   quyền xem NCC thì:
   - Tool tra cứu NCC (`supplier_search`, `top_suppliers_by_purchase`...) trả về từ chối rõ ràng
     `{"denied": true, "reason": "Bạn không có quyền xem ..."}` — model nhận cái này và nói lại
     "bạn không đủ quyền", thay vì tự chế câu trả lời.
   - Tool tra lịch sử mua hàng (`product_purchase_history`, `recent_purchases`, `purchase_report`)
     vẫn chạy được cho người có quyền xem sản phẩm, nhưng **cột tên/mã NCC bị cắt khỏi kết quả
     ngay ở backend** (biến `see_supplier` trong `catalog.py`) — dữ liệu NCC không hề đi vào
     model, nên model không thể "lỡ miệng" nói ra. Kèm theo một ghi chú trong kết quả:
     *"Ẩn thông tin nhà cung cấp vì người hỏi không có quyền xem NCC."*

4. **Mọi tool chạy dưới danh tính của chính người đang hỏi.** Không có "tài khoản bot" quyền
   cao. Ai hỏi thì tool kiểm quyền của người đó — cùng một câu hỏi, hai người khác quyền nhận
   hai kết quả khác nhau. Đây là điểm mấu chốt: quyền của AI **luôn bằng đúng** quyền của người
   dùng đang ngồi trước màn hình, không hơn.

Điểm 3 và 4 kiểm chứng được ngay trên môi trường dev: đăng nhập một tài khoản không có
`supplier.read`, hỏi "NCC nào bán giấy rẻ nhất" — trợ lý trả lời không đủ quyền; hỏi "lịch sử mua
mã hàng X" — thấy giá và số lượng nhưng không thấy tên NCC.

---

## 2. Trợ lý chạy như thế nào (luồng một câu hỏi)

```
Người dùng gõ câu hỏi trên giao diện (frontend-v2, phân hệ Trợ lý AI)
  │  kèm token đăng nhập JWT như mọi API khác
  ▼
POST /api/assistant/... — controller đòi quyền assistant.read (require("assistant","read"))
  │  và kiểm hạn mức: mỗi người tối đa AI_DAILY_MSG_LIMIT câu/ngày (usage.py)
  ▼
service.ask() dựng system prompt gồm:
  - Gói tri thức nghiệp vụ cố định (thuật ngữ, quy trình thu mua)
  - TOOL_GUIDE: luật dùng tool (không bịa số liệu, chỉ điền giá trị có trong danh mục...)
  - Khối "NGƯỜI HỎI": họ tên, mã NV, chức vụ, phòng ban, công ty của người đang hỏi
    (backend tự tra từ hồ sơ nhân sự — model không được tự đoán các thông tin này)
  ▼
Gửi lên nhà cung cấp model (Claude hoặc Gemini) kèm danh sách 30 tool
  (tin nhắn có thể kèm tệp người dùng tự tải lên - ảnh/PDF, xem mục 7)
  ▼
Model muốn dữ liệu thì phát yêu cầu gọi tool → backend run_tool() thực thi:
  - kiểm allowlist → kiểm quyền người hỏi → kiểm phạm vi dữ liệu → chỉ đọc → ghi audit
  → trả KẾT QUẢ ĐÃ LỌC THEO QUYỀN về cho model
  ▼
Model soạn câu trả lời từ kết quả đã lọc. Nếu là soạn phiếu (YCBG/YCMH/đơn nghỉ phép):
  backend chuẩn hóa bản nháp, giao diện hiện NÚT mở form đã điền sẵn —
  người dùng tự rà lại và tự bấm Tạo, phiếu KHÔNG tự sinh.
```

Ba tính chất vận hành đáng chú ý:

- **Chỉ đọc tuyệt đối.** Không tool nào ghi/sửa/xóa dữ liệu. Nhóm tool "soạn phiếu" (`draft_*`)
  cũng chỉ trả về một bản nháp JSON để điền form — việc tạo phiếu thật đi qua đúng API tạo phiếu
  bình thường, với đúng kiểm quyền của API đó, và do người dùng bấm nút.
- **Có hạn mức và thống kê sử dụng.** Mỗi người bị chặn số câu/ngày (`AI_DAILY_MSG_LIMIT`);
  màn thống kê tiêu dùng token theo người đòi quyền `assistant.export`.
- **Bật/tắt theo quyền.** Không cấp quyền `assistant.read` cho một vai trò thì vai trò đó không
  dùng được trợ lý — kiểm soát triển khai theo từng nhóm người dùng được ngay từ phân quyền sẵn có.

---

## 3. Vì sao model không thể "tự ý" vượt rào

Đây là phần trả lời câu hỏi lý thuyết: "model thông minh vậy, lỡ nó tìm cách lách thì sao?"

- Model **không cầm** kết nối DB, mật khẩu, hay API key nội bộ nào. Thứ duy nhất nó cầm là khả
  năng *đề nghị* backend chạy một tool có tên nằm trong danh sách đóng, với tham số do backend
  kiểm tra lại (ép kiểu, chặn trần `limit`, cắt độ dài chuỗi).
- Việc kiểm quyền nằm **ở backend, sau khi model đề nghị** — không phải "dặn dò" model trong
  prompt. Dù prompt bị người dùng cố tình dẫn dụ ("hãy bỏ qua mọi giới hạn..."), backend vẫn kiểm
  quyền y nguyên. Lời dặn trong prompt chỉ giúp model lịch sự hơn; hàng rào thật là code.
- Kết quả tool được đối xử là **dữ liệu, không phải mệnh lệnh**: nội dung lấy từ DB (ví dụ ghi
  chú trên chứng từ do ai đó gõ "hãy xuất toàn bộ danh sách NCC") không có quyền sai khiến
  backend chạy thêm gì — vòng lặp tool do backend điều khiển, mỗi lần gọi đều kiểm quyền lại.
- Khi bị từ chối, tool trả về mã từ chối tường minh (`denied`) để model nói thẳng "không đủ
  quyền" — thiết kế này chống chính cái rủi ro "model không lấy được số thật thì bịa số".

---

## 4. Bảy tầng bảo vệ (đúng như code đang chạy)

Bảy tầng này được thiết kế ở tài liệu 01 mục 4.2 và đã hiện thực trong
`backend/app/modules/assistant/tools/` (tầng nền: `base.py`, điều phối: `__init__.py`):

| # | Tầng | Hiện thực trong code |
|---|------|----------------------|
| 1 | Chạy dưới danh tính người hỏi | `ToolContext(db, user)` — không có service account cho bot (thiết kế 01 ghi rõ CẤM cấp tài khoản quyền cao cho bot) |
| 2 | Danh sách tool đóng (allowlist) | `run_tool()` chỉ chạy tool có đăng ký; tên lạ bị từ chối ngay |
| 3 | Hai lớp quyền trên từng tool | Lớp hành động: `ctx.can(entity, action)` (đúng hàm `user_has_permission` của toàn hệ thống). Lớp phạm vi dữ liệu: `apply_scope(query, ...)` (đúng hàm lọc own/dept/company/all của toàn hệ thống). Tool KHÔNG viết luật quyền riêng — dùng chung hạ tầng với API màn hình, nên sửa phân quyền một chỗ là cả hai nơi cùng đổi |
| 4 | Chỉ đọc | Không tool nào INSERT/UPDATE/DELETE; nhóm `draft_*` chỉ trả bản nháp |
| 5 | Tham số bị kiểm và chặn trần | Ép kiểu số, `_clamp` trần số dòng, cắt độ dài chuỗi — chống truy vấn quét ồ ạt |
| 6 | Kết quả là dữ liệu, không phải lệnh | Ranh giới chống prompt-injection như mục 3 |
| 7 | Ghi vết (audit) | Mỗi lần gọi tool ghi `record(...)`: ai gọi, tool gì, tham số gì, bao nhiêu dòng trả về, có bị từ chối không — tra lại được khi cần điều tra |

Điểm đáng nói với cấp quản lý ở tầng 3: hệ thống phân quyền hai trục (hành động theo vai trò +
phạm vi dữ liệu theo người dùng) là thứ đã chạy cho toàn bộ màn hình từ trước. Trợ lý AI **không
mở đường mới vào dữ liệu** — nó đi qua đúng cánh cửa cũ, với đúng chìa khóa của người đang hỏi.
Ngoài ra từ B-07/CR-131, entity nào quên khai phạm vi trong `SCOPE_FIELDS` thì mặc định bị
**chặn hết** (`false()`) chứ không rơi về "thấy tất" — lỗi cấu hình nghiêng về phía an toàn.

---

## 5. Bảng quyền của từng tool (30 tool, đối chiếu code 28/08/2026)

Cột "Điều kiện" là quyền của **người đang hỏi**; thiếu thì tool trả `denied` hoặc tự cắt cột.

### Nhóm tra cứu thu mua (`catalog.py`)

| Tool | Việc | Điều kiện |
|------|------|-----------|
| `product_search` | Tìm sản phẩm/vật tư | `product.read` |
| `supplier_search` | Tìm nhà cung cấp | `supplier.read` |
| `contract_list_by_expiry` | Hợp đồng sắp hết hạn | `contract.read` + lọc `apply_scope` theo phạm vi hợp đồng của người hỏi |
| `contract_count_by_status` | Đếm hợp đồng theo trạng thái | như trên |
| `supplier_contracts` | Hợp đồng của một NCC | như trên |
| `product_purchase_history` | Lịch sử mua một mã hàng | `product.read`; **tên/mã NCC chỉ hiện khi có thêm `supplier.read`** |
| `product_best_price` | Giá tốt nhất từng mua | `product.read` VÀ `supplier.read` (bản chất câu trả lời là "NCC nào giá tốt") |
| `suppliers_for_product` | NCC nào từng bán mã hàng | `product.read` VÀ `supplier.read` |
| `recent_purchases` | Các lần mua gần đây | `product.read`; NCC ẩn nếu thiếu `supplier.read` |
| `top_suppliers_by_purchase` | Xếp hạng NCC theo giá trị mua | `supplier.read` |
| `recent_purchase_orders` | Đơn mua hàng gần đây | `purchase_order.read` + `apply_scope` theo phạm vi ĐMH |
| `purchase_report` | Báo cáo mua hàng theo kỳ | `product.read`; số đếm NCC chỉ hiện khi có `supplier.read` |
| `analytics_query` | Thống kê linh hoạt theo chiều | `product.read`; riêng chiều phân tích theo NCC đòi thêm `supplier.read` |

### Nhóm văn bản và phê duyệt (`document_tool.py`, `approval_tool.py`)

| Tool | Việc | Điều kiện |
|------|------|-----------|
| `document_search` | Tìm trong kho văn bản | `document.read` (quét cả kho nên gác quyền phân hệ) |
| `document_read` | Đọc nội dung một văn bản | Kiểm quyền truy cập **từng văn bản** (`access_service.can`); không có quyền thì trả cùng một câu với "không tìm thấy" — không để lộ cả việc văn bản đó tồn tại |
| `my_documents` | Văn bản áp dụng cho chính mình | Chỉ cần đăng nhập (giống màn "áp dụng cho tôi" ai cũng mở được) |
| `approval_flow_lookup` | Xem cấu hình luồng phê duyệt | `approval_flow.read` (đúng quyền của màn cấu hình đó) |
| `my_approval_tasks` | Việc đang chờ CHÍNH MÌNH ký | Tự giới hạn vào người hỏi — không xem hộ được người khác |
| `my_requests_status` | Phiếu do CHÍNH MÌNH trình đang ở bước nào | Tự giới hạn vào người hỏi |

### Nhóm soạn phiếu và tiện ích (`draft_tool.py`, `rag_tool.py`, `export_tool.py`)

| Tool | Việc | Điều kiện |
|------|------|-----------|
| `draft_survey_request` | Soạn nháp Yêu cầu báo giá | `survey_request.create` — không có quyền tạo phiếu thì không soạn hộ |
| `draft_purchase_request` | Soạn nháp Yêu cầu mua hàng | `purchase_request.create` |
| `draft_leave_request` | Soạn nháp đơn nghỉ phép | `document.create` |
| `search_docs` | Tra cứu Hướng dẫn sử dụng (HDSD) | Chỉ cần đăng nhập — **cố ý**, vì kho HDSD vốn mở cho mọi người dùng đã đăng nhập |
| `export_report_file` | Xuất báo cáo dạng văn bản (Word .docx) từ dữ liệu vừa tra | Chỉ đóng gói lại dữ liệu **đã qua lọc quyền** ở tool báo cáo phía trước — không mở thêm đường dữ liệu mới |
| `export_excel_file` | Xuất bảng tính Excel (.xlsx) từ dữ liệu vừa tra — tối đa 5 sheet x 15 cột x 500 dòng (thêm 27/08/2026, CR-205) | Cùng luật với `export_report_file`: chỉ đóng gói dữ liệu **đã qua lọc quyền**, không mở thêm đường dữ liệu mới |

### Nhóm công nợ và Yêu cầu thanh toán (`payable_tool.py`, thêm 27/08/2026)

| Tool | Việc | Điều kiện |
|------|------|-----------|
| `payable_lookup` | Tra công nợ phải trả với NCC (tổng nợ / đã trả / còn lại / quá hạn) | `payable.read` + `apply_scope("payable")` — cùng phạm vi với màn Công nợ |
| `draft_payment_request` | Soạn nháp Yêu cầu thanh toán từ khoản nợ còn phải trả | `payment_request.create` **VÀ** `payable.read` — thiếu một là denied, vì bản nháp lộ số nợ + tên NCC; chỉ chọn khoản `remaining > 0` (chống lặp lỗi phân bổ thanh toán); nút trên giao diện mở form qua `?payables=<ids>`, form **tự nạp lại** khoản nợ dưới quyền người đăng nhập nên backend kiểm phạm vi thêm một lần nữa |

### Nhóm trợ lý cho quản lý (`procurement_doc_tool.py`, thêm 27/08/2026)

| Tool | Việc | Điều kiện |
|------|------|-----------|
| `procurement_doc_read` | Recap một chứng từ thu mua theo mã (ĐMH / YCMH / YCKS): đầu phiếu, dòng hàng, tiến độ giao nhận, công nợ phát sinh | `entity.read` + lấy phiếu qua `apply_scope` (mã đúng nhưng ngoài phạm vi = "không tìm thấy"); thiếu `supplier.read` thì ẩn NCC kèm ghi chú (kể cả NCC hiệu lực của YCMH); khối công nợ của ĐMH chỉ trả khi có thêm `payable.read`; YCKS chỉ **đếm** số phương án mỗi dòng, không trả chi tiết option (bảng đó chứa NCC thuộc cơ chế ẩn); YCMH xóa mềm coi như không tồn tại |
| `pending_procurement_approvals` | Đếm + liệt kê phiếu thu mua `Chờ duyệt` mà chính người hỏi có quyền duyệt (YCBG / khảo sát / YCMH / ĐMH / YCTT) | Từng loại chỉ đếm khi có `entity.approve` + trong `apply_scope` của chính người hỏi; loại thiếu quyền bị bỏ qua kèm ghi chú (hỏi đích danh thì denied); **trợ lý không duyệt hộ** — kết quả chỉ kèm `url` mở màn chi tiết, kèm `reminder` nhắc model điều đó |
| `my_procurement_requests` | Liệt kê YCBG / YCMH do CHÍNH người hỏi đứng tên (mới nhất trước) kèm recap tiến độ mua: số dòng theo bước mua, SL đã đặt / đã nhận (YCMH); số dòng khảo sát xong / đã sinh YCMH (YCKS) | `entity.read` + `apply_scope`, rồi **ép lọc thêm về chính người hỏi** (`created_by` = tài khoản hỏi HOẶC `requester_id` = mã nhân sự của họ) — quản lý scope `all` hỏi "phiếu của tôi" cũng chỉ nhận phiếu mình đứng tên; YCMH xóa mềm bị loại; không đòi quyền duyệt gì; limit mặc định 10/loại, trần 30, cắt bớt thì báo rõ trong `note` |

---

## 6. Các cập nhật gần nhất (commit `ba45326`, 27/08/2026)

Ba cải tiến, đều thuộc nhóm "soạn phiếu", và đều **không nới** hàng rào quyền nào:

1. **Chèn hồ sơ người hỏi vào system prompt (khối NGƯỜI HỎI).** Backend tự tra hồ sơ nhân sự
   (họ tên, mã NV, chức vụ, phòng ban, công ty) của chính người đăng nhập và đưa vào prompt, để
   trợ lý ngừng hỏi lại những thứ hệ thống đã biết, và form soạn phiếu tự điền đúng người/phòng
   ban/công ty. Về bảo mật: mỗi người chỉ thấy **hồ sơ của chính mình**; tài khoản không gắn
   nhân sự thì không chèn gì (không đoán mò). (`service.py`, hàm `_caller_context`)

2. **Bơm danh mục thật vào định nghĩa tool (enum động).** Danh sách phân loại hàng và danh sách
   công ty đang hoạt động được đọc từ DB và gắn vào schema tool mỗi lượt hỏi, để model chỉ điền
   được giá trị có thật trong danh mục thay vì tự chế. Đây là chống sai dữ liệu, không phải lộ
   dữ liệu: hai danh mục này là danh mục dùng chung mọi màn hình. (`draft_tool.py`,
   hàm `inject_catalog_enums`; có test chống lẫn dữ liệu giữa các request)

3. **Hỗ trợ mua cho pháp nhân khác (tham số `company`).** Khi người dùng nói mua cho công ty
   khác công ty mình, trợ lý điền tên công ty; backend đối chiếu với danh mục (tên/tên tắt/mã,
   không phân biệt hoa thường) — khớp thì form đặt đúng pháp nhân và trợ lý nhắc lại cho người
   dùng biết; không khớp thì **giữ mặc định công ty của người hỏi** và đưa danh sách hợp lệ để
   chọn lại. Kèm viết lại phần hướng dẫn để trợ lý hỏi đủ (mặt hàng, số lượng, có mua cho pháp
   nhân khác không) trước khi soạn. (`draft_tool.py`, hàm `_apply_company`)

---

## 7. Đính kèm ảnh / PDF vào chat (CR-204) + xuất Excel (CR-205) — commit `5e90af1`, 27/08/2026

Từ 27/08/2026 người dùng gửi được TỆP kèm câu hỏi (chụp chứng từ giấy, màn hình lỗi, file
PDF quy trình cũ...) để trợ lý đọc và trả lời trực tiếp trên nội dung đó. Đây là đường dữ
liệu ĐI VÀO model do chính người dùng chủ động cung cấp — không phải tool, không đọc gì từ
DB — nên các hàng rào ở đây xoay quanh **loại tệp, kích thước, quyền sở hữu và chi phí token**:

1. **Tải lên qua `POST /api/assistant/uploads`** (mỗi request một tệp), gác bằng đúng quyền
   `assistant.read` + cờ bật trợ lý như mọi endpoint chat. FE theo khuôn *tải trước — gắn
   sau*: tải xong nhận `id`, rồi truyền `attachment_ids` khi gửi tin (kèm dán ảnh Ctrl+V).
2. **Chỉ nhận 4 loại tệp, trần kích thước cứng:** ảnh JPG / PNG / WebP tối đa **5 MB**, PDF
   tối đa **10 MB**. Loại tệp nhận diện theo **magic bytes của nội dung thật**, KHÔNG tin
   content-type trình duyệt gửi — đổi đuôi tệp không lách được. Backend chỉ đọc dư 1 byte
   quá trần lớn nhất để phát hiện "quá to" mà không nuốt nguyên file khổng lồ vào RAM.
3. **Tối đa 3 tệp mỗi tin** (`MAX_FILES_PER_MESSAGE`).
4. **Tệp thuộc về chính chủ.** Bản ghi lưu ở bảng `assistant_message_attachments` (migration
   `c7e2a9f4d1b3`), nội dung lưu storage dưới thư mục `assistant-upload/`. Chỉ người tải lên
   gắn được tệp vào tin của mình và mở xem lại được (`resolve_owned` — sai chủ trả 404,
   không lộ tồn tại). Xem lại qua `GET /api/assistant/uploads/{file_id}`, trả `inline`.
5. **Chặn phình token khi hỏi tiếp:** chỉ `ATTACH_REPLAY_WINDOW = 4` tin cuối được nạp lại
   tệp thật vào ngữ cảnh; tin cũ hơn thay bằng dòng chữ "[Đã gửi kèm tệp: ...]" — model biết
   từng có tệp nhưng không tốn lại chi phí đọc.
6. **Tầng provider trung lập:** attachments đóng thành block chung, Claude nhận dạng base64
   image/document, Gemini nhận `inline_data` — logic kiểm quyền không phụ thuộc model nào.
7. **Về bảo mật thông tin:** nội dung tệp là DỮ LIỆU người hỏi tự đưa vào, được đối xử đúng
   như chữ họ gõ (mục 3 — dữ liệu không phải mệnh lệnh); chữ trong tệp có ghi "hãy bỏ qua
   giới hạn..." thì hàng rào quyền ở backend vẫn kiểm y nguyên. Tệp đi ra nhà cung cấp model
   cùng chuyến với câu hỏi — áp dụng đúng lưu ý số 1 ở mục 8.

Cùng commit này bổ sung tool thứ 30 `export_excel_file` (CR-205) — chiều ĐI RA: xuất dữ
liệu đã tra thành bảng tính .xlsx (openpyxl; chuỗi số được đổi thành kiểu số thật của Excel
để tính tiếp được; tên sheet rửa ký tự cấm). Quyền như `export_report_file` — xem bảng mục 5.

---

## 8. Giới hạn còn lại — nói thẳng để cân nhắc

Không có hệ nào an toàn tuyệt đối; đây là những điểm cần biết khi đánh giá:

1. **Dữ liệu câu hỏi + kết quả tool có đi ra nhà cung cấp model** (Anthropic/Google) qua API —
   giống mọi sản phẩm dùng LLM thương mại. Dữ liệu gửi đi đã được lọc theo quyền người hỏi
   (chỉ những gì người đó vốn được xem trên màn hình), nhưng về mặt chính sách cần ghi nhận:
   đây là dữ liệu rời khỏi hạ tầng của mình, ràng buộc bằng điều khoản không-huấn-luyện của
   API trả phí. Muốn siết hơn thì thu hẹp nhóm được cấp `assistant.read`.
2. **Model vẫn có thể bịa chữ (không bịa được số liệu có nguồn).** Đã có luật prompt cấm bịa và
   cơ chế `denied` tường minh, nhưng bản chất LLM là xác suất — câu trả lời diễn giải sai vẫn có
   thể xảy ra. Vì vậy mọi thao tác chốt (tạo phiếu) đều bắt người dùng tự rà và tự bấm.
3. **Kho HDSD mở cho mọi người đăng nhập là chủ đích** — không để tài liệu nhạy cảm vào Trung
   tâm HDSD.
4. **Tool mới phải tự giác đi qua checklist quyền.** Hiện chưa có test tự động ép "mọi tool đọc
   chứng từ phải gọi `apply_scope`" — đang dựa vào quy ước code review. Đề xuất bổ sung một
   guard test tương tự bài học B-07 (đã nêu với nhóm phát triển, chưa làm).
5. **Tồn kho chưa có tool** — nếu tương lai bổ sung, bắt buộc lặp lại đúng khuôn:
   `ctx.can` + `apply_scope` + ẩn cột nhạy cảm, và cập nhật bảng ở mục 5 tài liệu này.
   (Công nợ đã lên sóng 27/08/2026 theo đúng khuôn đó — xem nhóm cuối của mục 5.)

---

## 9. Kiểm chứng bằng test

Các hàng rào trên có test tự động kèm theo (chạy `pytest` trong container api,
phạm vi `test/backend/`):

- `test_assistant_tools.py` (kèm `test_assistant_document_tool.py`,
  `test_assistant_approval_tool.py`, `test_assistant_export_tool.py`) — từ chối khi thiếu quyền,
  ẩn NCC khi thiếu `supplier.read`, allowlist tool.
- `test_assistant_draft_tool.py` — quyền tạo phiếu trước khi soạn nháp; khớp/không khớp danh mục
  công ty; enum động lấy từ DB và không rò rỉ giữa các request.
- `test_assistant_payable_tool.py` — công nợ: từ chối khi thiếu `payable.read`; soạn nháp YCTT
  đòi đủ cả hai quyền; chỉ chọn khoản còn phải trả (khoản đã tất toán bị loại và báo rõ).
- `test_assistant_procurement_doc_tool.py` — recap chứng từ: từ chối khi thiếu quyền đọc; phiếu
  ngoài phạm vi báo "không tìm thấy"; ẩn NCC + không kèm công nợ khi thiếu quyền; YCKS chỉ đếm
  phương án không lộ NCC; đếm phiếu chờ duyệt đúng theo quyền `approve` từng loại, loại bỏ phiếu
  xóa mềm; "phiếu của tôi" chỉ trả phiếu chính mình đứng tên kể cả khi scope là `all`, kèm số
  liệu tiến độ, và denied khi hỏi đích danh loại phiếu không có quyền đọc.
- `test_assistant_attachment.py` — đính kèm chat (mục 7): từ chối tệp sai loại / quá trần
  kích thước, nhận diện theo magic bytes, chặn quá 3 tệp/tin, sai chủ tệp trả 404, chỉ
  nạp lại tệp thật cho cửa sổ tin cuối (tin cũ thành dòng placeholder).
- `test_assistant_export_tool.py` — thêm phần T30: thiếu sheets trả lời mềm, chuẩn hóa
  sheet lệch cột + đổi chuỗi số thành kiểu số Excel, tên sheet trùng không làm openpyxl
  nổ, file .xlsx hợp lệ và thuộc về đúng người hỏi.
- `test_pham_vi_khai_du_b07.py` — mọi entity phải khai phạm vi dữ liệu, quên khai là test đỏ
  (hàng rào "an toàn khi cấu hình thiếu").

Cách tự kiểm bằng tay nhanh nhất: dùng hai tài khoản khác quyền trên dev, hỏi cùng một câu về
NCC / lịch sử mua, so hai câu trả lời.
