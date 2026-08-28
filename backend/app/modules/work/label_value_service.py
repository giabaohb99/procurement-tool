"""Phân hệ Dự án — GHI giá trị cho trường tùy biến, sáu kiểu (B-13).

Tách khỏi `task_service` vì đây là một luật riêng và khá dày: mỗi kiểu nhận một
loại giá trị khác nhau, và mỗi kiểu có một cách hỏng riêng.

**Bất biến quan trọng nhất:** ràng buộc "một trường chỉ một giá trị" trước đây
do unique `(task_id, field_id)` dưới CSDL giữ, nhưng kiểu CHỌN NHIỀU cần nhiều
dòng nên unique đó đã bị gỡ ở migration `9e357b249200`. Từ nay luật ấy nằm ở
`write_value` — nó **xóa sạch dòng cũ của trường rồi mới ghi**. Bỏ qua bước xóa
là task lặng lẽ mọc hai giá trị cho một trường chọn-một, và giao diện chỉ vẽ cái
đầu tiên nên không ai thấy.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.work.label_model import (WorkLabelField, WorkLabelOption,
                                          WorkTaskLabel)
from app.modules.work.model import LABEL_TYPES_WITH_OPTIONS, WorkLabelFieldType

#  Trần số giá trị của một trường CHỌN NHIỀU trên một task. Không chặn thì một
#  lời gọi gửi mười nghìn id là mười nghìn dòng, và thẻ kanban dài vô tận.
MAX_MULTI_VALUES = 50

_DATE_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}")


def write_value(db: Session, field: WorkLabelField, task_id: int, value,
                user_id: int) -> None:
    """Ghi giá trị của MỘT trường cho MỘT task. `value = None`/rỗng = bỏ chọn.

    Hình dạng `value` theo kiểu trường:
    - chọn một → `option_id` (int)
    - chọn nhiều → danh sách `option_id`
    - người → `employee_id` (int)
    - số → số hoặc chuỗi số
    - ngày → chuỗi `YYYY-MM-DD`
    - chữ → chuỗi

    Không commit — nơi gọi tự quyết mốc giao dịch.
    """
    kind = WorkLabelFieldType(field.field_type)

    #  XÓA TRƯỚC, ghi sau: giữ bất biến "chọn một thì đúng một dòng" mà không
    #  cần đọc rồi so từng dòng.
    (db.query(WorkTaskLabel)
     .filter(WorkTaskLabel.task_id == task_id, WorkTaskLabel.field_id == field.id)
     .delete(synchronize_session=False))

    for row in _build_rows(db, field, kind, task_id, value):
        row.created_by = user_id
        row.updated_by = user_id
        db.add(row)


def _build_rows(db: Session, field: WorkLabelField, kind: WorkLabelFieldType,
                task_id: int, value) -> list[WorkTaskLabel]:
    def blank() -> WorkTaskLabel:
        return WorkTaskLabel(task_id=task_id, field_id=field.id)

    if kind in LABEL_TYPES_WITH_OPTIONS:
        ids = value if isinstance(value, list) else ([] if value is None else [value])
        if not ids:
            return []
        if kind is WorkLabelFieldType.SINGLE and len(ids) > 1:
            raise HTTPException(400, "Trường này chỉ chọn được một giá trị")
        if len(ids) > MAX_MULTI_VALUES:
            raise HTTPException(400, f"Mỗi trường tối đa {MAX_MULTI_VALUES} giá trị")
        rows = []
        for option_id in dict.fromkeys(ids):      # bỏ trùng, GIỮ thứ tự người gửi
            option = db.get(WorkLabelOption, option_id)
            if not option or option.field_id != field.id:
                raise HTTPException(400, "Giá trị nhãn không thuộc trường này")
            row = blank()
            row.option_id = option.id
            rows.append(row)
        return rows

    if value is None or value == "":
        return []

    if kind is WorkLabelFieldType.PERSON:
        row = blank()
        row.value_employee_id = _as_int(value, "Người phụ trách của trường không hợp lệ")
        return [row]

    if kind is WorkLabelFieldType.NUMBER:
        row = blank()
        row.value_number = _as_decimal(value)
        return [row]

    if kind is WorkLabelFieldType.DATE:
        row = blank()
        row.value_date = _as_date(value)
        return [row]

    row = blank()
    #  Cắt đúng bề rộng cột: gửi 10.000 ký tự mà không cắt thì MySQL nhận
    #  `Data too long` và cả lời gọi hỏng, thay vì lưu phần đọc được.
    row.value_text = str(value).strip()[:500]
    return [row]


def _as_int(value, message: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, message)


def _as_decimal(value) -> Decimal:
    try:
        return Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise HTTPException(400, "Giá trị của trường số không phải là số")


def _as_date(value) -> str:
    """Chỉ nhận đúng `YYYY-MM-DD`. Nhận bừa thì cột ngày lẫn cả chuỗi rác, và
    mọi phép so sánh ngày (quá hạn, lọc) im lặng cho kết quả sai."""
    text = str(value).strip()
    #  Phải có CẢ khuôn cứng lẫn strptime: `strptime` một mình nhận luôn
    #  "2026-9-1" (thiếu số 0), mà cột này so sánh bằng CHUỖI nên "2026-9-1"
    #  đứng sau "2026-12-31" — quá hạn và lọc theo ngày sai mà không báo gì.
    if not _DATE_SHAPE.fullmatch(text):
        raise HTTPException(400, "Ngày phải theo dạng YYYY-MM-DD")
    try:
        datetime.strptime(text, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Ngày không có thật")
    return text
