# Rà soát xóa cứng trong backend ERP (10/10/2026)

Đại ca yêu cầu 10/10/2026: chuyển xóa phiếu sang **xóa mềm** (cột ghi nhận đã xóa / thời điểm xóa) và kiểm còn chỗ nào xóa
cứng. Bản rà đọc mã `backend/app/modules/` + `core/` trên nhánh `agent-hub-bac-1` (= `erp-v2` cùng ngày), chỉ đọc, chưa sửa gì.

## 1. Đã xóa mềm sẵn

| Chứng từ | Cột |
|---|---|
| Yêu cầu mua hàng (YCMH) | `is_deleted` |
| Đơn nghỉ phép | `is_deleted` |
| Đặt phòng họp | `is_deleted` |
| Duyệt dấu | `is_deleted` |
| Đặt xe | `is_deleted` (nhưng vẫn xóa cứng lịch sử duyệt qua `approval.instance_service.delete_by_entity`) |
| Việc Dự án | `deleted_at` |
| Phiếu hỗ trợ | không có đường xóa |

## 2. Rủi ro cao — vá trước (đợt 1)

**Tiến độ:** cả 7 mục đã vá ở ai-CR-169 (10/10). Hợp đồng «nháp» = chưa ký và chưa tới ngày bắt đầu, hoặc đã hủy (model không có trạng thái nháp riêng — muốn chặt hơn sửa `delete_block_reason`). Phiếu nhập / phát sinh kho chưa chặn vì không có cột cho biết đã có giao dịch kế tiếp.

| # | Chỗ | Vấn đề |
|---|---|---|
| 1 | `contract/controller.py` `delete_` + `bulk_delete_contracts` | **Không kiểm trạng thái**: xóa được hợp đồng đang hiệu lực / đã ký, kèm tệp |
| 2 | `import_tool` hoàn tác lô (`POST /api/imports/{bid}/revert`) | Xóa cứng mọi YCBG / YCMH / PKS / ĐMH / đặt xe / duyệt dấu của lô **ở mọi trạng thái** (kể cả đã duyệt sau khi nhập), và mọi YCTT của ĐMH đó |
| 3 | `purchase_order` sửa dòng / đợt giao → `_cleanup_delivery` | Xóa cứng phiếu nhập, xuất nhập kho, **công nợ đã thanh toán** (`payable.remove` không kiểm đã trả) — YCTT mồ côi |
| 4 | `supplier` xóa một / xóa nhiều | Không kiểm phạm vi, không kiểm đang được dùng |
| 5 | `product` xóa nhiều | Không kiểm phạm vi |
| 6 | `core/crud.py` nhập CSV hành động *xóa* | Không gọi `before_delete` → vượt rào *đang dùng* của loại hồ sơ, chức vụ, mức mật |
| 7 | `agent_hub/ops_runner.py` | Bot vận hành chạy được một câu `UPDATE/INSERT/DELETE … WHERE` do AI viết lên bảng ERP sau thẻ duyệt |

## 3. Chứng từ chính đang xóa cứng — chuyển sang xóa mềm (đợt 2)

**Tiến độ:** đợt 2a (ai-CR-170, 10/10) đã làm `SoftDeleteMixin` + lọc tập trung ở `apply_scope` / `get_scoped` và áp cho **YCBG** (migration grp11). Đợt 2b (13/10): **ĐMH · YCTT · PKS** xong ở ai-CR-176 (grp12); **hợp đồng NCC · văn bản nháp · HĐLĐ · hồ sơ** xong ở ai-CR-177 (grp13, kèm `core/crud.remove_or_mark_deleted` cho CRUD chung). Báo cáo thực hiện YCBG GIỮ cách cũ (đã có `SurveyReportTrash` hoàn tác; xóa mục / giai đoạn là dòng con của khối báo cáo). Đợt 3 (§4 danh mục): cụm tổ chức xong ở ai-CR-190, danh mục chung + cấu hình ở ai-CR-191 (13/10).

Yêu cầu báo giá (YCBG) · Đơn mua hàng (ĐMH) · Yêu cầu thanh toán (YCTT) · Phiếu khảo sát (PKS) · Hợp đồng NCC · Văn bản
(bản nháp) · Hợp đồng lao động · Hồ sơ (dossier, qua CRUD chung) · báo cáo thực hiện (mục / giai đoạn / tài liệu).

Cách làm đề xuất: một `SoftDeleteMixin` (`is_deleted` 0/1 · `deleted_at` · `deleted_by`) + lọc **tập trung** trong
`core/scoping.apply_scope` và `get_scoped` (model có `is_deleted` thì tự thêm điều kiện chưa xóa) — phủ được phần lớn chỗ đọc
mà không phải sửa từng truy vấn. Các chỗ đọc thẳng không qua phạm vi phải lọc tay; riêng YCBG có danh sách đủ ở §5. Sinh mã
phiếu (`_gen_code`) GIỮ cả phiếu đã xóa để không tái dùng mã. Tệp đính kèm, bình luận, lịch sử duyệt của phiếu xóa mềm: giữ
nguyên. Xóa đính kèm hiện commit trước cha (`attachment.delete_attachments_for`) — không nguyên khối; xóa mềm thì bỏ luôn bước này.

## 4. Danh mục — đề xuất *ngưng dùng* thay vì xóa (đợt 3)

NCC · sản phẩm · công ty · phòng ban · nhân sự · người dùng · vai trò · danh mục CRUD chung (kho, đơn vị, nhóm hàng, thương hiệu,
loại văn bản, đối tác ngoài, ngày lễ, loại dấu, xe, tài xế…) · cấu hình (luồng duyệt, thư mục, mẫu, quy tắc đánh số…).
Đề xuất: đang được chứng từ tham chiếu thì CHẶN xóa, chỉ cho *ngưng dùng*; chưa ai dùng thì vẫn xóa được.

### 4.a Cụm TỔ CHỨC — công ty · phòng ban · nhân sự · tài khoản · vai trò (ai-CR-190, 13/10/2026)

Khai ở `<module>/references.py`, import từ `service.py` của chính module lúc khởi động (không qua `core/all_models.py`).
Năm module này đều có controller viết tay nên gọi `reference_guard.ensure_deletable` tường minh ở đường xóa một, xóa nhiều
(`bulk_delete_companies`: kiểm cả lô trước, một dòng vướng là không xóa dòng nào, câu báo liệt kê mã + lý do) và dòng CSV
«xóa» (phòng ban, nhân sự). Chốt cũ GIỮ và chạy TRƯỚC: HĐLĐ đã ký (409) của nhân sự; «tài khoản còn hồ sơ» + «đã tạo dữ
liệu» (`user_data_refs`) + «quản trị cuối» của tài khoản; vai trò admin. `created_by` / `updated_by` / lịch sử duyệt /
bình luận / thông báo / nhật ký: KHÔNG tính. Bài kiểm: `test/backend/test_chot_xoa_to_chuc_cr190.py`.

| Danh mục (entity) | Chỗ tham chiếu đã khai (nhãn trong câu 400) | «Ngưng dùng» |
|---|---|---|
| Công ty `company` (47 chỗ) | công ty con (`parent`); phòng ban + phòng hiện diện tại pháp nhân; nhân sự; quá trình công tác; HĐLĐ + mẫu HĐLĐ; luồng duyệt; YCMH · YCBG · ĐMH · phiếu nhập kho · công nợ · YCTT · lịch sử mua · hợp đồng NCC · tồn kho · phiếu kho; văn bản · yêu cầu văn bản · phạm vi áp dụng · nơi nhận (kind pháp nhân) · kế hoạch sao chép · sổ văn bản đến · sổ văn bản · thư mục · quyền xem văn bản / thư mục / báo cáo (subject pháp nhân); hồ sơ; phiếu đóng dấu (+ pháp nhân trên phiếu) · văn thư giữ dấu; đơn nghỉ phép · quỹ phép · ngày lễ · phòng họp · lịch đặt phòng · phiếu đặt xe · phiếu hỗ trợ · hộp thư · bài diễn đàn · chính sách / thành viên điểm cà phê; nhóm · bảng · thẻ công việc | `is_active` có ở model + `CompanyUpdate` + màn v2 (`company-form-dialog.tsx`) |
| Phòng ban `department` (30 chỗ) | phòng ban con (`parent`); nhân sự (`department_id`) · kiêm nhiệm · chức vụ · quá trình công tác · HĐLĐ · phân công nhóm hàng; YCMH / YCBG / ĐMH (`department_id` và `handler_dept_id` khai riêng) · công nợ · YCTT; văn bản · yêu cầu văn bản · phạm vi · nơi nhận (kind phòng) · quyền xem văn bản / thư mục / báo cáo (subject phòng) · hồ sơ · phiếu đóng dấu; đơn nghỉ phép · lịch đặt phòng · phiếu đặt xe · bài diễn đàn (`dept_id`); thành viên nhóm / bảng công việc | `is_active` có ở model + `DepartmentUpdate` + màn v2 (`department-form-dialog.tsx`) |
| Nhân sự `employee` (53 chỗ) | nhân sự do người này quản lý (`manager_id`) · phòng ban làm trưởng bộ phận (+ tại pháp nhân) · công ty làm người đại diện pháp luật · phân công nhóm hàng (chính / dự phòng) · thương hiệu phụ trách; chặng duyệt đích danh (`approver_ref` chuỗi, kind 1) · chặng duyệt người dự phòng · phiếu duyệt đã trình · việc duyệt được giao · ủy quyền duyệt (hai chiều); YCMH (người yêu cầu / trưởng bộ phận / người duyệt / người phụ trách) · YCBG (3 cột) · báo cáo thực hiện (người phụ trách) · ĐMH (người duyệt) · YCTT (trưởng bộ phận); văn bản (chủ trì / soạn / ký) · yêu cầu văn bản · phạm vi · nơi nhận (kind nhân sự) · chữ ký · văn bản đến được giao · thành viên sổ · quyền xem văn bản / thư mục / báo cáo (subject nhân sự) · hồ sơ + tiến độ hồ sơ · phiếu đóng dấu (yêu cầu / duyệt) · văn thư giữ dấu; đơn nghỉ · bàn giao · quỹ phép · lịch đặt phòng · người tham dự · phiếu đặt xe (yêu cầu / duyệt) · phiếu hỗ trợ · thành viên hộp thư · thành viên điểm cà phê; thẻ công việc được giao · thành viên nhóm / bảng | `is_active` có ở model + `EmployeeUpdate` + màn v2 (`employee-form-dialog.tsx`); ngoài ra «nghỉ việc» (`status`) |
| Tài khoản `user` (2 chỗ) | phiếu hỗ trợ đang xử lý (`tab_ticket.assignee_id`), tài xế liên kết (`tab_driver.user_id`) | `is_active` = khóa / mở khóa (`set_active`, màn v2 `user-account-table.tsx`) |
| Vai trò `role` (5 chỗ) | tài khoản đang giữ (`tab_user_role`); chặng duyệt theo vai trò (`approver_ref` = mã, kind 2); quyền xem văn bản / thư mục / báo cáo (subject vai trò) | KHÔNG có `is_active` (cố ý không thêm cột — tránh migration): còn người giữ thì chặn, hết thì xóa; `tab_permission` + `tab_user_scope` dọn kèm |

Giả định đã chốt khi làm (đổi thì sửa `references.py` tương ứng):

- **`tab_user.employee_id` KHÔNG tính là tham chiếu của nhân sự.** `delete_user` đã chặn «tài khoản còn hồ sơ thì không xóa»;
  nếu chiều ngược cũng chặn thì không xóa được cả hai (bế tắc, không có đường gỡ liên kết). Giữ lối CR-023: xóa hồ sơ → tự
  khóa + gỡ tài khoản (`detach_users`), chạy SAU chốt tham chiếu nên không khóa oan khi bị chặn.
- **Bảng con của chính dòng được dọn kèm, không đếm:** liên hệ / gia đình / kiêm nhiệm (`tab_employee_department`, mới thêm
  dọn ở ai-CR-190) / quá trình công tác / HĐLĐ nháp–hủy của nhân sự; `tab_department_company` của phòng ban (FK CASCADE);
  `tab_user_role` · `tab_user_scope` · thông báo · đăng ký đẩy · **phiên đăng nhập** (mới thêm xóa cứng kèm) của tài khoản;
  `tab_permission` · `tab_user_scope` của vai trò.
- **Bỏ qua, không đếm được / không thuộc ERP:** `tab_user_scope.value` (chuỗi: tên phòng, id công ty dạng text); bảng
  `tab_agent_*` của bot (liên kết chat, cấp quyền bot, sổ ghi nhớ…) vì ở dev/prod bot chạy `AGENT_MODE=service` với DB riêng;
  bình luận / cảm xúc / tùy chọn cá nhân / bộ lọc đã lưu / nhật ký yêu cầu (nhật ký, bộ đệm).
- **Hành vi đổi so với trước:** xóa nhân sự đang là quản lý trực tiếp của người khác nay CHẶN (trước: tự gỡ `manager_id`
  cấp dưới về 0 — dòng gỡ giữ lại làm lưới cho dữ liệu cũ); câu chặn vai trò còn người giữ đổi sang câu chung của sổ (vẫn
  chứa «n tài khoản»).

### 4.b Danh mục chung + cấu hình (ai-CR-191, 13/10/2026)

Khai ở `<module>/references.py` (import từ `controller.py` của module lúc khởi động); danh mục đi qua
`make_crud_router` được `core/crud` tự chốt ở nút xóa và dòng CSV «xóa». Chốt `before_delete` cũ của từng
danh mục GIỮ nguyên (câu riêng), sổ chung chạy sau. Đếm không lọc phạm vi, bản ghi xóa mềm vẫn tính.
Bài kiểm: `test/backend/test_chot_xoa_danh_muc_chung_cr191.py`.

| Danh mục (entity) | Chỗ tham chiếu đã khai | Khóa | «Ngưng dùng» |
|---|---|---|---|
| Kho `warehouse` | dòng ĐMH, dòng giao hàng, phiếu nhập kho, tồn kho, phát sinh kho (`warehouse_code`); dòng YCMH (`warehouse` = TÊN kho) | mã / tên | `is_active` |
| Đơn vị tính `unit` | sản phẩm, dòng YCMH, dòng ĐMH, phiếu nhập kho, tồn kho, lịch sử mua hàng (`unit` = TÊN) | tên | `is_active` |
| Nhóm hàng `item_group` | sản phẩm, dòng YCMH, dòng ĐMH, phiếu khảo sát, dòng YCBG (`item_group` = TÊN); phân công NSTM (`item_group_id`) | tên / id | `is_active` |
| Thương hiệu `brand` | không có tham chiếu, xóa tự do | — | `is_active` |
| Loại văn bản `doc_type` | văn bản, yêu cầu soạn, mẫu văn bản, quy tắc đánh số (`doc_type_id`); quy tắc quan hệ (`source_type_id` / `target_type_id`) | id | `is_active` |
| Đối tác ngoài `external_party` | nơi nhận văn bản (`external_party_id`), văn bản đến (`sender_party_id`) | id | `is_active` |
| Mức mật `security_level` | GIỮ chốt riêng `security_level_guard` (văn bản, loại văn bản, JSON điều kiện luồng) — tham chiếu theo cặp thang/bậc, không khai sổ chung | — | `is_active` |
| Ngày lễ `holiday` | không có tham chiếu, xóa tự do | — | `is_active` |
| Loại con dấu `seal_type` | phiếu duyệt dấu (`seal_type_id`) | id | `is_active` |
| Xe `vehicle` · Tài xế `driver` | chuyến xe (`assigned_vehicle_id` / `assigned_driver_id`) | id | **THIẾU** — chỉ có `status` (available / on_trip / maintenance), chưa có `is_active`; chặn xóa vẫn áp |
| Loại hồ sơ `dossier_type` | GIỮ `before_delete` (hồ sơ, trừ xóa mềm); không có chỗ thiếu | — | `is_active` |
| Chức vụ `job_position` | GIỮ `before_delete` (hồ sơ đang giữ) + khai thêm dòng quá trình công tác (`tab_employee_work_history.position_id`) | id | `is_active` |
| Loại nghỉ `leave_type` | GIỮ `before_delete` (đơn, dòng đơn, quỹ phép, loại khác quy đổi vào); không có chỗ thiếu | — | `is_active` |
| Phòng họp `meeting_room` | GIỮ `before_delete` (phiếu đặt chưa xóa mềm); không có chỗ thiếu | — | `is_active` |
| Loại chi phí ĐMH `purchase_cost_type` | GIỮ `before_delete` (dòng chi phí, mã 99); không có chỗ thiếu | — | `is_active` |
| Hải quan: `customs_regulation`, từ khóa / từ đồng nghĩa (`customs_price`), thuốc BVTV (`customs_pesticide`) | không bảng nào trỏ tới (dòng giá chỉ trỏ bên XNK `tab_customs_party`, bảng này không có nút xóa) — xóa tự do | — | `is_active` (BVTV dùng `status`) |

Cấu hình có đường xóa riêng — gọi `reference_guard.ensure_deletable` trong hàm xóa:

| Cấu hình (entity) | Chỗ tham chiếu đã khai | Ghi chú |
|---|---|---|
| Luồng duyệt `approval_flow` (`flow_controller.delete_flow`) | phiếu duyệt kể cả đã xong (`tab_approval_instance.flow_id`); loại văn bản lấy làm luồng mặc định (`default_flow_id`) | chốt cũ «phiếu đang chạy» đứng trước, giữ câu riêng. Ủy quyền: nút xóa = tắt từ trước, không đổi |
| Thư mục văn bản `doc_folder` (`folder_service._guard_deletable`) | loại văn bản lấy làm thư mục mặc định (`default_folder_id`) | văn bản TRONG thư mục KHÔNG chặn — giữ quyết định 25/09/2026 (xóa là gỡ / chuyển văn bản); hộp xem trước báo cùng lý do |
| Sổ văn bản `document_book` (`book_service.delete_book`) | văn bản (`book_id`), quy tắc đánh số (`tab_document_numbering_rule_book`) | chốt «đã cấp số» cũ giữ |
| Quy tắc đánh số `doc_numbering_rule` | văn bản (`numbering_rule_id`) | chốt «đã cấp số» cũ giữ |
| Quy tắc quan hệ `doc_link_rule` | liên kết văn bản (`tab_document_link.rule_id`) | TRƯỚC CR này cho xóa và để `rule_id` trỏ vào khoảng không — nay chặn |
| Quyền thư mục, mẫu văn bản / mẫu HĐLĐ | không đổi: dòng quyền không ai trỏ tới; mẫu HĐLĐ đã có chốt đếm hợp đồng | — |

## 5. YCBG — mọi chỗ truy vấn phải lọc phiếu đã xóa

- `survey_request/service.py`: `get_sr` (:38), `_auto_complete_sr` (:962), `unlink_deleted_pr` (:1018), đọc lại phiếu trong
  `delete_option` (:732); `_gen_code` (:83) GIỮ phiếu đã xóa.
- `survey_request/controller.py`: `scope_condition` / `_in_scope` (:50–79), `_list_query` (:296, dùng cho danh sách + xuất
  Excel), `get_` (:383), `clone_` (:419), xóa nhiều (:440), `result_view_` (:955); báo cáo thực hiện `report_controller.py`.
- `core`: `scoping.py` (SCOPE_FIELDS :47, phạm vi *của tôi* :534–545), `attachment_scope.py` (:77–83, :297),
  `comment_registry.py` (:55), `entity_models.py` (:27, nhật ký), `file_registry.py` (:20).
- Trang chủ / tiến độ / báo cáo / xuất: `dashboard/controller.py` (:286, :514), `survey_progress/controller.py` `_build_query`
  (:205–310) và xuất Excel, `report/service.py` (:352–389 — đã tự lọc khi model có `is_deleted`), `export_log/registry.py` (:77).
- Phân hệ khác: `purchase_request/controller.py` (:322–338), `purchase_request/service.py` (:314), `survey/service.py`
  (:69, :73), `attachment/controller.py` (:461), `dossier/applicability.py` (:197, :265), `import_tool/doc_import.py` (:208),
  `legacy_datxe/mapping.py` (:208).
- Trợ lý / bot: `assistant/tools/procurement_doc_tool.py` (:105–111, :294, :312, :453, :476–482, :569–579, :624),
  `assistant/tools/update_tool.py` (:190–216, :767, :832, :943–955), `agent_hub/draft_create.py` (:474, :633–648).
- YCBG không đi qua bộ máy duyệt chung (không có lịch sử duyệt chung để giữ).

## 6. Dọn dẹp chấp nhận được (không đổi)

Thay dòng con khi sửa phiếu cha; thông báo, nhật ký, sao lưu, phiên đăng nhập, bộ đệm; bảng nội bộ của bot; các nhập / hoàn
tác có bản chụp (dòng hải quan, nhập danh mục).

<!-- ai-CR-189/190/191: đợt 3 xong 13/10 -->
