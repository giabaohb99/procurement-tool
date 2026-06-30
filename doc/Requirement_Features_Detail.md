# Requirement chi tiết theo chức năng — Mini Tool Thu Mua

> Mục tiêu: mỗi chức năng mô tả rõ **Giao diện (FE)** · **Backend (BE)** · **Tiêu chí ĐẠT (acceptance)**, và mỗi **Phase** có **Định nghĩa ĐẠT (DoD)**. Dùng để giao 2 subagent (FE & BE) thực thi song song.
> Trạng thái: ✅ đã làm · 🟡 một phần · ⏳ chưa làm.

---

## A. QUY ƯỚC CHUNG (áp dụng MỌI chức năng)

**Giao diện**
- Mỗi thực thể có **màn List** (bảng + filter động + phân trang + nút Thêm) và **màn Detail theo route** `/{slug}` & `/{slug}/{id}` (KHÔNG dùng popup cho detail).
- Màn Detail: bố cục **theo section** (card), trường dạng lưới 2 cột; có **nút hành động gom ở thanh đầu trang**; có **Lịch sử thao tác** (timeline) bên phải; có **Đính kèm** nếu áp dụng.
- Bảng con (line items): **sửa inline trên dòng**, **kéo ngang** (overflow-x), nút **Thêm dòng / Thêm nhiều**, **Thành tiền tự tính**.
- Dropdown lấy từ **danh mục thật** (không gõ tay): Công ty, Kho, ĐVT, Phân loại, NCC…
- Style: tông teal/navy, font Inter, badge trạng thái, responsive ≤820px (sidebar drawer).

**Backend**
- Mỗi chức năng = 1 module `app/modules/<feature>/` gồm `controller · model · schema · service`; dùng chung ở `core/`.
- API envelope: `{ "success": true, "data": ... }` / `{ "success": false, "error": {code,message} }`.
- Auth: Bearer **access token** (refresh khi 401). RBAC: `require(entity, action)` cho mọi endpoint.
- Quy ước DB: `id` BIGINT; code `VARCHAR(25/50)`; note/JSON `TEXT`; tiền `DECIMAL(18,2)`, SL `DECIMAL(18,3)`; `parent=0` gốc; mọi bảng có `created_at/by, updated_at/by`.
- Mọi create/update/delete & đổi trạng thái: **ghi audit log**.

**Tiêu chí ĐẠT chung cho 1 chức năng (CRUD)** — phải pass hết:
- [ ] List: hiển thị + **filter đúng** + **phân trang** (page/limit) + nút Thêm.
- [ ] Detail: tạo/sửa/xóa chạy; validate lỗi trả message tiếng Việt rõ; readonly khi không có quyền.
- [ ] **RBAC**: thiếu quyền → ẩn nút (FE) + chặn 403 (BE).
- [ ] **Audit log** ghi đúng người/hành động/thời gian, hiển thị ở Detail.
- [ ] UI khớp mô tả + responsive; không lỗi console.

---

## B. ĐỊNH NGHĨA "ĐẠT" THEO PHASE (DoD)

- **Phase 0 — Nền tảng (✅):** đăng nhập (access+refresh) + RBAC chặn route; CRUD Company/Department/Employee/User/Role; Dashboard rỗng; Docker `up` chạy 1 phát; audit log + rate-limit + CORS.
- **Phase 1 — Danh mục + Khảo sát (🟡):** ĐẠT khi: Supplier, Product, 4 danh mục (Kho/ĐVT/Phân loại/Thương hiệu), **PYC** (đủ luồng + in + đính kèm), **Survey NCC + SP** (form + bảng con + LAB + duyệt), **Quy đổi ĐVT**, **Email cơ bản** — tất cả pass acceptance của từng chức năng.
- **Phase 2 — Mua hàng + GR:** ĐẠT khi tạo **PO** từ NCC đã duyệt → duyệt → in PO → **giao nhiều lần + vận chuyển (chi phí riêng)** → **nhận hàng (GR)** cập nhật **tồn kho**.
- **Phase 3 — Cảnh báo & thông báo:** ĐẠT khi Celery+Beat chạy: nhắc D-1, cảnh báo trễ hạn, công nợ tới hạn, HĐ hết hạn; trung tâm thông báo + email log/retry.
- **Phase 4 — Công nợ · Báo cáo · Hợp đồng:** ĐẠT khi công nợ 2 luồng + thanh toán gom; báo cáo (snapshot) xuất Excel; hợp đồng + cảnh báo hết hạn.
- **Phase 5 — Quản trị nâng cao:** cấu hình ngưỡng duyệt, mẫu in, danh mục dùng chung UI, audit log UI, sao lưu, (tùy chọn MISA).

---

## C. CHI TIẾT TỪNG CHỨC NĂNG

### C1. Đăng nhập & Phân quyền (Phase 0) ✅
**FE:** màn Login (mã NV + mật khẩu); lưu access+refresh; interceptor tự refresh khi 401 → hết hạn về login. Màn **Quản trị → Phân quyền**: ma trận Vai trò × Đối tượng × (Xem/Tạo/Sửa/Xóa/Duyệt/In/Xuất) + scope (own/dept/all).
**BE:** `POST /auth/login` (rate-limit) · `POST /auth/refresh` · `GET /auth/me` (trả permissions map). `tab_user/role/permission/user_role`. `require(entity,action)`.
**ĐẠT:** [ ] đăng nhập đúng/sai rõ ràng · [ ] hết hạn token tự refresh · [ ] đổi quyền 1 vai trò → user thuộc vai trò đó bị ẩn/chặn đúng · [ ] brute-force >10 lần/phút bị chặn.

### C2. Tổ chức: Công ty · Phòng ban · Nhân viên · Tài khoản (Phase 0) ✅
**FE:** 4 màn List + Detail (CRUD). Company/Department có **cây `parent`**. Employee gắn company/department. Màn Tài khoản: cấp tài khoản cho nhân viên + đặt lại mật khẩu (quyền HR/Admin).
**BE:** `tab_company/department/employee/user`. CRUD chuẩn + `POST /users` (provision) + `/users/{id}/reset-password`.
**ĐẠT:** theo acceptance chung + [ ] tạo nhân viên → cấp tài khoản → đăng nhập được · [ ] reset mật khẩu hoạt động.

### C3. Danh mục: Kho · ĐVT · Phân loại · Thương hiệu (Phase 1) ✅
**FE:** 4 màn List + Detail CRUD (generic). Phân loại có cột **Số ngày quy định** + Ngày áp dụng.
**BE:** `tab_warehouse/unit/item_group/brand` (generic CRUD). Seed từ `seed_data/*.json`.
**ĐẠT:** acceptance chung + [ ] dropdown các form khác lấy được danh mục này.

### C4. Nhà cung cấp (Phase 1) ✅
**FE:** List (filter mã/tên/MST/loại) + Detail. Trường: mã, tên pháp lý, MST, địa chỉ, **loại (goods/transport)**, hình thức thanh toán, VAT, trạng thái.
**BE:** `tab_supplier` (`supplier_type`). CRUD + filter. Seed 147 NCC từ JSON.
**ĐẠT:** acceptance chung + [ ] lọc theo loại bán hàng/vận chuyển.

### C5. Sản phẩm / Hàng hóa (Phase 1) ✅
**FE/BE:** `tab_product` (mã NLNK/NLT/BTPM…, tên, tên hóa đơn, phân loại, ĐVT). CRUD + filter.
**ĐẠT:** acceptance chung.

### C6. Yêu cầu mua — PYC (Phase 1) ✅ (lõi)
**FE — Detail (trang riêng):**
- Section *Thông tin chung*: Mã số (tự sinh `PYC#####`), Ngày tạo, Người yêu cầu*, Chức vụ, Phòng ban/Thương hiệu*, Trưởng bộ phận, Công ty nhận hóa đơn* (dropdown), Ngày cần hàng, VAT(%), Đơn gấp, Mục đích*.
- Section *Mặt hàng*: **bảng inline kéo ngang** — Mã vật tư, Tên vật tư*, Phân loại(dropdown), ĐVT(dropdown), Số lượng, Giá đề xuất, **Thành tiền (auto)**, Kho nhận(dropdown), NSPT, Trạng thái dòng. Nút **Thêm dòng / Thêm nhiều**. **Tổng tiền / VAT / Tổng thanh toán** auto.
- Section *Ghi chú* + *Chứng từ đính kèm* (nhiều file → R2).
- Thanh đầu: **Lưu · Gửi duyệt · Duyệt · Từ chối · In phiếu · Xóa** (theo trạng thái + quyền).
- **In phiếu** Mẫu 003/BM/PKT (trang in riêng).
**BE:** `tab_purchase_request` (+ `_item`). Trạng thái **Nháp → Chờ duyệt → Đã duyệt / Từ chối**. `POST /{id}/submit|approve|reject`. Chỉ sửa khi Nháp/Từ chối. Tính subtotal/vat/total ở `_out`.
**ĐẠT:** [ ] tạo PYC + nhiều dòng inline · [ ] tổng tiền đúng · [ ] gửi duyệt → duyệt/từ chối (chỉ người có quyền approve) · [ ] in ra phiếu đúng mẫu · [ ] đính kèm + xem lại file · [ ] log đủ các mốc.

### C7. Khảo sát Nhà cung cấp (Phase 1) ⏳
**Mục đích:** đánh giá NCC (so sánh nhiều NCC trong 1 phiếu) trước khi duyệt.
**FE — Detail (trang riêng), 3 section:**
1. *Tiếp nhận*: Mã yêu cầu (PYC)*, Ngày tiếp nhận, Nhóm hàng (select: Bao bì/Nguyên liệu/In ấn/Chai lọ/Hóa chất), Yêu cầu chi tiết (textarea).
2. *Bảng khảo sát NCC* — **bảng con inline/kéo ngang**, mỗi dòng 1 NCC: Tên NCC*, MST, SĐT, Người liên hệ, Nhóm SP cung ứng, Địa chỉ kho, Link Google Maps, Link báo giá (Drive), Chính sách công nợ (select: Tiền mặt/CN 30/CN 60/Trả trước), Chính sách hóa đơn, **Mức độ tin cậy** (select: Cao/TB/Thấp), Thời gian SX, Chính sách giao nhận, **Đánh giá NSPT** (select: Đạt/Không đạt).
3. *Phê duyệt*: Duyệt (TP/QL) (select Duyệt/Không duyệt), Ghi chú duyệt.
- Tự tính: số NCC, NCC chính (dòng đầu). List cột: Mã YC, Ngày, NCC chính, Số NCC, Duyệt.
**BE:** `tab_survey` (header: code/maYc, survey_type='supplier', nhom_hang, yeu_cau, duyet_tp, ghi_chu_duyet, status) + `tab_survey_supplier_line` (các field NCC trên). `POST /{id}/approve|reject`. Liên kết PYC qua `pr_code`.
**ĐẠT:** [ ] tạo phiếu + thêm ≥2 NCC inline · [ ] chọn mức tin cậy/đánh giá NSPT · [ ] duyệt/không duyệt + ghi chú · [ ] auto đếm số NCC & NCC chính · [ ] log đầy đủ.

### C8. Khảo sát Sản phẩm (Phase 1) ⏳
**FE — Detail 3 section** (giống C7, đổi bảng con):
- *Bảng khảo sát SP* — mỗi dòng 1 SP: Tên SP*, NCC*, Thông số kỹ thuật, Xuất xứ, ĐVT báo giá, MOQ, Khung SL, Giá theo khung, VAT(%), Số lượng YC, Phí vận chuyển, Thời gian giao, **Kết quả LAB** (select Đạt/Không đạt). **Thành tiền auto** = SL×Giá×(1+VAT/100).
**BE:** `tab_survey` (survey_type='product') + `tab_survey_product_line`. Có thể quy đổi ĐVT (xem C9).
**ĐẠT:** [ ] thêm nhiều SP inline · [ ] thành tiền auto đúng · [ ] kết quả LAB · [ ] duyệt + log.

### C9. Quy đổi ĐVT (Sheet 5) (Phase 1) ⏳
**FE:** màn danh mục `tab_unit_conversion` (mã hàng, ĐVT NCC, ĐVT nội bộ, hệ số). Trong Khảo sát SP: nếu có hệ số → tự quy đổi giá về ĐVT nội bộ; không có → cho nhập tay.
**BE:** `tab_unit_conversion` + hàm `convert(price, code)`.
**ĐẠT:** [ ] giá quy đổi hiển thị đúng · [ ] chặn trình duyệt nếu chưa quy đổi (cảnh báo).

### C10. Đơn mua hàng — PO (Phase 2) ⏳
**FE — Detail (trang riêng):**
- Header: Mã PO/Mã MISA, NCC (dropdown), Công ty hóa đơn, Ngày đặt, Trạng thái, Ghi chú.
- *Dòng hàng (inline)*: SP, ĐVT, **SL đặt NCC**, đơn giá, VAT, **thành tiền auto**.
- *Giao hàng (bảng con, nhiều lần)*: mỗi lần giao — Kho nhận, **Đơn vị vận chuyển (NCC transport)**, SL gửi, ĐVT VC, **SL đã nhận**, Ngày nhận, **Đơn giá VC + Thành tiền VC (riêng)**, Trạng thái.
- Nút: Lưu · Duyệt PO · **In PO gửi NCC** · Cập nhật giao nhận.
**BE:** `tab_purchase_order` (+`_item`) + `tab_po_delivery`. Trạng thái **Nháp → Chưa đặt → Đã đặt → Đang giao → Đã nhận đủ → Hoàn thành/Hủy**. Chi phí vận chuyển **không cộng vào giá hàng**. `supplier_type=transport` cho đơn vị VC.
**ĐẠT:** [ ] tạo PO + duyệt + in · [ ] 1 dòng hàng **giao nhiều lần** · [ ] chi phí VC tách riêng · [ ] cảnh báo trễ hạn (chênh lệch ngày).

### C11. Nhận hàng & Kiểm tra — GR (Phase 2) ⏳
**FE:** từ PO/đợt giao → màn nhận: đối chiếu PO, nhập **SL thực nhận**, kết quả QC (Đạt/Lỗi), đính kèm phiếu giao hàng + hóa đơn; nút Duyệt chứng từ → nhập kho. Tồn kho đơn giản theo kho.
**BE:** `tab_goods_receipt`(+`_item`), `tab_inventory(+move)` theo `company`. Tiêu chí chấp nhận theo `tab_tolerance_rule` (±% & số ngày kiểm theo NCC).
**ĐẠT:** [ ] nhận hàng cập nhật SL đã nhận + tồn kho · [ ] xử lý thiếu/lỗi/trả · [ ] công nợ ghi theo **SL thực nhận**.

### C12. Công nợ & Thanh toán (Phase 4) ⏳
**FE:** màn công nợ (2 luồng: **hàng** / **vận chuyển**); nút **Thanh toán ngay trên màn** (nhập số tiền + đính kèm chứng từ); thanh toán **gom nhiều công nợ** (DNTT theo tháng) hoặc theo đơn.
**BE:** `tab_payable(source_type=goods|shipping)`, `tab_payment(+line)`.
**ĐẠT:** [ ] 2 luồng công nợ riêng · [ ] 1 phiếu gom nhiều công nợ · [ ] đính kèm chứng từ.

### C13. Báo cáo (Phase 4) ⏳
**FE:** Báo cáo tiến độ, KPI NSPT, đánh giá NCC, chi phí; **xuất Excel**.
**BE:** **bảng snapshot** `tab_report_*` do **worker** cập nhật khi có action (không tính lúc mở màn → không treo).
**ĐẠT:** [ ] mở báo cáo nhanh (đọc snapshot) · [ ] xuất Excel đúng số liệu.

### C14. Dashboard (Phase 0) ✅
**FE:** thẻ chỉ số (NCC, SP, YC chờ duyệt, nhân viên) + thao tác nhanh + (sau) biểu đồ trạng thái.
**BE:** `GET /dashboard/stats`.
**ĐẠT:** [ ] số liệu đúng · [ ] bấm thẻ điều hướng.

### C15. Xuyên suốt: Đính kèm (R2) · Audit log · Thông báo email
- **Đính kèm:** `tab_attachment` đa hình + R2; mọi thực thể đính kèm nhiều file; xem **bộ chứng từ theo đơn**. ✅ (đã có ở PYC)
- **Audit log:** `tab_audit_log`; hiển thị timeline ở Detail. ✅
- **Email (Phase 1 cơ bản → Phase 3 đầy đủ):** trigger giao việc/chờ duyệt/kết quả; sau dùng Celery Beat nhắc lịch. ⏳
  **ĐẠT (email cơ bản):** [ ] gửi được email ở 3 mốc (giao việc, chờ duyệt, kết quả) · [ ] có log gửi.

---

## D. PHÂN CÔNG 2 SUBAGENT (gợi ý)
- **Subagent BE:** theo mục "Backend" + "Tiêu chí ĐẠT" mỗi chức năng; mỗi module = `controller/model/schema/service`; dùng `core/crud.py` cho danh mục; viết test nhanh qua `/docs`.
- **Subagent FE:** theo mục "Giao diện"; tái dùng `CrudList/CrudDetail` cho thực thể đơn giản; trang Detail riêng (PYC/Survey/PO) theo mẫu PurchaseRequestDetail (section + bảng inline kéo ngang).
- **Hợp đồng API** giữa 2 bên: envelope `{success,data}`, list trả `{total,items}`, lỗi `{success:false,error:{message}}`, action `POST /{id}/{verb}`.
