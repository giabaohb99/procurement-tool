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

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `purchase_request`, `survey_request`, `survey`, `survey_progress`, `purchase_order`, `purchase_progress`, `purchase_history`, `payable`, `payment_request`, `supplier`, `contract`, `category_assignee`; danh mục dựng bằng `make_crud_router`: `/api/po-cost-types`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| DELETE | `/api/purchase-requests` | bulk delete prs | `purchase_request.delete` | `apply_scope` | |
| GET | `/api/purchase-requests` | list pr | `purchase_request.read` |  | |
| POST | `/api/purchase-requests` | create pr | `purchase_request.create` |  | |
| GET | `/api/purchase-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCMH, mỗi dòng hàng một hàng. | `purchase_request.export` |  | |
| GET | `/api/purchase-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_request.read` |  | |
| GET | `/api/purchase-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không được xem DS nhân sự) tự điền TBP. | `purchase_request.read` |  | |
| GET | `/api/purchase-requests/meta/dept-head-candidates` | CR-071 — cùng danh sách nhưng tra theo PHÒNG BAN, cho màn TẠO MỚI (chưa có id phiếu). | `purchase_request.read` |  | |
| DELETE | `/api/purchase-requests/{pid}` | delete pr | `purchase_request.delete` |  | |
| GET | `/api/purchase-requests/{pid}` | get pr | `purchase_request.read` |  | |
| PATCH | `/api/purchase-requests/{pid}` | update pr | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/approve` | approve pr | `purchase_request.approve` |  | |
| GET | `/api/purchase-requests/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_request.read` | `apply_scope` | |
| PATCH | `/api/purchase-requests/{pid}/assign` | assign pr | `purchase_request.approve` |  | |
| GET | `/api/purchase-requests/{pid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho phiếu này: đi theo ô "Phòng xử lý" (xem | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/cancel` | cancel pr | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/clone` | clone pr | `purchase_request.create` |  | |
| POST | `/api/purchase-requests/{pid}/complete` | complete pr | `purchase_request.cancel` |  | |
| POST | `/api/purchase-requests/{pid}/copy` | copy pr | `purchase_request.create` |  | |
| GET | `/api/purchase-requests/{pid}/dept-head-candidates` | CR-071 — những người duyệt được bước 1 phiếu này, để ô "Trưởng bộ phận" cho chọn. | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/dispatch` | CR-034 — Duyệt lần 2 phía thu mua (điều phối): tự động phân bổ NSTM rồi mở khóa tạo ĐMH. | `purchase_request.approve` |  | |
| PATCH | `/api/purchase-requests/{pid}/item-status` | update item status | `purchase_request.read` |  | |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/available-survey-lines` | Kho phương án: các dòng khảo sát SẢN PHẨM đã duyệt, để NSTM nhặt vào dòng YCMH. | `purchase_request.write` |  | |
| GET | `/api/purchase-requests/{pid}/items/{item_id}/options` | list options | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options` | add option from survey | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/manual` | Phương án NSTM gõ tay — dùng khi giá biến động liên tục, kho khảo sát không kịp | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/reopen` | Người yêu cầu / quản lý MỞ LẠI một dòng đã chốt hoàn thành để NSTM sửa tiếp | `purchase_request.read` |  | |
| DELETE | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | delete option | `purchase_request.write` |  | |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}` | update option | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/choose` | Chốt phương án cho dòng — bấm lại đúng phương án đang chốt thì BỎ chốt. | `purchase_request.read` |  | |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/details` | bao-CR-583 — sửa thông tin PHƯƠNG ÁN 0 / NHẬP TAY (tên hàng, mã VTBB, NCC, giá, giao | `purchase_request.write` |  | |
| PATCH | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/supplier` | H.10.4 — điền/sửa NCC trên PHƯƠNG ÁN 0 / nhập tay, dùng được cả SAU khi dòng đã | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/items/{item_id}/options/{oid}/zero/reset` | bao-CR-583 — "Khôi phục ban đầu": phương án 0 về đúng như dòng yêu cầu lúc sinh. | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/options/assign-supplier` | H.10.5 — "Áp 1 NCC cho nhiều dòng" trên màn chọn: tick các dòng đang thiếu NCC, | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/options/choice-complete` | bao-CR-419 — NGƯỜI YÊU CẦU "Chốt xong lựa chọn" cho cả phiếu, rồi chuông báo | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/options/complete` | NSTM "Chốt hoàn thành xử lý" phần của mình trên phiếu (đợt 3b, khuôn YCBG | `purchase_request.write` |  | |
| POST | `/api/purchase-requests/{pid}/options/generate-orders` | H.10.6 — "Tạo đơn mua hàng theo phương án": gom phương án ĐANG CHỌN của từng | `purchase_order.create` |  | |
| GET | `/api/purchase-requests/{pid}/order-progress` | Tổng SL đã ĐẶT (qty_order) theo từng mã hàng, gộp từ các ĐMH cùng mã PYC. | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/reject` | reject pr | `purchase_request.approve` |  | |
| POST | `/api/purchase-requests/{pid}/return` | return pr | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện với chuyển phòng, đích là phòng thu mua | `purchase_request.approve` |  | |
| POST | `/api/purchase-requests/{pid}/submit` | submit pr | `purchase_request.read` |  | |
| POST | `/api/purchase-requests/{pid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ (đường 2): gỡ NSTM mọi dòng, đổi phòng, phiếu về | `purchase_request.approve` |  | |
| PATCH | `/api/purchase-requests/{pid}/urgent` | Bật/tắt cờ Đơn gấp (cả khi phiếu đã duyệt) + đồng bộ xuống ĐMH cùng pr_code. | `purchase_request.write` |  | |
| DELETE | `/api/execution-report/{entity}/{owner_id}` | Xóa CẢ khối báo cáo — có thể HOÀN TÁC từ Lịch sử thao tác. | — |  | |
| GET | `/api/execution-report/{entity}/{owner_id}` | get report  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/apply-template` | Nút "Tạo mẫu" trên một nút dòng hàng / một giai đoạn — đổ mẫu chung vào, | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/docs` | create doc  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/docs/bulk-delete` | delete docs  | — |  | |
| DELETE | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | delete doc  | — |  | |
| PATCH | `/api/execution-report/{entity}/{owner_id}/docs/{doc_id}` | update doc  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/first-doc` | create first doc  | — |  | |
| GET | `/api/execution-report/{entity}/{owner_id}/first-doc-options` | Ô chọn của hộp "Thêm hồ sơ" khi khối còn trống: dòng hàng của chứng từ + 5 giai | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/init` | init report  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/items` | create item  | — |  | |
| DELETE | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | delete item  | — |  | |
| PATCH | `/api/execution-report/{entity}/{owner_id}/items/{item_id}` | rename item  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/phases` | create phase  | — |  | |
| DELETE | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | delete phase  | — |  | |
| PATCH | `/api/execution-report/{entity}/{owner_id}/phases/{phase_id}` | update phase  | — |  | |
| POST | `/api/execution-report/{entity}/{owner_id}/restore` | Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác. | — |  | |
| GET | `/api/execution-report/{entity}/{owner_id}/templates` | Ô chọn mẫu của hộp "Khởi tạo báo cáo mẫu" (duoc-CR-614). Gác như thao tác ghi: chỉ | — |  | |
| DELETE | `/api/survey-requests` | bulk delete survey requests | `survey_request.delete` | `apply_scope` | |
| GET | `/api/survey-requests` | list  | `survey_request.read` |  | |
| POST | `/api/survey-requests` | create  | `survey_request.create` |  | |
| GET | `/api/survey-requests/export/xlsx` | CR-068 — xuất Excel danh sách YCBG: mỗi dòng yêu cầu một hàng, kèm phương án đã chốt. | `survey_request.export` |  | |
| GET | `/api/survey-requests/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `survey_request.read` |  | |
| GET | `/api/survey-requests/meta/department-managers` | bao-CR-552 — trưởng phòng mọi phòng đang hoạt động, cho ô "Trưởng bộ phận" YCBG của bản v1 chọn | `survey_request.read` |  | |
| GET | `/api/survey-requests/meta/dept-head` | Trưởng bộ phận của 1 phòng ban — cho người yêu cầu (không xem được DS nhân sự) tự điền TBP. | `survey_request.read` |  | |
| DELETE | `/api/survey-requests/{sid}` | delete  | `survey_request.delete` |  | |
| GET | `/api/survey-requests/{sid}` | get  | `survey_request.read` |  | |
| PATCH | `/api/survey-requests/{sid}` | update  | `survey_request.read` |  | |
| POST | `/api/survey-requests/{sid}/approve` | approve  | `survey_request.approve` |  | |
| GET | `/api/survey-requests/{sid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `survey_request.read` | `apply_scope` | |
| GET | `/api/survey-requests/{sid}/assignable-staff` | bao-CR-486 — NSTM chọn được cho YCBG này: đi theo ô "Phòng xử lý" (cùng luật YCMH). | `survey_request.read` |  | |
| POST | `/api/survey-requests/{sid}/cancel` | TỪ CHỐI — khóa đơn hẳn (không sửa được nữa, phải làm đơn mới). status → cancelled. | `survey_request.approve` |  | |
| POST | `/api/survey-requests/{sid}/clone` | Nhân bản 1 YCKS thành phiếu nháp mới (sao chép header + dòng). | `survey_request.create` | `apply_scope` | |
| POST | `/api/survey-requests/{sid}/complete` | Chốt hoàn thành khảo sát — NSTM chốt PHẦN DÒNG CỦA MÌNH; phiếu -> survey_done khi | — |  | |
| POST | `/api/survey-requests/{sid}/create-prs` | Người YC tạo Yêu cầu mua hàng từ các phương án đã chọn (gom theo NCC). | `survey_request.write` |  | |
| POST | `/api/survey-requests/{sid}/finalize` | Chuyển Hoàn thành (pr_created/survey_done → done). Cho phép Quản lý/Admin thu mua | `survey_request.write` |  | |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/assignee` | Gán/đổi NSTM phụ trách 1 dòng — CHỈ thu mua side (NSTM/QL/Admin TM). Người YC không được. Body: {assignee: mã NV}. | `survey_request.process` | `scope_condition` | |
| GET | `/api/survey-requests/{sid}/lines/{line_id}/available-survey-lines` | available survey lines  | — |  | |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/line-status` | Task 2: người YC / cùng phòng ban đổi trạng thái dòng khảo sát | `survey_request.write` |  | |
| POST | `/api/survey-requests/{sid}/lines/{line_id}/options` | add option  | — |  | |
| DELETE | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | del option  | — |  | |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}` | edit option  | — |  | |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/options/{oid}/choose` | Người YC chọn 1 phương án cho 1 sản phẩm (chỉ khi đã hoàn thành khảo sát). | `survey_request.write` |  | |
| PATCH | `/api/survey-requests/{sid}/lines/{line_id}/status` | Đổi Tình trạng dòng (is_completed). Body: {is_completed: bool}. Chặn khi phiếu đã từ chối/hoàn thành. | `survey_request.write` |  | |
| GET | `/api/survey-requests/{sid}/process` | Trang *Xử lý khảo sát* (CR-222). | — |  | |
| POST | `/api/survey-requests/{sid}/reject` | TRẢ ĐƠN — trả về để người YC sửa & gửi lại (như nháp). status → rejected (còn sửa được). | `survey_request.approve` |  | |
| GET | `/api/survey-requests/{sid}/result` | Kết quả khảo sát cho người YC — ẩn NCC ở tầng backend (whitelist field). | `survey_request.read` | `apply_scope` | |
| POST | `/api/survey-requests/{sid}/return-dept` | bao-CR-414 GĐ5 — TRẢ VỀ THU MUA: cùng điều kiện, đích là phòng thu mua mặc định | `survey_request.approve` |  | |
| POST | `/api/survey-requests/{sid}/submit` | submit  | `survey_request.read` |  | |
| POST | `/api/survey-requests/{sid}/sync-options` | Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCKS này (khớp phân loại). | — |  | |
| POST | `/api/survey-requests/{sid}/transfer-dept` | bao-CR-414 GĐ5 — CHUYỂN PHÒNG XỬ LÝ: gỡ NSTM + ngày tiếp nhận mọi dòng, đổi phòng; | `survey_request.approve` |  | |
| GET | `/api/survey-report/by-supplier` | Task 9: khảo sát của 1 NCC — KSNCC (theo tax_code) + KSSP (theo supplier_code). | `survey.read` | `apply_scope` | |
| GET | `/api/survey-report/lines` | report lines  | `survey.read` | `apply_scope` | |
| GET | `/api/survey-report/summary` | Tổng hợp Báo cáo khảo sát — cùng phạm vi + bộ lọc với `/lines`. | `báo cáo 5`, `survey.read` | `apply_scope` | |
| GET | `/api/survey-report/summary/export` | Xuất Excel bản THEO KỲ của Báo cáo khảo sát (P03) — cùng bộ lọc với `/summary`. | `báo cáo 5`, `survey.export` | `apply_scope` | |
| DELETE | `/api/surveys` | bulk delete surveys | `survey.delete` | `apply_scope` | |
| GET | `/api/surveys` | list surveys | `survey.read` | `apply_scope` | |
| POST | `/api/surveys` | create  | `survey.create` |  | |
| DELETE | `/api/surveys/{sid}` | delete  | `survey.delete` |  | |
| GET | `/api/surveys/{sid}` | get  | `survey.read` | `apply_scope` | |
| PATCH | `/api/surveys/{sid}` | update  | `survey.write` |  | |
| POST | `/api/surveys/{sid}/approve` | approve  | `survey.approve` |  | |
| POST | `/api/surveys/{sid}/cancel` | Từ chối phiếu đang chờ duyệt (khóa hẳn) — người duyệt thao tác. | `survey.approve` |  | |
| POST | `/api/surveys/{sid}/clone` | clone  | `survey.create` |  | |
| PATCH | `/api/surveys/{sid}/line-approve` | line approve  | `survey.approve` |  | |
| PATCH | `/api/surveys/{sid}/lines/{table}/{line_id}/fill` | Bổ sung 1 dòng đang 'Thiếu thông tin' (kể cả phiếu đã duyệt) — có guard trong service. | `survey.write` |  | |
| POST | `/api/surveys/{sid}/reject` | reject  | `survey.approve` |  | |
| POST | `/api/surveys/{sid}/submit` | submit  | `survey.write` |  | |
| GET | `/api/survey-progress` | list progress | — |  | |
| GET | `/api/survey-progress/export/xlsx` | Xuất Excel theo đúng bộ lọc + cột đang hiện (cùng lối với màn Tiến độ mua hàng). | — |  | |
| GET | `/api/survey-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi (cả lọc dòng theo NSTM) với bảng. | `báo cáo 3` |  | |
| GET | `/api/survey-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ báo giá (P03) — cùng bộ lọc với `/summary`. | `báo cáo 3` |  | |
| DELETE | `/api/purchase-orders` | bulk delete pos | `purchase_order.delete` | `apply_scope` | |
| GET | `/api/purchase-orders` | list po | `purchase_order.read` |  | |
| POST | `/api/purchase-orders` | create po | `purchase_order.create` |  | |
| GET | `/api/purchase-orders/export/xlsx` | CR-068 — xuất Excel danh sách ĐMH, cột dòng hàng lấy đúng bộ cột màn Tiến độ mua hàng | `purchase_order.export` |  | |
| GET | `/api/purchase-orders/lines` | Danh sách DÒNG HÀNG của các đơn mua hàng — dùng cho trang chi tiết Kho. | `purchase_order.read` | `apply_scope` | |
| GET | `/api/purchase-orders/meta/approver-candidates` | bao-CR-499 — người duyệt được chứng từ ĐANG LẬP (chưa có id), cho ô "Trưởng phòng phê duyệt". | `purchase_order.read` |  | |
| DELETE | `/api/purchase-orders/{pid}` | delete po | `purchase_order.delete` |  | |
| GET | `/api/purchase-orders/{pid}` | get po | `purchase_order.read` | `apply_scope` | |
| PATCH | `/api/purchase-orders/{pid}` | update po | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/approve` | approve po | `purchase_order.approve` |  | |
| GET | `/api/purchase-orders/{pid}/approver-candidates` | bao-CR-499 — người duyệt được ĐÚNG chứng từ này (hỏi apply_scope hành động approve). | `purchase_order.read` | `apply_scope` | |
| POST | `/api/purchase-orders/{pid}/cancel` | cancel po | `purchase_order.cancel` |  | |
| POST | `/api/purchase-orders/{pid}/clone` | Alias của /copy — dùng cho nút Nhân bản ở danh sách (đồng bộ với YCMH/YCKS). | `purchase_order.create` |  | |
| POST | `/api/purchase-orders/{pid}/complete` | complete po | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/copy` | copy po | `purchase_order.create` |  | |
| POST | `/api/purchase-orders/{pid}/cost-lines/finalize` | bao-CR-469 — Quyết toán NHIỀU dòng chi phí một lượt (tick chọn, hoặc chốt hết). | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/cost-stage/advance` | Chốt Tạm tính / Quyết toán. Có `import_costs` thì lưu bảng chi phí trước rồi mới chốt. | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/cost-stage/reopen` | Mở lại bộ chi phí về giai đoạn thấp hơn — cần quyền duyệt + lý do. | `purchase_order.approve` |  | |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/finalize` | Quyết toán RIÊNG một dòng chi phí (hóa đơn khoản đó về trước). | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/costs/{cost_id}/reopen` | Mở lại một dòng đã quyết toán riêng — cần quyền duyệt + lý do. | `purchase_order.approve` |  | |
| PATCH | `/api/purchase-orders/{pid}/document-status` | Task 10b: cập nhật tay trạng thái hồ sơ chứng từ (cho phép cả khi đơn đã hoàn thành). | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/items/{item_id}/progress` | Người phụ trách cập nhật trạng thái tiến độ 1 dòng (có gate điều kiện) + đồng bộ sang YCMH. | `purchase_order.write` |  | |
| GET | `/api/purchase-orders/{pid}/print` | print po | `purchase_order.print` |  | |
| GET | `/api/purchase-orders/{pid}/purchase-request` | Phiếu YCMH nguồn của đơn, đã cắt còn đúng các dòng hàng có trên đơn — bao-CR-314. | `purchase_order.print` | `apply_scope` | |
| POST | `/api/purchase-orders/{pid}/reject` | reject po | `purchase_order.approve` |  | |
| POST | `/api/purchase-orders/{pid}/reopen` | reopen po | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/return` | return po | `purchase_order.approve` |  | |
| POST | `/api/purchase-orders/{pid}/submit` | submit po | `purchase_order.write` |  | |
| POST | `/api/purchase-orders/{pid}/unapprove` | Hủy duyệt — đơn về Nháp để sửa rồi gửi duyệt lại (CR-108, phiếu hỗ trợ TK19082604). | `purchase_order.approve` |  | |
| GET | `/api/purchase-progress` | list progress | — |  | |
| GET | `/api/purchase-progress/export/xlsx` | CR-068 — xuất Excel màn Tiến độ mua hàng theo đúng bộ lọc + cột đang hiện. | — |  | |
| GET | `/api/purchase-progress/summary` | Số liệu tổng hợp cho màn biểu đồ — cùng bộ lọc + phạm vi với bảng. | `báo cáo 4` |  | |
| GET | `/api/purchase-progress/summary/export` | Xuất Excel bản THEO KỲ của màn Tiến độ mua hàng (P03) — cùng bộ lọc với `/summary`. | `báo cáo 4` |  | |
| GET | `/api/products/{code}/purchase-history` | product purchase history | `product.read` |  | |
| GET | `/api/suppliers/{code}/purchase-history` | supplier purchase history | `supplier.read` |  | |
| GET | `/api/payables` | list payables | `payable.read` |  | |
| GET | `/api/payables/export/xlsx` | Ticket #16 — xuất Excel danh sách Công nợ đúng bộ lọc + phạm vi màn hình. | `payable.export` |  | |
| GET | `/api/payables/summary` | Thẻ tổng hợp công nợ. | `payable.read` |  | |
| POST | `/api/payables/{pid}/offset-prepay` | CR-268 — kế toán cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước không gắn đơn) | `payable.write` | `apply_scope` | |
| DELETE | `/api/payment-requests` | bulk delete requests | `payment_request.delete` | `apply_scope` | |
| GET | `/api/payment-requests` | list  | `payment_request.read` |  | |
| POST | `/api/payment-requests` | create  | `payment_request.create` | `apply_scope` | |
| GET | `/api/payment-requests/export/xlsx` | bao-CR-525 — xuất Excel THEO DÒNG CHI TIẾT: phiếu đúng bộ lọc + phạm vi màn danh sách, | `payment_request.export` |  | |
| GET | `/api/payment-requests/hanging` | CR-268 — tiền treo (phiếu trả trước đã chi, chưa đối trừ/hoàn hết) của 1 NCC. | `payment_request.read` |  | |
| GET | `/api/payment-requests/meta/department-managers` | bao-CR-553 — ô "Trưởng bộ phận" của YCTT: trưởng phòng mọi phòng (có Ban Giám đốc). | `payment_request.read` |  | |
| DELETE | `/api/payment-requests/{rid}` | delete  | `payment_request.delete` |  | |
| GET | `/api/payment-requests/{rid}` | get  | `payment_request.read` | `apply_scope` | |
| PATCH | `/api/payment-requests/{rid}` | update  | `payment_request.write` |  | |
| POST | `/api/payment-requests/{rid}/approve` | approve  | `payment_request.approve` |  | |
| POST | `/api/payment-requests/{rid}/pay` | pay  | `payment_request.write` |  | |
| GET | `/api/payment-requests/{rid}/print` | print  | `payment_request.print` |  | |
| POST | `/api/payment-requests/{rid}/refresh-from-payables` | bao-CR-509 — GHI số mới theo công nợ vào phiếu NHÁP (tính lại từ DB lúc ghi). | `payment_request.write` |  | |
| GET | `/api/payment-requests/{rid}/refresh-preview` | bao-CR-509 — XEM TRƯỚC số mới của từng dòng theo công nợ hiện tại, KHÔNG ghi gì. | `payment_request.read` |  | |
| POST | `/api/payment-requests/{rid}/refund` | CR-268 — ghi nhận NCC HOÀN TIỀN phần treo của phiếu trả trước đã chi. | `payment_request.write` |  | |
| POST | `/api/payment-requests/{rid}/reject` | Từ chối phiếu yêu cầu thanh toán (khóa) — người duyệt thao tác. Body: {reason}. | `payment_request.approve` |  | |
| POST | `/api/payment-requests/{rid}/submit` | submit  | `payment_request.write` |  | |
| DELETE | `/api/suppliers` | bulk delete suppliers | `supplier.delete` | `apply_scope` | |
| GET | `/api/suppliers` | list suppliers | `supplier.read` |  | |
| POST | `/api/suppliers` | create supplier | `supplier.create` |  | |
| GET | `/api/suppliers/export/csv` | export suppliers csv | `supplier.export` | `apply_scope` | |
| POST | `/api/suppliers/import/csv` | import suppliers csv | `supplier.import` |  | |
| DELETE | `/api/suppliers/{sid}` | delete supplier | `supplier.delete` | `get_scoped` | |
| GET | `/api/suppliers/{sid}` | get supplier | `supplier.read` |  | |
| PATCH | `/api/suppliers/{sid}` | update supplier | `supplier.write` |  | |
| DELETE | `/api/contracts` | bulk delete contracts | `contract.delete` | `apply_scope` | |
| GET | `/api/contracts` | list  | `contract.read` | `apply_scope` | |
| POST | `/api/contracts` | create  | `contract.create` | `apply_scope` | |
| GET | `/api/contracts/meta/types` | Bộ loại hợp đồng cố định cho FE dựng ô chọn (CR-118). | `contract.read` |  | |
| DELETE | `/api/contracts/{cid}` | Xóa MỀM một hợp đồng (ai-CR-177): đánh cờ `is_deleted` + mốc + người xóa. | `contract.delete` |  | |
| GET | `/api/contracts/{cid}` | get  | `contract.read` |  | |
| PATCH | `/api/contracts/{cid}` | update  | `contract.write` |  | |
| GET | `/api/category-assignees` | Danh sách phân công NSTM — 1 query JOIN (hết N+1), phân trang + sort tại DB. | `category_assignee.read` |  | |
| POST | `/api/category-assignees` | create  | `category_assignee.create` |  | |
| POST | `/api/category-assignees/bulk` | bulk  | `category_assignee.create` |  | |
| DELETE | `/api/category-assignees/{cid}` | delete  | `category_assignee.delete` |  | |
| GET | `/api/category-assignees/{cid}` | get  | `category_assignee.read` |  | |
| PATCH | `/api/category-assignees/{cid}` | update  | `category_assignee.write` |  | |
| GET | `/api/po-cost-types` | list items | `purchase_cost_type.read` | `apply_scope` | |
| POST | `/api/po-cost-types` | create item | `purchase_cost_type.create` |  | |
| GET | `/api/po-cost-types/export/csv` | export csv | `purchase_cost_type.export` | `apply_scope` | |
| DELETE | `/api/po-cost-types/{oid}` | delete item | `purchase_cost_type.delete` | `get_scoped` | |
| GET | `/api/po-cost-types/{oid}` | get item | `purchase_cost_type.read` | `get_scoped` | |
| PATCH | `/api/po-cost-types/{oid}` | update item | `purchase_cost_type.write` | `get_scoped` | |

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
