"""ai-CR-240 — kết quả các tool ghi phiếu qua MCP trả link sâu mở THẲNG hộp đính tệp (`?attach=1`) của đúng chỗ.

- hàm dựng link dùng chung `assistant.tools.attach_link.build_attach_url` (ĐMH · Đề nghị thanh toán · Phiếu khảo sát ·
  YCBG); loại lạ / id sai không bịa link; tham số lạ là lỗi lập trình;
- lần giao ĐMH: nháp mở hộp đính tệp của lần giao có sẵn; lần giao MỚI lúc soạn chỉ mở đúng dòng (chưa có chỗ đính),
  sau khi ghi mở hộp đính tệp của đúng lần giao vừa thêm (theo số thứ tự);
- Đề nghị thanh toán Nháp (ai-CR-236) và YCBG tạo qua confirm_draft: `attach_url` tuyệt đối + câu dặn đưa link;
- link chỉ là đường màn web (không token, không đường tải ẩn danh).
"""
# ruff: noqa: F811  (fixture dùng chung từ bài bao-CR-740 / ai-CR-236)
from urllib.parse import parse_qs, urlparse

import pytest

from app.modules.agent_hub import erp, mcp, mcp_keys
from app.modules.assistant.tools.attach_link import build_attach_url
from app.modules.purchase_order.model import PODelivery

from test_assistant_ghi_lan_nhan_hang_cr740 import SUP, _item, _receive, kho  # noqa: F401
from test_mcp_tao_de_nghi_thanh_toan_nhap_cr236 import _call, _draft, mo_nhom_finance, nguoi_lap, no  # noqa: F401

INV = {"invoice_no": "6265", "invoice_date": "2026-11-12"}


def _query(url: str) -> dict:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_ham_dung_link_dung_chung():
    assert build_attach_url("purchase_order", 7, delivery=800) == "/procurement/purchase-orders/7?delivery=800&attach=1"
    assert build_attach_url("purchase_order", 7, line=5, delivery_no=3) == \
        "/procurement/purchase-orders/7?line=5&delivery_no=3&attach=1"
    assert build_attach_url("purchase_order", 7, open_upload=False, line=5) == "/procurement/purchase-orders/7?line=5"
    assert build_attach_url("payment_request", 12) == "/finance/payment-requests/12?attach=1"
    assert build_attach_url("survey", 3) == "/procurement/surveys/3?attach=1"
    assert build_attach_url("survey_request", 4, line=9) == "/procurement/survey-requests/4?line=9&attach=1"
    #  Không bịa link: loại lạ, id sai / âm / chữ → rỗng; tham số chọn chỗ ≤ 0 thì bỏ.
    assert build_attach_url("contract", 1) == "" and build_attach_url("survey", 0) == ""
    assert build_attach_url("survey", "abc") == "" and build_attach_url("survey", -3) == ""
    assert build_attach_url("purchase_order", 7, delivery=0) == "/procurement/purchase-orders/7?attach=1"
    with pytest.raises(ValueError):
        build_attach_url("purchase_order", 7, token="x")


def test_nhap_ghi_hoa_don_mo_hop_dinh_tep_cua_lan_giao(kho, db, mcp_all_groups):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "invoice_deliveries": [d.id], **INV})
    (link,) = out["attach_links"]
    assert link["url"].startswith("http") and link["opens_upload"] is True
    assert urlparse(link["url"]).path.endswith(f"/procurement/purchase-orders/{kho.po712.id}")
    assert _query(link["url"]) == {"delivery": str(d.id), "attach": "1"}
    assert "hộp đính tệp" in out["note"] and "đăng nhập" in out["note"]


def test_lan_giao_moi_sau_khi_ghi_mo_dung_lan_giao_vua_them(kho, db, mcp_all_groups):
    _receive(db, kho.po807, "NAP0156", 100)                       # dòng đã có lần giao số 1
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "slip_date": "2026-11-12", "lines": [{"product_code": "NAP0156", "qty": 10}],
                         **INV})
    item = _item(db, kho.po807, "NAP0156")
    (row,) = out["draft"]["rows"]
    assert row["op"] == "add" and row["planned_delivery_no"] == 2
    (link,) = out["attach_links"]
    assert _query(link["url"]) == {"line": str(item.id)} and link["opens_upload"] is False     # chưa có chỗ đính
    ok = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "po_receipt", "draft": out["draft"]})
    (link,) = ok["attach_links"]
    assert link["url"].startswith("http") and link["opens_upload"] is True
    assert _query(link["url"]) == {"line": str(item.id), "delivery_no": "2", "attach": "1"}
    new = db.query(PODelivery).filter(PODelivery.po_item_id == item.id, PODelivery.delivery_no == 2).one()
    assert float(new.received_qty) == 10 and new.invoice_no == "6265"     # đúng lần giao vừa ghi


def test_de_nghi_thanh_toan_nhap_tra_link_mo_hop_dinh_tep(db, no, nguoi_lap, mo_nhom_finance):
    out = _call(db, nguoi_lap, {"kind": "payment", "draft": _draft(no)})
    assert out["attach_url"].startswith("http")
    assert out["attach_url"].endswith(f"/finance/payment-requests/{out['id']}?attach=1")
    assert out["items"][0]["attach_url"] == out["attach_url"]
    assert "attach_url" in out["note"] and "đăng nhập" in out["note"]


def test_ycbg_tao_qua_mcp_tra_link_mo_hop_dinh_tep(db, seed, monkeypatch):
    monkeypatch.setattr(erp, "create_draft", lambda db, user, kind, draft: ("YCBG00055", 55))
    monkeypatch.setattr(erp, "created_details", lambda db, kind, oid: [])
    out = mcp._confirm_draft(db, object(), {"kind": "survey", "draft": {"lines": []}})
    assert out["ok"] and out["attach_url"].startswith("http")
    assert out["attach_url"].endswith("/procurement/survey-requests/55?attach=1")
    assert "attach_url" in out["note"]
    #  Loại không có chỗ đính tệp trong phạm vi CR này: không thêm link.
    monkeypatch.setattr(erp, "create_draft", lambda db, user, kind, draft: ("NP0001", 1))
    assert "attach_url" not in mcp._confirm_draft(db, object(), {"kind": "leave", "draft": {}})


def test_link_khong_chua_token_hay_duong_tai_an_danh(kho, db, mcp_all_groups):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "invoice_deliveries": [d.id], **INV})
    url = out["attach_links"][0]["url"]
    assert set(_query(url)) <= {"delivery", "line", "delivery_no", "attach"} and "/api/" not in url
