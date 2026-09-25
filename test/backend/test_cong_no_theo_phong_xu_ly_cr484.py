"""bao-CR-484 — CÔNG NỢ tính cho PHÒNG XỬ LÝ (đại ca chốt 25/09/2026).

Luật CR-414 GĐ4 gán nợ cho «phòng được nhờ, không thì phòng lập đơn». Từ CR-480 ô «Phòng
xử lý» có nghĩa: `handler_dept_id = 0` = THU MUA CHUNG xử lý. Nếu giữ luật cũ thì nợ của đơn
nhà máy xin mà thu mua chung mua hộ bị tính cho nhà máy — nhà máy không trả, không cấn trừ,
mà bậc `dept_proc` của họ lại thấy nó. Nay:
  · nợ = `handler_dept_id` của đơn, 0 = thu mua chung (`payable.service.debt_dept_of`);
  · `category_assignee.handling_dept_of` GIỮ nguyên lùi về phòng lập — nó tra bộ phân công
    người phụ trách, một việc khác; đừng gộp hai hàm làm một;
  · nợ cũ gán lại bằng `resync_departments_from_orders` (qua `backfill_handling_dept.py`),
    YCTT đã lập thì không đụng.
"""
import pytest

from app.modules.category_assignee.service import handling_dept_of
from app.modules.department.model import Department
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PurchaseOrder


@pytest.fixture
def two_departments(db, seed):
    factory = Department(code="NM8", name="Nhà máy", company_id=seed.company_id, is_active=True)
    purchasing = Department(code="TM8", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, purchasing])
    db.flush()
    return factory.id, purchasing.id


def _order(db, seed, code, department_id, handler_dept_id):
    po = PurchaseOrder(code=code, company_id=seed.company_id, department_id=department_id,
                       handler_dept_id=handler_dept_id, supplier_code="NCCA",
                       supplier_name="NCC Anpha", order_date="2026-09-01", status="approved",
                       created_by=seed.u_nstm_id)
    db.add(po)
    db.flush()
    return po


def _debt(db, seed, po, ref_id, department_id):
    return pay_service.upsert(db, source_type="goods", ref_id=ref_id, company_id=seed.company_id,
                              supplier_code="NCCA", supplier_name="NCC Anpha", po_id=po.id,
                              po_code=po.code, invoice_no="", incur_date="2026-09-01",
                              amount=100, vat=8, due_days=30, user_id=seed.u_nstm_id,
                              department_id=department_id)


def test_debt_follows_handler_department_and_never_falls_back_to_requesting_department(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    helped = _order(db, seed, "PO-CR484-A", factory_id, 0)          # nhà máy xin, thu mua chung mua
    own = _order(db, seed, "PO-CR484-B", factory_id, factory_id)    # nhà máy tự mua

    assert pay_service.debt_dept_of(helped) == 0, "thu mua chung xử lý -> nợ của thu mua chung"
    assert pay_service.debt_dept_of(own) == factory_id
    #  Hàm tra bộ phân công VẪN lùi về phòng lập — hai luật, hai hàm.
    assert handling_dept_of(helped) == factory_id
    assert pay_service.debt_dept_of(None) == 0


def test_resync_moves_old_debts_to_the_handler_department_only(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    helped = _order(db, seed, "PO-CR484-C", factory_id, 0)
    own = _order(db, seed, "PO-CR484-D", factory_id, factory_id)
    stale = _debt(db, seed, helped, 901, factory_id)     # sinh theo luật cũ: lùi về phòng lập
    right = _debt(db, seed, own, 902, factory_id)
    orphan = _debt(db, seed, helped, 903, purchasing_id)
    orphan.po_id = 0                                      # nợ không có đơn: giữ nguyên
    db.flush()

    assert pay_service.resync_departments_from_orders(db, dry_run=True) == 1
    assert db.get(Payable, stale.id).department_id == factory_id, "dry-run không ghi"

    assert pay_service.resync_departments_from_orders(db) == 1
    assert db.get(Payable, stale.id).department_id == 0
    assert db.get(Payable, right.id).department_id == factory_id
    assert db.get(Payable, orphan.id).department_id == purchasing_id
    assert pay_service.resync_departments_from_orders(db) == 0, "chạy lại vô hại"


def test_resync_follows_a_later_change_of_handler_department(db, seed, two_departments):
    """Chuyển phòng xử lý sau khi nợ đã sinh: chạy lại là nợ đi theo phòng mới."""
    factory_id, purchasing_id = two_departments
    po = _order(db, seed, "PO-CR484-E", purchasing_id, 0)
    debt = _debt(db, seed, po, 904, 0)
    po.handler_dept_id = factory_id
    db.flush()
    assert pay_service.resync_departments_from_orders(db) == 1
    assert db.get(Payable, debt.id).department_id == factory_id
