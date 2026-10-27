"""Che số nhóm tuổi nhỏ + chặn danh sách theo nhóm tuổi (duoc-CR-687, A2).

Nhóm tuổi chỉ ~5 nhóm; nhóm dưới `MIN_GROUP` người cho phép đoán tuổi từng người (nhất là khi
lọc thêm theo phòng ban). Người có `employee_sensitive.read` (được xem ngày sinh thật) không bị che.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.modules.employee.sensitive import can_read_sensitive

MIN_GROUP = 3
AGE_NOTE = "Nhóm tuổi dưới 3 người được che số để không đoán ra tuổi từng người"
EXTRA_NOTE = ("Để số bị che không suy ngược được từ Tổng, báo cáo che thêm nhóm tuổi nhỏ kế tiếp; "
              "dòng Tổng vẫn đủ số")
#  Bốn số ĐẾM của một nhóm — chỉ cần MỘT số ở mức 1–2 (kỳ này hoặc kỳ so sánh) là đủ chỉ ra từng người.
_COUNT_KEYS = ("headcount_start", "headcount_end", "new_hires", "departures")


def _counts(g: dict) -> list[int]:
    return [(g[side] or {}).get(k) or 0 for side in ("current", "compare") if g.get(side) is not None
            for k in _COUNT_KEYS]


def _hide(g: dict) -> None:
    """Mọi giá trị số (kỳ này + kỳ so sánh) -> None; cờ `suppressed` để xuất Excel ghi ô TRỐNG, không phải 0."""
    for side in ("current", "compare"):
        if g.get(side) is not None:
            g[side] = {k: None for k in g[side]}
    g["suppressed"] = True


def suppress_small_age_groups(data: dict, prof: dict) -> None:
    """Che nhóm tuổi nhỏ cho người KHÔNG có `employee_sensitive.read` (`employee_id=0` ở `can_read_sensitive`
    = chỉ xét KHÓA quyền, không xét ngoại lệ «chính mình»).

    1) Sơ cấp: nhóm có BẤT KỲ số đếm nào (đầu/cuối kỳ, vào, nghỉ — kỳ này hay kỳ so sánh) bằng 1 hoặc 2 bị che.
    2) Thứ cấp: Tổng vẫn hiện nên «Tổng − Σ nhóm hiện» lộ đúng số bị che. Nếu số nhóm bị che (bỏ nhóm toàn 0)
       chỉ là một, hoặc tổng định biên cuối kỳ của chúng < 3, che thêm nhóm hiện nhỏ nhất còn người, lặp tới
       khi đủ ≥ 2 nhóm với tổng ≥ 3 hoặc hết nhóm."""
    if can_read_sensitive(prof):
        return
    groups = data.get("groups") or []
    #  Chụp số liệu TRƯỚC khi che: (định biên cuối kỳ này, toàn 0?) của từng nhóm.
    end = {id(g): (g["current"].get("headcount_end") or 0) for g in groups}
    zero = {id(g): not any(_counts(g)) for g in groups}
    hidden = [g for g in groups if any(1 <= c < MIN_GROUP for c in _counts(g))]
    if not hidden:
        return
    for g in hidden:
        _hide(g)
    extra = False
    while True:
        real = [g for g in hidden if not zero[id(g)]]
        if len(real) >= 2 and sum(end[id(g)] for g in real) >= MIN_GROUP:
            break
        rest = [g for g in groups if not g.get("suppressed") and not zero[id(g)]]
        if not rest:
            break
        nxt = min(rest, key=lambda g: end[id(g)])
        _hide(nxt)
        hidden.append(nxt)
        extra = True
    data.setdefault("notes", []).append(AGE_NOTE)
    if extra:
        data["notes"].append(EXTRA_NOTE)


def require_age_rows_allowed(prof: dict, group_by: str | None, group_key: str | None) -> None:
    """Danh sách người của MỘT nhóm tuổi tiết lộ tuổi từng người → cần `employee_sensitive.read`."""
    if group_by == "age_band" and group_key is not None and not can_read_sensitive(prof):
        raise HTTPException(403, "Danh sách theo nhóm tuổi cần quyền xem thông tin nhạy cảm của nhân sự")
