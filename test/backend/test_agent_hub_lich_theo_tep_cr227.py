"""ai-CR-227 — lô vá hẹp Lạc Lạc tạo lịch (đại ca gật 19/10/2026, Agent 1 soi run #365–369, tin #969–#973 trên dev).

Lỗi thật → bài kiểm:
  1. tạo lịch KHÔNG theo tệp (01:30 «Dừng Long Thành», 04:00 «Ăn sáng Phan Thiết» trong khi tệp ghi 01:30 ngủ khách sạn
     Ruby Trảng Bom, 05:15 xăng, 09:00 ăn sáng Tazon) → máy tách bảng giờ (`plan_extract`), tạo đúng theo số thứ tự;
  2. bịa link `maps.app.goo.gl/HangRai` → URL không có nguyên văn trong tin người dùng / tệp / kết quả công cụ bị bỏ (cả
     trong câu trả lời lẫn mô tả sự kiện);
  3. «21/11/2026 Thứ Sáu» → thứ tính bằng lịch;
  4. tạo lịch chồng giờ → chặn trước khi tạo;
  5. «✅» trong tin bot → lọc.
"""
import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.modules.agent_hub import core_v2, plan_extract, reply_guard, service
from app.modules.agent_hub.constants import ACT_ANSWER, ACT_ASKED, DIR_IN, DIR_OUT
from app.modules.agent_hub.model import AgentMessage
from app.modules.assistant.provider.base import ChatResult

CHAT = "5552"
MAP_1A = ("https://www.google.com/maps/dir/?api=1&origin=Can%20Tho&destination=10.9564418%2C106.9971356"
          "&travelmode=two-wheeler")
MAP_2A = "https://www.google.com/maps/dir/?api=1&origin=11.5758678%2C108.9963583&travelmode=two-wheeler"
PLAN = f"""# CHUYẾN ĐI PHAN RANG – LONG HẢI · 4 NGÀY 3 ĐÊM
- **Thời gian:** Tối thứ Năm 19/11 → chiều thứ Hai 23/11/2026

## NGÀY 1 · Tối thứ Năm 19/11 → thứ Sáu 20/11
**🗺️ Đoạn 1A – Cần Thơ → Trảng Bom (ngủ)** · ~210km · [Mở map]({MAP_1A})

| Giờ | Điểm dừng | Làm gì | Ghi chú |
|---|---|---|---|
| 21:00 | Cần Thơ | Xuất phát | Đổ đầy bình trước khi đi |
| 23:00 | ⛽ **Petrolimex CHXD số 32** – Trung An, gần Mỹ Tho (QL1A) | Xăng lần 1, WC, nghỉ 15 phút | Mở 24/24 |
| ~01:30 | 🛏️ **Khách sạn Ruby Trảng Bom** – Đ. Hùng Vương, Trảng Bom | **Ngủ ~3,5 tiếng** | ☎ gọi đặt trước |
| 05:15 | ⛽ **Petrolimex CHXD số 11** – 61 QL1A, An Viễn, Trảng Bom | Xăng lần 2 (đổ đầy) | Mở 24/24 |
| 09:00 | 🍚 **Quán Cơm Tazon** – QL1A, Thôn 1, Hàm Thuận | Ăn sáng, nghỉ ~45 phút | Mở 6:30–19:00 |

## NGÀY 2 · Thứ Bảy 21/11
**🗺️ Đoạn 2A – Phan Rang → Hang Rái → Vĩnh Hy** · ~45km · [Mở map]({MAP_2A})

| Giờ | Điểm dừng | Làm gì | Ghi chú |
|---|---|---|---|
| 07:15 | 🏞️ **Khu du lịch Hang Rái** – Ninh Hải | Tham quan 1–1,5 tiếng | Mở 5:30–17:30 |
| 25:00 | Giờ hỏng | bỏ | |
| 09:00 | ⛴️ **Bến tàu đáy kính Vĩnh Hy** | Tàu đáy kính ~2 tiếng | |
"""


# ── 1. Tách lịch từ tệp ──────────────────────────────────────────────────────

def test_tach_dung_gio_ten_diem_qua_nua_dem_va_thu():
    out = plan_extract.extract(PLAN, date(2026, 10, 19))
    ev = {e["stt"]: e for e in out["su_kien"]}
    assert len(ev) == 7 and any("Giờ lạ" in w for w in out["canh_bao"])
    assert ev[3]["bat_dau"] == "2026-11-20T01:30" and ev[3]["tieu_de"].startswith("Khách sạn Ruby Trảng Bom")
    assert ev[3]["ket_thuc"] == "2026-11-20T05:00"                          # «Ngủ ~3,5 tiếng»
    assert ev[4]["bat_dau"] == "2026-11-20T05:15" and ev[5]["tieu_de"].startswith("Quán Cơm Tazon")
    assert ev[5]["ket_thuc"] == "2026-11-20T09:45"                          # «nghỉ ~45 phút»
    assert (ev[1]["thu"], ev[3]["thu"], ev[6]["thu"]) == ("Thứ Năm", "Thứ Sáu", "Thứ Bảy")
    assert "Long Thành" not in json.dumps(out, ensure_ascii=False)
    assert MAP_1A in ev[1]["mo_ta"] and MAP_2A in ev[6]["mo_ta"] and "http" not in ev[2]["mo_ta"]
    assert "⛽" not in ev[2]["tieu_de"] and "**" not in ev[3]["tieu_de"]
    starts = [e["bat_dau"] for e in out["su_kien"]]
    assert starts == sorted(starts)


def test_tep_khong_co_bang_gio_hoac_rong():
    assert plan_extract.extract("", date(2026, 10, 19))["su_kien"] == []
    assert plan_extract.extract("# Ghi chú\nkhông có bảng", date(2026, 10, 19))["su_kien"] == []
    bad_date = "## NGÀY 1 · 31/02\n| Giờ | Điểm dừng |\n|---|---|\n| 08:00 | A |\n"
    out = plan_extract.extract(bad_date, date(2026, 10, 19))
    assert out["su_kien"] == [] and out["canh_bao"]


@pytest.fixture
def chat(db, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    user = SimpleNamespace(id=275, is_active=True, email="dai.ca@dego.com", name="Đại ca")
    monkeypatch.setattr(service, "_assistant_user", lambda db_, chat_id="": user)
    monkeypatch.setattr(core_v2.user_keys, "active_key", lambda: "khoa-gia")
    monkeypatch.setattr(core_v2.erp, "describe", lambda db_, u: ("Đại ca", ""))
    monkeypatch.setattr(core_v2.erp, "tool_defs", lambda db_, u=None: [])
    monkeypatch.setattr(core_v2.erp, "caller_context", lambda db_, u: None)
    monkeypatch.setattr(core_v2.erp, "glossary_block", lambda db_, texts: None)
    monkeypatch.setattr(core_v2.erp, "skill_list", lambda db_, u, *a, **k: {"items": []})
    created: list[dict] = []

    def run_tool(db_, u, name, args):
        if name == "create_calendar_event":
            created.append(dict(args))
            return {"ok": True, "html_link": "https://calendar.google.com/event?eid=abc"}
        return {"ok": True}

    monkeypatch.setattr(core_v2.erp, "run_tool", run_tool)
    monkeypatch.setattr(core_v2.telegram, "download_file", lambda fid, max_bytes: (PLAN.encode(), "p"))
    sent: list[str] = []
    monkeypatch.setattr(core_v2.telegram, "send", lambda text, buttons=None, chat_id="": sent.append(text) or 1)
    monkeypatch.setattr(core_v2.telegram, "send_chat_action", lambda *a, **k: None)
    db.add(AgentMessage(chat_id=CHAT, direction=DIR_IN, body="[tệp ke-hoach.md] xem giúp", action=ACT_ASKED,
                        created_at=datetime.now() - timedelta(minutes=20),
                        files=[{"kind": "doc", "file_id": "f1", "name": "ke-hoach.md", "mime": "text/markdown"}]))
    db.commit()
    return SimpleNamespace(user=user, sent=sent, created=created)


def _incoming(db, text, minutes_ago=0):
    row = service.log_message(db, DIR_IN, CHAT, 0, text, action="")
    row.created_at = datetime.now() - timedelta(minutes=minutes_ago)
    db.commit()
    return row


class FakeProvider:
    name = "agent_gemini"
    supports_tools = True

    def __init__(self, script):
        self.script = script

    def run_tools(self, msgs, *, tools, execute, system=None, **kw):
        return self.script(msgs, tools, execute)


def _result(text, calls=None):
    return ChatResult(text=text, provider="openai_compat", model="claude", input_tokens=1, output_tokens=1,
                      tool_calls=calls or [])


def _install(monkeypatch, script):
    monkeypatch.setattr(core_v2.manager, "get_provider", lambda: FakeProvider(script))


def test_tao_lich_theo_tep_dung_gio_trong_tep_sau_khi_duyet(db, chat, monkeypatch):
    listed = {}

    def first(msgs, tools, execute):
        listed.update(execute("events_from_file", {"ngay": "20/11"}))
        refused = execute("create_events_from_file", {"stt": [3]})           # chưa duyệt → không tạo
        assert "CHƯA tạo" in refused["error"]
        return _result("Danh sách 4 sự kiện ngày 20/11 đây anh, ưng thì nhắn ok.")
    _install(monkeypatch, first)
    core_v2.handle(db, CHAT, _incoming(db, "tạo lịch ngày 20/11 theo tệp giúp anh"), "tạo lịch ngày 20/11 theo tệp giúp anh")
    assert [e["gio"][:5] for e in listed["su_kien"]] == ["01:30", "05:15", "09:00"] and not chat.created
    assert listed["doan_map"] == [] or all("google.com/maps" in m["url"] for m in listed["doan_map"])

    def second(msgs, tools, execute):
        out = execute("create_events_from_file", {"stt": [3, 4, 5, 3, "x", 99]})
        assert [d["stt"] for d in out["da_tao"]] == [3, 4, 5] and out["chua_tao"][0]["stt"] == 99
        return _result("Em đã tạo 3 sự kiện.", [{"name": "create_events_from_file", "result": out}])
    _install(monkeypatch, second)
    core_v2.handle(db, CHAT, _incoming(db, "ok"), "ok")
    assert [(c["start"], c["title"].split(" — ")[0]) for c in chat.created] == [
        ("2026-11-20T01:30", "Khách sạn Ruby Trảng Bom"), ("2026-11-20T05:15", "Petrolimex CHXD số 11"),
        ("2026-11-20T09:00", "Quán Cơm Tazon")]


# ── 2. Link bịa ───────────────────────────────────────────────────────────────

def test_link_bia_bi_bo_ca_trong_cau_tra_loi_lan_mo_ta_su_kien(db, chat, monkeypatch):
    service.log_message(db, DIR_OUT, CHAT, 0, "Em soạn sự kiện Hang Rái, anh ưng thì nhắn ok.", action=ACT_ANSWER)
    db.commit()

    def script(msgs, tools, execute):
        execute("read_chat_file", {})                                     # link thật vào danh sách được phép
        execute("create_calendar_event", {"title": "Hang Rái", "start": "2026-11-21T07:15:00", "duration_minutes": 90,
                                          "description": f"Map: https://maps.app.goo.gl/HangRai và {MAP_2A}"})
        return _result(f"✅ Xong: Hang Rái **Thứ Sáu 21/11/2026**, map https://maps.app.goo.gl/HangRai — đoạn 2A: {MAP_2A}",
                       [{"name": "create_calendar_event", "result": {"ok": True}}])
    _install(monkeypatch, script)
    core_v2.handle(db, CHAT, _incoming(db, "ok"), "ok")
    desc = chat.created[0]["description"]
    assert "maps.app.goo.gl" not in desc and MAP_2A in desc
    reply = chat.sent[-1]
    assert "maps.app.goo.gl" not in reply and "google.com/maps/dir" in reply
    assert "Thứ Bảy 21/11/2026" in reply and "Thứ Sáu" not in reply and "✅" not in reply


def test_link_nguoi_dung_tu_dan_duoc_giu():
    own = "https://maps.app.goo.gl/AbCdEf123"
    allowed = reply_guard.urls_in(f"anh lưu link này nhé {own}.")
    text, removed = reply_guard.strip_unknown_urls(f"Em ghi link anh gửi: {own}. Thêm [map](https://bia.example/x)", allowed)
    assert own in text and removed == ["https://bia.example/x"] and "map (link em không kiểm" in text


# ── 3–5. Hàm hậu kiểm ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("wrong,right", [
    ("NGÀY 2 - Thứ Sáu 21/11", "NGÀY 2 - Thứ Bảy 21/11"),
    ("21/11/2026 (Thứ Sáu)", "21/11/2026 (Thứ Bảy)"),
    ("thứ 6, ngày 21/11", "thứ 7, ngày 21/11"),
    ("T6 21/11", "T7 21/11"),
    ("Chủ nhật 22/11", "Chủ nhật 22/11"),                     # đúng rồi thì giữ nguyên
    ("thứ hai 5/1", "thứ ba 5/1"),                             # nói vào tháng 10 → tháng 1 NĂM SAU (5/1/2027 thứ Ba)
    ("Thứ Sáu 31/02", "Thứ Sáu 31/02"),                        # ngày không có thật → không đụng
])
def test_sua_thu_theo_lich(wrong, right):
    assert reply_guard.fix_weekdays(wrong, date(2026, 10, 19))[0] == right


def test_khong_dung_vao_cau_khong_co_thu_hay_phan_so():
    for t in ("Chặng 1/2 đã xong", "Mở 6:30–19:00", "giá 80–130k/người", "ngày 21/11 em rảnh"):
        assert reply_guard.fix_weekdays(t, date(2026, 10, 19)) == (t, 0)


def test_chong_gio_va_khoang_vo_ly():
    s = datetime(2026, 11, 20, 1, 30)
    made = [("Ngủ", s, s + timedelta(hours=3, minutes=30))]
    assert "chồng giờ" in reply_guard.overlapping((s + timedelta(hours=1), s + timedelta(hours=2)), made)
    assert reply_guard.overlapping((s + timedelta(hours=3, minutes=30), s + timedelta(hours=4)), made) is None
    assert "không sau" in reply_guard.overlapping((s, s), [])
    assert "24 giờ" in reply_guard.overlapping((s, s + timedelta(days=2)), [])
    assert reply_guard.event_span({"start": "2026-11-20T01:30:00+07:00"})[1] == datetime(2026, 11, 20, 2, 30)
    assert reply_guard.event_span({"start": "không phải giờ"}) is None


def test_chong_gio_trong_mot_luot_bi_chan_truoc_khi_tao(db, chat, monkeypatch):
    service.log_message(db, DIR_OUT, CHAT, 0, "Em soạn 2 sự kiện, anh ưng thì nhắn ok.", action=ACT_ANSWER)
    db.commit()
    outs = []

    def script(msgs, tools, execute):
        outs.append(execute("create_calendar_event", {"title": "A", "start": "2026-11-20T01:30:00", "end": "2026-11-20T05:00:00"}))
        outs.append(execute("create_calendar_event", {"title": "B", "start": "2026-11-20T04:00:00", "duration_minutes": 60}))
        return _result("Em tạo A, B bị chồng giờ nên chưa tạo.", [{"name": "create_calendar_event", "result": outs[0]}])
    _install(monkeypatch, script)
    core_v2.handle(db, CHAT, _incoming(db, "ok"), "ok")
    assert [c["title"] for c in chat.created] == ["A"] and "chồng giờ" in outs[1]["error"]


def test_bo_emoji_giu_chu():
    assert reply_guard.strip_emoji("✅ **21:00** - Xuất phát\n⛽ Đổ xăng 🛏️ ngủ") == "**21:00** - Xuất phát\nĐổ xăng ngủ"
    assert reply_guard.strip_emoji("Không có gì — giữ nguyên «x» 1/2") == "Không có gì — giữ nguyên «x» 1/2"


def test_luat_uoc_luong_khoang_cach_trong_system():
    assert "chưa tra bản đồ" in core_v2.CORE_RULES and "events_from_file" in core_v2.CORE_RULES
