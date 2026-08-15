from app.modules.doc_catalog.model import DocType
from app.modules.department.model import DepartmentCompany
from app.seed import seed_document_phase1
from app.seed_data.document_phase1 import ALL_DOC_TYPES, OFFICIAL_DOC_TYPES


def test_phase1_catalog_has_32_official_types_and_trich_luc_33():
    assert len(OFFICIAL_DOC_TYPES) == 32
    assert len(ALL_DOC_TYPES) == 33
    assert len({row["code"] for row in ALL_DOC_TYPES}) == 33

    trich_luc = ALL_DOC_TYPES[-1]
    assert trich_luc["code"] == "TL"
    assert trich_luc["name"] == "Trích lục"
    assert trich_luc["id_scheme"] == 2
    assert trich_luc["needs_decision"] is False
    assert trich_luc["number_when"] == 2
    assert trich_luc["sort_order"] == 33


def test_phase1_seed_is_idempotent_and_backfills_primary_department_company(db, seed):
    first_change_count = seed_document_phase1(db)

    assert first_change_count > 0
    assert db.query(DocType).count() == 33
    assert db.query(DocType).filter(DocType.code == "TL").one().sort_order == 33

    primary_link = (
        db.query(DepartmentCompany)
        .filter(
            DepartmentCompany.department_id == seed.dept_id,
            DepartmentCompany.company_id == seed.company_id,
        )
        .one()
    )
    assert primary_link.is_active is True

    assert seed_document_phase1(db) == 0
    assert db.query(DocType).count() == 33
