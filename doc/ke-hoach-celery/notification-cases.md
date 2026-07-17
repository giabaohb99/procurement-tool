# Các CASE thông báo — liệt kê rõ để dễ làm

Mục đích: gom TẤT CẢ trường hợp gửi thông báo (hiện có + sắp làm) — **sự kiện · nơi kích · ai nhận · kênh** — làm chuẩn khi chuyển sang Celery.

## Kênh thông báo
- **Chuông (in-app)**: tạo bản ghi `Notification` → hiện ở `NotificationBell` + trang `/notifications`. **Luôn có.**
- **Push (Web Push)**: đẩy tới thiết bị đã bật (`push_service.send_to_users`). **Best-effort**, thiết bị phải subscribe.
- **Email**: **KHÔNG dùng cho workflow** (chỉ cấp tài khoản / reset mật khẩu). Khi làm Phase 1 → **viết code nhưng comment**, chưa bật.

## Hàm xác định người nhận (tái dùng — `notification/service.py`)
- `get_department_head_users(db, dept)` — Trưởng bộ phận của phòng.
- `get_approvers_for_entity(db, entity)` — người có quyền `approve` trên entity đó.
- `get_users_by_role_codes(db, ["pur_manager","pur_admin"])` — Quản lý TM + Admin TM.
- `_users_of_codes(db, [ma_NV])` — tài khoản theo mã nhân viên (NSTM được gán).
- "Người tạo" = `created_by`; "Người yêu cầu" = `requester_id` (nếu admin tạo giùm).

---

## A. Theo THAO TÁC (event-driven) — ĐÃ CÓ

### A1. Yêu cầu mua hàng (PYC · purchase_request) — qua `trigger_notification`
| Sự kiện | Nơi kích (endpoint) | Người nhận | Kênh |
|---|---|---|---|
| `pr_submitted` Gửi duyệt | `POST /purchase-requests/{id}/submit` | Trưởng bộ phận của phòng | chuông + push |
| `pr_approved` Duyệt | `/approve` | Người tạo **+ Quản lý TM + Admin TM** | chuông + push |
| `pr_rejected` Từ chối | `/reject` | Người tạo | chuông + push |
| `pr_returned` Trả về | `/return` | Người tạo | chuông + push |
| `pr_cancelled` Hủy | `/cancel` | Người tạo | chuông + push |
| `pr_assigned` Phân bổ NSTM | `/assign` | NSTM được gán | chuông + push |

### A2. Yêu cầu khảo sát (YCKS · survey_request) — qua helper `_notify`
| Sự kiện | Nơi kích | Người nhận | Kênh |
|---|---|---|---|
| Gửi duyệt | `/submit` | Người duyệt (approvers survey_request) + Trưởng BP | chuông + push |
| Duyệt | `/approve` | Người tạo + QL TM + Admin TM; **+ NSTM tự gán theo phân loại** | chuông + push |
| Trả đơn (rejected) | `/reject` | Người tạo | chuông + push |
| Từ chối (cancelled) | `/cancel` | Người tạo | chuông + push |
| Gán NSTM 1 dòng | `/lines/{id}/assignee` | NSTM được gán | chuông + push |
| Khảo sát xong | `/complete` | Người tạo | chuông + push |
| Sinh YCMH | `/create-prs` | Quản lý TM + Admin TM | chuông + push |
| Chuyển Hoàn thành | `/finalize` | Người tạo | chuông + push |

### A3. Phiếu khảo sát (survey) — qua `trigger_notification`
| Sự kiện | Nơi kích | Người nhận | Kênh |
|---|---|---|---|
| `survey_submitted` Gửi duyệt | `/submit` | Người duyệt (approvers survey) | chuông + push |
| `survey_approved` Duyệt | `/approve` | Người tạo | chuông + push |
| `survey_rejected` Trả lại/Từ chối | `/reject`, `/cancel` | Người tạo | chuông + push |

### A4. Yêu cầu thanh toán (YCTT · payment_request) — qua `trigger_notification`
| Sự kiện | Nơi kích | Người nhận | Kênh |
|---|---|---|---|
| `pay_submitted` Gửi duyệt | `/submit` | Người duyệt (approvers payment_request) | chuông + push |
| `pay_approved` Duyệt | `/approve` | Người tạo | chuông + push |
| `pay_rejected` Từ chối | `/reject` | Người tạo | chuông + push |
| `pay_paid` Đã chi | `/pay` | Người tạo | chuông + push |

### A5. Đơn mua hàng (PO · purchase_order) — qua `trigger_notification`
| Sự kiện | Nơi kích | Người nhận | Kênh |
|---|---|---|---|
| `po_rejected` Từ chối | `/reject` | Người tạo | chuông + push |
| `po_returned` Trả về | `/return` | Người tạo | chuông + push |

> **Khi làm Phase 1**: các call trên đang chạy `BackgroundTasks` → đổi sang Celery task (push có retry). Chuông vẫn tạo đồng bộ trong request; **push đẩy qua worker**; email giữ **comment**.

---

## B. Theo LỊCH (scheduled) — SẼ LÀM (Phase 2)

Chạy bằng Celery beat (mỗi sáng), sinh chuông + push cho đúng người. Idempotent (đánh dấu "đã báo mục X hôm nay" — bảng `tab_alert_sent`). Chi tiết: [phase-2](phase-2-canh-bao-theo-lich.md).

| Nhóm | Điều kiện quét | Người nhận (dự kiến) |
|---|---|---|
| Công nợ | payable sắp/đến/quá hạn trả | Người phụ trách / QL TM |
| Giao hàng | ĐMH giao trễ / sắp tới hạn giao (`expected_date`, chưa nhận đủ) | NSPT phụ trách đơn |
| Hợp đồng | `contract.end_date` sắp hết hạn | Người tạo HĐ / Admin |
| **SLA** | PYC/YCKS/YCTT **chờ duyệt quá X ngày** | Người duyệt (+ leo thang) |
| **SLA** | YCKS đã duyệt nhưng NSTM chưa khảo sát lâu | NSTM |
| **Ngày cần hàng** | PYC/ĐMH sắp/quá `need_date`/`required_date` chưa nhận đủ | Người phụ trách / người tạo |
| **Thanh toán** | YCTT approved chưa `paid` quá lâu | QL TM |

---

## Ghi chú khi hiện thực
- Mỗi case cần **chống trùng người nhận** (dedup theo user id) — hàm hiện có đã khử trùng.
- Case theo lịch phải **idempotent** (không báo lại cùng mục trong ngày).
- Người nhận có thể **chưa có tài khoản** (mã NV → employee → user); nếu không có user thì bỏ qua, không lỗi.
