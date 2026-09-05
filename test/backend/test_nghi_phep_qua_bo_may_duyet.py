"""P-05 (CR-259) — đơn nghỉ phép chạy qua BỘ MÁY DUYỆT THẬT, không phải hook giả.

Tệp `test_nghi_phep_don_va_duyet.py` gọi thẳng bốn hook để chốt luật trừ quỹ.
Tệp này khác: nó dựng một luồng duyệt thật rồi để bộ máy tự gọi hook, nên nó
chốt phần NỐI — `entity_hooks.register` có ăn không, `instance_service.start` có
nhận entity `leave_request` không, và bốn kết cục có về đúng tay module này không.

⚠️ Bài quan trọng nhất là `test_huy_don_dang_trong_luong_thi_rut_phien_duyet`.
Lỗi thật, dựng lại được 03/09/2026 lúc chạy thử: đường hủy gọi nhầm
`block_legacy_path` nên người xin nghỉ đổi ý ăn đúng câu *"đừng bấm duyệt thẳng
ở đây"* — vô nghĩa với thao tác họ vừa làm, và không còn cách nào rút đơn.
Tệ hơn: nếu bỏ chốt đó mà KHÔNG rút phiên thì phiếu duyệt vẫn chạy, người duyệt
ký xong là hook trừ quỹ cho một tờ đơn đã hủy.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_RUNNING,
                                                 INSTANCE_WITHDRAWN,
                                                 TASK_PENDING)
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, balance_service, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LR_APPROVED, LR_CANCELLED, LR_DRAFT,
                                         LR_PENDING, LR_REJECTED, LR_RETURNED)
from app.modules.leave.schema import LeaveRequestCreate

ACTOR = 1
ENTITY = "leave_request"
MONDAY = date(2026, 1, 5)


# ── Dựng cảnh ───────────────────────────────────────────────────────────────

@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True,
                    annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def submitter(db):
    obj = Employee(code="NV_NOP", full_name="Người nộp", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def approver(db):
    obj = Employee(code="NV_DUYET", full_name="Người duyệt", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def flow_switch_off(db, approver):
    """Luồng MỘT bước đã khai, NHƯNG cờ bộ máy còn TẮT.

    Tách riêng khỏi `flow` để dựng được đúng cảnh của màn «Bật bộ máy duyệt»:
    quản trị khai luồng xong nhưng chưa gạt công tắc. Khai luồng và bật cờ là
    HAI việc, và giữa hai việc đó đơn vẫn phải nộp được.
    """
    row = ApprovalFlow(entity=ENTITY, code="NP-TEST", name="Duyệt nghỉ phép (thử)",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    db.add(ApprovalNode(flow_id=row.id, seq=1, name="Trưởng bộ phận",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(approver.id),
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    db.refresh(row)
    return row


@pytest.fixture()
def flow(db, flow_switch_off):
    """Luồng MỘT bước, người duyệt khai đích danh, cờ đã BẬT — chạy hết vòng đời."""
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow_switch_off


def _user(employee: Employee, uid: int = 1):
    return SimpleNamespace(id=uid, employee_id=employee.id)


def _submit(db, leave_type, employee, days=2):
    """Lập đơn rồi gửi duyệt qua đúng đường controller đi."""
    user = _user(employee)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id,
        from_date=MONDAY, to_date=MONDAY + timedelta(days=days - 1),
        reason="Về quê"), user)
    emp, lt = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    return request_service.mark_submitted(db, obj, emp, lt, user, instance_id), instance_id


def _remaining(db, employee, leave_type):
    return balance_service.remaining(db, employee.id, 2026, leave_type.id)


# ── 1. Nối vào bộ máy ───────────────────────────────────────────────────────

def test_co_luong_nhung_co_TAT_thi_don_di_duong_duyet_THANG(db, flow_switch_off,
                                                            leave_type, submitter):
    """Công tắc ở màn «Bật bộ máy duyệt» phải THẬT SỰ cắt được, không phải nút giả.

    Trước 05/09/2026 nghỉ phép trình thẳng vào bộ máy mà không hỏi cờ, nên gạt
    tắt xong đơn vẫn chui vào luồng nhiều bước — đúng cái mà cả màn hình đó nói
    là "đường lui". Đây là bài chốt: có luồng hẳn hoi mà cờ tắt thì không phiên
    nào được mở, và đơn rơi về đường duyệt thẳng một bước.
    """
    obj, instance_id = _submit(db, leave_type, submitter)

    assert instance_id == 0, "Cờ TẮT mà vẫn mở phiên nghĩa là công tắc là nút giả"
    assert approval_bridge.running_instance(db, obj.id) is None
    assert obj.status == LR_PENDING, "Đơn vẫn phải vào Chờ duyệt, không kẹt ở Nháp"

    #  Và đường lui phải đi được thật: không có phiên nên chốt chặn duyệt thẳng
    #  không được ném. Thiếu khẳng định này thì "rơi về đường cũ" mới chỉ đúng
    #  một nửa — đơn vào Chờ duyệt nhưng không ai ký nổi.
    approval_bridge.block_legacy_path(db, obj)


def test_quy_phep_van_giu_cho_khi_co_TAT(db, flow_switch_off, leave_type, submitter):
    """Tắt cờ là đổi ĐƯỜNG DUYỆT, không phải đổi luật quỹ.

    Giữ chỗ nằm ở `mark_submitted` chứ không ở bộ máy duyệt, nên nó phải trừ y
    hệt. Lẫn hai thứ này là nộp mười đơn liền tay đều lọt (xem QĐ `pending_days`).
    """
    _submit(db, leave_type, submitter, days=2)

    #  12 ngày quỹ − 2 ngày đang giữ chỗ. Đúng con số mà nhánh cờ BẬT ra
    #  (`test_gui_duyet_giu_cho_quy_phep`), vì cờ không được đụng tới quỹ.
    assert _remaining(db, submitter, leave_type) == leave_type.annual_quota_days - 2


def test_gui_duyet_mo_dung_mot_phien_tren_bo_may_dung_chung(db, flow, leave_type, submitter):
    obj, instance_id = _submit(db, leave_type, submitter)

    assert instance_id > 0, "Có luồng mà `start` trả 0 nghĩa là entity chưa nối được"
    assert obj.approval_instance_id == instance_id
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    assert instance is not None and instance.status == INSTANCE_RUNNING
    #  Tiêu đề phiếu phải đọc được ở màn Phê duyệt mà không phải mở đơn ra.
    assert obj.code in instance.entity_title


def test_chua_khai_luong_thi_van_gui_duyet_duoc(db, leave_type, submitter):
    """Cài mới xong là phải nộp được đơn, đừng chờ quản trị khai luồng."""
    obj, instance_id = _submit(db, leave_type, submitter)
    assert instance_id == 0
    assert obj.status == LR_PENDING
    assert _remaining(db, submitter, leave_type) == 10.0   # vẫn giữ chỗ


def test_boi_canh_mang_du_o_de_re_nhanh(db, leave_type, submitter):
    """Thiếu ô nào là luồng khai theo ô đó lặng lẽ không bao giờ khớp."""
    obj, _ = _submit(db, leave_type, submitter)
    ctx = approval_bridge.entity_context(obj)
    assert set(ctx) == {"id", "employee_id", "leave_type_id", "company_id",
                        "department_id", "total_days"}
    assert ctx["department_id"] == submitter.department_id


# ── 2. Bốn kết cục đi qua bộ máy thật ───────────────────────────────────────

def test_duyet_het_buoc_thi_don_da_duyet_va_quy_tru_that(db, flow, leave_type,
                                                          submitter, approver):
    obj, _ = _submit(db, leave_type, submitter)
    assert _remaining(db, submitter, leave_type) == 10.0   # đang giữ chỗ

    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, approver.id, ACTOR, {})
    db.refresh(obj)

    assert obj.status == LR_APPROVED
    row = balance_service.get_balance(db, submitter.id, 2026, leave_type.id)
    assert (row.pending_days, row.used_days) == (0.0, 2.0)
    assert _remaining(db, submitter, leave_type) == 10.0   # vẫn 10, nhưng đã nghỉ thật


def test_tu_choi_qua_bo_may_thi_tra_lai_giu_cho(db, flow, leave_type, submitter, approver):
    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.reject(db, instance, approver.id, ACTOR, "Không hợp lý")
    db.refresh(obj)

    assert obj.status == LR_REJECTED
    assert _remaining(db, submitter, leave_type) == 12.0
    #  Lý do phải chép về tận tờ đơn, để màn chi tiết không phải gọi sang bộ máy.
    assert "Không hợp lý" in obj.decision_note


def test_tra_lai_qua_bo_may_thi_don_sua_duoc_va_quy_ve_nguyen(db, flow, leave_type,
                                                               submitter, approver):
    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.send_back(db, instance, approver.id, ACTOR, "Thiếu bàn giao", {})
    db.refresh(obj)

    assert obj.status == LR_RETURNED
    assert _remaining(db, submitter, leave_type) == 12.0
    request_service.check_editable(obj)   # không ném = sửa được


# ── 3. HỦY đơn đang trong luồng — lỗi 03/09/2026 ────────────────────────────

def test_huy_don_dang_trong_luong_thi_rut_phien_duyet(db, flow, leave_type, submitter):
    """Xem docstring đầu tệp. ĐỪNG nới lỏng bài này.

    Ba khẳng định, thiếu cái nào cũng là một cách hỏng khác nhau:
      · đơn phải HỦY được — không thì người đổi ý bị kẹt;
      · phiên duyệt phải ĐÓNG — không thì người duyệt ký cho một đơn đã hủy;
      · quỹ phải TRẢ LẠI ĐỦ, đúng một lần — rút và hủy đều trả thì mất kiểm soát.
    """
    obj, _ = _submit(db, leave_type, submitter)
    assert _remaining(db, submitter, leave_type) == 10.0

    obj = approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))

    assert obj.status == LR_CANCELLED
    assert instance_service.running_instance(db, ENTITY, obj.id) is None
    assert _remaining(db, submitter, leave_type) == 12.0


def test_ly_do_huy_di_thang_vao_dau_vet_phien_duyet(db, flow, leave_type, submitter):
    """Lý do NGƯỜI DÙNG gõ phải nằm trong dấu vết, không phải một câu cứng.

    Dòng thời gian trên màn chi tiết đọc từ dấu vết này ra. Ghi câu chung
    ("Người nộp hủy đơn nghỉ phép") thì mọi tờ đơn hủy đều nói đúng một câu vô
    nghĩa như nhau, và người đọc lại không bao giờ biết VÌ SAO.
    """
    from app.modules.approval.instance_model import ApprovalAction

    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))

    comments = [row.comment for row in
                db.query(ApprovalAction).filter(ApprovalAction.instance_id == instance.id).all()]
    assert any("Đổi kế hoạch" in (c or "") for c in comments), comments


def test_huy_khong_ghi_ly_do_van_co_cau_mac_dinh(db, flow, leave_type, submitter):
    """Bỏ trống lý do thì vẫn phải có chữ, đừng để dấu vết trống trơn."""
    from app.modules.approval.instance_model import ApprovalAction

    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    approval_bridge.cancel_request(db, obj, "   ", _user(submitter))

    comments = [row.comment for row in
                db.query(ApprovalAction).filter(ApprovalAction.instance_id == instance.id).all()]
    assert any("Người nộp hủy đơn nghỉ phép" == (c or "") for c in comments), comments


def test_huy_khong_tra_quy_hai_lan(db, flow, leave_type, submitter):
    """Rút phiên trả quỹ MỘT lần, `cancel` thấy đơn đã về Nháp nên không trả nữa.

    Trả hai lần thì `pending` xuống âm — mà `release` kẹp ở 0, nên triệu chứng
    KHÔNG phải là số âm mà là quỹ đúng một cách tình cờ. Bài này chốt con số.
    """
    obj, _ = _submit(db, leave_type, submitter)
    approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))

    row = balance_service.get_balance(db, submitter.id, 2026, leave_type.id)
    assert row.pending_days == 0.0
    assert row.used_days == 0.0
    assert row.remaining_days == 12.0


def test_nguoi_khac_khong_huy_duoc_don_dang_trong_luong(db, flow, leave_type,
                                                         submitter, approver):
    """Luật của bộ máy vọng ra tới đây: chỉ NGƯỜI TRÌNH mới rút được phiên.

    Nhân sự muốn dẹp đơn của người khác thì dùng *Trả lại* / *Từ chối* ở màn Phê
    duyệt, nơi có ô ghi lý do — chứ không lặng lẽ hủy hộ.
    """
    obj, _ = _submit(db, leave_type, submitter)
    with pytest.raises(HTTPException) as e:
        approval_bridge.cancel_request(db, obj, "Dẹp", _user(approver, uid=9))
    assert e.value.status_code == 403

    db.refresh(obj)
    assert obj.status == LR_PENDING
    assert _remaining(db, submitter, leave_type) == 10.0


def test_huy_don_KHONG_o_trong_luong_van_chay_binh_thuong(db, leave_type, submitter):
    """Chưa khai luồng thì không có phiên nào để rút — đừng nổ ở nhánh đó."""
    obj, instance_id = _submit(db, leave_type, submitter)
    assert instance_id == 0

    obj = approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))
    assert obj.status == LR_CANCELLED
    assert _remaining(db, submitter, leave_type) == 12.0


def test_huy_don_da_duyet_hoan_lai_ngay_da_tru(db, flow, leave_type, submitter, approver):
    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, approver.id, ACTOR, {})
    db.refresh(obj)
    assert obj.status == LR_APPROVED

    #  Phiên đã đóng nên không còn gì để rút; đường hủy vẫn phải chạy.
    obj = approval_bridge.cancel_request(db, obj, "Đổi kế hoạch", _user(submitter))
    assert obj.status == LR_CANCELLED
    assert _remaining(db, submitter, leave_type) == 12.0


# ── 4. Chặn đường tắt ───────────────────────────────────────────────────────

def test_don_dang_trong_luong_thi_khong_duyet_thang_duoc(db, flow, leave_type, submitter):
    """Nút duyệt một bước không được thành đường tắt đi vòng qua cả luồng."""
    obj, _ = _submit(db, leave_type, submitter)
    with pytest.raises(HTTPException) as e:
        approval_bridge.block_legacy_path(db, obj)
    assert "luồng phê duyệt nhiều bước" in e.value.detail


def test_chua_khai_luong_thi_duyet_thang_duoc(db, leave_type, submitter):
    obj, _ = _submit(db, leave_type, submitter)
    approval_bridge.block_legacy_path(db, obj)   # không ném


def test_nguoi_ngoai_pham_vi_khong_doc_duoc_phieu_duyet(db, flow, leave_type, submitter):
    """`register_reader` phải ăn: thiếu nó thì phiếu duyệt phơi tên người nghỉ
    và lý do nghỉ cho bất kỳ ai đăng nhập (lỗ hổng đã dựng lại được với văn bản
    25/08/2026)."""
    from app.modules.approval import entity_hooks

    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)

    #  Người dùng KHÔNG có grant nào trên `leave_request` → `apply_scope` chặn hết.
    outsider = SimpleNamespace(id=999, employee_id=888)
    assert entity_hooks.can_read(db, instance, outsider) is False


# ── 5. Đơn không kẹt lại ────────────────────────────────────────────────────

def test_rut_phien_thi_don_ve_nhap_chu_khong_phai_tra_ve(db, flow, leave_type, submitter):
    """Chính người nộp rút thì không ai *trả* gì cho họ cả — về Nháp."""
    obj, _ = _submit(db, leave_type, submitter)
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.withdraw(db, instance, submitter.id, ACTOR, "Đổi ý")
    db.refresh(obj)

    assert instance.status == INSTANCE_WITHDRAWN
    assert obj.status == LR_DRAFT
    assert _remaining(db, submitter, leave_type) == 12.0
    #  Và gửi duyệt lại được ngay, không kẹt.
    request_service.prepare_submit(db, obj, _user(submitter))


def test_khong_mo_hai_phien_cho_cung_mot_don(db, flow, leave_type, submitter):
    """Nhấp đúp «Gửi duyệt» không được đẻ ra hai phiếu duyệt cùng chạy."""
    obj, _ = _submit(db, leave_type, submitter)
    with pytest.raises(HTTPException):
        approval_bridge.start_approval(db, obj, _user(submitter))

    running = [t for t in instance_service.tasks_of_instance(
        db, obj.approval_instance_id) if t.status == TASK_PENDING]
    assert len(running) == 1
