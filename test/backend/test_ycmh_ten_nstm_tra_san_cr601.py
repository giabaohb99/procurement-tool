"""bao-CR-601 — tên NSTM phụ trách trả SẴN theo dòng YCMH.

Vì sao cần: hai bản giao diện từng tra tên từ danh sách nhân sự tải về, mà danh sách đó
lọc theo PHẠM VI người xem. Người bị giới hạn pháp nhân (trong khi 259 hồ sơ nhân sự để
pháp nhân 0) chỉ thấy mã «NSU012» ở cột NSTM phụ trách. Máy chủ trả tên là hết phụ thuộc.
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.purchase_request import controller as C
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


def _pr_with_items(db, seed, assignees):
    pr = PurchaseRequest(code="PYC-CR601", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test", department_id=seed.dept_id,
                         status="dispatched", request_date="2026-10-06",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for n, code in enumerate(assignees):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"SP{n}", product_name=f"Hàng {n}",
                                   item_group="Nhãn", qty=1, unit="cái", price=1, vat_pct=0, amount=1,
                                   assignee=code, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    return pr


def test_assignee_name_is_resolved_per_line(db, seed):
    nstm = db.get(Employee, seed.emp_nstm_id)
    pr = _pr_with_items(db, seed, [seed.emp_nstm_code, "", "NSU-KHONG-CO"])

    items = C._out(db, pr, SimpleNamespace(id=seed.u_req_id))["items"]

    assert items[0]["assignee"] == seed.emp_nstm_code
    assert items[0]["assignee_name"] == nstm.full_name
    #  Chưa cử → rỗng; mã chết (nhân sự đã xóa) → rỗng chứ không nổ, màn hình lùi về mã.
    assert items[1]["assignee_name"] == ""
    assert items[2]["assignee_name"] == ""
