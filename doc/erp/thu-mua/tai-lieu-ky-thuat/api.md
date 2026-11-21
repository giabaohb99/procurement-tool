# TÀI LIỆU API — THU MUA

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `category_assignee`, `contract`, `execution_report`, `packaging-cost`, `payable`, `payment_request`, `purchase_cost_type`, `purchase_history`, `purchase_order`, `purchase_progress`, `purchase_request`, `supplier`, `survey`, `survey_progress`, `survey_report`, `survey_request`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `purchase_request`, `survey_request`, `survey`, `survey_progress`, `purchase_order`, `purchase_progress`, `purchase_history`, `payable`, `payment_request`, `supplier`, `contract`, `category_assignee`, `packaging_cost`, `product_price`; danh mục dựng bằng `make_crud_router`: `/api/po-cost-types`, `/api/packaging-boms`, `/api/product-price-quotes`, `/api/product-price-limits`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/category-assignees` | Danh sách phân công NSTM — 1 query JOIN (hết N+1), phân trang + sort tại DB. | `category_assignee.read` |  | tự dò: v2 `procurement` |
| POST | `/api/category-assignees` | Thêm phân công người phụ trách chính và dự phòng cho một phân loại hàng. | `category_assignee.create` |  | tự dò: v2 `procurement` |
| POST | `/api/category-assignees/bulk` | Gán cùng người phụ trách chính, dự phòng cho nhiều phân loại một lần. | `category_assignee.create` |  | tự dò: v2 `procurement` |
| GET | `/api/category-assignees/{cid}` | Xem một dòng phân công phụ trách theo phân loại hàng. | `category_assignee.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/category-assignees/{cid}` | Sửa một dòng phân công phụ trách. | `category_assignee.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/category-assignees/{cid}` | Xóa một dòng phân công phụ trách. | `category_assignee.delete` |  | tự dò: v2 `procurement` |
| GET | `/api/contracts` | Danh sách hợp đồng trong phạm vi được xem; lọc theo khoảng ngày hết hạn và đã ký hay chưa. | `contract.read` | `apply_scope` | tự dò: v2 `production` |
| POST | `/api/contracts` | Tạo hợp đồng; tự điền thông tin bên ký từ danh mục. | `contract.create` | `apply_scope` | tự dò: v2 `production` |
| DELETE | `/api/contracts` | Xóa nhiều hợp đồng theo danh sách id trong phạm vi được xóa. | `contract.delete` | `apply_scope` | tự dò: v2 `production` |
| GET | `/api/contracts/meta/types` | Bộ loại hợp đồng cố định cho FE dựng ô chọn (CR-118). | `contract.read` |  | tự dò: v2 `production` |
| GET | `/api/contracts/{cid}` | Chi tiết một hợp đồng. | `contract.read` |  | tự dò: v2 `production` |
| PATCH | `/api/contracts/{cid}` | Sửa hợp đồng; tự điền lại thông tin bên ký từ danh mục. | `contract.write` |  | tự dò: v2 `production` |
| DELETE | `/api/contracts/{cid}` | Xóa MỀM một hợp đồng (ai-CR-177): đánh cờ `is_deleted` + mốc + người xóa. | `contract.delete` |  | tự dò: v2 `production` |
| GET | `/api/execution-report/{entity}/{owner_id}` | Đọc khối Báo cáo thực hiện của một YCBG hoặc ĐMH (nút, giai đoạn, hồ sơ). | đăng nhập |  | tự dò: v2 `procurement`, v2 dùng chung |
| DELETE | `/api/execution-report/{entity}/{owner_id}` | Xóa CẢ khối báo cáo — có thể HOÀN TÁC từ Lịch sử thao tác. | đăng nhập |  | tự dò: v2 `procurement`, v2 dùng chung |
| POST | `/api/execution-report/{entity}/{owner_id}/apply-template` | Nút "Tạo mẫu" trên một nút dòng hàng / một giai đoạn — đổ mẫu chung vào, cộng thêm, bỏ qua hồ sơ đã có. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/docs` | Thêm một hồ sơ vào Báo cáo thực hiện. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/docs/bulk-delete` | Xóa nhiều hồ sơ của Báo cáo thực hiện một lần. | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | Cập nhật một hồ sơ của Báo cáo thực hiện. | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | Xóa một hồ sơ của Báo cáo thực hiện. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/first-doc` | Thêm hồ sơ đầu tiên và dựng khung năm giai đoạn cho Báo cáo thực hiện còn trống. | đăng nhập |  |  |
| GET | `/api/execution-report/{entity}/{owner_id}/first-doc-options` | Ô chọn của hộp "Thêm hồ sơ" khi khối còn trống: dòng hàng của chứng từ + 5 giai đoạn mặc định. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/init` | Dựng khung Báo cáo thực hiện theo mẫu từ các dòng hàng của phiếu. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/items` | Thêm một nút (nhóm hồ sơ) vào Báo cáo thực hiện. | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | Đổi tên một nút của Báo cáo thực hiện. | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | Xóa một nút của Báo cáo thực hiện; hồ sơ gắn nút đó chuyển về nút Chung. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/phases` | Thêm một giai đoạn vào Báo cáo thực hiện. | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | Sửa tên, nơi thực hiện của một giai đoạn. | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | Xóa một giai đoạn của Báo cáo thực hiện. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/restore` | Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác. | đăng nhập |  |  |
| GET | `/api/execution-report/{entity}/{owner_id}/templates` | Ô chọn mẫu của hộp "Khởi tạo báo cáo mẫu" (duoc-CR-614). | đăng nhập |  |  |
| GET | `/api/packaging-boms` | Danh sách giá bao bì, có lọc và phân trang. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| POST | `/api/packaging-boms` | Thêm một dòng giá bao bì; chặn trùng mã, ghi nhật ký. | `packaging_cost.create` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| GET | `/api/packaging-boms/{oid}` | Xem một dòng giá bao bì theo id. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| PATCH | `/api/packaging-boms/{oid}` | Sửa một dòng giá bao bì; chỉ ghi các ô gửi lên, ghi nhật ký. | `packaging_cost.write` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| DELETE | `/api/packaging-boms/{oid}` | Xóa một dòng giá bao bì; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `packaging_cost.delete` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| GET | `/api/packaging-cost/code-options` | Ô chọn nhiều mã của màn Tác động: mọi mã đang dùng trong định mức, kèm `{code, name, group, usage, new}`. | `packaging_cost.read` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/hh-options` | Ô chọn sản phẩm của Lịch sử mua hàng: mọi mã hàng hóa có định mức bao bì, kèm `{code, name}` (~1.000, không phân trang). | `packaging_cost.read` | không lọc (danh mục dùng chung) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/history` | Lịch sử mua hàng: từng lần mua của mã VTBB (hoặc thành phần của sản phẩm), mới nhất trước, kèm KPI và dữ liệu biểu đồ. | `packaging_cost.read` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/history/export` | Xuất Excel Lịch sử mua hàng theo đúng bộ lọc + thứ tự đang xem (không phân trang, tối đa 5.000 dòng). | `packaging_cost.export` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| POST | `/api/packaging-cost/impact` | Tác động giá bao bì: chọn các mã chai / nắp / nhãn / nhãn thùng / thùng (kèm giá giả định) → sản phẩm bị ảnh hưởng. | `packaging_cost.read` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| POST | `/api/packaging-cost/impact/export` | Xuất Excel kết quả Tác động giá (hai sheet: Mã đã chọn, Sản phẩm bị ảnh hưởng). | `packaging_cost.export` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/last-prices` | Giá mua gần nhất: mỗi mã VTBB một dòng (ngày, nhà cung cấp, số lượng, đơn giá n lần mua, biến động, giá trung bình). | `packaging_cost.read` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/last-prices/export` | Xuất Excel Giá mua gần nhất theo đúng bộ lọc, số lần `n` và thứ tự đang xem (không phân trang); `show_qty` thêm cột số lượng. | `packaging_cost.export` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/price-list` | Bảng giá VTBB: mỗi mã vật tư một dòng (giá cũ / mới / chênh, số sản phẩm dùng, báo giá, ngưỡng). | `packaging_cost.read` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/packaging-cost/price-list/export` | Xuất Excel Bảng giá VTBB theo đúng bộ lọc + thứ tự đang xem (không phân trang). | `packaging_cost.export` | `scope_condition` (pháp nhân, đo trên sổ giá) | tự dò: v2 `procurement` |
| GET | `/api/payables` | Danh sách công nợ phải trả, sắp theo hạn trả gần nhất, kèm mã MISA của đơn. | `payable.read` |  | tự dò: v2 `finance`, v2 `procurement`, v2 `production` |
| GET | `/api/payables/export/xlsx` | Ticket #16 — xuất Excel danh sách Công nợ đúng bộ lọc + phạm vi màn hình. | `payable.export` |  | tự dò: v2 `finance` |
| GET | `/api/payables/summary` | Thẻ tổng hợp công nợ. | `payable.read` |  | tự dò: v2 `finance` |
| POST | `/api/payables/{pid}/offset-prepay` | CR-268 — kế toán cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước không gắn đơn) vào khoản công nợ này. | `payable.write` | `apply_scope` | tự dò: v2 `finance` |
| GET | `/api/payment-requests` | Danh sách yêu cầu thanh toán (YCTT) trong phạm vi được xem, có lọc và phân trang. | `payment_request.read` |  | tự dò: v2 `finance`, v2 `procurement` |
| POST | `/api/payment-requests` | Tạo YCTT từ các dòng công nợ trong phạm vi được xem. | `payment_request.create` | `apply_scope` | tự dò: v2 `finance`, v2 `procurement` |
| DELETE | `/api/payment-requests` | Xóa nhiều YCTT theo danh sách id trong phạm vi được xóa. | `payment_request.delete` | `apply_scope` | tự dò: v2 `finance`, v2 `procurement` |
| GET | `/api/payment-requests/export/xlsx` | bao-CR-525 — xuất Excel THEO DÒNG CHI TIẾT: phiếu đúng bộ lọc + phạm vi màn danh sách, mỗi dòng PO / hóa đơn một hàng, thông tin phiếu lặp lại (xem `export.py`). | `payment_request.export` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/hanging` | CR-268 — tiền treo (phiếu trả trước đã chi, chưa đối trừ/hoàn hết) của 1 NCC. | `payment_request.read` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/meta/department-managers` | bao-CR-553 — ô "Trưởng bộ phận" của YCTT: trưởng phòng mọi phòng (có Ban Giám đốc). | `payment_request.read` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}` | Chi tiết một YCTT. | `payment_request.read` | `apply_scope` | tự dò: v2 `finance` |
| PATCH | `/api/payment-requests/{rid}` | Sửa YCTT. | `payment_request.write` |  | tự dò: v2 `finance` |
| DELETE | `/api/payment-requests/{rid}` | Xóa một YCTT. | `payment_request.delete` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/approve` | Duyệt YCTT và báo người liên quan. | `payment_request.approve` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/pay` | Ghi nhận đã chi cho YCTT đã duyệt và báo người liên quan. | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}/print` | Dữ liệu in một YCTT kèm thông tin công ty. | `payment_request.print` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/refresh-from-payables` | bao-CR-509 — GHI số mới theo công nợ vào phiếu NHÁP (tính lại từ DB lúc ghi). | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}/refresh-preview` | bao-CR-509 — XEM TRƯỚC số mới của từng dòng theo công nợ hiện tại, KHÔNG ghi gì. | `payment_request.read` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/refund` | CR-268 — ghi nhận NCC HOÀN TIỀN phần treo của phiếu trả trước đã chi. | `payment_request.write` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/reject` | Từ chối phiếu yêu cầu thanh toán (khóa) — người duyệt thao tác. | `payment_request.approve` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/submit` | Gửi duyệt YCTT và báo người duyệt. | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/po-cost-types` | Danh sách danh mục Loại chi phí thu mua, có lọc và phân trang. | `purchase_cost_type.read` | `apply_scope` | tự dò: v2 `procurement`, v2 dùng chung |
| POST | `/api/po-cost-types` | Thêm một dòng danh mục Loại chi phí thu mua; chặn trùng mã, ghi nhật ký. | `purchase_cost_type.create` |  | tự dò: v2 `procurement`, v2 dùng chung |
| GET | `/api/po-cost-types/export/csv` | Xuất danh mục Loại chi phí thu mua ra tệp CSV theo bộ lọc đang chọn. | `purchase_cost_type.export` | `apply_scope` |  |
| GET | `/api/po-cost-types/{oid}` | Xem một dòng danh mục Loại chi phí thu mua theo id. | `purchase_cost_type.read` | `get_scoped` |  |
| PATCH | `/api/po-cost-types/{oid}` | Sửa một dòng danh mục Loại chi phí thu mua; chỉ ghi các ô gửi lên, ghi nhật ký. | `purchase_cost_type.write` | `get_scoped` |  |
| DELETE | `/api/po-cost-types/{oid}` | Xóa một dòng danh mục Loại chi phí thu mua; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `purchase_cost_type.delete` | `get_scoped` |  |
| GET | `/api/products/{code}/purchase-history` | Lịch sử mua của một mặt hàng; tìm theo NCC chỉ khi được xem NCC. | `product.read` |  | tự dò: v2 `procurement`, v2 `production` |
| GET | `/api/product-price-limits` | Danh sách giá bao bì, có lọc và phân trang. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| POST | `/api/product-price-limits` | Thêm một dòng giá bao bì; chặn trùng mã, ghi nhật ký. | `packaging_cost.create` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| GET | `/api/product-price-limits/{oid}` | Xem một dòng giá bao bì theo id. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| PATCH | `/api/product-price-limits/{oid}` | Sửa một dòng giá bao bì; chỉ ghi các ô gửi lên, ghi nhật ký. | `packaging_cost.write` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| DELETE | `/api/product-price-limits/{oid}` | Xóa một dòng giá bao bì; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `packaging_cost.delete` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| GET | `/api/product-price-quotes` | Danh sách giá bao bì, có lọc và phân trang. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| POST | `/api/product-price-quotes` | Thêm một dòng giá bao bì; chặn trùng mã, ghi nhật ký. | `packaging_cost.create` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động | tự dò: v2 `procurement` |
| GET | `/api/product-price-quotes/{oid}` | Xem một dòng giá bao bì theo id. | `packaging_cost.read` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| PATCH | `/api/product-price-quotes/{oid}` | Sửa một dòng giá bao bì; chỉ ghi các ô gửi lên, ghi nhật ký. | `packaging_cost.write` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| DELETE | `/api/product-price-quotes/{oid}` | Xóa một dòng giá bao bì; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `packaging_cost.delete` | không lọc theo pháp nhân (danh mục dùng chung, `scoped=False`) — cổng là quyền hành động |  |
| GET | `/api/purchase-orders` | Danh sách đơn mua hàng (ĐMH) trong phạm vi được xem, có lọc và phân trang. | `purchase_order.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders` | Tạo ĐMH mới ở trạng thái Nháp. | `purchase_order.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-orders` | Xóa nhiều ĐMH theo danh sách id trong phạm vi được xóa. | `purchase_order.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/export/xlsx` | CR-068 — xuất Excel danh sách ĐMH, cột dòng hàng lấy đúng bộ cột màn Tiến độ mua hàng (một hàng = một lần giao). | `purchase_order.export` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/lines` | Danh sách DÒNG HÀNG của các đơn mua hàng — dùng cho trang chi tiết Kho. | `purchase_order.read` | `apply_scope` |  |
| GET | `/api/purchase-orders/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_order.read` |  |  |
| GET | `/api/purchase-orders/{pid}` | Chi tiết một ĐMH. | `purchase_order.read` | `apply_scope` | tự dò: v2 `procurement`, v2 `system` |
| PATCH | `/api/purchase-orders/{pid}` | Sửa ĐMH. | `purchase_order.write` |  | tự dò: v2 `procurement`, v2 `system` |
| DELETE | `/api/purchase-orders/{pid}` | Xóa một ĐMH. | `purchase_order.delete` |  | tự dò: v2 `procurement`, v2 `system` |
| POST | `/api/purchase-orders/{pid}/approve` | Duyệt ĐMH đang chờ duyệt và ghi người duyệt lên bản in. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_order.read` |  |  |
| POST | `/api/purchase-orders/{pid}/cancel` | Hủy ĐMH kèm lý do bắt buộc; đơn đã Hủy hay Hoàn thành thì không hủy lại. | `purchase_order.cancel` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/clone` | Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS). | `purchase_order.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/complete` | Chuyển ĐMH sang Hoàn thành khi mọi dòng đã xong hoặc đã hủy. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/copy` | Nhân bản một ĐMH thành đơn Nháp mới. | `purchase_order.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-lines/finalize` | bao-CR-469 — Quyết toán NHIỀU dòng chi phí một lượt (tick chọn, hoặc chốt hết). | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-stage/advance` | Chốt Tạm tính / Quyết toán. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-stage/reopen` | Mở lại bộ chi phí về giai đoạn thấp hơn — cần quyền duyệt + lý do. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/finalize` | Quyết toán RIÊNG một dòng chi phí (hóa đơn khoản đó về trước). | `purchase_order.write` |  |  |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/reopen` | Mở lại một dòng đã quyết toán riêng — cần quyền duyệt + lý do. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-orders/{pid}/document-status` | Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành). | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/items/{item_id}/progress` | Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/print` | Dữ liệu in một ĐMH (người ký, công ty, dòng hàng). | `purchase_order.print` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/purchase-request` | Phiếu YCMH nguồn của đơn, đã cắt còn đúng các dòng hàng có trên đơn — bao-CR-314. | `purchase_order.print` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/purchasing-print` | Dữ liệu "Mẫu thu mua" của màn In YCMH từ ĐMH: người đề xuất, quản lý trực tiếp, NCC và dòng hàng theo ĐMH. | `purchase_order.read` | `_in_scope` (đọc, ngoài phạm vi 404); NCC che khi thiếu `supplier.read` | v1 `PrintPurchaseRequest`, v2 `procurement` (duoc-CR-777) |
| POST | `/api/purchase-orders/{pid}/reject` | Từ chối ĐMH đang chờ duyệt (đơn chuyển Đã hủy) kèm lý do, báo người tạo. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/reopen` | Mở lại ĐMH đã hoàn thành để xử lý tiếp. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/return` | Trả ĐMH đang chờ duyệt về người tạo để sửa, kèm lý do. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/submit` | Gửi duyệt ĐMH ở trạng thái Nháp hoặc Bị trả lại; báo thiếu nhà cung cấp hay dòng hàng. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/unapprove` | Hủy duyệt — đơn về Nháp để sửa rồi gửi duyệt lại (CR-108, phiếu hỗ trợ TK19082604). | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress` | Bảng tiến độ đơn mua hàng theo từng dòng, có lọc và phân trang; cột NCC ẩn với người không được xem. | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress/export/xlsx` | CR-068 — xuất Excel màn Tiến độ mua hàng theo đúng bộ lọc + cột đang hiện. | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi với bảng. | `báo cáo 4` |  | tự dò: v2 `report` |
| GET | `/api/purchase-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ mua hàng (P03) — cùng bộ lọc với `/summary`. | `báo cáo 4` |  | tự dò: v2 `report` |
| GET | `/api/purchase-requests` | Danh sách yêu cầu mua hàng (YCMH) trong phạm vi được xem, có lọc và phân trang. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests` | Tạo YCMH mới ở trạng thái Nháp; cụm nhà cung cấp thu mua chỉ người có quyền sửa NCC mới ghi. | `purchase_request.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests` | Xóa nhiều YCMH theo danh sách id trong phạm vi được xóa. | `purchase_request.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCMH, mỗi dòng hàng một hàng. | `purchase_request.export` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_request.read` |  |  |
| GET | `/api/purchase-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/meta/dept-head-candidates` | CR-071 — cùng danh sách nhưng tra theo PHÒNG BAN, cho màn TẠO MỚI (chưa có id phiếu). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}` | Chi tiết một YCMH; người chỉ phụ trách một số dòng chỉ thấy dòng của mình. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}` | Sửa YCMH; chỉ người tạo khi phiếu còn sửa được, hoặc người có quyền sửa. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests/{pid}` | Xóa một YCMH. | `purchase_request.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/approve` | Duyệt YCMH; phiếu thuộc diện bỏ qua điều phối thì tự chuyển sang bước kế. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_request.read` |  |  |
| PATCH | `/api/purchase-requests/{pid}/assign` | Giao người phụ trách mua cho YCMH đã duyệt và báo chuông người được giao. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho phiếu này: đi theo ô "Phòng xử lý" (xem `category_assignee.service.assignable_staff`). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/cancel` | Hủy YCMH kèm lý do và báo người tạo. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/clone` | Nhân bản một YCMH thành phiếu Nháp mới (tên cũ của đường `/copy`, giữ cho màn cũ). | `purchase_request.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/complete` | Chuyển YCMH sang Hoàn thành. | `purchase_request.cancel` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/copy` | Nhân bản một YCMH thành phiếu Nháp mới. | `purchase_request.create` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/dept-head-candidates` | CR-071 — những người duyệt được bước 1 phiếu này, để ô "Trưởng bộ phận" cho chọn. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/dispatch` | CR-034 — Duyệt lần 2 phía thu mua (điều phối): tự động phân bổ NSTM rồi mở khóa tạo ĐMH. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/item-status` | Cập nhật trạng thái một dòng hàng của YCMH; quản lý sửa mọi dòng, người phụ trách chỉ dòng của mình. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/available-survey-lines` | Kho phương án: các dòng khảo sát SẢN PHẨM đã duyệt, để NSTM nhặt vào dòng YCMH. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/options` | Danh sách phương án (giá, nhà cung cấp) của một dòng YCMH. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options` | Gắn một phương án vào dòng YCMH lấy từ dòng phiếu khảo sát đã duyệt. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/manual` | Phương án NSTM gõ tay — dùng khi giá biến động liên tục, kho khảo sát không kịp theo, NSTM phải đưa ra một mức hợp lý cho người yêu cầu chốt. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/reopen` | Người yêu cầu / quản lý MỞ LẠI một dòng đã chốt hoàn thành để NSTM sửa tiếp (khuôn "Cần khảo sát lại" của YCBG). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | Sửa một phương án của dòng YCMH; dòng đã chốt thì chỉ thu mua có quyền xem NCC mới sửa được giá. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | Gỡ một phương án khỏi dòng YCMH chưa chốt. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/choose` | Chốt phương án cho dòng — bấm lại đúng phương án đang chốt thì BỎ chốt. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/details` | bao-CR-583 — sửa thông tin PHƯƠNG ÁN 0 / NHẬP TAY (tên hàng, mã VTBB, NCC, giá, giao hàng…), ở màn xử lý lẫn màn chọn. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/supplier` | H.10.4 — điền/sửa NCC trên PHƯƠNG ÁN 0 / nhập tay, dùng được cả SAU khi dòng đã chốt hoàn thành (đúng một khe nới, cố ý KHÔNG gọi `ensure_line_not_done`). | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/zero/reset` | bao-CR-583 — "Khôi phục ban đầu": phương án 0 về đúng như dòng yêu cầu lúc sinh. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/assign-supplier` | H.10.5 — "Áp 1 NCC cho nhiều dòng" trên màn chọn: tick các dòng đang thiếu NCC, chọn một NCC, áp một phát vào PHƯƠNG ÁN ĐANG CHỌN của từng dòng (giá sửa kèm theo dòng nếu cần). | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/choice-complete` | bao-CR-419 — NGƯỜI YÊU CẦU "Chốt xong lựa chọn" cho cả phiếu, rồi chuông báo NSTM của từng dòng vào gom đơn. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/complete` | NSTM "Chốt hoàn thành xử lý" phần của mình trên phiếu (đợt 3b, khuôn YCBG `complete_sr`): mọi dòng mình phụ trách phải có phương án hoặc được tick chốt rỗng. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/generate-orders` | H.10.6 — "Tạo đơn mua hàng theo phương án": gom phương án ĐANG CHỌN của từng dòng theo NCC thành các ĐMH NHÁP một lượt; dòng thiếu NCC gom vào một đơn riêng. | `purchase_order.create` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/order-progress` | Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ các ĐMH cùng mã PYC. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/reject` | Từ chối YCMH kèm lý do và báo người tạo. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/return` | Trả YCMH về người yêu cầu để sửa; chỉ khi phiếu chờ duyệt hoặc đã duyệt mà chưa dòng nào lên đơn mua. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện với chuyển phòng, đích là phòng thu mua mặc định (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo). | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/submit` | Gửi duyệt YCMH ở trạng thái Nháp hoặc Bị trả lại. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ (đường 2): gỡ NSTM mọi dòng, đổi phòng, phiếu về "Đã duyệt (chưa điều phối)" để phòng nhận điều phối lại. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/urgent` | Bật/tắt cờ Đơn gấp (cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH cùng pr_code. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| GET | `/api/suppliers` | Danh sách nhà cung cấp, có lọc, sắp xếp và phân trang. | `supplier.read` |  | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| POST | `/api/suppliers` | Thêm nhà cung cấp. | `supplier.create` |  | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| DELETE | `/api/suppliers` | Xóa nhiều nhà cung cấp theo danh sách id (tham số `ids` cách nhau dấu phẩy). | `supplier.delete` | `apply_scope` | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| GET | `/api/suppliers/export/csv` | Xuất nhà cung cấp ra tệp CSV theo bộ lọc hoặc theo các id đã chọn. | `supplier.export` | `apply_scope` |  |
| POST | `/api/suppliers/import/csv` | Nhập nhà cung cấp hàng loạt từ tệp CSV; mã trống thì hệ tự sinh. | `supplier.import` |  |  |
| GET | `/api/suppliers/{code}/purchase-history` | Lịch sử mua từ một nhà cung cấp. | `supplier.read` |  | tự dò: v2 `production` |
| GET | `/api/suppliers/{sid}` | Xem một nhà cung cấp theo id. | `supplier.read` |  | tự dò: v2 `production` |
| PATCH | `/api/suppliers/{sid}` | Sửa nhà cung cấp; chỉ ghi các ô gửi lên. | `supplier.write` |  | tự dò: v2 `production` |
| DELETE | `/api/suppliers/{sid}` | Xóa một nhà cung cấp trong phạm vi được xóa. | `supplier.delete` | `get_scoped` | tự dò: v2 `production` |
| GET | `/api/survey-progress` | Bảng tiến độ báo giá theo từng dòng YCBG, có lọc và phân trang; cột NCC ẩn với người không được xem. | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/survey-progress/export/xlsx` | Xuất Excel theo đúng bộ lọc + cột đang hiện (cùng lối với màn Tiến độ mua hàng). | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/survey-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi (cả lọc dòng theo NSTM) với bảng. | `báo cáo 3` |  | tự dò: v2 `report` |
| GET | `/api/survey-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ báo giá (P03) — cùng bộ lọc với `/summary`. | `báo cáo 3` |  | tự dò: v2 `report` |
| GET | `/api/survey-report/by-supplier` | Task 9: khảo sát của 1 NCC — KSNCC (theo tax_code) + KSSP (theo supplier_code). | `survey.read` | `apply_scope` | tự dò: v2 `production`, v2 dùng chung |
| GET | `/api/survey-report/lines` | Bảng dòng khảo sát cho báo cáo khảo sát, lọc theo loại, phân loại, NCC, ngày và người khảo sát. | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/survey-report/summary` | Tổng hợp Báo cáo khảo sát — cùng phạm vi + bộ lọc với `/lines`. | `báo cáo 5`, `survey.read` | `apply_scope` | tự dò: v2 `report` |
| GET | `/api/survey-report/summary/export` | Xuất Excel bản THEO KỲ của Báo cáo khảo sát (P03) — cùng bộ lọc với `/summary`. | `báo cáo 5`, `survey.export` | `apply_scope` | tự dò: v2 `report` |
| GET | `/api/survey-requests` | Danh sách yêu cầu báo giá (YCBG) trong phạm vi được xem, có lọc và phân trang. | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests` | Tạo YCBG mới ở trạng thái Nháp. | `survey_request.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests` | Xóa nhiều YCBG theo danh sách id trong phạm vi được xóa. | `survey_request.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCBG: mỗi dòng yêu cầu một hàng, kèm phương án đã chốt. | `survey_request.export` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `survey_request.read` |  |  |
| GET | `/api/survey-requests/meta/department-managers` | bao-CR-552 — trưởng phòng mọi phòng đang hoạt động, cho ô "Trưởng bộ phận" YCBG của bản v1 chọn được (v2 dựng cùng bộ từ danh mục phòng ban). | `survey_request.read` |  |  |
| GET | `/api/survey-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không xem được DS nhân sự) tự điền TBP. | `survey_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}` | Chi tiết một YCBG; trưởng bộ phận được chỉ đích danh cũng xem được. | `survey_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}` | Sửa YCBG; chỉ người tạo khi phiếu còn sửa được, hoặc người có quyền sửa. | `survey_request.read` |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests/{sid}` | Xóa một YCBG. | `survey_request.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/approve` | Duyệt YCBG và ghi người duyệt lên bản in. | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `survey_request.read` |  |  |
| GET | `/api/survey-requests/{sid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho YCBG này: đi theo ô "Phòng xử lý" (cùng luật YCMH). | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/cancel` | TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled. | `survey_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/clone` | Nhân bản 1 YCKS thành phiếu nháp mới (sao chép header + dòng). | `survey_request.create` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/complete` | Chốt hoàn thành khảo sát — NSTM chốt PHẦN DÒNG CỦA MÌNH; phiếu -> survey_done khi MỌI dòng (mọi NSTM) đã có option HOẶC được chốt rỗng. | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/create-prs` | Người YC tạo Yêu cầu mua hàng từ các phương án đã chọn (gom theo NCC). | `survey_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/finalize` | Chuyển Hoàn thành (pr_created/survey_done → done). | `survey_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/assignee` | Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). | `survey_request.process` | `scope_condition` | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/lines/{line_id}/available-survey-lines` | Dòng phiếu khảo sát đã duyệt có thể gắn làm phương án cho một dòng YCBG; phải có ít nhất một bộ lọc. | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/line-status` | Task 2: người YC / cùng phòng ban đổi trạng thái dòng khảo sát ("" chưa xác định · cần khảo sát lại · hoàn thành). | `survey_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/lines/{line_id}/options` | Gắn phương án cho một dòng YCBG khi phiếu đang xử lý hoặc đã khảo sát. | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | Sửa một phương án của dòng YCBG; chỉ người phụ trách dòng. | đăng nhập |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | Gỡ một phương án của dòng YCBG chưa tạo YCMH. | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}/choose` | Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát). | `survey_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/status` | Đổi Tình trạng dòng (is_completed). | `survey_request.write` |  |  |
| GET | `/api/survey-requests/{sid}/process` | Trang *Xử lý khảo sát* (CR-222). | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/reject` | TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được). bao-CR-554: trả được cả phiếu đã duyệt / đang xử lý khi việc khảo sát chưa bắt đầu. | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/result` | Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field). | `survey_request.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện, đích là phòng thu mua mặc định (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo). | `survey_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/submit` | Gửi duyệt YCBG ở trạng thái Nháp hoặc Bị trả lại. | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/sync-options` | Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCKS này (khớp phân loại). | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ: gỡ NSTM + ngày tiếp nhận mọi dòng, đổi phòng; trạng thái giữ nguyên (YCBG không có bước điều phối riêng). | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/surveys` | Danh sách phiếu khảo sát trong phạm vi được xem; tìm theo mã phiếu hoặc mã hàng. | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/surveys` | Tạo phiếu khảo sát mới. | `survey.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/surveys` | Xóa nhiều phiếu khảo sát theo danh sách id trong phạm vi được xóa. | `survey.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/surveys/{sid}` | Chi tiết một phiếu khảo sát. | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}` | Sửa phiếu khảo sát. | `survey.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/surveys/{sid}` | Xóa phiếu khảo sát ở trạng thái Nháp, Bị trả lại hoặc Đã hủy. | `survey.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/approve` | Duyệt phiếu khảo sát khi mọi dòng đã có quyết định; đồng bộ phương án sang YCBG. | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/cancel` | Từ chối phiếu đang chờ duyệt (khóa hẳn) — người duyệt thao tác. | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/clone` | Nhân bản phiếu khảo sát thành phiếu Nháp mới. | `survey.create` |  | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}/line-approve` | Lưu quyết định duyệt từng dòng của phiếu khảo sát và đồng bộ phương án sang YCBG. | `survey.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}/lines/{table}/{line_id}/fill` | Bổ sung 1 dòng đang 'Thiếu thông tin' (kể cả phiếu đã duyệt) — có guard trong service. | `survey.write` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/reject` | Trả về phiếu khảo sát đang chờ duyệt hoặc đã duyệt; gỡ các phương án đã đẩy sang YCBG. | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/submit` | Gửi duyệt phiếu khảo sát và báo người duyệt. | `survey.write` |  | tự dò: v2 `procurement` |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
| 03/11/2026 | duoc-CR-719 | YCTT nguồn `leave_encashment` (Thanh toán nghỉ phép): mọi đường `/api/payment-requests` lọc thêm chốt xem D1 trong `scope_condition` (cần `leave_encashment.read` phủ phiếu nguồn); `POST /` từ chối nguồn này; `PATCH` chỉ sửa một dòng tiền; `submit` 400 khi tiền 0; `DELETE` (một và nhiều), `refund`, `refresh-from-payables` chặn 400; `print` trả `payee` + `bank_hidden`; thêm trường `payee_employee_id`, `source_ref_id`, khối `leave_encashment`. Xem `doc/erp/hrm/02-nghi-phep.md` §16 |
| 16/11/2026 | bao-CR-759 | Dòng YCMH thêm trường `warehouse_code` (mã kho, khớp `tab_warehouse.code`) ở `GET/POST/PATCH /api/purchase-requests`, `POST /api/purchase-requests/{pid}/copy` và công cụ MCP `procurement_doc_read`. Trường `warehouse` (tên kho) giữ nguyên. Luật lưu: gửi mã khớp danh mục thì máy chủ điền tên theo danh mục; chỉ gửi tên (client cũ, trợ lý AI) thì máy chủ suy mã theo tên khớp đúng; dòng đang có mà tên không đổi, không gửi mã thì giữ mã cũ |
| 16/11/2026 | bao-CR-758 | `POST /api/purchase-orders` ghi `approver_employee_id` người lập chọn ở form tạo (trước đây bị bỏ rơi, chỉ `PATCH` mới ghi) |
| 20/11/2026 | duoc-CR-784 | Thêm khóa quyền `packaging_cost` (Giá bao bì) và các đường: `POST /api/packaging-cost/impact` (+ `/impact/export`), `GET /api/packaging-cost/price-list` (+ `/export`; mỗi dòng kèm `last_purchase_price` / `last_purchase_date` / `prev_purchase_price` = hai lần mua có giá gần nhất), `GET /api/packaging-cost/code-options`; CRUD `/api/packaging-boms` (định mức bao bì), `/api/product-price-quotes` (báo giá), `/api/product-price-limits` (ngưỡng sàn / trần). Phạm vi theo pháp nhân đo trên sổ giá `tab_product_price_ledger.company_id`; ba CRUD là danh mục dùng chung nên không lọc theo pháp nhân. Nhập định mức bao bì từ `DATA_CHAI.xlsx` qua `/api/imports` với `module=4` (cần `import.create` + `packaging_cost.create`; chưa hoàn tác được). Hợp đồng đầy đủ: `doc/erp/thu-mua/plans/261120-tac-dong-gia-bao-bi/phase-04-be-api-tac-dong-bang-gia-xuat-excel.md` |
| 20/11/2026 | duoc-CR-784 | Thêm `GET /api/packaging-cost/last-prices` (+ `/export`): tab Giá mua gần nhất, mỗi mã VTBB một dòng với `purchases[]` (n lần mua có giá gần nhất trước: `date`, `supplier_code`, `supplier`, `qty`, `price`), `v12` / `v1n` (tỷ số biến động lần 1 so lần 2 / lần n), `avg`, `purchase_count`. Tham số: `n` (2–10, mặc định 5), `q`, `group`, `supplier` (lặp được; giữ mã có nhà cung cấp đó trong n lần đang hiện), `date_from` / `date_to` (chỉ các lần mua trong khoảng được xếp hạng), `trend=all\|up\|down\|flat` (lần 1 so lần 2), `min_pct` (\|biến động\| >= %), `only_priced` (mặc định true), `bom_only`, `scope=bom\|all`, `sort_by` (`code, name, group, unit, purchase_count, last_price, last_date, v12, v1n, avg` hoặc `p{k}_price` / `p{k}_date`), `sort_dir`, `page`, `page_size`; `/export` thêm `show_qty`. Trả thêm `groups[{group,count}]` và `suppliers[{code,name}]` cho chip nhóm / ô chọn nhà cung cấp. Quyền `packaging_cost.read` / `.export`, phạm vi pháp nhân như Bảng giá. Cố định 5 truy vấn bất kể số mã, `n` hay bộ lọc |
| 20/11/2026 | duoc-CR-784 | Hiệu năng khi sổ giá lớn (đo trên 650 nghìn dòng sổ giá + 20 nghìn dòng định mức, từ 5 – 20 giây xuống dưới 1 giây). `POST /api/packaging-cost/impact`: bảng sản phẩm phân trang / tìm / xếp tại máy chủ — thân thêm `page` (>= 1, mặc định 1), `page_size` (1 – 500, mặc định 50), `sort_by` (`hh_code, hh_name, carton_qty, cost_old_bottle, cost_applied_bottle, diff_bottle, diff_carton, cost_old_carton, cost_applied_carton, pct, trend`; khóa lạ rơi về `hh_code`), `sort_dir` (`asc\|desc`), `q` (<= 100 ký tự; mã HH, tên, tên pháp lý, mã thành phần, không phân biệt dấu); kết quả thêm `products_total` (số dòng sau lọc `q`) và `products` chỉ còn TRANG được hỏi, còn `kpis` + `selected` vẫn tính trên toàn bộ tập bị ảnh hưởng. `POST /impact/export` bỏ qua `page` / `page_size` (xuất đủ mọi dòng, trần số dòng như mọi lần xuất) nhưng theo `q` + xếp. `GET /price-list`: xếp theo `code, name, group, unit` (và `scope=bom`, không `breach_only`) thì lọc + xếp + cắt trang trước rồi mới tính giá cho đúng mã của trang; `GET /code-options` không đổi hợp đồng (chỉ lấy giá mới, bỏ ngưỡng). Số truy vấn: `impact` 6, `price-list` <= 7, `last-prices` 5. Chỉ mục sổ giá đổi thành `ix_ppl_code_latest (product_code, price_date, doc_id, id, price, company_id)` (thay `ix_ppl_code_date`), nằm trong migration `pkgcost784` |
| 21/11/2026 | duoc-CR-784 | Thêm `GET /api/packaging-cost/history` (+ `/export`) và `GET /api/packaging-cost/hh-options`: tab Lịch sử mua hàng đọc thẳng sổ giá (cả hai nguồn, `source_type` 2 = dòng ĐMH đang mở; dòng đơn giá 0 vẫn hiện nhưng không tính vào KPI / biểu đồ). Tham số: `mode=code\|product`, `codes` / `hh_codes` (lặp được, tối đa 200; rỗng = mọi mã VTBB / mọi sản phẩm có định mức, chế độ sản phẩm mở rộng qua `tab_packaging_bom` và mỗi dòng kèm `roles`), `q`, `supplier` (lặp được), `date_from` / `date_to`, `sort_by` (`date, code, name, supplier, qty, price, amount, vat, source`, ô trống xuống cuối), `sort_dir`, `page`, `page_size` (<= 500). Mỗi dòng kèm `prev_price` / `diff` / `pct` so với lần mua có giá liền trước của cùng mã (không phụ thuộc bộ lọc), `seq`, `doc_id` / `po_code`. Trả thêm `stats` (`purchase_count, priced_count, qty_total, weighted_avg` gia quyền, `min, max, supplier_count, first_date, last_date`), `series` (đúng một mã: tối đa 1.000 điểm giá cũ → mới) và `suppliers`. Quyền `packaging_cost.read` / `.export`, phạm vi pháp nhân như Bảng giá. Cố định 3 – 5 truy vấn bất kể số mã, số dòng hay bộ lọc |
