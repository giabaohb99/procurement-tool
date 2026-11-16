"""ÁP chế độ "Cộng dần sau mỗi tháng làm đủ" cho loại Phép năm và TÍNH LẠI quỹ năm nay (duoc-CR-762).

Làm hai việc trong MỘT giao dịch:
  1. Đặt `accrual_mode` của loại nghỉ mã `annual` (Phép năm) = MONTHLY_AFTER.
  2. Với mọi dòng quỹ của loại đó ở năm HIỆN TẠI (giờ Việt Nam), tính lại `allocated_days` theo ngày làm chính thức
     (`accrual_start_service`: HĐLĐ đầu tiên đã ký không phải Thử việc; chỉ có HĐ Thử việc hoặc hồ sơ Thử việc thì 0;
     không có HĐ nào thì `hire_date`) bằng hàm dùng chung `accrual_refresh_service.refresh_monthly_after_allocation`
     (cũng là hàm chạy tự động khi ký HĐLĐ / đổi hình thức nhân viên): đường cấp quỹ của `ensure_balance` và hàm ghi
     của duoc-CR-717, nên nhật ký `leave_balance` giống hệt. KHÔNG đụng thâm niên / mang sang / điều chỉnh / nghỉ bù / đã dùng / giữ chỗ / đã thanh toán,
     KHÔNG đụng năm đã qua.

Chạy lại bao nhiêu lần cũng được (lần sau không còn dòng nào đổi). `--dry-run` làm đúng từng bước rồi HOÀN TÁC giao dịch,
chỉ in bảng so sánh.

Chạy: docker compose exec -T api python -m scripts.apply_monthly_after_annual_leave [--dry-run] [--all] [--code annual]
"""
import argparse
import sys
from dataclasses import dataclass
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.vn_time import vn_today
from app.modules.leave.constants import LEAVE_ACCRUAL_STATUS_LABELS, LeaveAccrualStatus

DEFAULT_CODE = "annual"
ACTOR = 0   # script vận hành, cùng quy ước các script khác


@dataclass
class Line:
    code: str
    name: str
    old: float
    new: float
    available: float
    spent: float            # đã dùng + đang giữ chỗ
    official_start: object  # ngày làm chính thức (hoặc hire_date) hoặc None
    accruing: bool
    missing_contract: bool
    status_label: str = ""
    incomplete: bool = False
    #  Số đã cấp khác số mà CHẾ ĐỘ CŨ sẽ cấp hôm nay với hạn mức hiện hành → hạn mức đã đổi kể từ lúc cấp quỹ,
    #  nên một phần chênh lệch không do chế độ / mốc tích mới.
    quota_drift: bool = False

    @property
    def negative(self) -> bool:
        return self.available < 0


def _old_mode_value(db: Session, leave_type, old_mode: int, employee, year: int) -> float:
    """`allocated_days` mà CHẾ ĐỘ CŨ sẽ cấp hôm nay với hạn mức hiện hành (cùng đường cấp quỹ, chỉ đổi chế độ)."""
    from app.modules.leave import policy_allocation

    stand_in = SimpleNamespace(id=leave_type.id, accrual_mode=old_mode, annual_quota_days=leave_type.annual_quota_days)
    return policy_allocation.allocated_days(db, stand_in, employee, year)


def run(db: Session, code: str = DEFAULT_CODE, *, dry_run: bool) -> tuple[list[Line], dict]:
    """Làm việc trong phiên `db`; commit khi thật, rollback khi `dry_run`. Trả (các dòng, tổng hợp)."""
    from app.modules.leave import balance_service
    from app.modules.leave.accrual_refresh_service import refresh_monthly_after_allocation
    from app.modules.leave.catalog_model import LeaveType
    from app.modules.leave.constants import LEAVE_ACCRUAL_MODE_LABELS, LeaveAccrualMode

    leave_type = db.query(LeaveType).filter(LeaveType.code == code).first()
    if leave_type is None:
        raise SystemExit(f"Không có loại nghỉ mã '{code}'.")
    year = vn_today().year
    target = int(LeaveAccrualMode.MONTHLY_AFTER)
    summary = {"leave_type": leave_type.name, "year": year, "mode_changed": False}
    old_mode = int(leave_type.accrual_mode or 1)

    try:
        if int(leave_type.accrual_mode or 1) != target:
            old_label = LEAVE_ACCRUAL_MODE_LABELS.get(int(leave_type.accrual_mode or 1), "?")
            leave_type.accrual_mode = target
            db.flush()     # các truy vấn của hàm làm mới phải thấy chế độ mới (phiên tắt autoflush)
            audit_record(db, ACTOR, "leave_type", leave_type.id, "update",
                         f"Đổi cách cấp quỹ của {leave_type.name}: {old_label} → "
                         f"{LEAVE_ACCRUAL_MODE_LABELS[LeaveAccrualMode.MONTHLY_AFTER]}", commit=False)
            summary["mode_changed"] = True

        #  Cùng hàm với hai chỗ tự làm mới (ký HĐLĐ, đổi hình thức nhân viên): tính lại quỹ năm nay của loại này.
        items = refresh_monthly_after_allocation(
            db, None, leave_type_ids=[leave_type.id], actor=ACTOR,
            label="Chuyển Phép năm sang cộng dần sau mỗi tháng làm đủ (duoc-CR-762)")
        lines = [Line(
            code=it.employee.code or str(it.employee.id), name=it.employee.full_name or "", old=it.old, new=it.new,
            available=balance_service.available_days(db, it.balance, leave_type=leave_type, accrual_start=it.start),
            spent=round(float(it.balance.used_days or 0.0) + float(it.balance.pending_days or 0.0), 2),
            official_start=it.start.start, accruing=it.start.accruing, missing_contract=it.start.missing_contract,
            status_label=LEAVE_ACCRUAL_STATUS_LABELS[LeaveAccrualStatus(it.start.status_at())],
            incomplete=it.start.incomplete,
            quota_drift=summary["mode_changed"] and it.changed
            and abs(it.old - _old_mode_value(db, leave_type, old_mode, it.employee, it.balance.year)) > 1e-9)
            for it in items if it.balance.year == year]
        #  Dòng quỹ NĂM SAU (nếu đã cấp sớm) cũng được tính lại nhưng không đưa vào bảng — bảng nói về năm nay.
        summary["future_rows"] = len(items) - len(lines)
    except BaseException:
        db.rollback()
        raise

    summary.update({
        "balances": len(lines),
        "changed": sum(1 for ln in lines if abs(ln.old - ln.new) > 1e-9),
        "unchanged": sum(1 for ln in lines if abs(ln.old - ln.new) <= 1e-9),
        "not_accruing": sum(1 for ln in lines if not ln.accruing),
        "missing_contract": sum(1 for ln in lines if ln.missing_contract),
        "negative": sum(1 for ln in lines if ln.negative),
        "incomplete": sum(1 for ln in lines if ln.incomplete),
        "quota_drift": sum(1 for ln in lines if ln.quota_drift),
    })
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return lines, summary


def render(lines: list[Line], summary: dict, *, dry_run: bool, show_all: bool = False) -> str:
    """Bảng Markdown. Mặc định chỉ dòng ĐÁNG CHÚ Ý (đổi hạn mức, âm, chưa tích); `show_all` in cả dòng giữ nguyên."""
    out = [f"# {'[DRY-RUN] ' if dry_run else ''}{summary['leave_type']} năm {summary['year']} -> cộng dần sau mỗi tháng làm đủ",
           "", "| Mã NV | Họ tên | Cũ | Mới | Dùng được hôm nay | Đã dùng + giữ chỗ | Mốc tích | Ghi chú |",
           "|---|---|---:|---:|---:|---:|---|---|"]
    shown = 0
    for ln in sorted(lines, key=lambda x: x.code):
        if not (show_all or abs(ln.old - ln.new) > 1e-9 or ln.negative or not ln.accruing or ln.incomplete):
            continue
        shown += 1
        notes = []
        if ln.negative:
            notes.append("ÂM")
        if ln.status_label and ln.status_label != LEAVE_ACCRUAL_STATUS_LABELS[LeaveAccrualStatus.ACCRUING]:
            notes.append(ln.status_label)      # thử việc / chưa có HĐ / lịch sử HĐ chưa đủ / HĐ dịch vụ / chưa tới ngày
        if ln.quota_drift:
            notes.append("hạn mức hiện hành khác số đã cấp")
        start = ln.official_start.strftime("%d/%m/%Y") if ln.official_start else "-"
        out.append(f"| {ln.code} | {ln.name} | {ln.old:g} | {ln.new:g} | {ln.available:g} | {ln.spent:g} | {start} "
                   f"| {', '.join(notes)} |")
    out += ["", f"(Hiện {shown}/{len(lines)} dòng; thêm --all để in đủ)" if shown < len(lines) else "", "Tổng hợp:",
            f"- Đổi cách cấp quỹ của loại: {'có' if summary['mode_changed'] else 'không (đã đúng)'}",
            f"- Dòng quỹ xét: {summary['balances']}  (đổi hạn mức: {summary['changed']}, giữ nguyên: {summary['unchanged']})",
            f"- Chưa tích (thử việc / hợp đồng dịch vụ): {summary['not_accruing']}",
            f"- Chưa có HĐLĐ chính thức trên hệ thống: {summary['missing_contract']}",
            f"- Lịch sử HĐLĐ chưa đủ (tính từ ngày vào làm): {summary['incomplete']}",
            f"- Số đã cấp khác số chế độ cũ sẽ cấp hôm nay (hạn mức hiện hành đã đổi): {summary['quota_drift']}",
            f"- Số dùng được hôm nay ÂM: {summary['negative']}",
            f"- Dòng quỹ năm sau cũng được tính lại: {summary.get('future_rows', 0)}"]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="làm thử rồi hoàn tác, chỉ in bảng")
    ap.add_argument("--all", action="store_true", help="in cả dòng không đổi")
    ap.add_argument("--code", default=DEFAULT_CODE, help="mã loại nghỉ (mặc định annual)")
    args = ap.parse_args(argv)

    import app.core.all_models  # noqa: F401
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        lines, summary = run(db, args.code, dry_run=args.dry_run)
        sys.stdout.write(render(lines, summary, dry_run=args.dry_run, show_all=args.all) + "\n")
        print("[DRY-RUN] Không ghi gì." if args.dry_run else "[APPLY] Đã ghi và commit.", file=sys.stderr)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
