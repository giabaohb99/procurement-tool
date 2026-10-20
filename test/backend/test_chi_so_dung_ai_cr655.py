"""duoc-CR-655 (D0d) — nhóm chỉ số 3.8 «Dùng AI»: chưa thu → NOT_COLLECTED, đã thu → đếm đúng, số truy vấn nguồn cố định,
không lộ chuỗi tự do. Nguồn `tab_ai_usage_daily` + `tab_audit_log.ai_channel` do ai-CR-230 dựng.
"""
import json
from datetime import timedelta

from app.core.ai_usage_codes import AiClient, ai_client_code
from app.core.logging_codes import AI_CHANNEL_MCP, AI_CHANNEL_TELEGRAM, AI_CHANNEL_WEB
from app.core.usage_codes import UnmeasuredReason as Why
from app.modules.ai_usage.model import AiUsageDaily
from app.modules.audit.model import AuditLog
from app.modules.usage_profile.metric_catalog import METRIC_CATALOG
from app.modules.usage_profile.snapshot_builder import build_snapshots
from app.modules.usage_profile.snapshot_metrics_ai import AI_KEYS
from app.modules.usage_profile.snapshot_sources import load_snapshot_sources

from ho_so_lam_viec_factory import vn
from lich_lam_viec_factory import count_queries
from test_ho_so_lam_viec_snapshot_cr641 import FIRST, WEEK, make_world, snap


def ai_row(db, user, day, channel, turns=0, **kw):
    db.add(AiUsageDaily(day=day, user_id=user.id, channel=channel, turns=turns, clients=kw.pop("clients", {}),
                        tool_groups=kw.pop("tool_groups", {}), **kw))


def test_chua_thu_thi_ca_tam_khoa_la_not_collected_khong_ghi_0(db):
    people, _ = make_world(db, 3, tag="A1")
    build_snapshots(db, WEEK)
    m = snap(db, people[0][0]).metrics
    for key in AI_KEYS:
        assert key not in m["metrics"], key
        assert m["unmeasured"][key] == int(Why.NOT_COLLECTED), key
    assert "ai_channels" not in m["lists"]


def test_da_thu_dem_dung_theo_nguoi(db):
    people, _ = make_world(db, 3, tag="A2", docs={"purchase_request": {"c": 1}})
    (u0, _e0), (u1, _e1), (u2, _e2) = people
    # u0: web 5 + MCP 3 (Claude) qua 2 ngày; u1 có dòng ở tuần cũ ngoài cửa sổ (chỉ để mốc thu); u2 không dùng
    ai_row(db, u0, FIRST + timedelta(days=1), AI_CHANNEL_WEB, 5, tool_calls=2, drafts_created=1,
           tool_groups={"mine": 2})
    ai_row(db, u0, FIRST + timedelta(days=2), AI_CHANNEL_MCP, 3, tool_calls=3, denied=2, drafts_confirmed=1,
           clients={"Claude Desktop": 3}, tool_groups={"leave": 1, "mine": 2})
    ai_row(db, u1, FIRST - timedelta(days=30), AI_CHANNEL_TELEGRAM, 9)
    # u0 lập 2 phiếu qua AI (một phiếu bị ghi 2 lần), 1 dòng ngoài danh mục phiếu, 1 dòng người tự bấm
    for eid in (101, 101, 102):
        db.add(AuditLog(entity="purchase_request", entity_id=eid, action="create", created_by=u0.id, ai_channel=3,
                        created_at=vn(FIRST + timedelta(days=3), "10:00")))
    db.add(AuditLog(entity="product", entity_id=1, action="create", created_by=u0.id, ai_channel=3,
                    created_at=vn(FIRST + timedelta(days=3), "10:00")))
    db.add(AuditLog(entity="purchase_request", entity_id=103, action="create", created_by=u0.id, ai_channel=0,
                    created_at=vn(FIRST + timedelta(days=3), "10:00")))
    db.commit()
    build_snapshots(db, WEEK)

    m0 = snap(db, u0).metrics
    v = {k: m0["metrics"][k]["v"] for k in AI_KEYS}
    assert v["ai_uses"] == 8 and v["ai_active_days"] == 2
    assert v["ai_mcp_share"] == 0.375 and v["ai_tool_groups_used"] == 2
    assert v["ai_denied"] == 2 and v["ai_drafts_confirmed"] == 1
    assert v["ai_docs_drafted"] == 2
    assert m0["metrics"]["docs_created"]["v"] == 28 and v["ai_docs_share"] == round(2 / 28, 4)
    assert m0["lists"]["ai_channels"] == {str(AI_CHANNEL_WEB): 5, str(AI_CHANNEL_MCP): 3}
    assert m0["lists"]["ai_clients"] == {str(int(AiClient.CLAUDE)): 3}
    assert m0["lists"]["ai_tool_groups"] == [["mine", 4], ["leave", 1]]
    assert m0["metrics"]["assistant_questions"]["v"] == 5

    m2 = snap(db, u2).metrics        # thu rồi mà không dùng = 0 thật, không phải «chưa thu»
    assert m2["metrics"]["ai_uses"]["v"] == 0 and m2["metrics"]["ai_docs_drafted"]["v"] == 0
    assert "ai_mcp_share" in m2["unmeasured"] and m2["unmeasured"]["ai_mcp_share"] == int(Why.NOT_APPLICABLE)
    assert m2["lists"]["ai_channels"] == {}


def test_ai_docs_share_khong_co_phieu_lap_la_not_applicable(db):
    people, _ = make_world(db, 2, tag="A3")
    u = people[0][0]
    ai_row(db, u, FIRST, AI_CHANNEL_WEB, 1)
    db.commit()
    build_snapshots(db, WEEK)
    m = snap(db, u).metrics
    assert "ai_docs_share" not in m["metrics"] and m["unmeasured"]["ai_docs_share"] == int(Why.NOT_APPLICABLE)


def test_nguon_ai_dung_3_truy_van_bat_ke_so_nguoi(db):
    for n, tag in ((2, "A4"), (12, "A5")):
        people, _ = make_world(db, n, tag=tag)
        for u, _e in people:
            ai_row(db, u, FIRST, AI_CHANNEL_WEB, 2)
        db.commit()
    from app.modules.usage_profile.snapshot_sources_ai import load_ai_sources
    from app.modules.usage_profile.snapshot_sources import Window
    _, sql = count_queries(db, lambda: load_ai_sources(db, Window(WEEK)))
    assert len([s for s in sql if s.startswith("SELECT") and ("tab_ai_usage_daily" in s or "tab_audit_log" in s)]) == 3, sql


def test_snapshot_khong_chua_chuoi_tu_do_ngoai_ma_nhom_cong_cu(db):
    people, _ = make_world(db, 2, tag="A6")
    u = people[0][0]
    ai_row(db, u, FIRST, AI_CHANNEL_MCP, 1, clients={"Ứng dụng lạ <script>": 1}, tool_groups={"mine": 1})
    db.commit()
    build_snapshots(db, WEEK)
    text = json.dumps(snap(db, u).metrics)
    assert "script" not in text and "Ứng dụng" not in text     # tên ứng dụng chỉ còn là mã số
    assert snap(db, u).metrics["lists"]["ai_clients"] == {str(int(AiClient.OTHER)): 1}


def test_ma_ung_dung_ai():
    assert ai_client_code("Claude Desktop") == AiClient.CLAUDE
    assert ai_client_code("ChatGPT") == AiClient.CHATGPT and ai_client_code("openai-mcp") == AiClient.CHATGPT
    assert ai_client_code("") == AiClient.OTHER


def test_danh_muc_3_8_du_8_khoa_pha_3():
    keys = [k for k, m in METRIC_CATALOG.items() if m.section == "3.8"]
    assert sorted(keys) == sorted(AI_KEYS) and all(METRIC_CATALOG[k].phase == 3 for k in keys)
