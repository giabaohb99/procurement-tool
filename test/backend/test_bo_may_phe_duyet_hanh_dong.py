"""BỘ MÁY PHÊ DUYỆT — hành động, ủy quyền, nhiều người trong một bước.

Phần này canh những luật dễ bị viết lỏng tay vì "chắc không ai làm thế":
  · ba hành động bắt buộc nêu lý do (I09/I10/I11);
  · rút lại chỉ khi CHƯA ai duyệt — có chữ ký rồi mà rút được là chữ ký vô nghĩa;
  · ủy quyền ghi CẢ HAI danh tính, và cấm dây chuyền (I12);
  · bốn chế độ nhiều người trong một bước (I05);
  · bàn giao hàng loạt khi nghỉ việc (I23).

Sáu bài NGHIỆM THU chuyển phase nằm ở `test_bo_may_phe_duyet.py`.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.modules.approval import (action_service, delegation_service,
                                  instance_service)
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, MULTI_ALL,
                                             MULTI_ANY, MULTI_QUORUM,
                                             MULTI_SEQUENTIAL, NODE_CC,
                                             SKIP_NONE, ApprovalFlow,
                                             ApprovalNode)
from app.modules.approval.instance_model import (ACTION_APPROVE,
                                                 INSTANCE_APPROVED,
                                                 INSTANCE_REJECTED,
                                                 INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 INSTANCE_WITHDRAWN,
                                                 TASK_APPROVED, TASK_CANCELLED,
                                                 TASK_PENDING, TASK_WAITING,
                                                 ApprovalAction, ApprovalTask)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def person(db, seed):
    ids = {"nop": seed.emp_req_id}
    for name in ("a", "b", "c", "d"):
        employee = Employee(code=f"HD_{name.upper()}", full_name=f"Người {name.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[name] = employee.id
    db.commit()
    return ids


def _luong_mot_buoc(db, employee_ids, **kw) -> ApprovalFlow:
    flow = ApprovalFlow(entity=ENTITY, code=kw.pop("code", "HD-01"), name="Luồng thử",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(
        flow_id=flow.id, seq=1, name="Bước duyệt",
        approver_kind=APPROVER_EMPLOYEE,
        approver_ref=",".join(str(i) for i in employee_ids),
        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR, **kw,
    ))
    db.commit()
    db.refresh(flow)
    return flow


def _trinh(db, submitter, entity_id=301):
    return instance_service.start(db, ENTITY, entity_id, {}, submitter, ACTOR,
                                    entity_code="VB-9", entity_title="Phiếu thử")


def _dang_cho(db, instance):
    return [row for row in instance_service.tasks_of_instance(db, instance.id)
            if row.status == TASK_PENDING]


# ── Ba hành động bắt buộc nêu lý do ─────────────────────────────────────────

@pytest.mark.parametrize("hook_fn,suffix", [
    ("reject", {}),
    ("send_back", {"subject": {}}),
])
def test_tu_choi_va_tra_lai_khong_co_ly_do_thi_bi_chan(db, seed, person, hook_fn, suffix):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    with pytest.raises(HTTPException) as error:
        getattr(action_service, hook_fn)(db, instance, person["a"], ACTOR, "   ", **suffix)
    assert error.value.status_code == 400
    assert "lý do" in error.value.detail


def test_rut_lai_khong_co_ly_do_thi_bi_chan(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    with pytest.raises(HTTPException) as error:
        action_service.withdraw(db, instance, person["nop"], ACTOR, "")
    assert "lý do" in error.value.detail


# ── Từ chối · trả lại · rút lại ─────────────────────────────────────────────

def test_tu_choi_dong_phieu_va_don_sach_viec_con_treo(db, seed, person):
    """Việc còn treo mà phiếu đã chết thì phải hủy — nếu không, màn «Việc của
    tôi» hiện việc của một phiếu không làm gì được nữa, và người dùng thôi tin
    cái danh sách đó."""
    _luong_mot_buoc(db, [person["a"], person["b"]], multi_mode=MULTI_ALL)
    instance = _trinh(db, person["nop"])

    action_service.reject(db, instance, person["a"], ACTOR, "Sai số liệu")

    assert instance.status == INSTANCE_REJECTED
    assert _dang_cho(db, instance) == []


def test_tra_lai_ve_nguoi_nop_thi_phieu_con_song(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    action_service.send_back(db, instance, person["a"], ACTOR, "Bổ sung phụ lục", {})

    assert instance.status == INSTANCE_RETURNED
    assert instance.finish_reason == "Bổ sung phụ lục"


def test_tra_ve_mot_buoc_phia_truoc_thi_cac_buoc_sau_phai_duyet_lai(db, seed, person):
    """Người ký sau đã ký trên một nội dung khác với nội dung sắp sửa."""
    flow = ApprovalFlow(entity=ENTITY, code="HD-TL", name="Ba bước", is_active=True,
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    for seq, name in ((1, "a"), (2, "b"), (3, "c")):
        db.add(ApprovalNode(flow_id=flow.id, seq=seq, name=f"Bước {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(person[name]),
                            skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    instance = _trinh(db, person["nop"])
    action_service.approve(db, instance, person["a"], ACTOR, {})
    action_service.approve(db, instance, person["b"], ACTOR, {})

    action_service.send_back(db, instance, person["c"], ACTOR, "Sửa điều 3", {}, to_step=1)

    assert instance.status == INSTANCE_RUNNING
    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["a"]]
    #  Chữ ký cũ của B bị hủy — B phải ký lại sau khi nội dung đổi.
    cua_b = [row for row in instance_service.tasks_of_instance(db, instance.id)
             if row.assignee_employee_id == person["b"]]
    assert all(row.status == TASK_CANCELLED for row in cua_b)


def test_khong_tra_ve_buoc_phia_sau(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])
    with pytest.raises(HTTPException) as error:
        action_service.send_back(db, instance, person["a"], ACTOR, "x", {}, to_step=5)
    assert "phía trước" in error.value.detail


def test_rut_lai_duoc_khi_chua_ai_duyet(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    action_service.withdraw(db, instance, person["nop"], ACTOR, "Gửi nhầm")

    assert instance.status == INSTANCE_WITHDRAWN
    assert _dang_cho(db, instance) == []


def test_da_co_nguoi_duyet_thi_khong_rut_lai_duoc(db, seed, person):
    """Rút sau khi có người ký = chữ ký đó thành vô nghĩa, mà người ký không hề biết."""
    _luong_mot_buoc(db, [person["a"], person["b"]], multi_mode=MULTI_ALL)
    instance = _trinh(db, person["nop"])
    action_service.approve(db, instance, person["a"], ACTOR, {})

    with pytest.raises(HTTPException) as error:
        action_service.withdraw(db, instance, person["nop"], ACTOR, "Đổi ý")
    assert "đã có người duyệt" in error.value.detail.lower()


def test_nguoi_khac_khong_rut_phieu_ho_nguoi_nop(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])
    with pytest.raises(HTTPException) as error:
        action_service.withdraw(db, instance, person["a"], ACTOR, "x")
    assert error.value.status_code == 403


def test_khong_co_viec_dang_cho_thi_khong_bam_duoc(db, seed, person):
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])
    with pytest.raises(HTTPException) as error:
        action_service.approve(db, instance, person["c"], ACTOR, {})
    assert error.value.status_code == 403


# ── Nhiều người trong một bước (I05) ────────────────────────────────────────

def test_mot_nguoi_duyet_la_du(db, seed, person):
    _luong_mot_buoc(db, [person["a"], person["b"]], multi_mode=MULTI_ANY)
    instance = _trinh(db, person["nop"])

    action_service.approve(db, instance, person["a"], ACTOR, {})

    assert instance.status == INSTANCE_APPROVED


def test_tat_ca_phai_duyet(db, seed, person):
    _luong_mot_buoc(db, [person["a"], person["b"]], multi_mode=MULTI_ALL)
    instance = _trinh(db, person["nop"])

    action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.status == INSTANCE_RUNNING

    action_service.approve(db, instance, person["b"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


def test_lan_luot_thi_nguoi_sau_chua_thay_viec(db, seed, person):
    """Mở việc cho cả ba cùng lúc thì «lần lượt» không còn nghĩa gì."""
    _luong_mot_buoc(db, [person["a"], person["b"], person["c"]], multi_mode=MULTI_SEQUENTIAL)
    instance = _trinh(db, person["nop"])

    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["a"]]

    action_service.approve(db, instance, person["a"], ACTOR, {})
    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["b"]]


def test_du_ty_le_thi_di_tiep(db, seed, person):
    """Quorum 50% trên bốn người: hai chữ ký là đủ."""
    _luong_mot_buoc(db, [person["a"], person["b"], person["c"], person["d"]],
                    multi_mode=MULTI_QUORUM, quorum_percent=50)
    instance = _trinh(db, person["nop"])

    action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.status == INSTANCE_RUNNING

    action_service.approve(db, instance, person["b"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


def test_buoc_nhan_ban_sao_khong_chan_luong(db, seed, person):
    """I15 — người nhận bản sao chỉ được báo, không phải bấm gì."""
    flow = ApprovalFlow(entity=ENTITY, code="HD-CC", name="Có bản sao", is_active=True,
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=str(person["a"]), skip_duplicate=SKIP_NONE,
                        created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalNode(flow_id=flow.id, seq=2, name="Báo kế toán", node_kind=NODE_CC,
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(person["b"]),
                        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    instance = _trinh(db, person["nop"])
    action_service.approve(db, instance, person["a"], ACTOR, {})

    assert instance.status == INSTANCE_APPROVED
    assert _dang_cho(db, instance) == []


# ── Ủy quyền (I12) ──────────────────────────────────────────────────────────

def _uy_quyen(db, tu, den, ngay_bat_dau=None, ngay_ket_thuc=None, entity=""):
    row = Delegation(
        from_employee_id=tu, to_employee_id=den, entity=entity,
        from_date=ngay_bat_dau or date.today() - timedelta(days=1),
        to_date=ngay_ket_thuc or date.today() + timedelta(days=7),
        is_active=True, created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_duyet_thay_thi_nhat_ky_ghi_ca_hai_danh_tinh(db, seed, person):
    """Bản in phải ghi được câu «ông B duyệt thay ông A theo ủy quyền số 12».

    Ghi mỗi một người là sau này không phân biệt được ai chịu trách nhiệm — mà
    đó chính là câu kiểm toán sẽ hỏi.
    """
    delegation = _uy_quyen(db, tu=person["a"], den=person["b"])
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    action_service.approve(db, instance, person["b"], ACTOR, {}, comment="Duyệt thay")

    dau_vet = db.query(ApprovalAction).filter(
        ApprovalAction.instance_id == instance.id,
        ApprovalAction.action == ACTION_APPROVE).first()
    assert dau_vet.actor_employee_id == person["b"]
    assert dau_vet.on_behalf_of_id == person["a"]
    assert dau_vet.delegation_id == delegation.id


def test_uy_quyen_het_han_thi_khong_bam_thay_duoc(db, seed, person):
    _uy_quyen(db, tu=person["a"], den=person["b"],
              ngay_bat_dau=date.today() - timedelta(days=30),
              ngay_ket_thuc=date.today() - timedelta(days=1))
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    with pytest.raises(HTTPException) as error:
        action_service.approve(db, instance, person["b"], ACTOR, {})
    assert error.value.status_code == 403


def test_uy_quyen_khac_loai_chung_tu_thi_khong_dung_duoc(db, seed, person):
    """Ủy quyền ký văn bản không có nghĩa là ủy quyền duyệt chi tiền."""
    _uy_quyen(db, tu=person["a"], den=person["b"], entity="payment_request")
    _luong_mot_buoc(db, [person["a"]])
    instance = _trinh(db, person["nop"])

    with pytest.raises(HTTPException):
        action_service.approve(db, instance, person["b"], ACTOR, {})


def test_viec_cua_chinh_minh_uu_tien_hon_viec_bam_thay(db, seed, person):
    """Đang nhận ủy quyền không có nghĩa là mất quyền xử lý việc của bản thân."""
    _uy_quyen(db, tu=person["a"], den=person["b"])
    _luong_mot_buoc(db, [person["a"], person["b"]], multi_mode=MULTI_ALL)
    instance = _trinh(db, person["nop"])

    action_service.approve(db, instance, person["b"], ACTOR, {})

    done = [row for row in instance_service.tasks_of_instance(db, instance.id)
            if row.status == TASK_APPROVED]
    assert [row.assignee_employee_id for row in done] == [person["b"]]


def test_cam_uy_quyen_day_chuyen(db, seed, person):
    """A ủy cho B rồi B ủy tiếp cho C thì việc của A cuối cùng do C bấm, mà C
    không hề biết mình đang ký thay A."""
    _uy_quyen(db, tu=person["a"], den=person["b"])

    with pytest.raises(HTTPException) as error:
        delegation_service.validate_before_save(
            db, from_employee_id=person["b"], to_employee_id=person["c"], entity="",
            from_date=date.today(), to_date=date.today() + timedelta(days=3))
    assert "dây chuyền" in error.value.detail


def test_khong_uy_quyen_cho_chinh_minh(db, seed, person):
    with pytest.raises(HTTPException):
        delegation_service.validate_before_save(
            db, person["a"], person["a"], "", date.today(), date.today())


def test_ngay_bat_dau_phai_truoc_ngay_ket_thuc(db, seed, person):
    with pytest.raises(HTTPException):
        delegation_service.validate_before_save(
            db, person["a"], person["b"], "",
            date.today() + timedelta(days=5), date.today())


# ── Bàn giao khi nghỉ việc (I23) ────────────────────────────────────────────

def test_ban_giao_hang_loat_chuyen_het_viec_dang_treo(db, seed, person):
    """Làm từng phiếu thì người bàn giao bỏ sót, và phiếu bỏ sót nằm im cho tới
    khi có người đi hỏi."""
    _luong_mot_buoc(db, [person["a"]], code="HD-BG")
    for i in range(3):
        _trinh(db, person["nop"], entity_id=900 + i)

    task_count = action_service.bulk_handover(db, person["a"], person["c"], ACTOR)

    assert task_count == 3
    remaining = db.query(ApprovalTask).filter(
        ApprovalTask.assignee_employee_id == person["a"],
        ApprovalTask.status == TASK_PENDING).count()
    assert remaining == 0


def test_ban_giao_khong_dung_toi_viec_da_xong(db, seed, person):
    _luong_mot_buoc(db, [person["a"]], code="HD-BG2")
    instance = _trinh(db, person["nop"], entity_id=950)
    action_service.approve(db, instance, person["a"], ACTOR, {})

    assert action_service.bulk_handover(db, person["a"], person["c"], ACTOR) == 0
