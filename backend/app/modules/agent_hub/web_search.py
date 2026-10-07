"""Tìm web KHÔNG cần Gemini (ai-CR-110) — đại ca 07/10/2026 chọn: tra mạng chạy được bằng khóa AI đang dùng (DeepSeek
qua modelapi…), không phụ thuộc Google Search của Gemini (khóa Gemini hết hạn mức tìm kiếm là cả bot mù mạng).

Cách làm: tìm DuckDuckGo (bản HTML) → không ra thì Bing → tải song song vài trang đầu, bóc chữ → model đang dùng tóm tắt
kèm số nguồn. Chỉ tải trang công khai: chặn localhost / IP nội bộ (kết quả tìm kiếm là dữ liệu người ngoài).
"""
from __future__ import annotations

import ipaddress
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import requests

log = logging.getLogger("app.agent_hub.web_search")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
SEARCH_TIMEOUT = 15
PAGE_TIMEOUT = 10
PAGE_MAX_BYTES = 1_500_000
PAGE_CHARS = 5000
MAX_RESULTS = 8
FETCH_PAGES = 4

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def _clean(html: str) -> str:
    return _SPACE.sub(" ", unescape(_TAG.sub(" ", html or ""))).strip()


# ---------------------------------------------------------------------------
# Tìm
# ---------------------------------------------------------------------------
def _ddg(query: str) -> list[dict]:
    r = requests.post("https://html.duckduckgo.com/html/", data={"q": query, "kl": "vn-vi"},
                      headers={"User-Agent": UA}, timeout=SEARCH_TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]+class="result__a"|$)',
                         r.text, re.S):
        href, title, rest = m.group(1), _clean(m.group(2)), m.group(3)
        if "uddg=" in href:
            href = unquote(parse_qs(urlparse(href if href.startswith("http") else "https:" + href).query)
                           .get("uddg", [""])[0])
        if "duckduckgo.com/y.js" in href or not href.startswith("http"):
            continue                                    # quảng cáo
        snip = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', rest, re.S)
        out.append({"title": title, "url": href, "snippet": _clean(snip.group(1)) if snip else ""})
    return out


def _bing(query: str) -> list[dict]:
    r = requests.get("https://www.bing.com/search", params={"q": query, "setlang": "vi", "cc": "VN"},
                     headers={"User-Agent": UA}, timeout=SEARCH_TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for block in re.findall(r'<li class="b_algo".*?</li>', r.text, re.S):
        a = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not a or not a.group(1).startswith("http"):
            continue
        p = re.search(r"<p[^>]*>(.*?)</p>", block, re.S)
        out.append({"title": _clean(a.group(2)), "url": unescape(a.group(1)), "snippet": _clean(p.group(1)) if p else ""})
    return out


def search(query: str, limit: int = MAX_RESULTS) -> list[dict]:
    """[{title, url, snippet}] — bỏ trùng tên miền + đường dẫn."""
    results: list[dict] = []
    for engine in (_ddg, _bing):
        try:
            results = engine(query)
        except requests.RequestException as e:
            log.info("agent_hub: %s hỏng: %s", engine.__name__, e)
            results = []
        if results:
            break
    seen, out = set(), []
    for r in results:
        key = r["url"].split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# Đọc trang
# ---------------------------------------------------------------------------
def public_url(url: str) -> bool:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    if u.scheme not in ("http", "https") or not host or host == "localhost" or host.endswith((".local", ".internal")):
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


class _Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "nav", "footer", "header", "svg", "form", "aside", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if not self.depth and data.strip():
            self.parts.append(data.strip())


def page_text(html: str) -> str:
    p = _Text()
    try:
        p.feed(html)
    except Exception:  # noqa: BLE001 — HTML hỏng thì lấy phần đã đọc
        pass
    return _SPACE.sub(" ", " ".join(p.parts)).strip()


def fetch(url: str) -> str:
    """Chữ của một trang công khai (≤ PAGE_CHARS). Hỏng / bị chặn → rỗng."""
    if not public_url(url):
        return ""
    try:
        with requests.get(url, headers={"User-Agent": UA, "Accept-Language": "vi,en;q=0.8"}, timeout=PAGE_TIMEOUT,
                          stream=True, allow_redirects=True) as r:
            if r.status_code != 200 or "html" not in (r.headers.get("content-type") or "text/html"):
                return ""
            if not public_url(r.url):
                return ""                               # chuyển hướng vào mạng nội bộ
            data = b""
            for chunk in r.iter_content(64 * 1024):
                data += chunk
                if len(data) > PAGE_MAX_BYTES:
                    break
            text = data.decode(r.encoding or "utf-8", errors="replace")
    except requests.RequestException:
        return ""
    return page_text(text)[:PAGE_CHARS]


def gather(query: str) -> tuple[list[dict], str]:
    """Tìm + đọc các trang đầu. Trả (nguồn, khối ngữ cảnh đánh số [n] cho model)."""
    results = search(query)
    if not results:
        return [], ""
    top = results[:FETCH_PAGES]
    with ThreadPoolExecutor(max_workers=FETCH_PAGES) as pool:
        texts = list(pool.map(lambda r: fetch(r["url"]), top))
    blocks = []
    for i, r in enumerate(results, 1):
        body = texts[i - 1] if i <= len(texts) else ""
        blocks.append(f"[{i}] {r['title']} — {r['url']}\nTóm tắt kết quả tìm: {r['snippet']}"
                      + (f"\nNội dung trang: {body}" if body else ""))
    return [{"title": r["title"], "url": r["url"]} for r in results], "\n\n".join(blocks)
