"""Tiện ích tên gọi + đường dẫn dùng chung cho `folder_service`.

Tách khỏi `folder_service.py` để giữ mỗi tệp dưới 200 dòng (rule `code-standards`),
không phải vì các hàm này độc lập về nghiệp vụ — `create_folder`/`update_folder`/
`move_folder` đều gọi thẳng vào đây.
"""
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .folder_constants import FolderStatus
from .folder_model import DocFolder


# ── Gập dấu (so tên anh em không phân biệt hoa/thường/dấu) ──────────────────
def _fold_char(ch: str) -> str:
    if ch in "đĐ":
        return "d"
    base = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
    return (base or ch).lower()


def fold(text: str) -> str:
    return "".join(_fold_char(c) for c in (text or ""))


def ensure_name_unique_among_siblings(db: Session, parent_id: int, name: str, *,
                                      exclude_id: int | None = None) -> None:
    folded = fold(name)
    q = db.query(DocFolder).filter(DocFolder.parent_id == parent_id,
                                   DocFolder.status == int(FolderStatus.ACTIVE))
    if exclude_id:
        q = q.filter(DocFolder.id != exclude_id)
    for sibling in q.all():
        if fold(sibling.name) == folded:
            raise HTTPException(400, f"Thư mục «{name}» đã tồn tại trong cùng cấp")


def branch_ids(db: Session, folder: DocFolder) -> list[int]:
    """Mọi id trong nhánh (cả chính nó), dựa trên `path` — không đệ quy."""
    if not folder.path:
        return [folder.id]
    rows = db.query(DocFolder.id).filter(DocFolder.path.like(f"{folder.path}%")).all()
    return [r[0] for r in rows]
