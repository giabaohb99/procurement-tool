"""Sổ quyết định của đại ca (ai-CR-015): bot tra trước khi hỏi, đại ca duyệt từng mục mới.

Tệp sống ở `doc/agent-hub/03-so-quyet-dinh.md` của kho mã, mount vào container ở
`settings.AGENT_PLAYBOOK_PATH`. Mô-đun này chỉ làm ba việc: đọc phần mục (từ `## QĐ-01` trở
xuống) để nhét vào lời nhắc, soi xem một đoạn chữ có chạm chủ đề LUÔN HỎI không, và nối một
mục đại ca vừa bấm «Ghi vào sổ» vào cuối tệp.

Luật 3 của sổ («tiền, công nợ, phân quyền, cấu trúc DB, prod, main, gộp mã luôn hỏi») được
thi hành ở ĐÂY và ở người gọi, không nhờ lời dặn trong sổ: việc rủi ro cao không được nạp sổ
(`prompt_block`), và mục chạm các chủ đề đó không ghi được (`append_entry`).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from app.core.config import settings

from .constants import RISK_HIGH

log = logging.getLogger(__name__)

PROMPT_MAX_CHARS = 12000     # sổ dài hơn thì cắt đuôi, mục cũ ở đầu được giữ
ENTRY_FIELD_MAX = 400        # mỗi dòng của một mục do bot nháp

_ENTRY_HEAD = re.compile(r"^## QĐ-(\d+)\s*\|\s*(.+?)\s*$", re.MULTILINE)

#  Chủ đề LUÔN HỎI. Cố ý rộng tay: bắt nhầm thì bot chỉ hỏi thêm một lần, bắt sót thì một
#  mục trong sổ mở đường cho bot tự quyết chuyện tiền hay quyền.
_PROTECTED_TOPICS: tuple[tuple[str, str], ...] = (
    ("tiền", r"\btiền\b|đơn giá|tỷ giá|thanh toán|hóa đơn|hoá đơn|\bthuế\b|\bvat\b"),
    ("công nợ", r"công nợ"),
    ("phân quyền", r"phân quyền|\bquyền\b|permission|scoping|apply_scope|vai trò"),
    #  KHÔNG bắt «thêm cột» trơn: phần lớn là cột của BẢNG GIAO DIỆN (lượt thử thật 23/09 bắt
    #  nhầm luật «cột mới trên bảng danh sách để ẩn»). Cột dưới DB thì câu chữ nhắc tới DB.
    ("cấu trúc cơ sở dữ liệu",
     r"migration|alembic|cơ sở dữ liệu|\bcsdl\b|\bdb\b|model\.py|cấu trúc bảng"),
    ("prod", r"\bprod\b|production|thumua\.degoholding"),
    ("nhánh main", r"\bmain\b"),
    ("gộp mã vào nhánh nền", r"\bmerge\b|erp-v2|\bgộp\b.{0,20}\bnhánh\b"),
    ("xóa dữ liệu", r"(xóa|xoá) (dữ liệu|bản ghi|phiếu)"),
)


class PlaybookError(RuntimeError):
    """Không ghi được mục vào sổ: chạm chủ đề cấm, nháp thiếu ý, hoặc tệp không ghi được."""


def protected_topic(text: str) -> str:
    """Tên chủ đề LUÔN HỎI mà `text` chạm vào, hoặc rỗng."""
    low = (text or "").lower()
    for label, pattern in _PROTECTED_TOPICS:
        if re.search(pattern, low):
            return label
    return ""


def _path() -> Path:
    return Path(settings.AGENT_PLAYBOOK_PATH)


def load_text() -> str:
    """Phần mục của sổ (từ `## QĐ-` đầu tiên), đã cắt trần. Không có tệp thì rỗng, không lỗi."""
    try:
        raw = _path().read_text(encoding="utf-8")
    except OSError:
        log.info("agent_hub: chưa có sổ quyết định ở %s", _path())
        return ""
    m = _ENTRY_HEAD.search(raw)
    if not m:
        return ""
    body = raw[m.start():].strip()
    if len(body) > PROMPT_MAX_CHARS:
        body = body[:PROMPT_MAX_CHARS].rsplit("\n## QĐ-", 1)[0] + "\n\n(… sổ còn tiếp, đã cắt)"
    return body


def titles(text: str | None = None) -> list[str]:
    """`["QĐ-01 | Lỗi không tái hiện được…", …]` — để bot nháp khỏi đề xuất trùng mục có sẵn."""
    text = load_text() if text is None else text
    return [f"QĐ-{int(n):02d} | {t}" for n, t in _ENTRY_HEAD.findall(text)]


def next_id(text: str) -> str:
    nums = [int(n) for n, _ in _ENTRY_HEAD.findall(text)]
    return f"QĐ-{(max(nums) if nums else 0) + 1:02d}"


def prompt_block(risk_level: int) -> str:
    """Sổ để nhét vào lời nhắc, hoặc rỗng nếu việc rủi ro cao (luật 3: việc đó luôn hỏi)."""
    if int(risk_level or 0) >= RISK_HIGH:
        return ""
    return load_text()


def _clean(value) -> str:
    return " ".join(str(value or "").split())[:ENTRY_FIELD_MAX]


def render_entry(qd_id: str, entry: dict, *, source: str) -> str:
    return "\n".join([
        f"## {qd_id} | {_clean(entry.get('title'))}",
        f"- Tình huống: {_clean(entry.get('situation'))}",
        f"- Bot làm: {_clean(entry.get('action'))}",
        f"- Không áp khi: {_clean(entry.get('not_when')) or 'chưa ghi'}",
        f"- Nguồn: {_clean(source)}",
    ]) + "\n"


def append_entry(entry: dict, *, source: str) -> str:
    """Nối một mục vào cuối sổ, trả số `QĐ-xx`. Soi chủ đề cấm LẦN NỮA ở đây — bản nháp đã
    nằm trong sổ lượt chạy cả phút trước khi đại ca bấm, và đây là cửa cuối trước khi thành luật."""
    for key in ("title", "situation", "action"):
        if not _clean(entry.get(key)):
            raise PlaybookError(f"bản nháp thiếu ý «{key}»")
    blob = " ".join(_clean(entry.get(k)) for k in ("title", "situation", "action", "not_when"))
    if topic := protected_topic(blob):
        raise PlaybookError(f"mục này chạm chủ đề «{topic}» — loại đó luôn phải hỏi, không ghi vào sổ")
    path = _path()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise PlaybookError(f"không đọc được sổ ở {path}: {e}") from None
    qd_id = next_id(raw)
    block = render_entry(qd_id, entry, source=source)
    sep = "" if raw.endswith("\n\n") else ("\n" if raw.endswith("\n") else "\n\n")
    try:
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(sep + block)
    except OSError as e:
        raise PlaybookError(f"không ghi được sổ ở {path}: {e}") from None
    log.info("agent_hub: ghi %s vào sổ quyết định lúc %s", qd_id, datetime.now().isoformat())
    return qd_id
