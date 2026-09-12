# TDD — Khối «Báo cáo thực hiện» trên chi tiết YCBG

| | |
|---|---|
| Loại | Thiết kế kỹ thuật (TDD) cho một tính năng |
| Bản | 1.0 — 12/09/2026 |
| Phạm vi mã | backend `app/modules/survey_request/report_*` · frontend `frontend-v2/src/modules/procurement/**/survey-report/**` |
| Migration | `7816572fed52` (down_revision `bee157de2ec8`) |
| Tài liệu chức năng | [`19-bao-cao-thuc-hien-ycbg.md`](../tai-lieu-chuc-nang/19-bao-cao-thuc-hien-ycbg.md) |
| Brief | [`doc/erp/18-bao-cao-thuc-hien-ycbg.md`](../erp/18-bao-cao-thuc-hien-ycbg.md) |

---

## 1. Mục tiêu & phạm vi

### 1.1 Trong phạm vi

- 3 bảng con của phiếu YCBG để lưu **giai đoạn · nút dòng hàng · hồ sơ** của một
  khối theo dõi tiến trình thực hiện thương vụ.
- Bộ API `/api/survey-requests/{sid}/report[...]` — CRUD ba loại đối tượng + khởi
  tạo khung mẫu, mọi mutation trả về **nguyên khối mới**.
- Khối UI trên trang chi tiết YCBG với hai khung nhìn (xem tài liệu chức năng).

### 1.2 Ngoài phạm vi

- **Không thêm khóa quyền mới** — tái dùng entity `survey_request` (luật «một khóa =
  một màn hình», CR-157). Ba bảng con cố ý **không có khóa phân quyền riêng**.
- Không nối kho `attachment` thật (ô tệp là chuỗi tự do).
- Không có bộ máy duyệt.

> **Phần mở rộng «hạn hồ sơ + nhân sự thực hiện» (12/09/2026):** hồ sơ có thêm
> `start_date`, `expires_at`, `assignee_id`. Backend **đã trọn** (model · schema ·
> service · migration `a1c2e3d4f5b6`) và FE `types/…` + tầng API đã khai; phần còn
> lại đang hoàn thiện là **ô nhập trên hộp thoại hồ sơ** (chọn ngày + chọn nhân sự)
> và cách hiển thị chúng trên dòng. Chi tiết ở [§3a](#3a-hạn-hồ-sơ--nhân-sự-thực-hiện).

## 2. Kiến trúc & danh sách tệp

```
backend/app/modules/survey_request/
├── report_constants.py     # bộ mã trạng thái (số) + 5 giai đoạn mẫu + trần
├── report_model.py         # 3 bảng SQLAlchemy
├── report_schema.py        # Pydantic In/Patch, ràng buộc max_length khớp model
├── report_service.py       # nghiệp vụ (không xét quyền, không commit)
└── report_controller.py    # router /api/survey-requests/{sid}/report/*

frontend-v2/src/modules/procurement/
├── types/survey-request-report.ts             # kiểu + bộ mã (gõ tay)
├── api/survey-request-report-api.ts           # tầng gọi API
├── hooks/use-survey-request-report.ts         # TanStack Query
├── utils/survey-report-helpers.ts (+ .test)   # logic thuần: lọc/khóa/tracking
└── components/survey-report/
    ├── survey-report-card.tsx        # khối chính (thanh công cụ, giai đoạn, dòng)
    ├── survey-report-tracking.tsx    # khung Tiến trình bên phải
    ├── survey-report-doc-dialog.tsx  # hộp thoại hồ sơ
    ├── survey-report-item-dialog.tsx # hộp thoại nút dòng hàng
    └── survey-report-phase-dialog.tsx# hộp thoại giai đoạn
```

Đăng ký: model thêm vào `app/core/all_models.py`; router `survey_request_report_router`
thêm vào `app/main.py`. Khối gắn vào trang bằng `<SurveyReportCard>` trong
`pages/survey-request-detail-page.tsx` (`canEdit={canViewNstm}`).

## 3. Mô hình dữ liệu

Cả ba bảng kế thừa `AuditMixin` (id, created_at/by, updated_at/by). Đều index
`survey_request_id`. **Không FK** — quan hệ giữ ở tầng service để xóa có kiểm soát.

### `tab_survey_request_report_item` — Nút dòng hàng
| Cột | Kiểu | Mô tả |
|---|---|---|
| survey_request_id | BIGINT INDEX | Thuộc phiếu YCBG |
| name | VARCHAR(100) | Tên nút (vd «K₂SO₄») |
| sort_order | SMALLINT | Thứ tự hiển thị |

### `tab_survey_request_report_phase` — Giai đoạn
| Cột | Kiểu | Mô tả |
|---|---|---|
| survey_request_id | BIGINT INDEX | Thuộc phiếu YCBG |
| name | VARCHAR(255) | Tên giai đoạn |
| location | VARCHAR(255) | Diễn giải / nơi thực hiện |
| sort_order | SMALLINT | Thứ tự hiển thị |

### `tab_survey_request_report_doc` — Hồ sơ
| Cột | Kiểu | Mô tả | Ghi chú |
|---|---|---|---|
| survey_request_id | BIGINT INDEX | Thuộc phiếu YCBG | |
| phase_id | BIGINT INDEX | Thuộc giai đoạn | |
| item_id | BIGINT INDEX | Gắn nút dòng hàng; **`0` = Chung** | Cố ý không FK: xóa nút → service đặt về 0 |
| title | VARCHAR(255) | Tiêu đề | |
| description | TEXT | Mô tả | |
| required | BOOLEAN | Cờ «Bắt buộc» (chỉ nhãn) | |
| status | SMALLINT INDEX | Mã trạng thái 0..3 | R2/QĐ-11 |
| file_note | VARCHAR(500) | Tên tệp / link | Chuỗi tự do |
| depends | JSON | Danh sách id hồ sơ tiên quyết | Trần 30 phần tử; service lọc id chết khi trả ra |
| start_date | DATE NULL | Ngày bắt đầu thực hiện | migration `a1c2e3d4f5b6` — xem §3a |
| expires_at | DATE NULL | Ngày hết hiệu lực / hạn | migration `a1c2e3d4f5b6` — xem §3a |
| assignee_id | BIGINT | Nhân sự thực hiện; **`0` = chưa cử** | Không FK; tên resolve lúc đọc |
| sort_order | SMALLINT | Thứ tự hiển thị | |

### Bộ mã trạng thái (`report_constants.py`)
`RD_IDLE=0` · `RD_DOING=1` · `RD_REVIEW=2` · `RD_DONE=3` — nhãn ở
`REPORT_DOC_STATUS_LABELS`. Bản TypeScript **gõ tay** ở `types/survey-request-report.ts`
(`gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI — cùng cảnh `hr/types/leave.ts`).

> **Vì sao SMALLINT chứ không chuỗi:** cột mang nghĩa trạng thái là bảng MỚI nên theo
> R2/QĐ-11. Không lẫn với `SurveyRequest.status` (mã chuỗi `draft|submitted|…` —
> ngoại lệ lịch sử QĐ-9 của thu mua).

### 3a. Hạn hồ sơ & nhân sự thực hiện

Phần mở rộng của hồ sơ (migration `a1c2e3d4f5b6`, revises `7816572fed52`):

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `start_date` | DATE NULL | Ngày bắt đầu thực hiện. `NULL`/`''` = chưa đặt |
| `expires_at` | DATE NULL | Ngày hết hiệu lực / hạn. Dùng để cảnh báo hồ sơ quá hạn |
| `assignee_id` | BIGINT NOT NULL, server_default `0` | Nhân sự thực hiện (`tab_employee.id`); `0` = chưa cử |

Quy ước & bẫy:

- **Ô ngày đi bằng CHUỖI `yyyy-mm-dd`** qua API (không phải object date), rỗng = chưa
  đặt. Schema kiểm định dạng bằng `date.fromisoformat` → sai định dạng trả **422**
  (cùng họ bẫy duoc-CR-316); service quy đổi chuỗi ↔ `date` bằng `_to_date`.
- **`''` vs `None` trên PATCH khác nghĩa:** `None` = không gửi (bỏ qua); `''` = **xóa**
  ngày đã đặt. Vòng gán generic của `update_doc` bỏ mọi `None` nên **không phân biệt
  được** — hai ô ngày phải xử lý **tách riêng** trước vòng đó (`changes.pop`).
- **`assignee_id` không FK, không xóa lây:** xóa nhân sự không xóa hồ sơ; `get_report_payload`
  **resolve tên một lượt** (`assignee_name`, tránh N+1), id chết (nhân sự đã xóa) ra
  chuỗi rỗng → FE hiện «Chưa cử».
- FE: `nearestExpiry` (helpers) lấy **ngày hết hiệu lực sớm nhất trong nhóm hồ sơ
  CHƯA xong** — hồ sơ quá hạn nổi lên đầu; hạn của hồ sơ đã xong không tính. So sánh
  chuỗi `yyyy-mm-dd` trực tiếp (thứ tự bảng chữ cái trùng thứ tự thời gian).
- **Phần đang hoàn thiện (12/09/2026):** ô nhập trên hộp thoại hồ sơ (chọn ngày +
  chọn nhân sự) và cách hiển thị ngày/người trên dòng hồ sơ — dữ liệu và API đã sẵn.

## 4. API

Tiền tố: `/api/survey-requests/{sid}/report`. Mọi mutation trả về **nguyên khối báo
cáo mới** (`{items, phases, docs}`) để FE thay cache một lượt.

| Method | Path | Quyền | Việc |
|---|---|---|---|
| GET | `` | `read` | Toàn khối của phiếu |
| POST | `/init` | `process` | Khởi tạo khung mẫu (idempotent) |
| POST | `/items` | `process` | Thêm nút dòng hàng |
| PATCH | `/items/{item_id}` | `process` | Đổi tên nút |
| DELETE | `/items/{item_id}` | `process` | Xóa nút (hồ sơ về Chung) |
| POST | `/phases` | `process` | Thêm giai đoạn |
| PATCH | `/phases/{phase_id}` | `process` | Sửa giai đoạn |
| DELETE | `/phases/{phase_id}` | `process` | Xóa giai đoạn (chặn nếu còn hồ sơ) |
| POST | `/docs` | `process` | Thêm hồ sơ |
| PATCH | `/docs/{doc_id}` | `process` | Sửa hồ sơ (gửi trường nào đổi trường đó; nút ✓ chỉ gửi `status`) |
| DELETE | `/docs/{doc_id}` | `process` | Xóa hồ sơ (gỡ khỏi tiên quyết hồ sơ khác) |

`POST/PATCH /docs` còn nhận `start_date`, `expires_at` (chuỗi `yyyy-mm-dd` | `''`),
`assignee_id` (id nhân sự | `0`) — xem [§3a](#3a-hạn-hồ-sơ--nhân-sự-thực-hiện).

**Ràng buộc schema** (`report_schema.py`) — `max_length` khớp **đúng** `String(n)` ở
model để lỗi ra **422 chứ không 500** (duoc-CR-316): `title≤255` · `file_note≤500` ·
`description≤4000` · `name` item ≤100 / phase ≤255. `status` chỉ nhận 0..3;
`depends` ≤30 phần tử; ô ngày kiểm `date.fromisoformat`. `ReportDocPatch` để trường
nào `None` thì không đụng (riêng hai ô ngày: `''` = xóa, `None` = bỏ qua).

## 5. Phân quyền — chốt thật ở đâu

Hai lớp, tái dùng khóa `survey_request`:

- **ĐỌC**: `require(survey_request, read)` + `_in_scope(db, sid, user, "read")` (nạp
  phiếu cha theo phạm vi; ngoài phạm vi → 404, kể cả gõ id vào API).
- **GHI**: `require(survey_request, process)`. `process` là **cờ suy ra** «là NS Thu
  mua», **không** phải action có trong grant → phạm vi vẫn phải hỏi theo `read` bằng
  `_in_scope(..., "read")` (`_writable_sr`). Hỏi `scope_condition("process")` thì
  không grant nào có và cổng đóng sạch.

Ba bảng con **cố ý không có khóa riêng** — chúng không có màn hình riêng, và phạm vi
của chúng chỉ là một cột `survey_request_id`, không diễn đạt được bằng khuôn một-cột
của `apply_scope`. Chốt là **hai lớp của phiếu CHA**.

Audit ghi lên **phiếu cha** (`record(..., "survey_request", sr.id, "update", "Báo cáo: …")`)
vì khối không có mã chứng từ riêng.

## 6. Nghiệp vụ trong service (`report_service.py`)

Mọi hàm ghi **không commit** (controller commit một lượt qua `record`). Các điểm chốt:

- `get_report_payload` — trả `{items, phases, docs}`; `depends` **lọc id chết** trước
  khi ra FE (id hồ sơ tiên quyết đã bị xóa mà lọt ra thì tầng hiển thị đếm nó là
  «chưa xong» → hồ sơ khóa vĩnh viễn); resolve `assignee_name` một lượt (xem §3a).
- `create_doc` / `update_doc` — lưu cả `start_date`/`expires_at`/`assignee_id`; hai ô
  ngày xử lý tách để phân biệt «xóa» (`''`) với «bỏ qua» (`None`) — xem §3a.
- `init_report` — idempotent: đã có giai đoạn hoặc nút thì trả `False`, không đụng.
- `delete_item` — chuyển hồ sơ đang gắn về `item_id = 0`.
- `delete_phase` — `count` hồ sơ trong giai đoạn, còn thì `raise 400`.
- `delete_doc` — gỡ `doc_id` khỏi `depends` của mọi hồ sơ khác.
- `check_depends` — khử trùng, chặn tự trỏ mình, chặn tiên quyết chéo phiếu, **dò
  vòng lặp** (DFS trên đồ thị sau khi lưu). Vòng dò có **trần độ sâu**; **chạm trần
  là raise**, không trả về im lặng («dò không thấy» ≠ «không có» — bài học
  `block_manager_cycle`).
- `_next_order` — kèm **trần số dòng** mỗi bảng (item 50 · phase 50 · doc 500) chống
  tràn `sort_order` SMALLINT (duoc-CR-316).

## 7. Frontend

- **Gọi API**: `survey-request-report-api.ts` dùng `apiGet/apiPost/apiPatch/apiDelete`
  (`@/core/api`, đã bóc phong bì `{success,message,data}`).
- **Query**: `use-survey-request-report.ts` — key `queryKeys.procurement.surveyRequestReport(id)`;
  mọi mutation `onSuccess` gọi `setQueryData` với khối trả về (thay cache, **không**
  invalidate → đỡ một lượt GET, màn đổi ngay khi bấm ✓).
- **Logic thuần** (`utils/survey-report-helpers.ts`, có test kề bên):
  - `filterReportDocs` — sentinel «Tất cả» là **`-1`** (0 là id thật của «Chung»).
  - `isReportDocLocked` / `pendingDepends` — tính khóa; hồ sơ đã xong không khóa ngược.
  - `matchReportDoc` — khớp **theo từng từ**, chuẩn hóa **NFKD** (không NFD — NFD
    không tách được ký tự ₃ của «KNO₃»).
  - `currentReportPhaseId` / `trackingMarkers` — điểm nháy khung Tiến trình.
  - `nearestExpiry` — ngày hết hiệu lực sớm nhất trong nhóm hồ sơ chưa xong (§3a).
- **UI**: `SurveyReportCard` giữ state lọc/tìm/thu-gọn; hộp thoại theo **case C-01**
  (chặn Esc/click ngoài, hỏi khi form dirty), reset bằng `useHasChanged` trong render
  (không `useEffect` → tránh warning `react-hooks`), chống bấm đúp bằng `useSingleFlight`.
  Ô chỉ-xem không dùng `<Input disabled>`; icon từ `lucide-react`, không emoji.

## 8. Kiểm thử

- Backend: `test/backend/test_bao_cao_thuc_hien_ycbg.py` (10 ca) — init idempotent,
  ba đường xóa dọn hậu quả, chặn vòng/chéo phiếu, lọc id chết, cô lập theo phiếu,
  **ràng buộc ở tầng schema** (SQLite không ép `VARCHAR` nên phải kiểm `ValidationError`),
  trần số dòng.
- Frontend: `utils/survey-report-helpers.test.ts` — lọc/khóa/tìm-không-dấu/tracking.
- Cổng `docker compose exec erp npm run check` xanh (typecheck 0 lỗi · lint 0 lỗi ·
  test toàn bộ xanh).

## 9. Migration & triển khai

- `7816572fed52` tạo 3 bảng + index. ⚠️ Bản autogenerate gốc kéo theo hàng trăm lệnh
  drift dev-DB không liên quan — **đã cắt tay** còn đúng 3 bảng; **đừng autogenerate
  lại rồi giữ nguyên**.
- `a1c2e3d4f5b6` (revises `7816572fed52`) thêm 3 cột `start_date` · `expires_at` ·
  `assignee_id` vào `tab_survey_request_report_doc` — cũng **viết tay** vì lý do drift
  trên. `assignee_id` NOT NULL + server_default `0` cho hồ sơ cũ.
- Trên hệ đang chạy: vai trò cũ **có sẵn** `process` của `survey_request` thì thao tác
  được ngay (không cần seed mới, vì không thêm entity).

## 10. Việc còn lại

1. Hoàn thiện **ô nhập ngày + chọn nhân sự** trên hộp thoại hồ sơ và cách hiển thị
   ngày/người thực hiện trên dòng (dữ liệu, API, migration của §3a đã sẵn).
2. **Nhắc hạn** chủ động (thông báo) dựa trên `expires_at` — hiện chỉ có cảnh báo bị
   động qua `nearestExpiry`.
3. Nối kho `attachment` thật cho ô tệp (thay chuỗi tự do bằng upload).
4. Nhớ trạng thái gấp/mở giai đoạn theo người dùng (`localStorage`).
5. Cấp số CR + ghi `change-log.md` + commit — chờ chốt prefix CR.
