"""DANH SÁCH VĂN BẢN gom BẢN RIÊNG vào dưới bản gốc.

Một văn bản clone cho mười hai pháp nhân sinh ra mười hai bản ghi mang **cùng
tiêu đề**. Để chúng đứng ngang hàng bản gốc thì danh sách thành mười ba dòng gần
như giống hệt nhau, và người đọc không đếm nổi có bao nhiêu văn bản thật.

Nhưng chỉ được giấu khi người đang xem THẤY ĐƯỢC bản gốc: người ở pháp nhân con
không xem được bản gốc thì bản riêng chính là văn bản của họ — giấu đi là danh
sách của họ trống trơn. Hai vế đó là hai bài đầu tiên dưới đây.
"""
import pytest

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service
from app.modules.document.model import Document
from app.modules.document.query import (an_ban_rieng_co_goc_xem_duoc,
                                        dem_ban_rieng, documents_query)
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def canh(db, seed):
    """Một bản gốc ở pháp nhân mẹ + một bản riêng ở công ty con."""
    me = db.get(Company, seed.company_id)
    me.issue_code = "DEGO"
    con = Company(name="Công ty con A", code="CON_A", is_active=True, parent=me.id)
    loai = DocType(code="TB", name="Thông báo", id_scheme=1, number_when=2)
    db.add_all([con, loai])
    db.commit()

    goc = service.create_document(db, DocumentCreate(
        doc_type_id=loai.id, company_id=me.id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Thông báo chung",
        content_html="<p>Nội dung</p>",
    ), ACTOR)
    db.commit()

    clone = Document(
        doc_type_id=loai.id, company_id=con.id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title=goc.title,
        source_document_id=goc.id, status=goc.status, origin=goc.origin,
        created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(clone)
    db.commit()
    return {"goc": goc, "clone": clone, "con": con, "loai": loai, "seed": seed}


def test_thay_ban_goc_thi_ban_rieng_khong_dung_ngang_hang(db, canh):
    ids = [row.id for row in an_ban_rieng_co_goc_xem_duoc(documents_query(db)).all()]

    assert canh["goc"].id in ids
    assert canh["clone"].id not in ids


def test_khong_thay_ban_goc_thi_ban_rieng_van_hien_nhu_van_ban_thuong(db, canh):
    #  Đúng cảnh người ở pháp nhân con: quyền của họ chỉ tới công ty con, bản
    #  gốc nằm ngoài tầm nhìn. Giấu bản riêng ở đây là xóa trắng danh sách của
    #  họ — lỗi nặng hơn hẳn việc danh sách hơi dài.
    chi_cong_ty_con = documents_query(db).filter(Document.company_id == canh["con"].id)

    ids = [row.id for row in an_ban_rieng_co_goc_xem_duoc(chi_cong_ty_con).all()]

    assert ids == [canh["clone"].id]


def test_dem_dung_so_ban_rieng_cua_tung_van_ban(db, canh):
    assert dem_ban_rieng(documents_query(db), [canh["goc"].id]) == {canh["goc"].id: 1}


def test_khong_dem_ban_rieng_nam_ngoai_tam_nhin(db, canh):
    #  Người ở pháp nhân mẹ không xem được văn bản của công ty con thì con số
    #  phải là 0 — nếu không giao diện bày mũi tên bung ra một danh sách rỗng.
    chi_phap_nhan_me = documents_query(db).filter(
        Document.company_id == canh["goc"].company_id)

    assert dem_ban_rieng(chi_phap_nhan_me, [canh["goc"].id]) == {}


def test_van_ban_khong_co_ban_rieng_thi_khong_co_trong_bang_dem(db, canh):
    them = service.create_document(db, DocumentCreate(
        doc_type_id=canh["loai"].id, company_id=canh["seed"].company_id,
        department_id=canh["seed"].dept_id, owner_employee_id=canh["seed"].emp_req_id,
        title="Thông báo lẻ", content_html="<p>x</p>",
    ), ACTOR)
    db.commit()

    assert dem_ban_rieng(documents_query(db), [them.id]) == {}


def test_danh_sach_rong_thi_khong_chay_truy_van_nao(db):
    assert dem_ban_rieng(documents_query(db), []) == {}
