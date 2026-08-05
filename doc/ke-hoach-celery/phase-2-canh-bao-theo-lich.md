# Phase 2 — Cảnh báo theo lịch ⭐

> Phần quan trọng nhất của kế hoạch Celery. Gộp **B1 SLA**, **B2 ngày cần hàng**, **B3 thanh toán** vào 1 khung job chạy mỗi sáng.
>
> Phụ thuộc: **Phase 0 (hạ tầng)** phải hoàn thành trước — Redis + worker + beat phải đang chạy.

---

## 1. Mục tiêu

Hệ thống **chủ động nhắc** người liên quan hàng ngày về các sự kiện quan trọng mà không cần ai vào xem thủ công:

| Nhóm | Vấn đề hiện tại | Kết quả sau phase |
|---|---|---|
| Giao hàng | Chỉ thấy chuông khi mở app | Nhắc chủ động lúc 8h sáng qua chuông + web push |
| Công nợ | Như trên | Như trên |
| Hợp đồng | Như trên | Như trên |
| **B1** SLA | Phiếu nằm yên không ai nhắc duyệt | Tự nhắc người duyệt/người phụ trách khi trễ hạn |
| **B2** Ngày cần hàng | Không theo dõi `need_date`/`required_date` | Nhắc trước và báo quá ngày cần hàng chưa nhận đủ |
| **B3** Thanh toán | Không nhắc khi YCTT đã duyệt mà chưa chi | Nhắc QL/kế toán ghi nhận chi |

Tất cả cảnh báo đều **idempotent** (báo mỗi đối tượng tối đa 1 lần/ngày) và dùng lại hàm `trigger_notification` + web push hiện có.

---

## 2. Phạm vi & việc cụ thể

### 2.1 Nhóm giao hàng — tái dùng logic `build()` từ `alert/controller.py`

- [ ] **Giao trễ**: `PODelivery.received_qty <= 0` + ngày hẹn (`expected_date` hoặc `promised_date`) < hôm nay
- [ ] **Sắp tới hạn giao** (trong 2 ngày): như trên nhưng `due ≤ today+2`

Người nhận: NSTM phụ trách PO (`PurchaseOrder.created_by`) + QL TM (`pur_manager`).

### 2.2 Nhóm công nợ — tái dùng logic `build()`

- [ ] **Quá hạn**: `Payable.status != "Đã TT"` + `Payable.due_date < today`
- [ ] **Sắp đến hạn** (trong 3 ngày): `due_date ≤ today+3`

Người nhận: QL TM (`pur_manager`), kế toán (`accountant`) nếu role tồn tại.

### 2.3 Hợp đồng sắp hết hạn — tái dùng logic `build()`

- [ ] **Hết hạn**: `Contract.status != "Thanh lý"` + `Contract.end_date < today`
- [ ] **Sắp hết hạn** (trong 30 ngày): `end_date ≤ today+30`

Người nhận: QL TM (`pur_manager`).

### 2.4 B1 — SLA: workflow bị treo

Mục tiêu: phát hiện phiếu bị "kẹt" ở trạng thái chờ quá lâu và nhắc đúng người.

- [ ] **PYC chờ duyệt quá 2 ngày**: `PurchaseRequest.status = "submitted"` + `updated_at < today - 2 ngày`  
  → Nhắc trưởng phòng bộ phận (`department`) + QL TM (`pur_manager`)
- [ ] **YCKS chờ duyệt quá 2 ngày**: `SurveyRequest.status = "submitted"` + `updated_at < today - 2 ngày`  
  → Nhắc người có quyền duyệt `survey_request`
- [ ] **YCKS đã duyệt nhưng chưa có phương án quá 5 ngày**: `SurveyRequest.status IN ("approved","processing")` + `updated_at < today - 5 ngày` + chưa sang `survey_done`  
  → Nhắc NSTM phụ trách **theo từng dòng** (`SurveyRequestLine.assignee`, mã NV → tài khoản).
  KHÔNG dùng `SurveyRequest.assignee_id` — trường header đã bỏ (CR-018); mỗi dòng có hạn trả kết quả riêng nên nhắc theo dòng mới đúng.
- [ ] **YCTT chờ duyệt quá 2 ngày**: `PaymentRequest.status = "submitted"` + `updated_at < today - 2 ngày`  
  → Nhắc người có quyền duyệt `payment_request`
- [ ] **Dòng PYC "Chưa đặt hàng" tồn quá 5 ngày sau khi PYC được duyệt**: `PurchaseRequestItem.line_status = "Chưa đặt hàng"` + PYC cha `status = "approved"` + PYC `updated_at < today - 5 ngày`  
  → Nhắc `PurchaseRequestItem.assignee` (mã NV → user), fallback sang QL TM
- [ ] **Dòng POItem "Chưa đặt hàng" tồn quá 5 ngày sau khi PO approved**: `POItem.progress_status = "Chưa đặt hàng"` + PO cha `status = "approved"` + PO `updated_at < today - 5 ngày`  
  → Nhắc người tạo PO (`created_by`) + QL TM

### 2.5 B2 — Ngày cần hàng

Mục tiêu: theo dõi `need_date`/`required_date` thay vì chỉ `expected_date` giao hàng.

- [ ] **PYC sắp tới `need_date`** (trong 3 ngày) mà PYC chưa có PO nhận đủ:  
  `PurchaseRequest.status = "approved"` + `need_date ≤ today+3` + `need_date != ""`  
  → Nhắc `PurchaseRequest.assignee_id` + QL TM
- [ ] **PYC quá `need_date`** chưa nhận đủ:  
  `need_date < today` + `status = "approved"` (chưa hoàn thành)  
  → Nhắc như trên, level `danger`
- [ ] **Dòng PYC**: `PurchaseRequestItem.required_date ≤ today+3` hoặc `< today` + `line_status NOT IN ("Đủ", "Đã nhận đủ")`  
  → Nhắc `PurchaseRequestItem.assignee` → user
- [ ] **Dòng POItem**: `POItem.required_date ≤ today+3` hoặc `< today` + `qty_received < qty_order` + PO `status NOT IN ("received","cancelled")`  
  → Nhắc người tạo PO (`PurchaseOrder.created_by`) + QL TM

### 2.6 B3 — Nhắc thanh toán

- [ ] **YCTT đã duyệt nhưng chưa paid quá 3 ngày**: `PaymentRequest.status = "approved"` + `updated_at < today - 3 ngày`  
  → Nhắc QL TM (`pur_manager`), kế toán (`accountant`)
- [ ] Công nợ sắp/quá hạn đã xử lý ở **2.2** — B3 không tạo thêm loại, chỉ đảm bảo người nhận đúng

---

## 3. Thiết kế kỹ thuật

### 3.1 File tạo mới / sửa

| Hành động | File |
|---|---|
| Tạo mới | `backend/app/tasks/__init__.py` |
| Tạo mới | `backend/app/tasks/alert_tasks.py` — task tổng + 6 hàm quét |
| Tạo mới | `backend/migrations/versions/xxxx_add_tab_alert_sent.py` — migration bảng chống trùng |
| Sửa | `backend/app/core/celery_app.py` — thêm `beat_schedule` cho `scan_alerts` |
| Sửa | `backend/app/core/all_models.py` — import model `AlertSent` để Alembic thấy |

Không sửa `alert/controller.py` — hàm `build()` vẫn dùng để phục vụ chuông realtime (GET request). Task Celery viết hàm quét riêng để độc lập với HTTP session.

### 3.2 Kiến trúc: 1 task tổng, N hàm quét con

```
scan_alerts()   ← Celery task, chạy 8h sáng VN
  ├── scan_delivery_alerts(db, today)
  ├── scan_payable_alerts(db, today)
  ├── scan_contract_alerts(db, today)
  ├── scan_sla_alerts(db, today)        ← B1
  ├── scan_need_date_alerts(db, today)  ← B2
  └── scan_payment_alerts(db, today)   ← B3
```

Mỗi hàm quét:
1. Truy vấn DB lấy danh sách đối tượng cần cảnh báo.
2. Với mỗi đối tượng: kiểm tra `already_sent()` — nếu đã báo hôm nay thì bỏ qua.
3. Xác định `recipient_ids`.
4. Gọi `trigger_notification(db, ..., background_tasks=None, recipient_ids=...)`.
5. Gọi `mark_sent()`.

### 3.3 Code phác thảo — task tổng

```python
# backend/app/tasks/alert_tasks.py
from datetime import date, timedelta
from celery import shared_task
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.modules.notification.service import trigger_notification, get_users_by_role_codes, get_department_head_users
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.contract.model import Contract
from app.modules.payment_request.model import PaymentRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User, UserRole


@shared_task(name="alert.scan_alerts", bind=True, max_retries=3)
def scan_alerts(self):
    """Quét toàn bộ cảnh báo và sinh thông báo. Chạy mỗi sáng 8h VN."""
    db = SessionLocal()
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    try:
        scan_delivery_alerts(db, today, today_str)
        scan_payable_alerts(db, today, today_str)
        scan_contract_alerts(db, today, today_str)
        scan_sla_alerts(db, today, today_str)
        scan_need_date_alerts(db, today, today_str)
        scan_payment_alerts(db, today, today_str)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=300)   # retry sau 5 phút
    finally:
        db.close()
```

### 3.4 Code phác thảo — hàm quét mẫu: công nợ (scan_payable_alerts)

```python
def scan_payable_alerts(db: Session, today: date, today_str: str):
    warn_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")
    payables = (
        db.query(Payable)
        .filter(Payable.status != "Đã TT", Payable.due_date != "")
        .all()
    )
    recipients = get_users_by_role_codes(db, ["pur_manager", "accountant"])
    recipient_ids = [r.id for r in recipients] if recipients else []

    for p in payables:
        if not p.due_date:
            continue
        if p.due_date < today_str:
            kind = "payable_overdue"
            msg_title = f"[Cảnh báo] Công nợ QUÁ HẠN: {p.supplier_name} · {p.po_code} (hạn {p.due_date})"
        elif p.due_date <= warn_date:
            kind = "payable_due_soon"
            msg_title = f"[Nhắc] Công nợ sắp đến hạn: {p.supplier_name} · {p.po_code} (hạn {p.due_date})"
        else:
            continue

        if already_sent(db, "payable", p.id, kind, today_str):
            continue

        link = f"/payables?po_code={p.po_code}" if p.po_code else "/payables"
        trigger_notification(
            db=db,
            event=kind,
            doc_type="payable",
            doc_code=p.po_code or str(p.id),
            creator_id=0,          # hệ thống tự tạo, không có creator thực
            background_tasks=None, # worker gọi trực tiếp, không dùng FastAPI BackgroundTasks
            link=link,
            recipient_ids=recipient_ids,
        )
        mark_sent(db, "payable", p.id, kind, today_str)
```

> **Lưu ý `trigger_notification`**: khi `background_tasks=None`, hàm push service gọi `push_service.send_to_users(SessionLocal, ...)` trực tiếp (không phải nền). Trong worker Celery điều này ổn vì task đang chạy bất đồng bộ rồi.

### 3.5 Code phác thảo — B1: SLA phiếu chờ duyệt

```python
def scan_sla_alerts(db: Session, today: date, today_str: str):
    # --- PYC chờ duyệt quá 2 ngày ---
    cutoff_2d = (today - timedelta(days=2))
    stale_prs = (
        db.query(PurchaseRequest)
        .filter(
            PurchaseRequest.status == "submitted",
            PurchaseRequest.is_deleted == False,
            PurchaseRequest.updated_at < cutoff_2d,
        )
        .all()
    )
    for pr in stale_prs:
        kind = "sla_pr_pending"
        if already_sent(db, "purchase_request", pr.id, kind, today_str):
            continue
        dept_users = get_department_head_users(db, pr.department)
        mgr_users = get_users_by_role_codes(db, ["pur_manager"])
        r_ids = list({u.id for u in dept_users + mgr_users})
        if not r_ids:
            continue
        trigger_notification(
            db=db, event=kind, doc_type="purchase_request",
            doc_code=pr.code, creator_id=pr.created_by,
            background_tasks=None,
            link=f"/purchase-requests/{pr.id}",
            recipient_ids=r_ids,
        )
        mark_sent(db, "purchase_request", pr.id, kind, today_str)

    # --- Dòng PYC "Chưa đặt hàng" tồn quá 5 ngày ---
    cutoff_5d = (today - timedelta(days=5))
    pr_ids_approved = {
        pr.id for pr in db.query(PurchaseRequest)
        .filter(PurchaseRequest.status == "approved", PurchaseRequest.updated_at < cutoff_5d)
        .all()
    }
    stale_lines = (
        db.query(PurchaseRequestItem)
        .filter(
            PurchaseRequestItem.pr_id.in_(pr_ids_approved),
            PurchaseRequestItem.line_status == "Chưa đặt hàng",
        )
        .all()
    )
    for line in stale_lines:
        kind = "sla_pr_line_unordered"
        if already_sent(db, "purchase_request_item", line.id, kind, today_str):
            continue
        # Tìm user từ mã NV assignee
        assignee_users = _users_by_employee_code(db, line.assignee) if line.assignee else []
        fallback = get_users_by_role_codes(db, ["pur_manager"])
        r_ids = list({u.id for u in assignee_users + fallback})
        if not r_ids:
            continue
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == line.pr_id).first()
        trigger_notification(
            db=db, event=kind, doc_type="purchase_request",
            doc_code=pr.code if pr else str(line.pr_id),
            creator_id=pr.created_by if pr else 0,
            background_tasks=None,
            link=f"/purchase-requests/{line.pr_id}",
            recipient_ids=r_ids,
        )
        mark_sent(db, "purchase_request_item", line.id, kind, today_str)
```

### 3.6 Code phác thảo — B2: Ngày cần hàng

```python
def scan_need_date_alerts(db: Session, today: date, today_str: str):
    warn_date = (today + timedelta(days=3)).strftime("%Y-%m-%d")

    # --- PYC đã duyệt sắp/quá need_date ---
    prs = (
        db.query(PurchaseRequest)
        .filter(
            PurchaseRequest.status == "approved",
            PurchaseRequest.need_date != "",
            PurchaseRequest.is_deleted == False,
        )
        .all()
    )
    for pr in prs:
        if not pr.need_date:
            continue
        if pr.need_date < today_str:
            kind = "need_date_overdue_pr"
        elif pr.need_date <= warn_date:
            kind = "need_date_soon_pr"
        else:
            continue
        if already_sent(db, "purchase_request", pr.id, kind, today_str):
            continue
        assignee_users = (
            db.query(User).filter(User.id == pr.assignee_id, User.is_active == True).all()
            if pr.assignee_id else []
        )
        mgr_users = get_users_by_role_codes(db, ["pur_manager"])
        r_ids = list({u.id for u in assignee_users + mgr_users})
        trigger_notification(
            db=db, event=kind, doc_type="purchase_request",
            doc_code=pr.code, creator_id=pr.created_by,
            background_tasks=None,
            link=f"/purchase-requests/{pr.id}",
            recipient_ids=r_ids,
        )
        mark_sent(db, "purchase_request", pr.id, kind, today_str)

    # --- Dòng POItem sắp/quá required_date chưa nhận đủ ---
    po_items = (
        db.query(POItem)
        .filter(
            POItem.required_date != "",
            POItem.qty_received < POItem.qty_order,
        )
        .all()
    )
    po_cache: dict[int, PurchaseOrder] = {}
    for item in po_items:
        if not item.required_date:
            continue
        if item.required_date < today_str:
            kind = "need_date_overdue_poi"
        elif item.required_date <= warn_date:
            kind = "need_date_soon_poi"
        else:
            continue
        if already_sent(db, "po_item", item.id, kind, today_str):
            continue
        po = po_cache.get(item.po_id) or db.query(PurchaseOrder).filter(PurchaseOrder.id == item.po_id).first()
        if po:
            po_cache[item.po_id] = po
        if po and po.status in ("received", "cancelled"):
            continue
        creator = db.query(User).filter(User.id == (po.created_by if po else 0), User.is_active == True).first()
        mgr_users = get_users_by_role_codes(db, ["pur_manager"])
        r_ids = list({u.id for u in ([creator] if creator else []) + mgr_users})
        trigger_notification(
            db=db, event=kind, doc_type="purchase_order",
            doc_code=po.code if po else str(item.po_id),
            creator_id=po.created_by if po else 0,
            background_tasks=None,
            link=f"/purchase-orders/{item.po_id}",
            recipient_ids=r_ids,
        )
        mark_sent(db, "po_item", item.id, kind, today_str)
```

### 3.7 Code phác thảo — B3: Thanh toán chưa ghi nhận

```python
def scan_payment_alerts(db: Session, today: date, today_str: str):
    cutoff_3d = today - timedelta(days=3)
    approved_prs = (
        db.query(PaymentRequest)
        .filter(
            PaymentRequest.status == "approved",
            PaymentRequest.updated_at < cutoff_3d,
        )
        .all()
    )
    recipients = get_users_by_role_codes(db, ["pur_manager", "accountant"])
    r_ids = [u.id for u in recipients]

    for pr in approved_prs:
        kind = "payment_approved_not_paid"
        if already_sent(db, "payment_request", pr.id, kind, today_str):
            continue
        if not r_ids:
            continue
        trigger_notification(
            db=db, event=kind, doc_type="payment_request",
            doc_code=pr.code, creator_id=pr.created_by,
            background_tasks=None,
            link=f"/payment-requests/{pr.id}",
            recipient_ids=r_ids,
        )
        mark_sent(db, "payment_request", pr.id, kind, today_str)
```

### 3.8 Hàm tiện ích nội bộ

```python
# --- Idempotent helpers (xem mục 5 cho model AlertSent) ---
from app.modules.alert_sent.model import AlertSent  # model mới — xem mục 5

def already_sent(db: Session, entity: str, entity_id: int, kind: str, sent_date: str) -> bool:
    return db.query(AlertSent).filter_by(
        entity=entity, entity_id=entity_id, kind=kind, sent_date=sent_date
    ).first() is not None

def mark_sent(db: Session, entity: str, entity_id: int, kind: str, sent_date: str):
    db.add(AlertSent(entity=entity, entity_id=entity_id, kind=kind, sent_date=sent_date))
    # db.commit() gọi 1 lần ở cuối scan_alerts() để tối ưu


# --- Tra user từ mã NV (dùng cho assignee là employee code) ---
def _users_by_employee_code(db: Session, employee_code: str) -> list[User]:
    from app.modules.employee.model import Employee
    emp = db.query(Employee).filter(Employee.code == employee_code).first()
    if not emp:
        return []
    return db.query(User).filter(User.employee_id == emp.id, User.is_active == True).all()
```

---

## 4. Cấu hình

### 4.1 Lịch cron (beat_schedule trong `backend/app/core/celery_app.py`)

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    "scan-alerts-daily": {
        "task": "alert.scan_alerts",
        "schedule": crontab(hour=8, minute=0),  # 8:00 sáng — Asia/Ho_Chi_Minh
    },
}
app.conf.timezone = "Asia/Ho_Chi_Minh"
```

> **Không để UTC**: beat đọc timezone từ `celery_app.py` — phải đặt `timezone = "Asia/Ho_Chi_Minh"` để 8h là 8h sáng Hà Nội, không phải 15h.

### 4.2 ENV cần thiết trong worker

Worker dùng **cùng `.env`** với api container. Các biến cần có:
- `DATABASE_URL` — kết nối MariaDB
- `VAPID_PRIVATE_KEY` + `VAPID_PUBLIC_KEY` — web push
- `REDIS_URL` — broker/backend Celery
- `SMTP_*`, `EMAIL_ENABLED` — nếu dùng email (không bắt buộc cho phase này)

### 4.3 Docker (thêm sau khi hoàn thành Phase 0)

```yaml
# docker-compose.yml (dev) — thêm 2 service
celery-worker:
  build:
    context: ./backend
    dockerfile: ../docker/Dockerfile.api
  command: celery -A app.core.celery_app worker --loglevel=info -c 2
  env_file: .env
  depends_on: [db, redis]

celery-beat:
  build:
    context: ./backend
    dockerfile: ../docker/Dockerfile.api
  command: celery -A app.core.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  env_file: .env
  depends_on: [db, redis, celery-worker]
```

> Prod: cùng image `docker/Dockerfile.api`, khác `command`; phải cùng mạng Docker để tới `dego-erp-db-1` và Redis.

---

## 5. Chống trùng / Idempotent

### 5.1 Phương án đề xuất: bảng `tab_alert_sent` (bền vững hơn Redis khi restart)

**Model** (tạo `backend/app/modules/alert_sent/model.py`):

```python
# backend/app/modules/alert_sent/model.py
from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.base_model import Base, AuditMixin

class AlertSent(Base, AuditMixin):
    """Đánh dấu đã gửi cảnh báo — chống trùng khi job chạy lại trong ngày."""
    __tablename__ = "tab_alert_sent"
    __table_args__ = (
        UniqueConstraint("entity", "entity_id", "kind", "sent_date", name="uq_alert_sent"),
    )
    entity: Mapped[str] = mapped_column(String(40))        # "payable", "purchase_request", ...
    entity_id: Mapped[int] = mapped_column(BigInteger)     # PK của đối tượng
    kind: Mapped[str] = mapped_column(String(60))          # "payable_overdue", "sla_pr_pending", ...
    sent_date: Mapped[str] = mapped_column(String(10))     # "YYYY-MM-DD"
```

Danh sách `kind` dùng trong phase này:

| kind | Loại cảnh báo |
|---|---|
| `delivery_overdue` | Giao trễ |
| `delivery_due_soon` | Sắp tới hạn giao |
| `payable_overdue` | Công nợ quá hạn |
| `payable_due_soon` | Công nợ sắp đến hạn |
| `contract_expired` | Hợp đồng hết hạn |
| `contract_expiring` | HĐ sắp hết hạn |
| `sla_pr_pending` | PYC chờ duyệt quá 2 ngày |
| `sla_sr_pending` | YCKS chờ duyệt quá 2 ngày |
| `sla_sr_processing` | YCKS đang xử lý quá 5 ngày |
| `sla_payr_pending` | YCTT chờ duyệt quá 2 ngày |
| `sla_pr_line_unordered` | Dòng PYC "Chưa đặt hàng" quá 5 ngày |
| `sla_po_line_unordered` | Dòng PO "Chưa đặt hàng" quá 5 ngày |
| `need_date_soon_pr` | PYC sắp tới need_date |
| `need_date_overdue_pr` | PYC quá need_date |
| `need_date_soon_poi` | Dòng PO sắp tới required_date |
| `need_date_overdue_poi` | Dòng PO quá required_date |
| `payment_approved_not_paid` | YCTT approved chưa paid |

**Migration**: sau khi tạo model, thêm import vào `app/core/all_models.py` rồi:
```bash
docker compose exec api alembic revision --autogenerate -m "add_tab_alert_sent"
docker compose exec api alembic upgrade head
```

### 5.2 Phương án thay thế: Redis key (không cần migration)

```python
import redis, os
_redis = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

def already_sent_redis(entity, entity_id, kind, sent_date) -> bool:
    key = f"alert:{entity}:{entity_id}:{kind}:{sent_date}"
    return _redis.exists(key) > 0

def mark_sent_redis(entity, entity_id, kind, sent_date):
    key = f"alert:{entity}:{entity_id}:{kind}:{sent_date}"
    _redis.set(key, "1", ex=90000)  # TTL 25h — hơn 1 ngày để an toàn
```

> Nhược điểm: mất dữ liệu nếu Redis flush/restart; không có lịch sử để debug. Dùng bảng DB để có thể truy vấn "đã báo gì hôm qua".

### 5.3 Xử lý race condition

Nếu chạy nhiều worker instance (scale-out), `INSERT ... ON DUPLICATE KEY IGNORE` (MariaDB) tự nhiên loại trùng nhờ `UniqueConstraint`. SQLAlchemy sẽ raise `IntegrityError` khi insert trùng — bắt exception và bỏ qua:

```python
from sqlalchemy.exc import IntegrityError

def mark_sent_safe(db: Session, entity, entity_id, kind, sent_date):
    try:
        db.add(AlertSent(entity=entity, entity_id=entity_id, kind=kind, sent_date=sent_date))
        db.flush()   # flush từng record, không commit toàn bộ
    except IntegrityError:
        db.rollback()  # bản ghi đã tồn tại — bỏ qua
```

---

## 6. Kiểm thử & tiêu chí hoàn thành

### 6.1 Unit test (SQLite in-memory, thêm vào `test/backend/`)

**File**: `test/backend/test_alert_tasks.py`

- [ ] `test_payable_overdue_sends_notification`: tạo `Payable` có `due_date = today-1`, status `"Chờ TT"` → gọi `scan_payable_alerts()` → kiểm tra 1 `Notification` được tạo
- [ ] `test_payable_no_duplicate`: gọi 2 lần cùng ngày → chỉ 1 `Notification`
- [ ] `test_payable_paid_skipped`: `status = "Đã TT"` → không có `Notification`
- [ ] `test_sla_pr_pending_notifies_dept_head`: PYC submitted + `updated_at = today-3` → `Notification` tới trưởng phòng
- [ ] `test_need_date_overdue_pr`: PYC approved + `need_date = today-1` → `Notification` tới `assignee_id`
- [ ] `test_payment_approved_not_paid`: YCTT approved + `updated_at = today-4` → `Notification` tới QL TM
- [ ] `test_already_sent_skips`: record `AlertSent` tồn tại → `already_sent()` trả `True`, không tạo thêm `Notification`

### 6.2 Smoke test thủ công

```bash
# Gọi task thủ công từ shell worker (không cần chờ beat)
docker compose exec celery-worker celery -A app.core.celery_app call alert.scan_alerts
# Hoặc từ Python shell trong api container:
docker compose exec api python -c "
from app.tasks.alert_tasks import scan_alerts
scan_alerts.delay()  # nếu worker đang chạy
# hoặc gọi trực tiếp không qua broker:
from datetime import date
from app.core.database import SessionLocal
from app.tasks.alert_tasks import scan_delivery_alerts
db = SessionLocal()
scan_delivery_alerts(db, date.today(), date.today().strftime('%Y-%m-%d'))
db.commit(); db.close()
print('OK')
"
```

### 6.3 Tiêu chí hoàn thành

- [ ] Task `scan_alerts` đăng ký thành công trong `beat_schedule`, thấy log chạy đúng 8h VN
- [ ] Sau khi chạy: `Notification` được tạo cho các đối tượng đủ điều kiện, **không trùng** khi chạy lại
- [ ] Web push đẩy được tới thiết bị đang đăng ký (kiểm tra bằng demo account)
- [ ] Bảng `tab_alert_sent` ghi đủ bản ghi sau mỗi lần chạy
- [ ] Không có exception chưa xử lý trong log worker
- [ ] Unit test toàn bộ pass: `docker compose exec -T api python -m pytest test/backend/test_alert_tasks.py -q`

---

## 7. Rủi ro & lưu ý

### 7.1 Cột kiểu String ngày (không phải Date)

Tất cả cột ngày trong dự án (`due_date`, `need_date`, `required_date`, `end_date`) đều là `String(10)` format `YYYY-MM-DD`. So sánh string `<`/`>` hoạt động đúng với format này — **không cần** chuyển sang `datetime.date`. Chú ý xử lý chuỗi rỗng `""` (kiểm tra `if not field:` trước khi so sánh).

### 7.2 Spam người nhận

- Công nợ quá hạn nhiều khoản → nhiều `Notification` riêng lẻ trong 1 ngày cho cùng 1 người nhận. Ở quy mô nhỏ (~20–100 user) chấp nhận được. Nếu phiền: gộp cùng loại thành 1 thông báo tổng hợp (digest) — để Phase 4.
- SLA: ngưỡng X ngày (2/5 ngày) nên cho phép cấu hình qua `setting` hoặc hằng số đặt đầu file thay vì hardcode.

### 7.3 Người nhận không tồn tại hoặc chưa gán

- Trưởng phòng chưa gán (`Department.manager_id` null): `get_department_head_users()` trả `[]` → không báo ai. Cần đảm bảo gán trưởng phòng trước khi bật phase này.
- `PurchaseRequestItem.assignee` là **mã NV** (string), không phải `user_id`. Cần hàm `_users_by_employee_code()` tra ngược qua `Employee.code → User.employee_id`. Nếu chưa có Employee trong hệ thống → fallback sang QL TM.
- Role code `"accountant"` có thể chưa tồn tại trong `tab_role`. `get_users_by_role_codes()` trả `[]` khi không tìm thấy — không crash, chỉ không báo ai. Cần tạo role hoặc dùng đúng `code` đang dùng.

### 7.4 Hiệu năng

- Không join phức tạp — mỗi hàm quét load full bảng rồi lọc Python. Với dữ liệu ~vài nghìn PO/PYC/dòng chấp nhận được.
- Nếu dữ liệu lớn hơn: thêm index trên `status` + `updated_at`/`due_date` trước (đã có index `status` ở hầu hết bảng).
- Gom `db.flush()` từng bản ghi `AlertSent` trong vòng lặp, `db.commit()` 1 lần cuối `scan_alerts()` để giảm round-trip.

### 7.5 Thứ tự làm

1. Tạo bảng `tab_alert_sent` (migration) + import vào `all_models.py`
2. Viết + test hàm `already_sent` / `mark_sent`
3. Viết từng hàm quét, test độc lập
4. Ghép vào `scan_alerts` task
5. Đăng ký `beat_schedule` sau khi Phase 0 xong
6. Smoke test trên VPS

### 7.6 Thông báo cho người dùng về loại cảnh báo mới

`trigger_notification` xử lý `event` qua `if/elif` — các `kind` mới (`sla_pr_pending`, `need_date_overdue_pr`…) sẽ rơi vào `else` fallback với `subject/body` tự sinh từ `DOC_LABEL + STATUS_VERB`. Cần thêm case hoặc đảm bảo fallback đủ rõ nghĩa trước khi deploy.
