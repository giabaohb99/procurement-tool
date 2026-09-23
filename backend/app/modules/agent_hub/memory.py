"""Trí nhớ của bot quản lý — tầng 1: kho tài liệu của chính dự án.

Đây mới là thứ làm con bot quản lý có giá trị. Tóm tắt suông thì không cần AI; cái
đáng tiền là nó tra được *"việc này giống bao-CR-388, hồi đó chốt là không tự gán"*.

Dùng lại nguyên tầng RAG của Trợ lý AI (`assistant/rag/`) — cắt đoạn, nhúng vector,
kho Qdrant — nhưng ở một **collection riêng** và bằng **khóa Gemini riêng**. Hai
corpus khác nhau: bên kia là HDSD cho người dùng cuối, bên này là nhật ký kỹ thuật
nội bộ. Trộn chung thì người dùng hỏi trợ lý một câu nghiệp vụ lại nhận về một đoạn
nhật ký deploy.

Ba tầng trí nhớ ở §6 bản thiết kế: tầng 1 ở tệp này, tầng 2 (task cũ) và tầng 3
(dữ liệu hệ thống) lấy thẳng từ DB trong `manager.py`.
"""
import logging
import time
import uuid
from pathlib import Path

from app.core.config import settings
from app.modules.assistant.rag.chunker import chunk_text
from app.modules.assistant.rag.embedder import EmbedError, GeminiEmbedder
from app.modules.assistant.rag.store import VectorStore

log = logging.getLogger("app.agent_hub.memory")

COLLECTION = "agent_docs"
_NS = uuid.UUID("3f2504e0-4f89-11d3-9a0c-0305e82c3301")

#  Nạp những tệp NÓI VỀ CÁCH DỰ ÁN NÀY ĐƯỢC LÀM RA, không nạp mã nguồn.
#  Mã nguồn thì bot code (bậc 2) đọc thẳng trong worktree — nhúng cả cây mã vào
#  vector vừa tốn vừa trả ra kết quả tệ hơn là để nó tự `grep`.
#  ⚠️ `doc/erp/` (10 MB) CỐ Ý đứng ngoài: phần lớn là kế hoạch dời màn đã xong, nạp
#  vào chỉ làm loãng kết quả tra. Thêm sau nếu thấy bot thiếu ngữ cảnh thật.
INDEX_GLOBS = (
    "CLAUDE.md",
    "doc/tai-lieu-ky-thuat/*.md",
    "doc/tai-lieu-chuc-nang/*.md",
    "doc/agent-hub/*.md",
    ".claude/rules/*.md",
)

#  Trần an toàn: một tệp phình quá cỡ này thì bỏ qua và ghi log, đừng nhúng 40 MB
#  vào Qdrant rồi mới phát hiện. `change-log.md` hiện ~1,3 MB nên trần 4 MB là rộng.
MAX_FILE_BYTES = 4 * 1024 * 1024
#  Số đoạn đẩy lên Qdrant mỗi lượt. Khớp trần batch của API nhúng Gemini.
UPSERT_BATCH = 100


def find_doc_root() -> Path:
    """Thư mục chứa `doc/`. Trong container là `/app` (nhờ mount), trên máy thật là
    gốc repo.

    Hai chỗ chạy khác nhau nên dò chứ không viết cứng: `celery-worker` mount
    `./backend` thành `/app` và `./doc` thành `/app/doc`; còn chạy pytest trên máy
    thì `doc/` nằm trên một cấp so với `backend/`.
    """
    here = Path(__file__).resolve()
    #  .../backend/app/modules/agent_hub/memory.py -> parents[3] = backend (hoặc /app)
    for candidate in (here.parents[3], here.parents[4]):
        if (candidate / "doc").is_dir():
            return candidate
    return here.parents[3]


def _get_embedder() -> GeminiEmbedder:
    """Bản nhúng RIÊNG của bot — khóa riêng (QĐ-AI-7), không dùng `get_embedder()`
    dùng chung vì hàm đó ghim `settings.GEMINI_API_KEY` của Trợ lý AI."""
    return GeminiEmbedder(
        model=settings.AI_EMBED_MODEL,
        api_key=settings.AGENT_GEMINI_API_KEY,
        dim=settings.AI_EMBED_DIM,
    )


def _get_store() -> VectorStore:
    return VectorStore(url=settings.QDRANT_URL, dim=settings.AI_EMBED_DIM,
                       collection=COLLECTION)


def is_configured() -> bool:
    return bool(settings.AGENT_GEMINI_API_KEY)


def collect_files() -> list[Path]:
    """Danh sách tệp sẽ nạp, đã sắp cho ổn định giữa các lần chạy."""
    root = find_doc_root()
    found: list[Path] = []
    for pattern in INDEX_GLOBS:
        found.extend(p for p in root.glob(pattern) if p.is_file())
    #  ai-CR-018: `doc/` giờ là thư mục ở máy đại ca (nhánh erp-v2), nơi KHÔNG có `doc/agent-hub/`
    #  — bộ tài liệu của bot nằm trên nhánh riêng, mount ở chỗ của sổ quyết định. Lấy từ đó.
    if not (root / "doc" / "agent-hub").is_dir():
        extra = Path(settings.AGENT_PLAYBOOK_PATH).parent
        if extra.is_dir():
            found.extend(p for p in extra.glob("*.md") if p.is_file())
    #  Bỏ trùng (một tệp có thể khớp hai glob) rồi sắp theo đường dẫn.
    return sorted(set(found))


def rel_path(path: Path, root: Path) -> str:
    """Đường dẫn ghi vào kho, tính từ gốc repo. Tệp tài liệu bot mượn chỗ mount khác thì ghi
    như thể nằm ở `doc/agent-hub/` — để bot quản lý trích đúng đường dẫn trong repo."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return f"doc/agent-hub/{path.name}"


def drop_stale(store: VectorStore, run_id: int) -> None:
    """Xóa mọi đoạn KHÔNG mang dấu của lượt nạp vừa rồi.

    Dọn theo dấu lượt chạy chứ không theo danh sách tệp, vì có HAI thứ thành rác chứ
    không phải một: tệp bị xóa khỏi repo, và cái đuôi của tệp bị NGẮN ĐI. `change-log.md`
    rút từ 1654 xuống 1600 đoạn thì 54 đoạn cuối vẫn mang đúng `path` đó, lọc theo tệp
    không thấy chúng, và bot trích dẫn một câu đã bị xóa khỏi tài liệu.

    Chỉ gọi sau khi một lượt nạp đã chạy TRỌN VẸN — gọi giữa chừng là xóa sạch phần
    chưa kịp nạp lại.
    """
    from qdrant_client.http import models as qm

    store.client.delete(
        collection_name=COLLECTION,
        points_selector=qm.FilterSelector(filter=qm.Filter(
            must_not=[qm.FieldCondition(key="run", match=qm.MatchValue(value=run_id))],
        )),
        wait=True,
    )


def reindex() -> dict:
    """Cắt đoạn, nhúng, nạp toàn bộ tài liệu lên Qdrant, rồi dọn đoạn của tệp đã xóa.

    Nạp ĐÈ chứ không xóa kho trước. Corpus hiện ~4000 đoạn = ~41 lượt gọi API nhúng
    nối nhau; hạn mức Gemini 429 ở lượt thứ 30 là chuyện bình thường. Nếu xóa kho
    trước thì lần hỏng đó để lại một kho đầy 3/4, mà `recall()` cố ý không ném lỗi —
    tức là bot vẫn tra, vẫn trả lời, chỉ là thiếu mất một phần tài liệu và KHÔNG AI
    THẤY. Nạp đè thì id điểm tất định (`uuid5` theo `đường-dẫn:số-đoạn`) nên chạy lại
    chỉ vá vào chỗ thiếu.

    Đổi lại phải tự dọn đoạn của tệp đã xóa khỏi repo — `drop_stale()` ở cuối, chỉ
    chạy khi lượt nạp đi hết.

    Trả `{"files", "chunks", "skipped"}`.
    """
    if not is_configured():
        raise EmbedError("Chưa cấu hình AGENT_GEMINI_API_KEY")

    embedder = _get_embedder()
    store = _get_store()
    store.ensure_collection()

    root = find_doc_root()
    run_id = int(time.time())
    total_chunks = 0
    indexed = 0
    skipped: list[str] = []
    buffer: list[tuple[str, str, str, int]] = []  # (id, text, rel_path, chunk_index)

    def flush() -> int:
        if not buffer:
            return 0
        vectors = embedder.embed([b[1] for b in buffer])
        points = [
            {
                "id": pid,
                "vector": vec,
                "payload": {
                    "source": "repo_doc",
                    "path": rel,
                    "title": Path(rel).name,
                    "chunk_index": idx,
                    "text": text,
                    "is_active": True,
                    #  Dấu lượt nạp — `drop_stale()` dọn theo cột này.
                    "run": run_id,
                },
            }
            for (pid, text, rel, idx), vec in zip(buffer, vectors, strict=False)
        ]
        store.upsert(points)
        n = len(points)
        buffer.clear()
        return n

    reused = 0
    for path in collect_files():
        rel = rel_path(path, root)
        if path.stat().st_size > MAX_FILE_BYTES:
            skipped.append(rel)
            log.warning("agent_hub: bỏ qua %s vì quá %d byte", rel, MAX_FILE_BYTES)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = chunk_text(text)
        if not chunks:
            continue
        indexed += 1
        #  ai-CR-022: tệp không đổi thì GIỮ vector cũ, chỉ đóng dấu lượt mới. Nạp đè cả kho mỗi lần
        #  là ~1,2 triệu token nhúng (~5 nghìn đồng) cho vài dòng sửa — khoản tốn nhất của bot.
        if _unchanged(store, rel, chunks):
            _retag(store, rel, run_id)
            reused += 1
            continue
        for i, chunk in enumerate(chunks):
            buffer.append((str(uuid.uuid5(_NS, f"{rel}:{i}")), chunk, rel, i))
            if len(buffer) >= UPSERT_BATCH:
                total_chunks += flush()

    total_chunks += flush()
    #  Tới được đây nghĩa là đã nạp trọn, giờ mới được phép dọn.
    drop_stale(store, run_id)
    log.info("agent_hub: nạp %d tệp (%d giữ nguyên), nhúng %d đoạn vào %s", indexed, reused,
             total_chunks, COLLECTION)
    return {"files": indexed, "reused": reused, "chunks": total_chunks, "skipped": skipped}


def _path_filter(rel: str):
    from qdrant_client.http import models as qm

    return qm.Filter(must=[qm.FieldCondition(key="path", match=qm.MatchValue(value=rel))])


def _unchanged(store: VectorStore, rel: str, chunks: list[str]) -> bool:
    """Các đoạn đang nằm trong kho của tệp này có y hệt các đoạn vừa cắt không. So bằng chữ,
    không cần cột băm — nên cả kho nạp từ trước ai-CR-022 cũng dùng lại được, khỏi nhúng lại."""
    points, _ = store.client.scroll(
        collection_name=COLLECTION, scroll_filter=_path_filter(rel),
        limit=len(chunks) + 50, with_payload=["chunk_index", "text"], with_vectors=False,
    )
    stored = {int((p.payload or {}).get("chunk_index", -1)): (p.payload or {}).get("text") for p in points}
    return len(stored) == len(chunks) and all(stored.get(i) == c for i, c in enumerate(chunks))


def _retag(store: VectorStore, rel: str, run_id: int) -> None:
    """Đóng dấu lượt mới cho các đoạn giữ nguyên, để `drop_stale()` không xóa nhầm chúng."""
    store.client.set_payload(collection_name=COLLECTION, payload={"run": run_id},
                             points=_path_filter(rel), wait=True)


#  Điểm cosine dưới ngưỡng coi như không liên quan. Thà trả rỗng — bot quản lý viện
#  dẫn một đoạn lạc đề còn tệ hơn là nó nói thẳng "không tra được gì" (luật B4).
MIN_SCORE = 0.5


def recall(query: str, limit: int = 6) -> list[dict]:
    """Tra tài liệu liên quan tới `query`. Trả [{path, title, text, score}].

    KHÔNG BAO GIỜ NÉM LỖI RA NGOÀI. Qdrant chưa dựng, chưa nạp chỉ mục, hay hết hạn
    mức nhúng — tất cả đều chỉ nghĩa là bot làm việc mà không có trí nhớ, và một bản
    tóm tắt không trích dẫn được vẫn tốt hơn một task chết vì kho vector.
    """
    query = (query or "").strip()
    if not query or not is_configured():
        return []
    try:
        vector = _get_embedder().embed([query], is_query=True)[0]
        hits = _get_store().search(vector, limit=limit, only_active=True)
    except Exception as e:  # noqa: BLE001 - xem docstring
        log.warning("agent_hub: tra trí nhớ hỏng, chạy tiếp không trí nhớ: %s", e)
        return []
    return [
        {
            "path": h.get("path", ""),
            "title": h.get("title", ""),
            "text": h.get("text", ""),
            "score": round(float(h.get("score", 0)), 4),
        }
        for h in hits
        if h.get("score", 0) >= MIN_SCORE
    ]
