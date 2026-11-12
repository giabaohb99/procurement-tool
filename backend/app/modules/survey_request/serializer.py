"""Dựng kết quả API của YCBG (bao-CR-711: dời nguyên từ `controller.py`, không đổi hành vi).

Ba bản dựng cho ba người đọc khác nhau, giữ đúng luật che NCC của từng bản:
  - `_out`         — màn chi tiết / danh sách (người yêu cầu, quản lý);
  - `_out_process` — màn *Xử lý khảo sát* của NSTM, ĐẦY ĐỦ cụm NCC;
  - `_out_result`  — kết quả cho người yêu cầu, chỉ trả trường trong danh sách trắng.
Truy vấn nằm ở `service.py`; thứ tự khóa trong từng dict giữ như bản cũ.
"""
from decimal import Decimal

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, user_has_permission
from app.core.central_purchasing import get_central_dept_id, is_central_dept, normalize_handler_dept_id
from app.core.scoping import holds_handling_dept

from . import line_state, service
from .model import SurveyRequest


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    base = _dict(s)
    # Trưởng bộ phận: phiếu lập lúc phòng chưa gán trưởng sẽ lưu rỗng và ở rỗng vĩnh viễn.
    # Rỗng thì lấy theo Department.manager_id hiện tại để HIỂN THỊ (không ghi đè dữ liệu đã lưu).
    if not base.get("head_of_dept") and (s.department_id or s.department):
        from app.modules.purchase_request.service import find_dept_head, find_dept_head_id
        base["head_of_dept"] = find_dept_head(db, s.department, s.department_id)
        base["head_of_dept_id"] = find_dept_head_id(db, s.department, s.department_id)   # CR-087
    # bao-CR-480: tên phòng xử lý đi kèm phiếu (cùng luật với YCMH); phòng ban có id mà thiếu
    # tên thì tra danh mục để hiển thị, không ghi đè.
    from app.modules.purchase_request.service import handler_dept_name_of
    base["handler_dept_name"] = handler_dept_name_of(db, s.handler_dept_id)
    # bao-CR-524: phiếu cũ còn `0` hiện đúng id phòng thu mua mặc định.
    base["handler_dept_id"] = normalize_handler_dept_id(db, s.handler_dept_id)
    # bao-CR-490: trưởng phòng phê duyệt (người thực bấm Duyệt) + trưởng phòng theo hồ sơ.
    from app.core.print_signers import approver_fields
    base.update(approver_fields(db, s))
    if not (base.get("department") or "").strip() and base.get("department_id"):
        base["department"] = handler_dept_name_of(db, base["department_id"])
    lines = service.lines_of(db, s.id)
    order = getattr(s, "_ordered_line_ids", None)   # sau create/update: giữ đúng thứ tự dòng đã gửi
    if order:
        pos = {lid: i for i, lid in enumerate(order)}
        lines = sorted(lines, key=lambda ln: pos.get(ln.id, 10 ** 9))
    if user is not None and profile is not None:   # NSTM chỉ thấy dòng mình phụ trách
        lines = service.visible_lines_for(db, s, lines, user, profile)
    name_by_code = service.employee_names_by_code(db, {ln.assignee for ln in lines if ln.assignee})
    out_lines = []
    for x in lines:
        d = _dict(x)
        d["assignee_name"] = name_by_code.get(x.assignee, "")
        opts = service.valid_options_of(db, x.id)
        d["option_count"] = len(opts)
        d["has_chosen"] = any(o.is_chosen for o in opts)
        # CR-077: nhãn tiến độ dòng do BACKEND suy, dùng chung với màn Tiến độ báo giá.
        # FE không tự tính lại — trước đây nó tự tính nên hai màn hiện hai chữ khác nhau.
        d["progress_state"] = line_state.progress_state(x, d["has_chosen"], d["option_count"])
        d["progress_tone"] = line_state.STATE_TONE.get(d["progress_state"], "gray")
        out_lines.append(d)
    base["lines"] = out_lines
    # bao-CR-414 GĐ5: nút "Chuyển phòng xử lý" / "Trả về thu mua" — chỉ quản lý thu mua của
    # phòng ĐANG CẦM phiếu (hoặc toàn hệ) và khi việc khảo sát chưa thật sự bắt đầu.
    can_transfer = False
    if user is not None:
        prof = profile if profile is not None else get_perm_profile(db, user)
        can_transfer = bool(service.can_transfer_dept(db, s)
                            and holds_handling_dept(prof, "survey_request", s, get_central_dept_id(db)))
    base["can_transfer_dept"] = can_transfer
    # bao-CR-524: "Trả về thu mua" chỉ khi phiếu đang ở phòng KHÁC phòng thu mua mặc định.
    base["can_return_dept"] = bool(can_transfer and not is_central_dept(db, s.handler_dept_id))
    # bao-CR-554: nút "Trả về" cho người yêu cầu — người có quyền duyệt, phiếu chờ duyệt hoặc đã
    # duyệt mà việc khảo sát chưa bắt đầu. Giao diện chỉ bày nút theo cờ này.
    #  bao-CR-753: ở bước chờ duyệt, phiếu đã chọn "Trưởng phòng phê duyệt" thì chỉ người đó quyết
    #  (kể cả quản trị). Giao diện ẩn Duyệt / Trả về / Từ chối theo cờ này.
    from app.core.designated_approver import is_designated_approver
    base["can_decide"] = bool(user is not None and (s.status != "submitted" or is_designated_approver(s, user, db)))
    base["can_return_requester"] = bool(user is not None and base["can_decide"]
                                        and service.can_return_requester(db, s)
                                        and user_has_permission(db, user, "survey_request", "approve"))
    return base


# ─────────────────── Phase 5B: màn xử lý NSTM (ẩn NCC ở tầng backend) ───────────────────

def _opt_internal(o) -> dict:
    return _dict(o)                      # đầy đủ, gồm supplier_* (NSTM/Admin xem được)


def _out_process(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    base = _dict(s)
    lines = service.lines_of(db, s.id)
    if user is not None and profile is not None:   # NSTM chỉ thấy dòng mình phụ trách
        lines = service.visible_lines_for(db, s, lines, user, profile)
    name_by_code = service.employee_names_by_code(db, {ln.assignee for ln in lines if ln.assignee})
    out_lines = []
    for ln in lines:
        d = _dict(ln)
        d["assignee_name"] = name_by_code.get(ln.assignee, "")
        d["options"] = [_opt_internal(o) for o in service.valid_options_of(db, ln.id)]
        # Cờ cho FE: dòng này người xem có được GẮN/XÓA phương án không. Admin TM (đọc-chỉ)
        # thấy hết dòng nhưng chỉ sửa được dòng mình phụ trách -> dòng khác hiển thị read-only.
        d["can_process"] = (service.can_process_line(db, ln, profile)
                            if profile is not None else True)
        out_lines.append(d)
    base["lines"] = out_lines
    return base


def _out_available_lines(db: Session, rows) -> list[dict]:
    """Dòng khảo sát SẢN PHẨM cho ô chọn NCC thủ công, kèm mã / phân loại phiếu khảo sát nguồn
    (đầu phiếu nạp một lần cho mỗi phiếu, cache theo `survey_id`)."""
    _sv_cache: dict = {}
    out = []
    for r in rows:
        d = _dict(r)
        d["supplier_name"] = service.resolve_supplier_name(db, r.supplier_code or "")
        if r.survey_id not in _sv_cache:
            _sv_cache[r.survey_id] = service.survey_header(db, r.survey_id)
        sv = _sv_cache[r.survey_id]
        d["survey_item_group"] = sv.item_group if sv else ""   # để FE cảnh báo khi khác phân loại dòng
        d["survey_code"] = sv.code if sv else ""
        d["survey_item_code"] = sv.item_code if sv else ""     # Mã VTBB/VL (lấy từ header phiếu khảo sát)
        # result_date (Ngày trả KQ của dòng NCC) đã có sẵn trong d -> FE dùng làm "Ngày khảo sát"
        out.append(d)
    return out


# ─────────────── Phase 5C: người YC xem kết quả (ẨN NCC) + chọn option ───────────────

# WHITELIST field an toàn trả cho người YC (KHÔNG có supplier_*, snap_internal_code,
# supplier_survey_id, product_survey_line_id → không lộ NCC).
# CR-147 (ticket #11): nstm_note ('Lý do NSPT') nay TRẢ cho người YC — khách yêu cầu
# hiện ghi chú lên thẻ phương án, chấp nhận rủi ro ghi chú có thể nhắc tên NCC.
_OPT_PUBLIC_FIELDS = [
    "id", "public_id", "display_label", "is_chosen",
    "system_product_code",   # Mã VTBB/VL hệ thống (mã vật tư của chính người YC — KHÔNG lộ NCC)
    "snap_product_name", "snap_spec", "snap_origin", "snap_quote_unit",
    "snap_moq", "snap_price_by_volume", "snap_volume_range", "snap_vat",
    "snap_delivery_time", "snap_delivery_place", "snap_shipping_cost",
    "snap_sample_ready", "snap_lab_result", "nstm_note",
]
_LINE_PUBLIC_FIELDS = [
    "id", "item_group", "requirement_detail", "other_requirement",
    "request_qty", "uom", "proposed_price", "is_completed", "line_status",
    "pr_id", "pr_code", "no_option",
]


def _opt_attachments(db: Session, psl_id: int) -> list[dict]:
    """Đính kèm của dòng khảo sát SP (entity 'survey_line') → hiện trên option.
    Chạy trong /result (đã kiểm quyền survey_request read) nên không gọi API riêng."""
    if not psl_id:
        return []
    return [{"file_id": f.id, "filename": f.filename, "url": f.url,
             "content_type": f.content_type, "size": f.size}
            for _lk, f in service.survey_line_files(db, psl_id)]


def _opt_public(o, db: Session) -> dict:
    d = _dict(o)
    out = {k: d.get(k) for k in _OPT_PUBLIC_FIELDS}
    out["attachments"] = _opt_attachments(db, o.product_survey_line_id)
    # Ngày khảo sát = Ngày trả KQ của dòng khảo sát NCC nguồn (không lộ NCC nào).
    # CR-147: survey_note = cột 'Ghi chú' của dòng khảo sát SP — đọc LIVE (không snapshot)
    # để phiếu cũ cũng hiện ngay, và NSTM sửa ghi chú trên khảo sát là bên YC thấy bản mới.
    out["survey_result_date"] = ""
    out["survey_note"] = ""
    if o.product_survey_line_id:
        psl = service.survey_product_line(db, o.product_survey_line_id)
        if psl:
            out["survey_result_date"] = psl.result_date or ""
            out["survey_note"] = psl.note or ""
    return out


def _out_result(db: Session, s: SurveyRequest, user=None, profile=None) -> dict:
    base = _dict(s)
    # Mã NCC ẩn danh: đánh số theo thứ tự xuất hiện, cùng NCC -> cùng số (KHÔNG lộ tên/mã thật).
    # Dùng chung toàn phiếu để so được "cùng 1 NCC" giữa các sản phẩm.
    ncc_seq: dict = {}

    def _ncc_ref(code: str) -> int:
        c = (code or "").strip()
        if not c:
            return 0
        if c not in ncc_seq:
            ncc_seq[c] = len(ncc_seq) + 1
        return ncc_seq[c]

    # YCMH đã tạo theo option (đếm nhiều lần) — trong phạm vi phiếu này
    links, pr_map = service.pr_links_of(db, s.id)
    ycmh_by_opt: dict = {}
    for link in links:
        pr = pr_map.get(link.pr_id)
        if pr is not None and pr.is_deleted:
            continue  # bao-CR-580: lưới đỡ — xóa YCMH đã gỡ dây nối, dữ liệu cũ thì dọn bằng script
        ycmh_by_opt.setdefault(link.option_id, []).append({
            "id": link.pr_id, "code": link.pr_code,
            "date": (pr.request_date if pr else ""), "status": (pr.status if pr else ""),
        })

    # Lọc dòng theo NGƯỜI XEM: NSTM chỉ thấy dòng mình phụ trách; người tạo/Admin/QL TM thấy hết.
    lines = service.lines_of(db, s.id)
    if user is not None and profile is not None:
        lines = service.visible_lines_for(db, s, lines, user, profile)
    out_lines = []
    for ln in lines:
        d = {k: getattr(ln, k) for k in _LINE_PUBLIC_FIELDS}
        d["request_qty"] = float(d["request_qty"] or 0)
        d["proposed_price"] = float(d["proposed_price"] or 0)
        opts = []
        for o in service.valid_options_of(db, ln.id):
            od = _opt_public(o, db)
            ref = _ncc_ref(o.supplier_code)
            od["ncc_ref"] = ref
            od["display_label"] = f"Option {o.public_id} — NCC #{ref}" if ref else f"Option {o.public_id}"
            od["ycmh_list"] = ycmh_by_opt.get(o.id, [])
            od["ycmh_count"] = len(od["ycmh_list"])
            opts.append(od)
        d["options"] = opts
        d["option_count"] = len(opts)
        d["has_chosen"] = any(o.get("is_chosen") for o in opts)
        d["progress_state"] = line_state.progress_state(ln, d["has_chosen"], d["option_count"])
        d["progress_tone"] = line_state.STATE_TONE.get(d["progress_state"], "gray")
        out_lines.append(d)
    base["lines"] = out_lines
    return base
