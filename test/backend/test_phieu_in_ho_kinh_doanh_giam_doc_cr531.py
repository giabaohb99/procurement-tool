"""bao-CR-531 — bộ ô ký cụm «XÉT DUYỆT» trên bản in Phiếu đề xuất mua hàng.

Đại ca chốt 30/09/2026:
  · danh mục Công ty có ô «Loại hình» (1 Công ty · 2 Hộ kinh doanh);
  · hộ kinh doanh: chỉ «Chủ hộ» + «Người lập», KHÔNG tên, KHÔNG chữ ký;
  · công ty: «Giám đốc» = người đại diện pháp luật; trùng NHÂN SỰ với ô «TP/BP đề xuất» và/hoặc
    «TP/BP mua hàng» thì bỏ ô trùng, tên + chữ ký dời sang ô «Giám đốc». Ca thật trên prod:
    ICARE (đại diện Lê Phước Hữu) — PYC29092604 do chính ông duyệt → phiếu in ba ô.
  · id chưa biết (0) thì KHÔNG gộp — `0 == 0` mà gộp là mọi pháp nhân chưa khai đại diện đều
    mất ô «TP/BP đề xuất».

`purchase_request/print_signature_cells.py` là chỗ DUY NHẤT quyết định; hai giao diện chỉ vẽ.
"""
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

import app
from app.core.audit import record
from app.modules.company import service as company_service
from app.modules.company.constants import CompanyType
from app.modules.company.model import Company
from app.modules.company.schema import CompanyCreate, CompanyOut, CompanyUpdate
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_request.controller import _out as pr_out
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.purchase_request.print_signature_cells import build_print_signature_cells
from app.modules.user.model import User


def _employee(db, full_name: str, department_id: int = 0) -> Employee:
    emp = Employee(full_name=full_name, code=full_name.replace(" ", "")[:20], department_id=department_id)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


def _user(db, emp: Employee, signature: str) -> User:
    user = User(email=f"{emp.code}@dego.vn", employee_id=emp.id, signature=signature, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _company(db, code: str, legal_rep_id: int | None, company_type: int = 1) -> Company:
    comp = Company(code=code, name=f"Cong ty {code}", legal_representative_id=legal_rep_id,
                   company_type=company_type)
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp


class _World:
    """Phòng thu mua có trưởng phòng (Ngân) + admin điều phối (Hậu); trưởng phòng đề xuất (Hữu)."""

    def __init__(self, db):
        dept = Department(code="TM531", name="Thu mua 531", manager_id=0)
        db.add(dept)
        db.commit()
        db.refresh(dept)
        self.head = _employee(db, "Pham Khanh Ngan", dept.id)
        _user(db, self.head, "https://cdn/ky-ngan.png")
        dept.manager_id = self.head.id
        db.commit()
        self.admin = _employee(db, "Chau Phuc Hau", dept.id)
        self.admin_user = _user(db, self.admin, "https://cdn/ky-hau.png")
        self.proposer = _employee(db, "Le Phuoc Huu")
        self.proposer_user = _user(db, self.proposer, "https://cdn/ky-huu.png")
        self.other = _employee(db, "Nguoi Khac")
        self.requester = _employee(db, "Nguoi Lap")
        _user(db, self.requester, "https://cdn/ky-lap.png")


@pytest.fixture
def world(db):
    return _World(db)


def _pr(db, world, company: Company | None, status: str = "dispatched", stored_approver: int | None = None,
        code: str = "PYC-531") -> PurchaseRequest:
    pr = PurchaseRequest(code=code, status=status, requester="Nguoi Lap", requester_id=world.requester.id,
                         department="Phong De Xuat", company_id=company.id if company else 0,
                         approver_employee_id=world.proposer.id if stored_approver is None else stored_approver,
                         created_by=1, updated_by=1)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if status == "dispatched":
        record(db, world.admin_user.id, "purchase_request", pr.id, "dispatched")
    return pr


def _roles(cells):
    return [c["role"] for c in cells]


def _cell(cells, role):
    return next(c for c in cells if c["role"] == role)


# ─── Luật 1: hộ kinh doanh ─────────────────────────────────────────────────────


def test_household_prints_only_owner_and_preparer_without_names(db, world):
    comp = _company(db, "HKD", world.proposer.id, int(CompanyType.HOUSEHOLD))
    cells = pr_out(db, _pr(db, world, comp))["print_signature_cells"]
    assert _roles(cells) == ["Chủ hộ", "Người lập"]
    assert all(c["name"] == "" and c["signature"] == "" for c in cells), \
        "hộ kinh doanh KHÔNG in tên/chữ ký ở mọi chế độ — kể cả khi hệ thống biết người lập"


# ─── Luật 2: công ty — gộp ô Giám đốc ───────────────────────────────────────────


def test_director_is_proposer_merges_into_director_cell(db, world):
    """Ca ICARE / PYC29092604: đại diện pháp luật chính là TP/BP đề xuất → ba ô."""
    comp = _company(db, "ICARE", world.proposer.id)
    d = pr_out(db, _pr(db, world, comp))
    cells = d["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "Người lập"]
    director = _cell(cells, "Giám đốc")
    assert director["name"] == "Le Phuoc Huu" and director["signature"] == "https://cdn/ky-huu.png"
    assert _cell(cells, "TP/BP mua hàng")["name"] == "Pham Khanh Ngan"
    assert _cell(cells, "Người lập") == {"key": "preparer", "role": "Người lập", "name": "Nguoi Lap",
                                         "signature": "https://cdn/ky-lap.png"}
    #  Khóa cũ giữ nguyên cho giao diện chưa cập nhật.
    assert d["approver_name"] == "Le Phuoc Huu" and d["purchasing_head_name"] == "Pham Khanh Ngan"


def test_director_is_purchasing_head_merges_into_director_cell(db, world):
    comp = _company(db, "CTYTM", world.head.id)
    cells = pr_out(db, _pr(db, world, comp))["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP đề xuất", "Người lập"]
    assert _cell(cells, "Giám đốc")["name"] == "Pham Khanh Ngan"
    assert _cell(cells, "Giám đốc")["signature"] == "https://cdn/ky-ngan.png"
    assert _cell(cells, "TP/BP đề xuất")["name"] == "Le Phuoc Huu"


def test_director_is_both_leaves_director_and_preparer(db, world):
    comp = _company(db, "CTYBOTH", world.head.id)
    pr = _pr(db, world, comp, stored_approver=world.head.id)
    cells = pr_out(db, pr)["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "Người lập"]
    assert _cell(cells, "Giám đốc")["name"] == "Pham Khanh Ngan"


def test_no_match_keeps_four_cells_with_blank_director(db, world):
    comp = _company(db, "CTYKHAC", world.other.id)
    cells = pr_out(db, _pr(db, world, comp))["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "TP/BP đề xuất", "Người lập"]
    assert _cell(cells, "Giám đốc")["name"] == "" and _cell(cells, "Giám đốc")["signature"] == ""
    assert _cell(cells, "TP/BP đề xuất")["name"] == "Le Phuoc Huu"


def test_company_without_legal_rep_never_merges(db, world):
    """Chưa khai đại diện (NULL) — không được gộp dù ô khác cũng chưa biết người (0 == 0)."""
    comp = _company(db, "CTYNULL", None)
    pr = _pr(db, world, comp, status="draft", stored_approver=0)
    cells = pr_out(db, pr)["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "TP/BP đề xuất", "Người lập"]


def test_pr_without_company_prints_four_cells(db, world):
    cells = pr_out(db, _pr(db, world, None))["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "TP/BP đề xuất", "Người lập"]


@pytest.mark.parametrize("proposer_id,purchasing_id", [(0, 0), (0, 9), (9, 0)])
def test_unknown_ids_do_not_merge(proposer_id, purchasing_id):
    """Pháp nhân CÓ đại diện (id 5) nhưng người ở ô kia chưa biết (0) hoặc khác → không gộp."""
    comp = Company(code="X", name="X", legal_representative_id=5, company_type=1)
    signers = {"approver_name": "A", "proposer_employee_id": proposer_id,
               "purchasing_head_name": "B", "purchasing_head_employee_id": purchasing_id}
    cells = build_print_signature_cells(comp, signers, "C", "")
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "TP/BP đề xuất", "Người lập"]
    assert cells[0]["name"] == ""


def test_director_zero_with_zero_ids_does_not_merge():
    comp = Company(code="Y", name="Y", legal_representative_id=0, company_type=1)
    cells = build_print_signature_cells(comp, {"proposer_employee_id": 0, "purchasing_head_employee_id": 0},
                                        "C", "")
    assert len(cells) == 4


def test_before_approval_director_cell_merges_but_stays_blank(db, world):
    """Chưa duyệt (bao-CR-521): ô đề xuất để trống tên — bộ ô đã biết nhờ người được chọn."""
    comp = _company(db, "CTYSUB", world.proposer.id)
    cells = pr_out(db, _pr(db, world, comp, status="submitted"))["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "Người lập"]
    assert _cell(cells, "Giám đốc")["name"] == "" and _cell(cells, "Giám đốc")["signature"] == ""


def test_old_ticket_merges_via_audit_approver(db, world):
    """Phiếu cũ chưa có cột `approver_employee_id`: người duyệt tra từ nhật ký → vẫn so theo nhân sự."""
    comp = _company(db, "CTYOLD", world.proposer.id)
    pr = _pr(db, world, comp, stored_approver=0)
    record(db, world.proposer_user.id, "purchase_request", pr.id, "approved")
    cells = pr_out(db, pr)["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP mua hàng", "Người lập"]
    assert _cell(cells, "Giám đốc")["signature"] == "https://cdn/ky-huu.png"


def test_dispatcher_fallback_is_compared_by_dispatcher_employee(db, world):
    """Phòng thu mua chưa gán trưởng → ô mua hàng lùi về người điều phối; so id của CHÍNH người đó."""
    db.query(Department).filter(Department.code == "TM531").update({"manager_id": 0})
    db.commit()
    comp = _company(db, "CTYDISP", world.admin.id)
    cells = pr_out(db, _pr(db, world, comp))["print_signature_cells"]
    assert _roles(cells) == ["Giám đốc", "TP/BP đề xuất", "Người lập"]
    assert _cell(cells, "Giám đốc")["signature"] == "https://cdn/ky-hau.png"


def test_same_name_different_employee_does_not_merge(db, world):
    """So bằng id, KHÔNG bằng tên: trùng tên với người đại diện vẫn giữ đủ bốn ô."""
    twin = _employee(db, "Le Phuoc Huu 2")
    twin.full_name = "Le Phuoc Huu"
    db.commit()
    comp = _company(db, "CTYTWIN", twin.id)
    cells = pr_out(db, _pr(db, world, comp))["print_signature_cells"]
    assert len(cells) == 4


# ─── Danh mục Công ty: ô «Loại hình» ─────────────────────────────────────────────


def test_company_type_defaults_to_company_and_accepts_household():
    assert CompanyCreate(name="A").company_type == CompanyType.COMPANY
    assert CompanyCreate(name="A", company_type=2).company_type == 2
    assert CompanyCreate(name="A", company_type="2").company_type == 2, "ô chọn v1 gửi chuỗi"
    assert CompanyUpdate(company_type=1).company_type == 1
    assert CompanyUpdate().company_type is None


@pytest.mark.parametrize("bad", [0, 3, -1, 99, "abc", "", True, 1.5])
def test_company_type_rejects_unknown_codes(bad):
    with pytest.raises(ValidationError):
        CompanyCreate(name="A", company_type=bad)
    with pytest.raises(ValidationError):
        CompanyUpdate(company_type=bad)


def test_company_out_none_type_reads_as_company():
    """Bản ghi chưa flush mang None — đừng để cả màn danh sách 500 vì một ô."""
    out = CompanyOut.model_validate({"id": 1, "name": "A", "company_type": None})
    assert out.company_type == CompanyType.COMPANY


def test_company_crud_persists_type(db):
    comp = company_service.create_company(db, CompanyCreate(code="HKD2", name="HKD", company_type=2), 1)
    assert comp.company_type == CompanyType.HOUSEHOLD
    comp = company_service.update_company(db, comp.id, CompanyUpdate(company_type=1), 1)
    assert comp.company_type == CompanyType.COMPANY
    #  Gửi null = không đổi (cột NOT NULL).
    comp = company_service.update_company(db, comp.id, CompanyUpdate(company_type=None), 1)
    assert comp.company_type == CompanyType.COMPANY


def test_migration_backfill_matches_household_names():
    path = (Path(app.__file__).resolve().parents[1] / "migrations" / "versions"
            / "c531a7e4d2f9_company_type_ho_kinh_doanh.py")
    spec = importlib.util.spec_from_file_location("mig_c531", path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    assert mig._is_household_name("HỘ KINH DOANH DR XANH"), "dòng prod id 7"
    assert mig._is_household_name("hộ kinh doanh Minh An")
    assert mig._is_household_name("  Hộ  Kinh   Doanh X")
    #  Chuỗi dạng tổ hợp (NFD) vẫn khớp.
    import unicodedata
    assert mig._is_household_name(unicodedata.normalize("NFD", "HỘ KINH DOANH Y"))
    assert not mig._is_household_name("CÔNG TY TNHH HỘ KINH DOANH")
    assert not mig._is_household_name("HO KINH DOANH")
    assert not mig._is_household_name(None)
    assert not mig._is_household_name("")
