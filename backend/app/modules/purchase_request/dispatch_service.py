"""YCMH — điều phối (duyệt lần 2 của thu mua) và phân công người thu mua (bao-CR-715 tách từ service.py)."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import is_central_dept
from app.modules.catalog import lead_time

from .model import PurchaseRequest
from .schema import AssignIn
from .base_service import ENTITY, get_pr, items_of, sla_base_date
from .edit_service import apply_auto_urgent


def dispatch_enabled() -> bool:
    """CR-034 — CÔNG TẮC bước duyệt lần 2 (điều phối).

    BẬT (mặc định): phiếu dừng ở 'approved' cho tới khi thu mua bấm duyệt lần 2.
    TẮT: quay về luồng cũ — duyệt phát là phân bổ NSTM luôn, phiếu đi thẳng sang 'dispatched'.
    Nguồn: màn Cấu hình hệ thống (key `pr_dispatch_enabled`, lưu DB) → fallback .env
    (`PR_DISPATCH_ENABLED`). Đổi có hiệu lực ngay, không cần deploy."""
    from app.core import app_settings
    return bool(app_settings.get("pr_dispatch_enabled"))


#  Các khóa `dispatch_context()` đưa vào điều kiện, kèm nhãn tiếng Việt — bao-CR-528. Cửa lưu của màn
#  Cấu hình hệ thống đọc bảng này để chặn điều kiện dùng trường lạ (gõ sai tên trường = điều kiện
#  không bao giờ khớp mà không ai hay). Thêm khóa vào `dispatch_context` thì thêm ở đây, và thêm
#  trường tương ứng ở bộ chọn điều kiện của hai giao diện.
DISPATCH_CONTEXT_FIELDS = {
    "handler_dept_id": "Phòng xử lý",
    "department_id": "Phòng lập phiếu",
    "company_id": "Công ty",
    "requester_id": "Người yêu cầu",
    "is_urgent": "Đơn gấp",
    "line_count": "Số dòng hàng",
}


def dispatch_context(db: Session, pr: PurchaseRequest) -> dict:
    """Bối cảnh phiếu cho điều kiện bỏ qua điều phối — bao-CR-497.

    Một dict PHẲNG, đúng khuôn "bối cảnh phiếu" của bộ máy duyệt chung (`approval/condition_service`),
    để sau này đưa YCMH lên bộ máy đó (P6) thì điều kiện admin đã khai dùng lại nguyên. Thêm trường
    mới thì thêm ở ĐÂY một chỗ, màn Cấu hình chỉ cần nhắc tên trường.
    """
    lines = items_of(db, pr.id)
    # bao-CR-524: phiếu phòng thu mua mặc định xử lý vẫn đưa `handler_dept_id = 0` vào điều kiện
    # — giữ nguyên nghĩa của mọi điều kiện admin đã khai kiểu "handler_dept_id not_empty" (= nhà
    # máy tự mua). Đưa id thật vào đây là mọi phiếu thu mua chung cũng bỏ qua điều phối.
    handler = int(pr.handler_dept_id or 0)
    return {
        "handler_dept_id": 0 if is_central_dept(db, handler) else handler,
        "department_id": int(pr.department_id or 0),
        "company_id": int(pr.company_id or 0),
        "requester_id": int(pr.requester_id or 0),
        "is_urgent": bool(pr.is_urgent),
        "line_count": len(lines),
    }


def dispatch_skip_rules() -> str:
    """Chuỗi điều kiện JSON ở màn Cấu hình hệ thống (`pr_dispatch_skip_rules`); rỗng = không có."""
    from app.core import app_settings
    return (app_settings.get("pr_dispatch_skip_rules") or "").strip()


def skip_dispatch_for(db: Session, pr: PurchaseRequest) -> bool:
    """Phiếu này có ĐI THẲNG từ duyệt sang điều phối (bỏ bước thu mua duyệt lần 2) không — bao-CR-497.

    Ba tầng, tầng trên thắng:
      1. Công tắc `pr_dispatch_enabled` TẮT → mọi phiếu bỏ qua (luồng cũ CR-034, giữ nguyên).
      2. Công tắc BẬT + ô điều kiện RỖNG → không phiếu nào bỏ qua (mặc định, hành vi trước CR-497).
      3. Công tắc BẬT + có điều kiện → phiếu THỎA điều kiện bỏ qua. Điều kiện gõ sai JSON hay không
         phải danh sách thì `parse()` trả rỗng và ở đây coi như tầng 2 — một ô cấu hình gõ sai không
         được phép đổi luồng của cả công ty.
    Đại ca chốt 25/09/2026: mặc định y như cũ; bật điều kiện lên thì nhà máy tự mua tách khỏi thu
    mua chung, nhân sự lấy theo bộ phân công riêng của phòng.
    """
    # Gọi công tắc QUA cửa `service` (không gọi thẳng tên cùng tệp): bài kiểm monkeypatch `service.dispatch_enabled`.
    from . import service as pr_service

    if not pr_service.dispatch_enabled():
        return True
    from app.modules.approval.condition_service import matches, parse
    raw = dispatch_skip_rules()
    if not parse(raw):
        return False
    return matches(raw, dispatch_context(db, pr))


def dispatch_pr(db: Session, pid: int, user_id: int,
                allow_global_assignee: bool = True,
                audit_action: str = "dispatched") -> tuple[PurchaseRequest, int, int]:
    """CR-034 — ĐIỀU PHỐI (duyệt lần 2, phía thu mua).

    Trưởng phòng duyệt xong phiếu chỉ dừng ở 'approved' và CHƯA có nhân sự phụ trách.
    Quản lý/Admin thu mua xem lại rồi bấm Điều phối: lúc này mới tự động phân bổ NSTM theo
    phân loại (logic cũ giữ nguyên, chỉ dời thời điểm) và phiếu chuyển sang 'dispatched' —
    mốc duy nhất cho phép tạo Đơn mua hàng.

    bao-CR-414 (GĐ2): bảng phân công tra theo PHÒNG ĐANG XỬ LÝ phiếu; phân loại phòng chưa khai
    riêng thì rơi về bộ của phòng thu mua mặc định (bao-CR-524: PBA017, gồm cả dòng `0` cũ).
    `allow_global_assignee=False` khi người điều phối chỉ có bậc `dept_proc` (quản lý thu mua
    của phòng tự mua): chỉ dùng bộ riêng của phòng, không đẩy việc sang tay thu mua chung.

    `audit_action` (bao-CR-485): bước này ghi sổ dưới hành động nào. Bấm nút Điều phối thật thì
    `dispatched` (mặc định). Công tắc điều phối TẮT thì đường duyệt gọi nó với `approved` — cả
    cú duyệt lẫn phần hệ thống tự phân bổ gói vào MỘT dòng "Duyệt" của trưởng phòng; ghi hai
    dòng thì người xem sổ tưởng trưởng phòng bấm Điều phối, một việc họ không có quyền.

    Trả về (phiếu, số dòng vừa gán tự động, số dòng vẫn chưa có người)."""
    pr = get_pr(db, pid)
    if pr.status != "approved":
        raise HTTPException(400, "Chỉ điều phối được phiếu ở trạng thái Đã duyệt "
                                 "(trưởng phòng duyệt xong, chưa điều phối).")
    from app.modules.category_assignee.service import auto_assign_by_category
    n = auto_assign_by_category(db, pr, allow_global=allow_global_assignee)
    blank_count = sum(1 for it in items_of(db, pid) if not (it.assignee or "").strip())
    pr.status = "dispatched"
    # bao-CR-293 (ticket 20): Ngày tiếp nhận = ngày thu mua duyệt điều phối, KHÔNG phải ngày lập
    # phiếu — thời gian quy định có hàng phải đếm từ lúc thu mua thật sự nhận việc. Dòng nào
    # "Thời gian dự kiến có hàng" vẫn là giá trị TỰ ĐIỀN theo mốc cũ thì dời theo mốc mới;
    # dòng NSTM đã sửa tay (giá trị khác bản tự điền) giữ nguyên.
    # bao-CR-316: ghi vào cột RIÊNG `received_date`. Bản CR-293 ghi đè thẳng `request_date`,
    # tức xóa mất ngày lập phiếu và làm cột đó đổi nghĩa giữa chừng.
    from datetime import date
    old_base = sla_base_date(pr)
    new_base = date.today().isoformat()
    std = lead_time.std_days_map(db)
    for it in items_of(db, pid):
        auto_old = lead_time.regulated_date(std, it.item_group or "", old_base)
        if auto_old and (it.expected_date or "").strip() == auto_old:
            it.expected_date = lead_time.regulated_date(std, it.item_group or "", new_base)
    pr.received_date = new_base
    pr.updated_by = user_id
    db.commit()
    # H.10.1 — mọi dòng luôn có ít nhất một phương án: sinh PHƯƠNG ÁN 0 (chụp từ chính
    # dòng yêu cầu, chọn sẵn) ngay lúc thu mua tiếp nhận. Cả đường công tắc điều phối
    # TẮT (duyệt phát là điều phối luôn) cũng đi qua đây nên không cần móc chỗ khác.
    from . import option_service
    option_service.ensure_option_zero(db, pr)
    lead = ("Điều phối — tự động phân bổ" if audit_action == "dispatched"
            else "Hệ thống tự phân bổ (công tắc điều phối tắt)")
    record(db, user_id, ENTITY, pid, audit_action,
           f"{lead} {n} dòng" + (f", còn {blank_count} dòng chưa có người" if blank_count else "")
           + (f" · Ngày tiếp nhận {old_base or '(trống)'} -> {new_base}" if old_base != new_base else ""))
    # Mốc gốc dời muộn hơn -> ngày QĐ có hàng dời theo, dòng "cần sớm hơn ngày QĐ" có thể phát
    # sinh mới -> soát lại cờ Đơn gấp (CR-082: chỉ BẬT, không tự tắt).
    apply_auto_urgent(db, pr, user_id, std)
    db.refresh(pr)
    return pr, n, blank_count


def assign(db: Session, pid: int, data: AssignIn, user_id: int) -> PurchaseRequest:
    """Phân bổ NSTM cho từng dòng — chạy được cả khi phiếu đã gửi duyệt (không bị khóa như sửa)."""
    pr = get_pr(db, pid)
    if pr.status in ("cancelled", "completed", "done"):
        raise HTTPException(400, "Phiếu đã bị từ chối/hoàn thành — không phân bổ được")
    if data.assignee_id:
        pr.assignee_id = data.assignee_id
    from app.modules.category_assignee.service import check_assignee_allowed
    rows = {i.id: i for i in items_of(db, pid)}
    for it in data.items:
        row = rows.get(it.id)
        if row is not None:
            # bao-CR-486: người phụ trách phải thuộc phòng xử lý của phiếu — kiểm TRƯỚC khi ghi
            # dòng nào, một dòng sai là cả lượt phân bổ không ghi (không để nửa chừng).
            if (it.assignee or "").strip() != (row.assignee or "").strip():
                check_assignee_allowed(db, pr, it.assignee)
            row.assignee = it.assignee
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "assign", "Phân bổ NSTM")
    return pr
