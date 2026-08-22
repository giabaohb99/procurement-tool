"""Bộ mã trạng thái của Thu mua — khai một chỗ duy nhất (R3).

Đây là nơi ở của **khuôn B** theo QĐ-9: 12 cột từng lưu chữ tiếng Việt nay lưu MÃ chuỗi tiếng
Anh. Danh sách 12 cột và lý do chọn khuôn nằm ở `doc/erp/15-do-be-tong-nen-v2.md` §2.2 và §2.4.

**Đây KHÔNG phải khuôn mặc định.** QĐ-11: chức năng làm mới dùng `SMALLINT` + `IntEnum`. Bộ mã
chuỗi ở tệp này là **ngoại lệ đóng**, chỉ cho 12 cột đã liệt kê, vì `status` cấp phiếu của tám
chứng từ Thu mua vốn đã là mã chuỗi — trộn hai khuôn trong cùng một chứng từ còn tệ hơn.

Mỗi đợt B-xx thêm một mục vào tệp này. Thêm xong nhớ chạy lại `scripts/gen_status_ts.py`.
"""

from app.core.status_catalog import Code, CodeSet, register

# =========================================================================
# B-02 — Hợp đồng (`tab_contract`)
# =========================================================================

# Cột `party_type`. Không có chuỗi tiến trình nên `sort_order` để 0 hết, giữ thứ tự khai.
CONTRACT_PARTY_TYPE = register(CodeSet("contract_party_type", "Loại đối tượng", [
    Code("supplier", "Nhà cung cấp"),
    Code("customer", "Khách hàng"),
    Code("other",    "Khác"),
]))

# Cột `status`. `sort_order` ở đây là thứ tự HIỂN THỊ, không phải máy trạng thái tự chạy —
# hợp đồng không tự nhảy trạng thái, người dùng chọn tay.
CONTRACT_STATUS = register(CodeSet("contract_status", "Trạng thái hợp đồng", [
    Code("active",     "Hiệu lực",  1),
    Code("expired",    "Hết hạn",   2),
    Code("liquidated", "Thanh lý",  3, is_terminal=True),
    Code("cancelled",  "Hủy", is_exception=True),
]))

# KHÔNG phải cột — backend TÍNH ra từ `end_date` mỗi lần trả về (`expiry_state`). Đưa vào đây vì
# nó cũng là chuỗi tiếng Việt đi qua API, mà tệ hơn: nó còn được dùng làm GIÁ TRỊ THAM SỐ URL
# (`?expiry=Hết hạn`) — tiếng Việt có dấu trong query string. Không cần migration.
#
# Đừng lẫn với `contract_status`: cả hai đều có nhãn "Hết hạn" nhưng khác nghĩa. `status` là
# người dùng đánh dấu; `expiry` là máy tính theo ngày hôm nay.
CONTRACT_EXPIRY = register(CodeSet("contract_expiry", "Tình trạng hạn hợp đồng", [
    Code("valid",         "Còn hạn",     1),
    Code("expiring_soon", "Sắp hết hạn", 2),
    Code("expired",       "Hết hạn",     3, is_terminal=True),
]))


# =========================================================================
# B-03 — Nhân sự (`tab_employee`) và Nhà cung cấp (`tab_supplier`)
# =========================================================================

# Cột `tab_employee.status`.
#
# Bộ giá trị KHÔNG lấy từ dữ liệu đang có: đếm ngày 22/08/2026 thì prod chỉ có 3 giá trị
# (Chính thức · Nghỉ thai sản · Nghỉ việc), dev/local chỉ có 1. Nhưng ô chọn ở cả hai bản
# giao diện mời đủ 4 — "Cộng tác viên" chưa ai chọn không có nghĩa là nó không hợp lệ, bỏ
# ra là lần đầu có người chọn sẽ ăn 422.
#
# Không có chuỗi tiến trình: nhân sự không tự nhảy trạng thái và nghỉ việc rồi vẫn vào lại
# được, nên `sort_order` để 0 hết (giữ thứ tự khai) và KHÔNG đặt `is_terminal`. Thứ tự khai
# chính là thứ tự vẽ vòng tròn ở Tổng quan Nhân sự.
EMPLOYEE_STATUS = register(CodeSet("employee_status", "Trạng thái nhân sự", [
    Code("official",        "Chính thức"),
    Code("collaborator",    "Cộng tác viên"),
    Code("maternity_leave", "Nghỉ thai sản"),
    Code("resigned",        "Nghỉ việc"),
]))

# Cột `tab_supplier.legal_type` — loại hình pháp lý của NCC.
#
# Rỗng = CHƯA CHỌN và là mặc định của cột (159/161 dòng prod đang rỗng), nên rỗng phải luôn
# hợp lệ. Cột này cố ý KHÔNG nằm trong `FILTERABLE` của NCC nên không có ô lọc nào phải đổi.
SUPPLIER_LEGAL_TYPE = register(CodeSet("supplier_legal_type", "Loại hình pháp lý NCC", [
    Code("company",     "Công ty"),
    Code("individual",  "Cá nhân"),
    Code("partnership", "Hợp danh"),
    Code("household",   "Hộ kinh doanh"),
]))


# =========================================================================
# B-04 — Phiếu khảo sát (`tab_survey.approve_status`)
# =========================================================================

# Cột `approve_status` — KẾT QUẢ XÉT DUYỆT của phiếu khảo sát.
#
# Khác mọi cột đã làm ở B-02/B-03: cột này KHÔNG do người dùng nhập. Nó không có mặt trong
# schema đầu vào nào cả, chỉ `survey/service.set_status()` ghi vào, suy từ `status` của phiếu.
# Vì vậy B-04 không phải sửa ô chọn hay ô lọc nào — `frontend/` không hề đọc cột này.
#
# Nó KHÔNG phải bản sao của `status`: `set_status` chỉ ghi khi `status` là `approved`/`rejected`,
# nên phiếu duyệt xong rồi bị hủy vẫn giữ `approved` ở đây. Cột này nhớ QUYẾT ĐỊNH DUYỆT GẦN
# NHẤT, còn `status` nhớ phiếu đang ở đâu. Đừng "dọn" bằng cách suy lại từ `status`.
#
# Mã trùng chữ với `status` của phiếu (`approved` / `rejected`) là CỐ Ý — cùng một sự kiện
# duyệt sinh ra cả hai, đặt tên khác nhau chỉ tổ khiến người đọc `set_status` tưởng có hai
# khái niệm.
#
# `pending` thay cho chuỗi rỗng: rỗng ở cột này có nghĩa riêng — CHƯA có quyết định duyệt (phiếu
# nháp hoặc vừa gửi duyệt) — chứ không phải dữ liệu thiếu, nên nó phải là một mã có tên chứ
# không được để lẫn với `NULL`/`""` (bẫy đã ghi ở `doc/erp/15` §3 B-04). Nhãn để "Chưa xét duyệt"
# chứ KHÔNG dùng "Chờ duyệt": "Chờ duyệt" là một giá trị của cột `line_approve` cấp DÒNG, hai
# cột đứng cạnh nhau trên cùng màn hình, trùng chữ là đọc báo cáo ra hiểu nhầm ngay.
#
# `sort_order` để 0 hết: phiếu bị "Không duyệt" vẫn sửa rồi gửi duyệt lại được, không có chuỗi
# một chiều nào để mà khai.
SURVEY_APPROVE_STATUS = register(CodeSet("survey_approve_status", "Kết quả duyệt phiếu khảo sát", [
    Code("pending",  "Chưa xét duyệt"),
    Code("approved", "Duyệt"),
    Code("rejected", "Không duyệt"),
]))


# =========================================================================
# B-05 — Công nợ phải trả (`tab_payable.status`)
# =========================================================================

# Cột `status` — cột này KHÔNG do người dùng chọn. `payable/service.recalc_status()` tính lại
# nó từ `paid_amount` so với `total` sau MỖI lần phân bổ thanh toán. Nghĩa là:
#
#   - Nó là hàm của hai con số tiền, không phải máy trạng thái. Sửa `total` của một công nợ đã
#     tất toán (thêm hóa đơn, đổi số) là nó tự lùi từ `paid` về `partial` — nên KHÔNG mã nào ở
#     đây được đánh `is_terminal`. `paid` trông như đích đến nhưng không phải.
#   - `sort_order` 1/2/3 là chuỗi tiến trình THẬT theo mức đã trả, khác với B-02/B-03/B-04 nơi
#     nó chỉ là thứ tự hiển thị. Dùng được để sắp cột, xếp thẻ tổng hợp.
#
# Nhãn ở đây là chữ ĐẦY ĐỦ ("Chờ thanh toán"), còn giá trị cũ trong CSDL là chữ VIẾT TẮT
# ("Chờ TT"). Cố ý lệch: bản v2 xưa nay hiện chữ đầy đủ qua bảng dịch tay
# `PAYABLE_STATUS_LABELS`, nay bảng đó bị bộ mã này thay. Ai viết `downgrade()` của migration
# nhớ trả lại chữ VIẾT TẮT chứ không phải nhãn ở đây — cả ba mã đều lệch, không mã nào trùng.
#
# Còn một trạng thái thứ tư ở giao diện: "Trả dư" (`remaining < 0`) trong
# `frontend/src/components/supplier-payables-stats.ts`. Nó CHỈ ĐỂ HIỂN THỊ, tính tại chỗ từ
# `remaining`, chưa bao giờ được ghi xuống cột này — nên KHÔNG đưa vào bộ mã. Đưa vào là mời
# người sau ghi nó xuống DB, mà đúng lúc đó công nợ âm sẽ trốn khỏi mọi bộ lọc `!= paid`
# (xem sự cố ở `payment-allocation-bug`, fix `82ce6ad`).
PAYABLE_STATUS = register(CodeSet("payable_status", "Trạng thái công nợ", [
    Code("unpaid",  "Chờ thanh toán",       1),
    Code("partial", "Thanh toán một phần",  2),
    Code("paid",    "Đã thanh toán",        3),
]))


# =========================================================================
# B-06 nhịp 1 — Cụm Đơn mua hàng + Yêu cầu mua hàng, bốn cột "phẳng"
# =========================================================================

# Cột `tab_purchase_request_item.line_status` — tiến độ của MỘT DÒNG hàng trên Yêu cầu mua hàng.
#
# Không ai gõ tay cột này (trừ nút Hủy dòng): `purchase_request/service.sync_from_purchase_orders`
# suy nó ra từ các dòng ĐMH liên kết theo `product_code`. Nó là bản RÚT GỌN của
# `PO_PROGRESS_STATUS` bên dưới: hai mức chứng từ kế toán (`doc_pending`/`doc_sent`) bị gộp vào
# `received`, và không có `paused`. Bốn mã `not_ordered · ordered · received · completed` cố ý
# TRÙNG TÊN với bốn mã cùng nghĩa của `PO_PROGRESS_STATUS` — hai cột này nói về cùng một dòng
# hàng nhìn từ hai phía, đặt tên lệch nhau là bắt người đọc phải tra bảng khi lần theo `_sync_pr`.
#
# `no_po` là mã RIÊNG của bộ này, không có bên ĐMH (CR-074): "chưa ai lập đơn" khác với "đã có
# đơn nhưng chưa bấm đặt hàng" — trước CR-074 hai tình huống chung một nhãn nên người yêu cầu
# không biết NSTM đã bắt tay làm chưa.
#
# `cancelled` đánh `is_exception` chứ không chỉ `is_terminal`: `recompute_status` LOẠI nó ra khỏi
# phép tính "mọi dòng đã hoàn thành chưa" (một dòng hủy + các dòng còn lại đủ = phiếu vẫn hoàn
# thành). Đó đúng là nghĩa "nằm ngoài chuỗi", không phải "đứng cuối chuỗi".
PR_LINE_STATUS = register(CodeSet("pr_line_status", "Trạng thái dòng Yêu cầu mua hàng", [
    Code("no_po",       "Chưa tạo đơn mua hàng", 1),
    Code("not_ordered", "Chưa đặt hàng",         2),
    Code("ordered",     "Đã đặt hàng",           3),
    Code("received",    "Đã nhận hàng",          4),
    Code("completed",   "Hoàn thành",            5, is_terminal=True),
    Code("cancelled",   "Hủy đơn", is_terminal=True, is_exception=True),
]))

# Cột `tab_purchase_order.document_status` — hồ sơ chứng từ của cả ĐƠN, người dùng chọn tay.
#
# ⚠️ Giá trị cũ trong CSDL VIẾT THƯỜNG hết ("chưa có chứng từ"), khác mọi cột tiếng Việt còn lại
# của Thu mua. `downgrade()` của migration phải trả lại đúng chữ thường, không phải nhãn ở đây.
#
# Nhãn `partial` là "Đã có thông tin chứng từ" — đúng chữ trong CSDL. `frontend/` từng rút gọn
# thành "Đã có chứng từ" ở ô lọc điều kiện, tức là màn danh sách và ô lọc hiện HAI chữ khác nhau
# cho cùng một giá trị. Nay cả hai đều đọc bộ mã này nên chuyện đó hết đường xảy ra.
PO_DOCUMENT_STATUS = register(CodeSet("po_document_status", "Hồ sơ chứng từ đơn mua hàng", [
    Code("none",    "Chưa có chứng từ",           1),
    Code("partial", "Đã có thông tin chứng từ",   2),
    Code("full",    "Đã đủ chứng từ",             3, is_terminal=True),
]))

# Cột `tab_po_item.line_status` — mức GIAO HÀNG của một dòng ĐMH, tính từ SL nhận so với SL đặt.
#
# Đừng lẫn với `PR_LINE_STATUS`: trùng tên cột (`line_status`) nhưng khác hẳn nghĩa. Cột này chỉ
# nói chuyện số lượng, không biết gì về chứng từ hay thanh toán.
#
# `purchase_order/service._recalc` tính lại cột này sau mỗi lần sửa lần giao, nên nó là HÀM của
# hai con số — giống `payable.status` ở B-05, và cũng vì vậy `full` KHÔNG phải trạng thái kết:
# tăng SL đặt của một dòng đã đủ là nó tự lùi về `partial`.
#
# Dòng cũ chưa từng được tính lại thì cột này RỖNG (3 dòng ở dev, 1 ở local). Rỗng là giá trị hợp
# lệ, migration để nguyên và giao diện hiện ô trống.
PO_ITEM_LINE_STATUS = register(CodeSet("po_item_line_status", "Trạng thái giao của dòng đơn mua hàng", [
    Code("not_delivered", "Chưa giao", 1),
    Code("partial",       "Đang giao", 2),
    Code("full",          "Đủ",        3),
]))

# Cột `tab_po_delivery.status` — kết quả của MỘT LẦN GIAO.
#
# ⚠️ Kiểm kê ngày 22/08/2026 chỉ thấy hai giá trị (`Đã nhận`, `Chờ giao`) trên cả ba môi trường,
# nhưng `purchase_order/service._recalc` sinh ra BỐN. `Lỗi` và `Giao thiếu` chưa từng xuất hiện
# vì chưa ai nhập lần giao nào hụt SL hoặc bị QC đánh lỗi — chúng vẫn là nhánh sống trong mã.
# Bỏ hai mã đó khỏi bộ này thì lần đầu có hàng lỗi, validator sẽ chặn một giá trị mà chính
# backend vừa tự đặt. Kiểm kê là ảnh chụp dữ liệu, không phải danh sách giá trị hợp lệ.
PO_DELIVERY_STATUS = register(CodeSet("po_delivery_status", "Trạng thái lần giao", [
    Code("pending",  "Chờ giao",   1),
    Code("short",    "Giao thiếu", 2),
    Code("defect",   "Lỗi",        3, is_exception=True),
    Code("received", "Đã nhận",    4),
]))


# =========================================================================
# B-06 nhịp 2 — Máy trạng thái tiến độ dòng ĐMH
# =========================================================================

# Hai cột dùng CHUNG bộ này: `tab_po_item.progress_status` và `tab_po_item.status_before_pause`.
# Cột thứ hai chỉ là bản chụp cột thứ nhất ngay trước khi bấm *Tạm ngưng*, để nút *Bỏ tạm ngưng*
# khôi phục lại. Đổi lệch nhau — ví dụ chỉ đổi `progress_status` — là nút đó khôi phục sai trạng
# thái mà KHÔNG báo lỗi gì: `set_item_progress` gán thẳng giá trị cũ, chẳng ai kiểm.
#
# ⚠️ `sort_order` ở đây LÀ LOGIC, không phải thứ tự hiển thị. `purchase_order/service` tính bước
# kế tiếp bằng `PROGRESS_ORDER.index(...)`; `ordered_values` của bộ này phải TRÙNG KHÍT list đó,
# và `purchase_request/service._PROGRESS_ORDER` là bản chép tay thứ hai của cùng list. Chèn một mã
# vào giữa là đổi luôn nghĩa của mọi dòng đang nằm sau nó.
#
# `paused` và `cancelled` là `is_exception` nên KHÔNG có mặt trong `ordered_values` — đúng tính
# chất "nằm ngoài luồng tuần tự" của `PROGRESS_EXCEPTIONS`. Chúng chỉ tới được bằng cách bấm nút
# kèm lý do; sáu mã còn lại thì máy tự tiến theo dữ liệu, không đặt tay được.
PO_PROGRESS_STATUS = register(CodeSet("po_progress_status", "Tiến độ dòng đơn mua hàng", [
    Code("not_ordered", "Chưa đặt hàng",        1),
    Code("ordered",     "Đã đặt hàng",          2),
    Code("received",    "Đã nhận hàng",         3),
    Code("doc_pending", "Chưa gửi ĐMH cho KT",  4),
    Code("doc_sent",    "Đã gửi ĐMH cho KT",    5),
    Code("completed",   "Hoàn thành",           6, is_terminal=True),
    Code("paused",      "Tạm ngưng", is_exception=True),
    Code("cancelled",   "Hủy đơn", is_terminal=True, is_exception=True),
]))
