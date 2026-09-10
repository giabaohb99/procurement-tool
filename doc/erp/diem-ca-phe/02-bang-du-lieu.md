# PHÂN HỆ ĐIỂM CÀ PHÊ — BẢNG DỮ LIỆU VÀ API

**Bản:** 1.0 — 08/09/2026 · Đọc sau [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md)

5 bảng mới, module backend `app/modules/coffee_point/`. CHƯA viết code — đây là bản thiết kế
để soát trước khi sinh migration.

## 0. Năm quyết định xuyên suốt (đọc trước khi soát từng bảng)

1. **Người là `employee_id` (ID NHÂN SỰ), không phải ID tài khoản** — điểm là phúc lợi của
   nhân sự; tài khoản không gắn nhân sự (admin kỹ thuật, `employee_id = 0`) không có ví.
   Nhất quán với khuôn của phân hệ Công việc (`cong-viec/02` §0.1).
2. **Sổ cái chỉ INSERT.** `tab_coffee_ledger` không có endpoint UPDATE/DELETE nào; service
   cũng không được gọi. Sửa sai = thêm dòng đảo ngược (`adjust`). Số dư **không có cột** —
   luôn là `SUM(points)`; cần nhanh thì thêm cache sau, **cache tính lại được từ sổ, không
   bao giờ ngược lại**.
3. **Điểm là số nguyên CÓ DẤU, đơn vị = đồng** (đề nghị N1: 1 điểm = 1 đồng — chờ xác nhận).
   `grant/refund` ghi dương, `expire/spend/revoke` ghi âm, `adjust` hai chiều. Nhờ vậy số dư
   là một phép `SUM`, không phải CASE theo loại.
4. **Trạng thái / loại / cấp là `SMALLINT` + `IntEnum`** (luật R2/QĐ-11): khai ở
   `backend/app/core/status_catalog.py`, đăng qua `app/core/code_sets.py`, frontend lấy từ
   `gen_status_ts.py` — không hand-write bộ trạng thái nào ở TypeScript.
5. **Mọi bảng có `company_id`** (luật DB10 — quán có thể thuộc pháp nhân khác công ty mẹ);
   model đăng vào `app/core/all_models.py` kẻo autogenerate bỏ sót; ngày-mốc lưu chuỗi
   `"YYYY-MM-DD"`, kỳ lưu `"YYYYMM"` — so sánh từ vựng như khuôn chung.

## 1. Bộ IntEnum

| Enum | Giá trị | Ghi chú |
|---|---|---|
| `CoffeeLevel` | *(bộ giá trị chờ nghiệp vụ chốt — A-02)* ví dụ: `1 STAFF · 2 SUPERVISOR · 3 MANAGER · 4 DIRECTOR` | Cấp phúc lợi. Thêm cấp mới = thêm thành viên enum (sự kiện hiếm, cố ý qua code review); **đổi MỨC ĐIỂM thì là dữ liệu** (`tab_coffee_policy`), không đụng code |
| `CoffeeLedgerType` | `1 GRANT · 2 EXPIRE · 3 SPEND · 4 REFUND · 5 ADJUST · 6 REVOKE` | Loại dòng sổ. `EXPIRE` = thu hết dư kỳ cũ lúc reset; `REVOKE` = thu hồi nghỉ việc; `REFUND` = hoàn do đơn void |
| `CoffeeMemberStatus` | `1 ACTIVE · 2 SUSPENDED · 3 LEFT` | `SUSPENDED` = tạm ngưng hưởng (nghỉ không lương/thai sản — N6 của `09`): không cấp kỳ mới, giữ số dư; `LEFT` = đã nghỉ, khóa hẳn |
| `PosOrderMatchStatus` | `1 MATCHED · 2 UNMATCHED · 3 IGNORED` | `UNMATCHED` = đơn "Trừ điểm" không khớp được nhân sự (hàng chờ D-02); `IGNORED` = người xử lý đánh dấu bỏ qua có lý do |
| `PosSyncKind` | `1 PULL_ORDERS · 2 CHECK_VOIDS · 3 MONTHLY_RESET · 4 RECONCILE · 5 MIRROR` | Loại lần chạy trong nhật ký đồng bộ |
| `PosSyncStatus` | `1 RUNNING · 2 SUCCESS · 3 FAILED` | |

## 2. `tab_coffee_policy` — chính sách cấp điểm (A-01)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT, index | Pháp nhân áp chính sách |
| level_code | SMALLINT | `CoffeeLevel` |
| monthly_points | INT | Mức cấp mỗi kỳ (đồng-điểm, §0.3) |
| effective_from | VARCHAR(10) | `"YYYY-MM-DD"`. Mức áp cho một kỳ = dòng có `effective_from` lớn nhất ≤ ngày 1 của kỳ |
| note | VARCHAR(500) | |
| (audit) | | `AuditMixin` sẵn có: created/modified |

UNIQUE `(company_id, level_code, effective_from)`. **Không có cột `effective_to`** — dòng
sau tự kết thúc dòng trước (ít cột hơn, không có ca hai dòng chồng hiệu lực). **Không sửa
`monthly_points` của dòng đã qua kỳ cấp** — service chặn: dòng đã được một lần reset dùng
tới thì chỉ đọc; đổi mức = thêm dòng `effective_from` mới.

## 3. `tab_coffee_member` — thành viên & ghép POS365 (B-01, B-02)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT, index | |
| employee_id | BIGINT, **UNIQUE** | Một nhân sự một ví |
| level_code | SMALLINT | `CoffeeLevel` — cấp đang hưởng |
| title_id | BIGINT, default 0 | **Để dành** cho HR5 (danh mục chức danh) — bản 1 chưa dùng, xem A-02 |
| status | SMALLINT | `CoffeeMemberStatus` |
| pos_partner_id | BIGINT, default 0, index | Khóa ghép POS365; `0` = chưa ghép. **Ghi MỘT lần lúc người xác nhận ghép (B-02); mọi lần sau chỉ đối chiếu theo cột này, không tra lại theo tên/SĐT** (luật A3) |
| pos_partner_code | VARCHAR(50) | Mã khách bên POS365 (`KH-xxxxx`), chỉ để hiển thị |
| matched_by | BIGINT, default 0 | Ai bấm xác nhận ghép |
| matched_at | DATETIME NULL | |
| (audit) | | |

## 4. `tab_coffee_ledger` — sổ cái điểm (C-01) — CHỈ INSERT

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT, index | |
| employee_id | BIGINT, index | |
| period | CHAR(6), index | `"YYYYMM"` — kỳ mà dòng thuộc về |
| type | SMALLINT | `CoffeeLedgerType` |
| points | INT | **Có dấu** (§0.3) |
| pos_order_id | BIGINT, default 0 | Đơn POS365 sinh ra dòng (`spend`/`refund`); `0` với các loại khác |
| reason | VARCHAR(500) | **Bắt buộc khác rỗng với `ADJUST`** — service chặn |
| created_by | BIGINT | `0` = task tự động |
| created_at | DATETIME | |
| uniq_key | VARCHAR(40) NULL, **UNIQUE** | Khóa idempotent, sinh trong service — xem dưới |

**`uniq_key` — một cột gánh hai lời hứa chống trùng** (MySQL cho nhiều NULL trong UNIQUE):

| Loại dòng | uniq_key | Hứa gì |
|---|---|---|
| `GRANT` | `G-{employee_id}-{period}` | Một người một kỳ đúng một lần cấp (A-04) — chạy lại reset không nhân đôi |
| `EXPIRE` | `E-{employee_id}-{period}` | Chạy lại reset không thu hai lần |
| `SPEND` | `S-{pos_order_id}` | Kéo trùng một đơn không trừ hai lần (D-01) |
| `REFUND` | `R-{pos_order_id}` | Một đơn void hoàn đúng một lần (D-03) |
| `ADJUST`, `REVOKE` | NULL | Cho phép nhiều dòng — đã có lý do + người ghi làm dấu vết |

Ghi bằng `INSERT ... ON DUPLICATE KEY` bỏ qua / hoặc bắt `IntegrityError` bỏ qua — **tầng DB
là lớp chặn cuối, không tin bộ nhớ tiến trình**.

## 5. `tab_pos_order` — bản sao đơn hàng kéo về (D-01)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| company_id | BIGINT, index | |
| pos_order_id | BIGINT, **UNIQUE** | `Id` bên POS365 — khóa idempotent của toàn bộ phần kéo |
| pos_code | VARCHAR(50) | `Code` (vd `HC190522-0008`) — số hiển thị trên bill, dùng khi đối chất với quầy |
| purchase_date | DATETIME | `PurchaseDate` |
| pos_partner_id | BIGINT, default 0, index | Khách trên đơn; `0` = đơn không chọn khách |
| employee_id | BIGINT, default 0, index | Khớp qua `tab_coffee_member.pos_partner_id`; `0` = chưa khớp |
| total | DECIMAL(18,2) | Tổng đơn |
| points_paid | INT | Phần `Value` trả bằng tài khoản "Trừ điểm" — **chỉ phần này thành dòng `spend`**, đơn hỗn hợp phần còn lại là tiền của quán, không liên quan sổ |
| pos_status | INT | `Status` thô bên POS365 — lưu nguyên số họ trả, không phiên dịch (enum của họ, họ đổi mình không gãy) |
| match_status | SMALLINT | `PosOrderMatchStatus` |
| is_voided | SMALLINT, default 0 | Đặt 1 khi D-03 phát hiện void (kèm dòng `refund`) |
| raw_json | JSON | Response thô — chứng cứ khi đối chất; **lọc bỏ trường `Password` của Partner trước khi lưu** (cảnh báo `09` §3.2) |
| synced_at | DATETIME | |

## 6. `tab_pos_sync_run` — nhật ký đồng bộ (D-05)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| kind | SMALLINT | `PosSyncKind` |
| status | SMALLINT | `PosSyncStatus` |
| started_at / finished_at | DATETIME | |
| cursor_from / cursor_to | VARCHAR(30) | Mốc kéo (thời điểm/`$skip`) — lần sau nối tiếp từ đây |
| fetched / written / skipped | INT | Đếm được bao nhiêu: kéo về / ghi mới / bỏ qua vì trùng |
| error | TEXT | Rút gọn lỗi cuối cùng |
| triggered_by | BIGINT, default 0 | `0` = beat tự động; khác 0 = ai bấm chạy tay |

## 7. Cấu hình (biến môi trường — N-01, N-02)

| Biến | Mặc định | Ghi chú |
|---|---|---|
| `POS365_BASE_URL` | *(rỗng)* | `https://<cửa-hàng>.pos365.vn` — rỗng thì client coi như HARD_OFF |
| `POS365_USERNAME` / `POS365_PASSWORD` | *(rỗng)* | Tài khoản API riêng. **Không vào mã nguồn, không vào compose file chung** |
| `POS365_PAYMENT_ACCOUNT_ID` | `0` | `AccountId` của tài khoản "Trừ điểm" (N-04) |
| `POS365_HARD_OFF` | **`true`** | Cầu dao — chỉ prod đặt `false`. Client kiểm cờ này **trước mọi request**, có test |
| `POS365_PULL_MINUTES` | `5` | Chu kỳ kéo đơn — siết sau POC P6 |

## 8. API nội bộ `/api/coffee/...`

Tất cả trả phong bì `{success, message, data}` qua `core.response.success/error`; route gác
bằng `require(entity, action)`; truy vấn danh sách qua `apply_scope`; đọc lẻ qua `get_scoped`.

| Method + đường dẫn | Quyền (`require`) | Nội dung |
|---|---|---|
| GET/POST/PATCH `/api/coffee/policies[...]` | `coffee_policy` read/create/write | CRUD chính sách (khung `make_crud_router` nếu vừa; chặn sửa dòng đã dùng — §2) |
| GET `/api/coffee/members` · POST · PATCH | `coffee_member` read/create/write | Gán cấp, đổi trạng thái |
| GET `/api/coffee/members/pos-search?q=` | `coffee_member` write | Tra khách bên POS365 (SĐT/tên) phục vụ ghép — proxy sang `/api/partners`, **lọc bỏ `Password`** |
| POST `/api/coffee/members/{id}/match` | `coffee_member` write | Xác nhận ghép: ghi `pos_partner_id` (chặn ghi đè nếu đã có — muốn ghép lại phải gỡ trước, có audit) |
| POST `/api/coffee/members/{id}/create-partner` | `coffee_member` write | B-03: tạo khách mới bên POS365 rồi tự ghép |
| GET `/api/coffee/my-wallet` | đăng nhập (tự lấy `employee_id` của mình) | Số dư + sổ của CHÍNH người gọi — không nhận tham số id, khỏi cãi nhau về scope |
| GET `/api/coffee/ledger` | `coffee_ledger` read (+ scope) | Sổ cái, lọc người/kỳ/loại — `apply_filters` + `pagination` |
| POST `/api/coffee/ledger/adjust` | `coffee_ledger` write | A-07 — `reason` bắt buộc |
| GET `/api/coffee/lookup?q=` | `coffee_member` read (vai trò quầy) | C-04 — trả đúng `{name, balance}`, **không trả lịch sử** |
| GET `/api/coffee/pos-orders` | `pos_order` read | Đơn kéo về + tab chưa khớp + lệch đối chiếu |
| POST `/api/coffee/pos-orders/{id}/resolve` | `coffee_ledger` write | Xử lý đơn chưa khớp: gán người (sinh `spend`) hoặc `IGNORED` kèm lý do |
| POST `/api/coffee/sync/run` | `pos_order` write | Chạy tay một `PosSyncKind` |
| GET `/api/coffee/sync/runs` | `pos_order` read | Nhật ký đồng bộ |

**Tiếp theo:** [`03-tich-hop-pos365.md`](./03-tich-hop-pos365.md) — client, thuật toán đồng bộ, POC.
