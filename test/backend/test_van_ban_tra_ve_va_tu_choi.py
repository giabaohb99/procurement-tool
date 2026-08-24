"""TRẢ VỀ ≠ TỪ CHỐI ≠ RÚT PHIẾU (24/08/2026).

Trước đó cả ba nhịp kết thúc phiên duyệt đều gọi chung `service.reject()` và kéo
văn bản về **Nháp (1)**. Mở văn bản ra thì nó trông y như bản chưa từng gửi
duyệt: người soạn không biết nó vừa bị trả, mà lý do thì nằm trong `change_reason`
của phiên bản và dấu vết tab Phê duyệt — hai chỗ không ai mở khi chỉ liếc trạng
thái.

Bài kiểm ở đây canh bốn ranh giới dễ hỏng nhất:

1. **Bản 2.0 trở đi bị trả thì VĂN BẢN KHÔNG ĐỔI trạng thái.** Bản 1.0 vẫn đang
   có hiệu lực trong lúc bản 2.0 chờ duyệt (`van-thu/02` chỗ dễ sai số 7), nên
   kéo văn bản sang «Trả về» là cả công ty thấy quy chế biến mất. Lúc đó chỗ duy
   nhất nói được "bản 2.0 vừa bị trả" là chính dòng phiên bản.
2. **Bản bị trả về VẪN giữ `open_slot`.** Nhả chỗ là `submit()` không tìm thấy
   bản nào để gửi lại, mà giao diện thì vẫn bày nút *Gửi duyệt*.
3. **Bản bị từ chối thì NHẢ `open_slot`** — giữ chỗ là văn bản bị một phiên bản
   chết chặn vĩnh viễn, không mở nổi bản mới.
4. **Xóa được ở «Trả về», không xóa được ở «Đã từ chối»** (bản đã từ chối khóa
   hẳn; muốn làm lại thì *Sao chép*).

Gọi thẳng tầng dịch vụ, đúng như một người gọi thẳng API sẽ làm.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, version_service
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                        STATUS_REJECTED, STATUS_RETURNED,
                                        STATUS_SUBMITTED)
from app.modules.document.schema import (DocumentCreate, VersionContentUpdate,
                                         VersionCreate)
from app.modules.document.version_model import (CHANGE_MAJOR,
                                                VERSION_REJECTED,
                                                VERSION_RETURNED,
                                                DocumentVersion)

ACTOR = 1


@pytest.fixture()
def doc(db, seed):
    """Một quy chế còn NHÁP, chưa gửi duyệt."""
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        content_html="<p>Bản 1</p>",
    ), ACTOR)


def _ban_dang_mo(db, doc) -> DocumentVersion | None:
    return service.open_version(db, doc)


# ── Bản ĐẦU TIÊN: văn bản đi theo phiên bản ──────────────────────────────────
def test_tra_ve_ban_dau_thi_van_ban_sang_tra_ve(db, doc):
    service.submit(db, doc, ACTOR)
    service.tra_lai(db, doc, "Thiếu căn cứ ở mục 2", ACTOR)

    assert doc.status == STATUS_RETURNED
    ban = _ban_dang_mo(db, doc)
    assert ban is not None, "Bản bị trả về phải còn đang mở để sửa tiếp"
    assert ban.status == VERSION_RETURNED
    assert "[Trả về] Thiếu căn cứ ở mục 2" in ban.change_reason


def test_tu_choi_ban_dau_thi_van_ban_sang_da_tu_choi(db, doc):
    service.submit(db, doc, ACTOR)
    service.tu_choi(db, doc, "Không duyệt nhu cầu này", ACTOR)

    assert doc.status == STATUS_REJECTED
    assert _ban_dang_mo(db, doc) is None, "Bản bị từ chối phải nhả open_slot"
    ban = db.get(DocumentVersion, doc.current_version_id)
    assert ban.status == VERSION_REJECTED
    assert "[Từ chối] Không duyệt nhu cầu này" in ban.change_reason


def test_rut_phieu_thi_ve_nhap_chu_khong_phai_bi_tra(db, doc):
    """Người nộp tự rút thì không ai trả gì cho ai — đừng treo lên phiếu chữ «Trả về»."""
    service.submit(db, doc, ACTOR)
    service.rut_phieu(db, doc, "Gửi sớm quá, cần bổ sung phụ lục", ACTOR)

    assert doc.status == STATUS_DRAFT
    ban = _ban_dang_mo(db, doc)
    assert ban is not None
    assert "[Rút phiếu]" in ban.change_reason


def test_tra_ve_roi_gui_duyet_lai_duoc_ngay(db, doc):
    """Cả mục đích của trạng thái «Trả về»: sửa xong gửi lại trên chính văn bản đó."""
    service.submit(db, doc, ACTOR)
    service.tra_lai(db, doc, "Sửa lại mục 2", ACTOR)

    version_service.save_content(
        db, _ban_dang_mo(db, doc),
        VersionContentUpdate(content_html="<p>Bản 1 đã sửa theo góp ý.</p>"), ACTOR)
    service.submit(db, doc, ACTOR)

    assert doc.status == STATUS_SUBMITTED
    assert _ban_dang_mo(db, doc).content_html == "<p>Bản 1 đã sửa theo góp ý.</p>"


def test_tu_choi_roi_khong_gui_duyet_lai_duoc(db, doc):
    service.submit(db, doc, ACTOR)
    service.tu_choi(db, doc, "Không duyệt", ACTOR)

    with pytest.raises(HTTPException) as loi:
        service.submit(db, doc, ACTOR)
    assert loi.value.status_code == 400
    assert "Sao chép" in loi.value.detail, "Phải chỉ ra đường ra, không chỉ báo lỗi"


# ── Bản 2.0 trở đi: VĂN BẢN GIỮ NGUYÊN ───────────────────────────────────────
def _len_ban_hai(db, doc) -> DocumentVersion:
    """Ban hành bản 1.0 rồi mở bản 2.0 và gửi duyệt bản đó."""
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    assert doc.status == STATUS_EFFECTIVE

    ban_hai = version_service.open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa chương II",
        change_reason="Đổi hạn mức phê duyệt",
    ), ACTOR)
    version_service.save_content(
        db, ban_hai, VersionContentUpdate(content_html="<p>Bản 2</p>"), ACTOR)
    service.submit(db, doc, ACTOR)
    return ban_hai


def test_tra_ve_ban_hai_thi_van_ban_van_co_hieu_luc(db, doc):
    """Chỗ dễ sai số 7 của `van-thu/02` — kéo văn bản đi theo là quy chế biến mất."""
    _len_ban_hai(db, doc)
    assert doc.status == STATUS_EFFECTIVE, "Gửi duyệt bản 2.0 không được đổi trạng thái văn bản"

    service.tra_lai(db, doc, "Chương II chưa khớp quy định mới", ACTOR)

    assert doc.status == STATUS_EFFECTIVE
    ban = _ban_dang_mo(db, doc)
    assert ban.status == VERSION_RETURNED, "Chỗ duy nhất nói được bản 2.0 vừa bị trả"
    assert (ban.major, ban.minor) == (2, 0)


def test_tu_choi_ban_hai_thi_van_ban_van_co_hieu_luc(db, doc):
    _len_ban_hai(db, doc)
    service.tu_choi(db, doc, "Không cần sửa nữa", ACTOR)

    assert doc.status == STATUS_EFFECTIVE
    assert _ban_dang_mo(db, doc) is None, "Bản 2.0 bị từ chối phải nhả chỗ cho bản khác"
    #  Và mở được bản mới — đây chính là lý do «Đã từ chối» không nằm trong OPEN_STATUSES.
    version_service.open_new_version(db, doc, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Làm lại chương II",
        change_reason="Bản trước bị từ chối",
    ), ACTOR)


# ── Xóa ──────────────────────────────────────────────────────────────────────
def test_xoa_duoc_van_ban_bi_tra_ve(db, doc):
    service.submit(db, doc, ACTOR)
    service.tra_lai(db, doc, "Thôi khỏi làm nữa", ACTOR)

    service.delete_document(db, doc)   # không ném lỗi là đủ


def test_khong_xoa_duoc_van_ban_da_tu_choi(db, doc):
    service.submit(db, doc, ACTOR)
    service.tu_choi(db, doc, "Không duyệt", ACTOR)

    with pytest.raises(HTTPException) as loi:
        service.delete_document(db, doc)
    assert loi.value.status_code == 400


def test_khong_co_ban_nao_dang_cho_duyet_thi_khong_tra_ve_duoc(db, doc):
    """Bấm trả về hai lần, hoặc trả về một văn bản còn nháp — phải chặn."""
    with pytest.raises(HTTPException) as loi:
        service.tra_lai(db, doc, "sao cũng được", ACTOR)
    assert loi.value.status_code == 400


def test_xoa_van_ban_thi_don_luon_phieu_duyet(db, doc):
    """L-04 — xóa chứng từ mà để phiếu duyệt nằm lại là đẻ rác trỏ vào hư không.

    Dựng lại được 24/08/2026 trên đường HỢP LỆ: văn bản ở «Trả về» thì gần như
    luôn có một phiếu duyệt đã đóng, mà luật lại cho xóa văn bản ở trạng thái đó.
    """
    from app.modules.approval.instance_model import (ApprovalAction,
                                                     ApprovalInstance,
                                                     ApprovalTask)

    #  Dựng tay một phiếu duyệt đã đóng gắn vào văn bản — đúng thứ còn lại sau
    #  một lần bị trả về. Không chạy cả bộ máy duyệt ở đây: bài này hỏi *xóa có
    #  dọn không*, không hỏi *bộ máy chạy đúng không*.
    phien = ApprovalInstance(entity="document", entity_id=doc.id, flow_id=1,
                             status=4, current_seq=1, created_by=ACTOR, updated_by=ACTOR)
    db.add(phien)
    db.flush()
    db.add(ApprovalTask(instance_id=phien.id, node_seq=1, order_no=1,
                        assignee_employee_id=1, status=6,
                        created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalAction(instance_id=phien.id, node_seq=1, action=1,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    #  Nhớ id TRƯỚC khi xóa: sau đó hai đối tượng ORM này không còn hàng để nạp.
    doc_id, phien_id = doc.id, phien.id

    service.delete_document(db, doc)

    con_phien = db.query(ApprovalInstance).filter(
        ApprovalInstance.entity == "document", ApprovalInstance.entity_id == doc_id).count()
    con_viec = db.query(ApprovalTask).filter(ApprovalTask.instance_id == phien_id).count()
    con_vet = db.query(ApprovalAction).filter(ApprovalAction.instance_id == phien_id).count()
    assert (con_phien, con_viec, con_vet) == (0, 0, 0), "Xóa văn bản phải dọn sạch phiếu duyệt"


def test_xoa_van_ban_thi_don_luon_QUAN_HE(db, doc):
    """Xóa chứng từ mà để quan hệ nằm lại là đẻ dòng trỏ vào chỗ trống.

    Tìm ra khi soi dữ liệu dev 24/08/2026: hai dòng quan hệ mồ côi có từ 19/08 và
    21/08. Văn bản còn sống mở tab «Quan hệ» ra thì thấy một dòng *Có kèm theo*
    trỏ vào `document: null` — không biết nó từng là gì, cũng không bấm đi đâu được.
    """
    from app.modules.doc_catalog.link_rule_model import RELATION_REFERENCE
    from app.modules.document.link_model import DocumentLink

    khac = service.create_document(db, DocumentCreate(
        doc_type_id=doc.doc_type_id, company_id=doc.company_id,
        department_id=doc.department_id, owner_employee_id=doc.owner_employee_id,
        title="Văn bản còn sống", content_html="<p>x</p>"), ACTOR)
    #  Hai chiều: văn bản sắp xóa vừa là nguồn vừa là đích của một quan hệ.
    db.add(DocumentLink(source_document_id=doc.id, target_document_id=khac.id,
                        relation=RELATION_REFERENCE, created_by=ACTOR, updated_by=ACTOR))
    db.add(DocumentLink(source_document_id=khac.id, target_document_id=doc.id,
                        relation=RELATION_REFERENCE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    doc_id = doc.id

    service.delete_document(db, doc)

    con = (db.query(DocumentLink)
           .filter((DocumentLink.source_document_id == doc_id)
                   | (DocumentLink.target_document_id == doc_id)).count())
    assert con == 0, "Xóa văn bản phải dọn quan hệ CẢ HAI CHIỀU"

