"""bao-CR-705 — danh sách Đơn mua hàng thêm cột "Phòng xử lý", "Trưởng phòng phê duyệt" và các cột ẩn sẵn.

`service.list_display_names` gắn tên cho cả trang bằng một lượt tra mỗi danh mục; đơn cũ còn phòng xử lý
`0` hiện đúng phòng thu mua mặc định (PBA017) như màn chi tiết (bao-CR-524). Tệp Excel của màn dùng
chung hàm này nên cột bật trên bảng xuất ra đúng tên.
"""
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order import export as po_export
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_order.service import list_display_names


def _setup(db, seed):
    central = Department(code="PBA017", name="Sản xuất -Thu mua", company_id=seed.company_id, is_active=True)
    factory = Department(code="NM705", name="Dego Organic", company_id=seed.company_id, is_active=True)
    boss = Employee(code="NSU705", full_name="Đoàn Minh Khôi", is_active=True)
    db.add_all([central, factory, boss])
    db.commit()
    return central, factory, boss


def _po(db, seed, code, handler, approver=0):
    po = PurchaseOrder(code=code, company_id=seed.company_id, handler_dept_id=handler,
                       approver_employee_id=approver, status="approved", exchange_rate=25400,
                       created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.commit()
    return po


def test_rows_get_handler_department_and_approver_names(db, seed):
    central, factory, boss = _setup(db, seed)
    a = _po(db, seed, "PO705A", factory.id, boss.id)
    b = _po(db, seed, "PO705B", central.id)
    out = list_display_names(db, [a, b])
    assert out[a.id]["handler_dept_name"] == "Dego Organic"
    assert out[a.id]["approver_name"] == "Đoàn Minh Khôi"
    assert out[b.id]["handler_dept_name"] == "Sản xuất -Thu mua"
    assert out[b.id]["approver_name"] == ""            # chưa có người duyệt -> trống, không lỗi


def test_legacy_zero_handler_shows_the_central_purchasing_department(db, seed):
    central, _, _ = _setup(db, seed)
    po = _po(db, seed, "PO705C", 0)
    row = list_display_names(db, [po])[po.id]
    assert row["handler_dept_id"] == central.id
    assert row["handler_dept_name"] == "Sản xuất -Thu mua"


def test_company_creator_and_rate_ride_along_for_the_hidden_columns(db, seed):
    _setup(db, seed)
    po = _po(db, seed, "PO705D", 0)
    row = list_display_names(db, [po])[po.id]
    assert row["company_name"] == db.get(Company, seed.company_id).name
    assert row["created_by_name"] != ""                 # người tạo luôn có nhãn (họ tên hoặc email)
    assert row["exchange_rate"] == 25400


def test_unknown_ids_leave_names_blank_and_empty_page_is_empty(db, seed):
    _setup(db, seed)
    po = _po(db, seed, "PO705E", 999999, 888888)
    row = list_display_names(db, [po])[po.id]
    assert row["handler_dept_name"] == "" and row["approver_name"] == ""
    assert list_display_names(db, []) == {}


def test_excel_export_carries_the_new_head_columns(db, seed):
    _, factory, boss = _setup(db, seed)
    po = _po(db, seed, "PO705F", factory.id, boss.id)
    rows = po_export.build_rows(db, [po])
    assert rows[0]["handler_dept_name"] == "Dego Organic"
    assert rows[0]["approver_name"] == "Đoàn Minh Khôi"
    keys = [c.key for c in po_export.HEADER_COLS] + [c.key for c in po_export.line_columns(True)]
    assert len(keys) == len(set(keys)), "hai cột trùng khóa trong một tệp Excel"
