# Phase 03 — Backend: bài kiểm

**Ưu tiên:** P2 · **Effort:** 3.5h · **Trạng thái:** completed · **Phụ thuộc:** 02

## Bối cảnh
- Fixture: `test/backend/conftest.py`; mẫu dựng người dùng/vai trò/phạm vi: `test_ho_so_pham_vi.py`, `test_ho_so_cua_toi_cr378.py`, `test_doi_phap_nhan_nhan_su.py`, `test_nghi_phep_dinh_kem.py`, `test_pham_vi_dinh_kem_b08.py`.
- ⚠️ SQLite không ép độ dài VARCHAR → kiểm `max_length` ở tầng SCHEMA (`pytest.raises(ValidationError)`), không ghi DB rồi khẳng định.
- ⚠️ SQLite tắt FK mặc định — FK mềm nên không ảnh hưởng, nhưng bài xóa hồ sơ phải khẳng định dòng + `FileLink` đã đi.

## Tệp (chỉ tạo, không sửa test cũ)

| Tệp | Nội dung |
|---|---|
| `test/backend/test_qua_trinh_cong_tac_quyen.py` | quyền, phạm vi, IDOR, /me, tệp |
| `test/backend/test_qua_trinh_cong_tac_ap_ho_so.py` | áp hồ sơ, một giao dịch, kiêm nhiệm |
| `test/backend/test_qua_trinh_cong_tac_kiem_du_lieu.py` | validate, cảnh báo, đóng dòng mở, trần, bộ mã |
| `test/backend/test_qua_trinh_cong_tac_thoi_viec.py` | áp Thôi việc qua đường nghỉ việc sẵn có (Q2) |

## Ma trận

**Quyền / IDOR**
- Thiếu `employee.read` → 403 ở list; có read nhưng hồ sơ ngoài phạm vi (phòng khác, scope `dept`) → **404**.
- Có `employee.read` nhưng không `write` → POST/PATCH/DELETE/apply 403.
- `hid` của người B gọi qua `eid` của người A (A trong phạm vi) → 404.
- HR tự thêm/sửa/xóa/áp dòng của chính mình → 403; gắn tệp vào dòng của mình → 403. **Quản trị hệ thống** làm cùng việc trên hồ sơ của mình → 200 (Q3).
- Cờ: HR có write xem hồ sơ người khác → `can_edit=true`; xem hồ sơ chính mình → `false`; quản trị xem hồ sơ mình → `true`. Thiếu sensitive → `can_open_files=false`.
- `/me/work-history`: tài khoản không có grant `employee` nào vẫn đọc được của mình; chỉ ra dòng của mình; `employee_id = 0` → rỗng, KHÔNG ra dòng có `employee_id = 0` (cài sẵn một dòng mồ côi id 0 để bẫy).
- `/me/work-history?employee_id=<khác>` → tham số bị lờ, vẫn chỉ của mình.

**Tệp đính kèm (Q4)**
- Nhân viên không `employee.read`, không sensitive: list + view + download tệp dòng của mình → 200; tệp dòng người khác → 403.
- Có `employee.read` + phạm vi nhưng **thiếu `employee_sensitive.read`**: list/view/download tệp người khác → **403**; nhưng `GET /{eid}/work-history` vẫn 200 và dòng vẫn có `file_count > 0`.
- Có `employee.read` + phạm vi + sensitive → 200.
- Có sensitive nhưng hồ sơ ngoài phạm vi → 403/404 (sensitive không mở rộng phạm vi).
- Có write nhưng thiếu sensitive → gắn/gỡ tệp người khác 403.
- HR scope `dept`: tệp dòng của người phòng khác 403/404.
- Kết quả list không có `url`/`thumb_url` (entity riêng tư).
- `test_pham_vi_dinh_kem_b08.py` cũ phải xanh (dòng `FILE_POLICY` mới tra được cha).
- Xóa dòng → `FileLink` của dòng mất; xóa hồ sơ → mọi dòng + link mất.

**Áp hồ sơ**
- Bổ nhiệm hôm nay `apply_to_profile=True` → `position_id` + `position` (nhãn qua `sync_label`) đổi; `applied_at` có; audit có câu «Áp vào hồ sơ».
- Điều chuyển sang phòng thuộc pháp nhân khác mà không đổi pháp nhân → 400 **và dòng lịch sử KHÔNG được lưu** (một giao dịch).
- Điều chuyển kèm đổi pháp nhân → phòng cũ bị gỡ (đi qua `detach_other_company_departments`).
- `from_date` mai → 400; dòng chính đã kết thúc → 400; dòng chính cũ hơn dòng chính khác → 400; Khác → 400.

**Thôi việc (Q2)** — tệp riêng `test/backend/test_qua_trinh_cong_tac_thoi_viec.py`
- Dòng Thôi việc hôm nay + `apply_to_profile=True` → hồ sơ `status == "resigned"`, `resign_date == from_date`; mọi tài khoản gắn hồ sơ `is_active == False`, `token_version` tăng (phiên bị thu hồi); audit có dòng khóa tài khoản trên entity `user` — **khẳng định giống hệt kết quả của `PATCH /employees/{id}` với `status=resigned`** (chạy cả hai đường trên hai hồ sơ, so kết quả) để chốt «đi đúng đường sẵn có».
- Ngày thôi việc trong quá khứ (nhập bù) → `resign_date` = ngày của DÒNG, không phải hôm nay; tài khoản vẫn bị khóa ngay.
- Ngày thôi việc ngày mai → 400, hồ sơ và tài khoản nguyên vẹn, dòng KHÔNG lưu (vì đi kèm `apply_to_profile`); lưu không áp → 200, tài khoản nguyên.
- `from_date` trước `hire_date` → 400, dòng không lưu, tài khoản nguyên.
- Một giao dịch: ép lỗi trong `lock_linked_users` (monkeypatch ném lỗi) → hồ sơ không đổi trạng thái, dòng lịch sử không còn.
- Hồ sơ đã nghỉ việc rồi, áp dòng có ngày khác → chỉ `resign_date` đổi, không thêm dòng audit «khóa tài khoản».
- Dòng Thôi việc cũ hơn một dòng chính khác (vd. đã có dòng Tuyển dụng lại sau đó) → 400.
- HR tự áp Thôi việc cho chính mình → 403 (Q3).
- Áp lần hai khi hồ sơ đã khớp → `applied_changes == []`, không lỗi.
- L2: người scope `dept` áp điều chuyển sang phòng ngoài tầm → 403, dòng không lưu.
- Kiêm nhiệm đang hiệu lực → phòng vào `extra_departments_of`; sửa `to_date` về hôm qua rồi áp → phòng bị gỡ; phòng chính không đổi.
- Kiêm nhiệm trùng phòng chính → không nhân đôi (hành vi `set_extra_departments` loại phòng chính).

**Kiểm dữ liệu**
- `to_date < from_date` → ValidationError; năm 1899 / 2201 → ValidationError; `event_type` 0, 7, 99 → lỗi; khóa lạ (`status`) → lỗi (forbid).
- `decision_no` 51 ký tự, `note` 501 ký tự → ValidationError (tầng schema).
- Id phòng/chức vụ/công ty không tồn tại → 400; phòng không thuộc công ty khai → 400.
- Kiêm nhiệm thiếu phòng → 400.
- Chồng lấn nhóm chính → 200 + `warnings` không rỗng; kiêm nhiệm hai phòng khác nhau trùng ngày → không cảnh báo.
- `close_open_main` đóng đúng dòng mở cũ hơn (`to_date = from − 1`), không đụng dòng mở mới hơn.
- Dòng thứ 201 → 400.
- Bộ mã: `status_catalog.get("work_event_type")` có đủ 7 mã; giá trị là chuỗi số khớp `WorkEventType`.

## Lệnh (chỉ phần vừa sửa)
```bash
docker compose exec -T api python -m pytest -q \
  test/backend/test_qua_trinh_cong_tac_quyen.py \
  test/backend/test_qua_trinh_cong_tac_ap_ho_so.py \
  test/backend/test_qua_trinh_cong_tac_kiem_du_lieu.py \
  test/backend/test_qua_trinh_cong_tac_thoi_viec.py \
  test/backend/test_pham_vi_dinh_kem_b08.py \
  test/backend/test_ho_so_nhan_su_dot1.py test/backend/test_employee_delete_account.py
```

## Todo
- [x] 4 tệp test, mỗi bài nói hành vi; test nhắc lỗi cũ thì ghi lỗi đó trong comment
- [x] chạy đúng lệnh trên, xanh (142 passed — 4 tệp mới + `b08` + `dot1` + `delete_account`)

## Thành công khi
Toàn bộ ma trận xanh; một test cố ý phá «một giao dịch» (commit sớm) phải đỏ.
