"""Hậu kiểm câu trả lời / tham số công cụ của lõi hội thoại trước khi tới người dùng (ai-CR-227).

Lượt run #365–369 (dev 19/10/2026, Lạc Lạc tạo lịch chuyến Phan Rang – Long Hải) có bốn lỗi máy kiểm được:
  - bịa link: `maps.app.goo.gl/HangRai`, `/VinhHy`, `/TapCham`… (tệp chỉ có link `google.com/maps/dir/?api=1…`) →
    `strip_unknown_urls`: URL chỉ được giữ khi có NGUYÊN VĂN trong tin người dùng / kết quả công cụ / tệp đã đọc;
  - sai thứ: «21/11/2026 Thứ Sáu» (đúng là Thứ Bảy) → `fix_weekdays` tính lại bằng lịch;
  - emoji «✅» dù luật cấm → `strip_emoji`;
  - tạo lịch chồng giờ → `overlapping` (lõi gọi trước mỗi lần tạo sự kiện).
Hàm thuần, không gọi DB / model.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

log = logging.getLogger("app.agent_hub.reply_guard")

URL_RX = re.compile(r"https?://[^\s<>\"'\])]+")
MD_LINK_RX = re.compile(r"\[([^\]\n]{0,200})\]\((https?://[^)\s]+)\)")
URL_REMOVED = "(link em không kiểm được nên không gửi)"
#  Dấu câu hay dính đuôi URL khi model viết trong câu.
_TRAIL = ".,;:!?…"


def _norm(url: str) -> str:
    return url.rstrip(_TRAIL)


def urls_in(text: str) -> set[str]:
    return {_norm(u) for u in URL_RX.findall(text or "")}


def strip_unknown_urls(text: str, allowed: set[str]) -> tuple[str, list[str]]:
    """Bỏ URL không có nguyên văn trong `allowed`. Link Markdown `[nhãn](url)` lạ → chỉ còn nhãn + câu báo."""
    if not text:
        return text, []
    removed: list[str] = []

    def md(m: re.Match) -> str:
        url = _norm(m.group(2))
        if url in allowed:
            return m.group(0)
        removed.append(url)
        return f"{m.group(1)} {URL_REMOVED}".strip()

    out = MD_LINK_RX.sub(md, text)

    def bare(m: re.Match) -> str:
        raw = m.group(0)
        url = _norm(raw)
        if url in allowed:
            return raw
        removed.append(url)
        return URL_REMOVED + raw[len(url):]

    out = URL_RX.sub(bare, out)
    if removed:
        log.warning("reply_guard: bỏ %d link không có nguồn: %s", len(removed), ", ".join(removed[:5]))
    return out, removed


# --- Thứ trong tuần -------------------------------------------------------------------------------------------------
WEEKDAY_NAMES = ("thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật")
_WD = (r"(?:thứ\s+(?:hai|ba|tư|năm|sáu|bảy|[2-7])|chủ\s+nhật|CN|T[2-7])")
_DATE = r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?"
#  «Thứ Sáu 21/11», «thứ 6, ngày 21/11/2026», «T6 21/11» … và «21/11 (Thứ Sáu)», «21/11/2026 - Thứ Sáu».
BEFORE_RX = re.compile(rf"(?<![\wÀ-ỹ])({_WD})(\s*[,·\-–]?\s*(?:ngày\s+)?){_DATE}(?!\d)", re.I)
AFTER_RX = re.compile(rf"(?<!\d){_DATE}(\s*(?:\(|[,·\-–]\s*)?\s*)({_WD})(?![\wÀ-ỹ])", re.I)


def _resolve(d: int, m: int, y: str | None, today: date) -> date | None:
    try:
        if y:
            return date(int(y), m, d)
        cand = date(today.year, m, d)
    except ValueError:
        return None
    if cand < today - timedelta(days=120):          # «5/1» nói vào tháng 11 là tháng 1 năm sau
        try:
            cand = date(today.year + 1, m, d)
        except ValueError:
            return None
    return cand


def _styled(name: str, like: str) -> str:
    """Giữ kiểu chữ của bản gốc: «Thứ Sáu» / «thứ sáu» / «THỨ SÁU»; dạng số «thứ 6», «T6», «CN» giữ dạng số."""
    low = like.lower().replace(" ", "")
    if low in ("cn",) or re.fullmatch(r"t[2-7]", low):
        return "CN" if name == "chủ nhật" else "T" + str(WEEKDAY_NAMES.index(name) + 2)
    if re.fullmatch(r"thứ\s*[2-7]", like.lower()):
        return ("Chủ nhật" if like[0].isupper() else "chủ nhật") if name == "chủ nhật" else \
            like[:like.lower().index("thứ") + 3] + " " + str(WEEKDAY_NAMES.index(name) + 2)
    if like.isupper():
        return name.upper()
    if like[:1].isupper():
        return " ".join(w.capitalize() for w in name.split())
    return name


def fix_weekdays(text: str, today: date) -> tuple[str, int]:
    """Sửa thứ đứng cạnh ngày cho đúng lịch. Trả (văn bản, số chỗ đã sửa)."""
    if not text:
        return text, 0
    fixed = 0

    def correct(wd_text: str, d: str, m: str, y: str | None) -> str:
        nonlocal fixed
        when = _resolve(int(d), int(m), y, today)
        if when is None:
            return wd_text
        right = WEEKDAY_NAMES[when.weekday()]
        new = _styled(right, wd_text)
        if new.lower().replace(" ", "") != wd_text.lower().replace(" ", ""):
            fixed += 1
            return new
        return wd_text

    text = BEFORE_RX.sub(lambda m: correct(m.group(1), m.group(3), m.group(4), m.group(5)) + m.group(2)
                         + m.group(0)[len(m.group(1)) + len(m.group(2)):], text)
    text = AFTER_RX.sub(lambda m: m.group(0)[:m.start(5) - m.start(0)]
                        + correct(m.group(5), m.group(1), m.group(2), m.group(3)), text)
    if fixed:
        log.warning("reply_guard: sửa %d chỗ sai thứ trong tuần", fixed)
    return text, fixed


# --- Emoji ----------------------------------------------------------------------------------------------------------
EMOJI_RX = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍⃣]")


def strip_emoji(text: str) -> str:
    if not text:
        return text
    out = EMOJI_RX.sub("", text)
    return re.sub(r"[ \t]{2,}", " ", re.sub(r"(?m)^[ \t]+(?=\S)", "", out)) if out != text else text


def clean_reply(text: str, *, allowed_urls: set[str], today: date) -> str:
    out, _ = strip_unknown_urls(text, allowed_urls)
    out, _ = fix_weekdays(out, today)
    return strip_emoji(out)


# --- Chồng giờ ------------------------------------------------------------------------------------------------------
def _dt(value) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.fromisoformat(str(value or "").strip().replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def event_span(args: dict) -> tuple[datetime, datetime] | None:
    """(bắt đầu, kết thúc) từ tham số create_calendar_event — kết thúc = end, hoặc start + duration_minutes (mặc định 60)."""
    start = _dt(args.get("start"))
    if start is None:
        return None
    end = _dt(args.get("end"))
    if end is None:
        try:
            minutes = int(args.get("duration_minutes") or 60)
        except (TypeError, ValueError):
            minutes = 60
        end = start + timedelta(minutes=minutes)
    return start, end


def overlapping(span: tuple[datetime, datetime], created: list[tuple[str, datetime, datetime]]) -> str | None:
    """Câu báo lỗi nếu khoảng `span` vô lý (kết thúc ≤ bắt đầu, dài quá 24 giờ) hoặc chồng một sự kiện vừa tạo trong lượt."""
    start, end = span
    if end <= start:
        return "giờ kết thúc không sau giờ bắt đầu"
    if end - start > timedelta(hours=24):
        return "sự kiện dài hơn 24 giờ"
    for title, s, e in created:
        if start < e and s < end:
            return f"chồng giờ với sự kiện vừa tạo «{title}» ({s:%H:%M %d/%m}–{e:%H:%M %d/%m})"
    return None


__all__ = ["urls_in", "strip_unknown_urls", "fix_weekdays", "strip_emoji", "clean_reply", "event_span", "overlapping"]
