# Sửa finding BACKEND của code review «Quá trình công tác nhân sự»

## Thực thi
- Plan: `frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/plan.md`
- Report backend gốc: `reports/fullstack-developer-261003-0938-phase-02-03-backend-api-bai-kiem.md`
- Nhánh: `erp-v2`, chưa commit.

## Quy trình: test đỏ trước, sửa sau
Với MỖI finding (H2, M1, M2, M3, M7, và 4 ca Low có thể kiểm bằng test), tôi:
1. Viết test phản ánh hành vi ĐÚNG.
2. Tạm revert đúng đoạn sửa (qua `cp`/`sed`/script Python, không qua git vì phần lớn tệp
   `work_history_*.py` CHƯA commit nên không `git stash` được) → chạy lại → xác nhận **ĐỎ**.
3. Khôi phục bản sửa → chạy lại → xác nhận **XANH**.
Đã làm thủ công cho: H2 (cả 2 bài), M1 (cả 7 ca), M2, M3, M7, và 4 Low (close_open_main scope,
gỡ kiêm nhiệm khi còn dòng khác, `serialize_one` theo dòng chính mới nhất, `applied_at` cùng giao
dịch). Tất cả đều đỏ đúng chỗ trước khi sửa, xanh sau khi khôi phục.

## Tệp mới
- `backend/app/core/vn_time.py` (23 dòng) — `vn_today()` DUY NHẤT, gộp từ hai bản chép tay.
- `test/backend/test_qua_trinh_cong_tac_gio_vn.py` (77 dòng, 2 bài) — H2.
- `test/backend/test_qua_trinh_cong_tac_sua_loi_review.py` (141 dòng, 16 bài) — M1/M2/M3/M7.
- `test/backend/test_qua_trinh_cong_tac_sua_loi_review_low.py` (153 dòng, 6 bài) — Low có thể kiểm.

## Tệp sửa
- `backend/app/modules/employee/report_headcount_events.py` — bỏ `vn_today()` chép tay, re-export
  từ `core.vn_time` (giữ tên cũ, `report_service.py` đang `from ... import vn_today`).
- `backend/app/modules/work/report_rows.py` — `today_vn = vn_today` (bí danh), giữ tên cũ cho
  `report_service.py` (`rows.today_vn()`).
- `backend/app/modules/employee/work_history_rules.py` — H2: `apply_gate` dùng `vn_today()`.
- `backend/app/modules/employee/work_history_apply_service.py` — H2 (2 chỗ) + Low (gộp
  `applied_at`/`applied_by` lên TRƯỚC khi gọi nhánh áp; gỡ kiêm nhiệm hết hạn xét còn dòng khác
  cùng phòng đang hiệu lực thì không gỡ).
- `backend/app/modules/employee/work_history_serializer.py` — H2 + Low (`serialize_one` tính
  `can_apply` trên toàn bộ dòng của nhân sự, không chỉ dòng lẻ).
- `backend/app/modules/employee/work_history_schema.py` — M1: `model_validator(mode="before")`
  trên `WorkHistoryUpdate`, chỉ `to_date`/`decision_date` được null tường minh.
- `backend/app/modules/employee/work_history_service.py` — Low: `_check_close_open_main_scope`
  (422 khi `close_open_main=True` mà `event_type` không phải nhóm chính), gọi ở `create`/`update`;
  M7: `delete_all_of` gọi `delete_attachments_for(..., commit=False)`.
- `backend/app/modules/employee/work_history_access.py` — M2: `block_delete_without_sensitive`;
  M3: nhánh "người khác" của `check_file` đòi thật `employee.write` (không nhận `create`).
- `backend/app/modules/employee/work_history_controller.py` — M2: gọi chốt mới trước khi xoá; Low:
  audit xoá dùng `_audit_base_message(row)` thay vì chỉ `#id`.
- `backend/app/modules/employee/work_history_model.py` — Low: bỏ `index=True` của `employee_id`
  (đã có index ghép `(employee_id, from_date)` làm leftmost-prefix; migration `wkhist01` vốn không
  tạo index đơn, nay model khớp migration — không cần sửa migration).
- `backend/app/modules/attachment/service.py` — M7: `delete_attachments_for` thêm `commit: bool =
  True` (giữ hành vi cũ cho mọi nơi gọi khác).
- `.claude/rules/hr-employee-profile.md` — M8: sửa mục «QUÁ TRÌNH CÔNG TÁC»: "bốn loại áp được"
  → SÁU loại (5 nhóm chính qua `update_employee` + CONCURRENT qua `set_extra_departments`, không
  phải "không áp"); thứ tự thật trong `update_employee` (gán ô → phát hiện nghỉ việc → khóa tài
  khoản); thêm mục 6 nói rõ dùng `vn_today()`, cấm chép tay `datetime.utcnow()+7h`.

## Chi tiết từng finding

**H2 (vn_today).** Bốn chỗ cũ dùng `date.today()` (ngày UTC của container) ở
`work_history_rules.apply_gate`, `work_history_apply_service.apply`/`_apply_concurrent`,
`work_history_serializer.serialize_list` — lệch ngày Việt Nam 00:00-06:59 giờ VN. Gộp về
`app.core.vn_time.vn_today()`. Test khoá đồng hồ giả (`monkeypatch.setattr(vn_time, "datetime",
_FixedDatetime)`) ở đúng mốc 23:30 UTC hôm trước (= 06:30 VN hôm sau): dòng `from_date` = hôm nay
giờ VN áp được; kiêm nhiệm `to_date` = hôm qua giờ VN bị gỡ. Patch đúng MỘT chỗ
(`app.core.vn_time.datetime`) là đủ cho mọi nơi gọi `vn_today()` vì hàm chạy trong namespace của
module đó bất kể ai import.

**M1 (PATCH null tường minh).** `WorkHistoryUpdate` thêm `model_validator(mode="before")`: mọi ô
gửi `null` tường minh đều 422 trừ `to_date`/`decision_date` (Q1: null = xoá/mở lại). 7 ca kiểm
(event_type/from_date/company_id/department_id/position_id/note/decision_no) + 2 ca xác nhận
`to_date`/`decision_date` vẫn null được + 1 ca không gửi gì vẫn qua.

**M2 (xoá dòng có tệp thiếu sensitive).** `block_delete_without_sensitive` — xoá dòng CỦA NGƯỜI
KHÁC mà dòng đó có tệp đính kèm, thiếu `employee_sensitive.read` → 403, KHÔNG xoá (tệp + dòng còn
nguyên). Chính chủ / dòng không tệp không bị chặn.

**M3 (create không thay write).** Nhánh "người khác" của `check_file` giờ đòi thật
`get_scoped(..., "write")` khi `mode != "read"`, không còn rơi về nhánh chung (`write HOẶC
create`) của `_check`. Vai trò chỉ có `employee.create` + `employee_sensitive.read` nay 403 khi
gắn/gỡ tệp của người khác.

**M7 (delete_all_of tự commit qua delete_attachments_for).** Thêm `commit: bool = True` (mặc định
giữ hành vi cũ); `delete_all_of` gọi `commit=False` để `delete_employee` giữ đúng một giao dịch.
Test: gọi `delete_all_of` rồi `rollback()` — FileLink phải còn nguyên (chưa bị M7 bug thật sự xoá
vĩnh viễn giữa chừng).

**Low đã sửa + có test:**
- `close_open_main` gửi kèm `event_type` ngoài nhóm chính (OTHER/CONCURRENT) → 422.
- Gỡ kiêm nhiệm hết hạn: còn dòng KHÁC cùng phòng đang hiệu lực → không gỡ.
- `serialize_one` tính `can_apply` theo TOÀN BỘ dòng của nhân sự (chốt "dòng chính mới nhất"),
  không chỉ so dòng với chính nó.
- `applied_at`/`applied_by` gán TRƯỚC khi gọi `update_employee` — đi cùng cú commit nội bộ của hàm
  đó, không lệch nếu có lỗi giữa `apply()` và commit cuối của controller (test dựng đúng ca: apply
  xong KHÔNG commit ở tầng gọi, rollback mô phỏng lỗi giữa đường — hồ sơ vẫn đổi vì
  `update_employee` đã tự commit, `applied_at` PHẢI còn nguyên theo).
- Audit xoá dòng ghi `_audit_base_message(row)` (nội dung dòng: loại, chức vụ, ngày, số QĐ), không
  chỉ `#id`.

**Low đã sửa, không thêm test riêng (đã phủ bởi test có sẵn hoặc không kiểm được qua pytest):**
- `employee_id` bỏ `index=True` — khớp migration `wkhist01` (vốn không tạo index đơn). SQLite test
  không phân biệt được (không ép index), xác nhận bằng đọc mã + so với migration.

## Hợp đồng API — có đổi, cần biết cho FE (phase 04/05)
- `PATCH .../work-history/{hid}` nay trả **422** nếu gửi `null` tường minh cho bất kỳ ô nào NGOÀI
  `to_date`/`decision_date`. Trước đây các ca này 500. FE nên tránh gửi `null` cho ô không đổi —
  bỏ hẳn khoá đó ra khỏi payload PATCH.
- `POST`/`PATCH .../work-history` nay trả **422** nếu `close_open_main=true` mà `event_type` không
  thuộc nhóm chính (HIRE/TRANSFER/APPOINT/DISMISS/RESIGN). FE chỉ nên cho tick ô "Đóng dòng mở" khi
  đang chọn một trong 5 loại đó.
- `DELETE .../work-history/{hid}` nay có thể trả **403** (thay vì 200+xoá) khi dòng có tệp QĐ của
  người khác và người gọi thiếu `employee_sensitive.read`. FE nên ẩn/disable nút Xoá theo đúng cờ
  đã có (`can_open_files`) khi dòng có `file_count > 0` và cờ đó false.
- Gắn/gỡ tệp qua `/api/attachments` (entity=`employee_work_history`) của NGƯỜI KHÁC nay đòi thật
  `employee.write` (không còn chấp nhận `employee.create`) — hiếm gặp trên FE vì UI quyết định hiện
  nút theo `can_edit` (đã tính đúng theo `employee.write`), không phải điểm cần sửa FE.
- `item.can_apply` trong response (POST/PATCH/apply trả `item` qua `serialize_one`) nay CHÍNH XÁC
  hơn theo chốt "dòng chính mới nhất" — trước đây có thể sai THÀNH `true` cho một dòng chính cũ
  hơn dòng chính khác (link "Áp" từng hiện nhầm, bấm vào vẫn 400 ở `/apply` vì `apply_gate` luôn
  đúng). Không đổi *shape*, chỉ đổi *giá trị* đúng hơn.

## Kiểm tra
```
docker compose exec -T api python -m pytest -q \
  test/backend/test_qua_trinh_cong_tac_quyen.py \
  test/backend/test_qua_trinh_cong_tac_ap_ho_so.py \
  test/backend/test_qua_trinh_cong_tac_kiem_du_lieu.py \
  test/backend/test_qua_trinh_cong_tac_thoi_viec.py \
  test/backend/test_qua_trinh_cong_tac_gio_vn.py \
  test/backend/test_qua_trinh_cong_tac_sua_loi_review.py \
  test/backend/test_qua_trinh_cong_tac_sua_loi_review_low.py \
  test/backend/test_pham_vi_dinh_kem_b08.py \
  test/backend/test_ho_so_nhan_su_dot1.py \
  test/backend/test_employee_delete_account.py \
  test/backend/test_pham_vi_khai_du_b07.py \
  test/backend/test_bao_cao_nhan_su.py \
  test/backend/test_bao_cao_cong_viec.py \
  test/backend/test_bao_cao_cong_viec_gom_sql.py
```
→ **190 passed**, 0 failed. `test_bao_cao_nhan_su.py`/`test_bao_cao_cong_viec*.py` chạy thêm vì
dùng `report_headcount_events.vn_today`/`work.report_rows.today_vn` (grep theo yêu cầu).
`python -c "import app.main"` sạch. `py_compile` sạch trên 12 tệp đã sửa/tạo. `pyflakes` sạch trừ
1 cảnh báo "unused import" CỐ Ý (re-export `vn_today` ở `report_headcount_events.py`, đã ghi comment
giải thích — `pyflakes` trần không hiểu `# noqa`, khác `flake8`).

## Không đụng
- `frontend-v2/src/**` (agent khác).
- Migration `wkhist01` — không cần sửa (bỏ `index=True` ở model đủ khớp, migration vốn đã không
  tạo index đơn).
- `attachment/service.py` còn 238 dòng (đã vượt 200 TỪ TRƯỚC, không phải do đợt này — chỉ thêm 1
  tham số + docstring cho `delete_attachments_for`; không nằm trong phạm vi review này để tách).

**Status:** DONE
**Summary:** Sửa đủ H2/M1/M2/M3/M7 + 6 ca Low (có test cho 6/7 ca Low, 1 ca còn lại — bỏ
`index=True` — chỉ xác nhận bằng đọc mã vì SQLite test không ép index); M8 sửa luật. Test viết
trước, xác nhận đỏ bằng cách tạm revert từng đoạn sửa rồi khôi phục — không chỉ viết test suông.
190/190 bài xanh (145 cũ+mới trong phạm vi quá trình công tác + 45 bài báo cáo/phạm vi liên quan
không hồi quy).
**Concerns:** (1) `can_apply` trả đúng hơn sau fix `serialize_one` có thể đổi hành vi nút "Áp" hiện
trên FE cho đúng số dòng cạnh biên (dòng chính không-mới-nhất từng hiện sai thành bấm được) — nên
soi lại nếu FE có test ảnh chụp cố định giá trị `can_apply`. (2) `attachment/service.py` 238 dòng
là nợ kỹ thuật có từ trước, không phải lỗi mới.

Không có câu hỏi treo.
