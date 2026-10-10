"""ai-CR-162 — dev 10/10: video quay màn hình KHÔNG có lời nói mà bot «chép» ra 12.800 ký tự hội thoại bịa và viết thành
biên bản 45 phút. Chặn bằng mã (ffprobe / silencedetect) trước khi gọi model + rào sau chép lời; báo lỗi nói rõ đã xong gì,
chưa xong gì, vì sao; lỗi tạm ở bước gửi tự thử lại; lỗi lạ có tin vận hành."""
import subprocess
from pathlib import Path

import pytest

from app.modules.agent_hub import meetings as mt


def _ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args], check=True, capture_output=True)


def _raise(exc):
    raise exc


@pytest.fixture
def media(tmp_path):
    silent = tmp_path / "silent.mp3"
    _ffmpeg("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", "-t", "120", "-c:a", "libmp3lame", str(silent))
    no_audio = tmp_path / "noaudio.mp4"
    _ffmpeg("-f", "lavfi", "-i", "color=c=black:s=64x64:d=5", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(no_audio))
    blip = tmp_path / "blip.mp3"         # 5 giây có tiếng trong 120 giây
    _ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=5", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=115",
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1", "-t", "120", "-c:a", "libmp3lame", str(blip))
    talk = tmp_path / "talk.mp3"         # 60 giây có tiếng trong 120 giây
    _ffmpeg("-f", "lavfi", "-i", "sine=f=300:d=60", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=60",
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1", "-t", "120", "-c:a", "libmp3lame", str(talk))
    return {"silent": silent, "no_audio": no_audio, "blip": blip, "talk": talk}


def test_do_luong_tieng_va_phan_co_tieng(media):
    assert mt.audio_streams(media["no_audio"]) == 0 and mt.audio_streams(media["silent"]) == 1
    with pytest.raises(mt.MeetingError, match="gần như không có tiếng"):
        mt.speech_check(media["silent"], 120)
    with pytest.raises(mt.MeetingError, match="gần như không có tiếng"):
        mt.speech_check(media["blip"], 120)
    voiced = mt.speech_check(media["talk"], 120)
    assert 50 <= voiced <= 70


def test_rao_sau_chep_loi():
    assert mt.plausible_transcript("[00:05] A: chào", 120, 60) == ""
    assert "ký tự" in mt.plausible_transcript("x" * 5000, 2749, 30)
    assert "mốc giờ" in mt.plausible_transcript("[50:00] A: bịa", 600, 500)


def _row(db, **kw):
    from app.modules.agent_hub.model import AgentMeeting

    row = AgentMeeting(user_id=7, chat_id="12345", source_kind=1, source_ref="F1", title="giao ban", mime="video/mp4",
                       status=int(mt.MeetingStatus.QUEUED), created_by=0, updated_by=0, **kw)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def env(db, monkeypatch):
    from app.modules.agent_hub import db_backup, service

    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    ops: list[str] = []
    monkeypatch.setattr(db_backup, "alert", lambda db, text: ops.append(text))
    monkeypatch.setattr(mt.user_keys, "gemini_key", lambda: "AIza-k")
    gem: list = []
    monkeypatch.setattr(mt, "gemini_upload",
                        lambda *a, **k: gem.append(a) or {"name": "f", "uri": "u", "state": "ACTIVE"})
    monkeypatch.setattr(mt.time, "sleep", lambda s: None)
    return sent, ops, gem


def test_video_khong_tieng_va_tep_im_lang_khong_ra_bien_ban(db, env, media, monkeypatch):
    sent, ops, gem = env
    for name in ("no_audio", "silent"):
        row = _row(db)
        monkeypatch.setattr(mt, "_download_telegram",
                            lambda ref, dest, src=media[name]: Path(dest).write_bytes(src.read_bytes()))
        out = mt.process(db, row.id)
        db.refresh(row)
        assert out["status"] == "error" and row.status == mt.MeetingStatus.FAILED and not row.recap
        assert "Em không làm biên bản" in sent[-1] and "thử lại" not in sent[-1]
    assert gem == [] and ops == []                     # không gọi Gemini; lỗi đã lường thì không báo vận hành


def test_model_bao_khong_co_loi_noi_thi_khong_viet(db, env, media, monkeypatch):
    sent, ops, gem = env
    row = _row(db)
    monkeypatch.setattr(mt, "_download_telegram", lambda ref, dest: Path(dest).write_bytes(media["talk"].read_bytes()))
    monkeypatch.setattr(mt, "gemini_transcribe", lambda *a, **k: (mt.NO_SPEECH, {"model": "g"}))
    monkeypatch.setattr(mt, "gemini_delete", lambda *a, **k: None)
    out = mt.process(db, row.id)
    db.refresh(row)
    assert out["status"] == "error" and not row.transcript and "không nghe ra lời nói" in sent[-1]


def test_hong_sau_khi_da_gui_bien_ban_thi_noi_dung_su_that_va_tu_thu_lai(db, env, monkeypatch):
    from app.modules.agent_hub import erp, meeting_actions

    sent, ops, gem = env
    row = _row(db, transcript="[00:05] A: chốt mua thép", recap="## Kết luận\n- Mua thép", duration_sec=600,
               steps=[1, 2, 3])
    row.status = int(mt.MeetingStatus.FAILED)
    db.commit()
    docs: list = []
    monkeypatch.setattr(mt.telegram, "send_document", lambda chat, fn, data, **kw: docs.append(fn) or 1)
    monkeypatch.setattr(mt, "_upload_word", lambda db, row, fn, data: "")
    tries = {"n": 0}

    def flaky(db, row):
        tries["n"] += 1
        if tries["n"] < 2:
            raise erp.ErpError("Không gọi được ERP (ConnectionError)")

    monkeypatch.setattr(meeting_actions, "offer", flaky)
    out = mt.process(db, row.id)
    db.refresh(row)
    assert out["status"] == "done" and tries["n"] == 2 and docs and row.steps == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    #  Lỗi tạm mãi không hết → báo đúng: biên bản đã gửi, bước nào chưa xong, lý do dễ hiểu; không báo vận hành.
    row.steps = [1, 2, 3, 4]
    row.status = int(mt.MeetingStatus.FAILED)
    db.commit()
    down = erp.ErpError("Không gọi được ERP (ConnectionError)")
    monkeypatch.setattr(meeting_actions, "offer", lambda db, row: _raise(down))
    monkeypatch.setattr(mt.telegram, "send_document", lambda *a, **k: _raise(down))
    out = mt.process(db, row.id)
    assert out["status"] == "error"
    msg = sent[-1]
    assert "đã gửi ở trên" in msg and "chưa làm được biên bản" not in msg and "Chưa xong: gửi tệp Word" in msg
    assert "hệ thống ERP đang khởi động lại" in msg and "thử lại biên bản" in msg and ops == []


def test_loi_la_co_tin_van_hanh_va_lenh_thu_lai(db, env, monkeypatch):
    from app.modules.agent_hub import chat_link, service
    from app.modules.agent_hub.constants import DIR_IN

    sent, ops, gem = env
    row = _row(db, transcript="[00:05] A: chốt", recap="## Kết luận", duration_sec=60, steps=[1, 2, 3, 4])
    row.status = int(mt.MeetingStatus.FAILED)
    db.commit()
    monkeypatch.setattr(mt, "word_of", lambda db, row: _raise(KeyError("boom")))
    assert mt.process(db, row.id)["status"] == "error"
    assert ops and "Biên bản họp #" in ops[-1] and "SEND_WORD" in ops[-1] and "KeyError" in ops[-1]
    assert "lỗi hệ thống chưa rõ" in sent[-1]
    #  «thử lại biên bản»: làm tiếp từ bước hỏng.
    dispatched: list = []
    monkeypatch.setattr(mt, "dispatch", lambda mid: dispatched.append(mid))
    monkeypatch.setattr(chat_link, "get_active_link", lambda db, chat_id: type("L", (), {"user_id": 7})())
    msg = service.log_message(db, DIR_IN, "12345", 1, "thử lại biên bản")
    db.commit()
    assert mt.retry_by_text(db, "12345", msg, "thử lại biên bản") and dispatched == [row.id]
    assert "làm tiếp các bước gửi" in sent[-1]
    assert not mt.retry_by_text(db, "12345", msg, "biên bản hôm qua thế nào")


def test_ket_noi_erp_bi_tu_choi_thi_thu_lai(monkeypatch):
    import requests

    from app.modules.agent_hub import erp

    assert erp._not_connected(requests.ConnectionError("Failed to establish a new connection: Connection refused"))
    assert not erp._not_connected(requests.ReadTimeout("read timed out"))
