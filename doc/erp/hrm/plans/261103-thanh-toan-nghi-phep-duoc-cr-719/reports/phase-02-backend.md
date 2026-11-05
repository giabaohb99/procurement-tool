# Phase 02 — BE YCTT nguồn nghỉ phép (duoc-CR-719)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Hiệu lực | duoc-CR-719 |

Trạng thái: xong, chưa commit. Không đổi migration (cột đã có từ phase 01).

## Tệp đã đổi
Sửa: `payment_request/{service,controller,export}.py` (+53/-7), `notification/service.py` (nhánh `pay_leave_created`).
`payment_request/schema.py` KHÔNG đổi: không có lớp `PaymentRequestResponse` (controller trả dict dựng từ `HEADER`), nên hai
trường mới vào `HEADER` là đủ (danh sách, `_out`, tạo phiếu đều có).
Tạo: `payment_request/leave_encashment_payout.py` (gom toàn bộ luật nguồn nghỉ phép), `test/backend/test_yctt_thanh_toan_nghi_phep_cr719.py` (37 bài).

## Hàm phase 03 gọi (`from app.modules.payment_request import leave_encashment_payout as payout`)
```python
def create_payout_request(db, encashment, employee, actor: int) -> PaymentRequest   # flush, KHÔNG commit; 400 nếu phiếu đã có YCTT còn sống
def payout_state(db, payment_request_id: int) -> dict | None   # {id, code, status, status_label, total}; None khi id=0 / đã xóa mềm
def void_draft_payout(db, payment_request_id: int, actor: int) -> None   # Nháp -> xóa mềm (không commit); id 0/đã xóa -> bỏ qua; khác Nháp hoặc sai nguồn -> 400
def payout_allows_cancel(state: dict | None) -> bool   # True khi None, "draft", "cancelled"
```
**Hàm thứ năm, PHẢI gọi:** `notify_payout_created(db, req, background_tasks=None) -> None`. Gọi SAU KHI commit giao dịch duyệt phiếu
(nó commit chuông; bọc try/except, lỗi chuông chỉ ghi log). Lý do tách: `create_payout_request` cam kết không commit, mà
`trigger_notification` luôn commit — gọi chung sẽ commit lửng giao dịch duyệt của phase 03. Quên gọi = kế toán không nhận chuông.

Hằng/hàm phụ có thể dùng: `is_payout(req)`, `MSG_NO_DELETE`, `MAX_PAYOUT_AMOUNT`.

## Việc đã làm (theo mục phase file)
1. Sửa: `apply_payout_update` — chỉ `request_date, note, payment_method, print_texts, head_of_dept*` + `lines` đúng 1 dòng
   (`payable_id=0`, `po_code` rỗng hoặc đúng mã cũ, `offset_amount` None/0, 0 <= amount <= 9.999.999.999.999). `prepay=0` được
   chấp nhận (màn gửi lại nguyên form), `prepay=1` -> 400. `total = amount`. Khóa trạng thái Nháp giữ nguyên.
2. Gửi duyệt: `check_submit` nhánh đầu -> `check_payout_submit` (1 dòng, amount > 0 với câu *Nhập số tiền thanh toán nghỉ phép
   trước khi gửi duyệt*, cấm cấn trừ, cấm trả trước, không khớp công nợ).
3. Duyệt/chi: `set_status` bỏ `apply_line_offsets`; `paid` -> `mark_payout_paid` (`allocated_amount = amount`), không đụng công nợ / ĐMH.
4. Chặn: `delete_request`, xóa nhiều (kiểm trước ở `bulk_delete_requests`), `record_refund`, `refresh_block_reason` (nên
   `apply_refresh` 400, `plan` `can_apply=False`); `create_requests` 400 khi `source_type == "leave_encashment"`
   (các `source_type` lạ khác vẫn rơi về `goods` như cũ để không đổi hành vi YCTT NCC; `SOURCE_TYPES` giữ nguyên).
5. `_out`/danh sách: `payee_employee_id`, `source_ref_id` (vào `HEADER`); khối `leave_encashment` một truy vấn (outer join loại nghỉ);
   `_out` bỏ qua `plan_refresh` cho nguồn này. Không lương, không STK.
6. Bản in D2a: `print_payee_info` — STK lấy từ `Employee.bank_account_no/bank_name` chỉ khi `transfer` VÀ `can_read_sensitive(profile, payee)`
   (khóa `employee_sensitive.read` hoặc chính chủ); không thì rỗng + `bank_hidden: true`. Tiền mặt: rỗng, `bank_hidden: false`.
   Thêm `payee {employee_id, code, full_name}` cho bản in. Excel: nhãn nguồn "Thanh toán nghỉ phép".
7. Chuông: `notify_payout_created` -> `trigger_notification(event="pay_leave_created", doc_id=req.id)`; nhánh trong `trigger_notification`
   dùng `get_approvers_for_entity(..., new_rules=True)` (đã lọc phạm vi + chốt D1a, rơi về quản trị). Chữ trơn, không số tiền/ngày.
   Các chuông `pay_approved/rejected/paid` đi cho `created_by` = 0 -> không ai nhận (không rò; xem câu hỏi 1).

## Rà đường đọc YCTT không qua `scope_condition` (mục 8)
Chốt D1a nằm trong `scope_condition` nên mọi đường `apply_scope` / `get_scoped` / `get_approvers_for_entity` đã phủ.
| Đường | Kết luận |
|---|---|
| `payment_request/controller` list, export, `get_`, `print_`, ghi (`_scoped`), xóa nhiều | đều qua `apply_scope`/`get_scoped`; có bài kiểm (a1 không thấy, 403/404) |
| `controller._line` `db.get(PaymentRequest, ln.request_id)` | nội bộ, chỉ chạy sau khi phiếu đã qua phạm vi; không cần đổi |
| `/hanging`, `summarize_hanging`, `get_hanging_lines` | lọc `supplier_code` rỗng trả `[]`, và `prepay=1` -> không dính |
| `assistant/datasets/catalog.py` (+ `base.run`) | `apply_scope(..., "payment_request")`; có bài kiểm (tổng/đếm chỉ thấy phiếu thường) |
| `assistant/tools/procurement_doc_tool.py` việc chờ duyệt | `apply_scope`; có bài kiểm |
| `assistant/tools/payable_tool.py` `payment_request_read` | `apply_scope` theo mã; ok |
| `assistant/tools/update_tool.py`, `change_service.py` | `get_scoped` (sửa/xóa/hoàn tác); sửa đi qua `update_request` nên chịu luật nguồn mới; xóa -> `delete_request` 400 |
| `core/attachment_scope.py` (`_live(PaymentRequest)` + `ensure_in_scope` -> `apply_scope`) | ok, đính kèm theo phạm vi của phiếu |
| `notification/service.py` `_filter_by_doc_scope` | `get_scoped` action approve; có bài kiểm chuông chỉ tới người thấy phiếu |
| `supplier/service.py:74` | lọc `supplier_code`; mã rỗng không khớp NCC nào |
| `payable/service.py:258` | đếm theo `payable_id` — dòng nghỉ phép có `payable_id=0`, không dính |
| `purchase_order/edit_service.py:345` | nối theo `po_code` = mã ĐMH; dòng mang mã phiếu `TTP…`, không trùng |
| `capability/cycle_specs.py` | đo thời gian chu trình theo bảng thô, gộp số, không tiền; phiếu nghỉ phép có góp vào số đo chu trình YCTT (chấp nhận, không lộ chi tiết) |
| `usage_profile/daily_docs.py` | đếm dòng audit theo động từ, không tiền |
| `approval_tool` / `task_notification` | chỉ bảng nhãn + đường dẫn, không truy vấn YCTT |
| `department|employee|company/references.py` | đếm chặn xóa, không lộ nội dung (xem câu hỏi 2) |
Không phải thêm `apply_scope` nào ngoài tệp sở hữu.

## Kiểm
- `test_yctt_thanh_toan_nghi_phep_cr719.py`: 37 bài xanh (hợp đồng, sửa chỉ tiền, tiền 0 -> 400, chi không đụng công nợ, xóa 400,
  in ẩn/hiện STK theo quyền/chính chủ/tiền mặt, a1 không thấy qua danh sách + chi tiết + in + ghi + xuất Excel + tập dữ liệu AI +
  việc chờ duyệt, chuông).
- Hồi quy xanh (một tiến trình mỗi lượt): 9 tệp YCTT/payment + `test_thanh_toan_nghi_phep_nen_cr719` + `khai_du_b07` + `duong_vong` +
  `luat_bat_bien` + 3 tệp assistant (dataset, procurement_doc, pham_vi_doc) = 240 xanh; `cr538` + `xoa_mem_cr176` +
  `bo_may_duyet_xuyen_suot` = 97 xanh; `can_tru_cr260` + `tien_treo_cr268` = 33 xanh.
- Không chạy: toàn bộ `test/backend`, frontend.

## Dòng phase 03 phải khai / làm
- Gọi `notify_payout_created` sau commit duyệt (xem trên).
- Không có truy vấn thẳng mới nào trong controller cần khai vào `test_pham_vi_duong_vong.py` (mọi đọc đều qua `apply_scope`/`get_scoped`).
- Hủy phiếu: `payout_state` -> `payout_allows_cancel` -> `void_draft_payout` (Nháp) hoặc để nguyên YCTT đã từ chối.

## Câu hỏi còn mở
1. Khi YCTT nghỉ phép được duyệt / từ chối / chi, không ai nhận chuông (vì `created_by = 0` theo spec). Có muốn báo cho người thao
   tác cuối (`updated_by`) hoặc nhân sự Nhân sự lập phiếu không? Chưa làm vì ngoài spec.
2. `employee/references.py` chưa có `Reference(PaymentRequest, "payee_employee_id", ...)`: xóa cứng một nhân sự đang là người nhận
   YCTT nghỉ phép không bị chặn. Tệp ngoài sở hữu phase 02; đề nghị phase 03 hoặc lead thêm một dòng.
3. `create_requests` vẫn đổi `source_type` lạ khác thành `goods` im lặng (hành vi cũ giữ nguyên); chỉ `leave_encashment` bị 400.

**Status:** DONE
**Summary:** YCTT nguồn nghỉ phép xong: bốn hàm hợp đồng + `notify_payout_created`, luật sửa/gửi duyệt/chi/xóa, bản in D2a, chuông, rà đủ đường đọc, 37 bài mới và hồi quy xanh.
**Concerns/Blockers:** Phase 03 phải gọi `notify_payout_created` sau commit; `employee/references.py` thiếu chặn xóa người nhận (ngoài phạm vi).
