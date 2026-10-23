"""kh-AI2-3 — công cụ `office_read`: đặt xe, duyệt dấu, tồn kho, diễn đàn cho Trợ lý web / bot / cổng MCP. Gọi đúng hàm
route của màn web nên người hỏi chỉ thấy đúng phần mình được xem: pháp nhân A không thấy phiếu pháp nhân B; ngoài phạm
vi và không tồn tại trả cùng một câu; thiếu quyền bị từ chối; không trả số điện thoại / bằng lái."""
from app.modules.assistant import tools as T
from app.modules.forum.model import ForumAudience, ForumPost
from app.modules.seal_request.model import SEAL_APPROVED, SealRequest, SealRequestCompany
from app.modules.vehicle_booking.model import VehicleBooking

from test_pham_vi_tai_chinh_kho_bao_cao import create_inventory


def _seed(world):
    db = world.db
    co_a, co_b = world.co["A"], world.co["B"]
    rows = {}
    for tag, co in (("A", co_a), ("B", co_b)):
        rows[f"bk{tag}"] = VehicleBooking(code=f"DX-{tag}", purpose=f"Đi công tác {tag}", request_type=1, requester_id=0,
                                          company_id=co, department_id=0, status=2, contact_phone="0909123456",
                                          license_number="ZZBANGLAI")
        rows[f"sl{tag}"] = SealRequest(code=f"DD-{tag}", purpose=f"Hợp đồng {tag}", company_id=co, department_id=0,
                                       requester_id=0, status=SEAL_APPROVED)   # phạm vi công ty chỉ thấy phiếu đã duyệt
        rows[f"fp{tag}"] = ForumPost(body=f"ZZTAUHAI tin của {tag}", audience=int(ForumAudience.COMPANY), company_id=co,
                                     created_by=world.actor(f"{tag.lower()}1").user.id)
        db.add_all([rows[f"bk{tag}"], rows[f"sl{tag}"], rows[f"fp{tag}"]])
        create_inventory(db, company_id=co, warehouse_code=f"K_{tag}", product_code=f"SP_{tag}", product_name=f"Hàng {tag}",
                         qty=5, avg_cost=100, value=500)
    db.flush()
    for tag, co in (("A", co_a), ("B", co_b)):
        db.add(SealRequestCompany(seal_request_id=rows[f"sl{tag}"].id, company_id=co))
    db.commit()
    return rows


def _read(user, db, resource, **kw):
    return T.run_tool(db, user, "office_read", {"resource": resource, **kw})


def test_moi_loai_phieu_dung_pham_vi_phap_nhan(world):
    rows = _seed(world)
    a1 = world.grant("a1", "vehicle_booking", scope="company")
    a1.grant("seal_request", scope="company")
    a1.grant("inventory", scope="company")
    db = world.db
    bk = _read(a1.user, db, "vehicle_booking")
    assert [r["code"] for r in bk["items"]] == ["DX-A"] and bk["items"][0]["url"] == f"/vehicle-booking/{rows['bkA'].id}"
    assert "contact_phone" not in bk["items"][0] and "ZZBANGLAI" not in str(bk)
    assert [r["code"] for r in _read(a1.user, db, "seal_request")["items"]] == ["DD-A"]
    inv = _read(a1.user, db, "inventory")
    assert [r["warehouse_code"] for r in inv["items"]] == ["K_A"] and inv["money_fields"] == {"avg_cost": "", "value": ""}
    forum = _read(a1.user, db, "forum_post", filters={"q": "ZZTAUHAI"})
    assert [r["id"] for r in forum["items"]] == [rows["fpA"].id] and "body" in forum["items"][0]
    #  Chi tiết: ngoài phạm vi và không tồn tại trả cùng một câu.
    assert _read(a1.user, db, "vehicle_booking", id=rows["bkA"].id)["item"]["code"] == "DX-A"
    other = _read(a1.user, db, "vehicle_booking", id=rows["bkB"].id)["error"]
    ghost = _read(a1.user, db, "vehicle_booking", id=987654)["error"]
    assert other.replace(str(rows["bkB"].id), "?") == ghost.replace("987654", "?")
    assert "error" in _read(a1.user, db, "forum_post", id=rows["fpB"].id)
    assert _read(a1.user, db, "seal_request", id=rows["slA"].id)["item"]["code"] == "DD-A"


def test_thieu_quyen_bi_tu_choi_va_tham_so_la(world):
    _seed(world)
    a1 = world.grant("a1", "payable", scope="company")
    db = world.db
    for res in ("vehicle_booking", "seal_request", "inventory"):
        assert _read(a1.user, db, res).get("denied") is True, res
    assert "error" in _read(a1.user, db, "purchase_order")              # resource của erp_read không mở ở đây
    out = _read(a1.user, db, "forum_post", filters={"q": "ZZTAUHAI", "la": "x"}, page_size=500)
    assert out["page_size"] == 50 and out["ignored_filters"] == ["la"]


def test_khai_du_o_cong_mcp_va_bo_loc():
    from app.modules.agent_hub import intent_ledger, mcp, mcp_settings
    from app.modules.assistant import tool_router

    assert "office_read" in mcp.READ_TOOLS and "office_read" in mcp.ROW_BUDGET_TOOLS
    assert mcp_settings.GROUP_OF["office_read"].key == "office" and "office_read" in intent_ledger.TOOL_SUB
    for q in ("Chuyến đặt xe đi Cần Thơ của anh tới đâu", "Phiếu duyệt dấu hợp đồng", "Tồn kho giấy A4", "Tìm bài diễn đàn"):
        assert "office" in tool_router.groups_for(q), q
