"""Ghi một lô tệp GTT02 xuống DB — chạy trong tác vụ nền `import_tool.run_import` (bao-CR-470).

Lô nạp dùng lại `tab_import_batch` (`ImportModule.CUSTOMS_DECLARATION`), chế độ
`DRY_RUN` (chạy thử, không ghi gì) hoặc `APPLY`. Thiết kế:
`doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` §3.1 + §4.

⚠️ **Nạp theo LÔ, CHỈ THÊM dòng chưa có — không ghi đè, không thay theo khoảng ngày**
(bao-CR-541, đại ca chốt 01/10/2026). Mỗi dòng mang mã băm đủ các cột dữ liệu
(`dedupe.py`); dòng giống hệt một dòng đã lưu hoặc một dòng phía trên trong cùng tệp thì
BỎ QUA, nên nạp lại một tệp không nhân đôi dữ liệu. Bản trước (bao-CR-470) xóa mọi dòng
của lô khác trong khoảng ngày của tệp rồi chèn lại — tệp mới xuất thiếu là mất dữ liệu cũ
đúng mà không ai hay (rủi ro R1), và lô đã thay thì không hoàn tác được.

bao-CR-608 (đại ca 07/10/2026) — hai cột ĐIỀU KHIỂN tùy chọn: «ID» có thật → GHI ĐÈ đúng dòng
đó (giữ id + `batch_id` cũ, tính lại `row_hash`); «Thao tác = xóa» → XÓA dòng có ID đó. Trước khi
đụng, dòng được chụp đủ vào `tab_customs_line_change` (`line_change.py`) để hoàn tác lô dựng lại
được. Không có hai cột đó thì nạp y như trên.

⚠️ **Ghi dòng hàng bằng lệnh chèn hàng loạt, không `db.add` từng dòng.** Một lần
kết xuất hàng chục nghìn dòng; `db.add` còn kích hoạt nhật ký trước/sau của
`change_tracker` cho từng dòng (hai bảng này đã vào `NO_LOG_TABLES`, nhưng chèn
hàng loạt còn nhanh hơn nhiều).
"""
import json
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import insert, text, update
from sqlalchemy.orm import Session

from app.modules.import_tool.model import ImportBatch, ImportStatus, LogLevel
from app.modules.import_tool.service import add_log

from . import dedupe, line_change, reader, row_log
from .constants import (COLUMNS, CONTROL_LABELS, INSERT_CHUNK, OPTIONAL_LABELS, REF_ID_KEY,
                        CustomsLineChangeAction, CustomsLineChangeSource, PartyType)
from .ingredient import load_kind_tagger, load_tagger
from .model import CustomsLine, CustomsParty

SHEET = "GTT02"

_PARTY_KEYS = ("importer_tax_code", "importer_name", "partner_name")
#  Khóa của dòng trong tệp KHÔNG phải cột của bảng: ba cột đối tượng (đi qua `CustomsParty`) và ô
#  «ID» của bao-CR-608. Ghi đè còn giữ `source_row` cũ (dòng mấy trong tệp GỐC của lô đã thêm nó).
_NON_COLUMN_KEYS = frozenset(_PARTY_KEYS) | {REF_ID_KEY}
_VND_KEYS = ("price_vnd_flat", "price_vnd_line_tax")
_LOCK_NAME = "customs_declaration_import"
_LOCK_WAIT_SECONDS = 300


class CustomsImportBusyError(reader.CustomsFileError):
    """Lượt nạp khác giữ khóa quá lâu — từ chối lô này bằng câu đọc được (không kèm traceback)."""


@contextmanager
def _import_lock(db: Session):
    """Cho từng lô ghi LẦN LƯỢT — kể cả khác tiến trình Celery (khóa có tên của MySQL).

    Hai lô chứa cùng một dòng mà ghi song song thì cả hai cùng thấy «chưa có» và cùng chèn:
    chống trùng thủng đúng ở chỗ nó cần nhất. Khóa giữ trên một kết nối RIÊNG (khóa MySQL gắn
    với kết nối, kết nối của `db` có thể trả về pool giữa chừng). SQLite (pytest) bỏ qua.
    """
    bind = db.get_bind()
    if bind.dialect.name != "mysql":
        yield
        return
    with bind.connect() as conn:
        got = conn.execute(text("SELECT GET_LOCK(:n, :w)"),
                           {"n": _LOCK_NAME, "w": _LOCK_WAIT_SECONDS}).scalar()
        if got != 1:
            raise CustomsImportBusyError("Đang có lượt nạp dữ liệu thị trường khác chạy quá lâu — thử lại sau")
        try:
            yield
        finally:
            conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": _LOCK_NAME})


def run(db: Session, batch: ImportBatch, raw: bytes, apply: bool) -> None:
    """Đọc tệp của lô, ghi số liệu vào lô; `apply=True` mới ghi dòng hàng thật."""
    res = reader.parse(raw, batch.filename or "")
    if res.optional_columns:
        #  bao-CR-603: nói ra tệp có thêm cột gì — người nạp biết hoạt chất / giá VND của lô này
        #  lấy từ tệp (ô trống vẫn suy ra / tính như cũ).
        names = ", ".join(f"«{(dict(COLUMNS) | OPTIONAL_LABELS)[k]}»" for k in res.optional_columns)
        add_log(db, batch, SHEET, 0, LogLevel.INFO, "customs", f"Tệp có cột tùy chọn: {names} — ô có giá trị thì lấy "
                "của tệp, ô trống thì suy ra / tính như cũ")
    if res.control_columns:
        names = ", ".join(f"«{CONTROL_LABELS[k]}»" for k in res.control_columns)
        add_log(db, batch, SHEET, 0, LogLevel.INFO, "customs", f"Tệp có cột {names} — ô ID có thật thì ghi đè "
                "đúng dòng đó, «Thao tác» = xóa thì xóa dòng có ID đó; hoàn tác lô trả lại như cũ")
    for row_no, level, message in res.logs:
        add_log(db, batch, SHEET, row_no, level, "customs", message)
    with _import_lock(db):
        _classify_and_write(db, batch, res, apply)


def _classify_and_write(db: Session, batch: ImportBatch, res: reader.ParseResult, apply: bool) -> None:
    rows = res.rows
    date_from = min((r["reg_date"] for r in rows), default=None)
    date_to = max((r["reg_date"] for r in rows), default=None)
    #  bao-CR-541: so trùng bằng mã băm với dòng đã lưu trong khoảng ngày của tệp (dòng cũ
    #  chưa có mã thì tính luôn), rồi chỉ giữ dòng thật sự mới. Chạy thử cũng so — người nạp
    #  thấy trước bao nhiêu dòng mới, bao nhiêu dòng đã có, bao nhiêu dòng trùng trong tệp.
    identities = dedupe.stamp_rows(rows)
    existing = dedupe.load_existing(db, date_from, date_to, exclude_batch_id=batch.id)
    #  bao-CR-608: tra MỘT LẦN mọi id mà cột «ID» trỏ tới (từng cụm 1000), không truy vấn từng dòng.
    wanted = {r[REF_ID_KEY] for r in rows if r.get(REF_ID_KEY)} | {d["ref_id"] for d in res.deletes if d["ref_id"]}
    targets = line_change.load_lines_by_id(db, wanted)
    taggers = _Taggers(db) if (targets or (apply and rows)) else None
    unchanged = _tag_overwrites(db, rows, targets, taggers) if targets else set()
    cls = row_log.classify_rows(res, identities, existing, frozenset(targets), unchanged)
    for row_no, message in cls.warnings:
        add_log(db, batch, SHEET, row_no, LogLevel.WARNING, "customs", message)
    #  bao-CR-496: mỗi dòng dữ liệu một dòng nhật ký mang kết cục — ghi ở CẢ chạy thử lẫn ghi thật.
    row_counts = row_log.write_row_logs(db, batch, cls.statuses)

    batch.total_rows = len(rows) + len(res.deletes) + res.skipped
    batch.skipped_count = res.skipped + cls.ignored
    batch.created_count = len(cls.to_insert)
    batch.updated_count = len(cls.to_update)    # bao-CR-608 — ghi đè theo cột «ID»
    batch.deleted_count = len(cls.to_delete)    # bao-CR-608 — xóa theo «Thao tác» (có bản chụp)
    batch.sheet_info = json.dumps({
        "date_from": date_from.isoformat() if date_from else "",
        "date_to": date_to.isoformat() if date_to else "",
        "date_fixed": sum(r["date_fixed"] for r in rows),
        "date_swap_detected": res.date_swap,
        "duplicate_rows": row_counts["duplicate"],     # trùng trong tệp — bỏ qua
        "existing_rows": row_counts["existing"],       # bao-CR-541: đã có trong bảng giá — bỏ qua
        "suspect_rows": cls.suspect,                   # bao-CR-541: thêm mới nhưng nghi sửa giá
        "updated_rows": row_counts["updated"],         # bao-CR-608: ghi đè theo ID
        "deleted_rows": row_counts["deleted"],         # bao-CR-608: xóa theo «Thao tác»
        "ignored_rows": row_counts["ignored"],         # bao-CR-608: xóa hỏng / ID lặp — bỏ qua
        "id_not_found": cls.id_not_found,              # bao-CR-608: ô ID có số mà không có → thêm mới
    }, ensure_ascii=False)

    if apply:
        user_id = batch.created_by or 0
        #  bao-CR-608: CHỤP trước rồi mới đụng — hoàn tác lô dựng lại từ bản chụp.
        if cls.to_delete:
            line_change.record_snapshots(db, [targets[i] for i in cls.to_delete], CustomsLineChangeAction.DELETE,
                                         CustomsLineChangeSource.IMPORT, batch.id, user_id)
            line_change.delete_lines(db, cls.to_delete)
        if cls.to_update:
            line_change.record_snapshots(db, [targets[i] for _, i in cls.to_update],
                                         CustomsLineChangeAction.UPDATE, CustomsLineChangeSource.IMPORT,
                                         batch.id, user_id)
        for r in cls.to_insert:
            taggers.tag(r)
        written = cls.to_insert + [r for r, _ in cls.to_update]
        if written:
            importer_ids = upsert_parties(db, PartyType.DOMESTIC, written)
            partner_ids = upsert_parties(db, PartyType.FOREIGN, written)
            _insert_lines(db, batch.id, cls.to_insert, importer_ids, partner_ids)
            _update_lines(db, cls.to_update, importer_ids, partner_ids)

    batch.status = ImportStatus.DONE
    batch.finished_at = datetime.utcnow()
    db.commit()


class _Taggers:
    """HQ4 — gắn hoạt chất + hàm lượng + nhãn Thành phẩm / Nguyên liệu; danh mục nạp MỘT lần cho cả lô."""

    def __init__(self, db: Session):
        self.tagger = load_tagger(db)
        self.kinds = load_kind_tagger(db)          # bao-CR-494: nhãn Thành phẩm / Nguyên liệu
        self.cache: dict[str, tuple[str, str, int]] = {}

    def derive(self, name: str) -> tuple[str, str, int]:
        if name not in self.cache:
            active, form = self.tagger.tag(name)
            self.cache[name] = (active, form, self.kinds.tag(name))
        return self.cache[name]

    def tag(self, r: dict, previous: CustomsLine | None = None) -> None:
        """Điền hoạt chất / hàm lượng / nhãn / giá VND vào dòng `r` của tệp (sửa tại chỗ).

        bao-CR-603: tệp có cột và ô có chữ thì lấy của tệp (cờ `_from_file` = giá trị do người
        nhập, `retag_all` không ghi đè); ô trống hoặc tệp không có cột thì suy ra như cũ. Giá VND
        của tệp (nếu có) đã nằm sẵn trong `r`; thiếu thì NULL → lúc đọc tính như cũ.

        bao-CR-608, `previous` = dòng đã lưu mà dòng này GHI ĐÈ (theo cột «ID»): ô của tệp trùng
        đúng giá trị hệ thống tự suy ra / tự tính — theo dữ liệu MỚI của dòng, hoặc đúng giá trị
        suy ra / tính đang hiện trên màn cho dòng CŨ — thì coi là SUY RA (cờ 0, giá VND NULL).
        Lý do: Excel xuất ra từ màn này điền sẵn cả bốn cột đó; xuất → sửa đơn giá → nạp lại mà
        coi mọi ô là «của tệp» thì giá VND cũ (tính theo đơn giá cũ) bị đóng băng thành số tay.
        """
        active, form, r["product_kind"] = self.derive(r["product_name"])
        file_active = (r.get("active_ingredient") or "").strip()
        file_form = (r.get("formulation") or "").strip()
        if previous is not None:
            if _is_derived_text(file_active, active, previous.active_ingredient, previous.active_ingredient_from_file):
                file_active = ""
            if _is_derived_text(file_form, form, previous.formulation, previous.formulation_from_file):
                file_form = ""
        r["active_ingredient"] = file_active or active
        r["active_ingredient_from_file"] = bool(file_active)
        r["formulation"] = file_form or form
        r["formulation_from_file"] = bool(file_form)
        for key in _VND_KEYS:
            r.setdefault(key, None)
        if previous is not None and any(r[key] is not None for key in _VND_KEYS):
            from .service import compute_vnd_prices    # nạp muộn — tránh nạp vòng lúc khởi động
            source = SimpleNamespace(**{k: r.get(k) for k in ("adj_price_usd", "price_usd", "usd_rate",
                                                              "fx_rate", "currency", "rate_import")})
            computed_new = dict(zip(_VND_KEYS, compute_vnd_prices(source)))
            computed_old = dict(zip(_VND_KEYS, compute_vnd_prices(previous)))
            for key in _VND_KEYS:
                shown_old = computed_old[key] if getattr(previous, key) is None else None
                if r[key] is not None and (_same_decimal(r[key], computed_new[key])
                                           or _same_decimal(r[key], shown_old)):
                    r[key] = None


def _is_derived_text(value: str, derived_now: str, stored: str, stored_from_user: bool) -> bool:
    """Ô chữ của tệp chỉ là giá trị SUY RA (không phải người nhập): trùng giá trị suy ra từ tên hàng
    mới, hoặc trùng giá trị suy ra đang lưu của dòng cũ (cờ 0)."""
    if not value:
        return False
    return (value.upper() == (derived_now or "").upper()
            or (not stored_from_user and value.upper() == (stored or "").upper()))


def _same_decimal(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return Decimal(str(a)).quantize(Decimal("0.01")) == Decimal(str(b)).quantize(Decimal("0.01"))


def _tag_overwrites(db: Session, rows: list[dict], targets: dict[int, CustomsLine], taggers: _Taggers) -> set[int]:
    """Gắn nhãn cho các dòng có ID trỏ đúng dòng đã có; → số dòng (trong tệp) có dữ liệu Y HỆT dòng
    đã lưu — những dòng đó bỏ qua, không chụp, không ghi (xuất → sửa vài dòng → nạp lại cả tệp
    thì chỉ dòng thật sự sửa mới thành «Ghi đè»)."""
    hashes = dedupe.stored_hashes(db, list(targets.values()))
    unchanged: set[int] = set()
    for r in rows:
        line = targets.get(r.get(REF_ID_KEY) or 0)
        if line is None:
            continue
        taggers.tag(r, previous=line)
        same = (r["row_hash"] == hashes[line.id]
                and r["active_ingredient"] == (line.active_ingredient or "")
                and r["formulation"] == (line.formulation or "")
                and r["active_ingredient_from_file"] == bool(line.active_ingredient_from_file)
                and r["formulation_from_file"] == bool(line.formulation_from_file)
                and all(_same_decimal(r[k], getattr(line, k)) for k in _VND_KEYS))
        if same:
            unchanged.add(r["source_row"])
    return unchanged


def revert(db: Session, batch: ImportBatch) -> dict:
    """Hoàn tác một lô đã ghi: xóa dòng thêm mới; bao-CR-608 còn dựng lại dòng lô đã xóa và trả
    dòng lô đã ghi đè về bản chụp (`line_change.revert_batch_lines`).

    Từ bao-CR-541 lô chỉ THÊM dòng chưa có (và từ bao-CR-608 ghi đè / xóa thì có bản chụp) nên
    hoàn tác luôn an toàn — kể cả để sửa số liệu: hoàn tác lô sai rồi nạp lại tệp đúng.
    ⚠️ **Vẫn chặn lô CŨ đã thay dữ liệu** (`deleted_count > 0` mà KHÔNG có bản chụp nào — nạp
    trước bao-CR-541). Dòng cũ đã xóa lúc thay và không có bản chụp để dựng lại — hoàn tác lúc
    đó là để trống cả khoảng ngày mà không ai hay.
    """
    if batch.deleted_count and not line_change.has_snapshots(db, batch.id):
        return {"ok": False,
                "message": f"Lô này nạp theo cách cũ, đã thay {batch.deleted_count} dòng cũ nên không "
                           "hoàn tác được — hoàn tác sẽ để trống cả khoảng ngày đó."}
    out = line_change.revert_batch_lines(db, batch.id)
    parts = [f"xóa {out['deleted']} dòng thêm mới"]
    if out["restored"]:
        parts.append(f"trả {out['restored']} dòng ghi đè về bản cũ")
    if out["reinserted"]:
        parts.append(f"dựng lại {out['reinserted']} dòng đã xóa")
    return {"ok": True, "deleted": out["deleted"], "restored": out["restored"] + out["reinserted"],
            "warnings": out["warnings"],
            "message": "Đã hoàn tác: " + ", ".join(parts) + line_change.summarize_warnings(out["warnings"])}


# ── Nội bộ ─────────────────────────────────────────────────────────────────
def _party_key(party_type: PartyType, row: dict) -> tuple[str, str, str] | None:
    """→ (khóa chống trùng, mã số thuế, tên), hoặc None nếu dòng không có đối tượng này."""
    if party_type == PartyType.DOMESTIC:
        tax = row["importer_tax_code"]
        return (tax, tax, row["importer_name"]) if tax else None
    name = row["partner_name"]
    return (reader.hash_name(name), "", name) if name else None


def upsert_parties(db: Session, party_type: PartyType, rows: list[dict]) -> dict[str, int]:
    """Tra hoặc tạo đối tượng cho CẢ LÔ trong vài truy vấn, không truy vấn từng dòng.

    → map khóa chống trùng → id. Tên lấy của lần nạp MỚI NHẤT (dòng cuối cùng gặp).
    """
    wanted: dict[str, tuple[str, str]] = {}
    for r in rows:
        k = _party_key(party_type, r)
        if k:
            wanted[k[0]] = (k[1], k[2])
    ids: dict[str, int] = {}
    keys = list(wanted)
    for i in range(0, len(keys), 1000):
        chunk = keys[i:i + 1000]
        for p in db.query(CustomsParty).filter(CustomsParty.party_type == int(party_type),
                                               CustomsParty.dedupe_key.in_(chunk)):
            ids[p.dedupe_key] = p.id
            if wanted[p.dedupe_key][1] and p.name != wanted[p.dedupe_key][1]:
                p.name = wanted[p.dedupe_key][1]
    new = [{"party_type": int(party_type), "dedupe_key": k, "tax_code": wanted[k][0],
            "name": wanted[k][1]} for k in keys if k not in ids]
    if new:
        db.execute(insert(CustomsParty), new)
        db.flush()
        for i in range(0, len(new), 1000):
            chunk = [n["dedupe_key"] for n in new[i:i + 1000]]
            for pid, key in db.query(CustomsParty.id, CustomsParty.dedupe_key).filter(
                    CustomsParty.party_type == int(party_type), CustomsParty.dedupe_key.in_(chunk)):
                ids[key] = pid
    return ids


def party_ids_of(row: dict, importer_ids: dict[str, int], partner_ids: dict[str, int]) -> dict[str, int]:
    imp = _party_key(PartyType.DOMESTIC, row)
    par = _party_key(PartyType.FOREIGN, row)
    return {"importer_id": importer_ids.get(imp[0], 0) if imp else 0,
            "partner_id": partner_ids.get(par[0], 0) if par else 0}


def _insert_lines(db: Session, batch_id: int, rows: list[dict],
                  importer_ids: dict[str, int], partner_ids: dict[str, int]) -> None:
    payload = []
    for r in rows:
        line = {k: v for k, v in r.items() if k not in _NON_COLUMN_KEYS}
        line.update(batch_id=batch_id, **party_ids_of(r, importer_ids, partner_ids))
        payload.append(line)
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(insert(CustomsLine), payload[i:i + INSERT_CHUNK])


def _update_lines(db: Session, pairs: list[tuple[dict, int]],
                  importer_ids: dict[str, int], partner_ids: dict[str, int]) -> None:
    """bao-CR-608 — ghi đè TOÀN BỘ cột dữ liệu theo khóa chính, giữ `batch_id` + `source_row` cũ.

    `row_hash` mới đã nằm trong dòng (`dedupe.stamp_rows`). Đổi `reg_date` sang năm khác thì
    MySQL tự dời dòng sang phân vùng mới. Lệnh cập nhật hàng loạt theo khóa chính của ORM —
    không nạp đối tượng, không kích hoạt `change_tracker`."""
    payload = []
    for r, line_id in pairs:
        line = {k: v for k, v in r.items() if k not in _NON_COLUMN_KEYS and k != "source_row"}
        line.update(id=line_id, **party_ids_of(r, importer_ids, partner_ids))
        payload.append(line)
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(update(CustomsLine), payload[i:i + INSERT_CHUNK])
