"""YCMH — tạo, sửa, sao chép, xóa phiếu; lưu dòng; cụm NCC; cờ gấp; chốt trước khi gửi duyệt (bao-CR-715 tách từ
service.py).
"""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import normalize_handler_dept_id
from app.core.utils import assert_unique_product_codes
from app.modules.catalog import lead_time
from app.modules.department.service import sync_department_ref

from .model import PurchaseRequest, PurchaseRequestItem
from .schema import PRCreate, PRUpdate
from .base_service import ENTITY, LINE_STATUS_CANCELLED, LINE_STATUS_NO_PO, get_pr, items_of, sla_base_date
from .department_service import (default_handler_dept_id, fill_department_from_employee, find_dept_head_id,
                                 sync_head_of_dept_name)


# Task 4 — NCC 2 cụm (req = bộ phận đề xuất · pur = khảo sát/thu mua) lưu JSON ở cột supplier_info.
_AUTO_NOTE_PREFIX = "Sinh tự động từ Yêu cầu báo giá"   # dấu hiệu phiếu tạo từ YCKS (fallback dữ liệu cũ)


def _empty_cluster() -> dict:
    return {"name": "", "tax_code": "", "contact": ""}


def _norm_cluster(c) -> dict:
    """Chuẩn hóa 1 cụm về đúng 3 khóa string (chống dữ liệu JSON lỗi)."""
    c = c if isinstance(c, dict) else {}
    return {"name": (c.get("name") or ""), "tax_code": (c.get("tax_code") or ""),
            "contact": (c.get("contact") or "")}


def clusters_of(pr) -> dict:
    """Trả về {req, pur, from_survey}. Ưu tiên supplier_info JSON; nếu trống thì suy từ dữ liệu cũ:
    phiếu sinh từ YCKS -> cụm 'pur', còn lại -> cụm 'req' (giữ nguyên cột suggested_supplier*)."""
    raw = (getattr(pr, "supplier_info", "") or "").strip()
    if raw:
        try:
            d = json.loads(raw)
            if isinstance(d, dict):
                return {"req": _norm_cluster(d.get("req")), "pur": _norm_cluster(d.get("pur")),
                        "from_survey": bool(d.get("from_survey"))}
        except Exception:
            pass
    # Dữ liệu cũ (trước Task 4): cột suggested_supplier* xưa CHỈ phía thu mua/nhập liệu điền được
    # (người yêu cầu bị khóa ở Task 5) -> luôn đưa vào cụm 'pur', KHÔNG cho bộ phận yêu cầu thấy.
    legacy = {"name": getattr(pr, "suggested_supplier", "") or "",
              "tax_code": getattr(pr, "suggested_supplier_tax_code", "") or "",
              "contact": getattr(pr, "suggested_supplier_contact", "") or ""}
    from_survey = (getattr(pr, "note", "") or "").startswith(_AUTO_NOTE_PREFIX)
    return {"req": _empty_cluster(), "pur": legacy, "from_survey": from_survey}


def apply_supplier_info(pr, clusters: dict) -> None:
    """Ghi supplier_info (JSON) + đồng bộ 'NCC hiệu lực' xuống cột suggested_supplier* cũ
    (ĐMH/list/mẫu in cũ vẫn dùng). Hiệu lực = cụm pur nếu có tên, ngược lại cụm req."""
    req = _norm_cluster(clusters.get("req"))
    pur = _norm_cluster(clusters.get("pur"))
    fs = bool(clusters.get("from_survey"))
    pr.supplier_info = json.dumps({"req": req, "pur": pur, "from_survey": fs}, ensure_ascii=False)
    eff = pur if pur["name"] else req
    pr.suggested_supplier = eff["name"]
    pr.suggested_supplier_tax_code = eff["tax_code"]
    pr.suggested_supplier_contact = eff["contact"]


def build_clusters(prev: dict, data, can_write_pur: bool, from_survey=None) -> dict:
    """Ghép cụm NCC khi lưu: cụm req ai sửa cũng được; cụm pur chỉ khi có quyền supplier.write.
    Cụm không được gửi/không đủ quyền -> giữ nguyên giá trị cũ (prev)."""
    req = _norm_cluster(prev.get("req"))
    pur = _norm_cluster(prev.get("pur"))
    fs = bool(prev.get("from_survey")) if from_survey is None else bool(from_survey)
    if getattr(data, "supplier_req", None) is not None:
        req = _norm_cluster(data.supplier_req.model_dump())
    if getattr(data, "supplier_pur", None) is not None and can_write_pur:
        pur = _norm_cluster(data.supplier_pur.model_dump())
    return {"req": req, "pur": pur, "from_survey": fs}


def ensure_submit_ready(db: Session, pr: PurchaseRequest, user_id: int) -> None:
    """Rà lại Phòng ban + Trưởng bộ phận NGAY TRƯỚC khi gửi duyệt — bao-CR-466.

    Luật nghiệp vụ đại ca chốt 23/09/2026: **gửi duyệt được thì phải có phòng ban và có
    người duyệt**. Thiếu một trong hai thì phiếu gửi đi cũng nằm chết — phạm vi `dept`
    lọc theo `department_id` nên phiếu rỗng phòng ban không lọt vào tầm mắt trưởng phòng
    nào, và chuông lẫn thư đều định tuyến theo cùng cột đó. Trước CR này không chỗ nào
    chặn: người lập bấm Gửi duyệt, nhận câu "Đã gửi duyệt", rồi chờ một người sẽ không
    bao giờ thấy phiếu.

    HAI NHỊP, ĐÚNG THỨ TỰ — chữa trước, chặn sau:

    1. **Chữa.** Ô rỗng thì tra lại từ đầu: phòng ban lùi về hồ sơ nhân sự, trưởng bộ
       phận tra lại theo phòng. Đây là nhịp quan trọng nhất của CR, vì ca thường gặp
       nhất là phiếu lập lúc tài khoản CHƯA gắn phòng, quản trị gắn phòng sau, mà phiếu
       thì vẫn giữ ô rỗng từ lúc ra đời. Chặn mà không chữa thì người lập bị khóa cứng
       trong một phiếu họ không sửa được (ô Phòng ban là ô chỉ xem).
    2. **Chặn.** Chữa xong vẫn rỗng mới báo lỗi, và câu lỗi phải chỉ ra việc cần làm —
       "thiếu phòng ban" là triệu chứng, thứ người đọc cần là "đi gắn phòng cho tài
       khoản rồi bấm lại".

    Phần đã chữa được thì GHI XUỐNG trước khi ném lỗi: chữa được phòng ban nhưng phòng
    chưa có trưởng thì lần bấm sau không phải dò lại từ đầu, và người đi sửa dữ liệu
    nhìn vào phiếu thấy đúng trạng thái hiện thời.

    ⚠️ Chốt này CHỈ gác cửa GỬI DUYỆT, không đụng tới luật DUYỆT. `head_of_dept_id` vẫn
    thuần túy là người đứng tên trên bản in (CR-071): ai có quyền `approve` và phiếu nằm
    trong phạm vi của họ thì vẫn bấm Duyệt được, kể cả khi không phải người đứng tên đó.
    Đừng biến điều kiện ở đây thành điều kiện duyệt.

    Đo trên dữ liệu thật trước khi chặn (23/09/2026): 17/17 phòng đang hoạt động đều đã
    gán trưởng và không phòng nào có trưởng đã nghỉ; trong 150 phiếu từng đi qua gửi
    duyệt chỉ 2 phiếu thiếu trưởng bộ phận, cả hai từ 03/08 trước khi có nhịp tự điền.
    Nghĩa là luật này không khóa ai đang làm việc bình thường.
    """
    # Nhịp 1 — chữa phòng ban. `fill_department_from_employee` tự bỏ qua phiếu đã có phòng.
    fill_department_from_employee(db, pr, user_id)
    sync_department_ref(db, pr)
    # Nhịp 2 — chữa trưởng bộ phận theo phòng vừa chốt (phòng có thể VỪA được gán trưởng).
    if not pr.head_of_dept_id:
        pr.head_of_dept_id = find_dept_head_id(db, pr.department, pr.department_id)
    sync_head_of_dept_name(db, pr)
    db.commit()

    if not pr.department_id:
        if (pr.department or "").strip():
            raise HTTPException(400,
                                f"Không gửi duyệt được: phòng ban \"{pr.department}\" trên phiếu "
                                "không khớp phòng ban nào đang có trong hệ thống (có thể phòng "
                                "đã đổi tên hoặc đã ngừng hoạt động). Nhờ quản trị kiểm tra lại "
                                "danh mục Phòng ban.")
        raise HTTPException(400,
                            "Không gửi duyệt được: phiếu chưa có Phòng ban. Phòng ban quyết định "
                            "ai nhìn thấy và duyệt phiếu, nên phiếu thiếu ô này gửi đi cũng không "
                            "ai duyệt được. Nhờ quản trị gắn phòng ban cho hồ sơ nhân sự của "
                            "người yêu cầu, rồi bấm Gửi duyệt lại — hệ thống sẽ tự điền.")
    if not pr.head_of_dept_id:
        raise HTTPException(400,
                            f"Không gửi duyệt được: phòng \"{pr.department}\" chưa gán Trưởng bộ "
                            "phận nên phiếu không có người đứng tên duyệt. Nhờ quản trị gán "
                            "Trưởng bộ phận trong danh mục Phòng ban, rồi bấm Gửi duyệt lại.")


def urgent_reasons(std: dict, base: str, lines) -> list[str]:
    """CR-082 — các dòng có NGÀY CẦN HÀNG sớm hơn NGÀY QUY ĐỊNH của phân loại.

    Luật chốt với khách: thiếu ĐÚNG MỘT ngày cũng là gấp (cần trong 14 ngày mà phân loại quy
    định 15 ngày -> gấp), nên phép so là `<` chứ không có ngưỡng dung sai. Ngày lưu dạng
    'YYYY-MM-DD' nên so chuỗi là so đúng thứ tự thời gian.

    Bỏ qua: dòng chưa nhập ngày cần hàng, dòng đã Hủy đơn, và cả phiếu chưa có Ngày tiếp nhận
    (không có mốc gốc thì không suy ra được ngày QĐ).
    """
    if not (base or "").strip():
        return []
    out: list[str] = []
    for it in lines or []:
        want = (getattr(it, "required_date", "") or "").strip()
        if not want or (getattr(it, "line_status", "") or "") == LINE_STATUS_CANCELLED:
            continue
        group = getattr(it, "item_group", "") or ""
        due = lead_time.regulated_date(std, group, base)
        if due and want < due:
            out.append(f'"{getattr(it, "product_name", "") or getattr(it, "product_code", "")}" '
                       f'cần {want} < ngày QĐ {due} '
                       f'(phân loại "{group or "chưa chọn"}": {lead_time.std_days_of(std, group)} ngày)')
    return out


def apply_auto_urgent(db: Session, pr: PurchaseRequest, user_id: int, std: dict | None = None) -> bool:
    """Tự BẬT cờ Đơn gấp khi có ≥1 dòng cần hàng sớm hơn thời gian quy định của phân loại.

    Chỉ bật, KHÔNG bao giờ tự tắt: cờ do người dùng bật tay (hoặc bật ở phiếu cũ) phải giữ
    nguyên, còn muốn bỏ gấp thì sửa ngày cần hàng rồi tắt tay bằng nút Đơn gấp.
    Phiếu đã hủy thì không đụng tới. Trả về True nếu vừa bật.
    """
    if pr is None or pr.is_urgent or pr.status == "cancelled":
        return False
    reasons = urgent_reasons(std if std is not None else lead_time.std_days_map(db),
                             sla_base_date(pr), items_of(db, pr.id))
    if not reasons:
        return False
    pr.is_urgent = True
    pr.updated_by = user_id
    db.commit()
    if pr.code:   # cờ gấp của YCMH đè xuống mọi ĐMH cùng pr_code (như khi bật tay)
        from app.modules.purchase_order.service import sync_urgent_group
        sync_urgent_group(db, pr.code, True)
    record(db, user_id, ENTITY, pr.id, "update",
           "Tự bật Đơn gấp — " + "; ".join(reasons[:5]))
    return True


def _save_items(db: Session, pr_id: int, items, user_id: int, auto_urgent: bool = True):
    """Upsert dòng THEO id — dòng có id thì cập nhật TẠI CHỖ (giữ nguyên id), dòng không id
    thêm mới, dòng cũ không còn trong danh sách thì xóa. GIỮ id để ảnh đối chiếu
    (đính kèm entity 'purchase_request_line_image' theo id dòng) không bị mồ côi khi lưu lại phiếu."""
    existing = {i.id: i for i in db.query(PurchaseRequestItem)
                .filter(PurchaseRequestItem.pr_id == pr_id).all()}
    # Mã hàng duy nhất trên phiếu — xem app/core/utils.assert_unique_product_codes
    assert_unique_product_codes([getattr(it, "product_code", "") for it in (items or [])],
                                [r.product_code for r in existing.values()])
    _pr = db.get(PurchaseRequest, pr_id)
    _base = sla_base_date(_pr)                   # mốc tính ngày QĐ có hàng — xem sla_base_date
    _std = lead_time.std_days_map(db)
    keep: set[int] = set()
    for it in items or []:
        data = it.model_dump()
        rid = data.pop("id", None)
        # Task 4: thành tiền dòng GỒM VAT (qty × giá × (1 + vat%/100))
        _vp = data.get("vat_pct") or 0
        data["amount"] = round((data.get("qty") or 0) * (data.get("price") or 0) * (1 + _vp / 100), 2)
        row = existing.get(rid) if rid else None
        if row is not None:                       # cập nhật tại chỗ -> id không đổi
            for k, v in data.items():
                setattr(row, k, v)
            row.updated_by = user_id
            keep.add(row.id)
        else:                                     # dòng mới
            # Thời gian dự kiến có hàng mặc định = NGÀY QĐ CÓ HÀNG theo phân loại
            # (Ngày tiếp nhận phiếu + số ngày QĐ; xem catalog/lead_time.py). CHỈ điền lúc TẠO
            # dòng: NSTM sửa lại sau (đổi giá trị đã có vẫn phải kèm lý do), và dòng đang sửa
            # mà người dùng cố ý xóa trắng thì giữ trắng.
            if not (data.get("expected_date") or "").strip():
                data["expected_date"] = lead_time.regulated_date(
                    _std, data.get("item_group") or "", _base)
            db.add(PurchaseRequestItem(pr_id=pr_id, created_by=user_id, updated_by=user_id, **data))
    for rid, row in existing.items():             # dòng bị bỏ khỏi danh sách -> xóa
        if rid not in keep:
            db.delete(row)
    db.flush()
    # Đồng bộ ngày cần hàng sớm nhất lên header phiếu (để lọc khoảng ngày trên CSDL chuẩn xác)
    all_req = [it.required_date for it in items_of(db, pr_id)
               if (it.required_date or "").strip() and it.line_status != LINE_STATUS_CANCELLED]
    if _pr:
        _pr.need_date = min(all_req) if all_req else ""
    db.commit()
    if auto_urgent:
        apply_auto_urgent(db, _pr, user_id, _std)   # CR-082 — dòng cần sớm hơn ngày QĐ -> Đơn gấp


def copy_pr(db: Session, pid: int, user_id: int) -> PurchaseRequest:
    """Nhân bản phiếu thành 1 phiếu Nháp mới: giữ dòng hàng, reset mã/trạng thái/NSTM/trạng thái dòng."""
    src = get_pr(db, pid)
    # NGƯỜI YÊU CẦU của bản sao = người BẤM NHÂN BẢN (không giữ người yêu cầu phiếu gốc): nếu giữ
    # nguyên thì created_by=người clone + requester=người gốc -> lệch danh + cả hai đều có quyền YC.
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    _u = db.get(User, user_id) if user_id else None
    _emp = db.get(Employee, getattr(_u, "employee_id", 0) or 0) if _u and getattr(_u, "employee_id", 0) else None
    if _emp:
        _requester, _requester_id = (_emp.full_name or ""), _emp.id
        _requester_position, _department = (_emp.position or ""), (_emp.department_name or "")
        _department_id = _emp.department_id or 0     # CR-086: lấy thẳng id phòng của nhân sự
        _head_of_dept = _emp.manager_name or ""
        # CR-071: bản sao đổi phòng theo người bấm nhân bản → chỉ định TBP phải tính lại
        # theo phòng MỚI, không bê id của phiếu gốc sang.
        _head_of_dept_id = find_dept_head_id(db, _department, _department_id)
    else:
        _requester, _requester_id = "", 0
        _requester_position, _department, _head_of_dept = "", src.department, src.head_of_dept
        _department_id = src.department_id
        _head_of_dept_id = src.head_of_dept_id
    pr = PurchaseRequest(
        code="", company_id=src.company_id, requester=_requester,
        requester_id=_requester_id,
        requester_position=_requester_position, department=_department,
        department_id=_department_id,
        # bao-CR-414: bản sao giữ phòng được nhờ; bao-CR-524: `0` cũ → phòng thu mua mặc định
        handler_dept_id=normalize_handler_dept_id(db, src.handler_dept_id),
        head_of_dept=_head_of_dept, head_of_dept_id=_head_of_dept_id,
        purpose=src.purpose, request_date=src.request_date,
        need_date=src.need_date, is_urgent=src.is_urgent, note=src.note,
        status="draft", assignee_id=0, created_by=user_id, updated_by=user_id,
        show_code_on_print=src.show_code_on_print, suggested_supplier=src.suggested_supplier,
        suggested_supplier_tax_code=src.suggested_supplier_tax_code,
        suggested_supplier_contact=src.suggested_supplier_contact,
        quote_filename=src.quote_filename, quote_file_url=src.quote_file_url,
        supplier_info=src.supplier_info or "",   # Task 4: giữ 2 cụm NCC khi nhân bản
    )
    sync_department_ref(db, pr)      # CR-086
    # CR-087: tên lấy từ `manager_name` của nhân sự, id lấy từ trưởng phòng — hai nguồn có thể
    # lệch nhau. Cho id nói tiếng nói cuối cùng rồi kéo tên theo.
    sync_head_of_dept_name(db, pr)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        from datetime import datetime
        date_str = datetime.now().strftime("%d%m%y")
        prefix = f"PYC{date_str}"
        last = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        seq = 1
        if last and last.code.startswith(prefix):
            try:
                seq = int(last.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _COPY = ["product_code", "product_name", "item_group", "group_desc", "qty", "unit",
             "price", "vat_pct", "amount", "warehouse", "required_date", "note"]
    _std = lead_time.std_days_map(db)
    for it in items_of(db, src.id):
        data = {k: getattr(it, k) for k in _COPY}
        db.add(PurchaseRequestItem(pr_id=pr.id, created_by=user_id, updated_by=user_id,
                                   assignee="", line_status=LINE_STATUS_NO_PO, progress_note="",
                                   # Ngày dự kiến của phiếu gốc là chuyện của phiếu gốc — dòng nhân
                                   # bản khởi tạo lại theo ngày QĐ như dòng mới.
                                   expected_date=lead_time.regulated_date(
                                       _std, it.item_group, sla_base_date(pr)),
                                   **data))
    db.commit()
    record(db, user_id, ENTITY, pr.id, "create", f"Nhân bản từ {src.code}")
    apply_auto_urgent(db, pr, user_id, _std)   # CR-082 — dòng nhân bản vẫn giữ ngày cần hàng cũ
    db.refresh(pr)
    return pr


def create_pr(db: Session, data: PRCreate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = PurchaseRequest(
        code=data.code or "", company_id=data.company_id, requester=data.requester,
        requester_id=data.requester_id,
        requester_position=data.requester_position, department=data.department,
        department_id=data.department_id,
        handler_dept_id=data.handler_dept_id or 0,   # bao-CR-414 (None → mặc định ở dưới, bao-CR-488/524)
        head_of_dept=data.head_of_dept, head_of_dept_id=data.head_of_dept_id,
        approver_employee_id=int(data.approver_employee_id or 0),   # bao-CR-499
        purpose=data.purpose, request_date=data.request_date,
        need_date=data.need_date, is_urgent=data.is_urgent, vat_rate=data.vat_rate,
        note=data.note, status="draft", created_by=user_id, updated_by=user_id,
        show_code_on_print=data.show_code_on_print,
        quote_filename=data.quote_filename,
        quote_file_url=data.quote_file_url,
    )
    # Task 4: NCC 2 cụm. Back-compat: body cũ gửi suggested_supplier* -> vào cụm 'req'.
    prev = {"req": {"name": data.suggested_supplier, "tax_code": data.suggested_supplier_tax_code,
                    "contact": data.suggested_supplier_contact},
            "pur": _empty_cluster(), "from_survey": False}
    apply_supplier_info(pr, build_clusters(prev, data, can_write_pur, from_survey=False))
    # bao-CR-465: phiếu lên mà không có phòng ban thì lùi về phòng của nhân sự đứng tên —
    # chạy TRƯỚC `sync_department_ref` để bước sau neo id và chụp lại tên như phiếu bình thường.
    fill_department_from_employee(db, pr, user_id)
    # CR-086: neo phòng ban bằng id ngay từ lúc lập phiếu (FE cũ chỉ gửi tên → tra ra id).
    sync_department_ref(db, pr)
    # bao-CR-480: phòng tự mua hàng lập phiếu thì phòng xử lý là chính phòng đó.
    # bao-CR-488: chỉ tra mặc định khi người lập KHÔNG chọn (không gửi ô này). Gửi 0 là chủ ý
    # nhờ phòng thu mua mặc định (nhà máy nhờ thu mua mua hộ) — phải giữ, không tra lại.
    if data.handler_dept_id is None:
        pr.handler_dept_id = default_handler_dept_id(db, pr.department_id)
    # bao-CR-524: gửi 0 (tick "Nhờ phòng khác xử lý" mà để trống / chọn thu mua) = phòng thu mua
    # mặc định — ghi id thật, không còn phòng ảo "Thu mua chung".
    pr.handler_dept_id = normalize_handler_dept_id(db, pr.handler_dept_id)
    # Tự điền Trưởng bộ phận theo phòng ban của người yêu cầu (nếu phòng có trưởng)
    if not pr.head_of_dept_id and (pr.department_id or pr.department):
        pr.head_of_dept_id = find_dept_head_id(db, pr.department, pr.department_id)
    # CR-087: ghi kép hai chiều — id có thì tên chạy theo, phiếu chỉ gửi tên thì tra ra id.
    sync_head_of_dept_name(db, pr)
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(pr)          # bao-CR-499: mặc định = Trưởng bộ phận
    db.add(pr)
    db.commit()
    db.refresh(pr)
    if not pr.code:
        date_str = ""
        if pr.request_date and len(pr.request_date) >= 10 and "-" in pr.request_date:
            parts = pr.request_date.split("-")
            if len(parts) == 3:
                date_str = f"{parts[2]}{parts[1]}{parts[0][-2:]}"
        if not date_str:
            from datetime import datetime
            date_str = datetime.now().strftime("%d%m%y")
            
        prefix = f"PYC{date_str}"
        last_pr = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%")).order_by(PurchaseRequest.code.desc()).first()
        
        seq = 1
        if last_pr and last_pr.code.startswith(prefix):
            try:
                seq = int(last_pr.code[len(prefix):]) + 1
            except ValueError:
                seq = 1
                
        pr.code = f"{prefix}{seq:02d}"
        db.commit()
    _save_items(db, pr.id, data.items, user_id)
    record(db, user_id, ENTITY, pr.id, "create")
    return pr


def update_pr(db: Session, pid: int, data: PRUpdate, user_id: int, can_write_pur: bool = False) -> PurchaseRequest:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected"):
        raise HTTPException(400, "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại "
                                 "(phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới).")
    old_urgent = bool(pr.is_urgent)
    old_head = int(pr.head_of_dept_id or 0)     # bao-CR-499: để ô người duyệt đi theo TBP mới
    # supplier_req/supplier_pur xử lý riêng bên dưới (không phải cột của model)
    for key, value in data.model_dump(exclude_unset=True,
                                      exclude={"items", "supplier_req", "supplier_pur"}).items():
        setattr(pr, key, value)
    if data.handler_dept_id is not None:   # bao-CR-524: 0 → phòng thu mua mặc định
        pr.handler_dept_id = normalize_handler_dept_id(db, data.handler_dept_id)
    # CR-086: FE cũ chỉ gửi TÊN phòng → bỏ id cũ đi rồi tra lại từ tên, kẻo đổi phòng mà id
    # vẫn nằm ở phòng trước đó. Gửi kèm id thì id nói tiếng nói cuối cùng.
    if data.department is not None or data.department_id is not None:
        if data.department_id is None:
            pr.department_id = 0
        sync_department_ref(db, pr)
    # Task 4: cập nhật cụm NCC (req do người yêu cầu · pur cần quyền supplier.write)
    if data.supplier_req is not None or data.supplier_pur is not None:
        apply_supplier_info(pr, build_clusters(clusters_of(pr), data, can_write_pur))
    # CR-071: đổi người duyệt chỉ định thì tên in trên phiếu phải chạy theo
    # CR-087: gửi mỗi TÊN (giao diện cũ) cũng phải tra lại id — bỏ id cũ trước, kẻo đổi người
    # mà id vẫn nằm ở người trước đó.
    if data.head_of_dept is not None or data.head_of_dept_id is not None:
        if data.head_of_dept_id is None:
            pr.head_of_dept_id = 0
        sync_head_of_dept_name(db, pr)
    from app.core.print_signers import default_approver_to_head
    default_approver_to_head(pr, old_head)       # bao-CR-499
    pr.updated_by = user_id
    db.commit()
    if data.items is not None:
        # CR-082: nếu chính lần lưu này là hành động TẮT cờ gấp thì đừng tự bật lại ngay —
        # người dùng vừa quyết định, hệ thống không cãi. Lần lưu sau mới xét lại.
        _save_items(db, pid, data.items, user_id,
                    auto_urgent=not (old_urgent and not bool(pr.is_urgent)))
    # Cờ Đơn gấp đổi → YCMH đè lên tất cả ĐMH cùng pr_code (đồng bộ nhóm)
    if bool(pr.is_urgent) != old_urgent and pr.code:
        from app.modules.purchase_order.service import sync_urgent_group
        sync_urgent_group(db, pr.code, bool(pr.is_urgent))
    record(db, user_id, ENTITY, pid, "update")
    db.refresh(pr)
    return pr


def set_urgent(db: Session, pid: int, is_urgent: bool, user_id: int) -> PurchaseRequest:
    """Bật/tắt cờ Đơn gấp trực tiếp (mọi trạng thái trừ đã hủy) + đồng bộ xuống các ĐMH cùng pr_code."""
    pr = get_pr(db, pid)
    if pr.status == "cancelled":
        raise HTTPException(400, "Phiếu đã hủy — không đổi được cờ Đơn gấp.")
    pr.is_urgent = bool(is_urgent)
    pr.updated_by = user_id
    db.commit()
    from app.modules.purchase_order.service import sync_urgent_group
    sync_urgent_group(db, pr.code, bool(is_urgent))
    record(db, user_id, ENTITY, pid, "update", f"Đơn gấp = {is_urgent}")
    db.refresh(pr)
    return pr


def delete_pr(db: Session, pid: int, user_id: int) -> None:
    pr = get_pr(db, pid)
    if pr.status not in ("draft", "rejected", "cancelled"):
        raise HTTPException(400, "Chỉ xóa được phiếu ở trạng thái Nháp, Bị trả lại hoặc Đã từ chối")
    pr.is_deleted = True
    pr.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, pid, "delete")
    #  bao-CR-580: YCMH sinh từ YCBG thì YCBG gỡ liên kết tới nó (trước đây vẫn bày phiếu đã xóa).
    from app.modules.survey_request.service import unlink_deleted_pr
    unlink_deleted_pr(db, pr, user_id)
