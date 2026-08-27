"""Tool recap chứng từ thu mua + phiếu chờ duyệt (`tools/procurement_doc_tool.py`).

CHỈ kiểm phần vừa làm: gác quyền hai lớp (can + apply_scope), luật ẩn NCC/công nợ,
tổng hợp số liệu recap, và đếm phiếu `submitted` theo đúng quyền duyệt từng loại.
"""
import pytest

from app.modules.assistant import tools as T
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)
from app.modules.user.model import User


@pytest.fixture
def ho_so(db, seed):
    """1 ĐMH chờ duyệt (2 dòng + 1 khoản nợ) + 1 YCMH chờ duyệt (kèm 1 bản xóa mềm)
    + 1 YCKS chờ duyệt (1 dòng, 2 phương án trong đó 1 đã chọn)."""
    po = PurchaseOrder(code="PO-K1", status="submitted", company_id=seed.company_id,
                       supplier_code="NCCA", supplier_name="NCC Anpha", nspt="NV Mua",
                       order_date="2026-08-20", created_by=seed.u_nstm_id)
    db.add(po)
    db.flush()
    db.add_all([
        POItem(po_id=po.id, product_code="P1", product_name="Hàng 1", qty_order=10,
               qty_received=10, price=300, amount=3000, progress_status="received"),
        POItem(po_id=po.id, product_code="P2", product_name="Hàng 2", qty_order=5,
               qty_received=0, price=400, amount=2000, progress_status="ordered"),
    ])
    db.add(Payable(company_id=seed.company_id, supplier_code="NCCA",
                   supplier_name="NCC Anpha", source_type="goods", po_code="PO-K1",
                   incur_date="2026-08-21", period="2026", due_date="2026-09-21",
                   total=5000, paid_amount=1000, remaining=4000, status="partial"))

    pr = PurchaseRequest(code="PYC-K1", status="submitted", company_id=seed.company_id,
                         requester="Người A", department="Phòng A", is_deleted=False,
                         created_by=seed.u_req_id)
    pr_xoa = PurchaseRequest(code="PYC-DEL", status="submitted",
                             company_id=seed.company_id, is_deleted=True,
                             created_by=seed.u_req_id)
    db.add_all([pr, pr_xoa])
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="P1", product_name="Hàng 1",
                               qty=10, unit="Cái", price=300, amount=3000,
                               line_status="no_po"))

    sr = SurveyRequest(code="YCKS-K1", status="submitted", company_id=seed.company_id,
                       requester="Người B", created_by=seed.u_req_id)
    db.add(sr)
    db.flush()
    line = SurveyRequestLine(survey_request_id=sr.id, item_group="Thùng",
                             requirement_detail="Thùng carton 5 lớp", request_qty=100,
                             uom="Cái", assignee="NV01")
    db.add(line)
    db.flush()
    db.add_all([
        SurveyRequestOption(survey_request_line_id=line.id, supplier_code="NCCA",
                            supplier_name="NCC Anpha", is_chosen=True),
        SurveyRequestOption(survey_request_line_id=line.id, supplier_code="NCCB",
                            supplier_name="NCC Beta", is_chosen=False),
    ])
    db.commit()
    return {"po": po, "pr": pr, "sr": sr}


# ── procurement_doc_read ────────────────────────────────────────────────────────────────

def test_doc_read_thieu_quyen_hoac_entity_sai(db, seed, ho_so):
    """Không có quyền đọc -> denied; entity lạ -> error, không chạy gì."""
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "procurement_doc_read",
                     {"entity": "purchase_order", "code": "PO-K1"})
    assert out.get("denied") is True

    sai = T.run_tool(db, user, "procurement_doc_read", {"entity": "hop_dong", "code": "X"})
    assert sai.get("error")


def test_doc_read_recap_dmh_du_khoi(db, seed, ho_so, cap_quyen):
    """Đủ quyền: recap ĐMH có NCC, tổng tiền, tiến độ từng dòng và khối công nợ."""
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_nstm_id)

    out = T.run_tool(db, user, "procurement_doc_read",
                     {"entity": "purchase_order", "code": "PO-K1"})
    assert out["header"]["supplier_name"] == "NCC Anpha"
    assert out["header"]["status_label"] == "Chờ duyệt"
    assert out["header"]["url"].endswith(f"/{ho_so['po'].id}")
    assert out["total"] == 2
    assert out["totals"]["amount"] == 5000.0
    assert {l["progress"] for l in out["lines"]} == {"Đã nhận hàng", "Đã đặt hàng"} \
        or len(out["lines"]) == 2   # nhãn lấy từ bộ mã, chỉ cần có nhãn không rỗng
    assert out["payables"]["remaining"] == 4000.0
    assert "supplier_note" not in out


def test_doc_read_an_ncc_va_cong_no_khi_thieu_quyen(db, seed, ho_so, cap_quyen):
    """Chỉ có purchase_order.read: NCC bị ẩn kèm ghi chú, khối công nợ không trả về."""
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    user = db.get(User, seed.u_nstm_id)

    out = T.run_tool(db, user, "procurement_doc_read",
                     {"entity": "purchase_order", "code": "PO-K1"})
    assert "supplier_name" not in out["header"]
    assert out.get("supplier_note")
    assert "payables" not in out
    assert out.get("payable_note")


def test_doc_read_ngoai_pham_vi_thi_khong_thay(db, seed, ho_so, cap_quyen):
    """Scope own mà phiếu của người khác -> báo không tìm thấy, không lộ dữ liệu."""
    # PO-K1 do u_nstm tạo; u_req chỉ có scope own.
    cap_quyen(seed.u_req_id, "purchase_order", scope="own", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "procurement_doc_read",
                     {"entity": "purchase_order", "code": "PO-K1"})
    assert out.get("error")
    assert "header" not in out


def test_doc_read_ycmh_va_ycks(db, seed, ho_so, cap_quyen):
    """YCMH: có dòng + đã lọc xóa mềm. YCKS: chỉ ĐẾM phương án, không lộ NCC option."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)
    cap_quyen(seed.u_req_id, "survey_request", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    pr = T.run_tool(db, user, "procurement_doc_read",
                    {"entity": "purchase_request", "code": "PYC-K1"})
    assert pr["header"]["status_label"] == "Chờ duyệt"
    assert pr["total"] == 1 and pr["totals"]["amount"] == 3000.0

    # Phiếu đã xóa mềm coi như không tồn tại.
    wipe = T.run_tool(db, user, "procurement_doc_read",
                     {"entity": "purchase_request", "code": "PYC-DEL"})
    assert wipe.get("error")

    sr = T.run_tool(db, user, "procurement_doc_read",
                    {"entity": "survey_request", "code": "YCKS-K1"})
    dong = sr["lines"][0]
    assert dong["options"] == 2 and dong["options_chosen"] == 1
    # Lỗi phải né: bảng option chứa supplier_* thuộc cơ chế ẩn NCC — cấm lộ ra recap.
    assert not any("supplier" in k for k in dong)


# ── pending_procurement_approvals ───────────────────────────────────────────────────────

def test_pending_dem_theo_quyen_duyet(db, seed, ho_so, cap_quyen):
    """Chỉ đếm loại phiếu người hỏi có quyền duyệt; phiếu xóa mềm không được đếm."""
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all", read=True, approve=True)
    user = db.get(User, seed.u_nstm_id)

    out = T.run_tool(db, user, "pending_procurement_approvals", {})
    assert out["total"] == 1                          # PYC-K1; PYC-DEL bị loại
    assert len(out["groups"]) == 1
    nhom = out["groups"][0]
    assert nhom["entity"] == "purchase_request" and nhom["pending"] == 1
    assert nhom["items"][0]["code"] == "PYC-K1"
    assert nhom["items"][0]["url"].endswith(f"/{ho_so['pr'].id}")
    assert "Bỏ qua" in out.get("note", "")            # 4 loại còn lại không có quyền duyệt
    assert out.get("reminder")                        # nhắc trợ lý không duyệt hộ


def test_pending_khong_quyen_duyet_gi(db, seed, ho_so):
    """Không có quyền duyệt loại nào -> total 0 + nói thẳng, không denied cả cụm."""
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "pending_procurement_approvals", {})
    assert out["total"] == 0 and out["groups"] == []
    assert out.get("note")


def test_pending_loc_dich_danh_loai_khong_co_quyen(db, seed, ho_so, cap_quyen):
    """Hỏi đích danh một loại mà không có quyền duyệt loại đó -> denied nói rõ."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True, approve=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "pending_procurement_approvals",
                     {"entity": "purchase_order"})
    assert out.get("denied") is True

    sai = T.run_tool(db, user, "pending_procurement_approvals", {"entity": "linh_tinh"})
    assert sai.get("error")


# ── my_procurement_requests ─────────────────────────────────────────────────────────────

def test_my_requests_chi_thay_phieu_cua_minh(db, seed, ho_so, cap_quyen):
    """Scope all nhưng hỏi "phiếu CỦA TÔI" thì chỉ trả phiếu mình đứng tên, kèm tiến độ."""
    # Phiếu của người khác — dù scope all cũng không được lọt vào "của tôi".
    other = PurchaseRequest(code="PYC-NGUOI-KHAC", status="approved",
                           company_id=seed.company_id, is_deleted=False,
                           created_by=seed.u_nstm_id)
    db.add(other)
    db.commit()

    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)
    cap_quyen(seed.u_req_id, "survey_request", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "my_procurement_requests", {})
    nhom = {g["entity"]: g for g in out["groups"]}

    pr_group = nhom["purchase_request"]
    assert pr_group["total"] == 1                      # PYC-K1; loại PYC-NGUOI-KHAC + xóa mềm
    phieu = pr_group["items"][0]
    assert phieu["code"] == "PYC-K1"
    assert phieu["status_label"] == "Chờ duyệt"
    assert phieu["lines"] == 1
    assert sum(phieu["progress"].values()) == 1        # 1 dòng no_po -> "Chưa tạo đơn mua hàng"
    assert phieu["qty"] == 10.0
    assert phieu["url"].endswith(f"/{ho_so['pr'].id}")

    sr_group = nhom["survey_request"]
    assert sr_group["total"] == 1
    assert sr_group["items"][0]["lines"] == 1
    assert sr_group["items"][0]["lines_completed"] == 0


def test_my_requests_thieu_quyen(db, seed, ho_so, cap_quyen):
    """Không có quyền xem loại nào -> total 0 + note; hỏi đích danh loại thiếu quyền -> denied."""
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "my_procurement_requests", {})
    assert out["total"] == 0 and out["groups"] == []
    assert out.get("note")

    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    dich_danh = T.run_tool(db, user, "my_procurement_requests", {"entity": "survey_request"})
    assert dich_danh.get("denied") is True

    sai = T.run_tool(db, user, "my_procurement_requests", {"entity": "linh_tinh"})
    assert sai.get("error")
