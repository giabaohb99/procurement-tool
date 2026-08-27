"""BỘ MÁY DUYỆT — CHIẾM CHỮ KÝ CỦA NGƯỜI KHÁC.

`test_bo_may_duyet_ca_hiem.py` đi tìm chỗ hai tính năng đúng riêng lẻ ghép lại
thành đường đi sai. Tệp này đi tìm một thứ khác: **kẻ tà đạo có sẵn một quyền
vai trò hành chính** (`approval_flow.write` / `create` — thứ hay được cấp cho
trợ lý, admin phân hệ, người khai luồng) rồi dùng nó để **ký thay giám đốc**.

Ba đường vào, cùng một họ lỗi: bộ máy hỏi *"anh có quyền vai trò không"* nhưng
KHÔNG hỏi *"anh có tư cách gì với CON NGƯỜI này"*.

    1. Ủy quyền  — lập tờ ủy quyền TỪ giám đốc SANG mình. Nhật ký ghi
       «B duyệt thay A theo ủy quyền số 12», nhìn hoàn toàn hợp lệ.
    2. Chuyển việc — đổi tên người xử lý một việc sang chính mình rồi tự ký.
    3. Bàn giao hàng loạt — một cú gọi chuyển SẠCH việc đang chờ của giám đốc
       sang mình, nhật ký ghi «Bàn giao 30 việc duyệt» như một thao tác nghỉ việc
       bình thường.

Đường 3 nặng nhất: ủy quyền còn để lại chữ «ký thay», còn bàn giao thì việc đổi
hẳn chủ — bản in dấu vết không còn chỗ nào nói người ký không phải người được
giao ban đầu.

Cặp đối chứng đi kèm mỗi ca: bịt cửa không được làm chết thao tác thật (trợ lý
lập ủy quyền hộ sếp, hành chính bàn giao việc khi có người nghỉ).
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, delegation_service, instance_service
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode)
from app.modules.approval.instance_model import TASK_PENDING
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1
ENTITY = "document"
TODAY = date.today()


@pytest.fixture()
def vai(db, seed):
    """Bốn nhân vật: giám đốc · kẻ tà đạo · người ngoài cuộc · người trình phiếu."""
    ids = {"nop": seed.emp_req_id}
    for name in ("giam_doc", "ke_gian", "nguoi_la"):
        employee = Employee(code=f"CQ_{name.upper()}", full_name=f"Người {name}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        user = User(email=f"{name}@cq.test", employee_id=employee.id,
                    password_hash="x", is_active=True)
        db.add(user)
        db.flush()
        ids[name] = employee.id
        ids[f"{name}_user"] = user.id
    db.commit()
    return ids


def _luong_mot_buoc(db, approvers: int, code="CQ-01") -> ApprovalFlow:
    flow = ApprovalFlow(entity=ENTITY, code=code, name="Luồng chiếm quyền",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Giám đốc duyệt",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(approvers),
                        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    db.refresh(flow)
    return flow


def _trinh(db, submitter, entity_id=9101):
    return instance_service.start(db, ENTITY, entity_id, {}, submitter, ACTOR,
                                    entity_code="VB-CQ", entity_title="Phiếu chiếm quyền")


def _viec_dang_cho(db, instance):
    return [row for row in instance_service.tasks_of_instance(db, instance.id)
            if row.status == TASK_PENDING]


# ── ĐƯỜNG 1: tự lập tờ ủy quyền TỪ người khác SANG mình ─────────────────────
def test_khong_tu_lap_uy_quyen_TU_nguoi_khac_SANG_minh(db, vai):
    """Ca bẩn nhất của cả tệp.

    Kẻ gian có `approval_flow.create` (quyền khai luồng — hay cấp cho trợ lý và
    admin phân hệ) lập một dòng ủy quyền `from = giám đốc, to = chính mình`. Giám
    đốc không hề bấm gì, không nhận thông báo nào. Từ giây đó kẻ gian ký được MỌI
    phiếu đang chờ giám đốc, và dấu vết ghi «ký thay theo ủy quyền» — đúng thứ
    một người soát sổ sẽ lướt qua.

    Luật đúng: **chỉ chính người ủy quyền mới lập được tờ ủy quyền của mình.**
    """
    with pytest.raises(HTTPException) as error:
        delegation_service.validate_before_save(
            db, vai["giam_doc"], vai["ke_gian"], ENTITY,
            TODAY, TODAY + timedelta(days=30),
            actor_employee_id=vai["ke_gian"],
        )
    assert error.value.status_code == 403


def test_chinh_chu_van_tu_lap_uy_quyen_cua_minh_duoc(db, vai):
    """CẶP ĐỐI CHỨNG. Giám đốc đi công tác tự khai ủy quyền — việc thường ngày."""
    delegation_service.validate_before_save(
        db, vai["giam_doc"], vai["ke_gian"], ENTITY,
        TODAY, TODAY + timedelta(days=30),
        actor_employee_id=vai["giam_doc"],
    )


def test_nguoi_quan_tri_van_lap_ho_duoc(db, vai):
    """CẶP ĐỐI CHỨNG. Trợ lý / hành chính lập hộ là nghiệp vụ có thật.

    Nên cửa không đóng bằng "phải là chính chủ" mà bằng "chính chủ HOẶC người có
    quyền quản trị nhân sự duyệt" — `actor_employee_id=None` nghĩa là chỗ gọi
    đã tự kiểm quyền ấy (xem `delegation_controller`).
    """
    delegation_service.validate_before_save(
        db, vai["giam_doc"], vai["ke_gian"], ENTITY,
        TODAY, TODAY + timedelta(days=30),
        actor_employee_id=None,
    )


def test_van_chan_uy_quyen_cho_chinh_minh_va_ngay_nguoc(db, vai):
    """Bịt cửa mới không được làm rơi ba luật cũ."""
    for tu, den, ngay_dau, ngay_cuoi in (
        (vai["giam_doc"], vai["giam_doc"], TODAY, TODAY + timedelta(days=1)),
        (vai["giam_doc"], vai["ke_gian"], TODAY + timedelta(days=5), TODAY),
    ):
        with pytest.raises(HTTPException) as error:
            delegation_service.validate_before_save(
                db, tu, den, ENTITY, ngay_dau, ngay_cuoi,
                actor_employee_id=tu)
        assert error.value.status_code == 400


# ── ĐƯỜNG 2: chuyển việc của người khác sang chính mình ─────────────────────
def test_khong_tu_chuyen_viec_cua_nguoi_khac_SANG_MINH(db, vai):
    """Kẻ gian có `approval_flow.write` đổi tên người xử lý việc sang chính mình.

    Bàn giao là thao tác dành cho người NGHỈ VIỆC — người thứ ba đứng ra sắp xếp.
    Tự bốc việc của người khác về tay mình không phải bàn giao, đó là chiếm việc.
    """
    flow = _luong_mot_buoc(db, vai["giam_doc"])
    assert flow.id
    instance = _trinh(db, vai["nop"])
    task = _viec_dang_cho(db, instance)[0]
    assert task.assignee_employee_id == vai["giam_doc"]

    with pytest.raises(HTTPException) as error:
        action_service.reassign(
            db, task, vai["ke_gian"], ACTOR, "Bàn giao",
            actor_employee_id=vai["ke_gian"])
    assert error.value.status_code == 403


def test_nguoi_thu_BA_van_chuyen_viec_binh_thuong(db, vai):
    """CẶP ĐỐI CHỨNG. Hành chính chuyển việc của người nghỉ sang người khác."""
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-02")
    instance = _trinh(db, vai["nop"], entity_id=9102)
    task = _viec_dang_cho(db, instance)[0]

    da_doi = action_service.reassign(
        db, task, vai["nguoi_la"], ACTOR, "Bàn giao khi nghỉ việc",
        actor_employee_id=vai["ke_gian"])
    assert da_doi.assignee_employee_id == vai["nguoi_la"]


def test_chinh_nguoi_giu_viec_van_nhuong_lai_duoc(db, vai):
    """CẶP ĐỐI CHỨNG. Giám đốc tự nhường việc của mình cho người khác."""
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-03")
    instance = _trinh(db, vai["nop"], entity_id=9103)
    task = _viec_dang_cho(db, instance)[0]

    da_doi = action_service.reassign(
        db, task, vai["nguoi_la"], ACTOR, "Nhờ xử lý hộ",
        actor_employee_id=vai["giam_doc"])
    assert da_doi.assignee_employee_id == vai["nguoi_la"]


def test_van_chan_chuyen_viec_sang_chinh_nguoi_trinh_phieu(db, vai):
    """Luật cũ I08 phải còn nguyên sau khi thêm luật mới."""
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-04")
    instance = _trinh(db, vai["nop"], entity_id=9104)
    task = _viec_dang_cho(db, instance)[0]

    with pytest.raises(HTTPException) as error:
        action_service.reassign(
            db, task, vai["nop"], ACTOR, "", actor_employee_id=vai["nguoi_la"])
    assert error.value.status_code == 400


# ── ĐƯỜNG 3: bàn giao HÀNG LOẠT về tay mình ────────────────────────────────
def test_khong_ban_giao_HANG_LOAT_ve_tay_minh(db, vai):
    """Nặng nhất trong ba đường.

    Ủy quyền còn để lại chữ «ký thay A»; bàn giao thì việc ĐỔI HẲN CHỦ — bản in
    dấu vết không còn chỗ nào nói người ký không phải người được giao ban đầu.
    Một cú gọi quét sạch hộp việc của giám đốc sang tên kẻ gian, nhật ký ghi
    «Bàn giao 30 việc duyệt», nhìn y như thao tác nghỉ việc bình thường.
    """
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-05")
    for i in range(3):
        _trinh(db, vai["nop"], entity_id=9200 + i)

    with pytest.raises(HTTPException) as error:
        action_service.bulk_handover(
            db, vai["giam_doc"], vai["ke_gian"], ACTOR, "Bàn giao",
            actor_employee_id=vai["ke_gian"])
    assert error.value.status_code == 403


def test_ban_giao_hang_loat_cho_NGUOI_KHAC_van_chay(db, vai):
    """CẶP ĐỐI CHỨNG — I23 là tính năng thật, không được làm chết nó."""
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-06")
    for i in range(3):
        _trinh(db, vai["nop"], entity_id=9300 + i)

    task_count = action_service.bulk_handover(
        db, vai["giam_doc"], vai["nguoi_la"], ACTOR, "Nghỉ việc",
        actor_employee_id=vai["ke_gian"])
    assert task_count == 3


def test_chinh_chu_ban_giao_het_viec_cua_MINH_thi_duoc(db, vai):
    """CẶP ĐỐI CHỨNG. Giám đốc nghỉ phép, tự đẩy hết việc sang cấp phó."""
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-07")
    for i in range(2):
        _trinh(db, vai["nop"], entity_id=9400 + i)

    task_count = action_service.bulk_handover(
        db, vai["giam_doc"], vai["nguoi_la"], ACTOR, "Đi công tác",
        actor_employee_id=vai["giam_doc"])
    assert task_count == 2


# ── Chốt lại bằng chiều KẾT QUẢ: chiếm được việc là ký được ────────────────
def test_chiem_duoc_viec_la_ky_duoc_ngay(db, vai):
    """Vì sao ba cửa trên đáng chặn: chiếm việc xong là ký được, không cửa nào nữa.

    Bài này KHÔNG kiểm lỗ hổng — nó chứng minh hậu quả, để ai đó định nới lỏng
    ba luật trên thì thấy ngay cái giá.
    """
    _luong_mot_buoc(db, vai["giam_doc"], code="CQ-08")
    instance = _trinh(db, vai["nop"], entity_id=9500)
    task = _viec_dang_cho(db, instance)[0]

    #  Kẻ gian chưa có việc gì ở phiếu này -> bấm duyệt là 403.
    with pytest.raises(HTTPException) as error:
        action_service.pending_task_of(db, instance, vai["ke_gian"])
    assert error.value.status_code == 403

    #  Nhưng chỉ cần MỘT thao tác hành chính chuyển việc về tay mình…
    action_service.reassign(db, task, vai["ke_gian"], ACTOR, "",
                                      actor_employee_id=vai["nguoi_la"])
    #  …là ký được ngay, không còn cửa nào hỏi lại.
    task, delegation = action_service.pending_task_of(db, instance, vai["ke_gian"])
    assert task.assignee_employee_id == vai["ke_gian"]
    assert delegation is None


# ── ĐƯỜNG 4: chiếm luôn ĐƯỜNG DUYỆT thay vì chiếm chữ ký ────────────────────
def test_pham_vi_hep_khong_khai_duoc_luong_cho_MOI_phap_nhan(db, seed, vai, cap_quyen):
    """Không giả chữ ký của ai — chỉ đổi chỗ cần chữ ký.

    Khai một luồng `company_id = None` (áp cho MỌI pháp nhân) với `priority` cao
    nhất và đúng một bước «người duyệt = tôi»: mọi văn bản mới của cả tập đoàn
    chạy về tay người khai, hoàn toàn đúng quy trình trên giấy tờ.

    Sửa luồng thì `_load` đã gác bằng `get_scoped` từ B-07, nhưng TẠO MỚI thì
    trước đây không ai hỏi gì.
    """
    from app.modules.approval.flow_controller import _block_scope_on_declare

    cap_quyen(vai["ke_gian_user"], "approval_flow", scope="company",
              create=True, write=True)
    tk = db.get(User, vai["ke_gian_user"])

    with pytest.raises(HTTPException) as error:
        _block_scope_on_declare(db, tk, None, "create")
    assert error.value.status_code == 403


def test_pham_vi_hep_khong_khai_duoc_luong_cho_phap_nhan_KHAC(db, seed, vai, cap_quyen):
    from app.modules.approval.flow_controller import _block_scope_on_declare

    cap_quyen(vai["ke_gian_user"], "approval_flow", scope="company", create=True)
    tk = db.get(User, vai["ke_gian_user"])

    with pytest.raises(HTTPException) as error:
        _block_scope_on_declare(db, tk, seed.company_id + 999, "create")
    assert error.value.status_code == 403


def test_pham_vi_hep_VAN_khai_duoc_luong_cua_phap_nhan_MINH(db, seed, vai, cap_quyen):
    """CẶP ĐỐI CHỨNG — văn thư pháp nhân con vẫn phải khai được luồng của mình."""
    from app.modules.approval.flow_controller import _block_scope_on_declare

    cap_quyen(vai["ke_gian_user"], "approval_flow", scope="company", create=True)
    tk = db.get(User, vai["ke_gian_user"])
    _block_scope_on_declare(db, tk, seed.company_id, "create")


def test_quan_tri_toan_he_van_khai_duoc_luong_dung_chung(db, vai, cap_quyen):
    """CẶP ĐỐI CHỨNG — luồng dùng chung cho mọi pháp nhân là tính năng thật."""
    from app.modules.approval.flow_controller import _block_scope_on_declare

    cap_quyen(vai["ke_gian_user"], "approval_flow", scope="all", create=True)
    tk = db.get(User, vai["ke_gian_user"])
    _block_scope_on_declare(db, tk, None, "create")


def test_cong_tac_TOAN_HE_doi_pham_vi_toan_he(db, vai, cap_quyen):
    """Công tắc I26 tắt bộ máy duyệt cho CẢ 13 PHÁP NHÂN.

    Nó không có `flow_id` nên `get_scoped` không với tới; chỉ `require(...)` thôi
    thì một văn thư pháp nhân con phạm vi *công ty* tắt được đường duyệt của toàn
    hệ, nhật ký chỉ ghi một dòng «Tắt bộ máy duyệt mới cho document».
    """
    from app.core.auth import get_perm_profile
    from app.core.scoping import has_global_scope

    cap_quyen(vai["ke_gian_user"], "approval_flow", scope="company", write=True)
    tk_hep = db.get(User, vai["ke_gian_user"])
    assert has_global_scope(get_perm_profile(db, tk_hep), "approval_flow", "write") is False

    cap_quyen(vai["nguoi_la_user"], "approval_flow", scope="all", write=True)
    tk_rong = db.get(User, vai["nguoi_la_user"])
    assert has_global_scope(get_perm_profile(db, tk_rong), "approval_flow", "write") is True
