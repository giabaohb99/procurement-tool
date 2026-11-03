"""Dựng kết quả API của YCMH (bao-CR-711: dời nguyên từ `controller.py`, không đổi hành vi).

Thứ tự khóa trong từng dict giữ ĐÚNG như bản cũ — bản in và hai giao diện đọc theo khóa,
nhưng xuất Excel / bài kiểm chụp kết quả thì so cả thứ tự. Truy vấn nằm ở `service.py`;
cờ quyền (`can_*`) hỏi `access.py`, cùng chốt mà route dùng.
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
from app.core.central_purchasing import get_central_dept_id, is_central_dept, normalize_handler_dept_id
from app.core.scoping import holds_handling_dept
from app.core.status_codes import PR_LINE_STATUS

from . import option_service, service
from .access import _can_dispatch, _can_return_requester, _in_approve_scope
from .constants import PR_OPTION_SOURCE_LABELS
from .model import STATUS_AFTER_APPROVE, STATUS_AFTER_DISPATCH

HEADER_COLS = ["id", "code", "company_id", "requester", "requester_id", "requester_position",
               "department_id", "handler_dept_id", "department", "head_of_dept", "head_of_dept_id",
               # bao-CR-316: `received_date` CHỈ có ở đây (đọc ra), cố ý KHÔNG nằm trong
               # PRCreate/PRUpdate — Ngày tiếp nhận do `dispatch_pr` điền, không ai sửa tay.
               "purpose", "request_date", "received_date", "need_date",
               "status", "is_urgent", "vat_rate", "assignee_id", "note",
               "show_code_on_print", "suggested_supplier", "suggested_supplier_tax_code",
               "suggested_supplier_contact", "quote_filename", "quote_file_url"]


_SUPPLIER_FIELDS = ("suggested_supplier", "suggested_supplier_tax_code", "suggested_supplier_contact")


def _blank_supplier(d: dict) -> None:
    """Task 5: che NCC đề xuất khi user không có quyền supplier.read."""
    for k in _SUPPLIER_FIELDS:
        d[k] = ""


def _out_option(db: Session, o, can_sup_read: bool) -> dict:
    """Một phương án ra API (bao-CR-310).

    Cụm NCC (`supplier_*`, `snap_internal_code`, `supplier_survey_id`) chỉ trả cho người
    có `supplier.read` — đúng luật cụm `pur` của Task 4. Phần thông số + GIÁ thì người
    yêu cầu ĐƯỢC thấy, giống hệt thẻ phương án bên Yêu cầu báo giá: họ cần so giá để
    chốt, chỉ không được biết giá đó của ai.
    """
    d = {
        "id": o.id, "pr_item_id": o.pr_item_id,
        "source": int(o.source or 0),
        "source_label": PR_OPTION_SOURCE_LABELS.get(int(o.source or 0), ""),
        "product_survey_line_id": o.product_survey_line_id,
        "public_id": o.public_id, "display_label": o.display_label,
        "is_chosen": bool(o.is_chosen),
        "snap_product_name": o.snap_product_name, "snap_spec": o.snap_spec,
        "snap_origin": o.snap_origin, "snap_quote_unit": o.snap_quote_unit,
        "snap_moq": float(o.snap_moq or 0),
        "snap_price_by_volume": float(o.snap_price_by_volume or 0),
        "snap_volume_range": o.snap_volume_range,
        "snap_vat": float(o.snap_vat or 0),
        "snap_delivery_time": o.snap_delivery_time,
        "snap_delivery_place": o.snap_delivery_place,
        "snap_shipping_cost": float(o.snap_shipping_cost or 0),
        "snap_sample_ready": bool(o.snap_sample_ready),
        "snap_lab_result": o.snap_lab_result,
        "nstm_note": o.nstm_note,
        "created_at": o.created_at,
    }
    if can_sup_read:
        d.update({"supplier_code": o.supplier_code, "supplier_name": o.supplier_name,
                  "supplier_survey_id": o.supplier_survey_id,
                  "snap_internal_code": o.snap_internal_code})
    else:
        d.update({"supplier_code": "", "supplier_name": "", "supplier_survey_id": 0,
                  "snap_internal_code": ""})
    return d


# Chữ ký 2 bước duyệt trên phiếu in chỉ có hiệu lực từ mốc trạng thái tương ứng trở đi.
# Phiếu bị TRẢ VỀ (Nháp / Chờ duyệt) sẽ KHÔNG in lại chữ ký duyệt của lần trước.
_AFTER_APPROVE = STATUS_AFTER_APPROVE
_AFTER_DISPATCH = STATUS_AFTER_DISPATCH


def _approval_signers(db: Session, pr) -> dict:
    """Người ký 2 bước duyệt của phiếu — tra từ nhật ký thao tác (audit log).

    Bước 1 `approved`  (trưởng phòng duyệt)  -> ô "TP/BP đề xuất" trên phiếu in.
    Bước 2 `dispatched` (thu mua điều phối)  -> `dispatcher_*` (người bấm nút, giữ cho
    tương thích) và `purchasing_head_*` = TRƯỞNG PHÒNG của người đó (bao-CR-397) -> ô
    "TP/BP mua hàng". Phòng chưa gán trưởng thì `purchasing_head_*` lùi về người điều phối.
    Công tắc `pr_dispatch_enabled` TẮT: từ bao-CR-485 sổ chỉ còn MỘT dòng `approved` (không
    còn dòng `dispatched` dưới tên người duyệt), nên ở đây lùi: người điều phối = người duyệt
    → ô "TP/BP mua hàng" ra trưởng phòng của NGƯỜI DUYỆT — chấp nhận như trước, vì luồng đó
    không có thu mua nào chạm vào phiếu. Phiếu cũ (trước CR-485) vẫn có dòng `dispatched` nên
    đi đường thường.

    bao-CR-531: kèm hai id NHÂN SỰ để `print_signature_cells` gộp ô "Giám đốc":
    `proposer_employee_id` = người của ô "TP/BP đề xuất" — cột `approver_employee_id` (người được
    chọn / người thực duyệt, có cả khi phiếu CHƯA duyệt: tên để trống nhưng bộ ô đã biết), phiếu cũ
    cột rỗng thì nhân sự của tài khoản bấm Duyệt trong nhật ký; `purchasing_head_employee_id` =
    người đang in ở ô "TP/BP mua hàng" (trưởng phòng, hoặc người điều phối khi lùi). 0 = chưa biết.
    """
    from app.core.audit import resolve_actor, resolve_signature
    from app.core.print_signers import employee_id_of_user

    out = {"approver_name": "", "approver_signature": "",
           "dispatcher_name": "", "dispatcher_signature": "",
           "purchasing_head_name": "", "purchasing_head_signature": "",
           "proposer_employee_id": 0, "purchasing_head_employee_id": 0}
    #  bao-CR-499: cột "Trưởng phòng phê duyệt" giữ người ĐƯỢC CHỌN khi chưa duyệt, người THỰC duyệt
    #  sau khi duyệt.
    #  bao-CR-521 (ticket prod #57, 28/09/2026): phiếu CHƯA duyệt thì ô "TP/BP đề xuất" để TRỐNG
    #  HẲN — cả tên lẫn chữ ký. Bản 504 còn in tên người được chọn, người đọc hiểu là trưởng phòng
    #  đã ký. Người được chọn vẫn hiện ở màn chi tiết (ô "Trưởng phòng phê duyệt").
    from app.core.print_signers import person_block
    stored_id = int(getattr(pr, "approver_employee_id", 0) or 0)
    stored = person_block(db, stored_id)
    if stored["name"]:
        out["proposer_employee_id"] = stored_id
    if stored["name"] and pr.status in _AFTER_APPROVE:
        out["approver_name"] = stored["name"]
        out["approver_signature"] = stored["signature"]
    want = ([("approved", "approver")] if pr.status in _AFTER_APPROVE else []) + \
           ([("dispatched", "dispatcher")] if pr.status in _AFTER_DISPATCH else [])
    if not want:
        return out
    actions = [a for a, _ in want]
    rows = service.audit_actors_of(db, pr.id, actions)
    latest: dict[str, int] = {}
    for action, uid in rows:
        latest.setdefault(action, uid)        # dòng đầu = lần duyệt GẦN NHẤT
    if ("dispatched" in actions and "dispatched" not in latest and latest.get("approved")
            and not service.dispatch_enabled()):
        latest["dispatched"] = latest["approved"]     # bao-CR-485, xem docstring
    for action, key in want:
        uid = latest.get(action)
        if uid:
            out[f"{key}_name"] = resolve_actor(db, uid)
            out[f"{key}_signature"] = resolve_signature(db, uid)
    if stored["name"]:      # cột thắng nhật ký (bao-CR-490/499)
        out["approver_name"], out["approver_signature"] = stored["name"], stored["signature"]
    elif out["approver_name"] and latest.get("approved"):
        out["proposer_employee_id"] = employee_id_of_user(db, latest["approved"])
    dispatcher_uid = latest.get("dispatched")
    if dispatcher_uid:
        head_name, head_sign, head_id = service.purchasing_head(db, dispatcher_uid)
        out["purchasing_head_name"] = head_name or out["dispatcher_name"]
        out["purchasing_head_signature"] = head_sign if head_name else out["dispatcher_signature"]
        if out["purchasing_head_name"]:
            out["purchasing_head_employee_id"] = head_id if head_name else employee_id_of_user(db, dispatcher_uid)
    return out


def _out(db: Session, pr, user=None) -> dict:
    from app.core.audit import (resolve_actor, resolve_signature,
                                resolve_signature_by_employee)
    d = {c: getattr(pr, c) for c in HEADER_COLS}
    d["vat_rate"] = float(pr.vat_rate or 0)
    # Trưởng bộ phận: phiếu lập lúc phòng chưa gán trưởng sẽ lưu rỗng và ở rỗng vĩnh viễn.
    # Rỗng thì lấy theo Department.manager_id hiện tại để HIỂN THỊ (không ghi đè dữ liệu đã lưu).
    if not d.get("head_of_dept") and (pr.department_id or pr.department):
        d["head_of_dept"] = service.find_dept_head(db, pr.department, pr.department_id)
    # bao-CR-480: ô Phòng ban rỗng thì HIỂN THỊ cho ra tên — có id phòng mà thiếu tên (phiếu
    # dựng bằng script) thì tra danh mục; không có cả id (lập trước bao-CR-465) thì theo hồ sơ
    # nhân sự của người yêu cầu. Không ghi đè dữ liệu: lưu / gửi duyệt mới ghi.
    if not (d.get("department") or "").strip():
        if d.get("department_id"):
            d["department"] = service.handler_dept_name_of(db, d["department_id"])
        else:
            d["department_id"], d["department"] = service.resolve_employee_department(db, pr.requester_id)
    # bao-CR-480: tên phòng xử lý đi kèm phiếu — màn hình không cần quyền đọc danh mục phòng
    # ban mới hiện được tên (trước đây người thiếu quyền chỉ thấy "Phòng #5").
    d["handler_dept_name"] = service.handler_dept_name_of(db, pr.handler_dept_id)
    # bao-CR-524: phiếu cũ còn `0` hiện đúng id phòng thu mua mặc định — ô chọn không còn mục
    # "Thu mua chung" mang số 0 để khớp.
    d["handler_dept_id"] = normalize_handler_dept_id(db, pr.handler_dept_id)
    # bao-CR-490: trưởng phòng phê duyệt (người thực bấm Duyệt) + trưởng phòng theo hồ sơ.
    from app.core.print_signers import approver_fields
    d.update(approver_fields(db, pr))
    # Task 4: NCC 2 cụm. Cụm 'req' (bộ phận đề xuất) MỌI người xem/sửa được — sửa bug người
    # yêu cầu không nhập nổi NCC của chính mình. Cụm 'pur' (khảo sát/thu mua) cần supplier.read
    # để xem, supplier.write để sửa.
    can_sup_read = user is None or user_has_permission(db, user, "supplier", "read")
    cl = service.clusters_of(pr)
    d["supplier_req"] = cl["req"]
    d["supplier_pur"] = cl["pur"] if can_sup_read else service._empty_cluster()
    d["supplier_from_survey"] = cl["from_survey"]
    d["can_edit_supplier_pur"] = user is not None and user_has_permission(db, user, "supplier", "write")
    # CR-034: nút duyệt lần 2 (điều phối) — quyền tính ở server (phạm vi grant không có ở map
    # quyền phía FE). Công tắc tắt thì không ai thấy nút, vì phiếu không dừng ở 'approved' nữa.
    d["dispatch_enabled"] = service.dispatch_enabled()
    # bao-CR-468: công tắc cụm phương án. Đi kèm phiếu chứ không phải một đường API riêng —
    # người dùng thường KHÔNG có quyền `setting.read`, mà hai chỗ phải ẩn (nút Xử lý phương án,
    # thẻ Chọn phương án) đều đã cầm sẵn dữ liệu phiếu này.
    d["options_enabled"] = option_service.options_enabled()
    d["can_dispatch"] = bool(user is not None and pr.status == "approved" and d["dispatch_enabled"]
                             and _can_dispatch(get_perm_profile(db, user)))
    # bao-CR-414 GĐ5: nút "Chuyển phòng xử lý" / "Trả về phòng lập" — chỉ quản lý thu mua của
    # phòng ĐANG CẦM phiếu (hoặc toàn hệ) và khi việc mua chưa thật sự bắt đầu.
    d["can_transfer_dept"] = bool(user is not None and service.can_transfer_dept(db, pr)
                                  and holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr,
                                                          get_central_dept_id(db)))
    # bao-CR-524: "Trả về thu mua" chỉ có nghĩa khi phiếu đang ở phòng KHÁC phòng thu mua mặc định.
    d["can_return_dept"] = bool(d["can_transfer_dept"] and not is_central_dept(db, pr.handler_dept_id))
    # Duyệt bước 1: cũng phải tính ở server vì có quyền `approve` chưa chắc đúng PHẠM VI —
    # Admin thu mua (phạm vi 'proc') có approve để duyệt điều phối nhưng không duyệt bước 1.
    # CR-071: ô TBP (`head_of_dept_id`) CHỈ để lưu + in, KHÔNG khóa quyền duyệt — chọn ai
    # thì ai có quyền trong phạm vi vẫn duyệt được như trước.
    d["can_approve"] = bool(user is not None and pr.status == "submitted"
                            and user_has_permission(db, user, "purchase_request", "approve")
                            and _in_approve_scope(db, user, pr.id))
    # bao-CR-554: nút "Trả về" cho người yêu cầu — server tính vì phải hỏi cả phạm vi lẫn dòng ĐMH.
    d["can_return"] = bool(user is not None and _can_return_requester(db, user, pr))
    # NCC "hiệu lực" ở cột cũ (suggested_supplier*) — che nếu không có supplier.read (giữ Task 5).
    if not can_sup_read:
        _blank_supplier(d)
    d["created_at"] = pr.created_at
    d["created_by_name"] = resolve_actor(db, pr.created_by)
    # bao-CR-419: mốc người yêu cầu chốt xong lựa chọn phương án (None = vòng này chưa xong).
    d["options_chosen_at"] = pr.options_chosen_at
    d["options_chosen_by_name"] = resolve_actor(db, pr.options_chosen_by) if pr.options_chosen_by else ""
    # bao-CR-317: ô "Báo giá đính kèm" trên bản in — xem `service.has_quote_file`.
    d["has_quote_file"] = service.has_quote_file(db, pr)
    # bao-CR-318 + bao-CR-422: đường quay về YCBG nguồn — xem `service.linked_survey_requests`.
    # Danh sách rỗng = phiếu lập tay. Hai khóa vô hướng bên dưới là phiếu nguồn ĐẦU TIÊN, giữ
    # nguyên tên cũ vì giao diện cũ (`frontend/`) và bản in đang đọc thẳng chúng — thêm khóa
    # mới thì bên đó không phải sửa gì.
    srs = service.linked_survey_requests(db, pr)
    d["survey_requests"] = srs
    d["survey_request_id"] = srs[0]["id"] if srs else 0
    d["survey_request_code"] = srs[0]["code"] if srs else ""
    # Chữ ký ô "Người lập" trên phiếu in. Tra theo NHÂN SỰ người yêu cầu (đúng cái TÊN đang in);
    # phiếu cũ chưa có requester_id thì mới lấy chữ ký người tạo, và chỉ khi tên trùng nhau —
    # tránh in chữ ký người A dưới tên người B khi thu mua lập phiếu hộ bộ phận khác.
    d["requester_signature"] = resolve_signature_by_employee(db, pr.requester_id)
    if (not d["requester_signature"] and not pr.requester_id
            and (d["created_by_name"] or "").strip() == (pr.requester or "").strip()):
        d["requester_signature"] = resolve_signature(db, pr.created_by)
    # Chữ ký + họ tên 2 ô duyệt trên phiếu in (TP/BP đề xuất · TP/BP mua hàng)
    d.update(_approval_signers(db, pr))

    # Fetch company name safely to avoid permission issues on the frontend
    d["company_name"] = ""
    comp = None
    if pr.company_id:
        comp = service.company_of(db, pr.company_id)
        if comp:
            d["company_name"] = comp.name
    # bao-CR-531: bộ ô ký cụm "XÉT DUYỆT" đã rút gọn (hộ kinh doanh · gộp ô Giám đốc) — hai giao
    # diện chỉ vẽ lại. Các khóa cũ (approver_name…) giữ nguyên cho giao diện chưa cập nhật.
    from .print_signature_cells import build_print_signature_cells
    d["print_signature_cells"] = build_print_signature_cells(
        comp, d, pr.requester or "", d["requester_signature"])

    items = service.items_of(db, pr.id)
    # Batch resolve ảnh gốc theo product_code (2 query/phiếu, tránh N+1).
    prod_by_code, thumb_by_pid = service.product_thumbnails(
        db, {i.product_code for i in items if i.product_code})
    # H.10.1 — SINH BÙ phương án 0 cho phiếu điều phối từ trước khi có tính năng
    # (idempotent; phiếu ngoài giai đoạn mở thì hàm tự bỏ qua). Đặt TRƯỚC hai truy
    # vấn tóm tắt để option_count/chosen_option của lần đọc này đã thấy nó.
    option_service.ensure_option_zero(db, pr, items)
    # bao-CR-310: tóm tắt phương án cho từng dòng — 2 truy vấn cho cả phiếu, không N+1.
    item_ids = [i.id for i in items]
    opt_counts = option_service.count_map(db, item_ids)
    chosen_by_item = option_service.chosen_map(db, item_ids)
    #  bao-CR-601: tên NSTM phụ trách trả sẵn theo dòng. Trước đây hai bản giao diện tự tra
    #  tên từ danh sách nhân sự tải về — danh sách đó lọc theo PHẠM VI người xem, nên ai bị
    #  giới hạn pháp nhân (mà 259 hồ sơ nhân sự đang để pháp nhân 0) chỉ thấy mã "NSU012".
    assignee_names = service.employee_names_by_code(db, {i.assignee for i in items if i.assignee})
    d["items"] = []
    for i in items:
        pid_ = prod_by_code.get(i.product_code or "")
        chosen = chosen_by_item.get(i.id)
        d["items"].append(
            {"id": i.id, "product_code": i.product_code, "product_name": i.product_name,
             "item_group": i.item_group, "group_desc": i.group_desc, "qty": float(i.qty or 0),
             "unit": i.unit, "price": float(i.price or 0), "vat_pct": float(i.vat_pct or 0),
             "amount": float(i.amount or 0),
             "warehouse": i.warehouse, "required_date": i.required_date, "assignee": i.assignee,
             "assignee_name": assignee_names.get(i.assignee or "", ""),
             "expected_date": i.expected_date,
             "line_status": i.line_status,
             # B-06: cột lưu MÃ, giao diện dùng mã để tô màu/lọc nên phải trả kèm nhãn
             "line_status_label": PR_LINE_STATUS.label_of(i.line_status),
             "progress_note": i.progress_note, "note": i.note,
             "qty_ordered": float(i.qty_ordered or 0), "qty_received": float(i.qty_received or 0),
             "product_id": pid_ or 0,                          # 0 = code không khớp catalog
             "product_thumbnail_url": thumb_by_pid.get(pid_, "") if pid_ else "",
             # bao-CR-310 — "đã chốt phương án chưa" SUY từ bảng phương án, dòng YCMH
             # không có cột nào lưu việc đó (một nguồn sự thật).
             "option_count": opt_counts.get(i.id, 0),
             "chosen_option": _out_option(db, chosen, can_sup_read) if chosen else None,
             # Đợt 3b — cờ "NSTM đã chốt hoàn thành xử lý" + chốt rỗng của dòng
             "options_done": bool(i.options_done), "no_option": bool(i.no_option)}
        )
    # Task 4: PYC tính VAT lại theo dòng — tiền hàng (chưa VAT) · VAT · tổng cộng (gồm VAT)
    subtotal = round(sum(x["qty"] * x["price"] for x in d["items"]), 2)   # chưa VAT
    total = round(sum(x["amount"] for x in d["items"]), 2)                # gồm VAT
    d["subtotal"] = subtotal
    d["vat"] = round(total - subtotal, 2)
    d["total"] = total
    return d


def _out_list(db: Session, items: list, user) -> list[dict]:
    """Các dòng của màn danh sách YCMH — tổng tiền / ngày cần / cờ dòng hủy gom cả trang
    một lượt (`service.list_line_summaries`), không N+1."""
    subtotals, need_dates, cancelled_ids = service.list_line_summaries(db, [p.id for p in items])
    can_see_supplier = user_has_permission(db, user, "supplier", "read")   # Task 5
    out_items = []
    for p in items:
        d = {c: getattr(p, c) for c in HEADER_COLS}
        d["created_at"] = p.created_at   # thời điểm tạo (có giờ) — hiển thị giờ VN ở list
        d["updated_at"] = p.updated_at   # bao-CR-294 — cột "Ngày cập nhật" + sort ở màn danh sách
        d["need_date"] = need_dates.get(p.id) or p.need_date or ""
        d["total"] = round(subtotals.get(p.id, 0.0), 2)   # gồm VAT (tính từ amount dòng)
        d["has_cancelled_line"] = p.id in cancelled_ids
        if not can_see_supplier:
            _blank_supplier(d)   # ẩn NCC đề xuất
        out_items.append(d)
    return out_items


def _out_survey_lines(db: Session, rows) -> list[dict]:
    """Kho phương án: các dòng khảo sát SẢN PHẨM kèm mã / phân loại phiếu khảo sát nguồn.
    Đầu phiếu khảo sát nạp một lần cho mỗi phiếu (cache theo `survey_id`)."""
    from app.modules.survey_request import service as sr_service

    sv_cache: dict = {}
    out = []
    for r in rows:
        sv = sv_cache.get(r.survey_id)
        if r.survey_id not in sv_cache:
            sv = sv_cache[r.survey_id] = sr_service.survey_header(db, r.survey_id)
        out.append({
            "id": r.id, "supplier_code": r.supplier_code,
            "supplier_name": sr_service.resolve_supplier_name(db, r.supplier_code or ""),
            "internal_code": r.internal_code, "product_name": r.product_name,
            "spec": r.spec, "origin": r.origin, "quote_unit": r.quote_unit,
            "moq": float(r.moq or 0), "price_by_volume": float(r.price_by_volume or 0),
            "volume_range": r.volume_range, "vat": float(r.vat or 0),
            "delivery_time": r.delivery_time, "delivery_place": r.delivery_place,
            "shipping_cost": float(r.shipping_cost or 0), "lab_result": r.lab_result,
            "result_date": r.result_date,
            "survey_code": sv.code if sv else "",
            "survey_item_code": sv.item_code if sv else "",
            "survey_item_group": sv.item_group if sv else "",   # để FE cảnh báo lệch phân loại
        })
    return out
