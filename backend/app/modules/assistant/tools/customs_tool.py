"""Tool GIÁ HẢI QUAN của trợ lý AI (bao-CR-470 + bao-CR-481, `doc/erp/hai-quan/01` A-01…A-03).

Bốn tool, cùng một nguồn với màn Tra cứu giá hải quan (`customs/service.py`), nên trợ lý
và màn hình không bao giờ ra hai con số khác nhau:

* `customs_price_stats` — giá / lượng theo tháng · quý · năm của một mặt hàng / hoạt chất;
  truyền thêm `compare_keywords` thì so 2–5 mặt hàng trên CÙNG một đơn vị (bao-CR-481).
* `customs_buy_timing` — "nên mua lúc nào / có nên mua lúc này không", kèm ĐỘ TIN CẬY và
  đánh giá THỜI ĐIỂM HIỆN TẠI (giá tháng gần nhất đang thấp / trung bình / cao so với năm,
  xu hướng 3 tháng, dữ liệu cũ hay mới) — bao-CR-481.
* `customs_market` — ai nhập, mua của đối tác nào, từ nước nào, mấy lô gần nhất (bao-CR-481).
* `customs_legal_check` — hóa chất có trong danh mục pháp lý nào (cấm / ngưỡng / công bố),
  và thuế nhập khẩu theo mã HS (bao-CR-481).

⚠️ **Trợ lý phải nói ra độ tin cậy và giới hạn.** Dữ liệu hiện chỉ có MỘT năm; một câu khẳng
định chắc nịch dựa trên 3 dòng là thứ nguy hiểm nhất của cả tính năng, vì người đọc sẽ đặt
hàng thật theo nó. Nên tool KHÔNG để model tự suy: nó trả sẵn `confidence` + `caveat` bắt
buộc nhắc lại; câu «có nên mua lúc này» chỉ dựa trên GIÁ NHẬP của thị trường — tool không
biết tồn kho, nhu cầu, hạn dùng, dòng tiền của công ty và câu trả lời phải nói rõ điều đó.
Phần pháp lý chỉ nói đúng dữ liệu có: dữ liệu KHÔNG có khung mức phạt, cấm tự nêu mức phạt.

Gác quyền: `customs_price.read`. Dữ liệu thị trường bên ngoài, không có chủ sở hữu để lọc
phạm vi (khai `PUBLIC`) — nhóm "danh mục / thống kê dùng chung" ở `test_assistant_pham_vi_doc.py`.
Bot Telegram (Agent Hub) dùng chung bộ tool này qua `assistant_service.ask`.
"""
from collections import defaultdict
from datetime import date

from fastapi import HTTPException

from app.modules.customs import service as customs
from app.modules.customs.constants import MIN_LINES_FOR_BEST, RegulationList

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

#  Câu nhắc chung cho mọi câu trả lời pháp lý — dữ liệu nạp từ văn bản, KHÔNG có khung phạt.
_LEGAL_NOTE = ("Tra cứu tham khảo từ danh mục đã nạp (NĐ 24/2026/NĐ-CP, TT 75/2025/TT-BNNMT, "
               "TT 01/2026/TT-BCT, biểu thuế 2026) — đối chiếu văn bản gốc trước khi quyết định. "
               "Dữ liệu KHÔNG có mức phạt: không được tự nêu mức phạt.")

#  Nặng nhất lên đầu, cùng thứ tự với màn hình (bao-CR-477): cấm · tiền chất · có ngưỡng ·
#  phải công bố · hai phụ lục còn lại.
_SEVERITY = {int(RegulationList.BANNED_TT75): 0, int(RegulationList.ND24_PL3): 1,
             int(RegulationList.ND24_PL4): 2, int(RegulationList.PUBLISH_TT01): 3,
             int(RegulationList.ND24_PL1): 4, int(RegulationList.ND24_PL2): 5}

_MAX_REGULATIONS = 15
_MAX_TARIFF_ROWS = 10


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


def _alerts(ctx: ToolContext, args: dict) -> list[str]:
    return [a["obligation"] + f" ({a['name']})" for a in customs.match_alerts(ctx.db, _filters(args))]


def _run_stats(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("customs_price", "read"):
        return denied("dữ liệu giá hải quan")
    period = args.get("period") or "month"
    price_mode = args.get("price_mode") or "adjusted"
    try:
        st = customs.compute_stats(ctx.db, _filters(args), period, price_mode, args.get("unit") or "")
        compare = None
        others = [t for t in (args.get("compare_keywords") or []) if (t or "").strip()]
        if others:
            if not _filters(args)["q"]:
                return {"error": "So sánh cần `keyword` cho mặt hàng chính (mã HS chỉ dùng làm bộ lọc chung)."}
            #  So trên CÙNG một đơn vị với mặt hàng chính — không thì hai đường không cùng thước đo.
            terms = [_filters(args)["q"], *others][:5]
            cmp = customs.compare_terms(ctx.db, terms, {**_filters(args), "q": ""}, period, price_mode,
                                        args.get("unit") or st["unit"])
            compare = {"unit": cmp["unit"], "terms": [
                {"keyword": t["term"], "summary": t["kpi"],
                 "series": [{k: s[k] for k in ("label", "count", "wavg")} for s in t["series"]]}
                for t in cmp["terms"]]}
    except HTTPException as e:
        return {"error": e.detail}
    level, caveat = _confidence(st)
    out = {
        "unit": st["unit"], "units_available": st["units"], "period": period,
        "series": [{k: s[k] for k in ("label", "count", "qty", "min", "max", "p25", "p75", "wavg", "low_data")}
                   for s in st["series"]],
        "summary": st["kpi"], "best_period": st["best_period"],
        "confidence": level, "caveat": caveat,
        "alerts": _alerts(ctx, args),
        "price_note": "Giá USD trên một đơn vị tính; ưu tiên giá hải quan ĐIỀU CHỈNH, thiếu thì giá khai báo. "
                      "wavg = bình quân gia quyền theo lượng; p25–p75 = khoảng giá phổ biến (nửa số dòng ở giữa).",
        "url": "/customs-prices",
    }
    if compare:
        out["compare"] = compare
    return out


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
    now = customs.assess_current_price(st, date.today())
    return {
        "unit": st["unit"], "units_available": st["units"],
        "recommended_month": best and {"label": best["label"], "wavg": best["wavg"], "count": best["count"]},
        "cheapest_month_any": cheapest_any and {
            "label": cheapest_any["label"], "wavg": cheapest_any["wavg"], "count": cheapest_any["count"],
            "reliable": cheapest_any["count"] >= MIN_LINES_FOR_BEST},
        "monthly": [{k: s[k] for k in ("label", "count", "wavg", "min", "max", "low_data")} for s in st["series"]],
        "calendar_months": {m: {"count": b["count"], "wavg": round(b["value"] / b["qty"], 4) if b["qty"] else None}
                            for m, b in sorted(by_calendar.items())},
        "now": now,
        "min_lines_for_best": MIN_LINES_FOR_BEST,
        "confidence": level, "caveat": caveat,
        "not_known": "Tool chỉ biết GIÁ NHẬP KHẨU của thị trường. KHÔNG biết tồn kho, nhu cầu sản xuất, "
                     "hạn dùng, dòng tiền, giá chào của NCC của công ty — quyết định mua phải xét thêm các thứ đó.",
        "alerts": _alerts(ctx, args),
        "url": "/customs-prices",
    }


def _run_market(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("customs_price", "read"):
        return denied("dữ liệu giá hải quan")
    try:
        mk = customs.market_overview(ctx.db, _filters(args), args.get("unit") or "",
                                     limit=min(int(args.get("limit") or 10), 20), recent=5)
    except HTTPException as e:
        return {"error": e.detail}
    for row in mk["importers"]:
        row.pop("importer_id", None)
    return {**mk,
            "note": "Gộp nhà nhập khẩu theo MÃ SỐ THUẾ; thị phần tính theo LƯỢNG của đơn vị đang xem. "
                    "Mỗi dòng là một DÒNG HÀNG trên tờ khai, không phải một tờ khai.",
            "alerts": _alerts(ctx, args),
            "url": "/customs-prices"}


def _run_legal(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("customs_price", "read"):
        return denied("dữ liệu giá hải quan")
    query = (args.get("query") or "").strip()
    hs = (args.get("hs_code") or "").strip()
    if not query and not hs:
        return {"error": "Cần tên hóa chất / số CAS / công thức (query) hoặc mã HS (hs_code)."}
    out: dict = {"note": _LEGAL_NOTE}
    try:
        if query:
            reg = customs.lookup_regulations(ctx.db, query)
            items = sorted(reg["items"], key=lambda r: (_SEVERITY.get(r["list_code"], 9), r["name"]))
            out["regulations"] = {
                "query": reg["term"], "formula_cas": reg["formula_cas"], "total": len(items),
                "items": [{k: r[k] for k in ("list_label", "name", "name_vi", "cas_no", "threshold_kg",
                                              "banned_year", "legal_basis", "obligation")}
                          for r in items[:_MAX_REGULATIONS]],
                "not_found": not items,
            }
        if hs:
            rows = customs.lookup_tariff(ctx.db, hs)
            out["tariff"] = {"hs_code": hs, "rows": [
                {k: r[k] for k in ("hs_code", "name_vn", "unit", "rate_normal", "rate_mfn", "rate_vat",
                                   "fta", "policy")} for r in rows[:_MAX_TARIFF_ROWS]],
                "not_found": not rows,
                "rate_note": "rate_normal = thuế suất thông thường; rate_mfn = ưu đãi (MFN); fta = thuế suất "
                             "theo từng hiệp định (%)."}
    except HTTPException as e:
        return {"error": e.detail}
    return out


CUSTOMS_PRICE_STATS_SPEC = ToolSpec(
    name="customs_price_stats",
    description=(
        "Giá NHẬP KHẨU thị trường của một mặt hàng / hoạt chất theo dữ liệu tờ khai hải quan "
        "(GTT02): giá thấp nhất, cao nhất, khoảng phổ biến, bình quân gia quyền, tổng lượng, số dòng — "
        "theo tháng, quý hoặc năm. Truyền `compare_keywords` để SO SÁNH thêm 1–4 mặt hàng khác trên "
        "cùng đơn vị. Gọi khi người dùng hỏi 'giá ATRAZINE nhập về bao nhiêu', 'so giá atrazine với "
        "mesotrione'. Cần ÍT NHẤT một trong keyword / hs_code. Khi trả lời: nêu đơn vị (USD/kg, "
        "USD/lít), KHÔNG cộng lẫn đơn vị, và LUÔN nhắc lại `caveat` + `alerts` nếu có."),
    parameters={"type": "object", "properties": {
        **_FILTER_PROPS,
        "period": {"type": "string", "enum": ["month", "quarter", "year"],
                   "description": "Kỳ gom: month (mặc định) · quarter · year."},
        "price_mode": {"type": "string", "enum": ["adjusted", "declared"],
                       "description": "adjusted (mặc định) = ưu tiên giá hải quan điều chỉnh; declared = chỉ giá khai báo."},
        "compare_keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 4,
                             "description": "Tùy chọn: 1–4 mặt hàng / hoạt chất KHÁC để so với keyword."},
    }},
    handler=_run_stats,
)

CUSTOMS_BUY_TIMING_SPEC = ToolSpec(
    name="customs_buy_timing",
    description=(
        "Tư vấn THỜI ĐIỂM MUA một mặt hàng / hoạt chất dựa trên giá nhập khẩu theo tháng từ tờ khai "
        "hải quan. Gọi khi người dùng hỏi 'nên mua atrazine lúc nào', 'có nên mua atrazine lúc này "
        "không', 'tháng nào rẻ nhất', 'có nên mua trước để tồn kho không'. BẮT BUỘC khi trả lời: "
        "(1) nói giá tháng gần nhất (`now.latest_month`, `now.latest_wavg`) đang THẤP / TRUNG BÌNH / "
        "CAO so với các tháng khác (`now.price_level`, `now.pct_months_cheaper`) và xu hướng "
        "(`now.trend_3_months`, chỉ tính trên tháng đủ dữ liệu); `now.reliable` false thì nói tháng đó "
        "quá ít dòng và lấy `now.reference_month` (tháng đủ dữ liệu gần nhất) làm mốc chính; `now.stale` true "
        "thì nói dữ liệu đã cũ `now.data_age_days` ngày, giá hôm nay có thể đã khác; "
        "(2) chỉ đề xuất `recommended_month` — tháng rẻ nhất trong số tháng ĐỦ dữ liệu; nếu "
        "`cheapest_month_any.reliable` là false thì nói rõ tháng đó rẻ hơn nhưng quá ít dòng để tin; "
        "(3) nhắc lại ý của `caveat` và mức `confidence` — với 'thấp' KHÔNG được khẳng định mùa vụ; "
        "(4) nhắc `not_known`: đây là góc nhìn GIÁ THỊ TRƯỜNG, chưa xét tồn kho / nhu cầu / hạn dùng "
        "của công ty — kết luận dạng 'dữ liệu nghiêng về …', không ra lệnh mua; (5) nêu `alerts` nếu có."),
    parameters={"type": "object", "properties": dict(_FILTER_PROPS)},
    handler=_run_timing,
)

CUSTOMS_MARKET_SPEC = ToolSpec(
    name="customs_market",
    description=(
        "Bức tranh THỊ TRƯỜNG nhập khẩu một mặt hàng / hoạt chất từ tờ khai hải quan: doanh nghiệp "
        "nhập nhiều nhất (gộp theo mã số thuế, kèm thị phần + giá bình quân), đối tác nước ngoài bán "
        "nhiều nhất, nước xuất xứ, và 5 lô gần nhất (ngày, lượng, giá, xuất xứ, bên bán, bên mua). "
        "Gọi khi hỏi 'ai đang nhập atrazine nhiều nhất', 'mua atrazine của ai, từ nước nào', 'lô "
        "gần nhất giá bao nhiêu'. Cần keyword hoặc hs_code. Nêu rõ đơn vị đang xem."),
    parameters={"type": "object", "properties": {
        **_FILTER_PROPS,
        "limit": {"type": "integer", "minimum": 1, "maximum": 20,
                  "description": "Số dòng mỗi bảng xếp hạng (mặc định 10)."},
    }},
    handler=_run_market,
)

CUSTOMS_LEGAL_CHECK_SPEC = ToolSpec(
    name="customs_legal_check",
    description=(
        "Tra PHÁP LÝ và THUẾ nhập khẩu: (a) hóa chất có trong danh mục nào — hoạt chất CẤM (TT 75/2025), "
        "tiền chất / Phụ lục I–III, có NGƯỠNG KHỐI LƯỢNG (NĐ 24/2026 Phụ lục IV), phải công bố theo lô "
        "(TT 01/2026) — tra theo tên, số CAS hoặc công thức (H2SO4); (b) thuế suất thông thường, ưu "
        "đãi MFN, VAT, thuế theo hiệp định FTA của một mã HS. Gọi khi hỏi 'H2SO4 có phải khai báo "
        "không', 'ammonia ngưỡng bao nhiêu kg', 'carbosulfan có bị cấm không', 'thuế nhập mã 38089199'. "
        "Khi trả lời: chỉ nói đúng dữ liệu tool trả về, nhắc `note`; KHÔNG tự nêu mức phạt; "
        "`not_found` true thì nói không có trong danh mục đã nạp — KHÔNG kết luận là được phép."),
    parameters={"type": "object", "properties": {
        "query": {"type": "string", "description": "Tên hóa chất, số CAS hoặc công thức, ví dụ 'Ammonia', "
                                                    "'7664-41-7', 'H2SO4'."},
        "hs_code": {"type": "string", "description": "Mã HS cần tra thuế, ít nhất 4 chữ số, ví dụ '38089199'."},
    }},
    handler=_run_legal,
)
