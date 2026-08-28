# SƠ ĐỒ KIẾN TRÚC — ERP V2

Bản 1.0 — 28/08/2026. Xem trực tiếp trên GitHub/VS Code (Mermaid). Sơ đồ vẽ mức khối,
tên container/domain lấy theo thực tế VPS; lệnh deploy chính xác đọc
[`quy-trinh-nhanh-va-deploy.md`](../../tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md).

## 1. Triển khai — ba môi trường

```mermaid
flowchart TB
    subgraph Internet
        U[Người dùng] --> CF[Cloudflare Tunnel]
    end

    subgraph VPS["VPS (Docker)"]
        subgraph PROD["Prod — nhánh main"]
            NP[nginx prod] --> WEBP[frontend v1<br>thumua.*]
            NP --> HELPP[help-center<br>help.*]
            NP --> APIP[api FastAPI]
            APIP --> CW[celery worker/beat<br>backup R2, email]
        end
        subgraph DEV["Dev — nhánh erp-v2<br>compose project procurement-dev"]
            ND[nginx dev] --> WEBD[frontend v1<br>devthumua.*]
            ND --> ERPD[frontend-v2<br>deverp.*]
            ND --> HELPD[help-center<br>devhelp.*]
            ND --> APID[api FastAPI dev]
        end
        MYSQL[(MySQL 8.4<br>2 database: prod + dev)]
        APIP --> MYSQL
        APID --> MYSQL
    end

    CF --> NP
    CF --> ND
    APIP --> R2[(Cloudflare R2<br>STORAGE_PREFIX tách prod/dev)]
    APID --> R2
```

Hai quy tắc sống còn: deploy prod **bắt buộc** `-f docker-compose.production.yml` (thiếu là 502);
cập nhật mã trên VPS bằng `git fetch` + `git reset --hard origin/<nhánh>`, không `pull`
(hai worktree chung một repo). Dev tắt email thật bằng `EMAIL_HARD_OFF`.

## 2. Local — một compose đủ cả hệ

```mermaid
flowchart LR
    DEV_LOCAL[Trình duyệt] --> WEB[web :8080<br>frontend v1]
    DEV_LOCAL --> ERP[erp :8083<br>frontend-v2]
    DEV_LOCAL --> HELP[help :8082]
    DEV_LOCAL --> ADM[adminer :8081]
    WEB & ERP & HELP -->|proxy /api| API[api :8000<br>alembic upgrade + seed lúc khởi động]
    API --> DB[(db MySQL 8)]
    API --> REDIS[(redis)]
    CELERY[celery-worker/beat] --> REDIS
    CELERY --> DB
    API -.tương lai RAG.-> QDRANT[(qdrant)]
```

## 3. Từ quyền trong DB tới thẻ phân hệ trên màn hình

```mermaid
flowchart TB
    subgraph BE["Backend — chốt thật"]
        GRANT[(Grant: người × vai trò<br>entity × action + phạm vi)] --> PROFILE[get_perm_profile<br>cache 60s]
        PROFILE --> REQ["require(entity, action)<br>403 khi thiếu"]
        PROFILE --> SCOPE["apply_scope / get_scoped<br>lọc dòng dữ liệu"]
    end

    subgraph FE["Frontend-v2 — chỉ ẩn/hiện"]
        LOGIN[Đăng nhập trả bản đồ quyền] --> CAN["can(entity, action)"]
        CAN --> ITEM["itemAllowed: mục menu khai<br>entity / entities / action / manage"]
        ITEM --> NAV[visibleNavItems của phân hệ]
        NAV --> CARD{"Còn ≥ 1 mục hiện được?"}
        CARD -->|Có| OPEN[Thẻ phân hệ MỞ]
        CARD -->|Không| LOCK[Thẻ KHÓA<br>'chưa được cấp quyền']
        EXT[Phân hệ externalUrl] --> OPEN
    end

    PROFILE -.trả lúc đăng nhập.-> LOGIN
```

Đọc kèm [`03-phan-quyen-va-hien-thi.md`](03-phan-quyen-va-hien-thi.md): mục menu quên khai khóa
là nhánh "Còn ≥ 1 mục" luôn đúng — chính là lỗi CR-196, đã có test canh.
