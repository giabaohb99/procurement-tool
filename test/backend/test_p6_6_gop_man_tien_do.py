"""P6-6 (bao-CR-284) — gộp hai màn tiến độ thành "Tiến độ mua hàng" có bộ lọc theo bước
(doc/erp/12 §P6-6): đang so giá / đang mua / đang nhận hàng.

Ba mảnh backend được kiểm ở đây:

1. `_state_cond` của survey_progress phải biết HAI nhãn P6-3 thêm vào (`Đã lên đơn`,
   `Đã chốt phương án`). Trước bản vá: chọn hai nhãn đó là lặng lẽ KHÔNG lọc gì (nhãn
   lạ -> None), còn dòng đã lên đơn thẳng (po_code, pr_code rỗng) thì lọt vào các nhãn
   phía sau — chọn "Đã chọn phương án" kéo về cả dòng đã thành đơn từ lâu.
2. `phase=quoting` — bước "Đang so giá" của màn gộp: chỉ dòng CHƯA rời giai đoạn báo
   giá (chưa hoàn thành, chưa tạo YCMH, chưa lên đơn thẳng).
3. `step=` của purchase_progress — hai bước còn lại là NHÓM mã `progress_status`;
   `paused`/`cancelled` ngoài luồng nên chỉ hiện ở "Tất cả".
"""
from types import SimpleNamespace

from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_progress import controller as pp
from app.modules.survey_progress import controller as sp
from app.modules.survey_progress import export as ex
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)


def req(qs: str = ""):
    """Request giả — `_build_query` chỉ đọc `.query_params`."""
    return SimpleNamespace(query_params=QueryParams(qs))


def _user(db, user_id: int):
    from app.modules.user.model import User
    return db.get(User, user_id)


def _line(**kw) -> SurveyRequestLine:
    base = dict(survey_request_id=1, item_group="Bao bì", assignee="DEMONV",
                received_date="", result_due_date="", result_date="",
                line_status="", no_option=False, pr_code="", po_code="")
    base.update(kw)
    return SurveyRequestLine(**base)


# ── 1. `_state_cond` phủ đủ 11 nhãn, chia đúng, không trùng ─────────────────────

def test_moi_nhan_deu_co_dieu_kien_sql():
    """Nhãn nào `progress_state` trả ra được thì bộ lọc phải dịch được — None chỉ dành
    cho nhãn KHÔNG có thật. Trước P6-6 hai nhãn P6-3 rơi vào None mà không ai hay."""
    for state in ex.STATES:
        assert sp._state_cond(state) is not None, f"nhãn {state} chưa có điều kiện lọc"
    assert sp._state_cond("Nhan-khong-co-that") is None


def test_loc_tien_do_dong_chia_dung_du_11_nhan(db):
    """Bản mở rộng của test CR-075: mẫu có đủ cả dòng ĐÃ CHỐT PHƯƠNG ÁN lẫn dòng LÊN ĐƠN
    THẲNG. Mỗi dòng rơi vào đúng một nhãn, tổng các nhãn = tổng số dòng."""
    s = SurveyRequest(code="YCBG-P66", status="processing")
    db.add(s); db.flush()
    mau = [
        _line(survey_request_id=s.id, assignee=""),                                  # chưa tiếp nhận
        _line(survey_request_id=s.id),                                               # đã tiếp nhận
        _line(survey_request_id=s.id),                                               # đang khảo sát (PA bên dưới)
        _line(survey_request_id=s.id, result_date="2026-09-01"),                     # đã trả kết quả
        _line(survey_request_id=s.id, result_date="2026-09-01", no_option=True),     # chốt rỗng
        _line(survey_request_id=s.id, result_date="2026-09-01"),                     # đã chọn PA (PA chốt bên dưới)
        _line(survey_request_id=s.id, result_date="2026-09-01",
              line_status="confirmed"),                                              # ĐÃ CHỐT PHƯƠNG ÁN (P6-3)
        _line(survey_request_id=s.id, line_status="resurvey"),                       # cần khảo sát lại
        _line(survey_request_id=s.id, pr_code="PYC-P66", pr_id=66),                  # đã tạo YCMH
        _line(survey_request_id=s.id, po_code="PO-P66", po_id=66),                   # ĐÃ LÊN ĐƠN (P6-3)
        _line(survey_request_id=s.id, po_code="PO-P66B", po_id=67,
              line_status="completed"),                                              # hoàn thành thắng po_code
    ]
    db.add_all(mau); db.flush()
    db.add(SurveyRequestOption(survey_request_line_id=mau[2].id, public_id=1))
    db.add(SurveyRequestOption(survey_request_line_id=mau[5].id, public_id=1, is_chosen=True))
    db.commit()

    def label(ln):
        opts = db.query(SurveyRequestOption).filter(
            SurveyRequestOption.survey_request_line_id == ln.id).all()
        return ex.progress_state(ln, any(o.is_chosen for o in opts), len(opts))

    mong_doi = {}
    for ln in mau:
        mong_doi.setdefault(label(ln), set()).add(ln.id)

    total = 0
    for state in ex.STATES:
        ids = {r.id for r in db.query(SurveyRequestLine).filter(sp._state_cond(state)).all()}
        assert ids == mong_doi.get(state, set()), f"lệch ở nhãn {state}"
        total += len(ids)
    assert total == len(mau)


def test_dong_len_don_thang_khong_lot_nhan_phia_sau(db):
    """Lỗi cũ: dòng lên đơn thẳng (po_code, pr_code rỗng) vẫn còn phương án chốt trong DB,
    chuỗi lọc không loại po_code nên chọn "Đã chọn phương án" là nó hiện về."""
    s = SurveyRequest(code="YCBG-P66C", status="processing")
    db.add(s); db.flush()
    ln = _line(survey_request_id=s.id, result_date="2026-09-01", po_code="PO-TRUC-TIEP", po_id=99)
    db.add(ln); db.flush()
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=True))
    db.commit()

    ids_chosen = {r.id for r in db.query(SurveyRequestLine)
                  .filter(sp._state_cond(ex.STATE_CHOSEN)).all()}
    ids_po = {r.id for r in db.query(SurveyRequestLine)
              .filter(sp._state_cond(ex.STATE_PO_CREATED)).all()}
    assert ln.id not in ids_chosen
    assert ln.id in ids_po


# ── 2. Bước "Đang so giá": `phase=quoting` trên /api/survey-progress ────────────

def _sr_codes(db, user, qs: str = "") -> set[str]:
    prof = get_perm_profile(db, user)
    q = sp._build_query(req(qs), db, user, prof, True)
    return {ln.internal_line_code for _s, ln in q.all()}


def test_phase_quoting_chi_lay_dong_chua_roi_giai_doan_bao_gia(db, seed, grant_role):
    grant_role(seed.u_nstm_id, "survey_request", scope="all", read=True)
    s = SurveyRequest(code="YCBG-P66Q", status="processing")
    db.add(s); db.flush()
    db.add_all([
        _line(survey_request_id=s.id, internal_line_code="CON-KHAO-SAT"),
        _line(survey_request_id=s.id, internal_line_code="DA-CHOT-PA",
              line_status="confirmed", result_date="2026-09-01"),
        _line(survey_request_id=s.id, internal_line_code="KHAO-SAT-LAI",
              line_status="resurvey"),
        _line(survey_request_id=s.id, internal_line_code="DA-TAO-YCMH", pr_code="PYC-Q"),
        _line(survey_request_id=s.id, internal_line_code="DA-LEN-DON", po_code="PO-Q"),
        _line(survey_request_id=s.id, internal_line_code="HOAN-THANH",
              line_status="completed"),
    ])
    db.commit()
    user = _user(db, seed.u_nstm_id)

    assert _sr_codes(db, user, "phase=quoting") == {"CON-KHAO-SAT", "DA-CHOT-PA",
                                                    "KHAO-SAT-LAI"}
    # Không truyền phase (hoặc phase lạ) thì màn cũ vẫn thấy đủ — đường lùi cho v1.
    assert len(_sr_codes(db, user)) == 6
    assert len(_sr_codes(db, user, "phase=khong-co")) == 6


# ── 3. Bước "Đang mua" / "Đang nhận hàng": `step=` trên /api/purchase-progress ──

def _po_with_status(db, code: str, progress: str):
    po = PurchaseOrder(code=code, status="approved", order_date="2026-09-01")
    db.add(po); db.flush()
    db.add(POItem(po_id=po.id, product_code=f"SP-{code}", qty_order=1, price=100,
                  progress_status=progress))
    db.commit()


def _po_codes(db, user, qs: str = "") -> set[str]:
    prof = get_perm_profile(db, user)
    q = pp._build_query(req(qs), db, user, prof, pp._po_scope(db, user), True)
    return {po.code for po, _it, _dl in q.all()}


def test_step_chia_dung_nhom_ma_tien_do(db, seed, grant_role):
    grant_role(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    for code, progress in [("PO-CHUA-DAT", "not_ordered"), ("PO-DA-DAT", "ordered"),
                           ("PO-DA-NHAN", "received"), ("PO-CHO-HS", "doc_pending"),
                           ("PO-DA-GUI-HS", "doc_sent"), ("PO-XONG", "completed"),
                           ("PO-TAM-NGUNG", "paused"), ("PO-HUY", "cancelled")]:
        _po_with_status(db, code, progress)
    user = _user(db, seed.u_nstm_id)

    assert _po_codes(db, user, "step=purchasing") == {"PO-CHUA-DAT", "PO-DA-DAT"}
    assert _po_codes(db, user, "step=receiving") == {"PO-DA-NHAN", "PO-CHO-HS",
                                                     "PO-DA-GUI-HS"}
    # "Tất cả" (không step / step lạ): đủ 8 đơn, kể cả ngoại lệ paused/cancelled.
    assert len(_po_codes(db, user)) == 8
    assert len(_po_codes(db, user, "step=khong-co")) == 8


def test_step_ket_hop_duoc_voi_loc_trang_thai_don_le(db, seed, grant_role):
    """`status=` (một mã) và `step=` (nhóm mã) là hai ô độc lập — giao nhau chứ không đè."""
    grant_role(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    _po_with_status(db, "PO-S1", "ordered")
    _po_with_status(db, "PO-S2", "received")
    user = _user(db, seed.u_nstm_id)
    assert _po_codes(db, user, "step=purchasing&status=ordered") == {"PO-S1"}
    assert _po_codes(db, user, "step=receiving&status=ordered") == set()
