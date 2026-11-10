"""Hợp đồng — biểu thức SQL xếp các cột danh sách KHÔNG xếp thẳng theo cột lưu (duoc-CR-744 lượt d).

Mỗi biểu thức xếp theo đúng chữ đang hiện trên bảng (`contract-crud.tsx`):
- `party_type` (cột "Bên ký kết"): dòng đậm là TÊN đối tượng nên xếp theo `party_name`.
- `contract_type`: lưu mã tiếng Anh, bảng hiện nhãn -> xếp theo chữ cái của NHÃN.
- `expiry` ("Hiệu lực"): giá trị TÍNH từ `end_date` (`controller.expiry_state`) -> xếp theo
  Đã hết hạn < Sắp hết hạn < Còn hiệu lực < Không thời hạn.
- `signed` ("Trạng thái ký"): cờ đúng / sai, Chưa ký < Đã ký.
"""
from datetime import datetime, timedelta

from sqlalchemy import case

from app.core.code_rank_sql import build_value_rank_expression

from .model import Contract

#  Mã loại hợp đồng theo chữ cái của NHÃN (`core/contract_types.py`): Hợp đồng dịch vụ <
#  khuôn mẫu < kinh tế < mua bán < nguyên tắc < vận chuyển < Khác.
CONTRACT_TYPE_LABEL_ORDER = ("service", "template", "economic", "purchase", "principle", "transport",
                             "other")


def _expiry_rank():
    """Hạng tình trạng hạn, cùng mốc với bộ lọc `expiry` của danh sách (hôm nay, +30 ngày)."""
    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    t30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")
    end = Contract.end_date
    return case(
        ((end.is_(None)) | (end == ""), 4),     # bảng hiện "Không thời hạn", không phải ô trống
        (end < tstr, 1),
        (end <= t30, 2),
        else_=3,
    )


def list_sort_allow() -> dict:
    return {
        "party_type": Contract.party_name,
        "contract_type": build_value_rank_expression(Contract.contract_type, CONTRACT_TYPE_LABEL_ORDER),
        "expiry": _expiry_rank(),
        "signed": Contract.signed,
    }
