"""Gộp dòng hàng hải quan trùng — bao-CR-699 (đại ca chốt 30/10/2026).

Đo prod 30/10: 371.721 dòng, `row_hash` không trùng, nhưng 37.311 nhóm cùng doanh nghiệp + đối tác + tờ khai (ngày
đăng ký, nơi mở, mã HS, số thứ tự hàng, tên hàng) VÀ cùng giá USD + lượng → ~44.900 dòng thừa, phần lớn nằm ở hai lô
khác nhau (cùng tờ khai nạp hai lần, lần sau có thêm "Nước nhận hàng" / ngày đã vá / số hợp đồng).

Luật gộp (A1 duyệt 30/10):
  · Nhóm = cùng mã khớp (`dedupe.MATCH_FIELDS`, so trên id doanh nghiệp / đối tác đã lưu).
  · Chỉ gộp nhóm KHÔNG XUNG ĐỘT: mọi cột dữ liệu (`dedupe.HASH_FIELDS`) bằng nhau hoặc một bên trống. Nhóm có hai giá
    trị khác nhau cùng có chữ → để nguyên, đếm theo cột cho người rà (`conflict_by_field`).
  · Nhóm có dòng từng bị sửa tay / ghi đè / xóa-dựng lại (có dòng ở `tab_customs_line_change`) → để nguyên: lịch sử và
    hoàn tác lô trỏ đúng id đó. Ngoài bảng này không bảng nào giữ id dòng hải quan (bộ lọc đã lưu lọc theo điều kiện).
  · Giữ dòng CŨ NHẤT (id nhỏ nhất): hoàn tác lô mới — việc hay xảy ra hơn — không làm mất dữ liệu. Ô trống của dòng giữ
    được điền bù từ các dòng bị bỏ, rồi tính lại `row_hash`.
  · Xóa theo lô nhỏ (`CLEANUP_BATCH_SIZE`), mỗi lô một commit. Giữ khóa nạp (`importer._import_lock`) suốt lượt gộp để
    không chạy chồng một lượt nạp tệp.
"""
import hashlib
import logging
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core.logging_policy import CLEANUP_BATCH_SIZE

from .dedupe import (_SEP, HASH_FIELDS, MATCH_FIELDS, _party_keys, canon_values, canonical_value, compute_row_hash,
                     conflict_fields, is_blank)
from .model import CustomsLine, CustomsLineChange

log = logging.getLogger("app.customs.line_merge")

#  Hai cột giá VND lấy từ tệp (bao-CR-603) không nằm trong mã băm nhưng vẫn là dữ liệu: dòng giữ trống thì điền bù.
EXTRA_FILL = ("price_vnd_flat", "price_vnd_line_tax")
GROUP_CHUNK = 500


@dataclass
class MergeResult:
    candidate_groups: int = 0          # nhóm cùng mã khớp có từ hai dòng
    merged_groups: int = 0
    deleted_rows: int = 0
    filled_rows: int = 0               # dòng giữ được điền bù ít nhất một ô
    conflict_groups: int = 0
    conflict_by_field: Counter = field(default_factory=Counter)
    history_groups: int = 0            # bỏ qua vì có lịch sử sửa / ghi đè
    delete_ids: list[int] = field(default_factory=list)

    def as_dict(self, dry_run: bool) -> dict:
        return {"status": "dry_run" if dry_run else "success", "candidate_groups": self.candidate_groups,
                "merged_groups": self.merged_groups,
                ("matched_rows" if dry_run else "deleted_rows"): len(self.delete_ids) if dry_run else self.deleted_rows,
                "filled_rows": self.filled_rows, "conflict_groups": self.conflict_groups,
                "conflict_by_field": dict(self.conflict_by_field.most_common()),
                "history_groups": self.history_groups}


def _match_key(line) -> str:
    """Mã khớp trên dòng ĐÃ LƯU — doanh nghiệp / đối tác so bằng id (cùng khóa chuẩn hóa thì cùng id)."""
    parts = [str(line.importer_id or 0), str(line.partner_id or 0)]
    parts += [canonical_value(k, getattr(line, k)) for k in MATCH_FIELDS]
    return hashlib.sha1(_SEP.join(parts).encode("utf-8")).hexdigest()


def candidate_groups(db: Session) -> list[list[int]]:
    """Mọi nhóm cùng mã khớp có từ hai dòng → danh sách id (tăng dần). Đọc từng phần, chỉ các cột khớp."""
    cols = [CustomsLine.id, CustomsLine.importer_id, CustomsLine.partner_id] + [getattr(CustomsLine, k)
                                                                                for k in MATCH_FIELDS]
    groups: dict[str, list[int]] = {}
    for row in db.query(*cols).order_by(CustomsLine.id).yield_per(5000):
        groups.setdefault(_match_key(row), []).append(int(row.id))
    return [sorted(ids) for ids in groups.values() if len(ids) > 1]


def _changed_ids(db: Session, ids: list[int]) -> set[int]:
    out: set[int] = set()
    for i in range(0, len(ids), 1000):
        out.update(int(x) for (x,) in db.query(CustomsLineChange.line_id)
                   .filter(CustomsLineChange.line_id.in_(ids[i:i + 1000])).distinct())
    return out


def _values(line: CustomsLine) -> dict:
    return {k: getattr(line, k) for k in HASH_FIELDS + EXTRA_FILL}


def _plan_group(lines: list[CustomsLine], result: MergeResult) -> dict | None:
    """Một nhóm (id tăng dần) → bản điền bù cho dòng giữ ({} = không cần điền), hoặc None nếu xung đột."""
    keep = lines[0]
    merged = list(canon_values(_values(keep)))
    fills: dict = {}
    for other in lines[1:]:
        values = _values(other)
        canon = canon_values(values)
        clash = conflict_fields(tuple(merged), canon)
        if clash:
            result.conflict_groups += 1
            result.conflict_by_field.update(clash)
            return None
        for i, k in enumerate(HASH_FIELDS):
            if is_blank(merged[i]) and not is_blank(canon[i]):
                merged[i] = canon[i]
                fills[k] = values[k]
        for k in EXTRA_FILL:
            if getattr(keep, k) is None and k not in fills and values[k] is not None:
                fills[k] = values[k]
    return fills


def plan(db: Session) -> tuple[MergeResult, list[dict]]:
    """Kế hoạch gộp, CHƯA ghi gì: (số đếm + id sẽ xóa, bản điền bù cho dòng giữ)."""
    result = MergeResult()
    groups = candidate_groups(db)
    result.candidate_groups = len(groups)
    updates: list[dict] = []
    for start in range(0, len(groups), GROUP_CHUNK):
        chunk = groups[start:start + GROUP_CHUNK]
        ids = [i for g in chunk for i in g]
        changed = _changed_ids(db, ids)
        by_id = {x.id: x for x in db.query(CustomsLine).filter(CustomsLine.id.in_(ids))}
        parties = _party_keys(db, {x.importer_id for x in by_id.values()} | {x.partner_id for x in by_id.values()})
        for g in chunk:
            if changed.intersection(g):
                result.history_groups += 1
                continue
            lines = [by_id[i] for i in g if i in by_id]
            if len(lines) < 2:
                continue
            fills = _plan_group(lines, result)
            if fills is None:
                continue
            result.merged_groups += 1
            result.delete_ids.extend(x.id for x in lines[1:])
            if fills:
                keep = lines[0]
                values = {**_values(keep), **fills}
                fills["row_hash"] = compute_row_hash(values, parties.get(keep.importer_id, ""),
                                                     parties.get(keep.partner_id, ""))
                updates.append({"id": keep.id, **fills})
        for x in by_id.values():
            db.expunge(x)
    result.filled_rows = len(updates)
    return result, updates


def apply_plan(db: Session, result: MergeResult, updates: list[dict], batch_size: int = CLEANUP_BATCH_SIZE) -> dict:
    """Ghi kế hoạch: điền bù dòng giữ trước, rồi xóa dòng thừa theo lô nhỏ (mỗi lô một commit)."""
    #  Cập nhật theo khóa chính hàng loạt cần mọi bản ghi cùng bộ cột → gom theo bộ cột được điền.
    by_shape: dict[frozenset, list[dict]] = {}
    for u in updates:
        by_shape.setdefault(frozenset(u), []).append(u)
    for rows in by_shape.values():
        for i in range(0, len(rows), batch_size):
            db.execute(update(CustomsLine), rows[i:i + batch_size])
            db.commit()
    for i in range(0, len(result.delete_ids), batch_size):
        part = result.delete_ids[i:i + batch_size]
        db.execute(delete(CustomsLine).where(CustomsLine.id.in_(part)))
        db.commit()
        result.deleted_rows += len(part)
    out = result.as_dict(False)
    log.info("Gộp dòng hải quan trùng: %s", out)
    return out


def merge_duplicates(db: Session, *, dry_run: bool = True) -> dict:
    """Gộp các nhóm trùng. `dry_run=True` chỉ đếm (không ghi gì). Trả số đếm + phân bổ nhóm xung đột theo cột."""
    result, updates = plan(db)
    return result.as_dict(True) if dry_run else apply_plan(db, result, updates)


def run(db: Session, *, dry_run: bool = True) -> dict:
    """Lượt gộp giữ khóa nạp tệp — không chạy chồng một lượt nạp (cả hai cùng đọc / ghi bảng dòng hàng)."""
    from .importer import _import_lock

    with _import_lock(db):
        return merge_duplicates(db, dry_run=dry_run)
