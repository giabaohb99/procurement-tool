"""Chống trùng dòng hàng khi nạp GTT02 — bao-CR-541.

Đại ca chốt 01/10/2026: nguồn "xuất ra rồi bỏ vào luôn", người nạp không biết tệp nào chồng
lên tệp nào, nên hệ thống phải tự so. Luật:

  · Mỗi dòng có một MÃ BĂM (`row_hash`, SHA-1 40 ký tự) gói đủ các cột dữ liệu của tệp sau
    chuẩn hóa. Dòng mới có mã đã nằm trong bảng → BỎ QUA ("Đã có"); lặp lại một dòng phía
    trên trong cùng tệp → BỎ QUA ("Trùng trong tệp"). Chỉ dòng thật sự mới được chèn.
  · KHÔNG ghi đè, KHÔNG thay theo khoảng ngày nữa. Tệp không có số tờ khai nên không biết chắc
    "dòng này là dòng kia đã sửa giá": đo trên 18.243 dòng thật có 129 nhóm / 327 dòng trùng
    hết các cột nhận diện mà khác giá hoặc lượng — phần lớn là các lô hàng thật khác nhau. Ghi
    đè theo cột nhận diện là tự xóa dòng thật. Thay vào đó dòng như vậy vẫn THÊM, kèm ghi chú
    "nghi sửa giá" để người nạp rà.

Vì sao băm mà không so thẳng 32 cột trong SQL: MySQL không dựng chỉ mục quá 16 cột, và nhiều
cột được phép trống mà `NULL = NULL` trong SQL không bao giờ đúng — hai dòng giống hệt nhau
cùng trống một ô sẽ bị coi là khác. Băm sau chuẩn hóa thì ô trống, hoa thường, khoảng trắng
đều đã về một dạng.

⚠️ **Mã phải tính ra Y HỆT từ dòng trong tệp và từ dòng đã lưu.** Vì vậy khóa dùng dạng ĐÃ
LƯU: doanh nghiệp nhập khẩu quy về mã số thuế (DB chỉ giữ một tên cho mỗi mã số thuế), đối tác
quy về khóa tên chuẩn hóa (`CustomsParty.dedupe_key`), số làm tròn đúng số chữ số lẻ của cột.
Lệch một trong ba thứ đó là cùng một dòng mà hai mã khác nhau — chống trùng thủng im lặng.

bao-CR-733 — bộ nhớ: `load_existing` từng nạp MỌI dòng trong dải ngày của tệp thành đối tượng ORM một lần (tệp 50.000
dòng nạp lại: worker ~1 GB). Nay đọc theo khúc (`EXISTING_CHUNK` dòng, chỉ các cột cần, câu Core) và chỉ GIỮ mã nằm
trong tệp (`FileKeys`) — chỉ mục chỉ được tra bằng mã của dòng trong tệp nên bỏ phần còn lại không đổi kết quả. Các ô
chuẩn hóa (để so xung đột) chỉ tính khi thật cần, không giữ sẵn cho mọi dòng.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, or_, select, update
from sqlalchemy.orm import Session

from .constants import COLUMNS, DECIMAL_KEYS, INSERT_CHUNK
from .model import CustomsLine, CustomsParty
from .reader import hash_name, normalize_text

#  Cột của tệp đi THẲNG vào khóa; ba cột doanh nghiệp / đối tác đi qua khóa đối tượng.
_PARTY_COLUMNS = frozenset({"importer_tax_code", "importer_name", "partner_name"})
HASH_FIELDS: tuple[str, ...] = tuple(k for k, _ in COLUMNS if k not in _PARTY_COLUMNS)
#  Cột NHẬN DIỆN: trùng hết mấy cột này mà khác giá/lượng thì nghi là nguồn sửa số liệu.
IDENTITY_FIELDS: tuple[str, ...] = ("reg_date", "office_code", "hs_code", "line_no", "product_name")
#  bao-CR-699: cột KHỚP — nhận diện + giá + lượng. Hai dòng cùng mã khớp mà KHÔNG xung đột (mọi cột dữ liệu bằng
#  nhau hoặc một bên trống) là MỘT dòng hàng nạp hai lần (đo prod 30/10: ~44.900 dòng thừa, khác nhau chủ yếu ở
#  Nước nhận hàng có / không, ngày đã vá, số hợp đồng) → lúc nạp bỏ qua, việc gộp định kỳ gộp lại.
MATCH_FIELDS: tuple[str, ...] = IDENTITY_FIELDS + ("price_usd", "quantity")

_NULL = "\x00"
_SEP = "\x1f"
_SCALES: dict[str, int] = {k: CustomsLine.__table__.c[k].type.scale for k in DECIMAL_KEYS}
#  Vị trí các cột nhận diện / khớp trong `HASH_FIELDS` — tính ô chuẩn MỘT lần rồi rút ra ba mã.
_IDENTITY_AT = tuple(HASH_FIELDS.index(k) for k in IDENTITY_FIELDS)
_MATCH_AT = tuple(HASH_FIELDS.index(k) for k in MATCH_FIELDS)
#  bao-CR-733: số dòng sẵn có đọc mỗi khúc khi dựng chỉ mục chống trùng (bài kiểm ép nhỏ để phủ nhiều khúc).
EXISTING_CHUNK = 2000


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
    """Mã của các cột nhận diện — chỉ để phát hiện "nghi sửa giá", KHÔNG dùng để bỏ qua dòng."""
    return _digest([importer_key, partner_key] + [canonical_value(k, values.get(k)) for k in IDENTITY_FIELDS])


def compute_match(values: dict, importer_key: str, partner_key: str) -> str:
    """bao-CR-699 — mã của các cột khớp (nhận diện + giá + lượng)."""
    return _digest([importer_key, partner_key] + [canonical_value(k, values.get(k)) for k in MATCH_FIELDS])


def canon_values(values: dict) -> tuple[str, ...]:
    """Các ô dữ liệu (đủ `HASH_FIELDS`) ở dạng chuẩn — để so xung đột giữa hai dòng cùng mã khớp."""
    return tuple(canonical_value(k, values.get(k)) for k in HASH_FIELDS)


def is_blank(canon: str) -> bool:
    return canon in (_NULL, "")


def conflict_fields(a: tuple[str, ...], b: tuple[str, ...]) -> list[str]:
    """Cột mà CẢ HAI dòng đều có chữ / số mà khác nhau. Rỗng = không xung đột (bằng nhau hoặc một bên trống)."""
    return [k for k, x, y in zip(HASH_FIELDS, a, b) if x != y and not is_blank(x) and not is_blank(y)]


def row_keys(values: dict, importer_key: str, partner_key: str) -> tuple[str, str, str, list[str]]:
    """(mã băm, mã nhận diện, mã khớp, các ô chuẩn) — tính ô chuẩn MỘT lần cho cả ba mã; ra đúng như
    `compute_row_hash` / `compute_identity` / `compute_match` (cột nhận diện / khớp đều nằm trong `HASH_FIELDS`)."""
    canon = [canonical_value(k, values.get(k)) for k in HASH_FIELDS]
    head = [importer_key, partner_key]
    return (_digest(head + canon), _digest(head + [canon[i] for i in _IDENTITY_AT]),
            _digest(head + [canon[i] for i in _MATCH_AT]), canon)


def file_party_keys(row: dict) -> tuple[str, str]:
    """(khóa doanh nghiệp nhập khẩu, khóa đối tác) của một dòng trong tệp — khớp `CustomsParty.dedupe_key`."""
    partner = row.get("partner_name") or ""
    return row.get("importer_tax_code") or "", hash_name(partner) if partner else ""


@dataclass
class ExistingIndex:
    """Mã của các dòng ĐÃ LƯU trong khoảng ngày của tệp → lô chứa nó."""
    by_hash: dict[str, int] = field(default_factory=dict)
    by_identity: dict[str, int] = field(default_factory=dict)
    #  bao-CR-699: mã khớp → (lô, các ô chuẩn hóa) của dòng đầu tiên mang mã đó.
    by_match: dict[str, tuple[int, tuple[str, ...]]] = field(default_factory=dict)


@dataclass
class FileKeys:
    """bao-CR-733 — mã của các dòng TRONG TỆP, cùng thứ tự dòng. Chỉ mục dòng sẵn có chỉ được tra bằng mấy mã
    này, nên chỉ giữ mã nằm trong đây: tệp nhỏ nạp vào dải ngày lớn không kéo cả dải vào bộ nhớ."""
    hashes: list[str]
    identities: list[str]
    matches: list[str]


def stamp_file_rows(rows: list[dict]) -> FileKeys:
    """Gắn `row_hash` vào từng dòng của tệp (cột thật của bảng); → ba mã của từng dòng cùng thứ tự `rows`.

    bao-CR-733 gộp `stamp_rows` + `match_rows` cũ (ô chuẩn tính một lần cho cả ba mã) và KHÔNG giữ các ô chuẩn của
    từng dòng nữa (~30 chuỗi mỗi dòng): bước phân loại cần thì tính lại từ chính dòng đó (`canon_values`)."""
    out = FileKeys([], [], [])
    for r in rows:
        r["row_hash"], identity, match, _ = row_keys(r, *file_party_keys(r))
        out.hashes.append(r["row_hash"])
        out.identities.append(identity)
        out.matches.append(match)
    return out


def _party_keys(db: Session, ids: set[int], cache: dict[int, str] | None = None) -> dict[int, str]:
    """id đối tượng → khóa chống trùng. `cache` (bao-CR-733): dùng lại qua nhiều khúc, chỉ tra id chưa có."""
    out: dict[int, str] = cache if cache is not None else {}
    wanted = [i for i in ids if i and i not in out]
    for i in range(0, len(wanted), 1000):
        for pid, key in db.query(CustomsParty.id, CustomsParty.dedupe_key).filter(
                CustomsParty.id.in_(wanted[i:i + 1000])):
            out[pid] = key or ""
    return out


def _stored_values(line: CustomsLine) -> dict:
    return {k: getattr(line, k) for k in HASH_FIELDS}


_EXISTING_COLUMNS = (CustomsLine.id, CustomsLine.batch_id, CustomsLine.row_hash, CustomsLine.importer_id,
                     CustomsLine.partner_id) + tuple(CustomsLine.__table__.c[k] for k in HASH_FIELDS)
_FIRST_VALUE = 5          # cột dữ liệu đầu tiên trong `_EXISTING_COLUMNS`


def load_existing(db: Session, date_from, date_to, exclude_batch_id: int = 0,
                  wanted: FileKeys | None = None) -> ExistingIndex:
    """Đọc mã của các dòng đã lưu trong [date_from, date_to]; dòng cũ chưa có mã thì tính và ghi luôn (dữ liệu nạp
    trước bao-CR-541 tự lành dần, không cần chờ script).

    bao-CR-733: đọc THEO KHÚC `EXISTING_CHUNK` dòng (khóa trang `(reg_date, id)`, đi theo chỉ mục `reg_date`), chỉ các
    cột cần, câu Core — không dựng đối tượng ORM. `wanted` = mã của dòng trong tệp (`stamp_file_rows`): chỉ giữ mã
    nằm trong đó (None = giữ hết, kèm ô chuẩn của mọi mã khớp). Dòng đầu tiên mang một mã vẫn thắng như cũ: ba mã đều
    gói `reg_date` nên các dòng cùng mã cùng ngày, đi theo `id` tăng dần.

    Ô chuẩn của mã khớp (để so xung đột, bao-CR-699) chỉ cần cho dòng tệp CHƯA trùng mã băm — dòng trùng mã băm dừng
    ở "Đã có" trước bước so khớp. Nên khi có `wanted`, đọc hết rồi mới tra lại đúng các dòng đó theo id (cụm 1000)."""
    index = ExistingIndex()
    if date_from is None:
        return index
    parties: dict[int, str] = {}
    first_of_match: dict[str, tuple[int, int]] = {}       # mã khớp → (lô, id dòng) của dòng đầu tiên
    #  Mã của tệp → CHÍNH chuỗi đó: chỉ mục giữ lại chuỗi của tệp, không giữ thêm một bản đọc từ DB.
    want_hash = {h: h for h in wanted.hashes} if wanted else None
    want_identity = {h: h for h in wanted.identities} if wanted else None
    want_match = {h: h for h in wanted.matches} if wanted else None
    last: tuple | None = None
    while True:
        q = select(*_EXISTING_COLUMNS).where(CustomsLine.reg_date >= date_from, CustomsLine.reg_date <= date_to,
                                             CustomsLine.batch_id != exclude_batch_id)
        if last is not None:
            q = q.where(CustomsLine.reg_date >= last[0],
                        or_(CustomsLine.reg_date > last[0], and_(CustomsLine.reg_date == last[0],
                                                                 CustomsLine.id > last[1])))
        chunk = db.execute(q.order_by(CustomsLine.reg_date, CustomsLine.id).limit(EXISTING_CHUNK)).all()
        if chunk:
            _party_keys(db, {x.importer_id for x in chunk} | {x.partner_id for x in chunk}, parties)
        healed = []
        for x in chunk:
            row_hash, identity, match, canon = row_keys(dict(zip(HASH_FIELDS, x[_FIRST_VALUE:])),
                                                        parties.get(x.importer_id, ""), parties.get(x.partner_id, ""))
            if x.row_hash:
                row_hash = x.row_hash
            else:
                healed.append({"id": x.id, "row_hash": row_hash})
            if want_hash is None:
                index.by_hash.setdefault(row_hash, x.batch_id)
                index.by_identity.setdefault(identity, x.batch_id)
                index.by_match.setdefault(match, (x.batch_id, tuple(canon)))
                continue
            if row_hash in want_hash:
                index.by_hash.setdefault(want_hash[row_hash], x.batch_id)
            if identity in want_identity:
                index.by_identity.setdefault(want_identity[identity], x.batch_id)
            if match in want_match:
                first_of_match.setdefault(want_match[match], (x.batch_id, x.id))
        for i in range(0, len(healed), INSERT_CHUNK):
            db.execute(update(CustomsLine), healed[i:i + INSERT_CHUNK])
        if len(chunk) < EXISTING_CHUNK:
            break
        last = (chunk[-1].reg_date, chunk[-1].id)
    if wanted is not None:
        needed = {m for h, m in zip(wanted.hashes, wanted.matches) if h not in index.by_hash and m in first_of_match}
        _fill_match_canon(db, index, {m: first_of_match[m] for m in needed})
    return index


def _fill_match_canon(db: Session, index: ExistingIndex, wanted: dict[str, tuple[int, int]]) -> None:
    """bao-CR-733 — đọc lại đúng các dòng đầu-tiên-của-mã-khớp còn cần so xung đột (theo id, cụm 1000)."""
    match_of_line = {line_id: m for m, (_, line_id) in wanted.items()}
    ids = sorted(match_of_line)
    for i in range(0, len(ids), 1000):
        for x in db.execute(select(*_EXISTING_COLUMNS).where(CustomsLine.id.in_(ids[i:i + 1000]))).all():
            m = match_of_line[x.id]
            index.by_match[m] = (wanted[m][0], canon_values(dict(zip(HASH_FIELDS, x[_FIRST_VALUE:]))))


def stored_hashes(db: Session, lines: list[CustomsLine], party_cache: dict[int, str] | None = None) -> dict[int, str]:
    """bao-CR-608 — mã băm HIỆN TẠI của các dòng đã lưu (dòng cũ chưa có mã thì tính), để biết dòng
    trong tệp có cột "ID" có thật sự đổi gì so với dòng nó trỏ tới không."""
    parties = _party_keys(db, {x.importer_id for x in lines} | {x.partner_id for x in lines}, party_cache)
    return {x.id: x.row_hash or compute_row_hash(_stored_values(x), parties.get(x.importer_id, ""),
                                                 parties.get(x.partner_id, "")) for x in lines}


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
