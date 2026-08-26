"""Tìm ngữ nghĩa trên chỉ mục loại B (HDSD + FAQ) để trợ lý trích dẫn khi tư vấn tự do.

Đây là NÃO của tool `search_docs`: nhúng câu hỏi -> truy vấn Qdrant -> lọc ngưỡng -> gọn kết quả.
Tách khỏi tool để test riêng (cắm embedder + store giả), và để chỗ khác (vd tổng hợp câu trả lời)
tái dùng mà không kéo theo tầng phân quyền của tool.
"""
from .embedder import get_embedder
from .store import get_store

# Điểm cosine dưới ngưỡng này coi như không liên quan — thà trả rỗng ("không có trong tài liệu")
# còn hơn bịa dựa trên đoạn lạc đề. 0.5 là mức thận trọng cho embedding bất đối xứng của Gemini.
MIN_SCORE = 0.5
DEFAULT_LIMIT = 5
MAX_LIMIT = 10


def search_docs(query: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Trả các đoạn liên quan nhất tới `query`, mỗi đoạn gồm text + nguồn + link + điểm.

    Câu hỏi rỗng -> []. Không có gì qua ngưỡng -> [] (tầng trên hiểu là 'không tra được').
    """
    query = (query or "").strip()
    if not query:
        return []
    limit = max(1, min(limit, MAX_LIMIT))

    vector = get_embedder().embed([query], is_query=True)[0]
    hits = get_store().search(vector, limit=limit, only_active=True)

    results = []
    for hit in hits:
        if hit.get("score", 0) < MIN_SCORE:
            continue
        results.append({
            "text": hit.get("text", ""),
            "source": hit.get("source", ""),
            "title": hit.get("title", ""),
            "url": hit.get("url", ""),
            "score": round(float(hit.get("score", 0)), 4),
        })
    return results
