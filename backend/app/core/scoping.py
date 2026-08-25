"""Lọc dữ liệu theo phạm vi — Lớp B (mô hình GRANT).

Mỗi vai trò của user là 1 grant: có quyền hành động + phạm vi riêng
(cấp bậc own/dept/company/all theo vai trò + chọn cụ thể công ty/phòng ban/nhân sự + loại trừ).
`apply_scope` = HỢP (OR) điều kiện của mọi grant có quyền `action` trên entity.

**B-07 — thiếu khai là CHẶN, không phải bỏ qua.** Trước đợt này `_role_scope_cond` trả `None`
cho entity vắng mặt trong `SCOPE_FIELDS`, mà `None` nghĩa là *thấy tất*. Mới khai 12/39 entity
nên 27 entity còn lại im lặng không lọc gì. Nay `SCOPE_FIELDS` phải khai **đủ mọi entity** — loại
nào cố ý không lọc thì khai thẳng là `PUBLIC`, kèm lý do — và entity lạ thì trả `false()`.
`test/backend/test_pham_vi_khai_du_b07.py` chốt con số ENTITIES == SCOPE_FIELDS, nên thêm entity mới vào
`core/permissions.ENTITIES` mà quên khai ở đây là **test đỏ**, không phải lỗ hổng lặng lẽ.
"""
import logging

from sqlalchemy import and_, false, or_, select

from app.core.auth import get_perm_profile  # noqa: F401  (re-export tiện dùng)

log = logging.getLogger("app.scoping")


class _Public(dict):
    """Nhãn 'entity này CỐ Ý không lọc phạm vi' — khác hẳn với 'quên khai'.

    Kế thừa `dict` rỗng để mọi chỗ đang gọi `f.get("company")` chạy nguyên như cũ;
    phần phân biệt nằm ở `entity in SCOPE_FIELDS` chứ không ở giá trị.
    """


PUBLIC = _Public()

# Entity → tên cột theo từng chiều. Thiếu chiều nào = không lọc theo chiều đó.
#
# CR-086 — chiều phòng ban: `dept_id` là NGUỒN SỰ THẬT. `dept_name` chỉ còn là ĐƯỜNG LÙI cho
# phiếu cũ chưa điền lùi được id (`department_id = 0`), xem `_dept_match`. Entity nào khai cả
# hai thì bỏ `dept_name` đi là xong phần lùi — làm cùng lúc với việc xóa cột text (N-008).
SCOPE_FIELDS = {
    "purchase_request": {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "owner": "created_by"},
    "survey_request":   {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "owner": "created_by"},
    "purchase_order":   {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "owner": "created_by"},
    "payable":          {"company": "company_id", "owner": "created_by"},
    # Hợp đồng: neo theo PHÁP NHÂN ĐỨNG TÊN (`company_id`). Trước đây entity này không có
    # trong bảng nên `_role_scope_cond` trả None — ai có `contract.read` là đọc hợp đồng của
    # MỌI công ty, kể cả khi phạm vi vai trò đặt là `company`/`own`. KHÔNG có chiều phòng ban:
    # hợp đồng thuộc pháp nhân chứ không thuộc phòng nào.
    "contract":         {"company": "company_id", "owner": "created_by"},
    "payment_request":  {"company": "company_id", "owner": "created_by"},
    "inventory":        {"company": "company_id"},
    "survey":           {"owner": "created_by"},
    "employee":         {"company": "company_id", "dept_id": "department_id", "self": "id"},
    "ticket":           {"company": "company_id", "owner": "created_by"},
    # Sổ văn bản: chỉ lọc theo pháp nhân sở hữu sổ. KHÔNG có chiều phòng ban —
    # quyền xem sổ cấp cho người đích danh qua tab_document_book_member.
    "document_book":    {"company": "company_id", "owner": "created_by"},
    # Văn bản: lọc theo pháp nhân BAN HÀNH + phòng chủ trì. `owner` là tài khoản
    # người tạo, không phải `owner_employee_id` (người chịu trách nhiệm nội dung)
    # — hai thứ khác nhau, người tạo hộ vẫn phải thấy phiếu mình vừa nhập.
    "document":         {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},

    # ------------------------------------------------------------------ B-07
    # Từ đây xuống là 27 entity trước kia KHÔNG có mặt trong bảng này. Vắng mặt
    # không phải "không cần lọc" — nó là *thấy tất*, vì `_role_scope_cond` trả
    # `None`. Nay mỗi entity phải nằm ở đúng một trong hai nhóm dưới.

    # --- Nhóm 1: CÓ chiều thật, nay lọc thật ---
    # Pháp nhân: chiều của chính nó là `id`, không phải `company_id`.
    "company":          {"company": "id"},
    # Phòng ban: neo theo pháp nhân chủ quản. CẨN THẬN — `tab_department_company`
    # cho phép một phòng phục vụ nhiều pháp nhân, nên `company_id` ở đây chỉ là
    # pháp nhân CHÍNH. Ai cần "thấy phòng của mọi pháp nhân mình phục vụ" thì
    # dùng phần chọn đích danh (`_dept_include_cond`), đừng nới lỏng dòng này.
    "department":       {"company": "company_id", "owner": "created_by"},
    # Tài khoản: `tab_user` KHÔNG có `company_id` — chiều pháp nhân nằm ở nhân sự
    # gắn kèm. Chỉ khai `self` để `own` nghĩa là "tài khoản của chính tôi";
    # `dept`/`company` sẽ rơi xuống chặn, đúng ý: người xem hẹp không duyệt danh
    # sách tài khoản toàn hệ.
    "user":             {"self": "employee_id"},
    "approval_flow":    {"company": "company_id", "owner": "created_by"},
    "goods_receipt":    {"company": "company_id", "owner": "created_by"},
    "seal_request":     {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},
    "vehicle_booking":  {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},

    # --- Nhóm 2: CỐ Ý công khai (xem `PUBLIC`) ---
    # 2a. Dữ liệu gốc dùng chung MỌI pháp nhân. Sản phẩm và nhà cung cấp là chỗ
    # các phân hệ nối vào nhau bằng CHUỖI `product_code` / mã NCC (xem
    # `mo-hinh-du-lieu-san-pham.md`). Lọc chúng theo pháp nhân là cắt đứt chính
    # mối nối đó: đơn của công ty A trỏ vào mã sản phẩm do công ty B nhập.
    # Muốn giấu NCC thì tắt bằng QUYỀN `supplier.read`, không phải bằng phạm vi.
    "product":          PUBLIC,
    "supplier":         PUBLIC,
    # 2b. Danh mục KHÔNG có chiều pháp nhân trong bảng. Đây là khoảng trống của
    # mô hình dữ liệu chứ không phải của tệp này — ngày nào thêm `company_id`
    # vào bảng nào thì đổi luôn dòng tương ứng ở đây.
    "warehouse":        PUBLIC,
    "unit":             PUBLIC,
    "item_group":       PUBLIC,
    "brand":            PUBLIC,
    "doc_type":         PUBLIC,
    "security_level":   PUBLIC,
    "external_party":   PUBLIC,
    "seal_type":        PUBLIC,
    "vehicle":          PUBLIC,
    "driver":           PUBLIC,
    "help_article":     PUBLIC,
    "category_assignee": PUBLIC,
    "role":             PUBLIC,
    "setting":          PUBLIC,
    # 2c. Quyền HÀNH ĐỘNG, không có bảng nào để lọc. `report`/`backup` là ô tick
    # trong ma trận phân quyền; `payment`/`import` thì đến model cũng không có
    # (không một chỗ nào gọi `require("payment", ...)`) — khai ra đây để bài
    # kiểm ENTITIES == SCOPE_FIELDS khỏi phải chừa ngoại lệ, và để ai xóa chúng khỏi `ENTITIES`
    # thì thấy luôn là xóa được.
    "report":           PUBLIC,
    "backup":           PUBLIC,
    "import":           PUBLIC,
    "payment":          PUBLIC,
    # `assistant` là cổng require() thuần (chỉ ban lãnh đạo), không có bảng nào
    # để lọc theo dòng — dữ liệu bot đọc đã đi qua apply_scope của từng tool.
    "assistant":        PUBLIC,
}


def _dept_match(model, f, dept_ids, dept_names):
    """Điều kiện "phiếu thuộc một trong các phòng này" — CR-086.

    Khớp bằng ID. Chỉ những phiếu KHÔNG điền lùi được id (`department_id = 0`, phòng đã đổi
    tên hoặc dữ liệu nhập tay) mới rơi về so tên, nên tên không bao giờ đè lên id. Xóa nhánh
    tên khi bỏ cột text (N-008). None = không có gì để so.
    """
    col_id, col_name = f.get("dept_id"), f.get("dept_name")
    cs = []
    if col_id and dept_ids:
        cs.append(getattr(model, col_id).in_(list(dept_ids)))
    if col_name and dept_names:
        legacy = getattr(model, col_name).in_(list(dept_names))
        cs.append(and_(getattr(model, col_id) == 0, legacy) if col_id else legacy)
    if not cs:
        return None
    return or_(*cs) if len(cs) > 1 else cs[0]


def _emp_match(model, col_id: str, col_name: str, emp_id: int, emp_name: str):
    """Điều kiện "ô nhân sự này là mình" — CR-087, cùng khuôn với `_dept_match`.

    `tab_employee.full_name` KHÔNG duy nhất nên khớp bằng tên là cho người trùng tên thấy
    việc của nhau. Khớp bằng id; chỉ dòng chưa điền lùi được (`<col_id> = 0`) mới rơi về so
    tên. Xóa nhánh tên khi bỏ cột chuỗi (N-008). None = không có gì để so.
    """
    cs = []
    if emp_id:
        cs.append(getattr(model, col_id) == emp_id)
    if emp_name:
        cs.append(and_(getattr(model, col_id) == 0, getattr(model, col_name) == emp_name))
    if not cs:
        return None
    return or_(*cs) if len(cs) > 1 else cs[0]


def _proc_status_cond(model, f, company_id: int, statuses: list[str]):
    """Nhánh "nhặt việc" của bậc `proc`: phiếu ở các trạng thái đã duyệt — P1-1 (kế hoạch 12).

    AND thêm pháp nhân của người xem để thu mua công ty con không nhặt được phiếu công ty
    khác. `company_id = 0` (nhân sự chưa gắn pháp nhân — dữ liệu prod hiện tại) thì KHÔNG
    thu hẹp, giữ đúng hành vi cũ để Thu mua không gián đoạn; gắn công ty rồi thì tự lọc.
    Entity không khai chiều `company` cũng không thu hẹp — nhưng cả hai chỗ đang gọi
    (`purchase_request`, `purchase_order`) đều có cột này.
    """
    status_cond = getattr(model, "status").in_(statuses)
    if company_id and f.get("company"):
        return and_(status_cond, getattr(model, f["company"]) == company_id)
    return status_cond


def _chan(entity, scope, user, ly_do):
    """Phạm vi hẹp nhưng không dựng nổi điều kiện → CHẶN, và nói ra vì sao — B-07.

    Trước đợt này mọi nhánh kiểu này đều lặng lẽ `return None`, mà `None` là *thấy tất*:
    phạm vi đặt hẹp bao nhiêu cũng vô nghĩa và không có một dòng log nào để biết. Dòng
    WARNING dưới đây chính là thứ để đi gom danh sách người bị ảnh hưởng — đừng bỏ nó khi
    dọn log, và khi thấy nó nổi lên thì việc phải làm gần như luôn là **sửa dữ liệu**
    (gắn pháp nhân/phòng ban cho nhân sự), không phải nới lại điều kiện ở đây.
    """
    log.warning("scope chan: entity=%s scope=%s user=%s — %s",
                entity, scope, getattr(user, "id", None), ly_do)
    return false()


def _role_scope_cond(model, entity, scope, user, profile):
    """Điều kiện theo cấp bậc vai trò (own/dept/company/all). None = 'all' (không giới hạn)."""
    if scope == "all":
        return None
    # B-07: KHÔNG khai = CHẶN. Trước đây nhánh này trả `None` nên 27 entity vắng mặt trong
    # `SCOPE_FIELDS` được xem thoải mái bất kể phạm vi vai trò. Entity cố ý không lọc thì
    # phải khai thẳng là `PUBLIC` ở trên; rơi vào đây nghĩa là ai đó vừa thêm entity mới
    # vào `core/permissions.ENTITIES` mà quên khai (bài kiểm ENTITIES == SCOPE_FIELDS sẽ đỏ).
    if entity not in SCOPE_FIELDS:
        log.error("scope thieu khai: entity=%s chua co trong SCOPE_FIELDS — dang chan het", entity)
        return false()
    f = SCOPE_FIELDS[entity]
    if isinstance(f, _Public):
        return None
    company_id = profile.get("company_id") or 0
    dept_name = profile.get("dept_name") or ""
    dept_id = profile.get("dept_id") or 0

    # "Được giao": của mình HOẶC được phân bổ cho mình (áp cho PYC)
    if scope in ("assigned", "proc"):
        if entity == "purchase_request":
            from app.modules.purchase_request.model import PurchaseRequestItem
            conds = [model.created_by == user.id]
            if profile.get("employee_id"):
                conds.append(model.requester_id == profile["employee_id"])   # phiếu mình là người yêu cầu
            # "proc" (NV/Admin thu mua): thấy thêm MỌI phiếu đã duyệt để nhặt việc + phân bổ.
            # CR-034: gồm cả 'approved' (TP duyệt xong, ĐANG CHỜ ĐIỀU PHỐI) — thiếu trạng thái này
            # thì chính người phải điều phối lại không nhìn thấy phiếu.
            # P1-1 (kế hoạch 12): nhánh này TRƯỚC ĐÂY không kèm lọc pháp nhân, nên bật đa pháp
            # nhân là thu mua công ty con nhặt được phiếu đã duyệt của MỌI công ty. AND thêm
            # công ty của người xem — nhưng CHỈ khi họ đã gắn `company_id`. Nhân sự chưa gắn
            # (dữ liệu prod hiện tại, company_id=0) giữ nguyên hành vi cũ để Thu mua không gián
            # đoạn; gắn company_id (bước bật đa pháp nhân) thì tự lọc đúng công ty.
            if scope == "proc":
                conds.append(_proc_status_cond(model, f, company_id,
                                                ["approved", "dispatched"]))
            if profile.get("employee_id"):
                conds.append(model.assignee_id == profile["employee_id"])
            if profile.get("emp_code"):
                sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == profile["emp_code"])
                conds.append(model.id.in_(sub))
            return or_(*conds)
        if entity == "survey_request":
            from app.modules.survey_request.model import SurveyRequestLine
            conds = [model.created_by == user.id]   # phiếu MÌNH tạo → thấy mọi trạng thái
            # "Việc thu mua của tôi" CHỈ áp cho phiếu ĐÃ DUYỆT (bỏ nháp/chờ duyệt/từ chối).
            # NSTM chỉ thấy phiếu khi CÓ DÒNG gán mã mình — việc khảo sát nằm ở DÒNG.
            # (Bỏ điều kiện theo `assignee_id` đầu phiếu: trường đó chỉ ghi 1 lần lúc duyệt và
            #  không đồng bộ khi đổi NSTM dòng → người cũ vẫn thấy phiếu không còn phần việc nào.)
            emp_id = profile.get("employee_id") or 0
            if emp_id:
                conds.append(model.requester_id == emp_id)   # phiếu mình là người yêu cầu → thấy mọi trạng thái
            if profile.get("emp_code"):
                code_sub = (select(SurveyRequestLine.survey_request_id)
                            .where(SurveyRequestLine.assignee == profile["emp_code"]))
                conds.append(and_(model.status.notin_(["draft", "submitted", "rejected"]),
                                  model.id.in_(code_sub)))
            return or_(*conds)
        if entity == "purchase_order":
            # ĐMH: thấy đơn MÌNH tạo HOẶC đơn có NSPT phụ trách = mình.
            # CR-087: khớp bằng `nspt_id`; tên chỉ còn là đường lùi cho đơn cũ (`nspt_id = 0`).
            conds = [model.created_by == user.id]
            if scope == "proc":
                conds.append(_proc_status_cond(model, f, company_id, ["approved"]))
            ec = _emp_match(model, "nspt_id", "nspt",
                            profile.get("employee_id") or 0, profile.get("emp_name") or "")
            if ec is not None:
                conds.append(ec)
            return or_(*conds)
        scope = "own"   # entity khác chưa có phân bổ → coi như của mình

    if scope == "own":
        if f.get("owner"):
            cond = getattr(model, f["owner"]) == user.id
            # Người YÊU CẦU cũng thấy phiếu của mình dù người khác (admin) tạo giùm
            rid = profile.get("employee_id") or 0
            if rid and hasattr(model, "requester_id"):
                cond = or_(cond, model.requester_id == rid)
            return cond
        if f.get("self"):   # entity không có owner (vd. employee) → chỉ chính mình
            return getattr(model, f["self"]) == (profile.get("employee_id") or 0)
        scope = "company"

    if scope == "dept":
        cs = []
        if f.get("company") and company_id:
            cs.append(getattr(model, f["company"]) == company_id)
        if f.get("dept_id") or f.get("dept_name"):
            dc = _dept_match(model, f, [dept_id] if dept_id else [],
                             [dept_name] if dept_name else [])
            # Người dùng chưa gắn phòng nào → không có gì để so → không thấy gì. (Luật cũ so
            # `department == ""` nên cũng gần như không ra phiếu nào; ở đây nói thẳng ra.)
            cs.append(dc if dc is not None else false())
        elif f.get("owner"):
            cs.append(getattr(model, f["owner"]) == user.id)
        if not cs:
            return _chan(entity, scope, user, "entity khong co chieu phong ban lan chu so huu")
        return and_(*cs)

    if scope == "company":
        if not f.get("company"):
            # Entity không có cột pháp nhân (vd. `survey`, `user`). Không có gì để lọc mà vẫn
            # trả None thì "company" hóa ra rộng bằng "all" — đúng lỗ N-14.
            return _chan(entity, scope, user, "entity khong co cot phap nhan")
        if not company_id:
            # NGƯỜI DÙNG CHƯA GẮN PHÁP NHÂN. Cùng luật với nhánh `dept` ở trên (chưa gắn
            # phòng → không thấy gì): thiếu dữ liệu thì chặn, chứ mở toang là nguy hiểm hơn.
            # ⚠️ Trước khi đưa lên môi trường thật phải gắn `company_id` cho nhân sự — xem
            # phần B-07 trong `doc/erp/15-do-be-tong-nen-v2.md`, đã đếm sẵn số người dính.
            return _chan(entity, scope, user, "nguoi dung chua gan phap nhan (company_id=0)")
        return getattr(model, f["company"]) == company_id

    return _chan(entity, scope, user, "pham vi la khong hieu duoc")


def _explicit_cond(model, entity, scopeconf):
    """Điều kiện THU HẸP: include công ty/nhân sự + MỌI loại trừ (AND).
    Riêng 'Phòng ban được xem' (department include) = CỘNG THÊM → xử lý ở apply_scope."""
    f = SCOPE_FIELDS.get(entity) or {}
    cs = []
    for dim, col in (("company", f.get("company")), ("employee", f.get("owner"))):
        if not col:
            continue
        column = getattr(model, col)
        inc = (scopeconf.get("inc") or {}).get(dim) or []
        exc = (scopeconf.get("exc") or {}).get(dim) or []
        if inc:
            cs.append(column.in_([int(v) for v in inc]))
        if exc:
            cs.append(~column.in_([int(v) for v in exc]))
    # Phòng ban: include là CỘNG THÊM (xem `_dept_include_cond`), ở đây chỉ còn loại trừ.
    dc = _dept_match(model, f, (scopeconf.get("exc") or {}).get("department") or [],
                     (scopeconf.get("exc") or {}).get("department_name") or [])
    if dc is not None:
        cs.append(~dc)
    return and_(*cs) if cs else None


def _dept_include_cond(model, entity, scopeconf):
    """'Phòng ban được xem' → điều kiện CỘNG THÊM (OR với phạm vi vai trò). None = không chọn phòng nào.

    `department` = danh sách ID, `department_name` = tên tương ứng (chỉ để lùi cho phiếu cũ).
    Hai khóa này do `core/auth.py` dựng sẵn khi đọc `tab_user_scope`.
    """
    inc = (scopeconf.get("inc") or {})
    return _dept_match(model, SCOPE_FIELDS.get(entity) or {},
                       inc.get("department") or [], inc.get("department_name") or [])


def scope_condition(model, entity: str, user, profile: dict, action: str = "read"):
    """ĐIỀU KIỆN phạm vi (chưa gắn vào query nào) = HỢP các grant có `action`.

    Ba giá trị trả về, phân biệt rõ:
      * `None` — thấy TẤT CẢ, không lọc gì;
      * `false()` — không grant nào cấp quyền này, không thấy gì;
      * điều kiện — phạm vi thật.

    Tách khỏi `apply_scope` để chỗ nào cần **OR thêm** một nguồn quyền khác còn
    ghép được. Chỗ đang cần: văn bản được chia sẻ đích danh cho một người — văn
    bản đó nằm NGOÀI phạm vi vai trò của họ, mà `apply_scope` thì chỉ biết thu
    hẹp, không biết mở thêm.
    """
    conds = []
    for g in profile.get("grants", []):
        p = g["perms"].get(entity)
        if not p or not p.get(action):
            continue
        scopeconf = g.get("scope") or {}
        rc = _role_scope_cond(model, entity, p.get("scope", "all"), user, profile)
        # 'Phòng ban được xem' = CỘNG THÊM vào phạm vi vai trò.
        # rc None (scope=all) → đã thấy hết, bỏ qua để không thu hẹp nhầm.
        dept_add = _dept_include_cond(model, entity, scopeconf)
        base = or_(rc, dept_add) if (rc is not None and dept_add is not None) else rc
        ec = _explicit_cond(model, entity, scopeconf)   # thu hẹp: company include + mọi loại trừ
        parts = [c for c in (base, ec) if c is not None]
        if not parts:
            return None           # grant này thấy tất cả → không lọc
        conds.append(and_(*parts))
    if not conds:
        return false()            # không grant nào cấp quyền này → không thấy gì
    return or_(*conds)


def apply_scope(query, model, entity: str, user, profile: dict, action: str = "read"):
    """Lọc query theo HỢP các grant có quyền `action` trên entity."""
    cond = scope_condition(model, entity, user, profile, action)
    return query if cond is None else query.filter(cond)


def get_scoped(db, model, entity: str, oid: int, user, profile: dict, action: str = "read"):
    """Lấy MỘT bản ghi, chỉ khi nó nằm trong phạm vi — trả `None` nếu không.

    Sinh ra cho các endpoint lấy/sửa/xóa một dòng: `db.get(Model, oid)` đi thẳng vào khóa
    chính nên bỏ qua sạch phần lọc phạm vi — danh sách giấu đúng, nhưng gõ thẳng id vào URL
    là ra. Nơi gọi cứ trả **404 "Không tìm thấy"** như với id không tồn tại: người ngoài
    phạm vi không cần biết bản ghi đó có thật hay không, và cũng không phải thêm mã lỗi mới.
    """
    cond = scope_condition(model, entity, user, profile, action)
    if cond is None:
        return db.get(model, oid)
    return db.query(model).filter(model.id == oid, cond).first()
