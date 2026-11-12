"""bao-CR-715 — bài kiểm CHỤP KẾT QUẢ trước khi tách hai hàm dựng kết quả rối nhất cụm thu mua.

`purchase_request/serializer._out` (F 53) và `purchase_order/serializer._item` (E 36) được tách thành các
hàm con theo khối (phòng ban, cụm NCC, cờ quyền, chữ ký, dòng hàng...). Hai giao diện, bản in và xuất Excel
đọc theo khóa, còn bài kiểm / xuất file so cả THỨ TỰ khóa — nên bài này so nguyên khối: danh sách khóa theo
thứ tự, giá trị, và số câu truy vấn của một lần dựng.

Số liệu trong các hằng `EXPECTED_*` lấy từ lần chạy trên mã trước khi tách. Đổi hành vi có chủ đích thì sửa
hằng kèm mã CR, đừng nới phép so.
"""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from app.modules.purchase_order import serializer as po_ser
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request import serializer as pr_ser
from app.modules.purchase_request.constants import PR_OPT_MANUAL
from app.modules.purchase_request.model import (PurchaseRequest, PurchaseRequestItem,
                                                PurchaseRequestItemOption)
from app.modules.user.model import User

FIXED = datetime(2026, 11, 3, 8, 30, 0)


class _QueryCounter:
    def __init__(self, db):
        self.engine = db.get_bind()
        self.count = 0

    def _on(self, *_a, **_k):
        self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._on)
        return self

    def __exit__(self, *_exc):
        event.remove(self.engine, "before_cursor_execute", self._on)


def _plain(d):
    """Đưa kết quả về dạng so được (datetime -> chuỗi), GIỮ thứ tự khóa."""
    return json.loads(json.dumps(d, default=str, ensure_ascii=False))


@pytest.fixture
def pr_full(db, seed):
    pr = PurchaseRequest(code="PYC-715S", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="", department_id=seed.dept_id,
                         status="submitted", request_date="2026-11-01", need_date="2026-11-20",
                         vat_rate=0.08, is_urgent=True, note="Ghi chú phiếu",
                         suggested_supplier="NCC đề xuất", suggested_supplier_tax_code="0101",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    pr.created_at = FIXED
    db.add(pr)
    db.flush()
    a = PurchaseRequestItem(pr_id=pr.id, product_code="SP-A", product_name="Hàng A", item_group="Nhãn",
                            qty=10, unit="cuộn", price=100, vat_pct=8, amount=1080,
                            assignee=seed.emp_nstm_code, required_date="2026-11-15",
                            expected_date="2026-11-18", created_by=seed.u_req_id)
    b = PurchaseRequestItem(pr_id=pr.id, product_code="SP-B", product_name="Hàng B", item_group="Thùng",
                            qty=3, unit="cái", price=50, vat_pct=10, amount=165, line_status="cancelled",
                            created_by=seed.u_req_id)
    db.add_all([a, b])
    db.flush()
    o = PurchaseRequestItemOption(pr_item_id=a.id, source=PR_OPT_MANUAL, is_chosen=True, public_id=1,
                                  display_label="Phương án 1", supplier_code="NX", supplier_name="NCC NX",
                                  snap_price_by_volume=95, snap_vat=8, snap_delivery_time="7 ngày")
    o.created_at = FIXED
    db.add(o)
    db.commit()
    return pr


EXPECTED_PR_OUT = {'id': 1,
 'code': 'PYC-715S',
 'company_id': 1,
 'requester': 'Người YC',
 'requester_id': 1,
 'requester_position': '',
 'department_id': 1,
 'handler_dept_id': 0,
 'department': 'Phòng Test',
 'head_of_dept': '',
 'head_of_dept_id': 0,
 'purpose': '',
 'request_date': '2026-11-01',
 'received_date': '',
 'need_date': '2026-11-20',
 'status': 'submitted',
 'is_urgent': True,
 'vat_rate': 0.08,
 'assignee_id': 0,
 'note': 'Ghi chú phiếu',
 'show_code_on_print': True,
 'suggested_supplier': 'NCC đề xuất',
 'suggested_supplier_tax_code': '0101',
 'suggested_supplier_contact': '',
 'quote_filename': '',
 'quote_file_url': '',
 'handler_dept_name': '',
 'approver_employee_id': 0,
 'approver_employee_name': '',
 'dept_head_employee_id': 0,
 'dept_head_name': '',
 'dept_head_signature': '',
 'supplier_req': {'name': '', 'tax_code': '', 'contact': ''},
 'supplier_pur': {'name': 'NCC đề xuất', 'tax_code': '0101', 'contact': ''},
 'supplier_from_survey': False,
 'can_edit_supplier_pur': False,
 'dispatch_enabled': True,
 'options_enabled': False,
 'can_dispatch': False,
 'can_transfer_dept': False,
 'can_return_dept': False,
 'can_decide': True,
 'can_approve': True,
 'can_return': True,
 'created_at': '2026-11-03 08:30:00',
 'created_by_name': 'Người YC',
 'options_chosen_at': None,
 'options_chosen_by_name': '',
 'has_quote_file': False,
 'survey_requests': [],
 'survey_request_id': 0,
 'survey_request_code': '',
 'requester_signature': '',
 'approver_name': '',
 'approver_signature': '',
 'dispatcher_name': '',
 'dispatcher_signature': '',
 'purchasing_head_name': '',
 'purchasing_head_signature': '',
 'proposer_employee_id': 0,
 'purchasing_head_employee_id': 0,
 'company_name': 'Cty Test',
 'print_signature_cells': [{'key': 'director', 'role': 'Giám đốc', 'name': '', 'signature': ''},
                           {'key': 'purchasing_head', 'role': 'TP/BP mua hàng', 'name': '', 'signature': ''},
                           {'key': 'proposer', 'role': 'TP/BP đề xuất', 'name': '', 'signature': ''},
                           {'key': 'preparer', 'role': 'Người lập', 'name': 'Người YC', 'signature': ''}],
 'items': [{'id': 1,
            'product_code': 'SP-A',
            'product_name': 'Hàng A',
            'item_group': 'Nhãn',
            'group_desc': '',
            'qty': 10.0,
            'unit': 'cuộn',
            'price': 100.0,
            'vat_pct': 8.0,
            'amount': 1080.0,
            'warehouse': '',
            'required_date': '2026-11-15',
            'assignee': 'DEMONV',
            'assignee_name': 'NSTM Chính',
            'expected_date': '2026-11-18',
            'line_status': 'no_po',
            'line_status_label': 'Chưa tạo đơn mua hàng',
            'progress_note': '',
            'note': '',
            'qty_ordered': 0.0,
            'qty_received': 0.0,
            'product_id': 0,
            'product_thumbnail_url': '',
            'option_count': 1,
            'chosen_option': {'id': 1,
                              'pr_item_id': 1,
                              'source': 2,
                              'source_label': 'Nhập tay',
                              'product_survey_line_id': 0,
                              'public_id': 1,
                              'display_label': 'Phương án 1',
                              'is_chosen': True,
                              'snap_product_name': '',
                              'snap_spec': '',
                              'snap_origin': '',
                              'snap_quote_unit': '',
                              'snap_moq': 0.0,
                              'snap_price_by_volume': 95.0,
                              'snap_volume_range': '',
                              'snap_vat': 8.0,
                              'snap_delivery_time': '7 ngày',
                              'snap_delivery_place': '',
                              'snap_shipping_cost': 0.0,
                              'snap_sample_ready': False,
                              'snap_lab_result': '',
                              'nstm_note': '',
                              'created_at': '2026-11-03 08:30:00',
                              'supplier_code': 'NX',
                              'supplier_name': 'NCC NX',
                              'supplier_survey_id': 0,
                              'snap_internal_code': ''},
            'options_done': False,
            'no_option': False},
           {'id': 2,
            'product_code': 'SP-B',
            'product_name': 'Hàng B',
            'item_group': 'Thùng',
            'group_desc': '',
            'qty': 3.0,
            'unit': 'cái',
            'price': 50.0,
            'vat_pct': 10.0,
            'amount': 165.0,
            'warehouse': '',
            'required_date': '',
            'assignee': '',
            'assignee_name': '',
            'expected_date': '',
            'line_status': 'cancelled',
            'line_status_label': 'Hủy đơn',
            'progress_note': '',
            'note': '',
            'qty_ordered': 0.0,
            'qty_received': 0.0,
            'product_id': 0,
            'product_thumbnail_url': '',
            'option_count': 0,
            'chosen_option': None,
            'options_done': False,
            'no_option': False}],
 'subtotal': 1150.0,
 'vat': 95.0,
 'total': 1245.0}
EXPECTED_PR_OUT_QUERIES = 21
EXPECTED_PR_OUT_ANON = {'id': 1,
 'code': 'PYC-715S',
 'company_id': 1,
 'requester': 'Người YC',
 'requester_id': 1,
 'requester_position': '',
 'department_id': 1,
 'handler_dept_id': 0,
 'department': 'Phòng Test',
 'head_of_dept': '',
 'head_of_dept_id': 0,
 'purpose': '',
 'request_date': '2026-11-01',
 'received_date': '',
 'need_date': '2026-11-20',
 'status': 'submitted',
 'is_urgent': True,
 'vat_rate': 0.08,
 'assignee_id': 0,
 'note': 'Ghi chú phiếu',
 'show_code_on_print': True,
 'suggested_supplier': 'NCC đề xuất',
 'suggested_supplier_tax_code': '0101',
 'suggested_supplier_contact': '',
 'quote_filename': '',
 'quote_file_url': '',
 'handler_dept_name': '',
 'approver_employee_id': 0,
 'approver_employee_name': '',
 'dept_head_employee_id': 0,
 'dept_head_name': '',
 'dept_head_signature': '',
 'supplier_req': {'name': '', 'tax_code': '', 'contact': ''},
 'supplier_pur': {'name': 'NCC đề xuất', 'tax_code': '0101', 'contact': ''},
 'supplier_from_survey': False,
 'can_edit_supplier_pur': False,
 'dispatch_enabled': True,
 'options_enabled': False,
 'can_dispatch': False,
 'can_transfer_dept': False,
 'can_return_dept': False,
 'can_decide': False,
 'can_approve': False,
 'can_return': False,
 'created_at': '2026-11-03 08:30:00',
 'created_by_name': 'Người YC',
 'options_chosen_at': None,
 'options_chosen_by_name': '',
 'has_quote_file': False,
 'survey_requests': [],
 'survey_request_id': 0,
 'survey_request_code': '',
 'requester_signature': '',
 'approver_name': '',
 'approver_signature': '',
 'dispatcher_name': '',
 'dispatcher_signature': '',
 'purchasing_head_name': '',
 'purchasing_head_signature': '',
 'proposer_employee_id': 0,
 'purchasing_head_employee_id': 0,
 'company_name': 'Cty Test',
 'print_signature_cells': [{'key': 'director', 'role': 'Giám đốc', 'name': '', 'signature': ''},
                           {'key': 'purchasing_head', 'role': 'TP/BP mua hàng', 'name': '', 'signature': ''},
                           {'key': 'proposer', 'role': 'TP/BP đề xuất', 'name': '', 'signature': ''},
                           {'key': 'preparer', 'role': 'Người lập', 'name': 'Người YC', 'signature': ''}],
 'items': [{'id': 1,
            'product_code': 'SP-A',
            'product_name': 'Hàng A',
            'item_group': 'Nhãn',
            'group_desc': '',
            'qty': 10.0,
            'unit': 'cuộn',
            'price': 100.0,
            'vat_pct': 8.0,
            'amount': 1080.0,
            'warehouse': '',
            'required_date': '2026-11-15',
            'assignee': 'DEMONV',
            'assignee_name': 'NSTM Chính',
            'expected_date': '2026-11-18',
            'line_status': 'no_po',
            'line_status_label': 'Chưa tạo đơn mua hàng',
            'progress_note': '',
            'note': '',
            'qty_ordered': 0.0,
            'qty_received': 0.0,
            'product_id': 0,
            'product_thumbnail_url': '',
            'option_count': 1,
            'chosen_option': {'id': 1,
                              'pr_item_id': 1,
                              'source': 2,
                              'source_label': 'Nhập tay',
                              'product_survey_line_id': 0,
                              'public_id': 1,
                              'display_label': 'Phương án 1',
                              'is_chosen': True,
                              'snap_product_name': '',
                              'snap_spec': '',
                              'snap_origin': '',
                              'snap_quote_unit': '',
                              'snap_moq': 0.0,
                              'snap_price_by_volume': 95.0,
                              'snap_volume_range': '',
                              'snap_vat': 8.0,
                              'snap_delivery_time': '7 ngày',
                              'snap_delivery_place': '',
                              'snap_shipping_cost': 0.0,
                              'snap_sample_ready': False,
                              'snap_lab_result': '',
                              'nstm_note': '',
                              'created_at': '2026-11-03 08:30:00',
                              'supplier_code': 'NX',
                              'supplier_name': 'NCC NX',
                              'supplier_survey_id': 0,
                              'snap_internal_code': ''},
            'options_done': False,
            'no_option': False},
           {'id': 2,
            'product_code': 'SP-B',
            'product_name': 'Hàng B',
            'item_group': 'Thùng',
            'group_desc': '',
            'qty': 3.0,
            'unit': 'cái',
            'price': 50.0,
            'vat_pct': 10.0,
            'amount': 165.0,
            'warehouse': '',
            'required_date': '',
            'assignee': '',
            'assignee_name': '',
            'expected_date': '',
            'line_status': 'cancelled',
            'line_status_label': 'Hủy đơn',
            'progress_note': '',
            'note': '',
            'qty_ordered': 0.0,
            'qty_received': 0.0,
            'product_id': 0,
            'product_thumbnail_url': '',
            'option_count': 0,
            'chosen_option': None,
            'options_done': False,
            'no_option': False}],
 'subtotal': 1150.0,
 'vat': 95.0,
 'total': 1245.0}


def test_out_ycmh_chup_ket_qua(db, seed, cap_quyen, pr_full):
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all", read=True, write=True, approve=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    user = db.get(User, seed.u_nstm_id)
    pr_ser._out(db, pr_full, user)                   # lượt đầu nạp bộ nhớ đệm quyền
    with _QueryCounter(db) as qc:
        d = _plain(pr_ser._out(db, pr_full, user))
    assert list(d) == list(EXPECTED_PR_OUT)          # thứ tự khóa
    assert d == EXPECTED_PR_OUT
    assert qc.count == EXPECTED_PR_OUT_QUERIES


def test_out_ycmh_khong_nguoi_xem_chup_ket_qua(db, seed, pr_full):
    d = _plain(pr_ser._out(db, pr_full))
    assert list(d) == list(EXPECTED_PR_OUT_ANON)
    assert d == EXPECTED_PR_OUT_ANON


def test_out_ycmh_thieu_quyen_ncc_thi_che(db, seed, cap_quyen, pr_full):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    user = db.get(User, seed.u_req_id)
    d = pr_ser._out(db, pr_full, user)
    assert d["suggested_supplier"] == "" and d["suggested_supplier_tax_code"] == ""
    assert d["items"][0]["chosen_option"]["supplier_code"] == ""
    assert d["can_approve"] is False and d["can_dispatch"] is False


EXPECTED_PO_ITEM = {'id': 1,
 'product_code': 'SP1',
 'product_name': 'Hàng một',
 'invoice_name': 'Tên HĐ',
 'item_group': '',
 'spec': '',
 'fg_code': '',
 'fg_name': '',
 'invoice_no': '',
 'invoice_date': '',
 'document_delivery_date': '',
 'supplier_ready': False,
 'required_date': '',
 'expected_date': '',
 'pr_expected_date': '2026-12-01',
 'unit': 'Cái',
 'qty_request': 10.0,
 'qty_order': 10.0,
 'price': 12.5,
 'vat': 8.0,
 'amount': 135.0,
 'currency': 'USD',
 'exchange_rate': 25000.0,
 'base_amount': 135.0,
 'weight_kg': 2.5,
 'dimension': '',
 'qty_received': 4.0,
 'qty_remaining': 6.0,
 'line_status': '',
 'line_status_label': '',
 'warehouse_code': '',
 'note': '',
 'progress_status': 'not_ordered',
 'progress_status_label': 'Chưa đặt hàng',
 'pause_reason': '',
 'status_before_pause': 'ordered',
 'status_before_pause_label': 'Đã đặt hàng',
 'is_short_delivery': True,
 'order_total': 135.0,
 'goods_total': 1000.55,
 'paid_total': 400.0,
 'remaining_total': 600.55,
 'deliveries': [{'id': 1,
                 'delivery_no': 1,
                 'warehouse_code': '',
                 'carrier_code': '',
                 'carrier_name': '',
                 'ship_qty': 4.0,
                 'ship_unit': '',
                 'received_qty': 4.0,
                 'promised_date': '2026-11-10',
                 'expected_date': '',
                 'received_date': '',
                 'std_days': 0,
                 'regulated_date': '',
                 'diff_promise': 0,
                 'diff_regulated': 0,
                 'diff_required': 0,
                 'invoice_no': '',
                 'invoice_date': '',
                 'shipping_unit_price': 0.0,
                 'shipping_amount': 0.0,
                 'qc_result': '',
                 'status': 'received',
                 'status_label': 'Đã nhận',
                 'extra_request': '',
                 'progress_note': '',
                 'goods_total': 1000.555,
                 'paid': 400.0,
                 'remaining': 600.555},
                {'id': 2,
                 'delivery_no': 2,
                 'warehouse_code': '',
                 'carrier_code': '',
                 'carrier_name': '',
                 'ship_qty': 6.0,
                 'ship_unit': '',
                 'received_qty': 0.0,
                 'promised_date': '2026-11-20',
                 'expected_date': '',
                 'received_date': '',
                 'std_days': 0,
                 'regulated_date': '',
                 'diff_promise': 0,
                 'diff_regulated': 0,
                 'diff_required': 0,
                 'invoice_no': '',
                 'invoice_date': '',
                 'shipping_unit_price': 0.0,
                 'shipping_amount': 0.0,
                 'qc_result': '',
                 'status': '',
                 'status_label': '',
                 'extra_request': '',
                 'progress_note': '',
                 'goods_total': 0.0,
                 'paid': 0.0,
                 'remaining': 0.0}]}


def test_item_dmh_chup_ket_qua(db):
    po = PurchaseOrder(code="PO-715S", pr_code="PYC-1", status="approved", currency="USD", exchange_rate=25000)
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code="SP1", product_name="Hàng một", invoice_name="", unit="Cái",
                qty_request=10, qty_order=10, price=12.5, vat=8, amount=135, base_amount=0, currency="USD",
                exchange_rate=25000, qty_received=4, qty_remaining=6, progress_status="",
                status_before_pause="ordered", weight_kg=2.5)
    db.add(it)
    db.flush()
    d1 = PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, ship_qty=4, received_qty=4,
                    promised_date="2026-11-10", status="received")
    d2 = PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=2, ship_qty=6, promised_date="2026-11-20")
    db.add_all([d1, d2])
    db.commit()
    pay = {d1.id: SimpleNamespace(total=1000.555, paid_amount=400, remaining=600.555)}
    out = _plain(po_ser._item(db, it, pay, {"SP1": "Tên HĐ"}, {"SP1": "2026-12-01"}))
    out_bare = _plain(po_ser._item(db, it, {}))
    assert list(out) == list(EXPECTED_PO_ITEM)
    assert out == EXPECTED_PO_ITEM
    assert out_bare["invoice_name"] == "" and out_bare["pr_expected_date"] == ""
    assert out_bare["goods_total"] == 0.0 and out_bare["paid_total"] == 0.0
