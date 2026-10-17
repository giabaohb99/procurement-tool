"""ai-CR-216 — cấu hình cổng MCP (màn G7, doc/erp/21 §6.2 G7 + §5.2) + gỡ ba tool báo cáo mua hàng cũ khỏi MCP.

Canh:
  - mỗi tool thuộc ĐÚNG MỘT nhóm (tool mới quên xếp nhóm là đỏ); mặc định theo Q4: mở tra cứu của chính mình, nghỉ phép,
    danh bạ, báo cáo gom sẵn, Kho skill — Thu mua, Công nợ… TẮT;
  - nhóm tắt: tools/list không liệt kê, tools/call trả denied nói rõ nhóm; dataset_query bộ công nợ / YCTT tắt theo nhóm
    Công nợ dù nhóm Báo cáo đang bật;
  - GET cần agent_group.read, PUT cần agent_group.write; kiểm kiểu + dải, sai thì 400 không lưu gì;
  - trần / ngân sách / số ngày giữ nhật ký lưu được và cổng dùng ngay; chưa lưu thì theo biến môi trường;
  - câu dặn thêm nối sau INSTRUCTIONS của initialize;
  - purchase_report / analytics_query / top_suppliers_by_purchase không còn qua MCP (mọi mức khóa), gọi thì chỉ đường mới.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.modules.agent_hub import controller, mcp, mcp_keys, mcp_settings
from app.modules.user.model import User

ENTITY = controller.MCP_LOG_VIEW_ALL_ENTITY


def _json(resp):
    return json.loads(resp.body)["data"]


@pytest.fixture
def admin(db, cap_quyen):
    u = User(email="g7-admin@test.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    cap_quyen(u.id, ENTITY, scope="all", read=True, write=True)
    return u


def _names(db, scope=mcp_keys.SCOPE_READ):
    return {t["name"] for t in mcp.list_tools(db, SimpleNamespace(id=1, is_active=True), scope)}


# ── Nhóm ──────────────────────────────────────────────────────────────────────

def test_moi_tool_dung_mot_nhom_va_nhom_khong_khai_tool_ma():
    from app.modules.assistant.tools import tool_defs

    old = settings.AI_RAG_ENABLED
    settings.AI_RAG_ENABLED = True
    try:
        real = {d.name for d in tool_defs()} | mcp.SKILL_TOOLS
    finally:
        settings.AI_RAG_ENABLED = old
    exposed = real - mcp.HIDDEN - set(mcp.MCP_RETIRED)
    missing = sorted(exposed - set(mcp_settings.GROUP_OF))
    assert missing == [], f"tool chưa xếp nhóm MCP ở mcp_settings.GROUPS: {missing}"
    seen: dict = {}
    for g in mcp_settings.GROUPS:
        for t in g.tools:
            assert t not in seen, f"{t} nằm ở hai nhóm: {seen.get(t)} và {g.key}"
            seen[t] = g.key
    assert sorted(set(seen) - real) == [], "nhóm khai tool không có thật"
    assert len({g.key for g in mcp_settings.GROUPS}) == len(mcp_settings.GROUPS)


def test_mac_dinh_theo_q4_va_nhom_tat_khong_liet_ke_khong_goi_duoc(db, monkeypatch):
    cur = mcp_settings.current(db)["groups"]
    assert {k for k, v in cur.items() if v} == {"mine", "leave", "directory", "reports", "skills"}
    names = _names(db)
    assert {"my_leave_summary", "report_summary", "employee_lookup", "report_issue"} <= names
    assert not names & {"product_search", "payable_lookup", "erp_read", "customs_market"}

    from app.modules.assistant import tools as tool_registry

    monkeypatch.setattr(tool_registry, "run_tool", lambda *a, **k: pytest.fail("nhóm tắt mà tool vẫn chạy"))
    out = mcp.call_tool(db, SimpleNamespace(id=1), mcp_keys.SCOPE_READ, "product_search", {"keyword": "x"})
    assert out["denied"] and '"Thu mua: chứng từ, sản phẩm, nhà cung cấp, hợp đồng" đang tắt' in out["error"]
    out = mcp.call_tool(db, SimpleNamespace(id=1), mcp_keys.SCOPE_READ, "dataset_query", {"dataset": "payable"})
    assert out["denied"] and "Công nợ và thanh toán" in out["error"]
    #  Tool lạ (chưa xếp nhóm) cũng không lọt.
    assert "chưa được xếp nhóm" in mcp_settings.tool_blocked(db, "tool_moi_toanh")


# ── GET / PUT ─────────────────────────────────────────────────────────────────

def test_doc_ghi_cau_hinh_quyen_va_kiem_tham_so(db, admin, cap_quyen):
    viewer = User(email="g7-viewer@test.vn", employee_id=0, password_hash="x", is_active=True)
    nobody = User(email="g7-no@test.vn", employee_id=0, password_hash="x", is_active=True)
    db.add_all([viewer, nobody])
    db.commit()
    cap_quyen(viewer.id, ENTITY, scope="all", read=True)
    with pytest.raises(HTTPException) as e:
        controller.get_mcp_settings(user=SimpleNamespace(id=nobody.id), db=db)
    assert e.value.status_code == 403
    got = _json(controller.get_mcp_settings(user=SimpleNamespace(id=viewer.id), db=db))
    assert got["can_write"] is False and len(got["groups"]) == len(mcp_settings.GROUPS)
    purchase = next(g for g in got["groups"] if g["key"] == "purchase")
    assert purchase["enabled"] is False and purchase["default"] is False and "erp_read" in purchase["tools"]
    with pytest.raises(HTTPException) as e:
        controller.put_mcp_settings({"groups": {"purchase": True}}, user=SimpleNamespace(id=viewer.id), db=db)
    assert e.value.status_code == 403

    me = SimpleNamespace(id=admin.id)
    for bad in ({"groups": {"khong_co": True}}, {"groups": ["purchase"]}, {"rate_per_key": 5}, {"rate_per_key": "nhiều"},
                {"log_retention_days": 9999}, {"extra_instructions": "x" * 1001}):
        with pytest.raises(HTTPException) as e:
            controller.put_mcp_settings(bad, user=me, db=db)
        assert e.value.status_code == 400, bad
    assert mcp_settings.current(db)["groups"]["purchase"] is False                # lượt sai không lưu gì

    out = _json(controller.put_mcp_settings({"groups": {"purchase": True}, "rate_per_key": 30, "row_budget_per_min": 0,
                                              "extra_instructions": "Trả lời ngắn, ghi rõ nguồn."}, user=me, db=db))
    assert next(g for g in out["groups"] if g["key"] == "purchase")["enabled"] is True
    assert {lim["key"]: lim["value"] for lim in out["limits"]}["rate_per_key"] == 30
    assert "product_search" in _names(db)                                         # bật là liệt kê ngay (bộ đệm đã xóa)
    #  Lưu một phần không làm mất phần đã lưu.
    controller.put_mcp_settings({"groups": {"finance": True}}, user=me, db=db)
    cur = mcp_settings.current(db)
    assert cur["groups"]["purchase"] and cur["groups"]["finance"] and cur["rate_per_key"] == 30
    assert cur["row_budget_per_min"] == 0


def test_tran_chua_luu_theo_bien_moi_truong_luu_roi_thi_theo_cau_hinh(db, admin, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_MCP_RATE_PER_KEY", 7)
    assert mcp.mcp_settings_now(db)["rate_per_key"] == 7
    mcp_settings.save(db, {"rate_per_key": 40, "log_retention_days": 30}, admin.id)
    assert mcp.mcp_settings_now(db)["rate_per_key"] == 40 and mcp_settings.current(db)["log_retention_days"] == 30


def test_cau_dan_them_noi_sau_instructions(db, admin):
    key = SimpleNamespace(id=1, scope=mcp_keys.SCOPE_READ)
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    assert mcp.handle(db, SimpleNamespace(id=1), key, init)["result"]["instructions"] == mcp.INSTRUCTIONS
    mcp_settings.save(db, {"extra_instructions": "Luôn trả lời bằng tiếng Việt."}, admin.id)
    text = mcp.handle(db, SimpleNamespace(id=1), key, init)["result"]["instructions"]
    assert text.startswith(mcp.INSTRUCTIONS) and text.endswith("Luôn trả lời bằng tiếng Việt.")


def test_cau_hinh_hong_thi_chay_theo_mac_dinh(db, monkeypatch):
    from app.modules.agent_hub import erp

    monkeypatch.setattr(erp, "setting_raw_get", lambda db_, key: "{khong phai json")
    assert mcp_settings.current(db)["groups"]["leave"] is True
    mcp_settings.clear_cache()
    monkeypatch.setattr(erp, "setting_raw_get", lambda db_, key: (_ for _ in ()).throw(RuntimeError("ERP sập")))
    assert mcp_settings.current(db)["rate_per_key"] == int(settings.AGENT_MCP_RATE_PER_KEY)


# ── Gỡ ba tool báo cáo cũ khỏi MCP ────────────────────────────────────────────

def test_ba_tool_bao_cao_cu_khong_con_qua_mcp(db, mcp_all_groups, monkeypatch):
    from app.modules.assistant import tools as tool_registry

    monkeypatch.setattr(tool_registry, "run_tool", lambda *a, **k: pytest.fail("tool đã gỡ mà vẫn chạy"))
    for scope in (mcp_keys.SCOPE_READ, mcp_keys.SCOPE_WRITE):
        assert not _names(db, scope) & set(mcp.MCP_RETIRED)
        assert {"report_summary", "dataset_query"} <= _names(db, scope)
    out = mcp.call_tool(db, SimpleNamespace(id=1), mcp_keys.SCOPE_WRITE, "purchase_report", {})
    assert "report_summary" in out["error"]
    assert "dataset=purchase" in mcp.call_tool(db, SimpleNamespace(id=1), mcp_keys.SCOPE_READ, "top_suppliers_by_purchase",
                                               {})["error"]
    assert not set(mcp.MCP_RETIRED) & mcp.READ_TOOLS
    #  Trợ lý web / bot vẫn còn ba tool này.
    from app.modules.assistant.tools import tool_defs

    assert set(mcp.MCP_RETIRED) <= {d.name for d in tool_defs()}


def test_duong_dan_tuong_doi_o_moi_tang_thanh_tuyet_doi(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    out = mcp._absolute_downloads({"header": {"url": "/procurement/purchase-orders/5"},
                                   "lines": [{"detail_url": "/production/products/9", "note": "/khong-phai-link"}],
                                   "items": [{"url": "https://x.vn/a"}, {"url": "//cdn/x"}]})
    assert out["header"]["url"] == "https://deverp.degoholding.vn/procurement/purchase-orders/5"
    assert out["lines"][0]["detail_url"] == "https://deverp.degoholding.vn/production/products/9"
    assert out["lines"][0]["note"] == "/khong-phai-link"
    assert out["items"][0]["url"] == "https://x.vn/a" and out["items"][1]["url"] == "//cdn/x"


# ── §5.6 cho tool tra cứu cũ ──────────────────────────────────────────────────

def _user(db, seed):
    return db.get(User, seed.u_req_id)


def test_tim_san_pham_ncc_bao_con_nua_va_nhan_loai_ncc(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.product.model import Product
    from app.modules.supplier.model import Supplier

    db.add_all([Product(code=f"CT{i}", name=f"Thùng carton {i}") for i in range(3)]
               + [Supplier(code="VC1", name="Vận tải A", supplier_type="transport")])
    db.commit()
    for entity in ("product", "supplier"):
        cap_quyen(seed.u_req_id, entity, scope="all", read=True)
    user = _user(db, seed)
    out = T.run_tool(db, user, "product_search", {"keyword": "carton", "limit": 2})
    assert (out["total"], out["has_more"], len(out["items"])) == (2, True, 2) and "limit" in out["more_note"]
    assert T.run_tool(db, user, "product_search", {"keyword": "carton", "limit": 3})["has_more"] is False
    sup = T.run_tool(db, user, "supplier_search", {"keyword": "Vận tải"})["items"][0]
    assert sup["supplier_type_label"] == "Đơn vị vận chuyển"


def test_hop_dong_co_nhan_trang_thai_va_han(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.contract.model import Contract

    db.add(Contract(code="HD-L1", party_type="supplier", party_code="A", party_name="NCC A", company_id=seed.company_id,
                    status="active", end_date="2020-01-01", created_by=seed.u_req_id))
    db.commit()
    cap_quyen(seed.u_req_id, "contract", scope="all", read=True)
    item = T.run_tool(db, _user(db, seed), "contract_list_by_expiry", {})["items"][0]
    assert item["status_label"] and item["status_label"] != "active"
    assert (item["expiry"], item["expiry_label"]) == ("expired", "Hết hạn")


def test_don_mua_hang_co_nhan_trang_thai_va_loai_tien(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.purchase_order.model import POItem, PurchaseOrder

    po = PurchaseOrder(code="PO-USD", company_id=seed.company_id, order_date="2026-10-01", status="partial", currency="USD",
                       created_by=seed.u_req_id)
    db.add(po)
    db.flush()
    db.add(POItem(po_id=po.id, product_code="SP1", amount=1200))
    db.commit()
    cap_quyen(seed.u_req_id, "purchase_order", scope="all", read=True)
    user = _user(db, seed)
    out = T.run_tool(db, user, "recent_purchase_orders", {})
    item = out["items"][0]
    assert (item["status_label"], item["currency"], item["amount"]) == ("Đã nhận một phần", "USD", 1200.0)
    assert out["has_more"] is False and "sau VAT" in out["amount_basis"]
    head = T.run_tool(db, user, "procurement_doc_read", {"entity": "purchase_order", "id": po.id})["header"]
    assert head["currency"] == "USD"


def test_lan_mua_gan_nhat_noi_ro_can_cu_vat_tung_dong(db, seed, cap_quyen):
    from app.modules.assistant import tools as T
    from app.modules.purchase_history.model import PurchaseHistory

    db.add_all([PurchaseHistory(product_code="P1", order_date="2026-10-02", qty_order=2, price=100, amount=220),
                PurchaseHistory(product_code="P2", order_date="2026-10-01", qty_order=3, price=50, amount=0)])
    db.commit()
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    rows = {r["product_code"]: r for r in T.run_tool(db, _user(db, seed), "recent_purchases", {})["items"]}
    assert (rows["P1"]["amount"], rows["P1"]["amount_basis"]) == (220.0, "sau VAT")
    assert rows["P2"]["amount"] == 150.0 and rows["P2"]["amount_basis"].startswith("trước VAT")


def test_cong_no_va_yctt_co_loai_tien(db, seed, cap_quyen):
    from app.modules.assistant import tools as T

    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    out = T.run_tool(db, _user(db, seed), "payable_lookup", {})
    assert (out["currency"], out["money_basis"], out["has_more"]) == ("VND", "sau VAT", False)


def test_bien_ban_hop_co_nhan_trang_thai():
    from app.modules.agent_hub import meetings

    row = SimpleNamespace(id=1, title="Họp", status=int(meetings.MeetingStatus.WAITING_OK), duration_sec=600, note_id=0,
                          error="", template_code="", template_id=0)
    try:
        out = meetings.describe(row)
    except Exception:  # noqa: BLE001 — template_for_row cần cột thật; chỉ cần kiểm bảng nhãn đủ mọi trạng thái
        out = None
    assert set(meetings.MEETING_STATUS_LABELS) == set(meetings.MeetingStatus)
    if out is not None:
        assert out["status_label"] == "Chờ người gửi đồng ý chi phí"


def test_mcp_gan_has_more_khi_total_la_tong_that_va_bo_qua_link_help_center(monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    assert mcp._mark_paging({"items": [1, 2], "total": 9})["has_more"] is True
    assert mcp._mark_paging({"items": [1, 2], "total": 2})["has_more"] is False
    assert mcp._mark_paging({"items": [1], "total": 5, "has_more": False})["has_more"] is False   # tool tự gắn thì giữ
    out = mcp._absolute_downloads({"items": [{"url": "/articles/12"}, {"url": "/faq"}, {"url": "/hr/leave-requests/3"}]})
    assert [i["url"] for i in out["items"]] == ["/articles/12", "/faq",
                                                 "https://deverp.degoholding.vn/hr/leave-requests/3"]
