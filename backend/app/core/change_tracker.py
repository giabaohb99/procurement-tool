"""LỚP ORM — gom giá trị TRƯỚC/SAU rồi ghi một lần cuối request (bao-CR-402, P4).

Vì sao nghe ở tầng ORM chứ không đi sửa từng service: giá trị cũ chỉ còn tồn
tại trong **một khoảnh khắc duy nhất** — sau khi service gán `obj.unit_price =
15000` và trước khi SQLAlchemy đẩy câu `UPDATE` xuống. Muốn bắt nó ở tầng
service thì mỗi hàm sửa dữ liệu phải tự đọc lại bản ghi cũ trước khi ghi đè, ở
hàng trăm chỗ, và chỗ nào quên thì im lặng. SQLAlchemy giữ sẵn khoảnh khắc đó
trong `inspect(obj).attrs.<cột>.history`; nghe một chỗ là đủ cho cả hệ.

BỐN LUẬT CỨNG CỦA TỆP NÀY — ba cái đầu là ba trong bốn cái bẫy ở §6:

1. **KHÔNG ghi DB bên trong flush.** `before_flush` chỉ được gom vào bộ đệm
   trong `ContextVar`. Ghi xuống DB ngay tại đó là mở một flush lồng trong
   flush, và vòng đệ quy đó không có đáy.
2. **KHÔNG bao giờ ghi bảng của chính mình** (`NO_LOG_TABLES`). Thiếu một tên
   trong danh sách đó là vòng lặp vô hạn: mỗi dòng thay đổi đẻ một dòng thay
   đổi. `tab_login_session` nằm trong đó vì `last_seen_at` bị dập mỗi lượt gọi.
3. **Nhập liệu hàng loạt phải GỘP.** Tệp khảo sát 2.666 phiếu ghi từng trường
   là vài chục nghìn dòng cho MỘT lần chạy. `actor_kind = 3` (script) bật cờ
   gộp; và đặt thêm một cầu chì cho cả người dùng thường, vì một cú duyệt hàng
   loạt cũng đủ chạm trần.
4. **Chỉ ghi thứ ĐÃ COMMIT.** Đây là chỗ P4 không lặp lại lỗi BM-013 của lớp
   audit: dữ liệu được flush xuống rồi giao dịch quay đầu là chuyện thường (một
   `except` bắt lỗi rồi `db.rollback()`), và nếu cứ ghi thì nhật ký kể lại một
   thay đổi **chưa từng xảy ra**. Dấu vết ma còn tệ hơn không có dấu vết, vì
   người đọc tin nó. Nên bộ đệm chỉ được đóng dấu ở `after_commit`, và bị vứt
   ở `after_rollback`.

Tài liệu gốc: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §4.3, §6.
"""
import logging
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.core.logging_codes import (ACTOR_KIND_SCRIPT, CHANGE_OP_ADD, CHANGE_OP_DELETE,
                                    CHANGE_OP_UPDATE)
from app.core.logging_policy import NO_LOG_TABLES, is_sensitive_column
from app.core.request_context import get_context

log = logging.getLogger("app.change_log")

#  Cột `TEXT` nhận được nhiều hơn thế, nhưng một ô mô tả vài chục KB nhân với
#  hai (trước + sau) nhân với mọi lần sửa là một bảng phình vì thứ không ai đọc
#  hết. Cắt và đánh dấu — biết "đã đổi, phần đầu như thế này" là đủ để đi tra.
MAX_VALUE_LEN = 4000

#  Cầu chì cho người dùng THƯỜNG (script đã gộp sẵn từ đầu). Quá trần thì phần
#  còn lại của lượt gọi chuyển sang gộp, chứ không phải bỏ im lặng — im lặng thì
#  người đọc tưởng lượt đó chỉ đổi 500 ô.
MAX_DETAIL_CHANGES = 500

#  Số dòng dữ liệu tối đa chịu khó dò ngược lên `tab_audit_log` để điền
#  `changed_fields`. Một cú duyệt hàng loạt đụng vài trăm phiếu thì đó là vài
#  trăm câu `UPDATE` cho một cột trang trí — không đáng.
MAX_AUDIT_BACKFILL_ROWS = 50

#  Cột đổi theo MÁY chứ không theo người: `updated_at` có `onupdate=func.now()`
#  nên đổi ở **mọi** lần sửa. Ghi nó là nhân đôi số dòng để kể lại một điều đã
#  nằm sẵn ở `created_at` của chính dòng nhật ký.
NOISE_COLUMNS = frozenset({"updated_at"})

#  ⚠️ `tab_user` theo luật NGƯỢC: cấm hết, trừ những cột nêu tên ở đây (§6).
#  Bảng đó chứa `password_hash`, `google_sub` — thứ mà lọt một lần là nằm trong
#  một bảng CHỈ-THÊM cho tới lúc hết hạn lưu. Cấm-trừ-khi-cho-phép nghĩa là
#  thêm một cột bí mật vào `tab_user` sau này thì nó tự động an toàn, không phải
#  nhớ đi khai thêm. `email` được phép vì đổi email đăng nhập là đúng loại việc
#  cần để lại dấu, và nó không phải bí mật.
TABLE_FIELD_ALLOWLIST = {
    "tab_user": frozenset({
        "id", "email", "employee_id", "is_active", "notify_email",
        "token_version", "avatar_file_id", "created_by", "updated_by",
    }),
}


@dataclass
class PendingChange:
    """Một thay đổi đã flush nhưng CHƯA chắc sống sót — xem luật 4 ở đầu tệp."""

    table_name: str
    op: int
    row_id: int = 0
    field: str = ""
    before_value: str | None = None
    after_value: str | None = None
    snapshot: dict | None = None
    is_masked: bool = False
    #  Dòng GỘP của nhập liệu hàng loạt: không chi tiết, chỉ con số.
    agg_count: int = 0
    #  Ai đẻ ra nó — để `after_commit` / `after_rollback` của ĐÚNG phiên đó xử.
    owner: int = 0
    committed: bool = False
    #  Bản ghi vừa thêm chưa có khóa chính cho tới `after_flush`. Giữ tạm tham
    #  chiếu rồi bỏ ngay sau khi điền, đừng để nó sống hết request.
    pending_obj: object = dc_field(default=None, repr=False)


# --------------------------------------------------------------------------
# Đọc giá trị
# --------------------------------------------------------------------------
def _stringify(value) -> str | None:
    """Giá trị bất kỳ -> chuỗi để so bằng mắt. `None` giữ nguyên `None`.

    Giữ `None` chứ không đổi thành `""`: *"ô này chưa ai nhập"* và *"ô này bị
    xóa trắng"* là hai chuyện khác nhau, và đó chính là loại chi tiết mà người
    mở nhật ký ra đang đi tìm.
    """
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.hex()[:MAX_VALUE_LEN]
    if isinstance(value, (datetime, date, Decimal)):
        return str(value)
    text = value if isinstance(value, str) else str(value)
    if len(text) > MAX_VALUE_LEN:
        return text[:MAX_VALUE_LEN] + "…(cắt)"
    return text


def _is_allowed(table_name: str, column: str) -> bool:
    """Cột này có được ghi GIÁ TRỊ không (tên cột thì luôn được ghi)."""
    allow = TABLE_FIELD_ALLOWLIST.get(table_name)
    if allow is not None and column not in allow:
        return False
    return not is_sensitive_column(column)


def _snapshot(state, table_name: str) -> dict:
    """Chụp cả bản ghi, ĐÃ CHE — dùng cho `op = 1` / `op = 3`.

    Chỉ đi trên cột, không đụng quan hệ: chạm vào một `relationship` ở đây là
    kéo thêm truy vấn xuống DB ngay giữa `before_flush`.
    """
    out: dict = {}
    for prop in state.mapper.column_attrs:
        column = prop.columns[0].name
        if column in NOISE_COLUMNS:
            continue
        if not _is_allowed(table_name, column):
            out[column] = "***"
            continue
        out[column] = _stringify(getattr(state.obj(), prop.key, None))
    return out


def _fetch_old_values(session, state, columns: list[str]) -> dict:
    """Đọc giá trị CŨ thẳng từ DB cho những cột không còn trong bộ nhớ.

    Vì sao cần: giá trị cũ chỉ nằm sẵn trong `history` khi thuộc tính đã được
    nạp. Bản ghi vừa đi qua một `commit` trong cùng phiên thì mọi cột **hết
    hạn**, và lúc gán đè SQLAlchemy không đọc lại — nó ghi nhận giá trị cũ là
    "không có". Dòng nhật ký khi đó chỉ còn nửa câu chuyện ("đổi thành 15000",
    không nói đổi từ đâu), đúng nửa mà BM-005 đang phải đóng.

    Chạy được ở đây vì `before_flush` đứng TRƯỚC câu `UPDATE`, nên dưới DB vẫn
    là giá trị cũ. Một truy vấn cho cả bản ghi, và chỉ khi có cột thật sự đổi mà
    thiếu giá trị cũ — luồng thường (nạp -> sửa -> lưu) không chạm vào đây.
    """
    from sqlalchemy import select

    table = state.mapper.local_table
    row_id = _row_id(state)
    if table is None or not row_id:
        return {}
    wanted = [c for c in columns if c in table.c]
    if not wanted:
        return {}
    stmt = select(*[table.c[c] for c in wanted]).where(state.mapper.primary_key[0] == row_id)
    row = session.connection().execute(stmt).first()
    if row is None:
        return {}
    return dict(zip(wanted, row))


def _row_id(state) -> int:
    """Khóa chính dạng số; khóa ghép thì lấy cột đầu, không có thì 0."""
    try:
        pk_col = state.mapper.primary_key[0]
        key = state.mapper.get_property_by_column(pk_col).key
        return int(getattr(state.obj(), key, 0) or 0)
    except (AttributeError, TypeError, ValueError, IndexError):
        return 0


# --------------------------------------------------------------------------
# Bộ đệm
# --------------------------------------------------------------------------
def _detail_count(ctx) -> int:
    return sum(1 for e in ctx.changes if not e.agg_count)


def _add_aggregate(ctx, owner: int, table_name: str, op: int) -> None:
    """Cộng một vạch vào dòng GỘP của (bảng, thao tác) — bẫy 3 ở §6.

    Chỉ gộp vào dòng CHƯA commit: dòng đã đóng dấu là một sự thật đã chốt, cộng
    thêm vào nó là sửa lại quá khứ.
    """
    for entry in reversed(ctx.changes):
        if (entry.agg_count and entry.owner == owner and not entry.committed
                and entry.table_name == table_name and entry.op == op):
            entry.agg_count += 1
            return
    ctx.changes.append(PendingChange(table_name=table_name, op=op, owner=owner, agg_count=1))


def _should_aggregate(ctx) -> bool:
    return ctx.actor_kind == ACTOR_KIND_SCRIPT or _detail_count(ctx) >= MAX_DETAIL_CHANGES


def _collect(session, ctx) -> None:
    """Duyệt `new` / `dirty` / `deleted`, gom vào `ctx.changes`."""
    owner = id(session)
    aggregate = _should_aggregate(ctx)

    for obj in session.new:
        table_name = getattr(obj, "__tablename__", "")
        if not table_name or table_name in NO_LOG_TABLES:
            continue
        if aggregate:
            _add_aggregate(ctx, owner, table_name, CHANGE_OP_ADD)
            continue
        state = inspect(obj)
        ctx.changes.append(PendingChange(
            table_name=table_name, op=CHANGE_OP_ADD, owner=owner,
            snapshot=_snapshot(state, table_name), pending_obj=obj,
        ))

    for obj in session.deleted:
        table_name = getattr(obj, "__tablename__", "")
        if not table_name or table_name in NO_LOG_TABLES:
            continue
        if aggregate:
            _add_aggregate(ctx, owner, table_name, CHANGE_OP_DELETE)
            continue
        state = inspect(obj)
        ctx.changes.append(PendingChange(
            table_name=table_name, op=CHANGE_OP_DELETE, owner=owner,
            row_id=_row_id(state), snapshot=_snapshot(state, table_name),
        ))

    for obj in session.dirty:
        table_name = getattr(obj, "__tablename__", "")
        if not table_name or table_name in NO_LOG_TABLES:
            continue
        if not session.is_modified(obj, include_collections=False):
            #  Nằm trong `dirty` không có nghĩa là ĐÃ đổi: chỉ cần chạm vào một
            #  thuộc tính là bản ghi vào danh sách này. Không lọc thì mỗi lượt
            #  đọc-rồi-lưu đẻ một nắm dòng "sửa" mà không ô nào khác đi.
            continue
        state = inspect(obj)
        row_id = _row_id(state)
        changed: list[tuple[str, object]] = []
        for prop in state.mapper.column_attrs:
            column = prop.columns[0].name
            if column in NOISE_COLUMNS:
                continue
            history = state.attrs[prop.key].history
            if history.has_changes():
                changed.append((column, history))
        if not changed:
            continue
        if aggregate:
            for _ in changed:
                _add_aggregate(ctx, owner, table_name, CHANGE_OP_UPDATE)
            continue

        #  Gom một lần cho cả bản ghi rồi hỏi DB một câu, đừng hỏi từng cột.
        missing = [column for column, history in changed if not history.deleted]
        old_values: dict = {}
        if missing:
            try:
                old_values = _fetch_old_values(session, state, missing)
            except Exception:  # noqa: BLE001
                log.warning("Không đọc lại được giá trị cũ của %s#%s", table_name, row_id,
                            exc_info=True)

        for column, history in changed:
            allowed = _is_allowed(table_name, column)
            before = history.deleted[0] if history.deleted else old_values.get(column)
            ctx.changes.append(PendingChange(
                table_name=table_name, op=CHANGE_OP_UPDATE, owner=owner, row_id=row_id,
                field=column[:64],
                before_value=_stringify(before) if allowed else None,
                after_value=(_stringify(history.added[0]) if history.added and allowed else None),
                is_masked=not allowed,
            ))


# --------------------------------------------------------------------------
# Sự kiện
# --------------------------------------------------------------------------
def _before_flush(session, flush_context, instances) -> None:
    ctx = get_context()
    if ctx is None:
        #  Không có ngữ cảnh thì không có `request_id` để nối, và cũng không có
        #  ai đứng ra ghi bộ đệm ở cuối. Việc nền / script muốn được ghi thì mở
        #  ngữ cảnh bằng `request_context.open_context(...)`.
        return
    try:
        _collect(session, ctx)
    except Exception:  # noqa: BLE001 — nhật ký hỏng thì nghiệp vụ vẫn phải chạy
        log.warning("Không gom được thay đổi cho nhật ký", exc_info=True)


def _after_flush(session, flush_context) -> None:
    """Điền khóa chính cho bản ghi vừa THÊM — trước flush nó chưa có."""
    ctx = get_context()
    if ctx is None:
        return
    for entry in ctx.changes:
        if entry.pending_obj is None:
            continue
        try:
            entry.row_id = _row_id(inspect(entry.pending_obj))
        except Exception:  # noqa: BLE001
            entry.row_id = 0
        entry.pending_obj = None


def _after_commit(session) -> None:
    """Đóng dấu: tới đây thay đổi mới là thật (luật 4 ở đầu tệp)."""
    ctx = get_context()
    if ctx is None:
        return
    owner = id(session)
    for entry in ctx.changes:
        if entry.owner == owner:
            entry.committed = True


def _drop_uncommitted(session) -> None:
    ctx = get_context()
    if ctx is None:
        return
    owner = id(session)
    ctx.changes = [e for e in ctx.changes if e.committed or e.owner != owner]


def _after_rollback(session) -> None:
    _drop_uncommitted(session)


def _after_soft_rollback(session, previous_transaction) -> None:
    _drop_uncommitted(session)


def record_change(session, table_name: str, row_id: int, field: str,
                  before, after, masked: bool = False) -> None:
    """Ghi tay MỘT dòng trước/sau — dành cho bảng mà lớp tự động nói không nên lời.

    Lớp ORM ghi theo TÊN CỘT, và điều đó đúng với mọi bảng có mỗi cột một ý
    nghĩa. Bảng KHÓA-GIÁ TRỊ thì không: `tab_setting` chỉ có `skey` và `svalue`,
    nên dòng tự động đọc ra *"tab_setting#7 svalue: false -> true"* — biết có
    người đổi một thứ gì đó, không biết thứ gì. Mà nguyên giá trị của quyển sổ
    này là trả lời được câu "ai đổi cái gì".

    Nên những bảng đó tự khai vào `NO_LOG_TABLES` rồi gọi hàm này với `field` là
    khóa THẬT. Đổi lại thì tầng gọi phải tự lo đúng hai việc lớp tự động lo hộ:
    đọc giá trị cũ TRƯỚC khi ghi đè, và tự quyết có che hay không.

    Vẫn đi chung đường ống với dòng tự động — cùng bộ đệm, cùng `request_id`,
    cùng luật "chỉ ghi thứ đã commit". Quay đầu giao dịch là dòng này mất theo,
    đúng như thế.
    """
    ctx = get_context()
    if ctx is None:
        return
    ctx.changes.append(PendingChange(
        table_name=table_name, op=CHANGE_OP_UPDATE, owner=id(session), row_id=row_id,
        field=str(field)[:64],
        before_value=_stringify(before) if not masked else None,
        after_value=_stringify(after) if not masked else None,
        is_masked=masked,
    ))


_INSTALLED = False


def install_change_tracker() -> None:
    """Gắn bộ nghe vào lớp `Session` — mọi phiên đều đi qua, gọi lại được."""
    global _INSTALLED
    if _INSTALLED:
        return
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_flush", _after_flush)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    event.listen(Session, "after_soft_rollback", _after_soft_rollback)
    _INSTALLED = True


# --------------------------------------------------------------------------
# Ghi bộ đệm — gọi MỘT lần ở cuối lượt gọi
# --------------------------------------------------------------------------
def _to_row(ctx, entry):
    from app.modules.change_log.model import ChangeLog

    snapshot = entry.snapshot
    if entry.agg_count:
        #  Dòng gộp: không có bản ghi nào để chụp, chỉ có con số. Nói rõ bằng
        #  cờ `_aggregated` để màn đọc (P5) không bày nó ra như một thay đổi lẻ.
        snapshot = {"_aggregated": True, "rows": entry.agg_count}
    return ChangeLog(
        created_by=ctx.user_id,
        request_id=ctx.request_id or None,
        session_id=ctx.session_id,
        table_name=entry.table_name[:64],
        row_id=entry.row_id,
        op=entry.op,
        field=entry.field[:64],
        before_value=entry.before_value,
        after_value=entry.after_value,
        snapshot_json=snapshot,
        is_masked=entry.is_masked,
    )


def _backfill_audit(db, ctx, entries) -> None:
    """Chép `changed_fields` / `change_count` lên dòng audit cùng `request_id`.

    Cố ý LẶP dữ liệu: dòng thời gian của một phiếu cần hiện "Sửa: đơn giá, số
    lượng" cho vài chục dòng một lúc, và đọc một cột phẳng rẻ hơn nhiều so với
    join sang bảng vài triệu dòng.

    Ghép theo quy ước `tab_<entity>` — quy ước đó đúng với gần hết bảng, và chỗ
    nào không đúng thì **không ghép**, chứ không đoán: một dòng audit mang tên
    trường của bảng khác thì tệ hơn hẳn một dòng audit để trống.
    """
    from app.modules.audit.model import AuditLog

    if not ctx.request_id:
        return
    by_row: dict[tuple[str, int], list[str]] = {}
    for entry in entries:
        if entry.op != CHANGE_OP_UPDATE or not entry.field or not entry.row_id:
            continue
        by_row.setdefault((entry.table_name, entry.row_id), []).append(entry.field)
    if not by_row or len(by_row) > MAX_AUDIT_BACKFILL_ROWS:
        return
    for (table_name, row_id), fields in by_row.items():
        if not table_name.startswith("tab_"):
            continue
        entity = table_name[4:]
        (db.query(AuditLog)
         .filter(AuditLog.request_id == ctx.request_id,
                 AuditLog.entity == entity,
                 AuditLog.entity_id == row_id)
         .update({AuditLog.changed_fields: ", ".join(fields)[:500],
                  AuditLog.change_count: min(len(fields), 32767)},
                 synchronize_session=False))


def flush_changes(ctx) -> int:
    """Ghi cả bộ đệm xuống `tab_change_log`. Trả về số dòng đã ghi.

    Mở phiên RIÊNG, cùng lẽ với `_write` của middleware: dòng nhật ký không
    được sống chết theo giao dịch nghiệp vụ, và tới đây thì giao dịch ấy đã
    đóng rồi. Hỏng thì nuốt lỗi — ghi nhật ký hỏng không được làm sập lượt gọi.
    """
    if ctx is None or not ctx.changes:
        return 0
    entries = [e for e in ctx.changes if e.committed]
    #  Dọn sạch kể cả phần chưa commit: chúng là thay đổi đã bị quay đầu, giữ
    #  lại thì lượt gọi sau trong cùng ngữ cảnh (Celery chạy vòng) vớ phải.
    ctx.changes = []
    if not entries:
        return 0

    from app.core.database import SessionLocal

    db = None
    written = 0
    try:
        db = SessionLocal()
        for entry in entries:
            db.add(_to_row(ctx, entry))
        written = len(entries)
        _backfill_audit(db, ctx, entries)
        db.commit()
    except Exception:  # noqa: BLE001
        log.warning("Không ghi được tab_change_log (%s dòng)", len(entries), exc_info=True)
        written = 0
        if db is not None:
            db.rollback()
    finally:
        if db is not None:
            db.close()
    ctx.change_count = min(ctx.change_count + written, 32767)
    return written
