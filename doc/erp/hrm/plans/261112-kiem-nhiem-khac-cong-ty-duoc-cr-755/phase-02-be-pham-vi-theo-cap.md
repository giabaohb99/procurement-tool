# Phase 02 — BE phạm vi quyền theo cặp (phòng, công ty) + bài canh

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | backend | Đã làm (chờ rà soát) | duoc-CR-755 |

## Context links
- [plan.md](plan.md) luật cốt lõi; [phase-01](phase-01-be-du-lieu-migration-api.md) (`active_concurrent_rows`, `dept_ids`).
- `core/auth.py:246-278`; `core/scoping.py`: `_dept_match` 349, `_handler_match` 389, `holds_handling_dept` 420,
  `_role_scope_cond` 489 (nhánh `assigned/proc/dept_proc` 520-626, `dept` 661-679, `company` 681-740),
  `_dept_include_cond` 823, `_grant_scope_condition` 870; `core/subject_match.py:27-47`.
- Bài kiểm sẵn: `test_pham_vi_*` (nhất là `test_pham_vi_cap_bac_ma_tran.py`, `test_pham_vi_duong_vong.py`),
  `test_va_ro_du_lieu_xuyen_phap_nhan.py`, `test_chuyen_phong_xu_ly_cr414.py`, `test_pham_vi_khai_du_b07.py`.

## Overview
P1, rủi ro cao nhất của CR. Đưa cặp khác công ty vào bộ phạm vi sao cho: chỉ mở đúng cặp, không lộ qua đường không ràng công
ty, không đổi `company_id` thành danh sách, không thêm khóa quyền mới, không thêm truy vấn theo số dòng.

## Key insights
- Phase 01 đã giữ `dept_ids` = phòng chính + kiêm nhiệm CÙNG công ty → mọi đường không ràng công ty (`dept_proc`,
  `_narrow_to_dept`, `_handler_match`, `holds_handling_dept`, L2 cũ) KHÔNG nhìn thấy cặp khác công ty. Đây là hàng rào mặc
  định: quên một đường = thiếu quyền (an toàn), không phải lộ dữ liệu. Riêng `subject_pairs` được cộng tường minh (Q3).
- Cặp khác công ty chỉ được cộng vào ở những nhánh ta tự viết thêm `AND <cột công ty> == c`.
- Entity có `dept_id` mà không có `company` trong `SCOPE_FIELDS` → KHÔNG cộng cặp (không ràng được). Hiện mọi entity có
  `dept_id` đều có `company` — khóa bằng bài canh.
- `_dept_include_cond` đọc ô "Phòng ban được xem" của `tab_user_scope` (admin chọn), không đọc kiêm nhiệm → KHÔNG đổi.
- ACL chủ thể (`subject_match`, chốt Q3 = CÓ): dòng loại PHÒNG không mang công ty → cộng phòng của `concurrent_pairs` vào
  `subject_pairs` (không ràng công ty được, rủi ro chấp nhận). KHÔNG cộng công ty B thành chủ thể CÔNG TY. Cùng hàm đó còn làm
  chốt tự cấp quyền báo cáo (`report_access/grant_guards.block_self_allow_grant`) và tập phòng cha của skill AI
  (`ai_skill/access_service.py:75-85`) — cộng thêm phòng là chặt hơn ở chốt tự cấp, rộng hơn ở skill AI (đúng ý Q3).
- Đọc hồ sơ người kiêm nhiệm (chốt Q1 = CÓ): entity `employee` lọc theo `Employee.department_id` (phòng CHÍNH) nên cần nhánh
  thứ hai "hồ sơ có dòng kiêm nhiệm hiệu lực + bật công tắc nằm ở cặp người xem phủ". Mặc định TẮT, bật tường minh ở đường đọc
  hồ sơ: quên bật = thiếu quyền (an toàn); bật mặc định thì mọi báo cáo nhân sự (~15 tệp gọi phạm vi `employee`) và truy vấn
  gốc của sơ đồ tổ chức tự kéo người công ty A vào màn của trưởng phòng B (lộ cơ cấu A, sai luật không đếm trùng).

## Requirements
- Hồ sơ quyền thêm `concurrent_pairs: list[list[int]]` — dòng hiệu lực + `counts_scope` + `company_id != công ty chính` +
  `company_id != 0`; xếp theo (company, dept) để cache ổn định. Lấy chung truy vấn của phase 01 (không thêm truy vấn).
- Hàm dùng chung `_pair_conds(model, f, pairs, builder)` gom theo công ty: `OR(AND(company_cond(c), builder(ids_c)) ...)`;
  `company_cond(c)` dùng lại khuôn `company` + `company_alt` (đặt xe) như nhánh `dept`.
- Nhánh `dept`: `OR(nhánh cũ, *_pair_conds(_dept_match))`.
- `dept_proc` rơi về `dept` (entity không phải chứng từ, 620-626): `OR(dm cũ, *_pair_conds(_dept_match))`.
- `_narrow_to_dept`: `AND(cond, OR(dm cũ, *_pair_conds(_dept_match(central_handler=True))))`; chặn `_chan` khi CẢ hai rỗng.
- PO `dept_proc`: `hm` thành `OR(hm cũ, *_pair_conds(_handler_match))`.
- `holds_handling_dept`: thêm `[current, ticket.company_id] ∈ concurrent_pairs`.
- Bậc `company`, `own`, `all`, `seal_request`: KHÔNG đổi.
- Hàm cho phase 05: `concurrent_row_scope_condition(viewer, profile, action="read")` — điều kiện SQL trên
  `EmployeeConcurrent` = phạm vi `employee` của người xem áp lên dòng như thể nhân sự ngồi tại (phòng, công ty) của dòng.
  Cách làm: lớp chuyển tiếp chỉ khai ba thuộc tính cột `company_id → EmployeeConcurrent.company_id`, `department_id →
  EmployeeConcurrent.department_id`, `id → EmployeeConcurrent.employee_id`, gọi `scope_condition(adapter, "employee", ...)`.
  Phải rà `_explicit_cond` xem với entity `employee` nó đọc thêm cột nào và khai đủ (thiếu là `AttributeError`, bài kiểm bắt).
  ⚠️ Gọi `_grant_scope_condition` (không gọi `scope_condition`) cho lớp chuyển tiếp — tránh đệ quy vào nhánh Q1 dưới đây.
- **Nhánh Q1** — tham số mới `include_concurrent: bool = False` ở `scope_condition`, `apply_scope`, `get_scoped`; chỉ có tác
  dụng khi `entity == "employee"` VÀ `action == "read"` (hành động khác bỏ qua cờ: sửa / xóa / xuất / in vẫn theo vị trí chính).
  Khi bật: `cond_cũ OR EXISTS(SELECT 1 FROM tab_employee_concurrent ec WHERE ec.employee_id = tab_employee.id AND <hiệu lực theo
  vn_today> AND ec.counts_scope = 1 AND <concurrent_row_scope_condition(người xem) trên ec>)`. Một subquery tương quan, không N+1,
  không truy vấn thêm khi dựng; `cond_cũ is None` (thấy tất) → giữ `None`; điều kiện cặp ra `false()` → bỏ nhánh. "Cùng luật bậc"
  có sẵn nhờ lớp chuyển tiếp: bậc `dept`/`dept_proc` → cặp nằm trong cặp của người xem (`dept_ids` cùng công ty chính hoặc
  `concurrent_pairs`); bậc `company` → `ec.company_id == công ty chính người xem`; loại trừ đích danh nhân sự vẫn ăn.
  Index `(employee_id)` của phase 01 đủ cho EXISTS.
- **`subject_pairs`** (Q3): sau phòng chính + `dept_ids`, thêm phòng của `concurrent_pairs` (bỏ trùng). Dòng hết hạn / tắt
  công tắc không có trong `concurrent_pairs` nên tự rơi.

## Architecture
```
get_perm_profile ──(1 truy vấn tab_employee_concurrent hiệu lực+bật)──┬─ cùng công ty chính → dept_ids (phase 01)
                                                                     └─ khác công ty       → concurrent_pairs (phase này)
scope_condition → _grant_scope_condition → _role_scope_cond
   dept      : AND(company==chính, dm(dept_ids)) OR AND(company==c, dm(ids_c)) ...
   dept_proc : narrow(cond, dm(dept_ids, central) OR AND(company==c, dm(ids_c, central)) ...)
   company   : company == chính   (không đổi)
   employee + read + include_concurrent=True : cond_cũ OR EXISTS(dòng kiêm nhiệm hiệu lực, bật, cặp được người xem phủ)
subject_pairs : dept_ids + phòng của concurrent_pairs (Q3)
```

## Related code files
Sửa (phase sở hữu): `backend/app/core/auth.py` (thêm `concurrent_pairs`), `backend/app/core/scoping.py`,
`backend/app/core/subject_match.py` (`subject_pairs` + chú thích), `doc/tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md`
(một mục **Kiêm nhiệm khác công ty**). Bật `include_concurrent=True` ở các đường đọc hồ sơ là việc của phase 05 (tệp của
`employee/`), phase này chỉ dựng tham số.
Tạo: `test/backend/test_kiem_nhiem_khac_cong_ty_pham_vi_cr755.py`.
Không đụng: `department_service.py` (phase 03 đang sửa), `scope_factory.py` (phase 01 đã sửa; chỉ dùng).

## Implementation steps
1. `auth.py`: tách kết quả `active_concurrent_rows` thành hai nhóm; thêm khóa `concurrent_pairs` vào `profile`.
2. `scoping.py`: viết `_pair_conds`, `_company_cond_for(model, f, company_id)` (tách từ nhánh `dept` để dùng chung, không đổi
   hành vi cũ); cắm vào năm chỗ ở Requirements; viết `concurrent_row_scope_condition`.
3. Chú thích đầu mỗi chỗ cắm: vì sao ràng công ty, trỏ về plan này.
4. Bài canh (dưới), rồi chạy lại các bài phạm vi cũ.
5. Tài liệu phân quyền: bảng **đường nào thấy cặp khác công ty, đường nào không**.

## Todo
- [x] `concurrent_pairs` trong hồ sơ quyền, không thêm truy vấn
- [x] `_pair_conds` + `_company_cond_for`
- [x] Cắm nhánh `dept`, `dept_proc` (2 chỗ), PO handler, `holds_handling_dept`
- [x] `concurrent_row_scope_condition` + rà `_explicit_cond`
- [x] Tham số `include_concurrent` (nhánh EXISTS Q1) ở `scope_condition` / `apply_scope` / `get_scoped`
- [x] `subject_pairs` cộng phòng kiêm nhiệm khác công ty (Q3)
- [x] Bài canh + chạy bài phạm vi cũ
- [x] Mục tài liệu phân quyền

## Success criteria
`docker compose exec -T api python -m pytest test/backend/test_kiem_nhiem_khac_cong_ty_pham_vi_cr755.py
test/backend/test_kiem_nhiem_phong_ban.py test/backend/test_pham_vi_cap_bac_ma_tran.py test/backend/test_pham_vi_duong_vong.py
test/backend/test_va_ro_du_lieu_xuyen_phap_nhan.py test/backend/test_chuyen_phong_xu_ly_cr414.py
test/backend/test_pham_vi_khai_du_b07.py -q --timeout=120` xanh (nặng thì chia `-k`). Bài canh mới phủ:
1. Người A kiêm nhiệm (X, B) bật công tắc, bậc `dept`: thấy YCMH/đơn nghỉ/hồ sơ nhân sự của (X, B); KHÔNG thấy (X, C) dù X
   là phòng dùng chung; KHÔNG thấy (Y, B).
2. Bậc `company`: chỉ công ty chính — cặp B không mở cả công ty B.
3. `dept_proc` (YCMH, YCBG, ĐMH, đặt xe): phiếu (X, C) có `handler_dept_id = X` KHÔNG lọt; (X, B) lọt.
4. `subject_match` (Q3): ACL thư mục / văn bản / báo cáo / skill AI cấp cho phòng X KHỚP người kiêm nhiệm (X, B) đang hiệu
   lực + bật công tắc; tắt công tắc, hết hạn, chưa bắt đầu → không khớp; ACL cấp cho CÔNG TY B không khớp nhờ kiêm nhiệm;
   chốt tự cấp quyền báo cáo chặn người kiêm nhiệm (X, B) tự cấp cho phòng X.
10. Nhánh Q1 (`include_concurrent=True`, `read`): trưởng phòng bậc `dept` ở (X, B) `get_scoped` được hồ sơ người A (chính ở
   A) có dòng (X, B) hiệu lực + bật; bậc `company` ở B cũng được; KHÔNG được khi dòng hết hạn / chưa bắt đầu / tắt công tắc /
   người xem chỉ phủ (Y, B) hoặc (X, C) / A bị loại trừ đích danh. Cùng người xem với `write` → 404 (không mở sửa). Cờ mặc
   định TẮT → `apply_scope` danh sách / báo cáo không đổi. Đếm truy vấn một danh sách 50 hồ sơ có bật cờ = như tắt cờ (EXISTS
   nằm trong một câu SQL).
5. Tắt công tắc, hoặc `to_date` = hôm qua, hoặc `from_date` = mai → mất quyền (sau `perm_cache_clear`); giờ VN 00:30 vẫn
   tính đúng ngày (`vn_today` giả lập).
6. `holds_handling_dept`: đúng cặp mới được chuyển phòng xử lý.
7. Đếm truy vấn `get_perm_profile` không đổi khi tăng từ 1 lên 10 dòng kiêm nhiệm.
8. Canh khai báo: mọi entity trong `SCOPE_FIELDS` có `dept_id` đều có `company` (thêm entity mới mà thiếu → đỏ).
9. `concurrent_row_scope_condition`: trưởng phòng (X, B) thấy dòng kiêm nhiệm (X, B) của người A; người bậc `dept` ở (Y, B)
   không thấy; bậc `all` thấy hết; loại trừ đích danh nhân sự A ở `tab_user_scope` → không thấy.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Sót một đường không ràng công ty → lộ dữ liệu B | Thấp × Cao | Hàng rào `dept_ids` chỉ cùng công ty (mặc định thiếu quyền); bài canh 3, 4 |
| Đổi nhánh `dept` làm lệch hành vi cũ | Trung × Cao | Tách `_company_cond_for` thuần cơ học; chạy lại toàn bộ `test_pham_vi_*` |
| SQL phình khi nhiều cặp | Thấp × Thấp | Gom theo công ty; trần 30 dòng/người |
| Nhân sự `company_id = 0` | Thấp × Trung | Cặp có công ty khác 0 vẫn ràng; nhánh cũ giữ nguyên |
| Dòng hết hạn vẫn tác dụng ≤ 60 giây (cache theo tiến trình) | Cao × Thấp | Ghi rõ trong tài liệu, cùng giới hạn mọi đường phân quyền |
| Nhánh Q1 lọt vào báo cáo / sơ đồ nếu ai đó đổi mặc định cờ | Thấp × Trung | Mặc định TẮT; bài canh báo cáo quân số + sơ đồ ở phase 05 |
| Quên bật cờ ở một tab hồ sơ → tab đó 404 với trưởng phòng B | Trung × Thấp | Bài canh phase 05 gọi lần lượt mọi đường `GET /api/employees/{eid}/...` |

## Security
- Bậc `company` không phình (đúng Q của người chủ). Không khóa quyền mới, `ENTITIES`/`SCOPE_FIELDS` không đổi (bài 44/44 giữ).
- Công tắc mở cả hành động có phạm vi `dept` (duyệt, sửa…) trên cặp theo vai trò sẵn có — đã chốt Q6; ghi rõ ở tài liệu.
- Q1 chỉ mở ĐỌC hồ sơ. Nhạy cảm: `employee_sensitive` là khóa toàn cục (`can_read_sensitive` không xét phạm vi) nên ai có khóa
  đó mở được hồ sơ là đọc được nhóm nhạy cảm — đúng ý "che như thường". Lương vẫn chỉ chính chủ (`SALARY_FIELDS`).
- Q3 rủi ro chấp nhận: phòng dùng chung nhiều công ty → ACL phòng X khớp mọi người có chân ở X ở bất kỳ công ty nào.

## Next steps
Phase 05 dùng `concurrent_row_scope_condition`. Phase 06 rút luật vào `.claude/rules/hr-employee-profile.md`.
