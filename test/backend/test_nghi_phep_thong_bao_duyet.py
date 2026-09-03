"""CR-260 — THÔNG BÁO cho người duyệt khi gửi duyệt đơn nghỉ phép.

Đường báo việc là thứ duy nhất nối «có người vừa nộp đơn» với «có người phải
ký». Nó gãy thì không ai ăn lỗi, không có gì đỏ lên: tờ đơn nằm im trong hàng
đợi cho tới khi người xin nghỉ sốt ruột đi hỏi bằng miệng — đúng cuộc gọi mà cả
phân hệ này sinh ra để chặn.

Hai lỗi tệp này chốt, cả hai đều đã có thật ở nhánh `erp-v2` trước 03/09/2026:

1. **`ENTITY_LABELS` thiếu `leave_request`** → thư mở đầu bằng *"Phiếu NP009
   đang chờ bạn"*. Người duyệt của một hệ có bảy loại chứng từ đọc "Phiếu" thì
   không biết mình sắp mở cái gì.
2. **`ENTITY_LINKS` thiếu `leave_request`** → `link` là chuỗi RỖNG, và thư vẫn
   gửi bình thường. Bấm vào **không đi đâu cả**; người duyệt phải tự mò vào menu
   tìm tờ đơn. Đúng lỗi mà phân hệ Văn thư đã phải vá ngày 20/08/2026, chỉ khác
   chỗ hỏng — xem `frontend-v2/src/shared/notifications/notification-link.ts`.

⚠️ `notify_new_tasks` **nuốt mọi lỗi có chủ ý** (mất phiếu vì không gửi được thư
thì tệ hơn thiếu một cái thư). Nghĩa là mọi hỏng hóc ở đây đều IM LẶNG, và bài
kiểm là thứ duy nhất phát hiện ra.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.task_notification import ENTITY_LABELS, ENTITY_LINKS
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.schema import LeaveRequestCreate
from app.modules.notification.model import Notification
from app.modules.user.model import User

ACTOR = 1
ENTITY = "leave_request"
MONDAY = date(2026, 1, 5)


@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


def _employee_with_account(db, code, name):
    """Người duyệt phải có TÀI KHOẢN — thư gửi cho `user_id`, không phải nhân sự.

    Nhân sự không có tài khoản thì `_accounts` trả rỗng và không thư nào được
    ghi; đó là hành vi đúng, nhưng nó cũng làm mọi bài kiểm ở đây xanh giả nếu
    quên dựng tài khoản.
    """
    employee = Employee(code=code, full_name=name, company_id=1,
                        department_id=7, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{code.lower()}@demo.com", password_hash="x",
                employee_id=employee.id, is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def submitter(db):
    employee, _ = _employee_with_account(db, "NOP", "Người nộp")
    return employee


@pytest.fixture()
def approver1(db):
    return _employee_with_account(db, "DUYET1", "Trưởng bộ phận")


@pytest.fixture()
def approver2(db):
    return _employee_with_account(db, "DUYET2", "Giám đốc")


@pytest.fixture()
def flow_2_buoc(db, approver1, approver2):
    row = ApprovalFlow(entity=ENTITY, code="NP-2B", name="Duyệt đơn nghỉ phép",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    for seq, (employee, _) in enumerate((approver1, approver2), start=1):
        db.add(ApprovalNode(flow_id=row.id, seq=seq,
                            name="Trưởng bộ phận duyệt" if seq == 1 else "Giám đốc duyệt",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(employee.id),
                            created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    db.refresh(row)
    return row


def _user(employee, uid=1):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _submit(db, leave_type, employee, start=MONDAY):
    user = _user(employee)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id, from_date=start,
        to_date=start + timedelta(days=1), reason="Về quê"), user)
    emp, lt = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    return request_service.mark_submitted(db, obj, emp, lt, user, instance_id)


def _inbox(db, user: User) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.id.asc())
        .all()
    )


def _instance(db, obj):
    return instance_service.running_instance(db, ENTITY, obj.id)


# ══════════════════════════════════════════════════════════════════════════════
#  1. Gửi duyệt → người duyệt chặng 1 nhận thư
# ══════════════════════════════════════════════════════════════════════════════

def test_gui_duyet_thi_nguoi_duyet_chang_1_nhan_thu(db, flow_2_buoc, leave_type,
                                                    submitter, approver1):
    _, account = approver1
    assert _inbox(db, account) == []

    obj = _submit(db, leave_type, submitter)
    thu = _inbox(db, account)

    assert len(thu) == 1, "Gửi duyệt xong mà người duyệt không nhận được thư nào"
    assert obj.code in thu[0].title
    assert thu[0].is_read is False


def test_thu_goi_DUNG_TEN_loai_chung_tu_chu_khong_phai_Phieu(db, flow_2_buoc, leave_type,
                                                             submitter, approver1):
    """Lỗi thật trước 03/09/2026: `ENTITY_LABELS` thiếu `leave_request`.

    Người duyệt của một hệ có bảy loại chứng từ mà đọc "Phiếu NP009" thì không
    biết mình sắp mở cái gì — mà họ quyết định có bấm vào hay không dựa đúng
    trên câu đó.
    """
    assert ENTITY_LABELS.get(ENTITY) == "Đơn nghỉ phép"

    _, account = approver1
    obj = _submit(db, leave_type, submitter)
    body = _inbox(db, account)[0].body

    assert body.startswith(f"Đơn nghỉ phép {obj.code}")
    assert "Phiếu" not in body


def test_thu_co_LINK_mo_dung_to_don(db, flow_2_buoc, leave_type, submitter, approver1):
    """Lỗi thật trước 03/09/2026: `ENTITY_LINKS` thiếu `leave_request`.

    `.get(...)` trả chuỗi rỗng nên thư VẪN GỬI, chỉ là bấm vào không đi đâu.
    Không có bài kiểm thì chuyện đó không bao giờ đỏ lên ở đâu cả.

    ⚠️ Tiền tố `/hr` phải nằm trong `V2_PREFIXES` của
    `frontend-v2/src/shared/notifications/notification-link.ts`, nếu không giao
    diện trả `null` và lại về đúng chỗ hỏng cũ.
    """
    assert ENTITY_LINKS.get(ENTITY) == "/hr/leave-requests/{id}"

    _, account = approver1
    obj = _submit(db, leave_type, submitter)

    assert _inbox(db, account)[0].link == f"/hr/leave-requests/{obj.id}"


def test_thu_noi_ro_DANG_CHO_O_CHANG_nao(db, flow_2_buoc, leave_type,
                                         submitter, approver1):
    """Một người có thể đứng ở nhiều chặng của nhiều luồng — thiếu tên chặng thì
    họ không biết mình đang được hỏi với tư cách gì."""
    _, account = approver1
    _submit(db, leave_type, submitter)

    assert "Trưởng bộ phận duyệt" in _inbox(db, account)[0].body


# ══════════════════════════════════════════════════════════════════════════════
#  2. Thư đi đúng người, đúng lúc — không sớm, không thừa
# ══════════════════════════════════════════════════════════════════════════════

def test_nguoi_chang_2_CHUA_nhan_thu_luc_moi_gui_duyet(db, flow_2_buoc, leave_type,
                                                       submitter, approver2):
    """Báo cả hàng thì hai người cùng lao vào một phiếu, mà một người bấm chưa
    tới lượt và ăn lỗi."""
    _, account = approver2
    _submit(db, leave_type, submitter)

    assert _inbox(db, account) == []


def test_ky_xong_chang_1_thi_chang_2_moi_nhan_thu(db, flow_2_buoc, leave_type,
                                                  submitter, approver1, approver2):
    """Đây là mắt xích dễ đứt nhất của luồng nhiều bước: chặng 1 ký xong mà
    chặng 2 không nhận thư thì phiếu nằm im vô thời hạn."""
    employee1, _ = approver1
    _, account2 = approver2

    obj = _submit(db, leave_type, submitter)
    assert _inbox(db, account2) == []

    action_service.approve(db, _instance(db, obj), employee1.id, ACTOR, {})
    thu = _inbox(db, account2)

    assert len(thu) == 1
    assert "Giám đốc duyệt" in thu[0].body
    assert thu[0].link == f"/hr/leave-requests/{obj.id}"


def test_NGUOI_NOP_khong_tu_nhan_thu_duyet_don_cua_chinh_minh(db, flow_2_buoc,
                                                              leave_type, submitter):
    """Người nộp có tài khoản, nhưng họ không đứng ở chặng nào — thư chỉ đi tới
    người ĐƯỢC GIAO việc."""
    account = db.query(User).filter(User.employee_id == submitter.id).one()
    _submit(db, leave_type, submitter)

    assert _inbox(db, account) == []


def test_nop_hai_don_thi_nhan_hai_thu_rieng(db, flow_2_buoc, leave_type,
                                            submitter, approver1):
    """Gộp thư là người duyệt đọc một dòng rồi tưởng chỉ có một việc."""
    _, account = approver1
    don1 = _submit(db, leave_type, submitter)
    don2 = _submit(db, leave_type, submitter, start=MONDAY + timedelta(days=14))

    links = [row.link for row in _inbox(db, account)]
    assert links == [f"/hr/leave-requests/{don1.id}", f"/hr/leave-requests/{don2.id}"]


def test_rut_roi_gui_lai_thi_nhan_them_thu_MOI(db, flow_2_buoc, leave_type,
                                               submitter, approver1):
    """Rút đơn rồi nộp lại là một phiên MỚI. Không báo lại thì người duyệt đã
    đọc thư cũ (và đánh dấu đã đọc) sẽ không bao giờ biết đơn quay lại."""
    _, account = approver1
    obj = _submit(db, leave_type, submitter)
    action_service.withdraw(db, _instance(db, obj), submitter.id, ACTOR, "Đổi ý")
    db.refresh(obj)

    assert len(_inbox(db, account)) == 1
    _submit(db, leave_type, submitter)
    assert len(_inbox(db, account)) == 2


def test_tai_khoan_TAT_thi_khong_gui_thu(db, flow_2_buoc, leave_type,
                                         submitter, approver1):
    """Người nghỉ việc vẫn còn hồ sơ nhân sự và vẫn còn tên trong luồng cũ. Gửi
    thư cho họ là thư rơi vào hộp không ai mở, và phiếu vẫn nằm im."""
    employee, account = approver1
    account.is_active = False
    db.commit()

    _submit(db, leave_type, submitter)
    assert _inbox(db, account) == []


# ══════════════════════════════════════════════════════════════════════════════
#  3. Thư KHÔNG được làm hỏng việc gửi duyệt
# ══════════════════════════════════════════════════════════════════════════════

def test_nguoi_duyet_KHONG_co_tai_khoan_van_gui_duyet_duoc(db, leave_type, submitter):
    """Không gửi được thư thì thôi, tuyệt đối không được kéo cả phiếu chết theo.

    Đây là lý do `notify_new_tasks` nuốt lỗi. Bỏ chốt đó thì một hồ sơ nhân sự
    thiếu tài khoản làm hỏng nút «Gửi duyệt» của cả công ty.
    """
    khong_tai_khoan = Employee(code="NO_ACC", full_name="Không tài khoản",
                               company_id=1, department_id=7, is_active=True)
    db.add(khong_tai_khoan)
    db.flush()

    row = ApprovalFlow(entity=ENTITY, code="NP-1B", name="Duyệt đơn nghỉ phép",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Duyệt",
                        approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(khong_tai_khoan.id),
                        created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    obj = _submit(db, leave_type, submitter)

    assert obj.approval_instance_id > 0
    assert _instance(db, obj) is not None
