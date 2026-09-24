"""Dọn bốn bảng nhật ký quá 16 tháng — CHỈ tháng nào đã có gói trên R2 (bao-CR-448, CR-312 P6).

Luật §9 của `nhat-ky-va-phien-dang-nhap.md`, và đây là luật cứng: **gói xong
mới xóa**. Việc đóng gói (`audit.archive`) chép cả bốn bảng của tháng trước lên
R2 kèm tệp `.sha256`; việc này xóa theo TỪNG THÁNG, và trước khi xóa tháng nào
của bảng nào thì hỏi R2 xem tệp `.sha256` của đúng tháng đó, bảng đó có chưa.
Chưa có thì bỏ qua tháng đó, ghi cảnh báo, và để nguyên — một bản duy nhất của
nhật ký nằm trên chính máy bị tấn công thì không phải bản sao, nhưng vẫn hơn
không có bản nào.

Mốc 16 tháng làm tròn về ĐẦU THÁNG: hôm nay 21/09/2026 thì mốc là 01/05/2025,
xóa những dòng thuộc tháng 04/2025 trở về trước. Làm tròn để đơn vị xóa trùng
đơn vị gói; xóa lẻ nửa tháng là nửa tháng đó có gói mà không tra được nữa
trong DB, còn nửa kia thì ngược lại.

Phiên đăng nhập xét theo lúc ĐÓNG (`revoked_at`, hoặc `expires_at` với phiên
không ai đăng xuất) nhưng gom tháng theo lúc MỞ, vì gói R2 gom theo
`created_at`. Phiên sống tối đa 7 ngày nên hai mốc cách nhau không quá một tháng.

**Đợt 2 (`bao-CR-454`) thêm đường bỏ CẢ NĂM bằng `DROP PARTITION`** — xem
`partition.py`. Hai đường sống cạnh nhau chứ không thay nhau, vì chúng dọn hai
phần khác nhau của cùng một mốc: mốc 16 tháng luôn rơi vào GIỮA một năm, nên
năm nằm trọn bên ngoài thì bỏ nguyên phân vùng, còn mấy tháng đầu của năm bị
mốc cắt đôi thì vẫn phải xóa theo dòng. Chạy phân vùng trước cho rẻ, rồi vòng
xóa theo tháng quét phần còn lại — năm đã bỏ phân vùng thì vòng sau không còn
dòng nào để đếm.
"""
import logging
from datetime import datetime

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.logging_policy import (CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES,
                                     LOG_RETENTION_MONTHS)
from app.core.storage import env_prefix, key_exists
from app.modules.audit.tasks import ARCHIVE_TABLES
from app.modules.login_session.model import LoginSession

from . import partition

log = logging.getLogger("app.system_log.retention")


def month_start(when: datetime) -> datetime:
    return when.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def shift_months(month: datetime, delta: int) -> datetime:
    """Đầu tháng `month` dịch đi `delta` tháng (âm là lùi)."""
    index = month.year * 12 + (month.month - 1) + delta
    return month.replace(year=index // 12, month=index % 12 + 1)


def retention_cutoff(now: datetime, months: int = 0) -> datetime:
    return shift_months(month_start(now), -(months or LOG_RETENTION_MONTHS))


def archive_marker_key(label: str, name: str) -> str:
    """Tệp `.sha256` mà `audit.archive` để lại cho bảng `name` tháng `label`."""
    return f"{env_prefix()}/log-archive/{label}/{name}.jsonl.gz.sha256"


def _expired_condition(model, cutoff: datetime):
    if model is LoginSession:
        return or_((LoginSession.revoked_at.isnot(None)) & (LoginSession.revoked_at < cutoff),
                   (LoginSession.revoked_at.is_(None)) & (LoginSession.expires_at < cutoff))
    return model.created_at < cutoff


def _delete_month(db: Session, model, condition, budget: int) -> tuple[int, int]:
    """Xóa theo lô các dòng khớp `condition`. Trả (số dòng đã xóa, số lô đã dùng)."""
    deleted = 0
    batches = 0
    while batches < budget:
        ids = [row[0] for row in db.execute(
            select(model.id).where(condition).order_by(model.id.asc()).limit(CLEANUP_BATCH_SIZE))]
        if not ids:
            break
        db.execute(delete(model).where(model.id.in_(ids)))
        db.commit()
        deleted += len(ids)
        batches += 1
    return deleted, batches


def year_bounds(year: int) -> tuple[datetime, datetime]:
    return datetime(year, 1, 1), datetime(year + 1, 1, 1)


def find_missing_archive_months(db: Session, model, name: str, year: int) -> list[str]:
    """Tháng nào của `year` CÓ dòng dưới DB mà CHƯA có gói `.sha256` trên R2.

    ⚠️ **Tháng rỗng không tính là thiếu.** `audit.archive` cố ý không đẩy gì lên
    khi tháng đó không có dòng nào (`status: empty`), nên đòi đủ 12 gói theo
    đúng câu chữ §9 thì một năm có một tháng nghỉ là một năm **không bao giờ**
    bỏ được phân vùng. Tháng đang rỗng thì hoặc chưa từng có dòng nào, hoặc đã
    bị vòng xóa theo tháng dọn — mà vòng đó cũng chỉ xóa sau khi thấy gói. Cả
    hai lối đều dẫn tới cùng một kết luận: không có gì để mất.
    """
    missing: list[str] = []
    for month in range(1, 13):
        start = datetime(year, month, 1)
        end = datetime(year + (month // 12), (month % 12) + 1, 1)
        label = f"{start:%Y-%m}"
        if key_exists(archive_marker_key(label, name)):
            continue
        total = db.execute(
            select(func.count()).select_from(model)
            .where(model.created_at >= start, model.created_at < end)).scalar() or 0
        if total:
            missing.append(label)
    return missing


def count_unexpired_in_year(db: Session, model, year: int, cutoff: datetime) -> int:
    """Dòng nào của năm đó CHƯA quá hạn — bỏ phân vùng là bỏ luôn cả chúng.

    Với ba bảng xét theo `created_at` thì con số này luôn là 0 khi cả năm nằm
    ngoài mốc. Nó tồn tại vì bảng thứ tư: `tab_login_session` gom theo lúc MỞ
    nhưng hết hạn theo lúc ĐÓNG, nên trên giấy vẫn có ca một phiên mở cuối năm
    mà tới nay chưa đóng. Phiên sống tối đa 7 ngày nên ca đó gần như không xảy
    ra — nhưng «gần như» không phải thứ để đánh cược với một thao tác không
    hoàn tác được.
    """
    start, end = year_bounds(year)
    in_year = and_(model.created_at >= start, model.created_at < end)

    def count_rows(*conditions) -> int:
        return db.execute(
            select(func.count()).select_from(model).where(*conditions)).scalar() or 0

    #  Đếm bằng HIỆU của hai phép đếm chứ không bằng `NOT (điều kiện hết hạn)`:
    #  điều kiện của phiên đăng nhập so trên hai cột cho phép NULL, mà trong SQL
    #  thì `NOT NULL_3_TRẠNG_THÁI` vẫn ra NULL — dòng đó rơi khỏi CẢ HAI vế và
    #  hàm này báo 0 cho đúng cái dòng nó sinh ra để bắt.
    return count_rows(in_year) - count_rows(in_year, _expired_condition(model, cutoff))


def maintain_partitions(db: Session, *, now: datetime) -> dict[str, list[int]]:
    """Tạo trước phân vùng của năm nay và năm sau cho cả bốn bảng.

    Dòng của năm chưa có phân vùng riêng vẫn ghi được — chúng rơi vào `pmax` —
    nhưng nằm chung một rọ thì **không bỏ riêng năm nào được nữa**. Chạy hằng
    đêm nên tới giao thừa thì phân vùng của năm mới đã đứng sẵn ở đó.
    """
    added: dict[str, list[int]] = {}
    for name, model in ARCHIVE_TABLES:
        years = partition.ensure_year_partitions(db, model.__tablename__, now.year + 1)
        if years:
            added[name] = years
    return added


def drop_expired_partitions(db: Session, *, now: datetime, months: int = 0,
                            dry_run: bool = False) -> dict:
    """Bỏ nguyên phân vùng của những NĂM đã nằm trọn ngoài mốc giữ.

    Ba điều kiện, thiếu một là bỏ qua và ghi cảnh báo: năm đó kết thúc trước
    mốc · mọi tháng có dòng của năm đó đã có gói trên R2 · không còn dòng nào
    của năm đó chưa quá hạn.
    """
    cutoff = retention_cutoff(now, months)
    dropped: list[str] = []
    skipped: list[str] = []
    for name, model in ARCHIVE_TABLES:
        table = model.__tablename__
        for year in partition.list_partition_years(db, table):
            #  Năm kết thúc lúc 01/01 năm sau; mốc đã làm tròn về đầu tháng nên
            #  «cả năm nằm ngoài mốc» rút gọn đúng thành phép so năm này.
            if year >= cutoff.year:
                continue
            missing = find_missing_archive_months(db, model, name, year)
            if missing:
                log.warning("Bỏ qua bỏ phân vùng %s năm %s: thiếu gói R2 của %s.",
                            name, year, ", ".join(missing))
                skipped.append(f"{name}:{year}:thieu-goi")
                continue
            alive = count_unexpired_in_year(db, model, year, cutoff)
            if alive:
                log.warning("Bỏ qua bỏ phân vùng %s năm %s: còn %s dòng chưa quá hạn.",
                            name, year, alive)
                skipped.append(f"{name}:{year}:chua-qua-han")
                continue
            if dry_run:
                dropped.append(f"{name}:{year}")
                continue
            if partition.drop_year_partition(db, table, year):
                dropped.append(f"{name}:{year}")
    return {"dropped": dropped, "skipped": skipped}


def cleanup_expired(db: Session, *, now: datetime, months: int = 0,
                    dry_run: bool = False) -> dict:
    """Dọn bốn bảng theo tháng, mỗi tháng của mỗi bảng phải có gói R2 trước.

    Ba nhịp, theo đúng thứ tự đó: tạo trước phân vùng năm tới · bỏ nguyên phân
    vùng của năm đã quá hạn · xóa theo dòng phần tháng còn lại. Nhịp giữa chạy
    TRƯỚC nhịp cuối để vòng xóa theo tháng không phải đếm lại những gì vừa bỏ.

    `dry_run=True` chỉ đếm và kiểm gói, không xóa và không đụng cấu trúc bảng.
    Trả về số dòng theo bảng, danh sách `bảng:tháng` bị bỏ qua vì thiếu gói, và
    cờ chạm trần số lô.
    """
    cutoff = retention_cutoff(now, months)
    deleted: dict[str, int] = {}
    matched: dict[str, int] = {}
    skipped: list[str] = []
    budget = CLEANUP_MAX_BATCHES
    added_partitions = {} if dry_run else maintain_partitions(db, now=now)
    year_result = drop_expired_partitions(db, now=now, months=months, dry_run=dry_run)
    skipped.extend(year_result["skipped"])
    for name, model in ARCHIVE_TABLES:
        expired = _expired_condition(model, cutoff)
        oldest = db.execute(select(func.min(model.created_at)).where(expired)).scalar()
        if oldest is None:
            continue
        if isinstance(oldest, str):  # SQLite trả chuỗi
            oldest = datetime.fromisoformat(oldest)
        month = month_start(oldest)
        while month < cutoff:
            next_month = shift_months(month, 1)
            in_month = expired & (model.created_at >= month) & (model.created_at < next_month)
            total = db.execute(select(func.count()).select_from(model).where(in_month)).scalar() or 0
            label = f"{month:%Y-%m}"
            if total:
                if not key_exists(archive_marker_key(label, name)):
                    #  Không xóa thứ chưa có bản sao ngoài máy — luật cứng §9.
                    log.warning("Bỏ qua dọn %s tháng %s: chưa có gói R2 (%s dòng giữ nguyên).",
                                name, label, total)
                    skipped.append(f"{name}:{label}")
                elif dry_run:
                    matched[name] = matched.get(name, 0) + int(total)
                elif budget <= 0:
                    skipped.append(f"{name}:{label}:het-lo")
                else:
                    count, used = _delete_month(db, model, in_month, budget)
                    budget -= used
                    deleted[name] = deleted.get(name, 0) + count
                    if budget <= 0 and count < total:
                        skipped.append(f"{name}:{label}:het-lo")
            month = next_month

    capped = any(item.endswith(":het-lo") for item in skipped)
    if capped:
        log.warning("Dọn nhật ký 16 tháng chạm trần %s lô, còn dòng quá hạn chưa xóa.",
                    CLEANUP_MAX_BATCHES)
    status = "dry_run" if dry_run else ("partial" if capped else "success")
    return {"status": status, "cutoff": cutoff.isoformat(),
            "deleted": deleted, "matched": matched, "skipped": skipped,
            "dropped_partitions": year_result["dropped"],
            "added_partitions": added_partitions}
