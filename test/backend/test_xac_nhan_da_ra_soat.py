"""XÁC NHẬN ĐÃ RÀ SOÁT — tắt cờ «cần rà lại» (19/08/2026).

Lỗ hổng bắt được khi người dùng hỏi "rà thì vào đâu": trong mã có **năm chỗ bật
cờ** (bản gốc lên phiên bản mới · cha bị bãi bỏ · cha lên bản mới · hai luật của
bản trích) mà **không chỗ nào tắt**. Rà xong, sửa xong, ban hành xong thì băng
vàng vẫn treo vĩnh viễn — vài tháng là văn bản nào cũng đeo băng và không ai còn
để ý tới nó nữa.
"""
import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import service
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    obj = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        content_html="<p>x</p>",
    ), ACTOR)
    obj.needs_review = True
    obj.needs_review_note = "Bản gốc đã lên bản 2.0"
    db.commit()
    return obj


def test_xac_nhan_thi_tat_co_va_xoa_ghi_chu(db, doc):
    service.xac_nhan_da_ra_soat(db, doc, "Đã đối chiếu, vẫn đúng", ACTOR)

    assert doc.needs_review is False
    assert doc.needs_review_note == ""


def test_khong_co_dau_thi_khong_xac_nhan_duoc(db, doc):
    """Bấm hai lần, hoặc bấm trên văn bản không có dấu — phải báo rõ, không im lặng."""
    service.xac_nhan_da_ra_soat(db, doc, "lần một", ACTOR)

    with pytest.raises(HTTPException) as loi:
        service.xac_nhan_da_ra_soat(db, doc, "lần hai", ACTOR)

    assert loi.value.status_code == 400


def test_xac_nhan_khong_dung_toi_noi_dung_hay_trang_thai(db, doc):
    """Rà soát là việc ĐỌC — không được đổi trạng thái hay nội dung văn bản."""
    trang_thai = doc.status
    tieu_de = doc.title

    service.xac_nhan_da_ra_soat(db, doc, "Đã đối chiếu", ACTOR)

    assert doc.status == trang_thai
    assert doc.title == tieu_de


def test_ket_luan_qua_ngan_bi_chan_o_schema(db):
    """Bấm cho xong thì không ghi được gì có ích vào nhật ký."""
    from app.modules.document.schema import ReviewedIn

    with pytest.raises(ValueError):
        ReviewedIn(ket_luan="ok"[:2])

    #  Ba ký tự trở lên thì nhận.
    assert ReviewedIn(ket_luan="Đã rà").ket_luan == "Đã rà"


def test_ket_luan_qua_dai_cung_bi_chan(db):
    from app.modules.document.schema import ReviewedIn

    with pytest.raises(ValueError):
        ReviewedIn(ket_luan="x" * 301)
