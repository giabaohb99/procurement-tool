"""Đọc / ghi THÀNH PHẦN của định mức bao bì (duoc-CR-784, chuẩn hóa 25/11/2026).

Cấu trúc: `tab_packaging_bom` (đầu phiếu) + `tab_packaging_bom_part` (loại `PackagingRole` + mã vật tư, nối bằng `bom_id`).
Mọi dịch vụ tính toán (tác động giá, tổng hợp theo sản phẩm, bảng giá, giá gần nhất, lịch sử theo sản phẩm, công cụ trợ lý) đi qua
đây thay vì tự biết "có năm cột mã" — thêm loại thành phần mới chỉ cần thêm thành viên `PackagingRole`.

SỐ TRUY VẤN CỐ ĐỊNH: `load_bom_rows` nạp đầu phiếu + thành phần bằng MỘT truy vấn (nối trái, gom ở Python); đếm / tra ngược mã
đi thẳng bảng thành phần qua chỉ mục `ix_pbom_part_code`.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.packaging_price_codes import PackagingRole

from .model import PackagingBom, PackagingBomPart, role_field


@dataclass(eq=False)
class BomRow:
    """Một định mức đã nạp vào bộ nhớ: đầu phiếu + `{loại thành phần: mã}` (chỉ loại có mã). Bản nhẹ thay thực thể ORM."""

    hh_code: str
    hh_name: str
    legal_name: str
    carton_qty: int
    codes: dict[int, str] = field(default_factory=dict)

    def code_of(self, role: int) -> str:
        """Mã của loại `role`, chuỗi rỗng nếu định mức không khai loại đó."""
        return self.codes.get(int(role), "")

    def code_set(self) -> set[str]:
        """Mọi mã vật tư có mặt trong định mức (không trùng, không rỗng)."""
        return {c for c in self.codes.values() if c}


def load_bom_rows(db: Session, *, hh_codes: Iterable[str] | None = None, uses_codes: Iterable[str] | None = None) -> list[BomRow]:
    """Định mức xếp theo mã hàng hóa tăng dần, MỘT truy vấn.

    `hh_codes` (không None) giữ các mã hàng hóa đó; `uses_codes` (không None) giữ định mức có dùng ÍT NHẤT MỘT mã vật tư đó —
    vẫn trả đủ thành phần của định mức giữ lại (để tính chi phí). Hai điều kiện ghép bằng VÀ.
    """
    query = (select(PackagingBom.hh_code, PackagingBom.hh_name, PackagingBom.legal_name, PackagingBom.carton_qty,
                    PackagingBomPart.part_type, PackagingBomPart.part_code)
             .select_from(PackagingBom).outerjoin(PackagingBomPart, PackagingBomPart.bom_id == PackagingBom.id))
    if hh_codes is not None:
        query = query.where(PackagingBom.hh_code.in_(list(hh_codes)))
    if uses_codes is not None:
        query = query.where(PackagingBom.id.in_(select(PackagingBomPart.bom_id).where(PackagingBomPart.part_code.in_(list(uses_codes)))))
    #  Chỉ xếp theo cột của đầu phiếu: đi theo chỉ mục `hh_code`, không phải tạo bảng tạm + filesort (đo: 22 ms -> 13 ms / 1.000 định mức).
    rows: list[BomRow] = []
    for hh_code, hh_name, legal_name, carton_qty, part_type, part_code in db.execute(query.order_by(PackagingBom.hh_code)):
        if not rows or rows[-1].hh_code != hh_code:     # hh_code duy nhất nên các dòng của một định mức nằm liền nhau
            rows.append(BomRow(hh_code, hh_name, legal_name, carton_qty))
        if part_type is not None and part_code:
            rows[-1].codes[int(part_type)] = part_code
    return rows


def usage_by_code(db: Session, codes: Iterable[str] | None = None) -> dict[str, int]:
    """`{mã vật tư: số sản phẩm dùng}` — đếm theo định mức riêng biệt (một mã giữ hai vai trò trong cùng sản phẩm chỉ tính một)."""
    query = (select(PackagingBomPart.part_code, func.count(func.distinct(PackagingBomPart.bom_id)))
             .where(PackagingBomPart.part_code != "").group_by(PackagingBomPart.part_code))
    if codes is not None:
        query = query.where(PackagingBomPart.part_code.in_(list(codes)))
    return {code: int(n) for code, n in db.execute(query)}


def component_codes_query():
    """Truy vấn `select` mã vật tư của MỌI định mức (có trùng) — dựng tập mã VTBB `union` với báo giá / sổ giá."""
    return select(PackagingBomPart.part_code).where(PackagingBomPart.part_code != "")


def codes_from_fields(values: Mapping[str, object]) -> dict[int, str]:
    """Trường phẳng của API (`bottle_code`, `cap_code`...) -> `{loại: mã đã bỏ khoảng trắng}`; chỉ lấy loại có mặt trong `values`."""
    return {int(role): str(values[role_field(role)] or "").strip() for role in PackagingRole if role_field(role) in values}


def current_codes(bom: PackagingBom) -> dict[int, str]:
    """`{loại: mã}` hiện có của một thực thể định mức (đọc `bom.parts`)."""
    return {int(p.part_type): p.part_code for p in bom.parts}


def set_bom_codes(bom: PackagingBom, codes: Mapping[int, str]) -> bool:
    """Đồng bộ thành phần của `bom` theo `codes` (chỉ đụng các loại có trong `codes`): mã rỗng = bỏ thành phần, mã mới = thêm / đổi.

    Trả `True` nếu có gì đổi. KHÔNG commit — nơi gọi tự commit cùng giao dịch với đầu phiếu. Loại thành phần lạ (ngoài
    `PackagingRole`) bị từ chối.
    """
    existing = {int(p.part_type): p for p in bom.parts}
    changed = False
    for role, raw in codes.items():
        role = PackagingRole(int(role))                 # ValueError nếu loại không có trong enum
        code = (raw or "").strip()
        part = existing.get(int(role))
        if not code:
            if part is not None:
                bom.parts.remove(part)                  # delete-orphan: ORM xóa dòng
                changed = True
        elif part is not None:
            if part.part_code != code:
                part.part_code = code
                changed = True
        else:
            bom.parts.append(PackagingBomPart(part_type=int(role), part_code=code))
            changed = True
    return changed
