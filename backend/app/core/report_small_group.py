"""Che nhóm nhỏ dùng chung cho báo cáo kiểu Haravan (duoc-CR-688) — rút từ luật Nhóm tuổi (CR-687).

Nhóm chỉ có 1–2 người cho phép đoán số liệu (tuổi, lương) của từng người. Luật:

1) Sơ cấp: nhóm bị che CẢ NHÓM (mọi giá trị kỳ này + kỳ so sánh -> None, cờ `suppressed` để xuất Excel
   ghi ô TRỐNG chứ không phải 0) nếu BẤT KỲ số đếm người nào của nhóm ở MỘT TRONG HAI kỳ bằng 1 hoặc 2.
2) Thứ cấp (xét RIÊNG từng kỳ, và chỉ ở kỳ mà một nhóm bị che có 1–2 người ở chính kỳ đó): dòng Tổng vẫn
   hiện nên "Tổng − Σ nhóm hiện" lộ đúng phần bị che. Trong các nhóm bị che còn người ở kỳ đó phải có >= 2
   nhóm với tổng >= `MIN_GROUP` người, nếu không che thêm nhóm hiện nhỏ nhất còn người; lặp tới khi đủ hoặc
   hết nhóm. Nhóm bị che thêm ở một kỳ thì che ở cả hai.
3) Không cứu được (`unsafe_sides`): hết nhóm để che thêm mà phần bị che vẫn < 2 nhóm hoặc < `MIN_GROUP`
   người (vd. bộ lọc chỉ còn một nhóm, hai nhóm 1 người) — Tổng đã lộ trọn phần đó. Hàm này KHÔNG tự bỏ
   nhóm; nơi gọi gọi `drop_unsafe_breakdown` để bỏ cả bảng "Xem theo" của lượt trả lời đó.
Ai chịu che (mọi người xem hay chỉ người thiếu quyền) do NƠI GỌI quyết định.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

MIN_GROUP = 3
_SIDES = ("current", "compare")

CountsOf = Callable[[dict], list[int]]   # các số ĐẾM NGƯỜI nằm sau một tập giá trị của nhóm
SizeOf = Callable[[dict], int]            # quy mô nhóm (để chọn "nhóm nhỏ nhất kế tiếp")


def hide_group(g: dict) -> None:
    """Mọi giá trị (kỳ này + kỳ so sánh) -> None; cờ `suppressed` cho bước xuất Excel."""
    for side in _SIDES:
        if g.get(side) is not None:
            g[side] = {k: None for k in g[side]}
    g["suppressed"] = True


@dataclass(frozen=True)
class SmallGroupResult:
    changed: bool = False                 # có nhóm nào bị che không
    unsafe_sides: tuple[str, ...] = ()    # kỳ ("current"/"compare") mà che xong vẫn lộ

    def __bool__(self) -> bool:
        return self.changed


def drop_unsafe_breakdown(data: dict, dim_key: str | None, dim_label: str) -> None:
    """Bỏ hẳn bảng "Xem theo" (và danh sách top cùng chiều) của lượt trả lời + ghi chú lý do."""
    data["groups"] = []
    if dim_key and isinstance(data.get("breakdowns"), dict) and dim_key in data["breakdowns"]:
        data["breakdowns"][dim_key] = []
    data.setdefault("notes", []).append(
        f"Không đủ người để xem theo {dim_label} mà không lộ thông tin từng người — bỏ bớt bộ lọc để xem")


def suppress_small_groups(data: dict, counts_of: CountsOf, size_of: SizeOf, note: str,
                          extra_note: str) -> SmallGroupResult:
    """Che nhóm nhỏ trong `data["groups"]` tại chỗ, thêm ghi chú vào `data["notes"]`."""
    groups = data.get("groups") or []
    if not groups:
        return SmallGroupResult()
    #  Chụp số liệu TRƯỚC khi che (che xong mọi giá trị đã là None).
    snap = {id(g): {s: (counts_of(g[s]), size_of(g[s]) or 0) for s in _SIDES if g.get(s) is not None}
            for g in groups}

    def real(g, side) -> bool:      # nhóm còn người ở kỳ `side`
        return side in snap[id(g)] and any(snap[id(g)][side][0])

    def small(g, side) -> bool:     # nhóm có 1–2 người ở chính kỳ `side`
        return side in snap[id(g)] and any(1 <= c < MIN_GROUP for c in snap[id(g)][side][0])

    hidden = [g for g in groups if any(small(g, s) for s in _SIDES)]
    if not hidden:
        return SmallGroupResult()
    chosen = {id(g) for g in hidden}

    def enough(side) -> bool:
        in_side = [g for g in groups if id(g) in chosen and real(g, side)]
        return len(in_side) >= 2 and sum(snap[id(g)][side][1] for g in in_side) >= MIN_GROUP

    extra, unsafe = False, set()
    changed = True
    while changed:
        changed = False
        for side in _SIDES:
            #  Chỉ khi chính kỳ này có nhóm 1–2 người thì phần bị che mới cần bù (nhóm bị che chỉ vì số
            #  ở kỳ kia mà kỳ này đông người thì Tổng kỳ này không lộ gì).
            if side in unsafe or not any(small(g, side) for g in hidden) or enough(side):
                continue
            rest = [g for g in groups if id(g) not in chosen and real(g, side)]
            if not rest:
                unsafe.add(side)
                continue
            chosen.add(id(min(rest, key=lambda g: snap[id(g)][side][1])))
            extra = changed = True
    for g in groups:
        if id(g) in chosen:
            hide_group(g)
    data.setdefault("notes", []).append(note)
    if extra:
        data["notes"].append(extra_note)
    return SmallGroupResult(True, tuple(s for s in _SIDES if s in unsafe))
