# DANH SÁCH MÀN HÌNH — PHÂN HỆ NGHIỆP VỤ (frontend-v2)

Bản 1.0 — 28/08/2026. Nguồn sự thật là `routes.tsx` của từng phân hệ.

---

## Phân hệ Thu mua (`procurement`)

Quản lý toàn bộ luồng chứng từ mua hàng: yêu cầu báo giá (YCBG) → phiếu khảo sát → yêu cầu mua hàng (YCMH) → đơn mua hàng (ĐMH) → tiến độ nhận hàng. Danh mục nhà cung cấp và sản phẩm thuộc phân hệ Sản xuất; phân hệ này chỉ đọc lại trên chứng từ.

Mục menu và entity/entities kiểm quyền:

| Mục menu | Quyền (`entity` / `entities`) |
|---|---|
| Tổng quan | `survey_request`, `purchase_request`, `purchase_order`, `survey`, `report` (OR — ẩn hết nếu không có cái nào) |
| Yêu cầu báo giá | `survey_request` |
| Yêu cầu mua hàng | `purchase_request` |
| Đơn mua hàng | `purchase_order` |
| Tiến độ mua hàng | `purchase_request` |
| Báo cáo mua hàng | `report` |
| Phiếu khảo sát | `survey` |
| Báo cáo khảo sát | `survey` |
| Phân công phụ trách | `category_assignee` (`manage: true` — chỉ hiện với tài khoản quản lý) |

**Tổng số route: 20** (18 trong `routes.tsx` + 2 trang in khai ngoài `ModuleLayout` trong `app-router.tsx`).

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Thu mua | `/procurement` | `procurement-dashboard-page.tsx` | Bảng điều khiển tổng hợp: KPI (YCMH chờ duyệt, chi tiêu năm, tiến độ giao hàng, YCBG), biểu đồ chi phí 12 tháng, cơ cấu theo nhóm hàng, top NCC chi tiêu, tuổi nợ AP và danh sách YCMH gần đây cần xử lý. Gọi `useProcurementDashboard` → `/api/dashboard/overview`. Từng khối gác riêng bằng `can(entity)`: khối `purchase_order` cần `purchase_order.read`, khối `payable` cần `payable.read`; thiếu quyền thì ẩn khối, không báo lỗi. |
| Danh sách Yêu cầu báo giá | `/procurement/survey-requests` | `survey-request-list-page.tsx` | Danh sách YCBG phân trang, lọc theo công ty/phòng ban/trạng thái/khoảng ngày và bộ lọc điều kiện nâng cao (`ConditionalFilter`). Gọi `useSurveyRequests` → `/api/survey-requests`. Cột trạng thái dùng `StatusBadge` ánh xạ từ `SR_STATUS_LABELS`. Nút "Tạo mới" gác bằng `PermissionGate` entity `survey_request` action `create`. |
| Tạo mới Yêu cầu báo giá | `/procurement/survey-requests/new` | `survey-request-detail-page.tsx` | Dùng chung tệp với màn Chi tiết YCBG. Form trắng: điền thông tin đầu phiếu và bảng dòng sản phẩm (`SurveyRequestLinesTable` dựng trên `LinesTable`). Tệp đính kèm gắn vào entity `survey_request_line`. Lưu nháp qua `useSaveSurveyRequest`; trường bắt buộc khi gửi duyệt kiểm qua `validateSurveyRequest` (`required-fields.ts`). |
| Chi tiết Yêu cầu báo giá | `/procurement/survey-requests/:id` | `survey-request-detail-page.tsx` | Dùng chung tệp với màn Tạo mới YCBG. Gọi `useSurveyRequest` → `/api/survey-requests/{id}`. Hiển thị đầy đủ: thông tin phiếu, bảng dòng khảo sát (chọn phương án NCC), card kết quả khảo sát, tệp đính kèm và `AuditTimeline`. Nút hành động (Gửi duyệt, Duyệt, Trả về, Hủy, Tạo YCMH từ phiếu) gác theo trạng thái + quyền; nút "Tạo YCMH" chỉ bật từ trạng thái `processing` trở lên (`CREATE_PR_STATUSES`). Hỗ trợ nhận draft từ trợ lý AI (`parseAssistantDraft`). |
| Danh sách Yêu cầu mua hàng | `/procurement/purchase-requests` | `purchase-request-list-page.tsx` | Danh sách YCMH phân trang, lọc theo công ty/phòng ban/trạng thái/khẩn cấp/khoảng ngày cần và ngày tạo, và bộ lọc điều kiện nâng cao. Gọi `usePurchaseRequests` → `/api/purchase-requests`. Nút "Tạo mới" gác bằng `PermissionGate`. |
| Tạo mới Yêu cầu mua hàng | `/procurement/purchase-requests/new` | `purchase-request-detail-page.tsx` | Dùng chung tệp với màn Chi tiết YCMH. Form trắng với bảng dòng `PurchaseRequestItemsTable` (dựng trên `LinesTable`). Nhận draft từ trợ lý AI (`parsePurchaseAssistantDraft`). Kiểm trường bắt buộc khi gửi duyệt qua `validatePurchaseRequest` (`required-fields.ts`) — backend không kiểm YCMH. |
| Chi tiết Yêu cầu mua hàng | `/procurement/purchase-requests/:id` | `purchase-request-detail-page.tsx` | Dùng chung tệp với màn Tạo mới YCMH. Gọi `usePurchaseRequest` → `/api/purchase-requests/{id}`. Hiển thị thông tin phiếu, bảng dòng, card NCC đề xuất, tổng tiền, tệp đính kèm, ĐMH liên quan và `AuditTimeline`. Nút nhanh "Tạo ĐMH" chuyển draft sang màn ĐMH mới. Hành động Gửi/Duyệt/Trả/Hủy/Đánh dấu khẩn gác theo trạng thái phiếu + quyền (`can`). |
| Danh sách Đơn mua hàng | `/procurement/purchase-orders` | `purchase-order-list-page.tsx` | Danh sách ĐMH phân trang, lọc theo công ty/NCC/người thực hiện/trạng thái phê duyệt/trạng thái tiến độ/hóa đơn/khẩn cấp/khoảng ngày và bộ lọc điều kiện nâng cao. Gọi `usePurchaseOrders` → `/api/purchase-orders`. Cột hiển thị song song `status` (phê duyệt) và `document_status` (tiến độ giao hàng). |
| Tạo mới Đơn mua hàng | `/procurement/purchase-orders/new` | `purchase-order-detail-page.tsx` | Dùng chung tệp với màn Chi tiết ĐMH. Form trắng hoặc nhận draft từ YCMH qua state điều hướng (`buildPurchaseOrderLines`). Bảng dòng `PurchaseOrderItemsTable` (dựng trên `LinesTable`). Kiểm trường bắt buộc qua `validatePurchaseOrder` — phải khớp `TRUONG_BAT_BUOC_DONG` ở `purchase_order/service.py` phía backend. |
| Chi tiết Đơn mua hàng | `/procurement/purchase-orders/:id` | `purchase-order-detail-page.tsx` | Dùng chung tệp với màn Tạo mới ĐMH. Gọi `usePurchaseOrder` → `/api/purchase-orders/{id}`. Hiển thị thông tin đơn, bảng dòng với tiến độ giao từng lần (popup `PurchaseOrderLineDialog`), tổng tiền, tệp đính kèm, thanh toán và `AuditTimeline`. Một số trường vẫn sửa được sau khi duyệt (`PO_FIELDS_EDITABLE_AFTER_APPROVE`). Hành động Trả và Hủy duyệt yêu cầu nhập lý do. |
| Tiến độ mua hàng | `/procurement/purchase-progress` | `purchase-progress-page.tsx` | Báo cáo phẳng theo TỪNG LẦN GIAO của mỗi dòng ĐMH, gọi `usePurchaseProgress` → `/api/purchase-progress`. Lọc theo công ty/phòng ban/trạng thái; không dùng `ConditionalFilter` vì endpoint tự xử tham số riêng (CR-088: lọc theo `department_id` thay vì tên tránh trượt khi phòng đổi tên). Backend trả cờ `show_supplier`: người thiếu quyền `supplier.read` thì ẩn hẳn cột NCC và vận chuyển. |
| Danh sách Phiếu khảo sát | `/procurement/surveys` | `survey-list-page.tsx` | Danh sách phiếu khảo sát phân trang, lọc theo trạng thái/loại phiếu/mã sản phẩm và bộ lọc điều kiện nâng cao. Gọi `useSurveys` → `/api/surveys`. Cột loại phiếu ánh xạ từ `SURVEY_TYPE_LABELS`. Nút "Tạo mới" gác bằng `PermissionGate`. |
| Tạo mới Phiếu khảo sát | `/procurement/surveys/new` | `survey-detail-page.tsx` | Dùng chung tệp với màn Chi tiết Phiếu khảo sát. Form trắng với hai bảng dòng tách theo loại (`SurveyLinesTable`): bảng NCC (`supplier`) và bảng sản phẩm (`product`). Tệp đính kèm đầu phiếu gắn entity `survey`, tệp từng dòng gắn entity `survey_line`. |
| Chi tiết Phiếu khảo sát | `/procurement/surveys/:id` | `survey-detail-page.tsx` | Dùng chung tệp với màn Tạo mới Phiếu khảo sát. Gọi `useSurvey` → `/api/surveys/{id}`. Mỗi dòng có thể điền giá và được duyệt riêng (`useSurveyLineApprove`). Hành động Gửi/Duyệt/Trả/Hủy gác theo trạng thái + quyền. CR-090 quy định chính xác hành vi bảng dòng (xuống dòng, ô chọn NCC, phím Enter, bề rộng cột). |
| Báo cáo khảo sát | `/procurement/survey-report` | `survey-report-page.tsx` | Báo cáo theo DÒNG khảo sát (không phải theo phiếu), gọi `useSurveyReport` → `/api/survey-report`. Lọc theo loại dòng (`kind`: NCC hoặc sản phẩm) và kết quả duyệt dòng (`line_approve`). Bốn ô đếm ở đầu bấm được lọc nhanh; backend tính số đếm trước khi lọc nên bấm qua lại vẫn thấy đủ bốn con số. |
| Báo cáo mua hàng | `/procurement/purchase-report` | `purchase-report-page.tsx` | Tám tab trên cùng bộ lọc (công ty · năm): Tổng quan, Chi tiêu NCC, Chi tiêu bộ phận, Chi tiêu nhóm hàng, Chi tiêu NSPT, YCMH, YCBG, Giao hàng. Gọi `useProcurementReport` + `useReportMatrix` → `/api/purchase-report` + `/api/purchase-report/matrix`. Một lần gọi `/matrix` trả đủ số liệu năm tab ma trận nên đổi tab không gọi lại API. Nút "Cập nhật" bắt backend tính lại snapshot. Quyền `report.export` gác nút xuất Excel. |
| Phân công phụ trách | `/procurement/category-assignees` | `category-assignee-list-page.tsx` | Bảng phân công người phụ trách chính và dự phòng theo nhóm hàng VTBB. Gọi `/api/category-assignees` trực tiếp qua `httpClient` (chưa dùng TanStack hook). Quyền `category_assignee.create` gác nút "Thêm", `category_assignee.delete` gác nút xóa từng dòng. |
| Tạo/Sửa phân công phụ trách | `/procurement/category-assignees/new` | `category-assignee-form-page.tsx` | Form chọn nhiều nhóm hàng (`MultiPicker`) và gán người phụ trách chính/dự phòng. Gọi `/api/category-assignees` + `/api/item-groups` + `/api/employees` qua `httpClient`. Có `AuditTimeline` xem lịch sử thay đổi của bản ghi. Hỗ trợ mode sửa hiện có qua query param `?cats=<item_group_id>`. |
| Bản in YCMH | `/print/purchase-request/:id` | `purchase-request-print-page.tsx` | Mẫu in 003/BM/PKT — khai ngoài `ModuleLayout` (không có menu, topbar). Gọi `usePurchaseRequest`. Hai chế độ: Mẫu thường và Mẫu thuế (`taxMode`). Bật/tắt khu vực chữ ký. Tên route đăng tại `app-router.tsx`. |
| Bản in ĐMH | `/print/purchase-order/:id` | `purchase-order-print-page.tsx` | Bản in ĐMH — khai ngoài `ModuleLayout`. Gọi `usePurchaseOrderPrintData`. Hai mẫu trên cùng một trang: Đơn đặt hàng (in ngang, 13 cột, gửi NCC) và Đơn mua hàng (in dọc, nội bộ). Tên route đăng tại `app-router.tsx`. |

---

## Phân hệ Sản xuất (`production`)

Quản lý danh mục dùng chung cho toàn hệ: Nhà cung cấp, Sản phẩm & Vật tư bán thành phẩm (VTBB), Đơn vị tính, Phân loại VTBB và Hợp đồng. Phần lệnh sản xuất thực sự chưa có backend; module hiện tại chỉ phục vụ các danh mục nền.

Mục menu và entity/entities kiểm quyền:

| Mục menu | Quyền (`entity` / `entities`) |
|---|---|
| Tổng quan | `supplier`, `product`, `unit`, `item_group`, `contract` (OR) |
| Nhà cung cấp | `supplier` |
| Sản phẩm & Vật tư | `product` |
| Đơn vị tính | `unit` |
| Phân loại VTBB | `item_group` |
| Hợp đồng | `contract` |

**Tổng số route: 11**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Sản xuất | `/production` | `production-dashboard-page.tsx` | Hiện số lượng NCC hàng hóa và đơn vị vận chuyển (hai lần gọi `useSuppliers` với `page_size: 1` chỉ lấy `total`). Gác bằng `can('supplier', 'read')` trước khi gọi API. Ghi chú: backend chưa có module sản xuất thực sự, phần lệnh sản xuất/định mức sẽ bổ sung sau. |
| Danh sách Nhà cung cấp | `/production/suppliers` | `supplier-list-page.tsx` | Dùng `CrudListPage` với `SUPPLIER_CRUD_CONFIG`. Gọi `/api/suppliers`. Lọc nhanh theo vai trò (NCC hàng hóa / Đơn vị vận chuyển). Ô tìm nhanh gửi tham số `name` (LIKE) vì backend không có tham số `search` chung cho NCC. |
| Chi tiết Nhà cung cấp | `/production/suppliers/:id` | `supplier-detail-page.tsx` | Dùng `CrudDetailPage` với `SUPPLIER_CRUD_CONFIG`. Gọi `/api/suppliers/{id}`. Năm tab: Thông tin (MST, tư cách pháp lý, VAT lưu tỷ lệ `0.08` — dùng kiểu trường `percent` của CrudDetailPage, hình thức thanh toán), Hợp đồng, Công nợ & Đánh giá, Lịch sử mua hàng, Khảo sát của NCC. Tab Công nợ gác `enabled` theo `can('payable', 'read')` để không gọi API khi thiếu quyền và tránh toast 403 (CR-106). |
| Danh sách Sản phẩm & Vật tư | `/production/products` | `product-list-page.tsx` | Dùng `CrudListPage` với `PRODUCT_CRUD_CONFIG`. Gọi `/api/products`. Mỗi dòng trong `tab_product` là một SKU (variant), nhận diện bằng `product_code` — không có tầng sản phẩm cha. |
| Chi tiết Sản phẩm & Vật tư | `/production/products/:id` | `product-detail-page.tsx` | Dùng `CrudDetailPage` với `PRODUCT_CRUD_CONFIG`. Gọi `/api/products/{id}`. Có tab "Lịch sử mua hàng" (`PurchaseHistoryTable`, `DataTable` riêng) ẩn cột NCC khi thiếu quyền `supplier.read`. |
| Danh sách Đơn vị tính | `/production/units` | `unit-list-page.tsx` | Dùng `CrudListPage` với `UNIT_CRUD_CONFIG`. Gọi `/api/units`. Danh mục đơn giản (tên, ký hiệu). |
| Chi tiết Đơn vị tính | `/production/units/:id` | `unit-detail-page.tsx` | Dùng `CrudDetailPage` với `UNIT_CRUD_CONFIG`. Gọi `/api/units/{id}`. |
| Danh sách Phân loại VTBB | `/production/item-groups` | `item-group-list-page.tsx` | Dùng `CrudListPage` với `ITEM_GROUP_CRUD_CONFIG`. Gọi `/api/item-groups`. Nhóm hàng được dùng để phân công phụ trách trong Thu mua. |
| Chi tiết Phân loại VTBB | `/production/item-groups/:id` | `item-group-detail-page.tsx` | Dùng `CrudDetailPage` với `ITEM_GROUP_CRUD_CONFIG`. Gọi `/api/item-groups/{id}`. |
| Danh sách Hợp đồng | `/production/contracts` | `contract-list-page.tsx` | Dùng `CrudListPage` với `CONTRACT_CRUD_CONFIG`. Gọi `/api/contracts`. Lọc theo loại đối tác, trạng thái hợp đồng và tình trạng hạn. CR-117/CR-118 chuẩn hóa phạm vi trường (`SCOPE_FIELDS`) và mã `contract_type` sang tiếng Anh. |
| Chi tiết Hợp đồng | `/production/contracts/:id` | `contract-detail-page.tsx` | Dùng `CrudDetailPage` với `CONTRACT_CRUD_CONFIG`. Gọi `/api/contracts/{id}`. Có tab Đối tác (`ContractPartnerTab`) và Tệp đính kèm (`ContractFilesTab`). Màu badge tình trạng hạn theo mã tiếng Anh `expired/expiring_soon/valid` (B-02) — không dùng chuỗi tiếng Việt tránh mất màu khi sửa nhãn. |

---

## Phân hệ Kho (`inventory`)

Quản lý tồn kho hiện tại và danh mục kho. Phần nhập xuất và luân chuyển kho vẫn nằm ở bản `frontend/` cũ, chưa dời sang frontend-v2.

Mục menu và entity/entities kiểm quyền:

| Mục menu | Quyền (`entity` / `entities`) |
|---|---|
| Tổng quan | `inventory`, `warehouse` (OR) |
| Tồn kho | `inventory` |
| Danh mục Kho | `warehouse` |

**Tổng số route: 4**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Kho | `/inventory` | `inventory-dashboard-page.tsx` | KPI giá trị tồn kho, số dòng hết hàng, bảng cảnh báo tồn thấp (`low_stock`). Gọi `useProcurementDashboard` (khối `kpi` + `low_stock`) và `useInventoryItems` (page_size 1 lấy total). Gác toàn bộ màn nếu thiếu quyền `inventory.read` (không chỉ ẩn khối — hiện thông báo "không có quyền" thay vì dashboard rỗng). |
| Tồn kho | `/inventory/stock` | `inventory-list-page.tsx` | Bảng tồn kho theo công ty · kho · mã sản phẩm. Gọi `useInventoryItems` → `/api/inventory`. Số dư do backend cộng dồn từ sổ phát sinh mỗi lần nhận hàng hoặc điều chỉnh, không nhập tay trực tiếp. Lọc theo công ty/kho/nhóm hàng/tình trạng số lượng và bộ lọc điều kiện nâng cao. Nút "Điều chỉnh" mở `InventoryAdjustDialog`, mỗi lần chỉnh để lại một dòng trong sổ; xem chi tiết sổ qua `InventoryDetailDialog`. |
| Danh mục Kho | `/inventory/warehouses` | `warehouse-list-page.tsx` | Dùng `CrudListPage` với `WAREHOUSE_CRUD_CONFIG`. Gọi `/api/warehouses`. |
| Chi tiết Kho | `/inventory/warehouses/:id` | `warehouse-detail-page.tsx` | Dùng `CrudDetailPage` với `WAREHOUSE_CRUD_CONFIG`. Gọi `/api/warehouses/{id}`. |

---

## Phân hệ Tài chính (`finance`)

Quản lý công nợ phải trả phát sinh từ nhận hàng và yêu cầu thanh toán (YCTT). Lối chính lên phiếu là cột tick ở màn Công nợ; nút tạo mới ở màn YCTT là lối phụ cho khoản chi không đi từ công nợ (CR-066). Module không khai `entity` ở tầng module (không giống các phân hệ khác) để tránh ẩn nhầm khi người chỉ có quyền xem công nợ nhưng không được lập phiếu.

Mục menu và entity/entities kiểm quyền:

| Mục menu | Quyền (`entity` / `entities`) |
|---|---|
| Tổng quan | `payable`, `payment_request` (OR) |
| Công nợ phải trả | `payable` |
| Yêu cầu thanh toán | `payment_request` |

**Tổng số route: 6** (5 trong `routes.tsx` + 1 trang in khai ngoài `ModuleLayout` trong `app-router.tsx`).

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Tài chính | `/finance` | `finance-dashboard-page.tsx` | KPI công nợ (đến hạn sớm, quá hạn), biểu đồ tuổi nợ (`ap_aging`), bảng top NCC nợ nhiều và danh sách YCTT gần đây. Gọi `useProcurementDashboard` (chỉ đọc khóa trong khối `payable`: `ap_aging`, `top_debt_suppliers`, `kpi.due_soon`, `kpi.overdue`), `usePayableSummary` và `usePaymentRequests`. Lưu ý: `kpi.pr_pending` trong `/dashboard/overview` là YCMH (Thu mua), KHÔNG phải YCTT. |
| Công nợ phải trả | `/finance/payables` | `payable-list-page.tsx` | Bảng chỉ đọc — backend tự sinh dòng khi nhận hàng (`payable/service.upsert`). Phân trang server-side (khác v1 kéo cả 1000 dòng). Gọi `usePayables` → `/api/payables`. Cột tick chọn nhiều khoản qua trang, nút "Tạo đề nghị thanh toán" chuyển sang màn YCTT mới kèm danh sách `payable_ids`. Tick giữ nguyên khi sang trang, xóa khi đổi bộ lọc. Lọc theo công ty/trạng thái/tuổi nợ/năm và bộ lọc điều kiện nâng cao. |
| Danh sách Yêu cầu thanh toán | `/finance/payment-requests` | `payment-request-list-page.tsx` | Danh sách YCTT phân trang, lọc theo công ty/trạng thái/nguồn chi (`source_type`)/phương thức thanh toán. Gọi `usePaymentRequests` → `/api/payment-requests`. Nút "Tạo mới" mở form trắng (chi ngoài công nợ — CR-066), gác bằng `can('payment_request', 'create')`. |
| Tạo mới Yêu cầu thanh toán | `/finance/payment-requests/new` | `payment-request-detail-page.tsx` | Dùng chung tệp với màn Chi tiết YCTT. Hai lối vào: từ Công nợ (nhận `payable_ids` qua query string → `useQuery` + `payableApi`) hoặc form trắng. Không ghi DB khi rời màn giữa chừng — không sinh phiếu nháp (CR-025). Gọi `useCreatePaymentRequests` → `POST /api/payment-requests`. |
| Chi tiết Yêu cầu thanh toán | `/finance/payment-requests/:id` | `payment-request-detail-page.tsx` | Dùng chung tệp với màn Tạo mới YCTT. Gọi `usePaymentRequest` → `/api/payment-requests/{id}`. Hiển thị bảng dòng công nợ (`PaymentRequestLinesTable`), tổng tiền, phương thức thanh toán, tệp đính kèm và `AuditTimeline`. Hành động Gửi/Duyệt/Từ chối/Hủy/Đánh dấu đã chi gác theo trạng thái + quyền. Nút in mở `/print/payment-request/:id`. |
| Bản in YCTT | `/print/payment-request/:id` | `payment-request-print-page.tsx` | Phiếu đề nghị thanh toán — khai ngoài `ModuleLayout`. Gọi `usePaymentRequestPrintData`. Hai chế độ: Mẫu thường và Mẫu thuế; gom dòng trùng số chứng từ (CR-127). Tên route đăng tại `app-router.tsx`. |

---

## Phân hệ Nhân sự (`hr`)

Quản lý nhân viên, phòng ban, pháp nhân (công ty) và hệ phân quyền hai trục: vai trò × phạm vi dữ liệu.

Mục menu và entity/entities kiểm quyền:

| Mục menu | Quyền (`entity` / `entities`) |
|---|---|
| Tổng quan | `employee`, `department`, `company`, `role` (OR) |
| Nhân sự | `employee` |
| Phòng ban | `department` |
| Công ty | `company` |
| Phân quyền tài khoản | `role` (`manage: true` — chỉ hiện với tài khoản quản lý) |

**Tổng số route: 9**.

| Màn | Route | Tệp | Mô tả và logic chính |
|---|---|---|---|
| Tổng quan Nhân sự | `/hr` | `hr-dashboard-page.tsx` | KPI số nhân sự đang làm/đã nghỉ/phòng ban/pháp nhân và biểu đồ phân bổ theo phòng ban (ngang) và theo loại (donut). Gọi `useHrOverview` → `/api/employees` nhiều lần với tham số khác nhau. Không có lối tắt vì menu trái đã đủ mục. |
| Danh sách Nhân sự | `/hr/employees` | `employee-list-page.tsx` | Danh sách nhân viên phân trang, lọc trạng thái và bộ lọc điều kiện nâng cao. Gọi `useEmployees` → `/api/employees`. Cột ảnh đại diện, mã, tên, phòng ban, công ty. Nút "Thêm" gác bằng `PermissionGate` entity `employee` action `create`. |
| Chi tiết Nhân sự | `/hr/employees/:id` | `employee-detail-page.tsx` | Form nhân viên dùng `react-hook-form` + zod. Gọi `useEmployee` / `useUpdateEmployee` / `useDeleteEmployee`. Có `AvatarUploader`, `RecordIdentityCard`, `AuditTimeline`. Nút xóa gác bằng `PermissionGate`. Quy tắc đồng bộ email nhân sự → `User.email` — chỉ cập nhật khi thật sự thay đổi, không đụng `handle` của tài khoản admin. |
| Danh sách Phòng ban | `/hr/departments` | `department-list-page.tsx` | Danh sách phòng ban phân trang, lọc trạng thái và bộ lọc điều kiện nâng cao. Gọi `useDepartments` → `/api/departments`. Nút "Thêm" gác bằng `PermissionGate`. |
| Chi tiết Phòng ban | `/hr/departments/:id` | `department-detail-page.tsx` | Form phòng ban dùng `react-hook-form` + zod. Gọi `useDepartment` / `useUpdateDepartment` / `useDeleteDepartment`. Có `AuditTimeline` và nút xóa gác bằng `PermissionGate`. |
| Danh sách Công ty | `/hr/companies` | `company-list-page.tsx` | Danh sách pháp nhân phân trang, lọc trạng thái và bộ lọc điều kiện nâng cao. Gọi `useCompanies` → `/api/companies`. Nút "Thêm" gác bằng `PermissionGate`. |
| Chi tiết Công ty | `/hr/companies/:id` | `company-detail-page.tsx` | Form pháp nhân dùng `react-hook-form` + zod. Gọi `useCompany` / `useUpdateCompany` / `useDeleteCompany`. Có `AvatarUploader` (logo công ty) và `AuditTimeline`. |
| Phân quyền tài khoản | `/hr/permissions` | `role-permission-page.tsx` | Hai tab: "Vai trò & quyền" (ma trận entity × action cho từng role, `RolePermissionMatrix`) và "Người dùng" (`UserAccountTable`). Gọi `useRoles` + `usePermissionMeta` + `useRolePermissions`. Panel bên (`RoleSidePanel`) hiện khi chọn vai trò; lưu bằng `useSaveRolePermissions`. Xóa vai trò gác bằng `can('role', 'delete')`. |
| Chi tiết phân quyền tài khoản | `/hr/permissions/users/:userId` | `user-permission-detail-page.tsx` | Gán vai trò và phạm vi dữ liệu cho một tài khoản. Gọi `useUserAccount` + `useRoles` + `useAssignRoles`. Phải lưu vai trò trước rồi mới đặt được phạm vi (phạm vi lưu theo cặp tài khoản × vai trò). Không cho tự sửa quyền của chính mình — giao diện khóa thêm ngoài chặn backend tại `core/privilege_escalation.py` (CR-158). |

---

## Ghi chú chung

Các khuôn dùng chung mà màn nghiệp vụ dựa vào:

**1. `DataTable`** (`shared/data-table/`) — tất cả bảng danh sách đều dùng. Không tự ghép `<Table>` ở tầng trang. Tài liệu chi tiết ở `docs/ui/table.md`.

**2. `LinesTable`** (`shared/data-table/lines-table.tsx`, CR-101/CR-102) — bảng dòng chứng từ dùng chung cho YCMH, YCBG, ĐMH và bảng giao hàng trong popup chi tiết dòng ĐMH. Tính năng: ghim cột, kéo thả đổi thứ tự, co giãn và auto-fit, tô màu, nhớ `localStorage`, chế độ rút gọn/đầy đủ (cột phụ khai `compactHidden`). Bảng dòng mới phải dùng `LinesTable`, không chép khung. Không đặt bề rộng cứng `style={{ width: totalWidth }}` trên `<table>` — dùng `table-fixed` + `w-full` là đủ.

**3. `CrudListPage` / `CrudDetailPage`** (`shared/crud/`) — khung CRUD khai báo (declarative) ba cấp kế thừa: danh sách, chi tiết với `RecordIdentityCard` + `AuditTimeline` + tabs/bảng con `DataTable` + `CrudFormDialog`. Cấu hình khai tại `modules/<module>/config/*-crud.tsx` cho từng entity. Các danh mục hiện dùng khung này: Nhà cung cấp, Sản phẩm & Vật tư, Đơn vị tính, Phân loại VTBB, Hợp đồng (Sản xuất) và Danh mục Kho (Kho).

**4. `required-fields.ts`** (`modules/procurement/utils/required-fields.ts`, CR-107) — nguồn sự thật duy nhất cho trường bắt buộc của YCMH, YCBG và ĐMH: vừa vẽ dấu sao đỏ (`RequiredMark`, `RequiredHeader`), vừa chặn khi gửi duyệt (không chặn khi lưu nháp). Bộ trường ĐMH phải khớp `TRUONG_BAT_BUOC_DONG` trong `purchase_order/service.py`; YCMH và YCBG chỉ kiểm ở giao diện. VAT cố ý không bắt buộc: giá trị `0` vừa nghĩa "chưa nhập" vừa nghĩa "hàng không chịu thuế".

**5. `ConditionalFilter` / `FilterProvider`** (`shared/conditional-filter/`) — bộ lọc điều kiện nâng cao (AND/OR) dùng cho: YCBG, YCMH, ĐMH, Phiếu khảo sát, Tồn kho, Công nợ, Nhân sự, Phòng ban, Công ty. Màn không dùng khuôn này: Tiến độ mua hàng (xử tham số riêng), Báo cáo khảo sát, Báo cáo mua hàng, Phân công phụ trách.
