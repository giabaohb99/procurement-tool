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

Phân vùng theo năm + `DROP PARTITION` (§9) để đợt sau — cần đổi cấu trúc bảng.
"""
import logging
from datetime import datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.logging_policy import (CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES,
                                     LOG_RETENTION_MONTHS)
from app.core.storage import env_prefix, key_exists
from app.modules.audit.tasks import ARCHIVE_TABLES
from app.modules.login_session.model import LoginSession

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


def cleanup_expired(db: Session, *, now: datetime, months: int = 0,
                    dry_run: bool = False) -> dict:
    """Dọn bốn bảng theo tháng, mỗi tháng của mỗi bảng phải có gói R2 trước.

    `dry_run=True` chỉ đếm và kiểm gói, không xóa. Trả về số dòng theo bảng,
    danh sách `bảng:tháng` bị bỏ qua vì thiếu gói, và cờ chạm trần số lô.
    """
    cutoff = retention_cutoff(now, months)
    deleted: dict[str, int] = {}
    matched: dict[str, int] = {}
    skipped: list[str] = []
    budget = CLEANUP_MAX_BATCHES
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
            "deleted": deleted, "matched": matched, "skipped": skipped}
