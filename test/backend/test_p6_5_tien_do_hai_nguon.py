"""P6-5 (bao-CR-283) — màn Tiến độ mua hàng đọc CẢ HAI nguồn (doc/erp/12 §P6-5).

Giai đoạn chuyển tiếp: đơn cũ vẫn bám YCMH qua `pr_code`, đơn mới (luồng YCBG gộp)
bám phiếu qua `survey_code` — `pr_code` để RỖNG, giữ nguyên ý nghĩa "mã YCMH nguồn".
Màn Tiến độ trước P6-5 chỉ biết một nguồn, thành ra ba lỗ:

1. Cổng quyền: người chỉ có `survey_request.read` (phòng yêu cầu đi luồng gộp,
   không còn YCMH) ăn 403 dù đơn sinh từ phiếu của chính họ.
2. Phạm vi lùi (không có `purchase_order.read`): chỉ khớp `pr_code` theo YCMH
   trong phạm vi — đơn lên thẳng từ YCBG vô hình với chính người yêu cầu.
3. Hàng dữ liệu / tìm kiếm / sort: không có `survey_code` — nhìn thấy đơn cũng
   không biết nó từ phiếu nào.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.purchase_progress import export as pp_ex
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import SurveyRequest


def req(qs: str = ""):
    """Request giả — `_build_query` chỉ đọc `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


def _user(db, user_id: int):
    from app.modules.user.model import User
    return db.get(User, user_id)


def _po(db, code: str, pr_code: str = "", survey_code: str = "", **kw):
    po = PurchaseOrder(code=code, status="approved", pr_code=pr_code,
                       survey_code=survey_code, order_date="2026-09-01", **kw)
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code=f"SP-{code}", qty_order=5, price=1000)
    db.add(it)
    db.commit()
    return po


def _codes(db, user, qs: str = "") -> set[str]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(qs), db, user, prof, pp._po_scope(db, user), True)
    return {po.code for po, _it, _dl in q.all()}


# ── 1. Cổng quyền nhận cả survey_request ─────────────────────────────────────────

def test_cong_quyen_nhan_survey_request_read(db, seed, grant_role):
    """Người chỉ có `survey_request.read` phải qua được cổng — luồng gộp không còn YCMH."""
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True)
    user = _user(db, seed.u_req_id)
    assert pp._require_progress(user=user, db=db) is user


def test_cong_quyen_khong_quyen_nao_van_403(db, seed):
    with pytest.raises(HTTPException) as e:
        pp._require_progress(user=_user(db, seed.u_req_id), db=db)
    assert e.value.status_code == 403


def test_cong_xuat_nhan_survey_request_export(db, seed, grant_role):
    grant_role(seed.u_req_id, "survey_request", scope="own", export=True)
    user = _user(db, seed.u_req_id)
    assert pp._require_progress_export(user=user, db=db) is user
    with pytest.raises(HTTPException):
        pp._require_progress_export(user=_user(db, seed.u_nstm_id), db=db)


# ── 2. Phạm vi lùi hợp HAI nguồn ─────────────────────────────────────────────────

@pytest.fixture
def two_sources(db, seed):
    """Người yêu cầu (u_req) có 1 YCMH + 1 YCBG của mình; người khác (nstm) cũng vậy."""
    db.add_all([
        PurchaseRequest(code="PR-CUA-TOI", status="approved", created_by=seed.u_req_id),
        PurchaseRequest(code="PR-NGUOI-KHAC", status="approved", created_by=seed.u_nstm_id),
        SurveyRequest(code="SR-CUA-TOI", status="pr_created", created_by=seed.u_req_id),
        SurveyRequest(code="SR-NGUOI-KHAC", status="pr_created", created_by=seed.u_nstm_id),
    ])
    db.commit()
    _po(db, "PO-TU-PR", pr_code="PR-CUA-TOI")
    _po(db, "PO-TU-SR", survey_code="SR-CUA-TOI")            # đơn LÊN THẲNG từ YCBG
    _po(db, "PO-PR-KHAC", pr_code="PR-NGUOI-KHAC")
    _po(db, "PO-SR-KHAC", survey_code="SR-NGUOI-KHAC")


def test_pham_vi_lui_hop_ca_hai_nguon(db, seed, grant_role, two_sources):
    """Không có `purchase_order.read`: thấy đơn từ YCMH của mình VÀ đơn lên thẳng
    từ YCBG của mình — trước P6-5 cái sau vô hình."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True)
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True)
    assert _codes(db, _user(db, seed.u_req_id)) == {"PO-TU-PR", "PO-TU-SR"}


def test_pham_vi_lui_chi_co_survey_request(db, seed, grant_role, two_sources):
    """Chỉ có `survey_request.read` (luồng gộp thuần): thấy đúng đơn từ phiếu mình."""
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True)
    assert _codes(db, _user(db, seed.u_req_id)) == {"PO-TU-SR"}


def test_pham_vi_lui_khong_thay_don_nguoi_khac(db, seed, grant_role, two_sources):
    """Đơn từ phiếu/YCMH người khác vẫn khuất — nới nguồn không được nới người."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True)
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True)
    codes = _codes(db, _user(db, seed.u_req_id))
    assert "PO-PR-KHAC" not in codes and "PO-SR-KHAC" not in codes


def test_pham_vi_lui_rong_ca_hai_thi_khong_thay_gi(db, seed, grant_role, two_sources):
    """Không phiếu nào trong phạm vi ở CẢ HAI nguồn -> danh sách rỗng, không phải thấy hết."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True)
    from app.modules.user.model import User
    u_backup = db.query(User).filter(User.email == "BACKUP01").one()
    grant_role(u_backup.id, "purchase_request", scope="own", read=True)
    assert _codes(db, u_backup) == set()


def test_po_scope_day_du_khong_bi_anh_huong(db, seed, grant_role, two_sources):
    """Có `purchase_order.read` scope all: vẫn đi theo phạm vi ĐMH, thấy cả bốn đơn."""
    grant_role(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    assert _codes(db, _user(db, seed.u_nstm_id)) == {
        "PO-TU-PR", "PO-TU-SR", "PO-PR-KHAC", "PO-SR-KHAC"}


# ── 3. survey_code trên hàng / tìm kiếm / sort / Excel ──────────────────────────

def test_row_values_co_survey_code(db, seed):
    po = _po(db, "PO-ROW", survey_code="SR-ROW")
    it = db.query(POItem).filter(POItem.po_id == po.id).one()
    r = pp_ex.row_values(po, it, None, True)
    assert r["survey_code"] == "SR-ROW"
    # survey_code KHÔNG phải dữ liệu NCC — người bị che NCC vẫn phải thấy nguồn đơn
    assert pp_ex.row_values(po, it, None, False)["survey_code"] == "SR-ROW"


def test_tim_kiem_theo_ma_ycbg(db, seed, grant_role, two_sources):
    grant_role(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    user = _user(db, seed.u_nstm_id)
    assert _codes(db, user, "q=SR-CUA-TOI") == {"PO-TU-SR"}


def test_sort_va_loc_dieu_kien_co_survey_code(db, seed):
    """`survey_code` vào `_sort_map` là tự chảy xuống `_cond_map` (CR-080) — cột
    nguồn đơn không thuộc cụm NCC nên không bị gỡ khi thiếu `supplier.read`."""
    assert pp._sort_map()["survey_code"] is PurchaseOrder.survey_code
    assert "survey_code" in pp._cond_map(True)
    assert "survey_code" in pp._cond_map(False)


def test_excel_tien_do_co_cot_ma_ycbg_con_excel_dmh_thi_khong(db, seed):
    """Cột `Mã YCBG` vào file xuất màn Tiến độ; file xuất màn ĐMH mượn chung `COLS`
    (CR-068) nhưng đầu phiếu đã tự khai nguồn nên khối DÒNG không nhận thêm cột này."""
    from app.modules.purchase_order import export as po_ex
    assert any(c.key == "survey_code" for c in pp_ex.columns_for(True))
    assert any(c.key == "survey_code" for c in pp_ex.columns_for(False))
    assert not any(c.key == "survey_code" for c in po_ex.LINE_COLS)
