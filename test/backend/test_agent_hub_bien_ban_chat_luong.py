"""ai-CR-164 — đại ca 10/10 xem biên bản họp 102 phút: lọt câu tiếng Anh của model vào Word; Người 1…4 chưa ra tên; họp dài
mà sơ sài; phụ lục bản chép lời làm Word nặng; tin chat bị cắt mà nói «xem trong sổ»."""
from app.modules.agent_hub import meetings as mt

PREAMBLE = ("Below is a Vietnamese meeting recap in Markdown, following the requested DEGO structure and only using "
            "information from the transcript.")


def test_bo_chu_cua_model_lot_vao_bien_ban():
    raw = f"{PREAMBLE}\n\n```markdown\n## TÓM TẮT NHANH\n- Chốt mua **20 tấn** thép\n```\nLet me know if you need more."
    out = mt.clean_recap(raw)
    assert out == "## TÓM TẮT NHANH\n- Chốt mua **20 tấn** thép"
    assert mt.clean_recap("Dưới đây là biên bản cuộc họp:\n## A\n- x") == "## A\n- x"
    assert mt.clean_recap("## A\n- Dưới đây là số liệu quý 3") == "## A\n- Dưới đây là số liệu quý 3"


def _transcript(minutes: int) -> str:
    lines = []
    for m in range(0, minutes, 2):
        who = 1 + (m // 2) % 3
        lines.append(f"[{m // 60}:{m % 60:02d}:00] Người {who}: anh Phú chốt giá thép {m} triệu, chị Ngân làm báo cáo"
                     if m >= 60 else f"[{m:02d}:00] Người {who}: anh Phú chốt giá thép {m} triệu, chị Ngân làm báo cáo")
    return "\n".join(lines)


def test_cat_doan_theo_moc_gio():
    chunks = mt.transcript_chunks(_transcript(100))
    assert len(chunks) == 5 and chunks[0][0] == "00:00–20:00" and "1:20:00" in chunks[-1][0]
    assert all(text for _label, text in chunks)


def _row(db, **kw):
    from app.modules.agent_hub.model import AgentMeeting

    row = AgentMeeting(user_id=7, chat_id="12345", source_kind=1, source_ref="F1", title="giao ban giá", mime="audio/mp4",
                       status=int(mt.MeetingStatus.QUEUED), created_by=0, updated_by=0, **kw)
    db.add(row)
    db.commit()
    return row


def test_hop_dai_tom_hai_tang_word_khong_phu_luc_gui_txt_va_hoi_ai_la_ai(db, monkeypatch):
    from app.modules.agent_hub import meeting_actions, service
    from app.modules.assistant.provider.base import ChatResult

    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    docs: list[tuple[str, bytes]] = []
    monkeypatch.setattr(mt.telegram, "send_document", lambda chat, fn, data, **kw: docs.append((fn, data)) or 1)
    monkeypatch.setattr(mt, "_upload_word", lambda *a, **k: "")
    monkeypatch.setattr(meeting_actions, "offer", lambda db, row: 0)
    monkeypatch.setattr(mt.personal_memory, "add_note", lambda *a, **k: {"note_id": 1})
    asked: list[tuple[str, str]] = []

    class P:
        def ask(self, messages, *, system=None, model=None, **kw):
            asked.append((system, messages[0].content))
            if system == mt.CHUNK_SYSTEM:
                return ChatResult(text="- Chủ đề giá thép: chốt **40 triệu**", provider="x", model="m")
            return ChatResult(text=f"{PREAMBLE}\n## TÓM TẮT NHANH\n- Giá thép chốt **40 triệu**\n" + "- ý\n" * 2000,
                              provider="x", model="m")

    monkeypatch.setattr(mt, "_ask_logged", lambda db, row, system, content, **kw: P().ask(
        [type("M", (), {"content": content})()], system=system).text)
    row = _row(db, transcript=_transcript(100), duration_sec=6000)
    out = mt.process(db, row.id)
    db.refresh(row)
    assert out["status"] == "done"
    chunk_calls = [a for a in asked if a[0] == mt.CHUNK_SYSTEM]
    assert len(chunk_calls) == 5 and "GHI CHÚ CHI TIẾT TỪNG ĐOẠN" in asked[-1][1]
    assert not row.recap.startswith("Below") and row.recap.startswith("## TÓM TẮT NHANH")
    names = [fn for fn, _ in docs]
    assert any(fn.endswith(".docx") for fn in names) and "giao ban giá - ban chep loi.txt" in names
    txt = dict(docs)["giao ban giá - ban chep loi.txt"].decode("utf-8")
    assert "[00:00] Người 1" in txt
    word = next(data for fn, data in docs if fn.endswith(".docx"))
    import io
    import zipfile

    xml = zipfile.ZipFile(io.BytesIO(word)).read("word/document.xml").decode("utf-8")
    assert "PHỤ LỤC" not in xml and "Người 1: anh Phú" not in xml
    biên_bản = next(t for t in sent if t.startswith("**BIÊN BẢN"))
    assert "tệp Word đính kèm" in biên_bản and "sổ" not in biên_bản      # ai-CR-165: bản rút gọn + dòng chỉ bản đầy đủ
    card = next(t for t in sent if "AI LÀ AI?" in t)
    assert "Người 1" in card and "Phú" in card and "Ngân" in card


def test_tra_loi_ai_la_ai_thay_ten_roi_viet_lai(db, monkeypatch):
    from app.modules.agent_hub import service
    from app.modules.agent_hub.constants import DIR_IN

    sent: list[str] = []
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    row = _row(db, transcript="[00:05] Người 1: chào\n[00:09] Người 2: em Ngân báo cáo", recap="## A",
               actions=[{"title": "Người 2 làm báo cáo"}], steps=[1, 2, 3, 4, 5, 6, 7, 9])
    row.status = int(mt.MeetingStatus.DONE)
    db.commit()
    monkeypatch.setattr(service, "reply", lambda db, chat_id, text, **kw: sent.append(text))
    mt.offer_speakers(db, row)
    dispatched: list[int] = []
    monkeypatch.setattr(mt, "dispatch", lambda mid: dispatched.append(mid))
    msg = service.log_message(db, DIR_IN, "12345", 3, "Người 1 = Phú, người 2 là Ngân")
    db.commit()
    assert mt.speakers_by_text(db, "12345", msg, "Người 1 = Phú, người 2 là Ngân")
    db.refresh(row)
    assert "[00:05] Phú: chào" in row.transcript and "[00:09] Ngân:" in row.transcript
    assert row.actions == [{"title": "Ngân làm báo cáo"}] and dispatched == [row.id]
    assert row.steps == [1, 2, 7, 9]          # viết + gửi chạy lại; thẻ việc và thẻ Ai là ai không gửi lần hai
    msg = service.log_message(db, DIR_IN, "12345", 4, "Người 1 = Bảo")
    db.commit()
    assert not mt.speakers_by_text(db, "12345", msg, "Người 1 = Bảo")    # thẻ đã trả lời rồi
