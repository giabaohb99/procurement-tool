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
MAX_PARTS = 8                                  # ai-CR-116: tối đa 8 tệp Drive gộp thành một cuộc họp
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
    #  ai-CR-116: chuẩn recap của công ty (STD-RECAP-DEGO-v1.0) — mặc định, Word dựng đúng các khối của chuẩn.
    Template("dego", "Recap DEGO",
             "Viết RECAP HỌP theo chuẩn DEGO, Markdown, ĐÚNG các mục theo thứ tự sau (mục nào không có nội dung thì bỏ):\n"
             "## TÓM TẮT NHANH — 3–6 gạch đầu dòng, mỗi dòng một ý cốt lõi.\n"
             "## NỘI DUNG CUỘC HỌP — mỗi vấn đề một mục «### 1. Tên vấn đề»: một đoạn diễn giải ngắn; dòng «Ý CHÍNH:» rồi các "
             "gạch đầu dòng; dòng «ĐÃ CHỐT:» rồi các dòng bắt đầu bằng «✓ ».\n"
             "## CÔNG VIỆC CẦN LÀM — bảng | Việc | Người | Hạn | Ưu tiên | (Ưu tiên chỉ ghi Cao / TB / Thấp; thiếu thì «chưa rõ»).\n"
             "## VẤN ĐỀ CÒN MỞ — gạch đầu dòng.\n"
             "## NGƯỜI THAM DỰ — gạch đầu dòng «Tên – vai trò (nếu nghe được)».\n"
             "In **đậm** con số, tên riêng, mốc thời gian quan trọng. Không viết tiêu đề lớn ở đầu.",
             ("recap", "chuẩn dego", "mẫu dego", "mẫu công ty")),
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
DEFAULT_TEMPLATE = "dego"
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
    #  ai-CR-118: so khớp không dấu («chinh thuc» cũng ra mẫu chính thức).
    from app.modules.assistant.glossary import fold

    t = fold(text)
    for tpl in BUILTIN.values():
        if any(fold(w) in t for w in tpl.words):
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
    from app.modules.assistant.glossary import fold

    low = fold(raw)
    if db is not None:
        for tpl in sorted(personal_templates(db, user_id), key=lambda t: -len(t.label)):
            if fold(tpl.label) and fold(tpl.label) in low:
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


def concat_audio(parts: list[Path], dest: Path) -> None:
    """Nối các phần (đã cùng định dạng sau `to_audio`) thành một tệp theo đúng thứ tự."""
    if len(parts) == 1:
        shutil.move(str(parts[0]), str(dest))
        return
    listing = dest.parent / "concat.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    _run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
          "-c", "copy", str(dest)])


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
_LABEL_LINE = re.compile(r"^\**\s*(Ý CHÍNH|ĐÃ CHỐT|KẾT LUẬN|QUYẾT ĐỊNH|VẤN ĐỀ|ĐỀ XUẤT)\s*:?\s*\**\s*:?\s*$", re.I)
_TLDR_HEAD = re.compile(r"(TL;?DR|TÓM TẮT NHANH)", re.I)
_PEOPLE_HEAD = re.compile(r"(NGƯỜI THAM DỰ|THÀNH PHẦN)", re.I)
COMPANY_LINE = "DEGO HOLDING · Cần Thơ, Việt Nam"
FOOTER_CENTER = "Tài liệu nội bộ · Lưu hành hạn chế"
AI_NOTE = ("Biên bản tổng hợp tự động từ bản ghi âm bằng Trợ lý AI — tên riêng, thuật ngữ và số liệu nên đối chiếu lại "
           "với bản chép lời ở phụ lục.")


def _html(text: str) -> str:
    """Markdown một dòng → chuỗi cho `dego_docx.add_runs`: **đậm** → <strong>, bỏ các dấu Markdown còn lại."""
    text = re.sub(r"`|(?<!\*)\*(?!\*)|^#+\s*", "", (text or "").strip())
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    return _MD_BOLD.sub(r"<strong>\1</strong>", text)


def _plain(text: str) -> str:
    return re.sub(r"</?strong>", "", _html(text))


def _md_table(doc, rows: list[list[str]]) -> None:
    """Bảng Markdown → bảng DEGO: hàng đầu nền teal chữ trắng, cột STT navy, dòng chẵn tô nền; cột «Ưu tiên» tô màu."""
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    from . import dego_docx as D

    head, body = rows[0], rows[1:]
    has_no = bool(head) and _plain(head[0]).strip().lower() in ("stt", "#", "tt")
    if not has_no:
        head = ["STT"] + head
        body = [[str(i)] + r for i, r in enumerate(body, 1)]
    n = len(head)
    t = doc.add_table(rows=1, cols=n)
    pri_col = next((i for i, h in enumerate(head) if "ưu tiên" in _plain(h).lower()), -1)
    for i, c in enumerate(t.rows[0].cells):
        D.shade(c, D.TEAL)
        D.cell_borders(c, color=D.TEAL, sz=4)
        D.set_cell_margins(c, 60, 60, 110, 110)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in (0, pri_col) else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(_plain(head[i]))
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = D.C(D.WHITE)
        D.set_font(r)
        c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for idx, row in enumerate(body, 1):
        cells = t.add_row().cells
        for j, c in enumerate(cells):
            value = row[j] if j < len(row) else ""
            D.cell_borders(c, color=D.LINE, sz=4)
            D.set_cell_margins(c, 50, 50, 110, 110)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.2
            if j == pri_col and _plain(value).strip():
                bg, tx = D.PRI.get(_plain(value).strip(), D.PRI_DEFAULT)
                D.shade(c, bg)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(_plain(value).strip())
                r.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = D.C(tx)
                D.set_font(r)
                continue
            if idx % 2 == 0:
                D.shade(c, D.BG_ROWALT)
            if j == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                r = p.add_run(_plain(value) or str(idx))
                r.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = D.C(D.NAVY)
                D.set_font(r)
            else:
                D.add_runs(p, _html(value), size=9)
    #  Bề rộng: STT 1,25 cm, cột thứ hai (nội dung chính) rộng gấp đôi các cột còn lại.
    rest = D.USABLE_CM - 1.25
    weights = [2.0] + [1.0] * (n - 2) if n > 2 else [1.0]
    unit = rest / sum(weights)
    D.set_col_widths(t, [1.25] + [w * unit for w in weights])
    D.spacer(doc, 6)


def _participants(recap: str) -> str:
    """Gạch đầu dòng dưới mục «NGƯỜI THAM DỰ» → một dòng cho bảng thông tin (để trống nếu không có)."""
    out, inside = [], False
    for line in (recap or "").splitlines():
        s = line.strip()
        if s.startswith("#"):
            inside = bool(_PEOPLE_HEAD.search(s))
            continue
        if inside and re.match(r"^[-*•+]\s+", s):
            out.append(_plain(re.sub(r"^[-*•+]\s+", "", s)))
    return " · ".join(out)[:600]


def _md_body(doc, md: str) -> None:
    """Markdown của model → các khối DEGO: «## TL;DR / TÓM TẮT NHANH» → hộp TL;DR · «## …» → thanh mục teal · «### …» →
    đề mục con · «Ý CHÍNH: / ĐÃ CHỐT:» → nhãn · «✓ …» → dòng đã chốt · gạch đầu dòng · bảng · đoạn văn."""
    from . import dego_docx as D

    lines = (md or "").splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or re.fullmatch(r"[-*_]{3,}", s):
            i += 1
            continue
        level = len(s) - len(s.lstrip("#"))
        if level and _TLDR_HEAD.search(s):
            items = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("#"):
                t = lines[i].strip()
                if t:
                    items.append(_html(re.sub(r"^([-*•+]|\d+[.)])\s+", "", t)))
                i += 1
            if items:
                D.tldr_box(doc, "TL;DR — Tóm tắt nhanh", items)
            continue
        if s.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not _MD_TABLE_SEP.match(lines[i]):
                    block.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if len(block) >= 2:
                _md_table(doc, block)
            elif block:
                D.para(doc, _html(" · ".join(block[0])))
            continue
        if level in (1, 2):
            D.section_bar(doc, _plain(s))
        elif level >= 3:
            D.h2(doc, _plain(s))
        elif _LABEL_LINE.match(s):
            D.label(doc, _plain(s).rstrip(": "))
        elif re.match(r"^([-*•+]\s+)?✓\s*", s) and "✓" in s[:4]:
            D.check(doc, _html(re.sub(r"^([-*•+]\s+)?✓\s*", "", s)))
        elif re.match(r"^[-*•+]\s+", s):
            D.bullet(doc, _html(re.sub(r"^[-*•+]\s+", "", s)))
        elif re.match(r"^\d+[.)]\s+", s):
            m = re.match(r"^(\d+[.)])\s+(.*)$", s)
            D.bullet(doc, _html(m.group(2)), marker=m.group(1))
        else:
            D.para(doc, _html(s))
        i += 1


def build_docx(title: str, when: datetime | None, recap: str, transcript: str, *, label: str = "",
               minutes: int = 0, author: str = "", formal: bool = False, code: str = "", source: str = "") -> bytes:
    """Biên bản / recap Word theo chuẩn DEGO (ai-CR-116, STD-RECAP-DEGO-v1.0 qua `dego_docx`): đầu trang logo + mã văn
    bản, tiêu đề, bảng thông tin, TL;DR, các thanh mục teal, bảng việc, (mẫu chính thức: khối XÉT DUYỆT ký), phụ lục bản
    chép lời, chân trang lặp mọi trang có số trang."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    from . import dego_docx as D

    when = when or datetime.now()
    doc = D.new_document()
    head = ["BIÊN BẢN HỌP", "MEETING MINUTES"] if formal else ["RECAP HỌP", "MEETING RECAP"]
    D.header(doc, head + [f"Mã văn bản: {code or f'RECAP-{when:%Y.%m.%d}'}", "Phiên bản: v1.0"])
    D.title(doc, (title or "Cuộc họp")[:150].upper())
    D.subtitle(doc, f"{label or 'Biên bản'} · tổng hợp từ bản ghi âm")
    people = _participants(recap)
    D.meta_table(doc, [("Ngày lập", f"{when:%d/%m/%Y %H:%M}", "Thời lượng", f"{minutes} phút" if minutes else "—"),
                       ("Người ghi", author or "Trợ lý AI", "Nguồn", (source or "tệp ghi âm")[:80])],
                 full=[("Thành phần", _html(people))] if people else None)
    D.note(doc, AI_NOTE)
    _md_body(doc, recap)
    if formal:
        D.section_bar(doc, "XÉT DUYỆT")
        D.signoff(doc, [("THƯ KÝ", ""), ("CHỦ TRÌ", "")])
    if transcript:
        doc.add_page_break()
        D.section_bar(doc, "PHỤ LỤC — BẢN CHÉP LỜI")
        for line in transcript.splitlines()[:5000]:
            if line.strip():
                D.para(doc, _html(line.strip()), size=9, space_after=2)
    D.footer(doc, COMPANY_LINE, FOOTER_CENTER, "Trang ", sub="Bản recap tạo tự động · Trợ lý AI DEGO")
    fp = doc.sections[0].footer.paragraphs[0]
    run = fp.add_run()
    run.bold = True
    run.font.size = Pt(7.5)
    run.font.color.rgb = D.C(D.GRAY)
    for kind, text in (("begin", None), ("instr", "PAGE"), ("end", None)):
        el = OxmlElement("w:instrText" if kind == "instr" else "w:fldChar")
        if kind == "instr":
            el.set(qn("xml:space"), "preserve")
            el.text = text
        else:
            el.set(qn("w:fldCharType"), kind)
        run._r.append(el)
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
    audio = workdir / "audio.mp3"
    if row.source_kind == int(SourceKind.DRIVE):
        #  ai-CR-116 (bước 10.4): nhiều tệp Drive của CÙNG một cuộc họp (ghi thành nhiều phần) — `source_ref` = các id
        #  cách nhau dấu phẩy, đã xếp theo giờ tạo; mỗi tệp tách tiếng rồi nối thành một.
        ids = [x for x in row.source_ref.split(",") if x.strip()][:MAX_PARTS]
        parts: list[Path] = []
        for i, fid in enumerate(ids):
            src = workdir / f"source_{i}.bin"
            name, mime = _download_drive(db, row.user_id, fid.strip(), src)
            if i == 0:
                if row.title in ("", "Cuộc họp"):
                    row.title = Path(name).stem[:200] or row.title
                row.mime = mime[:80]
            part = workdir / f"part_{i}.mp3"
            to_audio(src, part)
            src.unlink(missing_ok=True)
            parts.append(part)
        concat_audio(parts, audio)
    else:
        src = workdir / "source.bin"
        _download_telegram(row.source_ref, src)
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
    tag_run(run, row, Step.TRANSCRIBE)
    transcript = "\n".join(p for p in pieces if p).strip()
    if not transcript:
        raise MeetingError("Em không nghe ra lời nói nào trong tệp.")
    row.transcript = transcript
    db.commit()
    out = _write(db, row)
    return {**out, "segments": len(segments)}


# ---------------------------------------------------------------------------
# Chi phí từng biên bản (ai-CR-158) — đại ca 10/10: «chi phí token cho cái recap này là bao nhiêu»
# ---------------------------------------------------------------------------
class Step(IntEnum):
    TRANSCRIBE = 1      # chép lời
    WRITE = 2           # viết biên bản (cả lần viết lại theo mẫu khác)
    EXTRACT = 3         # rút việc + lịch


STEP_LABELS = {Step.TRANSCRIBE: "Chép lời", Step.WRITE: "Viết biên bản", Step.EXTRACT: "Rút việc và lịch"}


def tag_run(run, row: AgentMeeting, step: Step) -> None:
    """Gắn một dòng sổ gọi model vào phiên họp (`finish_run` ghi đè artifact nên gắn SAU nó)."""
    art = dict(run.artifact) if isinstance(run.artifact, dict) else {}
    art.pop("text", None)                    # bản chép / biên bản đã nằm ở tab_agent_meeting, không chép lần hai
    run.artifact = {**art, "meeting_id": int(row.id), "step": int(step)}


def runs_of(db: Session, row: AgentMeeting) -> list:
    """Các lượt model của một phiên họp. Phiên làm TRƯỚC ai-CR-158 chưa gắn: lấy lượt chép lời trong khoảng chạy của
    phiên (lượt viết biên bản hồi đó không ghi sổ)."""
    from datetime import timedelta

    from .constants import STAGE_MEETING
    from .model import AgentRun

    since = (row.started_at or row.created_at or datetime.now()) - timedelta(minutes=5)
    rows = (db.query(AgentRun).filter(AgentRun.stage == STAGE_MEETING, AgentRun.started_at >= since)
            .order_by(AgentRun.id).limit(500).all())
    mine = [r for r in rows if isinstance(r.artifact, dict) and int(r.artifact.get("meeting_id") or 0) == row.id]
    if mine:
        return mine
    until = row.finished_at or datetime.now()
    return [r for r in rows if not (isinstance(r.artifact, dict) and r.artifact.get("meeting_id"))
            and r.started_at and r.started_at <= until and r.owner_id in (0, user_keys.active_owner())][:1]


def cost_text(db: Session, row: AgentMeeting) -> str:
    """Tin trả lời: token vào / ra + tiền ước từng bước của MỘT biên bản."""
    from . import service
    from .constants import RUN_OK

    esc = telegram.esc
    runs = runs_of(db, row)
    minutes = int((row.duration_sec or 0) // 60)
    lines = [f"<b>Chi phí biên bản: {esc(row.title or f'#{row.id}')}</b>" + (f" ({minutes} phút ghi âm)" if minutes else "")]
    if not runs:
        lines.append("Em không tìm thấy lượt gọi model nào của biên bản này trong sổ.")
        return "\n".join(lines)
    tagged = any(isinstance(r.artifact, dict) and r.artifact.get("meeting_id") for r in runs)
    total_in = total_out = 0
    total_usd = 0.0
    for r in runs:
        step = int((r.artifact or {}).get("step") or Step.TRANSCRIBE) if isinstance(r.artifact, dict) else 1
        label = next((v for k, v in STEP_LABELS.items() if int(k) == step), "Lượt khác")
        total_in += int(r.input_tokens or 0)
        total_out += int(r.output_tokens or 0)
        total_usd += float(r.cost_usd or 0)
        state = "" if r.status == RUN_OK else " · <i>hỏng</i>"
        lines.append(f"• {esc(label)}: {esc(r.model or '?')} · {int(r.input_tokens or 0):,} token vào / "
                     f"{int(r.output_tokens or 0):,} ra · {service._money(float(r.cost_usd or 0))}{state}"
                     .replace(",", "."))
    lines.append(f"<b>Tổng:</b> {total_in + total_out:,} token · {service._money(total_usd)}".replace(",", "."))
    if not tagged:
        lines.append("<i>Biên bản này làm trước 10/10 nên em chỉ có số của bước chép lời; lượt viết biên bản hồi đó "
                     "chưa được ghi sổ.</i>")
    lines.append(f"Tiền thật trả theo khóa AI, ước theo bảng giá. Tỷ giá tạm {settings.AGENT_USD_VND:,} đ/USD."
                 .replace(",", "."))
    return "\n".join(lines)


def _author_of(db: Session, user_id: int) -> str:
    from . import erp, service

    user = erp.user_by_id(db, int(user_id or 0))
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
    from .constants import STAGE_MEETING

    run = service.start_run(db, 0, STAGE_MEETING)      # ai-CR-158: lượt viết biên bản cũng ghi sổ, gắn với phiên họp
    try:
        result = manager.get_provider().ask(
            [ChatMessage(role="user", content=f"YÊU CẦU: {tpl.prompt}\n\nBẢN CHÉP LỜI:\n{row.transcript[:RECAP_MAX_CHARS]}")],
            system=RECAP_SYSTEM, max_tokens=RECAP_MAX_TOKENS, temperature=0.2)
    except Exception as e:  # noqa: BLE001
        service.finish_run(db, run, error=str(e))
        tag_run(run, row, Step.WRITE)
        db.commit()
        raise MeetingError(ai_keys.short_error(str(e))) from None
    service.finish_run(db, run, result=result)
    tag_run(run, row, Step.WRITE)
    db.commit()
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
    filename, data = word_of(db, row)
    telegram.send_document(row.chat_id, filename, data, caption="Biên bản kèm phụ lục bản chép lời")
    drive_link = _upload_word(db, row, filename, data)
    if drive_link:
        service.reply(db, row.chat_id, f"Đã lưu lên Drive, thư mục «{DRIVE_FOLDER}»: {telegram.esc(drive_link)}")
    db.commit()
    #  ai-CR-114 (bước 10.3): rút việc + lịch hẹn thành MỘT thẻ duyệt; hỏng thì thôi, biên bản đã gửi.
    from . import meeting_actions

    meeting_actions.offer(db, row)
    return {"status": "done", "meeting_id": row.id, "minutes": minutes, "template": tpl.label}


def word_of(db: Session, row: AgentMeeting) -> tuple[str, bytes]:
    """(tên tệp, nội dung) Word của một phiên đã viết xong — dùng khi gửi lần đầu và khi gửi lại."""
    tpl = template_for_row(row)
    when = row.finished_at or datetime.now()
    data = build_docx(row.title, when, row.recap, row.transcript, label=tpl.label,
                      minutes=int((row.duration_sec or 0) // 60), author=_author_of(db, row.user_id),
                      formal=(tpl.key == "chinh_thuc"), code=f"RECAP-{when:%Y.%m.%d}-{row.id}",
                      source="Google Drive" if row.source_kind == int(SourceKind.DRIVE) else "Telegram")
    filename = re.sub(r"[^\w\- ]+", "", f"bien-ban {row.title} {tpl.label}")[:90].strip() + ".docx"
    return filename, data


def resend(db: Session, row: AgentMeeting) -> None:
    """ai-CR-116: gửi lại biên bản đã làm (chữ + Word) và thẻ việc / lịch còn chờ — «report cuộc họp mới nhất»."""
    from . import meeting_actions, service

    tpl = template_for_row(row)
    minutes = int((row.duration_sec or 0) // 60)
    service.reply(db, row.chat_id, f"**BIÊN BẢN — {row.title}** ({minutes} phút, {tpl.label.lower()})\n\n{row.recap}",
                  markdown=True)
    filename, data = word_of(db, row)
    telegram.send_document(row.chat_id, filename, data, caption="Biên bản kèm phụ lục bản chép lời")
    db.commit()
    meeting_actions.offer(db, row)


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
