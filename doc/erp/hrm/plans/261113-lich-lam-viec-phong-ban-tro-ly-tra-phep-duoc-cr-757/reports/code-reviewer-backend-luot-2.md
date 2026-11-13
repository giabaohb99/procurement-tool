# Rà backend duoc-CR-757 lượt 2 (khóa `work_schedule_personal` + bậc `dept` của quỹ phép)

| | |
|---|---|
| Ngày | 13/11/2026 |
| Người rà | code-reviewer (độc lập, chỉ đọc, không sửa mã) |
| Phạm vi | diff chưa commit: `core/{permissions,scoping,entity_models}.py`, `seed.py`, `work_schedule/{assignment_access (mới),assignment_controller}.py`, `leave/{policy_assignment_scope,balance_report_service}.py` (chỉ chú thích), 2 sổ giao diện v2 (`permission-types.ts`, `permission-groups.ts`), bài kiểm `test_truong_phong_gan_lich_rieng_cr757.py` (mới) + `scope_factory`, `test_pham_vi_thu_mua`, `test_pham_vi_cap_bac_ma_tran`, `test_pham_vi_khai_du_b07`, `test_assistant_pham_vi_doc`, `test_pham_vi_bo_may_duyet_xuyen_suot`. Bỏ qua `frontend-v2/src/modules/hr` (agent khác đang sửa). |
| Kết luận | **Trả lại.** Có 1 lỗi Chặn: bản vá "ràng công ty HIỆN TẠI của nhân sự" đang làm dở và đang làm đỏ `test_pham_vi_cap_bac_ma_tran`. Sửa bài kiểm (oracle) đó là gộp được. Có 3 mục Nên sửa, cả ba là quyết định phạm vi cần chốt hoặc đếm trên prod trước khi deploy. |

## Đã chạy

- Lần 1, chạy trước khi bản vá công ty đổ về:
  - `test_truong_phong_gan_lich_rieng_cr757` + `test_tro_ly_tra_phep_lich_lam_viec_cr757`: **45 xanh**.
  - 4 tệp phạm vi đã sửa (`thu_mua`, `cap_bac_ma_tran`, `assistant_pham_vi_doc`, `bo_may_duyet_xuyen_suot`): **736 xanh**.
  - 9 tệp lịch làm việc / quỹ phép (`lich_lam_viec_{api,bo_ma_va_quyen,ra_soat_be}`, `bao_cao_quy_phep_cr686`, `nghi_phep_{doi_chieu_ket_so_cr664,loc_quy_phep,phan_bo_hang_loat_cr717,ket_so_cuoi_nam}`, `noi_phan_bo_quy_phep_cr745`): **141 xanh**.
- Cụm 6 bài canh của skill `them-entity-moi`: **170 xanh, 1 đỏ** (`test_bo_ma_hanh_dong_cr358`, mã `resend`; xem mục 5, lỗi này có từ trước, không do CR này).
- Lần 2, chạy SAU khi bản vá công ty đổ về `scoping.py`: CR-757 ×2 + `cap_bac_ma_tran` + `khai_du_b07` + `phan_bo_hang_loat_cr717` + `bao_cao_quy_phep_cr686`: **690 xanh, 1 đỏ** (C1).
- `ruff check app` (cổng chuẩn): sạch. Không có ngoặc kép góc, không có emoji.
- Biên dịch điều kiện `leave_balance` (bậc dept + ô chọn phòng + loại trừ phòng) bằng dialect MySQL rồi chạy trên MySQL local, cả với `LeaveBalance` lẫn với "bảng giả" `Employee` của `writable_employee_query`. Bí danh `tab_employee_1/2/3` đúng, truy vấn con không bị tương quan, câu lệnh chạy được (30 dòng).
- Bốn bài dò tạm trong `/tmp` của container (đã xóa). Kết quả nằm ở N1 và N2.

## Chặn

### C1. Bản vá "công ty hiện tại" (đang làm dở) làm đỏ `test_pham_vi_cap_bac_ma_tran[dept-leave_balance]`

Mục này dán nhãn **pending fix**. Người điều phối báo phần này đang được sửa, nên chỉ ghi phần cần làm thêm.

Bản vá ở `core/scoping.py:745-753` bỏ điều kiện `tab_leave_balance.company_id` ở bậc `dept` khi entity khai `dept_via_employee`, rồi ràng `tab_employee_1.company_id IN (...)` bên trong truy vấn con. Về nghiệp vụ là đúng: bài dò với phòng dùng chung `company_id = 0` cho ra `['AS', 'M1']`, không lọt người cùng phòng ở công ty B. Tuy vậy, oracle `expect_outcome` ở `test/backend/test_pham_vi_cap_bac_ma_tran.py:134-140` vẫn đòi cột `company_id` của dòng có mặt trong SQL:

```
AssertionError: leave_balance × dept: điều kiện không đụng tới cột `company_id` đã khai trong SCOPE_FIELDS.
SQL: tab_leave_balance.employee_id IN (SELECT tab_employee_1.id FROM tab_employee AS tab_employee_1
     WHERE tab_employee_1.department_id IN (...) AND tab_employee_1.company_id IN (...))
```

Cách sửa: trong nhánh `scope == "dept"` của oracle, chỉ thêm `f["company"]` khi `not f.get("dept_via_employee")`, cùng điều kiện với `scoping.py:748`. Nên có thêm một bài nhỏ ghim hai ca: dòng quỹ `company_id = 0` của người phòng mình VẪN hiện ở bậc `dept`, và người cùng phòng dùng chung ở công ty khác KHÔNG hiện. Fixture `w` của `test_truong_phong_gan_lich_rieng_cr757.py` hiện dựng phòng có `company_id = công ty` và dòng quỹ có `company_id` khớp, nên không bắt được lỗi 240/307 dòng mà người điều phối thấy trên local. Đây đúng là bẫy ghi trong memory "departments-shared-across-companies".

## Nên sửa

### N1. Ô "Phòng ban được xem" của các grant cũ nay MỞ quỹ phép, lại mở xuyên công ty

`_dept_include_cond` (`scoping.py:~931`) gọi `_dept_match(model, f, inc...)` mà không truyền `employee_company_ids`. Từ khi `leave_balance` khai `dept_via_employee`, ô "Phòng ban được xem" bắt đầu có tác dụng lên quỹ phép. Trước CR này ô đó không làm gì với `leave_balance`, vì `_dept_match` trả `None`.

Ô phạm vi gắn theo cặp (người, vai trò), áp cho MỌI entity của vai trò (`auth.py:201-227`), và vòng `setdefault` của seed cấp `leave_balance` (`read`, bậc `own`) cho mọi vai trò. Vì vậy người nào trên prod đang có ô chọn phòng ở bất kỳ vai trò nào (thường để xem YCMH / văn bản của phòng khác) sẽ, kể từ lần deploy này, thấy quỹ phép của mọi người thuộc phòng đó ở MỌI công ty.

Bài dò: người dùng ở phòng AO, chỉ có `leave_balance` bậc `own` cộng ô chọn phòng dùng chung SH1. `GET /api/leave-balances` trả `['AO', 'AS', 'BS', 'M1']`, trong đó `BS` thuộc công ty B. Trước CR này cùng cấu hình đó chỉ trả `['AO']`.

Việc cần làm (chọn một):
- (a) Đếm trên prod trước khi deploy: số dòng `tab_user_scope` có `dim='department'`, `is_exclude=0`, nối với vai trò có `leave_balance.can_read`. Nếu đếm ra 0 hoặc người chủ chấp nhận thì ghi vào tài liệu.
- (b) Truyền `employee_company_ids=_own_companies(profile)` cả ở nhánh ô chọn phòng khi entity là `dept_via_employee`, để ô đó không mở xuyên công ty.

Ô loại trừ phòng thì chỉ thu hẹp (`NOT IN (...)`), an toàn.

Cùng cơ chế này cũng mở rộng khóa mới `work_schedule_personal`. Bài dò: Trưởng phòng có ô chọn phòng SH2 trên vai trò giữ khóa riêng, `POST` lịch riêng cho người phòng SH2 trả **201**. Đây đúng là nghĩa của ô "cộng thêm", nhưng Q1 chốt "nhân viên phòng mình". Vì vậy khi tick quyền tay trên prod (P8) cần kiểm vai trò Trưởng phòng có mang ô chọn phòng hay không.

### N2. Trưởng phòng sửa / xóa / đè được lịch riêng do Nhân sự lập, và lùi ngày về năm 2000

Đường Trưởng phòng (`assignment_access.check_personal_existing_row`, `assignment_access.py:74-86`) không phân biệt dòng do ai lập. Với một người trong phạm vi, Trưởng phòng làm được ba việc:
- `PATCH` hoặc `DELETE` dòng lịch riêng do Nhân sự lập. Khi xóa, `heal_before_delete` mở lại lịch cũ.
- `POST` một dòng mới từ ngày X: dòng "không thời hạn" của Nhân sự bị tự đóng ở X−1 và bị cắt đôi (`assignment_service.py:116-160`).
- Đặt `effective_from` tùy ý trong khoảng 2000–2100. Bài dò `POST` với ngày `2000-01-01` trả **201**.

Mọi thao tác chỉ chạm dòng của CÙNG nhân sự đó, và bài `test_tu_dong_dong_va_mo_lai_chi_cham_dong_cua_cung_nhan_su` đã ghim điều này. Như vậy không leo thang sang người hay cấp khác. Tuy vậy, Trưởng phòng ghi đè được quyết định của Nhân sự (vd lịch riêng cho người đang mang thai hay làm ca đặc biệt) và đổi lùi cách đếm ngày nghỉ cho cả quá khứ. Trưởng phòng lại thường chính là người duyệt đơn nghỉ của nhân viên đó.

Cần chốt với người chủ:
- (i) Đường Trưởng phòng có được đụng dòng do người giữ khóa `work_schedule` lập không? Nếu không thì chặn bằng `created_by`, hoặc bằng cờ nguồn.
- (ii) Có giới hạn `effective_from >= đầu tháng hiện tại` (hoặc `>= hôm nay`) cho đường Trưởng phòng không?

Dòng nhật ký hiện ghi chung `"Gán lịch làm việc"` dưới entity `work_schedule`. Nên ghi thêm `(Trưởng phòng)` để tra lại sau này.

### N3. Bậc `dept` của `leave_balance` HẸP LẠI trên prod: cần đếm trước khi deploy

Trước CR này bậc `dept` = cả công ty. Seed chỉ `dept_head` dùng bậc này, nhưng `seed_prod.py` không ghi đè quyền đã sửa tay, nên trên prod có thể có vai trò tự dựng (hoặc `dept_head` đã chỉnh) đặt `leave_balance` bậc `dept` với ý nghĩa thực tế là "xem cả công ty". Sau deploy những người này chỉ còn thấy phòng mình, mà không có ai được báo.

Cần đếm `tab_permission` có `entity='leave_balance'` và `scope='dept'` (kèm vai trò, số người đang giữ), ghi vào sổ việc P8. Cùng lúc kiểm `can_write` / `can_create`: `policy_assignment_scope.writable_employee_query` giao phạm vi xem hồ sơ với phạm vi GHI quỹ, nên người có ghi bậc `dept` cũng sẽ hẹp lại ở màn phân bổ chính sách.

## Gợi ý

- G1. Nhánh `dept_proc` của `leave_balance` đổi từ CHẶN sang MỞ xuyên công ty. `scoping.py:~734` (entity không phải chứng từ thu mua: bậc `dept_proc` rơi về `_dept_match` không có công ty). Trước CR, `_dept_match` trả `None` nên bị `_chan`. Bài dò cho bậc `dept_proc` trả `['AS', 'BS', 'M1']` (lọt `BS` ở công ty B). Không vai trò seed nào dùng bậc này cho quỹ phép. Nên truyền `employee_company_ids` ở nhánh này khi entity là `dept_via_employee`, hoặc ít nhất đếm trên prod.
- G2. Chú thích ở `scoping.py:203-205` viết "người có phòng ban chính HOẶC kiêm nhiệm nằm trong `dept_ids`", dễ đọc thành "kiêm nhiệm của NGƯỜI ĐƯỢC XEM". Thực tế truy vấn con chỉ so `tab_employee.department_id` (phòng chính) của người giữ quỹ; phần kiêm nhiệm là của NGƯỜI XEM (`profile.dept_ids`). Người phòng khác kiêm nhiệm vào phòng X không hiện với Trưởng phòng X, ở cả quỹ phép lẫn lịch riêng. Hành vi này nhất quán với `employee` khi không bật `include_concurrent`, nhưng nên viết rõ ra.
- G3. Ô "Chỉ trong công ty A" và ô loại trừ công ty (`_explicit_cond`) vẫn so `tab_leave_balance.company_id`, tức ảnh chụp lúc cấp quỹ. Dòng có `company_id = 0` sẽ biến mất với người có ô chọn công ty, kể cả ở bậc `dept`. Bậc `company` cũng vậy (đã ghi giới hạn G3 trong chú thích). Ngoài phạm vi CR này nhưng là cùng một gốc lỗi, nên đưa vào việc điền lùi `company_id`.
- G4. `allocate` / `close_year` (`balance_controller.py:174-283`) chỉ giao với phạm vi `employee`, không giao với phạm vi GHI `leave_balance`. Lỗ này có từ trước. Nay bậc `dept` đã có nghĩa thật, nên một vai trò có `leave_balance.create/write` bậc `dept` mà `employee.read` bậc công ty sẽ cấp quỹ / kết sổ được cho cả công ty dù chỉ thấy phòng mình. Nên dùng `writable_employee_query` ở hai đường này.
- G5. Docstring của `test_pham_vi_cap_bac_ma_tran.py:278` trỏ tới `test_dept_cua_quy_phep_di_qua_ho_so_nhan_su`, nhưng không có bài nào tên đó (các bài thật tên `test_quy_phep_bac_phong_*`).
- G6. `ENTITY_LABELS["work_schedule_personal"] = "Lịch làm việc riêng của nhân sự"` lệch khuôn `"Nhân sự › Lịch làm việc"` của khóa anh em. Gợi ý đổi thành `"Nhân sự › Lịch làm việc riêng (Trưởng phòng gán)"` để màn Phân quyền xếp cạnh nhau, dễ phân biệt.
- G7. Khóa mới hiện đủ 9 hành động trên ma trận, nhưng chỉ `create/write/delete` có tác dụng (`read` không được kiểm ở đâu). Không gây hại; có thể ghi rõ trong mô tả vai trò.
- G8. Tài liệu (P8) chưa nhắc `work_schedule_personal` / `dept_via_employee`: `doc/erp/hrm/tai-lieu-ky-thuat/api.md`, `03-lich-lam-viec.md`, mục CR-757 ở `change-log.md`. Cần thêm câu về N1 / N3 trong phần "ảnh hưởng người dùng".

## Kiểm theo đầu việc được giao

1. **Leo thang qua đường riêng.**
   - Ba ca bị chặn đúng: đổi cấp, đổi đích sang người ngoài phạm vi, đổi đích sang chính mình (`assignment_controller.py:95-107` chốt cả dòng cũ lẫn giá trị mới).
   - Xóa dòng cấp khác trả 403. Xóa dòng người ngoài phạm vi trả 404.
   - Chặn tự gán dùng `profile.employee_id`; mọi kiêm nhiệm đều trỏ cùng một hồ sơ nên không có ngả vòng.
   - Nhân sự có `department_id = 0` không lọt (bài kiểm có ca này). Tài khoản chưa gắn hồ sơ thì `dept_ids` rỗng, kết quả là `false()` rồi 400.
   - Mẫu lịch đã tắt bị chặn ở service cho cả hai đường. `template_controller` vẫn chỉ nhận `work_schedule`.
   - Tự đóng / mở lại chỉ chạm dòng cùng `(target_level, target_id)` (`assignment_service._overlaps`, `assignment_heal`).
   - Vấn đề còn lại thuộc nghiệp vụ, đã ghi ở N2.
2. **Điều kiện HOẶC theo từng hành động.**
   - `require_assignment_action(action)` hỏi đúng hành động trên cả hai khóa.
   - Người có `work_schedule.create` mà thiếu `work_schedule.write` thì `PATCH` đi đường riêng, đúng.
   - Khóa riêng chỉ có `create` thì `PATCH` / `DELETE` trả 403 (có bài kiểm).
   - Đường riêng đọc dòng bằng `work_schedule.read`. Thiếu quyền đó thì `false()` rồi 404, tức đóng an toàn.
3. **`dept_via_employee`.**
   - Biên dịch MySQL đúng, bí danh đủ, câu lệnh chạy được.
   - Dò trên `tab_employee` (vài trăm dòng) bằng một truy vấn con, không thêm truy vấn. Bài đếm truy vấn của công cụ trợ lý xanh.
   - Các chỗ dùng phạm vi `leave_balance` đều đi qua `apply_scope` / `get_scoped` / `scope_condition` nên tự hưởng thay đổi: danh sách, chi tiết, điều chỉnh, ma trận, báo cáo, đối chiếu kết sổ, phân bổ chính sách và nối phân bổ (`LeavePolicyAssignment` có `employee_id`), `request_controller:446`, công cụ trợ lý (`_balance_seat`).
   - Đường ghi bậc `dept`: `adjust` và phân bổ đi qua phạm vi ghi; `allocate` / `close_year` thì không (G4).
   - Các điểm còn mở: ô chọn phòng (N1), `dept_proc` (G1), so công ty của dòng (C1 pending, G3).
4. **Seed.**
   - `work_schedule_personal` nằm trong `_SYS_ENTITIES`, nên không lọt vào `_PUR_MANAGER_PERMS`.
   - Chỉ `dept_head` giữ khóa này (`read/create/write/delete`, bậc `dept`). Admin nhận qua vòng bù `ENTITIES`.
   - `seed_prod` không tự cấp, nên phải tick tay (P8). Có bài kiểm ghim.
5. **`test_bo_ma_hanh_dong_cr358` đỏ vì `resend`.** Lỗi có từ trước. Mã `record(db, actor_id, "email_log", fresh.id, "resend", ...)` ở `notification/email_log_controller.py:280` vào từ commit `b21433a8` "bao-CR-727 Nhat ky email: luu noi dung thu + nut Gui lai" (giabaohb99, 04/11/2026). Tệp đó và `core/action_catalog.py` đều không có thay đổi trong cây làm việc hiện tại.
6. **Luật dự án.**
   - Bảy sổ của `them-entity-moi`: (1) `permissions` (2) `SCOPE_FIELDS` + số đếm B-07 80→81 (3) `entity_models` (không phải `PUBLIC` nên khai đúng) (4) seed (5) hai sổ v2, bài canh đồng bộ xanh (6) không có mã hành động mới (7) không có cột chữ mới.
   - Tên tệp bài kiểm đúng khuôn `test_<chủ đề>_cr757.py`. Định danh tiếng Anh, chuỗi và chú thích tiếng Việt. Ba đường ghi có docstring tiếng Việt.

## Câu hỏi còn mở

1. N2: Trưởng phòng có được sửa / xóa / đè lịch riêng do Nhân sự lập, và có được lùi ngày hiệu lực không?
2. N1: trên prod, có grant nào mang ô "Phòng ban được xem" trên vai trò có `leave_balance.read`, hoặc trên vai trò Trưởng phòng không?
3. N3: trên prod, có vai trò nào đặt `leave_balance` bậc `dept` ngoài `dept_head` không, và họ có biết là sẽ hẹp lại?

---

## Lượt 3 (rà lại phần vá)

| | |
|---|---|
| Phạm vi | Chỉ phần đổi: `core/scoping.py`, `work_schedule/{assignment_access,assignment_controller,assignment_service}.py`, `test_truong_phong_gan_lich_rieng_cr757.py`, `test_pham_vi_cap_bac_ma_tran.py` |
| Kết luận | **Trả lại.** Phần phạm vi đạt: C1, N1, G1, G2, G5, G6 đã đóng. Đường Trưởng phòng còn 1 lỗi Chặn (lùi lịch qua dòng đã bắt đầu từ trước) và 1 mục Nên sửa (dòng nối lại, gỡ liên kết). |

### Đã chạy

- Bảy tệp: CR-757 ×2, `cap_bac_ma_tran`, `khai_du_b07`, `lich_lam_viec_api`, `lich_lam_viec_ra_soat_be`, `phan_bo_hang_loat_cr717`. Kết quả **745 xanh**.
- Ba tệp: `thu_mua`, `assistant_pham_vi_doc`, `luat_bat_bien`. Kết quả **146 xanh**.
- `ruff check app`: sạch.
- Chạy lại toàn bộ bài dò trong `/tmp` của container (đã xóa sau khi chạy). Thế giới dò có phòng dùng chung `company_id = 0`, hai công ty, và mọi dòng quỹ ghi `company_id = 0`.

### Kết quả bài dò

| Ca | Kết quả | Đánh giá |
|---|---|---|
| N1: bậc `own` + ô chọn phòng dùng chung SH1 | `['A1','AO','M1']`, không có `BS` (công ty B) | Đóng |
| Bậc `dept`, dòng quỹ ghi `company_id = 0` | `['A1','M1']` | Đóng (C1) |
| G1: bậc `dept_proc` | `['A1','M1']` | Đóng |
| Lịch riêng + ô chọn phòng SH2 | AO (cùng công ty) 201 · BO (công ty B) 400 · BS (phòng mình, công ty B) 400 | Đóng |
| Sửa / xóa dòng do Nhân sự lập | 403 / 403 | Đóng |
| Tạo ngày hôm nay, rồi sửa `effective_from` về hôm qua | 422 | Đóng |
| Tạo ngày hôm nay, rồi sửa `effective_to` về hôm qua | 400 (`check_period`) | Đóng |
| Nửa đêm: 17:30 UTC = 00:30 ngày 14/11 giờ VN, tạo từ ngày 13/11 | `vn_today` = 14/11, trả 422 | Đóng |
| Dòng TỰ LẬP đã bắt đầu 30 ngày trước: đổi mẫu · đặt `effective_to` lùi 20 ngày · đổi đích · xóa | **200 · 200 · 200 · 200** | **C2 bên dưới** |
| Tạo lịch tạm có hạn trên dòng Nhân sự, rồi xóa dòng NỐI LẠI | dòng nối lại `created_by` = Trưởng phòng; xóa trả **200** | **N4 bên dưới** |
| Tạo dòng không hạn, sửa `effective_to` (gỡ liên kết), rồi xóa | 200 / 200; dòng Nhân sự **vẫn bị đóng** ở hôm nay | **N4 bên dưới** |

### Chặn

**C2. Chốt "không lùi ngày" chỉ soi `effective_from` khi tạo hoặc khi đổi ngày bắt đầu. Dòng do chính Trưởng phòng lập mà đã bắt đầu từ trước thì vẫn sửa / xóa được và đổi lịch của những ngày đã qua.**

Chỗ lỗi: `assignment_controller.py`, nhánh Trưởng phòng của PATCH và DELETE.

Kịch bản:
1. Ngày 01/11, Trưởng phòng gán lịch T2–T7 cho A1 (hợp lệ).
2. Ngày 13/11, Trưởng phòng gửi `PATCH {schedule_id: <lịch nghỉ T7>}`, hoặc `{effective_to: 05/11}`, hoặc `{target_id: A2}`, hoặc `DELETE`. Mọi lệnh đều trả 200.
3. Lịch của A1 trong 01–12/11 đổi lùi.

Hậu quả cụ thể:
- `comp_request_service.py:112` dùng `count_leave_days(...) == 0` để nhận ngày làm việc vào ngày nghỉ (phiếu nghỉ bù). Lùi lịch biến các thứ Bảy đã đi làm thành "ngày nghỉ", nên nhân viên xin được nghỉ bù cho chúng. Trưởng phòng lại đang giữ `leave_comp_request` bậc `dept` có `approve`.
- Đơn nghỉ đang chờ hoặc đang sửa, và báo cáo ngày đã nghỉ, cũng tính lại theo lịch mới.

Đây là đúng điều người chủ đã chốt cấm (mục 7 trong docstring `assignment_access`).

Cách sửa đề xuất, chỉ cho đường Trưởng phòng, gom vào `assignment_access`:
- Nếu `obj.effective_from < vn_today()`:
  - chỉ cho đổi `effective_to` (và `note`);
  - giá trị mới phải là `None` hoặc `>= vn_today() - 1`;
  - cấm đổi `schedule_id` / `target_id` / `target_level` (400: "đặt Đến ngày rồi gán dòng mới").
- Nếu `obj.effective_to` đã `< vn_today()` (dòng đã kết thúc): cấm mọi sửa.
- `DELETE`: chỉ cho khi `obj.effective_from >= vn_today()`. Ngược lại 400, hướng người dùng đặt "Đến ngày".
- Thêm bài kiểm: chèn thẳng một dòng `created_by` = Trưởng phòng với ngày bắt đầu là `vn_today() - 30`, rồi thử bốn thao tác trên.

### Nên sửa

**N4. Hai ngả để Trưởng phòng kết thúc lịch riêng của Nhân sự mà không phải "đổi lịch từ một ngày trở đi".**

1. **Dòng nối lại do Trưởng phòng sở hữu.** `assignment_service.create_assignment` tạo dòng nối lại `R` (bản sao lịch của Nhân sự, chạy từ `to + 1`) với `created_by=user.id` (`assignment_service.py:~140`). Trong bài dò, R có `created_by = 1` (Trưởng phòng). Chốt `created_by` vì thế cho Trưởng phòng xóa R. Sau khi lịch tạm hết, A1 rơi xuống lịch phòng / hệ thống, tức lịch riêng của Nhân sự mất hẳn từ ngày đó.
   - Sửa: `created_by=a.created_by` (giữ người lập dòng gốc; `updated_by` vẫn là người thao tác). Sửa ở service nên áp cho cả đường Nhân sự, mà ở đó đây cũng là thông tin đúng hơn.
2. **Gỡ liên kết rồi xóa.** Trưởng phòng PATCH ngày của dòng tự lập. `clear_links` gỡ `linked_assignment_id` của dòng Nhân sự đã bị đóng, nên `DELETE` sau đó không còn mở lại dòng đó. Bài dò cho thấy dòng Nhân sự vẫn kết thúc ở 13/11 trong khi dòng của Trưởng phòng đã biến mất.
   - Sửa (đường Trưởng phòng): nếu còn dòng `linked_assignment_id == obj.id` mà PATCH đổi `(target, from, to)`, trả 400 "Dòng này đã đóng lịch do Nhân sự gán; xóa rồi gán lại".
   - Hoặc: cho `heal_before_delete` mở lại theo dấu riêng, không phụ thuộc liên kết. Cách này phức tạp hơn.

### Đã xem, đạt

- `_dept_include_cond(..., profile)`: chỉ có một nơi gọi (`_grant_scope_condition`).
  - Entity `dept_via_employee`: ràng công ty trong truy vấn con.
  - `INCLUDE_DEPT_SAME_COMPANY`: AND thêm cột công ty.
  - Entity khác: giữ nguyên.
  - Người xem chưa gắn pháp nhân: không ràng, giống nhánh `dept`.
- Ô loại trừ phòng vẫn không ràng công ty, như vậy là đúng vì loại trừ chỉ thu hẹp.
- `check_personal_existing_row` kiểm phạm vi TRƯỚC `created_by`: người ngoài phạm vi vẫn nhận 404, không lộ dòng có thật.
- `serialize_many` trả `created_by` (id tài khoản): không nhạy cảm.
- Oracle `expect_outcome` đã khớp `scoping.py`. Docstring trỏ tên bài kiểm thật.

### Câu hỏi còn mở

1. C2: ngoài việc đặt "Đến ngày", Trưởng phòng có được xóa dòng tự lập đã bắt đầu không, hay việc đó chỉ dành cho Nhân sự? Đề xuất: không được xóa.

**Status:** DONE
