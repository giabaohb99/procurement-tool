"""bao-CR-532 — gộp pháp nhân trùng (DEGO HOLDING) vào pháp nhân giữ (DEGO) rồi xóa bản trùng.

Mỗi bài canh một cái bẫy tìm thấy khi dò dữ liệu thật trên dev/prod 30/09/2026:
- liên kết phòng–pháp nhân có ``ON DELETE CASCADE``: chưa chuyển mà xóa là mất im lặng;
- phạm vi quyền lưu id công ty dạng CHỮ, và có dòng sẽ thành trùng sau khi đổi;
- tồn kho là số dẫn xuất — cùng (kho, mã hàng) ở hai bên phải cộng theo bình quân gia quyền;
- mỗi pháp nhân đúng một thư mục gốc (ràng buộc duy nhất);
- ``core.audit.record`` tự commit — gộp mà gọi nó thì chạy thử cũng thành ghi thật.
"""
import pytest
from sqlalchemy import text

from app.modules.audit.model import AuditLog
from app.modules.company.merge_service import (
    MergeError, company_columns, count_references, merge_companies, write_merge_audit,
)
from app.modules.company.model import Company
from app.modules.department.model import Department, DepartmentCompany
from app.modules.doc_catalog.folder_constants import FolderKind
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_model import DocFolder
from app.modules.employee.model import Employee
from app.modules.inventory.model import Inventory, InventoryMove
from app.modules.user.model import UserScope

MST = "1801722464"


def _pair(db, **dup_over):
    keep = Company(code="DEGO", name="CÔNG TY TNHH DEGO HOLDING", tax_code=MST,
                   address="B19 đường dẫn cầu Cần Thơ", is_active=True)
    dup = Company(code="DEGO HOLDING", name="CÔNG TY TNHH DEGO HOLDING", tax_code=MST,
                  address="", invoice_email="hoadon@dego.vn", is_active=True, **dup_over)
    db.add_all([keep, dup])
    db.commit()
    return keep.id, dup.id


def _root(db, company_id, fid_path):
    f = DocFolder(company_id=company_id, root_company_id=company_id, parent_id=0,
                  kind=int(FolderKind.COMPANY), path=fid_path, depth=1)
    db.add(f)
    db.flush()
    return f


def test_moves_live_references_fills_empty_fields_and_deletes_the_duplicate(db):
    keep, dup = _pair(db)
    emp = Employee(code="NSU231", full_name="Trần Minh Được", company_id=dup)
    dept = Department(code="IT", name="Lập trình & IT nội bộ", company_id=dup)
    db.add_all([emp, dept])
    db.commit()

    report = merge_companies(db, keep, dup)
    db.commit()

    assert db.get(Company, dup) is None
    assert db.get(Employee, emp.id).company_id == keep
    assert db.get(Department, dept.id).company_id == keep
    kept = db.get(Company, keep)
    #  Ô trống của bản giữ lấy từ bản trùng; ô đã có thì KHÔNG bị đè bằng chuỗi rỗng của bản trùng.
    assert kept.invoice_email == "hoadon@dego.vn"
    assert kept.address == "B19 đường dẫn cầu Cần Thơ"
    assert "invoice_email" in report["_filled_fields"]
    assert count_references(db, dup) == {}


def test_merge_never_commits_so_a_dry_run_really_rolls_back(db):
    """Bẫy thật: ``record()`` tự ``db.commit()``. Gộp mà gọi nó thì chạy thử trên prod xóa thật."""
    keep, dup = _pair(db)
    emp = Employee(code="NV1", full_name="Nhân viên", company_id=dup)
    db.add(emp)
    db.commit()

    merge_companies(db, keep, dup)
    db.rollback()

    assert db.get(Company, dup) is not None
    assert db.get(Employee, emp.id).company_id == dup
    assert db.query(AuditLog).count() == 0


def test_department_links_are_moved_before_delete_and_never_doubled(db):
    """``ON DELETE CASCADE``: chưa chuyển mà xóa bản trùng là MySQL xóa luôn liên kết."""
    keep, dup = _pair(db)
    both = Department(code="KT", name="Kế toán")
    only_dup = Department(code="KH", name="Kho")
    db.add_all([both, only_dup])
    db.flush()
    db.add_all([DepartmentCompany(department_id=both.id, company_id=keep),
                DepartmentCompany(department_id=both.id, company_id=dup),
                DepartmentCompany(department_id=only_dup.id, company_id=dup)])
    db.commit()

    merge_companies(db, keep, dup)
    db.commit()

    rows = sorted((r.department_id, r.company_id) for r in db.query(DepartmentCompany).all())
    assert rows == sorted([(both.id, keep), (only_dup.id, keep)])


def test_user_scope_drops_rows_that_would_duplicate_and_rewrites_the_rest(db):
    keep, dup = _pair(db)
    db.add_all([
        UserScope(user_id=249, role_id=2, entity="", dim="company", value=str(keep), is_exclude=False),
        UserScope(user_id=249, role_id=2, entity="", dim="company", value=str(dup), is_exclude=False),
        UserScope(user_id=271, role_id=77, entity="", dim="company", value=str(dup), is_exclude=False),
        #  Cùng CON SỐ nhưng khác chiều: đây là id PHÒNG BAN, không được đụng.
        UserScope(user_id=271, role_id=77, entity="", dim="department", value=str(dup), is_exclude=False),
    ])
    db.commit()

    report = merge_companies(db, keep, dup)
    db.commit()

    rows = sorted((s.user_id, s.role_id, s.dim, s.value) for s in db.query(UserScope).all())
    assert rows == sorted([(249, 2, "company", str(keep)), (271, 77, "company", str(keep)),
                           (271, 77, "department", str(dup))])
    assert report["_scope_users"] == [249, 271]


def test_inventory_on_both_sides_is_recomputed_as_weighted_average(db):
    keep, dup = _pair(db)
    db.add_all([
        InventoryMove(company_id=keep, warehouse_code="W1", product_code="P1", qty=10, unit_price=100),
        InventoryMove(company_id=dup, warehouse_code="W1", product_code="P1", qty=30, unit_price=200),
        Inventory(company_id=keep, warehouse_code="W1", product_code="P1", qty=10, avg_cost=100, value=1000),
        Inventory(company_id=dup, warehouse_code="W1", product_code="P1", qty=30, avg_cost=200, value=6000),
    ])
    db.commit()

    merge_companies(db, keep, dup)
    db.commit()

    rows = db.query(Inventory).all()
    assert len(rows) == 1, "cùng (công ty, kho, mã) phải còn đúng một dòng"
    inv = rows[0]
    assert inv.company_id == keep
    assert float(inv.qty) == 40 and float(inv.value) == 7000 and float(inv.avg_cost) == 175
    assert {m.company_id for m in db.query(InventoryMove).all()} == {keep}


def test_folder_links_go_to_the_keeping_root_and_the_duplicate_root_is_removed(db):
    keep, dup = _pair(db)
    keep_root, dup_root = _root(db, keep, "/1/"), _root(db, dup, "/2/")
    db.add_all([
        DocumentFolderLink(document_id=9, folder_id=dup_root.id, is_primary=True),
        #  Văn bản 10 nằm ở cả hai gốc: chuyển mù là đụng ràng buộc (văn bản, thư mục).
        DocumentFolderLink(document_id=10, folder_id=keep_root.id, is_primary=False),
        DocumentFolderLink(document_id=10, folder_id=dup_root.id, is_primary=True),
    ])
    db.commit()
    dup_root_id = dup_root.id

    merge_companies(db, keep, dup)
    db.commit()

    assert db.get(DocFolder, dup_root_id) is None
    links = sorted((l.document_id, l.folder_id, bool(l.is_primary)) for l in db.query(DocumentFolderLink).all())
    assert links == [(9, keep_root.id, True), (10, keep_root.id, True)]


def test_duplicate_root_is_handed_over_whole_when_the_keeper_has_none(db):
    keep, dup = _pair(db)
    dup_root = _root(db, dup, "/2/")
    db.commit()

    merge_companies(db, keep, dup)
    db.commit()

    f = db.get(DocFolder, dup_root.id)
    assert (f.company_id, f.root_company_id) == (keep, keep)


def test_stops_when_the_duplicate_root_still_has_subfolders(db):
    """Chuyển thư mục con phải viết lại ``path`` — việc của dịch vụ thư mục, script không tự làm."""
    keep, dup = _pair(db)
    _root(db, keep, "/1/")
    dup_root = _root(db, dup, "/2/")
    db.add(DocFolder(company_id=dup, parent_id=dup_root.id, kind=int(FolderKind.NORMAL), path="/2/3/", depth=2))
    db.commit()

    with pytest.raises(MergeError, match="thư mục con"):
        merge_companies(db, keep, dup)


@pytest.mark.parametrize("dup_tax", ["0301234567", ""])
def test_refuses_two_companies_that_are_not_the_same_legal_entity(db, dup_tax):
    keep, dup = _pair(db)
    db.get(Company, dup).tax_code = dup_tax
    db.commit()
    with pytest.raises(MergeError, match="Mã số thuế"):
        merge_companies(db, keep, dup)


def test_refuses_to_merge_a_company_into_itself(db):
    keep, _ = _pair(db)
    with pytest.raises(MergeError):
        merge_companies(db, keep, keep)


def test_history_tables_are_never_rewritten():
    assert company_columns(), "phải dò ra được cột công ty"
    assert all(not t.endswith("_log") for t, _ in company_columns())


def test_audit_is_written_for_both_sides_only_when_the_caller_asks(db):
    keep, dup = _pair(db)
    report = merge_companies(db, keep, dup)
    write_merge_audit(db, keep, dup, report, user_id=1)

    rows = db.execute(text("select entity_id, action from tab_audit_log where entity = 'company' "
                           "order by entity_id")).all()
    assert [(r[0], r[1]) for r in rows] == [(keep, "update"), (dup, "delete")]
    assert db.get(Company, dup) is None
