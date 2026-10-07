"""Biên bản họp từ ghi âm / video (ai-CR-104, phase 10 bước 10.1 — kế hoạch `doc/agent-hub/11-ke-hoach-bien-ban-hop.md`).

Đại ca chốt 07/10/2026: mọi người đã đăng nhập bot đều dùng (chạy bằng khóa AI của chính họ) · video chỉ lấy TIẾNG ·
biên bản chỉ người gửi xem · việc rút ra thì bot hỏi dự án (bước 10.3).

Đường đi (chạy nền, Celery `agent.meeting_process`):
  1. nhận tệp — Telegram (≤ 20 MB: audio, voice dài, video, document âm thanh/video) hoặc link Google Drive (tệp lớn, mp4)
     tải bằng token Google CÁ NHÂN của người gửi;
  2. `ffmpeg` lấy riêng tiếng, mono 16 kHz mp3 32 kbps (mp4 đọc cả hình thì đắt gấp nhiều lần, họp cần lời nói);
  3. dài hơn SPLIT_OVER_SEC thì cắt đoạn SEGMENT_SEC; mỗi đoạn đẩy lên Gemini File API, chép lời có mốc giờ, xóa tệp;
  4. một lượt model (bộ định tuyến khóa — hãng nào cũng được) viết biên bản theo mẫu;
  5. gửi biên bản vào chat + tệp Word; đẩy Word lên Drive của người gửi (nếu đã nối Google); cất vào kho ghi chú.
Tệp âm thanh chỉ nằm trong thư mục tạm, xóa ngay sau lượt chạy.
"""
from __future__ import annotations

import io
import json
import logging
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from enum import IntEnum
from pathlib import Path

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.provider.base import ChatMessage, ChatResult

from . import personal_memory, telegram, user_keys
from .model import AgentMeeting

log = logging.getLogger("app.agent_hub.meetings")

GEM_BASE = "https://generativelanguage.googleapis.com"
DRIVE_URL = "https://www.googleapis.com/drive/v3"
TELEGRAM_MAX_BYTES = 20 * 1024 * 1024          # trần tải tệp của Bot API
DRIVE_MAX_BYTES = 1536 * 1024 * 1024           # 1,5 GB — họp vài giờ quay video vẫn lọt
SEGMENT_SEC = 1800                             # 30 phút / đoạn chép
SPLIT_OVER_SEC = 2400                          # dài hơn 40 phút thì cắt (đầu ra một lượt có trần)
MAX_DURATION_SEC = 6 * 3600
TRANSCRIBE_MAX_TOKENS = 30000
ACTIVE_WAIT_SEC = 300
FFMPEG_TIMEOUT = 1800
LONG_VOICE_SEC = 180                           # tin thoại dài hơn 3 phút coi là ghi âm họp
RECAP_MAX_CHARS = 120_000                      # bản chép đưa vào lượt viết biên bản

_DRIVE_ID = re.compile(r"https?://(?:drive|docs)\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=)([\w-]{20,})")
_MEETING_WORDS = re.compile(r"(họp|biên bản|ghi âm|recap|tóm tắt|cuộc gọi|meeting)", re.IGNORECASE)


class MeetingStatus(IntEnum):
    QUEUED = 1
    TRANSCRIBING = 2
    WRITING = 3
    DONE = 4
    FAILED = 5


class SourceKind(IntEnum):
    TELEGRAM = 1
    DRIVE = 2


class MeetingError(RuntimeError):
    """Lỗi nói được cho người dùng (một câu tiếng Việt, không có URL / khóa)."""


#  Bốn mẫu biên bản là DỮ LIỆU (QĐ-M6 cũ): khóa · nhãn · lời dặn. Bước 10.2 cho sửa / thêm mẫu không cần sửa mã.
TEMPLATES: dict[str, tuple[str, str]] = {
    "gach_dau_dong": ("Tóm tắt nhanh", "Viết 5–12 gạch đầu dòng: mục đích cuộc họp, các ý chính, quyết định đã chốt, rồi mục "
                                       "«Việc cần làm» (mỗi dòng: việc — người làm — hạn, thiếu thì ghi «chưa rõ»)."),
    "chinh_thuc": ("Biên bản chính thức", "Viết biên bản họp chính thức: Thời gian, Thành phần (tên nghe được), Nội dung từng "
                                          "vấn đề đã bàn, Kết luận / quyết định, Việc cần làm (việc — người làm — hạn)."),
    "danh_sach_viec": ("Danh sách việc", "Chỉ liệt kê việc cần làm rút ra từ cuộc họp: mỗi dòng «việc — người làm — hạn», "
                                        "nhóm theo người làm; cuối cùng là các câu hỏi còn bỏ ngỏ."),
    "theo_gio": ("Đầy đủ theo giờ", "Viết diễn biến theo mốc giờ [mm:ss]: ai nói gì (tóm ý từng đoạn), kết thúc bằng Kết luận "
                                    "và Việc cần làm."),
}
DEFAULT_TEMPLATE = "gach_dau_dong"

TRANSCRIBE_PROMPT = (
    "Chép lại NGUYÊN VĂN lời nói tiếng Việt trong đoạn ghi âm cuộc họp này. Mỗi lượt nói một dòng dạng "
    "«[mm:ss] Người nói: lời nói». Phân biệt người nói bằng tên nếu nghe được, không thì «Người 1», «Người 2»… giữ "
    "nhất quán. Bỏ tiếng ậm ừ, không tóm tắt, không thêm lời bình. Đoạn không nghe rõ ghi «[không rõ]»."
)
RECAP_SYSTEM = (
    "Bạn là thư ký cuộc họp. Từ bản chép lời bên dưới, viết biên bản tiếng Việt có dấu theo yêu cầu. Chỉ dùng thông tin có "
    "trong bản chép, không bịa tên, số, hạn. Dùng Markdown đơn giản (tiêu đề ngắn, gạch đầu dòng)."
)


# ---------------------------------------------------------------------------
# Nhận diện yêu cầu
# ---------------------------------------------------------------------------
def drive_file_id(text: str) -> str:
    m = _DRIVE_ID.search(text or "")
    return m.group(1) if m else ""


def wants_meeting(text: str) -> bool:
    """Tin có link Drive + chữ nói về họp / biên bản / ghi âm."""
    return bool(drive_file_id(text)) and bool(_MEETING_WORDS.search(text or ""))


def template_of(text: str) -> str:
    t = (text or "").lower()
    if "chính thức" in t:
        return "chinh_thuc"
    if "danh sách việc" in t or "việc cần làm" in t:
        return "danh_sach_viec"
    if "theo giờ" in t or "đầy đủ" in t:
        return "theo_gio"
    return DEFAULT_TEMPLATE


def telegram_media(msg: dict) -> dict | None:
    """Tệp họp gửi qua Telegram: audio, video, document âm thanh / video, hoặc tin thoại dài. None nếu không phải."""
    for key in ("audio", "video", "video_note", "document"):
        m = msg.get(key) or {}
        mime = str(m.get("mime_type") or ("video/mp4" if key in ("video", "video_note") else ""))
        if m.get("file_id") and (key in ("audio", "video", "video_note") or mime.startswith(("audio/", "video/"))):
            return {"file_id": str(m["file_id"]), "mime": mime or "audio/mpeg", "size": int(m.get("file_size") or 0),
                    "name": str(m.get("file_name") or m.get("title") or key), "duration": int(m.get("duration") or 0)}
    v = msg.get("voice") or {}
    if v.get("file_id") and int(v.get("duration") or 0) > LONG_VOICE_SEC:
        return {"file_id": str(v["file_id"]), "mime": str(v.get("mime_type") or "audio/ogg"),
                "size": int(v.get("file_size") or 0), "name": "ghi âm", "duration": int(v.get("duration") or 0)}
    return None


# ---------------------------------------------------------------------------
# Tạo phiên + giao chạy nền
# ---------------------------------------------------------------------------
def create(db: Session, *, user_id: int, chat_id: str, kind: SourceKind, ref: str, title: str, mime: str = "",
           template: str = DEFAULT_TEMPLATE) -> AgentMeeting:
    row = AgentMeeting(user_id=int(user_id), chat_id=str(chat_id), source_kind=int(kind), source_ref=ref[:300],
                       title=(title or "Cuộc họp")[:200], mime=(mime or "")[:80], status=int(MeetingStatus.QUEUED),
                       template=template if template in TEMPLATES else DEFAULT_TEMPLATE,
                       created_by=int(user_id), updated_by=int(user_id))
    db.add(row)
    db.flush()
    return row


def dispatch(meeting_id: int) -> None:
    from .tasks import meeting_process_task  # import muộn: tasks import service

    meeting_process_task.apply_async(args=[int(meeting_id)])


# ---------------------------------------------------------------------------
# Tải tệp
# ---------------------------------------------------------------------------
def _download_drive(db: Session, user_id: int, file_id: str, dest: Path) -> tuple[str, str]:
    """Tải tệp Drive của chính người gửi về `dest` theo luồng. Trả (tên, mime)."""
    from . import google_link

    link = google_link.get_link(db, user_id)
    if link is None:
        raise MeetingError("Tệp trên Drive cần đại ca nối Google trước: ERP → Trang cá nhân → Khóa AI → «Nối Google».")
    meta = google_link.api_get(db, link, f"{DRIVE_URL}/files/{file_id}",
                               {"fields": "name,mimeType,size", "supportsAllDrives": "true"})
    mime = str(meta.get("mimeType") or "")
    if not mime.startswith(("audio/", "video/")):
        raise MeetingError(f"Tệp «{meta.get('name') or file_id}» không phải ghi âm / video ({mime or 'không rõ loại'}).")
    if int(meta.get("size") or 0) > DRIVE_MAX_BYTES:
        raise MeetingError("Tệp lớn hơn 1,5 GB — cắt nhỏ hoặc xuất lại chỉ phần tiếng giúp em.")
    token = google_link.access_token(db, link)
    try:
        with requests.get(f"{DRIVE_URL}/files/{file_id}", params={"alt": "media", "supportsAllDrives": "true"},
                          headers={"Authorization": f"Bearer {token}"}, stream=True, timeout=60) as resp:
            if resp.status_code >= 400:
                raise MeetingError(f"Google Drive trả lỗi {resp.status_code} khi tải tệp.")
            total = 0
            with open(dest, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    total += len(chunk)
                    if total > DRIVE_MAX_BYTES:
                        raise MeetingError("Tệp lớn hơn 1,5 GB.")
                    fh.write(chunk)
    except requests.RequestException as e:
        raise MeetingError(f"Không tải được tệp từ Drive ({type(e).__name__}).") from None
    return str(meta.get("name") or "cuộc họp"), mime


def _download_telegram(file_id: str, dest: Path) -> None:
    try:
        data, _remote = telegram.download_file(file_id, max_bytes=TELEGRAM_MAX_BYTES)
    except telegram.TelegramError as e:
        raise MeetingError(f"Không tải được tệp từ Telegram ({e}). Tệp trên 20 MB thì đưa lên Google Drive rồi gửi "
                           "link cho em.") from None
    dest.write_bytes(data)


# ---------------------------------------------------------------------------
# ffmpeg
# ---------------------------------------------------------------------------
def _run(cmd: list[str], timeout: int = FFMPEG_TIMEOUT) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise MeetingError("Máy chủ chưa cài ffmpeg (cần dựng lại image api).") from None
    except subprocess.TimeoutExpired:
        raise MeetingError("Xử lý âm thanh quá lâu, em đã dừng.") from None
    if proc.returncode != 0:
        raise MeetingError(f"Không đọc được tệp âm thanh / video ({(proc.stderr or '').strip()[-160:]}).")
    return proc.stdout


def probe_duration(path: Path) -> float:
    out = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], timeout=120)
    try:
        return float(out.strip().splitlines()[0])
    except (ValueError, IndexError):
        return 0.0


def to_audio(src: Path, dest: Path) -> None:
    """Chỉ lấy tiếng: mono 16 kHz, mp3 32 kbps (≈ 14 MB / giờ)."""
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
          "-c:a", "libmp3lame", "-b:a", "32k", str(dest)])


def split_audio(path: Path, workdir: Path, duration: float) -> list[Path]:
    if duration <= SPLIT_OVER_SEC:
        return [path]
    pattern = workdir / "seg_%03d.mp3"
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-f", "segment",
          "-segment_time", str(SEGMENT_SEC), "-c", "copy", str(pattern)])
    return sorted(workdir.glob("seg_*.mp3"))


# ---------------------------------------------------------------------------
# Gemini File API
# ---------------------------------------------------------------------------
def _gem_error(resp) -> MeetingError:
    from . import ai_keys

    text = f"Gemini trả lỗi {resp.status_code}: {resp.text[:300]}"
    return MeetingError(ai_keys.key_problem(text, "gemini") or ai_keys.short_error(text))


def gemini_upload(key: str, path: Path, mime: str, display: str) -> dict:
    size = path.stat().st_size
    start = requests.post(f"{GEM_BASE}/upload/v1beta/files", headers={
        "x-goog-api-key": key, "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(size), "X-Goog-Upload-Header-Content-Type": mime,
        "content-type": "application/json"}, json={"file": {"display_name": display[:100]}}, timeout=60)
    if start.status_code >= 400:
        raise _gem_error(start)
    url = start.headers.get("X-Goog-Upload-URL") or start.headers.get("x-goog-upload-url")
    if not url:
        raise MeetingError("Gemini không trả đường tải lên.")
    with open(path, "rb") as fh:
        done = requests.post(url, headers={"X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize",
                                           "Content-Length": str(size)}, data=fh, timeout=600)
    if done.status_code >= 400:
        raise _gem_error(done)
    return (done.json() or {}).get("file") or {}


def gemini_wait_active(key: str, name: str, *, timeout: int = ACTIVE_WAIT_SEC) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        resp = requests.get(f"{GEM_BASE}/v1beta/{name}", headers={"x-goog-api-key": key}, timeout=30)
        if resp.status_code >= 400:
            raise _gem_error(resp)
        info = resp.json() or {}
        state = str(info.get("state") or "")
        if state == "ACTIVE":
            return info
        if state == "FAILED":
            raise MeetingError("Gemini không xử lý được tệp âm thanh này.")
        if time.monotonic() > deadline:
            raise MeetingError("Gemini xử lý tệp quá lâu, em đã dừng.")
        time.sleep(3)


def gemini_delete(key: str, name: str) -> None:
    try:
        requests.delete(f"{GEM_BASE}/v1beta/{name}", headers={"x-goog-api-key": key}, timeout=30)
    except requests.RequestException:
        pass        # tệp tự hết hạn sau 48 giờ phía Gemini


def gemini_transcribe(key: str, file_uri: str, mime: str, model: str) -> tuple[str, dict]:
    payload = {
        "contents": [{"role": "user", "parts": [{"file_data": {"mime_type": mime, "file_uri": file_uri}},
                                                {"text": TRANSCRIBE_PROMPT}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": TRANSCRIBE_MAX_TOKENS},
    }
    if not model.startswith("gemini-3"):
        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    resp = None
    for attempt in range(2):
        resp = requests.post(f"{GEM_BASE}/v1beta/models/{model}:generateContent", headers={"x-goog-api-key": key},
                             json=payload, timeout=900)
        if resp.status_code in (500, 503, 504) and attempt == 0:
            time.sleep(3)
            continue
        break
    if resp is None or resp.status_code >= 400:
        raise _gem_error(resp)
    data = resp.json() or {}
    cands = data.get("candidates") or []
    parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
    return "".join(p.get("text", "") for p in parts).strip(), data.get("usageMetadata") or {}


def _shift_stamps(text: str, offset_sec: int) -> str:
    """[mm:ss] của đoạn thứ n cộng thêm mốc đầu đoạn để bản chép nối liền theo giờ cuộc họp."""
    if not offset_sec:
        return text

    def fix(m: re.Match) -> str:
        total = int(m.group(1)) * 60 + int(m.group(2)) + offset_sec
        return f"[{total // 3600:d}:{total % 3600 // 60:02d}:{total % 60:02d}]" if total >= 3600 else \
            f"[{total // 60:02d}:{total % 60:02d}]"

    return re.sub(r"\[(\d{1,3}):(\d{2})\]", fix, text)


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------
def build_docx(title: str, when: datetime | None, recap: str, transcript: str) -> bytes:
    from docx import Document

    doc = Document()
    doc.add_heading(f"Biên bản: {title[:150]}", level=1)
    if when:
        doc.add_paragraph(f"Thời gian xử lý: {when:%d/%m/%Y %H:%M}")
    for line in (recap or "").splitlines():
        clean = re.sub(r"[*_`#]+", "", line).strip()
        if not clean:
            continue
        if line.lstrip().startswith("#"):
            doc.add_heading(clean, level=2)
        elif clean.startswith(("- ", "• ")):
            doc.add_paragraph(clean[2:].strip(), style="List Bullet")
        else:
            doc.add_paragraph(clean)
    if transcript:
        doc.add_page_break()
        doc.add_heading("Phụ lục: bản chép lời", level=2)
        for line in transcript.splitlines()[:5000]:
            if line.strip():
                doc.add_paragraph(line.strip())
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Chạy một phiên
# ---------------------------------------------------------------------------
def process(db: Session, meeting_id: int) -> dict:
    """Chạy trọn một phiên. Mọi lỗi thành một câu nhắn cho người gửi; phiên ghi FAILED."""
    from . import service

    row = db.get(AgentMeeting, int(meeting_id))
    if row is None or row.status not in (int(MeetingStatus.QUEUED), int(MeetingStatus.FAILED)):
        return {"status": "skipped"}
    row.started_at = datetime.now()
    workdir = Path(tempfile.mkdtemp(prefix="meet_"))
    try:
        with user_keys.for_chat(db, row.chat_id):
            out = _process(db, row, workdir)
        return out
    except MeetingError as e:
        row.status = int(MeetingStatus.FAILED)
        row.error = str(e)[:500]
        db.commit()
        service.reply(db, row.chat_id, f"Em chưa làm được biên bản «{telegram.esc(row.title)}»: {telegram.esc(str(e))}")
        db.commit()
        return {"status": "error", "reason": str(e)[:300]}
    except Exception as e:  # noqa: BLE001 — lỗi lạ cũng phải thành một câu
        log.exception("agent_hub: biên bản họp hỏng")
        row.status = int(MeetingStatus.FAILED)
        row.error = str(e)[:500]
        db.commit()
        service.reply(db, row.chat_id, f"Em chưa làm được biên bản «{telegram.esc(row.title)}» (lỗi hệ thống). Đại ca "
                                       "gửi lại giúp em; lặp lại thì báo em xem sổ.")
        db.commit()
        return {"status": "error", "reason": str(e)[:300]}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _process(db: Session, row: AgentMeeting, workdir: Path) -> dict:
    from . import ai_keys, manager, service
    from .constants import STAGE_MEETING

    key = user_keys.gemini_key()
    if not key:
        raise MeetingError("Chép lời họp chỉ chạy bằng Gemini — thêm một khóa Gemini ở ERP → Trang cá nhân → Khóa AI.")
    row.status = int(MeetingStatus.TRANSCRIBING)
    db.commit()
    src = workdir / "source.bin"
    if row.source_kind == int(SourceKind.DRIVE):
        name, mime = _download_drive(db, row.user_id, row.source_ref, src)
        if row.title in ("", "Cuộc họp"):
            row.title = Path(name).stem[:200] or row.title
        row.mime = mime[:80]
    else:
        _download_telegram(row.source_ref, src)
    audio = workdir / "audio.mp3"
    to_audio(src, audio)
    src.unlink(missing_ok=True)
    duration = probe_duration(audio)
    row.duration_sec = int(duration)
    if duration > MAX_DURATION_SEC:
        raise MeetingError("Ghi âm dài hơn 6 giờ — cắt bớt giúp em.")
    db.commit()

    run = service.start_run(db, 0, STAGE_MEETING)
    db.commit()
    model = settings.AGENT_MANAGER_MODEL
    pieces: list[str] = []
    usage_in = usage_out = 0
    segments = split_audio(audio, workdir, duration)
    try:
        for i, seg in enumerate(segments):
            info = gemini_upload(key, seg, "audio/mp3", f"{row.title} {i + 1}/{len(segments)}")
            name = str(info.get("name") or "")
            try:
                info = gemini_wait_active(key, name) if info.get("state") != "ACTIVE" else info
                text, usage = gemini_transcribe(key, str(info.get("uri") or ""), "audio/mp3", model)
            finally:
                if name:
                    gemini_delete(key, name)
            usage_in += int(usage.get("promptTokenCount") or 0)
            usage_out += int(usage.get("candidatesTokenCount") or 0)
            pieces.append(_shift_stamps(text, i * SEGMENT_SEC if len(segments) > 1 else 0))
    except MeetingError as e:
        service.finish_run(db, run, error=str(e))
        db.commit()
        raise
    service.finish_run(db, run, result=ChatResult(text="", provider="gemini", model=model, input_tokens=usage_in,
                                                  output_tokens=usage_out))
    transcript = "\n".join(p for p in pieces if p).strip()
    if not transcript:
        raise MeetingError("Em không nghe ra lời nói nào trong tệp.")
    row.transcript = transcript
    row.status = int(MeetingStatus.WRITING)
    db.commit()

    label, instruction = TEMPLATES.get(row.template, TEMPLATES[DEFAULT_TEMPLATE])
    try:
        result = manager.get_provider().ask(
            [ChatMessage(role="user", content=f"YÊU CẦU: {instruction}\n\nBẢN CHÉP LỜI:\n{transcript[:RECAP_MAX_CHARS]}")],
            system=RECAP_SYSTEM, max_tokens=4000, temperature=0.2)
    except Exception as e:  # noqa: BLE001
        raise MeetingError(ai_keys.short_error(str(e))) from None
    recap = (result.text or "").strip()
    if not recap:
        raise MeetingError("Model không viết được biên bản, đại ca thử lại giúp em.")
    row.recap = recap
    note = personal_memory.add_note(db, row.user_id, f"Họp: {row.title}"[:200], f"{label}\n\n{recap}")
    row.note_id = int(note.get("note_id") or 0)
    row.status = int(MeetingStatus.DONE)
    row.finished_at = datetime.now()
    db.commit()

    minutes = int(duration // 60)
    service.reply(db, row.chat_id, f"**BIÊN BẢN — {row.title}** ({minutes} phút, {label.lower()})\n\n{recap}",
                  markdown=True)
    data = build_docx(row.title, row.finished_at, recap, transcript)
    filename = re.sub(r"[^\w\- ]+", "", f"bien-ban {row.title}")[:80].strip() + ".docx"
    telegram.send_document(row.chat_id, filename, data, caption="Biên bản kèm phụ lục bản chép lời")
    drive_link = _upload_word(db, row, filename, data)
    if drive_link:
        service.reply(db, row.chat_id, f"Đã lưu lên Drive của đại ca: {telegram.esc(drive_link)}")
    db.commit()
    return {"status": "done", "meeting_id": row.id, "minutes": minutes, "segments": len(segments)}


def _upload_word(db: Session, row: AgentMeeting, filename: str, data: bytes) -> str:
    from . import google_link

    link = google_link.get_link(db, row.user_id)
    if link is None:
        return ""
    try:
        info = google_link.upload_file(db, link, filename, data,
                                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:  # noqa: BLE001 — Drive hỏng thì thôi, Word đã gửi trong chat
        log.warning("agent_hub: đẩy biên bản lên Drive hỏng: %s", e)
        return ""
    row.drive_file_id = str(info.get("id") or "")[:120]
    return str(info.get("webViewLink") or "")


def describe(row: AgentMeeting) -> dict:
    return {"id": row.id, "title": row.title, "status": MeetingStatus(row.status).name.lower(),
            "minutes": int((row.duration_sec or 0) // 60), "template": row.template, "error": row.error or None,
            "info": json.dumps({"note_id": row.note_id}) if row.note_id else None}
