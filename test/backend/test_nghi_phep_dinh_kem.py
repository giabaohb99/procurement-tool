"""bao-CR-505 — ĐÍNH KÈM của đơn nghỉ phép (ảnh giấy khám bệnh, PDF…).

Tệp đi qua cửa đính kèm dùng chung `/api/attachments` với `entity="leave_request"`.
Bốn điều tệp này chốt, cả bốn đều hỏng IM LẶNG nếu ai đó sửa nhầm:

1. **Riêng tư.** Giấy khám bệnh là dữ liệu sức khỏe — API không được trả URL đọc
   thẳng kho lưu trữ (`PRIVATE_ENTITIES`).
2. **Phạm vi của tờ đơn.** Người ngoài phạm vi không đọc, không gắn được tệp,
   dù có đủ quyền vai trò `leave_request.read`.
3. **Người ĐANG phải ký đọc được.** Đúng ngoại lệ CR-260 của màn chi tiết đơn:
   Trưởng phòng Nhân sự duyệt chặng 2 thường nằm ngoài phạm vi dữ liệu. Không có
   nhánh `_ensure_leave_request` thì họ mở được tờ đơn nghỉ ốm mà ảnh giấy khám
   bệnh lại 403. Ký xong là quyền đó đóng lại, và người ký KHÔNG gắn/gỡ được tệp.
4. **Khóa theo tờ đơn.** Gửi duyệt rồi thì không thêm/gỡ tệp — bộ tệp là một phần
   hồ sơ người duyệt đang đọc.

Gọi thẳng hàm controller (khuôn `test_pham_vi_dinh_kem_b08.py`) với vai trò THẬT
cấp qua `cap_quyen`, để lớp vai trò lẫn lớp phạm vi đều chạy đúng như lúc chạy thật.
"""
import json
from datetime import date, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.core import attachment_scope as asc
from app.core.file_registry import FILE_POLICY, is_private
from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.request_model import LeaveRequest
from app.modules.leave.schema import LeaveRequestCreate

ENTITY = "leave_request"
ACTOR = 1
MONDAY = date(2026, 1, 5)
PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"

REQUESTER_UID, APPROVER1_UID, APPROVER2_UID, OUTSIDER_UID = 1, 9, 10, 11


def _employee(db, code, dept=7):
    obj = Employee(code=code, full_name=f"NV {code}", company_id=1,
                   department_id=dept, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def world(db, cap_quyen):
    """Người nộp + hai người duyệt (hai chặng) + một người ngoài cuộc.

    Cả bốn đều có quyền VAI TRÒ trên `leave_request` với phạm vi `own` — đúng cấu
    hình của nhân viên thường. Người duyệt chặng 2 ở phòng khác, tức phạm vi dữ
    liệu của họ không bao giờ với tới tờ đơn.
    """
    leave_type = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                           annual_quota_days=12.0)
    db.add(leave_type)
    submitter = _employee(db, "NOP")
    approver1 = _employee(db, "DUYET1")
    approver2 = _employee(db, "DUYET2", dept=9)
    outsider = _employee(db, "NGOAI", dept=9)

    flow = ApprovalFlow(entity=ENTITY, code="NP-2B", name="Duyệt nghỉ phép",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    for seq, emp in enumerate((approver1, approver2), start=1):
        db.add(ApprovalNode(flow_id=flow.id, seq=seq, name=f"Chặng {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(emp.id),
                            created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    for uid in (REQUESTER_UID, APPROVER1_UID, APPROVER2_UID, OUTSIDER_UID):
        cap_quyen(uid, ENTITY, scope="own", read=True, create=True, write=True)
    db.commit()

    return SimpleNamespace(
        db=db, leave_type=leave_type,
        requester=SimpleNamespace(id=REQUESTER_UID, employee_id=submitter.id),
        approver1=SimpleNamespace(id=APPROVER1_UID, employee_id=approver1.id),
        approver2=SimpleNamespace(id=APPROVER2_UID, employee_id=approver2.id),
        outsider=SimpleNamespace(id=OUTSIDER_UID, employee_id=outsider.id),
        approver1_emp=approver1,
    )


def _draft(w) -> LeaveRequest:
    return request_service.create(w.db, LeaveRequestCreate(
        leave_type_id=w.leave_type.id, from_date=MONDAY,
        to_date=MONDAY + timedelta(days=1), reason="Nghỉ ốm"), w.requester)


def _submit(w, obj: LeaveRequest) -> LeaveRequest:
    emp = request_service.prepare_submit(w.db, obj, w.requester)
    instance_id = approval_bridge.start_approval(w.db, obj, w.requester)
    return request_service.mark_submitted(w.db, obj, emp, w.requester, instance_id)


def _upload_pdf(w, obj: LeaveRequest, user) -> dict:
    """Đi đúng cửa `POST /api/attachments` — chỉ thay kho lưu trữ bằng hàm giả."""
    files = [UploadFile(file=BytesIO(PDF_BYTES), filename="giay-kham-benh.pdf")]
    res = ac.upload(entity=ENTITY, entity_id=obj.id, purchase_order_id=0, doc_type="",
                    files=files, db=w.db, user=user)
    return res.body


@pytest.fixture(autouse=True)
def _fake_storage(monkeypatch):
    monkeypatch.setattr(ac, "upload_fileobj", lambda f, key, ct: f"https://bucket/{key}")
    monkeypatch.setattr(ac, "read_file_bytes", lambda f: PDF_BYTES)


def _link_of(w, obj) -> FileLink:
    return (w.db.query(FileLink)
            .filter(FileLink.entity == ENTITY, FileLink.entity_id == obj.id).one())


def _status(fn, *args) -> int:
    with pytest.raises(HTTPException) as e:
        fn(*args)
    return e.value.status_code


# ══════════════════════════════════════════════════════════════════════════════
#  1. Khai chính sách
# ══════════════════════════════════════════════════════════════════════════════

def test_policy_declared_with_images_pdf_office_and_parent_leave_request():
    parent, exts, max_mb = FILE_POLICY[ENTITY]
    assert parent == ENTITY, "quyền phải kiểm trên chính tờ đơn"
    assert {"jpg", "jpeg", "png", "webp", "pdf", "docx", "xlsx"} <= exts
    assert "svg" not in exts
    assert max_mb == 50


def test_leave_attachments_are_private():
    """Giấy khám bệnh là dữ liệu sức khỏe — không phát URL đọc thẳng bucket."""
    assert is_private(ENTITY)


def test_parent_lookup_returns_the_leave_request(world):
    obj = _draft(world)
    model, ids = asc.parent_records(world.db, ENTITY, obj.id)
    assert model is LeaveRequest
    assert ids == [obj.id]


# ══════════════════════════════════════════════════════════════════════════════
#  2. Người nộp: gắn + đọc tệp của đơn mình
# ══════════════════════════════════════════════════════════════════════════════

def test_requester_uploads_and_lists_without_public_url(world):
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)

    rows = ac.list_attachments(entity=ENTITY, entity_id=obj.id, db=world.db,
                               user=world.requester).body
    data = json.loads(rows)["data"]
    assert [r["filename"] for r in data] == ["giay-kham-benh.pdf"]
    #  ⚠️ Rỗng CẢ HAI: `url` lẫn `thumb_url` đều là đường đọc thẳng kho.
    assert data[0]["url"] == ""
    assert data[0]["thumb_url"] == ""

    link = _link_of(world, obj)
    assert ac.view_one(link.id, world.db, world.requester).body == PDF_BYTES


# ══════════════════════════════════════════════════════════════════════════════
#  3. Người ngoài cuộc: có quyền vai trò nhưng ngoài phạm vi
# ══════════════════════════════════════════════════════════════════════════════

def test_outsider_cannot_read_or_attach(world):
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)
    link = _link_of(world, obj)

    assert _status(ac._check, world.db, world.outsider, ENTITY, "read", obj.id) == 403
    assert _status(ac.download_one, link.id, world.db, world.outsider) == 403
    assert _status(ac.view_one, link.id, world.db, world.outsider) == 403
    assert _status(_upload_pdf, world, obj, world.outsider) == 403
    assert _status(ac.remove, link.id, world.db, world.outsider) == 403


def test_user_without_role_permission_is_blocked_first(world):
    """Lớp vai trò vẫn còn nguyên: không có `leave_request.read` là 403 ngay."""
    obj = _draft(world)
    stranger = SimpleNamespace(id=777, employee_id=0)
    assert _status(ac._check, world.db, stranger, ENTITY, "read", obj.id) == 403


def test_deleted_request_is_404(world):
    obj = _draft(world)
    obj.is_deleted = True
    world.db.commit()
    assert _status(ac._check, world.db, world.requester, ENTITY, "read", obj.id) == 404


def test_unknown_request_id_is_404(world):
    assert _status(ac._check, world.db, world.requester, ENTITY, "read", 999999) == 404


# ══════════════════════════════════════════════════════════════════════════════
#  4. Người đang phải ký: đọc được, không gắn/gỡ được, ký xong thì đóng
# ══════════════════════════════════════════════════════════════════════════════

def test_pending_approver_reads_attachment_outside_scope(world):
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)
    _submit(world, obj)
    link = _link_of(world, obj)

    #  Phạm vi `own` không với tới đơn người khác — chỉ việc TASK_PENDING mở cửa.
    assert ac._check(world.db, world.approver1, ENTITY, "read", obj.id)
    assert ac.view_one(link.id, world.db, world.approver1).body == PDF_BYTES
    assert ac.download_one(link.id, world.db, world.approver1).body == PDF_BYTES


def test_pending_approver_cannot_attach_or_remove(world):
    """Được giao ký không có nghĩa là được sửa hồ sơ của người khác."""
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)
    _submit(world, obj)
    link = _link_of(world, obj)

    assert _status(ac._check, world.db, world.approver1, ENTITY, "manage", obj.id) == 403
    assert _status(ac.remove, link.id, world.db, world.approver1) == 403


def test_next_stage_approver_cannot_read_before_their_turn(world):
    obj = _draft(world)
    _submit(world, obj)
    assert _status(ac._check, world.db, world.approver2, ENTITY, "read", obj.id) == 403


def test_approver_loses_access_after_signing(world):
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)
    _submit(world, obj)
    instance = instance_service.running_instance(world.db, ENTITY, obj.id)
    action_service.approve(world.db, instance, world.approver1_emp.id, ACTOR, {})

    assert _status(ac._check, world.db, world.approver1, ENTITY, "read", obj.id) == 403
    #  …và quyền đi sang người ở chặng kế.
    assert ac._check(world.db, world.approver2, ENTITY, "read", obj.id)


# ══════════════════════════════════════════════════════════════════════════════
#  5. Khóa theo trạng thái tờ đơn
# ══════════════════════════════════════════════════════════════════════════════

def test_submitted_request_locks_attachments_even_for_requester(world):
    obj = _draft(world)
    _upload_pdf(world, obj, world.requester)
    _submit(world, obj)
    link = _link_of(world, obj)

    assert _status(_upload_pdf, world, obj, world.requester) == 400
    assert _status(ac.remove, link.id, world.db, world.requester) == 400
    #  Đọc thì vẫn đọc được — khóa chỉ chặn thêm/gỡ.
    assert ac.view_one(link.id, world.db, world.requester).body == PDF_BYTES


def test_register_prepared_file_is_also_locked(world):
    """Cửa thứ hai (`/upload-file` rồi `/register`) cũng phải khóa như cửa chính."""
    obj = _draft(world)
    _submit(world, obj)
    f = StoredFile(filename="anh.pdf", file_key="k", url="u", content_type="application/pdf",
                   size=1, sha256="s", created_by=REQUESTER_UID)
    world.db.add(f)
    world.db.commit()

    data = ac.RegisterIn(entity=ENTITY, entity_id=obj.id, file_ids=[f.id])
    assert _status(ac.register_files, data, world.db, world.requester) == 400


def test_returned_request_can_attach_again(world):
    """Trả về chỉnh sửa = sửa được = gắn thêm tệp được (người duyệt hay đòi bổ sung giấy)."""
    obj = _draft(world)
    _submit(world, obj)
    instance = instance_service.running_instance(world.db, ENTITY, obj.id)
    action_service.send_back(world.db, instance, world.approver1_emp.id, ACTOR,
                             "Bổ sung giấy khám bệnh", {})
    world.db.refresh(obj)

    _upload_pdf(world, obj, world.requester)
    assert _link_of(world, obj).entity_id == obj.id
