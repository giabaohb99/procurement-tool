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


# ---------------------------------------------------------------------------
# ai-CR-133: đọc MỘT bài viết theo đường link người dùng gửi («tóm tắt bài này giúp anh»)
# ---------------------------------------------------------------------------
#  Đường link do NGƯỜI DÙNG đưa → chặn kỹ hơn `fetch`: tự đi theo chuyển hướng từng bước, bước nào cũng phải là địa chỉ
#  công khai (chống trỏ vòng vào mạng nội bộ / máy chủ của chính mình).
_URL_IN_TEXT = re.compile(r"https?://[^\s<>\"'«»]+", re.I)
_META_TAG = re.compile(r"<meta\b[^>]*>", re.I)
_ATTR = re.compile(r'([a-zA-Z:_-]+)\s*=\s*"([^"]*)"|([a-zA-Z:_-]+)\s*=\s*\'([^\']*)\'')
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
ARTICLE_CHARS = 20_000
MAX_REDIRECTS = 4
#  Trang mạng xã hội trả trang đăng nhập cho trình duyệt thường, nhưng vẫn trả phần XEM TRƯỚC (og:…) cho máy đọc link
#  của mạng xã hội — đúng phần Telegram hiện dưới link. Chữ thân bài ít quá thì thử lại bằng tên máy đọc đó.
PREVIEW_UA = "facebookexternalhit/1.1"
LOGIN_WALL_HOSTS = ("facebook.com", "fb.com", "fb.watch", "instagram.com", "threads.net", "tiktok.com", "x.com",
                    "twitter.com", "linkedin.com")


def find_urls(text: str) -> list[str]:
    out = []
    for m in _URL_IN_TEXT.finditer(text or ""):
        url = m.group(0).rstrip(".,;:!?)]}…")
        if url not in out:
            out.append(url)
    return out


def _meta(html_text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for tag in _META_TAG.findall(html_text[:300_000]):
        attrs = {}
        for a in _ATTR.finditer(tag):
            key = (a.group(1) or a.group(3) or "").lower()
            attrs[key] = a.group(2) if a.group(1) else (a.group(4) or "")
        name = (attrs.get("property") or attrs.get("name") or "").lower()
        if name in ("og:title", "og:description", "description", "twitter:title", "twitter:description") \
                and attrs.get("content") and name not in found:
            found[name] = unescape(attrs["content"]).strip()
    return found


def _get_public(url: str, ua: str) -> tuple[str, str]:
    """(địa chỉ cuối, HTML) — tự theo chuyển hướng, mỗi bước đều phải công khai. Hỏng → ("", "")."""
    for _ in range(MAX_REDIRECTS + 1):
        if not public_url(url):
            return "", ""
        try:
            r = requests.get(url, headers={"User-Agent": ua, "Accept-Language": "vi,en;q=0.8"}, timeout=PAGE_TIMEOUT,
                             stream=True, allow_redirects=False)
        except requests.RequestException:
            return "", ""
        with r:
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                from urllib.parse import urljoin

                url = urljoin(url, r.headers["location"])
                continue
            if r.status_code != 200 or "html" not in (r.headers.get("content-type") or "text/html"):
                return "", ""
            data = b""
            for chunk in r.iter_content(64 * 1024):
                data += chunk
                if len(data) > PAGE_MAX_BYTES:
                    break
            return url, data.decode(r.encoding or "utf-8", errors="replace")
    return "", ""


def fetch_article(url: str) -> dict:
    """{url, title, description, text, preview_only} của một bài viết công khai. Không đọc được thì `text` rỗng."""
    host = (urlparse(url).hostname or "").lower()
    wall = any(host == h or host.endswith("." + h) for h in LOGIN_WALL_HOSTS)
    final, html_text = _get_public(url, UA)
    text = page_text(html_text)[:ARTICLE_CHARS] if html_text else ""
    meta = _meta(html_text) if html_text else {}
    if wall or len(text) < 400:
        f2, h2 = _get_public(url, PREVIEW_UA)
        if h2:
            meta = _meta(h2) or meta
            final = final or f2
            if wall:
                text = ""                              # thân trang mạng xã hội là chữ của trang đăng nhập — bỏ
    m = _TITLE.search(html_text or "")
    title = meta.get("og:title") or meta.get("twitter:title") or (unescape(m.group(1)).strip() if m else "")
    desc = meta.get("og:description") or meta.get("description") or meta.get("twitter:description") or ""
    return {"url": final or url, "title": title[:300], "description": desc[:2000], "text": text,
            "preview_only": bool(wall or len(text) < 400)}


# ---------------------------------------------------------------------------
# ai-CR-134: TỆP qua đường link — PDF / Word / Excel / văn bản, Google Drive / Docs công khai, bài báo khoa học
# ---------------------------------------------------------------------------
#  Đại ca 09/10: «đưa một file tài liệu qua link, hoặc bài báo khoa học, nhờ bot tổng hợp / nghiên cứu». Trang HTML đã
#  đọc được (ai-CR-133); đây là phần TỆP — tải về (cùng chốt chặn địa chỉ nội bộ) rồi đưa cho bộ đọc tệp `doc_text`.
DOC_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/msword": ".doc",
    "text/plain": ".txt",
    "text/csv": ".csv",
}
_DOC_EXT = (".pdf", ".docx", ".xlsx", ".doc", ".txt", ".csv")
_ARXIV = re.compile(r"^https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/([^?#]+?)(?:\.pdf)?(?:[?#].*)?$", re.I)
_DRIVE_FILE = re.compile(r"/file/d/([A-Za-z0-9_-]{10,})|[?&]id=([A-Za-z0-9_-]{10,})")
_GDOC = re.compile(r"docs\.google\.com/(document|spreadsheets|presentation)/d/([A-Za-z0-9_-]{10,})")
_FILENAME = re.compile(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", re.I)


def _download(url: str, ua: str, max_bytes: int) -> tuple[str, str, str, bytes]:
    """(địa chỉ cuối, content-type, content-disposition, nội dung) — tự theo chuyển hướng, bước nào cũng phải công khai.
    Hỏng / quá trần → ("", "", "", b"")."""
    from urllib.parse import urljoin

    for _ in range(MAX_REDIRECTS + 1):
        if not public_url(url):
            return "", "", "", b""
        try:
            r = requests.get(url, headers={"User-Agent": ua, "Accept-Language": "vi,en;q=0.8"}, timeout=30,
                             stream=True, allow_redirects=False)
        except requests.RequestException:
            return "", "", "", b""
        with r:
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                url = urljoin(url, r.headers["location"])
                continue
            if r.status_code != 200:
                return "", "", "", b""
            data = b""
            for chunk in r.iter_content(256 * 1024):
                data += chunk
                if len(data) > max_bytes:
                    return url, "too_large", "", b""
            ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
            return url, ctype, r.headers.get("content-disposition") or "", data
    return "", "", "", b""


def _doc_name(url: str, ctype: str, disposition: str, title: str = "") -> str:
    m = _FILENAME.search(disposition or "")
    name = unquote(m.group(1)).strip() if m else ""
    if not name:
        name = unquote(urlparse(url).path.rstrip("/").rsplit("/", 1)[-1] or "")
    if title:                                       # bài báo khoa học: tựa bài dễ nhận hơn tên tệp kiểu «thep.pdf»
        name = re.sub(r'[\\/:*?"<>|]+', " ", title).strip()[:120]
    ext = DOC_TYPES.get(ctype, "")
    if ext and not name.lower().endswith(ext):
        name = (name or "tai-lieu") + ext
    return name or "tai-lieu"


def _is_doc(url: str, ctype: str) -> bool:
    return ctype in DOC_TYPES or (ctype in ("application/octet-stream", "binary/octet-stream", "")
                                  and urlparse(url).path.lower().endswith(_DOC_EXT))


def _drive_targets(url: str) -> list[tuple[str, str]]:
    """Đường tải CÔNG KHAI của một link Google Drive / Docs (chỉ chạy khi tệp chia sẻ «Bất kỳ ai có đường liên kết")."""
    m = _GDOC.search(url)
    if m:
        kind, fid = m.group(1), m.group(2)
        if kind == "document":
            return [(f"https://docs.google.com/document/d/{fid}/export?format=txt", "text/plain")]
        if kind == "spreadsheets":
            return [(f"https://docs.google.com/spreadsheets/d/{fid}/export?format=csv", "text/csv")]
        return [(f"https://docs.google.com/presentation/d/{fid}/export/txt", "text/plain")]
    m = _DRIVE_FILE.search(url)
    if m and "drive.google.com" in url:
        fid = m.group(1) or m.group(2)
        return [(f"https://drive.google.com/uc?export=download&id={fid}", "")]
    return []


def is_google_file(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in ("drive.google.com", "docs.google.com")


def fetch_resource(url: str, *, max_bytes: int) -> dict:
    """Đọc một link: {"kind": "doc", url, name, mime, data} cho tệp; {"kind": "page"} cho trang web (để `fetch_article`
    đọc); {"kind": "none", "reason": …} khi không đọc được (private / quá trần / hỏng)."""
    if is_google_file(url):
        for target, mime in _drive_targets(url):
            final, ctype, disp, data = _download(target, UA, max_bytes)
            if ctype == "too_large":
                return {"kind": "none", "reason": "too_large"}
            if data and ctype != "text/html":
                ctype = mime or ctype
                return {"kind": "doc", "url": url, "name": _doc_name(final, ctype, disp), "mime": ctype, "data": data}
        return {"kind": "none", "reason": "drive_private"}
    m = _ARXIV.match(url)
    if m:
        url = f"https://arxiv.org/pdf/{m.group(1)}"
    final, ctype, disp, data = _download(url, UA, max_bytes)
    if ctype == "too_large":
        return {"kind": "none", "reason": "too_large"}
    if not final:
        return {"kind": "page"}                     # thử lại kiểu trang (máy đọc link mạng xã hội…)
    if _is_doc(final, ctype):
        return {"kind": "doc", "url": final, "name": _doc_name(final, ctype, disp), "mime": ctype, "data": data}
    if "html" in ctype or not ctype:
        meta = {}
        html_text = data.decode("utf-8", errors="replace")
        for tag in _META_TAG.findall(html_text[:300_000]):
            attrs = {(a.group(1) or a.group(3) or "").lower(): (a.group(2) if a.group(1) else a.group(4) or "")
                     for a in _ATTR.finditer(tag)}
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            if name in ("citation_pdf_url", "citation_title") and attrs.get("content") and name not in meta:
                meta[name] = unescape(attrs["content"]).strip()
        #  Trang bài báo khoa học (Springer, Elsevier, MDPI, IEEE…) khai `citation_pdf_url` — bản PDF mở thì đọc đủ bài.
        pdf = meta.get("citation_pdf_url", "")
        if pdf:
            from urllib.parse import urljoin

            f2, c2, d2, data2 = _download(urljoin(final, pdf), UA, max_bytes)
            if data2 and _is_doc(f2, c2):
                return {"kind": "doc", "url": f2, "name": _doc_name(f2, c2, d2, meta.get("citation_title", "")),
                        "mime": c2, "data": data2}
    return {"kind": "page"}
