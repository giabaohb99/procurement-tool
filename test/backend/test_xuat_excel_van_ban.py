"""XUẤT EXCEL danh sách văn bản.

Bài đáng giá nhất ở đây là `test_moi_cot_deu_co_du_lieu_that`: bộ cột khai bằng
CHUỖI khóa, còn dữ liệu do `serializer.serialize_many` dựng — đổi tên một khóa
bên serializer thì cột tương ứng lặng lẽ rỗng trong file Excel, không lỗi, không
ai biết cho tới lúc người nhận file hỏi "sao cột này trống".
"""
import pytest

from app.core.export_xlsx import Col, pick_columns
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import export as ex
from app.modules.document import serializer, service
from app.modules.document.model import Document
from app.modules.document.query import documents_query
from app.modules.document.schema import DocumentCreate

ACTOR = 1


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế thử",
        secrecy_level=3, urgency=2, content_html="<p>x</p>",
    ), ACTOR)


def _dong(db, doc) -> dict:
    return ex.build_rows(db, serializer.serialize_many(db, [doc]))[0]


def test_muc_mat_va_do_khan_ra_chu_khong_ra_so(db, doc):
    """Trên màn hình chúng hiện bằng badge màu; đổ số 3, 2 vào Excel thì vô nghĩa."""
    row = _dong(db, doc)

    assert row["secrecy_label"] == "Mật"
    assert row["urgency_label"] == "Khẩn"


def test_co_can_ra_soat_doi_thanh_chu(db, doc):
    doc.needs_review = True
    db.commit()

    assert _dong(db, doc)["needs_review_text"] == "Cần rà soát"
    doc.needs_review = False
    db.commit()
    assert _dong(db, doc)["needs_review_text"] == ""


def test_ban_rieng_duoc_danh_dau_trong_ten(db, doc):
    """Trong file Excel bản riêng nằm lẫn giữa bản gốc, không badge nào phân biệt."""
    doc.source_document_id = 999
    db.commit()

    assert _dong(db, doc)["title"].startswith("[Bản riêng] ")


def test_moi_cot_deu_co_du_lieu_that(db, doc):
    """Mọi `Col.key` phải là khóa CÓ THẬT trong dữ liệu đã dựng.

    Canh đúng chỗ dễ vỡ âm thầm: đổi tên khóa ở serializer → cột rỗng, không lỗi.
    """
    row = _dong(db, doc)
    missing = [col.key for col in ex.COLUMNS if col.key not in row]

    assert missing == [], f"cột khai trong export nhưng không có trong dữ liệu: {missing}"


def test_chon_cot_theo_man_hinh_giu_dung_thu_tu(db):
    chon = pick_columns(ex.COLUMNS, "title,display_code")

    assert [c.key for c in chon] == ["title", "display_code"]


def test_khong_chon_cot_thi_xuat_tron_bo(db):
    assert pick_columns(ex.COLUMNS, None) == ex.COLUMNS


def test_cot_ngay_thang_khai_dung_kieu(db):
    """Khai sai `kind` thì Excel đổ ra chuỗi, lọc và sắp xếp trong Excel hỏng theo."""
    theo_khoa = {c.key: c for c in ex.COLUMNS}

    assert theo_khoa["effective_date"].kind == "date"
    assert theo_khoa["expire_date"].kind == "date"
    assert theo_khoa["created_at"].kind == "datetime"
    assert theo_khoa["attachment_count"].kind == "int"


def test_xuat_di_qua_dung_truy_van_da_loc_quyen(db, doc):
    """`documents_query` là nơi duy nhất ép `origin = 1` — export phải đi qua nó."""
    ids = [d.id for d in documents_query(db).all()]

    assert doc.id in ids
    assert all(isinstance(x, int) for x in ids)


def test_bo_cot_khong_trung_khoa(db):
    key = [c.key for c in ex.COLUMNS]

    assert len(key) == len(set(key))
    assert all(isinstance(c, Col) for c in ex.COLUMNS)
