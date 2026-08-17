from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.limiter import limiter
from app.core.response import error
from app.modules.attachment.controller import router as attachment_router
from app.modules.audit.controller import router as audit_router
from app.modules.auth.controller import router as auth_router
from app.modules.doc_catalog.book_controller import router as document_book_router
from app.modules.doc_catalog.numbering_rule_controller import router as numbering_rule_router
from app.modules.doc_catalog.link_rule_controller import router as link_rule_router
from app.modules.doc_catalog.controller import (doc_type_router,
                                               external_party_router)
from app.modules.document.controller import router as document_router
from app.modules.document.link_controller import router as document_link_router
from app.modules.document.scope_controller import router as document_scope_router
from app.modules.document.signature_controller import router as document_signature_router
from app.modules.document.clone_controller import router as document_clone_router
from app.modules.document.template_controller import router as document_template_router
from app.modules.catalog.controller import (brand_router, item_group_router,
                                            unit_router, warehouse_router)
from app.modules.dashboard.controller import router as dashboard_router
from app.modules.inventory.controller import router as inventory_router
from app.modules.payable.controller import router as payable_router
from app.modules.payment_request.controller import router as payment_request_router
from app.modules.purchase_order.controller import router as po_router
from app.modules.purchase_progress.controller import router as purchase_progress_router
from app.modules.survey_progress.controller import router as survey_progress_router
from app.modules.report.controller import router as report_router
from app.modules.contract.controller import router as contract_router
from app.modules.alert.controller import router as alert_router
from app.modules.purchase_request.controller import router as pr_router
from app.modules.company.controller import router as company_router
from app.modules.department.controller import router as department_router
from app.modules.employee.controller import router as employee_router
from app.modules.product.controller import router as product_router
from app.modules.purchase_history.controller import router as purchase_history_router
from app.modules.role.controller import router as role_router
from app.modules.survey.controller import router as survey_router
from app.modules.survey.controller import report_router as survey_report_router
from app.modules.supplier.controller import router as supplier_router
from app.modules.user.controller import router as user_router
from app.modules.setting.controller import router as setting_router
from app.modules.notification.controller import router as notification_router
from app.modules.push.controller import router as push_router
from app.modules.category_assignee.controller import router as category_assignee_router
from app.modules.survey_request.controller import router as survey_request_router
from app.modules.import_tool.controller import router as import_tool_router
from app.modules.backup.controller import router as backup_router
from app.modules.help_center.controller import router as help_center_router
from app.modules.faq.controller import router as faq_router
from app.modules.ticket.controller import router as ticket_router
from app.modules.comment.controller import router as comment_router

app = FastAPI(title="Procurement Tool API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error(str(exc.detail), code=str(exc.status_code), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error("Dữ liệu không hợp lệ", code="validation_error", status_code=422,
                 details=exc.errors())


@app.get("/api/health")
def health():
    return {"success": True, "message": "ok"}


app.include_router(auth_router)
app.include_router(company_router)
app.include_router(department_router)
app.include_router(employee_router)
app.include_router(supplier_router)
app.include_router(product_router)
app.include_router(role_router)
app.include_router(user_router)
app.include_router(audit_router)
app.include_router(dashboard_router)
app.include_router(pr_router)
app.include_router(attachment_router)
app.include_router(warehouse_router)
app.include_router(unit_router)
app.include_router(item_group_router)
app.include_router(brand_router)
app.include_router(doc_type_router)
app.include_router(external_party_router)
app.include_router(document_book_router)
app.include_router(numbering_rule_router)
app.include_router(link_rule_router)
app.include_router(document_template_router)
#  ⚠️ THỨ TỰ QUAN TRỌNG. Bốn router dưới đây dùng CHUNG prefix `/api/documents`
#  với `document_router`, mà `document_router` có route động `/{document_id}`.
#  FastAPI khớp theo THỨ TỰ ĐĂNG KÝ, nên nếu `document_router` đứng trước thì
#  `/api/documents/applies-to-me` bị khớp vào `/{document_id}` và chết ở bước
#  ép kiểu số nguyên — 422, không phải 404, nên nhìn log cũng không ra ngay.
#
#  Quy tắc: router nào có đường dẫn TĨNH dưới `/api/documents/...` thì phải
#  đăng ký TRƯỚC `document_router`. Xem `test_thu_tu_route_van_ban.py`.
app.include_router(document_link_router)
app.include_router(document_scope_router)
app.include_router(document_signature_router)
app.include_router(document_clone_router)
app.include_router(document_router)
app.include_router(survey_router)
app.include_router(survey_report_router)
app.include_router(po_router)
app.include_router(purchase_progress_router)
app.include_router(survey_progress_router)
app.include_router(purchase_history_router)
app.include_router(inventory_router)
app.include_router(payable_router)
app.include_router(payment_request_router)
app.include_router(report_router)
app.include_router(contract_router)
app.include_router(alert_router)
app.include_router(setting_router)
app.include_router(notification_router)
app.include_router(push_router)
app.include_router(category_assignee_router)
app.include_router(survey_request_router)
app.include_router(import_tool_router)
app.include_router(backup_router)
app.include_router(help_center_router)
app.include_router(faq_router)
app.include_router(ticket_router)
app.include_router(comment_router)
