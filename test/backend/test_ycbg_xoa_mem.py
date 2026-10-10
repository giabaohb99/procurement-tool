"""ai-CR-170 — Yêu cầu báo giá (YCBG) xóa MỀM + lọc tập trung ở `core/scoping`.

Đại ca chốt 10/10/2026: xóa phiếu = đánh dấu `is_deleted` + thời điểm + người xóa, không
`db.delete`. Bài này chốt bảy việc:

  1. `DELETE /{sid}` để phiếu lại trong DB (cờ + mốc + người), dòng / phương án giữ nguyên;
  2. phiếu đã xóa KHÔNG còn ở danh sách · chi tiết · xuất Excel · xóa hàng loạt;
  3. trang chủ (KPI + việc của tôi) bỏ qua phiếu đã xóa;
  4. tool Trợ lý (`procurement_doc_read` · `my_procurement_requests` · `propose_document_delete`)
     không thấy phiếu đã xóa;
  5. mã phiếu KHÔNG tái dùng — `_gen_code` đếm cả phiếu đã xóa;
  6. phiếu khác (cùng người, cùng pháp nhân) không bị ảnh hưởng;
  7. `apply_scope` / `get_scoped` TỰ lọc cho MỌI model có cột `is_deleted` (kể cả phạm vi
     «thấy tất»), và không đụng model không có cột đó.

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
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)


class _Req:
    """Chỉ cần `query_params` thật (`collect_conditions_map` gọi `multi_items()`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _body(resp) -> dict:
    return json.loads(resp.body)


def _make_sr(db, *, code, company_id, department_id, created_by, status="draft",
             with_line=True) -> SurveyRequest:
    row = SurveyRequest(code=code, company_id=company_id, department_id=department_id,
                        department="", requester_id=0, status=status, purpose=f"Khảo sát {code}",
                        created_by=created_by, updated_by=created_by)
    db.add(row)
    db.flush()
    if with_line:
        ln = SurveyRequestLine(survey_request_id=row.id, item_group="Nhãn", request_qty=1,
                               requirement_detail="Decal 10x10", created_by=created_by)
        db.add(ln)
        db.flush()
        db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1,
                                   display_label="Option 1", snap_product_name="Decal A"))
        db.flush()
    db.commit()
    return row


@pytest.fixture
def actor(world):
    """`a1` thấy TẤT (scope `all`) với đủ hành động — để mọi khẳng định «không thấy» ở dưới
    chỉ có thể do cờ xóa mềm, không phải do phạm vi vai trò."""
    return world.grant("a1", "survey_request", scope="all",
                       actions=("read", "create", "write", "delete", "export", "approve"))


@pytest.fixture
def phieu(world, actor):
    """Hai YCBG nháp của a1 ở pháp nhân A: `xoa` sẽ bị xóa mềm, `giu` ở lại nguyên."""
    db = world.db
    uid = actor.user.id
    A, dept = world.co["A"], world.dept["A.kt"]
    xoa = _make_sr(db, code="YCBG_XOA", company_id=A, department_id=dept, created_by=uid)
    giu = _make_sr(db, code="YCBG_GIU", company_id=A, department_id=dept, created_by=uid)
    return {"xoa": xoa.id, "giu": giu.id}


# ── 1 + 2 + 6: xóa qua API → còn trong DB, biến khỏi danh sách / chi tiết / xuất / xóa lô ─────

def test_xoa_mem_qua_api_phieu_con_trong_db_va_bien_khoi_moi_cua_doc(world, actor, phieu):
    from app.modules.survey_request import controller as sr_ctl

    db, user = world.db, actor.user
    sid, keep = phieu["xoa"], phieu["giu"]
    line_ids = [ln.id for ln in sr_service.lines_of(db, sid)]
    assert line_ids, "phiếu mẫu phải có dòng để chứng minh dòng không bị xóa theo"

    truoc = datetime.utcnow()
    resp = sr_ctl.delete_(sid, db, user)
    assert _body(resp)["message"] == "Đã xóa"

    # (1) Còn trong DB — cờ + mốc + người xóa; dòng / phương án giữ nguyên.
    row = db.get(SurveyRequest, sid)
    assert row is not None
    assert row.is_deleted is True
    assert row.deleted_at is not None and row.deleted_at >= truoc.replace(microsecond=0)
    assert row.deleted_by == user.id
    assert db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sid).count() == len(line_ids)
    assert db.query(SurveyRequestOption).filter(
        SurveyRequestOption.survey_request_line_id.in_(line_ids)).count() == 1

    # (2) `service.get_sr` 404; chi tiết 403 (route coi như ngoài phạm vi); danh sách và xuất Excel bỏ.
    with pytest.raises(HTTPException) as e:
        sr_service.get_sr(db, sid)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        sr_ctl.get_(sid, db, user)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        sr_ctl._in_scope(db, sid, user, "read")
    assert e.value.status_code == 404

    ids_list = {r.id for r in sr_ctl._list_query(_Req(), db, user).all()}
    assert sid not in ids_list and keep in ids_list

    xlsx = sr_ctl.export_xlsx(_Req(), "", "", db, user)
    wb = openpyxl.load_workbook(BytesIO(xlsx.body))
    cells = {str(c.value) for row in wb.active.iter_rows() for c in row if c.value is not None}
    assert "YCBG_GIU" in cells and "YCBG_XOA" not in cells

    # Xóa lô trỏ vào phiếu đã xóa: `apply_scope` không trả dòng nào → 403 như id ngoài phạm vi.
    with pytest.raises(HTTPException) as e:
        sr_ctl.bulk_delete_survey_requests(str(sid), db, user)
    assert e.value.status_code == 403
    # Nhân bản / xem kết quả cũng không mở được phiếu đã xóa.
    for fn in (sr_ctl.clone_, sr_ctl.result_view_):
        with pytest.raises(HTTPException) as e:
            fn(sid, db, user)
        assert e.value.status_code == 403

    # (6) Phiếu khác nguyên vẹn, vẫn mở được.
    other = db.get(SurveyRequest, keep)
    assert other.is_deleted is False and other.deleted_at is None and other.deleted_by == 0
    assert _body(sr_ctl.get_(keep, db, user))["data"]["code"] == "YCBG_GIU"


def test_xoa_lan_hai_va_xoa_phieu_khong_phai_nhap_deu_bi_chan(world, actor, phieu):
    from app.modules.survey_request import controller as sr_ctl

    db, user = world.db, actor.user
    sr_ctl.delete_(phieu["xoa"], db, user)
    with pytest.raises(HTTPException) as e:
        sr_ctl.delete_(phieu["xoa"], db, user)          # phiếu đã xóa coi như không có
    assert e.value.status_code == 404

    db.get(SurveyRequest, phieu["giu"]).status = "processing"
    db.commit()
    with pytest.raises(HTTPException) as e:
        sr_service.delete_sr(db, phieu["giu"], user.id)  # luật trạng thái giữ như cũ
    assert e.value.status_code == 400
    assert db.get(SurveyRequest, phieu["giu"]).is_deleted is False


# ── 3: trang chủ ──────────────────────────────────────────────────────────────────────────

def test_trang_chu_bo_qua_phieu_da_xoa(world, actor, phieu):
    from app.modules.dashboard.controller import build_my_tasks, overview

    db, user = world.db, actor.user
    sr_service.delete_sr(db, phieu["xoa"], user.id)                # xóa lúc còn nháp
    for sid in phieu.values():
        db.get(SurveyRequest, sid).status = "submitted"             # cả hai «chờ duyệt», một đã xóa
    db.commit()

    data = _body(overview(db, user))["data"]
    assert data["kpi"]["sr_pending"] == 1
    assert [x["code"] for x in data["pending_srs_list"]] == ["YCBG_GIU"]

    tasks = build_my_tasks(db, user, actor.profile())
    codes = {t["code"] for t in tasks if t["type"] == "sr"}
    assert codes == {"YCBG_GIU"}


# ── 4: tool Trợ lý ─────────────────────────────────────────────────────────────────────────

def test_tool_tro_ly_khong_thay_phieu_da_xoa(world, actor, phieu):
    from app.modules.assistant import tools as T

    db, user = world.db, actor.user
    sr_service.delete_sr(db, phieu["xoa"], user.id)

    doc = T.run_tool(db, user, "procurement_doc_read", {"entity": "survey_request", "code": "YCBG_XOA"})
    assert doc.get("error") and "Không tìm thấy" in doc["error"]
    ok = T.run_tool(db, user, "procurement_doc_read", {"entity": "survey_request", "code": "YCBG_GIU"})
    assert ok["header"]["code"] == "YCBG_GIU"

    mine = T.run_tool(db, user, "my_procurement_requests", {"entity": "survey_request"})
    nhom = [g for g in mine["groups"] if g["entity"] == "survey_request"][0]
    assert [it["code"] for it in nhom["items"]] == ["YCBG_GIU"]

    de_xuat = T.run_tool(db, user, "propose_document_delete",
                         {"entity": "survey_request", "code": "YCBG_XOA"})
    assert de_xuat.get("error")


# ── 5: mã không tái dùng ───────────────────────────────────────────────────────────────────

def test_ma_phieu_khong_tai_dung_sau_khi_xoa(world, actor):
    db, user = world.db, actor.user
    A, dept = world.co["A"], world.dept["A.kt"]
    first = sr_service._gen_code(db)
    row = _make_sr(db, code=first, company_id=A, department_id=dept, created_by=user.id,
                   with_line=False)
    sr_service.delete_sr(db, row.id, user.id)
    second = sr_service._gen_code(db)
    assert second != first
    assert int(second[len(first) - 2:]) == int(first[-2:]) + 1, "hậu tố phải tăng, không lấp chỗ trống"


# ── 7: lọc tập trung ở core/scoping ────────────────────────────────────────────────────────

def test_apply_scope_tu_loc_model_co_is_deleted_ke_ca_pham_vi_thay_tat(world, actor, phieu):
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.survey.model import Survey

    db, user, prof = world.db, actor.user, actor.profile()
    sr_service.delete_sr(db, phieu["xoa"], user.id)

    # Phạm vi `all` → `scope_condition` trả None, nhưng `apply_scope` vẫn phải lọc cờ xóa.
    seen = {r.id for r in apply_scope(db.query(SurveyRequest), SurveyRequest, "survey_request",
                                      user, prof).all()}
    assert seen == {phieu["giu"]}
    assert actor.sees(SurveyRequest, "survey_request") == {phieu["giu"]}

    # `get_scoped` cùng cửa: phiếu đã xóa → None; phiếu còn → bản ghi.
    assert get_scoped(db, SurveyRequest, "survey_request", phieu["xoa"], user, prof) is None
    assert get_scoped(db, SurveyRequest, "survey_request", phieu["giu"], user, prof) is not None

    # Model đã có `is_deleted` từ trước (YCMH) cũng được phủ — không cần lọc tay nữa.
    actor.grant("purchase_request", scope="all", actions=("read",))
    prof = actor.profile()
    pr_live = PurchaseRequest(code="YC_SONG", company_id=world.co["A"], status="draft",
                              created_by=user.id)
    pr_dead = PurchaseRequest(code="YC_XOA", company_id=world.co["A"], status="draft",
                              created_by=user.id, is_deleted=True)
    db.add_all([pr_live, pr_dead])
    db.commit()
    assert {r.id for r in apply_scope(db.query(PurchaseRequest), PurchaseRequest,
                                      "purchase_request", user, prof).all()} == {pr_live.id}
    assert get_scoped(db, PurchaseRequest, "purchase_request", pr_dead.id, user, prof) is None

    # Model KHÔNG có cột `is_deleted` (PKS) → không thêm điều kiện nào, query giữ nguyên.
    assert not_deleted_cond(Survey) is None
    actor.grant("survey", scope="all", actions=("read",))
    q = db.query(Survey)
    assert str(apply_scope(q, Survey, "survey", user, actor.profile())) == str(q)


def test_get_scoped_pham_vi_hep_van_loc_co_xoa(world, phieu):
    """Phạm vi `own` → có điều kiện thật; cờ xóa phải AND thêm, không thay thế."""
    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", "delete"))
    db, user = world.db, a1.user
    sr_service.delete_sr(db, phieu["xoa"], user.id)
    prof = a1.profile()
    assert get_scoped(db, SurveyRequest, "survey_request", phieu["xoa"], user, prof) is None
    assert get_scoped(db, SurveyRequest, "survey_request", phieu["giu"], user, prof) is not None


# ── Những chỗ đọc thẳng không qua phạm vi ─────────────────────────────────────────────────

def test_lien_ket_tu_ycmh_va_chuoi_dinh_kem_bo_phieu_da_xoa(world, actor, phieu):
    from app.core import attachment_scope
    from app.modules.purchase_request.controller import _linked_survey_requests
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.survey_request.model import SurveyRequestPr

    db, user = world.db, actor.user
    pr = PurchaseRequest(code="YC_TU_YCBG", company_id=world.co["A"], status="approved",
                         created_by=user.id)
    db.add(pr)
    db.flush()
    for sid in phieu.values():
        ln = sr_service.lines_of(db, sid)[0]
        db.add(SurveyRequestPr(survey_request_id=sid, survey_request_line_id=ln.id,
                               pr_id=pr.id, pr_code=pr.code))
    db.commit()
    assert {x["code"] for x in _linked_survey_requests(db, pr)} == {"YCBG_XOA", "YCBG_GIU"}

    sr_service.delete_sr(db, phieu["xoa"], user.id)
    assert {x["code"] for x in _linked_survey_requests(db, pr)} == {"YCBG_GIU"}

    # Đính kèm treo vào phiếu đã xóa: chứng từ cha «không còn» → 404; phiếu sống vẫn mở được.
    model, ids = attachment_scope.parent_records(db, "survey_request", phieu["xoa"])
    assert model is SurveyRequest and ids == []
    with pytest.raises(HTTPException) as e:
        attachment_scope.ensure_in_scope(db, user, "survey_request", phieu["xoa"])
    assert e.value.status_code == 404
    attachment_scope.ensure_in_scope(db, user, "survey_request", phieu["giu"])   # không ném

    # Dòng của phiếu đã xóa đi qua `apply_scope` → ngoài phạm vi (403).
    ln_xoa = sr_service.lines_of(db, phieu["xoa"])[0]
    with pytest.raises(HTTPException) as e:
        attachment_scope.ensure_in_scope(db, user, "survey_request_line", ln_xoa.id)
    assert e.value.status_code == 403


def test_tu_hoan_thanh_va_go_lien_ket_bo_qua_phieu_da_xoa(world, actor, phieu):
    """`_auto_complete_sr` / `unlink_deleted_pr` không đổi trạng thái, không ghi sổ cho YCBG đã xóa."""
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.survey_request.model import SurveyRequestPr

    db, user = world.db, actor.user
    sid = phieu["xoa"]
    pr = PurchaseRequest(code="YC_HOAN_THANH", company_id=world.co["A"], status="completed",
                         created_by=user.id)
    db.add(pr)
    db.flush()
    ln = sr_service.lines_of(db, sid)[0]
    db.add(SurveyRequestPr(survey_request_id=sid, survey_request_line_id=ln.id,
                           pr_id=pr.id, pr_code=pr.code))
    db.commit()

    sr_service.delete_sr(db, sid, user.id)
    row = db.get(SurveyRequest, sid)
    row.status = "pr_created"          # giả lập phiếu đã xóa còn đứng ở «Đã tạo YCMH»
    db.commit()

    sr_service._auto_complete_sr(db, sid, user.id)
    assert db.get(SurveyRequest, sid).status == "pr_created", "phiếu đã xóa không tự hoàn thành"

    pr.is_deleted = True
    db.commit()
    assert sr_service.unlink_deleted_pr(db, pr, user.id) == [sid]      # dây nối vẫn được gỡ
    assert db.query(SurveyRequestPr).filter(SurveyRequestPr.pr_id == pr.id).count() == 0
    assert db.get(SurveyRequest, sid).status == "pr_created", "nhưng trạng thái phiếu đã xóa giữ nguyên"
