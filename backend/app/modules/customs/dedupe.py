"""Chống trùng dòng hàng khi nạp GTT02 — bao-CR-541.

Đại ca chốt 01/10/2026: nguồn «xuất ra rồi bỏ vào luôn», người nạp không biết tệp nào chồng
lên tệp nào, nên hệ thống phải tự so. Luật:

  · Mỗi dòng có một MÃ BĂM (`row_hash`, SHA-1 40 ký tự) gói đủ các cột dữ liệu của tệp sau
    chuẩn hóa. Dòng mới có mã đã nằm trong bảng → BỎ QUA («Đã có»); lặp lại một dòng phía
    trên trong cùng tệp → BỎ QUA («Trùng trong tệp»). Chỉ dòng thật sự mới được chèn.
  · KHÔNG ghi đè, KHÔNG thay theo khoảng ngày nữa. Tệp không có số tờ khai nên không biết chắc
    «dòng này là dòng kia đã sửa giá»: đo trên 18.243 dòng thật có 129 nhóm / 327 dòng trùng
    hết các cột nhận diện mà khác giá hoặc lượng — phần lớn là các lô hàng thật khác nhau. Ghi
    đè theo cột nhận diện là tự xóa dòng thật. Thay vào đó dòng như vậy vẫn THÊM, kèm ghi chú
    «nghi sửa giá» để người nạp rà.

Vì sao băm mà không so thẳng 32 cột trong SQL: MySQL không dựng chỉ mục quá 16 cột, và nhiều
cột được phép trống mà `NULL = NULL` trong SQL không bao giờ đúng — hai dòng giống hệt nhau
cùng trống một ô sẽ bị coi là khác. Băm sau chuẩn hóa thì ô trống, hoa thường, khoảng trắng
đều đã về một dạng.

⚠️ **Mã phải tính ra Y HỆT từ dòng trong tệp và từ dòng đã lưu.** Vì vậy khóa dùng dạng ĐÃ
LƯU: doanh nghiệp nhập khẩu quy về mã số thuế (DB chỉ giữ một tên cho mỗi mã số thuế), đối tác
quy về khóa tên chuẩn hóa (`CustomsParty.dedupe_key`), số làm tròn đúng số chữ số lẻ của cột.
Lệch một trong ba thứ đó là cùng một dòng mà hai mã khác nhau — chống trùng thủng im lặng.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import update
from sqlalchemy.orm import Session

from .constants import COLUMNS, DECIMAL_KEYS, INSERT_CHUNK
from .model import CustomsLine, CustomsParty
from .reader import hash_name, normalize_text

#  Cột của tệp đi THẲNG vào khóa; ba cột doanh nghiệp / đối tác đi qua khóa đối tượng.
_PARTY_COLUMNS = frozenset({"importer_tax_code", "importer_name", "partner_name"})
HASH_FIELDS: tuple[str, ...] = tuple(k for k, _ in COLUMNS if k not in _PARTY_COLUMNS)
#  Cột NHẬN DIỆN: trùng hết mấy cột này mà khác giá/lượng thì nghi là nguồn sửa số liệu.
IDENTITY_FIELDS: tuple[str, ...] = ("reg_date", "office_code", "hs_code", "line_no", "product_name")

_NULL = "\x00"
_SEP = "\x1f"
_SCALES: dict[str, int] = {k: CustomsLine.__table__.c[k].type.scale for k in DECIMAL_KEYS}


def canonical_value(key: str, value) -> str:
    """Một ô → chuỗi chuẩn để băm. Ô trống (None) khác hẳn chuỗi rỗng và số 0."""
    if value is None:
        return _NULL
    if key in _SCALES:
        step = Decimal(1).scaleb(-_SCALES[key])
        return format(Decimal(str(value)).quantize(step, rounding=ROUND_HALF_UP), "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(int(value))
    return normalize_text(value)


def _digest(parts: list[str]) -> str:
    return hashlib.sha1(_SEP.join(parts).encode("utf-8")).hexdigest()


def compute_row_hash(values: dict, importer_key: str, partner_key: str) -> str:
    """Mã băm đủ các cột dữ liệu — `values` là dòng của tệp HOẶC dòng đã lưu (cùng tên khóa)."""
    return _digest([importer_key, partner_key] + [canonical_value(k, values.get(k)) for k in HASH_FIELDS])


def compute_identity(values: dict, importer_key: str, partner_key: str) -> str:
    """Mã của các cột nhận diện — chỉ để phát hiện «nghi sửa giá», KHÔNG dùng để bỏ qua dòng."""
    return _digest([importer_key, partner_key] + [canonical_value(k, values.get(k)) for k in IDENTITY_FIELDS])


def file_party_keys(row: dict) -> tuple[str, str]:
    """(khóa doanh nghiệp nhập khẩu, khóa đối tác) của một dòng trong tệp — khớp `CustomsParty.dedupe_key`."""
    partner = row.get("partner_name") or ""
    return row.get("importer_tax_code") or "", hash_name(partner) if partner else ""


@dataclass
class ExistingIndex:
    """Mã của các dòng ĐÃ LƯU trong khoảng ngày của tệp → lô chứa nó."""
    by_hash: dict[str, int] = field(default_factory=dict)
    by_identity: dict[str, int] = field(default_factory=dict)


def _party_keys(db: Session, ids: set[int]) -> dict[int, str]:
    out: dict[int, str] = {}
    wanted = [i for i in ids if i]
    for i in range(0, len(wanted), 1000):
        for pid, key in db.query(CustomsParty.id, CustomsParty.dedupe_key).filter(
                CustomsParty.id.in_(wanted[i:i + 1000])):
            out[pid] = key or ""
    return out


def _stored_values(line: CustomsLine) -> dict:
    return {k: getattr(line, k) for k in HASH_FIELDS}


def load_existing(db: Session, date_from, date_to, exclude_batch_id: int = 0) -> ExistingIndex:
    """Đọc mã của mọi dòng đã lưu trong [date_from, date_to]; dòng cũ chưa có mã thì tính và
    ghi luôn (dữ liệu nạp trước bao-CR-541 tự lành dần, không cần chờ script)."""
    index = ExistingIndex()
    if date_from is None:
        return index
    lines = (db.query(CustomsLine)
             .filter(CustomsLine.reg_date >= date_from, CustomsLine.reg_date <= date_to,
                     CustomsLine.batch_id != exclude_batch_id)
             .all())
    parties = _party_keys(db, {x.importer_id for x in lines} | {x.partner_id for x in lines})
    healed = []
    for x in lines:
        imp, par = parties.get(x.importer_id, ""), parties.get(x.partner_id, "")
        values = _stored_values(x)
        row_hash = x.row_hash or compute_row_hash(values, imp, par)
        if not x.row_hash:
            healed.append({"id": x.id, "row_hash": row_hash})
        index.by_hash.setdefault(row_hash, x.batch_id)
        index.by_identity.setdefault(compute_identity(values, imp, par), x.batch_id)
    for i in range(0, len(healed), INSERT_CHUNK):
        db.execute(update(CustomsLine), healed[i:i + INSERT_CHUNK])
    #  Đọc xong thì bỏ khỏi phiên — vài chục nghìn đối tượng ORM ngồi lại tới lúc commit là phí bộ nhớ.
    for x in lines:
        db.expunge(x)
    return index


def stored_hashes(db: Session, lines: list[CustomsLine]) -> dict[int, str]:
    """bao-CR-608 — mã băm HIỆN TẠI của các dòng đã lưu (dòng cũ chưa có mã thì tính), để biết dòng
    trong tệp có cột «ID» có thật sự đổi gì so với dòng nó trỏ tới không."""
    parties = _party_keys(db, {x.importer_id for x in lines} | {x.partner_id for x in lines})
    return {x.id: x.row_hash or compute_row_hash(_stored_values(x), parties.get(x.importer_id, ""),
                                                 parties.get(x.partner_id, "")) for x in lines}


def stamp_rows(rows: list[dict]) -> list[str]:
    """Gắn `row_hash` vào từng dòng của tệp (cột thật của bảng); → mã nhận diện cùng thứ tự."""
    identities = []
    for r in rows:
        imp, par = file_party_keys(r)
        r["row_hash"] = compute_row_hash(r, imp, par)
        identities.append(compute_identity(r, imp, par))
    return identities


def backfill_hashes(db: Session, chunk: int = 5000) -> int:
    """Tính mã cho MỌI dòng còn trống (script một lần sau migration). → số dòng đã ghi."""
    done = 0
    last_id = 0
    while True:
        lines = (db.query(CustomsLine).filter(CustomsLine.id > last_id, CustomsLine.row_hash == "")
                 .order_by(CustomsLine.id).limit(chunk).all())
        if not lines:
            return done
        parties = _party_keys(db, {x.importer_id for x in lines} | {x.partner_id for x in lines})
        payload = [{"id": x.id, "row_hash": compute_row_hash(
            _stored_values(x), parties.get(x.importer_id, ""), parties.get(x.partner_id, ""))} for x in lines]
        last_id = lines[-1].id
        db.execute(update(CustomsLine), payload)
        db.commit()
        done += len(payload)
        for x in lines:
            db.expunge(x)


def find_surplus_ids(db: Session) -> tuple[int, list[int]]:
    """Dòng THỪA theo mã băm: mỗi nhóm cùng mã giữ dòng id nhỏ nhất. → (số nhóm, id cần xóa)."""
    groups: dict[str, list[int]] = {}
    for line_id, row_hash in db.query(CustomsLine.id, CustomsLine.row_hash).filter(CustomsLine.row_hash != ""):
        groups.setdefault(row_hash, []).append(line_id)
    dup_groups = [sorted(ids) for ids in groups.values() if len(ids) > 1]
    return len(dup_groups), [i for ids in dup_groups for i in ids[1:]]
