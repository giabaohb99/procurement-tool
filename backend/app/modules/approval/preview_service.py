"""XEM TRƯỚC LUỒNG DUYỆT — «Người duyệt dự kiến» (phase 01, duoc-CR-473).

Trả lời câu "gửi duyệt NGAY BÂY GIỜ thì ai sẽ ký" mà KHÔNG mở phiên duyệt nào —
chỉ đọc, không ghi, không commit, không audit.

Dùng lại ĐÚNG bốn khối đã có của bộ máy duyệt, không chép:

  * `flow_service.is_enabled` / `pick_flow` / `snapshot` / `stages` / `step_of_stage`
    — chọn luồng và chọn nhánh, y hệt lúc `instance_service.start()` chạy thật;
  * `approver_resolver.resolve` — bảy cách chọn người duyệt;
  * `instance_service.exclude_submitter_ids` / `split_duplicate_approvers` — hai
    luật lọc của `open_stage` đã tách thành hàm thuần đúng cho việc này.

Khác `open_stage` ở đúng một chỗ: `open_stage` chạy XUYÊN QUA một phiên duyệt
thật, "ai đã duyệt chặng trước" đọc từ bảng `tab_approval_task`. Ở đây CHƯA có
phiên nào cả, nên "đã duyệt chặng trước" là một GIẢ ĐỊNH LẠC QUAN: ai được giao
việc ở một chặng thì coi như rồi cũng sẽ duyệt chặng đó — dùng để suy ra những
chặng sau sẽ tự động qua vì trùng người. Đây là lý do thẻ trên giao diện luôn
phải kèm câu "dự kiến, chốt lúc gửi duyệt".
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from . import approver_resolver, flow_service, instance_service, serializer
from .flow_model import (APPROVER_FIELD, APPROVER_LEVEL_UP, APPROVER_ROLE,
                         NODE_CC, NO_APPROVER_FALLBACK, SKIP_ADJACENT,
                         SKIP_ANY_BEFORE, MULTI_MODE_LABELS, NODE_KIND_LABELS)

MODE_FLOW = "flow"
MODE_LEGACY = "legacy"

#  Nhãn tiếng Việt cho những ô trên phiếu hay được khai kiểu FIELD — chỉ để câu
#  «Sẽ là ... — chưa chọn» đọc tự nhiên. Ô lạ (module khác, chưa liệt kê) thì
#  rơi về đúng tên cột, vẫn đọc được, chỉ không đẹp bằng.
FIELD_LABELS = {
    "signer_employee_id": "người ký",
    "owner_employee_id": "người chịu trách nhiệm nội dung",
    "drafter_employee_id": "người soạn thảo",
}


def preview_flow(db: Session, entity: str, subject: dict,
                  submitter_employee_id: int | None, *,
                  company_flow_only: bool = False) -> dict:
    """Xem trước luồng sẽ áp cho `subject` nếu gửi duyệt ngay bây giờ.

    Trả `{mode, engine_enabled, flow_name, steps, cc}`:

    * `mode = "flow"` — luồng nhiều chặng, `steps` là từng chặng (bỏ CC ra
      riêng vào `cc`, xem `_stage_step`);
    * `mode = "legacy"` — không luồng nào khớp (`pick_flow` trả `None`), hoặc bộ
      máy đang TẮT — `steps`/`cc` rỗng, người gọi tự ghép câu "duyệt một bước".

    Câu "loại này KHÔNG CẦN duyệt" (`DocType.needs_approval = false`) không nằm
    ở đây — bộ máy duyệt không biết gì về khái niệm loại văn bản. Người gọi (API
    của văn bản) tự kiểm cờ đó TRƯỚC khi gọi hàm này.
    """
    engine_enabled = flow_service.is_enabled(db, entity)
    flow = (flow_service.pick_flow(db, entity, subject, company_only=company_flow_only)
            if engine_enabled else None)

    if flow is None:
        return {"mode": MODE_LEGACY, "engine_enabled": engine_enabled,
                "flow_name": "", "steps": [], "cc": []}

    raw_snapshot = flow_service.snapshot(db, flow)

    steps: list[dict] = []
    cc: list[dict] = []
    #  Hai tập "coi như đã duyệt", đúng hai phạm vi mà `skip_duplicate` phân
    #  biệt — xem `instance_service.split_duplicate_approvers`.
    approved_prev_stage: set[int] = set()
    approved_any_stage: set[int] = set()

    for seq in flow_service.stages(raw_snapshot):
        node = flow_service.step_of_stage(raw_snapshot, seq, subject)

        if node is None:
            #  Không nhánh nào khớp và không có nhánh mặc định — đúng ca phiếu
            #  KẸT của `open_stage`. Vẫn liệt kê ra (không dừng vòng lặp) để
            #  người soạn thấy được HÌNH DẠNG cả luồng, không chỉ phần chạy tới.
            steps.append({
                "seq": seq, "name": f"Chặng {seq}", "rule_label": "",
                "approvers": [], "fallback_used": False, "pending_field": "",
                "note": "",
                "unresolved_reason": ("Không nhánh nào khớp điều kiện và luồng "
                                      "không khai nhánh mặc định — phiếu sẽ DỪNG "
                                      "ở chặng này."),
            })
            approved_prev_stage = set()
            continue

        if node.node_kind == NODE_CC:
            recipients = approver_resolver.resolve(db, node, subject, submitter_employee_id)
            cc.append({
                "seq": node.seq, "name": node.name or NODE_KIND_LABELS.get(node.node_kind, ""),
                "rule_label": _rule_label(db, node),
                "approvers": _approver_profiles(db, recipients),
            })
            #  Bước CC không sinh việc, không có ai "đã duyệt" ở đây — xem
            #  `open_stage`: nó chỉ ghi dấu vết rồi đi tiếp ngay.
            approved_prev_stage = set()
            continue

        step = _stage_step(db, node, subject, submitter_employee_id,
                            approved_prev_stage, approved_any_stage)
        steps.append(step)

        newly_covered = {row["employee_id"] for row in step["approvers"]}
        approved_prev_stage = newly_covered
        approved_any_stage |= newly_covered

    return {"mode": MODE_FLOW, "engine_enabled": engine_enabled, "flow_name": flow.name,
            "steps": steps, "cc": cc}


def _stage_step(db: Session, node, subject: dict, submitter_employee_id: int | None,
                 approved_prev_stage: set[int], approved_any_stage: set[int]) -> dict:
    """Một chặng DUYỆT (đã loại CC) — áp đủ ba luật của `open_stage`."""
    step = {
        "seq": node.seq, "name": node.name or "", "rule_label": _rule_label(db, node),
        "approvers": [], "fallback_used": False, "pending_field": "", "note": "",
        "unresolved_reason": "",
    }

    raw_ids = approver_resolver.resolve(db, node, subject, submitter_employee_id)

    #  Chặng kiểu FIELD (vd "người ký") chưa có giá trị: đây là chuyện BÌNH
    #  THƯỜNG lúc đang soạn, không phải sự cố tổ chức — câu khác hẳn "không tìm
    #  được người duyệt", và KHÔNG đi qua `on_no_approver` (dự phòng/dừng phiếu)
    #  vì chưa có gì để dừng cả, người soạn chỉ chưa chọn xong.
    if node.approver_kind == APPROVER_FIELD and not raw_ids:
        field = (node.approver_ref or "").strip()
        step["pending_field"] = field
        step["unresolved_reason"] = f"Sẽ là {FIELD_LABELS.get(field, field or 'người duyệt')} — chưa chọn"
        return step

    ids = instance_service.exclude_submitter_ids(node.approver_kind, submitter_employee_id, raw_ids)

    if node.skip_duplicate == SKIP_ADJACENT:
        already = approved_prev_stage
    elif node.skip_duplicate == SKIP_ANY_BEFORE:
        already = approved_any_stage
    else:
        already = set()
    ids, duplicate = instance_service.split_duplicate_approvers(ids, node.skip_duplicate, already)

    if ids:
        step["approvers"] = _approver_profiles(db, ids)
        return step

    if duplicate:
        #  Cả chặng toàn người đã duyệt (hoặc coi như đã duyệt) ở chặng trước —
        #  `open_stage` cho qua ngay, không mở việc mới cho ai.
        step["note"] = ("Mọi người ở chặng này đều đã duyệt ở (các) chặng trước "
                       "— chặng này sẽ tự động qua, không cần ai bấm thêm.")
        return step

    if node.on_no_approver == NO_APPROVER_FALLBACK and node.fallback_employee_id:
        step["approvers"] = _approver_profiles(db, [node.fallback_employee_id])
        step["fallback_used"] = True
        step["note"] = "Không tìm được người duyệt theo quy tắc — sẽ chuyển cho người dự phòng."
        return step

    step["unresolved_reason"] = (
        f"Không tìm được người duyệt cho chặng «{node.name or node.seq}» — "
        "phiếu sẽ DỪNG LẠI ở đây và cần quản trị sửa luồng."
    )
    return step


def _rule_label(db: Session, node) -> str:
    """Câu QUY TẮC khai trong luồng (không phụ thuộc `subject`) — vd «Theo vai
    trò: Trưởng phòng Nhân sự». Dùng chung cho cả trợ lý AI (`describe_step`)
    lẫn xem trước ở màn tạo văn bản.

    ⚠️ `node` ở đây thường là `SimpleNamespace` dựng từ BẢN CHỤP luồng
    (`flow_service.step_of_stage`), không phải `ApprovalNode` thật — nên KHÔNG
    gọi `serializer.node_out` (đụng `node.flow_id`, cột không có trong bản
    chụp). Gọi thẳng `serializer.approver_names`, hàm chỉ đọc hai cột luôn có
    ở cả hai hình dạng (`approver_ref`, `approver_kind`).
    """
    from .flow_model import APPROVER_KIND_LABELS

    rule = APPROVER_KIND_LABELS.get(node.approver_kind, "")
    ref = (node.approver_ref or "").strip()
    names = serializer.approver_names(db, node)

    if names:
        rule += f": {names}"
    elif node.approver_kind == APPROVER_ROLE and ref:
        from app.modules.role.model import Role

        codes = [part.strip() for part in ref.split(",") if part.strip()]
        role_names = [row.name for row in db.query(Role).filter(Role.code.in_(codes)).all()]
        rule += ": " + ", ".join(role_names or codes)
    elif node.approver_kind == APPROVER_LEVEL_UP and ref:
        rule += f" ({ref} cấp)"
    elif node.approver_kind == APPROVER_FIELD and ref:
        rule += f" (ô '{ref}' trên phiếu)"
    return rule


def _approver_profiles(db: Session, ids: list[int]) -> list[dict]:
    """`employee_id` → `{employee_id, name, position}`, giữ NGUYÊN thứ tự `ids`."""
    if not ids:
        return []
    by_id = {row.id: row for row in db.query(Employee).filter(Employee.id.in_(ids)).all()}
    result = []
    for employee_id in ids:
        employee = by_id.get(employee_id)
        result.append({
            "employee_id": employee_id,
            "name": employee.full_name if employee else f"Nhân sự #{employee_id}",
            "position": (employee.position if employee else "") or "",
        })
    return result


def _employee_names(db: Session, ids: list[int]) -> list[str]:
    """Chỉ tên — cho `describe_step` (trợ lý AI đọc thành câu, không cần chức vụ)."""
    return [row["name"] for row in _approver_profiles(db, ids)]


def describe_step(db: Session, node, subject: dict, submitter_employee_id: int | None) -> dict:
    """Mô tả MỘT bước rời rạc — trợ lý AI dùng (`assistant/tools/document_tool.py`).

    Trước 23/09/2026 hàm này (`_describe_step`) sống trong chính công cụ trợ lý,
    tự gọi `approver_resolver.resolve` thô, KHÔNG áp `exclude_submitter_ids`.
    Chuyển về đây để dùng chung `_rule_label`, và áp luôn luật I08 cho đúng —
    trợ lý AI không còn nói "phiếu của chính bạn cần bạn tự ký".

    KHÔNG áp `split_duplicate_approvers`: luật đó cần TRẠNG THÁI đi qua nhiều
    chặng liên tiếp (`preview_flow` mới đi hết cả luồng), còn hàm này tả TỪNG
    BƯỚC rời rạc theo yêu cầu của `approval_flow_lookup` — không có gì để so
    trùng.
    """
    approvers = approver_resolver.resolve(db, node, subject, submitter_employee_id)
    approvers = instance_service.exclude_submitter_ids(
        node.approver_kind, submitter_employee_id, approvers)

    rule = _rule_label(db, node)
    step = {
        "seq": node.seq,
        "name": node.name or NODE_KIND_LABELS.get(node.node_kind, ""),
        "node_kind": NODE_KIND_LABELS.get(node.node_kind, ""),
        "approver_rule": rule,
        #  Tên NGƯỜI THẬT nếu chính người hỏi nộp phiếu này. Rỗng = chưa tính
        #  được (thiếu trưởng bộ phận, vai trò chưa gán ai...) — nói thẳng, đừng
        #  bịa.
        "approvers_for_me": _employee_names(db, approvers),
    }
    if node.branch_key:
        step["branch"] = node.branch_key
    if (node.condition or "").strip():
        step["condition"] = node.condition
    if MULTI_MODE_LABELS.get(node.multi_mode) and node.multi_mode != 1:
        step["multi_mode"] = MULTI_MODE_LABELS[node.multi_mode]
    return step
