"""bao-CR-538 — bài kiểm CANH: ô chữ của schema GHI phải chặn độ dài trước khi xuống MySQL.

Sự cố D30D24DF (30/09/2026): ghi chú 263 ký tự đi qua schema không có `max_length`, xuống MySQL
mới bị từ chối «Data too long» → người dùng thấy «lỗi không lường trước». Đại ca chốt: chặn ở
SCHEMA là tuyến chính, lỗi MySQL chỉ là lưới cuối.

Bài này quét các phân hệ thu mua: với mỗi schema GHI (không phải schema trả ra) và mỗi trường
chữ trùng tên một cột `String(n)` của model cùng phân hệ, gửi chuỗi dài n+1 ký tự thì schema phải
báo `string_too_long` ngay tại trường đó. Đỏ = liệt kê đủ mọi lỗ.

Kiểm bằng VALIDATION chứ không ghi xuống DB: bài kiểm chạy SQLite, mà SQLite không ép độ dài
VARCHAR (CLAUDE.md) — ghi xuống rồi khẳng định là xanh giả.
"""
import importlib
import inspect
import pkgutil

import pytest
from pydantic import BaseModel, ValidationError
from sqlalchemy import String

import app.core.all_models  # noqa: F401
from app.core.base_model import Base

#  Đợt 1 (thu mua) + đợt 2 (đại ca: «làm luôn 26 phân hệ kia»). Phân hệ nào có cột String(n) mà chưa
#  nằm ở đây thì `test_every_module_with_string_columns_is_covered` đỏ.
MODULES = ["survey", "survey_request", "purchase_request", "purchase_order", "payment_request", "supplier",
           "doc_catalog", "product", "work", "help_center", "catalog", "contract", "company", "approval",
           "leave", "coffee_point", "document", "ticket", "meeting_room", "customs", "department",
           "inventory", "attachment", "forum", "assistant", "dossier", "faq", "role", "agent_hub",
           "comment", "employee", "user", "setting", "user_preference"]

#  Tên lớp kết thúc bằng các đuôi này là schema TRẢ RA hoặc lọc — không ghi xuống DB.
READ_SUFFIXES = ("Out", "Response", "Read", "Detail", "Summary", "Row", "Filter", "Query", "Result", "Stats")

#  Schema GHI → các model nó ghi vào. Ghép theo TÊN trường chung một phân hệ thì sai (vd `note`
#  đầu phiếu YCMH khác `note` dòng YCMH), nên khai tay. Một trường có ở nhiều model đích thì lấy
#  trần NHỎ NHẤT. Schema ghi MỚI chưa khai ở đây (hay ở NO_TARGET) làm bài đỏ — buộc người thêm quyết.
TARGETS: dict[str, list[str]] = {
    "survey.LineApproveItem": ["SurveySupplierLine", "SurveyProductLine"],
    "survey.ProductLineIn": ["SurveyProductLine"],
    "survey.SupplierLineIn": ["SurveySupplierLine"],
    **{f"survey.{n}": ["Survey"] for n in ("ProductSurveyCreate", "ProductSurveyUpdate", "SupplierSurveyCreate",
                                             "SupplierSurveyUpdate", "SurveyCreate", "SurveyUpdate", "_HeaderUpdate",
                                             "_SurveyHeader", "RejectIn")},
    "survey_request.ReportDocIn": ["SurveyReportDoc"], "survey_request.ReportDocPatch": ["SurveyReportDoc"],
    "survey_request.ReportItemIn": ["SurveyReportItem"], "survey_request.ReportPhaseIn": ["SurveyReportPhase"],
    "survey_request.LineStatusIn": ["SurveyRequestLine"], "survey_request.SurveyRequestLineIn": ["SurveyRequestLine"],
    **{f"survey_request.{n}": ["SurveyRequest"] for n in ("SurveyRequestCreate", "SurveyRequestUpdate", "_Header",
                                                          "RejectIn", "TransferDeptIn")},
    **{f"purchase_request.{n}": ["PurchaseRequest"] for n in ("PRCreate", "PRUpdate", "ApproveIn", "AssignIn",
                                                              "ReasonIn", "RejectIn", "TransferDeptIn", "UrgentIn",
                                                              "SupplierClusterIn", "PRAssignSupplierIn")},
    **{f"purchase_request.{n}": ["PurchaseRequestItem"] for n in ("PRItemIn", "AssignItemIn", "ItemStatusIn",
                                                                  "ItemStatusItem", "PRAssignSupplierLineIn")},
    **{f"purchase_request.{n}": ["PurchaseRequestItemOption"] for n in ("PROptionCompleteIn", "PROptionManualIn",
                                                                        "PROptionSupplierIn", "PROptionSurveyIn",
                                                                        "PROptionUpdateIn")},
    "purchase_order.POCostTypeCreate": ["POCostType"], "purchase_order.POCostTypeUpdate": ["POCostType"],
    "purchase_order.POImportCostIn": ["POCost"], "purchase_order.CostLinesFinalizeIn": ["POCost"],
    "purchase_order.CostStageAdvanceIn": ["POCost"], "purchase_order.CostStageReopenIn": ["POCost"],
    "purchase_order.DeliveryIn": ["PODelivery"], "purchase_order.POItemIn": ["POItem"],
    "purchase_order.ItemProgressIn": ["POItem"],
    **{f"purchase_order.{n}": ["PurchaseOrder"] for n in ("POCreate", "POUpdate", "DocumentStatusIn", "RejectIn")},
    "payment_request.LineIn": ["PaymentRequestLine"],
    "payment_request.PRequestCreate": ["PaymentRequest"], "payment_request.PRequestUpdate": ["PaymentRequest"],
    **{f"supplier.{n}": ["Supplier"] for n in ("SupplierBase", "SupplierCreate", "SupplierUpdate")},
}
#  Đợt 2 — các phân hệ ngoài thu mua (chỉ khai những lớp KHÔNG tự ghép được, xem `_auto_targets`).
def _same(module: str, model: str, *names: str) -> dict[str, list[str]]:
    return {f"{module}.{n}": [model] for n in names}


TARGETS.update({
    **_same("doc_catalog", "DocFolderAccess", "FolderAccessBulkGrantIn", "FolderAccessBulkSubjectIn",
            "FolderAccessGrantIn", "FolderAccessLevelPatchIn", "FolderAccessRevokeIn"),
    **_same("doc_catalog", "DocFolder", "FolderCreate", "FolderUpdate"),
    **_same("work", "WorkGroup", "GroupCreate", "GroupUpdate"),
    **_same("work", "WorkLabelField", "LabelFieldIn", "LabelFieldUpdate"),
    **_same("work", "WorkLabelOption", "LabelOptionIn", "LabelOptionUpdate"),
    **_same("work", "WorkTaskLabel", "LabelIn"),
    **_same("work", "WorkList", "ListCreate", "ListUpdate"),
    **_same("work", "WorkSection", "SectionIn"),
    **_same("work", "WorkTask", "TaskCreate", "TaskUpdate", "TaskLinkIn", "TaskLinkUpdate"),
    **_same("approval", "ApprovalFlow", "FlowIn"),
    **_same("approval", "ApprovalNode", "NodeIn"),
    **_same("approval", "ApprovalSwitch", "SwitchIn"),
    **_same("approval", "ApprovalAction", "ActionIn", "HandoverIn", "ReasonIn", "ReassignIn"),
    **_same("leave", "LeaveHandover", "HandoverItem"),
    **_same("leave", "LeaveBalance", "LeaveBalanceAdjust", "LeaveBalanceAllocate", "LeaveBalanceCloseYear"),
    **_same("leave", "LeaveTypeSeniority", "SeniorityTierBase", "SeniorityTierCreate", "SeniorityTierUpdate"),
    **_same("coffee_point", "CoffeeLedger", "AdjustIn"),
    **_same("coffee_point", "CoffeeMember", "MemberCreate", "MemberUpdate", "CreatePartnerIn"),
    **_same("coffee_point", "CoffeePolicy", "PolicyIn"),
    **_same("coffee_point", "PosOrder", "MatchIn", "ResolveIn", "SelfOrderIn", "SelfOrderItemIn"),
    **_same("document", "DocumentClonePlan", "CloneCreate", "ClonePlanSave", "CloneStatusUpdate"),
    **_same("document", "DocumentLink", "ExcerptCreate", "LinkCreate"),
    **_same("document", "DocumentAccess", "AccessGrant", "AccessRevokeIn"),
    **{f"document.{n}": ["Document", "DocumentRequest"] for n in ("ApproveIn", "RejectIn", "ReviewedIn")},
    **_same("document", "Document", "ManualIssueNumberUpdate"),
    **_same("document", "DocumentVersion", "VersionCreate", "VersionContentUpdate"),
    **_same("document", "DocumentRecipient", "ScopeCreate"),
    **_same("document", "DocumentSignature", "SignIn"),
    **_same("meeting_room", "RoomBookingAttendee", "AttendeeItem"),
    **_same("meeting_room", "RoomBooking", "RoomBookingReschedule"),
    **_same("customs", "CustomsPesticide", "PesticideIn"),
    **_same("customs", "CustomsPesticideUse", "PesticideUseIn"),
    **_same("customs", "CustomsKindKeyword", "KindKeywordCreate", "KindKeywordUpdate"),
    **_same("customs", "CustomsRegulation", "RegulationCreate", "RegulationUpdate"),
    **_same("customs", "CustomsSavedFilter", "SavedFilterCreate", "SavedFilterUpdate"),
    **_same("customs", "CustomsSearchSynonym", "SearchSynonymCreate", "SearchSynonymUpdate"),
    **_same("department", "DepartmentCompany", "DepartmentCompanyReplace"),
    "inventory.AdjustIn": ["Inventory", "InventoryMove"],
    "attachment.RegisterIn": ["StoredFile", "FileLink"],
    **_same("forum", "ForumBoard", "BoardIn"),
    **_same("forum", "ForumPost", "PostIn", "ModerationIn"),
    **_same("assistant", "AssistantMessage", "AskIn", "HistoryItem"),
    **_same("dossier", "DossierProgress", "ProgressPayload"),
    **_same("role", "Permission", "PermissionItem"),
    **_same("agent_hub", "AgentUserKey", "AiKeyIn"),
    **_same("agent_hub", "AgentMcpKey", "McpKeyIn"),
    **_same("agent_hub", "AgentChatLink", "LinkNotifyIn"),
    **_same("employee", "Employee", "SelfContactUpdate"),
    **_same("user", "User", "NotifyEmailUpdate", "UserProvision"),
    **_same("user", "UserScope", "ScopeUpdate"),
})

#  Schema ghi không ghi thẳng cột nào (chỉ gói danh sách con / tham số thao tác).
NO_TARGET = {
    "survey.LineApproveIn", "survey.LineApproveCombined", "survey_request.ReportTemplateApplyIn",
    #  chỉ mang id / thứ tự / lệnh di chuyển — không ghi cột chữ nào
    "doc_catalog.DocumentFolderSetIn", "doc_catalog.FolderLinkIn", "doc_catalog.FolderUnlinkIn",
    "doc_catalog.FolderMoveIn", "doc_catalog.FolderReorderIn", "doc_catalog.FolderReorderItem",
    "work.SectionMove", "work.TaskMove", "work.AssigneesIn", "work.MemberIn", "work.TransferIn",
    "approval.ReorderIn", "coffee_point.ResetExecuteIn", "coffee_point.SyncRunIn",
    "document.PreviewApprovalIn", "attachment.ReorderIn", "forum.ReactionIn", "assistant.ConfirmUpdateIn",
    "role.RoleOrder", "employee.ExtraDepartmentsIn", "employee.EmployeeContactsIn",
    "employee.EmployeeFamiliesIn", "employee.SelfContactsIn", "user.ActiveUpdate", "user.RoleAssign",
    #  mật khẩu: không lưu nguyên văn (băm) — độ dài kiểm riêng ở luật mật khẩu
    "employee.SetPasswordIn", "user.PasswordReset",
    #  ghi vào bảng không có cột chữ, hoặc vào cột JSON của bảng cha
    "doc_catalog.DocTypeLinkRuleBase", "doc_catalog.DocTypeLinkRuleCreate", "doc_catalog.DocTypeLinkRuleUpdate",
    "leave.LeaveLineItem", "dossier.DossierFieldDef",
    #  ghi `issue_code` của Công ty / Phòng ban (phân hệ khác) — xem bài kiểm riêng của văn thư
    "doc_catalog.IssueCodeUpdate",
}

#  Phân hệ cố ý không quét: tên → lý do.
SKIPPED_MODULES: dict[str, str] = {}

#  Ngoại lệ có chủ đích: "phân hệ.Lớp.trường" → lý do.
ALLOWED: dict[str, str] = {}


def _models(module: str) -> dict:
    prefix = f"app.modules.{module}."
    return {m.class_.__name__: m.class_ for m in Base.registry.mappers if m.class_.__module__.startswith(prefix)}


def _limit(models: list, field: str) -> int | None:
    lengths = [m.__table__.c[field].type.length for m in models
               if field in m.__table__.c and isinstance(m.__table__.c[field].type, String)
               and m.__table__.c[field].type.length]
    return min(lengths) if lengths else None


def _write_schemas(module: str):
    pkg = importlib.import_module(f"app.modules.{module}")
    seen = set()
    for info in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"app.modules.{module}.{info.name}")
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if (issubclass(cls, BaseModel) and cls is not BaseModel and cls.__module__ == mod.__name__
                    and not name.endswith(READ_SUFFIXES) and cls not in seen):
                seen.add(cls)
                yield cls


_SCHEMA_SUFFIXES = ("Create", "Update", "Base", "Input", "Patch", "In")


def _auto_targets(module: str, cls_name: str, models: dict) -> list[str] | None:
    """Ghép tự động khi CHẮC: phân hệ một model, hoặc tên schema bỏ đuôi trùng đúng tên model."""
    if len(models) == 1:
        return list(models)
    stem = cls_name.lstrip("_")
    for suffix in _SCHEMA_SUFFIXES:
        if stem.endswith(suffix) and len(stem) > len(suffix):
            stem = stem[: -len(suffix)]
            break
    return [stem] if stem in models else None


def _holes() -> tuple[list[str], list[str]]:
    holes, unmapped = [], []
    for module in MODULES:
        models = {n: m for n, m in _models(module).items()
                  if any(isinstance(c.type, String) and c.type.length for c in m.__table__.columns)}
        for cls in _write_schemas(module):
            key = f"{module}.{cls.__name__}"
            if key in NO_TARGET:
                continue
            names = TARGETS.get(key) or _auto_targets(module, cls.__name__, models)
            if not names:
                unmapped.append(key)
                continue
            targets = [models[n] for n in names if n in models]
            for field, info in cls.model_fields.items():
                limit = _limit(targets, field)
                if not limit or "str" not in repr(info.annotation) or f"{key}.{field}" in ALLOWED:
                    continue
                try:
                    cls.model_validate({field: "x" * (limit + 1)})
                    caught = False
                except ValidationError as exc:
                    caught = any(e["type"] == "string_too_long" and e["loc"][:1] == (field,)
                                 for e in exc.errors())
                if not caught:
                    holes.append(f"{key}.{field} (cột String({limit}))")
    return holes, unmapped


def test_every_write_schema_is_mapped_to_its_table():
    _, unmapped = _holes()
    assert not unmapped, "schema ghi chưa khai bảng đích trong TARGETS / NO_TARGET: " + ", ".join(unmapped)


def test_every_write_schema_caps_string_columns():
    holes, _ = _holes()
    assert not holes, f"{len(holes)} ô chữ chưa chặn độ dài ở schema:\n  " + "\n  ".join(holes)


@pytest.mark.parametrize("module", MODULES)
def test_module_has_string_columns(module):
    """Canh chính bài canh: đổi tên phân hệ / dời model mà bài quét ra rỗng thì xanh giả."""
    assert any(_limit([m], c.name) for m in _models(module).values() for c in m.__table__.columns)


def test_every_module_with_string_columns_is_covered():
    """Phân hệ mới có cột String(n) mà quên thêm vào MODULES thì bài canh không quét tới nó."""
    import app.modules as modules_pkg
    missing = []
    for info in pkgutil.iter_modules(modules_pkg.__path__):
        has_string = any(isinstance(c.type, String) and c.type.length
                         for m in _models(info.name).values() for c in m.__table__.columns)
        has_schema = has_string and any(True for _ in _write_schemas(info.name))
        if has_schema and info.name not in MODULES and info.name not in SKIPPED_MODULES:
            missing.append(info.name)
    assert not missing, "phân hệ có cột String(n) + schema ghi nhưng chưa nằm trong MODULES: " + ", ".join(missing)
