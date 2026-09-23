"""PHƯƠNG ÁN MUA gắn lên từng dòng Yêu cầu mua hàng (bao-CR-310).

Luồng: Lập -> TBP duyệt -> Thu mua TIẾP NHẬN (điều phối) -> **NSTM gắn phương án**
-> chốt -> tạo Đơn mua hàng. Khác hướng gộp chứng từ đã khai tử ở chỗ YCMH vẫn là
chứng từ gốc, và Yêu cầu báo giá KHÔNG bị đụng tới — ai quen luồng cũ vẫn đi luồng cũ.

Tách khỏi `service.py` vì tệp đó đã hơn 1000 dòng và toàn bộ phần này chỉ nói chuyện
với một bảng (`tab_purchase_request_item_option`).
"""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .constants import PR_OPT_MANUAL, PR_OPT_ORIGINAL, PR_OPT_SURVEY
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
# Ngoại lệ duy nhất (H.10.4): PHƯƠNG ÁN 0 + nhập tay điền/sửa NCC qua `set_option_supplier`.
EDITABLE_FIELDS = ("nstm_note", "snap_price_by_volume", "snap_vat", "snap_moq",
                   "snap_quote_unit", "snap_volume_range", "snap_delivery_time",
                   "snap_delivery_place", "snap_shipping_cost")

OPTION_ZERO_LABEL = "Phương án 0"


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
    """Số phương án NSTM GẮN của từng dòng — cũng gom một truy vấn.

    PHƯƠNG ÁN 0 cố ý KHÔNG đếm (H.10): nó đứng ngoài trần 5, ngoài phép đếm
    "chốt rỗng" (chốt rỗng = không có phương án NSTM nào, H.10.3), và ô
    "x phương án" trên màn cũng chỉ nói về phương án NSTM gắn."""
    from sqlalchemy import func
    if not pr_item_ids:
        return {}
    rows = (db.query(PurchaseRequestItemOption.pr_item_id, func.count(PurchaseRequestItemOption.id))
            .filter(PurchaseRequestItemOption.pr_item_id.in_(pr_item_ids),
                    PurchaseRequestItemOption.source != PR_OPT_ORIGINAL)
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


def options_enabled() -> bool:
    """bao-CR-468 — CÔNG TẮC của cả cụm phương án YCMH (màn Xử lý phương án + thẻ chọn
    phương án trên chi tiết phiếu).

    Nguồn: màn Cấu hình hệ thống (key `pr_options_enabled`, lưu DB) → fallback .env
    (`PR_OPTIONS_ENABLED`, mặc định TẮT). Đổi có hiệu lực ngay, không cần deploy.
    Chỉ chặn đường GHI — ĐỌC luôn mở, vì tắt công tắc không được làm mất dấu những phương
    án đã chốt trên phiếu cũ.
    """
    from app.core import app_settings
    return bool(app_settings.get("pr_options_enabled"))


def ensure_stage(pr: PurchaseRequest) -> None:
    """Chặn gắn/sửa/chốt phương án khi công tắc đang tắt, khi phiếu chưa được thu mua tiếp
    nhận, hoặc khi phiếu đã đóng."""
    if not options_enabled():
        raise HTTPException(400, "Cụm phương án của Yêu cầu mua hàng đang TẮT. "
                                 "Quản trị bật lại ở màn Cấu hình hệ thống thì mới dùng được.")
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


def ensure_line_not_done(item: PurchaseRequestItem) -> None:
    """Dòng đã "chốt hoàn thành xử lý" thì NSTM hết sửa phương án (khuôn YCBG: sau
    complete_sr không gắn/gỡ nữa). Muốn sửa phải nhờ người yêu cầu / quản lý MỞ LẠI
    dòng (`reopen_line`) — một chiều có kiểm soát, không để hai bên giẫm nhau."""
    if item.options_done:
        raise HTTPException(400, "Dòng đã chốt hoàn thành xử lý — muốn sửa phương án "
                                 "hãy nhờ người yêu cầu hoặc quản lý thu mua mở lại dòng")


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
    # Trần 5 chỉ đếm phương án NSTM gắn — PHƯƠNG ÁN 0 đứng ngoài (H.10.1), không thì
    # hệ thống tự sinh một cái là ăn mất một suất của NSTM.
    if sum(1 for o in existing if o.source != PR_OPT_ORIGINAL) >= MAX_OPTIONS_PER_LINE:
        raise HTTPException(400, f"Mỗi dòng chỉ gắn được tối đa {MAX_OPTIONS_PER_LINE} phương án")
    return existing


def ensure_option_zero(db: Session, pr: PurchaseRequest,
                       items: list[PurchaseRequestItem] | None = None) -> int:
    """Sinh PHƯƠNG ÁN 0 cho các dòng chưa có (H.10.1) — idempotent, gọi lại vô hại.

    Ruột chụp từ CHÍNH DÒNG YÊU CẦU (tên hàng, ĐVT, giá đề xuất, VAT, mã hàng) và
    CHƯA có NCC: người yêu cầu im lặng = mua theo đúng yêu cầu gốc. Về kỹ thuật là
    một phương án nhập-tay-do-hệ-thống-tạo (`source = PR_OPT_ORIGINAL`,
    `created_by = 0` đánh dấu hệ thống), đứng NGOÀI trần 5 và ngoài phép đếm chốt
    rỗng. Điểm sinh chính là `service.dispatch_pr`; các đường ĐỌC phương án gọi lại
    hàm này để SINH BÙ cho phiếu đã điều phối từ trước khi có tính năng.

    `public_id = 0` xếp nó lên đầu danh sách và giữ `_next_public_id` bắt đầu từ 1.
    Tick chọn sẵn (H.10.2) CHỈ khi dòng chưa chọn gì khác — sinh bù trên phiếu đang
    chạy không được giật quyền chọn của người đã chọn. KHÔNG ghi nhật ký từng dòng:
    đây là dữ liệu nền sinh kèm phiếu, không phải thao tác của ai.

    bao-CR-468: công tắc TẮT thì không sinh gì cả — đây là đường ghi chạy kèm lúc ĐỌC phiếu,
    để nguyên thì tắt cụm phương án xong hệ thống vẫn lặng lẽ đẻ dữ liệu phương án mỗi lần
    có người mở một phiếu."""
    if not options_enabled():
        return 0
    if pr.status not in STAGE_OPEN:
        return 0
    if items is None:
        items = items_of(db, pr)
    ids = [i.id for i in items]
    if not ids:
        return 0
    has_zero = {o.pr_item_id for o in
                db.query(PurchaseRequestItemOption)
                .filter(PurchaseRequestItemOption.pr_item_id.in_(ids),
                        PurchaseRequestItemOption.source == PR_OPT_ORIGINAL).all()}
    todo = [i for i in items if i.id not in has_zero]
    if not todo:
        return 0
    chosen = chosen_map(db, [i.id for i in todo])
    for i in todo:
        db.add(PurchaseRequestItemOption(
            pr_item_id=i.id,
            source=PR_OPT_ORIGINAL,
            product_survey_line_id=0,
            public_id=0,
            display_label=OPTION_ZERO_LABEL,
            is_chosen=i.id not in chosen,
            chosen_by=0,
            created_by=0, updated_by=0,
            snap_product_name=i.product_name or "",
            snap_quote_unit=i.unit or "",
            snap_price_by_volume=i.price or 0,
            snap_vat=i.vat_pct or 0,
            # Mã hàng CỦA DÒNG chứ không phải mã theo NCC — để phép chép mã H.3.9
            # thành phép đồng nhất khi người ta chốt lại chính yêu cầu gốc.
            snap_internal_code=i.product_code or "",
        ))
    db.commit()
    return len(todo)


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


def update_option(db: Session, item_id: int, oid: int, data, user_id: int,
                  price_only: bool = False) -> PurchaseRequestItemOption:
    """Sửa các ô NSTM được phép chỉnh (xem `EDITABLE_FIELDS`).

    `price_only` là khe nới H.10.4: dòng đã "chốt hoàn thành xử lý" vẫn sửa được
    GIÁ của mọi phương án — và CHỈ giá; gửi kèm trường khác là từ chối cả gói chứ
    không âm thầm bỏ qua, người gọi phải biết mình vừa sửa hụt."""
    o = get_option(db, item_id, oid)
    if price_only:
        extra = [k for k in EDITABLE_FIELDS
                 if k != "snap_price_by_volume" and getattr(data, k, None) is not None]
        if extra:
            raise HTTPException(400, "Dòng đã chốt hoàn thành xử lý — sau chốt chỉ sửa "
                                     "được GIÁ của phương án")
    fields = ("snap_price_by_volume",) if price_only else EDITABLE_FIELDS
    for k in fields:
        v = getattr(data, k, None)
        if v is not None:
            setattr(o, k, v)
    o.updated_by = user_id
    db.commit()
    db.refresh(o)
    return o


def delete_option(db: Session, pr: PurchaseRequest, item_id: int, oid: int, user_id: int) -> None:
    o = get_option(db, item_id, oid)
    if o.source == PR_OPT_ORIGINAL:
        # H.10.1 — phương án 0 là chính dòng yêu cầu đội lốt phương án: gỡ nó đi là
        # dòng mất đường "mua theo đúng yêu cầu gốc", nên không gỡ được.
        raise HTTPException(400, "Phương án 0 sinh từ chính dòng yêu cầu — không gỡ được")
    label = o.display_label
    db.delete(o)
    db.commit()
    record(db, user_id, ENTITY, pr.id, "option_remove", f"Gỡ {label} khỏi dòng #{item_id}")


def choose_option(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem,
                  oid: int, user_id: int) -> PurchaseRequestItemOption:
    """Chốt một phương án cho dòng. Bấm lại đúng phương án đang chốt -> BỎ CHỐT (toggle),
    cùng cách bấm với bên Yêu cầu báo giá.

    H.3.9 — đồng bộ mã hàng khi chốt: dòng CHƯA có mã (`product_code` rỗng) mà phương
    án chốt mang `snap_internal_code` thì chép mã đó lên dòng — ngoại lệ duy nhất
    phương án được ghi vào nhóm trường nhu cầu; nhờ vậy dòng bắt đầu ăn được đồng bộ
    tiến độ `qty_ordered`/`qty_received` (nối theo `product_code`). Bỏ chốt KHÔNG xóa
    mã đã chép: mã đã thành dữ liệu của dòng."""
    target = get_option(db, item.id, oid)
    already = bool(target.is_chosen)
    for o in options_of(db, item.id):
        o.is_chosen = (o.id == oid) and not already
        if o.is_chosen:
            o.chosen_by = user_id
        o.updated_by = user_id
    copied_code = ""
    if not already and not (item.product_code or "").strip():
        code = (target.snap_internal_code or "").strip()
        # CR-047: mỗi mã chỉ đứng ở MỘT dòng trên phiếu — dòng khác đã mang mã này
        # thì thôi không chép, kẻo phép chốt tạo ra phiếu vi phạm luật trùng mã.
        if code and not (db.query(PurchaseRequestItem)
                         .filter(PurchaseRequestItem.pr_id == pr.id,
                                 PurchaseRequestItem.product_code == code,
                                 PurchaseRequestItem.id != item.id).first()):
            item.product_code = code
            copied_code = code
    db.commit()
    db.refresh(target)
    record(db, user_id, ENTITY, pr.id,
           "option_unchoose" if already else "option_choose",
           f"Dòng {item.product_name or item.product_code}: "
           + ("bỏ chốt " if already else "chốt ") + target.display_label
           + (f" · chép mã hàng {copied_code} lên dòng" if copied_code else ""))
    return target


def set_option_supplier(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem,
                        oid: int, data, user_id: int) -> PurchaseRequestItemOption:
    """Điền/sửa NCC trên PHƯƠNG ÁN 0 và phương án NHẬP TAY, kèm sửa giá nếu cần (H.10.4).

    Phương án TỪ KHẢO SÁT không đi qua đây: NCC của nó là dữ kiện khảo sát, đổi NCC
    nghĩa là một phương án khác. Cố ý KHÔNG chặn theo `options_done` — đây chính là
    khe nới sau chốt: thu mua điền NCC ngay trên màn chọn, không phải mở lại dòng."""
    o = get_option(db, item.id, oid)
    if o.source == PR_OPT_SURVEY:
        raise HTTPException(400, "Phương án từ khảo sát không đổi được nhà cung cấp — "
                                 "đổi NCC là một phương án khác")
    code = (data.supplier_code or "").strip()
    name = (data.supplier_name or "").strip()
    if not code and not name:
        raise HTTPException(400, "Phải chọn nhà cung cấp để áp vào phương án")
    o.supplier_code = code
    o.supplier_name = name or resolve_supplier_name(db, code)
    if data.snap_price_by_volume is not None:
        o.snap_price_by_volume = data.snap_price_by_volume
    o.updated_by = user_id
    db.commit()
    db.refresh(o)
    record(db, user_id, ENTITY, pr.id, "option_supplier_set",
           f"Dòng {item.product_name or item.product_code}: áp NCC "
           f"{o.supplier_name or code} vào {o.display_label}")
    return o


def assign_supplier_bulk(db: Session, pr: PurchaseRequest, data, user_id: int,
                         emp_code: str, see_all: bool) -> int:
    """"ÁP 1 NCC CHO NHIỀU DÒNG" trên màn chọn (H.10.5): với mỗi dòng tick, áp NCC
    (kèm giá riêng nếu gửi) vào PHƯƠNG ÁN ĐANG CHỌN của dòng đó.

    Soát TRƯỚC, ghi SAU — một dòng không hợp lệ là từ chối cả lô, không áp nửa vời:
    dòng chưa chọn phương án thì không biết áp vào đâu, dòng đang chọn phương án
    khảo sát thì NCC không sửa tại chỗ (cùng luật `set_option_supplier`)."""
    code = (data.supplier_code or "").strip()
    name = (data.supplier_name or "").strip()
    if not code and not name:
        raise HTTPException(400, "Phải chọn nhà cung cấp để áp")
    if not data.items:
        raise HTTPException(400, "Chưa tick dòng nào để áp nhà cung cấp")
    resolved = name or resolve_supplier_name(db, code)
    rows = []
    for entry in data.items:
        item = get_item(db, pr, entry.item_id)
        ensure_own_line(item, emp_code, see_all)
        chosen = chosen_option_of(db, item.id)
        label = item.product_name or item.product_code or f"#{item.id}"
        if not chosen:
            raise HTTPException(400, f"Dòng {label} chưa chọn phương án nào — "
                                     "không biết áp nhà cung cấp vào đâu")
        if chosen.source == PR_OPT_SURVEY:
            raise HTTPException(400, f"Dòng {label} đang chọn phương án từ khảo sát — "
                                     "không áp đè nhà cung cấp được")
        rows.append((chosen, entry.snap_price_by_volume, label))
    for chosen, price, _ in rows:
        chosen.supplier_code = code
        chosen.supplier_name = resolved
        if price is not None:
            chosen.snap_price_by_volume = price
        chosen.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pr.id, "option_supplier_set",
           f"Áp NCC {resolved or code} cho {len(rows)} dòng: "
           + ", ".join(label for _, _, label in rows))
    return len(rows)


def ensure_line_done(item: PurchaseRequestItem) -> None:
    """Người yêu cầu chỉ CHỌN sau khi NSTM đã chốt hoàn thành dòng (khuôn YCBG:
    chọn phương án mở ra khi phiếu sang survey_done). Chưa chốt mà cho chọn thì
    người yêu cầu chọn trên một danh sách NSTM còn đang gắn dở."""
    if not item.options_done:
        raise HTTPException(400, "NSTM chưa chốt hoàn thành xử lý dòng này — chưa chọn phương án được")


def items_of(db: Session, pr: PurchaseRequest) -> list[PurchaseRequestItem]:
    return (db.query(PurchaseRequestItem)
            .filter(PurchaseRequestItem.pr_id == pr.id)
            .order_by(PurchaseRequestItem.id.asc()).all())


def complete_options(db: Session, pr: PurchaseRequest, user, emp_code: str,
                     see_all: bool, empty_item_ids=None):
    """Chốt PHẦN XỬ LÝ PHƯƠNG ÁN CỦA NGƯỜI GỌI trên phiếu — khuôn `complete_sr`
    của Yêu cầu báo giá: dòng mình phụ trách phải có phương án HOẶC được tick
    "chốt rỗng" (không có NCC phù hợp); quản lý / người thấy hết chốt cả phiếu.

    Dòng đã `options_done` từ trước thì bỏ qua (gọi lại không đổi gì). Dòng vừa
    có phương án vừa bị tick rỗng thì phương án thắng — cùng cách xử của YCBG.
    Trả (số dòng vừa chốt, trong đó bao nhiêu chốt rỗng, cả phiếu xong chưa)."""
    empty_ids = {int(x) for x in (empty_item_ids or [])}
    items = items_of(db, pr)
    if not items:
        raise HTTPException(400, "Phiếu không có dòng hàng nào")
    mine = items if see_all else [i for i in items if (i.assignee or "") == (emp_code or "")]
    if not mine:
        raise HTTPException(403, "Không có dòng nào được giao cho bạn trên phiếu này")
    counts = count_map(db, [i.id for i in mine])
    missing = [i for i in mine
               if not i.options_done and not counts.get(i.id, 0) and i.id not in empty_ids]
    if missing:
        raise HTTPException(400, f"Còn {len(missing)} dòng chưa có phương án — "
                                 "hãy gắn phương án hoặc tick chốt rỗng")
    done_now = empty_now = 0
    for i in mine:
        if i.options_done:
            continue
        if counts.get(i.id, 0):
            i.no_option = False
        else:
            i.no_option = True
            empty_now += 1
        i.options_done = True
        i.updated_by = user.id
        done_now += 1
    db.commit()
    all_done = all(i.options_done for i in items)
    record(db, user.id, ENTITY, pr.id, "options_complete",
           f"Chốt hoàn thành xử lý phương án: {done_now} dòng"
           + (f" (trong đó {empty_now} chốt rỗng)" if empty_now else ""))
    return done_now, empty_now, all_done


def reopen_line(db: Session, pr: PurchaseRequest, item: PurchaseRequestItem, user) -> None:
    """MỞ LẠI dòng đã chốt hoàn thành cho NSTM sửa tiếp — việc của NGƯỜI CHỐT
    (người yêu cầu / quản lý), khuôn "Cần khảo sát lại" của YCBG. Giữ nguyên
    phương án đang chọn nếu có: mở lại là xin thêm/đổi phương án, không phải hủy
    lựa chọn — muốn bỏ chọn thì bấm lại nút chốt trên chính phương án đó."""
    if not item.options_done:
        raise HTTPException(400, "Dòng này chưa chốt hoàn thành — không có gì để mở lại")
    item.options_done = False
    item.no_option = False
    item.updated_by = user.id
    # bao-CR-419: mở lại một dòng là mở lại cả vòng thương lượng — mốc "đã chốt xong
    # lựa chọn" của phiếu phải xóa, kẻo thu mua vẫn thấy dấu cũ và tưởng phiếu đã yên.
    pr.options_chosen_at = None
    pr.options_chosen_by = 0
    db.commit()
    record(db, user.id, ENTITY, pr.id, "options_reopen",
           f"Mở lại xử lý phương án cho dòng {item.product_name or item.product_code}")


def mark_choice_done(db: Session, pr: PurchaseRequest, user) -> int:
    """bao-CR-419 — NGƯỜI YÊU CẦU bấm "Chốt xong lựa chọn" cho CẢ PHIẾU.

    Mặt đối xứng của `complete_options`: NSTM chốt hết phần mình thì người yêu cầu
    vào chọn, chọn xong bấm nút này để trả phiếu lại cho thu mua đi gom đơn.

    Vì sao phải có nút chứ không tự suy: H.10.2 tick sẵn phương án 0 nên dòng nào
    cũng đang có phương án được chọn kể từ lúc điều phối — "im lặng vì đồng ý mua
    theo yêu cầu gốc" và "chưa hề mở phiếu ra xem" cho ra cùng một dữ liệu. Không
    có nút thì thu mua chỉ còn cách đoán, hoặc đợi mãi.

    Chốt theo CẢ PHIẾU chứ không theo dòng (đại ca chốt 17/09): phiếu 20 dòng mà báo
    theo dòng là 20 cái chuông dội vào thu mua.

    Trả về số dòng của phiếu (để câu thông báo nói được đã chốt trên bao nhiêu dòng).
    """
    items = items_of(db, pr)
    if not items:
        raise HTTPException(400, "Phiếu không có dòng hàng nào")
    pending = [i for i in items if not i.options_done]
    if pending:
        raise HTTPException(400, f"Còn {len(pending)} dòng nhân sự thu mua chưa chốt "
                                 "hoàn thành xử lý — chưa chốt xong lựa chọn được")
    if pr.options_chosen_at:
        raise HTTPException(400, "Phiếu đã chốt xong lựa chọn rồi — muốn chọn lại "
                                 "hãy mở lại dòng cần sửa")
    pr.options_chosen_at = datetime.now()
    pr.options_chosen_by = user.id
    pr.updated_by = user.id
    db.commit()
    record(db, user.id, ENTITY, pr.id, "options_choice_done",
           f"Chốt xong lựa chọn phương án cho cả phiếu ({len(items)} dòng)")
    return len(items)


#  =====================================================================
#  CHUÔNG (bao-CR-419) — hai lần bàn giao của luồng phương án
#
#  Trước CR này luồng phương án không có cái chuông nào: NSTM chốt xong thì người
#  yêu cầu không biết tới lượt mình, người yêu cầu chọn xong thì thu mua không biết
#  để vào gom đơn. Hai bên phải hẹn nhau ngoài hệ thống.
#
#  Cả hai chuông đều ĐỢI XONG CẢ PHIẾU mới bắn một lần (đại ca chốt 17/09) — không
#  bắn theo từng dòng.
#  =====================================================================

#  TẮT có chủ ý (đại ca chốt 17/09/2026). Chuông đã viết xong và đã có bài kiểm,
#  nhưng chưa cho chạy thật vì người nhận chuông thứ nhất là NGƯỜI YÊU CẦU, mà
#  người yêu cầu phần lớn vẫn đang dùng giao diện cũ (`frontend/`) — màn chi tiết
#  phiếu bên đó KHÔNG có khu phương án, nên họ sẽ nhận một lời mời vào chọn mà bấm
#  vào thì không thấy chỗ nào để chọn.
#
#  MỞ LẠI: đổi hằng này thành True (chỉ một dòng, không phải viết lại gì), khi
#  giao diện cũ ngừng dùng cho luồng yêu cầu mua hàng, hoặc khi màn chi tiết phiếu
#  bên giao diện cũ có lối dẫn sang khu phương án của giao diện mới.
#
#  Tắt chuông KHÔNG tắt phần còn lại của bao-CR-419: nút "Chốt xong lựa chọn",
#  mốc `options_chosen_at` / `options_chosen_by` và việc mở lại dòng xóa mốc vẫn
#  chạy bình thường — đó là dữ liệu của luồng, không phải thông báo.
OPTION_BELLS_ENABLED = False

def _requester_user_id(db: Session, pr: PurchaseRequest) -> int:
    """Tài khoản của NGƯỜI YÊU CẦU — khuôn `service._notify_expected_changed`:
    tra theo nhân sự `requester_id`, phiếu cũ không có thì lấy người lập phiếu."""
    from app.modules.user.model import User

    if pr.requester_id:
        u = (db.query(User)
             .filter(User.employee_id == pr.requester_id, User.is_active == True)
             .first())
        if u:
            return u.id
    return pr.created_by or 0


def _line_assignee_user_ids(db: Session, items: list[PurchaseRequestItem]) -> list[int]:
    """Tài khoản của NSTM phụ trách TỪNG DÒNG (đại ca chốt 17/09: người nhận là NSTM
    trên dòng, không phải người đứng tên cả phiếu). Một NSTM ôm nhiều dòng thì vẫn
    chỉ một chuông — khử trùng ngay ở đây chứ không dựa vào bên nhận."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    codes = {(i.assignee or "").strip() for i in items if (i.assignee or "").strip()}
    if not codes:
        return []
    emp_ids = [e.id for e in db.query(Employee).filter(Employee.code.in_(codes)).all()]
    if not emp_ids:
        return []
    return [u.id for u in db.query(User)
            .filter(User.employee_id.in_(emp_ids), User.is_active == True).all()]


def notify_options_ready(db: Session, pr: PurchaseRequest, actor_id: int) -> None:
    """NSTM vừa chốt hoàn thành xử lý DÒNG CUỐI CÙNG -> báo người yêu cầu vào chọn.

    Chỉ gọi khi cả phiếu đã xong (`all_done`). Không tự báo cho chính người vừa bấm:
    quản lý thu mua chốt hộ phiếu của chính mình thì khỏi nhận chuông của mình.
    """
    if not OPTION_BELLS_ENABLED:
        return
    from app.modules.notification.service import trigger_notification

    uid = _requester_user_id(db, pr)
    if not uid or uid == actor_id:
        return
    trigger_notification(
        db=db, event="pr_options_ready", doc_type="purchase_request", doc_code=pr.code,
        creator_id=actor_id or pr.created_by, background_tasks=None,
        is_urgent=bool(pr.is_urgent), link=f"/purchase-requests/{pr.id}",
        recipient_ids=[uid])


def notify_options_chosen(db: Session, pr: PurchaseRequest, actor_id: int) -> None:
    """Người yêu cầu vừa CHỐT XONG LỰA CHỌN cả phiếu -> báo NSTM của từng dòng."""
    if not OPTION_BELLS_ENABLED:
        return
    from app.modules.notification.service import trigger_notification

    uids = [u for u in _line_assignee_user_ids(db, items_of(db, pr)) if u != actor_id]
    if not uids:
        return
    trigger_notification(
        db=db, event="pr_options_chosen", doc_type="purchase_request", doc_code=pr.code,
        creator_id=actor_id or pr.created_by, background_tasks=None,
        is_urgent=bool(pr.is_urgent), link=f"/purchase-requests/{pr.id}",
        recipient_ids=uids)


def generate_purchase_orders(db: Session, pr: PurchaseRequest, user_id: int) -> dict:
    """H.10.6 — "Tạo đơn mua hàng theo phương án": gom PHƯƠNG ÁN ĐANG CHỌN của từng
    dòng theo NCC -> mỗi NCC một đơn NHÁP; các dòng mà phương án chọn CHƯA có NCC
    gom thành MỘT đơn nháp không NCC (cổng CR-095 chỉ chặn lúc GỬI DUYỆT đơn,
    lập nháp không cần NCC — đơn đó là danh sách việc "đi tìm NCC" của thu mua).

    Nhân khuôn `survey_request.create_prs` nhưng KHÔNG tự dựng bản ghi: đi qua
    `purchase_order.create_po` để thừa kế trọn side-effect của đường lập đơn tay
    (sinh mã PO, NSPT mặc định theo NSTM của dòng, chép ngày dự kiến từ dòng YCMH,
    đồng bộ tiến độ dòng CR-074, nhật ký). `create_po` commit theo TỪNG đơn —
    cùng khuôn YCBG; payload tự dựng từ dữ liệu đã kiểm nên không có nhánh lỗi
    giữa chừng nào được trông đợi.

    Chống bấm hai lần KHÔNG bỏ chốt phương án (khác YCBG: bên đó option là công cụ
    của thu mua, bên này là QUYẾT ĐỊNH của người yêu cầu — bỏ chốt là xóa quyết
    định đó): dựa vào `line_status` — dòng đã nằm trên một ĐMH (kể cả Nháp, CR-074
    đổi trạng thái ngay lúc lập) thì bỏ qua, bấm lại chỉ tạo cho phần dòng còn lại.

    Giá dòng = `snap_price_by_volume`; VAT = `snap_vat`, trống rơi về `vat_pct`
    của dòng (CR-058). Cam kết giao hàng của phương án chép vào ghi chú dòng đơn.
    """
    from datetime import datetime

    from app.modules.purchase_order import service as po_service
    from app.modules.purchase_order.schema import POCreate, POItemIn
    from app.modules.purchase_request import service as pr_service
    from app.modules.supplier.model import Supplier

    items = items_of(db, pr)
    ensure_option_zero(db, pr, items)   # sinh bù cho phiếu điều phối trước tính năng
    chosen = chosen_map(db, [i.id for i in items])

    skipped = {"no_chosen": 0, "already_ordered": 0, "cancelled": 0}
    groups: dict[str, dict] = {}
    for i in items:
        if (i.line_status or "") == pr_service.LINE_STATUS_CANCELLED:
            skipped["cancelled"] += 1
            continue
        if (i.line_status or pr_service.LINE_STATUS_NO_PO) != pr_service.LINE_STATUS_NO_PO:
            skipped["already_ordered"] += 1
            continue
        opt = chosen.get(i.id)
        if not opt:
            # Người yêu cầu đã bỏ chốt hết phương án của dòng (kể cả phương án 0)
            # — đó là lời "khoan mua dòng này", tôn trọng.
            skipped["no_chosen"] += 1
            continue
        code = (opt.supplier_code or "").strip()
        name = (opt.supplier_name or "").strip()
        # NCC ngoài danh mục (chỉ có tên) là một nhóm riêng theo tên — không được
        # trộn vào nhóm "chưa có NCC" (key rỗng).
        key = code or (f"name:{name}" if name else "")
        group = groups.setdefault(key, {"code": code, "name": name, "rows": []})
        if not group["name"] and name:
            group["name"] = name
        group["rows"].append((i, opt))

    if not groups:
        raise HTTPException(400, "Không còn dòng nào tạo được đơn: các dòng hoặc chưa "
                                 "chốt phương án, hoặc đã nằm trên đơn mua hàng rồi.")

    today = datetime.now().strftime("%Y-%m-%d")
    created = []
    # Nhóm không NCC xếp CUỐI: đơn "đi tìm NCC" đứng sau các đơn đã đủ thông tin.
    for key in sorted(groups, key=lambda k: (k == "", k)):
        group = groups[key]
        sup = (db.query(Supplier).filter(Supplier.code == group["code"]).first()
               if group["code"] else None)
        sup_name = (sup.name if sup else "") or group["name"]
        note = f"Sinh tự động từ Yêu cầu mua hàng {pr.code} theo phương án đã chốt."
        if not group["code"] and not sup_name:
            note += " Chưa có nhà cung cấp — bổ sung trước khi gửi duyệt."
        po_items = []
        for i, opt in group["rows"]:
            # CR-058: VAT của phương án theo sang đơn; phương án không khai thì
            # rơi về VAT của dòng yêu cầu, đừng để 0% âm thầm.
            vat = float(opt.snap_vat or 0) or float(i.vat_pct or 0)
            note_parts = [p for p in [
                f"Cam kết giao: {(opt.snap_delivery_time or '').strip()}"
                if (opt.snap_delivery_time or "").strip() else "",
                f"Nơi giao: {(opt.snap_delivery_place or '').strip()}"
                if (opt.snap_delivery_place or "").strip() else "",
            ] if p]
            po_items.append(POItemIn(
                product_code=(i.product_code or "").strip(),
                product_name=i.product_name or "",
                item_group=i.item_group or "",
                unit=(opt.snap_quote_unit or i.unit or ""),
                qty_request=float(i.qty or 0),
                qty_order=float(i.qty or 0),
                price=float(opt.snap_price_by_volume or 0),
                vat=vat,
                required_date=i.required_date or "",
                expected_date=i.expected_date or "",
                note="; ".join(note_parts),
            ))
        po = po_service.create_po(db, POCreate(
            pr_code=pr.code,
            company_id=pr.company_id or 0,
            supplier_code=group["code"],
            supplier_name=sup_name,
            department=pr.department or "",
            department_id=pr.department_id or 0,
            order_date=today,
            vat_rate=float(pr.vat_rate or 0) or 0.08,
            is_urgent=bool(pr.is_urgent),
            note=note,
            items=po_items,
        ), user_id)
        created.append({"id": po.id, "code": po.code, "supplier_code": po.supplier_code,
                        "supplier_name": po.supplier_name, "line_count": len(po_items)})

    #  "options_gen_orders" chứ không phải "options_generate_orders": cột
    #  tab_audit_log.action là String(20), tên đầy đủ 23 ký tự làm MySQL nổ 1406
    #  ngay lúc bấm nút (SQLite của pytest không ép độ dài nên test không bắt được).
    record(db, user_id, ENTITY, pr.id, "options_gen_orders",
           f"Tạo {len(created)} đơn mua hàng nháp theo phương án: "
           + ", ".join(c["code"] for c in created))
    return {"orders": created, "skipped": skipped}
