# -*- coding: utf-8 -*-
"""LỊCH SỬ PHÊ DUYỆT PHẢI CÒN SAU KHI LUỒNG DUYỆT XONG (19/09/2026).

Lỗi đã bắt được trên dev: phiếu đặt xe DX000932 duyệt xong, trang chi tiết
KHÔNG còn thẻ «Luồng duyệt nhiều bước» lẫn «Lịch sử phê duyệt» — trong khi phiếu
đóng dấu DD000864 thì có. Nhìn qua tưởng đặt xe không được ghi nhận luồng duyệt;
thật ra phiên duyệt + dấu vết nằm đủ dưới DB, chỉ là không ai vẽ ra.

Nguyên nhân: trang chi tiết gác thẻ bằng `approval_running` — cờ "ĐANG chạy".
Luồng đặt xe của app cũ ("Duyệt tự động bởi HOD") chỉ MỘT bước nên đóng ngay khi
ký, cờ tắt tức thì và dấu vết không bao giờ kịp hiện. Phiếu dấu còn thấy chỉ vì
luồng ba bước của nó đang dở.

Câu hỏi đúng là "phiếu này ĐÃ TỪNG vào bộ máy chưa" → `latest_instance` +
`approval_instance_id`. Hai bài dưới canh đúng chỗ đó: một bài cho hàm tra cứu,
một bài cho cái cờ mà giao diện đọc.
"""
import pytest

from app.modules.approval import instance_service
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_RUNNING,
                                                 ApprovalInstance)

ACTOR = 1


def _make_instance(db, entity: str, entity_id: int, status: int) -> ApprovalInstance:
    row = ApprovalInstance(
        entity=entity, entity_id=entity_id, entity_code="DX000932",
        entity_title="Phiếu thử", flow_id=1, flow_version=1, flow_snapshot="{}",
        status=status, current_seq=1, created_by=ACTOR, updated_by=ACTOR,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@pytest.mark.parametrize("status", [INSTANCE_RUNNING, INSTANCE_APPROVED])
def test_latest_instance_survives_a_finished_flow(db, status):
    """`latest_instance` trả phiên kể cả đã đóng; `running_instance` thì không."""
    inst = _make_instance(db, "vehicle_booking", 932, status)

    assert instance_service.latest_instance(db, "vehicle_booking", 932) is not None
    assert instance_service.latest_instance(db, "vehicle_booking", 932).id == inst.id

    running = instance_service.running_instance(db, "vehicle_booking", 932)
    assert (running is not None) is (status == INSTANCE_RUNNING)


def test_latest_instance_does_not_leak_across_entities(db):
    """Cùng một `entity_id` ở hai phân hệ khác nhau không được lẫn vào nhau.

    `entity_id` là số đếm riêng của từng bảng nên trùng nhau là chuyện thường:
    phiếu dấu 932 và phiếu đặt xe 932 cùng tồn tại. Quên lọc `entity` thì trang
    này vẽ dấu vết của phiếu kia — rò dữ liệu, không chỉ vẽ sai.
    """
    _make_instance(db, "vehicle_booking", 932, INSTANCE_APPROVED)

    assert instance_service.latest_instance(db, "seal_request", 932) is None
    assert instance_service.latest_instance(db, "vehicle_booking", 931) is None


def test_latest_instance_picks_the_newest_round(db):
    """Phiếu bị trả về rồi trình lại có NHIỀU phiên — trang chi tiết lấy phiên mới nhất."""
    _make_instance(db, "seal_request", 864, INSTANCE_APPROVED)
    moi = _make_instance(db, "seal_request", 864, INSTANCE_RUNNING)

    assert instance_service.latest_instance(db, "seal_request", 864).id == moi.id
