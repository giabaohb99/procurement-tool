"""ai-CR-163 (phase 22) — đọc video YouTube công khai thành biên bản / tóm tắt qua Gemini (không tải video), và luật ước tính
chi phí trước khi chạy cho MỌI tệp họp: dưới 1 USD chạy luôn; từ 1 USD hoặc dài hơn 2 giờ thì hỏi ok / thôi."""
import pytest

from app.modules.agent_hub import meetings as mt

ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize("link", [f"https://www.youtube.com/watch?v={ID}", f"https://youtu.be/{ID}?t=30",
                                  f"https://youtube.com/shorts/{ID}", f"https://www.youtube.com/live/{ID}",
                                  f"https://m.youtube.com/watch?feature=share&v={ID}"])
def test_nhan_cac_dang_link(link):
    assert mt.youtube_url(f"tóm tắt giúp anh {link}") == f"https://www.youtube.com/watch?v={ID}"


def test_link_tron_khong_nhan_va_chon_mau():
    assert not mt.wants_youtube(f"https://youtu.be/{ID}")
    assert mt.wants_youtube(f"báo cáo video này https://youtu.be/{ID}")
    assert mt.youtube_template(None, 0, "tóm tắt video này").key == "tom_tat_video"
    assert mt.youtube_template(None, 0, "làm biên bản buổi họp này").key == mt.DEFAULT_TEMPLATE


def test_uoc_chi_phi_va_nguong_hoi():
    small = mt.estimate_cost(3600)                     # họp 1 giờ: rẻ, chạy luôn
    assert 0 < small["usd"] < mt.COST_CONFIRM_USD
    long = mt.estimate_cost(5 * 3600, youtube=True)
    assert long["minutes"] == 300 and long["usd"] > small["usd"]
    row = type("R", (), {"steps": []})()
    assert not mt.needs_ok(row, small, 3600)
    assert mt.needs_ok(row, small, 2 * 3600 + 1)        # dài hơn 2 giờ: luôn hỏi
    assert mt.needs_ok(row, {"usd": 1.2}, 600)
    row.steps = [int(mt.Progress.COST_OK)]
    assert not mt.needs_ok(row, {"usd": 5}, 9000)


def _row(db, **kw):
    from app.modules.agent_hub.model import AgentMeeting

    base = dict(user_id=7, chat_id="12345", source_kind=int(mt.SourceKind.YOUTUBE),
                source_ref=f"https://www.youtube.com/watch?v={ID}", title="Webinar giá thép", mime="video/youtube",
                status=int(mt.MeetingStatus.QUEUED), created_by=0, updated_by=0)
    base.update(kw)
    row = AgentMeeting(**base)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def env(db, monkeypatch):
    from app.modules.agent_hub import db_backup, meeting_actions, service

    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(db_backup, "alert", lambda db, text: None)
    monkeypatch.setattr(mt.user_keys, "gemini_key", lambda: "AIza-k")
    monkeypatch.setattr(mt.telegram, "send_document", lambda *a, **k: 1)
    monkeypatch.setattr(mt, "_upload_word", lambda *a, **k: "")
    monkeypatch.setattr(meeting_actions, "offer", lambda db, row: 0)
    monkeypatch.setattr(mt.personal_memory, "add_note", lambda *a, **k: {"note_id": 1})
    monkeypatch.setattr(mt, "_ask_logged", lambda db, row, system, content, **kw: "## TÓM TẮT NHANH\n- Giá thép tăng 5%")
    return sent


def test_video_youtube_cong_khai_thanh_tom_tat(db, env, monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(mt, "youtube_tokens", lambda key, url, model: int(600 * mt.YT_TOKENS_PER_SEC))

    def fake_transcribe(key, file_uri, mime, model, **kw):
        calls.append(kw)
        return "[00:10] Người 1: giá thép tháng này tăng 5%", {"model": "gemini", "promptTokenCount": 27000}

    monkeypatch.setattr(mt, "gemini_transcribe", fake_transcribe)
    row = _row(db, template="tom_tat_video")
    out = mt.process(db, row.id)
    db.refresh(row)
    assert out["status"] == "done" and row.duration_sec == 600 and "tăng 5%" in row.transcript
    part = calls[0]["part"]
    assert part["file_data"]["file_uri"].endswith(ID) and calls[0]["extra_config"]["mediaResolution"].endswith("LOW")
    assert "Bỏ qua hình ảnh" in calls[0]["prompt"]


def test_video_rieng_tu_va_khong_loi_noi(db, env, monkeypatch):
    sent = env

    class R:
        status_code = 403
        text = "The video is private or unavailable"

    monkeypatch.setattr(mt.requests, "post", lambda *a, **k: R())
    row = _row(db)
    assert mt.process(db, row.id)["status"] == "error" and "CÔNG KHAI" in sent[-1]
    monkeypatch.setattr(mt, "youtube_tokens", lambda key, url, model: int(300 * mt.YT_TOKENS_PER_SEC))
    monkeypatch.setattr(mt, "gemini_transcribe", lambda *a, **k: (mt.NO_SPEECH, {"model": "g"}))
    row = _row(db)
    assert mt.process(db, row.id)["status"] == "error" and "không có lời nói" in sent[-1]


def test_dat_hon_nguong_thi_hoi_ok_roi_moi_chay(db, env, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    sent = env
    monkeypatch.setattr(mt, "youtube_tokens", lambda key, url, model: int(3 * 3600 * mt.YT_TOKENS_PER_SEC))
    transcribed: list = []
    monkeypatch.setattr(mt, "gemini_transcribe", lambda *a, **k: transcribed.append(k) or ("[00:05] A: chào", {}))
    dispatched: list[int] = []
    monkeypatch.setattr(mt, "dispatch", lambda mid: dispatched.append(mid))
    row = _row(db)
    out = mt.process(db, row.id)
    db.refresh(row)
    assert out["status"] == "waiting" and row.status == mt.MeetingStatus.WAITING_OK and transcribed == []
    assert "Ước tính chi phí" in sent[-1] and "3 giờ 0 phút" in sent[-1] and "dài hơn 2 giờ" in sent[-1]
    msg = service.log_message(db, DIR_IN, "12345", 5, "ok")
    db.commit()
    assert mt.cost_ok_by_text(db, "12345", msg, "ok") and dispatched == [row.id]
    db.refresh(row)
    assert row.status == mt.MeetingStatus.QUEUED and mt._has(row, mt.Progress.COST_OK)
    out = mt.process(db, row.id)
    assert out["status"] == "done" and len(transcribed) == 18          # 3 giờ = 18 đoạn 10 phút (ai-CR-168)
    #  «thôi» trên thẻ khác → bỏ phiên, không chạy.
    row2 = _row(db)
    mt.process(db, row2.id)
    msg = service.log_message(db, DIR_IN, "12345", 6, "thôi")
    db.commit()
    assert mt.cost_ok_by_text(db, "12345", msg, "thôi")
    db.refresh(row2)
    assert row2.status == mt.MeetingStatus.FAILED and "không làm" in sent[-1]


def test_nhan_link_youtube_trong_chat(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import chat_link, service

    monkeypatch.setattr(settings, "AGENT_TELEGRAM_CHAT_ID", "12345")
    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: type("L", (), {"user_id": 7})())
    dispatched: list[int] = []
    monkeypatch.setattr(mt, "dispatch", lambda mid: dispatched.append(mid))
    text = f"tóm tắt video này giúp anh https://youtu.be/{ID}"
    msg = {"message_id": 1, "chat": {"id": "12345", "type": "private"}, "text": text}
    assert service._meeting_by_message(db, msg, "12345", text)
    from app.modules.agent_hub.model import AgentMeeting

    row = db.get(AgentMeeting, dispatched[0])
    assert row.source_kind == mt.SourceKind.YOUTUBE and row.template == "tom_tat_video"


def test_video_chia_doan_10_phut_va_moi_doan_co_moc_dau(db, env, monkeypatch):
    """ai-CR-168 — Gemini trả cả video thành một dòng với mốc [00:00] duy nhất; chia 10 phút một đoạn để chương có mốc thật."""
    monkeypatch.setattr(mt, "youtube_tokens", lambda key, url, model: int(1500 * mt.YT_TOKENS_PER_SEC))   # 25 phút
    calls: list[dict] = []
    monkeypatch.setattr(mt, "gemini_transcribe", lambda *a, **k: calls.append(k["part"]["video_metadata"]) or (
        "Người 1: nói liền một mạch không có mốc", {"model": "g"}))
    row = _row(db, template="tom_tat_video")
    assert mt.process(db, row.id)["status"] == "done"
    db.refresh(row)
    assert len(calls) == 3 and calls[1]["start_offset"] == "600s" and calls[2]["end_offset"] == "1800s"
    assert "[00:00] Người 1" in row.transcript and "[10:00] Người 1" in row.transcript and "[20:00] Người 1" in row.transcript
