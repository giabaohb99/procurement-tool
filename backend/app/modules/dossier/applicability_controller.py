"""API «HỒ SƠ CẦN KÈM» — `/api/dossiers/applicable` (21/09/2026).

Trang chi tiết của một chứng từ hỏi: *«có tờ hồ sơ nào phải kèm theo tôi không?»*
Luật khớp nằm ở `applicability.py`; tệp này chỉ lo **gác cửa** và ghép câu trả lời.

⚠️ **Tách khỏi `controller.py` và phải nạp TRƯỚC nó ở `main.py`.** Bộ sinh CRUD
đăng ký `/api/dossiers/{id}` với `id: int`; FastAPI khớp đường dẫn theo thứ tự
đăng ký, nên nạp sau thì `/api/dossiers/applicable` rơi vào tuyến `{id}` và
trả **422** «không đổi được 'applicable' sang số» — một lỗi trông như lỗi máy
khách gửi sai, chứ không chỉ về phía thứ tự nạp tuyến.

⚠️ **HAI cửa, không phải một.** Có `dossier.read` mới là được đọc hồ sơ; còn
chứng từ nguồn thì phải qua `get_scoped` bằng **khóa quyền của chính nó**. Thiếu
cửa thứ hai thì bất kỳ ai có quyền đọc hồ sơ đều dò được nội dung đơn hàng của
phòng khác: câu lý do trả về nói thẳng *«vì dòng 3 có SP-001»*, tức là đọc ra
được cả mã sản phẩm lẫn số dòng của một tờ đơn họ không được xem.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, get_perm_profile, require, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped

from .applicability import (DOC_KINDS, doc_lines, matches_line, reason_of)
from .constants import (DOSSIER_ARCHIVED, DP_DONE, DP_STATUS_LABELS,
                        DP_STATUS_VALUES)
from .model import Dossier
from .progress_model import DossierProgress
from .progress_service import (merge as merge_progress, pending_depends,
                               progress_map, upsert)

router = APIRouter(prefix="/api/dossiers", tags=["dossier"])

#  Trần số hồ sơ trả về. Một chứng từ cần kèm ba bốn tờ giấy là cùng; con số này
#  chỉ để chặn ca khai nhầm (bật «áp cho mọi đơn mua hàng» trên cả trăm tờ hồ sơ)
#  biến một thẻ thông tin thành một trang cuộn không hết.
MAX_APPLICABLE = 20


def _doc_model(doc_kind: str):
    """Model của chứng từ nguồn. Nhập trong hàm — xem ghi chú ở `applicability.py`."""
    if doc_kind == "purchase_request":
        from app.modules.purchase_request.model import PurchaseRequest
        return PurchaseRequest
    if doc_kind == "purchase_order":
        from app.modules.purchase_order.model import PurchaseOrder
        return PurchaseOrder
    if doc_kind == "survey_request":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest
    from app.modules.survey.model import Survey
    return Survey


@router.get("/applicable")
def applicable_dossiers(
    doc_kind: str = Query(..., description="purchase_request | purchase_order | survey_request | survey"),
    doc_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user=Depends(require("dossier", "read")),
):
    """Các hồ sơ phải kèm theo chứng từ này, kèm câu lý do vì sao khớp."""
    if doc_kind not in DOC_KINDS:
        raise HTTPException(400, "Loại chứng từ không hợp lệ: " + ", ".join(DOC_KINDS))

    profile = get_perm_profile(db, user)

    #  CỬA THỨ HAI. 404 chứ không 403 — người ngoài phạm vi không cần biết tờ
    #  chứng từ đó có thật hay không (cùng lý lẽ đã ghi ở `get_scoped`).
    entity = DOC_KINDS[doc_kind]["entity"]
    if not get_scoped(db, _doc_model(doc_kind), entity, doc_id, user, profile):
        raise HTTPException(404, "Không tìm thấy chứng từ")

    lines = doc_lines(db, doc_kind, doc_id)
    matched = _match(db, doc_kind, doc_id, lines, user, profile)

    #  MỘT truy vấn cho cả thẻ. Tra trong vòng lặp thì mỗi tờ hồ sơ một lượt
    #  đọc DB — hai chục tờ là hai chục truy vấn cho một lần mở phiếu.
    progress = progress_map(db, doc_kind, doc_id)
    employee_names = _assignee_names(db, progress)

    #  Tập hồ sơ CÒN áp dụng cho phiếu, và tập đã xong — hai thứ cần để tính
    #  khóa tiên quyết. Tính một lần ở đây, không tính lại trong vòng lặp.
    alive = {d.id for d, _, _ in matched}
    done_ids = {
        did for did, row in progress.items() if merge_progress(row)["progress_done"]
    }
    names = {d.id: d.name for d, _, _ in matched}

    out = [
        _row(dossier, reason, hits, progress.get(dossier.id), employee_names,
             done_ids, alive, names)
        for dossier, reason, hits in matched
    ]

    return success({
        "items": out,
        "doc_kind": doc_kind,
        "doc_id": doc_id,
        "doc_kind_label": DOC_KINDS[doc_kind]["label"],
        #  Danh sách dòng hàng của chính chứng từ này — chế độ xem «Theo dòng
        #  hàng» dựng khung từ đây. Trả kèm thay vì bắt máy khách gọi thêm một
        #  lượt vào API của phân hệ Thu mua: hai lượt gọi là hai bản dữ liệu có
        #  thể lệch nhau trong cùng một màn hình, và bản lệch là bản người dùng
        #  nhìn.
        "lines": lines,
    })


def _match(db: Session, doc_kind: str, doc_id: int, lines: list, user, profile):
    """Các hồ sơ KHỚP một chứng từ: `[(Dossier, câu lý do, số dòng khớp)]`.

    Tách khỏi tuyến đọc vì đường GHI tiến độ cũng cần đúng tập này — nó phải
    biết tờ tiên quyết có áp dụng cho phiếu hay không. Hai bản chép rời sẽ lệch
    nhau đúng lúc ai đó đổi luật khớp, và cái lệch là một ràng buộc khóa vĩnh
    viễn mà màn hình không giải thích được.
    """
    #  ⚠️ Lọc `apply_doc_kinds` ngay dưới DB thì gọn hơn, nhưng cột là JSON và
    #  MySQL 8 với SQLite của bộ test tra JSON bằng hai cú pháp khác nhau — một
    #  bài kiểm xanh trên SQLite mà hỏng trên chạy thật là thứ tệ hơn cả không
    #  có bài kiểm. Lọc trong Python: phân hệ này cỡ trăm dòng, không phải chỗ
    #  cần tối ưu.
    #
    #  Hồ sơ ĐÃ LƯU TRỮ thì bỏ: nó là giấy hết vòng đời, nhắc người ta kèm theo
    #  một tờ đã cất kho là chỉ dẫn sai. Hồ sơ HẾT HẠN thì VẪN hiện — người
    #  duyệt cần biết tờ giấy đáng lẽ phải có đang quá hạn, đó chính là lúc
    #  thông tin này đáng giá nhất.
    query = db.query(Dossier).filter(Dossier.status != DOSSIER_ARCHIVED)
    candidates = apply_scope(query, Dossier, "dossier", user, profile).all()

    out = []
    for dossier in candidates:
        if doc_kind not in dossier.apply_doc_kind_list:
            continue
        conditions = dossier.apply_condition_list

        if not conditions:
            #  Không khai điều kiện = áp cho MỌI phiếu loại này, kể cả phiếu
            #  chưa có dòng hàng nào. `matched_lines` RỖNG nghĩa là «hồ sơ
            #  CHUNG», khác hẳn «không khớp dòng nào» — hồ sơ không khớp thì
            #  không lọt vào danh sách này ngay từ đầu.
            out.append((dossier, reason_of(conditions, {}, doc_kind), []))
        else:
            #  ⚠️ Gom MỌI dòng khớp, không dừng ở dòng đầu tiên. Dừng sớm thì rẻ
            #  hơn một chút nhưng chế độ xem «Theo dòng hàng» mất sạch dữ liệu:
            #  một tờ hồ sơ áp cho ba dòng sẽ chỉ hiện ở một dòng, và người dùng
            #  kết luận hai dòng kia không cần tờ giấy đó.
            hits = [line for line in lines if matches_line(conditions, line)]
            if hits:
                out.append((dossier, reason_of(conditions, hits[0], doc_kind),
                            [line["no"] for line in hits]))

        if len(out) >= MAX_APPLICABLE:
            break
    return out


def _assignee_names(db: Session, progress: dict) -> dict[int, str]:
    """Tên người thực hiện, tra MỘT lượt cho cả thẻ.

    ⚠️ Không đi qua `apply_scope` của phân hệ Nhân sự: đây chỉ là cái TÊN gắn
    trên một việc của chính tờ phiếu người dùng đang được phép xem, cùng hạng
    với `owner_name` mà bộ sinh CRUD vẫn trả. Bắt nó theo phạm vi nhân sự thì
    người thu mua nhìn việc mình vừa giao cho phòng khác thành một ô trống.
    """
    ids = {row.assignee_id for row in progress.values() if row.assignee_id}
    if not ids:
        return {}
    from app.modules.employee.model import Employee
    rows = db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()
    return {eid: name for eid, name in rows}


def _row(
    dossier: Dossier,
    reason: str,
    matched_lines: list[int],
    progress_row: DossierProgress | None,
    employee_names: dict[int, str],
    done_ids: set[int],
    alive: set[int],
    names: dict[int, str],
) -> dict:
    """Bộ trường vừa đủ cho một thẻ — KHÔNG trả `extra_fields`.

    Thẻ này hiện ở màn của phân hệ khác, nơi người xem có `dossier.read` nhưng
    không hẳn có việc gì với ruột tờ hồ sơ. Trả cả `extra_fields` là rải nội
    dung giấy tờ (số tài khoản, số hợp đồng) sang bốn màn chứng từ; ai cần đọc
    đủ thì bấm vào mở chính tờ hồ sơ, ở đó có đủ chốt quyền của phân hệ Hồ sơ.
    """
    return {
        "id": dossier.id,
        "code": dossier.code,
        "name": dossier.name,
        #  Trả cả KHÓA lẫn NHÃN loại. Nhãn để bày, khóa để **gom nhóm** — thẻ
        #  thử «Hồ sơ cần hoàn thành» xếp hồ sơ theo loại và lấy thứ tự từ
        #  `sort_order` của danh mục, mà gom theo chuỗi tên thì đổi tên loại một
        #  cái là nhóm vỡ làm đôi, im lặng.
        "dossier_type_id": dossier.dossier_type_id,
        "dossier_type_name": dossier.dossier_type_name,
        "status": dossier.status,
        "status_label": dossier.status_label,
        #  Ghi chú = cột MÔ TẢ trên dòng hồ sơ của thẻ. `note` là chuỗi tự do
        #  ngắn, không phải `extra_fields` — nội dung tờ giấy vẫn không rời khỏi
        #  phân hệ Hồ sơ, xem ghi chú ở đầu `_row`.
        "note": dossier.note,
        "expiry_date": dossier.expiry_date.isoformat() if dossier.expiry_date else None,
        "expiry_state": dossier.expiry_state,
        "expiry_state_label": dossier.expiry_state_label,
        "expiry_days": dossier.expiry_days,
        "reason": reason,
        #  Số thứ tự các dòng hàng mà tờ hồ sơ này khớp. **RỖNG = hồ sơ CHUNG**
        #  (áp cho cả phiếu), không phải «không khớp dòng nào».
        "matched_lines": matched_lines,
        #  ⚠️ TIẾN ĐỘ RIÊNG CỦA PHIẾU NÀY — đừng lẫn với `status` ở trên.
        #  `status` = tờ giấy có trong kho công ty chưa; `progress_status` = việc
        #  làm tờ giấy đó cho phiếu này tới đâu. Thẻ đo tiến độ bằng khóa thứ
        #  hai, xem `progress_model.py`.
        **_with_lock(merge_progress(progress_row), dossier.depend_list,
                    done_ids, alive, names),
        "assignee_name": employee_names.get(
            progress_row.assignee_id if progress_row else 0, ""
        ),
    }


def _with_lock(
    values: dict,
    depends: list[int],
    done_ids: set[int],
    alive: set[int],
    names: dict[int, str],
) -> dict:
    """Gắn `depends` + `waiting` + `locked` vào bộ trường tiến độ.

    ⚠️ **Ràng buộc đọc từ TỜ HỒ SƠ (`tab_dossier.depends`), trạng thái đọc từ
    TIẾN ĐỘ (`tab_dossier_progress.status`).** Đó là toàn bộ điểm tinh tế của
    tính năng: chuỗi tiên quyết khai một lần cho cả kho, còn «đang khóa hay
    chưa» thì mỗi phiếu một câu trả lời, vì «xong» là chuyện của từng phiếu.
    Khai ở đây (trong một tờ YCBG) thì mỗi phiếu phải khai lại cả chuỗi; tính
    khóa ở tờ hồ sơ thì mở khóa cho phiếu này là mở luôn cho mọi phiếu.

    ⚠️ Tính Ở BACKEND, không để giao diện tự suy: luật có lọc id CHẾT, và hai
    bản luật sẽ lệch nhau đúng ở ca đó. Trả kèm TÊN của tờ đang chờ chứ không
    chỉ id — màn hình cần câu «chờ: Hợp đồng mua bán», mà tra tên ở TS thì phải
    tự dựng lại map.
    """
    waiting = pending_depends(depends, done_ids, alive)
    return {
        **values,
        #  Lọc qua `alive`: tờ tiên quyết KHÔNG áp dụng cho phiếu này thì không
        #  bày ra — người đọc sẽ đi tìm một dòng không có trên thẻ.
        "depends": [i for i in depends if i in alive],
        "waiting": [{"id": i, "name": names.get(i, "")} for i in waiting],
        "locked": bool(waiting),
    }


class ProgressPayload(BaseModel):
    """Ô nào không gửi thì GIỮ NGUYÊN — đây là PATCH, không phải PUT.

    ⚠️ `None` và «không gửi» là hai chuyện khác nhau ở `planned_date`: không gửi
    = đừng đụng vào, gửi `null` = xóa ngày đi. Phân biệt bằng `exclude_unset`
    lúc đọc, đừng thay bằng `if payload.planned_date` — bỏ trống ngày sẽ không
    bao giờ lưu được.
    """

    status: int | None = None
    required: bool | None = None
    assignee_id: int | None = Field(default=None, ge=0)
    planned_date: date | None = None
    note: str | None = Field(default=None, max_length=1000)
    file_note: str | None = Field(default=None, max_length=500)


@router.patch("/applicable/{dossier_id}/progress")
def set_progress(
    dossier_id: int,
    payload: ProgressPayload,
    doc_kind: str = Query(...),
    doc_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    user=Depends(require("dossier", "read")),
):
    """Đặt tiến độ của MỘT tờ hồ sơ TRÊN MỘT chứng từ.

    ⚠️ **Quyền GHI đòi quyền ghi trên CHỨNG TỪ, không phải trên kho hồ sơ.** Đây
    là dữ liệu của tờ phiếu — ai sửa được phiếu thì tick được hồ sơ của phiếu
    đó. Bắt `dossier.write` thì hóa ra phải có quyền sửa danh mục hồ sơ toàn
    công ty mới đánh dấu xong được một việc trên đơn của chính mình; mà cấp
    `dossier.write` cho cả phòng thu mua thì họ sửa được kho giấy tờ của công ty.
    """
    if doc_kind not in DOC_KINDS:
        raise HTTPException(400, "Loại chứng từ không hợp lệ: " + ", ".join(DOC_KINDS))

    values = payload.model_dump(exclude_unset=True)
    if "status" in values and values["status"] not in DP_STATUS_VALUES:
        raise HTTPException(422, "Trạng thái không hợp lệ")

    profile = get_perm_profile(db, user)
    entity = DOC_KINDS[doc_kind]["entity"]

    #  CỬA 1 — đọc được chính tờ chứng từ. 404 chứ không 403, xem `applicable`.
    doc = get_scoped(db, _doc_model(doc_kind), entity, doc_id, user, profile)
    if not doc:
        raise HTTPException(404, "Không tìm thấy chứng từ")
    #  CỬA 2 — sửa được nó.
    if not user_has_permission(db, user, entity, "write"):
        raise HTTPException(403, "Không có quyền sửa chứng từ này")

    #  Tờ hồ sơ phải nằm trong phạm vi của người dùng — không thì gõ một id vào
    #  URL là gắn được tiến độ cho tờ giấy họ không được xem.
    if not get_scoped(db, Dossier, "dossier", dossier_id, user, profile):
        raise HTTPException(404, "Không tìm thấy hồ sơ")

    #  ⚠️ Cả hai chốt dưới đây cần TẬP HỒ SƠ ÁP DỤNG cho phiếu, nên phải chạy
    #  lại phép khớp. Đắt hơn một chút, nhưng đây là đường GHI (một lần mỗi cú
    #  bấm) chứ không phải đường đọc, và không có tập đó thì không phân biệt nổi
    #  «tiên quyết hợp lệ» với «một id gõ đại vào URL».
    lines = doc_lines(db, doc_kind, doc_id)
    matched = _match(db, doc_kind, doc_id, lines, user, profile)
    alive = {d.id for d, _, _ in matched}
    if dossier_id not in alive:
        raise HTTPException(404, "Hồ sơ không áp dụng cho chứng từ này")

    rows = progress_map(db, doc_kind, doc_id)

    #  ⚠️ **CHẶN Ở BACKEND, không chỉ khóa ô tick trên màn hình.** Giao diện
    #  gác là tiện cho người dùng; ai gọi thẳng API vẫn đánh dấu xong được một
    #  việc mà tiên quyết của nó chưa xong, và khi đó dải tiến độ nói dối.
    if values.get("status") == DP_DONE:
        #  Tiên quyết đọc từ TỜ HỒ SƠ, không đọc từ dòng tiến độ — xem `_with_lock`.
        to = next((d for d, _, _ in matched if d.id == dossier_id), None)
        depends = to.depend_list if to else []
        done_ids = {
            did for did, r in rows.items() if r.status == DP_DONE and did != dossier_id
        }
        cho = pending_depends(depends, done_ids, alive)
        if cho:
            ten = ", ".join(
                next((d.name for d, _, _ in matched if d.id == i), str(i)) for i in cho
            )
            raise HTTPException(400, f"Còn hồ sơ tiên quyết chưa hoàn thành: {ten}")

    row = upsert(db, doc_kind, doc_id, dossier_id, values)
    #  Ghi nhật ký vào CHỨNG TỪ, không vào tờ hồ sơ: người đi tìm «ai tick cái
    #  này» mở tờ phiếu ra xem, chứ không mở kho hồ sơ.
    #
    #  ⚠️ Tham số thứ hai là `user_id`, KHÔNG phải object `user`. Truyền nhầm
    #  object thì SQLAlchemy nhét nguyên nó vào cột `created_by` và MySQL trả
    #  500 «Incorrect integer value» — một lỗi chỉ nổ lúc chạy thật, vì SQLite
    #  của bộ test không ép kiểu cột.
    record(db, user.id, entity, doc_id, "update",
           f"Tiến độ hồ sơ #{dossier_id}: {DP_STATUS_LABELS.get(row.status, '')}")
    #  `record` tự commit (xem ghi chú BM-013 ở `core/audit.py`), nhưng gọi lại
    #  cho rõ ý: dòng tiến độ vừa flush phải được chốt kể cả khi mai này nhật ký
    #  đổi nhịp commit.
    db.commit()
    return success(merge_progress(row), "Đã cập nhật tiến độ")
