"""Dịch vụ TÌM KIẾM TOÀN VĂN văn bản — `GET /api/documents/search`.

Tái dùng ĐÚNG luật lọc của danh sách văn bản
(`document/controller.py::_list_query`): `visible_condition`, whitelist bộ
lọc nâng cao, lọc thư mục (phase 03/04) — không chép lại, xem `search()`.
Phần RIÊNG của module này: dịch câu tìm của người dùng thành điều kiện khớp
trên `tab_document_search`, tính điểm, dựng đoạn trích.

Hai nhánh dialect, CÙNG một luật khớp (gập dấu, cụm, loại trừ):
- MySQL (chạy thật): `MATCH(...) AGAINST(... IN BOOLEAN MODE)` trên bốn chỉ
  mục FULLTEXT ngram để LỌC THÔ nhanh ở quy mô lớn — kiểm TAY trên MySQL local
  (bộ pytest chạy SQLite, không đụng nhánh này).
- SQLite (bộ kiểm): `LIKE` trên cột đã gập dấu để lọc thô.

Cả hai nhánh SQL chỉ lấy một TẬP ỨNG VIÊN; khớp CHÍNH XÁC (đủ mọi từ, loại
trừ, và tệp quá hạn xem thì không được tính) luôn chạy lại bằng Python trên
tập đó — để hai dialect ra đúng một logic, không phải viết lại luật gập
dấu/cụm/loại trừ hai lần bằng hai phương ngữ SQL khác nhau.
"""
import re
from dataclasses import dataclass, field

from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session

from app.core.text_fold import fold

from . import search_extract
from .attachment_window import view_window_expired
from .model import Document
from .search_model import DocumentSearch
from .version_model import DocumentVersion

#  Toán tử FULLTEXT của MySQL BOOLEAN MODE — lọc khỏi TỪNG TOKEN trước khi gập
#  dấu, để không ai gõ được cú pháp phá câu AGAINST (Bảo mật §, phase 07).
#  Áp dụng cho CẢ HAI dialect để hành vi tách từ đồng nhất.
#
#  ⚠️ `-` CỐ Ý không nằm trong danh sách này. Số hiệu văn bản thật luôn có dấu
#  gạch ngang («08/2026/TB-NS-DEGO», «ABC-999-XYZ»); tước nó thành khoảng trắng
#  thì câu tìm tách thành ba từ RỜI trong khi chữ đã lập chỉ mục vẫn giữ nguyên
#  dấu gạch — hai bên không còn khớp được nhau nữa. `-` Ở ĐẦU token đã được
#  `parse_query` đọc thành LOẠI TRỪ và cắt đi TRƯỚC khi tới đây; dấu gạch nằm
#  GIỮA token là ký tự thường, giữ nguyên. Vì `_mysql_boolean_expr` luôn bọc
#  từng từ trong `+"..."`/`-"..."` (cả cụm coi là một PHRASE), một dấu gạch nằm
#  giữa chuỗi không còn là toán tử BOOLEAN MODE nữa — an toàn giữ lại.
_SPECIAL_CHARS_RE = re.compile(r'[+*"()<>~@]')
#  Cụm trong ngoặc kép giữ nguyên làm MỘT token; còn lại tách theo khoảng trắng.
_TOKEN_RE = re.compile(r'"([^"]+)"|(\S+)')

#  Trọng số điểm — trúng tiêu đề/số hiệu (meta) đứng đầu, rồi nội dung soạn
#  thảo (body), cuối cùng mới tới chữ trong tệp đính kèm (file).
WEIGHT_META = 3
WEIGHT_BODY = 2
WEIGHT_FILE = 1

#  Trần ỨNG VIÊN lấy từ SQL trước khi Python lọc/xếp hạng chính xác — chặn một
#  câu tìm quá phổ biến kéo cả bảng vào bộ nhớ tiến trình `api`.
CANDIDATE_LIMIT = 2000
#  Trần văn bản trong PHẠM VI (quyền + bộ lọc + thư mục) đưa vào SQL `IN (...)`
#  — đo hiệu năng thật ở quy mô ~50k là việc CHƯA LÀM (Bước 7 của phase 07,
#  "đo trên dữ liệu bản sao"); trần này là lưới an toàn tạm thời, không phải
#  con số đã đo.
SCOPE_LIMIT = 20_000

SNIPPET_BEFORE = 80
SNIPPET_AFTER = 80


@dataclass
class ParsedQuery:
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.include


def parse_query(raw: str) -> ParsedQuery:
    """Tách câu tìm thành TỪ/CỤM CẦN CÓ và TỪ LOẠI TRỪ (`-từ`), đã gập dấu.

    Cụm trong ngoặc kép (`"hợp đồng lao động"`) giữ nguyên làm MỘT token — so
    khớp như một chuỗi con liền mạch, không tách theo từ (đúng nghĩa "cụm").
    Toán tử FULLTEXT đặc biệt `+*"()<>~@` trong một token bị lọc bỏ trước khi
    gập dấu; một cụm ký tự đặc biệt lẻ loi (không kèm chữ) rơi ra chuỗi rỗng
    (hoặc còn lại đúng một ký tự) và bị bỏ qua ở bước dưới — không crash,
    không bị coi là "từ khóa rỗng". Riêng `-` GIỮ NGUYÊN khi nằm GIỮA token
    (số hiệu văn bản thật luôn có gạch ngang) — chỉ có nghĩa LOẠI TRỪ khi đứng
    NGAY ĐẦU token, xem `_SPECIAL_CHARS_RE`.

    Token còn dưới 2 ký tự sau khi gập bị bỏ — khớp `ngram` (n=2) của chỉ mục
    MySQL: từ 1 ký tự không có ngram nào để khớp.
    """
    text_ = (raw or "").strip()
    include: list[str] = []
    exclude: list[str] = []
    for m in _TOKEN_RE.finditer(text_):
        phrase, word = m.group(1), m.group(2)
        token = phrase if phrase is not None else (word or "")
        negate = False
        if phrase is None and token.startswith("-") and len(token) > 1:
            negate = True
            token = token[1:]
        cleaned = _SPECIAL_CHARS_RE.sub(" ", token)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            continue
        folded = fold(cleaned)
        if len(folded) < 2:
            continue
        (exclude if negate else include).append(folded)
    return ParsedQuery(include=include, exclude=exclude)


def _any_hit(haystack: str, terms: list[str]) -> bool:
    return any(term in haystack for term in terms)


def _all_hit(haystack: str, terms: list[str]) -> bool:
    return all(term in haystack for term in terms)


def _mysql_boolean_expr(parsed: ParsedQuery) -> str:
    """`+"từ đã gập"` cho mỗi từ/cụm BẮT BUỘC, `-"từ"` cho loại trừ.

    Chỉ nhận CHỮ ĐÃ GẬP DẤU do `parse_query` dựng ra (không phải chuỗi thô
    người dùng gõ) — không toán tử lạ nào lọt vào biểu thức AGAINST (Bảo mật §).
    """
    parts = [f'+"{term}"' for term in parsed.include]
    parts += [f'-"{term}"' for term in parsed.exclude]
    return " ".join(parts)


def _scope_subquery(base_query):
    """Điều kiện PHẠM VI (quyền + bộ lọc + thư mục, đã áp ở tầng gọi) dưới dạng
    QUERY con — KHÔNG kéo id về Python rồi nhồi lại thành `IN (20000 tham số)`
    (M2, rà soát 23/09/2026): 20 nghìn bind param vừa nặng cho driver vừa sát
    trần gói tin MySQL. `ColumnOperators.in_()` nhận thẳng một `Query` (SQLAlchemy
    tự dựng thành subquery), MySQL/SQLite chạy nó phía server — y hệt `EXISTS`
    viết dạng `IN`."""
    return base_query.with_entities(Document.id).limit(SCOPE_LIMIT)


def _candidate_rows(db: Session, scope_query, parsed: ParsedQuery) -> tuple[list[DocumentSearch], bool]:
    """Tập ỨNG VIÊN từ `tab_document_search`, giới hạn trong `scope_query` (đã
    lọc quyền + bộ lọc + thư mục ở tầng gọi). Chỉ lọc THÔ — khớp chính xác
    (VÀ đủ từ, loại trừ, tệp quá hạn) chạy lại bằng Python ở `_evaluate`.

    Trả kèm `truncated` — `True` khi số ứng viên THÔ chạm đúng `CANDIDATE_LIMIT`,
    tức có thể còn ứng viên hợp lệ bị cắt bớt (giao diện nên nói rõ "còn kết
    quả khác, thu hẹp câu tìm" thay vì im lặng coi trang này là đủ)."""
    if not parsed.include:
        return [], False

    query = db.query(DocumentSearch).filter(DocumentSearch.document_id.in_(scope_query))
    dialect = db.get_bind().dialect.name if db.get_bind() is not None else "sqlite"

    if dialect == "mysql":
        expr = _mysql_boolean_expr(parsed)
        match_expr = text(
            "MATCH(meta_text, body_text, file_text) AGAINST (:doc_search_expr IN BOOLEAN MODE)"
        ).bindparams(doc_search_expr=expr)
        #  Sắp theo ĐỘ KHỚP trước khi cắt trần (M2) — không sắp thì
        #  `CANDIDATE_LIMIT` cắt theo thứ tự bất kỳ của MySQL, có thể bỏ sót
        #  đúng những ứng viên khớp NHẤT trước khi Python kịp xếp hạng lại.
        query = query.filter(match_expr).order_by(match_expr.desc())
    else:
        conds = []
        for term in parsed.include:
            like = f"%{term}%"
            conds.append(or_(DocumentSearch.meta_text.like(like),
                             DocumentSearch.body_text.like(like),
                             DocumentSearch.file_text.like(like)))
        #  SQLite (bộ test/dev) không có điểm khớp để sắp trước — id giảm dần
        #  (văn bản MỚI trước) là thứ tự có định, không phải điểm relevance.
        query = query.filter(and_(*conds)).order_by(DocumentSearch.document_id.desc())

    rows = query.limit(CANDIDATE_LIMIT + 1).all()
    truncated = len(rows) > CANDIDATE_LIMIT
    return rows[:CANDIDATE_LIMIT], truncated


@dataclass
class SearchHit:
    document_id: int
    score: int
    matched_in: str  # "meta" | "body" | "file" | ""


def _evaluate(row: DocumentSearch, doc: Document, parsed: ParsedQuery) -> SearchHit | None:
    """Khớp CHÍNH XÁC + tính điểm cho MỘT ứng viên.

    ⚠️ Gọi ĐÚNG `view_window_expired(doc)` — không tự so ngày (Bảo mật §/quyết
    định 23/09 của phase 09): công tắc hạn xem TẮT thì hàm đó luôn trả `False`
    bất kể `attachment_view_until`, nên nhánh này tự động "thoải mái" đúng như
    chốt hiện tại mà không cần biết công tắc đang bật hay tắt.
    """
    file_allowed = not view_window_expired(doc)
    file_text = row.file_text if file_allowed else ""

    combined = f"{row.meta_text} \n {row.body_text} \n {file_text}"
    if not parsed.include:
        return None
    if not _all_hit(combined, parsed.include):
        return None
    if _any_hit(combined, parsed.exclude):
        return None

    meta_hit = _any_hit(row.meta_text, parsed.include)
    body_hit = _any_hit(row.body_text, parsed.include)
    file_hit = file_allowed and _any_hit(row.file_text, parsed.include)

    score = ((WEIGHT_META if meta_hit else 0)
            + (WEIGHT_BODY if body_hit else 0)
            + (WEIGHT_FILE if file_hit else 0))
    if score == 0:
        #  Mọi từ khớp (đã qua `_all_hit` ở trên) nhưng rải NGOÀI ba cột (vd
        #  khớp nhờ khoảng trắng nối `combined`) — coi như trúng meta để có
        #  điểm dương, tránh chia 0 trong bước sắp hạng.
        score, meta_hit = WEIGHT_META, True

    matched_in = "body" if body_hit else ("file" if file_hit else "meta")
    return SearchHit(document_id=row.document_id, score=score, matched_in=matched_in)


def _merge_highlights(spans: list[list[int]]) -> list[list[int]]:
    if not spans:
        return []
    spans = sorted(spans)
    merged = [spans[0]]
    for s, e in spans[1:]:
        last = merged[-1]
        if s <= last[1]:
            last[1] = max(last[1], e)
        else:
            merged.append([s, e])
    return merged


def _snippet(folded_text: str, raw_text: str, terms: list[str]) -> dict | None:
    """Đoạn trích ±80 ký tự quanh lần trúng ĐẦU TIÊN, `highlights` là offset
    TRONG chính đoạn trích (không phải trong toàn văn) — giao diện dựng
    `<mark>` thẳng từ đó, không cần biết gì về vị trí gốc.
    """
    if not folded_text or not raw_text or len(folded_text) != len(raw_text) or not terms:
        return None

    positions: list[tuple[int, int]] = []
    for term in terms:
        start = 0
        while True:
            idx = folded_text.find(term, start)
            if idx < 0:
                break
            positions.append((idx, idx + len(term)))
            start = idx + max(len(term), 1)
    if not positions:
        return None

    positions.sort()
    center = positions[0][0]
    window_start = max(0, center - SNIPPET_BEFORE)
    window_end = min(len(raw_text), center + SNIPPET_AFTER)

    prefix = "…" if window_start > 0 else ""
    suffix = "…" if window_end < len(raw_text) else ""
    text_ = prefix + raw_text[window_start:window_end] + suffix

    highlights = []
    for s, e in positions:
        if e <= window_start or s >= window_end:
            continue
        hs = max(s, window_start) - window_start + len(prefix)
        he = min(e, window_end) - window_start + len(prefix)
        if he > hs:
            highlights.append([hs, he])

    return {"text": text_, "highlights": _merge_highlights(highlights)}


def _file_name_at(file_names: list, pos: int) -> str:
    for entry in file_names or []:
        if entry.get("start", 0) <= pos < entry.get("end", 0):
            return entry.get("name", "")
    return ""


def _search_payload(db: Session, hit: SearchHit, row: DocumentSearch, doc: Document,
                    parsed: ParsedQuery) -> dict:
    if hit.matched_in == "body":
        version = (db.get(DocumentVersion, doc.current_version_id)
                  if doc.current_version_id else None)
        raw_text = search_extract.strip_html(version.content_html) if version else ""
        snippet = _snippet(row.body_text, raw_text, parsed.include)
        return {"score": hit.score, "matched_in": hit.matched_in,
               "match_label": "Nội dung", "snippet": snippet}

    if hit.matched_in == "file":
        snippet = _snippet(row.file_text, row.file_text_raw, parsed.include)
        file_name = ""
        #  Đoạn trích lấy quanh lần trúng ĐẦU TIÊN trong `file_text` — dò
        #  đúng lần trúng đó để gọi tên đúng tệp chứa nó.
        first_idx = min(
            (row.file_text.find(term) for term in parsed.include if term in row.file_text),
            default=-1,
        )
        if first_idx >= 0:
            file_name = _file_name_at(row.file_names, first_idx)
        label = f"Tệp {file_name}" if file_name else "Tệp đính kèm"
        return {"score": hit.score, "matched_in": hit.matched_in,
               "match_label": label, "snippet": snippet}

    return {"score": hit.score, "matched_in": hit.matched_in, "match_label": "", "snippet": None}


def search(db: Session, request, user, profile: dict, q: str,
          effective_from=None, effective_to=None, page: int = 1, page_size: int = 20) -> dict:
    """Tìm toàn văn — trả `{total, items, truncated}` cùng hình dạng
    `serializer.serialize_many` của danh sách văn bản, mỗi dòng thêm khóa
    `search` (điểm, nơi trúng, đoạn trích). `truncated` (M2, rà soát 23/09/2026)
    báo SQL đã cắt bớt ứng viên thô trước khi xếp hạng — có thể còn kết quả
    hợp lệ ngoài trang này, không chỉ là "đã hết".

    Câu tìm rỗng hoặc chỉ còn token dưới 2 ký tự sau khi lọc/gập → RỖNG tường
    minh, không rơi về "liệt kê tất cả" (khác hành vi `q` của danh sách văn
    bản thường — tìm toàn văn mà gõ trống là một câu hỏi vô nghĩa, không phải
    "bỏ lọc").
    """
    from . import serializer
    from .controller import _list_query

    parsed = parse_query(q)
    if parsed.is_empty:
        return {"total": 0, "items": [], "truncated": False}

    base_query, _visible = _list_query(request, db, user, profile, "",
                                       effective_from, effective_to)
    scope_query = _scope_subquery(base_query)
    rows, truncated = _candidate_rows(db, scope_query, parsed)
    if not rows:
        return {"total": 0, "items": [], "truncated": False}

    doc_ids = [r.document_id for r in rows]
    docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()}

    hits: list[SearchHit] = []
    rows_by_id: dict[int, DocumentSearch] = {}
    for row in rows:
        doc = docs.get(row.document_id)
        if doc is None:
            continue
        hit = _evaluate(row, doc, parsed)
        if hit is not None:
            hits.append(hit)
            rows_by_id[hit.document_id] = row

    hits.sort(key=lambda h: (-h.score, -h.document_id))
    total = len(hits)

    page = max(page, 1)
    page_size = max(page_size, 1)
    offset = (page - 1) * page_size
    page_hits = hits[offset:offset + page_size]
    if not page_hits:
        return {"total": total, "items": [], "truncated": truncated}

    result_docs = [docs[h.document_id] for h in page_hits]
    serialized = serializer.serialize_many(db, result_docs, user=user)
    by_id = {row["id"]: row for row in serialized}

    items = []
    for hit in page_hits:
        row = by_id.get(hit.document_id)
        if row is None:
            continue
        row["search"] = _search_payload(db, hit, rows_by_id[hit.document_id],
                                        docs[hit.document_id], parsed)
        items.append(row)

    #  `truncated` (M2, rà soát 23/09/2026): SQL đã cắt ở `CANDIDATE_LIMIT`
    #  ứng viên THÔ trước khi Python xếp hạng chính xác — báo cho giao diện để
    #  nói "còn kết quả khác, thu hẹp câu tìm" thay vì im lặng coi là đủ.
    return {"total": total, "items": items, "truncated": truncated}
