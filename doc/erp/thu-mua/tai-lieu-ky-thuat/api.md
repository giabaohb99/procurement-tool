# TÀI LIỆU API — THU MUA

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `category_assignee`, `contract`, `execution_report`, `payable`, `payment_request`, `purchase_cost_type`, `purchase_history`, `purchase_order`, `purchase_progress`, `purchase_request`, `supplier`, `survey`, `survey_progress`, `survey_report`, `survey_request`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `purchase_request`, `survey_request`, `survey`, `survey_progress`, `purchase_order`, `purchase_progress`, `purchase_history`, `payable`, `payment_request`, `supplier`, `contract`, `category_assignee`; danh mục dựng bằng `make_crud_router`: `/api/po-cost-types`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/category-assignees` | Danh sách phân công NSTM — 1 query JOIN (hết N+1), phân trang + sort tại DB. | `category_assignee.read` |  | tự dò: v2 `procurement` |
| POST | `/api/category-assignees` | create | `category_assignee.create` |  | tự dò: v2 `procurement` |
| POST | `/api/category-assignees/bulk` | bulk | `category_assignee.create` |  | tự dò: v2 `procurement` |
| GET | `/api/category-assignees/{cid}` | get | `category_assignee.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/category-assignees/{cid}` | update | `category_assignee.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/category-assignees/{cid}` | delete | `category_assignee.delete` |  | tự dò: v2 `procurement` |
| GET | `/api/contracts` | list | `contract.read` | `apply_scope` | tự dò: v2 `production` |
| POST | `/api/contracts` | create | `contract.create` | `apply_scope` | tự dò: v2 `production` |
| DELETE | `/api/contracts` | bulk delete contracts | `contract.delete` | `apply_scope` | tự dò: v2 `production` |
| GET | `/api/contracts/meta/types` | Bộ loại hợp đồng cố định cho FE dựng ô chọn (CR-118). | `contract.read` |  | tự dò: v2 `production` |
| GET | `/api/contracts/{cid}` | get | `contract.read` |  | tự dò: v2 `production` |
| PATCH | `/api/contracts/{cid}` | update | `contract.write` |  | tự dò: v2 `production` |
| DELETE | `/api/contracts/{cid}` | Xóa MỀM một hợp đồng (ai-CR-177): đánh cờ `is_deleted` + mốc + người xóa. | `contract.delete` |  | tự dò: v2 `production` |
| GET | `/api/execution-report/{entity}/{owner_id}` | get report | đăng nhập |  | tự dò: v2 `procurement`, v2 dùng chung |
| DELETE | `/api/execution-report/{entity}/{owner_id}` | Xóa CẢ khối báo cáo — có thể HOÀN TÁC từ Lịch sử thao tác. | đăng nhập |  | tự dò: v2 `procurement`, v2 dùng chung |
| POST | `/api/execution-report/{entity}/{owner_id}/apply-template` | Nút "Tạo mẫu" trên một nút dòng hàng / một giai đoạn — đổ mẫu chung vào, cộng thêm, bỏ qua hồ sơ đã có. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/docs` | create doc | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/docs/bulk-delete` | delete docs | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | update doc | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | delete doc | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/first-doc` | create first doc | đăng nhập |  |  |
| GET | `/api/execution-report/{entity}/{owner_id}/first-doc-options` | Ô chọn của hộp "Thêm hồ sơ" khi khối còn trống: dòng hàng của chứng từ + 5 giai đoạn mặc định. | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/init` | init report | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/items` | create item | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | rename item | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | delete item | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/phases` | create phase | đăng nhập |  |  |
| PATCH | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | update phase | đăng nhập |  |  |
| DELETE | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | delete phase | đăng nhập |  |  |
| POST | `/api/execution-report/{entity}/{owner_id}/restore` | Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác. | đăng nhập |  |  |
| GET | `/api/execution-report/{entity}/{owner_id}/templates` | Ô chọn mẫu của hộp "Khởi tạo báo cáo mẫu" (duoc-CR-614). | đăng nhập |  |  |
| GET | `/api/payables` | list payables | `payable.read` |  | tự dò: v2 `finance`, v2 `procurement`, v2 `production` |
| GET | `/api/payables/export/xlsx` | Ticket #16 — xuất Excel danh sách Công nợ đúng bộ lọc + phạm vi màn hình. | `payable.export` |  | tự dò: v2 `finance` |
| GET | `/api/payables/summary` | Thẻ tổng hợp công nợ. | `payable.read` |  | tự dò: v2 `finance` |
| POST | `/api/payables/{pid}/offset-prepay` | CR-268 — kế toán cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước không gắn đơn) vào khoản công nợ này. | `payable.write` | `apply_scope` | tự dò: v2 `finance` |
| GET | `/api/payment-requests` | list | `payment_request.read` |  | tự dò: v2 `finance`, v2 `procurement` |
| POST | `/api/payment-requests` | create | `payment_request.create` | `apply_scope` | tự dò: v2 `finance`, v2 `procurement` |
| DELETE | `/api/payment-requests` | bulk delete requests | `payment_request.delete` | `apply_scope` | tự dò: v2 `finance`, v2 `procurement` |
| GET | `/api/payment-requests/export/xlsx` | bao-CR-525 — xuất Excel THEO DÒNG CHI TIẾT: phiếu đúng bộ lọc + phạm vi màn danh sách, mỗi dòng PO / hóa đơn một hàng, thông tin phiếu lặp lại (xem `export.py`). | `payment_request.export` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/hanging` | CR-268 — tiền treo (phiếu trả trước đã chi, chưa đối trừ/hoàn hết) của 1 NCC. | `payment_request.read` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/meta/department-managers` | bao-CR-553 — ô "Trưởng bộ phận" của YCTT: trưởng phòng mọi phòng (có Ban Giám đốc). | `payment_request.read` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}` | get | `payment_request.read` | `apply_scope` | tự dò: v2 `finance` |
| PATCH | `/api/payment-requests/{rid}` | update | `payment_request.write` |  | tự dò: v2 `finance` |
| DELETE | `/api/payment-requests/{rid}` | delete | `payment_request.delete` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/approve` | approve | `payment_request.approve` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/pay` | pay | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}/print` | print | `payment_request.print` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/refresh-from-payables` | bao-CR-509 — GHI số mới theo công nợ vào phiếu NHÁP (tính lại từ DB lúc ghi). | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/payment-requests/{rid}/refresh-preview` | bao-CR-509 — XEM TRƯỚC số mới của từng dòng theo công nợ hiện tại, KHÔNG ghi gì. | `payment_request.read` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/refund` | CR-268 — ghi nhận NCC HOÀN TIỀN phần treo của phiếu trả trước đã chi. | `payment_request.write` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/reject` | Từ chối phiếu yêu cầu thanh toán (khóa) — người duyệt thao tác. | `payment_request.approve` |  | tự dò: v2 `finance` |
| POST | `/api/payment-requests/{rid}/submit` | submit | `payment_request.write` |  | tự dò: v2 `finance` |
| GET | `/api/po-cost-types` | Danh sách danh mục Loại chi phí thu mua, có lọc và phân trang. | `purchase_cost_type.read` | `apply_scope` | tự dò: v2 `procurement`, v2 dùng chung |
| POST | `/api/po-cost-types` | Thêm một dòng danh mục Loại chi phí thu mua; chặn trùng mã, ghi nhật ký. | `purchase_cost_type.create` |  | tự dò: v2 `procurement`, v2 dùng chung |
| GET | `/api/po-cost-types/export/csv` | Xuất danh mục Loại chi phí thu mua ra tệp CSV theo bộ lọc đang chọn. | `purchase_cost_type.export` | `apply_scope` |  |
| GET | `/api/po-cost-types/{oid}` | Xem một dòng danh mục Loại chi phí thu mua theo id. | `purchase_cost_type.read` | `get_scoped` |  |
| PATCH | `/api/po-cost-types/{oid}` | Sửa một dòng danh mục Loại chi phí thu mua; chỉ ghi các ô gửi lên, ghi nhật ký. | `purchase_cost_type.write` | `get_scoped` |  |
| DELETE | `/api/po-cost-types/{oid}` | Xóa một dòng danh mục Loại chi phí thu mua; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `purchase_cost_type.delete` | `get_scoped` |  |
| GET | `/api/products/{code}/purchase-history` | product purchase history | `product.read` |  | tự dò: v2 `procurement`, v2 `production` |
| GET | `/api/purchase-orders` | list po | `purchase_order.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders` | create po | `purchase_order.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-orders` | bulk delete pos | `purchase_order.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/export/xlsx` | CR-068 — xuất Excel danh sách ĐMH, cột dòng hàng lấy đúng bộ cột màn Tiến độ mua hàng (một hàng = một lần giao). | `purchase_order.export` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/lines` | Danh sách DÒNG HÀNG của các đơn mua hàng — dùng cho trang chi tiết Kho. | `purchase_order.read` | `apply_scope` |  |
| GET | `/api/purchase-orders/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_order.read` |  |  |
| GET | `/api/purchase-orders/{pid}` | get po | `purchase_order.read` | `apply_scope` | tự dò: v2 `procurement`, v2 `system` |
| PATCH | `/api/purchase-orders/{pid}` | update po | `purchase_order.write` |  | tự dò: v2 `procurement`, v2 `system` |
| DELETE | `/api/purchase-orders/{pid}` | delete po | `purchase_order.delete` |  | tự dò: v2 `procurement`, v2 `system` |
| POST | `/api/purchase-orders/{pid}/approve` | approve po | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_order.read` |  |  |
| POST | `/api/purchase-orders/{pid}/cancel` | cancel po | `purchase_order.cancel` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/clone` | Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS). | `purchase_order.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/complete` | complete po | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/copy` | copy po | `purchase_order.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-lines/finalize` | bao-CR-469 — Quyết toán NHIỀU dòng chi phí một lượt (tick chọn, hoặc chốt hết). | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-stage/advance` | Chốt Tạm tính / Quyết toán. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/cost-stage/reopen` | Mở lại bộ chi phí về giai đoạn thấp hơn — cần quyền duyệt + lý do. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/finalize` | Quyết toán RIÊNG một dòng chi phí (hóa đơn khoản đó về trước). | `purchase_order.write` |  |  |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/reopen` | Mở lại một dòng đã quyết toán riêng — cần quyền duyệt + lý do. | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-orders/{pid}/document-status` | Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành). | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/items/{item_id}/progress` | Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH. | `purchase_order.write` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/print` | print po | `purchase_order.print` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-orders/{pid}/purchase-request` | Phiếu YCMH nguồn của đơn, đã cắt còn đúng các dòng hàng có trên đơn — bao-CR-314. | `purchase_order.print` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/reject` | reject po | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/reopen` | reopen po | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/return` | return po | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/submit` | submit po | `purchase_order.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-orders/{pid}/unapprove` | Hủy duyệt — đơn về Nháp để sửa rồi gửi duyệt lại (CR-108, phiếu hỗ trợ TK19082604). | `purchase_order.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress` | list progress | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress/export/xlsx` | CR-068 — xuất Excel màn Tiến độ mua hàng theo đúng bộ lọc + cột đang hiện. | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi với bảng. | `báo cáo 4` |  | tự dò: v2 `report` |
| GET | `/api/purchase-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ mua hàng (P03) — cùng bộ lọc với `/summary`. | `báo cáo 4` |  | tự dò: v2 `report` |
| GET | `/api/purchase-requests` | list pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests` | create pr | `purchase_request.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests` | bulk delete prs | `purchase_request.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCMH, mỗi dòng hàng một hàng. | `purchase_request.export` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_request.read` |  |  |
| GET | `/api/purchase-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/meta/dept-head-candidates` | CR-071 — cùng danh sách nhưng tra theo PHÒNG BAN, cho màn TẠO MỚI (chưa có id phiếu). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}` | get pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}` | update pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests/{pid}` | delete pr | `purchase_request.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/approve` | approve pr | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_request.read` |  |  |
| PATCH | `/api/purchase-requests/{pid}/assign` | assign pr | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho phiếu này: đi theo ô "Phòng xử lý" (xem `category_assignee.service.assignable_staff`). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/cancel` | cancel pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/clone` | clone pr | `purchase_request.create` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/complete` | complete pr | `purchase_request.cancel` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/copy` | copy pr | `purchase_request.create` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/dept-head-candidates` | CR-071 — những người duyệt được bước 1 phiếu này, để ô "Trưởng bộ phận" cho chọn. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/dispatch` | CR-034 — Duyệt lần 2 phía thu mua (điều phối): tự động phân bổ NSTM rồi mở khóa tạo ĐMH. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/item-status` | update item status | `purchase_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/available-survey-lines` | Kho phương án: các dòng khảo sát SẢN PHẨM đã duyệt, để NSTM nhặt vào dòng YCMH. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/options` | list options | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options` | add option from survey | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/manual` | Phương án NSTM gõ tay — dùng khi giá biến động liên tục, kho khảo sát không kịp theo, NSTM phải đưa ra một mức hợp lý cho người yêu cầu chốt. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/reopen` | Người yêu cầu / quản lý MỞ LẠI một dòng đã chốt hoàn thành để NSTM sửa tiếp (khuôn "Cần khảo sát lại" của YCBG). | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | update option | `purchase_request.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | delete option | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/choose` | Chốt phương án cho dòng — bấm lại đúng phương án đang chốt thì BỎ chốt. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/details` | bao-CR-583 — sửa thông tin PHƯƠNG ÁN 0 / NHẬP TAY (tên hàng, mã VTBB, NCC, giá, giao hàng…), ở màn xử lý lẫn màn chọn. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/supplier` | H.10.4 — điền/sửa NCC trên PHƯƠNG ÁN 0 / nhập tay, dùng được cả SAU khi dòng đã chốt hoàn thành (đúng một khe nới, cố ý KHÔNG gọi `ensure_line_not_done`). | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/zero/reset` | bao-CR-583 — "Khôi phục ban đầu": phương án 0 về đúng như dòng yêu cầu lúc sinh. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/assign-supplier` | H.10.5 — "Áp 1 NCC cho nhiều dòng" trên màn chọn: tick các dòng đang thiếu NCC, chọn một NCC, áp một phát vào PHƯƠNG ÁN ĐANG CHỌN của từng dòng (giá sửa kèm theo dòng nếu cần). | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/choice-complete` | bao-CR-419 — NGƯỜI YÊU CẦU "Chốt xong lựa chọn" cho cả phiếu, rồi chuông báo NSTM của từng dòng vào gom đơn. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/complete` | NSTM "Chốt hoàn thành xử lý" phần của mình trên phiếu (đợt 3b, khuôn YCBG `complete_sr`): mọi dòng mình phụ trách phải có phương án hoặc được tick chốt rỗng. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/options/generate-orders` | H.10.6 — "Tạo đơn mua hàng theo phương án": gom phương án ĐANG CHỌN của từng dòng theo NCC thành các ĐMH NHÁP một lượt; dòng thiếu NCC gom vào một đơn riêng. | `purchase_order.create` |  | tự dò: v2 `procurement` |
| GET | `/api/purchase-requests/{pid}/order-progress` | Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ các ĐMH cùng mã PYC. | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/reject` | reject pr | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/return` | return pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện với chuyển phòng, đích là phòng thu mua mặc định (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo). | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/submit` | submit pr | `purchase_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/purchase-requests/{pid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ (đường 2): gỡ NSTM mọi dòng, đổi phòng, phiếu về "Đã duyệt (chưa điều phối)" để phòng nhận điều phối lại. | `purchase_request.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/purchase-requests/{pid}/urgent` | Bật/tắt cờ Đơn gấp (cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH cùng pr_code. | `purchase_request.write` |  | tự dò: v2 `procurement` |
| GET | `/api/suppliers` | list suppliers | `supplier.read` |  | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| POST | `/api/suppliers` | create supplier | `supplier.create` |  | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| DELETE | `/api/suppliers` | bulk delete suppliers | `supplier.delete` | `apply_scope` | tự dò: v2 `dossier`, v2 `finance`, v2 `production`, v2 dùng chung |
| GET | `/api/suppliers/export/csv` | export suppliers csv | `supplier.export` | `apply_scope` |  |
| POST | `/api/suppliers/import/csv` | import suppliers csv | `supplier.import` |  |  |
| GET | `/api/suppliers/{code}/purchase-history` | supplier purchase history | `supplier.read` |  | tự dò: v2 `production` |
| GET | `/api/suppliers/{sid}` | get supplier | `supplier.read` |  | tự dò: v2 `production` |
| PATCH | `/api/suppliers/{sid}` | update supplier | `supplier.write` |  | tự dò: v2 `production` |
| DELETE | `/api/suppliers/{sid}` | delete supplier | `supplier.delete` | `get_scoped` | tự dò: v2 `production` |
| GET | `/api/survey-progress` | list progress | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/survey-progress/export/xlsx` | Xuất Excel theo đúng bộ lọc + cột đang hiện (cùng lối với màn Tiến độ mua hàng). | đăng nhập |  | tự dò: v2 `procurement` |
| GET | `/api/survey-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi (cả lọc dòng theo NSTM) với bảng. | `báo cáo 3` |  | tự dò: v2 `report` |
| GET | `/api/survey-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ báo giá (P03) — cùng bộ lọc với `/summary`. | `báo cáo 3` |  | tự dò: v2 `report` |
| GET | `/api/survey-report/by-supplier` | Task 9: khảo sát của 1 NCC — KSNCC (theo tax_code) + KSSP (theo supplier_code). | `survey.read` | `apply_scope` | tự dò: v2 `production`, v2 dùng chung |
| GET | `/api/survey-report/lines` | report lines | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/survey-report/summary` | Tổng hợp Báo cáo khảo sát — cùng phạm vi + bộ lọc với `/lines`. | `báo cáo 5`, `survey.read` | `apply_scope` | tự dò: v2 `report` |
| GET | `/api/survey-report/summary/export` | Xuất Excel bản THEO KỲ của Báo cáo khảo sát (P03) — cùng bộ lọc với `/summary`. | `báo cáo 5`, `survey.export` | `apply_scope` | tự dò: v2 `report` |
| GET | `/api/survey-requests` | list | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests` | create | `survey_request.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests` | bulk delete survey requests | `survey_request.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCBG: mỗi dòng yêu cầu một hàng, kèm phương án đã chốt. | `survey_request.export` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `survey_request.read` |  |  |
| GET | `/api/survey-requests/meta/department-managers` | bao-CR-552 — trưởng phòng mọi phòng đang hoạt động, cho ô "Trưởng bộ phận" YCBG của bản v1 chọn được (v2 dựng cùng bộ từ danh mục phòng ban). | `survey_request.read` |  |  |
| GET | `/api/survey-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không xem được DS nhân sự) tự điền TBP. | `survey_request.read` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}` | get | `survey_request.read` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}` | update | `survey_request.read` |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests/{sid}` | delete | `survey_request.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/approve` | approve | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `survey_request.read` |  |  |
| GET | `/api/survey-requests/{sid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho YCBG này: đi theo ô "Phòng xử lý" (cùng luật YCMH). | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/cancel` | TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled. | `survey_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/clone` | Nhân bản 1 YCKS thành phiếu nháp mới (sao chép header + dòng). | `survey_request.create` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/complete` | Chốt hoàn thành khảo sát — NSTM chốt PHẦN DÒNG CỦA MÌNH; phiếu -> survey_done khi MỌI dòng (mọi NSTM) đã có option HOẶC được chốt rỗng. | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/create-prs` | Người YC tạo Yêu cầu mua hàng từ các phương án đã chọn (gom theo NCC). | `survey_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/finalize` | Chuyển Hoàn thành (pr_created/survey_done → done). | `survey_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/assignee` | Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). | `survey_request.process` | `scope_condition` | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/lines/{line_id}/available-survey-lines` | available survey lines | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/line-status` | Task 2: người YC / cùng phòng ban đổi trạng thái dòng khảo sát ("" chưa xác định · cần khảo sát lại · hoàn thành). | `survey_request.write` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/lines/{line_id}/options` | add option | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | edit option | đăng nhập |  | tự dò: v2 `procurement` |
| DELETE | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | del option | đăng nhập |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}/choose` | Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát). | `survey_request.write` |  | tự dò: v2 `procurement` |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/status` | Đổi Tình trạng dòng (is_completed). | `survey_request.write` |  |  |
| GET | `/api/survey-requests/{sid}/process` | Trang *Xử lý khảo sát* (CR-222). | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/reject` | TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được). bao-CR-554: trả được cả phiếu đã duyệt / đang xử lý khi việc khảo sát chưa bắt đầu. | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/survey-requests/{sid}/result` | Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field). | `survey_request.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện, đích là phòng thu mua mặc định (bao-CR-524: ghi id thật của PBA017, không còn `0` = "Thu mua chung" ảo). | `survey_request.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/submit` | submit | `survey_request.read` |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/sync-options` | Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCKS này (khớp phân loại). | đăng nhập |  | tự dò: v2 `procurement` |
| POST | `/api/survey-requests/{sid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ: gỡ NSTM + ngày tiếp nhận mọi dòng, đổi phòng; trạng thái giữ nguyên (YCBG không có bước điều phối riêng). | `survey_request.approve` |  | tự dò: v2 `procurement` |
| GET | `/api/surveys` | list surveys | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| POST | `/api/surveys` | create | `survey.create` |  | tự dò: v2 `procurement` |
| DELETE | `/api/surveys` | bulk delete surveys | `survey.delete` | `apply_scope` | tự dò: v2 `procurement` |
| GET | `/api/surveys/{sid}` | get | `survey.read` | `apply_scope` | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}` | update | `survey.write` |  | tự dò: v2 `procurement` |
| DELETE | `/api/surveys/{sid}` | delete | `survey.delete` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/approve` | approve | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/cancel` | Từ chối phiếu đang chờ duyệt (khóa hẳn) — người duyệt thao tác. | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/clone` | clone | `survey.create` |  | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}/line-approve` | line approve | `survey.approve` |  | tự dò: v2 `procurement` |
| PATCH | `/api/surveys/{sid}/lines/{table}/{line_id}/fill` | Bổ sung 1 dòng đang 'Thiếu thông tin' (kể cả phiếu đã duyệt) — có guard trong service. | `survey.write` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/reject` | reject | `survey.approve` |  | tự dò: v2 `procurement` |
| POST | `/api/surveys/{sid}/submit` | submit | `survey.write` |  | tự dò: v2 `procurement` |

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
