# Requirement chi tiết — CƠ CHẾ PHÊ DUYỆT & THÔNG BÁO EMAIL

> Áp dụng cho mọi chứng từ có luồng duyệt: **PYC, Khảo sát NCC/SP, PO, Thanh toán**.
> Mục tiêu: 1 cơ chế duyệt dùng chung (không code lặp) + hệ thống thông báo (in-app + email) có cấu hình & log.

---

# PHẦN 1 — CƠ CHẾ PHÊ DUYỆT (APPROVAL)

## 1.1 Vòng trạng thái chuẩn theo chứng từ
| Chứng từ | Trạng thái |
|---|---|
| PYC (`purchase_request`) | `draft` → `submitted` → `approved` / `rejected` → (`completed`) |
| Khảo sát (`survey`) | `draft` → `submitted` → `approved` / `rejected` |
| Đơn mua (`purchase_order`) | `draft` → `pending` → `approved` → `ordering` → `received` → `completed` / `cancelled` |
| Thanh toán (`payment`) | `draft` → `pending` → `paid` |

## 1.2 Hành động & quy tắc
| Hành động | API | Điều kiện trạng thái | Quyền | Ghi chú |
|---|---|---|---|---|
| Gửi duyệt | `POST /{entity}/{id}/submit` | `draft`/`rejected` | `write` hoặc `create` | → `submitted`/`pending` |
| Duyệt | `POST /{entity}/{id}/approve` | `submitted`/`pending` | `approve` + thỏa **ngưỡng** | → `approved`; có thể gán NSPT |
| Từ chối | `POST /{entity}/{id}/reject` | `submitted`/`pending` | `approve` | **bắt buộc `reason`**; → `rejected` (về sửa lại) |
| Thu hồi (tùy chọn) | `POST /{entity}/{id}/recall` | `submitted` | người gửi | → `draft` |

**Nguyên tắc bất biến:**
- Chỉ **sửa** chứng từ khi `draft`/`rejected`. Đã `submitted`/`approved` → khóa form (chỉ xem).
- **Từ chối** phải kèm `reason` → ghi vào audit log + hiển thị ở timeline.
- Mọi submit/approve/reject → **ghi `tab_audit_log`** (action = trạng thái mới, message = lý do nếu có) + **bắn thông báo** (Phần 2).
- Sau `approved`: mở khóa bước kế (PYC approved → cho tạo Khảo sát/PO; PO approved → cho gửi NCC; …).

## 1.3 Phân cấp duyệt theo NGƯỠNG (multi-level, cấu hình được)
Bảng cấu hình:
```
tab_approval_rule(
  id, entity, level INT, min_amount DECIMAL(18,2), max_amount DECIMAL(18,2),
  approver_role_code VARCHAR(25)   -- vai trò được duyệt ở mức này
)
```
**Engine duyệt:**
1. Tính `total` của chứng từ (vd PYC = tổng thanh toán).
2. Tìm rule có `entity` khớp & `min_amount ≤ total ≤ max_amount`.
3. Yêu cầu người duyệt có **vai trò = `approver_role_code`** của rule (hoặc cao hơn).
4. Nếu nhiều `level` → duyệt **tuần tự** (lưu `current_level` trên chứng từ; duyệt xong level 1 mới tới level 2). Khi hết level → `approved`.

**Hiện tại (mặc định):** 1 rule duy nhất `level=1, min=0, max=∞, approver_role_code=qltm` → **QLTM là cấp cao nhất**. Khi cần thêm BOD: thêm rule `level=2, min=50.000.000, …, approver_role_code=bod`.

**Đơn gấp (`is_urgent=true`):** vẫn cần duyệt nhưng **đánh dấu ưu tiên** (badge đỏ + đẩy lên đầu danh sách chờ duyệt + email tiêu đề có `[GẤP]`).

**Ủy quyền khi vắng (tùy chọn Phase sau):** `tab_delegation(from_user, to_user, from_date, to_date)` — người được ủy quyền có quyền duyệt thay trong khoảng thời gian.

## 1.4 Backend — service dùng chung
```
core/approval.py:
  can_approve(db, user, entity, total) -> bool   # check role theo ngưỡng
  transition(db, doc, action, user, reason="") -> doc
     - validate trạng thái hợp lệ + quyền + ngưỡng
     - đổi status, set current_level/approver
     - record audit log
     - enqueue notification (Phần 2)
```
Mỗi module gọi `transition(...)` trong endpoint submit/approve/reject (không tự code lại).

## 1.5 Giao diện
- Nút **Gửi duyệt / Duyệt / Từ chối** hiện theo trạng thái + quyền (đã làm ở PYC — chuẩn hóa cho mọi chứng từ).
- Từ chối → mở hộp nhập **lý do** (bắt buộc).
- **Badge trạng thái** + (nếu multi-level) "Chờ duyệt cấp N".
- Màn **"Chờ tôi duyệt"** (Dashboard/menu): danh sách chứng từ ở `submitted/pending` mà user có quyền duyệt; đơn gấp lên đầu.

## 1.6 Tiêu chí ĐẠT (phê duyệt)
- [ ] Submit/Approve/Reject đúng điều kiện trạng thái; sai trạng thái → chặn.
- [ ] Chỉ người có quyền `approve` (và đúng ngưỡng) mới duyệt được; người khác bị 403 + ẩn nút.
- [ ] Từ chối bắt buộc lý do; chứng từ về `rejected` và sửa lại được.
- [ ] Mỗi bước ghi log (ai/hành động/thời gian/lý do) + bắn thông báo.
- [ ] Đổi `tab_approval_rule` (thêm cấp/ngưỡng) → luồng duyệt thay đổi đúng, KHÔNG sửa code.
- [ ] Đơn gấp ưu tiên hiển thị + email `[GẤP]`.

---

# PHẦN 2 — THÔNG BÁO (IN-APP + EMAIL)

## 2.1 Kiến trúc gửi
- **Phase 1 (cơ bản):** gửi qua **FastAPI `BackgroundTasks`** (không chặn request). Đủ cho mốc giao việc/chờ duyệt/kết quả.
- **Phase 3 (đầy đủ):** chuyển sang **Celery Worker + Beat + Redis** để: retry khi lỗi, và **chạy lịch định kỳ** (nhắc hạn, công nợ, HĐ).
- Mỗi sự kiện tạo: **1 bản ghi in-app** (`tab_notification`) + **1 email** (nếu bật) → ghi `tab_email_log`.

## 2.2 Bảng
```
tab_notification(id, user_id, title, body, link, is_read, created_at)
tab_email_template(id, code, subject, body, is_active)   -- Phase sau cho sửa; trước mắt Jinja trong code
tab_email_log(id, event, to_email, subject, status, error, created_at, sent_at)  -- status: pending/sent/failed
```

## 2.3 Cấu hình (Setting / .env)
- SMTP: `SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM` (hoặc Resend/SendGrid `API_KEY`).
- Màn **Setting → Email**: bật/tắt **từng sự kiện**; người nhận theo **vai trò**; thêm **CC/BCC**; tần suất (gửi ngay / tổng hợp cuối ngày); mẫu nội dung (Phase sau).

## 2.4 DANH SÁCH SỰ KIỆN (trigger) — đầy đủ
| # | Sự kiện | Người nhận | Biến template chính | Kênh | Phase |
|---|---|---|---|---|---|
| 1 | Giao việc khảo sát/PYC cho NSTM | NSTM được giao | `code, purpose, deadline, assigner` | in-app+email | 1 |
| 2 | Chứng từ **chờ duyệt** (PYC/Survey/PO) | người duyệt (theo ngưỡng) | `code, type, total, requester` | in-app+email | 1 |
| 3 | Kết quả **Duyệt** | người gửi (+ BPYC) | `code, approver, note` | in-app+email | 1 |
| 4 | Kết quả **Từ chối** | người gửi | `code, approver, reason` | in-app+email | 1 |
| 5 | Có **kết quả test LAB** | NSTM phụ trách | `survey_code, product, lab_result` | in-app+email | 1 |
| 6 | PO **đã duyệt** | NSTM | `po_code, supplier` | in-app+email | 2 |
| 7 | Đơn **sắp tới hạn giao** (D-1) | NSTM | `po_code, need_date, supplier` | email (Beat) | 3 |
| 8 | Đơn **trễ hạn** (chênh lệch ngày < 0) | NSTM + QLTM | `po_code, days_late` | in-app+email (Beat) | 3 |
| 9 | Hàng đã về – **cần nghiệm thu** | BPYC | `po_code, received_qty` | in-app+email | 3 |
| 10 | **Công nợ tới hạn** (trước ngày 12 hằng tháng) | NSTM + Kế toán | `supplier, amount, due` | email (Beat) | 4 |
| 11 | **Hợp đồng sắp hết hạn** | NSTM + QLTM | `contract_no, supplier, expire_date` | email (Beat) | 4 |
| 12 | **Cấp tài khoản mới** | nhân viên | `employee_code, temp_password, login_url` | email | 1 |
| 13 | Yêu cầu **khai báo mã MISA** | Admin/Kế toán | `supplier, product` | in-app+email | 2 |

> Đơn gấp: tiêu đề email prefix `[GẤP]` cho sự kiện #2.

## 2.5 Lịch định kỳ (Celery Beat — Phase 3)
| Job | Tần suất | Logic |
|---|---|---|
| Nhắc D-1 | hằng ngày 08:00 | quét PO có `need_date = mai`, status chưa nhận đủ → gửi #7 |
| Cảnh báo trễ hạn | hằng ngày 08:00 | quét delivery `chênh lệch ngày < 0` & chưa nhận đủ → #8 |
| Công nợ tới hạn | hằng ngày | quét payable `due_date ≤ ngày 12` chưa thanh toán → #10 |
| HĐ sắp hết hạn | hằng ngày | quét contract `expire_date ≤ +15 ngày` → #11 |

## 2.6 Mẫu email (ví dụ — Jinja)
```
[Chờ duyệt] {{type}} {{code}} cần duyệt
Xin chào {{approver}},
{{requester}} vừa gửi {{type}} {{code}} (tổng {{total}} đ) chờ anh/chị duyệt.
Mở duyệt: {{link}}
```

## 2.7 Backend — service
```
core/notify.py:
  notify(db, event, recipients, context, link)
     - tạo tab_notification cho từng user
     - nếu event bật email & có email → render template + gửi (BackgroundTasks/Celery) + ghi tab_email_log
  resolve_recipients(db, role_codes/users) -> [users có email]
```
Gọi `notify(...)` bên trong `approval.transition(...)` và tại các điểm nghiệp vụ (giao việc, LAB, GR…).

## 2.8 Tiêu chí ĐẠT (thông báo)
- [ ] 3 mốc cơ bản (giao việc, chờ duyệt, kết quả duyệt/từ chối) tạo **in-app + email** đúng người nhận.
- [ ] Email có **log** (sent/failed) + (Phase 3) **retry** khi lỗi.
- [ ] Bật/tắt được từng sự kiện ở Setting; người nhận theo vai trò.
- [ ] (Phase 3) các job Beat chạy đúng lịch, không trùng/sót.
- [ ] Cấp tài khoản mới gửi email mật khẩu tạm; đơn gấp có prefix `[GẤP]`.

---

## PHỤ LỤC — Hợp đồng API (cho subagent BE)
- `POST /api/{entity}/{id}/submit|approve|reject` body: `{ reason?, assignee_id? }` → trả chứng từ sau cập nhật (envelope `{success,data}`).
- `GET /api/notifications?unread=1` · `POST /api/notifications/{id}/read`.
- `GET /api/settings/email` · `PUT /api/settings/email` (bật/tắt sự kiện, người nhận, SMTP).
- `GET /api/approval-rules` · `PUT /api/approval-rules` (cấu hình ngưỡng duyệt).
