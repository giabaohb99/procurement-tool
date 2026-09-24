"""XEM TRƯỚC LUỒNG DUYỆT — thẻ «Người duyệt dự kiến» ở màn tạo văn bản (phase
01, duoc-CR-473).

Ba câu phải trả lời, đúng thứ tự ưu tiên của phase:

1. `preview_service.preview_flow` phải áp ĐÚNG luật của `open_stage` (bỏ người
   nộp, bỏ trùng người chặng trước, dự phòng/dừng phiếu) — chỉ khác ở chỗ
   KHÔNG ghi gì cả.
2. Ba trạng thái `mode` phải đúng: `flow` · `legacy` · `none`.
3. **Xem trước phải TRÙNG THỰC TẾ** — gửi duyệt xong, người được giao việc ở
   từng chặng phải khớp đúng danh sách đã xem trước (dữ liệu tổ chức không đổi
   giữa hai lần gọi). Đây là bài kiểm quan trọng nhất của cả phase.
"""
import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service, preview_service
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_EMPLOYEE, APPROVER_FIELD,
                                             NODE_CC, NO_APPROVER_BLOCK,
                                             NO_APPROVER_FALLBACK, SKIP_ADJACENT,
                                             SKIP_NONE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import approval_bridge, service
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

ACTOR = 1
ENTITY = "document"


def _loai(db, needs_approval=True):
    kind = DocType(code="QC", name="Quy chế", needs_approval=needs_approval,
                   is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(kind)
    db.commit()
    return kind


def _nguoi(db, code, company_id, dept_id):
    employee = Employee(code=code, full_name=f"Người {code}", company_id=company_id,
                        department_id=dept_id, is_active=True)
    db.add(employee)
    db.commit()
    return employee


def _bat_co(db):
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _luong(db, **kw):
    flow = ApprovalFlow(entity=ENTITY, code=kw.pop("code", "VB-01"),
                        name=kw.pop("name", "Luồng văn bản"), is_active=True,
                        created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(flow)
    db.commit()
    return flow


def _buoc(db, flow, seq, **kw):
    node = ApprovalNode(flow_id=flow.id, seq=seq, name=kw.pop("name", f"Bước {seq}"),
                        created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(node)
    db.commit()
    return node


@pytest.fixture()
def hai_nguoi_duyet(db, seed):
    a = _nguoi(db, "PV_A", seed.company_id, seed.dept_id)
    b = _nguoi(db, "PV_B", seed.company_id, seed.dept_id)
    return a, b


# ── mode: none ───────────────────────────────────────────────────────────────

def test_loai_khong_can_duyet_khong_goi_toi_preview_service(db, seed):
    """`needs_approval = false` là chuyện của `DocType`, bộ máy duyệt không biết
    khái niệm đó — chốt ở CONTROLLER, kiểm bằng cách gọi thẳng hàm route."""
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)
    from app.modules.user.model import User

    kind = _loai(db, needs_approval=False)
    user = db.get(User, seed.u_req_id)

    import json

    response = preview_approval(
        PreviewApprovalIn(doc_type_id=kind.id, company_id=seed.company_id),
        db, user,
    )
    body = json.loads(response.body)
    assert body["data"]["mode"] == "none"
    assert body["data"]["steps"] == []


# ── M3 (rà soát 23/09/2026) — chặn dò ngoài phạm vi qua xem trước ───────────
def test_xem_truoc_phap_nhan_ngoai_pham_vi_bi_chan(db, world):
    """`company_id` gõ tay TRỎ SANG một pháp nhân ngoài phạm vi `document.create`
    của người xem trước — trước M3 không kiểm gì, dò được tên người duyệt ở
    một pháp nhân người này chưa từng có quyền tạo văn bản."""
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)

    world.grant("a1", "document", scope="company", actions=("create",))
    kind = _loai(db)
    a1 = world.actor("a1")

    with pytest.raises(HTTPException) as exc:
        preview_approval(PreviewApprovalIn(doc_type_id=kind.id, company_id=world.co["B"]),
                         db, a1.user)
    assert exc.value.status_code == 400


def test_xem_truoc_phap_nhan_trong_pham_vi_khong_bi_chan(db, world):
    """Đối chứng: `company_id` ĐÚNG pháp nhân trong phạm vi thì đi tiếp bình
    thường (không 400 vì lý do phạm vi — có thể vẫn `legacy` vì chưa có luồng)."""
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)

    world.grant("a1", "document", scope="company", actions=("create",))
    kind = _loai(db)
    a1 = world.actor("a1")

    response = preview_approval(PreviewApprovalIn(doc_type_id=kind.id, company_id=world.co["A"]),
                                db, a1.user)
    assert response.status_code == 200


def test_xem_truoc_phong_ban_ngoai_pham_vi_bi_chan(db, world):
    """`department_id` của một pháp nhân KHÁC — không phải chỉ `company_id`
    mới cần kiểm, phòng ban cũng phải nằm trong phạm vi đọc của người xem."""
    from app.modules.department.model import Department
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)

    world.grant("a1", "document", scope="all", actions=("create",))   # mọi pháp nhân
    world.grant("a1", "department", scope="company", actions=("read",))   # CHỈ công ty mình
    kind = _loai(db)
    a1 = world.actor("a1")
    dept_b = db.get(Department, world.dept["B.kt"])

    with pytest.raises(HTTPException) as exc:
        preview_approval(
            PreviewApprovalIn(doc_type_id=kind.id, company_id=world.co["B"],
                              department_id=dept_b.id),
            db, a1.user)
    assert exc.value.status_code == 400


def test_xem_truoc_nhan_su_ngoai_pham_vi_bi_chan(db, world):
    """`owner_employee_id`/`drafter_employee_id`/`signer_employee_id` gõ tay
    trỏ sang nhân sự ngoài phạm vi `employee.read` — đây chính là lỗ lộ tên
    người quản lý trực tiếp (APPROVER_LEVEL_UP) mà M3 vá."""
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)

    world.grant("a1", "document", scope="all", actions=("create",))
    world.grant("a1", "employee", scope="company", actions=("read",))
    kind = _loai(db)
    a1 = world.actor("a1")

    with pytest.raises(HTTPException) as exc:
        preview_approval(
            PreviewApprovalIn(doc_type_id=kind.id, company_id=world.co["B"],
                              signer_employee_id=world.emp["b1"]),
            db, a1.user)
    assert exc.value.status_code == 400


def test_xem_truoc_van_ban_goc_khong_doc_duoc_bi_chan(db, world):
    """`source_document_id` (xem trước cho bản CLONE) trỏ vào văn bản người
    này KHÔNG đọc được — trước M3 không kiểm `access_service.can`, lộ luôn cả
    khả năng dò xem văn bản đó có tồn tại."""
    from app.modules.document.approval_preview_controller import (
        PreviewApprovalIn, preview_approval)
    from app.modules.document.model import ORIGIN_INTERNAL, Document

    world.grant("a1", "document", scope="company", actions=("create", "read"))
    other_doc = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=world.co["B"],
                         department_id=0, owner_employee_id=0, title="Bí mật công ty B",
                         legacy_code="SRC1", created_by=0, updated_by=0)
    db.add(other_doc)
    db.commit()
    kind = _loai(db)
    a1 = world.actor("a1")

    with pytest.raises(HTTPException) as exc:
        preview_approval(
            PreviewApprovalIn(doc_type_id=kind.id, company_id=world.co["A"],
                              source_document_id=other_doc.id),
            db, a1.user)
    assert exc.value.status_code == 400


# ── mode: legacy ─────────────────────────────────────────────────────────────

def test_bo_may_tat_thi_legacy(db, seed):
    _luong(db, code="VB-01")   # có luồng thật, nhưng cờ chưa bật

    out = preview_service.preview_flow(db, ENTITY, {"company_id": seed.company_id}, None)

    assert out["mode"] == "legacy"
    assert out["engine_enabled"] is False
    assert out["steps"] == [] and out["cc"] == []


def test_bat_co_nhung_khong_luong_nao_khop_thi_legacy(db, seed):
    _bat_co(db)

    out = preview_service.preview_flow(db, ENTITY, {"company_id": seed.company_id}, None)

    assert out["mode"] == "legacy"
    assert out["engine_enabled"] is True


# ── mode: flow — chuỗi cơ bản ────────────────────────────────────────────────

def test_luong_hai_chang_tra_dung_ten_va_chuc_vu(db, seed, hai_nguoi_duyet):
    a, b = hai_nguoi_duyet
    a.position, b.position = "Trưởng phòng Nhân sự", "Giám đốc Tài chính"
    db.commit()
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         skip_duplicate=SKIP_NONE)
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(b.id),
         skip_duplicate=SKIP_NONE)

    out = preview_service.preview_flow(db, ENTITY, {"company_id": seed.company_id}, None)

    assert out["mode"] == "flow"
    assert out["flow_name"] == "Luồng văn bản"
    assert [s["seq"] for s in out["steps"]] == [1, 2]
    assert out["steps"][0]["approvers"] == [
        {"employee_id": a.id, "name": "Người PV_A", "position": "Trưởng phòng Nhân sự"}]
    assert out["steps"][1]["approvers"][0]["position"] == "Giám đốc Tài chính"
    assert all(not s["unresolved_reason"] for s in out["steps"])


def test_nhanh_theo_dieu_kien_chon_dung_nhanh(db, seed, hai_nguoi_duyet):
    a, b = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    #  Cùng chặng 1, hai nhánh: khẩn (urgency=2) → a; mặc định → b.
    _buoc(db, flow, 1, branch_key="khan", approver_kind=APPROVER_EMPLOYEE,
         approver_ref=str(a.id), skip_duplicate=SKIP_NONE,
         condition='[{"field": "urgency", "op": "eq", "value": 2}]')
    _buoc(db, flow, 1, branch_key="thuong", approver_kind=APPROVER_EMPLOYEE,
         approver_ref=str(b.id), skip_duplicate=SKIP_NONE, is_default_branch=True)

    khan = preview_service.preview_flow(db, ENTITY, {"urgency": 2}, None)
    thuong = preview_service.preview_flow(db, ENTITY, {"urgency": 1}, None)

    assert khan["steps"][0]["approvers"][0]["employee_id"] == a.id
    assert thuong["steps"][0]["approvers"][0]["employee_id"] == b.id


def test_khong_nhanh_nao_khop_thi_bao_ket(db, seed, hai_nguoi_duyet):
    """`step_of_stage` chỉ THỰC SỰ xét điều kiện khi chặng có ≥ 2 nhánh — một
    chặng chỉ một bước thì luôn được chọn bất kể điều kiện (hành vi gốc của
    `flow_service`). Nên ca KẸT cần ÍT NHẤT hai nhánh, không nhánh nào mặc định,
    và cả hai đều không khớp `subject`."""
    a, b = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, branch_key="x1", approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         condition='[{"field": "urgency", "op": "eq", "value": 2}]')
    _buoc(db, flow, 1, branch_key="x2", approver_kind=APPROVER_EMPLOYEE, approver_ref=str(b.id),
         condition='[{"field": "urgency", "op": "eq", "value": 3}]')

    out = preview_service.preview_flow(db, ENTITY, {"urgency": 1}, None)

    assert out["steps"][0]["approvers"] == []
    assert "Không nhánh nào khớp" in out["steps"][0]["unresolved_reason"]


# ── I08 — bỏ người nộp (trừ kiểu khai đích danh) ─────────────────────────────

def test_truong_phong_tu_nop_phieu_thi_buoc_rong_va_dung_phieu(db, seed):
    """DEPT_HEAD khi chính người nộp là trưởng phòng — `_submitter_department_head`
    trả rỗng, và không có dự phòng thì hệ phải nói rõ SẼ DỪNG."""
    department = db.get(Department, seed.dept_id)
    department.manager_id = seed.emp_tp_id
    db.commit()
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_DEPT_HEAD, on_no_approver=NO_APPROVER_BLOCK)

    out = preview_service.preview_flow(
        db, ENTITY, {"department_id": seed.dept_id}, seed.emp_tp_id)

    assert out["steps"][0]["approvers"] == []
    assert "DỪNG" in out["steps"][0]["unresolved_reason"]
    assert out["steps"][0]["fallback_used"] is False


def test_khong_tim_duoc_nguoi_duyet_nhung_co_du_phong(db, seed, hai_nguoi_duyet):
    a, _ = hai_nguoi_duyet
    #  Phòng CHƯA có trưởng bộ phận -> DEPT_HEAD rỗng -> rơi vào dự phòng.
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_DEPT_HEAD,
         on_no_approver=NO_APPROVER_FALLBACK, fallback_employee_id=a.id)

    out = preview_service.preview_flow(
        db, ENTITY, {"department_id": seed.dept_id}, seed.emp_req_id)

    assert out["steps"][0]["approvers"] == [
        {"employee_id": a.id, "name": "Người PV_A", "position": ""}]
    assert out["steps"][0]["fallback_used"] is True
    assert not out["steps"][0]["unresolved_reason"]


# ── APPROVER_FIELD chưa chọn ──────────────────────────────────────────────────

def test_field_nguoi_ky_chua_chon_khong_phai_khong_co_ai(db, seed):
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_FIELD, approver_ref="signer_employee_id",
         on_no_approver=NO_APPROVER_BLOCK)

    out = preview_service.preview_flow(
        db, ENTITY, {"signer_employee_id": 0}, seed.emp_req_id)

    step = out["steps"][0]
    assert step["pending_field"] == "signer_employee_id"
    assert step["unresolved_reason"] == "Sẽ là người ký — chưa chọn"
    assert "DỪNG" not in step["unresolved_reason"]
    assert "không tìm được" not in step["unresolved_reason"].lower()


def test_field_da_chon_thi_tra_dung_nguoi(db, seed, hai_nguoi_duyet):
    a, _ = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_FIELD, approver_ref="signer_employee_id")

    out = preview_service.preview_flow(
        db, ENTITY, {"signer_employee_id": a.id}, seed.emp_req_id)

    assert out["steps"][0]["approvers"][0]["employee_id"] == a.id
    assert out["steps"][0]["pending_field"] == ""


# ── I06 — bỏ trùng người chặng trước ──────────────────────────────────────────

def test_trung_nguoi_chang_truoc_thi_tu_dong_qua(db, seed, hai_nguoi_duyet):
    a, _ = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         skip_duplicate=SKIP_ADJACENT)
    #  Chặng 2 CÙNG một người — mặc định `skip_duplicate=SKIP_ADJACENT` (cột
    #  của bảng), nên phải tự động qua theo giả định "chặng 1 rồi cũng duyệt".
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id))

    out = preview_service.preview_flow(db, ENTITY, {}, None)

    assert out["steps"][1]["approvers"] == []
    assert "tự động qua" in out["steps"][1]["note"]
    assert not out["steps"][1]["unresolved_reason"], "Tự qua KHÔNG phải là kẹt"


def test_tat_bo_qua_trung_thi_van_phai_duyet_lai(db, seed, hai_nguoi_duyet):
    a, _ = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         skip_duplicate=SKIP_NONE)
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         skip_duplicate=SKIP_NONE)

    out = preview_service.preview_flow(db, ENTITY, {}, None)

    assert out["steps"][1]["approvers"][0]["employee_id"] == a.id


# ── CC không chặn, tách riêng danh sách ───────────────────────────────────────

def test_cc_khong_nam_trong_steps_nhung_co_trong_cc(db, seed, hai_nguoi_duyet):
    a, b = hai_nguoi_duyet
    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, node_kind=NODE_CC, approver_kind=APPROVER_EMPLOYEE,
         approver_ref=str(a.id))
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(b.id),
         skip_duplicate=SKIP_NONE)

    out = preview_service.preview_flow(db, ENTITY, {}, None)

    assert len(out["steps"]) == 1 and out["steps"][0]["approvers"][0]["employee_id"] == b.id
    assert len(out["cc"]) == 1 and out["cc"][0]["approvers"][0]["employee_id"] == a.id


# ── Bản clone chỉ lấy luồng pháp nhân ──────────────────────────────────────────

def test_ban_sao_chi_xet_luong_rieng_cua_phap_nhan(db, seed, hai_nguoi_duyet):
    a, b = hai_nguoi_duyet
    child = Company(code="CON", name="Công ty con", issue_code="CON",
                    level=2, is_active=True)
    db.add(child)
    db.commit()
    _bat_co(db)
    #  Luồng DÙNG CHUNG (không khai pháp nhân) — company_flow_only phải BỎ QUA nó.
    generic = _luong(db, code="VB-CHUNG")
    _buoc(db, generic, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id))

    only_generic = preview_service.preview_flow(
        db, ENTITY, {"company_id": child.id}, None, company_flow_only=True)
    assert only_generic["mode"] == "legacy", "Chỉ có luồng dùng chung — bản sao KHÔNG được rơi về nó"

    dedicated = _luong(db, code="VB-CON", company_id=child.id)
    _buoc(db, dedicated, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(b.id))

    with_dedicated = preview_service.preview_flow(
        db, ENTITY, {"company_id": child.id}, None, company_flow_only=True)
    assert with_dedicated["mode"] == "flow"
    assert with_dedicated["flow_name"] == "VB-CON" or with_dedicated["steps"][0]["approvers"][0]["employee_id"] == b.id


# ── Trùng thực tế khi gửi duyệt thật (bài kiểm quan trọng nhất) ───────────────

def test_xem_truoc_trung_voi_nguoi_duoc_giao_viec_khi_gui_duyet_that(db, seed, hai_nguoi_duyet):
    """`Thành công khi` của phase: xem trước xong gửi duyệt thật, người được
    giao việc ở TỪNG CHẶNG phải khớp đúng những gì đã xem trước."""
    a, b = hai_nguoi_duyet
    kind = _loai(db)
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Điều 1.</p>",
    ), ACTOR)

    _bat_co(db)
    flow = _luong(db)
    _buoc(db, flow, 1, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(a.id),
         skip_duplicate=SKIP_NONE)
    _buoc(db, flow, 2, approver_kind=APPROVER_EMPLOYEE, approver_ref=str(b.id),
         skip_duplicate=SKIP_NONE)

    #  Đúng bối cảnh + đúng thứ tự chọn "người nộp" mà `submit_for_approval`
    #  dùng thật — xem `approval_bridge.submit_for_approval`.
    subject = approval_bridge.entity_context(doc)
    submitter_id = doc.drafter_employee_id or doc.owner_employee_id
    preview = preview_service.preview_flow(db, ENTITY, subject, submitter_id)

    doc = service.submit(db, doc, ACTOR)
    instance = instance_service.running_instance(db, ENTITY, doc.id)
    pending_step1 = [row.assignee_employee_id for row in
                   instance_service.tasks_of_instance(db, instance.id)
                   if row.node_seq == 1]
    assert pending_step1 == [row["employee_id"] for row in preview["steps"][0]["approvers"]]

    action_service.approve(db, instance, a.id, ACTOR, subject)
    #  Chặng 1 đã duyệt xong, chặng 2 vừa mở việc — so đúng phần MỚI mở đó.
    pending_step2 = [row.assignee_employee_id for row in
                   instance_service.tasks_of_instance(db, instance.id)
                   if row.node_seq == 2]
    assert pending_step2 == [row["employee_id"] for row in preview["steps"][1]["approvers"]]
