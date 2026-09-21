"""ĐIỀU KIỆN ÁP DỤNG của hồ sơ — *«giấy này phải kèm theo chứng từ nào»* (21/09/2026).

Mỗi tờ hồ sơ khai hai thứ: **áp cho loại chứng từ nào** (`apply_doc_kinds`) và
**dòng hàng phải thỏa gì** (`apply_conditions`). Trang chi tiết của chứng từ hỏi
ngược lại: *«có hồ sơ nào phải kèm theo tôi không?»*

    apply_doc_kinds  = ["purchase_order", "survey_request"]
    apply_conditions = [{"field": "product_code", "op": "in",
                         "value": ["SP-001", "SP-002"]}]

Các dòng điều kiện nối nhau bằng **VÀ**, và được soi trên **TỪNG DÒNG HÀNG** một:
chứng từ khớp khi **có ít nhất một dòng** thỏa **tất cả** điều kiện. Cần HOẶC thì
khai thành hai tờ hồ sơ, hoặc dùng `in` với danh sách — cùng lý lẽ với
`approval/condition_service.py`, nơi mượn lại hình dạng này. **Không import chéo
sang đó**: bộ máy duyệt soi bối cảnh của cả PHIẾU (tổng tiền, pháp nhân), còn
chỗ này soi từng DÒNG, nên gộp một hàm là hai nghĩa chen nhau trong một chữ.

⚠️ **Hai ca rỗng, hai nghĩa khác hẳn nhau** — nhầm là hỏng theo hai kiểu ngược nhau:
  * `apply_doc_kinds` rỗng → hồ sơ **không bao giờ** hiện ra ở đâu cả. Đây là
    trạng thái của 100% hồ sơ đang có, nên mặc định phải là nó.
  * `apply_doc_kinds` có, `apply_conditions` rỗng → áp cho **MỌI** phiếu loại
    đó. Ca thật (giấy phép kinh doanh kèm mọi đơn mua hàng) nhưng dễ bật nhầm,
    nên giao diện phải nói thành câu chứ đừng để người dùng suy ra từ bảng trống.
"""
from __future__ import annotations

#  ---- Loại chứng từ áp dụng được ----
#  `entity` dùng để gác cửa thứ hai ở controller: đọc được hồ sơ chưa đủ, phải
#  đọc được CHÍNH CHỨNG TỪ đó — xem ghi chú ở `controller.applicable_dossiers`.
DOC_KINDS: dict[str, dict[str, str]] = {
    "purchase_request": {"label": "Yêu cầu mua hàng", "entity": "purchase_request"},
    "purchase_order": {"label": "Đơn mua hàng", "entity": "purchase_order"},
    "survey_request": {"label": "Yêu cầu báo giá", "entity": "survey_request"},
    "survey": {"label": "Phiếu khảo sát", "entity": "survey"},
}

#  ---- Chiều khai điều kiện ----
#  Cố ý chỉ HAI. Cả hai đều là cột có thật trên dòng hàng của cả bốn loại chứng
#  từ (trừ ca YCBG ghi ở dưới), nên không chiều nào là lời hứa suông.
FIELDS: dict[str, str] = {
    "product_code": "Sản phẩm",
    "item_group": "Phân loại VTBB/NL",
}

#  Chỉ phép so sánh có nghĩa với CHUỖI. Không có `gt`/`lt` như bộ máy duyệt: so
#  mã sản phẩm lớn hơn nhỏ hơn thì ra một câu không ai đọc được nghĩa.
OPS: dict[str, str] = {
    "eq": "là",
    "ne": "khác",
    "in": "thuộc",
    "not_in": "không thuộc",
    "contains": "chứa",
}

MAX_CONDITIONS = 10
MAX_VALUES = 50
MAX_VALUE_LEN = 100


def validate_doc_kinds(raw) -> list[str]:
    """Lọc về danh sách mã hợp lệ, không trùng, giữ thứ tự khai."""
    if not isinstance(raw, list):
        return []
    seen: list[str] = []
    for item in raw:
        if isinstance(item, str) and item in DOC_KINDS and item not in seen:
            seen.append(item)
    return seen


def validate_conditions(raw) -> list[dict]:
    """Kiểm bộ điều kiện, NÉM lỗi khi sai — khác `parse()` của bộ máy duyệt.

    ⚠️ Bên duyệt cố ý nuốt lỗi vì có nhánh mặc định đỡ; ở đây thì không: khai sai
    mà im lặng bỏ qua nghĩa là người dùng bấm Lưu, thấy báo thành công, rồi đi
    tin rằng hồ sơ đã được gắn điều kiện — trong khi nó sẽ không bao giờ hiện ra
    ở đâu. Sai lúc KHAI thì chặn ngay lúc khai.
    """
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        raise ValueError("Điều kiện áp dụng phải là một danh sách")
    if len(raw) > MAX_CONDITIONS:
        raise ValueError(f"Tối đa {MAX_CONDITIONS} dòng điều kiện")

    out: list[dict] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Dòng điều kiện {index} không hợp lệ")
        field = row.get("field")
        op = row.get("op")
        if field not in FIELDS:
            raise ValueError(
                f"Dòng {index}: chiều điều kiện phải là một trong "
                + ", ".join(f"{k} ({v})" for k, v in FIELDS.items())
            )
        if op not in OPS:
            raise ValueError(
                f"Dòng {index}: phép so sánh phải là một trong " + ", ".join(OPS)
            )
        out.append({"field": field, "op": op, "value": _clean_value(row.get("value"), op, index)})
    return out


def _clean_value(value, op: str, index: int):
    """Chuẩn hoá giá trị: `in`/`not_in` ra DANH SÁCH, còn lại ra CHUỖI."""
    if op in ("in", "not_in"):
        items = value if isinstance(value, list) else [value]
        cleaned = [str(v).strip() for v in items if str(v or "").strip()]
        if not cleaned:
            raise ValueError(f"Dòng {index}: «{OPS[op]}» cần ít nhất một giá trị")
        if len(cleaned) > MAX_VALUES:
            raise ValueError(f"Dòng {index}: tối đa {MAX_VALUES} giá trị")
        for item in cleaned:
            if len(item) > MAX_VALUE_LEN:
                raise ValueError(f"Dòng {index}: mỗi giá trị tối đa {MAX_VALUE_LEN} ký tự")
        return cleaned

    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Dòng {index}: chưa nhập giá trị để so sánh")
    if len(text) > MAX_VALUE_LEN:
        raise ValueError(f"Dòng {index}: giá trị tối đa {MAX_VALUE_LEN} ký tự")
    return text


def matches_line(conditions: list[dict], line: dict) -> bool:
    """Một dòng hàng có thỏa TẤT CẢ điều kiện không. Không khai = thỏa."""
    if not conditions:
        return True
    return all(_one(row, line) for row in conditions)


def _one(row: dict, line: dict) -> bool:
    #  ⚠️ So sánh KHÔNG phân biệt hoa thường và bỏ khoảng trắng hai đầu. Mã sản
    #  phẩm gõ tay ở bốn màn khác nhau, và «sp-001 » với «SP-001» là cùng một
    #  thứ với người dùng — khớp đúng từng byte thì điều kiện im lặng trượt.
    actual = str(line.get(row["field"]) or "").strip().casefold()
    op = row["op"]
    value = row["value"]

    #  Ô rỗng CHỈ khớp `ne` / `not_in`. Không chặn riêng thì dòng YCBG chưa chốt
    #  phương án (không có mã SP) lọt vào mọi điều kiện `contains` giá trị rỗng.
    if not actual:
        return op in ("ne", "not_in")

    if op in ("in", "not_in"):
        pool = {str(v).strip().casefold() for v in value}
        return (actual in pool) if op == "in" else (actual not in pool)

    wanted = str(value).strip().casefold()
    if op == "eq":
        return actual == wanted
    if op == "ne":
        return actual != wanted
    if op == "contains":
        return wanted in actual
    return False


def reason_of(conditions: list[dict], line: dict, doc_kind: str) -> str:
    """Câu LÝ DO vì sao hồ sơ này hiện ra — dựng ở backend, không dựng ở TypeScript.

    Cùng lối với `approval/steps_service._summary`: bản in sau này cần đúng câu
    đó, mà chép luật sang TS rồi thì hai bên lệch nhau lúc nào không ai biết.
    """
    if not conditions:
        return f"Áp cho mọi {DOC_KINDS[doc_kind]['label'].lower()}"

    #  Phiếu khảo sát không có bảng dòng — số thứ tự dòng của nó vô nghĩa.
    where = "" if doc_kind == "survey" else f"dòng {line.get('no', 0)} "
    parts = []
    for row in conditions:
        actual = str(line.get(row["field"]) or "").strip()
        parts.append(f"{FIELDS[row['field']].lower()} «{actual}»")
    return f"vì {where}có " + " và ".join(parts)


#  ---------------------------------------------------------------------------
#  BỐI CẢNH DÒNG HÀNG của từng loại chứng từ
#  ---------------------------------------------------------------------------
#  ⚠️ Nhập model NGAY TRONG HÀM, không nhập ở đầu tệp. Bốn module chứng từ đều
#  không biết gì về phân hệ Hồ sơ, và giữ nguyên như vậy là cố ý — nhập ở đầu
#  tệp thì `app.core.all_models` kéo theo một vòng nhập lẫn nhau ngay lúc khởi
#  động, thứ chỉ lộ ra khi chạy thật chứ bộ test SQLite không bắt được.

def doc_lines(db, doc_kind: str, doc_id: int) -> list[dict]:
    """Rút các dòng hàng của một chứng từ về dạng `{no, product_code, item_group}`.

    Chứng từ không tồn tại, hoặc loại lạ, thì ra danh sách rỗng — nơi gọi đã gác
    quyền xong nên ở đây không cần phân biệt «không có» với «không được xem».
    """
    if doc_kind == "purchase_request":
        return _lines_of_purchase_request(db, doc_id)
    if doc_kind == "purchase_order":
        return _lines_of_purchase_order(db, doc_id)
    if doc_kind == "survey_request":
        return _lines_of_survey_request(db, doc_id)
    if doc_kind == "survey":
        return _lines_of_survey(db, doc_id)
    return []


def _numbered(rows) -> list[dict]:
    """`rows` = (mã sản phẩm, phân loại, tên hiển thị).

    ⚠️ `label` là thứ NGƯỜI ĐỌC thấy ở chế độ «Theo dòng hàng», nên nó phải tự
    nói ra dòng nào là dòng nào. Rơi về mã sản phẩm rồi mới tới phân loại: dòng
    YCBG thường chưa có mã, mà cả phiếu toàn «Chưa đặt tên» thì chế độ xem đó
    mất sạch tác dụng.
    """
    return [
        {
            "no": index,
            "product_code": product or "",
            "item_group": group or "",
            "label": (name or "").strip() or product or group or f"Dòng {index}",
        }
        for index, (product, group, name) in enumerate(rows, start=1)
    ]


def _lines_of_purchase_request(db, doc_id: int) -> list[dict]:
    from app.modules.purchase_request.model import PurchaseRequestItem

    rows = (
        db.query(PurchaseRequestItem.product_code, PurchaseRequestItem.item_group,
                 PurchaseRequestItem.product_name)
        .filter(PurchaseRequestItem.pr_id == doc_id)
        .order_by(PurchaseRequestItem.id)
        .all()
    )
    return _numbered(rows)


def _lines_of_purchase_order(db, doc_id: int) -> list[dict]:
    from app.modules.purchase_order.model import POItem

    rows = (
        db.query(POItem.product_code, POItem.item_group, POItem.product_name)
        .filter(POItem.po_id == doc_id)
        .order_by(POItem.id)
        .all()
    )
    return _numbered(rows)


def _lines_of_survey_request(db, doc_id: int) -> list[dict]:
    """YCBG — **dòng chưa có sản phẩm**, đây là hạn chế đã biết của màn này.

    `tab_survey_request_line` chỉ mang `item_group`: bản chất YCBG là đi hỏi
    *nên mua cái gì*, nên lúc lập phiếu chưa ai biết mã SP. Mã chỉ xuất hiện ở
    `tab_survey_request_option.system_product_code` sau khi NSTM khảo sát xong,
    và cột đó **không bắt buộc**.

    Chốt: lấy mã của **phương án ĐÃ CHỌN** (`is_chosen`). Lấy mọi phương án thì
    một dòng ba phương án kéo theo ba tờ hồ sơ, trong đó hai tờ thuộc về sản
    phẩm rốt cuộc không mua. Hệ quả phải nói ra ở giao diện: điều kiện theo SẢN
    PHẨM **im lặng không khớp** trên YCBG cho tới lúc chốt phương án.
    """
    from app.modules.survey_request.model import (SurveyRequestLine,
                                                  SurveyRequestOption)

    lines = (
        db.query(SurveyRequestLine.id, SurveyRequestLine.item_group,
                 SurveyRequestLine.requirement_detail)
        .filter(SurveyRequestLine.survey_request_id == doc_id)
        .order_by(SurveyRequestLine.id)
        .all()
    )
    if not lines:
        return []

    #  MỘT truy vấn cho cả phiếu, không một truy vấn mỗi dòng (bài N+1 của
    #  duoc-CR-322). Phiếu hai chục dòng thì khác biệt là 1 với 21 lượt.
    line_ids = [row[0] for row in lines]
    chosen = dict(
        db.query(SurveyRequestOption.survey_request_line_id,
                 SurveyRequestOption.system_product_code)
        .filter(SurveyRequestOption.survey_request_line_id.in_(line_ids))
        .filter(SurveyRequestOption.is_chosen.is_(True))
        .all()
    )
    #  Nhãn dòng YCBG: PHÂN LOẠI là thứ người dùng gọi tên dòng («Cốc đong»,
    #  «Chai Hdpe»), còn chi tiết thông số thì dài cả câu — ghép cả hai, cắt
    #  phần đuôi để tiêu đề nhóm không tràn hàng.
    return [
        {
            "no": index,
            "product_code": chosen.get(line_id) or "",
            "item_group": group or "",
            "label": _sr_label(index, group, detail),
        }
        for index, (line_id, group, detail) in enumerate(lines, start=1)
    ]


def _sr_label(index: int, group: str | None, detail: str | None) -> str:
    ten = (group or "").strip()
    mo_ta = " ".join((detail or "").split())[:60]
    if ten and mo_ta:
        return f"{ten} — {mo_ta}"
    return ten or mo_ta or f"Dòng {index}"


def _lines_of_survey(db, doc_id: int) -> list[dict]:
    """Phiếu khảo sát — **không có bảng dòng hàng**, cả phiếu là MỘT bối cảnh.

    `item_group` và `item_code` (mã VTBB nội bộ) nằm ở header `tab_survey`. Trả
    về đúng một "dòng" để phần khớp bên trên không phải biết ngoại lệ này.
    """
    from app.modules.survey.model import Survey

    row = (
        db.query(Survey.item_code, Survey.item_group, Survey.item_name)
        .filter(Survey.id == doc_id)
        .first()
    )
    if not row:
        return []
    return _numbered([row])
