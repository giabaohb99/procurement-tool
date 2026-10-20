"""Định nghĩa «xong» và «làm lại» của từng loại phiếu — CẤU HÌNH, không rải `if` theo loại (duoc-CR-656, D1a, Q2).

Đổi một định nghĩa = sửa MỘT dòng ở `SPECS` rồi chạy lại `scripts/backfill_work_cycles.py`.
Tài liệu cho người đọc: `doc/tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md`.

Mọi giá trị trạng thái ở đây là CHUỖI, vì `tab_change_log.after_value` là chuỗi: cột số `5` thành `"5"`.
Hai nguồn sự kiện, gộp lại (`cycle_compute` khử trùng):
  · `tab_change_log` (field `status`) — thấy cả bước tự chuyển không ghi audit, nhưng chỉ từ ngày bật (16/09/2026 ở local);
  · `tab_audit_log` (cho 4 chứng từ Thu mua) — có từ 01/07/2026 và có từ vựng nghiệp vụ («trả về» ≠ «từ chối»).
"""
from dataclasses import dataclass, field
from enum import IntEnum

from app.core.capability_codes import CycleKind


class Ev(IntEnum):
    """Loại sự kiện đã chuẩn hóa, độc lập với nguồn."""

    DONE = 1       # tới trạng thái «xong»
    CANCEL = 2     # hủy
    REJECT = 3     # từ chối (khóa)
    RETURN = 4     # trả về để làm lại  → tính 1 lần làm lại
    REOPEN = 5     # mở lại sau khi xong (task) → tính 1 lần làm lại


@dataclass(frozen=True)
class CycleSpec:
    kind: CycleKind
    table: str                              # tên bảng trong tab_change_log.table_name
    done: frozenset = frozenset()           # trạng thái hiện tại coi là XONG
    cancelled: frozenset = frozenset()
    rejected: frozenset = frozenset()       # trạng thái hiện tại = bị từ chối (khóa)
    returned: frozenset = frozenset()       # đổi SANG trạng thái này = trả về làm lại
    ambiguous_reject: frozenset = frozenset()  # YCMH: `rejected` dùng cho cả từ chối lẫn trả về → hỏi audit
    reopen_status: str | None = None        # task: đổi từ «xong» sang trạng thái này = mở lại
    done_pick: str = "first"                # `first` | `last` mốc xong khi có nhiều lần
    sticky_done: bool = False               # văn bản: hết hiệu lực/lưu trữ rồi vẫn là «đã xong» việc soạn
    done_ts_col: str | None = None          # cột mốc của chính bảng, dự phòng khi nhật ký thiếu
    audit_entity: str | None = None
    audit_map: dict = field(default_factory=dict)   # action → Ev


def _s(*vals) -> frozenset:
    return frozenset(str(v) for v in vals)


#  ĐMH: «Đã nhận đủ» (`received`) đã tính là XONG (đại ca chốt 20/10/2026) — `completed` chỉ là bước đóng sổ sau đó;
#  mốc xong lấy lần ĐẦU (`done_pick=first`) nên là lúc nhận đủ.
#  Thu mua: audit có «returned» cho YCMH; YCBG / ĐMH dùng status `rejected` = Trả về (không có «từ chối» thật).
SPECS: tuple[CycleSpec, ...] = (
    CycleSpec(CycleKind.PURCHASE_REQUEST, "tab_purchase_request",
              done=_s("completed", "done"), cancelled=_s("cancelled"),
              rejected=_s("rejected"), ambiguous_reject=_s("rejected"),
              audit_entity="purchase_request",
              audit_map={"completed": Ev.DONE, "cancelled": Ev.CANCEL, "rejected": Ev.REJECT, "returned": Ev.RETURN}),
    CycleSpec(CycleKind.SURVEY_REQUEST, "tab_survey_request",
              done=_s("done"), cancelled=_s("cancelled"), returned=_s("rejected"),
              audit_entity="survey_request",
              audit_map={"done": Ev.DONE, "cancelled": Ev.CANCEL, "rejected": Ev.RETURN}),
    CycleSpec(CycleKind.PURCHASE_ORDER, "tab_purchase_order",
              done=_s("received", "completed"), cancelled=_s("cancelled"), returned=_s("rejected"),
              audit_entity="purchase_order",
              audit_map={"received": Ev.DONE, "completed": Ev.DONE, "cancelled": Ev.CANCEL, "rejected": Ev.RETURN}),
    CycleSpec(CycleKind.PAYMENT_REQUEST, "tab_payment_request",
              done=_s("paid"), cancelled=_s("cancelled"),
              audit_entity="payment_request",
              audit_map={"paid": Ev.DONE, "cancelled": Ev.CANCEL}),
    CycleSpec(CycleKind.DOCUMENT, "tab_document",
              done=_s(3, 4), cancelled=_s(7), rejected=_s(10), returned=_s(9),
              sticky_done=True, done_ts_col="issued_at"),
    CycleSpec(CycleKind.VEHICLE_BOOKING, "tab_vehicle_booking",
              done=_s(5), cancelled=_s(7), rejected=_s(6), returned=_s(8)),
    CycleSpec(CycleKind.SEAL_REQUEST, "tab_seal_request",
              done=_s(4), cancelled=_s(6), rejected=_s(5), returned=_s(7), done_ts_col="completed_at"),
    CycleSpec(CycleKind.ROOM_BOOKING, "tab_room_booking",
              done=_s(3), cancelled=_s(6), rejected=_s(4), returned=_s(5), done_ts_col="decided_at"),
    CycleSpec(CycleKind.LEAVE_REQUEST, "tab_leave_request",
              done=_s(3), cancelled=_s(6), rejected=_s(4), returned=_s(5), done_ts_col="decided_at"),
    CycleSpec(CycleKind.WORK_TASK, "tab_work_task",
              done=_s(2), cancelled=_s(3), reopen_status="1", done_pick="last", done_ts_col="completed_at"),
)

SPEC_BY_KIND = {s.kind: s for s in SPECS}
SPEC_BY_TABLE = {s.table: s for s in SPECS}


def event_from_status_change(spec: CycleSpec, before: str | None, after: str | None) -> Ev | None:
    """Một dòng `tab_change_log` (field `status`) → sự kiện chuẩn hóa, hoặc None nếu không đáng kể."""
    after = None if after is None else str(after)
    before = None if before is None else str(before)
    if after in spec.done:
        return Ev.DONE
    if after in spec.cancelled:
        return Ev.CANCEL
    if after in spec.returned:
        return Ev.RETURN
    if after in spec.rejected and after not in spec.ambiguous_reject:
        return Ev.REJECT
    if spec.reopen_status is not None and after == spec.reopen_status and before in spec.done:
        return Ev.REOPEN
    return None
