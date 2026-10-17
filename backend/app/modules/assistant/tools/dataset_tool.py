"""Tool `dataset_query` — truy vấn tổng hợp trên sổ bộ dữ liệu khai báo (ai-CR-210, K12 — T2 doc/erp/21 §5.5).

Dùng khi cần một bảng số chưa có màn báo cáo nào (vd *công nợ còn lại theo NCC và pháp nhân*, *tiền đề nghị thanh toán
theo tháng*). Báo cáo chuẩn của phân hệ Báo cáo thì dùng `report_summary` (T1). Model chỉ chọn tên bộ / chỉ số / chiều /
bộ lọc trong danh sách khai sẵn ở `assistant/datasets/catalog.py`; máy chủ tự tính dưới quyền người hỏi.
"""
from __future__ import annotations

from .base import ToolContext, ToolSpec


def _dataset_query(ctx: ToolContext, args: dict) -> dict:
    from app.modules.assistant import datasets

    key = str(args.get("dataset") or "").strip().lower()
    if not key or args.get("describe"):
        found = [d for d in datasets.describe_all() if not key or d["dataset"] == key]
        if key and not found:
            return datasets.run(ctx, key, {})          # câu lỗi liệt kê bộ hợp lệ
        return {"datasets": found, "note": "Gọi lại với dataset + measures + dimensions + filters đúng mã ở trên."}
    return datasets.run(ctx, key, args)


def _description() -> str:
    from app.modules.assistant import datasets

    parts = []
    for ds in datasets.registry().values():
        parts.append(f"{ds.key} = {ds.label} [chỉ số: {', '.join(m.key for m in ds.measures)}; chiều: "
                     f"{', '.join(d.key for d in ds.dimensions)}; lọc: {', '.join(f.key for f in ds.filters)}]")
    return ("Bảng số TỔNG HỢP tự chọn trên bộ dữ liệu khai sẵn, máy chủ tự cộng trong phạm vi quyền người hỏi — dùng khi "
            "chưa có báo cáo chuẩn (báo cáo chuẩn: report_summary). Bộ: " + " | ".join(parts)
            + ". Tối đa 4 chỉ số × 2 chiều, 500 nhóm; quá thì trả truncated. Không chắc mã thì gọi describe=true. Tiền VND, "
            "căn cứ VAT ở measures[].vat.")


DATASET_QUERY_SPEC = ToolSpec(
    name="dataset_query",
    description=_description(),
    parameters={
        "type": "object",
        "properties": {
            "dataset": {"type": "string", "enum": ["purchase", "payable", "payment_request"],
                        "description": "purchase = mua hàng (lịch sử mua); payable = công nợ phải trả; "
                                       "payment_request = yêu cầu thanh toán."},
            "measures": {"type": "array", "items": {"type": "string"}, "maxItems": 4,
                         "description": "Mã chỉ số (mặc định chỉ số đầu của bộ)."},
            "dimensions": {"type": "array", "items": {"type": "string"}, "maxItems": 2,
                           "description": "Mã chiều để chia nhóm; bỏ trống = chỉ lấy tổng."},
            "filters": {"type": "object", "description": "{mã bộ lọc: giá trị}. Ngày dạng YYYY-MM-DD."},
            "sort": {"type": "string", "enum": ["value_desc", "value_asc", "dimension"],
                     "description": "Xếp nhóm theo chỉ số đầu (giảm / tăng) hay theo mã chiều."},
            "limit": {"type": "integer", "description": "Số nhóm trả về (mặc định 50, trần 500)."},
            "describe": {"type": "boolean", "description": "true = chỉ trả danh mục chỉ số / chiều / bộ lọc của bộ."},
        },
        "required": ["dataset"],
    },
    handler=_dataset_query,
)
