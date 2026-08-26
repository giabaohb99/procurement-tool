"""Lớp nhúng vector (embedding) — che nhà cung cấp sau một giao diện chung.

Hiện dùng Gemini API (REST bằng `requests`, cùng khuôn với provider chat, KHÔNG kéo thêm SDK).
Chọn API thay vì model local vì VPS đang chật RAM; nội dung loại B (HDSD/FAQ) là công khai nên
gửi đi nhúng không phát sinh rủi ro mới. Sau này muốn giữ trong nhà (Văn thư nhạy cảm) chỉ cần
thêm một lớp `LocalEmbedder` và đổi `get_embedder()`.

⚠ Đổi model nhúng => vector cũ KHÔNG so được với vector mới -> PHẢI reindex toàn bộ.
Truy vấn và tài liệu phải nhúng bằng CÙNG model, khác `task_type` (QUERY vs DOCUMENT).
"""
from typing import Protocol, runtime_checkable

import requests

from app.core.config import settings

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"
_TIMEOUT = 60
# Gemini nhận tối đa ~100 nội dung mỗi lượt batch; cắt nhỏ cho chắc.
_BATCH = 100


class EmbedError(RuntimeError):
    """Lỗi khi gọi dịch vụ nhúng — tách riêng để tầng trên nuốt gọn, không lẫn lỗi khác."""


@runtime_checkable
class Embedder(Protocol):
    """Giao diện nhúng: biến danh sách văn bản thành danh sách vector cùng số chiều `dim`."""

    dim: int

    def embed(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        ...


class GeminiEmbedder:
    """Bản hiện thực gọi Gemini embedding API."""

    def __init__(self, model: str, api_key: str, dim: int) -> None:
        self._model = model
        self._api_key = api_key
        self.dim = dim

    def is_configured(self) -> bool:
        return bool(self._api_key)

    def _request_body(self, texts: list[str], task_type: str) -> dict:
        model_ref = f"models/{self._model}"
        return {
            "requests": [
                {
                    "model": model_ref,
                    "content": {"parts": [{"text": t}]},
                    "taskType": task_type,
                    "outputDimensionality": self.dim,
                }
                for t in texts
            ]
        }

    def _post(self, texts: list[str], task_type: str) -> list[list[float]]:
        url = _BASE_URL.format(model=self._model)
        headers = {"content-type": "application/json", "x-goog-api-key": self._api_key}
        try:
            resp = requests.post(url, json=self._request_body(texts, task_type),
                                 headers=headers, timeout=_TIMEOUT)
        except requests.RequestException as e:
            raise EmbedError(f"Lỗi gọi Gemini embedding: {e}") from e
        if resp.status_code != 200:
            raise EmbedError(f"Gemini embedding lỗi {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return [item.get("values", []) for item in data.get("embeddings", [])]

    def embed(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        if not self.is_configured():
            raise EmbedError("Chưa cấu hình GEMINI_API_KEY cho nhúng vector")
        if not texts:
            return []
        # Câu hỏi dùng RETRIEVAL_QUERY, tài liệu dùng RETRIEVAL_DOCUMENT — bất đối xứng này giúp
        # khớp câu hỏi ngắn với đoạn văn dài tốt hơn.
        task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
        out: list[list[float]] = []
        for start in range(0, len(texts), _BATCH):
            out.extend(self._post(texts[start:start + _BATCH], task_type))
        return out


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Bản nhúng dùng chung (dựng một lần theo cấu hình). Đổi cấu hình phải restart tiến trình."""
    global _embedder
    if _embedder is None:
        _embedder = GeminiEmbedder(
            model=settings.AI_EMBED_MODEL,
            api_key=settings.GEMINI_API_KEY,
            dim=settings.AI_EMBED_DIM,
        )
    return _embedder


def set_embedder(embedder: Embedder | None) -> None:
    """Chỉ dùng cho KIỂM THỬ: cắm một bản nhúng giả để không gọi mạng."""
    global _embedder
    _embedder = embedder
