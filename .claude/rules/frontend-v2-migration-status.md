---
paths:
  - "frontend/**"
  - "frontend-v2/**"
  - "doc/erp/13-ke-hoach-man-con-lai-v2.md"
---
# Tiến độ dời màn từ `frontend/` sang `frontend-v2/` (Đ-01…Đ-15)

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

Phân xử khi có yêu cầu mới: **sửa lỗi** màn đang chạy thật → `frontend/`; **tính năng mới**
→ `frontend-v2/`, màn đó chưa có ở v2 thì dựng màn đó trước. `frontend/` chưa được tắt vì v2
còn thiếu màn. **Số đo đầy đủ và kế hoạch dời nằm ở `doc/erp/13-ke-hoach-man-con-lai-v2.md`**
(bản 2.0, xem **CR-097**): bản cũ có **48 màn** — _(rà lại từng dòng 03/09/2026)_ bảng §1 nay
**50 dòng** *(48 màn cũ + `/system/exports` + 44b)*: **50 xong** · **0 khuyết** · **0 thiếu** ·
**0 chờ quyết**. Chia **15 đợt Đ-01 … Đ-15**: đã xong **Đ-01…Đ-14**; còn mỗi **Đ-15**
(tắt `frontend/`), và **không còn gì chặn nó**. Màn cuối cùng — **_Chứng từ_** — đã dời
03/09/2026 (CR-266): `/procurement/purchase-orders/:id/documents`, **không đứng trong menu**,
vào từ nút _Xem cả chuỗi chứng từ_ trong thẻ chứng từ của chi tiết ĐMH. ⚠️ Đụng vào nó thì nhớ
`/api/attachments/chain` khai entity `survey_line` **hai lần** (id dòng NCC + id dòng sản phẩm)
nên **phải khử trùng theo `link_id`** — bản v1 không khử nên đếm dôi; và `url` trong kết quả
**rỗng với entity riêng tư**, xem trước phải đi qua `/api/attachments/{id}/view`.
⚠️ Mấy con số này cũ rất nhanh — **luôn mở §0 và bảng §3 của `13-...md` để lấy số mới nhất**,
đừng trích lại dòng này.
⚠️ **NHẬN ĐỢT TRƯỚC KHI LÀM.** Nhiều người cùng đẩy lên `erp-v2`, nên cột **_Ai làm_** trong bảng
§3 của `13-...md` là **chỗ ghi phân công duy nhất** — luật bốn dòng ở §3.1: ghi tên + đổi
_Đang làm_ rồi **push riêng dòng đó ngay** trước khi gõ mã, xong thì đổi _Xong (CR-xxx)_, bỏ
giữa chừng thì trả về _(chưa nhận)_. `git fetch` trước mỗi lần bắt đầu và trước mỗi lần push.
**Cụm Yêu cầu thanh toán ĐÃ XONG** (Đ-06/07/08, CR-119): danh sách + chi tiết + phiếu in ở
`/finance/payment-requests` theo QĐ-5 — `modules/finance/pages/payment-request-{list,detail,print}-page.tsx`,
route in đăng ở `app/router/app-router.tsx`. Bản in cũng đã có **gom dòng trùng số chứng từ** và
tab _Mẫu thuế_ giống hệt bản v1 (CR-127). Nghĩa là **không còn màn nào chặn nghiệp vụ** — dòng
"chặn nghiệp vụ chỉ còn Yêu cầu thanh toán" ở các bản CLAUDE.md trước nay đã sai, bỏ đi.
_Quản lý Import_ (MC-6) từng bị hoãn nhưng khách **mở lại 25/08/2026**: hai màn `/system/imports`
(+ `/:id`) và cụm `/system/exports` **đã chạy** (CR-186, Đ-13a/13b); phần còn dở của Đ-13 là **mở
rộng tính năng**, không phải màn thiếu — xem `doc/erp/16-quan-ly-import-export-v2.md` §9. _Tiến độ báo giá_ và _Xử lý khảo sát_ từng quyết bỏ nhưng
**đã SỐNG LẠI 29/08/2026** (CR-227 + CR-222) — xem đính chính ở `doc/erp/12-...` mục 2.7:
Xử lý khảo sát là trang riêng `/procurement/survey-requests/:id/process`, Tiến độ báo giá ở
`/procurement/survey-progress`, menu Thu mua v2 xếp đúng thứ tự bản v1.
**Đã xong Đ-11** (CR-132 — số cũ CR-129 bị trùng nên đánh lại): Trang chủ có lại đủ 4 khối
(_Top nhà cung cấp_, _Chi tiêu theo bộ phận_, _Trạng thái đơn hàng_, _Tuổi nợ_) và thao tác nhanh
_Duyệt / Trả lại_ YCMH; **Tổng quan Tài chính** và **Tổng quan Kho** đã dựng xong. §1.8 của `13`
nay đã ĐÓNG HẾT: dòng cuối (chi tiết YCBG thiếu nút _Xử lý khảo sát_) xong ở CR-222 ngày 29/08.
⚠️ **`/api/dashboard/overview` chỉ đòi đăng nhập, rồi gác TỪNG KHỐI bên trong bằng `can(entity)`
và BỎ HẲN khóa** khi thiếu quyền — nên đọc nhầm khóa của phân hệ khác thì không ai ăn 403, chỉ
thấy **0** vĩnh viễn. Mọi khóa trong `DashboardOverview.kpi` là **tùy chọn**, luôn đọc kèm `?? 0`.
Hai khóa dễ nhầm nhất: `top_suppliers` = **CHI TIÊU** theo NCC _(khối `purchase_order`)_, còn
`top_debt_suppliers` = **NỢ CÒN LẠI** _(khối `payable`)_. Xem `test/backend/test_tong_quan_thu_mua.py`.
Màn **Công nợ đã đủ** cột tick chọn + nút _Tạo đề nghị thanh toán_ từ Đ-09 (CR-119).
**Đã xong MC-1…MC-4** (CR-094): Đặt lại mật khẩu · Thông báo (`/notifications`) · Trang cá
nhân (`/me`) · Cấu hình hệ thống (`/system/settings`, phân hệ Quản trị nay **bật**).
**Đã xong Đ-01** (CR-098): Dựng khung Generic Declarative CRUD (`frontend-v2/src/shared/crud/`)
kế thừa 3 cấp độ (CrudListPage + CrudDetailPage có RecordIdentityCard + AuditTimeline + hỗ trợ tabs/bảng con DataTable + CrudFormDialog) và dời Danh mục Kho (`/inventory/warehouses` và `/inventory/warehouses/:id`).
**Đã xong Đ-02** (CR-099): Dời Đơn vị tính (`/production/units` + `/production/units/:id`) và Phân loại VTBB/NL (`/production/item-groups` + `/production/item-groups/:id`) sang `frontend-v2` kế thừa 100% tầng generic CRUD, gắn vào phân hệ Sản xuất.
**Đã xong Đ-03** (CR-100): Dời Sản phẩm & Vật tư (`/production/products` + `/production/products/:id`) sang `frontend-v2` có tab _Lịch sử mua hàng_ (`PurchaseHistoryTable` với `DataTable` riêng, ẩn/hiện cột NCC theo quyền `supplier.read`, link sang ĐMH và gắn `AuditTimeline`).
**Đã xong Đ-05** (CR-106): **Nhà cung cấp** — danh sách `/production/suppliers` dời sang khung CRUD
khai báo (`production/config/supplier-crud.tsx`) và dựng `/production/suppliers/:id` **5 tab** đúng
bản cũ: _Thông tin_ · _Hợp đồng_ · _Công nợ & Đánh giá_ · _Lịch sử mua hàng_ · _Khảo sát của NCC_
(kế hoạch `erp/13` ghi "3 tab" là đếm sai, đã đính chính). Đây là màn danh sách **cuối cùng** còn tự
ghép `<Table>`. Khung CRUD nay có kiểu trường **`percent`** (`shared/crud/field-values.ts`) — dùng nó
cho VAT, đừng tự nhân chia 100 ở tầng màn: `Supplier.vat` lưu **tỷ lệ** `0.08` chứ không lưu `8`
(CR-058). ⚠️ **Tab mượn dữ liệu của phân hệ khác thì phải tự tắt khi thiếu quyền** — `usePayables`,
`usePayableSummary`, `useCompanies` không có nhánh tắt, cứ mount là gọi và người dùng ăn toast 403
ngay lúc mở tab; truyền `enabled` hoặc bọc bằng `can(...)` trước khi dựng component con.

_Tiến độ mua hàng_ và _Phân quyền_ thì **đã có ở v2** rồi
(`procurement/pages/purchase-progress-page.tsx`, `hr/pages/role-permission-page.tsx` +
`user-permission-detail-page.tsx`) — danh sách cũ ghi sai.
Vừa dời xong: **chi tiết Phiếu khảo sát** (`procurement/pages/survey-detail-page.tsx`, xem
CR-091), **chi tiết Yêu cầu báo giá** (`procurement/pages/survey-request-detail-page.tsx` —
nút _Xử lý khảo sát_ đã có từ CR-222, dẫn sang trang riêng), **Công nợ**
(`finance/pages/payable-list-page.tsx` — cột tick chọn đã có lại ở Đ-09/CR-119),
**Tồn kho** (`inventory/pages/inventory-list-page.tsx`) và **Báo cáo mua hàng**
(`procurement/pages/purchase-report-page.tsx` — tám tab, dữ liệu vẫn gom theo TÊN phòng
ban / NSPT, xem N-008 trong `doc/tai-lieu-ky-thuat/change-log.md`).
