"""ĐANG CHẠY TRONG LUỒNG THÌ KHÔNG CÓ ĐƯỜNG TẮT — và hỏng thì phải nói ra.

Hai lỗi thật, bắt được khi chạy thử trên dữ liệu mẫu ngày 18/08/2026:

1. **Đi tắt.** Văn bản đang ở chặng 1 chờ trưởng bộ phận ký, một người có quyền
   `document.approve` bấm nút «Duyệt và ban hành» của luồng một bước cũ: văn bản
   được cấp số và chuyển hiệu lực ngay, còn phiên duyệt thì vẫn thản nhiên chạy
   tiếp trên một văn bản đã ban hành. Ba chữ ký còn lại trở thành vô nghĩa.
   Nút «Trả lại» cũ cũng vậy — kéo văn bản về nháp giữa lúc phiên đang chạy.

2. **Hỏng trong im lặng.** `entity_hooks.fire` nuốt lỗi có chủ ý để không làm
   mất chữ ký vừa đặt. Nhưng nuốt lỗi thành ra giấu lỗi: phiên ghi «Đã duyệt»,
   văn bản nằm lại ở *chờ duyệt* không số, và lý do chỉ nằm trong log container.
"""
import pytest

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import INSTANCE_APPROVED
from app.modules.doc_catalog.link_rule_model import RELATION_ATTACHED
from app.modules.doc_catalog.model import DocType
from app.modules.document import approval_bridge, service
from app.modules.document.model import (STATUS_EFFECTIVE, STATUS_SUBMITTED,
                                        Document)
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee
from fastapi import HTTPException

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def align(db, seed):
    """Một quy chế đang chạy trong luồng hai bước."""
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.flush()

    person = {}
    for name in ("a", "b"):
        employee = Employee(code=f"DUYET_{name.upper()}", full_name=f"Người duyệt {name.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        person[name] = employee.id

    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt quy chế",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    for seq, name in ((1, "a"), (2, "b")):
        db.add(ApprovalNode(flow_id=flow.id, seq=seq, name=f"Bước {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(person[name]),
                            skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)
    doc = service.submit(db, doc, ACTOR)
    return {"doc": doc, "nguoi": person, "doc_type": doc_type,
            "phien": instance_service.running_instance(db, ENTITY, doc.id)}


# ── 1 · không có đường tắt ──────────────────────────────────────────────────

def test_dang_o_chang_1_thi_khong_ban_hanh_thang_duoc(db, align):
    with pytest.raises(HTTPException) as error:
        approval_bridge.block_legacy_path(db, align["doc"])

    assert error.value.status_code == 400
    assert "luồng duyệt nhiều bước" in error.value.detail
    #  Và văn bản đứng nguyên chỗ cũ, không số.
    db.refresh(align["doc"])
    assert align["doc"].status == STATUS_SUBMITTED
    assert not align["doc"].doc_code


def test_duyet_xong_het_cac_buoc_thi_chot_mo_ra(db, align):
    """Chốt chỉ chặn lúc phiên CÒN MỞ — hết phiên thì đường cũ dùng lại được.

    Quan trọng vì chính bộ máy nhiều bước gọi `service.approve()` khi duyệt hết
    bước: chặn nhầm ở đó là không văn bản nào ban hành nổi.
    """
    action_service.approve(db, align["phien"], align["nguoi"]["a"], ACTOR, {})
    action_service.approve(db, align["phien"], align["nguoi"]["b"], ACTOR, {})
    assert align["phien"].status == INSTANCE_APPROVED

    db.refresh(align["doc"])
    approval_bridge.block_legacy_path(db, align["doc"])   # không được ném lỗi
    assert align["doc"].status == STATUS_EFFECTIVE


def test_chua_vao_bo_may_thi_khong_chan_gi(db, seed):
    """Văn bản chưa từng trình duyệt thì đường một bước cũ vẫn là đường chính."""
    doc_type = DocType(code="TB", name="Thông báo", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.flush()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Thông báo nghỉ lễ",
        content_html="<p>Nội dung.</p>",
    ), ACTOR)

    approval_bridge.block_legacy_path(db, doc)   # không được ném lỗi


def test_thieu_phong_chu_tri_thi_chan_ngay_luc_tao(db, seed):
    """Bước đầu luồng hỏi trưởng bộ phận CỦA PHÒNG CHỦ TRÌ.

    Không có phòng thì phiên duyệt chốt ở trạng thái KẸT ngay khi vừa gửi, và
    văn bản không đi tiếp được bằng đường nào — chặn từ lúc tạo rẻ hơn nhiều.
    """
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DocumentCreate(doc_type_id=1, company_id=seed.company_id,
                       owner_employee_id=seed.emp_req_id, title="Thiếu phòng")


# ── 1b · rút phiếu thì văn bản phải VỀ NHÁP ─────────────────────────────────

def test_rut_phieu_thi_van_ban_ve_nhap_va_khong_con_duong_tat(db, align):
    """Ca thật bắt được 19/08/2026.

    Trước đây rút phiếu chỉ đóng phiên duyệt, văn bản nằm lại ở *đang duyệt*:
    gửi duyệt lại không được (đường gửi chỉ nhận bản nháp), mà chốt chặn thì mở
    ra vì phiên hết chạy — thành ra ban hành thẳng được một văn bản không ai ký.
    """
    from app.modules.document.model import STATUS_DRAFT

    action_service.withdraw(db, align["phien"], align["doc"].owner_employee_id,
                           ACTOR, "gửi nhầm bản")

    db.refresh(align["doc"])
    assert align["doc"].status == STATUS_DRAFT
    assert not align["doc"].doc_code

    #  Về nháp thì không còn bản nào "đang chờ duyệt" để mà ban hành thẳng.
    with pytest.raises(HTTPException):
        service.approve(db, align["doc"], ACTOR)

    #  Và gửi duyệt lại được — đây là đường đi tiếp đúng.
    service.submit(db, align["doc"], ACTOR)
    assert align["doc"].status == STATUS_SUBMITTED


# ── 2 · hỏng thì phải nói ra ────────────────────────────────────────────────

def test_duyet_xong_ma_khong_ban_hanh_duoc_thi_ghi_ly_do_vao_phien(db, align):
    """Ca thật: loại «phải kèm Quyết định» mà thiếu Quyết định.

    Phiên vẫn ghi «Đã duyệt» — chữ ký là chữ ký, không xóa đi được. Nhưng lý do
    văn bản chưa ban hành phải nằm ở chỗ người dùng đọc được, không phải chỉ ở
    log container.
    """
    align["doc_type"].needs_decision = True
    db.commit()

    action_service.approve(db, align["phien"], align["nguoi"]["a"], ACTOR, {})
    action_service.approve(db, align["phien"], align["nguoi"]["b"], ACTOR, {})

    assert align["phien"].status == INSTANCE_APPROVED
    db.refresh(align["doc"])
    assert align["doc"].status == STATUS_SUBMITTED, "Thiếu Quyết định thì không ban hành"
    assert align["phien"].finish_reason, "Hỏng mà không ghi lý do là hỏng trong im lặng"
    assert "Quyết định" in align["phien"].finish_reason


def test_ban_hanh_tron_ven_thi_khong_de_lai_ly_do_hong(db, align):
    action_service.approve(db, align["phien"], align["nguoi"]["a"], ACTOR, {})
    action_service.approve(db, align["phien"], align["nguoi"]["b"], ACTOR, {})

    db.refresh(align["doc"])
    assert align["doc"].status == STATUS_EFFECTIVE
    assert not align["phien"].finish_reason


# ── 3 · loại cần Quyết định phải khai được quan hệ đó ───────────────────────

def test_moi_loai_can_quyet_dinh_deu_khai_duoc_quan_he_kem_theo():
    """Bảng quy tắc quan hệ phải theo kịp cờ `needs_decision` của danh mục loại.

    Lỗi đã xảy ra: Chính sách · Quy định · Quy trình đều bật `needs_decision`
    nhưng không có dòng quy tắc «Kèm theo» tới Quyết định. Hệ quả là khóa chết —
    `ensure_can_issue` đòi Quyết định, còn bảng quy tắc thì cấm khai quan hệ đó,
    nên ba loại này không còn đường nào ban hành được.
    """
    from app.seed_data.document_phase1 import (ALL_DOC_TYPES,
                                               DOC_TYPE_LINK_RULES)

    khai_duoc = {ma_nguon for ma_nguon, relation, ma_dich, *_ in DOC_TYPE_LINK_RULES
                 if relation == RELATION_ATTACHED and ma_dich == "QD"}
    needs_decision = {kind["code"] for kind in ALL_DOC_TYPES if kind.get("needs_decision")}

    assert needs_decision, "Bộ danh mục mẫu phải còn ít nhất một loại cần Quyết định"
    assert not (needs_decision - khai_duoc), (
        "Loại cần Quyết định mà không khai được quan hệ «Kèm theo» tới Quyết định: "
        f"{sorted(needs_decision - khai_duoc)}"
    )
