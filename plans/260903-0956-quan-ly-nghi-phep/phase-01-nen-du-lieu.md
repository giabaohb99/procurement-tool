# P-01 — Nền dữ liệu ✅ XONG (CR-259)

## Đã làm

| Việc | Ở đâu |
|---|---|
| Bộ mã **số** (R2/QĐ-11): trạng thái · buổi · đơn vị · giới tính | `backend/app/modules/leave/constants.py` |
| `tab_leave_type` + `tab_leave_type_seniority` + `tab_holiday` | `leave/catalog_model.py` |
| `tab_leave_balance` | `leave/balance_model.py` |
| `tab_leave_request` + `tab_leave_handover` | `leave/request_model.py` |
| `tab_employee` **thêm** `hire_date` (DATE, null) + `gender` (SMALLINT, mặc định 0) | `employee/model.py` |
| Migration | `migrations/versions/a3b31686db49_nghi_phep_nen_du_lieu_cr259.py` |
| Nạp model cho autogenerate | `core/all_models.py` — **ba** dòng, thiếu một là bỏ sót bảng |

## Quyết định đáng ghi

- **Số còn lại KHÔNG lưu thành cột.** Nó là hiệu của bốn khoản cộng trừ hai khoản
  trừ, tính ở `balance_service.remaining()`. Thêm cột `remaining` là có hai nguồn
  sự thật, và cái thứ hai sẽ lệch.
- **`pending_days` là cột bắt buộc**, không phải tối ưu: thiếu nó thì nộp mười đơn
  liền tay đều lọt vì đơn nào cũng thấy quỹ còn nguyên.
- **`gender` NOT NULL phải có `server_default='0'`** — bảng đang có dữ liệu, thiếu
  là MySQL từ chối thêm cột.
- **`hire_date` để NULL được**: hồ sơ cũ chưa ai nhập, và bịa một ngày cho mọi
  người thì thâm niên sai còn tệ hơn thâm niên trống (Q4).
- Migration đã **cắt tay**: `--autogenerate` kéo theo ~30 thay đổi không liên quan
  (`tab_assistant_*`, `tab_comment_*`, `tab_ticket*`…). Lý do ghi ở đầu tệp migration.

## Nghiệm thu

`alembic upgrade head` chạy sạch trên MySQL thật; sáu bảng có mặt, hai cột mới
đúng kiểu (`hire_date date YES`, `gender smallint NO default 0`).
