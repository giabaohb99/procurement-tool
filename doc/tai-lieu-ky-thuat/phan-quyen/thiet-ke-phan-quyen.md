# Thiết kế Phân quyền (RBAC + Phạm vi dữ liệu)

> Viết cho người không chuyên. Chốt cách phân quyền cho ~20 người dùng nội bộ DEGO.
> Ý tưởng gốc của anh: *khi cấp tài khoản, chọn phạm vi — admin = tất cả công ty; phòng thu mua =
> vài công ty; nhân sự = một phòng ban*. Tài liệu này biến ý đó thành thiết kế cụ thể.

---

## 1. Có 2 lớp quyền (tách riêng, đừng trộn)

**Lớp A — Quyền HÀNH ĐỘNG (theo VAI TRÒ):** vai trò được *làm gì* trên từng chức năng.
Ví dụ vai trò "Nhân viên thu mua": Xem + Tạo + Sửa trên Yêu cầu mua & Đơn mua hàng; KHÔNG được Duyệt.
→ Đây là **ma trận quyền** (giống ảnh Frappe anh gửi).

**Lớp B — PHẠM VI dữ liệu (theo NGƯỜI DÙNG):** người đó được *thấy dữ liệu của ai*.
Ví dụ: cùng vai trò "Nhân viên thu mua" nhưng anh A phụ trách **Công ty 1 & 2**, anh B chỉ **Phòng Sản xuất**.
→ Đây là cái anh mô tả: lúc cấp tài khoản thì tick công ty/phòng ban được phụ trách.

> Nguyên tắc: **Hành động gắn vào VAI TRÒ. Phạm vi gắn vào NGƯỜI DÙNG.**
> Vì 2 người cùng vai trò nhưng phạm vi khác nhau.

---

## 2. Bộ hành động (rút gọn — không bê 16 cột của Frappe)

Giữ gọn, đủ dùng cho nội bộ:

| Cờ | Nghĩa |
|---|---|
| Xem | đọc/danh sách |
| Tạo | thêm mới |
| Sửa | chỉnh sửa |
| Xóa | xóa |
| Duyệt | gửi duyệt / phê duyệt / từ chối |
| Hủy | hủy chứng từ (cancel) |
| In | in chứng từ |
| Xuất | xuất Excel/CSV |

→ Tổng **8 hành động**: Xem · Tạo · Sửa · Xóa · Duyệt · Hủy · In · Xuất.

Bỏ các cột thừa của Frappe: Select, Amend, Share, Email, và **Level (phân quyền theo từng ô/field)** — quá phức tạp, không cần.
Giữ khái niệm **"Chỉ của mình" (own)** như một lựa chọn phạm vi (xem mục 4).

---

## 3. Mô hình dữ liệu

### Đã có sẵn (Lớp A)
- `Role` (vai trò): mã, tên, mô tả — **tạo/sửa/xóa được**.
- `Permission`: theo (vai trò × chức năng) với các cờ `can_read/create/write/delete/approve/print/export`.
- `User` ↔ `UserRole` ↔ `Role`: 1 người có thể nhiều vai trò.

### Thêm mới (Lớp B) — PHẠM VI GẮN VÀO TỪNG "DÒNG PHÂN QUYỀN" (grant)

Thay vì 1 phạm vi chung cho cả người, **mỗi người có NHIỀU dòng phân quyền**, mỗi dòng =
**1 vai trò + phạm vi riêng của dòng đó**. (Mở rộng bảng `UserRole` hiện có thành "grant".)

| Cột (mỗi dòng grant) | Ý nghĩa |
|---|---|
| user_id | người dùng |
| role_id | vai trò của dòng này |
| company_ids | công ty áp cho dòng này (trống = tất cả) |
| department_codes | phòng ban áp cho dòng này (trống = tất cả) |
| own | chỉ bản ghi do chính mình tạo |

**Vì sao tách theo dòng:** để cấp *quyền khác nhau trên phạm vi khác nhau* cho cùng 1 người.
Đây chính là tình huống: "xử lý yêu cầu của phòng **Sản xuất**, nhưng còn được **duyệt** cho phòng **IT**".

Quy ước:
- Trống cả company & department ở 1 dòng = dòng đó không giới hạn phạm vi.
- Quyền hiệu lực = **HỢP (OR) của mọi dòng**: được làm hành động X trên bản ghi R nếu **tồn tại ≥1 dòng**
  mà (vai trò của dòng có quyền X trên chức năng đó) **và** (phạm vi dòng đó chứa R).
- Admin: 1 dòng vai trò Admin, để trống phạm vi ⇒ full.

---

## 4. Cách hệ thống thực thi (enforcement)

1. **Chặn hành động (Lớp A):** mọi API đã đi qua `require(entity, action)` — nếu vai trò không có cờ → chặn (đang chạy).
2. **Lọc phạm vi (Lớp B):** hàm `scope_query(query, entity, action, user)` áp vào **danh sách + chi tiết**:
   - Lấy các **dòng grant** của user mà vai trò có quyền `action` trên entity này.
   - Với mỗi grant, dựng điều kiện phạm vi (company_ids / department_codes / own) theo cột entity có.
   - Kết quả = **OR các điều kiện đó** (hợp các dòng). Không grant nào phù hợp → không thấy gì.
3. **Chặn ghi ngoài phạm vi:** khi tạo/sửa, không cho gán company/department ngoài phạm vi được cấp.

### Chức năng nào lọc theo chiều nào
| Chức năng | company_id | department | own |
|---|---|---|---|
| Đơn mua hàng (PO) | ✓ | ✓ | ✓ |
| Yêu cầu mua (PYC) | ✓ | ✓ | ✓ |
| Công nợ / Thanh toán | ✓ | – | – |
| Tồn kho | ✓ | – | – |
| Nhà cung cấp, Sản phẩm, Danh mục | (dùng chung, thường không giới hạn) | – | – |
| Báo cáo / Dashboard | ✓ (số liệu chỉ trong phạm vi) | ✓ | – |

> Ghi chú: Danh mục dùng chung (NCC, sản phẩm, kho…) **không lọc theo phạm vi**; nhưng vẫn theo quyền Xem (mục dưới).

### Ẩn/hiện menu theo quyền (theo ý anh: "được xem ở đâu thì hiện ra đó")
- **Mục menu sidebar chỉ hiện nếu user có quyền Xem** entity đó. Không có quyền Xem → ẩn khỏi menu.
- Cụm menu (Mua hàng / Kho & Công nợ / Danh mục…) tự ẩn nếu không còn mục con nào.
- Ngoài ẩn menu, backend vẫn chặn truy cập trực tiếp bằng `require()` (an toàn 2 lớp).

---

## 4b. Lớp gác thứ ba — Quyền xem TỪNG báo cáo (duoc-CR-562, 2026-10-02)

Gác riêng 13 báo cáo của phân hệ Báo cáo (Thu mua 5 · Nhân sự 3 · Hành chính 2 · Văn bản/Phê duyệt 2 · Công việc 1).

1. **Gác kép.** 26 đường `/summary` + `/summary/export` đòi CÙNG LÚC:
   - quyền của phân hệ gốc như cũ — `require(entity, 'read'|'export')` + `apply_scope` (entity: `report`, `survey_request`, `purchase_request`, `survey`, `employee`, `leave_request`, `leave_balance`, `vehicle_booking`, `seal_request`, `document`, `approval_flow`, `work_task`);
   - **và** được gán xem báo cáo đó — `dependencies=[Depends(require_report(ReportKey.X))]` (`modules/report_access/guard.py`).
   - Thiếu một trong hai → 403 (**Chưa được giao xem báo cáo: <tên>**). Gán thêm KHÔNG mở rộng dữ liệu.
**Phạm vi (đại ca chốt 02/10/2026):** quyền này CHỈ quyết định ai xem được trang báo cáo trong phân hệ Báo cáo (`/report/*` và 26 đường `/summary` của nó). Màn BẢNG gốc ở từng phân hệ (vd **Báo cáo mua hàng**, **Chi tiết YC mua hàng** bên Thu mua, cả bản cũ `thumua`; bảng dòng Tiến độ báo giá/mua hàng, Báo cáo khảo sát) vẫn chỉ theo quyền vai trò (`report.read`, …) — không phải lỗ, là phạm vi đã chọn. Muốn chặn cả màn gốc thì phải gác thêm các đường API cũ (lưu ý `/api/reports/matrix` còn được phân hệ Sản xuất dùng).
2. **Chưa gán = đóng.** Báo cáo không có dòng CHO PHÉP nào khớp người dùng → không xem được.
3. **Khóa báo cáo** `ReportKey` (IntEnum, `core/report_keys.py`, SMALLINT theo R2/QĐ-11). Số đã cấp không đổi, không tái dùng. Frontend nhận bản sinh `REPORT_KEY` qua `gen_status_ts.py`; test so khóa + nhãn catalog với bản sinh.
4. **Bảng `tab_report_access`** — cùng hình dạng `tab_doc_folder_access`, dùng lại `core/subject_match.py`:
   `report_key` · `subject_kind` (1 người · 2 phòng ban · 3 pháp nhân · 4 vai trò) · `subject_id` · `effect` (1 cho phép · 2 cấm) · `valid_from`/`valid_to` (chưa hiện trên giao diện) · `reason` · `revoked_at`/`revoked_by`/`revoke_reason`.
5. **CẤM thắng CHO PHÉP.** Kết quả = hợp các dòng cho phép còn hiệu lực, trừ mọi dòng cấm còn hiệu lực.
6. **Thu hồi = đánh dấu `revoked_at`**, không xóa dòng; giao diện chỉ hiện dòng còn hiệu lực. Mọi thay đổi ghi audit.
7. **Mặc định admin.** Migration `rptacc01` chèn 1 dòng CHO PHÉP cho vai trò `admin` ở mỗi báo cáo. `ensure_report_access_defaults` (gọi trong `seed.py` và `seed_prod.py`) chỉ chèn dòng admin cho khóa CHƯA TỪNG có dòng nào (kể cả dòng đã thu hồi, kể cả dòng của chủ thể khác) → báo cáo mới tự có admin, chỉnh sửa của người dùng không bị đè.
8. **Cấu hình:** thẻ **Báo cáo** ở Cài đặt › Phân quyền tài khoản (cạnh **Vai trò & quyền**, **Người dùng**). Xem cần `role.read`, gán/thu hồi cần `role.write`. API `/api/report-access`. Không thêm entity mới.
9. **Frontend:** `report_keys` trong `/api/auth/me`; menu, route gõ thẳng, trang Tổng quan và dải KPI chỉ hiện báo cáo có khóa trong đó. Thiếu `report_keys` (thông tin đăng nhập cũ còn trong trình duyệt) = đóng → sau deploy người dùng phải đăng nhập lại.

---

## 4c. Kiêm nhiệm — phạm vi theo hai loại dòng Phòng ban / Công ty (duoc-CR-755, mô hình sửa ở duoc-CR-756, 13/11/2026)

Kế hoạch: `doc/erp/hrm/plans/261112-kiem-nhiem-khac-cong-ty-duoc-cr-755/` (tab riêng, ngày, công tắc) và
`doc/erp/hrm/plans/261113-kiem-nhiem-phong-ban-cong-ty-doc-lap-duoc-cr-756/` (hai loại dòng). Bảng nguồn:
`tab_employee_concurrent` (cột `kind`). Mã: `core/auth.py` (hồ sơ quyền), `core/scoping.py`, `core/subject_match.py`,
`doc_catalog/folder_access_service.py`. Luật nghiệp vụ: `doc/erp/hrm/01-ho-so-nhan-su.md` §7.18.

Mô hình CẶP (phòng, công ty) của duoc-CR-755 (khóa `concurrent_pairs`, `_pair_conds`) **đã bỏ**. Người chủ chốt 13/11/2026:
*anh A kiêm nhiệm phòng ban A và công ty B; phòng ban thuộc công ty hiện tại* — hai loại dòng độc lập.

**Hồ sơ quyền.** Dòng kiêm nhiệm **còn hiệu lực hôm nay (giờ VN, `vn_today()`)** và **bật công tắc "Tính vào phạm vi quyền"**
được tách làm hai nhóm, trong CÙNG một truy vấn (số truy vấn không đổi theo số dòng):

| Loại dòng | Vào đâu | Hệ quả |
|---|---|---|
| 1 **Phòng ban** (phòng của công ty chính; `company_id` = công ty chính hoặc 0 ở dữ liệu cũ) | `dept_ids` (như CR-167) | Mọi đường theo phòng thấy phòng đó. Dòng loại 1 lệch công ty chính (dữ liệu trôi) bị bỏ qua + cảnh báo `app.scoping` |
| 2 **Công ty** (công ty khác, `department_id = 0`) | khóa `concurrent_companies` = danh sách công ty (xếp tăng, bỏ trùng, khác công ty chính) | Công ty B tính như công ty của người này ở bậc `company` và `dept` (bảng dưới) |

`company_id` của hồ sơ quyền **vẫn là MỘT số**; công ty kiêm nhiệm nằm riêng ở `concurrent_companies` và chỉ được cộng ở chỗ
có tên dưới đây. Hết hạn / sắp tới / tắt công tắc / bị loại trừ công ty B ở ô phạm vi: không cộng. Hồ sơ quyền cache 60 giây
theo tiến trình nên dòng hết hạn lúc 0h còn tác dụng tối đa 60 giây; bản cache cũ còn khóa `concurrent_pairs` thì mã mới bỏ
qua (đóng, không mở).

**Bậc nào thấy gì thêm** (`_own_companies(profile)` = công ty chính + `concurrent_companies`; `_company_in_cond` dùng `==` khi
chỉ một công ty để SQL người không kiêm nhiệm không đổi, nhiều công ty thì `IN`):

| Đường / bậc | Công ty kiêm nhiệm B cộng gì | Cách |
|---|---|---|
| Bậc `company` (`_role_scope_cond`) | Mọi phiếu / hồ sơ của B | `công ty IN (chính, *B)` (kèm cột `company_alt` nếu entity có). Chưa gắn pháp nhân mà có công ty kiêm nhiệm thì dùng danh sách đó, không chặn |
| Bậc `dept` | Phiếu của các phòng của họ tại B | `công ty IN (chính, *B) AND phòng IN dept_ids` |
| Duyệt dấu — Giám đốc (bậc `company`, chỉ `read`) | Phiếu đã duyệt có B trong bảng nối `tab_seal_request_company` | `_SRC.company_id IN (chính, *B)` |
| Duyệt dấu — Văn thư (bậc `company` + `write`) | KHÔNG | theo bảng phân công `tab_seal_clerk`, không theo hồ sơ |
| Bậc `dept_proc` (YCMH, YCBG, đặt xe `_narrow_to_dept`; ĐMH `_handler_match`; entity khác rơi về bậc phòng), `holds_handling_dept` (nút Chuyển phòng xử lý / Trả về thu mua) | KHÔNG cần | các nhánh này vốn KHÔNG ràng công ty (bao-CR-434) nên `dept_ids` đã phủ phòng của họ ở mọi công ty |
| Bậc `own` (kể cả entity không có cột chủ, rơi về bậc công ty — cờ `own_fallback`) | KHÔNG | nhánh rơi chỉ dùng công ty CHÍNH |
| Bậc `assigned`, `proc`, `all` | KHÔNG | |
| Ô "Phòng ban được xem" (`_dept_include_cond`) | KHÔNG | đọc `tab_user_scope` do quản trị chọn, không đọc kiêm nhiệm |
| ACL theo chủ thể (`subject_match`: văn bản, thư mục, báo cáo, skill AI) — chốt Q3 | CÓ | `subject_pairs` cộng `(SUBJECT_COMPANY, B)` cho mỗi B; phòng loại 1 đã nằm trong `dept_ids` |
| Tạo văn bản / thư mục cho công ty nào (`folder_access_service.company_reach`) | CÓ cho grant bậc `company` / `dept` / `dept_proc` | `own` / `assigned` / `proc` không cộng |
| Bài diễn đàn đối tượng **Công ty** | KHÔNG (chưa làm) | `forum/service.py` so thẳng `profile.company_id`, không qua `subject_match` |

**Q6 — công tắc mở cả hành động.** Bật công tắc = được tính như người của phòng / công ty đó theo MỌI hành động vai trò sẵn có của
người đó, đúng bậc của từng vai trò: vai trò bậc `company` có ghi / duyệt thì ghi / duyệt được cả công ty B. Chốt là công tắc
từng dòng và L2 loại Công ty (người gán phải có grant `employee.write` bậc `all`, hoặc bậc `company` với B thuộc công ty chính
∪ công ty kiêm nhiệm của chính họ — bậc phòng ban không gán được loại Công ty). L2 loại Công ty xét TỪNG grant và tôn trọng ô
"Chỉ trong công ty" / "Loại trừ công ty" của grant đó, cùng luật với bộ lọc phạm vi (`scoping._explicit_cond`): grant `all` bị
giới hạn công ty A thì không gán được công ty C. Công ty đã ngừng hoạt động không gán được (L3). L2 loại Phòng ban đo theo cặp
(phòng, công ty chính của hồ sơ) với từng grant `employee.write` (`department_service.pair_in_write_scope`).

**N3 — nhật ký riêng, rủi ro chấp nhận (người chủ chốt 13/11/2026).** Luật gán giữ nguyên (chỉ cần quyền ghi hồ sơ ở công ty
B). Đổi lại, mỗi lần phạm vi của một dòng loại Công ty được MỞ hay ĐÓNG (tạo dòng bật công tắc, bật / tắt công tắc, nới / kết
thúc ngày, xóa) ghi một dòng nhật ký thao tác riêng, hành động `concurrent_scope_open` / `concurrent_scope_close` (khai ở
`core/action_catalog.py`, ghi ở `employee/concurrent_scope_audit.py`), để quản trị soi lại. Rủi ro chấp nhận: gán dòng loại Công ty + bật công tắc = mở
dữ liệu công ty B theo vai trò SẴN CÓ của người đó (kể cả sửa, duyệt), **không đi qua màn Phân quyền tài khoản**.

**Q3 — rủi ro chấp nhận.** Dòng ACL chia cho công ty B khớp mọi người kiêm nhiệm loại Công ty ở B (đang hiệu lực + bật công
tắc). Dòng ACL loại PHÒNG không mang công ty, nên phòng DÙNG CHUNG nhiều công ty: ACL cấp cho phòng X khớp mọi người có phòng
X trong `dept_ids`, kể cả qua dòng loại Phòng ban. Chốt tự cấp quyền báo cáo (`block_self_allow_grant`) cũng tính chủ thể kiêm
nhiệm (chặt hơn).

**Q1 — đọc HỒ SƠ người kiêm nhiệm (chỉ ĐỌC, mặc định TẮT).** `scope_condition` / `apply_scope` / `get_scoped` nhận
`include_concurrent: bool = False`; chỉ có tác dụng khi `entity == "employee"` và `action == "read"` (sửa / xóa / xuất / in
vẫn theo vị trí chính). Khi bật: `cond_cũ OR EXISTS(dòng kiêm nhiệm R của hồ sơ này, hiệu lực + bật công tắc, mà người xem phủ
chỗ ngồi của R)` (`_or_concurrent_exists`) — một subquery tương quan trong cùng câu SQL, không N+1. Chỗ ngồi
(`concurrent_row_visible_condition`): **R loại 1** ngồi ở (`R.department_id`, `R.company_id`); **R loại 2** ngồi ở (phòng chính
của người đó, `R.company_id`) HOẶC (phòng của một dòng loại 1 hiệu lực + bật D của cùng người, `R.company_id`). Phạm vi
`employee` của người xem áp lên chỗ ngồi đó như thể nhân sự ngồi ở đó (bậc `dept` → phòng thuộc `dept_ids` và công ty thuộc
công ty của người xem; bậc `company` → công ty thuộc công ty chính ∪ công ty kiêm nhiệm của người xem; ô chọn / loại trừ công
ty ăn theo cột công ty của dòng). Chỉ bật cờ ở đường đọc hồ sơ MỘT người và ở `can_open` của bảng người kiêm nhiệm; báo cáo,
danh sách `/api/employees`, sơ đồ (truy vấn gốc), xuất tệp, ghi giữ TẮT — bật mặc định là mọi báo cáo quân số tự kéo người
công ty khác vào màn này (sai luật không đếm trùng). Nhạy cảm vẫn che theo `employee_sensitive`, lương chỉ chính chủ.

Giới hạn đã biết: (1) loại trừ đích danh nhân sự (`tab_user_scope`, chiều `employee`) không có tác dụng ở entity `employee`
vì `SCOPE_FIELDS["employee"]` không khai `owner` — dòng kiêm nhiệm đi cùng luật của hồ sơ chính, không thêm không bớt;
(2) bậc `company` ở công ty B mở cả ghi / duyệt toàn B ở mọi phân hệ vai trò đó có — đó là ý của chốt, không phải lỗ.

---

## 5. Giao diện — một màn "Phân quyền" riêng (3 tab)

### Tab 1 — Vai trò
- Danh sách vai trò + nút **Thêm vai trò**. Mỗi dòng: tên, mô tả, số người dùng, nút sửa/xóa.

### Tab 2 — Ma trận quyền (chọn 1 vai trò)
- Bảng: **hàng = chức năng** (gom cụm: Mua hàng / Kho & Công nợ / Danh mục / Hệ thống), **cột = hành động** (Xem/Tạo/Sửa/Xóa/Duyệt/Hủy/In/Xuất) — ô tick.
- Tiện ích: tick cả dòng ("cấp mọi quyền chức năng này"), tick cả cột, nút Lưu.
- (Giống ảnh Frappe nhưng ít cột, gom nhóm cho dễ nhìn.)

### Tab 3 — Người dùng & phạm vi (Ma trận + chỉnh phạm vi từng dòng)
Chọn 1 người → màn gồm:
1. **Phạm vi tổng (mặc định):** Công ty [chip] + Phòng ban [chip]. Trống = tất cả. Áp cho **mọi chức năng** trừ dòng nào chỉnh riêng.
2. **Ma trận quyền theo chức năng:** hàng = chức năng, cột = 8 hành động (tick). Cuối mỗi dòng có cột **Phạm vi**:
   - Nhãn **Mặc định** (kế thừa phạm vi tổng) hoặc **Tùy chỉnh**, kèm nút **✏️**.
   - Bấm ✏️ → **popup có tiêu đề = tên quyền** (vd "Quyền: Yêu cầu mua hàng"):
     - Chọn **Dùng phạm vi tổng** *hoặc* **Tùy chỉnh riêng**.
     - Nếu tùy chỉnh, chọn **nhiều** ở từng cấp: **Công ty** → **Phòng ban** → **Nhân sự**, và **Loại trừ** (công ty / phòng ban / nhân sự).
     - Phạm vi này áp **CHUNG cho mọi hành động** của chức năng đó (bản này).
     - Lưu.
- Đa số dòng để **Mặc định**; chỉ dòng ngoại lệ mới ✏️.
- *Phiên bản sau:* tách phạm vi **theo từng hành động** (xem ở đâu · tạo ở đâu · duyệt ở đâu khác nhau).

> Đúng ý anh: cài phạm vi tổng 1 lần; chức năng nào cần khác thì ✏️ chỉnh riêng (bao gồm + loại trừ),
> không đụng thì tự lấy theo phạm vi tổng.

### Tab 4 — Người dùng (vòng đời tài khoản) — bổ sung theo CR-037, 2026-08-07

Danh sách tài khoản kèm bộ lọc **Tình trạng**: `Chưa gán vai trò` · `Mồ côi`. Mỗi dòng có nhãn
**"Mồ côi"** / **"Đã khóa"**, nút khóa–mở khóa, và nút xóa (**chỉ hiện với dòng mồ côi**).

- **Mồ côi** = tài khoản **không còn gắn hồ sơ nhân sự** (`employee_id` rỗng hoặc trỏ vào hồ sơ đã xóa).
  Sinh ra từ CR-023: xóa hồ sơ nhân sự thì hệ thống **chỉ khóa** tài khoản chứ không xóa.
- **Khóa ≠ xóa.** Ngưng cho một người dùng hệ thống thì **KHÓA**. Xóa hẳn chỉ dành cho tài khoản mồ côi.
- **Rào chắn khi xóa** (backend, không phải chỉ ẩn nút): không xóa chính mình · **không xóa tài khoản còn
  gắn hồ sơ nhân sự, kể cả khi đã khóa** (báo lỗi kèm đúng mã + tên nhân sự) · không xóa tài khoản quản trị
  duy nhất · không xóa nếu còn bảng nghiệp vụ nào ghi `created_by` = tài khoản đó (bắt buộc khóa thay vì xóa).
  Muốn bỏ hẳn thì **xóa hồ sơ nhân sự trước** — tài khoản tự khóa và thành mồ côi, lúc đó mới xóa được.
- **Nhật ký thao tác giữ nguyên** khi xóa tài khoản (lịch sử bất biến, chỗ hiển thị tên ghi "User #id");
  vai trò / phạm vi / thông báo / đăng ký push xóa theo.
- **Tài khoản mới không chọn vai trò thì tự nhận vai trò `employee` ("Nhân sự")** — áp cho cả 3 đường tạo:
  cấp tài khoản từ màn Nhân sự, `POST /api/users`, đăng nhập Google lần đầu. Vai trò cao hơn vẫn phải gán tay.
  (Trước CR-037 tài khoản mới không có quyền gì, đăng nhập vào thấy màn trắng.)

---

## 5b. Luồng thao tác (mô phỏng) — làm sao cho GỌN

Bí quyết để dễ: **cài quyền hành động 1 lần theo vai trò**, sau đó **cấp người dùng chỉ còn 3 cú chọn**.

### (A) Cài 1 lần cho mỗi vai trò — người quản trị làm lúc đầu
1. Menu **Phân quyền → tab Vai trò → "Thêm vai trò"** → gõ tên (vd "Nhân viên thu mua") → Lưu.
2. Sang **tab Ma trận quyền → chọn vai trò đó** → tick quyền. Có nút **tick cả dòng** nên rất nhanh:
   - Yêu cầu mua: Xem, Tạo, Sửa
   - Đơn mua hàng: Xem, Tạo, Sửa
   (không tick Duyệt vì nhân viên không được duyệt) → **Lưu**.
   → Mỗi vai trò làm ~30 giây, chỉ 1 lần.

> Hệ thống seed sẵn vài vai trò mẫu (Admin, Trưởng phòng thu mua, Nhân viên thu mua, Thủ kho,
> Kế toán công nợ) để dùng ngay, đỡ phải tạo từ đầu.

### (B) Cấp tài khoản hằng ngày — 1 dòng, 3 bước
Vào **tab Người dùng & phạm vi → chọn người** (hoặc Thêm) → ở **dòng phân quyền**:
1. **Chọn vai trò** (vd "Nhân viên thu mua") — quyền hành động tự áp theo vai trò.
2. **Chọn phạm vi** bằng chip: Công ty = [Cty 1, Cty 2] *hoặc* Phòng ban = [Sản xuất]. (Trống = tất cả.)
3. **Lưu**. Xong.

### (C) Cấp thêm quyền ngoại lệ — thêm 1 dòng
VD: bạn trên **còn được duyệt** phiếu yêu cầu của **phòng IT**:
- Bấm **＋ Thêm dòng phân quyền** → chọn vai trò có quyền **Duyệt** (vd "Người duyệt PYC")
  + Phòng ban = **IT** → Lưu.
- Kết quả: dòng 1 cho làm việc ở Sản xuất, dòng 2 cho duyệt ở IT. Hệ thống lấy **hợp** cả hai.

### Hình dung nhanh (tab Người dùng & phạm vi — dạng dòng)
```
Nguyễn Văn A                                              [ Lưu ]
──────────────────────────────────────────────────────────────
Dòng 1  Vai trò [ Nhân viên thu mua ▾ ]  Phòng ban [ Sản xuất ✕ ]  ☐ Của mình   🗑
Dòng 2  Vai trò [ Người duyệt PYC   ▾ ]  Phòng ban [ IT ✕ ]        ☐ Của mình   🗑
                                                          ＋ Thêm dòng phân quyền
(Công ty để trống = tất cả công ty)
```

---

## 6. Ví dụ tình huống (kiểm chứng thiết kế)

| Người | Vai trò (Lớp A) | Phạm vi (Lớp B) | Kết quả |
|---|---|---|---|
| Giám đốc / Admin | Admin (mọi quyền) | (trống) | Thấy & làm mọi thứ, mọi công ty |
| Trưởng phòng thu mua | Thu mua + Duyệt | Công ty 1, 2 | Duyệt PO/PYC nhưng chỉ của Cty 1 & 2 |
| Nhân viên thu mua | Thu mua (không Duyệt) | Phòng Sản xuất | Tạo/sửa PYC-PO của phòng Sản xuất, không duyệt |
| **NV thu mua (2 dòng)** | Dòng 1: Thu mua · Dòng 2: Người duyệt PYC | Dòng 1: Sản xuất · Dòng 2: IT | Làm việc ở Sản xuất **+ duyệt PYC của IT** (hợp 2 dòng) |
| Thủ kho | Kho (Xem/Sửa tồn) | Công ty 1 | Chỉ thao tác tồn kho Cty 1 |
| Kế toán công nợ | Công nợ + Thanh toán | (trống) | Xem công nợ mọi công ty |

---

## 7. Lộ trình triển khai

- **Bước 1:** Tab Vai trò + Tab Ma trận quyền (Lớp A). Backend đã sẵn — chủ yếu dựng giao diện. → phân quyền hành động dùng được ngay.
- **Bước 2:** Mở rộng `UserRole` thành **grant** (company_ids/department_codes/own) + Tab Người dùng & phạm vi (nhiều dòng) + hàm `scope_query`; áp cho PO, PYC, công nợ, tồn kho, báo cáo.
- **Bước 3:** Chặn ghi ngoài phạm vi + ẩn mục menu theo quyền + mở rộng chiều (kho, NCC) nếu cần.

---

## 8. Đã chốt
1. ✅ Phạm vi giai đoạn đầu: **Công ty + Phòng ban** (Kho/NCC mở rộng sau).
2. ✅ Hành động: **8 cờ** — Xem/Tạo/Sửa/Xóa/Duyệt/**Hủy**/In/Xuất.
3. ✅ **Menu/danh mục hiện theo quyền Xem** — có quyền xem cái nào thì hiện cái đó (mục 4).
4. ✅ Làm theo lộ trình 3 bước, **Bước 1 trước**; thao tác cấp quyền theo luồng mục 5b (gọn, 3 bước/người).
5. ✅ **Một vai trò = một chức năng** (đại ca chốt 19/09/2026, bao-CR-428). Vai trò chỉ gom
   quyền của đúng một việc. Một người làm nhiều việc thì **gán nhiều vai trò**, không dồn
   thêm quyền vào vai trò sẵn có. Hệ quả: (a) KHÔNG có "bậc riêng" theo từng tài khoản —
   bậc phạm vi thuộc về vai trò, muốn một người thấy rộng hơn thì gán thêm vai trò có bậc
   rộng hơn; (b) ngoại lệ ở `tab_user_scope` dùng chung cho mọi vai trò của tài khoản đó;
   (c) mỗi vai trò chuẩn có **một câu mô tả** nói nó lo việc gì (seed điền khi ô trống, sửa
   được ở màn Vai trò & quyền) để người đọc hay trợ lý AI trả lời được câu "vai trò này để
   làm gì". Nhãn bậc viết tổng quát, không gắn tên phân hệ: **Được giao + đã duyệt** thay cho
   **Thu mua (được giao + đã duyệt)**.

---

## 9. Kiến trúc kiểm quyền & hiệu năng

**Kiểm quyền = dependency trên route, không phải middleware toàn cục.** `require(entity, action)`
gắn vào từng API (đã có). Middleware chỉ giải mã token → gắn user.

**Token chỉ chứa `user_id` (+ hạn).** Không nhét quyền vào token (đổi quyền là token cũ sai; token phình).
Quyền tra ở server theo user_id.

**Luồng mỗi request:** token → user_id → lấy *hồ sơ quyền* `{actions_by_entity, scope}` →
`require()` cho/chặn → `scope_query()` lọc dữ liệu.

**Cache (~100 user):** cache **hồ sơ quyền đã gộp** của user để khỏi tính lại mỗi request.
- Kích thước bảng vài ngàn dòng là **nhỏ** với MySQL — query `WHERE user_id=?` (có index) ~1–3ms;
  không phải lý do cần Redis. Lý do cache là **tránh gộp roles→ma trận+scope lặp lại**.
- Hồ sơ quyền mỗi user ~vài KB → 100 user ~vài trăm KB → **cache in-process** (dict/LRU) thoải mái,
  có thể nạp sẵn lúc khởi động. In-process **nhanh hơn Redis** (không qua mạng) khi chỉ 1 tiến trình.
- **Bọc sau interface** `perm_cache.get/set/clear`: bản đầu in-process; đổi sang **Redis khi chạy
  nhiều worker/instance** (không sửa chỗ gọi). Redis cũng dùng cho worker Phase 3.
- Lưu ý multi-worker: mỗi worker cache riêng → đổi quyền lệch tối đa 1 TTL; TTL 30–60s + xóa khi lưu là đủ.

**Invalidation:** khi lưu Vai trò/Ma trận/Phạm vi → xóa cache user liên quan (hoặc bump `perm_version`);
hoặc để TTL tự hết sau ≤1 phút.

**FE:** `GET /api/auth/me` trả hồ sơ quyền rút gọn để **ẩn menu/nút**. Nhưng **chốt chặn thật ở backend** —
ẩn ở FE chỉ là UX, không phải bảo mật.

### Việc cần code (tóm tắt)
- `get_perm_profile(user_id)` + cache in-process + invalidate khi lưu quyền.
- `require()` / `scope_query()` đọc từ profile.
- `/api/auth/me` trả quyền cho FE; FE ẩn menu/nút theo `read`.
