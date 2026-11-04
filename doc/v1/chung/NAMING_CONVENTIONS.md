# Quy ước đặt tên (Naming Conventions)

> Mọi định danh code bằng **English**; tiếng Việt chỉ ở nhãn UI & dữ liệu.

## Database
- Bảng: prefix `tab_`, số ít, snake_case → `tab_company`, `tab_purchase_order`.
- Cột: snake_case → `supplier_name`, `tax_code`, `created_at`.
- Khóa chính: `id` BIGINT auto-increment (KHÔNG UUID).
- Mã: `VARCHAR(25)` / `VARCHAR(50)`; tên `VARCHAR(255)`; note/JSON `TEXT`; trạng thái `VARCHAR(30)`.
- Tiền `DECIMAL(18,2)`, số lượng `DECIMAL(18,3)`, boolean `TINYINT(1)`.
- Cây phân cấp: cột `parent` (BIGINT), `parent = 0` là gốc.
- Mọi bảng có: `created_at, created_by, updated_at, updated_by`.

## Backend (Python / FastAPI — PEP8)
- Hàm/biến: `snake_case` → `get_list_companies`, `create_company`.
- Class: `PascalCase` → `Company`, `CompanyCreate`.
- Mỗi chức năng = 1 thư mục trong `app/modules/<feature>/`: `controller.py · model.py · schema.py · service.py`.
- Dùng chung → `app/core/`.

## Frontend (React / TypeScript)
- Hàm/biến: `camelCase` → `getListCompanies`, `createCompany`.
- Component: `PascalCase` → `CompanyList`, `CompanyForm`.

## API REST
- `GET /api/companies` · `GET /api/companies/{id}` · `POST /api/companies` · `PATCH /api/companies/{id}` · `DELETE /api/companies/{id}`.
- Hành động: `POST /api/purchase-orders/{id}/approve`.
- Response chuẩn: `{ "success": true, "data": ... }` / `{ "success": false, "error": {...} }`.
