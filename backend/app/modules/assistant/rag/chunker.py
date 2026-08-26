"""Cắt văn bản dài thành đoạn (chunk) để nhúng vector.

Thuần: không đụng DB, không gọi mạng — nên kiểm thử rẻ và đây chính là chỗ dễ sai âm thầm
(đoạn quá dài vượt trần token của model nhúng, hoặc cắt mất ngữ cảnh câu bắc cầu).

Cách cắt: bỏ HTML -> tách câu -> gói các câu liền nhau tới ~ngưỡng ký tự. Khi sang đoạn mới
thì GIỮ LẠI câu cuối của đoạn trước làm câu mở (chồng lấn nhẹ) để câu nằm vắt qua ranh giới
vẫn tìm được. Câu đơn lẻ dài quá ngưỡng thì cắt cứng theo ký tự.
"""
import re

# Ngưỡng ký tự mỗi đoạn. ~900 ký tự tiếng Việt ≈ 300-400 token — thừa an toàn dưới trần của
# model nhúng, mà vẫn đủ dài để một đoạn mang trọn một ý.
MAX_CHARS = 900

_BLOCK_CLOSE = re.compile(r"</(p|div|li|h[1-6]|tr|section|article)\s*>", re.IGNORECASE)
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_WS_INLINE = re.compile(r"[ \t]+")
_WS_BREAKS = re.compile(r"\n{2,}")
# Tách câu: sau dấu kết câu (. ! ? …) hoặc xuống dòng, theo sau là khoảng trắng.
_SENT_SPLIT = re.compile(r"(?<=[.!?…\n])\s+")


def strip_html(html: str) -> str:
    """Bỏ thẻ HTML nhưng GIỮ ranh giới khối thành xuống dòng (để tách câu không dính vào nhau)."""
    if not html:
        return ""
    text = _BR.sub("\n", html)
    text = _BLOCK_CLOSE.sub("\n", text)
    text = _TAG.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = _WS_INLINE.sub(" ", text)
    text = _WS_BREAKS.sub("\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def _hard_split(segment: str, max_chars: int) -> list[str]:
    """Cắt cứng một câu dài quá ngưỡng theo cửa sổ ký tự."""
    return [segment[i:i + max_chars] for i in range(0, len(segment), max_chars)]


def chunk_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Cắt `text` (có thể chứa HTML) thành danh sách đoạn, mỗi đoạn <= ~max_chars ký tự.

    Rỗng -> []. Ngắn hơn ngưỡng -> một đoạn nguyên. Không đoạn nào rỗng.
    """
    clean = strip_html(text)
    if not clean:
        return []
    if len(clean) <= max_chars:
        return [clean]

    sentences = [s.strip() for s in _SENT_SPLIT.split(clean) if s.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        if len(sentence) > max_chars:
            # Câu khổng lồ: chốt đoạn đang gom rồi cắt cứng câu này.
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            chunks.extend(_hard_split(sentence, max_chars))
            continue

        if current and current_len + len(sentence) + 1 > max_chars:
            chunks.append(" ".join(current))
            # Chồng lấn: mang câu cuối sang đoạn mới, trừ khi nó đã dài quá nửa ngưỡng.
            last = current[-1]
            current = [last] if len(last) <= max_chars // 2 else []
            current_len = (len(last) + 1) if current else 0

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))
    return chunks
