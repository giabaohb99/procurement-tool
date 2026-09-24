"""Nạp chỉ mục vector cho nội dung loại B: bài HDSD (help_article) và câu hỏi FAQ (faq).

Luồng một nguồn: đọc bản ghi -> ghép văn bản -> cắt đoạn -> nhúng -> XÓA đoạn cũ của nguồn đó
rồi nạp đoạn mới (xóa-trước-nạp để lần sửa làm bài ngắn đi không để sót đoạn thừa).

Không tự bắt lỗi nuốt gọn ở đây: gọi từ hook thì hook chịu trách nhiệm không làm vỡ nghiệp vụ;
gọi từ endpoint reindex thì để lỗi nổi lên cho người bấm thấy.
"""
from sqlalchemy.orm import Session

from app.modules.faq.model import Faq
from app.modules.help_center.model import HelpArticle

from .chunker import chunk_text
from .embedder import Embedder, get_embedder
from .store import VectorStore, get_store, point_id

# Nhãn nguồn dùng trong payload + để xóa theo nguồn. Trùng tên với entity phân quyền cho dễ lần.
SRC_HELP = "help_article"
SRC_FAQ = "faq"


def _points_for(source: str, source_id: int, title: str, url: str, body: str,
                embedder: Embedder) -> list[dict]:
    """Cắt `body` thành đoạn, nhúng, gói thành point sẵn sàng upsert. Body rỗng -> []."""
    chunks = chunk_text(body)
    if not chunks:
        return []
    vectors = embedder.embed(chunks, is_query=False)
    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append({
            "id": point_id(source, source_id, idx),
            "vector": vector,
            "payload": {
                "source": source,
                "source_id": source_id,
                "title": title,
                "url": url,
                "chunk_index": idx,
                "text": chunk,
                "is_active": True,
            },
        })
    return points


def _index_help_article(db: Session, article_id: int, embedder: Embedder, store: VectorStore) -> int:
    article = db.get(HelpArticle, article_id)
    store.delete_source(SRC_HELP, article_id)
    if not article:
        return 0
    # Gộp tiêu đề + tóm tắt + nội dung: câu hỏi của người dùng hay khớp TIÊU ĐỀ, nên nhồi
    # tiêu đề vào thân đoạn để nó cũng nằm trong vector.
    parts = [article.title or ""]
    if article.summary:
        parts.append(article.summary)
    parts.append(article.content or "")
    body = "\n".join(p for p in parts if p)
    points = _points_for(SRC_HELP, article_id, article.title or "",
                         f"/articles/{article_id}", body, embedder)
    store.upsert(points)
    return len(points)


def _index_faq(db: Session, faq_id: int, embedder: Embedder, store: VectorStore) -> int:
    faq = db.get(Faq, faq_id)
    store.delete_source(SRC_FAQ, faq_id)
    if not faq:
        return 0
    body = f"{faq.question or ''}\n{faq.answer or ''}"
    points = _points_for(SRC_FAQ, faq_id, faq.question or "", "/faq", body, embedder)
    store.upsert(points)
    return len(points)


def reindex_source(db: Session, source: str, source_id: int) -> int:
    """Nạp lại MỘT bản ghi. Trả số đoạn đã nạp. Nguồn lạ -> bỏ qua (0)."""
    embedder = get_embedder()
    store = get_store()
    store.ensure_collection()
    if source == SRC_HELP:
        return _index_help_article(db, source_id, embedder, store)
    if source == SRC_FAQ:
        return _index_faq(db, source_id, embedder, store)
    return 0


def remove_source(source: str, source_id: int) -> None:
    """Xóa mọi đoạn của một bản ghi đã bị xóa. Không đụng DB."""
    get_store().delete_source(source, source_id)


def all_source_refs(db: Session) -> list[tuple[str, int]]:
    """Danh sách (nguồn, id) của MỌI bài HDSD + câu FAQ — để rải ra nạp từng cái."""
    refs: list[tuple[str, int]] = [(SRC_HELP, r[0]) for r in db.query(HelpArticle.id).all()]
    refs += [(SRC_FAQ, r[0]) for r in db.query(Faq.id).all()]
    return refs


def missing_source_refs(db: Session) -> list[tuple[str, int]]:
    """Danh sách (nguồn, id) CÓ dưới DB mà CHƯA có đoạn nào trong kho vector.

    Vì sao cần: hook nạp chỉ mục bắn từ *service* Trung tâm HDSD, còn script seed ghi thẳng
    ORM — bài do seed dựng ra không bao giờ vào kho (bao-CR-450 phát hiện 32/87 bài hụt).
    Nạp bù chỉ chỗ thiếu rẻ hơn dựng lại toàn bộ rất nhiều: nhúng là lời gọi mạng có trần
    request/phút, dựng lại cả kho chỉ để thêm hai bài là cách chắc chắn nhất để ăn 429.

    Lưu ý. Bài có thân RỖNG cắt ra 0 đoạn nên không bao giờ nằm trong kho, tức là lần nạp bù
    nào cũng thấy nó "thiếu". Vô hại: `_points_for` thấy 0 đoạn là về ngay, không gọi nhúng.
    """
    indexed = get_store().source_refs()
    return [ref for ref in all_source_refs(db) if ref not in indexed]


def index_status(db: Session) -> dict:
    """Đối chiếu DB với kho vector, trả số liệu cho màn Cấu hình hệ thống.

    `orphans` = đoạn còn trong kho mà bản ghi dưới DB đã bị xóa. Đếm ra để người quản biết,
    nhưng KHÔNG tự dọn ở đây — dọn là việc xóa dữ liệu, phải có người bấm.
    """
    all_refs = all_source_refs(db)
    indexed = get_store().source_refs()
    in_db = set(all_refs)
    missing = [ref for ref in all_refs if ref not in indexed]
    return {
        "help_total": sum(1 for s, _ in all_refs if s == SRC_HELP),
        "faq_total": sum(1 for s, _ in all_refs if s == SRC_FAQ),
        "help_indexed": sum(1 for s, i in all_refs if s == SRC_HELP and (s, i) in indexed),
        "faq_indexed": sum(1 for s, i in all_refs if s == SRC_FAQ and (s, i) in indexed),
        "missing": len(missing),
        "missing_help": sum(1 for s, _ in missing if s == SRC_HELP),
        "missing_faq": sum(1 for s, _ in missing if s == SRC_FAQ),
        "orphans": sum(1 for ref in indexed if ref not in in_db),
    }


def rebuild_all(db: Session) -> dict:
    """Dựng lại toàn bộ chỉ mục từ đầu — dùng khi mới bật RAG hoặc đổi model nhúng.

    Không xóa cả collection; cứ nạp đè từng nguồn (point id tất định nên ghi đè đúng chỗ).
    Trả thống kê để endpoint báo lại cho người bấm.
    """
    embedder = get_embedder()
    store = get_store()
    store.ensure_collection()

    help_ids = [row[0] for row in db.query(HelpArticle.id).all()]
    faq_ids = [row[0] for row in db.query(Faq.id).all()]

    help_chunks = sum(_index_help_article(db, i, embedder, store) for i in help_ids)
    faq_chunks = sum(_index_faq(db, i, embedder, store) for i in faq_ids)

    return {
        "help_articles": len(help_ids),
        "faqs": len(faq_ids),
        "chunks": help_chunks + faq_chunks,
    }
