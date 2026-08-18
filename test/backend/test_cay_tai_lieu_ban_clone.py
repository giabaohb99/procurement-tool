"""CÂY TÀI LIỆU phải thấy cả BẢN RIÊNG của các pháp nhân con (E06 + F06).

Clone nối với bản gốc bằng cột `Document.source_document_id`, KHÔNG đi qua bảng
quan hệ `tab_document_link`. Cây cũ chỉ duyệt bảng quan hệ nên bản gốc đã tách
thành mười hai bản ở mười hai pháp nhân mà cây vẫn hiện trống trơn — người mở
văn bản không có đường nào biết chuyện đó.

Bản riêng của các pháp nhân con thường TRÙNG TIÊU ĐỀ với bản gốc, nên mỗi dòng
phải kèm tên pháp nhân; thiếu nó thì cây hiện năm dòng giống hệt nhau.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import link_serializer, service
from app.modules.document.model import Document
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def canh(db, seed):
    """Một bản gốc ở pháp nhân mẹ + hai pháp nhân con."""
    me = db.get(Company, seed.company_id)
    me.issue_code = "DEGO"

    con_a = Company(name="Công ty con A", code="CON_A", is_active=True, parent=me.id)
    con_b = Company(name="Công ty con B", code="CON_B", is_active=True, parent=me.id)
    quy_che = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add_all([con_a, con_b, quy_che])
    db.commit()

    goc = service.create_document(db, DocumentCreate(
        doc_type_id=quy_che.id, company_id=me.id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế chi tiêu",
        content_html="<p>Nội dung</p>",
    ), ACTOR)
    db.commit()
    return {"goc": goc, "con_a": con_a, "con_b": con_b, "quy_che": quy_che, "seed": seed}


def _tao_ban_rieng(db, canh, company: Company, **thay_doi) -> Document:
    """Dựng thẳng bản clone: `clone_service.create` đòi bản gốc đã ban hành, mà
    bài này kiểm CÂY chứ không kiểm luật ban hành."""
    clone = Document(
        doc_type_id=canh["quy_che"].id, company_id=company.id,
        department_id=canh["seed"].dept_id, owner_employee_id=canh["seed"].emp_req_id,
        title=canh["goc"].title, source_document_id=canh["goc"].id,
        status=canh["goc"].status, origin=canh["goc"].origin,
        created_by=ACTOR, updated_by=ACTOR, **thay_doi,
    )
    db.add(clone)
    db.commit()
    return clone


def test_cay_hien_ban_rieng_cua_tung_phap_nhan_con(db, canh):
    _tao_ban_rieng(db, canh, canh["con_a"])
    _tao_ban_rieng(db, canh, canh["con_b"])

    cay = link_serializer.build_tree(db, canh["goc"])

    assert [con["company_name"] for con in cay["children"]] == [
        "Công ty con A",
        "Công ty con B",
    ]
    assert all(con["kind"] == "clone" for con in cay["children"])


def test_chua_clone_thi_cay_van_rong(db, canh):
    assert link_serializer.build_tree(db, canh["goc"])["children"] == []


def test_moi_dong_kem_ten_phap_nhan_du_tieu_de_trung_nhau(db, canh):
    #  Clone chép nguyên tiêu đề của gốc — không có tên pháp nhân thì hai dòng
    #  trên cây không phân biệt được với nhau.
    _tao_ban_rieng(db, canh, canh["con_a"])
    _tao_ban_rieng(db, canh, canh["con_b"])

    cay = link_serializer.build_tree(db, canh["goc"])
    tieu_de = {con["title"] for con in cay["children"]}
    ten_phap_nhan = {con["company_name"] for con in cay["children"]}

    assert len(tieu_de) == 1
    assert len(ten_phap_nhan) == 2


def test_ban_rieng_can_ra_lai_duoc_danh_dau_tren_cay(db, canh):
    #  Gốc lên phiên bản mới → clone `needs_review`. Đây đúng là câu hỏi
    #  "pháp nhân nào chưa cập nhật theo bản mới", phải thấy ngay trên cây.
    _tao_ban_rieng(db, canh, canh["con_a"], needs_review=True)

    con = link_serializer.build_tree(db, canh["goc"])["children"][0]

    assert con["is_outdated"] is True
    assert con["needs_review"] is True


def test_ban_rieng_co_kem_quan_he_van_hien_la_ban_rieng(db, canh):
    """Ca THẬT: `clone_service.create_clones` vừa tạo bản riêng vừa ghi một quan
    hệ «căn cứ theo» trỏ về gốc. Nhánh quan hệ nhặt trước thì bản riêng tụt
    xuống thành một dòng quan hệ thường — mất nhãn, mất tên pháp nhân, mất
    trạng thái xử lý. Đúng lỗi đã thấy trên dữ liệu chạy thật."""
    from app.modules.doc_catalog.link_rule_model import RELATION_BASED_ON
    from app.modules.document.link_model import DocumentLink

    clone = _tao_ban_rieng(db, canh, canh["con_a"])
    db.add(DocumentLink(source_document_id=clone.id, target_document_id=canh["goc"].id,
                        relation=RELATION_BASED_ON, is_system=True,
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    con = link_serializer.build_tree(db, canh["goc"])["children"]

    assert len(con) == 1
    assert con[0]["kind"] == "clone"
    assert con[0]["company_name"] == "Công ty con A"


def test_ban_goc_cung_kem_ten_phap_nhan(db, canh):
    assert link_serializer.build_tree(db, canh["goc"])["company_name"] == "Cty Test"
