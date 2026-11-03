# Phase 02 — BE: YCTT nguồn "Thanh toán nghỉ phép"

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Nháp | duoc-CR-719 |

## Context
- [plan.md](plan.md) D1, D2, D7. Phase 01 đã có cột `payee_employee_id`, `source_ref_id`, chốt `hr_payout_guard`.
- `payment_request/service.py`: `create_requests` (`:231`), `update_request` (`:368`), `refresh_block_reason` (`:428`),
  `check_submit` (`:557`), `delete_request` (`:612`), `ALLOWED_FROM` + `set_status` (`:639`). `controller.py`: `print_` (`:217`),
  `_notify_pay` (`:327`). Bản in đọc STK NCC theo `supplier_code`.
- `employee/sensitive.py:66` `can_read_sensitive(profile, employee_id)`. Thông báo: `notification/service.py:442`, `:569`.
- Tài liệu YCTT: `doc/erp/thu-mua/chuc-nang/14-yeu-cau-thanh-toan.md`.

## Tổng quan
P1. YCTT hôm nay chỉ cho NCC + công nợ. Thêm nguồn thứ tư `leave_encashment` CHỈ do máy tạo (không có trong `SOURCE_TYPES`
người chọn), người nhận là nhân sự, một dòng, tiền 0 lúc tạo; kế toán nhập tiền rồi đi đúng luồng Nháp → Chờ duyệt → Đã duyệt →
Đã chi như mọi YCTT.

## Hợp đồng (phase 03 gọi) — tệp mới `payment_request/leave_encashment_payout.py`
```python
def create_payout_request(db, encashment, employee, actor: int) -> PaymentRequest   # flush, KHÔNG commit
def payout_state(db, payment_request_id: int) -> dict | None   # {id, code, status, status_label, total} hoặc None (đã xóa / 0)
def void_draft_payout(db, payment_request_id: int, actor: int) -> None   # chỉ Nháp → xóa mềm; khác Nháp → HTTPException 400
def payout_allows_cancel(state: dict | None) -> bool   # True khi None, "draft" hoặc "cancelled"
```
`create_payout_request`: `source_type="leave_encashment"`, `supplier_code=""`, `supplier_name=f"{full_name} ({code})"`,
`payee_employee_id`, `source_ref_id=encashment.id`, `company_id/department_id` của nhân sự, `request_date=vn_today()`,
`status="draft"`, `total=0`, `payment_method="transfer"`, `created_by=0` (máy tạo — không lọt phạm vi **của tôi** của người duyệt
phiếu nghỉ), `updated_by=actor`, `note` = *Thanh toán {days} ngày {loại nghỉ} năm {balance_year} — phiếu {code}*. Một dòng
`PaymentRequestLine(payable_id=0, po_code=encashment.code, amount=0)`. `code = f"YCTT{id:05d}"`. Ghi `record(..., "create")`.

## Việc
1. **Sửa** (`update_request`): YCTT nguồn nghỉ phép chỉ nhận `request_date`, `note`, `payment_method`, `print_texts`,
   `head_of_dept*` và **số tiền của dòng duy nhất** (qua `lines` đúng 1 dòng, `payable_id = 0`, chỉ lấy `amount`); thêm dòng /
   gắn công nợ / đổi `po_code` → 400. `total` = số tiền dòng. Chỉ Nháp sửa tiền (như cũ).
2. **Gửi duyệt** (`check_submit`): nhánh nguồn nghỉ phép đứng ĐẦU — bắt `amount > 0` (chép `before_submit` ERPNext:
   *Nhập số tiền thanh toán nghỉ phép trước khi gửi duyệt*), bỏ khớp công nợ, cấm `offset_amount`, cấm `prepay`.
3. **Duyệt / chi** (`set_status`): nguồn nghỉ phép bỏ `apply_line_offsets` và vòng cộng công nợ; `paid` chỉ đổi trạng thái +
   `allocated_amount = amount`. Không chạy tiến độ ĐMH.
4. **Chặn**: `delete_request` + xóa nhiều → 400 *YCTT thanh toán nghỉ phép không xóa ở đây — hủy phiếu thanh toán nghỉ phép bên
   Nghỉ phép*; `refresh_block_reason` trả lý do chặn; `record_refund` chặn; `create_requests` từ chối `source_type` lạ (giữ nguyên
   `SOURCE_TYPES`).
5. **Đọc ra** (`controller._out`): thêm `payee_employee_id`, `source_ref_id`, khối `leave_encashment` `{id, code, days,
   leave_type_name, balance_year, reason_kind}` khi nguồn nghỉ phép (một truy vấn). Không có lương, không có STK ở `_out`.
6. **Bản in (D2a)**: nguồn nghỉ phép lấy STK từ `Employee.bank_account_no/bank_name` CHỈ khi
   `sensitive.can_read_sensitive(get_perm_profile(db, user), payee_employee_id)` và `payment_method == "transfer"`; không thì rỗng
   + cờ `bank_hidden: true`. Người nhận in tên + mã nhân sự thay ô NCC.
7. **Chuông**: tạo YCTT nghỉ phép → `trigger_notification(event="pay_leave_created", recipients = get_approvers_for_entity(db,
   "payment_request", id, new_rules=True))`; thêm nhánh câu chữ *YCTT {code} — thanh toán nghỉ phép cần nhập số tiền* (chữ trơn, không
   số tiền). Các chuông `pay_*` cũ giữ nguyên (đã lọc phạm vi → chốt D1 áp sẵn).
8. **Rà đường đọc YCTT không qua `scope_condition`** (nghiên cứu mục 7): `supplier/service.py:74` (lọc theo `supplier_code` — nguồn
   nghỉ phép có mã rỗng, không dính), `payable/service.py:258` (theo `payable_id` — 0, không dính), `capability/cycle_specs.py`
   (đo thời gian, không tiền), `usage_profile/daily_docs.py` (đếm), `assistant/tools/procurement_doc_tool.py`,
   `assistant/datasets/catalog.py`, `assistant/tools/update_tool.py`, `assistant/change_service.py`, `core/attachment_scope.py`.
   Mỗi chỗ ghi kết luận vào báo cáo phase; chỗ nào trả số tiền mà không qua `apply_scope` → thêm `apply_scope` (không tự viết lọc).
9. **Bài kiểm** `test/backend/test_yctt_thanh_toan_nghi_phep_cr719.py`: hợp đồng 4 hàm; sửa chỉ được tiền; gửi duyệt tiền 0 → 400;
   chi không đụng công nợ; xóa → 400; bản in ẩn / hiện STK theo quyền; pur_staff không thấy qua danh sách, chi tiết, xuất Excel,
   tập dữ liệu AI, việc chờ duyệt của trợ lý; chuông không gửi cho người không thấy phiếu.

## Tệp sở hữu
Sửa: `backend/app/modules/payment_request/{service,controller,schema,export}.py`, `backend/app/modules/notification/service.py`,
các tệp ở mục 8 CHỈ khi phải thêm `apply_scope`. Tạo: `backend/app/modules/payment_request/leave_encashment_payout.py`,
`test/backend/test_yctt_thanh_toan_nghi_phep_cr719.py`. **Không** sửa `test_pham_vi_duong_vong.py` (phase 03 giữ) — thêm
truy vấn thẳng trong controller thì gửi dòng cần khai cho phase 03.

## Xong khi
Bài kiểm phase + các bài YCTT hiện có (`ls test/backend | grep -i "payment\|yctt"`) xanh; luồng YCTT NCC không đổi một con số.

## Rủi ro
| Rủi ro | K × T | Giảm |
|---|---|---|
| `service.py` 1033 dòng, nhánh mới rải nhiều hàm | Cao × TB | Gom luật nguồn nghỉ phép vào `leave_encashment_payout.py` (`is_payout(req)`, `check_payout_submit`) — `service.py` chỉ gọi |
| Ai đó gọi `create_requests` với `source_type="leave_encashment"` qua API | Thấp × Cao | Không thêm vào `SOURCE_TYPES`; bài kiểm |
| Không có vai trò Kế toán → YCTT kẹt Nháp | Cao × TB | Chuông rơi về quản trị (luật 3 của `get_approvers_for_entity`); tài liệu D-018 ở phase 06 |
