"""NỐI VĂN BẢN VÀO BỘ MÁY DUYỆT DÙNG CHUNG (task CHUYỂN của phase 3).

Ba câu phải trả lời được, và đúng theo thứ tự này:

1. **Cờ TẮT thì không có gì đổi.** Đây là điều kiện số một của cam kết "không
   ảnh hưởng thứ đang chạy": thêm bảng, thêm mã, nhưng hành vi y hệt hôm qua.
2. **Cờ BẬT mà chưa khai luồng cũng không đổi gì** — không có khe nào để văn bản
   rơi vào khoảng không giữa hai bộ máy.
3. Cờ BẬT và có luồng thì phiếu chạy nhiều bước, và **duyệt xong là văn bản
   được ban hành thật** (cấp số, khóa phiên bản), chứ không chỉ đổi một con số
   trạng thái ở bảng phiên duyệt.
"""
import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_RUNNING,
                                                 TASK_PENDING)
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                        STATUS_SUBMITTED, Document)
from app.modules.document.schema import DocumentCreate
from app.modules.document.version_model import VERSION_DRAFT, VERSION_SUBMITTED
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def canh(db, seed):
    """Một quy chế còn nháp + hai người duyệt."""
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.flush()

    nguoi = {}
    for ten in ("a", "b"):
        employee = Employee(code=f"BM_{ten.upper()}", full_name=f"Người duyệt {ten.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        nguoi[ten] = employee.id
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Điều 1. Nội dung.</p>",
    ), ACTOR)
    return {"doc": doc, "nguoi": nguoi, "doc_type": doc_type, "seed": seed}


def _bat_co(db):
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()


def _luong_hai_buoc(db, nguoi):
    flow = ApprovalFlow(entity=ENTITY, code="VB-01", name="Duyệt quy chế",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    for seq, ten in ((1, "a"), (2, "b")):
        db.add(ApprovalNode(flow_id=flow.id, seq=seq, name=f"Bước {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(nguoi[ten]),
                            skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow


def _luong_mot_buoc(db, code, name, company_id, employee_id):
    flow = ApprovalFlow(
        entity=ENTITY, code=code, name=name, company_id=company_id,
        is_active=True, created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(
        flow_id=flow.id, seq=1, name="Ban hành",
        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(employee_id),
        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR,
    ))
    db.commit()
    return flow


# ── 1 · cờ tắt thì không có gì đổi ─────────────────────────────────────────

def test_co_tat_thi_gui_duyet_chay_y_nhu_cu(db, canh):
    """Điều kiện số một của cam kết «không ảnh hưởng thứ đang chạy»."""
    doc = service.submit(db, canh["doc"], ACTOR)

    assert doc.status == STATUS_SUBMITTED
    assert service.open_version(db, doc).status == VERSION_SUBMITTED
    #  Không phiên duyệt nào được mở ra.
    assert instance_service.phien_dang_chay(db, ENTITY, doc.id) is None


def test_co_tat_thi_van_duyet_bang_nut_cu(db, canh):
    doc = service.submit(db, canh["doc"], ACTOR)
    doc = service.approve(db, doc, ACTOR)
    assert doc.status == STATUS_EFFECTIVE


# ── 2 · bật cờ nhưng chưa khai luồng ───────────────────────────────────────

def test_bat_co_ma_chua_khai_luong_thi_van_chay_duong_cu(db, canh):
    """Không có khe nào để văn bản rơi vào khoảng không giữa hai bộ máy."""
    _bat_co(db)

    doc = service.submit(db, canh["doc"], ACTOR)

    assert doc.status == STATUS_SUBMITTED
    assert instance_service.phien_dang_chay(db, ENTITY, doc.id) is None
    #  Và nút duyệt cũ vẫn ban hành được.
    assert service.approve(db, doc, ACTOR).status == STATUS_EFFECTIVE


# ── 3 · bật cờ và có luồng ─────────────────────────────────────────────────

def test_bat_co_va_co_luong_thi_mo_phien_nhieu_buoc(db, canh):
    _bat_co(db)
    _luong_hai_buoc(db, canh["nguoi"])

    doc = service.submit(db, canh["doc"], ACTOR)

    phien = instance_service.phien_dang_chay(db, ENTITY, doc.id)
    assert phien is not None
    assert phien.status == INSTANCE_RUNNING
    #  Nhãn phải sẵn trên phiên để màn «Việc của tôi» khỏi nạp bảng văn bản.
    assert phien.entity_title == "Quy chế bảo mật"

    dang_cho = [row for row in instance_service.viec_cua_phien(db, phien.id)
                if row.status == TASK_PENDING]
    assert [row.assignee_employee_id for row in dang_cho] == [canh["nguoi"]["a"]]


def test_ban_goc_va_clone_mo_hai_luong_rieng_theo_phap_nhan(db, canh):
    """Clone là văn bản của nơi nhận: phiên và người duyệt không dính bản gốc."""
    child = Company(code="CON", name="Công ty con", issue_code="CON",
                    level=2, is_active=True)
    db.add(child)
    db.flush()
    child_approver = Employee(
        code="DUYET_CON", full_name="Người duyệt công ty con",
        company_id=child.id, department_id=canh["seed"].dept_id, is_active=True,
    )
    db.add(child_approver)
    db.commit()

    clone = service.create_document(db, DocumentCreate(
        doc_type_id=canh["doc_type"].id,
        company_id=child.id,
        department_id=canh["seed"].dept_id,
        owner_employee_id=canh["seed"].emp_req_id,
        title="Quy chế bảo mật — bản công ty con",
        content_html="<p>Nội dung riêng.</p>",
    ), ACTOR)
    clone.source_document_id = canh["doc"].id
    db.commit()

    _bat_co(db)
    root_flow = _luong_mot_buoc(
        db, "VB-ME", "Luồng pháp nhân gốc", canh["seed"].company_id,
        canh["nguoi"]["a"],
    )
    child_flow = _luong_mot_buoc(
        db, "VB-CON", "Luồng pháp nhân con", child.id, child_approver.id,
    )

    service.submit(db, canh["doc"], ACTOR)
    service.submit(db, clone, ACTOR)
    root_instance = instance_service.phien_dang_chay(db, ENTITY, canh["doc"].id)
    child_instance = instance_service.phien_dang_chay(db, ENTITY, clone.id)

    assert root_instance.flow_id == root_flow.id
    assert child_instance.flow_id == child_flow.id
    assert root_instance.id != child_instance.id
    assert [row.assignee_employee_id for row in instance_service.viec_cua_phien(
        db, root_instance.id) if row.status == TASK_PENDING] == [canh["nguoi"]["a"]]
    assert [row.assignee_employee_id for row in instance_service.viec_cua_phien(
        db, child_instance.id) if row.status == TASK_PENDING] == [child_approver.id]


def test_clone_thieu_luong_rieng_bi_chan_truoc_khi_doi_trang_thai(db, canh):
    child = Company(code="CON", name="Công ty con", issue_code="CON",
                    level=2, is_active=True)
    db.add(child)
    db.commit()
    clone = service.create_document(db, DocumentCreate(
        doc_type_id=canh["doc_type"].id,
        company_id=child.id,
        department_id=canh["seed"].dept_id,
        owner_employee_id=canh["seed"].emp_req_id,
        title="Quy chế của công ty con",
        content_html="<p>Nội dung riêng.</p>",
    ), ACTOR)
    clone.source_document_id = canh["doc"].id
    db.commit()

    _bat_co(db)
    #  Chỉ có luồng dùng chung: bản gốc dùng được, clone thì không được phép
    #  rơi vào đây vì pháp nhân con phải có đường ký riêng của mình.
    _luong_hai_buoc(db, canh["nguoi"])

    with pytest.raises(HTTPException) as error:
        service.submit(db, clone, ACTOR)

    assert error.value.status_code == 400
    assert "chưa có luồng duyệt Văn bản riêng" in str(error.value)
    db.refresh(clone)
    assert clone.status == STATUS_DRAFT
    assert service.open_version(db, clone).status == VERSION_DRAFT
    assert instance_service.phien_dang_chay(db, ENTITY, clone.id) is None


def test_duyet_het_cac_buoc_thi_van_ban_duoc_BAN_HANH_that(db, canh):
    """Câu quan trọng nhất của cả task CHUYỂN.

    Phiên duyệt xong mà văn bản không được cấp số, không khóa phiên bản, thì bộ
    máy mới chỉ là một bảng ghi trạng thái nằm cạnh — người dùng vẫn phải bấm
    nút cũ, và không ai hiểu vì sao có hai chỗ phải bấm.
    """
    _bat_co(db)
    _luong_hai_buoc(db, canh["nguoi"])
    doc = service.submit(db, canh["doc"], ACTOR)
    phien = instance_service.phien_dang_chay(db, ENTITY, doc.id)

    action_service.duyet(db, phien, canh["nguoi"]["a"], ACTOR, {})
    db.refresh(doc)
    assert doc.status == STATUS_SUBMITTED, "Mới một chữ ký thì chưa ban hành"

    action_service.duyet(db, phien, canh["nguoi"]["b"], ACTOR, {})

    assert phien.status == INSTANCE_APPROVED
    db.refresh(doc)
    assert doc.status == STATUS_EFFECTIVE
    #  Ban hành THẬT: có số hiệu và phiên bản đã khóa.
    assert (doc.doc_code or doc.issue_number), "Ban hành mà không cấp số là chưa ban hành"
    assert service.open_version(db, doc) is None, "Phiên bản phải bị khóa sau khi ban hành"


def test_tu_choi_thi_van_ban_ve_lai_ban_nhap_sua_duoc(db, canh):
    _bat_co(db)
    _luong_hai_buoc(db, canh["nguoi"])
    doc = service.submit(db, canh["doc"], ACTOR)
    phien = instance_service.phien_dang_chay(db, ENTITY, doc.id)

    action_service.tu_choi(db, phien, canh["nguoi"]["a"], ACTOR, "Thiếu căn cứ pháp lý")

    db.refresh(doc)
    assert doc.status == STATUS_DRAFT
    #  Bản nháp phải mở lại được để người soạn sửa tiếp.
    version = service.open_version(db, doc)
    assert version is not None
    assert "Thiếu căn cứ pháp lý" in version.change_reason
