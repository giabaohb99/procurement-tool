"""ai-CR-238 — trợ lý nhập BÁO GIÁ NCC (AI đọc tệp PDF / ảnh) vào phiếu khảo sát đang mở hoặc YCBG đang khảo sát
(`draft_supplier_quote` · `confirm_draft` kind=supplier_quote). CHỈ kiểm phần vừa làm:

- khớp dòng theo NCC + mã / tên hàng, dòng không khớp không ghi, tự chọn phiếu của người đang phụ trách;
- dòng sẽ GHI ĐÈ giá đã có và ĐVT lệch được báo trong nháp, chưa ghi gì tới khi xác nhận;
- xác nhận ghi bằng đúng service lưu phiếu khảo sát của màn web, xác nhận lần hai không ghi đôi;
- YCBG chưa có phiếu khảo sát mở → lập phiếu khảo sát Nháp gắn YCBG như nút trên web;
- thiếu quyền / ngoài phạm vi / phiếu đã chốt hoặc đã duyệt bị chặn;
- cổng MCP: khóa chỉ đọc bị chặn, nhóm G7 tắt mặc định bị chặn, bật thì trả link tuyệt đối.
"""
import re
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import draft_create, mcp, mcp_keys
from app.modules.assistant import tools as T
from app.modules.supplier.model import Supplier
from app.modules.survey.model import Survey, SurveyProductLine
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User

SUP = "BBPN"


def _survey(db, code, *, status="draft", created_by, item_code="", item_name="", uom="", item_group="Chai",
            lines=()):
    s = Survey(code=code, survey_type="combined", status=status, item_group=item_group, item_code=item_code,
               item_name=item_name, has_product_code=bool(item_code), uom=uom, request_qty=1000,
               created_by=created_by, updated_by=created_by)
    db.add(s)
    db.flush()
    for sup, icode, name, unit, price in lines:
        db.add(SurveyProductLine(survey_id=s.id, supplier_code=sup, internal_code=icode, product_name=name,
                                 quote_unit=unit, price_by_volume=price, vat=8, moq=1000, request_qty=1000,
                                 line_approve="Chờ duyệt", created_by=created_by, updated_by=created_by))
    db.flush()
    return s


@pytest.fixture
def kho(db, seed, cap_quyen):
    db.add(Supplier(code=SUP, name="Công ty TNHH Bao Bì Nhựa Phương Nam", tax_code="0301234567"))
    db.add(Supplier(code="TANPHU", name="Công ty CP Nhựa Tân Phú"))
    staff = db.get(User, seed.u_nstm_id)
    outsider = db.get(User, seed.u_req_id)
    cap_quyen(staff.id, "survey", scope="all", read=True, write=True, create=True)
    cap_quyen(staff.id, "supplier", scope="all", read=True)
    cap_quyen(staff.id, "survey_request", scope="all", read=True)
    cap_quyen(outsider.id, "survey", scope="own", read=True, write=True, create=True)
    cap_quyen(outsider.id, "supplier", scope="all", read=True)
    w = SimpleNamespace(staff=staff, outsider=outsider, db=db)
    w.chai = _survey(db, "KS90001", created_by=staff.id, item_code="CPT0234", item_name="Chai PET 500ml", uom="Cái",
                     lines=[(SUP, "CPT0234", "Chai PET 500ml", "Cái", 1200), ("NX", "", "Chai PET 500ml", "Cái", 1300)])
    w.nap = _survey(db, "KS90002", created_by=staff.id, item_code="NAP0169", item_name="Nắp chai 28mm", uom="Cái")
    w.done = _survey(db, "KS90003", status="approved", created_by=staff.id, item_code="CPT0234",
                     item_name="Chai PET 500ml", uom="Cái", lines=[(SUP, "CPT0234", "Chai PET 500ml", "Cái", 1100)])
    w.ycbg = SurveyRequest(code="YCBG90001", status="processing", purpose="Hỏi giá thùng carton cho đợt Tết",
                           requester_id=seed.emp_req_id, company_id=seed.company_id, created_by=outsider.id,
                           updated_by=outsider.id)
    db.add(w.ycbg)
    db.flush()
    w.ycbg_line = SurveyRequestLine(survey_request_id=w.ycbg.id, item_group="Thùng", uom="Thùng", request_qty=500,
                                    requirement_detail="Thùng carton 5 lớp 60x40x40", assignee="DEMONV",
                                    created_by=outsider.id, updated_by=outsider.id)
    db.add(w.ycbg_line)
    db.commit()
    return w


def _draft(w, user=None, lines=None, **over):
    args = {"supplier": "Bao bì nhựa Phương Nam", "quote_no": "BG-1108", "quote_date": "12/11/2026",
            "lines": lines if lines is not None else [
                {"product_code": "CPT0234", "unit_price": "1.150", "vat": 8, "uom": "Cái", "delivery_time": "7 ngày",
                 "debt_term": "30 ngày", "note": "Giá đã gồm vận chuyển"},
                {"product_code": "XYZ999", "product_name": "Hàng lạ", "unit_price": 5}],
            **over}
    return T.run_tool(w.db, user or w.staff, "draft_supplier_quote", args)


def _lines(db, survey):
    return (db.query(SurveyProductLine).filter(SurveyProductLine.survey_id == survey.id)
            .order_by(SurveyProductLine.id).all())


# ── khớp dòng + nháp ──────────────────────────────────────────────────────────────────────
def test_khop_dong_ghi_de_co_canh_bao_va_chua_ghi_gi(kho, db):
    out = _draft(kho)
    d = out["draft"]
    assert out["kind"] == "supplier_quote" and d["survey_code"] == "KS90001"     # tự chọn phiếu mở có dòng khớp
    assert out["target"]["url"] == f"/procurement/surveys/{kho.chai.id}"
    [row] = d["rows"]
    assert (row["op"], row["after"]["price_by_volume"], row["after"]["debt_policy"]) == ("update", 1150, "Công nợ 30 ngày")
    assert row["supplier_code"] == SUP
    assert [m["product"] for m in out["matched"]] == ["CPT0234"]
    assert [u["product"] for u in out["unmatched"]] == ["XYZ999"]
    assert any("GHI ĐÈ" in x and "1.200" in x and "1.150" in x for x in out["overwrites"])
    assert out["uom_mismatches"] == []
    assert float(_lines(db, kho.chai)[0].price_by_volume) == 1200                 # nháp chưa ghi gì


def test_dvt_lech_duoc_bao(kho):
    out = _draft(kho, lines=[{"product_code": "CPT0234", "unit_price": 13500, "uom": "Thùng"}])
    assert any("Thùng" in x and "Cái" in x for x in out["uom_mismatches"])


def test_xac_nhan_ghi_nhu_man_web_va_khong_ghi_doi(kho, db):
    d = _draft(kho)["draft"]
    code, oid = draft_create.create(db, kho.staff, "supplier_quote", d)
    assert (code, oid) == ("KS90001", kho.chai.id)
    rows = _lines(db, kho.chai)
    assert len(rows) == 2                                                          # dòng NCC khác giữ nguyên
    mine = next(r for r in rows if r.supplier_code == SUP)
    other = next(r for r in rows if r.supplier_code == "NX")
    assert float(mine.price_by_volume) == 1150 and mine.debt_policy == "Công nợ 30 ngày"
    assert mine.delivery_time == "7 ngày" and mine.note == "Giá đã gồm vận chuyển"
    assert "BG-1108" in mine.nspt_note and "2026-11-12" in mine.nspt_note
    assert float(mine.amount) == round(1150 * 1000 * 1.08, 2)                      # thành tiền tính lại như form web
    assert float(other.price_by_volume) == 1300
    with pytest.raises(draft_create.DraftError, match="đã đổi sau lúc soạn"):
        draft_create.create(db, kho.staff, "supplier_quote", d)


def test_ncc_moi_cho_hang_cua_phieu_thi_them_dong(kho, db):
    out = _draft(kho, supplier="TANPHU", lines=[{"product_name": "chai pet 500ml", "unit_price": 1180, "vat": 10}])
    [row] = out["draft"]["rows"]
    assert row["op"] == "add" and out["draft"]["survey_code"] == "KS90001"
    draft_create.create(db, kho.staff, "supplier_quote", out["draft"])
    new = next(r for r in _lines(db, kho.chai) if r.supplier_code == "TANPHU")
    assert (float(new.price_by_volume), float(new.vat), new.product_name) == (1180, 10, "Chai PET 500ml")
    assert new.line_approve == "Chờ duyệt"


def test_khong_khop_phieu_nao_thi_hoi_lai(kho):
    out = _draft(kho, lines=[{"product_code": "KHONGCO", "unit_price": 1}])
    assert "draft" not in out and out.get("need_choice")
    assert any("YCBG90001" in o for o in out["options"])                           # YCBG mình đang phụ trách


# ── YCBG đang khảo sát → phiếu khảo sát mới ───────────────────────────────────────────────
def test_ycbg_chua_co_phieu_khao_sat_thi_lap_phieu_nhap_gan_ycbg(kho, db):
    out = _draft(kho, survey_request_code="ycbg90001",
                 lines=[{"product_name": "Thùng carton 5 lớp", "unit_price": 12000, "vat": 8, "uom": "Cái"}])
    d = out["draft"]
    assert d["new_survey"]["survey_request_code"] == "YCBG90001" and d["rows"][0]["op"] == "add"
    assert any("Cái" in x and "Thùng" in x for x in out["uom_mismatches"])
    assert db.query(Survey).filter(Survey.survey_request_id == kho.ycbg.id).count() == 0
    code, oid = draft_create.create(db, kho.staff, "supplier_quote", d)
    s = db.get(Survey, oid)
    assert (s.status, s.survey_request_id, s.sr_code, s.item_group, s.code) == ("draft", kho.ycbg.id, "YCBG90001",
                                                                                "Thùng", code)
    [ln] = _lines(db, s)
    assert (ln.supplier_code, float(ln.price_by_volume)) == (SUP, 12000)
    with pytest.raises(draft_create.DraftError, match="đã có phiếu khảo sát"):
        draft_create.create(db, kho.staff, "supplier_quote", d)
    #  Lần sau: YCBG đã có phiếu khảo sát Nháp → nhập thẳng vào phiếu đó.
    again = _draft(kho, survey_request_code="YCBG90001",
                   lines=[{"product_name": "Thùng carton 5 lớp", "unit_price": 11800}])
    assert again["draft"]["survey_id"] == oid and again["draft"]["rows"][0]["op"] == "update"


# ── chặn ──────────────────────────────────────────────────────────────────────────────────
def test_phieu_da_duyet_hoac_da_chot_khong_sua_duoc(kho, db):
    out = _draft(kho, survey_code="KS90003")
    assert "draft" not in out and "Đã duyệt" in out["error"]
    d = _draft(kho)["draft"]
    kho.chai.status = "submitted"                                                  # gửi duyệt sau lúc soạn
    db.commit()
    with pytest.raises(draft_create.DraftError, match="Chờ duyệt"):
        draft_create.create(db, kho.staff, "supplier_quote", d)
    assert float(_lines(db, kho.chai)[0].price_by_volume) == 1200
    kho.ycbg.status = "survey_done"
    db.commit()
    closed = _draft(kho, survey_request_code="YCBG90001", lines=[{"product_name": "Thùng", "unit_price": 1}])
    assert "draft" not in closed and "Đã khảo sát" in closed["error"]


def test_thieu_quyen_va_ngoai_pham_vi(kho, db, cap_quyen):
    nobody = User(email="NOBODY", password_hash="x", is_active=True)
    db.add(nobody)
    db.commit()
    assert _draft(kho, nobody).get("denied")
    reader = User(email="READER", password_hash="x", is_active=True)
    db.add(reader)
    db.commit()
    cap_quyen(reader.id, "survey", scope="all", read=True)
    cap_quyen(reader.id, "supplier", scope="all", read=True)
    assert _draft(kho, reader).get("denied")                                       # chỉ đọc phiếu khảo sát
    #  Phiếu của người khác (phạm vi own) và mã không tồn tại: cùng một câu.
    e1 = _draft(kho, kho.outsider, survey_code="KS90001")["error"]
    e2 = _draft(kho, kho.outsider, survey_code="KS99999")["error"]
    assert e1.replace("KS90001", "#") == e2.replace("KS99999", "#")
    staff_draft = _draft(kho)["draft"]
    with pytest.raises(draft_create.DraftError, match="phạm vi bạn được ghi") as x1:
        draft_create.create(db, kho.outsider, "supplier_quote", staff_draft)
    with pytest.raises(draft_create.DraftError, match="phạm vi bạn được ghi") as x2:
        draft_create.create(db, kho.outsider, "supplier_quote", {**staff_draft, "survey_id": 987654})
    assert re.sub(r"#\d+", "#", str(x1.value)) == re.sub(r"#\d+", "#", str(x2.value))
    with pytest.raises(draft_create.DraftError, match="quyền"):
        draft_create.create(db, reader, "supplier_quote", staff_draft)
    assert float(_lines(db, kho.chai)[0].price_by_volume) == 1200


def test_tham_so_la_khong_vo(kho):
    assert "error" in _draft(kho, lines=[])
    assert "error" in _draft(kho, lines=[{"product_code": "CPT0234", "unit_price": "abc"}])
    assert "error" in _draft(kho, lines=[{"product_code": "CPT0234", "unit_price": 1, "vat": 150}])
    assert "error" in _draft(kho, lines="khong phai mang")
    long = _draft(kho, supplier="x" * 5000, lines=[{"product_code": "C" * 500, "unit_price": 1}])
    assert "draft" not in long


# ── cổng MCP ──────────────────────────────────────────────────────────────────────────────
def test_cong_mcp_nhom_tat_mac_dinh_va_khoa_chi_doc(kho, db):
    from app.modules.agent_hub import mcp_settings

    assert mcp.is_write_tool("draft_supplier_quote")
    assert mcp_settings.GROUP_OF["draft_supplier_quote"].key == "supplier_quote"
    assert not next(g for g in mcp_settings.GROUPS if g.key == "supplier_quote").default_on
    d = _draft(kho)["draft"]
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_supplier_quote", {"supplier": SUP}).get("denied")
    args = {"kind": "supplier_quote", "draft": d}
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", args).get("denied")   # nhóm tắt
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_READ, "confirm_draft", args).get("denied")    # khóa chỉ đọc
    names = {t["name"] for t in mcp.list_tools(db, kho.staff, mcp_keys.SCOPE_WRITE)}
    assert "draft_supplier_quote" not in names
    assert float(_lines(db, kho.chai)[0].price_by_volume) == 1200


def test_cong_mcp_xac_nhan_tra_link_tuyet_doi(kho, db, mcp_all_groups):
    assert "draft_supplier_quote" not in {t["name"] for t in mcp.list_tools(db, kho.staff, mcp_keys.SCOPE_READ)}
    assert "draft_supplier_quote" in {t["name"] for t in mcp.list_tools(db, kho.staff, mcp_keys.SCOPE_WRITE)}
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_READ, "draft_supplier_quote", {"supplier": SUP}).get("denied")
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_supplier_quote",
                        {"supplier": SUP, "lines": [{"product_code": "CPT0234", "unit_price": 1150}]})
    assert out["target"]["url"].startswith("http") and out["attach_url"].startswith("http")
    ok = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "supplier_quote", "draft": out["draft"]})
    assert ok["ok"] and ok["code"] == "KS90001"
    assert ok["link"].startswith("http") and ok["link"].endswith(f"/procurement/surveys/{kho.chai.id}")
    assert ok["attach_url"] == ok["link"] and any("CPT0234" in x for x in ok["details"])
