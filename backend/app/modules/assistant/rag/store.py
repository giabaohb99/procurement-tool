"""Kho vector Qdrant — bọc `qdrant-client` sau một giao diện nhỏ, kết nối LƯỜI.

Import module này KHÔNG mở kết nối: `qdrant-client` chỉ nạp khi thật sự dùng, để môi trường
tắt RAG (AI_RAG_ENABLED=false) hoặc lúc chạy test đơn vị không cần Qdrant sống.

Mỗi đoạn (chunk) là một point:
  - id: UUID5 tất định từ (source, source_id, chunk_index) -> ghi đè đúng chỗ khi reindex.
  - payload: source, source_id, title, url, chunk_index, text, is_active.
  - vector: nhúng của đoạn. Đo khoảng cách COSINE (tự chuẩn hóa, khỏi lo độ dài vector).
"""
import uuid

from app.core.config import settings

COLLECTION = "kb_docs"
# Không gian tên cố định để UUID5 tất định giữa các lần chạy.
_NS = uuid.UUID("6f9619ff-8b86-d011-b42d-00cf4fc964ff")


def point_id(source: str, source_id: int, chunk_index: int) -> str:
    return str(uuid.uuid5(_NS, f"{source}:{source_id}:{chunk_index}"))


class VectorStore:
    """Giao tiếp Qdrant tối thiểu: bảo đảm collection, nạp point, xóa theo nguồn, tìm."""

    def __init__(self, url: str, dim: int) -> None:
        self._url = url
        self._dim = dim
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from qdrant_client import QdrantClient  # nạp lười
            self._client = QdrantClient(url=self._url, timeout=30)
        return self._client

    def ensure_collection(self) -> None:
        from qdrant_client.http import models as qm
        if self.client.collection_exists(COLLECTION):
            return
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=self._dim, distance=qm.Distance.COSINE),
        )

    def upsert(self, points: list[dict]) -> None:
        """`points`: list {id, vector, payload}. Không có gì thì thôi."""
        if not points:
            return
        from qdrant_client.http import models as qm
        self.client.upsert(
            collection_name=COLLECTION,
            points=[
                qm.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                for p in points
            ],
        )

    def delete_source(self, source: str, source_id: int) -> None:
        """Xóa mọi đoạn của MỘT bản ghi nguồn (trước khi nạp lại, hoặc khi bản ghi bị xóa)."""
        from qdrant_client.http import models as qm
        self.client.delete(
            collection_name=COLLECTION,
            points_selector=qm.FilterSelector(filter=qm.Filter(must=[
                qm.FieldCondition(key="source", match=qm.MatchValue(value=source)),
                qm.FieldCondition(key="source_id", match=qm.MatchValue(value=source_id)),
            ])),
        )

    def search(self, vector: list[float], limit: int, *, only_active: bool = True) -> list[dict]:
        """Trả list payload kèm `score`, sắp theo độ gần giảm dần."""
        from qdrant_client.http import models as qm
        flt = None
        if only_active:
            flt = qm.Filter(must=[qm.FieldCondition(key="is_active", match=qm.MatchValue(value=True))])
        hits = self.client.query_points(
            collection_name=COLLECTION, query=vector, limit=limit,
            query_filter=flt, with_payload=True,
        ).points
        return [{**(h.payload or {}), "score": h.score} for h in hits]


_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(url=settings.QDRANT_URL, dim=settings.AI_EMBED_DIM)
    return _store


def set_store(store) -> None:
    """Chỉ dùng cho KIỂM THỬ: cắm kho giả để không cần Qdrant sống."""
    global _store
    _store = store
