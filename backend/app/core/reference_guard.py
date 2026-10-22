"""CHỐT XÓA DANH MỤC — đợt 3 xóa mềm (ai-CR-189, đại ca chốt 13/10/2026): danh mục đang được chứng từ / cấu hình tham
chiếu thì KHÔNG xóa, chỉ cho *ngưng dùng*; chưa ai dùng thì vẫn xóa được (xem `doc/erp/nen-tang/20-ra-soat-xoa-cung.md` §4).

Một sổ đăng ký chung thay vì mỗi phân hệ tự viết một `count_references` (NCC / sản phẩm đã có ở ai-CR-169 — giữ, có thể
dời về đây dần): mỗi danh mục khai danh sách chỗ tham chiếu `(Model, cột, nhãn)`; `ensure_deletable` đếm hết, còn dòng nào
thì ném 400 cùng một câu cho mọi danh mục. `core/crud.make_crud_router` tự gọi theo `entity` nên danh mục CRUD chung chỉ
cần ĐĂNG KÝ, không phải viết `before_delete`.

Đếm KHÔNG lọc phạm vi (cố ý): bản ghi đã xóa mềm vẫn tính là còn dùng — dữ liệu còn trong DB, chặn an toàn hơn.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class Reference:
    """Một chỗ tham chiếu tới danh mục: `model.column == giá trị khóa của dòng danh mục` (+ điều kiện thêm nếu cần)."""

    model: type
    column: str
    label: str                                  # tiếng Việt, số nhiều: «đơn mua hàng», «nhân sự»
    key_attr: str = "id"                        # thuộc tính của dòng danh mục dùng làm khóa (id / code)
    extra: Callable[[object], list] | None = None   # (model) -> [điều kiện SQLAlchemy thêm], vd party_type == "supplier"


_REGISTRY: dict[str, list[Reference]] = {}
_LABELS: dict[str, str] = {}


def register(entity: str, label: str, refs: list[Reference]) -> None:
    """Khai các chỗ tham chiếu của một danh mục (`entity` = tên entity phân quyền / tên dùng ở `make_crud_router`).
    Gọi nhiều lần thì NỐI thêm (phân hệ khác có thể khai thêm chỗ tham chiếu của mình)."""
    _REGISTRY.setdefault(entity, []).extend(refs)
    _LABELS.setdefault(entity, label)


def registered(entity: str) -> bool:
    return entity in _REGISTRY


def count_references(db: Session, entity: str, obj) -> list[tuple[str, int]]:
    """[(nhãn, số dòng)] các chỗ còn trỏ tới `obj`; rỗng = xóa được."""
    out: list[tuple[str, int]] = []
    for ref in _REGISTRY.get(entity, []):
        value = getattr(obj, ref.key_attr, None)
        if value in (None, "", 0):
            continue
        col = getattr(ref.model, ref.column)
        q = db.query(ref.model).filter(col == value)
        if ref.extra is not None:
            q = q.filter(*ref.extra(ref.model))
        n = q.count()
        if n:
            out.append((ref.label, n))
    return out


def deletable_error(entity: str, obj, refs: list[tuple[str, int]]) -> str:
    label = _LABELS.get(entity, "danh mục")
    #  ai-CR-190/191: tài khoản không có code / name → email; xe → biển số; nhân sự → họ tên; cuối cùng mới tới id.
    name = None
    for attr in ("code", "name", "full_name", "email", "license_plate", "plate", "title"):
        if getattr(obj, attr, None):
            name = getattr(obj, attr)
            break
    name = name or getattr(obj, "id", "")
    total = sum(n for _, n in refs)
    detail = ", ".join(f"{n} {lbl}" for lbl, n in refs)
    return (f"{label} «{name}» đang được dùng ở {total} chỗ ({detail}), chỉ có thể ngưng dùng "
            f"(bỏ tick «Đang dùng») chứ không xóa được.")


def ensure_deletable(db: Session, entity: str, obj) -> None:
    """Còn chỗ tham chiếu thì 400 — cùng một câu cho mọi danh mục. Chưa đăng ký thì không chặn (hành vi cũ)."""
    if not registered(entity):
        return
    refs = count_references(db, entity, obj)
    if refs:
        raise HTTPException(400, deletable_error(entity, obj, refs))
