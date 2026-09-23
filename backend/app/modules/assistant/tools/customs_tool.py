"""Tool GIÁ HẢI QUAN của trợ lý AI (bao-CR-470, HQ5 — `doc/erp/hai-quan/01` A-01 · A-02 · A-03).

Hai tool, cùng một nguồn với màn Tra cứu giá hải quan (`customs/service.py`), nên trợ lý
và màn hình không bao giờ ra hai con số khác nhau:

* `customs_price_stats` — giá / lượng theo tháng · quý · năm của một mặt hàng / hoạt chất.
* `customs_buy_timing` — "nên mua lúc nào thì giá thấp nhất", kèm ĐỘ TIN CẬY.

⚠️ **A-03 — trợ lý phải nói ra độ tin cậy.** Dữ liệu hiện chỉ có MỘT năm; một câu khẳng
định chắc nịch dựa trên 3 dòng là thứ nguy hiểm nhất của cả tính năng, vì người đọc sẽ
đặt hàng thật theo nó. Nên tool KHÔNG để model tự suy: nó trả sẵn `confidence` + câu
`caveat` bắt buộc nhắc lại, và `best_period` chỉ xét kỳ có từ `MIN_LINES_FOR_BEST` dòng
trở lên (tháng 8 ATRAZINE "rẻ nhất" chỉ nhờ 3 dòng — không được chọn).

Gác quyền: `customs_price.read`. Dữ liệu thị trường bên ngoài, không có chủ sở hữu để lọc
phạm vi (khai `PUBLIC`) — nhóm "danh mục / thống kê dùng chung" ở `test_assistant_pham_vi_doc.py`.
Bot Telegram (Agent Hub) dùng chung bộ tool này nên có luôn, không phải làm thêm.
"""
from collections import defaultdict

from fastapi import HTTPException

from app.modules.customs import service as customs
from app.modules.customs.constants import MIN_LINES_FOR_BEST

from .base import ToolContext, ToolSpec, denied

_FILTER_PROPS = {
    "keyword": {"type": "string",
                "description": "Tên hàng HOẶC tên hoạt chất cần tra, ví dụ 'ATRAZINE', 'MANCOZEB'. "
                               "Khớp cả tên hàng trên tờ khai lẫn hoạt chất đã suy ra."},
    "hs_code": {"type": "string", "description": "Mã HS (đủ hoặc đầu mã), ví dụ '380893'."},
    "unit": {"type": "string",
             "description": "Đơn vị tính cần xem, ví dụ 'KGM' (kg), 'LTR' (lít). Bỏ trống = đơn vị "
                            "nhiều dòng nhất. KHÔNG bao giờ cộng lẫn đơn vị."},
    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD hoặc tháng YYYY-MM."},
    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD hoặc tháng YYYY-MM."},
}


def _filters(args: dict) -> dict:
    return {"q": (args.get("keyword") or "").strip(), "hs_code": (args.get("hs_code") or "").strip(),
            "date_from": args.get("date_from") or "", "date_to": args.get("date_to") or ""}


def _confidence(stats: dict) -> tuple[str, str]:
    """→ (mức, câu nhắc bắt buộc). Chấm theo số NĂM và số dòng, không theo cảm giác."""
    cov = stats["coverage"]
    years, lines = cov["years"], cov["lines"]
    if years >= 3 and lines >= 60:
        level = "cao"
    elif years >= 2 and lines >= 30:
        level = "trung bình"
    else:
        level = "thấp"
    caveat = (f"Dựa trên {lines} dòng hàng trong {cov['months']} tháng, {years} năm dữ liệu "
              f"({cov['date_from']} → {cov['date_to']}).")
    if years < 2:
        caveat += " Mới có MỘT năm dữ liệu — chỉ thấy xu hướng trong năm, CHƯA đủ để kết luận theo mùa vụ."
    if cov["empty_periods"]:
        caveat += f" Không có dữ liệu ở: {', '.join(cov['empty_periods'])}."
    return level, caveat


def _run_stats(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("customs_price", "read"):
        return denied("dữ liệu giá hải quan")
    period = args.get("period") or "month"
    try:
        st = customs.compute_stats(ctx.db, _filters(args), period,
                                   args.get("price_mode") or "adjusted", args.get("unit") or "")
    except HTTPException as e:
        return {"error": e.detail}
    level, caveat = _confidence(st)
    return {
        "unit": st["unit"], "units_available": st["units"], "period": period,
        "series": [{k: s[k] for k in ("label", "count", "qty", "min", "max", "wavg", "low_data")}
                   for s in st["series"]],
        "summary": st["kpi"], "best_period": st["best_period"],
        "confidence": level, "caveat": caveat,
        "alerts": [a["obligation"] + f" ({a['name']})" for a in customs.match_alerts(ctx.db, _filters(args))],
        "price_note": "Giá USD trên một đơn vị tính; ưu tiên giá hải quan ĐIỀU CHỈNH, thiếu thì giá khai báo. "
                      "wavg = bình quân gia quyền theo lượng.",
        "url": "/customs-prices",
    }


def _run_timing(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("customs_price", "read"):
        return denied("dữ liệu giá hải quan")
    try:
        st = customs.compute_stats(ctx.db, _filters(args), "month", "adjusted", args.get("unit") or "")
    except HTTPException as e:
        return {"error": e.detail}
    level, caveat = _confidence(st)
    with_data = [s for s in st["series"] if s["wavg"] is not None]
    cheapest_any = min(with_data, key=lambda s: s["wavg"]) if with_data else None
    best = next((s for s in st["series"] if s["period"] == st["best_period"]), None)
    #  Gộp theo THÁNG DƯƠNG LỊCH qua các năm — chỉ có ý nghĩa khi có từ 2 năm trở lên.
    by_calendar = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0})
    for s in with_data:
        b = by_calendar[int(s["period"][5:7])]
        b["count"] += s["count"]
        if s["qty"]:
            b["qty"] += s["qty"]
            b["value"] += s["wavg"] * s["qty"]
    return {
        "unit": st["unit"], "units_available": st["units"],
        "recommended_month": best and {"label": best["label"], "wavg": best["wavg"], "count": best["count"]},
        "cheapest_month_any": cheapest_any and {
            "label": cheapest_any["label"], "wavg": cheapest_any["wavg"], "count": cheapest_any["count"],
            "reliable": cheapest_any["count"] >= MIN_LINES_FOR_BEST},
        "monthly": [{k: s[k] for k in ("label", "count", "wavg", "min", "max", "low_data")} for s in st["series"]],
        "calendar_months": {m: {"count": b["count"], "wavg": round(b["value"] / b["qty"], 4) if b["qty"] else None}
                            for m, b in sorted(by_calendar.items())},
        "min_lines_for_best": MIN_LINES_FOR_BEST,
        "confidence": level, "caveat": caveat,
        "alerts": [a["obligation"] + f" ({a['name']})" for a in customs.match_alerts(ctx.db, _filters(args))],
        "url": "/customs-prices",
    }


CUSTOMS_PRICE_STATS_SPEC = ToolSpec(
    name="customs_price_stats",
    description=(
        "Giá NHẬP KHẨU thị trường của một mặt hàng / hoạt chất theo dữ liệu tờ khai hải quan "
        "(GTT02): giá thấp nhất, cao nhất, bình quân gia quyền, tổng lượng, số dòng — theo tháng, "
        "quý hoặc năm. Gọi khi người dùng hỏi 'giá ATRAZINE nhập về bao nhiêu', 'giá mancozeb theo "
        "quý', 'thị trường nhập bao nhiêu tấn'. Cần ÍT NHẤT một trong keyword / hs_code. "
        "Khi trả lời: nêu đơn vị (USD/kg, USD/lít), KHÔNG cộng lẫn đơn vị, và LUÔN nhắc lại "
        "`caveat` + `alerts` (cảnh báo pháp lý) nếu có."),
    parameters={"type": "object", "properties": {
        **_FILTER_PROPS,
        "period": {"type": "string", "enum": ["month", "quarter", "year"],
                   "description": "Kỳ gom: month (mặc định) · quarter · year."},
        "price_mode": {"type": "string", "enum": ["adjusted", "declared"],
                       "description": "adjusted (mặc định) = ưu tiên giá hải quan điều chỉnh; declared = chỉ giá khai báo."},
    }},
    handler=_run_stats,
)

CUSTOMS_BUY_TIMING_SPEC = ToolSpec(
    name="customs_buy_timing",
    description=(
        "Phân tích NÊN MUA VÀO THÁNG NÀO thì giá thấp nhất cho một mặt hàng / hoạt chất, dựa trên "
        "giá nhập khẩu theo tháng từ tờ khai hải quan. Gọi khi người dùng hỏi 'nên mua atrazine lúc "
        "nào', 'tháng nào giá rẻ nhất', 'có nên mua trước để tồn kho không'. BẮT BUỘC khi trả lời: "
        "(1) chỉ đề xuất `recommended_month` — tháng rẻ nhất trong số tháng ĐỦ dữ liệu; nếu "
        "`cheapest_month_any.reliable` là false thì nói rõ tháng đó rẻ hơn nhưng quá ít dòng để tin; "
        "(2) nhắc lại nguyên văn ý của `caveat` và mức `confidence` — với 'thấp' KHÔNG được khẳng "
        "định mùa vụ, chỉ nói 'trong năm dữ liệu hiện có'; (3) nêu `alerts` pháp lý nếu có."),
    parameters={"type": "object", "properties": dict(_FILTER_PROPS)},
    handler=_run_timing,
)
