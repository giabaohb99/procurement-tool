"""bao-CR-758 — tạo ĐMH (kể cả tạo từ YCMH trên v2) phải GIỮ ô "Trưởng phòng phê duyệt" người lập đã chọn.

Form tạo ĐMH v2 có ô chọn người duyệt (bao-CR-499) và gửi `approver_employee_id` lên, nhưng `create_po` không
ghi cột đó: mở đơn vừa tạo ra ô trống, người lập phải chọn lại rồi Lưu thêm — đúng lượt PATCH 02:48:22 của PO01178.
"""
from app.modules.purchase_order.schema import POCreate, POItemIn
from app.modules.purchase_order.service import create_po


def test_tao_dmh_ghi_nguoi_duoc_chon_duyet(db, seed):
    po = create_po(db, POCreate(company_id=seed.company_id, supplier_code="NCC01", supplier_name="NCC 01",
                                approver_employee_id=seed.emp_tp_id,
                                items=[POItemIn(product_code="VT01", product_name="Vật tư", qty_order=1,
                                                price=4250)]),
                   seed.u_req_id)
    assert po.approver_employee_id == seed.emp_tp_id


def test_tao_dmh_khong_chon_thi_de_0(db, seed):
    po = create_po(db, POCreate(company_id=seed.company_id, supplier_code="NCC01",
                                items=[POItemIn(product_code="VT01", product_name="Vật tư", qty_order=1)]),
                   seed.u_req_id)
    assert int(po.approver_employee_id or 0) == 0
