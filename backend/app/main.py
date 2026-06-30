from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.core.response import error
from app.modules.attachment.controller import router as attachment_router
from app.modules.audit.controller import router as audit_router
from app.modules.auth.controller import router as auth_router
from app.modules.catalog.controller import (brand_router, item_group_router,
                                            unit_router, warehouse_router)
from app.modules.dashboard.controller import router as dashboard_router
from app.modules.purchase_request.controller import router as pr_router
from app.modules.company.controller import router as company_router
from app.modules.department.controller import router as department_router
from app.modules.employee.controller import router as employee_router
from app.modules.product.controller import router as product_router
from app.modules.role.controller import router as role_router
from app.modules.supplier.controller import router as supplier_router
from app.modules.user.controller import router as user_router

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
