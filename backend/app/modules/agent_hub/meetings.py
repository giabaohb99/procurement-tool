"""Biên bản họp từ ghi âm / video (ai-CR-104 bước 10.1, ai-CR-112 bước 10.2 — kế hoạch `doc/agent-hub/11-ke-hoach-bien-ban-hop.md`).

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

Bước 10.2 (ai-CR-112): mẫu biên bản là DỮ LIỆU — bốn mẫu sẵn + mẫu RIÊNG của từng người (một dòng trong sổ ghi nhớ:
«Mẫu biên bản «tên»: lời dặn») + lời dặn tại chỗ («theo mẫu: …»). Mẫu đã chọn chép vào phiên (`template_label`,
`template_prompt`) để viết lại / tra lại đúng như lúc làm. Viết lại theo mẫu khác KHÔNG chép lời lại (giữ `transcript`).
Word theo mẫu DEGO (đầu trang, bảng thông tin, bảng việc, chỗ ký với mẫu chính thức), đẩy vào thư mục «Biên bản họp»
trên Drive của người gửi.
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
from dataclasses import dataclass
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
#  ai-CR-112: model suy luận (DeepSeek v4 qua trạm) tiêu 3–4 nghìn token cho phần nghĩ trước khi viết — trần 4000 cũ
#  có thể cắt cụt biên bản.
RECAP_MAX_TOKENS = 12000
DRIVE_FOLDER = "Biên bản họp"

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


@dataclass(frozen=True)
class Template:
    """Một mẫu biên bản: khóa · nhãn · lời dặn cho model · chữ khóa để chọn bằng lời."""

    key: str
    label: str
    prompt: str
    words: tuple[str, ...] = ()


#  Bốn mẫu sẵn (QĐ-M6 cũ: mẫu là DỮ LIỆU). Người dùng thêm mẫu riêng bằng lời, không cần sửa mã — xem `personal_templates`.
BUILTIN: dict[str, Template] = {t.key: t for t in (
    Template("gach_dau_dong", "Tóm tắt nhanh",
             "Viết 5–12 gạch đầu dòng: mục đích cuộc họp, các ý chính, quyết định đã chốt, rồi mục «Việc cần làm» (mỗi "
             "dòng: việc — người làm — hạn, thiếu thì ghi «chưa rõ»).",
             ("tóm tắt nhanh", "gạch đầu dòng", "ngắn gọn")),
    Template("chinh_thuc", "Biên bản chính thức",
             "Viết biên bản họp chính thức: Thời gian, Thành phần (tên nghe được), Nội dung từng vấn đề đã bàn, Kết luận / "
             "quyết định, Việc cần làm dạng bảng | Việc | Người làm | Hạn |. Không tự đặt tiêu đề lớn (đầu trang đã có).",
             ("chính thức", "hành chính", "trình ký")),
    Template("danh_sach_viec", "Danh sách việc",
             "Chỉ liệt kê việc cần làm rút ra từ cuộc họp: mỗi dòng «việc — người làm — hạn», nhóm theo người làm; cuối cùng "
             "là các câu hỏi còn bỏ ngỏ.",
             ("danh sách việc", "việc cần làm", "giao việc")),
    Template("theo_gio", "Đầy đủ theo giờ",
             "Viết diễn biến theo mốc giờ [mm:ss]: ai nói gì (tóm ý từng đoạn), kết thúc bằng Kết luận và Việc cần làm.",
             ("theo giờ", "đầy đủ", "diễn biến")),
)}
#  Giữ dạng cũ (khóa → (nhãn, lời dặn)) cho chỗ gọi cũ.
TEMPLATES: dict[str, tuple[str, str]] = {k: (t.label, t.prompt) for k, t in BUILTIN.items()}
DEFAULT_TEMPLATE = "gach_dau_dong"
CUSTOM_KEY = "rieng"
#  Dòng mẫu riêng trong sổ ghi nhớ: «Mẫu biên bản «Giao ban»: lời dặn…».
PERSONAL_PREFIX = "Mẫu biên bản"
_PERSONAL_RE = re.compile(r"^\s*Mẫu biên bản\s*«([^»]{1,40})»\s*:\s*(.+)$", re.IGNORECASE)
#  Lời dặn tại chỗ trong chú thích tệp: «theo mẫu: …» / «yêu cầu: …».
_ADHOC_RE = re.compile(r"(?:theo\s+)?(?:mẫu|yêu cầu|cách viết)\s*:\s*(.{8,})", re.IGNORECASE | re.S)
TEMPLATE_PROMPT_MAX = 1500

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
    """Khóa mẫu SẴN khớp chữ trong câu (không xét mẫu riêng); không khớp = mẫu mặc định."""
    t = (text or "").lower()
    for tpl in BUILTIN.values():
        if any(w in t for w in tpl.words):
            return tpl.key
    return DEFAULT_TEMPLATE


def personal_templates(db: Session, user_id: int) -> list[Template]:
    """Mẫu riêng của một người = các dòng «Mẫu biên bản «tên»: …» trong sổ ghi nhớ của họ."""
    if int(user_id or 0) <= 0:
        return []
    out = []
    for line in personal_memory.load_core(db, int(user_id)).splitlines():
        m = _PERSONAL_RE.match(line.lstrip("-• ").strip())
        if m:
            name = m.group(1).strip()
            prompt = re.sub(r"\s*\(đến \d{2}/\d{2}/\d{4}\)\s*$", "", m.group(2))
            out.append(Template(CUSTOM_KEY, name, prompt.strip(), (name.lower(),)))
    return out


def save_personal_template(db: Session, user_id: int, name: str, prompt: str) -> dict:
    """Lưu / thay mẫu riêng «name» vào sổ ghi nhớ (mục cách làm việc)."""
    name = " ".join((name or "").split()).strip(" «»\"'")[:40]
    prompt = " ".join((prompt or "").split()).strip()
    if not name or len(prompt) < 8:
        return {"ok": False, "message": "cần tên mẫu và lời dặn (ít nhất vài chữ)"}
    if name.lower() in {t.label.lower() for t in BUILTIN.values()}:
        return {"ok": False, "message": f"«{name}» trùng tên mẫu sẵn, đặt tên khác giúp em"}
    personal_memory.forget(db, int(user_id), f"{PERSONAL_PREFIX} «{name}»")
    res = personal_memory.remember(db, int(user_id), f"{PERSONAL_PREFIX} «{name}»: {prompt}", section="cach_lam_viec")
    return {**res, "template": name}


def list_templates(db: Session, user_id: int) -> list[dict]:
    return ([{"name": t.label, "kind": "sẵn", "say": t.words[0]} for t in BUILTIN.values()]
            + [{"name": t.label, "kind": "riêng", "say": f"mẫu {t.label}"} for t in personal_templates(db, user_id)])


def resolve_template(db: Session | None, user_id: int, text: str, *, allow_adhoc: bool = True) -> Template:
    """Chọn mẫu từ câu của người dùng: lời dặn tại chỗ («theo mẫu: …») → mẫu riêng nhắc tên → mẫu sẵn → mặc định."""
    raw = text or ""
    if allow_adhoc:
        m = _ADHOC_RE.search(raw)
        if m:
            return Template(CUSTOM_KEY, "Theo yêu cầu riêng", m.group(1).strip()[:TEMPLATE_PROMPT_MAX])
    low = raw.lower()
    if db is not None:
        for tpl in sorted(personal_templates(db, user_id), key=lambda t: -len(t.label)):
            if tpl.label.lower() in low:
                return tpl
    return BUILTIN[template_of(raw)]


def template_for_row(row: AgentMeeting) -> Template:
    if row.template_prompt:
        return Template(row.template or CUSTOM_KEY, row.template_label or "Theo yêu cầu riêng", row.template_prompt)
    return BUILTIN.get(row.template or "", BUILTIN[DEFAULT_TEMPLATE])


def apply_template(row: AgentMeeting, tpl: Template) -> None:
    row.template = tpl.key[:40]
    row.template_label = tpl.label[:80]
    #  Mẫu sẵn không chép lời dặn: sửa mẫu sẵn trong mã thì phiên cũ viết lại cũng theo bản mới.
    row.template_prompt = "" if tpl.key in BUILTIN and BUILTIN[tpl.key] == tpl else tpl.prompt[:TEMPLATE_PROMPT_MAX]


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
           template: str | Template = DEFAULT_TEMPLATE) -> AgentMeeting:
    row = AgentMeeting(user_id=int(user_id), chat_id=str(chat_id), source_kind=int(kind), source_ref=ref[:300],
                       title=(title or "Cuộc họp")[:200], mime=(mime or "")[:80], status=int(MeetingStatus.QUEUED),
                       created_by=int(user_id), updated_by=int(user_id))
    apply_template(row, template if isinstance(template, Template) else BUILTIN.get(template, BUILTIN[DEFAULT_TEMPLATE]))
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
        raise MeetingError("Tệp trên Drive cần nối Google trước: ERP → Trang cá nhân → Khóa AI → «Nối Google».")
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


def transcribe_timeout(audio_sec: float) -> int:
    """Trần chờ MỘT lượt chép lời (ai-CR-112): 2 phút + 1/3 độ dài đoạn. Chạy thử trên dev 07/10 một tệp 88 giây treo 12
    phút vì model chính quá tải mà trần cũ là 15 phút cố định — người gửi tưởng bot chết."""
    return int(120 + max(0.0, audio_sec) / 3)


def gemini_transcribe(key: str, file_uri: str, mime: str, model: str, *, audio_sec: float = 0,
                      fallback: str = "") -> tuple[str, dict]:
    """Chép lời một đoạn. Model chính quá tải (5xx) hoặc treo quá `transcribe_timeout` thì thử MỘT lần bằng model dự phòng
    (cùng khóa). `usage["model"]` = model đã chép được."""
    payload = {
        "contents": [{"role": "user", "parts": [{"file_data": {"mime_type": mime, "file_uri": file_uri}},
                                                {"text": TRANSCRIBE_PROMPT}]}],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": TRANSCRIBE_MAX_TOKENS},
    }
    timeout = transcribe_timeout(audio_sec)
    models = [model] + ([fallback] if fallback and fallback != model else [model])
    resp = None
    for i, m in enumerate(models):
        body = json.loads(json.dumps(payload))
        if not m.startswith("gemini-3"):
            body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
        try:
            resp = requests.post(f"{GEM_BASE}/v1beta/models/{m}:generateContent", headers={"x-goog-api-key": key},
                                 json=body, timeout=timeout)
        except requests.Timeout:
            log.warning("agent_hub: chép lời bằng %s quá %ss", m, timeout)
            resp = None
            if i + 1 < len(models):
                continue
            raise MeetingError(f"Gemini chép lời quá lâu (quá {timeout // 60} phút), có thể đang quá tải — gửi lại sau "
                               "ít phút giúp em.") from None
        except requests.RequestException as e:
            raise MeetingError(f"Không gọi được Gemini ({type(e).__name__}).") from None
        if resp.status_code in (429, 500, 503, 504) and i + 1 < len(models):
            time.sleep(2)
            continue
        break
    if resp is None or resp.status_code >= 400:
        raise _gem_error(resp)
    data = resp.json() or {}
    cands = data.get("candidates") or []
    parts = ((cands[0].get("content") or {}).get("parts") or []) if cands else []
    usage = dict(data.get("usageMetadata") or {})
    usage["model"] = m
    return "".join(p.get("text", "") for p in parts).strip(), usage


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
_MD_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_MD_BOLD = re.compile(r"\*\*(.+?)\*\*")
WORD_FONT = "Times New Roman"
COMPANY_NAME = "DEGO HOLDING"


def _runs(par, text: str, *, size: float | None = None, bold: bool = False, italic: bool = False) -> None:
    """Thêm chữ vào đoạn, **đậm** thành chữ đậm; bỏ các dấu Markdown khác."""
    from docx.shared import Pt

    text = re.sub(r"(?<!\*)\*(?!\*)|`|^#+\s*", "", text)
    pos = 0
    for m in list(_MD_BOLD.finditer(text)) + [None]:
        chunk = text[pos:m.start()] if m else text[pos:]
        if chunk:
            r = par.add_run(chunk)
            r.bold, r.italic = bold or None, italic or None
            if size:
                r.font.size = Pt(size)
        if m:
            r = par.add_run(m.group(1))
            r.bold, r.italic = True, italic or None
            if size:
                r.font.size = Pt(size)
            pos = m.end()


def _no_borders(table) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tbl_pr.append(borders)


def _page_number(par) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    par.add_run("Trang ")
    for code in ("PAGE",):
        run = par.add_run()
        begin, instr, end = OxmlElement("w:fldChar"), OxmlElement("w:instrText"), OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr.set(qn("xml:space"), "preserve")
        instr.text = code
        end.set(qn("w:fldCharType"), "end")
        run._r.append(begin)
        run._r.append(instr)
        run._r.append(end)


def _md_table(doc, rows: list[list[str]]) -> None:
    width = max(len(r) for r in rows)
    table = doc.add_table(rows=0, cols=width)
    table.style = "Table Grid"
    for i, cells in enumerate(rows):
        row = table.add_row().cells
        for j in range(width):
            par = row[j].paragraphs[0]
            _runs(par, cells[j] if j < len(cells) else "", bold=(i == 0))


def _md_body(doc, md: str) -> None:
    """Markdown đơn giản của model → Word: tiêu đề, gạch đầu dòng, đánh số, bảng, chữ đậm."""
    lines = (md or "").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped or re.fullmatch(r"[-*_]{3,}", stripped):
            i += 1
            continue
        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not _MD_TABLE_SEP.match(lines[i]):
                    block.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if block:
                _md_table(doc, block)
            continue
        if stripped.startswith("#"):
            level = min(3, len(stripped) - len(stripped.lstrip("#")) + 1)
            doc.add_heading(re.sub(r"[*#`]", "", stripped).strip(), level=max(2, level))
        elif re.match(r"^[-*•+]\s+", stripped):
            _runs(doc.add_paragraph(style="List Bullet"), re.sub(r"^[-*•+]\s+", "", stripped))
        elif re.match(r"^\d+[.)]\s+", stripped):
            _runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+[.)]\s+", "", stripped))
        else:
            _runs(doc.add_paragraph(), stripped)
        i += 1


def build_docx(title: str, when: datetime | None, recap: str, transcript: str, *, label: str = "",
               minutes: int = 0, author: str = "", formal: bool = False) -> bytes:
    """Biên bản Word theo mẫu DEGO. `formal` (mẫu chính thức): đầu trang hành chính + chỗ ký."""
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin = Cm(2), Cm(2), Cm(3), Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = WORD_FONT, Pt(13)
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), WORD_FONT)
    for st in ("Heading 1", "Heading 2", "Heading 3"):
        doc.styles[st].font.name = WORD_FONT
        doc.styles[st].font.color.rgb = None

    head = doc.add_table(rows=1, cols=2)
    _no_borders(head)
    left, right = head.rows[0].cells
    lp = left.paragraphs[0]
    lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _runs(lp, COMPANY_NAME, bold=True, size=12)
    if formal:
        _runs(left.add_paragraph(), "Số: ....../BB-HĐ", size=12)
        left.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        rp = right.paragraphs[0]
        rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(rp, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", bold=True, size=12)
        rp2 = right.add_paragraph()
        rp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _runs(rp2, "Độc lập – Tự do – Hạnh phúc", bold=True, size=12)
    else:
        rp = right.paragraphs[0]
        rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        _runs(rp, f"{when:%d/%m/%Y}" if when else "", italic=True, size=12)

    doc.add_paragraph()
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _runs(tp, "BIÊN BẢN HỌP" if formal or not label else label.upper(), bold=True, size=15)
    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _runs(sp, f"Về việc: {title[:150]}", italic=True)

    info = doc.add_table(rows=0, cols=2)
    info.style = "Table Grid"
    for k, v in (("Ngày lập", f"{when:%d/%m/%Y %H:%M}" if when else ""), ("Thời lượng ghi âm", f"{minutes} phút" if minutes else ""),
                 ("Mẫu biên bản", label), ("Người lập", author or "Trợ lý AI (từ bản ghi âm)")):
        if v:
            cells = info.add_row().cells
            _runs(cells[0].paragraphs[0], k, bold=True, size=12)
            _runs(cells[1].paragraphs[0], v, size=12)
    doc.add_paragraph()

    _md_body(doc, recap)

    if formal:
        doc.add_paragraph()
        doc.add_paragraph("Biên bản được lập từ bản ghi âm cuộc họp và được các bên thống nhất.").runs[0].italic = True
        sign = doc.add_table(rows=1, cols=2)
        _no_borders(sign)
        for cell, role in zip(sign.rows[0].cells, ("THƯ KÝ", "CHỦ TRÌ")):
            p1 = cell.paragraphs[0]
            p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _runs(p1, role, bold=True)
            p2 = cell.add_paragraph()
            p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _runs(p2, "(Ký, ghi rõ họ tên)", italic=True, size=12)

    if transcript:
        doc.add_page_break()
        doc.add_heading("Phụ lục: bản chép lời", level=2)
        for line in transcript.splitlines()[:5000]:
            if line.strip():
                _runs(doc.add_paragraph(), line.strip(), size=11)

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _page_number(fp)
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
    if row.transcript:
        #  ai-CR-112: đã có bản chép (viết lại theo mẫu khác, hoặc lần trước hỏng ở bước viết) → chỉ viết lại.
        with user_keys.for_chat(db, row.chat_id):
            try:
                return _write(db, row)
            except MeetingError as e:
                row.status = int(MeetingStatus.FAILED)
                row.error = str(e)[:500]
                db.commit()
                service.reply(db, row.chat_id, f"Em chưa viết lại được biên bản «{telegram.esc(row.title)}»: "
                                               f"{telegram.esc(str(e))}")
                db.commit()
                return {"status": "error", "reason": str(e)[:300]}
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
        service.reply(db, row.chat_id, f"Em chưa làm được biên bản «{telegram.esc(row.title)}» (lỗi hệ thống). Gửi lại "
                                       "giúp em; lặp lại thì báo quản trị xem sổ.")
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
    used_model = model
    segments = split_audio(audio, workdir, duration)
    try:
        for i, seg in enumerate(segments):
            info = gemini_upload(key, seg, "audio/mp3", f"{row.title} {i + 1}/{len(segments)}")
            name = str(info.get("name") or "")
            try:
                info = gemini_wait_active(key, name) if info.get("state") != "ACTIVE" else info
                seg_sec = min(SEGMENT_SEC, duration) if len(segments) > 1 else duration
                text, usage = gemini_transcribe(key, str(info.get("uri") or ""), "audio/mp3", model, audio_sec=seg_sec,
                                                fallback=manager.fallback_model())
            finally:
                if name:
                    gemini_delete(key, name)
            usage_in += int(usage.get("promptTokenCount") or 0)
            usage_out += int(usage.get("candidatesTokenCount") or 0)
            used_model = str(usage.get("model") or model)
            pieces.append(_shift_stamps(text, i * SEGMENT_SEC if len(segments) > 1 else 0))
    except MeetingError as e:
        service.finish_run(db, run, error=str(e))
        db.commit()
        raise
    service.finish_run(db, run, result=ChatResult(text="", provider="gemini", model=used_model, input_tokens=usage_in,
                                                  output_tokens=usage_out))
    transcript = "\n".join(p for p in pieces if p).strip()
    if not transcript:
        raise MeetingError("Em không nghe ra lời nói nào trong tệp.")
    row.transcript = transcript
    db.commit()
    out = _write(db, row)
    return {**out, "segments": len(segments)}


def _author_of(db: Session, user_id: int) -> str:
    from app.modules.user.model import User

    from . import service

    user = db.get(User, int(user_id or 0))
    if user is None:
        return ""
    try:
        return service.describe_user(db, user)[0]
    except Exception:  # noqa: BLE001 — chỉ là dòng «Người lập»
        return str(getattr(user, "email", "") or "")


def _write(db: Session, row: AgentMeeting) -> dict:
    """Viết biên bản theo mẫu của phiên từ bản chép đã có, gửi chữ + Word, lưu kho, đẩy Drive."""
    from . import ai_keys, manager, service

    row.status = int(MeetingStatus.WRITING)
    row.error = ""
    db.commit()
    tpl = template_for_row(row)
    try:
        result = manager.get_provider().ask(
            [ChatMessage(role="user", content=f"YÊU CẦU: {tpl.prompt}\n\nBẢN CHÉP LỜI:\n{row.transcript[:RECAP_MAX_CHARS]}")],
            system=RECAP_SYSTEM, max_tokens=RECAP_MAX_TOKENS, temperature=0.2)
    except Exception as e:  # noqa: BLE001
        raise MeetingError(ai_keys.short_error(str(e))) from None
    recap = (result.text or "").strip()
    if not recap:
        raise MeetingError("Model không viết được biên bản, thử lại giúp em.")
    row.recap = recap
    note = personal_memory.add_note(db, row.user_id, f"Họp: {row.title} — {tpl.label}"[:200], f"{tpl.label}\n\n{recap}")
    row.note_id = int(note.get("note_id") or 0)
    row.status = int(MeetingStatus.DONE)
    row.finished_at = datetime.now()
    db.commit()

    minutes = int((row.duration_sec or 0) // 60)
    service.reply(db, row.chat_id, f"**BIÊN BẢN — {row.title}** ({minutes} phút, {tpl.label.lower()})\n\n{recap}",
                  markdown=True)
    data = build_docx(row.title, row.finished_at, recap, row.transcript, label=tpl.label, minutes=minutes,
                      author=_author_of(db, row.user_id), formal=(tpl.key == "chinh_thuc"))
    filename = re.sub(r"[^\w\- ]+", "", f"bien-ban {row.title} {tpl.label}")[:90].strip() + ".docx"
    telegram.send_document(row.chat_id, filename, data, caption="Biên bản kèm phụ lục bản chép lời")
    drive_link = _upload_word(db, row, filename, data)
    if drive_link:
        service.reply(db, row.chat_id, f"Đã lưu lên Drive, thư mục «{DRIVE_FOLDER}»: {telegram.esc(drive_link)}")
    db.commit()
    return {"status": "done", "meeting_id": row.id, "minutes": minutes, "template": tpl.label}


def rewrite(db: Session, row: AgentMeeting, tpl: Template) -> None:
    """Viết lại biên bản một phiên đã chép lời theo mẫu khác — chạy nền, không chép lời lại."""
    apply_template(row, tpl)
    row.status = int(MeetingStatus.QUEUED)
    db.commit()
    dispatch(row.id)


def recent(db: Session, user_id: int, limit: int = 10) -> list[AgentMeeting]:
    from sqlalchemy import select

    return list(db.scalars(select(AgentMeeting).where(AgentMeeting.user_id == int(user_id))
                           .order_by(AgentMeeting.id.desc()).limit(limit)))


def find(db: Session, user_id: int, ref: str) -> AgentMeeting | None:
    """Phiên của chính người hỏi theo số thứ tự trong `recent` (1 = mới nhất), id, hoặc một phần tên. Trống = mới nhất."""
    rows = recent(db, user_id, 20)
    key = (ref or "").strip().lower().lstrip("#")
    if not key or key in ("mới nhất", "vừa rồi", "gần nhất", "cuối"):
        return rows[0] if rows else None
    if key.isdigit():
        n = int(key)
        if 1 <= n <= len(rows):
            return rows[n - 1]
        return next((r for r in rows if r.id == n), None)
    hits = [r for r in rows if key in (r.title or "").lower()]
    return hits[0] if hits else None


def _upload_word(db: Session, row: AgentMeeting, filename: str, data: bytes) -> str:
    from . import google_link

    link = google_link.get_link(db, row.user_id)
    if link is None:
        return ""
    try:
        folder = google_link.ensure_folder(db, link, DRIVE_FOLDER)
        info = google_link.upload_file(db, link, filename, data,
                                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       parent=folder)
    except Exception as e:  # noqa: BLE001 — Drive hỏng thì thôi, Word đã gửi trong chat
        log.warning("agent_hub: đẩy biên bản lên Drive hỏng: %s", e)
        return ""
    row.drive_file_id = str(info.get("id") or "")[:120]
    return str(info.get("webViewLink") or "")


def describe(row: AgentMeeting) -> dict:
    return {"id": row.id, "title": row.title, "status": MeetingStatus(row.status).name.lower(),
            "minutes": int((row.duration_sec or 0) // 60), "template": template_for_row(row).label,
            "error": row.error or None,
            "info": json.dumps({"note_id": row.note_id}) if row.note_id else None}
