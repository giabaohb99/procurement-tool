"""Gom cảnh báo công nợ quá hạn / sắp đến hạn — bao-CR-542.

Khoản nợ sinh theo TỪNG DÒNG HÀNG của từng lần giao (`Payable`: 1 dòng = 1 lần giao × 1 luồng),
nên một đơn 5 dòng nhận cùng ngày đẻ 5 khoản cùng NCC, cùng hạn. Trước CR này chuông và tab
Việc cần làm báo mỗi khoản một dòng → đại ca thấy «Công nợ QUÁ HẠN … PO00003» lặp 5 lần y hệt,
và muốn ẩn thì phải bấm «Đánh dấu làm hết» 5 lần.

Nay gom theo **đơn + bên được trả** (luồng `source_type` + mã đối tượng: NCC bán hàng, đơn vị vận
chuyển, bên của dòng chi phí) và theo **mức** (quá hạn / sắp đến hạn tách riêng). Mỗi nhóm một
dòng, ghi số khoản, tổng còn nợ, số ngày trễ tính từ hạn SỚM NHẤT trong nhóm.

Hạn trả không đổi: `Payable.due_date` = ngày nhận + số ngày công nợ của đơn/NCC
(`payable.service.upsert` + `debt_days`).

⚠️ **Khóa nhóm = `payable:{id lớn nhất trong nhóm}:{mức}`** — cùng khuôn khóa một khoản cũ:
  · nhóm một khoản ra ĐÚNG khóa cũ → việc người dùng đã «Đánh dấu làm hết» vẫn ẩn;
  · nhóm có thêm khoản nợ MỚI (id lớn hơn) → khóa đổi → cảnh báo nổi lại, không bị chôn
    dưới một lần đánh dấu cũ.
Chuông (`alert.controller.build`) và tab Việc cần làm (`dashboard.build_my_tasks`) PHẢI cùng gọi
hàm này — tab là tập cha của chuông (`test_viec_can_lam_dismiss.py`).
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

LEVEL_DANGER = "danger"
LEVEL_WARN = "warn"
WARN_DAYS = 3

#  Luồng nợ không phải hàng của NCC thì ghi kèm cho khỏi nhầm với nợ hàng của cùng đơn.
_SOURCE_SUFFIX = {"shipping": " (vận chuyển)", "import_cost": " (chi phí)"}


@dataclass
class PayableAlertGroup:
    level: str
    po_id: int
    po_code: str
    source_type: str
    supplier_code: str
    supplier_name: str
    due_date: str                 # hạn SỚM NHẤT trong nhóm (YYYY-MM-DD)
    days: int                     # quá hạn: số ngày trễ; sắp đến hạn: số ngày còn lại
    remaining: float = 0.0
    ids: list[int] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.ids)

    @property
    def key(self) -> str:
        return f"payable:{max(self.ids)}:{self.level}"

    @property
    def party(self) -> str:
        return (self.supplier_name or self.supplier_code) + _SOURCE_SUFFIX.get(self.source_type, "")

    def detail(self) -> str:
        """«5 khoản · còn nợ 12.345.000 đ · trễ 27 ngày (hạn 04/09/2026)» — dùng cho cả chuông lẫn tab."""
        parts = [f"{self.count} khoản"] if self.count > 1 else []
        parts.append(f"còn nợ {format_money(self.remaining)} đ")
        if self.level == LEVEL_DANGER:
            parts.append(f"trễ {self.days} ngày")
        else:
            parts.append("đến hạn hôm nay" if self.days == 0 else f"còn {self.days} ngày")
        return " · ".join(parts) + f" (hạn {format_date(self.due_date)})"

    def title(self) -> str:
        head = "Công nợ QUÁ HẠN" if self.level == LEVEL_DANGER else "Công nợ sắp đến hạn"
        where = f"{self.party} · {self.po_code}" if self.po_code else self.party
        return f"{head}: {where} — {self.detail()}"


def format_money(value: float) -> str:
    return f"{float(value or 0):,.0f}".replace(",", ".")


def format_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return value or ""


def group_due_payables(payables, today: date | None = None, warn_days: int = WARN_DAYS) -> list[PayableAlertGroup]:
    """Khoản nợ CHƯA TRẢ ĐỦ (người gọi đã lọc trạng thái + phạm vi) → nhóm cảnh báo.

    Thứ tự: quá hạn trước, trong cùng mức thì hạn sớm hơn trước. Khoản không có hạn hoặc chưa
    tới mốc cảnh báo thì bỏ.
    """
    today = today or datetime.now().date()
    today_s = today.strftime("%Y-%m-%d")
    warn_until = (today + timedelta(days=warn_days)).strftime("%Y-%m-%d")
    groups: dict[tuple, PayableAlertGroup] = {}
    for p in payables:
        due = p.due_date or ""
        if not due:
            continue
        if due < today_s:
            level = LEVEL_DANGER
        elif due <= warn_until:
            level = LEVEL_WARN
        else:
            continue
        gk = (level, int(p.po_id or 0), p.source_type or "", p.supplier_code or "")
        g = groups.get(gk)
        if g is None:
            g = groups[gk] = PayableAlertGroup(
                level=level, po_id=int(p.po_id or 0), po_code=p.po_code or "", source_type=p.source_type or "",
                supplier_code=p.supplier_code or "", supplier_name=p.supplier_name or "", due_date=due, days=0)
        g.ids.append(int(p.id))
        g.remaining += float(p.remaining or 0)
        if due < g.due_date:
            g.due_date = due
    for g in groups.values():
        try:
            due_day = datetime.strptime(g.due_date, "%Y-%m-%d").date()
        except ValueError:
            #  Hạn gõ tay sai khuôn (ô «Hạn thanh toán» của dòng chi phí) — vẫn báo, không đếm ngày.
            continue
        g.days = (today - due_day).days if g.level == LEVEL_DANGER else (due_day - today).days
    return sorted(groups.values(), key=lambda g: (g.level != LEVEL_DANGER, g.due_date, g.po_code))
