# Đề xuất — Phân quyền Văn thư theo tab nghiệp vụ & danh mục

Ngày 25/08/2026 · nhánh `erp-v2` · trạng thái **ĐÃ LÀM (PA-1) — xem CR-157**

> ⚠️ **Đính chính điểm C.** Câu «phân hệ gác bằng `document` nên vai trò chỉ giữ
> `document_book` không thấy cả phân hệ Văn thư» là **SAI**. `canOpenModule` xét
> «còn mục menu nào hiện không», và hai mục *Văn bản* / *Chờ tôi duyệt* không
> khai `entity` nên luôn hiện — `ErpModule.entity` thực ra là **trường chết,
> không chỗ nào đọc**. Nửa còn lại của C (Tổng quan gọi API cần `document.read`
> mà không có nhánh tắt) thì đúng và đã vá.
>
> Trường chết đó vẫn nằm nguyên trong `module-definition.ts` — để ngoài phạm vi
> đợt này, nhưng nó là cái bẫy: người sau sẽ khai nó và tưởng đã gác được.

## 1. Vấn đề

Ma trận phân quyền xếp theo **tên bảng**, menu xếp theo **màn hình**. Hai trục không khớp
nhau, nên người khai quyền không tick được thứ họ định tick.

Menu Văn thư (`modules/document/routes.tsx`) và khóa gác thực tế:

| Mục menu | Nhóm | Khóa gác menu | Khóa API thật sự dùng |
|---|---|---|---|
| Tổng quan | — | *(mở)* | `document.read` |
| Văn bản | Nghiệp vụ | *(mở — cố ý)* | `document.*` + `doc_reader` |
| Chờ tôi duyệt | Nghiệp vụ | *(mở — cố ý)* | không (việc của chính mình) |
| Sổ văn bản | Nghiệp vụ | `document_book` | `document_book.*` |
| Thiết lập › Loại văn bản | Danh mục | `doc_type` | `doc_type.*` |
| Thiết lập › Thư viện văn bản mẫu | Danh mục | `doc_type` | `doc_type.*` |
| Thiết lập › Mức mật / khẩn | Danh mục | `doc_type` | **`security_level.*`** |
| Thiết lập › Đơn vị gửi nhận | Danh mục | `doc_type` | **`external_party.*`** |
| Quy tắc đánh số | Danh mục | `doc_type` | `doc_type.*` |
| Quy tắc quan hệ | Danh mục | `doc_type` | `doc_type.*` |

Ba chỗ lệch, đều kiểm chứng được:

**A. Bốn màn dùng chung một khóa `doc_type`.** Loại văn bản · Thư viện mẫu · Quy tắc đánh
số · Quy tắc quan hệ. Cho một người sửa quy tắc đánh số = cho họ sửa luôn loại văn bản và
thư viện mẫu. Không tách được, dù ba việc đó do ba người khác nhau làm.

**B. Một mục menu lại gác bằng khóa mà tab bên trong không dùng.** «Thiết lập văn bản»
gác bằng `doc_type`, nhưng bốn tab chạy trên **ba** khóa. Hệ quả cụ thể:
- ai chỉ có `external_party` → **không vào nổi trang** chứa đúng tab của mình;
- ai có `doc_type` mà không có `security_level` → vào được trang, thấy tab *Mức mật / khẩn*,
  bấm vào ăn **403**.

**C. Phân hệ gác bằng `document`, nên vai trò «quản lý sổ» không tồn tại được.**
`documentModule.entity = 'document'`. Ai chỉ có `document_book` thì **không thấy cả phân hệ
Văn thư** — dù màn Sổ văn bản là của họ. Cùng chuỗi đó: `useDocumentDashboard` không có
nhánh tắt, nên nếu mở được Tổng quan mà thiếu `document.read` thì ăn toast 403 ngay lúc vào.

## 2. Ba phương án

### PA-1 — Tách khóa cho khớp màn hình *(khuyến nghị)*

Thêm 3 entity, sửa gác menu:

| Khóa mới | Nhãn | Thay cho |
|---|---|---|
| `doc_template` | Thư viện văn bản mẫu (Văn thư) | `doc_type` ở `template_controller` |
| `doc_numbering_rule` | Quy tắc đánh số (Văn thư) | `doc_type` ở `numbering_rule_controller` + `issue_code_controller` |
| `doc_link_rule` | Quy tắc quan hệ (Văn thư) | `doc_type` ở `link_rule_controller` |

Kèm 3 sửa ở giao diện:
- «Thiết lập văn bản» **bỏ `entity`**, để trang tự ẩn tab theo `can(...)` — đúng cách
  «Văn bản» đang làm, lý lẽ đã ghi sẵn trong `routes.tsx`.
- «Quy tắc đánh số» → `doc_numbering_rule`, «Quy tắc quan hệ» → `doc_link_rule`.
- `documentModule.entity`: bỏ, hoặc đổi sang phép HOẶC của cả nhóm — để vai trò chỉ có
  `document_book` vẫn thấy phân hệ (điểm **C**).
- `useDocumentDashboard` thêm `enabled: can('document', 'read')`.

Sau đó: **1 mục menu = 1 khóa**, riêng «Thiết lập văn bản» = 3 khóa nhưng tab tự ẩn.

**Rủi ro dời dữ liệu — điểm phải quyết.** Vai trò đã có trên DB thật KHÔNG tự nhận khóa
mới (`seed_prod` không ghi đè phân quyền sửa trên UI). Deploy xong, người đang có `doc_type`
sẽ **mất quyền vào 3 màn đó** cho tới khi admin tick lại tay.
→ Cách chữa: viết **migration một lần** cấp 3 khóa mới cho mọi vai trò **đang có `doc_type`**,
đúng từng action. Không ai mất gì, và từ đó về sau tách được. Rẻ hơn hẳn `SEED_FORCE_SYNC=true`
(cái đó ghi đè cả những chỉnh tay khác).

Chi phí: 3 dòng `ENTITIES` + `ENTITY_LABELS` + `SCOPE_FIELDS` (cả 3 đều `PUBLIC`, cùng lẽ
với `doc_type` — danh mục nền không lọc theo pháp nhân) · 4 controller đổi `require(...)` ·
1 migration · `STD_ROLES` · sửa `routes.tsx`. Bài kiểm 39/39 entity trong `SCOPE_FIELDS` sẽ
tự bắt nếu khai thiếu.

### PA-2 — Gom ngược: một khóa `doc_catalog` cho cả nhóm Danh mục

Gộp `doc_type` + `security_level` + `external_party` + 3 màn quy tắc thành **một** khóa.
Ma trận ngắn lại, hết lệch A và B. Nhưng mất hẳn khả năng tách — chỉ đúng nếu thực tế là
"ai được khai báo thì được khai hết". Rủi ro dời dữ liệu ngược lại: người đang chỉ có
`external_party` sẽ **được thêm** quyền trên loại văn bản.

### PA-3 — Chỉ đổi cách hiển thị ma trận

Giữ nguyên 5 khóa, chỉ gom dòng theo phân hệ và đổi nhãn theo tên màn hình
(«Loại văn bản (Văn thư)» → «Thiết lập văn bản › Loại văn bản»). Rẻ nhất, không đụng dữ
liệu quyền đang chạy. **Không chữa được A, B, C** — chỉ làm ma trận dễ đọc hơn.

## 3. Khuyến nghị

**PA-1 + migration kế thừa `doc_type`.** Đây đúng thứ khách hỏi ("phân quyền theo tab
nghiệp vụ và danh mục"), và chỉ có nó tách được ba nhóm việc thật sự khác nhau: soạn/ban
hành văn bản · giữ sổ · khai báo danh mục nền.

Nếu muốn làm dần: **C trước** (bỏ `documentModule.entity` + `enabled` cho dashboard) vì đó
là lỗi đang chặn người dùng thật, không phải chuyện thiết kế. A và B đi cùng PA-1.

## 4. Câu chưa có lời

1. Ba màn danh mục (loại văn bản · quy tắc đánh số · quy tắc quan hệ) thực tế **có do ba
   người khác nhau giữ không**, hay cùng một người văn thư trưởng? Nếu cùng một người thì
   PA-3 là đủ và PA-1 chỉ thêm việc.
2. Thư viện văn bản mẫu — người **soạn** văn bản có cần sửa mẫu không? Nếu có thì
   `doc_template` nên đi kèm `document.create` chứ không đi cùng nhóm danh mục.
3. Có vai trò nào thật sự chỉ giữ **Sổ văn bản** mà không đụng văn bản không? Nếu không thì
   điểm C chỉ cần sửa dashboard, khỏi đụng `documentModule.entity`.
4. Duyệt dấu (`seal_request`, `seal_type`) và Đặt xe (`vehicle_booking`, `vehicle`, `driver`)
   đã có khóa nhưng **chưa có màn nào** — có nằm trong đợt rà này không?
