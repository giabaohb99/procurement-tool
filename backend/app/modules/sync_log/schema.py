"""Dạng trả ra của một dòng sổ đồng bộ.

Chỉ có hàm dựng dict, không có lớp Pydantic: đây là màn CHỈ-XEM, không có body
ghi nào cần kiểm kiểu (nút "Chạy lại" chỉ nhận id trên đường dẫn). Mã số trả kèm
nhãn để giao diện khỏi chép bảng nhãn sang TypeScript (R2/QĐ-11).

⚠️ `payload` CỐ Ý không có trong danh sách. Nó là nguyên cục JSON bên kia gửi
sang — có thể vài trăm KB và thường mang dữ liệu cá nhân; kéo cả trang 50 dòng
là vừa nặng vừa phơi thứ không ai cần nhìn. Mở đúng một dòng thì mới trả.
"""
from .constants import ACTION_LABELS, DIRECTION_LABELS, GRAIN_LABELS, STATUS_LABELS


def serialize_entry(row) -> dict:
    """Một dòng cho màn danh sách.

    Trả MỘT hình dạng cho cả hai hạt: dòng bản ghi để trống mấy ô của lượt chạy
    (`job`, con trỏ, ba số đếm) và ngược lại. Một hình dạng thì bảng, ô lọc và
    kiểu TypeScript cũng chỉ có một bản.
    """
    return {
        "id": row.id,
        "source": row.source,
        "source_label": row.source_label,
        "grain": row.grain,
        "grain_label": GRAIN_LABELS.get(row.grain, ""),
        "run_id": row.run_id or 0,
        "job": row.job or "",
        "job_label": row.job_label,
        "direction": row.direction,
        "direction_label": DIRECTION_LABELS.get(row.direction, ""),
        "entity": row.entity,
        "entity_label": row.entity_label,
        "action": row.action,
        "action_label": ACTION_LABELS.get(row.action, ""),
        "legacy_id": row.legacy_id or "",
        "local_id": row.local_id or 0,
        "status": row.status,
        "status_label": STATUS_LABELS.get(row.status, ""),
        "message": row.message or "",
        "content_hash": row.content_hash or "",
        "event_id": row.event_id or "",
        "attempt_count": row.attempt_count or 0,
        "last_tried_at": row.last_tried_at or "",
        "finished_at": row.finished_at or "",
        "cursor_from": row.cursor_from or "",
        "cursor_to": row.cursor_to or "",
        "fetched": row.fetched or 0,
        "written": row.written or 0,
        "skipped": row.skipped or 0,
        "warnings": row.warning_list,
        "warning_labels": row.warning_label_list,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def serialize_detail(row) -> dict:
    """Một dòng mở rộng: kèm NGUYÊN CỤC dữ liệu bên kia gửi sang.

    Không cố `json.loads` rồi trả về object: cục đó có thể không phải JSON hợp lệ
    (đúng lúc hỏng thì càng hay không hợp lệ), mà chỗ này tồn tại chính là để
    người đi tra nhìn thấy thứ đã thật sự nhận được.
    """
    data = serialize_entry(row)
    data["payload"] = row.payload or ""
    return data
