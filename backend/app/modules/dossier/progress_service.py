"""Đọc / ghi TIẾN ĐỘ hồ sơ theo từng chứng từ. Xem `progress_model.py`.

⚠️ **Mặc định sống trong mã nguồn, không sống dưới DB.** Cặp (chứng từ × hồ sơ)
chưa ai động tới thì KHÔNG có dòng nào — `merge` trả bộ giá trị mặc định. Đẻ sẵn
n×m dòng rỗng lúc mở phiếu thì mỗi lượt xem một tờ đơn là một lượt GHI vào DB,
và nhật ký thao tác ngập dòng «đã tạo» cho những thứ chưa ai đụng vào.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .constants import DP_DONE, DP_IDLE, DP_STATUS_LABELS
from .progress_model import DossierProgress

#  Bộ giá trị của một cặp CHƯA có dòng. Giữ ở một chỗ để đường đọc và đường ghi
#  không lệch nhau: `merge` dựng nó, `upsert` dựng dòng mới cũng từ nó.
DEFAULTS = {
    "status": DP_IDLE,
    "required": True,
    "assignee_id": 0,
    "planned_date": None,
    "note": "",
    "file_note": "",
}

#  Những ô đường ghi nhận. Khai một chỗ, đừng liệt kê lại ở controller — thêm
#  cột mà quên sửa một trong hai nơi thì ô mới lưu được mà không đọc ra, hoặc
#  ngược lại, và cả hai đều im lặng.
WRITABLE = tuple(DEFAULTS)


def progress_map(db: Session, doc_kind: str, doc_id: int) -> dict[int, DossierProgress]:
    """Mọi dòng tiến độ của MỘT chứng từ, tra theo `dossier_id`.

    Một truy vấn cho cả thẻ, bất kể bao nhiêu tờ hồ sơ — đừng gọi trong vòng lặp.
    """
    rows = (
        db.query(DossierProgress)
        .filter(
            DossierProgress.doc_kind == doc_kind,
            DossierProgress.doc_id == doc_id,
        )
        .all()
    )
    return {row.dossier_id: row for row in rows}


def merge(row: DossierProgress | None) -> dict:
    """Bộ trường tiến độ của một tờ hồ sơ — dòng thật, hoặc mặc định khi chưa có."""
    if row is None:
        values = dict(DEFAULTS)
    else:
        values = {key: getattr(row, key) for key in WRITABLE}

    planned = values["planned_date"]
    return {
        "progress_status": values["status"],
        "progress_status_label": DP_STATUS_LABELS.get(values["status"], ""),
        "progress_done": values["status"] == DP_DONE,
        "required": values["required"],
        "assignee_id": values["assignee_id"],
        "planned_date": planned.isoformat() if isinstance(planned, date) else None,
        "progress_note": values["note"],
        "file_note": values["file_note"],
        #  Cặp chưa ai động tới thì `False`. Giao diện KHÔNG dùng cờ này để vẽ
        #  khác đi — nó chỉ để gỡ lỗi và để câu trả lời của API tự nói ra rằng
        #  «chưa bắt đầu» ở đây là mặc định chứ không phải ai đó đặt về đó.
        "progress_saved": row is not None,
    }


def upsert(
    db: Session,
    doc_kind: str,
    doc_id: int,
    dossier_id: int,
    values: dict,
) -> DossierProgress:
    """Ghi tiến độ của MỘT cặp — có dòng thì sửa, chưa có thì tạo.

    `values` chỉ được mang các khóa trong `WRITABLE`; khóa nào không gửi thì giữ
    nguyên giá trị đang có (đường ghi là PATCH, không phải PUT).
    """
    row = (
        db.query(DossierProgress)
        .filter(
            DossierProgress.doc_kind == doc_kind,
            DossierProgress.doc_id == doc_id,
            DossierProgress.dossier_id == dossier_id,
        )
        .first()
    )
    if row is None:
        #  ⚠️ Dựng từ `DEFAULTS` rồi mới chồng `values` lên. Bỏ bước này thì
        #  dòng mới nhận mặc định của CỘT, mà `required` mặc định `True` ở cột
        #  còn người dùng vừa bỏ tick — giá trị họ gửi bị nuốt, im lặng.
        row = DossierProgress(
            doc_kind=doc_kind,
            doc_id=doc_id,
            dossier_id=dossier_id,
            **DEFAULTS,
        )
        db.add(row)

    for key in WRITABLE:
        if key in values:
            setattr(row, key, values[key])

    db.flush()
    return row


def pending_depends(depends: list[int], done_ids: set[int], alive: set[int]) -> list[int]:
    """Những tờ tiên quyết CHƯA xong — rỗng nghĩa là tờ này mở khóa.

    ⚠️ Lọc theo `alive` (tập hồ sơ còn áp dụng cho phiếu): điều kiện áp dụng đổi
    sau khi đã khai tiên quyết thì id cũ thành ID CHẾT, và coi id chết là «chưa
    xong» sẽ khóa tờ kia vĩnh viễn bằng một tờ không còn hiện ra ở đâu. Cùng lối
    xử lý với `report_service` khi lọc `depends` qua `alive_ids`.
    """
    return [i for i in depends if i in alive and i not in done_ids]
