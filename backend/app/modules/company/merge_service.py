"""Gộp một pháp nhân TRÙNG vào pháp nhân GIỮ rồi xóa bản trùng — bao-CR-532.

Sinh ra vì hệ có hai dòng cùng tên, cùng mã số thuế cho DEGO Holding (`DEGO` và `DEGO HOLDING`),
và chứng từ đã chia đôi giữa hai dòng đó. Hàm này KHÔNG commit: người gọi quyết định giữ hay
bỏ. Script `scripts/merge_duplicate_company.py` chạy thử bằng cách chạy THẬT rồi rollback, nên
số liệu chạy thử là số thật, kể cả các dòng bị gộp trùng.

Luật (đọc trước khi sửa):

1. **Tự dò cột** từ model — mọi cột số có chữ ``compan`` trong tên — chứ không gắn cứng danh
   sách bảng: thêm bảng mới có ``company_id`` là tự được chuyển theo.
2. **Không ghi lại lịch sử**: bảng nhật ký (`*_log`, `tab_import_change`) giữ nguyên số cũ —
   đó là chuyện đã xảy ra, không phải dữ liệu đang sống.
3. **Bảng có ràng buộc duy nhất đụng cột công ty** phải có cách xử lý riêng ở dưới. Bảng nào
   chưa có mà lại đụng thật thì DỪNG (``MergeError``), không đoán cách gộp.
4. **Kiểm lại cuối cùng**: còn sót dù một dòng trỏ bản trùng thì ném lỗi — người gọi rollback.

Các chỗ xử lý riêng, và vì sao:

- ``tab_department_company`` — khóa ngoại ``ON DELETE CASCADE`` tới công ty: xóa bản trùng mà
  chưa chuyển là MySQL tự xóa luôn liên kết phòng–pháp nhân. Ràng buộc (phòng, công ty) nên dòng
  nào bản giữ đã có thì bỏ, còn lại thì chuyển.
- ``tab_doc_folder`` — mỗi pháp nhân đúng MỘT thư mục gốc (``ux_doc_folder_root_company``).
  Bản giữ đã có gốc thì chuyển liên kết văn bản sang gốc đó rồi xóa gốc của bản trùng; chưa có
  thì chuyển nguyên gốc. Gốc bản trùng còn thư mục con thì DỪNG: phải viết lại cột ``path``, mà
  cột đó chỉ được ghi qua dịch vụ thư mục (``folder_move_service``).
- ``tab_inventory`` — số DẪN XUẤT từ ``tab_inventory_move``. Chuyển dịch chuyển trước, rồi tính lại
  bằng chính ``inventory.service._recompute`` để cùng (kho, mã hàng) có ở cả hai bên thì cộng dồn
  theo bình quân gia quyền đúng như hệ tự tính — không tự chép công thức.
- ``tab_user_scope`` — id công ty lưu dạng CHỮ (``dim='company'``, ``value='15'``), quét theo cột
  số không thấy. Dòng nào người đó đã có id giữ thì xóa, còn lại thì đổi.
- Ghi chép tay vào ``tab_doc_folder`` / ``tab_document_folder_link`` ở đây là ngoại lệ có chủ đích
  của một đợt sửa dữ liệu, không phải đường ghi thường ngày.
"""
from __future__ import annotations

from sqlalchemy import Integer, text
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.base_model import Base
from app.modules.company.model import Company

#  Ô của bản giữ còn trống thì chép từ bản trùng sang; ô đã có thì KHÔNG đè.
FILL_FIELDS = ("address", "invoice_email", "short_name", "legal_rep_title", "legal_representative_id")

#  Bảng có cách xử lý riêng — vòng lặp chung bỏ qua chúng.
SPECIAL_TABLES = {"tab_company", "tab_department_company", "tab_doc_folder", "tab_inventory"}
HISTORY_TABLES = {"tab_import_change"}


class MergeError(Exception):
    """Dừng gộp — người gọi phải rollback."""


def is_history(table: str) -> bool:
    return table.endswith("_log") or table in HISTORY_TABLES


def company_columns(include_history: bool = False) -> list[tuple[str, str]]:
    """Mọi cột SỐ có chữ ``compan`` trong tên, trên mọi bảng đã khai model."""
    out = []
    for table in Base.metadata.sorted_tables:
        if table.name == "tab_company" or (is_history(table.name) and not include_history):
            continue
        for col in table.columns:
            if "compan" in col.name.lower() and isinstance(col.type, Integer):
                out.append((table.name, col.name))
    return out


def _unique_sets(table_name: str, column: str) -> list[list[str]]:
    """Các ràng buộc duy nhất của bảng có chứa ``column`` — trả về các cột CÒN LẠI của từng cái."""
    table = Base.metadata.tables[table_name]
    groups = [[c.name for c in u.columns] for u in table.constraints if u.__class__.__name__ == "UniqueConstraint"]
    groups += [[c.name for c in ix.columns] for ix in table.indexes if ix.unique]
    return [[c for c in g if c != column] for g in groups if column in g]


def _exec(db: Session, sql: str, **params) -> int:
    return db.execute(text(sql), params).rowcount or 0


def count_references(db: Session, company_id: int) -> dict[str, int]:
    """Số dòng còn trỏ vào ``company_id`` (không tính lịch sử). Dùng cho chạy thử và kiểm cuối."""
    out = {}
    for table, col in company_columns() + [("tab_department_company", "company_id"),
                                           ("tab_doc_folder", "company_id"),
                                           ("tab_doc_folder", "root_company_id"),
                                           ("tab_inventory", "company_id")]:
        n = db.execute(text(f"select count(*) from {table} where {col} = :c"), {"c": company_id}).scalar()
        if n:
            out[f"{table}.{col}"] = n
    n = db.execute(text("select count(*) from tab_user_scope where dim = 'company' and value = :v"),
                   {"v": str(company_id)}).scalar()
    if n:
        out["tab_user_scope(dim=company)"] = n
    n = db.execute(text("select count(*) from tab_company where parent = :c"), {"c": company_id}).scalar()
    if n:
        out["tab_company.parent"] = n
    return out


def _check_unique_conflicts(db: Session, keep_id: int, dup_id: int) -> None:
    """Bảng thường có ràng buộc duy nhất chứa cột công ty mà chuyển sẽ đụng → dừng, không đoán."""
    problems = []
    for table, col in company_columns():
        if table in SPECIAL_TABLES:
            continue
        for others in _unique_sets(table, col):
            if not others:
                n = db.execute(text(f"select count(*) from {table} where {col} = :k"), {"k": keep_id}).scalar()
                clash = n if db.execute(text(f"select count(*) from {table} where {col} = :d"),
                                        {"d": dup_id}).scalar() else 0
            else:
                on = " and ".join(f"a.{o} = b.{o}" for o in others)
                clash = db.execute(text(f"select count(*) from {table} a join {table} b on {on} "
                                        f"where a.{col} = :d and b.{col} = :k"),
                                   {"d": dup_id, "k": keep_id}).scalar()
            if clash:
                problems.append(f"{table}.{col} ({clash} dòng đụng ràng buộc trên {others or [col]})")
    if problems:
        raise MergeError("Chưa có cách gộp cho: " + "; ".join(problems))


def _merge_department_links(db: Session, keep_id: int, dup_id: int, report: dict) -> None:
    dropped = _exec(db, """delete from tab_department_company where company_id = :d and department_id in
                           (select department_id from (select department_id from tab_department_company
                            where company_id = :k) x)""", d=dup_id, k=keep_id)
    moved = _exec(db, "update tab_department_company set company_id = :k where company_id = :d", k=keep_id, d=dup_id)
    if dropped:
        report["tab_department_company (bỏ vì bản giữ đã có)"] = dropped
    if moved:
        report["tab_department_company.company_id"] = moved


def _merge_folders(db: Session, keep_id: int, dup_id: int, report: dict) -> None:
    dup_root = db.execute(text("select id from tab_doc_folder where root_company_id = :d"), {"d": dup_id}).scalar()
    keep_root = db.execute(text("select id from tab_doc_folder where root_company_id = :k"), {"k": keep_id}).scalar()
    if dup_root:
        children = db.execute(text("select count(*) from tab_doc_folder where parent_id = :r"), {"r": dup_root}).scalar()
        if children:
            raise MergeError(f"Thư mục gốc {dup_root} của bản trùng còn {children} thư mục con — chuyển chúng "
                             "sang gốc của bản giữ bằng màn Thư mục trước (cột path chỉ ghi qua dịch vụ thư mục)")
    if dup_root and keep_root:
        links = db.execute(text("select id, document_id, is_primary from tab_document_folder_link "
                                "where folder_id = :r"), {"r": dup_root}).all()
        for link_id, doc_id, primary in links:
            existing = db.execute(text("select id from tab_document_folder_link where document_id = :doc "
                                       "and folder_id = :k"), {"doc": doc_id, "k": keep_root}).scalar()
            if existing:
                if primary:
                    _exec(db, "update tab_document_folder_link set is_primary = :t where id = :i", t=True, i=existing)
                _exec(db, "delete from tab_document_folder_link where id = :i", i=link_id)
            else:
                _exec(db, "update tab_document_folder_link set folder_id = :k where id = :i", k=keep_root, i=link_id)
        if links:
            report["tab_document_folder_link (sang gốc bản giữ)"] = len(links)
        _exec(db, "delete from tab_doc_folder where id = :r", r=dup_root)
        report["tab_doc_folder (xóa gốc bản trùng)"] = 1
    elif dup_root:
        _exec(db, "update tab_doc_folder set company_id = :k, root_company_id = :k where id = :r",
              k=keep_id, r=dup_root)
        report["tab_doc_folder (gốc chuyển nguyên)"] = 1
    n = _exec(db, "update tab_doc_folder set company_id = :k where company_id = :d", k=keep_id, d=dup_id)
    if n:
        report["tab_doc_folder.company_id"] = n


def _merge_user_scope(db: Session, keep_id: int, dup_id: int, report: dict) -> list[int]:
    rows = db.execute(text("select id, user_id, role_id, entity, is_exclude from tab_user_scope "
                           "where dim = 'company' and value = :v"), {"v": str(dup_id)}).all()
    dropped = changed = 0
    for sid, uid, rid, entity, excl in rows:
        exists = db.execute(text("select 1 from tab_user_scope where user_id = :u and role_id = :r and entity = :e "
                                 "and dim = 'company' and value = :v and is_exclude = :x"),
                            {"u": uid, "r": rid, "e": entity, "v": str(keep_id), "x": excl}).first()
        if exists:
            dropped += _exec(db, "delete from tab_user_scope where id = :i", i=sid)
        else:
            changed += _exec(db, "update tab_user_scope set value = :v where id = :i", v=str(keep_id), i=sid)
    if dropped:
        report["tab_user_scope (bỏ vì đã có id giữ)"] = dropped
    if changed:
        report["tab_user_scope (đổi sang id giữ)"] = changed
    return sorted({r[1] for r in rows})


def merge_companies(db: Session, keep_id: int, dup_id: int) -> dict:
    """Chuyển mọi tham chiếu từ ``dup_id`` sang ``keep_id`` rồi xóa ``dup_id``.

    KHÔNG commit, và không gọi gì có commit (xem ``write_merge_audit``) — chạy thử dựa hoàn toàn
    vào việc người gọi rollback được.
    """
    from app.modules.inventory.service import _recompute

    if keep_id == dup_id:
        raise MergeError("Bản giữ và bản trùng là một")
    keep, dup = db.get(Company, keep_id), db.get(Company, dup_id)
    if not keep or not dup:
        raise MergeError(f"Không tìm thấy công ty (giữ={keep_id}, trùng={dup_id})")
    if not (keep.tax_code or "").strip() or keep.tax_code.strip() != (dup.tax_code or "").strip():
        raise MergeError(f"Mã số thuế khác nhau ({keep.tax_code!r} / {dup.tax_code!r}) — không phải bản trùng")

    _check_unique_conflicts(db, keep_id, dup_id)
    report: dict = {}

    filled = []
    for f in FILL_FIELDS:
        if not getattr(keep, f) and getattr(dup, f):
            setattr(keep, f, getattr(dup, f))
            filled.append(f)
    if filled:
        report["tab_company (chép ô trống sang bản giữ)"] = len(filled)
        report["_filled_fields"] = filled

    _merge_department_links(db, keep_id, dup_id, report)
    _merge_folders(db, keep_id, dup_id, report)

    inv_keys = {(w, p): (n, u) for w, p, n, u in db.execute(text(
        "select warehouse_code, product_code, product_name, unit from tab_inventory where company_id = :d"),
        {"d": dup_id}).all()}
    for w, p in db.execute(text("select distinct warehouse_code, product_code from tab_inventory_move "
                                "where company_id = :d"), {"d": dup_id}).all():
        inv_keys.setdefault((w, p), ("", ""))
    n = _exec(db, "delete from tab_inventory where company_id = :d", d=dup_id)
    if n:
        report["tab_inventory (xóa dòng bản trùng, tính lại bên giữ)"] = n

    for table, col in company_columns():
        if table in SPECIAL_TABLES:
            continue
        n = _exec(db, f"update {table} set {col} = :k where {col} = :d", k=keep_id, d=dup_id)
        if n:
            report[f"{table}.{col}"] = n

    db.flush()
    for (w, p), (name, unit) in sorted(inv_keys.items()):
        _recompute(db, keep_id, w, p, name or "", unit or "")
    if inv_keys:
        report["tab_inventory (khóa kho+mã được tính lại)"] = len(inv_keys)

    scope_users = _merge_user_scope(db, keep_id, dup_id, report)
    n = _exec(db, "update tab_company set parent = :k where parent = :d", k=keep_id, d=dup_id)
    if n:
        report["tab_company.parent"] = n

    db.flush()
    left = count_references(db, dup_id)
    if left:
        raise MergeError(f"Còn sót tham chiếu tới bản trùng: {left}")

    report["_dup_code"], report["_keep_code"] = dup.code, keep.code
    db.delete(dup)
    db.flush()
    report["tab_company (xóa bản trùng)"] = 1
    report["_scope_users"] = scope_users
    return report


def write_merge_audit(db: Session, keep_id: int, dup_id: int, report: dict, user_id: int = 0) -> None:
    """Ghi nhật ký cho một lần gộp ĐÃ CHỐT.

    ⚠️ Tách khỏi ``merge_companies`` có chủ đích: ``core.audit.record`` tự ``db.commit()`` (BM-013,
    cố ý giữ vì 273 lời gọi dựa vào nó). Gọi nó giữa lúc gộp là chạy thử cũng thành ghi thật —
    không còn gì để rollback. Chỉ gọi hàm này ở nhánh ``--apply``; lời gọi đầu tiên sẽ commit
    luôn cả phần gộp.
    """
    moved = sum(v for k, v in report.items() if not k.startswith("_"))
    dup_code, keep_code = report.get("_dup_code", ""), report.get("_keep_code", "")
    record(db, user_id, "company", keep_id, "update",
           f"bao-CR-532: gộp pháp nhân trùng {dup_code} (id {dup_id}) vào {keep_code} — {moved} thay đổi")
    record(db, user_id, "company", dup_id, "delete",
           f"bao-CR-532: xóa pháp nhân trùng, dữ liệu đã chuyển sang {keep_code} (id {keep_id})",
           doc_code=dup_code)
