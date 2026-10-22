"""ai-CR-176 — đợt 2b xóa MỀM cho cụm THU MUA: Đơn mua hàng (ĐMH) · Yêu cầu thanh toán (YCTT) ·
Phiếu khảo sát (PKS). Cùng khuôn với `test_ycbg_xoa_mem.py` (ai-CR-170).

Bài này chốt cho CẢ BA chứng từ:

  1. xóa qua API → phiếu còn trong DB (cờ + mốc + người xóa), dòng con GIỮ NGUYÊN;
  2. phiếu đã xóa biến khỏi danh sách · chi tiết · xuất Excel · xóa lô · nhân bản · in;
  3. xóa lần hai 404; luật trạng thái cũ vẫn chặn (400);
  4. mã phiếu không tái dùng (mã theo id, bản ghi đã xóa vẫn giữ chỗ);
  5. trang chủ + công cụ Trợ lý bỏ qua phiếu đã xóa;
  6. liên kết chéo coi phiếu đã xóa như không có: YCMH ↔ ĐMH (`sync_from_purchase_orders`), YCBG ↔ PKS
     (`available_survey_lines`, `sync_options_from_surveys`), ĐMH ↔ YCTT (hủy duyệt đơn), báo cáo ĐMH;
  7. đính kèm treo vào phiếu đã xóa → 404; chuỗi chứng từ bỏ PKS đã xóa;
  8. nhập liệu: hoàn tác lô PKS / ĐMH = xóa mềm (giữ dòng); mã trùng phiếu đã xóa → `doc_deleted`.

Dựng dữ liệu bằng `scope_factory` (fixture `world`) để hồ sơ quyền là hồ sơ thật.
"""
import json
from datetime import datetime
from io import BytesIO

import openpyxl
import pytest
from fastapi import HTTPException
from starlette.datastructures import QueryParams

from app.core.scoping import apply_scope, get_scoped, not_deleted_cond
from app.modules.payment_request import service as prq_service
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.survey import service as sv_service
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine

_PG = {"offset": 0, "limit": 100}
_ALL_ACTIONS = ("read", "create", "write", "delete", "export", "approve", "print")


class _Req:
    """Chỉ cần `query_params` thật (`apply_filters` / `collect_conditions_map` gọi `multi_items()`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _body(resp) -> dict:
    return json.loads(resp.body)


def _xlsx_cells(resp) -> set[str]:
    wb = openpyxl.load_workbook(BytesIO(resp.body))
    return {str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None}


# ── dựng dữ liệu ──────────────────────────────────────────────────────────────────────────

def _make_po(db, *, code, company_id, department_id, created_by, status="draft", pr_code="",
             with_line=True) -> PurchaseOrder:
    po = PurchaseOrder(code=code, company_id=company_id, department_id=department_id, department="",
                       pr_code=pr_code, supplier_code="NX", supplier_name="NCC Nam Xuân",
                       order_date="2026-10-01", status=status, created_by=created_by, updated_by=created_by)
    db.add(po)
    db.flush()
    if with_line:
        db.add(POItem(po_id=po.id, product_code="SP1", product_name="Hàng SP1", unit="Cái", qty_order=10,
                      price=1000, created_by=created_by, updated_by=created_by))
    db.commit()
    return po


def _make_prq(db, *, code, company_id, department_id, created_by, status="draft", po_code="",
              with_line=True) -> PaymentRequest:
    req = PaymentRequest(code=code, company_id=company_id, department_id=department_id, supplier_code="NX",
                         supplier_name="NCC Nam Xuân", status=status, total=100, request_date="2026-10-01",
                         created_by=created_by, updated_by=created_by)
    db.add(req)
    db.flush()
    if with_line:
        db.add(PaymentRequestLine(request_id=req.id, po_code=po_code, invoice_no="HD-1", amount=100,
                                  created_by=created_by, updated_by=created_by))
    db.commit()
    return req


def _make_survey(db, *, code, created_by, status="draft", survey_request_id=0, sr_code="",
                 item_group="Nhãn", with_line=True) -> Survey:
    s = Survey(code=code, survey_type="combined", status=status, item_group=item_group,
               main_content=f"Khảo sát {code}", survey_request_id=survey_request_id, sr_code=sr_code,
               received_date="2026-10-01", created_by=created_by, updated_by=created_by)
    db.add(s)
    db.flush()
    if with_line:
        db.add(SurveySupplierLine(survey_id=s.id, supplier_code="NX", supplier_name="NCC Nam Xuân",
                                  contact_date="2026-10-02", created_by=created_by, updated_by=created_by))
        db.add(SurveyProductLine(survey_id=s.id, supplier_code="NX", product_name="Decal A",
                                 internal_code="DECAL-A", line_approve="Đã duyệt", contact_date="2026-10-02",
                                 price_by_volume=1000, created_by=created_by, updated_by=created_by))
    db.commit()
    return s


@pytest.fixture
def actor(world):
    """`a1` thấy TẤT (scope `all`) với đủ hành động trên cả ba entity — mọi khẳng định «không thấy»
    ở dưới chỉ có thể do cờ xóa mềm, không phải do phạm vi vai trò."""
    a1 = world.actor("a1")
    for entity in ("purchase_order", "payment_request", "survey"):
        a1.grant(entity, scope="all", actions=_ALL_ACTIONS)
    return a1


@pytest.fixture
def phieu(world, actor):
    """Mỗi chứng từ hai phiếu nháp của a1 ở pháp nhân A: `xoa` sẽ bị xóa mềm, `giu` ở lại nguyên."""
    db, uid = world.db, actor.user.id
    A, dept = world.co["A"], world.dept["A.kt"]
    return {
        "po": {"xoa": _make_po(db, code="PO_XOA", company_id=A, department_id=dept, created_by=uid).id,
               "giu": _make_po(db, code="PO_GIU", company_id=A, department_id=dept, created_by=uid).id},
        "prq": {"xoa": _make_prq(db, code="YCTT_XOA", company_id=A, department_id=dept, created_by=uid).id,
                "giu": _make_prq(db, code="YCTT_GIU", company_id=A, department_id=dept, created_by=uid).id},
        "sv": {"xoa": _make_survey(db, code="KS_XOA", created_by=uid).id,
               "giu": _make_survey(db, code="KS_GIU", created_by=uid).id},
    }


def _assert_soft_deleted(row, user_id: int, since: datetime) -> None:
    assert row is not None, "bản ghi phải CÒN trong DB"
    assert row.is_deleted is True
    assert row.deleted_at is not None and row.deleted_at >= since.replace(microsecond=0)
    assert row.deleted_by == user_id


# ═══════════════════════════════ 1 + 2 + 3: ĐMH ═══════════════════════════════════════════

def test_dmh_xoa_mem_qua_api_con_trong_db_bien_khoi_moi_cua_doc(world, actor, phieu):
    from app.modules.purchase_order import controller as po_ctl

    db, user = world.db, actor.user
    pid, keep = phieu["po"]["xoa"], phieu["po"]["giu"]
    n_items = db.query(POItem).filter(POItem.po_id == pid).count()
    assert n_items == 1

    truoc = datetime.utcnow()
    assert _body(po_ctl.delete_po(pid, db, user))["message"] == "Đã xóa"

    _assert_soft_deleted(db.get(PurchaseOrder, pid), user.id, truoc)
    assert db.query(POItem).filter(POItem.po_id == pid).count() == n_items, "dòng hàng không bị xóa theo"

    with pytest.raises(HTTPException) as e:
        po_service.get_po(db, pid)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        po_ctl.get_po(pid, db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        po_ctl._in_scope(db, pid, user, "read")
    assert e.value.status_code == 404
    for fn in (po_ctl.clone_po, po_ctl.print_po):
        with pytest.raises(HTTPException) as e:
            fn(pid, db, user)
        assert e.value.status_code == 404

    ids_list = {r.id for r in po_ctl._list_query(_Req(), db, user).all()}
    assert pid not in ids_list and keep in ids_list
    cells = _xlsx_cells(po_ctl.export_xlsx(_Req(), "", "", db, user))
    assert "PO_GIU" in cells and "PO_XOA" not in cells

    with pytest.raises(HTTPException) as e:
        po_ctl.bulk_delete_pos(str(pid), db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        po_ctl.delete_po(pid, db, user)                 # xóa lần hai: coi như không có
    assert e.value.status_code == 404

    other = db.get(PurchaseOrder, keep)
    assert other.is_deleted is False and other.deleted_at is None and other.deleted_by == 0
    assert _body(po_ctl.get_po(keep, db, user))["data"]["code"] == "PO_GIU"


def test_dmh_luat_trang_thai_giu_nguyen(world, actor, phieu):
    db, user = world.db, actor.user
    po = db.get(PurchaseOrder, phieu["po"]["giu"])
    po.status = "approved"
    db.commit()
    with pytest.raises(HTTPException) as e:
        po_service.delete_po(db, po.id, user.id)
    assert e.value.status_code == 400
    assert db.get(PurchaseOrder, po.id).is_deleted is False


# ═══════════════════════════════ 1 + 2 + 3: YCTT ══════════════════════════════════════════

def test_yctt_xoa_mem_qua_api_con_trong_db_bien_khoi_moi_cua_doc(world, actor, phieu):
    from app.modules.payment_request import controller as prq_ctl

    db, user = world.db, actor.user
    rid, keep = phieu["prq"]["xoa"], phieu["prq"]["giu"]
    assert db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).count() == 1

    truoc = datetime.utcnow()
    assert _body(prq_ctl.delete_(rid, db, user))["message"] == "Đã xóa"

    _assert_soft_deleted(db.get(PaymentRequest, rid), user.id, truoc)
    assert db.query(PaymentRequestLine).filter(PaymentRequestLine.request_id == rid).count() == 1

    with pytest.raises(HTTPException) as e:
        prq_service.get_request(db, rid)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        prq_ctl.get_(rid, db, user)
    assert e.value.status_code == 403
    for action in ("read", "print", "delete"):
        with pytest.raises(HTTPException) as e:
            prq_ctl._scoped(db, rid, user, action)
        assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        prq_ctl.print_(rid, db, user)
    assert e.value.status_code == 404

    ids_list = {r.id for r in prq_ctl._list_query(db, _Req(), user).all()}
    assert rid not in ids_list and keep in ids_list
    cells = _xlsx_cells(prq_ctl.export_xlsx(_Req(), db, user))
    assert "YCTT_GIU" in cells and "YCTT_XOA" not in cells

    with pytest.raises(HTTPException) as e:
        prq_ctl.bulk_delete_requests(str(rid), db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        prq_ctl.delete_(rid, db, user)
    assert e.value.status_code == 404

    other = db.get(PaymentRequest, keep)
    assert other.is_deleted is False and other.deleted_at is None and other.deleted_by == 0
    assert _body(prq_ctl.get_(keep, db, user))["data"]["code"] == "YCTT_GIU"


def test_yctt_luat_trang_thai_giu_nguyen(world, actor, phieu):
    db, user = world.db, actor.user
    req = db.get(PaymentRequest, phieu["prq"]["giu"])
    req.status = "submitted"
    db.commit()
    with pytest.raises(HTTPException) as e:
        prq_service.delete_request(db, req.id, user.id)
    assert e.value.status_code == 400
    assert db.get(PaymentRequest, req.id).is_deleted is False


# ═══════════════════════════════ 1 + 2 + 3: PKS ═══════════════════════════════════════════

def test_pks_xoa_mem_qua_api_con_trong_db_bien_khoi_moi_cua_doc(world, actor, phieu):
    from app.modules.survey import controller as sv_ctl

    db, user = world.db, actor.user
    sid, keep = phieu["sv"]["xoa"], phieu["sv"]["giu"]
    assert db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sid).count() == 1
    assert db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == sid).count() == 1

    truoc = datetime.utcnow()
    assert _body(sv_ctl.delete_(sid, db, user))["message"] == "Đã xóa"

    _assert_soft_deleted(db.get(Survey, sid), user.id, truoc)
    assert db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sid).count() == 1
    assert db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == sid).count() == 1

    with pytest.raises(HTTPException) as e:
        sv_service.get_survey(db, sid)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        sv_ctl.get_(sid, db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        sv_ctl._in_scope(db, sid, user, "read")
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        sv_ctl.clone_(sid, db, user)
    assert e.value.status_code == 404

    ids_list = {x["id"] for x in _body(sv_ctl.list_surveys(_Req(), _PG, db, user))["data"]["items"]}
    assert sid not in ids_list and keep in ids_list

    with pytest.raises(HTTPException) as e:
        sv_ctl.bulk_delete_surveys(str(sid), db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        sv_ctl.delete_(sid, db, user)
    assert e.value.status_code == 404

    other = db.get(Survey, keep)
    assert other.is_deleted is False and other.deleted_at is None and other.deleted_by == 0
    assert _body(sv_ctl.get_(keep, db, user))["data"]["code"] == "KS_GIU"


def test_pks_luat_trang_thai_giu_nguyen(world, actor, phieu):
    from app.modules.survey import controller as sv_ctl

    db, user = world.db, actor.user
    s = db.get(Survey, phieu["sv"]["giu"])
    s.status = "submitted"
    db.commit()
    with pytest.raises(HTTPException) as e:
        sv_ctl.delete_(s.id, db, user)
    assert e.value.status_code == 400
    assert db.get(Survey, s.id).is_deleted is False


# ═══════════════════════════════ 4: mã không tái dùng ═════════════════════════════════════

def test_ma_phieu_khong_tai_dung_sau_khi_xoa(world, actor, phieu):
    """Ba chứng từ sinh mã theo id (`PO{id:05d}` / `YCTT{id:05d}` / `KS{id:05d}`): bản ghi đã xóa
    mềm vẫn nằm trong bảng nên id mới luôn lớn hơn — mã cũ không bao giờ được cấp lại."""
    db, user = world.db, actor.user
    po_service.delete_po(db, phieu["po"]["xoa"], user.id)
    prq_service.delete_request(db, phieu["prq"]["xoa"], user.id)
    sv_service.delete_survey(db, phieu["sv"]["xoa"], user.id)

    for model, key in ((PurchaseOrder, "po"), (PaymentRequest, "prq"), (Survey, "sv")):
        old = db.get(model, phieu[key]["xoa"])
        assert old is not None and old.code, "phiếu đã xóa vẫn giữ chỗ cùng mã trong bảng"
        assert db.query(model).filter(model.code == old.code).count() == 1
        new = model(code="", created_by=user.id, updated_by=user.id,
                    **({"survey_type": "combined"} if model is Survey else {}))
        db.add(new)
        db.flush()
        assert new.id > old.id


# ═══════════════════════════════ 5: trang chủ + Trợ lý ════════════════════════════════════

def test_trang_chu_bo_qua_phieu_da_xoa(world, actor, phieu):
    from app.modules.dashboard.controller import build_my_tasks, overview

    db, user = world.db, actor.user
    po_service.delete_po(db, phieu["po"]["xoa"], user.id)
    sv_service.delete_survey(db, phieu["sv"]["xoa"], user.id)
    for key, model in (("po", PurchaseOrder), ("sv", Survey)):
        for sid in phieu[key].values():
            db.get(model, sid).status = "submitted"          # cả hai «chờ duyệt», một đã xóa
    db.commit()

    data = _body(overview(db, user))["data"]
    assert data["kpi"]["survey_pending"] == 1
    assert [x["code"] for x in data["pending_surveys_list"]] == ["KS_GIU"]

    tasks = build_my_tasks(db, user, actor.profile())
    assert {t["code"] for t in tasks if t["type"] == "po"} == {"PO_GIU"}


def test_tool_tro_ly_khong_thay_phieu_da_xoa(world, actor, phieu):
    from app.modules.assistant import tools as T
    from app.modules.assistant.tools.update_tool import _fetch_by_code

    db, user = world.db, actor.user
    po_service.delete_po(db, phieu["po"]["xoa"], user.id)
    prq_service.delete_request(db, phieu["prq"]["xoa"], user.id)
    sv_service.delete_survey(db, phieu["sv"]["xoa"], user.id)

    doc = T.run_tool(db, user, "procurement_doc_read", {"entity": "purchase_order", "code": "PO_XOA"})
    assert doc.get("error") and "Không tìm thấy" in doc["error"]
    assert T.run_tool(db, user, "procurement_doc_read",
                      {"entity": "purchase_order", "code": "PO_GIU"})["header"]["code"] == "PO_GIU"

    yctt = T.run_tool(db, user, "payment_request_read", {"code": "YCTT_XOA"})
    assert yctt.get("error") and "Không tìm thấy" in yctt["error"]
    assert T.run_tool(db, user, "payment_request_read", {"code": "YCTT_GIU"})["code"] == "YCTT_GIU"

    de_xuat = T.run_tool(db, user, "propose_document_delete", {"entity": "payment_request", "code": "YCTT_XOA"})
    assert de_xuat.get("error")
    assert _fetch_by_code(db, "payment_request", "YCTT_XOA", user, actor.profile(), action="read") is None
    assert _fetch_by_code(db, "payment_request", "YCTT_GIU", user, actor.profile(), action="read") is not None

    #  Phiếu chờ duyệt: ba loại cùng «submitted», mỗi loại một phiếu đã xóa → chỉ còn phiếu sống.
    for key, model in (("po", PurchaseOrder), ("prq", PaymentRequest), ("sv", Survey)):
        for sid in phieu[key].values():
            db.get(model, sid).status = "submitted"
    db.commit()
    pending = T.run_tool(db, user, "pending_procurement_approvals", {})
    by_entity = {g["entity"]: g for g in pending["groups"]}
    assert by_entity["purchase_order"]["pending"] == 1
    assert by_entity["payment_request"]["pending"] == 1
    assert by_entity["survey"]["pending"] == 1
    codes = {it.get("code") for g in pending["groups"] for it in g["items"]}
    assert codes & {"PO_XOA", "YCTT_XOA", "KS_XOA"} == set()


# ═══════════════════════════════ lọc tập trung ở core/scoping ═════════════════════════════

def test_apply_scope_va_get_scoped_tu_loc_ca_ba_model(world, actor, phieu):
    db, user, prof = world.db, actor.user, actor.profile()
    po_service.delete_po(db, phieu["po"]["xoa"], user.id)
    prq_service.delete_request(db, phieu["prq"]["xoa"], user.id)
    sv_service.delete_survey(db, phieu["sv"]["xoa"], user.id)

    for model, entity, key in ((PurchaseOrder, "purchase_order", "po"),
                               (PaymentRequest, "payment_request", "prq"),
                               (Survey, "survey", "sv")):
        assert not_deleted_cond(model) is not None, f"{model.__name__} phải có cột is_deleted"
        seen = {r.id for r in apply_scope(db.query(model), model, entity, user, prof).all()}
        assert seen == {phieu[key]["giu"]}, entity
        assert get_scoped(db, model, entity, phieu[key]["xoa"], user, prof) is None
        assert get_scoped(db, model, entity, phieu[key]["giu"], user, prof) is not None


# ═══════════════════════════════ 6: liên kết chéo ═════════════════════════════════════════

def test_ycmh_coi_dmh_da_xoa_nhu_khong_co(world, actor):
    """`sync_from_purchase_orders`: đơn đã xóa mềm không tính → dòng YCMH quay về «Chưa tạo đơn»;
    đơn Nháp vẫn đứng (luật CR-074) thì không về."""
    from app.modules.purchase_request.service import LINE_STATUS_NO_PO, sync_from_purchase_orders
    from test_pr_line_no_po_cr074 import _pr

    db, user = world.db, actor.user
    _, rows = _pr(db, code="PYC_XM", products=("SP1",))
    po = _make_po(db, code="PO_PYC", company_id=world.co["A"], department_id=world.dept["A.kt"],
                  created_by=user.id, pr_code="PYC_XM")
    sync_from_purchase_orders(db, "PYC_XM")
    db.refresh(rows[0])
    assert rows[0].line_status != LINE_STATUS_NO_PO, "đơn Nháp còn sống thì dòng YCMH không phải «chưa tạo đơn»"

    po_service.delete_po(db, po.id, user.id)      # tự gọi `_sync_pr`
    db.refresh(rows[0])
    assert rows[0].line_status == LINE_STATUS_NO_PO


def test_ycbg_coi_pks_da_xoa_nhu_khong_co(world, actor, phieu):
    from app.modules.survey_request import service as sr_service
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine, SurveyRequestOption

    db, user = world.db, actor.user
    sr = SurveyRequest(code="YCBG_PKS", company_id=world.co["A"], department_id=world.dept["A.kt"],
                       department="", requester_id=0, status="processing", purpose="x",
                       created_by=user.id, updated_by=user.id)
    db.add(sr)
    db.flush()
    db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhãn", request_qty=1,
                             requirement_detail="Decal", created_by=user.id))
    for sid in phieu["sv"].values():
        s = db.get(Survey, sid)
        s.survey_request_id, s.sr_code = sr.id, sr.code
    db.commit()

    items, total = sr_service.available_survey_lines(db, supplier_code="NX", item_group="Nhãn")
    assert total == 2 and {x.survey_id for x in items} == set(phieu["sv"].values())

    sv_service.delete_survey(db, phieu["sv"]["xoa"], user.id)
    items, total = sr_service.available_survey_lines(db, supplier_code="NX", item_group="Nhãn")
    assert total == 1 and {x.survey_id for x in items} == {phieu["sv"]["giu"]}

    #  Tự gắn phương án từ PKS liên kết: chỉ PKS sống → đúng 1 option.
    assert sr_service.sync_options_from_surveys(db, sr.id, user.id) == 1
    opts = db.query(SurveyRequestOption).join(
        SurveyRequestLine, SurveyRequestLine.id == SurveyRequestOption.survey_request_line_id
    ).filter(SurveyRequestLine.survey_request_id == sr.id).all()
    psl_live = db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == phieu["sv"]["giu"]).one()
    assert [o.product_survey_line_id for o in opts] == [psl_live.id]

    #  Gắn tay dòng của PKS đã xóa → 400.
    psl_dead = db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == phieu["sv"]["xoa"]).one()
    line = db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sr.id).one()
    with pytest.raises(HTTPException) as e:
        sr_service.create_option(db, line, psl_dead.id, user.id)
    assert e.value.status_code == 400


def test_huy_duyet_dmh_bo_qua_yctt_da_xoa(world, actor, phieu):
    """YCTT đã xóa mềm còn trỏ mã đơn thì không chặn hủy duyệt đơn nữa."""
    db, user = world.db, actor.user
    po = db.get(PurchaseOrder, phieu["po"]["giu"])
    po.status = "approved"
    req = _make_prq(db, code="YCTT_CUA_PO", company_id=world.co["A"], department_id=world.dept["A.kt"],
                    created_by=user.id, po_code=po.code)
    db.commit()
    with pytest.raises(HTTPException) as e:
        po_service.unapprove_po(db, po.id, user.id)
    assert "yêu cầu thanh toán" in e.value.detail

    prq_service.delete_request(db, req.id, user.id)
    assert po_service.unapprove_po(db, po.id, user.id).status == "draft"


def test_bao_cao_dmh_bo_qua_don_da_xoa(world, actor, phieu):
    from app.modules.report import service as report_service
    from app.modules.report.procurement_summary_rows import real_po_ids

    db, user = world.db, actor.user
    for sid in phieu["po"].values():
        po = db.get(PurchaseOrder, sid)
        po.status, po.department = "approved", "Phòng KT"
    db.commit()
    assert real_po_ids(db, set(phieu["po"].values())) == set(phieu["po"].values())
    #  duoc-CR-663: báo cáo gom theo id phòng, nhãn = TÊN HIỆN HÀNH (không còn là bản chụp «Phòng KT»).
    from app.modules.department.model import Department
    ten = db.get(Department, db.get(PurchaseOrder, phieu["po"]["giu"]).department_id).name
    rows = report_service.compute_dept_range(db, "2026-10-01", "2026-10-31", None)
    assert {r["key"]: r["orders"] for r in rows} == {ten: 2}

    #  Đơn đã duyệt không xóa qua API được — giả lập bản ghi đã mang cờ (vd xóa lúc còn nháp rồi mới duyệt).
    db.get(PurchaseOrder, phieu["po"]["xoa"]).is_deleted = True
    db.commit()
    assert real_po_ids(db, set(phieu["po"].values())) == {phieu["po"]["giu"]}
    rows = report_service.compute_dept_range(db, "2026-10-01", "2026-10-31", None)
    assert {r["key"]: r["orders"] for r in rows} == {ten: 1}


# ═══════════════════════════════ 7: đính kèm + chuỗi chứng từ ═════════════════════════════

def test_dinh_kem_treo_vao_phieu_da_xoa_404_va_chuoi_bo_pks_da_xoa(world, actor, phieu):
    from app.core import attachment_scope
    from app.modules.attachment.controller import _resolve_chain
    from app.modules.purchase_order.model import PODelivery

    db, user = world.db, actor.user
    item = db.query(POItem).filter(POItem.po_id == phieu["po"]["xoa"]).one()
    dl = PODelivery(po_id=phieu["po"]["xoa"], po_item_id=item.id, delivery_no=1, created_by=user.id, updated_by=user.id)
    db.add(dl)
    db.commit()
    sv_dead = db.get(Survey, phieu["sv"]["xoa"])
    ssl_dead = db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == sv_dead.id).one()
    #  Đơn sống trỏ tới PKS sắp xóa — chuỗi chứng từ phải bỏ nhóm PKS sau khi xóa.
    po_live = db.get(PurchaseOrder, phieu["po"]["giu"])
    po_live.survey_code = sv_dead.code
    db.commit()
    assert any(g[0] == "survey" for g in _resolve_chain(db, user, "purchase_order", po_live.id)[1])

    #  Trước khi xóa: mọi cửa đều mở.
    for entity, oid in (("purchase_order", phieu["po"]["xoa"]), ("delivery", dl.id),
                        ("payment_request", phieu["prq"]["xoa"]), ("survey", sv_dead.id),
                        ("survey_line", ssl_dead.id)):
        attachment_scope.ensure_in_scope(db, user, entity, oid)

    po_service.delete_po(db, phieu["po"]["xoa"], user.id)
    prq_service.delete_request(db, phieu["prq"]["xoa"], user.id)
    sv_service.delete_survey(db, sv_dead.id, user.id)

    for entity, oid, model in (("purchase_order", phieu["po"]["xoa"], PurchaseOrder), ("delivery", dl.id, PurchaseOrder),
                               ("payment_request", phieu["prq"]["xoa"], PaymentRequest),
                               ("survey", sv_dead.id, Survey), ("survey_line", ssl_dead.id, Survey)):
        m, ids = attachment_scope.parent_records(db, entity, oid)
        assert m is model and ids == [], entity
        with pytest.raises(HTTPException) as e:
            attachment_scope.ensure_in_scope(db, user, entity, oid)
        assert e.value.status_code == 404, entity
    #  Phiếu sống vẫn mở được.
    attachment_scope.ensure_in_scope(db, user, "purchase_order", phieu["po"]["giu"])
    attachment_scope.ensure_in_scope(db, user, "payment_request", phieu["prq"]["giu"])
    attachment_scope.ensure_in_scope(db, user, "survey", phieu["sv"]["giu"])

    groups = _resolve_chain(db, user, "purchase_order", po_live.id)[1]
    assert not any(g[0] in ("survey", "survey_line") for g in groups), "PKS đã xóa không bày trong chuỗi"


# ═══════════════════════════════ 8: nhập liệu ═════════════════════════════════════════════

def _run_import(db, module, rows):
    from app.modules.import_tool import doc_import
    from app.modules.import_tool.model import ImportMode
    from test_import_documents import _batch, _wb

    b = _batch(db, module, ImportMode.APPLY)
    doc_import.run(db, b, _wb(module, rows), apply=True)
    return b


def test_hoan_tac_lo_nhap_pks_va_dmh_la_xoa_mem_giu_dong(db):
    from app.modules.import_tool import service as imp_service
    from app.modules.import_tool.model import ImportModule

    b_sv = _run_import(db, ImportModule.SURVEY, [
        {"code": "KS_LO", "item_group": "Thùng", "supplier_name": "NCC A", "tax_code": "111"},
        {"code": "KS_LO", "supplier_name": "NCC B", "tax_code": "222"},
    ])
    b_po = _run_import(db, ImportModule.PURCHASE_ORDER, [
        {"code": "PO_LO", "supplier_name": "NCC X", "product_name": "SP 1", "qty_order": 10, "price": 1000},
        {"code": "PO_LO", "product_name": "SP 2", "qty_order": 5},
    ])
    s = db.query(Survey).filter(Survey.code == "KS_LO").one()
    p = db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO_LO").one()

    res = imp_service.revert_batch(db, b_sv, user_id=1)
    assert res["ok"] is True and res["deleted"] == 1
    res = imp_service.revert_batch(db, b_po, user_id=1)
    assert res["ok"] is True and res["deleted"] == 1

    db.expire_all()
    assert s.is_deleted is True and p.is_deleted is True
    assert db.query(SurveySupplierLine).filter(SurveySupplierLine.survey_id == s.id).count() == 2
    assert db.query(POItem).filter(POItem.po_id == p.id).count() == 2

    #  Hoàn tác lần hai (giả lập lô còn DONE): phiếu đã xóa mềm coi như xong phần nó — không đếm, không nổ.
    from app.modules.import_tool.model import ImportStatus
    b_sv.status = b_po.status = ImportStatus.DONE
    db.commit()
    assert imp_service.revert_batch(db, b_sv, user_id=1)["deleted"] == 0
    assert imp_service.revert_batch(db, b_po, user_id=1)["deleted"] == 0


def test_nhap_lai_ma_cua_phieu_da_xoa_bi_bo_qua_doc_deleted(db):
    from app.modules.import_tool.model import ImportLog, ImportModule

    _run_import(db, ImportModule.PURCHASE_ORDER, [
        {"code": "PO_TRUNG", "supplier_name": "NCC X", "product_name": "SP 1", "qty_order": 1}])
    p = db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO_TRUNG").one()
    po_service.delete_po(db, p.id, user_id=1)

    b = _run_import(db, ImportModule.PURCHASE_ORDER, [
        {"code": "PO_TRUNG", "supplier_name": "NCC Y", "product_name": "SP 9", "qty_order": 1}])
    assert b.created_count == 0
    assert db.query(ImportLog).filter(ImportLog.batch_id == b.id, ImportLog.category == "doc_deleted").count() == 1
    assert db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO_TRUNG").count() == 1
    assert db.query(PurchaseOrder).filter(PurchaseOrder.code == "PO_TRUNG").one().supplier_name == "NCC X"
