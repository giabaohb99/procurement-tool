# 16 — QUẢN LÝ IMPORT/EXPORT (PHÂN HỆ QUẢN TRỊ `/system`)

**Bản 1.0 — 25/08/2026.**

> **Vì sao viết.** Yêu cầu ngày 25/08/2026: dựng màn **Quản lý Import và Export** trong phân hệ
> Quản trị `/system`; ai có quyền import/export thì màn danh sách tương ứng hiện nút đó; **mọi lần
> import/export đều được ghi nhận** ở màn quản lý; thêm **import thử** và **hoàn tác (revert) đúng
> lần import**. Tài liệu này đối chiếu mã nguồn đang chạy, chốt kiến trúc, liệt kê màn hình kèm
> input/output, và chia đợt nghiệm thu.
>
> Đây là bản thực thi chi tiết của **MC-6 / Đợt Đ-13** trong [`13-ke-hoach-man-con-lai-v2.md`](./13-ke-hoach-man-con-lai-v2.md)
> — đợt đó trước ghi "Hoãn", nay mở lại và tách nhỏ thành Đ-13a…Đ-13e ở §9.

---

## 0. Bốn con số đọc trước

1. **Backend import KHÔNG phải viết lại từ đầu.** Module `import_tool` đã có sẵn khung batch đầy đủ
   cho **2 đối tượng** (Khảo sát, Đơn mua hàng): dry-run, revert, chạy nền Celery, ghi log từng dòng.
2. **Hai cơ chế import đang chạy song song và lệch nhau** — đây là gốc của mọi việc phải làm (xem §1
   và giải thích KT-1 ở §4.1).
3. **Export hiện KHÔNG để lại dấu vết** ở bất kỳ đâu — phần "ghi nhận export" là làm mới hoàn toàn.
4. **Không màn nào của việc này đã có ở `frontend-v2`** — chỉ một dòng chữ "Sắp có" ở
   `system-dashboard-page.tsx`.

---

## 1. Hiện trạng đã khảo sát (đo ngày 25/08/2026)

| Mảng | Đường dẫn mã nguồn | Đã có | Thiếu |
|---|---|---|---|
| **Import batch** | `backend/app/modules/import_tool/` | 3 bảng `ImportBatch·ImportLog·ImportChange`; dry-run (`mode=0`); revert (`POST /api/imports/{id}/revert`); Celery `run_import`; gác quyền entity `import` (read/create/delete) | Chỉ chạy cho **Khảo sát** + **Đơn mua hàng** (hai importer viết tay: `survey_import.py`, `po_import.py`). Chưa có màn v2 |
| **Import CSV danh mục** | `backend/app/core/crud.py:129` (`POST /{prefix}/import/csv`) | Đồng bộ; cho 8 danh mục (company, supplier, product, employee, warehouse, unit, item_group, department); gác bằng `write` | **Không** batch, **không** dry-run, **không** revert, **không** log — ghi thẳng, không dấu vết |
| **Export CSV** | `crud.py:109` + 4 controller thủ công (employee, product, supplier, department) | Gác bằng **`read`** | Không log |
| **Export XLSX** | `purchase_order·purchase_request·survey_request·report·document/export.py` | Gác bằng **`export`** | Không log |
| **Phân quyền** | `backend/app/core/permissions.py` | Có action `export`; có **entity** `import` | **Không có action `import`**; export gác không nhất quán (`read` vs `export`) |
| **Màn cũ** | `frontend/src/pages/ImportBatches.tsx` (415d) · `ImportBatchDetail.tsx` (141d) | Đầy đủ danh sách + chi tiết + revert | Chưa port v2 |
| **frontend-v2** | `modules/system/` | — | Chưa có route/page/api/hook nào cho import/export |

---

## 2. Bảy quyết định đã chốt (25/08/2026)

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-I1 (KT-1)** | **Gộp mọi import vào một khung batch** `import_tool`. Bỏ dần `/import/csv` đồng bộ; mọi entity import qua registry adapter | Không gộp thì màn quản lý chỉ thấy import Khảo sát/ĐMH, còn nhập danh mục vẫn vô hình, không thử được, không revert được — trái yêu cầu. Giải thích đầy đủ §4.1 |
| **QĐ-I2 (KT-2)** | **Thêm action `import`** vào `ACTIONS` (8 → 9). Export dùng lại action `export` đã có | Bạn nói "quyền import **và** export" tách bạch. Dùng `write` nghĩa là ai sửa được là nhập hàng loạt được — khó kiểm soát |
| **QĐ-I3 (KT-3)** | Một khái niệm duy nhất **"thử → xem → commit"** cho mọi import (thay vì upload lại file như bản cũ) | Người dùng học một luồng, không phải hai. §4.3 |
| **QĐ-I4** | **Chuẩn hoá export CSV từ `read` → `export`** | Bạn đồng ý siết. Sau đổi, ai chỉ có `read` sẽ **không** còn nút xuất — đúng ý "chỉ người có quyền export mới xuất" |
| **QĐ-I5** | **Ghi nhận cả Import và Export**; export lưu **metadata**, không lưu file | Đủ để truy vết ai xuất gì, không phình dung lượng |
| **QĐ-I6** | Màn Import và Export là **2 mục nav riêng** dưới nhóm "Nhập / Xuất dữ liệu" của `/system` | Import phức tạp hơn nhiều, nhồi chung tab sẽ rối |
| **QĐ-I7** | **Revert = hoàn tác đúng batch** (dùng lại `ImportChange`), không snapshot toàn bảng | Chính xác, phạm vi hẹp, không đè mất thay đổi xen giữa. §8 |

### 2.1 Ba quyết định về Export (chốt 25/08/2026, khách)

| | Quyết định | Vì sao |
|---|---|---|
| **QĐ-E1** | **Phạm vi Export đợt đầu = tất cả bảng danh mục** (Nhân sự, Phòng ban, Công ty, NCC, Sản phẩm, Kho, ĐVT, Phân loại, Hợp đồng) qua lớp CRUD chung | Backend hầu hết đã có endpoint; gắn nút một lần dùng nhiều chỗ |
| **QĐ-E2** | **Xuất cả CSV và XLSX** — cho người dùng chọn | CSV nhẹ + khớp đường nhập ngược ở Import; XLSX đẹp cho người dùng cuối |
| **QĐ-E3** | **Thứ tự: nút Xuất trước (Pha A) → log + màn quản lý (Pha B) → chuẩn hoá quyền + vá scope (Pha C)** | Ra kết quả dùng được ngay; log và siết quyền làm đợt kế |

---

## 3. Danh mục được phép Import/Export hàng loạt

Cột **Ưu tiên**: `P0` = bạn yêu cầu trực tiếp · `P1` = danh mục nền nên có · `P2` = làm sau.
Cột **Khoá trùng** = trường dùng để phân biệt "tạo mới" hay "cập nhật" khi import.

### 3.1 Danh mục nền (master data) — Import + Export

> **Tình trạng Import (25/08/2026, CR-170):** ✅ = đã mở nhập hàng loạt qua batch (thử/ghi/hoàn tác +
> file mẫu). Cột *Export* trong bảng là **đề xuất** — phần Export (`ExportLog` + màn) thuộc Đ-13b, chưa làm.

| Ưu tiên | Entity | Nhãn | Import | Export | Khoá trùng | Ghi chú / bẫy |
|---|---|---|---|---|---|---|
| **P0** | `company` | Công ty | ✅ | ✓ | `code` / `tax_code` | Cây pháp nhân: `parent` map theo `code` |
| **P0** | `department` | Phòng ban | ✅ | ✓ | `code` | `parent` + `company` map theo `code`; kiêm nhiệm không nằm ở đây |
| **P0** | `employee` | Nhân sự | ✅ | ✓ | `code` (mã NV) | Map `company`/`department` theo `code`; **không** tạo tài khoản đăng nhập qua import |
| P1 | `supplier` | Nhà cung cấp | ✓ | ✓ | `code` / `tax_code` | `vat` lưu **tỷ lệ** 0.08 không phải 8 (CR-058) |
| P1 | `product` | Sản phẩm / VTBB | ✓ | ✓ | `product_code` | ⚠️ **CẤM đổi/tái dùng `product_code`** (D-025). Import chỉ tạo mới hoặc sửa thuộc tính, không đụng mã |
| P1 | `warehouse` | Kho | ✓ | ✓ | `code` | — |
| P1 | `unit` | Đơn vị tính | ✓ | ✓ | `code` | Dùng chung toàn tập đoàn — không gắn đơn vị sở hữu |
| P1 | `item_group` | Phân loại VTBB/NL | ✓ | ✓ | `code` | Dùng chung toàn tập đoàn |
| P2 | `brand` | Thương hiệu | ✓ | ✓ | `code` | Ít dùng |
| P2 | `contract` | Hợp đồng | ✓ | ✓ | `code` | `contract_type` = mã tiếng Anh (CR-118); **tệp đính kèm không qua import** |

### 3.2 Dữ liệu nghiệp vụ / lịch sử — Import dữ liệu cũ + Export

| Ưu tiên | Entity | Nhãn | Import | Export | Ghi chú |
|---|---|---|---|---|---|
| **P0** | `survey` | Phiếu khảo sát | ✓ *(đã có)* | ✓ | Importer `survey_import.py` sẵn — chỉ dựng màn |
| **P0** | `purchase_order` | Đơn mua hàng | ✓ *(đã có)* | ✓ *(xlsx đã có)* | Importer `po_import.py` sẵn — revert đã dọn cả GR/tồn/công nợ |
| P1 | `purchase_request` | Yêu cầu mua hàng | ✓ *(lịch sử)* | ✓ *(xlsx đã có)* | Import số liệu cũ để lên báo cáo |
| P2 | `survey_request` | Yêu cầu báo giá | — | ✓ *(xlsx đã có)* | Sinh từ nghiệp vụ, ít cần import |

### 3.3 Số dư đầu kỳ (đặc thù — import một lần lúc khai trương)

| Ưu tiên | Entity | Nhãn | Import | Export | Khoá trùng |
|---|---|---|---|---|---|
| P1 | `inventory` | Tồn kho đầu kỳ | ✓ | ✓ | `product_code` + `warehouse` |
| P2 | `payable` | Công nợ đầu kỳ | ✓ | ✓ | `supplier` + số chứng từ |

### 3.4 KHÔNG cho import hàng loạt (chỉ export khi cần)

`user`, `role` *(bảo mật — tạo tài khoản là hành vi có kiểm soát)* · `goods_receipt`, `payment`,
`payment_request` *(sinh từ nghiệp vụ, không nhập tay hàng loạt)* · `setting`, `backup`, `audit`
*(quản trị hệ thống)*.

> **Phạm vi đợt đầu (Đ-13d):** làm trước **P0 + P1** ở §3.1 và §3.2. P2 và số dư đầu kỳ để đợt sau,
> nhưng khung registry ở §6 phải mở sẵn để thêm một entity chỉ tốn một adapter.

---

## 4. Kiến trúc đích — ba quyết định giải thích rõ

### 4.1 KT-1 — Vì sao phải gộp về một khung batch *(giải thích đầy đủ)*

**Hôm nay có HAI cơ chế import khác hẳn nhau:**

**Cơ chế A — `import_tool` (batch).** Upload file → tạo một *batch* → Celery chạy nền → ghi log từng
dòng → cập nhật ô đếm (tạo/sửa/bỏ qua/lỗi) → cho **chạy thử** (không ghi) và **hoàn tác** (revert).
Mọi lần chạy để lại một bản ghi tra cứu được. **Nhưng chỉ có 2 đối tượng** dùng nó: Khảo sát và Đơn
mua hàng, và mỗi cái là **một hàm viết tay riêng** (`survey_import.py` 469 dòng, `po_import.py` 372
dòng).

**Cơ chế B — `/import/csv` (đồng bộ).** Sinh tự động bởi `make_crud_router` cho 8 danh mục. Upload
CSV → **ghi thẳng vào bảng thật ngay trong request** → trả về một câu thông báo → xong. **Không** tạo
batch, **không** log, **không** chạy thử, **không** hoàn tác, **không** hiện ở màn quản lý nào.

**Hệ quả nếu để nguyên:** một người nhập 500 nhân sự bằng cơ chế B thì — ghi tức thì, sai cũng ghi,
không thử trước được, không undo được, và **màn "Quản lý Import" không bao giờ thấy lần nhập đó**.
Ba yêu cầu cốt lõi của bạn — *(1) mọi action được ghi nhận, (2) import thử, (3) revert* — **không thể
đạt** cho nhóm danh mục chừng nào chúng còn chạy cơ chế B.

**KT-1 = xoá cơ chế B, đưa mọi import chạy qua cơ chế A đã tổng quát hoá.** Cụ thể biến `import_tool`
từ "2 importer viết cứng" thành **"một registry các importer"**: mỗi entity đăng ký một *adapter* nhỏ
khai:

```
IMPORT_ADAPTERS["employee"] = ImportAdapter(
    columns   = [...],                 # cột file → trường model, thứ tự, bắt buộc
    dedupe_key= "code",                # khoá trùng để quyết tạo/sửa
    validate  = fn(row) -> [lỗi...],   # kiểm định từng dòng
    apply     = fn(db, row, existing), # tạo/sửa 1 bản ghi
    delete    = fn(db, target_id),     # dùng cho revert dòng was_new
    snapshot  = fn(db, target_id),     # chụp trước khi sửa, dùng cho revert
)
```

Thân khung (staging, dry-run, commit, revert, log, Celery, quyền) **viết một lần, dùng chung**. Thêm
một danh mục import mới sau này = **thêm một adapter**, không đụng khung. Hai importer cũ (survey/po)
gói lại thành hai adapter đặc biệt (chúng có nhiều sheet + hiệu ứng phụ nên adapter phức tạp hơn, giữ
nguyên logic hiện có).

> **Đường lui.** Giữ `/import/csv` cũ **một thời gian** như wrapper mỏng: nhận file rồi tạo batch chế
> độ Ghi, để script/tài liệu cũ không gãy. Cắt hẳn khi màn mới chạy ổn (ghi mốc trong change-log).

### 4.2 KT-2 — Thêm action `import`, export dùng lại `export`

- `core/permissions.py`: `ACTIONS` thêm `"import"` → **9 action**
  (`read·create·write·delete·approve·cancel·print·export·import`), nhãn "Nhập". Cập nhật `ACTION_LABELS`.
- `frontend-v2/src/core/authorization/permission-types.ts`: thêm `'import'` vào mảng `ACTIONS`.
- `scripts/gen_status_ts.py` / ma trận phân quyền UI: cột mới hiện ra tự nhiên.
- **Seed:** cấp `import` cho các vai trò đang có `write` trên danh mục tương ứng, và cho `pur_admin`
  toàn bộ. Đặt cùng scope với `write` của entity đó. ⚠️ **Prod không tự đổi** — cần
  `SEED_FORCE_SYNC=true` một lần (xem CLAUDE.md), hoặc gán tay trên UI.
- **Không đụng** entity `import` cũ (màn nạp dữ liệu lịch sử): nó vẫn là entity gác cho *màn quản lý*
  `/system/imports`. Phân biệt: **entity `import`** = quyền vào *màn quản lý*; **action `import` trên
  entity X** = quyền *bấm nút Nhập ở màn của X*.

### 4.3 KT-3 — Một khái niệm "thử → xem → commit"

Bản cũ: chạy thử (dry-run) và ghi thật là **hai lần upload file khác nhau**. Thiết kế mới **giữ file,
chỉ đổi bước**:

```
Upload  ─▶  [THỬ] validate + ghi bảng tạm (staging)  ─▶  batch = "Chờ commit"
                                                          │
                       xem preview + danh sách lỗi ◀──────┤
                                                          ▼
                                     ┌──────────────────────────────┐
                              Commit │ ghi bảng thật + ImportChange  │─▶ "Xong"
                                Huỷ  │ xoá staging                   │─▶ "Đã huỷ"
                                     └──────────────────────────────┘
```

- Người dùng luôn **thử trước, xem kết quả, rồi mới quyết** — không sợ ghi nhầm.
- Muốn "ghi luôn không cần xem" thì vẫn cho chọn chế độ **Ghi** ngay lúc upload (bỏ qua bước xem) —
  giữ tốc độ cho người quen việc.
- Trạng thái batch mở rộng: `0 Chờ · 1 Đang chạy · 2 Xong · 3 Lỗi · 4 Đã hoàn tác · 5 Chờ commit ·
  6 Đã huỷ`.

---

## 5. Màn hình cần dựng (frontend-v2)

Thêm vào `modules/system/routes.tsx` một nhóm nav **"Nhập / Xuất dữ liệu"** với 2 mục.
`appRoutes.system` thêm: `imports: '/system/imports'`, `importDetail: (id) => '/system/imports/${id}'`,
`exports: '/system/exports'`.

### 5.1 Quản lý Import — danh sách · `/system/imports`

Port `ImportBatches.tsx` sang `DataTable` (đọc `docs/ui/table.md`), gác entity `import` (read).

| | |
|---|---|
| **Input — bộ lọc** | `module` (đối tượng), `status` (Chờ/Đang chạy/Xong/Lỗi/Đã hoàn tác/**Chờ commit**/Đã huỷ), `mode` (Thử/Ghi), `date_from·date_to`, `created_by_name`, `filename` |
| **Nút toolbar** | **"Nhập dữ liệu"** — mở dialog upload; hiện khi có bất kỳ entity nào người dùng có `import` |
| **Cột** | # · Thời gian · Người nhập · Đối tượng · Tên file · Chế độ · Trạng thái · Tạo · Cập nhật · Bỏ qua · Cảnh báo · Rà soát · Lỗi |
| **Hành vi** | Auto-poll 4s khi có batch `status ≤ 1`; click dòng → chi tiết |
| **Output** | `GET /api/imports` → `{items[], total, creators[]}` |

**Dialog upload:** chọn **Đối tượng** (dropdown động từ registry, chỉ hiện entity người dùng có
quyền `import`) · **Chế độ** (Thử / Ghi) · kéo-thả file (`.xlsx`/`.csv`) · nút **"Tải file mẫu"**
(`GET /api/imports/template?module=<entity>`) · hộp ghi chú theo chế độ. Gửi:
`POST /api/imports` FormData `{file, module, mode}`.

### 5.2 Quản lý Import — chi tiết · `/system/imports/:id`

Port `ImportBatchDetail.tsx`, **bổ sung khối staging**.

| | |
|---|---|
| **Khối thông tin** | Người nhập · Bắt đầu · Kết thúc · Chế độ · Tên file + 7 ô thống kê |
| **Khối STAGING** *(mới)* | Khi `status = Chờ commit`: bảng preview từng dòng **Tạo / Sửa / Bỏ qua** (đọc `GET /api/imports/{id}/staging`). Nút **"Ghi thật (Commit)"** + **"Huỷ bản thử"** |
| **Tabs log** | Tất cả / Lỗi / Cần rà soát / Cảnh báo — cột Sheet·Dòng·Loại·Phân loại·Thông báo·Tham chiếu(→target_code) |
| **Nút** | **"Hoàn tác"** — hiện khi `status=Xong & mode=Ghi & can('import','delete')` · **"Tải file"** gốc |
| **Output/API** | `GET /api/imports/{id}` · `/logs?level=` · `/staging` · `/file` · `POST /{id}/commit` · `POST /{id}/revert` |

### 5.3 Quản lý Export — danh sách · `/system/exports` *(mới hoàn toàn)*

Gác entity `export`… — lưu ý: **không có entity `export`**; màn này gác bằng entity `import` (read)
hoặc `setting` (read) — chọn **`import`** để hai màn cùng một cửa quản trị. Nguồn dữ liệu: bảng
`ExportLog` mới (§6).

| | |
|---|---|
| **Input — bộ lọc** | `entity` (đối tượng xuất), `format` (csv/xlsx), `date_from·date_to`, `created_by_name` |
| **Cột** | # · Thời gian · Người xuất · Đối tượng · Định dạng · Số dòng · Bộ lọc áp dụng (tóm tắt) · Tên file |
| **Nút** | Chỉ đọc (export không revert). Không tải lại file (chỉ lưu metadata) |
| **Output/API** | `GET /api/exports` → `{items[], total, creators[]}` |

### 5.4 Nút Nhập/Xuất trên các màn danh sách *(không phải màn mới)*

Gắn qua `renderToolbarExtra` của `CrudConfig` (đã có sẵn), hoặc thêm cờ `bulkImport?/bulkExport?`
vào `CrudConfig` để lớp `CrudListPage` tự vẽ nút:

- **"Xuất"** — hiện khi `can(entity,'export')` → gọi endpoint export của entity → BE ghi `ExportLog`.
- **"Nhập"** — hiện khi `can(entity,'import')` → mở dialog upload (dùng lại dialog ở 5.1, khoá sẵn
  `module = entity`) → tạo batch → điều hướng sang `/system/imports/{id}` để thử/commit.

---

## 6. Backend — thêm/sửa

**A. Bảng `tab_export_log`** — module mới `app/modules/export_log/`:
`id · entity(VARCHAR30) · format(VARCHAR10) · row_count(INT) · filter_summary(TEXT/JSON) ·
filename(VARCHAR255) · file_size(INT) · created_at · created_by` (+ audit mixin). Đăng ký ở
`all_models.py`.

**B. Helper log export + chuẩn hoá quyền:**
- Hàm `record_export(db, user, entity, fmt, rows, filters, filename)` trong `core/export_log.py`.
- Gọi ở **mọi** endpoint export: `crud.py:export_csv`, 4 controller CSV thủ công, các `/export/xlsx`,
  `report/export`, `document/export/docx`.
- **Đổi `crud.py:115` và 4 controller CSV: `require(entity,'read')` → `require(entity,'export')`** (QĐ-I4).

**C. Khung import tổng quát (KT-1):**
- `import_tool/registry.py`: kiểu `ImportAdapter` + dict `IMPORT_ADAPTERS`.
- `ImportModule` (enum) mở rộng: giữ `1=SURVEY, 2=PURCHASE_ORDER`, thêm `10=COMPANY, 11=DEPARTMENT,
  12=EMPLOYEE, 13=SUPPLIER, 14=PRODUCT, 15=WAREHOUSE, 16=UNIT, 17=ITEM_GROUP, …` (chừa số cho P2).
- Bảng **`tab_import_staging`**: `batch_id(index) · sheet · row_no · action(SMALLINT create/update/skip)
  · target_id(BIGINT null) · parsed(TEXT JSON)`.
- `ImportStatus` thêm `5=PENDING_COMMIT, 6=CANCELLED`.
- Wrap `survey_import`/`po_import` thành 2 adapter đặc biệt; viết adapter cho P0/P1 ở §3.

**D. Endpoint mới (prefix `/api/imports`):**
- `GET /{id}/staging` — đọc bảng tạm để preview.
- `POST /{id}/commit` — promote staging → bảng thật + ghi `ImportChange` → `Xong`.
- `POST /{id}/cancel` — xoá staging → `Đã huỷ`.
- `GET /template?module=<entity>` — tải `.xlsx` mẫu (cột từ adapter).
- `GET /api/exports` — danh sách `ExportLog`.

**E. Phân quyền (KT-2):** như §4.2.

**F. Migration:** một revision cho `tab_export_log` + `tab_import_staging` + cột enum mở rộng
(chỉ thêm cột/bảng, không sửa cột cũ — theo "chỉ thêm không sửa"). Autogenerate xong **review tay**.

---

## 7. Import thử (staging) — chi tiết luồng

1. Upload chế độ **Thử** → batch `Chờ` → Celery `run_import(apply=False)`.
2. Worker validate từng dòng bằng `adapter.validate`, tính hành động (create/update/skip theo
   `dedupe_key`), **ghi `tab_import_staging` + `ImportLog`**, cập nhật ô đếm → batch **`Chờ commit`**.
   *(Khác bản cũ: bản cũ rollback nên không giữ preview; nay giữ trong bảng tạm.)*
3. Người dùng mở chi tiết → xem preview (staging) + lỗi (log).
4. **Commit** (`POST /{id}/commit`): worker đọc staging, gọi `adapter.apply`, ghi `ImportChange`
   (snapshot trước-sau), xoá staging, batch → **`Xong`**. Hoặc **Huỷ** → xoá staging → **`Đã huỷ`**.
5. Chọn thẳng chế độ **Ghi** lúc upload = gộp bước 2+4, bỏ qua xem.

**Điều kiện đủ:** thử một file có dòng đúng + dòng trùng + dòng thiếu trường → preview phân đúng
Tạo/Sửa/Bỏ qua, log chỉ ra đúng dòng lỗi, và **bảng thật không đổi một dòng nào** cho tới khi Commit.

---

## 8. Revert — chi tiết (QĐ-I7)

Dùng lại `tab_import_change` đã có:
- Lúc Commit/Ghi, mỗi dòng đụng tới → lưu `was_new=1` (batch tạo) hoặc `snapshot` (JSON trước khi sửa).
- `POST /{id}/revert`: `was_new` → `adapter.delete`; dòng cũ → khôi phục từ `snapshot`
  (`adapter.apply` với giá trị cũ) → batch **`Đã hoàn tác`**.
- **Chốt chặn mới:** trước khi revert, so `updated_at` bản ghi với `finished_at` của batch — nếu bản
  ghi **đã bị sửa sau import** thì cảnh báo và cho người dùng chọn *bỏ qua dòng đó* thay vì đè mù.
- Chỉ revert batch `mode=Ghi & status=Xong`, có `ImportChange`.

**Điều kiện đủ:** ghi một batch tạo 3 + sửa 2 → revert → 3 bản ghi mới biến mất, 2 bản ghi cũ về đúng
giá trị trước import, batch chuyển `Đã hoàn tác`; với `purchase_order` kiểm cả GR/tồn/công nợ được dọn.

---

## 9. Chia đợt — Đ-13a … Đ-13e

Bám luật nhận việc §3.1 của [`13-...md`](./13-ke-hoach-man-con-lai-v2.md): ghi tên vào cột *Ai làm*,
đổi *Đang làm*, push riêng dòng đó trước khi gõ mã. Số CR cấp ở `change-log.md`.

| Đợt | Việc | Ngày công | Phụ thuộc | Điều kiện đủ (tóm tắt) |
|---|---|---|---|---|
| **Đ-13a** ✅ | Port Màn Import list+detail (Khảo sát + ĐMH) sang v2 — *backend đã đủ*, thuần FE | 2 – 3 | — | **XONG (25/08/2026)** — `/system/imports` + `/system/imports/:id`, upload thử/ghi + revert + tải file; nav "Quản lý Import" trong Quản trị; link thông báo `/import-batches/{id}` dịch sang v2. Cổng `npm run check` xanh (typecheck 0 · lint 23 cảnh báo baseline · 615 test). Smoke test live OK |
| **Đ-13b** ◐ | Export **tập trung** (đổi hướng CR-172): màn `/system/exports` chọn bảng + định dạng → tải + **ghi nhật ký**; `ExportLog` + registry | 4 – 6 | — | **XONG lõi (CR-171→CR-172)**: module `export_log` + màn `/system/exports` + dialog Xuất (Nhân sự/Phòng ban/Công ty, CSV/XLSX) + nhật ký, đã áp `apply_scope`. Đã **gỡ** nút Xuất per-screen. Còn: thêm bảng vào registry + Pha C vá 3 export viết tay. Chi tiết §9.2 |
| **Đ-13c** | Action `import` + chuẩn hoá export→`export` + seed + permission-types v2 | 1 – 1,5 | — | Ma trận có cột Nhập/Xuất; ai chỉ `read` mất nút xuất CSV |
| **Đ-13d** ◐ | Khung adapter danh mục + template + adapter Công ty/Phòng ban/Nhân sự (§3) | 4 – 6 | 13a | **XONG phần 1 (25/08/2026, CR-170)** — 3 danh mục nền nhập qua batch: **thử (rollback) → ghi → hoàn tác đúng batch** + file mẫu. Còn: **staging thử→xem→commit (KT-3)**, các danh mục P1/P2 còn lại, gác per-entity (chờ Đ-13c). Chi tiết §9.1 |
| **Đ-13e** | Nút Nhập/Xuất trên các `CrudListPage` + wiring dialog | 1 – 2 | 13a-d | Màn danh mục hiện nút theo `can('import'/'export')`, dẫn về batch |
| | **Cộng** | **10 – 15,5** | | Không phải viết lại backend import lõi |

Nhóm để hẹn: **13a+13b độc lập, làm song song được** (một FE-import, một Export/BE). 13c là điều kiện
của 13d. 13e đứng cuối vì cần cả registry.

### 9.1 Đ-13d phần 1 — đã làm gì (25/08/2026, CR-170)

**Backend** — `import_tool/catalog_import.py` (mới): mỗi thực thể một *adapter* khai `header cột →
attr · kind (str/int/bool/ref) · required · ref (company/department/employee/self)`. Hàm `run()`
dùng lại đúng khuôn `survey_import`: tích luỹ log/changes/counts trong bộ nhớ → `apply` thì
`db.commit()`, `dry-run` thì `db.rollback()` → `_persist` ghi batch + log (và changes NẾU apply) ở
transaction riêng, **nên bản chạy thử vẫn còn log xem trước**. Revert danh mục: `was_new` → xoá;
bản cũ → khôi phục cột từ snapshot. Enum `ImportModule` +`COMPANY/DEPARTMENT/EMPLOYEE`; dispatch ở
`tasks.run_import` + `service.revert_batch`; endpoint file mẫu `GET /api/imports/template?module=`
đặt **trước** `/{bid}` để "template" không bị bắt làm `bid`.

**Frontend** — thêm 3 đối tượng vào `import-meta.ts` (Công ty/Phòng ban/Nhân sự lên đầu, mặc định
Công ty), nút **"Tải file mẫu"** trong dialog cho danh mục có `hasTemplate`.

**Bộ cột file mẫu:** Công ty (mã*·tên*·viết tắt·mã hiệu VB·cấp·MST·địa chỉ·email HĐ·công ty mẹ theo
mã·hoạt động) · Phòng ban (mã*·tên*·mã hiệu VB·loại·công ty theo mã·phòng cấp trên theo mã·trưởng bộ
phận theo mã NV·hoạt động) · Nhân sự (mã NV*·họ tên*·email·điện thoại·công ty theo mã·phòng ban theo
mã·chức vụ·trạng thái·hoạt động).

**Bẫy / giới hạn v1 đã ghi rõ:** tham chiếu (công ty/phòng/NV/cấp trên) resolve theo **mã**, không
thấy → log REVIEW + để trống (không dựng phiếu lỗi); `parent` tự tham chiếu trong cùng file dựa vào
dòng đã flush trước đó nên **xếp cha trước con**; **không** tạo tài khoản đăng nhập, **không** kiêm
nhiệm nhiều phòng, **không** đụng người đại diện pháp luật — mở việc riêng.

**Chưa làm (phần 2 của Đ-13d):** luồng **staging thử→xem→commit (KT-3)** — hiện *thử* và *ghi* là hai
lần chạy (như bản Khảo sát/ĐMH), chưa giữ file để commit; các danh mục P1/P2 còn lại (NCC, sản phẩm,
kho, ĐVT, phân loại, hợp đồng, tồn/công nợ đầu kỳ); gác **per-entity** bằng action `import` (chờ Đ-13c,
nay tạm gác chung bằng entity `import`).

### 9.2 Đ-13b — Xuất dữ liệu TẬP TRUNG + nhật ký (25/08/2026, CR-171 → **đổi hướng CR-172**)

> **Đổi hướng (khách chốt 25/08/2026).** Bản đầu (CR-171) làm **nút Xuất trên từng màn danh mục**.
> Khách yêu cầu **bỏ nút trên các bảng, gom về một màn Xuất tập trung** ở `/system/exports` có
> **nhật ký ghi lại** giống màn Quản lý Import. CR-172 làm theo hướng này; `shared/ui/export-button.tsx`
> per-screen đã **gỡ bỏ**.

**Backend — module mới `export_log/`** (giống `import_tool` nhưng cho xuất):
- `model.ExportLog` (`tab_export_log`, migration `16a85b39ddcf`) — metadata mỗi lần xuất: đối tượng,
  định dạng, số dòng, tên file, dung lượng, người, thời gian *(không lưu nội dung file)*.
- `registry.EXPORT_ADAPTERS` — mỗi bảng khai model + khóa phạm vi + bộ cột (dùng lại `export_xlsx.Col`).
  Đợt đầu: **Nhân sự · Phòng ban · Công ty**; thêm bảng = thêm adapter.
- `service.run_export` — query + **`apply_scope`** + dựng CSV (`utf-8-sig` BOM) hoặc XLSX + **ghi
  `ExportLog`** + trả file. `available_entities` chỉ trả bảng người dùng có quyền `export`.
- `controller`: `GET /api/exports` (nhật ký) · `/entities` (bảng được phép) · `/run?entity=&format=`
  (xuất + tải). Xuất gác `export` trên bảng đích; xem nhật ký cần `export` bất kỳ hoặc `setting` read.

**Frontend** — màn `/system/exports` (`export-list-page.tsx`): bảng nhật ký (# · Thời gian · Người
xuất · Đối tượng · Định dạng · Số dòng · Dung lượng · Tên file) + lọc; nút **"Xuất dữ liệu"** mở
`export-run-dialog.tsx` (chọn **Bảng** = Select + **Định dạng** Excel/CSV → tải + ghi log). Nav
**"Quản lý Export"** trong nhóm *Nhập / Xuất dữ liệu*. **Đã gỡ** nút Xuất khỏi `EmployeeListPage`.

**Trang chi tiết `/system/exports/:id`** *(tham khảo `imports/:id`)* — `export-detail-page.tsx`: header
`Export #id — <đối tượng>` + badge định dạng, nút **Tải file**, và các ô Người xuất · Thời gian · Đối
tượng · Định dạng · Số dòng · Dung lượng · Tên file; click dòng ở danh sách để mở. **Để tải lại đúng
file đã xuất**, `run_export` nay **lưu file lên storage** (StoredFile) và ghi `file_id` vào `ExportLog`
*(migration `16a85b39ddcf` gồm cột `file_id`)*; endpoint `GET /api/exports/{id}` (chi tiết) và
`/{id}/file` (tải, có kiểm quyền).

**Kiểm chứng:** live — chọn bảng + định dạng → tải file + **dòng nhật ký mới hiện ngay** (đối tượng,
số dòng, người xuất); backend `test/backend/test_export_data.py` (**4 ca**: liệt kê bảng theo quyền ·
CSV ghi log + đếm đúng · XLSX file hợp lệ · **scope chặn khi không có grant**); cổng `npm run check`
xanh (620 test).

**Còn giữ từ CR-171** *(không thuộc màn per-screen)*: `employee/controller.py` thêm
`GET /export/xlsx` và **vá `apply_scope` cho export CSV** — lỗ rò phạm vi ở export Nhân sự đã chốt.

**Đồng nhất giao diện (CR-173, 26/08/2026).** Nav đổi tên **«Nhập dữ liệu» / «Xuất dữ liệu»** (bỏ
«Quản lý Import/Export»); hai hộp thoại dùng chung `module-table-picker.tsx` — chọn **Phân hệ** (ô bấm
icon + tên) → **Bảng dữ liệu** (Select trong phân hệ). Phân hệ khai ở `config/data-modules.ts`; import
gắn `moduleId` trong `import-meta`, export lấy `module` từ backend registry (`/entities`).

**Mở rộng bảng (CR-174, 26/08/2026).** Phân hệ picker thêm **Sản xuất** + **Kho** (4 phân hệ).
- **Export = 11 bảng**: Nhân sự{NS·PB·CT} · Thu mua{YCBG·YCMH·ĐMH} · Sản xuất{NCC·SP·ĐVT·Phân loại} ·
  Kho{Danh mục kho}. Trần export tập trung nới lên **100.000 dòng** (product 6.803 dòng).
- **Import = danh mục đơn bảng có file mẫu**: thêm NCC·SP·ĐVT·Phân loại·Kho (enum 13..17, kind `float`
  cho VAT).
- **Import chứng từ nhiều dòng (CR-175/176)**: khung `doc_import.py` — 1 phiếu = 1 header + N dòng, gộp
  theo **Mã phiếu**, validate từng dòng, tạo-mới + hoàn tác, có file mẫu. Adapter cho **Yêu cầu báo giá**,
  **Yêu cầu mua hàng** (CR-175) và **Khảo sát**, **Đơn mua hàng** (CR-176 — thay importer Misa; revert
  vẫn qua `_revert_survey`/`_revert_po` để dọn đủ 2 loại dòng KS / cascade ĐMH). Nay phân hệ Thu mua ở
  dialog Nhập đủ **4 bảng** và **mọi đối tượng import đều có file mẫu**.
- **Pha C (rà scope export CSV):** đóng — không có lỗ rò thật (`product`/`supplier` PUBLIC, `department`
  export đã lọc phạm vi, `employee` đã vá CR-171). Còn lại chỉ là chuẩn hoá gác `read`→`export` (chưa làm,
  tránh siết quyền v1 đột ngột).

**Chưa làm:** thêm bảng còn lại (hợp đồng, thương hiệu…) khi cần; importer chứng từ Thu mua (YCBG/YCMH);
**Pha C** đổi export CSV `read`→`export` và vá `apply_scope` cho 3 export CSV viết tay
(product/supplier/department ở controller từng entity — **vẫn đang rò phạm vi**; export TẬP TRUNG mới
thì đã áp scope).

---

## 10. Rủi ro / bẫy đã biết

- **`product_code` bất biến** (D-025): adapter product **cấm** cập nhật `product_code`; sửa mã = tạo
  bản ghi mới → cảnh báo, không tự làm.
- **Prod không tự áp quyền mới** — action `import` seed xong vẫn phải `SEED_FORCE_SYNC=true` một lần
  hoặc gán tay; ghi rõ trong nhật ký deploy.
- **Chuẩn hoá export siết quyền** — sau QĐ-I4, tài khoản chỉ có `read` **mất** nút xuất CSV; rà lại
  vai trò trước khi deploy, tránh người dùng mất chức năng đang quen.
- **Mã hoá tiếng Việt khi import** — không đi tắt qua `mysql -e`; file CSV đọc `utf-8-sig`, XLSX qua
  `openpyxl` (đã có ở importer cũ).
- **File lớn / timeout** — mọi import chạy nền Celery (đã có); không import đồng bộ trong request nữa.
- **Trùng head migration trên `erp-v2`** — `git fetch` trước khi tạo revision; merge migration, không
  sửa `down_revision` của người khác.

## 11. Điều kiện đủ tổng (Definition of Done)

- Cổng `docker compose exec erp npm run check` xanh cả ba (typecheck/lint/test = 0 lỗi) ở mỗi đợt.
- Backend: `python -m pytest test/backend -q` xanh; thêm test cho registry adapter (validate/dedupe),
  staging→commit, revert (kể cả ca bản ghi bị sửa sau import), và ghi `ExportLog`.
  - ✅ **Đã có cho Đ-13d** (CR-170): `test/backend/test_import_catalog.py` (10 ca — validate/dedupe/
    dry-run-không-ghi/apply/revert-xoá/revert-khôi-phục/tham-chiếu-theo-mã/không-tạo-tài-khoản/file-mẫu)
    và `frontend-v2/.../config/import-meta.test.ts` (5 ca ràng buộc dữ liệu). ⚠️ Suite BE có **5 fail
    có sẵn trên nhánh** (attachment ext/scope · expected_date · duyệt khảo sát) — **không do CR-170**,
    đã đối chứng bằng `git stash`. Chưa có: test staging→commit (chờ KT-3) và `ExportLog` (chờ Đ-13b).
- Mọi endpoint export gọi `record_export`; mọi import đi qua batch (không còn đường ghi thẳng ngoài
  wrapper tạm).
- Nút Nhập/Xuất ẩn/hiện đúng `can('import'/'export', entity)`; backend chặn thật bằng `require`.
- Cập nhật `doc/erp/13-...md` (Đ-13 → tách 13a–e, đánh dấu tình trạng) và một dòng
  `change-log.md`; nếu chạm CSDL prod thì ghi nhật ký deploy.
