"""Giờ VN cho tầng nghiệp vụ — MỘT chỗ duy nhất, container luôn chạy UTC.

Review backend "Quá trình công tác nhân sự" (H2, 03/10/2026): bốn chỗ của
module quá trình công tác (`work_history_rules.apply_gate`,
`work_history_apply_service.apply`/`_apply_concurrent`,
`work_history_serializer.serialize_list`) dùng thẳng `date.today()` — đọc
NGÀY UTC của container, không phải ngày Việt Nam. Từ 00:00 đến 06:59 giờ VN
(tức 17:00-23:59 UTC hôm trước), `date.today()` còn trả NGÀY HÔM TRƯỚC: một
dòng «hôm nay mới có hiệu lực» bị từ chối áp hồ sơ nhầm («Chưa tới ngày hiệu
lực»), và một dòng kiêm nhiệm hết hạn «hôm qua giờ VN» chưa bị gỡ.

Trước đợt này đã có HAI bản chép tay cùng công thức
(`employee/report_headcount_events.vn_today`, `work/report_rows.today_vn`) —
gộp về đây, hai tệp đó nay chỉ re-export.
"""
from datetime import date, datetime

from app.core.export_xlsx import VN_OFFSET


def vn_today() -> date:
    """"Hôm nay" theo giờ Việt Nam (UTC+7) — container luôn chạy giờ UTC."""
    return (datetime.utcnow() + VN_OFFSET).date()
