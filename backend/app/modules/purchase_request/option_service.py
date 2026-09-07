"""PHƯƠNG ÁN MUA gắn lên từng dòng Yêu cầu mua hàng (bao-CR-310).

Luồng: Lập -> TBP duyệt -> Thu mua TIẾP NHẬN (điều phối) -> **NSTM gắn phương án**
-> chốt -> tạo Đơn mua hàng. Khác hướng gộp chứng từ đã khai tử ở chỗ YCMH vẫn là
chứng từ gốc, và Yêu cầu báo giá KHÔNG bị đụng tới — ai quen luồng cũ vẫn đi luồng cũ.

Tách khỏi `service.py` vì tệp đó đã hơn 1000 dòng và toàn bộ phần này chỉ nói chuyện
với một bảng (`tab_purchase_request_item_option`).
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .constants import PR_OPT_MANUAL, PR_OPT_SURVEY
from .model import PurchaseRequest, PurchaseRequestItem, PurchaseRequestItemOption

ENTITY = "purchase_request"

MAX_OPTIONS_PER_LINE = 5   # bằng Yêu cầu báo giá — cùng một việc thì cùng một trần

# Chỉ gắn/chốt phương án khi thu mua ĐÃ TIẾP NHẬN phiếu. `dispatched` là mốc đó
# (xem `service.dispatch_pr` — nó cũng chính là lúc ghi Ngày tiếp nhận, bao-CR-293);
# công tắc `pr_dispatch_enabled` TẮT thì bước duyệt của TBP đẩy thẳng sang trạng thái
# này, nên không cần khai thêm `approved`. Ba trạng thái sau là các bậc «đang mua»
# của bao-CR-292 — phiếu chạy tới đó vẫn còn dòng cần thêm phương án.
STAGE_OPEN = ("dispatched", "processing", "purchasing", "purchased")

# Ô NSTM sửa được sau khi phương án đã nằm trên dòng. Cố ý KHÔNG cho sửa
# `supplier_code` — đổi NCC là một phương án khác, xóa rồi gắn lại chứ không vá tại chỗ.
EDITABLE_FIELDS = ("nstm_note", "snap_price_by_volume", "snap_vat", "snap_moq",
                   "snap_quote_unit", "snap_volume_range", "snap_delivery_time",
                   "snap_delivery_place", "snap_shipping_cost")


def options_of(db: Session, pr_item_id: int) -> list[PurchaseRequestItemOption]:
    return (db.query(PurchaseRequestItemOption)
            .filter(PurchaseRequestItemOption.pr_item_id == pr_item_id)
            .order_by(PurchaseRequestItemOption.public_id.asc(),
                      PurchaseRequestItemOption.id.asc()).all())


def chosen_option_of(db: Session, pr_item_id: int) -> PurchaseRequestItemOption | None:
    """Phương án ĐANG CHỐT của dòng. Đây là nguồn sự thật duy nhất của câu hỏi
    "dòng này chốt phương án chưa" — dòng YCMH cố ý không có cột nào trả lời thay."""
    return (db.query(PurchaseRequestItemOption)
            .filter(PurchaseRequestItemOption.pr_item_id == pr_item_id,
                    PurchaseRequestItemOption.is_chosen == True).first())


def chosen_map(db: Session, pr_item_ids: list[int]) -> dict[int, PurchaseRequestItemOption]:
    """Phương án đã chốt của NHIỀU dòng — một truy vấn cho cả phiếu, đừng gọi
    `chosen_option_of` trong vòng lặp dòng."""
    if not pr_item_ids:
        return {}
    rows = (db.query(PurchaseRequestItemOption)
            .filter(PurchaseRequestItemOption.pr_item_id.in_(pr_item_ids),
                    PurchaseRequestItemOption.is_chosen == True).all())
    return {o.pr_item_id: o for o in rows}


def count_map(db: Session, pr_item_ids: list[int]) -> dict[int, int]:
    """Số phương án của từng dòng — cũng gom một truy vấn."""
    from sqlalchemy import func
    if not pr_item_ids:
        return {}
    rows = (db.query(PurchaseRequestItemOption.pr_item_id, func.count(PurchaseRequestItemOption.id))
            .filter(PurchaseRequestItemOption.pr_item_id.in_(pr_item_ids))
            .group_by(PurchaseRequestItemOption.pr_item_id).all())
    return {pid: int(n or 0) for pid, n in rows}


def get_item(db: Session, pr: PurchaseRequest, item_id: int) -> PurchaseRequestItem:
    """Dòng hàng theo id NHƯNG phải thuộc đúng phiếu đang mở — thiếu vế sau thì gõ id
    dòng của phiếu khác vào URL là gắn phương án xuyên phiếu."""
    it = (db.query(PurchaseRequestItem)
          .filter(PurchaseRequestItem.id == item_id,
                  PurchaseRequestItem.pr_id == pr.id).first())
    if not it:
        raise HTTPException(404, "Không tìm thấy dòng hàng của phiếu này")
    return it


def ensure_stage(pr: PurchaseRequest) -> None:
    """Chặn gắn/sửa/chốt phương án khi phiếu chưa được thu mua tiếp nhận, hoặc đã đóng."""
    if pr.status not in STAGE_OPEN:
        raise HTTPException(400, "Chỉ gắn phương án sau khi thu mua đã tiếp nhận phiếu "
                                 "và trước khi phiếu đóng.")


def ensure_own_line(item: PurchaseRequestItem, emp_code: str, see_all: bool) -> None:
    """NSTM chỉ động vào dòng được giao cho mình; quản lý/người duyệt thì mọi dòng.
    Cùng luật với bộ lọc dòng ở `controller._see_all_items` — nếu không thì màn hình
    giấu dòng của người khác nhưng API vẫn cho sửa."""
    if see_all:
        return
    if (item.assignee or "") != (emp_code or ""):
        raise HTTPException(403, "Dòng này không được giao cho bạn")


def is_requester(pr: PurchaseRequest, user) -> bool:
    """Chủ phiếu: người bấm lập, hoặc người đứng tên yêu cầu (khi hành chính lập giùm)."""
    if pr.created_by == user.id:
        return True
    emp_id = getattr(user, "employee_id", 0) or 0
    return bool(emp_id and getattr(pr, "requester_id", 0) == emp_id)


def ensure_can_choose(pr: PurchaseRequest, user, has_approve: bool) -> None:
    """CHỐT phương án là việc của NGƯỜI YÊU CẦU, không phải của NSTM.

    NSTM chỉ biết giá bao nhiêu; người yêu cầu mới biết mức giá đó **còn đáng mua
    không** — giá vừa nhảy thì họ chốt lại, hoặc thôi để đợt sau. Nên NSTM GẮN
    phương án, người yêu cầu CHỐT.

    Quản lý / Admin thu mua (có `purchase_request.approve`) chốt được luôn: hàng gấp
    thì không bắt đi thêm một người nữa. Khóa `approve` chia đúng ranh giới sẵn có —
    `pur_manager` và `pur_admin` có, `pur_staff` không.
    """
    if is_requester(pr, user) or has_approve:
        return
    raise HTTPException(403, "Chỉ người yêu cầu hoặc quản lý thu mua mới chốt được phương án")


def _next_public_id(existing: list[PurchaseRequestItemOption]) -> int:
    """Số hiệu ẩn danh kế tiếp. Đếm theo số LỚN NHẤT đang có chứ không theo số lượng:
    xóa phương án 2 trong ba phương án rồi gắn mới sẽ ra "Phương án 4", không đụng số cũ."""
    return max((o.public_id or 0) for o in existing) + 1 if existing else 1


def _label(public_id: int) -> str:
    return f"Phương án {public_id}"


def _check_room(db: Session, item: PurchaseRequestItem) -> list[PurchaseRequestItemOption]:
    existing = options_of(db, item.id)
    if len(existing) >= MAX_OPTIONS_PER_LINE:
        raise HTTPException(400, f"Mỗi dòng chỉ gắn được tối đa {MAX_OPTIONS_PER_LINE} phương án")
    return existing


def create_from_survey(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem,
                       psl_id: int, user_id: int) -> PurchaseRequestItemOption:
    """Gắn một dòng khảo sát sản phẩm ĐÃ DUYỆT vào dòng YCMH (chụp lại thông số + giá).

    Chụp chứ không đọc live: phiếu khảo sát sửa giá về sau không được phép làm đổi
    phương án của một YCMH đang chạy."""
    from app.modules.survey.model import SurveyProductLine

    psl = db.get(SurveyProductLine, psl_id)
    if not psl:
        raise HTTPException(404, "Không tìm thấy dòng khảo sát sản phẩm")
    if psl.line_approve != "Đã duyệt":
        raise HTTPException(400, "Dòng khảo sát chưa được duyệt")
    existing = _check_room(db, item)
    if any(o.product_survey_line_id == psl_id for o in existing):
        raise HTTPException(400, "Dòng khảo sát này đã được gắn vào dòng hàng")

    public_id = _next_public_id(existing)
    o = PurchaseRequestItemOption(
        pr_item_id=item.id,
        source=PR_OPT_SURVEY,
        product_survey_line_id=psl.id,
        public_id=public_id,
        display_label=_label(public_id),
        created_by=user_id, updated_by=user_id,
        snap_product_name=psl.product_name or "",
        snap_spec=psl.spec or "",
        snap_origin=psl.origin or "",
        snap_quote_unit=psl.quote_unit or "",
        snap_moq=psl.moq or 0,
        snap_price_by_volume=psl.price_by_volume or 0,
        snap_volume_range=psl.volume_range or "",
        snap_vat=psl.vat or 0,
        snap_delivery_time=psl.delivery_time or "",
        snap_delivery_place=psl.delivery_place or "",
        snap_shipping_cost=psl.shipping_cost or 0,
        snap_sample_ready=bool(psl.sample_ready),
        snap_lab_result=psl.lab_result or "",
        snap_internal_code=psl.internal_code or "",
        supplier_code=psl.supplier_code or "",
        supplier_name=resolve_supplier_name(db, psl.supplier_code or ""),
        supplier_survey_id=psl.survey_id or 0,
        nstm_note=psl.nspt_reason or "",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    record(db, user_id, ENTITY, pr.id, "option_add",
           f"Dòng {item.product_name or item.product_code}: gắn {o.display_label} từ khảo sát #{psl.id}")
    return o


def create_manual(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem,
                  data, user_id: int) -> PurchaseRequestItemOption:
    """NSTM gõ thẳng NCC + giá, không đi qua phiếu khảo sát.

    Cố ý KHÔNG bắt khai lý do: khách chốt là thao tác này phải nhanh. Dấu vết nằm ở
    `source = PR_OPT_MANUAL` — lọc ra soát lúc nào cũng được, còn báo cáo thì không
    trộn giá có nguồn khảo sát với giá gõ tay.
    """
    if not (data.supplier_code or "").strip() and not (data.supplier_name or "").strip():
        raise HTTPException(400, "Phải nhập nhà cung cấp cho phương án")
    existing = _check_room(db, item)
    public_id = _next_public_id(existing)
    code = (data.supplier_code or "").strip()
    o = PurchaseRequestItemOption(
        pr_item_id=item.id,
        source=PR_OPT_MANUAL,
        product_survey_line_id=0,
        public_id=public_id,
        display_label=_label(public_id),
        created_by=user_id, updated_by=user_id,
        # Bỏ trống tên sản phẩm thì lấy theo dòng YCMH — phương án gõ tay là để nhanh,
        # bắt gõ lại đúng cái tên đang nằm ngay trên cùng dòng là thừa.
        snap_product_name=(data.snap_product_name or "").strip() or (item.product_name or ""),
        snap_spec=data.snap_spec or "",
        snap_origin=data.snap_origin or "",
        snap_quote_unit=(data.snap_quote_unit or "").strip() or (item.unit or ""),
        snap_moq=data.snap_moq or 0,
        snap_price_by_volume=data.snap_price_by_volume or 0,
        snap_volume_range=data.snap_volume_range or "",
        snap_vat=data.snap_vat if data.snap_vat is not None else (float(item.vat_pct or 0)),
        snap_delivery_time=data.snap_delivery_time or "",
        snap_delivery_place=data.snap_delivery_place or "",
        snap_shipping_cost=data.snap_shipping_cost or 0,
        snap_sample_ready=False,
        snap_lab_result="",
        snap_internal_code=data.snap_internal_code or "",
        supplier_code=code,
        supplier_name=(data.supplier_name or "").strip() or resolve_supplier_name(db, code),
        supplier_survey_id=0,
        nstm_note=data.nstm_note or "",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    record(db, user_id, ENTITY, pr.id, "option_add",
           f"Dòng {item.product_name or item.product_code}: nhập tay {o.display_label} "
           f"({o.supplier_name or o.supplier_code or 'chưa rõ NCC'})")
    return o


def resolve_supplier_name(db: Session, code: str) -> str:
    """Tên NCC theo mã. Không tìm thấy thì trả lại chính mã — phương án nhập tay hay
    dùng mã chưa có trong danh mục, trả rỗng là mất luôn thông tin duy nhất đang có."""
    if not (code or "").strip():
        return ""
    from app.modules.supplier.model import Supplier
    s = db.query(Supplier).filter(Supplier.code == code).first()
    return s.name if s else code


def get_option(db: Session, item_id: int, oid: int) -> PurchaseRequestItemOption:
    o = (db.query(PurchaseRequestItemOption)
         .filter(PurchaseRequestItemOption.id == oid,
                 PurchaseRequestItemOption.pr_item_id == item_id).first())
    if not o:
        raise HTTPException(404, "Không tìm thấy phương án")
    return o


def update_option(db: Session, item_id: int, oid: int, data, user_id: int) -> PurchaseRequestItemOption:
    """Sửa các ô NSTM được phép chỉnh (xem `EDITABLE_FIELDS`)."""
    o = get_option(db, item_id, oid)
    for k in EDITABLE_FIELDS:
        v = getattr(data, k, None)
        if v is not None:
            setattr(o, k, v)
    o.updated_by = user_id
    db.commit()
    db.refresh(o)
    return o


def delete_option(db: Session, pr: PurchaseRequest, item_id: int, oid: int, user_id: int) -> None:
    o = get_option(db, item_id, oid)
    label = o.display_label
    db.delete(o)
    db.commit()
    record(db, user_id, ENTITY, pr.id, "option_remove", f"Gỡ {label} khỏi dòng #{item_id}")


def choose_option(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem,
                  oid: int, user_id: int) -> PurchaseRequestItemOption:
    """Chốt một phương án cho dòng. Bấm lại đúng phương án đang chốt -> BỎ CHỐT (toggle),
    cùng cách bấm với bên Yêu cầu báo giá."""
    target = get_option(db, item.id, oid)
    already = bool(target.is_chosen)
    for o in options_of(db, item.id):
        o.is_chosen = (o.id == oid) and not already
        if o.is_chosen:
            o.chosen_by = user_id
        o.updated_by = user_id
    db.commit()
    db.refresh(target)
    record(db, user_id, ENTITY, pr.id,
           "option_unchoose" if already else "option_choose",
           f"Dòng {item.product_name or item.product_code}: "
           + ("bỏ chốt " if already else "chốt ") + target.display_label)
    return target
